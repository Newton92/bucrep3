# Importation de modules pour la compatibilité avec les versions futures de Python

# Importation du module os pour interagir avec le système d'exploitation
import os

# Importation de Celery pour la gestion des tâches asynchrones
from celery import Celery

# Importation de crontab pour la planification des tâches périodiques

# Définit le module de configuration de Django par défaut pour le programme 'celery'.
# Cela permet à Celery de savoir où trouver les paramètres de configuration de Django.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bucrep.settings")

# Crée une instance de Celery avec le nom 'bucrep'.
# Cette instance sera utilisée pour configurer et exécuter les tâches Celery.
app = Celery("bucrep")

# Configuration des tâches périodiques
# beat_schedule est un dictionnaire qui définit les tâches périodiques à exécuter.
# app.conf.beat_schedule = {}

# Charge les paramètres de configuration à partir du fichier settings.py
# Cela permet à Celery de lire les paramètres de configuration de Django.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-découverte des tâches définies dans l'app Django
# Cela permet à Celery de découvrir automatiquement les tâches définies dans les applications Django.
app.autodiscover_tasks()


# Définition d'une tâche de débogage
@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


# Pour démarrer Redis, vous pouvez utiliser la commande suivante dans votre terminal :
# Lancer le broker (par exemple, Redis : redis-server)
# redis-server

# Pour démarrer Celery, vous pouvez utiliser la commande suivante dans votre terminal :
# celery -A myproject worker --loglevel=info
# celery -A bucrep worker --loglevel=info

# Pour démarrer le beat scheduler de Celery, utilisez la commande suivante :
# celery -A myproject beat --loglevel=info

# celery -A votre_projet beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
# celery -A bucrep beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Acces aux taches
# http://localhost:8004/admin/django_celery_beat/
