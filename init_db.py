#!/usr/bin/env python3
"""
Script d'initialisation de la base de données avec gestion d'erreurs robuste.
"""

import time
import sys
from sqlalchemy import text
from db_config import SessionLocal, User, engine
from werkzeug.security import generate_password_hash
from datetime import datetime

def wait_for_database():
    """Attendre que la base de données soit prête."""
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print("✅ Base de données connectée avec succès!")
                return True
        except Exception as e:
            attempt += 1
            print(f"⏳ Tentative {attempt}/{max_attempts} - Attente de la base de données... ({e})")
            time.sleep(2)
    
    print("❌ Impossible de se connecter à la base de données après 30 tentatives")
    return False

def check_tables_exist():
    """Vérifier que les tables existent (créées par le fichier SQL)."""
    try:
        with engine.connect() as conn:
            # Vérifier que la table users existe
            result = conn.execute(text("SHOW TABLES LIKE 'users'"))
            if result.fetchone():
                print("✅ Tables existent (créées par payload_analyser.sql)")
                return True
            else:
                print("❌ Tables manquantes - le fichier SQL n'a pas été exécuté")
                return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des tables: {e}")
        return False

def create_admin_user():
    """Créer l'utilisateur admin 'khz'."""
    session = SessionLocal()
    
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = session.query(User).filter_by(username="khz").first()
        
        if existing_user:
            print("ℹ️ L'utilisateur 'khz' existe déjà.")
            return True
        
        # Créer le hash du mot de passe
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
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def main():
    """Fonction principale d'initialisation."""
    print("🚀 Démarrage de l'initialisation de la base de données...")
    
    # Attendre que la base de données soit prête
    if not wait_for_database():
        sys.exit(1)
    
    # Vérifier que les tables existent
    if not check_tables_exist():
        print("⚠️ Les tables n'existent pas. Vérifiez que le fichier payload_analyser.sql est bien exécuté.")
        sys.exit(1)
    
    # Créer l'utilisateur admin
    if not create_admin_user():
        sys.exit(1)
    
    print("🎉 Initialisation terminée avec succès!")

if __name__ == "__main__":
    main() 