#!/usr/bin/env python3
"""
AI Philosophy — Proxy v13 (Production / Flask)
Deploy: Railway / Render
"""

import json
import base64
import time
import io
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY", "")
REPLICATE_TOKEN = os.environ.get("REPLICATE_TOKEN", "")
PORT = int(os.environ.get("PORT", 5555))

GEMINI_FLASH_URL = (
    "https://generativelanguage.googleapis.com/v1beta"
    "/models/gemini-2.5-flash:generateContent"
)
REPLICATE_API = "https://api.replicate.com/v1"
FLUX_MODEL    = "black-forest-labs/flux-schnell"

STYLES = {
    "auto":        "AUTO — choose the visual register that best serves the philosophical tension, subject, and territory. Available registers: flemish, moreau, cinema (with its 9 sub-registers), typographic, documentary, cosmic, everyday, sociopolitical. Choose the one that creates the strongest image for this specific concept. State your choice in the prompt.",
    "flemish":     "Flemish Renaissance oil painting, rich jewel tones, dramatic chiaroscuro, intricate ornamental detail, Rubens and Van Eyck influence, monumental composition, aged impasto texture, deep shadows, luminous golden light, museum quality",
    "moreau":      "Gustave Moreau symbolist oil painting, mythological grandeur, dense ornamental surfaces, luminous jewel-like colors, dreamlike layered atmosphere, Pre-Raphaelite influence, mysterious narrative depth, jeweled figures, museum quality",
    "cinema":      "CINEMATIC — detect the cinematic register the concept demands and build from there. Available registers: (1) NOIR: urban night, hard shadows, wet streets, moral ambiguity, Blade Runner / Se7en aesthetic; (2) EPIC/SUBLIME: vast landscape, golden hour, lone figure OR massive crowd OR animal migration, Terrence Malick / Roger Deakins; (3) INTIMATE DRAMA: close interior, warm window light, human face or hands or body in private moment, child or elder or animal, Wong Kar-wai / Alfonso Cuarón / Hirokazu Kore-eda — USE THIS REGISTER MORE, it is underrepresented; (4) DYSTOPIAN/SCI-FI: cold industrial light, surveillance, dehumanized space, Tarkovsky / Children of Men; (5) NEOREALISM: raw street, available light, unposed crowd or community, family or neighbors, Cassavetes / Bicycle Thieves / Pasolini; (6) PSYCHOLOGICAL THRILLER: claustrophobic space, destabilizing angle, dread in ordinary setting, Kubrick / Haneke; (7) POLITICAL DRAMA: collective protest, institutional power, masses vs system, Loach / Costa-Gavras / Eisenstein; (8) TECHNOLOGY & SCREEN: human beings in relationship with screens, devices, interfaces, data — not dystopian but ambiguous, intimate or alienating depending on concept, Spike Jonze / Michel Gondry / Black Mirror calm episodes — phones as mirrors, screens as windows, code as landscape, light from devices on human faces; (9) URBAN STREET LIFE: the street as philosophical space — not protest, but daily life, vendors, commuters, children playing, rain on pavement, neon reflections, bodies in motion, city as living organism, Wong Kar-wai street / Edward Yang / Jia Zhangke. BALANCE RULE: registers (3) INTIMATE DRAMA, (5) NEOREALISM, (8) TECHNOLOGY, and (9) URBAN STREET are chronically underused — actively favor them. Registers (4) and (7) are overused — only when concept explicitly demands it. SUBJECT RANGE: hands, faces, domestic objects, children, elders, animals in human spaces, communities, devices, streets. Always: anamorphic lens, 35mm film grain, cinematic color grading.",
    "typographic": "stark typographic graphic design, bold serif display text as primary visual element, extreme high contrast black and white photography, editorial brutalist layout, Barbara Kruger influence, raw confrontational composition",
    "documentary": "documentary black and white photography, raw photojournalism, Cartier-Bresson decisive moment, Sebastião Salgado influence, heavy 35mm film grain, honest unfiltered natural light, street photography intimacy",
    "cosmic":      "vast cosmic scale photography, lone human figure dwarfed by universe, nebulae and deep star fields, Hubble Space Telescope aesthetic, sublime existential scale, monochrome figure against infinite color cosmos",
    "everyday":    "intimate everyday photography, natural window light, ordinary domestic or urban spaces, close human scale, hands and objects and rooms, quiet moments in familiar places, Nan Goldin and Stephen Shore influence, color photography with emotional weight",
    "sociopolitical": "documentary street photography with political weight, urban environments, protest or institutional spaces, raw social tension, graffiti and architecture, people in collective or confrontational contexts, Josef Koudelka and Dorothea Lange influence",
}

RATIO_MAP = {
    "16:9": (1344, 768),
    "1:1":  (1024, 1024),
    "4:5":  (896,  1120),
    "9:16": (768,  1344),
}

EXPANDER_SYSTEM = """Eres el motor filosófico de AI Philosophy.

Tu trabajo: tomar un concepto libre y expandirlo a una TENSIÓN FILOSÓFICA con fricción real.
No resumes el concepto — lo abres. Buscas el problema sin resolver.

CUATRO CAPAS QUE DEBES PRODUCIR:

CAPA 1 — TENSIÓN
NO uses siempre la estructura paradójica "X que en realidad es Y".
Varía entre estos tipos:

TIPO A — PARADOJA: dos fuerzas en contradicción directa.
  "sistemas diseñados para proteger que terminan protegiendo solo a quienes los diseñaron"

TIPO B — AUSENCIA: lo que falta, el vacío como presencia activa.
  "la forma que tiene una vida cuando ya no hay nadie que la recuerde"

TIPO C — PROCESO IRREVERSIBLE: algo que no puede deshacerse.
  "el momento en que una creencia se vuelve parte de quien eres y ya no puedes verla desde afuera"

TIPO D — CONDICIÓN INVISIBLE: algo que opera sin ser visto.
  "las reglas no escritas que todos obedecen sin saber que existen"

TIPO E — HERENCIA NO ELEGIDA: lo que se recibe sin consentimiento.
  "el idioma en que piensas sin haberlo elegido"
  "el miedo que alguien te dejó sin saber que lo hacía"

TIPO F — LÍMITE: el borde donde algo termina o no puede continuar.
  "el punto exacto donde el cuidado se convierte en control"

TIPO G — COEXISTENCIA IMPOSIBLE: dos cosas que no deberían existir juntas pero existen.
  "la ternura que existe dentro de la crueldad cotidiana"

TIPO H — TENSIÓN EMOCIONAL DIRECTA: cuando el concepto tiene carga afectiva,
la tensión puede ser emocional antes que filosófica.
  "el momento en que dos personas se tocan y ninguna sabe que es la última vez"
  "la distancia que existe dentro del abrazo más cercano"
  "lo que se dice con el cuerpo cuando las palabras ya no alcanzan"
  → No toda tensión necesita ser conceptual. A veces la emoción es el concepto.
  ÚSALO cuando: el concepto involucra relación, cercanía, pérdida, amor, presencia,
  contacto — especialmente si la guía visual indica calidez humana.

Elige el tipo que la tensión del concepto pide. No uses Tipo A por defecto.

FIDELIDAD AL IMPULSO ORIGINAL — REGLA CRÍTICA:
El concepto tiene una dirección emocional. Tu trabajo es profundizarla, no traicionarla.

Si el concepto apunta hacia: vida, belleza, naturaleza, amor, comunidad, creación,
esperanza, conexión, asombro — la tensión debe honrar esa dirección.
NO derives hacia la oscuridad más compleja solo porque es filosóficamente interesante.

Ejemplos de traición al impulso:
- Concepto "naturaleza como fuente de vida" → tensión sobre descomposición y olvido = TRAICIÓN
- Concepto "amor" → tensión sobre el poder y el control = TRAICIÓN
- Concepto "infancia" → tensión sobre el trauma = TRAICIÓN (a menos que sea explícito)

Ejemplos de fidelidad al impulso:
- Concepto "naturaleza como fuente de vida" → tensión sobre la autopoiesis, la vida que se genera a sí misma continuamente = FIDELIDAD
- Concepto "amor" → tensión sobre la distancia que existe dentro del abrazo más cercano = FIDELIDAD
- Concepto "infancia" → tensión sobre lo que el cuerpo aprende antes que el lenguaje = FIDELIDAD

PREGUNTA DE VERIFICACIÓN antes de elegir la tensión:
¿Esta tensión honra la dirección del concepto original, o la lleva a un lugar que el concepto no pedía?
Si la lleva a un lugar no pedido — elige otra tensión.

CAPA 2 — ANCLAJE
No siempre un filósofo académico. El anclaje puede ser:
- Filósofo o concepto técnico: Merleau-Ponty, Benjamin, Arendt, Bourdieu, Camus, Wittgenstein
- Científico: Darwin, Einstein, Heisenberg, Maturana/Varela (autopoiesis), Lynn Margulis (simbiosis), Gregory Bateson (mente en la naturaleza), Carl Sagan
- Psicólogo: Jung (inconsciente colectivo, arquetipos), Winnicott (espacio transicional), Freud, Viktor Frankl, William James
- Escritor / poeta: Borges, Clarice Lispector, Rilke, Neruda, Celan, Pessoa, Baldwin, Kafka, Woolf
- Cineasta: Tarkovsky, Wong Kar-wai, Bergman, Kubrick — cuando una escena o concepto ancla mejor que un texto
- Canción o álbum: si captura exactamente la tensión emocional
- Frase o imagen cultural que ancle sin necesitar explicación académica
REGLA: elige el anclaje que mejor sostenga la tensión específica del concepto,
sin importar la disciplina. La filosofía no tiene fronteras disciplinarias.
Cuando la tensión es Tipo H (emocional directa), el anclaje debe
ser también emocional — un poeta, una canción, una escena — no un filósofo.
CAPA 3 — SUJETO:
  - colectivo_en_tension, animal, objeto_espacio, celeste, dualidad, monumental, figura_individual
  REGLA: figura_individual es el último recurso.
CAPA 4 — TERRITORIO: sublime | cotidiano | sociopolítico

EQUILIBRIO TERRITORIAL — REGLA CRÍTICA:
El territorio sociopolítico está sobrerepresentado. Antes de elegirlo pregúntate:
¿El concepto realmente exige poder, política o conflicto colectivo?
Si no, elige cotidiano o sublime.

TERRITORIO COTIDIANO: tiempo, memoria, cuerpo, rutina, silencio, objetos,
espacios domésticos, relaciones, trabajo, comida, sueño, infancia, vejez.
Es el territorio más subutilizado — úsalo más.

TERRITORIO SUBLIME: escala, cosmos, naturaleza, fenómenos naturales,
muerte, eternidad, vacío, lo inconmensurable.

TERRITORIO SOCIOPOLÍTICO solo cuando el concepto exige explícitamente:
poder institucional, conflicto colectivo, desigualdad, control, resistencia.

REGISTRO EMOCIONAL — REGLA ESPECIAL:
Cuando el concepto tiene carga humana directa (madre, hijo, duelo, amor, familia,
cuerpo, tacto, ternura, comunidad, rutina, infancia, vejez, amistad):
  - Drama íntimo antes que político
  - Cotidiano o sublime emocional antes que sociopolítico
  - Cinematográfico → sub-registro INTIMATE DRAMA: Wong Kar-wai / Cuarón / Kore-eda
  - Calidez, cercanía, escala humana — no frialdad institucional

Responde SOLO con JSON válido, sin markdown. TODOS los valores en INGLÉS:
{
  "tension": "the unresolved tension — choose the right type, not always paradox — in English",
  "anchor": "Philosopher/Concept — one line of context — in English",
  "subject": "colectivo_en_tension|animal|objeto_espacio|celeste|dualidad|monumental|figura_individual",
  "subject_note": "concrete description — 10 words max — in English",
  "territory": "sublime|cotidiano|sociopolítico",
  "core": "philosophical core — one line — NOT always paradox — in English"
}"""

IMAGE_SYSTEM = """Eres el constructor visual de AI Philosophy.

REGLAS DEL IMAGE PROMPT:
- Concreto y específico — sin adjetivos abstractos
- Mínimo 80 palabras
- Sin texto en la imagen

ILUMINACIÓN — evitar por defecto:
- luz dorada de atardecer, sol visible en frame, cielo naranja/dorado
Preferir: luz difusa, overcast, interior, nocturna, contraluz frío, neblina, luz artificial.

REGLAS DEL SUBTITLE:
- Máximo 12 palabras
- NO describe la imagen — abre una grieta
- NO uses siempre la misma estructura — varía entre estos tipos:

TIPO 1 — PARADOJA (dos frases en tensión):
  "The line moves forward. No one remembers why."
  "We consume what we love. We call it communion."
  → Úsala ocasionalmente, no como default.

TIPO 2 — DECLARACIÓN QUE INCOMODA (una sola frase perturbadora):
  "It was always going to end this way."
  "Nobody asked if you wanted to arrive."
  "The contract was signed before you were born."
  → Sin inversión, sin dos partes. Solo una verdad incómoda.

TIPO 3 — PREGUNTA GENUINAMENTE ABIERTA (no retórica):
  "What remains when the witness leaves?"
  "Who taught you that this was yours?"
  → No tiene respuesta obvia. Deja al lector suspendido.

TIPO 4 — IMAGEN VERBAL CONCRETA (escena que abre):
  "A door left open in an empty house."
  "The last light on a face that isn't there."
  → No explica, no filosofa — muestra algo concreto que resuena.

TIPO 5 — INTERRUPCIÓN (frase que no termina donde debería):
  "We were almost—"
  "The answer came. It changed nothing."
  → Corta antes de cerrar, o cierra de forma inesperada.

TIPO 6 — EVOCACIÓN EMOCIONAL DIRECTA (calidez, conexión, presencia):
  "We stayed. That was everything."
  "The city kept moving. We didn't."
  "In the rain, we forgot to perform."
  "This is what we meant when we said together."
  → No pregunta, no filosofa, no fractura — nombra lo que se siente
  de forma que el espectador lo reconozca en su propio cuerpo.
  Corto, concreto, cálido o tenso según el concepto. Sin abstracción.
  ÚSALO cuando: la imagen muestra cercanía humana, contacto, intimidad,
  comunidad, ternura — o cuando el concepto tiene carga emocional directa
  y la guía visual indica presencia humana cálida.

TIPO 7 — DESDE ADENTRO DE LA EXPERIENCIA (cercanía, presencia en primera o segunda persona):
  "I stood where the water ends and didn't move."
  "Something in me is still standing at that edge."
  "You've been here before. You just don't remember when."
  "I kept looking. Nothing answered. That was enough."
  → Habla desde la experiencia del espectador, no sobre el concepto.
  Usa "I", "you", "we" no como concepto sino como presencia viva.
  El lector no piensa — se reconoce.
  ÚSALO cuando: la imagen tiene una cualidad contemplativa o liminal,
  cuando el espectador podría estar en ese lugar, cuando el concepto
  tiene una dimensión de experiencia directa — no solo filosófica.

REGLA DE CERCANÍA:
Un subtítulo llega cuando el espectador puede decir "eso lo he sentido"
o "eso me ha pasado" — no solo "eso es interesante".
La filosofía puede vivir en las capas. El subtítulo puede simplemente
hablar desde adentro.

REGLA DE TEMPERATURA EMOCIONAL:
Cuando la guía visual incluye: pareja, abrazo, manos que se tocan, lluvia compartida,
luz cálida, interior doméstico, contacto físico, comunidad, familia — el subtítulo
debe tener calidez. No frialdad conceptual. El Tipo 6 es el primero a considerar.
La filosofía puede vivir en la imagen. El subtítulo puede simplemente hacer sentir.

Elige el tipo que mejor sirva a la tensión filosófica del concepto.
Ejemplo malo: "The enduring echo of foundational tales." — descriptivo, cierra.
Ejemplo malo para imagen cálida: "What remains when the day's masks fall?" — 
  la imagen pide sentir, el subtítulo filosofa en frío.

QUÉ HACE UN SUBTÍTULO INTELIGENTE:
Un subtítulo inteligente dice algo que el espectador no esperaba
pero reconoce como verdadero en el momento de leerlo.
No es oscuro — es preciso. No es poético — es exacto.
Abre algo que no sabías que estaba cerrado.

ESTRUCTURAS SOBREUSADAS — EVITAR:
- "To [verb] is to [verb]." — To be born is to forget. To die is to feed.
- "[X] remembers. [Y] forgets." — The screen remembers. We forget.
- "[X] [verbs]. [Y] [verbs]." — dos frases cortas separadas por punto como default
- "We [verb]. That is [noun]." — We stayed. That was everything.
- Preguntas que empiezan con "What is born from..."
- Cualquier estructura que el sistema haya usado más de dos veces

CRITERIO DE CALIDAD:
Antes de generar el subtítulo, pregúntate:
¿Alguien que lea esto dirá "nunca lo había pensado así" o "eso es exactamente lo que es"?
Si la respuesta es sí — es el subtítulo correcto.
Si suena a algo que ya has leído antes — busca otro ángulo.

Responde SOLO con JSON válido, sin markdown:
{
  "prompt": "image prompt técnico en inglés — mínimo 80 palabras",
  "subtitle": "subtítulo en inglés — fractura o evocación — máximo 12 palabras"
}"""


def expand_concept(concept):
    resp = requests.post(
        f"{GEMINI_FLASH_URL}?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": EXPANDER_SYSTEM}]},
            "contents": [{"parts": [{"text": f"Concepto: {concept}"}]}],
            "generationConfig": {"temperature": 0.9, "responseMimeType": "application/json"}
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise Exception(f"Gemini expander error {resp.status_code}")
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text.replace("```json", "").replace("```", "").strip())


def build_image_prompt(expanded, style, subtitle_override, visual_guide=""):
    style_desc = STYLES.get(style, STYLES["cinema"])
    user_msg = (
        f"TENSIÓN: {expanded['tension']}\n"
        f"ANCLAJE: {expanded['anchor']}\n"
        f"SUJETO: {expanded['subject']} — {expanded['subject_note']}\n"
        f"TERRITORIO: {expanded['territory']}\n"
        f"REGISTRO: {style_desc}\n"
    )
    if visual_guide:
        user_msg += f"\nGUÍA VISUAL DEL ARTISTA (incorpora esto en el prompt de imagen): {visual_guide}\n"
    if subtitle_override:
        user_msg += f"\nSUBTÍTULO (usa exactamente): {subtitle_override}\n"
    else:
        user_msg += "\nSUBTÍTULO: genera uno — fractura, no descripción.\n"

    resp = requests.post(
        f"{GEMINI_FLASH_URL}?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": IMAGE_SYSTEM}]},
            "contents": [{"parts": [{"text": user_msg}]}],
            "generationConfig": {"temperature": 0.75, "responseMimeType": "application/json"}
        },
        timeout=30,
    )
    if resp.status_code != 200:
        raise Exception(f"Gemini image builder error {resp.status_code}")
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text.replace("```json", "").replace("```", "").strip())


def generate_image(prompt, ratio):
    width, height = RATIO_MAP.get(ratio, (896, 1120))
    headers = {"Authorization": f"Bearer {REPLICATE_TOKEN}", "Content-Type": "application/json"}
    resp = requests.post(
        f"{REPLICATE_API}/models/{FLUX_MODEL}/predictions",
        headers=headers,
        json={"input": {"prompt": prompt, "width": width, "height": height,
                        "aspect_ratio": ratio, "output_format": "png",
                        "output_quality": 90, "safety_tolerance": 2}},
        timeout=30,
    )
    if resp.status_code not in (200, 201, 202):
        raise Exception(f"Replicate error {resp.status_code}: {resp.text[:300]}")

    prediction = resp.json()
    pred_id = prediction.get("id")
    output = prediction.get("output")
    status = prediction.get("status", "")

    if not output or status != "succeeded":
        for _ in range(90):
            time.sleep(2)
            poll = requests.get(f"{REPLICATE_API}/predictions/{pred_id}", headers=headers, timeout=30)
            if poll.status_code != 200:
                continue
            poll_data = poll.json()
            status = poll_data.get("status", "")
            if status == "succeeded":
                output = poll_data.get("output")
                break
            elif status in ("failed", "canceled"):
                raise Exception(f"Prediction {status}: {poll_data.get('error', '')}")

    if not output:
        raise Exception("Flux no devolvió imagen.")

    image_url = output[0] if isinstance(output, list) else output
    img_resp = requests.get(image_url, timeout=60)
    if img_resp.status_code != 200:
        raise Exception(f"Error descargando imagen: {img_resp.status_code}")
    return img_resp.content


def compose_subtitle(image_bytes, subtitle):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    W, H = img.size
    gradient = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_grad = ImageDraw.Draw(gradient)
    grad_height = int(H * 0.35)
    for y in range(grad_height):
        alpha = int(210 * (y / grad_height))
        draw_grad.line([(0, H - grad_height + y), (W, H - grad_height + y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img, gradient)
    draw = ImageDraw.Draw(img)
    font_size = max(48, int(W * 0.056))
    font = None
    for path in [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
    ]:
        try:
            font = ImageFont.truetype(path, font_size)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()
    words = subtitle.split()
    lines, current = [], ""
    max_width = int(W * 0.80)
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    line_height = int(font_size * 1.5)
    total_text_h = len(lines) * line_height
    y_start = H - int(H * 0.08) - total_text_h
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (W - (bbox[2] - bbox[0])) // 2
        y = y_start + i * line_height
        draw.text((x + 1, y + 1), line, font=font, fill=(0, 0, 0, 160))
        draw.text((x, y), line, font=font, fill=(232, 224, 208, 220))
    result = img.convert("RGB")
    buf = io.BytesIO()
    result.save(buf, format="PNG")
    return buf.getvalue()


@app.route("/health")
@app.route("/")
def health():
    return jsonify({"status": "ok"})


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido"}), 400

    concept     = data.get("concept", "").strip()
    style       = data.get("style", "cinema")
    ratio       = data.get("ratio", "4:5")
    subtitle    = data.get("subtitle", "").strip()
    visual_guide = data.get("visualGuide", "").strip()

    if not concept:
        return jsonify({"error": "concept requerido"}), 400

    print(f"\n  Concepto: {concept[:80]}")

    try:
        expanded = expand_concept(concept)
    except Exception as e:
        return jsonify({"error": f"Error expandiendo concepto: {e}"}), 500

    try:
        built = build_image_prompt(expanded, style, subtitle, visual_guide)
    except Exception as e:
        return jsonify({"error": f"Error construyendo prompt: {e}"}), 500

    final_subtitle = subtitle or built.get("subtitle", "")

    try:
        image_bytes = generate_image(built["prompt"], ratio)
    except Exception as e:
        return jsonify({"error": f"Error generando imagen: {e}"}), 500

    return jsonify({
        "image":     base64.b64encode(image_bytes).decode("utf-8"),
        "prompt":    built.get("prompt", ""),
        "core":      expanded.get("core", ""),
        "territory": expanded.get("territory", "—"),
        "tension":   expanded.get("tension", ""),
        "anchor":    expanded.get("anchor", ""),
        "subject":   expanded.get("subject", ""),
        "subtitle":  final_subtitle,
    })


@app.route("/regen", methods=["POST"])
def regen():
    """Regenera imagen con un prompt existente — sin llamar a Gemini."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido"}), 400

    prompt = data.get("prompt", "").strip()
    ratio  = data.get("ratio", "4:5")

    if not prompt:
        return jsonify({"error": "prompt requerido"}), 400

    print(f"\n  Regen — Ratio: {ratio}")

    try:
        image_bytes = generate_image(prompt, ratio)
    except Exception as e:
        return jsonify({"error": f"Error generando imagen: {e}"}), 500

    return jsonify({
        "image": base64.b64encode(image_bytes).decode("utf-8"),
    })


if __name__ == "__main__":
    print(f"\n  AI Philosophy — Proxy v13 Flask / PORT {PORT}")
    app.run(host="0.0.0.0", port=PORT)
