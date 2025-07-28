#!/usr/bin/env python3
"""
Script de test pour l'analyse IA
Teste les différentes parties de l'analyse IA
"""

import os
import sys
import json
from datetime import datetime, timezone

def test_ia_analysis():
    """Teste l'analyse IA étape par étape"""
    
    print("🧠 Test de l'analyse IA...")
    print("=" * 60)
    
    # Test 1: Vérifier la clé API
    print("\n1️⃣ Test de la clé API...")
    try:
        from app import get_openai_api_key
        api_key = get_openai_api_key()
        if api_key:
            print(f"✅ Clé API trouvée: {api_key[:10]}...")
        else:
            print("❌ Aucune clé API trouvée")
            return
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la clé API: {e}")
        return
    
    # Test 2: Test du parsing
    print("\n2️⃣ Test du parsing...")
    test_payload = {
        "ClientIP": "80.245.19.42",
        "UserId": "a.delaporte@rgen.fr",
        "Operation": "SoftDelete",
        "Workload": "Exchange",
        "ResultStatus": "Succeeded",
        "MailboxOwnerUPN": "savelec@rgen.fr",
        "CreationTime": "2025-07-21T06:53:30"
    }
    
    try:
        from parser import flatten_dict
        flat_fields = flatten_dict(test_payload)
        pattern_nom = flat_fields.get("pattern", "unknown_pattern")
        print(f"✅ Parsing réussi - Pattern: {pattern_nom}")
        print(f"   Champs extraits: {list(flat_fields.keys())}")
    except Exception as e:
        print(f"❌ Erreur lors du parsing: {e}")
        return
    
    # Test 3: Test de l'analyse GPT
    print("\n3️⃣ Test de l'analyse GPT...")
    try:
        from gpt_analysis import analyze_payload_with_gpt
        ia_response = analyze_payload_with_gpt(test_payload, api_key)
        
        if ia_response.startswith("[ERREUR]"):
            print(f"❌ Erreur GPT: {ia_response}")
            print("\n🔧 Test avec une réponse simulée...")
            ia_response = simulate_gpt_response(test_payload)
        else:
            print("✅ Analyse GPT réussie")
        
        print(f"Réponse IA:\n{ia_response}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse GPT: {e}")
        print("\n🔧 Test avec une réponse simulée...")
        ia_response = simulate_gpt_response(test_payload)
    
    # Test 4: Test de l'extraction des données
    print("\n4️⃣ Test de l'extraction des données...")
    try:
        import re
        pattern_match = re.search(r'Pattern du payload\s*[:：\-–]?\s*([^\n]{1,50})', ia_response)
        short_desc_match = re.search(r'Résumé court\s*[:：\-–]?\s*([^\n]{1,120})', ia_response)
        statut_match = re.search(r'Statut\s*[:：\-–]?\s*([^\n]{1,50})', ia_response)
        description_match = re.search(r'1\. Description des faits\s*\n(.+?)\n2\.', ia_response, re.DOTALL)
        analyse_technique_match = re.search(r'2\. Analyse technique\s*\n(.+?)\n3\.', ia_response, re.DOTALL)
        resultat_match = re.search(r'3\. Résultat\s*\n(.+)', ia_response, re.DOTALL)
        
        extracted_pattern = pattern_match.group(1).strip() if pattern_match else pattern_nom
        resume_court = short_desc_match.group(1).strip() if short_desc_match else ""
        statut = statut_match.group(1).strip() if statut_match else ""
        description_faits = description_match.group(1).strip() if description_match else ""
        analyse_technique = analyse_technique_match.group(1).strip() if analyse_technique_match else ""
        resultat = resultat_match.group(1).strip() if resultat_match else ""
        
        print(f"✅ Extraction réussie:")
        print(f"   - Pattern: {extracted_pattern}")
        print(f"   - Résumé: {resume_court}")
        print(f"   - Statut: {statut}")
        print(f"   - Description: {description_faits[:50]}...")
        print(f"   - Analyse: {analyse_technique[:50]}...")
        print(f"   - Résultat: {resultat[:50]}...")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction: {e}")
        return
    
    # Test 5: Test du stockage
    print("\n5️⃣ Test du stockage...")
    try:
        from pattern_storage import store_analysis
        store_analysis(
            payload=json.dumps(test_payload),
            rapport_ia=ia_response,
            pattern_nom=extracted_pattern,
            resume_court=resume_court,
            description_faits=description_faits,
            analyse_technique=analyse_technique,
            resultat=resultat,
            justification=resultat,
            user_id=1,  # Utilisateur de test
            tags=None,
            statut=statut
        )
        print("✅ Stockage réussi")
        
    except Exception as e:
        print(f"❌ Erreur lors du stockage: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test de l'analyse IA terminé!")

def simulate_gpt_response(payload):
    """Simule une réponse GPT pour les tests"""
    
    return f"""Pattern du payload : Suppression Exchange
Résumé court : Suppression d'élément Exchange par utilisateur externe
Statut : Faux positif
1. Description des faits
Une suppression d'élément Exchange a été effectuée depuis l'IP 80.245.19.42 par l'utilisateur a.delaporte@rgen.fr. L'opération a réussi et concerne le propriétaire savelec@rgen.fr.

2. Analyse technique
L'opération SoftDelete sur Exchange est une action administrative normale. L'IP source est externe mais l'utilisateur semble légitime. Aucun indicateur de compromission détecté.

3. Résultat
Il s'agit d'un faux positif. L'opération est légitime et fait partie des tâches administratives normales sur Exchange. Aucune action corrective requise."""

if __name__ == "__main__":
    test_ia_analysis() 