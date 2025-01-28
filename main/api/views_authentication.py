from django.shortcuts import render
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from main.models import CustomUser
from main.serializers import *
import random
import string
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from django.contrib.auth.decorators import login_required
from main.utils import send_email_with_secret_code
from django.template.loader import render_to_string
from rest_framework import status
from django.contrib.auth import logout
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django.urls import reverse
from django.contrib.auth import login
from rest_framework.viewsets import ModelViewSet
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


# Create your views here.

# === Fonctions Utilitaires === #

def generate_token(length=32):
    """Génère un token aléatoire."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def send_email(subject, recipient_list, template_name, context):
    """Envoie un email HTML avec un sujet et un contenu donné."""
    html_message = render_to_string(template_name, context)
    from_email = 'bucrepcontact@gmail.com'
    send_mail(
        subject,
        '',  # Corps texte vide (on utilise HTML)
        from_email,
        recipient_list,
        fail_silently=False,
        html_message=html_message,
    )


# === Vues Authentification === #

CustomUser = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.set_cookie(
            'access_token',
            response.data['access'],
            httponly=True,
            secure=True,
            samesite='Strict',
        )
        response.set_cookie(
            'refresh_token',
            response.data['refresh'],
            httponly=True,
            secure=True,
            samesite='Strict',
        )
        del response.data['access']
        del response.data['refresh']
        return response


class CustomRefreshTokenView(APIView):
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')

        # Vérifier si user_id est présent
        if not user_id:
            return Response(
                {'detail': _('user_id est requis.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Récupérer l'utilisateur
            user = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {'detail': _('Utilisateur non trouvé.')},
                status=status.HTTP_404_NOT_FOUND
            )

        # Mettre à jour la dernière connexion
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        # Générer les tokens d'accès
        refresh = RefreshToken.for_user(user)

        # Retourner les tokens
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': _('Token rafraichi avec succès !'),
        })


class CustomLoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user:
            # Mise à jour de la dernière connexion
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            # Génération des tokens d'accès
            refresh = RefreshToken.for_user(user)

            # Génération et enregistrement du code de connexion
            code_connexion = generate_token(6)
            reset_token = generate_token()
            
            user.code_connexion = code_connexion
            user.reset_token = reset_token
            user.save()
            
            reset_url = reverse('check_auth') + f'?token={reset_token}'
            # reset_url = reverse('dash_root')

            # Envoi du code de connexion par email
            send_email(
                _('Votre code de connexion'),
                [user.email],
                'main/emails/email_with_connexion_code.html',
                {'code_connexion': code_connexion},
            )

            # Génération du cookie
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': _('Un code secret a été envoyé à votre adresse email !'),
                'reset_url': reset_url,
            })

        return Response({'detail': _('Vos identifiants sont invalides.')}, status=status.HTTP_401_UNAUTHORIZED)


class CustomDoubleFactorAuthView(APIView):
    def post(self, request, *args, **kwargs):
        code_connexion = request.data.get('code_connexion')
        token = request.data.get('token')

        if not code_connexion or not token:
            return Response({'detail': _('Informations manquantes.')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Recherche de l'utilisateur correspondant au code_connexion et au token
            user = CustomUser.objects.get(code_connexion=code_connexion, reset_token=token)

            # Authentification de l'utilisateur
            login(request, user)
            
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)

            # Réponse avec cookies sécurisés
            response = Response({'message': 'Authentification réussie.'})
            response.set_cookie(
                'access_token', str(refresh.access_token),
                httponly=True, secure=True, samesite='Strict'
            )
            response.set_cookie(
                'refresh_token', str(refresh),
                httponly=True, secure=True, samesite='Strict'
            )

            # Redirection en fonction du rôle de l'utilisateur
            role_redirects = {
                'Root': reverse('dash_root'),
                'Validateur': reverse('dash_validateur'),
                'Analyste': reverse('dash_analyste'),
                'Client': reverse('dash_client'),
            }

            redirect_url = role_redirects.get(user.role)
            if not redirect_url:
                return Response({'detail': _('Rôle utilisateur inconnu.')}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'redirect_url': f"{redirect_url}?token={token}"}, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response({'detail': _('Code de connexion ou token invalide.')}, status=status.HTTP_400_BAD_REQUEST)


class CustomForgotPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')

        if not email:
            return Response({'detail': _('Veuillez fournir une adresse email.')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
            code_secret = generate_token(6)
            reset_token = generate_token()

            user.code_secret = code_secret
            user.reset_token = reset_token
            user.save()

            # Envoi du code secret par email
            send_email(
                _('Votre code secret'),
                [user.email],
                'main/emails/email_with_secret_code.html',
                {'code_secret': code_secret},
            )

            reset_url = reverse('reset_auth') + f'?token={reset_token}'
            return Response({'detail': _('Courriel de réinitialisation du mot de passe envoyé.'), 'reset_url': reset_url})

        except CustomUser.DoesNotExist:
            return Response({'detail': _('Aucun utilisateur trouvé avec cet email.')}, status=status.HTTP_404_NOT_FOUND)


class CustomResetPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        code_secret = request.data.get('code_secret')
        new_password = request.data.get('new_password')
        token = request.data.get('token')

        if not code_secret or not new_password or not token:
            return Response({'detail': _('Informations manquantes.')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(reset_token=token, code_secret=code_secret)
            user.set_password(new_password)
            user.reset_token = None
            user.code_secret = None
            user.save()

            # Envoi de l'email de confirmation au propriétaire du compte
            send_email(
                _('Confirmation de réinitialisation du mot de passe'),
                [user.email],
                'main/emails/email_reset_password_confirmation.html',
                {'user': user},
            )

            return Response({'detail': _('Mot de passe réinitialisé avec succès.')})

        except CustomUser.DoesNotExist:
            # Envoi d'un email au webmaster pour signaler une tentative non autorisée
            send_email(
                _('Tentative non autorisée de réinitialisation du mot de passe'),
                ['webmaster@example.com'],  # Remplacez par l'email du webmaster
                'main/emails/email_unauthorized_reset_attempt.html',
                {'token': token, 'code_secret': code_secret},
            )

            return Response({'detail': _('Token invalide ou expiré.')}, status=status.HTTP_400_BAD_REQUEST)


class CustomLogoutView(APIView):
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({'detail': _('Déconnecté avec succès.')}, status=status.HTTP_200_OK)
