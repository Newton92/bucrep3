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
    #  API ROUTES END FOR CLIENT                                                                                                    #
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
    path('api/provinces/<int:country_id>/', ListProvincesByCountryView.as_view(), name='list-provinces'),
    path('api/ajouter-une-province/', AddProvinceView.as_view(), name='add_province'),
    path('api/editer-une-province/<int:id>/', EditProvinceView.as_view(), name='edit_province'),
    path('api/supprimer-des-provinces/', DeleteProvincesView.as_view(), name='delete_provinces'),
    
    path('api/liste-des-villes/', ListVillesView.as_view(), name='list_villes'),
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
    
    ########################################################################################################################
    #                                                                                                                      #
    #  API ROUTES END                                                                                                      #
    #                                                                                                                      #
    ########################################################################################################################
    

    
    
    
]

# urlpatterns += router.urls
