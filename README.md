# QRadar Ticket - Déploiement Simplifié

## 🚀 Déploiement Automatique

### Prérequis
- VirtualBox
- Vagrant

### Lancement
```bash
vagrant up
```

### Accès aux Services
- **Application Web** : http://localhost:5000
- **Interface Nginx** : http://localhost:8081
- **API Retriever** : http://localhost:5001
- **Base de données** : localhost:3307
- **TGI Mistral** : http://localhost:8080
- **ChromaDB** : http://localhost:8000

### Identifiants par défaut
- **Utilisateur** : khz
- **Mot de passe** : admin123

## 📁 Structure
```
qradar_ticket/
├── app.py                 # Application Flask principale
├── Dockerfile            # Dockerfile pour l'application web
├── requirements.txt      # Dépendances Python
├── Docker/
│   ├── docker-compose.yml # Orchestration des services
│   └── retriever/        # API Retriever
├── templates/            # Templates HTML
├── static/              # Fichiers statiques
└── Vagrantfile          # Configuration VM
```

## 🔧 Services Déployés
- **MySQL** : Base de données
- **TGI Mistral** : Modèle de langage local
- **ChromaDB** : Base de données vectorielle
- **Retriever API** : API d'analyse
- **Flask Web App** : Interface utilisateur
- **Nginx** : Proxy inverse

## 🎯 Fonctionnalités
- Analyse de payloads avec IA
- Base de données de patterns
- Interface web moderne
- API REST complète
- Modèle Mistral local 