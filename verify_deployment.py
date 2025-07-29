#!/usr/bin/env python3
"""
Script de vérification complète avant déploiement
Vérifie tous les fichiers et configurations
"""

import os
import sys
import json
import yaml
from pathlib import Path

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

def check_file_exists(filepath, description):
    """Vérifie qu'un fichier existe"""
    if os.path.exists(filepath):
        print_status(f"✅ {description}: {filepath}", "SUCCESS")
        return True
    else:
        print_status(f"❌ {description}: {filepath} - FICHIER MANQUANT", "ERROR")
        return False

def check_docker_compose():
    """Vérifie la configuration docker-compose.yml"""
    print_status("\n🔍 Vérification docker-compose.yml", "INFO")
    
    compose_file = "Docker/docker-compose.yml"
    if not check_file_exists(compose_file, "Docker Compose"):
        return False
    
    try:
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Vérifications spécifiques
        checks = [
            ("TGI service", "tgi:" in content),
            ("ChromaDB service", "chromadb:" in content),
            ("Retriever service", "retriever:" in content),
            ("Web service", "web:" in content),
            ("MySQL service", "db:" in content),
            ("Nginx service", "nginx:" in content),
            ("Modèle local", "/models/mistral-7b" in content),
            ("Pas de HF_HUB_TOKEN", "HF_HUB_TOKEN" not in content),
            ("Ports corrects", "8080:80" in content and "5001:5000" in content),
        ]
        
        all_good = True
        for check_name, condition in checks:
            if condition:
                print_status(f"  ✅ {check_name}", "SUCCESS")
            else:
                print_status(f"  ❌ {check_name}", "ERROR")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print_status(f"❌ Erreur lecture docker-compose.yml: {e}", "ERROR")
        return False

def check_retriever_service():
    """Vérifie le service Retriever"""
    print_status("\n🔍 Vérification service Retriever", "INFO")
    
    checks = [
        ("Dockerfile", "Docker/retriever/Dockerfile"),
        ("requirements.txt", "Docker/retriever/requirements.txt"),
        ("app.py", "Docker/retriever/app.py"),
    ]
    
    all_good = True
    for check_name, filepath in checks:
        if not check_file_exists(filepath, check_name):
            all_good = False
    
    # Vérifier les dépendances
    if all_good:
        try:
            with open("Docker/retriever/requirements.txt", 'r') as f:
                requirements = f.read()
            
            deps = [
                "fastapi", "uvicorn", "requests", "chromadb", 
                "sentence-transformers", "sqlalchemy", "pymysql"
            ]
            
            for dep in deps:
                if dep in requirements:
                    print_status(f"  ✅ Dépendance {dep}", "SUCCESS")
                else:
                    print_status(f"  ❌ Dépendance manquante: {dep}", "ERROR")
                    all_good = False
        except Exception as e:
            print_status(f"❌ Erreur lecture requirements: {e}", "ERROR")
            all_good = False
    
    return all_good

def check_app_integration():
    """Vérifie l'intégration dans app.py"""
    print_status("\n🔍 Vérification intégration app.py", "INFO")
    
    if not check_file_exists("app.py", "Application principale"):
        return False
    
    try:
        with open("app.py", 'r') as f:
            content = f.read()
        
        checks = [
            ("Import requests", "import requests" in content),
            ("Route analyze_mistral", "@app.route(\"/analyze_mistral\"" in content),
            ("MISTRAL_LEARNER_URL", "MISTRAL_LEARNER_URL" in content),
            ("Appel retriever", "MISTRAL_LEARNER_URL" in content),
            ("Logging Mistral", "analyze_mistral_tgi" in content),
        ]
        
        all_good = True
        for check_name, condition in checks:
            if condition:
                print_status(f"  ✅ {check_name}", "SUCCESS")
            else:
                print_status(f"  ❌ {check_name}", "ERROR")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print_status(f"❌ Erreur lecture app.py: {e}", "ERROR")
        return False

def check_frontend_integration():
    """Vérifie l'intégration frontend"""
    print_status("\n🔍 Vérification intégration frontend", "INFO")
    
    dashboard_file = "templates/dashboard.html"
    if not check_file_exists(dashboard_file, "Dashboard"):
        return False
    
    try:
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        checks = [
            ("Bouton Mistral", "analyzeMistralBtn" in content),
            ("Fonction Mistral", "analyzePayloadMistral" in content),
            ("Appel API", "/analyze_mistral" in content),
            ("Gestion réponse", "mistral_text" in content),
        ]
        
        all_good = True
        for check_name, condition in checks:
            if condition:
                print_status(f"  ✅ {check_name}", "SUCCESS")
            else:
                print_status(f"  ❌ {check_name}", "ERROR")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print_status(f"❌ Erreur lecture dashboard: {e}", "ERROR")
        return False

def check_scripts():
    """Vérifie les scripts de déploiement"""
    print_status("\n🔍 Vérification scripts", "INFO")
    
    scripts = [
        ("Script téléchargement Linux", "download_mistral_local.sh"),
        ("Script téléchargement Windows", "download_mistral_local.ps1"),
        ("Script déploiement", "deploy_mistral_local.sh"),
        ("Documentation", "README_MISTRAL_LOCAL.md"),
    ]
    
    all_good = True
    for script_name, filepath in scripts:
        if not check_file_exists(filepath, script_name):
            all_good = False
    
    return all_good

def check_version_conflicts():
    """Vérifie les conflits de version"""
    print_status("\n🔍 Vérification conflits de version", "INFO")
    
    # Vérifier ChromaDB version
    try:
        with open("Docker/retriever/requirements.txt", 'r') as f:
            retriever_reqs = f.read()
        
        # Extraire version ChromaDB
        import re
        chroma_match = re.search(r'chromadb==([\d.]+)', retriever_reqs)
        if chroma_match:
            chroma_version = chroma_match.group(1)
            print_status(f"  📊 Version ChromaDB dans retriever: {chroma_version}", "INFO")
            
            # Vérifier compatibilité avec docker-compose
            with open("Docker/docker-compose.yml", 'r') as f:
                compose_content = f.read()
            
            compose_chroma_match = re.search(r'chromadb/chroma:([\d.]+)', compose_content)
            if compose_chroma_match:
                compose_chroma_version = compose_chroma_match.group(1)
                print_status(f"  📊 Version ChromaDB dans docker-compose: {compose_chroma_version}", "INFO")
                
                if chroma_version.startswith(compose_chroma_version):
                    print_status("  ✅ Versions ChromaDB compatibles", "SUCCESS")
                else:
                    print_status("  ⚠️ Versions ChromaDB différentes - vérifier compatibilité", "WARNING")
        
        # Vérifier NumPy version
        numpy_match = re.search(r'numpy==([\d.]+)', retriever_reqs)
        if numpy_match:
            numpy_version = numpy_match.group(1)
            print_status(f"  📊 Version NumPy: {numpy_version}", "INFO")
            
            if numpy_version.startswith("1."):
                print_status("  ✅ Version NumPy compatible (1.x)", "SUCCESS")
            else:
                print_status("  ⚠️ Version NumPy 2.x - risque de conflit", "WARNING")
        
        return True
        
    except Exception as e:
        print_status(f"❌ Erreur vérification versions: {e}", "ERROR")
        return False

def check_directory_structure():
    """Vérifie la structure des dossiers"""
    print_status("\n🔍 Vérification structure dossiers", "INFO")
    
    directories = [
        ("Docker", "Docker/"),
        ("Retriever", "Docker/retriever/"),
        ("Templates", "templates/"),
        ("Static", "static/"),
    ]
    
    all_good = True
    for dir_name, dirpath in directories:
        if os.path.exists(dirpath):
            print_status(f"  ✅ {dir_name}: {dirpath}", "SUCCESS")
        else:
            print_status(f"  ❌ {dir_name}: {dirpath} - DOSSIER MANQUANT", "ERROR")
            all_good = False
    
    return all_good

def main():
    """Fonction principale"""
    print_status("🚀 VÉRIFICATION COMPLÈTE AVANT DÉPLOIEMENT", "INFO")
    print_status("==========================================", "INFO")
    
    checks = [
        ("Structure dossiers", check_directory_structure),
        ("Docker Compose", check_docker_compose),
        ("Service Retriever", check_retriever_service),
        ("Intégration app.py", check_app_integration),
        ("Intégration frontend", check_frontend_integration),
        ("Scripts", check_scripts),
        ("Conflits de version", check_version_conflicts),
    ]
    
    results = []
    for check_name, check_func in checks:
        print_status(f"\n📋 {check_name}", "INFO")
        print_status("-" * 40, "INFO")
        
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print_status(f"❌ Erreur lors de {check_name}: {e}", "ERROR")
            results.append((check_name, False))
    
    # Résumé final
    print_status("\n📊 RÉSUMÉ DES VÉRIFICATIONS", "INFO")
    print_status("=" * 40, "INFO")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print_status(f"{status} {check_name}")
    
    print_status(f"\n🎯 {passed}/{total} vérifications réussies", "INFO")
    
    if passed == total:
        print_status("\n🎉 TOUTES LES VÉRIFICATIONS RÉUSSIES !", "SUCCESS")
        print_status("Vous pouvez maintenant lancer le déploiement :", "SUCCESS")
        print_status("  bash deploy_mistral_local.sh", "SUCCESS")
        return True
    else:
        print_status("\n⚠️ CERTAINES VÉRIFICATIONS ONT ÉCHOUÉ", "WARNING")
        print_status("Corrigez les problèmes avant le déploiement", "WARNING")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 