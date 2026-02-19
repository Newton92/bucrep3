# Procédure de mise à jour et de redémarrage de l’application BUCREP V3 EN PROPRODUCTION

Ce document décri la procedure standard à suivre pour mettre à jour, migrer et redémarrer l’application Django **BUCREP V3** sur le serveur de preproduction.

# Acces
Serveur IP : 107.172.88.238 
Port : 8014
Login : yannick
Mot de passe : ****** 
Tesla : 1651221@$Ng

---

## Prérequis

- Accès SSH au serveur
- Python et virtualenv correctement installés
- Gunicorn installé et fonctionnel
- Droits suffisants pour arrêter et démarrer les services

---

## Étapes de mise à jour

### 1. Mise à jour du code source

Se positionner dans le répertoire du projet et récupérer les dernières modifications depuis le dépôt Git :
- cd /var/www/html/bucrepapi

```bash
git pull
```

---

### 2. Activation de l’environnement virtuel

Activer l’environnement virtuel afin d’utiliser les dépendances du projet :

```bash
source /venv/bin/activate
```

---

### 3. Gestion des migrations (si applicable)

⚠️ Cette étape est **obligatoire uniquement en cas de modification des modèles Django**.

Générer les fichiers de migration :

```bash
python manage.py makemigrations
```

Appliquer les migrations à la base de données :

```bash
python manage.py migrate
```

---

### 4. Redémarrage de Gunicorn

Arrêter tous les processus Gunicorn en cours d’exécution :

```bash
killall gunicorn
```

Redémarrer Gunicorn avec la configuration définie pour l’application :

```bash
gunicorn --workers 4 --bind 0.0.0.0:8014 bucrep.wsgi:application --daemon
```

---

## Vérification

Si aucune erreur n’est retournée par les commandes précédentes, l’application est opérationnelle et accessible à l’adresse suivante :

👉 **http://107.172.88.238/**

---

## Notes complémentaires

- En cas d’erreur, vérifier les logs Gunicorn et Django
- Toujours s’assurer que l’environnement virtuel est activé avant toute commande Django
- Ne pas lancer plusieurs instances Gunicorn simultanément sur le même port

---

## Auteur

Documentation technique – **PELBA**

[ #fcfefe, #0a95ca, #0d80be, #25add6, #106cb2 ]
[ cd /var/www/html/bucrepapi ]
[ ./deploy.sh ]
[ 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 ]
[ 107.172.88.238 - 1651221@$Ng - yannick ]
[ git remote set-url origin git@github.com:yannickaboh/bucrep-api.git ]

[ python manage.py import_clients_list --default-password "VotreMotDePasseFort!2026" --update-existing]

python manage.py seed_solvabilite_gabon --code GAB-SOLV-TEST
python manage.py seed_solvabilite_gabon --code GAB-SOLV-TEST --with-commande --force-reset
python manage.py seed_solvabilite_cote_divoire --code CIV-SOLV-TEST --with-commande --force-reset
python manage.py seed_solvabilite_south_africa --code ZA-SOLV-TEST --with-commande --force-reset




Genere moi un management command seed_solvabilite_cote_divoire --code CIV-SOLV-TEST --with-commande --force-reset
Nom acheteur (African Distribution Company) | 
Pays : Cote d'ivoire | 
Recuperer informations dans pdf que j'ai fourni precedemment, le reste des infos tu les genere


Genere moi un management command seed_solvabilite_south_africa --code ZA-SOLV-TEST --with-commande --force-reset
Nom acheteur (Aquatan Proprietary Limited) | 
Pays : Afrique du sud ou South Africa | Bilan Anglais (a mon avis)
Recuperer informations dans pdf que j'ai fourni precedemment, le reste des infos tu les genere