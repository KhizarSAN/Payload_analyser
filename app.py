from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from parser import parse_payload, extract_critical_fields, flatten_dict
from normalizer import generate_soc_report
import json
import os
from gpt_analysis import analyze_payload_with_gpt, generate_short_summary
from mistral_local_analyzer import analyze_payload_with_mistral
from pattern_storage import store_analysis, find_existing_pattern, get_all_patterns
from auth import check_login_db, login_user, logout_user, is_logged_in
from db_config import SessionLocal, Analysis, Pattern, User, Log
from logger import log_action
from werkzeug.security import check_password_hash, generate_password_hash

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
        user = check_login_db(username, password)
        if user:
            login_user(session, user)
            log_action(user.id, "login_success", f"Connexion réussie pour {username}", request.remote_addr, request.headers.get('User-Agent'))
            return redirect(url_for("menu"))  # Redirige vers le menu quadrillé après login
        else:
            log_action(None, "login_failed", f"Connexion échouée pour {username}", request.remote_addr, request.headers.get('User-Agent'))
            error = "Identifiants invalides."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    username = session.get("username")
    log_action(user_id, "logout", f"Déconnexion de {username}", request.remote_addr, request.headers.get('User-Agent'))
    logout_user(session)
    return redirect(url_for("login"))

@app.route("/")
def root():
    if not is_logged_in(session):
        return redirect(url_for("login"))
    else:
        return redirect(url_for("menu"))

@app.route("/analyze")
def analyze():
    if not is_logged_in(session):
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/analyze_ia", methods=["POST"])
def analyze_ia():
    data = request.get_json()
    raw_payload = data.get("payload", "")
    custom_prompt = data.get("custom_prompt", None)
    user_id = session.get("user_id")
    try:
        payload_dict = json.loads(raw_payload)
    except Exception:
        from parser import parse_payload
        payload_dict = parse_payload(raw_payload)
    from parser import flatten_dict
    flat_fields = flatten_dict(payload_dict)
    pattern_nom = flat_fields.get("pattern", "unknown_pattern")
    api_key = get_openai_api_key()
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY non défini et static/openai_key.txt absent"}), 500
    from gpt_analysis import analyze_payload_with_gpt
    ia_response = analyze_payload_with_gpt(payload_dict, api_key, custom_prompt=custom_prompt)
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
    justification = resultat
    if not statut and resultat:
        if re.search(r'faux positif', resultat, re.IGNORECASE):
            statut = "Faux positif"
        elif re.search(r'positif[\s_-]*confirm[ée]', resultat, re.IGNORECASE):
            statut = "Vrai positif"
    if not statut:
        statut = "Non identifié"
    user_intent = data.get("user_intent", "")
    if user_intent == "faux_positif":
        statut = "Faux positif"
    elif user_intent == "positif_confirme":
        statut = "Vrai positif"
    elif user_intent:
        statut = user_intent
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
    log_action(user_id, "analyze_ia", f"Pattern: {extracted_pattern}", request.remote_addr, request.headers.get('User-Agent'))
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
    if not is_logged_in(session):
        return redirect(url_for("login"))
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

@app.route("/analyses_history")
def analyses_history():
    if not is_logged_in(session):
        return redirect(url_for("login"))
    db = SessionLocal()
    analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).all()
    db.close()
    return render_template("analyses_history.html", analyses=analyses)

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
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    data = request.get_json()
    pattern_id = data.get("pattern_id")
    db = SessionLocal()
    pattern = db.query(Pattern).filter_by(id=pattern_id).first()
    if not pattern:
        db.close()
        return jsonify({"error": "Pattern introuvable"}), 404
    db.delete(pattern)
    db.commit()
    db.close()
    log_action(session["user_id"], "delete_pattern", f"Suppression du pattern id={pattern_id}", request.remote_addr, request.headers.get('User-Agent'))
    return jsonify({"success": True})

@app.route("/clear_history", methods=["POST"])
def clear_history():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    db = SessionLocal()
    deleted = db.query(Analysis).delete()
    db.commit()
    db.close()
    log_action(session["user_id"], "clear_history", f"Suppression de {deleted} analyses", request.remote_addr, request.headers.get('User-Agent'))
    return jsonify({"success": True, "deleted": deleted})

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

@app.route("/api/profile", methods=["GET"])
def get_profile():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    db = SessionLocal()
    user = db.query(User).filter_by(id=session["user_id"]).first()
    db.close()
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 404
    return jsonify({
        "username": user.username,
        "email": user.email,
        "role": user.role
    })

@app.route("/api/profile", methods=["POST"])
def update_profile():
    if not is_logged_in(session):
        log_action(None, "update_profile_failed", "Tentative de modification sans être connecté", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": "Non authentifié"}), 401
    data = request.get_json()
    db = SessionLocal()
    user = db.query(User).filter_by(id=session["user_id"]).first()
    if not user:
        log_action(session["user_id"], "update_profile_failed", "Utilisateur introuvable", request.remote_addr, request.headers.get('User-Agent'))
        db.close()
        return jsonify({"error": "Utilisateur introuvable"}), 404
    old_username = user.username
    old_email = user.email
    old_role = user.role
    user.username = data.get("username", user.username)
    user.email = data.get("email", user.email)
    user.role = data.get("role", user.role)
    db.commit()
    log_action(session["user_id"], "update_profile", f"Ancien nom: {old_username}, Nouveau nom: {user.username}, Ancien email: {old_email}, Nouveau email: {user.email}, Ancien rôle: {old_role}, Nouveau rôle: {user.role}", request.remote_addr, request.headers.get('User-Agent'))
    db.close()
    return jsonify({"success": True})

@app.route("/api/profile/password", methods=["POST"])
def update_password():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    data = request.get_json()
    current_password = data.get("currentPassword")
    new_password = data.get("newPassword")
    db = SessionLocal()
    user = db.query(User).filter_by(id=session["user_id"]).first()
    if not user:
        db.close()
        return jsonify({"error": "Utilisateur introuvable"}), 404
    if not check_password_hash(user.password_hash, current_password):
        db.close()
        log_action(session["user_id"], "change_password_failed", "Mot de passe actuel incorrect", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": "Mot de passe actuel incorrect"}), 400
    if not new_password or len(new_password) < 8:
        db.close()
        log_action(session["user_id"], "change_password_failed", "Nouveau mot de passe trop court", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": "Le nouveau mot de passe doit contenir au moins 8 caractères."}), 400
    user.password_hash = generate_password_hash(new_password)
    db.commit()
    db.close()
    log_action(session["user_id"], "change_password", "Mot de passe changé avec succès", request.remote_addr, request.headers.get('User-Agent'))
    return jsonify({"success": True})

@app.route("/logs")
def logs():
    if not is_logged_in(session):
        return redirect(url_for("login"))
    db = SessionLocal()
    user = db.query(User).filter_by(id=session["user_id"]).first()
    if not user or user.role != "admin":
        db.close()
        return "Accès refusé : réservé aux administrateurs.", 403
    logs = db.query(Log).order_by(Log.created_at.desc()).all()
    users = {u.id: u.username for u in db.query(User).all()}
    db.close()
    return render_template("logs.html", logs=logs, users=users)

@app.route("/menu")
def menu():
    if not is_logged_in(session):
        return redirect(url_for("login"))
    return render_template("menu.html")

@app.route("/settings")
def settings():
    if not is_logged_in(session):
        return redirect(url_for("login"))
    return render_template("settings.html")

@app.route("/api/user_stats")
def user_stats():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    db = SessionLocal()
    user_id = session["user_id"]
    # Temps passé = différence entre première connexion et dernière action
    logs = db.query(Log).filter_by(user_id=user_id).order_by(Log.created_at).all()
    if logs:
        t0 = logs[0].created_at
        t1 = logs[-1].created_at
        delta = t1 - t0
        hours = delta.total_seconds() // 3600
        minutes = (delta.total_seconds() % 3600) // 60
        time_spent = f"{int(hours)}h {int(minutes)}min"
    else:
        time_spent = "0h"
    # Analyses IA
    ia_analyses = db.query(Analysis).filter_by(user_id=user_id).filter(Analysis.rapport_complet != None).count()
    # Analyses classiques (sans IA)
    normal_analyses = db.query(Analysis).filter_by(user_id=user_id).filter(Analysis.rapport_complet == None).count()
    db.close()
    return jsonify({
        "time_spent": time_spent,
        "ia_analyses": ia_analyses,
        "normal_analyses": normal_analyses
    })

if __name__ == "__main__":
    app.run(debug=True)
