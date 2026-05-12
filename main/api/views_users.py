from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import secrets
import string
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from main.models import User, Pays
from main.serializers import *

# === Vues Acheteur === #


User = get_user_model()



# Ajouter la méthode get_queryset pour la réutilisabilité
class ListUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self, search_query='', user_type=''):
        """Retourne le queryset filtré selon la recherche et le type"""
        queryset = User.objects.select_related('pays').prefetch_related(
            'groups', 'affectation', 'affectation_possible'
        )

        if user_type == 'client':
            queryset = queryset.filter(Q(role='Client') | Q(is_client=True))
        elif user_type == 'staff':
            queryset = queryset.exclude(Q(role='Client') | Q(is_client=True))

        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(pays__nom__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(role__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        return queryset.order_by("-date_joined")

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get("search", "").strip()
        user_type = request.query_params.get("user_type", "").strip()
        page_number = request.query_params.get("page", 1)
        
        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1
        
        # Obtenir le queryset
        users_query = self.get_queryset(search_query, user_type)
        
        # Pagination
        paginator = Paginator(users_query, 10)
        
        try:
            user_page = paginator.page(page_number)
        except PageNotAnInteger:
            user_page = paginator.page(1)
            page_number = 1
        except EmptyPage:
            user_page = paginator.page(paginator.num_pages)
            page_number = paginator.num_pages
        
        # **IMPORTANT: Passer request dans le contexte**
        serializer = NewUserSerializer(
            user_page, 
            many=True, 
            context={'request': request}  # <-- Ajouter ceci
        )
        
        # Calculer les indices
        start_index = (page_number - 1) * paginator.per_page + 1
        end_index = min(page_number * paginator.per_page, paginator.count)
        
        return Response({
            "results": serializer.data,
            "pagination": {
                "total": paginator.count,
                "per_page": paginator.per_page,
                "current_page": page_number,
                "total_pages": paginator.num_pages,
                "start_index": start_index,
                "end_index": end_index,
                "has_next": user_page.has_next(),
                "has_previous": user_page.has_previous(),
                "next_page": user_page.next_page_number() if user_page.has_next() else None,
                "previous_page": user_page.previous_page_number() if user_page.has_previous() else None,
            }
        })

# Vous pouvez supprimer SearchUtilisateurView si vous n'en avez pas besoin
# ou le fusionner avec ListUtilisateurView

class SearchUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        users_list = User.objects.filter(
            Q(username__icontains=search_term)
            | Q(pays__nom__icontains=search_term)
            | Q(email__icontains=search_term)
            | Q(role__icontains=search_term)
            | Q(first_name__icontains=search_term)
            | Q(last_name__icontains=search_term)
        ).order_by("-date_joined")

        paginator = Paginator(users_list, 10)  # 10 éléments par page
        page_number = request.query_params.get("page", 1)
        user_page = paginator.get_page(page_number)
        serializer = NewUserSerializer(user_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": user_page.has_next(),
                "previous": user_page.has_previous(),
            }
        )


class AddUtilisateurViewTwo(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    


class AddUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]

    def generate_password(self, length=14):
        """Génère un mot de passe complexe."""
        alphabet = string.ascii_letters + string.digits + "!@#$%&*?"
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
            if (
                any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#$%&*?" for c in password)
            ):
                return password

    def _to_bool(self, value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def _to_int_list(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            raw_values = value
        elif isinstance(value, str):
            raw_values = [v.strip() for v in value.split(",") if v.strip()]
        else:
            raw_values = [value]

        ids = []
        for item in raw_values:
            try:
                ids.append(int(item))
            except (TypeError, ValueError):
                continue
        # Conserver l'ordre tout en retirant les doublons
        return list(dict.fromkeys(ids))

    def send_welcome_email(self, user, plain_password):
        """Envoie l'email de bienvenue avec les identifiants"""
        try:
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            from django.conf import settings
            
            subject = "Vos identifiants de connexion - BUCREP/ACREMAC"
            
            context = {
                'user_username': user.username,
                'user_password': plain_password,
                'user_email': user.email,
                'user_fullname': f"{user.first_name} {user.last_name}",
            }
            
            # Template HTML
            html_message = render_to_string('main/emails/email_new_account.html', context)
            
            # Version texte
            text_message = f"""
            Bonjour {user.first_name} {user.last_name},
            
            Votre compte a été créé avec succès sur la plateforme BUCREP/ACREMAC.
            
            VOS IDENTIFIANTS :
            -----------------
            Nom d'utilisateur : {user.username}
            Mot de passe temporaire : {plain_password}
            
            ACCÈS À LA PLATEFORME :
            ----------------------
            • Avec VPN : http://10.0.57.47/
            • Sans VPN : http://preprod.bucrep3.bucrep.net/
            
            SÉCURITÉ :
            ---------
            Veuillez changer votre mot de passe dès votre première connexion.
            
            Cordialement,
            L'équipe BUCREP/ACREMAC
            """
            
            # Liste des destinataires
            recipient_list = [user.email]
            if user.email_cc:
                recipient_list.append(user.email_cc)
            
            # Envoyer l'email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bucrep.net'),
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=True,
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur d'envoi d'email: {str(e)}")
            return False

    def post(self, request, *args, **kwargs):
        """
        Crée un nouvel utilisateur avec mot de passe généré automatiquement
        et envoie les identifiants par email.
        """
        try:
            print(f"=== DEBUG AJOUT UTILISATEUR ===")
            print(f"Données reçues: {request.data}")
            print(f"Type de activation: {type(request.data.get('activation'))}")
            print(f"Valeur de activation: {request.data.get('activation')}")
            print("==============================")
            
            # 1. Préparer les données
            data = request.data.copy()
            
            # 2. Gérer les booléens
            data['activation'] = self._to_bool(data.get('activation'), default=True)
            data['is_staff'] = self._to_bool(data.get('is_staff'), default=False)
            data['is_superuser'] = self._to_bool(data.get('is_superuser'), default=False)
            data['is_client'] = self._to_bool(data.get('is_client'), default=False)
            if data.get('role') == 'Client':
                data['is_client'] = True
            
            # 3. S'assurer que 'pays' est un entier
            if 'pays' in data and data['pays']:
                try:
                    data['pays'] = int(data['pays'])
                except (ValueError, TypeError) as e:
                    return Response(
                        {"pays": ["Veuillez fournir un ID de pays valide (nombre entier)."]},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # 4. Champs multiples
            data['groups'] = self._to_int_list(data.get('groups'))
            data['affectation'] = self._to_int_list(data.get('affectation'))
            data['affectation_possible'] = self._to_int_list(data.get('affectation_possible'))
            
            print(f"Données après traitement: {data}")
            
            # 5. Générer (ou récupérer) un mot de passe sécurisé
            plain_password = data.get('password') or self.generate_password()
            print(f"Mot de passe généré: {plain_password}")
            
            # 6. Valider les données avec le serializer
            serializer = AddUserSerializer(data=data, context={'request': request})
            
            if not serializer.is_valid():
                print(f"❌ Erreurs de validation: {serializer.errors}")
                return Response(
                    {
                        'success': False,
                        'errors': serializer.errors,
                        'message': 'Erreurs de validation'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print(f"✅ Données validées: {serializer.validated_data}")
            
            # 7. Créer l'utilisateur
            user = serializer.save(password=plain_password)
            
            print(f"✅ Utilisateur créé: {user.username} (ID: {user.id})")
            
            # 8. Envoyer l'email de bienvenue
            email_sent = self.send_welcome_email(user, plain_password)
            print(f"📧 Email envoyé: {email_sent}")
            
            # 9. Préparer la réponse
            response_data = {
                'success': True,
                'message': 'Utilisateur créé avec succès',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': f"{user.first_name} {user.last_name}".strip(),
                    'role': user.role,
                    'is_client': user.is_client,
                },
                'email_sent': email_sent,
                'note': 'Les identifiants ont été envoyés par email.' if email_sent 
                       else 'Les identifiants n\'ont pas pu être envoyés par email.',
                'generated_password': plain_password,
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"❌ Erreur inattendue: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return Response(
                {
                    'success': False,
                    'message': 'Erreur interne du serveur',
                    'error': str(e),
                    'traceback': traceback.format_exc() if settings.DEBUG else None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            
            
            
# views_users.py
class EditUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, id):
        """Récupère l'utilisateur ou retourne 404"""
        try:
            return User.objects.select_related('pays').prefetch_related(
                'groups', 'affectation', 'affectation_possible'
            ).get(id=id)
        except User.DoesNotExist:
            return None
    
    def get(self, request, id, *args, **kwargs):
        utilisateur = self.get_object(id)
        if not utilisateur:
            return Response(
                {"detail": "Cet utilisateur ne figure pas dans la base."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = GetUserSerializer(utilisateur)
        return Response(serializer.data)
    
    def put(self, request, id, *args, **kwargs):
        utilisateur = self.get_object(id)
        if not utilisateur:
            return Response(
                {"detail": "Cet utilisateur ne figure pas dans la base."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Vérifier si l'utilisateur peut modifier son propre rôle/pays
        # (ajoutez cette logique selon vos besoins)
        
        # Préparer les données
        data = request.data.copy()
        
        # Convertir les booléens
        for bool_field in ['activation', 'is_staff', 'is_superuser', 'is_client']:
            if bool_field in data:
                value = data.get(bool_field)
                if isinstance(value, bool):
                    data[bool_field] = value
                else:
                    data[bool_field] = str(value).strip().lower() in {'1', 'true', 'yes', 'on'}
        if data.get('role') == 'Client':
            data['is_client'] = True
        
        # Convertir pays en entier si nécessaire
        if 'pays' in data and data['pays']:
            try:
                data['pays'] = int(data['pays'])
            except (ValueError, TypeError):
                return Response(
                    {"pays": ["Veuillez fournir un ID de pays valide."]},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Convertir les listes d'IDs
        def _to_int_list(value):
            if value is None:
                return []
            if isinstance(value, list):
                values = value
            elif isinstance(value, str):
                values = [v.strip() for v in value.split(',') if v.strip()]
            else:
                values = [value]
            output = []
            for item in values:
                try:
                    output.append(int(item))
                except (TypeError, ValueError):
                    continue
            return list(dict.fromkeys(output))

        if 'groups' in data:
            data['groups'] = _to_int_list(data.get('groups'))
        if 'affectation' in data:
            data['affectation'] = _to_int_list(data.get('affectation'))
        if 'affectation_possible' in data:
            data['affectation_possible'] = _to_int_list(data.get('affectation_possible'))
        
        serializer = EditUserSerializer(
            utilisateur, 
            data=data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Retourner les données complètes de l'utilisateur
            updated_user = self.get_object(id)
            response_serializer = GetUserSerializer(updated_user)
            
            return Response({
                "success": True,
                "message": "Utilisateur mis à jour avec succès.",
                "user": response_serializer.data
            })
        
        return Response({
            "success": False,
            "errors": serializer.errors,
            "message": "Erreurs de validation."
        }, status=status.HTTP_400_BAD_REQUEST)
        
        

class EditUtilisateurAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def put(self, request, id, *args, **kwargs):
        utilisateur = User.objects.filter(id=id).first()
        if not utilisateur:
            return Response(
                {"detail": "Cet utilisateur ne figure pas dans la base."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditUserAvatarSerializer(
            utilisateur, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id=None, *args, **kwargs):
        # Si un ID est fourni dans l'URL
        if id:
            utilisateur = User.objects.filter(id=id).first()
            if not utilisateur:
                return Response(
                    {"error": "Utilisateur non trouvé."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            
            # Vérifier qu'on ne supprime pas l'utilisateur courant
            if utilisateur == request.user:
                return Response(
                    {"error": "Vous ne pouvez pas supprimer votre propre compte."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            utilisateur.delete()
            return Response(
                {"message": "Utilisateur supprimé avec succès."},
                status=status.HTTP_200_OK,
            )
        
        # Pour la suppression multiple (version originale)
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Exclure l'utilisateur courant de la suppression
        ids = [i for i in ids if i != request.user.id]
        
        utilisateurs = User.objects.filter(id__in=ids)
        if not utilisateurs.exists():
            return Response(
                {"error": "Aucun utilisateur trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = utilisateurs.delete()
        return Response(
            {"message": f"{count} Utilisateurs supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class GenerateAndSendPasswordUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]

    def _generate_password(self, length=14):
        alphabet = string.ascii_letters + string.digits + "!@#$%&*?"
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
            if (
                any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#$%&*?" for c in password)
            ):
                return password

    def _send_credentials_mail(self, user, plain_password):
        try:
            subject = "Vos identifiants de connexion - BUCREP/ACREMAC"
            context = {
                'user_username': user.username,
                'user_password': plain_password,
                'user_email': user.email,
                'user_fullname': f"{user.first_name} {user.last_name}",
            }
            html_message = render_to_string('main/emails/email_new_account.html', context)
            text_message = strip_tags(html_message)

            recipients = [user.email] if user.email else []
            if user.email_cc:
                recipients.append(user.email_cc)
            if not recipients:
                return False

            mail = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bucrep.net'),
                to=recipients,
            )
            mail.attach_alternative(html_message, "text/html")
            mail.send(fail_silently=True)
            return True
        except Exception:
            return False

    def post(self, request, id, *args, **kwargs):
        user = User.objects.filter(id=id).first()
        if not user:
            return Response(
                {"success": False, "message": "Utilisateur non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        plain_password = self._generate_password()
        user.set_password(plain_password)
        user.save(update_fields=["password", "password_changed_at"])

        email_sent = self._send_credentials_mail(user, plain_password)

        return Response(
            {
                "success": True,
                "message": "Mot de passe généré et mis à jour.",
                "generated_password": plain_password,
                "email_sent": email_sent,
            },
            status=status.HTTP_200_OK,
        )
