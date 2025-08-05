#!/usr/bin/env python3
"""
Script de diagnostic pour identifier le problème de clé API (erreur 401)
"""

import os
import sys
import requests
from datetime import datetime

# Ajouter le répertoire courant au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_environment_variables():
    """Vérifie les variables d'environnement"""
    print("🔍 Vérification des variables d'environnement...")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"✅ Variable OPENAI_API_KEY trouvée: {openai_key[:10]}...")
        return openai_key
    else:
        print("❌ Variable OPENAI_API_KEY non trouvée")
        return None

def check_static_file():
    """Vérifie le fichier static/openai_key.txt"""
    print("\n📁 Vérification du fichier static/openai_key.txt...")
    
    try:
        file_path = os.path.join("static", "openai_key.txt")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    print(f"✅ Fichier trouvé avec clé: {content[:10]}...")
                    return content
                else:
                    print("❌ Fichier vide")
                    return None
        else:
            print("❌ Fichier non trouvé")
            return None
    except Exception as e:
        print(f"❌ Erreur lecture fichier: {e}")
        return None

def check_database_keys():
    """Vérifie les clés API stockées en base"""
    print("\n🗄️ Vérification des clés API en base de données...")
    
    try:
        from db_config import SessionLocal, User
        
        db = SessionLocal()
        users_with_keys = db.query(User).filter(User.api_key.isnot(None)).all()
        
        if users_with_keys:
            print(f"✅ {len(users_with_keys)} utilisateur(s) avec clé API personnelle:")
            for user in users_with_keys:
                print(f"   - {user.username}: {user.api_key[:10]}...")
            return users_with_keys
        else:
            print("❌ Aucun utilisateur avec clé API personnelle")
            return []
            
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return []

def test_api_key(api_key, description):
    """Teste une clé API avec l'API OpenAI"""
    print(f"\n🧪 Test de la clé API ({description}): {api_key[:10]}...")
    
    if not api_key or not api_key.startswith('sk-'):
        print("❌ Format de clé API invalide")
        return False
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": "Test de connexion - répondez simplement 'OK'"
                }
            ],
            "max_tokens": 10
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Clé API valide")
            return True
        elif response.status_code == 401:
            print("❌ Erreur 401 - Clé API invalide ou expirée")
            return False
        elif response.status_code == 429:
            print("⚠️ Erreur 429 - Limite de taux dépassée")
            return False
        else:
            print(f"❌ Erreur {response.status_code}: {response.text[:100]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout lors du test")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Erreur de connexion")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def test_get_openai_api_key_function():
    """Teste la fonction get_openai_api_key"""
    print("\n🔧 Test de la fonction get_openai_api_key...")
    
    try:
        from app import get_openai_api_key
        
        # Test sans user_id
        api_key_default = get_openai_api_key()
        if api_key_default:
            print(f"✅ Clé par défaut récupérée: {api_key_default[:10]}...")
            test_api_key(api_key_default, "Clé par défaut")
        else:
            print("❌ Aucune clé par défaut trouvée")
        
        # Test avec user_id (si des utilisateurs ont des clés)
        from db_config import SessionLocal, User
        db = SessionLocal()
        user_with_key = db.query(User).filter(User.api_key.isnot(None)).first()
        db.close()
        
        if user_with_key:
            api_key_personal = get_openai_api_key(user_with_key.id)
            if api_key_personal:
                print(f"✅ Clé personnelle récupérée pour {user_with_key.username}: {api_key_personal[:10]}...")
                test_api_key(api_key_personal, f"Clé personnelle de {user_with_key.username}")
            else:
                print(f"❌ Impossible de récupérer la clé personnelle pour {user_with_key.username}")
        else:
            print("⚠️ Aucun utilisateur avec clé personnelle pour tester")
            
    except Exception as e:
        print(f"❌ Erreur lors du test de get_openai_api_key: {e}")

def check_quota_and_billing():
    """Vérifie le quota et la facturation OpenAI"""
    print("\n💰 Vérification du quota et de la facturation...")
    
    # Récupérer une clé API pour tester
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            with open(os.path.join("static", "openai_key.txt"), 'r') as f:
                api_key = f.read().strip()
        except:
            pass
    
    if not api_key:
        print("❌ Aucune clé API disponible pour vérifier le quota")
        return
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # Vérifier l'utilisation
        response = requests.get(
            "https://api.openai.com/v1/usage",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            usage_data = response.json()
            print("✅ Informations d'utilisation récupérées")
            print(f"   - Total usage: {usage_data.get('total_usage', 'N/A')}")
            print(f"   - Daily costs: {usage_data.get('daily_costs', 'N/A')}")
        else:
            print(f"⚠️ Impossible de récupérer l'utilisation: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification du quota: {e}")

def provide_solutions():
    """Fournit des solutions pour résoudre le problème"""
    print("\n" + "="*60)
    print("🔧 SOLUTIONS POUR RÉSOUDRE L'ERREUR 401")
    print("="*60)
    
    print("\n1. 🔑 VÉRIFIER LA CLÉ API:")
    print("   - Allez sur https://platform.openai.com/api-keys")
    print("   - Vérifiez que votre clé API est active et valide")
    print("   - Créez une nouvelle clé si nécessaire")
    
    print("\n2. 💰 VÉRIFIER LA FACTURATION:")
    print("   - Allez sur https://platform.openai.com/account/billing")
    print("   - Vérifiez que vous avez des crédits disponibles")
    print("   - Ajoutez une méthode de paiement si nécessaire")
    
    print("\n3. 🗄️ CONFIGURER LA CLÉ DANS L'APPLICATION:")
    print("   Option A - Variable d'environnement:")
    print("   export OPENAI_API_KEY='sk-votre-cle-api'")
    
    print("\n   Option B - Fichier static/openai_key.txt:")
    print("   echo 'sk-votre-cle-api' > static/openai_key.txt")
    
    print("\n   Option C - Interface utilisateur:")
    print("   - Connectez-vous à l'application")
    print("   - Allez dans Profil > Configuration API")
    print("   - Entrez votre clé API personnelle")
    
    print("\n4. 🔄 REDÉMARRER L'APPLICATION:")
    print("   - Arrêtez l'application")
    print("   - Redémarrez avec la nouvelle configuration")
    
    print("\n5. 📝 VÉRIFIER LES LOGS:")
    print("   - Consultez les logs de l'application")
    print("   - Vérifiez les messages d'erreur détaillés")

def main():
    """Fonction principale de diagnostic"""
    print("🚀 Diagnostic du problème de clé API (erreur 401)")
    print("=" * 60)
    
    # Vérifications
    env_key = check_environment_variables()
    file_key = check_static_file()
    db_keys = check_database_keys()
    
    # Tests des clés
    if env_key:
        test_api_key(env_key, "Variable d'environnement")
    
    if file_key:
        test_api_key(file_key, "Fichier static/openai_key.txt")
    
    for user in db_keys:
        test_api_key(user.api_key, f"Base de données - {user.username}")
    
    # Test de la fonction
    test_get_openai_api_key_function()
    
    # Vérification du quota
    check_quota_and_billing()
    
    # Solutions
    provide_solutions()
    
    print("\n" + "="*60)
    print("✅ Diagnostic terminé")
    print("="*60)

if __name__ == "__main__":
    main() 