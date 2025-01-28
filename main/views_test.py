from django.shortcuts import render
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from .serializers import *
import random
import string
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from django.contrib.auth.decorators import login_required
from .utils import send_email_with_secret_code
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

            # Envoi du code de connexion par email
            send_email(
                _('Votre code de connexion'),
                [user.email],
                'main/emails/email_with_connexion_code.html',
                {'code_connexion': code_connexion},
            )

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': _('Un code secret a été envoyé à votre adresse email !'),
                'reset_url': reset_url,
            })
            
            response = JsonResponse({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': _('Un code secret a été envoyé à votre adresse email !'),
                'reset_url': reset_url,
            })
            response.set_cookie('auth_token', str(refresh.access_token), max_age=3600)
            return response

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



# === Vues Pages Statiques === #

def index(request):
    return render(request, 'main/index.html')


def check_auth(request):
    return render(request, 'main/check_auth.html')


def forgot_auth(request):
    return render(request, 'main/forgot_auth.html')


def reset_auth(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/reset_auth.html', {'error': _('Token manquant.')})
    return render(request, 'main/reset_auth.html', {'token': token})



# === Vues Dashboards === #

@login_required
def dash_root(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
    user = request.user
    context = {
        'dash_active': 'active',
        'users_active': '',
        'buyers_active': '',
        'requests_active': '',
        'reports_active': '',
        'alerts_active': '',
        'modules_active': '',
        'countries_active': '',
        'settings_active': '',
        'account_active': '',
        
        'user': user,
    }
    return render(request, 'main/root/dash_root.html', context)

@login_required
def dash_root_pays(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
    
    user = request.user
    search_query = request.GET.get('search', '')  # Recherche
    page_number = request.GET.get('page', 1)  # Pagination

    # Requête filtrée
    pays_list = Pays.objects.filter(
        Q(nom__icontains=search_query) | Q(code__icontains=search_query)
    ).order_by('nom')

    # Pagination
    paginator = Paginator(pays_list, 10)  # 10 items par page
    pays_page = paginator.get_page(page_number)

    context = {
        
        'dash_active': '',
        'users_active': '',
        'buyers_active': '',
        'requests_active': '',
        'reports_active': '',
        'alerts_active': '',
        'modules_active': '',
        'countries_active': 'active',
        'settings_active': '',
        'account_active': '',
        
        'user': user,
        'token': token,
        'pays_page': pays_page,
    }
    return render(request, 'main/root/pays/dash_root_pays.html', context)


@login_required
def dash_validateur(request):
    return render(request, 'main/validateur/dash_validateur.html')


@login_required
def dash_analyste(request):
    return render(request, 'main/analyste/dash_analyste.html')


@login_required
def dash_client(request):
    return render(request, 'main/client/dash_client.html')


# === Vues Localisation === #

class ListPaysView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return Response({'detail': 'Token manquant ou invalide.'}, status=status.HTTP_401_UNAUTHORIZED)

        token = token.split(' ')[1]
        try:
            user = CustomUser.objects.get(reset_token=token)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Token invalide.'}, status=status.HTTP_401_UNAUTHORIZED)

        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        pays_list = Pays.objects.filter(
            Q(nom__icontains=search_query) | Q(code__icontains=search_query)
        ).order_by('nom')

        paginator = Paginator(pays_list, 10)  # 10 items par page
        pays_page = paginator.get_page(page_number)
        serializer = PaysSerializer(pays_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': pays_page.has_next(),
            'previous': pays_page.has_previous()
        })
        
        
class SearchPaysView(APIView):
    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        pays = Pays.objects.filter(nom__icontains=search_term).order_by('nom')
        paginator = Paginator(pays, 10)  # Nombre d'éléments par page
        page_number = request.query_params.get('page')
        page_obj = paginator.get_page(page_number)
        serializer = PaysSerializer(page_obj, many=True)
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous()
        })

class AddPaysView(APIView):
    def post(self, request, *args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return Response({'detail': 'Token manquant ou invalide.'}, status=status.HTTP_401_UNAUTHORIZED)

        token = token.split(' ')[1]
        try:
            user = CustomUser.objects.get(reset_token=token)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Token invalide.'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = PaysSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class EditPaysView(APIView):
    def put(self, request, id, *args, **kwargs):
        try:
            pays = Pays.objects.get(id=id)
        except Pays.DoesNotExist:
            return Response({'detail': 'Pays non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PaysSerializer(pays, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeletePaysView(APIView):
    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids')
        if not ids:
            return Response({'detail': 'Aucun ID de pays fourni.'}, status=status.HTTP_400_BAD_REQUEST)

        pays = Pays.objects.filter(id__in=ids)
        pays.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

def gestion_article(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
    user = request.user
    context = {
        'dash_active': '',
        'users_active': '',
        'buyers_active': '',
        'requests_active': '',
        'reports_active': '',
        'alerts_active': '',
        'modules_active': '',
        'countries_active': '',
        'articles_active': 'active',
        'settings_active': '',
        'account_active': '',
        
        'user': user,
    }
    return render(request, 'main/root/articles/gestion_article.html', context)    
    
    
class ArticleListCreateView(APIView):
    def get(self, request):
        articles = Article.objects.all()
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ArticleDetailView(APIView):
    def get_object(self, pk):
        try:
            return Article.objects.get(pk=pk)
        except Article.DoesNotExist:
            return None

    def get(self, request, pk):
        article = self.get_object(pk)
        if article:
            serializer = ArticleSerializer(article)
            return Response(serializer.data)
        return Response(status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        article = self.get_object(pk)
        if article:
            serializer = ArticleSerializer(article, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        article = self.get_object(pk)
        if article:
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)

class ArticleSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '')
        articles = Article.objects.filter(titre__icontains=query)
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)
