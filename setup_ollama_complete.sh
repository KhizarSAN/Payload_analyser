#!/bin/bash

# =============================================================================
# SCRIPT D'AUTOMATISATION COMPLÈTE - ENVIRONNEMENT OLLAMA QRADAR
# =============================================================================
# Ce script configure automatiquement l'environnement complet pour demain
# Usage: ./setup_ollama_complete.sh
# =============================================================================

set -e  # Arrêter en cas d'erreur

echo "🚀 DÉMARRAGE DE L'AUTOMATISATION COMPLÈTE OLLAMA QRADAR"
echo "=================================================="

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
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
# ÉTAPE 1: VÉRIFICATIONS PRÉALABLES
# =============================================================================

log_info "Vérification de l'environnement..."

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker n'est pas installé"
    exit 1
fi

# Vérifier Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose n'est pas installé"
    exit 1
fi

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "docker-compose-ollama.yml" ]; then
    log_error "Fichier docker-compose-ollama.yml non trouvé"
    log_info "Assurez-vous d'être dans le répertoire Docker/"
    exit 1
fi

log_success "Environnement vérifié"

# =============================================================================
# ÉTAPE 2: NETTOYAGE COMPLET
# =============================================================================

log_info "Nettoyage complet de l'environnement..."

# Arrêter et supprimer tous les containers
docker-compose -f docker-compose-ollama.yml down --volumes --remove-orphans 2>/dev/null || true

# Supprimer les images pour forcer le rebuild
docker rmi docker-web docker-retriever 2>/dev/null || true

# Nettoyer les volumes non utilisés
docker volume prune -f

# Nettoyer les réseaux non utilisés
docker network prune -f

log_success "Nettoyage terminé"

# =============================================================================
# ÉTAPE 3: CONFIGURATION DES FICHIERS
# =============================================================================

log_info "Configuration des fichiers..."

# Vérifier que le fichier retriever/app.py existe
if [ ! -f "retriever/app.py" ]; then
    log_error "Fichier retriever/app.py non trouvé"
    exit 1
fi

# Vérifier que le fichier requirements.txt existe
if [ ! -f "requirements.txt" ]; then
    log_error "Fichier requirements.txt non trouvé"
    exit 1
fi

log_success "Fichiers vérifiés"

# =============================================================================
# ÉTAPE 4: DÉMARRAGE DES SERVICES
# =============================================================================

log_info "Démarrage des services..."

# Démarrer les services de base (MySQL, ChromaDB, Ollama)
docker-compose -f docker-compose-ollama.yml up -d db chromadb ollama

log_info "Attente du démarrage des services de base..."
sleep 30

# Vérifier que MySQL est healthy
log_info "Vérification de MySQL..."
for i in {1..30}; do
    if docker-compose -f docker-compose-ollama.yml ps db | grep -q "healthy"; then
        log_success "MySQL est prêt"
        break
    fi
    log_info "Attente MySQL... ($i/30)"
    sleep 10
done

# =============================================================================
# ÉTAPE 5: INSTALLATION DU MODÈLE TINYLLAMA
# =============================================================================

log_info "Installation du modèle TinyLlama..."

# Supprimer les anciens modèles s'ils existent
curl -X DELETE http://localhost:11434/api/delete -d '{"name": "mistral"}' 2>/dev/null || true
curl -X DELETE http://localhost:11434/api/delete -d '{"name": "phi3:mini"}' 2>/dev/null || true

# Installer TinyLlama
log_info "Téléchargement de TinyLlama (peut prendre plusieurs minutes)..."
curl -X POST http://localhost:11434/api/pull -d '{"name": "tinyllama:1.1b-chat"}'

# Vérifier que le modèle est installé
log_info "Vérification de l'installation..."
sleep 10
if curl -s http://localhost:11434/api/tags | grep -q "tinyllama"; then
    log_success "TinyLlama installé avec succès"
else
    log_error "Échec de l'installation de TinyLlama"
    exit 1
fi

# =============================================================================
# ÉTAPE 6: TEST DU MODÈLE
# =============================================================================

log_info "Test du modèle TinyLlama..."

# Test simple
TEST_RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "tinyllama:1.1b-chat", "prompt": "Bonjour, comment allez-vous?", "stream": false}')

if echo "$TEST_RESPONSE" | grep -q "response"; then
    log_success "TinyLlama fonctionne correctement"
else
    log_error "TinyLlama ne répond pas correctement"
    echo "Réponse: $TEST_RESPONSE"
    exit 1
fi

# =============================================================================
# ÉTAPE 7: CONSTRUCTION ET DÉMARRAGE DES APPLICATIONS
# =============================================================================

log_info "Construction des applications..."

# Construire les images
docker-compose -f docker-compose-ollama.yml build web retriever

log_success "Construction terminée"

# Démarrer les applications
log_info "Démarrage des applications..."
docker-compose -f docker-compose-ollama.yml up -d web retriever

# Attendre que les services démarrent
log_info "Attente du démarrage des applications..."
sleep 30

# =============================================================================
# ÉTAPE 8: VÉRIFICATIONS FINALES
# =============================================================================

log_info "Vérifications finales..."

# Vérifier que tous les services sont en cours d'exécution
SERVICES=("mysql_payload" "chromadb" "ollama_mistral" "qradar_ticket" "mistral_retriever")
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

# Test de l'interface web
log_info "Test de l'interface web..."
if curl -s http://localhost:5000 | grep -q "html"; then
    log_success "Interface web accessible"
else
    log_warning "Interface web non accessible (peut être normal au démarrage)"
fi

# =============================================================================
# ÉTAPE 9: TEST D'ANALYSE COMPLÈTE
# =============================================================================

log_info "Test d'analyse complète..."

# Test avec un payload simple
TEST_PAYLOAD='{"payload":"Test payload QRadar - Suspicious activity detected from IP 192.168.1.100"}'
ANALYSIS_RESPONSE=$(curl -s -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD")

if echo "$ANALYSIS_RESPONSE" | grep -q "analysis"; then
    log_success "Analyse fonctionne correctement"
    echo "Résultat de l'analyse:"
    echo "$ANALYSIS_RESPONSE" | jq '.analysis' 2>/dev/null || echo "$ANALYSIS_RESPONSE"
else
    log_error "Échec de l'analyse"
    echo "Réponse: $ANALYSIS_RESPONSE"
fi

# =============================================================================
# ÉTAPE 10: AFFICHAGE DES INFORMATIONS FINALES
# =============================================================================

echo ""
echo "🎉 AUTOMATISATION TERMINÉE AVEC SUCCÈS !"
echo "=========================================="
echo ""
echo "📊 SERVICES DÉMARRÉS:"
echo "  • MySQL (port 3306)"
echo "  • ChromaDB (port 8000)"
echo "  • Ollama + TinyLlama (port 11434)"
echo "  • Interface Web (port 5000)"
echo "  • API Retriever (port 5001)"
echo ""
echo "🔗 ACCÈS:"
echo "  • Interface Web: http://localhost:5000"
echo "  • API Retriever: http://localhost:5001"
echo "  • Health Check: http://localhost:5001/health"
echo "  • Statistiques: http://localhost:5001/stats"
echo ""
echo "🧠 IA LOCALE:"
echo "  • Modèle: TinyLlama 1.1B Chat"
echo "  • Langue: Français (forcé)"
echo "  • Fonctionnalités: RAG + Embeddings + Apprentissage"
echo ""
echo "📝 COMMANDES UTILES:"
echo "  • Voir les logs: docker logs mistral_retriever"
echo "  • Redémarrer: docker-compose -f docker-compose-ollama.yml restart"
echo "  • Arrêter: docker-compose -f docker-compose-ollama.yml down"
echo ""
echo "✅ Votre environnement d'IA locale pour QRadar est prêt !"
echo ""

# Afficher les statistiques
log_info "Statistiques du système:"
curl -s http://localhost:5001/stats | jq . 2>/dev/null || curl -s http://localhost:5001/stats

echo ""
log_success "Configuration terminée ! 🚀" 