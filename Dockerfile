FROM python:3.11-slim

# Dépôts en HTTPS explicite
RUN echo "deb https://deb.debian.org/debian bookworm main" > /etc/apt/sources.list \
 && echo "deb https://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list \
 && echo "deb https://deb.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    default-mysql-client \
    curl \
 && rm -rf /var/lib/apt/lists/* \
 && apt-get clean

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Installer les dépendances Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copier seulement les fichiers nécessaires (pas tout le contexte)
COPY app.py .
COPY auth.py .
COPY db_config.py .
COPY logger.py .
COPY gpt_analysis.py .
COPY pattern_storage.py .
COPY parser.py .
COPY normalizer.py .

# Copier les dossiers nécessaires
COPY templates/ ./templates/
COPY static/ ./static/

# Créer le répertoire pour les photos de profil avec les bonnes permissions
RUN mkdir -p /app/profile_photos && \
    chown -R appuser:appuser /app/profile_photos && \
    chmod 755 /app/profile_photos

# Changer les permissions et propriétaire
RUN chown -R appuser:appuser /app

# Passer à l'utilisateur non-root
USER appuser

EXPOSE 5000

# Health check pour vérifier que l'application fonctionne
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

# Configuration pour écouter sur toutes les interfaces
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

CMD ["python", "app.py"]