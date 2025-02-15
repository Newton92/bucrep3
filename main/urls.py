# main/urls.py
from django.urls import path
from django.urls import path, include
from .views import index
from .views import *
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
# from .views import PaysViewSet

from main.api.views_localisation import *
from main.api.views_standard import *
from main.api.views_authentication import *
from main.api.views_acheteur import *
from main.api.views_modules_acheteur import *

# router = DefaultRouter()
# router.register(r'pays', PaysViewSet, basename='pays')

urlpatterns = [
    
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES START FOR AUTH                                                                                           #
    #                                                                                                                      #
    ########################################################################################################################
    path('', index, name='index'),
    path('verification/compte/', check_auth, name='check_auth'),
    path('mot-de-passe-oublie/', forgot_auth, name='forgot_auth'),
    path('reinitialisation-mot-de-passe-oublie/', reset_auth, name='reset_auth'),
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
    path('root-dashboard/', dash_root, name='dash_root'),
    path('root-dashboard/localisation/liste-des-pays', dash_root_pays, name='dash_root_pays'),
    path('root-dashboard/localisation/liste-des-provinces', dash_root_province, name='dash_root_province'),
    path('root-dashboard/localisation/liste-des-villes', dash_root_ville, name='dash_root_ville'),
    
    
    path('root-dashboard/standard/liste-des-devises', dash_root_devise, name='dash_root_devise'),
    path('root-dashboard/standard/liste-des-annees-civiles', dash_root_annee, name='dash_root_annee'),
    path('root-dashboard/standard/liste-des-colorations', dash_root_coloration, name='dash_root_coloration'),
    path('root-dashboard/standard/liste-des-categories-nace', dash_root_category_nace, name='dash_root_category_nace'),
    path('root-dashboard/standard/liste-des-categories-naf', dash_root_category_naf, name='dash_root_category_naf'),
    path('root-dashboard/standard/liste-des-codes-nace', dash_root_code_nace, name='dash_root_code_nace'),
    path('root-dashboard/standard/liste-des-codes-naf', dash_root_code_naf, name='dash_root_code_naf'),
    path('root-dashboard/standard/liste-des-formes-juridiques', dash_root_forme_juridique, name='dash_root_forme_juridique'),
    path('root-dashboard/standard/liste-des-domaines', dash_root_domaine, name='dash_root_domaine'),
    path('root-dashboard/standard/liste-des-postes', dash_root_poste, name='dash_root_poste'),
    path('root-dashboard/standard/liste-des-categories-entreprise', dash_root_category_entreprise, name='dash_root_category_entreprise'),
    path('root-dashboard/standard/liste-des-structures-entreprise', dash_root_structure_entreprise, name='dash_root_structure_entreprise'),
    path('root-dashboard/standard/liste-des-status-entreprise', dash_root_statut_entreprise, name='dash_root_statut_entreprise'),
    
    
    path('root-dashboard/acheteurs/liste-des-acheteurs', dash_root_acheteur, name='dash_root_acheteur'),
    path('root-dashboard/acheteurs/ajouter-un-acheteur', dash_root_add_acheteur, name='dash_root_add_acheteur'),
    path('root-dashboard/acheteurs/editer-un-acheteur/<int:acheteur_id>/', dash_root_edit_acheteur, name='dash_root_edit_acheteur'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/', dash_root_manage_acheteur, name='dash_root_manage_acheteur'),
    
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/resumes/', dash_root_manage_acheteur_resume, name='dash_root_manage_acheteur_resume'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/evaluation-risques/', dash_root_manage_acheteur_risk_rating, name='dash_root_manage_acheteur_risk_rating'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/donnees-enregistrees/', dash_root_manage_acheteur_data_save, name='dash_root_manage_acheteur_data_save'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/tendances/', dash_root_manage_acheteur_tendance, name='dash_root_manage_acheteur_tendance'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/responsables/', dash_root_manage_acheteur_responsable, name='dash_root_manage_acheteur_responsable'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/antecedents-juridiques/', dash_root_manage_acheteur_antecedent, name='dash_root_manage_acheteur_antecedent'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/gestion-des-risques/', dash_root_manage_acheteur_gestion_risque, name='dash_root_manage_acheteur_gestion_risque'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/membres-du-conseil/', dash_root_manage_acheteur_membre_conseil, name='dash_root_manage_acheteur_membre_conseil'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/compositions-du-capital-social/', dash_root_manage_acheteur_composition_capital, name='dash_root_manage_acheteur_composition_capital'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/actionnaires/', dash_root_manage_acheteur_actionnaire, name='dash_root_manage_acheteur_actionnaire'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/opinions-acremac/', dash_root_manage_acheteur_opinion_acremac, name='dash_root_manage_acheteur_opinion_acremac'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/filiales/', dash_root_manage_acheteur_filiale, name='dash_root_manage_acheteur_filiale'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/analyses-sectorielles/', dash_root_manage_acheteur_analyse_sectorielle, name='dash_root_manage_acheteur_analyse_sectorielle'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/comptes-financiers/', dash_root_manage_acheteur_compte_financier, name='dash_root_manage_acheteur_compte_financier'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/operations-et-historiques/', dash_root_manage_acheteur_operation_historique, name='dash_root_manage_acheteur_operation_historique'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/proprietes-et-actifs/', dash_root_manage_acheteur_propriete_actif, name='dash_root_manage_acheteur_propriete_actif'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conditions-achat/', dash_root_manage_acheteur_condition_achat, name='dash_root_manage_acheteur_condition_achat'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conditions-vente/', dash_root_manage_acheteur_condition_vente, name='dash_root_manage_acheteur_condition_vente'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/sommaires-et-avis/', dash_root_manage_acheteur_sommaire_avis, name='dash_root_manage_acheteur_sommaire_avis'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/conseils/', dash_root_manage_acheteur_advice, name='dash_root_manage_acheteur_advice'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/geopolitiques/', dash_root_manage_acheteur_geopolitic, name='dash_root_manage_acheteur_geopolitic'),
    path('root-dashboard/acheteurs/manager-un-acheteur/<int:acheteur_id>/donnees-bancaires/', dash_root_manage_acheteur_banking, name='dash_root_manage_acheteur_banking'),
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
    path('validateur-dashboard/', dash_validateur, name='dash_validateur'),
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
    path('analyste-dashboard/', dash_analyste, name='dash_analyste'),
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
    path('client-dashboard/', dash_client, name='dash_client'),
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
    
    path('api/login/', CustomLoginView.as_view(), name='login'),
    path('double-factor-auth/', CustomDoubleFactorAuthView.as_view(), name='double-factor-auth'),
    path('forgot-password/', CustomForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', CustomResetPasswordView.as_view(), name='reset-password'),
    path('api/logout/', CustomLogoutView.as_view(), name='api-logout'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('api/liste-des-pays/', ListPaysView.as_view(), name='list-pays'),
    path('api/recherche-pays/', SearchPaysView.as_view(), name='search-pays'),
    path('api/ajouter-un-pays/', AddPaysView.as_view(), name='add-pays'),
    path('api/editer-un-pays/<int:id>/', EditPaysView.as_view(), name='edit-pays'),
    path('api/supprimer-des-pays/', DeletePaysView.as_view(), name='delete-pays'),
    
    path('api/liste-des-provinces/', ListProvincesView.as_view(), name='list_provinces'),
    path('api/provinces/<int:country_id>/', ListProvincesByCountryView.as_view(), name='list-provinces-pays'),
    path('api/ajouter-une-province/', AddProvinceView.as_view(), name='add_province'),
    path('api/editer-une-province/<int:id>/', EditProvinceView.as_view(), name='edit_province'),
    path('api/supprimer-des-provinces/', DeleteProvincesView.as_view(), name='delete_provinces'),
    
    path('api/liste-des-villes/', ListVillesView.as_view(), name='list_villes'),
    path('api/villes/<int:province_id>/', ListVillesByProvinceView.as_view(), name='list-villes-provinces'),
    path('api/ajouter-une-ville/', AddVilleView.as_view(), name='add_ville'),
    path('api/editer-une-ville/<int:id>/', EditVilleView.as_view(), name='edit_ville'),
    path('api/supprimer-des-villes/', DeleteVillesView.as_view(), name='delete_villes'),
    
    path('api/liste-des-devises/', ListDeviseView.as_view(), name='list-devise'),
    path('api/recherche-devise/', SearchDeviseView.as_view(), name='search-devise'),
    path('api/ajouter-une-devise/', AddDeviseView.as_view(), name='add-devise'),
    path('api/editer-une-devise/<int:id>/', EditDeviseView.as_view(), name='edit-devise'),
    path('api/supprimer-des-devises/', DeleteDeviseView.as_view(), name='delete-devise'),
    
    path('api/liste-des-annees-civiles/', ListAnneeView.as_view(), name='list-annee'),
    path('api/recherche-annee/', SearchAnneeView.as_view(), name='search-annee'),
    path('api/ajouter-une-annee/', AddAnneeView.as_view(), name='add-annee'),
    path('api/editer-une-annee/<int:id>/', EditAnneeView.as_view(), name='edit-annee'),
    path('api/supprimer-des-annees/', DeleteAnneeView.as_view(), name='delete-annee'),
    
    path('api/liste-des-colorations/', ListColorationView.as_view(), name='list-coloration'),
    path('api/recherche-coloration/', SearchColorationView.as_view(), name='search-coloration'),
    path('api/ajouter-une-coloration/', AddColorationView.as_view(), name='add-coloration'),
    path('api/editer-une-coloration/<int:id>/', EditColorationView.as_view(), name='edit-coloration'),
    path('api/supprimer-des-colorations/', DeleteColorationView.as_view(), name='delete-coloration'),
    
    path('api/liste-des-categories-nace/', ListCategoryNaceView.as_view(), name='list-categorie-nace'),
    path('api/recherche-categorie-nace/', SearchCategoryNaceView.as_view(), name='search-categorie-nace'),
    path('api/ajouter-une-categorie-nace/', AddCategoryNaceView.as_view(), name='add-categorie-nace'),
    path('api/editer-une-categorie-nace/<int:id>/', EditCategoryNaceView.as_view(), name='edit-categorie-nace'),
    path('api/supprimer-des-categories-nace/', DeleteCategoryNaceView.as_view(), name='delete-categorie-nace'),
    
    path('api/liste-des-categories-naf/', ListCategoryNafView.as_view(), name='list-categorie-naf'),
    path('api/recherche-categorie-naf/', SearchCategoryNafView.as_view(), name='search-categorie-naf'),
    path('api/ajouter-une-categorie-naf/', AddCategoryNafView.as_view(), name='add-categorie-naf'),
    path('api/editer-une-categorie-naf/<int:id>/', EditCategoryNafView.as_view(), name='edit-categorie-naf'),
    path('api/supprimer-des-categories-naf/', DeleteCategoryNafView.as_view(), name='delete-categorie-naf'),
    
    path('api/liste-des-codes-nace/', ListCodeNaceView.as_view(), name='list-code-nace'),
    path('api/recherche-codes-nace/', SearchCodeNaceView.as_view(), name='search-code-nace'),
    path('api/ajouter-un-code-nace/', AddCodeNaceView.as_view(), name='add-code-nace'),
    path('api/editer-un-code-nace/<int:id>/', EditCodeNaceView.as_view(), name='edit-code-nace'),
    path('api/supprimer-des-codes-nace/', DeleteCodeNaceView.as_view(), name='delete-code-nace'),
    
    path('api/liste-des-codes-naf/', ListCodeNafView.as_view(), name='list-code-naf'),
    path('api/recherche-codes-naf/', SearchCodeNafView.as_view(), name='search-code-naf'),
    path('api/ajouter-un-code-naf/', AddCodeNafView.as_view(), name='add-code-naf'),
    path('api/editer-un-code-naf/<int:id>/', EditCodeNafView.as_view(), name='edit-code-naf'),
    path('api/supprimer-des-codes-naf/', DeleteCodeNafView.as_view(), name='delete-code-naf'),
    
    path('api/liste-des-formes-juridiques/', ListFormeJuridiqueView.as_view(), name='list-forme-juridique'),
    path('api/recherche-forme-juridique/', SearchFormeJuridiqueView.as_view(), name='search-forme-juridique'),
    path('api/ajouter-une-forme-juridique/', AddFormeJuridiqueView.as_view(), name='add-forme-juridique'),
    path('api/editer-une-forme-juridique/<int:id>/', EditFormeJuridiqueView.as_view(), name='edit-forme-juridique'),
    path('api/supprimer-des-formes-juridiques/', DeleteFormeJuridiqueView.as_view(), name='delete-forme-juridique'),
    
    path('api/liste-des-domaines/', ListDomaineView.as_view(), name='list-domaine'),
    path('api/recherche-domaine/', SearchDomaineView.as_view(), name='search-domaine'),
    path('api/ajouter-une-domaine/', AddDomaineView.as_view(), name='add-domaine'),
    path('api/editer-une-domaine/<int:id>/', EditDomaineView.as_view(), name='edit-domaine'),
    path('api/supprimer-des-domaine/', DeleteDomaineView.as_view(), name='delete-domaine'),
    
    path('api/liste-des-categories-entreprise/', ListCategorieEntrepriseView.as_view(), name='list-categorie-entreprise'),
    path('api/recherche-categorie-entreprise/', SearchCategorieEntrepriseView.as_view(), name='search-categorie-entreprise'),
    path('api/ajouter-une-categorie-entreprise/', AddCategorieEntrepriseView.as_view(), name='add-categorie-entreprise'),
    path('api/editer-une-categorie-entreprise/<int:id>/', EditCategorieEntrepriseView.as_view(), name='edit-categorie-entreprise'),
    path('api/supprimer-des-categories-entreprise/', DeleteCategorieEntrepriseView.as_view(), name='delete-categorie-entreprise'),
    
    path('api/liste-des-structures-entreprise/', ListStructureEntrepriseView.as_view(), name='list-structure-entreprise'),
    path('api/recherche-structure-entreprise/', SearchStructureEntrepriseView.as_view(), name='search-structure-entreprise'),
    path('api/ajouter-une-structure-entreprise/', AddStructureEntrepriseView.as_view(), name='add-structure-entreprise'),
    path('api/editer-une-structure-entreprise/<int:id>/', EditStructureEntrepriseView.as_view(), name='edit-structure-entreprise'),
    path('api/supprimer-des-structures-entreprise/', DeleteStructureEntrepriseView.as_view(), name='delete-structure-entreprise'),
    
    path('api/liste-des-statuts-entreprise/', ListStatutEntrepriseView.as_view(), name='list-statut-entreprise'),
    path('api/recherche-statut-entreprise/', SearchStatutEntrepriseView.as_view(), name='search-statut-entreprise'),
    path('api/ajouter-une-statut-entreprise/', AddStatutEntrepriseView.as_view(), name='add-statut'),
    path('api/editer-une-statut-entreprise/<int:id>/', EditStatutEntrepriseView.as_view(), name='edit-statut-entreprise'),
    path('api/supprimer-des-statuts-entreprise/', DeleteStatutEntrepriseView.as_view(), name='delete-statut-entreprise'),
    
    path('api/liste-des-postes/', ListPosteView.as_view(), name='list-poste'),
    path('api/recherche-poste/', SearchPosteView.as_view(), name='search-poste'),
    path('api/ajouter-une-poste/', AddPosteView.as_view(), name='add-poste'),
    path('api/editer-une-poste/<int:id>/', EditPosteView.as_view(), name='edit-poste'),
    path('api/supprimer-des-postes/', DeletePosteView.as_view(), name='delete-poste'),
    
    path('api/liste-des-acheteurs/', ListAcheteurView.as_view(), name='list-acheteur'),
    path('api/recherche-acheteur/', SearchAcheteurView.as_view(), name='search-acheteur'),
    path('api/ajouter-un-acheteur/', AddAcheteurView.as_view(), name='add-acheteur'),
    path('api/editer-un-acheteur/<int:id>/', EditAcheteurView.as_view(), name='edit-acheteur'),
    path('api/consulter-un-acheteur/<int:id>/', GetAcheteurView.as_view(), name='get-acheteur'),
    path('api/supprimer-des-acheteurs/', DeleteAcheteurView.as_view(), name='delete-acheteur'),
    
    path('api/acheteur/<int:acheteur_id>/liste-des-resumes/', ListAcheteurResumeView.as_view(), name='list-resume-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-resume/', SearchAcheteurResumeView.as_view(), name='search-resume-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-un-resume/', AddAcheteurResumeView.as_view(), name='add-resume-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-un-resume/<int:resume_id>/', EditAcheteurResumeView.as_view(), name='edit-resume-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-resumes/', DeleteAcheteurResumeView.as_view(), name='delete-resume-acheteur'),
    
    path('api/acheteur/<int:acheteur_id>/liste-des-evaluations-de-risque/', ListAcheteurRiskRatingView.as_view(), name='list-risk-rating-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-evaluation-risque/', SearchAcheteurRiskRatingView.as_view(), name='search-risk-rating-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-une-evaluation-risque/', AddAcheteurRiskRatingView.as_view(), name='add-risk-rating-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-une-evaluation-risque/<int:risk_rating_id>/', EditAcheteurRiskRatingView.as_view(), name='edit-risk-rating-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-evaluation-risque/', DeleteAcheteurRiskRatingView.as_view(), name='delete-risk-rating-acheteur'),
    
    path('api/acheteur/<int:acheteur_id>/liste-des-donnees-enregistrees/', ListAcheteurDataSaveView.as_view(), name='list-donnee-enregistree-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-donnee-enregistree/', SearchAcheteurDataSaveView.as_view(), name='search-donnee-enregistree-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-une-donnee-enregistree/', AddAcheteurDataSaveView.as_view(), name='add-donnee-enregistree-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-une-donnee-enregistree/<int:donnee_enregistrement_id>/', EditAcheteurDataSaveView.as_view(), name='edit-donnee-enregistree-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-donnees-enregistrees/', DeleteAcheteurDataSaveView.as_view(), name='delete-donnee-enregistree-acheteur'),
    
    path('api/acheteur/<int:acheteur_id>/liste-des-tendances/', ListAcheteurTendanceView.as_view(), name='list-tendance-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-tendance/', SearchAcheteurTendanceView.as_view(), name='search-tendance-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-une-tendance/', AddAcheteurTendanceView.as_view(), name='add-tendance-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-une-tendance/<int:tendance_id>/', EditAcheteurTendanceView.as_view(), name='edit-tendance-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-tendances/', DeleteAcheteurTendanceView.as_view(), name='delete-tendance-acheteur'),
    
    path('api/acheteur/<int:acheteur_id>/liste-des-responsables/', ListAcheteurResponsableView.as_view(), name='list-responsable-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-responsable/', SearchAcheteurResponsableView.as_view(), name='search-responsable-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-une-responsable/', AddAcheteurResponsableView.as_view(), name='add-responsable-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-une-responsable/<int:responsable_id>/', EditAcheteurResponsableView.as_view(), name='edit-responsable-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-responsables/', DeleteAcheteurResponsableView.as_view(), name='delete-responsable-acheteur'),
    
    path('api/acheteur/<int:acheteur_id>/liste-des-antecdents-juridiques/', ListAcheteurAntecedentView.as_view(), name='list-antecedent-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-antecedent/', SearchAcheteurAntecedentView.as_view(), name='search-antecedent-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-un-antecedent/', AddAcheteurAntecedentView.as_view(), name='add-antecedent-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-un-antecedent/<int:antecedent_id>/', EditAcheteurAntecedentView.as_view(), name='edit-antecedent-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-antecedents/', DeleteAcheteurAntecedentView.as_view(), name='delete-antecedent-acheteur'),
    
    path('api/acheteur/<int:acheteur_id>/liste-des-gestions-de-risque/', ListAcheteurGestionRisqueView.as_view(), name='list-gestion-de-risque-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-gestion-de-risque/', SearchAcheteurGestionRisqueView.as_view(), name='search-gestion-de-risque-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-une-gestion-de-risque/', AddAcheteurGestionRisqueView.as_view(), name='add-gestion-de-risque-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-une-gestion-de-risque/<int:gestion_risque_id>/', EditAcheteurGestionRisqueView.as_view(), name='edit-gestion-de-risque-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-gestions-de-risque/', DeleteAcheteurGestionRisqueView.as_view(), name='delete-gestion-de-risque-acheteur'),
    
    path('api/acheteur/<int:acheteur_id>/liste-des-membres-du-conseil/', ListAcheteurMembreConseilView.as_view(), name='list-membre-du-conseil-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-membre-du-conseil/', SearchAcheteurMembreConseilView.as_view(), name='search-membre-du-conseil-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-un-membre-du-conseil/', AddAcheteurMembreConseilView.as_view(), name='add-membre-du-conseil-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-un-membre-du-conseil/<int:membre_conseil_id>/', EditAcheteurMembreConseilView.as_view(), name='edit-membre-du-conseil-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-membres-du-conseil/', DeleteAcheteurMembreConseilView.as_view(), name='delete-membre-du-conseil-acheteur'),
    
    path('api/acheteur/<int:acheteur_id>/liste-des-compositions-du-capital/', ListAcheteurCompositionCapitalView.as_view(), name='list-composition-du-capital-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-composition-du-capital/', SearchAcheteurCompositionCapitalView.as_view(), name='search-composition-du-capital-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-une-composition-du-capital/', AddAcheteurCompositionCapitalView.as_view(), name='add-composition-du-capital-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-une-composition-du-capital/<int:composition_capital_id>/', EditAcheteurCompositionCapitalView.as_view(), name='edit-composition-du-capital-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-compositions-du-capital/', DeleteAcheteurCompositionCapitalView.as_view(), name='delete-composition-du-capital-acheteur'),
    
    path('api/acheteur/<int:acheteur_id>/liste-des-actionnaires/', ListAcheteurActionnaireView.as_view(), name='list-actionnaire-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-actionnaire/', SearchAcheteurActionnaireView.as_view(), name='search-actionnaire-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-un-actionnaire/', AddAcheteurActionnaireView.as_view(), name='add-actionnaire-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-un-actionnaire/<int:actionnaire_id>/', EditAcheteurActionnaireView.as_view(), name='edit-actionnaire-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-actionnaires/', DeleteAcheteurActionnaireView.as_view(), name='delete-actionnaire-acheteur'),
    
    
    path('api/acheteur/<int:acheteur_id>/liste-des-opinions-acremac/', ListAcheteurOpinionAcremacView.as_view(), name='list-opinion-acremac-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-opinion-acremac/', SearchAcheteurOpinionAcremacView.as_view(), name='search-opinion-acremac-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-une-opinion-acremac/', AddAcheteurOpinionAcremacView.as_view(), name='add-opinion-acremac-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-une-opinion-acremac/<int:opinion_id>/', EditAcheteurOpinionAcremacView.as_view(), name='edit-opinion-acremac-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-opinions-acremac/', DeleteAcheteurOpinionAcremacView.as_view(), name='delete-opinion-acremac-acheteur'),
    
    
    path('api/acheteur/<int:acheteur_id>/liste-des-filiales/', ListAcheteurFilialeView.as_view(), name='list-filiale-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-filiale/', SearchAcheteurFilialeView.as_view(), name='search-filiale-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-une-filiale/', AddAcheteurFilialeView.as_view(), name='add-filiale-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-une-filiale/<int:filiale_id>/', EditAcheteurFilialeView.as_view(), name='edit-filiale-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-filiales/', DeleteAcheteurFilialeView.as_view(), name='delete-filiale-acheteur'),
    
    
    path('api/acheteur/<int:acheteur_id>/liste-des-analyses-sectorielles/', ListAcheteurAnalyseSectorielleView.as_view(), name='list-analyse-sectorielle-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-analyse-sectorielle/', SearchAcheteurAnalyseSectorielleView.as_view(), name='search-analyse-sectorielle-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-une-analyse-sectorielle/', AddAcheteurAnalyseSectorielleView.as_view(), name='add-analyse-sectorielle-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-une-analyse-sectorielle/<int:analyse_id>/', EditAcheteurAnalyseSectorielleView.as_view(), name='edit-analyse-sectorielle-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-analyses-sectorielles/', DeleteAcheteurAnalyseSectorielleView.as_view(), name='delete-analyse-sectorielle-acheteur'),
    
    
    path('api/acheteur/<int:acheteur_id>/liste-des-comptes-financiers/', ListAcheteurCompteFinancierView.as_view(), name='list-compte-financier-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-compte-financier/', SearchAcheteurCompteFinancierView.as_view(), name='search-compte-financier-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-un-compte-financier/', AddAcheteurCompteFinancierView.as_view(), name='add-compte-financier-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-un-compte-financier/<int:compte_financier_id>/', EditAcheteurCompteFinancierView.as_view(), name='edit-compte-financier-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-comptes-financiers/', DeleteAcheteurCompteFinancierView.as_view(), name='delete-compte-financier-acheteur'),
    
    path('api/acheteur/<int:acheteur_id>/liste-des-operations-et-historiques/', ListAcheteurOperationHistoriqueView.as_view(), name='list-operation-et-historique-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-operation-et-historique/', SearchAcheteurOperationHistoriqueView.as_view(), name='search-operation-et-historique-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-une-operation-et-historique/', AddAcheteurOperationHistoriqueView.as_view(), name='add-operation-et-historique-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-une-operation-et-historique/<int:operation_historique_id>/', EditAcheteurOperationHistoriqueView.as_view(), name='edit-operation-et-historique-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-operations-et-historiques/', DeleteAcheteurOperationHistoriqueView.as_view(), name='delete-operation-et-historique-acheteur'),
    
    path('api/acheteur/<int:acheteur_id>/liste-des-proprietes-et-actifs/', ListAcheteurProprieteActifView.as_view(), name='list-propriete-et-actif-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-propriete-et-actif/', SearchAcheteurProprieteActifView.as_view(), name='search-propriete-et-actif-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-une-propriete-et-actif/', AddAcheteurProprieteActifView.as_view(), name='add-propriete-et-actif-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-une-propriete-et-actif/<int:propriete_actif_id>/', EditAcheteurProprieteActifView.as_view(), name='edit-propriete-et-actif-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-proprietes-et-actifs/', DeleteAcheteurProprieteActifView.as_view(), name='delete-propriete-et-actif-acheteur'),
    
    
    path('api/acheteur/<int:acheteur_id>/liste-des-conditions-achat/', ListAcheteurConditionAchatView.as_view(), name='list-condition-achat-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-condition-achat/', SearchAcheteurConditionAchatView.as_view(), name='search-condition-achat-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-une-condition-achat/', AddAcheteurConditionAchatView.as_view(), name='add-condition-achat-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-une-condition-achat/<int:condition_achat_id>/', EditAcheteurConditionAchatView.as_view(), name='edit-condition-achat-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-conditions-achat/', DeleteAcheteurConditionAchatView.as_view(), name='delete-condition-achat-acheteur'),
    
    
    
    path('api/acheteur/<int:acheteur_id>/liste-des-conditions-vente/', ListAcheteurConditionVenteView.as_view(), name='list-condition-vente-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-condition-vente/', SearchAcheteurConditionVenteView.as_view(), name='search-condition-vente-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-une-condition-vente/', AddAcheteurConditionVenteView.as_view(), name='add-condition-vente-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-une-condition-vente/<int:condition_vente_id>/', EditAcheteurConditionVenteView.as_view(), name='edit-condition-vente-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-conditions-vente/', DeleteAcheteurConditionVenteView.as_view(), name='delete-condition-vente-acheteur'),
    
    
    path('api/acheteur/<int:acheteur_id>/liste-des-sommaires-et-avis/', ListAcheteurSommaireAvisView.as_view(), name='list-sommaire-et-avis-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-sommaire-et-avis/', SearchAcheteurSommaireAvisView.as_view(), name='search-sommaire-et-avis-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-un-sommaire-et-avis/', AddAcheteurSommaireAvisView.as_view(), name='add-sommaire-et-avis-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-un-sommaire-et-avis/<int:sommaire_avis_id>/', EditAcheteurSommaireAvisView.as_view(), name='edit-sommaire-et-avis-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-sommaires-et-avis/', DeleteAcheteurSommaireAvisView.as_view(), name='delete-sommaire-et-avis-acheteur'),
    
    
    path('api/acheteur/<int:acheteur_id>/liste-des-conseils/', ListAcheteurConseilView.as_view(), name='list-conseil-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-conseil/', SearchAcheteurConseilView.as_view(), name='search-conseil-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-un-conseil/', AddAcheteurConseilView.as_view(), name='add-conseil-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-un-conseil/<int:advice_id>/', EditAcheteurConseilView.as_view(), name='edit-conseil-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-conseils/', DeleteAcheteurConseilView.as_view(), name='delete-conseil-acheteur'),
    
    
    path('api/acheteur/<int:acheteur_id>/liste-des-donnees-geopolitiques/', ListAcheteurGeopoliticView.as_view(), name='list-donnee-geopolitique-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-donnee-geopolitique/', SearchAcheteurGeopoliticView.as_view(), name='search-donnee-geopolitique-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-un-donnee-geopolitique/', AddAcheteurGeopoliticView.as_view(), name='add-donnee-geopolitique-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-un-donnee-geopolitique/<int:geopolitic_id>/', EditAcheteurGeopoliticView.as_view(), name='edit-donnee-geopolitique-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-donnees-geopolitiques/', DeleteAcheteurGeopoliticView.as_view(), name='delete-donnee-geopolitique-acheteur'),
    
    
    path('api/acheteur/<int:acheteur_id>/liste-des-donnees-bancaires/', ListAcheteurBankingView.as_view(), name='list-donnee-bancaire-acheteur'),
    path('api/acheteur/<int:acheteur_id>/recherche-donnee-bancaire/', SearchAcheteurBankingView.as_view(), name='search-donnee-bancaire-acheteur'),
    path('api/acheteur/<int:acheteur_id>/ajouter-un-donnee-bancaire/', AddAcheteurBankingView.as_view(), name='add-donnee-bancaire-acheteur'),
    path('api/acheteur/<int:acheteur_id>/editer-un-donnee-bancaire/<int:banking_id>/', EditAcheteurBankingView.as_view(), name='edit-donnee-bancaire-acheteur'),
    path('api/acheteur/<int:acheteur_id>/supprimer-des-donnees-bancaires/', DeleteAcheteurBankingView.as_view(), name='delete-donnee-bancaire-acheteur'),
    
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES END                                                                                                      #
    #                                                                                                                      #
    ########################################################################################################################
    

    
    
    
]

# urlpatterns += router.urls
