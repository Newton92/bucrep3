# middleware.py
import json
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.cache import cache
from django.http import Http404, HttpResponseRedirect
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Chemins réservés à l'espace privé (inaccessibles depuis le site public)
# ---------------------------------------------------------------------------
_PRIVATE_PREFIXES = (
    '/espace-prive/',
    '/root-dashboard/',
    '/api/',
    '/login/',
    '/verification/',
    '/mot-de-passe-oublie/',
    '/reinitialisation-mot-de-passe-oublie/',
    '/generate-admin/',
    '/report-modele/',
    '/report-template/',
    '/admin/',
    '/swagger/',
    '/redoc/',
)


class SiteSegregationMiddleware:
    """
    Sépare le site public (vitrine) de l'espace privé (dashboard / API).

    En développement :
      - localhost:8000  → vitrine uniquement  (DJANGO_PUBLIC_HOST)
      - localhost:8001  → espace privé complet (DJANGO_PRIVATE_HOST)

    En production :
      - www.bucrep.net  → vitrine uniquement
      - app.bucrep.net  → espace privé

    Les chemins privés retournent 404 quand ils sont accédés depuis le
    domaine public — sans révéler qu'ils existent.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()          # ex. "localhost:8000"
        path = request.path_info           # ex. "/espace-prive/se-connecter/"

        public_host  = getattr(settings, 'PUBLIC_HOST',  'localhost:8000')
        private_host = getattr(settings, 'PRIVATE_HOST', 'localhost:8001')

        is_on_public_host  = host == public_host
        is_on_private_host = host == private_host

        # En mode DEBUG avec un seul hôte on n'applique la règle
        # que si les deux hôtes sont effectivement distincts.
        if public_host == private_host:
            return self.get_response(request)

        is_private_path = path.startswith(_PRIVATE_PREFIXES)

        if is_on_public_host and is_private_path:
            raise Http404

        if is_on_private_host and path == '/':
            return HttpResponseRedirect('/login/')

        return self.get_response(request)

class JWTRefreshMiddleware(MiddlewareMixin):
    """
    Middleware pour gérer le rafraîchissement automatique des tokens JWT expirés
    """
    
    def process_request(self, request):
        """
        Intercepte les requêtes API pour vérifier les tokens
        """
        # Ne traiter que les requêtes API
        if not request.path.startswith('/api/'):
            return None
            
        # Vérifier si l'Authorization header est présent
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None
            
        # Extraire le token
        token = auth_header.split(' ')[1]
        
        try:
            # Vérifier si le token est valide
            access_token = AccessToken(token)
            request.user_id = access_token['user_id']
            
        except TokenError as e:
            # Token invalide ou expiré
            if 'expired' in str(e).lower():
                # Marquer la requête comme ayant un token expiré
                request.token_expired = True
                request.original_token = token
            return None
            
        except Exception as e:
            # Autre erreur avec le token
            logger.error(f"Erreur de token: {str(e)}")
            return None
            
        return None
    
    def process_response(self, request, response):
        """
        Intercepte les réponses pour rafraîchir automatiquement les tokens expirés
        """
        # Vérifier si c'est une erreur 401 (non autorisé)
        if response.status_code == 401 and request.path.startswith('/api/'):
            try:
                data = json.loads(response.content)
                
                # Vérifier si c'est une erreur de token expiré
                if 'code' in data and data['code'] == 'token_not_valid':
                    
                    # Vérifier si le middleware a détecté un token expiré
                    if hasattr(request, 'token_expired') and request.token_expired:
                        
                        # Récupérer le refresh token depuis les cookies ou le cache
                        refresh_token = self.get_refresh_token_for_user(request)
                        
                        if refresh_token:
                            try:
                                # Rafraîchir le token
                                refresh = RefreshToken(refresh_token)
                                new_access_token = str(refresh.access_token)
                                
                                # Ajouter le nouveau token dans les headers de la réponse
                                response['X-New-Access-Token'] = new_access_token
                                response['X-Token-Refreshed'] = 'true'
                                
                                # Ajouter un message pour le frontend
                                response_data = json.loads(response.content)
                                response_data['token_refreshed'] = True
                                response_data['new_access_token'] = new_access_token
                                response.content = json.dumps(response_data)
                                
                                logger.info("Token rafraîchi automatiquement pour l'utilisateur")
                                
                            except TokenError as e:
                                logger.error(f"Impossible de rafraîchir le token: {str(e)}")
                                
            except (json.JSONDecodeError, KeyError) as e:
                pass
            except Exception as e:
                logger.error(f"Erreur dans le middleware JWT: {str(e)}")
        
        return response
    
    def get_refresh_token_for_user(self, request):
        """
        Récupère le refresh token pour l'utilisateur
        Plusieurs méthodes possibles:
        1. Depuis les cookies (si stocké côté client)
        2. Depuis le cache Django (si stocké côté serveur)
        3. Depuis la session
        """
        # Méthode 1: Depuis les cookies (si vous utilisez HttpOnly cookies)
        refresh_token = request.COOKIES.get('refresh_token')
        
        if refresh_token:
            return refresh_token
            
        # Méthode 2: Depuis le cache (si stocké avec user_id)
        if hasattr(request, 'user_id'):
            cache_key = f'refresh_token_{request.user_id}'
            refresh_token = cache.get(cache_key)
            return refresh_token
            
        # Méthode 3: Depuis le header (non recommandé pour production)
        refresh_header = request.META.get('HTTP_X_REFRESH_TOKEN')
        return refresh_header