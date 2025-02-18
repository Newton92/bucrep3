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



class ListModeleRapportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        modele_list = ModeleRapport.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        modele_page = paginator.get_page(page_number)
        serializer = ModeleRapportSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class SearchModeleRapportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        modele_list = ModeleRapport.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        modele_page = paginator.get_page(page_number)
        serializer = ModeleRapportSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class AddModeleRapportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ModeleRapportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditModeleRapportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        modele = ModeleRapport.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de rapport non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleRapportSerializer(modele)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        modele = ModeleRapport.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de rapport non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleRapportSerializer(modele, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteModeleRapportView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        modeles = ModeleRapport.objects.filter(id__in=ids)
        if not modeles.exists():
            return Response({'error': 'Aucun modèle de rapport trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = modeles.delete()
        return Response({'message': f'{count} modèles de rapport supprimés avec succès.'}, status=status.HTTP_200_OK)
    
    
    
    


class ListModeleAlarmeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        modele_list = ModeleAlarme.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        modele_page = paginator.get_page(page_number)
        serializer = ModeleAlarmeSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class SearchModeleAlarmeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        modele_list = ModeleAlarme.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        modele_page = paginator.get_page(page_number)
        serializer = ModeleAlarmeSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class AddModeleAlarmeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ModeleAlarmeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditModeleAlarmeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        modele = ModeleAlarme.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle d\'alarme non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleAlarmeSerializer(modele)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        modele = ModeleAlarme.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle d\'alarme non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleAlarmeSerializer(modele, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteModeleAlarmeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        modeles = ModeleAlarme.objects.filter(id__in=ids)
        if not modeles.exists():
            return Response({'error': 'Aucun modèle d\'alarme trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = modeles.delete()
        return Response({'message': f'{count} modèles d\'alarme supprimés avec succès.'}, status=status.HTTP_200_OK)
    
    
    
    




class ListModeleBilanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        modele_list = ModeleBilan.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        modele_page = paginator.get_page(page_number)
        serializer = ModeleBilanSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class SearchModeleBilanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        modele_list = ModeleBilan.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        modele_page = paginator.get_page(page_number)
        serializer = ModeleBilanSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class AddModeleBilanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ModeleBilanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditModeleBilanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        modele = ModeleBilan.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de bilan non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleBilanSerializer(modele)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        modele = ModeleBilan.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de bilan non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleBilanSerializer(modele, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteModeleBilanView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        modeles = ModeleBilan.objects.filter(id__in=ids)
        if not modeles.exists():
            return Response({'error': 'Aucun modèle de bilan trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = modeles.delete()
        return Response({'message': f'{count} modèles de bilan supprimés avec succès.'}, status=status.HTTP_200_OK)
    
    
    
    
    
    
    
    


class ListModeleBailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        modele_list = ModeleBail.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        modele_page = paginator.get_page(page_number)
        serializer = ModeleBailSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class SearchModeleBailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        modele_list = ModeleBail.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        modele_page = paginator.get_page(page_number)
        serializer = ModeleBailSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class AddModeleBailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ModeleBailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditModeleBailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        modele = ModeleBail.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de bail non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleBailSerializer(modele)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        modele = ModeleBail.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de bail non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleBailSerializer(modele, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteModeleBailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        modeles = ModeleBail.objects.filter(id__in=ids)
        if not modeles.exists():
            return Response({'error': 'Aucun modèle de bail trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = modeles.delete()
        return Response({'message': f'{count} modèles de bail supprimés avec succès.'}, status=status.HTTP_200_OK)
    
    
    
    
    
    
    
    
    
    
    


class ListModeleNotationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        modele_list = ModeleNotation.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        modele_page = paginator.get_page(page_number)
        serializer = ModeleNotationSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class SearchModeleNotationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        modele_list = ModeleNotation.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        modele_page = paginator.get_page(page_number)
        serializer = ModeleNotationSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class AddModeleNotationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ModeleNotationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditModeleNotationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        modele = ModeleNotation.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de notation non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleNotationSerializer(modele)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        modele = ModeleNotation.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de notation non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleNotationSerializer(modele, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteModeleNotationView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        modeles = ModeleNotation.objects.filter(id__in=ids)
        if not modeles.exists():
            return Response({'error': 'Aucun modèle de notation trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = modeles.delete()
        return Response({'message': f'{count} modèles de notation supprimés avec succès.'}, status=status.HTTP_200_OK)
    
    
    
    




class ListModeleAvisCommercialView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        modele_list = ModeleAvisCommercial.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        modele_page = paginator.get_page(page_number)
        serializer = ModeleAvisCommercialSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class SearchModeleAvisCommercialView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        modele_list = ModeleAvisCommercial.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        modele_page = paginator.get_page(page_number)
        serializer = ModeleAvisCommercialSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class AddModeleAvisCommercialView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ModeleAvisCommercialSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditModeleAvisCommercialView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        modele = ModeleAvisCommercial.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle d\'avis commercial non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleAvisCommercialSerializer(modele)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        modele = ModeleAvisCommercial.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle d\'avis commercial non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleAvisCommercialSerializer(modele, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteModeleAvisCommercialView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        modeles = ModeleAvisCommercial.objects.filter(id__in=ids)
        if not modeles.exists():
            return Response({'error': 'Aucun modèle d\'avis commercial trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = modeles.delete()
        return Response({'message': f'{count} modèles d\'avis commercial supprimés avec succès.'}, status=status.HTTP_200_OK)
    
    
    
    
    
    



class ListModeleRelationEntrepriseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        modele_list = ModeleRelationEntreprise.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        modele_page = paginator.get_page(page_number)
        serializer = ModeleRelationEntrepriseSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class SearchModeleRelationEntrepriseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        modele_list = ModeleRelationEntreprise.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        modele_page = paginator.get_page(page_number)
        serializer = ModeleRelationEntrepriseSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class AddModeleRelationEntrepriseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ModeleRelationEntrepriseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditModeleRelationEntrepriseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        modele = ModeleRelationEntreprise.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de relation entreprise non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleRelationEntrepriseSerializer(modele)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        modele = ModeleRelationEntreprise.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de relation entreprise non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleRelationEntrepriseSerializer(modele, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteModeleRelationEntrepriseView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        modeles = ModeleRelationEntreprise.objects.filter(id__in=ids)
        if not modeles.exists():
            return Response({'error': 'Aucun modèle de relation entreprise trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = modeles.delete()
        return Response({'message': f'{count} modèles de relation entreprise supprimés avec succès.'}, status=status.HTTP_200_OK)
    
    
    
    
    
    
    
    
    
    
    
    
    

class ListModeleInformationNotationEntrepriseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        modele_list = ModeleInformationNotationEntreprise.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        modele_page = paginator.get_page(page_number)
        serializer = ModeleInformationNotationEntrepriseSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class SearchModeleInformationNotationEntrepriseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        modele_list = ModeleInformationNotationEntreprise.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        modele_page = paginator.get_page(page_number)
        serializer = ModeleInformationNotationEntrepriseSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class AddModeleInformationNotationEntrepriseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ModeleInformationNotationEntrepriseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditModeleInformationNotationEntrepriseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        modele = ModeleInformationNotationEntreprise.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle d\'information sur notation entreprise non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleInformationNotationEntrepriseSerializer(modele)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        modele = ModeleInformationNotationEntreprise.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle d\'information sur notation entreprise non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleInformationNotationEntrepriseSerializer(modele, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteModeleInformationNotationEntrepriseView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        modeles = ModeleInformationNotationEntreprise.objects.filter(id__in=ids)
        if not modeles.exists():
            return Response({'error': 'Aucun modèle d\'information sur notation entreprise trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = modeles.delete()
        return Response({'message': f'{count} modèles d\'information sur notation entreprise supprimés avec succès.'}, status=status.HTTP_200_OK)
    
    
    
    
    
    
    
    
    
    
    
    
    


class ListModeleComportementPaiementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        modele_list = ModeleComportementPaiement.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        modele_page = paginator.get_page(page_number)
        serializer = ModeleComportementPaiementSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class SearchModeleComportementPaiementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        modele_list = ModeleComportementPaiement.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        modele_page = paginator.get_page(page_number)
        serializer = ModeleComportementPaiementSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class AddModeleComportementPaiementView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ModeleComportementPaiementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditModeleComportementPaiementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        modele = ModeleComportementPaiement.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de comportement de paiement non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleComportementPaiementSerializer(modele)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        modele = ModeleComportementPaiement.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de comportement de paiement non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleComportementPaiementSerializer(modele, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteModeleComportementPaiementView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        modeles = ModeleComportementPaiement.objects.filter(id__in=ids)
        if not modeles.exists():
            return Response({'error': 'Aucun modèle de comportement de paiement trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = modeles.delete()
        return Response({'message': f'{count} modèles de comportement de paiement supprimés avec succès.'}, status=status.HTTP_200_OK)









class ListModeleComportementJugementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        modele_list = ModeleComportementJugement.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        modele_page = paginator.get_page(page_number)
        serializer = ModeleComportementJugementSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class SearchModeleComportementJugementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        modele_list = ModeleComportementJugement.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term)
        ).order_by('libelle')

        paginator = Paginator(modele_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        modele_page = paginator.get_page(page_number)
        serializer = ModeleComportementJugementSerializer(modele_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': modele_page.has_next(),
            'previous': modele_page.has_previous()
        })

class AddModeleComportementJugementView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ModeleComportementJugementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditModeleComportementJugementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        modele = ModeleComportementJugement.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de comportement de jugement non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleComportementJugementSerializer(modele)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        modele = ModeleComportementJugement.objects.filter(id=id).first()
        if not modele:
            return Response({'detail': 'Modèle de comportement de jugement non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModeleComportementJugementSerializer(modele, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteModeleComportementJugementView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        modeles = ModeleComportementJugement.objects.filter(id__in=ids)
        if not modeles.exists():
            return Response({'error': 'Aucun modèle de comportement de jugement trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = modeles.delete()
        return Response({'message': f'{count} modèles de comportement de jugement supprimés avec succès.'}, status=status.HTTP_200_OK)
