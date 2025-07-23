import os
from datetime import datetime
from db_config import SessionLocal, Analysis, Pattern

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
        # Cherche le pattern existant ou crée-le
        pattern = session.query(Pattern).filter_by(nom=pattern_nom).first()
        if not pattern:
            pattern = Pattern(nom=pattern_nom)
            session.add(pattern)
            session.commit()
        # Correction : tags doit être une string
        if tags is not None and isinstance(tags, list):
            tags = ','.join(tags)
        elif tags is None:
            tags = ""
        # Statut : stocke tel quel (binaire)
        if statut not in ["Faux positif", "Vrai positif"]:
            statut = "Non identifié"
        # Crée l'analyse
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
            tags=tags,
            statut=statut
        )
        session.add(analysis)
        session.commit()
        print("Analyse stockée avec succès !")
    finally:
        session.close() 