# 🚀 GUIDE DE DÉPLOIEMENT SOC - ENVIRONNEMENT IA QRADAR

## 📋 RÉSUMÉ DES MODIFICATIONS

### ✅ **Ce qui a été configuré :**

1. **Migration de TGI vers Ollama** : Remplacement du service TGI par Ollama pour une IA locale plus simple
2. **Modèles SOC optimisés** : Configuration des modèles spécialisés cybersécurité
3. **VM 8GB RAM** : Configuration du Vagrantfile pour 8GB RAM et 4 CPU cores
4. **Scripts automatisés** : Création de scripts d'installation et de vérification
5. **Chemins corrigés** : Vérification et correction de tous les chemins relatifs

## 🧠 MODÈLES SOC CONFIGURÉS

### **Détection automatique selon la RAM :**

| RAM | Modèle | Description | Performance |
|-----|--------|-------------|-------------|
| **4-6GB** | `openhermes-2.5-mistral:7b-q4_K_M` | Rapide et efficace | ⚡⚡⚡ |
| **6-8GB** | `nous-hermes-2-mistral:7b-dpo-q4_K_M` | Équilibré | ⚡⚡⚡⚡ |
| **8GB+** | `mixtral:8x7b-instruct-q4_K_M` | Très puissant | ⚡⚡⚡⚡⚡ |

### **Fallback automatique :**
- **TinyLlama** : `tinyllama:1.1b-chat` (si aucun modèle SOC disponible)

## 🔧 FICHIERS MODIFIÉS

### **1. Docker/docker-compose.yml**
- ✅ Ajout du service Ollama
- ✅ Suppression du service TGI (commenté)
- ✅ Configuration des volumes et ports
- ✅ Mise à jour des dépendances

### **2. Docker/retriever/app.py**
- ✅ Détection automatique des modèles disponibles
- ✅ Choix intelligent du modèle selon la RAM
- ✅ Configuration des paramètres optimisés
- ✅ Gestion des erreurs améliorée

### **3. Vagrantfile**
- ✅ RAM augmentée à 8GB
- ✅ CPU augmentés à 4 cores
- ✅ Port Ollama (11434) configuré
- ✅ Messages de fin mis à jour

### **4. Scripts créés**
- ✅ `setup_soc_models.sh` : Installation automatique des modèles SOC
- ✅ `verify_config.sh` : Vérification des configurations

## 🚀 PROCÉDURE DE DÉPLOIEMENT

### **Étape 1 : Vérification**
```bash
# Vérifier que tout est correctement configuré
./verify_config.sh
```

### **Étape 2 : Démarrage de la VM**
```bash
# Démarrer la VM avec 8GB RAM
vagrant up

# Se connecter à la VM
vagrant ssh
```

### **Étape 3 : Installation des modèles SOC**
```bash
# Dans la VM, installer les modèles SOC
cd /vagrant
chmod +x setup_soc_models.sh
./setup_soc_models.sh
```

## 🌐 SERVICES DISPONIBLES

| Service | URL | Port | Description |
|---------|-----|------|-------------|
| **Interface Web** | http://localhost:5000 | 5000 | Interface utilisateur |
| **API Retriever** | http://localhost:5001 | 5001 | API d'analyse SOC |
| **Health Check** | http://localhost:5001/health | 5001 | État des services |
| **Statistiques** | http://localhost:5001/stats | 5001 | Stats du système |
| **Ollama SOC** | http://localhost:11434 | 11434 | Serveur IA SOC local |
| **ChromaDB** | http://localhost:8000 | 8000 | Base vectorielle |
| **MySQL** | localhost:3306 | 3306 | Base de données |

## 📝 COMMANDES UTILES

### **Gestion des services**
```bash
# Voir les logs
docker logs mistral_retriever
docker logs qradar_ticket

# Redémarrer un service
cd Docker && docker-compose restart retriever

# Arrêter tout
cd Docker && docker-compose down

# Voir les statistiques
curl http://localhost:5001/stats
```

### **Gestion des modèles IA**
```bash
# Lister les modèles installés
curl http://localhost:11434/api/tags

# Supprimer un modèle
curl -X DELETE http://localhost:11434/api/delete -d '{"name": "model_name"}'

# Installer un nouveau modèle
curl -X POST http://localhost:11434/api/pull -d '{"name": "model_name"}'
```

### **Tests et diagnostics**
```bash
# Test de santé complet
curl http://localhost:5001/health | jq .

# Test d'analyse SOC
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"payload":"Suspicious activity detected from IP 192.168.1.100 - Multiple failed login attempts"}'

# Test direct Ollama SOC
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "mixtral:8x7b-instruct-q4_K_M", "prompt": "Analyse cette menace cybersécurité", "stream": false}'
```

## 🔍 DÉPANNAGE

### **Problèmes courants**

#### 1. **Service ne démarre pas**
```bash
# Vérifier les logs
docker logs mistral_retriever --tail 50

# Reconstruire l'image
cd Docker && docker-compose build retriever
```

#### 2. **Erreur de mémoire**
```bash
# Vérifier la RAM disponible
free -h

# Utiliser un modèle plus léger
curl -X POST http://localhost:11434/api/pull -d '{"name": "openhermes-2.5-mistral:7b-q4_K_M"}'
```

#### 3. **Erreur MySQL**
```bash
# Vérifier la base de données
docker exec -it mysql_payload mysql -u root -proot -e "SHOW DATABASES;"
```

#### 4. **Erreur ChromaDB**
```bash
# Redémarrer ChromaDB
cd Docker && docker-compose restart chromadb
```

## 🎯 FONCTIONNALITÉS SOC

### ✅ **Ce qui fonctionne**
- **IA SOC locale** : Modèles optimisés cybersécurité via Ollama
- **RAG** : Recherche d'analyses similaires
- **Embeddings** : Stockage vectoriel ChromaDB
- **Base de données** : MySQL + SQLite
- **Interface web** : Analyse de payloads QRadar
- **API REST** : Endpoints d'analyse SOC
- **Logs complets** : Traçabilité des analyses

### 🔄 **Apprentissage automatique**
- **Contexte historique** : Utilise les analyses précédentes
- **Similarité** : Trouve des cas similaires
- **Amélioration** : Le système s'améliore avec l'usage

## 🚀 OPTIMISATIONS SOC

### **Avec 8GB+ RAM**
1. **Mixtral 8x7B** : Analyse très détaillée et précise
2. **Nous-Hermes-2-Mistral** : Équilibre performance/précision
3. **OpenHermes-2.5-Mistral** : Rapidité optimale

### **Améliorations futures**
1. **GPU** : Accélération matérielle
2. **Modèles spécialisés** : IA dédiée SOC/cybersécurité
3. **Interface avancée** : Dashboard temps réel SOC

## 📞 SUPPORT

En cas de problème :
1. Vérifier les logs : `docker logs mistral_retriever`
2. Tester les services : `curl http://localhost:5001/health`
3. Redémarrer : `cd Docker && docker-compose restart`

---

**🎉 Votre environnement SOC d'IA locale pour QRadar est prêt !**

### **Prochaines étapes :**
1. Tester l'analyse de payloads réels
2. Optimiser les prompts pour votre contexte
3. Ajouter des patterns spécifiques à votre environnement
4. Configurer des alertes automatiques 