# Fichier : views_reporting.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from main.models import Annee, Devise, Commande, Resume, CodeNafAcheteur, CodeNafAcheteur
from main.models import Resume, RiskRating, RiskManagment, OpinionCreditAcremac, DonneesEnregistrement, AntecedantsJuridique
from main.models import ResponsableAcheteur, ConseilAdministration, CompositionCapitalSocial, CompositionAction, Structure
from main.models import Annee, AnalyseSectorielle, Tendance, Geopolitics, Advice, Banquier
from main.models import CompteFinancier, OperationEtHistorique, ScoringSansBilanAcheteur, ConditionAchat, ConditionDeVente, SommaireEtAvis

from main.serializers_reporting import AnneeSerializer, DeviseSerializer, CommandeSerializer, RapportSolvabiliteSerializer

from main.utils import get_simple_actifs_data, get_structured_actif_data, get_structured_passif_data, get_structured_resultat_data, get_structured_ratios_data
from main.utils import get_structured_actif_anglais_data, get_structured_passif_anglais_data, get_structured_resultat_anglais_data, get_structured_ratios_anglais_data
from main.utils import get_structured_actif_bancaire_data, get_structured_passif_bancaire_data, get_structured_produit_bancaire_data, get_structured_depense_bancaire_data, get_structured_hors_bilan_bancaire_data, get_structured_ratios_bancaire_data
from main.utils import get_structured_actif_syscohada_data, get_structured_passif_syscohada_data, get_structured_resultat_syscohada_data, get_structured_ratios_syscohada_data
from main.utils import get_structured_actif_ifrs_data, get_structured_passif_ifrs_data, get_structured_resultat_ifrs_data, get_structured_ratios_ifrs_data

from main.utils import (
    get_charts_structure_financiere_data,
    get_charts_rentabilite_financiere_data, 
    get_charts_delais_data
)
from main.utils import (
    get_charts_structure_financiere_anglais_data,
    get_charts_rentabilite_financiere_anglais_data, 
    get_charts_delais_anglais_data
)
from main.utils import (
    get_charts_structure_financiere_bancaire_data,
    get_charts_rentabilite_bancaire_data, 
    get_charts_ratios_bancaire_data
)
from main.utils import (
    get_structured_actif_syscohada_data,
    get_structured_passif_syscohada_data,
    get_structured_resultat_syscohada_data,
    get_charts_structure_financiere_syscohada_data,
    get_charts_rentabilite_financiere_syscohada_data, 
    get_charts_delais_syscohada_data
)
from main.utils import (
    get_structured_actif_ifrs_data,
    get_structured_passif_ifrs_data,
    get_structured_resultat_ifrs_data,
    get_structured_ratios_ifrs_data,
    get_charts_structure_financiere_ifrs_data, 
    get_charts_rentabilite_financiere_ifrs_data,
    get_charts_delais_ifrs_data
)


from main.api.views_scoring_classique import *
from main.api.views_scoring_anglais import *
from main.api.views_scoring_bancaire import *
from main.api.views_scoring_syscohada import *
from main.api.views_scoring_ifrs import *

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from datetime import datetime, timedelta
from django.utils import timezone
import html
import base64
import os
from django.conf import settings
from django.contrib.staticfiles import finders

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status  # Ajoutez cette importation
from main.models import Annee, Devise, Commande, Acheteur, CodeNaceAcheteur, TelephoneAcheteur, ProprieteEtActif  # Ajoutez Acheteur ici
from main.serializers_reporting import AnneeSerializer, DeviseSerializer, CommandeSerializer, RapportSolvabiliteSerializer
from datetime import datetime, timedelta
from django.utils import timezone
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

import json
from django.core.serializers.json import DjangoJSONEncoder
from decimal import Decimal
from datetime import datetime, date
from urllib.parse import urljoin
from django.db.models.query import QuerySet
from django.db.models.manager import BaseManager
from django.utils.functional import Promise

# Dans views_reporting.py - ajoutez ces imports
from main.api.views_report import (
    generate_pdf_weasyprint_3,
    generate_html,
    generate_xml_v2,
    render_html_template,
    generate_xml_with_xsd,
    render_to_string,
    HttpResponse,
    Response,
    status
)

# Importez aussi la fonction de génération de logo si besoin
from main.api.views_report import get_logo_data, get_logo_path
# Dans views_reporting.py
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
import json
import xml.etree.ElementTree as ET
from weasyprint import HTML
import tempfile
import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import base64
from datetime import datetime
import random
import re
import string
import unicodedata
# Dans views_reporting.py, modifiez la fonction generer_pdf_weasyprint
import base64
import os
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
import tempfile


# ... vos autres vues ...


def _to_json_safe(value):
    """Convertit récursivement les données en types JSON sérialisables."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    # gettext_lazy renvoie un objet "lazy" (Promise) qui peut être itérable
    # et sinon se retrouver découpé caractère par caractère.
    if isinstance(value, Promise):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, QuerySet):
        return [_to_json_safe(v) for v in value]
    if isinstance(value, BaseManager):
        return [_to_json_safe(v) for v in value.all()]
    # Couvre aussi les related managers dynamiques (ManyRelatedManager).
    if hasattr(value, "all") and callable(getattr(value, "all", None)):
        try:
            return [_to_json_safe(v) for v in value.all()]
        except Exception:
            pass
    if isinstance(value, dict):
        return {k: _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(v) for v in value]
    # Fallback pour autres objets itérables non pris en charge ci-dessus.
    if hasattr(value, "__iter__"):
        try:
            return [_to_json_safe(v) for v in value]
        except Exception:
            pass
    if hasattr(value, "_meta"):  # Objet Django (Model)
        return str(value)
    return str(value)


def _safe_nested_attr(obj, attrs, default="Non spécifié"):
    """Lit un attribut imbriqué de manière sûre (None-safe)."""
    current = obj
    for attr in attrs:
        if current is None:
            return default
        current = getattr(current, attr, None)
    return current if current not in (None, "") else default


def _normalize_type_bilan(value, default="classique"):
    """Normalise le type de bilan vers les clés attendues côté reporting."""
    if not value:
        return default

    normalized = str(value).strip().lower()
    mapping = {
        "classique": "classique",
        "bancaire": "bancaire",
        "anglais": "anglais",
        "syscohada": "syscohada",
        "ifrs": "ifrs",
        "ifrs cobac": "ifrs",
        "irfs_cobac": "ifrs",
        "irfs cobac": "ifrs",
    }
    return mapping.get(normalized, default)


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

    encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"


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


def _find_static_file_path(image_path):
    """Résout le chemin absolu d'un asset statique."""
    absolute_path = finders.find(image_path)
    if absolute_path and os.path.exists(absolute_path):
        return absolute_path

    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root:
        fallback_path = os.path.join(static_root, image_path)
        if os.path.exists(fallback_path):
            return fallback_path

    return None


def _convert_svg_file_to_png_base64(svg_path):
    """Convertit un fichier SVG en data URI PNG base64."""
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM

        drawing = svg2rlg(svg_path)
        if drawing is None:
            return None

        png_bytes = renderPM.drawToString(drawing, fmt="PNG")
        if not png_bytes:
            return None

        encoded_png = base64.b64encode(png_bytes).decode("utf-8")
        return f"data:image/png;base64,{encoded_png}"
    except Exception as e:
        print(f"Erreur conversion SVG->PNG ({svg_path}): {e}")
        return None


def get_static_image_base64(image_path):
    """
    Convertit une image statique en Base64
    :param image_path: Chemin relatif de l'image (ex: 'riskrating/5.svg')
    :return: Chaîne Base64 ou None
    """
    absolute_path = _find_static_file_path(image_path)

    if absolute_path and os.path.exists(absolute_path):
        try:
            with open(absolute_path, 'rb') as img_file:
                img_content = img_file.read()
                
                # Déterminer le type MIME
                if image_path.endswith('.svg'):
                    mime_type = 'image/svg+xml'
                elif image_path.endswith('.png'):
                    mime_type = 'image/png'
                elif image_path.endswith('.jpg') or image_path.endswith('.jpeg'):
                    mime_type = 'image/jpeg'
                else:
                    mime_type = 'application/octet-stream'
                
                encoded_string = base64.b64encode(img_content).decode('utf-8')
                return f"data:{mime_type};base64,{encoded_string}"
        except Exception as e:
            print(f"Erreur lors de la conversion de {image_path}: {e}")
    
    return None


def get_risk_rating_base64(score):
    """Convertit le score de risque en image Base64"""
    if score is None or score == "Non spécifié":
        score = 0
    try:
        score = int(score)
    except (ValueError, TypeError):
        score = 0
    
    # Les assets disponibles sont 0.svg a 8.svg
    score = max(0, min(8, score))
    image_path = f'riskrating/{score}.svg'
    svg_path = _find_static_file_path(image_path)

    if svg_path:
        # Force la compatibilité navigateur: on renvoie du PNG même si la source est un SVG.
        png_data_uri = _convert_svg_file_to_png_base64(svg_path)
        if png_data_uri:
            return png_data_uri

    # Fallback: renvoyer le SVG en base64 si la conversion PNG échoue.
    return get_static_image_base64(image_path)


def _normalize_base_url(url):
    value = str(url or '').strip()
    if not value:
        return ''
    return value if value.endswith('/') else f'{value}/'


def _get_public_base_url(request=None):
    explicit_base_url = (
        getattr(settings, 'REPORT_BASE_URL', None)
        or getattr(settings, 'SITE_URL', None)
    )
    if explicit_base_url:
        return _normalize_base_url(explicit_base_url)

    if request is not None:
        try:
            return _normalize_base_url(request.build_absolute_uri('/'))
        except Exception:
            pass

    return _normalize_base_url('http://localhost:8000/')


def _get_static_base_url(request=None, subpath=''):
    static_url = getattr(settings, 'STATIC_URL', '/static/')
    if static_url.startswith(('http://', 'https://')):
        base_static_url = _normalize_base_url(static_url)
    else:
        base_static_url = _normalize_base_url(
            urljoin(_get_public_base_url(request), static_url.lstrip('/'))
        )

    if not subpath:
        return base_static_url
    return urljoin(base_static_url, subpath.lstrip('/'))


def _get_weasy_base_url(request=None):
    if request is not None:
        return _get_public_base_url(request)
    return settings.BASE_DIR


def _inject_static_urls(report_data, request=None):
    if not isinstance(report_data, dict):
        return report_data

    static_base_url = _get_static_base_url(request)
    riskrating_base_url = _get_static_base_url(request, 'riskrating/')

    report_data['url_site'] = riskrating_base_url

    summary_section = report_data.get('summary_and_opinion')
    if isinstance(summary_section, dict):
        summary_section['url_site'] = riskrating_base_url

    for section_name in (
        'scoring_sans_bilan',
        'scoring_classique',
        'scoring_anglais',
        'scoring_bancaire',
        'scoring_syscohada',
        'scoring_ifrs',
    ):
        section_value = report_data.get(section_name)
        if isinstance(section_value, dict):
            section_value['url_site'] = static_base_url

    return report_data



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
            
        
        
        # 2. Définir les années et récupérer la devise
        years_to_retrieve = [data['annee_n'], data['annee_n1'], data['annee_n2']]
        print(years_to_retrieve)
        
        # Récupération de la commande si spécifiée
        commande = None
        if data.get('inclure_commande') == 'oui' and data.get('commande_id'):
            try:
                commande = Commande.objects.get(pk=data['commande_id'])
            except Commande.DoesNotExist:
                pass
        
        # Récupération du premier téléphone
        # Recuperation des téléphones en fonction de l'acheteur
        telephone = None
        try:
            telephone = TelephoneAcheteur.objects.filter(acheteur=acheteur).first()
        except TelephoneAcheteur.DoesNotExist:
            pass
        
        # Récupération du Résumé executif
        # Recuperation du resume en fonction de l'acheteur
        resume = None
        try:
            resume = Resume.objects.filter(acheteur=acheteur).first()
        except Resume.DoesNotExist:
            pass
            
        # Recuperation des codes NAF de l'acheteur
        # Recuperation des codes NACE de l'acheteur
        # naf_codes = list(CodeNafAcheteur.objects.filter(acheteur=acheteur).values_list('code', flat=True))
        # nace_codes = list(CodeNaceAcheteur.objects.filter(acheteur=acheteur).values_list('code', flat=True))
        # Recuperation des codes NACE avec leurs libellés
        nace_codes_data = list(CodeNaceAcheteur.objects.filter(acheteur=acheteur)
            .select_related('code__category')
            .values('code__code', 'code__libelle', 'code__category__libelle')
            .distinct())

        # Formatage pour affichage
        nace_codes_formatted = []
        for item in nace_codes_data:
            if item['code__libelle']:
                nace_codes_formatted.append(f"{item['code__code']} - {item['code__libelle']}")
            else:
                nace_codes_formatted.append(item['code__code'])

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
        notes_details = []
        risk_field_labels = {
            'risque_de_defaut': 'Risque de défaut',
            'risque_de_concentration_credit': 'Risque de concentration crédit',
            'risque_de_reputation': 'Risque de réputation',
            'risque_pays': 'Risque pays',
            'risque_de_taux_dinteret': "Risque de taux d'intérêt",
            'risque_de_liquidite': 'Risque de liquidité',
            'risque_eleve': 'Risque élevé',
            'risque_moyen': 'Risque moyen',
            'risque_faible': 'Risque faible',
        }
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
                    notes_details.append({
                        "field": field,
                        "label": risk_field_labels.get(field, field),
                        "value": value,
                    })

        # Formatez la liste en une chaîne séparée par des virgules
        notes_str = ", ".join(note_values) if note_values else "Non spécifié"
        notes_detailed_str = "\n".join([f"{item['label']}: {item['value']}" for item in notes_details]) if notes_details else "Non spécifié"
        
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
                "autre": antecedant.Autre if antecedant.Autre else "Non spécifié",
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
                "sexe": responsable.Sexe if responsable.Sexe else "Non spécifié",
                "poste": responsable.poste if responsable.poste else "Non spécifié",
                "nationalite": responsable.nationalite if responsable.nationalite else "Non spécifié",
                "commentaire": responsable.commentaire if responsable.commentaire else "Non spécifié",
            })

        # Recuperation des membres du conseil d'administration de l'acheteur 
        conseil_administration_membres = ConseilAdministration.objects.filter(acheteur=acheteur)
        list_ca_membres_data = []
        for membre in conseil_administration_membres:
            list_ca_membres_data.append({
                "nom": membre.nom if membre.nom else "Non spécifié",
                "fonction_dans_le_conseil": membre.fonction_dans_le_conseil if membre.fonction_dans_le_conseil else "Non spécifié",
                "numero_adresse": membre.numero_adresse if membre.numero_adresse else "Non spécifié",
                "rue_adresse": membre.rue_adresse if membre.rue_adresse else "Non spécifié",
                "code_postale_adresse": membre.code_postale_adresse if membre.code_postale_adresse else "Non spécifié",
                "commentaire": membre.commentaire if membre.commentaire else "Non spécifié",
            })
          
        
        # Récupération Capital social
        # Recuperation de la composition du capital social de l'acheteur
        composition_capital_social = None
        try:
            composition_capital_social = CompositionCapitalSocial.objects.get(acheteur=acheteur)
        except CompositionCapitalSocial.DoesNotExist:
            pass
            
         
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
                "type_affiliation": affiliation.type_affiliation if affiliation.type_affiliation else "Non spécifié",
                "numero_adresse": affiliation.numero_adresse if affiliation.numero_adresse else "Non spécifié",
                "rue_adresse": affiliation.rue_adresse if affiliation.rue_adresse else "Non spécifié",
                "code_postale_adresse": affiliation.code_postale_adresse if affiliation.code_postale_adresse else "Non spécifié",
                "commentaire": affiliation.commentaire if affiliation.commentaire else "Non spécifié",
            })
        
            
        # Recuperation de l'analyse sectorielle de l'acheteur
        analyse_sectorielle = None
        try:
            analyse_sectorielle = AnalyseSectorielle.objects.get(acheteur=acheteur)
        except AnalyseSectorielle.DoesNotExist:
            pass

        # Recuperation de la tendance de l'acheteur
        tendance = None
        try:
            tendance = Tendance.objects.get(acheteur=acheteur)
        except Tendance.DoesNotExist:
            pass

        # Recuperation des conseils sur l'acheteur
        advice = None
        try:
            advice = Advice.objects.filter(acheteur=acheteur).first()
        except Advice.DoesNotExist:
            pass

        # Recuperation des donnees geopolitiques sur l'acheteur
        geopolitics = None
        try:
            geopolitics = Geopolitics.objects.get(acheteur=acheteur)
        except Geopolitics.DoesNotExist:
            pass
            
            
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
        compte_financier = None
        try:
            compte_financier = CompteFinancier.objects.get(acheteur=acheteur)
        except CompteFinancier.DoesNotExist:
            pass

        # Résolution métier: devise/type_bilan viennent d'abord de la requête, sinon de CompteFinancier.
        requested_devise = (data.get("devise") or "").strip().upper()
        financial_devise = (getattr(compte_financier, "devise", None) or "").strip().upper()
        effective_devise = requested_devise or financial_devise or "XAF"

        requested_type_bilan = data.get("type_bilan")
        financial_type_bilan = getattr(compte_financier, "type_bilan", None)
        effective_type_bilan = _normalize_type_bilan(requested_type_bilan or financial_type_bilan, default="classique")

        data["devise"] = effective_devise
        data["type_bilan"] = effective_type_bilan
            
            
        # Recuperation de l'historique des operations de l'acheteur
        operation_history = None
        try:
            operation_history = OperationEtHistorique.objects.get(acheteur=acheteur)
        except OperationEtHistorique.DoesNotExist:
            pass
        
        # Recuperation de l'opinion credit ACREMAC de l'acheteur  
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
        notes_details = []
        risk_field_labels = {
            'risque_de_defaut': 'Risque de défaut',
            'risque_de_concentration_credit': 'Risque de concentration crédit',
            'risque_de_reputation': 'Risque de réputation',
            'risque_pays': 'Risque pays',
            'risque_de_taux_dinteret': "Risque de taux d'intérêt",
            'risque_de_liquidite': 'Risque de liquidité',
            'risque_eleve': 'Risque élevé',
            'risque_moyen': 'Risque moyen',
            'risque_faible': 'Risque faible',
        }
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
                    notes_details.append({
                        "field": field,
                        "label": risk_field_labels.get(field, field),
                        "value": value,
                    })

        # Formatez la liste en une chaîne séparée par des virgules
        notes_str = ", ".join(note_values) if note_values else "Non spécifié"
        notes_detailed_str = "\n".join([f"{item['label']}: {item['value']}" for item in notes_details]) if notes_details else "Non spécifié"
        
        # Calculer le score
        risk_score = risk_rating.calculate_risk_score() if risk_rating else 1

        # Générer l'image de la jauge en Base64
        risk_gauge_base64 = get_risk_gauge_chart(risk_score)
        
        # NOUVEAU: SCORING SANS BILAN
        # Recuperer le scoring sans bilan ici 
        scoring_sans_bilan = ScoringSansBilanAcheteur.objects.filter(acheteur=acheteur).first()
        
        # Limiter le score entre 0 et 10 pour correspondre aux images
        raw_score_sans_bilan = float(scoring_sans_bilan.scoring_value) if scoring_sans_bilan and scoring_sans_bilan.scoring_value is not None else 0.0
        score_indexe = int(round(raw_score_sans_bilan))  # arrondi à l'entier le plus proche
        score_indexe = max(0, min(score_indexe, 10))
        print(int(round(raw_score_sans_bilan)))
        print(score_indexe)
        
        # NOUVEAU: SCORING AVEC BILAN CLASSIQUE
        # Scoring avec bilan classique
        # Initialisation des scores par année pour le bilan classique
        score_value_annee_N = None
        score_value_annee_N1 = None
        score_value_annee_N2 = None
        interpretation_annee_N = "N/A"
        interpretation_annee_N1 = "N/A"
        interpretation_annee_N2 = "N/A"

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
                    interpretation_anglais_annee_N2 = classe_risque_anglais



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

        
        # Recuperation des proprietes et actifs de l'acheteur
        # Utilisez .filter() pour récupérer toutes les instances
        properties_and_assets = ProprieteEtActif.objects.filter(acheteur=acheteur).prefetch_related("locaux")
        list_properties_and_assets_data = []

        # 2. Bouclez sur les objets pour construire une liste de dictionnaires
        for prop_asset in properties_and_assets:
            locaux_labels = [str(local) for local in prop_asset.locaux.all()]
            list_properties_and_assets_data.append({
                "locaux": locaux_labels if locaux_labels else [],
                "branche": prop_asset.branche if prop_asset.branche else "Non spécifié",
            })  
        
        
        # Recuperation des conditions d'achat et de vente de l'acheteur
        condition_achat = None
        try:
            condition_achat = ConditionAchat.objects.get(acheteur=acheteur)
        except ConditionAchat.DoesNotExist:
            pass
        
        condition_vente = None    
        try:
            condition_vente = ConditionDeVente.objects.get(acheteur=acheteur)
        except ConditionDeVente.DoesNotExist:
            pass

        # Valeurs robustes pour couvrir les modèles avec/sans champs *_ref
        condition_vente_recouvrement = "Non spécifié"
        condition_vente_comportement = "Non spécifié"
        if condition_vente:
            recouvrement_ref = getattr(condition_vente, "recouvrement_de_dette_jugement_ref", None)
            comportement_ref = getattr(condition_vente, "comportement_de_paiement_ref", None)

            condition_vente_recouvrement = (
                getattr(recouvrement_ref, "libelle", None)
                or getattr(condition_vente, "recouvrement_de_dette_jugement", None)
                or "Non spécifié"
            )
            condition_vente_comportement = (
                getattr(comportement_ref, "libelle", None)
                or getattr(condition_vente, "comportement_de_paiement", None)
                or "Non spécifié"
            )
            
        
        # Add new section to retrieve general conclusion
        conclusion_generale = None
        try:
            conclusion_generale = SommaireEtAvis.objects.get(acheteur=acheteur)
        except SommaireEtAvis.DoesNotExist:
            pass

        # DEBUG: Diagnostic détaillé des données classiques
        classic_actif_table = get_simple_actifs_data(acheteur, years_to_retrieve)
        classic_actif_data = get_structured_actif_data(acheteur, years_to_retrieve)
        classic_passif_data = get_structured_passif_data(acheteur, years_to_retrieve)
        classic_resultat_data = get_structured_resultat_data(acheteur, years_to_retrieve)
        classic_ratios_data = get_structured_ratios_data(acheteur, years_to_retrieve)
        classic_chart_structure = get_charts_structure_financiere_data(acheteur, years_to_retrieve)
        classic_chart_rentabilite = get_charts_rentabilite_financiere_data(acheteur, years_to_retrieve)
        classic_chart_delais = get_charts_delais_data(acheteur, years_to_retrieve)

        print(
            "[DEBUG][REPORTING][CLASSIQUE] "
            f"acheteur_id={getattr(acheteur, 'id', None)} years={years_to_retrieve} "
            f"actif_table_rows={len(classic_actif_table) if isinstance(classic_actif_table, list) else 'N/A'} "
            f"actif_sections={len(classic_actif_data.keys()) if isinstance(classic_actif_data, dict) else 'N/A'} "
            f"passif_sections={len(classic_passif_data.keys()) if isinstance(classic_passif_data, dict) else 'N/A'} "
            f"resultat_sections={len(classic_resultat_data.keys()) if isinstance(classic_resultat_data, dict) else 'N/A'} "
            f"ratios_sections={len(classic_ratios_data.keys()) if isinstance(classic_ratios_data, dict) else 'N/A'} "
            f"chart_structure={'OK' if classic_chart_structure else 'None'} "
            f"chart_rentabilite={'OK' if classic_chart_rentabilite else 'None'} "
            f"chart_delais={'OK' if classic_chart_delais else 'None'}"
        )
           
        
        
        
        static_base_url = _get_static_base_url(request)

        def _score_image_path(score_value):
            try:
                score_int = round(float(score_value)) if score_value is not None else 0
            except (TypeError, ValueError):
                score_int = 0
            score_int = max(0, min(10, score_int))
            return f"scoring/{score_int}.png"

        def _score_image_base64(score_value):
            return get_static_image_base64(_score_image_path(score_value))
        riskrating_base_url = _get_static_base_url(request, 'riskrating/')

        # Préparation des données pour le template
        report_data = {
            "logo_data": get_logo_data(),
            "logo_path": get_logo_path(),
            "url_site": riskrating_base_url,
            "header_report": {
                "acremac_services": "Services ACREMAC Gabon",
                "acremac_mail": "credit.report@acremac.com",
                "date_today": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "bilan_report": data['type_bilan'].upper() if 'type_bilan' in data else "",
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
                    "pays": _safe_nested_attr(commande, ["pays", "nom"]),
                    "ville": _safe_nested_attr(commande, ["ville", "nom"]),
                },
                "acremac_info": {
                    "nom": acheteur.nom if hasattr(acheteur, 'nom') else "Non spécifié",
                    "sigle": acheteur.sigle if hasattr(acheteur, 'sigle') else "Non spécifié",
                    "email": acheteur.email if hasattr(acheteur, 'email') else "Non spécifié",
                    "boite_postale": acheteur.boite_postale if hasattr(acheteur, 'boite_postale') else "Non spécifié",
                    "pays": _safe_nested_attr(acheteur, ["pays", "nom"]),
                    "province": _safe_nested_attr(acheteur, ["province", "nom"]),
                    "ville": _safe_nested_attr(acheteur, ["ville", "nom"]),
                    "fax": acheteur.fax if hasattr(acheteur, 'fax') else "Non spécifié",
                    "telephone": telephone.telephone if hasattr(telephone, 'telephone') else "Non spécifié",
                    "numero_adresse": acheteur.numero_adresse if hasattr(acheteur, 'numero_adresse') else "Non spécifié",
                    "rue_adresse": acheteur.rue_adresse if hasattr(acheteur, 'rue_adresse') else "Non spécifié",
                    "code_nace": acheteur.code_nace if hasattr(acheteur, 'code_nace') else "Non spécifié",
                    "code_postal": acheteur.code_postal if hasattr(acheteur, 'code_postal') else "Non spécifié",
                    "activite_principale": acheteur.activite_principale if hasattr(acheteur, 'activite_principale') else "Non spécifié",
                }
            },
            "additional_information": {
                "title_3": "INFORMATIONS SUPPLEMENTAIRES",
                "date_creation": acheteur.date_creation.strftime("%d/%m/%Y") if hasattr(acheteur, 'date_creation') and acheteur.date_creation else "Non spécifié",
                "nace_codes": nace_codes_formatted if nace_codes_formatted else ["Aucun code NACE disponible"],
                "naf_codes": naf_codes_formatted if naf_codes_formatted else ["Aucun code NAF disponible"],
                "boite_postale": acheteur.boite_postale if hasattr(acheteur, 'boite_postale') else "Non spécifié",
                "site_internet": acheteur.site_internet if hasattr(acheteur, 'site_internet') else "Non spécifié",
                "description": acheteur.description if hasattr(acheteur, 'description') else "Non spécifié",
                "commentaire": acheteur.commentaire if hasattr(acheteur, 'commentaire') else "Non spécifié",
                "categorie_entreprise": _safe_nested_attr(acheteur, ["categorie_entreprise", "libelle"]),
                "statut_entreprise": _safe_nested_attr(acheteur, ["statut_entreprise", "libelle"]),
                "forme_juridique": _safe_nested_attr(acheteur, ["forme_juridique", "libelle"]),
                "activite_principale": acheteur.activite_principale if hasattr(acheteur, 'activite_principale') else "Non spécifié",
                "code_nace": acheteur.code_nace if hasattr(acheteur, 'code_nace') else "Non spécifié",
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
                # Utiliser la chaîne Base64 pour l'affichage de la jauge
                "risk_gauge_base64": risk_gauge_base64,
                "risk_rating_image_base64": get_risk_rating_base64(risk_rating_value),
                "risk_rating_image_url": risk_rating.get_risk_rating_image_url() if risk_rating else None,
                "url_site": riskrating_base_url,
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
                "title_6": "AVIS CREDIT ACREMAC",
                # Passez le dictionnaire directement au template
                "notes": notes_str, # Passez la chaîne formatée au template
                "notes_details": notes_details,
                "notes_detailed": notes_detailed_str,
                "highlighted_risks": highlighted_risks,
                "montant_credit_maximum": acremac_opinion.montant_credit_maximum if acremac_opinion else "Non spécifié",
                "commentaire": acremac_opinion.commentaire if acremac_opinion else "Aucun commentaire disponible",
            },
            "registered_data": {
                "title_7": "DONNEES D'ENREGISTREMENT",
                "date_creation": donnees_enregistrement.date_creation.strftime("%d/%m/%Y") if donnees_enregistrement and donnees_enregistrement.date_creation else "Non spécifié",
                "date_registre": donnees_enregistrement.date_registre.strftime("%d/%m/%Y") if donnees_enregistrement and donnees_enregistrement.date_registre else "Non spécifié",
                "forme_juridique": (
                    donnees_enregistrement.forme_juridique
                    if donnees_enregistrement and donnees_enregistrement.forme_juridique
                    else donnees_enregistrement.forme_juridique if donnees_enregistrement else "Non spécifié"
                ),
                "acheteur": _safe_nested_attr(donnees_enregistrement, ["acheteur", "nom"]),
                "numero_registre_commerce": donnees_enregistrement.numero_registre_commerce if donnees_enregistrement and donnees_enregistrement.numero_registre_commerce else "Non spécifié",
                "numero_fiscale": donnees_enregistrement.numero_fiscale if donnees_enregistrement and donnees_enregistrement.numero_fiscale else "Non spécifié",
                "statut_registre": (
                    donnees_enregistrement.statut_registre
                    if donnees_enregistrement and donnees_enregistrement.statut_registre
                    else donnees_enregistrement.statut_registre if donnees_enregistrement else "Non spécifié"
                ),
                "commentaire": donnees_enregistrement.commentaire if donnees_enregistrement and donnees_enregistrement.commentaire else "Aucun commentaire disponible",
            },
            "legal_background": {
                "title_8": "ANTECEDENTS JURIDIQUES",
                "antecedents_juridiques": list_antecedants_data if list_antecedants_data else [],
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
                    "score": risk_management.get_management_score()['oui_count'] if risk_management else 0,
                    "image": risk_management.get_management_image_path_report() if risk_management else "management/passable.png",
                    "image_base64": risk_management.get_management_image_base64() if risk_management else None,
                    "image_path": risk_management.get_management_image_path_report() if risk_management else "management/passable.png",
                },
                "responsables": list_responsables_data if list_responsables_data else [],
                "conseil_administration": list_ca_membres_data if list_ca_membres_data else [],
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
                "actionnaires": list_shareholders_data if list_shareholders_data else [],
            },
            "affiliations": {
                "title_12": "AFFILIATIONS D'ENTREPRISE",
                "affiliations": list_affiliations_data if list_affiliations_data else [],
            },
            "sector_analysis": {
                "title_13": "ANALYSE SECTORIELLE",
                "nace_codes": nace_codes_formatted if nace_codes_formatted else ["Aucun code NACE disponible"],
                "naf_codes": naf_codes_formatted if naf_codes_formatted else ["Aucun code NAF disponible"],
                "sectorielle": {
                    "commentaire": analyse_sectorielle.commentaire if analyse_sectorielle and analyse_sectorielle.commentaire else "Aucun commentaire disponible",
                    "impact_covid_19": analyse_sectorielle.impact_covid_19 if analyse_sectorielle and analyse_sectorielle.impact_covid_19 else "Non spécifié",
                },
                "tendance": {
                    "avis_commercial": (
                        getattr(tendance.avis_commercial, "libelle", str(tendance.avis_commercial))
                        if tendance and tendance.avis_commercial
                        else "Non spécifié"
                    ),
                    "plus_informations": tendance.plus_informations if tendance and tendance.plus_informations else "Non spécifié",
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
                "data_banks": list_banking_data if list_banking_data else [],
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
                "type_bilan": compte_financier.type_bilan if compte_financier and compte_financier.type_bilan else compte_financier.type_bilan if compte_financier else "Non spécifié",
                "commentaire": compte_financier.commentaire if compte_financier and compte_financier.commentaire else "Aucun commentaire disponible",
            },
            
            
            "financial_statements": {
                "years": [data['annee_n'], data['annee_n1'], data['annee_n2']],
                "bilan_type": data['type_bilan'],
                "etats_financiers_classiques": {
                    "annee_N": data['annee_n'],
                    "annee_N1": data['annee_n1'],
                    "annee_N2": data['annee_n2'],
                    "actif_table": classic_actif_table,
                    "actif_data": classic_actif_data,
                    "passif_data": classic_passif_data,
                    "resultat_data": classic_resultat_data,
                    "ratios_data": classic_ratios_data,
                    "charts_data": {
                        "charts_structure_financiere": classic_chart_structure,
                        "charts_rentabilite_financiere": classic_chart_rentabilite,
                        "charts_delais": classic_chart_delais,
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
            
            "charts": {
                "charts_structure_financiere": {},
                "charts_rentabilite_financiere": {},
                "charts_delais": {},
            },
            
            "scoring_sans_bilan": {
                "title_16": "SCORING ACREMAC - SANS BILAN",
                "score_image": f"scoring/{score_indexe}.png",
                "score_png": f"scoring/{score_indexe}.png",
                "score_image_base64": get_static_image_base64(f"scoring/{score_indexe}.png"),
                "score_value": f"{raw_score_sans_bilan:.2f}",  # <- toujours 2 décimales
                "interpretation": scoring_sans_bilan.interpretation if scoring_sans_bilan else "Non spécifié",
                "commentaire": scoring_sans_bilan.commentaire if scoring_sans_bilan else "Aucun commentaire disponible",
                "score_type": "Scoring sans bilan",
                "url_site": static_base_url,
            },
            "scoring_classique": {
                "title_16": "SCORING CLASSIQUE - AVEC BILAN",
                "annee_N": data['annee_n'],
                "annee_N1": data['annee_n1'],
                "annee_N2": data['annee_n2'],
                
                "score_image_annee_N": _score_image_path(score_value_annee_N),
                "score_image_annee_N_base64": _score_image_base64(score_value_annee_N),
                "score_value_annee_N": score_value_annee_N,
                "score_value_annee_N_arrondi": round(float(score_value_annee_N)) if score_value_annee_N is not None else 0,
                "interpretation_annee_N": interpretation_annee_N,
                
                "score_image_annee_N1": _score_image_path(score_value_annee_N1),
                "score_image_annee_N1_base64": _score_image_base64(score_value_annee_N1),
                "score_value_annee_N1": score_value_annee_N1,
                "score_value_annee_N1_arrondi": round(float(score_value_annee_N1)) if score_value_annee_N1 is not None else 0,
                "interpretation_annee_N1": interpretation_annee_N1,
                
                "score_image_annee_N2": _score_image_path(score_value_annee_N2),
                "score_image_annee_N2_base64": _score_image_base64(score_value_annee_N2),
                "score_value_annee_N2": score_value_annee_N2,
                "score_value_annee_N2_arrondi": round(float(score_value_annee_N2)) if score_value_annee_N2 is not None else 0,
                "interpretation_annee_N2": interpretation_annee_N2,
                
                "url_site": static_base_url,
            },
            "scoring_anglais": {
                "title_16": "SCORING ANGLAIS - AVEC BILAN",
                "annee_N": data['annee_n'],
                "annee_N1": data['annee_n1'],
                "annee_N2": data['annee_n2'],
                
                "score_image_annee_N": _score_image_path(score_value_anglais_annee_N),
                "score_image_annee_N_base64": _score_image_base64(score_value_anglais_annee_N),
                "score_value_annee_N": score_value_anglais_annee_N,
                "score_value_annee_N_arrondi": round(float(score_value_anglais_annee_N)) if score_value_anglais_annee_N is not None else 0,
                "interpretation_annee_N": interpretation_anglais_annee_N,
                
                "score_image_annee_N1": _score_image_path(score_value_anglais_annee_N1),
                "score_image_annee_N1_base64": _score_image_base64(score_value_anglais_annee_N1),
                "score_value_annee_N1": score_value_anglais_annee_N1,
                "score_value_annee_N1_arrondi": round(float(score_value_anglais_annee_N1)) if score_value_anglais_annee_N1 is not None else 0,
                "interpretation_annee_N1": interpretation_anglais_annee_N1,
                
                "score_image_annee_N2": _score_image_path(score_value_anglais_annee_N2),
                "score_image_annee_N2_base64": _score_image_base64(score_value_anglais_annee_N2),
                "score_value_annee_N2": score_value_anglais_annee_N2,
                "score_value_annee_N2_arrondi": round(float(score_value_anglais_annee_N2)) if score_value_anglais_annee_N2 is not None else 0,
                "interpretation_annee_N2": interpretation_anglais_annee_N2,
                
                "url_site": static_base_url,
            },
            "scoring_bancaire": {
                "title_16": "SCORING BANCAIRE - AVEC BILAN",
                "annee_N": data['annee_n'],
                "annee_N1": data['annee_n1'],
                "annee_N2": data['annee_n2'],
                
                "score_image_annee_N": _score_image_path(score_value_bancaire_annee_N),
                "score_image_annee_N_base64": _score_image_base64(score_value_bancaire_annee_N),
                "score_value_annee_N": score_value_bancaire_annee_N,
                "score_value_annee_N_arrondi": round(float(score_value_bancaire_annee_N)) if score_value_bancaire_annee_N is not None else 0,
                "interpretation_annee_N": interpretation_bancaire_annee_N,
                
                "score_image_annee_N1": _score_image_path(score_value_bancaire_annee_N1),
                "score_image_annee_N1_base64": _score_image_base64(score_value_bancaire_annee_N1),
                "score_value_annee_N1": score_value_bancaire_annee_N1,
                "score_value_annee_N1_arrondi": round(float(score_value_bancaire_annee_N1)) if score_value_bancaire_annee_N1 is not None else 0,
                "interpretation_annee_N1": interpretation_bancaire_annee_N1,
                
                "score_image_annee_N2": _score_image_path(score_value_bancaire_annee_N2),
                "score_image_annee_N2_base64": _score_image_base64(score_value_bancaire_annee_N2),
                "score_value_annee_N2": score_value_bancaire_annee_N2,
                "score_value_annee_N2_arrondi": round(float(score_value_bancaire_annee_N2)) if score_value_bancaire_annee_N2 is not None else 0,
                "interpretation_annee_N2": interpretation_bancaire_annee_N2,
                
                "url_site": static_base_url,
            },
            "scoring_syscohada": {
                "title_16": "SCORING SYSCOHADA - AVEC BILAN",
                "annee_N": data['annee_n'],
                "annee_N1": data['annee_n1'],
                "annee_N2": data['annee_n2'],
                
                "score_image_annee_N": _score_image_path(score_value_syscohada_annee_N),
                "score_image_annee_N_base64": _score_image_base64(score_value_syscohada_annee_N),
                "score_value_annee_N": score_value_syscohada_annee_N,
                "score_value_annee_N_arrondi": round(float(score_value_syscohada_annee_N)) if score_value_syscohada_annee_N is not None else 0,
                "interpretation_annee_N": interpretation_syscohada_annee_N,
                
                "score_image_annee_N1": _score_image_path(score_value_syscohada_annee_N1),
                "score_image_annee_N1_base64": _score_image_base64(score_value_syscohada_annee_N1),
                "score_value_annee_N1": score_value_syscohada_annee_N1,
                "score_value_annee_N1_arrondi": round(float(score_value_syscohada_annee_N1)) if score_value_syscohada_annee_N1 is not None else 0,
                "interpretation_annee_N1": interpretation_syscohada_annee_N1,
                
                "score_image_annee_N2": _score_image_path(score_value_syscohada_annee_N2),
                "score_image_annee_N2_base64": _score_image_base64(score_value_syscohada_annee_N2),
                "score_value_annee_N2": score_value_syscohada_annee_N2,
                "score_value_annee_N2_arrondi": round(float(score_value_syscohada_annee_N2)) if score_value_syscohada_annee_N2 is not None else 0,
                "interpretation_annee_N2": interpretation_syscohada_annee_N2,
                
                "url_site": static_base_url,
            },
            "scoring_ifrs": {
                "title_16": "SCORING IFRS COBAC - AVEC BILAN",
                "annee_N": data['annee_n'],
                "annee_N1": data['annee_n1'],
                "annee_N2": data['annee_n2'],
                
                "score_image_annee_N": _score_image_path(score_value_ifrs_annee_N),
                "score_image_annee_N_base64": _score_image_base64(score_value_ifrs_annee_N),
                "score_value_annee_N": score_value_ifrs_annee_N,
                "score_value_annee_N_arrondi": round(float(score_value_ifrs_annee_N)) if score_value_ifrs_annee_N is not None else 0,
                "interpretation_annee_N": interpretation_ifrs_annee_N,
                
                "score_image_annee_N1": _score_image_path(score_value_ifrs_annee_N1),
                "score_image_annee_N1_base64": _score_image_base64(score_value_ifrs_annee_N1),
                "score_value_annee_N1": score_value_ifrs_annee_N1,
                "score_value_annee_N1_arrondi": round(float(score_value_ifrs_annee_N1)) if score_value_ifrs_annee_N1 is not None else 0,
                "interpretation_annee_N1": interpretation_ifrs_annee_N1,
                
                "score_image_annee_N2": _score_image_path(score_value_ifrs_annee_N2),
                "score_image_annee_N2_base64": _score_image_base64(score_value_ifrs_annee_N2),
                "score_value_annee_N2": score_value_ifrs_annee_N2,
                "score_value_annee_N2_arrondi": round(float(score_value_ifrs_annee_N2)) if score_value_ifrs_annee_N2 is not None else 0,
                "interpretation_annee_N2": interpretation_ifrs_annee_N2,
                
                "url_site": static_base_url,
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
                    "local": condition_achat.local if condition_achat and condition_achat.local else "Non spécifié",
                    "importation": condition_achat.importation if condition_achat and condition_achat.importation else "Non spécifié",
                    "les_clients": condition_achat.les_clients if condition_achat and condition_achat.les_clients else "Non spécifié",
                    "fournisseur": condition_achat.fournisseur if condition_achat and condition_achat.fournisseur else "Non spécifié",
                },
                "conditions_vente": {
                    "local": condition_vente.local if condition_vente and condition_vente.local else "Non spécifié",
                    "recouvrement_dette_jugement": condition_vente_recouvrement,
                    "comportement_de_paiement": condition_vente_comportement,
                }
            },
            "conclusion_generale": {
                "title": "CONCLUSION GENERALE",
                "couleur_commentaire": conclusion_generale.couleur_commentaire.couleur if conclusion_generale and conclusion_generale.couleur_commentaire else "Non spécifié",
                "commentaire": conclusion_generale.commentaire if conclusion_generale and conclusion_generale.commentaire else "Aucun commentaire disponible",
            }
        }
        
        # Retourner les données pour affichage dans le template
        return Response({
            'status': 'success',
            'message': 'Rapport généré avec succès',
            'report_data': _to_json_safe(report_data),
            'form_data': _to_json_safe(data)
        })
    
    return Response(serializer.errors, status=400)



def generate_code_reference():
    date_du_jour = datetime.now().strftime("%Y%m%d")  # ex : 20241204
    chiffre_aleatoire = random.randint(10000, 99999)  # 5 chiffres aléatoires
    codeReference = f"{date_du_jour}.{chiffre_aleatoire}"
    return codeReference


def _safe_download_filename(name, default='rapport_solvabilite'):
    """
    Nettoie un nom de fichier pour éviter les erreurs d'en-têtes HTTP
    (caractères spéciaux, slash, espaces multiples, etc.).
    """
    value = str(name or '').strip()
    if not value:
        return default

    normalized = unicodedata.normalize('NFKD', value)
    ascii_value = normalized.encode('ascii', 'ignore').decode('ascii')
    cleaned = re.sub(r'[^A-Za-z0-9._-]+', '_', ascii_value).strip('._-')
    return cleaned or default


def _extract_country_for_filename(report_data):
    identification = report_data.get('identification', {}) if isinstance(report_data, dict) else {}
    acremac_address = identification.get('acremac_address', {}) if isinstance(identification, dict) else {}
    acremac_info = identification.get('acremac_info', {}) if isinstance(identification, dict) else {}

    country_raw = (
        acremac_address.get('pays')
        or acremac_info.get('pays')
        or identification.get('pays')
        or 'gabon'
    )
    return _safe_download_filename(str(country_raw).lower(), default='gabon')


def _build_export_filename(report_data, acheteur_id, extension):
    date_part = timezone.localtime().strftime('%d_%m_%Y')
    country_part = _extract_country_for_filename(report_data)
    try:
        acheteur_part = str(int(acheteur_id))
    except (TypeError, ValueError):
        acheteur_part = 'inconnu'
    unique_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    ext = str(extension or '').lower().strip('.')
    return f'rapport_{date_part}_{country_part}_acheteur_{acheteur_part}_code_{unique_code}.{ext}'


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def exporter_rapport(request):
    """
    Vue principale pour exporter le rapport
    """
    try:
        data = request.data
        report_data = data.get('report_data', {})
        form_data = data.get('form_data', {})
        export_format = data.get('export_format', 'pdf').lower()
        acheteur_id = data.get('acheteur_id')
        report_data = _inject_static_urls(report_data, request)
        
        print(f"📤 Export demandé: {export_format}")
        print(f"📊 Données reçues - Clés: {list(report_data.keys())}")
        print(f"📝 Form data - Clés: {list(form_data.keys())}")
        
        if export_format.upper() == 'PDF':
            print("Génération du PDF...")  # Debug
            # Rendre le template HTML
            html_string = render_to_string('main/report_html_standalone_pdf.html', report_data)
            
            # Générer le PDF en mémoire
            pdf_file = HTML(string=html_string, base_url=_get_weasy_base_url(request)).write_pdf()
            
            # Préparer la réponse HTTP
            response = HttpResponse(pdf_file, content_type='application/pdf')
            pdf_filename = _build_export_filename(report_data, acheteur_id, 'pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            response['Content-Length'] = len(pdf_file)
            
            return response
        elif export_format.upper() == 'JSON':
            response = exporter_json(report_data, form_data, request)
            json_filename = _build_export_filename(report_data, acheteur_id, 'json')
            response['Content-Disposition'] = f'attachment; filename="{json_filename}"'
            return response
        elif export_format.upper() == 'XML':
            logger.info("Génération du XML...")

            try:
                response = generate_xml_v2(report_data)
                xml_filename = _build_export_filename(report_data, acheteur_id, 'xml')
                response['Content-Disposition'] = f'attachment; filename="{xml_filename}"'
                logger.info("XML généré avec succès")
                return response

            except Exception as e:
                logger.error(f"Erreur lors de la génération XML : {str(e)}")

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
                xml_filename = _build_export_filename(report_data, acheteur_id, 'xml')
                response['Content-Disposition'] = f'attachment; filename="{xml_filename}"'
                return response
        elif export_format.upper() == 'HTML':
            print("Génération du HTML...")  # Debug
            response = generate_report_html_standalone(report_data)
            html_filename = _build_export_filename(report_data, acheteur_id, 'html')
            response['Content-Disposition'] = f'attachment; filename="{html_filename}"'
            return response
        else:
            print("Génération du JSON...")  # Debug
            print(report_data)  # Debug
            response = exporter_json(report_data, form_data, request)
            json_filename = _build_export_filename(report_data, acheteur_id, 'json')
            response['Content-Disposition'] = f'attachment; filename="{json_filename}"'
            return response
    except Exception as e:
        print(f"Erreur : {str(e)}")  # Debug
        return Response(
            {"error": f"Erreur lors de la génération du rapport : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def exporter_rapport_two(request):
    """
    Vue principale pour exporter le rapport
    """
    try:
        data = request.data
        report_data = data.get('report_data', {})
        form_data = data.get('form_data', {})
        export_format = data.get('export_format', 'pdf').lower()
        
        print(f"📤 Export demandé: {export_format}")
        print(f"📊 Données reçues - Clés: {list(report_data.keys())}")
        print(f"📝 Form data - Clés: {list(form_data.keys())}")
        
        if not report_data:
            return Response({'error': 'Aucune donnée de rapport fournie'}, status=400)
        
        # Utiliser la fonction unifiée d'export avec la requête
        return exporter_rapport_unifie(request, report_data, form_data, export_format)
        
    except Exception as e:
        print(f"❌ Erreur lors de l'export: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Erreur lors de l\'export: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def exporter_rapport_version1(request):
    """
    Vue pour exporter le rapport dans différents formats
    """
    try:
        data = request.data
        report_data = data.get('report_data', {})
        form_data = data.get('form_data', {})
        export_format = data.get('export_format', 'pdf').lower()
        
        print(f"📤 Export demandé: {export_format}")
        
        if not report_data:
            return Response({'error': 'Aucune donnée de rapport fournie'}, status=400)
        
        # Nom du fichier
        nom_acheteur = report_data.get('identification', {}).get('acremac_info', {}).get('nom', 'rapport')
        # Nettoyer le nom du fichier
        nom_acheteur = ''.join(c for c in nom_acheteur if c.isalnum() or c in (' ', '-', '_')).strip()
        nom_acheteur = nom_acheteur.replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nom_fichier = f"rapport_solvabilite_{nom_acheteur}_{timestamp}"
        
        if export_format == 'pdf':
            return generer_pdf_weasyprint(report_data, form_data, nom_fichier, request=request)
        elif export_format == 'html':
            return generer_html_standalone(report_data, form_data, nom_fichier)
        elif export_format == 'xml':
            return generer_xml(report_data, nom_fichier)
        elif export_format == 'json':
            return generer_json(report_data, nom_fichier)
        else:
            return Response({'error': f'Format {export_format} non supporté'}, status=400)
            
    except Exception as e:
        print(f"❌ Erreur lors de l'export: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': f'Erreur lors de l\'export: {str(e)}'}, status=500)



def generer_pdf_weasyprint(report_data, form_data, nom_fichier, request=None):
    try:
        report_data = _inject_static_urls(report_data, request)
        
        print("Génération du PDF...")  # Debug
        # Rendre le template HTML
        html_string = render_to_string('main/report_html_standalone_pdf.html', report_data)
        
        # Générer le PDF en mémoire
        pdf_file = HTML(string=html_string, base_url=_get_weasy_base_url(request)).write_pdf()
        
        # Préparer la réponse HTTP
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="rapport_solvabilite.pdf"'
        response['Content-Length'] = len(pdf_file)
        
        return response
    
    except Exception as e:
        print(f"Erreur : {str(e)}")  # Debug
        return Response(
            {"error": f"Erreur lors de la génération du rapport : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



def generer_pdf_weasyprint_two(report_data, form_data, nom_fichier, request=None):
    """Générer un PDF avec WeasyPrint optimisé"""
    try:
        report_data = _inject_static_urls(report_data, request)
        print("📄 Début génération PDF...")
        
        # VÉRIFICATION CRITIQUE: Assurez-vous que report_data n'est pas None
        if not report_data or not isinstance(report_data, dict):
            print("❌ Données de rapport invalides pour PDF")
            raise ValueError("Données de rapport invalides")
        
        # 1. GÉRER LE LOGO - Convertir en base64
        logo_base64 = None
        logo_paths = [
            os.path.join(settings.STATIC_ROOT, 'images', 'acremac_option.png'),
            os.path.join(settings.BASE_DIR, 'main', 'static', 'images', 'acremac_option.png'),
            os.path.join(settings.BASE_DIR, 'static', 'images', 'acremac_option.png'),
        ]
        
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                print(f"✅ Logo trouvé: {logo_path}")
                try:
                    with open(logo_path, "rb") as image_file:
                        logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                    break
                except Exception as e:
                    print(f"❌ Erreur lecture logo: {e}")
                    continue
        
        if not logo_base64:
            print("⚠️ Logo non trouvé, utilisation d'un placeholder")
            # Créer un placeholder simple
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (200, 60), color='#003366')
            d = ImageDraw.Draw(img)
            d.text((10, 20), "ACREMAC", fill=(255, 255, 255))
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            logo_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # 2. PRÉPARER LE CONTEXTE - Assurez-vous d'avoir toutes les données
        context = {
            'report_data': report_data,
            'form_data': form_data or {},
            'logo_base64': logo_base64,
            'STATIC_URL': settings.STATIC_URL,
            'debug': settings.DEBUG,
        }
        
        print(f"📋 Contexte préparé. Sections dans report_data: {list(report_data.keys())}")
        
        # 3. RENDRE LE TEMPLATE
        html_string = render_to_string('main/report_html_standalone.html', context)
        
        # Vérifier que le HTML n'est pas vide
        if not html_string or len(html_string) < 100:
            raise ValueError("Le template HTML est vide ou trop court")
        
        # 4. CRÉER UN FICHIER HTML TEMPORAIRE POUR DÉBOGAGE (optionnel)
        if settings.DEBUG:
            debug_dir = os.path.join(settings.BASE_DIR, 'debug_pdf')
            os.makedirs(debug_dir, exist_ok=True)
            debug_html_path = os.path.join(debug_dir, f'{nom_fichier}_debug.html')
            with open(debug_html_path, 'w', encoding='utf-8') as f:
                f.write(html_string)
            print(f"📝 HTML de débogage sauvegardé: {debug_html_path}")
        
        # 5. CONVERTIR EN PDF
        print("🔄 Conversion HTML vers PDF...")
        
        # Créer un fichier temporaire pour le PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            tmp_pdf_path = tmp_pdf.name
        
        try:
            # Configuration WeasyPrint
            base_url = _get_weasy_base_url(request)
            
            # Convertir HTML en PDF
            HTML(
                string=html_string,
                base_url=base_url
            ).write_pdf(tmp_pdf_path)
            
            # Lire le PDF généré
            with open(tmp_pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Supprimer le fichier temporaire
            os.unlink(tmp_pdf_path)
            
            print(f"✅ PDF généré avec succès! Taille: {len(pdf_content)} bytes")
            
            # 7. CRÉER LA RÉPONSE
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{nom_fichier}.pdf"'
            response['Content-Length'] = len(pdf_content)
            
            return response
            
        except Exception as pdf_error:
            print(f"❌ Erreur lors de la conversion PDF: {pdf_error}")
            import traceback
            traceback.print_exc()
            
            # Fallback: retourner le HTML pour débogage
            response = HttpResponse(html_string, content_type='text/html')
            response['Content-Disposition'] = f'inline; filename="{nom_fichier}_debug.html"'
            return response
            
    except Exception as e:
        print(f"❌ Erreur génération PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Retourner une erreur simple
        error_html = f"""
        <html>
        <head><title>Erreur PDF</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h1 style="color: #d32f2f;">Erreur lors de la génération du PDF</h1>
            <h3>Détails de l'erreur:</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px;">{str(e)}</pre>
            <h3>Solutions possibles:</h3>
            <ol>
                <li>Vérifier que WeasyPrint est installé: <code>pip install weasyprint</code></li>
                <li>Sur Windows, installer GTK+ Runtime</li>
                <li>Utiliser l'export HTML à la place</li>
            </ol>
            <p><a href="#" onclick="window.history.back()">← Retour</a></p>
        </body>
        </html>
        """
        
        return HttpResponse(error_html, content_type='text/html')



def generer_html_standalone(report_data, form_data, nom_fichier):
    """Générer un fichier HTML autonome avec tous les styles intégrés"""
    try:
        # Préparer le contexte
        context = {
            'report_data': report_data,
            'form_data': form_data,
            'is_standalone': True,  # Flag pour le template
        }
        
        # Utiliser un template spécifique pour HTML autonome
        html_content = render_to_string('main/report_html_standalone.html', context)
        
        response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}.html"'
        response['Content-Length'] = len(html_content.encode('utf-8'))
        
        return response
        
    except Exception as e:
        print(f"❌ Erreur génération HTML: {str(e)}")
        return Response({'error': f'Erreur génération HTML: {str(e)}'}, status=500)



def generer_xml(report_data, nom_fichier):
    """Générer un fichier XML structuré"""
    try:
        def dict_to_xml(tag, d, parent=None):
            """Convertir un dictionnaire en éléments XML"""
            if parent is None:
                elem = ET.Element(tag)
            else:
                elem = ET.SubElement(parent, tag)
            
            for key, val in d.items():
                # Nettoyer la clé pour qu'elle soit valide en XML
                clean_key = key.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
                clean_key = clean_key.replace('.', '_').replace('[', '').replace(']', '')
                
                if isinstance(val, dict):
                    dict_to_xml(clean_key, val, elem)
                elif isinstance(val, list):
                    list_elem = ET.SubElement(elem, f"{clean_key}_list")
                    for idx, item in enumerate(val):
                        if isinstance(item, dict):
                            dict_to_xml('item', item, list_elem)
                        else:
                            item_elem = ET.SubElement(list_elem, 'item')
                            item_elem.text = str(item) if item is not None else ''
                elif val is None:
                    child = ET.SubElement(elem, clean_key)
                    child.text = ''
                else:
                    child = ET.SubElement(elem, clean_key)
                    # Gérer les types spéciaux
                    if isinstance(val, (datetime, date)):
                        child.text = val.isoformat()
                    elif isinstance(val, Decimal):
                        child.text = str(float(val))
                    else:
                        child.text = str(val)
            return elem
        
        def clean_data_for_xml(data):
            """Nettoyer les données pour XML"""
            if isinstance(data, dict):
                return {key: clean_data_for_xml(value) for key, value in data.items()}
            elif isinstance(data, list):
                return [clean_data_for_xml(item) for item in data]
            elif isinstance(data, (datetime, date)):
                return data.isoformat()
            elif isinstance(data, Decimal):
                return float(data)
            elif hasattr(data, '__dict__'):
                return {
                    key: clean_data_for_xml(value)
                    for key, value in data.__dict__.items()
                    if not key.startswith('_')
                }
            else:
                return data
        
        # Nettoyer les données
        cleaned_data = clean_data_for_xml(report_data)
        
        # Créer la racine XML
        root = dict_to_xml('rapport_solvabilite', cleaned_data)
        
        # Créer un arbre XML
        tree = ET.ElementTree(root)
        
        # Générer la chaîne XML avec en-tête et indentation
        ET.indent(tree, space="  ", level=0)
        
        # Utiliser tostring avec encoding unicode
        xml_string = ET.tostring(root, encoding='unicode', method='xml')
        
        # Ajouter l'en-tête XML
        xml_content = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_string}'
        
        response = HttpResponse(xml_content, content_type='application/xml; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}.xml"'
        response['Content-Length'] = len(xml_content.encode('utf-8'))
        
        return response
        
    except Exception as e:
        print(f"❌ Erreur génération XML: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': f'Erreur génération XML: {str(e)}'}, status=500)



def generer_json(report_data, nom_fichier):
    """Générer un fichier JSON formaté"""
    try:
        # Fonction pour nettoyer les données avant sérialisation
        def clean_data_for_json(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            elif isinstance(obj, Decimal):
                return float(obj)
            elif hasattr(obj, '__dict__'):
                # Pour les objets Django
                return {
                    key: clean_data_for_json(value)
                    for key, value in obj.__dict__.items()
                    if not key.startswith('_')
                }
            elif isinstance(obj, dict):
                return {key: clean_data_for_json(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [clean_data_for_json(item) for item in obj]
            elif obj is None:
                return None
            else:
                return str(obj)
        
        # Nettoyer les données
        cleaned_data = clean_data_for_json(report_data)
        
        # Convertir en JSON avec une belle indentation
        json_content = json.dumps(
            cleaned_data, 
            ensure_ascii=False, 
            indent=2,
            cls=DjangoJSONEncoder  # Utiliser l'encodeur Django
        )
        
        response = HttpResponse(json_content, content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}.json"'
        response['Content-Length'] = len(json_content.encode('utf-8'))
        
        return response
        
    except Exception as e:
        print(f"❌ Erreur génération JSON: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'error': f'Erreur génération JSON: {str(e)}'}, status=500)
    
    
    
def exporter_rapport_unifie(request, report_data, form_data, export_format):
    """
    Fonction unifiée pour exporter dans tous les formats
    """
    try:
        print(f"🔄 Début export {export_format.upper()}...")
        print(f"📋 Données reçues - Sections: {list(report_data.keys())}")
        
        # 1. Préparer les données pour être compatible avec le module 1
        data_complete = preparer_donnees_pour_export(report_data, form_data, export_format)
        data_complete = _inject_static_urls(data_complete, request)
        
        # 2. Sélectionner le bon format
        format_lower = export_format.lower()
        
        if format_lower == 'pdf':
            return exporter_pdf(data_complete, form_data, request)
        elif format_lower == 'html':
            return exporter_html(data_complete, form_data, request)
        elif format_lower == 'xml':
            return exporter_xml(data_complete, form_data, request)
        elif format_lower == 'json':
            return exporter_json(data_complete, form_data, request)
        else:
            from rest_framework.response import Response
            from rest_framework import status
            return Response(
                {"error": f"Format {export_format} non supporté"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        print(f"❌ Erreur export: {str(e)}")
        import traceback
        traceback.print_exc()
        
        from rest_framework.response import Response
        from rest_framework import status
        return Response(
            {"error": f"Erreur lors de l'export: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



def preparer_donnees_pour_export(report_data, form_data, export_format):
    """
    Prépare les données dans le format attendu par le module 1
    """
    print("🔧 Préparation des données pour l'export...")
    
    # Commencez avec les données existantes
    data_complete = report_data.copy()
    
    # Sections obligatoires pour le module 1
    sections_requises = [
        'header_report',
        'footer_report', 
        'identification',
        'executive_summary',
        'summary_and_opinion',
        'acremac_opinion',
        'registered_data',
        'legal_background',
        'management',
        'commande'
    ]
    
    # Vérifiez et ajoutez les sections manquantes
    for section in sections_requises:
        if section not in data_complete:
            print(f"⚠️ Section manquante: {section}")
            data_complete[section] = {}
    
    # Assurez-vous d'avoir header_report avec tous les champs nécessaires
    if 'header_report' not in data_complete or not data_complete['header_report']:
        data_complete['header_report'] = {
            "acremac_services": "Services ACREMAC",
            "acremac_mail": "credit.report@acremac.com",
            "date_today": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "bilan_report": form_data.get('type_bilan', 'Classique').upper(),
            "format_report": export_format.upper(),
            "language_report": "français" if form_data.get('langue', 'fr') == 'fr' else "english"
        }
    else:
        # Complétez les champs manquants dans header_report existant
        header = data_complete['header_report']
        if 'acremac_services' not in header:
            header['acremac_services'] = "Services ACREMAC"
        if 'acremac_mail' not in header:
            header['acremac_mail'] = "credit.report@acremac.com"
        if 'date_today' not in header:
            header['date_today'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        if 'bilan_report' not in header:
            header['bilan_report'] = form_data.get('type_bilan', 'Classique').upper()
    
    # Assurez-vous d'avoir footer_report
    if 'footer_report' not in data_complete or not data_complete['footer_report']:
        data_complete['footer_report'] = {
            "footer_text_1": "Nos informations sont confidentielles et ne peuvent être divulguées sous peine de dommages-intérêts.",
            "footer_text_2": "Acremac s'engage à mettre en œuvre avec diligence les ",
            "footer_text_3": "moyens à sa disposition sans être liée par une obligation de résultat."
        }
    
    # Assurez-vous d'avoir identification avec acremac_info
    if 'identification' in data_complete:
        ident = data_complete['identification']
        if 'acremac_info' not in ident:
            ident['acremac_info'] = {}
        
        acremac_info = ident['acremac_info']
        if 'nom' not in acremac_info:
            acremac_info['nom'] = "Nom inconnu"
        if 'email' not in acremac_info:
            acremac_info['email'] = "email@inconnu.com"
    else:
        data_complete['identification'] = {
            "acremac_info": {
                "nom": "Nom inconnu",
                "email": "email@inconnu.com"
            }
        }
    
    print(f"✅ Données préparées - Sections: {list(data_complete.keys())}")
    return data_complete      
        
    
        
def exporter_pdf_old(report_data, form_data, request=None):
    """
    Export PDF en réutilisant la fonction du module 1
    """
    try:
        print("📄 Début génération PDF...")
        report_data = _inject_static_urls(report_data, request)
        
        # Si request n'est pas fourni, créez un objet request minimal
        if request is None:
            from django.http import HttpRequest
            request = HttpRequest()
            request.META['SERVER_NAME'] = 'localhost'
            request.META['SERVER_PORT'] = '8000'
        
        # Utilisez la fonction qui fonctionne déjà dans views_report.py
        from django.template.loader import render_to_string
        from weasyprint import HTML
        from django.http import HttpResponse
        
        # Rendre le template HTML
        html_string = render_to_string('main/report_deep_seek_test.html', report_data)
        
        # Générer le PDF en mémoire
        pdf_file = HTML(string=html_string, base_url=_get_weasy_base_url(request)).write_pdf()
        
        # Préparer la réponse HTTP
        response = HttpResponse(pdf_file, content_type='application/pdf')
        nom_acheteur = report_data.get('identification', {}).get('acremac_info', {}).get('nom', 'acheteur')
        safe_nom = _safe_download_filename(nom_acheteur, default='acheteur')
        filename = f"rapport_solvabilite_{safe_nom}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(pdf_file)
        
        print(f"✅ PDF généré: {len(pdf_file)} bytes")
        return response
        
    except Exception as e:
        print(f"❌ Erreur PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Retourner une réponse d'erreur
        from rest_framework.response import Response
        from rest_framework import status
        return Response(
            {"error": f"Erreur lors de la génération du PDF: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



def exporter_html_old(report_data, form_data, request=None):
    """
    Export HTML en réutilisant la fonction du module 1
    """
    try:
        print("🌐 Début génération HTML...")
        report_data = _inject_static_urls(report_data, request)
        
        from django.template.loader import render_to_string
        from django.http import HttpResponse

        # Template HTML dédié (même structure globale, gestion d'image risque spécifique web)
        html_content = render_to_string('main/report_html_standalone_html.html', report_data)
        
        response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
        nom_acheteur = report_data.get('identification', {}).get('acremac_info', {}).get('nom', 'acheteur')
        safe_nom = _safe_download_filename(nom_acheteur, default='acheteur')
        filename = f"rapport_solvabilite_{safe_nom}.html"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        print(f"✅ HTML généré: {len(html_content)} caractères")
        return response
        
    except Exception as e:
        print(f"❌ Erreur HTML: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # HTML d'erreur
        html_content = f"""
        <html>
            <head><title>Erreur Rapport</title></head>
            <body>
                <h1>Erreur lors de la génération du rapport HTML</h1>
                <p>{str(e)}</p>
            </body>
        </html>
        """
        
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = 'attachment; filename="rapport_erreur.html"'
        return response



def exporter_xml_old(report_data, form_data, request=None):
    """
    Export XML en utilisant la fonction qui fonctionne déjà dans le module 1
    """
    try:
        print("📤 Début génération XML + XSD...")
        
        # Utiliser directement la fonction du module 1 qui fonctionne
        from main.api.views_report import generate_xml_with_xsd
        response = generate_xml_with_xsd(report_data)
        
        print("✅ XML + XSD généré avec succès")
        return response
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération XML/XSD : {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Créer un XML d'erreur propre
        error_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<erreur>
    <message>Erreur lors de la génération du rapport XML</message>
    <details>{str(e)}</details>
    <timestamp>{datetime.now().isoformat()}</timestamp>
</erreur>'''
        
        from django.http import HttpResponse
        response = HttpResponse(
            error_xml, 
            content_type='application/xml; charset=utf-8',
            status=500
        )
        response['Content-Disposition'] = 'attachment; filename="rapport_erreur.xml"'
        return response



def exporter_json_old(report_data, form_data, request=None):
    """
    Export JSON
    """
    try:
        print("📊 Début génération JSON...")
        
        # Nettoyer les données pour JSON
        def clean_for_json(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            elif isinstance(obj, Decimal):
                return float(obj)
            elif hasattr(obj, '__dict__'):
                return {k: clean_for_json(v) for k, v in obj.__dict__.items() 
                        if not k.startswith('_')}
            elif isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            else:
                return obj
        
        cleaned_data = clean_for_json(report_data)
        json_content = json.dumps(cleaned_data, ensure_ascii=False, indent=2)
        
        from django.http import HttpResponse
        response = HttpResponse(json_content, content_type='application/json; charset=utf-8')
        nom_acheteur = report_data.get('identification', {}).get('acremac_info', {}).get('nom', 'acheteur')
        safe_nom = _safe_download_filename(nom_acheteur, default='acheteur')
        filename = f"rapport_solvabilite_{safe_nom}.json"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        print(f"✅ JSON généré: {len(json_content)} caractères")
        return response
        
    except Exception as e:
        print(f"❌ Erreur JSON: {str(e)}")
        import traceback
        traceback.print_exc()
        
        from rest_framework.response import Response
        from rest_framework import status
        return Response(
            {"error": f"Erreur lors de la génération du JSON: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    """
    Export JSON
    """
    try:
        # Nettoyer les données pour JSON
        def clean_for_json(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            elif isinstance(obj, Decimal):
                return float(obj)
            elif hasattr(obj, '__dict__'):
                return {k: clean_for_json(v) for k, v in obj.__dict__.items() 
                        if not k.startswith('_')}
            elif isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            else:
                return obj
        
        cleaned_data = clean_for_json(report_data)
        json_content = json.dumps(cleaned_data, ensure_ascii=False, indent=2)
        
        response = HttpResponse(json_content, content_type='application/json; charset=utf-8')
        nom_acheteur = report_data.get('identification', {}).get('acremac_info', {}).get('nom', 'acheteur')
        safe_nom = _safe_download_filename(nom_acheteur, default='acheteur')
        filename = f"rapport_solvabilite_{safe_nom}.json"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        print(f"❌ Erreur JSON: {str(e)}")
        return Response(
            {"error": f"Erreur lors de la génération du JSON: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
               
        
def generate_report_html_standalone(report_data):
    """Génère un rapport HTML complet et le force en téléchargement"""
    try:
        # Utiliser le template HTML dédié
        html_content = render_to_string('main/report_html_standalone_html.html', report_data)
        
        # Créer une réponse HTTP avec le contenu HTML
        response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
        
        # Forcer le téléchargement avec Content-Disposition
        acheteur_nom = report_data.get("identification", {}).get("acremac_info", {}).get("nom", "acheteur")
        safe_nom = _safe_download_filename(acheteur_nom, default='acheteur')
        response['Content-Disposition'] = f'attachment; filename="rapport_solvabilite_{safe_nom}.html"'
        
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
        response = HttpResponse(html_content, content_type='text/html; charset=utf-8', status=500)
        response['Content-Disposition'] = 'attachment; filename="rapport_erreur.html"'
        return response



def exporter_pdf(report_data, form_data, request=None):
    try:
        print("📄 Début génération PDF...")
        report_data = _inject_static_urls(report_data, request)
        
        if request is None:
            from django.http import HttpRequest
            request = HttpRequest()
            request.META['SERVER_NAME'] = 'localhost'
            request.META['SERVER_PORT'] = '8000'
        
        from django.template.loader import render_to_string
        from weasyprint import HTML
        from django.http import HttpResponse
        
        html_string = render_to_string('main/report_html_standalone_pdf.html', report_data)
        pdf_file = HTML(string=html_string, base_url=_get_weasy_base_url(request)).write_pdf()
        
        response = HttpResponse(pdf_file, content_type='application/pdf')
        
        # ✅ AMÉLIORATION : Inclure l'ID de la commande dans le nom
        nom_acheteur = report_data.get('identification', {}).get('acremac_info', {}).get('nom', 'acheteur')
        safe_nom = _safe_download_filename(nom_acheteur, default='acheteur')
        
        # Récupérer l'ID de la commande depuis form_data
        commande_id = form_data.get('commande_id', '')
        
        # Ajouter timestamp pour garantir l'unicité
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"rapport_solvabilite_{safe_nom}_cmd{commande_id}_{timestamp}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(pdf_file)
        
        print(f"✅ PDF généré: {filename} ({len(pdf_file)} bytes)")
        return response
        
    except Exception as e:
        print(f"❌ Erreur PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        
        from rest_framework.response import Response
        from rest_framework import status
        return Response(
            {"error": f"Erreur lors de la génération du PDF: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        
def exporter_html(report_data, form_data, request=None):
    try:
        print("🌐 Début génération HTML...")
        report_data = _inject_static_urls(report_data, request)
        
        from django.template.loader import render_to_string
        from django.http import HttpResponse

        html_content = render_to_string('main/report_html_standalone_html.html', report_data)
        
        response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
        
        # ✅ AMÉLIORATION : Inclure l'ID de la commande dans le nom
        nom_acheteur = report_data.get('identification', {}).get('acremac_info', {}).get('nom', 'acheteur')
        safe_nom = _safe_download_filename(nom_acheteur, default='acheteur')
        
        # Récupérer l'ID de la commande depuis form_data
        commande_id = form_data.get('commande_id', '')
        
        # Ajouter timestamp pour garantir l'unicité
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"rapport_solvabilite_{safe_nom}_cmd{commande_id}_{timestamp}.html"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        print(f"✅ HTML généré: {filename} ({len(html_content)} caractères)")
        return response
        
    except Exception as e:
        print(f"❌ Erreur HTML: {str(e)}")
        import traceback
        traceback.print_exc()
        
        html_content = f"""
        <html>
            <head><title>Erreur Rapport</title></head>
            <body>
                <h1>Erreur lors de la génération du rapport HTML</h1>
                <p>{str(e)}</p>
            </body>
        </html>
        """
        
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = 'attachment; filename="rapport_erreur.html"'
        return response
    
    
    

def exporter_xml(report_data, form_data, request=None):
    try:
        print("📤 Début génération XML + XSD...")
        
        from main.api.views_report import generate_xml_with_xsd
        response = generate_xml_with_xsd(report_data)
        
        # ✅ AMÉLIORATION : Renommer le fichier avec un meilleur format
        nom_acheteur = report_data.get('identification', {}).get('acremac_info', {}).get('nom', 'acheteur')
        safe_nom = _safe_download_filename(nom_acheteur, default='acheteur')
        commande_id = form_data.get('commande_id', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"rapport_solvabilite_{safe_nom}_cmd{commande_id}_{timestamp}.zip"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        print(f"✅ XML généré: {filename}")
        return response
        
    except Exception as e:
        print(f"❌ Erreur XML: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
        <erreur>
            <message>Erreur lors de la génération du rapport XML</message>
            <details>{str(e)}</details>
            <timestamp>{datetime.now().isoformat()}</timestamp>
        </erreur>'''
        
        from django.http import HttpResponse
        response = HttpResponse(
            error_xml, 
            content_type='application/xml; charset=utf-8',
            status=500
        )
        response['Content-Disposition'] = 'attachment; filename="rapport_erreur.xml"'
        return response


def exporter_json(report_data, form_data, request=None):
    try:
        print("📊 Début génération JSON...")
        
        def clean_for_json(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            elif isinstance(obj, Decimal):
                return float(obj)
            elif hasattr(obj, '__dict__'):
                return {k: clean_for_json(v) for k, v in obj.__dict__.items() 
                        if not k.startswith('_')}
            elif isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            else:
                return obj
        
        cleaned_data = clean_for_json(report_data)
        json_content = json.dumps(cleaned_data, ensure_ascii=False, indent=2)
        
        from django.http import HttpResponse
        response = HttpResponse(json_content, content_type='application/json; charset=utf-8')
        
        # ✅ AMÉLIORATION : Inclure l'ID de la commande dans le nom
        nom_acheteur = report_data.get('identification', {}).get('acremac_info', {}).get('nom', 'acheteur')
        safe_nom = _safe_download_filename(nom_acheteur, default='acheteur')
        commande_id = form_data.get('commande_id', '')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filename = f"rapport_solvabilite_{safe_nom}_cmd{commande_id}_{timestamp}.json"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        print(f"✅ JSON généré: {filename} ({len(json_content)} caractères)")
        return response
        
    except Exception as e:
        print(f"❌ Erreur JSON: {str(e)}")
        import traceback
        traceback.print_exc()
        
        from rest_framework.response import Response
        from rest_framework import status
        return Response(
            {"error": f"Erreur lors de la génération du JSON: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )