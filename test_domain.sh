#!/bin/bash

echo "🔍 TEST DE CONFIGURATION DU NOM DE DOMAINE"
echo "=========================================="

# IP du serveur
SERVER_IP="192.168.1.54"

echo "📍 IP du serveur: $SERVER_IP"
echo "🌐 Nom de domaine: payload-analyser.ai"
echo ""

# Test de résolution DNS
echo "🔍 Test de résolution DNS..."
if nslookup payload-analyser.ai > /dev/null 2>&1; then
    echo "✅ Résolution DNS fonctionne"
else
    echo "❌ Résolution DNS ne fonctionne pas"
fi

# Test de ping
echo "📡 Test de ping..."
if ping -c 1 payload-analyser.ai > /dev/null 2>&1; then
    echo "✅ Ping vers le nom de domaine fonctionne"
else
    echo "❌ Ping vers le nom de domaine ne fonctionne pas"
fi

# Test HTTP via IP
echo "🌐 Test HTTP via IP..."
if curl -s --connect-timeout 5 "http://$SERVER_IP/" > /dev/null 2>&1; then
    echo "✅ Application accessible via IP"
else
    echo "❌ Application non accessible via IP"
fi

# Test HTTP via nom de domaine
echo "🌐 Test HTTP via nom de domaine..."
if curl -s --connect-timeout 5 "http://payload-analyser.ai/" > /dev/null 2>&1; then
    echo "✅ Application accessible via nom de domaine"
else
    echo "❌ Application non accessible via nom de domaine"
fi

# Vérifier le fichier hosts
echo ""
echo "📋 VÉRIFICATION DU FICHIER HOSTS:"
if grep -q "payload-analyser.ai" /etc/hosts; then
    echo "✅ Entrée trouvée dans /etc/hosts:"
    grep "payload-analyser.ai" /etc/hosts
else
    echo "❌ Aucune entrée trouvée dans /etc/hosts"
    echo ""
    echo "🔧 SOLUTION:"
    echo "Ajoutez cette ligne dans /etc/hosts:"
    echo "$SERVER_IP payload-analyser.ai"
fi

echo ""
echo "🎯 RÉSULTAT:"
if curl -s --connect-timeout 5 "http://payload-analyser.ai/" > /dev/null 2>&1; then
    echo "✅ SUCCÈS: Le nom de domaine fonctionne !"
    echo "🌐 Vous pouvez maintenant utiliser: http://payload-analyser.ai"
else
    echo "❌ ÉCHEC: Le nom de domaine ne fonctionne pas encore"
    echo "🔧 Vérifiez que vous avez bien ajouté l'entrée dans /etc/hosts"
fi 