#!/bin/sh

# python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate
# python manage.py runserver 0.0.0.0:8005
gunicorn --workers 30 bucrep.wsgi:application --bind 0.0.0.0:8000
