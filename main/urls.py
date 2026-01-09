# main/urls.py
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from main.api.views_acheteur import *
from main.api.views_authentication import *

from main.api.views_bilans_bancaires import *
from main.api.views_bilans_irfs_cobac import *
from main.api.views_bilans_classiques import *
from main.api.views_bilans_sysohada import *
from main.api.views_bilans_anglais import *

from main.api.views_commande import *
from main.api.views_localisation import *
from main.api.views_modele import *
from main.api.views_modules_acheteur import *
from main.api.views_monitoring import *
from main.api.views_standard import *
from main.api.views_users import *
from main.api.views_warning import *
from main.api.views_account import *
from main.api.views_report import *
from main.api.views_reporting import *
from main.api.views_api_load_data import *
from main.views import *
from main.api.views_scoring import (
    ScoringSansBilanAcheteurDetailView,
    FormeJuridiqueScoringListView,
    ModeleComportementPaiementScoringListView,
    ModeleAgeSocieteScoringListView,
    ModeleAvisCommercialScoringListView,
    ModeleBailScoringListView,
    CategoryNaceCodeScoringListView,
    calculer_score_acrema_bilan,
    calculer_score_direct,
    historique_scores_acheteur
)
from main.api.views_scoring_classique import *
from main.api.views_scoring_anglais import *
from main.api.views_scoring_bancaire import *
from main.api.views_scoring_syscohada import *
from main.api.views_scoring_ifrs import *
from main.api.views_solvency_reporting_system import *
from main.api.views_reporting import *
from main.api.views_api_emailling import *
from main.api.views_bucrep3 import *

# from .views import PaysViewSet


# router = DefaultRouter()
# router.register(r'pays', PaysViewSet, basename='pays')

urlpatterns = [
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES START FOR TRANSLATION                                                                                    #
    #                                                                                                                      #
    ########################################################################################################################
    path(
        "i18n/", include("django.conf.urls.i18n")
    ),  # Vue intégrée pour changer de langue
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES END FOR AUTH                                                                                             #
    #                                                                                                                      #
    ########################################################################################################################
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES END FOR TRANSLATION                                                                                      #
    #                                                                                                                      #
    ########################################################################################################################
    path("", index, name="index"),
    path("login/", index, name="index"),
    path("verification/compte/", check_auth, name="check_auth"),
    path("mot-de-passe-oublie/", forgot_auth, name="forgot_auth"),
    path("reinitialisation-mot-de-passe-oublie/", reset_auth, name="reset_auth"),
    path("generate-admin/", new_admin, name="new_admin"),
    path("report-modele/", report_modele, name="report_modele"),
    path("report-template/", report, name="report"),
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES END FOR AUTH                                                                                             #
    #                                                                                                                      #
    ########################################################################################################################
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES START FOR ROOT                                                                                           #
    #                                                                                                                      #
    ########################################################################################################################
    path("root-dashboard/", dash_root, name="dash_root"),
    path("root-dashboard/profile/", dash_root_profile_page, name="dash_root_profile_page"),
    path(
        "root-dashboard/localisation/liste-des-pays",
        dash_root_pays,
        name="dash_root_pays",
    ),
    path(
        "root-dashboard/localisation/liste-des-provinces",
        dash_root_province,
        name="dash_root_province",
    ),
    path(
        "root-dashboard/localisation/liste-des-villes",
        dash_root_ville,
        name="dash_root_ville",
    ),
    path(
        "root-dashboard/utilisateurs/liste-des-utilisateurs",
        dash_root_user,
        name="dash_root_user",
    ),
    path(
        "root-dashboard/standard/liste-des-devises",
        dash_root_devise,
        name="dash_root_devise",
    ),
    path(
        "root-dashboard/standard/liste-des-annees-civiles",
        dash_root_annee,
        name="dash_root_annee",
    ),
    path(
        "root-dashboard/standard/liste-des-colorations",
        dash_root_coloration,
        name="dash_root_coloration",
    ),
    path(
        "root-dashboard/standard/liste-des-categories-nace",
        dash_root_category_nace,
        name="dash_root_category_nace",
    ),
    path(
        "root-dashboard/standard/liste-des-categories-naf",
        dash_root_category_naf,
        name="dash_root_category_naf",
    ),
    path(
        "root-dashboard/standard/liste-des-codes-nace",
        dash_root_code_nace,
        name="dash_root_code_nace",
    ),
    path(
        "root-dashboard/standard/liste-des-codes-naf",
        dash_root_code_naf,
        name="dash_root_code_naf",
    ),
    path(
        "root-dashboard/standard/liste-des-formes-juridiques",
        dash_root_forme_juridique,
        name="dash_root_forme_juridique",
    ),
    path(
        "root-dashboard/standard/liste-des-domaines",
        dash_root_domaine,
        name="dash_root_domaine",
    ),
    path(
        "root-dashboard/standard/liste-des-postes",
        dash_root_poste,
        name="dash_root_poste",
    ),
    path(
        "root-dashboard/standard/liste-des-categories-entreprise",
        dash_root_category_entreprise,
        name="dash_root_category_entreprise",
    ),
    path(
        "root-dashboard/standard/liste-des-structures-entreprise",
        dash_root_structure_entreprise,
        name="dash_root_structure_entreprise",
    ),
    path(
        "root-dashboard/standard/liste-des-status-entreprise",
        dash_root_statut_entreprise,
        name="dash_root_statut_entreprise",
    ),
    path(
        "root-dashboard/nomenclature/liste-des-modeles-de-bail",
        dash_root_modele_bail,
        name="dash_root_modele_bail",
    ),
    path(
        "root-dashboard/nomenclature/liste-des-modeles-de-bilan",
        dash_root_modele_bilan,
        name="dash_root_modele_bilan",
    ),
    path(
        "root-dashboard/nomenclature/liste-des-modeles-alarme",
        dash_root_modele_alarme,
        name="dash_root_modele_alarme",
    ),
    path(
        "root-dashboard/nomenclature/liste-des-modeles-de-rapport",
        dash_root_modele_rapport,
        name="dash_root_modele_rapport",
    ),
    path(
        "root-dashboard/nomenclature/liste-des-modeles-avis-commercial",
        dash_root_modele_avis_commercial,
        name="dash_root_modele_avis_commercial",
    ),
    path(
        "root-dashboard/nomenclature/liste-des-modeles-de-relation-entreprise",
        dash_root_modele_relation_entreprise,
        name="dash_root_modele_relation_entreprise",
    ),
    path(
        "root-dashboard/nomenclature/liste-des-modeles-de-notation",
        dash_root_modele_notation,
        name="dash_root_modele_notation",
    ),
    path(
        "root-dashboard/nomenclature/liste-des-modeles-de-comportement-paiement",
        dash_root_modele_comportement_paiement,
        name="dash_root_modele_comportement_paiement",
    ),
    path(
        "root-dashboard/nomenclature/liste-des-modeles-de-comportement-jugement",
        dash_root_modele_comportement_jugement,
        name="dash_root_modele_comportement_jugement",
    ),
    path(
        "root-dashboard/nomenclature/liste-des-modeles-ages-societe",
        dash_root_modele_age_societe,
        name="dash_root_modele_age_societe",
    ),
    path(
        "root-dashboard/nomenclature/liste-des-modeles-information-notation-entreprise",
        dash_root_modele_information_notation_entreprise,
        name="dash_root_modele_information_notation_entreprise",
    ),
    path(
        "root-dashboard/acheteurs/liste-des-acheteurs",
        dash_root_acheteur,
        name="dash_root_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/ajouter-un-acheteur",
        dash_root_add_acheteur,
        name="dash_root_add_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/editer-un-acheteur/<int:acheteur_id>/",
        dash_root_edit_acheteur,
        name="dash_root_edit_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/",
        dash_root_manage_acheteur,
        name="dash_root_manage_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/resumes/",
        dash_root_manage_acheteur_resume,
        name="dash_root_manage_acheteur_resume",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/evaluation-risques/",
        dash_root_manage_acheteur_risk_rating,
        name="dash_root_manage_acheteur_risk_rating",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/donnees-enregistrees/",
        dash_root_manage_acheteur_data_save,
        name="dash_root_manage_acheteur_data_save",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/tendances/",
        dash_root_manage_acheteur_tendance,
        name="dash_root_manage_acheteur_tendance",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/responsables/",
        dash_root_manage_acheteur_responsable,
        name="dash_root_manage_acheteur_responsable",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/antecedents-juridiques/",
        dash_root_manage_acheteur_antecedent,
        name="dash_root_manage_acheteur_antecedent",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/gestion-des-risques/",
        dash_root_manage_acheteur_gestion_risque,
        name="dash_root_manage_acheteur_gestion_risque",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/membres-du-conseil/",
        dash_root_manage_acheteur_membre_conseil,
        name="dash_root_manage_acheteur_membre_conseil",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/compositions-du-capital-social/",
        dash_root_manage_acheteur_composition_capital,
        name="dash_root_manage_acheteur_composition_capital",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/actionnaires/",
        dash_root_manage_acheteur_actionnaire,
        name="dash_root_manage_acheteur_actionnaire",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/opinions-acremac/",
        dash_root_manage_acheteur_opinion_acremac,
        name="dash_root_manage_acheteur_opinion_acremac",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/filiales/",
        dash_root_manage_acheteur_filiale_optimized,
        name="dash_root_manage_acheteur_filiale_optimized",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/analyses-sectorielles/",
        dash_root_manage_acheteur_analyse_sectorielle,
        name="dash_root_manage_acheteur_analyse_sectorielle",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/comptes-financiers/",
        dash_root_manage_acheteur_compte_financier,
        name="dash_root_manage_acheteur_compte_financier",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/operations-et-historiques/",
        dash_root_manage_acheteur_operation_historique,
        name="dash_root_manage_acheteur_operation_historique",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/proprietes-et-actifs/",
        dash_root_manage_acheteur_propriete_actif,
        name="dash_root_manage_acheteur_propriete_actif",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conditions-achat/",
        dash_root_manage_acheteur_condition_achat,
        name="dash_root_manage_acheteur_condition_achat",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conditions-vente/",
        dash_root_manage_acheteur_condition_vente,
        name="dash_root_manage_acheteur_condition_vente",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/sommaires-et-avis/",
        dash_root_manage_acheteur_sommaire_avis,
        name="dash_root_manage_acheteur_sommaire_avis",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conseils/",
        dash_root_manage_acheteur_advice,
        name="dash_root_manage_acheteur_advice",
    ),
    
    
    
    
    
    
    
    
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/geopolitiques/",
        dash_root_manage_acheteur_geopolitic,
        name="dash_root_manage_acheteur_geopolitic",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/donnees-bancaires/",
        dash_root_manage_acheteur_banking_optimized,
        name="dash_root_manage_acheteur_banking_optimized",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/certifications/",
        dash_root_certification_acheteur,
        name="dash_root_certification_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/innovations-et-developement/",
        dash_root_innovation_acheteur,
        name="dash_root_innovation_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/strategies-et-planifications/",
        dash_root_strategie_acheteur,
        name="dash_root_strategie_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conformites-et-reglementations/",
        dash_root_conformite_acheteur,
        name="dash_root_conformite_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-anglais/actifs/",
        dash_root_manage_acheteur_actif_anglais,
        name="dash_root_manage_acheteur_actif_anglais",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-anglais/passifs/",
        dash_root_manage_acheteur_passif_anglais,
        name="dash_root_manage_acheteur_passif_anglais",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-anglais/resultats/",
        dash_root_manage_acheteur_resultat_anglais,
        name="dash_root_manage_acheteur_resultat_anglais",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-classique/actifs/",
        dash_root_manage_acheteur_actif_classique,
        name="dash_root_manage_acheteur_actif_classique",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-classique/passifs/",
        dash_root_manage_acheteur_passif_classique,
        name="dash_root_manage_acheteur_passif_classique",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-classique/resultats/",
        dash_root_manage_acheteur_resultat_classique,
        name="dash_root_manage_acheteur_resultat_classique",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-syscohada/actifs/",
        dash_root_manage_acheteur_actif_syscohada,
        name="dash_root_manage_acheteur_actif_syscohada",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-syscohada/passifs/",
        dash_root_manage_acheteur_passif_syscohada,
        name="dash_root_manage_acheteur_passif_syscohada",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-syscohada/resultats/",
        dash_root_manage_acheteur_resultat_syscohada,
        name="dash_root_manage_acheteur_resultat_syscohada",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/actifs/",
        dash_root_manage_acheteur_asset_bancaire,
        name="dash_root_manage_acheteur_asset_bancaire",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/modules-bancaires/",
        dash_root_manage_acheteur_bilan_actif_bancaire,
        name="dash_root_manage_acheteur_bilan_actif_bancaire",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs-cobac/modules-irfs-cobac/",
        dash_root_manage_acheteur_bilan_irfs_cobac,
        name="dash_root_manage_acheteur_bilan_irfs_cobac",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/passifs/",
        dash_root_manage_acheteur_liabilitie_bancaire,
        name="dash_root_manage_acheteur_liabilitie_bancaire",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/depenses/",
        dash_root_manage_acheteur_expense_bancaire,
        name="dash_root_manage_acheteur_expense_bancaire",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/produits/",
        dash_root_manage_acheteur_product_bancaire,
        name="dash_root_manage_acheteur_product_bancaire",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/donnees-hors-bilan/",
        dash_root_manage_acheteur_offbalancesheet_bancaire,
        name="dash_root_manage_acheteur_offbalancesheet_bancaire",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/comptes-financiers/",
        dash_root_manage_acheteur_compte_financier_irfs,
        name="dash_root_manage_acheteur_compte_financier_irfs",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/ratios-financiers/",
        dash_root_manage_acheteur_ratio_financier_irfs,
        name="dash_root_manage_acheteur_ratio_financier_irfs",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/liste-des-actifs/",
        dash_root_manage_acheteur_actif_irfs,
        name="dash_root_manage_acheteur_actif_irfs",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/ajouter-un-actif/",
        dash_root_manage_acheteur_add_actif_irfs,
        name="dash_root_manage_acheteur_add_actif_irfs",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/liste-des-passifs/",
        dash_root_manage_acheteur_passif_irfs,
        name="dash_root_manage_acheteur_passif_irfs",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/ajouter-un-passif/",
        dash_root_manage_acheteur_add_passif_irfs,
        name="dash_root_manage_acheteur_add_passif_irfs",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/rapport-version-web/",
        dash_root_manage_acheteur_report_web,
        name="dash_root_manage_acheteur_report_web",
    ),
    path(
        "root-dashboard/commandes/liste-des-commandes",
        dash_root_commande,
        name="dash_root_commande",
    ),
    path(
        "root-dashboard/commandes/manager-une-commande/<int:commande_id>/",
        dash_root_manage_commande,
        name="dash_root_manage_commande",
    ),
    path(
        "root-dashboard/warnings/liste-des-alertes/",
        dash_root_alerte,
        name="dash_root_alerte",
    ),
    path(
        "root-dashboard/warnings/ajouter-une-alerte/etape-1/",
        dash_root_add_alerte,
        name="dash_root_add_alerte",
    ),
    path(
        "root-dashboard/warnings/ajouter-une-alerte/etape-1/<slug:reference>/",
        dash_root_edit_new_alerte,
        name="dash_root_edit_new_alerte",
    ),
    path(
        "root-dashboard/warnings/ajouter-une-alerte/etape-2/<slug:reference>/",
        dash_root_document_alerte,
        name="dash_root_document_alerte",
    ),
    path(
        "root-dashboard/warnings/ajouter-une-alerte/etape-3/<slug:reference>/",
        dash_root_client_alerte,
        name="dash_root_client_alerte",
    ),
    path(
        "root-dashboard/warnings/editer-une-alerte/<int:alerte_id>/",
        dash_root_edit_alerte,
        name="dash_root_edit_alerte",
    ),
    path(
        "root-dashboard/warnings/manager-une-alerte/<int:alerte_id>/",
        dash_root_manage_alerte,
        name="dash_root_manage_alerte",
    ),
    path(
        "root-dashboard/monitoring/liste-des-clients/",
        dash_root_client,
        name="dash_root_client",
    ),
    path(
        "root-dashboard/monitoring/carnet-adresses/",
        dash_root_carnet,
        name="dash_root_carnet",
    ),
    path(
        "root-dashboard/monitoring/liste-des-portefeuilles/",
        dash_root_portefeuille,
        name="dash_root_portefeuille",
    ),
    path(
        "root-dashboard/monitoring/ajouter-un-portefeuille/",
        dash_root_add_portefeuille,
        name="dash_root_add_portefeuille",
    ),
    path(
        "root-dashboard/monitoring/editer-une-portefeuille/<int:portefeuille_id>/",
        dash_root_edit_portefeuille,
        name="dash_root_edit_portefeuille",
    ),
    path(
        "root-dashboard/simulateurs/scoring-sans-bilan/",
        dash_root_simulateur_scoring_sb,
        name="dash_root_simulateur_scoring_sb",
    ),
    path(
        "root-dashboard/elements-de-surveillance/",
        dash_root_element_surveillance,
        name="dash_root_element_surveillance",
    ),
    path(
        "root-dashboard/monitoring/alertes-log/",
        dash_root_alerte_log,
        name="dash_root_alerte_log",
    ),
    
    
    
    
    
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/marques/",
        dash_root_manage_marque_acheteur,
        name="dash_root_manage_marque_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/produits-services/",
        dash_root_manage_produit_service_acheteur,
        name="dash_root_manage_produit_service_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/cotisations/",
        dash_root_manage_cotisation_acheteur,
        name="dash_root_manage_cotisation_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/swot/",
        dash_root_manage_swot_acheteur,
        name="dash_root_manage_swot_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/registre-commerce/",
        dash_root_manage_registre_commerce_acheteur,
        name="dash_root_manage_registre_commerce_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/procedures-collectives/",
        dash_root_manage_procedure_collective_acheteur,
        name="dash_root_manage_procedure_collective_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/documents/",
        dash_root_manage_document_acheteur,
        name="dash_root_manage_document_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/adresses/",
        dash_root_manage_adresse_acheteur,
        name="dash_root_manage_adresse_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/portables/",
        dash_root_manage_portable_acheteur,
        name="dash_root_manage_portable_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/telephones/",
        dash_root_manage_telephone_acheteur,
        name="dash_root_manage_telephone_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/emails/",
        dash_root_manage_email_acheteur,
        name="dash_root_manage_email_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/codes-nace/",
        dash_root_manage_code_nace_acheteur,
        name="dash_root_manage_code_nace_acheteur",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/codes-naf/",
        dash_root_manage_code_naf_acheteur,
        name="dash_root_manage_code_naf_acheteur",
    ),
    # --- URL pour la gestion du Bilan Classique ---
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-classique/",
        dash_root_manage_acheteur_bilan_classique,
        name="dash_root_manage_acheteur_bilan_classique",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-syscohada/",
        dash_root_manage_acheteur_bilan_syscohada,
        name="dash_root_manage_acheteur_bilan_syscohada",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-anglais/",
        dash_root_manage_acheteur_bilan_anglais,
        name="dash_root_manage_acheteur_bilan_anglais",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/scoring-sans-bilan/",
        dash_root_manage_acheteur_scoring,
        name="dash_root_manage_acheteur_scoring",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/scoring-avec-bilan/",
        dash_root_manage_acheteur_scoring_with_bilan,
        name="dash_root_manage_acheteur_scoring_with_bilan",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/gestion-des-rapports/",
        dash_root_manage_acheteur_report_solvency,
        name="dash_root_manage_acheteur_report_solvency",
    ),
    path(
        "root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/gestion-des-emails/",
        dash_root_manage_acheteur_emailling,
        name="dash_root_manage_acheteur_emailling",
    ),
    path(
        "root-dashboard/acheteurs/rapports/envoi-des-emails/",
        dash_root_manage_report_mailing,
        name="dash_root_manage_report_mailing",
    ),
    path(
        "root-dashboard/sauvegardes/",
        dash_root_manage_backup,
        name="dash_root_manage_backup",
    ),
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES END FOR ROOT                                                                                             #
    #                                                                                                                      #
    ########################################################################################################################
    
    
    
    
    
    
    
    
    
    
    
    
    
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES START FOR VALIDATEUR                                                                                     #
    #                                                                                                                      #
    ########################################################################################################################
    
    path("validateur-dashboard/", dash_validateur, name="dash_validateur"),
    path(
        "validateur-dashboard/localisation/liste-des-pays",
        dash_validateur_pays,
        name="dash_validateur_pays",
    ),
    path(
        "validateur-dashboard/localisation/liste-des-provinces",
        dash_validateur_province,
        name="dash_validateur_province",
    ),
    path(
        "validateur-dashboard/localisation/liste-des-villes",
        dash_validateur_ville,
        name="dash_validateur_ville",
    ),
    path(
        "validateur-dashboard/utilisateurs/liste-des-utilisateurs",
        dash_validateur_user,
        name="dash_validateur_user",
    ),
    path(
        "validateur-dashboard/standard/liste-des-devises",
        dash_validateur_devise,
        name="dash_validateur_devise",
    ),
    path(
        "validateur-dashboard/standard/liste-des-annees-civiles",
        dash_validateur_annee,
        name="dash_validateur_annee",
    ),
    path(
        "validateur-dashboard/standard/liste-des-colorations",
        dash_validateur_coloration,
        name="dash_validateur_coloration",
    ),
    path(
        "validateur-dashboard/standard/liste-des-categories-nace",
        dash_validateur_category_nace,
        name="dash_validateur_category_nace",
    ),
    path(
        "validateur-dashboard/standard/liste-des-categories-naf",
        dash_validateur_category_naf,
        name="dash_validateur_category_naf",
    ),
    path(
        "validateur-dashboard/standard/liste-des-codes-nace",
        dash_validateur_code_nace,
        name="dash_validateur_code_nace",
    ),
    path(
        "validateur-dashboard/standard/liste-des-codes-naf",
        dash_validateur_code_naf,
        name="dash_validateur_code_naf",
    ),
    path(
        "validateur-dashboard/standard/liste-des-formes-juridiques",
        dash_validateur_forme_juridique,
        name="dash_validateur_forme_juridique",
    ),
    path(
        "validateur-dashboard/standard/liste-des-domaines",
        dash_validateur_domaine,
        name="dash_validateur_domaine",
    ),
    path(
        "validateur-dashboard/standard/liste-des-postes",
        dash_validateur_poste,
        name="dash_validateur_poste",
    ),
    path(
        "validateur-dashboard/standard/liste-des-categories-entreprise",
        dash_validateur_category_entreprise,
        name="dash_validateur_category_entreprise",
    ),
    path(
        "validateur-dashboard/standard/liste-des-structures-entreprise",
        dash_validateur_structure_entreprise,
        name="dash_validateur_structure_entreprise",
    ),
    path(
        "validateur-dashboard/standard/liste-des-status-entreprise",
        dash_validateur_statut_entreprise,
        name="dash_validateur_statut_entreprise",
    ),
    path(
        "validateur-dashboard/nomenclature/liste-des-modeles-de-bail",
        dash_validateur_modele_bail,
        name="dash_validateur_modele_bail",
    ),
    path(
        "validateur-dashboard/nomenclature/liste-des-modeles-de-bilan",
        dash_validateur_modele_bilan,
        name="dash_validateur_modele_bilan",
    ),
    path(
        "validateur-dashboard/nomenclature/liste-des-modeles-alarme",
        dash_validateur_modele_alarme,
        name="dash_validateur_modele_alarme",
    ),
    path(
        "validateur-dashboard/nomenclature/liste-des-modeles-de-rapport",
        dash_validateur_modele_rapport,
        name="dash_validateur_modele_rapport",
    ),
    path(
        "validateur-dashboard/nomenclature/liste-des-modeles-avis-commercial",
        dash_validateur_modele_avis_commercial,
        name="dash_validateur_modele_avis_commercial",
    ),
    path(
        "validateur-dashboard/nomenclature/liste-des-modeles-de-relation-entreprise",
        dash_validateur_modele_relation_entreprise,
        name="dash_validateur_modele_relation_entreprise",
    ),
    path(
        "validateur-dashboard/nomenclature/liste-des-modeles-de-notation",
        dash_validateur_modele_notation,
        name="dash_validateur_modele_notation",
    ),
    path(
        "validateur-dashboard/nomenclature/liste-des-modeles-de-comportement-paiement",
        dash_validateur_modele_comportement_paiement,
        name="dash_validateur_modele_comportement_paiement",
    ),
    path(
        "validateur-dashboard/nomenclature/liste-des-modeles-de-comportement-jugement",
        dash_validateur_modele_comportement_jugement,
        name="dash_validateur_modele_comportement_jugement",
    ),
    
    
    path(
        "validateur-dashboard/nomenclature/liste-des-modeles-information-notation-entreprise",
        dash_validateur_modele_information_notation_entreprise,
        name="dash_validateur_modele_information_notation_entreprise",
    ),
    path(
        "validateur-dashboard/acheteurs/liste-des-acheteurs",
        dash_validateur_acheteur,
        name="dash_validateur_acheteur",
    ),
    path(
        "validateur-dashboard/acheteurs/ajouter-un-acheteur",
        dash_validateur_add_acheteur,
        name="dash_validateur_add_acheteur",
    ),
    path(
        "validateur-dashboard/acheteurs/editer-un-acheteur/<int:acheteur_id>/",
        dash_validateur_edit_acheteur,
        name="dash_validateur_edit_acheteur",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/",
        dash_validateur_manage_acheteur,
        name="dash_validateur_manage_acheteur",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/resumes/",
        dash_validateur_manage_acheteur_resume,
        name="dash_validateur_manage_acheteur_resume",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/evaluation-risques/",
        dash_validateur_manage_acheteur_risk_rating,
        name="dash_validateur_manage_acheteur_risk_rating",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/donnees-enregistrees/",
        dash_validateur_manage_acheteur_data_save,
        name="dash_validateur_manage_acheteur_data_save",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/tendances/",
        dash_validateur_manage_acheteur_tendance,
        name="dash_validateur_manage_acheteur_tendance",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/responsables/",
        dash_validateur_manage_acheteur_responsable,
        name="dash_validateur_manage_acheteur_responsable",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/antecedents-juridiques/",
        dash_validateur_manage_acheteur_antecedent,
        name="dash_validateur_manage_acheteur_antecedent",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/gestion-des-risques/",
        dash_validateur_manage_acheteur_gestion_risque,
        name="dash_validateur_manage_acheteur_gestion_risque",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/membres-du-conseil/",
        dash_validateur_manage_acheteur_membre_conseil,
        name="dash_validateur_manage_acheteur_membre_conseil",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/compositions-du-capital-social/",
        dash_validateur_manage_acheteur_composition_capital,
        name="dash_validateur_manage_acheteur_composition_capital",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/actionnaires/",
        dash_validateur_manage_acheteur_actionnaire,
        name="dash_validateur_manage_acheteur_actionnaire",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/opinions-acremac/",
        dash_validateur_manage_acheteur_opinion_acremac,
        name="dash_validateur_manage_acheteur_opinion_acremac",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/filiales/",
        dash_validateur_manage_acheteur_filiale,
        name="dash_validateur_manage_acheteur_filiale",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/analyses-sectorielles/",
        dash_validateur_manage_acheteur_analyse_sectorielle,
        name="dash_validateur_manage_acheteur_analyse_sectorielle",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/comptes-financiers/",
        dash_validateur_manage_acheteur_compte_financier,
        name="dash_validateur_manage_acheteur_compte_financier",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/operations-et-historiques/",
        dash_validateur_manage_acheteur_operation_historique,
        name="dash_validateur_manage_acheteur_operation_historique",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/proprietes-et-actifs/",
        dash_validateur_manage_acheteur_propriete_actif,
        name="dash_validateur_manage_acheteur_propriete_actif",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conditions-achat/",
        dash_validateur_manage_acheteur_condition_achat,
        name="dash_validateur_manage_acheteur_condition_achat",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conditions-vente/",
        dash_validateur_manage_acheteur_condition_vente,
        name="dash_validateur_manage_acheteur_condition_vente",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/sommaires-et-avis/",
        dash_validateur_manage_acheteur_sommaire_avis,
        name="dash_validateur_manage_acheteur_sommaire_avis",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conseils/",
        dash_validateur_manage_acheteur_advice,
        name="dash_validateur_manage_acheteur_advice",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/geopolitiques/",
        dash_validateur_manage_acheteur_geopolitic,
        name="dash_validateur_manage_acheteur_geopolitic",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/donnees-bancaires/",
        dash_validateur_manage_acheteur_banking,
        name="dash_validateur_manage_acheteur_banking",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/certifications/",
        dash_validateur_certification_acheteur,
        name="dash_validateur_certification_acheteur",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/innovations-et-developement/",
        dash_validateur_innovation_acheteur,
        name="dash_validateur_innovation_acheteur",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/strategies-et-planifications/",
        dash_validateur_strategie_acheteur,
        name="dash_validateur_strategie_acheteur",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conformites-et-reglementations/",
        dash_validateur_conformite_acheteur,
        name="dash_validateur_conformite_acheteur",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-anglais/actifs/",
        dash_validateur_manage_acheteur_actif_anglais,
        name="dash_validateur_manage_acheteur_actif_anglais",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-anglais/passifs/",
        dash_validateur_manage_acheteur_passif_anglais,
        name="dash_validateur_manage_acheteur_passif_anglais",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-anglais/resultats/",
        dash_validateur_manage_acheteur_resultat_anglais,
        name="dash_validateur_manage_acheteur_resultat_anglais",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-classique/actifs/",
        dash_validateur_manage_acheteur_actif_classique,
        name="dash_validateur_manage_acheteur_actif_classique",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-classique/passifs/",
        dash_validateur_manage_acheteur_passif_classique,
        name="dash_validateur_manage_acheteur_passif_classique",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-classique/resultats/",
        dash_validateur_manage_acheteur_resultat_classique,
        name="dash_validateur_manage_acheteur_resultat_classique",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-syscohada/actifs/",
        dash_validateur_manage_acheteur_actif_syscohada,
        name="dash_validateur_manage_acheteur_actif_syscohada",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-syscohada/passifs/",
        dash_validateur_manage_acheteur_passif_syscohada,
        name="dash_validateur_manage_acheteur_passif_syscohada",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-syscohada/resultats/",
        dash_validateur_manage_acheteur_resultat_syscohada,
        name="dash_validateur_manage_acheteur_resultat_syscohada",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/actifs/",
        dash_validateur_manage_acheteur_asset_bancaire,
        name="dash_validateur_manage_acheteur_asset_bancaire",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/modules-bancaires/",
        dash_validateur_manage_acheteur_bilan_actif_bancaire,
        name="dash_validateur_manage_acheteur_bilan_actif_bancaire",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs-cobac/modules-irfs-cobac/",
        dash_validateur_manage_acheteur_bilan_irfs_cobac,
        name="dash_validateur_manage_acheteur_bilan_irfs_cobac",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/passifs/",
        dash_validateur_manage_acheteur_liabilitie_bancaire,
        name="dash_validateur_manage_acheteur_liabilitie_bancaire",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/depenses/",
        dash_validateur_manage_acheteur_expense_bancaire,
        name="dash_validateur_manage_acheteur_expense_bancaire",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/produits/",
        dash_validateur_manage_acheteur_product_bancaire,
        name="dash_validateur_manage_acheteur_product_bancaire",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/donnees-hors-bilan/",
        dash_validateur_manage_acheteur_offbalancesheet_bancaire,
        name="dash_validateur_manage_acheteur_offbalancesheet_bancaire",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/comptes-financiers/",
        dash_validateur_manage_acheteur_compte_financier_irfs,
        name="dash_validateur_manage_acheteur_compte_financier_irfs",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/ratios-financiers/",
        dash_validateur_manage_acheteur_ratio_financier_irfs,
        name="dash_validateur_manage_acheteur_ratio_financier_irfs",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/liste-des-actifs/",
        dash_validateur_manage_acheteur_actif_irfs,
        name="dash_validateur_manage_acheteur_actif_irfs",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/ajouter-un-actif/",
        dash_validateur_manage_acheteur_add_actif_irfs,
        name="dash_validateur_manage_acheteur_add_actif_irfs",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/liste-des-passifs/",
        dash_validateur_manage_acheteur_passif_irfs,
        name="dash_validateur_manage_acheteur_passif_irfs",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/ajouter-un-passif/",
        dash_validateur_manage_acheteur_add_passif_irfs,
        name="dash_validateur_manage_acheteur_add_passif_irfs",
    ),
    path(
        "validateur-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/rapport-version-web/",
        dash_validateur_manage_acheteur_report_web,
        name="dash_validateur_manage_acheteur_report_web",
    ),
    path(
        "validateur-dashboard/commandes/liste-des-commandes",
        dash_validateur_commande,
        name="dash_validateur_commande",
    ),
    path(
        "validateur-dashboard/commandes/manager-une-commande/<int:commande_id>/",
        dash_validateur_manage_commande,
        name="dash_validateur_manage_commande",
    ),
    path(
        "validateur-dashboard/warnings/liste-des-alertes/",
        dash_validateur_alerte,
        name="dash_validateur_alerte",
    ),
    path(
        "validateur-dashboard/warnings/ajouter-une-alerte/etape-1/",
        dash_validateur_add_alerte,
        name="dash_validateur_add_alerte",
    ),
    path(
        "validateur-dashboard/warnings/ajouter-une-alerte/etape-1/<slug:reference>/",
        dash_validateur_edit_new_alerte,
        name="dash_validateur_edit_new_alerte",
    ),
    path(
        "validateur-dashboard/warnings/ajouter-une-alerte/etape-2/<slug:reference>/",
        dash_validateur_document_alerte,
        name="dash_validateur_document_alerte",
    ),
    path(
        "validateur-dashboard/warnings/ajouter-une-alerte/etape-3/<slug:reference>/",
        dash_validateur_client_alerte,
        name="dash_validateur_client_alerte",
    ),
    path(
        "validateur-dashboard/warnings/editer-une-alerte/<int:alerte_id>/",
        dash_validateur_edit_alerte,
        name="dash_validateur_edit_alerte",
    ),
    path(
        "validateur-dashboard/warnings/manager-une-alerte/<int:alerte_id>/",
        dash_validateur_manage_alerte,
        name="dash_validateur_manage_alerte",
    ),
    path(
        "validateur-dashboard/monitoring/liste-des-clients/",
        dash_validateur_client,
        name="dash_validateur_client",
    ),
    path(
        "validateur-dashboard/monitoring/carnet-adresses/",
        dash_validateur_carnet,
        name="dash_validateur_carnet",
    ),
    path(
        "validateur-dashboard/monitoring/liste-des-portefeuilles/",
        dash_validateur_portefeuille,
        name="dash_validateur_portefeuille",
    ),
    path(
        "validateur-dashboard/monitoring/ajouter-un-portefeuille/",
        dash_validateur_add_portefeuille,
        name="dash_validateur_add_portefeuille",
    ),
    path(
        "validateur-dashboard/monitoring/editer-une-portefeuille/<int:portefeuille_id>/",
        dash_validateur_edit_portefeuille,
        name="dash_validateur_edit_portefeuille",
    ),
    path(
        "validateur-dashboard/simulateurs/scoring-sans-bilan/",
        dash_validateur_simulateur_scoring_sb,
        name="dash_validateur_simulateur_scoring_sb",
    ),
    path(
        "validateur-dashboard/elements-de-surveillance/",
        dash_validateur_element_surveillance,
        name="dash_validateur_element_surveillance",
    ),
    path(
        "validateur-dashboard/monitoring/alertes-log/",
        dash_validateur_alerte_log,
        name="dash_validateur_alerte_log",
    ),
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES END FOR VALIDATEUR                                                                                       #
    #                                                                                                                      #
    ########################################################################################################################
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES START FOR ANALYSTE                                                                                       #
    #                                                                                                                      #
    ########################################################################################################################

    path("analyste-dashboard/", dash_analyste, name="dash_analyste"),
    path(
        "analyste-dashboard/localisation/liste-des-pays",
        dash_analyste_pays,
        name="dash_analyste_pays",
    ),
    path(
        "analyste-dashboard/localisation/liste-des-provinces",
        dash_analyste_province,
        name="dash_analyste_province",
    ),
    path(
        "analyste-dashboard/localisation/liste-des-villes",
        dash_analyste_ville,
        name="dash_analyste_ville",
    ),
    path(
        "analyste-dashboard/utilisateurs/liste-des-utilisateurs",
        dash_analyste_user,
        name="dash_analyste_user",
    ),
    path(
        "analyste-dashboard/standard/liste-des-devises",
        dash_analyste_devise,
        name="dash_analyste_devise",
    ),
    path(
        "analyste-dashboard/standard/liste-des-annees-civiles",
        dash_analyste_annee,
        name="dash_analyste_annee",
    ),
    path(
        "analyste-dashboard/standard/liste-des-colorations",
        dash_analyste_coloration,
        name="dash_analyste_coloration",
    ),
    path(
        "analyste-dashboard/standard/liste-des-categories-nace",
        dash_analyste_category_nace,
        name="dash_analyste_category_nace",
    ),
    path(
        "analyste-dashboard/standard/liste-des-categories-naf",
        dash_analyste_category_naf,
        name="dash_analyste_category_naf",
    ),
    path(
        "analyste-dashboard/standard/liste-des-codes-nace",
        dash_analyste_code_nace,
        name="dash_analyste_code_nace",
    ),
    path(
        "analyste-dashboard/standard/liste-des-codes-naf",
        dash_analyste_code_naf,
        name="dash_analyste_code_naf",
    ),
    path(
        "analyste-dashboard/standard/liste-des-formes-juridiques",
        dash_analyste_forme_juridique,
        name="dash_analyste_forme_juridique",
    ),
    path(
        "analyste-dashboard/standard/liste-des-domaines",
        dash_analyste_domaine,
        name="dash_analyste_domaine",
    ),
    path(
        "analyste-dashboard/standard/liste-des-postes",
        dash_analyste_poste,
        name="dash_analyste_poste",
    ),
    path(
        "analyste-dashboard/standard/liste-des-categories-entreprise",
        dash_analyste_category_entreprise,
        name="dash_analyste_category_entreprise",
    ),
    path(
        "analyste-dashboard/standard/liste-des-structures-entreprise",
        dash_analyste_structure_entreprise,
        name="dash_analyste_structure_entreprise",
    ),
    path(
        "analyste-dashboard/standard/liste-des-status-entreprise",
        dash_analyste_statut_entreprise,
        name="dash_analyste_statut_entreprise",
    ),
    path(
        "analyste-dashboard/nomenclature/liste-des-modeles-de-bail",
        dash_analyste_modele_bail,
        name="dash_analyste_modele_bail",
    ),
    path(
        "analyste-dashboard/nomenclature/liste-des-modeles-de-bilan",
        dash_analyste_modele_bilan,
        name="dash_analyste_modele_bilan",
    ),
    path(
        "analyste-dashboard/nomenclature/liste-des-modeles-alarme",
        dash_analyste_modele_alarme,
        name="dash_analyste_modele_alarme",
    ),
    path(
        "analyste-dashboard/nomenclature/liste-des-modeles-de-rapport",
        dash_analyste_modele_rapport,
        name="dash_analyste_modele_rapport",
    ),
    path(
        "analyste-dashboard/nomenclature/liste-des-modeles-avis-commercial",
        dash_analyste_modele_avis_commercial,
        name="dash_analyste_modele_avis_commercial",
    ),
    path(
        "analyste-dashboard/nomenclature/liste-des-modeles-de-relation-entreprise",
        dash_analyste_modele_relation_entreprise,
        name="dash_analyste_modele_relation_entreprise",
    ),
    path(
        "analyste-dashboard/nomenclature/liste-des-modeles-de-notation",
        dash_analyste_modele_notation,
        name="dash_analyste_modele_notation",
    ),
    path(
        "analyste-dashboard/nomenclature/liste-des-modeles-de-comportement-paiement",
        dash_analyste_modele_comportement_paiement,
        name="dash_analyste_modele_comportement_paiement",
    ),
    path(
        "analyste-dashboard/nomenclature/liste-des-modeles-de-comportement-jugement",
        dash_analyste_modele_comportement_jugement,
        name="dash_analyste_modele_comportement_jugement",
    ),
    path(
        "analyste-dashboard/nomenclature/liste-des-modeles-information-notation-entreprise",
        dash_analyste_modele_information_notation_entreprise,
        name="dash_analyste_modele_information_notation_entreprise",
    ),
    path(
        "analyste-dashboard/acheteurs/liste-des-acheteurs",
        dash_analyste_acheteur,
        name="dash_analyste_acheteur",
    ),
    path(
        "analyste-dashboard/acheteurs/ajouter-un-acheteur",
        dash_analyste_add_acheteur,
        name="dash_analyste_add_acheteur",
    ),
    path(
        "analyste-dashboard/acheteurs/editer-un-acheteur/<int:acheteur_id>/",
        dash_analyste_edit_acheteur,
        name="dash_analyste_edit_acheteur",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/",
        dash_analyste_manage_acheteur,
        name="dash_analyste_manage_acheteur",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/resumes/",
        dash_analyste_manage_acheteur_resume,
        name="dash_analyste_manage_acheteur_resume",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/evaluation-risques/",
        dash_analyste_manage_acheteur_risk_rating,
        name="dash_analyste_manage_acheteur_risk_rating",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/donnees-enregistrees/",
        dash_analyste_manage_acheteur_data_save,
        name="dash_analyste_manage_acheteur_data_save",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/tendances/",
        dash_analyste_manage_acheteur_tendance,
        name="dash_analyste_manage_acheteur_tendance",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/responsables/",
        dash_analyste_manage_acheteur_responsable,
        name="dash_analyste_manage_acheteur_responsable",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/antecedents-juridiques/",
        dash_analyste_manage_acheteur_antecedent,
        name="dash_analyste_manage_acheteur_antecedent",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/gestion-des-risques/",
        dash_analyste_manage_acheteur_gestion_risque,
        name="dash_analyste_manage_acheteur_gestion_risque",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/membres-du-conseil/",
        dash_analyste_manage_acheteur_membre_conseil,
        name="dash_analyste_manage_acheteur_membre_conseil",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/compositions-du-capital-social/",
        dash_analyste_manage_acheteur_composition_capital,
        name="dash_analyste_manage_acheteur_composition_capital",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/actionnaires/",
        dash_analyste_manage_acheteur_actionnaire,
        name="dash_analyste_manage_acheteur_actionnaire",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/opinions-acremac/",
        dash_analyste_manage_acheteur_opinion_acremac,
        name="dash_analyste_manage_acheteur_opinion_acremac",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/filiales/",
        dash_analyste_manage_acheteur_filiale,
        name="dash_analyste_manage_acheteur_filiale",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/analyses-sectorielles/",
        dash_analyste_manage_acheteur_analyse_sectorielle,
        name="dash_analyste_manage_acheteur_analyse_sectorielle",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/comptes-financiers/",
        dash_analyste_manage_acheteur_compte_financier,
        name="dash_analyste_manage_acheteur_compte_financier",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/operations-et-historiques/",
        dash_analyste_manage_acheteur_operation_historique,
        name="dash_analyste_manage_acheteur_operation_historique",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/proprietes-et-actifs/",
        dash_analyste_manage_acheteur_propriete_actif,
        name="dash_analyste_manage_acheteur_propriete_actif",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conditions-achat/",
        dash_analyste_manage_acheteur_condition_achat,
        name="dash_analyste_manage_acheteur_condition_achat",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conditions-vente/",
        dash_analyste_manage_acheteur_condition_vente,
        name="dash_analyste_manage_acheteur_condition_vente",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/sommaires-et-avis/",
        dash_analyste_manage_acheteur_sommaire_avis,
        name="dash_analyste_manage_acheteur_sommaire_avis",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conseils/",
        dash_analyste_manage_acheteur_advice,
        name="dash_analyste_manage_acheteur_advice",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/geopolitiques/",
        dash_analyste_manage_acheteur_geopolitic,
        name="dash_analyste_manage_acheteur_geopolitic",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/donnees-bancaires/",
        dash_analyste_manage_acheteur_banking,
        name="dash_analyste_manage_acheteur_banking",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/certifications/",
        dash_analyste_certification_acheteur,
        name="dash_analyste_certification_acheteur",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/innovations-et-developement/",
        dash_analyste_innovation_acheteur,
        name="dash_analyste_innovation_acheteur",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/strategies-et-planifications/",
        dash_analyste_strategie_acheteur,
        name="dash_analyste_strategie_acheteur",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conformites-et-reglementations/",
        dash_analyste_conformite_acheteur,
        name="dash_analyste_conformite_acheteur",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-anglais/actifs/",
        dash_analyste_manage_acheteur_actif_anglais,
        name="dash_analyste_manage_acheteur_actif_anglais",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-anglais/passifs/",
        dash_analyste_manage_acheteur_passif_anglais,
        name="dash_analyste_manage_acheteur_passif_anglais",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-anglais/resultats/",
        dash_analyste_manage_acheteur_resultat_anglais,
        name="dash_analyste_manage_acheteur_resultat_anglais",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-classique/actifs/",
        dash_analyste_manage_acheteur_actif_classique,
        name="dash_analyste_manage_acheteur_actif_classique",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-classique/passifs/",
        dash_analyste_manage_acheteur_passif_classique,
        name="dash_analyste_manage_acheteur_passif_classique",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-classique/resultats/",
        dash_analyste_manage_acheteur_resultat_classique,
        name="dash_analyste_manage_acheteur_resultat_classique",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-syscohada/actifs/",
        dash_analyste_manage_acheteur_actif_syscohada,
        name="dash_analyste_manage_acheteur_actif_syscohada",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-syscohada/passifs/",
        dash_analyste_manage_acheteur_passif_syscohada,
        name="dash_analyste_manage_acheteur_passif_syscohada",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-syscohada/resultats/",
        dash_analyste_manage_acheteur_resultat_syscohada,
        name="dash_analyste_manage_acheteur_resultat_syscohada",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/actifs/",
        dash_analyste_manage_acheteur_asset_bancaire,
        name="dash_analyste_manage_acheteur_asset_bancaire",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/modules-bancaires/",
        dash_analyste_manage_acheteur_bilan_actif_bancaire,
        name="dash_analyste_manage_acheteur_bilan_actif_bancaire",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs-cobac/modules-irfs-cobac/",
        dash_analyste_manage_acheteur_bilan_irfs_cobac,
        name="dash_analyste_manage_acheteur_bilan_irfs_cobac",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/passifs/",
        dash_analyste_manage_acheteur_liabilitie_bancaire,
        name="dash_analyste_manage_acheteur_liabilitie_bancaire",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/depenses/",
        dash_analyste_manage_acheteur_expense_bancaire,
        name="dash_analyste_manage_acheteur_expense_bancaire",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/produits/",
        dash_analyste_manage_acheteur_product_bancaire,
        name="dash_analyste_manage_acheteur_product_bancaire",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-bancaire/donnees-hors-bilan/",
        dash_analyste_manage_acheteur_offbalancesheet_bancaire,
        name="dash_analyste_manage_acheteur_offbalancesheet_bancaire",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/comptes-financiers/",
        dash_analyste_manage_acheteur_compte_financier_irfs,
        name="dash_analyste_manage_acheteur_compte_financier_irfs",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/ratios-financiers/",
        dash_analyste_manage_acheteur_ratio_financier_irfs,
        name="dash_analyste_manage_acheteur_ratio_financier_irfs",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/liste-des-actifs/",
        dash_analyste_manage_acheteur_actif_irfs,
        name="dash_analyste_manage_acheteur_actif_irfs",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/ajouter-un-actif/",
        dash_analyste_manage_acheteur_add_actif_irfs,
        name="dash_analyste_manage_acheteur_add_actif_irfs",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/liste-des-passifs/",
        dash_analyste_manage_acheteur_passif_irfs,
        name="dash_analyste_manage_acheteur_passif_irfs",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/bilan-irfs/ajouter-un-passif/",
        dash_analyste_manage_acheteur_add_passif_irfs,
        name="dash_analyste_manage_acheteur_add_passif_irfs",
    ),
    path(
        "analyste-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/rapport-version-web/",
        dash_analyste_manage_acheteur_report_web,
        name="dash_analyste_manage_acheteur_report_web",
    ),
    path(
        "analyste-dashboard/commandes/liste-des-commandes",
        dash_analyste_commande,
        name="dash_analyste_commande",
    ),
    path(
        "analyste-dashboard/commandes/manager-une-commande/<int:commande_id>/",
        dash_analyste_manage_commande,
        name="dash_analyste_manage_commande",
    ),
    path(
        "analyste-dashboard/warnings/liste-des-alertes/",
        dash_analyste_alerte,
        name="dash_analyste_alerte",
    ),
    path(
        "analyste-dashboard/warnings/ajouter-une-alerte/etape-1/",
        dash_analyste_add_alerte,
        name="dash_analyste_add_alerte",
    ),
    path(
        "analyste-dashboard/warnings/ajouter-une-alerte/etape-1/<slug:reference>/",
        dash_analyste_edit_new_alerte,
        name="dash_analyste_edit_new_alerte",
    ),
    path(
        "analyste-dashboard/warnings/ajouter-une-alerte/etape-2/<slug:reference>/",
        dash_analyste_document_alerte,
        name="dash_analyste_document_alerte",
    ),
    path(
        "analyste-dashboard/warnings/ajouter-une-alerte/etape-3/<slug:reference>/",
        dash_analyste_client_alerte,
        name="dash_analyste_client_alerte",
    ),
    path(
        "analyste-dashboard/warnings/editer-une-alerte/<int:alerte_id>/",
        dash_analyste_edit_alerte,
        name="dash_analyste_edit_alerte",
    ),
    path(
        "analyste-dashboard/warnings/manager-une-alerte/<int:alerte_id>/",
        dash_analyste_manage_alerte,
        name="dash_analyste_manage_alerte",
    ),
    path(
        "analyste-dashboard/monitoring/liste-des-clients/",
        dash_analyste_client,
        name="dash_analyste_client",
    ),
    path(
        "analyste-dashboard/monitoring/carnet-adresses/",
        dash_analyste_carnet,
        name="dash_analyste_carnet",
    ),
    path(
        "analyste-dashboard/monitoring/liste-des-portefeuilles/",
        dash_analyste_portefeuille,
        name="dash_analyste_portefeuille",
    ),
    path(
        "analyste-dashboard/monitoring/ajouter-un-portefeuille/",
        dash_analyste_add_portefeuille,
        name="dash_analyste_add_portefeuille",
    ),
    path(
        "analyste-dashboard/monitoring/editer-une-portefeuille/<int:portefeuille_id>/",
        dash_analyste_edit_portefeuille,
        name="dash_analyste_edit_portefeuille",
    ),
    path(
        "analyste-dashboard/simulateurs/scoring-sans-bilan/",
        dash_analyste_simulateur_scoring_sb,
        name="dash_analyste_simulateur_scoring_sb",
    ),
    path(
        "analyste-dashboard/elements-de-surveillance/",
        dash_analyste_element_surveillance,
        name="dash_analyste_element_surveillance",
    ),
    path(
        "analyste-dashboard/monitoring/alertes-log/",
        dash_analyste_alerte_log,
        name="dash_analyste_alerte_log",
    ),
    

    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES END FOR ANALYSTE                                                                                         #
    #                                                                                                                      #
    ########################################################################################################################
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES START FOR CLIENT                                                                                         #
    #                                                                                                                      #
    ########################################################################################################################
    path("client-dashboard/", dash_client, name="dash_client"),
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES END FOR CLIENT                                                                                           #
    #                                                                                                                      #
    ########################################################################################################################
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES START                                                                                                    #
    #                                                                                                                      #
    ########################################################################################################################
    # === AUTHENTIFICATION SYSTEME === #
    path("api/login/", CustomLoginView.as_view(), name="api_login"),
    path(
        "api/double-factor-auth/",
        CustomDoubleFactorAuthView.as_view(),
        name="double-factor-auth",
    ),
    path('api/init-session/', SessionInitView.as_view(), name='api_init_session'), # La nouvelle URL
    path(
        "forgot-password/", CustomForgotPasswordView.as_view(), name="forgot-password"
    ),
    path("reset-password/", CustomResetPasswordView.as_view(), name="reset-password"),
    path("api/logout/", CustomLogoutView.as_view(), name="api-logout"),
    path("api/token/refresh/", CustomRefreshTokenView.as_view(), name="token_refresh"),

    # === GRAPHES === #
    path('api/acheteurs-par-mois/', AcheteursParMois.as_view(), name='acheteurs-par-mois'),
    path('api/alertes-par-mois/', AlertesParMois.as_view(), name='alertes-par-mois'),
    path('api/alertelogs-par-mois/', AlerteLogsParMois.as_view(), name='alertelogs-par-mois'),
    path('api/commandes-par-mois/', CommandesParMois.as_view(), name='commandes-par-mois'),


    # === MODULES UTILISATEURS === #
    path(
        "api/liste-des-utilisateurs/",
        ListUtilisateurView.as_view(),
        name="list-utilisateur",
    ),
    path(
        "api/recherche-utilisateur/",
        SearchUtilisateurView.as_view(),
        name="search-utilisateur",
    ),
    path(
        "api/ajouter-une-utilisateur/",
        AddUtilisateurView.as_view(),
        name="add-utilisateur",
    ),
    path(
        "api/editer-une-utilisateur/<int:id>/",
        EditUtilisateurView.as_view(),
        name="edit-utilisateur",
    ),
    path(
        "api/editer-avatar-utilisateur/<int:id>/",
        EditUtilisateurAvatarView.as_view(),
        name="edit-utilisateur-avatar",
    ),
    path('api/supprimer-des-utilisateurs/<int:id>/', DeleteUtilisateurView.as_view(), name='delete-single-user'),
    path('api/supprimer-des-utilisateurs/', DeleteUtilisateurView.as_view(), name='delete-multiple-users'),
    
    # === MODULES STANDARD === #
    path("api/pays-carte/", PaysCarteView.as_view(), name="pays-carte"),
    path('api/pays-statistiques/', PaysStatistiquesView.as_view(), name='pays-statistiques'),
    path("api/liste-des-pays/", ListPaysView.as_view(), name="list-pays"),
    path("api/recherche-pays/", SearchPaysView.as_view(), name="search-pays"),
    path("api/ajouter-un-pays/", AddPaysView.as_view(), name="add-pays"),
    path("api/editer-un-pays/<int:id>/", EditPaysView.as_view(), name="edit-pays"),
    path("api/supprimer-des-pays/", DeletePaysView.as_view(), name="delete-pays"),
    path("api/update-selected-pays/", UpdateSelectedPaysView.as_view(), name="update-selected-pays"),
    path('api/pays-list/', PaysListView.as_view(), name='pays_list'),  # API pour lister les pays
    path(
        "api/liste-des-provinces/", ListProvincesView.as_view(), name="list_provinces"
    ),
    path(
        "api/provinces/<int:country_id>/",
        ListProvincesByCountryView.as_view(),
        name="list-provinces-pays",
    ),
    path("api/ajouter-une-province/", AddProvinceView.as_view(), name="add_province"),
    path(
        "api/editer-une-province/<int:id>/",
        EditProvinceView.as_view(),
        name="edit_province",
    ),
    path(
        "api/supprimer-des-provinces/",
        DeleteProvincesView.as_view(),
        name="delete_provinces",
    ),
    path("api/liste-des-villes/", ListVillesView.as_view(), name="list_villes"),
    path(
        "api/villes/<int:province_id>/",
        ListVillesByProvinceView.as_view(),
        name="list-villes-provinces",
    ),
    path("api/ajouter-une-ville/", AddVilleView.as_view(), name="add_ville"),
    path("api/editer-une-ville/<int:id>/", EditVilleView.as_view(), name="edit_ville"),
    path("api/supprimer-des-villes/", DeleteVillesView.as_view(), name="delete_villes"),
    path("api/liste-des-devises/", ListDeviseView.as_view(), name="list-devise"),
    path("api/recherche-devise/", SearchDeviseView.as_view(), name="search-devise"),
    path("api/ajouter-une-devise/", AddDeviseView.as_view(), name="add-devise"),
    path(
        "api/editer-une-devise/<int:id>/", EditDeviseView.as_view(), name="edit-devise"
    ),
    path(
        "api/supprimer-des-devises/", DeleteDeviseView.as_view(), name="delete-devise"
    ),
    path("api/liste-des-annees-civiles/", ListAnneeView.as_view(), name="list-annee"),
    path(
        "api/liste-des-annees-civiles/simple/",
        ListAnneeViewWithoutPagination.as_view(),
        name="list-annee-simple",
    ),
    path("api/recherche-annee/", SearchAnneeView.as_view(), name="search-annee"),
    path("api/ajouter-une-annee/", AddAnneeView.as_view(), name="add-annee"),
    path("api/editer-une-annee/<int:id>/", EditAnneeView.as_view(), name="edit-annee"),
    path("api/supprimer-des-annees/", DeleteAnneeView.as_view(), name="delete-annee"),
    path(
        "api/liste-des-colorations/",
        ListColorationView.as_view(),
        name="list-coloration",
    ),
    path(
        "api/recherche-coloration/",
        SearchColorationView.as_view(),
        name="search-coloration",
    ),
    path(
        "api/ajouter-une-coloration/",
        AddColorationView.as_view(),
        name="add-coloration",
    ),
    path(
        "api/editer-une-coloration/<int:id>/",
        EditColorationView.as_view(),
        name="edit-coloration",
    ),
    path(
        "api/supprimer-des-colorations/",
        DeleteColorationView.as_view(),
        name="delete-coloration",
    ),
    path(
        "api/liste-des-categories-nace/",
        ListCategoryNaceView.as_view(),
        name="list-categorie-nace",
    ),
    path(
        "api/recherche-categorie-nace/",
        SearchCategoryNaceView.as_view(),
        name="search-categorie-nace",
    ),
    path(
        "api/ajouter-une-categorie-nace/",
        AddCategoryNaceView.as_view(),
        name="add-categorie-nace",
    ),
    path(
        "api/editer-une-categorie-nace/<int:id>/",
        EditCategoryNaceView.as_view(),
        name="edit-categorie-nace",
    ),
    path(
        "api/supprimer-des-categories-nace/",
        DeleteCategoryNaceView.as_view(),
        name="delete-categorie-nace",
    ),
    path(
        "api/liste-des-categories-naf/",
        ListCategoryNafView.as_view(),
        name="list-categorie-naf",
    ),
    path(
        "api/recherche-categorie-naf/",
        SearchCategoryNafView.as_view(),
        name="search-categorie-naf",
    ),
    path(
        "api/ajouter-une-categorie-naf/",
        AddCategoryNafView.as_view(),
        name="add-categorie-naf",
    ),
    path(
        "api/editer-une-categorie-naf/<int:id>/",
        EditCategoryNafView.as_view(),
        name="edit-categorie-naf",
    ),
    path(
        "api/supprimer-des-categories-naf/",
        DeleteCategoryNafView.as_view(),
        name="delete-categorie-naf",
    ),
    path(
        "api/liste-des-codes-nace/", ListCodeNaceView.as_view(), name="list-code-nace"
    ),
    path(
        "api/recherche-codes-nace/",
        SearchCodeNaceView.as_view(),
        name="search-code-nace",
    ),
    path("api/ajouter-un-code-nace/", AddCodeNaceView.as_view(), name="add-code-nace"),
    path(
        "api/editer-un-code-nace/<int:id>/",
        EditCodeNaceView.as_view(),
        name="edit-code-nace",
    ),
    path(
        "api/supprimer-des-codes-nace/",
        DeleteCodeNaceView.as_view(),
        name="delete-code-nace",
    ),
    path("api/liste-des-codes-naf/", ListCodeNafView.as_view(), name="list-code-naf"),
    path(
        "api/recherche-codes-naf/", SearchCodeNafView.as_view(), name="search-code-naf"
    ),
    path("api/ajouter-un-code-naf/", AddCodeNafView.as_view(), name="add-code-naf"),
    path(
        "api/editer-un-code-naf/<int:id>/",
        EditCodeNafView.as_view(),
        name="edit-code-naf",
    ),
    path(
        "api/supprimer-des-codes-naf/",
        DeleteCodeNafView.as_view(),
        name="delete-code-naf",
    ),
    path(
        "api/liste-des-formes-juridiques/",
        ListFormeJuridiqueView.as_view(),
        name="list-forme-juridique",
    ),
    path(
        "api/recherche-forme-juridique/",
        SearchFormeJuridiqueView.as_view(),
        name="search-forme-juridique",
    ),
    path(
        "api/ajouter-une-forme-juridique/",
        AddFormeJuridiqueView.as_view(),
        name="add-forme-juridique",
    ),
    path(
        "api/editer-une-forme-juridique/<int:id>/",
        EditFormeJuridiqueView.as_view(),
        name="edit-forme-juridique",
    ),
    path(
        "api/supprimer-des-formes-juridiques/",
        DeleteFormeJuridiqueView.as_view(),
        name="delete-forme-juridique",
    ),
    path("api/liste-des-domaines/", ListDomaineView.as_view(), name="list-domaine"),
    path("api/recherche-domaine/", SearchDomaineView.as_view(), name="search-domaine"),
    path("api/ajouter-une-domaine/", AddDomaineView.as_view(), name="add-domaine"),
    path(
        "api/editer-une-domaine/<int:id>/",
        EditDomaineView.as_view(),
        name="edit-domaine",
    ),
    path(
        "api/supprimer-des-domaine/", DeleteDomaineView.as_view(), name="delete-domaine"
    ),
    path(
        "api/liste-des-categories-entreprise/",
        ListCategorieEntrepriseView.as_view(),
        name="list-categorie-entreprise",
    ),
    path(
        "api/recherche-categorie-entreprise/",
        SearchCategorieEntrepriseView.as_view(),
        name="search-categorie-entreprise",
    ),
    path(
        "api/ajouter-une-categorie-entreprise/",
        AddCategorieEntrepriseView.as_view(),
        name="add-categorie-entreprise",
    ),
    path(
        "api/editer-une-categorie-entreprise/<int:id>/",
        EditCategorieEntrepriseView.as_view(),
        name="edit-categorie-entreprise",
    ),
    path(
        "api/supprimer-des-categories-entreprise/",
        DeleteCategorieEntrepriseView.as_view(),
        name="delete-categorie-entreprise",
    ),
    path(
        "api/liste-des-structures-entreprise/",
        ListStructureEntrepriseView.as_view(),
        name="list-structure-entreprise",
    ),
    path(
        "api/recherche-structure-entreprise/",
        SearchStructureEntrepriseView.as_view(),
        name="search-structure-entreprise",
    ),
    path(
        "api/ajouter-une-structure-entreprise/",
        AddStructureEntrepriseView.as_view(),
        name="add-structure-entreprise",
    ),
    path(
        "api/editer-une-structure-entreprise/<int:id>/",
        EditStructureEntrepriseView.as_view(),
        name="edit-structure-entreprise",
    ),
    path(
        "api/supprimer-des-structures-entreprise/",
        DeleteStructureEntrepriseView.as_view(),
        name="delete-structure-entreprise",
    ),
    path(
        "api/liste-des-statuts-entreprise/",
        ListStatutEntrepriseView.as_view(),
        name="list-statut-entreprise",
    ),
    path(
        "api/recherche-statut-entreprise/",
        SearchStatutEntrepriseView.as_view(),
        name="search-statut-entreprise",
    ),
    path(
        "api/ajouter-une-statut-entreprise/",
        AddStatutEntrepriseView.as_view(),
        name="add-statut",
    ),
    path(
        "api/editer-une-statut-entreprise/<int:id>/",
        EditStatutEntrepriseView.as_view(),
        name="edit-statut-entreprise",
    ),
    path(
        "api/supprimer-des-statuts-entreprise/",
        DeleteStatutEntrepriseView.as_view(),
        name="delete-statut-entreprise",
    ),
    path("api/liste-des-postes/", ListPosteView.as_view(), name="list-poste"),
    path("api/recherche-poste/", SearchPosteView.as_view(), name="search-poste"),
    path("api/ajouter-une-poste/", AddPosteView.as_view(), name="add-poste"),
    path("api/editer-une-poste/<int:id>/", EditPosteView.as_view(), name="edit-poste"),
    path("api/supprimer-des-postes/", DeletePosteView.as_view(), name="delete-poste"),
    # === MODULES NOMENCLATURE === #
    path(
        "api/liste-des-modeles-de-rapport/",
        ListModeleRapportView.as_view(),
        name="list-modele-de-rapport",
    ),
    path(
        "api/recherche-modele-de-rapport/",
        SearchModeleRapportView.as_view(),
        name="search-modele-de-rapport",
    ),
    path(
        "api/ajouter-un-modele-de-rapport/",
        AddModeleRapportView.as_view(),
        name="add-modele-de-rapport",
    ),
    path(
        "api/editer-un-modele-de-rapport/<int:id>/",
        EditModeleRapportView.as_view(),
        name="edit-modele-de-rapport",
    ),
    path(
        "api/supprimer-des-modeles-de-rapport/",
        DeleteModeleRapportView.as_view(),
        name="delete-modele-de-rapport",
    ),
    path(
        "api/liste-des-modeles-de-bilan/",
        ListModeleBilanView.as_view(),
        name="list-modele-de-bilan",
    ),
    path(
        "api/recherche-modele-de-bilan/",
        SearchModeleBilanView.as_view(),
        name="search-modele-de-bilan",
    ),
    path(
        "api/ajouter-un-modele-de-bilan/",
        AddModeleBilanView.as_view(),
        name="add-modele-de-bilan",
    ),
    path(
        "api/editer-un-modele-de-bilan/<int:id>/",
        EditModeleBilanView.as_view(),
        name="edit-modele-de-bilan",
    ),
    path(
        "api/supprimer-des-modeles-de-bilan/",
        DeleteModeleBilanView.as_view(),
        name="delete-modele-de-bilan",
    ),
    path(
        "api/liste-des-modeles-de-bail/",
        ListModeleBailView.as_view(),
        name="list-modele-de-bail",
    ),
    path(
        "api/recherche-modele-de-bail/",
        SearchModeleBailView.as_view(),
        name="search-modele-de-bail",
    ),
    path(
        "api/ajouter-un-modele-de-bail/",
        AddModeleBailView.as_view(),
        name="add-modele-de-bail",
    ),
    path(
        "api/editer-un-modele-de-bail/<int:id>/",
        EditModeleBailView.as_view(),
        name="edit-modele-de-bail",
    ),
    path(
        "api/supprimer-des-modeles-de-bail/",
        DeleteModeleBailView.as_view(),
        name="delete-modele-de-bail",
    ),
    path(
        "api/liste-des-modeles-de-notation/",
        ListModeleNotationView.as_view(),
        name="list-modele-de-notation",
    ),
    path(
        "api/recherche-modele-de-notation/",
        SearchModeleNotationView.as_view(),
        name="search-modele-de-notation",
    ),
    path(
        "api/ajouter-un-modele-de-notation/",
        AddModeleNotationView.as_view(),
        name="add-modele-de-notation",
    ),
    path(
        "api/editer-un-modele-de-notation/<int:id>/",
        EditModeleNotationView.as_view(),
        name="edit-modele-de-notation",
    ),
    path(
        "api/supprimer-des-modeles-de-notation/",
        DeleteModeleNotationView.as_view(),
        name="delete-modele-de-notation",
    ),
    path(
        "api/liste-des-modeles-alarme/",
        ListModeleAlarmeView.as_view(),
        name="list-modele-alarme",
    ),
    path(
        "api/recherche-modele-alarme/",
        SearchModeleAlarmeView.as_view(),
        name="search-modele-alarme",
    ),
    path(
        "api/ajouter-un-modele-alarme/",
        AddModeleAlarmeView.as_view(),
        name="add-modele-alarme",
    ),
    path(
        "api/editer-un-modele-alarme/<int:id>/",
        EditModeleAlarmeView.as_view(),
        name="edit-modele-alarme",
    ),
    path(
        "api/supprimer-des-modeles-alarme/",
        DeleteModeleAlarmeView.as_view(),
        name="delete-modele-alarme",
    ),
    path(
        "api/liste-des-modeles-avis-commerciaux/",
        ListModeleAvisCommercialView.as_view(),
        name="list-modele-avis-commercial",
    ),
    path(
        "api/recherche-modele-avis-commercial/",
        SearchModeleAvisCommercialView.as_view(),
        name="search-modele-avis-commercial",
    ),
    path(
        "api/ajouter-un-modele-avis-commercial/",
        AddModeleAvisCommercialView.as_view(),
        name="add-modele-avis-commercial",
    ),
    path(
        "api/editer-un-modele-avis-commercial/<int:id>/",
        EditModeleAvisCommercialView.as_view(),
        name="edit-modele-avis-commercial",
    ),
    path(
        "api/supprimer-des-modeles-avis-commerciaux/",
        DeleteModeleAvisCommercialView.as_view(),
        name="delete-modele-avis-commercial",
    ),
    path(
        "api/liste-des-modeles-de-relation-entreprise/",
        ListModeleRelationEntrepriseView.as_view(),
        name="list-modele-relation-entreprise",
    ),
    path(
        "api/recherche-modele-de-relation-entreprise/",
        SearchModeleRelationEntrepriseView.as_view(),
        name="search-modele-relation-entreprise",
    ),
    path(
        "api/ajouter-un-modele-de-relation-entreprise/",
        AddModeleRelationEntrepriseView.as_view(),
        name="add-modele-relation-entreprise",
    ),
    path(
        "api/editer-un-modele-de-relation-entreprise/<int:id>/",
        EditModeleRelationEntrepriseView.as_view(),
        name="edit-modele-relation-entreprise",
    ),
    path(
        "api/supprimer-des-modeles-de-relation-entreprise/",
        DeleteModeleRelationEntrepriseView.as_view(),
        name="delete-modele-relation-entreprise",
    ),
    path(
        "api/liste-des-modeles-information-notation-entreprise/",
        ListModeleInformationNotationEntrepriseView.as_view(),
        name="list-modele-information-notation-entreprise",
    ),
    path(
        "api/recherche-modele-information-notation-entreprise/",
        SearchModeleInformationNotationEntrepriseView.as_view(),
        name="search-modele-information-notation-entreprise",
    ),
    path(
        "api/ajouter-un-modele-information-notation-entreprise/",
        AddModeleInformationNotationEntrepriseView.as_view(),
        name="add-modele-information-notation-entreprise",
    ),
    path(
        "api/editer-un-modele-information-notation-entreprise/<int:id>/",
        EditModeleInformationNotationEntrepriseView.as_view(),
        name="edit-modele-information-notation-entreprise",
    ),
    path(
        "api/supprimer-des-modeles-information-notation-entreprise/",
        DeleteModeleInformationNotationEntrepriseView.as_view(),
        name="delete-modele-information-notation-entreprise",
    ),
    path(
        "api/liste-des-modeles-comportement-paiement/",
        ListModeleComportementPaiementView.as_view(),
        name="list-modele-comportement-paiement",
    ),
    path(
        "api/recherche-modele-comportement-paiement/",
        SearchModeleComportementPaiementView.as_view(),
        name="search-modele-comportement-paiement",
    ),
    path(
        "api/ajouter-un-modele-comportement-paiement/",
        AddModeleComportementPaiementView.as_view(),
        name="add-modele-comportement-paiement",
    ),
    path(
        "api/editer-un-modele-comportement-paiement/<int:id>/",
        EditModeleComportementPaiementView.as_view(),
        name="edit-modele-comportement-paiement",
    ),
    path(
        "api/supprimer-des-modeles-comportement-paiement/",
        DeleteModeleComportementPaiementView.as_view(),
        name="delete-modele-comportement-paiement",
    ),
    path(
        "api/liste-des-modeles-comportement-jugement/",
        ListModeleComportementJugementView.as_view(),
        name="list-modele-comportement-jugement",
    ),
    path(
        "api/recherche-modele-comportement-jugement/",
        SearchModeleComportementJugementView.as_view(),
        name="search-modele-comportement-jugement",
    ),
    path(
        "api/ajouter-un-modele-comportement-jugement/",
        AddModeleComportementJugementView.as_view(),
        name="add-modele-comportement-jugement",
    ),
    path(
        "api/editer-un-modele-comportement-jugement/<int:id>/",
        EditModeleComportementJugementView.as_view(),
        name="edit-modele-comportement-jugement",
    ),
    path(
        "api/supprimer-des-modeles-comportement-jugement/",
        DeleteModeleComportementJugementView.as_view(),
        name="delete-modele-comportement-jugement",
    ),
    # === MODULES ACHETEUR === #
    path("api/liste-des-acheteurs/", ListAcheteurView.as_view(), name="list-acheteur"),
    path("api/acheteurs/stats/", AcheteurStatsView.as_view(), name="acheteurs-stats"),
    path(
        "api/recherche-acheteur/", SearchAcheteurView.as_view(), name="search-acheteur"
    ),
    path("api/ajouter-un-acheteur/", AddAcheteurView.as_view(), name="add-acheteur"),
    path(
        "api/editer-un-acheteur/<int:id>/",
        EditAcheteurView.as_view(),
        name="edit-acheteur",
    ),
    path(
        "api/consulter-un-acheteur/<int:id>/",
        GetAcheteurView.as_view(),
        name="get-acheteur",
    ),
    path(
        "api/supprimer-des-acheteurs/",
        DeleteAcheteurView.as_view(),
        name="delete-acheteur",
    ),
    # === MODULES LIAISONS ACHETEUR === #
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-resumes/",
        ListAcheteurResumeView.as_view(),
        name="list-resume-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-resume/",
        SearchAcheteurResumeView.as_view(),
        name="search-resume-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-resume/",
        AddAcheteurResumeView.as_view(),
        name="add-resume-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-resume/<int:resume_id>/",
        EditAcheteurResumeView.as_view(),
        name="edit-resume-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-resumes/",
        DeleteAcheteurResumeView.as_view(),
        name="delete-resume-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/resume/",
        AcheteurResumeView.as_view(),
        name="acheteur-resume"
    ),
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-evaluations-de-risque/",
        ListAcheteurRiskRatingView.as_view(),
        name="list-risk-rating-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-evaluation-risque/",
        SearchAcheteurRiskRatingView.as_view(),
        name="search-risk-rating-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-evaluation-risque/",
        AddAcheteurRiskRatingView.as_view(),
        name="add-risk-rating-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-evaluation-risque/<int:risk_rating_id>/",
        EditAcheteurRiskRatingView.as_view(),
        name="edit-risk-rating-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-evaluation-risque/",
        DeleteAcheteurRiskRatingView.as_view(),
        name="delete-risk-rating-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/evaluation-risque/",
        AcheteurRiskRatingView.as_view(),
        name="acheteur-evaluation-risque"
    ),
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-donnees-enregistrees/",
        ListAcheteurDataSaveView.as_view(),
        name="list-donnee-enregistree-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-donnee-enregistree/",
        SearchAcheteurDataSaveView.as_view(),
        name="search-donnee-enregistree-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-donnee-enregistree/",
        AddAcheteurDataSaveView.as_view(),
        name="add-donnee-enregistree-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-donnee-enregistree/<int:donnee_enregistrement_id>/",
        EditAcheteurDataSaveView.as_view(),
        name="edit-donnee-enregistree-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-donnees-enregistrees/",
        DeleteAcheteurDataSaveView.as_view(),
        name="delete-donnee-enregistree-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/donnees-enregistrement/",
        AcheteurDonneesEnregistrementView.as_view(),
        name="acheteur-donnees-enregistrement"
    ),
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-tendances/",
        ListAcheteurTendanceView.as_view(),
        name="list-tendance-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-tendance/",
        SearchAcheteurTendanceView.as_view(),
        name="search-tendance-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-tendance/",
        AddAcheteurTendanceView.as_view(),
        name="add-tendance-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-tendance/<int:tendance_id>/",
        EditAcheteurTendanceView.as_view(),
        name="edit-tendance-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-tendances/",
        DeleteAcheteurTendanceView.as_view(),
        name="delete-tendance-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/tendance/",
        AcheteurTendanceView.as_view(),
        name="acheteur-tendance",
    ),
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-responsables/",
        ListAcheteurResponsableView.as_view(),
        name="list-responsable-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-responsable/",
        SearchAcheteurResponsableView.as_view(),
        name="search-responsable-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-responsable/",
        AddAcheteurResponsableView.as_view(),
        name="add-responsable-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-responsable/<int:responsable_id>/",
        EditAcheteurResponsableView.as_view(),
        name="edit-responsable-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-responsables/",
        DeleteAcheteurResponsableView.as_view(),
        name="delete-responsable-acheteur",
    ),
    path(
        'api/acheteur/<int:acheteur_id>/responsables/',
        AcheteurResponsableListView.as_view(),
        name='api-responsables-acheteur'
    ),
    path(
        'api/acheteur/<int:acheteur_id>/responsables/<int:responsable_id>/',
        AcheteurResponsableDetailView.as_view(),
        name='api-responsable-detail'
    ),
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-antecdents-juridiques/",
        ListAcheteurAntecedentView.as_view(),
        name="list-antecedent-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-antecedent/",
        SearchAcheteurAntecedentView.as_view(),
        name="search-antecedent-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-antecedent/",
        AddAcheteurAntecedentView.as_view(),
        name="add-antecedent-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-antecedent/<int:antecedent_id>/",
        EditAcheteurAntecedentView.as_view(),
        name="edit-antecedent-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-antecedents/",
        DeleteAcheteurAntecedentView.as_view(),
        name="delete-antecedent-acheteur",
    ),
    path(
        'api/acheteur/<int:acheteur_id>/antecedents/',
        AcheteurAntecedentListView.as_view(),
        name='api-antecedents-acheteur'
    ),
    path(
        'api/acheteur/<int:acheteur_id>/antecedents/<int:antecedent_id>/',
        AcheteurAntecedentDetailView.as_view(),
        name='api-antecedent-detail'
    ),
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-gestions-de-risque/",
        ListAcheteurGestionRisqueView.as_view(),
        name="list-gestion-de-risque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-gestion-de-risque/",
        SearchAcheteurGestionRisqueView.as_view(),
        name="search-gestion-de-risque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-gestion-de-risque/",
        AddAcheteurGestionRisqueView.as_view(),
        name="add-gestion-de-risque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-gestion-de-risque/<int:gestion_risque_id>/",
        EditAcheteurGestionRisqueView.as_view(),
        name="edit-gestion-de-risque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-gestions-de-risque/",
        DeleteAcheteurGestionRisqueView.as_view(),
        name="delete-gestion-de-risque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/gestion-risque/",
        AcheteurGestionRisqueView.as_view(),
        name="acheteur-gestion-risque",
    ),
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-membres-du-conseil/",
        ListAcheteurMembreConseilView.as_view(),
        name="list-membre-du-conseil-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-membre-du-conseil/",
        SearchAcheteurMembreConseilView.as_view(),
        name="search-membre-du-conseil-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-membre-du-conseil/",
        AddAcheteurMembreConseilView.as_view(),
        name="add-membre-du-conseil-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-membre-du-conseil/<int:membre_conseil_id>/",
        EditAcheteurMembreConseilView.as_view(),
        name="edit-membre-du-conseil-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-membres-du-conseil/",
        DeleteAcheteurMembreConseilView.as_view(),
        name="delete-membre-du-conseil-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/conseil/",
        AcheteurConseilListView.as_view(),
        name="acheteur-conseil-list",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/conseil/<int:membre_id>/",
        AcheteurConseilDetailView.as_view(),
        name="acheteur-conseil-detail",
    ),
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-compositions-du-capital/",
        ListAcheteurCompositionCapitalView.as_view(),
        name="list-composition-du-capital-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-composition-du-capital/",
        SearchAcheteurCompositionCapitalView.as_view(),
        name="search-composition-du-capital-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-composition-du-capital/",
        AddAcheteurCompositionCapitalView.as_view(),
        name="add-composition-du-capital-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-composition-du-capital/<int:composition_capital_id>/",
        EditAcheteurCompositionCapitalView.as_view(),
        name="edit-composition-du-capital-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-compositions-du-capital/",
        DeleteAcheteurCompositionCapitalView.as_view(),
        name="delete-composition-du-capital-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/capital/', AcheteurCapitalView.as_view(), name='acheteur-capital'),
    
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-actionnaires/",
        ListAcheteurActionnaireView.as_view(),
        name="list-actionnaire-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-actionnaire/",
        SearchAcheteurActionnaireView.as_view(),
        name="search-actionnaire-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-actionnaire/",
        AddAcheteurActionnaireView.as_view(),
        name="add-actionnaire-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-actionnaire/<int:actionnaire_id>/",
        EditAcheteurActionnaireView.as_view(),
        name="edit-actionnaire-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-actionnaires/",
        DeleteAcheteurActionnaireView.as_view(),
        name="delete-actionnaire-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/actionnaires/",
        AcheteurActionnaireListView.as_view(),
        name="acheteur-actionnaire-list",
    ),
    path(
        'api/acheteur/<int:acheteur_id>/actionnaires/stats/',
        ActionnaireStatsView.as_view(),
        name='actionnaire-stats'
    ),
    path(
        'api/acheteur/<int:acheteur_id>/actionnaires/<int:pk>/',
        ActionnaireDetailView.as_view(),
        name='actionnaire-detail'
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-actionnaires/",
        AcheteurActionnaireListView.as_view(),
        name="delete-actionnaire-acheteur",
    ),
    
    
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-opinions-acremac/",
        ListAcheteurOpinionAcremacView.as_view(),
        name="list-opinion-acremac-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-opinion-acremac/",
        SearchAcheteurOpinionAcremacView.as_view(),
        name="search-opinion-acremac-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-opinion-acremac/",
        AddAcheteurOpinionAcremacView.as_view(),
        name="add-opinion-acremac-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-opinion-acremac/<int:opinion_id>/",
        EditAcheteurOpinionAcremacView.as_view(),
        name="edit-opinion-acremac-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-opinions-acremac/",
        DeleteAcheteurOpinionAcremacView.as_view(),
        name="delete-opinion-acremac-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/opinion-acremac/",
        AcheteurOpinionAcremacView.as_view(),
        name="acheteur-opinion-acremac",
    ),
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-filiales/",
        ListAcheteurFilialeView.as_view(),
        name="list-filiale-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-filiale/",
        SearchAcheteurFilialeView.as_view(),
        name="search-filiale-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-filiale/",
        AddAcheteurFilialeView.as_view(),
        name="add-filiale-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-filiale/<int:filiale_id>/",
        EditAcheteurFilialeView.as_view(),
        name="edit-filiale-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-filiales/",
        DeleteAcheteurFilialeView.as_view(),
        name="delete-filiale-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/filiales/",
        AcheteurFilialeListView.as_view(),
        name="acheteur-filiale-list",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/filiales/<int:filiale_id>/",
        AcheteurFilialeDetailView.as_view(),
        name="acheteur-filiale-detail",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/filiales/stats/",
        FilialeStatsView.as_view(),
        name="acheteur-filiale-stats",
    ),
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-analyses-sectorielles/",
        ListAcheteurAnalyseSectorielleView.as_view(),
        name="list-analyse-sectorielle-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-analyse-sectorielle/",
        SearchAcheteurAnalyseSectorielleView.as_view(),
        name="search-analyse-sectorielle-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-analyse-sectorielle/",
        AddAcheteurAnalyseSectorielleView.as_view(),
        name="add-analyse-sectorielle-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-analyse-sectorielle/<int:analyse_id>/",
        EditAcheteurAnalyseSectorielleView.as_view(),
        name="edit-analyse-sectorielle-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-analyses-sectorielles/",
        DeleteAcheteurAnalyseSectorielleView.as_view(),
        name="delete-analyse-sectorielle-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/analyse-sectorielle/', AcheteurAnalyseSectorielleView.as_view(), name='acheteur-analyse-sectorielle'),
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-comptes-financiers/",
        ListAcheteurCompteFinancierView.as_view(),
        name="list-compte-financier-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-compte-financier/",
        SearchAcheteurCompteFinancierView.as_view(),
        name="search-compte-financier-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-compte-financier/",
        AddAcheteurCompteFinancierView.as_view(),
        name="add-compte-financier-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-compte-financier/<int:compte_financier_id>/",
        EditAcheteurCompteFinancierView.as_view(),
        name="edit-compte-financier-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-comptes-financiers/",
        DeleteAcheteurCompteFinancierView.as_view(),
        name="delete-compte-financier-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/compte-financier/',  AcheteurCompteFinancierView.as_view(), name='acheteur-compte-financier'),
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-operations-et-historiques/",
        ListAcheteurOperationHistoriqueView.as_view(),
        name="list-operation-et-historique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-operation-et-historique/",
        SearchAcheteurOperationHistoriqueView.as_view(),
        name="search-operation-et-historique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-operation-et-historique/",
        AddAcheteurOperationHistoriqueView.as_view(),
        name="add-operation-et-historique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-operation-et-historique/<int:operation_historique_id>/",
        EditAcheteurOperationHistoriqueView.as_view(),
        name="edit-operation-et-historique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-operations-et-historiques/",
        DeleteAcheteurOperationHistoriqueView.as_view(),
        name="delete-operation-et-historique-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/operations/', 
     AcheteurOperationHistoriqueListView.as_view(), 
     name='acheteur-operations-list'),
    path('api/acheteur/<int:acheteur_id>/operations/<int:operation_id>/', 
        AcheteurOperationHistoriqueDetailView.as_view(), 
        name='acheteur-operation-detail'),
    path('api/liste-importations/', 
        ListeImportationListView.as_view(), 
        name='liste-importations'),
    
    
    
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-proprietes-et-actifs/",
        ListAcheteurProprieteActifView.as_view(),
        name="list-propriete-et-actif-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-propriete-et-actif/",
        SearchAcheteurProprieteActifView.as_view(),
        name="search-propriete-et-actif-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-propriete-et-actif/",
        AddAcheteurProprieteActifView.as_view(),
        name="add-propriete-et-actif-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-propriete-et-actif/<int:propriete_actif_id>/",
        EditAcheteurProprieteActifView.as_view(),
        name="edit-propriete-et-actif-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-proprietes-et-actifs/",
        DeleteAcheteurProprieteActifView.as_view(),
        name="delete-propriete-et-actif-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/propriete-actif/', 
        AcheteurProprieteActifView.as_view(), 
        name='acheteur-propriete-actif'),
    
    # Locaux
    path('api/locaux/', 
        LocauxListView.as_view(), 
        name='locaux-list'),
    
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-conditions-achat/",
        ListAcheteurConditionAchatView.as_view(),
        name="list-condition-achat-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-condition-achat/",
        SearchAcheteurConditionAchatView.as_view(),
        name="search-condition-achat-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-condition-achat/",
        AddAcheteurConditionAchatView.as_view(),
        name="add-condition-achat-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-condition-achat/<int:condition_achat_id>/",
        EditAcheteurConditionAchatView.as_view(),
        name="edit-condition-achat-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-conditions-achat/",
        DeleteAcheteurConditionAchatView.as_view(),
        name="delete-condition-achat-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/condition-achat/', 
        AcheteurConditionAchatView.as_view(), 
        name='acheteur-condition-achat'),
    
    # Liste des conditions d'achat
    path('api/conditions-achat/', 
        ListeConditionAchatListView.as_view(), 
        name='conditions-achat-list'),
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-conditions-vente/",
        ListAcheteurConditionVenteView.as_view(),
        name="list-condition-vente-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-condition-vente/",
        SearchAcheteurConditionVenteView.as_view(),
        name="search-condition-vente-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-condition-vente/",
        AddAcheteurConditionVenteView.as_view(),
        name="add-condition-vente-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-condition-vente/<int:condition_vente_id>/",
        EditAcheteurConditionVenteView.as_view(),
        name="edit-condition-vente-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-conditions-vente/",
        DeleteAcheteurConditionVenteView.as_view(),
        name="delete-condition-vente-acheteur",
    ),
    # Conditions de Vente
    path('api/acheteur/<int:acheteur_id>/condition-vente/', 
        AcheteurConditionVenteView.as_view(), 
        name='acheteur-condition-vente'),
    
    # Liste des conditions de vente
    path('api/conditions-vente/', 
        ListeConditionVenteListView.as_view(), 
        name='conditions-vente-list'),
    
    # Choix pour les conditions de vente
    path('api/condition-vente/choices/', 
        ConditionVenteChoicesView.as_view(), 
        name='condition-vente-choices'),
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-sommaires-et-avis/",
        ListAcheteurSommaireAvisView.as_view(),
        name="list-sommaire-et-avis-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-sommaire-et-avis/",
        SearchAcheteurSommaireAvisView.as_view(),
        name="search-sommaire-et-avis-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-sommaire-et-avis/",
        AddAcheteurSommaireAvisView.as_view(),
        name="add-sommaire-et-avis-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-sommaire-et-avis/<int:sommaire_avis_id>/",
        EditAcheteurSommaireAvisView.as_view(),
        name="edit-sommaire-et-avis-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-sommaires-et-avis/",
        DeleteAcheteurSommaireAvisView.as_view(),
        name="delete-sommaire-et-avis-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/sommaire-avis/', AcheteurSommaireEtAvisView.as_view(), name='acheteur-sommaire-avis'),
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-conseils/",
        ListAcheteurConseilView.as_view(),
        name="list-conseil-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-conseil/",
        SearchAcheteurConseilView.as_view(),
        name="search-conseil-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-conseil/",
        AddAcheteurConseilView.as_view(),
        name="add-conseil-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-conseil/<int:advice_id>/",
        EditAcheteurConseilView.as_view(),
        name="edit-conseil-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-conseils/",
        DeleteAcheteurConseilView.as_view(),
        name="delete-conseil-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/advice/', AcheteurAdviceView.as_view(),  name='acheteur-advice'),
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-donnees-geopolitiques/",
        ListAcheteurGeopoliticView.as_view(),
        name="list-donnee-geopolitique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-donnee-geopolitique/",
        SearchAcheteurGeopoliticView.as_view(),
        name="search-donnee-geopolitique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-donnee-geopolitique/",
        AddAcheteurGeopoliticView.as_view(),
        name="add-donnee-geopolitique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-donnee-geopolitique/<int:geopolitic_id>/",
        EditAcheteurGeopoliticView.as_view(),
        name="edit-donnee-geopolitique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-donnees-geopolitiques/",
        DeleteAcheteurGeopoliticView.as_view(),
        name="delete-donnee-geopolitique-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/geopolitics/',  AcheteurGeopoliticsView.as_view(), name='acheteur-geopolitics'),
    
    
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-donnees-bancaires/",
        ListAcheteurBankingView.as_view(),
        name="list-donnee-bancaire-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-donnee-bancaire/",
        SearchAcheteurBankingView.as_view(),
        name="search-donnee-bancaire-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-donnee-bancaire/",
        AddAcheteurBankingView.as_view(),
        name="add-donnee-bancaire-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-donnee-bancaire/<int:banking_id>/",
        EditAcheteurBankingView.as_view(),
        name="edit-donnee-bancaire-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-donnees-bancaires/",
        DeleteAcheteurBankingView.as_view(),
        name="delete-donnee-bancaire-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/banquiers/",
        AcheteurBanquierListView.as_view(),
        name="acheteur-banquier-list",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/banquiers/<int:banquier_id>/",
        AcheteurBanquierDetailView.as_view(),
        name="acheteur-banquier-detail",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/banquiers/stats/",
        BanquierStatsView.as_view(),
        name="acheteur-banquier-stats",
    ),
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/liste-des-actifs/",
        ListAcheteurActifAnglaisView.as_view(),
        name="list-actif-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/recherche-actif/",
        SearchAcheteurActifAnglaisView.as_view(),
        name="search-actif-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/ajouter-un-actif/",
        AddAcheteurActifAnglaisView.as_view(),
        name="add-actif-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/editer-un-actif/<int:actif_id>/",
        EditAcheteurActifAnglaisView.as_view(),
        name="edit-actif-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/supprimer-des-actifs/",
        DeleteAcheteurActifAnglaisView.as_view(),
        name="delete-actif-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/liste-des-passifs/",
        ListAcheteurPassifAnglaisView.as_view(),
        name="list-passif-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/recherche-passif/",
        SearchAcheteurPassifAnglaisView.as_view(),
        name="search-passif-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/ajouter-un-passif/",
        AddAcheteurPassifAnglaisView.as_view(),
        name="add-passif-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/editer-un-passif/<int:passif_id>/",
        EditAcheteurPassifAnglaisView.as_view(),
        name="edit-passif-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/supprimer-des-passifs/",
        DeleteAcheteurPassifAnglaisView.as_view(),
        name="delete-passif-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/liste-des-resultats/",
        ListAcheteurResultatAnglaisView.as_view(),
        name="list-resultat-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/recherche-resultat/",
        SearchAcheteurResultatAnglaisView.as_view(),
        name="search-resultat-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/ajouter-un-resultat/",
        AddAcheteurResultatAnglaisView.as_view(),
        name="add-resultat-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/editer-un-resultat/<int:resultat_id>/",
        EditAcheteurResultatAnglaisView.as_view(),
        name="edit-resultat-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-anglais/supprimer-des-resultats/",
        DeleteAcheteurResultatAnglaisView.as_view(),
        name="delete-resultat-anglais-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/liste-des-actifs/",
        ListAcheteurActifClassiqueView.as_view(),
        name="list-actif-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/recherche-actif/",
        SearchAcheteurActifClassiqueView.as_view(),
        name="search-actif-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/ajouter-un-actif/",
        AddAcheteurActifClassiqueView.as_view(),
        name="add-actif-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/editer-un-actif/<int:actif_id>/",
        EditAcheteurActifClassiqueView.as_view(),
        name="edit-actif-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/supprimer-des-actifs/",
        DeleteAcheteurActifClassiqueView.as_view(),
        name="delete-actif-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/liste-des-passifs/",
        ListAcheteurPassifClassiqueView.as_view(),
        name="list-passif-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/recherche-passif/",
        SearchAcheteurPassifClassiqueView.as_view(),
        name="search-passif-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/ajouter-un-passif/",
        AddAcheteurPassifClassiqueView.as_view(),
        name="add-passif-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/editer-un-passif/<int:passif_id>/",
        EditAcheteurPassifClassiqueView.as_view(),
        name="edit-passif-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/supprimer-des-passifs/",
        DeleteAcheteurPassifClassiqueView.as_view(),
        name="delete-passif-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/liste-des-resultats/",
        ListAcheteurResultatClassiqueView.as_view(),
        name="list-resultat-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/recherche-resultat/",
        SearchAcheteurResultatClassiqueView.as_view(),
        name="search-resultat-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/ajouter-un-resultat/",
        AddAcheteurResultatClassiqueView.as_view(),
        name="add-resultat-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/editer-un-resultat/<int:resultat_id>/",
        EditAcheteurResultatClassiqueView.as_view(),
        name="edit-resultat-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-classique/supprimer-des-resultats/",
        DeleteAcheteurResultatClassiqueView.as_view(),
        name="delete-resultat-classique-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/liste-des-actifs/",
        ListAcheteurActifSysCohadaView.as_view(),
        name="list-actif-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/recherche-actif/",
        SearchAcheteurActifSysCohadaView.as_view(),
        name="search-actif-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/ajouter-un-actif/",
        AddAcheteurActifSysCohadaView.as_view(),
        name="add-actif-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/editer-un-actif/<int:actif_id>/",
        EditAcheteurActifSysCohadaView.as_view(),
        name="edit-actif-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/supprimer-des-actifs/",
        DeleteAcheteurActifSysCohadaView.as_view(),
        name="delete-actif-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/liste-des-passifs/",
        ListAcheteurPassifSysCohadaView.as_view(),
        name="list-passif-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/recherche-passif/",
        SearchAcheteurPassifSysCohadaView.as_view(),
        name="search-passif-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/ajouter-un-passif/",
        AddAcheteurPassifSysCohadaView.as_view(),
        name="add-passif-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/editer-un-passif/<int:passif_id>/",
        EditAcheteurPassifSysCohadaView.as_view(),
        name="edit-passif-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/supprimer-des-passifs/",
        DeleteAcheteurPassifSysCohadaView.as_view(),
        name="delete-passif-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/liste-des-resultats/",
        ListAcheteurResultatSysCohadaView.as_view(),
        name="list-resultat-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/recherche-resultat/",
        SearchAcheteurResultatSysCohadaView.as_view(),
        name="search-resultat-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/ajouter-un-resultat/",
        AddAcheteurResultatSysCohadaView.as_view(),
        name="add-resultat-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/editer-un-resultat/<int:resultat_id>/",
        EditAcheteurResultatSysCohadaView.as_view(),
        name="edit-resultat-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-syscohada/supprimer-des-resultats/",
        DeleteAcheteurResultatSysCohadaView.as_view(),
        name="delete-resultat-syscohada-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/liste-des-actifs/",
        ListAcheteurAssetsView.as_view(),
        name="list-assets-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/recherche-actif/",
        SearchAcheteurAssetsView.as_view(),
        name="search-assets-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/ajouter-un-actif/",
        AddAcheteurAssetsView.as_view(),
        name="add-assets-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/editer-un-actif/<int:asset_id>/",
        EditAcheteurAssetsView.as_view(),
        name="edit-assets-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/supprimer-des-actifs/",
        DeleteAcheteurAssetsView.as_view(),
        name="delete-assets-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/liste-des-passifs/",
        ListAcheteurLiabilitiesView.as_view(),
        name="list-liabilities-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/recherche-passif/",
        SearchAcheteurLiabilitiesView.as_view(),
        name="search-liabilities-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/ajouter-un-passif/",
        AddAcheteurLiabilitiesView.as_view(),
        name="add-liabilities-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/editer-un-passif/<int:liability_id>/",
        EditAcheteurLiabilitiesView.as_view(),
        name="edit-liabilities-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/supprimer-des-lipassifsabilities/",
        DeleteAcheteurLiabilitiesView.as_view(),
        name="delete-liabilities-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/liste-des-depenses/",
        ListAcheteurExpensesView.as_view(),
        name="list-expenses-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/recherche-depense/",
        SearchAcheteurExpensesView.as_view(),
        name="search-expenses-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/ajouter-une-depense/",
        AddAcheteurExpensesView.as_view(),
        name="add-expenses-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/editer-une-depense/<int:expense_id>/",
        EditAcheteurExpensesView.as_view(),
        name="edit-expenses-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/supprimer-des-depenses/",
        DeleteAcheteurExpensesView.as_view(),
        name="delete-expenses-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/liste-des-produits/",
        ListAcheteurProductsView.as_view(),
        name="list-products-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/recherche-produit/",
        SearchAcheteurProductsView.as_view(),
        name="search-products-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/ajouter-un-produit/",
        AddAcheteurProductsView.as_view(),
        name="add-products-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/editer-un-produit/<int:product_id>/",
        EditAcheteurProductsView.as_view(),
        name="edit-products-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/supprimer-des-produits/",
        DeleteAcheteurProductsView.as_view(),
        name="delete-products-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/liste-des-donnees-hors-bilan/",
        ListAcheteurOffBalanceSheetView.as_view(),
        name="list-off-balance-sheet-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/recherche-donnee-hors-bilan/",
        SearchAcheteurOffBalanceSheetView.as_view(),
        name="search-off-balance-sheet-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/ajouter-une-donnee-hors-bilan/",
        AddAcheteurOffBalanceSheetView.as_view(),
        name="add-off-balance-sheet-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/editer-une-donnee-hors-bilan/<int:off_balance_sheet_id>/",
        EditAcheteurOffBalanceSheetView.as_view(),
        name="edit-off-balance-sheet-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-bancaire/supprimer-des-donnees-hors-bilan/",
        DeleteAcheteurOffBalanceSheetView.as_view(),
        name="delete-off-balance-sheet-acheteur",
    ),
    # === MODULES COMMANDE === #
    path("api/liste-des-commandes/", ListCommandeView.as_view(), name="list-commande"),
    path(
        "api/recherche-commande/", SearchCommandeView.as_view(), name="search-commande"
    ),
    path("api/ajouter-une-commande/", AddCommandeView.as_view(), name="add-commande"),
    path(
        "api/editer-une-commande/<int:id>/",
        EditCommandeView.as_view(),
        name="edit-commande",
    ),
    path(
        "api/consulter-une-commande/<int:id>/",
        GetCommandeView.as_view(),
        name="get-commande",
    ),
    path(
        "api/supprimer-des-commandes/",
        DeleteCommandeView.as_view(),
        name="delete-commande",
    ),
    path('api/commande-details/<int:commande_id>/', CommandeDetailsView.as_view(), name='commande-details'),
    
    path("api/liste-des-alertes/", ListAlerteView.as_view(), name="list-alerte"),
    path("api/recherche-alerte/", SearchAlerteView.as_view(), name="search-alerte"),
    path("api/ajouter-une-alerte/", AddAlerteView.as_view(), name="add-alerte"),
    path(
        "api/editer-une-alerte/<int:id>/", EditAlerteView.as_view(), name="edit-alerte"
    ),
    path(
        "api/consulter-une-alerte/<int:id>/", GetAlerteView.as_view(), name="get-alerte"
    ),
    path(
        "api/supprimer-des-alertes/", DeleteAlerteView.as_view(), name="delete-alerte"
    ),
    path("api/envoyer-warning/", EnvoyerWarningView.as_view(), name="envoyer-warning"),
    
    
    
    
    path(
        "api/liste-des-documents-alerte/",
        ListDocumentAlerteView.as_view(),
        name="list-document-alerte",
    ),
    path(
        "api/ajouter-un-document-alerte/",
        AddDocumentAlerteView.as_view(),
        name="add-document-alerte",
    ),
    path(
        "api/editer-un-document-alerte/<int:id>/",
        EditDocumentAlerteView.as_view(),
        name="edit-document-alerte",
    ),
    path(
        "api/consulter-un-document-alerte/<int:id>/",
        GetDocumentAlerteView.as_view(),
        name="get-document-alerte",
    ),
    path(
        "api/supprimer-des-documents-alerte/",
        DeleteDocumentAlerteView.as_view(),
        name="delete-document-alerte",
    ),
    # Dans votre fichier urls.py API
    path('api/acheteur/<int:acheteur_id>/documents-oneview/', 
         AcheteurDocumentListOneView.as_view(), 
         name='acheteur-documents-list-oneview'),
    path('api/acheteur/<int:acheteur_id>/documents-oneview/<int:document_id>/', 
         AcheteurDocumentDetailOneView.as_view(), 
         name='acheteur-document-detail-oneview'),
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    path("api/liste-des-clients/", ListClientView.as_view(), name="list-client"),
    path("api/ajouter-un-client/", AddClientView.as_view(), name="add-client"),
    path(
        "api/editer-un-client/<int:id>/", EditClientView.as_view(), name="edit-client"
    ),
    path(
        "api/consulter-un-client/<int:id>/", GetClientView.as_view(), name="get-client"
    ),
    path(
        "api/supprimer-des-clients/", DeleteClientView.as_view(), name="delete-client"
    ),
    path("api/liste-des-contacts/", ListContactView.as_view(), name="list-contact"),
    path("api/ajouter-un-contact/", AddContactView.as_view(), name="add-contact"),
    path(
        "api/editer-un-contact/<int:id>/",
        EditContactView.as_view(),
        name="edit-contact",
    ),
    path(
        "api/consulter-un-contact/<int:id>/",
        GetContactView.as_view(),
        name="get-contact",
    ),
    path(
        "api/supprimer-des-contacts/",
        DeleteContactView.as_view(),
        name="delete-contact",
    ),
    path(
        "api/liste-des-portefeuilles/",
        ListPortefeuilleView.as_view(),
        name="list-portefeuille",
    ),
    path(
        "api/ajouter-un-portefeuille/",
        AddPortefeuilleView.as_view(),
        name="add-portefeuille",
    ),
    path(
        "api/editer-un-portefeuille/<int:id>/",
        EditPortefeuilleView.as_view(),
        name="edit-portefeuille",
    ),
    path(
        "api/consulter-un-portefeuille/<int:id>/",
        GetPortefeuilleView.as_view(),
        name="get-portefeuille",
    ),
    path(
        "api/supprimer-des-portefeuilles/",
        DeletePortefeuilleView.as_view(),
        name="delete-portefeuille",
    ),
    path(
        "api/liste-des-portefeuilles-client/",
        ListPortefeuilleClientView.as_view(),
        name="list-portefeuille-client",
    ),
    path(
        "api/ajouter-un-portefeuille-client/",
        AddPortefeuilleClientView.as_view(),
        name="add-portefeuille-client",
    ),
    path(
        "api/ajouter-un-portefeuille-avec-clients/",
        AddPortefeuilleWithClientsView.as_view(),
        name="add-portefeuille-with-client",
    ),
    path(
        "api/ajouter-un-portefeuille-avec-acheteurs/",
        AddPortefeuilleWithAcheteursView.as_view(),
        name="add-portefeuille-with-acheteur",
    ),
    path(
        "api/editer-un-portefeuille-client/<int:id>/",
        EditPortefeuilleClientView.as_view(),
        name="edit-portefeuille-with-client",
    ),
    path(
        "api/consulter-un-portefeuille-avec-clients/<int:id>/",
        EditPortefeuilleWithClientsView.as_view(),
        name="get-portefeuille-client",
    ),
    path(
        "api/consulter-un-portefeuille-client/<int:id>/",
        GetPortefeuilleClientView.as_view(),
        name="get-portefeuille-client",
    ),
    path(
        "api/supprimer-des-portefeuilles-client/",
        DeletePortefeuilleClientView.as_view(),
        name="delete-portefeuille-client",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/liste-des-comptes-financiers-irfs/",
        ListAcheteurCompteFinancierIrfsView.as_view(),
        name="list-compte-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/recherche-compte-financier-irfs/",
        SearchAcheteurCompteFinancierIrfsView.as_view(),
        name="search-compte-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/ajouter-un-compte-financier-irfs/",
        AddAcheteurCompteFinancierIrfsView.as_view(),
        name="add-compte-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/editer-un-compte-financier-irfs/<int:compte_irfs_id>/",
        EditAcheteurCompteFinancierIrfsView.as_view(),
        name="edit-compte-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/supprimer-des-comptes-financiers-irfs/",
        DeleteAcheteurCompteFinancierIrfsView.as_view(),
        name="delete-compte-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/liste-des-valeurs-financieres-irfs/",
        ListAcheteurValeurCompteFinancierIrfsView.as_view(),
        name="list-valeur-financiere-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/liste-des-actifs-financiers-irfs/",
        ListAcheteurActifFinancierIrfsView.as_view(),
        name="list-actif-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/liste-des-passifs-financiers-irfs/",
        ListAcheteurPassifFinancierIrfsView.as_view(),
        name="list-passif-financier-irfs-acheteur",
    ),
    # path('api/acheteur/<int:acheteur_id>/bilan-irfs/liste-des-resultats-financiers-irfs/', ListAcheteurResultatFinancierIrfsView.as_view(), name='list-resultat-financier-irfs-acheteur'),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/recherche-valeur-financiere-irfs/",
        SearchAcheteurValeurCompteFinancierIrfsView.as_view(),
        name="search-valeur-financiere-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/ajouter-une-valeur-financier-irfs/",
        AddAcheteurValeurCompteFinancierIrfsView.as_view(),
        name="add-valeur-financiere-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/ajout-une-valeur-financier-irfs/",
        AjoutAcheteurValeurCompteFinancierIrfsView.as_view(),
        name="ajout-valeur-financiere-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/editer-une-valeur-financier-irfs/<int:valeur_actif_irfs_id>/",
        EditAcheteurValeurCompteFinancierIrfsView.as_view(),
        name="edit-valeur-financiere-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/supprimer-des-valeurs-financieres-irfs/",
        DeleteAcheteurValeurCompteFinancierIrfsView.as_view(),
        name="delete-valeur-financiere-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/liste-des-ratios-financiers-irfs/",
        ListAcheteurRatioFinancierIrfsView.as_view(),
        name="list-ratio-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/recherche-ratio-financier-irfs/",
        SearchAcheteurRatioFinancierIrfsView.as_view(),
        name="search-ratio-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/ajouter-un-ratio-financier-irfs/",
        AddAcheteurRatioFinancierIrfsView.as_view(),
        name="add-ratio-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/editer-un-ratio-financier-irfs/<int:ratio_irfs_id>/",
        EditAcheteurRatioFinancierIrfsView.as_view(),
        name="edit-ratio-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/supprimer-des-ratios-financiers-irfs/",
        DeleteAcheteurRatioFinancierIrfsView.as_view(),
        name="delete-ratio-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/liste-des-valeurs-ratios-financiers-irfs/",
        ListAcheteurValeurRatioFinancierIrfsView.as_view(),
        name="list-valeur-ratio-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/recherche-valeur-ratio-financier-irfs/",
        SearchAcheteurValeurRatioFinancierIrfsView.as_view(),
        name="search-valeur-ratio-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/ajouter-une-valeur-ratio-financier-irfs/",
        AddAcheteurValeurRatioFinancierIrfsView.as_view(),
        name="add-valeur-ratio-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/editer-une-valeur-ratio-financier-irfs/<int:valeur_ratio_irfs_id>/",
        EditAcheteurValeurRatioFinancierIrfsView.as_view(),
        name="edit-valeur-ratio-financier-irfs-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/bilan-irfs/supprimer-des-valeurs-ratios-financiers-irfs/",
        DeleteAcheteurValeurRatioFinancierIrfsView.as_view(),
        name="delete-valeur-ratio-financier-irfs-acheteur",
    ),
    path(
        "api/liste-des-elements-de-surveillance/",
        ListElementSurveillanceView.as_view(),
        name="list-surveillance",
    ),
    path(
        "api/recherche-element-de-surveillance/",
        SearchElementSurveillanceView.as_view(),
        name="search-surveillance",
    ),
    path(
        "api/ajouter-un-element-de-surveillance/",
        AddElementSurveillanceView.as_view(),
        name="add-surveillance",
    ),
    path(
        "api/editer-un-element-de-surveillance/<int:id>/",
        EditElementSurveillanceView.as_view(),
        name="edit-surveillance",
    ),
    path(
        "api/supprimer-des-elements-de-surveillance/",
        DeleteElementSurveillanceView.as_view(),
        name="delete-surveillance",
    ),
    
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-certifications/",
        ListAcheteurCertificationView.as_view(),
        name="list-certification-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-certification/",
        SearchAcheteurCertificationView.as_view(),
        name="search-certification-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-certification/",
        AddAcheteurCertificationView.as_view(),
        name="add-certification-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-certification/<int:certification_id>/",
        EditAcheteurCertificationView.as_view(),
        name="edit-certification-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-certification/<int:certification_id>/",
        DetailAcheteurCertificationView.as_view(),
        name="detail-certification-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-certifications/",
        DeleteAcheteurCertificationView.as_view(),
        name="delete-certification-acheteur",
    ),
    # Certifications
    path('api/acheteur/<int:acheteur_id>/certifications-oneview/', 
        AcheteurCertificationListOneView.as_view(), 
        name='acheteur-certifications-list-oneview'),
    path('api/acheteur/<int:acheteur_id>/certifications-oneview/<int:certification_id>/', 
        AcheteurCertificationDetailOneView.as_view(), 
        name='acheteur-certification-detail-oneview'),
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-innovations/",
        ListAcheteurInnovationView.as_view(),
        name="list-innovation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-innovation/",
        SearchAcheteurInnovationView.as_view(),
        name="search-innovation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-innovation/",
        AddAcheteurInnovationView.as_view(),
        name="add-innovation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-innovation/<int:innovation_id>/",
        DetailAcheteurInnovationView.as_view(),
        name="detail-innovation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-innovation/<int:innovation_id>/",
        EditAcheteurInnovationView.as_view(),
        name="edit-innovation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-innovations/",
        DeleteAcheteurInnovationView.as_view(),
        name="delete-innovation-acheteur",
    ),
    # URLs pour les innovations et développements
    path('api/acheteur/<int:acheteur_id>/innovations-oneview/', 
        AcheteurInnovationDeveloppementListOneView.as_view(), 
        name='acheteur-innovations-list-oneview'),
    path('api/acheteur/<int:acheteur_id>/innovations-oneview/<int:innovation_id>/', 
        AcheteurInnovationDeveloppementDetailOneView.as_view(), 
        name='acheteur-innovation-detail-oneview'),
    
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-strategies/",
        ListAcheteurStrategieView.as_view(),
        name="list-strategie-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-strategie/",
        SearchAcheteurStrategieView.as_view(),
        name="search-strategie-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-strategie/",
        AddAcheteurStrategieView.as_view(),
        name="add-strategie-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-strategie/<int:strategie_id>/",
        DetailAcheteurStrategieView.as_view(),
        name="detail-strategie-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-strategie/<int:strategie_id>/",
        EditAcheteurStrategieView.as_view(),
        name="edit-strategie-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-strategies/",
        DeleteAcheteurStrategieView.as_view(),
        name="delete-strategie-acheteur",
    ),
    # URLs pour les stratégies et planifications
    path('api/acheteur/<int:acheteur_id>/strategies-oneview/', 
        AcheteurStrategiePlanificationListOneView.as_view(), 
        name='acheteur-strategies-list-oneview'),
    path('api/acheteur/<int:acheteur_id>/strategies-oneview/<int:strategie_id>/', 
        AcheteurStrategiePlanificationDetailOneView.as_view(), 
        name='acheteur-strategie-detail-oneview'),
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-conformites/",
        ListAcheteurConformiteView.as_view(),
        name="list-conformite-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-conformite/",
        SearchAcheteurConformiteView.as_view(),
        name="search-conformite-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-conformite/",
        AddAcheteurConformiteView.as_view(),
        name="add-conformite-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-conformite/<int:conformite_id>/",
        DetailAcheteurConformiteView.as_view(),
        name="detail-conformite-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-conformite/<int:conformite_id>/",
        EditAcheteurConformiteView.as_view(),
        name="edit-conformite-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-conformites/",
        DeleteAcheteurConformiteView.as_view(),
        name="delete-conformite-acheteur",
    ),
    # URLs pour les conformités et réglementations
    path('api/acheteur/<int:acheteur_id>/conformites-oneview/', 
        AcheteurConformiteReglementationListOneView.as_view(), 
        name='acheteur-conformites-list-oneview'),
    path('api/acheteur/<int:acheteur_id>/conformites-oneview/<int:conformite_id>/', 
        AcheteurConformiteReglementationDetailOneView.as_view(), 
        name='acheteur-conformite-detail-oneview'),
    
    
    
    
    
    
    
    
    
    
    
    
    path(
        "api/alertes/liste-des-alertes/",
        ListAlerteLogView.as_view(),
        name="list-alerte",
    ),
    path(
        "api/alertes/recherche-alerte/",
        SearchAlerteLogView.as_view(),
        name="search-alerte",
    ),
    path(
        "api/alertes/ajouter-une-alerte/",
        AddAlerteLogView.as_view(),
        name="add-alerte",
    ),
    path(
        "api/alertes/detail-alerte/<int:alerte_id>/",
        DetailAlerteLogView.as_view(),
        name="detail-alerte",
    ),
    path(
        "api/alertes/editer-une-alerte/<int:alerte_id>/",
        EditAlerteLogView.as_view(),
        name="edit-alerte",
    ),
    path(
        "api/alertes/supprimer-des-alertes/",
        DeleteAlerteLogView.as_view(),
        name="delete-alerte",
    ),
    path(
        "api/bilan-bancaire/assets/liste/<int:acheteur_id>/",
        ListAssetsView.as_view(),
        name="list-assets-by-acheteur",
    ),
    path(
        "api/bilan-bancaire/assets/ajouter/",
        AddMultiYearAssetsView.as_view(),
        name="add-multi-year-assets",
    ),
    path(
        "api/bilan-bancaire/assets/detail/<int:asset_id>/",
        GetAssetView.as_view(),
        name="get-asset",
    ),
    path(
        "api/bilan-bancaire/assets/editer/<int:asset_id>/",
        EditAssetView.as_view(),
        name="edit-asset",
    ),
    path(
        "api/bilan-bancaire/assets/supprimer/",
        DeleteAssetsView.as_view(),
        name="delete-assets",
    ),
    path(
        "api/bilan-bancaire/liabilities/liste/<int:acheteur_id>/",
        ListLiabilitiesView.as_view(),
        name="list-liabilities-by-acheteur",
    ),
    path(
        "api/bilan-bancaire/liabilities/ajouter/",
        AddMultiYearLiabilitiesView.as_view(),
        name="add-multi-year-liabilities",
    ),
    path(
        "api/bilan-bancaire/liabilities/detail/<int:liability_id>/",
        GetLiabilityView.as_view(),
        name="get-liability",
    ),
    path(
        "api/bilan-bancaire/liabilities/editer/<int:liability_id>/",
        EditLiabilityView.as_view(),
        name="edit-liability",
    ),
    path(
        "api/bilan-bancaire/liabilities/supprimer/",
        DeleteLiabilitiesView.as_view(),
        name="delete-liabilities",
    ),
    path(
        "api/bilan-bancaire/expenses/liste/<int:acheteur_id>/",
        ListExpensesView.as_view(),
        name="list-expenses-by-acheteur",
    ),
    path(
        "api/bilan-bancaire/expenses/ajouter/",
        AddMultiYearExpensesView.as_view(),
        name="add-multi-year-expenses",
    ),
    path(
        "api/bilan-bancaire/expenses/detail/<int:expense_id>/",
        GetExpenseView.as_view(),
        name="get-expense",
    ),
    path(
        "api/bilan-bancaire/expenses/editer/<int:expense_id>/",
        EditExpenseView.as_view(),
        name="edit-expense",
    ),
    path(
        "api/bilan-bancaire/expenses/supprimer/",
        DeleteExpensesView.as_view(),
        name="delete-expenses",
    ),
    path(
        "api/bilan-bancaire/products/liste/<int:acheteur_id>/",
        ListProductsView.as_view(),
        name="list-products-by-acheteur",
    ),
    path(
        "api/bilan-bancaire/products/ajouter/",
        AddMultiYearProductsView.as_view(),
        name="add-multi-year-products",
    ),
    path(
        "api/bilan-bancaire/products/detail/<int:product_id>/",
        GetProductView.as_view(),
        name="get-product",
    ),
    path(
        "api/bilan-bancaire/products/editer/<int:product_id>/",
        EditProductView.as_view(),
        name="edit-product",
    ),
    path(
        "api/bilan-bancaire/products/supprimer/",
        DeleteProductsView.as_view(),
        name="delete-products",
    ),
    path(
        "api/bilan-bancaire/off-balance-sheet/liste/<int:acheteur_id>/",
        ListOffBalanceSheetsView.as_view(),
        name="list-off-balance-sheets-by-acheteur",
    ),
    path(
        "api/bilan-bancaire/off-balance-sheet/ajouter/",
        AddMultiYearOffBalanceSheetsView.as_view(),
        name="add-multi-year-off-balance-sheets",
    ),
    path(
        "api/bilan-bancaire/off-balance-sheet/detail/<int:off_balance_sheet_id>/",
        GetOffBalanceSheetView.as_view(),
        name="get-off-balance-sheet",
    ),
    path(
        "api/bilan-bancaire/off-balance-sheet/editer/<int:off_balance_sheet_id>/",
        EditOffBalanceSheetView.as_view(),
        name="edit-off-balance-sheet",
    ),
    path(
        "api/bilan-bancaire/off-balance-sheet/supprimer/",
        DeleteOffBalanceSheetsView.as_view(),
        name="delete-off-balance-sheets",
    ),
    # --- Actif IFRS ---
    path(
        "api/bilan-ifrs/actifs/liste/<int:acheteur_id>/",
        ListActifsIFRSView.as_view(),
        name="ifrs-list-actifs",
    ),
    path(
        "api/bilan-ifrs/actifs/ajouter/",
        AddMultiYearActifsIFRSView.as_view(),
        name="ifrs-add-multi-actifs",
    ),
    path(
        "api/bilan-ifrs/actifs/detail/<int:pk>/",
        GetActifIFRSView.as_view(),
        name="ifrs-get-actif",
    ),
    path(
        "api/bilan-ifrs/actifs/editer/<int:pk>/",
        EditActifIFRSView.as_view(),
        name="ifrs-edit-actif",
    ),
    path(
        "api/bilan-ifrs/actifs/supprimer/",
        DeleteActifsIFRSView.as_view(),
        name="ifrs-delete-actifs",
    ),
    # --- Passif IFRS ---
    path(
        "api/bilan-ifrs/passifs/liste/<int:acheteur_id>/",
        ListPassifsIFRSView.as_view(),
        name="ifrs-list-passifs",
    ),
    path(
        "api/bilan-ifrs/passifs/ajouter/",
        AddMultiYearPassifsIFRSView.as_view(),
        name="ifrs-add-multi-passifs",
    ),
    path(
        "api/bilan-ifrs/passifs/detail/<int:pk>/",
        GetPassifIFRSView.as_view(),
        name="ifrs-get-passif",
    ),
    path(
        "api/bilan-ifrs/passifs/editer/<int:pk>/",
        EditPassifIFRSView.as_view(),
        name="ifrs-edit-passif",
    ),
    path(
        "api/bilan-ifrs/passifs/supprimer/",
        DeletePassifsIFRSView.as_view(),
        name="ifrs-delete-passifs",
    ),
    # --- Compte de Résultat IFRS ---
    path(
        "api/bilan-ifrs/resultats/liste/<int:acheteur_id>/",
        ListResultatsIFRSView.as_view(),
        name="ifrs-list-resultats",
    ),
    path(
        "api/bilan-ifrs/resultats/ajouter/",
        AddMultiYearResultatsIFRSView.as_view(),
        name="ifrs-add-multi-resultats",
    ),
    path(
        "api/bilan-ifrs/resultats/detail/<int:pk>/",
        GetResultatIFRSView.as_view(),
        name="ifrs-get-resultat",
    ),
    path(
        "api/bilan-ifrs/resultats/editer/<int:pk>/",
        EditResultatIFRSView.as_view(),
        name="ifrs-edit-resultat",
    ),
    path(
        "api/bilan-ifrs/resultats/supprimer/",
        DeleteResultatsIFRSView.as_view(),
        name="ifrs-delete-resultats",
    ),
    # --- Ratios IFRS (Lecture seule) ---
    path(
        "api/bilan-ifrs/ratios/liste/<int:acheteur_id>/",
        ListRatiosIFRSView.as_view(),
        name="ifrs-list-ratios",
    ),
    path(
        "api/bilan-ifrs/ratios/detail/<int:pk>/",
        GetRatioIFRSView.as_view(),
        name="ifrs-get-ratio",
    ),
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-portables/",
        ListAcheteurPortableView.as_view(),
        name="list-portable-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-portable/",
        SearchAcheteurPortableView.as_view(),
        name="search-portable-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-portable/",
        AddAcheteurPortableView.as_view(),
        name="add-portable-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-portable/<int:portable_id>/",
        EditAcheteurPortableView.as_view(),
        name="edit-portable-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-portables/",
        DeleteAcheteurPortableView.as_view(),
        name="delete-portable-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/portables/', 
         AcheteurPortableListView.as_view(), 
         name='acheteur-portables-list'),
    
    path('api/acheteur/<int:acheteur_id>/portables/<int:portable_id>/', 
         AcheteurPortableDetailView.as_view(), 
         name='acheteur-portable-detail'),
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-emails/",
        ListAcheteurEmailView.as_view(),
        name="list-email-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-email/",
        SearchAcheteurEmailView.as_view(),
        name="search-email-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-email/",
        AddAcheteurEmailView.as_view(),
        name="add-email-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-email/<int:email_id>/",
        EditAcheteurEmailView.as_view(),
        name="edit-email-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-emails/",
        DeleteAcheteurEmailView.as_view(),
        name="delete-email-acheteur",
    ),
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-adresses/",
        ListAcheteurAdresseView.as_view(),
        name="list-adresse-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-adresse/",
        SearchAcheteurAdresseView.as_view(),
        name="search-adresse-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-adresse/",
        AddAcheteurAdresseView.as_view(),
        name="add-adresse-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-adresse/<int:adresse_id>/",
        EditAcheteurAdresseView.as_view(),
        name="edit-adresse-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-adresses/",
        DeleteAcheteurAdresseView.as_view(),
        name="delete-adresse-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/adresses/', 
        AcheteurAdresseListView.as_view(), 
        name='acheteur-adresses-list'),
    path('api/acheteur/<int:acheteur_id>/adresses/<int:adresse_id>/', 
        AcheteurAdresseDetailView.as_view(), 
        name='acheteur-adresse-detail'),
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-analyses-swot/",
        ListAcheteurSwotView.as_view(),
        name="list-swot-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-swot/",
        SearchAcheteurSwotView.as_view(),
        name="search-swot-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-analyse-swot/",
        AddAcheteurSwotView.as_view(),
        name="add-swot-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-analyse-swot/<int:swot_id>/",
        EditAcheteurSwotView.as_view(),
        name="edit-swot-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-analyses-swot/",
        DeleteAcheteurSwotView.as_view(),
        name="delete-swot-acheteur",
    ),
    # Dans votre fichier urls.py API
    path('api/acheteur/<int:acheteur_id>/swot-oneview/', 
         AcheteurSwotListOneView.as_view(), 
         name='acheteur-swot-list-oneview'),
    path('api/acheteur/<int:acheteur_id>/swot-oneview/<int:swot_id>/', 
         AcheteurSwotDetailOneView.as_view(), 
         name='acheteur-swot-detail-oneview'),
    
    
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-produits-services/",
        ListAcheteurProduitServiceView.as_view(),
        name="list-produit-service-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-produit-service/",
        SearchAcheteurProduitServiceView.as_view(),
        name="search-produit-service-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-produit-service/",
        AddAcheteurProduitServiceView.as_view(),
        name="add-produit-service-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-produit-service/<int:ps_id>/",
        EditAcheteurProduitServiceView.as_view(),
        name="edit-produit-service-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-produits-services/",
        DeleteAcheteurProduitServiceView.as_view(),
        name="delete-produit-service-acheteur",
    ),
    # Produits et Services
    path('api/acheteur/<int:acheteur_id>/produits-services-oneview/', 
        AcheteurProduitServiceListOneView.as_view(), 
        name='acheteur-produits-services-list-oneview'),
    path('api/acheteur/<int:acheteur_id>/produits-services-oneview/<int:produit_service_id>/', 
        AcheteurProduitServiceDetailOneView.as_view(), 
        name='acheteur-produit-service-detail-oneview'),
    
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-marques/",
        ListAcheteurMarqueView.as_view(),
        name="list-marque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-marque/",
        SearchAcheteurMarqueView.as_view(),
        name="search-marque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-marque/",
        AddAcheteurMarqueView.as_view(),
        name="add-marque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-marque/<int:marque_id>/",
        EditAcheteurMarqueView.as_view(),
        name="edit-marque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-marques/",
        DeleteAcheteurMarqueView.as_view(),
        name="delete-marque-acheteur",
    ),
    # Marques
    path('api/acheteur/<int:acheteur_id>/marques-oneview/', 
        AcheteurMarqueListOneView.as_view(), 
        name='acheteur-marques-list-oneview'),
    path('api/acheteur/<int:acheteur_id>/marques-oneview/<int:marque_id>/', 
        AcheteurMarqueDetailOneView.as_view(), 
        name='acheteur-marque-detail-oneview'),
    
    
    
    
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-procedures-collectives/",
        ListAcheteurProcedureCollectiveView.as_view(),
        name="list-procedure-collective-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-procedure-collective/",
        SearchAcheteurProcedureCollectiveView.as_view(),
        name="search-procedure-collective-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-procedure-collective/",
        AddAcheteurProcedureCollectiveView.as_view(),
        name="add-procedure-collective-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-procedure-collective/<int:pc_id>/",
        EditAcheteurProcedureCollectiveView.as_view(),
        name="edit-procedure-collective-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-procedures-collectives/",
        DeleteAcheteurProcedureCollectiveView.as_view(),
        name="delete-procedure-collective-acheteur",
    ),
    # Dans votre fichier urls.py API
    path('api/acheteur/<int:acheteur_id>/procedures-collectives-oneview/', 
         AcheteurProcedureCollectiveListOneView.as_view(), 
         name='acheteur-procedures-collectives-list-oneview'),
    path('api/acheteur/<int:acheteur_id>/procedures-collectives-oneview/<int:procedure_id>/', 
         AcheteurProcedureCollectiveDetailOneView.as_view(), 
         name='acheteur-procedure-collective-detail-oneview'),
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-registres-commerce/",
        ListAcheteurRegistreCommerceView.as_view(),
        name="list-registre-commerce-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-registre-commerce/",
        SearchAcheteurRegistreCommerceView.as_view(),
        name="search-registre-commerce-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-registre-commerce/",
        AddAcheteurRegistreCommerceView.as_view(),
        name="add-registre-commerce-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-registre-commerce/<int:rc_id>/",
        EditAcheteurRegistreCommerceView.as_view(),
        name="edit-registre-commerce-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-registres-commerce/",
        DeleteAcheteurRegistreCommerceView.as_view(),
        name="delete-registre-commerce-acheteur",
    ),
    # Registres de commerce
    path('api/acheteur/<int:acheteur_id>/registres-commerce-oneview/', 
        AcheteurRegistreCommerceListOneView.as_view(), 
        name='acheteur-registres-commerce-list-oneview'),
    path('api/acheteur/<int:acheteur_id>/registres-commerce-oneview/<int:registre_id>/', 
        AcheteurRegistreCommerceDetailOneView.as_view(), 
        name='acheteur-registre-commerce-detail-oneview'),
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-cotisations/",
        ListAcheteurCotisationView.as_view(),
        name="list-cotisation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-cotisation/",
        SearchAcheteurCotisationView.as_view(),
        name="search-cotisation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-cotisation/",
        AddAcheteurCotisationView.as_view(),
        name="add-cotisation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-cotisation/<int:cotisation_id>/",
        EditAcheteurCotisationView.as_view(),
        name="edit-cotisation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-cotisations/",
        DeleteAcheteurCotisationView.as_view(),
        name="delete-cotisation-acheteur",
    ),
    # Cotisations sociales
    path('api/acheteur/<int:acheteur_id>/cotisations-oneview/', 
        AcheteurCotisationListOneView.as_view(), 
        name='acheteur-cotisations-list-oneview'),
    path('api/acheteur/<int:acheteur_id>/cotisations-oneview/<int:cotisation_id>/', 
        AcheteurCotisationDetailOneView.as_view(), 
        name='acheteur-cotisation-detail-oneview'),
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-documents/",
        ListAcheteurDocumentView.as_view(),
        name="list-document-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-document/",
        SearchAcheteurDocumentView.as_view(),
        name="search-document-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-document/",
        AddAcheteurDocumentView.as_view(),
        name="add-document-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-document/<int:document_id>/",
        EditAcheteurDocumentView.as_view(),
        name="edit-document-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-documents/",
        DeleteAcheteurDocumentView.as_view(),
        name="delete-document-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-cotisations/",
        ListAcheteurCotisationView.as_view(),
        name="list-cotisation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-cotisation/",
        SearchAcheteurCotisationView.as_view(),
        name="search-cotisation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-cotisation/",
        AddAcheteurCotisationView.as_view(),
        name="add-cotisation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-cotisation/<int:cotisation_id>/",
        EditAcheteurCotisationView.as_view(),
        name="edit-cotisation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-cotisations/",
        DeleteAcheteurCotisationView.as_view(),
        name="delete-cotisation-acheteur",
    ),
    
    
    
    
    
    
    # Liste et recherche des numéros de téléphone pour un acheteur donné
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-telephones/",
        ListAcheteurTelephoneView.as_view(),
        name="list-telephone-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-telephone/",
        AddAcheteurTelephoneView.as_view(),
        name="add-telephone-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-telephone/<int:telephone_id>/",
        EditAcheteurTelephoneView.as_view(),
        name="edit-telephone-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-telephones/",
        DeleteAcheteurTelephoneView.as_view(),
        name="delete-telephone-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/telephones/', 
     AcheteurTelephoneListView.as_view(), 
     name='acheteur-telephones-list'),
    path('api/acheteur/<int:acheteur_id>/telephones/<int:telephone_id>/', 
        AcheteurTelephoneDetailView.as_view(), 
        name='acheteur-telephone-detail'),
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-marques/",
        ListAcheteurMarqueView.as_view(),
        name="list-marque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-marque/",
        SearchAcheteurMarqueView.as_view(),
        name="search-marque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-marque/",
        AddAcheteurMarqueView.as_view(),
        name="add-marque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-marque/<int:marque_id>/",
        EditAcheteurMarqueView.as_view(),
        name="edit-marque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-marque/<int:marque_id>/",
        DetailAcheteurMarqueView.as_view(),
        name="detail-marque-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-marques/",
        DeleteAcheteurMarqueView.as_view(),
        name="delete-marque-acheteur",
    ),
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-produits-services/",
        ListAcheteurProduitServiceView.as_view(),
        name="list-produit-service-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-produit-service/",
        SearchAcheteurProduitServiceView.as_view(),
        name="search-produit-service-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-un-produit-service/",
        AddAcheteurProduitServiceView.as_view(),
        name="add-produit-service-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-un-produit-service/<int:produit_service_id>/",
        EditAcheteurProduitServiceView.as_view(),
        name="edit-produit-service-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-produit-service/<int:produit_service_id>/",
        DetailAcheteurProduitServiceView.as_view(),
        name="detail-produit-service-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-produits-services/",
        DeleteAcheteurProduitServiceView.as_view(),
        name="delete-produit-service-acheteur",
    ),
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-des-cotisations/",
        ListAcheteurCotisationView.as_view(),
        name="list-cotisation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-cotisation/",
        SearchAcheteurCotisationView.as_view(),
        name="search-cotisation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-une-cotisation/",
        AddAcheteurCotisationView.as_view(),
        name="add-cotisation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-une-cotisation/<int:cotisation_id>/",
        EditAcheteurCotisationView.as_view(),
        name="edit-cotisation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-cotisation/<int:cotisation_id>/",
        DetailAcheteurCotisationView.as_view(),
        name="detail-cotisation-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-des-cotisations/",
        DeleteAcheteurCotisationView.as_view(),
        name="delete-cotisation-acheteur",
    ),
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-swot/",
        ListAcheteurSwotView.as_view(),
        name="list-swot-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-swot/",
        AddAcheteurSwotView.as_view(),
        name="add-swot-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-swot/",
        DetailAcheteurSwotView.as_view(),
        name="detail-swot-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-swot/",
        EditAcheteurSwotView.as_view(),
        name="edit-swot-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-swot/",
        DeleteAcheteurSwotView.as_view(),
        name="delete-swot-acheteur",
    ),
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-registre-commerce/",
        ListAcheteurRegistreCommerceView.as_view(),
        name="list-registre-commerce-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-registre-commerce/",
        AddAcheteurRegistreCommerceView.as_view(),
        name="add-registre-commerce-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-registre-commerce/",
        DetailAcheteurRegistreCommerceView.as_view(),
        name="detail-registre-commerce-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-registre-commerce/",
        EditAcheteurRegistreCommerceView.as_view(),
        name="edit-registre-commerce-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-registre-commerce/",
        DeleteAcheteurRegistreCommerceView.as_view(),
        name="delete-registre-commerce-acheteur",
    ),
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-procedures-collectives/",
        ListAcheteurProcedureCollectiveView.as_view(),
        name="list-procedure-collective-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-procedure-collective/",
        SearchAcheteurProcedureCollectiveView.as_view(),
        name="search-procedure-collective-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-procedure-collective/",
        AddAcheteurProcedureCollectiveView.as_view(),
        name="add-procedure-collective-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-procedure-collective/<int:procedure_id>/",
        DetailAcheteurProcedureCollectiveView.as_view(),
        name="detail-procedure-collective-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-procedure-collective/<int:procedure_id>/",
        EditAcheteurProcedureCollectiveView.as_view(),
        name="edit-procedure-collective-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-procedures-collectives/",
        DeleteAcheteurProcedureCollectiveView.as_view(),
        name="delete-procedure-collective-acheteur",
    ),
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-documents/",
        ListAcheteurDocumentView.as_view(),
        name="list-document-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-document/",
        SearchAcheteurDocumentView.as_view(),
        name="search-document-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-document/",
        AddAcheteurDocumentView.as_view(),
        name="add-document-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-document/<int:document_id>/",
        DetailAcheteurDocumentView.as_view(),
        name="detail-document-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-document/<int:document_id>/",
        EditAcheteurDocumentView.as_view(),
        name="edit-document-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-documents/",
        DeleteAcheteurDocumentView.as_view(),
        name="delete-document-acheteur",
    ),
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-adresses/",
        ListAcheteurAdresseView.as_view(),
        name="list-adresse-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-adresse/",
        AddAcheteurAdresseView.as_view(),
        name="add-adresse-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-adresse/<int:adresse_id>/",
        DetailAcheteurAdresseView.as_view(),
        name="detail-adresse-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-adresse/<int:adresse_id>/",
        EditAcheteurAdresseView.as_view(),
        name="edit-adresse-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-adresses/",
        DeleteAcheteurAdresseView.as_view(),
        name="delete-adresse-acheteur",
    ),
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-portables/",
        ListAcheteurPortableView.as_view(),
        name="list-portable-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-portable/",
        SearchAcheteurPortableView.as_view(),
        name="search-portable-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-portable/",
        AddAcheteurPortableView.as_view(),
        name="add-portable-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-portable/<int:portable_id>/",
        DetailAcheteurPortableView.as_view(),
        name="detail-portable-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-portable/<int:portable_id>/",
        EditAcheteurPortableView.as_view(),
        name="edit-portable-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-portables/",
        DeleteAcheteurPortableView.as_view(),
        name="delete-portable-acheteur",
    ),
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-telephones/",
        ListAcheteurTelephoneView.as_view(),
        name="list-telephone-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-telephone/",
        SearchAcheteurTelephoneView.as_view(),
        name="search-telephone-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-telephone/",
        AddAcheteurTelephoneView.as_view(),
        name="add-telephone-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-telephone/<int:telephone_id>/",
        DetailAcheteurTelephoneView.as_view(),
        name="detail-telephone-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-telephone/<int:telephone_id>/",
        EditAcheteurTelephoneView.as_view(),
        name="edit-telephone-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-telephones/",
        DeleteAcheteurTelephoneView.as_view(),
        name="delete-telephone-acheteur",
    ),
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/liste-emails/",
        ListAcheteurEmailView.as_view(),
        name="list-email-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-email/",
        SearchAcheteurEmailView.as_view(),
        name="search-email-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-email/",
        AddAcheteurEmailView.as_view(),
        name="add-email-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-email/<int:email_id>/",
        DetailAcheteurEmailView.as_view(),
        name="detail-email-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-email/<int:email_id>/",
        EditAcheteurEmailView.as_view(),
        name="edit-email-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-emails/",
        DeleteAcheteurEmailView.as_view(),
        name="delete-email-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/emails/', 
     AcheteurEmailListView.as_view(), 
     name='acheteur-emails-list'),
    path('api/acheteur/<int:acheteur_id>/emails/<int:email_id>/', 
        AcheteurEmailDetailView.as_view(), 
        name='acheteur-email-detail'),
    
    
    
    
    
    
    
    
    
    
    
    
    
    # Codes NACE
    path(
        "api/codes-nace/subcategories/",
        ListAllSubCategoriesView.as_view(),
        name="list-all-subcategories-nace-code",
    ),
    path(
        "api/codes-nace/categories/",
        ListCategoryNaceCodeView.as_view(),
        name="list-category-nace-code",
    ),
    path(
        "api/codes-nace/categories/<int:category_id>/subcategories/",
        ListSubCategoryNaceCodeView.as_view(),
        name="list-subcategory-nace-code",
    ),
    # Codes NACE Acheteur
    path(
        "api/acheteur/<int:acheteur_id>/liste-codes-nace/",
        ListAcheteurCodeNaceView.as_view(),
        name="list-code-nace-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-code-nace/",
        SearchAcheteurCodeNaceView.as_view(),
        name="search-code-nace-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-code-nace/",
        AddAcheteurCodeNaceView.as_view(),
        name="add-code-nace-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-code-nace/<int:code_nace_id>/",
        DetailAcheteurCodeNaceView.as_view(),
        name="detail-code-nace-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-code-nace/<int:code_nace_id>/",
        EditAcheteurCodeNaceView.as_view(),
        name="edit-code-nace-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-codes-nace/",
        DeleteAcheteurCodeNaceView.as_view(),
        name="delete-code-nace-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/codes-nace-oneview/', 
         AcheteurCodeNaceListOneView.as_view(), 
         name='acheteur-codes-nace-list-oneview'),
    path('api/acheteur/<int:acheteur_id>/codes-nace-oneview/<int:code_nace_id>/', 
         AcheteurCodeNaceDetailOneView.as_view(), 
         name='acheteur-code-nace-detail-oneview'),
    path('api/subcategories-nace-oneview/', 
         SubCategoryNaceCodeListOneView.as_view(), 
         name='subcategories-nace-list-oneview'),
    
    
    
    
    
    
    
    
    
    
    
    
    # Codes NACE pour acheteurs
    path('api/acheteur/<int:acheteur_id>/codes-nace/', 
         AcheteurCodeNaceListView.as_view(), 
         name='acheteur-codes-nace-list'),
    
    path('api/acheteur/<int:acheteur_id>/codes-nace/<int:code_nace_id>/', 
         AcheteurCodeNaceDetailView.as_view(), 
         name='acheteur-code-nace-detail'),
    
    # Recherche de codes NACE
    path('api/codes-nace/search/', 
         SearchSubCategoryNaceCodeView.as_view(), 
         name='search-subcategory-nace'),
    
    # Catégories NACE
    path('api/codes-nace/categories/', 
         CategoryNaceCodeListView.as_view(), 
         name='category-nace-list'),
    
    # Codes NACE disponibles pour un acheteur
    path('api/acheteur/<int:acheteur_id>/codes-nace/available/', 
         AcheteurAvailableCodesNaceView.as_view(), 
         name='acheteur-available-codes-nace'),
    
    
    path(
        "api/acheteurs/<int:acheteur_id>/codes-nace/",
        ListAcheteurCodeNaceView.as_view(),
        name="acheteur-codes-nace-list"
    ),
    path(
        "api/acheteurs/<int:acheteur_id>/codes-nace/<int:code_nace_id>/",
        DetailAcheteurCodeNaceView.as_view(),
        name="acheteur-code-nace-detail"
    ),
    path(
        "api/acheteurs/<int:acheteur_id>/codes-nace/add/",
        AddAcheteurCodeNaceView.as_view(),
        name="acheteur-code-nace-add"
    ),
    path(
        "api/acheteurs/<int:acheteur_id>/codes-nace/<int:code_nace_id>/edit/",
        EditAcheteurCodeNaceView.as_view(),
        name="acheteur-code-nace-edit"
    ),
    path(
        "api/acheteurs/<int:acheteur_id>/codes-nace/delete/",
        DeleteAcheteurCodeNaceView.as_view(),
        name="acheteur-code-nace-delete"
    ),
    path(
        "api/acheteurs/<int:acheteur_id>/codes-nace/search/",
        SearchAcheteurCodeNaceView.as_view(),
        name="acheteur-code-nace-search"
    ),
    path(
        "api/acheteurs/<int:acheteur_id>/codes-nace/available/",
        AvailableCodesNaceForAcheteurView.as_view(),  # À créer
        name="acheteur-codes-nace-available"
    ),
    
    # URLs pour les codes NACE généraux
    path(
        "api/codes-nace/categories/",
        ListCategoryNaceCodeView.as_view(),
        name="codes-nace-categories"
    ),
    path(
        "api/codes-nace/subcategories/",
        ListAllSubCategoriesView.as_view(),
        name="codes-nace-subcategories"
    ),
    path(
        "api/codes-nace/search/",
        SearchSubCategoryNaceCodeView.as_view(),  # À créer
        name="codes-nace-search"
    ),
    path(
        "api/codes-nace/category/<int:category_id>/subcategories/",
        ListSubCategoryNaceCodeView.as_view(),
        name="codes-nace-subcategories-by-category"
    ),
    
    
    
    
    
    
    
    
    
    
    
    path(
        "api/codes-naf/categories/",
        ListCategoryNafCodeView.as_view(),
        name="list-category-naf-code",
    ),
    path(
        "api/codes-naf/subcategories/",
        ListAllSubCategoryNafCodeView.as_view(),
        name="list-all-subcategories-naf-code",
    ),
    path(
        "api/codes-naf/categories/<int:category_id>/subcategories/",
        ListSubCategoryNafCodeView.as_view(),
        name="list-subcategory-naf-code",
    ),
    # Codes NAF Acheteur
    path(
        "api/acheteur/<int:acheteur_id>/liste-codes-naf/",
        ListAcheteurCodeNafView.as_view(),
        name="list-code-naf-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/recherche-code-naf/",
        SearchAcheteurCodeNafView.as_view(),
        name="search-code-naf-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/ajouter-code-naf/",
        AddAcheteurCodeNafView.as_view(),
        name="add-code-naf-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/detail-code-naf/<int:code_naf_id>/",
        DetailAcheteurCodeNafView.as_view(),
        name="detail-code-naf-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/editer-code-naf/<int:code_naf_id>/",
        EditAcheteurCodeNafView.as_view(),
        name="edit-code-naf-acheteur",
    ),
    path(
        "api/acheteur/<int:acheteur_id>/supprimer-codes-naf/",
        DeleteAcheteurCodeNafView.as_view(),
        name="delete-code-naf-acheteur",
    ),
    path('api/acheteur/<int:acheteur_id>/codes-naf-oneview/', 
         AcheteurCodeNafListOneView.as_view(), 
         name='acheteur-codes-naf-list-oneview'),
    path('api/acheteur/<int:acheteur_id>/codes-naf-oneview/<int:code_naf_id>/', 
         AcheteurCodeNafDetailOneView.as_view(), 
         name='acheteur-code-naf-detail-oneview'),
    path('api/subcategories-naf-oneview/', 
         SubCategoryNafCodeListOneView.as_view(), 
         name='subcategories-naf-list-oneview'),
    
    
    
    
    
    
    
    
    
    path(
        "api/acheteur/<int:acheteur_id>/generer-report/",
        GenerateReport.as_view(),
        name="generer-report",
    ),
    path('api/acheteur/<int:acheteur_id>/generer-report-final/', generer_rapport_solvabilite,  name='generer_rapport_solvabilite'),
    
    
    
    path(
        "api/liste-des-modeles-age-societe/",
        ListModeleAgeSocieteView.as_view(),
        name="list-modele-age-societe",
    ),
    path(
        "api/recherche-modele-age-societe/",
        SearchModeleAgeSocieteView.as_view(),
        name="search-modele-age-societe",
    ),
    path(
        "api/ajouter-un-modele-age-societe/",
        AddModeleAgeSocieteView.as_view(),
        name="add-modele-age-societe",
    ),
    path(
        "api/editer-un-modele-age-societe/<int:id>/",
        EditModeleAgeSocieteView.as_view(),
        name="edit-modele-age-societe",
    ),
    path(
        "api/supprimer-des-modeles-age-societe/",
        DeleteModeleAgeSocieteView.as_view(),
        name="delete-modele-age-societe",
    ),
    
    
    
    
    
    
    path(
        "api/liste-des-comportements-de-jugement/",
        ListModeleComportementJugementView.as_view(),
        name="list-comportement-de-jugement",
    ),
    path(
        "api/recherche-comportement-de-jugement/",
        SearchModeleComportementJugementView.as_view(),
        name="search-comportement-de-jugement",
    ),
    path(
        "api/ajouter-un-comportement-de-jugement/",
        AddModeleComportementJugementView.as_view(),
        name="add-comportement-de-jugement",
    ),
    path(
        "api/editer-un-comportement-de-jugement/<int:id>/",
        EditModeleComportementJugementView.as_view(),
        name="edit-comportement-de-jugement",
    ),
    path(
        "api/supprimer-des-comportements-de-jugement/",
        DeleteModeleComportementJugementView.as_view(),
        name="delete-comportement-de-jugement",
    ),

    
    
    
    # --- URLs pour les Actifs Classiques ---
    path(
        "api/bilan-classique/actif/liste/<int:acheteur_id>/",
        ListActifCView.as_view(),
        name="list-actif-c-by-acheteur",
    ),
    path(
        "api/bilan-classique/actif/ajouter/",
        AddMultiYearActifCView.as_view(),
        name="add-multi-year-actif-c",
    ),
    path(
        "api/bilan-classique/actif/detail/<int:actif_id>/",
        GetActifCView.as_view(),
        name="get-actif-c",
    ),
    path(
        "api/bilan-classique/actif/editer/<int:actif_id>/",
        EditActifCView.as_view(),
        name="edit-actif-c",
    ),
    path(
        "api/bilan-classique/actif/supprimer/",
        DeleteActifCView.as_view(),
        name="delete-actif-c",
    ),

    # --- URLs pour les Passifs Classiques ---
    path(
        "api/bilan-classique/passif/liste/<int:acheteur_id>/",
        ListPassifCView.as_view(),
        name="list-passif-c-by-acheteur",
    ),
    path(
        "api/bilan-classique/passif/ajouter/",
        AddMultiYearPassifCView.as_view(),
        name="add-multi-year-passif-c",
    ),
    path(
        "api/bilan-classique/passif/detail/<int:passif_id>/",
        GetPassifCView.as_view(),
        name="get-passif-c",
    ),
    path(
        "api/bilan-classique/passif/editer/<int:passif_id>/",
        EditPassifCView.as_view(),
        name="edit-passif-c",
    ),
    path(
        "api/bilan-classique/passif/supprimer/",
        DeletePassifCView.as_view(),
        name="delete-passif-c",
    ),

    # --- URLs pour les Résultats Classiques ---
    path(
        "api/bilan-classique/resultat/liste/<int:acheteur_id>/",
        ListResultatCView.as_view(),
        name="list-resultat-c-by-acheteur",
    ),
    path(
        "api/bilan-classique/resultat/ajouter/",
        AddMultiYearResultatCView.as_view(),
        name="add-multi-year-resultat-c",
    ),
    path(
        "api/bilan-classique/resultat/detail/<int:resultat_id>/",
        GetResultatCView.as_view(),
        name="get-resultat-c",
    ),
    path(
        "api/bilan-classique/resultat/editer/<int:resultat_id>/",
        EditResultatCView.as_view(),
        name="edit-resultat-c",
    ),
    path(
        "api/bilan-classique/resultat/supprimer/",
        DeleteResultatCView.as_view(),
        name="delete-resultat-c",
    ),
    
    
    
    
    path(
        "api/bilan-syscohada/actif/ajouter/",
        AddMultiYearActifSView.as_view(),
        name="add-multi-year-actif-s",
    ),
    path(
        "api/bilan-syscohada/actif/detail/<int:actif_id>/",
        GetActifSView.as_view(),
        name="get-actif-s",
    ),
    path(
        "api/bilan-syscohada/actif/editer/<int:actif_id>/",
        EditActifSView.as_view(),
        name="edit-actif-s",
    ),
    path(
        "api/bilan-syscohada/actif/supprimer/",
        DeleteActifSView.as_view(),
        name="delete-actif-s",
    ),

    # --- URLs pour les Passifs SYSCOHADA ---
    path(
        "api/bilan-syscohada/passif/liste/<int:acheteur_id>/",
        ListPassifSView.as_view(),
        name="list-passif-s-by-acheteur",
    ),
    path(
        "api/bilan-syscohada/passif/ajouter/",
        AddMultiYearPassifSView.as_view(),
        name="add-multi-year-passif-s",
    ),
    path(
        "api/bilan-syscohada/passif/detail/<int:passif_id>/",
        GetPassifSView.as_view(),
        name="get-passif-s",
    ),
    path(
        "api/bilan-syscohada/passif/editer/<int:passif_id>/",
        EditPassifSView.as_view(),
        name="edit-passif-s",
    ),
    path(
        "api/bilan-syscohada/passif/supprimer/",
        DeletePassifSView.as_view(),
        name="delete-passif-s",
    ),

    # --- URLs pour les Résultats SYSCOHADA ---
    path(
        "api/bilan-syscohada/resultat/liste/<int:acheteur_id>/",
        ListResultatSView.as_view(),
        name="list-resultat-s-by-acheteur",
    ),
    path(
        "api/bilan-syscohada/resultat/ajouter/",
        AddMultiYearResultatSView.as_view(),
        name="add-multi-year-resultat-s",
    ),
    path(
        "api/bilan-syscohada/resultat/detail/<int:resultat_id>/",
        GetResultatSView.as_view(),
        name="get-resultat-s",
    ),
    path(
        "api/bilan-syscohada/resultat/editer/<int:resultat_id>/",
        EditResultatSView.as_view(),
        name="edit-resultat-s",
    ),
    path(
        "api/bilan-syscohada/resultat/supprimer/",
        DeleteResultatSView.as_view(),
        name="delete-resultat-s",
    ),
    
    
    
    
    # --- URLs pour les Actifs Anglais ---
    path(
        "api/bilan-anglais/actif/liste/<int:acheteur_id>/",
        ListActifAView.as_view(),
        name="list-actif-a-by-acheteur",
    ),
    path(
        "api/bilan-anglais/actif/ajouter/",
        AddMultiYearActifAView.as_view(),
        name="add-multi-year-actif-a",
    ),
    path(
        "api/bilan-anglais/actif/detail/<int:actif_id>/",
        GetActifAView.as_view(),
        name="get-actif-a",
    ),
    path(
        "api/bilan-anglais/actif/editer/<int:actif_id>/",
        EditActifAView.as_view(),
        name="edit-actif-a",
    ),
    path(
        "api/bilan-anglais/actif/supprimer/",
        DeleteActifAView.as_view(),
        name="delete-actif-a",
    ),

    # --- URLs pour les Passifs Anglais ---
    path(
        "api/bilan-anglais/passif/liste/<int:acheteur_id>/",
        ListPassifAView.as_view(),
        name="list-passif-a-by-acheteur",
    ),
    path(
        "api/bilan-anglais/passif/ajouter/",
        AddMultiYearPassifAView.as_view(),
        name="add-multi-year-passif-a",
    ),
    path(
        "api/bilan-anglais/passif/detail/<int:passif_id>/",
        GetPassifAView.as_view(),
        name="get-passif-a",
    ),
    path(
        "api/bilan-anglais/passif/editer/<int:passif_id>/",
        EditPassifAView.as_view(),
        name="edit-passif-a",
    ),
    path(
        "api/bilan-anglais/passif/supprimer/",
        DeletePassifAView.as_view(),
        name="delete-passif-a",
    ),

    # --- URLs pour les Résultats Anglais ---
    path(
        "api/bilan-anglais/resultat/liste/<int:acheteur_id>/",
        ListResultatAView.as_view(),
        name="list-resultat-a-by-acheteur",
    ),
    path(
        "api/bilan-anglais/resultat/ajouter/",
        AddMultiYearResultatAView.as_view(),
        name="add-multi-year-resultat-a",
    ),
    path(
        "api/bilan-anglais/resultat/detail/<int:resultat_id>/",
        GetResultatAView.as_view(),
        name="get-resultat-a",
    ),
    path(
        "api/bilan-anglais/resultat/editer/<int:resultat_id>/",
        EditResultatAView.as_view(),
        name="edit-resultat-a",
    ),
    path(
        "api/bilan-anglais/resultat/supprimer/",
        DeleteResultatAView.as_view(),
        name="delete-resultat-a",
    ),
    
    
    
    path("api/acheteur/<int:acheteur_id>/scoring/", ScoringSansBilanAcheteurDetailView.as_view(), name="api_acheteur_scoring"),
    path("api/comportement-paiement/", ModeleComportementPaiementScoringListView.as_view(), name="api_comportement_paiement_list"),
    path("api/forme-juridique/", FormeJuridiqueScoringListView.as_view(), name="api_forme_juridique_list"),
    path("api/age-societe/", ModeleAgeSocieteScoringListView.as_view(), name="api_age_societe_list"),
    path("api/avis-commercial/", ModeleAvisCommercialScoringListView.as_view(), name="api_avis_commercial_list"),
    path("api/bail/", ModeleBailScoringListView.as_view(), name="api_bail_list"),
    path("api/categorie-nace/", CategoryNaceCodeScoringListView.as_view(), name="api_categorie_nace_list"),
    
    path('api/calculer-score/', calculer_score_acrema_bilan, name='calculer_score'),
    path('api/calculer-score-direct/', calculer_score_direct, name='calculer_score_direct'),
    path('api/historique/<int:acheteur_id>/', historique_scores_acheteur, name='historique_scores'),
    
    # URLs pour le scoring avec bilan classique
    path('api/scoring/bilan-classique/calculer-score/', calculer_score_bilan_classique, name='calculer_score_bilan_classique'),
    path('api/scoring/bilan-classique/acheteurs/<int:acheteur_id>/annees/', get_annees_bilan_classique, name='annees_bilan_classique'),
    path('api/scoring/bilan-classique/acheteurs/<int:acheteur_id>/annees/<int:annee>/details/', get_details_bilan_classique, name='details_bilan_classique'),
    
    # URLs pour le scoring avec bilan anglais
    path('api/scoring/bilan-anglais/calculer-score/', calculer_score_bilan_anglais, name='calculer_score_bilan_anglais'),
    path('api/scoring/bilan-anglais/acheteurs/<int:acheteur_id>/annees/', get_annees_bilan_anglais, name='annees_bilan_anglais'),
    path('api/scoring/bilan-anglais/acheteurs/<int:acheteur_id>/annees/<int:annee>/details/', get_details_bilan_anglais, name='details_bilan_anglais'),
    
    path('api/scoring/bilan-bancaire/calculer-score/', calculer_score_bilan_bancaire, name='calculer_score_bilan_bancaire'),
    path('api/scoring/bilan-bancaire/acheteurs/<int:acheteur_id>/annees/', get_annees_bilan_bancaire, name='get_annees_bilan_bancaire'),
    
    
    path('api/scoring/bilan-syscohada/calculer-score/', calculer_score_bilan_syscohada, name='calculer_score_bilan_syscohada'),
    path('api/scoring/bilan-syscohada/acheteurs/<int:acheteur_id>/annees/', get_annees_bilan_syscohada, name='get_annees_bilan_syscohada'),
    
    path('api/scoring/bilan-ifrs/calculer-score/', calculer_score_bilan_ifrs, name='calculer_score_bilan_ifrs'),
    path('api/scoring/bilan-ifrs/acheteurs/<int:acheteur_id>/annees/', get_annees_bilan_ifrs, name='get_annees_bilan_ifrs'),
    
    path('api/reporting/annees/', liste_annees, name='liste_annees'),
    path('api/reporting/devises/', liste_devises, name='liste_devises'),
    path('api/reporting/commandes/acheteur/<int:acheteur_id>/', liste_commandes_acheteur, name='liste_commandes_acheteur'),
    path('api/reporting/generer-rapport-solvabilite/', generer_rapport_solvabilite, name='generer_rapport_solvabilite'),
    
    
    path('api/mailing/clients/', ClientListView.as_view(), name='client-list'),
    path('api/mailing/clients/<int:client_id>/commandes/', get_client_commandes, name='client-commandes'),
    path('api/mailing/documents-by-acheteurs/', get_documents_by_acheteurs, name='documents-by-acheteurs'),
    path('api/mailing/commandes-acheteurs/', get_acheteurs_by_commandes, name='commandes-acheteurs'),
    # path('api/mailing/generate-report/', generate_report, name='generate-report'),
    # path('api/mailing/generate-report-commandes-acheteurs/', GenerateReportCommandeAcheteur.as_view(), name='generate-commandes-acheteurs'),
    
    path('api/mailing/clients/autocomplete/', get_clients_autocomplete, name='api_mailing_clients_autocomplete'),
    path('api/mailing/client/<int:client_id>/commandes/', get_commandes_by_client, name='api_mailing_client_commandes'),
    path('api/mailing/documents/by-acheteurs/', get_documents_by_acheteurs, name='api_mailing_documents_by_acheteurs'),
    # path('api/mailing/send-detailed-email/', send_detailed_email, name='api_mailing_send_detailed_email'),
    # path('api/mailing/send-email/', send_rapports_email, name='api_mailing_send_email'),
    # path('api/mailing/history/', get_email_history, name='api_mailing_history'),
    # path('api/mailing/history/<int:mail_id>/', get_mail_details, name='api_mailing_history_detail'),
    
    # path('api/mailing/clients/', get_clients, name='api_mailing_clients'),
    # path('api/mailing/commandes-acheteurs/', get_acheteurs_from_commandes, name='api_mailing_commandes_acheteurs'),
    # path('api/mailing/generate-report/', generate_report, name='api_mailing_generate_report'),
    # path('api/mailing/send-email/', send_email, name='api_mailing_send_email'),
    
    
    
    # Clients
    # path('api/mailing/clients/', get_clients, name='api_mailing_clients'),
    # path('api/mailing/clients/autocomplete/', get_clients_autocomplete, name='api_mailing_clients_autocomplete'),
    
    # Commandes
    path('api/mailing/clients/<int:client_id>/commandes/', get_commandes_by_client, name='api_mailing_client_commandes'),
    
    # Documents
    path('api/mailing/documents/by-acheteurs/', get_documents_by_acheteurs, name='api_mailing_documents_by_acheteurs'),
    path('api/mailing/commandes-acheteurs/', get_acheteurs_from_commandes, name='api_mailing_commandes_acheteurs'),
    
    # Rapports
    path('api/mailing/generate-report/', generate_report, name='api_mailing_generate_report'),
    
    # Envoi d'emails
    path('api/mailing/send-email/', send_email, name='api_mailing_send_email'),
    
    # Historique
    path('api/mailing/history/', get_email_history, name='api_mailing_history'),
    path('api/mailing/history/<int:mail_id>/', get_mail_details, name='api_mailing_history_detail'),
    
    # Exportation
    path('api/reporting/exporter-rapport/', exporter_rapport, name='exporter_rapport'),
    
    # Load data
    path("load-data/", APILoadDataView.as_view(), name="api-load-data"),
    

        
    
    path("api/profile/", UserProfileView.as_view(), name="user-profile"),
    path("api/profile/avatar/", UserAvatarView.as_view(), name="user-avatar-update"),
    path("api/profile/change-password/", ChangePasswordView.as_view(), name="change-password"),
    
    path('api/database/dump/', DatabaseDumpAPIView.as_view(), name='api-db-dump'),
    path('api/load-data/', APILoadDataView.as_view(), name='api-load-data'),
    path('api/telecharger-data-sql/', telecharger_donnees_postgres_sql_texte, name='telecharger_data_sql'),
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES END                                                                                                      #
    #                                                                                                                      #
    ########################################################################################################################
]
