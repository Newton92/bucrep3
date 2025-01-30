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
    
    
class ListCategoryNafView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        category_list = CategoryNafCode.objects.filter(
            Q(code__icontains=search_query) | Q(libelle__icontains=search_query)
        ).order_by('code')

        paginator = Paginator(category_list, 10)  # 10 éléments par page
        category_page = paginator.get_page(page_number)
        serializer = AddCategoryNafCodeSerializer(category_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': category_page.has_next(),
            'previous': category_page.has_previous()
        })
        
        
class SearchCategoryNafView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        category_list = CategoryNafCode.objects.filter(
            Q(code__icontains=search_term) | Q(libelle__icontains=search_term)
        ).order_by('code')

        paginator = Paginator(category_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        category_page = paginator.get_page(page_number)
        serializer = AddCategoryNafCodeSerializer(category_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': category_page.has_next(),
            'previous': category_page.has_previous()
        })
        
        
class AddCategoryNafView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddCategoryNafCodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class EditCategoryNafView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        category = CategoryNafCode.objects.filter(id=id).first()
        if not category:
            return Response({'detail': 'Catégorie NAF non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AddCategoryNafCodeSerializer(category)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        category = CategoryNafCode.objects.filter(id=id).first()
        if not category:
            return Response({'detail': 'Catégorie NAF non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AddCategoryNafCodeSerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class DeleteCategoryNafView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        categories = CategoryNafCode.objects.filter(id__in=ids)
        if not categories.exists():
            return Response({'error': 'Aucune catégorie trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = categories.delete()
        return Response({'message': f'{count} catégories supprimées avec succès.'}, status=status.HTTP_200_OK)


class ListCodeNaceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)
        
        subcategory_list = SubCategoryNaceCode.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query) |
            Q(category__code__icontains=search_query) |
            Q(category__libelle__icontains=search_query)
        ).order_by('code')
        
        paginator = Paginator(subcategory_list, 10)  # 10 éléments par page
        subcategory_page = paginator.get_page(page_number)
        serializer = SubCategoryNaceCodeSerializer(subcategory_page, many=True)
        
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': subcategory_page.has_next(),
            'previous': subcategory_page.has_previous()
        })


class SearchCodeNaceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)
        
        subcategory_list = SubCategoryNaceCode.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term) |
            Q(category__code__icontains=search_term) |
            Q(category__libelle__icontains=search_term)
        ).order_by('code')

        paginator = Paginator(subcategory_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        subcategory_page = paginator.get_page(page_number)
        serializer = SubCategoryNaceCodeSerializer(subcategory_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': subcategory_page.has_next(),
            'previous': subcategory_page.has_previous()
        })


class AddCodeNaceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddSubCategoryNaceCodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditCodeNaceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        subcategory = SubCategoryNaceCode.objects.filter(id=id).first()
        if not subcategory:
            return Response({'detail': 'Sous-catégorie NAF non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditSubCategoryNaceCodeSerializer(subcategory)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        subcategory = SubCategoryNaceCode.objects.filter(id=id).first()
        if not subcategory:
            return Response({'detail': 'Sous-catégorie NAF non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditSubCategoryNaceCodeSerializer(subcategory, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteCodeNaceView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        subcategories = SubCategoryNaceCode.objects.filter(id__in=ids)
        if not subcategories.exists():
            return Response({'error': 'Aucune sous-catégorie trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = subcategories.delete()
        return Response({'message': f'{count} sous-catégories supprimées avec succès.'}, status=status.HTTP_200_OK)



class ListCodeNafView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)
        
        subcategory_list = SubCategoryNafCode.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query) |
            Q(category__code__icontains=search_query) |
            Q(category__libelle__icontains=search_query)
        ).order_by('code')
        
        paginator = Paginator(subcategory_list, 10)  # 10 éléments par page
        subcategory_page = paginator.get_page(page_number)
        serializer = SubCategoryNafCodeSerializer(subcategory_page, many=True)
        
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': subcategory_page.has_next(),
            'previous': subcategory_page.has_previous()
        })


class SearchCodeNafView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)
        
        subcategory_list = SubCategoryNafCode.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term) |
            Q(category__code__icontains=search_term) |
            Q(category__libelle__icontains=search_term)
        ).order_by('code')

        paginator = Paginator(subcategory_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        subcategory_page = paginator.get_page(page_number)
        serializer = SubCategoryNafCodeSerializer(subcategory_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': subcategory_page.has_next(),
            'previous': subcategory_page.has_previous()
        })


class AddCodeNafView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddSubCategoryNafCodeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditCodeNafView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        subcategory = SubCategoryNafCode.objects.filter(id=id).first()
        if not subcategory:
            return Response({'detail': 'Sous-catégorie NAF non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditSubCategoryNafCodeSerializer(subcategory)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        subcategory = SubCategoryNafCode.objects.filter(id=id).first()
        if not subcategory:
            return Response({'detail': 'Sous-catégorie NAF non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditSubCategoryNafCodeSerializer(subcategory, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteCodeNafView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        subcategories = SubCategoryNafCode.objects.filter(id__in=ids)
        if not subcategories.exists():
            return Response({'error': 'Aucune sous-catégorie trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = subcategories.delete()
        return Response({'message': f'{count} sous-catégories supprimées avec succès.'}, status=status.HTTP_200_OK)


class ListFormeJuridiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        forme_juridique_list = FormeJuridique.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query) |
            Q(description__icontains=search_query)
        ).order_by('code')

        paginator = Paginator(forme_juridique_list, 10)  # 10 éléments par page
        forme_juridique_page = paginator.get_page(page_number)
        serializer = FormeJuridiqueSerializer(forme_juridique_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': forme_juridique_page.has_next(),
            'previous': forme_juridique_page.has_previous()
        })
        
        
class SearchFormeJuridiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        forme_juridique_list = FormeJuridique.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term) |
            Q(description__icontains=search_term)
        ).order_by('code')

        paginator = Paginator(forme_juridique_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        forme_juridique_page = paginator.get_page(page_number)
        serializer = FormeJuridiqueSerializer(forme_juridique_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': forme_juridique_page.has_next(),
            'previous': forme_juridique_page.has_previous()
        })


class AddFormeJuridiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = FormeJuridiqueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditFormeJuridiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        forme_juridique = FormeJuridique.objects.filter(id=id).first()
        if not forme_juridique:
            return Response({'detail': 'Forme juridique non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = FormeJuridiqueSerializer(forme_juridique)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        forme_juridique = FormeJuridique.objects.filter(id=id).first()
        if not forme_juridique:
            return Response({'detail': 'Forme juridique non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = FormeJuridiqueSerializer(forme_juridique, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteFormeJuridiqueView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        formes_juridiques = FormeJuridique.objects.filter(id__in=ids)
        if not formes_juridiques.exists():
            return Response({'error': 'Aucune forme juridique trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = formes_juridiques.delete()
        return Response({'message': f'{count} formes juridiques supprimées avec succès.'}, status=status.HTTP_200_OK)


class ListDomaineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        domaine_list = DomaineEntreprise.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query) |
            Q(description__icontains=search_query)
        ).order_by('libelle')

        paginator = Paginator(domaine_list, 10)  # 10 éléments par page
        domaine_page = paginator.get_page(page_number)
        serializer = DomaineEntrepriseSerializer(domaine_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': domaine_page.has_next(),
            'previous': domaine_page.has_previous()
        })

class SearchDomaineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        domaine_list = DomaineEntreprise.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term) |
            Q(description__icontains=search_term)
        ).order_by('libelle')

        paginator = Paginator(domaine_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        domaine_page = paginator.get_page(page_number)
        serializer = DomaineEntrepriseSerializer(domaine_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': domaine_page.has_next(),
            'previous': domaine_page.has_previous()
        })

class AddDomaineView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = DomaineEntrepriseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditDomaineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        domaine = DomaineEntreprise.objects.filter(id=id).first()
        if not domaine:
            return Response({'detail': 'Domaine entreprise non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DomaineEntrepriseSerializer(domaine)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        domaine = DomaineEntreprise.objects.filter(id=id).first()
        if not domaine:
            return Response({'detail': 'Domaine entreprise non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DomaineEntrepriseSerializer(domaine, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteDomaineView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        domaines = DomaineEntreprise.objects.filter(id__in=ids)
        if not domaines.exists():
            return Response({'error': 'Aucun domaine entreprise trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = domaines.delete()
        return Response({'message': f'{count} domaines entreprise supprimés avec succès.'}, status=status.HTTP_200_OK)


class ListPosteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        poste_list = PosteEntreprise.objects.filter(
            Q(code__icontains=search_query) |
            Q(libelle__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(domaine__code__icontains=search_query) |
            Q(domaine__libelle__icontains=search_query)
        ).order_by('libelle')

        paginator = Paginator(poste_list, 10)  # 10 éléments par page
        poste_page = paginator.get_page(page_number)
        serializer = PosteEntrepriseSerializer(poste_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': poste_page.has_next(),
            'previous': poste_page.has_previous()
        })

class SearchPosteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        poste_list = PosteEntreprise.objects.filter(
            Q(code__icontains=search_term) |
            Q(libelle__icontains=search_term) |
            Q(description__icontains=search_term) |
            Q(domaine__code__icontains=search_term) |
            Q(domaine__libelle__icontains=search_term)
        ).order_by('libelle')

        paginator = Paginator(poste_list, 10)  # 10 éléments par page
        page_number = request.query_params.get('page', 1)
        poste_page = paginator.get_page(page_number)
        serializer = PosteEntrepriseSerializer(poste_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': poste_page.has_next(),
            'previous': poste_page.has_previous()
        })

class AddPosteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddPosteEntrepriseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditPosteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        poste = PosteEntreprise.objects.filter(id=id).first()
        if not poste:
            return Response({'detail': 'Poste entreprise non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditPosteEntrepriseSerializer(poste)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        poste = PosteEntreprise.objects.filter(id=id).first()
        if not poste:
            return Response({'detail': 'Poste entreprise non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditPosteEntrepriseSerializer(poste, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeletePosteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        postes = PosteEntreprise.objects.filter(id__in=ids)
        if not postes.exists():
            return Response({'error': 'Aucun poste entreprise trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = postes.delete()
        return Response({'message': f'{count} postes entreprise supprimés avec succès.'}, status=status.HTTP_200_OK)
