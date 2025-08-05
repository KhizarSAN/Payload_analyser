# 🌐 Configuration Réseau LAN Automatique - Payload Analyser

**🎯 NOUVEAU : Configuration réseau LAN automatique intégrée dans Vagrant !**

L'application Payload Analyser est maintenant configurée automatiquement pour être accessible sur le réseau LAN via le nom de domaine `payload-analyser.ai` lors de la création de la VM.

## 🚀 Démarrage Simplifié

### Option 1: Démarrage automatique complet
```bash
# Démarrer avec configuration réseau automatique
./start_payload_analyser_lan.sh
```

### Option 2: Démarrage Vagrant classique
```bash
# Créer et démarrer la VM (configuration automatique incluse)
vagrant up
```

## ✅ Ce qui est configuré automatiquement

Lors du `vagrant up`, le système configure automatiquement :

### 🌐 Réseau
- **Interface bridge** : Accès direct au réseau LAN
- **Détection IP automatique** : L'IP LAN est détectée automatiquement
- **Ports ouverts** : Tous les services sont accessibles depuis le réseau

### 🔧 Services
- **Docker Compose** : Configuré pour écouter sur toutes les interfaces (`0.0.0.0`)
- **Nginx** : Reverse proxy configuré pour `payload-analyser.ai`
- **Firewall** : Règles automatiques pour les ports nécessaires

### 📁 Fichiers créés automatiquement
- `setup_client_dns.sh` - Script de configuration DNS pour les clients
- `test_network.sh` - Script de test de connectivité réseau
- `INSTRUCTIONS_RESEAU_LAN.txt` - Instructions complètes

## 🌐 Accès Disponibles

### Sur la machine hôte
- **Application Web** : http://localhost:5000
- **Interface Nginx** : http://localhost:8081
- **Ollama SOC** : http://localhost:11434
- **ChromaDB** : http://localhost:8000
- **Retriever API** : http://localhost:5001

### Sur le réseau LAN
- **Application Web** : http://[IP_VM]
- **Nom de domaine** : http://payload-analyser.ai
- **Ollama SOC** : http://[IP_VM]:11434
- **ChromaDB** : http://[IP_VM]:8000
- **Retriever API** : http://[IP_VM]:5001

## 🔧 Configuration des Machines Client

### Étape 1: Récupérer le script client
Le script `setup_client_dns.sh` est créé automatiquement dans la VM. Pour le récupérer :

```bash
# Depuis la machine hôte
vagrant ssh -c "cat /vagrant/setup_client_dns.sh" > setup_client_dns.sh
chmod +x setup_client_dns.sh
```

### Étape 2: Exécuter sur les machines clientes
```bash
# Sur chaque machine cliente du réseau LAN
./setup_client_dns.sh
```

## 🛠️ Commandes Utiles

### Gestion de la VM
```bash
# Démarrer
vagrant up

# Arrêter
vagrant halt

# Redémarrer
vagrant reload

# Accès SSH
vagrant ssh

# Statut
vagrant status
```

### Tests de connectivité
```bash
# Depuis la VM
./test_network.sh

# Depuis une machine cliente
./test_connection.sh
```

## 📋 Ports Utilisés

| Port | Service | Description |
|------|---------|-------------|
| 80 | Nginx | Interface web principale |
| 5000 | Flask | Application web |
| 11434 | Ollama | Service IA SOC |
| 8000 | ChromaDB | Base vectorielle |
| 5001 | Retriever | API d'analyse |
| 3307 | MySQL | Base de données |

## 🔒 Sécurité

### Firewall automatique
- **Windows** : Règles Windows Firewall ajoutées automatiquement
- **Linux** : Règles UFW configurées automatiquement

### Accès réseau
- Seuls les ports nécessaires sont ouverts
- Accès limité au réseau LAN
- Pas d'exposition sur Internet

## 🛠️ Dépannage

### Problème: Application non accessible
```bash
# Vérifier le statut de la VM
vagrant status

# Vérifier les services Docker
vagrant ssh -c "docker ps"

# Vérifier les logs
vagrant ssh -c "docker logs qradar_ticket"
```

### Problème: Nom de domaine non résolu
```bash
# Vérifier le fichier hosts
cat /etc/hosts | grep payload-analyser.ai

# Tester la résolution
nslookup payload-analyser.ai
```

### Problème: IP non détectée
```bash
# Récupérer l'IP manuellement
vagrant ssh -c "hostname -I"

# Ou via VirtualBox
VBoxManage guestproperty get qradar-debian "/VirtualBox/GuestInfo/Net/1/V4/IP"
```

## 🎯 Avantages de la Configuration Automatique

- ✅ **Zéro configuration manuelle** : Tout est automatique
- ✅ **Détection IP automatique** : Pas besoin de configurer l'IP
- ✅ **DNS automatique** : Nom de domaine configuré automatiquement
- ✅ **Firewall automatique** : Sécurité configurée automatiquement
- ✅ **Scripts générés** : Outils de configuration client créés automatiquement
- ✅ **Documentation intégrée** : Instructions créées automatiquement

## 📞 Support

En cas de problème :
1. Vérifier les logs : `vagrant ssh -c "docker logs [container_name]"`
2. Tester la connectivité : `./test_network.sh`
3. Vérifier la configuration réseau : `vagrant ssh -c "ip addr"`

## 🔄 Mise à jour

Pour mettre à jour la configuration :
```bash
# Arrêter la VM
vagrant halt

# Redémarrer avec nouvelle configuration
vagrant up
```

La configuration réseau est automatiquement mise à jour lors de chaque `vagrant up` !

---

**🎉 Résultat : Une seule commande `vagrant up` et votre application est accessible sur tout le réseau LAN via `payload-analyser.ai` !** 