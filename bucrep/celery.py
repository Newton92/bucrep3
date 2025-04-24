# import os
# from __future__ import *
# from celery import Celery
# from celery.schedules import crontab

# Définit le module de configuration de Django
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bucrep.settings')

# Crée une instance de Celery
# app = Celery('bucrep')

# Schedule 
# app.conf.beat_schedule = {
    # 'check-emails-every-10-minutes': {
        # 'task': 'main.tasks.check_new_emails',
        # 'schedule': crontab(minute='*/10'),  # Toutes les 10 minutes
    # },
# }

# Charge les paramètres de configuration à partir du fichier settings.py
# app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-découverte des tâches définies dans l'app Django
# app.autodiscover_tasks()

# @app.task(bind=True)
# def debug_task(self):
    # print(f'Request: {self.request!r}')
