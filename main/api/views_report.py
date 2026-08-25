# Fichier : views_report.py
from django.utils.translation import gettext as _, get_language
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.functions import TruncMonth
from django.db.models import Count
# from datetime import datetime
from datetime import datetime as dt
import html  # Pour l'échappement XML
import re  # regex utilities

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
from main.utils import FinancialReportGenerator, get_simple_actifs_data
from main.utils import AcremacScoring, get_structured_actif_data, get_structured_passif_data
from main.utils import get_structured_resultat_data, get_structured_ratios_data
# ... (votre code existant) ...
import matplotlib.pyplot as plt
import pandas as pd
from decimal import Decimal
import io
import base64
from django.conf import settings
import os

# Import des classes de services
from main.utils import FinancialReportGenerator
from main.utils import AcremacScoring
import matplotlib
matplotlib.use('Agg') # Utiliser un backend sans interface graphique

import matplotlib.pyplot as plt
import pandas as pd
from decimal import Decimal
import io
import base64
import json
from main.models import ActifC, PassifC, ResultatC
# from datetime import datetime
from django.conf import settings
# import datetime
from main.models import (
    ActifC, PassifC, ResultatC,  # Classique
    ActifA, PassifA, ResultatA,  # Anglais
    Assets, Liabilities,          # Bancaire
    ActifS, PassifS, ResultatS,  # SYSCOHADA
    ActifIFRS, PassifIFRS, ResultatIFRS,  # IFRS COBAC
    Scoring
)
from main.models import TelephoneAcheteur, PortableAcheteur, EmailAcheteur, AdresseAcheteur
from main.models import ScoringRating, ScoringDelphi
# from datetime import datetime as dt 
from main.api.views_scoring_classique import *
from main.api.views_scoring_anglais import *
from main.api.views_scoring_bancaire import *
from main.api.views_scoring_syscohada import *
from main.api.views_scoring_ifrs import *

from main.utils import *
import logging

logger = logging.getLogger(__name__)

# Une fonction pour s'assurer que les données sont numériques.
def to_float(value):
    """Convertit une valeur en float, gère les None et les Decimals."""
    try:
        if value is None or value == '':
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _format_value_as_percent(value):
    if value is None:
        return value
    if isinstance(value, str):
        raw = value.strip()
        if not raw or raw in {"-", "--", "N/A", "Non spécifié", "None"}:
            return value
        if "%" in raw:
            return value
        raw_norm = raw.replace(" ", "").replace(",", ".")
        try:
            number = float(raw_norm)
            return f"{number:.2f}%"
        except (TypeError, ValueError):
            return value
    if isinstance(value, (int, float, Decimal)):
        return f"{float(value):.2f}%"
    return value


def _format_ratios_node_as_percent(node):
    if isinstance(node, dict):
        return {k: _format_ratios_node_as_percent(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_format_ratios_node_as_percent(item) for item in node]
    return _format_value_as_percent(node)


def _force_ratios_percent_display(report_data):
    if not isinstance(report_data, dict):
        return report_data

    financial_statements = report_data.get("financial_statements")
    if not isinstance(financial_statements, dict):
        return report_data

    for section_key in (
        "etats_financiers_classiques",
        "etats_financiers_anglais",
        "etats_financiers_bancaires",
        "etats_financiers_syscohada",
        "etats_financiers_irfs_cobac",
    ):
        section = financial_statements.get(section_key)
        if not isinstance(section, dict):
            continue
        if "ratios_data" in section:
            section["ratios_data"] = _format_ratios_node_as_percent(section.get("ratios_data"))

    return report_data


def build_scoring_manuel_context(acheteur, years_to_retrieve):
    """Construit l'historique de scoring manuel pour N, N-1, N-2."""
    labels = ["N", "N-1", "N-2"]
    normalized_years = []
    for year in (years_to_retrieve or [])[:3]:
        try:
            normalized_years.append(int(year))
        except (TypeError, ValueError):
            normalized_years.append(year)

    scorings = (
        Scoring.objects
        .filter(acheteur=acheteur, annee__annee__in=normalized_years)
        .select_related("annee")
        .order_by("-updated_at", "-created_at")
    )

    scoring_by_year = {}
    for scoring in scorings:
        year_value = getattr(scoring.annee, "annee", None)
        if year_value is not None and year_value not in scoring_by_year:
            scoring_by_year[year_value] = scoring

    annees = []
    for idx, year in enumerate(normalized_years):
        scoring = scoring_by_year.get(year)
        raw_score = str(scoring.score).strip() if scoring and scoring.score else None
        score_numeric = None
        if raw_score:
            try:
                score_numeric = float(raw_score)
            except (TypeError, ValueError):
                score_numeric = None

        if score_numeric is not None:
            score_arrondi = max(0, min(10, round(score_numeric)))
            score_affiche = f"{score_numeric:.2f}"
        else:
            score_arrondi = 0
            score_affiche = raw_score or "N/A"

        annees.append({
            "label": labels[idx] if idx < len(labels) else f"N-{idx}",
            "annee": year,
            "score": score_affiche,
            "score_raw": raw_score,
            "score_numeric": score_numeric,
            "score_arrondi": score_arrondi,
            "score_image": f"scoring/{score_arrondi}.png",
            "interpretation": scoring.get_score_category() if scoring else "Non évalué",
            "commentaire": scoring.commentaire if scoring and scoring.commentaire else "",
            "is_available": bool(scoring),
        })

    return {
        "title": "SCORING MANUEL",
        "annees": annees,
        "has_data": any(item["is_available"] for item in annees),
    }


# Fichier : views_report.py

# Fichier : views_report.py

def get_base64_chart2(data, title, y_label, chart_type='bar', is_percentage=False):
    """
    Crée un graphique à barres ou en ligne, le sauvegarde dans un buffer et renvoie sa représentation Base64.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    labels = data['labels']
    datasets = data['datasets']

    # For consistent X-axis ordering we sort by numeric value of the labels
    # and re‑order the corresponding dataset values. This prevents charts
    # from showing years like [2025,2024,2023].
    def _numeric_key(label):
        # attempt to coerce into int, otherwise raise
        return int(label)

    def _nlabel_key(label):
        # support patterns N, N-1, N-2, N+1 etc.
        m = re.match(r'^N([+-]?\d+)?$', label)
        if m:
            offset = int(m.group(1)) if m.group(1) else 0
            # we want N-2 < N-1 < N < N+1 so use offset
            return offset
        # finally fall back to label index (preserve original order)
        try:
            return labels.index(label)
        except ValueError:
            return 0

    try:
        order = sorted(range(len(labels)), key=lambda i: _numeric_key(labels[i]))
    except Exception:
        try:
            order = sorted(range(len(labels)), key=lambda i: _nlabel_key(labels[i]))
        except Exception:
            order = list(range(len(labels)))

    if order != list(range(len(labels))):
        labels = [labels[i] for i in order]
        datasets = [
            {**ds, 'data': [ds['data'][i] for i in order]}
            for ds in datasets
        ]

    # Nouvelle méthode pour créer le DataFrame
    if chart_type == 'bar' or chart_type == 'hist':
        # On extrait les données et les labels pour les années
        years = [d['label'] for d in datasets]
        datas = [d['data'] for d in datasets]

        # Création du DataFrame avec les labels comme index des colonnes et les années comme index des lignes
        df = pd.DataFrame(datas, columns=labels, index=years)

        # Affichage du graphique directement depuis le DataFrame
        # 'hist' est traité de la même façon que 'bar' : diagramme en bâtons
        df.plot(kind='bar', ax=ax, width=0.8, rot=0)
    
    elif chart_type == 'line':
        for dataset in datasets:
            ax.plot(labels, dataset['data'], label=dataset['label'], marker='o')
        ax.set_xticks(labels)

    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.legend(title="Année")

    if is_percentage:
        from matplotlib.ticker import PercentFormatter
        ax.yaxis.set_major_formatter(PercentFormatter())

    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close(fig)

    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def get_charts_data(actifs_by_year, passifs_by_year, ratios_by_year_dict, years_to_retrieve):
    charts_data = {}
    
    # Données pour le graphique de Structure Financière (barres)
    labels_sf = [str(year) for year in years_to_retrieve]
    datasets_sf = [
        {
            'label': 'Actif Immobilisé', 
            'data': [float(actifs_by_year.get(y, {}).get('total_I', Decimal('0'))) for y in years_to_retrieve]
        },
        {
            'label': 'Actif Circulant', 
            'data': [float(actifs_by_year.get(y, {}).get('total_II', Decimal('0'))) for y in years_to_retrieve]
        },
    ]
    charts_data['structure_financiere'] = get_base64_chart2(
        {'labels': labels_sf, 'datasets': datasets_sf},
        "Structure Financière",
        "Valeur en FCFA",
        chart_type='bar'
    )

    # Données pour le graphique de Rentabilité Financière (ligne)
    labels_rf = [str(year) for year in years_to_retrieve]
    datasets_rf = [
        {
            'label': 'Rendement des Capitaux Propres', 
            'data': [float(ratios_by_year_dict.get(y, {}).get('rendement_capitaux_propres', Decimal('0'))) for y in years_to_retrieve]
        }
    ]
    charts_data['rentabilite_financiere'] = get_base64_chart2(
        {'labels': labels_rf, 'datasets': datasets_rf},
        "Rendement des Capitaux Propres",
        "Valeur en %",
        chart_type='line',
        is_percentage=True
    )
    return charts_data


def get_base64_chart(data, title, y_label):
    """
    Crée un graphique à barres, le sauvegarde dans un buffer et renvoie sa représentation Base64.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    labels = data['labels']
    years = data['years']
    values = data['values']

    x = range(len(labels))
    width = 0.35

    for i, year in enumerate(years):
        rects = ax.bar([pos + i * width for pos in x], values[i], width, label=str(year))
        ax.bar_label(rects, padding=3)

    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.set_xticks([pos + width / (2 if len(years) > 1 else 1) for pos in x])
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend(title="Année")

    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close(fig)

    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def create_and_encode_charts(ratios_data, years):
    """
    Extrait les données de ratio, génère les graphiques et les encode en Base64.
    """
    charts = {}

    # Données pour le graphique de Structure Financière (Année N vs N-1)
    structure_ratios_data = {
        'labels': [row['label'] for row in ratios_data['STRUCTURE FINANCIÈRE']],
        'years': [years[0], years[1]],
        'values': [
            [row['values']['n'] for row in ratios_data['STRUCTURE FINANCIÈRE']],
            [row['values']['n_moins_1'] for row in ratios_data['STRUCTURE FINANCIÈRE']],
        ]
    }
    charts['structure_financiere'] = get_base64_chart(
        structure_ratios_data,
        "Graphique de structure financière (Année N vs Année N-1)",
        "Valeur du ratio"
    )

    # Données pour le graphique de Rentabilité Financière (Année N-1 vs N-2)
    rentabilite_ratios_data = {
        'labels': [row['label'] for row in ratios_data['RENTABILITÉ']],
        'years': [years[1], years[2]],
        'values': [
            [row['values']['n_moins_1'] for row in ratios_data['RENTABILITÉ']],
            [row['values']['n_moins_2'] for row in ratios_data['RENTABILITÉ']],
        ]
    }
    charts['rentabilite_financiere'] = get_base64_chart(
        rentabilite_ratios_data,
        "Graphique de rentabilité financière (Année N-1 vs Année N-2)",
        "Valeur du ratio"
    )

    return charts


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


def get_risk_rating_png_base64(score):
    """Retourne l'image de risque en PNG base64 (priorité aux fichiers 00.png..88.png)."""
    try:
        score_int = int(score)
    except (TypeError, ValueError):
        score_int = 0
    score_int = max(0, min(8, score_int))

    candidate_files = [
        f"riskrating/{score_int}{score_int}.png",
        f"riskrating/{score_int}.png",
    ]

    for image_path in candidate_files:
        absolute_path = finders.find(image_path)
        if not absolute_path:
            static_root = getattr(settings, "STATIC_ROOT", None)
            if static_root:
                probe = os.path.join(static_root, image_path)
                if os.path.exists(probe):
                    absolute_path = probe

        if absolute_path and os.path.exists(absolute_path):
            try:
                with open(absolute_path, "rb") as png_file:
                    encoded = base64.b64encode(png_file.read()).decode("utf-8")
                    return f"data:image/png;base64,{encoded}"
            except Exception as e:
                print(f"Erreur lecture image risque PNG ({absolute_path}): {e}")
                continue

    return None


def render_html_template(report_data):
    """Retourne le HTML rendu par le moteur de templates Django.
    L'ancienne version utilisait Jinja2 avec un contexte restreint, ce qui empêchait
    certaines données (comme le scoring) d'apparaître dans l'aperçu HTML. En
    privilégiant le moteur Django on bénéficie également de l'auto-escaping
    et de la compatibilité avec les tags/filtres utilisés dans
    `report_acremac_template.html`.
    """
    # utilisation de render_to_string garantit que tout `report_data` est
    # rendu et que les filtres `{% load %}` fonctionnent.
    return render_to_string('main/report_acremac_template.html', report_data)


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
    """Génère un rapport HTML complet et le force en téléchargement"""
    try:
        # Utiliser render_to_string pour générer le HTML à partir du template
        html_content = render_to_string('main/report_acremac_template.html', report_data)
        
        # Créer une réponse HTTP avec le contenu HTML
        response = HttpResponse(html_content, content_type='text/html')
        
        # Forcer le téléchargement avec Content-Disposition
        response['Content-Disposition'] = f'attachment; filename="rapport_solvabilite_{report_data.get("identification", {}).get("acremac_info", {}).get("nom", "acheteur")}.html"'
        
        return response
        
    except Exception as e:
        # En cas d'erreur, retourner un HTML simple
        html_content = f"""
        <html>
            <head>
                <title>Rapport d'erreur</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    .error {{ color: red; border: 1px solid #ddd; padding: 15px; background-color: #f8d7da; }}
                </style>
            </head>
            <body>
                <h1>Erreur lors de la génération du rapport</h1>
                <div class="error">
                    <h3>Détails de l'erreur :</h3>
                    <p>{str(e)}</p>
                </div>
            </body>
        </html>
        """
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = 'attachment; filename="rapport_erreur.html"'
        return response


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


def dict_to_xml(tag, data, parent=None):
    if parent is None:
        root = ET.Element(tag)
    else:
        root = ET.SubElement(parent, tag)

    if isinstance(data, dict):
        for key, value in data.items():
            clean_key = ''.join(c if c.isalnum() or c in '_-' else '_' for c in str(key))
            if not clean_key:
                continue

            if isinstance(value, dict):
                dict_to_xml(clean_key, value, root)
            elif isinstance(value, list):
                list_elem = ET.SubElement(root, clean_key)
                for item in value:
                    if item is not None and str(item).strip() != "":
                        if isinstance(item, dict):
                            dict_to_xml('item', item, list_elem)
                        else:
                            item_elem = ET.SubElement(list_elem, 'item')
                            item_elem.text = html.escape(str(item))
            else:
                if value is not None and str(value).strip() != "":
                    elem = ET.SubElement(root, clean_key)
                    elem.text = html.escape(str(value))
    elif isinstance(data, list):
        for item in data:
            if item is not None and str(item).strip() != "":
                dict_to_xml('item', item, root)
    else:
        if data is not None and str(data).strip() != "":
            root.text = html.escape(str(data))

    return root



def generate_xml_v1(report_data):
    try:
        from datetime import datetime as dt
        import xml.etree.ElementTree as ET
        import html
        import re

        # Créer l'élément racine
        root = ET.Element('rapport_solvabilite')
        
        # Ajouter un timestamp
        timestamp_elem = ET.SubElement(root, 'timestamp')
        timestamp_elem.text = dt.now().isoformat()
        
        # Ajouter la version
        version_elem = ET.SubElement(root, 'version')
        version_elem.text = '1.0'

        # Fonction pour nettoyer les noms de balises XML
        def clean_tag_name(tag):
            # Remplacer les caractères non valides dans les noms de balises
            tag = re.sub(r'[^a-zA-Z0-9_\-]', '_', str(tag))
            # S'assurer que le nom commence par une lettre
            if tag and tag[0].isdigit():
                tag = 'tag_' + tag
            # Si vide, retourner une valeur par défaut
            if not tag:
                tag = 'item'
            return tag

        # Fonction pour nettoyer les valeurs XML
        def clean_xml_value(value):
            if value is None:
                return ''
            # Convertir en chaîne
            str_value = str(value)
            # Échapper les caractères XML spéciaux
            str_value = html.escape(str_value)
            # Nettoyer les caractères de contrôle non valides
            str_value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str_value)
            return str_value

        # Fonction récursive pour convertir dict/list en XML
        def dict_to_xml_element(parent, data, parent_tag=None):
            if isinstance(data, dict):
                for key, value in data.items():
                    clean_key = clean_tag_name(key)
                    if isinstance(value, (dict, list)) and value:
                        sub_elem = ET.SubElement(parent, clean_key)
                        dict_to_xml_element(sub_elem, value, clean_key)
                    else:
                        cleaned_value = clean_xml_value(value)
                        if cleaned_value and cleaned_value != "Non spécifié":
                            elem = ET.SubElement(parent, clean_key)
                            elem.text = cleaned_value
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    clean_key = f"{parent_tag}_item_{i}" if parent_tag else f"item_{i}"
                    list_elem = ET.SubElement(parent, clean_key)
                    if isinstance(item, (dict, list)):
                        dict_to_xml_element(list_elem, item, clean_key)
                    else:
                        cleaned_value = clean_xml_value(item)
                        if cleaned_value and cleaned_value != "Non spécifié":
                            list_elem.text = cleaned_value
            else:
                cleaned_value = clean_xml_value(data)
                if cleaned_value and cleaned_value != "Non spécifié":
                    parent.text = cleaned_value

        # Ajouter les sections principales du rapport (une à la fois pour déboguer)
        sections_to_include = [
            'header_report', 'footer_report', 'commande', 'identification',
            'executive_summary', 'summary_and_opinion', 'acremac_opinion',
            'registered_data', 'legal_background', 'management'
        ]
        
        for section_key in sections_to_include:
            if section_key in report_data and report_data[section_key]:
                try:
                    section_elem = ET.SubElement(root, clean_tag_name(section_key))
                    dict_to_xml_element(section_elem, report_data[section_key], section_key)
                    print(f"Section {section_key} ajoutée au XML")
                except Exception as section_error:
                    print(f"Erreur avec section {section_key}: {section_error}")
                    # Ajouter une balise d'erreur pour cette section
                    error_elem = ET.SubElement(root, f"{clean_tag_name(section_key)}_error")
                    error_elem.text = f"Erreur lors de la génération: {str(section_error)[:100]}"

        # Convertir en chaîne XML avec indentation
        xml_str = ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
        
        # Nettoyer les caractères non valides supplémentaires
        # xml_str = re.sub(r'&#x[0-9A-Fa-f]+;', '', xml_str)  # Supprimer les références d'entités hex
        xml_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', xml_str)  # Supprimer les caractères de contrôle
        
        # Ajouter la déclaration XML
        xml_with_declaration = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'
        
        # Vérifier que le XML est bien formé
        try:
            ET.fromstring(xml_with_declaration)
            print(f"XML validé avec succès. Taille: {len(xml_with_declaration)} caractères")
        except ET.ParseError as e:
            # Pour déboguer, afficher les 200 caractères autour de l'erreur
            error_position = int(str(e).split('column ')[1].split(')')[0])
            start_pos = max(0, error_position - 100)
            end_pos = min(len(xml_with_declaration), error_position + 100)
            print(f"Erreur de parsing à la position {error_position}:")
            print(f"Contexte: {xml_with_declaration[start_pos:end_pos]}")
            raise ValueError(f"XML mal formé: {e}")

        # Retourner la réponse HTTP
        response = HttpResponse(
            xml_with_declaration.encode('utf-8'),   # ✔️ bytes OK
            content_type='application/xml'
        )
        response['Content-Length'] = len(xml_with_declaration.encode('utf-8'))
        response['Content-Disposition'] = f'attachment; filename="rapport_solvabilite_{report_data.get("identification", {}).get("acremac_info", {}).get("nom", "acheteur")}.xml"'
        
        return response

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERREUR dans generate_xml: {str(e)}")
        print(f"Traceback: {error_details}")
        
        # XML d'erreur simple et sûr
        error_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<erreur>
    <message>Erreur lors de la génération du rapport XML</message>
    <details>Une erreur technique s'est produite lors de la génération du rapport.</details>
    <timestamp>{}</timestamp>
</erreur>'''.format(dt.now().isoformat())
        
        response = HttpResponse(
            error_xml, 
            content_type='application/xml; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="rapport_erreur.xml"'
        response.status_code = 500
        return response


def generate_xml_with_xsd(report_data):
    from datetime import datetime
    import xml.etree.ElementTree as ET
    import html, re, io, zipfile
    from django.http import HttpResponse

    # ---------------- UTILITAIRES ----------------

    def clean_tag(tag):
        tag = re.sub(r'[^a-zA-Z0-9_\-]', '_', tag)
        return f"tag_{tag}" if tag[0].isdigit() else tag

    def clean_value(val):
        if val is None:
            return ""
        return re.sub(r'[\x00-\x1F\x7F]', '', html.escape(str(val)))

    def build_xml(elem, data):
        if isinstance(data, dict):
            for k, v in data.items():
                tag = clean_tag(k)
                child = ET.SubElement(elem, tag)
                build_xml(child, v)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                item_tag = f"item_{i}"
                child = ET.SubElement(elem, item_tag)
                build_xml(child, item)
        else:
            elem.text = clean_value(data)

    # ---------------- CONSTRUCTION DU XML ----------------

    root = ET.Element("rapport_solvabilite", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "rapport_solvabilite.xsd"
    })

    ET.SubElement(root, "timestamp").text = datetime.now().isoformat()
    ET.SubElement(root, "version").text = "1.0"

    for key, value in report_data.items():
        tag = clean_tag(key)
        section = ET.SubElement(root, tag)
        build_xml(section, value)

    xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
    xml_final = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

    # ---------------- GÉNÉRATION XSD ----------------
    # XSD minimaliste mais valide (compatible avec tout XML dynamique)

    xsd = f'''<?xml version="1.0" encoding="UTF-8"?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">

        <xs:element name="rapport_solvabilite">
            <xs:complexType>
                <xs:sequence>
                    <xs:any minOccurs="0" maxOccurs="unbounded" processContents="lax"/>
                </xs:sequence>
                <xs:attribute name="xmlns:xsi" use="optional"/>
                <xs:attribute name="xsi:noNamespaceSchemaLocation" use="optional"/>
            </xs:complexType>
        </xs:element>

    </xs:schema>
    '''

    # ---------------- ZIP XML + XSD ----------------

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("rapport_solvabilite.xml", xml_final)
        z.writestr("rapport_solvabilite.xsd", xsd)

    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type="application/zip")
    filename = f"rapport_solvabilite_{datetime.now().strftime('%Y%m%d%H%M')}.zip"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response




def generate_xml(report_data):
    try:
        from datetime import datetime as dt
        import xml.etree.ElementTree as ET
        import html
        import re
        
        # Créer l'élément racine
        root = ET.Element('rapport_solvabilite')
        
        # Ajouter les métadonnées de base
        ET.SubElement(root, 'date_generation').text = dt.now().isoformat()
        ET.SubElement(root, 'format').text = 'XML'
        ET.SubElement(root, 'version').text = '1.0'
        
        # Fonction pour nettoyer le texte XML
        def clean_text(text):
            if text is None:
                return ''
            # Convertir en chaîne
            str_text = str(text)
            # Échapper les caractères XML
            str_text = html.escape(str_text)
            # Supprimer les caractères de contrôle
            str_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str_text)
            return str_text
        
        # Fonction pour ajouter des données simples (pas de structures imbriquées complexes)
        def add_simple_section(parent, section_name, data):
            if not data or not isinstance(data, dict):
                return
            
            section_elem = ET.SubElement(parent, section_name)
            for key, value in data.items():
                if value is None:
                    continue
                    
                if isinstance(value, dict):
                    # Pour les sous-dictionnaires simples
                    sub_elem = ET.SubElement(section_elem, key)
                    for sub_key, sub_value in value.items():
                        if sub_value is not None:
                            cleaned = clean_text(sub_value)
                            if cleaned and cleaned != "Non spécifié":
                                ET.SubElement(sub_elem, sub_key).text = cleaned
                elif isinstance(value, list):
                    # Pour les listes simples
                    list_elem = ET.SubElement(section_elem, key)
                    for i, item in enumerate(value):
                        if item is not None:
                            cleaned = clean_text(item)
                            if cleaned and cleaned != "Non spécifié":
                                ET.SubElement(list_elem, f'item_{i}').text = cleaned
                else:
                    # Pour les valeurs simples
                    cleaned = clean_text(value)
                    if cleaned and cleaned != "Non spécifié":
                        ET.SubElement(section_elem, key).text = cleaned
        
        # Ajouter les sections principales (limitées pour éviter les problèmes)
        if 'header_report' in report_data:
            add_simple_section(root, 'entete', report_data['header_report'])
        
        if 'identification' in report_data:
            ident_elem = ET.SubElement(root, 'identification')
            if 'client_info' in report_data['identification']:
                add_simple_section(ident_elem, 'client', report_data['identification']['client_info'])
            if 'acremac_info' in report_data['identification']:
                add_simple_section(ident_elem, 'acremac', report_data['identification']['acremac_info'])
        
        if 'commande' in report_data:
            add_simple_section(root, 'commande', report_data['commande'])
        
        if 'executive_summary' in report_data:
            add_simple_section(root, 'resume_executif', report_data['executive_summary'])
        
        # Convertir en chaîne XML
        xml_str = ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
        
        # Assurer que le XML est valide
        xml_with_declaration = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'
        
        # Valider le XML
        try:
            ET.fromstring(xml_with_declaration)
        except ET.ParseError as e:
            # Créer un XML minimal en cas d'erreur
            simple_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rapport_solvabilite>
    <erreur>Erreur lors de la génération du rapport complet</erreur>
    <date>{dt.now().isoformat()}</date>
    <acheteur>{report_data.get("identification", {}).get("acremac_info", {}).get("nom", "Inconnu")}</acheteur>
    <message>Rapport XML généré avec des données limitées</message>
</rapport_solvabilite>'''
            xml_with_declaration = simple_xml
        
        # Retourner la réponse HTTP
        response = HttpResponse(
            xml_with_declaration, 
            content_type='application/xml; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename="rapport_solvabilite.xml"'
        
        print(f"XML généré avec succès. Taille: {len(xml_with_declaration)} caractères")
        
        return response
        
    except Exception as e:
        import traceback
        print(f"ERREUR grave dans generate_xml: {str(e)}")
        
        # XML d'erreur minimal
        error_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<erreur>
    <message>Erreur lors de la génération du rapport XML</message>
    <timestamp>{}</timestamp>
</erreur>'''.format(dt.now().isoformat())
        
        response = HttpResponse(
            error_xml, 
            content_type='application/xml; charset=utf-8',
            status=500
        )
        response['Content-Disposition'] = 'attachment; filename="rapport_erreur.xml"'
        return response


def generate_xml_v2(report_data):
    from datetime import datetime
    import xml.etree.ElementTree as ET
    import html, re
    from django.http import HttpResponse

    try:
        # ----------- FONCTIONS UTILES -----------
        def clean_tag_name(tag: str) -> str:
            """Nettoie correctement les noms de balise XML"""
            tag = re.sub(r'[^a-zA-Z0-9_\-]', '_', str(tag))
            if tag and tag[0].isdigit():
                tag = "tag_" + tag
            return tag or "item"

        def clean_value(value) -> str:
            if value is None:
                return ""
            s = html.escape(str(value))
            return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', s)

        def build_xml(parent, data, parent_tag=None):
            """Conversion récursive dict/list → XML"""
            if isinstance(data, dict):
                for key, val in data.items():
                    t = clean_tag_name(key)
                    elem = ET.SubElement(parent, t)
                    if isinstance(val, (dict, list)):
                        build_xml(elem, val, t)
                    else:
                        v = clean_value(val)
                        if v and v != "Non spécifié":
                            elem.text = v

            elif isinstance(data, list):
                for i, item in enumerate(data):
                    item_tag = f"{parent_tag}_item" if parent_tag else "item"
                    elem = ET.SubElement(parent, f"{item_tag}_{i}")
                    if isinstance(item, (dict, list)):
                        build_xml(elem, item, item_tag)
                    else:
                        v = clean_value(item)
                        if v and v != "Non spécifié":
                            elem.text = v

        # ----------- CONSTRUCTION DU XML -----------

        root = ET.Element("rapport_solvabilite")

        ET.SubElement(root, "timestamp").text = datetime.now().isoformat()
        ET.SubElement(root, "version").text = "1.0"

        SECTIONS = [
            "header_report", "footer_report", "commande", "identification",
            "executive_summary", "summary_and_opinion", "acremac_opinion",
            "registered_data", "legal_background", "management"
        ]

        for section in SECTIONS:
            section_data = report_data.get(section)
            if section_data:
                section_elem = ET.SubElement(root, clean_tag_name(section))
                build_xml(section_elem, section_data, section)

        # ----------- FINALISATION XML -----------

        xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")

        xml_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', xml_str)

        xml_out = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

        # Vérification du XML
        ET.fromstring(xml_out)

        # ----------- REPONSE HTTP -----------

        company_name = (
            report_data.get("identification", {})
                       .get("acremac_info", {})
                       .get("nom", "acheteur")
        )

        response = HttpResponse(
            xml_out,
            content_type="application/xml; charset=utf-8"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="rapport_solvabilite_{company_name}.xml"'
        )

        return response

    except Exception:
        # Générer un XML propre même en cas d’erreur
        err_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<erreur>
  <message>Erreur lors de la génération du rapport XML</message>
  <timestamp>{datetime.now().isoformat()}</timestamp>
</erreur>
"""
        response = HttpResponse(err_xml, content_type="application/xml; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="rapport_erreur.xml"'
        response.status_code = 500
        return response




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



def get_charts_data(actifs_by_year, passifs_by_year, ratios_by_year_dict, years_to_retrieve):
    charts_data = {}
    
    # Données pour le graphique de Structure Financière
    labels = ['Actif Immobilisé', 'Actif Circulant']
    data_points = []
    
    for year in years_to_retrieve[:2]: # N et N-1
        actifs_immo = float(actifs_by_year.get(year, {}).get('total_I', Decimal('0')))
        actifs_circ = float(actifs_by_year.get(year, {}).get('total_II', Decimal('0')))
        data_points.append([actifs_immo, actifs_circ])
        
    charts_data['structure_financiere'] = get_base64_chart(
        labels,
        data_points,
        "Structure Financière (Année N vs N-1)",
        "Valeur en FCFA"
    )

    # Données pour le graphique de Rentabilité Financière
    labels = ['Rendement des Capitaux Propres']
    data_points_rentab = []
    for year in years_to_retrieve[:2]: # N et N-1
        roc = float(ratios_by_year_dict.get(year, {}).get('rendement_capitaux_propres', Decimal('0')) or Decimal('0'))
        data_points_rentab.append(roc)
    
    charts_data['rentabilite_financiere'] = get_base64_chart(
        labels,
        [[data_points_rentab[0]], [data_points_rentab[1]]],
        "Rendement des Capitaux Propres (Année N vs N-1)",
        "Valeur en %"
    )

    return charts_data




def get_charts_data_test(actifs_by_year, passifs_by_year, ratios_by_year_dict, years_to_retrieve):
    charts_data = {}

    # Données pour le graphique de Structure Financière (N vs N-1)
    labels_sf = ['Actif Immobilisé', 'Actif Circulant', 'Capitaux Propres', 'Dettes']
    data_sf = {
        'N': [
            float(actifs_by_year.get(years_to_retrieve[0], {}).get('total_I', Decimal('0'))),
            float(actifs_by_year.get(years_to_retrieve[0], {}).get('total_II', Decimal('0'))),
            float(passifs_by_year.get(years_to_retrieve[0], {}).get('total_I', Decimal('0'))),
            float(passifs_by_year.get(years_to_retrieve[0], {}).get('total_II', Decimal('0')) +
                  passifs_by_year.get(years_to_retrieve[0], {}).get('total_III', Decimal('0'))),
        ],
        'N-1': [
            float(actifs_by_year.get(years_to_retrieve[1], {}).get('total_I', Decimal('0'))),
            float(actifs_by_year.get(years_to_retrieve[1], {}).get('total_II', Decimal('0'))),
            float(passifs_by_year.get(years_to_retrieve[1], {}).get('total_I', Decimal('0'))),
            float(passifs_by_year.get(years_to_retrieve[1], {}).get('total_II', Decimal('0')) +
                  passifs_by_year.get(years_to_retrieve[1], {}).get('total_III', Decimal('0'))),
        ],
    }

    charts_data['structure_financiere'] = get_base64_chart(
        {'labels': labels_sf, 'years': ['N', 'N-1'], 'values': [data_sf['N'], data_sf['N-1']]},
        "Structure Financière (Année N vs Année N-1)",
        "Valeur en FCFA"
    )

    # Données pour le graphique de Rentabilité Financière (N-1 vs N-2)
    labels_rf = ['Rendement des Capitaux Propres', 'Rentabilité Économique', 'Rentabilité Financière']
    data_rf = {
        'N-1': [
            float(ratios_by_year_dict.get(years_to_retrieve[1], {}).get('rendement_capitaux_propres', Decimal('0'))),
            float(ratios_by_year_dict.get(years_to_retrieve[1], {}).get('rentabilite_economique', Decimal('0'))),
            float(ratios_by_year_dict.get(years_to_retrieve[1], {}).get('rentabilite_fin', Decimal('0'))),
        ],
        'N-2': [
            float(ratios_by_year_dict.get(years_to_retrieve[2], {}).get('rendement_capitaux_propres', Decimal('0'))),
            float(ratios_by_year_dict.get(years_to_retrieve[2], {}).get('rentabilite_economique', Decimal('0'))),
            float(ratios_by_year_dict.get(years_to_retrieve[2], {}).get('rentabilite_fin', Decimal('0'))),
        ],
    }

    charts_data['rentabilite_financiere'] = get_base64_chart(
        {'labels': labels_rf, 'years': ['N-1', 'N-2'], 'values': [data_rf['N-1'], data_rf['N-2']]},
        "Rentabilité Financière (Année N-1 vs Année N-2)",
        "Valeur en %"
    )

    return charts_data



# Dans vos fichiers d'outils, sous get_base64_chart2 par exemple
import numpy as np

def get_risk_gauge_chart_two(score):
    """
    Génère une jauge de risque (demi-cercle) basée sur un score de 1 à 9.
    """
    if score is None:
        score = 1 # Valeur par défaut si le score est manquant

    # Définition des couleurs et des bornes (Low, Medium, High, Very High)
    # 9 points de risque, divisés en 5 zones
    zones = [
        (1, 3, 'green'),   # 1-3 : Low Risk
        (4, 5, 'yellow'),  # 4-5 : Medium Risk
        (6, 7, 'orange'),  # 6-7 : High Risk
        (8, 9, 'red'),     # 8-9 : Very High Risk
    ]
    
    # Cartographie de l'angle du graphique (0 à 180 degrés)
    max_score = 9
    angle_max = 180
    
    # Calculer l'angle de l'aiguille pour le score
    angle_score = (score - 1) / (max_score - 1) * angle_max
    
    # Conversion de l'angle du graphique à l'angle trigonométrique (cadran inversé)
    angle_aiguille = 90 - angle_score  # 90° au milieu, 180° à gauche, 0° à droite
    
    # Créer la figure Matplotlib
    fig, ax = plt.subplots(figsize=(6, 4), subplot_kw={'projection': 'polar'})
    
    # --- Tracé des zones de risque ---
    for start_score, end_score, color in zones:
        start_angle = (start_score - 1) / (max_score - 1) * angle_max
        end_angle = (end_score) / (max_score - 1) * angle_max
        
        # Inverser l'ordre pour le sens anti-horaire
        ax.bar(
            np.radians(angle_max - end_angle), # Position de départ
            height=0.5, 
            width=np.radians(end_angle - start_angle), # Largeur de la zone
            bottom=0,
            color=color,
            linewidth=0,
            align='edge'
        )

    # --- Configuration du cadran ---
    ax.set_theta_zero_location("N")  # Le 0 est en haut (Nord)
    ax.set_theta_direction(-1)       # Rotation horaire
    ax.set_rticks([])                # Cacher les rayons
    ax.set_xticks(np.radians(np.linspace(180, 0, max_score + 1))) # Étiquettes des scores
    ax.set_xticklabels([str(i) for i in range(1, max_score + 1)] + ['']) # Afficher les chiffres 1 à 9
    ax.set_rlim(0, 1) # Rayon
    ax.spines['polar'].set_visible(False) # Cacher le cercle extérieur
    
    # --- Positionnement de l'aiguille ---
    ax.plot(
        np.radians([angle_max - angle_score, angle_max - angle_score]), 
        [0, 0.5], 
        color='black', 
        linewidth=3, 
        marker='^',
        markersize=10
    )
    
    ax.set_title(f"Évaluation du Risque : Score {score}/9", va='bottom')

    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close(fig)

    return base64.b64encode(buffer.getvalue()).decode('utf-8')





import matplotlib.pyplot as plt
import numpy as np
import io
import base64

def get_risk_gauge_chart_one(score):
    """
    Génère une jauge de risque stylisée comme l'exemple fourni.
    Le score est supposé être entre 1 et 9.
    """
    if score is None:
        score = 1 # Valeur par défaut si le score est manquant

    # Définition des zones de risque (score min, score max, couleur, libellé)
    # Les scores sont de 1 à 9
    zones_config = [
        (1, 2, 'lightgreen', 'VERY LOW'),   # 1-2
        (3, 4, 'green',      'LOW'),        # 3-4
        (5, 6, 'gold',       'MEDIUM'),     # 5-6
        (7, 8, 'orange',     'HIGH'),       # 7-8
        (9, 9, 'red',        'CRITICAL'),   # 9
    ]
    
    # Calcul des angles pour le demi-cercle (0 à 180 degrés)
    max_score = 9
    angle_total = 180
    
    # Créer la figure Matplotlib
    fig, ax = plt.subplots(figsize=(8, 4), subplot_kw={'projection': 'polar'})
    
    # --- Tracé des zones de risque ---
    for start_score, end_score, color, label in zones_config:
        # Calculer les angles correspondants aux scores
        # Les angles vont de 180 (pour le score 1) à 0 (pour le score 9)
        start_angle_deg = angle_total - ((start_score - 1) / (max_score - 1)) * angle_total
        end_angle_deg = angle_total - ((end_score - 1) / (max_score - 1)) * angle_total
        
        # Inverser start_angle_deg et end_angle_deg pour le tracé du bar si nécessaire
        # et s'assurer que l'angle de départ est toujours plus petit pour np.radians
        bar_start_angle = np.radians(min(start_angle_deg, end_angle_deg))
        bar_width_angle = np.radians(abs(start_angle_deg - end_angle_deg))

        ax.bar(
            bar_start_angle,
            height=0.5, # Épaisseur de la bande
            width=bar_width_angle,
            bottom=0,
            color=color,
            linewidth=0,
            align='edge' # Aligner au bord de l'angle
        )
        
        # Ajouter les étiquettes de texte au-dessus des zones
        mid_angle_rad = np.radians(angle_total - (((start_score + end_score) / 2 - 1) / (max_score - 1)) * angle_total)
        
        # Ajustement pour éviter que "CRITICAL" ne se superpose au titre
        text_offset_angle = 10 if label == 'CRITICAL' else 0

        ax.text(
            mid_angle_rad, 
            0.65, # Distance radiale de l'étiquette
            label, 
            ha='center', 
            va='center', 
            fontsize=9, 
            fontweight='bold', 
            color='black',
            rotation=(np.degrees(mid_angle_rad) - 90 + text_offset_angle) % 180 - 90 # Rotation pour suivre la courbure
        )


    # --- Configuration du cadran ---
    ax.set_theta_zero_location("W")  # Le 0 est à gauche (Ouest)
    ax.set_theta_direction(1)        # Rotation anti-horaire
    ax.set_rticks([])                # Cacher les rayons
    ax.set_xticks([])                # Cacher les étiquettes des ticks (les chiffres 1 à 9 ne sont pas dans l'exemple)
    ax.set_rlim(0, 1)                # Rayon
    ax.spines['polar'].set_visible(False) # Cacher le cercle extérieur
    
    # --- Positionnement de l'aiguille ---
    # Convertir le score en angle : score 1 -> 180 deg, score 9 -> 0 deg
    needle_angle_deg = angle_total - ((score - 1) / (max_score - 1)) * angle_total
    
    ax.plot(
        np.radians([needle_angle_deg, needle_angle_deg]), 
        [0, 0.5], # L'aiguille va du centre jusqu'à la moitié du rayon de la jauge
        color='black', 
        linewidth=4, 
        marker='^',
        markersize=12,
        markeredgecolor='black',
        markerfacecolor='black'
    )
    
    # Texte "RISK METER" en haut
    ax.text(np.radians(90), 0.9, "RISK METER", ha='center', va='center', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', transparent=True) # Utiliser transparent=True pour un meilleur rendu
    buffer.seek(0)
    plt.close(fig)

    return base64.b64encode(buffer.getvalue()).decode('utf-8')







import matplotlib.pyplot as plt
import numpy as np
import io
import base64

def get_risk_gauge_chart(score):
    """
    Génère une jauge de risque stylisée exactement comme l'exemple fourni.
    Le score est supposé être entre 1 et 9.
    """
    if score is None:
        score = 1 # Valeur par défaut si le score est manquant, ou gérer comme vous le souhaitez

    # Définition des zones de risque (couleur, libellé, angles de début/fin en degrés)
    # Total de 180 degrés pour le demi-cercle (de -90 à 90 en coordonnées cartésiennes)
    # Ou de 180 (gauche) à 0 (droite) dans notre système polaire ajusté
    
    # Pour un score de 1 à 9, nous avons 8 "intervalles" (9-1)
    # Chaque intervalle fait 180 / 8 = 22.5 degrés
    
    # Mapping des scores aux angles (où 1 = 180 deg, 9 = 0 deg)
    def score_to_angle(s):
        return 180 - ((s - 1) / (9 - 1)) * 180

    zones_config = [
        {'label': 'VERY LOW', 'color': '#92D050', 'start_score': 1, 'end_score': 2}, # Vert clair
        {'label': 'LOW', 'color': '#00B050', 'start_score': 3, 'end_score': 4},     # Vert foncé
        {'label': 'MEDIUM', 'color': '#FFC000', 'start_score': 5, 'end_score': 6}, # Jaune/Or
        {'label': 'HIGH', 'color': '#FF7000', 'start_score': 7, 'end_score': 8},   # Orange
        {'label': 'CRITICAL', 'color': '#FF0000', 'start_score': 9, 'end_score': 9}, # Rouge
    ]
    
    max_score = 9
    
    # Créer la figure Matplotlib
    fig, ax = plt.subplots(figsize=(8, 4.5), subplot_kw={'projection': 'polar'})
    
    # --- Configuration du cadran ---
    ax.set_theta_zero_location("W")  # Le 0 est à gauche (Ouest)
    ax.set_theta_direction(1)        # Rotation anti-horaire (pour que 180 soit à gauche, 0 à droite)
    ax.set_rticks([])                # Cacher les rayons
    ax.set_xticks([])                # Cacher les étiquettes des ticks
    ax.set_rlim(0, 1)                # Rayon
    ax.spines['polar'].set_visible(False) # Cacher le cercle extérieur
    
    # --- Tracé des zones de risque ---
    for zone in zones_config:
        start_angle_rad = np.radians(score_to_angle(zone['start_score']))
        end_angle_rad = np.radians(score_to_angle(zone['end_score']))
        
        # Pour dessiner les arcs, bar en mode polaire
        # L'angle doit être le "milieu" de la barre, et la largeur sa "taille"
        # Il faut que start < end pour np.arange
        # Pour une barre allant de A à B, on la positionne à (A+B)/2 avec une largeur de B-A
        
        # Inverser pour que les angles soient croissants de gauche à droite
        bar_center_rad = (start_angle_rad + end_angle_rad) / 2
        bar_width_rad = abs(start_angle_rad - end_angle_rad)

        ax.bar(
            bar_center_rad,
            height=0.4, # Épaisseur de la bande
            width=bar_width_rad,
            bottom=0,
            color=zone['color'],
            linewidth=0,
            zorder=1 # S'assurer que les zones sont en arrière-plan
        )
        
        # Ajouter les étiquettes de texte
        label_angle_rad = (start_angle_rad + end_angle_rad) / 2
        
        # Ajustement pour la rotation du texte afin qu'il suive la courbure
        # L'angle doit être par rapport à l'horizontale (90 pour vertical)
        text_rotation_deg = np.degrees(label_angle_rad) - 90
        
        ax.text(
            label_angle_rad, 
            0.6, # Distance radiale de l'étiquette
            zone['label'], 
            ha='center', 
            va='center', 
            fontsize=10, 
            fontweight='bold', 
            color='black',
            rotation=text_rotation_deg,
            rotation_mode='anchor' # Permet une rotation plus naturelle
        )

    # --- Positionnement de l'aiguille ---
    needle_angle_rad = np.radians(score_to_angle(score))
    
    ax.plot(
        [needle_angle_rad, needle_angle_rad], 
        [0, 0.4], # L'aiguille va du centre jusqu'à la hauteur des barres de couleur
        color='black', 
        linewidth=3, 
        marker='^',
        markersize=10,
        markeredgecolor='black',
        markerfacecolor='black',
        zorder=2 # S'assurer que l'aiguille est au-dessus des zones
    )
    
    # Texte "RISK METER" en haut, centré
    ax.text(np.radians(90), 0.9, "RISK METER", ha='center', va='center', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', transparent=True, dpi=300) # Augmenter DPI pour meilleure qualité
    buffer.seek(0)
    plt.close(fig)

    return base64.b64encode(buffer.getvalue()).decode('utf-8')





import matplotlib.pyplot as plt
import numpy as np
import io, base64

def get_risk_gauge_base64(score, max_score=9):
    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw={'projection': 'polar'})
    ax.set_theta_offset(np.pi/2)
    ax.set_theta_direction(-1)

    # Zones colorées
    categories = [
        (0, 2, 'green'),
        (2, 4, 'yellow'),
        (4, 6, 'orange'),
        (6, 9, 'red')
    ]

    for start, end, color in categories:
        ax.bar(
            np.linspace(np.radians(start*20), np.radians(end*20), 100),
            np.ones(100), width=0.05, bottom=0,
            color=color, edgecolor=color, alpha=0.7
        )

    # Aiguille
    angle = np.radians(score * 20)
    ax.plot([angle, angle], [0, 1], color='black', linewidth=3)
    ax.set_axis_off()

    # Sauvegarde en mémoire
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    # Conversion en base64
    return base64.b64encode(buf.read()).decode("utf-8")





import base64
import io
import matplotlib.pyplot as plt
from django.template.loader import render_to_string
from weasyprint import HTML

def generate_gauge(score=3):
    # Création d'une petite jauge avec matplotlib
    fig, ax = plt.subplots(figsize=(4, 2))
    ax.barh([0], [score], color="red")
    ax.set_xlim(0, 5)
    ax.set_axis_off()

    # Sauvegarde en mémoire (buffer)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    # Encodage en base64
    return base64.b64encode(buf.read()).decode("utf-8")

def my_view(request):
    # génération de l’image base64
    risk_gauge_base64 = generate_gauge(3)

    context = {
        "summary_and_opinion": {
            "title_5": _("EVALUATION DU RISQUE"),
            "risk_gauge_base64": risk_gauge_base64,
        }
    }

    html_string = render_to_string("rapport.html", context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=rapport.pdf"
    return response


def calculer_scoring_bilan_anglais(acheteur, years_to_retrieve):
    """
    Calcule le scoring ACREMAC avec bilan anglais pour les 3 années
    suivant le même pattern que le scoring classique
    """
    try:
        from main.views_scoring_anglais import ScoreACREMACBilanAnglaisService
        
        scores_anglais = {}
        
        for i, year in enumerate(years_to_retrieve):
            try:
                # Extraire les données du bilan anglais
                donnees_bilan = ScoreACREMACBilanAnglaisService.extraire_donnees_bilan_anglais(acheteur, year)
                
                if donnees_bilan:
                    # Calculer le score complet
                    resultat_calcul = ScoreACREMACBilanAnglaisService.calculer_score_complet(donnees_bilan)
                    
                    score_value = resultat_calcul.get('score', 0.0)
                    interpretation = resultat_calcul.get('classe_risque', 'Non calculé')
                    
                    # Stocker les résultats avec les clés appropriées
                    if i == 0:  # Année N (la plus récente)
                        scores_anglais['score_value_annee_N'] = f"{score_value:.2f}"
                        scores_anglais['interpretation_annee_N'] = interpretation
                    elif i == 1:  # Année N-1
                        scores_anglais['score_value_annee_N1'] = f"{score_value:.2f}"
                        scores_anglais['interpretation_annee_N1'] = interpretation
                    elif i == 2:  # Année N-2
                        scores_anglais['score_value_annee_N2'] = f"{score_value:.2f}"
                        scores_anglais['interpretation_annee_N2'] = interpretation
                        
                else:
                    # Données manquantes pour cette année
                    default_value = "N/A"
                    default_interpretation = "Données manquantes"
                    
                    if i == 0:
                        scores_anglais['score_value_annee_N'] = default_value
                        scores_anglais['interpretation_annee_N'] = default_interpretation
                    elif i == 1:
                        scores_anglais['score_value_annee_N1'] = default_value
                        scores_anglais['interpretation_annee_N1'] = default_interpretation
                    elif i == 2:
                        scores_anglais['score_value_annee_N2'] = default_value
                        scores_anglais['interpretation_annee_N2'] = default_interpretation
                        
            except Exception as e:
                print(f"Erreur calcul scoring anglais année {year}: {e}")
                # Valeurs par défaut en cas d'erreur
                default_value = "Erreur"
                default_interpretation = "Erreur de calcul"
                
                if i == 0:
                    scores_anglais['score_value_annee_N'] = default_value
                    scores_anglais['interpretation_annee_N'] = default_interpretation
                elif i == 1:
                    scores_anglais['score_value_annee_N1'] = default_value
                    scores_anglais['interpretation_annee_N1'] = default_interpretation
                elif i == 2:
                    scores_anglais['score_value_annee_N2'] = default_value
                    scores_anglais['interpretation_annee_N2'] = default_interpretation
        
        return scores_anglais
        
    except Exception as e:
        print(f"Erreur initialisation scoring anglais: {e}")
        # Retourner un dictionnaire vide en cas d'erreur générale
        return {
            'score_value_annee_N': "N/A",
            'interpretation_annee_N': "Service indisponible",
            'score_value_annee_N1': "N/A", 
            'interpretation_annee_N1': "Service indisponible",
            'score_value_annee_N2': "N/A",
            'interpretation_annee_N2': "Service indisponible"
        }
        
        
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
        current_year = dt.now().year
        years_to_retrieve = [current_year - 1, current_year - 2, current_year - 3]
        # N, N-1, N-2 : le plus récent en premier (years[0]=N, years[1]=N-1, years[2]=N-2)
        years_to_retrieve = sorted(years_to_retrieve, reverse=True)
        print("years_to_retrieve (sorted desc):", years_to_retrieve)
        
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
        # naf_codes = list(CodeNafAcheteur.objects.filter(acheteur=acheteur).values_list('code', flat=True))
        # nace_codes = list(CodeNaceAcheteur.objects.filter(acheteur=acheteur).values_list('code', flat=True))
        # Recuperation des codes NACE avec leurs libellés
        nace_codes_data = list(CodeNaceAcheteur.objects.filter(acheteur=acheteur)
            .select_related('code__category')
            .values('code__code', 'code__libelle', 'code__category__code', 'code__category__libelle')
            .distinct()
            .order_by('code__category__code', 'code__code'))

        nace_codes_formatted = []
        nace_by_cat: dict = {}
        for item in nace_codes_data:
            raw_code = item['code__code'] or ''
            display_code = raw_code.split('.', 1)[1] if '.' in raw_code else raw_code
            libelle = item['code__libelle'] or ''
            nace_codes_formatted.append(f"{display_code} - {libelle}" if libelle else display_code)
            cat_code = item['code__category__code'] or '—'
            cat_libelle = item['code__category__libelle'] or 'Non classifié'
            if cat_code not in nace_by_cat:
                nace_by_cat[cat_code] = {'cat_code': cat_code, 'cat_libelle': cat_libelle, 'codes': []}
            nace_by_cat[cat_code]['codes'].append({'code': display_code, 'libelle': libelle or '—'})
        nace_codes_grouped = list(nace_by_cat.values())

        # Recuperation des codes NAF avec leurs libellés
        naf_codes_data = list(CodeNafAcheteur.objects.filter(acheteur=acheteur)
            .select_related('code__category')
            .values('code__code', 'code__libelle', 'code__category__libelle')
            .distinct())

        # Formatage pour affichage
        naf_codes_formatted = []
        for item in naf_codes_data:
            if item['code__libelle']:
                naf_codes_formatted.append(f"{item['code__code']} - {item['code__libelle']}")
            else:
                naf_codes_formatted.append(item['code__code'])

        
        
        # Recuperation du resume en fonction de l'acheteur
        try:
            resume = Resume.objects.get(acheteur=acheteur)
        except Resume.DoesNotExist:
            resume = None
        
        # Recuperation de l'evaluation de risque de l'acheteur 
        # Recuperation de l'evaluation de risque chiffree de l'acheteur  
        risk_rating_value = 0
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
                risk_rating_value = min(risk_rating_value, 8)
            else:
                risk_rating = None
                
        except Exception as e:
            risk_rating = None
            risk_rating_value = 0
            
        
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
        properties_and_assets = ProprieteEtActif.objects.filter(acheteur=acheteur).prefetch_related("locaux")
        list_properties_and_assets_data = []

        # 2. Bouclez sur les objets pour construire une liste de dictionnaires
        for prop_asset in properties_and_assets:
            locaux_labels = [str(local) for local in prop_asset.locaux.all()]
            list_properties_and_assets_data.append({
                "locaux": locaux_labels if locaux_labels else [],
                "branche": prop_asset.branche if prop_asset.branche else "",
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
        footer_3 = "moyens à sa disposition sans être liée par une obligation de résultat.."
            
            
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
        
        
        # Décodez et sauvegardez l'image si vous voulez la voir localement
        # with open(f"risk_gauge_score_{score_exemple}.png", "wb") as f:
        #     f.write(base64.b64decode(base64_image))
        # print(f"Image sauvegardée pour le score {score_exemple}")
        
        
        def format_currency(value):
            """Formate un nombre décimal en chaîne avec des séparateurs de milliers."""
            if value is None:
                return "Non spécifié"
            return f"{value:,.2f}".replace(",", " ").replace(".", ",") # Exemple de formatage français
        
        # 4. Appel à la fonction pour obtenir les données structurées des actifs
        actifs_table_data = get_simple_actifs_data(acheteur, years_to_retrieve)
        actifs_structured_data = get_structured_actif_data(acheteur, years_to_retrieve)
        passif_structured_data = get_structured_passif_data(acheteur, years_to_retrieve)
        resultat_structured_data = get_structured_resultat_data(acheteur, years_to_retrieve)
        ratios_structured_data = get_structured_ratios_data(acheteur, years_to_retrieve) 
        
        # NOUVEAU : Gérer la génération des graphiques
        # Dans la vue GenerateReport, après avoir récupéré les données financières :
        # ...
        # Récupérer les données pour les graphiques
        # actifs_by_year = {year: get_structured_actif_data(acheteur, [year])[0] for year in years_to_retrieve}
        # passifs_by_year = {year: get_structured_passif_data(acheteur, [year])[0] for year in years_to_retrieve}
        # ratios_by_year_dict = {year: get_structured_ratios_data(acheteur, [year])[0] for year in years_to_retrieve}

        # Générer les graphiques
        # charts_data = get_charts_data(actifs_by_year, passifs_by_year, ratios_by_year_dict, years_to_retrieve)

        # charts_data = {}
        
        # print(charts_data)
        
        # 2. Récupérer les données financières pour les années spécifiées
        actifs_by_year = {}
        resultats_by_year = {}
        ratios_by_year = {}

        for annee in years_to_retrieve:
            try:
                actif_instance = ActifC.objects.get(acheteur_id=acheteur_id, annee__annee=annee)
                resultat_instance = ResultatC.objects.get(acheteur_id=acheteur_id, annee__annee=annee)
                
                # Créez une instance de RatiosClassique pour chaque année
                # Remarque : Votre code initial n'avait pas de PassifC, mais le modèle RatiosClassique en a besoin
                # Supposons que vous ayez une instance de PassifC pour cette année aussi.
                try:
                    passif_instance = PassifC.objects.get(acheteur_id=acheteur_id, annee__annee=annee)
                except PassifC.DoesNotExist:
                    passif_instance = None # Ou créez une instance vide

                ratios_instance = RatiosClassique(actif_instance, passif_instance, resultat_instance)
                
                # Stocker les instances et leurs calculs
                actifs_by_year[annee] = actif_instance
                resultats_by_year[annee] = resultat_instance
                
                # Stocker les ratios calculés dans un dictionnaire
                ratios_by_year[annee] = {
                    'rentabilite_fin': ratios_instance.rentabilite_fin,
                    'solvabilite': ratios_instance.solvabilite,
                    'rendement_capitaux_propres': ratios_instance.rendement_capitaux_propres
                }
            except (ActifC.DoesNotExist, ResultatC.DoesNotExist):
                # Gérer le cas où les données pour une année sont manquantes
                continue
        
        # 3. Préparer les données pour les graphiques
        # Graphique de Structure Financière (Année N vs N-1)
        data_structure = {
            'labels': ['Actif Immobilisé', 'Actif Circulant', 'Total Actif'],
            'datasets': [
                {
                    'label': f'Année {years_to_retrieve[0]}',
                    'data': [
                        to_float(actifs_by_year.get(years_to_retrieve[0], ActifC()).total_I),
                        to_float(actifs_by_year.get(years_to_retrieve[0], ActifC()).total_II),
                        to_float(actifs_by_year.get(years_to_retrieve[0], ActifC()).general_total),
                    ]
                },
                {
                    'label': f'Année {years_to_retrieve[1]}',
                    'data': [
                        to_float(actifs_by_year.get(years_to_retrieve[1], ActifC()).total_I),
                        to_float(actifs_by_year.get(years_to_retrieve[1], ActifC()).total_II),
                        to_float(actifs_by_year.get(years_to_retrieve[1], ActifC()).general_total),
                    ]
                }
            ]
        }

        # Graphique de Rentabilité Financière (Année N-1 vs N-2)
        data_rentabilite = {
            'labels': ['Résultat Net', 'Chiffre d\'Affaires'],
            'datasets': [
                {
                    'label': f'Année {years_to_retrieve[1]}',
                    'data': [
                        to_float(resultats_by_year.get(years_to_retrieve[1], ResultatC()).resultat_exercice),
                        to_float(resultats_by_year.get(years_to_retrieve[1], ResultatC()).ca),
                    ]
                },
                {
                    'label': f'Année {years_to_retrieve[2]}',
                    'data': [
                        to_float(resultats_by_year.get(years_to_retrieve[2], ResultatC()).resultat_exercice),
                        to_float(resultats_by_year.get(years_to_retrieve[2], ResultatC()).ca),
                    ]
                }
            ]
        }


        # Calculer le score
        risk_score = risk_rating.calculate_risk_score() if risk_rating else 1

        # Générer l'image de la jauge en Base64
        risk_gauge_base64 = get_risk_gauge_chart(risk_score)
        
        
        # NOUVEAU: SCORING SANS BILAN
        # Recuperer le scoring sans bilan ici 
        scoring_sans_bilan = ScoringSansBilanAcheteur.objects.filter(acheteur=acheteur).first()
        scoring_manuel_context = build_scoring_manuel_context(acheteur, years_to_retrieve)
        print(scoring_sans_bilan)

        # par défaut
        score_indexe = 0
        scoring_context = None
        if scoring_sans_bilan:
            # Limiter le score entre 0 et 10 pour correspondre aux images
            try:
                score_indexe = int(round(scoring_sans_bilan.scoring_value or 0))
            except Exception:
                score_indexe = 0
            score_indexe = max(0, min(score_indexe, 10))
            print(int(round(scoring_sans_bilan.scoring_value or 0)))
            print(score_indexe)
            scoring_context = {
                "title_26": _("SCORING ACREMAC - SANS BILAN"),
                "score_image": f"scoring/{score_indexe}.png",
                "score_png": f"scoring/{score_indexe}.png",
                "score_value": f"{scoring_sans_bilan.scoring_value:.2f}" if scoring_sans_bilan.scoring_value is not None else "",
                "interpretation": scoring_sans_bilan.interpretation or "",
                "commentaire": scoring_sans_bilan.commentaire or "",
                "score_type": "Scoring sans bilan",
            }
        else:
            score_indexe = 0
        # NOUVEAU: SCORING AVEC BILAN CLASSIQUE
        # Scoring avec bilan classique
        # Récupérer le scoring avec bilan en fonction du type de bilan
        scoring_avec_bilan = None
        try:
            # Initialiser le scoring avec bilan
            scoring_generator = AcremacScoring(acheteur, bilan_report, current_year-1)
            scoring_result = scoring_generator.calculate_score_with_bilan()
            
            if scoring_result[0]:  # Si le calcul a réussi
                scoring_avec_bilan_data = scoring_result[0]
                score_avec_bilan = scoring_avec_bilan_data['score']
                
                # Limiter le score entre 0 et 10 pour correspondre aux images
                score_index_avec_bilan = int(round(score_avec_bilan))
                score_index_avec_bilan = max(0, min(score_index_avec_bilan, 10))
                
                scoring_avec_bilan = {
                    'score_image': f"scoring/{score_index_avec_bilan}.png",
                    'score_value': f"{score_avec_bilan:.2f}",
                    'interpretation': scoring_generator.get_score_interpretation(score_avec_bilan),
                    'commentaire': f"Score calculé avec les données du bilan {bilan_report}",
                    'details': scoring_avec_bilan_data.get('details', [])
                }
            else:
                scoring_avec_bilan = {
                    'score_image': "scoring/1.png",
                    'score_value': "N/A",
                    'interpretation': "Calcul impossible - données manquantes",
                    'commentaire': f"Impossible de calculer le score avec le bilan {bilan_report}",
                    'details': []
                }
        except Exception as e:
            print(f"Erreur lors du calcul du scoring avec bilan: {e}")
            scoring_avec_bilan = None

        
        
        
        # 4. Générer les graphiques en Base64
        charts_data = {
            'structure_financiere': get_base64_chart2(
                data_structure,
                "Structure Financière (Année N vs N-1)",
                "Montant en FCFA",
                chart_type='bar'
            ),
            'rentabilite_financiere': get_base64_chart2(
                data_rentabilite,
                "Rentabilité Financière (Année N-1 vs N-2)",
                "Montant en FCFA",
                chart_type='bar'
            )
        }

        # NOUVEAU: SCORING AVEC BILAN CLASSIQUE
        # Scoring avec bilan classique
        # Récupérer le scoring avec bilan en fonction du type de bilan
        # Calculer le scoring pour chaque année
        for i, year in enumerate(years_to_retrieve):
            annee_label = f"annee_N{i}" if i == 0 else f"annee_N{i+1}"[-2:]
            donnees_bilan = ScoreACREMACBilanClassiqueService.extraire_donnees_bilan_classique(acheteur, year)

            if donnees_bilan:
                resultat_calcul = ScoreACREMACBilanClassiqueService.calculer_score_complet(donnees_bilan)
                score = resultat_calcul['score']
                score_index = round(score)
                classe_risque = resultat_calcul['classe_risque']

                # Mettre à jour les variables de score
                if i == 0:
                    score_value_annee_N = str(score)
                    interpretation_annee_N = classe_risque
                elif i == 1:
                    score_value_annee_N1 = str(score)
                    interpretation_annee_N1 = classe_risque
                elif i == 2:
                    score_value_annee_N2 = str(score)
                    interpretation_annee_N2 = classe_risque


        # NOUVEAU: SCORING AVEC BILAN ANGLAIS
        # Scoring avec bilan anglais
        # Initialisation des scores par année pour le bilan anglais
        score_value_anglais_annee_N = None
        score_value_anglais_annee_N1 = None
        score_value_anglais_annee_N2 = None
        interpretation_anglais_annee_N = "N/A"
        interpretation_anglais_annee_N1 = "N/A"
        interpretation_anglais_annee_N2 = "N/A"
        # Calculer le scoring anglais pour chaque année
        for i, year in enumerate(years_to_retrieve):
            annee_label = f"annee_N{i}" if i == 0 else f"annee_N{i+1}"[-2:]
            donnees_bilan_anglais = ScoreACREMACBilanAnglaisService.extraire_donnees_bilan_anglais(acheteur, year)

            if donnees_bilan_anglais:
                resultat_calcul_anglais = ScoreACREMACBilanAnglaisService.calculer_score_complet(donnees_bilan_anglais)
                score_anglais = resultat_calcul_anglais['score']
                score_index_anglais = round(score_anglais)
                classe_risque_anglais = resultat_calcul_anglais['classe_risque']

                # Mettre à jour les variables de score anglais
                if i == 0:
                    score_value_anglais_annee_N = str(score_anglais)
                    interpretation_anglais_annee_N = classe_risque_anglais
                elif i == 1:
                    score_value_anglais_annee_N1 = str(score_anglais)
                    interpretation_anglais_annee_N1 = classe_risque_anglais
                elif i == 2:
                    score_value_anglais_annee_N2 = str(score_anglais)
                    interpretation_anglais_anglais_annee_N2 = classe_risque_anglais



        # NOUVEAU: SCORING AVEC BILAN BANCAIRE
        # Scoring avec bilan bancaire
        # Initialisation des scores par année pour le bilan bancaire
        score_value_bancaire_annee_N = None
        score_value_bancaire_annee_N1 = None
        score_value_bancaire_annee_N2 = None
        interpretation_bancaire_annee_N = "N/A"
        interpretation_bancaire_annee_N1 = "N/A"
        interpretation_bancaire_annee_N2 = "N/A"
        # Calculer le scoring bancaire pour chaque année
        for i, year in enumerate(years_to_retrieve):
            annee_label = f"annee_N{i}" if i == 0 else f"annee_N{i+1}"[-2:]
            donnees_bilan_bancaire = ScoreACREMACBilanBancaireService.extraire_donnees_bilan_bancaire(acheteur, year, bilan_type="annuel")

            if donnees_bilan_bancaire:
                resultat_calcul_bancaire = ScoreACREMACBilanBancaireService.calculer_score_complet_bancaire(donnees_bilan_bancaire)
                score_bancaire = resultat_calcul_bancaire['score']
                score_index_bancaire = round(score_bancaire)
                classe_risque_bancaire = resultat_calcul_bancaire['classe_risque']

                # Mettre à jour les variables de score bancaire
                if i == 0:
                    score_value_bancaire_annee_N = str(score_bancaire)
                    interpretation_bancaire_annee_N = classe_risque_bancaire
                elif i == 1:
                    score_value_bancaire_annee_N1 = str(score_bancaire)
                    interpretation_bancaire_annee_N1 = classe_risque_bancaire
                elif i == 2:
                    score_value_bancaire_annee_N2 = str(score_bancaire)
                    interpretation_bancaire_annee_N2 = classe_risque_bancaire
            


        # NOUVEAU: SCORING AVEC BILAN SYSCOHADA
        # Scoring avec bilan syscohada
        # Initialisation des scores par année pour le bilan syscohada
        # Initialisation des scores par année pour le bilan SYSCOHADA
        score_value_syscohada_annee_N = None
        score_value_syscohada_annee_N1 = None
        score_value_syscohada_annee_N2 = None
        interpretation_syscohada_annee_N = "N/A"
        interpretation_syscohada_annee_N1 = "N/A"
        interpretation_syscohada_annee_N2 = "N/A"
        # Calculer le scoring SYSCOHADA pour chaque année
        for i, year in enumerate(years_to_retrieve):
            annee_label = f"annee_N{i}" if i == 0 else f"annee_N{i+1}"[-2:]
            donnees_bilan_syscohada = ScoreACREMACBilanSyscohadaService.extraire_donnees_bilan_syscohada(acheteur, year)

            if donnees_bilan_syscohada:
                resultat_calcul_syscohada = ScoreACREMACBilanSyscohadaService.calculer_score_complet_syscohada(donnees_bilan_syscohada)
                score_syscohada = resultat_calcul_syscohada['score']
                score_index_syscohada = round(score_syscohada)
                classe_risque_syscohada = resultat_calcul_syscohada['classe_risque']

                # Mettre à jour les variables de score SYSCOHADA
                if i == 0:
                    score_value_syscohada_annee_N = str(score_syscohada)
                    interpretation_syscohada_annee_N = classe_risque_syscohada
                elif i == 1:
                    score_value_syscohada_annee_N1 = str(score_syscohada)
                    interpretation_syscohada_annee_N1 = classe_risque_syscohada
                elif i == 2:
                    score_value_syscohada_annee_N2 = str(score_syscohada)
                    interpretation_syscohada_annee_N2 = classe_risque_syscohada




        # NOUVEAU: SCORING AVEC BILAN IFRS COBAC
        # Scoring avec bilan Ifrs Cobac
        # Initialisation des scores par année pour le bilan IFRS COBAC
        score_value_ifrs_annee_N = None
        score_value_ifrs_annee_N1 = None
        score_value_ifrs_annee_N2 = None
        interpretation_ifrs_annee_N = "N/A"
        interpretation_ifrs_annee_N1 = "N/A"
        interpretation_ifrs_annee_N2 = "N/A"
        # Calculer le scoring IFRS COBAC pour chaque année
        for i, year in enumerate(years_to_retrieve):
            annee_label = f"annee_N{i}" if i == 0 else f"annee_N{i+1}"[-2:]
            donnees_bilan_ifrs = ScoreACREMACBilanIFRSService.extraire_donnees_bilan_ifrs(acheteur, year)

            if donnees_bilan_ifrs:
                resultat_calcul_ifrs = ScoreACREMACBilanIFRSService.calculer_score_complet_ifrs(donnees_bilan_ifrs)
                score_ifrs = resultat_calcul_ifrs['score']
                score_index_ifrs = round(score_ifrs)
                classe_risque_ifrs = resultat_calcul_ifrs['classe_risque']

                # Mettre à jour les variables de score IFRS COBAC
                if i == 0:
                    score_value_ifrs_annee_N = str(score_ifrs)
                    interpretation_ifrs_annee_N = classe_risque_ifrs
                elif i == 1:
                    score_value_ifrs_annee_N1 = str(score_ifrs)
                    interpretation_ifrs_annee_N1 = classe_risque_ifrs
                elif i == 2:
                    score_value_ifrs_annee_N2 = str(score_ifrs)
                    interpretation_ifrs_annee_N2 = classe_risque_ifrs


        


        # ACREMAC Rating Score et Delphi Score
        scorings_rating_qs = ScoringRating.objects.filter(acheteur=acheteur).select_related('annee').order_by('-annee__annee')
        scoring_rating_entries = []
        for sr in scorings_rating_qs:
            sv = float(sr.score_final) if sr.score_final is not None else None
            scoring_rating_entries.append({
                "annee": str(sr.annee) if sr.annee else "",
                "score_final": f"{sv:.2f}" if sv is not None else "-",
                "rating": sr.rating or "-",
                "classe_risque": sr.classe_risque or "-",
                "decision": sr.decision or "-",
                "red_flag": sr.red_flag,
                "commentaire": sr.commentaire or "",
            })
        try:
            _sd = ScoringDelphi.objects.get(acheteur=acheteur)
            scoring_delphi_ctx = {
                "score_delphi": _sd.score_delphi if _sd.score_delphi is not None else "-",
                "bande": _sd.bande or "-",
                "etoiles": _sd.etoiles if _sd.etoiles is not None else "-",
                "niveau_risque": _sd.niveau_risque or "-",
                "commentaire": _sd.commentaire or "",
            }
        except ScoringDelphi.DoesNotExist:
            scoring_delphi_ctx = None

        telephones_acheteur = list(
            TelephoneAcheteur.objects.filter(acheteur=acheteur)
            .exclude(telephone__isnull=True)
            .exclude(telephone__exact="")
            .values("telephone", "nom")
            .distinct()
        )
        portables_acheteur = list(
            PortableAcheteur.objects.filter(acheteur=acheteur)
            .exclude(portable__isnull=True)
            .exclude(portable__exact="")
            .values("portable", "nom")
            .distinct()
        )
        emails_acheteur = list(
            EmailAcheteur.objects.filter(acheteur=acheteur)
            .exclude(email__isnull=True)
            .exclude(email__exact="")
            .values("email", "description")
            .distinct()
        )
        adresses_acheteur = list(
            AdresseAcheteur.objects.filter(acheteur=acheteur)
            .exclude(adresse__isnull=True)
            .exclude(adresse__exact="")
            .values_list("adresse", flat=True)
            .distinct()
        )

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
                "bilan_report": bilan_report.upper() if bilan_report else "",
                "format_report": format_report,
                "date_today": dt.now().strftime("%d/%m/%Y %H:%M:%S"),
            },
            "footer_report": {
                "footer_text_1": footer_1,
                "footer_text_2": footer_2,
                "footer_text_3": footer_3,
            },
            "commande": {
                "title_1": _("DETAILS COMMANDE"),
                "client": commande.client.username if hasattr(commande, 'client') and commande.client else "Non spécifié",
                "ref_client": commande.reference_client if hasattr(commande, 'reference_client') else "Non spécifié",
                "notre_ref": commande.notre_ref if hasattr(commande, 'notre_ref') else "Non spécifié",
                "date_recept_commande": commande.date_recept_commande.strftime("%d/%m/%Y") if hasattr(commande, 'date_recept_commande') and commande.date_recept_commande else "Non spécifié",
                "date_rapport": commande.date_rapport.strftime("%d/%m/%Y") if hasattr(commande, 'date_rapport') and commande.date_rapport else "Non spécifié",
                "delais": commande.delais if hasattr(commande, 'delais') else "Non spécifié",
                "priorite": commande.priorite if hasattr(commande, 'priorite') else "Non spécifié",
                "type_rapport": commande.type_rapport if hasattr(commande, 'type_rapport') else "Non spécifié"
            },
            "identification": {
                "title_2": _("IDENTIFICATION"),
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
                    "province": acheteur.province.nom if hasattr(acheteur, 'province') and acheteur.province else "Non spécifié",
                    "ville": acheteur.ville.nom if hasattr(acheteur, 'ville') and acheteur.ville else "Non spécifié",
                    "region": acheteur.region.nom if hasattr(acheteur, 'region') and acheteur.region else "",
                    "fax": acheteur.fax if hasattr(acheteur, 'fax') else "Non spécifié",
                    "telephone": telephones_acheteur[0]["telephone"] if telephones_acheteur else (acheteur.telephone if hasattr(acheteur, 'telephone') and acheteur.telephone else "Non spécifié"),
                    "telephones": telephones_acheteur,
                    "portables": portables_acheteur,
                    "emails_secondaires": emails_acheteur,
                    "adresses_secondaires": adresses_acheteur,
                    "numero_adresse": acheteur.numero_adresse if hasattr(acheteur, 'numero_adresse') else "Non spécifié",
                    "code_postal": acheteur.code_postal if hasattr(acheteur, 'code_postal') else "Non spécifié",
                }
            },
            "additional_information": {
                "title_3": _("INFORMATIONS SUPPLEMENTAIRES"),
                "site_internet": acheteur.site_internet if hasattr(acheteur, 'site_internet') else "Non spécifié",
                "forme_juridique": acheteur.forme_juridique.libelle if hasattr(acheteur, 'forme_juridique') else "Non spécifié",
                "activite_principale": acheteur.activite_principale if hasattr(acheteur, 'activite_principale') else "Non spécifié",
                "description": acheteur.description if hasattr(acheteur, 'description') else "Non spécifié",
                "statut_entreprise": acheteur.statut_entreprise.libelle if hasattr(acheteur, 'statut_entreprise') else "Non spécifié",
                "date_creation": acheteur.date_creation.strftime("%d/%m/%Y") if hasattr(acheteur, 'date_creation') and acheteur.date_creation else "Non spécifié",
                "nace_codes": nace_codes_formatted if nace_codes_formatted else ["Aucun code NACE disponible"],
                "nace_codes_grouped": nace_codes_grouped if nace_codes_grouped else [],
                "naf_codes": naf_codes_formatted if naf_codes_formatted else ["Aucun code NAF disponible"],
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
                "title_4": _("RESUME EXECUTIF"),
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
                "title_5": _("EVALUATION DU RISQUE"),
                # Utiliser la chaîne Base64 pour l'affichage de la jauge
                "risk_gauge_base64": risk_gauge_base64,
                "risk_rating_image_base64": (
                    get_risk_rating_png_base64(risk_rating_value)
                    or (risk_rating.get_risk_rating_image_base64() if risk_rating else None)
                ),
                #"get_risk_gauge_image": get_risk_gauge_image,
                "risk_gauge_base64": risk_gauge_base64,
                "risk_rating_value": max(0, min(8, int(risk_rating_value or 0))),
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
                "title_6": _("AVIS CREDIT ACREMAC"),
                # Passez le dictionnaire directement au template
                "notes": notes_str, # Passez la chaîne formatée au template
                "highlighted_risks": highlighted_risks,
                "montant_credit_maximum": acremac_opinion.montant_credit_maximum if acremac_opinion else "Non spécifié",
                "commentaire": acremac_opinion.commentaire if acremac_opinion else "Aucun commentaire disponible",
            },
            "registered_data": {
                "title_7": _("DONNEES D'ENREGISTREMENT"),
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
                "title_8": _("ANTECEDENTS JURIDIQUES"),
                "antecedents_juridiques": list_antecedants_data if list_antecedants_data else [],
            },
            "management": {
                "title_9": _("MANAGEMENT DU RISQUE"),
                "risk_management": {
                    "professionalisme": risk_management.professionalisme if risk_management and risk_management.professionalisme else "Non spécifié",
                    "organisation": risk_management.organisation if risk_management and risk_management.organisation else "Non spécifié",
                    "turn_over": risk_management.turn_over if risk_management and risk_management.turn_over else "Non spécifié",
                    "greve": risk_management.greve if risk_management and risk_management.greve else "Non spécifié",
                    "degradation_qualite": risk_management.degradation_qualite if risk_management and risk_management.degradation_qualite else "Non spécifié",
                    "non_respect_condition": risk_management.non_respect_condition if risk_management and risk_management.non_respect_condition else "Non spécifié",
                    "commentaire": risk_management.commentaire if risk_management and risk_management.commentaire else "Aucun commentaire disponible",
                    "score": risk_management.get_management_score()['oui_count'] if risk_management else 0,
                    "image": risk_management.get_management_image_path_report() if risk_management else "management/passable.png",
                },
                "responsables": list_responsables_data if list_responsables_data else "Aucun responsable disponible",
                "conseil_administration": list_ca_membres_data if list_ca_membres_data else "Aucun membre du conseil d'administration disponible",
            },
            "capital_composition": {
                "title_10": _("COMPOSITION DU CAPITAL"),
                "emis": format_currency(composition_capital_social.emis) if composition_capital_social else "Non spécifié",
                "publie": format_currency(composition_capital_social.publie) if composition_capital_social else "Non spécifié",
                "libere": format_currency(composition_capital_social.libere) if composition_capital_social else "Non spécifié",
                "devise": composition_capital_social.devise.code if composition_capital_social and composition_capital_social.devise else "Non spécifié",
                "commentaire": composition_capital_social.commentaire if composition_capital_social and composition_capital_social.commentaire else "Aucun commentaire disponible",
            },
            "shareholders": {
                "title_11": _("ACTIONNARIAT/PROPRIETAIRES"),
                "actionnaires": list_shareholders_data if list_shareholders_data else [],
            },
            "affiliations": {
                "title_12": _("AFFILIATIONS CORPORATIVES"),
                "affiliations": list_affiliations_data if list_affiliations_data else [],
            },
            "sector_analysis": {
                "title_13": _("ANALYSE SECTORIELLE"),
                "nace_codes": nace_codes_formatted if nace_codes_formatted else ["Aucun code NACE disponible"],
                "nace_codes_grouped": nace_codes_grouped if nace_codes_grouped else [],
                "naf_codes": naf_codes_formatted if naf_codes_formatted else ["Aucun code NAF disponible"],
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
                    "title_advice": _("CONSEILS D'ACREMAC"),
                    "forces": advice.forces if advice and advice.forces else "",
                    "faiblesses": advice.faiblesses if advice and advice.faiblesses else "",
                    "opportunites": advice.opportunites if advice and advice.opportunites else "",
                    "dynamisme_long_terme": advice.dynamisme_long_terme if advice and advice.dynamisme_long_terme else "",
                    "menaces": advice.menaces if advice and advice.menaces else "",
                },
                "geopolitics": {
                    "donnees_politiques": geopolitics.donnees_politiques if geopolitics and geopolitics.donnees_politiques else "Non spécifié",
                    "donnees_economiques": geopolitics.donnees_economiques if geopolitics and geopolitics.donnees_economiques else "Non spécifié",
                },
            },
            "advice": {
                "title_advice": _("CONSEILS D'ACREMAC"),
                "forces": advice.forces if advice and advice.forces else "",
                "faiblesses": advice.faiblesses if advice and advice.faiblesses else "",
                "opportunites": advice.opportunites if advice and advice.opportunites else "",
                "dynamisme_long_terme": advice.dynamisme_long_terme if advice and advice.dynamisme_long_terme else "",
                "menaces": advice.menaces if advice and advice.menaces else "",
            },
            "banking_data": {
                "title_14": _("DONNEES BANCAIRES"),
                "data_banks": list_banking_data if list_banking_data else [],
            },

            "financial_accounts": {
                "title_15": _("COMPTES FINANCIERS"),
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
                "title_16": _("ETATS FINANCIERS"),
                "years": years_to_retrieve,
                "bilan_type": bilan_report,
                "etats_financiers_classiques": {
                    "actif_table": actifs_table_data,
                    "actif_data": actifs_structured_data,
                    "passif_data": passif_structured_data,
                    "resultat_data": resultat_structured_data,
                    "ratios_data": ratios_structured_data,
                    "charts_data_v1": charts_data,
                    "charts_data": {
                        "charts_structure_financiere": get_charts_structure_financiere_data(acheteur, years_to_retrieve, chart_type='bar'),
                        "charts_rentabilite_financiere": get_charts_rentabilite_financiere_data(acheteur, years_to_retrieve, chart_type='bar'),
                        "charts_delais": get_charts_delais_data(acheteur, years_to_retrieve, chart_type='bar'),
                    },
                },
                "etats_financiers_anglais": {
                    "actif_data": get_structured_actif_anglais_data(acheteur, years_to_retrieve),
                    "passif_data": get_structured_passif_anglais_data(acheteur, years_to_retrieve),
                    "resultat_data": get_structured_resultat_anglais_data(acheteur, years_to_retrieve),
                    "ratios_data": get_structured_ratios_anglais_data(acheteur, years_to_retrieve),
                    "charts_data": {
                        "charts_structure_financiere": get_charts_structure_financiere_anglais_data(acheteur, years_to_retrieve),
                        "charts_rentabilite_financiere": get_charts_rentabilite_financiere_anglais_data(acheteur, years_to_retrieve),
                        "charts_delais": get_charts_delais_anglais_data(acheteur, years_to_retrieve),
                    },
                },
                "etats_financiers_bancaires": {
                    "actif_data": get_structured_actif_bancaire_data(acheteur, years_to_retrieve),
                    "passif_data": get_structured_passif_bancaire_data(acheteur, years_to_retrieve),
                    "produit_data": get_structured_produit_bancaire_data(acheteur, years_to_retrieve),
                    "depense_data": get_structured_depense_bancaire_data(acheteur, years_to_retrieve),
                    "hors_bilan_data": get_structured_hors_bilan_bancaire_data(acheteur, years_to_retrieve),
                    "ratios_data": get_structured_ratios_bancaire_data(acheteur, years_to_retrieve),
                    "charts_data": {
                        "charts_structure_financiere": get_charts_structure_financiere_bancaire_data(acheteur, years_to_retrieve),
                        "charts_rentabilite_financiere": get_charts_rentabilite_bancaire_data(acheteur, years_to_retrieve),
                        "charts_delais": get_charts_ratios_bancaire_data(acheteur, years_to_retrieve),
                    },
                },
                "etats_financiers_syscohada": {
                    "actif_data": get_structured_actif_syscohada_data(acheteur, years_to_retrieve),
                    "passif_data": get_structured_passif_syscohada_data(acheteur, years_to_retrieve),
                    "resultat_data": get_structured_resultat_syscohada_data(acheteur, years_to_retrieve),
                    "ratios_data": get_structured_ratios_syscohada_data(acheteur, years_to_retrieve),
                    "charts_data": {
                        "charts_structure_financiere": get_charts_structure_financiere_syscohada_data(acheteur, years_to_retrieve),
                        "charts_rentabilite_financiere": get_charts_rentabilite_financiere_syscohada_data(acheteur, years_to_retrieve),
                        "charts_delais": get_charts_delais_syscohada_data(acheteur, years_to_retrieve),
                    },
                },
                "etats_financiers_irfs_cobac": {
                    "actif_data": get_structured_actif_ifrs_data(acheteur, years_to_retrieve),
                    "passif_data": get_structured_passif_ifrs_data(acheteur, years_to_retrieve),
                    "resultat_data": get_structured_resultat_ifrs_data(acheteur, years_to_retrieve),
                    "ratios_data": get_structured_ratios_ifrs_data(acheteur, years_to_retrieve),
                    "charts_data": {
                        "charts_structure_financiere": get_charts_structure_financiere_ifrs_data(acheteur, years_to_retrieve),
                        "charts_rentabilite_financiere": get_charts_rentabilite_financiere_ifrs_data(acheteur, years_to_retrieve),
                        "charts_delais": get_charts_delais_ifrs_data(acheteur, years_to_retrieve),
                    },
                },

            },
            
            "translations": {},
            "scoring_manuel": scoring_manuel_context,
            "scoring_sansbilan": {
                "title_17": _("SCORING ACREMAC - SANS BILAN"),
                "score_image": f"scoring/{score_indexe}.png",
                "score_png": f"scoring/{int(round(scoring_sans_bilan.scoring_value))}.png",
                "score_value": f"{scoring_sans_bilan.scoring_value:.2f}",  # <- toujours 2 décimales
                "interpretation": scoring_sans_bilan.interpretation,
                "commentaire": scoring_sans_bilan.commentaire,
                "score_indexe": score_indexe,
                "score_type": "Scoring sans bilan",
            },
            "scoring_classique": {
                "title_18": _("SCORING CLASSIQUE - AVEC BILAN"),
                "score_image_annee_N": f"scoring/{round(float(score_value_annee_N)) if score_value_annee_N else 0}.png",
                "score_value_annee_N": score_value_annee_N,
                "interpretation_annee_N": interpretation_annee_N,
                
                "score_image_annee_N1": f"scoring/{round(float(score_value_annee_N1)) if score_value_annee_N1 else 0}.png",
                "score_value_annee_N1": score_value_annee_N1,
                "interpretation_annee_N1": interpretation_annee_N1,
                
                "score_image_annee_N2": f"scoring/{round(float(score_value_annee_N2)) if score_value_annee_N2 else 0}.png",
                "score_value_annee_N2": score_value_annee_N2,
                "interpretation_annee_N2": interpretation_annee_N2,
            },
            "scoring_anglais": {
                "title_19": _("SCORING ANGLAIS - AVEC BILAN"),
                "score_image_annee_N": f"scoring/{round(float(score_value_anglais_annee_N)) if score_value_anglais_annee_N else 0}.png",
                "score_value_annee_N": score_value_anglais_annee_N,
                "interpretation_annee_N": interpretation_anglais_annee_N,
                "score_image_annee_N1": f"scoring/{round(float(score_value_anglais_annee_N1)) if score_value_anglais_annee_N1 else 0}.png",
                "score_value_annee_N1": score_value_anglais_annee_N1,
                "interpretation_annee_N1": interpretation_anglais_annee_N1,
                "score_image_annee_N2": f"scoring/{round(float(score_value_anglais_annee_N2)) if score_value_anglais_annee_N2 else 0}.png",
                "score_value_annee_N2": score_value_anglais_annee_N2,
                "interpretation_annee_N2": interpretation_anglais_anglais_annee_N2,
            },
            "scoring_bancaire": {
                "title_20": _("SCORING BANCAIRE - AVEC BILAN"),
                "score_image_annee_N": f"scoring/{round(float(score_value_bancaire_annee_N)) if score_value_bancaire_annee_N else 0}.png",
                "score_value_annee_N": score_value_bancaire_annee_N,
                "interpretation_annee_N": interpretation_bancaire_annee_N,
                "score_image_annee_N1": f"scoring/{round(float(score_value_bancaire_annee_N1)) if score_value_bancaire_annee_N1 else 0}.png",
                "score_value_annee_N1": score_value_bancaire_annee_N1,
                "interpretation_annee_N1": interpretation_bancaire_annee_N1,
                "score_image_annee_N2": f"scoring/{round(float(score_value_bancaire_annee_N2)) if score_value_bancaire_annee_N2 else 0}.png",
                "score_value_annee_N2": score_value_bancaire_annee_N2,
                "interpretation_annee_N2": interpretation_bancaire_annee_N2,
            },
            "scoring_syscohada": {
                "title_21": _("SCORING SYSCOHADA - AVEC BILAN"),
                "score_image_annee_N": f"scoring/{round(float(score_value_syscohada_annee_N)) if score_value_syscohada_annee_N else 0}.png",
                "score_value_annee_N": score_value_syscohada_annee_N,
                "interpretation_annee_N": interpretation_syscohada_annee_N,
                "score_image_annee_N1": f"scoring/{round(float(score_value_syscohada_annee_N1)) if score_value_syscohada_annee_N1 else 0}.png",
                "score_value_annee_N1": score_value_syscohada_annee_N1,
                "interpretation_annee_N1": interpretation_syscohada_annee_N1,
                "score_image_annee_N2": f"scoring/{round(float(score_value_syscohada_annee_N2)) if score_value_syscohada_annee_N2 else 0}.png",
                "score_value_annee_N2": score_value_syscohada_annee_N2,
                "interpretation_annee_N2": interpretation_syscohada_annee_N2,
            },
            "scoring_ifrs": {
                "title_22": _("SCORING IFRS COBAC - AVEC BILAN"),
                "score_image_annee_N": f"scoring/{round(float(score_value_ifrs_annee_N)) if score_value_ifrs_annee_N else 0}.png",
                "score_value_annee_N": score_value_ifrs_annee_N,
                "interpretation_annee_N": interpretation_ifrs_annee_N,
                "score_image_annee_N1": f"scoring/{round(float(score_value_ifrs_annee_N1)) if score_value_ifrs_annee_N1 else 0}.png",
                "score_value_annee_N1": score_value_ifrs_annee_N1,
                "interpretation_annee_N1": interpretation_ifrs_annee_N1,
                "score_image_annee_N2": f"scoring/{round(float(score_value_ifrs_annee_N2)) if score_value_ifrs_annee_N2 else 0}.png",
                "score_value_annee_N2": score_value_ifrs_annee_N2,
                "interpretation_annee_N2": interpretation_ifrs_annee_N2,
            },
            "scoring_rating": {
                "entries": scoring_rating_entries,
            },
            "scoring_delphi": scoring_delphi_ctx,

            "operation_history": {
                "title_23": _("HISTORIQUE DES OPERATIONS"),
                "commentaire_ratios": operation_history.commentaire_ratios if operation_history and operation_history.commentaire_ratios else "Aucun commentaire disponible",
                "description_complete_activite": operation_history.description_complete_activite if operation_history and operation_history.description_complete_activite else "Aucune description disponible",
                "importation": operation_history.importation if operation_history and operation_history.importation else "Non spécifié",
                "historique": operation_history.historique if operation_history and operation_history.historique else "Aucun historique disponible",
            },
            "properties_and_assets": {
                "title_24": _("PROPRIÉTÉ ET ACTIFS"),
                "assets_list": list_properties_and_assets_data if list_properties_and_assets_data else None,
            },
            "terms_of_purchase_and_sale": {
                "title_25": _("CONDITION D'ACHAT ET DE VENTE"),
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
            },
            "investigations": {
                "source1": "Tribunal de commerce (registre du commerce)",
                "source2": "Chambres de commerces et métiers",
                "source3": "Banques",
                "source4": "Groupement de sociétés",
                "source5": "La société a enquêté",
            },
            "copyright": {
                "assureur": "© ACREMAC",
                "note": "Nos renseignements sont confidentiels et ne peuvent être divulgues sous peine de dommages et intérêts. Acremac s'oblige à mettre en œuvre avec diligence les moyens dont elle dispose sans être tenue par des obligations de résultat.",
            }
        }
        
        _force_ratios_percent_display(report_data)
        print(report_data)
        logger.info(f"Récupération de report data {report_data}")

            
        # 3. Retourner le format demandé
        try:
            if format_report.upper() == 'PDF':
                print("Génération du PDF...")  # Debug
                # Rendre le template HTML
                html_string = render_to_string('main/report_acremac_template.html', report_data)
                
                # Générer le PDF en mémoire
                pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri('/static/')).write_pdf()
                
                # Préparer la réponse HTTP
                response = HttpResponse(pdf_file, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="rapport_solvabilite.pdf"'
                response['Content-Length'] = len(pdf_file)
                
                return response
            elif format_report.upper() == 'JSON':
                # Renvoyer le dictionnaire directement comme une réponse JSON pour inspection
                return Response(report_data, status=status.HTTP_200_OK)
            elif format_report.upper() == 'XML':
                logger.info("Génération du XML + XSD...")

                try:
                    response = generate_xml_with_xsd(report_data)
                    logger.info("XML + XSD généré avec succès")
                    return response

                except Exception as e:
                    logger.error(f"Erreur lors de la génération XML/XSD : {str(e)}")

                    error_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
                    <erreur>
                        <message>Erreur lors de la génération du rapport XML</message>
                        <details>{str(e)}</details>
                    </erreur>'''

                    response = HttpResponse(
                        error_xml, 
                        content_type='application/xml; charset=utf-8',
                        status=500
                    )
                    response['Content-Disposition'] = 'attachment; filename="rapport_erreur.xml"'
                    return response
            elif format_report.upper() == 'HTML':
                print("Génération du HTML...")  # Debug
                response = generate_html(report_data)
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






class GenerateReportCommandeAcheteur(APIView):
    def get(self, request, acheteur_id, id_commande, format_report, *args, **kwargs):
        
        
        # Récupération des paramètres
        id_commande_str = request.query_params.get('id_commande')
        language_report = request.query_params.get('language', 'fr')
        
        # 2. Définir les années et récupérer la devise
        current_year = dt.now().year
        years_to_retrieve = [current_year - 1, current_year - 2, current_year - 3]
        # N, N-1, N-2 : le plus récent en premier (years[0]=N, years[1]=N-1, years[2]=N-2)
        years_to_retrieve = sorted(years_to_retrieve, reverse=True)
        print(years_to_retrieve)
        
        # Variables
        acheteur = None
        compte_financier = None
        devise = None
        type_bilan = None
        bilan_report = None
        
        
        # Recuperation de l'acheteur
        try:
            acheteur = Acheteur.objects.get(pk=acheteur_id)
        except Acheteur.DoesNotExist:
            return {"error": f"Acheteur avec l'ID {acheteur_id} non trouvé."}
        
        # Get devise   
        try:
            compte_financier = CompteFinancier.objects.get(acheteur=acheteur)
            devise = compte_financier.devise if compte_financier else "N/A"
        except CompteFinancier.DoesNotExist:
            pass
        
        # Get type de bilan   
        try:
            compte_financier = CompteFinancier.objects.get(acheteur=acheteur)
            type_bilan = compte_financier.type_bilan if compte_financier else "N/A"
            bilan_report = compte_financier.type_bilan if compte_financier else "N/A"
        except CompteFinancier.DoesNotExist:
            pass
        
        
        
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
        # naf_codes = list(CodeNafAcheteur.objects.filter(acheteur=acheteur).values_list('code', flat=True))
        # nace_codes = list(CodeNaceAcheteur.objects.filter(acheteur=acheteur).values_list('code', flat=True))
        # Recuperation des codes NACE avec leurs libellés
        nace_codes_data = list(CodeNaceAcheteur.objects.filter(acheteur=acheteur)
            .select_related('code__category')
            .values('code__code', 'code__libelle', 'code__category__code', 'code__category__libelle')
            .distinct()
            .order_by('code__category__code', 'code__code'))

        nace_codes_formatted = []
        nace_by_cat: dict = {}
        for item in nace_codes_data:
            raw_code = item['code__code'] or ''
            display_code = raw_code.split('.', 1)[1] if '.' in raw_code else raw_code
            libelle = item['code__libelle'] or ''
            nace_codes_formatted.append(f"{display_code} - {libelle}" if libelle else display_code)
            cat_code = item['code__category__code'] or '—'
            cat_libelle = item['code__category__libelle'] or 'Non classifié'
            if cat_code not in nace_by_cat:
                nace_by_cat[cat_code] = {'cat_code': cat_code, 'cat_libelle': cat_libelle, 'codes': []}
            nace_by_cat[cat_code]['codes'].append({'code': display_code, 'libelle': libelle or '—'})
        nace_codes_grouped = list(nace_by_cat.values())

        # Recuperation des codes NAF avec leurs libellés
        naf_codes_data = list(CodeNafAcheteur.objects.filter(acheteur=acheteur)
            .select_related('code__category')
            .values('code__code', 'code__libelle', 'code__category__libelle')
            .distinct())

        # Formatage pour affichage
        naf_codes_formatted = []
        for item in naf_codes_data:
            if item['code__libelle']:
                naf_codes_formatted.append(f"{item['code__code']} - {item['code__libelle']}")
            else:
                naf_codes_formatted.append(item['code__code'])

        
        
        # Recuperation du resume en fonction de l'acheteur
        try:
            resume = Resume.objects.get(acheteur=acheteur)
        except Resume.DoesNotExist:
            resume = None
        
        # Recuperation de l'evaluation de risque de l'acheteur 
        # Recuperation de l'evaluation de risque chiffree de l'acheteur  
        risk_rating_value = 0
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
                risk_rating_value = min(risk_rating_value, 8)
            else:
                risk_rating = None
                
        except Exception as e:
            risk_rating = None
            risk_rating_value = 0
            
        
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

        # Recuperation des registres de commerce de l'acheteur
        registres = RegistreCommerce.objects.filter(acheteur=acheteur)
        list_registres_data = []
        for registre in registres:
            list_registres_data.append({
                "numero": registre.numero if registre.numero else "Non spécifié",
                "date_inscription": registre.date_inscription if registre.date_inscription else "Non spécifié",
                "est_actif": registre.est_actif if registre.est_actif else False,
                "commentaires": registre.commentaire if getattr(registre, "commentaire", None) else "Non spécifié",
            })
            
            
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
            
            
        # Recuperation des procedures collectives de l'acheteur
        procedures = ProcedureCollective.objects.filter(acheteur=acheteur)
        list_procedures_data = []
        for procedure in procedures:
            list_procedures_data.append({
                "type_procedure": (
                    getattr(procedure, "get_type_procedure_display", lambda: procedure.type_procedure)()
                    if procedure.type_procedure else "Non spécifié"
                ),
                "date_ouverture": procedure.date_ouverture if procedure.date_ouverture else "Non spécifié",
                "date_cloture": procedure.date_cloture if procedure.date_cloture else "Non spécifié",
                "tribunal": procedure.tribunal if procedure.tribunal else "Non spécifié",
                "numero_dossier": procedure.numero_dossier if procedure.numero_dossier else "Non spécifié",
                "secteur_activite": procedure.secteur_activite if procedure.secteur_activite else "Non spécifié",
                "description": procedure.description if procedure.description else "Non spécifié",
                "montant_creance": procedure.montant_creance if procedure.montant_creance else "Non spécifié",
                "impact_assureur": procedure.impact_assureur if procedure.impact_assureur else "Non spécifié",
                "commentaires": procedure.commentaire if getattr(procedure, "commentaire", None) else "Non spécifié",
            })
            
            
        # Recuperation des produits et services de l'acheteur
        produits_services = ProduitService.objects.filter(acheteur=acheteur)
        list_produits_services_data = []
        for produit_service in produits_services:
            list_produits_services_data.append({
                "produits": produit_service.produits if produit_service.produits else "Non spécifié",
                "services": produit_service.services if produit_service.services else "Non spécifié",
                "commentaires": produit_service.commentaire if getattr(produit_service, "commentaire", None) else "Non spécifié",
            })
            
            
        # Recuperation des marques de l'acheteur
        marques = Marque.objects.filter(acheteur=acheteur)
        list_marques_data = []
        for marque in marques:
            list_marques_data.append({
                "marques": marque.marques if marque.marques else "Non spécifié",
                "commentaires": marque.commentaire if getattr(marque, "commentaire", None) else "Non spécifié",
            })
            
            
        # Recuperation des certifications de l'acheteur
        certifications = Certification.objects.filter(acheteur=acheteur)
        list_certifications_data = []
        for certification in certifications:
            list_certifications_data.append({
                "type_certification": (
                    getattr(certification, "get_type_certification_display", lambda: certification.type_certification)()
                    if certification.type_certification else "Non spécifié"
                ),
                "nom_certification": certification.nom_certification if certification.nom_certification else "Non spécifié",
                "date_obtention": certification.date_obtention if certification.date_obtention else "Non spécifié",
                "organisme_delivreur": certification.organisme_delivreur if certification.organisme_delivreur else "Non spécifié",
                "description": certification.description if certification.description else "Non spécifié",
                "commentaires": certification.commentaire if getattr(certification, "commentaire", None) else "Non spécifié",
            })
            
            
        # Recuperation des innovations et developpements de l'acheteur
        innovations_developpements = InnovationDeveloppement.objects.filter(acheteur=acheteur)
        list_innovations_developpements_data = []
        for innovation_developpement in innovations_developpements:
            list_innovations_developpements_data.append({
                "type_innovation": (
                    getattr(innovation_developpement, "get_type_innovation_display", lambda: innovation_developpement.type_innovation)()
                    if innovation_developpement.type_innovation else "Non spécifié"
                ),
                "titre": innovation_developpement.titre if innovation_developpement.titre else "Non spécifié",
                "description": innovation_developpement.description if innovation_developpement.description else "Non spécifié",
                "date_debut": innovation_developpement.date_debut if innovation_developpement.date_debut else "Non spécifié",
                "date_fin": innovation_developpement.date_fin if innovation_developpement.date_fin else "Non spécifié",
                "commentaires": innovation_developpement.commentaire if getattr(innovation_developpement, "commentaire", None) else "Non spécifié",
            })
            
            
        # Recuperation des strategies et planifications de l'acheteur
        strategies_planifications = StrategiePlanification.objects.filter(acheteur=acheteur)
        list_strategies_planifications_data = []
        for strategie_planification in strategies_planifications:
            list_strategies_planifications_data.append({
                "type_strategie": (
                    getattr(strategie_planification, "get_type_strategie_display", lambda: strategie_planification.type_strategie)()
                    if strategie_planification.type_strategie else "Non spécifié"
                ),
                "description": strategie_planification.description if strategie_planification.description else "Non spécifié",
                "date_mise_en_place": strategie_planification.date_mise_en_place if strategie_planification.date_mise_en_place else "Non spécifié",
                "commentaires": strategie_planification.commentaire if getattr(strategie_planification, "commentaire", None) else "Non spécifié",
            })
            
            
        # Recuperation des conformites et reglementations de l'acheteur
        conformites_reglementations = ConformiteReglementation.objects.filter(acheteur=acheteur)
        list_conformites_reglementations_data = []
        for conformite_reglementation in conformites_reglementations:
            list_conformites_reglementations_data.append({
                "type_conformite": (
                    getattr(conformite_reglementation, "get_type_conformite_display", lambda: conformite_reglementation.type_conformite)()
                    if conformite_reglementation.type_conformite else "Non spécifié"
                ),
                "statut": conformite_reglementation.statut if conformite_reglementation.statut else "Non spécifié",
                "details_non_conformite": conformite_reglementation.details_non_conformite if conformite_reglementation.details_non_conformite else "Non spécifié",
                "date_verification": conformite_reglementation.date_verification if conformite_reglementation.date_verification else "Non spécifié",
                "organisme_controle": conformite_reglementation.organisme_controle if conformite_reglementation.organisme_controle else "Non spécifié",
                "commentaires": conformite_reglementation.commentaires if conformite_reglementation.commentaires else "Non spécifié",
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
        properties_and_assets = ProprieteEtActif.objects.filter(acheteur=acheteur).prefetch_related("locaux")
        list_properties_and_assets_data = []

        # 2. Bouclez sur les objets pour construire une liste de dictionnaires
        for prop_asset in properties_and_assets:
            locaux_labels = [str(local) for local in prop_asset.locaux.all()]
            list_properties_and_assets_data.append({
                "locaux": locaux_labels if locaux_labels else [],
                "branche": prop_asset.branche if prop_asset.branche else "",
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
        footer_3 = "moyens à sa disposition sans être liée par une obligation de résultat.."
            
            
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
        
        
        # Décodez et sauvegardez l'image si vous voulez la voir localement
        # with open(f"risk_gauge_score_{score_exemple}.png", "wb") as f:
        #     f.write(base64.b64decode(base64_image))
        # print(f"Image sauvegardée pour le score {score_exemple}")
        
        
        def format_currency(value):
            """Formate un nombre décimal en chaîne avec des séparateurs de milliers."""
            if value is None:
                return "Non spécifié"
            return f"{value:,.2f}".replace(",", " ").replace(".", ",") # Exemple de formatage français
        
        # 4. Appel à la fonction pour obtenir les données structurées des actifs
        actifs_table_data = get_simple_actifs_data(acheteur, years_to_retrieve)
        actifs_structured_data = get_structured_actif_data(acheteur, years_to_retrieve)
        passif_structured_data = get_structured_passif_data(acheteur, years_to_retrieve)
        resultat_structured_data = get_structured_resultat_data(acheteur, years_to_retrieve)
        ratios_structured_data = get_structured_ratios_data(acheteur, years_to_retrieve) 
        
        # NOUVEAU : Gérer la génération des graphiques
        # Dans la vue GenerateReport, après avoir récupéré les données financières :
        # ...
        # Récupérer les données pour les graphiques
        # actifs_by_year = {year: get_structured_actif_data(acheteur, [year])[0] for year in years_to_retrieve}
        # passifs_by_year = {year: get_structured_passif_data(acheteur, [year])[0] for year in years_to_retrieve}
        # ratios_by_year_dict = {year: get_structured_ratios_data(acheteur, [year])[0] for year in years_to_retrieve}

        # Générer les graphiques
        # charts_data = get_charts_data(actifs_by_year, passifs_by_year, ratios_by_year_dict, years_to_retrieve)

        # charts_data = {}
        
        # print(charts_data)
        
        # 2. Récupérer les données financières pour les années spécifiées
        actifs_by_year = {}
        resultats_by_year = {}
        ratios_by_year = {}

        for annee in years_to_retrieve:
            try:
                actif_instance = ActifC.objects.get(acheteur_id=acheteur_id, annee__annee=annee)
                resultat_instance = ResultatC.objects.get(acheteur_id=acheteur_id, annee__annee=annee)
                
                # Créez une instance de RatiosClassique pour chaque année
                # Remarque : Votre code initial n'avait pas de PassifC, mais le modèle RatiosClassique en a besoin
                # Supposons que vous ayez une instance de PassifC pour cette année aussi.
                try:
                    passif_instance = PassifC.objects.get(acheteur_id=acheteur_id, annee__annee=annee)
                except PassifC.DoesNotExist:
                    passif_instance = None # Ou créez une instance vide

                ratios_instance = RatiosClassique(actif_instance, passif_instance, resultat_instance)
                
                # Stocker les instances et leurs calculs
                actifs_by_year[annee] = actif_instance
                resultats_by_year[annee] = resultat_instance
                
                # Stocker les ratios calculés dans un dictionnaire
                ratios_by_year[annee] = {
                    'rentabilite_fin': ratios_instance.rentabilite_fin,
                    'solvabilite': ratios_instance.solvabilite,
                    'rendement_capitaux_propres': ratios_instance.rendement_capitaux_propres
                }
            except (ActifC.DoesNotExist, ResultatC.DoesNotExist):
                # Gérer le cas où les données pour une année sont manquantes
                continue
        
        # 3. Préparer les données pour les graphiques
        # Graphique de Structure Financière (Année N vs N-1)
        data_structure = {
            'labels': ['Actif Immobilisé', 'Actif Circulant', 'Total Actif'],
            'datasets': [
                {
                    'label': f'Année {years_to_retrieve[0]}',
                    'data': [
                        to_float(actifs_by_year.get(years_to_retrieve[0], ActifC()).total_I),
                        to_float(actifs_by_year.get(years_to_retrieve[0], ActifC()).total_II),
                        to_float(actifs_by_year.get(years_to_retrieve[0], ActifC()).general_total),
                    ]
                },
                {
                    'label': f'Année {years_to_retrieve[1]}',
                    'data': [
                        to_float(actifs_by_year.get(years_to_retrieve[1], ActifC()).total_I),
                        to_float(actifs_by_year.get(years_to_retrieve[1], ActifC()).total_II),
                        to_float(actifs_by_year.get(years_to_retrieve[1], ActifC()).general_total),
                    ]
                }
            ]
        }

        # Graphique de Rentabilité Financière (Année N-1 vs N-2)
        data_rentabilite = {
            'labels': ['Résultat Net', 'Chiffre d\'Affaires'],
            'datasets': [
                {
                    'label': f'Année {years_to_retrieve[1]}',
                    'data': [
                        to_float(resultats_by_year.get(years_to_retrieve[1], ResultatC()).resultat_exercice),
                        to_float(resultats_by_year.get(years_to_retrieve[1], ResultatC()).ca),
                    ]
                },
                {
                    'label': f'Année {years_to_retrieve[2]}',
                    'data': [
                        to_float(resultats_by_year.get(years_to_retrieve[2], ResultatC()).resultat_exercice),
                        to_float(resultats_by_year.get(years_to_retrieve[2], ResultatC()).ca),
                    ]
                }
            ]
        }


        # Calculer le score
        risk_score = risk_rating.calculate_risk_score() if risk_rating else 1

        # Générer l'image de la jauge en Base64
        risk_gauge_base64 = get_risk_gauge_chart(risk_score)
        
        
        # NOUVEAU: SCORING SANS BILAN
        # Recuperer le scoring sans bilan ici 
        scoring_sans_bilan = ScoringSansBilanAcheteur.objects.filter(acheteur=acheteur).first()
        scoring_manuel_context = build_scoring_manuel_context(acheteur, years_to_retrieve)
        print(scoring_sans_bilan)

        # par défaut
        score_indexe = 0
        scoring_context = None
        if scoring_sans_bilan:
            # Limiter le score entre 0 et 10 pour correspondre aux images
            try:
                score_indexe = int(round(scoring_sans_bilan.scoring_value or 0))
            except Exception:
                score_indexe = 0
            score_indexe = max(0, min(score_indexe, 10))
            print(int(round(scoring_sans_bilan.scoring_value or 0)))
            print(score_indexe)
            scoring_context = {
                "title_26": _("SCORING ACREMAC - SANS BILAN"),
                "score_image": f"scoring/{score_indexe}.png",
                "score_png": f"scoring/{score_indexe}.png",
                "score_value": f"{scoring_sans_bilan.scoring_value:.2f}" if scoring_sans_bilan.scoring_value is not None else "",
                "interpretation": scoring_sans_bilan.interpretation or "",
                "commentaire": scoring_sans_bilan.commentaire or "",
                "score_type": "Scoring sans bilan",
            }
        else:
            score_indexe = 0
        # NOUVEAU: SCORING AVEC BILAN CLASSIQUE
        # Scoring avec bilan classique
        # Récupérer le scoring avec bilan en fonction du type de bilan
        scoring_avec_bilan = None
        try:
            # Initialiser le scoring avec bilan
            scoring_generator = AcremacScoring(acheteur, bilan_report, current_year-1)
            scoring_result = scoring_generator.calculate_score_with_bilan()
            
            if scoring_result[0]:  # Si le calcul a réussi
                scoring_avec_bilan_data = scoring_result[0]
                score_avec_bilan = scoring_avec_bilan_data['score']
                
                # Limiter le score entre 0 et 10 pour correspondre aux images
                score_index_avec_bilan = int(round(score_avec_bilan))
                score_index_avec_bilan = max(0, min(score_index_avec_bilan, 10))
                
                scoring_avec_bilan = {
                    'score_image': f"scoring/{score_index_avec_bilan}.png",
                    'score_value': f"{score_avec_bilan:.2f}",
                    'interpretation': scoring_generator.get_score_interpretation(score_avec_bilan),
                    'commentaire': f"Score calculé avec les données du bilan {bilan_report}",
                    'details': scoring_avec_bilan_data.get('details', [])
                }
            else:
                scoring_avec_bilan = {
                    'score_image': "scoring/1.png",
                    'score_value': "N/A",
                    'interpretation': "Calcul impossible - données manquantes",
                    'commentaire': f"Impossible de calculer le score avec le bilan {bilan_report}",
                    'details': []
                }
        except Exception as e:
            print(f"Erreur lors du calcul du scoring avec bilan: {e}")
            scoring_avec_bilan = None

        
        
        
        # 4. Générer les graphiques en Base64
        charts_data = {
            'structure_financiere': get_base64_chart2(
                data_structure,
                "Structure Financière (Année N vs N-1)",
                "Montant en FCFA",
                chart_type='bar'
            ),
            'rentabilite_financiere': get_base64_chart2(
                data_rentabilite,
                "Rentabilité Financière (Année N-1 vs N-2)",
                "Montant en FCFA",
                chart_type='bar'
            )
        }

        # NOUVEAU: SCORING AVEC BILAN CLASSIQUE
        # Scoring avec bilan classique
        # Récupérer le scoring avec bilan en fonction du type de bilan
        # Calculer le scoring pour chaque année
        for i, year in enumerate(years_to_retrieve):
            annee_label = f"annee_N{i}" if i == 0 else f"annee_N{i+1}"[-2:]
            donnees_bilan = ScoreACREMACBilanClassiqueService.extraire_donnees_bilan_classique(acheteur, year)

            if donnees_bilan:
                resultat_calcul = ScoreACREMACBilanClassiqueService.calculer_score_complet(donnees_bilan)
                score = resultat_calcul['score']
                score_index = round(score)
                classe_risque = resultat_calcul['classe_risque']

                # Mettre à jour les variables de score
                if i == 0:
                    score_value_annee_N = str(score)
                    interpretation_annee_N = classe_risque
                elif i == 1:
                    score_value_annee_N1 = str(score)
                    interpretation_annee_N1 = classe_risque
                elif i == 2:
                    score_value_annee_N2 = str(score)
                    interpretation_annee_N2 = classe_risque


        # NOUVEAU: SCORING AVEC BILAN ANGLAIS
        # Scoring avec bilan anglais
        # Initialisation des scores par année pour le bilan anglais
        score_value_anglais_annee_N = None
        score_value_anglais_annee_N1 = None
        score_value_anglais_annee_N2 = None
        interpretation_anglais_annee_N = "N/A"
        interpretation_anglais_annee_N1 = "N/A"
        interpretation_anglais_annee_N2 = "N/A"
        # Calculer le scoring anglais pour chaque année
        for i, year in enumerate(years_to_retrieve):
            annee_label = f"annee_N{i}" if i == 0 else f"annee_N{i+1}"[-2:]
            donnees_bilan_anglais = ScoreACREMACBilanAnglaisService.extraire_donnees_bilan_anglais(acheteur, year)

            if donnees_bilan_anglais:
                resultat_calcul_anglais = ScoreACREMACBilanAnglaisService.calculer_score_complet(donnees_bilan_anglais)
                score_anglais = resultat_calcul_anglais['score']
                score_index_anglais = round(score_anglais)
                classe_risque_anglais = resultat_calcul_anglais['classe_risque']

                # Mettre à jour les variables de score anglais
                if i == 0:
                    score_value_anglais_annee_N = str(score_anglais)
                    interpretation_anglais_annee_N = classe_risque_anglais
                elif i == 1:
                    score_value_anglais_annee_N1 = str(score_anglais)
                    interpretation_anglais_annee_N1 = classe_risque_anglais
                elif i == 2:
                    score_value_anglais_annee_N2 = str(score_anglais)
                    interpretation_anglais_anglais_annee_N2 = classe_risque_anglais



        # NOUVEAU: SCORING AVEC BILAN BANCAIRE
        # Scoring avec bilan bancaire
        # Initialisation des scores par année pour le bilan bancaire
        score_value_bancaire_annee_N = None
        score_value_bancaire_annee_N1 = None
        score_value_bancaire_annee_N2 = None
        interpretation_bancaire_annee_N = "N/A"
        interpretation_bancaire_annee_N1 = "N/A"
        interpretation_bancaire_annee_N2 = "N/A"
        # Calculer le scoring bancaire pour chaque année
        for i, year in enumerate(years_to_retrieve):
            annee_label = f"annee_N{i}" if i == 0 else f"annee_N{i+1}"[-2:]
            donnees_bilan_bancaire = ScoreACREMACBilanBancaireService.extraire_donnees_bilan_bancaire(acheteur, year, bilan_type="annuel")

            if donnees_bilan_bancaire:
                resultat_calcul_bancaire = ScoreACREMACBilanBancaireService.calculer_score_complet_bancaire(donnees_bilan_bancaire)
                score_bancaire = resultat_calcul_bancaire['score']
                score_index_bancaire = round(score_bancaire)
                classe_risque_bancaire = resultat_calcul_bancaire['classe_risque']

                # Mettre à jour les variables de score bancaire
                if i == 0:
                    score_value_bancaire_annee_N = str(score_bancaire)
                    interpretation_bancaire_annee_N = classe_risque_bancaire
                elif i == 1:
                    score_value_bancaire_annee_N1 = str(score_bancaire)
                    interpretation_bancaire_annee_N1 = classe_risque_bancaire
                elif i == 2:
                    score_value_bancaire_annee_N2 = str(score_bancaire)
                    interpretation_bancaire_annee_N2 = classe_risque_bancaire
            


        # NOUVEAU: SCORING AVEC BILAN SYSCOHADA
        # Scoring avec bilan syscohada
        # Initialisation des scores par année pour le bilan syscohada
        # Initialisation des scores par année pour le bilan SYSCOHADA
        score_value_syscohada_annee_N = None
        score_value_syscohada_annee_N1 = None
        score_value_syscohada_annee_N2 = None
        interpretation_syscohada_annee_N = "N/A"
        interpretation_syscohada_annee_N1 = "N/A"
        interpretation_syscohada_annee_N2 = "N/A"
        # Calculer le scoring SYSCOHADA pour chaque année
        for i, year in enumerate(years_to_retrieve):
            annee_label = f"annee_N{i}" if i == 0 else f"annee_N{i+1}"[-2:]
            donnees_bilan_syscohada = ScoreACREMACBilanSyscohadaService.extraire_donnees_bilan_syscohada(acheteur, year)

            if donnees_bilan_syscohada:
                resultat_calcul_syscohada = ScoreACREMACBilanSyscohadaService.calculer_score_complet_syscohada(donnees_bilan_syscohada)
                score_syscohada = resultat_calcul_syscohada['score']
                score_index_syscohada = round(score_syscohada)
                classe_risque_syscohada = resultat_calcul_syscohada['classe_risque']

                # Mettre à jour les variables de score SYSCOHADA
                if i == 0:
                    score_value_syscohada_annee_N = str(score_syscohada)
                    interpretation_syscohada_annee_N = classe_risque_syscohada
                elif i == 1:
                    score_value_syscohada_annee_N1 = str(score_syscohada)
                    interpretation_syscohada_annee_N1 = classe_risque_syscohada
                elif i == 2:
                    score_value_syscohada_annee_N2 = str(score_syscohada)
                    interpretation_syscohada_annee_N2 = classe_risque_syscohada




        # NOUVEAU: SCORING AVEC BILAN IFRS COBAC
        # Scoring avec bilan Ifrs Cobac
        # Initialisation des scores par année pour le bilan IFRS COBAC
        score_value_ifrs_annee_N = None
        score_value_ifrs_annee_N1 = None
        score_value_ifrs_annee_N2 = None
        interpretation_ifrs_annee_N = "N/A"
        interpretation_ifrs_annee_N1 = "N/A"
        interpretation_ifrs_annee_N2 = "N/A"
        # Calculer le scoring IFRS COBAC pour chaque année
        for i, year in enumerate(years_to_retrieve):
            annee_label = f"annee_N{i}" if i == 0 else f"annee_N{i+1}"[-2:]
            donnees_bilan_ifrs = ScoreACREMACBilanIFRSService.extraire_donnees_bilan_ifrs(acheteur, year)

            if donnees_bilan_ifrs:
                resultat_calcul_ifrs = ScoreACREMACBilanIFRSService.calculer_score_complet_ifrs(donnees_bilan_ifrs)
                score_ifrs = resultat_calcul_ifrs['score']
                score_index_ifrs = round(score_ifrs)
                classe_risque_ifrs = resultat_calcul_ifrs['classe_risque']

                # Mettre à jour les variables de score IFRS COBAC
                if i == 0:
                    score_value_ifrs_annee_N = str(score_ifrs)
                    interpretation_ifrs_annee_N = classe_risque_ifrs
                elif i == 1:
                    score_value_ifrs_annee_N1 = str(score_ifrs)
                    interpretation_ifrs_annee_N1 = classe_risque_ifrs
                elif i == 2:
                    score_value_ifrs_annee_N2 = str(score_ifrs)
                    interpretation_ifrs_annee_N2 = classe_risque_ifrs


        


        # ACREMAC Rating Score et Delphi Score
        scorings_rating_qs = ScoringRating.objects.filter(acheteur=acheteur).select_related('annee').order_by('-annee__annee')
        scoring_rating_entries = []
        for sr in scorings_rating_qs:
            sv = float(sr.score_final) if sr.score_final is not None else None
            scoring_rating_entries.append({
                "annee": str(sr.annee) if sr.annee else "",
                "score_final": f"{sv:.2f}" if sv is not None else "-",
                "rating": sr.rating or "-",
                "classe_risque": sr.classe_risque or "-",
                "decision": sr.decision or "-",
                "red_flag": sr.red_flag,
                "commentaire": sr.commentaire or "",
            })
        try:
            _sd = ScoringDelphi.objects.get(acheteur=acheteur)
            scoring_delphi_ctx = {
                "score_delphi": _sd.score_delphi if _sd.score_delphi is not None else "-",
                "bande": _sd.bande or "-",
                "etoiles": _sd.etoiles if _sd.etoiles is not None else "-",
                "niveau_risque": _sd.niveau_risque or "-",
                "commentaire": _sd.commentaire or "",
            }
        except ScoringDelphi.DoesNotExist:
            scoring_delphi_ctx = None

        telephones_acheteur = list(
            TelephoneAcheteur.objects.filter(acheteur=acheteur)
            .exclude(telephone__isnull=True)
            .exclude(telephone__exact="")
            .values("telephone", "nom")
            .distinct()
        )
        portables_acheteur = list(
            PortableAcheteur.objects.filter(acheteur=acheteur)
            .exclude(portable__isnull=True)
            .exclude(portable__exact="")
            .values("portable", "nom")
            .distinct()
        )
        emails_acheteur = list(
            EmailAcheteur.objects.filter(acheteur=acheteur)
            .exclude(email__isnull=True)
            .exclude(email__exact="")
            .values("email", "description")
            .distinct()
        )
        adresses_acheteur = list(
            AdresseAcheteur.objects.filter(acheteur=acheteur)
            .exclude(adresse__isnull=True)
            .exclude(adresse__exact="")
            .values_list("adresse", flat=True)
            .distinct()
        )

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
                "bilan_report": bilan_report.upper() if bilan_report else "",
                "format_report": format_report,
                "date_today": dt.now().strftime("%d/%m/%Y %H:%M:%S"),
            },
            "footer_report": {
                "footer_text_1": footer_1,
                "footer_text_2": footer_2,
                "footer_text_3": footer_3,
            },
            "commande": {
                "title_1": _("DETAILS COMMANDE"),
                "client": commande.client.username if hasattr(commande, 'client') and commande.client else "Non spécifié",
                "ref_client": commande.reference_client if hasattr(commande, 'reference_client') else "Non spécifié",
                "notre_ref": commande.notre_ref if hasattr(commande, 'notre_ref') else "Non spécifié",
                "date_recept_commande": commande.date_recept_commande.strftime("%d/%m/%Y") if hasattr(commande, 'date_recept_commande') and commande.date_recept_commande else "Non spécifié",
                "date_rapport": commande.date_rapport.strftime("%d/%m/%Y") if hasattr(commande, 'date_rapport') and commande.date_rapport else "Non spécifié",
                "delais": commande.delais if hasattr(commande, 'delais') else "Non spécifié",
                "priorite": commande.priorite if hasattr(commande, 'priorite') else "Non spécifié",
                "type_rapport": commande.type_rapport if hasattr(commande, 'type_rapport') else "Non spécifié"
            },
            "identification": {
                "title_2": _("IDENTIFICATION"),
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
                    "province": acheteur.province.nom if hasattr(acheteur, 'province') and acheteur.province else "Non spécifié",
                    "ville": acheteur.ville.nom if hasattr(acheteur, 'ville') and acheteur.ville else "Non spécifié",
                    "region": acheteur.region.nom if hasattr(acheteur, 'region') and acheteur.region else "",
                    "fax": acheteur.fax if hasattr(acheteur, 'fax') else "Non spécifié",
                    "telephone": telephones_acheteur[0]["telephone"] if telephones_acheteur else (acheteur.telephone if hasattr(acheteur, 'telephone') and acheteur.telephone else "Non spécifié"),
                    "telephones": telephones_acheteur,
                    "portables": portables_acheteur,
                    "emails_secondaires": emails_acheteur,
                    "adresses_secondaires": adresses_acheteur,
                    "numero_adresse": acheteur.numero_adresse if hasattr(acheteur, 'numero_adresse') else "Non spécifié",
                    "code_postal": acheteur.code_postal if hasattr(acheteur, 'code_postal') else "Non spécifié",
                }
            },
            "additional_information": {
                "title_3": _("INFORMATIONS SUPPLEMENTAIRES"),
                "site_internet": acheteur.site_internet if hasattr(acheteur, 'site_internet') else "Non spécifié",
                "forme_juridique": acheteur.forme_juridique.libelle if hasattr(acheteur, 'forme_juridique') else "Non spécifié",
                "activite_principale": acheteur.activite_principale if hasattr(acheteur, 'activite_principale') else "Non spécifié",
                "description": acheteur.description if hasattr(acheteur, 'description') else "Non spécifié",
                "statut_entreprise": acheteur.statut_entreprise.libelle if hasattr(acheteur, 'statut_entreprise') else "Non spécifié",
                "date_creation": acheteur.date_creation.strftime("%d/%m/%Y") if hasattr(acheteur, 'date_creation') and acheteur.date_creation else "Non spécifié",
                "nace_codes": nace_codes_formatted if nace_codes_formatted else ["Aucun code NACE disponible"],
                "nace_codes_grouped": nace_codes_grouped if nace_codes_grouped else [],
                "naf_codes": naf_codes_formatted if naf_codes_formatted else ["Aucun code NAF disponible"],
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
                "title_4": _("RESUME EXECUTIF"),
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
                "title_5": _("EVALUATION DU RISQUE"),
                # Utiliser la chaîne Base64 pour l'affichage de la jauge
                "risk_gauge_base64": risk_gauge_base64,
                "risk_rating_image_base64": (
                    get_risk_rating_png_base64(risk_rating_value)
                    or (risk_rating.get_risk_rating_image_base64() if risk_rating else None)
                ),
                #"get_risk_gauge_image": get_risk_gauge_image,
                "risk_gauge_base64": risk_gauge_base64,
                "risk_rating_value": max(0, min(8, int(risk_rating_value or 0))),
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
                "title_6": _("AVIS CREDIT ACREMAC"),
                # Passez le dictionnaire directement au template
                "notes": notes_str, # Passez la chaîne formatée au template
                "highlighted_risks": highlighted_risks,
                "montant_credit_maximum": acremac_opinion.montant_credit_maximum if acremac_opinion else "Non spécifié",
                "commentaire": acremac_opinion.commentaire if acremac_opinion else "Aucun commentaire disponible",
            },
            "registered_data": {
                "title_7": _("DONNEES D'ENREGISTREMENT"),
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
                "title_8": _("ANTECEDENTS JURIDIQUES"),
                "antecedents_juridiques": list_antecedants_data if list_antecedants_data else [],
            },
            "management": {
                "title_9": _("MANAGEMENT DU RISQUE"),
                "risk_management": {
                    "professionalisme": risk_management.professionalisme if risk_management and risk_management.professionalisme else "Non spécifié",
                    "organisation": risk_management.organisation if risk_management and risk_management.organisation else "Non spécifié",
                    "turn_over": risk_management.turn_over if risk_management and risk_management.turn_over else "Non spécifié",
                    "greve": risk_management.greve if risk_management and risk_management.greve else "Non spécifié",
                    "degradation_qualite": risk_management.degradation_qualite if risk_management and risk_management.degradation_qualite else "Non spécifié",
                    "non_respect_condition": risk_management.non_respect_condition if risk_management and risk_management.non_respect_condition else "Non spécifié",
                    "commentaire": risk_management.commentaire if risk_management and risk_management.commentaire else "Aucun commentaire disponible",
                    "score": risk_management.get_management_score()['oui_count'] if risk_management else 0,
                    "image": risk_management.get_management_image_path_report() if risk_management else "management/passable.png",
                },
                "responsables": list_responsables_data if list_responsables_data else "Aucun responsable disponible",
                "conseil_administration": list_ca_membres_data if list_ca_membres_data else "Aucun membre du conseil d'administration disponible",
            },
            "capital_composition": {
                "title_10": _("COMPOSITION DU CAPITAL"),
                "emis": format_currency(composition_capital_social.emis) if composition_capital_social else "Non spécifié",
                "publie": format_currency(composition_capital_social.publie) if composition_capital_social else "Non spécifié",
                "libere": format_currency(composition_capital_social.libere) if composition_capital_social else "Non spécifié",
                "devise": composition_capital_social.devise.code if composition_capital_social and composition_capital_social.devise else "Non spécifié",
                "commentaire": composition_capital_social.commentaire if composition_capital_social and composition_capital_social.commentaire else "Aucun commentaire disponible",
            },
            "shareholders": {
                "title_11": _("ACTIONNARIAT/PROPRIETAIRES"),
                "actionnaires": list_shareholders_data if list_shareholders_data else [],
            },
            # Nouveaux elements
            "registres": {
                "title_12": _("REGISTRES DE COMMERCE"),
                "registres": list_registres_data if list_registres_data else [],
            },
            "produits_services": {
                "title_13": _("PRODUITS & SERVICES"),
                "produits": list_produits_services_data if list_produits_services_data else [],
            },
            "marques": {
                "title_14": _("MARQUES"),
                "marques": list_marques_data if list_marques_data else [],
            },
            "procedures_collectives": {
                "title_15": _("PROCEDURES & COLLECTIVES"),
                "procedures_collectives": list_procedures_data if list_procedures_data else [],
            },
            "certifications": {
                "title_17": _("CERTIFICATIONS"),
                "certifications": list_certifications_data if list_certifications_data else [],
            },
            "innovations_developpements": {
                "title_18": _("INNOVATIONS & DEVELOPPEMENT"),
                "innovations_developpements": list_innovations_developpements_data if list_innovations_developpements_data else [],
            },
            "strategies_planifications": {
                "title_19": _("STRATEGIES & PLANIFICATIONS"),
                "strategies_planifications": list_strategies_planifications_data if list_strategies_planifications_data else [],
            },
            "conformitesy": {
                "title_20": _("CONFORMITE REGLEMENTATION"),
                "strategies_planifications": list_strategies_planifications_data if list_strategies_planifications_data else [],
            },
            
            
            "affiliations": {
                "title_21": _("AFFILIATIONS CORPORATIVES"),
                "affiliations": list_affiliations_data if list_affiliations_data else [],
            },
            "sector_analysis": {
                "title_22": _("ANALYSE ECONOMIQUE"),
                "nace_codes": nace_codes_formatted if nace_codes_formatted else ["Aucun code NACE disponible"],
                "nace_codes_grouped": nace_codes_grouped if nace_codes_grouped else [],
                "naf_codes": naf_codes_formatted if naf_codes_formatted else ["Aucun code NAF disponible"],
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
                    "title_advice": _("CONSEILS D'ACREMAC"),
                    "forces": advice.forces if advice and advice.forces else "",
                    "faiblesses": advice.faiblesses if advice and advice.faiblesses else "",
                    "opportunites": advice.opportunites if advice and advice.opportunites else "",
                    "dynamisme_long_terme": advice.dynamisme_long_terme if advice and advice.dynamisme_long_terme else "",
                    "menaces": advice.menaces if advice and advice.menaces else "",
                },
                "geopolitics": {
                    "donnees_politiques": geopolitics.donnees_politiques if geopolitics and geopolitics.donnees_politiques else "Non spécifié",
                    "donnees_economiques": geopolitics.donnees_economiques if geopolitics and geopolitics.donnees_economiques else "Non spécifié",
                },
            },
            "advice": {
                "title_advice": _("CONSEILS D'ACREMAC"),
                "forces": advice.forces if advice and advice.forces else "",
                "faiblesses": advice.faiblesses if advice and advice.faiblesses else "",
                "opportunites": advice.opportunites if advice and advice.opportunites else "",
                "dynamisme_long_terme": advice.dynamisme_long_terme if advice and advice.dynamisme_long_terme else "",
                "menaces": advice.menaces if advice and advice.menaces else "",
            },
            "banking_data": {
                "title_23": _("DONNEES BANCAIRES"),
                "data_banks": list_banking_data if list_banking_data else [],
            },

            "financial_accounts": {
                "title_24": _("COMPTES FINANCIERS"),
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
                "title_25": _("ETATS FINANCIERS"),
                "years": years_to_retrieve,
                "bilan_type": bilan_report,
                "etats_financiers_classiques": {
                    "actif_table": actifs_table_data,
                    "actif_data": actifs_structured_data,
                    "passif_data": passif_structured_data,
                    "resultat_data": resultat_structured_data,
                    "ratios_data": ratios_structured_data,
                    "charts_data_v1": charts_data,
                    "charts_data": {
                        "charts_structure_financiere": get_charts_structure_financiere_data(acheteur, years_to_retrieve, chart_type='bar'),
                        "charts_rentabilite_financiere": get_charts_rentabilite_financiere_data(acheteur, years_to_retrieve, chart_type='bar'),
                        "charts_delais": get_charts_delais_data(acheteur, years_to_retrieve, chart_type='bar'),
                    },
                },
                "etats_financiers_anglais": {
                    "actif_data": get_structured_actif_anglais_data(acheteur, years_to_retrieve),
                    "passif_data": get_structured_passif_anglais_data(acheteur, years_to_retrieve),
                    "resultat_data": get_structured_resultat_anglais_data(acheteur, years_to_retrieve),
                    "ratios_data": get_structured_ratios_anglais_data(acheteur, years_to_retrieve),
                    "charts_data": {
                        "charts_structure_financiere": get_charts_structure_financiere_anglais_data(acheteur, years_to_retrieve),
                        "charts_rentabilite_financiere": get_charts_rentabilite_financiere_anglais_data(acheteur, years_to_retrieve),
                        "charts_delais": get_charts_delais_anglais_data(acheteur, years_to_retrieve),
                    },
                },
                "etats_financiers_bancaires": {
                    "actif_data": get_structured_actif_bancaire_data(acheteur, years_to_retrieve),
                    "passif_data": get_structured_passif_bancaire_data(acheteur, years_to_retrieve),
                    "produit_data": get_structured_produit_bancaire_data(acheteur, years_to_retrieve),
                    "depense_data": get_structured_depense_bancaire_data(acheteur, years_to_retrieve),
                    "hors_bilan_data": get_structured_hors_bilan_bancaire_data(acheteur, years_to_retrieve),
                    "ratios_data": get_structured_ratios_bancaire_data(acheteur, years_to_retrieve),
                    "charts_data": {
                        "charts_structure_financiere": get_charts_structure_financiere_bancaire_data(acheteur, years_to_retrieve),
                        "charts_rentabilite_financiere": get_charts_rentabilite_bancaire_data(acheteur, years_to_retrieve),
                        "charts_delais": get_charts_ratios_bancaire_data(acheteur, years_to_retrieve),
                    },
                },
                "etats_financiers_syscohada": {
                    "actif_data": get_structured_actif_syscohada_data(acheteur, years_to_retrieve),
                    "passif_data": get_structured_passif_syscohada_data(acheteur, years_to_retrieve),
                    "resultat_data": get_structured_resultat_syscohada_data(acheteur, years_to_retrieve),
                    "ratios_data": get_structured_ratios_syscohada_data(acheteur, years_to_retrieve),
                    "charts_data": {
                        "charts_structure_financiere": get_charts_structure_financiere_syscohada_data(acheteur, years_to_retrieve),
                        "charts_rentabilite_financiere": get_charts_rentabilite_financiere_syscohada_data(acheteur, years_to_retrieve),
                        "charts_delais": get_charts_delais_syscohada_data(acheteur, years_to_retrieve),
                    },
                },
                "etats_financiers_irfs_cobac": {
                    "actif_data": get_structured_actif_ifrs_data(acheteur, years_to_retrieve),
                    "passif_data": get_structured_passif_ifrs_data(acheteur, years_to_retrieve),
                    "resultat_data": get_structured_resultat_ifrs_data(acheteur, years_to_retrieve),
                    "ratios_data": get_structured_ratios_ifrs_data(acheteur, years_to_retrieve),
                    "charts_data": {
                        "charts_structure_financiere": get_charts_structure_financiere_ifrs_data(acheteur, years_to_retrieve),
                        "charts_rentabilite_financiere": get_charts_rentabilite_financiere_ifrs_data(acheteur, years_to_retrieve),
                        "charts_delais": get_charts_delais_ifrs_data(acheteur, years_to_retrieve),
                    },
                },

            },
            
            "translations": {},
            "scoring": scoring_context,
            "scoring_manuel": scoring_manuel_context,
            "scoring_classique": {
                "title_26": _("SCORING CLASSIQUE - AVEC BILAN"),
                "score_image_annee_N": f"scoring/{round(float(score_value_annee_N)) if score_value_annee_N else 0}.png",
                "score_value_annee_N": score_value_annee_N,
                "interpretation_annee_N": interpretation_annee_N,
                "score_image_annee_N1": f"scoring/{round(float(score_value_annee_N1)) if score_value_annee_N1 else 0}.png",
                "score_value_annee_N1": score_value_annee_N1,
                "interpretation_annee_N1": interpretation_annee_N1,
                "score_image_annee_N2": f"scoring/{round(float(score_value_annee_N2)) if score_value_annee_N2 else 0}.png",
                "score_value_annee_N2": score_value_annee_N2,
                "interpretation_annee_N2": interpretation_annee_N2,
            },
            "scoring_anglais": {
                "title_27": _("SCORING ANGLAIS - AVEC BILAN"),
                "score_image_annee_N": f"scoring/{round(float(score_value_anglais_annee_N)) if score_value_anglais_annee_N else 0}.png",
                "score_value_annee_N": score_value_anglais_annee_N,
                "interpretation_annee_N": interpretation_anglais_annee_N,
                "score_image_annee_N1": f"scoring/{round(float(score_value_anglais_annee_N1)) if score_value_anglais_annee_N1 else 0}.png",
                "score_value_annee_N1": score_value_anglais_annee_N1,
                "interpretation_annee_N1": interpretation_anglais_annee_N1,
                "score_image_annee_N2": f"scoring/{round(float(score_value_anglais_annee_N2)) if score_value_anglais_annee_N2 else 0}.png",
                "score_value_annee_N2": score_value_anglais_annee_N2,
                "interpretation_annee_N2": interpretation_anglais_anglais_annee_N2,
            },
            "scoring_bancaire": {
                "title_28": _("SCORING BANCAIRE - AVEC BILAN"),
                "score_image_annee_N": f"scoring/{round(float(score_value_bancaire_annee_N)) if score_value_bancaire_annee_N else 0}.png",
                "score_value_annee_N": score_value_bancaire_annee_N,
                "interpretation_annee_N": interpretation_bancaire_annee_N,
                "score_image_annee_N1": f"scoring/{round(float(score_value_bancaire_annee_N1)) if score_value_bancaire_annee_N1 else 0}.png",
                "score_value_annee_N1": score_value_bancaire_annee_N1,
                "interpretation_annee_N1": interpretation_bancaire_annee_N1,
                "score_image_annee_N2": f"scoring/{round(float(score_value_bancaire_annee_N2)) if score_value_bancaire_annee_N2 else 0}.png",
                "score_value_annee_N2": score_value_bancaire_annee_N2,
                "interpretation_annee_N2": interpretation_bancaire_annee_N2,
            },
            "scoring_syscohada": {
                "title_29": _("SCORING SYSCOHADA - AVEC BILAN"),
                "score_image_annee_N": f"scoring/{round(float(score_value_syscohada_annee_N)) if score_value_syscohada_annee_N else 0}.png",
                "score_value_annee_N": score_value_syscohada_annee_N,
                "interpretation_annee_N": interpretation_syscohada_annee_N,
                "score_image_annee_N1": f"scoring/{round(float(score_value_syscohada_annee_N1)) if score_value_syscohada_annee_N1 else 0}.png",
                "score_value_annee_N1": score_value_syscohada_annee_N1,
                "interpretation_annee_N1": interpretation_syscohada_annee_N1,
                "score_image_annee_N2": f"scoring/{round(float(score_value_syscohada_annee_N2)) if score_value_syscohada_annee_N2 else 0}.png",
                "score_value_annee_N2": score_value_syscohada_annee_N2,
                "interpretation_annee_N2": interpretation_syscohada_annee_N2,
            },
            "scoring_ifrs": {
                "title_30": _("SCORING IFRS COBAC - AVEC BILAN"),
                "score_image_annee_N": f"scoring/{round(float(score_value_ifrs_annee_N)) if score_value_ifrs_annee_N else 0}.png",
                "score_value_annee_N": score_value_ifrs_annee_N,
                "interpretation_annee_N": interpretation_ifrs_annee_N,
                "score_image_annee_N1": f"scoring/{round(float(score_value_ifrs_annee_N1)) if score_value_ifrs_annee_N1 else 0}.png",
                "score_value_annee_N1": score_value_ifrs_annee_N1,
                "interpretation_annee_N1": interpretation_ifrs_annee_N1,
                "score_image_annee_N2": f"scoring/{round(float(score_value_ifrs_annee_N2)) if score_value_ifrs_annee_N2 else 0}.png",
                "score_value_annee_N2": score_value_ifrs_annee_N2,
                "interpretation_annee_N2": interpretation_ifrs_annee_N2,
            },
            "scoring_rating": {
                "entries": scoring_rating_entries,
            },
            "scoring_delphi": scoring_delphi_ctx,

            "operation_history": {
                "title_31": _("HISTORIQUE DES OPERATIONS"),
                "commentaire_ratios": operation_history.commentaire_ratios if operation_history and operation_history.commentaire_ratios else "Aucun commentaire disponible",
                "description_complete_activite": operation_history.description_complete_activite if operation_history and operation_history.description_complete_activite else "Aucune description disponible",
                "importation": operation_history.importation if operation_history and operation_history.importation else "Non spécifié",
                "historique": operation_history.historique if operation_history and operation_history.historique else "Aucun historique disponible",
            },
            "properties_and_assets": {
                "title_32": _("PROPRIÉTÉ ET ACTIFS"),
                "assets_list": list_properties_and_assets_data if list_properties_and_assets_data else None,
            },
            "terms_of_purchase_and_sale": {
                "title_33": _("CONDITION D'ACHAT ET DE VENTE"),
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
            },
            "investigations": {
                "source1": "Tribunal de commerce (registre du commerce)",
                "source2": "Chambres de commerces et métiers",
                "source3": "Banques",
                "source4": "Groupement de sociétés",
                "source5": "La société a enquêté",
            },
            "copyright": {
                "assureur": "© ACREMAC",
                "note": "Nos renseignements sont confidentiels et ne peuvent être divulgues sous peine de dommages et intérêts. Acremac s'oblige à mettre en œuvre avec diligence les moyens dont elle dispose sans être tenue par des obligations de résultat.",
            }
        }
        
        # fallback: ensure scoring_context exists or has a value
        if "scoring_context" not in locals() or scoring_context is None:
            if scoring_sans_bilan:
                score_indexe = score_indexe if score_indexe is not None else 0
                scoring_context = {
                    "title_26": _("SCORING ACREMAC - SANS BILAN"),
                    "score_image": f"scoring/{score_indexe}.png",
                    "score_png": f"scoring/{score_indexe}.png",
                    "score_value": f"{scoring_sans_bilan.scoring_value:.2f}" if scoring_sans_bilan.scoring_value is not None else "",
                    "interpretation": scoring_sans_bilan.interpretation or "",
                    "commentaire": scoring_sans_bilan.commentaire or "",
                    "score_type": "Scoring sans bilan",
                }
            else:
                scoring_context = None
            # keep compatibility with template expecting 'scoring'
            report_data["scoring"] = scoring_context

        _force_ratios_percent_display(report_data)
        print(report_data)

            
        # 3. Retourner le format demandé
        try:
            if format_report.upper() == 'PDF':
                print("Génération du PDF...")  # Debug
                # Rendre le template HTML
                html_string = render_to_string('main/report_acremac_template.html', report_data)
                
                # Générer le PDF en mémoire
                pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri('/static/')).write_pdf()
                
                # Préparer la réponse HTTP
                response = HttpResponse(pdf_file, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="rapport_solvabilite.pdf"'
                response['Content-Length'] = len(pdf_file)
                
                return response
            elif format_report.upper() == 'JSON':
                # Renvoyer le dictionnaire directement comme une réponse JSON pour inspection
                return Response(report_data, status=status.HTTP_200_OK)
            elif format_report.upper() == 'XML':
                logger.info("Génération du XML + XSD...")

                try:
                    response = generate_xml_with_xsd(report_data)
                    logger.info("XML + XSD généré avec succès")
                    return response

                except Exception as e:
                    logger.error(f"Erreur lors de la génération XML/XSD : {str(e)}")

                    error_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
                    <erreur>
                        <message>Erreur lors de la génération du rapport XML</message>
                        <details>{str(e)}</details>
                    </erreur>'''

                    response = HttpResponse(
                        error_xml, 
                        content_type='application/xml; charset=utf-8',
                        status=500
                    )
                    response['Content-Disposition'] = 'attachment; filename="rapport_erreur.xml"'
                    return response
            elif format_report.upper() == 'HTML':
                print("Génération du HTML...")  # Debug
                response = generate_html(report_data)
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
