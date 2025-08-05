#!/bin/bash

# =============================================================================
# CONFIGURATION ACCÈS RÉSEAU LAN - payload-analyser.ai
# =============================================================================
# Configure l'application pour être accessible sur le réseau LAN
# Usage: ./setup_network_access.sh
# =============================================================================

set -e

echo "🌐 CONFIGURATION ACCÈS RÉSEAU LAN"
echo "================================="

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
# ÉTAPE 1: DÉTECTION DE L'IP LAN
# =============================================================================

log_info "Détection de l'adresse IP LAN..."

# Détecter l'IP LAN (Windows)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    LAN_IP=$(ipconfig | grep -A 5 "Ethernet adapter" | grep "IPv4" | head -1 | awk '{print $NF}')
    if [ -z "$LAN_IP" ]; then
        LAN_IP=$(ipconfig | grep -A 5 "Wi-Fi" | grep "IPv4" | head -1 | awk '{print $NF}')
    fi
else
    # Linux/Mac
    LAN_IP=$(hostname -I | awk '{print $1}')
fi

if [ -z "$LAN_IP" ]; then
    log_error "Impossible de détecter l'IP LAN"
    exit 1
fi

log_success "IP LAN détectée: $LAN_IP"

# =============================================================================
# ÉTAPE 2: CONFIGURATION HOSTS
# =============================================================================

log_info "Configuration du fichier hosts..."

HOSTS_ENTRY="$LAN_IP payload-analyser.ai"

# Vérifier si l'entrée existe déjà
if grep -q "payload-analyser.ai" /etc/hosts; then
    log_warning "L'entrée payload-analyser.ai existe déjà dans /etc/hosts"
    log_info "Mise à jour de l'entrée..."
    # Supprimer l'ancienne entrée
    sudo sed -i '/payload-analyser.ai/d' /etc/hosts
fi

# Ajouter la nouvelle entrée
echo "$HOSTS_ENTRY" | sudo tee -a /etc/hosts > /dev/null
log_success "Entrée ajoutée dans /etc/hosts: $HOSTS_ENTRY"

# =============================================================================
# ÉTAPE 3: MODIFICATION DU VAGRANTFILE
# =============================================================================

log_info "Modification du Vagrantfile pour l'accès réseau..."

# Créer une sauvegarde
cp Vagrantfile Vagrantfile.backup
log_success "Sauvegarde créée: Vagrantfile.backup"

# Modifier le Vagrantfile pour ajouter l'interface réseau bridge
sed -i '/config.vm.network "forwarded_port", guest: 5001, host: 5001, id: "retriever"/a\
  # Interface réseau bridge pour accès LAN\
  config.vm.network "public_network", ip: "'$LAN_IP'", bridge: "auto"\
' Vagrantfile

log_success "Interface réseau bridge ajoutée au Vagrantfile"

# =============================================================================
# ÉTAPE 4: MODIFICATION DOCKER-COMPOSE
# =============================================================================

log_info "Modification du docker-compose.yml..."

# Créer une sauvegarde
cp Docker/docker-compose.yml Docker/docker-compose.yml.backup
log_success "Sauvegarde créée: Docker/docker-compose.yml.backup"

# Modifier les ports pour écouter sur toutes les interfaces
sed -i 's/- "5000:5000"/- "0.0.0.0:5000:5000"/' Docker/docker-compose.yml
sed -i 's/- "80:80"/- "0.0.0.0:80:80"/' Docker/docker-compose.yml

log_success "Ports Docker configurés pour écouter sur toutes les interfaces"

# =============================================================================
# ÉTAPE 5: CONFIGURATION NGINX
# =============================================================================

log_info "Configuration de Nginx pour le nom de domaine..."

# Modifier la configuration Nginx
sed -i 's/server_name _;/server_name payload-analyser.ai localhost;/' Docker/nginx.conf

log_success "Nginx configuré pour le nom de domaine payload-analyser.ai"

# =============================================================================
# ÉTAPE 6: AJOUT DU SERVICE NGINX AU DOCKER-COMPOSE
# =============================================================================

log_info "Ajout du service Nginx au docker-compose.yml..."

# Ajouter le service Nginx
cat >> Docker/docker-compose.yml << 'EOF'

  # Nginx - Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: nginx_proxy
    restart: always
    depends_on:
      - web
    ports:
      - "0.0.0.0:80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:80"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

EOF

log_success "Service Nginx ajouté au docker-compose.yml"

# =============================================================================
# ÉTAPE 7: CONFIGURATION FIREWALL
# =============================================================================

log_info "Configuration du firewall..."

# Windows Firewall
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    log_info "Configuration du Windows Firewall..."
    
    # Règles pour les ports nécessaires
    netsh advfirewall firewall add rule name="Payload Analyser Web" dir=in action=allow protocol=TCP localport=5000
    netsh advfirewall firewall add rule name="Payload Analyser Nginx" dir=in action=allow protocol=TCP localport=80
    netsh advfirewall firewall add rule name="Payload Analyser Ollama" dir=in action=allow protocol=TCP localport=11434
    netsh advfirewall firewall add rule name="Payload Analyser ChromaDB" dir=in action=allow protocol=TCP localport=8000
    netsh advfirewall firewall add rule name="Payload Analyser Retriever" dir=in action=allow protocol=TCP localport=5001
    
    log_success "Règles Windows Firewall ajoutées"
else
    log_info "Configuration du firewall Linux..."
    
    # UFW (Ubuntu/Debian)
    if command -v ufw &> /dev/null; then
        sudo ufw allow 5000/tcp
        sudo ufw allow 80/tcp
        sudo ufw allow 11434/tcp
        sudo ufw allow 8000/tcp
        sudo ufw allow 5001/tcp
        log_success "Règles UFW ajoutées"
    fi
fi

# =============================================================================
# ÉTAPE 8: SCRIPT DE DÉMARRAGE
# =============================================================================

log_info "Création du script de démarrage..."

cat > start_payload_analyser.sh << 'EOF'
#!/bin/bash

echo "🚀 DÉMARRAGE PAYLOAD ANALYSER - LAN ACCESS"
echo "=========================================="

# Vérifier que Vagrant est installé
if ! command -v vagrant &> /dev/null; then
    echo "❌ Vagrant n'est pas installé"
    exit 1
fi

# Démarrer la VM
echo "🔧 Démarrage de la VM Vagrant..."
vagrant up

# Attendre que la VM soit prête
echo "⏳ Attente que la VM soit prête..."
sleep 30

# Vérifier les services
echo "🔍 Vérification des services..."

# Test de l'application web
if curl -s http://payload-analyser.ai/ > /dev/null; then
    echo "✅ Application accessible via payload-analyser.ai"
else
    echo "⚠️ Application pas encore prête"
fi

# Test de l'IP directe
LAN_IP=$(grep "payload-analyser.ai" /etc/hosts | awk '{print $1}')
if curl -s http://$LAN_IP/ > /dev/null; then
    echo "✅ Application accessible via IP directe: $LAN_IP"
else
    echo "⚠️ Application pas accessible via IP directe"
fi

echo ""
echo "🎉 DÉMARRAGE TERMINÉ !"
echo "====================="
echo ""
echo "📱 Accès via nom de domaine:"
echo "   http://payload-analyser.ai"
echo ""
echo "🌐 Accès via IP directe:"
echo "   http://$LAN_IP"
echo ""
echo "🔧 Autres services:"
echo "   • Ollama SOC: http://$LAN_IP:11434"
echo "   • ChromaDB: http://$LAN_IP:8000"
echo "   • Retriever API: http://$LAN_IP:5001"
echo "   • MySQL: $LAN_IP:3307"
echo ""
echo "💡 Pour arrêter: vagrant halt"
echo "💡 Pour redémarrer: vagrant reload"
EOF

chmod +x start_payload_analyser.sh
log_success "Script de démarrage créé: start_payload_analyser.sh"

# =============================================================================
# ÉTAPE 9: INSTRUCTIONS FINALES
# =============================================================================

echo ""
echo "🎉 CONFIGURATION RÉSEAU TERMINÉE !"
echo "=================================="
echo ""
echo "📋 RÉSUMÉ DES MODIFICATIONS:"
echo "  • Fichier hosts mis à jour"
echo "  • Vagrantfile modifié (interface bridge)"
echo "  • Docker-compose mis à jour (ports 0.0.0.0)"
echo "  • Nginx configuré pour payload-analyser.ai"
echo "  • Firewall configuré"
echo "  • Script de démarrage créé"
echo ""
echo "🚀 PROCHAINES ÉTAPES:"
echo "1. Redémarrer la VM: vagrant reload"
echo "2. Ou utiliser le script: ./start_payload_analyser.sh"
echo "3. Tester l'accès: http://payload-analyser.ai"
echo ""
echo "🌐 ACCÈS DISPONIBLES:"
echo "  • Nom de domaine: http://payload-analyser.ai"
echo "  • IP directe: http://$LAN_IP"
echo ""
log_success "Configuration réseau terminée ! 🎯" 