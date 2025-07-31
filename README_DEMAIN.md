# 🚀 GUIDE DÉMARRAGE RAPIDE - ENVIRONNEMENT IA QRADAR

## 📋 PRÉREQUIS POUR DEMAIN

### 1. **Nouvelle VM Vagrant avec plus de RAM**
```bash
# Dans le Vagrantfile, augmenter la RAM à 8GB minimum
config.vm.provider "virtualbox" do |vb|
  vb.memory = "8192"  # 8GB RAM
  vb.cpus = 4         # 4 CPU cores
end
```

### 2. **Démarrer la nouvelle VM**
```bash
vagrant up
vagrant ssh
```

## 🎯 DÉMARRAGE AUTOMATIQUE

### Option 1: Script complet (recommandé)
```bash
cd /vagrant/Docker
chmod +x setup_ollama_complete.sh
./setup_ollama_complete.sh
```

### Option 2: Script IA puissante (si 8GB+ RAM)
```bash
cd /vagrant/Docker
chmod +x setup_powerful_ai.sh
./setup_powerful_ai.sh
```

## 🔧 CONFIGURATION MANUELLE (si nécessaire)

### 1. **Vérifier l'environnement**
```bash
# Vérifier Docker
docker --version
docker-compose --version

# Vérifier les fichiers
ls -la docker-compose-ollama.yml
ls -la retriever/app.py
```

### 2. **Démarrer les services**
```bash
# Démarrer tout
docker-compose -f docker-compose-ollama.yml up -d

# Vérifier les services
docker ps
```

### 3. **Installer le modèle IA**
```bash
# Pour TinyLlama (léger)
curl -X POST http://localhost:11434/api/pull -d '{"name": "tinyllama:1.1b-chat"}'

# Pour Mistral 7B (puissant - 8GB+ RAM)
curl -X POST http://localhost:11434/api/pull -d '{"name": "mistral:7b-instruct-q4_K_M"}'
```

### 4. **Tester l'installation**
```bash
# Test Ollama
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "tinyllama:1.1b-chat", "prompt": "Bonjour", "stream": false}'

# Test Retriever
curl http://localhost:5001/health

# Test Analyse
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"payload":"Test QRadar"}'
```

## 🌐 ACCÈS AUX SERVICES

| Service | URL | Port | Description |
|---------|-----|------|-------------|
| **Interface Web** | http://localhost:5000 | 5000 | Interface utilisateur |
| **API Retriever** | http://localhost:5001 | 5001 | API d'analyse IA |
| **Health Check** | http://localhost:5001/health | 5001 | État des services |
| **Statistiques** | http://localhost:5001/stats | 5001 | Stats du système |
| **Ollama** | http://localhost:11434 | 11434 | Serveur IA local |
| **ChromaDB** | http://localhost:8000 | 8000 | Base vectorielle |
| **MySQL** | localhost:3306 | 3306 | Base de données |

## 🧠 MODÈLES IA DISPONIBLES

### Modèles légers (2-4GB RAM)
- **TinyLlama 1.1B** : `tinyllama:1.1b-chat` (1GB RAM)
- **Phi-3 Mini** : `phi3:mini` (2GB RAM)

### Modèles puissants (8GB+ RAM)
- **Mistral 7B** : `mistral:7b-instruct-q4_K_M` (4GB RAM)
- **Llama2 7B** : `llama2:7b-chat-q4_K_M` (4GB RAM)

## 📝 COMMANDES UTILES

### Gestion des services
```bash
# Voir les logs
docker logs mistral_retriever
docker logs qradar_ticket

# Redémarrer un service
docker-compose -f docker-compose-ollama.yml restart retriever

# Arrêter tout
docker-compose -f docker-compose-ollama.yml down

# Voir les statistiques
curl http://localhost:5001/stats
```

### Gestion des modèles IA
```bash
# Lister les modèles installés
curl http://localhost:11434/api/tags

# Supprimer un modèle
curl -X DELETE http://localhost:11434/api/delete -d '{"name": "model_name"}'

# Installer un nouveau modèle
curl -X POST http://localhost:11434/api/pull -d '{"name": "model_name"}'
```

### Tests et diagnostics
```bash
# Test de santé complet
curl http://localhost:5001/health | jq .

# Test d'analyse simple
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"payload":"Test payload QRadar"}'

# Test direct Ollama
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "tinyllama:1.1b-chat", "prompt": "Test", "stream": false}'
```

## 🔍 DÉPANNAGE

### Problèmes courants

#### 1. **Service ne démarre pas**
```bash
# Vérifier les logs
docker logs mistral_retriever --tail 50

# Reconstruire l'image
docker-compose -f docker-compose-ollama.yml build retriever
```

#### 2. **Erreur de mémoire**
```bash
# Vérifier la RAM disponible
free -h

# Utiliser un modèle plus léger
curl -X POST http://localhost:11434/api/pull -d '{"name": "tinyllama:1.1b-chat"}'
```

#### 3. **Erreur MySQL**
```bash
# Vérifier la base de données
docker exec -it mysql_payload mysql -u root -proot -e "SHOW DATABASES;"
```

#### 4. **Erreur ChromaDB**
```bash
# Redémarrer ChromaDB
docker-compose -f docker-compose-ollama.yml restart chromadb
```

## 🎯 FONCTIONNALITÉS

### ✅ Ce qui fonctionne
- **IA locale** : TinyLlama/Mistral via Ollama
- **RAG** : Recherche d'analyses similaires
- **Embeddings** : Stockage vectoriel ChromaDB
- **Base de données** : MySQL + SQLite
- **Interface web** : Analyse de payloads QRadar
- **API REST** : Endpoints d'analyse
- **Logs complets** : Traçabilité des analyses

### 🔄 Apprentissage automatique
- **Contexte historique** : Utilise les analyses précédentes
- **Similarité** : Trouve des cas similaires
- **Amélioration** : Le système s'améliore avec l'usage

## 🚀 OPTIMISATIONS POUR DEMAIN

### Avec plus de RAM (8GB+)
1. **Mistral 7B** : Meilleure qualité d'analyse
2. **Plus de contexte** : Analyses plus détaillées
3. **Parallélisation** : Traitement plus rapide

### Améliorations possibles
1. **GPU** : Accélération matérielle
2. **Modèles spécialisés** : IA dédiée cybersécurité
3. **Interface avancée** : Dashboard temps réel

## 📞 SUPPORT

En cas de problème :
1. Vérifier les logs : `docker logs mistral_retriever`
2. Tester les services : `curl http://localhost:5001/health`
3. Redémarrer : `docker-compose -f docker-compose-ollama.yml restart`

---

**🎉 Votre environnement d'IA locale pour QRadar est prêt !** 