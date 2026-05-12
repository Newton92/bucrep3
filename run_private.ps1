# ============================================================
# Serveur ESPACE PRIVÉ — localhost:8001
# Dashboard, API, login espace-privé accessibles.
# ============================================================
$env:DJANGO_PUBLIC_HOST  = "localhost:8000"
$env:DJANGO_PRIVATE_HOST = "localhost:8001"

Write-Host "=== ESPACE PRIVE === http://localhost:8001/espace-prive/se-connecter/" -ForegroundColor Green

& ".\venv\Scripts\Activate.ps1"
python manage.py runserver localhost:8001
