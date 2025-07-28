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

# Démarrer l'application
echo "🚀 Démarrage de l'application..."
python3 app.py 