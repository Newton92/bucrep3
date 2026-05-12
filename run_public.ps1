# ============================================================
# Serveur VITRINE PUBLIQUE — localhost:8000
# Seules les pages marketing sont accessibles.
# Les routes /espace-prive/, /root-dashboard/, /api/ → 404
# ============================================================
$env:DJANGO_PUBLIC_HOST  = "localhost:8000"
$env:DJANGO_PRIVATE_HOST = "localhost:8001"

Write-Host "=== VITRINE PUBLIQUE === http://localhost:8000/" -ForegroundColor Cyan

& ".\venv\Scripts\Activate.ps1"
python manage.py runserver localhost:8000
