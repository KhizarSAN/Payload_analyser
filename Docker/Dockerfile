# Utilise une image légère avec Python
FROM python:3.11-slim

# Installer les dépendances système nécessaires à mysqlclient
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du projet
COPY . .

# Exposer le port de l'application (si Flask)
EXPOSE 5000

# Lancer l'app avec le script de démarrage
CMD ["python", "app.py"]
