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


# === Vues Acheteur === #


class ListAcheteurView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        acheteur_list = Acheteur.objects.filter(
            Q(code__icontains=search_query) |
            Q(nom__icontains=search_query) |
            Q(sigle__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(numero_adresse__icontains=search_query) |
            Q(site_internet__icontains=search_query) |
            Q(rue_adresse__icontains=search_query) |
            Q(activite_principale__icontains=search_query) |
            Q(categorie_entreprise__libelle__icontains=search_query) |
            Q(forme_juridique__libelle__icontains=search_query) |
            Q(statut_entreprise__libelle__icontains=search_query) |
            Q(pays__nom__icontains=search_query) |
            Q(province__nom__icontains=search_query) |
            Q(ville__nom__icontains=search_query)
        ).order_by('nom')
        
        print(str(acheteur_list.query))  # Affiche la requête SQL exécutée

        paginator = Paginator(acheteur_list, 10)  # 10 éléments par page
        acheteur_page = paginator.get_page(page_number)
        serializer = AcheteurSerializer(acheteur_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': acheteur_page.has_next(),
            'previous': acheteur_page.has_previous()
        })


class SearchAcheteurView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        acheteur_list = Acheteur.objects.filter(
            Q(code__icontains=search_term) |
            Q(nom__icontains=search_term) |
            Q(sigle__icontains=search_term) |
            Q(email__icontains=search_term) |
            Q(numero_adresse__icontains=search_term) |
            Q(site_internet__icontains=search_term) |
            Q(rue_adresse__icontains=search_term) |
            Q(activite_principale__icontains=search_term) |
            Q(ville__icontains=search_term) |
            Q(province__icontains=search_term) |
            Q(pays__icontains=search_term) |
            Q(couleur_commentaire__icontains=search_term) |
            Q(commentaire__icontains=search_term) |
            Q(categorie_entreprise__code__icontains=search_term) |
            Q(categorie_entreprise__libelle__icontains=search_term) |
            Q(forme_juridique__code__icontains=search_term) |
            Q(forme_juridique__libelle__icontains=search_term) |
            Q(statut_entreprise__code__icontains=search_term) |
            Q(statut_entreprise__libelle__icontains=search_term) |
            Q(pays__code__icontains=search_term) |
            Q(pays__nom__icontains=search_term) |
            Q(province__code__icontains=search_term) |
            Q(province__nom__icontains=search_term) |
            Q(ville__code__icontains=search_term) |
            Q(ville__nom__icontains=search_term) |
            Q(statut_entreprise__code__icontains=search_term) 
        ).order_by('nom')

        paginator = Paginator(acheteur_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        acheteur_page = paginator.get_page(page_number)
        serializer = AcheteurSerializer(acheteur_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': acheteur_page.has_next(),
            'previous': acheteur_page.has_previous()
        })

class AddAcheteurView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddAcheteurSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAcheteurView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        acheteur = Acheteur.objects.filter(id=id).first()
        if not acheteur:
            return Response({'detail': 'Acheteur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditAcheteurSerializer(acheteur)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        acheteur = Acheteur.objects.filter(id=id).first()
        if not acheteur:
            return Response({'detail': 'Acheteur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditAcheteurSerializer(acheteur, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAcheteurView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        acheteurs = Acheteur.objects.filter(id__in=ids)
        if not acheteurs.exists():
            return Response({'error': 'Aucun acheteur trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = acheteurs.delete()
        return Response({'message': f'{count} acheteurs supprimés avec succès.'}, status=status.HTTP_200_OK)
    
    
class GetAcheteurView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        acheteur = Acheteur.objects.filter(id=id).first()
        if not acheteur:
            return Response({'detail': 'Acheteur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetAcheteurSerializer(acheteur)
        return Response(serializer.data)
