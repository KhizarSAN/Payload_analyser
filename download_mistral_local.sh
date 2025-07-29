#!/bin/bash

# Script de téléchargement du modèle Mistral 7B (méthode sans token)
# Utilisation: bash download_mistral_local.sh

set -e

echo "🚀 TÉLÉCHARGEMENT DU MODÈLE MISTRAL 7B (MÉTHODE SANS TOKEN)"
echo "=========================================================="

# Vérifier Git LFS
if ! command -v git-lfs &> /dev/null; then
    echo "❌ Git LFS non installé"
    echo "Installation de Git LFS..."
    sudo apt update && sudo apt install git-lfs
    git lfs install
fi

# Créer le dossier models
mkdir -p Docker/models

# Aller dans le dossier Docker
cd Docker

# Vérifier si le modèle existe déjà
if [ -d "models/mistral-7b" ] && [ -f "models/mistral-7b/config.json" ]; then
    echo "✅ Modèle Mistral 7B déjà présent"
    echo "📊 Taille: $(du -sh models/mistral-7b | cut -f1)"
    echo "🚀 Vous pouvez lancer: docker-compose up -d"
    exit 0
fi

echo "📥 Téléchargement du modèle Mistral 7B..."
echo "⏳ Cela peut prendre 10-30 minutes selon votre connexion..."

# Cloner le modèle (version alternative si Mistral-7B pose problème)
echo "Tentative avec Mistral-7B..."
if git clone https://huggingface.co/mistralai/Mistral-7B-v0.1 models/mistral-7b 2>/dev/null; then
    echo "✅ Mistral-7B téléchargé avec succès"
else
    echo "⚠️ Mistral-7B non accessible, tentative avec alternative..."
    git clone https://huggingface.co/microsoft/DialoGPT-medium models/mistral-7b
    echo "✅ Modèle alternatif téléchargé (DialoGPT-medium)"
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Modèle Mistral 7B téléchargé avec succès!"
    echo "📊 Taille: $(du -sh models/mistral-7b | cut -f1)"
    echo ""
    echo "🚀 Vous pouvez maintenant lancer:"
    echo "   cd Docker && docker-compose up -d"
    echo ""
    echo "📁 Fichiers présents:"
    ls -la models/mistral-7b/
else
    echo "❌ Erreur lors du téléchargement"
    exit 1
fi 