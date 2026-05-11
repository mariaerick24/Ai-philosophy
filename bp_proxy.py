#!/usr/bin/env python3
"""
AI Philosophy — Proxy v13 (Production)
Deploy: Railway / Render
API keys via environment variables.
"""

import json
import base64
import time
import io
import os
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from PIL import Image, ImageDraw, ImageFont

# ── API keys desde variables de entorno (nunca hardcodeadas en producción) ──
GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY", "")
REPLICATE_TOKEN = os.environ.get("REPLICATE_TOKEN", "")

GEMINI_FLASH_URL = (
    "https://generativelanguage.googleapis.com/v1beta"
    "/models/gemini-2.5-flash:generateContent"
)
REPLICATE_API = "https://api.replicate.com/v1"
FLUX_MODEL    = "black-forest-labs/flux-schnell"

PORT = int(os.environ.get("PORT", 5555))

STYLES = {
    "flemish":     "Flemish Renaissance oil painting, rich jewel tones, dramatic chiaroscuro, intricate ornamental detail, Rubens and Van Eyck influence, monumental composition, aged impasto texture, deep shadows, luminous golden light, museum quality",
    "moreau":      "Gustave Moreau symbolist oil painting, mythological grandeur, dense ornamental surfaces, luminous jewel-like colors, dreamlike layered atmosphere, Pre-Raphaelite influence, mysterious narrative depth, jeweled figures, museum quality",
    "cinema":      "CINEMATIC — detect the cinematic register the concept demands and build from there. Available registers: (1) NOIR: urban night, hard shadows, wet streets, moral ambiguity, Blade Runner / Se7en aesthetic; (2) EPIC/SUBLIME: vast landscape, golden hour, lone figure OR massive crowd OR animal migration, Terrence Malick / Roger Deakins; (3) INTIMATE DRAMA: close interior, window light, human face or animal in private moment, Wong Kar-wai / Alfonso Cuarón; (4) DYSTOPIAN/SCI-FI: cold industrial light, surveillance, dehumanized space, Tarkovsky / Children of Men; (5) NEOREALISM: raw street, available light, unposed crowd or community, Cassavetes / Bicycle Thieves; (6) PSYCHOLOGICAL THRILLER: claustrophobic space, destabilizing angle, dread in ordinary setting, Kubrick / Haneke; (7) POLITICAL DRAMA: collective protest, institutional power, masses vs system, Loach / Costa-Gavras / Eisenstein. SUBJECT RANGE — do not default to solitary human figure. Consider: animal subjects (single or herd), human collectives (crowds, communities, masses, families), non-human natural forces, urban multitudes, animal-human coexistence. CELESTIAL SUBJECTS: moon over city or landscape, star fields above human activity, night sky as philosophical backdrop. The concept dictates the subject and scale. Always: anamorphic lens, 35mm film grain, cinematic color grading.",
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
No resumes el concepto — lo abres. Buscas la contradicción interna, el problema sin resolver.

CUATRO CAPAS QUE DEBES PRODUCIR:

CAPA 1 — TENSIÓN (no tema, sino contradicción sin resolver)
  No: "el tiempo"
  Sí: "cosas que existen solo porque creemos en ellas, aunque nadie pueda probarlas"
  No: "la justicia"  
  Sí: "sistemas diseñados para proteger que terminan protegiendo solo a quienes los diseñaron"

CAPA 2 — ANCLAJE (filósofo, texto, o concepto técnico específico)
  No para citar — para tener coordenadas precisas.
  Ejemplos válidos: Sorel/mito político, Benjamin/estado de excepción, 
  Simone Weil/affliction, Fanon/colonialismo interiorizado, 
  Arendt/banalidad del mal, Bourdieu/violencia simbólica,
  Wittgenstein/límites del lenguaje, Camus/absurdo, etc.

CAPA 3 — SUJETO (quién o qué porta la tensión visualmente)
  Elige uno — el que la tensión pide, no el más obvio:
  - colectivo_en_tension: multitud, fila, grupo fragmentado, masa
  - animal: un animal como protagonista filosófico (no decorativo)
  - objeto_espacio: lugar o cosa sin figura humana
  - celeste: escala no-humana, cosmos, fenómeno natural
  - dualidad: par en tensión, dos elementos opuestos
  - monumental: escultura, arquitectura, obra de arte, monumento —
    el objeto cultural como portador de la tensión filosófica.
    Válido cuando el concepto tiene peso histórico, estético o civilizatorio.
    Ejemplos: una estatua sin cabeza, una catedral vacía, un fresco deteriorado,
    un arco triunfal abandonado, una escultura inacabada, un mural borrado.
  - figura_individual: solo cuando la tensión es genuinamente sobre la soledad interior
  
  REGLA: figura_individual es el último recurso, no el primero.

CAPA 4 — TERRITORIO
  sublime | cotidiano | sociopolítico
  El que la tensión pide, no el más fotogénico.

REGISTRO EMOCIONAL — REGLA ESPECIAL:
Cuando el concepto tiene carga humana directa (madre, hijo, infancia, duelo,
amor, cuerpo, pérdida, familia, vínculo, nacimiento, vejez, ternura):
  - Priorizar drama íntimo sobre drama político o institucional
  - Territorio cotidiano o sublime emocional ANTES que sociopolítico
  - La escala humana antes que la escala institucional
  - Si el registro es cinematográfico → sub-registro INTIMATE DRAMA:
    Wong Kar-wai / Alfonso Cuarón / Abbas Kiarostami — NO Loach / Eisenstein
  - La tensión filosófica debe surgir del vínculo, no de la estructura social
  - El subtítulo puede ser provocativo o emotivo — no solo conceptual

Responde SOLO con JSON válido, sin markdown:
{
  "tension": "la contradicción sin resolver, en una frase larga y específica",
  "anchor": "Filósofo/Concepto — una línea de contexto",
  "subject": "colectivo_en_tension|animal|objeto_espacio|celeste|dualidad|monumental|figura_individual",
  "subject_note": "descripción concreta de qué sujeto específico — 10 palabras máximo",
  "territory": "sublime|cotidiano|sociopolítico",
  "core": "núcleo filosófico en español — una línea, no descripción sino apertura"
}"""

IMAGE_SYSTEM = """Eres el constructor visual de AI Philosophy.

Recibes una tensión filosófica estructurada en 4 capas y debes producir:
1. Un IMAGE PROMPT técnico y concreto para Flux Schnell
2. Un SUBTITLE que funcione como fractura, no como descripción

REGLAS DEL IMAGE PROMPT:
- Concreto y específico — sin adjetivos abstractos ("profound", "meaningful", "deep")
- Describe luz, composición, sujeto, atmósfera con precisión cinematográfica
- El sujeto viene dado — úsalo. No lo reemplaces por figura solitaria masculina por default
- El registro visual viene dado — aplícalo
- Sin texto en la imagen
- Mínimo 80 palabras

ILUMINACIÓN — evitar por defecto:
- luz dorada de atardecer como solución estética fácil
- sol visible en frame como elemento dramático
- cielo naranja/dorado como fondo
Preferir según lo que el concepto pide, no lo que el modelo prefiere:
luz difusa, overcast, interior, nocturna, contraluz frío,
neblina, luz artificial, amanecer frío, sombra dura urbana.
La luz dorada solo si el concepto la justifica explícitamente.

REGLAS DEL SUBTITLE:
- Máximo 12 palabras
- NO describe lo que se ve en la imagen
- NO es una cita de filósofo
- Abre una grieta — algo que interrumpe, no que cierra
- Debe poder existir sin la imagen
- La imagen debe poder existir sin el subtítulo
- Juntos crean un tercer significado que ninguno tiene solo

EJEMPLOS DE SUBTÍTULOS QUE FUNCIONAN:
  "What holds us together may be what never happened."
  "The line moves forward. No one remembers why."
  "We inherited the wound. We also inherited the silence."
  "It was called order. It looked exactly like this."

EJEMPLOS QUE NO FUNCIONAN:
  "The enduring echo of foundational tales." — poético pero descriptivo, cierra
  "Time passes and we forget." — genérico, sin filo
  "In the shadow of ancient structures..." — describe la imagen

Responde SOLO con JSON válido, sin markdown:
{
  "prompt": "image prompt técnico completo en inglés para Flux Schnell — mínimo 80 palabras",
  "subtitle": "subtítulo en inglés — fractura, no descripción — máximo 12 palabras"
}"""


def expand_concept(concept: str) -> dict:
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
        raise Exception(f"Gemini expander error {resp.status_code}: {resp.text[:200]}")
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text.replace("```json", "").replace("```", "").strip())


def build_image_prompt(expanded: dict, style: str, subtitle_override: str) -> dict:
    style_desc = STYLES.get(style, STYLES["cinema"])
    user_msg = (
        f"TENSIÓN FILOSÓFICA: {expanded['tension']}\n"
        f"ANCLAJE: {expanded['anchor']}\n"
        f"SUJETO: {expanded['subject']} — {expanded['subject_note']}\n"
        f"TERRITORIO: {expanded['territory']}\n"
        f"REGISTRO VISUAL: {style_desc}\n"
    )
    if subtitle_override:
        user_msg += f"\nSUBTÍTULO DEL ARTISTA (usa este exactamente): {subtitle_override}\n"
    else:
        user_msg += "\nSUBTÍTULO: genera uno según las reglas — fractura, no descripción.\n"

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
        raise Exception(f"Gemini image builder error {resp.status_code}: {resp.text[:200]}")
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text.replace("```json", "").replace("```", "").strip())


def generate_image(prompt: str, ratio: str) -> bytes:
    width, height = RATIO_MAP.get(ratio, (1344, 768))
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
        for i in range(90):
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
        raise Exception(f"Error descargando: {img_resp.status_code}")
    return img_resp.content


def compose_subtitle(image_bytes: bytes, subtitle: str) -> bytes:
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
    font_size = max(24, int(W * 0.028))
    font = None
    for path in [
        "C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/Georgia.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/System/Library/Fonts/Times.ttc",
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
    y_start = H - int(H * 0.06) - total_text_h
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        y = y_start + i * line_height
        draw.text((x + 1, y + 1), line, font=font, fill=(0, 0, 0, 160))
        draw.text((x, y), line, font=font, fill=(232, 224, 208, 220))
    result = img.convert("RGB")
    buf = io.BytesIO()
    result.save(buf, format="PNG")
    return buf.getvalue()


class ProxyHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        # Health check para Railway/Render
        if self.path == "/health":
            self._respond(200, {"status": "ok"})
        else:
            self._respond(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/generate":
            self._respond(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except Exception:
            self._respond(400, {"error": "JSON inválido"})
            return

        concept  = data.get("concept", "").strip()
        style    = data.get("style", "cinema")
        ratio    = data.get("ratio", "16:9")
        subtitle = data.get("subtitle", "").strip()

        if not concept:
            self._respond(400, {"error": "concept requerido"})
            return

        print(f"\n  Concepto: {concept[:80]}")
        print(f"  Ratio: {ratio} — Estilo: {style}")

        print(f"  [1/3] Expandiendo tensión filosófica...")
        try:
            expanded = expand_concept(concept)
        except Exception as e:
            self._respond(500, {"error": f"Error expandiendo concepto: {e}"})
            return

        print(f"  Tensión: {expanded.get('tension', '—')[:80]}")
        print(f"  Territorio: {expanded.get('territory', '—')}")

        print(f"  [2/3] Construyendo prompt de imagen...")
        try:
            built = build_image_prompt(expanded, style, subtitle)
        except Exception as e:
            self._respond(500, {"error": f"Error construyendo prompt: {e}"})
            return

        final_subtitle = subtitle or built.get("subtitle", "")

        print(f"  [3/3] Generando imagen...")
        try:
            image_bytes = generate_image(built["prompt"], ratio)
        except Exception as e:
            self._respond(500, {"error": f"Error generando imagen: {e}"})
            return

        if final_subtitle:
            try:
                image_bytes = compose_subtitle(image_bytes, final_subtitle)
            except Exception as e:
                print(f"  Warning subtítulo: {e}")

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        print(f"  Listo.")

        self._respond(200, {
            "image":     image_b64,
            "prompt":    built.get("prompt", ""),
            "core":      expanded.get("core", ""),
            "territory": expanded.get("territory", "—"),
            "tension":   expanded.get("tension", ""),
            "anchor":    expanded.get("anchor", ""),
            "subject":   expanded.get("subject", ""),
            "subtitle":  final_subtitle,
        })

    def _respond(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    print(f"\n  AI Philosophy — Proxy v13 (Production)")
    print(f"  PORT: {PORT}")
    server = HTTPServer(("0.0.0.0", PORT), ProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Proxy detenido.")
