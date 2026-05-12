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
from django.http import Http404
# views_scoring_manuel.py - AJOUTEZ CET IMPORT EN HAUT DU FICHIER

from django.db import IntegrityError
from django.db import transaction

import logging

logger = logging.getLogger(__name__)


import json

class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Log des réponses API qui ne sont pas du JSON
        if request.path.startswith('/api/') and 'application/json' not in response.get('Content-Type', ''):
            print(f"⚠️  API {request.path} retourne non-JSON: {response.status_code}")
            print(f"   Content-Type: {response.get('Content-Type')}")
            
        return response

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
    
    def get_serializer_context(self):
        """Ajouter request au contexte"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def update(self, request, *args, **kwargs):
        """Mise à jour d'un scoring existant"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        print(f"📝 Mise à jour du scoring ID: {instance.id}")
        print(f"📦 Données reçues: {request.data}")
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Mettre à jour updated_by
                    serializer.save(updated_by=request.user)
                    
                print(f"✅ Scoring {instance.id} mis à jour avec succès")
                
                return Response({
                    'success': True,
                    'message': 'Scoring mis à jour avec succès',
                    'data': serializer.data,
                    'is_update': True,
                    'scoring_id': instance.id
                })
            except IntegrityError as e:
                print(f"❌ Erreur d'intégrité: {e}")
                return Response({
                    'detail': 'Erreur de contrainte unique',
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"❌ Erreurs de validation: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, *args, **kwargs):
        """Récupérer un scoring spécifique"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Http404:
            return Response(
                {'detail': f"Scoring avec ID {kwargs.get('pk')} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )


# views_scoring_manuel.py - CORRECTION COMPLÈTE DE ScoringCreateView

class ScoringCreateView(CreateAPIView):
    """Création d'un nouveau scoring manuel"""
    serializer_class = ScoringSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_context(self):
        """Ajouter request au contexte"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def create(self, request, *args, **kwargs):
        print("📦 Données reçues:", request.data)
        
        data = request.data.copy()
        
        # Vérifier les doublons
        annee_id = data.get('annee')
        acheteur_id = data.get('acheteur')
        
        if annee_id and acheteur_id:
            existing_scoring = Scoring.objects.filter(
                annee_id=annee_id,
                acheteur_id=acheteur_id
            ).first()
            
            if existing_scoring:
                return Response(
                    {
                        'detail': 'Un scoring existe déjà.',
                        'existing_scoring_id': existing_scoring.id
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Créer normalement
        serializer = self.get_serializer(data=data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {'detail': 'Un scoring existe déjà pour cette combinaison.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




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
        
        
        
# views_scoring_manuel.py - CORRECTION DE CreateOrUpdateScoringView
# views_scoring_manuel.py
# views_scoring_manuel.py - VERSION CORRIGÉE
class CreateOrUpdateScoringView(APIView):
    """Créer ou mettre à jour un scoring de manière atomique"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            
            # Validation des champs requis
            required_fields = ['annee', 'acheteur', 'score']
            missing_fields = [f for f in required_fields if not data.get(f)]
            
            if missing_fields:
                return Response(
                    {'detail': f'Champs manquants: {", ".join(missing_fields)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Conversion et validation des IDs
            try:
                annee_id = int(data['annee'])
                acheteur_id = int(data['acheteur'])
                score = str(data['score'])  # Garder en string pour le modèle actuel
            except (ValueError, TypeError) as e:
                return Response(
                    {'detail': f'Données invalides: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Vérifier que l'année et l'acheteur existent
            try:
                annee = Annee.objects.get(id=annee_id)
                acheteur = Acheteur.objects.get(id=acheteur_id)
            except (Annee.DoesNotExist, Acheteur.DoesNotExist) as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Transaction atomique pour create_or_update
            with transaction.atomic():
                # CORRECTION : Chercher AUSSI dans les soft-deleted
                try:
                    # Essayer de récupérer l'enregistrement (même soft-deleted)
                    scoring = Scoring.all_objects.get(
                        annee=annee,
                        acheteur=acheteur
                    )
                    
                    # Si trouvé et soft-deleted, le "restaurer"
                    if scoring.deleted:
                        scoring.undelete()
                        logger.info(f"Scoring {scoring.id} restauré depuis soft-delete")
                    
                    # Mettre à jour
                    scoring.score = score
                    scoring.commentaire = data.get('commentaire', '')
                    scoring.updated_by = request.user
                    scoring.save()
                    
                    created = False
                    logger.info(f"Scoring {scoring.id} mis à jour")
                    
                except Scoring.DoesNotExist:
                    # Créer un nouveau scoring
                    scoring = Scoring.objects.create(
                        annee=annee,
                        acheteur=acheteur,
                        score=score,
                        commentaire=data.get('commentaire', ''),
                        created_by=request.user
                    )
                    created = True
                    logger.info(f"Scoring {scoring.id} créé")
                
                # Sérialiser le résultat
                serializer = ScoringSerializer(scoring, context={'request': request})
                
                return Response({
                    'success': True,
                    'message': f"Scoring {'créé' if created else 'mis à jour'} avec succès",
                    'data': serializer.data,
                    'is_update': not created,
                    'scoring_id': scoring.id
                }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
                
        except IntegrityError as e:
            logger.error(f"Erreur d'intégrité: {e}")
            return Response({
                'detail': 'Erreur de contrainte unique - Un scoring existe déjà',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}", exc_info=True)
            return Response({
                'detail': 'Une erreur interne est survenue',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)          
            


# views_scoring_manuel.py - ajoutez cette classe

class DebugCleanupView(APIView):
    """Vue pour nettoyer la base de données des scorings problématiques"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        acheteur_id = request.data.get('acheteur_id', 2)
        
        try:
            # 1. Vérifier ce qui existe
            from django.db import connection
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, annee_id, acheteur_id, score, deleted 
                    FROM main_scoring 
                    WHERE acheteur_id = %s
                    ORDER BY annee_id
                """, [acheteur_id])
                
                rows = cursor.fetchall()
                
                result = {
                    'acheteur_id': acheteur_id,
                    'total_rows': len(rows),
                    'scorings': []
                }
                
                for row in rows:
                    result['scorings'].append({
                        'id': row[0],
                        'annee_id': row[1],
                        'acheteur_id': row[2],
                        'score': row[3],
                        'deleted': row[4]
                    })
                
                print(f"🔍 Debug: {result}")
                
                # 2. Supprimer TOUS les scorings (hard delete)
                if request.data.get('cleanup', False):
                    cursor.execute("""
                        DELETE FROM main_scoring 
                        WHERE acheteur_id = %s
                    """, [acheteur_id])
                    
                    deleted_count = cursor.rowcount
                    result['deleted_count'] = deleted_count
                    result['message'] = f"{deleted_count} scorings supprimés"
                    print(f"🗑️  Suppression: {deleted_count} scorings")
            
            return Response(result)
            
        except Exception as e:
            return Response({
                'error': str(e),
                'detail': 'Erreur lors du nettoyage'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)