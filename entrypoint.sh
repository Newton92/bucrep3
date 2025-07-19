#!/bin/sh

# python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate
# python manage.py runserver 0.0.0.0:8005
python manage.py collectstatic --noinput

# echo "[+] Creating superuser if it doesn't exist..."

# python manage.py shell <<EOF
# from django.contrib.auth import get_user_model
# User = get_user_model()

# username = "admin_bucrep"
# email = "yannickabohthierry@gmail.com"
# password = "admin@bucrep"
# role = "Root"

# if not User.objects.filter(username=username).exists():
#     User.objects.create_superuser(username=username, email=email, password=password, role=role)
#     print("✅ Superuser created.")
# else:
#     print("ℹ️ Superuser already exists.")
# EOF

gunicorn bucrep.wsgi:application --bind 0.0.0.0:8000
