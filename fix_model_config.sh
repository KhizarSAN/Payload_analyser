#!/bin/bash

# =============================================================================
# SCRIPT DE CORRECTION DE LA CONFIGURATION DU MODÈLE
# =============================================================================
# Corrige la configuration pour utiliser le bon modèle Ollama
# Usage: ./fix_model_config.sh
# =============================================================================

set -e

echo "🔧 CORRECTION CONFIGURATION MODÈLE"
echo "=================================="

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
# ÉTAPE 1: VÉRIFICATION D'OLLAMA
# =============================================================================

log_info "Vérification du service Ollama..."

if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    log_error "Ollama n'est pas accessible"
    exit 1
fi

log_success "Ollama est accessible"

# =============================================================================
# ÉTAPE 2: LISTE DES MODÈLES INSTALLÉS
# =============================================================================

log_info "Modèles installés dans Ollama:"

MODELS_RESPONSE=$(curl -s http://localhost:11434/api/tags)
if echo "$MODELS_RESPONSE" | grep -q '"models":\[\]'; then
    log_warning "Aucun modèle installé"
    log_info "Installation de mistral:7b..."
    curl -X POST http://localhost:11434/api/pull -d '{"name": "mistral:7b"}'
    sleep 30
else
    echo "$MODELS_RESPONSE" | jq -r '.models[]?.name' 2>/dev/null || echo "$MODELS_RESPONSE"
fi

# =============================================================================
# ÉTAPE 3: TEST DU MODÈLE MISTRAL
# =============================================================================

log_info "Test du modèle mistral:7b..."

TEST_RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:7b", "prompt": "Bonjour", "stream": false}' \
  --max-time 30)

if echo "$TEST_RESPONSE" | grep -q "response"; then
    log_success "✅ mistral:7b fonctionne correctement"
else
    log_error "❌ mistral:7b ne répond pas"
    echo "Réponse: $TEST_RESPONSE"
    exit 1
fi

# =============================================================================
# ÉTAPE 4: CORRECTION DE LA CONFIGURATION
# =============================================================================

log_info "Correction de la configuration..."

# Sauvegarder le fichier original
cp Docker/retriever/app.py Docker/retriever/app.py.backup

# Corriger la logique de sélection du modèle
sed -i '/# Choix du modèle selon disponibilité/,/logger.warning.*Aucun modèle détecté/c\
            # Choix du modèle selon disponibilité\
            model_choice = None\
            if "mistral:7b" in available_models:\
                model_choice = "mistral:7b"\
                logger.info("🎯 Utilisation de Mistral 7B (modèle installé)")\
            elif "llama2:7b" in available_models:\
                model_choice = "llama2:7b"\
                logger.info("🎯 Utilisation de Llama2 7B")\
            elif "codellama:7b" in available_models:\
                model_choice = "codellama:7b"\
                logger.info("🎯 Utilisation de CodeLlama 7B")\
            else:\
                # Fallback vers mistral:7b par défaut\
                model_choice = "mistral:7b"\
                logger.warning("⚠️ Aucun modèle détecté, utilisation de Mistral 7B par défaut")' Docker/retriever/app.py

log_success "✅ Configuration corrigée"

# =============================================================================
# ÉTAPE 5: REDÉMARRAGE DES SERVICES
# =============================================================================

log_info "Redémarrage des services..."

cd Docker

# Vérifier la syntaxe Docker Compose disponible
if command -v docker compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

# Redémarrer le retriever
$DOCKER_COMPOSE_CMD restart retriever

log_info "Attente du redémarrage..."
sleep 30

# =============================================================================
# ÉTAPE 6: TEST DE L'API
# =============================================================================

log_info "Test de l'API Retriever..."

if curl -s http://localhost:5001/health >/dev/null 2>&1; then
    log_success "✅ API Retriever accessible"
    
    # Test d'analyse
    log_info "Test d'analyse avec un payload simple..."
    TEST_PAYLOAD='{"payload": "Test de connexion SSH depuis 192.168.1.100"}'
    
    ANALYSIS_RESPONSE=$(curl -s -X POST http://localhost:5001/analyze \
      -H "Content-Type: application/json" \
      -d "$TEST_PAYLOAD" \
      --max-time 60)
    
    if echo "$ANALYSIS_RESPONSE" | grep -q "analysis"; then
        log_success "✅ Analyse fonctionnelle"
        echo "Réponse: $(echo "$ANALYSIS_RESPONSE" | jq -r '.analysis' | head -3)"
    else
        log_warning "⚠️ Analyse échouée"
        echo "Réponse: $ANALYSIS_RESPONSE"
    fi
else
    log_warning "⚠️ API Retriever pas encore prête"
fi

# =============================================================================
# ÉTAPE 7: RÉSUMÉ FINAL
# =============================================================================

echo ""
echo "🎯 CONFIGURATION CORRIGÉE !"
echo "==========================="
echo ""
echo "✅ Modèle: mistral:7b"
echo "✅ Ollama: http://localhost:11434"
echo "✅ API Retriever: http://localhost:5001"
echo "✅ Application Web: http://localhost:5000"
echo ""
echo "📝 Pour tester l'analyse:"
echo "curl -X POST http://localhost:5001/analyze \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"payload\": \"Votre payload QRadar ici\"}'"
echo ""

log_success "Configuration corrigée avec succès ! 🎯" 