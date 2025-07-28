#!/usr/bin/env python3
"""
Script de vérification du mapping des données
Vérifie que toutes les données sont bien triées, classées et rangées
"""

import os
import sys
from datetime import datetime, timezone
from db_config import SessionLocal, Pattern, Analysis, User

def verify_data_mapping():
    """Vérifie le mapping des données dans toutes les tables"""
    
    try:
        db = SessionLocal()
        
        print("🔍 Vérification du mapping des données...")
        print("=" * 60)
        
        # 1. Vérifier les patterns
        print("\n📋 VÉRIFICATION DES PATTERNS:")
        patterns = db.query(Pattern).all()
        print(f"Nombre de patterns: {len(patterns)}")
        
        for i, p in enumerate(patterns[:5]):  # Afficher les 5 premiers
            print(f"\nPattern {i+1}:")
            print(f"  - ID: {p.id}")
            print(f"  - Nom: {p.nom}")
            print(f"  - Résumé: {p.resume[:50] if p.resume else 'N/A'}...")
            print(f"  - Description: {p.description[:50] if p.description else 'N/A'}...")
            print(f"  - Status: {p.status}")
            print(f"  - Feedback: {p.feedback[:50] if p.feedback else 'N/A'}...")
            print(f"  - Tags: {p.tags}")
            print(f"  - User ID: {p.user_id}")
            print(f"  - Créé le: {p.created_at}")
            print(f"  - Modifié le: {p.updated_at}")
        
        # 2. Vérifier les analyses
        print("\n📊 VÉRIFICATION DES ANALYSES:")
        analyses = db.query(Analysis).all()
        print(f"Nombre d'analyses: {len(analyses)}")
        
        for i, a in enumerate(analyses[:5]):  # Afficher les 5 premiers
            print(f"\nAnalyse {i+1}:")
            print(f"  - ID: {a.id}")
            print(f"  - Pattern ID: {a.pattern_id}")
            print(f"  - Pattern Nom: {a.pattern_nom}")
            print(f"  - Payload: {a.payload[:50] if a.payload else 'N/A'}...")
            print(f"  - Résumé court: {a.resume_court[:50] if a.resume_court else 'N/A'}...")
            print(f"  - Description faits: {a.description_faits[:50] if a.description_faits else 'N/A'}...")
            print(f"  - Analyse technique: {a.analyse_technique[:50] if a.analyse_technique else 'N/A'}...")
            print(f"  - Résultat: {a.resultat[:50] if a.resultat else 'N/A'}...")
            print(f"  - Justification: {a.justification[:50] if a.justification else 'N/A'}...")
            print(f"  - Rapport complet: {a.rapport_complet[:50] if a.rapport_complet else 'N/A'}...")
            print(f"  - Tags: {a.tags}")
            print(f"  - Statut: {a.statut}")
            print(f"  - User ID: {a.user_id}")
            print(f"  - Créé le: {a.created_at}")
            print(f"  - Modifié le: {a.updated_at}")
        
        # 3. Vérifier les relations
        print("\n🔗 VÉRIFICATION DES RELATIONS:")
        
        # Patterns avec analyses
        patterns_with_analyses = db.query(Pattern).join(Analysis).distinct().count()
        print(f"Patterns avec analyses: {patterns_with_analyses}")
        
        # Patterns sans analyses
        patterns_without_analyses = db.query(Pattern).outerjoin(Analysis).filter(Analysis.id.is_(None)).count()
        print(f"Patterns sans analyses: {patterns_without_analyses}")
        
        # Analyses sans pattern
        analyses_without_pattern = db.query(Analysis).outerjoin(Pattern).filter(Pattern.id.is_(None)).count()
        print(f"Analyses sans pattern: {analyses_without_pattern}")
        
        # 4. Vérifier la cohérence des données
        print("\n✅ VÉRIFICATION DE LA COHÉRENCE:")
        
        # Vérifier que les patterns ont des noms
        patterns_without_name = db.query(Pattern).filter(Pattern.nom.is_(None) | (Pattern.nom == "")).count()
        print(f"Patterns sans nom: {patterns_without_name}")
        
        # Vérifier que les analyses ont des payloads
        analyses_without_payload = db.query(Analysis).filter(Analysis.payload.is_(None) | (Analysis.payload == "")).count()
        print(f"Analyses sans payload: {analyses_without_payload}")
        
        # Vérifier les statuts
        status_counts = db.query(Analysis.statut, db.func.count(Analysis.id)).group_by(Analysis.statut).all()
        print("\nRépartition des statuts dans les analyses:")
        for status, count in status_counts:
            print(f"  - {status}: {count}")
        
        pattern_status_counts = db.query(Pattern.status, db.func.count(Pattern.id)).group_by(Pattern.status).all()
        print("\nRépartition des statuts dans les patterns:")
        for status, count in pattern_status_counts:
            print(f"  - {status}: {count}")
        
        # 5. Vérifier les utilisateurs
        print("\n👥 VÉRIFICATION DES UTILISATEURS:")
        users = db.query(User).all()
        print(f"Nombre d'utilisateurs: {len(users)}")
        
        for user in users:
            user_patterns = db.query(Pattern).filter_by(user_id=user.id).count()
            user_analyses = db.query(Analysis).filter_by(user_id=user.id).count()
            print(f"  - {user.username}: {user_patterns} patterns, {user_analyses} analyses")
        
        print("\n" + "=" * 60)
        print("✅ Vérification terminée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        sys.exit(1)
    finally:
        db.close()

def create_sample_data():
    """Crée des données d'exemple pour tester le mapping"""
    
    try:
        db = SessionLocal()
        
        # Récupérer le premier utilisateur
        user = db.query(User).first()
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return
        
        print(f"👤 Utilisateur trouvé: {user.username}")
        
        # Créer un pattern d'exemple
        pattern = Pattern(
            nom="Test Pattern Mapping",
            resume="Test de vérification du mapping des données",
            description="Description technique détaillée du pattern",
            status="à surveiller",
            feedback="Pattern de test pour vérification",
            tags="test,mapping,verification",
            user_id=user.id
        )
        db.add(pattern)
        db.flush()
        
        # Créer une analyse associée
        analysis = Analysis(
            payload='{"test": "payload", "data": "example"}',
            pattern_id=pattern.id,
            pattern_nom=pattern.nom,
            resume_court=pattern.resume,
            description_faits="Fait de test pour vérification",
            analyse_technique=pattern.description,
            resultat="Résultat de test",
            justification="Justification de test",
            rapport_complet="Rapport complet de test",
            user_id=user.id,
            tags=pattern.tags,
            statut=pattern.status
        )
        db.add(analysis)
        db.commit()
        
        print("✅ Données d'exemple créées avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des données d'exemple: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Vérification du mapping des données...")
    
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        create_sample_data()
    else:
        verify_data_mapping()
    
    print("\n✅ Script terminé!") 