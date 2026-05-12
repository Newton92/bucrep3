# main/context_processors.py
from django.conf import settings

def auth_tokens(request):
    """Ajoute les tokens d'authentification au contexte global"""
    tokens = {}
    
    if request.user.is_authenticated:
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(request.user)
            tokens = {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
            }
        except Exception:
            pass
    
    return tokens