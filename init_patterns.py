#!/usr/bin/env python3
"""
Script pour initialiser des patterns de test
"""

import os
import sys
from datetime import datetime, timezone
from db_config import SessionLocal, Pattern, User

def init_test_patterns():
    """Initialise des patterns de test"""
    
    try:
        db = SessionLocal()
        
        # Récupérer le premier utilisateur (admin)
        user = db.query(User).first()
        if not user:
            print("❌ Aucun utilisateur trouvé. Créez d'abord un utilisateur admin.")
            return
        
        print(f"👤 Utilisateur trouvé: {user.username}")
        
        # Patterns de test
        test_patterns = [
            {
                "nom": "Échec EAP NPS",
                "resume": "Échec d'authentification EAP sur serveur NPS",
                "description": "Tentative d'authentification EAP échouée sur le serveur Network Policy Server",
                "status": "critique",
                "feedback": "Pattern validé par l'équipe SOC",
                "tags": "authentication,eap,nps",
                "categorie": "Authentification",
                "criticite": "Élevée"
            },
            {
                "nom": "Tentative SQL Injection",
                "resume": "Détection d'une tentative d'injection SQL",
                "description": "Requête SQL suspecte détectée dans les logs d'application",
                "status": "à surveiller",
                "feedback": "À investiguer plus en détail",
                "tags": "sql,injection,security",
                "categorie": "Sécurité",
                "criticite": "Moyenne"
            },
            {
                "nom": "Connexion VPN Anormale",
                "resume": "Connexion VPN depuis une IP non autorisée",
                "description": "Tentative de connexion VPN depuis une adresse IP non dans la liste blanche",
                "status": "ignoré",
                "feedback": "Faux positif - IP légitime",
                "tags": "vpn,network,access",
                "categorie": "Réseau",
                "criticite": "Faible"
            },
            {
                "nom": "Suppression Fichier Système",
                "resume": "Suppression d'un fichier système critique",
                "description": "Tentative de suppression d'un fichier système important",
                "status": "vrai positif",
                "feedback": "Incident confirmé - action corrective en cours",
                "tags": "filesystem,deletion,incident",
                "categorie": "Système",
                "criticite": "Critique"
            },
            {
                "nom": "Brute Force SSH",
                "resume": "Tentative de brute force sur service SSH",
                "description": "Multiples tentatives de connexion SSH échouées depuis la même IP",
                "status": "faux positif",
                "feedback": "Test de sécurité légitime",
                "tags": "ssh,bruteforce,security",
                "categorie": "Sécurité",
                "criticite": "Élevée"
            }
        ]
        
        # Vérifier si des patterns existent déjà
        existing_patterns = db.query(Pattern).count()
        if existing_patterns > 0:
            print(f"ℹ️ {existing_patterns} patterns existent déjà. Suppression des anciens patterns...")
            db.query(Pattern).delete()
            db.commit()
        
        # Créer les nouveaux patterns
        created_count = 0
        for pattern_data in test_patterns:
            try:
                pattern = Pattern(
                    nom=pattern_data["nom"],
                    resume=pattern_data["resume"],
                    description=pattern_data["description"],
                    status=pattern_data["status"],
                    feedback=pattern_data["feedback"],
                    tags=pattern_data["tags"],
                    categorie=pattern_data["categorie"],
                    criticite=pattern_data["criticite"],
                    user_id=user.id,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                db.add(pattern)
                created_count += 1
                print(f"✅ Pattern créé: {pattern_data['nom']}")
                
            except Exception as e:
                print(f"❌ Erreur lors de la création du pattern {pattern_data['nom']}: {e}")
        
        db.commit()
        print(f"\n🎉 {created_count} patterns de test créés avec succès!")
        
        # Afficher un résumé
        print("\n📊 Résumé des patterns créés:")
        patterns = db.query(Pattern).all()
        for pattern in patterns:
            print(f"  - {pattern.nom} (Status: {pattern.status}, Catégorie: {pattern.categorie})")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Fonction principale pour l'initialisation"""
    print("🚀 Initialisation des patterns de test...")
    init_test_patterns()
    print("\n✅ Script terminé!")

if __name__ == "__main__":
    main() 