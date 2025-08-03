#!/bin/bash

# =============================================================================
# SCRIPT D'INSTALLATION MODÈLES SOC OPTIMISÉS
# =============================================================================
# Installation automatique des modèles SOC optimisés pour QRadar
# Usage: ./setup_soc_models.sh
# =============================================================================

set -e

echo "🚀 INSTALLATION MODÈLES SOC OPTIMISÉS"
echo "====================================="

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

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker n'est pas installé"
    exit 1
fi

# Vérifier Docker Compose (nouvelle syntaxe)
if ! command -v docker compose &> /dev/null; then
    # Essayer l'ancienne syntaxe
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose n'est pas installé"
        exit 1
    else
        DOCKER_COMPOSE_CMD="docker-compose"
    fi
else
    DOCKER_COMPOSE_CMD="docker compose"
fi

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "Docker/docker-compose.yml" ]; then
    log_error "Fichier Docker/docker-compose.yml non trouvé"
    log_info "Assurez-vous d'être dans le répertoire racine du projet"
    exit 1
fi

log_success "Environnement vérifié"

# =============================================================================
# ÉTAPE 2: VÉRIFICATION DE LA RAM
# =============================================================================

log_info "Vérification de la RAM disponible..."

TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
log_info "RAM totale: ${TOTAL_RAM}GB"

if [ "$TOTAL_RAM" -lt 4 ]; then
    log_error "RAM insuffisante (minimum 4GB requis)"
    log_info "Recommandé: 8GB pour les modèles SOC optimaux"
    exit 1
elif [ "$TOTAL_RAM" -lt 6 ]; then
    log_warning "RAM limitée (4-6GB)"
    RECOMMENDED_MODEL="openhermes2.5-mistral:7b"
    log_info "Modèle recommandé: OpenHermes2.5-Mistral (4GB RAM)"
elif [ "$TOTAL_RAM" -lt 8 ]; then
    log_info "RAM correcte (6-8GB)"
    RECOMMENDED_MODEL="nous-hermes2-mistral:7b"
    log_info "Modèle recommandé: Nous-Hermes2-Mistral (6GB RAM)"
else
    log_success "RAM excellente (8GB+)"
    RECOMMENDED_MODEL="mixtral:8x7b"
    log_info "Modèle recommandé: Mixtral 8x7B (8GB RAM)"
fi

# =============================================================================
# ÉTAPE 3: DÉMARRAGE DES SERVICES
# =============================================================================

log_info "Démarrage des services Docker..."

cd Docker

# Arrêter les services existants
$DOCKER_COMPOSE_CMD down 2>/dev/null || true

# Démarrer les services de base
$DOCKER_COMPOSE_CMD up -d db chromadb ollama

log_info "Attente du démarrage des services..."
sleep 30

# Vérifier que Ollama est prêt
log_info "Vérification d'Ollama..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        log_success "Ollama est prêt"
        break
    fi
    log_info "Attente Ollama... ($i/30)"
    sleep 10
done

# =============================================================================
# ÉTAPE 4: INSTALLATION DU MODÈLE RECOMMANDÉ
# =============================================================================

log_info "Installation du modèle recommandé: $RECOMMENDED_MODEL"

# Supprimer les anciens modèles pour libérer de l'espace
log_info "Nettoyage des anciens modèles..."
curl -X DELETE http://localhost:11434/api/delete -d '{"name": "tinyllama:1.1b-chat"}' 2>/dev/null || true
curl -X DELETE http://localhost:11434/api/delete -d '{"name": "mistral:7b"}' 2>/dev/null || true

# Installer le modèle recommandé
log_info "Téléchargement de $RECOMMENDED_MODEL (peut prendre 10-30 minutes)..."
curl -X POST http://localhost:11434/api/pull -d "{\"name\": \"$RECOMMENDED_MODEL\"}"

# Vérifier l'installation
sleep 10
if curl -s http://localhost:11434/api/tags | grep -q "$(echo $RECOMMENDED_MODEL | cut -d: -f1)"; then
    log_success "Modèle $RECOMMENDED_MODEL installé avec succès"
else
    log_error "Échec de l'installation du modèle"
    exit 1
fi

# =============================================================================
# ÉTAPE 5: TEST DU MODÈLE
# =============================================================================

log_info "Test du modèle $RECOMMENDED_MODEL..."

# Test simple
TEST_RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d "{\"model\": \"$RECOMMENDED_MODEL\", \"prompt\": \"Bonjour, tu es un expert en cybersécurité. Réponds en français.\", \"stream\": false}")

if echo "$TEST_RESPONSE" | grep -q "response"; then
    log_success "Modèle $RECOMMENDED_MODEL fonctionne correctement"
else
    log_error "Modèle $RECOMMENDED_MODEL ne répond pas correctement"
    echo "Réponse: $TEST_RESPONSE"
    exit 1
fi

# =============================================================================
# ÉTAPE 6: DÉMARRAGE DES APPLICATIONS
# =============================================================================

log_info "Démarrage des applications..."

# Construire et démarrer les applications
$DOCKER_COMPOSE_CMD build web retriever
$DOCKER_COMPOSE_CMD up -d web retriever

log_info "Attente du démarrage des applications..."
sleep 30

# =============================================================================
# ÉTAPE 7: VÉRIFICATIONS FINALES
# =============================================================================

log_info "Vérifications finales..."

# Vérifier que tous les services sont en cours d'exécution
SERVICES=("mysql_payload" "chromadb" "ollama_soc" "qradar_ticket" "mistral_retriever")
for service in "${SERVICES[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$service"; then
        log_success "Service $service en cours d'exécution"
    else
        log_error "Service $service non démarré"
        exit 1
    fi
done

# Test du health check du retriever
log_info "Test du retriever..."
if curl -s http://localhost:5001/health | grep -q "healthy"; then
    log_success "Retriever fonctionne"
else
    log_error "Retriever ne répond pas"
    exit 1
fi

# Test d'analyse complète
log_info "Test d'analyse complète..."

TEST_PAYLOAD='{"payload":"Suspicious activity detected from IP 192.168.1.100 - Multiple failed login attempts"}'
ANALYSIS_RESPONSE=$(curl -s -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD")

if echo "$ANALYSIS_RESPONSE" | grep -q "analysis"; then
    log_success "Analyse SOC fonctionne correctement"
    echo "Résultat de l'analyse:"
    echo "$ANALYSIS_RESPONSE" | jq '.analysis' 2>/dev/null || echo "$ANALYSIS_RESPONSE"
else
    log_error "Échec de l'analyse SOC"
    echo "Réponse: $ANALYSIS_RESPONSE"
fi

# =============================================================================
# ÉTAPE 8: AFFICHAGE DES INFORMATIONS FINALES
# =============================================================================

echo ""
echo "🎉 INSTALLATION SOC TERMINÉE AVEC SUCCÈS !"
echo "==========================================="
echo ""
echo "📊 SERVICES DÉMARRÉS:"
echo "  • MySQL (port 3306)"
echo "  • ChromaDB (port 8000)"
echo "  • Ollama SOC (port 11434)"
echo "  • Interface Web (port 5000)"
echo "  • API Retriever (port 5001)"
echo ""
echo "🧠 MODÈLE IA SOC:"
echo "  • Modèle: $RECOMMENDED_MODEL"
echo "  • Optimisé pour: Cybersécurité et SOC"
echo "  • Langue: Français (forcé)"
echo "  • Fonctionnalités: RAG + Embeddings + Apprentissage"
echo ""
echo "🔗 ACCÈS:"
echo "  • Interface Web: http://localhost:5000"
echo "  • API Retriever: http://localhost:5001"
echo "  • Health Check: http://localhost:5001/health"
echo "  • Statistiques: http://localhost:5001/stats"
echo "  • Ollama: http://localhost:11434"
echo ""
echo "📝 COMMANDES UTILES:"
echo "  • Voir les logs: docker logs mistral_retriever"
echo "  • Redémarrer: docker-compose restart"
echo "  • Arrêter: docker-compose down"
echo "  • Modèles installés: curl http://localhost:11434/api/tags"
echo ""
echo "✅ Votre environnement SOC d'IA locale pour QRadar est prêt !"
echo ""

# Afficher les statistiques
log_info "Statistiques du système:"
curl -s http://localhost:5001/stats | jq . 2>/dev/null || curl -s http://localhost:5001/stats

echo ""
log_success "Configuration SOC terminée ! 🚀" 
