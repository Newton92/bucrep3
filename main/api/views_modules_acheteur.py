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


# === Fonctions utiles === #


def str_to_bool(value):
    return value.lower() in ("true", "1", "t")


# === Vues Modules Acheteur === #



class ListAcheteurResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')
        devise = request.query_params.get('devise', '')
        capital_social_min = request.query_params.get('capital_social_min', '')
        capital_social_max = request.query_params.get('capital_social_max', '')

        # Validate and convert query parameters
        try:
            capital_social_min = decimal.Decimal(capital_social_min) if capital_social_min else None
            capital_social_max = decimal.Decimal(capital_social_max) if capital_social_max else None
        except decimal.InvalidOperation:
            return Response({'error': 'Les valeurs de capital_social_min et capital_social_max doivent être des nombres décimaux valides.'}, status=400)

        resume_list = Resume.objects.filter(
            acheteur_id=acheteur_id,
            devise__nom__icontains=devise
        ).order_by('-created_at')

        if capital_social_min is not None:
            resume_list = resume_list.filter(capital_social__gte=capital_social_min)

        if capital_social_max is not None:
            resume_list = resume_list.filter(capital_social__lte=capital_social_max)

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
        search_term = request.query_params.get('search', '')

        risk_rating_list = RiskRating.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(interpretation__icontains=search_term) |
                Q(analyse__icontains=search_term)
            )
        ).order_by('-created_at')

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
    
    





class ListAcheteurDataSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')
        date_creation = request.query_params.get('date_creation', '')
        date_registre = request.query_params.get('date_registre', '')

        donnees_list = DonneesEnregistrement.objects.filter(
            acheteur_id=acheteur_id,
            date_creation__icontains=date_creation,
            date_registre__icontains=date_registre
        ).order_by('-created_at')

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








class ListAcheteurTendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        tendances_list = Tendance.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by('-created_at')

        if search_term:
            tendances_list = tendances_list.filter(
                Q(presse_media__icontains=search_term) |
                Q(principaux_concurrent__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(tendances_list, 10)  # 10 enregistrements par page
        tendances_page = paginator.get_page(page_number)
        serializer = TendanceSerializer(tendances_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': tendances_page.has_next(),
            'previous': tendances_page.has_previous()
        })


class SearchAcheteurTendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        tendances_list = Tendance.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(presse_media__icontains=search_term) |
                Q(principaux_concurrent__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(tendances_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        tendances_page = paginator.get_page(page_number)
        serializer = TendanceSerializer(tendances_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': tendances_page.has_next(),
            'previous': tendances_page.has_previous()
        })


class AddAcheteurTendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddTendanceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class EditAcheteurTendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, tendance_id, *args, **kwargs):
        tendance = Tendance.objects.filter(id=tendance_id, acheteur_id=acheteur_id).first()
        if not tendance:
            return Response({'detail': 'Tendance non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetTendanceSerializer(tendance)
        return Response(serializer.data)

    def put(self, request, acheteur_id, tendance_id, *args, **kwargs):
        tendance = Tendance.objects.filter(id=tendance_id, acheteur_id=acheteur_id).first()
        if not tendance:
            return Response({'detail': 'Tendance non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditTendanceSerializer(tendance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class DeleteAcheteurTendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        tendances = Tendance.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not tendances.exists():
            return Response({'error': 'Aucune tendance trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = tendances.delete()
        return Response({'message': f'{count} tendances supprimées avec succès.'}, status=status.HTTP_200_OK)







class ListAcheteurResponsableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        responsables_list = ResponsableAcheteur.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by('-created_at')

        if search_term:
            responsables_list = responsables_list.filter(
                Q(nom__icontains=search_term) |
                Q(prenom__icontains=search_term) |
                Q(poste__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(responsables_list, 10)  # 10 enregistrements par page
        responsables_page = paginator.get_page(page_number)
        serializer = ResponsableAcheteurSerializer(responsables_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': responsables_page.has_next(),
            'previous': responsables_page.has_previous()
        })



class SearchAcheteurResponsableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        responsables_list = ResponsableAcheteur.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(nom__icontains=search_term) |
                Q(prenom__icontains=search_term) |
                Q(poste__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(responsables_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        responsables_page = paginator.get_page(page_number)
        serializer = ResponsableAcheteurSerializer(responsables_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': responsables_page.has_next(),
            'previous': responsables_page.has_previous()
        })




class AddAcheteurResponsableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddResponsableAcheteurSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class EditAcheteurResponsableView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, responsable_id, *args, **kwargs):
        responsable = ResponsableAcheteur.objects.filter(id=responsable_id, acheteur_id=acheteur_id).first()
        if not responsable:
            return Response({'detail': 'Responsable non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetResponsableAcheteurSerializer(responsable)
        return Response(serializer.data)

    def put(self, request, acheteur_id, responsable_id, *args, **kwargs):
        responsable = ResponsableAcheteur.objects.filter(id=responsable_id, acheteur_id=acheteur_id).first()
        if not responsable:
            return Response({'detail': 'Responsable non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditResponsableAcheteurSerializer(responsable, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class DeleteAcheteurResponsableView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        responsables = ResponsableAcheteur.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not responsables.exists():
            return Response({'error': 'Aucun responsable trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = responsables.delete()
        return Response({'message': f'{count} responsables supprimés avec succès.'}, status=status.HTTP_200_OK)









class ListAcheteurAntecedentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        antecedents_list = AntecedantsJuridique.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by('-created_at')

        if search_term:
            antecedents_list = antecedents_list.filter(
                Q(dossier_faillite__icontains=search_term) |
                Q(jugement_cour__icontains=search_term) |
                Q(antecedant_redressement__icontains=search_term) |
                Q(autre__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(antecedents_list, 10)  # 10 enregistrements par page
        antecedents_page = paginator.get_page(page_number)
        serializer = AntecedantsJuridiqueSerializer(antecedents_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': antecedents_page.has_next(),
            'previous': antecedents_page.has_previous()
        })



class SearchAcheteurAntecedentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        antecedents_list = AntecedantsJuridique.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(dossier_faillite__icontains=search_term) |
                Q(jugement_cour__icontains=search_term) |
                Q(antecedant_redressement__icontains=search_term) |
                Q(autre__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(antecedents_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        antecedents_page = paginator.get_page(page_number)
        serializer = AntecedantsJuridiqueSerializer(antecedents_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': antecedents_page.has_next(),
            'previous': antecedents_page.has_previous()
        })



class AddAcheteurAntecedentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddAntecedantsJuridiqueSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class EditAcheteurAntecedentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, antecedent_id, *args, **kwargs):
        antecedent = AntecedantsJuridique.objects.filter(id=antecedent_id, acheteur_id=acheteur_id).first()
        if not antecedent:
            return Response({'detail': 'Antécédent non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetAntecedantsJuridiqueSerializer(antecedent)
        return Response(serializer.data)

    def put(self, request, acheteur_id, antecedent_id, *args, **kwargs):
        antecedent = AntecedantsJuridique.objects.filter(id=antecedent_id, acheteur_id=acheteur_id).first()
        if not antecedent:
            return Response({'detail': 'Antécédent non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditAntecedantsJuridiqueSerializer(antecedent, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class DeleteAcheteurAntecedentView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        antecedents = AntecedantsJuridique.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not antecedents.exists():
            return Response({'error': 'Aucun antécédent trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = antecedents.delete()
        return Response({'message': f'{count} antécédents supprimés avec succès.'}, status=status.HTTP_200_OK)









class ListAcheteurGestionRisqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        gestion_risque_list = RiskManagment.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by('-created_at')

        if search_term:
            gestion_risque_list = gestion_risque_list.filter(
                Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(gestion_risque_list, 10)  # 10 enregistrements par page
        gestion_risque_page = paginator.get_page(page_number)
        serializer = RiskManagmentSerializer(gestion_risque_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': gestion_risque_page.has_next(),
            'previous': gestion_risque_page.has_previous()
        })
        
        
        
class SearchAcheteurGestionRisqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        gestion_risque_list = RiskManagment.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(commentaire__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(gestion_risque_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        gestion_risque_page = paginator.get_page(page_number)
        serializer = RiskManagmentSerializer(gestion_risque_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': gestion_risque_page.has_next(),
            'previous': gestion_risque_page.has_previous()
        })



class AddAcheteurGestionRisqueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddRiskManagmentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class EditAcheteurGestionRisqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, gestion_risque_id, *args, **kwargs):
        gestion_risque = RiskManagment.objects.filter(id=gestion_risque_id, acheteur_id=acheteur_id).first()
        if not gestion_risque:
            return Response({'detail': 'Gestion de risque non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetRiskManagmentSerializer(gestion_risque)
        return Response(serializer.data)

    def put(self, request, acheteur_id, gestion_risque_id, *args, **kwargs):
        gestion_risque = RiskManagment.objects.filter(id=gestion_risque_id, acheteur_id=acheteur_id).first()
        if not gestion_risque:
            return Response({'detail': 'Gestion de risque non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditRiskManagmentSerializer(gestion_risque, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class DeleteAcheteurGestionRisqueView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        gestion_risques = RiskManagment.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not gestion_risques.exists():
            return Response({'error': 'Aucune gestion de risque trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = gestion_risques.delete()
        return Response({'message': f'{count} gestions de risque supprimées avec succès.'}, status=status.HTTP_200_OK)
    
    
    
    
    
    
    
    

class ListAcheteurMembreConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        membre_conseil_list = ConseilAdministration.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by('-created_at')

        if search_term:
            membre_conseil_list = membre_conseil_list.filter(
                Q(nom__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(membre_conseil_list, 10)  # 10 enregistrements par page
        membre_conseil_page = paginator.get_page(page_number)
        serializer = ConseilAdministrationSerializer(membre_conseil_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': membre_conseil_page.has_next(),
            'previous': membre_conseil_page.has_previous()
        })
        
        
        
class SearchAcheteurMembreConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        membre_conseil_list = ConseilAdministration.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(nom__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(membre_conseil_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        membre_conseil_page = paginator.get_page(page_number)
        serializer = ConseilAdministrationSerializer(membre_conseil_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': membre_conseil_page.has_next(),
            'previous': membre_conseil_page.has_previous()
        })


class AddAcheteurMembreConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddConseilAdministrationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class EditAcheteurMembreConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, membre_conseil_id, *args, **kwargs):
        membre_conseil = ConseilAdministration.objects.filter(id=membre_conseil_id, acheteur_id=acheteur_id).first()
        if not membre_conseil:
            return Response({'detail': 'Membre du conseil non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetConseilAdministrationSerializer(membre_conseil)
        return Response(serializer.data)

    def put(self, request, acheteur_id, membre_conseil_id, *args, **kwargs):
        membre_conseil = ConseilAdministration.objects.filter(id=membre_conseil_id, acheteur_id=acheteur_id).first()
        if not membre_conseil:
            return Response({'detail': 'Membre du conseil non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditConseilAdministrationSerializer(membre_conseil, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class DeleteAcheteurMembreConseilView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        membres_conseil = ConseilAdministration.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not membres_conseil.exists():
            return Response({'error': 'Aucun membre du conseil trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = membres_conseil.delete()
        return Response({'message': f'{count} membres du conseil supprimés avec succès.'}, status=status.HTTP_200_OK)











class ListAcheteurCompositionCapitalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        composition_list = CompositionCapitalSocial.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by('-created_at')

        if search_term:
            composition_list = composition_list.filter(
                Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(composition_list, 10)  # 10 enregistrements par page
        composition_page = paginator.get_page(page_number)
        serializer = CompositionCapitalSocialSerializer(composition_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': composition_page.has_next(),
            'previous': composition_page.has_previous()
        })
        
        
        
        
class SearchAcheteurCompositionCapitalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        composition_list = CompositionCapitalSocial.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(commentaire__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(composition_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        composition_page = paginator.get_page(page_number)
        serializer = CompositionCapitalSocialSerializer(composition_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': composition_page.has_next(),
            'previous': composition_page.has_previous()
        })




class AddAcheteurCompositionCapitalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddCompositionCapitalSocialSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class EditAcheteurCompositionCapitalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, composition_capital_id, *args, **kwargs):
        composition = CompositionCapitalSocial.objects.filter(id=composition_capital_id, acheteur_id=acheteur_id).first()
        if not composition:
            return Response({'detail': 'Composition du capital non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetCompositionCapitalSocialSerializer(composition)
        return Response(serializer.data)

    def put(self, request, acheteur_id, composition_capital_id, *args, **kwargs):
        composition = CompositionCapitalSocial.objects.filter(id=composition_capital_id, acheteur_id=acheteur_id).first()
        if not composition:
            return Response({'detail': 'Composition du capital non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditCompositionCapitalSocialSerializer(composition, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class DeleteAcheteurCompositionCapitalView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        compositions = CompositionCapitalSocial.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not compositions.exists():
            return Response({'error': 'Aucune composition du capital trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = compositions.delete()
        return Response({'message': f'{count} compositions du capital supprimées avec succès.'}, status=status.HTTP_200_OK)
    
    
    






class ListAcheteurActionnaireView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        actionnaire_list = CompositionAction.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by('-created_at')

        if search_term:
            actionnaire_list = actionnaire_list.filter(
                Q(commentaire__icontains=search_term) |
                Q(nom__icontains=search_term) |
                Q(prenom__icontains=search_term)
            )

        paginator = Paginator(actionnaire_list, 10)  # 10 enregistrements par page
        actionnaire_page = paginator.get_page(page_number)
        serializer = CompositionActionSerializer(actionnaire_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': actionnaire_page.has_next(),
            'previous': actionnaire_page.has_previous()
        })



class SearchAcheteurActionnaireView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        actionnaire_list = CompositionAction.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(commentaire__icontains=search_term) |
                Q(nom__icontains=search_term) |
                Q(prenom__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(actionnaire_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        actionnaire_page = paginator.get_page(page_number)
        serializer = CompositionActionSerializer(actionnaire_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': actionnaire_page.has_next(),
            'previous': actionnaire_page.has_previous()
        })



class AddAcheteurActionnaireView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddCompositionActionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class EditAcheteurActionnaireView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, actionnaire_id, *args, **kwargs):
        actionnaire = CompositionAction.objects.filter(id=actionnaire_id, acheteur_id=acheteur_id).first()
        if not actionnaire:
            return Response({'detail': 'Actionnaire non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetCompositionActionSerializer(actionnaire)
        return Response(serializer.data)

    def put(self, request, acheteur_id, actionnaire_id, *args, **kwargs):
        actionnaire = CompositionAction.objects.filter(id=actionnaire_id, acheteur_id=acheteur_id).first()
        if not actionnaire:
            return Response({'detail': 'Actionnaire non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditCompositionActionSerializer(actionnaire, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class DeleteAcheteurActionnaireView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        actionnaires = CompositionAction.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not actionnaires.exists():
            return Response({'error': 'Aucun actionnaire trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = actionnaires.delete()
        return Response({'message': f'{count} actionnaires supprimés avec succès.'}, status=status.HTTP_200_OK)








class ListAcheteurOpinionAcremacView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        opinion_list = OpinionCreditAcremac.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by('-created_at')

        if search_term:
            opinion_list = opinion_list.filter(
                Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(opinion_list, 10)  # 10 enregistrements par page
        opinion_page = paginator.get_page(page_number)
        serializer = OpinionCreditAcremacSerializer(opinion_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': opinion_page.has_next(),
            'previous': opinion_page.has_previous()
        })



class SearchAcheteurOpinionAcremacView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        opinion_list = OpinionCreditAcremac.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(commentaire__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(opinion_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        opinion_page = paginator.get_page(page_number)
        serializer = OpinionCreditAcremacSerializer(opinion_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': opinion_page.has_next(),
            'previous': opinion_page.has_previous()
        })



class AddAcheteurOpinionAcremacView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddOpinionCreditAcremacSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class EditAcheteurOpinionAcremacView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, opinion_id, *args, **kwargs):
        opinion = OpinionCreditAcremac.objects.filter(id=opinion_id, acheteur_id=acheteur_id).first()
        if not opinion:
            return Response({'detail': 'Opinion de crédit non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetOpinionCreditAcremacSerializer(opinion)
        return Response(serializer.data)

    def put(self, request, acheteur_id, opinion_id, *args, **kwargs):
        opinion = OpinionCreditAcremac.objects.filter(id=opinion_id, acheteur_id=acheteur_id).first()
        if not opinion:
            return Response({'detail': 'Opinion de crédit non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditOpinionCreditAcremacSerializer(opinion, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class DeleteAcheteurOpinionAcremacView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        opinions = OpinionCreditAcremac.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not opinions.exists():
            return Response({'error': 'Aucune opinion de crédit trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = opinions.delete()
        return Response({'message': f'{count} opinions de crédit supprimées avec succès.'}, status=status.HTTP_200_OK)
    
    
    
    
    
    
    


class ListAcheteurFilialeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        filiale_list = Structure.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by('-created_at')

        if search_term:
            filiale_list = filiale_list.filter(
                Q(nom__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )

        paginator = Paginator(filiale_list, 10)  # 10 enregistrements par page
        filiale_page = paginator.get_page(page_number)
        serializer = StructureSerializer(filiale_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': filiale_page.has_next(),
            'previous': filiale_page.has_previous()
        })

class SearchAcheteurFilialeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        filiale_list = Structure.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(nom__icontains=search_term) |
                Q(commentaire__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(filiale_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        filiale_page = paginator.get_page(page_number)
        serializer = StructureSerializer(filiale_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': filiale_page.has_next(),
            'previous': filiale_page.has_previous()
        })

class AddAcheteurFilialeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddStructureSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurFilialeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, filiale_id, *args, **kwargs):
        filiale = Structure.objects.filter(id=filiale_id, acheteur_id=acheteur_id).first()
        if not filiale:
            return Response({'detail': 'Filiale non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetStructureSerializer(filiale)
        return Response(serializer.data)

    def put(self, request, acheteur_id, filiale_id, *args, **kwargs):
        filiale = Structure.objects.filter(id=filiale_id, acheteur_id=acheteur_id).first()
        if not filiale:
            return Response({'detail': 'Filiale non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditStructureSerializer(filiale, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurFilialeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        filiales = Structure.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not filiales.exists():
            return Response({'error': 'Aucune filiale trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = filiales.delete()
        return Response({'message': f'{count} filiales supprimées avec succès.'}, status=status.HTTP_200_OK)







class ListAcheteurAnalyseSectorielleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        analyse_list = AnalyseSectorielle.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by('-created_at')

        if search_term:
            analyse_list = analyse_list.filter(
                Q(commentaire__icontains=search_term) |
                Q(impact_covid_19__icontains=search_term)
            )

        paginator = Paginator(analyse_list, 10)  # 10 enregistrements par page
        analyse_page = paginator.get_page(page_number)
        serializer = AnalyseSectorielleSerializer(analyse_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': analyse_page.has_next(),
            'previous': analyse_page.has_previous()
        })

class SearchAcheteurAnalyseSectorielleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        analyse_list = AnalyseSectorielle.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(commentaire__icontains=search_term) |
                Q(impact_covid_19__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(analyse_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        analyse_page = paginator.get_page(page_number)
        serializer = AnalyseSectorielleSerializer(analyse_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': analyse_page.has_next(),
            'previous': analyse_page.has_previous()
        })

class AddAcheteurAnalyseSectorielleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddAnalyseSectorielleSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurAnalyseSectorielleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, analyse_id, *args, **kwargs):
        analyse = AnalyseSectorielle.objects.filter(id=analyse_id, acheteur_id=acheteur_id).first()
        if not analyse:
            return Response({'detail': 'Analyse sectorielle non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetAnalyseSectorielleSerializer(analyse)
        return Response(serializer.data)

    def put(self, request, acheteur_id, analyse_id, *args, **kwargs):
        analyse = AnalyseSectorielle.objects.filter(id=analyse_id, acheteur_id=acheteur_id).first()
        if not analyse:
            return Response({'detail': 'Analyse sectorielle non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditAnalyseSectorielleSerializer(analyse, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurAnalyseSectorielleView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        analyses = AnalyseSectorielle.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not analyses.exists():
            return Response({'error': 'Aucune analyse sectorielle trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = analyses.delete()
        return Response({'message': f'{count} analyses sectorielles supprimées avec succès.'}, status=status.HTTP_200_OK)








class ListAcheteurCompteFinancierView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        compte_list = CompteFinancier.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by('-created_at')

        if search_term:
            compte_list = compte_list.filter(
                Q(commentaire__icontains=search_term) |
                Q(cabinet__icontains=search_term)
            )

        paginator = Paginator(compte_list, 10)  # 10 enregistrements par page
        compte_page = paginator.get_page(page_number)
        serializer = CompteFinancierSerializer(compte_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': compte_page.has_next(),
            'previous': compte_page.has_previous()
        })



class SearchAcheteurCompteFinancierView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        compte_list = CompteFinancier.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(commentaire__icontains=search_term) |
                Q(cabinet__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(compte_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        compte_page = paginator.get_page(page_number)
        serializer = CompteFinancierSerializer(compte_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': compte_page.has_next(),
            'previous': compte_page.has_previous()
        })



class AddAcheteurCompteFinancierView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddCompteFinancierSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class EditAcheteurCompteFinancierView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, compte_financier_id, *args, **kwargs):
        compte = CompteFinancier.objects.filter(id=compte_financier_id, acheteur_id=acheteur_id).first()
        if not compte:
            return Response({'detail': 'Compte financier non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetCompteFinancierSerializer(compte)
        return Response(serializer.data)

    def put(self, request, acheteur_id, compte_financier_id, *args, **kwargs):
        compte = CompteFinancier.objects.filter(id=compte_financier_id, acheteur_id=acheteur_id).first()
        if not compte:
            return Response({'detail': 'Compte financier non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditCompteFinancierSerializer(compte, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class DeleteAcheteurCompteFinancierView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        comptes = CompteFinancier.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not comptes.exists():
            return Response({'error': 'Aucun compte financier trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = comptes.delete()
        return Response({'message': f'{count} comptes financiers supprimés avec succès.'}, status=status.HTTP_200_OK)











class ListAcheteurOperationHistoriqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        operation_list = OperationEtHistorique.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by('-created_at')

        if search_term:
            operation_list = operation_list.filter(
                Q(commentaire_ratios__icontains=search_term) |
                Q(description_complete_activite__icontains=search_term) |
                Q(importation__icontains=search_term) |
                Q(historique__icontains=search_term)
            )

        paginator = Paginator(operation_list, 10)  # 10 enregistrements par page
        operation_page = paginator.get_page(page_number)
        serializer = OperationEtHistoriqueSerializer(operation_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': operation_page.has_next(),
            'previous': operation_page.has_previous()
        })

class SearchAcheteurOperationHistoriqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        operation_list = OperationEtHistorique.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(commentaire_ratios__icontains=search_term) |
                Q(description_complete_activite__icontains=search_term) |
                Q(importation__icontains=search_term) |
                Q(historique__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(operation_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        operation_page = paginator.get_page(page_number)
        serializer = OperationEtHistoriqueSerializer(operation_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': operation_page.has_next(),
            'previous': operation_page.has_previous()
        })

class AddAcheteurOperationHistoriqueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddOperationEtHistoriqueSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurOperationHistoriqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, operation_historique_id, *args, **kwargs):
        operation = OperationEtHistorique.objects.filter(id=operation_historique_id, acheteur_id=acheteur_id).first()
        if not operation:
            return Response({'detail': 'Opération et historique non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetOperationEtHistoriqueSerializer(operation)
        return Response(serializer.data)

    def put(self, request, acheteur_id, operation_historique_id, *args, **kwargs):
        operation = OperationEtHistorique.objects.filter(id=operation_historique_id, acheteur_id=acheteur_id).first()
        if not operation:
            return Response({'detail': 'Opération et historique non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditOperationEtHistoriqueSerializer(operation, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurOperationHistoriqueView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        operations = OperationEtHistorique.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not operations.exists():
            return Response({'error': 'Aucune opération et historique trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = operations.delete()
        return Response({'message': f'{count} opérations et historiques supprimées avec succès.'}, status=status.HTTP_200_OK)










class ListAcheteurProprieteActifView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        page_number = request.query_params.get('page', 1)
        search_term = request.query_params.get('search', '')

        propriete_list = ProprieteEtActif.objects.filter(
            acheteur_id=acheteur_id,
        ).order_by('-created_at')

        if search_term:
            propriete_list = propriete_list.filter(
                Q(locaux__icontains=search_term) |
                Q(locaux_ref__libelle__icontains=search_term) |
                Q(branche__icontains=search_term)
            )

        paginator = Paginator(propriete_list, 10)  # 10 enregistrements par page
        propriete_page = paginator.get_page(page_number)
        serializer = ProprieteEtActifSerializer(propriete_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': propriete_page.has_next(),
            'previous': propriete_page.has_previous()
        })

class SearchAcheteurProprieteActifView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        propriete_list = ProprieteEtActif.objects.filter(
            Q(acheteur_id=acheteur_id) & (
                Q(locaux__icontains=search_term) |
                Q(locaux_ref__libelle__icontains=search_term) |
                Q(branche__icontains=search_term)
            )
        ).order_by('-created_at')

        paginator = Paginator(propriete_list, 10)  # 10 enregistrements par page
        page_number = request.query_params.get('page', 1)
        propriete_page = paginator.get_page(page_number)
        serializer = ProprieteEtActifSerializer(propriete_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': propriete_page.has_next(),
            'previous': propriete_page.has_previous()
        })

class AddAcheteurProprieteActifView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, acheteur_id, *args, **kwargs):
        data = request.data.copy()
        data['acheteur'] = acheteur_id

        serializer = AddProprieteEtActifSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurProprieteActifView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, propriete_actif_id, *args, **kwargs):
        propriete = ProprieteEtActif.objects.filter(id=propriete_actif_id, acheteur_id=acheteur_id).first()
        if not propriete:
            return Response({'detail': 'Propriété et actif non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetProprieteEtActifSerializer(propriete)
        return Response(serializer.data)

    def put(self, request, acheteur_id, propriete_actif_id, *args, **kwargs):
        propriete = ProprieteEtActif.objects.filter(id=propriete_actif_id, acheteur_id=acheteur_id).first()
        if not propriete:
            return Response({'detail': 'Propriété et actif non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditProprieteEtActifSerializer(propriete, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurProprieteActifView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, acheteur_id, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        proprietes = ProprieteEtActif.objects.filter(id__in=ids, acheteur_id=acheteur_id)
        if not proprietes.exists():
            return Response({'error': 'Aucune propriété et actif trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = proprietes.delete()
        return Response({'message': f'{count} propriétés et actifs supprimés avec succès.'}, status=status.HTTP_200_OK)
