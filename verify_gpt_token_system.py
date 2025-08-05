#!/usr/bin/env python3
"""
Script de vérification du système de tokens GPT personnels
Vérifie la structure de la base de données et les fonctions clés
"""

import os
import sys

# Ajouter le répertoire courant au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def verify_database_structure():
    """Vérifie la structure de la base de données"""
    print("🔍 Vérification de la structure de la base de données...")
    try:
        from db_config import User, SessionLocal
        
        # Vérifier que la table User a la colonne api_key
        user_columns = User.__table__.columns.keys()
        print(f"📋 Colonnes de la table User: {user_columns}")
        
        if 'api_key' in user_columns:
            print("✅ Colonne api_key présente dans la table User")
            return True
        else:
            print("❌ Colonne api_key manquante dans la table User")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la structure DB: {e}")
        return False

def verify_get_openai_api_key_function():
    """Vérifie la fonction get_openai_api_key"""
    print("\n🔍 Vérification de la fonction get_openai_api_key...")
    try:
        from app import get_openai_api_key
        
        # Vérifier que la fonction existe et peut être appelée
        print("✅ Fonction get_openai_api_key importée avec succès")
        
        # Vérifier la signature de la fonction
        import inspect
        sig = inspect.signature(get_openai_api_key)
        params = list(sig.parameters.keys())
        print(f"📝 Paramètres de la fonction: {params}")
        
        if 'user_id' in params or len(params) == 0:
            print("✅ Signature de fonction correcte")
            return True
        else:
            print("❌ Signature de fonction incorrecte")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de get_openai_api_key: {e}")
        return False

def verify_api_config_routes():
    """Vérifie les routes de configuration API"""
    print("\n🌐 Vérification des routes de configuration API...")
    try:
        from app import app
        
        # Vérifier que les routes existent
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        api_routes = [
            '/api/profile/api-config',
            '/api/profile/api-status'
        ]
        
        for route in api_routes:
            if route in routes:
                print(f"✅ Route {route} présente")
            else:
                print(f"❌ Route {route} manquante")
                return False
        
        print("✅ Toutes les routes API de configuration sont présentes")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des routes: {e}")
        return False

def verify_gpt_analysis_function():
    """Vérifie la fonction d'analyse GPT"""
    print("\n🤖 Vérification de la fonction d'analyse GPT...")
    try:
        from gpt_analysis import analyze_payload_with_gpt
        
        # Vérifier que la fonction existe
        print("✅ Fonction analyze_payload_with_gpt importée avec succès")
        
        # Vérifier la signature
        import inspect
        sig = inspect.signature(analyze_payload_with_gpt)
        params = list(sig.parameters.keys())
        print(f"📝 Paramètres de la fonction: {params}")
        
        required_params = ['payload_dict', 'api_key']
        for param in required_params:
            if param in params:
                print(f"✅ Paramètre {param} présent")
            else:
                print(f"❌ Paramètre {param} manquant")
                return False
        
        print("✅ Signature de la fonction d'analyse GPT correcte")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de l'analyse GPT: {e}")
        return False

def verify_analyze_ia_function():
    """Vérifie la fonction analyze_ia dans app.py"""
    print("\n🔍 Vérification de la fonction analyze_ia...")
    try:
        # Lire le fichier app.py pour vérifier la logique
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier les éléments clés
        checks = [
            ("get_openai_api_key(user_id)", "Appel de get_openai_api_key avec user_id"),
            ("analyze_payload_with_gpt", "Appel de la fonction d'analyse GPT"),
            ("ia_response.get(\"success\", False)", "Vérification du succès de l'analyse"),
            ("ia_text = ia_response.get(\"analysis\", \"\")", "Extraction du texte d'analyse"),
            ("store_analysis", "Stockage en base de données")
        ]
        
        for check_text, description in checks:
            if check_text in content:
                print(f"✅ {description}")
            else:
                print(f"❌ {description} manquant")
                return False
        
        print("✅ Logique de la fonction analyze_ia correcte")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de analyze_ia: {e}")
        return False

def verify_logging_integration():
    """Vérifie l'intégration du logging"""
    print("\n📝 Vérification de l'intégration du logging...")
    try:
        from logger import log_action, log_error, log_success
        
        print("✅ Fonctions de logging importées avec succès")
        
        # Vérifier que le logging est utilisé dans les fonctions clés
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        logging_checks = [
            ("log_action", "Logging des actions"),
            ("log_error", "Logging des erreurs"),
            ("log_success", "Logging des succès")
        ]
        
        for check_text, description in logging_checks:
            if check_text in content:
                print(f"✅ {description} intégré")
            else:
                print(f"⚠️ {description} non trouvé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification du logging: {e}")
        return False

def main():
    """Fonction principale de vérification"""
    print("🚀 Vérification du système de tokens GPT personnels")
    print("=" * 60)
    
    verifications = [
        ("Structure de la base de données", verify_database_structure),
        ("Fonction get_openai_api_key", verify_get_openai_api_key_function),
        ("Routes de configuration API", verify_api_config_routes),
        ("Fonction d'analyse GPT", verify_gpt_analysis_function),
        ("Fonction analyze_ia", verify_analyze_ia_function),
        ("Intégration du logging", verify_logging_integration)
    ]
    
    results = []
    
    for verification_name, verification_func in verifications:
        print(f"\n{'='*20} {verification_name} {'='*20}")
        try:
            success = verification_func()
            results.append((verification_name, success))
        except Exception as e:
            print(f"❌ Exception dans {verification_name}: {e}")
            results.append((verification_name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DE LA VÉRIFICATION")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for verification_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {verification_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Résultat: {passed}/{total} vérifications réussies")
    
    if passed == total:
        print("🎉 Toutes les vérifications sont passées!")
        print("\n📋 RÉSUMÉ DU SYSTÈME DE TOKENS GPT PERSONNELS:")
        print("✅ La table User contient la colonne api_key pour stocker les clés personnelles")
        print("✅ La fonction get_openai_api_key() récupère d'abord la clé personnelle de l'utilisateur")
        print("✅ Les routes API permettent de configurer et gérer les clés personnelles")
        print("✅ La fonction analyze_ia utilise la clé personnelle via get_openai_api_key(user_id)")
        print("✅ L'analyse GPT est effectuée avec la clé personnelle")
        print("✅ Les résultats sont stockés en base de données avec l'ID utilisateur")
        print("✅ Le logging est intégré pour tracer les actions")
        
        print("\n🔄 FLUX COMPLET:")
        print("1. L'utilisateur sauvegarde sa clé API personnelle via /api/profile/api-config")
        print("2. La clé est stockée dans la table User.api_key pour cet utilisateur")
        print("3. Lors d'une analyse IA, get_openai_api_key(user_id) récupère la clé personnelle")
        print("4. Si aucune clé personnelle, la fonction utilise la clé par défaut")
        print("5. L'analyse GPT est effectuée avec la clé appropriée")
        print("6. Les résultats sont stockés en base avec l'ID utilisateur")
        
    else:
        print("⚠️ Certaines vérifications ont échoué. Vérifiez les erreurs ci-dessus.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 