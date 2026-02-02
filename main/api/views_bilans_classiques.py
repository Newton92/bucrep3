# Dans votre fichier views_bilans_classiques.py

from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import ActifC, PassifC, ResultatC
from main.serializers import (
    ActifClassiqueSerializer, AddActifClassiqueSerializer, EditActifClassiqueSerializer,
    PassifClassiqueSerializer, AddPassifClassiqueSerializer, EditPassifClassiqueSerializer,
    ResultatClassiqueSerializer, AddResultatClassiqueSerializer, EditResultatClassiqueSerializer,
)

# --- Vues pour la gestion des Actifs Classiques (ActifC) ---

class ListActifCView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        actif_list = ActifC.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")

        paginator = Paginator(actif_list, 10)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)

        serializer = ActifClassiqueSerializer(page_obj, many=True)

        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
        }, status=status.HTTP_200_OK)

class AddMultiYearActifCView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        created_items = []
        errors = {}

        for suffix in ["n", "n1", "n2"]:
            # On vérifie si l'année est fournie pour le suffixe
            if f"annee_{suffix}" in data:
                item_data = {
                    key.rsplit("_", 1)[0]: value
                    for key, value in data.items()
                    if key.endswith(f"_{suffix}")
                }
                item_data['acheteur'] = request.data.get(f'acheteur_{suffix}')
                
                if not item_data.get('acheteur') or not item_data.get('annee'):
                    continue

                serializer = AddActifClassiqueSerializer(data=item_data, context={"request": request})
                if serializer.is_valid():
                    instance = serializer.save(created_by=request.user)
                    created_items.append(ActifClassiqueSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        if not created_items:
            return Response(
                {"detail": "Aucune donnée valide à enregistrer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(created_items, status=status.HTTP_201_CREATED)

class GetActifCView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, actif_id, *args, **kwargs):
        try:
            actif = ActifC.objects.get(id=actif_id)
            serializer = ActifClassiqueSerializer(actif)
            return Response(serializer.data)
        except ActifC.DoesNotExist:
            return Response(
                {"detail": "Actif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

class EditActifCView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, actif_id, *args, **kwargs):
        try:
            actif = ActifC.objects.get(id=actif_id)
            serializer = EditActifClassiqueSerializer(
                actif, data=request.data, partial=True, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(ActifClassiqueSerializer(actif).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ActifC.DoesNotExist:
            return Response(
                {"detail": "Actif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

class DeleteActifCView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"error": "La liste des IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        count, _ = ActifC.objects.filter(id__in=ids).delete()
        if count == 0:
            return Response(
                {"error": "Aucun actif trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"message": f"{count} actif(s) supprimé(s) avec succès."},
            status=status.HTTP_200_OK,
        )

# --- Vues pour la gestion des Passifs Classiques (PassifC) ---

class ListPassifCView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        passif_list = PassifC.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")
        
        paginator = Paginator(passif_list, 10)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)
        
        serializer = PassifClassiqueSerializer(page_obj, many=True)
        
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
        }, status=status.HTTP_200_OK)

class AddMultiYearPassifCView(APIView):
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
                
                serializer = AddPassifClassiqueSerializer(data=item_data, context={"request": request})
                if serializer.is_valid():
                    instance = serializer.save(created_by=request.user)
                    created_items.append(PassifClassiqueSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors
        
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        
        if not created_items:
            return Response(
                {"detail": "Aucune donnée valide à enregistrer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(created_items, status=status.HTTP_201_CREATED)

class GetPassifCView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, passif_id, *args, **kwargs):
        try:
            passif = PassifC.objects.get(id=passif_id)
            serializer = PassifClassiqueSerializer(passif)
            return Response(serializer.data)
        except PassifC.DoesNotExist:
            return Response(
                {"detail": "Passif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

class EditPassifCView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, passif_id, *args, **kwargs):
        try:
            passif = PassifC.objects.get(id=passif_id)
            serializer = EditPassifClassiqueSerializer(
                passif, data=request.data, partial=True, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(PassifClassiqueSerializer(passif).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PassifC.DoesNotExist:
            return Response(
                {"detail": "Passif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

class DeletePassifCView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"error": "La liste des IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        count, _ = PassifC.objects.filter(id__in=ids).delete()
        if count == 0:
            return Response(
                {"error": "Aucun passif trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"message": f"{count} passif(s) supprimé(s) avec succès."},
            status=status.HTTP_200_OK,
        )

# --- Vues pour la gestion du Compte de Résultat Classique (ResultatC) ---

class ListResultatCView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        resultat_list = ResultatC.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")

        paginator = Paginator(resultat_list, 10)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)

        serializer = ResultatClassiqueSerializer(page_obj, many=True)

        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
        }, status=status.HTTP_200_OK)

class AddMultiYearResultatCView(APIView):
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
                
                serializer = AddResultatClassiqueSerializer(data=item_data, context={"request": request})
                if serializer.is_valid():
                    instance = serializer.save(created_by=request.user)
                    created_items.append(ResultatClassiqueSerializer(instance).data)
                else:
                    errors[f"annee_{suffix}"] = serializer.errors

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        if not created_items:
            return Response(
                {"detail": "Aucune donnée valide à enregistrer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(created_items, status=status.HTTP_201_CREATED)

class GetResultatCView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, resultat_id, *args, **kwargs):
        try:
            resultat = ResultatC.objects.get(id=resultat_id)
            serializer = ResultatClassiqueSerializer(resultat)
            return Response(serializer.data)
        except ResultatC.DoesNotExist:
            return Response(
                {"detail": "Résultat non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

class EditResultatCView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, resultat_id, *args, **kwargs):
        try:
            resultat = ResultatC.objects.get(id=resultat_id)
            serializer = EditResultatClassiqueSerializer(
                resultat, data=request.data, partial=True, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(ResultatClassiqueSerializer(resultat).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ResultatC.DoesNotExist:
            return Response(
                {"detail": "Résultat non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

class DeleteResultatCView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"error": "La liste des IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        count, _ = ResultatC.objects.filter(id__in=ids).delete()
        if count == 0:
            return Response(
                {"error": "Aucun résultat trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"message": f"{count} résultat(s) supprimé(s) avec succès."},
            status=status.HTTP_200_OK,
        )