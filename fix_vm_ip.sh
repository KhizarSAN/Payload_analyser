#!/bin/bash

echo "🔧 CORRECTION DE L'IP LAN DE LA VM"
echo "=================================="

# IP LAN correcte détectée
VM_LAN_IP="192.168.1.54"

echo "📍 IP LAN détectée: $VM_LAN_IP"
echo ""

# Mettre à jour le fichier hosts local
echo "🔧 Mise à jour du fichier hosts local..."
if grep -q "payload-analyser.ai" /etc/hosts; then
    sudo sed -i '/payload-analyser.ai/d' /etc/hosts
fi

echo "$VM_LAN_IP payload-analyser.ai" | sudo tee -a /etc/hosts > /dev/null
echo "✅ Fichier hosts mis à jour: $VM_LAN_IP payload-analyser.ai"

# Mettre à jour le script de configuration client dans la VM
echo "🔧 Mise à jour du script de configuration client..."
cat > setup_client_dns_fixed.sh << EOF
#!/bin/bash

echo "🌐 CONFIGURATION DNS CLIENT - payload-analyser.ai"
echo "================================================"

# IP du serveur
SERVER_IP="$VM_LAN_IP"

echo "📍 IP du serveur: \$SERVER_IP"

# Configuration du fichier hosts
HOSTS_ENTRY="\$SERVER_IP payload-analyser.ai"

# Vérifier si l'entrée existe déjà
if grep -q "payload-analyser.ai" /etc/hosts; then
    echo "⚠️ L'entrée payload-analyser.ai existe déjà dans /etc/hosts"
    echo "🔄 Mise à jour de l'entrée..."
    sudo sed -i '/payload-analyser.ai/d' /etc/hosts
fi

# Ajouter la nouvelle entrée
echo "\$HOSTS_ENTRY" | sudo tee -a /etc/hosts > /dev/null
echo "✅ Entrée ajoutée dans /etc/hosts: \$HOSTS_ENTRY"

# Test de connectivité
echo "🔍 Test de connectivité..."
if curl -s --connect-timeout 5 "http://\$SERVER_IP/" > /dev/null 2>&1; then
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
echo "   • http://\$SERVER_IP"
echo ""
EOF

chmod +x setup_client_dns_fixed.sh
echo "✅ Script de configuration client mis à jour"

# Test de connectivité
echo ""
echo "🔍 Test de connectivité..."
if ping -c 1 "$VM_LAN_IP" > /dev/null 2>&1; then
    echo "✅ Serveur accessible via ping"
else
    echo "⚠️ Serveur non accessible via ping (peut être normal)"
fi

if curl -s --connect-timeout 5 "http://$VM_LAN_IP/" > /dev/null 2>&1; then
    echo "✅ Application web accessible via IP"
else
    echo "❌ Application web non accessible via IP"
fi

if curl -s --connect-timeout 5 "http://payload-analyser.ai/" > /dev/null 2>&1; then
    echo "✅ Application web accessible via nom de domaine"
else
    echo "❌ Application web non accessible via nom de domaine"
fi

echo ""
echo "🎉 CONFIGURATION TERMINÉE !"
echo "=========================="
echo ""
echo "🌐 ACCÈS DISPONIBLES:"
echo "   • IP directe: http://$VM_LAN_IP"
echo "   • Nom de domaine: http://payload-analyser.ai"
echo ""
echo "🔧 POUR LES AUTRES MACHINES DU RÉSEAU:"
echo "   Utilisez le script: ./setup_client_dns_fixed.sh"
echo "   Ou ajoutez manuellement dans /etc/hosts:"
echo "   $VM_LAN_IP payload-analyser.ai"
echo ""
echo "📋 SERVICES DISPONIBLES:"
echo "   • Application Web: http://$VM_LAN_IP"
echo "   • Ollama SOC: http://$VM_LAN_IP:11434"
echo "   • ChromaDB: http://$VM_LAN_IP:8000"
echo "   • Retriever API: http://$VM_LAN_IP:5001" 