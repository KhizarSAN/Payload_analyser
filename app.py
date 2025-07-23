from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from parser import parse_payload, extract_critical_fields, flatten_dict
from normalizer import generate_soc_report
import json
import os
from gpt_analysis import analyze_payload_with_gpt, generate_short_summary
from mistral_local_analyzer import analyze_payload_with_mistral
from pattern_storage import store_analysis, find_existing_pattern, get_all_patterns
from auth import check_login, login_user, logout_user, is_logged_in
from db_config import SessionLocal, Analysis, Pattern, User
from logger import log_action
from werkzeug.security import generate_password_hash

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
    db = SessionLocal()
    analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).limit(50).all()
    db.close()
    return render_template("dashboard.html", analyses=analyses)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    raw_payload = data.get("payload", "")
    try:
        payload_dict = json.loads(raw_payload)
    except Exception:
        payload_dict = parse_payload(raw_payload)
    # Extraction dynamique de tous les champs présents
    flat_fields = flatten_dict(payload_dict)
    soc_report = generate_soc_report(payload_dict)
    return jsonify({
        "summary": flat_fields,
        "parsed": payload_dict,
    })

@app.route("/analyze_ia", methods=["POST"])
def analyze_ia():
    data = request.get_json()
    raw_payload = data.get("payload", "")
    custom_prompt = data.get("custom_prompt", None)
    user_id = session.get("user_id")  # Si tu gères l'authentification
    try:
        payload_dict = json.loads(raw_payload)
    except Exception:
        from parser import parse_payload
        payload_dict = parse_payload(raw_payload)

    # 1. Extraction des champs utiles
    from parser import flatten_dict
    flat_fields = flatten_dict(payload_dict)
    pattern_nom = flat_fields.get("pattern", "unknown_pattern")

    # 2. Appel IA
    api_key = get_openai_api_key()
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY non défini et static/openai_key.txt absent"}), 500
    from gpt_analysis import analyze_payload_with_gpt
    ia_response = analyze_payload_with_gpt(payload_dict, api_key, custom_prompt=custom_prompt)

    # 3. Extraction stricte des champs de la réponse IA
    import re
    pattern_match = re.search(r'Pattern du payload\s*[:：\-–]?\s*([^\n]{1,50})', ia_response)
    short_desc_match = re.search(r'Résumé court\s*[:：\-–]?\s*([^\n]{1,120})', ia_response)
    statut_match = re.search(r'Statut\s*[:：\-–]?\s*([^\n]{1,50})', ia_response)
    description_match = re.search(r'1\. Description des faits\s*\n(.+?)\n2\.', ia_response, re.DOTALL)
    analyse_technique_match = re.search(r'2\. Analyse technique\s*\n(.+?)\n3\.', ia_response, re.DOTALL)
    resultat_match = re.search(r'3\. Résultat\s*\n(.+)', ia_response, re.DOTALL)

    extracted_pattern = pattern_match.group(1).strip() if pattern_match else pattern_nom
    resume_court = short_desc_match.group(1).strip() if short_desc_match else ""
    statut = statut_match.group(1).strip() if statut_match else ""
    description_faits = description_match.group(1).strip() if description_match else ""
    analyse_technique = analyse_technique_match.group(1).strip() if analyse_technique_match else ""
    resultat = resultat_match.group(1).strip() if resultat_match else ""
    justification = resultat  # Ou extraire une justification spécifique si besoin

    # Fallback si statut non trouvé, on cherche dans le résultat
    if not statut and resultat:
        if re.search(r'faux positif', resultat, re.IGNORECASE):
            statut = "Faux positif"
        elif re.search(r'positif[\s_-]*confirm[ée]', resultat, re.IGNORECASE):
            statut = "Vrai positif"
    if not statut:
        statut = "Non identifié"

    # Prise en compte de l'intention utilisateur si présente
    user_intent = data.get("user_intent", "")
    if user_intent == "faux_positif":
        statut = "Faux positif"
    elif user_intent == "positif_confirme":
        statut = "Vrai positif"
    elif user_intent:
        statut = user_intent

    # 4. Stockage en base
    from pattern_storage import store_analysis
    store_analysis(
        payload=raw_payload,
        rapport_ia=ia_response,
        pattern_nom=extracted_pattern,
        resume_court=resume_court,
        description_faits=description_faits,
        analyse_technique=analyse_technique,
        resultat=resultat,
        justification=justification,
        user_id=user_id,
        tags=None,
        statut=statut
    )
    log_action(user_id, "analyse_ia", f"Pattern: {extracted_pattern}", request.remote_addr, request.headers.get('User-Agent'))

    # 5. Restitution complète pour le JS
    return jsonify({
        "ia_text": ia_response,
        "pattern": extracted_pattern,
        "short_description": resume_court,
        "result": resultat,
        "analyse_technique": analyse_technique,
        "description_faits": description_faits,
        "statut": statut,
        "summary": flat_fields,
        "parsed": payload_dict
    })

@app.route("/save_pattern", methods=["POST"])
def save_pattern():
    data = request.get_json()
    pattern_nom = data.get("pattern", "")
    short_description = data.get("short_description", "")
    analyse_technique = data.get("analyse_technique", "")
    result = data.get("result", "")
    feedback = data.get("feedback", "")
    tags = data.get("tags", [])
    input_payload = data.get("input", "")
    statut = data.get("statut", None)  # transmis par l'utilisateur

    from pattern_storage import store_analysis
    store_analysis(
        payload=input_payload,
        rapport_ia=result,
        pattern_nom=pattern_nom,
        resume_court=short_description,
        description_faits="",  # à remplir si tu veux
        analyse_technique=analyse_technique,
        resultat=result,
        justification=result,
        user_id=session.get("user_id"),
        tags=tags,
        statut=statut
    )
    log_action(session.get("user_id"), "save_pattern", f"Pattern: {pattern_nom}", request.remote_addr, request.headers.get('User-Agent'))
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
    db = SessionLocal()
    exemples = db.query(Pattern).all()
    db.close()
    return render_template("exemple.html", exemples=exemples)

@app.route("/patterns_history")
def patterns_history():
    db = SessionLocal()
    patterns = db.query(Pattern).order_by(Pattern.created_at.desc()).all()
    patterns_list = []
    for p in patterns:
        last_analysis = db.query(Analysis).filter_by(pattern_id=p.id).order_by(Analysis.created_at.desc()).first()
        user = db.query(User).filter_by(id=last_analysis.user_id).first() if last_analysis else None
        patterns_list.append({
            "pattern": p.nom,
            "status": last_analysis.statut if last_analysis and hasattr(last_analysis, 'statut') else "",
            "user": user.username if user else "N/A",
            "tags": p.tags.split(",") if hasattr(p, 'tags') and p.tags else [],
            "feedbacks": [],
            "short_description": (last_analysis.resume_court if last_analysis else p.resume) or "",
            "analyse_technique": last_analysis.analyse_technique if last_analysis else (p.description or ""),
            "result": last_analysis.resultat if last_analysis else "",
            "input": last_analysis.payload if last_analysis else "",
            "date": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "",
        })
    db.close()
    return jsonify(patterns_list)

@app.route("/export_patterns_history")
def export_patterns_history():
    db = SessionLocal()
    patterns = db.query(Pattern).order_by(Pattern.created_at.desc()).all()
    patterns_list = []
    for p in patterns:
        last_analysis = db.query(Analysis).filter_by(pattern_id=p.id).order_by(Analysis.created_at.desc()).first()
        patterns_list.append({
            "pattern": p.nom,
            "status": "",
            "tags": p.tags.split(",") if hasattr(p, 'tags') and p.tags else [],
            "feedbacks": [],
            "short_description": (last_analysis.resume_court if last_analysis else p.resume) or "",
            "analyse_technique": last_analysis.analyse_technique if last_analysis else (p.description or ""),
            "result": last_analysis.resultat if last_analysis else "",
            "input": last_analysis.payload if last_analysis else "",
            "date": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "",
        })
    db.close()
    from flask import Response
    import json
    return Response(
        json.dumps(patterns_list, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=historique_patterns.json"}
    )

@app.route("/analyses_history_json")
def analyses_history_json():
    db = SessionLocal()
    analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).all()
    analyses_list = []
    for a in analyses:
        user = db.query(User).filter_by(id=a.user_id).first() if a.user_id else None
        analyses_list.append({
            "id": a.id,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else "",
            "pattern_nom": a.pattern_nom,
            "resume_court": a.resume_court,
            "resultat": a.resultat,
            "user": user.username if user else "N/A",
            "rapport_complet": a.rapport_complet,
            "statut": a.statut,
        })
    db.close()
    return jsonify(analyses_list)

@app.route("/delete_pattern", methods=["DELETE"])
def delete_pattern():
    pattern_nom = request.args.get("pattern")
    if not pattern_nom:
        return jsonify({"error": "pattern manquant"}), 400
    db = SessionLocal()
    pattern = db.query(Pattern).filter_by(nom=pattern_nom).first()
    if pattern:
        db.delete(pattern)
        db.commit()
        log_action(session.get("user_id"), "delete_pattern", f"Pattern: {pattern_nom}", request.remote_addr, request.headers.get('User-Agent'))
        db.close()
        return jsonify({"status": "ok"})
    db.close()
    return jsonify({"error": "Pattern non trouvé"}), 404

@app.route("/clear_history", methods=["POST"])
def clear_history():
    db = SessionLocal()
    db.query(Pattern).delete()
    db.commit()
    log_action(session.get("user_id"), "clear_history", "", request.remote_addr, request.headers.get('User-Agent'))
    db.close()
    return jsonify({"status": "ok"})

@app.route("/user_profile")
def user_profile():
    if not is_logged_in(session):
        return redirect(url_for("login"))
    user_id = session.get("user_id")
    db = SessionLocal()
    user = db.query(User).filter_by(id=user_id).first()
    db.close()
    return render_template("user_profile.html", user=user)

@app.route("/update_user", methods=["POST"])
def update_user():
    if not is_logged_in(session):
        return jsonify({"error": "Non autorisé"}), 401
    user_id = session.get("user_id")
    data = request.get_json()
    db = SessionLocal()
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        db.close()
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    # Mise à jour des champs
    user.username = data.get("username", user.username)
    user.email = data.get("email", user.email)
    if data.get("password"):
        user.password_hash = generate_password_hash(data["password"])
    db.commit()
    db.close()
    return jsonify({"status": "ok", "message": "Profil mis à jour"})

@app.route("/menu")
def menu():
    return render_template("menu.html")

if __name__ == "__main__":
    app.run(debug=True)
