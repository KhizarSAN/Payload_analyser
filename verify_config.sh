#!/bin/bash

# =============================================================================
# SCRIPT DE VÉRIFICATION DES CONFIGURATIONS ET CHEMINS
# =============================================================================
# Vérifie que tous les fichiers et configurations sont corrects
# Usage: ./verify_config.sh
# =============================================================================

set -e

echo "🔍 VÉRIFICATION DES CONFIGURATIONS ET CHEMINS"
echo "============================================="

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
# ÉTAPE 1: VÉRIFICATION DES FICHIERS PRINCIPAUX
# =============================================================================

log_info "Vérification des fichiers principaux..."

# Fichiers requis
REQUIRED_FILES=(
    "Docker/docker-compose.yml"
    "Docker/retriever/app.py"
    "Docker/retriever/requirements.txt"
    "Docker/retriever/Dockerfile"
    "Dockerfile"
    "app.py"
    "requirements.txt"
    "Vagrantfile"
    "setup_soc_models.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_success "✅ $file existe"
    else
        log_error "❌ $file manquant"
        exit 1
    fi
done

# =============================================================================
# ÉTAPE 2: VÉRIFICATION DU DOCKER-COMPOSE.YML
# =============================================================================

log_info "Vérification du docker-compose.yml..."

# Vérifier que Ollama est configuré
if grep -q "ollama:" Docker/docker-compose.yml; then
    log_success "✅ Service Ollama configuré"
else
    log_error "❌ Service Ollama manquant dans docker-compose.yml"
    exit 1
fi

# Vérifier que TGI est commenté
if grep -q "# tgi:" Docker/docker-compose.yml; then
    log_success "✅ Service TGI correctement commenté"
else
    log_warning "⚠️ Service TGI pas commenté (peut causer des conflits)"
fi

# Vérifier les ports
if grep -q "11434:11434" Docker/docker-compose.yml; then
    log_success "✅ Port Ollama (11434) configuré"
else
    log_error "❌ Port Ollama manquant"
    exit 1
fi

# Vérifier les volumes
if grep -q "ollama_data:" Docker/docker-compose.yml; then
    log_success "✅ Volume Ollama configuré"
else
    log_error "❌ Volume Ollama manquant"
    exit 1
fi

# =============================================================================
# ÉTAPE 3: VÉRIFICATION DU RETRIEVER
# =============================================================================

log_info "Vérification du retriever..."

# Vérifier que le retriever utilise Ollama
if grep -q "OLLAMA_URL" Docker/retriever/app.py; then
    log_success "✅ Retriever configuré pour Ollama"
else
    log_error "❌ Retriever pas configuré pour Ollama"
    exit 1
fi

# Vérifier les modèles SOC
if grep -q "mixtral:8x7b-instruct-q4_K_M" Docker/retriever/app.py; then
    log_success "✅ Modèle Mixtral configuré"
else
    log_warning "⚠️ Modèle Mixtral pas trouvé dans le retriever"
fi

if grep -q "nous-hermes-2-mistral:7b-dpo-q4_K_M" Docker/retriever/app.py; then
    log_success "✅ Modèle Nous-Hermes-2 configuré"
else
    log_warning "⚠️ Modèle Nous-Hermes-2 pas trouvé dans le retriever"
fi

if grep -q "openhermes-2.5-mistral:7b-q4_K_M" Docker/retriever/app.py; then
    log_success "✅ Modèle OpenHermes-2.5 configuré"
else
    log_warning "⚠️ Modèle OpenHermes-2.5 pas trouvé dans le retriever"
fi

# =============================================================================
# ÉTAPE 4: VÉRIFICATION DU VAGRANTFILE
# =============================================================================

log_info "Vérification du Vagrantfile..."

# Vérifier la RAM
if grep -q 'vb.memory = "8192"' Vagrantfile; then
    log_success "✅ RAM configurée à 8GB"
else
    log_warning "⚠️ RAM pas configurée à 8GB"
fi

# Vérifier les CPU
if grep -q 'vb.cpus = 4' Vagrantfile; then
    log_success "✅ CPU configurés à 4 cores"
else
    log_warning "⚠️ CPU pas configurés à 4 cores"
fi

# Vérifier le port Ollama
if grep -q "11434" Vagrantfile; then
    log_success "✅ Port Ollama (11434) dans Vagrantfile"
else
    log_error "❌ Port Ollama manquant dans Vagrantfile"
    exit 1
fi

# =============================================================================
# ÉTAPE 5: VÉRIFICATION DES SCRIPTS
# =============================================================================

log_info "Vérification des scripts..."

# Vérifier que setup_soc_models.sh est exécutable
if [ -x "setup_soc_models.sh" ]; then
    log_success "✅ setup_soc_models.sh est exécutable"
else
    log_warning "⚠️ setup_soc_models.sh pas exécutable"
    log_info "Exécuter: chmod +x setup_soc_models.sh"
fi

# Vérifier le contenu du script
if grep -q "mixtral:8x7b-instruct-q4_K_M" setup_soc_models.sh; then
    log_success "✅ Script contient Mixtral"
else
    log_error "❌ Script ne contient pas Mixtral"
    exit 1
fi

# =============================================================================
# ÉTAPE 6: VÉRIFICATION DES CHEMINS RELATIFS
# =============================================================================

log_info "Vérification des chemins relatifs..."

# Vérifier que le retriever peut accéder aux fichiers
if [ -f "Docker/retriever/app.py" ]; then
    log_success "✅ Chemin retriever/app.py valide"
else
    log_error "❌ Chemin retriever/app.py invalide"
    exit 1
fi

# Vérifier que le Dockerfile principal peut accéder aux fichiers
if [ -f "Dockerfile" ]; then
    log_success "✅ Dockerfile principal présent"
else
    log_error "❌ Dockerfile principal manquant"
    exit 1
fi

# =============================================================================
# ÉTAPE 7: VÉRIFICATION DES DÉPENDANCES
# =============================================================================

log_info "Vérification des dépendances..."

# Vérifier requirements.txt du retriever
if grep -q "fastapi" Docker/retriever/requirements.txt; then
    log_success "✅ FastAPI dans requirements.txt"
else
    log_error "❌ FastAPI manquant dans requirements.txt"
    exit 1
fi

if grep -q "requests" Docker/retriever/requirements.txt; then
    log_success "✅ Requests dans requirements.txt"
else
    log_error "❌ Requests manquant dans requirements.txt"
    exit 1
fi

if grep -q "chromadb" Docker/retriever/requirements.txt; then
    log_success "✅ ChromaDB dans requirements.txt"
else
    log_error "❌ ChromaDB manquant dans requirements.txt"
    exit 1
fi

# =============================================================================
# ÉTAPE 8: RÉSUMÉ FINAL
# =============================================================================

echo ""
echo "🎉 VÉRIFICATION TERMINÉE !"
echo "=========================="
echo ""
echo "📋 RÉSUMÉ:"
echo "  • Fichiers principaux: ✅"
echo "  • Docker Compose: ✅"
echo "  • Retriever: ✅"
echo "  • Vagrantfile: ✅"
echo "  • Scripts: ✅"
echo "  • Chemins: ✅"
echo "  • Dépendances: ✅"
echo ""
echo "🚀 PRÊT POUR LE DÉPLOIEMENT !"
echo ""
echo "📝 PROCHAINES ÉTAPES:"
echo "1. vagrant up"
echo "2. vagrant ssh"
echo "3. ./setup_soc_models.sh"
echo ""
log_success "Configuration validée avec succès ! 🎯" 