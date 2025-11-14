# views_scoring_syscohada.py - CORRECTION
import logging
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

from main.models import ActifS, PassifS, ResultatS, Acheteur, Annee
from main.serializers import BilanSyscohadaScoreSerializer

logger = logging.getLogger(__name__)

class ScoreACREMACBilanSyscohadaService:
    """
    Service spécialisé pour le calcul du score ACREMAC avec bilan SYSCOHADA
    """
    
    # Coefficients ACREMAC adaptés pour SYSCOHADA
    COEFFICIENTS = {
        'constante': Decimal('0.65'),
        'r1': Decimal('0.045'),   # Ratio frais financiers / EBE
        'r2': Decimal('0.032'),   # Ratio liquidité
        'r3': Decimal('0.028'),   # Ratio structure financière
        'r4': Decimal('0.015'),   # Ratio performance économique
        'r5': Decimal('0.012'),   # Ratio autonomie financière
        'r6': Decimal('0.008')    # Ratio couverture BFR
    }

    @classmethod
    def extraire_donnees_bilan_syscohada(cls, acheteur, annee):
        """
        Extrait les données spécifiques au bilan SYSCOHADA pour le calcul ACREMAC
        """
        try:
            annee_value = annee.annee if hasattr(annee, 'annee') else annee
            
            logger.info(f"Recherche données bilan SYSCOHADA - Acheteur: {acheteur.id}, Année: {annee_value}")
            
            # Récupération des données SYSCOHADA
            actif = ActifS.objects.filter(acheteur=acheteur, annee__annee=annee_value).first()
            passif = PassifS.objects.filter(acheteur=acheteur, annee__annee=annee_value).first()
            resultat = ResultatS.objects.filter(acheteur=acheteur, annee__annee=annee_value).first()
            
            logger.info(f"ActifS trouvé: {actif is not None}")
            logger.info(f"PassifS trouvé: {passif is not None}")
            logger.info(f"ResultatS trouvé: {resultat is not None}")
            
            if not all([actif, passif, resultat]):
                logger.warning(f"Données incomplètes pour le bilan SYSCOHADA - Acheteur: {acheteur.id}, Année: {annee_value}")
                return None
            
            # Extraction des données avec gestion des propriétés calculées
            donnees = {
                # Données d'actif
                'total_actif': Decimal(getattr(actif, 'total_actif', 0.0) or 0.0),
                'total_actif_immobilise': Decimal(getattr(actif, 'total_actif_immobilise', 0.0) or 0.0),
                'total_actif_circulant': Decimal(getattr(actif, 'total_actif_circulant', 0.0) or 0.0),
                'total_tresorerie_actif': Decimal(getattr(actif, 'total_tresorerie_equivalents', 0.0) or 0.0),
                'creances_clients': Decimal(getattr(actif, 'clients', 0.0) or 0.0),
                'stocks': Decimal(getattr(actif, 'stock_encours', 0.0) or 0.0),
                'disponibilites': Decimal(getattr(actif, 'disponibilites', 0.0) or 0.0),
                
                # Données de passif
                'total_passif': Decimal(getattr(passif, 'total_passifs', 0.0) or 0.0),
                'capitaux_propres': Decimal(getattr(passif, 'total_capitaux_propres_ressources_similaires', 0.0) or 0.0),
                'dettes_financieres': Decimal(getattr(passif, 'total_dettes_financieres_ressources_similaires', 0.0) or 0.0),
                'dettes_court_terme': Decimal(getattr(passif, 'total_passifs_courants', 0.0) or 0.0),
                'total_tresorerie_passif': Decimal(getattr(passif, 'total_tresorerie_equivalents', 0.0) or 0.0),
                
                # Données de résultat
                'chiffre_affaires': Decimal(getattr(resultat, 'chiffre_affaires', 0.0) or 0.0),
                'valeur_ajoutee': Decimal(getattr(resultat, 'valeur_ajoutee', 0.0) or 0.0),
                'ebe': Decimal(getattr(resultat, 'excedent_brute_exploitation', 0.0) or 0.0),
                'resultat_exploitation': Decimal(getattr(resultat, 'resultat_exploitation', 0.0) or 0.0),
                'resultat_net': Decimal(getattr(resultat, 'resultat_net', 0.0) or 0.0),
                'charges_financieres': Decimal(getattr(resultat, 'charges_financieres_assimilees', 0.0) or 0.0),
                'frais_personnel': Decimal(getattr(resultat, 'frais_personnel', 0.0) or 0.0),
            }
            
            logger.info(f"Données extraites bilan SYSCOHADA pour {acheteur.nom} - {annee_value}: {donnees}")
            return donnees
            
        except Exception as e:
            logger.error(f"Erreur extraction données bilan SYSCOHADA: {str(e)}", exc_info=True)
            return None

    @classmethod
    def calculer_ratios_syscohada(cls, donnees):
        """
        Calcule les 6 ratios du score ACREMAC adaptés pour SYSCOHADA
        """
        ratios = {}
        
        try:
            # R1: Frais financiers / EBE
            ebe = donnees.get('ebe', Decimal('0'))
            charges_financieres = donnees.get('charges_financieres', Decimal('0'))
            if ebe and ebe != Decimal('0'):
                ratios['r1'] = (charges_financieres / ebe) * Decimal('100')
            else:
                ratios['r1'] = Decimal('0')
            
            # R2: (Créances + disponibilités) / Dettes CT
            creances_disponibilites = donnees.get('creances_clients', Decimal('0')) + donnees.get('disponibilites', Decimal('0'))
            dettes_court_terme = donnees.get('dettes_court_terme', Decimal('0'))
            if dettes_court_terme and dettes_court_terme != Decimal('0'):
                ratios['r2'] = (creances_disponibilites / dettes_court_terme) * Decimal('100')
            else:
                ratios['r2'] = Decimal('0')
            
            # R3: Capitaux permanents / Passif
            capitaux_permanents = donnees.get('capitaux_propres', Decimal('0')) + donnees.get('dettes_financieres', Decimal('0'))
            total_passif = donnees.get('total_passif', Decimal('0'))
            if total_passif and total_passif != Decimal('0'):
                ratios['r3'] = (capitaux_permanents / total_passif) * Decimal('100')
            else:
                ratios['r3'] = Decimal('0')
            
            # R4: Valeur ajoutée / Chiffre d'affaires
            valeur_ajoutee = donnees.get('valeur_ajoutee', Decimal('0'))
            chiffre_affaires = donnees.get('chiffre_affaires', Decimal('0'))
            if chiffre_affaires and chiffre_affaires != Decimal('0'):
                ratios['r4'] = (valeur_ajoutee / chiffre_affaires) * Decimal('100')
            else:
                ratios['r4'] = Decimal('0')
            
            # R5: Trésorerie / Ventes (jours)
            tresorerie = donnees.get('total_tresorerie_actif', Decimal('0'))
            if chiffre_affaires and chiffre_affaires != Decimal('0'):
                ratios['r5'] = (tresorerie / chiffre_affaires) * Decimal('360')  # Conversion en jours
            else:
                ratios['r5'] = Decimal('0')
            
            # R6: Fonds de roulement / CA (jours)
            fonds_roulement = (donnees.get('capitaux_propres', Decimal('0')) + donnees.get('dettes_financieres', Decimal('0'))) - donnees.get('total_actif_immobilise', Decimal('0'))
            if chiffre_affaires and chiffre_affaires != Decimal('0'):
                ratios['r6'] = (fonds_roulement / chiffre_affaires) * Decimal('360')  # Conversion en jours
            else:
                ratios['r6'] = Decimal('0')
                
            logger.info(f"Ratios SYSCOHADA calculés: {ratios}")
                
        except Exception as e:
            logger.error(f"Erreur calcul ratios SYSCOHADA: {str(e)}")
            ratios = {
                'r1': Decimal('0'), 'r2': Decimal('0'), 'r3': Decimal('0'), 
                'r4': Decimal('0'), 'r5': Decimal('0'), 'r6': Decimal('0')
            }
        
        return ratios

    @classmethod
    def appliquer_bornes_syscohada(cls, ratios):
        """Applique les bornes spécifiques aux ratios SYSCOHADA"""
        ratios_bornees = {}
        
        try:
            # Conversion en float pour l'application des bornes, puis retour en Decimal
            # Bornes adaptées pour SYSCOHADA
            r1 = float(ratios.get('r1', Decimal('0')))
            r2 = float(ratios.get('r2', Decimal('0')))
            r3 = float(ratios.get('r3', Decimal('0')))
            r4 = float(ratios.get('r4', Decimal('0')))
            r5 = float(ratios.get('r5', Decimal('0')))
            r6 = float(ratios.get('r6', Decimal('0')))
            
            ratios_bornees['r1'] = Decimal(str(max(0, min(100, r1))))  # R1: 0% à 100%
            ratios_bornees['r2'] = Decimal(str(max(50, min(200, r2))))  # R2: 50% à 200%
            ratios_bornees['r3'] = Decimal(str(max(20, min(80, r3))))   # R3: 20% à 80%
            ratios_bornees['r4'] = Decimal(str(max(5, min(50, r4))))    # R4: 5% à 50%
            ratios_bornees['r5'] = Decimal(str(max(0, min(90, r5))))    # R5: 0 à 90 jours
            ratios_bornees['r6'] = Decimal(str(max(-60, min(60, r6))))  # R6: -60 à 60 jours
            
            logger.info(f"Ratios après bornes: {ratios_bornees}")
            
        except Exception as e:
            logger.error(f"Erreur application bornes SYSCOHADA: {str(e)}")
            ratios_bornees = ratios.copy()
        
        return ratios_bornees

    @classmethod
    def calculer_score_syscohada(cls, ratios_bornees):
        """Calcule le score final ACREMAC pour SYSCOHADA"""
        try:
            score = cls.COEFFICIENTS['constante']
            score += cls.COEFFICIENTS['r1'] * ratios_bornees.get('r1', Decimal('0'))
            score += cls.COEFFICIENTS['r2'] * ratios_bornees.get('r2', Decimal('0'))
            score += cls.COEFFICIENTS['r3'] * ratios_bornees.get('r3', Decimal('0'))
            score += cls.COEFFICIENTS['r4'] * ratios_bornees.get('r4', Decimal('0'))
            score += cls.COEFFICIENTS['r5'] * ratios_bornees.get('r5', Decimal('0'))
            score += cls.COEFFICIENTS['r6'] * ratios_bornees.get('r6', Decimal('0'))
            
            # Conversion en float pour le résultat final
            score_final = float(score)
            
            logger.info(f"Score SYSCOHADA calculé: {score_final}")
            
            return round(score_final, 2)
            
        except Exception as e:
            logger.error(f"Erreur calcul score SYSCOHADA: {str(e)}")
            return 0.0

    @classmethod
    def determiner_classe_risque_syscohada(cls, score):
        """Détermine la classe de risque pour SYSCOHADA"""
        try:
            if score >= 2.10:
                return "Risque faible à excellent", 0.5, "Excellente santé financière"
            elif score >= 1.26:
                return "Risque acceptable", 2.0, "Bonne santé financière"
            elif score >= 0.28:
                return "Risque normal", 5.0, "Situation satisfaisante"
            elif score >= -1.00:
                return "Risque modéré", 15.0, "Vigilance recommandée"
            elif score >= -2.57:
                return "Risque important", 30.0, "Situation fragile"
            elif score >= -4.01:
                return "Risque élevé", 50.0, "Situation difficile"
            else:
                return "Risque très élevé", 75.0, "Situation très difficile"
                
        except Exception as e:
            logger.error(f"Erreur détermination classe risque SYSCOHADA: {str(e)}")
            return "Erreur", 0.0, "Erreur de calcul"

    @classmethod
    def calculer_score_complet_syscohada(cls, donnees):
        """
        Calcule le score ACREMAC complet pour bilan SYSCOHADA
        """
        try:
            # Calcul des ratios
            ratios = cls.calculer_ratios_syscohada(donnees)
            
            # Application des bornes
            ratios_bornees = cls.appliquer_bornes_syscohada(ratios)
            
            # Calcul du score
            score = cls.calculer_score_syscohada(ratios_bornees)
            
            # Détermination de la classe de risque
            classe_risque, probabilite, commentaire = cls.determiner_classe_risque_syscohada(score)
            
            # Conversion des Decimal en float pour la sérialisation JSON
            ratios_float = {k: float(v) for k, v in ratios.items()}
            ratios_bornees_float = {k: float(v) for k, v in ratios_bornees.items()}
            coefficients_float = {k: float(v) for k, v in cls.COEFFICIENTS.items()}
            
            resultat = {
                'score': score,
                'ratios': ratios_float,
                'ratios_bornees': ratios_bornees_float,
                'classe_risque': classe_risque,
                'probabilite_defaillance': probabilite,
                'commentaire': commentaire,
                'coefficients': coefficients_float
            }
            
            logger.info(f"Score complet SYSCOHADA calculé: {resultat}")
            
            return resultat
            
        except Exception as e:
            logger.error(f"Erreur calcul score complet SYSCOHADA: {str(e)}")
            return {
                'score': 0.0,
                'ratios': {},
                'ratios_bornees': {},
                'classe_risque': "Erreur",
                'probabilite_defaillance': 0.0,
                'commentaire': "Erreur lors du calcul",
                'coefficients': {k: float(v) for k, v in cls.COEFFICIENTS.items()}
            }

# Les fonctions API restent identiques...
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculer_score_bilan_syscohada(request):
    """
    Calcule le score ACREMAC avec données de bilan SYSCOHADA
    """
    serializer = BilanSyscohadaScoreSerializer(data=request.data)
    
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
                donnees_bilan = ScoreACREMACBilanSyscohadaService.extraire_donnees_bilan_syscohada(
                    acheteur, annee
                )
                
                if donnees_bilan:
                    resultat_calcul = ScoreACREMACBilanSyscohadaService.calculer_score_complet_syscohada(donnees_bilan)
                    resultats[annee_label] = resultat_calcul
                else:
                    resultats[annee_label] = {
                        'erreur': f'Données bilan SYSCOHADA non disponibles pour {annee}',
                        'score': 0.0,
                        'classe_risque': 'Données manquantes',
                        'probabilite_defaillance': 0.0,
                        'commentaire': f'Bilan SYSCOHADA {annee} non disponible'
                    }
            
            # Préparation de la réponse
            response_data = {
                'acheteur': acheteur.nom,
                'annees': {
                    'n': annee_n,
                    'n1': annee_n1,
                    'n2': annee_n2
                },
                'bilan_type': 'syscohada',
                'scores': resultats,
                'score_principal': resultats.get('n', {}).get('score', 0)
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Erreur calcul score bilan SYSCOHADA: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors du calcul du score bilan SYSCOHADA'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_annees_bilan_syscohada(request, acheteur_id):
    """
    Retourne les années de bilan SYSCOHADA disponibles pour un acheteur
    """
    try:
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        
        # Récupération des années disponibles (depuis ActifS)
        annees = ActifS.objects.filter(acheteur=acheteur).values_list('annee__annee', flat=True).distinct()
        annees_disponibles = sorted(annees, reverse=True)
        
        return Response({
            'acheteur': acheteur.nom,
            'bilan_type': 'syscohada',
            'years': annees_disponibles,
            'count': len(annees_disponibles)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération années bilan SYSCOHADA: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors de la récupération des années'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )