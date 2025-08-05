# 🌐 Configuration Réseau LAN - Payload Analyser

Ce document explique comment configurer l'application Payload Analyser pour qu'elle soit accessible sur le réseau LAN via le nom de domaine `payload-analyser.ai`.

## 📋 Prérequis

- Vagrant installé
- Docker installé
- Accès administrateur sur la machine
- Machines clientes sur le même réseau LAN

## 🚀 Configuration du Serveur

### Étape 1: Exécuter le script de configuration réseau

```bash
# Rendre le script exécutable
chmod +x setup_network_access.sh

# Exécuter la configuration
./setup_network_access.sh
```

Ce script va :
- Détecter automatiquement votre IP LAN
- Configurer le fichier `/etc/hosts`
- Modifier le `Vagrantfile` pour ajouter une interface réseau bridge
- Mettre à jour `docker-compose.yml` pour écouter sur toutes les interfaces
- Configurer Nginx pour le nom de domaine
- Configurer le firewall
- Créer un script de démarrage

### Étape 2: Redémarrer la VM

```bash
# Redémarrer la VM avec la nouvelle configuration
vagrant reload

# Ou utiliser le script de démarrage créé
./start_payload_analyser.sh
```

### Étape 3: Vérifier l'accessibilité

```bash
# Test local
curl http://payload-analyser.ai/

# Test depuis une autre machine du réseau
curl http://[IP_SERVEUR]/
```

## 🔧 Configuration des Machines Client

### Étape 1: Exécuter le script client

Sur chaque machine cliente du réseau LAN :

```bash
# Rendre le script exécutable
chmod +x setup_client_dns.sh

# Exécuter avec l'IP du serveur
./setup_client_dns.sh [IP_SERVEUR]

# Ou sans paramètre (le script demandera l'IP)
./setup_client_dns.sh
```

### Étape 2: Tester la connectivité

```bash
# Utiliser le script de test créé
./test_connection.sh
```

## 🌐 Accès Disponibles

Une fois configuré, l'application sera accessible via :

### Nom de domaine
- **Application Web**: http://payload-analyser.ai
- **Interface Nginx**: http://payload-analyser.ai

### IP directe
- **Application Web**: http://[IP_SERVEUR]
- **Interface Nginx**: http://[IP_SERVEUR]

### Services API
- **Ollama SOC**: http://[IP_SERVEUR]:11434
- **ChromaDB**: http://[IP_SERVEUR]:8000
- **Retriever API**: http://[IP_SERVEUR]:5001
- **MySQL**: [IP_SERVEUR]:3307

## 🔒 Sécurité

### Firewall
Le script configure automatiquement :
- Windows Firewall (Windows)
- UFW (Linux)

### Ports ouverts
- **80**: Nginx (HTTP)
- **5000**: Application Flask
- **11434**: Ollama
- **8000**: ChromaDB
- **5001**: Retriever API
- **3307**: MySQL

## 🛠️ Dépannage

### Problème: Application non accessible
```bash
# Vérifier que la VM est démarrée
vagrant status

# Vérifier les services Docker
vagrant ssh
docker ps

# Vérifier les logs
docker logs qradar_ticket
docker logs nginx_proxy
```

### Problème: Nom de domaine non résolu
```bash
# Vérifier le fichier hosts
cat /etc/hosts | grep payload-analyser.ai

# Tester la résolution DNS
nslookup payload-analyser.ai
```

### Problème: Firewall bloque l'accès
```bash
# Windows - Vérifier les règles
netsh advfirewall firewall show rule name="Payload Analyser*"

# Linux - Vérifier UFW
sudo ufw status
```

## 📁 Fichiers Créés

### Sur le serveur
- `setup_network_access.sh` - Script de configuration réseau
- `start_payload_analyser.sh` - Script de démarrage
- `Vagrantfile.backup` - Sauvegarde du Vagrantfile original
- `Docker/docker-compose.yml.backup` - Sauvegarde du docker-compose

### Sur les clients
- `setup_client_dns.sh` - Script de configuration DNS client
- `test_connection.sh` - Script de test de connectivité
- `payload_analyser_links.txt` - Liste des liens d'accès

## 🔄 Mise à jour

Pour mettre à jour la configuration :

```bash
# Arrêter la VM
vagrant halt

# Exécuter à nouveau le script de configuration
./setup_network_access.sh

# Redémarrer
vagrant up
```

## 📞 Support

En cas de problème :
1. Vérifier les logs : `vagrant ssh && docker logs [container_name]`
2. Tester la connectivité : `./test_connection.sh`
3. Vérifier la configuration réseau : `ipconfig` (Windows) ou `ip addr` (Linux)

## 🎯 Avantages de cette Configuration

- ✅ Accès via nom de domaine facile à retenir
- ✅ Accessible depuis toutes les machines du réseau LAN
- ✅ Configuration automatique du DNS local
- ✅ Gestion automatique du firewall
- ✅ Scripts de test et de diagnostic
- ✅ Sauvegarde des configurations originales
- ✅ Documentation complète 