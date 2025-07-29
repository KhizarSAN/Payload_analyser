#!/bin/bash

# Attendre que MySQL soit prêt
while ! mysqladmin ping -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" --silent; do
    sleep 1
done

# Vérifier les permissions du répertoire profile_photos
echo "🔍 Vérification des permissions..."
python3 check_permissions.py

# Initialiser la base de données
echo "🗄️ Initialisation de la base de données..."
python3 init_db.py

# Créer l'utilisateur admin
echo "👤 Création de l'utilisateur admin..."
python3 init_admin.py

# Initialiser les patterns de test
echo "📋 Initialisation des patterns de test..."
python3 init_patterns.py

# Initialiser Mistral (si le service est disponible)
echo "🤖 Initialisation de Mistral..."
if python3 init_mistral.py; then
    echo "✅ Mistral initialisé avec succès"
else
    echo "⚠️ Mistral non disponible, utilisation du mode fallback"
fi

# Démarrer l'application
echo "🚀 Démarrage de l'application..."
python3 app.py 