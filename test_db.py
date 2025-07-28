from db_config import SessionLocal, User, init_db

# Crée les tables si elles n'existent pas (à faire une seule fois)
init_db()

# Démarre une session
session = SessionLocal()

try:
    # Test d'insertion d'un utilisateur
    new_user = User(username="testuser", password_hash="hash", email="test@example.com", role="admin", api_key=None, photo=None)
    session.add(new_user)
    session.commit()
    print("Utilisateur inséré avec succès !")

    # Test de lecture
    users = session.query(User).all()
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {user.role}")

finally:
    session.close()
