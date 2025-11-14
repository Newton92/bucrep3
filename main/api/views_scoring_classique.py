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
import logging

logger = logging.getLogger(__name__)



class NoPagination(PageNumberPagination):
    page_size = None
    
    
    
class ScoreACREMACBilanClassiqueService:
    """
    Service spécialisé pour le calcul du score ACREMAC avec bilan classique
    """
    
    # Bornes pour les ratios
    BORNES_R1 = (0, 100)
    BORNES_R2 = (0, 200)
    BORNES_R3 = (-25, 100)
    BORNES_R4 = (0, 100)
    BORNES_R5 = (-100, 100)
    BORNES_R6 = (-100, 150)
    
    # Coefficients ACREMAC
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
    def extraire_donnees_bilan_classique(cls, acheteur, annee):
        """
        Extrait les données spécifiques au bilan classique pour le calcul ACREMAC
        """
        try:
            actif = ActifC.objects.filter(acheteur=acheteur, annee__annee=annee).first()
            passif = PassifC.objects.filter(acheteur=acheteur, annee__annee=annee).first()
            resultat = ResultatC.objects.filter(acheteur=acheteur, annee__annee=annee).first()
            
            if not all([actif, passif, resultat]):
                return None
            
            # Calcul des données nécessaires pour ACREMAC
            donnees = {
                # R1: Frais financiers / EBE
                'frais_financiers': float(resultat.frais_fin_charges_assi or 0),
                'ebe': float(resultat.excedent_brut_ex or 0),
                
                # R2: (Créances + disponibilités) / Dettes CT
                'creances_disponibilites': float(
                    (actif.creances or 0) + 
                    (actif.disponibilites_vmp or 0)
                ),
                'dettes_court_terme': float(passif.total_III or 0),
                
                # R3: Capitaux permanents / Passif
                'capitaux_permanents': float(
                    (passif.total_I or 0) + 
                    (passif.total_II or 0)
                ),
                'total_passif': float(passif.total_general or 0),
                
                # R4: VA / CA
                'valeur_ajoutee': float(resultat.valeur_ajoutee or 0),
                'chiffre_affaires': float(resultat.ca or 0),
                
                # R5: Trésorerie / Ventes (j)
                'tresorerie': float(actif.disponibilites_vmp or 0),
                
                # R6: Fonds de roulement / CA (j)
                'fonds_roulement': float(
                    ((passif.total_I or 0) + (passif.total_II or 0)) - 
                    (actif.total_I or 0)
                )
            }
            
            return donnees
            
        except Exception as e:
            logger.error(f"Erreur extraction données bilan classique: {str(e)}")
            return None

    @classmethod
    def calculer_ratios(cls, donnees):
        """
        Calcule les 6 ratios du score ACREMAC pour le bilan classique
        """
        ratios = {}
        
        try:
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
                
        except Exception as e:
            logger.error(f"Erreur calcul ratios: {str(e)}")
            # Valeurs par défaut en cas d'erreur
            ratios = {'r1': 0, 'r2': 0, 'r3': 0, 'r4': 0, 'r5': 0, 'r6': 0}
        
        return ratios

    @classmethod
    def appliquer_bornes(cls, ratios):
        """
        Applique les bornes aux ratios selon les limites ACREMAC
        """
        ratios_bornees = {}
        
        try:
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
            
        except Exception as e:
            logger.error(f"Erreur application bornes: {str(e)}")
            ratios_bornees = ratios.copy()
        
        return ratios_bornees

    @classmethod
    def calculer_score(cls, ratios_bornees):
        """
        Calcule le score final ACREMAC
        """
        try:
            score = cls.COEFFICIENTS['constante']
            score += cls.COEFFICIENTS['r1'] * ratios_bornees['r1']
            score += cls.COEFFICIENTS['r2'] * ratios_bornees['r2']
            score += cls.COEFFICIENTS['r3'] * ratios_bornees['r3']
            score += cls.COEFFICIENTS['r4'] * ratios_bornees['r4']
            score += cls.COEFFICIENTS['r5'] * ratios_bornees['r5']
            score += cls.COEFFICIENTS['r6'] * ratios_bornees['r6']
            
            return round(score, 6)
        except Exception as e:
            logger.error(f"Erreur calcul score: {str(e)}")
            return 0.0

    @classmethod
    def determiner_classe_risque(cls, score):
        """
        Détermine la classe de risque basée sur le score ACREMAC
        """
        try:
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
        except Exception as e:
            logger.error(f"Erreur détermination classe risque: {str(e)}")
            return "Indéterminé", 0.0, "Impossible de déterminer le risque"

    @classmethod
    def calculer_score_complet(cls, donnees):
        """
        Calcule le score ACREMAC complet avec toutes les informations
        """
        try:
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
        except Exception as e:
            logger.error(f"Erreur calcul score complet: {str(e)}")
            return {
                'score': 0.0,
                'ratios': {},
                'ratios_bornees': {},
                'classe_risque': "Erreur",
                'probabilite_defaillance': 0.0,
                'commentaire': "Erreur lors du calcul",
                'coefficients': cls.COEFFICIENTS
            }
            
            
            
            
            
            
            
            
# API pour le scoring avec bilan classique
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculer_score_bilan_classique(request):
    """
    Calcule le score ACREMAC avec données de bilan classique
    """
    serializer = BilanClassiqueScoreSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            acheteur_id = serializer.validated_data['acheteur_id']
            annee_n = serializer.validated_data['annee_n']
            annee_n1 = serializer.validated_data['annee_n1']
            annee_n2 = serializer.validated_data['annee_n2']
            bilan_type = serializer.validated_data['bilan_type']
            
            # Récupération de l'acheteur
            acheteur = get_object_or_404(Acheteur, id=acheteur_id)
            
            # Calcul des scores pour les 3 années
            resultats = {}
            
            for annee_label, annee in [('n', annee_n), ('n1', annee_n1), ('n2', annee_n2)]:
                donnees_bilan = ScoreACREMACBilanClassiqueService.extraire_donnees_bilan_classique(acheteur, annee)
                
                if donnees_bilan:
                    resultat_calcul = ScoreACREMACBilanClassiqueService.calculer_score_complet(donnees_bilan)
                    resultats[annee_label] = resultat_calcul
                else:
                    resultats[annee_label] = {
                        'erreur': f'Données bilan classique non disponibles pour {annee}',
                        'score': 0.0,
                        'classe_risque': 'Données manquantes',
                        'probabilite_defaillance': 0.0,
                        'commentaire': f'Bilan classique {annee} non disponible'
                    }
            
            # Préparation de la réponse
            response_data = {
                'acheteur': acheteur.nom,
                'annees': {
                    'n': annee_n,
                    'n1': annee_n1,
                    'n2': annee_n2
                },
                'scores': resultats,
                'score_principal': resultats.get('n', {}).get('score', 0),
                'bilan_type': bilan_type
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Erreur calcul score bilan classique: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors du calcul du score bilan classique'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_annees_bilan_classique(request, acheteur_id):
    """
    Retourne les années de bilan classique disponibles pour un acheteur
    """
    try:
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        
        # Récupération des années de bilan classique disponibles
        annees = ActifC.objects.filter(acheteur=acheteur).values_list('annee__annee', flat=True).distinct()
        annees_disponibles = sorted(annees, reverse=True)
        
        return Response({
            'acheteur': acheteur.nom,
            'bilan_type': 'classique',
            'years': annees_disponibles,
            'count': len(annees_disponibles)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération années bilan classique: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors de la récupération des années'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_details_bilan_classique(request, acheteur_id, annee):
    """
    Retourne les détails du bilan classique pour analyse
    """
    try:
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        
        actif = ActifC.objects.filter(acheteur=acheteur, annee__annee=annee).first()
        passif = PassifC.objects.filter(acheteur=acheteur, annee__annee=annee).first()
        resultat = ResultatC.objects.filter(acheteur=acheteur, annee__annee=annee).first()
        
        if not all([actif, passif, resultat]):
            return Response({
                'erreur': f'Bilan classique non complet pour {annee}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Données détaillées pour l'analyse
        details = {
            'annee': annee,
            'actif': {
                'immobilisations_incorporelles': float(actif.elements_incorporels or 0),
                'immobilisations_corporelles': float(actif.elements_corporels or 0),
                'immobilisations_financieres': float(actif.elements_financiers or 0),
                'total_immobilisations': float(actif.total_I or 0),
                'stocks': float(actif.stocks or 0),
                'creances': float(actif.creances or 0),
                'disponibilites': float(actif.disponibilites_vmp or 0),
                'total_actif_circulant': float(actif.total_II or 0),
                'total_actif': float(actif.general_total or 0)
            },
            'passif': {
                'capitaux_propres': float(passif.total_I or 0),
                'dettes_financieres': float(passif.total_II or 0),
                'dettes_court_terme': float(passif.total_III or 0),
                'total_passif': float(passif.total_general or 0)
            },
            'resultat': {
                'chiffre_affaires': float(resultat.ca or 0),
                'valeur_ajoutee': float(resultat.valeur_ajoutee or 0),
                'ebe': float(resultat.excedent_brut_ex or 0),
                'resultat_exploitation': float(resultat.resultat_exploitation or 0),
                'frais_financiers': float(resultat.frais_fin_charges_assi or 0),
                'resultat_net': float(resultat.resultat_exercice or 0)
            }
        }
        
        return Response(details, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération détails bilan: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors de la récupération des détails du bilan'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )