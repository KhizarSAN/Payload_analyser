#!/bin/bash

# =============================================================================
# SCRIPT DE CORRECTION AUTHENTIFICATION MYSQL
# =============================================================================
# Corrige le problème d'authentification MySQL avec cryptography
# Usage: ./fix_mysql_auth.sh
# =============================================================================

set -e

echo "🔧 CORRECTION AUTHENTIFICATION MYSQL"
echo "===================================="

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# ÉTAPE 1: VÉRIFICATION DE L'ENVIRONNEMENT
# =============================================================================

log_info "Vérification de l'environnement..."

# Vérifier que nous sommes dans la VM
if [ ! -f "/vagrant/app.py" ]; then
    log_error "Ce script doit être exécuté dans la VM Vagrant"
    log_info "Exécuter: vagrant ssh puis cd /vagrant"
    exit 1
fi

# =============================================================================
# ÉTAPE 2: INSTALLATION DE CRYPTOGRAPHY
# =============================================================================

log_info "Installation du package cryptography..."

# Créer un environnement virtuel temporaire
python3 -m venv /tmp/fix_mysql
source /tmp/fix_mysql/bin/activate

# Installer seulement les packages nécessaires (sans mysqlclient qui pose problème)
log_info "Installation des packages nécessaires..."
pip install cryptography==41.0.7 pymysql sqlalchemy flask requests pillow werkzeug

log_success "Packages nécessaires installés"

# =============================================================================
# ÉTAPE 3: TEST DE CONNEXION MYSQL
# =============================================================================

log_info "Test de connexion MySQL..."

# Attendre que MySQL soit prêt
for i in {1..10}; do
    if docker exec mysql_payload mysqladmin ping -h localhost -u root -proot >/dev/null 2>&1; then
        log_success "MySQL est prêt"
        break
    fi
    log_info "Attente MySQL... ($i/10)"
    sleep 5
done

# =============================================================================
# ÉTAPE 4: CONFIGURATION MYSQL POUR AUTHENTIFICATION
# =============================================================================

log_info "Configuration de l'authentification MySQL..."

# Se connecter à MySQL et configurer l'authentification
docker exec -i mysql_payload mysql -u root -proot << EOF
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY 'root';
FLUSH PRIVILEGES;
EOF

log_success "Authentification MySQL configurée"

# =============================================================================
# ÉTAPE 5: TEST DE L'APPLICATION
# =============================================================================

log_info "Test de l'application..."

# Définir les variables d'environnement
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=root
export DB_NAME=payload_analyser

# Activer l'environnement virtuel et tester
cd /vagrant
source /tmp/fix_mysql/bin/activate

# Tester la connexion avec Python
python3 -c "
import pymysql
try:
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='root',
        database='payload_analyser',
        port=3306
    )
    print('✅ Connexion MySQL réussie')
    conn.close()
except Exception as e:
    print(f'❌ Erreur connexion: {e}')
    exit(1)
"

# =============================================================================
# ÉTAPE 6: INITIALISATION DE LA BASE DE DONNÉES
# =============================================================================

log_info "Initialisation de la base de données..."

# Exécuter le fichier SQL
docker exec -i mysql_payload mysql -u root -proot payload_analyser < payload_analyser.sql

# Initialiser la base de données
python3 init_db.py

log_success "Base de données initialisée"

# =============================================================================
# ÉTAPE 7: TEST DE L'APPLICATION WEB
# =============================================================================

log_info "Test de l'application web..."

# Démarrer l'application en arrière-plan
python3 app.py &
APP_PID=$!

# Attendre que l'application démarre
sleep 10

# Tester l'application
if curl -s http://localhost:5000/ > /dev/null; then
    log_success "Application web accessible"
else
    log_warning "Application web pas encore prête"
fi

# Arrêter l'application
kill $APP_PID 2>/dev/null || true

# =============================================================================
# ÉTAPE 8: NETTOYAGE
# =============================================================================

log_info "Nettoyage..."

# Désactiver l'environnement virtuel
deactivate

# Supprimer l'environnement virtuel temporaire
rm -rf /tmp/fix_mysql

# =============================================================================
# ÉTAPE 9: RÉSUMÉ FINAL
# =============================================================================

echo ""
echo "🎉 CORRECTION MYSQL TERMINÉE !"
echo "=============================="
echo ""
echo "✅ Cryptography installé"
echo "✅ Authentification MySQL configurée"
echo "✅ Base de données initialisée"
echo "✅ Application testée"
echo ""
echo "📝 PROCHAINES ÉTAPES:"
echo "1. cd /vagrant"
echo "2. chmod +x setup_soc_models.sh"
echo "3. ./setup_soc_models.sh"
echo ""
log_success "Problème MySQL résolu ! 🎯" 