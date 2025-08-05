#!/usr/bin/env python3
"""
Script de test pour vérifier le fonctionnement des tokens GPT personnels
Vérifie le stockage en base, la liaison aux comptes utilisateur et l'utilisation correcte
"""

import os
import sys
import json
import requests
from datetime import datetime

# Ajouter le répertoire courant au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test de connexion à la base de données"""
    print("🔍 Test de connexion à la base de données...")
    try:
        from db_config import SessionLocal, User
        db = SessionLocal()
        
        # Test de connexion
        users = db.query(User).all()
        print(f"✅ Connexion DB réussie - {len(users)} utilisateurs trouvés")
        
        # Vérifier la structure de la table User
        user_columns = User.__table__.columns.keys()
        print(f"📋 Colonnes de la table User: {user_columns}")
        
        if 'api_key' in user_columns:
            print("✅ Colonne api_key présente dans la table User")
        else:
            print("❌ Colonne api_key manquante dans la table User")
            return False
            
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion DB: {e}")
        return False

def test_user_api_key_storage():
    """Test du stockage des clés API personnelles"""
    print("\n🔑 Test du stockage des clés API personnelles...")
    try:
        from db_config import SessionLocal, User
        from werkzeug.security import generate_password_hash
        
        db = SessionLocal()
        
        # Créer un utilisateur de test
        test_username = "test_gpt_user"
        test_api_key = "sk-test123456789abcdef"
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = db.query(User).filter_by(username=test_username).first()
        if existing_user:
            print(f"👤 Utilisateur de test existant: {test_username}")
            user = existing_user
        else:
            print(f"👤 Création d'un utilisateur de test: {test_username}")
            user = User(
                username=test_username,
                password_hash=generate_password_hash("test123"),
                email="test@example.com",
                role="user",
                api_key=None
            )
            db.add(user)
            db.flush()  # Pour obtenir l'ID
        
        # Sauvegarder une clé API personnelle
        user.api_key = test_api_key
        db.commit()
        
        print(f"💾 Clé API sauvegardée pour l'utilisateur {user.id}")
        
        # Vérifier que la clé est bien sauvegardée
        db.refresh(user)
        if user.api_key == test_api_key:
            print("✅ Clé API correctement sauvegardée en base")
        else:
            print(f"❌ Erreur de sauvegarde - Attendu: {test_api_key}, Reçu: {user.api_key}")
            return False
        
        # Nettoyer
        user.api_key = None
        db.commit()
        print("🧹 Clé API de test supprimée")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de stockage: {e}")
        return False

def test_get_openai_api_key_function():
    """Test de la fonction get_openai_api_key"""
    print("\n🔍 Test de la fonction get_openai_api_key...")
    try:
        from app import get_openai_api_key
        from db_config import SessionLocal, User
        from werkzeug.security import generate_password_hash
        
        db = SessionLocal()
        
        # Créer un utilisateur avec une clé API
        test_username = "test_api_user"
        test_api_key = "sk-test987654321fedcba"
        
        user = db.query(User).filter_by(username=test_username).first()
        if not user:
            user = User(
                username=test_username,
                password_hash=generate_password_hash("test123"),
                email="test2@example.com",
                role="user",
                api_key=test_api_key
            )
            db.add(user)
            db.flush()
        else:
            user.api_key = test_api_key
            db.commit()
        
        # Test 1: Récupération avec user_id
        api_key = get_openai_api_key(user.id)
        if api_key == test_api_key:
            print("✅ get_openai_api_key retourne la clé personnelle correctement")
        else:
            print(f"❌ Erreur get_openai_api_key - Attendu: {test_api_key}, Reçu: {api_key}")
            return False
        
        # Test 2: Récupération sans user_id (doit utiliser la clé par défaut)
        api_key_default = get_openai_api_key()
        print(f"🔑 Clé API par défaut: {api_key_default[:10]}..." if api_key_default else "Aucune clé par défaut")
        
        # Nettoyer
        user.api_key = None
        db.commit()
        db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test get_openai_api_key: {e}")
        return False

def test_gpt_analysis_function():
    """Test de la fonction d'analyse GPT"""
    print("\n🤖 Test de la fonction d'analyse GPT...")
    try:
        from gpt_analysis import analyze_payload_with_gpt
        
        # Payload de test
        test_payload = {
            "source": "192.168.1.100",
            "destination": "10.0.0.1",
            "event": "Suspicious activity detected",
            "severity": "High"
        }
        
        # Clé API de test (ne fonctionnera pas mais permet de tester la structure)
        test_api_key = "sk-test123456789"
        
        # Test de la fonction
        result = analyze_payload_with_gpt(test_payload, test_api_key)
        
        print(f"📊 Type de retour: {type(result)}")
        print(f"🔍 Clés du dictionnaire: {list(result.keys())}")
        
        if isinstance(result, dict) and "success" in result:
            print("✅ Structure de retour correcte")
            
            if result["success"]:
                print("✅ Analyse GPT réussie (simulation)")
            else:
                print(f"⚠️ Analyse GPT échouée (attendu avec une clé de test): {result.get('error', 'Erreur inconnue')}")
        else:
            print("❌ Structure de retour incorrecte")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'analyse GPT: {e}")
        return False

def test_api_endpoints():
    """Test des endpoints API pour la configuration GPT"""
    print("\n🌐 Test des endpoints API...")
    
    # URL de base (à adapter selon votre configuration)
    base_url = "http://localhost:5000"
    
    endpoints = [
        "/api/profile/api-config",
        "/api/profile/api-status"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"🔗 Test de {endpoint}...")
            
            response = requests.get(url, timeout=5)
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 401:
                print("✅ Endpoint protégé (authentification requise)")
            elif response.status_code == 200:
                print("✅ Endpoint accessible")
                try:
                    data = response.json()
                    print(f"📄 Données: {data}")
                except:
                    print("⚠️ Réponse non-JSON")
            else:
                print(f"⚠️ Status inattendu: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Impossible de se connecter à l'application")
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    return True

def test_complete_flow():
    """Test du flux complet: sauvegarde -> récupération -> utilisation"""
    print("\n🔄 Test du flux complet...")
    try:
        from db_config import SessionLocal, User
        from app import get_openai_api_key
        from gpt_analysis import analyze_payload_with_gpt
        from werkzeug.security import generate_password_hash
        
        db = SessionLocal()
        
        # 1. Créer un utilisateur
        test_username = "flow_test_user"
        test_api_key = "sk-flowtest123456789"
        
        user = db.query(User).filter_by(username=test_username).first()
        if not user:
            user = User(
                username=test_username,
                password_hash=generate_password_hash("test123"),
                email="flow@test.com",
                role="user"
            )
            db.add(user)
            db.flush()
        
        # 2. Sauvegarder une clé API personnelle
        user.api_key = test_api_key
        db.commit()
        print("✅ Étape 1: Clé API sauvegardée")
        
        # 3. Récupérer la clé via get_openai_api_key
        retrieved_key = get_openai_api_key(user.id)
        if retrieved_key == test_api_key:
            print("✅ Étape 2: Clé API récupérée correctement")
        else:
            print(f"❌ Étape 2: Erreur de récupération - Attendu: {test_api_key}, Reçu: {retrieved_key}")
            return False
        
        # 4. Utiliser la clé dans l'analyse GPT
        test_payload = {"test": "data"}
        result = analyze_payload_with_gpt(test_payload, retrieved_key)
        
        if isinstance(result, dict) and "success" in result:
            print("✅ Étape 3: Analyse GPT exécutée (structure correcte)")
        else:
            print("❌ Étape 3: Erreur dans l'analyse GPT")
            return False
        
        # 5. Nettoyer
        user.api_key = None
        db.commit()
        db.close()
        print("✅ Étape 4: Nettoyage effectué")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le flux complet: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests pour les tokens GPT personnels")
    print("=" * 60)
    
    tests = [
        ("Connexion à la base de données", test_database_connection),
        ("Stockage des clés API", test_user_api_key_storage),
        ("Fonction get_openai_api_key", test_get_openai_api_key_function),
        ("Fonction d'analyse GPT", test_gpt_analysis_function),
        ("Endpoints API", test_api_endpoints),
        ("Flux complet", test_complete_flow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Exception dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés! Le système de tokens GPT personnels fonctionne correctement.")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 