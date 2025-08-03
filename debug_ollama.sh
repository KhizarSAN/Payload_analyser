#!/bin/bash

# =============================================================================
# SCRIPT DE DEBUG OLLAMA
# =============================================================================
# Debug les problèmes de connexion Ollama
# Usage: ./debug_ollama.sh
# =============================================================================

set -e

echo "🔍 DEBUG OLLAMA"
echo "==============="

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
# ÉTAPE 1: VÉRIFICATION DES CONTENEURS
# =============================================================================

log_info "Vérification des conteneurs Docker..."

cd Docker

# Vérifier l'état des conteneurs
docker compose ps

echo ""
log_info "Logs du conteneur Ollama:"
docker compose logs --tail=20 ollama

echo ""
log_info "Logs du conteneur Retriever:"
docker compose logs --tail=20 retriever

# =============================================================================
# ÉTAPE 2: TEST DE CONNEXION OLLAMA
# =============================================================================

echo ""
log_info "Test de connexion Ollama depuis l'hôte..."

# Test depuis l'hôte
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    log_success "✅ Ollama accessible depuis l'hôte (localhost:11434)"
else
    log_error "❌ Ollama non accessible depuis l'hôte"
fi

# Test depuis le réseau Docker
log_info "Test de connexion Ollama depuis le réseau Docker..."

# Créer un conteneur temporaire pour tester
docker run --rm --network docker_default alpine/curl:latest \
  curl -s http://ollama:11434/api/tags >/dev/null 2>&1

if [ $? -eq 0 ]; then
    log_success "✅ Ollama accessible depuis le réseau Docker (ollama:11434)"
else
    log_error "❌ Ollama non accessible depuis le réseau Docker"
fi

# =============================================================================
# ÉTAPE 3: VÉRIFICATION DES MODÈLES
# =============================================================================

echo ""
log_info "Vérification des modèles installés..."

MODELS_RESPONSE=$(curl -s http://localhost:11434/api/tags)
if echo "$MODELS_RESPONSE" | grep -q '"models":\[\]'; then
    log_warning "⚠️ Aucun modèle installé"
else
    log_success "✅ Modèles installés:"
    echo "$MODELS_RESPONSE" | jq -r '.models[]?.name' 2>/dev/null || echo "$MODELS_RESPONSE"
fi

# =============================================================================
# ÉTAPE 4: TEST DU MODÈLE MISTRAL
# =============================================================================

echo ""
log_info "Test du modèle mistral:7b..."

TEST_RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:7b", "prompt": "Bonjour", "stream": false}' \
  --max-time 30)

if echo "$TEST_RESPONSE" | grep -q "response"; then
    log_success "✅ mistral:7b fonctionne"
    echo "Réponse: $(echo "$TEST_RESPONSE" | jq -r '.response' | head -2)"
else
    log_error "❌ mistral:7b ne répond pas"
    echo "Réponse: $TEST_RESPONSE"
fi

# =============================================================================
# ÉTAPE 5: TEST DE L'API RETRIEVER
# =============================================================================

echo ""
log_info "Test de l'API Retriever..."

if curl -s http://localhost:5001/health >/dev/null 2>&1; then
    log_success "✅ API Retriever accessible"
    
    HEALTH_RESPONSE=$(curl -s http://localhost:5001/health)
    echo "Health: $HEALTH_RESPONSE"
else
    log_error "❌ API Retriever non accessible"
fi

# =============================================================================
# ÉTAPE 6: SUGGESTIONS
# =============================================================================

echo ""
echo "📋 SUGGESTIONS:"
echo "=============="

log_info "Si Ollama ne répond pas:"
echo "1. docker compose restart ollama"
echo "2. Attendre 30 secondes"
echo "3. Vérifier les logs: docker compose logs ollama"

log_info "Si le modèle ne fonctionne pas:"
echo "1. Réinstaller le modèle: curl -X POST http://localhost:11434/api/pull -d '{\"name\": \"mistral:7b\"}'"
echo "2. Vérifier l'espace disque disponible"

log_info "Si l'API Retriever ne fonctionne pas:"
echo "1. docker compose restart retriever"
echo "2. Vérifier les logs: docker compose logs retriever"

log_success "Debug terminé ! 🎯" 