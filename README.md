# Deploiment
`docker compose up --build -d`

# Arreter le système
`docker compose stop`

# Démarrage
`docker compose start`

# Arreter et écraser
`docker compose down`

# Modificiations faites
- j'ai dû supprimer le contenu du dossier main/migrations et relancer les migrations car il manquait un fichier de migration.
- ajout dossier `db`: qui contient le script de la base de données mises à jour (08-12-2025).
- modification bucrep/settings.py :
    1. configuration pour postgres
    2. désactiver les cookies et csrf sécurisés car le sous domaine n'est pas en HTTPS. Donc quand vous aurez les certificats
    et que vous aurez configuré apache2 avec, faudra remettre ces paramètres à true.
    3. Ajouter le domaine dans allowed hosts.

```
    # pip install psycopg2-binary
    DATABASES = {
        'default': {
             'ENGINE': 'django.db.backends.postgresql',
             'NAME': 'bucrep',  # Nom de votre base de données PostgreSQL
             'USER': 'bucrep',  # Nom d'utilisateur de la base de données PostgreSQL
             'PASSWORD': 'bucrep',  # Mot de passe de la base de données PostgreSQL
             'HOST': '172.17.0.1',  # Adresse de l'hôte de la base de données PostgreSQL
             'PORT': '5433',  # Port de la base de données PostgreSQL (par défaut 5432)
         }
     }


...
    if not DEBUG:
        SECURE_HSTS_SECONDS = 3600
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        SECURE_HSTS_PRELOAD = True
        SECURE_SSL_REDIRECT = False # True
        SESSION_COOKIE_SECURE = False # True
        CSRF_COOKIE_SECURE = False # True
        X_FRAME_OPTIONS = 'DENY'

...
    # Cookies sécurisés
    SESSION_COOKIE_SECURE = False # True
    CSRF_COOKIE_SECURE = False # True
    SESSION_COOKIE_HTTPONLY = False # True
    CSRF_COOKIE_HTTPONLY = False # True
    SECURE_BROWSER_XSS_FILTER = False # True
    SECURE_CONTENT_TYPE_NOSNIFF = False # True 

    CSRF_TRUSTED_ORIGINS = [
        'http://preprod.bucrep3.bucrep.net'
    ]

``` 

- modifications dans .env
```
    DJANGO_DEBUG=False
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,10.0.57.47,3.236.213.114,93.127.202.151,http://preprod.bucrep3.bucrep.net
```


python manage.py seed_fake_acheteur_reporting --code FAKE-RPT-DEMO --years 2025,2024,2023 --with-commande
