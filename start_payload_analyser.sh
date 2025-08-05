#!/bin/bash

echo "🚀 DÉMARRAGE PAYLOAD ANALYSER - LAN ACCESS"
echo "=========================================="

# Vérifier que Vagrant est installé
if ! command -v vagrant &> /dev/null; then
    echo "❌ Vagrant n'est pas installé"
    exit 1
fi

# Démarrer la VM
echo "🔧 Démarrage de la VM Vagrant..."
vagrant up

# Attendre que la VM soit prête
echo "⏳ Attente que la VM soit prête..."
sleep 30

# Vérifier les services
echo "🔍 Vérification des services..."

# Test de l'application web
if curl -s http://payload-analyser.ai/ > /dev/null; then
    echo "✅ Application accessible via payload-analyser.ai"
else
    echo "⚠️ Application pas encore prête"
fi

# Test de l'IP directe
LAN_IP=$(grep "payload-analyser.ai" /etc/hosts | awk '{print $1}')
if curl -s http://$LAN_IP/ > /dev/null; then
    echo "✅ Application accessible via IP directe: $LAN_IP"
else
    echo "⚠️ Application pas accessible via IP directe"
fi

echo ""
echo "🎉 DÉMARRAGE TERMINÉ !"
echo "====================="
echo ""
echo "📱 Accès via nom de domaine:"
echo "   http://payload-analyser.ai"
echo ""
echo "🌐 Accès via IP directe:"
echo "   http://$LAN_IP"
echo ""
echo "🔧 Autres services:"
echo "   • Ollama SOC: http://$LAN_IP:11434"
echo "   • ChromaDB: http://$LAN_IP:8000"
echo "   • Retriever API: http://$LAN_IP:5001"
echo "   • MySQL: $LAN_IP:3307"
echo ""
echo "💡 Pour arrêter: vagrant halt"
echo "💡 Pour redémarrer: vagrant reload"
