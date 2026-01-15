Bon, vous avez bien cloné votre projet Django sur le serveur. Maintenant, vous devez suivre les étapes pour le déployer correctement. Voici la procédure complète à suivre :

## 1. **Mise à jour du système et installation des dépendances**

```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y
sudo reboot  # Redémarrer si nécessaire (comme indiqué dans le message)

# Installer les dépendances système
sudo apt install -y python3-pip python3-venv nginx postgresql postgresql-contrib
```

## 2. **Configurer l'environnement virtuel**

```bash
cd /var/www/html/bucrepapi

# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances Python
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. **Configurer la base de données PostgreSQL**

```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Dans psql, créer la base de données et l'utilisateur
CREATE DATABASE bucrepdb;
CREATE USER bucrepuser WITH PASSWORD 'bucrepapi';
ALTER ROLE bucrepuser SET client_encoding TO 'utf8';
ALTER ROLE bucrepuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE bucrepuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE bucrepdb TO bucrepuser;
\q
```

## 4. **Configurer les variables d'environnement**

```bash
# Créer un fichier .env dans le projet
nano /var/www/html/bucrepapi/.env
```

Ajoutez ces variables (adaptez-les à votre configuration) :
```
DEBUG=False
SECRET_KEY=votre_clé_secrète_django
DATABASE_URL=postgres://bucrepuser:votre_mot_de_passe_complexe@localhost/bucrepdb
ALLOWED_HOSTS=107.172.88.238,localhost,127.0.0.1
```

## 5. **Configurer les paramètres Django pour la production**

Vérifiez votre `settings.py` :
- `DEBUG = False`
- Configurer `ALLOWED_HOSTS`
- Configurer les fichiers statiques
- Configurer la base de données PostgreSQL

## 6. **Appliquer les migrations et collecter les fichiers statiques**

```bash
source venv/bin/activate

# Activer l'environnement virtuel (si pas déjà fait)
source venv/bin/activate

# Installer django-model-changes
pip install django-model-changes

# Ou installer toutes les dépendances depuis requirements.txt
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
```

## 7. **Tester Gunicorn**

```bash
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 bucrep.wsgi:application
```

Testez avec `curl http://localhost:8000` ou dans un autre terminal.

## 8. **Créer un service systemd pour Gunicorn**

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Contenu :
```ini
[Unit]
Description=gunicorn daemon for bucrep
After=network.target

[Service]
User=yannick
Group=www-data
WorkingDirectory=/var/www/html/bucrepapi
ExecStart=/var/www/html/bucrepapi/venv/bin/gunicorn --workers 3 --bind unix:/var/www/html/bucrepapi/bucrep.sock bucrep.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

## 9. **Configurer Nginx**

```bash
sudo nano /etc/nginx/sites-available/bucrep
```

Contenu :
```nginx
server {
    listen 80;
    server_name 107.172.88.238;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/html/bucrepapi;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/html/bucrepapi/bucrep.sock;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/bucrep /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 10. **Ouvrir les ports firewall**

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

## 11. **Tester l'application**

Accédez à `http://107.172.88.238/` depuis votre navigateur.

## 12. **Procédure de mise à jour future**

Une fois tout configuré, voici la procédure simplifiée pour les mises à jour :

```bash
cd /var/www/html/bucrepapi
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

## Points d'attention :

1. **Sécurité** : Régénérez un `SECRET_KEY` et ne le commitez pas
2. **Base de données** : Sauvegardez vos données avant les migrations
3. **Logs** : Consultez les logs en cas d'erreur :
   ```bash
   sudo journalctl -u gunicorn
   sudo tail -f /var/log/nginx/error.log
   ```

Commencez par l'étape 1 et avancez progressivement. Testez à chaque étape avant de passer à la suivante.