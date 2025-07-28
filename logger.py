from db_config import SessionLocal, Log
from datetime import datetime, timezone
import traceback
import sys

def log_action(user_id, action, details="", ip_address=None, user_agent=None, level="INFO"):
    """
    Fonction de logging améliorée avec gestion d'erreurs et niveaux
    """
    try:
        session = SessionLocal()
        log = Log(
            user_id=user_id,
            action=f"[{level}] {action}",
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        session.add(log)
        session.commit()
        session.close()
        
        # Log console pour debugging
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        user_info = f"User:{user_id}" if user_id else "Anonymous"
        print(f"[{timestamp}] {level} - {user_info} - {action}: {details}")
        
    except Exception as e:
        # En cas d'erreur de logging, on affiche dans la console
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ERROR - Logging failed: {str(e)}")
        print(f"Original action: {action} - {details}")

def log_error(user_id, action, error, ip_address=None, user_agent=None):
    """
    Fonction spécialisée pour les erreurs avec stack trace
    """
    error_details = f"ERROR: {str(error)}\nStack trace: {traceback.format_exc()}"
    log_action(user_id, action, error_details, ip_address, user_agent, "ERROR")

def log_warning(user_id, action, details="", ip_address=None, user_agent=None):
    """
    Fonction spécialisée pour les avertissements
    """
    log_action(user_id, action, details, ip_address, user_agent, "WARNING")

def log_success(user_id, action, details="", ip_address=None, user_agent=None):
    """
    Fonction spécialisée pour les succès
    """
    log_action(user_id, action, details, ip_address, user_agent, "SUCCESS") 