# views_scoring_anglais.py

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
from main.models import ScoringSansBilanAcheteur, Acheteur, ActifA, PassifA, ResultatA
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)

class ScoreACREMACBilanAnglaisService:
    """
    Service spécialisé pour le calcul du score ACREMAC avec bilan anglais
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
    def extraire_donnees_bilan_anglais(cls, acheteur, annee):
        """
        Extrait les données spécifiques au bilan anglais pour le calcul ACREMAC
        """
        try:
            # DEBUG: Vérifions ce qu'on reçoit
            logger.info(f"Recherche données pour acheteur {acheteur.id}, année: {annee}, type: {type(annee)}")
            
            # Si annee est un objet Annee, on prend son attribut annee
            if hasattr(annee, 'annee'):
                annee_value = annee.annee
            else:
                annee_value = annee
                
            logger.info(f"Valeur année utilisée pour la recherche: {annee_value}")
            
            actif = ActifA.objects.filter(acheteur=acheteur, annee__annee=annee_value).first()
            passif = PassifA.objects.filter(acheteur=acheteur, annee__annee=annee_value).first()
            resultat = ResultatA.objects.filter(acheteur=acheteur, annee__annee=annee_value).first()
            
            # Data for tests
            tests_resultat_count = 0
            tests_resultat = None
            
            # Compter les ResultatA pour l'acheteur 1
            tests_resultat_count = ResultatA.objects.filter(acheteur_id=1).count()

            # Voir les années disponibles
            tests_resultat = ResultatA.objects.filter(acheteur_id=1).values_list('annee__annee', flat=True)
            
            logger.info(f"Tests resultat (nbre): {tests_resultat_count is not None}")
            logger.info(f"Tests resultats: {tests_resultat is not None}")
            
            # DEBUG: Log des objets trouvés
            logger.info(f"Actif trouvé: {actif is not None}")
            logger.info(f"Passif trouvé: {passif is not None}")
            logger.info(f"Resultat trouvé: {resultat is not None}")
            
            if not all([actif, passif, resultat]):
                logger.warning(f"Données manquantes pour l'acheteur {acheteur.id}, année {annee_value}")
                return None
            
            # DEBUG: Log des valeurs principales
            logger.info(f"Total Actif: {actif.total_actif}")
            logger.info(f"Total Passif: {passif.total_passif}")
            logger.info(f"Ventes: {resultat.ventes}")
            
            # Vérification que les données ne sont pas toutes nulles
            total_data = sum([
                float(actif.total_actif or 0),
                float(passif.total_passif or 0),
                float(resultat.ventes or 0)
            ])
            
            if total_data == 0:
                logger.warning(f"Données toutes nulles pour l'acheteur {acheteur.id}, année {annee_value}")
                return None
            
            # Calcul des données nécessaires pour ACREMAC adaptées au bilan anglais
            donnees = {
                # R1: Frais financiers / EBE
                'frais_financiers': float(resultat.frais_financier or 0),
                'ebe': float(resultat.resultat_exploitation or 0),  # EBIT comme approximation de l'EBE
                
                # R2: (Créances + disponibilités) / Dettes CT
                'creances_disponibilites': float(
                    (actif.creances_commerciales_autres_creances or 0) + 
                    (actif.caisses_banques or 0)
                ),
                'dettes_court_terme': float(passif.total_passifs_courants or 0),
                
                # R3: Capitaux permanents / Passif
                'capitaux_permanents': float(
                    (passif.total_fonds_propres or 0) + 
                    (passif.total_passifs_non_courants or 0)
                ),
                'total_passif': float(passif.total_passif or 0),
                
                # R4: VA / CA
                'valeur_ajoutee': float(resultat.marge_brute or 0),
                'chiffre_affaires': float(resultat.ventes or 0),
                
                # R5: Trésorerie / Ventes (j)
                'tresorerie': float(actif.caisses_banques or 0),
                
                # R6: Fonds de roulement / CA (j)
                'fonds_roulement': float(
                    (passif.total_fonds_propres or 0) + 
                    (passif.total_passifs_non_courants or 0) - 
                    (actif.total_actifs_non_courants or 0)
                )
            }
            
            logger.info(f"Données extraites pour {acheteur.nom} - {annee_value}: {donnees}")
            return donnees
            
        except Exception as e:
            logger.error(f"Erreur extraction données bilan anglais: {str(e)}", exc_info=True)
            return None
        
    @classmethod
    def calculer_ratios(cls, donnees):
        """
        Calcule les 6 ratios du score ACREMAC pour le bilan anglais
        """
        ratios = {}
        
        try:
            # R1 = Frais financiers / EBE
            ebe = donnees.get('ebe', 0)
            frais_financiers = donnees.get('frais_financiers', 0)
            if ebe and ebe != 0:
                ratios['r1'] = (frais_financiers / ebe) * 100
            else:
                ratios['r1'] = 0
            
            # R2 = (Créances + disponibilités) / Dettes CT
            creances_dispo = donnees.get('creances_disponibilites', 0)
            dettes_ct = donnees.get('dettes_court_terme', 0)
            if dettes_ct and dettes_ct != 0:
                ratios['r2'] = (creances_dispo / dettes_ct) * 100
            else:
                ratios['r2'] = 0
            
            # R3 = Capitaux permanents / Passif
            capitaux_permanents = donnees.get('capitaux_permanents', 0)
            total_passif = donnees.get('total_passif', 0)
            if total_passif and total_passif != 0:
                ratios['r3'] = (capitaux_permanents / total_passif) * 100
            else:
                ratios['r3'] = 0
            
            # R4 = VA / CA
            valeur_ajoutee = donnees.get('valeur_ajoutee', 0)
            chiffre_affaires = donnees.get('chiffre_affaires', 0)
            if chiffre_affaires and chiffre_affaires != 0:
                ratios['r4'] = (valeur_ajoutee / chiffre_affaires) * 100
            else:
                ratios['r4'] = 0
            
            # R5 = Trésorerie / Ventes (j)
            tresorerie = donnees.get('tresorerie', 0)
            ca_journalier = chiffre_affaires / 360 if chiffre_affaires else 0
            if ca_journalier and ca_journalier != 0:
                ratios['r5'] = tresorerie / ca_journalier
            else:
                ratios['r5'] = 0
            
            # R6 = Fonds de roulement / CA (j)
            fonds_roulement = donnees.get('fonds_roulement', 0)
            if ca_journalier and ca_journalier != 0:
                ratios['r6'] = fonds_roulement / ca_journalier
            else:
                ratios['r6'] = 0
                
            logger.info(f"Ratios calculés: {ratios}")
                
        except Exception as e:
            logger.error(f"Erreur calcul ratios anglais: {str(e)}")
            ratios = {'r1': 0, 'r2': 0, 'r3': 0, 'r4': 0, 'r5': 0, 'r6': 0}
        
        return ratios

    @classmethod
    def appliquer_bornes(cls, ratios):
        """Applique les bornes aux ratios"""
        ratios_bornees = {}
        
        try:
            ratios_bornees['r1'] = max(cls.BORNES_R1[0], min(cls.BORNES_R1[1], ratios.get('r1', 0)))
            ratios_bornees['r2'] = max(cls.BORNES_R2[0], min(cls.BORNES_R2[1], ratios.get('r2', 0)))
            ratios_bornees['r3'] = max(cls.BORNES_R3[0], min(cls.BORNES_R3[1], ratios.get('r3', 0)))
            ratios_bornees['r4'] = max(cls.BORNES_R4[0], min(cls.BORNES_R4[1], ratios.get('r4', 0)))
            ratios_bornees['r5'] = max(cls.BORNES_R5[0], min(cls.BORNES_R5[1], ratios.get('r5', 0)))
            ratios_bornees['r6'] = max(cls.BORNES_R6[0], min(cls.BORNES_R6[1], ratios.get('r6', 0)))
            
            logger.info(f"Ratios après bornes: {ratios_bornees}")
            
        except Exception as e:
            logger.error(f"Erreur application bornes: {str(e)}")
            ratios_bornees = ratios.copy()
        
        return ratios_bornees

    @classmethod
    def calculer_score(cls, ratios_bornees):
        """Calcule le score final ACREMAC"""
        try:
            score = cls.COEFFICIENTS['constante']
            score += cls.COEFFICIENTS['r1'] * ratios_bornees.get('r1', 0)
            score += cls.COEFFICIENTS['r2'] * ratios_bornees.get('r2', 0)
            score += cls.COEFFICIENTS['r3'] * ratios_bornees.get('r3', 0)
            score += cls.COEFFICIENTS['r4'] * ratios_bornees.get('r4', 0)
            score += cls.COEFFICIENTS['r5'] * ratios_bornees.get('r5', 0)
            score += cls.COEFFICIENTS['r6'] * ratios_bornees.get('r6', 0)
            
            logger.info(f"Score calculé: {score}")
            
            return round(score, 2)
            
        except Exception as e:
            logger.error(f"Erreur calcul score: {str(e)}")
            return 0.0

    @classmethod
    def determiner_classe_risque(cls, score):
        """Détermine la classe de risque"""
        try:
            if score >= 3.5:
                return "Très faible risque", 0.5, "Excellente santé financière"
            elif score >= 2.5:
                return "Faible risque", 1.5, "Bonne santé financière"
            elif score >= 1.5:
                return "Risque modéré", 4.0, "Situation satisfaisante"
            elif score >= 0.5:
                return "Risque élevé", 15.0, "Vigilance recommandée"
            elif score >= -1.0:
                return "Risque très élevé", 40.0, "Situation fragile"
            else:
                return "Risque extrême", 70.0, "Situation très difficile"
                
        except Exception as e:
            logger.error(f"Erreur détermination classe risque: {str(e)}")
            return "Erreur", 0.0, "Erreur de calcul"

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
            
            resultat = {
                'score': score,
                'ratios': ratios,
                'ratios_bornees': ratios_bornees,
                'classe_risque': classe_risque,
                'probabilite_defaillance': probabilite,
                'commentaire': commentaire,
                'coefficients': cls.COEFFICIENTS
            }
            
            logger.info(f"Score complet calculé: {resultat}")
            
            return resultat
            
        except Exception as e:
            logger.error(f"Erreur calcul score complet anglais: {str(e)}")
            return {
                'score': 0.0,
                'ratios': {},
                'ratios_bornees': {},
                'classe_risque': "Erreur",
                'probabilite_defaillance': 0.0,
                'commentaire': "Erreur lors du calcul",
                'coefficients': cls.COEFFICIENTS
            }

    @classmethod
    def debug_donnees_bilan(cls, acheteur_id, annee):
        """
        Méthode de debug pour vérifier les données en base
        """
        try:
            acheteur = Acheteur.objects.get(id=acheteur_id)
            
            # Vérifier les années disponibles
            annees_actif = ActifA.objects.filter(acheteur=acheteur).values_list('annee__annee', flat=True)
            annees_passif = PassifA.objects.filter(acheteur=acheteur).values_list('annee__annee', flat=True)
            annees_resultat = ResultatA.objects.filter(acheteur=acheteur).values_list('annee__annee', flat=True)
            
            print(f"Années disponibles - Actif: {list(annees_actif)}")
            print(f"Années disponibles - Passif: {list(annees_passif)}")
            print(f"Années disponibles - Resultat: {list(annees_resultat)}")
            
            # Vérifier les données pour l'année spécifique
            actif = ActifA.objects.filter(acheteur=acheteur, annee__annee=annee).first()
            passif = PassifA.objects.filter(acheteur=acheteur, annee__annee=annee).first()
            resultat = ResultatA.objects.filter(acheteur=acheteur, annee__annee=annee).first()
            
            if actif:
                print(f"Actif {annee}: total_actif={actif.total_actif}")
            if passif:
                print(f"Passif {annee}: total_passif={passif.total_passif}")
            if resultat:
                print(f"Resultat {annee}: ventes={resultat.ventes}, resultat_exploitation={resultat.resultat_exploitation}")
                
        except Exception as e:
            print(f"Erreur debug: {e}")



# Les fonctions API restent identiques...
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculer_score_bilan_anglais(request):
    """
    Calcule le score ACREMAC avec données de bilan anglais
    """
    serializer = BilanAnglaisScoreSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            acheteur_id = serializer.validated_data['acheteur_id']
            # S'assurer que ce sont des entiers
            annee_n = int(serializer.validated_data['annee_n'])
            annee_n1 = int(serializer.validated_data['annee_n1'])
            annee_n2 = int(serializer.validated_data['annee_n2'])
            bilan_type = serializer.validated_data['bilan_type']
            
            # Récupération de l'acheteur
            acheteur = get_object_or_404(Acheteur, id=acheteur_id)
            
            # Calcul des scores pour les 3 années
            resultats = {}
            
            for annee_label, annee in [('n', annee_n), ('n1', annee_n1), ('n2', annee_n2)]:
                donnees_bilan = ScoreACREMACBilanAnglaisService.extraire_donnees_bilan_anglais(acheteur, annee)
                
                if donnees_bilan:
                    resultat_calcul = ScoreACREMACBilanAnglaisService.calculer_score_complet(donnees_bilan)
                    resultats[annee_label] = resultat_calcul
                else:
                    resultats[annee_label] = {
                        'erreur': f'Données bilan anglais non disponibles pour {annee}',
                        'score': 0.0,
                        'classe_risque': 'Données manquantes',
                        'probabilite_defaillance': 0.0,
                        'commentaire': f'Bilan anglais {annee} non disponible'
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
        logger.error(f"Erreur calcul score bilan anglais: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors du calcul du score bilan anglais'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
# ... (les autres fonctions API restent identiques)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_annees_bilan_anglais(request, acheteur_id):
    """
    Retourne les années de bilan anglais disponibles pour un acheteur
    """
    try:
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        
        # Récupération des années de bilan anglais disponibles
        annees = ActifA.objects.filter(acheteur=acheteur).values_list('annee__annee', flat=True).distinct()
        annees_disponibles = sorted(annees, reverse=True)
        
        return Response({
            'acheteur': acheteur.nom,
            'bilan_type': 'anglais',
            'years': annees_disponibles,
            'count': len(annees_disponibles)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération années bilan anglais: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors de la récupération des années'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_details_bilan_anglais(request, acheteur_id, annee):
    """
    Retourne les détails du bilan anglais pour analyse
    """
    try:
        acheteur = get_object_or_404(Acheteur, id=acheteur_id)
        
        actif = ActifA.objects.filter(acheteur=acheteur, annee__annee=annee).first()
        passif = PassifA.objects.filter(acheteur=acheteur, annee__annee=annee).first()
        resultat = ResultatA.objects.filter(acheteur=acheteur, annee__annee=annee).first()
        
        if not all([actif, passif, resultat]):
            return Response({
                'erreur': f'Bilan anglais non complet pour {annee}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Données détaillées pour l'analyse
        details = {
            'annee': annee,
            'actif': {
                'biens_installations_equipements': float(actif.biens_installations_equipements or 0),
                'inventaire': float(actif.inventaire or 0),
                'creances_commerciales': float(actif.creances_commerciales_autres_creances or 0),
                'caisses_banques': float(actif.caisses_banques or 0),
                'total_actifs_non_courants': float(actif.total_actifs_non_courants or 0),
                'total_actifs_courants': float(actif.total_actifs_courants or 0),
                'total_actif': float(actif.total_actif or 0)
            },
            'passif': {
                'capital_reserves': float(passif.capital_reserves or 0),
                'capital_declare': float(passif.capital_declare or 0),
                'benefices_non_distribues': float(passif.benefices_non_distribues or 0),
                'total_fonds_propres': float(passif.total_fonds_propres or 0),
                'pret_bancaire': float(passif.pret_bancaire or 0),
                'dettes_commerciales': float(passif.dettes_commerciales_autres_dettes or 0),
                'decouvert_bancaire': float(passif.decouvert_bancaire or 0),
                'total_passifs_courants': float(passif.total_passifs_courants or 0),
                'total_passif': float(passif.total_passif or 0)
            },
            'resultat': {
                'ventes': float(resultat.ventes or 0),
                'charges_exploitation': float(resultat.charges_exploitation or 0),
                'marge_brute': float(resultat.marge_brute or 0),
                'frais_vente_generaux_administratifs': float(resultat.frais_vente_generaux_administratifs or 0),
                'resultat_exploitation': float(resultat.resultat_exploitation or 0),
                'frais_financier': float(resultat.frais_financier or 0),
                'resultat_net': float(resultat.resultat_net or 0)
            }
        }
        
        return Response(details, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur récupération détails bilan anglais: {str(e)}")
        return Response(
            {'erreur': 'Erreur lors de la récupération des détails du bilan'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )