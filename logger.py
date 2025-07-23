from db_config import SessionLocal, Log

def log_action(user_id, action, details="", ip_address=None, user_agent=None):
    session = SessionLocal()
    log = Log(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    session.add(log)
    session.commit()
    session.close() 