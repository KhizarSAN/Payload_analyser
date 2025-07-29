#!/usr/bin/env python3
"""
Script de test pour la nouvelle architecture TGI Mistral
Teste tous les services et endpoints
"""

import requests
import time
import json
import sys

# Configuration
TGI_URL = "http://localhost:8080"
CHROMA_URL = "http://localhost:8000"
RETRIEVER_URL = "http://localhost:5001"  # Port corrigé
WEB_URL = "http://localhost"

def print_status(message, status="INFO"):
    """Affiche un message avec couleur"""
    colors = {
        "INFO": "\033[94m",    # Blue
        "SUCCESS": "\033[92m", # Green
        "ERROR": "\033[91m",   # Red
        "WARNING": "\033[93m"  # Yellow
    }
    color = colors.get(status, "\033[0m")
    print(f"{color}{message}\033[0m")

def test_service(url, name, health_endpoint="/health"):
    """Teste un service"""
    try:
        response = requests.get(f"{url}{health_endpoint}", timeout=10)
        if response.status_code == 200:
            print_status(f"✅ {name} fonctionnel", "SUCCESS")
            return True
        else:
            print_status(f"❌ {name} erreur {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_status(f"❌ {name} non accessible: {e}", "ERROR")
        return False

def test_tgi_mistral():
    """Teste TGI Mistral"""
    print_status("🧪 Test TGI Mistral...", "INFO")
    
    # Test health
    if not test_service(TGI_URL, "TGI Mistral", "/health"):
        return False
    
    # Test génération
    try:
        response = requests.post(
            f"{TGI_URL}/generate",
            json={
                "prompt": "Test simple",
                "max_new_tokens": 50,
                "temperature": 0.7
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "generated_text" in result:
                print_status("✅ Génération TGI fonctionnelle", "SUCCESS")
                return True
            else:
                print_status("❌ Réponse TGI invalide", "ERROR")
                return False
        else:
            print_status(f"❌ Erreur génération TGI: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_status(f"❌ Erreur test TGI: {e}", "ERROR")
        return False

def test_chromadb():
    """Teste ChromaDB"""
    print_status("🧪 Test ChromaDB...", "INFO")
    return test_service(CHROMA_URL, "ChromaDB", "/api/v1/heartbeat")

def test_retriever():
    """Teste le service Retriever"""
    print_status("🧪 Test Retriever...", "INFO")
    
    # Test health
    if not test_service(RETRIEVER_URL, "Retriever"):
        return False
    
    # Test stats
    try:
        response = requests.get(f"{RETRIEVER_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print_status(f"✅ Stats Retriever: {stats}", "SUCCESS")
        else:
            print_status(f"❌ Erreur stats Retriever: {response.status_code}", "ERROR")
    except Exception as e:
        print_status(f"❌ Erreur stats Retriever: {e}", "ERROR")
    
    return True

def test_analysis():
    """Teste l'analyse complète"""
    print_status("🧪 Test analyse complète...", "INFO")
    
    test_payload = {
        "payload": "Test payload QRadar - Suspicious activity detected from IP 192.168.1.100"
    }
    
    try:
        response = requests.post(
            f"{RETRIEVER_URL}/analyze",
            json=test_payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if "analysis" in result:
                print_status("✅ Analyse Retriever fonctionnelle", "SUCCESS")
                print_status(f"📊 Contexte trouvé: {result.get('context_count', 0)} analyses", "INFO")
                return True
            else:
                print_status("❌ Réponse analyse invalide", "ERROR")
                return False
        else:
            print_status(f"❌ Erreur analyse: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"❌ Erreur test analyse: {e}", "ERROR")
        return False

def test_web_integration():
    """Teste l'intégration web"""
    print_status("🧪 Test intégration web...", "INFO")
    
    # Test page principale
    try:
        response = requests.get(WEB_URL, timeout=10)
        if response.status_code == 200:
            print_status("✅ Application web accessible", "SUCCESS")
        else:
            print_status(f"❌ Erreur application web: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_status(f"❌ Application web non accessible: {e}", "ERROR")
        return False
    
    # Test API Mistral
    test_payload = {
        "payload": json.dumps({
            "pattern": "test_pattern",
            "source": "test_source",
            "data": "Test data for web integration"
        })
    }
    
    try:
        response = requests.post(
            f"{WEB_URL}/analyze_mistral",
            json=test_payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if "mistral_text" in result:
                print_status("✅ API Mistral web fonctionnelle", "SUCCESS")
                return True
            else:
                print_status("❌ Réponse API Mistral web invalide", "ERROR")
                return False
        else:
            print_status(f"❌ Erreur API Mistral web: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_status(f"❌ Erreur test API Mistral web: {e}", "ERROR")
        return False

def main():
    """Fonction principale"""
    print_status("🚀 TEST COMPLET ARCHITECTURE TGI MISTRAL", "INFO")
    print_status("=========================================", "INFO")
    
    tests = [
        ("TGI Mistral", test_tgi_mistral),
        ("ChromaDB", test_chromadb),
        ("Retriever", test_retriever),
        ("Analyse complète", test_analysis),
        ("Intégration web", test_web_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print_status(f"\n📋 {test_name}", "INFO")
        print_status("-" * 30, "INFO")
        
        if test_func():
            passed += 1
        else:
            print_status(f"❌ Test {test_name} échoué", "ERROR")
    
    # Résultats
    print_status(f"\n📊 RÉSULTATS: {passed}/{total} tests réussis", "INFO")
    
    if passed == total:
        print_status("🎉 TOUS LES TESTS RÉUSSIS - Architecture TGI Mistral opérationnelle!", "SUCCESS")
        return True
    else:
        print_status("⚠️ CERTAINS TESTS ONT ÉCHOUÉ - Vérifiez les services", "WARNING")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 