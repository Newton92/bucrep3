import os

import django
from celery import Celery

# Configurez l'environnement Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bucrep.settings")
django.setup()

# Créez une instance de Celery
app = Celery("bucrep")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Appelez la tâche
from main.tasks import test_email_task

test_email_task.delay()
