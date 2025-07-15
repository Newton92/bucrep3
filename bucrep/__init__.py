# from __future__ import absolute_import, unicode_literals

__all__ = ("bucrep",)


# Lancez les processus. Vous aurez besoin de deux terminaux distincts (en plus de votre runserver).
# Terminal 1 : Le "Worker" (celui qui exécute les tâches)
# celery -A bucrep worker -l info

# Terminal 2 : Le "Beat" (celui qui planifie les tâches)
# celery -A bucrep beat -l info
