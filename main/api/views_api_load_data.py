import subprocess
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from rest_framework.permissions import BasePermission

class IsAdminOrHasPermission(BasePermission):
    """
    Permission personnalisée pour les imports
    """
    def has_permission(self, request, view):
        # Vérifie si l'utilisateur est admin
        if request.user.is_superuser:
            return True
        
        # Vérifie les permissions spécifiques
        allowed_commands = request.query_params.get('cmd', '')
        if allowed_commands in ['provinces_pays', 'provinces_villes', 'provinces_complet']:
            # Nécessite une permission spécifique
            return request.user.has_perm('your_app.can_import_geographic_data')
        
        return request.user.has_perm('your_app.can_import_data')

# Appliquer à la vue
from rest_framework.permissions import IsAuthenticated

class APILoadDataView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrHasPermission]
    """
    Lance une commande Django depuis une API.
    Ex : import_nace_simple, import_modele_notation_simple, etc.
    """

    def get(self, request, *args, **kwargs):
        command = request.query_params.get("cmd")

        if not command:
            return Response(
                {"error": "Paramètre 'cmd' requis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Liste blanche des commandes autorisées
        allowed_commands = {
            "nace": "import_nace_simple",
            "notation": "import_modele_notation_simple",
            "comportement": "import_modele_comportement_paiement --clear",
            "forme": "import_forme_juridique --clear --dry-run",
            "poste": "import_domaines_poste_entreprise --clear --dry-run",
            "poste_real": "import_domaines_poste_entreprise --clear",  # ← SANS dry-run
            
            # NOUVELLES COMMANDES POUR LES PROVINCES
            "provinces_pays": "import_province_pays",
            "provinces_villes": "import_province_in_ville",
            "provinces_villes_dry": "import_province_in_ville --dry-run",  # Mode test
        }

        if command not in allowed_commands:
            return Response(
                {"error": "Commande non autorisée"},
                status=status.HTTP_403_FORBIDDEN
            )

        django_command = allowed_commands[command]

        try:
            process = subprocess.Popen(
                ['python', 'manage.py', django_command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=settings.BASE_DIR
            )

            out, err = process.communicate()

            return Response({
                "status": "success",
                "message": f"Commande '{django_command}' exécutée.",
                "output": out.decode(),
                "error": err.decode()
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
