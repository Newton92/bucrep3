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


# Create your views here.


# === Vues Pages Statiques === #

def index(request):
    return render(request, 'main/index.html')


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



