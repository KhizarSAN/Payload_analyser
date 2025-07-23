# auth.py

USER = {
    'username': 'admin',
    'password': 'test123'  # À changer si besoin
}

def check_login(username, password):
    return username == USER['username'] and password == USER['password']

def login_user(session):
    session['logged_in'] = True

def logout_user(session):
    session.pop('logged_in', None)

def is_logged_in(session):
    return session.get('logged_in', False) 