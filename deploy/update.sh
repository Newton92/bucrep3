#!/bin/bash
# ===========================================================================
# BUCREP — Mise à jour du code (après git push)
# Exécuter depuis le serveur à chaque nouvelle version
# ===========================================================================
set -e

APP_DIR="/app/bucrep3"

echo "→ Pull du code..."
cd "$APP_DIR"
git pull origin main

echo "→ Dépendances Python..."
"$APP_DIR/venv/bin/pip" install -r requirements.txt -q

echo "→ Migrations..."
"$APP_DIR/venv/bin/python" manage.py migrate --noinput

echo "→ Fichiers statiques..."
"$APP_DIR/venv/bin/python" manage.py collectstatic --noinput

echo "→ Redémarrage Gunicorn..."
systemctl restart gunicorn

echo "→ Rechargement Apache2..."
systemctl reload apache2

echo ""
echo "Mise à jour terminée !"
systemctl status gunicorn --no-pager --lines=5
