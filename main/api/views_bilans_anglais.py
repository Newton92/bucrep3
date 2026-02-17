# Dans votre fichier views.py

from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import ActifA, PassifA, ResultatA
from main.serializers import (
    ActifAnglaisSerializer, AddActifAnglaisSerializer, EditActifAnglaisSerializer,
    PassifAnglaisSerializer, AddPassifAnglaisSerializer, EditPassifAnglaisSerializer,
    ResultatAnglaisSerializer, AddResultatAnglaisSerializer, EditResultatAnglaisSerializer,
)

# --- Vues pour la gestion des Actifs Anglais (ActifA) ---

class ListActifAView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        actif_list = ActifA.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")
        paginator = Paginator(actif_list, 10)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)
        serializer = ActifAnglaisSerializer(page_obj, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
        }, status=status.HTTP_200_OK)

class AddMultiYearActifAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        created_items = []
        errors = {}
        for suffix in ["n", "n1", "n2"]:
            if f"annee_{suffix}" in data:
                item_data = {
                    key.rsplit("_", 1)[0]: value
                    for key, value in data.items()
                    if key.endswith(f"_{suffix}")
                }
                item_data['acheteur'] = request.data.get(f'acheteur_{suffix}')
                if not item_data.get('acheteur') or not item_data.get('annee'):
                    continue
                serializer = AddActifAnglaisSerializer(data=item_data, context={"request": request})
                if serializer.is_valid():
                    instance = serializer.save(created_by=request.user)
                    created_items.append(ActifAnglaisSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        if not created_items:
            return Response({"detail": "Aucune donnée valide à enregistrer."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(created_items, status=status.HTTP_201_CREATED)

class GetActifAView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, actif_id, *args, **kwargs):
        try:
            actif = ActifA.objects.get(id=actif_id, acheteur_id=acheteur_id)
            serializer = ActifAnglaisSerializer(actif)
            return Response(serializer.data)
        except ActifA.DoesNotExist:
            return Response({"detail": "Actif non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class EditActifAView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, acheteur_id, actif_id, *args, **kwargs):
        try:
            actif = ActifA.objects.get(id=actif_id, acheteur_id=acheteur_id)
            serializer = EditActifAnglaisSerializer(actif, data=request.data, partial=True, context={"request": request})
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(ActifAnglaisSerializer(actif).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ActifA.DoesNotExist:
            return Response({"detail": "Actif non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class DeleteActifAView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response({"error": "La liste des IDs est requise."}, status=status.HTTP_400_BAD_REQUEST)
        count, _ = ActifA.objects.filter(id__in=ids, acheteur_id=acheteur_id).delete()
        if count == 0:
            return Response({"error": "Aucun actif trouvé pour les IDs fournis."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": f"{count} actif(s) supprimé(s) avec succès."}, status=status.HTTP_200_OK)

# --- Vues pour la gestion des Passifs Anglais (PassifA) ---

class ListPassifAView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        passif_list = PassifA.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")
        paginator = Paginator(passif_list, 10)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)
        serializer = PassifAnglaisSerializer(page_obj, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
        }, status=status.HTTP_200_OK)

class AddMultiYearPassifAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        created_items = []
        errors = {}
        for suffix in ["n", "n1", "n2"]:
            if f"annee_{suffix}" in data:
                item_data = {
                    key.rsplit("_", 1)[0]: value
                    for key, value in data.items()
                    if key.endswith(f"_{suffix}")
                }
                item_data['acheteur'] = request.data.get(f'acheteur_{suffix}')
                if not item_data.get('acheteur') or not item_data.get('annee'):
                    continue
                serializer = AddPassifAnglaisSerializer(data=item_data, context={"request": request})
                if serializer.is_valid():
                    instance = serializer.save(created_by=request.user)
                    created_items.append(PassifAnglaisSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        if not created_items:
            return Response({"detail": "Aucune donnée valide à enregistrer."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(created_items, status=status.HTTP_201_CREATED)

class GetPassifAView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, passif_id, *args, **kwargs):
        try:
            passif = PassifA.objects.get(id=passif_id, acheteur_id=acheteur_id)
            serializer = PassifAnglaisSerializer(passif)
            return Response(serializer.data)
        except PassifA.DoesNotExist:
            return Response({"detail": "Passif non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class EditPassifAView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, acheteur_id, passif_id, *args, **kwargs):
        try:
            passif = PassifA.objects.get(id=passif_id, acheteur_id=acheteur_id)
            serializer = EditPassifAnglaisSerializer(passif, data=request.data, partial=True, context={"request": request})
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(PassifAnglaisSerializer(passif).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PassifA.DoesNotExist:
            return Response({"detail": "Passif non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class DeletePassifAView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response({"error": "La liste des IDs est requise."}, status=status.HTTP_400_BAD_REQUEST)
        count, _ = PassifA.objects.filter(id__in=ids, acheteur_id=acheteur_id).delete()
        if count == 0:
            return Response({"error": "Aucun passif trouvé pour les IDs fournis."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": f"{count} passif(s) supprimé(s) avec succès."}, status=status.HTTP_200_OK)

# --- Vues pour la gestion des Comptes de Résultat Anglais (ResultatA) ---

class ListResultatAView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        resultat_list = ResultatA.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")
        paginator = Paginator(resultat_list, 10)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)
        serializer = ResultatAnglaisSerializer(page_obj, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
        }, status=status.HTTP_200_OK)

class AddMultiYearResultatAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        created_items = []
        errors = {}
        for suffix in ["n", "n1", "n2"]:
            if f"annee_{suffix}" in data:
                item_data = {
                    key.rsplit("_", 1)[0]: value
                    for key, value in data.items()
                    if key.endswith(f"_{suffix}")
                }
                item_data['acheteur'] = request.data.get(f'acheteur_{suffix}')
                if not item_data.get('acheteur') or not item_data.get('annee'):
                    continue
                serializer = AddResultatAnglaisSerializer(data=item_data, context={"request": request})
                if serializer.is_valid():
                    instance = serializer.save(created_by=request.user)
                    created_items.append(ResultatAnglaisSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        if not created_items:
            return Response({"detail": "Aucune donnée valide à enregistrer."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(created_items, status=status.HTTP_201_CREATED)

class GetResultatAView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, resultat_id, *args, **kwargs):
        try:
            resultat = ResultatA.objects.get(id=resultat_id, acheteur_id=acheteur_id)
            serializer = ResultatAnglaisSerializer(resultat)
            return Response(serializer.data)
        except ResultatA.DoesNotExist:
            return Response({"detail": "Résultat non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class EditResultatAView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, acheteur_id, resultat_id, *args, **kwargs):
        try:
            resultat = ResultatA.objects.get(id=resultat_id, acheteur_id=acheteur_id)
            serializer = EditResultatAnglaisSerializer(resultat, data=request.data, partial=True, context={"request": request})
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(ResultatAnglaisSerializer(resultat).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ResultatA.DoesNotExist:
            return Response({"detail": "Résultat non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class DeleteResultatAView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response({"error": "La liste des IDs est requise."}, status=status.HTTP_400_BAD_REQUEST)
        count, _ = ResultatA.objects.filter(id__in=ids, acheteur_id=acheteur_id).delete()
        if count == 0:
            return Response({"error": "Aucun résultat trouvé pour les IDs fournis."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": f"{count} résultat(s) supprimé(s) avec succès."}, status=status.HTTP_200_OK)
