import json
import re
import random
import threading
from django.core.cache import cache

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from django.utils.translation import gettext_lazy as _, get_language
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from main.commandes.fetch_bucrep_mails import fetch_and_save_emails
from main.models import User
from main.serializers import *
from main.constantes import *  # IMPORTANT: importer depuis constantes.py

from django.http import HttpResponse
from django.contrib.auth import get_user_model

from main.models import User  # assurez-vous d'importer correctement votre modèle
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from main.utils import populate_database, create_fake_commands, create_fake_buyers
from django.utils import timezone
from faker import Faker
import random
from django.db.models import Q, Count, Sum
from main.utils import generate_test_commandes

import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from main.models import Client, Commande, Acheteur, Pays, Ville, Devise, ModeleRapport, SuiviCommande

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Sum


import json
from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.tokens import RefreshToken

from main.models import ActifC, PassifC, ResultatC, Annee, Acheteur
from main.models import TYPE_BILAN_CHOICES, SEMESTRE_CHOICES

import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from rest_framework_simplejwt.tokens import RefreshToken

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
import logging
from rest_framework_simplejwt.tokens import RefreshToken

from main.models import Acheteur, Annee


logger = logging.getLogger(__name__)


User = get_user_model()


def _resolve_pays_id(request, persist=True):
    """
    Résout le pays actif (même logique que views_acheteur._resolve_selected_pays_id).
    Priorité : session → user.pays_actif → user.pays → None.
    """
    selected_pays_id = None

    session_value = request.session.get("selected_pays_id")
    if session_value:
        try:
            sid = int(session_value)
        except (TypeError, ValueError):
            sid = None
        if sid and Pays.objects.filter(id=sid, afficher_au_dashboard=True).exists():
            selected_pays_id = sid

    if not selected_pays_id:
        pays_actif_id = getattr(request.user, "pays_actif_id", None)
        if pays_actif_id and Pays.objects.filter(id=pays_actif_id, afficher_au_dashboard=True).exists():
            selected_pays_id = pays_actif_id

    if not selected_pays_id:
        user_pays = getattr(request.user, "pays", None)
        if user_pays:
            selected_pays_id = user_pays.id

    if persist:
        if selected_pays_id:
            request.session["selected_pays_id"] = selected_pays_id
        else:
            request.session.pop("selected_pays_id", None)

    return selected_pays_id

elements = [
    {
        "nom": "Changement de niveau de scoring",
        "code_interne": "SCORING_CHANGE",
        "categorie": "Santé Financière et Risque de Crédit",
        "sous_categorie": "Évaluation et Notation",
    },
    {
        "nom": "Changement de Limite de crédit",
        "code_interne": "CREDIT_LIMIT_CHANGE",
        "categorie": "Santé Financière et Risque de Crédit",
        "sous_categorie": "Évaluation et Notation",
    },
    {
        "nom": "Incorporation de nouveaux états financiers",
        "code_interne": "NEW_FINANCIALS",
        "categorie": "Santé Financière et Risque de Crédit",
        "sous_categorie": "Transparence et Fiabilité Financière",
    },
    {
        "nom": "Alerte sur faux états financiers",
        "code_interne": "FAKE_FINANCIALS_ALERT",
        "categorie": "Santé Financière et Risque de Crédit",
        "sous_categorie": "Transparence et Fiabilité Financière",
    },
    {
        "nom": "Changement de Raison sociale",
        "code_interne": "COMPANY_NAME_CHANGE",
        "categorie": "Identité et Structure de l'Entreprise",
        "sous_categorie": "Changements d'identification",
    },
    {
        "nom": "Changement d’Adresse / Téléphone",
        "code_interne": "CONTACT_INFO_CHANGE",
        "categorie": "Identité et Structure de l'Entreprise",
        "sous_categorie": "Changements d'identification",
    },
    {
        "nom": "Changement de Maison-mère",
        "code_interne": "PARENT_COMPANY_CHANGE",
        "categorie": "Identité et Structure de l'Entreprise",
        "sous_categorie": "Changements structurels",
    },
    {
        "nom": "Procédure de sauvegarde",
        "code_interne": "SAFEGUARD_PROCEDURE",
        "categorie": "Procédures Collectives et Difficultés",
        "sous_categorie": "Procédures Préventives et Curatives",
    },
    {
        "nom": "Redressement ou procédure judiciaire",
        "code_interne": "JUDICIAL_RECOVERY_PROCEDURE",
        "categorie": "Procédures Collectives et Difficultés",
        "sous_categorie": "Procédures Préventives et Curatives",
    },
    {
        "nom": "Dissolution de l'entreprise",
        "code_interne": "DISSOLUTION",
        "categorie": "Procédures Collectives et Difficultés",
        "sous_categorie": "Cessation d'Activité",
    },
    {
        "nom": "Liquidation de l’entreprise",
        "code_interne": "LIQUIDATION",
        "categorie": "Procédures Collectives et Difficultés",
        "sous_categorie": "Cessation d'Activité",
    },
    {
        "nom": "Redressement URSAFF, Trésor Public, etc.",
        "code_interne": "PUBLIC_DEBT_RECOVERY",
        "categorie": "Obligations Légales et Contentieux",
        "sous_categorie": "Contentieux avec Organismes Publics",
    },
    {
        "nom": "Procédure de recouvrement",
        "code_interne": "DEBT_COLLECTION_PROCEDURE",
        "categorie": "Obligations Légales et Contentieux",
        "sous_categorie": "Actions en Recouvrement",
    },
    {
        "nom": "Changement de dirigeants",
        "code_interne": "EXECUTIVE_CHANGE",
        "categorie": "Dirigeants et Gouvernance",
        "sous_categorie": "Mouvements au sein de la Direction",
    },
    {
        "nom": "Commentaires sur dirigeants",
        "code_interne": "EXECUTIVE_REPUTATION",
        "categorie": "Dirigeants et Gouvernance",
        "sous_categorie": "Réputation des Dirigeants",
    },
    {
        "nom": "Nouveau contrat important",
        "code_interne": "NEW_MAJOR_CONTRACT",
        "categorie": "Activité Commerciale et Contrats",
        "sous_categorie": "Contrats et Partenariats",
    },
    {
        "nom": "Résiliation de contrat important",
        "code_interne": "CONTRACT_TERMINATION",
        "categorie": "Activité Commerciale et Contrats",
        "sous_categorie": "Contrats et Partenariats",
    },
    {
        "nom": "Nouveau produit ou service",
        "code_interne": "NEW_PRODUCT_SERVICE",
        "categorie": "Innovation et Développement",
        "sous_categorie": "Lancement de Produits",
    },
    {
        "nom": "Changement de stratégie commerciale",
        "code_interne": "COMMERCIAL_STRATEGY_CHANGE",
        "categorie": "Stratégie et Planification",
        "sous_categorie": "Stratégie Commerciale",
    },
    {
        "nom": "Nouveau partenariat stratégique",
        "code_interne": "NEW_STRATEGIC_PARTNERSHIP",
        "categorie": "Stratégie et Planification",
        "sous_categorie": "Partenariats et Alliances",
    },
    {
        "nom": "Changement de politique de prix",
        "code_interne": "PRICING_POLICY_CHANGE",
        "categorie": "Stratégie et Planification",
        "sous_categorie": "Politique de Prix",
    },
    {
        "nom": "Nouvelle réglementation applicable",
        "code_interne": "NEW_REGULATION",
        "categorie": "Conformité et Réglementation",
        "sous_categorie": "Conformité Légale",
    },
    {
        "nom": "Alerte sur non-conformité",
        "code_interne": "NON_COMPLIANCE_ALERT",
        "categorie": "Conformité et Réglementation",
        "sous_categorie": "Conformité Légale",
    },
    {
        "nom": "Nouvelle certification obtenue",
        "code_interne": "NEW_CERTIFICATION",
        "categorie": "Qualité et Certifications",
        "sous_categorie": "Certifications et Normes",
    },
    {
        "nom": "Perte de certification",
        "code_interne": "CERTIFICATION_LOSS",
        "categorie": "Qualité et Certifications",
        "sous_categorie": "Certifications et Normes",
    },
    {
        "nom": "Nouvelle embauche clé",
        "code_interne": "KEY_HIRE",
        "categorie": "Ressources Humaines",
        "sous_categorie": "Recrutement et Départs",
    },
    {
        "nom": "Départ d'un employé clé",
        "code_interne": "KEY_EMPLOYEE_DEPARTURE",
        "categorie": "Ressources Humaines",
        "sous_categorie": "Recrutement et Départs",
    },
]

    
    
def dash_root_profile_page(request):
    """
    Vue front-end pour afficher et gérer le profil utilisateur.
    """
    # Vérifier si l'utilisateur est authentifié
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    
    user = request.user
    
    # Génération des tokens d'accès avec gestion d'erreur
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        # Log l'erreur mais ne pas bloquer l'accès
        print(f"Erreur génération token: {e}")
        access_token = ""
        refresh_token = ""
    
    context = {
        "account_active": "active",
        "user": user,
        "refresh": refresh_token,
        "access": access_token,
    }
    return render(request, "main/root/profile/user_profile.html", context)
    



# Create your views here.


# === Vues Pages Statiques === #


def index(request):

    context = {
        "index_active": "active",
    }
    return render(request, "main/vitrine/index.html", context)

def connexion(request):

    context = {
        "index_active": "active",
    }
    return render(request, "main/vitrine/connexion.html", context)

def registration(request):

    context = {
        "index_active": "active",
    }
    return render(request, "main/vitrine/registration.html", context)

def forgot_password(request):

    context = {
        "index_active": "active",
    }
    return render(request, "main/vitrine/forgot_password.html", context)


def reset_password(request):

    context = {
        "index_active": "active",
    }
    return render(request, "main/vitrine/reset_password.html", context)


def solutions(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/solutions.html", context)


def solvency_report(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/solvency_report.html", context)


def solvency_report_model(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/solvency_report_model.html", context)


def abonnement_saas(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/abonnement_saas.html", context)


def licence_autonome(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/licence_autonome.html", context)


def access_api_bucrep(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/access_api_bucrep.html", context)


def comment_ca_marche(request):

    context = {
        "comment_ca_marche_active": "active",
    }
    return render(request, "main/vitrine/comment_ca_marche.html", context)


def tarifs(request):

    context = {
        "tarifs_active": "active",
    }
    return render(request, "main/vitrine/tarifs.html", context)


def support(request):

    context = {
        "supports_active": "active",
    }
    return render(request, "main/vitrine/support.html", context)


def support_doc_bucrep(request):

    context = {
        "supports_active": "active",
    }
    return render(request, "main/vitrine/support_doc_bucrep.html", context)


def support_doc_demand_report(request):

    context = {
        "supports_active": "active",
    }
    return render(request, "main/vitrine/support_doc_demand_report.html", context)


def support_doc_licence_autonome(request):

    context = {
        "supports_active": "active",
    }
    return render(request, "main/vitrine/support_doc_licence_autonome.html", context)


def support_doc_licence_autonome_details(request):

    context = {
        "supports_active": "active",
    }
    return render(request, "main/vitrine/support_doc_licence_autonome_details.html", context)


def orders_report(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/orders_report.html", context)


def ask_demo(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/ask_demo.html", context)


def contact_commercial_team(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/contact_commercial_team_two.html", context)


def discuss_with_expert(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/discuss_with_expert.html", context)


def free_trial(request):
    aujourd_hui = datetime.today()
    date_plus_30 = aujourd_hui + timedelta(days=30)

    context = {
        "solutions_active": "active",
        "date_plus_30": date_plus_30
    }
    return render(request, "main/vitrine/free_trial.html", context)


def report_payment(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/report_payment.html", context)


def abonnement_payment(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/abonnement_payment.html", context)


def confirm_order(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/confirm_order.html", context)


def documentation_api(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/documentation_api.html", context)


def key_api(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/key_api.html", context)


def key_api_free(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/key_api_free.html", context)


def key_api_devis(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/key_api_devis.html", context)


def key_api(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/key_api.html", context)


def policy_confidentiality(request):
    aujourd_hui = datetime.today()
    date_plus_30 = aujourd_hui + timedelta(days=30)

    context = {
        "solutions_active": "active",
        "date_plus_30": date_plus_30,
        "aujourd_hui": aujourd_hui
    }
    return render(request, "main/vitrine/policy_confidentiality.html", context)


def legal_mention(request):
    aujourd_hui = datetime.today()
    date_plus_30 = aujourd_hui + timedelta(days=30)

    context = {
        "solutions_active": "active",
        "date_plus_30": date_plus_30,
        "aujourd_hui": aujourd_hui
    }
    return render(request, "main/vitrine/legal_mention.html", context)


def terms_of_use(request):
    aujourd_hui = datetime.today()
    date_plus_30 = aujourd_hui + timedelta(days=30)

    context = {
        "solutions_active": "active",
        "date_plus_30": date_plus_30,
        "aujourd_hui": aujourd_hui
    }
    return render(request, "main/vitrine/terms_of_use.html", context)


def gestion_cookie(request):

    context = {
        "solutions_active": "active",
    }
    return render(request, "main/vitrine/gestion_cookie.html", context)


def blog(request):

    context = {
        "index_active": "active",
    }
    return render(request, "main/vitrine/blog.html", context)


def blog_article(request):

    context = {
        "index_active": "active",
    }
    return render(request, "main/vitrine/blog_article.html", context)


def webinaires(request):

    context = {
        "index_active": "active",
    }
    return render(request, "main/vitrine/webinaires.html", context)


def webinaires_masterclass(request):

    context = {
        "index_active": "active",
    }
    return render(request, "main/vitrine/webinaires_masterclass.html", context)




def login(request):

    context = {
        "index_active": "active",
    }
    return render(request, "main/vitrine/login.html", context)


def check_auth(request):

    context = {
        "index_active": "active",
    }
    return render(request, "main/vitrine/check_auth.html", context)


def forgot_auth(request):

    context = {
        "index_active": "active",
    }
    return render(request, "main/vitrine/forgot_auth.html", context)


def reset_auth(request):

    context = {
        "index_active": "active",
    }
    return render(request, "main/vitrine/reset_auth.html", context)


def report(request):
    return render(request, "main/vitrine/report_template.html")



def new_admin():
    username = "admin"
    email = "yannickabohthierry@gmail.com"
    role = "Root"

    try:
        user, created = User.objects.get_or_create(username=username)

        user.email = email
        user.role = role
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.activation = True
        user.auth_a2f = False

        # 🛡️ Définit le mot de passe de manière sécurisée
        # user.set_password(raw_password)
        user.save()

        if created:
            return HttpResponse("✅ Superutilisateur créé avec succès.", status=201)
        else:
            return HttpResponse("ℹ️ Superutilisateur existant mis à jour avec succès.", status=200)

    except Exception as e:
        return HttpResponse(f"❌ Erreur lors de la création ou mise à jour : {str(e)}", status=500)



JSON_LIST_ADMIN = {
  "emails": [
    "abdrahmane.kone@acremac.com",
    "abdrahmane.kone@acremac.com",
    "abdrahmane.kone@acremac.com",
    "abdrahmane.kone@acremac.com",
  ]
}



def new_admins_from_list(request):
    # Cette vue devrait être protégée, par exemple, par @staff_member_required
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            emails = data.get('emails', [])
            root_role = "Root"

            if not emails or not isinstance(emails, list):
                return JsonResponse({"error": "La requête doit contenir une liste d'emails."}, status=400)

            created_count = 0
            updated_count = 0

            with transaction.atomic():
                for email in emails:
                    username = email.split('@')[0]
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': email,
                            'role': root_role,
                            'is_staff': True,
                            'is_superuser': True,
                            'is_active': True,
                            'activation': True,
                            'auth_a2f': False,
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        # Si l'utilisateur existe, on met à jour les champs
                        user.email = email
                        user.role = root_role
                        user.is_staff = True
                        user.is_superuser = True
                        user.is_active = True
                        user.activation = True
                        user.auth_a2f = False
                        user.save()
                        updated_count += 1

            return JsonResponse({
                "message": "Opération terminée.",
                "created": created_count,
                "updated": updated_count,
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Format JSON invalide."}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Erreur interne : {str(e)}"}, status=500)

    return JsonResponse({"message": "Cette vue accepte uniquement les requêtes POST."}, status=405)










def report_modele(request):
    return render(request, "main/report_model.html")


# === VIEWS Dashboards === #


########################################################################################################################
#                                                                                                                      #
#  VIEWS START FOR ROOT                                                                                                #
#                                                                                                                      #
########################################################################################################################
from django.contrib.auth import get_user_model
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Ensure User is correctly imported or defined
User = get_user_model()


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.tokens import RefreshToken


@login_required
def dash_root(request):
    # Vérifier si l'utilisateur est authentifié
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    
    user = request.user

    # Génération des tokens d'accès
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')
    
    selected_pays_id = _resolve_pays_id(request)

    # Recuperer les donnees filtrées par pays si disponible
    commandes = Commande.objects.all()
    acheteurs = Acheteur.objects.all()
    alertes = Warning.objects.all()
    if selected_pays_id:
        commandes = commandes.filter(pays_id=selected_pays_id)
        acheteurs = acheteurs.filter(pays_id=selected_pays_id)
        alertes = alertes.filter(acheteurs__pays_id=selected_pays_id).distinct()

    # Données carte : pays actifs avec comptage d'acheteurs
    pays_map_qs = (
        Pays.objects
        .filter(afficher_au_dashboard=True, is_active=True)
        .annotate(nb_acheteurs=Count('acheteur'))
        .values('id', 'nom', 'code', 'nb_acheteurs')
    )
    pays_map_data = json.dumps([
        {
            'id': p['id'],
            'nom': p['nom'],
            'code': p['code'],
            'nb_acheteurs': p['nb_acheteurs'],
        }
        for p in pays_map_qs
    ])

    # Totaux pour les statistiques de la carte
    total_pays = Pays.objects.filter(is_active=True).count()
    actifs_count = pays_map_qs.count()
    inactifs_count = max(0, total_pays - actifs_count)

    context = {
        "dash_active": "active",
        "user": user,
        "refresh": refresh_token,
        "access": access_token,
        "access_token": access_token,
        "commandes": commandes,
        "acheteurs": acheteurs,
        "alertes": alertes,
        "current_date": timezone.now().date(),
        "current_time": timezone.now().time(),
        "pays_map_data": pays_map_data,
        "total_pays": total_pays,
        "actifs_count": actifs_count,
        "inactifs_count": inactifs_count,
    }

    return render(
        request,
        "main/root/dash_root.html",
        context
    )




@login_required
def dash_root_user(request):
    # Vérifier si l'utilisateur a les permissions nécessaires
    # Vérifier si l'utilisateur est authentifié
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    
    user = request.user

    # Génération des tokens d'accès
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')

    pays_list = Pays.objects.all().only('id', 'nom')
    groups_list = Group.objects.all().only('id', 'name').order_by('name')

    context = {
        "users_active": "active",
        "pays_list": pays_list,
        "groups_list": groups_list,
        "user": request.user,
        "refresh": refresh_token,
        "access": access_token,
    }
    return render(
        request,
        "main/root/utilisateur/dash_root_user.html",
        context
    )





@never_cache
@login_required
def dash_root_order(request):
    # Vérifier si l'utilisateur a les permissions nécessaires
    # Vérifier si l'utilisateur est authentifié
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    
    user = request.user

    # Génération des tokens d'accès
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')

    selected_pays_id = _resolve_pays_id(request)
    ville_queryset = Ville.objects.all()
    acheteur_queryset = Acheteur.objects.all()
    if selected_pays_id:
        ville_queryset = ville_queryset.filter(pays_id=selected_pays_id)
        acheteur_queryset = acheteur_queryset.filter(pays_id=selected_pays_id)

    context = {
        "requests_active": "active",
        "orders_active": "active",
        "user": request.user,
        "refresh": refresh_token,
        "access": access_token,
        "devise_list": Devise.objects.all(),
        "acheteur_list": acheteur_queryset,
        "client_list": User.objects.filter(role="Client", is_active=True).order_by("username"),
        "validateur_list": User.objects.filter(is_active=True).exclude(role="Client").order_by("username"),
        "pays_list": Pays.objects.all(),
        "ville_list": ville_queryset,
        "selected_pays_id": selected_pays_id,
        "modele_rapport_list": ModeleRapport.objects.all(),
        "status_choices": Commande.STATUS_CHOICES,
        "type_rapport_choices": [
            choice for choice in Commande._meta.get_field("type_rapport").choices if choice[0] != "--------"
        ],
    }
    return render(
        request,
        "main/root/orders/dash_root_order.html",
        context
    )


@never_cache
@login_required
def dash_root_order_create(request):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    user = request.user
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')

    selected_pays_id = _resolve_pays_id(request)
    ville_queryset = Ville.objects.all()
    acheteur_queryset = Acheteur.objects.all()
    if selected_pays_id:
        ville_queryset = ville_queryset.filter(pays_id=selected_pays_id)
        acheteur_queryset = acheteur_queryset.filter(pays_id=selected_pays_id)

    context = {
        "requests_active": "active",
        "orders_active": "active",
        "user": user,
        "refresh": refresh_token,
        "access": access_token,
        "devise_list": Devise.objects.all(),
        "acheteur_list": acheteur_queryset,
        "client_list": User.objects.filter(role="Client", is_active=True).order_by("username"),
        "validateur_list": User.objects.filter(is_active=True).exclude(role="Client").order_by("username"),
        "ville_list": ville_queryset,
        "status_choices": Commande.STATUS_CHOICES,
        "type_rapport_choices": [
            choice for choice in Commande._meta.get_field("type_rapport").choices if choice[0] != "--------"
        ],
    }
    return render(request, "main/root/orders/dash_root_order_create.html", context)


@login_required
def dash_root_order_edit(request, order_id):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    user = request.user
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')

    selected_pays_id = _resolve_pays_id(request)
    ville_queryset = Ville.objects.all()
    acheteur_queryset = Acheteur.objects.all()
    if selected_pays_id:
        ville_queryset = ville_queryset.filter(pays_id=selected_pays_id)
        acheteur_queryset = acheteur_queryset.filter(pays_id=selected_pays_id)

    context = {
        "requests_active": "active",
        "orders_active": "active",
        "user": user,
        "refresh": refresh_token,
        "access": access_token,
        "order_id": order_id,
        "devise_list": Devise.objects.all(),
        "acheteur_list": acheteur_queryset,
        "client_list": User.objects.filter(role="Client", is_active=True).order_by("username"),
        "validateur_list": User.objects.filter(is_active=True).exclude(role="Client").order_by("username"),
        "ville_list": ville_queryset,
        "status_choices": Commande.STATUS_CHOICES,
        "type_rapport_choices": [
            choice for choice in Commande._meta.get_field("type_rapport").choices if choice[0] != "--------"
        ],
    }
    return render(request, "main/root/orders/dash_root_order_edit.html", context)


@login_required
def dash_root_pays(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "locations_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/root/pays/dash_root_pays.html", context)


@login_required
def dash_root_province(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    context = {
        "locations_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "pays_list": pays_list,  # Ajouter la liste des pays au contexte
    }
    return render(request, "main/root/province/dash_root_province.html", context)


@login_required
def dash_root_ville(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    # pays_list = Pays.objects.all()

    # Récupérer tous les pays
    province_list = Province.objects.all()

    context = {
        "locations_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        # 'pays_list': pays_list,  # Ajouter la liste des pays au contexte
        "province_list": province_list,  # Ajouter la liste des pays au contexte
    }
    return render(request, "main/root/ville/dash_root_ville.html", context)


@login_required
def dash_root_devise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    # Récupérer tous les pays
    province_list = Province.objects.all()

    context = {
        "codification_active": "active",
        "devise_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "pays_list": pays_list,  # Ajouter la liste des pays au contexte
        "province_list": province_list,  # Ajouter la liste des pays au contexte
    }
    return render(request, "main/root/devise/dash_root_devise.html", context)


@login_required
def dash_root_annee(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    Pays.objects.all()

    # Récupérer tous les pays
    Province.objects.all()

    context = {
        "codification_active": "active",
        "annee_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/root/annee/dash_root_annee.html", context)


@login_required
def dash_root_coloration(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "coloration_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/root/coloration/dash_root_coloration.html", context)


@login_required
def dash_root_category_nace(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "nace_cat_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/root/nace/dash_root_category_nace.html", context)


@login_required
def dash_root_category_naf(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "naf_cat_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/root/naf/dash_root_category_naf.html", context)


@login_required
def dash_root_code_nace(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les categories nace
    categorie_list = CategoryNaceCode.objects.all()

    context = {
        "codification_active": "active",
        "nace_code_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "categorie_list": categorie_list,
    }
    return render(request, "main/root/nace/dash_root_code_nace.html", context)


@login_required
def dash_root_code_naf(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les categories nace
    categorie_list = CategoryNafCode.objects.all()

    context = {
        "codification_active": "active",
        "naf_code_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "categorie_list": categorie_list,
    }
    return render(request, "main/root/naf/dash_root_code_naf.html", context)


@login_required
def dash_root_forme_juridique(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "juridique_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/root/juridique/dash_root_forme_juridique.html", context
    )


@login_required
def dash_root_domaine(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "domaine_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/root/domaine/dash_root_domaine.html", context)


@login_required
def dash_root_modele_bail(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_bail_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/root/modele/dash_root_modele_bail.html", context)


@login_required
def dash_root_modele_bilan(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_bilan_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/root/modele/dash_root_modele_bilan.html", context)


@login_required
def dash_root_modele_alarme(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_alarme_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/root/modele/dash_root_modele_alarme.html", context)


@login_required
def dash_root_modele_rapport(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_rapport_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/root/modele/dash_root_modele_rapport.html", context)


@login_required
def dash_root_modele_avis_commercial(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_avis_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/root/modele/dash_root_modele_avis_commercial.html", context
    )


@login_required
def dash_root_modele_relation_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_relation_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/root/modele/dash_root_modele_relation_entreprise.html", context
    )


@login_required
def dash_root_modele_notation(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_notation_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/root/modele/dash_root_modele_notation.html", context)


@login_required
def dash_root_modele_comportement_paiement(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_cpaiement_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/root/modele/dash_root_modele_comportement_paiement.html", context
    )


@login_required
def dash_root_modele_comportement_jugement(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_cjugement_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/root/modele/dash_root_modele_comportement_jugement.html", context
    )


@login_required
def dash_root_modele_information_notation_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_infone_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request,
        "main/root/modele/dash_root_modele_information_notation_entreprise.html",
        context,
    )


@login_required
def dash_root_poste(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupération des domaines
    domaines = DomaineEntreprise.objects.all()

    context = {
        "codification_active": "active",
        "poste_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "domaines": domaines,  # Ajouter les domaines au contexte
    }
    return render(request, "main/root/poste/dash_root_poste.html", context)


@login_required
def dash_root_category_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "entreprise_cat_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/root/entreprise/dash_root_category_entreprise.html", context
    )


@login_required
def dash_root_structure_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "entreprise_structure_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/root/structure/dash_root_structure_entreprise.html", context
    )


@login_required
def dash_root_statut_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "entreprise_statut_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/root/statut/dash_root_statut_entreprise.html", context)


@login_required
def dash_root_acheteur(request):
    # Vérifier les permissions
    # Vérifier si l'utilisateur est authentifié
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    
    user = request.user
    
    # Récupérer le pays sélectionné (session -> profil -> premier pays dashboard)
    selected_pays_id = _resolve_pays_id(request)

    # Le listing est chargé côté API (pagination server-side), on évite de charger toute la table ici.
    acheteurs = Acheteur.objects.none()
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access": access_token,
        "refresh": refresh_token,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteurs": acheteurs,
        "selected_pays_id": selected_pays_id,
    }

    return render(
        request,
        "main/root/acheteur/dash_root_acheteur.html",
        context
    )


_RE_PAREN_SUFFIX = re.compile(r'\s*\([^)]*\)\s*$')


def _fj_to_english(code, libelle):
    """Translate a FormeJuridique to English. Returns original libelle if unknown."""
    # 1. Exact code match
    code = (code or '').strip()
    if code:
        en = FORME_JURIDIQUE_EN.get(code)
        if en:
            return en
    # 2. Exact libelle match
    lib = (libelle or '').strip()
    en = FORME_JURIDIQUE_LIBELLE_EN.get(lib)
    if en:
        return en
    # 3. Libelle without trailing parenthetical suffix, e.g. "Société anonyme (SA)" → "Société anonyme"
    lib_stripped = _RE_PAREN_SUFFIX.sub('', lib).strip()
    if lib_stripped and lib_stripped != lib:
        en = FORME_JURIDIQUE_LIBELLE_EN.get(lib_stripped)
        if en:
            return en
    # 4. Libelle match ignoring case
    lib_lower = lib.lower()
    for key, val in FORME_JURIDIQUE_LIBELLE_EN.items():
        if key.lower() == lib_lower:
            return val
    # Not found — keep original
    return libelle


def _translate_juridique_list(request):
    """Return FormeJuridique list with libelle translated to the active language."""
    lang = getattr(request, 'LANGUAGE_CODE', '') or ''
    qs = FormeJuridique.objects.all().order_by('libelle')
    if lang.startswith('en'):
        return [{'id': j.id, 'libelle': _fj_to_english(j.code, j.libelle)} for j in qs]
    return [{'id': j.id, 'libelle': j.libelle} for j in qs]


def _se_to_english(code, libelle):
    """Translate a StatutEntreprise to English. Returns original libelle if unknown."""
    code = (code or '').strip()
    if code:
        en = STATUT_ENTREPRISE_EN.get(code)
        if en:
            return en
    lib = (libelle or '').strip()
    en = STATUT_ENTREPRISE_LIBELLE_EN.get(lib)
    if en:
        return en
    lib_lower = lib.lower()
    for key, val in STATUT_ENTREPRISE_LIBELLE_EN.items():
        if key.lower() == lib_lower:
            return val
    return libelle


def _translate_statut_list(request):
    """Return StatutEntreprise list with libelle translated to the active language."""
    lang = getattr(request, 'LANGUAGE_CODE', '') or ''
    qs = StatutEntreprise.objects.all().order_by('libelle')
    if lang.startswith('en'):
        return [{'id': s.id, 'libelle': _se_to_english(s.code, s.libelle)} for s in qs]
    return [{'id': s.id, 'libelle': s.libelle} for s in qs]


@login_required
def dash_root_add_acheteur(request):
    user = request.user

    # Génération des tokens d'accès
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')

    # Activation des données de référence
    StatutEntreprise.objects.update(active=True)
    CategorieEntreprise.objects.update(active=True)
    FormeJuridique.objects.update(active=True)
    
    # Récupération des données de référence
    juridique_list = _translate_juridique_list(request)
    statut_list = _translate_statut_list(request)

    coloration_list = CouleurCommentaire.objects.all()
    pays_list = Pays.objects.all()
    province_list = Province.objects.all()
    ville_list = Ville.objects.all()

    selected_pays_id = _resolve_pays_id(request)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": refresh_token,
        "access": access_token,
        "juridique_list": juridique_list,
        "statut_list": statut_list,
        "coloration_list": coloration_list,
        "pays_list": pays_list,
        "province_list": province_list,
        "ville_list": ville_list,
        "selected_pays_id": selected_pays_id,
        "selected_pays_nom": Pays.objects.filter(pk=selected_pays_id).values_list("nom", flat=True).first() if selected_pays_id else "",
    }

    return render(
        request,
        "main/root/acheteur/dash_root_add_acheteur.html",
        context
    )


@login_required
def dash_root_edit_acheteur(request, acheteur_id):
    user = request.user

    # Génération des tokens d'accès
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')

    # Activation des données de référence
    StatutEntreprise.objects.update(active=True)
    CategorieEntreprise.objects.update(active=True)
    FormeJuridique.objects.update(active=True)
    
    # Récupération des données de référence
    juridique_list = _translate_juridique_list(request)
    statut_list = _translate_statut_list(request)

    coloration_list = CouleurCommentaire.objects.all()
    pays_list = Pays.objects.all()
    province_list = Province.objects.all()
    ville_list = Ville.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": refresh_token,
        "access": access_token,
        "id_acheteur": acheteur_id,
        "juridique_list": juridique_list,
        "statut_list": statut_list,
        "coloration_list": coloration_list,
        "pays_list": pays_list,
        "province_list": province_list,
        "ville_list": ville_list,
    }

    return render(
        request,
        "main/root/acheteur/dash_root_edit_acheteur.html",
        context
    )



@login_required
def dash_root_manage_acheteur(request, acheteur_id):
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )
    
    # Vérifier si l'utilisateur a les permissions nécessaires
    # Vérifier si l'utilisateur est authentifié
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    
    user = request.user

    # Génération des tokens d'accès
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les categories d'entreprise
    categorie_list = CategorieEntreprise.objects.all()

    # Récupérer tous les formes juridiques (traduites selon la langue active)
    juridique_list = _translate_juridique_list(request)

    # Récupérer tous les statuts entreprise
    statut_list = _translate_statut_list(request)

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    # Récupérer tous les provinces
    province_list = Province.objects.all()

    # Récupérer tous les villes
    ville_list = Ville.objects.all()

    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'forme_juridique': acheteur.forme_juridique.libelle if acheteur.forme_juridique else 'Non spécifié',
        'description': acheteur.description or 'Aucune description disponible',
        'email': acheteur.email or 'Non spécifié',
        'fax': acheteur.fax or 'Non spécifié',
        'boite_postale': acheteur.boite_postale or 'Non spécifié',
        'site_internet': acheteur.site_internet or 'Non spécifié',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'ville': acheteur.ville.nom if acheteur.ville else 'Non spécifié',
        'province': acheteur.province.nom if acheteur.province else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": refresh_token,
        "access": access_token,
        "id_acheteur": id_acheteur,
        "acheteur_json": acheteur_json,  # JSON pour JavaScript
        "acheteur": acheteur,  # Objet pour le template si besoin
        "categorie_list": categorie_list,
        "juridique_list": juridique_list,
        "statut_list": statut_list,
        "coloration_list": coloration_list,
        "pays_list": pays_list,
        "province_list": province_list,
        "ville_list": ville_list,
    }
    return render(request, "main/root/acheteur/dash_root_manage_acheteur.html", context)




from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from rest_framework_simplejwt.tokens import RefreshToken
from main.models import Acheteur, Devise, CouleurCommentaire
import json
import logging

logger = logging.getLogger(__name__)

@login_required
def dash_root_manage_acheteur_resume(request, acheteur_id):
    """
    Vue pour la gestion des résumés financiers d'un acheteur
    Un acheteur ne peut avoir qu'un seul résumé
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )
    
    # ⭐⭐ AJOUTEZ CETTE LIGNE : Récupérer le résumé existant ⭐⭐
    resume = Resume.objects.filter(acheteur=acheteur).first()
    
    # Vérifier les permissions
    # Vérifier si l'utilisateur a les permissions nécessaires
    # Vérifier si l'utilisateur est authentifié
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Récupération des données avec les champs corrects
    devise_list = Devise.objects.all().values('id', 'nom', 'code', 'symbole')
    
    # CORRECTION ICI : Retirer 'description' qui n'existe pas
    coloration_list = CouleurCommentaire.objects.all().values('id', 'couleur', 'code')
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'forme_juridique': acheteur.forme_juridique.libelle if acheteur.forme_juridique else 'Non spécifié',
        'description': acheteur.description or 'Aucune description disponible',
        'email': acheteur.email or 'Non spécifié',
        'fax': acheteur.fax or 'Non spécifié',
        'boite_postale': acheteur.boite_postale or 'Non spécifié',
        'site_internet': acheteur.site_internet or 'Non spécifié',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'ville': acheteur.ville.nom if acheteur.ville else 'Non spécifié',
        'province': acheteur.province.nom if acheteur.province else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,  # JSON pour JavaScript
        "acheteur": acheteur,  # Objet pour le template si besoin
        "resume": resume,  # ⭐⭐ AJOUTEZ CECI AU CONTEXTE ⭐⭐
        "id_acheteur": acheteur_id,
        "devise_list": list(devise_list),
        "coloration_list": list(coloration_list),
        "bons_postes_list": BON_POST_CHOICES_CHOICES,
    }
    
    return render(
        request,
        "main/root/acheteur/resume/dash_root_manage_acheteur_resume.html",
        context,
    )




@login_required
def dash_root_manage_acheteur_risk_rating(request, acheteur_id):
    """
    Vue pour la gestion des résumés financiers d'un acheteur
    Un acheteur ne peut avoir qu'un seul résumé
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer l'acheteur
    acheteur = get_object_or_404(Acheteur, id=acheteur_id)
    
    # ⭐ AJOUTER : Récupérer l'évaluation de risque existante ⭐
    risk_rating = RiskRating.objects.filter(acheteur=acheteur).first()
    
    # Vérifier les permissions
    # Vérifier si l'utilisateur a les permissions nécessaires
    # Vérifier si l'utilisateur est authentifié
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'forme_juridique': acheteur.forme_juridique.libelle if acheteur.forme_juridique else 'Non spécifié',
        'description': acheteur.description or 'Aucune description disponible',
        'email': acheteur.email or 'Non spécifié',
        'fax': acheteur.fax or 'Non spécifié',
        'boite_postale': acheteur.boite_postale or 'Non spécifié',
        'site_internet': acheteur.site_internet or 'Non spécifié',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'ville': acheteur.ville.nom if acheteur.ville else 'Non spécifié',
        'province': acheteur.province.nom if acheteur.province else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,  # JSON pour JavaScript
        "acheteur": acheteur,  # ⭐ AJOUTER
        "risk_rating": risk_rating,  # ⭐ AJOUTER
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/riskrating/dash_root_manage_acheteur_risk_rating.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_scoring(request, acheteur_id):
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )
    
    # Recupere l'user connecte
    user = request.user

    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'forme_juridique': acheteur.forme_juridique.libelle if acheteur.forme_juridique else 'Non spécifié',
        'description': acheteur.description or 'Aucune description disponible',
        'email': acheteur.email or 'Non spécifié',
        'fax': acheteur.fax or 'Non spécifié',
        'boite_postale': acheteur.boite_postale or 'Non spécifié',
        'site_internet': acheteur.site_internet or 'Non spécifié',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'ville': acheteur.ville.nom if acheteur.ville else 'Non spécifié',
        'province': acheteur.province.nom if acheteur.province else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur_json": acheteur_json,  # JSON pour JavaScript
        "acheteur": acheteur,  # Objet pour le template si besoin
        "id_acheteur": acheteur_id,
    }
    
    return render(
        request,
        "main/root/acheteur/scoring/dash_root_manage_acheteur_scoring.html",
        context,
    )
    
    
# views.py - Ajoutez cette vue
@login_required
def dash_root_manage_acheteur_scoring_manuel(request, acheteur_id):
    """
    Vue pour la gestion du scoring manuel
    Si acheteur_id est fourni, on filtre par acheteur
    """
    try:
        # Récupérer l'acheteur avec préfetch pour optimiser
        acheteur = get_object_or_404(
            Acheteur.objects.select_related(
                'statut_entreprise',
                'forme_juridique',
                'pays',
                'province',
                'ville'
            ),
            id=acheteur_id
        )
        
        # Supprimez TOUS les scorings pour l'acheteur 2
        # scorings = Scoring.objects.filter(acheteur_id=acheteur_id)
        # print(f"Suppression de {scorings.count()} scorings")
        # deleted_count, _ = scorings.delete()
        # print(f"{deleted_count} scorings supprimés")

        # Vérifiez que c'est vide
        # remaining = Scoring.objects.filter(acheteur_id=acheteur_id).count()
        # print(f"Scorings restants: {remaining}")
        
        # Dans votre vue dash_root_manage_acheteur_scoring_manuel
        # Au lieu de :s
        # scorings = Scoring.objects.filter(acheteur_id=acheteur_id)
        # print(f"Suppression de {scorings.count()} scorings")

        # Essayez avec ALL pour voir même les soft-deletes :
        # from safedelete.models import DELETED_INVISIBLE
        # from safedelete.managers import SafeDeleteManager

        # Pour voir TOUS les scorings (y compris soft-deleted)
        # all_scorings = Scoring.objects.all(force_visibility=SafeDeleteManager.DELETED_VISIBLE)
        # print(f"Total scorings (y compris soft-deleted): {all_scorings.filter(acheteur_id=acheteur_id).count()}")

        # Pour vraiment supprimer (hard delete) :
        # Scoring.objects.filter(acheteur_id=acheteur_id).delete()
        
        # Préparer les données pour l'encart acheteur
        acheteur_context = {
            'id': acheteur.id,
            'nom': acheteur.nom or 'Non spécifié',
            'sigle': acheteur.sigle or '',
            'code': acheteur.code or 'N/A',
            'activite_principale': acheteur.activite_principale or 'Non spécifié',
            'date_creation': acheteur.date_creation.strftime('%d/%m/%Y') if acheteur.date_creation else None,
            'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
            'forme_juridique': acheteur.forme_juridique.libelle if acheteur.forme_juridique else 'Non spécifié',
            'description': acheteur.description or 'Aucune description disponible',
            'email': acheteur.email or 'Non spécifié',
            'fax': acheteur.fax or 'Non spécifié',
            'boite_postale': acheteur.boite_postale or 'Non spécifié',
            'site_internet': acheteur.site_internet or 'Non spécifié',
            'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
            'ville': acheteur.ville.nom if acheteur.ville else 'Non spécifié',
            'province': acheteur.province.nom if acheteur.province else 'Non spécifié',
        }
        
        # Convertir en JSON sécurisé pour JavaScript
        acheteur_json = json.dumps(acheteur_context, default=str)
        
        # Génération des tokens JWT
        try:
            refresh = RefreshToken.for_user(request.user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
        except Exception as e:
            logger.error(f"Erreur lors de la génération des tokens: {e}")
            messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
            return redirect_to_login(request.get_full_path())
        
        # Récupérer les années actives pour le formulaire
        annee_list = Annee.objects.filter(is_active=True).order_by('-annee')
        
        # Préparer les données des années pour le template
        annee_data = [{'id': a.id, 'annee': a.annee} for a in annee_list]
        
        context = {
            "acheteur_active": "active",
            "user": request.user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "acheteur_json": acheteur_json,  # JSON pour JavaScript
            "acheteur": acheteur,  # Objet pour le template
            "annee_list": annee_data,  # Liste pour le select
            "id_acheteur": acheteur_id,
        }
        
        return render(
            request,
            "main/root/acheteur/scoring/dash_root_manage_acheteur_scoring_manuel.html",
            context,
        )
        
    except Exception as e:
        logger.error(f"Erreur dans la vue scoring manuel: {e}")
        messages.error(request, f"Une erreur est survenue: {str(e)}")
        return redirect('dashboard')
    
    

@login_required
def dash_root_manage_acheteur_scoring_with_bilan(request, acheteur_id):
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )
    
    # Recupere l'user connecte
    user = request.user

    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'forme_juridique': acheteur.forme_juridique.libelle if acheteur.forme_juridique else 'Non spécifié',
        'description': acheteur.description or 'Aucune description disponible',
        'email': acheteur.email or 'Non spécifié',
        'fax': acheteur.fax or 'Non spécifié',
        'boite_postale': acheteur.boite_postale or 'Non spécifié',
        'site_internet': acheteur.site_internet or 'Non spécifié',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'ville': acheteur.ville.nom if acheteur.ville else 'Non spécifié',
        'province': acheteur.province.nom if acheteur.province else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur_json": acheteur_json,  # JSON pour JavaScript
        "acheteur": acheteur,  # Objet pour le template si besoin
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/scoring/dash_root_manage_acheteur_scoring_with_bilan.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_data_save(request, acheteur_id):
    """
    Vue pour la gestion des résumés financiers d'un acheteur
    Un acheteur ne peut avoir qu'un seul résumé
    """
    
    # ⭐ CORRECTION : Supprimer la duplication
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )
    
    # Récupérer les données existantes
    data_save = DonneesEnregistrement.objects.filter(acheteur=acheteur).first()
    
    # Vérifier si l'utilisateur est authentifié
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'forme_juridique': acheteur.forme_juridique.libelle if acheteur.forme_juridique else 'Non spécifié',
        'description': acheteur.description or 'Aucune description disponible',
        'email': acheteur.email or 'Non spécifié',
        'fax': acheteur.fax or 'Non spécifié',
        'boite_postale': acheteur.boite_postale or 'Non spécifié',
        'site_internet': acheteur.site_internet or 'Non spécifié',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'ville': acheteur.ville.nom if acheteur.ville else 'Non spécifié',
        'province': acheteur.province.nom if acheteur.province else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # ⭐ AJOUT : Préparer les choix pour le template
    forme_juridique_choices = NOUVEAU_LEGAL_FORM
    statut_registre_choices = LIEN_STATUT_CHOICE
    
    # CORRECTION ICI : Retirer 'description' qui n'existe pas
    coloration_list = CouleurCommentaire.objects.all().values('id', 'couleur', 'code')

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "acheteur": acheteur,
        "data_save": data_save,
        "id_acheteur": acheteur_id,
        "forme_juridique_choices": forme_juridique_choices,
        "statut_registre_choices": statut_registre_choices,
        # ⭐ AJOUT : Conserver les listes existantes pour compatibilité
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/root/acheteur/data/dash_root_manage_acheteur_data_save.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_tendance(request, acheteur_id):
    """
    Vue pour la gestion de la tendance unique d'un acheteur
    Un acheteur ne peut avoir qu'une seule tendance
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer la tendance existante (une seule)
    tendance = Tendance.objects.filter(acheteur=acheteur).first()
    
    # Récupérer tous les avis commerciaux pour les listes déroulantes
    lang = get_language() or 'fr'
    _qs = ListeInformationsAvisCommercial.objects.all()
    if lang.startswith('en'):
        commercial_list = [
            {'id': a.id, 'libelle': a.libelle_en or a.libelle}
            for a in _qs
        ]
    else:
        commercial_list = _qs
    
    # ⭐ AJOUT : Préparer les choix pour le template
    plus_informations_choices = LIEN_PLUS_INFORMATIONS_NOTATION_CHOICE
    alarmes_choices = LIEN_ALARMES_CHOICE
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "acheteur": acheteur,
        "tendance": tendance,
        "id_acheteur": acheteur_id,
        "commercial_list": commercial_list,
        # ⭐ AJOUT : Ajouter les choix pour le template
        "plus_informations_choices": plus_informations_choices,
        "alarmes_choices": alarmes_choices,
    }
    return render(
        request,
        "main/root/acheteur/tendance/dash_root_manage_acheteur_tendance.html",
        context,
    )



@login_required
def dash_root_manage_acheteur_responsable(request, acheteur_id):
    """
    Vue pour la gestion des responsables d'un acheteur
    """
    try:
        # Récupérer l'acheteur avec relations optimisées
        acheteur = get_object_or_404(
            Acheteur.objects.select_related(
                'statut_entreprise',
                'forme_juridique'
            ),
            id=acheteur_id
        )

        # Récupérer les listes pour les formulaires
        coloration_list = CouleurCommentaire.objects.all().order_by('couleur')

        # Récupérer les responsables existants (limité à 5 pour les statistiques)
        responsables = ResponsableAcheteur.objects.filter(
            acheteur=acheteur
        ).select_related(
            'couleur_commentaire',
            'created_by',
            'updated_by'
        ).order_by('-created_at')[:5]


        # Statistiques
        stats = {
            'total': ResponsableAcheteur.objects.filter(acheteur=acheteur).count(),
            'masculin': ResponsableAcheteur.objects.filter(acheteur=acheteur, Sexe='Masculin').count(),
            'feminin': ResponsableAcheteur.objects.filter(acheteur=acheteur, Sexe='Feminin').count(),
            'avec_commentaire': ResponsableAcheteur.objects.filter(
                acheteur=acheteur,
                commentaire__isnull=False
            ).exclude(commentaire='').count(),
        }

        # Génération des tokens JWT
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Préparer les données pour JavaScript
        acheteur_data = {
            'id': acheteur.id,
            'nom': acheteur.nom or 'Non spécifié',
            'sigle': acheteur.sigle or '',
            'code': acheteur.code or 'N/A',
            'activite_principale': acheteur.activite_principale or 'Non spécifié',
            'date_creation': acheteur.date_creation.strftime('%d/%m/%Y') if acheteur.date_creation else 'Non spécifiée',
            'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        }
    
        # ⭐ AJOUT : Préparer les choix pour le template
        poste_choices = LISTE_NOUVELLE_FONCTION

        context = {
            "acheteur_active": "active",
            "user": request.user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "acheteur_json": json.dumps(acheteur_data),
            "id_acheteur": acheteur_id,
            "acheteur": acheteur,
            "coloration_list": coloration_list,
            "responsables_recent": responsables,
            "stats": stats,
            "poste_choices": poste_choices,
        }
        
        return render(
            request,
            "main/root/acheteur/responsable/dash_root_manage_acheteur_responsable.html",
            context,
        )
        
    except Exception as e:
        logger.error(f"Erreur dans dash_root_manage_acheteur_responsable: {e}")
        messages.error(request, "Une erreur est survenue lors du chargement des responsables.")
        return redirect('dash_root_manage_acheteur', acheteur_id=acheteur_id)




@login_required
def dash_root_manage_acheteur_antecedent(request, acheteur_id):
    """
    Vue pour la gestion des antécédents juridiques d'un acheteur
    """
    try:
        # Récupérer l'acheteur avec relations optimisées
        acheteur = get_object_or_404(
            Acheteur.objects.select_related(
                'statut_entreprise',
                'forme_juridique'
            ),
            id=acheteur_id
        )

        # Récupérer les listes pour les formulaires
        coloration_list = CouleurCommentaire.objects.all().order_by('couleur')

        # Récupérer les antécédents récents
        antecedents_recent = AntecedantsJuridique.objects.filter(
            acheteur=acheteur
        ).select_related('couleur_commentaire').order_by('-created_at')[:5]

        # Statistiques
        # views.py - Correction des stats
        stats = {
            'total': AntecedantsJuridique.objects.filter(acheteur=acheteur).count(),
            'avec_faillite': AntecedantsJuridique.objects.filter(
                acheteur=acheteur
            ).exclude(
                Q(dossier_faillite__isnull=True) | Q(dossier_faillite='')
            ).count(),
            'avec_jugement': AntecedantsJuridique.objects.filter(
                acheteur=acheteur
            ).exclude(
                Q(jugement_cour__isnull=True) | Q(jugement_cour='')
            ).count(),
            'avec_redressement': AntecedantsJuridique.objects.filter(
                acheteur=acheteur
            ).exclude(
                Q(antecedant_redressement__isnull=True) | Q(antecedant_redressement='')
            ).count(),
            'avec_commentaire': AntecedantsJuridique.objects.filter(
                acheteur=acheteur
            ).exclude(
                Q(commentaire__isnull=True) | Q(commentaire='')
            ).count(),
        }

        # Génération des tokens JWT
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Préparer les données pour JavaScript
        acheteur_data = {
            'id': acheteur.id,
            'nom': acheteur.nom or 'Non spécifié',
            'sigle': acheteur.sigle or '',
            'code': acheteur.code or 'N/A',
            'activite_principale': acheteur.activite_principale or 'Non spécifié',
            'date_creation': acheteur.date_creation.strftime('%d/%m/%Y') if acheteur.date_creation else 'Non spécifiée',
            'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        }

        context = {
            "acheteur_active": "active",
            "user": request.user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "acheteur_json": json.dumps(acheteur_data),
            "id_acheteur": acheteur_id,
            "acheteur": acheteur,
            "coloration_list": coloration_list,
            "antecedents_recent": antecedents_recent,
            "stats": stats,
        }
        
        return render(
            request,
            "main/root/acheteur/antecedent/dash_root_manage_acheteur_antecedent.html",
            context,
        )
        
    except Exception as e:
        logger.error(f"Erreur dans dash_root_manage_acheteur_antecedent: {e}")
        messages.error(request, "Une erreur est survenue lors du chargement des antécédents.")
        return redirect('dash_root_manage_acheteur', acheteur_id=acheteur_id)



# views/main/risk_views.py

@login_required
def dash_root_manage_acheteur_gestion_risque(request, acheteur_id):
    """
    Vue pour la gestion des risques unique d'un acheteur
    Un acheteur ne peut avoir qu'une seule gestion des risques
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer la gestion des risques existante (une seule)
    gestion_risque = RiskManagment.objects.filter(acheteur=acheteur).first()
    
    # Récupérer toutes les colorations pour les listes déroulantes
    coloration_list = CouleurCommentaire.objects.all()
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Si une gestion des risques existe, préparer ses données
    gestion_risque_json = None
    if gestion_risque:
        gestion_risque_data = {
            'id': gestion_risque.id,
            'professionalisme': gestion_risque.professionalisme or '',
            'organisation': gestion_risque.organisation or '',
            'turn_over': gestion_risque.turn_over or '',
            'greve': gestion_risque.greve or '',
            'degradation_qualite': gestion_risque.degradation_qualite or '',
            'non_respect_condition': gestion_risque.non_respect_condition or '',
            'couleur_commentaire': gestion_risque.couleur_commentaire.id if gestion_risque.couleur_commentaire else None,
            'commentaire': gestion_risque.commentaire or '',
        }
        gestion_risque_json = json.dumps(gestion_risque_data, default=str)
        
    # Configuration des champs pour le template
    fields = [
        {
            'id': 'professionalisme',
            'name': 'professionalisme',
            'label': 'Professionnalisme',
            'icon': 'fa-user-tie',
            'description': 'Évaluation du professionnalisme de l\'entreprise'
        },
        {
            'id': 'organisation',
            'name': 'organisation',
            'label': 'Organisation',
            'icon': 'fa-sitemap',
            'description': 'Évaluation de l\'organisation interne'
        },
        {
            'id': 'turn_over',
            'name': 'turn_over',
            'label': 'Non départ des employés',
            'icon': 'fa-user-friends',
            'description': 'Stabilité du personnel'
        },
        {
            'id': 'greve',
            'name': 'greve',
            'label': 'Non grève',
            'icon': 'fa-hand-paper',
            'description': 'Absence de mouvements sociaux'
        },
        {
            'id': 'degradation_qualite',
            'name': 'degradation_qualite',
            'label': 'Non dégradation de la qualité',
            'icon': 'fa-chart-line',
            'description': 'Maintien de la qualité du travail'
        },
        {
            'id': 'non_respect_condition',
            'name': 'non_respect_condition',
            'label': 'Respect des Employés',
            'icon': 'fa-handshake',
            'description': 'Respect des conditions de travail'
        }
    ]

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "gestion_risque_json": gestion_risque_json or 'null',
        "acheteur": acheteur,
        "gestion_risque": gestion_risque,
        "id_acheteur": acheteur_id,
        "coloration_list": coloration_list,
        "fields": fields,
    }
    return render(
        request,
        "main/root/acheteur/gestion/dash_root_manage_acheteur_gestion_risque.html",
        context,
    )




@login_required
def dash_root_manage_acheteur_report_solvency(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )
        
    # Préparer les données pour l'encart acheteur
    acheteur_context = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.strftime('%d/%m/%Y') if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'forme_juridique': acheteur.forme_juridique.libelle if acheteur.forme_juridique else 'Non spécifié',
        'description': acheteur.description or 'Aucune description disponible',
        'email': acheteur.email or 'Non spécifié',
        'fax': acheteur.fax or 'Non spécifié',
        'boite_postale': acheteur.boite_postale or 'Non spécifié',
        'site_internet': acheteur.site_internet or 'Non spécifié',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'ville': acheteur.ville.nom if acheteur.ville else 'Non spécifié',
        'province': acheteur.province.nom if acheteur.province else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_context, default=str)
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Récupérer les années actives pour le formulaire
    annee_list = Annee.objects.filter(is_active=True).order_by('-annee')
    
    # Préparer les données des années pour le template
    annee_data = [{'id': a.id, 'annee': a.annee} for a in annee_list]
    
    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,  # JSON pour JavaScript
        "acheteur": acheteur,  # Objet pour le template
        "annee_list": annee_data,  # Liste pour le select
        "id_acheteur": acheteur_id,
    }
        
    return render(
        request,
        "main/root/acheteur/reporting/dash_root_manage_acheteur_report_solvency.html",
        context,
    )



@login_required
def dash_root_manage_acheteur_emailling(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer l'acheteur pour avoir ses données
    # Récupérer l'acheteur avec relations optimisées
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique'
        ),
        id=acheteur_id
    )

    # Préparer les données pour JavaScript
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.strftime('%d/%m/%Y') if acheteur.date_creation else 'Non spécifiée',
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    
    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur_json": json.dumps(acheteur_data),
        "id_acheteur": id_acheteur,
        "acheteur": acheteur,  # Ajoutez l'objet acheteur
        "coloration_list": coloration_list,
    }
    
    return render(
        request,
        "main/root/acheteur/mailing/dash_root_manage_acheteur_emailling.html",
        context,
    )



@login_required
def dash_root_manage_report_mailing(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    
    context = {
        "reports_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "coloration_list": coloration_list,
    }
    
    return render(
        request,
        "main/root/report/dash_root_manage_report_mailing.html",
        context,
    )




@login_required
def dash_root_manage_acheteur_emailling_test(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()
    
    # Générer 15 commandes
    # NETTOYAGE AVANT GÉNÉRATION (optionnel - décommenter si besoin)
    # cleanup_done = False
    # if request.GET.get('cleanup') == 'true':
        # from main.utils import cleanup_test_data
        # cleanup_test_data(keep_today=False)
        # cleanup_done = True
        # print("🧹 Nettoyage effectué à la demande")
    
    # Générer des commandes seulement si nécessaire
    # from main.utils import generate_test_commandes
    # if Commande.objects.count() < 10:  # Seulement si peu de commandes
        # print("🎯 Génération de commandes de test...")
        # generate_test_commandes(15)
    
    # Afficher des infos de debug
    # clients_count = Client.objects.count()
    # commandes_count = Commande.objects.count()
    # print(f"🔍 Debug - Clients: {clients_count}, Commandes: {commandes_count}")
    
    nombre = 50
    print(f"🎯 Génération de {nombre} commandes de test...")

    # Récupérer ou créer les données de base
    clients = Client.objects.all()
    acheteurs = Acheteur.objects.all()
    demandeurs = User.objects.filter(role='Client')
    pays = Pays.objects.filter(nom='Gabon').first() or Pays.objects.create(nom='Gabon')
    ville = Ville.objects.first() or Ville.objects.create(nom='Libreville', pays=pays)
    devise = Devise.objects.first() or Devise.objects.create(code='XAF', nom='Franc CFA', symbole='FCFA')
    modele_rapport = ModeleRapport.objects.first() or ModeleRapport.objects.create(nom='Standard', code='STD')

    # Générer les commandes
    commandes_crees = []
    for i in range(nombre):
        # Choisir un client aléatoire (CLIENT, pas ACHETEUR)
        client_choisi = random.choice(clients)  # ← CORRECTION ICI
        acheteur_choisi = random.choice(acheteurs)  # ← Acheteur séparé
        
        commande = Commande.objects.create(
            notre_ref=f'CMD-2025-{i+1:03d}',
            reference_client=f'REF-ACHETEUR-{i+1:03d}',
            date_recept_commande=timezone.now().date() - timedelta(days=random.randint(1, 60)),
            date_rapport=timezone.now().date() + timedelta(days=random.randint(1, 30)),
            delais=f'{random.randint(1, 30)} jours',
            priorite=random.choice(['Haute', 'Moyenne', 'Basse']),
            raison_sociale=acheteur_choisi.nom,  # Nom du ACHETEUR (nom de l'acheteur)
            type_rapport=random.choice(['Standard', 'Détaillé', 'Express']),
            ref_type_rapport=modele_rapport,
            credit_demande=random.uniform(1000, 50000),
            devise_credit_demande=devise,
            credit_recommande=random.uniform(800, 45000),
            devise_credit_recommande=devise,
            numero_adresse=str(random.randint(1, 200)),
            rue_adresse=random.choice(['Rue de la Paix', 'Avenue des Ternes', 'Boulevard Saint-Germain']),
            code_postale_adresse=f'750{random.randint(1, 20):02d}',
            telephone=acheteur_choisi.fax,  # Téléphone du ACHETEUR
            email=acheteur_choisi.email,  # Email du ACHETEUR - IMPORTANT pour le filtrage!
            pays=pays,
            ville=ville,
            client=random.choice(demandeurs),  # L'analyste responsable
            acheteur=acheteur_choisi,  # L'acheteur (différent du client)
            status=random.choice(["nouvelle", "en_cours"]),
        )
        commandes_crees.append(commande)
        print(f"✅ Commande {i+1}/{nombre}: {commande.notre_ref} pour {client_choisi.nom} (Acheteur: {acheteur_choisi.nom})")
        print(f"🎉 {len(commandes_crees)} commandes générées avec succès!")

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "coloration_list": coloration_list,
    }
    
    return render(
        request,
        "main/root/acheteur/mailing/dash_root_manage_acheteur_emailling.html",
        context,
    )



# views/main/conseil_views.py

@login_required
def dash_root_manage_acheteur_membre_conseil(request, acheteur_id):
    """
    Vue pour la gestion des membres du conseil d'administration
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer tous les postes pour les listes déroulantes
    poste_list = PosteEntreprise.objects.all()
    fonction_list = [{'valeur': val[0], 'libelle': str(val[1])} for val in LISTE_NOUVELLE_FONCTION]
    
    # Récupérer toutes les colorations pour les listes déroulantes
    coloration_list = CouleurCommentaire.objects.all()
    
    # Statistiques
    stats = {
        'total': ConseilAdministration.objects.filter(acheteur=acheteur).count(),
        'avec_adresse': ConseilAdministration.objects.filter(
            acheteur=acheteur
        ).exclude(
            Q(numero_adresse='') | Q(rue_adresse='')
        ).count(),
        'avec_commentaire': ConseilAdministration.objects.filter(
            acheteur=acheteur
        ).exclude(commentaire='').count(),
    }
    
    # Membres récents
    membres_recent = ConseilAdministration.objects.filter(
        acheteur=acheteur
    ).select_related(
        'couleur_commentaire'
    ).order_by('-updated_at')[:4]
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "acheteur": acheteur,
        "poste_list": poste_list,
        "fonction_list": fonction_list,  # Ajoutez cette ligne
        "coloration_list": coloration_list,
        "stats": stats,
        "membres_recent": membres_recent,
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/conseil/dash_root_manage_acheteur_membre_conseil.html",
        context,
    )



# views/main/capital_views.py

@login_required
def dash_root_manage_acheteur_composition_capital(request, acheteur_id):
    """
    Vue pour la gestion du capital social unique d'un acheteur
    Un acheteur ne peut avoir qu'un seul capital social
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer le capital social existant (un seul)
    capital = CompositionCapitalSocial.objects.filter(acheteur=acheteur).first()
    
    # Calculer le pourcentage de capital libéré si le capital existe
    if capital and capital.emis and capital.emis > 0:
        capital.pourcentage_libere = round((capital.libere / capital.emis) * 100, 2)
    elif capital:
        capital.pourcentage_libere = 0
    
    # Récupérer toutes les devises pour les listes déroulantes
    devise_list = Devise.objects.all()
    
    # Récupérer toutes les colorations pour les listes déroulantes
    coloration_list = CouleurCommentaire.objects.all()
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Si un capital existe, préparer ses données pour le template et JavaScript
    capital_json = None
    if capital:
        capital_data = {
            'id': capital.id,
            'emis': float(capital.emis) if capital.emis else 0,
            'publie': float(capital.publie) if capital.publie else 0,
            'libere': float(capital.libere) if capital.libere else 0,
            'pourcentage_libere': capital.pourcentage_libere,
            'devise': {
                'id': capital.devise.id if capital.devise else None,
                'nom': capital.devise.nom if capital.devise else '',
                'symbole': capital.devise.symbole if capital.devise else '',
            } if capital.devise else None,
            'couleur_commentaire': {
                'id': capital.couleur_commentaire.id if capital.couleur_commentaire else None,
                'couleur': capital.couleur_commentaire.couleur if capital.couleur_commentaire else '',
                'code': capital.couleur_commentaire.code if capital.couleur_commentaire else '',
            } if capital.couleur_commentaire else None,
            'commentaire': capital.commentaire or '',
            'created_at': capital.created_at.isoformat() if capital.created_at else None,
            'updated_at': capital.updated_at.isoformat() if capital.updated_at else None,
        }
        capital_json = json.dumps(capital_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "capital_json": capital_json or 'null',
        "acheteur": acheteur,
        "capital": capital,
        "id_acheteur": acheteur_id,
        "devise_list": devise_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/root/acheteur/composition/dash_root_manage_acheteur_composition_capital.html",
        context,
    )





@login_required
def dash_root_manage_acheteur_actionnaire(request, acheteur_id):
    """
    Vue optimisée pour la gestion des actionnaires avec préfetch et statistiques
    """
    try:
        # Récupérer l'acheteur avec préfetch pour optimiser
        acheteur = get_object_or_404(
            Acheteur.objects.select_related(
                'statut_entreprise',
                'forme_juridique',
                'pays',
                'province',
                'ville'
            ).prefetch_related('compositionaction_set'),
            id=acheteur_id
        )

        # Récupérer toutes les colorations
        coloration_list = CouleurCommentaire.objects.all()
        
        # Statistiques détaillées
        actionnaires = CompositionAction.objects.filter(acheteur=acheteur)
        
        stats = {
            'total': actionnaires.count(),
            'avec_pourcentage': actionnaires.exclude(pourcentage__isnull=True).count(),
            'pourcentage_total': actionnaires.aggregate(total=Sum('pourcentage'))['total'] or 0,
            'avec_commentaire': actionnaires.exclude(commentaire='').count(),
            'avec_couleur': actionnaires.exclude(couleur_commentaire__isnull=True).count(),
        }
        
        # Actionnaires récents
        actionnaires_recent = actionnaires.select_related(
            'couleur_commentaire'
        ).order_by('-updated_at')[:4]
        
        # Génération des tokens JWT
        try:
            refresh = RefreshToken.for_user(request.user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
        except Exception as e:
            logger.error(f"Erreur lors de la génération des tokens: {e}")
            messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
            return redirect_to_login(request.get_full_path())
        
        # Préparer les données de l'acheteur pour le template
        acheteur_data = {
            'id': acheteur.id,
            'nom': acheteur.nom or 'Non spécifié',
            'sigle': acheteur.sigle or '',
            'code': acheteur.code or 'N/A',
            'activite_principale': acheteur.activite_principale or 'Non spécifié',
            'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
            'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
            'pourcentage_total_actionnaires': stats['pourcentage_total'],
        }
        
        # Convertir en JSON sécurisé
        acheteur_json = json.dumps(acheteur_data, default=str)

        context = {
            "acheteur_active": "active",
            "user": request.user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "acheteur_json": acheteur_json,
            "acheteur": acheteur,
            "coloration_list": coloration_list,
            "stats": stats,
            "actionnaires_recent": actionnaires_recent,
            "id_acheteur": acheteur_id,
        }
        return render(
            request,
            "main/root/acheteur/actionnaire/dash_root_manage_acheteur_actionnaire.html",
            context,
        )
        
    except Exception as e:
        logger.error(f"Erreur dans la vue actionnaire: {e}")
        messages.error(request, "Erreur lors du chargement de la page.")
        return redirect('dash_root_manage_acheteur', acheteur_id=acheteur_id)



@login_required
def dash_root_manage_acheteur_opinion_acremac(request, acheteur_id):
    """
    Vue pour la gestion de l'opinion de crédit unique d'un acheteur
    Un acheteur ne peut avoir qu'une seule opinion de crédit
    """
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer l'opinion existante (une seule)
    opinion = OpinionCreditAcremac.objects.filter(acheteur=acheteur).first()
    
    # Récupérer toutes les colorations pour les listes déroulantes
    coloration_list = CouleurCommentaire.objects.all()
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Si une opinion existe, préparer ses données
    opinion_json = None
    if opinion:
        opinion_data = {
            'id': opinion.id,
            'risque_de_defaut': opinion.risque_de_defaut or 0,
            'risque_de_concentration_credit': opinion.risque_de_concentration_credit or 0,
            'risque_de_reputation': opinion.risque_de_reputation or 0,
            'risque_pays': opinion.risque_pays or 0,
            'risque_de_taux_dinteret': opinion.risque_de_taux_dinteret or 0,
            'risque_de_liquidite': opinion.risque_de_liquidite or 0,
            'risque_eleve': opinion.risque_eleve or 0,
            'risque_moyen': opinion.risque_moyen or 0,
            'risque_faible': opinion.risque_faible or 0,
            'montant_credit_maximum': str(opinion.montant_credit_maximum) if opinion.montant_credit_maximum else '',
            'couleur_commentaire': opinion.couleur_commentaire.id if opinion.couleur_commentaire else None,
            'commentaire': opinion.commentaire or '',
        }
        opinion_json = json.dumps(opinion_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "opinion_json": opinion_json or 'null',
        "acheteur": acheteur,
        "opinion": opinion,
        "id_acheteur": acheteur_id,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/root/acheteur/opinion/dash_root_manage_acheteur_opinion_acremac.html",
        context,
    )




@login_required
def dash_root_manage_acheteur_filiale_optimized(request, acheteur_id):
    """
    Vue optimisée pour la gestion des filiales avec préfetch et statistiques
    """
    try:
        # Récupérer l'acheteur avec préfetch pour optimiser
        acheteur = get_object_or_404(
            Acheteur.objects.select_related(
                'statut_entreprise',
                'forme_juridique',
                'pays',
                'province',
                'ville'
            ).prefetch_related('structure_set'),
            id=acheteur_id
        )

        # Récupérer les listes pour les formulaires
        structure_list = StructureEntreprise.objects.all()
        coloration_list = CouleurCommentaire.objects.all()
        
        # Statistiques détaillées
        filiales = Structure.objects.filter(acheteur=acheteur)
        
        # Calcul des statistiques
        filiales_total = filiales.count()
        
        # Récupérer la répartition par type
        repartition_par_type = list(filiales.values('type_affiliation').annotate(
            count=Count('id')
        ).order_by('-count'))
        
        # Calculer le nombre total avec structure définie
        avec_structure = filiales.exclude(type_affiliation__isnull=True).count()
        
        stats = {
            'total': filiales_total,
            'avec_adresse': filiales.exclude(
                Q(numero_adresse='') | Q(rue_adresse='')
            ).count(),
            'avec_commentaire': filiales.exclude(commentaire='').count(),
            'avec_couleur': filiales.exclude(couleur_commentaire__isnull=True).count(),
            'avec_structure': avec_structure,
            'par_type': repartition_par_type,  # Liste de dictionnaires
            'par_type_json': json.dumps(repartition_par_type),  # Pour JavaScript
        }
        
        # Filiales récentes
        # Pour optimiser davantage
        filiales_recent = filiales.select_related(
            'couleur_commentaire',
            'created_by',    # Si vous voulez accéder à ces informations
            'updated_by'     # Si vous voulez accéder à ces informations
        ).order_by('-updated_at')[:4]
        
        # Génération des tokens JWT
        try:
            refresh = RefreshToken.for_user(request.user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
        except Exception as e:
            logger.error(f"Erreur lors de la génération des tokens: {e}")
            messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
            return redirect_to_login(request.get_full_path())
        
        # Préparer les données de l'acheteur pour le template
        acheteur_data = {
            'id': acheteur.id,
            'nom': acheteur.nom or 'Non spécifié',
            'sigle': acheteur.sigle or '',
            'code': acheteur.code or 'N/A',
            'activite_principale': acheteur.activite_principale or 'Non spécifié',
            'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
            'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
            'filiales_total': stats['total'],
        }
        
        # Convertir en JSON sécurisé
        acheteur_json = json.dumps(acheteur_data, default=str)

        context = {
            "acheteur_active": "active",
            "user": request.user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "acheteur_json": acheteur_json,
            "acheteur": acheteur,
            "structure_list": structure_list,
            "coloration_list": coloration_list,
            "stats": stats,
            "filiales_recent": filiales_recent,
            "id_acheteur": acheteur_id,
            "type_affiliation_choices": LIEN_ENTREPRISE_CHOICE,  # Ajouté
        }
        return render(
            request,
            "main/root/acheteur/filiale/dash_root_manage_acheteur_filiale_optimized.html",
            context,
        )
        
    except Exception as e:
        logger.error(f"Erreur dans la vue filiale: {e}")
        messages.error(request, "Erreur lors du chargement de la page.")
        return redirect('dash_root_manage_acheteur', acheteur_id=acheteur_id)




@login_required
def dash_root_manage_acheteur_analyse_sectorielle(request, acheteur_id):
    """
    Vue pour la gestion de l'analyse sectorielle unique d'un acheteur
    Un acheteur ne peut avoir qu'une seule analyse sectorielle
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer l'analyse sectorielle existante (une seule)
    analyse = AnalyseSectorielle.objects.filter(acheteur=acheteur).first()
    
    # Récupérer toutes les colorations pour les listes déroulantes
    coloration_list = CouleurCommentaire.objects.all()
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Si une analyse existe, préparer ses données pour le template et JavaScript
    analyse_json = None
    if analyse:
        analyse_data = {
            'id': analyse.id,
            'commentaire': analyse.commentaire or '',
            'impact_covid_19': analyse.impact_covid_19 or '',
            'couleur_commentaire': {
                'id': analyse.couleur_commentaire.id if analyse.couleur_commentaire else None,
                'couleur': analyse.couleur_commentaire.couleur if analyse.couleur_commentaire else '',
                'code': analyse.couleur_commentaire.code if analyse.couleur_commentaire else '',
            } if analyse.couleur_commentaire else None,
            'created_at': analyse.created_at.isoformat() if analyse.created_at else None,
            'updated_at': analyse.updated_at.isoformat() if analyse.updated_at else None,
        }
        analyse_json = json.dumps(analyse_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "analyse_json": analyse_json or 'null',
        "acheteur": acheteur,
        "analyse": analyse,
        "id_acheteur": acheteur_id,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/root/acheteur/analyse/dash_root_manage_acheteur_analyse_sectorielle.html",
        context,
    )




@login_required
def dash_root_manage_acheteur_compte_financier(request, acheteur_id):
    """
    Vue pour la gestion du compte financier unique d'un acheteur
    Un acheteur ne peut avoir qu'un seul compte financier
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer le compte financier existant (un seul)
    compte_financier = CompteFinancier.objects.filter(acheteur=acheteur).first()
    
    # Récupérer les listes pour les formulaires
    coloration_list = CouleurCommentaire.objects.all()
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Si un compte financier existe, préparer ses données pour le template et JavaScript
    compte_financier_json = None
    if compte_financier:
        compte_financier_data = {
            'id': compte_financier.id,
            'cabinet': compte_financier.cabinet or '',
            'requis_pour_deposer': compte_financier.requis_pour_deposer or '',
            'credibilite_cabinet': compte_financier.credibilite_cabinet or '',
            'source': compte_financier.source or '',
            'presentation': compte_financier.presentation or '',
            'date_compte': compte_financier.date_compte.isoformat() if compte_financier.date_compte else None,
            'date_fin': compte_financier.date_fin.isoformat() if compte_financier.date_fin else None,
            'date_compte_n_moins_un': compte_financier.date_compte_n_moins_un.isoformat() if compte_financier.date_compte_n_moins_un else None,
            'date_fin_n_moins_un': compte_financier.date_fin_n_moins_un.isoformat() if compte_financier.date_fin_n_moins_un else None,
            'date_compte_n_moins_deux': compte_financier.date_compte_n_moins_deux.isoformat() if compte_financier.date_compte_n_moins_deux else None,
            'date_fin_n_moins_deux': compte_financier.date_fin_n_moins_deux.isoformat() if compte_financier.date_fin_n_moins_deux else None,
            'type_compte': compte_financier.type_compte or '',
            'devise': compte_financier.devise or 'XAF',
            'type_bilan': compte_financier.type_bilan or '',
            'couleur_commentaire': {
                'id': compte_financier.couleur_commentaire.id if compte_financier.couleur_commentaire else None,
                'couleur': compte_financier.couleur_commentaire.couleur if compte_financier.couleur_commentaire else '',
                'code': compte_financier.couleur_commentaire.code if compte_financier.couleur_commentaire else '',
            } if compte_financier.couleur_commentaire else None,
            'commentaire': compte_financier.commentaire or '',
            'created_at': compte_financier.created_at.isoformat() if compte_financier.created_at else None,
            'updated_at': compte_financier.updated_at.isoformat() if compte_financier.updated_at else None,
        }
        compte_financier_json = json.dumps(compte_financier_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "compte_financier_json": compte_financier_json or 'null',
        "acheteur": acheteur,
        "compte_financier": compte_financier,
        "id_acheteur": acheteur_id,
        "coloration_list": coloration_list,
        "devise_list": Devise.objects.filter(code__in=[c for c, _ in CompteFinancier.STATUS_CHANGE]),
        "type_bilan_choices": CompteFinancier.LIEN_TYPE_BILAN_CHOICE,
        "oui_non_choices": CompteFinancier.STATUS__OUI_NON,  # Si disponible dans le modèle
    }
    return render(
        request,
        "main/root/acheteur/finance/dash_root_manage_acheteur_compte_financier.html",
        context,
    )




@login_required
def dash_root_manage_acheteur_operation_historique(request, acheteur_id):
    """
    Vue pour la gestion des opérations et historiques d'un acheteur
    """

    # =========================
    # Acheteur
    # =========================
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # =========================
    # Opérations / Historiques
    # =========================
    operation = (
        OperationEtHistorique.objects
        .filter(acheteur=acheteur)
        .prefetch_related('importation')
        .order_by('-created_at')
        .first()
    )

    # =========================
    # JWT Tokens
    # =========================
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens JWT : {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    # =========================
    # Importations
    # =========================
    importations = ListeImportation.objects.all().order_by('libelle')
    importations_json = json.dumps(
        [{'id': imp.id, 'libelle': str(imp)} for imp in importations],
        default=str
    )

    # =========================
    # Données Acheteur (JS)
    # =========================
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }

    acheteur_json = json.dumps(acheteur_data, default=str)

    # =========================
    # Données Opérations (JS)
    # =========================
    operations_data = []

    if operation:
        operations_data.append({
            'id': operation.id,
            'commentaire_ratios': operation.commentaire_ratios or '',
            'description_complete_activite': operation.description_complete_activite or '',
            'historique': operation.historique or '',
            'importation_list': [
                {'id': imp.id, 'libelle': str(imp)}
                for imp in operation.importation.all()
            ],
            'created_at': operation.created_at.isoformat() if operation.created_at else None,
            'updated_at': operation.updated_at.isoformat() if operation.updated_at else None,
        })

    operations_json = json.dumps(operations_data, default=str)

    # =========================
    # Context Template
    # =========================
    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "operations_json": operations_json,
        "importations_json": importations_json,
        "acheteur": acheteur,
        "operation": operation,
        "importations": importations,
        "id_acheteur": acheteur_id,
    }

    return render(
        request,
        "main/root/acheteur/operation/dash_root_manage_acheteur_operation_historique.html",
        context,
    )



# views.py

@login_required
def dash_root_manage_acheteur_propriete_actif(request, acheteur_id):
    """
    Vue pour la gestion des propriétés et actifs d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer la propriété/actif de l'acheteur
    propriete_actif = ProprieteEtActif.objects.filter(
        acheteur=acheteur
    ).prefetch_related('locaux').first()
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Récupérer tous les locaux disponibles
    locaux = Locaux.objects.all().order_by('nom')
    locaux_data = [
        {'id': local.id, 'nom': local.nom or ''} 
        for local in locaux
    ]
    # Convertir en JSON sécurisé
    locaux_json = json.dumps(locaux_data, ensure_ascii=False)
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Préparer les données de la propriété/actif pour le template
    propriete_actif_data = None
    if propriete_actif:
        propriete_actif_data = {
            'id': propriete_actif.id,
            'branche': propriete_actif.branche or '',
            'locaux_list': [{'id': local.id, 'nom': local.nom} for local in propriete_actif.locaux.all()],
            'created_at': propriete_actif.created_at.isoformat() if propriete_actif.created_at else None,
            'updated_at': propriete_actif.updated_at.isoformat() if propriete_actif.updated_at else None,
        }
    
    propriete_actif_json = json.dumps(propriete_actif_data, default=str) if propriete_actif_data else 'null'

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "propriete_actif_json": propriete_actif_json or 'null',
        "acheteur": acheteur,
        "propriete_actif": propriete_actif,
        "locaux": locaux,
        "locaux_data": locaux_data,  # Ajoutez cette ligne
        "locaux_json": locaux_json or '[]',
        "has_propriete_actif": propriete_actif is not None,
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/propriete/dash_root_manage_acheteur_propriete_actif.html",
        context,
    )




# views.py

@login_required
def dash_root_manage_acheteur_condition_achat(request, acheteur_id):
    """
    Vue pour la gestion des conditions d'achat d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer les conditions d'achat de l'acheteur
    condition_achat = ConditionAchat.objects.filter(
        acheteur=acheteur
    ).prefetch_related('local', 'importation').first()
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Récupérer toutes les conditions d'achat disponibles
    conditions_liste = ListeConditionAchat.objects.all().order_by('nom')
    conditions_json = json.dumps([
        {'id': cond.id, 'nom': cond.nom} for cond in conditions_liste
    ], default=str)
    
    print(conditions_liste)
    print(conditions_json)
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Préparer les données des conditions d'achat pour le template
    condition_achat_data = None
    if condition_achat:
        condition_achat_data = {
            'id': condition_achat.id,
            'les_clients': condition_achat.les_clients or '',
            'fournisseur': condition_achat.fournisseur or '',
            'local_list': [{'id': item.id, 'nom': item.nom} for item in condition_achat.local.all()],
            'importation_list': [{'id': item.id, 'nom': item.nom} for item in condition_achat.importation.all()],
            'created_at': condition_achat.created_at.isoformat() if condition_achat.created_at else None,
            'updated_at': condition_achat.updated_at.isoformat() if condition_achat.updated_at else None,
        }
    
    condition_achat_json = json.dumps(condition_achat_data, default=str) if condition_achat_data else 'null'

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "condition_achat_json": condition_achat_json or 'null',
        "conditions_json": conditions_json or '[]',
        "acheteur": acheteur,
        "condition_achat": condition_achat,
        "conditions_liste": conditions_liste,
        "has_condition_achat": condition_achat is not None,
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/achat/dash_root_manage_acheteur_condition_achat.html",
        context,
    )



# views.py

@login_required
def dash_root_manage_acheteur_condition_vente(request, acheteur_id):
    """
    Vue pour la gestion des conditions de vente d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer les conditions de vente de l'acheteur
    condition_vente = ConditionDeVente.objects.filter(
        acheteur=acheteur
    ).prefetch_related('local').first()
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Récupérer toutes les conditions de vente disponibles
    conditions_liste = ListeConditionVente.objects.all().order_by('nom')
    conditions_json = json.dumps([
        {'id': cond.id, 'nom': cond.nom} for cond in conditions_liste
    ], default=str)
    
    # Préparer les choix pour les champs
    recouvrement_choices = [
        {'value': choice[0], 'label': str(choice[1])}
        for choice in ConditionDeVente.LIEN_COMPORTEMENT_JUGEMENT_CHOICE
    ]
    
    paiement_choices = [
        {'value': choice[0], 'label': str(choice[1])}
        for choice in ConditionDeVente.LIEN_COMPORTEMENT_PAIEMENT_CHOICE
    ]
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Préparer les données des conditions de vente pour le template
    condition_vente_data = None
    if condition_vente:
        condition_vente_data = {
            'id': condition_vente.id,
            'recouvrement_de_dette_jugement': condition_vente.recouvrement_de_dette_jugement,
            'comportement_de_paiement': condition_vente.comportement_de_paiement,
            'local_list': [{'id': item.id, 'nom': item.nom} for item in condition_vente.local.all()],
            'created_at': condition_vente.created_at.isoformat() if condition_vente.created_at else None,
            'updated_at': condition_vente.updated_at.isoformat() if condition_vente.updated_at else None,
        }
    
    condition_vente_json = json.dumps(condition_vente_data, default=str) if condition_vente_data else 'null'

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "condition_vente_json": condition_vente_json or 'null',
        "conditions_json": conditions_json or '[]',
        "recouvrement_choices": json.dumps(recouvrement_choices, default=str),
        "paiement_choices": json.dumps(paiement_choices, default=str),
        "acheteur": acheteur,
        "condition_vente": condition_vente,
        "conditions_liste": conditions_liste,
        "recouvrement_choices_list": recouvrement_choices,
        "paiement_choices_list": paiement_choices,
        "has_condition_vente": condition_vente is not None,
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/vente/dash_root_manage_acheteur_condition_vente.html",
        context,
    )



@login_required
def dash_root_manage_acheteur_sommaire_avis(request, acheteur_id):
    """
    Vue pour la gestion du sommaire et avis unique d'un acheteur
    Un acheteur ne peut avoir qu'un seul sommaire et avis
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer le sommaire et avis existant (un seul)
    sommaire_avis = SommaireEtAvis.objects.filter(acheteur=acheteur).first()
    
    # Récupérer toutes les colorations pour les listes déroulantes
    coloration_list = CouleurCommentaire.objects.all()
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Si un sommaire/avis existe, préparer ses données pour le template et JavaScript
    sommaire_avis_json = None
    if sommaire_avis:
        sommaire_avis_data = {
            'id': sommaire_avis.id,
            'commentaire': sommaire_avis.commentaire or '',
            'couleur_commentaire': {
                'id': sommaire_avis.couleur_commentaire.id if sommaire_avis.couleur_commentaire else None,
                'couleur': sommaire_avis.couleur_commentaire.couleur if sommaire_avis.couleur_commentaire else '',
                'code': sommaire_avis.couleur_commentaire.code if sommaire_avis.couleur_commentaire else '',
            } if sommaire_avis.couleur_commentaire else None,
            'created_at': sommaire_avis.created_at.isoformat() if sommaire_avis.created_at else None,
            'updated_at': sommaire_avis.updated_at.isoformat() if sommaire_avis.updated_at else None,
        }
        sommaire_avis_json = json.dumps(sommaire_avis_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "sommaire_avis_json": sommaire_avis_json or 'null',
        "acheteur": acheteur,
        "sommaire_avis": sommaire_avis,
        "id_acheteur": acheteur_id,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/root/acheteur/sommaire/dash_root_manage_acheteur_sommaire_avis.html",
        context,
    )




@login_required
def dash_root_manage_acheteur_advice(request, acheteur_id):
    """
    Vue pour la gestion des conseils unique d'un acheteur
    Un acheteur ne peut avoir qu'un seul conseil
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer le conseil existant (un seul)
    advice = Advice.objects.filter(acheteur=acheteur).first()
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Si un conseil existe, préparer ses données pour le template et JavaScript
    advice_json = None
    if advice:
        advice_data = {
            'id': advice.id,
            'points_forts': advice.points_forts or '',
            'points_faibles': advice.points_faibles or '',
            'dynamisme_court_terme': advice.dynamisme_court_terme or '',
            'dynamisme_long_terme': advice.dynamisme_long_terme or '',
            'risque_potentiel_court_terme': advice.risque_potentiel_court_terme or '',
            'created_at': advice.created_at.isoformat() if advice.created_at else None,
            'updated_at': advice.updated_at.isoformat() if advice.updated_at else None,
        }
        advice_json = json.dumps(advice_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "advice_json": advice_json or 'null',
        "acheteur": acheteur,
        "advice": advice,
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/advice/dash_root_manage_acheteur_advice.html",
        context,
    )




@login_required
def dash_root_manage_acheteur_geopolitic(request, acheteur_id):
    """
    Vue pour la gestion de la géopolitique unique d'un acheteur
    Un acheteur ne peut avoir qu'une seule analyse géopolitique
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer l'analyse géopolitique existante (une seule)
    geopolitic = Geopolitics.objects.filter(acheteur=acheteur).first()
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Si une analyse géopolitique existe, préparer ses données pour le template et JavaScript
    geopolitic_json = None
    if geopolitic:
        geopolitic_data = {
            'id': geopolitic.id,
            'stabilite_politique': geopolitic.stabilite_politique or '',
            'etat_droit': geopolitic.etat_droit or '',
            'efficacite': geopolitic.efficacite or '',
            'qualite': geopolitic.qualite or '',
            'liberte_expression': geopolitic.liberte_expression or '',
            'donnees_politiques': geopolitic.donnees_politiques or '',
            'donnees_economiques': geopolitic.donnees_economiques or '',
            'created_at': geopolitic.created_at.isoformat() if geopolitic.created_at else None,
            'updated_at': geopolitic.updated_at.isoformat() if geopolitic.updated_at else None,
            'score_moyen': calculate_average_score(geopolitic)
        }
        geopolitic_json = json.dumps(geopolitic_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "geopolitic_json": geopolitic_json or 'null',
        "acheteur": acheteur,
        "geopolitic": geopolitic,
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/geopolitique/dash_root_manage_acheteur_geopolitic.html",
        context,
    )


def dash_root_manage_acheteur_geopolitic_form(request, acheteur_id):
    """Page dédiée pour créer/modifier l'analyse géopolitique (évite le débordement du modal Quill)."""
    acheteur = get_object_or_404(
        Acheteur.objects.select_related('statut_entreprise', 'forme_juridique', 'pays', 'province', 'ville'),
        id=acheteur_id,
    )

    geopolitic = Geopolitics.objects.filter(acheteur=acheteur).first()

    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    geopolitic_json = None
    if geopolitic:
        geopolitic_data = {
            'id': geopolitic.id,
            'stabilite_politique': geopolitic.stabilite_politique or '',
            'etat_droit': geopolitic.etat_droit or '',
            'efficacite': geopolitic.efficacite or '',
            'qualite': geopolitic.qualite or '',
            'liberte_expression': geopolitic.liberte_expression or '',
            'donnees_politiques': geopolitic.donnees_politiques or '',
            'donnees_economiques': geopolitic.donnees_economiques or '',
        }
        geopolitic_json = json.dumps(geopolitic_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur": acheteur,
        "geopolitic": geopolitic,
        "geopolitic_json": geopolitic_json or 'null',
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/geopolitique/dash_root_manage_acheteur_geopolitic_form.html",
        context,
    )


def calculate_average_score(geopolitic):
    """Calcule la moyenne des scores géopolitiques"""
    scores = []
    if geopolitic.stabilite_politique and geopolitic.stabilite_politique.isdigit():
        scores.append(int(geopolitic.stabilite_politique))
    if geopolitic.etat_droit and geopolitic.etat_droit.isdigit():
        scores.append(int(geopolitic.etat_droit))
    if geopolitic.efficacite and geopolitic.efficacite.isdigit():
        scores.append(int(geopolitic.efficacite))
    if geopolitic.qualite and geopolitic.qualite.isdigit():
        scores.append(int(geopolitic.qualite))
    if geopolitic.liberte_expression and geopolitic.liberte_expression.isdigit():
        scores.append(int(geopolitic.liberte_expression))
    
    if scores:
        return round(sum(scores) / len(scores), 1)
    return 0




@login_required
def dash_root_manage_acheteur_banking_optimized(request, acheteur_id):
    """
    Vue optimisée pour la gestion des données bancaires
    """
    
    start_time = time.time()
    cache_key = f'banking_view_{acheteur_id}_{request.user.id}'
    cached_data = cache.get(cache_key)
    
    # J'ai un pays stocke en 
    pays = request.session.get('pays')

    pays_user = None
    if request.user.is_authenticated:
        pays_user = getattr(request.user, 'pays', None)

    print("Pays session :", pays)
    print("Pays utilisateur :", pays_user)


    try:
        # Récupérer l'acheteur avec préfetch pour optimiser
        acheteur = get_object_or_404(
            Acheteur.objects.select_related(
                'statut_entreprise',
                'forme_juridique',
                'pays',
                'province',
                'ville'
            ).prefetch_related('banquier_set'),
            id=acheteur_id
        )

        # Récupérer les listes pour les formulaires
        # ville_list = Ville.objects.select_related('pays').all()[:100]  # Limiter à 100
        ville_list = Ville.objects.filter(
            Q(pays=pays) | Q(pays=pays_user)
        )
        coloration_list = CouleurCommentaire.objects.all()
        
        # Statistiques détaillées
        bankings = Banquier.objects.filter(acheteur=acheteur)
        
        # Calcul des statistiques
        bankings_total = bankings.count()
        
        # Statistiques
        stats = {
            'total': bankings_total,
            'banques_uniques': bankings.aggregate(
                count=Count('nom_banque', distinct=True)
            )['count'],
            'avec_compte': bankings.filter(
                numero_compte__isnull=False
            ).exclude(numero_compte='').count(),
            'avec_adresse': bankings.filter(
                ~Q(numero='') & ~Q(rue='')
            ).count(),
            'avec_commentaire': bankings.filter(
                commentaire__isnull=False
            ).exclude(commentaire='').count(),
            'avec_couleur': bankings.exclude(couleur_commentaire__isnull=True).count(),
            'par_relation': list(bankings.filter(
                type_relation__isnull=False
            ).exclude(type_relation='').values('type_relation').annotate(
                count=Count('id')
            ).order_by('-count')),
        }
        
        # Données bancaires récentes
        banking_recent = bankings.select_related(
            'ville', 
            'couleur_commentaire'
        ).order_by('-updated_at')[:4]
        
        # Génération des tokens JWT
        try:
            refresh = RefreshToken.for_user(request.user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
        except Exception as e:
            logger.error(f"Erreur lors de la génération des tokens: {e}")
            messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
            return redirect_to_login(request.get_full_path())
        
        context = {
            "acheteur_active": "active",
            "user": request.user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "acheteur": acheteur,
            "ville_list": ville_list,
            "coloration_list": coloration_list,
            "stats": stats,
            "banking_recent": banking_recent,
            "id_acheteur": acheteur_id,
        }
        
        # Log des temps
        logger.info(f"Temps total pour banking view: {time.time() - start_time:.2f}s")
        
        return render(
            request,
            "main/root/acheteur/banque/dash_root_manage_acheteur_banking_optimized.html",
            context,
        )
        
    except Exception as e:
        logger.error(f"Erreur dans la vue banking: {e}")
        messages.error(request, "Erreur lors du chargement de la page.")
        return redirect('dash_root_manage_acheteur', acheteur_id=acheteur_id)







@login_required
def dash_root_manage_acheteur_actif_anglais(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    compte_financier = CompteFinancier.objects.filter(acheteur=acheteur).first()
    devise_acheteur = (compte_financier.devise or '') if compte_financier else ''

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_acheteur": devise_acheteur,
    }
    return render(
        request,
        "main/root/acheteur/bilans/anglais/dash_root_manage_acheteur_actif_anglais.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_passif_anglais(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    compte_financier = CompteFinancier.objects.filter(acheteur=acheteur).first()
    devise_acheteur = (compte_financier.devise or '') if compte_financier else ''

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_acheteur": devise_acheteur,
    }
    return render(
        request,
        "main/root/acheteur/bilans/anglais/dash_root_manage_acheteur_passif_anglais.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_resultat_anglais(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    compte_financier = CompteFinancier.objects.filter(acheteur=acheteur).first()
    devise_acheteur = (compte_financier.devise or '') if compte_financier else ''

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_acheteur": devise_acheteur,
    }
    return render(
        request,
        "main/root/acheteur/bilans/anglais/dash_root_manage_acheteur_resultat_anglais.html",
        context,
    )


def _bilan_anglais_base_context(request, acheteur_id):
    """Shared context builder for all bilan anglais add/edit views."""
    acheteur = get_object_or_404(
        Acheteur.objects.select_related('statut_entreprise', 'forme_juridique', 'pays', 'province', 'ville'),
        id=acheteur_id,
    )
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        return None, acheteur
    compte_financier = CompteFinancier.objects.filter(acheteur=acheteur).first()
    devise_acheteur = (compte_financier.devise or '') if compte_financier else ''
    return {
        "acheteur_active": "active",
        "user": request.user,
        "access": access_token,
        "refresh": refresh_token,
        "acheteur": acheteur,
        "annee_list": Annee.objects.all(),
        "devise_acheteur": devise_acheteur,
    }, acheteur


@login_required
def dash_root_manage_acheteur_add_actif_anglais(request, acheteur_id):
    ctx, acheteur = _bilan_anglais_base_context(request, acheteur_id)
    if ctx is None:
        messages.error(request, "Erreur d'authentification.")
        return redirect_to_login(request.get_full_path())
    return render(request, "main/root/acheteur/bilans/anglais/dash_root_manage_acheteur_add_actif_anglais.html", ctx)


@login_required
def dash_root_manage_acheteur_edit_actif_anglais(request, acheteur_id, actif_id):
    ctx, acheteur = _bilan_anglais_base_context(request, acheteur_id)
    if ctx is None:
        messages.error(request, "Erreur d'authentification.")
        return redirect_to_login(request.get_full_path())
    ctx["actif_id"] = actif_id
    return render(request, "main/root/acheteur/bilans/anglais/dash_root_manage_acheteur_edit_actif_anglais.html", ctx)


@login_required
def dash_root_manage_acheteur_add_passif_anglais(request, acheteur_id):
    ctx, acheteur = _bilan_anglais_base_context(request, acheteur_id)
    if ctx is None:
        messages.error(request, "Erreur d'authentification.")
        return redirect_to_login(request.get_full_path())
    return render(request, "main/root/acheteur/bilans/anglais/dash_root_manage_acheteur_add_passif_anglais.html", ctx)


@login_required
def dash_root_manage_acheteur_edit_passif_anglais(request, acheteur_id, passif_id):
    ctx, acheteur = _bilan_anglais_base_context(request, acheteur_id)
    if ctx is None:
        messages.error(request, "Erreur d'authentification.")
        return redirect_to_login(request.get_full_path())
    ctx["passif_id"] = passif_id
    return render(request, "main/root/acheteur/bilans/anglais/dash_root_manage_acheteur_edit_passif_anglais.html", ctx)


@login_required
def dash_root_manage_acheteur_add_resultat_anglais(request, acheteur_id):
    ctx, acheteur = _bilan_anglais_base_context(request, acheteur_id)
    if ctx is None:
        messages.error(request, "Erreur d'authentification.")
        return redirect_to_login(request.get_full_path())
    return render(request, "main/root/acheteur/bilans/anglais/dash_root_manage_acheteur_add_resultat_anglais.html", ctx)


@login_required
def dash_root_manage_acheteur_edit_resultat_anglais(request, acheteur_id, resultat_id):
    ctx, acheteur = _bilan_anglais_base_context(request, acheteur_id)
    if ctx is None:
        messages.error(request, "Erreur d'authentification.")
        return redirect_to_login(request.get_full_path())
    ctx["resultat_id"] = resultat_id
    return render(request, "main/root/acheteur/bilans/anglais/dash_root_manage_acheteur_edit_resultat_anglais.html", ctx)








@login_required
def dash_root_manage_acheteur_actif_classique(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les actifs
    actifs_classiques = ActifC.objects.filter(acheteur=acheteur)
    print("[ACHETEUR][CLASSIQUE][ACTIFS] "f"actifs={actifs_classiques}")

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/root/acheteur/bilans/classique/dash_root_manage_acheteur_actif_classique.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_passif_classique(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les actifs
    passifs_classiques = PassifC.objects.filter(acheteur=acheteur)
    print("[ACHETEUR][CLASSIQUE][PASSIFS] "f"passifs={passifs_classiques}")

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/root/acheteur/bilans/classique/dash_root_manage_acheteur_passif_classique.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_resultat_classique(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les actifs
    resultats_classiques = ResultatC.objects.filter(acheteur=acheteur)
    print("[ACHETEUR][CLASSIQUE][RESULTATS] "f"resultats={resultats_classiques}")

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/root/acheteur/bilans/classique/dash_root_manage_acheteur_resultat_classique.html",
        context,
    )
    
    
@login_required
def dash_root_manage_acheteur_bilan_classique(request, acheteur_id):
    # 1. Récupération unique et optimisée de l'acheteur
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise', 'forme_juridique',
            'pays', 'province', 'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )

    # 2. Gestion des Tokens JWT (Une seule fois)
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
    except Exception as e:
        logger.error(f"Erreur JWT : {e}")
        messages.error(request, "Session expirée. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    # 3. Préparation des données JSON pour le frontend
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }

    # 4. Pagination Helper (pour éviter la répétition)
    def get_paginated_data(queryset, page_param, per_page=10):
        paginator = Paginator(queryset, per_page)
        return paginator.get_page(request.GET.get(page_param))

    # Récupération des données financières
    actifs = ActifC.objects.filter(acheteur=acheteur).all()
    actifs_qs = ActifC.objects.filter(acheteur=acheteur).select_related('annee').order_by("-created_at")
    passifs_qs = PassifC.objects.filter(acheteur=acheteur).select_related('annee').order_by("-created_at")
    resultats_qs = ResultatC.objects.filter(acheteur=acheteur).select_related('annee').order_by("-created_at")
    
    print(acheteur)
    print(actifs)
    print(actifs_qs)
    print(passifs_qs)
    print(resultats_qs)

    # 5. Construction du contexte
    context = {
        # UI State
        "acheteur_active": "active",
        
        # Auth/Tokens
        "access_token": access_token,
        "refresh_token": str(refresh),
        
        # Objets principaux
        "acheteur": acheteur,
        "acheteur_json": json.dumps(acheteur_data, default=str),
        
        # Données pour formulaires/listes
        "acheteurs": Acheteur.objects.only('id', 'nom'), # Optimisé : ne charge que le nécessaire
        "annee_list": Annee.objects.all().order_by('-annee'),
        "annee_list_data": json.dumps(list(Annee.objects.values("id", "annee"))),
        "type_bilan_choices_json": json.dumps(list(TYPE_BILAN_CHOICES)),
        "semestre_choices_json": json.dumps(list(SEMESTRE_CHOICES)),
        
        # Pagination
        "actifs_c_page": get_paginated_data(actifs_qs, "page_actifs"),
        "passifs_c_page": get_paginated_data(passifs_qs, "page_passifs"),
        "resultats_c_page": get_paginated_data(resultats_qs, "page_resultats"),
    }

    return render(
        request,
        "main/root/acheteur/bilans/classique/dash_root_manage_acheteur_bilan_classique.html",
        context,
    ) 







@login_required
def dash_root_manage_acheteur_actif_syscohada(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/root/acheteur/bilans/syscohada/dash_root_manage_acheteur_actif_syscohada.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_passif_syscohada(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/root/acheteur/bilans/syscohada/dash_root_manage_acheteur_passif_syscohada.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_resultat_syscohada(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/root/acheteur/bilans/syscohada/dash_root_manage_acheteur_resultat_syscohada.html",
        context,
    )










@login_required
def dash_root_manage_acheteur_asset_bancaire(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.filter(is_active=True).order_by('-annee')

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/root/acheteur/bilans/bancaire/dash_root_manage_acheteur_asset_bancaire.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_liabilitie_bancaire(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Convertir la liste des années en JSON
    annee_list_json = json.dumps([
        {'id': annee.id, 'annee': annee.annee} 
        for annee in annee_list
    ])

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "annee_list_json": annee_list_json,
    }
    return render(
        request,
        "main/root/acheteur/bilans/bancaire/dash_root_manage_acheteur_liabilitie_bancaire.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_offbalancesheet_bancaire(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Convertir la liste des années en JSON
    annee_list_json = json.dumps([
        {'id': annee.id, 'annee': annee.annee} 
        for annee in annee_list
    ])

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "annee_list_json": annee_list_json,
    }
    return render(
        request,
        "main/root/acheteur/bilans/bancaire/dash_root_manage_acheteur_offbalancesheet_bancaire.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_expense_bancaire(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Convertir la liste des années en JSON
    annee_list_json = json.dumps([
        {'id': annee.id, 'annee': annee.annee} 
        for annee in annee_list
    ])

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "annee_list_json": annee_list_json,
    }
    return render(
        request,
        "main/root/acheteur/bilans/bancaire/dash_root_manage_acheteur_expense_bancaire.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_product_bancaire(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
        
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Convertir la liste des années en JSON
    annee_list_json = json.dumps([
        {'id': annee.id, 'annee': annee.annee} 
        for annee in annee_list
    ])

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "annee_list_json": annee_list_json,
    }
    return render(
        request,
        "main/root/acheteur/bilans/bancaire/dash_root_manage_acheteur_product_bancaire.html",
        context,
    )


















@login_required
def dash_root_manage_acheteur_actif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Actif"
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
    }
    return render(
        request,
        "main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_actif_irfs.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_passif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Passif"
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
    }
    return render(
        request,
        "main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_passif_irfs.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_resultat_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Compte de "
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
    }
    return render(
        request,
        "main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_passif_irfs.html",
        context,
    )



@login_required
def dash_root_manage_acheteur_ratio_financier_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_ratio_financier_irfs.html",
        context,
    )








@login_required
def dash_root_manage_acheteur_compte_financier_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_compte_financier_irfs.html",
        context,
    )



@login_required
def dash_root_manage_acheteur_add_actif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Actif"
    )

    # Récupérer tous les actifs financiers irfs
    actif_financier_irfs_list = ValeurCompteIrfs.objects.filter(
        compte__type_compte__icontains="Actif", acheteur__pk=id_acheteur
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
        "actif_financier_irfs_list": actif_financier_irfs_list,
    }
    return render(
        request,
        "main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_add_actif_irfs.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_add_passif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Passif"
    )

    # Récupérer tous les actifs financiers irfs
    actif_financier_irfs_list = ValeurCompteIrfs.objects.filter(
        compte__type_compte__icontains="Passif", acheteur__pk=id_acheteur
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
        "actif_financier_irfs_list": actif_financier_irfs_list,
    }
    return render(
        request,
        "main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_add_passif_irfs.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_report_web(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Recuperer les elements du rapports ici !

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/root/acheteur/report/dash_root_manage_acheteur_report_web.html",
        context,
    )




from django.db import connection
@login_required
def dash_root_commande(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user
    # create_fake_commands(15)
    # 1. Delete all objects using the ORM (this is the "delete" part)
    # Commande.objects.all().delete()

    # 2. Manually reset the sequence (this is the "truncate" part)
    # with connection.cursor() as cursor:
        # cursor.execute("ALTER SEQUENCE main_commande_id_seq RESTART WITH 1;")

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les devises
    devise_list_one = Devise.objects.all()

    # Récupérer tous les devises
    devise_list_two = Devise.objects.all()

    # Récupérer tous les acheteurs
    acheteur_list = Acheteur.objects.all()

    # Récupérer tous les clients
    client_list = User.objects.filter(
        Q(role__icontains="Client") | Q(role__icontains="client")
    ).order_by("id")

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    # Récupérer tous les villes
    ville_list = Ville.objects.all()

    # Récupérer tous les modeles de rapport
    modele_rapport_list = ModeleRapport.objects.all()

    context = {
        "requests_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "devise_list_one": devise_list_one,
        "devise_list_two": devise_list_two,
        "client_list": client_list,
        "pays_list": pays_list,
        "ville_list": ville_list,
        "acheteur_list": acheteur_list,
        "modele_rapport_list": modele_rapport_list,
    }
    return render(request, "main/root/orders/dash_root_commande.html", context)






@login_required
def dash_root_commande_old(request):
    token = request.GET.get("token")
    if not token:
        pass
    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    
    # Créer 15 commandes factices uniquement si aucune commande n'existe
    # if not Commande.objects.exists():
    # create_fake_commands(15)
    commandes_list = Commande.objects.all()
    print(commandes_list)

    # Récupérer tous les devises
    devise_list_one = Devise.objects.all()
    devise_list_two = Devise.objects.all()

    # Récupérer tous les acheteurs
    acheteur_list = Acheteur.objects.all()

    # Récupérer tous les clients
    client_list = User.objects.filter(
        Q(role__icontains="Client") | Q(role__icontains="client")
    ).order_by("id")

    # Récupérer tous les villes
    ville_list = Ville.objects.all()

    # Récupérer tous les modèles de rapport
    modele_rapport_list = ModeleRapport.objects.all()

    context = {
        "requests_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "devise_list_one": devise_list_one,
        "devise_list_two": devise_list_two,
        "client_list": client_list,
        "ville_list": ville_list,
        "acheteur_list": acheteur_list,
        "modele_rapport_list": modele_rapport_list,
    }
    return render(request, "main/root/orders/dash_root_commande.html", context)






@login_required
def dash_root_manage_commande(request, commande_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    commande = Commande.objects.filter(id=commande_id).first()
    if not commande:
        messages.error(request, "Commande introuvable.")
        return redirect("dash_root_order")

    context = {
        "requests_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_commande": commande_id,
        "commande": commande,
        "status_choices": Commande.STATUS_CHOICES,
        "action_types": SuiviCommande.TYPE_ACTIONS,
        "validateur_list": User.objects.filter(
            Q(role__icontains="Validateur") | Q(role__icontains="Root")
        ).order_by("username"),
    }
    return render(request, "main/root/orders/dash_root_manage_commande.html", context)


@login_required
def dash_root_alerte(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Supprimer d'abord tous
    # alertes = Alerte.objects.all()
    # alertes.delete()

    # documents = DocumentAlerte.objects.all()
    # documents.delete()

    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/root/warning/dash_root_alerte.html", context)


@login_required
def dash_root_add_alerte(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Créer une nouvelle alerte ici
    random_number = random.randint(100, 9999)
    reference = f"ALT{random_number}"

    # Créer une instance de l'alerte
    # alerte = Alerte.objects.create(
    # reference=reference,
    # objet="Nouvelle alerte",  # Vous pouvez définir un objet par défaut ou le laisser vide
    # content="Contenu de l'alerte"  # Vous pouvez définir un contenu par défaut ou le laisser vide
    # )

    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "reference": reference,  # Passer l'alerte au contexte si nécessaire
    }
    return render(request, "main/root/warning/dash_root_add_alerte.html", context)


@login_required
def dash_root_edit_new_alerte(request, reference):

    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Get alerte
    alerte = Alerte.objects.get(reference=reference)

    # Get all documents from this alert
    documents = DocumentAlerte.objects.filter(alerte=alerte)

    # Get context
    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "reference": reference,  # Passer l'alerte au contexte si nécessaire
        "alerte": alerte,  # Passer l'alerte au contexte si nécessaire
        "documents": documents,  # Passer l'alerte au contexte si nécessaire
    }

    return render(request, "main/root/warning/dash_root_edit_new_alerte.html", context)


@login_required
def dash_root_document_alerte(request, reference):

    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Get alerte
    alerte = Alerte.objects.get(reference=reference)

    # Get all documents from this alert
    documents = DocumentAlerte.objects.filter(alerte=alerte)

    # Get context
    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "reference": reference,  # Passer l'alerte au contexte si nécessaire
        "alerte": alerte,  # Passer l'alerte au contexte si nécessaire
        "documents": documents,  # Passer l'alerte au contexte si nécessaire
    }

    return render(
        request, "main/root/warning/dash_root_add_document_alerte.html", context
    )


@login_required
def dash_root_client_alerte(request, reference):

    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Get all clients
    clients = Client.objects.all()

    # Get alerte
    alerte = Alerte.objects.get(reference=reference)

    # Get all documents from this alert
    documents = DocumentAlerte.objects.filter(alerte=alerte)

    # Get context
    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "reference": reference,  # Passer l'alerte au contexte si nécessaire
        "alerte": alerte,  # Passer l'alerte au contexte si nécessaire
        "documents": documents,  # Passer l'alerte au contexte si nécessaire
        "clients": clients,  # Passer l'alerte au contexte si nécessaire
    }

    return render(request, "main/root/warning/dash_root_client_alerte.html", context)


@login_required
def dash_root_edit_alerte(request, alerte_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'alerte
    id_alerte = alerte_id

    # Récupérer tous les documents lies a l'alerte
    # document_list = DocumentAlerte.objects.fliter(alerte__pk=id_alerte)

    # Récupérer tous les clients
    # client_list = User.objects.filter(Q(role__icontains="Client") | Q(role__icontains="client")).order_by('id')

    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_alerte": id_alerte,
        # 'document_list': document_list,
        # 'client_list': client_list,
    }
    return render(request, "main/root/warning/dash_root_edit_alerte.html", context)


@login_required
def dash_root_manage_alerte(request, alerte_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'alerte
    id_alerte = alerte_id

    # Récupérer l'alerte
    alerte = Alerte.objects.filter(id=id_alerte).first()

    # Récupérer tous les documents lies a l'alerte
    document_list = DocumentAlerte.objects.filter(alerte__pk=id_alerte)

    # Récupérer tous les clients
    client_list = User.objects.filter(
        Q(role__icontains="Client") | Q(role__icontains="client")
    ).order_by("id")

    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_alerte": id_alerte,
        "alerte": alerte,
        "document_list": document_list,
        "client_list": client_list,
    }
    return render(request, "main/root/warning/dash_root_manage_alerte.html", context)


@login_required
def dash_root_client(request):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    user = request.user

    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')

    pays_list = Pays.objects.all().only('id', 'nom')

    context = {
        "clients_active": "active",
        "user": user,
        "pays_list": pays_list,
        "refresh": refresh_token,
        "access": access_token,
    }
    return render(request, "main/root/monitoring/dash_root_client.html", context)


@login_required
def dash_root_portefeuille(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "client_list": client_list,
        "acheteur_list": acheteur_list,
    }
    return render(request, "main/root/monitoring/dash_root_portefeuille.html", context)


@login_required
def dash_root_add_portefeuille(request, portefeuille_id=None):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    # Recuperation des frequences
    frequences = Portefeuille.FREQUENCE_CHOICES

    # Récupérer tous les éléments de surveillance
    surveillances = ElementSurveillance.objects.all()

    # Regrouper les éléments par catégorie
    surveillances_by_category = {}
    for surveillance in surveillances:
        if surveillance.categorie not in surveillances_by_category:
            surveillances_by_category[surveillance.categorie] = []
        surveillances_by_category[surveillance.categorie].append(surveillance)

    # Initialiser selected_elements
    selected_elements = []

    # Si vous modifiez un portefeuille existant
    if portefeuille_id:
        portefeuille = Portefeuille.objects.get(id=portefeuille_id)
        selected_elements = portefeuille.elements_surveillance_actifs.values_list(
            "id", flat=True
        )

    # Passer les éléments groupés et les éléments sélectionnés au template
    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "client_list": client_list,
        "acheteur_list": acheteur_list,
        "frequences": frequences,
        "surveillances_by_category": surveillances_by_category,
        "selected_elements": selected_elements,  # Assurez-vous de définir selected_elements
    }
    return render(
        request, "main/root/monitoring/dash_root_add_portefeuille.html", context
    )


@login_required
def dash_root_edit_portefeuille(request, portefeuille_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer le portefeuille à modifier
    try:
        portefeuille = Portefeuille.objects.get(id=portefeuille_id)
    except Portefeuille.DoesNotExist:
        return render(
            request, "main/index.html", {"error": _("Portefeuille non trouvé.")}
        )

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs associés à ce portefeuille
    acheteurs_associes = PortefeuilleClient.objects.filter(
        portefeuille=portefeuille
    ).values_list("acheteur_id", flat=True)

    acheteur_list = Acheteur.objects.all()

    # Recuperation des frequences
    frequences = Portefeuille.FREQUENCE_CHOICES

    # Récupérer tous les éléments de surveillance
    surveillances = ElementSurveillance.objects.all()

    # Regrouper les éléments par catégorie
    surveillances_by_category = {}
    for surveillance in surveillances:
        if surveillance.categorie not in surveillances_by_category:
            surveillances_by_category[surveillance.categorie] = []
        surveillances_by_category[surveillance.categorie].append(surveillance)

    # Initialiser selected_elements
    selected_elements = []

    # Si vous modifiez un portefeuille existant
    if portefeuille_id:
        portefeuille = Portefeuille.objects.get(id=portefeuille_id)
        selected_elements = portefeuille.elements_surveillance_actifs.values_list(
            "id", flat=True
        )

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "portefeuille": portefeuille,  # Données du portefeuille à modifier
        "acheteurs_associes": list(
            acheteurs_associes
        ),  # Liste des IDs des acheteurs associés
        "portefeuille_id": portefeuille_id,
        "client_list": client_list,
        "acheteur_list": acheteur_list,
        "frequences": frequences,
        "surveillances_by_category": surveillances_by_category,
        "selected_elements": selected_elements,  # Assurez-vous de définir selected_elements
    }
    return render(
        request, "main/root/monitoring/dash_root_edit_portefeuille.html", context
    )


@login_required
def dash_root_simulateur_scoring_sb(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "client_list": client_list,
        "acheteur_list": acheteur_list,
    }
    return render(
        request, "main/root/simulateur/dash_root_simulateur_scoring_sb.html", context
    )


@login_required
def dash_root_element_surveillance(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    for element in elements:
        ElementSurveillance.objects.get_or_create(
            code_interne=element[
                "code_interne"
            ],  # Utilisez un champ unique pour vérifier les doublons
            defaults={
                "nom": element["nom"],
                "categorie": element["categorie"],
                "sous_categorie": element["sous_categorie"],
            },
        )

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "client_list": client_list,
        "acheteur_list": acheteur_list,
    }
    return render(
        request, "main/root/surveillance/dash_root_element_surveillance.html", context
    )


@login_required
def dash_root_alerte_log(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les alertes
    alerte_list = AlerteLog.objects.all()

    # Récupérer les portefeuilles
    portefeuille_list = Portefeuille.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    # Récupérer les elements
    element_surveille_list = ElementSurveillance.objects.all()

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "alerte_list": alerte_list,
        "portefeuille_list": portefeuille_list,
        "acheteur_list": acheteur_list,
        "element_surveille_list": element_surveille_list,
    }
    return render(request, "main/root/monitoring/dash_root_alerte_log.html", context)


@login_required
def dash_root_certification_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des certifications d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('certifications'),
        id=acheteur_id
    )

    # Récupérer toutes les certifications de l'acheteur
    certifications_list = Certification.objects.filter(
        acheteur=acheteur
    ).order_by('-date_obtention', '-created_at')

    certifications_avec_date = certifications_list.filter(date_obtention__isnull=False).count()
    certifications_sans_date = certifications_list.filter(date_obtention__isnull=True).count()

    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    coloration_list = CouleurCommentaire.objects.all()

    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'certifications_count': certifications_list.count(),
    }
    
    # Liste des types de certifications pour le filtre
    certification_types = Certification.TYPES
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    certification_types_json = json.dumps(certification_types, default=str)
    
    # Préparer les données pour le template
    certifications_data = []
    for cert in certifications_list:
        certifications_data.append({
            'id': cert.id,
            'type_certification': cert.type_certification,
            'type_certification_display': cert.get_type_certification_display(),
            'nom_certification': cert.nom_certification or '',
            'date_obtention': cert.date_obtention.isoformat() if cert.date_obtention else None,
            'date_obtention_display': cert.date_obtention.strftime('%d/%m/%Y') if cert.date_obtention else 'Non spécifiée',
            'organisme_delivreur': cert.organisme_delivreur or '',
            'description': cert.description or '',
            'created_at': cert.created_at.isoformat() if cert.created_at else None,
            'updated_at': cert.updated_at.isoformat() if cert.updated_at else None,
            'created_at_display': cert.created_at.strftime('%d/%m/%Y %H:%M') if cert.created_at else '',
            'updated_at_display': cert.updated_at.strftime('%d/%m/%Y %H:%M') if cert.updated_at else '',
        })
    
    certifications_json = json.dumps(certifications_data, default=str)
    
    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "certification_types": certification_types,
        "certification_types_json": certification_types_json,
        "certifications": certifications_list,
        "certifications_count": certifications_list.count(),
        "certifications_avec_date": certifications_avec_date,
        "certifications_sans_date": certifications_sans_date,
        "certifications_json": certifications_json or '[]',
        "coloration_list": coloration_list,
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/certification/dash_root_certification_acheteur.html",
        context,
    )


def get_type_badge_class(type_innovation):
    class_map = {
        'nouveau_produit_service': 'badge-nouveau-produit-premium',
        'nouveaux_outils_production': 'badge-outils-production-premium',
        'innovation_produit': 'badge-innovation-produit-premium',
        'innovation_procede': 'badge-innovation-procede-premium',
        'innovation_commercialisation': 'badge-innovation-commercialisation-premium',
        'innovation_organisation': 'badge-innovation-organisation-premium'
    }
    return class_map.get(type_innovation, 'badge-nouveau-produit-premium')



@login_required
def dash_root_innovation_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des innovations et développements d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('innovations'),
        id=acheteur_id
    )

    # Récupérer toutes les innovations de l'acheteur
    innovations_list = InnovationDeveloppement.objects.filter(
        acheteur=acheteur
    ).select_related(
        'created_by',
        'updated_by'
    ).order_by('-created_at')
    
    # Statistiques par type d'innovation
    innovations_stats = innovations_list.values('type_innovation').annotate(
        count=Count('id')
    )
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    coloration_list = CouleurCommentaire.objects.all()

    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Préparer les données des innovations pour le template
    innovations_data = []
    for innovation in innovations_list:
        innovations_data.append({
            'id': innovation.id,
            'type_innovation': innovation.type_innovation,
            'type_innovation_display': innovation.get_type_innovation_display(),
            'titre': innovation.titre or '',
            'description': innovation.description or '',
            'date_debut': innovation.date_debut.isoformat() if innovation.date_debut else None,
            'date_fin': innovation.date_fin.isoformat() if innovation.date_fin else None,
            'created_at': innovation.created_at.isoformat() if innovation.created_at else None,
            'updated_at': innovation.updated_at.isoformat() if innovation.updated_at else None,
            'created_by': {
                'id': innovation.created_by.id if innovation.created_by else None,
                'username': innovation.created_by.username if innovation.created_by else None,
                'full_name': innovation.created_by.get_full_name() if innovation.created_by else None
            } if innovation.created_by else None,
            'updated_by': {
                'id': innovation.updated_by.id if innovation.updated_by else None,
                'username': innovation.updated_by.username if innovation.updated_by else None,
                'full_name': innovation.updated_by.get_full_name() if innovation.updated_by else None
            } if innovation.updated_by else None,
        })
    
    innovations_json = json.dumps(innovations_data, default=str)
    
    # Types d'innovation pour le template
    TYPES_INNOVATION_DISPLAY = dict(InnovationDeveloppement.TYPES_INNOVATION)
    
    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "innovations": innovations_list,
        "innovations_count": innovations_list.count(),
        "innovations_stats": innovations_stats,
        "innovations_json": innovations_json or '[]',
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
        "types_innovation": InnovationDeveloppement.TYPES_INNOVATION,
        "types_innovation_display": TYPES_INNOVATION_DISPLAY,
        "get_type_badge_class": get_type_badge_class,
        "coloration_list": coloration_list,
    }
    
    return render(
        request,
        "main/root/acheteur/innovation/dash_root_innovation_acheteur.html",
        context,
    )


@login_required
def dash_root_strategie_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des stratégies et planifications d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('strategies'),
        id=acheteur_id
    )

    # Récupérer toutes les stratégies de l'acheteur
    strategies_list = StrategiePlanification.objects.filter(
        acheteur=acheteur
    ).select_related(
        'created_by',
        'updated_by'
    ).order_by('-created_at')
    
    # Statistiques par type de stratégie
    strategies_stats = strategies_list.values('type_strategie').annotate(
        count=Count('id')
    )
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    coloration_list = CouleurCommentaire.objects.all()

    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Préparer les données des stratégies pour le template
    strategies_data = []
    for strategie in strategies_list:
        strategies_data.append({
            'id': strategie.id,
            'type_strategie': strategie.type_strategie,
            'type_strategie_display': strategie.get_type_strategie_display(),
            'description': strategie.description or '',
            'date_mise_en_place': strategie.date_mise_en_place.isoformat() if strategie.date_mise_en_place else None,
            'created_at': strategie.created_at.isoformat() if strategie.created_at else None,
            'updated_at': strategie.updated_at.isoformat() if strategie.updated_at else None,
            'created_by': {
                'id': strategie.created_by.id if strategie.created_by else None,
                'username': strategie.created_by.username if strategie.created_by else None,
                'full_name': strategie.created_by.get_full_name() if strategie.created_by else None
            } if strategie.created_by else None,
            'updated_by': {
                'id': strategie.updated_by.id if strategie.updated_by else None,
                'username': strategie.updated_by.username if strategie.updated_by else None,
                'full_name': strategie.updated_by.get_full_name() if strategie.updated_by else None
            } if strategie.updated_by else None,
        })
    
    strategies_json = json.dumps(strategies_data, default=str)
    
    # Types de stratégie pour le template
    TYPES_STRATEGIE_DISPLAY = dict(StrategiePlanification.TYPES_STRATEGIE)
    
    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "strategies": strategies_list,
        "strategies_count": strategies_list.count(),
        "strategies_stats": strategies_stats,
        "strategies_json": strategies_json or '[]',
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
        "types_strategie": StrategiePlanification.TYPES_STRATEGIE,
        "types_strategie_display": TYPES_STRATEGIE_DISPLAY,
        "coloration_list": coloration_list,
    }
    
    return render(
        request,
        "main/root/acheteur/strategie/dash_root_strategie_acheteur.html",
        context,
    )


@login_required
def dash_root_conformite_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des conformités et réglementations d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('conformites'),
        id=acheteur_id
    )

    # Récupérer toutes les conformités de l'acheteur
    conformites_list = ConformiteReglementation.objects.filter(
        acheteur=acheteur
    ).select_related(
        'created_by',
        'updated_by'
    ).order_by('-created_at')
    
    # Statistiques par type et statut
    conformites_stats = conformites_list.aggregate(
        total=Count('id'),
        conformes=Count('id', filter=Q(statut=True)),
        non_conformes=Count('id', filter=Q(statut=False))
    )
    
    # Statistiques par type de conformité
    stats_par_type = conformites_list.values('type_conformite').annotate(
        total=Count('id'),
        conformes=Count('id', filter=Q(statut=True)),
        non_conformes=Count('id', filter=Q(statut=False))
    )
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Préparer les données des conformités pour le template
    conformites_data = []
    for conformite in conformites_list:
        conformites_data.append({
            'id': conformite.id,
            'type_conformite': conformite.type_conformite,
            'type_conformite_display': conformite.get_type_conformite_display(),
            'statut': conformite.statut,
            'statut_display': "Conforme" if conformite.statut else "Non-conforme",
            'details_non_conformite': conformite.details_non_conformite or '',
            'date_verification': conformite.date_verification.isoformat() if conformite.date_verification else None,
            'organisme_controle': conformite.organisme_controle or '',
            'commentaires': conformite.commentaires or '',
            'created_at': conformite.created_at.isoformat() if conformite.created_at else None,
            'updated_at': conformite.updated_at.isoformat() if conformite.updated_at else None,
            'created_by': {
                'id': conformite.created_by.id if conformite.created_by else None,
                'username': conformite.created_by.username if conformite.created_by else None,
                'full_name': conformite.created_by.get_full_name() if conformite.created_by else None
            } if conformite.created_by else None,
            'updated_by': {
                'id': conformite.updated_by.id if conformite.updated_by else None,
                'username': conformite.updated_by.username if conformite.updated_by else None,
                'full_name': conformite.updated_by.get_full_name() if conformite.updated_by else None
            } if conformite.updated_by else None,
        })
    
    conformites_json = json.dumps(conformites_data, default=str)
    
    # Types de conformité pour le template
    TYPES_CONFORMITE_DISPLAY = dict(ConformiteReglementation.TYPES_CONFORMITE)
    
    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "conformites": conformites_list,
        "conformites_count": conformites_list.count(),
        "conformites_stats": conformites_stats,
        "stats_par_type": stats_par_type,
        "conformites_json": conformites_json or '[]',
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
        "types_conformite": ConformiteReglementation.TYPES_CONFORMITE,
        "types_conformite_display": TYPES_CONFORMITE_DISPLAY,
    }
    
    return render(
        request,
        "main/root/acheteur/conformite/dash_root_conformite_acheteur.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_bilan_actif_bancaire_0(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer l'acheteur actuel pour l'afficher
    acheteur_actuel = Acheteur.objects.get(id=acheteur_id)

    # Récupérer TOUS les acheteurs pour la liste déroulante
    tous_les_acheteurs = Acheteur.objects.all()

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les actifs de l'acheteur
    actifs = Assets.objects.filter(acheteur_id=acheteur_id)

    # Récupérer tous les passifs de l'acheteur
    passifs = Liabilities.objects.filter(acheteur_id=acheteur_id)

    # Récupérer tous les depenses de l'acheteur
    depenses = Expenses.objects.filter(acheteur_id=acheteur_id)

    # Récupérer tous les produits de l'acheteur
    produits = Products.objects.filter(acheteur_id=acheteur_id)

    # Récupérer tous les hors bilans de l'acheteur
    hors_bilans = OffBalanceSheet.objects.filter(acheteur_id=acheteur_id)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "acheteur": acheteur_actuel,  # Ajouter l'objet acheteur actuel
        "acheteurs": tous_les_acheteurs,  # <--- AJOUTER CETTE LIGNE
        "annee_list": annee_list,
        "actifs": actifs,
        "passifs": passifs,
        "depenses": depenses,
        "produits": produits,
        "hors_bilans": hors_bilans,
    }
    return render(
        request,
        "main/root/acheteur/bilans/bancaire/dash_root_manage_acheteur_bilan_actif_bancaire.html",
        context,
    )

    # En haut de votre fichier views.py, ajoutez cet import


@login_required
def dash_root_manage_acheteur_bilan_actif_bancaire(request, acheteur_id):
    """
    Vue pour gérer les bilans (Actifs, Passifs, Dépenses, Produits) d'un acheteur,
    avec pagination pour chaque section.
    """
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user
    refresh = RefreshToken.for_user(user)
    id_acheteur = acheteur_id

    try:
        acheteur_actuel = Acheteur.objects.get(id=id_acheteur)
    except Acheteur.DoesNotExist:
        return render(
            request, "main/error_page.html", {"error": _("Acheteur non trouvé.")}
        )

    tous_les_acheteurs = Acheteur.objects.all()
    annee_list = Annee.objects.all()

    # --- PAGINATION DES ACTIFS ---
    actifs_list = Assets.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    actifs_paginator = Paginator(actifs_list, 10)
    page_actifs = request.GET.get("page_actifs")
    actifs_page_obj = actifs_paginator.get_page(page_actifs)

    # --- PAGINATION DES PASSIFS ---
    passifs_list = Liabilities.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    passifs_paginator = Paginator(passifs_list, 10)
    page_passifs = request.GET.get("page_passifs")
    passifs_page_obj = passifs_paginator.get_page(page_passifs)

    # --- PAGINATION DES DÉPENSES ---
    depenses_list = Expenses.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    depenses_paginator = Paginator(depenses_list, 10)
    page_depenses = request.GET.get("page_depenses")
    depenses_page_obj = depenses_paginator.get_page(page_depenses)

    # --- NOUVEAU : PAGINATION DES PRODUITS ---
    produits_list = Products.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    produits_paginator = Paginator(produits_list, 10)
    page_produits = request.GET.get("page_produits")
    produits_page_obj = produits_paginator.get_page(page_produits)

    # --- NOUVEAU : PAGINATION DU HORS BILAN ---
    hors_bilans_list = OffBalanceSheet.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    hors_bilans_paginator = Paginator(hors_bilans_list, 10)
    page_hors_bilans = request.GET.get("page_hors_bilans")
    hors_bilans_page_obj = hors_bilans_paginator.get_page(page_hors_bilans)

    # MODIFIÉ : Mise à jour du contexte pour inclure les produits paginés
    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "acheteur": acheteur_actuel,
        "acheteurs": tous_les_acheteurs,
        "annee_list": annee_list,
        "annee_list_data": json.dumps(list(Annee.objects.values("id", "annee"))),
        "type_bilan_choices_json": json.dumps(list(TYPE_BILAN_CHOICES)),
        "semestre_choices_json": json.dumps(list(SEMESTRE_CHOICES)),
        # Objets de page paginés pour le template
        "actifs_page": actifs_page_obj,
        "passifs_page": passifs_page_obj,
        "depenses_page": depenses_page_obj,
        "produits_page": produits_page_obj,
        "hors_bilans_page": hors_bilans_page_obj,  # <- NOUVEAU CONTEXTE
    }

    return render(
        request,
        "main/root/acheteur/bilans/bancaire/dash_root_manage_acheteur_bilan_actif_bancaire.html",  # Nom de template suggéré
        context,
    )


@login_required
def dash_root_manage_acheteur_bilan_irfs_cobac(request, acheteur_id):
    """
    Vue pour gérer les états financiers IFRS (Actif, Passif, Résultat, Ratios)
    d'un acheteur, avec pagination pour chaque section.
    """
    token = request.GET.get("token")
    if not token:
        # Idéalement, rediriger vers une page de connexion ou afficher une erreur claire.
        pass

    user = request.user
    refresh = RefreshToken.for_user(user)

    try:
        acheteur_actuel = Acheteur.objects.get(id=acheteur_id)
    except Acheteur.DoesNotExist:
        return render(
            request, "main/error_page.html", {"error": _("Acheteur non trouvé.")}
        )

    # Données communes pour les formulaires
    tous_les_acheteurs = Acheteur.objects.all()
    annee_list = Annee.objects.all()

    # --- PAGINATION ACTIF IFRS ---
    actifs_list = ActifIFRS.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee"
    )
    actifs_paginator = Paginator(actifs_list, 10)  # 10 par page
    page_actifs = request.GET.get("page_actifs")
    actifs_page_obj = actifs_paginator.get_page(page_actifs)

    # --- PAGINATION PASSIF IFRS ---
    passifs_list = PassifIFRS.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee"
    )
    passifs_paginator = Paginator(passifs_list, 10)
    page_passifs = request.GET.get("page_passifs")
    passifs_page_obj = passifs_paginator.get_page(page_passifs)

    # --- PAGINATION COMPTE DE RÉSULTAT IFRS ---
    resultats_list = ResultatIFRS.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee"
    )
    resultats_paginator = Paginator(resultats_list, 10)
    page_resultats = request.GET.get("page_resultats")
    resultats_page_obj = resultats_paginator.get_page(page_resultats)

    # --- PAGINATION RATIOS IFRS ---
    ratios_list = RatiosIFRS.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee"
    )  # Pas de semestre pour les ratios a priori
    ratios_paginator = Paginator(ratios_list, 10)
    page_ratios = request.GET.get("page_ratios")
    ratios_page_obj = ratios_paginator.get_page(page_ratios)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": acheteur_id,
        "acheteur": acheteur_actuel,
        "acheteurs": tous_les_acheteurs,
        "annee_list": annee_list,
        "annee_list_data": json.dumps(list(Annee.objects.values("id", "annee"))),
        "type_bilan_choices_json": json.dumps(list(TYPE_BILAN_CHOICES)),
        "semestre_choices_json": json.dumps(list(SEMESTRE_CHOICES)),
        # Objets de page paginés pour le template
        "actifs_ifrs_page": actifs_page_obj,
        "passifs_ifrs_page": passifs_page_obj,
        "resultats_ifrs_page": resultats_page_obj,
        "ratios_ifrs_page": ratios_page_obj,
    }

    return render(
        request,
        "main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_bilan_irfs_cobac.html",
        context,
    )
    
    




@login_required
def dash_root_manage_acheteur_actif_ifrs_one(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Récupérer toutes les années
    annee_list = Annee.objects.all()
    
    # Options pour le type de bilan
    type_bilan_choices = [
        {'value': 'annuel', 'label': 'Bilan annuel'},
        {'value': 'semestriel', 'label': 'Bilan semestriel'},
    ]
    
    # Options pour les semestres
    semestre_choices = [
        {'value': 1, 'label': '1er semestre (Janvier - Juin)'},
        {'value': 2, 'label': '2e semestre (Juillet - Décembre)'},
    ]
    
    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": acheteur_id,
        "annee_list": annee_list,
        "type_bilan_choices": json.dumps(type_bilan_choices),
        "semestre_choices": json.dumps(semestre_choices),
    }
    
    return render(
        request,
        "main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_actif_ifrs_one.html",
        context,
    )
    
    


@login_required
def dash_root_manage_acheteur_passif_ifrs_one(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Récupérer toutes les années
    annee_list = Annee.objects.all()
    
    # Options pour le type de bilan
    type_bilan_choices = [
        {'value': 'annuel', 'label': 'Bilan annuel'},
        {'value': 'semestriel', 'label': 'Bilan semestriel'},
    ]
    
    # Options pour les semestres
    semestre_choices = [
        {'value': 1, 'label': '1er semestre (Janvier - Juin)'},
        {'value': 2, 'label': '2e semestre (Juillet - Décembre)'},
    ]
    
    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": acheteur_id,
        "annee_list": annee_list,
        "type_bilan_choices": json.dumps(type_bilan_choices),
        "semestre_choices": json.dumps(semestre_choices),
    }
    
    return render(
        request,
        "main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_passif_ifrs_one.html",
        context,
    )
    




@login_required
def dash_root_manage_acheteur_resultat_ifrs_one(request, acheteur_id):
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('banquier_set'),
        id=acheteur_id
    )
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Récupérer toutes les années
    annee_list = Annee.objects.all()
    
    # Options pour le type de bilan
    type_bilan_choices = [
        {'value': 'annuel', 'label': 'Bilan annuel'},
        {'value': 'semestriel', 'label': 'Bilan semestriel'},
    ]
    
    # Options pour les semestres
    semestre_choices = [
        {'value': 1, 'label': '1er semestre (Janvier - Juin)'},
        {'value': 2, 'label': '2e semestre (Juillet - Décembre)'},
    ]
    
    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "acheteur": acheteur,
        "acheteur_json": acheteur_json,
        "id_acheteur": acheteur_id,
        "annee_list": annee_list,
        "type_bilan_choices": json.dumps(type_bilan_choices),
        "semestre_choices": json.dumps(semestre_choices),
    }
    
    return render(
        request,
        "main/root/acheteur/bilans/irfs/dash_root_manage_acheteur_resultat_ifrs_one.html",
        context,
    )
    
    
# Dans votre fichier views.py
 
    
    
# Dans votre fichier views.py

import json
from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.tokens import RefreshToken

from main.models import ActifS, PassifS, ResultatS, Annee, Acheteur
from main.models import TYPE_BILAN_CHOICES, SEMESTRE_CHOICES

@login_required
def dash_root_manage_acheteur_bilan_syscohada(request, acheteur_id):
    """
    Vue pour gérer les bilans (Actifs, Passifs, Résultats) d'un acheteur,
    avec pagination pour chaque section, selon le plan SYSCOHADA.
    """
    user = request.user
    refresh = RefreshToken.for_user(user)
    id_acheteur = acheteur_id

    try:
        acheteur_actuel = Acheteur.objects.get(id=id_acheteur)
    except Acheteur.DoesNotExist:
        return render(
            request, "main/error_page.html", {"error": "Acheteur non trouvé."}
        )
    
    tous_les_acheteurs = Acheteur.objects.all()
    annee_list = Annee.objects.all()

    # --- PAGINATION DES ACTIFS SYSCOHADA ---
    actifs_s_list = ActifS.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")
    actifs_s_paginator = Paginator(actifs_s_list, 10)
    page_actifs_s = request.GET.get("page_actifs")
    actifs_s_page_obj = actifs_s_paginator.get_page(page_actifs_s)

    # --- PAGINATION DES PASSIFS SYSCOHADA ---
    passifs_s_list = PassifS.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")
    passifs_s_paginator = Paginator(passifs_s_list, 10)
    page_passifs_s = request.GET.get("page_passifs")
    passifs_s_page_obj = passifs_s_paginator.get_page(page_passifs_s)

    # --- PAGINATION DES COMPTES DE RÉSULTATS SYSCOHADA ---
    resultats_s_list = ResultatS.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")
    resultats_s_paginator = Paginator(resultats_s_list, 10)
    page_resultats_s = request.GET.get("page_resultats")
    resultats_s_page_obj = resultats_s_paginator.get_page(page_resultats_s)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "acheteur": acheteur_actuel,
        "acheteurs": tous_les_acheteurs,
        "annee_list": annee_list,
        "annee_list_data": json.dumps(list(Annee.objects.values("id", "annee"))),
        "type_bilan_choices_json": json.dumps(list(TYPE_BILAN_CHOICES)),
        "semestre_choices_json": json.dumps(list(SEMESTRE_CHOICES)),
        # Objets de page paginés pour le template
        "actifs_s_page": actifs_s_page_obj,
        "passifs_s_page": passifs_s_page_obj,
        "resultats_s_page": resultats_s_page_obj,
    }

    return render(
        request,
        "main/root/acheteur/bilans/syscohada/dash_root_manage_acheteur_bilan_syscohada.html",
        context,
    )    
    
    
    
    
# Dans votre fichier views.py

import json
from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.tokens import RefreshToken

from main.models import ActifA, PassifA, ResultatA, Annee, Acheteur
from main.models import TYPE_BILAN_CHOICES, SEMESTRE_CHOICES

@login_required
def dash_root_manage_acheteur_bilan_anglais(request, acheteur_id):
    """
    Vue pour gérer les bilans (Actifs, Passifs, Résultats) d'un acheteur,
    avec pagination pour chaque section, selon le plan comptable anglais.
    """
    user = request.user
    refresh = RefreshToken.for_user(user)
    id_acheteur = acheteur_id

    try:
        acheteur_actuel = Acheteur.objects.get(id=id_acheteur)
    except Acheteur.DoesNotExist:
        return render(
            request, "main/error_page.html", {"error": "Acheteur non trouvé."}
        )
    
    tous_les_acheteurs = Acheteur.objects.all()
    annee_list = Annee.objects.all()

    # --- PAGINATION DES ACTIFS ANGLAIS ---
    actifs_a_list = ActifA.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")
    actifs_a_paginator = Paginator(actifs_a_list, 10)
    page_actifs_a = request.GET.get("page_actifs")
    actifs_a_page_obj = actifs_a_paginator.get_page(page_actifs_a)

    # --- PAGINATION DES PASSIFS ANGLAIS ---
    passifs_a_list = PassifA.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")
    passifs_a_paginator = Paginator(passifs_a_list, 10)
    page_passifs_a = request.GET.get("page_passifs")
    passifs_a_page_obj = passifs_a_paginator.get_page(page_passifs_a)

    # --- PAGINATION DES COMPTES DE RÉSULTATS ANGLAIS ---
    resultats_a_list = ResultatA.objects.filter(acheteur_id=acheteur_id).order_by("-annee__annee")
    resultats_a_paginator = Paginator(resultats_a_list, 10)
    page_resultats_a = request.GET.get("page_resultats")
    resultats_a_page_obj = resultats_a_paginator.get_page(page_resultats_a)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "acheteur": acheteur_actuel,
        "acheteurs": tous_les_acheteurs,
        "annee_list": annee_list,
        "annee_list_data": json.dumps(list(Annee.objects.values("id", "annee"))),
        "type_bilan_choices_json": json.dumps(list(TYPE_BILAN_CHOICES)),
        "semestre_choices_json": json.dumps(list(SEMESTRE_CHOICES)),
        # Objets de page paginés pour le template
        "actifs_a_page": actifs_a_page_obj,
        "passifs_a_page": passifs_a_page_obj,
        "resultats_a_page": resultats_a_page_obj,
    }

    return render(
        request,
        "main/root/acheteur/bilans/anglais/dash_root_manage_acheteur_bilan_anglais.html",
        context,
    )

    


@login_required
def dash_root_manage_acheteur_portable(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    try:
        acheteur_actuel = Acheteur.objects.get(id=acheteur_id)
    except Acheteur.DoesNotExist:
        return render(
            request, "main/error_page.html", {"error": _("Acheteur non trouvé.")}
        )

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "acheteur": acheteur_actuel,
    }
    return render(
        request,
        "main/root/acheteur/portable/dash_root_manage_acheteur_portable.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_telephone(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    try:
        acheteur_actuel = Acheteur.objects.get(id=acheteur_id)
    except Acheteur.DoesNotExist:
        return render(
            request, "main/error_page.html", {"error": _("Acheteur non trouvé.")}
        )

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "acheteur": acheteur_actuel,
    }
    return render(
        request,
        "main/root/acheteur/telephone/dash_root_manage_acheteur_telephone.html",
        context,
    )


@login_required
def dash_root_manage_acheteur_swot(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    try:
        acheteur_actuel = Acheteur.objects.get(id=acheteur_id)
    except Acheteur.DoesNotExist:
        return render(
            request, "main/error_page.html", {"error": _("Acheteur non trouvé.")}
        )

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "acheteur": acheteur_actuel,
    }
    return render(
        request,
        "main/root/acheteur/swot/dash_root_manage_acheteur_swot.html",
        context,
    )
    
    
    
    
    
    
@login_required
def dash_root_manage_marque_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des marques d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('marques'),
        id=acheteur_id
    )

    # Récupérer tous les enregistrements de marques de l'acheteur
    marques_list = Marque.objects.filter(
        acheteur=acheteur
    ).order_by('-created_at')
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    coloration_list = CouleurCommentaire.objects.all()

    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'marques_count': marques_list.count(),
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Préparer les données pour le template
    marques_data = []
    for marque in marques_list:
        # Limiter l'affichage du texte pour l'aperçu
        marques_preview = marque.marques[:150] + "..." if marque.marques and len(marque.marques) > 150 else marque.marques or ''
        
        marques_data.append({
            'id': marque.id,
            'marques': marque.marques or '',
            'marques_preview': marques_preview,
            'has_marques': bool(marque.marques and marque.marques.strip()),
            'created_at': marque.created_at.isoformat() if marque.created_at else None,
            'updated_at': marque.updated_at.isoformat() if marque.updated_at else None,
            'created_at_display': marque.created_at.strftime('%d/%m/%Y %H:%M') if marque.created_at else '',
            'updated_at_display': marque.updated_at.strftime('%d/%m/%Y %H:%M') if marque.updated_at else '',
        })
    
    marques_json = json.dumps(marques_data, default=str)
    
    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "marques": marques_list,
        "marques_count": marques_list.count(),
        "marques_json": marques_json or '[]',
        "coloration_list": coloration_list,
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/marque/dash_root_marque_acheteur.html",
        context,
    )
    
    
    


@login_required
def dash_root_manage_produit_service_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des produits et services d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('produits_services'),
        id=acheteur_id
    )

    # Récupérer tous les enregistrements de produits et services de l'acheteur
    produits_services_list = ProduitService.objects.filter(
        acheteur=acheteur
    ).order_by('-created_at')
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    coloration_list = CouleurCommentaire.objects.all()

    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'produits_services_count': produits_services_list.count(),
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Préparer les données pour le template
    produits_services_data = []
    for ps in produits_services_list:
        # Limiter l'affichage des textes pour l'aperçu
        produits_preview = ps.produits[:100] + "..." if ps.produits and len(ps.produits) > 100 else ps.produits or ''
        services_preview = ps.services[:100] + "..." if ps.services and len(ps.services) > 100 else ps.services or ''
        
        produits_services_data.append({
            'id': ps.id,
            'produits': ps.produits or '',
            'services': ps.services or '',
            'produits_preview': produits_preview,
            'services_preview': services_preview,
            'has_produits': bool(ps.produits and ps.produits.strip()),
            'has_services': bool(ps.services and ps.services.strip()),
            'created_at': ps.created_at.isoformat() if ps.created_at else None,
            'updated_at': ps.updated_at.isoformat() if ps.updated_at else None,
            'created_at_display': ps.created_at.strftime('%d/%m/%Y %H:%M') if ps.created_at else '',
            'updated_at_display': ps.updated_at.strftime('%d/%m/%Y %H:%M') if ps.updated_at else '',
        })
    
    produits_services_json = json.dumps(produits_services_data, default=str)
    
    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "produits_services": produits_services_list,
        "produits_services_count": produits_services_list.count(),
        "produits_services_json": produits_services_json or '[]',
        "coloration_list": coloration_list,
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/produit_service/dash_root_produit_service_acheteur.html",
        context,
    )
    
    
    


@login_required
def dash_root_manage_cotisation_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des cotisations sociales d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('cotisations'),
        id=acheteur_id
    )

    # Récupérer toutes les cotisations sociales de l'acheteur
    cotisations_list = Cotisation.objects.filter(
        acheteur=acheteur
    ).order_by('-created_at')
    cotisations_avec_date = cotisations_list.filter(date_affiliation__isnull=False).count()
    cotisations_sans_date = cotisations_list.filter(date_affiliation__isnull=True).count()

    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    coloration_list = CouleurCommentaire.objects.all()

    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'cotisations_count': cotisations_list.count(),
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Préparer les données pour le template
    cotisations_data = []
    for cotisation in cotisations_list:
        cotisations_data.append({
            'id': cotisation.id,
            'numero': cotisation.numero or '',
            'date_affiliation': cotisation.date_affiliation.isoformat() if cotisation.date_affiliation else None,
            'date_affiliation_display': cotisation.date_affiliation.strftime('%d/%m/%Y') if cotisation.date_affiliation else 'Non spécifiée',
            'created_at': cotisation.created_at.isoformat() if cotisation.created_at else None,
            'updated_at': cotisation.updated_at.isoformat() if cotisation.updated_at else None,
            'created_at_display': cotisation.created_at.strftime('%d/%m/%Y %H:%M') if cotisation.created_at else '',
            'updated_at_display': cotisation.updated_at.strftime('%d/%m/%Y %H:%M') if cotisation.updated_at else '',
        })
    
    cotisations_json = json.dumps(cotisations_data, default=str)
    
    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "cotisations": cotisations_list,
        "cotisations_count": cotisations_list.count(),
        "cotisations_avec_date": cotisations_avec_date,
        "cotisations_sans_date": cotisations_sans_date,
        "cotisations_json": cotisations_json or '[]',
        "coloration_list": coloration_list,
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/cotisation/dash_root_cotisation_acheteur.html",
        context,
    )
    
    

@login_required
def dash_root_modele_age_societe(request):
    token = request.GET.get("token")
    if not token:
        pass
    user = request.user
    refresh = RefreshToken.for_user(user)
    context = {
        "modele_age_societe_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/root/modele/dash_root_modele_age_societe.html", context
    )


    
    
    


@login_required
def dash_root_manage_swot_acheteur(request, acheteur_id):
    """
    Vue pour la gestion de l'analyse SWOT d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('swot'),
        id=acheteur_id
    )

    # Récupérer l'analyse SWOT de l'acheteur
    swot_analysis = Swot.objects.filter(acheteur=acheteur).first()
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    coloration_list = CouleurCommentaire.objects.all()

    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'forme_juridique': acheteur.forme_juridique.libelle if acheteur.forme_juridique else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Préparer les données SWOT pour le template
    swot_data = None
    if swot_analysis:
        swot_data = {
            'id': swot_analysis.id,
            'forces': swot_analysis.forces or '',
            'faiblesses': swot_analysis.faiblesses or '',
            'opportunites': swot_analysis.opportunites or '',
            'menaces': swot_analysis.menaces or '',
            'created_at': swot_analysis.created_at,
            'updated_at': swot_analysis.updated_at,
        }
    
    # Compter le nombre d'éléments dans chaque catégorie
    forces_count = 0
    faiblesses_count = 0
    opportunites_count = 0
    menaces_count = 0
    
    if swot_analysis:
        forces_count = len([f for f in (swot_analysis.forces or '').split('\n') if f.strip()])
        faiblesses_count = len([f for f in (swot_analysis.faiblesses or '').split('\n') if f.strip()])
        opportunites_count = len([o for o in (swot_analysis.opportunites or '').split('\n') if o.strip()])
        menaces_count = len([m for m in (swot_analysis.menaces or '').split('\n') if m.strip()])
    
    total_elements = forces_count + faiblesses_count + opportunites_count + menaces_count
    
    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "swot": swot_analysis,
        "swot_data": swot_data,
        "swot_exists": swot_analysis is not None,
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
        "forces_count": forces_count,
        "faiblesses_count": faiblesses_count,
        "opportunites_count": opportunites_count,
        "menaces_count": menaces_count,
        "total_elements": total_elements,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/root/acheteur/swot/dash_root_swot_acheteur.html",
        context,
    )
    
    
    
    
    


@login_required
def dash_root_manage_registre_commerce_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des registres de commerce d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('registre_commerce'),
        id=acheteur_id
    )

    # Récupérer tous les registres de commerce de l'acheteur
    registres_list = RegistreCommerce.objects.filter(
        acheteur=acheteur
    ).order_by('-created_at')
    registres_actifs_count = registres_list.filter(est_actif=True).count()
    registres_archives_count = registres_list.filter(est_actif=False).count()

    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    coloration_list = CouleurCommentaire.objects.all()

    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'registres_count': registres_list.count(),
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Préparer les données pour le template
    registres_data = []
    for registre in registres_list:
        registres_data.append({
            'id': registre.id,
            'numero': registre.numero or '',
            'est_actif': registre.est_actif,
            'date_inscription': registre.date_inscription.isoformat() if registre.date_inscription else None,
            'date_inscription_display': registre.date_inscription.strftime('%d/%m/%Y') if registre.date_inscription else 'Non spécifiée',
            'created_at': registre.created_at.isoformat() if registre.created_at else None,
            'updated_at': registre.updated_at.isoformat() if registre.updated_at else None,
            'created_at_display': registre.created_at.strftime('%d/%m/%Y %H:%M') if registre.created_at else '',
            'updated_at_display': registre.updated_at.strftime('%d/%m/%Y %H:%M') if registre.updated_at else '',
        })
    
    registres_json = json.dumps(registres_data, default=str)
    
    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "registres": registres_list,
        "registres_count": registres_list.count(),
        "registres_actifs": registres_actifs_count,
        "registres_archives": registres_archives_count,
        "registres_json": registres_json or '[]',
        "coloration_list": coloration_list,
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/registre_commerce/dash_root_registre_commerce_acheteur.html",
        context,
    )


@login_required
def dash_root_manage_identifiant_fiscal_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des identifiants fiscaux d'un acheteur
    """
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())

    try:
        identifiant = IdentifiantFiscal.objects.get(acheteur=acheteur)
    except IdentifiantFiscal.DoesNotExist:
        identifiant = None

    identifiant_data = None
    if identifiant:
        identifiant_data = {
            'id': identifiant.id,
            'nif': identifiant.nif or '',
            'numero_tva': identifiant.numero_tva or '',
            'numero_statistique': identifiant.numero_statistique or '',
            'numero_cnss_employeur': identifiant.numero_cnss_employeur or '',
            'numero_national_unique': identifiant.numero_national_unique or '',
            'commentaire': identifiant.commentaire or '',
            'updated_at_display': identifiant.updated_at.strftime('%d/%m/%Y %H:%M') if identifiant.updated_at else '',
        }

    identifiant_json = json.dumps(identifiant_data, default=str)

    champs_renseignes = identifiant.champs_renseignes() if identifiant else 0

    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "identifiant": identifiant,
        "identifiant_json": identifiant_json,
        "champs_renseignes": champs_renseignes,
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/identifiant_fiscal/dash_root_identifiant_fiscal_acheteur.html",
        context,
    )


@login_required
def dash_root_manage_procedure_collective_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des procédures collectives d'un acheteur
    """

    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('procedures_collectives'),
        id=acheteur_id
    )

    # Récupérer toutes les procédures collectives de l'acheteur
    procedures_list = ProcedureCollective.objects.filter(
        acheteur=acheteur
    ).order_by('-date_ouverture', '-created_at')
    
    # Calculer les statistiques
    procedures_actives = procedures_list.filter(date_cloture__isnull=True).count()
    procedures_cloturees = procedures_list.filter(date_cloture__isnull=False).count()
    
    # Types de procédures disponibles (vous pouvez les définir dans settings ou models)
    TYPES_PROCEDURES = [
        'Redressement judiciaire',
        'Liquidation judiciaire',
        'Sauvegarde',
        'Conciliation',
        'Procédure de rétablissement professionnel',
        'Autre'
    ]
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    coloration_list = CouleurCommentaire.objects.all()

    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Préparer les données pour le template
    procedures_with_data = []
    for procedure in procedures_list:
        # Déterminer le statut
        if procedure.date_cloture:
            statut = 'Clôturée'
            statut_class = 'badge bg-success'
        else:
            statut = 'En cours'
            statut_class = 'badge bg-warning'
        
        # Calculer la durée (si date d'ouverture disponible)
        duree = None
        if procedure.date_ouverture:
            if procedure.date_cloture:
                duree_jours = (procedure.date_cloture - procedure.date_ouverture).days
                duree = f"{duree_jours} jours"
            else:
                duree_jours = (datetime.date.today() - procedure.date_ouverture).days
                duree = f"{duree_jours} jours (en cours)"
        
        # Obtenir l'icône selon le type de procédure
        icon_map = {
            'Redressement judiciaire': 'fas fa-balance-scale',
            'Liquidation judiciaire': 'fas fa-gavel',
            'Sauvegarde': 'fas fa-shield-alt',
            'Conciliation': 'fas fa-handshake',
            'Procédure de rétablissement professionnel': 'fas fa-redo',
            'Autre': 'fas fa-file-contract'
        }
        icon_class = icon_map.get(procedure.type_procedure, 'fas fa-file-contract')
        
        procedures_with_data.append({
            'procedure_obj': procedure,
            'id': procedure.id,
            'type_procedure': procedure.type_procedure or 'Non spécifié',
            'date_ouverture': procedure.date_ouverture,
            'date_cloture': procedure.date_cloture,
            'description': procedure.description or '',
            'statut': statut,
            'statut_class': statut_class,
            'duree': duree,
            'icon_class': icon_class,
            'created_at': procedure.created_at,
            'updated_at': procedure.updated_at
        })

    # Préparer les données JSON pour JavaScript
    procedures_data = []
    for procedure in procedures_with_data:
        procedures_data.append({
            'id': procedure['procedure_obj'].id,
            'type_procedure': procedure['type_procedure'],
            'date_ouverture': procedure['date_ouverture'].isoformat() if procedure['date_ouverture'] else None,
            'date_cloture': procedure['date_cloture'].isoformat() if procedure['date_cloture'] else None,
            'description': procedure['description'],
            'statut': procedure['statut'],
            'duree': procedure['duree'],
            'created_at': procedure['created_at'].isoformat() if procedure['created_at'] else None,
            'updated_at': procedure['updated_at'].isoformat() if procedure['updated_at'] else None,
        })
    
    procedures_json = json.dumps(procedures_data, default=str)
    
    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "procedures": procedures_list,
        "procedures_count": procedures_list.count(),
        "procedures_data": procedures_with_data,
        "procedures_actives": procedures_actives,
        "procedures_cloturees": procedures_cloturees,
        "procedures_json": procedures_json or '[]',
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
        "types_procedures": TYPES_PROCEDURES,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/root/acheteur/procedure_collective/dash_root_procedure_collective_acheteur.html",
        context,
    )
    
    
    
    


@login_required
def dash_root_manage_document_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des documents d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related('documents'),
        id=acheteur_id
    )

    # Récupérer tous les documents de l'acheteur
    documents_list = Document.objects.filter(
        acheteur=acheteur
    ).order_by('-created_at')
    
    # Calculer la taille totale des fichiers
    taille_totale_bytes = 0
    for document in documents_list:
        if document.fichier:
            try:
                if hasattr(document.fichier, 'size'):
                    taille_totale_bytes += document.fichier.size
            except (ValueError, TypeError, OSError):
                continue
    
    # Convertir en MB
    taille_totale_mb = taille_totale_bytes / (1024 * 1024) if taille_totale_bytes > 0 else 0
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Préparer les données pour le template
    documents_with_data = []
    for document in documents_list:
        # Obtenir l'extension du fichier
        extension = None
        if document.fichier and document.fichier.name:
            try:
                extension = document.fichier.name.split('.')[-1].lower()
            except:
                extension = 'unknown'
        
        # Obtenir la taille du fichier
        taille = None
        if document.fichier and hasattr(document.fichier, 'size'):
            taille_bytes = document.fichier.size
            if taille_bytes < 1024:
                taille = f"{taille_bytes} B"
            elif taille_bytes < 1024 * 1024:
                taille = f"{taille_bytes/1024:.1f} KB"
            else:
                taille = f"{taille_bytes/(1024*1024):.1f} MB"
        
        # Obtenir l'icône basée sur l'extension
        icon_class = get_file_icon(extension)
        
        documents_with_data.append({
            'document_obj': document,
            'id': document.id,
            'titre': document.titre or 'Sans titre',
            'description': document.description or '',
            'fichier_url': document.fichier.url if document.fichier else '',
            'fichier_nom': document.fichier.name if document.fichier else '',
            'extension': extension,
            'icon_class': icon_class,
            'taille': taille,
            'created_at': document.created_at,
            'updated_at': document.updated_at
        })

    # Préparer les données JSON pour JavaScript
    documents_data = []
    for document in documents_with_data:
        documents_data.append({
            'id': document['document_obj'].id,
            'titre': document['titre'],
            'description': document['description'],
            'fichier_url': document['fichier_url'],
            'fichier_nom': document['fichier_nom'],
            'extension': document['extension'],
            'icon_class': document['icon_class'],
            'taille': document['taille'],
            'created_at': document['created_at'].isoformat() if document['created_at'] else None,
            'updated_at': document['updated_at'].isoformat() if document['updated_at'] else None,
        })
    
    documents_json = json.dumps(documents_data, default=str)
    
    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "documents": documents_list,
        "documents_count": documents_list.count(),
        "documents_data": documents_with_data,
        "taille_totale_mb": round(taille_totale_mb, 2),
        "documents_json": documents_json or '[]',
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
        "max_file_size": 10 * 1024 * 1024,  # 10MB en bytes
        "allowed_extensions": "'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png'"
    }
    return render(
        request,
        "main/root/acheteur/document/dash_root_document_acheteur.html",
        context,
    )

def get_file_icon(extension):
    """
    Retourne la classe FontAwesome appropriée pour l'extension de fichier
    """
    icon_map = {
        'pdf': 'fas fa-file-pdf',
        'doc': 'fas fa-file-word',
        'docx': 'fas fa-file-word',
        'xls': 'fas fa-file-excel',
        'xlsx': 'fas fa-file-excel',
        'jpg': 'fas fa-file-image',
        'jpeg': 'fas fa-file-image',
        'png': 'fas fa-file-image',
        'txt': 'fas fa-file-alt',
        'zip': 'fas fa-file-archive',
        'rar': 'fas fa-file-archive',
        'ppt': 'fas fa-file-powerpoint',
        'pptx': 'fas fa-file-powerpoint',
        'csv': 'fas fa-file-csv',
    }
    return icon_map.get(extension, 'fas fa-file')







# views.py

@login_required
def dash_root_manage_adresse_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des adresses d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer les adresses de l'acheteur avec pagination
    adresses_list = AdresseAcheteur.objects.filter(
        acheteur=acheteur
    ).select_related('created_by', 'updated_by').order_by('-created_at')
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
        'ville': acheteur.ville.nom if acheteur.ville else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Préparer les données des adresses pour le template
    adresses_data = []
    for adresse in adresses_list:
        adresses_data.append({
            'id': adresse.id,
            'adresse': adresse.adresse or '',
            'rue': adresse.rue or '',
            'numero_porte': adresse.numero_porte or '',
            'bp': adresse.bp or '',
            'nom': adresse.nom or '',
            'created_at': adresse.created_at.isoformat() if adresse.created_at else None,
            'updated_at': adresse.updated_at.isoformat() if adresse.updated_at else None,
            'created_by': adresse.created_by.get_full_name() if adresse.created_by else None,
            'updated_by': adresse.updated_by.get_full_name() if adresse.updated_by else None,
        })
    
    adresses_json = json.dumps(adresses_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "adresses_json": adresses_json or '[]',
        "acheteur": acheteur,
        "adresses": adresses_list,
        "adresses_count": adresses_list.count(),
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/adresse/dash_root_adresse_acheteur.html",
        context,
    )
    
    
    
    
    
    
  

@login_required
def dash_root_manage_portable_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des numéros de portable d'un acheteur
    Un acheteur peut avoir plusieurs numéros de portable
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer tous les portables de l'acheteur
    portables = PortableAcheteur.objects.filter(acheteur=acheteur).order_by('-created_at')
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Préparer les données des portables pour le template
    portables_data = []
    for portable in portables:
        portables_data.append({
            'id': portable.id,
            'portable': portable.portable or '',
            'nom': portable.nom or '',
            'created_at': portable.created_at.isoformat() if portable.created_at else None,
            'updated_at': portable.updated_at.isoformat() if portable.updated_at else None,
            'created_by': portable.created_by.get_full_name() if portable.created_by else 'Inconnu',
        })
    
    portables_json = json.dumps(portables_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "portables_json": portables_json or '[]',
        "acheteur": acheteur,
        "portables": portables,
        "portables_count": portables.count(),
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/portable/dash_root_portable_acheteur.html",
        context,
    )
    
    
    
    
    
    


@login_required
def dash_root_manage_telephone_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des numéros de téléphone fixe d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer tous les téléphones de l'acheteur
    telephones = TelephoneAcheteur.objects.filter(acheteur=acheteur).order_by('-created_at')
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Préparer les données des téléphones pour le template
    telephones_data = []
    for telephone in telephones:
        telephones_data.append({
            'id': telephone.id,
            'telephone': telephone.telephone or '',
            'nom': telephone.nom or '',
            'formatted_number': telephone.get_formatted_number(),
            'created_at': telephone.created_at.isoformat() if telephone.created_at else None,
            'updated_at': telephone.updated_at.isoformat() if telephone.updated_at else None,
            'created_by': telephone.created_by.get_full_name() if telephone.created_by else 'Inconnu',
        })
    
    telephones_json = json.dumps(telephones_data, default=str)

    context = {
        "acheteur_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "telephones_json": telephones_json or '[]',
        "acheteur": acheteur,
        "telephones": telephones,
        "telephones_count": telephones.count(),
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/telephone/dash_root_telephone_acheteur.html",
        context,
    )
    
    
    
    
    
    
    

@login_required
def dash_root_manage_email_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des adresses email d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ),
        id=acheteur_id
    )

    # Récupérer tous les emails de l'acheteur
    emails = EmailAcheteur.objects.filter(acheteur=acheteur).order_by('-created_at')
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)

    # Préparer les données des emails pour le template
    emails_data = []
    for email in emails:
        emails_data.append({
            'id': email.id,
            'email': email.email or '',
            'description': email.description or '',
            'created_at': email.created_at.isoformat() if email.created_at else None,
            'updated_at': email.updated_at.isoformat() if email.updated_at else None,
            'created_by': email.created_by.get_full_name() if email.created_by else 'Inconnu',
        })
    
    emails_json = json.dumps(emails_data, default=str)

    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "emails_json": emails_json or '[]',
        "acheteur": acheteur,
        "emails": emails,
        "emails_count": emails.count(),
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/email/dash_root_email_acheteur.html",
        context,
    )









@login_required
def dash_root_manage_code_nace_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des codes NACE d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    # Au lieu de .prefetch_related('code_nace')
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related(
            'codes_nace__code',  # ← Utilisez le related_name
            'codes_nace__code__category'
        ),
        id=acheteur_id
    )

    # Récupérer tous les codes NACE de l'acheteur avec les détails
    codes_nace_list = CodeNaceAcheteur.objects.filter(
        acheteur=acheteur
    ).select_related(
        'code',
        'code__category'
    ).order_by('-created_at')
    
    # Calculer le poids total
    poids_total = 0.0
    for code_nace in codes_nace_list:
        if code_nace.code and code_nace.code.poids:
            try:
                poids_total += float(code_nace.code.poids)
            except (ValueError, TypeError):
                continue
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Préparer les données pour le template
    codes_nace_with_data = []
    for code_nace in codes_nace_list:
        if code_nace.code:
            codes_nace_with_data.append({
                'code_nace_obj': code_nace,
                'code': code_nace.code.code or '',
                'libelle': code_nace.code.libelle or '',
                'category_code': code_nace.code.category.code if code_nace.code.category else '',
                'category_libelle': code_nace.code.category.libelle if code_nace.code.category else '',
                'poids': code_nace.code.poids or 0.0,
                'active': code_nace.code.active or False,
                'created_at': code_nace.created_at,
                'updated_at': code_nace.updated_at
            })

    # Préparer les données des codes NACE pour le template
    codes_nace_data = []
    for code_nace in codes_nace_list:
        codes_nace_data.append({
            'id': code_nace.id,
            'code_id': code_nace.code.id,
            'code': code_nace.code.code or '',
            'libelle': code_nace.code.libelle or '',
            'category': {
                'id': code_nace.code.category.id,
                'code': code_nace.code.category.code or '',
                'libelle': code_nace.code.category.libelle or ''
            },
            'poids': float(code_nace.code.poids) if code_nace.code.poids else 0.0,
            'created_at': code_nace.created_at.isoformat() if code_nace.created_at else None,
            'updated_at': code_nace.updated_at.isoformat() if code_nace.updated_at else None,
        })
    
    codes_nace_json = json.dumps(codes_nace_data, default=str)
    
    
    # Dans votre vue, avant le return render()
    print("=== DEBUG: Informations sur les codes NACE ===")
    print(f"Nombre total de codes NACE: {codes_nace_list.count()}")
    print(f"Poids total: {poids_total}")

    for i, code_nace in enumerate(codes_nace_list):
        print(f"\n--- Code NACE #{i+1} ---")
        print(f"ID CodeNaceAcheteur: {code_nace.id}")
        print(f"Acheteur ID: {code_nace.acheteur_id}")
        print(f"Code ID: {code_nace.code_id}")
        
        if code_nace.code:
            print(f"Code object: {code_nace.code}")
            print(f"Code code: {code_nace.code.code}")
            print(f"Code libelle: {code_nace.code.libelle}")
            print(f"Code poids: {code_nace.code.poids}")
            
            if code_nace.code.category:
                print(f"Category: {code_nace.code.category}")
                print(f"Category code: {code_nace.code.category.code}")
                print(f"Category libelle: {code_nace.code.category.libelle}")
            else:
                print("Category: None")
        else:
            print("Code object: None")
        
        print(f"Created at: {code_nace.created_at}")
        print(f"Updated at: {code_nace.updated_at}")

    print("\n=== Fin DEBUG ===")

    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "codes_nace": codes_nace_list,  # UNE SEULE FOIS
        "codes_nace_count": codes_nace_list.count(),
        "codes_nace_data": codes_nace_with_data,  # Nouvelles données structurées
        "poids_total": round(poids_total, 2),
        "codes_nace_json": codes_nace_json or '[]',
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
    }
    return render(
        request,
        "main/root/acheteur/code_nace/dash_root_code_nace_acheteur.html",
        context,
    ) 
    
    
    
    

@login_required
def dash_root_manage_code_naf_acheteur(request, acheteur_id):
    """
    Vue pour la gestion des codes NAF d'un acheteur
    """
    
    # Récupérer l'acheteur avec préfetch pour optimiser
    acheteur = get_object_or_404(
        Acheteur.objects.select_related(
            'statut_entreprise',
            'forme_juridique',
            'pays',
            'province',
            'ville'
        ).prefetch_related(
            'codes_naf__code',  # ← Utilisez le related_name
            'codes_naf__code__category'
        ),
        id=acheteur_id
    )

    # Récupérer tous les codes NAF de l'acheteur avec les détails
    codes_naf_list = CodeNafAcheteur.objects.filter(
        acheteur=acheteur
    ).select_related(
        'code',
        'code__category'
    ).order_by('-created_at')
    
    # Calculer le poids total
    poids_total = 0.0
    for code_naf in codes_naf_list:
        if code_naf.code and code_naf.code.poids:
            try:
                poids_total += float(code_naf.code.poids)
            except (ValueError, TypeError):
                continue
    
    # Génération des tokens JWT
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception as e:
        logger.error(f"Erreur lors de la génération des tokens: {e}")
        messages.error(request, "Erreur d'authentification. Veuillez vous reconnecter.")
        return redirect_to_login(request.get_full_path())
    
    # Préparer les données de l'acheteur pour le template
    acheteur_data = {
        'id': acheteur.id,
        'nom': acheteur.nom or 'Non spécifié',
        'sigle': acheteur.sigle or '',
        'code': acheteur.code or 'N/A',
        'activite_principale': acheteur.activite_principale or 'Non spécifié',
        'date_creation': acheteur.date_creation.isoformat() if acheteur.date_creation else None,
        'statut_entreprise': acheteur.statut_entreprise.libelle if acheteur.statut_entreprise else 'Inconnu',
        'pays': acheteur.pays.nom if acheteur.pays else 'Non spécifié',
    }
    
    # Convertir en JSON sécurisé pour JavaScript
    acheteur_json = json.dumps(acheteur_data, default=str)
    
    # Préparer les données pour le template
    codes_naf_with_data = []
    for code_naf in codes_naf_list:
        if code_naf.code:
            codes_naf_with_data.append({
                'code_naf_obj': code_naf,
                'code': code_naf.code.code or '',
                'libelle': code_naf.code.libelle or '',
                'category_code': code_naf.code.category.code if code_naf.code.category else '',
                'category_libelle': code_naf.code.category.libelle if code_naf.code.category else '',
                'poids': code_naf.code.poids or 0.0,
                'active': code_naf.code.active or False,
                'created_at': code_naf.created_at,
                'updated_at': code_naf.updated_at
            })

    # Préparer les données des codes NAF pour le template
    codes_naf_data = []
    for code_naf in codes_naf_list:
        if code_naf.code:
            codes_naf_data.append({
                'id': code_naf.id,
                'code_id': code_naf.code.id,
                'code': code_naf.code.code or '',
                'libelle': code_naf.code.libelle or '',
                'category': {
                    'id': code_naf.code.category.id if code_naf.code.category else None,
                    'code': code_naf.code.category.code if code_naf.code.category else '',
                    'libelle': code_naf.code.category.libelle if code_naf.code.category else ''
                },
                'poids': float(code_naf.code.poids) if code_naf.code.poids else 0.0,
                'created_at': code_naf.created_at.isoformat() if code_naf.created_at else None,
                'updated_at': code_naf.updated_at.isoformat() if code_naf.updated_at else None,
            })
    
    codes_naf_json = json.dumps(codes_naf_data, default=str)
    
    # Tous les codes NAF actifs pour le Select2 côté serveur (évite AJAX dans modal)
    all_naf_subcategories = (
        SubCategoryNafCode.objects
        .filter(active=True)
        .select_related('category')
        .order_by('category__code', 'code')
    )

    context = {
        "acheteurs_active": "active",
        "user": request.user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "acheteur_json": acheteur_json,
        "codes_naf": codes_naf_list,
        "codes_naf_count": codes_naf_list.count(),
        "codes_naf_data": codes_naf_with_data,
        "poids_total": round(poids_total, 2),
        "codes_naf_json": codes_naf_json or '[]',
        "acheteur": acheteur,
        "id_acheteur": acheteur_id,
        "all_naf_subcategories": all_naf_subcategories,
        "is_english": (get_language() or '').startswith('en'),
    }
    return render(
        request,
        "main/root/acheteur/code_naf/dash_root_code_naf_acheteur.html",
        context,
    )

    
    
    

@login_required
def dash_root_manage_backup(request):
    user = request.user

    # Génération des tokens d'accès
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')
    
    context = {
        "acheteurs_active": "active",
        "user": user,
        "refresh": refresh,
        "access": access_token,
    }
    return render(
        request,
        "main/root/backup/dash_root_manage_backup.html",
        context,
    )
    
    
    
def _warning_token_context(request):
    """Helper : génère les tokens JWT et la langue pour les vues Warning."""
    user = request.user
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception:
        return None, None, None
    preferred_lang = getattr(user, 'preferred_language', None) or 'fr'
    lang_map = {'fr': 'fr', 'en': 'en', 'en-us': 'en', 'fr-fr': 'fr'}
    spell_lang = lang_map.get(str(preferred_lang).lower(), 'fr')
    return access_token, refresh_token, spell_lang


def dash_root_warning(request):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    access_token, refresh_token, spell_lang = _warning_token_context(request)
    if access_token is None:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')
    return render(request, "main/root/alertes/dash_root_warning.html", {
        "warnings_active": "active",
        "user": request.user,
        "refresh": refresh_token,
        "access": access_token,
        "spell_lang": spell_lang,
    })


def dash_root_create_warning(request):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    access_token, refresh_token, spell_lang = _warning_token_context(request)
    if access_token is None:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')
    return render(request, "main/root/alertes/dash_root_warning_form.html", {
        "warnings_active": "active",
        "form_mode": "create",
        "user": request.user,
        "refresh": refresh_token,
        "access": access_token,
        "spell_lang": spell_lang,
    })


def dash_root_edit_warning(request, warning_id):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    access_token, refresh_token, spell_lang = _warning_token_context(request)
    if access_token is None:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')
    return render(request, "main/root/alertes/dash_root_warning_form.html", {
        "warnings_active": "active",
        "form_mode": "edit",
        "warning_id": warning_id,
        "user": request.user,
        "refresh": refresh_token,
        "access": access_token,
        "spell_lang": spell_lang,
    })


def dash_root_view_warning(request, warning_id):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    access_token, refresh_token, spell_lang = _warning_token_context(request)
    if access_token is None:
        messages.error(request, "Erreur lors de la génération des tokens.")
        return redirect('index')
    return render(request, "main/root/alertes/dash_root_warning_detail.html", {
        "warnings_active": "active",
        "warning_id": warning_id,
        "user": request.user,
        "refresh": refresh_token,
        "access": access_token,
    })











########################################################################################################################
#                                                                                                                      #
#  VIEWS END FOR ROOT                                                                                                  #
#                                                                                                                      #
########################################################################################################################

























########################################################################################################################
#                                                                                                                      #
#  VIEWS START FOR VALIDATEUR                                                                                          #
#                                                                                                                      #
########################################################################################################################
from django.contrib.auth import get_user_model
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Ensure User is correctly imported or defined
User = get_user_model()

#@login_required
def dash_validateur_2(request):
    token = request.GET.get("token")
    logger.debug(f"Token received: {token}")

    if not token:
        logger.error("Token is missing.")
        pass

    try:
        # Attempt to create an AccessToken from the provided token
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        logger.debug(f"User ID extracted from token: {user_id}")

        user = User.objects.get(pk=user_id)
        login(request, user)  # Manually authenticate the user
        logger.debug(f"User {user.username} logged in successfully.")
    except TokenError as e:
        logger.error(f"Token error: {e}")
        # Handle the case where the token is invalid
        return render(request, "main/index.html", {"error": _("Token invalide.")})
    except User.DoesNotExist as e:
        logger.error(f"User not found: {e}")
        # Handle the case where the user does not exist
        return render(request, "main/index.html", {"error": _("Utilisateur non trouvé.")})

    refresh = RefreshToken.for_user(user)
    context = {
        "dash_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/dash_root.html", context)


#@login_required
def dash_validateur_3(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "users_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/dash_root.html", context)


#@login_required
def dash_validateur(request):
    print(f"DEBUG: dash_validateur - Utilisateur authentifié ? {request.user.is_authenticated}")
    if request.user.is_authenticated:
        print(f"DEBUG: dash_validateur - Nom d'utilisateur : {request.user.username}")
        print(f"DEBUG: dash_validateur - Clé de session : {request.session.session_key}")
    else:
        print("DEBUG: dash_validateur - Utilisateur non authentifié malgré #@login_required (devrait rediriger).")

    user = request.user
    context = {
        "users_active": "active",
        "user": user,
        # Supprimez la génération de tokens refresh/access ici comme suggéré précédemment
    }
    return render(request, "main/validateur/dash_root.html", context)


@login_required
def dash_validateur_user(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    context = {
        "users_active": "active",
        "pays_list": pays_list,
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/utilisateur/dash_root_user.html", context)


@login_required
def dash_validateur_pays(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "locations_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/pays/dash_root_pays.html", context)


@login_required
def dash_validateur_province(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    context = {
        "locations_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "pays_list": pays_list,  # Ajouter la liste des pays au contexte
    }
    return render(request, "main/validateur/province/dash_root_province.html", context)


@login_required
def dash_validateur_ville(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    # pays_list = Pays.objects.all()

    # Récupérer tous les pays
    province_list = Province.objects.all()

    context = {
        "locations_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        # 'pays_list': pays_list,  # Ajouter la liste des pays au contexte
        "province_list": province_list,  # Ajouter la liste des pays au contexte
    }
    return render(request, "main/validateur/ville/dash_root_ville.html", context)


@login_required
def dash_validateur_devise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    # Récupérer tous les pays
    province_list = Province.objects.all()

    context = {
        "codification_active": "active",
        "devise_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "pays_list": pays_list,  # Ajouter la liste des pays au contexte
        "province_list": province_list,  # Ajouter la liste des pays au contexte
    }
    return render(request, "main/validateur/devise/dash_root_devise.html", context)


@login_required
def dash_validateur_annee(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    Pays.objects.all()

    # Récupérer tous les pays
    Province.objects.all()

    context = {
        "codification_active": "active",
        "annee_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/annee/dash_root_annee.html", context)


@login_required
def dash_validateur_coloration(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "coloration_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/coloration/dash_root_coloration.html", context)


@login_required
def dash_validateur_category_nace(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "nace_cat_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/nace/dash_root_category_nace.html", context)


@login_required
def dash_validateur_category_naf(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "naf_cat_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/naf/dash_root_category_naf.html", context)


@login_required
def dash_validateur_code_nace(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les categories nace
    categorie_list = CategoryNaceCode.objects.all()

    context = {
        "codification_active": "active",
        "nace_code_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "categorie_list": categorie_list,
    }
    return render(request, "main/validateur/nace/dash_root_code_nace.html", context)


@login_required
def dash_validateur_code_naf(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les categories nace
    categorie_list = CategoryNafCode.objects.all()

    context = {
        "codification_active": "active",
        "naf_code_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "categorie_list": categorie_list,
    }
    return render(request, "main/validateur/naf/dash_root_code_naf.html", context)


@login_required
def dash_validateur_forme_juridique(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "juridique_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/validateur/juridique/dash_root_forme_juridique.html", context
    )


@login_required
def dash_validateur_domaine(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "domaine_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/domaine/dash_root_domaine.html", context)


@login_required
def dash_validateur_modele_bail(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_bail_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/modele/dash_root_modele_bail.html", context)


@login_required
def dash_validateur_modele_bilan(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_bilan_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/modele/dash_root_modele_bilan.html", context)


@login_required
def dash_validateur_modele_alarme(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_alarme_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/modele/dash_root_modele_alarme.html", context)


@login_required
def dash_validateur_modele_rapport(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_rapport_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/modele/dash_root_modele_rapport.html", context)


@login_required
def dash_validateur_modele_avis_commercial(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_avis_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/validateur/modele/dash_root_modele_avis_commercial.html", context
    )


@login_required
def dash_validateur_modele_relation_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_relation_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/validateur/modele/dash_root_modele_relation_entreprise.html", context
    )


@login_required
def dash_validateur_modele_notation(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_notation_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/modele/dash_root_modele_notation.html", context)


@login_required
def dash_validateur_modele_comportement_paiement(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_cpaiement_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/validateur/modele/dash_root_modele_comportement_paiement.html", context
    )


@login_required
def dash_validateur_modele_comportement_jugement(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_cjugement_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/validateur/modele/dash_root_modele_comportement_jugement.html", context
    )

    
    


@login_required
def dash_validateur_modele_information_notation_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_infone_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request,
        "main/validateur/modele/dash_root_modele_information_notation_entreprise.html",
        context,
    )


@login_required
def dash_validateur_poste(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupération des domaines
    domaines = DomaineEntreprise.objects.all()

    context = {
        "codification_active": "active",
        "poste_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "domaines": domaines,  # Ajouter les domaines au contexte
    }
    return render(request, "main/validateur/poste/dash_root_poste.html", context)


@login_required
def dash_validateur_category_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "entreprise_cat_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/validateur/entreprise/dash_root_category_entreprise.html", context
    )


@login_required
def dash_validateur_structure_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "entreprise_structure_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/validateur/structure/dash_root_structure_entreprise.html", context
    )


@login_required
def dash_validateur_statut_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "entreprise_statut_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/statut/dash_root_statut_entreprise.html", context)


@login_required
def dash_validateur_acheteur(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/acheteur/dash_root_acheteur.html", context)


@login_required
def dash_validateur_add_acheteur(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les categories d'entreprise
    categorie_list = CategorieEntreprise.objects.all()

    # Récupérer tous les formes juridiques
    juridique_list = _translate_juridique_list(request)

    # Récupérer tous les statuts entreprise
    statut_list = _translate_statut_list(request)

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    # Récupérer tous les provinces
    province_list = Province.objects.all()

    # Récupérer tous les villes
    ville_list = Ville.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "categorie_list": categorie_list,
        "juridique_list": juridique_list,
        "statut_list": statut_list,
        "coloration_list": coloration_list,
        "pays_list": pays_list,
        "province_list": province_list,
        "ville_list": ville_list,
    }
    return render(request, "main/validateur/acheteur/dash_root_add_acheteur.html", context)


@login_required
def dash_validateur_edit_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les categories d'entreprise
    categorie_list = CategorieEntreprise.objects.all()

    # Récupérer tous les formes juridiques
    juridique_list = _translate_juridique_list(request)

    # Récupérer tous les statuts entreprise
    statut_list = _translate_statut_list(request)

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    # Récupérer tous les provinces
    province_list = Province.objects.all()

    # Récupérer tous les villes
    ville_list = Ville.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "categorie_list": categorie_list,
        "juridique_list": juridique_list,
        "statut_list": statut_list,
        "coloration_list": coloration_list,
        "pays_list": pays_list,
        "province_list": province_list,
        "ville_list": ville_list,
    }
    return render(request, "main/validateur/acheteur/dash_root_edit_acheteur.html", context)


@login_required
def dash_validateur_manage_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les categories d'entreprise
    categorie_list = CategorieEntreprise.objects.all()

    # Récupérer tous les formes juridiques
    juridique_list = _translate_juridique_list(request)

    # Récupérer tous les statuts entreprise
    statut_list = _translate_statut_list(request)

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    # Récupérer tous les provinces
    province_list = Province.objects.all()

    # Récupérer tous les villes
    ville_list = Ville.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "categorie_list": categorie_list,
        "juridique_list": juridique_list,
        "statut_list": statut_list,
        "coloration_list": coloration_list,
        "pays_list": pays_list,
        "province_list": province_list,
        "ville_list": ville_list,
    }
    return render(request, "main/validateur/acheteur/dash_root_manage_acheteur.html", context)


@login_required
def dash_validateur_manage_acheteur_resume(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "devise_list": devise_list,
        "coloration_list": coloration_list,
        "bons_postes_list": bons_postes_list,
    }
    return render(
        request,
        "main/validateur/acheteur/resume/dash_root_manage_acheteur_resume.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_risk_rating(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/validateur/acheteur/riskrating/dash_root_manage_acheteur_risk_rating.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_data_save(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les statuts d'entreprise
    statut_list = _translate_statut_list(request)

    # Récupérer tous les formes juridiques
    juridique_list = _translate_juridique_list(request)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "statut_list": statut_list,
        "juridique_list": juridique_list,
    }
    return render(
        request,
        "main/validateur/acheteur/data/dash_root_manage_acheteur_data_save.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_tendance(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les avis commerciaux
    commercial_list = ModeleAvisCommercial.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "commercial_list": commercial_list,
    }
    return render(
        request,
        "main/validateur/acheteur/tendance/dash_root_manage_acheteur_tendance.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_responsable(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "poste_list": poste_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/validateur/acheteur/responsable/dash_root_manage_acheteur_responsable.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_antecedent(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/validateur/acheteur/antecedent/dash_root_manage_acheteur_antecedent.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_gestion_risque(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/validateur/acheteur/gestion/dash_root_manage_acheteur_gestion_risque.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_membre_conseil(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "poste_list": poste_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/validateur/acheteur/conseil/dash_root_manage_acheteur_membre_conseil.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_composition_capital(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "devise_list": devise_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/validateur/acheteur/composition/dash_root_manage_acheteur_composition_capital.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_actionnaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/validateur/acheteur/actionnaire/dash_root_manage_acheteur_actionnaire.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_opinion_acremac(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/validateur/acheteur/opinion/dash_root_manage_acheteur_opinion_acremac.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_filiale(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "structure_list": structure_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/validateur/acheteur/filiale/dash_root_manage_acheteur_filiale.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_analyse_sectorielle(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "structure_list": structure_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/validateur/acheteur/analyse/dash_root_manage_acheteur_analyse_sectorielle.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_compte_financier(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "bilan_list": bilan_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/validateur/acheteur/finance/dash_root_manage_acheteur_compte_financier.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_operation_historique(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/validateur/acheteur/operation/dash_root_manage_acheteur_operation_historique.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_propriete_actif(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les reference des locaux
    locaux_list = ModeleBail.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "locaux_list": locaux_list,
    }
    return render(
        request,
        "main/validateur/acheteur/propriete/dash_root_manage_acheteur_propriete_actif.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_condition_achat(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/validateur/acheteur/achat/dash_root_manage_acheteur_condition_achat.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_condition_vente(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "paiement_list": paiement_list,
        "jugement_list": jugement_list,
    }
    return render(
        request,
        "main/validateur/acheteur/vente/dash_root_manage_acheteur_condition_vente.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_sommaire_avis(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/validateur/acheteur/sommaire/dash_root_manage_acheteur_sommaire_avis.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_advice(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/validateur/acheteur/advice/dash_root_manage_acheteur_advice.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_geopolitic(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/validateur/acheteur/geopolitique/dash_root_manage_acheteur_geopolitic.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_banking(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "ville_list": ville_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/validateur/acheteur/banque/dash_root_manage_acheteur_banking.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_actif_anglais(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/anglais/dash_root_manage_acheteur_actif_anglais.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_passif_anglais(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/anglais/dash_root_manage_acheteur_passif_anglais.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_resultat_anglais(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/anglais/dash_root_manage_acheteur_resultat_anglais.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_actif_classique(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/classique/dash_root_manage_acheteur_actif_classique.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_passif_classique(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/classique/dash_root_manage_acheteur_passif_classique.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_resultat_classique(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/classique/dash_root_manage_acheteur_resultat_classique.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_actif_syscohada(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/syscohada/dash_root_manage_acheteur_actif_syscohada.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_passif_syscohada(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/syscohada/dash_root_manage_acheteur_passif_syscohada.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_resultat_syscohada(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/syscohada/dash_root_manage_acheteur_resultat_syscohada.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_asset_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/bancaire/dash_root_manage_acheteur_asset_bancaire.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_liabilitie_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/bancaire/dash_root_manage_acheteur_liabilitie_bancaire.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_offbalancesheet_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/bancaire/dash_root_manage_acheteur_offbalancesheet_bancaire.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_expense_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/bancaire/dash_root_manage_acheteur_expense_bancaire.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_product_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/bancaire/dash_root_manage_acheteur_product_bancaire.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_compte_financier_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/irfs/dash_root_manage_acheteur_compte_financier_irfs.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_ratio_financier_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/irfs/dash_root_manage_acheteur_ratio_financier_irfs.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_actif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Actif"
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/irfs/dash_root_manage_acheteur_actif_irfs.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_passif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Passif"
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/irfs/dash_root_manage_acheteur_passif_irfs.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_resultat_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Compte de "
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/irfs/dash_root_manage_acheteur_passif_irfs.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_add_actif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Actif"
    )

    # Récupérer tous les actifs financiers irfs
    actif_financier_irfs_list = ValeurCompteIrfs.objects.filter(
        compte__type_compte__icontains="Actif", acheteur__pk=id_acheteur
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
        "actif_financier_irfs_list": actif_financier_irfs_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/irfs/dash_root_manage_acheteur_add_actif_irfs.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_add_passif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Passif"
    )

    # Récupérer tous les actifs financiers irfs
    actif_financier_irfs_list = ValeurCompteIrfs.objects.filter(
        compte__type_compte__icontains="Passif", acheteur__pk=id_acheteur
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
        "actif_financier_irfs_list": actif_financier_irfs_list,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/irfs/dash_root_manage_acheteur_add_passif_irfs.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_report_web(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Recuperer les elements du rapports ici !

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/validateur/acheteur/report/dash_root_manage_acheteur_report_web.html",
        context,
    )


@login_required
def dash_validateur_commande(request):
    token = request.GET.get("token")
    if not token:
        pass

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
    client_list = User.objects.filter(
        Q(role__icontains="Client") | Q(role__icontains="client")
    ).order_by("id")

    # Récupérer tous les villes
    ville_list = Ville.objects.all()

    # Récupérer tous les modeles de rapport
    modele_rapport_list = ModeleRapport.objects.all()

    context = {
        "requests_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "devise_list_one": devise_list_one,
        "devise_list_two": devise_list_two,
        "client_list": client_list,
        "ville_list": ville_list,
        "acheteur_list": acheteur_list,
        "modele_rapport_list": modele_rapport_list,
    }
    return render(request, "main/validateur/orders/dash_root_commande.html", context)


@login_required
def dash_validateur_manage_commande(request, commande_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de la commande
    id_commande = commande_id

    # Récupérer tous les categories d'entrepris

    context = {
        "requests_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_commande": id_commande,
    }
    return render(request, "main/validateur/orders/dash_root_manage_commande.html", context)


@login_required
def dash_validateur_alerte(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Supprimer d'abord tous
    # alertes = Alerte.objects.all()
    # alertes.delete()

    # documents = DocumentAlerte.objects.all()
    # documents.delete()

    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/warning/dash_root_alerte.html", context)


@login_required
def dash_validateur_add_alerte(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Créer une nouvelle alerte ici
    random_number = random.randint(100, 9999)
    reference = f"ALT{random_number}"

    # Créer une instance de l'alerte
    # alerte = Alerte.objects.create(
    # reference=reference,
    # objet="Nouvelle alerte",  # Vous pouvez définir un objet par défaut ou le laisser vide
    # content="Contenu de l'alerte"  # Vous pouvez définir un contenu par défaut ou le laisser vide
    # )

    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "reference": reference,  # Passer l'alerte au contexte si nécessaire
    }
    return render(request, "main/validateur/warning/dash_root_add_alerte.html", context)


@login_required
def dash_validateur_edit_new_alerte(request, reference):

    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Get alerte
    alerte = Alerte.objects.get(reference=reference)

    # Get all documents from this alert
    documents = DocumentAlerte.objects.filter(alerte=alerte)

    # Get context
    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "reference": reference,  # Passer l'alerte au contexte si nécessaire
        "alerte": alerte,  # Passer l'alerte au contexte si nécessaire
        "documents": documents,  # Passer l'alerte au contexte si nécessaire
    }

    return render(request, "main/validateur/warning/dash_root_edit_new_alerte.html", context)


@login_required
def dash_validateur_document_alerte(request, reference):

    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Get alerte
    alerte = Alerte.objects.get(reference=reference)

    # Get all documents from this alert
    documents = DocumentAlerte.objects.filter(alerte=alerte)

    # Get context
    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "reference": reference,  # Passer l'alerte au contexte si nécessaire
        "alerte": alerte,  # Passer l'alerte au contexte si nécessaire
        "documents": documents,  # Passer l'alerte au contexte si nécessaire
    }

    return render(
        request, "main/validateur/warning/dash_root_add_document_alerte.html", context
    )


@login_required
def dash_validateur_client_alerte(request, reference):

    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Get all clients
    clients = Client.objects.all()

    # Get alerte
    alerte = Alerte.objects.get(reference=reference)

    # Get all documents from this alert
    documents = DocumentAlerte.objects.filter(alerte=alerte)

    # Get context
    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "reference": reference,  # Passer l'alerte au contexte si nécessaire
        "alerte": alerte,  # Passer l'alerte au contexte si nécessaire
        "documents": documents,  # Passer l'alerte au contexte si nécessaire
        "clients": clients,  # Passer l'alerte au contexte si nécessaire
    }

    return render(request, "main/validateur/warning/dash_root_client_alerte.html", context)


@login_required
def dash_validateur_edit_alerte(request, alerte_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'alerte
    id_alerte = alerte_id

    # Récupérer tous les documents lies a l'alerte
    # document_list = DocumentAlerte.objects.fliter(alerte__pk=id_alerte)

    # Récupérer tous les clients
    # client_list = User.objects.filter(Q(role__icontains="Client") | Q(role__icontains="client")).order_by('id')

    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_alerte": id_alerte,
        # 'document_list': document_list,
        # 'client_list': client_list,
    }
    return render(request, "main/validateur/warning/dash_root_edit_alerte.html", context)


@login_required
def dash_validateur_manage_alerte(request, alerte_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'alerte
    id_alerte = alerte_id

    # Récupérer l'alerte
    alerte = Alerte.objects.filter(id=id_alerte).first()

    # Récupérer tous les documents lies a l'alerte
    document_list = DocumentAlerte.objects.filter(alerte__pk=id_alerte)

    # Récupérer tous les clients
    client_list = User.objects.filter(
        Q(role__icontains="Client") | Q(role__icontains="client")
    ).order_by("id")

    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_alerte": id_alerte,
        "alerte": alerte,
        "document_list": document_list,
        "client_list": client_list,
    }
    return render(request, "main/validateur/warning/dash_root_manage_alerte.html", context)


@login_required
def dash_validateur_client(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "clients_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/monitoring/dash_root_client.html", context)


@login_required
def dash_validateur_portefeuille(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "client_list": client_list,
        "acheteur_list": acheteur_list,
    }
    return render(request, "main/validateur/monitoring/dash_root_portefeuille.html", context)


@login_required
def dash_validateur_add_portefeuille(request, portefeuille_id=None):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    # Recuperation des frequences
    frequences = Portefeuille.FREQUENCE_CHOICES

    # Récupérer tous les éléments de surveillance
    surveillances = ElementSurveillance.objects.all()

    # Regrouper les éléments par catégorie
    surveillances_by_category = {}
    for surveillance in surveillances:
        if surveillance.categorie not in surveillances_by_category:
            surveillances_by_category[surveillance.categorie] = []
        surveillances_by_category[surveillance.categorie].append(surveillance)

    # Initialiser selected_elements
    selected_elements = []

    # Si vous modifiez un portefeuille existant
    if portefeuille_id:
        portefeuille = Portefeuille.objects.get(id=portefeuille_id)
        selected_elements = portefeuille.elements_surveillance_actifs.values_list(
            "id", flat=True
        )

    # Passer les éléments groupés et les éléments sélectionnés au template
    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "client_list": client_list,
        "acheteur_list": acheteur_list,
        "frequences": frequences,
        "surveillances_by_category": surveillances_by_category,
        "selected_elements": selected_elements,  # Assurez-vous de définir selected_elements
    }
    return render(
        request, "main/validateur/monitoring/dash_root_add_portefeuille.html", context
    )


@login_required
def dash_validateur_edit_portefeuille(request, portefeuille_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer le portefeuille à modifier
    try:
        portefeuille = Portefeuille.objects.get(id=portefeuille_id)
    except Portefeuille.DoesNotExist:
        return render(
            request, "main/index.html", {"error": _("Portefeuille non trouvé.")}
        )

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs associés à ce portefeuille
    acheteurs_associes = PortefeuilleClient.objects.filter(
        portefeuille=portefeuille
    ).values_list("acheteur_id", flat=True)

    acheteur_list = Acheteur.objects.all()

    # Recuperation des frequences
    frequences = Portefeuille.FREQUENCE_CHOICES

    # Récupérer tous les éléments de surveillance
    surveillances = ElementSurveillance.objects.all()

    # Regrouper les éléments par catégorie
    surveillances_by_category = {}
    for surveillance in surveillances:
        if surveillance.categorie not in surveillances_by_category:
            surveillances_by_category[surveillance.categorie] = []
        surveillances_by_category[surveillance.categorie].append(surveillance)

    # Initialiser selected_elements
    selected_elements = []

    # Si vous modifiez un portefeuille existant
    if portefeuille_id:
        portefeuille = Portefeuille.objects.get(id=portefeuille_id)
        selected_elements = portefeuille.elements_surveillance_actifs.values_list(
            "id", flat=True
        )

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "portefeuille": portefeuille,  # Données du portefeuille à modifier
        "acheteurs_associes": list(
            acheteurs_associes
        ),  # Liste des IDs des acheteurs associés
        "portefeuille_id": portefeuille_id,
        "client_list": client_list,
        "acheteur_list": acheteur_list,
        "frequences": frequences,
        "surveillances_by_category": surveillances_by_category,
        "selected_elements": selected_elements,  # Assurez-vous de définir selected_elements
    }
    return render(
        request, "main/validateur/monitoring/dash_root_edit_portefeuille.html", context
    )


@login_required
def dash_validateur_simulateur_scoring_sb(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "client_list": client_list,
        "acheteur_list": acheteur_list,
    }
    return render(
        request, "main/validateur/simulateur/dash_root_simulateur_scoring_sb.html", context
    )


@login_required
def dash_validateur_element_surveillance(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    for element in elements:
        ElementSurveillance.objects.get_or_create(
            code_interne=element[
                "code_interne"
            ],  # Utilisez un champ unique pour vérifier les doublons
            defaults={
                "nom": element["nom"],
                "categorie": element["categorie"],
                "sous_categorie": element["sous_categorie"],
            },
        )

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "client_list": client_list,
        "acheteur_list": acheteur_list,
    }
    return render(
        request, "main/validateur/surveillance/dash_root_element_surveillance.html", context
    )


@login_required
def dash_validateur_alerte_log(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les alertes
    alerte_list = AlerteLog.objects.all()

    # Récupérer les portefeuilles
    portefeuille_list = Portefeuille.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    # Récupérer les elements
    element_surveille_list = ElementSurveillance.objects.all()

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "alerte_list": alerte_list,
        "portefeuille_list": portefeuille_list,
        "acheteur_list": acheteur_list,
        "element_surveille_list": element_surveille_list,
    }
    return render(request, "main/validateur/monitoring/dash_root_alerte_log.html", context)


@login_required
def dash_validateur_certification_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les certifications
    certification_list = Certification.objects.all()

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteurs_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "certification_list": certification_list,
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/validateur/acheteur/certification/dash_root_certification_acheteur.html",
        context,
    )


@login_required
def dash_validateur_innovation_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer les innovations
    innovation_list = InnovationDeveloppement.objects.all()

    context = {
        "acheteurs_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "innovation_list": innovation_list,
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/validateur/acheteur/innovation/dash_root_innovation_acheteur.html",
        context,
    )


@login_required
def dash_validateur_strategie_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer les strategies
    strategie_list = StrategiePlanification.objects.all()

    context = {
        "acheteurs_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "strategie_list": strategie_list,
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/validateur/acheteur/strategie/dash_root_strategie_acheteur.html",
        context,
    )


@login_required
def dash_validateur_conformite_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer les conformites
    conformite_list = ConformiteReglementation.objects.all()

    context = {
        "acheteurs_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "conformite_list": conformite_list,
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/validateur/acheteur/conformite/dash_root_conformite_acheteur.html",
        context,
    )


@login_required
def dash_validateur_manage_acheteur_bilan_actif_bancaire_0(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer l'acheteur actuel pour l'afficher
    acheteur_actuel = Acheteur.objects.get(id=acheteur_id)

    # Récupérer TOUS les acheteurs pour la liste déroulante
    tous_les_acheteurs = Acheteur.objects.all()

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les actifs de l'acheteur
    actifs = Assets.objects.filter(acheteur_id=acheteur_id)

    # Récupérer tous les passifs de l'acheteur
    passifs = Liabilities.objects.filter(acheteur_id=acheteur_id)

    # Récupérer tous les depenses de l'acheteur
    depenses = Expenses.objects.filter(acheteur_id=acheteur_id)

    # Récupérer tous les produits de l'acheteur
    produits = Products.objects.filter(acheteur_id=acheteur_id)

    # Récupérer tous les hors bilans de l'acheteur
    hors_bilans = OffBalanceSheet.objects.filter(acheteur_id=acheteur_id)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "acheteur": acheteur_actuel,  # Ajouter l'objet acheteur actuel
        "acheteurs": tous_les_acheteurs,  # <--- AJOUTER CETTE LIGNE
        "annee_list": annee_list,
        "actifs": actifs,
        "passifs": passifs,
        "depenses": depenses,
        "produits": produits,
        "hors_bilans": hors_bilans,
    }
    return render(
        request,
        "main/validateur/acheteur/bilans/bancaire/dash_root_manage_acheteur_bilan_actif_bancaire.html",
        context,
    )

    # En haut de votre fichier views.py, ajoutez cet import


@login_required
def dash_validateur_manage_acheteur_bilan_actif_bancaire(request, acheteur_id):
    """
    Vue pour gérer les bilans (Actifs, Passifs, Dépenses, Produits) d'un acheteur,
    avec pagination pour chaque section.
    """
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user
    refresh = RefreshToken.for_user(user)
    id_acheteur = acheteur_id

    try:
        acheteur_actuel = Acheteur.objects.get(id=id_acheteur)
    except Acheteur.DoesNotExist:
        return render(
            request, "main/error_page.html", {"error": _("Acheteur non trouvé.")}
        )

    tous_les_acheteurs = Acheteur.objects.all()
    annee_list = Annee.objects.all()

    # --- PAGINATION DES ACTIFS ---
    actifs_list = Assets.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    actifs_paginator = Paginator(actifs_list, 10)
    page_actifs = request.GET.get("page_actifs")
    actifs_page_obj = actifs_paginator.get_page(page_actifs)

    # --- PAGINATION DES PASSIFS ---
    passifs_list = Liabilities.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    passifs_paginator = Paginator(passifs_list, 10)
    page_passifs = request.GET.get("page_passifs")
    passifs_page_obj = passifs_paginator.get_page(page_passifs)

    # --- PAGINATION DES DÉPENSES ---
    depenses_list = Expenses.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    depenses_paginator = Paginator(depenses_list, 10)
    page_depenses = request.GET.get("page_depenses")
    depenses_page_obj = depenses_paginator.get_page(page_depenses)

    # --- NOUVEAU : PAGINATION DES PRODUITS ---
    produits_list = Products.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    produits_paginator = Paginator(produits_list, 10)
    page_produits = request.GET.get("page_produits")
    produits_page_obj = produits_paginator.get_page(page_produits)

    # --- NOUVEAU : PAGINATION DU HORS BILAN ---
    hors_bilans_list = OffBalanceSheet.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    hors_bilans_paginator = Paginator(hors_bilans_list, 10)
    page_hors_bilans = request.GET.get("page_hors_bilans")
    hors_bilans_page_obj = hors_bilans_paginator.get_page(page_hors_bilans)

    # MODIFIÉ : Mise à jour du contexte pour inclure les produits paginés
    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "acheteur": acheteur_actuel,
        "acheteurs": tous_les_acheteurs,
        "annee_list": annee_list,
        "annee_list_data": json.dumps(list(Annee.objects.values("id", "annee"))),
        "type_bilan_choices_json": json.dumps(list(TYPE_BILAN_CHOICES)),
        "semestre_choices_json": json.dumps(list(SEMESTRE_CHOICES)),
        # Objets de page paginés pour le template
        "actifs_page": actifs_page_obj,
        "passifs_page": passifs_page_obj,
        "depenses_page": depenses_page_obj,
        "produits_page": produits_page_obj,
        "hors_bilans_page": hors_bilans_page_obj,  # <- NOUVEAU CONTEXTE
    }

    return render(
        request,
        "main/validateur/acheteur/bilans/bancaire/dash_root_manage_acheteur_bilan_actif_bancaire.html",  # Nom de template suggéré
        context,
    )


@login_required
def dash_validateur_manage_acheteur_bilan_irfs_cobac(request, acheteur_id):
    """
    Vue pour gérer les états financiers IFRS (Actif, Passif, Résultat, Ratios)
    d'un acheteur, avec pagination pour chaque section.
    """
    token = request.GET.get("token")
    if not token:
        # Idéalement, rediriger vers une page de connexion ou afficher une erreur claire.
        return render(
            request,
            "main/index.html",
            {"error": _("Token d'authentification manquant.")},
        )

    user = request.user
    refresh = RefreshToken.for_user(user)

    try:
        acheteur_actuel = Acheteur.objects.get(id=acheteur_id)
    except Acheteur.DoesNotExist:
        return render(
            request, "main/error_page.html", {"error": _("Acheteur non trouvé.")}
        )

    # Données communes pour les formulaires
    tous_les_acheteurs = Acheteur.objects.all()
    annee_list = Annee.objects.all()

    # --- PAGINATION ACTIF IFRS ---
    actifs_list = ActifIFRS.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee"
    )
    actifs_paginator = Paginator(actifs_list, 10)  # 10 par page
    page_actifs = request.GET.get("page_actifs")
    actifs_page_obj = actifs_paginator.get_page(page_actifs)

    # --- PAGINATION PASSIF IFRS ---
    passifs_list = PassifIFRS.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee"
    )
    passifs_paginator = Paginator(passifs_list, 10)
    page_passifs = request.GET.get("page_passifs")
    passifs_page_obj = passifs_paginator.get_page(page_passifs)

    # --- PAGINATION COMPTE DE RÉSULTAT IFRS ---
    resultats_list = ResultatIFRS.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee"
    )
    resultats_paginator = Paginator(resultats_list, 10)
    page_resultats = request.GET.get("page_resultats")
    resultats_page_obj = resultats_paginator.get_page(page_resultats)

    # --- PAGINATION RATIOS IFRS ---
    ratios_list = RatiosIFRS.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee"
    )  # Pas de semestre pour les ratios a priori
    ratios_paginator = Paginator(ratios_list, 10)
    page_ratios = request.GET.get("page_ratios")
    ratios_page_obj = ratios_paginator.get_page(page_ratios)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": acheteur_id,
        "acheteur": acheteur_actuel,
        "acheteurs": tous_les_acheteurs,
        "annee_list": annee_list,
        "annee_list_data": json.dumps(list(Annee.objects.values("id", "annee"))),
        "type_bilan_choices_json": json.dumps(list(TYPE_BILAN_CHOICES)),
        "semestre_choices_json": json.dumps(list(SEMESTRE_CHOICES)),
        # Objets de page paginés pour le template
        "actifs_ifrs_page": actifs_page_obj,
        "passifs_ifrs_page": passifs_page_obj,
        "resultats_ifrs_page": resultats_page_obj,
        "ratios_ifrs_page": ratios_page_obj,
    }

    return render(
        request,
        "main/validateur/acheteur/bilans/irfs/dash_root_manage_acheteur_bilan_irfs_cobac.html",
        context,
    )


########################################################################################################################
#                                                                                                                      #
#  VIEWS END FOR VALIDATEUR                                                                                            #
#                                                                                                                      #
########################################################################################################################




########################################################################################################################
#                                                                                                                      #
#  VIEWS START FOR ANALYSTE                                                                                            #
#                                                                                                                      #
########################################################################################################################
from django.contrib.auth import get_user_model
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Ensure User is correctly imported or defined
User = get_user_model()

#@login_required
def dash_analyste_2(request):
    token = request.GET.get("token")
    logger.debug(f"Token received: {token}")

    if not token:
        logger.error("Token is missing.")
        pass

    try:
        # Attempt to create an AccessToken from the provided token
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        logger.debug(f"User ID extracted from token: {user_id}")

        user = User.objects.get(pk=user_id)
        login(request, user)  # Manually authenticate the user
        logger.debug(f"User {user.username} logged in successfully.")
    except TokenError as e:
        logger.error(f"Token error: {e}")
        # Handle the case where the token is invalid
        return render(request, "main/index.html", {"error": _("Token invalide.")})
    except User.DoesNotExist as e:
        logger.error(f"User not found: {e}")
        # Handle the case where the user does not exist
        return render(request, "main/index.html", {"error": _("Utilisateur non trouvé.")})

    refresh = RefreshToken.for_user(user)
    context = {
        "dash_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/dash_root.html", context)


#@login_required
def dash_analyste_3(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "users_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/dash_root.html", context)


#@login_required
def dash_analyste(request):
    print(f"DEBUG: dash_analyste - Utilisateur authentifié ? {request.user.is_authenticated}")
    if request.user.is_authenticated:
        print(f"DEBUG: dash_analyste - Nom d'utilisateur : {request.user.username}")
        print(f"DEBUG: dash_analyste - Clé de session : {request.session.session_key}")
    else:
        print("DEBUG: dash_analyste - Utilisateur non authentifié malgré #@login_required (devrait rediriger).")

    user = request.user
    context = {
        "users_active": "active",
        "user": user,
        # Supprimez la génération de tokens refresh/access ici comme suggéré précédemment
    }
    return render(request, "main/analyste/dash_root.html", context)


@login_required
def dash_analyste_user(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    context = {
        "users_active": "active",
        "pays_list": pays_list,
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/utilisateur/dash_root_user.html", context)


@login_required
def dash_analyste_pays(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "locations_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/pays/dash_root_pays.html", context)


@login_required
def dash_analyste_province(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    context = {
        "locations_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "pays_list": pays_list,  # Ajouter la liste des pays au contexte
    }
    return render(request, "main/analyste/province/dash_root_province.html", context)


@login_required
def dash_analyste_ville(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    # pays_list = Pays.objects.all()

    # Récupérer tous les pays
    province_list = Province.objects.all()

    context = {
        "locations_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        # 'pays_list': pays_list,  # Ajouter la liste des pays au contexte
        "province_list": province_list,  # Ajouter la liste des pays au contexte
    }
    return render(request, "main/analyste/ville/dash_root_ville.html", context)


@login_required
def dash_analyste_devise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    # Récupérer tous les pays
    province_list = Province.objects.all()

    context = {
        "codification_active": "active",
        "devise_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "pays_list": pays_list,  # Ajouter la liste des pays au contexte
        "province_list": province_list,  # Ajouter la liste des pays au contexte
    }
    return render(request, "main/analyste/devise/dash_root_devise.html", context)


@login_required
def dash_analyste_annee(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les pays
    Pays.objects.all()

    # Récupérer tous les pays
    Province.objects.all()

    context = {
        "codification_active": "active",
        "annee_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/annee/dash_root_annee.html", context)


@login_required
def dash_analyste_coloration(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "coloration_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/coloration/dash_root_coloration.html", context)


@login_required
def dash_analyste_category_nace(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "nace_cat_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/nace/dash_root_category_nace.html", context)


@login_required
def dash_analyste_category_naf(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "naf_cat_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/naf/dash_root_category_naf.html", context)


@login_required
def dash_analyste_code_nace(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les categories nace
    categorie_list = CategoryNaceCode.objects.all()

    context = {
        "codification_active": "active",
        "nace_code_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "categorie_list": categorie_list,
    }
    return render(request, "main/analyste/nace/dash_root_code_nace.html", context)


@login_required
def dash_analyste_code_naf(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les categories nace
    categorie_list = CategoryNafCode.objects.all()

    context = {
        "codification_active": "active",
        "naf_code_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "categorie_list": categorie_list,
    }
    return render(request, "main/analyste/naf/dash_root_code_naf.html", context)


@login_required
def dash_analyste_forme_juridique(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "juridique_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/analyste/juridique/dash_root_forme_juridique.html", context
    )


@login_required
def dash_analyste_domaine(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "domaine_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/domaine/dash_root_domaine.html", context)


@login_required
def dash_analyste_modele_bail(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_bail_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/modele/dash_root_modele_bail.html", context)


@login_required
def dash_analyste_modele_bilan(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_bilan_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/modele/dash_root_modele_bilan.html", context)


@login_required
def dash_analyste_modele_alarme(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_alarme_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/modele/dash_root_modele_alarme.html", context)


@login_required
def dash_analyste_modele_rapport(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_rapport_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/modele/dash_root_modele_rapport.html", context)


@login_required
def dash_analyste_modele_avis_commercial(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_avis_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/analyste/modele/dash_root_modele_avis_commercial.html", context
    )


@login_required
def dash_analyste_modele_relation_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_relation_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/analyste/modele/dash_root_modele_relation_entreprise.html", context
    )


@login_required
def dash_analyste_modele_notation(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_notation_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/modele/dash_root_modele_notation.html", context)


@login_required
def dash_analyste_modele_comportement_paiement(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_cpaiement_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/analyste/modele/dash_root_modele_comportement_paiement.html", context
    )


@login_required
def dash_analyste_modele_comportement_jugement(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_cjugement_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/analyste/modele/dash_root_modele_comportement_jugement.html", context
    )


@login_required
def dash_analyste_modele_information_notation_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "modele_infone_active": "active",
        "modele_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request,
        "main/analyste/modele/dash_root_modele_information_notation_entreprise.html",
        context,
    )


@login_required
def dash_analyste_poste(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupération des domaines
    domaines = DomaineEntreprise.objects.all()

    context = {
        "codification_active": "active",
        "poste_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "domaines": domaines,  # Ajouter les domaines au contexte
    }
    return render(request, "main/analyste/poste/dash_root_poste.html", context)


@login_required
def dash_analyste_category_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "entreprise_cat_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/analyste/entreprise/dash_root_category_entreprise.html", context
    )


@login_required
def dash_analyste_structure_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "entreprise_structure_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(
        request, "main/analyste/structure/dash_root_structure_entreprise.html", context
    )


@login_required
def dash_analyste_statut_entreprise(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "codification_active": "active",
        "entreprise_statut_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/statut/dash_root_statut_entreprise.html", context)


@login_required
def dash_analyste_acheteur(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/acheteur/dash_root_acheteur.html", context)


@login_required
def dash_analyste_add_acheteur(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer tous les categories d'entreprise
    categorie_list = CategorieEntreprise.objects.all()

    # Récupérer tous les formes juridiques
    juridique_list = _translate_juridique_list(request)

    # Récupérer tous les statuts entreprise
    statut_list = _translate_statut_list(request)

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    # Récupérer tous les provinces
    province_list = Province.objects.all()

    # Récupérer tous les villes
    ville_list = Ville.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "categorie_list": categorie_list,
        "juridique_list": juridique_list,
        "statut_list": statut_list,
        "coloration_list": coloration_list,
        "pays_list": pays_list,
        "province_list": province_list,
        "ville_list": ville_list,
    }
    return render(request, "main/analyste/acheteur/dash_root_add_acheteur.html", context)


@login_required
def dash_analyste_edit_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les categories d'entreprise
    categorie_list = CategorieEntreprise.objects.all()

    # Récupérer tous les formes juridiques
    juridique_list = _translate_juridique_list(request)

    # Récupérer tous les statuts entreprise
    statut_list = _translate_statut_list(request)

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    # Récupérer tous les provinces
    province_list = Province.objects.all()

    # Récupérer tous les villes
    ville_list = Ville.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "categorie_list": categorie_list,
        "juridique_list": juridique_list,
        "statut_list": statut_list,
        "coloration_list": coloration_list,
        "pays_list": pays_list,
        "province_list": province_list,
        "ville_list": ville_list,
    }
    return render(request, "main/analyste/acheteur/dash_root_edit_acheteur.html", context)


@login_required
def dash_analyste_manage_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les categories d'entreprise
    categorie_list = CategorieEntreprise.objects.all()

    # Récupérer tous les formes juridiques
    juridique_list = _translate_juridique_list(request)

    # Récupérer tous les statuts entreprise
    statut_list = _translate_statut_list(request)

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    # Récupérer tous les pays
    pays_list = Pays.objects.all()

    # Récupérer tous les provinces
    province_list = Province.objects.all()

    # Récupérer tous les villes
    ville_list = Ville.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "categorie_list": categorie_list,
        "juridique_list": juridique_list,
        "statut_list": statut_list,
        "coloration_list": coloration_list,
        "pays_list": pays_list,
        "province_list": province_list,
        "ville_list": ville_list,
    }
    return render(request, "main/analyste/acheteur/dash_root_manage_acheteur.html", context)


@login_required
def dash_analyste_manage_acheteur_resume(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "devise_list": devise_list,
        "coloration_list": coloration_list,
        "bons_postes_list": bons_postes_list,
    }
    return render(
        request,
        "main/analyste/acheteur/resume/dash_root_manage_acheteur_resume.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_risk_rating(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/analyste/acheteur/riskrating/dash_root_manage_acheteur_risk_rating.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_data_save(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les statuts d'entreprise
    statut_list = _translate_statut_list(request)

    # Récupérer tous les formes juridiques
    juridique_list = _translate_juridique_list(request)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "statut_list": statut_list,
        "juridique_list": juridique_list,
    }
    return render(
        request,
        "main/analyste/acheteur/data/dash_root_manage_acheteur_data_save.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_tendance(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les avis commerciaux
    commercial_list = ModeleAvisCommercial.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "commercial_list": commercial_list,
    }
    return render(
        request,
        "main/analyste/acheteur/tendance/dash_root_manage_acheteur_tendance.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_responsable(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "poste_list": poste_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/analyste/acheteur/responsable/dash_root_manage_acheteur_responsable.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_antecedent(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/analyste/acheteur/antecedent/dash_root_manage_acheteur_antecedent.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_gestion_risque(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/analyste/acheteur/gestion/dash_root_manage_acheteur_gestion_risque.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_membre_conseil(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "poste_list": poste_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/analyste/acheteur/conseil/dash_root_manage_acheteur_membre_conseil.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_composition_capital(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "devise_list": devise_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/analyste/acheteur/composition/dash_root_manage_acheteur_composition_capital.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_actionnaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/analyste/acheteur/actionnaire/dash_root_manage_acheteur_actionnaire.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_opinion_acremac(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/analyste/acheteur/opinion/dash_root_manage_acheteur_opinion_acremac.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_filiale(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "structure_list": structure_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/analyste/acheteur/filiale/dash_root_manage_acheteur_filiale.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_analyse_sectorielle(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "structure_list": structure_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/analyste/acheteur/analyse/dash_root_manage_acheteur_analyse_sectorielle.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_compte_financier(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "bilan_list": bilan_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/analyste/acheteur/finance/dash_root_manage_acheteur_compte_financier.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_operation_historique(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/analyste/acheteur/operation/dash_root_manage_acheteur_operation_historique.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_propriete_actif(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les reference des locaux
    locaux_list = ModeleBail.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "locaux_list": locaux_list,
    }
    return render(
        request,
        "main/analyste/acheteur/propriete/dash_root_manage_acheteur_propriete_actif.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_condition_achat(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/analyste/acheteur/achat/dash_root_manage_acheteur_condition_achat.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_condition_vente(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "paiement_list": paiement_list,
        "jugement_list": jugement_list,
    }
    return render(
        request,
        "main/analyste/acheteur/vente/dash_root_manage_acheteur_condition_vente.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_sommaire_avis(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les colorations
    coloration_list = CouleurCommentaire.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/analyste/acheteur/sommaire/dash_root_manage_acheteur_sommaire_avis.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_advice(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/analyste/acheteur/advice/dash_root_manage_acheteur_advice.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_geopolitic(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/analyste/acheteur/geopolitique/dash_root_manage_acheteur_geopolitic.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_banking(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

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
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "ville_list": ville_list,
        "coloration_list": coloration_list,
    }
    return render(
        request,
        "main/analyste/acheteur/banque/dash_root_manage_acheteur_banking.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_actif_anglais(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/anglais/dash_root_manage_acheteur_actif_anglais.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_passif_anglais(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/anglais/dash_root_manage_acheteur_passif_anglais.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_resultat_anglais(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/anglais/dash_root_manage_acheteur_resultat_anglais.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_actif_classique(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/classique/dash_root_manage_acheteur_actif_classique.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_passif_classique(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/classique/dash_root_manage_acheteur_passif_classique.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_resultat_classique(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/classique/dash_root_manage_acheteur_resultat_classique.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_actif_syscohada(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/syscohada/dash_root_manage_acheteur_actif_syscohada.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_passif_syscohada(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/syscohada/dash_root_manage_acheteur_passif_syscohada.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_resultat_syscohada(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/syscohada/dash_root_manage_acheteur_resultat_syscohada.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_asset_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/bancaire/dash_root_manage_acheteur_asset_bancaire.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_liabilitie_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/bancaire/dash_root_manage_acheteur_liabilitie_bancaire.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_offbalancesheet_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/bancaire/dash_root_manage_acheteur_offbalancesheet_bancaire.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_expense_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/bancaire/dash_root_manage_acheteur_expense_bancaire.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_product_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/bancaire/dash_root_manage_acheteur_product_bancaire.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_compte_financier_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/irfs/dash_root_manage_acheteur_compte_financier_irfs.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_ratio_financier_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/irfs/dash_root_manage_acheteur_ratio_financier_irfs.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_actif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Actif"
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/irfs/dash_root_manage_acheteur_actif_irfs.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_passif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Passif"
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/irfs/dash_root_manage_acheteur_passif_irfs.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_resultat_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Compte de "
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/irfs/dash_root_manage_acheteur_passif_irfs.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_add_actif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Actif"
    )

    # Récupérer tous les actifs financiers irfs
    actif_financier_irfs_list = ValeurCompteIrfs.objects.filter(
        compte__type_compte__icontains="Actif", acheteur__pk=id_acheteur
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
        "actif_financier_irfs_list": actif_financier_irfs_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/irfs/dash_root_manage_acheteur_add_actif_irfs.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_add_passif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer tous les comptes financiers irfs
    compte_financier_irfs_list = CompteFinancierIrfs.objects.filter(
        type_compte__icontains="Passif"
    )

    # Récupérer tous les actifs financiers irfs
    actif_financier_irfs_list = ValeurCompteIrfs.objects.filter(
        compte__type_compte__icontains="Passif", acheteur__pk=id_acheteur
    )

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les devises
    devise_list = Devise.objects.all()

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "annee_list": annee_list,
        "devise_list": devise_list,
        "compte_financier_irfs_list": compte_financier_irfs_list,
        "actif_financier_irfs_list": actif_financier_irfs_list,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/irfs/dash_root_manage_acheteur_add_passif_irfs.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_report_web(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Recuperer les elements du rapports ici !

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/analyste/acheteur/report/dash_root_manage_acheteur_report_web.html",
        context,
    )


@login_required
def dash_analyste_commande(request):
    token = request.GET.get("token")
    if not token:
        pass

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
    client_list = User.objects.filter(
        Q(role__icontains="Client") | Q(role__icontains="client")
    ).order_by("id")

    # Récupérer tous les villes
    ville_list = Ville.objects.all()

    # Récupérer tous les modeles de rapport
    modele_rapport_list = ModeleRapport.objects.all()

    context = {
        "requests_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "devise_list_one": devise_list_one,
        "devise_list_two": devise_list_two,
        "client_list": client_list,
        "ville_list": ville_list,
        "acheteur_list": acheteur_list,
        "modele_rapport_list": modele_rapport_list,
    }
    return render(request, "main/analyste/orders/dash_root_commande.html", context)


@login_required
def dash_analyste_manage_commande(request, commande_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de la commande
    id_commande = commande_id

    # Récupérer tous les categories d'entrepris

    context = {
        "requests_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_commande": id_commande,
    }
    return render(request, "main/analyste/orders/dash_root_manage_commande.html", context)


@login_required
def dash_analyste_alerte(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Supprimer d'abord tous
    # alertes = Alerte.objects.all()
    # alertes.delete()

    # documents = DocumentAlerte.objects.all()
    # documents.delete()

    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/warning/dash_root_alerte.html", context)


@login_required
def dash_analyste_add_alerte(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Créer une nouvelle alerte ici
    random_number = random.randint(100, 9999)
    reference = f"ALT{random_number}"

    # Créer une instance de l'alerte
    # alerte = Alerte.objects.create(
    # reference=reference,
    # objet="Nouvelle alerte",  # Vous pouvez définir un objet par défaut ou le laisser vide
    # content="Contenu de l'alerte"  # Vous pouvez définir un contenu par défaut ou le laisser vide
    # )

    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "reference": reference,  # Passer l'alerte au contexte si nécessaire
    }
    return render(request, "main/analyste/warning/dash_root_add_alerte.html", context)


@login_required
def dash_analyste_edit_new_alerte(request, reference):

    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Get alerte
    alerte = Alerte.objects.get(reference=reference)

    # Get all documents from this alert
    documents = DocumentAlerte.objects.filter(alerte=alerte)

    # Get context
    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "reference": reference,  # Passer l'alerte au contexte si nécessaire
        "alerte": alerte,  # Passer l'alerte au contexte si nécessaire
        "documents": documents,  # Passer l'alerte au contexte si nécessaire
    }

    return render(request, "main/analyste/warning/dash_root_edit_new_alerte.html", context)


@login_required
def dash_analyste_document_alerte(request, reference):

    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Get alerte
    alerte = Alerte.objects.get(reference=reference)

    # Get all documents from this alert
    documents = DocumentAlerte.objects.filter(alerte=alerte)

    # Get context
    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "reference": reference,  # Passer l'alerte au contexte si nécessaire
        "alerte": alerte,  # Passer l'alerte au contexte si nécessaire
        "documents": documents,  # Passer l'alerte au contexte si nécessaire
    }

    return render(
        request, "main/analyste/warning/dash_root_add_document_alerte.html", context
    )


@login_required
def dash_analyste_client_alerte(request, reference):

    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Get all clients
    clients = Client.objects.all()

    # Get alerte
    alerte = Alerte.objects.get(reference=reference)

    # Get all documents from this alert
    documents = DocumentAlerte.objects.filter(alerte=alerte)

    # Get context
    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "reference": reference,  # Passer l'alerte au contexte si nécessaire
        "alerte": alerte,  # Passer l'alerte au contexte si nécessaire
        "documents": documents,  # Passer l'alerte au contexte si nécessaire
        "clients": clients,  # Passer l'alerte au contexte si nécessaire
    }

    return render(request, "main/analyste/warning/dash_root_client_alerte.html", context)


@login_required
def dash_analyste_edit_alerte(request, alerte_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'alerte
    id_alerte = alerte_id

    # Récupérer tous les documents lies a l'alerte
    # document_list = DocumentAlerte.objects.fliter(alerte__pk=id_alerte)

    # Récupérer tous les clients
    # client_list = User.objects.filter(Q(role__icontains="Client") | Q(role__icontains="client")).order_by('id')

    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_alerte": id_alerte,
        # 'document_list': document_list,
        # 'client_list': client_list,
    }
    return render(request, "main/analyste/warning/dash_root_edit_alerte.html", context)


@login_required
def dash_analyste_manage_alerte(request, alerte_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'alerte
    id_alerte = alerte_id

    # Récupérer l'alerte
    alerte = Alerte.objects.filter(id=id_alerte).first()

    # Récupérer tous les documents lies a l'alerte
    document_list = DocumentAlerte.objects.filter(alerte__pk=id_alerte)

    # Récupérer tous les clients
    client_list = User.objects.filter(
        Q(role__icontains="Client") | Q(role__icontains="client")
    ).order_by("id")

    context = {
        "alerts_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_alerte": id_alerte,
        "alerte": alerte,
        "document_list": document_list,
        "client_list": client_list,
    }
    return render(request, "main/analyste/warning/dash_root_manage_alerte.html", context)


@login_required
def dash_analyste_client(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "clients_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/analyste/monitoring/dash_root_client.html", context)


@login_required
def dash_analyste_portefeuille(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "client_list": client_list,
        "acheteur_list": acheteur_list,
    }
    return render(request, "main/analyste/monitoring/dash_root_portefeuille.html", context)


@login_required
def dash_analyste_add_portefeuille(request, portefeuille_id=None):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    # Recuperation des frequences
    frequences = Portefeuille.FREQUENCE_CHOICES

    # Récupérer tous les éléments de surveillance
    surveillances = ElementSurveillance.objects.all()

    # Regrouper les éléments par catégorie
    surveillances_by_category = {}
    for surveillance in surveillances:
        if surveillance.categorie not in surveillances_by_category:
            surveillances_by_category[surveillance.categorie] = []
        surveillances_by_category[surveillance.categorie].append(surveillance)

    # Initialiser selected_elements
    selected_elements = []

    # Si vous modifiez un portefeuille existant
    if portefeuille_id:
        portefeuille = Portefeuille.objects.get(id=portefeuille_id)
        selected_elements = portefeuille.elements_surveillance_actifs.values_list(
            "id", flat=True
        )

    # Passer les éléments groupés et les éléments sélectionnés au template
    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "client_list": client_list,
        "acheteur_list": acheteur_list,
        "frequences": frequences,
        "surveillances_by_category": surveillances_by_category,
        "selected_elements": selected_elements,  # Assurez-vous de définir selected_elements
    }
    return render(
        request, "main/analyste/monitoring/dash_root_add_portefeuille.html", context
    )


@login_required
def dash_analyste_edit_portefeuille(request, portefeuille_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer le portefeuille à modifier
    try:
        portefeuille = Portefeuille.objects.get(id=portefeuille_id)
    except Portefeuille.DoesNotExist:
        return render(
            request, "main/index.html", {"error": _("Portefeuille non trouvé.")}
        )

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs associés à ce portefeuille
    acheteurs_associes = PortefeuilleClient.objects.filter(
        portefeuille=portefeuille
    ).values_list("acheteur_id", flat=True)

    acheteur_list = Acheteur.objects.all()

    # Recuperation des frequences
    frequences = Portefeuille.FREQUENCE_CHOICES

    # Récupérer tous les éléments de surveillance
    surveillances = ElementSurveillance.objects.all()

    # Regrouper les éléments par catégorie
    surveillances_by_category = {}
    for surveillance in surveillances:
        if surveillance.categorie not in surveillances_by_category:
            surveillances_by_category[surveillance.categorie] = []
        surveillances_by_category[surveillance.categorie].append(surveillance)

    # Initialiser selected_elements
    selected_elements = []

    # Si vous modifiez un portefeuille existant
    if portefeuille_id:
        portefeuille = Portefeuille.objects.get(id=portefeuille_id)
        selected_elements = portefeuille.elements_surveillance_actifs.values_list(
            "id", flat=True
        )

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "portefeuille": portefeuille,  # Données du portefeuille à modifier
        "acheteurs_associes": list(
            acheteurs_associes
        ),  # Liste des IDs des acheteurs associés
        "portefeuille_id": portefeuille_id,
        "client_list": client_list,
        "acheteur_list": acheteur_list,
        "frequences": frequences,
        "surveillances_by_category": surveillances_by_category,
        "selected_elements": selected_elements,  # Assurez-vous de définir selected_elements
    }
    return render(
        request, "main/analyste/monitoring/dash_root_edit_portefeuille.html", context
    )


@login_required
def dash_analyste_simulateur_scoring_sb(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "client_list": client_list,
        "acheteur_list": acheteur_list,
    }
    return render(
        request, "main/analyste/simulateur/dash_root_simulateur_scoring_sb.html", context
    )


@login_required
def dash_analyste_element_surveillance(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les clients
    client_list = Client.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    for element in elements:
        ElementSurveillance.objects.get_or_create(
            code_interne=element[
                "code_interne"
            ],  # Utilisez un champ unique pour vérifier les doublons
            defaults={
                "nom": element["nom"],
                "categorie": element["categorie"],
                "sous_categorie": element["sous_categorie"],
            },
        )

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "client_list": client_list,
        "acheteur_list": acheteur_list,
    }
    return render(
        request, "main/analyste/surveillance/dash_root_element_surveillance.html", context
    )


@login_required
def dash_analyste_alerte_log(request):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les alertes
    alerte_list = AlerteLog.objects.all()

    # Récupérer les portefeuilles
    portefeuille_list = Portefeuille.objects.all()

    # Récupérer les acheteurs
    acheteur_list = Acheteur.objects.all()

    # Récupérer les elements
    element_surveille_list = ElementSurveillance.objects.all()

    context = {
        "portefeuilles_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "alerte_list": alerte_list,
        "portefeuille_list": portefeuille_list,
        "acheteur_list": acheteur_list,
        "element_surveille_list": element_surveille_list,
    }
    return render(request, "main/analyste/monitoring/dash_root_alerte_log.html", context)


@login_required
def dash_analyste_certification_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Récupérer les certifications
    certification_list = Certification.objects.all()

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    context = {
        "acheteurs_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "certification_list": certification_list,
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/analyste/acheteur/certification/dash_root_certification_acheteur.html",
        context,
    )


@login_required
def dash_analyste_innovation_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer les innovations
    innovation_list = InnovationDeveloppement.objects.all()

    context = {
        "acheteurs_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "innovation_list": innovation_list,
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/analyste/acheteur/innovation/dash_root_innovation_acheteur.html",
        context,
    )


@login_required
def dash_analyste_strategie_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer les strategies
    strategie_list = StrategiePlanification.objects.all()

    context = {
        "acheteurs_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "strategie_list": strategie_list,
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/analyste/acheteur/strategie/dash_root_strategie_acheteur.html",
        context,
    )


@login_required
def dash_analyste_conformite_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer les conformites
    conformite_list = ConformiteReglementation.objects.all()

    context = {
        "acheteurs_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "conformite_list": conformite_list,
        "id_acheteur": id_acheteur,
    }
    return render(
        request,
        "main/analyste/acheteur/conformite/dash_root_conformite_acheteur.html",
        context,
    )


@login_required
def dash_analyste_manage_acheteur_bilan_actif_bancaire_0(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    # Recuperer l'id de l'acheteur
    id_acheteur = acheteur_id

    # Récupérer l'acheteur actuel pour l'afficher
    acheteur_actuel = Acheteur.objects.get(id=acheteur_id)

    # Récupérer TOUS les acheteurs pour la liste déroulante
    tous_les_acheteurs = Acheteur.objects.all()

    # Récupérer tous les annees
    annee_list = Annee.objects.all()

    # Récupérer tous les actifs de l'acheteur
    actifs = Assets.objects.filter(acheteur_id=acheteur_id)

    # Récupérer tous les passifs de l'acheteur
    passifs = Liabilities.objects.filter(acheteur_id=acheteur_id)

    # Récupérer tous les depenses de l'acheteur
    depenses = Expenses.objects.filter(acheteur_id=acheteur_id)

    # Récupérer tous les produits de l'acheteur
    produits = Products.objects.filter(acheteur_id=acheteur_id)

    # Récupérer tous les hors bilans de l'acheteur
    hors_bilans = OffBalanceSheet.objects.filter(acheteur_id=acheteur_id)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "acheteur": acheteur_actuel,  # Ajouter l'objet acheteur actuel
        "acheteurs": tous_les_acheteurs,  # <--- AJOUTER CETTE LIGNE
        "annee_list": annee_list,
        "actifs": actifs,
        "passifs": passifs,
        "depenses": depenses,
        "produits": produits,
        "hors_bilans": hors_bilans,
    }
    return render(
        request,
        "main/analyste/acheteur/bilans/bancaire/dash_root_manage_acheteur_bilan_actif_bancaire.html",
        context,
    )

    # En haut de votre fichier views.py, ajoutez cet import


@login_required
def dash_analyste_manage_acheteur_bilan_actif_bancaire(request, acheteur_id):
    """
    Vue pour gérer les bilans (Actifs, Passifs, Dépenses, Produits) d'un acheteur,
    avec pagination pour chaque section.
    """
    token = request.GET.get("token")
    if not token:
        pass

    user = request.user
    refresh = RefreshToken.for_user(user)
    id_acheteur = acheteur_id

    try:
        acheteur_actuel = Acheteur.objects.get(id=id_acheteur)
    except Acheteur.DoesNotExist:
        return render(
            request, "main/error_page.html", {"error": _("Acheteur non trouvé.")}
        )

    tous_les_acheteurs = Acheteur.objects.all()
    annee_list = Annee.objects.all()

    # --- PAGINATION DES ACTIFS ---
    actifs_list = Assets.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    actifs_paginator = Paginator(actifs_list, 10)
    page_actifs = request.GET.get("page_actifs")
    actifs_page_obj = actifs_paginator.get_page(page_actifs)

    # --- PAGINATION DES PASSIFS ---
    passifs_list = Liabilities.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    passifs_paginator = Paginator(passifs_list, 10)
    page_passifs = request.GET.get("page_passifs")
    passifs_page_obj = passifs_paginator.get_page(page_passifs)

    # --- PAGINATION DES DÉPENSES ---
    depenses_list = Expenses.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    depenses_paginator = Paginator(depenses_list, 10)
    page_depenses = request.GET.get("page_depenses")
    depenses_page_obj = depenses_paginator.get_page(page_depenses)

    # --- NOUVEAU : PAGINATION DES PRODUITS ---
    produits_list = Products.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    produits_paginator = Paginator(produits_list, 10)
    page_produits = request.GET.get("page_produits")
    produits_page_obj = produits_paginator.get_page(page_produits)

    # --- NOUVEAU : PAGINATION DU HORS BILAN ---
    hors_bilans_list = OffBalanceSheet.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee", "-semestre"
    )
    hors_bilans_paginator = Paginator(hors_bilans_list, 10)
    page_hors_bilans = request.GET.get("page_hors_bilans")
    hors_bilans_page_obj = hors_bilans_paginator.get_page(page_hors_bilans)

    # MODIFIÉ : Mise à jour du contexte pour inclure les produits paginés
    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": id_acheteur,
        "acheteur": acheteur_actuel,
        "acheteurs": tous_les_acheteurs,
        "annee_list": annee_list,
        "annee_list_data": json.dumps(list(Annee.objects.values("id", "annee"))),
        "type_bilan_choices_json": json.dumps(list(TYPE_BILAN_CHOICES)),
        "semestre_choices_json": json.dumps(list(SEMESTRE_CHOICES)),
        # Objets de page paginés pour le template
        "actifs_page": actifs_page_obj,
        "passifs_page": passifs_page_obj,
        "depenses_page": depenses_page_obj,
        "produits_page": produits_page_obj,
        "hors_bilans_page": hors_bilans_page_obj,  # <- NOUVEAU CONTEXTE
    }

    return render(
        request,
        "main/analyste/acheteur/bilans/bancaire/dash_root_manage_acheteur_bilan_actif_bancaire.html",  # Nom de template suggéré
        context,
    )


@login_required
def dash_analyste_manage_acheteur_bilan_irfs_cobac(request, acheteur_id):
    """
    Vue pour gérer les états financiers IFRS (Actif, Passif, Résultat, Ratios)
    d'un acheteur, avec pagination pour chaque section.
    """
    token = request.GET.get("token")
    if not token:
        # Idéalement, rediriger vers une page de connexion ou afficher une erreur claire.
        return render(
            request,
            "main/index.html",
            {"error": _("Token d'authentification manquant.")},
        )

    user = request.user
    refresh = RefreshToken.for_user(user)

    try:
        acheteur_actuel = Acheteur.objects.get(id=acheteur_id)
    except Acheteur.DoesNotExist:
        return render(
            request, "main/error_page.html", {"error": _("Acheteur non trouvé.")}
        )

    # Données communes pour les formulaires
    tous_les_acheteurs = Acheteur.objects.all()
    annee_list = Annee.objects.all()

    # --- PAGINATION ACTIF IFRS ---
    actifs_list = ActifIFRS.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee"
    )
    actifs_paginator = Paginator(actifs_list, 10)  # 10 par page
    page_actifs = request.GET.get("page_actifs")
    actifs_page_obj = actifs_paginator.get_page(page_actifs)

    # --- PAGINATION PASSIF IFRS ---
    passifs_list = PassifIFRS.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee"
    )
    passifs_paginator = Paginator(passifs_list, 10)
    page_passifs = request.GET.get("page_passifs")
    passifs_page_obj = passifs_paginator.get_page(page_passifs)

    # --- PAGINATION COMPTE DE RÉSULTAT IFRS ---
    resultats_list = ResultatIFRS.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee"
    )
    resultats_paginator = Paginator(resultats_list, 10)
    page_resultats = request.GET.get("page_resultats")
    resultats_page_obj = resultats_paginator.get_page(page_resultats)

    # --- PAGINATION RATIOS IFRS ---
    ratios_list = RatiosIFRS.objects.filter(acheteur_id=acheteur_id).order_by(
        "-annee__annee"
    )  # Pas de semestre pour les ratios a priori
    ratios_paginator = Paginator(ratios_list, 10)
    page_ratios = request.GET.get("page_ratios")
    ratios_page_obj = ratios_paginator.get_page(page_ratios)

    context = {
        "acheteur_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "id_acheteur": acheteur_id,
        "acheteur": acheteur_actuel,
        "acheteurs": tous_les_acheteurs,
        "annee_list": annee_list,
        "annee_list_data": json.dumps(list(Annee.objects.values("id", "annee"))),
        "type_bilan_choices_json": json.dumps(list(TYPE_BILAN_CHOICES)),
        "semestre_choices_json": json.dumps(list(SEMESTRE_CHOICES)),
        # Objets de page paginés pour le template
        "actifs_ifrs_page": actifs_page_obj,
        "passifs_ifrs_page": passifs_page_obj,
        "resultats_ifrs_page": resultats_page_obj,
        "ratios_ifrs_page": ratios_page_obj,
    }

    return render(
        request,
        "main/analyste/acheteur/bilans/irfs/dash_root_manage_acheteur_bilan_irfs_cobac.html",
        context,
    )


########################################################################################################################
#                                                                                                                      #
#  VIEWS END FOR ANALYSTE                                                                                              #
#                                                                                                                      #
########################################################################################################################


@login_required
def dash_client(request):
    return render(request, "main/client/dash_client.html")


def verifier_rapport(request, token):
    """Page publique de vérification d'authenticité d'un rapport ACREMAC."""
    from main.models import Acheteur
    from django.core import signing
    acheteur = None
    try:
        acheteur_id = signing.loads(token, salt='rapport-verif-acremac')
        acheteur = Acheteur.objects.select_related('ville', 'pays', 'statut_entreprise').get(pk=acheteur_id)
    except (signing.BadSignature, signing.SignatureExpired, Acheteur.DoesNotExist, Exception):
        acheteur = None
    return render(request, "main/rapport_verification.html", {"acheteur": acheteur})


########################################################################################################################
#  GESTION DES EXPORTATIONS
########################################################################################################################

@login_required
def dash_root_export_listing(request):
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token  = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception:
        access_token = refresh_token = ""
    return render(request, "main/root/exports/dash_root_export_listing.html", {
        "exports_listing_active": "active",
        "access_token":  access_token,
        "refresh_token": refresh_token,
    })


@login_required
def dash_root_export_decompte(request):
    try:
        refresh = RefreshToken.for_user(request.user)
        access_token  = str(refresh.access_token)
        refresh_token = str(refresh)
    except Exception:
        access_token = refresh_token = ""
    from main.models import User as _User
    client_list = _User.objects.filter(role="Client", is_active=True).order_by("username")
    return render(request, "main/root/exports/dash_root_export_decompte.html", {
        "exports_decompte_active": "active",
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "client_list":   client_list,
    })


@login_required
def dash_root_parametrage_mail(request):
    """Page de configuration IMAP et gestion des sources mail."""
    if request.user.role != "Root":
        return redirect_to_login(request.get_full_path())
    refresh = RefreshToken.for_user(request.user)
    return render(request, "main/root/parametrage/dash_root_parametrage_mail.html", {
        "parametrage_active": "active",
        "parametrage_mail_active": "active",
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
    })


@login_required
def dash_root_mail_inbox(request):
    """Boîte de réception des mails entrants et dispatching."""
    if request.user.role != "Root":
        return redirect_to_login(request.get_full_path())
    refresh = RefreshToken.for_user(request.user)
    return render(request, "main/root/parametrage/dash_root_mail_inbox.html", {
        "parametrage_active": "active",
        "parametrage_inbox_active": "active",
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
    })








