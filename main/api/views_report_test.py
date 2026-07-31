# Fichier : views_report.py
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _, get_language
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.functions import TruncMonth
from django.db.models import Count
from datetime import datetime

from main.serializers import *
import xml.etree.ElementTree as ET
from django.http import HttpResponse

from io import BytesIO
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import xml.etree.ElementTree as ET
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os
from django.conf import settings
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from django.contrib.staticfiles import finders
import base64
from django.conf import settings
from io import BytesIO
from django.shortcuts import get_object_or_404
import html

# ... (votre code d'importation existant) ..
# Import des classes de services
from main.utils import FinancialReportGenerator
from main.utils import AcremacScoring


# Fonctions d'assistance pour les parties du rapport
def _get_list_data(model, acheteur, fields_map):
    """
    Récupère les données d'un modèle et les formate en liste de dictionnaires.
    Args:
        model (Model): Le modèle Django à interroger.
        acheteur (Acheteur): L'objet Acheteur.
        fields_map (dict): Dictionnaire de mapping des champs du modèle vers les clés du dictionnaire de sortie.
    Returns:
        list: Liste de dictionnaires de données.
    """
    data_list = []
    queryset = model.objects.filter(acheteur=acheteur)
    for obj in queryset:
        item_data = {}
        for key, field_name in fields_map.items():
            if '.' in field_name:
                parts = field_name.split('.')
                val = getattr(getattr(obj, parts[0], None), parts[1], None)
            else:
                val = getattr(obj, field_name, None)
            item_data[key] = val if val not in [None, ''] else "Non spécifié"
        data_list.append(item_data)
    return data_list






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


def render_html_template(report_data):
    # Chemin absolu vers le dossier des templates
    template_dir = os.path.join(settings.BASE_DIR, 'main', 'templates', 'main')
    print("Chemin des templates :", os.path.abspath(template_dir))  # Debug
    if not os.path.exists(template_dir):
        raise FileNotFoundError(f"Le dossier {template_dir} n'existe pas.")

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('report_acremac_template.html')

    # Rendu du template avec des valeurs par défaut
    html = template.render(
        # Pied de page
        footer_text_1=report_data.get('footer_report', {}).get('footer_text_1', 'Texte par défaut 1'),
        footer_text_2=report_data.get('footer_report', {}).get('footer_text_2', 'Texte par défaut 2'),
        footer_text_3=report_data.get('footer_report', {}).get('footer_text_3', 'Texte par défaut 3'),

        # En-tête
        acremac_services=report_data.get('header_report', {}).get('acremac_services', 'Services ACREMAC'),
        acremac_mail=report_data.get('header_report', {}).get('acremac_mail', 'credit.report@acremac.com'),

        # Client
        client=report_data.get('commande', {}).get('client', 'Client inconnu'),

        # Nom de l'acheteur
        client_nom_acheteur=report_data.get('identification', {}).get('acremac_info', {}).get('nom', 'Nom inconnu'),
    )
    return html


def generate_pdf_weasyprint(report_data):
    html = render_html_template(report_data)
    buffer = BytesIO()
    HTML(string=html).write_pdf(buffer)
    buffer.seek(0)
    return buffer


def generate_pdf_weasyprint_2(report_data):
    html = render_to_string('main/report_full_template.html', report_data)

    # CSS pour ajuster la mise en page
    css = CSS(string='''
        @page {
            size: A4;
            margin: 10mm 15mm 10mm 15mm; /* marges : haut, droite, bas, gauche */
        }
        body {
            font-family: Arial, sans-serif;
            width: 100%;
            overflow: hidden;
        }
        img {
            max-width: 100%; /* limite la largeur des images */
        }
        table {
            width: 100%;
            table-layout: fixed; /* force le tableau à respecter la largeur */
            word-wrap: break-word; /* évite les débordements de texte */
        }
    ''')

    buffer = BytesIO()
    HTML(string=html).write_pdf(buffer, stylesheets=[css])
    buffer.seek(0)
    return buffer


def generate_pdf_weasyprint_3(report_data):
    html = render_to_string('main/report_full_template.html', report_data)
    
    # Chercher le chemin du fichier CSS statique
    css_path = finders.find('main/css/report_full_template.css')
    
    if css_path:
        # WeasyPrint accepte les chemins d'accès au fichier
        stylesheets = [CSS(filename=css_path)]
    else:
        stylesheets = []

    buffer = BytesIO()
    HTML(string=html).write_pdf(buffer, stylesheets=stylesheets)
    buffer.seek(0)
    return buffer


def generate_pdf_weasyprint_3_debug(report_data):
    html_content = render_to_string('main/report_full_template.html', report_data)
    
    # Écrire le contenu HTML dans un fichier local pour inspection
    with open('debug_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    css_path = finders.find('main/css/report_full_template.css')
    stylesheets = [CSS(filename=css_path)] if css_path else []

    buffer = BytesIO()
    HTML(string=html_content).write_pdf(buffer, stylesheets=stylesheets)
    buffer.seek(0)
    return buffer


def generate_pdf_xhtml2pdf(report_data):
    try:
        html = render_html_template(report_data)
        # Sauvegardez le HTML pour débogage
        with open('debug_template.html', 'w', encoding='utf-8') as f:
            f.write(html)

        buffer = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode('utf-8')), buffer)
        if pdf.err:
            raise Exception(f"Erreur lors de la génération du PDF : {pdf.err}")
        buffer.seek(0)
        return buffer
    except Exception as e:
        raise Exception(f"Erreur lors de la génération du PDF : {str(e)}")


def generate_html(report_data):
    html = f"""
    <html>
        <head>
            <title>Rapport</title>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Rapport pour {report_data['identification']['acremac_info']['nom']}</h1>
            <table>
                <tr><th>Clé</th><th>Valeur</th></tr>
                <tr><td>Nom</td><td>{report_data['identification']['acremac_info']['nom']}</td></tr>
                <tr><td>Date</td><td>{report_data['header_report']['date_today']}</td></tr>
                <!-- Ajoutez d'autres champs ici -->
            </table>
        </body>
    </html>
    """
    return html


def generate_pdf(report_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Exemple d'utilisation de report_data
    title = f"Rapport pour {report_data['identification']['acremac_info']['nom']}"
    story.append(Paragraph(title, styles['Title']))

    # Ajoutez des tableaux ou paragraphes avec les données de report_data
    data = [
        ["Clé", "Valeur"],
        ["Nom", report_data['identification']['acremac_info']['nom']],
        ["Date", report_data['header_report']['date_today']],
    ]
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer


def dict_to_xml(tag, data):
    elem = ET.Element(tag)
    if isinstance(data, dict):
        for key, val in data.items():
            child = dict_to_xml(str(key), val)
            elem.append(child)
    elif isinstance(data, (list, tuple)):
        for item in data:
            child = dict_to_xml('item', item)
            elem.append(child)
    else:
        elem.text = str(data)
    return elem


def calculate_variation(n, n_minus_1):
    if n is None or n_minus_1 is None or n_minus_1 == Decimal('0'):
        return "N/A"
    n = float(n)
    n_minus_1 = float(n_minus_1)
    if n_minus_1 == 0:
        return "N/A"
    variation = ((n - n_minus_1) / abs(n_minus_1)) * 100
    return f"{variation:.2f}%"


def get_nested_value(data, keys):
    if not isinstance(data, dict):
        return None
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value



# --- Fonction améliorée pour la génération des données du rapport ---
def get_financial_data_for_template(data_by_year, years, fields):
    table_data = []
    
    # Créer une liste de toutes les années et de toutes les valeurs pour chaque champ
    field_values = {}
    for field_info in fields:
        field_values[field_info['key']] = {}
        for year in years:
            value = get_nested_value(data_by_year.get(year, {}), field_info['key'].split('.'))
            
            # --- Correction ici : Assurer que la valeur est un Decimal ---
            if value is not None and value != '':
                try:
                    # Convertir la valeur en Decimal, si c'est un string
                    value = Decimal(str(value))
                except (ValueError, TypeError):
                    value = Decimal('0')
            else:
                value = Decimal('0')
            # --- Fin de la correction ---

            field_values[field_info['key']][year] = value

    # Parcourir la liste de champs pour construire les lignes du tableau
    for field_info in fields:
        row = {
            'label': field_info['label'],
            'is_total': field_info.get('is_total', False),
            'is_subtotal': field_info.get('is_subtotal', False),
            'is_section': field_info.get('is_section', False),
            'is_final_total': field_info.get('is_final_total', False)
        }
        
        for i, year in enumerate(years):
            value = Decimal('0')
            
            if field_info.get('is_subtotal', False):
                subtotal_keys = field_info.get('subtotal_of', [])
                # La correction rend cette somme sûre
                value = sum(field_values.get(k, {}).get(year, Decimal('0')) for k in subtotal_keys)
            
            elif field_info.get('is_total', False) or field_info.get('is_final_total', False):
                total_keys = field_info.get('total_of', [])
                # La correction rend cette somme sûre
                value = sum(field_values.get(k, {}).get(year, Decimal('0')) for k in total_keys)
            
            else:
                value = field_values.get(field_info['key'], {}).get(year, Decimal('0'))

            row[f'value_{year}'] = value
            
            if i > 0:
                prev_year = years[i - 1]
                prev_value = row.get(f'value_{prev_year}', Decimal('0'))
                variation = calculate_variation(value, prev_value)
                row[f'var_{year}'] = variation
            else:
                row[f'var_{year}'] = 'N/A'
                
        table_data.append(row)
    return table_data

# === Vues Report === #






class GenerateReport(APIView):
    def get(self, request, acheteur_id, *args, **kwargs):
        
        # Get data
        # Récupération des paramètres
        id_commande_str = request.query_params.get('id_commande')
        language_report = request.query_params.get('language', 'fr')
        format_report = request.query_params.get('format_report', 'PDF')
        bilan_report = request.query_params.get('bilan_report', 'Classique')
        
        print(id_commande_str)
        print(language_report)
        print(format_report)
        print(bilan_report)
        
        # 2. Définir les années et récupérer la devise
        current_year = datetime.datetime.now().year
        years_to_retrieve = [current_year - 1, current_year - 2, current_year - 3]
        years_to_retrieve = sorted(years_to_retrieve)
        print("years_to_retrieve (sorted):", years_to_retrieve)
        
        
        
        # 3. Définir les textes en fonction de la langue
        if language_report.lower() == "en":
            # English translations
            translations = {
                "title_financial_statements": "FINANCIAL STATEMENTS",
                "title_balance_sheet": "Balance Sheet",
                "title_income_statement": "Income Statement",
                "title_ratios": "Ratios",
                "total_current_assets": "Total Current Assets",
                "total_assets": "Total Assets",
                "total_current_liabilities": "Total Current Liabilities",
                "total_liabilities_and_equity": "Total Liabilities and Equity",
                "sales": "Sales",
                "operating_expenses": "Operating Expenses",
                "net_profit": "Net Profit",
                "general_liquidity": "General Liquidity",
                "gross_margin": "Gross Margin",
                "assets_turnover": "Assets Turnover",
                "financial_data_not_available": "Financial data not available."
            }
        else:
            # French translations (default)
            translations = {
                "title_financial_statements": "ETATS FINANCIERS",
                "title_balance_sheet": "Bilan",
                "title_income_statement": "Compte de Résultat",
                "title_ratios": "Ratios",
                "total_current_assets": "Total Actifs Courants",
                "total_assets": "Total Actifs",
                "total_current_liabilities": "Total Passifs Courants",
                "total_liabilities_and_equity": "Total Passifs et Capitaux Propres",
                "sales": "Ventes",
                "operating_expenses": "Charges d'Exploitation",
                "net_profit": "Résultat Net",
                "general_liquidity": "Liquidité Générale",
                "gross_margin": "Marge Brute",
                "assets_turnover": "Rotation des Actifs",
                "financial_data_not_available": "Données financières non disponibles."
            }
        
        
        # Recuperation de l'acheteur
        try:
            acheteur = Acheteur.objects.get(pk=acheteur_id)
        except Acheteur.DoesNotExist:
            return {"error": f"Acheteur avec l'ID {acheteur_id} non trouvé."}
        
        
            
        # Get devise   
        try:
            compte_financier = CompteFinancier.objects.get(acheteur=acheteur)
            devise = compte_financier.devise
            # devise_code = devise.code if devise else "N/A"
        except CompteFinancier.DoesNotExist:
            compte_financier = None
            devise = None
            # devise_code = "N/A"
        
        
        # Recuperation de la commande
        # Vérifier si l'ID est une chaîne de chiffres valide
        if id_commande_str and id_commande_str.isdigit():
            # Convertir en entier uniquement si c'est un chiffre
            # Tenter de récupérer la commande
            try:
                commande = get_object_or_404(Commande, pk=id_commande_str)
                print(commande)
            except Commande.DoesNotExist:
                # Gérer le cas où la commande n'est pas trouvée
                commande = None
        else:
            # Gérer le cas où l'ID est manquant ou non valide
            commande = None
            # Vous pouvez également retourner une erreur 400 pour "mauvaise requête"
            # return Response({"error": "ID de commande manquant ou invalide."}, status=status.HTTP_400_BAD_REQUEST)
        
        
        # Recuperation des codes NAF de l'acheteur
        # Recuperation des codes NACE de l'acheteur
        naf_codes = list(CodeNafAcheteur.objects.filter(acheteur=acheteur).values_list('code', flat=True))
        nace_codes = list(CodeNaceAcheteur.objects.filter(acheteur=acheteur).values_list('code', flat=True))

        
        
        # Recuperation du resume en fonction de l'acheteur
        try:
            resume = Resume.objects.get(acheteur=acheteur)
        except Resume.DoesNotExist:
            resume = None
        
        # Recuperation de l'evaluation de risque de l'acheteur 
        # Recuperation de l'evaluation de risque chiffree de l'acheteur  
        risk_rating_value = 1  # Commencer à 0
        try:
            # Utiliser filter().first() pour éviter l'exception MultipleObjectsReturned
            risk_rating = RiskRating.objects.filter(acheteur=acheteur).first()
            
            if risk_rating:
                if risk_rating.remboursabilite:
                    risk_rating_value += 1
                if risk_rating.situation_liquidite:
                    risk_rating_value += 1
                if risk_rating.performance_rentabilite:
                    risk_rating_value += 1
                if risk_rating.perspective_secteur:
                    risk_rating_value += 1
                if risk_rating.qualite_information_analyse:
                    risk_rating_value += 1
                if risk_rating.existence_garantie:
                    risk_rating_value += 1
                if risk_rating.terme_financier_duree_pret:
                    risk_rating_value += 1
                if risk_rating.mesure_propre_soutenir_credit:
                    risk_rating_value += 1
                
                # S'assurer que la valeur est entre 0 et 8
                risk_rating_value = min(risk_rating_value, 9)
            else:
                risk_rating = None
                
        except Exception as e:
            risk_rating = None
            risk_rating_value = 1
            
        
        # Recuperation de l'opinion ACREMAC en fonction de l'acheteur   
        try:
            acremac_opinion = OpinionCreditAcremac.objects.filter(acheteur=acheteur).first()
        except OpinionCreditAcremac.DoesNotExist:
            acremac_opinion = None
        
        # Recuperation des donnees enregistrement en fonction de l'acheteur 
        try:
            donnees_enregistrement = DonneesEnregistrement.objects.get(acheteur=acheteur)
        except DonneesEnregistrement.DoesNotExist:
            donnees_enregistrement = None
        
        # Recuperation des donnees enregistrement en fonction de l'acheteur 
        try:
            antecedants_juridiques = AntecedantsJuridique.objects.filter(acheteur=acheteur)
        except AntecedantsJuridique.DoesNotExist:
            antecedants_juridiques = None
            
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
            
            
        # Recuperation des elements de gestion de risque de l'acheteur 
        try:
            risk_management = RiskManagment.objects.get(acheteur=acheteur)
        except RiskManagment.DoesNotExist:
            risk_management = None
        
        
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
            
            
        # Recuperation de la composition du capital social de l'acheteur
        try:
            composition_capital_social = CompositionCapitalSocial.objects.get(acheteur=acheteur)
        except CompositionCapitalSocial.DoesNotExist:
            composition_capital_social = None
            
            
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
            
            
        # Recuperation de l'analyse sectorielle de l'acheteur
        try:
            analyse_sectorielle = AnalyseSectorielle.objects.get(acheteur=acheteur)
        except AnalyseSectorielle.DoesNotExist:
            analyse_sectorielle = None

        # Recuperation de la tendance de l'acheteur
        try:
            tendance = Tendance.objects.get(acheteur=acheteur)
        except Tendance.DoesNotExist:
            tendance = None

        # Recuperation des conseils sur l'acheteur
        try:
            advice = Advice.objects.filter(acheteur=acheteur).first()
        except Advice.DoesNotExist:
            advice = None

        # Recuperation des donnees geopolitiques sur l'acheteur
        try:
            geopolitics = Geopolitics.objects.get(acheteur=acheteur)
        except Geopolitics.DoesNotExist:
            geopolitics = None
            
            
        # Recuperation des banques associees de l'acheteur
        bankers = Banquier.objects.filter(acheteur=acheteur)
        list_banking_data = []
        for banker in bankers:
            list_banking_data.append({
                "nom_banque": banker.nom_banque if banker.nom_banque else "Non spécifié",
                "numero_compte": banker.numero_compte if banker.numero_compte else "Non spécifié",
                "type_relation": banker.type_relation if banker.type_relation else "Non spécifié",
                "numero": banker.numero if banker.numero else "Non spécifié",
                "rue": banker.rue if banker.rue else "Non spécifié",
                "ville": banker.ville.nom if banker.ville else None,
                "code_postal": banker.code_postal if banker.code_postal else "Non spécifié",
                "commentaire": banker.commentaire if banker.commentaire else "Non spécifié",
            })
            
            
        # Recuperation le compte financier de l'acheteur
        try:
            compte_financier = CompteFinancier.objects.get(acheteur=acheteur)
        except CompteFinancier.DoesNotExist:
            compte_financier = None
            
            
        # Recuperation de l'historique des operations de l'acheteur
        try:
            operation_history = OperationEtHistorique.objects.get(acheteur=acheteur)
        except OperationEtHistorique.DoesNotExist:
            operation_history = None
            
            
        
        
        
        # 1. Récupération des propriétés et actifs de l'acheteur
        # Utilisez .filter() pour récupérer toutes les instances
        properties_and_assets = ProprieteEtActif.objects.filter(acheteur=acheteur)
        list_properties_and_assets_data = []

        # 2. Bouclez sur les objets pour construire une liste de dictionnaires
        for prop_asset in properties_and_assets:
            list_properties_and_assets_data.append({
                "locaux": prop_asset.locaux_ref.libelle if prop_asset.locaux_ref else prop_asset.locaux,
                "branche": prop_asset.branche if prop_asset.branche else "Non spécifié",
            })    
            
        # Recuperation des conditions d'achat et de vente de l'acheteur
        try:
            condition_achat = ConditionAchat.objects.get(acheteur=acheteur)
        except ConditionAchat.DoesNotExist:
            condition_achat = None
            
        try:
            condition_vente = ConditionDeVente.objects.get(acheteur=acheteur)
        except ConditionDeVente.DoesNotExist:
            condition_vente = None
            
        
        # Add new section to retrieve general conclusion
        try:
            conclusion_generale = SommaireEtAvis.objects.get(acheteur=acheteur)
        except SommaireEtAvis.DoesNotExist:
            conclusion_generale = None
            
        # Footer advice
        footer_1 = "Nos informations sont confidentielles et ne peuvent être divulguées sous peine de dommages-intérêts."
        footer_2 = "Acremac s'engage à mettre en œuvre avec diligence les "
        footer_3 = "moyens à sa disposition sans être liée par une obligation de résultat."
            
            
        # Récupération des données financières pour les 3 dernières années
        # Nous supposons que l'année courante est 2024
        # Mise à jour des champs de résumé avec les données de la dernière année disponible 
        
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
        
        
        def format_currency(value):
            """Formate un nombre décimal en chaîne avec des séparateurs de milliers."""
            if value is None:
                return "Non spécifié"
            return f"{value:,.2f}".replace(",", " ").replace(".", ",") # Exemple de formatage français
        
        
        
        # 4. Exécution des algorithmes de calcul
        financial_report_generator = FinancialReportGenerator(acheteur, bilan_report)
        financial_tables = financial_report_generator.get_structured_data()
        

        
        

        # 3. Initialize the report data structure
        # 3. Initialize the report data structure
        report_data = {
            "logo_data": get_logo_data(),
            "logo_path": get_logo_path(),
            "header_report": {
                "acremac_branche_country": acheteur.pays.nom if hasattr(acheteur, 'pays') and acheteur.pays else "Non spécifié",
                "acremac_services": f"Services ACREMAC {acheteur.pays.nom}" if hasattr(acheteur, 'pays') and acheteur.pays else "Services ACREMAC",
                "acremac_mail": "credit.report@acremac.com",
                "language_report": "français" if language_report.lower() == "fr" else "english",
                # "devise_report": devise.code if devise else "Non spécifiée",
                "format_report": format_report,
                "date_today": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            },
            "footer_report": {
                "footer_text_1": footer_1,
                "footer_text_2": footer_2,
                "footer_text_3": footer_3,
            },
            "commande": {
                "title_1": "DETAILS COMMANDE",
                "client": commande.client.username if hasattr(commande, 'client') and commande.client else "Non spécifié",
                "ref_client": commande.reference_client if hasattr(commande, 'reference_client') else "Non spécifié",
                "notre_ref": commande.notre_ref if hasattr(commande, 'notre_ref') else "Non spécifié",
                "date_recept_commande": commande.date_recept_commande.strftime("%d/%m/%Y") if hasattr(commande, 'date_recept_commande') and commande.date_recept_commande else "Non spécifié",
                "date_rapport": commande.date_rapport.strftime("%d/%m/%Y") if hasattr(commande, 'date_rapport') and commande.date_rapport else "Non spécifié",
                "delais": commande.delais if hasattr(commande, 'delais') else "Non spécifié",
                "priorite": commande.priorite if hasattr(commande, 'priorite') else "Non spécifié",
                "type_rapport": commande.type_rapport if hasattr(commande, 'type_rapport') else "Non spécifié",
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
                "site_internet": acheteur.site_internet if hasattr(acheteur, 'site_internet') else "Non spécifié",
                "forme_juridique": acheteur.forme_juridique.libelle if hasattr(acheteur, 'forme_juridique') else "Non spécifié",
                "activite_principale": acheteur.activite_principale if hasattr(acheteur, 'activite_principale') else "Non spécifié",
                "description": acheteur.description if hasattr(acheteur, 'description') else "Non spécifié",
                "statut_entreprise": acheteur.statut_entreprise.libelle if hasattr(acheteur, 'statut_entreprise') else "Non spécifié",
                "date_creation": acheteur.date_creation.strftime("%d/%m/%Y") if hasattr(acheteur, 'date_creation') and acheteur.date_creation else "Non spécifié",
                "naf_codes": naf_codes if naf_codes else ["Aucun code NAF disponible"],
                "nace_codes": nace_codes if nace_codes else "Aucun code NACE disponible",
                "naf_codes": naf_codes if naf_codes else "Aucun code NAF disponible",
                "date_creation": acheteur.date_creation if hasattr(acheteur, 'date_creation') else "Non spécifié",
                "boite_postale": acheteur.boite_postale if hasattr(acheteur, 'boite_postale') else "Non spécifié",
                "description": acheteur.description if hasattr(acheteur, 'description') else "Non spécifié",
                "activite_principale": acheteur.activite_principale if hasattr(acheteur, 'activite_principale') else "Non spécifié",
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
                "commentaire": resume.commentaire if resume and resume.commentaire else "Aucun commentaire disponible",
            },
            "summary_and_opinion": {
                "title_5": "EVALUATION DU RISQUE",
                "risk_rating_value": risk_rating.calculate_risk_score() if risk_rating else "Non spécifié",
                "remboursabilite": "Oui" if risk_rating and risk_rating.remboursabilite else "Non",
                "situation_liquidite": "Oui" if risk_rating and risk_rating.situation_liquidite else "Non",
                "performance_rentabilite": "Oui" if risk_rating and risk_rating.performance_rentabilite else "Non",
                "perspective_secteur": "Oui" if risk_rating and risk_rating.perspective_secteur else "Non",
                "qualite_information_analyse": "Oui" if risk_rating and risk_rating.qualite_information_analyse else "Non",
                "existence_garantie": "Oui" if risk_rating and risk_rating.existence_garantie else "Non",
                "terme_financier_duree_pret": "Oui" if risk_rating and risk_rating.terme_financier_duree_pret else "Non",
                "mesure_propre_soutenir_credit": "Oui" if risk_rating and risk_rating.mesure_propre_soutenir_credit else "Non",
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
            "shareholders": {
                "title_11": "ACTIONNARIAT/PROPRIETAIRES",
                "actionnaires": list_shareholders_data if list_shareholders_data else ["Aucun actionnaire disponible"],
            },
            "affiliations": {
                "title_12": "AFFILIATIONS D'ENTREPRISE",
                "affiliations": list_affiliations_data if list_affiliations_data else ["Aucune affiliation disponible"],
            },
            "sector_analysis": {
                "title_13": "ANALYSE SECTORIELLE",
                "naf_codes": naf_codes if naf_codes else ["Aucun code NAF disponible"],
                "nace_codes": nace_codes if nace_codes else ["Aucun code NACE disponible"],
                "sectorielle": {
                    "commentaire": analyse_sectorielle.commentaire if analyse_sectorielle and analyse_sectorielle.commentaire else "Aucun commentaire disponible",
                    "impact_covid_19": analyse_sectorielle.impact_covid_19 if analyse_sectorielle and analyse_sectorielle.impact_covid_19 else "Non spécifié",
                },
                "tendance": {
                    "avis_commercial": tendance.avis_commercial_ref.libelle if tendance and tendance.avis_commercial_ref else tendance.avis_commercial if tendance else "Non spécifié",
                    "presse_media": tendance.presse_media if tendance and tendance.presse_media else "Non spécifié",
                    "principaux_concurrent": tendance.principaux_concurrent if tendance and tendance.principaux_concurrent else "Non spécifié",
                    "commentaire": tendance.commentaire if tendance and tendance.commentaire else "Aucun commentaire disponible",
                },
                "advice": {
                    "points_forts": advice.points_forts if advice and advice.points_forts else "Non spécifié",
                    "points_faibles": advice.points_faibles if advice and advice.points_faibles else "Non spécifié",
                    "dynamisme_court_terme": advice.dynamisme_court_terme if advice and advice.dynamisme_court_terme else "Non spécifié",
                    "dynamisme_long_terme": advice.dynamisme_long_terme if advice and advice.dynamisme_long_terme else "Non spécifié",
                },
                "geopolitics": {
                    "donnees_politiques": geopolitics.donnees_politiques if geopolitics and geopolitics.donnees_politiques else "Non spécifié",
                    "donnees_economiques": geopolitics.donnees_economiques if geopolitics and geopolitics.donnees_economiques else "Non spécifié",
                },
            },
            "banking_data": {
                "title_14": "DONNEES BANCAIRES",
                "data_banks": list_banking_data if list_banking_data else ["Aucune donnée bancaire disponible"],
            },
            "financial_accounts": {
                "title_15": "COMPTES FINANCIERS",
                "cabinet": compte_financier.cabinet if compte_financier and compte_financier.cabinet else "Non spécifié",
                "requis_pour_deposer": compte_financier.requis_pour_deposer if compte_financier and compte_financier.requis_pour_deposer else "Non spécifié",
                "credibilite_cabinet": compte_financier.credibilite_cabinet if compte_financier and compte_financier.credibilite_cabinet else "Non spécifié",
                "source": compte_financier.source if compte_financier and compte_financier.source else "Non spécifié",
                "presentation": compte_financier.presentation if compte_financier and compte_financier.presentation else "Non spécifié",
                "date_compte": compte_financier.date_compte.strftime("%d/%m/%Y") if compte_financier and compte_financier.date_compte else "Non spécifié",
                "date_fin": compte_financier.date_fin.strftime("%d/%m/%Y") if compte_financier and compte_financier.date_fin else "Non spécifié",
                "date_compte_n_moins_un": compte_financier.date_compte_n_moins_un.strftime("%d/%m/%Y") if compte_financier and compte_financier.date_compte_n_moins_un else "Non spécifié",
                "date_fin_n_moins_un": compte_financier.date_fin_n_moins_un.strftime("%d/%m/%Y") if compte_financier and compte_financier.date_fin_n_moins_un else "Non spécifié",
                "date_compte_n_moins_deux": compte_financier.date_compte_n_moins_deux.strftime("%d/%m/%Y") if compte_financier and compte_financier.date_compte_n_moins_deux else "Non spécifié",
                "date_fin_n_moins_deux": compte_financier.date_fin_n_moins_deux.strftime("%d/%m/%Y") if compte_financier and compte_financier.date_fin_n_moins_deux else "Non spécifié",
                "type_compte": compte_financier.type_compte if compte_financier and compte_financier.type_compte else "Non spécifié",
                "devise": compte_financier.devise if compte_financier and compte_financier.devise else "Non spécifié",
                "type_bilan": compte_financier.type_bilan_ref.libelle if compte_financier and compte_financier.type_bilan_ref else compte_financier.type_bilan if compte_financier else "Non spécifié",
                "commentaire": compte_financier.commentaire if compte_financier and compte_financier.commentaire else "Aucun commentaire disponible",
            },
            "financial_statements": {
                "title_20": "ETATS FINANCIERS",
                "years": years_to_retrieve,
                "bilan_type": bilan_report,
                "tables": financial_tables,
            },
            "translations": {},
            "scoring": {
                "title_16": "SCORING ACREMAC",
                # "score": scoring_result['value'],
                # "interpretation": scoring_result['interpretation'],
                # "score_type": scoring_result['type'],
            },
            "operation_history": {
                "title_17": "HISTORIQUE DES OPERATIONS",
                "commentaire_ratios": operation_history.commentaire_ratios if operation_history and operation_history.commentaire_ratios else "Aucun commentaire disponible",
                "description_complete_activite": operation_history.description_complete_activite if operation_history and operation_history.description_complete_activite else "Aucune description disponible",
                "importation": operation_history.importation if operation_history and operation_history.importation else "Non spécifié",
                "historique": operation_history.historique if operation_history and operation_history.historique else "Aucun historique disponible",
            },
            "properties_and_assets": {
                "title_18": "PROPRIÉTÉ ET ACTIFS",
                "assets_list": list_properties_and_assets_data if list_properties_and_assets_data else None,
            },
            "terms_of_purchase_and_sale": {
                "title_19": "CONDITION D'ACHAT ET DE VENTE",
                "conditions_achat": {
                    "local": (", ".join((c.nom_en or c.nom_fr or c.nom) if (get_language() or 'fr').startswith('en') else (c.nom_fr or c.nom_en or c.nom) for c in condition_achat.local.all()) or _("Non spécifié")) if condition_achat else _("Non spécifié"),
                    "importation": (", ".join((c.nom_en or c.nom_fr or c.nom) if (get_language() or 'fr').startswith('en') else (c.nom_fr or c.nom_en or c.nom) for c in condition_achat.importation.all()) or _("Non spécifié")) if condition_achat else _("Non spécifié"),
                    "les_clients": condition_achat.les_clients if condition_achat and condition_achat.les_clients else _("Non spécifié"),
                    "fournisseur": condition_achat.fournisseur if condition_achat and condition_achat.fournisseur else _("Non spécifié"),
                },
                "conditions_vente": {
                    "local": (", ".join((c.nom_en or c.nom_fr or c.nom) if (get_language() or 'fr').startswith('en') else (c.nom_fr or c.nom_en or c.nom) for c in condition_vente.local.all()) or _("Non spécifié")) if condition_vente else _("Non spécifié"),
                    "recouvrement_dette_jugement": condition_vente.recouvrement_de_dette_jugement_ref.libelle if condition_vente and condition_vente.recouvrement_de_dette_jugement_ref else condition_vente.recouvrement_de_dette_jugement if condition_vente else "Non spécifié",
                    "comportement_de_paiement": condition_vente.comportement_de_paiement_ref.libelle if condition_vente and condition_vente.comportement_de_paiement_ref else condition_vente.comportement_de_paiement if condition_vente else "Non spécifié",
                }
            },
            "conclusion_generale": {
                "title": "CONCLUSION GENERALE",
                "couleur_commentaire": conclusion_generale.couleur_commentaire.couleur if conclusion_generale and conclusion_generale.couleur_commentaire else "Non spécifié",
                "commentaire": conclusion_generale.commentaire if conclusion_generale and conclusion_generale.commentaire else "Aucun commentaire disponible",
            }
        }
        
        print(report_data)

            
        # 3. Retourner le format demandé
        try:
            if format_report.upper() == 'PDF':
                print("Génération du PDF...")  # Debug
                # Rendre le template HTML
                html_string = render_to_string('main/report_acremac_template.html', report_data)
                
                # Conversion en PDF avec WeasyPrint
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="rapport_solvabilite.pdf"'
                
                # Générer le PDF avec le base_url pointant vers le répertoire static
                HTML(
                    string=html_string, 
                    base_url=request.build_absolute_uri('/static/')
                ).write_pdf(response)
                
                return response
            elif format_report.upper() == 'XML':
                print("Génération du XML...")  # Debug
                root = dict_to_xml('report', report_data)
                xml_str = ET.tostring(root, encoding='utf-8')
                print(xml_str.decode('utf-8'))  # Debug
                response = HttpResponse(xml_str, content_type='application/xml')
                response['Content-Disposition'] = f'attachment; filename="rapport_acheteur_{acheteur_id}.xml"'
                return response
            elif format_report.upper() == 'HTML':
                print("Génération du HTML...")  # Debug
                html_content = generate_html(report_data)
                print(html_content)  # Debug
                response = HttpResponse(html_content, content_type='text/html')
                response['Content-Disposition'] = f'attachment; filename="rapport_acheteur_{acheteur_id}.html"'
                return response
            else:
                print("Génération du JSON...")  # Debug
                print(report_data)  # Debug
                return Response(report_data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Erreur : {str(e)}")  # Debug
            return Response(
                {"error": f"Erreur lors de la génération du rapport : {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

