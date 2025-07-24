# auth.py

from db_config import SessionLocal, User
from werkzeug.security import check_password_hash

# Authentification via la base de données

def check_login_db(username, password):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            return user
        return None
    finally:
        db.close()

def login_user(session, user):
    session['logged_in'] = True
    session['user_id'] = user.id
    session['username'] = user.username

def logout_user(session):
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)

def is_logged_in(session):
    return session.get('user_id') is not None 