# Fichier : views_reporting.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from main.models import Annee, Devise, Commande, Resume, CodeNafAcheteur, CodeNafAcheteur
from main.models import Resume, RiskRating, RiskManagment, OpinionCreditAcremac, DonneesEnregistrement, AntecedantsJuridique
from main.models import ResponsableAcheteur, ConseilAdministration, CompositionCapitalSocial, CompositionAction, Structure
from main.models import Annee

from main.serializers_reporting import AnneeSerializer, DeviseSerializer, CommandeSerializer, RapportSolvabiliteSerializer

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from datetime import datetime, timedelta
from django.utils import timezone
import html


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_annees(request):
    annees = Annee.objects.filter(is_active=True).order_by('-annee')
    serializer = AnneeSerializer(annees, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_devises(request):
    devises = Devise.objects.filter(is_active=True).order_by('nom')
    serializer = DeviseSerializer(devises, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_commandes_acheteur_two(request, acheteur_id):
    # CORRECTION : Retirer le filtre is_active qui n'existe pas
    commandes = Commande.objects.filter(
        acheteur_id=acheteur_id
    ).order_by('-created_at')[:10]  # Les 10 dernières commandes
    serializer = CommandeSerializer(commandes, many=True)
    return Response(serializer.data)


# Dans views_reporting.py, modifiez la vue liste_commandes_acheteur
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_commandes_acheteur(request, acheteur_id):
    try:
        commandes = Commande.objects.filter(acheteur_id=acheteur_id)
        
        # Filtrage par période
        jours = request.GET.get('jours')
        mois = request.GET.get('mois') 
        annees = request.GET.get('annees')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        
        date_limit = timezone.now()
        
        if jours:
            date_limit = timezone.now() - timedelta(days=int(jours))
        elif mois:
            date_limit = timezone.now() - timedelta(days=30*int(mois))
        elif annees:
            date_limit = timezone.now() - timedelta(days=365*int(annees))
        elif date_debut and date_fin:
            try:
                date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                commandes = commandes.filter(created_at__date__range=[date_debut_obj, date_fin_obj])
            except ValueError:
                pass
        else:
            # Par défaut, 3 derniers mois
            date_limit = timezone.now() - timedelta(days=90)
        
        if not (date_debut and date_fin):
            commandes = commandes.filter(created_at__gte=date_limit)
        
        commandes = commandes.order_by('-created_at')[:20]  # Augmenté à 20 commandes
        
        serializer = CommandeSerializer(commandes, many=True)
        return Response(serializer.data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)




from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status  # Ajoutez cette importation
from main.models import Annee, Devise, Commande, Acheteur, CodeNaceAcheteur  # Ajoutez Acheteur ici
from main.serializers_reporting import AnneeSerializer, DeviseSerializer, CommandeSerializer, RapportSolvabiliteSerializer
from datetime import datetime, timedelta
from django.utils import timezone

# ... vos autres vues ...


def get_logo_data():
    # Chercher le logo dans les dossiers statiques
    logo_paths = [
        os.path.join(settings.STATIC_ROOT, 'images', 'acremac_option.png'),
        os.path.join(settings.BASE_DIR, 'main', 'static', 'images', 'acremac_option.png'),
    ]
    
    for logo_path in logo_paths:
        try:
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    return f"data:image/png;base64,{encoded_string}"
        except Exception as e:
            print(f"Erreur lors du chargement du logo {logo_path}: {e}")
            continue
    
    return None


def get_logo_path():
    # Chercher le logo dans les dossiers statiques
    logo_paths = [
        os.path.join(settings.STATIC_ROOT, 'images', 'acremac_option.png'),
        os.path.join(settings.BASE_DIR, 'main', 'static', 'images', 'acremac_option.png'),
    ]
    
    for logo_path in logo_paths:
        if os.path.exists(logo_path):
            return logo_path
    
    return None


def format_currency(value):
    """Formate un nombre décimal en chaîne avec des séparateurs de milliers."""
    if value is None:
        return "Non spécifié"
    return f"{value:,.2f}".replace(",", " ").replace(".", ",") # Exemple de formatage français


@api_view(['POST', 'GET'])  # Autorisez GET temporairement pour tester
@permission_classes([IsAuthenticated])
def generer_rapport_solvabilite(request):
    print("🎯 VUE generer_rapport_solvabilite APPELÉE !")
    print("📝 Méthode:", request.method)
    print("👤 Utilisateur:", request.user.username)
    print("📦 Données:", request.data)
    print("🔗 Chemin:", request.path)
    print("🌐 URL complète:", request.build_absolute_uri())
    
    serializer = RapportSolvabiliteSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        acheteur_id = data.get('acheteur_id')
        print(data)
        print(f"🔍 Acheteur ID reçu: {acheteur_id} (type: {type(acheteur_id)})")

        # Vérifiez que acheteur_id est un entier valide
        if not acheteur_id or acheteur_id <= 0:
            return Response(
                {"error": "ID de l'acheteur invalide ou manquant."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Récupération de l'acheteur
        try:
            acheteur = Acheteur.objects.get(pk=acheteur_id)
        except Acheteur.DoesNotExist:
            return Response(
                {"error": f"Acheteur avec l'ID {acheteur_id} non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupération de la commande si spécifiée
        commande = None
        if data.get('inclure_commande') == 'oui' and data.get('commande_id'):
            try:
                commande = Commande.objects.get(pk=data['commande_id'])
            except Commande.DoesNotExist:
                pass
        
        # Récupération du Résumé executif
        # Recuperation du resume en fonction de l'acheteur
        resume = None
        try:
            resume = Resume.objects.filter(acheteur=acheteur).first()
        except Resume.DoesNotExist:
            pass
            
        # Recuperation des codes NAF de l'acheteur
        naf_codes = list(CodeNafAcheteur.objects.filter(acheteur=acheteur).values_list('code', flat=True))
        
        # Recuperation des codes NACE de l'acheteur
        nace_codes = list(CodeNaceAcheteur.objects.filter(acheteur=acheteur).values_list('code', flat=True))
        
        # Récupération Evaluation de risque
        # Au niveau du template il faudra afficher une image en fonction de la valeur totale trouve
        # Ex. si risk_rating_value = 4 on devra afficher l'image qui se trouve dans main/static/riskrating/4.svg
        # Ex. si risk_rating_value = 6 on devra afficher l'image qui se trouve dans main/static/riskrating/6.svg
        # Les images dans le dossier riskrating sont nommees de 0 a 8 donc[o.svg, 1.svg, ...., 8.svg]
        # Recuperation de l'evaluation de risque chiffree de l'acheteur  
        # Récupération de l'évaluation de risque
        risk_rating = RiskRating.objects.filter(acheteur=acheteur).first()

        # Valeur de rating entre 0 et 8
        risk_rating_value = 0

        if risk_rating:
            champs = [
                'remboursabilite',
                'situation_liquidite',
                'performance_rentabilite',
                'perspective_secteur',
                'qualite_information_analyse',
                'existence_garantie',
                'terme_financier_duree_pret',
                'mesure_propre_soutenir_credit',
            ]

            for c in champs:
                if getattr(risk_rating, c, False):
                    risk_rating_value += 1

            # Limite max = 8
            risk_rating_value = min(risk_rating_value, 8)

        
        # Récupération Opinion Credit ACREMAC
        acremac_opinion = None
        try:
            acremac_opinion = OpinionCreditAcremac.objects.filter(acheteur=acheteur).first()
        except OpinionCreditAcremac.DoesNotExist:
            pass
        
        # Création du dictionnaire pour la mise en surbrillance
        # Les valeurs sont 1 pour "vrai" (surligné) et 0 pour "faux" (non surligné)
        # selon la logique que vous avez dans votre modèle
        highlighted_risks = {
            'risque_de_defaut': acremac_opinion.risque_de_defaut if acremac_opinion else 0,
            'risque_de_concentration_credit': acremac_opinion.risque_de_concentration_credit if acremac_opinion else 0,
            'risque_de_reputation': acremac_opinion.risque_de_reputation if acremac_opinion else 0,
            'risque_pays': acremac_opinion.risque_pays if acremac_opinion else 0,
            'risque_de_taux_dinteret': acremac_opinion.risque_de_taux_dinteret if acremac_opinion else 0,
            'risque_de_liquidite': acremac_opinion.risque_de_liquidite if acremac_opinion else 0,
            'risque_eleve': acremac_opinion.risque_eleve if acremac_opinion else 0,
            'risque_moyen': acremac_opinion.risque_moyen if acremac_opinion else 0,
            'risque_faible': acremac_opinion.risque_faible if acremac_opinion else 0,
        }  
        
        note_values = []
        if acremac_opinion:
            # Créez une liste de tous les champs de note
            # Utilisez une boucle pour rendre le code plus propre
            risk_fields = [
                'risque_de_defaut',
                'risque_de_concentration_credit',
                'risque_de_reputation',
                'risque_pays',
                'risque_de_taux_dinteret',
                'risque_de_liquidite',
                'risque_eleve',
                'risque_moyen',
                'risque_faible',
            ]

            # Isolez les valeurs qui ne sont pas 0
            for field in risk_fields:
                value = getattr(acremac_opinion, field)
                if value is not None and value != 0:
                    note_values.append(str(value)) # Convertir en chaîne de caractères

        # Formatez la liste en une chaîne séparée par des virgules
        notes_str = ", ".join(note_values)
        
        # Récupération Donnees Enregistrement
        donnees_enregistrement = None
        try:
            donnees_enregistrement = DonneesEnregistrement.objects.filter(acheteur=acheteur).first()
        except DonneesEnregistrement.DoesNotExist:
            pass
        
        
        # Récupération Antecedents juridiques
        # Recuperation des donnees enregistrement en fonction de l'acheteur 
        antecedants_juridiques = None
        try:
            antecedants_juridiques = AntecedantsJuridique.objects.filter(acheteur=acheteur)
        except AntecedantsJuridique.DoesNotExist:
            pass
        
        # Modifiez cette section pour récupérer une liste d'antécédents juridiques
        list_antecedants_data = []
        for antecedant in antecedants_juridiques:
            list_antecedants_data.append({
                "dossier_faillite": antecedant.dossier_faillite if antecedant.dossier_faillite else "Non spécifié",
                "jugement_cour": antecedant.jugement_cour if antecedant.jugement_cour else "Non spécifié",
                "antecedant_redressement": antecedant.antecedant_redressement if antecedant.antecedant_redressement else "Non spécifié",
                "autre": antecedant.autre if antecedant.autre else "Non spécifié",
                "commentaire": antecedant.commentaire if antecedant.commentaire else "Non spécifié",
            })
          
        # Récupération Management et Staff
        # Recuperation des elements de gestion de risque de l'acheteur 
        risk_management = None
        try:
            risk_management = RiskManagment.objects.get(acheteur=acheteur)
        except RiskManagment.DoesNotExist:
            pass
        
        
        # Recuperation des dirigeants de l'acheteur 
        responsables = ResponsableAcheteur.objects.filter(acheteur=acheteur)
        list_responsables_data = []
        for responsable in responsables:
            list_responsables_data.append({
                "nom": responsable.nom if responsable.nom else "Non spécifié",
                "prenom": responsable.prenom if responsable.prenom else "Non spécifié",
                "sexe": responsable.sexe if responsable.sexe else "Non spécifié",
                "poste": responsable.poste_ref.libelle if responsable.poste_ref else responsable.poste,
                "nationalite": responsable.nationalite if responsable.nationalite else "Non spécifié",
                "commentaire": responsable.commentaire if responsable.commentaire else "Non spécifié",
            })

        # Recuperation des membres du conseil d'administration de l'acheteur 
        conseil_administration_membres = ConseilAdministration.objects.filter(acheteur=acheteur)
        list_ca_membres_data = []
        for membre in conseil_administration_membres:
            list_ca_membres_data.append({
                "nom": membre.nom if membre.nom else "Non spécifié",
                "fonction_dans_le_conseil": membre.fonction_dans_le_conseil_ref.libelle if membre.fonction_dans_le_conseil_ref else membre.fonction_dans_le_conseil,
                "numero_adresse": membre.numero_adresse if membre.numero_adresse else "Non spécifié",
                "rue_adresse": membre.rue_adresse if membre.rue_adresse else "Non spécifié",
                "code_postale_adresse": membre.code_postale_adresse if membre.code_postale_adresse else "Non spécifié",
                "commentaire": membre.commentaire if membre.commentaire else "Non spécifié",
            })
          
        
        # Récupération Capital social
        # Recuperation de la composition du capital social de l'acheteur
        try:
            composition_capital_social = CompositionCapitalSocial.objects.get(acheteur=acheteur)
        except CompositionCapitalSocial.DoesNotExist:
            composition_capital_social = None
            
         
        # Récupération Actionnarat/Proprietaires
        # Recuperation des actionnaires de l'acheteur
        shareholders = CompositionAction.objects.filter(acheteur=acheteur)
        list_shareholders_data = []
        for shareholder in shareholders:
            list_shareholders_data.append({
                "nom": shareholder.nom if shareholder.nom else "Non spécifié",
                "prenom": shareholder.prenom if shareholder.prenom else "Non spécifié",
                "pourcentage": shareholder.pourcentage if shareholder.pourcentage else "Non spécifié",
                "commentaire": shareholder.commentaire if shareholder.commentaire else "Non spécifié",
            })
        
        # Récupération Affiliations
        # Recuperation des affiliations (filiales ou branches) de l'acheteur
        affiliations = Structure.objects.filter(acheteur=acheteur)
        list_affiliations_data = []
        for affiliation in affiliations:
            list_affiliations_data.append({
                "nom": affiliation.nom if affiliation.nom else "Non spécifié",
                "type_affiliation": affiliation.type_affiliation_ref.libelle if affiliation.type_affiliation_ref else affiliation.type_affiliation,
                "numero_adresse": affiliation.numero_adresse if affiliation.numero_adresse else "Non spécifié",
                "rue_adresse": affiliation.rue_adresse if affiliation.rue_adresse else "Non spécifié",
                "code_postale_adresse": affiliation.code_postale_adresse if affiliation.code_postale_adresse else "Non spécifié",
                "commentaire": affiliation.commentaire if affiliation.commentaire else "Non spécifié",
            })
        # Récupération Analyse sectorielle
        # Récupération Comptes financiers
        # Récupération Etats financiers 
        # Récupération Ratios
        # Récupération Structure financiere
        # Récupération Scoring ACREMAC
        # Récupération Operations et Historique
        # Récupération Comportement de paiement
        # Récupération Conclusion et Avis
       
        
        
        
        # Préparation des données pour le template
        report_data = {
            "header_report": {
                "acremac_services": "Services ACREMAC Gabon",
                "acremac_mail": "credit.report@acremac.com",
                "date_today": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            },
            "commande": {
                "title_1": "DETAILS COMMANDE",
                "client": commande.client.username if commande and commande.client else "Non spécifié",
                "ref_client": commande.reference_client if commande else "Non spécifié",
                "notre_ref": commande.notre_ref if commande else "Non spécifié",
                "date_recept_commande": commande.date_recept_commande.strftime("%d/%m/%Y") if commande and commande.date_recept_commande else "Non spécifié",
                "date_rapport": commande.date_rapport.strftime("%d/%m/%Y") if commande and commande.date_rapport else "Non spécifié",
                "delais": commande.delais if commande else "Non spécifié",
                "priorite": commande.priorite if commande else "Non spécifié",
                "type_rapport": commande.type_rapport if commande else "Non spécifié"
            },
            "identification": {
                "title_2": "IDENTIFICATION",
                "client_info": {
                    "nom": commande.raison_sociale if hasattr(commande, 'raison_sociale') else "Non spécifié",
                    "numero_adresse": commande.numero_adresse if hasattr(commande, 'numero_adresse') else "Non spécifié",
                    "rue_adresse": commande.rue_adresse if hasattr(commande, 'rue_adresse') else "Non spécifié",
                    "code_postale_adresse": commande.code_postale_adresse if hasattr(commande, 'code_postale_adresse') else "Non spécifié",
                    "telephone": commande.telephone if hasattr(commande, 'telephone') else "Non spécifié",
                    "email": commande.email if hasattr(commande, 'email') else "Non spécifié",
                    "pays": commande.pays.nom if hasattr(commande, 'pays') else "Non spécifié",
                    "ville": commande.ville.nom if hasattr(commande, 'ville') else "Non spécifié",
                },
                "acremac_info": {
                    "nom": acheteur.nom if hasattr(acheteur, 'nom') else "Non spécifié",
                    "sigle": acheteur.sigle if hasattr(acheteur, 'sigle') else "Non spécifié",
                    "email": acheteur.email if hasattr(acheteur, 'email') else "Non spécifié",
                    "boite_postale": acheteur.boite_postale if hasattr(acheteur, 'boite_postale') else "Non spécifié",
                    "pays": acheteur.pays.nom if hasattr(acheteur, 'pays') else "Non spécifié",
                    "province": acheteur.province.nom if hasattr(acheteur, 'province') else "Non spécifié",
                    "ville": acheteur.ville.nom if hasattr(acheteur, 'ville') else "Non spécifié",
                    "fax": acheteur.fax if hasattr(acheteur, 'fax') else "Non spécifié",
                    "numero_adresse": acheteur.numero_adresse if hasattr(acheteur, 'numero_adresse') else "Non spécifié",
                    "code_postal": acheteur.code_postal if hasattr(acheteur, 'code_postal') else "Non spécifié",
                }
            },
            "additional_information": {
                "title_3": "INFORMATIONS SUPPLEMENTAIRES",
                "date_creation": acheteur.date_creation.strftime("%d/%m/%Y") if hasattr(acheteur, 'date_creation') and acheteur.date_creation else "Non spécifié",
                "naf_codes": naf_codes if naf_codes else ["Aucun code NAF disponible"],
                "nace_codes": nace_codes if nace_codes else "Aucun code NACE disponible",
                "boite_postale": acheteur.boite_postale if hasattr(acheteur, 'boite_postale') else "Non spécifié",
                "site_internet": acheteur.site_internet if hasattr(acheteur, 'site_internet') else "Non spécifié",
                "description": acheteur.description if hasattr(acheteur, 'description') else "Non spécifié",
                "commentaire": acheteur.commentaire if hasattr(acheteur, 'commentaire') else "Non spécifié",
                "categorie_entreprise": acheteur.categorie_entreprise.libelle if hasattr(acheteur, 'categorie_entreprise') else "Non spécifié",
                "statut_entreprise": acheteur.statut_entreprise.libelle if hasattr(acheteur, 'statut_entreprise') else "Non spécifié",
                "forme_juridique": acheteur.forme_juridique.libelle if hasattr(acheteur, 'forme_juridique') else "Non spécifié",
            },
            "executive_summary": {
                "title_4": "RESUME EXECUTIF",
                "capital_social": resume.capital_social if resume and resume.capital_social else "Non spécifié",
                "devise": resume.devise.code if resume and hasattr(resume, 'devise') and resume.devise else "Non spécifié",
                "chiffre_affaire": resume.chiffre_affaire if resume and resume.chiffre_affaire else "Non spécifié",
                "resultat_net": resume.resultat_net if resume and resume.resultat_net else "Non spécifié",
                "capitaux_propre": resume.capitaux_propre if resume and resume.capitaux_propre else "Non spécifié",
                "nombre_employe": resume.nombre_employe if resume and resume.nombre_employe else "Non spécifié",
                "date_creation": resume.date_creation.strftime("%d/%m/%Y") if resume and resume.date_creation else "Non spécifié",
                "commentaire": resume.commentaire if resume and resume.commentaire else "Aucun commentaire disponible !",
            },
            "summary_and_opinion": {
                "title_5": "EVALUATION DU RISQUE",
                "risk_rating_value": risk_rating.calculate_risk_score() if risk_rating else "Non spécifié",
                "cotation_du_risque": risk_rating.get_cotation_explication() if risk_rating else "Non spécifié",
                "indice_du_risque": risk_rating.get_indice_explication() if risk_rating else "Non spécifié",
                "interpretation": risk_rating.interpretation if risk_rating and risk_rating.interpretation else "Aucune interprétation disponible",
                "analyse_detailee": html.unescape(risk_rating.analyse) if risk_rating and risk_rating.analyse else "Aucune analyse détaillée disponible",
            },
            "acremac_opinion": {
                "title_6": "AVIS CREDIT ACREMAC",
                # Passez le dictionnaire directement au template
                "notes": notes_str, # Passez la chaîne formatée au template
                "highlighted_risks": highlighted_risks,
                "montant_credit_maximum": acremac_opinion.montant_credit_maximum if acremac_opinion else "Non spécifié",
                "commentaire": acremac_opinion.commentaire if acremac_opinion else "Aucun commentaire disponible",
            },
            "registered_data": {
                "title_7": "DONNEES D'ENREGISTREMENT",
                "date_creation": donnees_enregistrement.date_creation.strftime("%d/%m/%Y") if donnees_enregistrement and donnees_enregistrement.date_creation else "Non spécifié",
                "date_registre": donnees_enregistrement.date_registre.strftime("%d/%m/%Y") if donnees_enregistrement and donnees_enregistrement.date_registre else "Non spécifié",
                "forme_juridique": (
                    donnees_enregistrement.forme_juridique_ref.libelle
                    if donnees_enregistrement and donnees_enregistrement.forme_juridique_ref
                    else donnees_enregistrement.forme_juridique if donnees_enregistrement else "Non spécifié"
                ),
                "acheteur": donnees_enregistrement.acheteur.nom if donnees_enregistrement.acheteur.nom else "Non spécifié",
                "numero_registre_commerce": donnees_enregistrement.numero_registre_commerce if donnees_enregistrement and donnees_enregistrement.numero_registre_commerce else "Non spécifié",
                "numero_fiscale": donnees_enregistrement.numero_fiscale if donnees_enregistrement and donnees_enregistrement.numero_fiscale else "Non spécifié",
                "statut_registre": (
                    donnees_enregistrement.statut_registre_ref.libelle
                    if donnees_enregistrement and donnees_enregistrement.statut_registre_ref
                    else donnees_enregistrement.statut_registre if donnees_enregistrement else "Non spécifié"
                ),
                "commentaire": donnees_enregistrement.commentaire if donnees_enregistrement and donnees_enregistrement.commentaire else "Aucun commentaire disponible",
            },
            "legal_background": {
                "title_8": "ANTECEDENTS JURIDIQUES",
                "antecedents_juridiques": list_antecedants_data if list_antecedants_data else ["Aucun antécédent juridique disponible"],
            },
            "management": {
                "title_9": "MANAGEMENT DU RISQUE",
                "risk_management": {
                    "professionalisme": risk_management.professionalisme if risk_management and risk_management.professionalisme else "Non spécifié",
                    "organisation": risk_management.organisation if risk_management and risk_management.organisation else "Non spécifié",
                    "turn_over": risk_management.turn_over if risk_management and risk_management.turn_over else "Non spécifié",
                    "greve": risk_management.greve if risk_management and risk_management.greve else "Non spécifié",
                    "degradation_qualite": risk_management.degradation_qualite if risk_management and risk_management.degradation_qualite else "Non spécifié",
                    "non_respect_condition": risk_management.non_respect_condition if risk_management and risk_management.non_respect_condition else "Non spécifié",
                    "commentaire": risk_management.commentaire if risk_management and risk_management.commentaire else "Aucun commentaire disponible",
                },
                "responsables": list_responsables_data if list_responsables_data else "Aucun responsable disponible",
                "conseil_administration": list_ca_membres_data if list_ca_membres_data else "Aucun membre du conseil d'administration disponible",
            },
            "capital_composition": {
                "title_10": "COMPOSITION DU CAPITAL",
                "emis": format_currency(composition_capital_social.emis) if composition_capital_social else "Non spécifié",
                "publie": format_currency(composition_capital_social.publie) if composition_capital_social else "Non spécifié",
                "libere": format_currency(composition_capital_social.libere) if composition_capital_social else "Non spécifié",
                "devise": composition_capital_social.devise.code if composition_capital_social and composition_capital_social.devise else "Non spécifié",
                "commentaire": composition_capital_social.commentaire if composition_capital_social and composition_capital_social.commentaire else "Aucun commentaire disponible",
            },
            
            
            
            "financial_statements": {
                "years": [data['annee_n'], data['annee_n1'], data['annee_n2']],
                "bilan_type": data['type_bilan'],
            },
            "conclusion_generale": {
                "commentaire": "Rapport généré avec succès. Les données financières seront analysées dans les sections dédiées."
            }
        }
        
        # Retourner les données pour affichage dans le template
        return Response({
            'status': 'success',
            'message': 'Rapport généré avec succès',
            'report_data': report_data,
            'form_data': data
        })
    
    return Response(serializer.errors, status=400)