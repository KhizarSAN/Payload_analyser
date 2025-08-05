#!/bin/bash

echo "🔍 TEST DE CONNECTIVITÉ RÉSEAU"
echo "=============================="

# Récupérer l'IP du serveur
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "📍 IP du serveur: $SERVER_IP"
echo ""

# Test des services
SERVICES=(
    "80:Application Web (Nginx)"
    "5000:Application Flask"
    "11434:Ollama SOC"
    "8000:ChromaDB"
    "5001:Retriever API"
)

for service in "${SERVICES[@]}"; do
    port=$(echo $service | cut -d: -f1)
    name=$(echo $service | cut -d: -f2)
    
    if curl -s --connect-timeout 5 "http://localhost:$port/" > /dev/null 2>&1; then
        echo "✅ $name accessible localement"
    else
        echo "❌ $name non accessible localement"
    fi
    
    if curl -s --connect-timeout 5 "http://$SERVER_IP:$port/" > /dev/null 2>&1; then
        echo "✅ $name accessible via réseau"
    else
        echo "❌ $name non accessible via réseau"
    fi
done

echo ""
echo "🌐 Accès réseau disponibles:"
echo "   • Application Web: http://$SERVER_IP"
echo "   • Ollama SOC: http://$SERVER_IP:11434"
echo "   • ChromaDB: http://$SERVER_IP:8000"
echo "   • Retriever API: http://$SERVER_IP:5001"
echo ""
