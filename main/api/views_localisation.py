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


# === Vues Localisation === #

class ListPaysView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        pays_list = Pays.objects.filter(
            Q(nom__icontains=search_query) | Q(code__icontains=search_query)
        ).order_by('nom')

        paginator = Paginator(pays_list, 10)  # 10 items par page
        pays_page = paginator.get_page(page_number)
        serializer = PaysSerializer(pays_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': pays_page.has_next(),
            'previous': pays_page.has_previous()
        })
        
        
class SearchPaysView(APIView):
    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        pays = Pays.objects.filter(nom__icontains=search_term).order_by('nom')
        paginator = Paginator(pays, 10)  # Nombre d'éléments par page
        page_number = request.query_params.get('page')
        page_obj = paginator.get_page(page_number)
        serializer = PaysSerializer(page_obj, many=True)
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous()
        })


class AddPaysView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PaysSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditPaysView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            pays = Pays.objects.get(id=id)
        except Pays.DoesNotExist:
            return Response({'detail': 'Pays non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PaysSerializer(pays)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        try:
            pays = Pays.objects.get(id=id)
        except Pays.DoesNotExist:
            return Response({'detail': 'Pays non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PaysSerializer(pays, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeletePaysView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids')
        if not ids:
            return Response({'detail': 'Aucun ID de pays fourni.'}, status=status.HTTP_400_BAD_REQUEST)

        pays = Pays.objects.filter(id__in=ids)
        pays.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
class ListProvincesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)
        pays_id = request.query_params.get('pays')  # Récupère l'ID du pays depuis la requête

        provinces_list = Province.objects.all()

        # Filtrer par pays si un ID est fourni
        if pays_id:
            provinces_list = provinces_list.filter(pays_id=pays_id)

        # Filtrer par recherche si nécessaire
        if search_query:
            provinces_list = provinces_list.filter(
                Q(nom__icontains=search_query) | Q(code__icontains=search_query)
            )

        provinces_list = provinces_list.order_by('nom')

        paginator = Paginator(provinces_list, 10)  # 10 items par page
        provinces_page = paginator.get_page(page_number)
        serializer = ProvinceSerializer(provinces_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': provinces_page.has_next(),
            'previous': provinces_page.has_previous()
        })
        
class ListProvincesByCountryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        country_id = kwargs.get('country_id')
        provinces = Province.objects.filter(pays_id=country_id, is_active=True).order_by('nom')
        serializer = ProvinceSerializer(provinces, many=True)
        return Response(serializer.data)


class AddProvinceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddProvinceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class EditProvinceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            province = Province.objects.get(id=id)
        except Province.DoesNotExist:
            return Response({'detail': 'Province non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProvinceSerializer(province)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        try:
            province = Province.objects.get(id=id)
        except Province.DoesNotExist:
            return Response({'detail': 'Province non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateProvinceSerializer(province, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        print(serializer.errors)  # Ajoutez ce log
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteProvincesView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids')
        if not ids:
            return Response({'detail': 'Aucun ID de province fourni.'}, status=status.HTTP_400_BAD_REQUEST)

        provinces = Province.objects.filter(id__in=ids)
        provinces.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
class ListVillesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        villes_list = Ville.objects.filter(
            Q(nom__icontains=search_query) | Q(code__icontains=search_query)
        ).order_by('nom')

        paginator = Paginator(villes_list, 10)  # 10 items par page
        villes_page = paginator.get_page(page_number)
        serializer = VilleSerializer(villes_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': villes_page.has_next(),
            'previous': villes_page.has_previous()
        })

class AddVilleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddVilleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditVilleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            ville = Ville.objects.get(id=id)
        except Ville.DoesNotExist:
            return Response({'detail': 'Ville non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = VilleSerializer(ville)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        try:
            ville = Ville.objects.get(id=id)
        except Ville.DoesNotExist:
            return Response({'detail': 'Ville non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateVilleSerializer(ville, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteVillesView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids')
        if not ids:
            return Response({'detail': 'Aucun ID de ville fourni.'}, status=status.HTTP_400_BAD_REQUEST)

        villes = Ville.objects.filter(id__in=ids)
        deleted_count = villes.count()
        villes.delete()
        return Response({'detail': f'{deleted_count} ville(s) supprimée(s).'}, status=status.HTTP_204_NO_CONTENT)
    