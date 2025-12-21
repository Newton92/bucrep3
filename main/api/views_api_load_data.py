# your_app/views.py - Version SIMPLIFIÉE pour débogage
import subprocess
import sys
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

class APILoadDataView(APIView):
    """
    Lance une commande Django depuis une API.
    Version simplifiée pour débogage - SANS permissions
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
            "notation": "import_modele_notation --clear",
            "comportementp": "import_modele_comportement_paiement --clear",
            "comportementj": "import_modele_comportement_jugement --clear",
            "forme": "import_forme_juridique --clear --dry-run",
            "poste": "import_domaines_poste_entreprise --clear --dry-run",
            "poste_real": "import_domaines_poste_entreprise --clear",
            
            # NOUVELLES COMMANDES
            "provinces_pays": "import_province_pays",
            "provinces_villes": "import_province_in_ville",
            "provinces_villes_dry": "import_province_in_ville --dry-run",
            "bail": "import_modele_bail --clear",
            "bilan": "import_modele_bilan --clear",
            "alarme": "import_modele_alarme",
            "rapport": "import_type_rapport",
            "aviscom": "import_modele_avis_commercial --clear",
            "agesoc": "import_modele_age_societe --clear",
            "statuse": "import_statut_entreprise --clear",
            "categorie": "import_categorie_entreprise --clear",
        }

        if command not in allowed_commands:
            return Response(
                {"error": f"Commande non autorisée: {command}"},
                status=status.HTTP_403_FORBIDDEN
            )

        django_command = allowed_commands[command]
        
        # DÉBOGAGE: Afficher les infos dans les logs serveur
        print(f"\n" + "="*60)
        print(f"API COMMANDE: {command} -> {django_command}")
        print(f"Python: {sys.executable}")
        print(f"Base dir: {settings.BASE_DIR}")
        print(f"CWD: {os.getcwd()}")
        print("="*60)

        try:
            # FORCER l'utilisation du Python correct
            python_exec = sys.executable
            manage_path = os.path.join(settings.BASE_DIR, 'manage.py')
            
            # Commande complète à exécuter
            full_command = f"{python_exec} {manage_path} {django_command}"
            print(f"Commande complète: {full_command}")
            
            # Exécution avec capture COMPLÈTE des logs
            process = subprocess.Popen(
                [python_exec, manage_path] + django_command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=settings.BASE_DIR,
                text=True,  # IMPORTANT: Pour avoir du texte
                encoding='utf-8',
                errors='replace'
            )

            # Timeout de 5 minutes
            try:
                out, err = process.communicate(timeout=300)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                out, err = process.communicate()
                return_code = -1
                err = err + "\n[ERREUR: Timeout après 5 minutes]"

            # DEBUG: Afficher dans les logs serveur
            print(f"\nRETOUR COMMANDE: {return_code}")
            print(f"OUTPUT (premiers 500 chars):\n{out[:500]}...")
            if err:
                print(f"ERROR:\n{err}")
            
            # Construire la réponse AVEC TOUS les logs
            response_data = {
                "status": "success" if return_code == 0 else "error",
                "return_code": return_code,
                "command": django_command,
                "full_command": full_command,
                "python_executable": python_exec,
                "output": out,
                "error": err,
                "message": f"Commande exécutée (code retour: {return_code})"
            }

            return Response(response_data)

        except Exception as e:
            # Capture complète de l'erreur
            import traceback
            error_details = traceback.format_exc()
            print(f"EXCEPTION DANS API:\n{error_details}")
            
            return Response({
                "status": "exception",
                "error": str(e),
                "traceback": error_details,
                "python_executable": sys.executable,
                "base_dir": settings.BASE_DIR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)