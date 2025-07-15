# DANS VOTRE FICHIER views.py
# Assurez-vous d'avoir tous les imports nécessaires en haut de votre fichier
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Importer les modèles et serializers IFRS
from main.models import ActifIFRS, PassifIFRS, RatiosIFRS, ResultatIFRS
from main.serializers import (ActifIFRSSerializer, AddActifIFRSSerializer,
                              AddPassifIFRSSerializer,
                              AddResultatIFRSSerializer, PassifIFRSSerializer,
                              RatiosIFRSSerializer, ResultatIFRSSerializer)

# --- FONCTION UTILITAIRE POUR LA GESTION DES RATIOS ---


def update_or_create_ratios(instance):
    """
    Vérifie si les trois états financiers (Actif, Passif, Résultat) pour une
    période donnée existent. Si oui, crée ou met à jour l'objet RatiosIFRS associé.

    :param instance: Une instance de ActifIFRS, PassifIFRS, ou ResultatIFRS.
    """
    params = {
        "acheteur": instance.acheteur,
        "annee": instance.annee,
        "semestre": instance.semestre,
    }

    try:
        actif = ActifIFRS.objects.get(**params)
        passif = PassifIFRS.objects.get(**params)
        resultat = ResultatIFRS.objects.get(**params)

        # Si les 3 existent, on crée ou met à jour le ratio
        RatiosIFRS.objects.update_or_create(
            annee=instance.annee,
            acheteur=instance.acheteur,
            defaults={"actif": actif, "passif": passif, "resultat": resultat},
        )
    except (ActifIFRS.DoesNotExist, PassifIFRS.DoesNotExist, ResultatIFRS.DoesNotExist):
        # Un ou plusieurs composants manquent, on ne fait rien.
        pass


# --- CLASSE DE VUE DE BASE POUR LE CRUD (Optionnel mais recommandé pour DRY) ---


class BaseIFRSView(APIView):
    """Classe de base pour les vues IFRS afin de réduire la redondance."""

    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    add_serializer_class = None

    def get_list(self, request, acheteur_id, *args, **kwargs):
        """Liste les objets pour un acheteur."""
        object_list = self.model.objects.filter(acheteur_id=acheteur_id).order_by(
            "-annee__annee", "-semestre"
        )
        paginator = Paginator(object_list, 10)
        page_number = request.query_params.get("page", 1)
        page_obj = paginator.get_page(page_number)
        serializer = self.serializer_class(page_obj, many=True)
        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
            },
            status=status.HTTP_200_OK,
        )

    def get_detail(self, request, pk, *args, **kwargs):
        """Récupère un objet par son ID."""
        obj = get_object_or_404(self.model, pk=pk)
        serializer = self.serializer_class(obj)
        return Response(serializer.data)

    def update_object(self, request, pk, *args, **kwargs):
        """Met à jour un objet."""
        obj = get_object_or_404(self.model, pk=pk)
        serializer = self.add_serializer_class(
            obj, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            instance = serializer.save()
            update_or_create_ratios(instance)  # Met à jour les ratios
            return Response(self.serializer_class(instance).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete_objects(self, request, *args, **kwargs):
        """Supprime plusieurs objets en bloc."""
        ids = request.data.get("ids", [])
        if not ids:
            return Response(
                {"error": "La liste des IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        count, _ = self.model.objects.filter(id__in=ids).delete()

        if count == 0:
            return Response(
                {
                    "error": f"Aucun {self.model._meta.verbose_name} trouvé pour les IDs fournis."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "message": f"{count} {self.model._meta.verbose_name_plural} supprimé(s) avec succès."
            },
            status=status.HTTP_200_OK,
        )


class MultiYearCreateView(APIView):
    """Vue de base pour la création multi-années."""

    permission_classes = [IsAuthenticated]
    model = None
    serializer_class = None
    add_serializer_class = None

    def post(self, request, *args, **kwargs):
        data = request.data
        created_items = []
        errors = {}

        for suffix in ["n", "n1", "n2"]:
            if f"type_bilan_{suffix}" in data and data.get(f"annee_{suffix}"):
                item_data = {}
                for key, value in data.items():
                    if key.endswith(f"_{suffix}"):
                        base_key = key.rsplit("_", 1)[0]
                        item_data[base_key] = value

                if not item_data.get("acheteur"):
                    continue

                serializer = self.add_serializer_class(
                    data=item_data, context={"request": request}
                )
                if serializer.is_valid():
                    instance = serializer.save()
                    update_or_create_ratios(
                        instance
                    )  # Déclenche la mise à jour des ratios
                    created_items.append(self.serializer_class(instance).data)
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


# --- Vues pour ActifIFRS ---


class ListActifsIFRSView(BaseIFRSView):
    model = ActifIFRS
    serializer_class = ActifIFRSSerializer

    def get(self, request, acheteur_id, *args, **kwargs):
        return super().get_list(request, acheteur_id, *args, **kwargs)


class AddMultiYearActifsIFRSView(MultiYearCreateView):
    model = ActifIFRS
    serializer_class = ActifIFRSSerializer
    add_serializer_class = AddActifIFRSSerializer


class GetActifIFRSView(BaseIFRSView):
    model = ActifIFRS
    serializer_class = ActifIFRSSerializer

    def get(self, request, pk, *args, **kwargs):
        return super().get_detail(request, pk, *args, **kwargs)


class EditActifIFRSView(BaseIFRSView):
    model = ActifIFRS
    serializer_class = ActifIFRSSerializer
    add_serializer_class = AddActifIFRSSerializer

    def put(self, request, pk, *args, **kwargs):
        return super().update_object(request, pk, *args, **kwargs)


class DeleteActifsIFRSView(BaseIFRSView):
    model = ActifIFRS

    def delete(self, request, *args, **kwargs):
        return super().delete_objects(request, *args, **kwargs)


# --- Vues pour PassifIFRS ---


class ListPassifsIFRSView(BaseIFRSView):
    model = PassifIFRS
    serializer_class = PassifIFRSSerializer

    def get(self, request, acheteur_id, *args, **kwargs):
        return super().get_list(request, acheteur_id, *args, **kwargs)


class AddMultiYearPassifsIFRSView(MultiYearCreateView):
    model = PassifIFRS
    serializer_class = PassifIFRSSerializer
    add_serializer_class = AddPassifIFRSSerializer


class GetPassifIFRSView(BaseIFRSView):
    model = PassifIFRS
    serializer_class = PassifIFRSSerializer

    def get(self, request, pk, *args, **kwargs):
        return super().get_detail(request, pk, *args, **kwargs)


class EditPassifIFRSView(BaseIFRSView):
    model = PassifIFRS
    serializer_class = PassifIFRSSerializer
    add_serializer_class = AddPassifIFRSSerializer

    def put(self, request, pk, *args, **kwargs):
        return super().update_object(request, pk, *args, **kwargs)


class DeletePassifsIFRSView(BaseIFRSView):
    model = PassifIFRS

    def delete(self, request, *args, **kwargs):
        return super().delete_objects(request, *args, **kwargs)


# --- Vues pour ResultatIFRS ---


class ListResultatsIFRSView(BaseIFRSView):
    model = ResultatIFRS
    serializer_class = ResultatIFRSSerializer

    def get(self, request, acheteur_id, *args, **kwargs):
        return super().get_list(request, acheteur_id, *args, **kwargs)


class AddMultiYearResultatsIFRSView(MultiYearCreateView):
    model = ResultatIFRS
    serializer_class = ResultatIFRSSerializer
    add_serializer_class = AddResultatIFRSSerializer


class GetResultatIFRSView(BaseIFRSView):
    model = ResultatIFRS
    serializer_class = ResultatIFRSSerializer

    def get(self, request, pk, *args, **kwargs):
        return super().get_detail(request, pk, *args, **kwargs)


class EditResultatIFRSView(BaseIFRSView):
    model = ResultatIFRS
    serializer_class = ResultatIFRSSerializer
    add_serializer_class = AddResultatIFRSSerializer

    def put(self, request, pk, *args, **kwargs):
        return super().update_object(request, pk, *args, **kwargs)


class DeleteResultatsIFRSView(BaseIFRSView):
    model = ResultatIFRS

    def delete(self, request, *args, **kwargs):
        return super().delete_objects(request, *args, **kwargs)


# --- Vues pour RatiosIFRS (Lecture Seule) ---


class ListRatiosIFRSView(BaseIFRSView):
    model = RatiosIFRS
    serializer_class = RatiosIFRSSerializer

    def get(self, request, acheteur_id, *args, **kwargs):
        return super().get_list(request, acheteur_id, *args, **kwargs)


class GetRatioIFRSView(BaseIFRSView):
    model = RatiosIFRS
    serializer_class = RatiosIFRSSerializer

    def get(self, request, pk, *args, **kwargs):
        return super().get_detail(request, pk, *args, **kwargs)
