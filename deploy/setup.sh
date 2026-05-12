#!/bin/bash
# ===========================================================================
# BUCREP — Script de déploiement sans Docker
# Serveur : Ubuntu 22.04 / Debian 12
# À exécuter en tant que root ou avec sudo
# ===========================================================================
set -e

APP_DIR="/app/bucrep3"
APP_USER="www-data"
PYTHON="python3.12"

echo "========================================"
echo "  BUCREP — Installation / Mise à jour  "
echo "========================================"

# ---------------------------------------------------------------------------
# 1. Dépendances système
# ---------------------------------------------------------------------------
echo "[1/8] Installation des dépendances système..."
apt-get update -q
apt-get install -y -q \
    python3.12 python3.12-venv python3.12-dev \
    libpq-dev gcc g++ make \
    postgresql postgresql-client \
    redis-server \
    apache2 \
    libapache2-mod-proxy-html \
    certbot python3-certbot-apache \
    gettext \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev shared-mime-info \
    fonts-liberation fonts-dejavu \
    curl git

# ---------------------------------------------------------------------------
# 2. Cloner ou mettre à jour le code
# ---------------------------------------------------------------------------
echo "[2/8] Clonage / mise à jour du code..."
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git pull origin main
else
    mkdir -p /app
    git clone https://github.com/Newton92/bucrep3.git "$APP_DIR"
    cd "$APP_DIR"
fi

# ---------------------------------------------------------------------------
# 3. Environnement Python
# ---------------------------------------------------------------------------
echo "[3/8] Environnement Python..."
if [ ! -d "$APP_DIR/venv" ]; then
    $PYTHON -m venv "$APP_DIR/venv"
fi
"$APP_DIR/venv/bin/pip" install --upgrade pip -q
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q
"$APP_DIR/venv/bin/pip" install gunicorn -q

# ---------------------------------------------------------------------------
# 4. Fichier .env (à créer manuellement si absent)
# ---------------------------------------------------------------------------
echo "[4/8] Vérification du fichier .env..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo ""
    echo "⚠  IMPORTANT : éditez $APP_DIR/.env avec vos vraies valeurs !"
    echo "   nano $APP_DIR/.env"
    echo "   Puis relancez ce script."
    echo ""
    exit 1
fi

# ---------------------------------------------------------------------------
# 5. Base de données PostgreSQL
# ---------------------------------------------------------------------------
echo "[5/8] Configuration PostgreSQL..."
source "$APP_DIR/.env"

# Créer user + DB si inexistants
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='$LOCAL_DB_USER'" \
    | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER $LOCAL_DB_USER WITH PASSWORD '$LOCAL_DB_PASS';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='$LOCAL_DB_NAME'" \
    | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE $LOCAL_DB_NAME OWNER $LOCAL_DB_USER;"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $LOCAL_DB_NAME TO $LOCAL_DB_USER;"

# ---------------------------------------------------------------------------
# 6. Django : migrations, static, .mo
# ---------------------------------------------------------------------------
echo "[6/8] Migrations et fichiers statiques..."
cd "$APP_DIR"
"$APP_DIR/venv/bin/python" manage.py migrate --noinput
"$APP_DIR/venv/bin/python" manage.py collectstatic --noinput

# Permissions
mkdir -p /var/log/gunicorn
chown -R $APP_USER:$APP_USER "$APP_DIR" /var/log/gunicorn

# ---------------------------------------------------------------------------
# 7. Service Gunicorn (systemd)
# ---------------------------------------------------------------------------
echo "[7/8] Installation du service Gunicorn..."
cp "$APP_DIR/deploy/gunicorn.service" /etc/systemd/system/gunicorn.service
systemctl daemon-reload
systemctl enable gunicorn
systemctl restart gunicorn
systemctl status gunicorn --no-pager

# ---------------------------------------------------------------------------
# 8. Apache2
# ---------------------------------------------------------------------------
echo "[8/8] Configuration Apache2..."
a2enmod proxy proxy_http headers rewrite ssl expires

cp "$APP_DIR/apache2/bucrep.net.conf"             /etc/apache2/sites-available/
cp "$APP_DIR/apache2/application.bucrep.net.conf" /etc/apache2/sites-available/
a2ensite bucrep.net.conf
a2ensite application.bucrep.net.conf
a2dissite 000-default.conf 2>/dev/null || true

apache2ctl configtest
systemctl reload apache2

echo ""
echo "========================================"
echo "  Installation terminée !"
echo ""
echo "  Prochaine étape : obtenir le SSL"
echo "  Voir deploy/ssl.sh"
echo "========================================"
