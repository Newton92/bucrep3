from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.serializers import *

# === Vues Commande === #


class ListCommandeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get("search", "")
        page_number = request.query_params.get("page", 1)

        commande_list = Commande.objects.filter(
            Q(notre_ref__icontains=search_query)
            | Q(reference_client__icontains=search_query)
            | Q(raison_sociale__icontains=search_query)
            | Q(status__icontains=search_query)
        ).order_by("-created_at")

        paginator = Paginator(commande_list, 10)  # 10 éléments par page
        commande_page = paginator.get_page(page_number)
        serializer = CommandeSerializer(commande_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": commande_page.has_next(),
                "previous": commande_page.has_previous(),
            }
        )


class SearchCommandeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        commande_list = Commande.objects.filter(
            Q(notre_ref__icontains=search_term)
            | Q(reference_client__icontains=search_term)
            | Q(raison_sociale__icontains=search_term)
            | Q(status__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(commande_list, 10)  # 10 éléments par page
        page_number = request.query_params.get("page", 1)
        commande_page = paginator.get_page(page_number)
        serializer = CommandeSerializer(commande_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": commande_page.has_next(),
                "previous": commande_page.has_previous(),
            }
        )


class AddCommandeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddCommandeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditCommandeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        commande = Commande.objects.filter(id=id).first()
        if not commande:
            return Response(
                {"detail": "Commande non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetCommandeSerializer(commande)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        commande = Commande.objects.filter(id=id).first()
        if not commande:
            return Response(
                {"detail": "Commande non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditCommandeSerializer(commande, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteCommandeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        commandes = Commande.objects.filter(id__in=ids)
        if not commandes.exists():
            return Response(
                {"error": "Aucune commande trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = commandes.delete()
        return Response(
            {"message": f"{count} commandes supprimées avec succès."},
            status=status.HTTP_200_OK,
        )


class GetCommandeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        commande = Commande.objects.filter(id=id).first()
        if not commande:
            return Response(
                {"detail": "Commande non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CheckCommandeSerializer(commande)
        return Response(serializer.data)
