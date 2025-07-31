Vagrant.configure("2") do |config|
  config.vm.box = "debian/bookworm64"
  config.vm.hostname = "qradar-debian"
  
  # Configuration réseau ultra-simple sans réseau privé
  # Seulement les ports forwards pour éviter les conflits DHCP
  config.vm.network "forwarded_port", guest: 22, host: 2223, id: "ssh"
  config.vm.network "forwarded_port", guest: 8080, host: 8080, id: "tgi"
  config.vm.network "forwarded_port", guest: 8000, host: 8000, id: "chromadb"
  config.vm.network "forwarded_port", guest: 5000, host: 5000, id: "web"
  config.vm.network "forwarded_port", guest: 80, host: 8081, id: "nginx"
  config.vm.network "forwarded_port", guest: 3306, host: 3307, id: "mysql"
  config.vm.network "forwarded_port", guest: 5001, host: 5001, id: "retriever"
  
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "4096"
    vb.cpus = 2
    # Désactiver les symlinks pour éviter l'avertissement
    vb.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/vagrant", "0"]
  end

  # Synchronise tout le projet dans /vagrant avec les bonnes permissions
  config.vm.synced_folder ".", "/vagrant", type: "virtualbox", owner: "vagrant", group: "vagrant"

  # Provisionnement Shell au lieu d'Ansible (plus simple sur Windows)
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
  SHELL
end