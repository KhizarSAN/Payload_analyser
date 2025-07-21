from flask import Flask, render_template, request, jsonify
from parser import parse_payload, extract_critical_fields, flatten_dict
from normalizer import generate_soc_report
import json
import os
from gpt_analysis import analyze_payload_with_gpt

app = Flask(__name__)

def get_openai_api_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    # Fallback : lire la clé dans static/openai_key.txt
    try:
        with open(os.path.join("static", "openai_key.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    raw_payload = data.get("payload", "")
    try:
        import json
        payload_dict = json.loads(raw_payload)
    except Exception:
        payload_dict = parse_payload(raw_payload)
    # Extraction dynamique de tous les champs présents
    flat_fields = flatten_dict(payload_dict)
    soc_report = generate_soc_report(payload_dict)
    return jsonify({
        "summary": flat_fields,
        "parsed": payload_dict,
        "soc_report": soc_report
    })

@app.route("/analyze_ia", methods=["POST"])
def analyze_ia():
    data = request.get_json()
    raw_payload = data.get("payload", "")
    try:
        import json
        payload_dict = json.loads(raw_payload)
    except Exception:
        from parser import parse_payload
        payload_dict = parse_payload(raw_payload)
    api_key = get_openai_api_key()
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY non défini et static/openai_key.txt absent"}), 500
    result = analyze_payload_with_gpt(payload_dict, api_key)
    print("Réponse brute IA:", result)
    return jsonify({"ia_text": result})

@app.route("/exemples")
def exemples():
    # Charger les exemples depuis le fichier JSON
    exemples_path = os.path.join(os.path.dirname(__file__), "exemple.json")
    with open(exemples_path, encoding="utf-8") as f:
        exemples = json.load(f)
    return render_template("exemple.html", exemples=exemples)

if __name__ == "__main__":
    app.run(debug=True)
