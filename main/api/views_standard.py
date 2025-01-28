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


# === Vues Standard === #


class ListDeviseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        devise_list = Devise.objects.filter(
            Q(nom__icontains=search_query) | Q(code__icontains=search_query)
        ).order_by('nom')

        paginator = Paginator(devise_list, 10)  # 10 éléments par page
        devise_page = paginator.get_page(page_number)
        serializer = DeviseSerializer(devise_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': devise_page.has_next(),
            'previous': devise_page.has_previous()
        })


class SearchDeviseView(APIView):
    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        devise_list = Devise.objects.filter(
            Q(nom__icontains=search_term) | Q(code__icontains=search_term)
        ).order_by('nom')

        paginator = Paginator(devise_list, 10)  # Nombre d'éléments par page
        page_number = request.query_params.get('page')
        devise_page = paginator.get_page(page_number)
        serializer = DeviseSerializer(devise_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': devise_page.has_next(),
            'previous': devise_page.has_previous()
        })


class AddDeviseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = DeviseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditDeviseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            devise = Devise.objects.get(id=id)
        except Devise.DoesNotExist:
            return Response({'detail': 'Devise non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DeviseSerializer(devise)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        try:
            devise = Devise.objects.get(id=id)
        except Devise.DoesNotExist:
            return Response({'detail': 'Devise non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DeviseSerializer(devise, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteDeviseView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids')
        if not ids:
            return Response({'detail': 'Aucun ID de devise fourni.'}, status=status.HTTP_400_BAD_REQUEST)

        devises = Devise.objects.filter(id__in=ids)
        if not devises.exists():
            return Response({'detail': 'Aucune devise trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        devises.delete()
        return Response({'detail': 'Les devises ont été supprimées avec succès.'}, status=status.HTTP_204_NO_CONTENT)


class ListAnneeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        annee_list = Annee.objects.filter(
            Q(annee__icontains=search_query)
        ).order_by('annee')

        paginator = Paginator(annee_list, 10)  # 10 éléments par page
        annee_page = paginator.get_page(page_number)
        serializer = AnneeSerializer(annee_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': annee_page.has_next(),
            'previous': annee_page.has_previous()
        })


class SearchAnneeView(APIView):
    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        annee_list = Annee.objects.filter(
            Q(annee__icontains=search_term)
        ).order_by('annee')

        paginator = Paginator(annee_list, 10)  # Nombre d'éléments par page
        page_number = request.query_params.get('page')
        annee_page = paginator.get_page(page_number)
        serializer = AnneeSerializer(annee_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': annee_page.has_next(),
            'previous': annee_page.has_previous()
        })


class AddAnneeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AnneeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditAnneeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            annee = Annee.objects.get(id=id)
        except Annee.DoesNotExist:
            return Response({'detail': 'Année non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AnneeSerializer(annee)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        try:
            annee = Annee.objects.get(id=id)
        except Annee.DoesNotExist:
            return Response({'detail': 'Année non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AnneeSerializer(annee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAnneeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids')
        if not ids:
            return Response({'detail': 'Aucun ID d\'année fourni.'}, status=status.HTTP_400_BAD_REQUEST)

        annees = Annee.objects.filter(id__in=ids)
        if not annees.exists():
            return Response({'detail': 'Aucune année trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        annees.delete()
        return Response({'detail': 'Les années ont été supprimées avec succès.'}, status=status.HTTP_204_NO_CONTENT)



class ListColorationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        coloration_list = CouleurCommentaire.objects.filter(
            Q(couleur__icontains=search_query) | Q(code__icontains=search_query)
        ).order_by('code')

        paginator = Paginator(coloration_list, 10)  # 10 éléments par page
        coloration_page = paginator.get_page(page_number)
        serializer = CouleurCommentaireSerializer(coloration_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': coloration_page.has_next(),
            'previous': coloration_page.has_previous()
        })
        
        
class SearchColorationView(APIView):
    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        coloration_list = CouleurCommentaire.objects.filter(
            Q(couleur__icontains=search_term) | Q(code__icontains=search_term)
        ).order_by('code')

        paginator = Paginator(coloration_list, 10)  # Nombre d'éléments par page
        page_number = request.query_params.get('page')
        coloration_page = paginator.get_page(page_number)
        serializer = CouleurCommentaireSerializer(coloration_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': coloration_page.has_next(),
            'previous': coloration_page.has_previous()
        })
        
        
class AddColorationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CouleurCommentaireSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class EditColorationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            coloration = CouleurCommentaire.objects.get(id=id)
        except CouleurCommentaire.DoesNotExist:
            return Response({'detail': 'Coloration non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CouleurCommentaireSerializer(coloration)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        try:
            coloration = CouleurCommentaire.objects.get(id=id)
        except CouleurCommentaire.DoesNotExist:
            return Response({'detail': 'Coloration non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CouleurCommentaireSerializer(coloration, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class DeleteColorationView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids')
        if not ids:
            return Response({'detail': 'Aucun ID de coloration fourni.'}, status=status.HTTP_400_BAD_REQUEST)

        colorations = CouleurCommentaire.objects.filter(id__in=ids)
        if not colorations.exists():
            return Response({'detail': 'Aucune coloration trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        colorations.delete()
        return Response({'detail': 'Les colorations ont été supprimées avec succès.'}, status=status.HTTP_204_NO_CONTENT)
    
    
    
class ListCategoryNaceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        category_list = CategoryNaceCode.objects.filter(
            Q(code__icontains=search_query) | Q(libelle__icontains=search_query)
        ).order_by('code')

        paginator = Paginator(category_list, 10)  # 10 éléments par page
        category_page = paginator.get_page(page_number)
        serializer = AddCategoryNaceCodeSerializer(category_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': category_page.has_next(),
            'previous': category_page.has_previous()
        })


class SearchCategoryNaceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        category_list = CategoryNaceCode.objects.filter(
            Q(code__icontains=search_term) | Q(libelle__icontains=search_term)
        ).order_by('code')

        paginator = Paginator(category_list, 10)
        page_number = request.query_params.get('page')
        category_page = paginator.get_page(page_number)
        serializer = AddCategoryNaceCodeSerializer(category_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': category_page.has_next(),
            'previous': category_page.has_previous()
        })


class AddCategoryNaceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddCategoryNaceCodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditCategoryNaceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            category = CategoryNaceCode.objects.get(id=id)
        except CategoryNaceCode.DoesNotExist:
            return Response({'detail': 'Catégorie non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AddCategoryNaceCodeSerializer(category)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        try:
            category = CategoryNaceCode.objects.get(id=id)
        except CategoryNaceCode.DoesNotExist:
            return Response({'detail': 'Catégorie non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AddCategoryNaceCodeSerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteCategoryNaceView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'detail': 'Liste des IDs manquante ou invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        categories = CategoryNaceCode.objects.filter(id__in=ids)
        deleted_count = categories.count()
        categories.delete()

        return Response({'detail': f'{deleted_count} catégorie(s) supprimée(s).'}, status=status.HTTP_200_OK)