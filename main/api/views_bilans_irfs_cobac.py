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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.db.models import Q


from main.models import ActifIFRS
from main.serializers import ActifIFRSOneSerializer, AddActifIFRSOneSerializer, EditActifIFRSOneSerializer

from main.models import PassifIFRS
from main.serializers import PassifIFRSOneSerializer, AddPassifIFRSOneSerializer, EditPassifIFRSOneSerializer

from main.models import ResultatIFRS
from main.serializers import ResultatIFRSOneSerializer, AddResultatIFRSOneSerializer, EditResultatIFRSOneSerializer

import logging
logger = logging.getLogger(__name__)

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










# views_bilans_ifrs_cobac.py
# Vues spécifiques pour ActifIFRS avec des fonctionnalités supplémentaires (pagination, recherche, etc.)
class ListActifIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        try:
            actif_list = ActifIFRS.objects.filter(
                acheteur_id=acheteur_id
            ).select_related('annee', 'acheteur', 'created_by', 'updated_by').order_by("-annee__annee", "-semestre")
            
            paginator = Paginator(actif_list, 10)
            page_number = request.query_params.get("page", 1)
            page_obj = paginator.get_page(page_number)
            
            serializer = ActifIFRSOneSerializer(page_obj, many=True)
            return Response({
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des actifs IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de la récupération des données."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetActifIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, actif_id, *args, **kwargs):
        try:
            actif = ActifIFRS.objects.select_related(
                'annee', 'acheteur', 'created_by', 'updated_by'
            ).get(id=actif_id, acheteur_id=acheteur_id)
            serializer = ActifIFRSOneSerializer(actif)
            return Response(serializer.data)
        except ActifIFRS.DoesNotExist:
            return Response(
                {"detail": "Actif IFRS non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'actif IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SearchActifIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        
        try:
            actif_list = ActifIFRS.objects.filter(acheteur_id=acheteur_id)
            
            if search_query:
                # Recherche par année
                actif_list = actif_list.filter(
                    Q(annee__annee__icontains=search_query) |
                    Q(type_bilan__icontains=search_query) |
                    Q(semestre__icontains=search_query)
                )
            
            actif_list = actif_list.select_related(
                'annee', 'acheteur', 'created_by', 'updated_by'
            ).order_by("-annee__annee", "-semestre")
            
            serializer = ActifIFRSOneSerializer(actif_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des actifs IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de la recherche."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AddActifIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        try:
            # Ajouter l'acheteur aux données
            data = request.data.copy()
            data['acheteur'] = acheteur_id
            
            serializer = AddActifIFRSOneSerializer(data=data)
            if serializer.is_valid():
                # Vérifier l'unicité (acheteur, année, semestre)
                annee_id = data.get('annee')
                semestre = data.get('semestre')
                type_bilan = data.get('type_bilan')
                
                # Si bilan annuel, semestre doit être None
                if type_bilan == 'annuel':
                    semestre = None
                
                existing_actif = ActifIFRS.objects.filter(
                    acheteur_id=acheteur_id,
                    annee_id=annee_id,
                    semestre=semestre
                ).first()

                if existing_actif:
                    # Upsert : mettre à jour l'enregistrement existant
                    upd_serializer = EditActifIFRSOneSerializer(existing_actif, data=data, partial=False)
                    if upd_serializer.is_valid():
                        actif = upd_serializer.save(updated_by=request.user)
                        return Response(ActifIFRSOneSerializer(actif).data, status=status.HTTP_200_OK)
                    return Response(upd_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                # Sauvegarder avec l'utilisateur connecté
                actif = serializer.save(
                    created_by=request.user,
                    updated_by=request.user
                )

                # Retourner l'objet créé
                return Response(
                    ActifIFRSOneSerializer(actif).data,
                    status=status.HTTP_201_CREATED
                )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de l'actif IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de l'ajout."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EditActifIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, acheteur_id, actif_id, *args, **kwargs):
        try:
            actif = ActifIFRS.objects.get(id=actif_id, acheteur_id=acheteur_id)
            
            # Vérifier si les modifications créent un doublon
            data = request.data.copy()
            annee_id = data.get('annee', actif.annee_id)
            semestre = data.get('semestre', actif.semestre)
            type_bilan = data.get('type_bilan', actif.type_bilan)
            
            # Si bilan annuel, semestre doit être None
            if type_bilan == 'annuel':
                semestre = None
                data['semestre'] = None
            
            # Vérifier s'il existe déjà un bilan pour cette période (exclure l'actuel)
            existing = ActifIFRS.objects.filter(
                acheteur_id=acheteur_id,
                annee_id=annee_id,
                semestre=semestre
            ).exclude(id=actif_id).exists()
            
            if existing:
                return Response(
                    {"error": "Un autre bilan IFRS existe déjà pour cette période."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = EditActifIFRSOneSerializer(
                actif, 
                data=data, 
                partial=True,
                context={"request": request}
            )
            
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(ActifIFRSOneSerializer(actif).data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except ActifIFRS.DoesNotExist:
            return Response(
                {"detail": "Actif IFRS non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la modification de l'actif IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de la modification."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DeleteActifIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        
        if not ids:
            return Response(
                {"error": "La liste des IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Filtrer par acheteur pour plus de sécurité
            count, _ = ActifIFRS.objects.filter(
                id__in=ids, 
                acheteur_id=acheteur_id
            ).delete()
            
            if count == 0:
                return Response(
                    {"error": "Aucun actif IFRS trouvé pour les IDs fournis."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                {"message": f"{count} actif(s) IFRS supprimé(s) avec succès."},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des actifs IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de la suppression."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            


# views_bilans_ifrs_cobac.py
# Vues spécifiques pour PassifIFRS avec des fonctionnalités supplémentaires (pagination, recherche, etc.)
class ListPassifIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        try:
            passif_list = PassifIFRS.objects.filter(
                acheteur_id=acheteur_id
            ).select_related('annee', 'acheteur', 'created_by', 'updated_by').order_by("-annee__annee", "-semestre")
            
            paginator = Paginator(passif_list, 10)
            page_number = request.query_params.get("page", 1)
            page_obj = paginator.get_page(page_number)
            
            serializer = PassifIFRSOneSerializer(page_obj, many=True)
            return Response({
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des passifs IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de la récupération des données."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetPassifIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, passif_id, *args, **kwargs):
        try:
            passif = PassifIFRS.objects.select_related(
                'annee', 'acheteur', 'created_by', 'updated_by'
            ).get(id=passif_id, acheteur_id=acheteur_id)
            serializer = PassifIFRSOneSerializer(passif)
            return Response(serializer.data)
        except PassifIFRS.DoesNotExist:
            return Response(
                {"detail": "Passif IFRS non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du passif IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SearchPassifIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        
        try:
            passif_list = PassifIFRS.objects.filter(acheteur_id=acheteur_id)
            
            if search_query:
                # Recherche par année
                passif_list = passif_list.filter(
                    Q(annee__annee__icontains=search_query) |
                    Q(type_bilan__icontains=search_query) |
                    Q(semestre__icontains=search_query)
                )
            
            passif_list = passif_list.select_related(
                'annee', 'acheteur', 'created_by', 'updated_by'
            ).order_by("-annee__annee", "-semestre")
            
            serializer = PassifIFRSOneSerializer(passif_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des passifs IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de la recherche."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AddPassifIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        try:
            # Ajouter l'acheteur aux données
            data = request.data.copy()
            data['acheteur'] = acheteur_id
            
            serializer = AddPassifIFRSOneSerializer(data=data)
            if serializer.is_valid():
                # Vérifier l'unicité (acheteur, année, semestre)
                annee_id = data.get('annee')
                semestre = data.get('semestre')
                type_bilan = data.get('type_bilan')
                
                # Si bilan annuel, semestre doit être None
                if type_bilan == 'annuel':
                    semestre = None
                
                existing_passif = PassifIFRS.objects.filter(
                    acheteur_id=acheteur_id,
                    annee_id=annee_id,
                    semestre=semestre
                ).first()

                if existing_passif:
                    upd_serializer = EditPassifIFRSOneSerializer(existing_passif, data=data, partial=False)
                    if upd_serializer.is_valid():
                        passif = upd_serializer.save(updated_by=request.user)
                        return Response(PassifIFRSOneSerializer(passif).data, status=status.HTTP_200_OK)
                    return Response(upd_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                # Sauvegarder avec l'utilisateur connecté
                passif = serializer.save(
                    created_by=request.user,
                    updated_by=request.user
                )

                # Retourner l'objet créé
                return Response(
                    PassifIFRSOneSerializer(passif).data,
                    status=status.HTTP_201_CREATED
                )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du passif IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de l'ajout."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EditPassifIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, acheteur_id, passif_id, *args, **kwargs):
        try:
            passif = PassifIFRS.objects.get(id=passif_id, acheteur_id=acheteur_id)
            
            # Vérifier si les modifications créent un doublon
            data = request.data.copy()
            annee_id = data.get('annee', passif.annee_id)
            semestre = data.get('semestre', passif.semestre)
            type_bilan = data.get('type_bilan', passif.type_bilan)
            
            # Si bilan annuel, semestre doit être None
            if type_bilan == 'annuel':
                semestre = None
                data['semestre'] = None
            
            # Vérifier s'il existe déjà un bilan pour cette période (exclure l'actuel)
            existing = PassifIFRS.objects.filter(
                acheteur_id=acheteur_id,
                annee_id=annee_id,
                semestre=semestre
            ).exclude(id=passif_id).exists()
            
            if existing:
                return Response(
                    {"error": "Un autre bilan IFRS (passif) existe déjà pour cette période."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = EditPassifIFRSOneSerializer(
                passif, 
                data=data, 
                partial=True,
                context={"request": request}
            )
            
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(PassifIFRSOneSerializer(passif).data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except PassifIFRS.DoesNotExist:
            return Response(
                {"detail": "Passif IFRS non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la modification du passif IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de la modification."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DeletePassifIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        
        if not ids:
            return Response(
                {"error": "La liste des IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Filtrer par acheteur pour plus de sécurité
            count, _ = PassifIFRS.objects.filter(
                id__in=ids, 
                acheteur_id=acheteur_id
            ).delete()
            
            if count == 0:
                return Response(
                    {"error": "Aucun passif IFRS trouvé pour les IDs fournis."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                {"message": f"{count} passif(s) IFRS supprimé(s) avec succès."},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des passifs IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de la suppression."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            
            
            





# views_bilans_ifrs_cobac.py
# Vues spécifiques pour ResultatIFRS avec des fonctionnalités supplémentaires (pagination, recherche, etc.)
class ListResultatIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        try:
            resultat_list = ResultatIFRS.objects.filter(
                acheteur_id=acheteur_id
            ).select_related('annee', 'acheteur', 'created_by', 'updated_by').order_by("-annee__annee", "-semestre")
            
            paginator = Paginator(resultat_list, 10)
            page_number = request.query_params.get("page", 1)
            page_obj = paginator.get_page(page_number)
            
            serializer = ResultatIFRSOneSerializer(page_obj, many=True)
            return Response({
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des résultats IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de la récupération des données."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetResultatIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, resultat_id, *args, **kwargs):
        try:
            resultat = ResultatIFRS.objects.select_related(
                'annee', 'acheteur', 'created_by', 'updated_by'
            ).get(id=resultat_id, acheteur_id=acheteur_id)
            serializer = ResultatIFRSOneSerializer(resultat)
            return Response(serializer.data)
        except ResultatIFRS.DoesNotExist:
            return Response(
                {"detail": "Compte de résultat IFRS non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du compte de résultat IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SearchResultatIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        
        try:
            resultat_list = ResultatIFRS.objects.filter(acheteur_id=acheteur_id)
            
            if search_query:
                # Recherche par année
                resultat_list = resultat_list.filter(
                    Q(annee__annee__icontains=search_query) |
                    Q(type_bilan__icontains=search_query) |
                    Q(semestre__icontains=search_query)
                )
            
            resultat_list = resultat_list.select_related(
                'annee', 'acheteur', 'created_by', 'updated_by'
            ).order_by("-annee__annee", "-semestre")
            
            serializer = ResultatIFRSOneSerializer(resultat_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des résultats IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de la recherche."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AddResultatIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        try:
            # Ajouter l'acheteur aux données
            data = request.data.copy()
            data['acheteur'] = acheteur_id
            
            serializer = AddResultatIFRSOneSerializer(data=data)
            if serializer.is_valid():
                # Vérifier l'unicité (acheteur, année, semestre)
                annee_id = data.get('annee')
                semestre = data.get('semestre')
                type_bilan = data.get('type_bilan')
                
                # Si bilan annuel, semestre doit être None
                if type_bilan == 'annuel':
                    semestre = None
                
                existing_resultat = ResultatIFRS.objects.filter(
                    acheteur_id=acheteur_id,
                    annee_id=annee_id,
                    semestre=semestre
                ).first()

                if existing_resultat:
                    upd_serializer = EditResultatIFRSOneSerializer(existing_resultat, data=data, partial=False)
                    if upd_serializer.is_valid():
                        resultat = upd_serializer.save(updated_by=request.user)
                        return Response(ResultatIFRSOneSerializer(resultat).data, status=status.HTTP_200_OK)
                    return Response(upd_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                # Sauvegarder avec l'utilisateur connecté
                resultat = serializer.save(
                    created_by=request.user,
                    updated_by=request.user
                )

                # Retourner l'objet créé
                return Response(
                    ResultatIFRSOneSerializer(resultat).data,
                    status=status.HTTP_201_CREATED
                )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du compte de résultat IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de l'ajout."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EditResultatIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, acheteur_id, resultat_id, *args, **kwargs):
        try:
            resultat = ResultatIFRS.objects.get(id=resultat_id, acheteur_id=acheteur_id)
            
            # Vérifier si les modifications créent un doublon
            data = request.data.copy()
            annee_id = data.get('annee', resultat.annee_id)
            semestre = data.get('semestre', resultat.semestre)
            type_bilan = data.get('type_bilan', resultat.type_bilan)
            
            # Si bilan annuel, semestre doit être None
            if type_bilan == 'annuel':
                semestre = None
                data['semestre'] = None
            
            # Vérifier s'il existe déjà un bilan pour cette période (exclure l'actuel)
            existing = ResultatIFRS.objects.filter(
                acheteur_id=acheteur_id,
                annee_id=annee_id,
                semestre=semestre
            ).exclude(id=resultat_id).exists()
            
            if existing:
                return Response(
                    {"error": "Un autre compte de résultat IFRS existe déjà pour cette période."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = EditResultatIFRSOneSerializer(
                resultat, 
                data=data, 
                partial=True,
                context={"request": request}
            )
            
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(ResultatIFRSOneSerializer(resultat).data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except ResultatIFRS.DoesNotExist:
            return Response(
                {"detail": "Compte de résultat IFRS non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la modification du compte de résultat IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de la modification."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DeleteResultatIFRSOneView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        
        if not ids:
            return Response(
                {"error": "La liste des IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Filtrer par acheteur pour plus de sécurité
            count, _ = ResultatIFRS.objects.filter(
                id__in=ids, 
                acheteur_id=acheteur_id
            ).delete()
            
            if count == 0:
                return Response(
                    {"error": "Aucun compte de résultat IFRS trouvé pour les IDs fournis."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                {"message": f"{count} compte(s) de résultat IFRS supprimé(s) avec succès."},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des comptes de résultat IFRS: {e}")
            return Response(
                {"error": "Une erreur est survenue lors de la suppression."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
