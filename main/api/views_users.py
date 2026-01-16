from django.contrib.auth import get_user_model
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

from main.models import User
from main.serializers import *

# === Vues Acheteur === #


User = get_user_model()



# Ajouter la méthode get_queryset pour la réutilisabilité
class ListUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self, search_query=''):
        """Retourne le queryset filtré selon la recherche"""
        queryset = User.objects.select_related('pays')
        
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
        page_number = request.query_params.get("page", 1)
        
        try:
            page_number = int(page_number)
        except ValueError:
            page_number = 1
        
        # Obtenir le queryset
        users_query = self.get_queryset(search_query)
        
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

    def generate_password(self, length=10):
        """Génère un mot de passe sécurisé mais lisible"""
        import secrets
        import string
        letters = string.ascii_letters
        digits = string.digits
        alphabet = letters + digits
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        return password

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
            
            # 2. Gérer le champ 'activation' correctement
            if 'activation' in data:
                activation_value = data['activation']
                if isinstance(activation_value, str):
                    # Si c'est une chaîne ('true' ou 'false'), convertir en booléen
                    data['activation'] = activation_value.lower() == 'true'
                # Si c'est déjà un booléen, le laisser tel quel
                # Si c'est autre chose, essayer de convertir
                elif not isinstance(activation_value, bool):
                    try:
                        data['activation'] = bool(activation_value)
                    except:
                        data['activation'] = True  # Valeur par défaut
            
            # 3. S'assurer que 'pays' est un entier
            if 'pays' in data and data['pays']:
                try:
                    data['pays'] = int(data['pays'])
                except (ValueError, TypeError) as e:
                    return Response(
                        {"pays": ["Veuillez fournir un ID de pays valide (nombre entier)."]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            print(f"Données après traitement: {data}")
            
            # 4. Générer un mot de passe sécurisé
            plain_password = self.generate_password()
            print(f"Mot de passe généré: {plain_password}")
            
            # 5. Valider les données avec le serializer
            serializer = AddUserSerializer(data=data)
            
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
            
            # 6. Créer l'utilisateur
            validated_data = serializer.validated_data
            
            # Extraire le pays de validated_data
            pays = validated_data.pop('pays') if 'pays' in validated_data else None
            
            # Créer l'instance utilisateur
            user = User(
                username=validated_data['username'],
                email=validated_data['email'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
                email_cc=validated_data.get('email_cc'),
                address=validated_data.get('address'),
                activation=validated_data.get('activation', True),
                telephone=validated_data.get('telephone'),
                profession=validated_data.get('profession'),
                role=validated_data.get('role'),
                pays=pays,  # Assigner le pays
            )
            
            # 7. Définir le mot de passe
            user.set_password(plain_password)
            user.save()
            
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
                },
                'email_sent': email_sent,
                'note': 'Les identifiants ont été envoyés par email.' if email_sent 
                       else 'Les identifiants n\'ont pas pu être envoyés par email.',
                'debug': {
                    'password_generated': plain_password,
                    'activation_set_to': user.activation
                }
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
            return User.objects.select_related('pays').get(id=id)
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
        
        # Convertir l'activation si c'est une chaîne
        if 'activation' in data and isinstance(data['activation'], str):
            data['activation'] = data['activation'].lower() == 'true'
        
        # Convertir pays en entier si nécessaire
        if 'pays' in data and data['pays']:
            try:
                data['pays'] = int(data['pays'])
            except (ValueError, TypeError):
                return Response(
                    {"pays": ["Veuillez fournir un ID de pays valide."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
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
