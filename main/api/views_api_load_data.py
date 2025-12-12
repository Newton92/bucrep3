import subprocess
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

class APILoadDataView(APIView):
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
            "comportement": "import_modele_comportement_paiement",
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
