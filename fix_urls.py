#!/usr/bin/env python3
"""
Script pour corriger automatiquement les URLs dans les templates Flask
Remplace les chemins absolus par url_for() pour l'accès réseau
"""

import os
import re
from pathlib import Path

def fix_template_urls():
    """Corrige les URLs dans tous les templates"""
    
    templates_dir = Path("templates")
    if not templates_dir.exists():
        print("❌ Dossier templates non trouvé")
        return
    
    # Patterns à remplacer
    replacements = [
        # Liens CSS/JS
        (r'href="/static/([^"]+)"', r'href="{{ url_for(\'static\', filename=\'\1\') }}"'),
        (r'src="/static/([^"]+)"', r'src="{{ url_for(\'static\', filename=\'\1\') }}"'),
        
        # Liens de navigation
        (r'href="/menu"', r'href="{{ url_for(\'menu\') }}"'),
        (r'href="/analyze"', r'href="{{ url_for(\'analyze\') }}"'),
        (r'href="/exemples"', r'href="{{ url_for(\'exemples\') }}"'),
        (r'href="/analyses_history"', r'href="{{ url_for(\'analyses_history\') }}"'),
        (r'href="/user_profile"', r'href="{{ url_for(\'user_profile\') }}"'),
        (r'href="/settings"', r'href="{{ url_for(\'settings\') }}"'),
        (r'href="/logout"', r'href="{{ url_for(\'logout\') }}"'),
        (r'href="/login"', r'href="{{ url_for(\'login\') }}"'),
        (r'href="/logs"', r'href="{{ url_for(\'logs\') }}"'),
        
        # Redirections JavaScript
        (r'window\.location\.href=\'/menu\'', r'window.location.href=\'{{ url_for(\'menu\') }}\''),
        (r'window\.location\.href=\'/analyze\'', r'window.location.href=\'{{ url_for(\'analyze\') }}\''),
        (r'window\.location\.href=\'/exemples\'', r'window.location.href=\'{{ url_for(\'exemples\') }}\''),
        (r'window\.location\.href=\'/analyses_history\'', r'window.location.href=\'{{ url_for(\'analyses_history\') }}\''),
        (r'window\.location\.href=\'/user_profile\'', r'window.location.href=\'{{ url_for(\'user_profile\') }}\''),
        (r'window\.location\.href=\'/settings\'', r'window.location.href=\'{{ url_for(\'settings\') }}\''),
        (r'window\.location\.href=\'/logout\'', r'window.location.href=\'{{ url_for(\'logout\') }}\''),
        (r'window\.location\.href=\'/login\'', r'window.location.href=\'{{ url_for(\'login\') }}\''),
        (r'window\.location\.href=\'/logs\'', r'window.location.href=\'{{ url_for(\'logs\') }}\''),
    ]
    
    fixed_files = []
    
    for html_file in templates_dir.glob("*.html"):
        print(f"🔧 Traitement de {html_file.name}...")
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Appliquer tous les remplacements
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            # Si le contenu a changé, sauvegarder
            if content != original_content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_files.append(html_file.name)
                print(f"  ✅ {html_file.name} corrigé")
            else:
                print(f"  ⏭️ {html_file.name} déjà correct")
                
        except Exception as e:
            print(f"  ❌ Erreur lors du traitement de {html_file.name}: {e}")
    
    print(f"\n🎉 Correction terminée !")
    print(f"📁 Fichiers corrigés: {len(fixed_files)}")
    if fixed_files:
        print("📋 Liste des fichiers corrigés:")
        for file in fixed_files:
            print(f"  • {file}")

if __name__ == "__main__":
    print("🔧 CORRECTION AUTOMATIQUE DES URLS DANS LES TEMPLATES")
    print("=" * 60)
    fix_template_urls() 