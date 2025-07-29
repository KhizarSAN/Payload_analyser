FROM python:3.10-slim

# Configuration des dépôts HTTPS pour réseau d'entreprise
RUN echo "deb https://deb.debian.org/debian bookworm main" > /etc/apt/sources.list \
 && echo "deb https://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list \
 && echo "deb https://deb.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends --fix-missing \
    curl \
    gcc \
    g++ \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Créer le dossier de données
RUN mkdir -p /data

# Exposer le port
EXPOSE 5000

# Lancer FastAPI via Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"] 