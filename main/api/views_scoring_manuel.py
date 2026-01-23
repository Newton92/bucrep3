# views_scoring_manuel.py

from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from main.serializers import *
from main.models import ScoringSansBilanAcheteur, Acheteur, ActifC, PassifC, ResultatC, Scoring, Annee
from main.serializers import ScoringSansBilanAcheteurSerializer, BilanClassiqueScoreSerializer, ScoringSerializer
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from main.models import ScoringSansBilanAcheteur, Acheteur, Scoring
from main.serializers import ScoringSansBilanAcheteurSerializer, ScoringSerializer
from decimal import Decimal
from typing import Dict, Tuple, Optional
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

# Ajoutez cette classe de pagination personnalisée
class NoPagination(PageNumberPagination):
    page_size = None

# views_scoring.py - Corrigez la classe ScoringListView

class ScoringListView(ListAPIView):
    """Liste des scorings manuels avec filtrage"""
    serializer_class = ScoringSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        queryset = Scoring.objects.select_related(
            'annee', 'acheteur', 'created_by'
        ).order_by('-created_at')
        
        # Filtrage par acheteur
        acheteur_id = self.request.query_params.get('acheteur_id')
        if acheteur_id:
            # Vérifier si l'acheteur existe
            try:
                acheteur = Acheteur.objects.get(id=int(acheteur_id))
                queryset = queryset.filter(acheteur=acheteur)
            except (ValueError, Acheteur.DoesNotExist):
                # Si l'acheteur n'existe pas, retourner un queryset vide
                return Scoring.objects.none()
        
        # Filtrage par année - CORRECTION ICI
        annee_id = self.request.query_params.get('annee_id')
        if annee_id and annee_id != 'undefined' and annee_id != '':
            try:
                annee_id_int = int(annee_id)
                queryset = queryset.filter(annee_id=annee_id_int)
            except (ValueError, TypeError):
                pass  # Ignorer les valeurs invalides
        
        # Filtrage par score - CORRECTION ICI
        score_min = self.request.query_params.get('score_min')
        score_max = self.request.query_params.get('score_max')
        
        if score_min and score_min != 'undefined' and score_min != '':
            try:
                score_min_float = float(score_min)
                queryset = queryset.filter(score__gte=str(score_min_float))
            except (ValueError, TypeError):
                pass
        
        if score_max and score_max != 'undefined' and score_max != '':
            try:
                score_max_float = float(score_max)
                queryset = queryset.filter(score__lte=str(score_max_float))
            except (ValueError, TypeError):
                pass
        
        # Recherche par nom d'acheteur - CORRECTION ICI
        search = self.request.query_params.get('search')
        if search and search != 'undefined' and search != '':
            queryset = queryset.filter(
                Q(acheteur__nom__icontains=search) |
                Q(acheteur__sigle__icontains=search) |
                Q(commentaire__icontains=search)
            )
        
        return queryset
    
    def get(self, request, *args, **kwargs):
        print(f"📡 API Scoring manuel appelée, {self.get_queryset().count()} éléments")
        return super().get(request, *args, **kwargs)
    

class ScoringDetailView(RetrieveUpdateDestroyAPIView):
    """Détail, mise à jour et suppression d'un scoring manuel"""
    serializer_class = ScoringSerializer
    permission_classes = [IsAuthenticated]
    queryset = Scoring.objects.all()
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    def perform_destroy(self, instance):
        instance.delete()


class ScoringCreateView(CreateAPIView):
    """Création d'un nouveau scoring manuel"""
    serializer_class = ScoringSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ScoringByAcheteurAnneeView(APIView):
    """Récupérer ou créer un scoring pour un acheteur et une année spécifiques"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, acheteur_id, annee_id):
        try:
            scoring = Scoring.objects.get(
                acheteur_id=acheteur_id,
                annee_id=annee_id
            )
            serializer = ScoringSerializer(scoring)
            return Response(serializer.data)
        except Scoring.DoesNotExist:
            return Response(
                {'detail': _('Scoring non trouvé')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request, acheteur_id, annee_id):
        # Vérifier si un scoring existe déjà
        existing_scoring = Scoring.objects.filter(
            acheteur_id=acheteur_id,
            annee_id=annee_id
        ).first()
        
        if existing_scoring:
            serializer = ScoringSerializer(
                existing_scoring,
                data=request.data,
                partial=True
            )
        else:
            data = request.data.copy()
            data['acheteur_id'] = acheteur_id
            data['annee_id'] = annee_id
            serializer = ScoringSerializer(data=data)
        
        if serializer.is_valid():
            if existing_scoring:
                serializer.save(updated_by=request.user)
            else:
                serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AnneeListView(ListAPIView):
    """Liste des années pour le formulaire"""
    queryset = Annee.objects.filter(is_active=True).order_by('-annee')
    serializer_class = serializers.SerializerMethodField()
    permission_classes = [IsAuthenticated]
    pagination_class = NoPagination
    
    def get_serializer_class(self):
        return serializers.Serializer
    
    def get(self, request, *args, **kwargs):
        annees = self.get_queryset()
        data = [
            {
                'id': annee.id,
                'annee': annee.annee,
                'is_active': annee.is_active
            }
            for annee in annees
        ]
        return Response(data)


class ScoringStatsView(APIView):
    """Statistiques sur les scorings manuels"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        total = Scoring.objects.count()
        
        # Distribution par catégorie
        categories = {
            'excellent': Scoring.objects.filter(score__gte='8').count(),
            'bon': Scoring.objects.filter(score__gte='6', score__lt='8').count(),
            'moyen': Scoring.objects.filter(score__gte='4', score__lt='6').count(),
            'faible': Scoring.objects.filter(score__gte='2', score__lt='4').count(),
            'tres_faible': Scoring.objects.filter(score__lt='2').count(),
        }
        
        # Derniers scorings
        derniers = Scoring.objects.select_related('acheteur', 'annee') \
            .order_by('-created_at')[:5]
        
        derniers_data = [
            {
                'id': s.id,
                'acheteur': s.acheteur.nom if s.acheteur else '',
                'annee': s.annee.annee if s.annee else '',
                'score': s.score,
                'created_at': s.created_at
            }
            for s in derniers
        ]
        
        return Response({
            'total': total,
            'categories': categories,
            'derniers': derniers_data
        })