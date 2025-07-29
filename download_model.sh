#!/bin/bash

# Script de téléchargement du modèle Mistral 7B
# Utilisation: HF_HUB_TOKEN=<votre_token> bash download_model.sh

set -e

echo "🚀 TÉLÉCHARGEMENT DU MODÈLE MISTRAL 7B"
echo "======================================"

# Vérifier le token Hugging Face
if [ -z "$HF_HUB_TOKEN" ]; then
    echo "❌ Erreur: HF_HUB_TOKEN non défini"
    echo "Usage: HF_HUB_TOKEN=<votre_token> bash download_model.sh"
    exit 1
fi

# Créer les dossiers
mkdir -p Docker/models/mistral-7b
mkdir -p Docker/cache

echo "📁 Dossiers créés"

# Télécharger le modèle
echo "📥 Téléchargement du modèle Mistral 7B..."
echo "⏳ Cela peut prendre plusieurs minutes..."

python3 - <<EOF
import os
from transformers import AutoTokenizer, AutoModelForCausalLM

# Configuration
os.environ['HF_HUB_TOKEN'] = '${HF_HUB_TOKEN}'
model_path = "Docker/models/mistral-7b"

print("🔧 Téléchargement du tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(
    "mistralai/Mistral-7B-v0.1", 
    trust_remote_code=True,
    cache_dir="Docker/cache"
)
tokenizer.save_pretrained(model_path)
print("✅ Tokenizer téléchargé")

print("🔧 Téléchargement du modèle...")
model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-v0.1",
    trust_remote_code=True,
    torch_dtype="auto",
    device_map="auto",
    cache_dir="Docker/cache"
)
model.save_pretrained(model_path)
print("✅ Modèle téléchargé")

print("🎉 Téléchargement terminé avec succès!")
EOF

echo ""
echo "✅ Modèle Mistral 7B téléchargé dans Docker/models/mistral-7b"
echo "📊 Taille du modèle: $(du -sh Docker/models/mistral-7b | cut -f1)"
echo ""
echo "🚀 Vous pouvez maintenant lancer:"
echo "   cd Docker && docker-compose up -d" 