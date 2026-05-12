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
    "flemish":     "Flemish Renaissance oil painting, rich jewel tones, dramatic chiaroscuro, intricate ornamental detail, Rubens and Van Eyck influence, monumental composition, aged impasto texture, deep shadows, luminous golden light, museum quality",
    "moreau":      "Gustave Moreau symbolist oil painting, mythological grandeur, dense ornamental surfaces, luminous jewel-like colors, dreamlike layered atmosphere, Pre-Raphaelite influence, mysterious narrative depth, jeweled figures, museum quality",
    "cinema":      "CINEMATIC — detect the cinematic register the concept demands and build from there. Available registers: (1) NOIR: urban night, hard shadows, wet streets, moral ambiguity, Blade Runner / Se7en aesthetic; (2) EPIC/SUBLIME: vast landscape, golden hour, lone figure OR massive crowd OR animal migration, Terrence Malick / Roger Deakins; (3) INTIMATE DRAMA: close interior, window light, human face or animal in private moment, Wong Kar-wai / Alfonso Cuarón; (4) DYSTOPIAN/SCI-FI: cold industrial light, surveillance, dehumanized space, Tarkovsky / Children of Men; (5) NEOREALISM: raw street, available light, unposed crowd or community, Cassavetes / Bicycle Thieves; (6) PSYCHOLOGICAL THRILLER: claustrophobic space, destabilizing angle, dread in ordinary setting, Kubrick / Haneke; (7) POLITICAL DRAMA: collective protest, institutional power, masses vs system, Loach / Costa-Gavras / Eisenstein. SUBJECT RANGE: do not default to solitary human figure. Always: anamorphic lens, 35mm film grain, cinematic color grading.",
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
CAPA 2 — ANCLAJE (filósofo, texto, o concepto técnico específico)
CAPA 3 — SUJETO:
  - colectivo_en_tension, animal, objeto_espacio, celeste, dualidad, monumental, figura_individual
  REGLA: figura_individual es el último recurso.
CAPA 4 — TERRITORIO: sublime | cotidiano | sociopolítico

REGISTRO EMOCIONAL — REGLA ESPECIAL:
Cuando el concepto tiene carga humana directa (madre, hijo, duelo, amor, familia):
  - Drama íntimo antes que político
  - Cotidiano o sublime emocional antes que sociopolítico
  - Cinematográfico → sub-registro INTIMATE DRAMA: Wong Kar-wai / Cuarón / Kiarostami

Responde SOLO con JSON válido, sin markdown:
{
  "tension": "la contradicción sin resolver",
  "anchor": "Filósofo/Concepto — contexto",
  "subject": "colectivo_en_tension|animal|objeto_espacio|celeste|dualidad|monumental|figura_individual",
  "subject_note": "descripción concreta — 10 palabras máximo",
  "territory": "sublime|cotidiano|sociopolítico",
  "core": "núcleo filosófico en español — una línea"
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
- Ejemplo bueno: "The line moves forward. No one remembers why."
- Ejemplo malo: "The enduring echo of foundational tales." — descriptivo, cierra

Responde SOLO con JSON válido, sin markdown:
{
  "prompt": "image prompt técnico en inglés — mínimo 80 palabras",
  "subtitle": "subtítulo en inglés — fractura — máximo 12 palabras"
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


def build_image_prompt(expanded, style, subtitle_override):
    style_desc = STYLES.get(style, STYLES["cinema"])
    user_msg = (
        f"TENSIÓN: {expanded['tension']}\n"
        f"ANCLAJE: {expanded['anchor']}\n"
        f"SUJETO: {expanded['subject']} — {expanded['subject_note']}\n"
        f"TERRITORIO: {expanded['territory']}\n"
        f"REGISTRO: {style_desc}\n"
    )
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
    font_size = max(24, int(W * 0.028))
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
    y_start = H - int(H * 0.06) - total_text_h
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

    concept  = data.get("concept", "").strip()
    style    = data.get("style", "cinema")
    ratio    = data.get("ratio", "4:5")
    subtitle = data.get("subtitle", "").strip()

    if not concept:
        return jsonify({"error": "concept requerido"}), 400

    print(f"\n  Concepto: {concept[:80]}")

    try:
        expanded = expand_concept(concept)
    except Exception as e:
        return jsonify({"error": f"Error expandiendo concepto: {e}"}), 500

    try:
        built = build_image_prompt(expanded, style, subtitle)
    except Exception as e:
        return jsonify({"error": f"Error construyendo prompt: {e}"}), 500

    final_subtitle = subtitle or built.get("subtitle", "")

    try:
        image_bytes = generate_image(built["prompt"], ratio)
    except Exception as e:
        return jsonify({"error": f"Error generando imagen: {e}"}), 500

    if final_subtitle:
        try:
            image_bytes = compose_subtitle(image_bytes, final_subtitle)
        except Exception as e:
            print(f"  Warning subtítulo: {e}")

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


if __name__ == "__main__":
    print(f"\n  AI Philosophy — Proxy v13 Flask / PORT {PORT}")
    app.run(host="0.0.0.0", port=PORT)
