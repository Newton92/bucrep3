import subprocess
import os
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from django.http import StreamingHttpResponse
import subprocess
import os
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


# --- Fonction Utilitaires pour le Streaming ---

def get_db_credentials():
    """Récupère les infos de la BD à partir des settings."""
    DB_CONFIG = settings.DATABASES['default']
    return {
        'DB_NAME': DB_CONFIG.get('NAME'),
        'DB_USER': DB_CONFIG.get('USER'),
        'DB_PASS': DB_CONFIG.get('PASSWORD'),
        'DB_HOST': DB_CONFIG.get('HOST', 'localhost'),
        'DB_PORT': DB_CONFIG.get('PORT', '5432'),
    }

def stream_pg_dump(db_info, timeout=300):
    """Exécute pg_dump et renvoie le flux binaire (bytes) de la sortie."""
    
    command = [
        'pg_dump',
        '-h', db_info['DB_HOST'],
        '-p', db_info['DB_PORT'],
        '-U', db_info['DB_USER'],
        '-Fc', # Utiliser le format binaire pour plus d'efficacité
        db_info['DB_NAME']
    ]

    env = os.environ.copy()
    env['PGPASSWORD'] = db_info['DB_PASS']
    
    try:
        # Popen permet l'exécution asynchrone pour le streaming
        process = subprocess.Popen(
            command,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # Tant qu'il y a des données ou que le processus est actif, on lit
        for chunk in iter(lambda: process.stdout.read(4096), b''):
            if chunk:
                yield chunk
            
        # Vérification du code de retour après que le stream soit terminé
        process.wait(timeout=timeout)
        if process.returncode != 0:
            error = process.stderr.read().decode()
            raise Exception(f"Erreur lors de pg_dump: {error}")

    except Exception as e:
        # Ici, vous pouvez logguer l'erreur
        print(f"Erreur de sauvegarde: {e}")
        # Optionnel: Renvoie un message d'erreur clair dans le flux si possible
        yield str(e).encode('utf-8')
        
        
        


# Recuperer les mails ici !
# Exécuter la récupération des emails en tâche de fond
def run_fetch_emails():
    try:
        fetch_and_save_emails()
    except Exception as e:
        print(f"Erreur lors de la récupération des emails : {e}")

    threading.Thread(target=run_fetch_emails, daemon=True).start()
    
    

# Fonction simplifiée pour lire le contenu du dump au fur et à mesure
def lire_le_dump_en_stream(command, env):
    proc = subprocess.Popen(
        command,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    # Yield le contenu par morceaux (chunks)
    for line in proc.stdout:
        yield line
    
    # Gérer la fin du processus
    proc.wait(timeout=300) # Assurez-vous d'avoir un timeout ici aussi

# --- FONCTION DE SÉCURITÉ ---
def est_super_utilisateur(user):
    """Vérifie si l'utilisateur est connecté et est un super-utilisateur."""
    return user.is_authenticated and user.is_superuser

@user_passes_test(est_super_utilisateur)
def telecharger_donnees_postgres_sql_texte(request):
    """
    Exécute pg_dump pour exporter la base de données en SQL brut (texte).
    """
    # 1. Récupération des informations de connexion
    DB_CONFIG = settings.DATABASES['default']
    DB_NAME = DB_CONFIG.get('NAME')
    DB_USER = DB_CONFIG.get('USER')
    DB_PASS = DB_CONFIG.get('PASSWORD')
    DB_HOST = DB_CONFIG.get('HOST', 'localhost')
    DB_PORT = DB_CONFIG.get('PORT', '5432')

    if not all([DB_NAME, DB_USER, DB_PASS]):
        return HttpResponse("Erreur : Les informations de connexion à la base de données sont incomplètes.", status=500)

    # 2. Définir la commande pg_dump (SANS option de format pour obtenir du SQL texte)
    # Options : -h (hôte), -p (port), -U (utilisateur)
    command = [
        'pg_dump',
        '-h', DB_HOST,
        '-p', DB_PORT,
        '-U', DB_USER,
        DB_NAME  # Nom de la base de données en dernier
    ]

    # 3. Préparer l'environnement pour le mot de passe
    env = os.environ.copy()
    env['PGPASSWORD'] = DB_PASS

    try:
        # 4. Exécuter la commande shell
        process = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,  # Important pour capturer du texte (SQL brut)
            check=True, 
            timeout=300
        )
        
        sql_content = process.stdout
        
    except subprocess.CalledProcessError as e:
        return HttpResponse(f"Erreur pg_dump : {e.stderr}", status=500)
    except FileNotFoundError:
        return HttpResponse("Erreur : La commande 'pg_dump' n'a pas été trouvée. Assurez-vous que PostgreSQL bin est dans le PATH.", status=500)
    except Exception as e:
        return HttpResponse(f"Erreur inattendue : {e}", status=500)
    
    # 5. Créer la réponse HTTP avec le type de contenu TEXTE
    # response = HttpResponse(sql_content, content_type='text/plain')
    # 5. Créer la réponse HTTP en streaming
    response = StreamingHttpResponse(
        lire_le_dump_en_stream(command, env),
        content_type='text/plain'
    )
    
    # Nommer le fichier avec une extension .sql
    filename = f"sauvegarde_{DB_NAME}.sql"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
    
    


# --- La Vue DRF ---

class DatabaseDumpAPIView(APIView):
    # 1. Utiliser les permissions DRF (seuls les administrateurs peuvent y accéder)
    # permission_classes = [IsAdminUser] 
    permission_classes = [IsAuthenticated] # Vous pouvez ajuster cela selon vos besoins (ex: AllowAny pour tout le monde)

    
    def get(self, request, *args, **kwargs):
        """Déclenche le dump de la base de données et le renvoie en streaming."""
        
        db_info = get_db_credentials()
        db_name = db_info['DB_NAME']
        
        # 2. Créer le StreamingHttpResponse
        response = StreamingHttpResponse(
            stream_pg_dump(db_info, timeout=600), # Timeout augmenté à 10 minutes
            content_type='application/octet-stream' # Type binaire
        )
        
        # 3. Headers pour forcer le téléchargement du fichier
        filename = f"sauvegarde_{db_name}_{os.times()[4]}.dump" # ajout d'un timestamp pour l'unicité
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response