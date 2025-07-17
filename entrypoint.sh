#!/bin/sh

# python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate
# python manage.py runserver 0.0.0.0:8005
python manage.py collectstatic --noinput
gunicorn bucrep.wsgi:application --bind 0.0.0.0:8000
