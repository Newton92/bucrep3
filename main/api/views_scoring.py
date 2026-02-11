# views_scoring.py

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
from main.models import ScoringSansBilanAcheteur, Acheteur, ActifC, PassifC, ResultatC
from main.serializers import ScoringSansBilanAcheteurSerializer, BilanClassiqueScoreSerializer
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from main.models import ScoringSansBilanAcheteur, Acheteur
from main.serializers import ScoringSansBilanAcheteurSerializer
from decimal import Decimal
from typing import Dict, Tuple, Optional


import logging


logger = logging.getLogger(__name__)


class NoPagination(PageNumberPagination):
    page_size = None

# views.py
class ModeleComportementPaiementScoringListView(ListAPIView):
    queryset = ModeleComportementPaiement.objects.all()
    serializer_class = ModeleComportementPaiementScoringSerializer
    permission_classes = [AllowAny]
    pagination_class = NoPagination  # Désactive la pagination
    
    def get(self, request, *args, **kwargs):
        print(f"📡 API Comportement Paiement appelée, {self.queryset.count()} éléments")
        return super().get(request, *args, **kwargs)

class FormeJuridiqueScoringListView(ListAPIView):
    queryset = FormeJuridique.objects.all()
    serializer_class = FormeJuridiqueScoringSerializer
    permission_classes = [AllowAny]
    pagination_class = NoPagination  # Désactive la pagination
    
    def get(self, request, *args, **kwargs):
        print(f"📡 API Comportement Paiement appelée, {self.queryset.count()} éléments")
        return super().get(request, *args, **kwargs)

class ModeleAgeSocieteScoringListView(ListAPIView):
    queryset = ModeleAgeSociete.objects.all()
    serializer_class = ModeleAgeSocieteScoringSerializer
    permission_classes = [AllowAny]
    pagination_class = NoPagination  # Désactive la pagination
    
    def get(self, request, *args, **kwargs):
        print(f"📡 API Comportement Paiement appelée, {self.queryset.count()} éléments")
        return super().get(request, *args, **kwargs)

class ModeleAvisCommercialScoringListView(ListAPIView):
    queryset = ModeleAvisCommercial.objects.all()
    serializer_class = ModeleAvisCommercialScoringSerializer
    permission_classes = [AllowAny]
    pagination_class = NoPagination  # Désactive la pagination
    
    def get(self, request, *args, **kwargs):
        print(f"📡 API Comportement Paiement appelée, {self.queryset.count()} éléments")
        return super().get(request, *args, **kwargs)

class ModeleBailScoringListView(ListAPIView):
    queryset = ModeleBail.objects.all()
    serializer_class = ModeleBailScoringSerializer
    permission_classes = [AllowAny]
    pagination_class = NoPagination  # Désactive la pagination
    
    def get(self, request, *args, **kwargs):
        print(f"📡 API Comportement Paiement appelée, {self.queryset.count()} éléments")
        return super().get(request, *args, **kwargs)

class CategoryNaceCodeScoringListView(ListAPIView):
    queryset = CategoryNaceCode.objects.all()
    serializer_class = CategoryNaceCodeScoringSerializer
    permission_classes = [AllowAny]
    pagination_class = NoPagination  # Désactive la pagination
    
    def get(self, request, *args, **kwargs):
        print(f"📡 API Comportement Paiement appelée, {self.queryset.count()} éléments")
        return super().get(request, *args, **kwargs)

class ScoringSansBilanAcheteurDetailViewTwo(RetrieveUpdateAPIView):
    serializer_class = ScoringSansBilanAcheteurSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        acheteur_id = self.kwargs.get("acheteur_id")
        return ScoringSansBilanAcheteur.objects.filter(acheteur_id=acheteur_id)

    def get_object(self):
        acheteur_id = self.kwargs.get("acheteur_id")
        return ScoringSansBilanAcheteur.objects.get(acheteur_id=acheteur_id)

class ScoringSansBilanAcheteurDetailView(RetrieveUpdateAPIView):
    serializer_class = ScoringSansBilanAcheteurSerializer
    permission_classes = [IsAuthenticated]
    
    

    def get_queryset(self):
        acheteur_id = self.kwargs.get("acheteur_id")
        return ScoringSansBilanAcheteur.objects.filter(acheteur_id=acheteur_id)

    def get_object(self):
        acheteur_id = self.kwargs.get("acheteur_id")
        print(f"📡 Scoring demandé pour acheteur {acheteur_id}")
        code_scoring = generate_unique_code()
        libelle_scoring = "Scoring crédit acheteur basé sur critères non financiers"
        
        try:
            scoring = ScoringSansBilanAcheteur.objects.get(acheteur_id=acheteur_id)

            print(code_scoring)
            print(libelle_scoring)
            print(f"✅ Scoring existant trouvé: {scoring.id}, score: {scoring.scoring_value}")
            
            # Forcer le recalcul du score pour s'assurer qu'il est à jour
            scoring.scoring_value = scoring.calculate_scoring_value()
            scoring.interpretation = scoring.generate_interpretation()
            
            if scoring._state.adding or scoring.has_changed():
                scoring.code = code_scoring
                scoring.libelle = libelle_scoring
                scoring.updated_by = self.request.user
                scoring.save()
                
            return scoring
        except ScoringSansBilanAcheteur.DoesNotExist:
            print(f"⚠️ Scoring non trouvé, création d'un nouveau pour acheteur {acheteur_id}")
            acheteur = get_object_or_404(Acheteur, id=acheteur_id)
            scoring = ScoringSansBilanAcheteur.objects.create(
                code=code_scoring,
                libelle=libelle_scoring,
                acheteur=acheteur,
                created_by=self.request.user
            )
            return scoring
        
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

class ScoreACREMACBilanService:
    """
    Service pour calculer le score ACREMAC avec données de bilan
    """
    
    # Bornes pour les ratios
    BORNES_R1 = (0, 100)
    BORNES_R2 = (0, 200)
    BORNES_R3 = (-25, 100)
    BORNES_R4 = (0, 100)
    BORNES_R5 = (-100, 100)
    BORNES_R6 = (-100, 150)
    
    # Coefficients
    COEFFICIENTS = {
        'constante': 0.57,
        'r1': 0.0535,
        'r2': 0.0115,
        'r3': 0.0371,
        'r4': 0.0246,
        'r5': 0.0115,
        'r6': 0.0096
    }
    
    @classmethod
    def calculer_ratios(cls, donnees: Dict) -> Dict:
        """
        Calcule les 6 ratios du score ACREMAC
        """
        ratios = {}
        
        # R1 = Frais financiers / EBE
        if donnees.get('ebe') and donnees['ebe'] != 0:
            ratios['r1'] = (donnees.get('frais_financiers', 0) / donnees['ebe']) * 100
        else:
            ratios['r1'] = 0
        
        # R2 = (Créances + disponibilités) / Dettes CT
        if donnees.get('dettes_court_terme') and donnees['dettes_court_terme'] != 0:
            ratios['r2'] = (donnees.get('creances_disponibilites', 0) / donnees['dettes_court_terme']) * 100
        else:
            ratios['r2'] = 0
        
        # R3 = Capitaux permanents / Passif
        if donnees.get('total_passif') and donnees['total_passif'] != 0:
            ratios['r3'] = (donnees.get('capitaux_permanents', 0) / donnees['total_passif']) * 100
        else:
            ratios['r3'] = 0
        
        # R4 = VA / CA
        if donnees.get('chiffre_affaires') and donnees['chiffre_affaires'] != 0:
            ratios['r4'] = (donnees.get('valeur_ajoutee', 0) / donnees['chiffre_affaires']) * 100
        else:
            ratios['r4'] = 0
        
        # R5 = Trésorerie / Ventes (j)
        ca_journalier = donnees.get('chiffre_affaires', 0) / 360 if donnees.get('chiffre_affaires') else 0
        if ca_journalier and ca_journalier != 0:
            ratios['r5'] = (donnees.get('tresorerie', 0) / ca_journalier)
        else:
            ratios['r5'] = 0
        
        # R6 = Fonds de roulement / CA (j)
        if ca_journalier and ca_journalier != 0:
            ratios['r6'] = (donnees.get('fonds_roulement', 0) / ca_journalier)
        else:
            ratios['r6'] = 0
        
        return ratios
    
    @classmethod
    def appliquer_bornes(cls, ratios: Dict) -> Dict:
        """
        Applique les bornes aux ratios selon les limites définies
        """
        ratios_bornees = {}
        
        # R1 [0*;100]
        ratios_bornees['r1'] = max(cls.BORNES_R1[0], min(ratios.get('r1', 0), cls.BORNES_R1[1]))
        
        # R2 [0;200]
        ratios_bornees['r2'] = max(cls.BORNES_R2[0], min(ratios.get('r2', 0), cls.BORNES_R2[1]))
        
        # R3 [-25;100]
        ratios_bornees['r3'] = max(cls.BORNES_R3[0], min(ratios.get('r3', 0), cls.BORNES_R3[1]))
        
        # R4 [0;100]
        ratios_bornees['r4'] = max(cls.BORNES_R4[0], min(ratios.get('r4', 0), cls.BORNES_R4[1]))
        
        # R5 [-100;100]
        ratios_bornees['r5'] = max(cls.BORNES_R5[0], min(ratios.get('r5', 0), cls.BORNES_R5[1]))
        
        # R6 [-100;150]
        ratios_bornees['r6'] = max(cls.BORNES_R6[0], min(ratios.get('r6', 0), cls.BORNES_R6[1]))
        
        return ratios_bornees
    
    @classmethod
    def calculer_score(cls, ratios_bornees: Dict) -> float:
        """
        Calcule le score final
        """
        score = cls.COEFFICIENTS['constante']
        score += cls.COEFFICIENTS['r1'] * ratios_bornees['r1']
        score += cls.COEFFICIENTS['r2'] * ratios_bornees['r2']
        score += cls.COEFFICIENTS['r3'] * ratios_bornees['r3']
        score += cls.COEFFICIENTS['r4'] * ratios_bornees['r4']
        score += cls.COEFFICIENTS['r5'] * ratios_bornees['r5']
        score += cls.COEFFICIENTS['r6'] * ratios_bornees['r6']
        
        return round(score, 6)
    
    @classmethod
    def determiner_classe_risque(cls, score: float) -> Tuple[str, float, str]:
        """
        Détermine la classe de risque basée sur le score
        """
        if score < -4.01:
            return "Risque très élevé", 12.7, "Procédure d'insolvabilité probable"
        elif -4.01 <= score < -2.57:
            return "Risque élevé", 6.00, "Risque élevé (taux de défaillance >10%)"
        elif -2.57 <= score < -1.00:
            return "Risque important", 4.96, "Risque important"
        elif -1.00 <= score < 0.28:
            return "Risque modéré", 3.29, "Risque modéré"
        elif 0.28 <= score < 1.26:
            return "Risque normal", 2.15, "Risque normal (taux de défaillance = 3%)"
        elif 1.26 <= score < 2.10:
            return "Risque acceptable", 1.57, "Risque acceptable"
        elif 2.10 <= score < 2.86:
            return "Risque faible", 1.06, "Risque faible"
        elif 2.86 <= score < 3.68:
            return "Risque très faible", 0.64, "Risque faible (taux de défaillance < 1%)"
        elif 3.68 <= score < 4.83:
            return "Risque excellent", 0.38, "Risque excellent"
        else:  # score >= 5.83
            return "Risque exceptionnel", 0.42, "Risque exceptionnel"
    
    @classmethod
    def calculer_score_complet(cls, donnees: Dict) -> Dict:
        """
        Calcule le score ACREMAC complet avec toutes les informations
        """
        # Calcul des ratios
        ratios = cls.calculer_ratios(donnees)
        
        # Application des bornes
        ratios_bornees = cls.appliquer_bornes(ratios)
        
        # Calcul du score
        score = cls.calculer_score(ratios_bornees)
        
        # Détermination de la classe de risque
        classe_risque, probabilite, commentaire = cls.determiner_classe_risque(score)
        
        return {
            'score': score,
            'ratios': ratios,
            'ratios_bornees': ratios_bornees,
            'classe_risque': classe_risque,
            'probabilite_defaillance': probabilite,
            'commentaire': commentaire,
            'coefficients': cls.COEFFICIENTS
        }
        
        
        
        



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculer_score_acremac_bilan(request):
    """
    Calcule le score ACREMAC avec données de bilan pour un acheteur
    """
    serializer = ScoreACREMACBilanSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            acheteur_id = serializer.validated_data['acheteur_id']
            annee_n = serializer.validated_data['annee_n']
            annee_n1 = serializer.validated_data['annee_n1']
            annee_n2 = serializer.validated_data['annee_n2']
            
            # Récupération de l'acheteur
            acheteur = get_object_or_404(Acheteur, id=acheteur_id)
            
            # Calcul des scores pour les 3 années
            resultats = {}
            
            for annee_label, annee in [('n', annee_n), ('n1', annee_n1), ('n2', annee_n2)]:
                donnees_bilan = extraire_donnees_bilan_par_annee(acheteur, annee)
                
                if donnees_bilan:
                    resultat_calcul = ScoreACREMACBilanService.calculer_score_complet(donnees_bilan)
                    resultats[annee_label] = resultat_calcul
                else:
                    resultats[annee_label] = {'erreur': f'Données bilan non disponibles pour {annee}'}
            
            # Préparation de la réponse
            response_data = {
                'acheteur': acheteur.nom,
                'annees': {
                    'n': annee_n,
                    'n1': annee_n1,
                    'n2': annee_n2
                },
                'scores': resultats,
                'score_principal': resultats.get('n', {}).get('score', 0)
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Erreur calcul score ACREMAC: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors du calcul du score'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculer_score_direct(request):
    """
    Calcule le score ACREMAC avec des données directes (pour tests)
    """
    serializer = CalculScoreACREMACBilanSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        donnees = serializer.validated_data
        
        resultat_calcul = ScoreACREMACBilanService.calculer_score_complet({
            'frais_financiers': float(donnees['frais_financiers']),
            'ebe': float(donnees['ebe']),
            'creances_disponibilites': float(donnees['creances_disponibilites']),
            'dettes_court_terme': float(donnees['dettes_court_terme']),
            'capitaux_permanents': float(donnees['capitaux_permanents']),
            'total_passif': float(donnees['total_passif']),
            'valeur_ajoutee': float(donnees['valeur_ajoutee']),
            'chiffre_affaires': float(donnees['chiffre_affaires']),
            'tresorerie': float(donnees['tresorerie']),
            'fonds_roulement': float(donnees['fonds_roulement'])
        })
        
        return Response(resultat_calcul, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur calcul score direct: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors du calcul du score'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historique_scores_acheteur(request, acheteur_id):
    """
    Récupère l'historique des scores ACREMAC pour un acheteur
    """
    try:
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        
        # Récupération des années disponibles
        annees_disponibles = get_annees_bilan_disponibles(acheteur)
        
        scores_historique = []
        
        for annee in annees_disponibles[:5]:  # Limite aux 5 dernières années
            donnees_bilan = extraire_donnees_bilan_par_annee(acheteur, annee)
            
            if donnees_bilan:
                resultat_calcul = ScoreACREMACBilanService.calculer_score_complet(donnees_bilan)
                scores_historique.append({
                    'annee': annee,
                    'score': resultat_calcul['score'],
                    'classe_risque': resultat_calcul['classe_risque'],
                    'probabilite_defaillance': resultat_calcul['probabilite_defaillance']
                })
        
        return Response({
            'acheteur': acheteur.nom,
            'historique': scores_historique
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur historique scores: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors de la récupération de l\'historique'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Fonctions utilitaires
def extraire_donnees_bilan_par_annee(acheteur, annee):
    """
    Extrait les données de bilan nécessaires pour une année donnée
    Adaptez cette fonction selon votre structure de modèles
    """
    try:
        # Exemple avec le bilan classique - adaptez selon vos modèles
        actif = ActifC.objects.filter(acheteur=acheteur, annee__annee=annee).first()
        passif = PassifC.objects.filter(acheteur=acheteur, annee__annee=annee).first()
        resultat = ResultatC.objects.filter(acheteur=acheteur, annee__annee=annee).first()
        
        if not all([actif, passif, resultat]):
            return None
        
        # Extraction des données selon la structure ACREMAC
        donnees = {
            'frais_financiers': float(resultat.frais_fin_charges_assi or 0),
            'ebe': float(resultat.excedent_brut_ex or 0),
            'creances_disponibilites': float((actif.creances or 0) + (actif.disponibilites_vmp or 0)),
            'dettes_court_terme': float(passif.total_III or 0),
            'capitaux_permanents': float(passif.total_I + passif.total_II or 0),
            'total_passif': float(passif.total_general or 0),
            'valeur_ajoutee': float(resultat.valeur_ajoutee or 0),
            'chiffre_affaires': float(resultat.ca or 0),
            'tresorerie': float(actif.disponibilites_vmp or 0),
            'fonds_roulement': float((passif.total_I + passif.total_II) - (actif.total_I) or 0)
        }
        
        return donnees
        
    except Exception as e:
        logger.error(f"Erreur extraction données bilan: {str(e)}")
        return None

def get_annees_bilan_disponibles(acheteur):
    """
    Retourne la liste des années de bilan disponibles pour un acheteur
    """
    annees = ActifC.objects.filter(acheteur=acheteur).values_list('annee__annee', flat=True).distinct()
    return sorted(annees, reverse=True)
