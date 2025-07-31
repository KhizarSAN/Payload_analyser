#!/bin/bash

# =============================================================================
# SCRIPT POUR IA PLUS PUISSANTE (DEMAIN AVEC PLUS DE RAM)
# =============================================================================
# Ce script configure une IA plus puissante quand vous aurez plus de RAM
# Usage: ./setup_powerful_ai.sh
# =============================================================================

set -e

echo "🚀 CONFIGURATION IA PUISSANTE POUR DEMAIN"
echo "========================================="

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
# ÉTAPE 1: VÉRIFICATION DE LA RAM
# =============================================================================

log_info "Vérification de la RAM disponible..."

TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
log_info "RAM totale: ${TOTAL_RAM}GB"

if [ "$TOTAL_RAM" -lt 8 ]; then
    log_warning "RAM insuffisante pour une IA puissante"
    log_info "Recommandé: 8GB minimum pour Mistral 7B"
    log_info "Utilisation de TinyLlama par défaut"
    MODEL_CHOICE="tinyllama:1.1b-chat"
else
    log_success "RAM suffisante pour une IA puissante"
    echo ""
    echo "🤖 CHOIX DU MODÈLE IA:"
    echo "1. Mistral 7B Instruct (recommandé - 4GB RAM)"
    echo "2. Llama2 7B Chat (4GB RAM)"
    echo "3. Phi-3 Mini (2GB RAM)"
    echo "4. TinyLlama (1GB RAM)"
    echo ""
    read -p "Choisissez le modèle (1-4): " choice
    
    case $choice in
        1) MODEL_CHOICE="mistral:7b-instruct-q4_K_M" ;;
        2) MODEL_CHOICE="llama2:7b-chat-q4_K_M" ;;
        3) MODEL_CHOICE="phi3:mini" ;;
        4) MODEL_CHOICE="tinyllama:1.1b-chat" ;;
        *) MODEL_CHOICE="mistral:7b-instruct-q4_K_M" ;;
    esac
fi

log_info "Modèle choisi: $MODEL_CHOICE"

# =============================================================================
# ÉTAPE 2: INSTALLATION DU MODÈLE
# =============================================================================

log_info "Installation du modèle $MODEL_CHOICE..."

# Supprimer les anciens modèles
curl -X DELETE http://localhost:11434/api/delete -d '{"name": "tinyllama:1.1b-chat"}' 2>/dev/null || true
curl -X DELETE http://localhost:11434/api/delete -d '{"name": "mistral:7b-instruct-q4_K_M"}' 2>/dev/null || true
curl -X DELETE http://localhost:11434/api/delete -d '{"name": "llama2:7b-chat-q4_K_M"}' 2>/dev/null || true
curl -X DELETE http://localhost:11434/api/delete -d '{"name": "phi3:mini"}' 2>/dev/null || true

# Installer le nouveau modèle
log_info "Téléchargement de $MODEL_CHOICE (peut prendre 10-30 minutes)..."
curl -X POST http://localhost:11434/api/pull -d "{\"name\": \"$MODEL_CHOICE\"}"

# Vérifier l'installation
sleep 10
if curl -s http://localhost:11434/api/tags | grep -q "$(echo $MODEL_CHOICE | cut -d: -f1)"; then
    log_success "Modèle $MODEL_CHOICE installé avec succès"
else
    log_error "Échec de l'installation du modèle"
    exit 1
fi

# =============================================================================
# ÉTAPE 3: MISE À JOUR DU CODE
# =============================================================================

log_info "Mise à jour du code pour utiliser $MODEL_CHOICE..."

# Extraire le nom du modèle sans version
MODEL_NAME=$(echo $MODEL_CHOICE | cut -d: -f1)

# Mettre à jour le fichier retriever/app.py
sed -i "s/\"model\": \"tinyllama:1.1b-chat\"/\"model\": \"$MODEL_CHOICE\"/g" retriever/app.py
sed -i "s/TinyLlama/$MODEL_NAME/g" retriever/app.py

log_success "Code mis à jour"

# =============================================================================
# ÉTAPE 4: REDÉMARRAGE DES SERVICES
# =============================================================================

log_info "Redémarrage des services..."

# Reconstruire et redémarrer le retriever
docker-compose -f docker-compose-ollama.yml build retriever
docker-compose -f docker-compose-ollama.yml up -d retriever

log_info "Attente du redémarrage..."
sleep 30

# =============================================================================
# ÉTAPE 5: TESTS
# =============================================================================

log_info "Tests du nouveau modèle..."

# Test direct d'Ollama
TEST_RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d "{\"model\": \"$MODEL_CHOICE\", \"prompt\": \"Bonjour, comment allez-vous?\", \"stream\": false}")

if echo "$TEST_RESPONSE" | grep -q "response"; then
    log_success "Modèle $MODEL_CHOICE fonctionne"
else
    log_error "Modèle $MODEL_CHOICE ne répond pas"
    exit 1
fi

# Test du retriever
if curl -s http://localhost:5001/health | grep -q "healthy"; then
    log_success "Retriever fonctionne avec le nouveau modèle"
else
    log_error "Retriever ne fonctionne pas"
    exit 1
fi

# Test d'analyse
ANALYSIS_RESPONSE=$(curl -s -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"payload":"Test payload QRadar - Suspicious activity detected from IP 192.168.1.100"}')

if echo "$ANALYSIS_RESPONSE" | grep -q "analysis"; then
    log_success "Analyse fonctionne avec $MODEL_CHOICE"
    echo "Résultat de l'analyse:"
    echo "$ANALYSIS_RESPONSE" | jq '.analysis' 2>/dev/null || echo "$ANALYSIS_RESPONSE"
else
    log_error "Échec de l'analyse"
fi

# =============================================================================
# ÉTAPE 6: AFFICHAGE FINAL
# =============================================================================

echo ""
echo "🎉 IA PUISSANTE CONFIGURÉE AVEC SUCCÈS !"
echo "========================================="
echo ""
echo "🧠 NOUVEAU MODÈLE: $MODEL_CHOICE"
echo "📊 RAM UTILISÉE: ~$(echo $MODEL_CHOICE | grep -o '[0-9]\+' | head -1)GB"
echo ""
echo "🔗 ACCÈS:"
echo "  • Interface Web: http://localhost:5000"
echo "  • API Retriever: http://localhost:5001"
echo "  • Health Check: http://localhost:5001/health"
echo ""
echo "📝 COMMANDES:"
echo "  • Logs: docker logs mistral_retriever"
echo "  • Stats: curl http://localhost:5001/stats"
echo "  • Test: curl -X POST http://localhost:5001/analyze -H 'Content-Type: application/json' -d '{\"payload\":\"test\"}'"
echo ""
echo "✅ Votre IA puissante est prête ! 🚀"
echo ""

log_success "Configuration terminée !" 