from django import template
from django.urls import reverse

register = template.Library()

# Séquence ordonnée de toutes les pages d'un acheteur
ACHETEUR_PAGES = [
    ('resume',               'dash_root_manage_acheteur_resume',              'Résumé'),
    ('tendance',             'dash_root_manage_acheteur_tendance',            'Tendance'),
    ('sommaire_avis',        'dash_root_manage_acheteur_sommaire_avis',       'Sommaire & Avis'),
    ('geopolitic',           'dash_root_manage_acheteur_geopolitic',          'Géopolitiques'),
    ('analyse_sectorielle',  'dash_root_manage_acheteur_analyse_sectorielle', 'Analyse sectorielle'),
    ('opinion_acremac',      'dash_root_manage_acheteur_opinion_acremac',     'Opinion crédit'),
    ('risk_rating',          'dash_root_manage_acheteur_risk_rating',         'Évaluation du risque'),
    ('gestion_risque',       'dash_root_manage_acheteur_gestion_risque',      'Management du risque'),
    ('scoring',              'dash_root_manage_acheteur_scoring',             'Scoring sans bilan'),
    ('scoring_with_bilan',   'dash_root_manage_acheteur_scoring_with_bilan',  'Scoring avec bilan'),
    ('scoring_manuel',       'dash_root_manage_acheteur_scoring_manuel',      'Scoring manuel'),
    ('scoring_delphi',       'dash_root_manage_acheteur_scoring_delphi',      'Score Delphi'),
    ('scoring_rating',       'dash_root_manage_acheteur_scoring_rating',      'Score Rating'),
    ('acx',                  'dash_root_manage_acheteur_acx',                 'Vérification ACX'),
    ('advice',               'dash_root_manage_acheteur_advice',              'Conseils'),
    ('membre_conseil',       'dash_root_manage_acheteur_membre_conseil',      'Conseil d\'administration'),
    ('composition_capital',  'dash_root_manage_acheteur_composition_capital', 'Capital social'),
    ('actionnaire',          'dash_root_manage_acheteur_actionnaire',         'Actionnaires'),
    ('filiale',              'dash_root_manage_acheteur_filiale_optimized',   'Filiales & Branches'),
    ('antecedent',           'dash_root_manage_acheteur_antecedent',          'Antécédents'),
    ('responsable',          'dash_root_manage_acheteur_responsable',         'Responsables'),
    ('compte_financier',     'dash_root_manage_acheteur_compte_financier',    'Comptes financiers'),
    ('banking',              'dash_root_manage_acheteur_banking_optimized',   'Données bancaires'),
    ('data_save',            'dash_root_manage_acheteur_data_save',           'Données enregistrées'),
    ('operation_historique', 'dash_root_manage_acheteur_operation_historique','Opérations & Historique'),
    ('condition_achat',      'dash_root_manage_acheteur_condition_achat',     'Conditions d\'achat'),
    ('condition_vente',      'dash_root_manage_acheteur_condition_vente',     'Conditions de vente'),
    ('propriete_actif',      'dash_root_manage_acheteur_propriete_actif',     'Propriétés & Actifs'),
]

_PAGE_INDEX = {key: i for i, (key, _, _) in enumerate(ACHETEUR_PAGES)}


@register.inclusion_tag('main/root/acheteur/_page_navigation.html', takes_context=True)
def acheteur_page_nav(context, current_page):
    acheteur = context.get('acheteur')
    acheteur_id = acheteur.id if acheteur else None
    idx = _PAGE_INDEX.get(current_page)

    prev_data = next_data = None
    if idx is not None:
        if idx > 0:
            key, url_name, label = ACHETEUR_PAGES[idx - 1]
            prev_data = {'url': reverse(url_name, args=[acheteur_id]), 'label': label}
        if idx < len(ACHETEUR_PAGES) - 1:
            key, url_name, label = ACHETEUR_PAGES[idx + 1]
            next_data = {'url': reverse(url_name, args=[acheteur_id]), 'label': label}

    return {'prev': prev_data, 'next': next_data}
