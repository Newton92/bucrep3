from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import CustomUser
from main.serializers import *

# === Vues Acheteur === #


CustomUser = get_user_model()


class ListUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get("search", "")
        page_number = request.query_params.get("page", 1)

        users_list = CustomUser.objects.filter(
            Q(username__icontains=search_query)
            | Q(pays__nom__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(role__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        ).order_by("-date_joined")

        paginator = Paginator(users_list, 10)  # 10 éléments par page
        user_page = paginator.get_page(page_number)
        serializer = CustomUserSerializer(user_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": user_page.has_next(),
                "previous": user_page.has_previous(),
            }
        )


class SearchUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        users_list = CustomUser.objects.filter(
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
        serializer = CustomUserSerializer(user_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": user_page.has_next(),
                "previous": user_page.has_previous(),
            }
        )


class AddUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddCustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        utilisateur = CustomUser.objects.filter(id=id).first()
        if not utilisateur:
            return Response(
                {"detail": "Cet utilisateur ne figure pas dans la base."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetCustomUserSerializer(utilisateur)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        utilisateur = CustomUser.objects.filter(id=id).first()
        if not utilisateur:
            return Response(
                {"detail": "Cet utilisateur ne figure pas dans la base."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditCustomUserSerializer(
            utilisateur, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditUtilisateurAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def put(self, request, id, *args, **kwargs):
        utilisateur = CustomUser.objects.filter(id=id).first()
        if not utilisateur:
            return Response(
                {"detail": "Cet utilisateur ne figure pas dans la base."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditCustomUserAvatarSerializer(
            utilisateur, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteUtilisateurView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        utilisateurs = CustomUser.objects.filter(id__in=ids)
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
