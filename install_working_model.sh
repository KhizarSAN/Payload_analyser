#!/bin/bash

# =============================================================================
# SCRIPT D'INSTALLATION D'UN MODÈLE FONCTIONNEL
# =============================================================================
# Trouve et installe un modèle qui existe réellement dans Ollama
# Usage: ./install_working_model.sh
# =============================================================================

set -e

echo "🔍 INSTALLATION D'UN MODÈLE FONCTIONNEL"
echo "======================================="

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
# ÉTAPE 2: LISTE DES MODÈLES DISPONIBLES
# =============================================================================

log_info "Recherche des modèles disponibles..."

# Modèles à tester (par ordre de préférence)
MODELS_TO_TEST=(
    "mistral:7b"
    "mistral:7b-instruct"
    "llama2:7b"
    "llama2:7b-chat"
    "codellama:7b"
    "codellama:7b-instruct"
    "tinyllama:1.1b-chat"
    "phi:2.7b"
    "phi:2.7b-chat"
)

# =============================================================================
# ÉTAPE 3: TEST ET INSTALLATION
# =============================================================================

WORKING_MODEL=""
for model in "${MODELS_TO_TEST[@]}"; do
    log_info "Test du modèle: $model"
    
    # Vérifier si le modèle est déjà installé
    if curl -s http://localhost:11434/api/tags | grep -q "$model"; then
        log_success "✅ $model est déjà installé"
        WORKING_MODEL="$model"
        break
    fi
    
    # Essayer d'installer le modèle
    log_info "Tentative d'installation de $model..."
    RESPONSE=$(curl -s -X POST http://localhost:11434/api/pull -d "{\"name\": \"$model\"}")
    
    if echo "$RESPONSE" | grep -q "status.*pulling"; then
        log_success "✅ $model en cours d'installation..."
        
        # Attendre que l'installation se termine
        for i in {1..60}; do
            if curl -s http://localhost:11434/api/tags | grep -q "$model"; then
                log_success "✅ $model installé avec succès !"
                WORKING_MODEL="$model"
                break 2
            fi
            log_info "Attente... ($i/60)"
            sleep 30
        done
    elif echo "$RESPONSE" | grep -q "error.*not found"; then
        log_warning "⚠️ $model n'existe pas dans la bibliothèque"
        continue
    else
        log_warning "⚠️ Erreur lors de l'installation de $model"
        continue
    fi
done

# =============================================================================
# ÉTAPE 4: VÉRIFICATION FINALE
# =============================================================================

if [ -n "$WORKING_MODEL" ]; then
    log_success "🎉 Modèle fonctionnel trouvé: $WORKING_MODEL"
    
    # Test du modèle
    log_info "Test du modèle $WORKING_MODEL..."
    TEST_RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
      -H "Content-Type: application/json" \
      -d "{\"model\": \"$WORKING_MODEL\", \"prompt\": \"Bonjour\", \"stream\": false}" \
      --max-time 30)
    
    if echo "$TEST_RESPONSE" | grep -q "response"; then
        log_success "✅ $WORKING_MODEL fonctionne correctement"
        
        # Mettre à jour le fichier de configuration
        log_info "Mise à jour de la configuration..."
        sed -i "s/mixtral:8x7b/$WORKING_MODEL/g" Docker/retriever/app.py
        sed -i "s/nous-hermes2-mistral:7b/$WORKING_MODEL/g" Docker/retriever/app.py
        sed -i "s/openhermes2.5-mistral:7b/$WORKING_MODEL/g" Docker/retriever/app.py
        
        log_success "✅ Configuration mise à jour avec $WORKING_MODEL"
    else
        log_warning "⚠️ $WORKING_MODEL ne répond pas correctement"
    fi
else
    log_error "❌ Aucun modèle fonctionnel trouvé"
    log_info "Essayez d'installer manuellement un modèle:"
    echo "curl -X POST http://localhost:11434/api/pull -d '{\"name\": \"mistral:7b\"}'"
fi

# =============================================================================
# ÉTAPE 5: DÉMARRAGE DES APPLICATIONS
# =============================================================================

if [ -n "$WORKING_MODEL" ]; then
    log_info "Démarrage des applications..."
    
    cd Docker
    
    # Vérifier la syntaxe Docker Compose disponible
    if command -v docker compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        DOCKER_COMPOSE_CMD="docker-compose"
    fi
    
    $DOCKER_COMPOSE_CMD up -d web retriever
    
    log_info "Attente du démarrage..."
    sleep 30
    
    # Vérifications
    if curl -s http://localhost:5000/ >/dev/null 2>&1; then
        log_success "✅ Application web accessible"
    else
        log_warning "⚠️ Application web pas encore prête"
    fi
    
    if curl -s http://localhost:5001/health >/dev/null 2>&1; then
        log_success "✅ API Retriever accessible"
    else
        log_warning "⚠️ API Retriever pas encore prête"
    fi
fi

echo ""
echo "🎯 RÉSUMÉ:"
echo "=========="
if [ -n "$WORKING_MODEL" ]; then
    echo "✅ Modèle installé: $WORKING_MODEL"
    echo "🌐 Application Web: http://localhost:5000"
    echo "🤖 API Retriever: http://localhost:5001"
    echo "🧠 Ollama: http://localhost:11434"
else
    echo "❌ Aucun modèle installé"
    echo "💡 Essayez: curl -X POST http://localhost:11434/api/pull -d '{\"name\": \"mistral:7b\"}'"
fi

log_success "Installation terminée ! 🎯" 