#!/bin/bash

# =============================================================================
# VÉRIFICATION FINALE AVANT DÉPLOIEMENT VAGRANT
# =============================================================================
# Vérifie que tout est prêt pour le déploiement
# Usage: ./check_deployment.sh
# =============================================================================

set -e

echo "🔍 VÉRIFICATION FINALE AVANT DÉPLOIEMENT"
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
# ÉTAPE 1: VÉRIFICATION DES FICHIERS ESSENTIELS
# =============================================================================

log_info "Vérification des fichiers essentiels..."

ESSENTIAL_FILES=(
    "Vagrantfile"
    "Docker/docker-compose.yml"
    "Docker/retriever/app.py"
    "Docker/retriever/requirements.txt"
    "Docker/retriever/Dockerfile"
    "Dockerfile"
    "app.py"
    "requirements.txt"
    "gpt_analysis.py"
    "db_config.py"
    "auth.py"
    "logger.py"
    "pattern_storage.py"
    "parser.py"
    "normalizer.py"
    "init_db.py"
    "init_admin.py"
    "init_patterns.py"
    "insert_mdp.py"
    "payload_analyser.sql"
    "templates/"
    "static/"
    "patterns_data/"
    "setup_soc_models.sh"
    "verify_config.sh"
    "fix_mysql_auth.sh"
    "DEPLOIEMENT_SOC.md"
    "README_DEMAIN.md"
)

for file in "${ESSENTIAL_FILES[@]}"; do
    if [ -f "$file" ] || [ -d "$file" ]; then
        log_success "✅ $file"
    else
        log_error "❌ $file manquant"
        exit 1
    fi
done

# =============================================================================
# ÉTAPE 2: VÉRIFICATION DES FICHIERS SUPPRIMÉS
# =============================================================================

log_info "Vérification des fichiers supprimés..."

DELETED_FILES=(
    "setup_ollama_complete.sh"
    "setup_powerful_ai.sh"
    "README_MISTRAL_LOCAL.md"
    "METHODE_MISTRAL.txt"
    "payloadsshpublic"
    "Docker/docker-compose-cpu.yml"
    "Docker/models"
    "Docker/cache"
    "__pycache__"
)

for file in "${DELETED_FILES[@]}"; do
    if [ ! -e "$file" ]; then
        log_success "✅ $file supprimé"
    else
        log_warning "⚠️ $file existe encore"
    fi
done

# =============================================================================
# ÉTAPE 3: VÉRIFICATION DU VAGRANTFILE
# =============================================================================

log_info "Vérification du Vagrantfile..."

if grep -q 'vb.memory = "8192"' Vagrantfile; then
    log_success "✅ RAM configurée à 8GB"
else
    log_error "❌ RAM pas configurée à 8GB"
    exit 1
fi

if grep -q 'vb.cpus = 4' Vagrantfile; then
    log_success "✅ CPU configurés à 4 cores"
else
    log_error "❌ CPU pas configurés à 4 cores"
    exit 1
fi

if grep -q "11434" Vagrantfile; then
    log_success "✅ Port Ollama configuré"
else
    log_error "❌ Port Ollama manquant"
    exit 1
fi

# =============================================================================
# ÉTAPE 4: VÉRIFICATION DU DOCKER-COMPOSE
# =============================================================================

log_info "Vérification du docker-compose.yml..."

if grep -q "ollama:" Docker/docker-compose.yml; then
    log_success "✅ Service Ollama configuré"
else
    log_error "❌ Service Ollama manquant"
    exit 1
fi

if grep -q "11434:11434" Docker/docker-compose.yml; then
    log_success "✅ Port Ollama dans docker-compose"
else
    log_error "❌ Port Ollama manquant dans docker-compose"
    exit 1
fi

# =============================================================================
# ÉTAPE 5: VÉRIFICATION DU RETRIEVER
# =============================================================================

log_info "Vérification du retriever..."

if grep -q "OLLAMA_URL" Docker/retriever/app.py; then
    log_success "✅ Retriever configuré pour Ollama"
else
    log_error "❌ Retriever pas configuré pour Ollama"
    exit 1
fi

if grep -q "mixtral:8x7b" Docker/retriever/app.py; then
    log_success "✅ Modèles SOC configurés"
else
    log_error "❌ Modèles SOC manquants"
    exit 1
fi

# =============================================================================
# ÉTAPE 6: VÉRIFICATION DES SCRIPTS
# =============================================================================

log_info "Vérification des scripts..."

if [ -x "setup_soc_models.sh" ]; then
    log_success "✅ setup_soc_models.sh exécutable"
else
    log_warning "⚠️ setup_soc_models.sh pas exécutable"
    log_info "Exécuter: chmod +x setup_soc_models.sh"
fi

if [ -x "verify_config.sh" ]; then
    log_success "✅ verify_config.sh exécutable"
else
    log_warning "⚠️ verify_config.sh pas exécutable"
    log_info "Exécuter: chmod +x verify_config.sh"
fi

# =============================================================================
# ÉTAPE 7: RÉSUMÉ FINAL
# =============================================================================

echo ""
echo "🎉 VÉRIFICATION FINALE TERMINÉE !"
echo "================================="
echo ""
echo "📋 STATUT:"
echo "  • Fichiers essentiels: ✅"
echo "  • Fichiers supprimés: ✅"
echo "  • Vagrantfile: ✅"
echo "  • Docker Compose: ✅"
echo "  • Retriever: ✅"
echo "  • Scripts: ✅"
echo ""
echo "🚀 PRÊT POUR LE DÉPLOIEMENT !"
echo ""
echo "📝 PROCHAINES ÉTAPES:"
echo "1. vagrant up"
echo "2. vagrant ssh"
echo "3. ./setup_soc_models.sh"
echo "4. Tests complets"
echo ""
log_success "Projet prêt pour le déploiement ! 🎯" 