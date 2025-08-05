#!/bin/bash

echo "🌐 CONFIGURATION DNS CLIENT - payload-analyser.ai"
echo "================================================"

# IP du serveur
SERVER_IP="192.168.1.54"

echo "📍 IP du serveur: $SERVER_IP"

# Configuration du fichier hosts
HOSTS_ENTRY="$SERVER_IP payload-analyser.ai"

# Vérifier si l'entrée existe déjà
if grep -q "payload-analyser.ai" /etc/hosts; then
    echo "⚠️ L'entrée payload-analyser.ai existe déjà dans /etc/hosts"
    echo "🔄 Mise à jour de l'entrée..."
    sudo sed -i '/payload-analyser.ai/d' /etc/hosts
fi

# Ajouter la nouvelle entrée
echo "$HOSTS_ENTRY" | sudo tee -a /etc/hosts > /dev/null
echo "✅ Entrée ajoutée dans /etc/hosts: $HOSTS_ENTRY"

# Test de connectivité
echo "🔍 Test de connectivité..."
if curl -s --connect-timeout 5 "http://$SERVER_IP/" > /dev/null 2>&1; then
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
echo "   • http://$SERVER_IP"
echo ""
