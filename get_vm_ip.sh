#!/bin/bash

echo "🔍 RÉCUPÉRATION DE L'IP LAN DE LA VM"
echo "===================================="

# Méthode 1: Via VirtualBox Guest Properties
echo "📍 Tentative via VirtualBox..."
VM_IP=$(VBoxManage guestproperty get qradar-debian "/VirtualBox/GuestInfo/Net/1/V4/IP" 2>/dev/null | cut -d' ' -f2)

if [ ! -z "$VM_IP" ] && [ "$VM_IP" != "No value set!" ]; then
    echo "✅ IP LAN détectée via VirtualBox: $VM_IP"
else
    echo "❌ IP non trouvée via VirtualBox"
    
    # Méthode 2: Via SSH et commande réseau
    echo "📍 Tentative via SSH..."
    VM_IP=$(vagrant ssh -c "ip route get 8.8.8.8 | awk '{print \$7}' | head -1" --no-tty 2>/dev/null | tr -d '\r')
    
    if [ ! -z "$VM_IP" ]; then
        echo "✅ IP LAN détectée via SSH: $VM_IP"
    else
        echo "❌ IP non trouvée via SSH"
        
        # Méthode 3: Via hostname -I
        echo "📍 Tentative via hostname..."
        VM_IP=$(vagrant ssh -c "hostname -I | awk '{print \$1}'" --no-tty 2>/dev/null | tr -d '\r')
        
        if [ ! -z "$VM_IP" ]; then
            echo "✅ IP LAN détectée via hostname: $VM_IP"
        else
            echo "❌ Impossible de détecter l'IP LAN automatiquement"
            echo ""
            echo "🔧 SOLUTIONS MANUELLES:"
            echo "1. Vérifiez que la VM a bien une interface réseau bridge"
            echo "2. Vérifiez que VirtualBox est configuré pour l'accès réseau"
            echo "3. Redémarrez la VM: vagrant reload"
            exit 1
        fi
    fi
fi

echo ""
echo "🌐 IP LAN DE LA VM: $VM_IP"
echo ""

# Mettre à jour le fichier hosts local
echo "🔧 Mise à jour du fichier hosts local..."
if grep -q "payload-analyser.ai" /etc/hosts; then
    sudo sed -i '/payload-analyser.ai/d' /etc/hosts
fi

echo "$VM_IP payload-analyser.ai" | sudo tee -a /etc/hosts > /dev/null
echo "✅ Fichier hosts mis à jour: $VM_IP payload-analyser.ai"

# Test de connectivité
echo ""
echo "🔍 Test de connectivité..."
if ping -c 1 "$VM_IP" > /dev/null 2>&1; then
    echo "✅ Serveur accessible via ping"
else
    echo "⚠️ Serveur non accessible via ping (peut être normal)"
fi

if curl -s --connect-timeout 5 "http://$VM_IP/" > /dev/null 2>&1; then
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
echo "   • IP directe: http://$VM_IP"
echo "   • Nom de domaine: http://payload-analyser.ai"
echo ""
echo "🔧 POUR LES AUTRES MACHINES DU RÉSEAU:"
echo "   Ajoutez cette ligne dans leur fichier /etc/hosts:"
echo "   $VM_IP payload-analyser.ai" 