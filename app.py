from flask import Flask, render_template, request, jsonify
from parser import parse_payload, extract_critical_fields
from normalizer import generate_soc_report
import json
import os

app = Flask(__name__)

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    raw_payload = data.get("payload", "")
    try:
        payload_dict = json.loads(raw_payload)
    except Exception:
        payload_dict = parse_payload(raw_payload)
    summary = extract_critical_fields(payload_dict)
    soc_report = generate_soc_report(payload_dict)
    return jsonify({
        "summary": summary,
        "parsed": payload_dict,
        "soc_report": soc_report
    })

@app.route("/exemples")
def exemples():
    # Charger les exemples depuis le fichier JSON
    exemples_path = os.path.join(os.path.dirname(__file__), "exemple.json")
    with open(exemples_path, encoding="utf-8") as f:
        exemples = json.load(f)
    return render_template("exemple.html", exemples=exemples)

if __name__ == "__main__":
    app.run(debug=True)
