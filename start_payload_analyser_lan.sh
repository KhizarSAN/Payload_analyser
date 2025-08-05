#!/bin/bash

# =============================================================================
# DÉMARRAGE PAYLOAD ANALYSER - CONFIGURATION RÉSEAU LAN AUTOMATIQUE
# =============================================================================
# Démarre l'application avec configuration réseau LAN automatique
# Usage: ./start_payload_analyser_lan.sh
# =============================================================================

set -e

echo "🚀 DÉMARRAGE PAYLOAD ANALYSER - LAN ACCESS"
echo "=========================================="

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
# ÉTAPE 1: VÉRIFICATION PRÉALABLE
# =============================================================================

log_info "Vérification des prérequis..."

# Vérifier que Vagrant est installé
if ! command -v vagrant &> /dev/null; then
    log_error "❌ Vagrant n'est pas installé"
    echo "💡 Installez Vagrant depuis: https://www.vagrantup.com/downloads"
    exit 1
fi

log_success "✅ Vagrant installé"

# Vérifier que VirtualBox est installé
if ! command -v VBoxManage &> /dev/null; then
    log_warning "⚠️ VirtualBox n'est pas installé ou pas dans le PATH"
    echo "💡 Installez VirtualBox depuis: https://www.virtualbox.org/wiki/Downloads"
fi

# =============================================================================
# ÉTAPE 2: DÉMARRAGE DE LA VM
# =============================================================================

log_info "Démarrage de la VM Vagrant..."

# Vérifier le statut de la VM
VM_STATUS=$(vagrant status --machine-readable | grep ",state," | cut -d',' -f4)

if [ "$VM_STATUS" = "running" ]; then
    log_info "VM déjà en cours d'exécution"
elif [ "$VM_STATUS" = "poweroff" ]; then
    log_info "Démarrage de la VM..."
    vagrant up
else
    log_info "Création et démarrage de la VM..."
    vagrant up
fi

# =============================================================================
# ÉTAPE 3: ATTENTE ET VÉRIFICATION
# =============================================================================

log_info "⏳ Attente que la VM soit prête..."
sleep 30

# Vérifier que la VM est bien démarrée
if ! vagrant status | grep -q "running"; then
    log_error "❌ La VM n'est pas démarrée"
    exit 1
fi

log_success "✅ VM démarrée avec succès"

# =============================================================================
# ÉTAPE 4: RÉCUPÉRATION DE L'IP LAN
# =============================================================================

log_info "Récupération de l'IP LAN..."

# Récupérer l'IP LAN de la VM
VM_LAN_IP=$(vagrant ssh -c "hostname -I | awk '{print \$1}'" --no-tty 2>/dev/null | tr -d '\r')

if [ -z "$VM_LAN_IP" ]; then
    log_warning "⚠️ Impossible de récupérer l'IP LAN de la VM"
    log_info "Tentative de récupération via VirtualBox..."
    VM_LAN_IP=$(VBoxManage guestproperty get qradar-debian "/VirtualBox/GuestInfo/Net/1/V4/IP" 2>/dev/null | cut -d' ' -f2)
fi

if [ -z "$VM_LAN_IP" ]; then
    log_warning "⚠️ IP LAN non détectée automatiquement"
    log_info "Vous devrez configurer manuellement le DNS sur les machines clientes"
else
    log_success "📍 IP LAN de la VM: $VM_LAN_IP"
fi

# =============================================================================
# ÉTAPE 5: VÉRIFICATION DES SERVICES
# =============================================================================

log_info "Vérification des services..."

# Attendre un peu plus pour que les services soient prêts
sleep 20

# Test des services principaux
SERVICES=(
    "5000:Application Web Flask"
    "80:Interface Nginx"
    "11434:Ollama SOC"
    "8000:ChromaDB"
    "5001:Retriever API"
)

for service in "${SERVICES[@]}"; do
    port=$(echo $service | cut -d: -f1)
    name=$(echo $service | cut -d: -f2)
    
    if curl -s --connect-timeout 10 "http://localhost:$port/" > /dev/null 2>&1; then
        log_success "✅ $name accessible"
    else
        log_warning "⚠️ $name pas encore prêt"
    fi
done

# =============================================================================
# ÉTAPE 6: CONFIGURATION DNS LOCAL (OPTIONNELLE)
# =============================================================================

if [ ! -z "$VM_LAN_IP" ]; then
    log_info "Configuration DNS local..."
    
    # Vérifier si l'entrée existe déjà
    if grep -q "payload-analyser.ai" /etc/hosts; then
        log_info "Mise à jour de l'entrée DNS existante..."
        sudo sed -i '/payload-analyser.ai/d' /etc/hosts
    fi
    
    # Ajouter l'entrée DNS
    echo "$VM_LAN_IP payload-analyser.ai" | sudo tee -a /etc/hosts > /dev/null
    log_success "✅ DNS local configuré"
fi

# =============================================================================
# ÉTAPE 7: AFFICHAGE DES INFORMATIONS
# =============================================================================

echo ""
echo "🎉 DÉMARRAGE TERMINÉ !"
echo "====================="
echo ""
echo "📱 ACCÈS LOCAUX:"
echo "   • Application Web: http://localhost:5000"
echo "   • Interface Nginx: http://localhost:8081"
echo "   • Ollama SOC: http://localhost:11434"
echo "   • ChromaDB: http://localhost:8000"
echo "   • Retriever API: http://localhost:5001"
echo ""

if [ ! -z "$VM_LAN_IP" ]; then
    echo "🌐 ACCÈS RÉSEAU LAN:"
    echo "   • IP du serveur: $VM_LAN_IP"
    echo "   • Application Web: http://$VM_LAN_IP"
    echo "   • Nom de domaine: http://payload-analyser.ai"
    echo "   • Ollama SOC: http://$VM_LAN_IP:11434"
    echo "   • ChromaDB: http://$VM_LAN_IP:8000"
    echo "   • Retriever API: http://$VM_LAN_IP:5001"
    echo ""
    echo "📋 POUR LES MACHINES CLIENTES:"
    echo "   1. Copiez le fichier 'setup_client_dns.sh' depuis la VM"
    echo "   2. Exécutez: ./setup_client_dns.sh"
    echo "   3. Accédez à: http://payload-analyser.ai"
    echo ""
fi

echo "🔧 COMMANDES UTILES:"
echo "   • Arrêter: vagrant halt"
echo "   • Redémarrer: vagrant reload"
echo "   • Accès SSH: vagrant ssh"
echo "   • Statut: vagrant status"
echo ""

if [ ! -z "$VM_LAN_IP" ]; then
    log_success "🎯 Application accessible sur le réseau LAN via payload-analyser.ai"
else
    log_warning "⚠️ Configuration réseau à vérifier manuellement"
fi 