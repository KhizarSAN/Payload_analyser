#!/usr/bin/env python3
"""
Script d'initialisation de la base de données avec un utilisateur admin par défaut.
"""

from db_config import SessionLocal, User, init_db
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin_user():
    """Crée l'utilisateur admin 'khz' avec le mot de passe par défaut."""
    
    # Initialiser la base de données
    print("Initialisation de la base de données...")
    init_db()
    
    # Créer une session
    session = SessionLocal()
    
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = session.query(User).filter_by(username="khz").first()
        
        if existing_user:
            print("L'utilisateur 'khz' existe déjà.")
            return
        
        # Créer le hash du mot de passe (admin123 par défaut)
        password_hash = generate_password_hash("admin123")
        
        # Créer l'utilisateur admin
        admin_user = User(
            username="khz",
            password_hash=password_hash,
            email="khz@admin.local",
            role="admin",
            api_key=None,
            photo=None,
            created_at=datetime.now()
        )
        
        # Ajouter à la base de données
        session.add(admin_user)
        session.commit()
        
        print("✅ Utilisateur admin 'khz' créé avec succès!")
        print("   Username: khz")
        print("   Password: admin123")
        print("   Role: admin")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    create_admin_user() 