from django.shortcuts import render
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from main.models import CustomUser
from main.serializers import *
import random
import string
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from django.contrib.auth.decorators import login_required
from main.utils import send_email_with_secret_code
from django.template.loader import render_to_string
from rest_framework import status
from django.contrib.auth import logout
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django.urls import reverse
from django.contrib.auth import login
from rest_framework.viewsets import ModelViewSet
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


# === Vues Modules Acheteur === #



class ListAcheteurResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)

        resume_list = Resume.objects.filter(acheteur_id=acheteur_id).order_by('-created_at')

        paginator = Paginator(resume_list, 10)  # 10 résumés par page
        resume_page = paginator.get_page(page_number)
        serializer = ResumeSerializer(resume_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': resume_page.has_next(),
            'previous': resume_page.has_previous()
        })



class SearchAcheteurResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        resume_list = Resume.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(capital_social__icontains=search_term) |
                Q(chiffre_affaire__icontains=search_term) |
                Q(resultat_net__icontains=search_term) |
                Q(capitaux_propre__icontains=search_term) |
                Q(nombre_employe__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(resume_list, 10)  # 10 résumés par page
        page_number = request.query_params.get('page', 1)
        resume_page = paginator.get_page(page_number)
        serializer = ResumeSerializer(resume_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': resume_page.has_next(),
            'previous': resume_page.has_previous()
        })
        
        

class AddAcheteurResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        # Créez une copie modifiable de request.data
        data = request.data.copy()
        data['acheteur'] = acheteur_id

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
            return Response({'detail': 'Résumé non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetResumeSerializer(resume)
        return Response(serializer.data)

    def put(self, request, acheteur_id, resume_id, *args, **kwargs):
        resume = Resume.objects.filter(id=resume_id, acheteur_id=acheteur_id).first()
        if not resume:
            return Response({'detail': 'Résumé non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditResumeSerializer(resume, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
class DeleteAcheteurResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        resumes = Resume.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not resumes.exists():
            return Response({'error': 'Aucun résumé trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = resumes.delete()
        return Response({'message': f'{count} résumés supprimés avec succès.'}, status=status.HTTP_200_OK)






class ListAcheteurRiskRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)

        risk_rating_list = RiskRating.objects.filter(acheteur_id=acheteur_id).order_by('-created_at')

        paginator = Paginator(risk_rating_list, 10)  # 10 évaluations par page
        risk_rating_page = paginator.get_page(page_number)
        serializer = RiskRatingSerializer(risk_rating_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': risk_rating_page.has_next(),
            'previous': risk_rating_page.has_previous()
        })
        

class SearchAcheteurRiskRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        risk_rating_list = RiskRating.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(interpretation__icontains=search_term) |
                Q(analyse__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(risk_rating_list, 10)  # 10 évaluations par page
        page_number = request.query_params.get('page', 1)
        risk_rating_page = paginator.get_page(page_number)
        serializer = RiskRatingSerializer(risk_rating_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': risk_rating_page.has_next(),
            'previous': risk_rating_page.has_previous()
        })
        
        

class AddAcheteurRiskRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        # Créez une copie modifiable de request.data
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddRiskRatingSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class EditAcheteurRiskRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, risk_rating_id, *args, **kwargs):
        risk_rating = RiskRating.objects.filter(id=risk_rating_id, acheteur_id=acheteur_id).first()
        if not risk_rating:
            return Response({'detail': 'Évaluation de risque non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetRiskRatingSerializer(risk_rating)
        return Response(serializer.data)

    def put(self, request, acheteur_id, risk_rating_id, *args, **kwargs):
        risk_rating = RiskRating.objects.filter(id=risk_rating_id, acheteur_id=acheteur_id).first()
        if not risk_rating:
            return Response({'detail': 'Évaluation de risque non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditRiskRatingSerializer(risk_rating, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    
class DeleteAcheteurRiskRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        risk_ratings = RiskRating.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not risk_ratings.exists():
            return Response({'error': 'Aucune évaluation de risque trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = risk_ratings.delete()
        return Response({'message': f'{count} évaluations de risque supprimées avec succès.'}, status=status.HTTP_200_OK)
    
    





class ListAcheteurDataSaveRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)

        donnees_list = DonneesEnregistrement.objects.filter(acheteur_id=acheteur_id).order_by('-created_at')

        paginator = Paginator(donnees_list, 10)  # 10 enregistrements par page
        donnees_page = paginator.get_page(page_number)
        serializer = DonneesEnregistrementSerializer(donnees_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': donnees_page.has_next(),
            'previous': donnees_page.has_previous()
        })
        
        


class SearchAcheteurDataSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        donnees_list = DonneesEnregistrement.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(numero_registre_commerce__icontains=search_term) |
                Q(numero_fiscale__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(donnees_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        donnees_page = paginator.get_page(page_number)
        serializer = DonneesEnregistrementSerializer(donnees_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': donnees_page.has_next(),
            'previous': donnees_page.has_previous()
        })
        
        

class AddAcheteurDataSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        # Créez une copie modifiable de request.data
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddDonneesEnregistrementSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
        
        
        
class EditAcheteurDataSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, donnee_enregistrement_id, *args, **kwargs):
        donnee = DonneesEnregistrement.objects.filter(id=donnee_enregistrement_id, acheteur_id=acheteur_id).first()
        if not donnee:
            return Response({'detail': 'Donnée d\'enregistrement non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetDonneesEnregistrementSerializer(donnee)
        return Response(serializer.data)

    def put(self, request, acheteur_id, donnee_enregistrement_id, *args, **kwargs):
        donnee = DonneesEnregistrement.objects.filter(id=donnee_enregistrement_id, acheteur_id=acheteur_id).first()
        if not donnee:
            return Response({'detail': 'Donnée d\'enregistrement non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditDonneesEnregistrementSerializer(donnee, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    

class DeleteAcheteurDataSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        donnees = DonneesEnregistrement.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not donnees.exists():
            return Response({'error': 'Aucune donnée d\'enregistrement trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = donnees.delete()
        return Response({'message': f'{count} données d\'enregistrement supprimées avec succès.'}, status=status.HTTP_200_OK)








