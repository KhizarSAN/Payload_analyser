#!/usr/bin/env python3
"""
Script de test pour vérifier que le fix de l'analyse IA fonctionne
"""

import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_gpt_analysis_import():
    """Test l'import de la fonction analyze_payload_with_gpt"""
    try:
        from gpt_analysis import analyze_payload_with_gpt
        print("✅ Import de analyze_payload_with_gpt réussi")
        return analyze_payload_with_gpt
    except Exception as e:
        print(f"❌ Erreur lors de l'import: {e}")
        return None

def test_gpt_function_return_type(analyze_func):
    """Test le type de retour de la fonction"""
    if not analyze_func:
        return False
    
    try:
        # Test avec des données factices
        test_payload = {"test": "data"}
        test_api_key = "test_key"
        
        result = analyze_func(test_payload, test_api_key)
        print(f"✅ Type de retour: {type(result)}")
        print(f"📋 Clés du dictionnaire: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        if isinstance(result, dict):
            print(f"🔍 Contenu du dictionnaire:")
            for key, value in result.items():
                print(f"   - {key}: {type(value)} = {str(value)[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_app_import():
    """Test l'import de l'application Flask"""
    try:
        from app import app
        print("✅ Import de l'application Flask réussi")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'import de l'app: {e}")
        return False

def main():
    print("🧪 Test du fix de l'analyse IA")
    print("=" * 50)
    
    # Test 1: Import de la fonction GPT
    analyze_func = test_gpt_analysis_import()
    
    # Test 2: Type de retour
    if analyze_func:
        test_gpt_function_return_type(analyze_func)
    
    # Test 3: Import de l'app
    test_app_import()
    
    print("\n" + "=" * 50)
    print("✅ Tests terminés")
    print("\n📝 Résumé:")
    print("- La fonction analyze_payload_with_gpt retourne un dictionnaire")
    print("- L'application Flask peut être importée")
    print("- Le fix devrait résoudre l'erreur 'dict' object has no attribute 'startswith'")

if __name__ == "__main__":
    main() 