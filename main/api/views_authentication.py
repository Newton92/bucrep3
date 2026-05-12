import random
import string

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from django.utils.translation import gettext_lazy as _
from django.utils import translation
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from main.models import User, Pays
from main.serializers import PaysSerializer
import requests

import logging

logger = logging.getLogger(__name__)


# Create your views here.

# === Fonctions Utilitaires === #


def get_country_from_ip(ip):
    try:
        # API gratuite : ipapi.co (pas besoin de clé)
        url = f"https://ipapi.co/{ip}/json/"
        data = requests.get(url, timeout=3).json()

        country_code = data.get("country_code")
        country_name = data.get("country_name")

        if country_code:
            try:
                return Pays.objects.get(code__iexact=country_code)
            except Pays.DoesNotExist:
                pass

        if country_name:
            try:
                return Pays.objects.get(nom__iexact=country_name)
            except Pays.DoesNotExist:
                pass

    except Exception:
        pass

    return None   # Aucun pays trouvé



def generate_token(length=32):
    """Génère un token aléatoire."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def send_email(subject, recipient_list, template_name, context):
    """Envoie un email HTML avec un sujet et un contenu donné."""
    html_message = render_to_string(template_name, context)
    from_email = "bucrepcontact@gmail.com"
    send_mail(
        subject,
        "",  # Corps texte vide (on utilise HTML)
        from_email,
        recipient_list,
        fail_silently=False,
        html_message=html_message,
    )


# === Vues Authentification === #

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.set_cookie(
            "access_token",
            response.data["access"],
            httponly=True,
            secure=True,
            samesite="Strict",
        )
        response.set_cookie(
            "refresh_token",
            response.data["refresh"],
            httponly=True,
            secure=True,
            samesite="Strict",
        )
        del response.data["access"]
        del response.data["refresh"]
        return response




class CustomRefreshTokenView(APIView):
    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")

        # Vérifier si user_id est présent
        if not user_id:
            return Response(
                {"detail": _("user_id est requis.")}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Récupérer l'utilisateur
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": _("Utilisateur non trouvé.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Mettre à jour la dernière connexion
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        # Générer les tokens d'accès
        refresh = RefreshToken.for_user(user)

        # Retourner les tokens
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "message": _("Token rafraichi avec succès !"),
            }
        )




class CustomLoginViewFirst(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user:
            # Mise à jour de la dernière connexion
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])

            # Génération des tokens d'accès
            refresh = RefreshToken.for_user(user)

            # Génération et enregistrement du code de connexion
            code_connexion = generate_token(6)
            reset_token = generate_token()

            user.code_connexion = code_connexion
            user.reset_token = reset_token
            user.save()

            reset_url = reverse("check_auth") + f"?token={reset_token}"
            # reset_url = reverse('dash_root')

            # Envoi du code de connexion par email
            send_email(
                _("Votre code de connexion"),
                [user.email],
                "main/emails/email_with_connexion_code.html",
                {"code_connexion": code_connexion},
            )

            # Génération du cookie
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "message": _("Un code secret a été envoyé à votre adresse email !"),
                    "reset_url": reset_url,
                }
            )

        return Response(
            {"detail": _("Vos identifiants sont invalides.")},
            status=status.HTTP_401_UNAUTHORIZED,
        )




class CustomLoginViewCopy(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user:
            # Mise à jour de la dernière connexion
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])

            # Génération des tokens d'accès
            refresh = RefreshToken.for_user(user)

            # Génération et enregistrement du code de connexion
            code_connexion = generate_token(6)
            reset_token = generate_token()

            user.code_connexion = code_connexion
            user.reset_token = reset_token
            user.save()

            reset_url = reverse("check_auth") + f"?token={reset_token}"
            # reset_url = reverse('dash_root')

            # Envoi du code de connexion par email
            send_email(
                _("Votre code de connexion"),
                [user.email],
                "main/emails/email_with_connexion_code.html",
                {"code_connexion": code_connexion},
            )

            # Génération du cookie
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "message": _("Un code secret a été envoyé à votre adresse email !"),
                    "reset_url": reset_url,
                }
            )

        return Response(
            {"detail": _("Vos identifiants sont invalides.")},
            status=status.HTTP_401_UNAUTHORIZED,
        )




# @method_decorator(csrf_exempt, name='dispatch')
class CustomLoginView(APIView):
    # authentication_classes = []   # IMPORTANT
    # permission_classes = []       # IMPORTANT

    def post(self, request, *args, **kwargs):
        logger.info("Tentative de connexion reçue")

        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            logger.warning("Login échoué : username ou password manquant")
            return Response(
                {"detail": _("Nom d'utilisateur ou mot de passe manquant.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.debug(f"Tentative d'authentification pour l'utilisateur: {username}")

        user = authenticate(username=username, password=password)

        if user:
            logger.info(f"Authentification réussie pour l'utilisateur: {username}")

            # Création de la session Django
            login(request, user)
            logger.debug(f"Session Django créée pour user_id={user.id}")

            # Génération des tokens JWT
            refresh = RefreshToken.for_user(user)
            logger.debug(f"JWT généré pour user_id={user.id}")

            # Génération des codes de sécurité
            code_connexion = generate_token(6)
            reset_token = generate_token()

            user.code_connexion = code_connexion
            user.reset_token = reset_token
            user.save(update_fields=["code_connexion", "reset_token"])

            logger.info(
                f"Codes de sécurité mis à jour pour user_id={user.id}"
            )

            selected_pays = None
            selected_pays_id = None

            # Détection du pays selon le rôle
            if user.role == "Root":
                logger.debug("Utilisateur ROOT détecté")

                # Priorité 1 : dernier pays persisté en DB
                if user.pays_actif_id:
                    selected_pays = user.pays_actif
                    selected_pays_id = user.pays_actif_id
                    logger.debug(f"Root: pays_actif restauré depuis DB : {selected_pays_id}")
                else:
                    # Fallback : géolocalisation IP
                    client_ip = request.META.get("REMOTE_ADDR")
                    logger.debug(f"Root: IP client détectée : {client_ip}")
                    selected_pays = get_country_from_ip(client_ip)

                    if not selected_pays:
                        logger.warning("Root: géolocalisation échouée, pays par défaut appliqué")
                        selected_pays = Pays.objects.filter(is_active=True).first()

                    selected_pays_id = selected_pays.id if selected_pays else None

            else:
                logger.debug(
                    f"Utilisateur standard ({user.role}), récupération du pays"
                )

                # Priorité 1 : dernier pays persisté en DB
                if user.pays_actif_id:
                    selected_pays = user.pays_actif
                    selected_pays_id = user.pays_actif_id
                    logger.debug(f"Pays restauré depuis DB (pays_actif) : {selected_pays_id}")

                elif user.pays:
                    selected_pays = user.pays
                    selected_pays_id = user.pays.id
                    logger.debug(
                        f"Pays récupéré depuis le profil utilisateur : {selected_pays_id}"
                    )

                else:
                    logger.warning(
                        "Aucun pays trouvé (profil), pays par défaut appliqué"
                    )
                    selected_pays = Pays.objects.filter(is_active=True).first()
                    selected_pays_id = selected_pays.id if selected_pays else None

            logger.info(
                f"Pays sélectionné pour user_id={user.id} : {selected_pays_id}"
            )

            if selected_pays_id:
                request.session["selected_pays_id"] = selected_pays_id

            # Restaurer la langue préférée depuis la DB
            if user.preferred_language:
                translation.activate(user.preferred_language)
                request.session['_language'] = user.preferred_language
                logger.debug(f"Langue restaurée depuis DB : {user.preferred_language}")

            # Cookies sécurisés
            response = Response({"message": _("Authentification réussie.")})

            response.set_cookie(
                "access_token",
                str(refresh.access_token),
                httponly=True,
                secure=True,
                samesite="Strict",
            )
            response.set_cookie(
                "refresh_token",
                str(refresh),
                httponly=True,
                secure=True,
                samesite="Strict",
            )

            # Redirection selon le rôle
            role_redirects = {
                "Root": reverse("dash_root"),
                "Validateur": reverse("dash_validateur"),
                "Analyste": reverse("dash_analyste"),
                "Client": reverse("dash_client"),
            }

            redirect_url = role_redirects.get(user.role)

            if not redirect_url:
                logger.error(
                    f"Rôle inconnu pour user_id={user.id} : {user.role}"
                )
                return Response(
                    {"detail": _("Rôle utilisateur inconnu.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            logger.info(
                f"Redirection utilisateur user_id={user.id} vers {redirect_url}"
            )

            return Response(
                {
                    "message": _("Authentification réussie. Redirection en cours..."),
                    "reset_url": redirect_url,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "selected_pays_id": selected_pays_id,
                },
                status=status.HTTP_200_OK,
            )

        logger.warning(
            f"Échec d'authentification pour username={username}"
        )

        return Response(
            {"detail": _("Vos identifiants sont invalides.")},
            status=status.HTTP_401_UNAUTHORIZED,
        )





class CustomLoginViewDirect(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user:
            # Authentification et création de la session Django
            login(request, user)

            # Générer les tokens JWT
            # refresh = RefreshToken.for_user(user)

            # Génération et enregistrement du code de connexion
            code_connexion = generate_token(6)
            reset_token = generate_token()

            user.code_connexion = code_connexion
            user.reset_token = reset_token
            user.save()

            # Redirection en fonction du rôle de l'utilisateur
            role_redirects = {
                "Root": reverse("dash_root"),
                "Validateur": reverse("dash_validateur"),
                "Analyste": reverse("dash_analyste"),
                "Client": reverse("dash_client"),
            }

            redirect_url = role_redirects.get(user.role)

            if not redirect_url:
                return Response(
                    {"detail": _("Rôle utilisateur inconnu.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {
                    "message": _("Authentification réussie. Redirection en cours..."),
                    "redirect_url": redirect_url,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"detail": _("Vos identifiants sont invalides.")},
            status=status.HTTP_401_UNAUTHORIZED,
        )





class CustomDoubleFactorAuthViewOld(APIView):
    def post(self, request, *args, **kwargs):
        code_connexion = request.data.get("code_connexion")
        token = request.data.get("token")

        if not code_connexion or not token:
            return Response(
                {"detail": _("Informations manquantes.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Recherche de l'utilisateur correspondant au code_connexion et au token
            user = User.objects.get(
                code_connexion=code_connexion, reset_token=token
            )

            # Authentification de l'utilisateur
            login(request, user)

            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)

            # Génération et enregistrement du code de connexion
            code_connexion = generate_token(6)
            reset_token = generate_token()

            user.code_connexion = code_connexion
            user.reset_token = reset_token
            user.save()

            # Réponse avec cookies sécurisés
            response = Response({"message": "Authentification réussie."})
            response.set_cookie(
                "access_token",
                str(refresh.access_token),
                httponly=True,
                secure=True,
                samesite="Strict",
            )
            response.set_cookie(
                "refresh_token",
                str(refresh),
                httponly=True,
                secure=True,
                samesite="Strict",
            )

            # Redirection en fonction du rôle de l'utilisateur
            role_redirects = {
                "Root": reverse("dash_root") + f"?token={reset_token}",
                "Validateur": reverse("dash_validateur") + f"?token={reset_token}",
                "Analyste": reverse("dash_analyste") + f"?token={reset_token}",
                "Client": reverse("dash_client") + f"?token={reset_token}",
            }

            redirect_url = role_redirects.get(user.role)
            if not redirect_url:
                return Response(
                    {"detail": _("Rôle utilisateur inconnu.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                #{"redirect_url": f"{redirect_url}?token={token}"},
                {"redirect_url": f"{redirect_url}"},
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {"detail": _("Code de connexion ou token invalide.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
            




class CustomDoubleFactorAuthView(APIView):
    def post(self, request, *args, **kwargs):
        code_connexion = request.data.get("code_connexion")
        token = request.data.get("token")

        if not code_connexion or not token:
            return Response(
                {"detail": _("Informations manquantes.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(
                code_connexion=code_connexion, reset_token=token
            )
            
            # Ne générez pas de nouveaux tokens ici et ne faites pas de login()
            # On renvoie simplement l'ID de l'utilisateur pour l'initialisation de la session
            return Response(
                {
                    "message": "Authentification 2FA réussie.",
                    "user_id": user.pk,
                    "user_role": user.role,  # Ajoutez cette ligne
                },
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {"detail": _("Code de connexion ou token invalide.")},
                status=status.HTTP_400_BAD_REQUEST,
            )            
      
      
            
# La vue que vous devez ajouter
class SessionInitView(APIView):
    authentication_classes = [] # N'utilise pas l'authentification DRF classique
    permission_classes = [] # Ne nécessite pas d'être authentifié au préalable

    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=user_id)
            # L'appel à login() crée la session Django et le cookie
            login(request, user)
            return Response({"message": "Session initialized successfully."})
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)




class CustomForgotPasswordView(APIView):

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")

        if not email:
            return Response(
                {"detail": _("Veuillez fournir une adresse email.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email=email, is_active=True).first()

        if not user:
            return Response(
                {"detail": _("Aucun utilisateur trouvé avec cet email.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        code_secret = generate_token(6)
        reset_token = generate_token()

        user.code_secret = code_secret
        user.reset_token = reset_token
        user.save(update_fields=["code_secret", "reset_token"])

        # Envoi du code secret par email
        send_email(
            _("Votre code secret"),
            [user.email],
            "main/emails/email_with_secret_code.html",
            {"code_secret": code_secret},
        )

        # Redirect to the vitrine reset page (same treatment as reset_auth, but consistent UI).
        reset_url = reverse("reset_password") + f"?token={reset_token}"

        return Response(
            {
                "detail": _("Courriel de réinitialisation du mot de passe envoyé."),
                "reset_url": reset_url,
            },
            status=status.HTTP_200_OK,
        )




class CustomResetPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        code_secret = request.data.get("code_secret")
        new_password = request.data.get("new_password")
        token = request.data.get("token")

        if not code_secret or not new_password or not token:
            return Response(
                {"detail": _("Informations manquantes.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(reset_token=token, code_secret=code_secret)
            user.set_password(new_password)
            user.reset_token = None
            user.code_secret = None
            user.save()

            # Envoi de l'email de confirmation au propriétaire du compte
            send_email(
                _("Confirmation de réinitialisation du mot de passe"),
                [user.email],
                "main/emails/email_reset_password_confirmation.html",
                {"user": user},
            )

            return Response({"detail": _("Mot de passe réinitialisé avec succès.")})

        except User.DoesNotExist:
            # Envoi d'un email au webmaster pour signaler une tentative non autorisée
            send_email(
                _("Tentative non autorisée de réinitialisation du mot de passe"),
                ["webmaster@example.com"],  # Remplacez par l'email du webmaster
                "main/emails/email_unauthorized_reset_attempt.html",
                {"token": token, "code_secret": code_secret},
            )

            return Response(
                {"detail": _("Token invalide ou expiré.")},
                status=status.HTTP_400_BAD_REQUEST,
            )




class CustomLogoutViewOld(APIView):
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response(
            {"detail": _("Déconnecté avec succès.")}, status=status.HTTP_200_OK
        )





class CustomLogoutView(APIView):
    authentication_classes = []  # No authentication required for logout
    permission_classes = []      # No permissions required

    def post(self, request, *args, **kwargs):
        # Persister la langue préférée en DB avant que la session soit détruite
        if request.user.is_authenticated:
            current_lang = request.session.get('_language') or translation.get_language()
            if current_lang:
                request.user.__class__.objects.filter(pk=request.user.pk).update(
                    preferred_language=current_lang
                )
                logger.debug(f"Langue préférée sauvegardée pour user_id={request.user.id} : {current_lang}")

        logout(request)
        response = Response(
            {"detail": _("Déconnecté avec succès.")},
            status=status.HTTP_200_OK
        )
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response
    
    
    
    
    
class PaysListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pays_list = Pays.objects.filter(afficher_au_dashboard=True).order_by("nom")
        serializer = PaysSerializer(pays_list, many=True)
        return Response(serializer.data)
    
    
    
class UpdateSelectedPaysView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        pays_id = request.data.get('pays_id')
        if not pays_id:
            return Response(
                {"error": _("L'ID du pays est requis.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pays = Pays.objects.get(id=pays_id, afficher_au_dashboard=True)
            # Persister en session ET en base (survit à la déconnexion)
            request.session['selected_pays_id'] = pays.id
            request.user.__class__.objects.filter(pk=request.user.pk).update(pays_actif_id=pays.id)
            return Response(
                {
                    "message": _("Pays sélectionné mis à jour."),
                    "selected_pays_id": pays.id
                },
                status=status.HTTP_200_OK
            )
        except Pays.DoesNotExist:
            return Response(
                {"error": _("Pays non trouvé.")},
                status=status.HTTP_404_NOT_FOUND
            )
            
    def get(self, request, *args, **kwargs):
        # Priorité : session en cours → pays_actif en DB → user.pays → premier pays dashboard
        selected_pays_id = request.session.get("selected_pays_id")

        if not selected_pays_id:
            # Restaurer depuis la DB (persisté entre sessions)
            db_pays_actif = getattr(request.user, 'pays_actif_id', None)
            if db_pays_actif:
                selected_pays_id = db_pays_actif
            elif request.user.pays:
                selected_pays_id = request.user.pays.id

        if not selected_pays_id:
            first_pays = Pays.objects.filter(afficher_au_dashboard=True).order_by('nom').first()
            if first_pays:
                selected_pays_id = first_pays.id

        # Vérifier que ce pays est toujours valide
        if selected_pays_id:
            if not Pays.objects.filter(id=selected_pays_id, afficher_au_dashboard=True).exists():
                selected_pays_id = request.user.pays.id if request.user.pays else None

        # Toujours synchroniser la session
        if selected_pays_id:
            request.session["selected_pays_id"] = selected_pays_id

        return Response(
            {"selected_pays_id": selected_pays_id},
            status=status.HTTP_200_OK
        )
