import json
import random
import threading

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone  # Ajoutez cette ligne pour importer timezone
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from main.commandes.fetch_bucrep_mails import fetch_and_save_emails
from main.models import User
from main.serializers import *

from django.http import HttpResponse
from django.contrib.auth import get_user_model

from main.models import User  # assurez-vous d'importer correctement votre modèle
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login
from django.db import transaction
from django.http import HttpResponse, JsonResponse

User = get_user_model()

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


# Recuperer les mails ici !
# Exécuter la récupération des emails en tâche de fond
def run_fetch_emails():
    try:
        fetch_and_save_emails()
    except Exception as e:
        print(f"Erreur lors de la récupération des emails : {e}")

    threading.Thread(target=run_fetch_emails, daemon=True).start()


# Create your views here.

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
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_user(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_pays(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_province(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_ville(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_devise(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_annee(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_coloration(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_category_nace(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_category_naf(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_code_nace(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_code_naf(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_forme_juridique(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_domaine(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_modele_bail(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_modele_bilan(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_modele_alarme(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_modele_rapport(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_modele_avis_commercial(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_modele_relation_entreprise(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_modele_notation(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_modele_comportement_paiement(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_modele_comportement_jugement(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_modele_information_notation_entreprise(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_poste(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_category_entreprise(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_structure_entreprise(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_statut_entreprise(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_acheteur(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_add_acheteur(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_edit_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_resume(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_risk_rating(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_data_save(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_tendance(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_responsable(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_antecedent(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_gestion_risque(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_membre_conseil(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_composition_capital(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_actionnaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_opinion_acremac(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_filiale(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_analyse_sectorielle(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_compte_financier(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_operation_historique(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_propriete_actif(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_condition_achat(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_condition_vente(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_sommaire_avis(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_advice(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_geopolitic(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_banking(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_actif_anglais(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_passif_anglais(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_resultat_anglais(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_actif_classique(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_passif_classique(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_resultat_classique(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_actif_syscohada(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_passif_syscohada(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_resultat_syscohada(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_asset_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_liabilitie_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_offbalancesheet_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_expense_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_product_bancaire(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_compte_financier_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_ratio_financier_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_actif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_passif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_resultat_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_add_actif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_add_passif_irfs(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_report_web(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_commande(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_commande(request, commande_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_alerte(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_add_alerte(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_edit_new_alerte(request, reference):

    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_document_alerte(request, reference):

    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_client_alerte(request, reference):

    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_edit_alerte(request, alerte_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_alerte(request, alerte_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_client(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_carnet(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

    user = request.user

    # Génération des tokens d'accès
    refresh = RefreshToken.for_user(user)

    context = {
        "clients_active": "active",
        "user": user,
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return render(request, "main/validateur/monitoring/dash_root_carnet.html", context)


##@login_required
def dash_validateur_portefeuille(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_add_portefeuille(request, portefeuille_id=None):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_edit_portefeuille(request, portefeuille_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_simulateur_scoring_sb(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_element_surveillance(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_alerte_log(request):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_certification_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_innovation_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_strategie_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_conformite_acheteur(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_bilan_actif_bancaire_0(request, acheteur_id):
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
def dash_validateur_manage_acheteur_bilan_actif_bancaire(request, acheteur_id):
    """
    Vue pour gérer les bilans (Actifs, Passifs, Dépenses, Produits) d'un acheteur,
    avec pagination pour chaque section.
    """
    token = request.GET.get("token")
    if not token:
        return render(request, "main/index.html", {"error": _("Token manquant.")})

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


##@login_required
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
