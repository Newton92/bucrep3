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


# === Vues Warning === #



class ListAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        alerte_list = Alerte.objects.filter(
            Q(reference__icontains=search_query) |
            Q(objet__icontains=search_query) |
            Q(content__icontains=search_query)
        ).order_by('-created_at')

        paginator = Paginator(alerte_list, 10)
        alerte_page = paginator.get_page(page_number)
        serializer = AlerteSerializer(alerte_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': alerte_page.has_next(),
            'previous': alerte_page.has_previous()
        })

class SearchAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_term = request.query_params.get('search', '')
        if not search_term:
            return Response({'detail': 'Terme de recherche manquant.'}, status=status.HTTP_400_BAD_REQUEST)

        alerte_list = Alerte.objects.filter(
            Q(reference__icontains=search_term) |
            Q(objet__icontains=search_term) |
            Q(content__icontains=search_term)
        ).order_by('-created_at')

        paginator = Paginator(alerte_list, 10)
        page_number = request.query_params.get('page', 1)
        alerte_page = paginator.get_page(page_number)
        serializer = AlerteSerializer(alerte_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': alerte_page.has_next(),
            'previous': alerte_page.has_previous()
        })

class AddAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddAlerteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        alerte = Alerte.objects.filter(id=id).first()
        if not alerte:
            return Response({'detail': 'Alerte non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AlerteSerializer(alerte)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        alerte = Alerte.objects.filter(id=id).first()
        if not alerte:
            return Response({'detail': 'Alerte non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditAlerteSerializer(alerte, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        alertes = Alerte.objects.filter(id__in=ids)
        if not alertes.exists():
            return Response({'error': 'Aucune alerte trouvée pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = alertes.delete()
        return Response({'message': f'{count} alertes supprimées avec succès.'}, status=status.HTTP_200_OK)

class GetAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        alerte = Alerte.objects.filter(id=id).first()
        if not alerte:
            return Response({'detail': 'Alerte non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AlerteSerializer(alerte)
        return Response(serializer.data)

class ListDocumentAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get('search', '')
        page_number = request.query_params.get('page', 1)

        document_list = DocumentAlerte.objects.filter(
            Q(titre__icontains=search_query) |
            Q(alerte__reference__icontains=search_query)
        ).order_by('-created_at')

        paginator = Paginator(document_list, 10)
        document_page = paginator.get_page(page_number)
        serializer = DocumentAlerteSerializer(document_page, many=True)

        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': document_page.has_next(),
            'previous': document_page.has_previous()
        })

class AddDocumentAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AddDocumentAlerteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EditDocumentAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        document = DocumentAlerte.objects.filter(id=id).first()
        if not document:
            return Response({'detail': 'Document non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DocumentAlerteSerializer(document)
        return Response(serializer.data)

    def put(self, request, id, *args, **kwargs):
        document = DocumentAlerte.objects.filter(id=id).first()
        if not document:
            return Response({'detail': 'Document non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditDocumentAlerteSerializer(document, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteDocumentAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response({'error': 'Une liste d\'IDs est requise.'}, status=status.HTTP_400_BAD_REQUEST)

        documents = DocumentAlerte.objects.filter(id__in=ids)
        if not documents.exists():
            return Response({'error': 'Aucun document trouvé pour les IDs fournis.'}, status=status.HTTP_404_NOT_FOUND)

        count, _ = documents.delete()
        return Response({'message': f'{count} documents supprimés avec succès.'}, status=status.HTTP_200_OK)

class GetDocumentAlerteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        document = DocumentAlerte.objects.filter(id=id).first()
        if not document:
            return Response({'detail': 'Document non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DocumentAlerteSerializer(document)
        return Response(serializer.data)
