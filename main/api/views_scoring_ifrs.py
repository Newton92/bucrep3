# views_scoring_ifrs.py
import logging
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

from main.models import ActifIFRS, PassifIFRS, ResultatIFRS, Acheteur, Annee
from main.serializers import BilanIFRSScoreSerializer

logger = logging.getLogger(__name__)

class ScoreACREMACBilanIFRSService:
    """
    Service spécialisé pour le calcul du score ACREMAC avec bilan IFRS COBAC
    """
    
    # CORRECTION : Coefficients ACREMAC révisés pour IFRS COBAC
    COEFFICIENTS = {
        'constante': Decimal('0.65'),
        'r1': Decimal('0.0045'),   # Réduit de 0.045 à 0.0045
        'r2': Decimal('0.0032'),   # Réduit de 0.032 à 0.0032
        'r3': Decimal('0.0028'),   # Réduit de 0.028 à 0.0028
        'r4': Decimal('0.0015'),   # Réduit de 0.015 à 0.0015
        'r5': Decimal('0.0012'),   # Réduit de 0.012 à 0.0012
        'r6': Decimal('0.0008')    # Réduit de 0.008 à 0.0008
    }

    @classmethod
    def _safe_ratio(cls, numerator, denominator, multiplier=Decimal('1')):
        """Retourne Decimal('0') si le dénominateur est invalide."""
        try:
            numerator = Decimal(str(numerator or 0))
            denominator = Decimal(str(denominator or 0))
            multiplier = Decimal(str(multiplier))
            if denominator == 0:
                return Decimal('0')
            return (numerator / denominator) * multiplier
        except Exception:
            return Decimal('0')

    @classmethod
    def extraire_donnees_bilan_ifrs(cls, acheteur, annee):
        """
        Extrait les données spécifiques au bilan IFRS pour le calcul ACREMAC
        """
        try:
            annee_value = annee.annee if hasattr(annee, 'annee') else annee
            
            logger.info(f"Recherche données bilan IFRS - Acheteur: {acheteur.id}, Année: {annee_value}")
            
            # Récupération des données IFRS
            actif = ActifIFRS.objects.filter(acheteur=acheteur, annee__annee=annee_value).first()
            passif = PassifIFRS.objects.filter(acheteur=acheteur, annee__annee=annee_value).first()
            resultat = ResultatIFRS.objects.filter(acheteur=acheteur, annee__annee=annee_value).first()
            
            logger.info(f"ActifIFRS trouvé: {actif is not None}")
            logger.info(f"PassifIFRS trouvé: {passif is not None}")
            logger.info(f"ResultatIFRS trouvé: {resultat is not None}")
            
            if not all([actif, passif, resultat]):
                logger.warning(f"Données incomplètes pour le bilan IFRS - Acheteur: {acheteur.id}, Année: {annee_value}")
                return None
            
            # CORRECTION : S'assurer que toutes les valeurs sont en Decimal
            def safe_decimal(value):
                """Convertit une valeur en Decimal de manière sécurisée"""
                if value is None:
                    return Decimal('0')
                if isinstance(value, Decimal):
                    return value
                try:
                    return Decimal(str(value))
                except:
                    return Decimal('0')
            
            # Extraction des données avec gestion des propriétés calculées
            donnees = {
                # Données d'actif
                'total_actif': safe_decimal(getattr(actif, 'total_actif', 0)),
                'total_actif_immobilise': safe_decimal(getattr(actif, 'total_actif_non_courant', 0)),
                'total_actif_circulant': safe_decimal(getattr(actif, 'total_actif_courant', 0)),
                'total_tresorerie_actif': safe_decimal(getattr(actif, 'disponibilites_bancaires', 0)),
                'creances_clients': safe_decimal(getattr(actif, 'creances_a_court_terme', 0)),
                'stocks': safe_decimal(
                    safe_decimal(getattr(actif, 'matieres_premieres', 0)) + 
                    safe_decimal(getattr(actif, 'produits_finis', 0))
                ),
                'disponibilites': safe_decimal(getattr(actif, 'disponibilites_bancaires', 0)),
                
                # Données de passif
                'total_passif': safe_decimal(getattr(passif, 'total_passif', 0)),
                'capitaux_propres': safe_decimal(getattr(passif, 'total_capitaux_propres', 0)),
                'dettes_financieres': safe_decimal(
                    safe_decimal(getattr(passif, 'emprunts_bancaires_long_terme', 0)) +
                    safe_decimal(getattr(passif, 'obligations', 0)) +
                    safe_decimal(getattr(passif, 'emprunts_bancaires_court_terme', 0))
                ),
                'dettes_court_terme': safe_decimal(getattr(passif, 'total_passif_courant', 0)),
                'total_tresorerie_passif': Decimal('0'),
                
                # Données de résultat - CORRECTION ICI
                'chiffre_affaires': safe_decimal(getattr(resultat, 'chiffre_affaires', 0)),
                'valeur_ajoutee': Decimal('0'),
                'ebe': safe_decimal(
                    safe_decimal(getattr(resultat, 'resultat_operationnel', 0)) +
                    safe_decimal(getattr(resultat, 'amortissement_des_immobilisations', 0)) +
                    safe_decimal(getattr(resultat, 'provisions_pour_risques_et_charges', 0))
                ),
                'resultat_exploitation': safe_decimal(getattr(resultat, 'resultat_operationnel', 0)),
                'resultat_net': safe_decimal(getattr(resultat, 'resultat_net', 0)),
                'charges_financieres': safe_decimal(getattr(resultat, 'charges_financieres', 0)),
                'frais_personnel': safe_decimal(getattr(resultat, 'salaires_et_charges_sociales', 0)),
                
                # Données spécifiques IFRS
                'goodwill': safe_decimal(getattr(actif, 'goodwill', 0)),
                'immobilisations_incorporelles': safe_decimal(
                    safe_decimal(getattr(actif, 'marques_et_droits_auteur', 0)) +
                    safe_decimal(getattr(actif, 'brevets_et_licences', 0)) +
                    safe_decimal(getattr(actif, 'autres_immobilisations_incorporelles', 0))
                ),
                'actifs_biologiques': Decimal('0'),
            }
            
            logger.info(f"Donnees soumises :  {donnees}")
            
            # Calcul de la valeur ajoutée approximative pour IFRS
            if donnees['chiffre_affaires'] > Decimal('0'):
                donnees['valeur_ajoutee'] = donnees['ebe'] + donnees['frais_personnel']
            
            logger.info(f"Données extraites bilan IFRS pour {acheteur.nom} - {annee_value}: {donnees}")
            return donnees
            
        except Exception as e:
            logger.error(f"Erreur extraction données bilan IFRS: {str(e)}", exc_info=True)
            return None
    
    @classmethod
    def calculer_ratios_ifrs(cls, donnees):
        """
        Calcule les 6 ratios du score ACREMAC adaptés pour IFRS COBAC
        """
        ratios = {}
        
        try:
            # R1: Frais financiers / EBE
            ebe = donnees.get('ebe', Decimal('0'))
            charges_financieres = donnees.get('charges_financieres', Decimal('0'))
            ratios['r1'] = cls._safe_ratio(charges_financieres, ebe, Decimal('100'))
            
            # R2: (Créances + disponibilités) / Dettes CT
            creances_disponibilites = donnees.get('creances_clients', Decimal('0')) + donnees.get('disponibilites', Decimal('0'))
            dettes_court_terme = donnees.get('dettes_court_terme', Decimal('0'))
            ratios['r2'] = cls._safe_ratio(creances_disponibilites, dettes_court_terme, Decimal('100'))
            
            # R3: Capitaux permanents / Passif
            capitaux_permanents = donnees.get('capitaux_propres', Decimal('0')) + donnees.get('dettes_financieres', Decimal('0'))
            total_passif = donnees.get('total_passif', Decimal('0'))
            ratios['r3'] = cls._safe_ratio(capitaux_permanents, total_passif, Decimal('100'))
            
            # R4: Valeur ajoutée / Chiffre d'affaires
            valeur_ajoutee = donnees.get('valeur_ajoutee', Decimal('0'))
            chiffre_affaires = donnees.get('chiffre_affaires', Decimal('0'))
            ratios['r4'] = cls._safe_ratio(valeur_ajoutee, chiffre_affaires, Decimal('100'))
            
            # R5: Trésorerie / Ventes (jours)
            tresorerie = donnees.get('total_tresorerie_actif', Decimal('0'))
            ratios['r5'] = cls._safe_ratio(tresorerie, chiffre_affaires, Decimal('360'))
            
            # R6: Fonds de roulement / CA (jours)
            fonds_roulement = (donnees.get('capitaux_propres', Decimal('0')) + donnees.get('dettes_financieres', Decimal('0'))) - donnees.get('total_actif_immobilise', Decimal('0'))
            ratios['r6'] = cls._safe_ratio(fonds_roulement, chiffre_affaires, Decimal('360'))
                
            logger.info(f"Ratios IFRS calculés: {ratios}")
                
        except Exception as e:
            logger.error(f"Erreur calcul ratios IFRS: {str(e)}")
            ratios = {
                'r1': Decimal('0'), 'r2': Decimal('0'), 'r3': Decimal('0'), 
                'r4': Decimal('0'), 'r5': Decimal('0'), 'r6': Decimal('0')
            }
        
        return ratios

    @classmethod
    def appliquer_bornes_ifrs(cls, ratios):
        """Applique les bornes spécifiques aux ratios IFRS"""
        ratios_bornees = {}
        
        try:
            r1 = Decimal(str(ratios.get('r1', Decimal('0'))))
            r2 = Decimal(str(ratios.get('r2', Decimal('0'))))
            r3 = Decimal(str(ratios.get('r3', Decimal('0'))))
            r4 = Decimal(str(ratios.get('r4', Decimal('0'))))
            r5 = Decimal(str(ratios.get('r5', Decimal('0'))))
            r6 = Decimal(str(ratios.get('r6', Decimal('0'))))
            
            # Bornes adaptées pour IFRS COBAC
            ratios_bornees['r1'] = max(Decimal('0'), min(Decimal('100'), r1))
            ratios_bornees['r2'] = max(Decimal('0'), min(Decimal('200'), r2))
            ratios_bornees['r3'] = max(Decimal('-100'), min(Decimal('100'), r3))
            ratios_bornees['r4'] = max(Decimal('0'), min(Decimal('100'), r4))
            ratios_bornees['r5'] = max(Decimal('0'), min(Decimal('360'), r5))
            ratios_bornees['r6'] = max(Decimal('-360'), min(Decimal('360'), r6))
            
            logger.info(f"Ratios après bornes: {ratios_bornees}")
            
        except Exception as e:
            logger.error(f"Erreur application bornes IFRS: {str(e)}")
            ratios_bornees = ratios.copy()
        
        return ratios_bornees

    @classmethod
    def calculer_score_ifrs(cls, ratios_bornees):
        """Calcule le score final ACREMAC pour IFRS"""
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
            
            logger.info(f"Score IFRS calculé: {score_final}")
            
            return round(score_final, 2)
            
        except Exception as e:
            logger.error(f"Erreur calcul score IFRS: {str(e)}")
            return 0.0

    @classmethod
    def determiner_classe_risque_ifrs(cls, score):
        """Détermine la classe de risque pour IFRS COBAC"""
        try:
            if score >= 2.10:
                return "Risque faible à excellent", 0.5, "Excellente santé financière selon IFRS"
            elif score >= 1.26:
                return "Risque acceptable", 2.0, "Bonne santé financière selon IFRS"
            elif score >= 0.28:
                return "Risque normal", 5.0, "Situation satisfaisante selon IFRS"
            elif score >= -1.00:
                return "Risque modéré", 15.0, "Vigilance recommandée selon IFRS"
            elif score >= -2.57:
                return "Risque important", 30.0, "Situation fragile selon IFRS"
            elif score >= -4.01:
                return "Risque élevé", 50.0, "Situation difficile selon IFRS"
            else:
                return "Risque très élevé", 75.0, "Situation très difficile selon IFRS"
                
        except Exception as e:
            logger.error(f"Erreur détermination classe risque IFRS: {str(e)}")
            return "Erreur", 0.0, "Erreur de calcul"

    @classmethod
    def calculer_score_complet_ifrs(cls, donnees):
        """
        Calcule le score ACREMAC complet pour bilan IFRS
        """
        try:
            # Calcul des ratios
            ratios = cls.calculer_ratios_ifrs(donnees)
            
            # Application des bornes
            ratios_bornees = cls.appliquer_bornes_ifrs(ratios)
            
            # Calcul du score
            score = cls.calculer_score_ifrs(ratios_bornees)
            
            # Détermination de la classe de risque
            classe_risque, probabilite, commentaire = cls.determiner_classe_risque_ifrs(score)
            
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
            
            logger.info(f"Score complet IFRS calculé: {resultat}")
            
            return resultat
            
        except Exception as e:
            logger.error(f"Erreur calcul score complet IFRS: {str(e)}")
            return {
                'score': 0.0,
                'ratios': {},
                'ratios_bornees': {},
                'classe_risque': "Erreur",
                'probabilite_defaillance': 0.0,
                'commentaire': "Erreur lors du calcul",
                'coefficients': {k: float(v) for k, v in cls.COEFFICIENTS.items()}
            }
            
    @classmethod
    def valider_coherence_donnees(cls, donnees, annee):
        """Valide la cohérence des données financières"""
        warnings = []
        
        # Vérifier l'échelle des montants
        if donnees['total_actif'] > Decimal('1000000000'):  # > 1 milliard
            warnings.append(f"Actif très élevé ({donnees['total_actif']}) pour l'année {annee}")
        
        if donnees['total_passif'] > Decimal('1000000000'):  # > 1 milliard
            warnings.append(f"Passif très élevé ({donnees['total_passif']}) pour l'année {annee}")
        
        # Vérifier la cohérence actif/passif
        if abs(donnees['total_actif'] - donnees['total_passif']) / max(donnees['total_actif'], Decimal('1')) > Decimal('0.1'):
            warnings.append(f"Écart important entre actif ({donnees['total_actif']}) et passif ({donnees['total_passif']})")
        
        # Vérifier EBE négatif
        if donnees['ebe'] < Decimal('0'):
            warnings.append(f"EBE négatif ({donnees['ebe']}) - entreprise potentiellement en difficulté")
        
        return warnings

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculer_score_bilan_ifrs(request):
    """
    Calcule le score ACREMAC avec données de bilan IFRS COBAC
    """
    serializer = BilanIFRSScoreSerializer(data=request.data)
    
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
                donnees_bilan = ScoreACREMACBilanIFRSService.extraire_donnees_bilan_ifrs(
                    acheteur, annee
                )
                
                if donnees_bilan:
                    resultat_calcul = ScoreACREMACBilanIFRSService.calculer_score_complet_ifrs(donnees_bilan)
                    resultats[annee_label] = resultat_calcul
                else:
                    resultats[annee_label] = {
                        'erreur': f'Données bilan IFRS non disponibles pour {annee}',
                        'score': 0.0,
                        'classe_risque': 'Données manquantes',
                        'probabilite_defaillance': 0.0,
                        'commentaire': f'Bilan IFRS {annee} non disponible'
                    }
            
            # Préparation de la réponse
            response_data = {
                'acheteur': acheteur.nom,
                'annees': {
                    'n': annee_n,
                    'n1': annee_n1,
                    'n2': annee_n2
                },
                'bilan_type': 'ifrs',
                'scores': resultats,
                'score_principal': resultats.get('n', {}).get('score', 0)
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Erreur calcul score bilan IFRS: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors du calcul du score bilan IFRS'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_annees_bilan_ifrs(request, acheteur_id):
    """
    Retourne les années de bilan IFRS disponibles pour un acheteur
    """
    try:
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        
        # Récupération des années disponibles (depuis ActifIFRS)
        annees = ActifIFRS.objects.filter(acheteur=acheteur).values_list('annee__annee', flat=True).distinct()
        annees_disponibles = sorted(annees, reverse=True)
        
        return Response({
            'acheteur': acheteur.nom,
            'bilan_type': 'ifrs',
            'years': annees_disponibles,
            'count': len(annees_disponibles)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération années bilan IFRS: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors de la récupération des années'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
