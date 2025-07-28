FROM python:3.11-slim

# Dépôts en HTTPS explicite
RUN echo "deb https://deb.debian.org/debian bookworm main" > /etc/apt/sources.list \
 && echo "deb https://deb.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list \
 && echo "deb https://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list \
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

# Copier le code source
COPY . .

# Créer le répertoire pour les photos de profil avec les bonnes permissions
RUN mkdir -p /app/profile_photos && \
    chown -R appuser:appuser /app/profile_photos && \
    chmod 755 /app/profile_photos

# Vérifier les permissions au démarrage
COPY check_permissions.py /app/
RUN chmod +x /app/check_permissions.py

# Changer les permissions et propriétaire
RUN chown -R appuser:appuser /app

# Passer à l'utilisateur non-root
USER appuser

EXPOSE 5000

# Health check pour vérifier que l'application fonctionne
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

CMD ["python", "app.py"]