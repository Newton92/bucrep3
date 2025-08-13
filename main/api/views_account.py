from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.serializers import *

# === Fonctions utiles === #


def str_to_bool(value):
    return value.lower() in ("true", "1", "t")


# === Vues Modules Acheteur === #

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from main.models import CustomUser
from main.serializers import CustomUserSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Affiche le profil de l'utilisateur connecté.
        """
        user = request.user
        serializer = CustomUserSerializer(user)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """
        Modifie le profil de l'utilisateur connecté.
        """
        user = request.user
        serializer = CustomUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def put(self, request, *args, **kwargs):
        """
        Modifie l'avatar (photo de profil) de l'utilisateur connecté.
        """
        user = request.user
        # S'assurer que le champ 'avatar' est présent dans les données
        if 'avatar' not in request.data:
            return Response(
                {"error": "Le champ 'avatar' est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Utiliser un sérialiseur pour valider et sauvegarder le fichier
        serializer = CustomUserSerializer(user, data={'avatar': request.data['avatar']}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    
class ChangePasswordView(APIView):
    """
    Vue pour modifier le mot de passe de l'utilisateur connecté.
    Nécessite l'ancien mot de passe, le nouveau et sa confirmation.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        # Vérifier si les champs sont présents
        if not current_password or not new_password or not confirm_password:
            return Response(
                {"error": "Tous les champs (current_password, new_password, confirm_password) sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vérifier l'ancien mot de passe
        if not user.check_password(current_password):
            return Response(
                {"error": "L'ancien mot de passe est incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vérifier que le nouveau mot de passe et sa confirmation correspondent
        if new_password != confirm_password:
            return Response(
                {"error": "Le nouveau mot de passe et la confirmation ne correspondent pas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mettre à jour le mot de passe
        user.password = make_password(new_password)
        user.save()

        return Response(
            {"message": "Mot de passe mis à jour avec succès."},
            status=status.HTTP_200_OK,
        )
