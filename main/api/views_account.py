from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.hashers import make_password, check_password
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from PIL import Image
import io

from main.serializers import *
from main.models import User


def str_to_bool(value):
    """Convertit une chaîne en booléen"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "t", "yes", "y", "oui")
    return bool(value)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """
        Affiche le profil de l'utilisateur connecté.
        """
        user = request.user
        # IMPORTANT: Passer request dans le contexte
        serializer = ProfileUserSerializer(user, context={'request': request})
        return Response({
            "success": True,
            "user": serializer.data
        })
    
    def put(self, request, *args, **kwargs):
        """
        Modifie le profil de l'utilisateur connecté.
        """
        user = request.user
        data = request.data.copy()
        
        # Log pour debug
        print(f"Données reçues pour mise à jour profil: {data}")
        
        # Nettoyer les données
        for field in ['first_name', 'last_name', 'telephone', 'profession', 'address', 'email_cc']:
            if field in data and data[field] == '':
                data[field] = None
        
        # IMPORTANT: Passer request dans le contexte
        serializer = ProfileUserSerializer(
            user, 
            data=data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Profil mis à jour avec succès.",
                "user": serializer.data
            })
        
        return Response({
            "success": False,
            "errors": serializer.errors,
            "message": "Erreurs de validation."
        }, status=status.HTTP_400_BAD_REQUEST)


class UserAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def validate_avatar(self, file):
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        valid_mimetypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']

        ext = os.path.splitext(file.name)[1].lower()
        if ext not in valid_extensions:
            return False, "Format de fichier non supporté."

        if file.content_type not in valid_mimetypes:
            return False, "Type MIME non supporté."

        if file.size > 5 * 1024 * 1024:
            return False, "Le fichier dépasse 5MB."

        try:
            file.seek(0)
            image_bytes = io.BytesIO(file.read())
            image_bytes.seek(0)

            img = Image.open(image_bytes)
            img.verify()

            image_bytes.seek(0)
            img = Image.open(image_bytes)

            if img.width < 100 or img.height < 100:
                return False, "Image trop petite (min 100x100)."

            ratio = max(img.width, img.height) / min(img.width, img.height)
            if ratio > 2:
                return False, "Ratio d'image trop extrême."

        except Exception as e:
            return False, f"Image invalide: {e}"

        finally:
            file.seek(0)

        return True, "OK"

    
    def process_avatar(self, file, user_id):
        """Traite et optimise l'image avatar"""
        try:
            # Ouvrir l'image avec PIL
            img = Image.open(file)
            
            # Convertir en RGB si nécessaire
            if img.mode in ('RGBA', 'LA', 'P'):
                # Créer un fond blanc
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            
            # Redimensionner si trop grand (max 400x400)
            max_size = (400, 400)
            if img.width > max_size[0] or img.height > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convertir en format WebP pour un meilleur rapport qualité/taille
            output = io.BytesIO()
            img.save(output, format='WEBP', quality=85, optimize=True)
            output.seek(0)
            
            # Nom du fichier
            filename = f"avatar_{user_id}_{int(timezone.now().timestamp())}.webp"
            
            return output, filename
            
        except Exception as e:
            print(f"Erreur traitement avatar: {e}")
            # Fallback: utiliser le fichier original
            file.seek(0)
            return file, file.name
    
    def put(self, request, *args, **kwargs):
        """
        Modifie l'avatar (photo de profil) de l'utilisateur connecté.
        """
        user = request.user
        
        if 'avatar' not in request.data:
            return Response({
                "success": False,
                "error": "Le champ 'avatar' est requis."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        avatar_file = request.data['avatar']
        
        # Valider le fichier
        is_valid, error_message = self.validate_avatar(avatar_file)
        if not is_valid:
            return Response({
                "success": False,
                "error": error_message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Traiter l'image
            processed_file, filename = self.process_avatar(avatar_file, user.id)
            
            # Sauvegarder l'ancien avatar pour suppression
            old_avatar = user.avatar
            
            # Sauvegarder le nouveau fichier
            avatar_path = default_storage.save(f"avatars/{filename}", ContentFile(processed_file.getvalue()))
            
            # Mettre à jour l'utilisateur
            user.avatar = avatar_path
            user.save()
            
            # Supprimer l'ancien avatar si différent du nouveau
            if old_avatar and old_avatar.name != avatar_path:
                try:
                    default_storage.delete(old_avatar.name)
                except:
                    pass  # Ignorer l'erreur si le fichier n'existe pas
            
            # Sérialiser la réponse
            serializer = ProfileUserSerializer(user, context={'request': request})
            
            return Response({
                "success": True,
                "message": "Avatar mis à jour avec succès.",
                "user": serializer.data
            })
            
        except Exception as e:
            print(f"Erreur sauvegarde avatar: {e}")
            return Response({
                "success": False,
                "error": f"Erreur lors du traitement de l'image: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    def validate_password(self, password):
        """Valide la force du mot de passe"""
        errors = []
        
        # Vérifier la longueur
        if len(password) < 8:
            errors.append("Le mot de passe doit contenir au moins 8 caractères.")
        
        # Vérifier la complexité
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '@$!%*?&' for c in password)
        
        if not has_upper:
            errors.append("Le mot de passe doit contenir au moins une lettre majuscule.")
        if not has_lower:
            errors.append("Le mot de passe doit contenir au moins une lettre minuscule.")
        if not has_digit:
            errors.append("Le mot de passe doit contenir au moins un chiffre.")
        if not has_special:
            errors.append("Le mot de passe doit contenir au moins un caractère spécial (@$!%*?&).")
        
        # Vérifier les mots de passe courants
        common_passwords = [
            'password', '123456', 'qwerty', 'admin', 'letmein', 
            'welcome', 'monkey', 'dragon', 'baseball', 'football',
            'sunshine', 'master', 'hello', 'freedom', 'whatever'
        ]
        if password.lower() in common_passwords:
            errors.append("Ce mot de passe est trop commun. Veuillez en choisir un autre.")
        
        return errors
    
    def put(self, request, *args, **kwargs):
        user = request.user
        current_password = request.data.get("current_password", "").strip()
        new_password = request.data.get("new_password", "").strip()
        confirm_password = request.data.get("confirm_password", "").strip()
        
        # Vérifier la présence des champs
        if not current_password or not new_password or not confirm_password:
            return Response({
                "success": False,
                "error": "Tous les champs sont requis."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier l'ancien mot de passe
        if not check_password(current_password, user.password):
            return Response({
                "success": False,
                "error": "L'ancien mot de passe est incorrect."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier que le nouveau n'est pas identique à l'ancien
        if current_password == new_password:
            return Response({
                "success": False,
                "error": "Le nouveau mot de passe doit être différent de l'ancien."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier la correspondance
        if new_password != confirm_password:
            return Response({
                "success": False,
                "error": "Le nouveau mot de passe et la confirmation ne correspondent pas."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Valider la force du nouveau mot de passe
        password_errors = self.validate_password(new_password)
        if password_errors:
            return Response({
                "success": False,
                "error": " ".join(password_errors)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour le mot de passe
        try:
            user.set_password(new_password)
            user.save()
            
            # Mettre à jour la dernière modification du mot de passe
            user.password_changed_at = timezone.now()
            user.save(update_fields=['password_changed_at'])
            
            return Response({
                "success": True,
                "message": "Mot de passe mis à jour avec succès.",
                "password_changed_at": user.password_changed_at.isoformat() if user.password_changed_at else None
            })
            
        except Exception as e:
            print(f"Erreur changement mot de passe: {e}")
            return Response({
                "success": False,
                "error": "Une erreur est survenue lors de la mise à jour du mot de passe."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)