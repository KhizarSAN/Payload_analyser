Vagrant.configure("2") do |config|
  config.vm.box = "debian/bookworm64"
  config.vm.hostname = "qradar-debian"
  
  # Configuration réseau
  config.vm.network "forwarded_port", guest: 22, host: 2224, id: "ssh"
  config.vm.network "forwarded_port", guest: 11434, host: 11434, id: "ollama"
  config.vm.network "forwarded_port", guest: 8000, host: 8000, id: "chromadb"
  config.vm.network "forwarded_port", guest: 5000, host: 5000, id: "web"
  config.vm.network "forwarded_port", guest: 80, host: 8081, id: "nginx"
  config.vm.network "forwarded_port", guest: 3306, host: 3307, id: "mysql"
  config.vm.network "forwarded_port", guest: 5001, host: 5001, id: "retriever"
  
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "8192"  # 8GB RAM pour les modèles SOC
    vb.cpus = 4         # 4 CPU cores pour les performances
    vb.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/vagrant", "0"]
  end

  # Synchronisation optimisée
  config.vm.synced_folder ".", "/vagrant", type: "virtualbox", 
    owner: "vagrant", 
    group: "vagrant",
    exclude: [
      "models/",
      "Docker/models/",
      "**/*.bin",
      "**/*.safetensors",
      "**/*.pth",
      "**/*.pt",
      "**/*.ckpt",
      "__pycache__/",
      "**/__pycache__/",
      ".git/",
      ".vagrant/",
      "**/.git/",
      "**/.vagrant/",
      "cache/",
      "**/cache/",
      "*.log",
      "**/*.log",
      "*.db",
      "**/*.db",
      "*.sqlite",
      "**/*.sqlite",
      "*.sqlite3",
      "**/*.sqlite3",
      "venv/",
      "**/venv/",
      ".env/",
      "**/.env/",
      "*.pyc",
      "**/*.pyc",
      "patterns_data/",
      "**/patterns_data/",
      "test_*.py",
      "**/test_*.py",
      "METHODE_*.txt",
      "**/METHODE_*.txt",
      "download_*.sh",
      "download_*.ps1",
      "**/download_*.sh",
      "**/download_*.ps1",
      "*.sql",
      "**/*.sql",
      "payloadsshpublic",
      "**/payloadsshpublic",
      "*.key",
      "*.pem",
      "*.p12",
      "*.pfx",
      "**/*.key",
      "**/*.pem",
      "**/*.p12",
      "**/*.pfx",
      "*.csv",
      "*.tsv",
      "*.parquet",
      "*.json",
      "**/*.csv",
      "**/*.tsv",
      "**/*.parquet",
      "**/*.json",
      "*.md",
      "README*",
      "**/*.md",
      "**/README*",
      "*.sh",
      "*.ps1",
      "*.bat",
      "**/*.sh",
      "**/*.ps1",
      "**/*.bat",
      "*.yml",
      "*.yaml",
      "*.ini",
      "*.cfg",
      "*.conf",
      "**/*.yml",
      "**/*.yaml",
      "**/*.ini",
      "**/*.cfg",
      "**/*.conf",
      "ansible/",
      "**/ansible/",
      "static/openai_key.txt",
      "**/static/openai_key.txt"
    ]

  # Provisionnement Shell
  config.vm.provision "shell", inline: <<-SHELL
    # Mise à jour du système
    sudo apt-get update
    
    # Installation des packages nécessaires
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release python3-pip git
    
    # Ajout de la clé GPG Docker
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Ajout du repository Docker
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Installation de Docker
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Ajout de l'utilisateur vagrant au groupe docker
    sudo usermod -aG docker vagrant
    
    # Démarrage du service Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Installation de docker-compose via pip (fallback)
    sudo pip3 install docker-compose
    
    # Configuration des permissions sur /vagrant
    sudo chown -R vagrant:vagrant /vagrant
    
    # Lancement des containers Docker
    cd /vagrant/Docker
    sudo docker compose up -d --build
    
    # Attendre que les services soient prêts
    echo "⏳ Attente que les services Docker soient prêts..."
    sleep 120
    
    # Installer les dépendances Python pour l'initialisation
    echo "🐍 Installation des dépendances Python..."
    cd /vagrant
    
    # Installer python3-venv et default-mysql-client
    sudo apt-get install -y python3-venv default-mysql-client python3-full
    
    # Attendre que les containers Docker soient prêts
    echo "⏳ Attente que les containers Docker soient prêts..."
    for i in {1..60}; do
        if docker ps | grep -q "mysql_payload.*Up"; then
            echo "✅ Container MySQL est démarré"
            break
        fi
        echo "⏳ Tentative $i/60 - Container MySQL pas encore prêt..."
        sleep 10
    done
    
    # Attendre que MySQL soit prêt dans le container
    echo "⏳ Attente que MySQL soit prêt dans le container..."
    for i in {1..30}; do
        if docker exec mysql_payload mysqladmin ping -h localhost -u root -proot >/dev/null 2>&1; then
            echo "✅ MySQL est prêt"
            break
        fi
        echo "⏳ Tentative $i/30 - MySQL pas encore prêt..."
        sleep 10
    done
    
    # Créer un environnement virtuel pour éviter les conflits
    echo "🔧 Création de l'environnement virtuel..."
    python3 -m venv /tmp/venv_init
    source /tmp/venv_init/bin/activate
    
    # Installer les dépendances
    echo "📦 Installation des dépendances Python..."
    pip install --upgrade pip
    pip install sqlalchemy pymysql flask requests pillow cryptography
    
    # Exécuter le fichier SQL pour créer les tables
    echo "🗃️ Création des tables de la base de données..."
    docker exec -i mysql_payload mysql -u root -proot payload_analyser < payload_analyser.sql
    
    # Initialiser la base de données et créer l'utilisateur admin
    echo "🗄️ Initialisation de la base de données..."
    # Définir les variables d'environnement pour la connexion au container MySQL
    export DB_HOST=localhost
    export DB_USER=root
    export DB_PASSWORD=root
    export DB_NAME=payload_analyser
    python3 init_db.py
    
    # Nettoyer l'environnement virtuel
    deactivate
    rm -rf /tmp/venv_init
    
    # Vérifier que tout fonctionne
    echo "🔍 Vérification des services..."
    sleep 10
    
    # Tester l'application web
    if curl -s http://localhost:5000/ > /dev/null; then
        echo "✅ Application web accessible"
    else
        echo "⚠️ Application web pas encore prête"
    fi
    
    # Tester Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        echo "✅ Ollama accessible"
    else
        echo "⚠️ Ollama pas encore prêt (modèles à télécharger)"
    fi
    
    # Tester ChromaDB
    if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
        echo "✅ ChromaDB accessible"
    else
        echo "⚠️ ChromaDB pas encore prêt"
    fi
    
    echo "🎉 Déploiement terminé !"
    echo "📱 Application Web: http://localhost:5000"
    echo "🌐 Interface Nginx: http://localhost:8081"
    echo "🤖 API Retriever: http://localhost:5001"
    echo "🗄️ Base de données: localhost:3307"
    echo "🧠 Ollama SOC: http://localhost:11434"
    echo "📊 ChromaDB: http://localhost:8000"
    echo ""
    echo "💡 Pour installer les modèles SOC optimisés:"
    echo "   cd /vagrant && chmod +x setup_soc_models.sh && ./setup_soc_models.sh"
  SHELL
end