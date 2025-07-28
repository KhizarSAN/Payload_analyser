#!/usr/bin/env python3
"""
Script de vérification et correction des permissions pour profile_photos
"""

import os
import stat
import pwd
import grp
import sys

def check_and_fix_permissions():
    """Vérifie et corrige les permissions du répertoire profile_photos"""
    
    # Chemin du répertoire
    photos_dir = os.path.join(os.getcwd(), "profile_photos")
    
    print(f"🔍 Vérification des permissions pour: {photos_dir}")
    
    try:
        # Vérifier si le répertoire existe
        if not os.path.exists(photos_dir):
            print(f"📁 Création du répertoire: {photos_dir}")
            os.makedirs(photos_dir, exist_ok=True)
        
        # Obtenir les informations actuelles
        current_stat = os.stat(photos_dir)
        current_permissions = stat.filemode(current_stat.st_mode)
        current_owner = pwd.getpwuid(current_stat.st_uid).pw_name
        current_group = grp.getgrgid(current_stat.st_gid).gr_name
        
        print(f"📊 Permissions actuelles: {current_permissions}")
        print(f"👤 Propriétaire: {current_owner}")
        print(f"👥 Groupe: {current_group}")
        
        # Vérifier les permissions d'écriture
        if os.access(photos_dir, os.W_OK):
            print("✅ Permissions d'écriture OK")
        else:
            print("❌ Pas de permissions d'écriture")
            
            # Essayer de corriger les permissions
            try:
                # Définir les permissions 755 (rwxr-xr-x)
                os.chmod(photos_dir, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                print("🔧 Permissions corrigées à 755")
                
                # Vérifier à nouveau
                if os.access(photos_dir, os.W_OK):
                    print("✅ Permissions d'écriture maintenant OK")
                else:
                    print("❌ Impossible de corriger les permissions")
                    
            except PermissionError as e:
                print(f"❌ Erreur lors de la correction des permissions: {e}")
                return False
        
        # Test d'écriture
        test_file = os.path.join(photos_dir, "test_permissions.txt")
        try:
            with open(test_file, 'w') as f:
                f.write("Test de permissions")
            os.remove(test_file)
            print("✅ Test d'écriture réussi")
            return True
            
        except Exception as e:
            print(f"❌ Test d'écriture échoué: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Script de vérification des permissions")
    print("=" * 50)
    
    success = check_and_fix_permissions()
    
    print("=" * 50)
    if success:
        print("✅ Vérification terminée avec succès")
        sys.exit(0)
    else:
        print("❌ Vérification échouée")
        sys.exit(1) 