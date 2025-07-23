from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from parser import parse_payload, extract_critical_fields, flatten_dict
from normalizer import generate_soc_report
import json
import os
from gpt_analysis import analyze_payload_with_gpt, generate_short_summary
from mistral_local_analyzer import analyze_payload_with_mistral
from pattern_storage import save_analysis, find_existing_pattern, load_data, save_data
from auth import check_login, login_user, logout_user, is_logged_in

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'  # Nécessaire pour les sessions Flask

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

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if check_login(username, password):
            login_user(session)
            return redirect(url_for("dashboard"))
        else:
            error = "Identifiants invalides."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    logout_user(session)
    return redirect(url_for("login"))

@app.route("/")
def dashboard():
    if not is_logged_in(session):
        return redirect(url_for("login"))
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
    custom_prompt = data.get("custom_prompt", None)
    user_intent = data.get("user_intent", "")
    try:
        import json
        payload_dict = json.loads(raw_payload)
    except Exception:
        from parser import parse_payload
        payload_dict = parse_payload(raw_payload)
    api_key = get_openai_api_key()
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY non défini et static/openai_key.txt absent"}), 500
    flat_fields = flatten_dict(payload_dict)
    pattern = flat_fields.get("pattern", "unknown_pattern")
    existing = find_existing_pattern(pattern)
    context = ""
    if existing:
        feedbacks = existing.get('feedbacks', [])
        tags = existing.get('tags', [])
        status = existing.get('status', '')
        context += f"[INFO] Ce pattern a déjà été rencontré.\n"
        if status:
            context += f"Statut : {status}\n"
        if tags:
            context += f"Tags : {', '.join(tags)}\n"
        if feedbacks:
            context += "Historique des feedbacks :\n"
            for fb in feedbacks:
                context += f"- {fb.get('date','')} | {fb.get('type','')} | {fb.get('comment','')}\n"
        context += "\n"
    # Injection de l'intention utilisateur dans le contexte
    if user_intent == "faux_positif":
        context += "L'utilisateur pense que ce log est un faux positif. Prends-le en compte dans ton analyse.\n"
    elif user_intent == "positif_confirme":
        context += "L'utilisateur pense que ce log est un positif confirmé. Prends-le en compte dans ton analyse.\n"
    prompt_payload = payload_dict.copy()
    if context:
        prompt_payload['__pattern_context'] = context
    result = analyze_payload_with_gpt(prompt_payload, api_key, custom_prompt=custom_prompt, context=context)
    # Extraction stricte du pattern et du résumé court
    import re
    pattern_match = re.search(r'Pattern du payload\s*[:：\-–]?\s*([^\n]{1,50})', result)
    short_desc_match = re.search(r'Résumé court\s*[:：\-–]?\s*([^\n]{1,120})', result)
    extracted_pattern = pattern_match.group(1).strip() if pattern_match else ''
    extracted_short_desc = short_desc_match.group(1).strip() if short_desc_match else ''
    # Fallback si extraction échoue
    if not extracted_pattern:
        extracted_pattern = flat_fields.get('pattern', '')[:50]
    if not extracted_short_desc:
        extracted_short_desc = result.split('. ')[0][:120]
    short_description = extracted_short_desc
    if context:
        result = context + result
    print("Réponse brute IA:", result)
    return jsonify({
        "ia_text": result,
        "summary": flat_fields,
        "parsed": payload_dict,
        "short_description": short_description,
        "pattern": extracted_pattern
    })

@app.route("/save_pattern", methods=["POST"])
def save_pattern():
    data = request.get_json()
    # On attend tous les champs nécessaires dans data
    entry = {
        "input": data.get("input", ""),
        "pattern": data.get("pattern", "unknown_pattern"),
        "result": data.get("result", ""),
        "analyse_technique": data.get("analyse_technique", ""),
        "short_description": data.get("short_description", ""),
        "feedback": data.get("feedback", ""),
        "tags": data.get("tags", []),
        "status": data.get("status", "")
    }
    save_analysis(entry)
    return jsonify({"status": "ok", "message": "Pattern sauvegardé"})

@app.route("/analyze_mistral", methods=["POST"])
def analyze_mistral():
    data = request.get_json()
    raw_payload = data.get("payload", "")
    try:
        import json
        payload_dict = json.loads(raw_payload)
    except Exception:
        from parser import parse_payload
        payload_dict = parse_payload(raw_payload)
    result = analyze_payload_with_mistral(payload_dict)
    if result.startswith("[ERREUR MISTRAL]"):
        return jsonify({"error": result}), 500
    print("Réponse brute Mistral:", result)
    return jsonify({"mistral_text": result})

@app.route("/exemples")
def exemples():
    exemples = load_data()
    return render_template("exemple.html", exemples=exemples)

@app.route("/patterns_history")
def patterns_history():
    data = load_data()
    return jsonify(data)

@app.route("/delete_pattern", methods=["DELETE"])
def delete_pattern():
    pattern = request.args.get("pattern")
    if not pattern:
        return {"error": "pattern manquant"}, 400
    data = load_data()
    new_data = [entry for entry in data if entry.get("pattern") != pattern]
    save_data(new_data)
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(debug=True)
