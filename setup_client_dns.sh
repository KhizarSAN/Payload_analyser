#!/bin/bash

echo "🌐 CONFIGURATION DNS CLIENT - payload-analyser.ai"
echo "================================================"

# IP du serveur
SERVER_IP="10.0.2.15"

echo "📍 IP du serveur: "

# Configuration du fichier hosts
HOSTS_ENTRY=" payload-analyser.ai"

# Vérifier si l'entrée existe déjà
if grep -q "payload-analyser.ai" /etc/hosts; then
    echo "⚠️ L'entrée payload-analyser.ai existe déjà dans /etc/hosts"
    echo "🔄 Mise à jour de l'entrée..."
    sudo sed -i '/payload-analyser.ai/d' /etc/hosts
fi

# Ajouter la nouvelle entrée
echo "" | sudo tee -a /etc/hosts > /dev/null
echo "✅ Entrée ajoutée dans /etc/hosts: "

# Test de connectivité
echo "🔍 Test de connectivité..."
if curl -s --connect-timeout 5 "http:///" > /dev/null 2>&1; then
    echo "✅ Application web accessible via IP"
else
    echo "⚠️ Application web pas encore accessible via IP"
fi

if curl -s --connect-timeout 5 "http://payload-analyser.ai/" > /dev/null 2>&1; then
    echo "✅ Application web accessible via nom de domaine"
else
    echo "⚠️ Application web pas encore accessible via nom de domaine"
fi

echo ""
echo "🎉 Configuration DNS client terminée !"
echo "🌐 Accès disponibles:"
echo "   • http://payload-analyser.ai"
echo "   • http://"
echo ""
