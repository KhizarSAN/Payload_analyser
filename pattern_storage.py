import os
from datetime import datetime, timezone
from db_config import SessionLocal, Analysis, Pattern
from logger import log_action, log_error, log_success

def find_existing_pattern(pattern_nom):
    session = SessionLocal()
    try:
        pattern = session.query(Pattern).filter_by(nom=pattern_nom).first()
        return pattern
    finally:
        session.close()

def get_all_patterns():
    session = SessionLocal()
    try:
        patterns = session.query(Pattern).all()
        return [p.nom for p in patterns]
    finally:
        session.close()

def store_analysis(payload, rapport_ia, pattern_nom, resume_court, description_faits, analyse_technique, resultat, justification, user_id=None, tags=None, statut=None):
    session = SessionLocal()
    try:
        log_action(user_id, "store_analysis_start", f"Début stockage analyse - Pattern: {pattern_nom}, Statut: {statut}")
        
        # Cherche le pattern existant ou crée-le
        pattern = session.query(Pattern).filter_by(nom=pattern_nom).first()
        if not pattern:
            pattern = Pattern(nom=pattern_nom)
            session.add(pattern)
            session.flush()  # Pour obtenir l'ID du pattern
        
        # Mettre à jour le pattern avec les nouvelles informations
        if resume_court:
            pattern.resume = resume_court
        if tags is not None:
            if isinstance(tags, list):
                pattern.tags = ','.join(tags)
            else:
                pattern.tags = str(tags)
        if statut:
            pattern.status = statut
        if user_id:
            pattern.user_id = user_id
        
        # Correction : tags doit être une string pour l'analyse
        if tags is not None and isinstance(tags, list):
            tags_str = ','.join(tags)
        elif tags is None:
            tags_str = ""
        else:
            tags_str = str(tags)
        
        # Statut : validation et valeur par défaut
        if not statut or statut.strip() == "":
            statut = "À CHOISIR"
        elif statut not in ["Faux positif", "Vrai positif", "À CHOISIR", "critique", "à surveiller", "ignoré"]:
            # Si le statut n'est pas reconnu, on le garde tel quel mais on log
            print(f"Statut non reconnu: '{statut}', gardé tel quel")
        
        # Crée l'analyse avec timestamp correct
        now = datetime.now(timezone.utc)
        analysis = Analysis(
            payload=payload,
            pattern_id=pattern.id,
            pattern_nom=pattern_nom,
            resume_court=resume_court,
            description_faits=description_faits,
            analyse_technique=analyse_technique,
            resultat=resultat,
            justification=justification,
            rapport_complet=rapport_ia,
            user_id=user_id,
            tags=tags_str,
            statut=statut,
            created_at=now,
            updated_at=now
        )
        session.add(analysis)
        session.commit()
        
        log_success(user_id, "store_analysis_complete", f"Analyse stockée avec succès - Pattern: {pattern_nom}, ID: {analysis.id}")
    except Exception as e:
        log_error(user_id, "store_analysis_error", f"Erreur lors du stockage: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close() 