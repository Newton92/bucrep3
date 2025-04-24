from django.shortcuts import render
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from .serializers import *
import random
import string
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from django.contrib.auth.decorators import login_required
from .utils import send_email_with_secret_code
from django.template.loader import render_to_string
from rest_framework import status
from django.contrib.auth import logout
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django.urls import reverse
from django.contrib.auth import login
from rest_framework.viewsets import ModelViewSet
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from main.utilitaires import constantes

from main.commandes.bucrepcontact_test_fetch_mails import fetch_emails
from main.commandes.fetch_bucrep_mails import fetch_and_save_emails
import threading


    
# Recuperer les mails ici !
# Exécuter la récupération des emails en tâche de fond
def run_fetch_emails():
    try:
        fetch_and_save_emails()
    except Exception as e:
        print(f"Erreur lors de la récupération des emails : {e}")
        
    threading.Thread(target=run_fetch_emails, daemon=True).start()


# Create your views here.


# === Vues Pages Statiques === #

def index(request):
    return render(request, 'main/index.html')


def report(request):
    return render(request, 'main/report_template.html')


def check_auth(request):
    return render(request, 'main/check_auth.html')


def forgot_auth(request):
    return render(request, 'main/forgot_auth.html')


def reset_auth(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/reset_auth.html', {'error': _('Token manquant.')})
    return render(request, 'main/reset_auth.html', {'token': token})



# === VIEWS Dashboards === #


########################################################################################################################
#                                                                                                                      #
#  VIEWS START FOR ROOT                                                                                                #
#                                                                                                                      #
########################################################################################################################

@login_required
def dash_root(request):
    token = request.GET.get('token')
    if not token:
      return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    context = {
        'dash_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
    return render(request, 'main/root/dash_root.html', context)

@login_required
def dash_root_pays(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        'locations_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
    return render(request, 'main/root/pays/dash_root_pays.html', context)


@login_required
def dash_root_province(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    context = {
        'locations_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'pays_list': pays_list,  # Ajouter la liste des pays au contexte
    }
    return render(request, 'main/root/province/dash_root_province.html', context)


@login_required
def dash_root_ville(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Récupérer tous les pays
    # pays_list = Pays.objects.all()
    
    # Récupérer tous les pays
    province_list = Province.objects.all()

    context = {
        'locations_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        # 'pays_list': pays_list,  # Ajouter la liste des pays au contexte
        'province_list': province_list,  # Ajouter la liste des pays au contexte
    }
    return render(request, 'main/root/ville/dash_root_ville.html', context)


@login_required
def dash_root_devise(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Récupérer tous les pays
    pays_list = Pays.objects.all()
    
    # Récupérer tous les pays
    province_list = Province.objects.all()

    context = {
        'codification_active': 'active',
        'devise_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'pays_list': pays_list,  # Ajouter la liste des pays au contexte
        'province_list': province_list,  # Ajouter la liste des pays au contexte
    }
    return render(request, 'main/root/devise/dash_root_devise.html', context)


@login_required
def dash_root_annee(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Récupérer tous les pays
    pays_list = Pays.objects.all()
    
    # Récupérer tous les pays
    province_list = Province.objects.all()

    context = {
        'codification_active': 'active',
        'annee_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/annee/dash_root_annee.html', context)


@login_required
def dash_root_coloration(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'codification_active': 'active',
        'coloration_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/coloration/dash_root_coloration.html', context)


@login_required
def dash_root_category_nace(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'codification_active': 'active',
        'nace_cat_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/nace/dash_root_category_nace.html', context)


@login_required
def dash_root_category_naf(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'codification_active': 'active',
        'naf_cat_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/naf/dash_root_category_naf.html', context)


@login_required
def dash_root_code_nace(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Récupérer tous les categories nace
    categorie_list = CategoryNaceCode.objects.all()
    

    context = {
        'codification_active': 'active',
        'nace_code_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'categorie_list': categorie_list
        
    }
    return render(request, 'main/root/nace/dash_root_code_nace.html', context)


@login_required
def dash_root_code_naf(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Récupérer tous les categories nace
    categorie_list = CategoryNafCode.objects.all()
    

    context = {
        'codification_active': 'active',
        'naf_code_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'categorie_list': categorie_list
        
    }
    return render(request, 'main/root/naf/dash_root_code_naf.html', context)


@login_required
def dash_root_forme_juridique(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'codification_active': 'active',
        'juridique_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/juridique/dash_root_forme_juridique.html', context)



@login_required
def dash_root_domaine(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'codification_active': 'active',
        'domaine_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/domaine/dash_root_domaine.html', context)



@login_required
def dash_root_modele_bail(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'modele_bail_active': 'active',
        'modele_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/modele/dash_root_modele_bail.html', context)



@login_required
def dash_root_modele_bilan(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'modele_bilan_active': 'active',
        'modele_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/modele/dash_root_modele_bilan.html', context)



@login_required
def dash_root_modele_alarme(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'modele_alarme_active': 'active',
        'modele_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/modele/dash_root_modele_alarme.html', context)



@login_required
def dash_root_modele_rapport(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'modele_rapport_active': 'active',
        'modele_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/modele/dash_root_modele_rapport.html', context)



@login_required
def dash_root_modele_avis_commercial(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'modele_avis_active': 'active',
        'modele_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/modele/dash_root_modele_avis_commercial.html', context)



@login_required
def dash_root_modele_relation_entreprise(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'modele_relation_active': 'active',
        'modele_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/modele/dash_root_modele_relation_entreprise.html', context)



@login_required
def dash_root_modele_notation(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'modele_notation_active': 'active',
        'modele_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/modele/dash_root_modele_notation.html', context)



@login_required
def dash_root_modele_comportement_paiement(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'modele_cpaiement_active': 'active',
        'modele_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/modele/dash_root_modele_comportement_paiement.html', context)



@login_required
def dash_root_modele_comportement_jugement(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'modele_cjugement_active': 'active',
        'modele_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/modele/dash_root_modele_comportement_jugement.html', context)



@login_required
def dash_root_modele_information_notation_entreprise(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})
  
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'modele_infone_active': 'active',
        'modele_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/modele/dash_root_modele_information_notation_entreprise.html', context)




@login_required
def dash_root_poste(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupération des domaines
    domaines = DomaineEntreprise.objects.all()

    context = {
        'codification_active': 'active',
        'poste_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'domaines': domaines,  # Ajouter les domaines au contexte
    }
    return render(request, 'main/root/poste/dash_root_poste.html', context)



@login_required
def dash_root_category_entreprise(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        'codification_active': 'active',
        'entreprise_cat_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/entreprise/dash_root_category_entreprise.html', context)



@login_required
def dash_root_structure_entreprise(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        'codification_active': 'active',
        'entreprise_structure_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/structure/dash_root_structure_entreprise.html', context)



@login_required
def dash_root_statut_entreprise(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        'codification_active': 'active',
        'entreprise_statut_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/statut/dash_root_statut_entreprise.html', context)



@login_required
def dash_root_acheteur(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/acheteur/dash_root_acheteur.html', context)


@login_required
def dash_root_add_acheteur(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Récupérer tous les categories d'entreprise
    categorie_list = CategorieEntreprise.objects.all()
    
    # Récupérer tous les formes juridiques
    juridique_list = FormeJuridique.objects.all()
    
    # Récupérer tous les statuts entreprise
    statut_list = StatutEntreprise.objects.all()
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    
    # Récupérer tous les pays
    pays_list = Pays.objects.all()
    
    # Récupérer tous les provinces
    province_list = Province.objects.all()
    
    # Récupérer tous les villes
    ville_list = Ville.objects.all()

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'categorie_list': categorie_list,
        'juridique_list': juridique_list,
        'statut_list': statut_list,
        'coloration_list': coloration_list,
        'pays_list': pays_list,
        'province_list': province_list,
        'ville_list': ville_list,
        
    }
    return render(request, 'main/root/acheteur/dash_root_add_acheteur.html', context)


@login_required
def dash_root_edit_acheteur(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les categories d'entreprise
    categorie_list = CategorieEntreprise.objects.all()
    
    # Récupérer tous les formes juridiques
    juridique_list = FormeJuridique.objects.all()
    
    # Récupérer tous les statuts entreprise
    statut_list = StatutEntreprise.objects.all()
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    
    # Récupérer tous les pays
    pays_list = Pays.objects.all()
    
    # Récupérer tous les provinces
    province_list = Province.objects.all()
    
    # Récupérer tous les villes
    ville_list = Ville.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'categorie_list': categorie_list,
        'juridique_list': juridique_list,
        'statut_list': statut_list,
        'coloration_list': coloration_list,
        'pays_list': pays_list,
        'province_list': province_list,
        'ville_list': ville_list,
        
    }
    return render(request, 'main/root/acheteur/dash_root_edit_acheteur.html', context)


@login_required
def dash_root_manage_acheteur(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les categories d'entreprise
    categorie_list = CategorieEntreprise.objects.all()
    
    # Récupérer tous les formes juridiques
    juridique_list = FormeJuridique.objects.all()
    
    # Récupérer tous les statuts entreprise
    statut_list = StatutEntreprise.objects.all()
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    
    # Récupérer tous les pays
    pays_list = Pays.objects.all()
    
    # Récupérer tous les provinces
    province_list = Province.objects.all()
    
    # Récupérer tous les villes
    ville_list = Ville.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'categorie_list': categorie_list,
        'juridique_list': juridique_list,
        'statut_list': statut_list,
        'coloration_list': coloration_list,
        'pays_list': pays_list,
        'province_list': province_list,
        'ville_list': ville_list,
        
    }
    return render(request, 'main/root/acheteur/dash_root_manage_acheteur.html', context)


@login_required
def dash_root_manage_acheteur_resume(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les devises
    devise_list = Devise.objects.all()
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    
    # Passer les postes du fichier constantes.py ici 
    bons_postes_list = BON_POST_CHOICES_CHOICES
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'devise_list': devise_list,
        'coloration_list': coloration_list,
        'bons_postes_list': bons_postes_list,
        
    }
    return render(request, 'main/root/acheteur/resume/dash_root_manage_acheteur_resume.html', context)


@login_required
def dash_root_manage_acheteur_risk_rating(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
    }
    return render(request, 'main/root/acheteur/riskrating/dash_root_manage_acheteur_risk_rating.html', context)


@login_required
def dash_root_manage_acheteur_data_save(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les statuts d'entreprise
    statut_list = StatutEntreprise.objects.all()
    
    # Récupérer tous les formes juridiques
    juridique_list = FormeJuridique.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'statut_list': statut_list,
        'juridique_list': juridique_list,
        
    }
    return render(request, 'main/root/acheteur/data/dash_root_manage_acheteur_data_save.html', context)



@login_required
def dash_root_manage_acheteur_tendance(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les avis commerciaux
    commercial_list = ModeleAvisCommercial.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'commercial_list': commercial_list,
        
    }
    return render(request, 'main/root/acheteur/tendance/dash_root_manage_acheteur_tendance.html', context)



@login_required
def dash_root_manage_acheteur_responsable(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les avis commerciaux
    poste_list = PosteEntreprise.objects.all()
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'poste_list': poste_list,
        'coloration_list': coloration_list,
        
    }
    return render(request, 'main/root/acheteur/responsable/dash_root_manage_acheteur_responsable.html', context)



@login_required
def dash_root_manage_acheteur_antecedent(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'coloration_list': coloration_list,
        
    }
    return render(request, 'main/root/acheteur/antecedent/dash_root_manage_acheteur_antecedent.html', context)




@login_required
def dash_root_manage_acheteur_gestion_risque(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'coloration_list': coloration_list,
        
    }
    return render(request, 'main/root/acheteur/gestion/dash_root_manage_acheteur_gestion_risque.html', context)





@login_required
def dash_root_manage_acheteur_membre_conseil(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les avis commerciaux
    poste_list = PosteEntreprise.objects.all()
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'poste_list': poste_list,
        'coloration_list': coloration_list,
        
    }
    return render(request, 'main/root/acheteur/conseil/dash_root_manage_acheteur_membre_conseil.html', context)




@login_required
def dash_root_manage_acheteur_composition_capital(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les devises
    devise_list = Devise.objects.all()
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'devise_list': devise_list,
        'coloration_list': coloration_list,
        
    }
    return render(request, 'main/root/acheteur/composition/dash_root_manage_acheteur_composition_capital.html', context)




@login_required
def dash_root_manage_acheteur_actionnaire(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'coloration_list': coloration_list,
        
    }
    return render(request, 'main/root/acheteur/actionnaire/dash_root_manage_acheteur_actionnaire.html', context)



@login_required
def dash_root_manage_acheteur_opinion_acremac(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'coloration_list': coloration_list,
        
    }
    return render(request, 'main/root/acheteur/opinion/dash_root_manage_acheteur_opinion_acremac.html', context)




@login_required
def dash_root_manage_acheteur_filiale(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les structures d'entreprise
    structure_list = StructureEntreprise.objects.all()
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'structure_list': structure_list,
        'coloration_list': coloration_list,
        
    }
    return render(request, 'main/root/acheteur/filiale/dash_root_manage_acheteur_filiale.html', context)




@login_required
def dash_root_manage_acheteur_analyse_sectorielle(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les structures d'entreprise
    structure_list = StructureEntreprise.objects.all()
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'structure_list': structure_list,
        'coloration_list': coloration_list,
        
    }
    return render(request, 'main/root/acheteur/analyse/dash_root_manage_acheteur_analyse_sectorielle.html', context)





@login_required
def dash_root_manage_acheteur_compte_financier(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les modeles de bilan
    bilan_list = ModeleBilan.objects.all()
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'bilan_list': bilan_list,
        'coloration_list': coloration_list,
        
    }
    return render(request, 'main/root/acheteur/finance/dash_root_manage_acheteur_compte_financier.html', context)




@login_required
def dash_root_manage_acheteur_operation_historique(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        
        'coloration_list': coloration_list,
        
    }
    return render(request, 'main/root/acheteur/operation/dash_root_manage_acheteur_operation_historique.html', context)




@login_required
def dash_root_manage_acheteur_propriete_actif(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    
    # Récupérer tous les reference des locaux
    locaux_list = ModeleBail.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'locaux_list': locaux_list,
        
    }
    return render(request, 'main/root/acheteur/propriete/dash_root_manage_acheteur_propriete_actif.html', context)





@login_required
def dash_root_manage_acheteur_condition_achat(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
    }
    return render(request, 'main/root/acheteur/achat/dash_root_manage_acheteur_condition_achat.html', context)






@login_required
def dash_root_manage_acheteur_condition_vente(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    
    # Récupérer tous les modeles de comportement de paiement
    paiement_list = ModeleComportementPaiement.objects.all()
    
    
    # Récupérer tous les reference de comportement de jugement
    jugement_list = ModeleComportementJugement.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'paiement_list': paiement_list,
        'jugement_list': jugement_list,
        
    }
    return render(request, 'main/root/acheteur/vente/dash_root_manage_acheteur_condition_vente.html', context)



@login_required
def dash_root_manage_acheteur_sommaire_avis(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'coloration_list': coloration_list,
        
    }
    return render(request, 'main/root/acheteur/sommaire/dash_root_manage_acheteur_sommaire_avis.html', context)



@login_required
def dash_root_manage_acheteur_advice(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
    }
    return render(request, 'main/root/acheteur/advice/dash_root_manage_acheteur_advice.html', context)




@login_required
def dash_root_manage_acheteur_geopolitic(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
    }
    return render(request, 'main/root/acheteur/geopolitique/dash_root_manage_acheteur_geopolitic.html', context)




@login_required
def dash_root_manage_acheteur_banking(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les villes
    ville_list = Ville.objects.all()
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'ville_list': ville_list,
        'coloration_list': coloration_list,
        
    }
    return render(request, 'main/root/acheteur/banque/dash_root_manage_acheteur_banking.html', context)





@login_required
def dash_root_manage_acheteur_actif_anglais(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/anglais/dash_root_manage_acheteur_actif_anglais.html', context)



@login_required
def dash_root_manage_acheteur_passif_anglais(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/anglais/dash_root_manage_acheteur_passif_anglais.html', context)



@login_required
def dash_root_manage_acheteur_resultat_anglais(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/anglais/dash_root_manage_acheteur_resultat_anglais.html', context)





@login_required
def dash_root_manage_acheteur_actif_classique(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/classique/dash_root_manage_acheteur_actif_classique.html', context)






@login_required
def dash_root_manage_acheteur_passif_classique(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/classique/dash_root_manage_acheteur_passif_classique.html', context)




@login_required
def dash_root_manage_acheteur_resultat_classique(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/classique/dash_root_manage_acheteur_resultat_classique.html', context)



@login_required
def dash_root_manage_acheteur_actif_syscohada(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/syscohada/dash_root_manage_acheteur_actif_syscohada.html', context)



@login_required
def dash_root_manage_acheteur_passif_syscohada(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/syscohada/dash_root_manage_acheteur_passif_syscohada.html', context)




@login_required
def dash_root_manage_acheteur_resultat_syscohada(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/syscohada/dash_root_manage_acheteur_resultat_syscohada.html', context)




@login_required
def dash_root_manage_acheteur_asset_bancaire(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/bancaire/dash_root_manage_acheteur_asset_bancaire.html', context)





@login_required
def dash_root_manage_acheteur_liabilitie_bancaire(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/bancaire/dash_root_manage_acheteur_liabilitie_bancaire.html', context)





@login_required
def dash_root_manage_acheteur_offbalancesheet_bancaire(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/bancaire/dash_root_manage_acheteur_offbalancesheet_bancaire.html', context)




@login_required
def dash_root_manage_acheteur_expense_bancaire(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/bancaire/dash_root_manage_acheteur_expense_bancaire.html', context)



@login_required
def dash_root_manage_acheteur_product_bancaire(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/bancaire/dash_root_manage_acheteur_product_bancaire.html', context)





@login_required
def dash_root_manage_acheteur_compte_financier_irfs(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
    }
    return render(request, 'main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_compte_financier_irfs.html', context)


@login_required
def dash_root_manage_acheteur_ratio_financier_irfs(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
    }
    return render(request, 'main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_ratio_financier_irfs.html', context)




@login_required
def dash_root_manage_acheteur_actif_irfs(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(type_compte__icontains='Actif')
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    
    # Récupérer tous les devises
    devise_list = Devise.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        'devise_list': devise_list,
        'compte_financier_irfs_list': compte_financier_irfs_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_actif_irfs.html', context)





@login_required
def dash_root_manage_acheteur_passif_irfs(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(type_compte__icontains='Passif')
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    
    # Récupérer tous les devises
    devise_list = Devise.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        'devise_list': devise_list,
        'compte_financier_irfs_list': compte_financier_irfs_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_passif_irfs.html', context)




@login_required
def dash_root_manage_acheteur_resultat_irfs(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(type_compte__icontains='Compte de ')
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    
    # Récupérer tous les devises
    devise_list = Devise.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        'devise_list': devise_list,
        'compte_financier_irfs_list': compte_financier_irfs_list,
        
    }
    return render(request, 'main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_passif_irfs.html', context)




@login_required
def dash_root_manage_acheteur_add_actif_irfs(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(type_compte__icontains='Actif')
    
    # Récupérer tous les actifs financiers irfs
    actif_financier_irfs_list = ValeurCompteIrfs.objects.filter(compte__type_compte__icontains='Actif', acheteur__pk=id_acheteur)
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    
    # Récupérer tous les devises
    devise_list = Devise.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        'devise_list': devise_list,
        'compte_financier_irfs_list': compte_financier_irfs_list,
        'actif_financier_irfs_list': actif_financier_irfs_list
        
    }
    return render(request, 'main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_add_actif_irfs.html', context)



@login_required
def dash_root_manage_acheteur_add_passif_irfs(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(type_compte__icontains='Passif')
    
    # Récupérer tous les actifs financiers irfs
    actif_financier_irfs_list = ValeurCompteIrfs.objects.filter(compte__type_compte__icontains='Passif', acheteur__pk=id_acheteur)
    
    # Récupérer tous les annees
    annee_list = Annee.objects.all()
    
    # Récupérer tous les devises
    devise_list = Devise.objects.all()
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
        'annee_list': annee_list,
        'devise_list': devise_list,
        'compte_financier_irfs_list': compte_financier_irfs_list,
        'actif_financier_irfs_list': actif_financier_irfs_list
        
    }
    return render(request, 'main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_add_passif_irfs.html', context)





@login_required
def dash_root_manage_acheteur_report_web(request, acheteur_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id
    
    # Recuperer les elements du rapports ici !
    

    context = {
        'acheteur_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_acheteur': id_acheteur,
        
    }
    return render(request, 'main/root/acheteur/report/dash_root_manage_acheteur_report_web.html', context)








@login_required
def dash_root_commande(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Récupérer tous les devises
    devise_list_one = Devise.objects.all()
    
    # Récupérer tous les devises
    devise_list_two = Devise.objects.all()
    
    # Récupérer tous les acheteurs
    acheteur_list = Acheteur.objects.all()
    
    # Récupérer tous les clients
    client_list = CustomUser.objects.filter(Q(role__icontains="Client") | Q(role__icontains="client")).order_by('id')
    
    # Récupérer tous les villes
    ville_list = Ville.objects.all()
    
    # Récupérer tous les modeles de rapport
    modele_rapport_list = ModeleRapport.objects.all()

    context = {
        'requests_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'devise_list_one': devise_list_one,
        'devise_list_two': devise_list_two,
        'client_list': client_list,
        'ville_list': ville_list,
        'acheteur_list': acheteur_list,
        'modele_rapport_list': modele_rapport_list,
        
    }
    return render(request, 'main/root/orders/dash_root_commande.html', context)






@login_required
def dash_root_manage_commande(request, commande_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de la commande
    id_commande = commande_id
    
    # Récupérer tous les categories d'entrepris
    

    context = {
        'requests_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_commande': id_commande,
        
        
    }
    return render(request, 'main/root/orders/dash_root_manage_commande.html', context)






@login_required
def dash_root_alerte(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    

    context = {
        'alerts_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        
    }
    return render(request, 'main/root/warning/dash_root_alerte.html', context)




@login_required
def dash_root_add_alerte(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        'alerts_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
    }
    return render(request, 'main/root/warning/dash_root_add_alerte.html', context)



@login_required
def dash_root_edit_alerte(request, alerte_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'alerte
    id_alerte = alerte_id
    
    # Récupérer tous les documents lies a l'alerte
    # document_list = DocumentAlerte.objects.fliter(alerte__pk=id_alerte)
    
    # Récupérer tous les clients
    # client_list = CustomUser.objects.filter(Q(role__icontains="Client") | Q(role__icontains="client")).order_by('id')
    

    context = {
        'alerts_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_alerte': id_alerte,
        
        # 'document_list': document_list,
        # 'client_list': client_list,
        
    }
    return render(request, 'main/root/warning/dash_root_edit_alerte.html', context)




@login_required
def dash_root_manage_alerte(request, alerte_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Recuperer l'id de l'alerte
    id_alerte = alerte_id
    
    # Récupérer l'alerte
    alerte = Alerte.objects.fliter(alerte__pk=id_alerte).first()
    
    # Récupérer tous les documents lies a l'alerte
    document_list = DocumentAlerte.objects.fliter(alerte__pk=id_alerte)
    
    # Récupérer tous les clients
    client_list = CustomUser.objects.filter(Q(role__icontains="Client") | Q(role__icontains="client")).order_by('id')
    

    context = {
        'alerts_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'id_alerte': id_alerte,
        
        'alerte': alerte,
        'document_list': document_list,
        'client_list': client_list,
        
    }
    return render(request, 'main/root/warning/dash_root_manage_alerte.html', context)




@login_required
def dash_root_client(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    

    context = {
        'clients_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        
    }
    return render(request, 'main/root/monitoring/dash_root_client.html', context)









@login_required
def dash_root_portefeuille(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Récupérer les clients
    client_list = Client.objects.all()
    
    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()
    

    context = {
        'portefeuilles_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'client_list': client_list,
        'acheteur_list': acheteur_list,
        
        
    }
    return render(request, 'main/root/monitoring/dash_root_portefeuille.html', context)




@login_required
def dash_root_add_portefeuille(request):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Récupérer les clients
    client_list = Client.objects.all()
    
    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()
    
    # Récupérer tous les categories d'entreprise
    categorie_list = CategorieEntreprise.objects.all()
    
    # Récupérer tous les formes juridiques
    juridique_list = FormeJuridique.objects.all()
    
    # Récupérer tous les statuts entreprise
    statut_list = StatutEntreprise.objects.all()
    
    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    
    # Récupérer tous les pays
    pays_list = Pays.objects.all()
    
    # Récupérer tous les provinces
    province_list = Province.objects.all()
    
    # Récupérer tous les villes
    ville_list = Ville.objects.all()
    

    context = {
        'portefeuilles_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'client_list': client_list,
        'acheteur_list': acheteur_list,
        
        
    }
    return render(request, 'main/root/monitoring/dash_root_add_portefeuille.html', context)


@login_required
def dash_root_edit_portefeuille(request, portefeuille_id):
    token = request.GET.get('token')
    if not token:
        return render(request, 'main/index.html', {'error': _('Token manquant.')})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)
    
    # Récupérer le portefeuille à modifier
    try:
        portefeuille = Portefeuille.objects.get(id=portefeuille_id)
    except Portefeuille.DoesNotExist:
        return render(request, 'main/index.html', {'error': _('Portefeuille non trouvé.')})

    # Récupérer les clients
    client_list = Client.objects.all()
    
    # Récupérer les acheteurs associés à ce portefeuille
    acheteurs_associes = PortefeuilleClient.objects.filter(portefeuille=portefeuille).values_list('acheteur_id', flat=True)
    acheteur_list = Acheteur.objects.all()

    context = {
        'portefeuilles_active': 'active',
        
        'user': user,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        
        'portefeuille': portefeuille,  # Données du portefeuille à modifier
        'acheteurs_associes': list(acheteurs_associes),  # Liste des IDs des acheteurs associés
        
        'client_list': client_list,
        'acheteur_list': acheteur_list,
    }
    return render(request, 'main/root/monitoring/dash_root_edit_portefeuille.html', context)



########################################################################################################################
#                                                                                                                      #
#  VIEWS END FOR ROOT                                                                                                  #
#                                                                                                                      #
########################################################################################################################














@login_required
def dash_validateur(request):
    return render(request, 'main/validateur/dash_validateur.html')


@login_required
def dash_analyste(request):
    return render(request, 'main/analyste/dash_analyste.html')


@login_required
def dash_client(request):
    return render(request, 'main/client/dash_client.html')



