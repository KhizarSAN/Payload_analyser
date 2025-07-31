from db_config import SessionLocal, Log
from datetime import datetime, timezone
import traceback
import sys
import logging
import os

# Configuration du logging système
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Logger principal de l'application
app_logger = logging.getLogger('qradar_ticket')

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
        log_message = f"[{timestamp}] {level} - {user_info} - {action}: {details}"
        
        # Log système
        app_logger.info(log_message)
        
        # Log console
        print(log_message)
        
    except Exception as e:
        # En cas d'erreur de logging, on affiche dans la console
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        error_msg = f"[{timestamp}] ERROR - Logging failed: {str(e)}"
        original_msg = f"Original action: {action} - {details}"
        
        app_logger.error(error_msg)
        app_logger.error(original_msg)
        print(error_msg)
        print(original_msg)

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