# api_views.py
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.db import transaction

from django.db.models import Q, Count, Sum  # Ajouter Sum ici
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from decimal import Decimal, InvalidOperation
from rest_framework import generics
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum, DecimalField
from django.db.models.functions import Coalesce
# views.py
from django.db.models import Q, Sum, Avg, Max, Min, Count
from django.db.models.functions import Coalesce
from django.db.models import DecimalField

from django.core.cache import cache
import logging
logger = logging.getLogger(__name__)

from django.contrib.auth import get_user_model

User = get_user_model()


from main.serializers import *

# === Fonctions utiles === #

class StandardPagination(PageNumberPagination):
    """
    Pagination standard pour toutes les API
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        Retourne une réponse paginée formatée
        """
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


def str_to_bool(value):
    return value.lower() in ("true", "1", "t")


# === Vues Modules Acheteur === #


class ListAcheteurResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        devise = request.query_params.get("devise", "")
        capital_social_min = request.query_params.get("capital_social_min", "")
        capital_social_max = request.query_params.get("capital_social_max", "")

        # Validate and convert query parameters
        try:
            capital_social_min = (
                decimal.Decimal(capital_social_min) if capital_social_min else None
            )
            capital_social_max = (
                decimal.Decimal(capital_social_max) if capital_social_max else None
            )
        except decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de capital_social_min et capital_social_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        resume_list = Resume.objects.filter(
            acheteur_id=acheteur_id, devise__nom__icontains=devise
        ).order_by("-created_at")

        if capital_social_min is not None:
            resume_list = resume_list.filter(capital_social__gte=capital_social_min)

        if capital_social_max is not None:
            resume_list = resume_list.filter(capital_social__lte=capital_social_max)

        paginator = Paginator(resume_list, 10)  # 10 résumés par page
        resume_page = paginator.get_page(page_number)
        serializer = ResumeSerializer(resume_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": resume_page.has_next(),
                "previous": resume_page.has_previous(),
            }
        )


class SearchAcheteurResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resume_list = Resume.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(capital_social__icontains=search_term)
                | Q(chiffre_affaire__icontains=search_term)
                | Q(resultat_net__icontains=search_term)
                | Q(capitaux_propre__icontains=search_term)
                | Q(nombre_employe__icontains=search_term)
                | Q(commentaire__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(resume_list, 10)  # 10 résumés par page
        page_number = request.query_params.get("page", 1)
        resume_page = paginator.get_page(page_number)
        serializer = ResumeSerializer(resume_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": resume_page.has_next(),
                "previous": resume_page.has_previous(),
            }
        )


class AddAcheteurResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        # Créez une copie modifiable de request.data
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        # Ajouter l'utilisateur connecté comme créateur
        data["created_by"] = request.user.id
        data["updated_by"] = request.user.id

        serializer = AddResumeSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, resume_id, *args, **kwargs):
        resume = Resume.objects.filter(id=resume_id, acheteur_id=acheteur_id).first()
        if not resume:
            return Response(
                {"detail": "Résumé non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetResumeSerializer(resume)
        return Response(serializer.data)

    def post(self, request, acheteur_id, resume_id, *args, **kwargs):
        resume = Resume.objects.filter(id=resume_id, acheteur_id=acheteur_id).first()
        if not resume:
            return Response(
                {"detail": "Résumé non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        # Ajouter l'utilisateur connecté comme modificateur
        data = request.data.copy()
        data["updated_by"] = request.user.id

        serializer = EditResumeSerializer(resume, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resumes = Resume.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not resumes.exists():
            return Response(
                {"error": "Aucun résumé trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = resumes.delete()
        return Response(
            {"message": f"{count} résumés supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class AcheteurResumeView(APIView):
    """
    API pour gérer le résumé unique d'un acheteur
    Méthodes: GET, POST (create/update), DELETE
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère le résumé de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            resume = Resume.objects.get(acheteur=acheteur)
            serializer = GetResumeSerializer(resume)
            return Response(serializer.data)
        except Resume.DoesNotExist:
            return Response({
                "message": "Aucun résumé trouvé pour cet acheteur",
                "acheteur_id": acheteur_id
            }, status=status.HTTP_404_NOT_FOUND)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée ou met à jour le résumé de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si un résumé existe déjà
        try:
            resume = Resume.objects.get(acheteur=acheteur)
            print(resume)
            serializer = EditResumeSerializer(resume, data=request.data, partial=True)
            action = "mis à jour"
        except Resume.DoesNotExist:
            # Créez une copie modifiable de request.data
            data = request.data.copy()
            data["acheteur"] = acheteur_id
            print(data)

            serializer = AddResumeSerializer(data=data)
            print(serializer)
            action = "créé"
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": f"Résumé {action} avec succès",
                "data": serializer.data
            }, status=status.HTTP_200_OK if action == "mis à jour" else status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime le résumé de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            resume = Resume.objects.get(acheteur=acheteur)
            resume.delete()
            return Response({
                "message": "Résumé supprimé avec succès"
            }, status=status.HTTP_200_OK)
        except Resume.DoesNotExist:
            return Response({
                "message": "Aucun résumé à supprimer"
            }, status=status.HTTP_404_NOT_FOUND)






class ListAcheteurRiskRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        risk_rating_list = RiskRating.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(interpretation__icontains=search_term)
                | Q(analyse__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(risk_rating_list, 10)  # 10 évaluations par page
        risk_rating_page = paginator.get_page(page_number)
        serializer = RiskRatingSerializer(risk_rating_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": risk_rating_page.has_next(),
                "previous": risk_rating_page.has_previous(),
            }
        )



class SearchAcheteurRiskRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        risk_rating_list = RiskRating.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(interpretation__icontains=search_term)
                | Q(analyse__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(risk_rating_list, 10)  # 10 évaluations par page
        page_number = request.query_params.get("page", 1)
        risk_rating_page = paginator.get_page(page_number)
        serializer = RiskRatingSerializer(risk_rating_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": risk_rating_page.has_next(),
                "previous": risk_rating_page.has_previous(),
            }
        )



class AddAcheteurRiskRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        # Convertir les champs booléens
        boolean_fields = [
            'remboursabilite', 'situation_liquidite', 'performance_rentabilite',
            'perspective_secteur', 'qualite_information_analyse', 'existence_garantie',
            'terme_financier_duree_pret', 'mesure_propre_soutenir_credit'
        ]
        for field in boolean_fields:
            if field in data:
                data[field] = data[field].lower() == 'true'  # Convertit "true" en True, "false" en False

        serializer = AddRiskRatingSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def validate(self, data):
        print("=== DONNÉES REÇUES ===")
        print(f"cotation_du_risque: {data.get('cotation_du_risque')}")
        print(f"indice_du_risque: {data.get('indice_du_risque')}")
        print(f"Type cotation: {type(data.get('cotation_du_risque'))}")
        print(f"Type indice: {type(data.get('indice_du_risque'))}")

        # Vérifiez que les valeurs sont bien dans les choix autorisés
        if data.get('cotation_du_risque') not in dict(RISK_RATING_CHOICES):
            raise serializers.ValidationError(f"'{data.get('cotation_du_risque')}' n'est pas un choix valide pour cotation_du_risque.")

        if data.get('indice_du_risque') not in dict(RISK_INDEX_CHOICES):
            raise serializers.ValidationError(f"'{data.get('indice_du_risque')}' n'est pas un choix valide pour indice_du_risque.")

        return data



class EditAcheteurRiskRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, risk_rating_id, *args, **kwargs):
        risk_rating = RiskRating.objects.filter(
            id=risk_rating_id, acheteur_id=acheteur_id
        ).first()
        if not risk_rating:
            return Response(
                {"detail": "Évaluation de risque non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetRiskRatingSerializer(risk_rating)
        return Response(serializer.data)

    def post(self, request, acheteur_id, risk_rating_id, *args, **kwargs):
        risk_rating = RiskRating.objects.filter(
            id=risk_rating_id, acheteur_id=acheteur_id
        ).first()
        if not risk_rating:
            return Response(
                {"detail": "Évaluation de risque non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditRiskRatingSerializer(
            risk_rating, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurRiskRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        risk_ratings = RiskRating.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not risk_ratings.exists():
            return Response(
                {"error": "Aucune évaluation de risque trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = risk_ratings.delete()
        return Response(
            {"message": f"{count} évaluations de risque supprimées avec succès."},
            status=status.HTTP_200_OK,
        )    
        
        
class AcheteurRiskRatingView(APIView):
    """
    API pour gérer l'évaluation de risque unique d'un acheteur
    Méthodes: GET, POST (create/update), DELETE
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère l'évaluation de risque de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            risk_rating = RiskRating.objects.get(acheteur=acheteur)
            serializer = GetRiskRatingSerializer(risk_rating)
            return Response(serializer.data)
        except RiskRating.DoesNotExist:
            return Response({
                "message": "Aucune évaluation de risque trouvée pour cet acheteur",
                "acheteur_id": acheteur_id
            }, status=status.HTTP_404_NOT_FOUND)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée ou met à jour l'évaluation de risque de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si une évaluation existe déjà
        try:
            risk_rating = RiskRating.objects.get(acheteur=acheteur)
            serializer = EditRiskRatingSerializer(
                risk_rating, data=request.data, partial=True
            )
            action = "mis à jour"
        except RiskRating.DoesNotExist:
            data = request.data.copy()
            data["acheteur"] = acheteur_id

            # Convertir les champs booléens
            boolean_fields = [
                'remboursabilite', 'situation_liquidite', 'performance_rentabilite',
                'perspective_secteur', 'qualite_information_analyse', 'existence_garantie',
                'terme_financier_duree_pret', 'mesure_propre_soutenir_credit'
            ]
            for field in boolean_fields:
                if field in data:
                    data[field] = data[field].lower() == 'true'  # Convertit "true" en True, "false" en False

            serializer = AddRiskRatingSerializer(data=data)
            action = "créé"
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": f"Évaluation de risque {action} avec succès",
                "data": serializer.data
            }, status=status.HTTP_200_OK if action == "mis à jour" else status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime l'évaluation de risque de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            risk_rating = RiskRating.objects.get(acheteur=acheteur)
            risk_rating.delete()
            return Response({
                "message": "Évaluation de risque supprimée avec succès"
            }, status=status.HTTP_200_OK)
        except RiskRating.DoesNotExist:
            return Response({
                "message": "Aucune évaluation de risque à supprimer"
            }, status=status.HTTP_404_NOT_FOUND)




class ListAcheteurDataSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        date_creation = request.query_params.get("date_creation", "")
        date_registre = request.query_params.get("date_registre", "")

        donnees_list = DonneesEnregistrement.objects.filter(
            acheteur_id=acheteur_id,
            date_creation__icontains=date_creation,
            date_registre__icontains=date_registre,
        ).order_by("-created_at")

        paginator = Paginator(donnees_list, 10)  # 10 enregistrements par page
        donnees_page = paginator.get_page(page_number)
        serializer = DonneesEnregistrementSerializer(donnees_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": donnees_page.has_next(),
                "previous": donnees_page.has_previous(),
            }
        )


class SearchAcheteurDataSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        donnees_list = DonneesEnregistrement.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(numero_registre_commerce__icontains=search_term)
                | Q(numero_fiscale__icontains=search_term)
                | Q(commentaire__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(donnees_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        donnees_page = paginator.get_page(page_number)
        serializer = DonneesEnregistrementSerializer(donnees_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": donnees_page.has_next(),
                "previous": donnees_page.has_previous(),
            }
        )


class AddAcheteurDataSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        # Créez une copie modifiable de request.data
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddDonneesEnregistrementSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurDataSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, donnee_enregistrement_id, *args, **kwargs):
        donnee = DonneesEnregistrement.objects.filter(
            id=donnee_enregistrement_id, acheteur_id=acheteur_id
        ).first()
        if not donnee:
            return Response(
                {"detail": "Donnée d'enregistrement non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetDonneesEnregistrementSerializer(donnee)
        return Response(serializer.data)

    def put(self, request, acheteur_id, donnee_enregistrement_id, *args, **kwargs):
        donnee = DonneesEnregistrement.objects.filter(
            id=donnee_enregistrement_id, acheteur_id=acheteur_id
        ).first()
        if not donnee:
            return Response(
                {"detail": "Donnée d'enregistrement non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditDonneesEnregistrementSerializer(
            donnee, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurDataSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        donnees = DonneesEnregistrement.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not donnees.exists():
            return Response(
                {
                    "error": "Aucune donnée d'enregistrement trouvée pour les IDs fournis."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = donnees.delete()
        return Response(
            {"message": f"{count} données d'enregistrement supprimées avec succès."},
            status=status.HTTP_200_OK,
        )


class AcheteurDonneesEnregistrementView(APIView):
    """
    API pour gérer les données d'enregistrement unique d'un acheteur
    Méthodes: GET, POST (create/update), DELETE
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère les données d'enregistrement de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            data_save = DonneesEnregistrement.objects.get(acheteur=acheteur)
            serializer = GetDonneesEnregistrementSerializer(data_save)
            return Response(serializer.data)
        except DonneesEnregistrement.DoesNotExist:
            return Response({
                "message": "Aucune donnée d'enregistrement trouvée pour cet acheteur",
                "acheteur_id": acheteur_id
            }, status=status.HTTP_404_NOT_FOUND)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée ou met à jour les données d'enregistrement de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si des données existent déjà
        try:
            data_save = DonneesEnregistrement.objects.get(acheteur=acheteur)
            serializer = EditDonneesEnregistrementSerializer(
                data_save, 
                data=request.data, 
                partial=True,
                context={'request': request}
            )
            action = "mis à jour"
        except DonneesEnregistrement.DoesNotExist:
            data = request.data.copy()
            data["acheteur"] = acheteur_id
            # ⭐ AJOUT : Enregistrer l'utilisateur qui crée
            data["created_by"] = request.user.id
            
            serializer = AddDonneesEnregistrementSerializer(
                data=data,
                context={'request': request}
            )
            action = "créé"
        
        if serializer.is_valid():
            # ⭐ AJOUT : Enregistrer qui a modifié
            instance = serializer.save()
            if action == "mis à jour":
                instance.updated_by = request.user
                instance.save()
            
            return Response({
                "message": f"Données d'enregistrement {action} avec succès",
                "data": GetDonneesEnregistrementSerializer(instance).data
            }, status=status.HTTP_200_OK if action == "mis à jour" else status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime les données d'enregistrement de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            data_save = DonneesEnregistrement.objects.get(acheteur=acheteur)
            data_save.delete()
            return Response({
                "message": "Données d'enregistrement supprimées avec succès"
            }, status=status.HTTP_200_OK)
        except DonneesEnregistrement.DoesNotExist:
            return Response({
                "message": "Aucune donnée d'enregistrement à supprimer"
            }, status=status.HTTP_404_NOT_FOUND)







class ListAcheteurTendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        tendances_list = Tendance.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            tendances_list = tendances_list.filter(
                Q(presse_media__icontains=search_term)
                | Q(principaux_concurrent__icontains=search_term)
                | Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(tendances_list, 10)  # 10 enregistrements par page
        tendances_page = paginator.get_page(page_number)
        serializer = TendanceSerializer(tendances_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": tendances_page.has_next(),
                "previous": tendances_page.has_previous(),
            }
        )


class SearchAcheteurTendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tendances_list = Tendance.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(presse_media__icontains=search_term)
                | Q(principaux_concurrent__icontains=search_term)
                | Q(commentaire__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(tendances_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        tendances_page = paginator.get_page(page_number)
        serializer = TendanceSerializer(tendances_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": tendances_page.has_next(),
                "previous": tendances_page.has_previous(),
            }
        )


class AddAcheteurTendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddTendanceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurTendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, tendance_id, *args, **kwargs):
        tendance = Tendance.objects.filter(
            id=tendance_id, acheteur_id=acheteur_id
        ).first()
        if not tendance:
            return Response(
                {"detail": "Tendance non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetTendanceSerializer(tendance)
        return Response(serializer.data)

    def put(self, request, acheteur_id, tendance_id, *args, **kwargs):
        tendance = Tendance.objects.filter(
            id=tendance_id, acheteur_id=acheteur_id
        ).first()
        if not tendance:
            return Response(
                {"detail": "Tendance non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditTendanceSerializer(tendance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurTendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tendances = Tendance.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not tendances.exists():
            return Response(
                {"error": "Aucune tendance trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = tendances.delete()
        return Response(
            {"message": f"{count} tendances supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
              
        
class AcheteurTendanceView(APIView):
    """
    API pour gérer la tendance unique d'un acheteur
    Méthodes: GET, POST (create/update), DELETE
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la tendance de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            tendance = Tendance.objects.get(acheteur=acheteur)
            serializer = GetTendanceSerializer(tendance)
            return Response(serializer.data)
        except Tendance.DoesNotExist:
            return Response({
                "message": "Aucune tendance trouvée pour cet acheteur",
                "acheteur_id": acheteur_id
            }, status=status.HTTP_404_NOT_FOUND)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée ou met à jour la tendance de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si une tendance existe déjà
        try:
            tendance = Tendance.objects.get(acheteur=acheteur)
            serializer = EditTendanceSerializer(
                tendance, 
                data=request.data, 
                partial=True,
                context={'request': request}
            )
            action = "mise à jour"
        except Tendance.DoesNotExist:
            data = request.data.copy()
            data["acheteur"] = acheteur_id
            # ⭐ AJOUT : Enregistrer l'utilisateur qui crée
            data["created_by"] = request.user.id
            
            serializer = AddTendanceSerializer(
                data=data,
                context={'request': request}
            )
            action = "créée"
        
        if serializer.is_valid():
            # ⭐ AJOUT : Enregistrer qui a modifié
            instance = serializer.save()
            if action == "mise à jour":
                instance.updated_by = request.user
                instance.save()
            
            return Response({
                "message": f"Tendance {action} avec succès",
                "data": GetTendanceSerializer(instance).data
            }, status=status.HTTP_200_OK if action == "mise à jour" else status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime la tendance de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            tendance = Tendance.objects.get(acheteur=acheteur)
            tendance.delete()
            return Response({
                "message": "Tendance supprimée avec succès"
            }, status=status.HTTP_200_OK)
        except Tendance.DoesNotExist:
            return Response({
                "message": "Aucune tendance à supprimer"
            }, status=status.HTTP_404_NOT_FOUND)







class ListAcheteurResponsableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        responsables_list = ResponsableAcheteur.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            responsables_list = responsables_list.filter(
                Q(nom__icontains=search_term)
                | Q(prenom__icontains=search_term)
                | Q(poste__icontains=search_term)
                | Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(responsables_list, 10)  # 10 enregistrements par page
        responsables_page = paginator.get_page(page_number)
        serializer = ResponsableAcheteurSerializer(responsables_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": responsables_page.has_next(),
                "previous": responsables_page.has_previous(),
            }
        )


class SearchAcheteurResponsableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        responsables_list = ResponsableAcheteur.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(nom__icontains=search_term)
                | Q(prenom__icontains=search_term)
                | Q(poste__icontains=search_term)
                | Q(commentaire__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(responsables_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        responsables_page = paginator.get_page(page_number)
        serializer = ResponsableAcheteurSerializer(responsables_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": responsables_page.has_next(),
                "previous": responsables_page.has_previous(),
            }
        )


class AddAcheteurResponsableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddResponsableAcheteurSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurResponsableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, responsable_id, *args, **kwargs):
        responsable = ResponsableAcheteur.objects.filter(
            id=responsable_id, acheteur_id=acheteur_id
        ).first()
        if not responsable:
            return Response(
                {"detail": "Responsable non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetResponsableAcheteurSerializer(responsable)
        return Response(serializer.data)

    def put(self, request, acheteur_id, responsable_id, *args, **kwargs):
        responsable = ResponsableAcheteur.objects.filter(
            id=responsable_id, acheteur_id=acheteur_id
        ).first()
        if not responsable:
            return Response(
                {"detail": "Responsable non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditResponsableAcheteurSerializer(
            responsable, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurResponsableView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        responsables = ResponsableAcheteur.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not responsables.exists():
            return Response(
                {"error": "Aucun responsable trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = responsables.delete()
        return Response(
            {"message": f"{count} responsables supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class ResponsablePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data,
            'next': self.page.has_next(),
            'previous': self.page.has_previous(),
            'start_index': self.page.start_index(),
            'end_index': self.page.end_index()
        })


class AcheteurResponsableListView(APIView):
    """
    API pour gérer la liste des responsables d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = ResponsablePagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def log_activity(self, request, action_type, object_id, object_type, details):
        """Enregistre une activité dans le log"""
        ActivityLog.objects.create(
            user=request.user,
            action_type=action_type,
            object_id=object_id,
            object_type=object_type,
            details=details,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get(self, request, acheteur_id):
        """Récupère la liste paginée des responsables avec recherche"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Paramètres de recherche et filtrage
        search_term = request.query_params.get('search', '')
        sexe = request.query_params.get('sexe', '')
        poste = request.query_params.get('poste', '')
        
        # Construction de la requête
        responsables = ResponsableAcheteur.objects.filter(
            acheteur=acheteur
        ).select_related('couleur_commentaire')
        
        # Filtres
        if sexe:
            responsables = responsables.filter(Sexe=sexe)
        if poste:
            responsables = responsables.filter(poste=poste)
        
        # Recherche
        if search_term:
            responsables = responsables.filter(
                Q(nom__icontains=search_term) |
                Q(prenom__icontains=search_term) |
                Q(poste__icontains=search_term) |
                Q(nationalite__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )
        
        # Tri
        sort_by = request.query_params.get('sort_by', '-created_at')
        if sort_by in ['nom', 'prenom', 'poste', 'created_at']:
            responsables = responsables.order_by(sort_by)
        else:
            responsables = responsables.order_by('-created_at')
        
        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(responsables, request)
        
        if page is not None:
            serializer = ResponsableAcheteurListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = ResponsableAcheteurListSerializer(responsables, many=True)
        return Response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Ajoute un nouveau responsable"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si un responsable avec le même nom et prénom existe déjà
        nom = request.data.get('nom', '').strip()
        prenom = request.data.get('prenom', '').strip()
        
        if nom and prenom:
            existe_deja = ResponsableAcheteur.objects.filter(
                acheteur=acheteur,
                nom__iexact=nom,
                prenom__iexact=prenom
            ).exists()
            
            if existe_deja:
                return Response({
                    'error': f"Un responsable avec le nom {nom} {prenom} existe déjà."
                }, status=status.HTTP_409_CONFLICT)
        
        # Ajouter l'acheteur aux données
        data = request.data.copy()
        data['acheteur'] = acheteur_id
        
        serializer = AddResponsableAcheteurSerializer(data=data)
        if serializer.is_valid():
            responsable = serializer.save()
            
            # Log d'activité
            self.log_activity(
                request=request,
                action_type='CREATE_RESPONSABLE',
                object_id=responsable.id,
                object_type='ResponsableAcheteur',
                details=f"Ajout du responsable {responsable.nom} {responsable.prenom} pour l'acheteur {acheteur.nom} ({acheteur.code})"
            )
            
            return Response({
                'message': 'Responsable ajouté avec succès',
                'data': GetResponsableAcheteurSerializer(responsable).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id):
        """Supprime un ou plusieurs responsables"""
        acheteur = self.get_acheteur(acheteur_id)
        
        responsable_ids = request.data.get('ids', [])
        if not isinstance(responsable_ids, list) or not responsable_ids:
            return Response(
                {'error': 'Une liste d\'IDs est requise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer les responsables à supprimer
        responsables = ResponsableAcheteur.objects.filter(
            id__in=responsable_ids,
            acheteur=acheteur
        )
        
        if not responsables.exists():
            return Response(
                {'error': 'Aucun responsable trouvé pour les IDs fournis'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Log d'activité pour chaque responsable avant suppression
        responsables_details = []
        for resp in responsables:
            responsables_details.append({
                'id': resp.id,
                'nom': resp.nom,
                'prenom': resp.prenom
            })
            
            # Log d'activité
            self.log_activity(
                request=request,
                action_type='DELETE_RESPONSABLE',
                object_id=resp.id,
                object_type='ResponsableAcheteur',
                details=f"Suppression du responsable {resp.nom} {resp.prenom} de l'acheteur {acheteur.nom}"
            )
        
        # Suppression
        count = responsables.count()
        responsables.delete()
        
        return Response({
            'message': f'{count} responsable(s) supprimé(s) avec succès',
            'count': count
        })


class AcheteurResponsableDetailView(APIView):
    """
    API pour gérer un responsable spécifique d'un acheteur
    Méthodes: GET (détail), PUT (mise à jour)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def log_activity(self, request, action_type, object_id, object_type, details):
        """Enregistre une activité dans le log"""
        ActivityLog.objects.create(
            user=request.user,
            action_type=action_type,
            object_id=object_id,
            object_type=object_type,
            details=details,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get(self, request, acheteur_id, responsable_id):
        """Récupère les détails d'un responsable spécifique"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            responsable = ResponsableAcheteur.objects.get(
                id=responsable_id,
                acheteur=acheteur
            )
        except ResponsableAcheteur.DoesNotExist:
            return Response(
                {'error': 'Responsable non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = GetResponsableAcheteurSerializer(responsable)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, responsable_id):
        """Met à jour un responsable existant"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            responsable = ResponsableAcheteur.objects.get(
                id=responsable_id,
                acheteur=acheteur
            )
        except ResponsableAcheteur.DoesNotExist:
            return Response(
                {'error': 'Responsable non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier les doublons (sauf pour le responsable en cours)
        nom = request.data.get('nom', responsable.nom).strip()
        prenom = request.data.get('prenom', responsable.prenom).strip()
        
        doublon = ResponsableAcheteur.objects.filter(
            acheteur=acheteur,
            nom__iexact=nom,
            prenom__iexact=prenom
        ).exclude(id=responsable_id).exists()
        
        if doublon:
            return Response({
                'error': f"Un autre responsable avec le nom {nom} {prenom} existe déjà."
            }, status=status.HTTP_409_CONFLICT)
        
        # Sauvegarder les anciennes valeurs pour le log
        old_values = {
            'nom': responsable.nom,
            'prenom': responsable.prenom,
            'poste': responsable.poste,
            'Sexe': responsable.Sexe,
            'nationalite': responsable.nationalite,
            'commentaire': responsable.commentaire
        }
        
        serializer = EditResponsableAcheteurSerializer(
            responsable,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            updated_responsable = serializer.save()
            
            # Détecter les changements pour le log
            changes = []
            new_values = serializer.validated_data
            
            for field in ['nom', 'prenom', 'poste', 'Sexe', 'nationalite', 'commentaire']:
                old_value = old_values.get(field)
                if field in new_values and new_values[field] != old_value:
                    old_val = str(old_value)[:50] + ('...' if len(str(old_value)) > 50 else '')
                    new_val = str(new_values[field])[:50] + ('...' if len(str(new_values[field])) > 50 else '')
                    changes.append(f"{field}: '{old_val}' → '{new_val}'")
            
            # Log d'activité
            details = f"Mise à jour du responsable {responsable.nom} {responsable.prenom}"
            if changes:
                details += f" - Changements: {', '.join(changes)}"
            
            self.log_activity(
                request=request,
                action_type='UPDATE_RESPONSABLE',
                object_id=responsable.id,
                object_type='ResponsableAcheteur',
                details=details
            )
            
            return Response({
                'message': 'Responsable mis à jour avec succès',
                'data': GetResponsableAcheteurSerializer(updated_responsable).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)








class ListAcheteurAntecedentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        antecedents_list = AntecedantsJuridique.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            antecedents_list = antecedents_list.filter(
                Q(dossier_faillite__icontains=search_term)
                | Q(jugement_cour__icontains=search_term)
                | Q(antecedant_redressement__icontains=search_term)
                | Q(autre__icontains=search_term)
                | Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(antecedents_list, 10)  # 10 enregistrements par page
        antecedents_page = paginator.get_page(page_number)
        serializer = AntecedantsJuridiqueSerializer(antecedents_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": antecedents_page.has_next(),
                "previous": antecedents_page.has_previous(),
            }
        )


class SearchAcheteurAntecedentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        antecedents_list = AntecedantsJuridique.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(dossier_faillite__icontains=search_term)
                | Q(jugement_cour__icontains=search_term)
                | Q(antecedant_redressement__icontains=search_term)
                | Q(autre__icontains=search_term)
                | Q(commentaire__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(antecedents_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        antecedents_page = paginator.get_page(page_number)
        serializer = AntecedantsJuridiqueSerializer(antecedents_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": antecedents_page.has_next(),
                "previous": antecedents_page.has_previous(),
            }
        )


class AddAcheteurAntecedentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddAntecedantsJuridiqueSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurAntecedentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, antecedent_id, *args, **kwargs):
        antecedent = AntecedantsJuridique.objects.filter(
            id=antecedent_id, acheteur_id=acheteur_id
        ).first()
        if not antecedent:
            return Response(
                {"detail": "Antécédent non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetAntecedantsJuridiqueSerializer(antecedent)
        return Response(serializer.data)

    def put(self, request, acheteur_id, antecedent_id, *args, **kwargs):
        antecedent = AntecedantsJuridique.objects.filter(
            id=antecedent_id, acheteur_id=acheteur_id
        ).first()
        if not antecedent:
            return Response(
                {"detail": "Antécédent non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditAntecedantsJuridiqueSerializer(
            antecedent, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurAntecedentView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        antecedents = AntecedantsJuridique.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not antecedents.exists():
            return Response(
                {"error": "Aucun antécédent trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = antecedents.delete()
        return Response(
            {"message": f"{count} antécédents supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
        
        

class AntecedentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data,
            'next': self.page.has_next(),
            'previous': self.page.has_previous(),
            'start_index': self.page.start_index(),
            'end_index': self.page.end_index()
        })



class AcheteurAntecedentListView(APIView):
    """
    API pour gérer la liste des antécédents juridiques d'un acheteur
    Méthodes: GET (liste), POST (création), DELETE (suppression multiple)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = AntecedentPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def log_activity(self, request, action_type, object_id, object_type, details):
        """Enregistre une activité dans le log"""
        ActivityLog.objects.create(
            user=request.user,
            action_type=action_type,
            object_id=object_id,
            object_type=object_type,
            details=details,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get(self, request, acheteur_id):
        """Récupère la liste paginée des antécédents avec recherche"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Paramètres de recherche et filtrage
        search_term = request.query_params.get('search', '')
        type_filter = request.query_params.get('type', '')
        
        # Construction de la requête
        antecedents = AntecedantsJuridique.objects.filter(
            acheteur=acheteur
        ).select_related('couleur_commentaire')
        
        # Filtre par type
        if type_filter:
            if type_filter == 'faillite':
                antecedents = antecedents.exclude(dossier_faillite='')
            elif type_filter == 'jugement':
                antecedents = antecedents.exclude(jugement_cour='')
            elif type_filter == 'redressement':
                antecedents = antecedents.exclude(antecedant_redressement='')
            elif type_filter == 'autre':
                antecedents = antecedents.exclude(Autre='')
            elif type_filter == 'avec_commentaire':
                antecedents = antecedents.exclude(commentaire='')
        
        # Recherche
        if search_term:
            antecedents = antecedents.filter(
                Q(dossier_faillite__icontains=search_term) |
                Q(jugement_cour__icontains=search_term) |
                Q(antecedant_redressement__icontains=search_term) |
                Q(Autre__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )
        
        # Tri
        sort_by = request.query_params.get('sort_by', '-created_at')
        if sort_by in ['dossier_faillite', 'jugement_cour', 'antecedant_redressement', 'Autre', 'created_at']:
            antecedents = antecedents.order_by(sort_by)
        else:
            antecedents = antecedents.order_by('-created_at')
        
        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(antecedents, request)
        
        if page is not None:
            serializer = AntecedantJuridiqueListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = AntecedantJuridiqueListSerializer(antecedents, many=True)
        return Response(serializer.data)
    
    def post(self, request, acheteur_id):
        """Ajoute un nouvel antécédent juridique"""
        acheteur = self.get_acheteur(acheteur_id)

        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        # Normaliser : 'autre' (minuscule) → 'Autre' (majuscule, nom du champ modèle)
        if 'autre' in data and 'Autre' not in data:
            data['Autre'] = data.pop('autre')

        data['acheteur'] = acheteur_id

        serializer = AddAntecedantsJuridiqueSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            antecedent = serializer.save()
        except Exception as e:
            logger.error(f"Erreur création antécédent: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            self.log_activity(
                request=request,
                action_type='CREATE_ANTECEDENT',
                object_id=antecedent.id,
                object_type='AntecedantsJuridique',
                details=f"Ajout d'un antécédent juridique pour l'acheteur {acheteur.nom} ({acheteur.code})"
            )
        except Exception:
            pass  # ne pas bloquer la réponse si le log échoue

        return Response({
            'message': 'Antécédent juridique ajouté avec succès',
            'id': antecedent.id
        }, status=status.HTTP_201_CREATED)
    
    
    @transaction.atomic
    def delete(self, request, acheteur_id):
        """Supprime un ou plusieurs antécédents"""
        acheteur = self.get_acheteur(acheteur_id)
        
        antecedent_ids = request.data.get('ids', [])
        if not isinstance(antecedent_ids, list) or not antecedent_ids:
            return Response(
                {'error': 'Une liste d\'IDs est requise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer les antécédents à supprimer
        antecedents = AntecedantsJuridique.objects.filter(
            id__in=antecedent_ids,
            acheteur=acheteur
        )
        
        if not antecedents.exists():
            return Response(
                {'error': 'Aucun antécédent trouvé pour les IDs fournis'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Log d'activité pour chaque antécédent avant suppression
        for antecedent in antecedents:
            self.log_activity(
                request=request,
                action_type='DELETE_ANTECEDENT',
                object_id=antecedent.id,
                object_type='AntecedantsJuridique',
                details=f"Suppression d'un antécédent juridique de l'acheteur {acheteur.nom}"
            )
        
        # Suppression
        count = antecedents.count()
        antecedents.delete()
        
        return Response({
            'message': f'{count} antécédent(s) supprimé(s) avec succès',
            'count': count
        })



class AcheteurAntecedentDetailView(APIView):
    """
    API pour gérer un antécédent juridique spécifique
    Méthodes: GET (détail), PUT (mise à jour)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def log_activity(self, request, action_type, object_id, object_type, details):
        """Enregistre une activité dans le log"""
        ActivityLog.objects.create(
            user=request.user,
            action_type=action_type,
            object_id=object_id,
            object_type=object_type,
            details=details,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get(self, request, acheteur_id, antecedent_id):
        """Récupère les détails d'un antécédent spécifique"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            antecedent = AntecedantsJuridique.objects.get(
                id=antecedent_id,
                acheteur=acheteur
            )
        except AntecedantsJuridique.DoesNotExist:
            return Response(
                {'error': 'Antécédent non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = GetAntecedantsJuridiqueSerializer(antecedent)
        return Response(serializer.data)
    
    def put(self, request, acheteur_id, antecedent_id):
        """Met à jour un antécédent existant"""
        acheteur = self.get_acheteur(acheteur_id)

        try:
            antecedent = AntecedantsJuridique.objects.get(
                id=antecedent_id,
                acheteur=acheteur
            )
        except AntecedantsJuridique.DoesNotExist:
            return Response(
                {'error': 'Antécédent non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        # Normaliser : 'Autre' → 'autre' pour correspondre au champ serializer (source='Autre')
        if 'Autre' in data and 'autre' not in data:
            data['autre'] = data.pop('Autre')
        
        serializer = EditAntecedantsJuridiqueSerializer(
            antecedent,
            data=data,
            partial=True
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            updated_antecedent = serializer.save()
        except Exception as e:
            logger.error(f"Erreur mise à jour antécédent: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            self.log_activity(
                request=request,
                action_type='UPDATE_ANTECEDENT',
                object_id=antecedent.id,
                object_type='AntecedantsJuridique',
                details=f"Mise à jour d'un antécédent juridique pour l'acheteur {acheteur.nom}"
            )
        except Exception:
            pass

        return Response({
            'message': 'Antécédent juridique mis à jour avec succès',
            'id': updated_antecedent.id
        })






class ListAcheteurGestionRisqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        gestion_risque_list = RiskManagment.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            gestion_risque_list = gestion_risque_list.filter(
                Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(gestion_risque_list, 10)  # 10 enregistrements par page
        gestion_risque_page = paginator.get_page(page_number)
        serializer = RiskManagmentSerializer(gestion_risque_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": gestion_risque_page.has_next(),
                "previous": gestion_risque_page.has_previous(),
            }
        )


class SearchAcheteurGestionRisqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        gestion_risque_list = RiskManagment.objects.filter(
            Q(acheteur_id=acheteur_id) & (Q(commentaire__icontains=search_term))
        ).order_by("-created_at")

        paginator = Paginator(gestion_risque_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        gestion_risque_page = paginator.get_page(page_number)
        serializer = RiskManagmentSerializer(gestion_risque_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": gestion_risque_page.has_next(),
                "previous": gestion_risque_page.has_previous(),
            }
        )


class AddAcheteurGestionRisqueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddRiskManagmentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurGestionRisqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, gestion_risque_id, *args, **kwargs):
        gestion_risque = RiskManagment.objects.filter(
            id=gestion_risque_id, acheteur_id=acheteur_id
        ).first()
        if not gestion_risque:
            return Response(
                {"detail": "Gestion de risque non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetRiskManagmentSerializer(gestion_risque)
        return Response(serializer.data)

    def put(self, request, acheteur_id, gestion_risque_id, *args, **kwargs):
        gestion_risque = RiskManagment.objects.filter(
            id=gestion_risque_id, acheteur_id=acheteur_id
        ).first()
        if not gestion_risque:
            return Response(
                {"detail": "Gestion de risque non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditRiskManagmentSerializer(
            gestion_risque, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurGestionRisqueView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        gestion_risques = RiskManagment.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not gestion_risques.exists():
            return Response(
                {"error": "Aucune gestion de risque trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = gestion_risques.delete()
        return Response(
            {"message": f"{count} gestions de risque supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        

class AcheteurGestionRisqueView(APIView):
    """
    API pour gérer la gestion des risques unique d'un acheteur
    Un acheteur ne peut avoir qu'une seule gestion des risques
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la gestion des risques de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)

        gestion_risque = RiskManagment.objects.filter(acheteur=acheteur).order_by('-created_at').first()
        if gestion_risque:
            serializer = GetRiskManagmentSerializer(gestion_risque)
            return Response(serializer.data)
        return Response({
            "message": "Aucune gestion des risques trouvée pour cet acheteur",
            "acheteur_id": acheteur_id
        }, status=status.HTTP_404_NOT_FOUND)

    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée ou met à jour la gestion des risques de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)

        gestion_risque = RiskManagment.objects.filter(acheteur=acheteur).order_by('-created_at').first()
        if gestion_risque:
            serializer = EditRiskManagmentSerializer(
                gestion_risque, data=request.data, partial=True
            )
            action = "mise à jour"
            http_status = status.HTTP_200_OK
        else:
            data = request.data.copy()
            data["acheteur"] = acheteur_id
            serializer = AddRiskManagmentSerializer(data=data)
            action = "créée"
            http_status = status.HTTP_201_CREATED

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": f"Gestion des risques {action} avec succès",
                "data": serializer.data
            }, status=http_status)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, acheteur_id):
        """Supprime la gestion des risques de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)

        gestion_risque = RiskManagment.objects.filter(acheteur=acheteur).order_by('-created_at').first()
        if gestion_risque:
            gestion_risque.delete()
            return Response({
                "message": "Gestion des risques supprimée avec succès"
            }, status=status.HTTP_200_OK)
        return Response({
            "message": "Aucune gestion des risques à supprimer"
        }, status=status.HTTP_404_NOT_FOUND)






class ListAcheteurMembreConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        membre_conseil_list = ConseilAdministration.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            membre_conseil_list = membre_conseil_list.filter(
                Q(nom__icontains=search_term) | Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(membre_conseil_list, 10)  # 10 enregistrements par page
        membre_conseil_page = paginator.get_page(page_number)
        serializer = ConseilAdministrationSerializer(membre_conseil_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": membre_conseil_page.has_next(),
                "previous": membre_conseil_page.has_previous(),
            }
        )


class SearchAcheteurMembreConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membre_conseil_list = ConseilAdministration.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (Q(nom__icontains=search_term) | Q(commentaire__icontains=search_term))
        ).order_by("-created_at")

        paginator = Paginator(membre_conseil_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        membre_conseil_page = paginator.get_page(page_number)
        serializer = ConseilAdministrationSerializer(membre_conseil_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": membre_conseil_page.has_next(),
                "previous": membre_conseil_page.has_previous(),
            }
        )


class AddAcheteurMembreConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddConseilAdministrationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurMembreConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, membre_conseil_id, *args, **kwargs):
        membre_conseil = ConseilAdministration.objects.filter(
            id=membre_conseil_id, acheteur_id=acheteur_id
        ).first()
        if not membre_conseil:
            return Response(
                {"detail": "Membre du conseil non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetConseilAdministrationSerializer(membre_conseil)
        return Response(serializer.data)

    def put(self, request, acheteur_id, membre_conseil_id, *args, **kwargs):
        membre_conseil = ConseilAdministration.objects.filter(
            id=membre_conseil_id, acheteur_id=acheteur_id
        ).first()
        if not membre_conseil:
            return Response(
                {"detail": "Membre du conseil non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditConseilAdministrationSerializer(
            membre_conseil, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurMembreConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membres_conseil = ConseilAdministration.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not membres_conseil.exists():
            return Response(
                {"error": "Aucun membre du conseil trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = membres_conseil.delete()
        return Response(
            {"message": f"{count} membres du conseil supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
        

class ConseilPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data,
            'next': self.page.has_next(),
            'previous': self.page.has_previous(),
            'start_index': self.page.start_index(),
            'end_index': self.page.end_index()
        })


class AcheteurConseilListView(APIView):
    """
    API pour gérer la liste des membres du conseil d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = ConseilPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def log_activity(self, request, action_type, object_id, object_type, details):
        """Enregistre une activité dans le log"""
        ActivityLog.objects.create(
            user=request.user,
            action_type=action_type,
            object_id=object_id,
            object_type=object_type,
            details=details,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get(self, request, acheteur_id):
        """Récupère la liste paginée des membres avec recherche"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Paramètres de recherche et filtrage
        search_term = request.query_params.get('search', '')
        
        # Construction de la requête
        membres = ConseilAdministration.objects.filter(
            acheteur=acheteur
        ).select_related('couleur_commentaire')
        
        # Recherche
        if search_term:
            membres = membres.filter(
                Q(nom__icontains=search_term) |
                Q(fonction_dans_le_conseil__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )
        
        # Tri
        sort_by = request.query_params.get('sort_by', '-created_at')
        if sort_by in ['nom', 'fonction_dans_le_conseil', 'created_at']:
            membres = membres.order_by(sort_by)
        else:
            membres = membres.order_by('-created_at')
        
        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(membres, request)
        
        if page is not None:
            serializer = ConseilAdministrationListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = ConseilAdministrationListSerializer(membres, many=True)
        return Response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Ajoute un nouveau membre du conseil"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si un membre avec le même nom existe déjà
        nom = request.data.get('nom', '').strip()
        
        if nom:
            existe_deja = ConseilAdministration.objects.filter(
                acheteur=acheteur,
                nom__iexact=nom
            ).exists()
            
            if existe_deja:
                return Response({
                    'error': f"Un membre du conseil avec le nom {nom} existe déjà."
                }, status=status.HTTP_409_CONFLICT)
        
        # Ajouter l'acheteur aux données
        data = request.data.copy()
        data['acheteur'] = acheteur_id
        
        serializer = AddConseilAdministrationSerializer(data=data)
        if serializer.is_valid():
            membre = serializer.save()
            
            # Log d'activité
            self.log_activity(
                request=request,
                action_type='CREATE_CONSEIL',
                object_id=membre.id,
                object_type='ConseilAdministration',
                details=f"Ajout du membre du conseil {membre.nom} pour l'acheteur {acheteur.nom} ({acheteur.code})"
            )
            
            return Response({
                'message': 'Membre du conseil ajouté avec succès',
                'data': GetConseilAdministrationSerializer(membre).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id):
        """Supprime un ou plusieurs membres du conseil"""
        acheteur = self.get_acheteur(acheteur_id)
        
        membre_ids = request.data.get('ids', [])
        if not isinstance(membre_ids, list) or not membre_ids:
            return Response(
                {'error': 'Une liste d\'IDs est requise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer les membres à supprimer
        membres = ConseilAdministration.objects.filter(
            id__in=membre_ids,
            acheteur=acheteur
        )
        
        if not membres.exists():
            return Response(
                {'error': 'Aucun membre du conseil trouvé pour les IDs fournis'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Log d'activité pour chaque membre avant suppression
        membres_details = []
        for membre in membres:
            membres_details.append({
                'id': membre.id,
                'nom': membre.nom
            })
            
            # Log d'activité
            self.log_activity(
                request=request,
                action_type='DELETE_CONSEIL',
                object_id=membre.id,
                object_type='ConseilAdministration',
                details=f"Suppression du membre du conseil {membre.nom} de l'acheteur {acheteur.nom}"
            )
        
        # Suppression
        count = membres.count()
        membres.delete()
        
        return Response({
            'message': f'{count} membre(s) du conseil supprimé(s) avec succès',
            'count': count
        })


class AcheteurConseilDetailView(APIView):
    """
    API pour gérer un membre du conseil spécifique
    Méthodes: GET (détail), PUT (mise à jour)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def log_activity(self, request, action_type, object_id, object_type, details):
        """Enregistre une activité dans le log"""
        ActivityLog.objects.create(
            user=request.user,
            action_type=action_type,
            object_id=object_id,
            object_type=object_type,
            details=details,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get(self, request, acheteur_id, membre_id):
        """Récupère les détails d'un membre spécifique"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            membre = ConseilAdministration.objects.get(
                id=membre_id,
                acheteur=acheteur
            )
        except ConseilAdministration.DoesNotExist:
            return Response(
                {'error': 'Membre du conseil non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = GetConseilAdministrationSerializer(membre)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, membre_id):
        """Met à jour un membre existant"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            membre = ConseilAdministration.objects.get(
                id=membre_id,
                acheteur=acheteur
            )
        except ConseilAdministration.DoesNotExist:
            return Response(
                {'error': 'Membre du conseil non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier les doublons (sauf pour le membre en cours)
        nom = request.data.get('nom', membre.nom).strip()
        
        doublon = ConseilAdministration.objects.filter(
            acheteur=acheteur,
            nom__iexact=nom
        ).exclude(id=membre_id).exists()
        
        if doublon:
            return Response({
                'error': f"Un autre membre du conseil avec le nom {nom} existe déjà."
            }, status=status.HTTP_409_CONFLICT)
        
        # Sauvegarder les anciennes valeurs pour le log
        old_values = {
            'nom': membre.nom,
            'fonction_dans_le_conseil': membre.fonction_dans_le_conseil,
            'numero_adresse': membre.numero_adresse,
            'rue_adresse': membre.rue_adresse,
            'code_postale_adresse': membre.code_postale_adresse,
            'commentaire': membre.commentaire
        }
        
        serializer = EditConseilAdministrationSerializer(
            membre,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            updated_membre = serializer.save()
            
            # Détecter les changements pour le log
            changes = []
            new_values = serializer.validated_data
            
            for field in ['nom', 'fonction_dans_le_conseil', 'numero_adresse', 
                         'rue_adresse', 'code_postale_adresse', 'commentaire']:
                if field in new_values and new_values[field] != old_values[field]:
                    old_val = str(old_values[field])[:50] + ('...' if len(str(old_values[field])) > 50 else '')
                    new_val = str(new_values[field])[:50] + ('...' if len(str(new_values[field])) > 50 else '')
                    changes.append(f"{field}: '{old_val}' → '{new_val}'")
            
            # Log d'activité
            details = f"Mise à jour du membre du conseil {membre.nom}"
            if changes:
                details += f" - Changements: {', '.join(changes)}"
            
            self.log_activity(
                request=request,
                action_type='UPDATE_CONSEIL',
                object_id=membre.id,
                object_type='ConseilAdministration',
                details=details
            )
            
            return Response({
                'message': 'Membre du conseil mis à jour avec succès',
                'data': GetConseilAdministrationSerializer(updated_membre).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_fonctions_list(request):
    """API pour récupérer la liste des fonctions"""
    # Transformer le tuple en liste de dictionnaires
    fonctions = [{'value': val[0], 'label': str(val[1])} for val in LISTE_NOUVELLE_FONCTION]
    return Response(fonctions)








class ListAcheteurCompositionCapitalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        composition_list = CompositionCapitalSocial.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            composition_list = composition_list.filter(
                Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(composition_list, 10)  # 10 enregistrements par page
        composition_page = paginator.get_page(page_number)
        serializer = CompositionCapitalSocialSerializer(composition_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": composition_page.has_next(),
                "previous": composition_page.has_previous(),
            }
        )


class SearchAcheteurCompositionCapitalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        composition_list = CompositionCapitalSocial.objects.filter(
            Q(acheteur_id=acheteur_id) & (Q(commentaire__icontains=search_term))
        ).order_by("-created_at")

        paginator = Paginator(composition_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        composition_page = paginator.get_page(page_number)
        serializer = CompositionCapitalSocialSerializer(composition_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": composition_page.has_next(),
                "previous": composition_page.has_previous(),
            }
        )


class AddAcheteurCompositionCapitalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddCompositionCapitalSocialSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurCompositionCapitalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, composition_capital_id, *args, **kwargs):
        composition = CompositionCapitalSocial.objects.filter(
            id=composition_capital_id, acheteur_id=acheteur_id
        ).first()
        if not composition:
            return Response(
                {"detail": "Composition du capital non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetCompositionCapitalSocialSerializer(composition)
        return Response(serializer.data)

    def put(self, request, acheteur_id, composition_capital_id, *args, **kwargs):
        composition = CompositionCapitalSocial.objects.filter(
            id=composition_capital_id, acheteur_id=acheteur_id
        ).first()
        if not composition:
            return Response(
                {"detail": "Composition du capital non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditCompositionCapitalSocialSerializer(
            composition, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurCompositionCapitalView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        compositions = CompositionCapitalSocial.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not compositions.exists():
            return Response(
                {
                    "error": "Aucune composition du capital trouvée pour les IDs fournis."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = compositions.delete()
        return Response(
            {"message": f"{count} compositions du capital supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        
        

class AcheteurCapitalView(APIView):
    """
    API pour gérer le capital social unique d'un acheteur
    Méthodes: GET, POST (create/update), DELETE
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère le capital social de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            capital = CompositionCapitalSocial.objects.get(acheteur=acheteur)
            serializer = GetCompositionCapitalSocialSerializer(capital)
            return Response(serializer.data)
        except CompositionCapitalSocial.DoesNotExist:
            return Response({
                "message": "Aucun capital social trouvé pour cet acheteur",
                "exists": False
            }, status=status.HTTP_404_NOT_FOUND)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée ou met à jour le capital social de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Validation des montants
        for field in ['emis', 'publie', 'libere']:
            value = request.data.get(field)
            if value and float(value) < 0:
                return Response({
                    'error': f'Le capital {field} ne peut pas être négatif'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si un capital existe déjà
        try:
            capital = CompositionCapitalSocial.objects.get(acheteur=acheteur)
            # Mise à jour
            serializer = EditCompositionCapitalSocialSerializer(
                capital, 
                data=request.data, 
                partial=True
            )
            action = "mis à jour"
            http_status = status.HTTP_200_OK
        except CompositionCapitalSocial.DoesNotExist:
            # Création
            data = request.data.copy()
            data["acheteur"] = acheteur_id
            serializer = AddCompositionCapitalSocialSerializer(data=data)
            action = "créé"
            http_status = status.HTTP_201_CREATED
        
        if serializer.is_valid():
            capital = serializer.save()
            return Response({
                "message": f"Capital social {action} avec succès",
                "data": GetCompositionCapitalSocialSerializer(capital).data
            }, status=http_status)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime le capital social de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            capital = CompositionCapitalSocial.objects.get(acheteur=acheteur)
            capital.delete()
            return Response({
                "message": "Capital social supprimé avec succès"
            }, status=status.HTTP_200_OK)
        except CompositionCapitalSocial.DoesNotExist:
            return Response({
                "message": "Aucun capital social à supprimer"
            }, status=status.HTTP_404_NOT_FOUND)











class ListAcheteurActionnaireView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        actionnaire_list = CompositionAction.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            actionnaire_list = actionnaire_list.filter(
                Q(commentaire__icontains=search_term)
                | Q(nom__icontains=search_term)
                | Q(prenom__icontains=search_term)
            )

        paginator = Paginator(actionnaire_list, 10)  # 10 enregistrements par page
        actionnaire_page = paginator.get_page(page_number)
        serializer = CompositionActionSerializer(actionnaire_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": actionnaire_page.has_next(),
                "previous": actionnaire_page.has_previous(),
            }
        )


class SearchAcheteurActionnaireView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        actionnaire_list = CompositionAction.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(commentaire__icontains=search_term)
                | Q(nom__icontains=search_term)
                | Q(prenom__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(actionnaire_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        actionnaire_page = paginator.get_page(page_number)
        serializer = CompositionActionSerializer(actionnaire_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": actionnaire_page.has_next(),
                "previous": actionnaire_page.has_previous(),
            }
        )


class AddAcheteurActionnaireView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddCompositionActionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurActionnaireView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, actionnaire_id, *args, **kwargs):
        actionnaire = CompositionAction.objects.filter(
            id=actionnaire_id, acheteur_id=acheteur_id
        ).first()
        if not actionnaire:
            return Response(
                {"detail": "Actionnaire non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetCompositionActionSerializer(actionnaire)
        return Response(serializer.data)

    def put(self, request, acheteur_id, actionnaire_id, *args, **kwargs):
        actionnaire = CompositionAction.objects.filter(
            id=actionnaire_id, acheteur_id=acheteur_id
        ).first()
        if not actionnaire:
            return Response(
                {"detail": "Actionnaire non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditCompositionActionSerializer(
            actionnaire, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurActionnaireView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        actionnaires = CompositionAction.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not actionnaires.exists():
            return Response(
                {"error": "Aucun actionnaire trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = actionnaires.delete()
        return Response(
            {"message": f"{count} actionnaires supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
        
        
class ActionnairePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data,
            'next': self.page.has_next(),
            'previous': self.page.has_previous(),
            'start_index': self.page.start_index(),
            'end_index': self.page.end_index()
        })


class AcheteurActionnaireListView(APIView):
    """
    API optimisée pour gérer la liste des actionnaires
    """
    permission_classes = [IsAuthenticated]
    pagination_class = ActionnairePagination
    
    def get_acheteur(self, acheteur_id):
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def log_activity(self, request, action_type, object_id, object_type, details):
        """Enregistre une activité dans le log"""
        ActivityLog.objects.create(
            user=request.user,
            action_type=action_type,
            object_id=object_id,
            object_type=object_type,
            details=details,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get(self, request, acheteur_id):
        """Récupère la liste paginée des actionnaires avec recherche"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Paramètres
        search_term = request.query_params.get('search', '')
        sort_by = request.query_params.get('sort_by', '-created_at')
        
        # Construction de la requête optimisée
        actionnaires = CompositionAction.objects.filter(
            acheteur=acheteur
        ).select_related('couleur_commentaire')
        
        # Recherche avancée
        if search_term:
            actionnaires = actionnaires.filter(
                Q(nom__icontains=search_term) |
                Q(prenom__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )
        
        # Tri sécurisé
        valid_sort_fields = ['nom', 'prenom', 'pourcentage', 'created_at', 'updated_at']
        if sort_by.lstrip('-') in valid_sort_fields:
            actionnaires = actionnaires.order_by(sort_by)
        else:
            actionnaires = actionnaires.order_by('-created_at')
        
        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(actionnaires, request)
        
        if page is not None:
            serializer = CompositionActionListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = CompositionActionListSerializer(actionnaires, many=True)
        return Response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Ajoute un nouvel actionnaire avec validation améliorée"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # CORRECTION CRITIQUE : Gérer proprement le pourcentage
        pourcentage = request.data.get('pourcentage')
        
        if pourcentage is not None:
            try:
                # Convertir en Decimal pour une précision exacte
                pourcentage_val = Decimal(str(pourcentage))
                
                # Validation du format
                if pourcentage_val < 0 or pourcentage_val > 100:
                    return Response({
                        'error': 'Le pourcentage doit être compris entre 0 et 100'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculer le total actuel
                total_pourcentage = CompositionAction.objects.filter(
                    acheteur=acheteur
                ).aggregate(total=Sum('pourcentage'))['total'] or Decimal('0')
                
                # CORRECTION : S'assurer que total_pourcentage est Decimal
                if isinstance(total_pourcentage, float):
                    total_pourcentage = Decimal(str(total_pourcentage))
                
                # Vérifier que le total ne dépasse pas 100%
                nouveau_total = total_pourcentage + pourcentage_val
                
                if nouveau_total > 100:
                    disponible = 100 - total_pourcentage
                    return Response({
                        'error': f'Pourcentage maximum disponible: {disponible:.2f}%'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except (ValueError, InvalidOperation, TypeError) as e:
                return Response({
                    'error': f'Pourcentage invalide: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Si pas de pourcentage, mettre à None
            pourcentage_val = None
        
        # Vérification des doublons (nom + prénom)
        nom = request.data.get('nom', '').strip().upper()
        prenom = request.data.get('prenom', '').strip()
        
        if nom and prenom:
            existe_deja = CompositionAction.objects.filter(
                acheteur=acheteur,
                nom__iexact=nom,
                prenom__iexact=prenom
            ).exists()
            
            if existe_deja:
                return Response({
                    'error': f'Un actionnaire {nom} {prenom} existe déjà.'
                }, status=status.HTTP_409_CONFLICT)
        
        # Préparation des données avec conversion appropriée
        data = request.data.copy()
        data['acheteur'] = acheteur_id
        
        # Nettoyer les données
        if 'pourcentage' in data:
            if data['pourcentage'] == '':
                data['pourcentage'] = None
            else:
                try:
                    data['pourcentage'] = Decimal(str(data['pourcentage']))
                except:
                    data['pourcentage'] = None
        
        # Mettre le nom en majuscules
        if 'nom' in data:
            data['nom'] = data['nom'].strip().upper()
        if 'prenom' in data:
            data['prenom'] = data['prenom'].strip()
        
        serializer = AddCompositionActionSerializer(data=data)
        
        if serializer.is_valid():
            try:
                actionnaire = serializer.save()
                
                # Log d'activité
                self.log_activity(
                    request=request,
                    action_type='CREATE_ACTIONNAIRE',
                    object_id=actionnaire.id,
                    object_type='CompositionAction',
                    details=f"Ajout de l'actionnaire {actionnaire.nom} {actionnaire.prenom} ({actionnaire.pourcentage}%) pour l'acheteur {acheteur.nom}"
                )
                
                # Mettre à jour les statistiques en cache
                cache.delete(f'actionnaire_stats_{acheteur_id}')
                
                return Response({
                    'message': 'Actionnaire ajouté avec succès',
                    'data': GetCompositionActionSerializer(actionnaire).data,
                    'pourcentage_total': CompositionAction.objects.filter(
                        acheteur=acheteur
                    ).aggregate(total=Sum('pourcentage'))['total'] or 0
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Erreur création actionnaire: {str(e)}")
                return Response({
                    'error': 'Erreur interne lors de la création'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Retourner les erreurs de validation
        errors = serializer.errors
        if errors:
            error_message = self.format_serializer_errors(errors)
            return Response({
                'error': error_message
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def format_serializer_errors(self, errors):
        """Formate les erreurs du serializer pour l'affichage"""
        formatted_errors = []
        for field, field_errors in errors.items():
            if isinstance(field_errors, list):
                for error in field_errors:
                    formatted_errors.append(f"{field}: {error}")
            else:
                formatted_errors.append(f"{field}: {field_errors}")
        return " | ".join(formatted_errors)
    
    
    
    @transaction.atomic
    def delete(self, request, acheteur_id):
        """Supprime un ou plusieurs actionnaires"""
        acheteur = self.get_acheteur(acheteur_id)
        
        actionnaire_ids = request.data.get('ids', [])
        if not isinstance(actionnaire_ids, list) or not actionnaire_ids:
            return Response(
                {'error': 'Une liste d\'IDs est requise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer les actionnaires
        actionnaires = CompositionAction.objects.filter(
            id__in=actionnaire_ids,
            acheteur=acheteur
        )
        
        if not actionnaires.exists():
            return Response(
                {'error': 'Aucun actionnaire trouvé pour les IDs fournis'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Log avant suppression
        for actionnaire in actionnaires:
            self.log_activity(
                request=request,
                action_type='DELETE_ACTIONNAIRE',
                object_id=actionnaire.id,
                object_type='CompositionAction',
                details=f"Suppression de l'actionnaire {actionnaire.nom} {actionnaire.prenom}"
            )
        
        # Suppression
        count = actionnaires.count()
        actionnaires.delete()
        
        # CORRECTION : Mettre à jour le cache
        from django.core.cache import cache
        cache.delete(f'actionnaire_stats_{acheteur_id}')
        
        return Response({
            'message': f'{count} actionnaire(s) supprimé(s) avec succès',
            'count': count
        })


class ActionnaireDetailView(APIView):
    """Vue pour récupérer, modifier ou supprimer un actionnaire spécifique"""
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_actionnaire(self, acheteur_id, actionnaire_id):
        return get_object_or_404(
            CompositionAction, 
            id=actionnaire_id,
            acheteur_id=acheteur_id
        )
    
    def log_activity(self, request, action_type, object_id, object_type, details):
        """Enregistre une activité dans le log"""
        ActivityLog.objects.create(
            user=request.user,
            action_type=action_type,
            object_id=object_id,
            object_type=object_type,
            details=details,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get(self, request, acheteur_id, pk):
        """Récupère les détails d'un actionnaire"""
        try:
            actionnaire = self.get_actionnaire(acheteur_id, pk)
            serializer = GetCompositionActionSerializer(actionnaire)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Erreur récupération actionnaire: {str(e)}")
            return Response(
                {'error': 'Actionnaire non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @transaction.atomic
    def put(self, request, acheteur_id, pk):
        """Met à jour un actionnaire"""
        try:
            acheteur = self.get_acheteur(acheteur_id)
            actionnaire = self.get_actionnaire(acheteur_id, pk)
            
            # Validation du pourcentage
            pourcentage = request.data.get('pourcentage')
            pourcentage_val = None
            
            if pourcentage is not None and pourcentage != '':
                try:
                    # Convertir en Decimal
                    pourcentage_val = Decimal(str(pourcentage))
                    
                    # Validation de base
                    if pourcentage_val < Decimal('0') or pourcentage_val > Decimal('100'):
                        return Response({
                            'error': 'Le pourcentage doit être compris entre 0 et 100'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Vérifier les décimales
                    if pourcentage_val.as_tuple().exponent < -2:
                        return Response({
                            'error': 'Maximum 2 décimales autorisées'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Calculer le total actuel (sans l'actionnaire en cours)
                    total_pourcentage = CompositionAction.objects.filter(
                        acheteur=acheteur
                    ).exclude(id=pk).aggregate(
                        total=Sum('pourcentage')
                    )['total'] or Decimal('0')
                    
                    # Vérifier que total_pourcentage est Decimal
                    if isinstance(total_pourcentage, float):
                        total_pourcentage = Decimal(str(total_pourcentage))
                    
                    # Vérifier le nouveau total
                    nouveau_total = total_pourcentage + pourcentage_val
                    if nouveau_total > Decimal('100'):
                        disponible = Decimal('100') - total_pourcentage
                        return Response({
                            'error': f'Pourcentage maximum disponible: {disponible:.2f}%'
                        }, status=status.HTTP_400_BAD_REQUEST)
                        
                except (ValueError, InvalidOperation, TypeError) as e:
                    logger.error(f"Erreur conversion pourcentage: {str(e)}")
                    return Response({
                        'error': 'Pourcentage invalide. Format attendu: 25.50'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Préparation des données
            data = request.data.copy()
            
            # Nettoyer le pourcentage
            if 'pourcentage' in data:
                if data['pourcentage'] == '':
                    data['pourcentage'] = None
                elif data['pourcentage'] is not None:
                    try:
                        data['pourcentage'] = Decimal(str(data['pourcentage']))
                    except:
                        data['pourcentage'] = None
            
            # Normaliser les noms
            if 'nom' in data:
                data['nom'] = data['nom'].strip().upper()
            if 'prenom' in data:
                data['prenom'] = data['prenom'].strip().title()
            
            # Validation avec serializer
            serializer = EditCompositionActionSerializer(
                actionnaire, 
                data=data, 
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                
                # Log d'activité
                self.log_activity(
                    request=request,
                    action_type='UPDATE_ACTIONNAIRE',
                    object_id=actionnaire.id,
                    object_type='CompositionAction',
                    details=f"Modification de l'actionnaire {actionnaire.nom} {actionnaire.prenom}"
                )
                
                # Mettre à jour le cache
                from django.core.cache import cache
                cache.delete(f'actionnaire_stats_{acheteur_id}')
                
                # Recalculer le pourcentage total
                nouveau_total = CompositionAction.objects.filter(
                    acheteur=acheteur
                ).aggregate(total=Sum('pourcentage'))['total'] or Decimal('0')
                
                return Response({
                    'message': 'Actionnaire mis à jour avec succès',
                    'data': GetCompositionActionSerializer(actionnaire).data,
                    'pourcentage_total': float(nouveau_total)
                })
            
            # Formater les erreurs
            errors = []
            for field, field_errors in serializer.errors.items():
                if isinstance(field_errors, list):
                    for error in field_errors:
                        errors.append(f"{field}: {error}")
                else:
                    errors.append(f"{field}: {field_errors}")
            
            return Response({
                'error': ' | '.join(errors)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur mise à jour actionnaire: {str(e)}", exc_info=True)
            return Response({
                'error': 'Une erreur interne est survenue lors de la mise à jour'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def delete(self, request, acheteur_id, pk):
        """Supprime un actionnaire spécifique"""
        try:
            actionnaire = self.get_actionnaire(acheteur_id, pk)
            
            # Log avant suppression
            self.log_activity(
                request=request,
                action_type='DELETE_ACTIONNAIRE',
                object_id=actionnaire.id,
                object_type='CompositionAction',
                details=f"Suppression de l'actionnaire {actionnaire.nom} {actionnaire.prenom}"
            )
            
            # Suppression
            actionnaire.delete()
            
            # Mettre à jour le cache
            from django.core.cache import cache
            cache.delete(f'actionnaire_stats_{acheteur_id}')
            
            return Response({
                'message': 'Actionnaire supprimé avec succès'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur suppression actionnaire: {str(e)}")
            return Response({
                'error': 'Actionnaire non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
            

class ActionnaireStatsView(APIView):
    """
    API pour les statistiques des actionnaires
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, acheteur_id):
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        
        stats = CompositionAction.objects.filter(acheteur=acheteur).aggregate(
            total=Count('id'),
            avec_pourcentage=Count('id', filter=Q(pourcentage__isnull=False)),
            total_pourcentage=Sum('pourcentage'),
            avec_commentaire=Count('id', filter=~Q(commentaire='')),
            avec_couleur=Count('id', filter=Q(couleur_commentaire__isnull=False)),
        )
        
        # Répartition par pourcentage
        repartition = {
            '0-10%': CompositionAction.objects.filter(
                acheteur=acheteur,
                pourcentage__range=(0, 10)
            ).count(),
            '10-25%': CompositionAction.objects.filter(
                acheteur=acheteur,
                pourcentage__range=(10, 25)
            ).count(),
            '25-50%': CompositionAction.objects.filter(
                acheteur=acheteur,
                pourcentage__range=(25, 50)
            ).count(),
            '50-100%': CompositionAction.objects.filter(
                acheteur=acheteur,
                pourcentage__range=(50, 100)
            ).count(),
        }
        
        return Response({
            'stats': stats,
            'repartition': repartition,
            'pourcentage_total': stats['total_pourcentage'] or 0
        })







class ListAcheteurOpinionAcremacView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        opinion_list = OpinionCreditAcremac.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            opinion_list = opinion_list.filter(Q(commentaire__icontains=search_term))

        paginator = Paginator(opinion_list, 10)  # 10 enregistrements par page
        opinion_page = paginator.get_page(page_number)
        serializer = OpinionCreditAcremacSerializer(opinion_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": opinion_page.has_next(),
                "previous": opinion_page.has_previous(),
            }
        )


class SearchAcheteurOpinionAcremacView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        opinion_list = OpinionCreditAcremac.objects.filter(
            Q(acheteur_id=acheteur_id) & (Q(commentaire__icontains=search_term))
        ).order_by("-created_at")

        paginator = Paginator(opinion_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        opinion_page = paginator.get_page(page_number)
        serializer = OpinionCreditAcremacSerializer(opinion_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": opinion_page.has_next(),
                "previous": opinion_page.has_previous(),
            }
        )


class AddAcheteurOpinionAcremacView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddOpinionCreditAcremacSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurOpinionAcremacView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, opinion_id, *args, **kwargs):
        opinion = OpinionCreditAcremac.objects.filter(
            id=opinion_id, acheteur_id=acheteur_id
        ).first()
        if not opinion:
            return Response(
                {"detail": "Opinion de crédit non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetOpinionCreditAcremacSerializer(opinion)
        return Response(serializer.data)

    def put(self, request, acheteur_id, opinion_id, *args, **kwargs):
        opinion = OpinionCreditAcremac.objects.filter(
            id=opinion_id, acheteur_id=acheteur_id
        ).first()
        if not opinion:
            return Response(
                {"detail": "Opinion de crédit non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditOpinionCreditAcremacSerializer(
            opinion, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurOpinionAcremacView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        opinions = OpinionCreditAcremac.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not opinions.exists():
            return Response(
                {"error": "Aucune opinion de crédit trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = opinions.delete()
        return Response(
            {"message": f"{count} opinions de crédit supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        
        
class AcheteurOpinionAcremacView(APIView):
    """
    API pour gérer l'opinion de crédit unique d'un acheteur
    Méthodes: GET, POST (create/update), DELETE
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère l'opinion de crédit de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            opinion = OpinionCreditAcremac.objects.get(acheteur=acheteur)
            serializer = GetOpinionCreditAcremacSerializer(opinion)
            return Response(serializer.data)
        except OpinionCreditAcremac.DoesNotExist:
            return Response({
                "message": "Aucune opinion de crédit trouvée pour cet acheteur",
                "acheteur_id": acheteur_id
            }, status=status.HTTP_404_NOT_FOUND)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée ou met à jour l'opinion de crédit de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si une opinion existe déjà
        try:
            opinion = OpinionCreditAcremac.objects.get(acheteur=acheteur)
            serializer = EditOpinionCreditAcremacSerializer(
                opinion, data=request.data, partial=True
            )
            action = "mise à jour"
        except OpinionCreditAcremac.DoesNotExist:
            data = request.data.copy()
            data["acheteur"] = acheteur_id
            serializer = AddOpinionCreditAcremacSerializer(data=data)
            action = "créée"
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": f"Opinion de crédit {action} avec succès",
                "data": serializer.data
            }, status=status.HTTP_200_OK if action == "mise à jour" else status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime l'opinion de crédit de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            opinion = OpinionCreditAcremac.objects.get(acheteur=acheteur)
            opinion.delete()
            return Response({
                "message": "Opinion de crédit supprimée avec succès"
            }, status=status.HTTP_200_OK)
        except OpinionCreditAcremac.DoesNotExist:
            return Response({
                "message": "Aucune opinion de crédit à supprimer"
            }, status=status.HTTP_404_NOT_FOUND)







class ListAcheteurFilialeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        filiale_list = Structure.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            filiale_list = filiale_list.filter(
                Q(nom__icontains=search_term) | Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(filiale_list, 10)  # 10 enregistrements par page
        filiale_page = paginator.get_page(page_number)
        serializer = StructureSerializer(filiale_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": filiale_page.has_next(),
                "previous": filiale_page.has_previous(),
            }
        )


class SearchAcheteurFilialeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filiale_list = Structure.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (Q(nom__icontains=search_term) | Q(commentaire__icontains=search_term))
        ).order_by("-created_at")

        paginator = Paginator(filiale_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        filiale_page = paginator.get_page(page_number)
        serializer = StructureSerializer(filiale_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": filiale_page.has_next(),
                "previous": filiale_page.has_previous(),
            }
        )


class AddAcheteurFilialeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddStructureSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurFilialeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, filiale_id, *args, **kwargs):
        filiale = Structure.objects.filter(
            id=filiale_id, acheteur_id=acheteur_id
        ).first()
        if not filiale:
            return Response(
                {"detail": "Filiale non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetStructureSerializer(filiale)
        return Response(serializer.data)

    def put(self, request, acheteur_id, filiale_id, *args, **kwargs):
        filiale = Structure.objects.filter(
            id=filiale_id, acheteur_id=acheteur_id
        ).first()
        if not filiale:
            return Response(
                {"detail": "Filiale non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditStructureSerializer(filiale, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurFilialeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filiales = Structure.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not filiales.exists():
            return Response(
                {"error": "Aucune filiale trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = filiales.delete()
        return Response(
            {"message": f"{count} filiales supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        
        
        
class FilialePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data,
            'next': self.page.has_next(),
            'previous': self.page.has_previous(),
            'start_index': self.page.start_index(),
            'end_index': self.page.end_index()
        })


class AcheteurFilialeListView(APIView):
    """
    API optimisée pour gérer la liste des filiales
    """
    permission_classes = [IsAuthenticated]
    pagination_class = FilialePagination
    
    def get_acheteur(self, acheteur_id):
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def log_activity(self, request, action_type, object_id, object_type, details):
        """Enregistre une activité dans le log"""
        ActivityLog.objects.create(
            user=request.user,
            action_type=action_type,
            object_id=object_id,
            object_type=object_type,
            details=details,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get(self, request, acheteur_id):
        """Récupère la liste paginée des filiales avec recherche"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Paramètres
        search_term = request.query_params.get('search', '')
        sort_by = request.query_params.get('sort_by', '-created_at')
        
        # Construction de la requête optimisée
        filiales = Structure.objects.filter(
            acheteur=acheteur
        ).select_related('couleur_commentaire')
        
        # Recherche avancée
        if search_term:
            filiales = filiales.filter(
                Q(nom__icontains=search_term) |
                Q(type_affiliation__icontains=search_term) |
                Q(commentaire__icontains=search_term) |
                Q(numero_adresse__icontains=search_term) |
                Q(rue_adresse__icontains=search_term)
            )
        
        # Tri sécurisé
        valid_sort_fields = ['nom', 'type_affiliation', 'created_at', 'updated_at']
        if sort_by.lstrip('-') in valid_sort_fields:
            filiales = filiales.order_by(sort_by)
        else:
            filiales = filiales.order_by('-created_at')
        
        # Pagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(filiales, request)
        
        if page is not None:
            serializer = StructureListSerializer(page, many=True)
            print(serializer)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = StructureListSerializer(filiales, many=True)
        return Response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Ajoute une nouvelle filiale avec validation"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérification des doublons (même nom pour le même acheteur)
        nom = request.data.get('nom', '').strip()
        
        if nom:
            existe_deja = Structure.objects.filter(
                acheteur=acheteur,
                nom__iexact=nom
            ).exists()
            
            if existe_deja:
                return Response({
                    'error': f"Une filiale avec le nom {nom} existe déjà."
                }, status=status.HTTP_409_CONFLICT)
        
        # Préparation des données
        data = request.data.copy()
        data['acheteur'] = acheteur_id
        
        # Nettoyage et validation des données
        if 'nom' in data:
            data['nom'] = data['nom'].strip()
        
        serializer = AddStructureSerializer(data=data)
        
        if serializer.is_valid():
            filiale = serializer.save()
            
            # Log d'activité
            self.log_activity(
                request=request,
                action_type='CREATE_FILIALE',
                object_id=filiale.id,
                object_type='Structure',
                details=f"Ajout de la filiale {filiale.nom} ({filiale.type_affiliation}) pour l'acheteur {acheteur.nom}"
            )
            
            return Response({
                'message': 'Filiale ajoutée avec succès',
                'data': GetStructureSerializer(filiale).data
            }, status=status.HTTP_201_CREATED)
        
        # Formater les erreurs
        errors = []
        for field, field_errors in serializer.errors.items():
            if isinstance(field_errors, list):
                for error in field_errors:
                    errors.append(f"{field}: {error}")
            else:
                errors.append(f"{field}: {field_errors}")
        
        return Response({
            'error': ' | '.join(errors)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id):
        """Supprime une ou plusieurs filiales"""
        acheteur = self.get_acheteur(acheteur_id)
        
        filiale_ids = request.data.get('ids', [])
        if not isinstance(filiale_ids, list) or not filiale_ids:
            return Response(
                {'error': 'Une liste d\'IDs est requise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer les filiales
        filiales = Structure.objects.filter(
            id__in=filiale_ids,
            acheteur=acheteur
        )
        
        if not filiales.exists():
            return Response(
                {'error': 'Aucune filiale trouvée pour les IDs fournis'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Log avant suppression
        for filiale in filiales:
            self.log_activity(
                request=request,
                action_type='DELETE_FILIALE',
                object_id=filiale.id,
                object_type='Structure',
                details=f"Suppression de la filiale {filiale.nom}"
            )
        
        # Suppression
        count = filiales.count()
        filiales.delete()
        
        return Response({
            'message': f'{count} filiale(s) supprimée(s) avec succès',
            'count': count
        })


class AcheteurFilialeDetailView(APIView):
    """
    API pour gérer une filiale spécifique
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_filiale(self, acheteur_id, filiale_id):
        return get_object_or_404(
            Structure, 
            id=filiale_id,
            acheteur_id=acheteur_id
        )
    
    def log_activity(self, request, action_type, object_id, object_type, details):
        ActivityLog.objects.create(
            user=request.user,
            action_type=action_type,
            object_id=object_id,
            object_type=object_type,
            details=details,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get(self, request, acheteur_id, filiale_id):
        """Récupère les détails d'une filiale"""
        try:
            filiale = Structure.objects.select_related(
                'couleur_commentaire'
            ).get(
                id=filiale_id,
                acheteur_id=acheteur_id
            )
        except Structure.DoesNotExist:
            return Response(
                {'error': 'Filiale non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = GetStructureSerializer(filiale)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, filiale_id):
        """Met à jour une filiale"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            filiale = Structure.objects.get(
                id=filiale_id,
                acheteur=acheteur
            )
        except Structure.DoesNotExist:
            return Response(
                {'error': 'Filiale non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérification des doublons (sauf pour la filiale en cours)
        nom = request.data.get('nom', filiale.nom).strip()
        
        if nom:
            doublon = Structure.objects.filter(
                acheteur=acheteur,
                nom__iexact=nom
            ).exclude(id=filiale_id).exists()
            
            if doublon:
                return Response({
                    'error': f"Une autre filiale avec le nom {nom} existe déjà."
                }, status=status.HTTP_409_CONFLICT)
        
        # Préparation des données
        data = request.data.copy()
        
        # Nettoyage des données
        if 'nom' in data:
            data['nom'] = data['nom'].strip()
        
        serializer = EditStructureSerializer(
            filiale,
            data=data,
            partial=True
        )
        
        if serializer.is_valid():
            updated_filiale = serializer.save()
            
            # Détection des changements pour le log
            old_values = {
                'nom': filiale.nom,
                'type_affiliation': filiale.type_affiliation,
                'numero_adresse': filiale.numero_adresse,
                'rue_adresse': filiale.rue_adresse,
                'commentaire': filiale.commentaire
            }
            
            changes = []
            new_values = serializer.validated_data
            
            for field in ['nom', 'type_affiliation', 'numero_adresse', 'rue_adresse', 'commentaire']:
                if field in new_values and new_values[field] != old_values[field]:
                    old_val = str(old_values[field])[:50] + ('...' if len(str(old_values[field])) > 50 else '')
                    new_val = str(new_values[field])[:50] + ('...' if len(str(new_values[field])) > 50 else '')
                    changes.append(f"{field}: '{old_val}' → '{new_val}'")
            
            # Log d'activité
            details = f"Mise à jour de la filiale {filiale.nom}"
            if changes:
                details += f" - Changements: {', '.join(changes)}"
            
            self.log_activity(
                request=request,
                action_type='UPDATE_FILIALE',
                object_id=filiale.id,
                object_type='Structure',
                details=details
            )
            
            return Response({
                'message': 'Filiale mise à jour avec succès',
                'data': GetStructureSerializer(updated_filiale).data
            })
        
        # Formater les erreurs
        errors = []
        for field, field_errors in serializer.errors.items():
            if isinstance(field_errors, list):
                for error in field_errors:
                    errors.append(f"{field}: {error}")
            else:
                errors.append(f"{field}: {field_errors}")
        
        return Response({
            'error': ' | '.join(errors)
        }, status=status.HTTP_400_BAD_REQUEST)


class FilialeStatsView(APIView):
    """
    API pour les statistiques des filiales
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, acheteur_id):
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        
        stats = Structure.objects.filter(acheteur=acheteur).aggregate(
            total=Count('id'),
            avec_adresse=Count('id', filter=~Q(numero_adresse='') & ~Q(rue_adresse='')),
            avec_commentaire=Count('id', filter=~Q(commentaire='')),
            avec_couleur=Count('id', filter=Q(couleur_commentaire__isnull=False)),
        )
        
        # Répartition par type d'affiliation
        repartition = Structure.objects.filter(
            acheteur=acheteur
        ).values('type_affiliation').annotate(
            count=Count('id'),
            percentage=Count('id') * 100.0 / stats['total']
        ).order_by('-count')
        
        # Types d'affiliation disponibles
        types_disponibles = [
            'Société - mère',
            'Filiale', 
            'Subsidiary',
            'Société Sœur',
            'La holding',
            'Le groupe de sociétés',
            'Société de gestion'
        ]
        
        repartition_complete = []
        for type_aff in types_disponibles:
            count = Structure.objects.filter(
                acheteur=acheteur,
                type_affiliation=type_aff
            ).count()
            
            if count > 0 or stats['total'] == 0:
                repartition_complete.append({
                    'type': type_aff,
                    'count': count,
                    'percentage': (count * 100.0 / stats['total']) if stats['total'] > 0 else 0
                })
        
        return Response({
            'stats': stats,
            'repartition': repartition_complete,
            'total': stats['total']
        })











class ListAcheteurAnalyseSectorielleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        analyse_list = AnalyseSectorielle.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            analyse_list = analyse_list.filter(
                Q(commentaire__icontains=search_term)
                | Q(impact_covid_19__icontains=search_term)
            )

        paginator = Paginator(analyse_list, 10)  # 10 enregistrements par page
        analyse_page = paginator.get_page(page_number)
        serializer = AnalyseSectorielleSerializer(analyse_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": analyse_page.has_next(),
                "previous": analyse_page.has_previous(),
            }
        )


class SearchAcheteurAnalyseSectorielleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        analyse_list = AnalyseSectorielle.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(commentaire__icontains=search_term)
                | Q(impact_covid_19__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(analyse_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        analyse_page = paginator.get_page(page_number)
        serializer = AnalyseSectorielleSerializer(analyse_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": analyse_page.has_next(),
                "previous": analyse_page.has_previous(),
            }
        )


class AddAcheteurAnalyseSectorielleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddAnalyseSectorielleSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurAnalyseSectorielleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, analyse_id, *args, **kwargs):
        analyse = AnalyseSectorielle.objects.filter(
            id=analyse_id, acheteur_id=acheteur_id
        ).first()
        if not analyse:
            return Response(
                {"detail": "Analyse sectorielle non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetAnalyseSectorielleSerializer(analyse)
        return Response(serializer.data)

    def put(self, request, acheteur_id, analyse_id, *args, **kwargs):
        analyse = AnalyseSectorielle.objects.filter(
            id=analyse_id, acheteur_id=acheteur_id
        ).first()
        if not analyse:
            return Response(
                {"detail": "Analyse sectorielle non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditAnalyseSectorielleSerializer(
            analyse, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurAnalyseSectorielleView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        analyses = AnalyseSectorielle.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not analyses.exists():
            return Response(
                {"error": "Aucune analyse sectorielle trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = analyses.delete()
        return Response(
            {"message": f"{count} analyses sectorielles supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        

        
class AcheteurAnalyseSectorielleView(APIView):
    """
    API pour gérer l'analyse sectorielle unique d'un acheteur
    Méthodes: GET, POST (create/update), DELETE
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère l'analyse sectorielle de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            analyse = AnalyseSectorielle.objects.get(acheteur=acheteur)
            serializer = GetAnalyseSectorielleSerializer(analyse)
            return Response(serializer.data)
        except AnalyseSectorielle.DoesNotExist:
            return Response({
                "message": "Aucune analyse sectorielle trouvée pour cet acheteur",
                "exists": False
            }, status=status.HTTP_404_NOT_FOUND)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée ou met à jour l'analyse sectorielle de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si une analyse existe déjà
        try:
            analyse = AnalyseSectorielle.objects.get(acheteur=acheteur)
            serializer = EditAnalyseSectorielleSerializer(
                analyse, data=request.data, partial=True
            )
            action = "mise à jour"
            http_status = status.HTTP_200_OK
        except AnalyseSectorielle.DoesNotExist:
            data = request.data.copy()
            data["acheteur"] = acheteur_id
            serializer = AddAnalyseSectorielleSerializer(data=data)
            action = "créée"
            http_status = status.HTTP_201_CREATED
        
        if serializer.is_valid():
            analyse = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_ANALYSE' if action == "créée" else 'UPDATE_ANALYSE',
                object_id=analyse.id,
                object_type='AnalyseSectorielle',
                details=f"Analyse sectorielle {action} pour l'acheteur {acheteur.nom} ({acheteur.code})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": f"Analyse sectorielle {action} avec succès",
                "data": GetAnalyseSectorielleSerializer(analyse).data
            }, status=http_status)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime l'analyse sectorielle de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            analyse = AnalyseSectorielle.objects.get(acheteur=acheteur)
            
            # Log d'activité avant suppression
            ActivityLog.objects.create(
                user=request.user,
                action_type='DELETE_ANALYSE',
                object_id=analyse.id,
                object_type='AnalyseSectorielle',
                details=f"Analyse sectorielle supprimée pour l'acheteur {acheteur.nom} ({acheteur.code})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            analyse.delete()
            return Response({
                "message": "Analyse sectorielle supprimée avec succès"
            }, status=status.HTTP_200_OK)
        except AnalyseSectorielle.DoesNotExist:
            return Response({
                "message": "Aucune analyse sectorielle à supprimer"
            }, status=status.HTTP_404_NOT_FOUND)










class ListAcheteurCompteFinancierView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        compte_list = CompteFinancier.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            compte_list = compte_list.filter(
                Q(commentaire__icontains=search_term)
                | Q(cabinet__icontains=search_term)
            )

        paginator = Paginator(compte_list, 10)  # 10 enregistrements par page
        compte_page = paginator.get_page(page_number)
        serializer = CompteFinancierSerializer(compte_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": compte_page.has_next(),
                "previous": compte_page.has_previous(),
            }
        )


class SearchAcheteurCompteFinancierView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        compte_list = CompteFinancier.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(commentaire__icontains=search_term)
                | Q(cabinet__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(compte_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        compte_page = paginator.get_page(page_number)
        serializer = CompteFinancierSerializer(compte_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": compte_page.has_next(),
                "previous": compte_page.has_previous(),
            }
        )


class AddAcheteurCompteFinancierView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddCompteFinancierSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurCompteFinancierView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, compte_financier_id, *args, **kwargs):
        compte = CompteFinancier.objects.filter(
            id=compte_financier_id, acheteur_id=acheteur_id
        ).first()
        if not compte:
            return Response(
                {"detail": "Compte financier non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetCompteFinancierSerializer(compte)
        return Response(serializer.data)

    def put(self, request, acheteur_id, compte_financier_id, *args, **kwargs):
        compte = CompteFinancier.objects.filter(
            id=compte_financier_id, acheteur_id=acheteur_id
        ).first()
        if not compte:
            return Response(
                {"detail": "Compte financier non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditCompteFinancierSerializer(
            compte, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurCompteFinancierView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        comptes = CompteFinancier.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not comptes.exists():
            return Response(
                {"error": "Aucun compte financier trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = comptes.delete()
        return Response(
            {"message": f"{count} comptes financiers supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
        
        
class AcheteurCompteFinancierView(APIView):
    """
    API pour gérer le compte financier unique d'un acheteur
    Méthodes: GET, POST (create/update), DELETE
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère le compte financier de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            compte_financier = CompteFinancier.objects.get(acheteur=acheteur)
            serializer = GetCompteFinancierSerializer(compte_financier)
            return Response({
                "exists": True,
                "data": serializer.data
            })
        except CompteFinancier.DoesNotExist:
            return Response({
                "message": "Aucun compte financier trouvé pour cet acheteur",
                "exists": False
            }, status=status.HTTP_404_NOT_FOUND)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée ou met à jour le compte financier de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si un compte financier existe déjà
        try:
            compte_financier = CompteFinancier.objects.get(acheteur=acheteur)
            serializer = EditCompteFinancierSerializer(
                compte_financier, data=request.data, partial=True
            )
            action = "mis à jour"
            http_status = status.HTTP_200_OK
        except CompteFinancier.DoesNotExist:
            data = request.data.copy()
            data["acheteur"] = acheteur_id
            serializer = AddCompteFinancierSerializer(data=data)
            action = "créé"
            http_status = status.HTTP_201_CREATED
        
        if serializer.is_valid():
            compte_financier = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_COMPTE_FINANCIER' if action == "créé" else 'UPDATE_COMPTE_FINANCIER',
                object_id=compte_financier.id,
                object_type='CompteFinancier',
                details=f"Compte financier {action} pour l'acheteur {acheteur.nom} ({acheteur.code})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": f"Compte financier {action} avec succès",
                "data": GetCompteFinancierSerializer(compte_financier).data
            }, status=http_status)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime le compte financier de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            compte_financier = CompteFinancier.objects.get(acheteur=acheteur)
            
            # Log d'activité avant suppression
            ActivityLog.objects.create(
                user=request.user,
                action_type='DELETE_COMPTE_FINANCIER',
                object_id=compte_financier.id,
                object_type='CompteFinancier',
                details=f"Compte financier supprimé pour l'acheteur {acheteur.nom} ({acheteur.code})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            compte_financier.delete()
            return Response({
                "message": "Compte financier supprimé avec succès"
            }, status=status.HTTP_200_OK)
        except CompteFinancier.DoesNotExist:
            return Response({
                "message": "Aucun compte financier à supprimer"
            }, status=status.HTTP_404_NOT_FOUND)
            
            
            
            
            










class BasculerAnneesCompteFinancierView(APIView):
    """
    Décale les périodes N/N-1/N-2 du CompteFinancier d'un acheteur :
      - Ancien N  → nouveau N-1
      - Ancien N-1 → nouveau N-2
      - Ancien N-2 → archivé (perdu, données bilan conservées via FK Annee)
      - Nouveau N  → vide (à remplir)
    Ne touche PAS aux enregistrements ActifC/PassifC/ResultatC qui restent
    liés à leurs années respectives.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, acheteur_id):
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)

        try:
            cf = CompteFinancier.objects.get(acheteur=acheteur)
        except CompteFinancier.DoesNotExist:
            return Response(
                {"success": False, "error": "Aucun compte financier trouvé pour cet acheteur."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Mémoriser les périodes actuelles avant décalage
        old_n = {
            'debut': cf.date_compte.isoformat() if cf.date_compte else None,
            'fin':   cf.date_fin.isoformat()     if cf.date_fin    else None,
        }
        old_n1 = {
            'debut': cf.date_compte_n_moins_un.isoformat() if cf.date_compte_n_moins_un else None,
            'fin':   cf.date_fin_n_moins_un.isoformat()    if cf.date_fin_n_moins_un    else None,
        }
        old_n2 = {
            'debut': cf.date_compte_n_moins_deux.isoformat() if cf.date_compte_n_moins_deux else None,
            'fin':   cf.date_fin_n_moins_deux.isoformat()    if cf.date_fin_n_moins_deux    else None,
        }

        # Décalage
        cf.date_compte_n_moins_deux = cf.date_compte_n_moins_un
        cf.date_fin_n_moins_deux    = cf.date_fin_n_moins_un
        cf.date_compte_n_moins_un   = cf.date_compte
        cf.date_fin_n_moins_un      = cf.date_fin
        cf.date_compte              = None
        cf.date_fin                 = None
        cf.updated_by               = request.user
        cf.save()

        ActivityLog.objects.create(
            user=request.user,
            action_type='UPDATE_COMPTE_FINANCIER',
            object_id=cf.id,
            object_type='CompteFinancier',
            details=(
                f"Bascule des années effectuée pour {acheteur.nom} ({acheteur.code}). "
                f"Ancien N ({old_n['debut']}→{old_n['fin']}) → N-1 ; "
                f"Ancien N-1 ({old_n1['debut']}→{old_n1['fin']}) → N-2 ; "
                f"Ancien N-2 archivé."
            ),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        return Response({
            "success": True,
            "message": "Bascule des années effectuée avec succès.",
            "decalage": {
                "archive_n2": old_n2,
                "nouveau_n1": old_n,
                "nouveau_n2": old_n1,
            },
            "data": GetCompteFinancierSerializer(cf).data,
        })


class AnnulerBasculerAnneesView(APIView):
    """
    Annule la dernière bascule des années en restaurant les 6 dates fournies.
    Le client envoie les anciennes dates (stockées côté client après la bascule).
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, acheteur_id):
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)

        try:
            cf = CompteFinancier.objects.get(acheteur=acheteur)
        except CompteFinancier.DoesNotExist:
            return Response(
                {"success": False, "error": "Aucun compte financier trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        d = request.data

        def parse_date(val):
            if not val:
                return None
            from datetime import date as date_type
            import datetime
            try:
                return datetime.date.fromisoformat(str(val))
            except (ValueError, TypeError):
                return None

        cf.date_compte              = parse_date(d.get('date_compte'))
        cf.date_fin                 = parse_date(d.get('date_fin'))
        cf.date_compte_n_moins_un   = parse_date(d.get('date_compte_n_moins_un'))
        cf.date_fin_n_moins_un      = parse_date(d.get('date_fin_n_moins_un'))
        cf.date_compte_n_moins_deux = parse_date(d.get('date_compte_n_moins_deux'))
        cf.date_fin_n_moins_deux    = parse_date(d.get('date_fin_n_moins_deux'))
        cf.updated_by               = request.user
        cf.save()

        ActivityLog.objects.create(
            user=request.user,
            action_type='UPDATE_COMPTE_FINANCIER',
            object_id=cf.id,
            object_type='CompteFinancier',
            details=f"Annulation de bascule des années pour {acheteur.nom} ({acheteur.code}).",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        return Response({
            "success": True,
            "message": "Bascule annulée avec succès.",
            "data": GetCompteFinancierSerializer(cf).data,
        })


class ListAcheteurOperationHistoriqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        operation_list = OperationEtHistorique.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            operation_list = operation_list.filter(
                Q(commentaire_ratios__icontains=search_term)
                | Q(description_complete_activite__icontains=search_term)
                | Q(importation__icontains=search_term)
                | Q(historique__icontains=search_term)
            )

        paginator = Paginator(operation_list, 10)  # 10 enregistrements par page
        operation_page = paginator.get_page(page_number)
        serializer = OperationEtHistoriqueSerializer(operation_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": operation_page.has_next(),
                "previous": operation_page.has_previous(),
            }
        )


class SearchAcheteurOperationHistoriqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        operation_list = OperationEtHistorique.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(commentaire_ratios__icontains=search_term)
                | Q(description_complete_activite__icontains=search_term)
                | Q(importation__icontains=search_term)
                | Q(historique__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(operation_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        operation_page = paginator.get_page(page_number)
        serializer = OperationEtHistoriqueSerializer(operation_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": operation_page.has_next(),
                "previous": operation_page.has_previous(),
            }
        )


class AddAcheteurOperationHistoriqueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddOperationEtHistoriqueSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurOperationHistoriqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, operation_historique_id, *args, **kwargs):
        operation = OperationEtHistorique.objects.filter(
            id=operation_historique_id, acheteur_id=acheteur_id
        ).first()
        if not operation:
            return Response(
                {"detail": "Opération et historique non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetOperationEtHistoriqueSerializer(operation)
        return Response(serializer.data)

    def put(self, request, acheteur_id, operation_historique_id, *args, **kwargs):
        operation = OperationEtHistorique.objects.filter(
            id=operation_historique_id, acheteur_id=acheteur_id
        ).first()
        if not operation:
            return Response(
                {"detail": "Opération et historique non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditOperationEtHistoriqueSerializer(
            operation, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurOperationHistoriqueView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        operations = OperationEtHistorique.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not operations.exists():
            return Response(
                {
                    "error": "Aucune opération et historique trouvée pour les IDs fournis."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = operations.delete()
        return Response(
            {"message": f"{count} opérations et historiques supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        


def _resolve_importations(items):
    """Résout un mix d'IDs (int) et de libellés (str) en liste d'IDs ListeImportation."""
    ids = []
    for item in (items or []):
        try:
            ids.append(int(item))
        except (ValueError, TypeError):
            label = str(item).strip()
            if label:
                obj, _ = ListeImportation.objects.get_or_create(libelle=label)
                ids.append(obj.id)
    return ids


class AcheteurOperationHistoriqueListView(APIView):
    """
    API pour gérer les opérations et historiques d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des opérations/historiques de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        operations = OperationEtHistorique.objects.filter(
            acheteur=acheteur
        ).select_related('acheteur').prefetch_related('importation').order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            operations = operations.filter(
                Q(description_complete_activite__icontains=search) |
                Q(commentaire_ratios__icontains=search) |
                Q(historique__icontains=search)
            )
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(operations, request)
        
        serializer = OperationEtHistoriqueSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée une nouvelle opération/historique pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        # Extraire importation avant sérialisation (peut contenir des labels texte via tags select2)
        raw_importations = data.getlist('importation') if hasattr(data, 'getlist') else data.get('importation', [])
        try:
            del data['importation']
        except KeyError:
            pass

        serializer = OperationEtHistoriqueCreateSerializer(data=data)

        if serializer.is_valid():
            operation = serializer.save()

            # Résoudre IDs + créer nouveaux ListeImportation si libellé inconnu
            if raw_importations:
                operation.importation.set(_resolve_importations(raw_importations))
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_OPERATION',
                object_id=operation.id,
                object_type='OperationEtHistorique',
                details=f"Opération/historique créé pour l'acheteur {acheteur.nom}: {(operation.description_complete_activite or '')[:100]}...",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Opération/historique créé avec succès",
                "data": OperationEtHistoriqueSerializer(operation).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AcheteurOperationHistoriqueDetailView(APIView):
    """
    API pour gérer une opération/historique spécifique
    Méthodes: GET (détail), PUT (modification), DELETE (suppression)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_operation(self, acheteur_id, operation_id):
        """Récupère l'opération ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            OperationEtHistorique.objects.select_related('acheteur').prefetch_related('importation'),
            id=operation_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, operation_id):
        """Récupère les détails d'une opération spécifique"""
        operation = self.get_operation(acheteur_id, operation_id)
        serializer = OperationEtHistoriqueSerializer(operation)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, operation_id):
        """Modifie une opération/historique existante"""
        operation = self.get_operation(acheteur_id, operation_id)
        
        # Extraire importation avant sérialisation (peut contenir des labels texte via tags select2)
        has_importation = 'importation' in request.data
        raw_importations = []
        if has_importation:
            raw_importations = request.data.getlist('importation') if hasattr(request.data, 'getlist') else request.data['importation']

        data_for_serializer = request.data.copy()
        try:
            del data_for_serializer['importation']
        except KeyError:
            pass

        serializer = OperationEtHistoriqueUpdateSerializer(
            operation, data=data_for_serializer, partial=True
        )

        if serializer.is_valid():
            operation = serializer.save()

            # Résoudre IDs + créer nouveaux ListeImportation si libellé inconnu
            if has_importation:
                operation.importation.set(_resolve_importations(raw_importations))
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_OPERATION',
                object_id=operation.id,
                object_type='OperationEtHistorique',
                details=f"Opération/historique modifié pour l'acheteur {operation.acheteur.nom}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Opération/historique modifié avec succès",
                "data": OperationEtHistoriqueSerializer(operation).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id, operation_id):
        """Supprime une opération/historique"""
        operation = self.get_operation(acheteur_id, operation_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_OPERATION',
            object_id=operation.id,
            object_type='OperationEtHistorique',
            details=f"Opération/historique supprimé pour l'acheteur {operation.acheteur.nom}: {operation.description_complete_activite[:100]}...",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        operation.delete()
        return Response({
            "message": "Opération/historique supprimé avec succès"
        }, status=status.HTTP_200_OK)


# API pour récupérer les listes d'importation
class ListeImportationListView(APIView):
    """
    API pour récupérer la liste des importations disponibles
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère toutes les importations"""
        importations = ListeImportation.objects.all().order_by('libelle')
        serializer = ListeImportationSerializer(importations, many=True)
        return Response(serializer.data)











class ListAcheteurProprieteActifView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        propriete_list = ProprieteEtActif.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            propriete_list = propriete_list.filter(
                Q(locaux__icontains=search_term)
                | Q(locaux_ref__libelle__icontains=search_term)
                | Q(branche__icontains=search_term)
            )

        paginator = Paginator(propriete_list, 10)  # 10 enregistrements par page
        propriete_page = paginator.get_page(page_number)
        serializer = ProprieteEtActifSerializer(propriete_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": propriete_page.has_next(),
                "previous": propriete_page.has_previous(),
            }
        )


class SearchAcheteurProprieteActifView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        propriete_list = ProprieteEtActif.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(locaux__icontains=search_term)
                | Q(locaux_ref__libelle__icontains=search_term)
                | Q(branche__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(propriete_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        propriete_page = paginator.get_page(page_number)
        serializer = ProprieteEtActifSerializer(propriete_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": propriete_page.has_next(),
                "previous": propriete_page.has_previous(),
            }
        )


class AddAcheteurProprieteActifView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddProprieteEtActifSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurProprieteActifView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, propriete_actif_id, *args, **kwargs):
        propriete = ProprieteEtActif.objects.filter(
            id=propriete_actif_id, acheteur_id=acheteur_id
        ).first()
        if not propriete:
            return Response(
                {"detail": "Propriété et actif non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetProprieteEtActifSerializer(propriete)
        return Response(serializer.data)

    def put(self, request, acheteur_id, propriete_actif_id, *args, **kwargs):
        propriete = ProprieteEtActif.objects.filter(
            id=propriete_actif_id, acheteur_id=acheteur_id
        ).first()
        if not propriete:
            return Response(
                {"detail": "Propriété et actif non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditProprieteEtActifSerializer(
            propriete, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurProprieteActifView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        proprietes = ProprieteEtActif.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not proprietes.exists():
            return Response(
                {"error": "Aucune propriété et actif trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = proprietes.delete()
        return Response(
            {"message": f"{count} propriétés et actifs supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
        
        
class AcheteurProprieteActifView(APIView):
    """
    API pour gérer la propriété et les actifs d'un acheteur
    - GET : Récupère la propriété/actif de l'acheteur (une seule)
    - POST : Crée la propriété/actif pour l'acheteur
    - PUT : Met à jour la propriété/actif existante
    - DELETE : Supprime la propriété/actif
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_propriete_actif(self, acheteur_id):
        """Récupère la propriété/actif de l'acheteur ou retourne None"""
        acheteur = self.get_acheteur(acheteur_id)
        try:
            return ProprieteEtActif.objects.select_related('acheteur').prefetch_related('locaux').get(
                acheteur=acheteur
            )
        except ProprieteEtActif.DoesNotExist:
            return None
    
    def get(self, request, acheteur_id):
        """Récupère la propriété/actif de l'acheteur"""
        propriete_actif = self.get_propriete_actif(acheteur_id)
        
        if propriete_actif:
            serializer = ProprieteEtActifSerializer(propriete_actif)
            return Response(serializer.data)
        else:
            return Response({
                "exists": False,
                "message": "Aucune propriété/actif enregistrée pour cet acheteur"
            }, status=status.HTTP_200_OK)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée une propriété/actif pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si une propriété/actif existe déjà
        existing = ProprieteEtActif.objects.filter(acheteur=acheteur).first()
        if existing:
            return Response({
                "error": "Une propriété/actif existe déjà pour cet acheteur",
                "id": existing.id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = ProprieteEtActifCreateSerializer(data=data)
        
        if serializer.is_valid():
            # Sauvegarder la propriété/actif
            propriete_actif = serializer.save()
            
            # Gérer les locaux ManyToMany
            if 'locaux' in data:
                propriete_actif.locaux.set(data['locaux'])
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_PROPRIETE_ACTIF',
                object_id=propriete_actif.id,
                object_type='ProprieteEtActif',
                details=f"Propriété/actif créé pour l'acheteur {acheteur.nom}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Propriété/actif créé avec succès",
                "data": ProprieteEtActifSerializer(propriete_actif).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def put(self, request, acheteur_id):
        """Met à jour la propriété/actif existante"""
        propriete_actif = self.get_propriete_actif(acheteur_id)
        
        if not propriete_actif:
            return Response({
                "error": "Aucune propriété/actif trouvée pour cet acheteur"
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProprieteEtActifUpdateSerializer(
            propriete_actif, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            propriete_actif = serializer.save()
            
            # Mettre à jour les locaux ManyToMany
            if 'locaux' in request.data:
                propriete_actif.locaux.set(request.data['locaux'])
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_PROPRIETE_ACTIF',
                object_id=propriete_actif.id,
                object_type='ProprieteEtActif',
                details=f"Propriété/actif modifié pour l'acheteur {propriete_actif.acheteur.nom}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Propriété/actif modifié avec succès",
                "data": ProprieteEtActifSerializer(propriete_actif).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime la propriété/actif de l'acheteur"""
        propriete_actif = self.get_propriete_actif(acheteur_id)
        
        if not propriete_actif:
            return Response({
                "error": "Aucune propriété/actif trouvée pour cet acheteur"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_PROPRIETE_ACTIF',
            object_id=propriete_actif.id,
            object_type='ProprieteEtActif',
            details=f"Propriété/actif supprimé pour l'acheteur {propriete_actif.acheteur.nom}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        propriete_actif.delete()
        return Response({
            "message": "Propriété/actif supprimé avec succès"
        }, status=status.HTTP_200_OK)


# API pour récupérer les locaux
class LocauxListView(APIView):
    """
    API pour récupérer la liste des locaux disponibles
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère tous les locaux"""
        search = request.query_params.get('search', '')
        
        locaux = Locaux.objects.all().order_by('nom')
        
        if search:
            locaux = locaux.filter(nom__icontains=search)
        
        serializer = LocauxSerializer(locaux, many=True)
        return Response(serializer.data)














class ListAcheteurConditionAchatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        condition_list = ConditionAchat.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            condition_list = condition_list.filter(
                Q(local__icontains=search_term)
                | Q(importation__icontains=search_term)
                | Q(les_clients__icontains=search_term)
                | Q(fournisseur__icontains=search_term)
            )

        paginator = Paginator(condition_list, 10)  # 10 enregistrements par page
        condition_page = paginator.get_page(page_number)
        serializer = ConditionAchatSerializer(condition_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": condition_page.has_next(),
                "previous": condition_page.has_previous(),
            }
        )


class SearchAcheteurConditionAchatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        condition_list = ConditionAchat.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(local__icontains=search_term)
                | Q(importation__icontains=search_term)
                | Q(les_clients__icontains=search_term)
                | Q(fournisseur__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(condition_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        condition_page = paginator.get_page(page_number)
        serializer = ConditionAchatSerializer(condition_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": condition_page.has_next(),
                "previous": condition_page.has_previous(),
            }
        )


class AddAcheteurConditionAchatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddConditionAchatSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurConditionAchatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, condition_achat_id, *args, **kwargs):
        condition = ConditionAchat.objects.filter(
            id=condition_achat_id, acheteur_id=acheteur_id
        ).first()
        if not condition:
            return Response(
                {"detail": "Condition d'achat non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetConditionAchatSerializer(condition)
        return Response(serializer.data)

    def put(self, request, acheteur_id, condition_achat_id, *args, **kwargs):
        condition = ConditionAchat.objects.filter(
            id=condition_achat_id, acheteur_id=acheteur_id
        ).first()
        if not condition:
            return Response(
                {"detail": "Condition d'achat non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditConditionAchatSerializer(
            condition, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurConditionAchatView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conditions = ConditionAchat.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not conditions.exists():
            return Response(
                {"error": "Aucune condition d'achat trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = conditions.delete()
        return Response(
            {"message": f"{count} conditions d'achat supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
            
        
class AcheteurConditionAchatView(APIView):
    """
    API pour gérer les conditions d'achat d'un acheteur
    - GET : Récupère les conditions d'achat de l'acheteur (une seule)
    - POST : Crée les conditions d'achat pour l'acheteur
    - PUT : Met à jour les conditions d'achat existantes
    - DELETE : Supprime les conditions d'achat
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_condition_achat(self, acheteur_id):
        """Récupère les conditions d'achat de l'acheteur ou retourne None"""
        acheteur = self.get_acheteur(acheteur_id)
        try:
            return ConditionAchat.objects.select_related('acheteur').prefetch_related('local', 'importation').get(
                acheteur=acheteur
            )
        except ConditionAchat.DoesNotExist:
            return None
    
    def get(self, request, acheteur_id):
        """Récupère les conditions d'achat de l'acheteur"""
        condition_achat = self.get_condition_achat(acheteur_id)
        
        if condition_achat:
            serializer = ConditionAchatSerializer(condition_achat)
            return Response(serializer.data)
        else:
            return Response({
                "exists": False,
                "message": "Aucune condition d'achat enregistrée pour cet acheteur"
            }, status=status.HTTP_200_OK)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée des conditions d'achat pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si des conditions d'achat existent déjà
        existing = ConditionAchat.objects.filter(acheteur=acheteur).first()
        if existing:
            return Response({
                "error": "Des conditions d'achat existent déjà pour cet acheteur",
                "id": existing.id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = ConditionAchatCreateSerializer(data=data)
        
        if serializer.is_valid():
            # Sauvegarder les conditions d'achat
            condition_achat = serializer.save()
            
            # Gérer les ManyToMany
            if 'local' in data:
                condition_achat.local.set(data['local'])
            if 'importation' in data:
                condition_achat.importation.set(data['importation'])
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_CONDITION_ACHAT',
                object_id=condition_achat.id,
                object_type='ConditionAchat',
                details=f"Conditions d'achat créées pour l'acheteur {acheteur.nom}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Conditions d'achat créées avec succès",
                "data": ConditionAchatSerializer(condition_achat).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def put(self, request, acheteur_id):
        """Met à jour les conditions d'achat existantes"""
        condition_achat = self.get_condition_achat(acheteur_id)
        
        if not condition_achat:
            return Response({
                "error": "Aucune condition d'achat trouvée pour cet acheteur"
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ConditionAchatUpdateSerializer(
            condition_achat, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            condition_achat = serializer.save()
            
            # Mettre à jour les ManyToMany
            if 'local' in request.data:
                condition_achat.local.set(request.data['local'])
            if 'importation' in request.data:
                condition_achat.importation.set(request.data['importation'])
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_CONDITION_ACHAT',
                object_id=condition_achat.id,
                object_type='ConditionAchat',
                details=f"Conditions d'achat modifiées pour l'acheteur {condition_achat.acheteur.nom}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Conditions d'achat modifiées avec succès",
                "data": ConditionAchatSerializer(condition_achat).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime les conditions d'achat de l'acheteur"""
        condition_achat = self.get_condition_achat(acheteur_id)
        
        if not condition_achat:
            return Response({
                "error": "Aucune condition d'achat trouvée pour cet acheteur"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_CONDITION_ACHAT',
            object_id=condition_achat.id,
            object_type='ConditionAchat',
            details=f"Conditions d'achat supprimées pour l'acheteur {condition_achat.acheteur.nom}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        condition_achat.delete()
        return Response({
            "message": "Conditions d'achat supprimées avec succès"
        }, status=status.HTTP_200_OK)


# API pour récupérer les conditions d'achat disponibles
class ListeConditionAchatListView(APIView):
    """
    API pour récupérer la liste des conditions d'achat disponibles
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère toutes les conditions d'achat"""
        search = request.query_params.get('search', '')
        
        conditions = ListeConditionAchat.objects.all().order_by('nom')
        
        if search:
            conditions = conditions.filter(nom__icontains=search)
        
        serializer = ListeConditionAchatSerializer(conditions, many=True)
        return Response(serializer.data)











class ListAcheteurConditionVenteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        condition_list = ConditionDeVente.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            condition_list = condition_list.filter(
                Q(local__icontains=search_term)
                | Q(recouvrement_de_dette_jugement__icontains=search_term)
                | Q(comportement_de_paiement__icontains=search_term)
            )

        paginator = Paginator(condition_list, 10)  # 10 enregistrements par page
        condition_page = paginator.get_page(page_number)
        serializer = ConditionDeVenteSerializer(condition_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": condition_page.has_next(),
                "previous": condition_page.has_previous(),
            }
        )


class SearchAcheteurConditionVenteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        condition_list = ConditionDeVente.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(local__icontains=search_term)
                | Q(recouvrement_de_dette_jugement__icontains=search_term)
                | Q(comportement_de_paiement__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(condition_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        condition_page = paginator.get_page(page_number)
        serializer = ConditionDeVenteSerializer(condition_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": condition_page.has_next(),
                "previous": condition_page.has_previous(),
            }
        )


class AddAcheteurConditionVenteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddConditionDeVenteSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurConditionVenteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, condition_vente_id, *args, **kwargs):
        condition = ConditionDeVente.objects.filter(
            id=condition_vente_id, acheteur_id=acheteur_id
        ).first()
        if not condition:
            return Response(
                {"detail": "Condition de vente non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetConditionDeVenteSerializer(condition)
        return Response(serializer.data)

    def put(self, request, acheteur_id, condition_vente_id, *args, **kwargs):
        condition = ConditionDeVente.objects.filter(
            id=condition_vente_id, acheteur_id=acheteur_id
        ).first()
        if not condition:
            return Response(
                {"detail": "Condition de vente non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditConditionDeVenteSerializer(
            condition, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurConditionVenteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conditions = ConditionDeVente.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not conditions.exists():
            return Response(
                {"error": "Aucune condition de vente trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = conditions.delete()
        return Response(
            {"message": f"{count} conditions de vente supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        
        
class AcheteurConditionVenteView(APIView):
    """
    API pour gérer les conditions de vente d'un acheteur
    - GET : Récupère les conditions de vente de l'acheteur (une seule)
    - POST : Crée les conditions de vente pour l'acheteur
    - PUT : Met à jour les conditions de vente existantes
    - DELETE : Supprime les conditions de vente
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_condition_vente(self, acheteur_id):
        """Récupère les conditions de vente de l'acheteur ou retourne None"""
        acheteur = self.get_acheteur(acheteur_id)
        try:
            return ConditionDeVente.objects.select_related('acheteur').prefetch_related('local').get(
                acheteur=acheteur
            )
        except ConditionDeVente.DoesNotExist:
            return None
    
    def get(self, request, acheteur_id):
        """Récupère les conditions de vente de l'acheteur"""
        condition_vente = self.get_condition_vente(acheteur_id)
        
        if condition_vente:
            serializer = ConditionDeVenteSerializer(condition_vente)
            return Response(serializer.data)
        else:
            return Response({
                "exists": False,
                "message": "Aucune condition de vente enregistrée pour cet acheteur"
            }, status=status.HTTP_200_OK)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée des conditions de vente pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si des conditions de vente existent déjà
        existing = ConditionDeVente.objects.filter(acheteur=acheteur).first()
        if existing:
            return Response({
                "error": "Des conditions de vente existent déjà pour cet acheteur",
                "id": existing.id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = ConditionDeVenteCreateSerializer(data=data)
        
        if serializer.is_valid():
            # Sauvegarder les conditions de vente
            condition_vente = serializer.save()
            
            # Gérer les ManyToMany
            if 'local' in data:
                condition_vente.local.set(data['local'])
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_CONDITION_VENTE',
                object_id=condition_vente.id,
                object_type='ConditionDeVente',
                details=f"Conditions de vente créées pour l'acheteur {acheteur.nom}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Conditions de vente créées avec succès",
                "data": ConditionDeVenteSerializer(condition_vente).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def put(self, request, acheteur_id):
        """Met à jour les conditions de vente existantes"""
        condition_vente = self.get_condition_vente(acheteur_id)
        
        if not condition_vente:
            return Response({
                "error": "Aucune condition de vente trouvée pour cet acheteur"
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ConditionDeVenteUpdateSerializer(
            condition_vente, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            condition_vente = serializer.save()
            
            # Mettre à jour les ManyToMany
            if 'local' in request.data:
                condition_vente.local.set(request.data['local'])
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_CONDITION_VENTE',
                object_id=condition_vente.id,
                object_type='ConditionDeVente',
                details=f"Conditions de vente modifiées pour l'acheteur {condition_vente.acheteur.nom}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Conditions de vente modifiées avec succès",
                "data": ConditionDeVenteSerializer(condition_vente).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime les conditions de vente de l'acheteur"""
        condition_vente = self.get_condition_vente(acheteur_id)
        
        if not condition_vente:
            return Response({
                "error": "Aucune condition de vente trouvée pour cet acheteur"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_CONDITION_VENTE',
            object_id=condition_vente.id,
            object_type='ConditionDeVente',
            details=f"Conditions de vente supprimées pour l'acheteur {condition_vente.acheteur.nom}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        condition_vente.delete()
        return Response({
            "message": "Conditions de vente supprimées avec succès"
        }, status=status.HTTP_200_OK)


# API pour récupérer les conditions de vente disponibles
class ListeConditionVenteListView(APIView):
    """
    API pour récupérer la liste des conditions de vente disponibles
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère toutes les conditions de vente"""
        search = request.query_params.get('search', '')
        
        conditions = ListeConditionVente.objects.all().order_by('nom')
        
        if search:
            conditions = conditions.filter(nom__icontains=search)
        
        serializer = ListeConditionVenteSerializer(conditions, many=True)
        return Response(serializer.data)


# API pour récupérer les choix disponibles
class ConditionVenteChoicesView(APIView):
    """
    API pour récupérer les choix disponibles pour les champs
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère les choix disponibles"""
        # Récupérer les choix du modèle
        recouvrement_choices = [
            {'value': choice[0], 'label': str(choice[1])}
            for choice in ConditionDeVente.LIEN_COMPORTEMENT_JUGEMENT_CHOICE
        ]
        
        paiement_choices = [
            {'value': choice[0], 'label': str(choice[1])}
            for choice in ConditionDeVente.LIEN_COMPORTEMENT_PAIEMENT_CHOICE
        ]
        
        return Response({
            'recouvrement_choices': recouvrement_choices,
            'paiement_choices': paiement_choices
        })
        
        
        
        
        







class ListAcheteurSommaireAvisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        sommaire_list = SommaireEtAvis.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            sommaire_list = sommaire_list.filter(Q(commentaire__icontains=search_term))

        paginator = Paginator(sommaire_list, 10)  # 10 enregistrements par page
        sommaire_page = paginator.get_page(page_number)
        serializer = SommaireEtAvisSerializer(sommaire_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": sommaire_page.has_next(),
                "previous": sommaire_page.has_previous(),
            }
        )


class SearchAcheteurSommaireAvisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sommaire_list = SommaireEtAvis.objects.filter(
            Q(acheteur_id=acheteur_id) & (Q(commentaire__icontains=search_term))
        ).order_by("-created_at")

        paginator = Paginator(sommaire_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        sommaire_page = paginator.get_page(page_number)
        serializer = SommaireEtAvisSerializer(sommaire_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": sommaire_page.has_next(),
                "previous": sommaire_page.has_previous(),
            }
        )


class AddAcheteurSommaireAvisView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddSommaireEtAvisSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurSommaireAvisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, sommaire_avis_id, *args, **kwargs):
        sommaire = SommaireEtAvis.objects.filter(
            id=sommaire_avis_id, acheteur_id=acheteur_id
        ).first()
        if not sommaire:
            return Response(
                {"detail": "Sommaire et avis non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetSommaireEtAvisSerializer(sommaire)
        return Response(serializer.data)

    def put(self, request, acheteur_id, sommaire_avis_id, *args, **kwargs):
        sommaire = SommaireEtAvis.objects.filter(
            id=sommaire_avis_id, acheteur_id=acheteur_id
        ).first()
        if not sommaire:
            return Response(
                {"detail": "Sommaire et avis non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditSommaireEtAvisSerializer(
            sommaire, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurSommaireAvisView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sommaires = SommaireEtAvis.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not sommaires.exists():
            return Response(
                {"error": "Aucun sommaire et avis trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = sommaires.delete()
        return Response(
            {"message": f"{count} sommaires et avis supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
        
        
class AcheteurSommaireEtAvisView(APIView):
    """
    API pour gérer le sommaire et avis unique d'un acheteur
    Méthodes: GET, POST (create/update), DELETE
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère le sommaire et avis de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            sommaire_avis = SommaireEtAvis.objects.get(acheteur=acheteur)
            serializer = GetSommaireEtAvisSerializer(sommaire_avis)
            return Response({
                "exists": True,
                "data": serializer.data
            })
        except SommaireEtAvis.DoesNotExist:
            return Response({
                "message": "Aucun sommaire et avis trouvé pour cet acheteur",
                "exists": False
            }, status=status.HTTP_404_NOT_FOUND)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée ou met à jour le sommaire et avis de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si un sommaire/avis existe déjà
        try:
            sommaire_avis = SommaireEtAvis.objects.get(acheteur=acheteur)
            serializer = EditSommaireEtAvisSerializer(
                sommaire_avis, data=request.data, partial=True
            )
            action = "mis à jour"
            http_status = status.HTTP_200_OK
        except SommaireEtAvis.DoesNotExist:
            data = request.data.copy()
            data["acheteur"] = acheteur_id
            serializer = AddSommaireEtAvisSerializer(data=data)
            action = "créé"
            http_status = status.HTTP_201_CREATED
        
        if serializer.is_valid():
            sommaire_avis = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_SOMMAIRE' if action == "créé" else 'UPDATE_SOMMAIRE',
                object_id=sommaire_avis.id,
                object_type='SommaireEtAvis',
                details=f"Sommaire et avis {action} pour l'acheteur {acheteur.nom} ({acheteur.code})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": f"Sommaire et avis {action} avec succès",
                "data": GetSommaireEtAvisSerializer(sommaire_avis).data
            }, status=http_status)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime le sommaire et avis de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            sommaire_avis = SommaireEtAvis.objects.get(acheteur=acheteur)
            
            # Log d'activité avant suppression
            ActivityLog.objects.create(
                user=request.user,
                action_type='DELETE_SOMMAIRE',
                object_id=sommaire_avis.id,
                object_type='SommaireEtAvis',
                details=f"Sommaire et avis supprimé pour l'acheteur {acheteur.nom} ({acheteur.code})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            sommaire_avis.delete()
            return Response({
                "message": "Sommaire et avis supprimé avec succès"
            }, status=status.HTTP_200_OK)
        except SommaireEtAvis.DoesNotExist:
            return Response({
                "message": "Aucun sommaire et avis à supprimer"
            }, status=status.HTTP_404_NOT_FOUND)










class ListAcheteurConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        conseil_list = Advice.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            conseil_list = conseil_list.filter(
                Q(forces__icontains=search_term)
                | Q(faiblesses__icontains=search_term)
                | Q(opportunites__icontains=search_term)
                | Q(dynamisme_long_terme__icontains=search_term)
            )

        paginator = Paginator(conseil_list, 10)  # 10 enregistrements par page
        conseil_page = paginator.get_page(page_number)
        serializer = AdviceSerializer(conseil_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": conseil_page.has_next(),
                "previous": conseil_page.has_previous(),
            }
        )


class SearchAcheteurConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conseil_list = Advice.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(forces__icontains=search_term)
                | Q(faiblesses__icontains=search_term)
                | Q(opportunites__icontains=search_term)
                | Q(dynamisme_long_terme__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(conseil_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        conseil_page = paginator.get_page(page_number)
        serializer = AdviceSerializer(conseil_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": conseil_page.has_next(),
                "previous": conseil_page.has_previous(),
            }
        )


class AddAcheteurConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddAdviceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, advice_id, *args, **kwargs):
        conseil = Advice.objects.filter(id=advice_id, acheteur_id=acheteur_id).first()
        if not conseil:
            return Response(
                {"detail": "Conseil non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetAdviceSerializer(conseil)
        return Response(serializer.data)

    def put(self, request, acheteur_id, advice_id, *args, **kwargs):
        conseil = Advice.objects.filter(id=advice_id, acheteur_id=acheteur_id).first()
        if not conseil:
            return Response(
                {"detail": "Conseil non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditAdviceSerializer(conseil, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conseils = Advice.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not conseils.exists():
            return Response(
                {"error": "Aucun conseil trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = conseils.delete()
        return Response(
            {"message": f"{count} conseils supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
        

class AcheteurAdviceView(APIView):
    """
    API pour gérer les conseils unique d'un acheteur
    Méthodes: GET, POST (create/update), DELETE
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère les conseils de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            advice = Advice.objects.get(acheteur=acheteur)
            serializer = GetAdviceSerializer(advice)
            return Response({
                "exists": True,
                "data": serializer.data
            })
        except Advice.DoesNotExist:
            return Response({
                "message": "Aucun conseil trouvé pour cet acheteur",
                "exists": False
            }, status=status.HTTP_404_NOT_FOUND)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée ou met à jour les conseils de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Vérifier si un conseil existe déjà
        try:
            advice = Advice.objects.get(acheteur=acheteur)
            serializer = EditAdviceSerializer(
                advice, data=request.data, partial=True
            )
            action = "mis à jour"
            http_status = status.HTTP_200_OK
        except Advice.DoesNotExist:
            data = request.data.copy()
            data["acheteur"] = acheteur_id
            serializer = AddAdviceSerializer(data=data)
            action = "créé"
            http_status = status.HTTP_201_CREATED
        
        if serializer.is_valid():
            advice = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_ADVICE' if action == "créé" else 'UPDATE_ADVICE',
                object_id=advice.id,
                object_type='Advice',
                details=f"Conseil {action} pour l'acheteur {acheteur.nom} ({acheteur.code})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": f"Conseil {action} avec succès",
                "data": GetAdviceSerializer(advice).data
            }, status=http_status)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime les conseils de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            advice = Advice.objects.get(acheteur=acheteur)
            
            # Log d'activité avant suppression
            ActivityLog.objects.create(
                user=request.user,
                action_type='DELETE_ADVICE',
                object_id=advice.id,
                object_type='Advice',
                details=f"Conseil supprimé pour l'acheteur {acheteur.nom} ({acheteur.code})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            advice.delete()
            return Response({
                "message": "Conseil supprimé avec succès"
            }, status=status.HTTP_200_OK)
        except Advice.DoesNotExist:
            return Response({
                "message": "Aucun conseil à supprimer"
            }, status=status.HTTP_404_NOT_FOUND)










class ListAcheteurGeopoliticView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        geopolitics_list = Geopolitics.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            geopolitics_list = geopolitics_list.filter(
                Q(donnees_politiques__icontains=search_term)
                | Q(donnees_economiques__icontains=search_term)
            )

        paginator = Paginator(geopolitics_list, 10)  # 10 enregistrements par page
        geopolitics_page = paginator.get_page(page_number)
        serializer = GeopoliticsSerializer(geopolitics_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": geopolitics_page.has_next(),
                "previous": geopolitics_page.has_previous(),
            }
        )


class SearchAcheteurGeopoliticView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        geopolitics_list = Geopolitics.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(donnees_politiques__icontains=search_term)
                | Q(donnees_economiques__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(geopolitics_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        geopolitics_page = paginator.get_page(page_number)
        serializer = GeopoliticsSerializer(geopolitics_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": geopolitics_page.has_next(),
                "previous": geopolitics_page.has_previous(),
            }
        )


class AddAcheteurGeopoliticView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddGeopoliticsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurGeopoliticView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, geopolitic_id, *args, **kwargs):
        geopolitics = Geopolitics.objects.filter(
            id=geopolitic_id, acheteur_id=acheteur_id
        ).first()
        if not geopolitics:
            return Response(
                {"detail": "Donnée géopolitique non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetGeopoliticsSerializer(geopolitics)
        return Response(serializer.data)

    def put(self, request, acheteur_id, geopolitic_id, *args, **kwargs):
        geopolitics = Geopolitics.objects.filter(
            id=geopolitic_id, acheteur_id=acheteur_id
        ).first()
        if not geopolitics:
            return Response(
                {"detail": "Donnée géopolitique non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditGeopoliticsSerializer(
            geopolitics, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurGeopoliticView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        geopolitics = Geopolitics.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not geopolitics.exists():
            return Response(
                {"error": "Aucune donnée géopolitique trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = geopolitics.delete()
        return Response(
            {"message": f"{count} données géopolitiques supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        
            
class AcheteurGeopoliticsView(APIView):
    """
    API pour gérer l'analyse géopolitique unique d'un acheteur
    Méthodes: GET, POST (create/update), DELETE
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère l'analyse géopolitique de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        geopolitic = Geopolitics.objects.filter(acheteur=acheteur).order_by('-created_at').first()
        if geopolitic:
            serializer = GetGeopoliticsSerializer(geopolitic)

            # Ajouter le score moyen calculé
            data = serializer.data
            scores = []
            for field in ['stabilite_politique', 'etat_droit', 'efficacite', 'qualite', 'liberte_expression']:
                if data[field] and data[field].isdigit():
                    scores.append(int(data[field]))

            if scores:
                data['score_moyen'] = round(sum(scores) / len(scores), 1)
            else:
                data['score_moyen'] = 0

            return Response({
                "exists": True,
                "data": data
            })
        else:
            return Response({
                "message": "Aucune analyse géopolitique trouvée pour cet acheteur",
                "exists": False
            }, status=status.HTTP_404_NOT_FOUND)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée ou met à jour l'analyse géopolitique de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Validation des scores (0-10)
        score_fields = ['stabilite_politique', 'etat_droit', 'efficacite', 'qualite', 'liberte_expression']
        for field in score_fields:
            if field in request.data and request.data[field]:
                try:
                    score = int(request.data[field])
                    if not (0 <= score <= 10):
                        return Response({
                            field: [f"Le score doit être compris entre 0 et 10. Valeur reçue: {score}"]
                        }, status=status.HTTP_400_BAD_REQUEST)
                except ValueError:
                    return Response({
                        field: ["Le score doit être un nombre entier entre 0 et 10"]
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si une analyse existe déjà
        geopolitic = Geopolitics.objects.filter(acheteur=acheteur).order_by('-created_at').first()
        if geopolitic:
            serializer = EditGeopoliticsSerializer(
                geopolitic, data=request.data, partial=True
            )
            action = "mise à jour"
            http_status = status.HTTP_200_OK
        else:
            data = request.data.copy()
            data["acheteur"] = acheteur_id
            serializer = AddGeopoliticsSerializer(data=data)
            action = "créée"
            http_status = status.HTTP_201_CREATED
        
        if serializer.is_valid():
            geopolitic = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_GEOPOLITIC' if action == "créée" else 'UPDATE_GEOPOLITIC',
                object_id=geopolitic.id,
                object_type='Geopolitics',
                details=f"Analyse géopolitique {action} pour l'acheteur {acheteur.nom} ({acheteur.code})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": f"Analyse géopolitique {action} avec succès",
                "data": GetGeopoliticsSerializer(geopolitic).data
            }, status=http_status)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id):
        """Supprime l'analyse géopolitique de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        try:
            geopolitic = Geopolitics.objects.get(acheteur=acheteur)
            
            # Log d'activité avant suppression
            ActivityLog.objects.create(
                user=request.user,
                action_type='DELETE_GEOPOLITIC',
                object_id=geopolitic.id,
                object_type='Geopolitics',
                details=f"Analyse géopolitique supprimée pour l'acheteur {acheteur.nom} ({acheteur.code})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            geopolitic.delete()
            return Response({
                "message": "Analyse géopolitique supprimée avec succès"
            }, status=status.HTTP_200_OK)
        except Geopolitics.DoesNotExist:
            return Response({
                "message": "Aucune analyse géopolitique à supprimer"
            }, status=status.HTTP_404_NOT_FOUND)











class ListAcheteurBankingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        banking_list = Banquier.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            banking_list = banking_list.filter(
                Q(nom_banque__icontains=search_term)
                | Q(numero_compte__icontains=search_term)
                | Q(type_relation__icontains=search_term)
                | Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(banking_list, 10)  # 10 enregistrements par page
        banking_page = paginator.get_page(page_number)
        serializer = BanquierSerializer(banking_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": banking_page.has_next(),
                "previous": banking_page.has_previous(),
            }
        )


class SearchAcheteurBankingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        banking_list = Banquier.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(nom_banque__icontains=search_term)
                | Q(numero_compte__icontains=search_term)
                | Q(type_relation__icontains=search_term)
                | Q(commentaire__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(banking_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get("page", 1)
        banking_page = paginator.get_page(page_number)
        serializer = BanquierSerializer(banking_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": banking_page.has_next(),
                "previous": banking_page.has_previous(),
            }
        )


class AddAcheteurBankingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddBanquierSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurBankingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, banking_id, *args, **kwargs):
        banking = Banquier.objects.filter(
            id=banking_id, acheteur_id=acheteur_id
        ).first()
        if not banking:
            return Response(
                {"detail": "Donnée bancaire non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = GetBanquierSerializer(banking)
        return Response(serializer.data)

    def put(self, request, acheteur_id, banking_id, *args, **kwargs):
        banking = Banquier.objects.filter(
            id=banking_id, acheteur_id=acheteur_id
        ).first()
        if not banking:
            return Response(
                {"detail": "Donnée bancaire non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditBanquierSerializer(banking, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurBankingView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        banking = Banquier.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not banking.exists():
            return Response(
                {"error": "Aucune donnée bancaire trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = banking.delete()
        return Response(
            {"message": f"{count} données bancaires supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        

class AcheteurBanquierListView(APIView):
    """Vue pour lister et créer des banquiers pour un acheteur"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self, acheteur_id):
        """Retourne le queryset des banquiers pour un acheteur"""
        return Banquier.objects.filter(
            acheteur_id=acheteur_id,
            deleted__isnull=True
        ).select_related('ville', 'couleur_commentaire').order_by('-created_at')
    
    def get(self, request, acheteur_id, *args, **kwargs):
        """Lister les banquiers d'un acheteur"""
        # Vérifier que l'acheteur existe
        try:
            acheteur = Acheteur.objects.get(id=acheteur_id, deleted__isnull=True)
        except Acheteur.DoesNotExist:
            return Response(
                {"error": "Acheteur non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer les banquiers avec pagination
        banquiers = self.get_queryset(acheteur_id)
        
        # Pagination
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        
        try:
            page = int(page)
            page_size = int(page_size)
        except ValueError:
            page = 1
            page_size = 20
        
        # Limiter la taille de page
        page_size = min(page_size, 100)
        
        # Calculer les indices
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        total_count = banquiers.count()
        total_pages = (total_count + page_size - 1) // page_size
        
        # Récupérer les données paginées
        paginated_banquiers = banquiers[start_index:end_index]
        
        # Sérialiser les données
        serializer = BanquierListSerializer(paginated_banquiers, many=True)
        
        # Retourner la réponse avec les métadonnées de pagination
        return Response({
            'count': total_count,
            'total_pages': total_pages,
            'current_page': page,
            'page_size': page_size,
            'start_index': start_index + 1 if total_count > 0 else 0,
            'end_index': min(end_index, total_count),
            'previous': page > 1,
            'next': page < total_pages,
            'results': serializer.data
        })
    
    def post(self, request, acheteur_id, *args, **kwargs):
        """Créer un nouveau banquier"""
        # Vérifier que l'acheteur existe
        try:
            acheteur = Acheteur.objects.get(id=acheteur_id, deleted__isnull=True)
        except Acheteur.DoesNotExist:
            return Response(
                {"error": "Acheteur non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Ajouter l'acheteur dans les données
        data = request.data.copy()
        data['acheteur'] = acheteur_id
        
        # Gérer les champs vides
        for field in ['numero_compte', 'type_relation', 'numero', 'rue', 'code_postal', 'commentaire', 'ville']:
            if field in data and data[field] == '':
                data[field] = None
        
        # Gérer couleur_commentaire vide
        if 'couleur_commentaire' in data and data['couleur_commentaire'] == '':
            data['couleur_commentaire'] = None
        
        serializer = AddBanquierSerializer(data=data)
        
        if serializer.is_valid():
            try:
                # Créer le banquier avec l'utilisateur courant
                banquier = serializer.save(
                    created_by=request.user,
                    updated_by=request.user
                )
                
                # Sérialiser la réponse
                response_serializer = GetBanquierSerializer(banquier)
                return Response(
                    {
                        'message': 'Banquier créé avec succès',
                        'data': response_serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                logger.error(f"Erreur lors de la création du banquier: {e}")
                return Response(
                    {'error': 'Erreur lors de la création du banquier'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, acheteur_id, *args, **kwargs):
        """Supprimer plusieurs banquiers"""
        # Vérifier que l'acheteur existe
        try:
            acheteur = Acheteur.objects.get(id=acheteur_id, deleted__isnull=True)
        except Acheteur.DoesNotExist:
            return Response(
                {"error": "Acheteur non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier si des IDs sont fournis
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {'error': 'Aucun ID fourni pour la suppression'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que les IDs sont des entiers
        try:
            ids = [int(id) for id in ids]
        except (ValueError, TypeError):
            return Response(
                {'error': 'Les IDs doivent être des nombres entiers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer les banquiers
        banquiers = Banquier.objects.filter(
            id__in=ids,
            acheteur=acheteur,
            deleted__isnull=True
        )
        
        count = banquiers.count()
        
        if count == 0:
            return Response(
                {'error': 'Aucun banquier trouvé avec les IDs fournis'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Soft delete
        for banquier in banquiers:
            banquier.delete()
        
        return Response(
            {'message': f'{count} banquier(s) supprimé(s) avec succès'},
            status=status.HTTP_200_OK
        )


class AcheteurBanquierDetailView(APIView):
    """Vue pour récupérer, modifier et supprimer un banquier"""
    permission_classes = [IsAuthenticated]
    
    def get_banquier(self, acheteur_id, banquier_id):
        """Récupère un banquier spécifique"""
        try:
            acheteur = Acheteur.objects.get(id=acheteur_id, deleted__isnull=True)
        except Acheteur.DoesNotExist:
            return None, Response(
                {"error": "Acheteur non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            banquier = Banquier.objects.select_related('ville', 'couleur_commentaire').get(
                id=banquier_id,
                acheteur=acheteur,
                deleted__isnull=True
            )
            return banquier, None
        except Banquier.DoesNotExist:
            return None, Response(
                {"error": "Banquier non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def get(self, request, acheteur_id, banquier_id, *args, **kwargs):
        """Récupérer les détails d'un banquier"""
        banquier, error_response = self.get_banquier(acheteur_id, banquier_id)
        
        if error_response:
            return error_response
        
        serializer = GetBanquierSerializer(banquier)
        return Response(serializer.data)
    
    def put(self, request, acheteur_id, banquier_id, *args, **kwargs):
        """Mettre à jour complètement un banquier"""
        banquier, error_response = self.get_banquier(acheteur_id, banquier_id)
        
        if error_response:
            return error_response
        
        serializer = EditBanquierSerializer(banquier, data=request.data)
        
        if serializer.is_valid():
            updated_banquier = serializer.save()
            
            # Retourner les données mises à jour
            response_serializer = GetBanquierSerializer(updated_banquier)
            return Response(
                {
                    'message': 'Banquier mis à jour avec succès',
                    'data': response_serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def patch(self, request, acheteur_id, banquier_id, *args, **kwargs):
        """Mettre à jour partiellement un banquier"""
        banquier, error_response = self.get_banquier(acheteur_id, banquier_id)
        
        if error_response:
            return error_response
        
        serializer = EditBanquierSerializer(banquier, data=request.data, partial=True)
        
        if serializer.is_valid():
            updated_banquier = serializer.save()
            
            # Retourner les données mises à jour
            response_serializer = GetBanquierSerializer(updated_banquier)
            return Response(
                {
                    'message': 'Banquier mis à jour avec succès',
                    'data': response_serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, acheteur_id, banquier_id, *args, **kwargs):
        """Supprimer un banquier"""
        banquier, error_response = self.get_banquier(acheteur_id, banquier_id)
        
        if error_response:
            return error_response
        
        # Soft delete
        banquier.delete()
        
        return Response(
            {'message': 'Banquier supprimé avec succès'},
            status=status.HTTP_200_OK
        )


class BanquierStatsView(APIView):
    """Vue pour les statistiques des banquiers d'un acheteur"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, acheteur_id, *args, **kwargs):
        """Récupérer les statistiques des banquiers"""
        try:
            acheteur = Acheteur.objects.get(id=acheteur_id, deleted__isnull=True)
        except Acheteur.DoesNotExist:
            return Response(
                {"error": "Acheteur non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # CORRECTION : Enlever select_related pour la queryset principale
        banquiers = Banquier.objects.filter(
            acheteur=acheteur,
            deleted__isnull=True
        )
        
        total_banquiers = banquiers.count()
        
        # Utiliser une seule requête pour plusieurs statistiques
        stats_data = banquiers.aggregate(
            total=Count('id'),
            avec_commentaire=Count('id', filter=~Q(commentaire='')),
            avec_compte=Count('id', filter=~Q(numero_compte='')),
            avec_adresse=Count('id', filter=~Q(numero='') & ~Q(rue='')),
            avec_couleur=Count('id', filter=Q(couleur_commentaire__isnull=False))
        )
        
        stats = {
            'total': stats_data['total'],
            'avec_commentaire': stats_data['avec_commentaire'],
            'avec_compte': stats_data['avec_compte'],
            'avec_adresse': stats_data['avec_adresse'],
            'avec_couleur': stats_data['avec_couleur'],
        }
        
        stats['sans_compte'] = stats['total'] - stats['avec_compte']
        
        # Calculer les pourcentages
        if stats['total'] > 0:
            stats['pourcentage_avec_commentaire'] = round(
                (stats['avec_commentaire'] / stats['total'] * 100), 2
            )
            stats['pourcentage_avec_compte'] = round(
                (stats['avec_compte'] / stats['total'] * 100), 2
            )
            stats['pourcentage_avec_adresse'] = round(
                (stats['avec_adresse'] / stats['total'] * 100), 2
            )
        else:
            stats['pourcentage_avec_commentaire'] = 0
            stats['pourcentage_avec_compte'] = 0
            stats['pourcentage_avec_adresse'] = 0
        
        # OPTIMISATION : Utiliser une requête séparée pour les statistiques agrégées
        # Ville - utiliser .values() pour éviter select_related
        banquiers_par_ville = banquiers.filter(
            ville__isnull=False
        ).values('ville__nom', 'ville__code').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        stats['repartition_par_ville'] = list(banquiers_par_ville)
        
        # Couleur
        banquiers_par_couleur = banquiers.filter(
            couleur_commentaire__isnull=False
        ).values(
            'couleur_commentaire__couleur',
            'couleur_commentaire__code'
        ).annotate(count=Count('id')).order_by('-count')[:10]
        
        stats['repartition_par_couleur'] = list(banquiers_par_couleur)
        
        # Répartition par type de relation
        banquiers_par_relation = banquiers.exclude(
            type_relation=''
        ).values('type_relation').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        stats['repartition_par_relation'] = list(banquiers_par_relation)
        
        # Banques uniques
        stats['banques_uniques'] = banquiers.values('nom_banque').distinct().count()
        
        # CORRECTION : Dernière mise à jour - utiliser une requête séparée
        # NE PAS utiliser .only() après select_related
        dernier_banquier = banquiers.order_by('-updated_at').values(
            'updated_at', 'nom_banque'
        ).first()
        
        if dernier_banquier:
            stats['derniere_mise_a_jour'] = dernier_banquier['updated_at'].isoformat()
            stats['dernier_banquier'] = dernier_banquier['nom_banque']
        else:
            stats['derniere_mise_a_jour'] = None
            stats['dernier_banquier'] = None
        
        return Response(stats)


class VilleSearchAPIView(generics.ListAPIView):
    """API pour la recherche de villes avec pagination"""
    serializer_class = VilleSerializer
    
    def get_queryset(self):
        queryset = Ville.objects.all()
        
        # Filtre par recherche
        search_term = self.request.query_params.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(nom__icontains=search_term) | 
                Q(code__icontains=search_term)
            )
        
        # Limiter si trop de résultats
        return queryset.order_by('nom')[:100]  # Limiter à 100 résultats
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Pagination simple
        page = int(request.query_params.get('page', 1))
        page_size = 20
        start = (page - 1) * page_size
        end = start + page_size
        
        serializer = self.get_serializer(queryset[start:end], many=True)
        
        return Response({
            'results': serializer.data,
            'count': queryset.count(),
            'next': end < queryset.count()
        })





class ListAcheteurActifAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")
        request.query_params.get("annee", "")
        biens_installations_equipements_min = request.query_params.get(
            "biens_installations_equipements_min", ""
        )
        biens_installations_equipements_max = request.query_params.get(
            "biens_installations_equipements_max", ""
        )

        try:
            biens_installations_equipements_min = (
                Decimal(biens_installations_equipements_min)
                if biens_installations_equipements_min
                else None
            )
            biens_installations_equipements_max = (
                Decimal(biens_installations_equipements_max)
                if biens_installations_equipements_max
                else None
            )
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de biens_installations_equipements_min et biens_installations_equipements_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        actif_list = ActifA.objects.filter(acheteur_id=acheteur_id).order_by("-created_at")
        if search_term:
            actif_list = actif_list.filter(
                Q(biens_installations_equipements__icontains=search_term)
                | Q(inventaire__icontains=search_term)
                | Q(creances_commerciales_autres_creances__icontains=search_term)
                | Q(actif_impots_courant__icontains=search_term)
                | Q(annee__annee__icontains=search_term)
                | Q(caisses_banques__icontains=search_term)
            )

        if biens_installations_equipements_min is not None:
            actif_list = actif_list.filter(
                biens_installations_equipements__gte=biens_installations_equipements_min
            )

        if biens_installations_equipements_max is not None:
            actif_list = actif_list.filter(
                biens_installations_equipements__lte=biens_installations_equipements_max
            )

        paginator = Paginator(actif_list, 10)
        actif_page = paginator.get_page(page_number)
        serializer = ActifASerializer(actif_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": actif_page.has_next(),
                "previous": actif_page.has_previous(),
            }
        )


class SearchAcheteurActifAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        actif_list = ActifA.objects.filter(
            acheteur_id=acheteur_id
        ).filter(
            Q(biens_installations_equipements__icontains=search_term)
            | Q(inventaire__icontains=search_term)
            | Q(creances_commerciales_autres_creances__icontains=search_term)
            | Q(actif_impots_courant__icontains=search_term)
            | Q(annee__annee__icontains=search_term)
            | Q(caisses_banques__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(actif_list, 10)
        page_number = request.query_params.get("page", 1)
        actif_page = paginator.get_page(page_number)
        serializer = ActifASerializer(actif_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": actif_page.has_next(),
                "previous": actif_page.has_previous(),
            }
        )


class AddAcheteurActifAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        annee_id = data.get("annee")
        existing = ActifA.objects.filter(acheteur_id=acheteur_id, annee_id=annee_id).first()
        if existing:
            serializer = EditActifASerializer(existing, data=data, partial=False, context={"request": request})
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer = AddActifASerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save(created_by=request.user, updated_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurActifAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, actif_id, *args, **kwargs):
        actif = ActifA.objects.filter(id=actif_id, acheteur_id=acheteur_id).first()
        if not actif:
            return Response(
                {"detail": "Actif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetActifASerializer(actif)
        return Response(serializer.data)

    def put(self, request, acheteur_id, actif_id, *args, **kwargs):
        actif = ActifA.objects.filter(id=actif_id, acheteur_id=acheteur_id).first()
        if not actif:
            return Response(
                {"detail": "Actif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditActifASerializer(
            actif, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurActifAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        actifs = ActifA.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not actifs.exists():
            return Response(
                {"error": "Aucun actif trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = actifs.delete()
        return Response(
            {"message": f"{count} actifs supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class ListAcheteurPassifAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")
        request.query_params.get("annee", "")
        capital_reserves_min = request.query_params.get("capital_reserves_min", "")
        capital_reserves_max = request.query_params.get("capital_reserves_max", "")

        try:
            capital_reserves_min = (
                Decimal(capital_reserves_min) if capital_reserves_min else None
            )
            capital_reserves_max = (
                Decimal(capital_reserves_max) if capital_reserves_max else None
            )
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de capital_reserves_min et capital_reserves_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        passif_list = PassifA.objects.filter(acheteur_id=acheteur_id).order_by("-created_at")
        if search_term:
            passif_list = passif_list.filter(
                Q(capital_reserves__icontains=search_term)
                | Q(capital_declare__icontains=search_term)
                | Q(benefices_non_distribues__icontains=search_term)
                | Q(pret_bancaire__icontains=search_term)
                | Q(compte_courant_administrateurs__icontains=search_term)
                | Q(dettes_commerciales_autres_dettes__icontains=search_term)
                | Q(decouvert_bancaire__icontains=search_term)
                | Q(impots__icontains=search_term)
                | Q(annee__annee__icontains=search_term)
            )

        if capital_reserves_min is not None:
            passif_list = passif_list.filter(capital_reserves__gte=capital_reserves_min)

        if capital_reserves_max is not None:
            passif_list = passif_list.filter(capital_reserves__lte=capital_reserves_max)

        paginator = Paginator(passif_list, 10)
        passif_page = paginator.get_page(page_number)
        serializer = PassifASerializer(passif_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": passif_page.has_next(),
                "previous": passif_page.has_previous(),
            }
        )


class SearchAcheteurPassifAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        passif_list = PassifA.objects.filter(
            acheteur_id=acheteur_id
        ).filter(
            Q(capital_reserves__icontains=search_term)
            | Q(capital_declare__icontains=search_term)
            | Q(benefices_non_distribues__icontains=search_term)
            | Q(pret_bancaire__icontains=search_term)
            | Q(compte_courant_administrateurs__icontains=search_term)
            | Q(dettes_commerciales_autres_dettes__icontains=search_term)
            | Q(decouvert_bancaire__icontains=search_term)
            | Q(impots__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(passif_list, 10)
        page_number = request.query_params.get("page", 1)
        passif_page = paginator.get_page(page_number)
        serializer = PassifASerializer(passif_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": passif_page.has_next(),
                "previous": passif_page.has_previous(),
            }
        )


class AddAcheteurPassifAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        annee_id = data.get("annee")
        existing = PassifA.objects.filter(acheteur_id=acheteur_id, annee_id=annee_id).first()
        if existing:
            serializer = EditPassifASerializer(existing, data=data, partial=False, context={"request": request})
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer = AddPassifASerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save(created_by=request.user, updated_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurPassifAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, passif_id, *args, **kwargs):
        passif = PassifA.objects.filter(id=passif_id, acheteur_id=acheteur_id).first()
        if not passif:
            return Response(
                {"detail": "Passif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetPassifASerializer(passif)
        return Response(serializer.data)

    def put(self, request, acheteur_id, passif_id, *args, **kwargs):
        passif = PassifA.objects.filter(id=passif_id, acheteur_id=acheteur_id).first()
        if not passif:
            return Response(
                {"detail": "Passif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditPassifASerializer(
            passif, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurPassifAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        passifs = PassifA.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not passifs.exists():
            return Response(
                {"error": "Aucun passif trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = passifs.delete()
        return Response(
            {"message": f"{count} passifs supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class ListAcheteurResultatAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")
        request.query_params.get("annee", "")
        produits_activites_ordinaires_min = request.query_params.get(
            "produits_activites_ordinaires_min", ""
        )
        produits_activites_ordinaires_max = request.query_params.get(
            "produits_activites_ordinaires_max", ""
        )

        try:
            produits_activites_ordinaires_min = (
                Decimal(produits_activites_ordinaires_min)
                if produits_activites_ordinaires_min
                else None
            )
            produits_activites_ordinaires_max = (
                Decimal(produits_activites_ordinaires_max)
                if produits_activites_ordinaires_max
                else None
            )
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de produits_activites_ordinaires_min et produits_activites_ordinaires_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        resultat_list = ResultatA.objects.filter(acheteur_id=acheteur_id).order_by("-created_at")
        if search_term:
            resultat_list = resultat_list.filter(
                Q(produits_activites_ordinaires__icontains=search_term)
                | Q(ventes__icontains=search_term)
                | Q(charges_exploitation__icontains=search_term)
                | Q(frais_vente_generaux_administratifs__icontains=search_term)
                | Q(autres_revenus__icontains=search_term)
                | Q(frais_financier__icontains=search_term)
                | Q(charge_impot_sur_revenu__icontains=search_term)
                | Q(autres_elements_resultat_global__icontains=search_term)
                | Q(annee__annee__icontains=search_term)
            )

        if produits_activites_ordinaires_min is not None:
            resultat_list = resultat_list.filter(
                produits_activites_ordinaires__gte=produits_activites_ordinaires_min
            )

        if produits_activites_ordinaires_max is not None:
            resultat_list = resultat_list.filter(
                produits_activites_ordinaires__lte=produits_activites_ordinaires_max
            )

        paginator = Paginator(resultat_list, 10)
        resultat_page = paginator.get_page(page_number)
        serializer = ResultatASerializer(resultat_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": resultat_page.has_next(),
                "previous": resultat_page.has_previous(),
            }
        )


class SearchAcheteurResultatAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resultat_list = ResultatA.objects.filter(
            acheteur_id=acheteur_id
        ).filter(
            Q(produits_activites_ordinaires__icontains=search_term)
            | Q(ventes__icontains=search_term)
            | Q(charges_exploitation__icontains=search_term)
            | Q(frais_vente_generaux_administratifs__icontains=search_term)
            | Q(autres_revenus__icontains=search_term)
            | Q(frais_financier__icontains=search_term)
            | Q(charge_impot_sur_revenu__icontains=search_term)
            | Q(autres_elements_resultat_global__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(resultat_list, 10)
        page_number = request.query_params.get("page", 1)
        resultat_page = paginator.get_page(page_number)
        serializer = ResultatASerializer(resultat_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": resultat_page.has_next(),
                "previous": resultat_page.has_previous(),
            }
        )


class AddAcheteurResultatAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        annee_id = data.get("annee")
        existing = ResultatA.objects.filter(acheteur_id=acheteur_id, annee_id=annee_id).first()
        if existing:
            serializer = EditResultatASerializer(existing, data=data, partial=False, context={"request": request})
            if serializer.is_valid():
                serializer.save(updated_by=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer = AddResultatASerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save(created_by=request.user, updated_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurResultatAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, resultat_id, *args, **kwargs):
        resultat = ResultatA.objects.filter(id=resultat_id, acheteur_id=acheteur_id).first()
        if not resultat:
            return Response(
                {"detail": "Résultat non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetResultatASerializer(resultat)
        return Response(serializer.data)

    def put(self, request, acheteur_id, resultat_id, *args, **kwargs):
        resultat = ResultatA.objects.filter(id=resultat_id, acheteur_id=acheteur_id).first()
        if not resultat:
            return Response(
                {"detail": "Résultat non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditResultatASerializer(
            resultat, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurResultatAnglaisView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resultats = ResultatA.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not resultats.exists():
            return Response(
                {"error": "Aucun résultat trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = resultats.delete()
        return Response(
            {"message": f"{count} résultats supprimés avec succès."},
            status=status.HTTP_200_OK,
        )



class ListAcheteurActifClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        
        # Numeric range filters
        capital_souscrit_non_app_min = request.query_params.get("capital_souscrit_non_app_min", "")
        capital_souscrit_non_app_max = request.query_params.get("capital_souscrit_non_app_max", "")
        
        frais_recherche_developpement_min = request.query_params.get("frais_recherche_developpement_min", "")
        frais_recherche_developpement_max = request.query_params.get("frais_recherche_developpement_max", "")
        
        brevet_licence_logiciels_min = request.query_params.get("brevet_licence_logiciels_min", "")
        brevet_licence_logiciels_max = request.query_params.get("brevet_licence_logiciels_max", "")
        
        fonds_commercial_min = request.query_params.get("fonds_commercial_min", "")
        fonds_commercial_max = request.query_params.get("fonds_commercial_max", "")
        
        autres_immobilisations_incorporelles_min = request.query_params.get("autres_immobilisations_incorporelles_min", "")
        autres_immobilisations_incorporelles_max = request.query_params.get("autres_immobilisations_incorporelles_max", "")
        
        terrains_min = request.query_params.get("terrains_min", "")
        terrains_max = request.query_params.get("terrains_max", "")
        
        constructions_min = request.query_params.get("constructions_min", "")
        constructions_max = request.query_params.get("constructions_max", "")
        
        materiels_et_outils_min = request.query_params.get("materiels_et_outils_min", "")
        materiels_et_outils_max = request.query_params.get("materiels_et_outils_max", "")
        
        materiel_de_transport_min = request.query_params.get("materiel_de_transport_min", "")
        materiel_de_transport_max = request.query_params.get("materiel_de_transport_max", "")
        
        autres_immos_corp_min = request.query_params.get("autres_immos_corp_min", "")
        autres_immos_corp_max = request.query_params.get("autres_immos_corp_max", "")
        
        immos_en_cours_min = request.query_params.get("immos_en_cours_min", "")
        immos_en_cours_max = request.query_params.get("immos_en_cours_max", "")
        
        avances_et_acptes_min = request.query_params.get("avances_et_acptes_min", "")
        avances_et_acptes_max = request.query_params.get("avances_et_acptes_max", "")
        
        participations_min = request.query_params.get("participations_min", "")
        participations_max = request.query_params.get("participations_max", "")
        
        prets_min = request.query_params.get("prets_min", "")
        prets_max = request.query_params.get("prets_max", "")
        
        autres_min = request.query_params.get("autres_min", "")
        autres_max = request.query_params.get("autres_max", "")
        
        stocks_mp_min = request.query_params.get("stocks_mp_min", "")
        stocks_mp_max = request.query_params.get("stocks_mp_max", "")
        
        stocks_encours_mp_min = request.query_params.get("stocks_encours_mp_min", "")
        stocks_encours_mp_max = request.query_params.get("stocks_encours_mp_max", "")
        
        stocks_pf_min = request.query_params.get("stocks_pf_min", "")
        stocks_pf_max = request.query_params.get("stocks_pf_max", "")
        
        stocks_encours_pf_min = request.query_params.get("stocks_encours_pf_min", "")
        stocks_encours_pf_max = request.query_params.get("stocks_encours_pf_max", "")
        
        stocks_encours_services_min = request.query_params.get("stocks_encours_services_min", "")
        stocks_encours_services_max = request.query_params.get("stocks_encours_services_max", "")
        
        stocks_mses_min = request.query_params.get("stocks_mses_min", "")
        stocks_mses_max = request.query_params.get("stocks_mses_max", "")
        
        avances_acptes_verses_min = request.query_params.get("avances_acptes_verses_min", "")
        avances_acptes_verses_max = request.query_params.get("avances_acptes_verses_max", "")
        
        clients_et_cptes_rattaches_min = request.query_params.get("clients_et_cptes_rattaches_min", "")
        clients_et_cptes_rattaches_max = request.query_params.get("clients_et_cptes_rattaches_max", "")
        
        autres_creances_min = request.query_params.get("autres_creances_min", "")
        autres_creances_max = request.query_params.get("autres_creances_max", "")
        
        valeurs_a_encaisser_min = request.query_params.get("valeurs_a_encaisser_min", "")
        valeurs_a_encaisser_max = request.query_params.get("valeurs_a_encaisser_max", "")
        
        banques_cheques_postaux_caisse_min = request.query_params.get("banques_cheques_postaux_caisse_min", "")
        banques_cheques_postaux_caisse_max = request.query_params.get("banques_cheques_postaux_caisse_max", "")
        
        cca_min = request.query_params.get("cca_min", "")
        cca_max = request.query_params.get("cca_max", "")
        
        charges_a_repartir_et_frais_etablissement_min = request.query_params.get("charges_a_repartir_et_frais_etablissement_min", "")
        charges_a_repartir_et_frais_etablissement_max = request.query_params.get("charges_a_repartir_et_frais_etablissement_max", "")
        
        primes_de_rbt_min = request.query_params.get("primes_de_rbt_min", "")
        primes_de_rbt_max = request.query_params.get("primes_de_rbt_max", "")
        
        eca_min = request.query_params.get("eca_min", "")
        eca_max = request.query_params.get("eca_max", "")
        
        eene_min = request.query_params.get("eene_min", "")
        eene_max = request.query_params.get("eene_max", "")
        
        effectif_min = request.query_params.get("effectif_min", "")
        effectif_max = request.query_params.get("effectif_max", "")
        
        amortissements_min = request.query_params.get("amortissements_min", "")
        amortissements_max = request.query_params.get("amortissements_max", "")
        
        provisions_stocks_min = request.query_params.get("provisions_stocks_min", "")
        provisions_stocks_max = request.query_params.get("provisions_stocks_max", "")
        
        provisions_creances_min = request.query_params.get("provisions_creances_min", "")
        provisions_creances_max = request.query_params.get("provisions_creances_max", "")
        
        provisions_vmp_min = request.query_params.get("provisions_vmp_min", "")
        provisions_vmp_max = request.query_params.get("provisions_vmp_max", "")

        # Convert string parameters to Decimal where needed
        range_filters = {
            'capital_souscrit_non_app': (capital_souscrit_non_app_min, capital_souscrit_non_app_max),
            'frais_recherche_developpement': (frais_recherche_developpement_min, frais_recherche_developpement_max),
            'brevet_licence_logiciels': (brevet_licence_logiciels_min, brevet_licence_logiciels_max),
            'fonds_commercial': (fonds_commercial_min, fonds_commercial_max),
            'autres_immobilisations_incorporelles': (autres_immobilisations_incorporelles_min, autres_immobilisations_incorporelles_max),
            'terrains': (terrains_min, terrains_max),
            'constructions': (constructions_min, constructions_max),
            'materiels_et_outils': (materiels_et_outils_min, materiels_et_outils_max),
            'materiel_de_transport': (materiel_de_transport_min, materiel_de_transport_max),
            'autres_immos_corp': (autres_immos_corp_min, autres_immos_corp_max),
            'immos_en_cours': (immos_en_cours_min, immos_en_cours_max),
            'avances_et_acptes': (avances_et_acptes_min, avances_et_acptes_max),
            'participations': (participations_min, participations_max),
            'prets': (prets_min, prets_max),
            'autres': (autres_min, autres_max),
            'stocks_mp': (stocks_mp_min, stocks_mp_max),
            'stocks_encours_mp': (stocks_encours_mp_min, stocks_encours_mp_max),
            'stocks_pf': (stocks_pf_min, stocks_pf_max),
            'stocks_encours_pf': (stocks_encours_pf_min, stocks_encours_pf_max),
            'stocks_encours_services': (stocks_encours_services_min, stocks_encours_services_max),
            'stocks_mses': (stocks_mses_min, stocks_mses_max),
            'avances_acptes_verses': (avances_acptes_verses_min, avances_acptes_verses_max),
            'clients_et_cptes_rattaches': (clients_et_cptes_rattaches_min, clients_et_cptes_rattaches_max),
            'autres_creances': (autres_creances_min, autres_creances_max),
            'valeurs_a_encaisser': (valeurs_a_encaisser_min, valeurs_a_encaisser_max),
            'banques_cheques_postaux_caisse': (banques_cheques_postaux_caisse_min, banques_cheques_postaux_caisse_max),
            'cca': (cca_min, cca_max),
            'charges_a_repartir_et_frais_etablissement': (charges_a_repartir_et_frais_etablissement_min, charges_a_repartir_et_frais_etablissement_max),
            'primes_de_rbt': (primes_de_rbt_min, primes_de_rbt_max),
            'eca': (eca_min, eca_max),
            'eene': (eene_min, eene_max),
            'effectif': (effectif_min, effectif_max),
            'amortissements': (amortissements_min, amortissements_max),
            'provisions_stocks': (provisions_stocks_min, provisions_stocks_max),
            'provisions_creances': (provisions_creances_min, provisions_creances_max),
            'provisions_vmp': (provisions_vmp_min, provisions_vmp_max),
        }

        range_values = {}
        for field_name, (min_val, max_val) in range_filters.items():
            try:
                range_values[f'{field_name}_min'] = Decimal(min_val) if min_val else None
                range_values[f'{field_name}_max'] = Decimal(max_val) if max_val else None
            except InvalidOperation:
                return Response(
                    {f"error": f"Les valeurs de {field_name}_min et {field_name}_max doivent être des nombres décimaux valides."},
                    status=400,
                )

        # Start with filtering by acheteur_id
        actif_list = ActifC.objects.filter(acheteur_id=acheteur_id)
        
        # Apply year filter if provided
        if annee:
            actif_list = actif_list.filter(annee__annee__icontains=annee)
        
        # Apply search filter if provided
        if search_term:
            actif_list = actif_list.filter(
                Q(capital_souscrit_non_app__icontains=search_term) |
                Q(frais_recherche_developpement__icontains=search_term) |
                Q(brevet_licence_logiciels__icontains=search_term) |
                Q(fonds_commercial__icontains=search_term) |
                Q(autres_immobilisations_incorporelles__icontains=search_term) |
                Q(terrains__icontains=search_term) |
                Q(constructions__icontains=search_term) |
                Q(materiels_et_outils__icontains=search_term) |
                Q(materiel_de_transport__icontains=search_term) |
                Q(autres_immos_corp__icontains=search_term) |
                Q(immos_en_cours__icontains=search_term) |
                Q(avances_et_acptes__icontains=search_term) |
                Q(participations__icontains=search_term) |
                Q(prets__icontains=search_term) |
                Q(autres__icontains=search_term) |
                Q(stocks_mp__icontains=search_term) |
                Q(stocks_encours_mp__icontains=search_term) |
                Q(stocks_pf__icontains=search_term) |
                Q(stocks_encours_pf__icontains=search_term) |
                Q(stocks_encours_services__icontains=search_term) |
                Q(stocks_mses__icontains=search_term) |
                Q(avances_acptes_verses__icontains=search_term) |
                Q(clients_et_cptes_rattaches__icontains=search_term) |
                Q(autres_creances__icontains=search_term) |
                Q(valeurs_a_encaisser__icontains=search_term) |
                Q(banques_cheques_postaux_caisse__icontains=search_term) |
                Q(cca__icontains=search_term) |
                Q(charges_a_repartir_et_frais_etablissement__icontains=search_term) |
                Q(primes_de_rbt__icontains=search_term) |
                Q(eca__icontains=search_term) |
                Q(eene__icontains=search_term) |
                Q(effectif__icontains=search_term) |
                Q(amortissements__icontains=search_term) |
                Q(provisions_stocks__icontains=search_term) |
                Q(provisions_creances__icontains=search_term) |
                Q(provisions_vmp__icontains=search_term)
            )
        
        # Apply numeric range filters
        for field_name, (min_val, max_val) in range_filters.items():
            min_key = f'{field_name}_min'
            max_key = f'{field_name}_max'
            
            if range_values[min_key] is not None:
                actif_list = actif_list.filter(**{f"{field_name}__gte": range_values[min_key]})
            if range_values[max_key] is not None:
                actif_list = actif_list.filter(**{f"{field_name}__lte": range_values[max_key]})

        # Order by most recent first
        actif_list = actif_list.order_by("-created_at")

        # Paginate results
        paginator = Paginator(actif_list, 10)
        
        try:
            actif_page = paginator.get_page(page_number)
        except Exception:
            return Response(
                {"error": "Numéro de page invalide."},
                status=400,
            )
        
        serializer = ActifCSerializer(actif_page, many=True)

        # Calculate start and end indices for pagination info
        start_index = (actif_page.number - 1) * paginator.per_page + 1 if actif_page else 0
        end_index = min(actif_page.number * paginator.per_page, paginator.count) if actif_page else 0

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": actif_page.has_next(),
                "previous": actif_page.has_previous(),
                "start_index": start_index,
                "end_index": end_index,
            }
        )


class SearchAcheteurActifClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        actif_list = ActifC.objects.filter(
            Q(capital_souscrit_non_app__icontains=search_term)
            | Q(frais_recherche_developpement__icontains=search_term)
            | Q(brevet_licence_logiciels__icontains=search_term)
            | Q(fonds_commercial__icontains=search_term)
            | Q(autres_immobilisations_incorporelles__icontains=search_term)
            | Q(terrains__icontains=search_term)
            | Q(constructions__icontains=search_term)
            | Q(materiels_et_outils__icontains=search_term)
            | Q(materiel_de_transport__icontains=search_term)
            | Q(autres_immos_corp__icontains=search_term)
            | Q(immos_en_cours__icontains=search_term)
            | Q(avances_et_acptes__icontains=search_term)
            | Q(participations__icontains=search_term)
            | Q(prets__icontains=search_term)
            | Q(autres__icontains=search_term)
            | Q(stocks_mp__icontains=search_term)
            | Q(stocks_encours_mp__icontains=search_term)
            | Q(stocks_pf__icontains=search_term)
            | Q(stocks_encours_pf__icontains=search_term)
            | Q(stocks_encours_services__icontains=search_term)
            | Q(stocks_mses__icontains=search_term)
            | Q(avances_acptes_verses__icontains=search_term)
            | Q(clients_et_cptes_rattaches__icontains=search_term)
            | Q(autres_creances__icontains=search_term)
            | Q(valeurs_a_encaisser__icontains=search_term)
            | Q(banques_cheques_postaux_caisse__icontains=search_term)
            | Q(cca__icontains=search_term)
            | Q(charges_a_repartir_et_frais_etablissement__icontains=search_term)
            | Q(primes_de_rbt__icontains=search_term)
            | Q(eca__icontains=search_term)
            | Q(ene__icontains=search_term)
            | Q(effectif__icontains=search_term)
            | Q(amortissements__icontains=search_term)
            | Q(provisions_stocks__icontains=search_term)
            | Q(provisions_creances__icontains=search_term)
            | Q(provisions_vmp__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(actif_list, 10)
        page_number = request.query_params.get("page", 1)
        actif_page = paginator.get_page(page_number)
        serializer = ActifCSerializer(actif_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": actif_page.has_next(),
                "previous": actif_page.has_previous(),
            }
        )


class AddAcheteurActifClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id
        serializer = AddActifCSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurActifClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, actif_id, *args, **kwargs):
        actif = ActifC.objects.filter(id=actif_id, acheteur_id=acheteur_id).first()
        if not actif:
            return Response(
                {"detail": "Actif non trouvé pour cet acheteur."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetActifCSerializer(actif)
        return Response(serializer.data)

    def put(self, request, acheteur_id, actif_id, *args, **kwargs):
        actif = ActifC.objects.filter(id=actif_id, acheteur_id=acheteur_id).first()
        if not actif:
            return Response(
                {"detail": "Actif non trouvé pour cet acheteur."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditActifCSerializer(actif, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurActifClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):  # Add acheteur_id parameter
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the actifs belong to the specified acheteur
        actifs = ActifC.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not actifs.exists():
            return Response(
                {"error": "Aucun actif trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = actifs.delete()
        return Response(
            {"message": f"{count} actifs supprimés avec succès."},
            status=status.HTTP_200_OK,
        )







class ListAcheteurPassifClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):  # Add acheteur_id parameter
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        
        # Numeric range filters
        capital_social_min = request.query_params.get("capital_social_min", "")
        capital_social_max = request.query_params.get("capital_social_max", "")
        
        primes_min = request.query_params.get("primes_min", "")
        primes_max = request.query_params.get("primes_max", "")
        
        ecarts_de_reevaluation_min = request.query_params.get("ecarts_de_reevaluation_min", "")
        ecarts_de_reevaluation_max = request.query_params.get("ecarts_de_reevaluation_max", "")
        
        reserve_min = request.query_params.get("reserve_min", "")
        reserve_max = request.query_params.get("reserve_max", "")
        
        report_a_nouveau_min = request.query_params.get("report_a_nouveau_min", "")
        report_a_nouveau_max = request.query_params.get("report_a_nouveau_max", "")
        
        resultat_exercice_min = request.query_params.get("resultat_exercice_min", "")
        resultat_exercice_max = request.query_params.get("resultat_exercice_max", "")
        
        subv_invest_min = request.query_params.get("subv_invest_min", "")
        subv_invest_max = request.query_params.get("subv_invest_max", "")
        
        provision_regl_min = request.query_params.get("provision_regl_min", "")
        provision_regl_max = request.query_params.get("provision_regl_max", "")
        
        emprunts_min = request.query_params.get("emprunts_min", "")
        emprunts_max = request.query_params.get("emprunts_max", "")
        
        dette_credit_bail_contrat_assimile_min = request.query_params.get("dette_credit_bail_contrat_assimile_min", "")
        dette_credit_bail_contrat_assimile_max = request.query_params.get("dette_credit_bail_contrat_assimile_max", "")
        
        dettes_financiere_diverses_min = request.query_params.get("dettes_financiere_diverses_min", "")
        dettes_financiere_diverses_max = request.query_params.get("dettes_financiere_diverses_max", "")
        
        provision_financiere_risque_charge_min = request.query_params.get("provision_financiere_risque_charge_min", "")
        provision_financiere_risque_charge_max = request.query_params.get("provision_financiere_risque_charge_max", "")
        
        dettes_fournisseurs_divers_min = request.query_params.get("dettes_fournisseurs_divers_min", "")
        dettes_fournisseurs_divers_max = request.query_params.get("dettes_fournisseurs_divers_max", "")
        
        avance_et_acomptes_recu_min = request.query_params.get("avance_et_acomptes_recu_min", "")
        avance_et_acomptes_recu_max = request.query_params.get("avance_et_acomptes_recu_max", "")
        
        dettes_min = request.query_params.get("dettes_min", "")
        dettes_max = request.query_params.get("dettes_max", "")
        
        dettes_fiscales_sociales_min = request.query_params.get("dettes_fiscales_sociales_min", "")
        dettes_fiscales_sociales_max = request.query_params.get("dettes_fiscales_sociales_max", "")
        
        autres_dettes_min = request.query_params.get("autres_dettes_min", "")
        autres_dettes_max = request.query_params.get("autres_dettes_max", "")
        
        banques_credit_escompte_min = request.query_params.get("banques_credit_escompte_min", "")
        banques_credit_escompte_max = request.query_params.get("banques_credit_escompte_max", "")
        
        banque_credit_caisse_min = request.query_params.get("banque_credit_caisse_min", "")
        banque_credit_caisse_max = request.query_params.get("banque_credit_caisse_max", "")
        
        banques_decouvert_min = request.query_params.get("banques_decouvert_min", "")
        banques_decouvert_max = request.query_params.get("banques_decouvert_max", "")
        
        ecart_conversion_passif_min = request.query_params.get("ecart_conversion_passif_min", "")
        ecart_conversion_passif_max = request.query_params.get("ecart_conversion_passif_max", "")

        # Convert string parameters to Decimal where needed
        range_filters = {
            'capital_social': (capital_social_min, capital_social_max),
            'primes': (primes_min, primes_max),
            'ecarts_de_reevaluation': (ecarts_de_reevaluation_min, ecarts_de_reevaluation_max),
            'reserve': (reserve_min, reserve_max),
            'report_a_nouveau': (report_a_nouveau_min, report_a_nouveau_max),
            'resultat_exercice': (resultat_exercice_min, resultat_exercice_max),
            'subv_invest': (subv_invest_min, subv_invest_max),
            'provision_regl': (provision_regl_min, provision_regl_max),
            'emprunts': (emprunts_min, emprunts_max),
            'dette_credit_bail_contrat_assimile': (dette_credit_bail_contrat_assimile_min, dette_credit_bail_contrat_assimile_max),
            'dettes_financiere_diverses': (dettes_financiere_diverses_min, dettes_financiere_diverses_max),
            'provision_financiere_risque_charge': (provision_financiere_risque_charge_min, provision_financiere_risque_charge_max),
            'dettes_fournisseurs_divers': (dettes_fournisseurs_divers_min, dettes_fournisseurs_divers_max),
            'avance_et_acomptes_recu': (avance_et_acomptes_recu_min, avance_et_acomptes_recu_max),
            'dettes': (dettes_min, dettes_max),
            'dettes_fiscales_sociales': (dettes_fiscales_sociales_min, dettes_fiscales_sociales_max),
            'autres_dettes': (autres_dettes_min, autres_dettes_max),
            'banques_credit_escompte': (banques_credit_escompte_min, banques_credit_escompte_max),
            'banque_credit_caisse': (banque_credit_caisse_min, banque_credit_caisse_max),
            'banques_decouvert': (banques_decouvert_min, banques_decouvert_max),
            'ecart_conversion_passif': (ecart_conversion_passif_min, ecart_conversion_passif_max),
        }

        range_values = {}
        for field_name, (min_val, max_val) in range_filters.items():
            try:
                range_values[f'{field_name}_min'] = Decimal(min_val) if min_val else None
                range_values[f'{field_name}_max'] = Decimal(max_val) if max_val else None
            except InvalidOperation:
                return Response(
                    {f"error": f"Les valeurs de {field_name}_min et {field_name}_max doivent être des nombres décimaux valides."},
                    status=400,
                )

        # Start with filtering by acheteur_id
        passif_list = PassifC.objects.filter(acheteur_id=acheteur_id)
        
        # Apply year filter if provided
        if annee:
            passif_list = passif_list.filter(annee__annee__icontains=annee)
        
        # Apply search filter if provided
        if search_term:
            passif_list = passif_list.filter(
                Q(capital_social__icontains=search_term) |
                Q(primes__icontains=search_term) |
                Q(ecarts_de_reevaluation__icontains=search_term) |
                Q(reserve__icontains=search_term) |
                Q(report_a_nouveau__icontains=search_term) |
                Q(resultat_exercice__icontains=search_term) |
                Q(subv_invest__icontains=search_term) |
                Q(provision_regl__icontains=search_term) |
                Q(emprunts__icontains=search_term) |
                Q(dette_credit_bail_contrat_assimile__icontains=search_term) |
                Q(dettes_financiere_diverses__icontains=search_term) |
                Q(provision_financiere_risque_charge__icontains=search_term) |
                Q(dettes_fournisseurs_divers__icontains=search_term) |
                Q(avance_et_acomptes_recu__icontains=search_term) |
                Q(dettes__icontains=search_term) |
                Q(dettes_fiscales_sociales__icontains=search_term) |
                Q(autres_dettes__icontains=search_term) |
                Q(banques_credit_escompte__icontains=search_term) |
                Q(banque_credit_caisse__icontains=search_term) |
                Q(banques_decouvert__icontains=search_term) |
                Q(ecart_conversion_passif__icontains=search_term)
            )
        
        # Apply numeric range filters
        for field_name, (min_val, max_val) in range_filters.items():
            min_key = f'{field_name}_min'
            max_key = f'{field_name}_max'
            
            if range_values[min_key] is not None:
                passif_list = passif_list.filter(**{f"{field_name}__gte": range_values[min_key]})
            if range_values[max_key] is not None:
                passif_list = passif_list.filter(**{f"{field_name}__lte": range_values[max_key]})

        # Order by most recent first
        passif_list = passif_list.order_by("-created_at")

        # Paginate results
        paginator = Paginator(passif_list, 10)
        
        try:
            passif_page = paginator.get_page(page_number)
        except Exception:
            return Response(
                {"error": "Numéro de page invalide."},
                status=400,
            )
        
        serializer = PassifCSerializer(passif_page, many=True)

        # Calculate start and end indices for pagination info
        start_index = (passif_page.number - 1) * paginator.per_page + 1 if passif_page else 0
        end_index = min(passif_page.number * paginator.per_page, paginator.count) if passif_page else 0

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": passif_page.has_next(),
                "previous": passif_page.has_previous(),
                "start_index": start_index,
                "end_index": end_index,
            }
        )


class SearchAcheteurPassifClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):  # Add acheteur_id parameter
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filter by acheteur_id first, then by search term
        passif_list = PassifC.objects.filter(acheteur_id=acheteur_id).filter(
            Q(capital_social__icontains=search_term) |
            Q(primes__icontains=search_term) |
            Q(ecarts_de_reevaluation__icontains=search_term) |
            Q(reserve__icontains=search_term) |
            Q(report_a_nouveau__icontains=search_term) |
            Q(resultat_exercice__icontains=search_term) |
            Q(subv_invest__icontains=search_term) |
            Q(provision_regl__icontains=search_term) |
            Q(emprunts__icontains=search_term) |
            Q(dette_credit_bail_contrat_assimile__icontains=search_term) |
            Q(dettes_financiere_diverses__icontains=search_term) |
            Q(provision_financiere_risque_charge__icontains=search_term) |
            Q(dettes_fournisseurs_divers__icontains=search_term) |
            Q(avance_et_acomptes_recu__icontains=search_term) |
            Q(dettes__icontains=search_term) |
            Q(dettes_fiscales_sociales__icontains=search_term) |
            Q(autres_dettes__icontains=search_term) |
            Q(banques_credit_escompte__icontains=search_term) |
            Q(banque_credit_caisse__icontains=search_term) |
            Q(banques_decouvert__icontains=search_term) |
            Q(ecart_conversion_passif__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(passif_list, 10)
        page_number = request.query_params.get("page", 1)
        
        try:
            passif_page = paginator.get_page(page_number)
        except Exception:
            return Response(
                {"error": "Numéro de page invalide."},
                status=400,
            )
            
        serializer = PassifCSerializer(passif_page, many=True)

        start_index = (passif_page.number - 1) * paginator.per_page + 1 if passif_page else 0
        end_index = min(passif_page.number * paginator.per_page, paginator.count) if passif_page else 0

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": passif_page.has_next(),
                "previous": passif_page.has_previous(),
                "start_index": start_index,
                "end_index": end_index,
            }
        )


class AddAcheteurPassifClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id
        serializer = AddPassifCSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurPassifClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, passif_id, *args, **kwargs):  # Add acheteur_id parameter
        # Verify the passif belongs to the specified acheteur
        passif = PassifC.objects.filter(id=passif_id, acheteur_id=acheteur_id).first()
        if not passif:
            return Response(
                {"detail": "Passif non trouvé pour cet acheteur."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetPassifCSerializer(passif)
        return Response(serializer.data)

    def put(self, request, acheteur_id, passif_id, *args, **kwargs):  # Add acheteur_id parameter
        # Verify the passif belongs to the specified acheteur
        passif = PassifC.objects.filter(id=passif_id, acheteur_id=acheteur_id).first()
        if not passif:
            return Response(
                {"detail": "Passif non trouvé pour cet acheteur."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditPassifCSerializer(passif, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurPassifClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):  # Add acheteur_id parameter
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the passifs belong to the specified acheteur
        passifs = PassifC.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not passifs.exists():
            return Response(
                {"error": "Aucun passif trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = passifs.delete()
        return Response(
            {"message": f"{count} passifs supprimés avec succès."},
            status=status.HTTP_200_OK,
        )







class ListAcheteurResultatClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):  # Add acheteur_id parameter
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        
        # Numeric range filters for all fields
        vente_de_mdses_min = request.query_params.get("vente_de_mdses_min", "")
        vente_de_mdses_max = request.query_params.get("vente_de_mdses_max", "")
        
        ventes_de_produits_fabriques_min = request.query_params.get("ventes_de_produits_fabriques_min", "")
        ventes_de_produits_fabriques_max = request.query_params.get("ventes_de_produits_fabriques_max", "")
        
        travaux_services_vendus_min = request.query_params.get("travaux_services_vendus_min", "")
        travaux_services_vendus_max = request.query_params.get("travaux_services_vendus_max", "")
        
        produit_accessoires_min = request.query_params.get("produit_accessoires_min", "")
        produit_accessoires_max = request.query_params.get("produit_accessoires_max", "")
        
        production_imblise_min = request.query_params.get("production_imblise_min", "")
        production_imblise_max = request.query_params.get("production_imblise_max", "")
        
        subventions_exploitations_min = request.query_params.get("subventions_exploitations_min", "")
        subventions_exploitations_max = request.query_params.get("subventions_exploitations_max", "")
        
        production_stockee_min = request.query_params.get("production_stockee_min", "")
        production_stockee_max = request.query_params.get("production_stockee_max", "")
        
        reprises_de_provision_min = request.query_params.get("reprises_de_provision_min", "")
        reprises_de_provision_max = request.query_params.get("reprises_de_provision_max", "")
        
        transferts_charges_min = request.query_params.get("transferts_charges_min", "")
        transferts_charges_max = request.query_params.get("transferts_charges_max", "")
        
        autres_produits_min = request.query_params.get("autres_produits_min", "")
        autres_produits_max = request.query_params.get("autres_produits_max", "")
        
        achat_mdses_min = request.query_params.get("achat_mdses_min", "")
        achat_mdses_max = request.query_params.get("achat_mdses_max", "")
        
        variation_stock_mdses_min = request.query_params.get("variation_stock_mdses_min", "")
        variation_stock_mdses_max = request.query_params.get("variation_stock_mdses_max", "")
        
        achat_mp_autres_appro_min = request.query_params.get("achat_mp_autres_appro_min", "")
        achat_mp_autres_appro_max = request.query_params.get("achat_mp_autres_appro_max", "")
        
        var_stk_mp_app_min = request.query_params.get("var_stk_mp_app_min", "")
        var_stk_mp_app_max = request.query_params.get("var_stk_mp_app_max", "")
        
        autres_achats_min = request.query_params.get("autres_achats_min", "")
        autres_achats_max = request.query_params.get("autres_achats_max", "")
        
        variation_de_stocks_autres_appro_min = request.query_params.get("variation_de_stocks_autres_appro_min", "")
        variation_de_stocks_autres_appro_max = request.query_params.get("variation_de_stocks_autres_appro_max", "")
        
        transports_min = request.query_params.get("transports_min", "")
        transports_max = request.query_params.get("transports_max", "")
        
        services_ext_min = request.query_params.get("services_ext_min", "")
        services_ext_max = request.query_params.get("services_ext_max", "")
        
        impots_taxes_min = request.query_params.get("impots_taxes_min", "")
        impots_taxes_max = request.query_params.get("impots_taxes_max", "")
        
        autres_charges_valeur_ajoutee_min = request.query_params.get("autres_charges_valeur_ajoutee_min", "")
        autres_charges_valeur_ajoutee_max = request.query_params.get("autres_charges_valeur_ajoutee_max", "")
        
        charges_personnel_min = request.query_params.get("charges_personnel_min", "")
        charges_personnel_max = request.query_params.get("charges_personnel_max", "")
        
        dotation_aux_amorts_min = request.query_params.get("dotation_aux_amorts_min", "")
        dotation_aux_amorts_max = request.query_params.get("dotation_aux_amorts_max", "")
        
        dotation_aux_provisions_min = request.query_params.get("dotation_aux_provisions_min", "")
        dotation_aux_provisions_max = request.query_params.get("dotation_aux_provisions_max", "")
        
        autres_charges_excedent_brute_min = request.query_params.get("autres_charges_excedent_brute_min", "")
        autres_charges_excedent_brute_max = request.query_params.get("autres_charges_excedent_brute_max", "")
        
        revenus_fin_assimiles_min = request.query_params.get("revenus_fin_assimiles_min", "")
        revenus_fin_assimiles_max = request.query_params.get("revenus_fin_assimiles_max", "")
        
        prof_vmp_et_cre_actif_immo_min = request.query_params.get("prof_vmp_et_cre_actif_immo_min", "")
        prof_vmp_et_cre_actif_immo_max = request.query_params.get("prof_vmp_et_cre_actif_immo_max", "")
        
        interets_produit_assim_min = request.query_params.get("interets_produit_assim_min", "")
        interets_produit_assim_max = request.query_params.get("interets_produit_assim_max", "")
        
        reprise_prov_et_transfert_min = request.query_params.get("reprise_prov_et_transfert_min", "")
        reprise_prov_et_transfert_max = request.query_params.get("reprise_prov_et_transfert_max", "")
        
        diff_positive_de_change_min = request.query_params.get("diff_positive_de_change_min", "")
        diff_positive_de_change_max = request.query_params.get("diff_positive_de_change_max", "")
        
        prod_nets_cessions_vmp_min = request.query_params.get("prod_nets_cessions_vmp_min", "")
        prod_nets_cessions_vmp_max = request.query_params.get("prod_nets_cessions_vmp_max", "")
        
        dap_min = request.query_params.get("dap_min", "")
        dap_max = request.query_params.get("dap_max", "")
        
        frais_fin_charges_assi_min = request.query_params.get("frais_fin_charges_assi_min", "")
        frais_fin_charges_assi_max = request.query_params.get("frais_fin_charges_assi_max", "")
        
        diff_negatives_de_change_min = request.query_params.get("diff_negatives_de_change_min", "")
        diff_negatives_de_change_max = request.query_params.get("diff_negatives_de_change_max", "")
        
        ch_nettes_cessions_vmp_min = request.query_params.get("ch_nettes_cessions_vmp_min", "")
        ch_nettes_cessions_vmp_max = request.query_params.get("ch_nettes_cessions_vmp_max", "")
        
        sur_op_gestion_prod_except_min = request.query_params.get("sur_op_gestion_prod_except_min", "")
        sur_op_gestion_prod_except_max = request.query_params.get("sur_op_gestion_prod_except_max", "")
        
        sur_op_en_capital_prod_except_min = request.query_params.get("sur_op_en_capital_prod_except_min", "")
        sur_op_en_capital_prod_except_max = request.query_params.get("sur_op_en_capital_prod_except_max", "")
        
        reprise_prov_transfert_min = request.query_params.get("reprise_prov_transfert_min", "")
        reprise_prov_transfert_max = request.query_params.get("reprise_prov_transfert_max", "")
        
        sur_op_gestion_charg_except_min = request.query_params.get("sur_op_gestion_charg_except_min", "")
        sur_op_gestion_charg_except_max = request.query_params.get("sur_op_gestion_charg_except_max", "")
        
        sur_op_en_capital_charg_except_min = request.query_params.get("sur_op_en_capital_charg_except_min", "")
        sur_op_en_capital_charg_except_max = request.query_params.get("sur_op_en_capital_charg_except_max", "")
        
        dap_et_transfert_charg_except_min = request.query_params.get("dap_et_transfert_charg_except_min", "")
        dap_et_transfert_charg_except_max = request.query_params.get("dap_et_transfert_charg_except_max", "")
        
        participation_salairies_min = request.query_params.get("participation_salairies_min", "")
        participation_salairies_max = request.query_params.get("participation_salairies_max", "")
        
        impot_sur_benefices_min = request.query_params.get("impot_sur_benefices_min", "")
        impot_sur_benefices_max = request.query_params.get("impot_sur_benefices_max", "")

        # Convert string parameters to Decimal where needed
        range_filters = {
            'vente_de_mdses': (vente_de_mdses_min, vente_de_mdses_max),
            'ventes_de_produits_fabriques': (ventes_de_produits_fabriques_min, ventes_de_produits_fabriques_max),
            'travaux_services_vendus': (travaux_services_vendus_min, travaux_services_vendus_max),
            'produit_accessoires': (produit_accessoires_min, produit_accessoires_max),
            'production_imblise': (production_imblise_min, production_imblise_max),
            'subventions_exploitations': (subventions_exploitations_min, subventions_exploitations_max),
            'production_stockee': (production_stockee_min, production_stockee_max),
            'reprises_de_provision': (reprises_de_provision_min, reprises_de_provision_max),
            'transferts_charges': (transferts_charges_min, transferts_charges_max),
            'autres_produits': (autres_produits_min, autres_produits_max),
            'achat_mdses': (achat_mdses_min, achat_mdses_max),
            'variation_stock_mdses': (variation_stock_mdses_min, variation_stock_mdses_max),
            'achat_mp_autres_appro': (achat_mp_autres_appro_min, achat_mp_autres_appro_max),
            'var_stk_mp_app': (var_stk_mp_app_min, var_stk_mp_app_max),
            'autres_achats': (autres_achats_min, autres_achats_max),
            'variation_de_stocks_autres_appro': (variation_de_stocks_autres_appro_min, variation_de_stocks_autres_appro_max),
            'transports': (transports_min, transports_max),
            'services_ext': (services_ext_min, services_ext_max),
            'impots_taxes': (impots_taxes_min, impots_taxes_max),
            'autres_charges_valeur_ajoutee': (autres_charges_valeur_ajoutee_min, autres_charges_valeur_ajoutee_max),
            'charges_personnel': (charges_personnel_min, charges_personnel_max),
            'dotation_aux_amorts': (dotation_aux_amorts_min, dotation_aux_amorts_max),
            'dotation_aux_provisions': (dotation_aux_provisions_min, dotation_aux_provisions_max),
            'autres_charges_excedent_brute': (autres_charges_excedent_brute_min, autres_charges_excedent_brute_max),
            'revenus_fin_assimiles': (revenus_fin_assimiles_min, revenus_fin_assimiles_max),
            'prof_vmp_et_cre_actif_immo': (prof_vmp_et_cre_actif_immo_min, prof_vmp_et_cre_actif_immo_max),
            'interets_produit_assim': (interets_produit_assim_min, interets_produit_assim_max),
            'reprise_prov_et_transfert': (reprise_prov_et_transfert_min, reprise_prov_et_transfert_max),
            'diff_positive_de_change': (diff_positive_de_change_min, diff_positive_de_change_max),
            'prod_nets_cessions_vmp': (prod_nets_cessions_vmp_min, prod_nets_cessions_vmp_max),
            'dap': (dap_min, dap_max),
            'frais_fin_charges_assi': (frais_fin_charges_assi_min, frais_fin_charges_assi_max),
            'diff_negatives_de_change': (diff_negatives_de_change_min, diff_negatives_de_change_max),
            'ch_nettes_cessions_vmp': (ch_nettes_cessions_vmp_min, ch_nettes_cessions_vmp_max),
            'sur_op_gestion_prod_except': (sur_op_gestion_prod_except_min, sur_op_gestion_prod_except_max),
            'sur_op_en_capital_prod_except': (sur_op_en_capital_prod_except_min, sur_op_en_capital_prod_except_max),
            'reprise_prov_transfert': (reprise_prov_transfert_min, reprise_prov_transfert_max),
            'sur_op_gestion_charg_except': (sur_op_gestion_charg_except_min, sur_op_gestion_charg_except_max),
            'sur_op_en_capital_charg_except': (sur_op_en_capital_charg_except_min, sur_op_en_capital_charg_except_max),
            'dap_et_transfert_charg_except': (dap_et_transfert_charg_except_min, dap_et_transfert_charg_except_max),
            'participation_salairies': (participation_salairies_min, participation_salairies_max),
            'impot_sur_benefices': (impot_sur_benefices_min, impot_sur_benefices_max),
        }

        range_values = {}
        for field_name, (min_val, max_val) in range_filters.items():
            try:
                range_values[f'{field_name}_min'] = Decimal(min_val) if min_val else None
                range_values[f'{field_name}_max'] = Decimal(max_val) if max_val else None
            except InvalidOperation:
                return Response(
                    {f"error": f"Les valeurs de {field_name}_min et {field_name}_max doivent être des nombres décimaux valides."},
                    status=400,
                )

        # Start with filtering by acheteur_id
        resultat_list = ResultatC.objects.filter(acheteur_id=acheteur_id)
        
        # Apply year filter if provided
        if annee:
            resultat_list = resultat_list.filter(annee__annee__icontains=annee)
        
        # Apply search filter if provided
        if search_term:
            resultat_list = resultat_list.filter(
                Q(vente_de_mdses__icontains=search_term) |
                Q(ventes_de_produits_fabriques__icontains=search_term) |
                Q(travaux_services_vendus__icontains=search_term) |
                Q(produit_accessoires__icontains=search_term) |
                Q(production_imblise__icontains=search_term) |
                Q(subventions_exploitations__icontains=search_term) |
                Q(production_stockee__icontains=search_term) |
                Q(reprises_de_provision__icontains=search_term) |
                Q(transferts_charges__icontains=search_term) |
                Q(autres_produits__icontains=search_term) |
                Q(achat_mdses__icontains=search_term) |
                Q(variation_stock_mdses__icontains=search_term) |
                Q(achat_mp_autres_appro__icontains=search_term) |
                Q(var_stk_mp_app__icontains=search_term) |
                Q(autres_achats__icontains=search_term) |
                Q(variation_de_stocks_autres_appro__icontains=search_term) |
                Q(transports__icontains=search_term) |
                Q(services_ext__icontains=search_term) |
                Q(impots_taxes__icontains=search_term) |
                Q(autres_charges_valeur_ajoutee__icontains=search_term) |
                Q(charges_personnel__icontains=search_term) |
                Q(dotation_aux_amorts__icontains=search_term) |
                Q(dotation_aux_provisions__icontains=search_term) |
                Q(autres_charges_excedent_brute__icontains=search_term) |
                Q(revenus_fin_assimiles__icontains=search_term) |
                Q(prof_vmp_et_cre_actif_immo__icontains=search_term) |
                Q(interets_produit_assim__icontains=search_term) |
                Q(reprise_prov_et_transfert__icontains=search_term) |
                Q(diff_positive_de_change__icontains=search_term) |
                Q(prod_nets_cessions_vmp__icontains=search_term) |
                Q(dap__icontains=search_term) |
                Q(frais_fin_charges_assi__icontains=search_term) |
                Q(diff_negatives_de_change__icontains=search_term) |
                Q(ch_nettes_cessions_vmp__icontains=search_term) |
                Q(sur_op_gestion_prod_except__icontains=search_term) |
                Q(sur_op_en_capital_prod_except__icontains=search_term) |
                Q(reprise_prov_transfert__icontains=search_term) |
                Q(sur_op_gestion_charg_except__icontains=search_term) |
                Q(sur_op_en_capital_charg_except__icontains=search_term) |
                Q(dap_et_transfert_charg_except__icontains=search_term) |
                Q(participation_salairies__icontains=search_term) |
                Q(impot_sur_benefices__icontains=search_term)
            )
        
        # Apply numeric range filters
        for field_name, (min_val, max_val) in range_filters.items():
            min_key = f'{field_name}_min'
            max_key = f'{field_name}_max'
            
            if range_values[min_key] is not None:
                resultat_list = resultat_list.filter(**{f"{field_name}__gte": range_values[min_key]})
            if range_values[max_key] is not None:
                resultat_list = resultat_list.filter(**{f"{field_name}__lte": range_values[max_key]})

        # Order by most recent first
        resultat_list = resultat_list.order_by("-created_at")

        # Paginate results
        paginator = Paginator(resultat_list, 10)
        
        try:
            resultat_page = paginator.get_page(page_number)
        except Exception:
            return Response(
                {"error": "Numéro de page invalide."},
                status=400,
            )
        
        serializer = ResultatCSerializer(resultat_page, many=True)

        # Calculate start and end indices for pagination info
        start_index = (resultat_page.number - 1) * paginator.per_page + 1 if resultat_page else 0
        end_index = min(resultat_page.number * paginator.per_page, paginator.count) if resultat_page else 0

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": resultat_page.has_next(),
                "previous": resultat_page.has_previous(),
                "start_index": start_index,
                "end_index": end_index,
            }
        )


class SearchAcheteurResultatClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):  # Add acheteur_id parameter
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filter by acheteur_id first, then by search term
        resultat_list = ResultatC.objects.filter(acheteur_id=acheteur_id).filter(
            Q(vente_de_mdses__icontains=search_term) |
            Q(ventes_de_produits_fabriques__icontains=search_term) |
            Q(travaux_services_vendus__icontains=search_term) |
            Q(produit_accessoires__icontains=search_term) |
            Q(production_imblise__icontains=search_term) |
            Q(subventions_exploitations__icontains=search_term) |
            Q(production_stockee__icontains=search_term) |
            Q(reprises_de_provision__icontains=search_term) |
            Q(transferts_charges__icontains=search_term) |
            Q(autres_produits__icontains=search_term) |
            Q(achat_mdses__icontains=search_term) |
            Q(variation_stock_mdses__icontains=search_term) |
            Q(achat_mp_autres_appro__icontains=search_term) |
            Q(var_stk_mp_app__icontains=search_term) |
            Q(autres_achats__icontains=search_term) |
            Q(variation_de_stocks_autres_appro__icontains=search_term) |
            Q(transports__icontains=search_term) |
            Q(services_ext__icontains=search_term) |
            Q(impots_taxes__icontains=search_term) |
            Q(autres_charges_valeur_ajoutee__icontains=search_term) |
            Q(charges_personnel__icontains=search_term) |
            Q(dotation_aux_amorts__icontains=search_term) |
            Q(dotation_aux_provisions__icontains=search_term) |
            Q(autres_charges_excedent_brute__icontains=search_term) |
            Q(revenus_fin_assimiles__icontains=search_term) |
            Q(prof_vmp_et_cre_actif_immo__icontains=search_term) |
            Q(interets_produit_assim__icontains=search_term) |
            Q(reprise_prov_et_transfert__icontains=search_term) |
            Q(diff_positive_de_change__icontains=search_term) |
            Q(prod_nets_cessions_vmp__icontains=search_term) |
            Q(dap__icontains=search_term) |
            Q(frais_fin_charges_assi__icontains=search_term) |
            Q(diff_negatives_de_change__icontains=search_term) |
            Q(ch_nettes_cessions_vmp__icontains=search_term) |
            Q(sur_op_gestion_prod_except__icontains=search_term) |
            Q(sur_op_en_capital_prod_except__icontains=search_term) |
            Q(reprise_prov_transfert__icontains=search_term) |
            Q(sur_op_gestion_charg_except__icontains=search_term) |
            Q(sur_op_en_capital_charg_except__icontains=search_term) |
            Q(dap_et_transfert_charg_except__icontains=search_term) |
            Q(participation_salairies__icontains=search_term) |
            Q(impot_sur_benefices__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(resultat_list, 10)
        page_number = request.query_params.get("page", 1)
        
        try:
            resultat_page = paginator.get_page(page_number)
        except Exception:
            return Response(
                {"error": "Numéro de page invalide."},
                status=400,
            )
            
        serializer = ResultatCSerializer(resultat_page, many=True)

        start_index = (resultat_page.number - 1) * paginator.per_page + 1 if resultat_page else 0
        end_index = min(resultat_page.number * paginator.per_page, paginator.count) if resultat_page else 0

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": resultat_page.has_next(),
                "previous": resultat_page.has_previous(),
                "start_index": start_index,
                "end_index": end_index,
            }
        )


class AddAcheteurResultatClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id
        serializer = AddResultatCSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurResultatClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, resultat_id, *args, **kwargs):  # Add acheteur_id parameter
        # Verify the result belongs to the specified acheteur
        resultat = ResultatC.objects.filter(id=resultat_id, acheteur_id=acheteur_id).first()
        if not resultat:
            return Response(
                {"detail": "Résultat non trouvé pour cet acheteur."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetResultatCSerializer(resultat)
        return Response(serializer.data)

    def put(self, request, acheteur_id, resultat_id, *args, **kwargs):  # Add acheteur_id parameter
        # Verify the result belongs to the specified acheteur
        resultat = ResultatC.objects.filter(id=resultat_id, acheteur_id=acheteur_id).first()
        if not resultat:
            return Response(
                {"detail": "Résultat non trouvé pour cet acheteur."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditResultatCSerializer(resultat, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurResultatClassiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):  # Add acheteur_id parameter
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the results belong to the specified acheteur
        resultats = ResultatC.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not resultats.exists():
            return Response(
                {"error": "Aucun résultat trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = resultats.delete()
        return Response(
            {"message": f"{count} résultats supprimés avec succès."},
            status=status.HTTP_200_OK,
        )





class ListAcheteurActifSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        frais_developpement_prospection_min = request.query_params.get(
            "frais_developpement_prospection_min", ""
        )
        frais_developpement_prospection_max = request.query_params.get(
            "frais_developpement_prospection_max", ""
        )

        try:
            frais_developpement_prospection_min = (
                Decimal(frais_developpement_prospection_min)
                if frais_developpement_prospection_min
                else None
            )
            frais_developpement_prospection_max = (
                Decimal(frais_developpement_prospection_max)
                if frais_developpement_prospection_max
                else None
            )
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de frais_developpement_prospection_min et frais_developpement_prospection_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        actif_list = ActifS.objects.filter(acheteur_id=acheteur_id).order_by("-created_at")
        if annee:
            actif_list = actif_list.filter(annee__annee__icontains=annee)

        if frais_developpement_prospection_min is not None:
            actif_list = actif_list.filter(
                frais_developpement_prospection__gte=frais_developpement_prospection_min
            )

        if frais_developpement_prospection_max is not None:
            actif_list = actif_list.filter(
                frais_developpement_prospection__lte=frais_developpement_prospection_max
            )

        paginator = Paginator(actif_list, 10)
        actif_page = paginator.get_page(page_number)
        serializer = ActifSysCohadaSerializer(actif_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": actif_page.has_next(),
                "previous": actif_page.has_previous(),
            }
        )


class SearchAcheteurActifSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        actif_list = ActifS.objects.filter(
            acheteur_id=acheteur_id
        ).filter(
            Q(annee__annee__icontains=search_term)
            | Q(type_bilan__icontains=search_term)
            | Q(semestre__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(actif_list, 10)
        page_number = request.query_params.get("page", 1)
        actif_page = paginator.get_page(page_number)
        serializer = ActifSysCohadaSerializer(actif_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": actif_page.has_next(),
                "previous": actif_page.has_previous(),
            }
        )


class AddAcheteurActifSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        serializer = AddActifSysCohadaSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurActifSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, actif_id, *args, **kwargs):
        actif = ActifS.objects.filter(id=actif_id, acheteur_id=acheteur_id).first()
        if not actif:
            return Response(
                {"detail": "Actif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetActifSysCohadaSerializer(actif)
        return Response(serializer.data)

    def put(self, request, acheteur_id, actif_id, *args, **kwargs):
        actif = ActifS.objects.filter(id=actif_id, acheteur_id=acheteur_id).first()
        if not actif:
            return Response(
                {"detail": "Actif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditActifSysCohadaSerializer(
            actif, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurActifSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        actifs = ActifS.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not actifs.exists():
            return Response(
                {"error": "Aucun actif trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = actifs.delete()
        return Response(
            {"message": f"{count} actifs supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class ListAcheteurPassifSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        capital_min = request.query_params.get("capital_min", "")
        capital_max = request.query_params.get("capital_max", "")

        try:
            capital_min = Decimal(capital_min) if capital_min else None
            capital_max = Decimal(capital_max) if capital_max else None
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de capital_min et capital_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        passif_list = PassifS.objects.filter(acheteur_id=acheteur_id).order_by("-created_at")
        if annee:
            passif_list = passif_list.filter(annee__annee__icontains=annee)

        if capital_min is not None:
            passif_list = passif_list.filter(capital__gte=capital_min)

        if capital_max is not None:
            passif_list = passif_list.filter(capital__lte=capital_max)

        paginator = Paginator(passif_list, 10)
        passif_page = paginator.get_page(page_number)
        serializer = PassifSysSCohadaSerializer(passif_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": passif_page.has_next(),
                "previous": passif_page.has_previous(),
            }
        )


class SearchAcheteurPassifSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        passif_list = PassifS.objects.filter(
            acheteur_id=acheteur_id
        ).filter(
            Q(annee__annee__icontains=search_term)
            | Q(type_bilan__icontains=search_term)
            | Q(semestre__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(passif_list, 10)
        page_number = request.query_params.get("page", 1)
        passif_page = paginator.get_page(page_number)
        serializer = PassifSysSCohadaSerializer(passif_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": passif_page.has_next(),
                "previous": passif_page.has_previous(),
            }
        )


class AddAcheteurPassifSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        serializer = AddPassifSysCohadaSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurPassifSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, passif_id, *args, **kwargs):
        passif = PassifS.objects.filter(id=passif_id, acheteur_id=acheteur_id).first()
        if not passif:
            return Response(
                {"detail": "Passif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetPassifSysCohadaSerializer(passif)
        return Response(serializer.data)

    def put(self, request, acheteur_id, passif_id, *args, **kwargs):
        passif = PassifS.objects.filter(id=passif_id, acheteur_id=acheteur_id).first()
        if not passif:
            return Response(
                {"detail": "Passif non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditPassifSysCohadaSerializer(
            passif, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurPassifSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        passifs = PassifS.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not passifs.exists():
            return Response(
                {"error": "Aucun passif trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = passifs.delete()
        return Response(
            {"message": f"{count} passifs supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class ListAcheteurResultatSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        ventes_marchandises_a_min = request.query_params.get(
            "ventes_marchandises_a_min", ""
        )
        ventes_marchandises_a_max = request.query_params.get(
            "ventes_marchandises_a_max", ""
        )

        try:
            ventes_marchandises_a_min = (
                Decimal(ventes_marchandises_a_min)
                if ventes_marchandises_a_min
                else None
            )
            ventes_marchandises_a_max = (
                Decimal(ventes_marchandises_a_max)
                if ventes_marchandises_a_max
                else None
            )
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de ventes_marchandises_a_min et ventes_marchandises_a_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        resultat_list = ResultatS.objects.filter(acheteur_id=acheteur_id).order_by("-created_at")
        if annee:
            resultat_list = resultat_list.filter(annee__annee__icontains=annee)

        if ventes_marchandises_a_min is not None:
            resultat_list = resultat_list.filter(
                ventes_marchandises_a__gte=ventes_marchandises_a_min
            )

        if ventes_marchandises_a_max is not None:
            resultat_list = resultat_list.filter(
                ventes_marchandises_a__lte=ventes_marchandises_a_max
            )

        paginator = Paginator(resultat_list, 10)
        resultat_page = paginator.get_page(page_number)
        serializer = ResultatSysCohadaSerializer(resultat_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": resultat_page.has_next(),
                "previous": resultat_page.has_previous(),
            }
        )


class SearchAcheteurResultatSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resultat_list = ResultatS.objects.filter(
            acheteur_id=acheteur_id
        ).filter(
            Q(annee__annee__icontains=search_term)
            | Q(type_bilan__icontains=search_term)
            | Q(semestre__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(resultat_list, 10)
        page_number = request.query_params.get("page", 1)
        resultat_page = paginator.get_page(page_number)
        serializer = ResultatSysCohadaSerializer(resultat_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": resultat_page.has_next(),
                "previous": resultat_page.has_previous(),
            }
        )


class AddAcheteurResultatSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        serializer = AddResultatSysCohadaSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurResultatSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, resultat_id, *args, **kwargs):
        resultat = ResultatS.objects.filter(id=resultat_id, acheteur_id=acheteur_id).first()
        if not resultat:
            return Response(
                {"detail": "Résultat non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetResultatSysCohadaSerializer(resultat)
        return Response(serializer.data)

    def put(self, request, acheteur_id, resultat_id, *args, **kwargs):
        resultat = ResultatS.objects.filter(id=resultat_id, acheteur_id=acheteur_id).first()
        if not resultat:
            return Response(
                {"detail": "Résultat non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditResultatSysCohadaSerializer(
            resultat, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurResultatSysCohadaView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resultats = ResultatS.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not resultats.exists():
            return Response(
                {"error": "Aucun résultat trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = resultats.delete()
        return Response(
            {"message": f"{count} résultats supprimés avec succès."},
            status=status.HTTP_200_OK,
        )






class ListAcheteurAssetsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        logger.info(f"GET ListAcheteurAssetsView - Acheteur ID: {acheteur_id}")
        logger.info(f"Paramètres de requête: page={request.query_params.get('page')}, search={request.query_params.get('search')}")
        
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        caisse_min = request.query_params.get("caisse_min", "")
        caisse_max = request.query_params.get("caisse_max", "")

        try:
            caisse_min = Decimal(caisse_min) if caisse_min else None
            caisse_max = Decimal(caisse_max) if caisse_max else None
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de caisse_min et caisse_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        # Filtrer par acheteur spécifique
        assets_list = Assets.objects.filter(acheteur_id=acheteur_id)
        logger.info(f"Nombre d'assets pour acheteur {acheteur_id}: {assets_list.count()}")
        
        # Log des premiers assets
        for asset in assets_list[:5]:
            logger.info(f"Asset ID: {asset.id}, Année: {asset.annee}, Caisse: {asset.caisse}")
        
        # Filtres supplémentaires
        if annee:
            assets_list = assets_list.filter(annee__annee__icontains=annee)
            logger.info(f"Filtré par année '{annee}': {assets_list.count()} résultats")
        
        if caisse_min is not None:
            assets_list = assets_list.filter(caisse__gte=caisse_min)

        if caisse_max is not None:
            assets_list = assets_list.filter(caisse__lte=caisse_max)

        # Si un terme de recherche est fourni, chercher dans les champs pertinents
        if search_term:
            assets_list = assets_list.filter(
                Q(annee__annee__icontains=search_term) |
                Q(acheteur__nom__icontains=search_term)
            )
            logger.info(f"Recherche '{search_term}': {assets_list.count()} résultats")

        assets_list = assets_list.order_by("-created_at")

        paginator = Paginator(assets_list, 10)
        assets_page = paginator.get_page(page_number)
        serializer = AssetsSerializer(assets_page, many=True)
        
        logger.info(f"Données sérialisées pour la page {page_number}: {len(serializer.data)} éléments")
        if serializer.data:
            logger.info(f"Premier élément sérialisé: {serializer.data[0]}")

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": assets_page.has_next(),
                "previous": assets_page.has_previous(),
                "start_index": assets_page.start_index(),
                "end_index": assets_page.end_index(),
            }
        )


class SearchAcheteurAssetsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assets_list = Assets.objects.filter(
            # Ajoutez les champs de recherche ici
        ).order_by("-created_at")

        paginator = Paginator(assets_list, 10)
        page_number = request.query_params.get("page", 1)
        assets_page = paginator.get_page(page_number)
        serializer = AssetsSerializer(assets_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": assets_page.has_next(),
                "previous": assets_page.has_previous(),
            }
        )


class AddAcheteurAssetsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        logger.info(f"POST AddAcheteurAssetsView - Acheteur ID: {acheteur_id}")
        logger.info(f"Données reçues: {request.data}")
        
        # Vérifier si l'acheteur existe
        try:
            acheteur = Acheteur.objects.get(id=acheteur_id)
        except Acheteur.DoesNotExist:
            return Response(
                {"detail": "Acheteur non trouvé."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Ajouter l'acheteur aux données
        data = request.data.copy()
        data['acheteur'] = acheteur_id
        logger.info(f"Données avec acheteur: {data}")
        
        # Passez le contexte avec la requête
        serializer = AddAssetsSerializer(
            data=data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            logger.info("Serializer valide, création de l'asset...")
            serializer.save()
            logger.info(f"Asset créé avec ID: {serializer.instance.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            logger.error(f"Erreurs de validation: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurAssetsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, asset_id, *args, **kwargs):
        logger.info(f"GET EditAcheteurAssetsView - Acheteur ID: {acheteur_id}, Asset ID: {asset_id}")
        logger.info(f"Requête utilisateur: {request.user}")
        
        try:
            asset = Assets.objects.get(id=asset_id, acheteur_id=acheteur_id)
            logger.info(f"Asset trouvé: {asset.id}, Annee: {asset.annee}, Acheteur: {asset.acheteur_id}")
            logger.info(f"Valeurs de l'asset: caisse={asset.caisse}, banques_centrales={asset.banques_centrales}")
        except Assets.DoesNotExist:
            logger.error(f"Asset non trouvé avec ID: {asset_id} pour acheteur: {acheteur_id}")
            return Response(
                {"detail": "Asset non trouvé."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AssetsSerializer(asset)
        logger.info(f"Données sérialisées: {serializer.data}")
        return Response(serializer.data)

    def put(self, request, acheteur_id, asset_id, *args, **kwargs):
        logger.info(f"PUT EditAcheteurAssetsView - Acheteur ID: {acheteur_id}, Asset ID: {asset_id}")
        logger.info(f"Données reçues: {request.data}")
        
        try:
            asset = Assets.objects.get(id=asset_id, acheteur_id=acheteur_id)
        except Assets.DoesNotExist:
            return Response(
                {"detail": "Asset non trouvé."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditAssetsSerializer(
            asset, 
            data=request.data, 
            context={'request': request}, 
            partial=True
        )
        
        if serializer.is_valid():
            logger.info("Serializer valide, sauvegarde...")
            serializer.save()
            logger.info(f"Données sauvegardées: {serializer.data}")
            return Response(serializer.data)
        else:
            logger.error(f"Erreurs de validation: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class DeleteAcheteurAssetsView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assets = Assets.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not assets.exists():
            return Response(
                {"error": "Aucun asset trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = assets.delete()
        return Response(
            {"message": f"{count} assets supprimés avec succès."},
            status=status.HTTP_200_OK,
        )







class ListAcheteurLiabilitiesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        tresorerie_ccp_min = request.query_params.get("tresorerie_ccp_min", "")
        tresorerie_ccp_max = request.query_params.get("tresorerie_ccp_max", "")

        try:
            tresorerie_ccp_min = (
                Decimal(tresorerie_ccp_min) if tresorerie_ccp_min else None
            )
            tresorerie_ccp_max = (
                Decimal(tresorerie_ccp_max) if tresorerie_ccp_max else None
            )
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de tresorerie_ccp_min et tresorerie_ccp_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        liabilities_list = Liabilities.objects.filter(
            acheteur_id=acheteur_id
        ).order_by("-created_at")

        if annee:
            liabilities_list = liabilities_list.filter(annee__annee__icontains=annee)

        if tresorerie_ccp_min is not None:
            liabilities_list = liabilities_list.filter(
                tresorerie_ccp__gte=tresorerie_ccp_min
            )

        if tresorerie_ccp_max is not None:
            liabilities_list = liabilities_list.filter(
                tresorerie_ccp__lte=tresorerie_ccp_max
            )

        paginator = Paginator(liabilities_list, 10)
        liabilities_page = paginator.get_page(page_number)
        serializer = LiabilitiesSerializer(liabilities_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": liabilities_page.has_next(),
                "previous": liabilities_page.has_previous(),
            }
        )


class SearchAcheteurLiabilitiesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        liabilities_list = Liabilities.objects.filter(
            acheteur_id=acheteur_id
        ).filter(
            Q(annee__annee__icontains=search_term)
            | Q(acheteur__nom__icontains=search_term)
            | Q(type_bilan__icontains=search_term)
            | Q(semestre__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(liabilities_list, 10)
        page_number = request.query_params.get("page", 1)
        liabilities_page = paginator.get_page(page_number)
        serializer = LiabilitiesSerializer(liabilities_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": liabilities_page.has_next(),
                "previous": liabilities_page.has_previous(),
            }
        )


class AddAcheteurLiabilitiesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        serializer = AddLiabilitiesSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurLiabilitiesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, liability_id, *args, **kwargs):
        liability = Liabilities.objects.filter(
            id=liability_id, acheteur_id=acheteur_id
        ).first()
        if not liability:
            return Response(
                {"detail": "Liability non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetLiabilitiesSerializer(liability)
        return Response(serializer.data)

    def put(self, request, acheteur_id, liability_id, *args, **kwargs):
        liability = Liabilities.objects.filter(
            id=liability_id, acheteur_id=acheteur_id
        ).first()
        if not liability:
            return Response(
                {"detail": "Liability non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditLiabilitiesSerializer(
            liability, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurLiabilitiesView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        liabilities = Liabilities.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not liabilities.exists():
            return Response(
                {"error": "Aucune liability trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = liabilities.delete()
        return Response(
            {"message": f"{count} liabilities supprimées avec succès."},
            status=status.HTTP_200_OK,
        )










class SearchAcheteurOffBalanceSheetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        off_balance_sheet_list = OffBalanceSheet.objects.filter(
            # Ajoutez les champs de recherche ici
        ).order_by("-created_at")

        paginator = Paginator(off_balance_sheet_list, 10)
        page_number = request.query_params.get("page", 1)
        off_balance_sheet_page = paginator.get_page(page_number)
        serializer = OffBalanceSheetSerializer(off_balance_sheet_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": off_balance_sheet_page.has_next(),
                "previous": off_balance_sheet_page.has_previous(),
            }
        )


class ListAcheteurOffBalanceSheetView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self, acheteur_id, search_term=""):
        """Retourne le queryset filtré et optimisé"""
        queryset = OffBalanceSheet.objects.filter(
            acheteur_id=acheteur_id
        ).select_related('annee', 'created_by', 'updated_by')
        
        if search_term:
            queryset = queryset.filter(
                Q(annee__annee__icontains=search_term) |
                Q(type_bilan__icontains=search_term) |
                Q(semestre__icontains=search_term)
            )
        
        return queryset.order_by("-created_at")

    def get(self, request, acheteur_id, *args, **kwargs):
        try:
            page_number = int(request.query_params.get("page", 1))
            search_term = request.query_params.get("search", "").strip()
            items_per_page = int(request.query_params.get("per_page", 10))
            
            # Récupérer le queryset
            queryset = self.get_queryset(acheteur_id, search_term)
            
            # Pagination
            paginator = Paginator(queryset, items_per_page)
            
            try:
                off_balance_sheet_page = paginator.page(page_number)
            except EmptyPage:
                return Response({
                    "results": [],
                    "count": 0,
                    "total_pages": 0,
                    "next": False,
                    "previous": False,
                    "current_page": page_number,
                    "global_totals": {
                        "total_engagements_donnes": 0,
                        "total_engagements_recus": 0,
                        "total_general": 0,
                        "total_count": 0
                    },
                    "per_page": items_per_page
                })
            
            # Sérialiser les données
            serializer = OffBalanceSheetSerializer(off_balance_sheet_page, many=True)
            
            # Calculer les totaux manuellement (car ce sont des propriétés)
            total_engagements_donnes = 0
            total_engagements_recus = 0
            total_general = 0
            
            for item in off_balance_sheet_page:
                total_engagements_donnes += float(item.total_engagements_donnes or 0)
                total_engagements_recus += float(item.total_engagements_recus or 0)
                total_general += float(item.total_general or 0)
            
            global_totals = {
                "total_engagements_donnes": total_engagements_donnes,
                "total_engagements_recus": total_engagements_recus,
                "total_general": total_general,
                "total_count": paginator.count
            }
            
            return Response({
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": off_balance_sheet_page.has_next(),
                "previous": off_balance_sheet_page.has_previous(),
                "current_page": off_balance_sheet_page.number,
                "global_totals": global_totals,
                "per_page": items_per_page
            })
            
        except ValueError as e:
            return Response(
                {"error": "Paramètres de pagination invalides."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Erreur lors du chargement des données: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AddAcheteurOffBalanceSheetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        try:
            # Vérifier qu'un hors bilan n'existe pas déjà pour cette année/semestre
            annee_id = request.data.get('annee')
            semestre = request.data.get('semestre')
            type_bilan = request.data.get('type_bilan', 'annuel')
            
            if annee_id:
                existing = OffBalanceSheet.objects.filter(
                    acheteur_id=acheteur_id,
                    annee_id=annee_id,
                    semestre=semestre if type_bilan == 'semestriel' else None
                ).exists()
                
                if existing:
                    return Response(
                        {"error": "Un hors bilan existe déjà pour cette période."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Ajouter l'acheteur_id aux données
            data = request.data.copy()
            data['acheteur'] = acheteur_id
            
            serializer = AddOffBalanceSheetSerializer(
                data=data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response(
                    OffBalanceSheetSerializer(serializer.instance).data,
                    status=status.HTTP_201_CREATED
                )
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de l'ajout: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EditAcheteurOffBalanceSheetView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, acheteur_id, off_balance_sheet_id):
        """Récupère l'objet avec vérification de l'acheteur"""
        try:
            return OffBalanceSheet.objects.get(
                id=off_balance_sheet_id,
                acheteur_id=acheteur_id
            )
        except OffBalanceSheet.DoesNotExist:
            return None

    def get(self, request, acheteur_id, off_balance_sheet_id, *args, **kwargs):
        off_balance_sheet = self.get_object(acheteur_id, off_balance_sheet_id)
        
        if not off_balance_sheet:
            return Response(
                {"detail": "OffBalanceSheet non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = OffBalanceSheetSerializer(off_balance_sheet)
        return Response(serializer.data)

    def put(self, request, acheteur_id, off_balance_sheet_id, *args, **kwargs):
        off_balance_sheet = self.get_object(acheteur_id, off_balance_sheet_id)
        
        if not off_balance_sheet:
            return Response(
                {"detail": "OffBalanceSheet non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditOffBalanceSheetSerializer(
            off_balance_sheet,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            # Retourner les données complètes après mise à jour
            updated_serializer = OffBalanceSheetSerializer(serializer.instance)
            return Response(updated_serializer.data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurOffBalanceSheetView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        try:
            ids = request.data.get("ids", [])
            if not ids or not isinstance(ids, list):
                return Response(
                    {"error": "Une liste d'IDs est requise."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Vérifier que tous les IDs appartiennent à l'acheteur
            off_balance_sheets = OffBalanceSheet.objects.filter(
                id__in=ids,
                acheteur_id=acheteur_id
            )
            
            deleted_count = off_balance_sheets.count()
            
            if deleted_count == 0:
                return Response(
                    {"error": "Aucun off_balance_sheet trouvé pour les IDs fournis."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Supprimer les objets
            off_balance_sheets.delete()
            
            return Response(
                {
                    "message": f"{deleted_count} off_balance_sheets supprimés avec succès.",
                    "deleted_count": deleted_count
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la suppression: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OffBalanceSheetStatsView(APIView):
    """Vue pour les statistiques des hors bilans"""
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        try:
            # Récupérer tous les hors bilans de l'acheteur
            off_balance_sheets = OffBalanceSheet.objects.filter(
                acheteur_id=acheteur_id
            )
            
            # Initialiser les statistiques
            stats = {
                "total_count": off_balance_sheets.count(),
                "total_engagements_donnes_sum": 0,
                "total_engagements_recus_sum": 0,
                "avg_engagements_donnes": 0,
                "avg_engagements_recus": 0,
                "max_engagements_donnes": 0,
                "max_engagements_recus": 0,
                "min_engagements_donnes": 0,
                "min_engagements_recus": 0,
            }
            
            # Calculer manuellement car ce sont des propriétés
            engagements_donnes_list = []
            engagements_recus_list = []
            
            for item in off_balance_sheets:
                engagements_donnes = float(item.total_engagements_donnes or 0)
                engagements_recus = float(item.total_engagements_recus or 0)
                
                stats["total_engagements_donnes_sum"] += engagements_donnes
                stats["total_engagements_recus_sum"] += engagements_recus
                
                engagements_donnes_list.append(engagements_donnes)
                engagements_recus_list.append(engagements_recus)
            
            # Calculer les autres statistiques si on a des données
            if engagements_donnes_list:
                stats["avg_engagements_donnes"] = stats["total_engagements_donnes_sum"] / len(engagements_donnes_list)
                stats["max_engagements_donnes"] = max(engagements_donnes_list)
                stats["min_engagements_donnes"] = min(engagements_donnes_list)
            
            if engagements_recus_list:
                stats["avg_engagements_recus"] = stats["total_engagements_recus_sum"] / len(engagements_recus_list)
                stats["max_engagements_recus"] = max(engagements_recus_list)
                stats["min_engagements_recus"] = min(engagements_recus_list)
            
            # Ajouter le total général
            stats['total_general_sum'] = (
                stats['total_engagements_donnes_sum'] + 
                stats['total_engagements_recus_sum']
            )
            
            # Calculer les pourcentages
            total_general = stats['total_general_sum']
            if total_general > 0:
                stats['percentage_engagements_donnes'] = round(
                    (stats['total_engagements_donnes_sum'] / total_general) * 100, 2
                )
                stats['percentage_engagements_recus'] = round(
                    (stats['total_engagements_recus_sum'] / total_general) * 100, 2
                )
            else:
                stats['percentage_engagements_donnes'] = 0
                stats['percentage_engagements_recus'] = 0
            
            # Formater les nombres
            for key in stats:
                if isinstance(stats[key], float):
                    stats[key] = round(stats[key], 2)
            
            return Response(stats)
            
        except Exception as e:
            return Response(
                {"error": f"Erreur lors du calcul des statistiques: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )






class ListAcheteurExpensesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        interet_charges_assimilee_dette_interbancaire_min = request.query_params.get(
            "interet_charges_assimilee_dette_interbancaire_min", ""
        )
        interet_charges_assimilee_dette_interbancaire_max = request.query_params.get(
            "interet_charges_assimilee_dette_interbancaire_max", ""
        )

        try:
            interet_charges_assimilee_dette_interbancaire_min = (
                Decimal(interet_charges_assimilee_dette_interbancaire_min)
                if interet_charges_assimilee_dette_interbancaire_min
                else None
            )
            interet_charges_assimilee_dette_interbancaire_max = (
                Decimal(interet_charges_assimilee_dette_interbancaire_max)
                if interet_charges_assimilee_dette_interbancaire_max
                else None
            )
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de interet_charges_assimilee_dette_interbancaire_min et interet_charges_assimilee_dette_interbancaire_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        expenses_list = Expenses.objects.filter(acheteur_id=acheteur_id).order_by(
            "-created_at"
        )

        if annee:
            expenses_list = expenses_list.filter(annee__annee__icontains=annee)

        if interet_charges_assimilee_dette_interbancaire_min is not None:
            expenses_list = expenses_list.filter(
                interet_charges_assimilee_dette_interbancaire__gte=interet_charges_assimilee_dette_interbancaire_min
            )

        if interet_charges_assimilee_dette_interbancaire_max is not None:
            expenses_list = expenses_list.filter(
                interet_charges_assimilee_dette_interbancaire__lte=interet_charges_assimilee_dette_interbancaire_max
            )

        paginator = Paginator(expenses_list, 10)
        expenses_page = paginator.get_page(page_number)
        serializer = ExpensesSerializer(expenses_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": expenses_page.has_next(),
                "previous": expenses_page.has_previous(),
            }
        )


class SearchAcheteurExpensesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expenses_list = Expenses.objects.filter(
            acheteur_id=acheteur_id
        ).filter(
            Q(annee__annee__icontains=search_term)
            | Q(acheteur__nom__icontains=search_term)
            | Q(type_bilan__icontains=search_term)
            | Q(semestre__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(expenses_list, 10)
        page_number = request.query_params.get("page", 1)
        expenses_page = paginator.get_page(page_number)
        serializer = ExpensesSerializer(expenses_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": expenses_page.has_next(),
                "previous": expenses_page.has_previous(),
            }
        )


class AddAcheteurExpensesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        serializer = AddExpensesSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurExpensesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, expense_id, *args, **kwargs):
        expense = Expenses.objects.filter(id=expense_id, acheteur_id=acheteur_id).first()
        if not expense:
            return Response(
                {"detail": "Expense non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetExpensesSerializer(expense)
        return Response(serializer.data)

    def put(self, request, acheteur_id, expense_id, *args, **kwargs):
        expense = Expenses.objects.filter(id=expense_id, acheteur_id=acheteur_id).first()
        if not expense:
            return Response(
                {"detail": "Expense non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditExpensesSerializer(
            expense, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurExpensesView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expenses = Expenses.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not expenses.exists():
            return Response(
                {"error": "Aucune expense trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = expenses.delete()
        return Response(
            {"message": f"{count} expenses supprimées avec succès."},
            status=status.HTTP_200_OK,
        )


class ListAcheteurProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        interets_produit_assimile_sur_pret_avance_interbancaire_min = (
            request.query_params.get(
                "interets_produit_assimile_sur_pret_avance_interbancaire_min", ""
            )
        )
        interets_produit_assimile_sur_pret_avance_interbancaire_max = (
            request.query_params.get(
                "interets_produit_assimile_sur_pret_avance_interbancaire_max", ""
            )
        )

        try:
            interets_produit_assimile_sur_pret_avance_interbancaire_min = (
                Decimal(interets_produit_assimile_sur_pret_avance_interbancaire_min)
                if interets_produit_assimile_sur_pret_avance_interbancaire_min
                else None
            )
            interets_produit_assimile_sur_pret_avance_interbancaire_max = (
                Decimal(interets_produit_assimile_sur_pret_avance_interbancaire_max)
                if interets_produit_assimile_sur_pret_avance_interbancaire_max
                else None
            )
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de interets_produit_assimile_sur_pret_avance_interbancaire_min et interets_produit_assimile_sur_pret_avance_interbancaire_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        products_list = Products.objects.filter(acheteur_id=acheteur_id).order_by(
            "-created_at"
        )

        if annee:
            products_list = products_list.filter(annee__annee__icontains=annee)

        if interets_produit_assimile_sur_pret_avance_interbancaire_min is not None:
            products_list = products_list.filter(
                interets_produit_assimile_sur_pret_avance_interbancaire__gte=interets_produit_assimile_sur_pret_avance_interbancaire_min
            )

        if interets_produit_assimile_sur_pret_avance_interbancaire_max is not None:
            products_list = products_list.filter(
                interets_produit_assimile_sur_pret_avance_interbancaire__lte=interets_produit_assimile_sur_pret_avance_interbancaire_max
            )

        paginator = Paginator(products_list, 10)
        products_page = paginator.get_page(page_number)
        serializer = ProductsSerializer(products_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": products_page.has_next(),
                "previous": products_page.has_previous(),
            }
        )


class SearchAcheteurProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        products_list = Products.objects.filter(
            acheteur_id=acheteur_id
        ).filter(
            Q(annee__annee__icontains=search_term)
            | Q(acheteur__nom__icontains=search_term)
            | Q(type_bilan__icontains=search_term)
            | Q(semestre__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(products_list, 10)
        page_number = request.query_params.get("page", 1)
        products_page = paginator.get_page(page_number)
        serializer = ProductsSerializer(products_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": products_page.has_next(),
                "previous": products_page.has_previous(),
            }
        )


class AddAcheteurProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        serializer = AddProductsSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, product_id, *args, **kwargs):
        product = Products.objects.filter(id=product_id, acheteur_id=acheteur_id).first()
        if not product:
            return Response(
                {"detail": "Product non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetProductsSerializer(product)
        return Response(serializer.data)

    def put(self, request, acheteur_id, product_id, *args, **kwargs):
        product = Products.objects.filter(id=product_id, acheteur_id=acheteur_id).first()
        if not product:
            return Response(
                {"detail": "Product non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditProductsSerializer(
            product, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        products = Products.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not products.exists():
            return Response(
                {"error": "Aucun product trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = products.delete()
        return Response(
            {"message": f"{count} products supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class ListAcheteurCompteFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        type_compte = request.query_params.get("type_compte", "")
        sous_type = request.query_params.get("sous_type", "")

        comptes_list = CompteFinancierIrfs.objects.all().order_by("nom")

        if type_compte:
            comptes_list = comptes_list.filter(type_compte__icontains=type_compte)

        if sous_type:
            comptes_list = comptes_list.filter(sous_type__icontains=sous_type)

        paginator = Paginator(comptes_list, 10)
        comptes_page = paginator.get_page(page_number)
        serializer = CompteFinancierIrfsSerializer(comptes_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": comptes_page.has_next(),
                "previous": comptes_page.has_previous(),
            }
        )


class SearchAcheteurCompteFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        comptes_list = CompteFinancierIrfs.objects.filter(
            nom__icontains=search_term
        ).order_by("nom")

        paginator = Paginator(comptes_list, 10)
        page_number = request.query_params.get("page", 1)
        comptes_page = paginator.get_page(page_number)
        serializer = CompteFinancierIrfsSerializer(comptes_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": comptes_page.has_next(),
                "previous": comptes_page.has_previous(),
            }
        )


class AddAcheteurCompteFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddCompteFinancierIrfsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurCompteFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, compte_irfs_id, *args, **kwargs):
        compte = CompteFinancierIrfs.objects.filter(id=compte_irfs_id).first()
        if not compte:
            return Response(
                {"detail": "Compte non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetCompteFinancierIrfsSerializer(compte)
        return Response(serializer.data)

    def put(self, request, compte_irfs_id, *args, **kwargs):
        compte = CompteFinancierIrfs.objects.filter(id=compte_irfs_id).first()
        if not compte:
            return Response(
                {"detail": "Compte non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditCompteFinancierIrfsSerializer(
            compte, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurCompteFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        comptes = CompteFinancierIrfs.objects.filter(id__in=ids)
        if not comptes.exists():
            return Response(
                {"error": "Aucun compte trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = comptes.delete()
        return Response(
            {"message": f"{count} comptes supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class ListAcheteurValeurCompteFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        valeur_min = request.query_params.get("valeur_min", "")
        valeur_max = request.query_params.get("valeur_max", "")

        try:
            valeur_min = Decimal(valeur_min) if valeur_min else None
            valeur_max = Decimal(valeur_max) if valeur_max else None
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de valeur_min et valeur_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        valeurs_list = ValeurCompteIrfs.objects.filter(
            acheteur__pk=acheteur_id, annee__annee__icontains=annee
        ).order_by("compte__nom")

        if valeur_min is not None:
            valeurs_list = valeurs_list.filter(valeur__gte=valeur_min)

        if valeur_max is not None:
            valeurs_list = valeurs_list.filter(valeur__lte=valeur_max)

        paginator = Paginator(valeurs_list, 10)
        valeurs_page = paginator.get_page(page_number)
        serializer = ValeurCompteIrfsSerializer(valeurs_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": valeurs_page.has_next(),
                "previous": valeurs_page.has_previous(),
            }
        )


class ListAcheteurActifFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        valeur_min = request.query_params.get("valeur_min", "")
        valeur_max = request.query_params.get("valeur_max", "")

        try:
            valeur_min = Decimal(valeur_min) if valeur_min else None
            valeur_max = Decimal(valeur_max) if valeur_max else None
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de valeur_min et valeur_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        valeurs_list = ValeurCompteIrfs.objects.filter(
            acheteur__pk=acheteur_id,
            annee__annee__icontains=annee,
            compte__type_compte__icontains="Actif",
        ).order_by("compte__nom")

        if valeur_min is not None:
            valeurs_list = valeurs_list.filter(valeur__gte=valeur_min)

        if valeur_max is not None:
            valeurs_list = valeurs_list.filter(valeur__lte=valeur_max)

        paginator = Paginator(valeurs_list, 10)
        valeurs_page = paginator.get_page(page_number)
        serializer = ValeurCompteIrfsSerializer(valeurs_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": valeurs_page.has_next(),
                "previous": valeurs_page.has_previous(),
            }
        )


class ListAcheteurPassifFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        valeur_min = request.query_params.get("valeur_min", "")
        valeur_max = request.query_params.get("valeur_max", "")

        try:
            valeur_min = Decimal(valeur_min) if valeur_min else None
            valeur_max = Decimal(valeur_max) if valeur_max else None
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de valeur_min et valeur_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        valeurs_list = ValeurCompteIrfs.objects.filter(
            acheteur__pk=acheteur_id,
            annee__annee__icontains=annee,
            compte__type_compte__icontains="Passif",
        ).order_by("compte__nom")

        if valeur_min is not None:
            valeurs_list = valeurs_list.filter(valeur__gte=valeur_min)

        if valeur_max is not None:
            valeurs_list = valeurs_list.filter(valeur__lte=valeur_max)

        paginator = Paginator(valeurs_list, 10)
        valeurs_page = paginator.get_page(page_number)
        serializer = ValeurCompteIrfsSerializer(valeurs_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": valeurs_page.has_next(),
                "previous": valeurs_page.has_previous(),
            }
        )


class SearchAcheteurValeurCompteFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valeurs_list = ValeurCompteIrfs.objects.filter(
            acheteur__pk=acheteur_id, compte__nom__icontains=search_term
        ).order_by("compte__nom")

        paginator = Paginator(valeurs_list, 10)
        page_number = request.query_params.get("page", 1)
        valeurs_page = paginator.get_page(page_number)
        serializer = ValeurCompteIrfsSerializer(valeurs_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": valeurs_page.has_next(),
                "previous": valeurs_page.has_previous(),
            }
        )


class AddAcheteurValeurCompteFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddValeurCompteIrfsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


import json

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class AjoutAcheteurValeurCompteFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)

            # Vérifiez que 'data' est une liste
            if not isinstance(data, list):
                return Response(
                    {"error": "Invalid data format"}, status=status.HTTP_400_BAD_REQUEST
                )

            for item in data:
                serializer = AddValeurCompteIrfsSerializer(
                    data={
                        "acheteur": item.get("acheteur_id"),
                        "compte": item.get("compte"),
                        "annee": item.get("annee"),
                        "valeur": item.get("valeur"),
                        "devise": item.get("devise"),
                    }
                )
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(
                        serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )

            return Response(
                {"message": "Données sauvegardées avec succès"},
                status=status.HTTP_201_CREATED,
            )
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST
            )


class EditAcheteurValeurCompteFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, valeur_actif_irfs_id, *args, **kwargs):
        valeur = ValeurCompteIrfs.objects.filter(
            id=valeur_actif_irfs_id, acheteur__pk=acheteur_id
        ).first()
        if not valeur:
            return Response(
                {"detail": "Valeur non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetValeurCompteIrfsSerializer(valeur)
        return Response(serializer.data)

    def put(self, request, acheteur_id, valeur_actif_irfs_id, *args, **kwargs):
        valeur = ValeurCompteIrfs.objects.filter(
            id=valeur_actif_irfs_id, acheteur__pk=acheteur_id
        ).first()
        if not valeur:
            return Response(
                {"detail": "Valeur non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditValeurCompteIrfsSerializer(
            valeur, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurValeurCompteFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valeurs = ValeurCompteIrfs.objects.filter(id__in=ids, acheteur__pk=acheteur_id)
        if not valeurs.exists():
            return Response(
                {"error": "Aucune valeur trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = valeurs.delete()
        return Response(
            {"message": f"{count} valeurs supprimées avec succès."},
            status=status.HTTP_200_OK,
        )


class ListAcheteurRatioFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        type_ratio = request.query_params.get("type_ratio", "")

        ratios_list = RatioFinancierIrfs.objects.filter().order_by("nom")

        if type_ratio:
            ratios_list = ratios_list.filter(type_ratio__icontains=type_ratio)

        paginator = Paginator(ratios_list, 10)
        ratios_page = paginator.get_page(page_number)
        serializer = RatioFinancierIrfsSerializer(ratios_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": ratios_page.has_next(),
                "previous": ratios_page.has_previous(),
            }
        )


class SearchAcheteurRatioFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ratios_list = RatioFinancierIrfs.objects.filter(
            nom__icontains=search_term
        ).order_by("nom")

        paginator = Paginator(ratios_list, 10)
        page_number = request.query_params.get("page", 1)
        ratios_page = paginator.get_page(page_number)
        serializer = RatioFinancierIrfsSerializer(ratios_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": ratios_page.has_next(),
                "previous": ratios_page.has_previous(),
            }
        )


class AddAcheteurRatioFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddRatioFinancierIrfsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurRatioFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ratio_irfs_id, *args, **kwargs):
        ratio = RatioFinancierIrfs.objects.filter(id=ratio_irfs_id).first()
        if not ratio:
            return Response(
                {"detail": "Ratio non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetRatioFinancierIrfsSerializer(ratio)
        return Response(serializer.data)

    def put(self, request, ratio_irfs_id, *args, **kwargs):
        ratio = RatioFinancierIrfs.objects.filter(id=ratio_irfs_id).first()
        if not ratio:
            return Response(
                {"detail": "Ratio non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditRatioFinancierIrfsSerializer(
            ratio, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurRatioFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ratios = RatioFinancierIrfs.objects.filter(id__in=ids)
        if not ratios.exists():
            return Response(
                {"error": "Aucun ratio trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = ratios.delete()
        return Response(
            {"message": f"{count} ratios supprimés avec succès."},
            status=status.HTTP_200_OK,
        )


class ListAcheteurValeurRatioFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        request.query_params.get("search", "")
        annee = request.query_params.get("annee", "")
        valeur_min = request.query_params.get("valeur_min", "")
        valeur_max = request.query_params.get("valeur_max", "")

        try:
            valeur_min = Decimal(valeur_min) if valeur_min else None
            valeur_max = Decimal(valeur_max) if valeur_max else None
        except Decimal.InvalidOperation:
            return Response(
                {
                    "error": "Les valeurs de valeur_min et valeur_max doivent être des nombres décimaux valides."
                },
                status=400,
            )

        valeurs_list = ValeurRatioIrfs.objects.filter(
            acheteur_id=acheteur_id, annee__nom__icontains=annee
        ).order_by("ratio__nom")

        if valeur_min is not None:
            valeurs_list = valeurs_list.filter(valeur__gte=valeur_min)

        if valeur_max is not None:
            valeurs_list = valeurs_list.filter(valeur__lte=valeur_max)

        paginator = Paginator(valeurs_list, 10)
        valeurs_page = paginator.get_page(page_number)
        serializer = ValeurRatioIrfsSerializer(valeurs_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": valeurs_page.has_next(),
                "previous": valeurs_page.has_previous(),
            }
        )


class SearchAcheteurValeurRatioFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valeurs_list = ValeurRatioIrfs.objects.filter(
            acheteur_id=acheteur_id, ratio__nom__icontains=search_term
        ).order_by("ratio__nom")

        paginator = Paginator(valeurs_list, 10)
        page_number = request.query_params.get("page", 1)
        valeurs_page = paginator.get_page(page_number)
        serializer = ValeurRatioIrfsSerializer(valeurs_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": valeurs_page.has_next(),
                "previous": valeurs_page.has_previous(),
            }
        )


class AddAcheteurValeurRatioFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        serializer = AddValeurRatioIrfsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(acheteur_id=acheteur_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurValeurRatioFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, valeur_ratio_irfs_id, *args, **kwargs):
        valeur = ValeurRatioIrfs.objects.filter(
            id=valeur_ratio_irfs_id, acheteur_id=acheteur_id
        ).first()
        if not valeur:
            return Response(
                {"detail": "Valeur non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetValeurRatioIrfsSerializer(valeur)
        return Response(serializer.data)

    def put(self, request, acheteur_id, valeur_ratio_irfs_id, *args, **kwargs):
        valeur = ValeurRatioIrfs.objects.filter(
            id=valeur_ratio_irfs_id, acheteur_id=acheteur_id
        ).first()
        if not valeur:
            return Response(
                {"detail": "Valeur non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditValeurRatioIrfsSerializer(
            valeur, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurValeurRatioFinancierIrfsView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valeurs = ValeurRatioIrfs.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not valeurs.exists():
            return Response(
                {"error": "Aucune valeur trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = valeurs.delete()
        return Response(
            {"message": f"{count} valeurs supprimées avec succès."},
            status=status.HTTP_200_OK,
        )


from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import Certification
from main.serializers import (AddCertificationSerializer,
                              DetailCertificationSerializer,
                              EditCertificationSerializer,
                              ListCertificationSerializer,
                              SearchCertificationSerializer)


class ListAcheteurCertificationView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        certifications = Certification.objects.filter(acheteur_id=acheteur_id).order_by(
            "-date_obtention"
        )

        paginator = Paginator(certifications, 10)
        certification_page = paginator.get_page(page_number)
        serializer = ListCertificationSerializer(certification_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": certification_page.has_next(),
                "previous": certification_page.has_previous(),
            }
        )

class SearchAcheteurCertificationView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        certifications = Certification.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(nom_certification__icontains=search_term)
                | Q(type_certification__icontains=search_term)
                | Q(description__icontains=search_term)
            )
        ).order_by("-date_obtention")

        paginator = Paginator(certifications, 10)
        page_number = request.query_params.get("page", 1)
        certification_page = paginator.get_page(page_number)
        serializer = SearchCertificationSerializer(certification_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": certification_page.has_next(),
                "previous": certification_page.has_previous(),
            }
        )

class AddAcheteurCertificationView(APIView):
    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddCertificationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DetailAcheteurCertificationView(APIView):
    def get(self, request, acheteur_id, certification_id, *args, **kwargs):
        certification = Certification.objects.filter(
            id=certification_id, acheteur_id=acheteur_id
        ).first()
        if not certification:
            return Response(
                {"detail": "Certification non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DetailCertificationSerializer(certification)
        return Response(serializer.data)

class EditAcheteurCertificationView(APIView):
    def put(self, request, acheteur_id, certification_id, *args, **kwargs):
        certification = Certification.objects.filter(
            id=certification_id, acheteur_id=acheteur_id
        ).first()
        if not certification:
            return Response(
                {"detail": "Certification non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EditCertificationSerializer(
            certification, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurCertificationView(APIView):
    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        certifications = Certification.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not certifications.exists():
            return Response(
                {"error": "Aucune certification trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = certifications.delete()
        return Response(
            {"message": f"{count} certifications supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        
class AcheteurCertificationListOneView(APIView):
    """
    API pour gérer les certifications d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des certifications de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        certifications = Certification.objects.filter(
            acheteur=acheteur
        ).order_by('-date_obtention', '-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            certifications = certifications.filter(
                Q(nom_certification__icontains=search) |
                Q(type_certification__icontains=search) |
                Q(organisme_delivreur__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filtrer par type si spécifié
        type_filter = request.query_params.get('type', '')
        if type_filter:
            certifications = certifications.filter(type_certification=type_filter)
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(certifications, request)
        
        serializer = CertificationOneSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée une nouvelle certification pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        # Passer le contexte avec la requête au serializer
        serializer = AddCertificationOneSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            # Le serializer gère maintenant created_by et updated_by
            certification = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_CERTIFICATION',
                object_id=certification.id,
                object_type='Certification',
                details=f"Certification ajoutée pour l'acheteur {acheteur.nom} ({acheteur.code}): {certification.nom_certification or certification.get_type_display()}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Certification ajoutée avec succès",
                "data": CertificationOneSerializer(certification).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurCertificationDetailOneView(APIView):
    """
    API pour gérer une certification spécifique d'un acheteur
    Méthodes: GET (détail), PUT (modification), DELETE (suppression)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_certification(self, acheteur_id, certification_id):
        """Récupère la certification ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            Certification.objects.select_related('acheteur'),
            id=certification_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, certification_id):
        """Récupère les détails d'une certification spécifique"""
        certification = self.get_certification(acheteur_id, certification_id)
        serializer = CertificationOneSerializer(certification)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, certification_id):
        """Modifie une certification existante"""
        certification = self.get_certification(acheteur_id, certification_id)
        
        # Passer le contexte avec la requête pour que le serializer puisse accéder à request.user
        serializer = EditCertificationOneSerializer(
            certification, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Le serializer gère maintenant updated_by via sa méthode update()
            certification = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_CERTIFICATION',
                object_id=certification.id,
                object_type='Certification',
                details=f"Certification modifiée pour l'acheteur {certification.acheteur.nom}: {certification.nom_certification or certification.get_type_display()}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Certification modifiée avec succès",
                "data": CertificationOneSerializer(certification).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id, certification_id):
        """Supprime une certification"""
        certification = self.get_certification(acheteur_id, certification_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_CERTIFICATION',
            object_id=certification.id,
            object_type='Certification',
            details=f"Certification supprimée pour l'acheteur {certification.acheteur.nom}: {certification.nom_certification or certification.get_type_display()}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        certification.delete()
        return Response({
            "message": "Certification supprimée avec succès"
        }, status=status.HTTP_200_OK)






from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import InnovationDeveloppement
from main.serializers import (AddInnovationDeveloppementSerializer,
                              DetailInnovationDeveloppementSerializer,
                              EditInnovationDeveloppementSerializer,
                              ListInnovationDeveloppementSerializer,
                              SearchInnovationDeveloppementSerializer)


class ListAcheteurInnovationView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        innovations = InnovationDeveloppement.objects.filter(
            acheteur_id=acheteur_id
        ).order_by("-date_debut")

        paginator = Paginator(innovations, 10)
        innovation_page = paginator.get_page(page_number)
        serializer = ListInnovationDeveloppementSerializer(innovation_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": innovation_page.has_next(),
                "previous": innovation_page.has_previous(),
            }
        )

class SearchAcheteurInnovationView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        innovations = InnovationDeveloppement.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(titre__icontains=search_term)
                | Q(type_innovation__icontains=search_term)
                | Q(description__icontains=search_term)
            )
        ).order_by("-date_debut")

        paginator = Paginator(innovations, 10)
        page_number = request.query_params.get("page", 1)
        innovation_page = paginator.get_page(page_number)
        serializer = SearchInnovationDeveloppementSerializer(innovation_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": innovation_page.has_next(),
                "previous": innovation_page.has_previous(),
            }
        )

class AddAcheteurInnovationView(APIView):
    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddInnovationDeveloppementSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DetailAcheteurInnovationView(APIView):
    def get(self, request, acheteur_id, innovation_id, *args, **kwargs):
        innovation = InnovationDeveloppement.objects.filter(
            id=innovation_id, acheteur_id=acheteur_id
        ).first()
        if not innovation:
            return Response(
                {"detail": "Innovation non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = DetailInnovationDeveloppementSerializer(innovation)
        return Response(serializer.data)

class EditAcheteurInnovationView(APIView):
    def put(self, request, acheteur_id, innovation_id, *args, **kwargs):
        innovation = InnovationDeveloppement.objects.filter(
            id=innovation_id, acheteur_id=acheteur_id
        ).first()
        if not innovation:
            return Response(
                {"detail": "Innovation non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditInnovationDeveloppementSerializer(
            innovation, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurInnovationView(APIView):
    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        innovations = InnovationDeveloppement.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not innovations.exists():
            return Response(
                {"error": "Aucune innovation trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = innovations.delete()
        return Response(
            {"message": f"{count} innovations supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        
class AcheteurInnovationDeveloppementListOneView(APIView):
    """
    API pour gérer les innovations et développements d'un acheteur
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des innovations de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        innovations = InnovationDeveloppement.objects.filter(
            acheteur=acheteur
        ).select_related(
            'created_by', 
            'updated_by',
            'acheteur'
        ).order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            innovations = innovations.filter(
                Q(titre__icontains=search) |
                Q(description__icontains=search) |
                Q(type_innovation__icontains=search)
            )
        
        # Filtrer par type d'innovation
        type_innovation = request.query_params.get('type_innovation')
        if type_innovation:
            innovations = innovations.filter(type_innovation=type_innovation)
        
        # Filtrer par période
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        if date_debut:
            innovations = innovations.filter(date_debut__gte=date_debut)
        if date_fin:
            innovations = innovations.filter(date_fin__lte=date_fin)
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(innovations, request)
        
        serializer = InnovationDeveloppementOneSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée une nouvelle innovation pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = AddInnovationDeveloppementOneSerializer(data=data)
        
        if serializer.is_valid():
            # Ajouter l'utilisateur courant comme créateur
            innovation = serializer.save(
                created_by=request.user,
                updated_by=request.user
            )
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_INNOVATION',
                object_id=innovation.id,
                object_type='InnovationDeveloppement',
                details=f"Innovation créée pour l'acheteur {acheteur.nom} ({acheteur.code}): {innovation.titre}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Innovation créée avec succès",
                "data": InnovationDeveloppementOneSerializer(innovation).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurInnovationDeveloppementDetailOneView(APIView):
    """
    API pour gérer une innovation spécifique d'un acheteur
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_innovation(self, acheteur_id, innovation_id):
        """Récupère l'innovation ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            InnovationDeveloppement.objects.select_related(
                'created_by', 
                'updated_by',
                'acheteur'
            ),
            id=innovation_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, innovation_id):
        """Récupère les détails d'une innovation spécifique"""
        innovation = self.get_innovation(acheteur_id, innovation_id)
        serializer = InnovationDeveloppementOneSerializer(innovation)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, innovation_id):
        """Modifie une innovation existante"""
        innovation = self.get_innovation(acheteur_id, innovation_id)
        
        serializer = EditInnovationDeveloppementOneSerializer(
            innovation, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            innovation = serializer.save(
                updated_by=request.user
            )
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_INNOVATION',
                object_id=innovation.id,
                object_type='InnovationDeveloppement',
                details=f"Innovation modifiée pour l'acheteur {innovation.acheteur.nom}: {innovation.titre}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Innovation modifiée avec succès",
                "data": InnovationDeveloppementOneSerializer(innovation).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id, innovation_id):
        """Supprime une innovation"""
        innovation = self.get_innovation(acheteur_id, innovation_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_INNOVATION',
            object_id=innovation.id,
            object_type='InnovationDeveloppement',
            details=f"Innovation supprimée pour l'acheteur {innovation.acheteur.nom}: {innovation.titre}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        innovation.delete()
        return Response({
            "message": "Innovation supprimée avec succès"
        }, status=status.HTTP_200_OK)







from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import StrategiePlanification
from main.serializers import (AddStrategiePlanificationSerializer,
                              DetailStrategiePlanificationSerializer,
                              EditStrategiePlanificationSerializer,
                              ListStrategiePlanificationSerializer,
                              SearchStrategiePlanificationSerializer)


class ListAcheteurStrategieView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        strategies = StrategiePlanification.objects.filter(
            acheteur_id=acheteur_id
        ).order_by("-date_mise_en_place")

        paginator = Paginator(strategies, 10)
        strategie_page = paginator.get_page(page_number)
        serializer = ListStrategiePlanificationSerializer(strategie_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": strategie_page.has_next(),
                "previous": strategie_page.has_previous(),
            }
        )

class SearchAcheteurStrategieView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        strategies = StrategiePlanification.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(type_strategie__icontains=search_term)
                | Q(description__icontains=search_term)
            )
        ).order_by("-date_mise_en_place")

        paginator = Paginator(strategies, 10)
        page_number = request.query_params.get("page", 1)
        strategie_page = paginator.get_page(page_number)
        serializer = SearchStrategiePlanificationSerializer(strategie_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": strategie_page.has_next(),
                "previous": strategie_page.has_previous(),
            }
        )

class AddAcheteurStrategieView(APIView):
    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddStrategiePlanificationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DetailAcheteurStrategieView(APIView):
    def get(self, request, acheteur_id, strategie_id, *args, **kwargs):
        strategie = StrategiePlanification.objects.filter(
            id=strategie_id, acheteur_id=acheteur_id
        ).first()
        if not strategie:
            return Response(
                {"detail": "Stratégie non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = DetailStrategiePlanificationSerializer(strategie)
        return Response(serializer.data)

class EditAcheteurStrategieView(APIView):
    def put(self, request, acheteur_id, strategie_id, *args, **kwargs):
        strategie = StrategiePlanification.objects.filter(
            id=strategie_id, acheteur_id=acheteur_id
        ).first()
        if not strategie:
            return Response(
                {"detail": "Stratégie non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditStrategiePlanificationSerializer(
            strategie, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurStrategieView(APIView):
    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        strategies = StrategiePlanification.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not strategies.exists():
            return Response(
                {"error": "Aucune stratégie trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = strategies.delete()
        return Response(
            {"message": f"{count} stratégies supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        
class AcheteurStrategiePlanificationListOneView(APIView):
    """
    API pour gérer les stratégies et planifications d'un acheteur
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des stratégies de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        strategies = StrategiePlanification.objects.filter(
            acheteur=acheteur
        ).select_related(
            'created_by', 
            'updated_by',
            'acheteur'
        ).order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            strategies = strategies.filter(
                Q(description__icontains=search) |
                Q(type_strategie__icontains=search)
            )
        
        # Filtrer par type de stratégie
        type_strategie = request.query_params.get('type_strategie')
        if type_strategie:
            strategies = strategies.filter(type_strategie=type_strategie)
        
        # Filtrer par période
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        if date_debut:
            strategies = strategies.filter(date_mise_en_place__gte=date_debut)
        if date_fin:
            strategies = strategies.filter(date_mise_en_place__lte=date_fin)
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(strategies, request)
        
        serializer = StrategiePlanificationOneSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée une nouvelle stratégie pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = AddStrategiePlanificationOneSerializer(data=data)
        
        if serializer.is_valid():
            # Ajouter l'utilisateur courant comme créateur
            strategie = serializer.save(
                created_by=request.user,
                updated_by=request.user
            )
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_STRATEGIE',
                object_id=strategie.id,
                object_type='StrategiePlanification',
                details=f"Stratégie créée pour l'acheteur {acheteur.nom} ({acheteur.code}): {strategie.get_type_strategie_display()}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Stratégie créée avec succès",
                "data": StrategiePlanificationOneSerializer(strategie).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurStrategiePlanificationDetailOneView(APIView):
    """
    API pour gérer une stratégie spécifique d'un acheteur
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_strategie(self, acheteur_id, strategie_id):
        """Récupère la stratégie ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            StrategiePlanification.objects.select_related(
                'created_by', 
                'updated_by',
                'acheteur'
            ),
            id=strategie_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, strategie_id):
        """Récupère les détails d'une stratégie spécifique"""
        strategie = self.get_strategie(acheteur_id, strategie_id)
        serializer = StrategiePlanificationOneSerializer(strategie)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, strategie_id):
        """Modifie une stratégie existante"""
        strategie = self.get_strategie(acheteur_id, strategie_id)
        
        serializer = EditStrategiePlanificationOneSerializer(
            strategie, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            strategie = serializer.save(
                updated_by=request.user
            )
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_STRATEGIE',
                object_id=strategie.id,
                object_type='StrategiePlanification',
                details=f"Stratégie modifiée pour l'acheteur {strategie.acheteur.nom}: {strategie.get_type_strategie_display()}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Stratégie modifiée avec succès",
                "data": StrategiePlanificationOneSerializer(strategie).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id, strategie_id):
        """Supprime une stratégie"""
        strategie = self.get_strategie(acheteur_id, strategie_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_STRATEGIE',
            object_id=strategie.id,
            object_type='StrategiePlanification',
            details=f"Stratégie supprimée pour l'acheteur {strategie.acheteur.nom}: {strategie.get_type_strategie_display()}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        strategie.delete()
        return Response({
            "message": "Stratégie supprimée avec succès"
        }, status=status.HTTP_200_OK)











from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import ConformiteReglementation
from main.serializers import (AddConformiteReglementationSerializer,
                              DetailConformiteReglementationSerializer,
                              EditConformiteReglementationSerializer,
                              ListConformiteReglementationSerializer,
                              SearchConformiteReglementationSerializer)


class ListAcheteurConformiteView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        conformites = ConformiteReglementation.objects.filter(
            acheteur_id=acheteur_id
        ).order_by("-date_verification")

        paginator = Paginator(conformites, 10)
        conformite_page = paginator.get_page(page_number)
        serializer = ListConformiteReglementationSerializer(conformite_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": conformite_page.has_next(),
                "previous": conformite_page.has_previous(),
            }
        )

class SearchAcheteurConformiteView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conformites = ConformiteReglementation.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(type_conformite__icontains=search_term)
                | Q(commentaires__icontains=search_term)
            )
        ).order_by("-date_verification")

        paginator = Paginator(conformites, 10)
        page_number = request.query_params.get("page", 1)
        conformite_page = paginator.get_page(page_number)
        serializer = SearchConformiteReglementationSerializer(
            conformite_page, many=True
        )

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": conformite_page.has_next(),
                "previous": conformite_page.has_previous(),
            }
        )

class AddAcheteurConformiteView(APIView):
    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddConformiteReglementationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DetailAcheteurConformiteView(APIView):
    def get(self, request, acheteur_id, conformite_id, *args, **kwargs):
        conformite = ConformiteReglementation.objects.filter(
            id=conformite_id, acheteur_id=acheteur_id
        ).first()
        if not conformite:
            return Response(
                {"detail": "Conformité non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = DetailConformiteReglementationSerializer(conformite)
        return Response(serializer.data)

class EditAcheteurConformiteView(APIView):
    def put(self, request, acheteur_id, conformite_id, *args, **kwargs):
        conformite = ConformiteReglementation.objects.filter(
            id=conformite_id, acheteur_id=acheteur_id
        ).first()
        if not conformite:
            return Response(
                {"detail": "Conformité non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditConformiteReglementationSerializer(
            conformite, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurConformiteView(APIView):
    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conformites = ConformiteReglementation.objects.filter(
            id__in=ids, acheteur_id=acheteur_id
        )
        if not conformites.exists():
            return Response(
                {"error": "Aucune conformité trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = conformites.delete()
        return Response(
            {"message": f"{count} conformités supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        
class AcheteurConformiteReglementationListOneView(APIView):
    """
    API pour gérer les conformités et réglementations d'un acheteur
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des conformités de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        conformites = ConformiteReglementation.objects.filter(
            acheteur=acheteur
        ).select_related(
            'created_by', 
            'updated_by',
            'acheteur'
        ).order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            conformites = conformites.filter(
                Q(type_conformite__icontains=search) |
                Q(details_non_conformite__icontains=search) |
                Q(organisme_controle__icontains=search) |
                Q(commentaires__icontains=search)
            )
        
        # Filtrer par type de conformité
        type_conformite = request.query_params.get('type_conformite')
        if type_conformite:
            conformites = conformites.filter(type_conformite=type_conformite)
        
        # Filtrer par statut
        statut = request.query_params.get('statut')
        if statut is not None:
            conformites = conformites.filter(statut=(statut.lower() == 'true'))
        
        # Filtrer par période de vérification
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        if date_debut:
            conformites = conformites.filter(date_verification__gte=date_debut)
        if date_fin:
            conformites = conformites.filter(date_verification__lte=date_fin)
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(conformites, request)
        
        serializer = ConformiteReglementationOneSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée une nouvelle conformité pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = AddConformiteReglementationOneSerializer(data=data)
        
        if serializer.is_valid():
            # Ajouter l'utilisateur courant comme créateur
            conformite = serializer.save(
                created_by=request.user,
                updated_by=request.user
            )
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_CONFORMITE',
                object_id=conformite.id,
                object_type='ConformiteReglementation',
                details=f"Conformité créée pour l'acheteur {acheteur.nom} ({acheteur.code}): {conformite.get_type_conformite_display()} - {'Conforme' if conformite.statut else 'Non-conforme'}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Conformité créée avec succès",
                "data": ConformiteReglementationOneSerializer(conformite).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurConformiteReglementationDetailOneView(APIView):
    """
    API pour gérer une conformité spécifique d'un acheteur
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_conformite(self, acheteur_id, conformite_id):
        """Récupère la conformité ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            ConformiteReglementation.objects.select_related(
                'created_by', 
                'updated_by',
                'acheteur'
            ),
            id=conformite_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, conformite_id):
        """Récupère les détails d'une conformité spécifique"""
        conformite = self.get_conformite(acheteur_id, conformite_id)
        serializer = ConformiteReglementationOneSerializer(conformite)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, conformite_id):
        """Modifie une conformité existante"""
        conformite = self.get_conformite(acheteur_id, conformite_id)
        
        serializer = EditConformiteReglementationOneSerializer(
            conformite, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            conformite = serializer.save(
                updated_by=request.user
            )
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_CONFORMITE',
                object_id=conformite.id,
                object_type='ConformiteReglementation',
                details=f"Conformité modifiée pour l'acheteur {conformite.acheteur.nom}: {conformite.get_type_conformite_display()} - {'Conforme' if conformite.statut else 'Non-conforme'}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Conformité modifiée avec succès",
                "data": ConformiteReglementationOneSerializer(conformite).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id, conformite_id):
        """Supprime une conformité"""
        conformite = self.get_conformite(acheteur_id, conformite_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_CONFORMITE',
            object_id=conformite.id,
            object_type='ConformiteReglementation',
            details=f"Conformité supprimée pour l'acheteur {conformite.acheteur.nom}: {conformite.get_type_conformite_display()}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        conformite.delete()
        return Response({
            "message": "Conformité supprimée avec succès"
        }, status=status.HTTP_200_OK)









from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import AlerteLog
from main.serializers import (AddAlerteLogSerializer,
                              DetailAlerteLogSerializer,
                              EditAlerteLogSerializer, ListAlerteLogSerializer,
                              SearchAlerteLogSerializer)


class ListAlerteLogView(APIView):
    def get(self, request, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        alertes = AlerteLog.objects.all().order_by("-date_creation")

        paginator = Paginator(alertes, 10)
        alerte_page = paginator.get_page(page_number)
        serializer = ListAlerteLogSerializer(alerte_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": alerte_page.has_next(),
                "previous": alerte_page.has_previous(),
            }
        )


class SearchAlerteLogView(APIView):
    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alertes = AlerteLog.objects.filter(
            Q(message__icontains=search_term)
            | Q(acheteur__nom__icontains=search_term)
            | Q(element_surveille__nom__icontains=search_term)
        ).order_by("-date_creation")

        paginator = Paginator(alertes, 10)
        page_number = request.query_params.get("page", 1)
        alerte_page = paginator.get_page(page_number)
        serializer = SearchAlerteLogSerializer(alerte_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": alerte_page.has_next(),
                "previous": alerte_page.has_previous(),
            }
        )


class AddAlerteLogView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AddAlerteLogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DetailAlerteLogView(APIView):
    def get(self, request, alerte_id, *args, **kwargs):
        alerte = AlerteLog.objects.filter(id=alerte_id).first()
        if not alerte:
            return Response(
                {"detail": "Alerte non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = DetailAlerteLogSerializer(alerte)
        return Response(serializer.data)


class EditAlerteLogView(APIView):
    def put(self, request, alerte_id, *args, **kwargs):
        alerte = AlerteLog.objects.filter(id=alerte_id).first()
        if not alerte:
            return Response(
                {"detail": "Alerte non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditAlerteLogSerializer(alerte, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAlerteLogView(APIView):
    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alertes = AlerteLog.objects.filter(id__in=ids)
        if not alertes.exists():
            return Response(
                {"error": "Aucune alerte trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = alertes.delete()
        return Response(
            {"message": f"{count} alertes supprimées avec succès."},
            status=status.HTTP_200_OK,
        )







class ListAcheteurEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        email_list = EmailAcheteur.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            email_list = email_list.filter(
                Q(email__icontains=search_term)
            )

        paginator = Paginator(email_list, 10)
        email_page = paginator.get_page(page_number)
        serializer = EmailAcheteurSerializer(email_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": email_page.has_next(),
                "previous": email_page.has_previous(),
            }
        )

class SearchAcheteurEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email_list = EmailAcheteur.objects.filter(
            Q(acheteur_id=acheteur_id) & Q(email__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(email_list, 10)
        page_number = request.query_params.get("page", 1)
        email_page = paginator.get_page(page_number)
        serializer = EmailAcheteurSerializer(email_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": email_page.has_next(),
                "previous": email_page.has_previous(),
            }
        )

class AddAcheteurEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddEmailAcheteurSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, email_id, *args, **kwargs):
        email = EmailAcheteur.objects.filter(id=email_id, acheteur_id=acheteur_id).first()
        if not email:
            return Response(
                {"detail": "Email non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetEmailAcheteurSerializer(email)
        return Response(serializer.data)

    def put(self, request, acheteur_id, email_id, *args, **kwargs):
        email = EmailAcheteur.objects.filter(id=email_id, acheteur_id=acheteur_id).first()
        if not email:
            return Response(
                {"detail": "Email non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditEmailAcheteurSerializer(email, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        emails = EmailAcheteur.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not emails.exists():
            return Response(
                {"error": "Aucun email trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = emails.delete()
        return Response(
            {"message": f"{count} emails supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
        
        
        
        
        

class ListAcheteurEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        email_list = EmailAcheteur.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            email_list = email_list.filter(
                Q(email__icontains=search_term)
            )

        paginator = Paginator(email_list, 10)
        email_page = paginator.get_page(page_number)
        serializer = EmailAcheteurSerializer(email_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": email_page.has_next(),
                "previous": email_page.has_previous(),
            }
        )

class SearchAcheteurEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email_list = EmailAcheteur.objects.filter(
            Q(acheteur_id=acheteur_id) & Q(email__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(email_list, 10)
        page_number = request.query_params.get("page", 1)
        email_page = paginator.get_page(page_number)
        serializer = EmailAcheteurSerializer(email_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": email_page.has_next(),
                "previous": email_page.has_previous(),
            }
        )

class AddAcheteurEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddEmailAcheteurSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, email_id, *args, **kwargs):
        email = EmailAcheteur.objects.filter(id=email_id, acheteur_id=acheteur_id).first()
        if not email:
            return Response(
                {"detail": "Email non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetEmailAcheteurSerializer(email)
        return Response(serializer.data)

    def put(self, request, acheteur_id, email_id, *args, **kwargs):
        email = EmailAcheteur.objects.filter(id=email_id, acheteur_id=acheteur_id).first()
        if not email:
            return Response(
                {"detail": "Email non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditEmailAcheteurSerializer(email, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        emails = EmailAcheteur.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not emails.exists():
            return Response(
                {"error": "Aucun email trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = emails.delete()
        return Response(
            {"message": f"{count} emails supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
        
 
 
 
 



class ListAcheteurTelephoneView(APIView):
    """
    Vue pour lister et rechercher les numéros de téléphone d'un acheteur.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        portable_list = TelephoneAcheteur.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            portable_list = portable_list.filter(
                Q(telephone__icontains=search_term)
            )

        paginator = Paginator(portable_list, 10)
        portable_page = paginator.get_page(page_number)
        serializer = GetPortableAcheteurSerializer(portable_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": portable_page.has_next(),
                "previous": portable_page.has_previous(),
            }
        )


class AddAcheteurTelephoneView(APIView):
    """
    Vue pour ajouter un nouveau numéro de téléphone à un acheteur.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        # Le sérialiseur AddPortableAcheteurSerializer attend un champ 'portable',
        # mais votre modèle a un champ 'telephone'. Assurez-vous que les deux
        # sont synchronisés. Pour cet exemple, j'ai supposé que le nom du champ
        # 'portable' du sérialiseur correspondait au champ 'telephone' du modèle.
        # Si ce n'est pas le cas, vous devrez ajuster le sérialiseur ou la vue.
        
        serializer = AddPortableAcheteurSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAcheteurTelephoneView(APIView):
    """
    Vue pour récupérer les détails et modifier un numéro de téléphone existant.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, portable_id, *args, **kwargs):
        portable = TelephoneAcheteur.objects.filter(id=portable_id, acheteur_id=acheteur_id).first()
        if not portable:
            return Response(
                {"detail": _("Numéro de téléphone non trouvé.")},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetPortableAcheteurSerializer(portable)
        return Response(serializer.data)

    def put(self, request, acheteur_id, portable_id, *args, **kwargs):
        portable = TelephoneAcheteur.objects.filter(id=portable_id, acheteur_id=acheteur_id).first()
        if not portable:
            return Response(
                {"detail": _("Numéro de téléphone non trouvé.")},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditPortableAcheteurSerializer(portable, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAcheteurTelephoneView(APIView):
    """
    Vue pour supprimer un ou plusieurs numéros de téléphone.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": _("Une liste d'IDs est requise.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        portables = TelephoneAcheteur.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not portables.exists():
            return Response(
                {"error": _("Aucun numéro de téléphone trouvé pour les IDs fournis.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = portables.delete()
        return Response(
            {"message": _(f"{count} numéros de téléphone supprimés avec succès.")},
            status=status.HTTP_200_OK,
        )      
        
        
  
  
  
        


class ListAcheteurAdresseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        adresse_list = AdresseAcheteur.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            adresse_list = adresse_list.filter(
                Q(adresse__icontains=search_term)
            )

        paginator = Paginator(adresse_list, 10)
        adresse_page = paginator.get_page(page_number)
        serializer = AdresseAcheteurSerializer(adresse_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": adresse_page.has_next(),
                "previous": adresse_page.has_previous(),
            }
        )

class SearchAcheteurAdresseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        adresse_list = AdresseAcheteur.objects.filter(
            Q(acheteur_id=acheteur_id) & Q(adresse__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(adresse_list, 10)
        page_number = request.query_params.get("page", 1)
        adresse_page = paginator.get_page(page_number)
        serializer = AdresseAcheteurSerializer(adresse_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": adresse_page.has_next(),
                "previous": adresse_page.has_previous(),
            }
        )

class AddAcheteurAdresseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddAdresseAcheteurSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurAdresseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, adresse_id, *args, **kwargs):
        adresse = AdresseAcheteur.objects.filter(id=adresse_id, acheteur_id=acheteur_id).first()
        if not adresse:
            return Response(
                {"detail": "Adresse non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetAdresseAcheteurSerializer(adresse)
        return Response(serializer.data)

    def put(self, request, acheteur_id, adresse_id, *args, **kwargs):
        adresse = AdresseAcheteur.objects.filter(id=adresse_id, acheteur_id=acheteur_id).first()
        if not adresse:
            return Response(
                {"detail": "Adresse non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditAdresseAcheteurSerializer(adresse, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurAdresseView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        adresses = AdresseAcheteur.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not adresses.exists():
            return Response(
                {"error": "Aucune adresse trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = adresses.delete()
        return Response(
            {"message": f"{count} adresses supprimées avec succès."},
            status=status.HTTP_200_OK,
        )

class AcheteurAdresseListView(APIView):
    """
    API pour gérer les adresses d'un acheteur
    - GET : Liste toutes les adresses de l'acheteur
    - POST : Crée une nouvelle adresse pour l'acheteur
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des adresses de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        adresses = AdresseAcheteur.objects.filter(
            acheteur=acheteur
        ).select_related('acheteur', 'created_by', 'updated_by').order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            adresses = adresses.filter(adresse__icontains=search)
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(adresses, request)
        
        serializer = AdresseAcheteurSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée une nouvelle adresse pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = AdresseAcheteurCreateSerializer(
            data=data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Sauvegarder l'adresse
            adresse = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_ADRESSE',
                object_id=adresse.id,
                object_type='AdresseAcheteur',
                details=f"Adresse créée pour l'acheteur {acheteur.nom}: {(adresse.rue or adresse.adresse or '')[:50]}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Adresse créée avec succès",
                "data": AdresseAcheteurSerializer(adresse).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurAdresseDetailView(APIView):
    """
    API pour gérer une adresse spécifique d'un acheteur
    - GET : Détails d'une adresse
    - PUT : Modifie une adresse
    - DELETE : Supprime une adresse
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_adresse(self, acheteur_id, adresse_id):
        """Récupère l'adresse ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            AdresseAcheteur.objects.select_related('acheteur', 'created_by', 'updated_by'),
            id=adresse_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, adresse_id):
        """Récupère les détails d'une adresse spécifique"""
        adresse = self.get_adresse(acheteur_id, adresse_id)
        serializer = AdresseAcheteurSerializer(adresse)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, adresse_id):
        """Modifie une adresse existante"""
        adresse = self.get_adresse(acheteur_id, adresse_id)
        
        serializer = AdresseAcheteurUpdateSerializer(
            adresse, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            adresse = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_ADRESSE',
                object_id=adresse.id,
                object_type='AdresseAcheteur',
                details=f"Adresse modifiée pour l'acheteur {adresse.acheteur.nom}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Adresse modifiée avec succès",
                "data": AdresseAcheteurSerializer(adresse).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id, adresse_id):
        """Supprime une adresse"""
        adresse = self.get_adresse(acheteur_id, adresse_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_ADRESSE',
            object_id=adresse.id,
            object_type='AdresseAcheteur',
            details=f"Adresse supprimée pour l'acheteur {adresse.acheteur.nom}: {adresse.adresse[:50]}...",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        adresse.delete()
        return Response({
            "message": "Adresse supprimée avec succès"
        }, status=status.HTTP_200_OK)



















        
        
        
        
        
        
        
        
        
        


class ListAcheteurProduitServiceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        produits_services_list = ProduitService.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            produits_services_list = produits_services_list.filter(
                Q(produits__icontains=search_term) | Q(services__icontains=search_term)
            )

        paginator = Paginator(produits_services_list, 10)
        produits_services_page = paginator.get_page(page_number)
        serializer = ProduitServiceSerializer(produits_services_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": produits_services_page.has_next(),
                "previous": produits_services_page.has_previous(),
            }
        )

class SearchAcheteurProduitServiceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        produits_services_list = ProduitService.objects.filter(
            Q(acheteur_id=acheteur_id) & (Q(produits__icontains=search_term) | Q(services__icontains=search_term))
        ).order_by("-created_at")

        paginator = Paginator(produits_services_list, 10)
        page_number = request.query_params.get("page", 1)
        produits_services_page = paginator.get_page(page_number)
        serializer = ProduitServiceSerializer(produits_services_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": produits_services_page.has_next(),
                "previous": produits_services_page.has_previous(),
            }
        )

class AddAcheteurProduitServiceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddProduitServiceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurProduitServiceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, ps_id, *args, **kwargs):
        produit_service = ProduitService.objects.filter(id=ps_id, acheteur_id=acheteur_id).first()
        if not produit_service:
            return Response(
                {"detail": "Produit/Service non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetProduitServiceSerializer(produit_service)
        return Response(serializer.data)

    def put(self, request, acheteur_id, ps_id, *args, **kwargs):
        produit_service = ProduitService.objects.filter(id=ps_id, acheteur_id=acheteur_id).first()
        if not produit_service:
            return Response(
                {"detail": "Produit/Service non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditProduitServiceSerializer(produit_service, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurProduitServiceView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        produits_services = ProduitService.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not produits_services.exists():
            return Response(
                {"error": "Aucun Produit/Service trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = produits_services.delete()
        return Response(
            {"message": f"{count} Produits/Services supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
              
class AcheteurProduitServiceListOneView(APIView):
    """
    API pour gérer les produits et services d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des produits et services de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        produits_services = ProduitService.objects.filter(
            acheteur=acheteur
        ).order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            produits_services = produits_services.filter(
                Q(produits__icontains=search) |
                Q(services__icontains=search)
            )
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(produits_services, request)
        
        serializer = ProduitServiceOneSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request, acheteur_id):
        """Crée un nouvel enregistrement de produits et services pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)

        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddProduitServiceOneSerializer(data=data, context={'request': request})

        if not serializer.is_valid():
            print("[ProduitService POST] Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                produit_service = serializer.save()
        except Exception as e:
            import traceback
            print("[ProduitService POST] Save error:", str(e))
            traceback.print_exc()
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ActivityLog hors transaction pour ne pas annuler le save si ça échoue
        try:
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_PRODUIT_SERVICE',
                object_id=produit_service.id,
                object_type='ProduitService',
                details=f"Produits et services ajoutés pour l'acheteur {acheteur.nom} ({acheteur.code})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print("[ProduitService POST] ActivityLog error (non-blocking):", str(e))

        return Response({
            "message": "Produits et services ajoutés avec succès",
            "data": ProduitServiceOneSerializer(produit_service).data
        }, status=status.HTTP_201_CREATED)

class AcheteurProduitServiceDetailOneView(APIView):
    """
    API pour gérer un enregistrement spécifique de produits et services d'un acheteur
    Méthodes: GET (détail), PUT (modification), DELETE (suppression)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_produit_service(self, acheteur_id, produit_service_id):
        """Récupère l'enregistrement de produits et services ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            ProduitService.objects.select_related('acheteur'),
            id=produit_service_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, produit_service_id):
        """Récupère les détails d'un enregistrement spécifique"""
        produit_service = self.get_produit_service(acheteur_id, produit_service_id)
        serializer = ProduitServiceOneSerializer(produit_service)
        return Response(serializer.data)
    
    def put(self, request, acheteur_id, produit_service_id):
        """Modifie un enregistrement de produits et services existant"""
        produit_service = self.get_produit_service(acheteur_id, produit_service_id)

        serializer = EditProduitServiceOneSerializer(
            produit_service,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if not serializer.is_valid():
            print("[ProduitService PUT] Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                produit_service = serializer.save()
        except Exception as e:
            import traceback
            print("[ProduitService PUT] Save error:", str(e))
            traceback.print_exc()
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_PRODUIT_SERVICE',
                object_id=produit_service.id,
                object_type='ProduitService',
                details=f"Produits et services modifiés pour l'acheteur {produit_service.acheteur.nom}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print("[ProduitService PUT] ActivityLog error (non-blocking):", str(e))

        return Response({
            "message": "Produits et services modifiés avec succès",
            "data": ProduitServiceOneSerializer(produit_service).data
        })
    
    @transaction.atomic
    def delete(self, request, acheteur_id, produit_service_id):
        """Supprime un enregistrement de produits et services"""
        produit_service = self.get_produit_service(acheteur_id, produit_service_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_PRODUIT_SERVICE',
            object_id=produit_service.id,
            object_type='ProduitService',
            details=f"Produits et services supprimés pour l'acheteur {produit_service.acheteur.nom}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        produit_service.delete()
        return Response({
            "message": "Produits et services supprimés avec succès"
        }, status=status.HTTP_200_OK)
        
        
        
        
        
        
        


class ListAcheteurMarqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        marque_list = Marque.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            marque_list = marque_list.filter(
                Q(marques__icontains=search_term)
            )

        paginator = Paginator(marque_list, 10)
        marque_page = paginator.get_page(page_number)
        serializer = MarqueSerializer(marque_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": marque_page.has_next(),
                "previous": marque_page.has_previous(),
            }
        )

class SearchAcheteurMarqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        marque_list = Marque.objects.filter(
            Q(acheteur_id=acheteur_id) & Q(marques__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(marque_list, 10)
        page_number = request.query_params.get("page", 1)
        marque_page = paginator.get_page(page_number)
        serializer = MarqueSerializer(marque_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": marque_page.has_next(),
                "previous": marque_page.has_previous(),
            }
        )

class AddAcheteurMarqueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddMarqueSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurMarqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, marque_id, *args, **kwargs):
        marque = Marque.objects.filter(id=marque_id, acheteur_id=acheteur_id).first()
        if not marque:
            return Response(
                {"detail": "Marque non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetMarqueSerializer(marque)
        return Response(serializer.data)

    def put(self, request, acheteur_id, marque_id, *args, **kwargs):
        marque = Marque.objects.filter(id=marque_id, acheteur_id=acheteur_id).first()
        if not marque:
            return Response(
                {"detail": "Marque non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditMarqueSerializer(marque, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurMarqueView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        marques = Marque.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not marques.exists():
            return Response(
                {"error": "Aucune marque trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = marques.delete()
        return Response(
            {"message": f"{count} marques supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        
class AcheteurMarqueListOneView(APIView):
    """
    API pour gérer les marques d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des marques de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        marques = Marque.objects.filter(
            acheteur=acheteur
        ).order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            marques = marques.filter(
                Q(marques__icontains=search)
            )
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(marques, request)
        
        serializer = MarqueOneSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée un nouvel enregistrement de marques pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        # Passer le contexte avec la requête au serializer
        serializer = AddMarqueOneSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            # Le serializer gère maintenant created_by et updated_by
            marque = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_MARQUE',
                object_id=marque.id,
                object_type='Marque',
                details=f"Marques ajoutées pour l'acheteur {acheteur.nom} ({acheteur.code})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Marques ajoutées avec succès",
                "data": MarqueOneSerializer(marque).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurMarqueDetailOneView(APIView):
    """
    API pour gérer un enregistrement spécifique de marques d'un acheteur
    Méthodes: GET (détail), PUT (modification), DELETE (suppression)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_marque(self, acheteur_id, marque_id):
        """Récupère l'enregistrement de marques ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            Marque.objects.select_related('acheteur'),
            id=marque_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, marque_id):
        """Récupère les détails d'un enregistrement spécifique"""
        marque = self.get_marque(acheteur_id, marque_id)
        serializer = MarqueOneSerializer(marque)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, marque_id):
        """Modifie un enregistrement de marques existant"""
        marque = self.get_marque(acheteur_id, marque_id)
        
        # Passer le contexte avec la requête pour que le serializer puisse accéder à request.user
        serializer = EditMarqueOneSerializer(
            marque, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Le serializer gère maintenant updated_by via sa méthode update()
            marque = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_MARQUE',
                object_id=marque.id,
                object_type='Marque',
                details=f"Marques modifiées pour l'acheteur {marque.acheteur.nom}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Marques modifiées avec succès",
                "data": MarqueOneSerializer(marque).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id, marque_id):
        """Supprime un enregistrement de marques"""
        marque = self.get_marque(acheteur_id, marque_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_MARQUE',
            object_id=marque.id,
            object_type='Marque',
            details=f"Marques supprimées pour l'acheteur {marque.acheteur.nom}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        marque.delete()
        return Response({
            "message": "Marques supprimées avec succès"
        }, status=status.HTTP_200_OK)
        
        
        
        
        






class ListAcheteurProcedureCollectiveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        procedure_list = ProcedureCollective.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            procedure_list = procedure_list.filter(
                Q(type_procedure__icontains=search_term) | Q(description__icontains=search_term)
            )

        paginator = Paginator(procedure_list, 10)
        procedure_page = paginator.get_page(page_number)
        serializer = ProcedureCollectiveSerializer(procedure_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": procedure_page.has_next(),
                "previous": procedure_page.has_previous(),
            }
        )

class SearchAcheteurProcedureCollectiveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        procedure_list = ProcedureCollective.objects.filter(
            Q(acheteur_id=acheteur_id) & (Q(type_procedure__icontains=search_term) | Q(description__icontains=search_term))
        ).order_by("-created_at")

        paginator = Paginator(procedure_list, 10)
        page_number = request.query_params.get("page", 1)
        procedure_page = paginator.get_page(page_number)
        serializer = ProcedureCollectiveSerializer(procedure_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": procedure_page.has_next(),
                "previous": procedure_page.has_previous(),
            }
        )

class AddAcheteurProcedureCollectiveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddProcedureCollectiveSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurProcedureCollectiveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, pc_id, *args, **kwargs):
        procedure_collective = ProcedureCollective.objects.filter(id=pc_id, acheteur_id=acheteur_id).first()
        if not procedure_collective:
            return Response(
                {"detail": "Procédure collective non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetProcedureCollectiveSerializer(procedure_collective)
        return Response(serializer.data)

    def put(self, request, acheteur_id, pc_id, *args, **kwargs):
        procedure_collective = ProcedureCollective.objects.filter(id=pc_id, acheteur_id=acheteur_id).first()
        if not procedure_collective:
            return Response(
                {"detail": "Procédure collective non trouvée."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditProcedureCollectiveSerializer(procedure_collective, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurProcedureCollectiveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        procedures_collectives = ProcedureCollective.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not procedures_collectives.exists():
            return Response(
                {"error": "Aucune procédure collective trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = procedures_collectives.delete()
        return Response(
            {"message": f"{count} procédures collectives supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
              
class AcheteurProcedureCollectiveListOneView(APIView):
    """
    API pour gérer les procédures collectives d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des procédures collectives de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        procedures = ProcedureCollective.objects.filter(
            acheteur=acheteur
        ).order_by('-date_ouverture', '-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            procedures = procedures.filter(
                Q(type_procedure__icontains=search) |
                Q(description__icontains=search) |
                Q(tribunal__icontains=search) |
                Q(numero_dossier__icontains=search) |
                Q(secteur_activite__icontains=search)
            )
        
        # Filtrer par statut
        statut = request.query_params.get('statut', '')
        if statut == 'active':
            procedures = procedures.filter(date_cloture__isnull=True)
        elif statut == 'closed':
            procedures = procedures.filter(date_cloture__isnull=False)
        
        # Filtrer par type
        type_procedure = request.query_params.get('type', '')
        if type_procedure:
            procedures = procedures.filter(type_procedure__icontains=type_procedure)
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(procedures, request)
        
        serializer = ProcedureCollectiveOneSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée une nouvelle procédure collective pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = AddProcedureCollectiveOneSerializer(data=data)
        
        if serializer.is_valid():
            # Sauvegarder la procédure
            procedure = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_PROCEDURE_COLLECTIVE',
                object_id=procedure.id,
                object_type='ProcedureCollective',
                details=f"Procédure collective créée pour l'acheteur {acheteur.nom} ({acheteur.code}): {procedure.type_procedure}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Procédure collective créée avec succès",
                "data": ProcedureCollectiveOneSerializer(procedure).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurProcedureCollectiveDetailOneView(APIView):
    """
    API pour gérer une procédure collective spécifique d'un acheteur
    Méthodes: GET (détail), PUT (modification), DELETE (suppression)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_procedure(self, acheteur_id, procedure_id):
        """Récupère la procédure collective ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            ProcedureCollective.objects,
            id=procedure_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, procedure_id):
        """Récupère les détails d'une procédure collective spécifique"""
        procedure = self.get_procedure(acheteur_id, procedure_id)
        serializer = ProcedureCollectiveOneSerializer(procedure)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, procedure_id):
        """Modifie une procédure collective existante"""
        procedure = self.get_procedure(acheteur_id, procedure_id)
        
        serializer = EditProcedureCollectiveOneSerializer(
            procedure, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            procedure = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_PROCEDURE_COLLECTIVE',
                object_id=procedure.id,
                object_type='ProcedureCollective',
                details=f"Procédure collective modifiée pour l'acheteur {procedure.acheteur.nom}: {procedure.type_procedure}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Procédure collective modifiée avec succès",
                "data": ProcedureCollectiveOneSerializer(procedure).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id, procedure_id):
        """Supprime une procédure collective"""
        procedure = self.get_procedure(acheteur_id, procedure_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_PROCEDURE_COLLECTIVE',
            object_id=procedure.id,
            object_type='ProcedureCollective',
            details=f"Procédure collective supprimée pour l'acheteur {procedure.acheteur.nom}: {procedure.type_procedure}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        procedure.delete()
        return Response({
            "message": "Procédure collective supprimée avec succès"
        }, status=status.HTTP_200_OK)














class ListAcheteurDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        document_list = Document.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            document_list = document_list.filter(
                Q(titre__icontains=search_term) | Q(description__icontains=search_term)
            )

        paginator = Paginator(document_list, 10)
        document_page = paginator.get_page(page_number)
        serializer = DocumentSerializer(document_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": document_page.has_next(),
                "previous": document_page.has_previous(),
            }
        )

class SearchAcheteurDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document_list = Document.objects.filter(
            Q(acheteur_id=acheteur_id) & (Q(titre__icontains=search_term) | Q(description__icontains=search_term))
        ).order_by("-created_at")

        paginator = Paginator(document_list, 10)
        page_number = request.query_params.get("page", 1)
        document_page = paginator.get_page(page_number)
        serializer = DocumentSerializer(document_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": document_page.has_next(),
                "previous": document_page.has_previous(),
            }
        )

class AddAcheteurDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddDocumentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, document_id, *args, **kwargs):
        document = Document.objects.filter(id=document_id, acheteur_id=acheteur_id).first()
        if not document:
            return Response(
                {"detail": "Document non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetDocumentSerializer(document)
        return Response(serializer.data)

    def put(self, request, acheteur_id, document_id, *args, **kwargs):
        document = Document.objects.filter(id=document_id, acheteur_id=acheteur_id).first()
        if not document:
            return Response(
                {"detail": "Document non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditDocumentSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurDocumentView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        documents = Document.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not documents.exists():
            return Response(
                {"error": "Aucun document trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = documents.delete()
        return Response(
            {"message": f"{count} documents supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
              
class AcheteurDocumentListOneView(APIView):
    """
    API pour gérer les documents d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des documents de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        documents = Document.objects.filter(
            acheteur=acheteur
        ).order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            documents = documents.filter(
                Q(titre__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(documents, request)
        
        serializer = DocumentOneSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée un nouveau document pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        # Make request.data mutable
        if hasattr(request.data, '_mutable'):
            request.data._mutable = True
        
        # Add the acheteur_id directly to request.data
        request.data['acheteur'] = acheteur_id
        
        serializer = AddDocumentOneSerializer(data=request.data)
        
        if serializer.is_valid():
            # Sauvegarder le document
            document = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_DOCUMENT',
                object_id=document.id,
                object_type='Document',
                details=f"Document ajouté pour l'acheteur {acheteur.nom} ({acheteur.code}): {document.titre}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Document ajouté avec succès",
                "data": DocumentOneSerializer(document).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurDocumentDetailOneView(APIView):
    """
    API pour gérer un document spécifique d'un acheteur
    Méthodes: GET (détail), PUT (modification), DELETE (suppression)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_document(self, acheteur_id, document_id):
        """Récupère le document ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            Document.objects,
            id=document_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, document_id):
        """Récupère les détails d'un document spécifique"""
        document = self.get_document(acheteur_id, document_id)
        serializer = DocumentOneSerializer(document)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, document_id):
        """Modifie un document existant (titre et description seulement)"""
        document = self.get_document(acheteur_id, document_id)
        
        serializer = EditDocumentOneSerializer(
            document, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            document = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_DOCUMENT',
                object_id=document.id,
                object_type='Document',
                details=f"Document modifié pour l'acheteur {document.acheteur.nom}: {document.titre}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Document modifié avec succès",
                "data": DocumentOneSerializer(document).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id, document_id):
        """Supprime un document"""
        document = self.get_document(acheteur_id, document_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_DOCUMENT',
            object_id=document.id,
            object_type='Document',
            details=f"Document supprimé pour l'acheteur {document.acheteur.nom}: {document.titre}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Supprimer le fichier physique
        if document.fichier and hasattr(document.fichier, 'delete'):
            document.fichier.delete(save=False)
        
        document.delete()
        return Response({
            "message": "Document supprimé avec succès"
        }, status=status.HTTP_200_OK)
        
        
        
        
        
        
        
        
        
        
        
        
        
        


class ListAcheteurPortableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        portable_list = PortableAcheteur.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            portable_list = portable_list.filter(
                Q(portable__icontains=search_term)
            )

        paginator = Paginator(portable_list, 10)
        portable_page = paginator.get_page(page_number)
        serializer = PortableAcheteurSerializer(portable_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": portable_page.has_next(),
                "previous": portable_page.has_previous(),
            }
        )

class SearchAcheteurPortableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        portable_list = PortableAcheteur.objects.filter(
            Q(acheteur_id=acheteur_id) & Q(portable__icontains=search_term)
        ).order_by("-created_at")

        paginator = Paginator(portable_list, 10)
        page_number = request.query_params.get("page", 1)
        portable_page = paginator.get_page(page_number)
        serializer = PortableAcheteurSerializer(portable_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": portable_page.has_next(),
                "previous": portable_page.has_previous(),
            }
        )

class AddAcheteurPortableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddPortableAcheteurSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurPortableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, portable_id, *args, **kwargs):
        portable = PortableAcheteur.objects.filter(id=portable_id, acheteur_id=acheteur_id).first()
        if not portable:
            return Response(
                {"detail": "Portable non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetPortableAcheteurSerializer(portable)
        return Response(serializer.data)

    def put(self, request, acheteur_id, portable_id, *args, **kwargs):
        portable = PortableAcheteur.objects.filter(id=portable_id, acheteur_id=acheteur_id).first()
        if not portable:
            return Response(
                {"detail": "Portable non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditPortableAcheteurSerializer(portable, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurPortableView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        portables = PortableAcheteur.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not portables.exists():
            return Response(
                {"error": "Aucun portable trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = portables.delete()
        return Response(
            {"message": f"{count} portables supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
             
class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class AcheteurPortableListView(APIView):
    """
    API pour gérer les numéros de portable d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des portables de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        portables = PortableAcheteur.objects.filter(
            acheteur=acheteur
        ).order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            portables = portables.filter(portable__icontains=search)
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(portables, request)
        
        serializer = PortableAcheteurSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée un nouveau numéro de portable pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = AddPortableAcheteurSerializer(data=data)
        
        if serializer.is_valid():
            # Sauvegarder en passant created_by comme argument supplémentaire
            portable = serializer.save(
                created_by=request.user,
                updated_by=request.user  # Si nécessaire
            )
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_PORTABLE',
                object_id=portable.id,
                object_type='PortableAcheteur',
                details=f"Numéro de portable ajouté pour l'acheteur {acheteur.nom} ({acheteur.code}): {portable.portable}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Numéro de portable ajouté avec succès",
                "data": PortableAcheteurSerializer(portable).data
            }, status=status.HTTP_201_CREATED)
        
        print(f"Erreurs serializer: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurPortableDetailView(APIView):
    """
    API pour gérer un numéro de portable spécifique
    Méthodes: GET (détail), PUT (modification), DELETE (suppression)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_portable(self, acheteur_id, portable_id):
        """Récupère le portable ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(PortableAcheteur, id=portable_id, acheteur=acheteur)
    
    def get(self, request, acheteur_id, portable_id):
        """Récupère les détails d'un portable spécifique"""
        portable = self.get_portable(acheteur_id, portable_id)
        serializer = PortableAcheteurSerializer(portable)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, portable_id):
        """Modifie un numéro de portable existant"""
        portable = self.get_portable(acheteur_id, portable_id)
        
        data = request.data.copy()
        data["updated_by"] = request.user.id
        
        serializer = EditPortableAcheteurSerializer(
            portable, data=data, partial=True
        )
        
        if serializer.is_valid():
            portable = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_PORTABLE',
                object_id=portable.id,
                object_type='PortableAcheteur',
                details=f"Numéro de portable modifié pour l'acheteur {portable.acheteur.nom}: {portable.portable}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Numéro de portable modifié avec succès",
                "data": PortableAcheteurSerializer(portable).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id, portable_id):
        """Supprime un numéro de portable"""
        portable = self.get_portable(acheteur_id, portable_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_PORTABLE',
            object_id=portable.id,
            object_type='PortableAcheteur',
            details=f"Numéro de portable supprimé pour l'acheteur {portable.acheteur.nom}: {portable.portable}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        portable.delete()
        return Response({
            "message": "Numéro de portable supprimé avec succès"
        }, status=status.HTTP_200_OK)
        
        
 
 
        
        
        
        
        

class ListAcheteurRegistreCommerceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")

        registre_list = RegistreCommerce.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by("-created_at")

        if search_term:
            registre_list = registre_list.filter(
                Q(numero__icontains=search_term)
                | Q(description__icontains=search_term)
            )

        paginator = Paginator(registre_list, 10)
        registre_page = paginator.get_page(page_number)
        serializer = RegistreCommerceSerializer(registre_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": registre_page.has_next(),
                "previous": registre_page.has_previous(),
            }
        )

class SearchAcheteurRegistreCommerceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registre_list = RegistreCommerce.objects.filter(
            Q(acheteur_id=acheteur_id)
            & (
                Q(numero__icontains=search_term)
                | Q(description__icontains=search_term)
            )
        ).order_by("-created_at")

        paginator = Paginator(registre_list, 10)
        page_number = request.query_params.get("page", 1)
        registre_page = paginator.get_page(page_number)
        serializer = RegistreCommerceSerializer(registre_page, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "next": registre_page.has_next(),
                "previous": registre_page.has_previous(),
            }
        )

class AddAcheteurRegistreCommerceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id

        serializer = AddRegistreCommerceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurRegistreCommerceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, rc_id, *args, **kwargs):
        registre = RegistreCommerce.objects.filter(id=rc_id, acheteur_id=acheteur_id).first()
        if not registre:
            return Response(
                {"detail": "Registre de commerce non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = GetRegistreCommerceSerializer(registre)
        return Response(serializer.data)

    def put(self, request, acheteur_id, rc_id, *args, **kwargs):
        registre = RegistreCommerce.objects.filter(id=rc_id, acheteur_id=acheteur_id).first()
        if not registre:
            return Response(
                {"detail": "Registre de commerce non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EditRegistreCommerceSerializer(registre, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurRegistreCommerceView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registres = RegistreCommerce.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not registres.exists():
            return Response(
                {"error": "Aucun registre de commerce trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        count, _ = registres.delete()
        return Response(
            {"message": f"{count} registres de commerce supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
        
class AcheteurRegistreCommerceListOneView(APIView):
    """
    API pour gérer les registres de commerce d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des registres de commerce de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        registres = RegistreCommerce.objects.filter(
            acheteur=acheteur
        ).order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            registres = registres.filter(
                Q(numero__icontains=search) |
                Q(date_inscription__icontains=search)
            )
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(registres, request)
        
        serializer = RegistreCommerceOneSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée un nouveau registre de commerce pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        # Passer le contexte avec la requête au serializer
        serializer = AddRegistreCommerceOneSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            # Le serializer gère maintenant created_by et updated_by
            registre = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_REGISTRE_COMMERCE',
                object_id=registre.id,
                object_type='RegistreCommerce',
                details=f"Registre de commerce ajouté pour l'acheteur {acheteur.nom} ({acheteur.code}): {registre.numero}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Registre de commerce ajouté avec succès",
                "data": RegistreCommerceOneSerializer(registre).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurRegistreCommerceDetailOneView(APIView):
    """
    API pour gérer un registre de commerce spécifique d'un acheteur
    Méthodes: GET (détail), PUT (modification), DELETE (suppression)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_registre(self, acheteur_id, registre_id):
        """Récupère le registre de commerce ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            RegistreCommerce.objects.select_related('acheteur'),
            id=registre_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, registre_id):
        """Récupère les détails d'un registre de commerce spécifique"""
        registre = self.get_registre(acheteur_id, registre_id)
        serializer = RegistreCommerceOneSerializer(registre)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, registre_id):
        """Modifie un registre de commerce existant"""
        print(f"DEBUG - Requête PUT reçue")
        print(f"DEBUG - acheteur_id: {acheteur_id}, registre_id: {registre_id}")
        print(f"DEBUG - request.data: {request.data}")
        print(f"DEBUG - request.user: {request.user}")
        
        registre = self.get_registre(acheteur_id, registre_id)
        print(f"DEBUG - registre trouvé: {registre.numero}, date: {registre.date_inscription}")
        
        serializer = EditRegistreCommerceOneSerializer(
            registre, 
            data=request.data, 
            partial=True
        )
        
        print(f"DEBUG - Serializer créé")
        
        if serializer.is_valid():
            print(f"DEBUG - Serializer valide")
            registre = serializer.save()
            print(f"DEBUG - Registre sauvegardé: {registre.numero}")
            
            # Mettre à jour manuellement updated_by
            registre.updated_by = request.user
            registre.save()
            print(f"DEBUG - Registre mis à jour avec updated_by: {registre.updated_by}")
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_REGISTRE_COMMERCE',
                object_id=registre.id,
                object_type='RegistreCommerce',
                details=f"Registre de commerce modifié pour l'acheteur {registre.acheteur.nom}: {registre.numero}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Registre de commerce modifié avec succès",
                "data": RegistreCommerceOneSerializer(registre).data
            })
        else:
            print(f"DEBUG - Serializer non valide")
            print(f"DEBUG - Erreurs: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id, registre_id):
        """Supprime un registre de commerce"""
        registre = self.get_registre(acheteur_id, registre_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_REGISTRE_COMMERCE',
            object_id=registre.id,
            object_type='RegistreCommerce',
            details=f"Registre de commerce supprimé pour l'acheteur {registre.acheteur.nom}: {registre.numero}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        registre.delete()
        return Response({
            "message": "Registre de commerce supprimé avec succès"
        }, status=status.HTTP_200_OK)


class AcheteurIdentifiantFiscalListOneView(APIView):
    """
    API identifiants fiscaux : un seul enregistrement par acheteur.
    GET  → retourne l'enregistrement (ou null)
    POST → crée l'enregistrement
    PUT  → met à jour l'enregistrement
    """
    permission_classes = [IsAuthenticated]

    def get_acheteur(self, acheteur_id):
        return get_object_or_404(Acheteur, id=acheteur_id)

    def get(self, request, acheteur_id):
        acheteur = self.get_acheteur(acheteur_id)
        try:
            obj = IdentifiantFiscal.objects.get(acheteur=acheteur)
            return Response(IdentifiantFiscalOneSerializer(obj).data)
        except IdentifiantFiscal.DoesNotExist:
            return Response(None)

    @transaction.atomic
    def post(self, request, acheteur_id):
        acheteur = self.get_acheteur(acheteur_id)
        # Upsert : si l'enregistrement existe déjà, on met à jour
        try:
            obj = IdentifiantFiscal.objects.get(acheteur=acheteur)
            serializer = SaveIdentifiantFiscalOneSerializer(obj, data=request.data, partial=True)
        except IdentifiantFiscal.DoesNotExist:
            data = request.data.copy()
            data['acheteur'] = acheteur_id
            serializer = SaveIdentifiantFiscalOneSerializer(data=data)

        if serializer.is_valid():
            obj = serializer.save()
            obj.updated_by = request.user
            if not obj.created_by:
                obj.created_by = request.user
            obj.save()
            ActivityLog.objects.create(
                user=request.user,
                action_type='SAVE_IDENTIFIANT_FISCAL',
                object_id=obj.id,
                object_type='IdentifiantFiscal',
                details=f"Identifiants fiscaux enregistrés pour {acheteur.nom}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            return Response({
                "message": "Identifiants fiscaux enregistrés avec succès",
                "data": IdentifiantFiscalOneSerializer(obj).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AcheteurIdentifiantFiscalDetailOneView(APIView):
    """Alias PUT vers la même logique upsert."""
    permission_classes = [IsAuthenticated]

    def put(self, request, acheteur_id, identifiant_id):
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        obj = get_object_or_404(IdentifiantFiscal, id=identifiant_id, acheteur=acheteur)
        serializer = SaveIdentifiantFiscalOneSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            obj = serializer.save()
            obj.updated_by = request.user
            obj.save()
            return Response({
                "message": "Identifiants fiscaux mis à jour",
                "data": IdentifiantFiscalOneSerializer(obj).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListAcheteurMarqueView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        marques = Marque.objects.filter(acheteur_id=acheteur_id).order_by("-updated_at")
        paginator = Paginator(marques, 10)
        marque_page = paginator.get_page(page_number)
        serializer = ListMarqueSerializer(marque_page, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": marque_page.has_next(),
            "previous": marque_page.has_previous(),
        })

class SearchAcheteurMarqueView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        marques = Marque.objects.filter(
            Q(acheteur_id=acheteur_id) & Q(marques__icontains=search_term)
        ).order_by("-updated_at")
        paginator = Paginator(marques, 10)
        page_number = request.query_params.get("page", 1)
        marque_page = paginator.get_page(page_number)
        serializer = SearchMarqueSerializer(marque_page, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": marque_page.has_next(),
            "previous": marque_page.has_previous(),
        })

class AddAcheteurMarqueView(APIView):
    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        serializer = AddMarqueSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DetailAcheteurMarqueView(APIView):
    def get(self, request, acheteur_id, marque_id, *args, **kwargs):
        marque = Marque.objects.filter(id=marque_id, acheteur_id=acheteur_id).first()
        if not marque:
            return Response(
                {"detail": "Marque non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DetailMarqueSerializer(marque)
        return Response(serializer.data)

class EditAcheteurMarqueView(APIView):
    def put(self, request, acheteur_id, marque_id, *args, **kwargs):
        marque = Marque.objects.filter(id=marque_id, acheteur_id=acheteur_id).first()
        if not marque:
            return Response(
                {"detail": "Marque non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = EditMarqueSerializer(marque, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurMarqueView(APIView):
    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        marques = Marque.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not marques.exists():
            return Response(
                {"error": "Aucune marque trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )
        count, _ = marques.delete()
        return Response(
            {"message": f"{count} marques supprimées avec succès."},
            status=status.HTTP_200_OK,
        )






class ListAcheteurProduitServiceView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        produits_services = ProduitService.objects.filter(acheteur_id=acheteur_id).order_by("-updated_at")
        paginator = Paginator(produits_services, 10)
        produit_service_page = paginator.get_page(page_number)
        serializer = ListProduitServiceSerializer(produit_service_page, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": produit_service_page.has_next(),
            "previous": produit_service_page.has_previous(),
        })

class SearchAcheteurProduitServiceView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        produits_services = ProduitService.objects.filter(
            Q(acheteur_id=acheteur_id) &
            (Q(produits__icontains=search_term) | Q(services__icontains=search_term))
        ).order_by("-updated_at")
        paginator = Paginator(produits_services, 10)
        page_number = request.query_params.get("page", 1)
        produit_service_page = paginator.get_page(page_number)
        serializer = SearchProduitServiceSerializer(produit_service_page, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": produit_service_page.has_next(),
            "previous": produit_service_page.has_previous(),
        })

class AddAcheteurProduitServiceView(APIView):
    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        serializer = AddProduitServiceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DetailAcheteurProduitServiceView(APIView):
    def get(self, request, acheteur_id, produit_service_id, *args, **kwargs):
        produit_service = ProduitService.objects.filter(id=produit_service_id, acheteur_id=acheteur_id).first()
        if not produit_service:
            return Response(
                {"detail": "Produit/Service non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DetailProduitServiceSerializer(produit_service)
        return Response(serializer.data)

class EditAcheteurProduitServiceView(APIView):
    def put(self, request, acheteur_id, produit_service_id, *args, **kwargs):
        produit_service = ProduitService.objects.filter(id=produit_service_id, acheteur_id=acheteur_id).first()
        if not produit_service:
            return Response(
                {"detail": "Produit/Service non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = EditProduitServiceSerializer(
            produit_service, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurProduitServiceView(APIView):
    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        produits_services = ProduitService.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not produits_services.exists():
            return Response(
                {"error": "Aucun produit/service trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )
        count, _ = produits_services.delete()
        return Response(
            {"message": f"{count} produits/services supprimés avec succès."},
            status=status.HTTP_200_OK,
        )










class ListAcheteurPortableView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        portables = PortableAcheteur.objects.filter(acheteur_id=acheteur_id).order_by("-updated_at")
        serializer = ListPortableAcheteurSerializer(portables, many=True)
        return Response({"results": serializer.data})

class SearchAcheteurPortableView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        portables = PortableAcheteur.objects.filter(
            Q(acheteur_id=acheteur_id) & Q(portable__icontains=search_term)
        ).order_by("-updated_at")
        serializer = ListPortableAcheteurSerializer(portables, many=True)
        return Response({"results": serializer.data})

class AddAcheteurPortableView(APIView):
    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        data["created_by"] = request.user.id
        data["updated_by"] = request.user.id
        serializer = AddPortableAcheteurSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DetailAcheteurPortableView(APIView):
    def get(self, request, acheteur_id, portable_id, *args, **kwargs):
        portable = PortableAcheteur.objects.filter(id=portable_id, acheteur_id=acheteur_id).first()
        if not portable:
            return Response(
                {"detail": "Numéro de portable non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DetailPortableAcheteurSerializer(portable)
        return Response(serializer.data)

class EditAcheteurPortableView(APIView):
    def put(self, request, acheteur_id, portable_id, *args, **kwargs):
        portable = PortableAcheteur.objects.filter(id=portable_id, acheteur_id=acheteur_id).first()
        if not portable:
            return Response(
                {"detail": "Numéro de portable non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )
        data = request.data.copy()
        data["updated_by"] = request.user.id
        serializer = EditPortableAcheteurSerializer(portable, data=data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurPortableView(APIView):
    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        portables = PortableAcheteur.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not portables.exists():
            return Response(
                {"error": "Aucun numéro de portable trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )
        count, _ = portables.delete()
        return Response(
            {"message": f"{count} numéros de portable supprimés avec succès."},
            status=status.HTTP_200_OK,
        )












class ListAcheteurTelephoneView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        telephones = TelephoneAcheteur.objects.filter(acheteur_id=acheteur_id).order_by("-updated_at")
        serializer = ListTelephoneAcheteurSerializer(telephones, many=True)
        return Response({"results": serializer.data})

class SearchAcheteurTelephoneView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        telephones = TelephoneAcheteur.objects.filter(
            Q(acheteur_id=acheteur_id) & Q(telephone__icontains=search_term)
        ).order_by("-updated_at")
        serializer = ListTelephoneAcheteurSerializer(telephones, many=True)
        return Response({"results": serializer.data})

class AddAcheteurTelephoneView(APIView):
    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        data["created_by"] = request.user.id
        data["updated_by"] = request.user.id
        serializer = AddTelephoneAcheteurSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DetailAcheteurTelephoneView(APIView):
    def get(self, request, acheteur_id, telephone_id, *args, **kwargs):
        telephone = TelephoneAcheteur.objects.filter(id=telephone_id, acheteur_id=acheteur_id).first()
        if not telephone:
            return Response(
                {"detail": "Numéro de téléphone non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DetailTelephoneAcheteurSerializer(telephone)
        return Response(serializer.data)

class EditAcheteurTelephoneView(APIView):
    def put(self, request, acheteur_id, telephone_id, *args, **kwargs):
        telephone = TelephoneAcheteur.objects.filter(id=telephone_id, acheteur_id=acheteur_id).first()
        if not telephone:
            return Response(
                {"detail": "Numéro de téléphone non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )
        data = request.data.copy()
        data["updated_by"] = request.user.id
        serializer = EditTelephoneAcheteurSerializer(telephone, data=data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurTelephoneView(APIView):
    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        telephones = TelephoneAcheteur.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not telephones.exists():
            return Response(
                {"error": "Aucun numéro de téléphone trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )
        count, _ = telephones.delete()
        return Response(
            {"message": f"{count} numéros de téléphone supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
        
class AcheteurTelephoneListView(APIView):
    """
    API pour gérer les numéros de téléphone fixe d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des téléphones de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        telephones = TelephoneAcheteur.objects.filter(
            acheteur=acheteur
        ).order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            telephones = telephones.filter(telephone__icontains=search)
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(telephones, request)
        
        serializer = TelephoneAcheteurSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée un nouveau numéro de téléphone pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = AddTelephoneAcheteurSerializer(data=data)
        
        if serializer.is_valid():
            # Sauvegarder en passant created_by comme argument supplémentaire
            telephone = serializer.save(
                created_by=request.user,
                updated_by=request.user
            )
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_TELEPHONE',
                object_id=telephone.id,
                object_type='TelephoneAcheteur',
                details=f"Numéro de téléphone fixe ajouté pour l'acheteur {acheteur.nom} ({acheteur.code}): {telephone.telephone}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Numéro de téléphone fixe ajouté avec succès",
                "data": TelephoneAcheteurSerializer(telephone).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurTelephoneDetailView(APIView):
    """
    API pour gérer un numéro de téléphone fixe spécifique
    Méthodes: GET (détail), PUT (modification), DELETE (suppression)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_telephone(self, acheteur_id, telephone_id):
        """Récupère le téléphone ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(TelephoneAcheteur, id=telephone_id, acheteur=acheteur)
    
    def get(self, request, acheteur_id, telephone_id):
        """Récupère les détails d'un téléphone spécifique"""
        telephone = self.get_telephone(acheteur_id, telephone_id)
        serializer = TelephoneAcheteurSerializer(telephone)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, telephone_id):
        """Modifie un numéro de téléphone existant"""
        telephone = self.get_telephone(acheteur_id, telephone_id)
        
        data = request.data.copy()
        data["updated_by"] = request.user.id
        
        serializer = EditTelephoneAcheteurSerializer(
            telephone, data=data, partial=True
        )
        
        if serializer.is_valid():
            telephone = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_TELEPHONE',
                object_id=telephone.id,
                object_type='TelephoneAcheteur',
                details=f"Numéro de téléphone fixe modifié pour l'acheteur {telephone.acheteur.nom}: {telephone.telephone}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Numéro de téléphone fixe modifié avec succès",
                "data": TelephoneAcheteurSerializer(telephone).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id, telephone_id):
        """Supprime un numéro de téléphone"""
        telephone = self.get_telephone(acheteur_id, telephone_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_TELEPHONE',
            object_id=telephone.id,
            object_type='TelephoneAcheteur',
            details=f"Numéro de téléphone fixe supprimé pour l'acheteur {telephone.acheteur.nom}: {telephone.telephone}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        telephone.delete()
        return Response({
            "message": "Numéro de téléphone fixe supprimé avec succès"
        }, status=status.HTTP_200_OK)











class ListAcheteurEmailView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        emails = EmailAcheteur.objects.filter(acheteur_id=acheteur_id).order_by("-updated_at")
        serializer = ListEmailAcheteurSerializer(emails, many=True)
        return Response({"results": serializer.data})

class SearchAcheteurEmailView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        emails = EmailAcheteur.objects.filter(
            Q(acheteur_id=acheteur_id) & Q(email__icontains=search_term)
        ).order_by("-updated_at")
        serializer = ListEmailAcheteurSerializer(emails, many=True)
        return Response({"results": serializer.data})

class AddAcheteurEmailView(APIView):
    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        data["created_by"] = request.user.id
        data["updated_by"] = request.user.id
        serializer = AddEmailAcheteurSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DetailAcheteurEmailView(APIView):
    def get(self, request, acheteur_id, email_id, *args, **kwargs):
        email = EmailAcheteur.objects.filter(id=email_id, acheteur_id=acheteur_id).first()
        if not email:
            return Response(
                {"detail": "Adresse email non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DetailEmailAcheteurSerializer(email)
        return Response(serializer.data)

class EditAcheteurEmailView(APIView):
    def put(self, request, acheteur_id, email_id, *args, **kwargs):
        email = EmailAcheteur.objects.filter(id=email_id, acheteur_id=acheteur_id).first()
        if not email:
            return Response(
                {"detail": "Adresse email non trouvée."},
                status=status.HTTP_404_NOT_FOUND,
            )
        data = request.data.copy()
        data["updated_by"] = request.user.id
        serializer = EditEmailAcheteurSerializer(email, data=data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurEmailView(APIView):
    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        emails = EmailAcheteur.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not emails.exists():
            return Response(
                {"error": "Aucune adresse email trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )
        count, _ = emails.delete()
        return Response(
            {"message": f"{count} adresses email supprimées avec succès."},
            status=status.HTTP_200_OK,
        )
        
class AcheteurEmailListView(APIView):
    """
    API pour gérer les adresses email d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des emails de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        emails = EmailAcheteur.objects.filter(
            acheteur=acheteur
        ).order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            emails = emails.filter(email__icontains=search)
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(emails, request)
        
        serializer = EmailAcheteurSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée une nouvelle adresse email pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = AddEmailAcheteurSerializer(data=data)
        
        if serializer.is_valid():
            # Sauvegarder en passant created_by comme argument supplémentaire
            email = serializer.save(
                created_by=request.user,
                updated_by=request.user
            )
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_EMAIL',
                object_id=email.id,
                object_type='EmailAcheteur',
                details=f"Adresse email ajoutée pour l'acheteur {acheteur.nom} ({acheteur.code}): {email.email}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Adresse email ajoutée avec succès",
                "data": EmailAcheteurSerializer(email).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurEmailDetailView(APIView):
    """
    API pour gérer une adresse email spécifique
    Méthodes: GET (détail), PUT (modification), DELETE (suppression)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_email(self, acheteur_id, email_id):
        """Récupère l'email ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(EmailAcheteur, id=email_id, acheteur=acheteur)
    
    def get(self, request, acheteur_id, email_id):
        """Récupère les détails d'un email spécifique"""
        email = self.get_email(acheteur_id, email_id)
        serializer = EmailAcheteurSerializer(email)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, email_id):
        """Modifie une adresse email existante"""
        email = self.get_email(acheteur_id, email_id)
        
        data = request.data.copy()
        data["updated_by"] = request.user.id
        
        serializer = EditEmailAcheteurSerializer(
            email, data=data, partial=True
        )
        
        if serializer.is_valid():
            email = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_EMAIL',
                object_id=email.id,
                object_type='EmailAcheteur',
                details=f"Adresse email modifiée pour l'acheteur {email.acheteur.nom}: {email.email}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Adresse email modifiée avec succès",
                "data": EmailAcheteurSerializer(email).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, acheteur_id, email_id):
        """Supprime une adresse email"""
        email = self.get_email(acheteur_id, email_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_EMAIL',
            object_id=email.id,
            object_type='EmailAcheteur',
            details=f"Adresse email supprimée pour l'acheteur {email.acheteur.nom}: {email.email}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        email.delete()
        return Response({
            "message": "Adresse email supprimée avec succès"
        }, status=status.HTTP_200_OK)










# views.py
class ListAllSubCategoriesView(APIView):
    def get(self, request, *args, **kwargs):
        subcategories = SubCategoryNaceCode.objects.filter(active=True).order_by("code")
        serializer = SubCategoryNaceCodeSerializer(subcategories, many=True)
        return Response(serializer.data)

class ListSubCategoryNaceCodeView(APIView):
    def get(self, request, category_id, *args, **kwargs):
        subcategories = SubCategoryNaceCode.objects.filter(category_id=category_id, active=True).order_by("code")
        serializer = SubCategoryNaceCodeSerializer(subcategories, many=True)
        return Response(serializer.data)

class ListCategoryNaceCodeView(APIView):
    def get(self, request, *args, **kwargs):
        categories = CategoryNaceCode.objects.filter(active=True).order_by("code")
        serializer = CategoryNaceCodeSerializer(categories, many=True)
        return Response(serializer.data)

class ListSubCategoryNaceCodeView(APIView):
    def get(self, request, category_id, *args, **kwargs):
        subcategories = SubCategoryNaceCode.objects.filter(category_id=category_id, active=True).order_by("code")
        serializer = SubCategoryNaceCodeSerializer(subcategories, many=True)
        return Response(serializer.data)

class ListAcheteurCodeNaceView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        codes_nace = CodeNaceAcheteur.objects.filter(acheteur_id=acheteur_id).order_by("-updated_at")
        paginator = Paginator(codes_nace, 10)
        code_nace_page = paginator.get_page(page_number)
        serializer = ListCodeNaceAcheteurSerializer(code_nace_page, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": code_nace_page.has_next(),
            "previous": code_nace_page.has_previous(),
        })

class SearchAcheteurCodeNaceView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        codes_nace = CodeNaceAcheteur.objects.filter(
            Q(acheteur_id=acheteur_id) &
            (Q(code__code__icontains=search_term) | Q(code__libelle__icontains=search_term))
        ).order_by("-updated_at")
        paginator = Paginator(codes_nace, 10)
        page_number = request.query_params.get("page", 1)
        code_nace_page = paginator.get_page(page_number)
        serializer = ListCodeNaceAcheteurSerializer(code_nace_page, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": code_nace_page.has_next(),
            "previous": code_nace_page.has_previous(),
        })

class AddAcheteurCodeNaceView(APIView):
    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        serializer = AddCodeNaceAcheteurSerializer(data=data)
        if serializer.is_valid():
            # Vérifier si ce code NACE est déjà associé à cet acheteur
            if CodeNaceAcheteur.objects.filter(acheteur_id=acheteur_id, code_id=data["code"]).exists():
                return Response(
                    {"detail": "Ce code NACE est déjà associé à cet acheteur."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DetailAcheteurCodeNaceView(APIView):
    def get(self, request, acheteur_id, code_nace_id, *args, **kwargs):
        code_nace = CodeNaceAcheteur.objects.filter(id=code_nace_id, acheteur_id=acheteur_id).first()
        if not code_nace:
            return Response(
                {"detail": "Code NACE non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DetailCodeNaceAcheteurSerializer(code_nace)
        return Response(serializer.data)

class EditAcheteurCodeNaceView(APIView):
    def put(self, request, acheteur_id, code_nace_id, *args, **kwargs):
        code_nace = CodeNaceAcheteur.objects.filter(id=code_nace_id, acheteur_id=acheteur_id).first()
        if not code_nace:
            return Response(
                {"detail": "Code NACE non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = EditCodeNaceAcheteurSerializer(code_nace, data=request.data, partial=True)
        if serializer.is_valid():
            # Vérifier si le nouveau code est déjà associé à cet acheteur
            new_code_id = request.data.get("code")
            if new_code_id and CodeNaceAcheteur.objects.filter(acheteur_id=acheteur_id, code_id=new_code_id).exclude(id=code_nace_id).exists():
                return Response(
                    {"detail": "Ce code NACE est déjà associé à cet acheteur."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurCodeNaceView(APIView):
    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        codes_nace = CodeNaceAcheteur.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not codes_nace.exists():
            return Response(
                {"error": "Aucun code NACE trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )
        count, _ = codes_nace.delete()
        return Response(
            {"message": f"{count} codes NACE supprimés avec succès."},
            status=status.HTTP_200_OK,
        )
        
class AvailableCodesNaceForAcheteurView(APIView):
    """API pour récupérer les codes NACE disponibles pour un acheteur"""
    
    def get(self, request, acheteur_id):
        search = request.query_params.get('search', '')
        category_id = request.query_params.get('category_id', '')
        
        # Récupérer les codes déjà assignés à cet acheteur
        assigned_codes = CodeNaceAcheteur.objects.filter(
            acheteur_id=acheteur_id
        ).values_list('code_id', flat=True)
        
        # Filtrer les codes non assignés
        queryset = SubCategoryNaceCode.objects.filter(
            active=True
        ).exclude(
            id__in=assigned_codes
        )
        
        # Appliquer les filtres
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | 
                Q(libelle__icontains=search)
            )
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Pagination
        page_number = request.query_params.get('page', 1)
        paginator = Paginator(queryset.order_by('code'), 20)
        page = paginator.get_page(page_number)
        
        serializer = SearchSubCategoryNaceCodeSerializer(page, many=True)
        
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': page.has_next(),
            'previous': page.has_previous(),
        })

class SearchSubCategoryNaceCodeView(APIView):
    """API pour rechercher des sous-catégories NACE"""
    
    def get(self, request):
        search = request.query_params.get('search', '')
        category_id = request.query_params.get('category_id', '')
        
        queryset = SubCategoryNaceCode.objects.filter(active=True)
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | 
                Q(libelle__icontains=search)
            )
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Pagination
        page_number = request.query_params.get('page', 1)
        paginator = Paginator(queryset.order_by('code'), 50)
        page = paginator.get_page(page_number)
        
        serializer = SearchSubCategoryNaceCodeSerializer(page, many=True)
        
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': page.has_next(),
            'previous': page.has_previous(),
        })
        


class AcheteurCodeNaceListView(APIView):
    """
    API pour gérer les codes NACE d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des codes NACE de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        codes_nace = CodeNaceAcheteur.objects.filter(
            acheteur=acheteur
        ).select_related(
            'code', 'code__category'
        ).order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            codes_nace = codes_nace.filter(
                Q(code__code__icontains=search) |
                Q(code__libelle__icontains=search) |
                Q(code__category__code__icontains=search) |
                Q(code__category__libelle__icontains=search)
            )
        
        # Filtrer par catégorie si spécifié
        category_id = request.query_params.get('category_id')
        if category_id:
            codes_nace = codes_nace.filter(code__category_id=category_id)
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(codes_nace, request)
        
        serializer = CodeNaceAcheteurWithDetailsSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Ajoute un nouveau code NACE à l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = AddCodeNaceAcheteurSerializer(data=data)
        
        if serializer.is_valid():
            # Sauvegarder en passant created_by comme argument supplémentaire
            code_nace = serializer.save(created_by=request.user)
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='ADD_CODE_NACE',
                object_id=code_nace.id,
                object_type='CodeNaceAcheteur',
                details=f"Code NACE {code_nace.code.code} - {code_nace.code.libelle} ajouté pour l'acheteur {acheteur.nom} ({acheteur.code})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Code NACE ajouté avec succès",
                "data": CodeNaceAcheteurSerializer(code_nace).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AcheteurCodeNaceDetailView(APIView):
    """
    API pour gérer un code NACE spécifique d'un acheteur
    Méthodes: GET (détail), PUT (modification), DELETE (suppression)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_code_nace(self, acheteur_id, code_nace_id):
        """Récupère le code NACE ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            CodeNaceAcheteur.objects.select_related('code', 'code__category'),
            id=code_nace_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, code_nace_id):
        """Récupère les détails d'un code NACE spécifique"""
        code_nace = self.get_code_nace(acheteur_id, code_nace_id)
        serializer = CodeNaceAcheteurSerializer(code_nace)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, code_nace_id):
        """Modifie un code NACE existant"""
        code_nace = self.get_code_nace(acheteur_id, code_nace_id)
        
        serializer = EditCodeNaceAcheteurSerializer(
            code_nace, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            code_nace = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_CODE_NACE',
                object_id=code_nace.id,
                object_type='CodeNaceAcheteur',
                details=f"Code NACE modifié pour l'acheteur {code_nace.acheteur.nom}: {code_nace.code.code} - {code_nace.code.libelle}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Code NACE modifié avec succès",
                "data": CodeNaceAcheteurSerializer(code_nace).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id, code_nace_id):
        """Supprime un code NACE"""
        code_nace = self.get_code_nace(acheteur_id, code_nace_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_CODE_NACE',
            object_id=code_nace.id,
            object_type='CodeNaceAcheteur',
            details=f"Code NACE supprimé pour l'acheteur {code_nace.acheteur.nom}: {code_nace.code.code} - {code_nace.code.libelle}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        code_nace.delete()
        return Response({
            "message": "Code NACE supprimé avec succès"
        }, status=status.HTTP_200_OK)


class SearchSubCategoryNaceCodeView(APIView):
    """
    API pour rechercher des sous-catégories NACE
    Méthodes: GET (recherche)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get(self, request):
        """Recherche de sous-catégories NACE"""
        search = request.query_params.get('search', '')
        category_id = request.query_params.get('category_id')
        
        queryset = SubCategoryNaceCode.objects.filter(active=True)
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(libelle__icontains=search) |
                Q(category__code__icontains=search) |
                Q(category__libelle__icontains=search)
            )
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Trier par code
        queryset = queryset.order_by('code')
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request)
        
        serializer = SearchSubCategoryNaceCodeSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class CategoryNaceCodeListView(APIView):
    """
    API pour récupérer les catégories NACE actives
    Méthodes: GET (liste)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupère toutes les catégories NACE actives"""
        categories = CategoryNaceCode.objects.filter(active=True).order_by('code')
        
        serializer = CategoryNaceCodeSerializer(categories, many=True)
        return Response(serializer.data)


class AcheteurAvailableCodesNaceView(APIView):
    """
    API pour récupérer les codes NACE disponibles pour un acheteur
    (codes NACE non encore associés à l'acheteur)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get(self, request, acheteur_id):
        """Récupère les codes NACE non encore associés à l'acheteur"""
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        search = request.query_params.get('search', '')
        
        # Récupérer les IDs des codes NACE déjà associés à cet acheteur
        existing_code_ids = CodeNaceAcheteur.objects.filter(
            acheteur=acheteur
        ).values_list('code_id', flat=True)
        
        # Chercher les codes NACE non associés
        queryset = SubCategoryNaceCode.objects.filter(
            active=True
        ).exclude(
            id__in=existing_code_ids
        )
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(libelle__icontains=search) |
                Q(category__code__icontains=search) |
                Q(category__libelle__icontains=search)
            )
        
        # Trier par code
        queryset = queryset.order_by('code')
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(queryset, request)
        
        serializer = SearchSubCategoryNaceCodeSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)





class AcheteurCodeNaceListOneView(APIView):
    """
    API pour gérer les codes NACE d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des codes NACE de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        codes_nace = CodeNaceAcheteur.objects.filter(
            acheteur=acheteur
        ).select_related('code', 'code__category').order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            codes_nace = codes_nace.filter(
                code__code__icontains=search
            ) | codes_nace.filter(
                code__libelle__icontains=search
            )
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(codes_nace, request)
        
        serializer = CodeNaceAcheteurOneSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée une nouvelle association code NACE pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = AddCodeNaceAcheteurOneSerializer(data=data)
        
        if serializer.is_valid():
            # Sauvegarder l'association
            code_nace = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_CODE_NACE',
                object_id=code_nace.id,
                object_type='CodeNaceAcheteur',
                details=f"Code NACE ajouté pour l'acheteur {acheteur.nom} ({acheteur.code}): {code_nace.code.code} - {code_nace.code.libelle}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Code NACE ajouté avec succès",
                "data": CodeNaceAcheteurOneSerializer(code_nace).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurCodeNaceDetailOneView(APIView):
    """
    API pour gérer un code NACE spécifique d'un acheteur
    Méthodes: GET (détail), PUT (modification), DELETE (suppression)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_code_nace(self, acheteur_id, code_nace_id):
        """Récupère l'association code NACE ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            CodeNaceAcheteur.objects.select_related('code', 'code__category'),
            id=code_nace_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, code_nace_id):
        """Récupère les détails d'un code NACE spécifique"""
        code_nace = self.get_code_nace(acheteur_id, code_nace_id)
        serializer = CodeNaceAcheteurOneSerializer(code_nace)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, code_nace_id):
        """Modifie une association code NACE existante"""
        code_nace = self.get_code_nace(acheteur_id, code_nace_id)
        
        serializer = EditCodeNaceAcheteurOneSerializer(
            code_nace, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            code_nace = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_CODE_NACE',
                object_id=code_nace.id,
                object_type='CodeNaceAcheteur',
                details=f"Code NACE modifié pour l'acheteur {code_nace.acheteur.nom}: {code_nace.code.code} - {code_nace.code.libelle}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Code NACE modifié avec succès",
                "data": CodeNaceAcheteurOneSerializer(code_nace).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id, code_nace_id):
        """Supprime une association code NACE"""
        code_nace = self.get_code_nace(acheteur_id, code_nace_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_CODE_NACE',
            object_id=code_nace.id,
            object_type='CodeNaceAcheteur',
            details=f"Code NACE supprimé pour l'acheteur {code_nace.acheteur.nom}: {code_nace.code.code} - {code_nace.code.libelle}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        code_nace.delete()
        return Response({
            "message": "Code NACE supprimé avec succès"
        }, status=status.HTTP_200_OK)

class SubCategoryNaceCodeListOneView(APIView):
    """
    API pour lister les sous-catégories NACE (pour sélection)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Retourne la liste des sous-catégories NACE actives"""
        search = request.query_params.get('search', '')
        
        queryset = SubCategoryNaceCode.objects.filter(
            active=True
        ).select_related('category').order_by('code')
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(libelle__icontains=search) |
                Q(category__code__icontains=search) |
                Q(category__libelle__icontains=search)
            )
        
        # Limiter les résultats pour la recherche
        queryset = queryset[:100]
        
        # DEBUG: Ajoutez des logs
        print(f"DEBUG - Search term: {search}")
        print(f"DEBUG - Results count: {queryset.count()}")
        
        serializer = SubCategoryNaceCodeSimpleOneSerializer(queryset, many=True)
        
        # DEBUG: Vérifiez la réponse
        print(f"DEBUG - Serialized data: {serializer.data[:2]}")
        
        return Response(serializer.data)

















class ListCategoryNafCodeView(APIView):
    def get(self, request, *args, **kwargs):
        categories = CategoryNafCode.objects.filter(active=True).order_by("code")
        serializer = CategoryNafCodeSerializer(categories, many=True)
        return Response(serializer.data)

class ListAllSubCategoryNafCodeView(APIView):
    def get(self, request, *args, **kwargs):
        subcategories = SubCategoryNafCode.objects.filter(active=True).order_by("code")
        serializer = SubCategoryNafCodeSerializer(subcategories, many=True)
        return Response(serializer.data)

class ListSubCategoryNafCodeView(APIView):
    def get(self, request, category_id, *args, **kwargs):
        subcategories = SubCategoryNafCode.objects.filter(category_id=category_id, active=True).order_by("code")
        serializer = SubCategoryNafCodeSerializer(subcategories, many=True)
        return Response(serializer.data)

class ListAcheteurCodeNafView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get("page", 1)
        codes_naf = CodeNafAcheteur.objects.filter(acheteur_id=acheteur_id).order_by("-updated_at")
        paginator = Paginator(codes_naf, 10)
        code_naf_page = paginator.get_page(page_number)
        serializer = ListCodeNafAcheteurSerializer(code_naf_page, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": code_naf_page.has_next(),
            "previous": code_naf_page.has_previous(),
        })

class SearchAcheteurCodeNafView(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get("search", "")
        if not search_term:
            return Response(
                {"detail": "Terme de recherche manquant."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        codes_naf = CodeNafAcheteur.objects.filter(
            Q(acheteur_id=acheteur_id) &
            (Q(code__code__icontains=search_term) | Q(code__libelle__icontains=search_term))
        ).order_by("-updated_at")
        paginator = Paginator(codes_naf, 10)
        page_number = request.query_params.get("page", 1)
        code_naf_page = paginator.get_page(page_number)
        serializer = ListCodeNafAcheteurSerializer(code_naf_page, many=True)
        return Response({
            "results": serializer.data,
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "next": code_naf_page.has_next(),
            "previous": code_naf_page.has_previous(),
        })

class AddAcheteurCodeNafView(APIView):
    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        serializer = AddCodeNafAcheteurSerializer(data=data)
        if serializer.is_valid():
            # Vérifier si ce code NAF est déjà associé à cet acheteur
            if CodeNafAcheteur.objects.filter(acheteur_id=acheteur_id, code_id=data["code"]).exists():
                return Response(
                    {"detail": "Ce code NAF est déjà associé à cet acheteur."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DetailAcheteurCodeNafView(APIView):
    def get(self, request, acheteur_id, code_naf_id, *args, **kwargs):
        code_naf = CodeNafAcheteur.objects.filter(id=code_naf_id, acheteur_id=acheteur_id).first()
        if not code_naf:
            return Response(
                {"detail": "Code NAF non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DetailCodeNafAcheteurSerializer(code_naf)
        return Response(serializer.data)

class EditAcheteurCodeNafView(APIView):
    def put(self, request, acheteur_id, code_naf_id, *args, **kwargs):
        code_naf = CodeNafAcheteur.objects.filter(id=code_naf_id, acheteur_id=acheteur_id).first()
        if not code_naf:
            return Response(
                {"detail": "Code NAF non trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = EditCodeNafAcheteurSerializer(code_naf, data=request.data, partial=True)
        if serializer.is_valid():
            # Vérifier si le nouveau code est déjà associé à cet acheteur
            new_code_id = request.data.get("code")
            if new_code_id and CodeNafAcheteur.objects.filter(acheteur_id=acheteur_id, code_id=new_code_id).exclude(id=code_naf_id).exists():
                return Response(
                    {"detail": "Ce code NAF est déjà associé à cet acheteur."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurCodeNafView(APIView):
    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not ids or not isinstance(ids, list):
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        codes_naf = CodeNafAcheteur.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not codes_naf.exists():
            return Response(
                {"error": "Aucun code NAF trouvé pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )
        count, _ = codes_naf.delete()
        return Response(
            {"message": f"{count} codes NAF supprimés avec succès."},
            status=status.HTTP_200_OK,
        )     
        
class AcheteurCodeNafListOneView(APIView):
    """
    API pour gérer les codes NAF d'un acheteur
    Méthodes: GET (liste), POST (création)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get(self, request, acheteur_id):
        """Récupère la liste des codes NAF de l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        codes_naf = CodeNafAcheteur.objects.filter(
            acheteur=acheteur
        ).select_related('code', 'code__category').order_by('-created_at')
        
        # Recherche si paramètre fourni
        search = request.query_params.get('search', '')
        if search:
            codes_naf = codes_naf.filter(
                code__code__icontains=search
            ) | codes_naf.filter(
                code__libelle__icontains=search
            )
        
        # Pagination
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(codes_naf, request)
        
        serializer = CodeNafAcheteurOneSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @transaction.atomic
    def post(self, request, acheteur_id):
        """Crée une nouvelle association code NAF pour l'acheteur"""
        acheteur = self.get_acheteur(acheteur_id)
        
        data = request.data.copy()
        data["acheteur"] = acheteur_id
        
        serializer = AddCodeNafAcheteurOneSerializer(data=data)
        
        if serializer.is_valid():
            # Sauvegarder l'association
            code_naf = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='CREATE_CODE_NAF',
                object_id=code_naf.id,
                object_type='CodeNafAcheteur',
                details=f"Code NAF ajouté pour l'acheteur {acheteur.nom} ({acheteur.code}): {code_naf.code.code} - {code_naf.code.libelle}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Code NAF ajouté avec succès",
                "data": CodeNafAcheteurOneSerializer(code_naf).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AcheteurCodeNafDetailOneView(APIView):
    """
    API pour gérer un code NAF spécifique d'un acheteur
    Méthodes: GET (détail), PUT (modification), DELETE (suppression)
    """
    permission_classes = [IsAuthenticated]
    
    def get_acheteur(self, acheteur_id):
        """Récupère l'acheteur ou retourne 404"""
        return get_object_or_404(Acheteur, id=acheteur_id)
    
    def get_code_naf(self, acheteur_id, code_naf_id):
        """Récupère l'association code NAF ou retourne 404"""
        acheteur = self.get_acheteur(acheteur_id)
        return get_object_or_404(
            CodeNafAcheteur.objects.select_related('code', 'code__category'),
            id=code_naf_id, 
            acheteur=acheteur
        )
    
    def get(self, request, acheteur_id, code_naf_id):
        """Récupère les détails d'un code NAF spécifique"""
        code_naf = self.get_code_naf(acheteur_id, code_naf_id)
        serializer = CodeNafAcheteurOneSerializer(code_naf)
        return Response(serializer.data)
    
    @transaction.atomic
    def put(self, request, acheteur_id, code_naf_id):
        """Modifie une association code NAF existante"""
        code_naf = self.get_code_naf(acheteur_id, code_naf_id)
        
        serializer = EditCodeNafAcheteurOneSerializer(
            code_naf, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            code_naf = serializer.save()
            
            # Log d'activité
            ActivityLog.objects.create(
                user=request.user,
                action_type='UPDATE_CODE_NAF',
                object_id=code_naf.id,
                object_type='CodeNafAcheteur',
                details=f"Code NAF modifié pour l'acheteur {code_naf.acheteur.nom}: {code_naf.code.code} - {code_naf.code.libelle}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                "message": "Code NAF modifié avec succès",
                "data": CodeNafAcheteurOneSerializer(code_naf).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request, acheteur_id, code_naf_id):
        """Supprime une association code NAF"""
        code_naf = self.get_code_naf(acheteur_id, code_naf_id)
        
        # Log d'activité avant suppression
        ActivityLog.objects.create(
            user=request.user,
            action_type='DELETE_CODE_NAF',
            object_id=code_naf.id,
            object_type='CodeNafAcheteur',
            details=f"Code NAF supprimé pour l'acheteur {code_naf.acheteur.nom}: {code_naf.code.code} - {code_naf.code.libelle}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        code_naf.delete()
        return Response({
            "message": "Code NAF supprimé avec succès"
        }, status=status.HTTP_200_OK)

class SubCategoryNafCodeListOneView(APIView):
    """
    API pour lister les sous-catégories NAF (pour sélection)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Retourne la liste des sous-catégories NAF actives"""
        search = request.query_params.get('search', '')
        
        queryset = SubCategoryNafCode.objects.filter(
            active=True
        ).select_related('category').order_by('code')
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(libelle__icontains=search) |
                Q(category__code__icontains=search) |
                Q(category__libelle__icontains=search)
            )
        
        # Limiter les résultats pour la recherche
        queryset = queryset[:100]
        
        serializer = SubCategoryNafCodeSimpleOneSerializer(queryset, many=True)

        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
# Commentaire Ratios Bilan
# ─────────────────────────────────────────────────────────────────────────────
from main.models import CommentaireRatiosBilan

class CommentaireRatiosBilanAPIView(APIView):
    """
    GET  /api/acheteur/<acheteur_id>/commentaire-ratios/<type_bilan>/
    POST /api/acheteur/<acheteur_id>/commentaire-ratios/<type_bilan>/
    """
    permission_classes = [IsAuthenticated]

    VALID_TYPES = {'classique', 'syscohada', 'anglais', 'ifrs', 'financier_ifrs', 'bancaire'}

    def _get_acheteur(self, acheteur_id):
        return get_object_or_404(Acheteur, id=acheteur_id)

    def get(self, request, acheteur_id, type_bilan):
        if type_bilan not in self.VALID_TYPES:
            return Response({'error': 'Type de bilan invalide'}, status=status.HTTP_400_BAD_REQUEST)
        acheteur = self._get_acheteur(acheteur_id)
        obj, _ = CommentaireRatiosBilan.objects.get_or_create(acheteur=acheteur, type_bilan=type_bilan)
        return Response({'commentaire': obj.commentaire or '', 'updated_at': obj.updated_at})

    def post(self, request, acheteur_id, type_bilan):
        if type_bilan not in self.VALID_TYPES:
            return Response({'error': 'Type de bilan invalide'}, status=status.HTTP_400_BAD_REQUEST)
        acheteur = self._get_acheteur(acheteur_id)
        commentaire = request.data.get('commentaire', '')
        obj, _ = CommentaireRatiosBilan.objects.get_or_create(acheteur=acheteur, type_bilan=type_bilan)
        obj.commentaire = commentaire
        obj.save()
        return Response({'message': 'Commentaire enregistré', 'updated_at': obj.updated_at})
