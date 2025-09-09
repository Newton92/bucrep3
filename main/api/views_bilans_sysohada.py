# Dans votre fichier views.py

from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import ActifS, PassifS, ResultatS
from main.serializers import (
    ActifSysOhadaSerializer, AddActifSysOhadaSerializer, EditActifSysOhadaSerializer,
    PassifSysOhadaSerializer, AddPassifSysOhadaSerializer, EditPassifSysOhadaSerializer,
    ResultatSysOhadaSerializer, AddResultatSysOhadaSerializer, EditResultatSysOhadaSerializer,
)

# --- Vues pour la gestion des Actifs SYSCOHADA (ActifS) ---

class ListActifSView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        actif_list = ActifS.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")
        paginator = Paginator(actif_list, 10)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)
        serializer = ActifSysOhadaSerializer(page_obj, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
        }, status=status.HTTP_200_OK)

class AddMultiYearActifSView(APIView):
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
                serializer = AddActifSysOhadaSerializer(data=item_data, context={"request": request})
                if serializer.is_valid():
                    instance = serializer.save(created_by=request.user)
                    created_items.append(ActifSysOhadaSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        if not created_items:
            return Response({"detail": "Aucune donnée valide à enregistrer."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(created_items, status=status.HTTP_201_CREATED)

class GetActifSView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, actif_id, *args, **kwargs):
        try:
            actif = ActifS.objects.get(id=actif_id)
            serializer = ActifSysOhadaSerializer(actif)
            return Response(serializer.data)
        except ActifS.DoesNotExist:
            return Response({"detail": "Actif non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class EditActifSView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, actif_id, *args, **kwargs):
        try:
            actif = ActifS.objects.get(id=actif_id)
            serializer = EditActifSysOhadaSerializer(actif, data=request.data, partial=True, context={"request": request})
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(ActifSysOhadaSerializer(actif).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ActifS.DoesNotExist:
            return Response({"detail": "Actif non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class DeleteActifSView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response({"error": "La liste des IDs est requise."}, status=status.HTTP_400_BAD_REQUEST)
        count, _ = ActifS.objects.filter(id__in=ids).delete()
        if count == 0:
            return Response({"error": "Aucun actif trouvé pour les IDs fournis."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": f"{count} actif(s) supprimé(s) avec succès."}, status=status.HTTP_200_OK)

# --- Vues pour la gestion des Passifs SYSCOHADA (PassifS) ---

class ListPassifSView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        passif_list = PassifS.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")
        paginator = Paginator(passif_list, 10)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)
        serializer = PassifSysOhadaSerializer(page_obj, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
        }, status=status.HTTP_200_OK)

class AddMultiYearPassifSView(APIView):
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
                serializer = AddPassifSysOhadaSerializer(data=item_data, context={"request": request})
                if serializer.is_valid():
                    instance = serializer.save(created_by=request.user)
                    created_items.append(PassifSysOhadaSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        if not created_items:
            return Response({"detail": "Aucune donnée valide à enregistrer."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(created_items, status=status.HTTP_201_CREATED)

class GetPassifSView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, passif_id, *args, **kwargs):
        try:
            passif = PassifS.objects.get(id=passif_id)
            serializer = PassifSysOhadaSerializer(passif)
            return Response(serializer.data)
        except PassifS.DoesNotExist:
            return Response({"detail": "Passif non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class EditPassifSView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, passif_id, *args, **kwargs):
        try:
            passif = PassifS.objects.get(id=passif_id)
            serializer = EditPassifSysOhadaSerializer(passif, data=request.data, partial=True, context={"request": request})
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(PassifSysOhadaSerializer(passif).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PassifS.DoesNotExist:
            return Response({"detail": "Passif non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class DeletePassifSView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response({"error": "La liste des IDs est requise."}, status=status.HTTP_400_BAD_REQUEST)
        count, _ = PassifS.objects.filter(id__in=ids).delete()
        if count == 0:
            return Response({"error": "Aucun passif trouvé pour les IDs fournis."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": f"{count} passif(s) supprimé(s) avec succès."}, status=status.HTTP_200_OK)

# --- Vues pour la gestion des Comptes de Résultat SYSCOHADA (ResultatS) ---

class ListResultatSView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        resultat_list = ResultatS.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")
        paginator = Paginator(resultat_list, 10)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)
        serializer = ResultatSysOhadaSerializer(page_obj, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
        }, status=status.HTTP_200_OK)

class AddMultiYearResultatSView(APIView):
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
                serializer = AddResultatSysOhadaSerializer(data=item_data, context={"request": request})
                if serializer.is_valid():
                    instance = serializer.save(created_by=request.user)
                    created_items.append(ResultatSysOhadaSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        if not created_items:
            return Response({"detail": "Aucune donnée valide à enregistrer."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(created_items, status=status.HTTP_201_CREATED)

class GetResultatSView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, resultat_id, *args, **kwargs):
        try:
            resultat = ResultatS.objects.get(id=resultat_id)
            serializer = ResultatSysOhadaSerializer(resultat)
            return Response(serializer.data)
        except ResultatS.DoesNotExist:
            return Response({"detail": "Résultat non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class EditResultatSView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, resultat_id, *args, **kwargs):
        try:
            resultat = ResultatS.objects.get(id=resultat_id)
            serializer = EditResultatSysOhadaSerializer(resultat, data=request.data, partial=True, context={"request": request})
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(ResultatSysOhadaSerializer(resultat).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ResultatS.DoesNotExist:
            return Response({"detail": "Résultat non trouvé."}, status=status.HTTP_404_NOT_FOUND)

class DeleteResultatSView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response({"error": "La liste des IDs est requise."}, status=status.HTTP_400_BAD_REQUEST)
        count, _ = ResultatS.objects.filter(id__in=ids).delete()
        if count == 0:
            return Response({"error": "Aucun résultat trouvé pour les IDs fournis."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": f"{count} résultat(s) supprimé(s) avec succès."}, status=status.HTTP_200_OK)