# 🚀 Mistral 7B - Méthode Sans Token (100% Local)

## 📋 Vue d'ensemble

Cette implémentation utilise **Mistral 7B** avec une approche **100% locale** sans dépendance à Hugging Face ou à des tokens d'API.

### ✅ Avantages de cette méthode

- **🔒 Aucune dépendance externe** - Fonctionne même si Hugging Face est down
- **⚡ Démarrage rapide** - Pas de téléchargement à chaque redémarrage
- **🚫 Pas de limite de rate** - Pas de quota Hugging Face
- **🛡️ Plus stable** - Pas de problème d'authentification
- **🏢 Compatible réseau d'entreprise** - Évite les blocages potentiels

## 🛠️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   TGI Mistral   │    │   ChromaDB      │
│   Web Flask     │◄──►│   (Local Model) │◄──►│   (Vector DB)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Retriever     │    │   MySQL DB      │    │   Nginx Proxy   │
│   (FastAPI)     │    │   (Analyses)    │    │   (Port 80)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 Services Docker

1. **TGI Mistral** (`mistral_tgi`) - Port 8080
   - Modèle local : `./models/mistral-7b`
   - Pas de token HF requis

2. **ChromaDB** (`chromadb`) - Port 8000
   - Base de données vectorielle
   - Stockage des embeddings

3. **Retriever** (`mistral_retriever`) - Port 5001
   - Service FastAPI
   - RAG (Retrieval-Augmented Generation)

4. **MySQL** (`mysql_payload`) - Port 3306
   - Base de données principale
   - Stockage des analyses

5. **Web App** (`qradar_ticket`) - Port 5000
   - Application Flask
   - Interface utilisateur

6. **Nginx** (`nginx_front`) - Port 80
   - Reverse proxy
   - Point d'entrée principal

## 🚀 Déploiement

### Option 1 : Script automatique (Recommandé)

```bash
# Déploiement complet automatique
bash deploy_mistral_local.sh
```

### Option 2 : Déploiement manuel

#### 1. Télécharger le modèle

**Linux/Mac :**
```bash
bash download_mistral_local.sh
```

**Windows :**
```powershell
.\download_mistral_local.ps1
```

#### 2. Lancer les services

```bash
cd Docker
docker-compose up -d
```

#### 3. Initialiser la base de données

```bash
python3 init_db.py
python3 init_admin.py
```

## 📁 Structure des fichiers

```
qradar_ticket/
├── Docker/
│   ├── docker-compose.yml          # Configuration des services
│   ├── models/
│   │   └── mistral-7b/             # Modèle Mistral (téléchargé)
│   ├── retriever/
│   │   ├── Dockerfile              # Image Retriever
│   │   ├── requirements.txt        # Dépendances Python
│   │   └── app.py                  # Service FastAPI
│   └── cache/                      # Cache Hugging Face
├── download_mistral_local.sh       # Script téléchargement (Linux/Mac)
├── download_mistral_local.ps1      # Script téléchargement (Windows)
├── deploy_mistral_local.sh         # Script déploiement complet
└── README_MISTRAL_LOCAL.md         # Ce fichier
```

## 🔧 Configuration

### Variables d'environnement

Aucune variable d'environnement requise ! Le système fonctionne entièrement en local.

### Ports utilisés

- **80** : Nginx (accès principal)
- **5000** : Application Web Flask
- **5001** : Retriever API
- **8000** : ChromaDB
- **8080** : TGI Mistral
- **3306** : MySQL

## 🧪 Tests

### Test des services

```bash
# Test TGI Mistral
curl http://localhost:8080/health

# Test ChromaDB
curl http://localhost:8000/api/v1/heartbeat

# Test Retriever
curl http://localhost:5001/health

# Test d'analyse
curl -X POST http://localhost:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"payload":"Test payload QRadar"}'
```

### Test complet

```bash
python3 test_tgi_mistral.py
```

## 📊 Monitoring

### Logs des services

```bash
# Logs TGI Mistral
docker-compose logs -f tgi

# Logs ChromaDB
docker-compose logs -f chromadb

# Logs Retriever
docker-compose logs -f retriever

# Logs Application Web
docker-compose logs -f web
```

### Statut des conteneurs

```bash
docker-compose ps
```

## 🔄 Maintenance

### Redémarrer un service

```bash
docker-compose restart [service_name]
```

### Mettre à jour le modèle

```bash
# Supprimer l'ancien modèle
rm -rf Docker/models/mistral-7b

# Retélécharger
bash download_mistral_local.sh

# Redémarrer TGI
docker-compose restart tgi
```

### Nettoyage complet

```bash
cd Docker
docker-compose down -v
docker system prune -f
```

## 🚨 Dépannage

### Problème : Modèle non trouvé

```bash
# Vérifier que le modèle existe
ls -la Docker/models/mistral-7b/

# Retélécharger si nécessaire
bash download_mistral_local.sh
```

### Problème : Service non accessible

```bash
# Vérifier les logs
docker-compose logs [service_name]

# Vérifier le statut
docker-compose ps
```

### Problème : Port déjà utilisé

```bash
# Vérifier les ports utilisés
netstat -tulpn | grep :80
netstat -tulpn | grep :8080

# Arrêter les services conflictuels
sudo systemctl stop [service_name]
```

## 📈 Performance

### Ressources recommandées

- **RAM** : 16 GB minimum (8 GB pour le modèle + 8 GB pour les services)
- **CPU** : 4 cœurs minimum
- **Stockage** : 20 GB pour le modèle + 10 GB pour les données

### Optimisations

- Le modèle utilise la quantification automatique
- ChromaDB utilise SQLite pour la persistance
- Les embeddings sont mis en cache

## 🔐 Sécurité

- Aucune connexion externe requise
- Tous les services sont isolés dans Docker
- Pas de tokens ou de clés d'API exposés
- Compatible avec les politiques de sécurité d'entreprise

## 📞 Support

En cas de problème :

1. Vérifiez les logs : `docker-compose logs [service]`
2. Testez les services : `python3 test_tgi_mistral.py`
3. Consultez ce README pour le dépannage
4. Redémarrez avec : `bash deploy_mistral_local.sh` 