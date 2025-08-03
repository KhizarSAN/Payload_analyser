import time
import os
import pymysql as MySQLdb
import base64
import requests
from datetime import datetime, timezone
from io import BytesIO
from PIL import Image

# Logs de diagnostic au démarrage
print("🚀 Démarrage de l'application QRadar Ticket Analyzer...")
print(f"📁 Répertoire de travail: {os.getcwd()}")
print(f"🐍 Version Python: {os.sys.version}")

def wait_for_mysql():
    print("⏳ Attente de la connexion MySQL...")
    max_attempts = 30
    attempt = 0
    while attempt < max_attempts:
        try:
            conn = MySQLdb.connect(
                host=os.getenv('DB_HOST', 'db'),
                user=os.getenv('DB_USER', 'root'),
                passwd=os.getenv('DB_PASSWORD', 'root'),
                db=os.getenv('DB_NAME', 'payload_analyser'),
                connect_timeout=2
            )
            conn.close()
            print("✅ MySQL est prêt !")
            return
        except Exception as e:
            attempt += 1
            print(f"⏳ Attente de MySQL... ({attempt}/30) : {e}")
            time.sleep(2)
    print("❌ MySQL n'est pas prêt après 30 tentatives.")
    exit(1)

print("🔌 Test de connexion MySQL...")
wait_for_mysql()

print("📦 Import des modules Flask...")
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
print("✅ Modules Flask importés")

print("🔧 Import des modules personnalisés...")
from parser import parse_payload, extract_critical_fields, flatten_dict
from normalizer import generate_soc_report
import json
import os
from gpt_analysis import analyze_payload_with_gpt, generate_short_summary
# from mistral_local_analyzer import analyze_payload_with_mistral  # Supprimé - remplacé par TGI
from pattern_storage import store_analysis, find_existing_pattern, get_all_patterns
from auth import check_login_db, login_user, logout_user, is_logged_in
from db_config import init_db, SessionLocal, Analysis, Pattern, User, Log
from logger import log_action, log_error, log_warning, log_success
from werkzeug.security import check_password_hash, generate_password_hash
print("✅ Modules personnalisés importés")

app = Flask(__name__)
app.secret_key = 'change_this_secret_key'  # Nécessaire pour les sessions Flask
print("✅ Application Flask initialisée")

# Configuration TGI Mistral
MISTRAL_URL = os.getenv('MISTRAL_URL', 'http://tgi:80')
MISTRAL_LEARNER_URL = os.getenv('MISTRAL_LEARNER_URL', 'http://retriever:5000')
print(f"🔗 Configuration Mistral - URL: {MISTRAL_URL}, Learner: {MISTRAL_LEARNER_URL}")

def get_openai_api_key(user_id=None):
    # Si un user_id est fourni, vérifier d'abord la clé API personnelle
    if user_id:
        try:
            db = SessionLocal()
            user = db.query(User).filter_by(id=user_id).first()
            db.close()
            
            if user and user.api_key:
                return user.api_key
        except Exception:
            pass  # En cas d'erreur, continuer avec les méthodes par défaut
    
    # Méthodes par défaut
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
        
        log_action(None, "login_attempt", f"Tentative de connexion pour {username}", request.remote_addr, request.headers.get('User-Agent'))
        
        user = check_login_db(username, password)
        if user:
            login_user(session, user)
            log_success(user.id, "login_success", f"Connexion réussie pour {username} (ID: {user.id}, Role: {user.role})", request.remote_addr, request.headers.get('User-Agent'))
            return redirect(url_for("menu"))
        else:
            log_warning(None, "login_failed", f"Connexion échouée pour {username} - Identifiants invalides", request.remote_addr, request.headers.get('User-Agent'))
            error = "Identifiants invalides."
    else:
        log_action(None, "login_page_access", "Accès à la page de connexion", request.remote_addr, request.headers.get('User-Agent'))
    
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    username = session.get("username")
    log_success(user_id, "logout", f"Déconnexion de {username} (ID: {user_id})", request.remote_addr, request.headers.get('User-Agent'))
    logout_user(session)
    return redirect(url_for("login"))

@app.route("/")
def root():
    if not is_logged_in(session):
        log_action(None, "root_access_redirect", "Accès racine - Redirection vers login (non authentifié)", request.remote_addr, request.headers.get('User-Agent'))
        return redirect(url_for("login"))
    else:
        user_id = session.get("user_id")
        log_action(user_id, "root_access_redirect", "Accès racine - Redirection vers menu (authentifié)", request.remote_addr, request.headers.get('User-Agent'))
        return redirect(url_for("menu"))

@app.route("/analyze")
def analyze():
    if not is_logged_in(session):
        return redirect(url_for("login"))
    user_id = session.get("user_id")
    log_action(user_id, "analyze_page_access", "Accès à la page d'analyse", request.remote_addr, request.headers.get('User-Agent'))
    return render_template("dashboard.html")

@app.route("/analyze_ia", methods=["POST"])
def analyze_ia():
    data = request.get_json()
    raw_payload = data.get("payload", "")
    custom_prompt = data.get("custom_prompt", None)
    user_id = session.get("user_id")
    
    log_action(user_id, "analyze_ia_start", f"Début analyse IA - Payload length: {len(raw_payload)} chars, Custom prompt: {bool(custom_prompt)}", request.remote_addr, request.headers.get('User-Agent'))
    try:
        payload_dict = json.loads(raw_payload)
    except Exception:
        from parser import parse_payload
        payload_dict = parse_payload(raw_payload)
    from parser import flatten_dict
    flat_fields = flatten_dict(payload_dict)
    pattern_nom = flat_fields.get("pattern", "unknown_pattern")
    api_key = get_openai_api_key(user_id)
    if not api_key:
        log_error(user_id, "analyze_ia_api_error", "Aucune clé API disponible (ni personnelle, ni par défaut)", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": "Aucune clé API disponible (ni personnelle, ni par défaut)"}), 500
    from gpt_analysis import analyze_payload_with_gpt
    try:
        ia_response = analyze_payload_with_gpt(payload_dict, api_key, custom_prompt=custom_prompt)
        if ia_response.startswith("[ERREUR]"):
            log_error(user_id, "analyze_ia_gpt_error", f"Erreur GPT: {ia_response}", request.remote_addr, request.headers.get('User-Agent'))
            return jsonify({"error": f"Erreur lors de l'analyse IA: {ia_response}"}), 500
    except Exception as gpt_error:
        log_error(user_id, "analyze_ia_gpt_exception", f"Exception GPT: {str(gpt_error)}", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": f"Erreur lors de l'analyse IA: {str(gpt_error)}"}), 500
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
        statut = "À CHOISIR"
    user_intent = data.get("user_intent", "")
    if user_intent == "faux_positif":
        statut = "Faux positif"
    elif user_intent == "positif_confirme":
        statut = "Vrai positif"
    elif user_intent:
        statut = user_intent
    from pattern_storage import store_analysis
    try:
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
    except Exception as store_error:
        log_error(user_id, "analyze_ia_store_error", f"Erreur lors du stockage: {str(store_error)}", request.remote_addr, request.headers.get('User-Agent'))
        # On continue quand même pour retourner le résultat de l'analyse
    log_success(user_id, "analyze_ia_complete", f"Analyse IA terminée - Pattern: {extracted_pattern}, Statut: {statut}, Résumé: {resume_court[:50]}...", request.remote_addr, request.headers.get('User-Agent'))
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
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données manquantes"}), 400
        
        pattern_nom = data.get("pattern", "").strip()
        short_description = data.get("short_description", "").strip()
        analyse_technique = data.get("analyse_technique", "")
        result = data.get("result", "")
        feedback = data.get("feedback", "")
        tags = data.get("tags", [])
        input_payload = data.get("input", "")
        statut = data.get("statut", None)
        
        # Validation des données
        if not pattern_nom:
            return jsonify({"error": "Nom du pattern requis"}), 400
        
        user_id = session.get("user_id")
        log_action(user_id, "save_pattern_start", f"Sauvegarde pattern: {pattern_nom}, Statut: {statut}, Tags: {tags}", request.remote_addr, request.headers.get('User-Agent'))

        # Créer ou mettre à jour le pattern et l'analyse
        db = SessionLocal()
        try:
            pattern = db.query(Pattern).filter_by(nom=pattern_nom).first()
            
            if not pattern:
                # Créer un nouveau pattern
                pattern = Pattern(
                    nom=pattern_nom,
                    resume=short_description,
                    description=analyse_technique,
                    status=statut,
                    feedback=feedback,
                    tags=','.join(tags) if isinstance(tags, list) else str(tags) if tags else "",
                    user_id=user_id
                )
                db.add(pattern)
                db.flush()  # Pour obtenir l'ID du pattern
                log_action(user_id, "pattern_created", f"Nouveau pattern créé: {pattern_nom}", request.remote_addr, request.headers.get('User-Agent'))
            else:
                # Mettre à jour le pattern existant
                pattern.resume = short_description
                pattern.description = analyse_technique
                pattern.status = statut
                pattern.feedback = feedback
                pattern.tags = ','.join(tags) if isinstance(tags, list) else str(tags) if tags else ""
                pattern.user_id = user_id
                log_action(user_id, "pattern_updated", f"Pattern mis à jour: {pattern_nom}", request.remote_addr, request.headers.get('User-Agent'))
            
            # Créer une nouvelle analyse associée au pattern
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            
            analysis = Analysis(
                payload=input_payload,
                pattern_id=pattern.id,
                pattern_nom=pattern_nom,
                resume_court=short_description,
                description_faits="",
                analyse_technique=analyse_technique,
                resultat=result,
                justification=result,
                rapport_complet=result,
                user_id=user_id,
                tags=','.join(tags) if isinstance(tags, list) else str(tags) if tags else "",
                statut=statut,
                created_at=now,
                updated_at=now
            )
            db.add(analysis)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            log_error(user_id, "save_pattern_db_error", f"Erreur base de données: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
            raise
        finally:
            db.close()
        
        log_success(user_id, "save_pattern_complete", f"Pattern sauvegardé avec succès: {pattern_nom}, Statut: {statut}", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"status": "ok", "message": "Pattern sauvegardé avec succès"})
        
    except Exception as e:
        log_error(session.get("user_id"), "save_pattern_error", f"Erreur lors de la sauvegarde: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": f"Erreur lors de la sauvegarde: {str(e)}"}), 500

@app.route("/analyze_mistral", methods=["POST"])
def analyze_mistral():
    """Analyse avec TGI Mistral - Nouvelle architecture RAG"""
    data = request.get_json()
    raw_payload = data.get("payload", "")
    custom_prompt = data.get("custom_prompt", None)
    user_id = session.get("user_id")
    
    log_action(user_id, "analyze_mistral_tgi_start", f"Début analyse TGI Mistral - Payload length: {len(raw_payload)} chars, Custom prompt: {bool(custom_prompt)}", request.remote_addr, request.headers.get('User-Agent'))
    
    try:
        payload_dict = json.loads(raw_payload)
    except Exception:
        from parser import parse_payload
        payload_dict = parse_payload(raw_payload)
    
    from parser import flatten_dict
    flat_fields = flatten_dict(payload_dict)
    pattern_nom = flat_fields.get("pattern", "unknown_pattern")
    
    # Appel au nouveau service TGI Retriever
    try:
        response = requests.post(f'{MISTRAL_LEARNER_URL}/analyze', 
                               json={'payload': raw_payload}, 
                               timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            ia_response = result['analysis']
            context_count = result.get('context_count', 0)
            payload_hash = result.get('payload_hash', '')
            similar_analyses = result.get('similar_analyses', [])
            
            log_action(user_id, "analyze_mistral_tgi_context", f"Contexte trouvé: {context_count} analyses similaires", request.remote_addr, request.headers.get('User-Agent'))
            
        else:
            error_msg = f'[ERREUR TGI MISTRAL] {response.text}'
            log_error(user_id, "analyze_mistral_tgi_error", f"Erreur TGI Mistral: {error_msg}", request.remote_addr, request.headers.get('User-Agent'))
            return jsonify({"error": f"Erreur lors de l'analyse TGI Mistral: {error_msg}"}), 500
            
    except requests.exceptions.Timeout:
        error_msg = '[ERREUR TGI MISTRAL] Timeout - Service non disponible'
        log_error(user_id, "analyze_mistral_tgi_timeout", error_msg, request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": error_msg}), 504
    except requests.exceptions.ConnectionError as e:
        error_msg = f'[ERREUR TGI MISTRAL] Service non disponible: {str(e)}'
        log_error(user_id, "analyze_mistral_tgi_connection", f"Erreur de connexion TGI: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": error_msg}), 503
    except Exception as mistral_error:
        error_msg = f'[ERREUR TGI MISTRAL] {str(mistral_error)}'
        log_error(user_id, "analyze_mistral_tgi_exception", f"Exception TGI Mistral: {str(mistral_error)}", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": f"Erreur lors de l'analyse TGI Mistral: {str(mistral_error)}"}), 500
    
    # Extraction des informations (comme dans analyze_ia)
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
        statut = "À CHOISIR"
    
    user_intent = data.get("user_intent", "")
    if user_intent == "faux_positif":
        statut = "Faux positif"
    elif user_intent == "positif_confirme":
        statut = "Vrai positif"
    elif user_intent:
        statut = user_intent
    
    # Le stockage est déjà fait par le service Retriever
    # Pas besoin de stocker à nouveau ici
    
    log_success(user_id, "analyze_mistral_tgi_complete", f"Analyse TGI Mistral terminée - Pattern: {extracted_pattern}, Statut: {statut}, Contexte: {context_count} analyses", request.remote_addr, request.headers.get('User-Agent'))
    
    return jsonify({
        "mistral_text": ia_response,
        "pattern": extracted_pattern,
        "short_description": resume_court,
        "result": resultat,
        "analyse_technique": analyse_technique,
        "description_faits": description_faits,
        "statut": statut,
        "summary": flat_fields,
        "parsed": payload_dict,
        "context_count": context_count,
        "payload_hash": payload_hash,
        "similar_analyses": similar_analyses,
        "source": "mistral_tgi_rag"
    })

@app.route("/exemples")
def exemples():
    if not is_logged_in(session):
        return redirect(url_for("login"))
    
    try:
        # Test simple de connexion à la base
        db = SessionLocal()
        
        # Vérifier si la table Pattern existe
        try:
            exemples = db.query(Pattern).all()
            log_action(session.get("user_id"), "exemples_page_access", f"Accès à la page exemples - {len(exemples)} patterns disponibles", request.remote_addr, request.headers.get('User-Agent'))
        except Exception as db_error:
            log_error(session.get("user_id"), "exemples_db_error", f"Erreur base de données: {str(db_error)}", request.remote_addr, request.headers.get('User-Agent'))
            db.close()
            return f"Erreur base de données: {str(db_error)}", 500
        
        db.close()
        
        # Rendre le template avec une liste vide si pas de données
        return render_template("exemple.html", exemples=exemples or [])
        
    except Exception as e:
        log_error(session.get("user_id"), "exemples_page_error", f"Erreur lors de l'accès à la page exemples: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
        return f"Erreur lors du chargement de la page: {str(e)}", 500

@app.route("/exemples_test")
def exemples_test():
    """Route de test pour diagnostiquer les problèmes"""
    if not is_logged_in(session):
        return redirect(url_for("login"))
    
    try:
        # Test minimal
        db = SessionLocal()
        
        # Test 1: Connexion
        print("Test 1: Connexion à la base")
        
        # Test 2: Comptage des patterns
        try:
            count = db.query(Pattern).count()
            print(f"Test 2: {count} patterns trouvés")
        except Exception as e:
            print(f"Test 2 échoué: {e}")
            db.close()
            return f"Erreur comptage patterns: {str(e)}", 500
        
        # Test 3: Récupération des patterns
        try:
            patterns = db.query(Pattern).all()
            print(f"Test 3: {len(patterns)} patterns récupérés")
        except Exception as e:
            print(f"Test 3 échoué: {e}")
            db.close()
            return f"Erreur récupération patterns: {str(e)}", 500
        
        db.close()
        
        # Test 4: Rendu du template
        try:
            return render_template("exemple.html", exemples=patterns)
        except Exception as e:
            print(f"Test 4 échoué: {e}")
            return f"Erreur rendu template: {str(e)}", 500
        
    except Exception as e:
        return f"Erreur générale: {str(e)}", 500

@app.route("/patterns_history")
def patterns_history():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        db = SessionLocal()
        
        # Vérifier si la table Pattern existe
        try:
            patterns = db.query(Pattern).order_by(Pattern.created_at.desc()).all()
        except Exception as db_error:
            log_error(session.get("user_id"), "patterns_history_db_error", f"Erreur base de données: {str(db_error)}", request.remote_addr, request.headers.get('User-Agent'))
            db.close()
            return jsonify({"error": f"Erreur base de données: {str(db_error)}"}), 500
        
        patterns_list = []
        
        for p in patterns:
            try:
                # Récupérer l'utilisateur créateur du pattern
                pattern_user = db.query(User).filter_by(id=p.user_id).first() if p.user_id else None
                
                # Récupérer la dernière analyse associée pour les données complètes
                last_analysis = db.query(Analysis).filter_by(pattern_id=p.id).order_by(Analysis.created_at.desc()).first()
                
                # Gérer les tags
                tags = []
                if p.tags:
                    try:
                        tags = p.tags.split(",") if isinstance(p.tags, str) else p.tags
                    except:
                        tags = []
                
                patterns_list.append({
                    "id": p.id,
                    "pattern": p.nom or "",
                    "status": p.status or "À CHOISIR",
                    "user": pattern_user.username if pattern_user else "N/A",
                    "tags": tags,
                    "feedback": p.feedback or "",
                    "short_description": p.resume or (last_analysis.resume_court if last_analysis else ""),
                    "analyse_technique": p.description or (last_analysis.analyse_technique if last_analysis else ""),
                    "result": last_analysis.resultat if last_analysis else "",
                    "input": last_analysis.payload if last_analysis else "",
                    "date": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "N/A",
                })
            except Exception as e:
                # En cas d'erreur sur un pattern, on continue avec les autres
                log_warning(session.get("user_id"), "pattern_processing_error", f"Erreur lors du traitement du pattern {p.id}: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
                continue
        
        db.close()
        
        log_action(session.get("user_id"), "patterns_history_access", f"Accès à l'historique des patterns - {len(patterns_list)} patterns récupérés", request.remote_addr, request.headers.get('User-Agent'))
        
        return jsonify(patterns_list)
        
    except Exception as e:
        log_error(session.get("user_id"), "patterns_history_error", f"Erreur lors du chargement des patterns: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": f"Erreur lors du chargement des patterns: {str(e)}"}), 500

@app.route("/export_patterns_history")
def export_patterns_history():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        db = SessionLocal()
        patterns = db.query(Pattern).order_by(Pattern.created_at.desc()).all()
        patterns_list = []
        
        for p in patterns:
            # Récupérer la dernière analyse associée
            last_analysis = db.query(Analysis).filter_by(pattern_id=p.id).order_by(Analysis.created_at.desc()).first()
            
            # Gérer les tags
            tags = []
            if p.tags:
                try:
                    tags = p.tags.split(",") if isinstance(p.tags, str) else p.tags
                except:
                    tags = []
            
            patterns_list.append({
                "pattern": p.nom or "",
                "status": p.status or "À CHOISIR",
                "tags": tags,
                "feedbacks": [],
                "short_description": p.resume or (last_analysis.resume_court if last_analysis else ""),
                "analyse_technique": p.description or (last_analysis.analyse_technique if last_analysis else ""),
                "result": last_analysis.resultat if last_analysis else "",
                "input": last_analysis.payload if last_analysis else "",
                "date": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "N/A",
            })
        
        db.close()
        
        from flask import Response
        import json
        return Response(
            json.dumps(patterns_list, ensure_ascii=False, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment;filename=historique_patterns.json"}
        )
        
    except Exception as e:
        log_error(session.get("user_id"), "export_patterns_error", f"Erreur lors de l'export: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": f"Erreur lors de l'export: {str(e)}"}), 500

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
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else "N/A",
            "pattern_nom": a.pattern_nom,
            "resume_court": a.resume_court,
            "resultat": a.resultat,
            "user": user.username if user else "N/A",
            "rapport_complet": a.rapport_complet,
            "statut": a.statut or "À CHOISIR",
        })
    db.close()
    return jsonify(analyses_list)

@app.route("/delete_pattern", methods=["DELETE"])
def delete_pattern():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        # Récupérer le pattern par nom ou ID
        pattern_name = request.args.get("pattern")
        pattern_id = request.args.get("pattern_id")
        
        db = SessionLocal()
        
        if pattern_name:
            pattern = db.query(Pattern).filter_by(nom=pattern_name).first()
        elif pattern_id:
            pattern = db.query(Pattern).filter_by(id=pattern_id).first()
        else:
            db.close()
            return jsonify({"error": "Pattern non spécifié"}), 400
        
        if not pattern:
            db.close()
            log_warning(session.get("user_id"), "delete_pattern_not_found", f"Tentative de suppression d'un pattern inexistant: {pattern_name or pattern_id}", request.remote_addr, request.headers.get('User-Agent'))
            return jsonify({"error": "Pattern introuvable"}), 404
        
        # Supprimer les analyses associées d'abord
        analyses_deleted = db.query(Analysis).filter_by(pattern_id=pattern.id).delete()
        
        # Supprimer le pattern
        pattern_name = pattern.nom
        db.delete(pattern)
        db.commit()
        db.close()
        
        log_success(session.get("user_id"), "delete_pattern", f"Pattern supprimé avec succès: {pattern_name} ({analyses_deleted} analyses supprimées)", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"success": True, "message": f"Pattern supprimé avec succès ({analyses_deleted} analyses supprimées)"})
        
    except Exception as e:
        log_error(session.get("user_id"), "delete_pattern_error", f"Erreur lors de la suppression: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": f"Erreur lors de la suppression: {str(e)}"}), 500

@app.route("/update_pattern", methods=["POST"])
def update_pattern():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        data = request.get_json()
        pattern_name = data.get("pattern")
        new_status = data.get("status")
        new_description = data.get("short_description")
        new_feedback = data.get("feedback")
        
        if not pattern_name:
            return jsonify({"error": "Nom du pattern requis"}), 400
        
        db = SessionLocal()
        pattern = db.query(Pattern).filter_by(nom=pattern_name).first()
        
        if not pattern:
            db.close()
            return jsonify({"error": "Pattern introuvable"}), 404
        
        # Collecter les changements
        changes = []
        old_values = {}
        
        if new_status is not None and new_status != pattern.status:
            old_values['status'] = pattern.status
            pattern.status = new_status
            changes.append(f"statut: '{old_values['status']}' → '{new_status}'")
        
        if new_description is not None and new_description != pattern.resume:
            old_values['resume'] = pattern.resume
            pattern.resume = new_description
            changes.append(f"résumé: '{old_values['resume']}' → '{new_description}'")
        
        if new_feedback is not None and new_feedback != pattern.feedback:
            old_values['feedback'] = pattern.feedback
            pattern.feedback = new_feedback
            changes.append(f"feedback: '{old_values['feedback']}' → '{new_feedback}'")
        
        db.commit()
        db.close()
        
        if changes:
            changes_text = " | ".join(changes)
            log_success(session.get("user_id"), "update_pattern", f"Pattern '{pattern_name}' modifié: {changes_text}", request.remote_addr, request.headers.get('User-Agent'))
        else:
            log_warning(session.get("user_id"), "update_pattern_no_changes", f"Pattern '{pattern_name}' - Aucune modification détectée", request.remote_addr, request.headers.get('User-Agent'))
        
        return jsonify({"success": True, "message": "Pattern mis à jour avec succès"})
        
    except Exception as e:
        log_error(session.get("user_id"), "update_pattern_error", f"Erreur lors de la mise à jour: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": f"Erreur lors de la mise à jour: {str(e)}"}), 500

@app.route("/clear_history", methods=["POST"])
def clear_history():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        db = SessionLocal()
        
        # Supprimer toutes les analyses
        analyses_deleted = db.query(Analysis).delete()
        
        # Supprimer tous les patterns
        patterns_deleted = db.query(Pattern).delete()
        
        db.commit()
        db.close()
        
        log_success(session["user_id"], "clear_history", f"Suppression de {analyses_deleted} analyses et {patterns_deleted} patterns", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"success": True, "analyses_deleted": analyses_deleted, "patterns_deleted": patterns_deleted})
        
    except Exception as e:
        log_error(session["user_id"], "clear_history_error", f"Erreur lors de la suppression: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": f"Erreur lors de la suppression: {str(e)}"}), 500

@app.route("/user_profile")
def user_profile():
    if not is_logged_in(session):
        return redirect(url_for("login"))
    return render_template("user_profile.html")

@app.route("/api/profile/photo", methods=["POST"])
def upload_profile_photo():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        # Vérifier si une image a été envoyée
        if 'photo' not in request.files:
            return jsonify({"error": "Aucune image sélectionnée"}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({"error": "Aucune image sélectionnée"}), 400
        
        # Vérifier le type de fichier
        if not file.content_type.startswith('image/'):
            return jsonify({"error": "Le fichier doit être une image"}), 400
        
        # Vérifier la taille du fichier (max 5MB)
        file.seek(0, 2)  # Aller à la fin du fichier
        file_size = file.tell()
        file.seek(0)  # Retourner au début
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return jsonify({"error": "L'image est trop volumineuse (max 5MB)"}), 400
        
        # Créer le répertoire profile_photos s'il n'existe pas
        photos_dir = os.path.join(os.getcwd(), "profile_photos")
        try:
            os.makedirs(photos_dir, exist_ok=True)
            # Vérifier les permissions
            if not os.access(photos_dir, os.W_OK):
                log_error(user_id, "upload_profile_photo_permission_error", f"Pas de permission d'écriture sur {photos_dir}", request.remote_addr, request.headers.get('User-Agent'))
                return jsonify({"error": f"Erreur de permissions: pas d'accès en écriture sur {photos_dir}"}), 500
        except PermissionError as e:
            log_error(user_id, "upload_profile_photo_permission_error", f"Erreur de permissions lors de la création du répertoire: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
            return jsonify({"error": f"Erreur de permissions: {str(e)}"}), 500
        except Exception as e:
            log_error(user_id, "upload_profile_photo_directory_error", f"Erreur lors de la création du répertoire: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
            return jsonify({"error": f"Erreur lors de la création du répertoire: {str(e)}"}), 500
        
        # Lire et traiter l'image
        image_data = file.read()
        
        # Redimensionner l'image (max 300x300 pour optimiser)
        try:
            img = Image.open(BytesIO(image_data))
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            # Convertir en JPEG pour réduire la taille
            output = BytesIO()
            img.save(output, format='JPEG', quality=80, optimize=True)
            processed_image_data = output.getvalue()
        except Exception as e:
            return jsonify({"error": f"Erreur lors du traitement de l'image: {str(e)}"}), 400
        
        # Générer un nom de fichier unique
        user_id = session["user_id"]
        timestamp = int(time.time())
        filename = f"user_{user_id}_{timestamp}.jpg"
        filepath = os.path.join(photos_dir, filename)
        
        # Sauvegarder l'image sur le disque
        try:
            with open(filepath, 'wb') as f:
                f.write(processed_image_data)
        except PermissionError as e:
            log_error(user_id, "upload_profile_photo_save_permission_error", f"Erreur de permissions lors de la sauvegarde: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
            return jsonify({"error": f"Erreur de permissions lors de la sauvegarde: {str(e)}"}), 500
        except Exception as e:
            log_error(user_id, "upload_profile_photo_save_error", f"Erreur lors de la sauvegarde: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
            return jsonify({"error": f"Erreur lors de la sauvegarde: {str(e)}"}), 500
        
        # Supprimer l'ancienne photo si elle existe
        db = SessionLocal()
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            db.close()
            return jsonify({"error": "Utilisateur introuvable"}), 404
        
        if user.photo:
            old_photo_path = os.path.join(os.getcwd(), user.photo)
            if os.path.exists(old_photo_path):
                try:
                    os.remove(old_photo_path)
                except:
                    pass  # Ignorer les erreurs de suppression
        
        # Sauvegarder le chemin en base de données
        user.photo = os.path.join("profile_photos", filename)
        db.commit()
        db.close()
        
        log_success(user_id, "update_profile_photo", f"Photo de profil mise à jour - Fichier: {filename}, Taille: {len(processed_image_data)} bytes", request.remote_addr, request.headers.get('User-Agent'))
        
        return jsonify({"success": True, "message": "Photo de profil mise à jour avec succès"})
        
    except Exception as e:
        log_error(user_id, "upload_profile_photo_error", f"Erreur lors de l'upload: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
        return jsonify({"error": f"Erreur lors de l'upload: {str(e)}"}), 500

@app.route("/api/profile/photo", methods=["GET"])
def get_profile_photo():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        db = SessionLocal()
        user = db.query(User).filter_by(id=session["user_id"]).first()
        db.close()
        
        if not user or not user.photo:
            return jsonify({"error": "Aucune photo trouvée"}), 404
        
        # Construire le chemin complet vers l'image
        photo_path = os.path.join(os.getcwd(), user.photo)
        
        if not os.path.exists(photo_path):
            return jsonify({"error": "Fichier photo introuvable"}), 404
        
        # Retourner l'image
        return send_file(
            photo_path,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name='profile_photo.jpg'
        )
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération de la photo: {str(e)}"}), 500

@app.route("/api/profile/photo/delete", methods=["DELETE"])
def delete_profile_photo():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        db = SessionLocal()
        user = db.query(User).filter_by(id=session["user_id"]).first()
        if not user:
            db.close()
            return jsonify({"error": "Utilisateur introuvable"}), 404
        
        # Supprimer le fichier physique si il existe
        if user.photo:
            photo_path = os.path.join(os.getcwd(), user.photo)
            if os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except:
                    pass  # Ignorer les erreurs de suppression
        
        user.photo = None
        db.commit()
        db.close()
        
        log_success(session["user_id"], "delete_profile_photo", "Photo de profil supprimée avec succès", request.remote_addr, request.headers.get('User-Agent'))
        
        return jsonify({"success": True, "message": "Photo de profil supprimée avec succès"})
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la suppression: {str(e)}"}), 500

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
        "role": user.role,
        "api_key": user.api_key,
        "photo": user.photo
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
    old_api_key = user.api_key
    old_photo = user.photo
    user.username = data.get("username", user.username)
    user.email = data.get("email", user.email)
    user.role = data.get("role", user.role)
    user.api_key = data.get("api_key", user.api_key)
    user.photo = data.get("photo", user.photo)
    db.commit()
    log_action(session["user_id"], "update_profile", f"Ancien nom: {old_username}, Nouveau nom: {user.username}, Ancien email: {old_email}, Nouveau email: {user.email}, Ancien rôle: {old_role}, Nouveau rôle: {user.role}, Ancien API key: {old_api_key}, Nouveau API key: {user.api_key}, Ancienne photo: {old_photo}, Nouvelle photo: {user.photo}", request.remote_addr, request.headers.get('User-Agent'))
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
        log_warning(session.get("user_id"), "logs_access_denied", f"Tentative d'accès aux logs par un utilisateur non-admin: {user.username if user else 'Unknown'}", request.remote_addr, request.headers.get('User-Agent'))
        return "Accès refusé : réservé aux administrateurs.", 403
    
    try:
        # Récupérer TOUS les logs avec pagination pour éviter les problèmes de mémoire
        logs = db.query(Log).order_by(Log.created_at.desc()).limit(10000).all()
        
        # Récupérer tous les utilisateurs pour l'affichage
        users = {u.id: {"username": u.username, "role": u.role} for u in db.query(User).all()}
        
        # Statistiques pour l'affichage
        total_logs = db.query(Log).count()
        today_logs = db.query(Log).filter(
            Log.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        unique_users = db.query(Log.user_id).distinct().count()
        
        log_action(session["user_id"], "logs_page_access", f"Accès à la page logs - Total: {total_logs}, Aujourd'hui: {today_logs}, Utilisateurs uniques: {unique_users}", request.remote_addr, request.headers.get('User-Agent'))
        
        return render_template("logs.html", 
                             logs=logs, 
                             users=users, 
                             stats={
                                 "total": total_logs,
                                 "today": today_logs,
                                 "unique_users": unique_users
                             })
    
    except Exception as e:
        log_error(session["user_id"], "logs_page_error", f"Erreur lors du chargement des logs: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
        db.rollback()
        return "Erreur lors du chargement des logs.", 500
    
    finally:
        db.close()

@app.route("/menu")
def menu():
    if not is_logged_in(session):
        return redirect(url_for("login"))
    return render_template("menu.html")

@app.route("/settings")
def settings():
    if not is_logged_in(session):
        return redirect(url_for("login"))
    
    try:
        log_action(session.get("user_id"), "settings_page_access", "Accès à la page paramètres", request.remote_addr, request.headers.get('User-Agent'))
        return render_template("settings.html")
        
    except Exception as e:
        log_error(session.get("user_id"), "settings_page_error", f"Erreur lors de l'accès aux paramètres: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
        return "Erreur lors du chargement des paramètres", 500

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

@app.route("/api/profile/api-config", methods=["GET"])
def get_api_config():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        db = SessionLocal()
        user = db.query(User).filter_by(id=session["user_id"]).first()
        db.close()
        
        if not user:
            return jsonify({"error": "Utilisateur introuvable"}), 404
        
        # Détermine si l'utilisateur utilise une API personnelle
        api_config = "custom" if user.api_key else "default"
        
        return jsonify({
            "apiConfig": api_config,
            "hasCustomApi": bool(user.api_key)
        })
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération de la configuration API: {str(e)}"}), 500

@app.route("/api/profile/api-config", methods=["POST"])
def update_api_config():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        data = request.get_json()
        api_config = data.get("apiConfig")
        custom_api_key = data.get("customApiKey")
        
        db = SessionLocal()
        user = db.query(User).filter_by(id=session["user_id"]).first()
        
        if not user:
            db.close()
            return jsonify({"error": "Utilisateur introuvable"}), 404
        
        if api_config == "custom":
            if not custom_api_key or not custom_api_key.strip():
                db.close()
                return jsonify({"error": "Clé API personnelle requise"}), 400
            
            # Validation basique de la clé API
            if not custom_api_key.startswith(('sk-', 'pk-', 'Bearer ')):
                db.close()
                return jsonify({"error": "Format de clé API invalide"}), 400
            
            user.api_key = custom_api_key.strip()
            log_success(session["user_id"], "update_api_config", "Configuration API personnelle activée", request.remote_addr, request.headers.get('User-Agent'))
        else:
            user.api_key = None
            log_success(session["user_id"], "update_api_config", "Configuration API par défaut activée", request.remote_addr, request.headers.get('User-Agent'))
        
        db.commit()
        db.close()
        
        return jsonify({"success": True})
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la mise à jour de la configuration API: {str(e)}"}), 500

@app.route("/api/profile/api-config/reset", methods=["POST"])
def reset_api_config():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        db = SessionLocal()
        user = db.query(User).filter_by(id=session["user_id"]).first()
        
        if not user:
            db.close()
            return jsonify({"error": "Utilisateur introuvable"}), 404
        
        user.api_key = None
        db.commit()
        db.close()
        
        log_success(session["user_id"], "reset_api_config", "Configuration API réinitialisée à la valeur par défaut", request.remote_addr, request.headers.get('User-Agent'))
        
        return jsonify({"success": True})
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la réinitialisation de la configuration API: {str(e)}"}), 500

@app.route("/api/profile/api-status", methods=["GET"])
def get_api_status():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    try:
        db = SessionLocal()
        user = db.query(User).filter_by(id=session["user_id"]).first()
        db.close()
        
        if not user:
            return jsonify({"error": "Utilisateur introuvable"}), 404
        
        # Retourne si l'utilisateur utilise une API personnelle
        return jsonify({
            "isCustomApi": bool(user.api_key)
        })
        
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération du statut API: {str(e)}"}), 500

@app.route("/api/logs/refresh", methods=["GET"])
def refresh_logs():
    if not is_logged_in(session):
        return jsonify({"error": "Non authentifié"}), 401
    
    db = SessionLocal()
    user = db.query(User).filter_by(id=session["user_id"]).first()
    
    if not user or user.role != "admin":
        db.close()
        return jsonify({"error": "Accès refusé : réservé aux administrateurs."}), 403
    
    try:
        # Récupérer les logs récents (derniers 1000)
        logs = db.query(Log).order_by(Log.created_at.desc()).limit(1000).all()
        
        # Récupérer tous les utilisateurs
        users = {u.id: {"username": u.username, "role": u.role} for u in db.query(User).all()}
        
        # Statistiques
        total_logs = db.query(Log).count()
        today_logs = db.query(Log).filter(
            Log.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        unique_users = db.query(Log.user_id).distinct().count()
        
        # Formater les logs pour JSON
        logs_data = []
        for log in logs:
            user_info = users.get(log.user_id, {"username": "Utilisateur inconnu", "role": "user"})
            logs_data.append({
                "id": log.id,
                "date": log.created_at.strftime('%d/%m/%Y %H:%M:%S') if log.created_at else 'N/A',
                "user": user_info["username"],
                "user_role": user_info["role"],
                "action": log.action,
                "details": log.details,
                "ip": log.ip_address or 'N/A',
                "user_agent": log.user_agent or 'N/A'
            })
        
        log_action(session["user_id"], "logs_refresh", f"Rafraîchissement des logs - {len(logs_data)} logs récupérés", request.remote_addr, request.headers.get('User-Agent'))
        
        return jsonify({
            "logs": logs_data,
            "stats": {
                "total": total_logs,
                "today": today_logs,
                "unique_users": unique_users
            }
        })
        di
    except Exception as e:
        log_error(session["user_id"], "logs_refresh_error", f"Erreur lors du rafraîchissement des logs: {str(e)}", request.remote_addr, request.headers.get('User-Agent'))
        db.rollback()
        return jsonify({"error": f"Erreur lors du rafraîchissement: {str(e)}"}), 500
    
    finally:
        db.close()

def create_admin_user():
    session = SessionLocal()
    if not session.query(User).filter_by(username="khz").first():
        user = User(
            username="khz",
            password_hash=generate_password_hash("admin123"),
            email="khz@admin.local",
            role="admin",
            api_key=None,
            photo=None
        )
        session.add(user)
        session.commit()
    session.close()

if __name__ == "__main__":
    print("🗄️ Initialisation de la base de données...")
    init_db()
    print("✅ Base de données initialisée")
    
    print("👤 Création de l'utilisateur admin...")
    create_admin_user()
    print("✅ Utilisateur admin créé")
    
    print("🌐 Démarrage du serveur Flask...")
    print("📍 URL: http://0.0.0.0:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)