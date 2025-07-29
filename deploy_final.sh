#!/bin/bash

# Script de déploiement final pour TGI Mistral
# Architecture moderne avec RAG et apprentissage

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 DÉPLOIEMENT FINAL TGI MISTRAL${NC}"
echo "====================================="

# 1. Vérification de Docker
echo -e "${YELLOW}🔍 Vérification de Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker non installé${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose non installé${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker et Docker Compose disponibles${NC}"

# 2. Vérification du token Hugging Face
if [ -z "$HF_HUB_TOKEN" ]; then
    echo -e "${YELLOW}⚠️ HF_HUB_TOKEN non défini${NC}"
    echo "Le modèle sera téléchargé automatiquement par TGI"
    echo "Pour un déploiement optimal, définissez HF_HUB_TOKEN"
else
    echo -e "${GREEN}✅ HF_HUB_TOKEN configuré${NC}"
fi

# 3. Nettoyage complet
echo -e "${YELLOW}🧹 Nettoyage complet...${NC}"
cd Docker
docker-compose down -v 2>/dev/null || true
docker system prune -f
docker volume prune -f

# 4. Vérification des fichiers
echo -e "${YELLOW}📁 Vérification des fichiers...${NC}"
required_files=(
    "docker-compose.yml"
    "retriever/Dockerfile"
    "retriever/requirements.txt"
    "retriever/app.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Fichier manquant: $file${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Tous les fichiers requis présents${NC}"

# 5. Création des dossiers
echo -e "${YELLOW}📁 Création des dossiers...${NC}"
mkdir -p models
mkdir -p cache
mkdir -p retriever-data

# 6. Construction des images
echo -e "${YELLOW}🔨 Construction des images Docker...${NC}"
docker-compose build --no-cache

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Erreur lors de la construction${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Images construites avec succès${NC}"

# 7. Démarrage des services
echo -e "${YELLOW}🚀 Démarrage des services...${NC}"
docker-compose up -d

# 8. Attente des services
echo -e "${YELLOW}⏳ Attente des services...${NC}"

# Attendre MySQL
echo "Attente de MySQL..."
for i in {1..30}; do
    if docker-compose exec -T db mysqladmin ping -h localhost --silent 2>/dev/null; then
        echo -e "${GREEN}✅ MySQL prêt${NC}"
        break
    fi
    sleep 2
done

# Attendre ChromaDB
echo "Attente de ChromaDB..."
for i in {1..20}; do
    if curl -s http://localhost:8000/api/v1/heartbeat >/dev/null 2>&1; then
        echo -e "${GREEN}✅ ChromaDB prêt${NC}"
        break
    fi
    sleep 3
done

# Attendre TGI Mistral
echo "Attente de TGI Mistral..."
for i in {1..60}; do
    if curl -s http://localhost:8080/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ TGI Mistral prêt${NC}"
        break
    fi
    sleep 5
done

# Attendre Retriever
echo "Attente du Retriever..."
for i in {1..20}; do
    if curl -s http://localhost:5001/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Retriever prêt${NC}"
        break
    fi
    sleep 3
done

# 9. Initialisation de la base de données
echo -e "${YELLOW}🗄️ Initialisation de la base de données...${NC}"
cd ..
python3 init_db.py
python3 init_admin.py

# 10. Test des services
echo -e "${YELLOW}🧪 Test des services...${NC}"

# Test TGI
echo "Test TGI Mistral..."
if curl -s http://localhost:8080/health >/dev/null; then
    echo -e "${GREEN}✅ TGI Mistral fonctionnel${NC}"
else
    echo -e "${RED}❌ TGI Mistral non accessible${NC}"
fi

# Test ChromaDB
echo "Test ChromaDB..."
if curl -s http://localhost:8000/api/v1/heartbeat >/dev/null; then
    echo -e "${GREEN}✅ ChromaDB fonctionnel${NC}"
else
    echo -e "${RED}❌ ChromaDB non accessible${NC}"
fi

# Test Retriever
echo "Test Retriever..."
if curl -s http://localhost:5001/health >/dev/null; then
    echo -e "${GREEN}✅ Retriever fonctionnel${NC}"
else
    echo -e "${RED}❌ Retriever non accessible${NC}"
fi

# Test d'analyse
echo "Test d'analyse..."
TEST_RESPONSE=$(curl -s -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"payload":"Test payload QRadar"}' 2>/dev/null || echo "{}")

if echo "$TEST_RESPONSE" | grep -q "analysis"; then
    echo -e "${GREEN}✅ Test d'analyse réussi${NC}"
else
    echo -e "${YELLOW}⚠️ Test d'analyse échoué (normal au premier démarrage)${NC}"
fi

# 11. Statut final
echo -e "${BLUE}📊 STATUT FINAL${NC}"
echo "=================="
cd Docker
docker-compose ps

echo ""
echo -e "${GREEN}🎉 Déploiement terminé !${NC}"
echo ""
echo -e "${BLUE}📱 Accès aux services:${NC}"
echo "  • Application Web: http://localhost"
echo "  • TGI Mistral API: http://localhost:8080"
echo "  • ChromaDB: http://localhost:8000"
echo "  • Retriever API: http://localhost:5001"
echo ""
echo -e "${BLUE}🔧 Commandes utiles:${NC}"
echo "  • Logs: docker-compose logs -f [service]"
echo "  • Redémarrer: docker-compose restart [service]"
echo "  • Arrêter: docker-compose down"
echo "  • Test complet: python3 test_tgi_mistral.py"
echo ""
echo -e "${YELLOW}📚 Documentation: METHODE_MISTRAL.txt${NC}" 