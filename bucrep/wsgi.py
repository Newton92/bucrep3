"""
WSGI config for bucrep project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from celery import Celery
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bucrep.settings")

application = get_wsgi_application()

app = Celery("bucrep")  # Importez votre instance Celery
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
