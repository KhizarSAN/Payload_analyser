#!/usr/bin/env python3
"""
Script pour améliorer la gestion des erreurs de clé API
"""

import os
import sys

def improve_gpt_analysis_error_handling():
    """Améliore la gestion des erreurs dans gpt_analysis.py"""
    print("🔧 Amélioration de la gestion des erreurs dans gpt_analysis.py...")
    
    try:
        with open('gpt_analysis.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier si les améliorations sont déjà présentes
        if "Erreur 401 - Clé API invalide" in content:
            print("✅ Gestion d'erreur 401 déjà présente")
            return True
        
        # Améliorer la gestion des erreurs 401
        old_error_handling = """        else:
            print(f"❌ [GPT_ANALYSIS] Erreur API GPT: {response.status_code}")
            print(f"📄 [GPT_ANALYSIS] Réponse: {response.text[:200]}...")
            logger.error(f"❌ Erreur API GPT: {response.status_code}")
            return {
                "success": False,
                "error": f"Erreur API: {response.status_code}",
                "analysis": "Erreur lors de l'analyse GPT"
            }"""
        
        new_error_handling = """        else:
            print(f"❌ [GPT_ANALYSIS] Erreur API GPT: {response.status_code}")
            print(f"📄 [GPT_ANALYSIS] Réponse: {response.text[:200]}...")
            logger.error(f"❌ Erreur API GPT: {response.status_code}")
            
            # Gestion spécifique des erreurs courantes
            if response.status_code == 401:
                error_msg = "Clé API invalide ou expirée. Veuillez vérifier votre clé API dans les paramètres."
                logger.error("❌ Erreur 401 - Clé API invalide ou expirée")
            elif response.status_code == 429:
                error_msg = "Limite de taux dépassée. Veuillez réessayer dans quelques minutes."
                logger.error("❌ Erreur 429 - Limite de taux dépassée")
            elif response.status_code == 500:
                error_msg = "Erreur serveur OpenAI. Veuillez réessayer plus tard."
                logger.error("❌ Erreur 500 - Problème serveur OpenAI")
            else:
                error_msg = f"Erreur API: {response.status_code}"
            
            return {
                "success": False,
                "error": error_msg,
                "analysis": "Erreur lors de l'analyse GPT"
            }"""
        
        if old_error_handling in content:
            content = content.replace(old_error_handling, new_error_handling)
            
            with open('gpt_analysis.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Gestion d'erreur améliorée dans gpt_analysis.py")
            return True
        else:
            print("⚠️ Section de gestion d'erreur non trouvée dans gpt_analysis.py")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'amélioration de gpt_analysis.py: {e}")
        return False

def improve_app_error_handling():
    """Améliore la gestion des erreurs dans app.py"""
    print("\n🔧 Amélioration de la gestion des erreurs dans app.py...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier si les améliorations sont déjà présentes
        if "Clé API invalide ou expirée" in content:
            print("✅ Gestion d'erreur API déjà présente dans app.py")
            return True
        
        # Améliorer la gestion des erreurs dans analyze_ia
        old_error_check = """        if not ia_response.get("success", False):
            error_msg = ia_response.get("error", "Erreur inconnue lors de l'analyse IA")
            print(f"❌ [ANALYZE_IA] Erreur GPT: {error_msg}")
            log_error(user_id, "analyze_ia_gpt_error", f"Erreur GPT: {error_msg}", request.remote_addr, request.headers.get('User-Agent'))
            return jsonify({"error": f"Erreur lors de l'analyse IA: {error_msg}"}), 500"""
        
        new_error_check = """        if not ia_response.get("success", False):
            error_msg = ia_response.get("error", "Erreur inconnue lors de l'analyse IA")
            print(f"❌ [ANALYZE_IA] Erreur GPT: {error_msg}")
            
            # Logging détaillé selon le type d'erreur
            if "Clé API invalide" in error_msg or "401" in error_msg:
                log_error(user_id, "analyze_ia_api_key_error", f"Erreur clé API: {error_msg}", request.remote_addr, request.headers.get('User-Agent'))
                error_msg = "Erreur de clé API. Veuillez vérifier votre configuration API dans votre profil."
            elif "429" in error_msg:
                log_error(user_id, "analyze_ia_rate_limit", f"Limite de taux: {error_msg}", request.remote_addr, request.headers.get('User-Agent'))
                error_msg = "Limite de taux dépassée. Veuillez réessayer dans quelques minutes."
            else:
                log_error(user_id, "analyze_ia_gpt_error", f"Erreur GPT: {error_msg}", request.remote_addr, request.headers.get('User-Agent'))
            
            return jsonify({"error": f"Erreur lors de l'analyse IA: {error_msg}"}), 500"""
        
        if old_error_check in content:
            content = content.replace(old_error_check, new_error_check)
            
            with open('app.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Gestion d'erreur améliorée dans app.py")
            return True
        else:
            print("⚠️ Section de gestion d'erreur non trouvée dans app.py")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'amélioration de app.py: {e}")
        return False

def add_api_key_validation():
    """Ajoute une validation améliorée des clés API"""
    print("\n🔧 Ajout de validation des clés API...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier si la validation est déjà présente
        if "def validate_api_key" in content:
            print("✅ Fonction de validation API déjà présente")
            return True
        
        # Ajouter la fonction de validation avant get_openai_api_key
        validation_function = '''
def validate_api_key(api_key):
    """
    Valide une clé API OpenAI
    """
    if not api_key:
        return False, "Aucune clé API fournie"
    
    if not api_key.startswith('sk-'):
        return False, "Format de clé API invalide (doit commencer par 'sk-')"
    
    if len(api_key) < 20:
        return False, "Clé API trop courte"
    
    return True, "Clé API valide"

'''
        
        # Insérer la fonction avant get_openai_api_key
        if "def get_openai_api_key" in content:
            content = content.replace("def get_openai_api_key", validation_function + "def get_openai_api_key")
            
            with open('app.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Fonction de validation API ajoutée")
            return True
        else:
            print("⚠️ Fonction get_openai_api_key non trouvée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la validation: {e}")
        return False

def improve_api_config_validation():
    """Améliore la validation dans les routes de configuration API"""
    print("\n🔧 Amélioration de la validation dans les routes API...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Améliorer la validation dans update_api_config
        old_validation = """            # Validation basique de la clé API
            if not custom_api_key.startswith(('sk-', 'pk-', 'Bearer ')):
                db.close()
                return jsonify({"error": "Format de clé API invalide"}), 400"""
        
        new_validation = """            # Validation améliorée de la clé API
            is_valid, validation_msg = validate_api_key(custom_api_key)
            if not is_valid:
                db.close()
                return jsonify({"error": f"Clé API invalide: {validation_msg}"}), 400"""
        
        if old_validation in content:
            content = content.replace(old_validation, new_validation)
            
            with open('app.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Validation API améliorée dans les routes")
            return True
        else:
            print("⚠️ Section de validation non trouvée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'amélioration de la validation: {e}")
        return False

def create_api_key_test_script():
    """Crée un script de test pour les clés API"""
    print("\n📝 Création d'un script de test pour les clés API...")
    
    test_script = '''#!/usr/bin/env python3
"""
Script de test rapide pour vérifier une clé API
Usage: python test_api_key.py [clé_api]
"""

import sys
import requests

def test_api_key(api_key):
    """Teste une clé API avec l'API OpenAI"""
    print(f"🧪 Test de la clé API: {api_key[:10]}...")
    
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
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Clé API valide!")
            return True
        elif response.status_code == 401:
            print("❌ Erreur 401 - Clé API invalide ou expirée")
            print("💡 Solutions:")
            print("   - Vérifiez votre clé sur https://platform.openai.com/api-keys")
            print("   - Vérifiez votre facturation sur https://platform.openai.com/account/billing")
            return False
        elif response.status_code == 429:
            print("⚠️ Erreur 429 - Limite de taux dépassée")
            return False
        else:
            print(f"❌ Erreur {response.status_code}: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_api_key.py [clé_api]")
        print("Exemple: python test_api_key.py sk-1234567890abcdef...")
        sys.exit(1)
    
    api_key = sys.argv[1]
    success = test_api_key(api_key)
    sys.exit(0 if success else 1)
'''
    
    try:
        with open('test_api_key.py', 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        # Rendre le script exécutable
        os.chmod('test_api_key.py', 0o755)
        
        print("✅ Script test_api_key.py créé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du script: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Amélioration de la gestion des erreurs de clé API")
    print("=" * 60)
    
    improvements = [
        ("Gestion d'erreur dans gpt_analysis.py", improve_gpt_analysis_error_handling),
        ("Gestion d'erreur dans app.py", improve_app_error_handling),
        ("Validation des clés API", add_api_key_validation),
        ("Validation dans les routes API", improve_api_config_validation),
        ("Script de test API", create_api_key_test_script)
    ]
    
    results = []
    
    for improvement_name, improvement_func in improvements:
        print(f"\n{'='*20} {improvement_name} {'='*20}")
        try:
            success = improvement_func()
            results.append((improvement_name, success))
        except Exception as e:
            print(f"❌ Exception dans {improvement_name}: {e}")
            results.append((improvement_name, False))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES AMÉLIORATIONS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for improvement_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {improvement_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Résultat: {passed}/{total} améliorations appliquées")
    
    if passed == total:
        print("🎉 Toutes les améliorations ont été appliquées!")
        print("\n📋 PROCHAINES ÉTAPES:")
        print("1. Redémarrez l'application")
        print("2. Testez votre clé API avec: python test_api_key.py [votre_clé]")
        print("3. Configurez une clé API valide dans l'application")
        print("4. Vérifiez les logs pour des messages d'erreur plus détaillés")
    else:
        print("⚠️ Certaines améliorations ont échoué. Vérifiez les erreurs ci-dessus.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 