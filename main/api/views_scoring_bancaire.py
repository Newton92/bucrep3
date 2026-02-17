# views_scoring_bancaire.py - VERSION COMPLÈTEMENT CORRIGÉE
import logging
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main.models import Assets, Liabilities, Expenses, Products, OffBalanceSheet, Acheteur
from main.serializers import BilanBancaireScoreSerializer

logger = logging.getLogger(__name__)

class ScoreACREMACBilanBancaireService:
    """
    Service spécialisé pour le calcul du score ACREMAC avec bilan bancaire
    """
    
    # Coefficients ACREMAC adaptés pour les banques
    COEFFICIENTS = {
        'constante': 0.65,
        'r1': 0.045,   # Ratio de solvabilité
        'r2': 0.032,   # Ratio de liquidité
        'r3': 0.028,   # Ratio de rentabilité
        'r4': 0.015,   # Ratio de qualité des actifs
        'r5': 0.012,   # Ratio d'efficience
        'r6': 0.008    # Ratio de diversification
    }

    @staticmethod
    def _safe_ratio(numerator, denominator, multiplier=1.0):
        """Retourne 0.0 si le dénominateur est invalide."""
        try:
            denominator = float(denominator or 0)
            if denominator == 0:
                return 0.0
            return (float(numerator or 0) / denominator) * float(multiplier)
        except (TypeError, ValueError, ZeroDivisionError):
            return 0.0

    @classmethod
    def extraire_donnees_bilan_bancaire(cls, acheteur, annee, bilan_type="annuel", semestre=None):
        """
        Extrait les données spécifiques au bilan bancaire pour le calcul ACREMAC
        """
        try:
            annee_value = annee.annee if hasattr(annee, 'annee') else annee
            
            logger.info(f"Recherche données bilan bancaire - Acheteur: {acheteur.id}, Année: {annee_value}, Type: {bilan_type}")
            
            # Filtres communs
            filters = {
                'acheteur': acheteur,
                'annee__annee': annee_value,
                'type_bilan': bilan_type
            }
            if semestre:
                filters['semestre'] = semestre
            
            # Récupération des données
            assets = Assets.objects.filter(**filters).first()
            liabilities = Liabilities.objects.filter(**filters).first()
            expenses = Expenses.objects.filter(**filters).first()
            products = Products.objects.filter(**filters).first()
            off_balance = OffBalanceSheet.objects.filter(**filters).first()
            
            logger.info(f"Assets trouvé: {assets is not None}")
            logger.info(f"Liabilities trouvé: {liabilities is not None}")
            logger.info(f"Expenses trouvé: {expenses is not None}")
            logger.info(f"Products trouvé: {products is not None}")
            logger.info(f"OffBalance trouvé: {off_balance is not None}")
            
            if not all([assets, liabilities, expenses, products]):
                logger.warning(f"Données incomplètes pour le bilan bancaire - Acheteur: {acheteur.id}, Année: {annee_value}")
                return None
            
            # FONCTION HELPER POUR GÉRER LES MÉTHODES/PROPRIÉTÉS
            def get_value(obj, attr_name, default=0.0):
                """
                Récupère une valeur d'un objet, qu'elle soit méthode, propriété ou champ
                """
                try:
                    # Obtenir l'attribut
                    attr = getattr(obj, attr_name, default)
                    
                    # Si c'est une méthode, l'appeler
                    if callable(attr):
                        result = attr()
                        return float(result) if result is not None else default
                    # Si c'est déjà une valeur
                    else:
                        return float(attr) if attr is not None else default
                        
                except (TypeError, ValueError, AttributeError) as e:
                    logger.warning(f"Erreur récupération {attr_name}: {e}")
                    return default
            
            # Calcul des données nécessaires pour ACREMAC adaptées au bilan bancaire
            donnees = {
                # Données d'actif - AVEC GESTION DES MÉTHODES
                'total_actif': get_value(assets, 'total_assets'),
                'pret_interbancaire': get_value(assets, 'pret_interbancaire'),
                'creance_clientele': get_value(assets, 'creance_sur_la_clientele'),
                'titres_placement': get_value(assets, 'titres_placement'),
                
                # Données de passif - AVEC GESTION DES MÉTHODES
                'total_passif': get_value(liabilities, 'total_liabilities'),
                'dette_interbancaire': get_value(liabilities, 'dette_interbancaire'),
                'dette_clientele': get_value(liabilities, 'dette_envers_clientelle'),
                'capitaux_propres': (
                    get_value(liabilities, 'capital_ou_dotation') +
                    get_value(liabilities, 'primes_liees_reserve_capital') +
                    get_value(liabilities, 'ecarts_reevaluation') +
                    get_value(liabilities, 'benefices_non_distribue') +
                    get_value(liabilities, 'resultat_net_exercie')
                ),
                
                # Données de résultat - AVEC GESTION DES MÉTHODES
                'total_produits': get_value(products, 'total_produit'),
                'total_charges': get_value(expenses, 'total_des_charges'),
                'interets_produits': get_value(products, 'interet_produit_assimile'),
                'interets_charges': get_value(expenses, 'interet_charges_assimilee'),
                'commissions_produits': get_value(products, 'commissions'),
                'commissions_charges': get_value(expenses, 'commissions'),
                
                # Données hors bilan
                'engagements_donnes': get_value(off_balance, 'total_engagements_donnes') if off_balance else 0.0,
                'engagements_recus': get_value(off_balance, 'total_engagements_recus') if off_balance else 0.0,
                
                # Autres indicateurs
                'frais_personnel': get_value(expenses, 'frais_personnel'),
                'frais_generaux': get_value(expenses, 'autres_frais_generaux'),
            }
            
            logger.info(f"Données extraites bilan bancaire pour {acheteur.nom} - {annee_value}: {donnees}")
            return donnees
            
        except Exception as e:
            logger.error(f"Erreur extraction données bilan bancaire: {str(e)}", exc_info=True)
            return None

    @classmethod
    def calculer_ratios_bancaires(cls, donnees):
        """
        Calcule les 6 ratios du score ACREMAC adaptés pour les banques
        """
        ratios = {}
        
        try:
            # R1: Ratio de solvabilité (Capitaux propres / Total actif)
            total_actif = donnees.get('total_actif', 0)
            capitaux_propres = donnees.get('capitaux_propres', 0)
            ratios['r1'] = cls._safe_ratio(capitaux_propres, total_actif, 100)
            
            # R2: Ratio de liquidité (Actifs liquides / Dettes à court terme)
            actifs_liquides = (
                donnees.get('pret_interbancaire', 0) + 
                donnees.get('titres_placement', 0)
            )
            dettes_court_terme = (
                donnees.get('dette_interbancaire', 0) + 
                donnees.get('dette_clientele', 0)
            )
            ratios['r2'] = cls._safe_ratio(actifs_liquides, dettes_court_terme, 100)
            
            # R3: Ratio de rentabilité (Résultat net / Total actif)
            resultat_net = donnees.get('total_produits', 0) - donnees.get('total_charges', 0)
            ratios['r3'] = cls._safe_ratio(resultat_net, total_actif, 100)
            
            # R4: Ratio de qualité des actifs (Créances clientèle / Total actif)
            creance_clientele = donnees.get('creance_clientele', 0)
            ratios['r4'] = cls._safe_ratio(creance_clientele, total_actif, 100)
            
            # R5: Ratio d'efficience (Charges / Produits)
            total_produits = donnees.get('total_produits', 0)
            total_charges = donnees.get('total_charges', 0)
            ratios['r5'] = cls._safe_ratio(total_charges, total_produits, 100)
            
            # R6: Ratio de diversification (Produits hors intérêts / Total produits)
            produits_hors_interets = total_produits - donnees.get('interets_produits', 0)
            ratios['r6'] = cls._safe_ratio(produits_hors_interets, total_produits, 100)
                
            logger.info(f"Ratios bancaires calculés: {ratios}")
                
        except Exception as e:
            logger.error(f"Erreur calcul ratios bancaires: {str(e)}")
            ratios = {'r1': 0, 'r2': 0, 'r3': 0, 'r4': 0, 'r5': 0, 'r6': 0}
        
        return ratios

    @classmethod
    def appliquer_bornes_bancaires(cls, ratios):
        """Applique les bornes spécifiques aux ratios bancaires"""
        ratios_bornees = {}
        
        try:
            # Bornes sans plancher biaisé pour éviter d'améliorer artificiellement le score
            ratios_bornees['r1'] = max(0, min(100, ratios.get('r1', 0)))     # Solvabilité
            ratios_bornees['r2'] = max(0, min(200, ratios.get('r2', 0)))     # Liquidité
            ratios_bornees['r3'] = max(-100, min(100, ratios.get('r3', 0)))  # Rentabilité
            ratios_bornees['r4'] = max(0, min(100, ratios.get('r4', 0)))     # Qualité d'actif
            ratios_bornees['r5'] = max(0, min(200, ratios.get('r5', 0)))     # Efficience
            ratios_bornees['r6'] = max(0, min(100, ratios.get('r6', 0)))     # Diversification
            
            logger.info(f"Ratios après bornes: {ratios_bornees}")
            
        except Exception as e:
            logger.error(f"Erreur application bornes bancaires: {str(e)}")
            ratios_bornees = ratios.copy()
        
        return ratios_bornees

    @classmethod
    def calculer_score_bancaire(cls, ratios_bornees):
        """Calcule le score final ACREMAC pour banques"""
        try:
            score = cls.COEFFICIENTS['constante']
            score += cls.COEFFICIENTS['r1'] * ratios_bornees.get('r1', 0)
            score += cls.COEFFICIENTS['r2'] * ratios_bornees.get('r2', 0)
            score += cls.COEFFICIENTS['r3'] * ratios_bornees.get('r3', 0)
            score += cls.COEFFICIENTS['r4'] * ratios_bornees.get('r4', 0)
            score += cls.COEFFICIENTS['r5'] * ratios_bornees.get('r5', 0)
            score += cls.COEFFICIENTS['r6'] * ratios_bornees.get('r6', 0)
            
            logger.info(f"Score bancaire calculé: {score}")
            
            return round(score, 2)
            
        except Exception as e:
            logger.error(f"Erreur calcul score bancaire: {str(e)}")
            return 0.0

    @classmethod
    def determiner_classe_risque_bancaire(cls, score):
        """Détermine la classe de risque pour les banques"""
        try:
            if score >= 4.0:
                return "Très faible risque", 0.3, "Excellente santé financière"
            elif score >= 3.0:
                return "Faible risque", 1.2, "Bonne santé financière"
            elif score >= 2.0:
                return "Risque modéré", 3.5, "Situation satisfaisante"
            elif score >= 1.0:
                return "Risque élevé", 12.0, "Vigilance recommandée"
            elif score >= -0.5:
                return "Risque très élevé", 35.0, "Situation fragile"
            else:
                return "Risque extrême", 65.0, "Situation très difficile"
                
        except Exception as e:
            logger.error(f"Erreur détermination classe risque bancaire: {str(e)}")
            return "Erreur", 0.0, "Erreur de calcul"

    @classmethod
    def calculer_score_complet_bancaire(cls, donnees):
        """
        Calcule le score ACREMAC complet pour bilan bancaire
        """
        try:
            # Calcul des ratios
            ratios = cls.calculer_ratios_bancaires(donnees)
            
            # Application des bornes
            ratios_bornees = cls.appliquer_bornes_bancaires(ratios)
            
            # Calcul du score
            score = cls.calculer_score_bancaire(ratios_bornees)
            
            # Détermination de la classe de risque
            classe_risque, probabilite, commentaire = cls.determiner_classe_risque_bancaire(score)
            
            resultat = {
                'score': score,
                'ratios': ratios,
                'ratios_bornees': ratios_bornees,
                'classe_risque': classe_risque,
                'probabilite_defaillance': probabilite,
                'commentaire': commentaire,
                'coefficients': cls.COEFFICIENTS
            }
            
            logger.info(f"Score complet bancaire calculé: {resultat}")
            
            return resultat
            
        except Exception as e:
            logger.error(f"Erreur calcul score complet bancaire: {str(e)}")
            return {
                'score': 0.0,
                'ratios': {},
                'ratios_bornees': {},
                'classe_risque': "Erreur",
                'probabilite_defaillance': 0.0,
                'commentaire': "Erreur lors du calcul",
                'coefficients': cls.COEFFICIENTS
            }

# Les fonctions API restent identiques...
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculer_score_bilan_bancaire(request):
    """
    Calcule le score ACREMAC avec données de bilan bancaire
    """
    serializer = BilanBancaireScoreSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            acheteur_id = serializer.validated_data['acheteur_id']
            annee_n = serializer.validated_data['annee_n']
            annee_n1 = serializer.validated_data['annee_n1']
            annee_n2 = serializer.validated_data['annee_n2']
            bilan_type = serializer.validated_data['bilan_type']
            semestre = serializer.validated_data.get('semestre')
            
            # Récupération de l'acheteur
            acheteur = get_object_or_404(Acheteur, id=acheteur_id)
            
            # Calcul des scores pour les 3 années
            resultats = {}
            
            for annee_label, annee in [('n', annee_n), ('n1', annee_n1), ('n2', annee_n2)]:
                donnees_bilan = ScoreACREMACBilanBancaireService.extraire_donnees_bilan_bancaire(
                    acheteur, annee, bilan_type, semestre
                )
                
                if donnees_bilan:
                    resultat_calcul = ScoreACREMACBilanBancaireService.calculer_score_complet_bancaire(donnees_bilan)
                    resultats[annee_label] = resultat_calcul
                else:
                    resultats[annee_label] = {
                        'erreur': f'Données bilan bancaire non disponibles pour {annee}',
                        'score': 0.0,
                        'classe_risque': 'Données manquantes',
                        'probabilite_defaillance': 0.0,
                        'commentaire': f'Bilan bancaire {annee} non disponible'
                    }
            
            # Préparation de la réponse
            response_data = {
                'acheteur': acheteur.nom,
                'annees': {
                    'n': annee_n,
                    'n1': annee_n1,
                    'n2': annee_n2
                },
                'bilan_type': bilan_type,
                'semestre': semestre,
                'scores': resultats,
                'score_principal': resultats.get('n', {}).get('score', 0)
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Erreur calcul score bilan bancaire: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors du calcul du score bilan bancaire'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_annees_bilan_bancaire(request, acheteur_id):
    """
    Retourne les années de bilan bancaire disponibles pour un acheteur
    """
    try:
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        
        # Récupération des années disponibles (depuis Assets)
        annees = Assets.objects.filter(acheteur=acheteur).values_list('annee__annee', flat=True).distinct()
        annees_disponibles = sorted(annees, reverse=True)
        
        return Response({
            'acheteur': acheteur.nom,
            'bilan_type': 'bancaire',
            'years': annees_disponibles,
            'count': len(annees_disponibles)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération années bilan bancaire: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors de la récupération des années'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
