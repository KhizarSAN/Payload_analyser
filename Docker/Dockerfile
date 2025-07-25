# Utilise une image légère avec Python
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de l'application
COPY . .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port Flask (par défaut)
EXPOSE 5000

# Lancer l'application
CMD ["python", "app.py"]
