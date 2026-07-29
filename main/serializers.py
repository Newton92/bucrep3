# main/serializers.py
import decimal

from django.core.exceptions import ValidationError
from rest_framework import serializers

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from main.models import *
from django.shortcuts import get_object_or_404
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from main.models import ScoringSansBilanAcheteur
from django.db import transaction
from rest_framework import serializers
import re
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from rest_framework.response import Response  # ⭐⭐ AJOUTEZ CET IMPORT ⭐⭐
from rest_framework import serializers
from main.models import MailInfo, MailAttachment, Commande, Document, Client
import json
from rest_framework import serializers
from main.models import User, Commande, Acheteur, Document, MailInfo, MailAttachment
# ... autres imports

from django.contrib.auth import get_user_model

# Classe de pagination personnalisée
# ===== CLASSES DE PAGINATION =====
class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class NoPagination(PageNumberPagination):
    page_size = None

User = get_user_model()

# Vos serializers ici !
class UserSimpleSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
    
    
class UserSimpleOneSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name()



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "avatar",
            "code_secret",
            "address",
            "activation",
            "auth_a2f",
            "telephone",
            "profession",
            "email_cc",
        ]
        
        
        
# serializers.py
class ProfileUserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    avatar_absolute_url = serializers.SerializerMethodField()  # Nouveau champ
    full_name = serializers.SerializerMethodField()
    password_changed_at = serializers.SerializerMethodField()
    last_login_formatted = serializers.SerializerMethodField()
    date_joined_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name", 
            "full_name", "avatar", "avatar_url", "avatar_absolute_url", "telephone",  # Ajouté avatar_absolute_url
            "profession", "address", "email_cc", "role",
            "last_login", "last_login_formatted",
            "date_joined", "date_joined_formatted",
            "password_changed_at"
        ]
        read_only_fields = ['id', 'username', 'role', 'last_login', 'date_joined']
    
    def get_avatar_url(self, obj):
        """Retourne le chemin relatif de l'avatar"""
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return obj.avatar.url
        return None
    
    def get_avatar_absolute_url(self, obj):
        """Retourne l'URL absolue de l'avatar"""
        if obj.avatar and hasattr(obj.avatar, 'url'):
            request = self.context.get('request')
            if request:
                # En développement avec request
                return request.build_absolute_uri(obj.avatar.url)
            else:
                # En production sans request, construire l'URL
                from django.conf import settings
                
                # Obtenir le domaine
                domain = getattr(settings, 'DOMAIN', '')
                if not domain:
                    # Essayer d'autres sources
                    domain = getattr(settings, 'SITE_DOMAIN', '')
                    if not domain:
                        # Par défaut, utiliser le nom d'hôte actuel
                        domain = getattr(settings, 'BASE_URL', '')
                        if not domain:
                            # Dernier recours
                            import socket
                            domain = f"http://{socket.gethostname()}"
                
                # S'assurer que le domaine se termine par /
                if domain and not domain.endswith('/'):
                    domain = domain + '/'
                
                # Construire l'URL complète
                avatar_path = obj.avatar.url.lstrip('/') if obj.avatar.url.startswith('/') else obj.avatar.url
                return f"{domain}{avatar_path}"
        return f"{getattr(settings, 'DOMAIN', '')}/static/images/default-avatar.png"
    
    def get_full_name(self, obj):
        name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return name if name else obj.username
    
    def get_password_changed_at(self, obj):
        if hasattr(obj, 'password_changed_at') and obj.password_changed_at:
            return obj.password_changed_at.strftime('%d/%m/%Y %H:%M')
        return "Non défini"
    
    def get_last_login_formatted(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%d/%m/%Y %H:%M')
        return "Jamais connecté"
    
    def get_date_joined_formatted(self, obj):
        if obj.date_joined:
            return obj.date_joined.strftime('%d/%m/%Y %H:%M')
        return "Non défini"
    
    def validate_email(self, value):
        # Vérifier que l'email n'est pas déjà utilisé par un autre utilisateur
        user = self.instance
        if user and User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value
    
    def validate_telephone(self, value):
        if value and not value.startswith('+'):
            raise serializers.ValidationError("Le numéro de téléphone doit commencer par + (ex: +241...)")
        return value


class PaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pays
        fields = [
            "id",
            "nom",
            "code",
            "afficher_au_dashboard",
            "is_active",
            "date_creation",
            "date_modification",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pays
        fields = [
            "id",
            "nom",
        ]


class ProvinceSerializer(serializers.ModelSerializer):
    pays = PaysSerializer()  # Utilisez le sérialiseur pour inclure les détails du pays

    class Meta:
        model = Province
        fields = [
            "id",
            "nom",
            "code",
            "pays",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class AddProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = [
            "id",
            "nom",
            "code",
            "pays",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class UpdateProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = [
            "id",
            "nom",
            "code",
            "pays",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class VilleSerializer(serializers.ModelSerializer):
    pays = PaysSerializer(read_only=True)

    class Meta:
        model = Ville
        fields = [
            "id",
            "nom",
            "code",
            "pays",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class RegionSerializer(serializers.ModelSerializer):
    pays = PaysSerializer(read_only=True)

    class Meta:
        model = Region
        fields = ["id", "nom", "code", "pays", "is_active"]
        read_only_fields = ["id"]


class VilleProvinceSerializer(serializers.ModelSerializer):
    province = (
        ProvinceSerializer()
    )  # Utilisez le sérialiseur pour inclure les détails du pays

    class Meta:
        model = Ville
        fields = [
            "id",
            "nom",
            "code",
            "province",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class AddVilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ville
        fields = [
            "id",
            "nom",
            "code",
            "pays",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class UpdateVilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ville
        fields = [
            "id",
            "nom",
            "code",
            "pays",
            "date_creation",
            "date_modification",
            "is_active",
        ]
        read_only_fields = ["id", "date_creation", "date_modification"]


class AnneeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annee
        fields = "__all__"  # Inclut tous les champs du modèle
        read_only_fields = [
            "date_creation",
            "date_modification",
        ]  # Ces champs seront uniquement en lecture


class DeviseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devise
        fields = "__all__"  # Inclut tous les champs du modèle
        read_only_fields = [
            "date_creation",
            "date_modification",
        ]  # Ces champs seront uniquement en lecture


class CouleurCommentaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouleurCommentaire
        fields = ["id", "couleur", "code"]


class AddCategoryNaceCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CategoryNaceCode
        fields = ["id", "code", "libelle", "poids", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class AddSubCategoryNaceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategoryNaceCode
        fields = [
            "id",
            "category",
            "code",
            "libelle",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]



class CategoryNaceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNaceCode
        fields = ["id", "code", "libelle", "poids", "created_at", "updated_at"]
        
        
class EditCategoryNaceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNaceCode
        fields = ["id", "code", "libelle", "poids"]


class EditSubCategoryNaceCodeSerializer(serializers.ModelSerializer):
    category = CategoryNaceCodeSerializer()

    class Meta:
        model = SubCategoryNaceCode
        fields = [
            "id",
            "category",
            "code",
            "libelle",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class SubCategoryNaceCodeSerializer(serializers.ModelSerializer):
    category = CategoryNaceCodeSerializer()

    class Meta:
        model = SubCategoryNaceCode
        fields = [
            "id",
            "category",
            "code",
            "libelle",
            "poids",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CategoryNaceCodeSerializer(serializers.ModelSerializer):
    #subcategories = SubCategoryNaceCodeSerializer(many=True, read_only=True)

    class Meta:
        model = CategoryNaceCode
        fields = [
            "id",
            "code",
            "libelle",
            "poids",
            "active",
            "created_at",
            "updated_at",
            #"subcategories",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AddSubCategoryNafCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategoryNafCode
        fields = [
            "id",
            "category",
            "code",
            "libelle",
            "poids",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CategoryNafCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CategoryNafCode
        fields = [
            "id",
            "code",
            "libelle",
            "active",
            "created_at",
            "updated_at",
            "subcategories",
        ]
        read_only_fields = ["created_at", "updated_at"]


class SubCategoryNafCodeSerializer(serializers.ModelSerializer):
    category = CategoryNafCodeSerializer()

    class Meta:
        model = SubCategoryNafCode
        fields = [
            "id",
            "category",
            "code",
            "libelle",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AddCategoryNafCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CategoryNafCode
        fields = ["id", "code", "libelle", "active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class CategoryNafCodeSerializer(serializers.ModelSerializer):
    subcategories = SubCategoryNafCodeSerializer(many=True, read_only=True)

    class Meta:
        model = CategoryNafCode
        fields = [
            "id",
            "code",
            "libelle",
            "active",
            "created_at",
            "updated_at",
            "subcategories",
        ]
        read_only_fields = ["created_at", "updated_at"]


class EditSubCategoryNafCodeSerializer(serializers.ModelSerializer):
    category = CategoryNafCodeSerializer()

    class Meta:
        model = SubCategoryNafCode
        fields = [
            "id",
            "category",
            "code",
            "libelle",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


# ── Traduction par code DB (source: requête SELECT code, libelle FROM main_formejuridique) ──
FORME_JURIDIQUE_EN = {
    "ASSOC":    "Association",
    "COOP":     "Cooperative",
    "EI":       "Sole proprietorship (EI)",
    "EIRL":     "Single-member limited liability sole proprietorship (EIRL)",
    "FIDUCIE":  "Trust operating a commercial enterprise",
    "GIE":      "Economic interest grouping (GIE)",
    "GP":       "Group of persons",
    "LLP":      "Limited liability partnership (LLP)",
    "LTD":      "Private Limited Company (Ltd)",
    "PARTNER":  "Partnership",
    "PLC":      "Public Limited Company (PLC)",
    "PMSBL":    "Non-profit legal entity",
    "SA":       "Public limited company (SA)",
    "SA-AG":    "Public limited company – general management (SA)",
    "SA-CA":    "Public limited company – board of directors (SA)",
    "SA-PLURI": "Multi-member public limited company (SA)",
    "SARL":     "Multi-member limited liability company (SARL)",
    "SARL-U":   "Single-member limited liability company (SARL-U)",
    "SAS":      "Multi-member simplified joint-stock company (SAS)",
    "SASU":     "Single-member simplified joint-stock company (SASU)",
    "SAU":      "Single-member public limited company (SAU)",
    "SC":       "Civil companies (SC)",
    "SCI":      "Real estate civil company (SCI)",
    "SCP":      "Professional civil company (SCP)",
    "SCS":      "Simple limited partnership (SCS)",
    "SDF":      "De facto company",
    "SE":       "State-owned company (SE)",
    "SEP":      "Joint venture (SEP)",
    "SNC":      "General partnership (SNC)",
    "SPRL":     "Private limited liability company (SPRL)",
    "SSPJ":     "Company without legal personality",
    "SYNDIC":   "Condominium association",
}

# ── Traduction par libelle exact DB (fallback si code absent ou inconnu) ──
FORME_JURIDIQUE_LIBELLE_EN = {
    # ── Libellés standards ──
    "Association":                                                          "Association",
    "Coopérative":                                                          "Cooperative",
    "Entreprise individuelle (EI)":                                         "Sole proprietorship (EI)",
    "Entreprise individuelle à responsabilité limitée (EIRL)":              "Single-member limited liability sole proprietorship (EIRL)",
    "Fiducie exploitant une entreprise à caractère commercial":             "Trust operating a commercial enterprise",
    "Groupement d'intérêt économique (GIE)":                               "Economic interest grouping (GIE)",
    "Groupement de personnes":                                              "Group of persons",
    "Partnership / Partenariat":                                            "Partnership",
    "Partnership à responsabilité limitée (LLP)":                          "Limited liability partnership (LLP)",
    "Personne morale sans but lucratif":                                    "Non-profit legal entity",
    "Private Limited Company (Ltd)":                                        "Private Limited Company (Ltd)",
    "Public Limited Company (PLC)":                                         "Public Limited Company (PLC)",
    "Société à responsabilité limitée pluripersonnelle (SARL)":            "Multi-member limited liability company (SARL)",
    "Société à responsabilité limitée unipersonnelle (SARL U)":            "Single-member limited liability company (SARL-U)",
    "Société anonyme (SA)":                                                 "Public limited company (SA)",
    "Société anonyme avec administration générale (SA)":                   "Public limited company – general management (SA)",
    "Société anonyme avec conseil d'administration (SA)":                  "Public limited company – board of directors (SA)",
    "Société anonyme pluripersonnelle (SA)":                               "Multi-member public limited company (SA)",
    "Société anonyme unipersonnelle (SAU)":                                "Single-member public limited company (SAU)",
    "Société civile immobilière (SCI)":                                    "Real estate civil company (SCI)",
    "Société civile professionnelle (SCP)":                                "Professional civil company (SCP)",
    "Société créée de fait / Société de fait":                             "De facto company",
    "Société d'état (SE)":                                                  "State-owned company (SE)",
    "Société en commandite simple (SCS)":                                  "Simple limited partnership (SCS)",
    "Société en nom collectif (SNC)":                                      "General partnership (SNC)",
    "Société en participation (SEP)":                                      "Joint venture (SEP)",
    "Société par action simplifiée pluripersonnelle (SAS)":               "Multi-member simplified joint-stock company (SAS)",
    "Société par action simplifiée unipersonnelle (SASU)":                "Single-member simplified joint-stock company (SASU)",
    "Société privée à responsabilité limitée (SPRL)":                     "Private limited liability company (SPRL)",
    "Sociétés civiles (SC)":                                               "Civil companies (SC)",
    "Sociétés sans personnalité juridique":                                "Company without legal personality",
    "Syndicat de copropriété":                                             "Condominium association",
    # ── Variantes présentes dans d'anciens enregistrements ──
    "Partenariat":                                                          "Partnership",
    "Partenership à responsibilité limitée":                               "Limited liability partnership (LLP)",
    "Société anonyme avec administration générale":                        "Public limited company – general management (SA)",
    "Société anonyme avec conseil d'administration":                       "Public limited company – board of directors (SA)",
    "Société anonyme pluripersonnelle":                                    "Multi-member public limited company (SA)",
    "Société à Responsabilité Limitée (SARL)":                            "Multi-member limited liability company (SARL)",
    "Société à responsabilité limitée unipersonnelle":                    "Single-member limited liability company (SARL-U)",
    "Société créée de fait et société de fait":                           "De facto company",
    "Société d'État":                                                       "State-owned company (SE)",
    "Société en Participation (SP)":                                       "Joint venture (SEP)",
    "Société par Actions Simplifiée (SAS)":                               "Multi-member simplified joint-stock company (SAS)",
    "Sociétés civiles immobilières":                                       "Real estate civil companies (SCI)",
    "Groupement d'Intérêt Economique (GIE)":                             "Economic interest grouping (GIE)",
    # ── Formes spécifiques au Gabon / CEMAC présentes en base ──
    "Administration publique":                                             "Public Administration",
    "Coopérative de Groupement":                                          "Group Cooperative",
    "Etablissement Public à Caractère Commercial (EPCC)":                 "Public Commercial Establishment (EPCC)",
    "Etablissement Public à Caractère Industriel et Commercial (EPIC)":   "Public Industrial and Commercial Establishment (EPIC)",
    "Filiale":                                                             "Subsidiary",
    "Succursale":                                                          "Branch",
}


# ── Traduction StatutEntreprise : code DB → EN ──
STATUT_ENTREPRISE_EN = {
    "ACTIVE":          "Active Business",
    "INACTIVE":        "Inactive Business",
    "MERGING":         "Companies in merger",
    "MERGED":          "Merged company",
    "NOT_EXIST":       "The company does not exist",
    "NOT_IDENTIFIED":  "The company could not be identified",
    "DORMANT":         "Business is dormant",
    "NOT_LOCATED":     "Unable to locate the company",
    "CEASED":          "Ceased activity",
    "NOT_REGISTERED":  "The company is not registered",
    "NOT_LOCAL_REG":   "The company is not locally registered",
    "LIMITED":         "Limited business activity",
    "NO_VISIBLE_ACT":  "No Business activity visible locally",
    "WINDING_VOL":     "Voluntarily winding up",
    "WINDING_CRED":    "Creditor's voluntarily winding up",
    "WINDING_COMP":    "Compulsorily winding up",
    "RADIATION":       "Radiation",
    "DEREGISTRATION":  "Company in the process of de-registration",
    "DISSOLVED":       "Dissolved",
    "FOLLOW_UP":       "Will follow up",
    "NOT_FOUND":       "Company Not Found",
}

# ── Traduction StatutEntreprise : libelle FR → EN (fallback) ──
STATUT_ENTREPRISE_LIBELLE_EN = {
    # ── Libellés standards ──
    "Entreprise active":                                  "Active Business",
    "Entreprise inactive":                                "Inactive Business",
    "Entreprises en fusion":                              "Companies in merger",
    "Entreprise fusionnée":                               "Merged company",
    "L'entreprise n'existe pas":                          "The company does not exist",
    "L'entreprise n'a pas pu être identifiée":            "The company could not be identified",
    "Entreprise en sommeil":                              "Business is dormant",
    "Impossible de localiser l'entreprise":               "Unable to locate the company",
    "Activité cessée":                                    "Ceased activity",
    "L'entreprise n'est pas immatriculée":                "The company is not registered",
    "L'entreprise n'est pas immatriculée localement":     "The company is not locally registered",
    "Activité commerciale limitée":                       "Limited business activity",
    "Aucune activité commerciale visible localement":     "No Business activity visible locally",
    "Dissolution volontaire":                             "Voluntarily winding up",
    "Dissolution volontaire des créanciers":              "Creditor's voluntarily winding up",
    "Liquidation judiciaire obligatoire":                 "Compulsorily winding up",
    "Radiation":                                          "Radiation",
    "Entreprise en cours de radiation":                   "Company in the process of de-registration",
    "Dissoute":                                           "Dissolved",
    "À suivre":                                           "Will follow up",
    "Entreprise introuvable":                             "Company Not Found",
    # ── Variantes présentes dans d'anciens enregistrements ──
    "Entreprise en fusion":                               "Companies in merger",
    "Entreprise est en sommeil":                          "Business is dormant",
    "L'activité a cessé":                                 "Ceased activity",
    "Dissolution forcée":                                 "Compulsorily winding up",
    "Dissolution volontaire du créancier":                "Creditor's voluntarily winding up",
    "Entreprise en cours de désimmatriculation":          "Company in the process of de-registration",
    "Va suivre":                                          "Will follow up",
    "Pas immatriculée":                                   "The company is not registered",
    "Impossible à localiser":                             "Unable to locate the company",
    "N'existe pas":                                       "The company does not exist",
    "Non identifiée":                                     "The company could not be identified",
}


class FormeJuridiqueSerializer(serializers.ModelSerializer):
    libelle = serializers.SerializerMethodField()

    class Meta:
        model = FormeJuridique
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "poids",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def _get_lang(self):
        from django.utils.translation import get_language
        request = self.context.get("request")
        # 1. Session (most reliable for web clients)
        if request and hasattr(request, "session"):
            lang = request.session.get("django_language", "")
            if lang:
                return lang
        # 2. Cookie
        if request and hasattr(request, "COOKIES"):
            lang = request.COOKIES.get("django_language", "")
            if lang:
                return lang
        # 3. LANGUAGE_CODE set by LocaleMiddleware on the Django request
        if request:
            lang = getattr(request, "LANGUAGE_CODE", "") or getattr(getattr(request, "_request", None), "LANGUAGE_CODE", "")
            if lang:
                return lang
        # 4. Thread-local activated language
        return get_language() or "fr"

    def get_libelle(self, obj):
        lang = self._get_lang()
        if lang.startswith("en") and obj.code:
            return FORME_JURIDIQUE_EN.get(obj.code.strip(), obj.libelle)
        return obj.libelle







class DomaineEntrepriseSerializer(serializers.ModelSerializer):

    class Meta:
        model = DomaineEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AddPosteEntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosteEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "domaine",
            "active",
            "created_at",
            "updated_at",
        ]


class EditPosteEntrepriseSerializer(serializers.ModelSerializer):
    domaine = DomaineEntrepriseSerializer()

    class Meta:
        model = PosteEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "domaine",
            "active",
            "created_at",
            "updated_at",
        ]


class PosteEntrepriseSerializer(serializers.ModelSerializer):
    domaine = DomaineEntrepriseSerializer()

    class Meta:
        model = PosteEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "domaine",
            "active",
            "created_at",
            "updated_at",
        ]


class BaseModeleSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%d/%m/%Y")
    updated_at = serializers.DateTimeField(format="%d/%m/%Y")

    class Meta:
        fields = ["id", "code", "libelle", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ModeleRapportSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleRapport


class ModeleAlarmeSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleAlarme


class ModeleBilanSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleBilan


class ModeleBailSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleBail
        fields = "__all__"
        
        
class AddModeleBailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleBail
        fields = [
            "code",
            "libelle",
            "poids",
        ]

class EditModeleBailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleBail
        fields = [
            "id",
            "code",
            "libelle",
            "poids",
        ]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchModeleBailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleBail
        fields = "__all__"
        
        


class ModeleNotationSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleNotation


class ModeleAvisCommercialSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleAvisCommercial
        fields = "__all__"
        
        
class AddModeleAvisCommercialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAvisCommercial
        fields = [
            "code",
            "libelle",
            "poids",
        ]

class EditModeleAvisCommercialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAvisCommercial
        fields = [
            "id",
            "code",
            "libelle",
            "poids",
        ]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchModeleAvisCommercialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAvisCommercial
        fields = "__all__"
        
   







class ModeleRelationEntrepriseSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleRelationEntreprise


class ModeleInformationNotationEntrepriseSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleInformationNotationEntreprise


class ModeleComportementPaiementSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleComportementPaiement
        fields = "__all__"
        
        
class AddModeleComportementPaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementPaiement
        fields = [
            "code",
            "libelle",
            "poids",
        ]

class EditModeleComportementPaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementPaiement
        fields = [
            "id",
            "code",
            "libelle",
            "poids",
        ]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchModeleComportementPaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementPaiement
        fields = "__all__"
        
        
        
        





class ModeleComportementJugementSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleComportementJugement
              
class AddModeleModeleComportementJugementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementJugement
        fields = [
            "code",
            "libelle",
        ]

class EditModeleModeleComportementJugementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementJugement
        fields = [
            "id",
            "code",
            "libelle",
        ]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchModeleModeleComportementJugementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementJugement
        fields = "__all__"
        
     






class ModeleAgeSocieteSerializer(BaseModeleSerializer):
    class Meta(BaseModeleSerializer.Meta):
        model = ModeleAgeSociete
        fields = "__all__"
              
class AddModeleAgeSocieteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAgeSociete
        fields = [
            "code",
            "libelle",
            "poids",
        ]

class EditModeleAgeSocieteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAgeSociete
        fields = [
            "id",
            "code",
            "libelle",
            "poids",
        ]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchModeleAgeSocieteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAgeSociete
        fields = "__all__"
        
        
        
        


class CategorieEntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class StructureEntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = StructureEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class StatutEntrepriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatutEntreprise
        fields = [
            "id",
            "code",
            "libelle",
            "description",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AcheteurSerializerTwo(serializers.ModelSerializer):
    forme_juridique = FormeJuridiqueSerializer()
    statut_entreprise = StatutEntrepriseSerializer()

    pays = PaysSerializer()
    province = ProvinceSerializer()
    ville = VilleSerializer()

    class Meta:
        model = Acheteur
        fields = [
            "id",
            "code",
            "forme_juridique",
            "activite_principale",
            "nom",
            "sigle",
            "description",
            "date_creation",
            "statut_entreprise",
            "code_postal",
            "fax",
            "boite_postale",
            "site_internet",
            "numero_adresse",
            "rue_adresse",
            "ville",
            "province",
            "pays",
            "couleur_commentaire",
            "commentaire",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

class AcheteurSerializer(serializers.ModelSerializer):
    forme_juridique = FormeJuridiqueSerializer()
    statut_entreprise = StatutEntrepriseSerializer()
    pays = PaysSerializer()
    province = ProvinceSerializer()
    ville = VilleSerializer()

    class Meta:
        model = Acheteur
        fields = [
            "id", "code", "forme_juridique",
            "activite_principale",
            "nom", "sigle", "description", "date_creation",
            "statut_entreprise", "code_postal", "fax", "boite_postale",
            "site_internet", "numero_adresse", "rue_adresse",
            "ville", "province", "pays", "couleur_commentaire",
            "commentaire", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class DomainNameField(serializers.CharField):
    """Champ personnalisé pour les noms de domaine"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault('max_length', 300)
        kwargs.setdefault('allow_blank', True)
        kwargs.setdefault('required', False)
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        """Convertir pour stockage"""
        if data:
            data = str(data).strip()
            # Supprimer https://
            data = re.sub(r'^https?://', '', data)
            # Supprimer slash final
            data = data.rstrip('/')
        return data
    
    def to_representation(self, value):
        """Convertir pour affichage"""
        if value:
            return f"https://{value}"
        return value

class AddAcheteurSerializerTwo(serializers.ModelSerializer):
    # Utiliser notre champ personnalisé
    site_internet = DomainNameField()
    
    class Meta:
        model = Acheteur
        fields = [
            "id", "forme_juridique",
            "activite_principale", "nom", "sigle", "description",
            "date_creation", "statut_entreprise", "code_postal",
            "fax", "boite_postale", "site_internet",
            "numero_adresse", "rue_adresse", "ville", "province",
            "pays", "couleur_commentaire", "commentaire",
            "code"
        ]
        read_only_fields = ["created_at", "updated_at", "code"]

    def validate_site_internet(self, value):
        """Validation simple du site internet"""
        if value:
            value = value.strip()
            value = re.sub(r'^https?://', '', value)
            value = value.rstrip('/')
        return value

    def validate_nom(self, value):
        """Validation du nom"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Le nom doit contenir au moins 2 caractères")
        return value.strip()

    def validate_activite_principale(self, value):
        """Validation de l'activité principale"""
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError("L'activité principale doit contenir au moins 3 caractères")
        return value.strip() if value else value

    def validate_commentaire(self, value):
        """Validation du commentaire"""
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError("Le commentaire doit contenir au moins 10 caractères")
        return value.strip() if value else value

    def validate(self, data):
        """Validation globale"""
        date_creation = data.get('date_creation')
        if date_creation and date_creation > timezone.now().date():
            raise serializers.ValidationError({
                "date_creation": "La date de création ne peut pas être dans le futur"
            })

        ville = data.get('ville')
        province = data.get('province')
        pays = data.get('pays')

        if ville and province:
            if ville.province_id != province.id:
                raise serializers.ValidationError({
                    "ville": "La ville doit appartenir à la province sélectionnée"
                })

        if province and pays:
            if province.pays_id != pays.id:
                raise serializers.ValidationError({
                    "province": "La province doit appartenir au pays sélectionné"
                })

        if not data.get('code'):
            data['code'] = self.generate_code(data.get('nom'), data.get('pays'))

        return data

    def generate_code(self, nom, pays):
        from django.db.models import Max
        if not nom or not pays:
            return ""
        prefix = nom[:3].upper()
        pays_code = pays.code if hasattr(pays, 'code') else 'GA'
        last_code = Acheteur.objects.filter(
            code__startswith=f"ACH-{pays_code}-{prefix}"
        ).aggregate(max_num=Max('code'))
        if last_code['max_num']:
            try:
                last_num = int(last_code['max_num'].split('-')[-1])
                next_num = last_num + 1
            except Exception:
                next_num = 1
        else:
            next_num = 1
        return f"ACH-{pays_code}-{prefix}{next_num:04d}"

    @transaction.atomic
    def create(self, validated_data):
        try:
            acheteur = super().create(validated_data)
            try:
                request = self.context.get('request')
                if request and request.user:
                    from main.models import ActivityLog
                    ActivityLog.objects.create(
                        user=request.user,
                        action_type='CREATE',
                        object_id=acheteur.id,
                        object_type='Acheteur',
                        details=f"Création de l'acheteur '{acheteur.nom}' (ID: {acheteur.id})",
                        ip_address=request.META.get('REMOTE_ADDR', ''),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                    )
            except Exception as log_error:
                import logging
                logging.getLogger(__name__).warning(f"Échec de journalisation: {str(log_error)}")
            return acheteur
        except Exception as e:
            raise serializers.ValidationError({
                "non_field_errors": f"Erreur lors de la création: {str(e)}"
            })

class AddAcheteurSerializer(serializers.ModelSerializer):
    site_internet = DomainNameField()
    
    class Meta:
        model = Acheteur
        fields = [
            "id", "forme_juridique",
            "activite_principale", "nom", "sigle",
            "description", "date_creation", "statut_entreprise",
            "code_postal", "fax", "boite_postale",
            "site_internet", "numero_adresse", "rue_adresse",
            "ville", "province", "pays", "region", "couleur_commentaire",
            "commentaire", "code", "created_by"
        ]
        read_only_fields = ["created_at", "updated_at", "code"]

    def validate_site_internet(self, value):
        if value:
            value = value.strip()
            value = re.sub(r'^https?://', '', value)
            value = value.rstrip('/')
        return value

    def validate_nom(self, value):
        """Validation du nom"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Le nom doit contenir au moins 2 caractères")
        return value.strip()
    
    def validate_activite_principale(self, value):
        """Validation de l'activité principale"""
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError("L'activité principale doit contenir au moins 3 caractères")
        return value.strip() if value else value
    
    def validate_commentaire(self, value):
        """Validation du commentaire"""
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError("Le commentaire doit contenir au moins 10 caractères")
        return value.strip() if value else value
    
    def validate(self, data):
        """Validation globale"""
        # Vérifier la cohérence des dates
        date_creation = data.get('date_creation')
        if date_creation and date_creation > timezone.now().date():
            raise serializers.ValidationError({
                "date_creation": "La date de création ne peut pas être dans le futur"
            })
        
        # Vérifier la cohérence géographique
        ville = data.get('ville')
        province = data.get('province')
        pays = data.get('pays')
        
        if ville and province:
            if ville.province_id != province.id:
                raise serializers.ValidationError({
                    "ville": "La ville doit appartenir à la province sélectionnée"
                })
        
        if province and pays:
            if province.pays_id != pays.id:
                raise serializers.ValidationError({
                    "province": "La province doit appartenir au pays sélectionné"
                })
        
        # Générer un code automatique si non fourni
        if not data.get('code'):
            data['code'] = self.generate_code(data.get('nom'), data.get('pays'))
        
        return data
    
    def generate_code(self, nom, pays):
        """Génère un code unique pour l'acheteur"""
        from django.db.models import Max
        
        if not nom or not pays:
            return ""
        
        # Prendre les 3 premières lettres du nom
        prefix = nom[:3].upper()
        
        # Prendre le code du pays
        pays_code = pays.code if hasattr(pays, 'code') else 'GA'
        
        # Chercher le dernier numéro pour ce préfixe/pays
        last_code = Acheteur.objects.filter(
            code__startswith=f"ACH-{pays_code}-{prefix}"
        ).aggregate(max_num=Max('code'))
        
        if last_code['max_num']:
            try:
                last_num = int(last_code['max_num'].split('-')[-1])
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1
        
        return f"ACH-{pays_code}-{prefix}{next_num:04d}"
    
    @transaction.atomic
    def create(self, validated_data):
        """Création avec gestion des transactions et journalisation"""
        try:
            # Créer l'acheteur
            acheteur = super().create(validated_data)
            
            # Journaliser la création (ne pas bloquer en cas d'échec)
            try:
                request = self.context.get('request')
                if request and request.user:
                    from main.models import ActivityLog
                    
                    ActivityLog.objects.create(
                        user=request.user,
                        action_type='CREATE',  # ou 'ACHETEUR_CREATED'
                        object_id=acheteur.id,
                        object_type='Acheteur',
                        details=f"Création de l'acheteur '{acheteur.nom}' (ID: {acheteur.id})",
                        ip_address=request.META.get('REMOTE_ADDR', ''),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]  # Limiter la taille
                    )
            except Exception as log_error:
                # Log l'erreur mais ne pas bloquer la création
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Échec de journalisation: {str(log_error)}")
            
            return acheteur
            
        except Exception as e:
            import traceback
            print(f"=== ERREUR create() ===")
            print(f"Message: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            print(f"Validated data: {validated_data}")
            
            raise serializers.ValidationError({
                "non_field_errors": f"Erreur lors de la création: {str(e)}"
            })    
    
            

class EditAcheteurSerializerTwo(serializers.ModelSerializer):
    site_internet = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=300,
        validators=[]  # DÉSACTIVER la validation Django
    )
    
    class Meta:
        model = Acheteur
        fields = [
            "id", "forme_juridique",
            "activite_principale", "nom", "sigle", "description",
            "date_creation", "statut_entreprise", "code_postal",
            "fax", "boite_postale", "site_internet",
            "numero_adresse", "rue_adresse", "ville", "province",
            "pays", "couleur_commentaire", "commentaire"
        ]

    def validate_site_internet(self, value):
        if not value:
            return ''
        value = str(value).strip()
        if not value:
            return ''
        value = re.sub(r'^https?://', '', value)
        value = value.rstrip('/')
        value = re.sub(r'^www\.', '', value)
        return value.lower()

    def validate(self, data):
        if 'site_internet' in data:
            data['site_internet'] = self.validate_site_internet(data['site_internet'])
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        try:
            request = self.context.get('request')
            for field, value in validated_data.items():
                setattr(instance, field, value)
            if hasattr(instance, 'site_internet') and instance.site_internet:
                if not instance.site_internet.startswith(('http://', 'https://')):
                    instance.site_internet = f'https://{instance.site_internet}'
            instance.save()
            if request and request.user:
                from main.models import ActivityLog
                ActivityLog.objects.create(
                    user=request.user,
                    action_type='UPDATE',
                    object_id=instance.id,
                    object_type='Acheteur',
                    details=f"Mise à jour de l'acheteur {instance.nom}",
                    ip_address=request.META.get('REMOTE_ADDR', '')
                )
            return instance
        except Exception as e:
            raise serializers.ValidationError({
                'non_field_errors': [f'Erreur lors de la mise à jour: {str(e)}']
            })

class EditAcheteurSerializer(serializers.ModelSerializer):
    site_internet = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=300,
        validators=[]
    )
    
    class Meta:
        model = Acheteur
        fields = [
            "id", "forme_juridique",
            "activite_principale", "nom", "sigle",
            "description", "date_creation", "statut_entreprise",
            "code_postal", "fax", "boite_postale",
            "site_internet", "numero_adresse", "rue_adresse",
            "ville", "province", "pays", "region", "couleur_commentaire",
            "commentaire"
        ]

    def validate_site_internet(self, value):
        if not value:
            return ''
        value = str(value).strip()
        if not value:
            return ''
        value = re.sub(r'^https?://', '', value)
        value = value.rstrip('/')
        value = re.sub(r'^www\.', '', value)
        return value.lower()

    def validate(self, data):
        if 'site_internet' in data:
            data['site_internet'] = self.validate_site_internet(data['site_internet'])
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        try:
            request = self.context.get('request')
            for field, value in validated_data.items():
                setattr(instance, field, value)
            if hasattr(instance, 'site_internet') and instance.site_internet:
                if not instance.site_internet.startswith(('http://', 'https://')):
                    instance.site_internet = f'https://{instance.site_internet}'
            instance.save()
            if request and request.user:
                from main.models import ActivityLog
                ActivityLog.objects.create(
                    user=request.user,
                    action_type='UPDATE',
                    object_id=instance.id,
                    object_type='Acheteur',
                    details=f"Mise à jour de l'acheteur {instance.nom}",
                    ip_address=request.META.get('REMOTE_ADDR', '')
                )
            return instance
        except Exception as e:
            raise serializers.ValidationError({
                'non_field_errors': [f'Erreur lors de la mise à jour: {str(e)}']
            })
  


class GetAcheteurSerializerTwo(serializers.ModelSerializer):
    forme_juridique = FormeJuridiqueSerializer(read_only=True)
    statut_entreprise = StatutEntrepriseSerializer(read_only=True)
    pays = PaysSerializer(read_only=True)
    province = ProvinceSerializer(read_only=True)
    ville = VilleSerializer(read_only=True)
    couleur_commentaire = CouleurCommentaireSerializer(read_only=True)

    site_internet_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Acheteur
        fields = [
            "id", "code", "forme_juridique",
            "activite_principale", "nom", "sigle", "description",
            "date_creation", "statut_entreprise", "code_postal",
            "fax", "boite_postale", "site_internet",
            "site_internet_formatted", "numero_adresse", "rue_adresse",
            "ville", "province", "pays", "couleur_commentaire",
            "commentaire", "created_at", "updated_at"
        ]
        read_only_fields = fields

    def get_site_internet_formatted(self, obj):
        if obj.site_internet:
            return f"https://{obj.site_internet}"
        return None

class GetAcheteurSerializer(serializers.ModelSerializer):
    forme_juridique = FormeJuridiqueSerializer(read_only=True)
    statut_entreprise = StatutEntrepriseSerializer(read_only=True)
    pays = PaysSerializer(read_only=True)
    province = ProvinceSerializer(read_only=True)
    ville = VilleSerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    couleur_commentaire = CouleurCommentaireSerializer(read_only=True)
    
    site_internet_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Acheteur
        fields = [
            "id", "code", "forme_juridique",
            "activite_principale", "nom",
            "sigle", "description", "date_creation", "statut_entreprise",
            "code_postal", "fax", "boite_postale", "site_internet",
            "site_internet_formatted", "numero_adresse", "rue_adresse",
            "ville", "province", "pays", "region", "couleur_commentaire",
            "commentaire", "created_at", "updated_at"
        ]
        read_only_fields = fields

    def get_site_internet_formatted(self, obj):
        if obj.site_internet:
            return f"https://{obj.site_internet}"
        return None



class RiskRatingSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = RiskRating
        fields = "__all__"

    def validate_remboursabilite(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_situation_liquidite(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_performance_rentabilite(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_perspective_secteur(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_qualite_information_analyse(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_existence_garantie(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_terme_financier_duree_pret(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value

    def validate_mesure_propre_soutenir_credit(self, value):
        if value not in [True, False]:
            raise ValidationError("La valeur doit être True ou False.")
        return value


class GetRiskRatingSerializer(serializers.ModelSerializer):

    acheteur = AcheteurSerializer()

    class Meta:
        model = RiskRating
        fields = "__all__"


class AddRiskRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskRating
        fields = [
            "id",
            "acheteur",
            "remboursabilite",
            "situation_liquidite",
            "performance_rentabilite",
            "perspective_secteur",
            "qualite_information_analyse",
            "existence_garantie",
            "terme_financier_duree_pret",
            "mesure_propre_soutenir_credit",
            "cotation_du_risque",
            "indice_du_risque",
            "interpretation",
            "analyse",
        ]
        

class EditRiskRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskRating
        fields = [
            "id",
            "acheteur",
            "remboursabilite",
            "situation_liquidite",
            "performance_rentabilite",
            "perspective_secteur",
            "qualite_information_analyse",
            "existence_garantie",
            "terme_financier_duree_pret",
            "mesure_propre_soutenir_credit",
            "cotation_du_risque",
            "indice_du_risque",
            "interpretation",
            "analyse",
        ]



# START MODEL RESUME

class ResumeSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    devise = DeviseSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = Resume
        fields = "__all__"

    def validate_capital_social(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimale.")
        return value

    def validate_chiffre_affaire(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimale.")
        return value

    def validate_resultat_net(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_capitaux_propres(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimale.")
        return value

    def validate_nombre_employe(self, value):
        if not isinstance(value, (int, float, decimal.Decimal)):
            raise ValidationError("La valeur doit être un nombre décimale.")
        return value


class AddResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = [
            "id",
            "acheteur",
            "devise",
            "capital_social",
            "chiffre_affaire",
            "resultat_net",
            "capitaux_propre",
            "nombre_employe",
            "date_creation",
            "couleur_commentaire",
            "commentaire",
            "created_by",  # Ajouter pour affichage
            "updated_by",  # Ajouter pour affichage
        ]
        read_only_fields = ["created_by", "updated_by"]  # Rendre en lecture seule


class GetResumeSerializer(serializers.ModelSerializer):

    acheteur = AcheteurSerializer()
    devise = DeviseSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = Resume
        fields = "__all__"


class EditResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = [
            "id",
            "acheteur",
            "devise",
            "capital_social",
            "chiffre_affaire",
            "resultat_net",
            "capitaux_propre",
            "nombre_employe",
            "date_creation",
            "couleur_commentaire",
            "commentaire",
            "updated_by",  # Ajouter pour affichage
        ]
        read_only_fields = ["updated_by"]  # Rendre en lecture seule


class ResumeSerializer(serializers.ModelSerializer):
    """Serializer pour les opérations CRUD"""
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    devise_code = serializers.CharField(source='devise.code', read_only=True)
    couleur_code = serializers.CharField(source='couleur_commentaire.code', read_only=True)
    couleur_nom = serializers.CharField(source='couleur_commentaire.couleur', read_only=True)
    
    class Meta:
        model = Resume
        fields = [
            'id', 'acheteur', 'acheteur_nom',
            'devise', 'devise_code',
            'capital_social', 'chiffre_affaire', 'resultat_net',
            'capitaux_propre', 'nombre_employe', 'date_creation',
            'couleur_commentaire', 'couleur_code', 'couleur_nom',
            'commentaire', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'acheteur_nom']
    
    def validate(self, data):
        """Validation globale"""
        # Vérification cohérence des montants
        if (data.get('resultat_net') and data.get('chiffre_affaire') and 
            abs(data['resultat_net']) > abs(data['chiffre_affaire']) * 2):
            raise serializers.ValidationError({
                'resultat_net': "Le résultat net semble incohérent par rapport au chiffre d'affaires."
            })
        
        # Vérification de l'unicité
        if self.instance is None:  # Création
            if Resume.objects.filter(acheteur=data.get('acheteur')).exists():
                raise serializers.ValidationError({
                    'acheteur': "Un résumé existe déjà pour cet acheteur."
                })
        
        return data


class ResumeSummarySerializer(serializers.ModelSerializer):
    """Serializer léger pour l'affichage sommaire"""
    devise = serializers.CharField(source='devise.code')
    resultat_net_classe = serializers.SerializerMethodField()
    
    class Meta:
        model = Resume
        fields = [
            'capital_social', 'chiffre_affaire', 'resultat_net',
            'resultat_net_classe', 'capitaux_propre', 'nombre_employe',
            'devise', 'date_creation'
        ]
    
    def get_resultat_net_classe(self, obj):
        """Classe CSS en fonction du résultat net"""
        if obj.resultat_net is None:
            return 'neutral'
        return 'positive' if obj.resultat_net >= 0 else 'negative'

# END MODEL RESUME




class DonneesEnregistrementSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    forme_juridique = FormeJuridiqueSerializer(read_only=True)

    class Meta:
        model = DonneesEnregistrement
        fields = "__all__"


class GetDonneesEnregistrementSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    forme_juridique = FormeJuridiqueSerializer(read_only=True)

    class Meta:
        model = DonneesEnregistrement
        fields = "__all__"


class AddDonneesEnregistrementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonneesEnregistrement
        fields = [
            "id",
            "acheteur",
            "nom_anterieur",
            "date_creation",
            "forme_juridique",
            "numero_fiscale",
            "commentaire",
        ]


class EditDonneesEnregistrementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonneesEnregistrement
        fields = [
            "id",
            "acheteur",
            "nom_anterieur",
            "date_creation",
            "forme_juridique",
            "numero_fiscale",
            "commentaire",
        ]
        extra_kwargs = {
            'acheteur': {'read_only': True}
        }







class TendanceSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    # ⭐ CORRECTION : Ajouter les champs display
    plus_informations_display = serializers.CharField(
        source='get_plus_informations_display', 
        read_only=True
    )
    alarmes_display = serializers.CharField(
        source='get_alarmes_display', 
        read_only=True
    )

    class Meta:
        model = Tendance
        fields = "__all__"
        extra_fields = ['plus_informations_display', 'alarmes_display']


class GetTendanceSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la lecture des tendances"""
    
    # Ajoutez ces champs si nécessaire
    plus_informations_display = serializers.CharField(source='get_plus_informations_display', read_only=True)
    alarmes_display = serializers.CharField(source='get_alarmes_display', read_only=True)
    
    class Meta:
        model = Tendance
        fields = [
            'id', 'acheteur', 'avis_commercial', 'plus_informations', 
            'presse_media', 'alarmes', 'principaux_concurrent', 'commentaire',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'plus_informations_display', 'alarmes_display'  # Optionnel
        ]
        depth = 1


class AddTendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tendance
        fields = [
            'acheteur', 'avis_commercial',
            'presse_media', 'principaux_concurrent', 'plus_informations',
            'alarmes', 'commentaire'
        ]
    
    def validate_plus_informations(self, value):
        """Valider que la valeur est dans les choix"""
        if value and value not in [choice[0] for choice in LIEN_PLUS_INFORMATIONS_NOTATION_CHOICE]:
            raise serializers.ValidationError(
                f"Valeur invalide pour 'Plus d'informations'"
            )
        return value
    
    def validate_alarmes(self, value):
        """Valider que la valeur est dans les choix"""
        if value and value not in [choice[0] for choice in LIEN_ALARMES_CHOICE]:
            raise serializers.ValidationError(
                f"Valeur invalide pour 'Alarmes'"
            )
        return value


class EditTendanceSerializer(serializers.ModelSerializer):
    # ⭐ SIMPLIFICATION : Supprimer la conversion complexe
    class Meta:
        model = Tendance
        fields = [
            'avis_commercial',
            'presse_media', 'principaux_concurrent', 'plus_informations',
            'alarmes', 'commentaire'
        ]
    
    def validate_plus_informations(self, value):
        if value and value not in [choice[0] for choice in LIEN_PLUS_INFORMATIONS_NOTATION_CHOICE]:
            raise serializers.ValidationError("Valeur invalide pour 'Plus d'informations'")
        return value
    
    def validate_alarmes(self, value):
        if value and value not in [choice[0] for choice in LIEN_ALARMES_CHOICE]:
            raise serializers.ValidationError("Valeur invalide pour 'Alarmes'")
        return value






class CategorieEntrepriseMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieEntreprise
        fields = ['id', 'libelle', 'code']

class FormeJuridiqueMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormeJuridique
        fields = ['id', 'libelle', 'code']

class StatutEntrepriseMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatutEntreprise
        fields = ['id', 'libelle', 'code']

class PaysMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pays
        fields = ['id', 'nom', 'code']

class ProvinceMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ['id', 'nom', 'code']

class VilleMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'code']

class CouleurCommentaireMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouleurCommentaire
        fields = ['id', 'couleur', 'code']

class AcheteurMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer minimal pour les acheteurs
    Utilisé dans les listes et relations
    """
    forme_juridique = FormeJuridiqueMinimalSerializer(read_only=True)
    statut_entreprise = StatutEntrepriseMinimalSerializer(read_only=True)
    pays = PaysMinimalSerializer(read_only=True)
    province = ProvinceMinimalSerializer(read_only=True)
    ville = VilleMinimalSerializer(read_only=True)
    couleur_commentaire = CouleurCommentaireMinimalSerializer(read_only=True)
    
    # Champs calculés
    date_creation_formatted = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    updated_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Acheteur
        fields = [
            'id',
            'code',
            'nom',
            'sigle',
            'activite_principale',
            'date_creation',
            'date_creation_formatted',
            'forme_juridique',
            'statut_entreprise',
            'site_internet',
            'pays',
            'province',
            'ville',
            'couleur_commentaire',
            'created_at',
            'created_at_formatted',
            'updated_at',
            'updated_at_formatted'
        ]
        read_only_fields = fields
    
    def get_date_creation_formatted(self, obj):
        if obj.date_creation:
            return obj.date_creation.strftime('%d/%m/%Y')
        return None
    
    def get_created_at_formatted(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%d/%m/%Y %H:%M')
        return None
    
    def get_updated_at_formatted(self, obj):
        if obj.updated_at:
            return obj.updated_at.strftime('%d/%m/%Y %H:%M')
        return None


class AcheteurDetailSerializer(serializers.ModelSerializer):
    """
    Serializer détaillé pour les acheteurs
    Inclut toutes les informations
    """
    forme_juridique = FormeJuridiqueMinimalSerializer(read_only=True)
    statut_entreprise = StatutEntrepriseMinimalSerializer(read_only=True)
    pays = PaysMinimalSerializer(read_only=True)
    province = ProvinceMinimalSerializer(read_only=True)
    ville = VilleMinimalSerializer(read_only=True)
    couleur_commentaire = CouleurCommentaireMinimalSerializer(read_only=True)

    forme_juridique_id = serializers.PrimaryKeyRelatedField(
        queryset=FormeJuridique.objects.all(),
        source='forme_juridique',
        write_only=True,
        required=False,
        allow_null=True
    )
    statut_entreprise_id = serializers.PrimaryKeyRelatedField(
        queryset=StatutEntreprise.objects.all(),
        source='statut_entreprise',
        write_only=True,
        required=False,
        allow_null=True
    )
    pays_id = serializers.PrimaryKeyRelatedField(
        queryset=Pays.objects.all(),
        source='pays',
        write_only=True,
        required=False,
        allow_null=True
    )
    province_id = serializers.PrimaryKeyRelatedField(
        queryset=Province.objects.all(),
        source='province',
        write_only=True,
        required=False,
        allow_null=True
    )
    ville_id = serializers.PrimaryKeyRelatedField(
        queryset=Ville.objects.all(),
        source='ville',
        write_only=True,
        required=False,
        allow_null=True
    )
    couleur_commentaire_id = serializers.PrimaryKeyRelatedField(
        queryset=CouleurCommentaire.objects.all(),
        source='couleur_commentaire',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Acheteur
        fields = [
            'id',
            'code',
            'nom',
            'sigle',
            'activite_principale',
            'description',
            'date_creation',
            'forme_juridique',
            'forme_juridique_id',
            'statut_entreprise',
            'statut_entreprise_id',
            'email',
            'site_internet',
            'fax',
            'boite_postale',
            'code_postal',
            'numero_adresse',
            'rue_adresse',
            'pays',
            'pays_id',
            'province',
            'province_id',
            'ville',
            'ville_id',
            'couleur_commentaire',
            'couleur_commentaire_id',
            'commentaire',
            'created_at',
            'updated_at'
        ]
    
    def to_internal_value(self, data):
        """
        Convertit les IDs en entiers pour les relations
        """
        if 'forme_juridique' in data and isinstance(data['forme_juridique'], str):
            data['forme_juridique'] = int(data['forme_juridique']) if data['forme_juridique'] else None
        if 'statut_entreprise' in data and isinstance(data['statut_entreprise'], str):
            data['statut_entreprise'] = int(data['statut_entreprise']) if data['statut_entreprise'] else None
        if 'pays' in data and isinstance(data['pays'], str):
            data['pays'] = int(data['pays']) if data['pays'] else None
        if 'province' in data and isinstance(data['province'], str):
            data['province'] = int(data['province']) if data['province'] else None
        if 'ville' in data and isinstance(data['ville'], str):
            data['ville'] = int(data['ville']) if data['ville'] else None
        if 'couleur_commentaire' in data and isinstance(data['couleur_commentaire'], str):
            data['couleur_commentaire'] = int(data['couleur_commentaire']) if data['couleur_commentaire'] else None
        
        return super().to_internal_value(data)
    
    def validate(self, data):
        """
        Validation personnalisée
        """
        # Validation de l'email
        if 'email' in data and data['email']:
            from django.core.validators import validate_email
            try:
                validate_email(data['email'])
            except ValidationError:
                raise serializers.ValidationError({
                    'email': 'Format d\'email invalide'
                })
        
        # Validation de la date
        if 'date_creation' in data and data['date_creation']:
            from datetime import datetime
            if data['date_creation'] > datetime.now().date():
                raise serializers.ValidationError({
                    'date_creation': 'La date de création ne peut pas être dans le futur'
                })
        
        return data

class AcheteurListSerializer(serializers.ModelSerializer):
    """
    Serializer pour les listes d'acheteurs
    Optimisé pour les performances
    """
    statut_entreprise = serializers.StringRelatedField()
    pays = serializers.StringRelatedField()

    class Meta:
        model = Acheteur
        fields = [
            'id',
            'code',
            'nom',
            'sigle',
            'activite_principale',
            'statut_entreprise',
            'pays',
            'created_at'
        ]

class PosteEntrepriseMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosteEntreprise
        fields = ['id', 'libelle', 'code']


class CouleurCommentaireMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouleurCommentaire
        fields = ['id', 'couleur', 'code']

class ResponsableAcheteurListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des responsables"""
    couleur_commentaire = CouleurCommentaireMinimalSerializer()
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = ResponsableAcheteur
        fields = [
            'id',
            'nom',
            'prenom',
            'Sexe',
            'poste',
            'nationalite',
            'couleur_commentaire',
            'commentaire_preview',
            'created_at',
            'created_at_formatted'
        ]
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else ''

class GetResponsableAcheteurSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un responsable"""
    acheteur = AcheteurMinimalSerializer()
    couleur_commentaire = CouleurCommentaireMinimalSerializer()
    
    class Meta:
        model = ResponsableAcheteur
        fields = '__all__'

class AddResponsableAcheteurSerializer(serializers.ModelSerializer):
    """Serializer pour l'ajout d'un responsable"""
    Sexe = serializers.ChoiceField(
        choices=ResponsableAcheteur.STATUS_CHOICES,
        required=True,
        error_messages={
            'required': 'Le sexe est obligatoire',
            'invalid_choice': 'Le sexe doit être "Masculin" ou "Feminin"'
        }
    )
    nom = serializers.CharField(
        max_length=50,
        required=True,
        error_messages={'required': 'Le nom est obligatoire'}
    )
    prenom = serializers.CharField(
        max_length=50,
        required=True,
        error_messages={'required': 'Le prénom est obligatoire'}
    )
    # CharField simple pour éviter le ChoiceField qui évalue les clés gettext_lazy
    # en langue serveur (EN) et rejette les clés françaises soumises par le formulaire
    poste = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)

    class Meta:
        model = ResponsableAcheteur
        fields = [
            'acheteur',
            'nom',
            'prenom',
            'Sexe',
            'poste',
            'nationalite',
            'couleur_commentaire',
            'commentaire'
        ]
    
    def to_internal_value(self, data):
        if 'sexe' in data and 'Sexe' not in data:
            data = data.copy()
            data['Sexe'] = data.get('sexe')
        return super().to_internal_value(data)

    def validate(self, data):
        # Validation de la nationalité
        nationalite = data.get('nationalite', '').strip()
        if len(nationalite) < 2:
            raise serializers.ValidationError({
                'nationalite': 'La nationalité doit contenir au moins 2 caractères'
            })
        
        return data

class EditResponsableAcheteurSerializer(serializers.ModelSerializer):
    """Serializer pour la modification d'un responsable"""
    Sexe = serializers.ChoiceField(
        choices=ResponsableAcheteur.STATUS_CHOICES,
        required=False,
        allow_null=True,
        error_messages={
            'invalid_choice': 'Le sexe doit être "Masculin" ou "Feminin"'
        }
    )
    couleur_commentaire = serializers.PrimaryKeyRelatedField(
        queryset=CouleurCommentaire.objects.all(),
        required=False,
        allow_null=True
    )
    poste = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)

    class Meta:
        model = ResponsableAcheteur
        fields = [
            'nom',
            'prenom',
            'Sexe',
            'poste',
            'nationalite',
            'couleur_commentaire',
            'commentaire'
        ]
    
    def to_internal_value(self, data):
        if 'sexe' in data and 'Sexe' not in data:
            data = data.copy()
            data['Sexe'] = data.get('sexe')
        if 'couleur_commentaire' in data and isinstance(data['couleur_commentaire'], str):
            if data['couleur_commentaire']:
                try:
                    data['couleur_commentaire'] = int(data['couleur_commentaire'])
                except (ValueError, TypeError):
                    raise serializers.ValidationError({
                        'couleur_commentaire': 'ID invalide'
                    })
            else:
                data['couleur_commentaire'] = None
        
        return super().to_internal_value(data)






class AntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = AntecedantsJuridique
        fields = "__all__"


class AntecedantJuridiqueListSerializer(serializers.ModelSerializer):
    couleur_commentaire = serializers.StringRelatedField(
        source='couleur_commentaire.couleur',
        read_only=True
    )
    
    # Ajouter ce champ pour avoir le code couleur dans le frontend
    couleur_commentaire_code = serializers.CharField(
        source='couleur_commentaire.code',
        read_only=True,
        allow_null=True
    )
    
    created_at_formatted = serializers.SerializerMethodField()

    has_faillite = serializers.SerializerMethodField()
    has_jugement = serializers.SerializerMethodField()
    has_redressement = serializers.SerializerMethodField()
    has_autre = serializers.SerializerMethodField()

    # 🔹 exposer Autre sous le nom "autre"
    autre = serializers.CharField(source='Autre', allow_blank=True, allow_null=True)

    class Meta:
        model = AntecedantsJuridique
        fields = [
            'id',
            'dossier_faillite',
            'jugement_cour',
            'antecedant_redressement',
            'autre',
            'couleur_commentaire',
            'couleur_commentaire_code',  # Ajouté
            'commentaire_preview',
            'has_faillite',
            'has_jugement',
            'has_redressement',
            'has_autre',
            'created_at',
            'created_at_formatted',
        ]

    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else ''

    def get_has_faillite(self, obj):
        return bool(obj.dossier_faillite and obj.dossier_faillite.strip())

    def get_has_jugement(self, obj):
        return bool(obj.jugement_cour and obj.jugement_cour.strip())

    def get_has_redressement(self, obj):
        return bool(obj.antecedant_redressement and obj.antecedant_redressement.strip())

    def get_has_autre(self, obj):
        return bool(obj.Autre and obj.Autre.strip())


class GetAntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un antécédent"""
    # Exposer 'Autre' comme 'autre' pour l'API
    autre = serializers.CharField(source='Autre', allow_null=True)
    
    # Ajouter le champ couleur_commentaire_id pour la lecture
    couleur_commentaire_id = serializers.IntegerField(
        source='couleur_commentaire.id',
        read_only=True,
        allow_null=True
    )
    
    # Ajouter aussi le code couleur pour l'affichage
    couleur_commentaire_code = serializers.CharField(
        source='couleur_commentaire.code',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = AntecedantsJuridique
        fields = [
            'id',
            'acheteur',
            'dossier_faillite',
            'jugement_cour',
            'antecedant_redressement',
            'autre',
            'couleur_commentaire',
            'couleur_commentaire_id',  # ID pour la sélection
            'couleur_commentaire_code',  # Code pour l'affichage
            'commentaire',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]


class AddAntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    """Serializer pour l'ajout d'un antécédent - SIMPLIFIÉ"""
    class Meta:
        model = AntecedantsJuridique
        fields = [
            'acheteur',
            'dossier_faillite',
            'jugement_cour',
            'antecedant_redressement',
            'Autre',  # Utiliser 'Autre' directement
            'couleur_commentaire',
            'commentaire'
        ]
    
    def validate(self, data):
        fields_to_check = ['dossier_faillite', 'jugement_cour', 'antecedant_redressement', 'Autre']
        if not any(data.get(field) for field in fields_to_check):
            raise serializers.ValidationError({
                'non_field_errors': 'Au moins un champ (dossier de faillite, jugement, redressement ou autre) doit être rempli.'
            })
        return data
    

class EditAntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    """Serializer pour la modification d'un antécédent"""
    # Ajouter un champ 'autre' qui pointe vers 'Autre'
    autre = serializers.CharField(
        source='Autre',
        required=False,
        allow_blank=True,
        allow_null=True
    )
    
    couleur_commentaire = serializers.PrimaryKeyRelatedField(
        queryset=CouleurCommentaire.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = AntecedantsJuridique
        fields = [
            'dossier_faillite',
            'jugement_cour',
            'antecedant_redressement',
            'autre',  # Utiliser 'autre' ici
            'couleur_commentaire',
            'commentaire'
        ]





class RiskManagmentSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = RiskManagment
        fields = "__all__"


class GetRiskManagmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskManagment
        fields = "__all__"


class AddRiskManagmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskManagment
        fields = [
            "id",
            "acheteur",
            "professionalisme",
            "organisation",
            "turn_over",
            "greve",
            "degradation_qualite",
            "non_respect_condition",
            "couleur_commentaire",
            "commentaire",
        ]
        
        
class EditRiskManagmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskManagment
        fields = [
            "id",
            "acheteur",
            "professionalisme",
            "organisation",
            "turn_over",
            "greve",
            "degradation_qualite",
            "non_respect_condition",
            "couleur_commentaire",
            "commentaire",
        ]






# serializers.py
class FonctionDansLeConseilSerializer(serializers.Serializer):
    """Serializer pour les fonctions dans le conseil"""
    valeur = serializers.CharField()
    libelle = serializers.CharField()


class ConseilAdministrationSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = ConseilAdministration
        fields = "__all__"


class ConseilAdministrationListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des membres du conseil"""
    couleur_commentaire = CouleurCommentaireMinimalSerializer()
    created_at_formatted = serializers.SerializerMethodField()
    adresse_complete = serializers.SerializerMethodField()
    fonction_display = serializers.SerializerMethodField()  # Ajoutez ce champ
    
    class Meta:
        model = ConseilAdministration
        fields = [
            'id',
            'nom',
            'fonction_dans_le_conseil',
            'fonction_display',  # Ajoutez ce champ
            'numero_adresse',
            'rue_adresse',
            'code_postale_adresse',
            'adresse_complete',
            'couleur_commentaire',
            'commentaire',
            'created_at',
            'created_at_formatted'
        ]
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else ''
    
    def get_adresse_complete(self, obj):
        parts = []
        if obj.numero_adresse:
            parts.append(obj.numero_adresse)
        if obj.rue_adresse:
            parts.append(obj.rue_adresse)
        if obj.code_postale_adresse:
            parts.append(obj.code_postale_adresse)
        return ', '.join(parts) if parts else 'Non spécifiée'
    
    def get_fonction_display(self, obj):
        """Retourne le libellé de la fonction"""
        # Utilisez la méthode intégrée de Django
        return obj.get_fonction_dans_le_conseil_display()


class GetConseilAdministrationSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un membre du conseil"""
    acheteur = AcheteurMinimalSerializer()
    couleur_commentaire = CouleurCommentaireMinimalSerializer()
    fonction_display = serializers.SerializerMethodField()  # Ajoutez ce champ
    
    class Meta:
        model = ConseilAdministration
        fields = [
            'id',
            'acheteur',
            'nom',
            'fonction_dans_le_conseil',
            'fonction_display',
            'numero_adresse',
            'rue_adresse',
            'code_postale_adresse',
            'couleur_commentaire',
            'commentaire',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
    
    def get_fonction_display(self, obj):
        """Retourne le libellé de la fonction"""
        if obj.fonction_dans_le_conseil:
            from main.constantes import LISTE_NOUVELLE_FONCTION
            for valeur, libelle in LISTE_NOUVELLE_FONCTION:
                if valeur == obj.fonction_dans_le_conseil:
                    return str(libelle)
        return obj.fonction_dans_le_conseil


class AddConseilAdministrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'ajout d'un membre du conseil"""
    nom = serializers.CharField(
        max_length=100,
        required=True,
        error_messages={'required': 'Le nom est obligatoire'}
    )
    
    # Remplacer le champ par défaut
    fonction_dans_le_conseil = serializers.CharField(required=False)
    
    class Meta:
        model = ConseilAdministration
        fields = [
            'acheteur',
            'nom',
            'fonction_dans_le_conseil',
            'numero_adresse',
            'rue_adresse',
            'code_postale_adresse',
            'couleur_commentaire',
            'commentaire'
        ]
    
    def validate(self, data):
        # Validation de l'adresse
        if data.get('numero_adresse') and len(data['numero_adresse']) > 50:
            raise serializers.ValidationError({
                'numero_adresse': 'Le numéro d\'adresse ne peut pas dépasser 50 caractères'
            })
        
        if data.get('rue_adresse') and len(data['rue_adresse']) > 200:
            raise serializers.ValidationError({
                'rue_adresse': 'La rue ne peut pas dépasser 200 caractères'
            })
        
        if data.get('code_postale_adresse') and len(data['code_postale_adresse']) > 20:
            raise serializers.ValidationError({
                'code_postale_adresse': 'Le code postal ne peut pas dépasser 20 caractères'
            })
        
        return data


class EditConseilAdministrationSerializer(serializers.ModelSerializer):
    """Serializer pour la modification d'un membre du conseil"""
    
    # Remplacer le champ par défaut
    fonction_dans_le_conseil = serializers.CharField(required=False)
    couleur_commentaire = serializers.PrimaryKeyRelatedField(
        queryset=CouleurCommentaire.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = ConseilAdministration
        fields = [
            'nom',
            'fonction_dans_le_conseil',
            'numero_adresse',
            'rue_adresse',
            'code_postale_adresse',
            'couleur_commentaire',
            'commentaire'
        ]
    
    def to_internal_value(self, data):
        # Gérer les IDs pour les relations
        if 'couleur_commentaire' in data and isinstance(data['couleur_commentaire'], str):
            if data['couleur_commentaire']:
                try:
                    data['couleur_commentaire'] = int(data['couleur_commentaire'])
                except (ValueError, TypeError):
                    raise serializers.ValidationError({
                        'couleur_commentaire': 'ID invalide'
                    })
            else:
                data['couleur_commentaire'] = None
        
        return super().to_internal_value(data)








class CompositionCapitalSocialSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    devise = DeviseSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = CompositionCapitalSocial
        fields = "__all__"


class DeviseMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devise
        fields = ['id', 'nom', 'code', 'symbole']


class CouleurCommentaireMinimalSerializer(serializers.ModelSerializer):
    code_couleur = serializers.CharField(read_only=True)
    
    class Meta:
        model = CouleurCommentaire
        fields = ['id', 'couleur', 'code_couleur']


class CompositionCapitalListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des compositions de capital"""
    devise = DeviseMinimalSerializer()
    couleur_commentaire = CouleurCommentaireMinimalSerializer()
    created_at_formatted = serializers.SerializerMethodField()
    updated_at_formatted = serializers.SerializerMethodField()
    pourcentage_libere = serializers.SerializerMethodField()
    
    class Meta:
        model = CompositionCapitalSocial
        fields = [
            'id',
            'emis',
            'publie',
            'libere',
            'pourcentage_libere',
            'devise',
            'couleur_commentaire',
            'commentaire',
            'created_at',
            'created_at_formatted',
            'updated_at',
            'updated_at_formatted'
        ]
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else ''
    
    def get_updated_at_formatted(self, obj):
        return obj.updated_at.strftime('%d/%m/%Y %H:%M') if obj.updated_at else ''
    
    def get_pourcentage_libere(self, obj):
        """Calcule le pourcentage du capital libéré"""
        if obj.emis and obj.emis > 0:
            try:
                return round((obj.libere / obj.emis) * 100, 2)
            except (TypeError, ZeroDivisionError):
                return 0
        return 0


class GetCompositionCapitalSocialSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une composition de capital"""
    acheteur = AcheteurMinimalSerializer()
    devise = DeviseMinimalSerializer()
    couleur_commentaire = CouleurCommentaireMinimalSerializer()
    
    class Meta:
        model = CompositionCapitalSocial
        fields = '__all__'


class AddCompositionCapitalSocialSerializer(serializers.ModelSerializer):
    """Serializer pour l'ajout d'une composition de capital"""
    emis = serializers.DecimalField(
        max_digits=100,
        decimal_places=2,
        required=True,
        min_value=0
    )
    publie = serializers.DecimalField(
        max_digits=100,
        decimal_places=2,
        required=True,
        min_value=0
    )
    libere = serializers.DecimalField(
        max_digits=100,
        decimal_places=2,
        required=True,
        min_value=0
    )
    
    class Meta:
        model = CompositionCapitalSocial
        fields = [
            'acheteur',
            'devise',
            'emis',
            'publie',
            'libere',
            'couleur_commentaire',
            'commentaire'
        ]
    
    def validate(self, data):
        # Validation des montants
        emis = data.get('emis')
        publie = data.get('publie')
        libere = data.get('libere')
        
        # Le capital libéré ne peut pas dépasser le capital émis
        if emis and libere and libere > emis:
            raise serializers.ValidationError({
                'libere': 'Le capital libéré ne peut pas dépasser le capital émis'
            })
        
        # Le capital publié ne peut pas dépasser le capital émis
        if emis and publie and publie > emis:
            raise serializers.ValidationError({
                'publie': 'Le capital publié ne peut pas dépasser le capital émis'
            })
        
        return data


class EditCompositionCapitalSocialSerializer(serializers.ModelSerializer):
    """Serializer pour la modification d'une composition de capital"""
    devise = serializers.PrimaryKeyRelatedField(
        queryset=Devise.objects.all(),
        required=False,
        allow_null=True
    )
    couleur_commentaire = serializers.PrimaryKeyRelatedField(
        queryset=CouleurCommentaire.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = CompositionCapitalSocial
        fields = [
            'devise',
            'emis',
            'publie',
            'libere',
            'couleur_commentaire',
            'commentaire'
        ]
    
    def to_internal_value(self, data):
        # Gérer les IDs pour les relations
        if 'devise' in data and isinstance(data['devise'], str):
            if data['devise']:
                try:
                    data['devise'] = int(data['devise'])
                except (ValueError, TypeError):
                    raise serializers.ValidationError({
                        'devise': 'ID invalide'
                    })
            else:
                data['devise'] = None
        
        if 'couleur_commentaire' in data and isinstance(data['couleur_commentaire'], str):
            if data['couleur_commentaire']:
                try:
                    data['couleur_commentaire'] = int(data['couleur_commentaire'])
                except (ValueError, TypeError):
                    raise serializers.ValidationError({
                        'couleur_commentaire': 'ID invalide'
                    })
            else:
                data['couleur_commentaire'] = None
        
        return super().to_internal_value(data)
    
    def validate(self, data):
        # Validation des montants
        emis = data.get('emis')
        publie = data.get('publie')
        libere = data.get('libere')
        
        # Vérifier les valeurs négatives
        if emis is not None and emis < 0:
            raise serializers.ValidationError({
                'emis': 'Le capital émis ne peut pas être négatif'
            })
        
        if publie is not None and publie < 0:
            raise serializers.ValidationError({
                'publie': 'Le capital publié ne peut pas être négatif'
            })
        
        if libere is not None and libere < 0:
            raise serializers.ValidationError({
                'libere': 'Le capital libéré ne peut pas être négatif'
            })
        
        return data












class CompositionActionSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = CompositionAction
        fields = "__all__"


class CouleurCommentaireMinimalSerializer(serializers.ModelSerializer):
    """Serializer minimal pour les couleurs"""
    class Meta:
        model = CouleurCommentaire
        fields = ['id', 'couleur', 'code']


class CompositionActionListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des actionnaires"""
    couleur_commentaire = CouleurCommentaireMinimalSerializer()
    created_at_formatted = serializers.SerializerMethodField()
    pourcentage_formatted = serializers.SerializerMethodField()
    nom_complet = serializers.SerializerMethodField()
    
    class Meta:
        model = CompositionAction
        fields = [
            'id',
            'nom',
            'prenom',
            'nom_complet',
            'pourcentage',
            'pourcentage_formatted',
            'couleur_commentaire',
            'commentaire',
            'created_at',
            'created_at_formatted',
            'updated_at'
        ]
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else ''
    
    def get_pourcentage_formatted(self, obj):
        return f"{obj.pourcentage}%" if obj.pourcentage else 'Non spécifié'
    
    def get_nom_complet(self, obj):
        return f"{obj.nom} {obj.prenom}".strip()
    
    def get_commentaire_preview(self, obj):
        return obj.commentaire[:100] + '...' if obj.commentaire and len(obj.commentaire) > 100 else obj.commentaire


class GetCompositionActionSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un actionnaire"""
    couleur_commentaire = CouleurCommentaireMinimalSerializer()
    
    class Meta:
        model = CompositionAction
        fields = '__all__'


class AddCompositionActionSerializer(serializers.ModelSerializer):
    """Serializer amélioré pour l'ajout d'un actionnaire"""
    
    nom = serializers.CharField(
        max_length=200,
        required=True,
        trim_whitespace=True,
        error_messages={
            'required': 'Le nom est obligatoire',
            'blank': 'Le nom ne peut pas être vide'
        }
    )
    
    prenom = serializers.CharField(
        max_length=200,
        required=True,
        trim_whitespace=True,
        error_messages={
            'required': 'Le prénom est obligatoire',
            'blank': 'Le prénom ne peut pas être vide'
        }
    )
    
    pourcentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal('0'),
        max_value=Decimal('100'),
        error_messages={
            'invalid': 'Veuillez entrer un nombre valide (ex: 25.50)',
            'min_value': 'Le pourcentage ne peut pas être négatif',
            'max_value': 'Le pourcentage ne peut pas dépasser 100%',
            'max_digits': 'Le pourcentage ne peut avoir que 5 chiffres au total',
            'max_decimal_places': 'Maximum 2 décimales autorisées'
        }
    )
    
    couleur_commentaire = serializers.PrimaryKeyRelatedField(
        queryset=CouleurCommentaire.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = CompositionAction
        fields = [
            'acheteur',
            'nom',
            'prenom',
            'pourcentage',
            'couleur_commentaire',
            'commentaire'
        ]
    
    def validate_nom(self, value):
        """Validation du nom"""
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError("Le nom est obligatoire")
        if len(value) < 2:
            raise serializers.ValidationError("Le nom doit contenir au moins 2 caractères")
        return value
    
    def validate_prenom(self, value):
        """Validation du prénom"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le prénom est obligatoire")
        if len(value) < 2:
            raise serializers.ValidationError("Le prénom doit contenir au moins 2 caractères")
        return value.title()
    
    def validate_pourcentage(self, value):
        """Validation spécifique du pourcentage"""
        if value is None:
            return value
        
        try:
            # S'assurer que c'est un Decimal
            if not isinstance(value, Decimal):
                value = Decimal(str(value))
            
            # Vérifier les limites
            if value < 0:
                raise serializers.ValidationError("Le pourcentage ne peut pas être négatif")
            
            if value > 100:
                raise serializers.ValidationError("Le pourcentage ne peut pas dépasser 100%")
            
            # Vérifier le format décimal
            if value.as_tuple().exponent < -2:
                raise serializers.ValidationError("Maximum 2 décimales autorisées")
            
            return value
            
        except (ValueError, InvalidOperation, TypeError):
            raise serializers.ValidationError("Format de pourcentage invalide. Exemple: 25.50")
    
    def validate(self, attrs):
        """Validation globale"""
        # Normalisation des noms
        if 'nom' in attrs:
            attrs['nom'] = attrs['nom'].strip().upper()
        if 'prenom' in attrs:
            attrs['prenom'] = attrs['prenom'].strip().title()
        
        # Vérification de la longueur du commentaire
        commentaire = attrs.get('commentaire', '')
        if len(commentaire) > 10000:  # Réduit à 10k caractères
            raise serializers.ValidationError({
                'commentaire': 'Le commentaire est trop long (max: 10,000 caractères)'
            })
        
        return attrs
    

class EditCompositionActionSerializer(serializers.ModelSerializer):
    """Serializer amélioré pour l'édition d'un actionnaire"""
    
    nom = serializers.CharField(
        required=False,
        max_length=200,
        trim_whitespace=True,
        error_messages={
            'max_length': 'Le nom ne peut pas dépasser 200 caractères'
        }
    )
    
    prenom = serializers.CharField(
        required=False,
        max_length=200,
        trim_whitespace=True,
        error_messages={
            'max_length': 'Le prénom ne peut pas dépasser 200 caractères'
        }
    )
    
    pourcentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal('0'),
        max_value=Decimal('100'),
        error_messages={
            'invalid': 'Veuillez entrer un nombre valide (ex: 25.50)',
            'min_value': 'Le pourcentage ne peut pas être négatif',
            'max_value': 'Le pourcentage ne peut pas dépasser 100%'
        }
    )
    
    couleur_commentaire = serializers.PrimaryKeyRelatedField(
        queryset=CouleurCommentaire.objects.all(),
        required=False,
        allow_null=True
    )
    
    commentaire = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=10000
    )
    
    class Meta:
        model = CompositionAction
        fields = [
            'nom',
            'prenom',
            'pourcentage',
            'couleur_commentaire',
            'commentaire'
        ]
    
    def validate_nom(self, value):
        """Validation du nom"""
        if value is not None:
            value = value.strip().upper()
            if not value:
                raise serializers.ValidationError("Le nom ne peut pas être vide")
            if len(value) < 2:
                raise serializers.ValidationError("Le nom doit contenir au moins 2 caractères")
        return value
    
    def validate_prenom(self, value):
        """Validation du prénom"""
        if value is not None:
            value = value.strip()
            if not value:
                raise serializers.ValidationError("Le prénom ne peut pas être vide")
            if len(value) < 2:
                raise serializers.ValidationError("Le prénom doit contenir au moins 2 caractères")
            value = value.title()
        return value
    
    def validate_pourcentage(self, value):
        """Validation spécifique du pourcentage"""
        if value is None:
            return value
        
        try:
            # S'assurer que c'est un Decimal
            if not isinstance(value, Decimal):
                value = Decimal(str(value))
            
            # Vérifier les limites
            if value < Decimal('0'):
                raise serializers.ValidationError("Le pourcentage ne peut pas être négatif")
            
            if value > Decimal('100'):
                raise serializers.ValidationError("Le pourcentage ne peut pas dépasser 100%")
            
            # Vérifier le format décimal
            if value.as_tuple().exponent < -2:
                raise serializers.ValidationError("Maximum 2 décimales autorisées")
            
            return value
            
        except (ValueError, InvalidOperation, TypeError):
            raise serializers.ValidationError("Format de pourcentage invalide. Exemple: 25.50")
    
    def validate(self, attrs):
        """Validation globale"""
        # Normalisation des noms si présents
        if 'nom' in attrs and attrs['nom'] is not None:
            attrs['nom'] = attrs['nom'].strip().upper()
        
        if 'prenom' in attrs and attrs['prenom'] is not None:
            attrs['prenom'] = attrs['prenom'].strip().title()
        
        return attrs








class OpinionCreditAcremacSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = OpinionCreditAcremac
        fields = "__all__"


class GetOpinionCreditAcremacSerializer(serializers.ModelSerializer):

    class Meta:
        model = OpinionCreditAcremac
        fields = "__all__"


class AddOpinionCreditAcremacSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpinionCreditAcremac
        fields = [
            "acheteur",
            "risque_de_defaut",
            "risque_de_concentration_credit",
            "risque_de_reputation",
            "risque_pays",
            "risque_de_taux_dinteret",
            "risque_de_liquidite",
            "risque_eleve",
            "risque_moyen",
            "risque_faible",
            "couleur_commentaire",
            "montant_credit_maximum",
            "commentaire",
        ]


class EditOpinionCreditAcremacSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpinionCreditAcremac
        fields = [
            "acheteur",
            "risque_de_defaut",
            "risque_de_concentration_credit",
            "risque_de_reputation",
            "risque_pays",
            "risque_de_taux_dinteret",
            "risque_de_liquidite",
            "risque_eleve",
            "risque_moyen",
            "risque_faible",
            "couleur_commentaire",
            "montant_credit_maximum",
            "commentaire",
        ]








class StructureSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    couleur_commentaire = CouleurCommentaireSerializer()
    type_affiliation_ref = StructureEntrepriseSerializer()

    class Meta:
        model = Structure
        fields = "__all__"


class StructureEntrepriseMinimalSerializer(serializers.ModelSerializer):
    """Serializer minimal pour les structures d'entreprise"""
    class Meta:
        model = StructureEntreprise
        fields = ['id', 'libelle', 'code']


class CouleurCommentaireMinimalSerializer(serializers.ModelSerializer):
    """Serializer minimal pour les couleurs"""
    class Meta:
        model = CouleurCommentaire
        fields = ['id', 'couleur', 'code']


class StructureListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des filiales"""
    couleur_commentaire = CouleurCommentaireMinimalSerializer()
    created_at_formatted = serializers.SerializerMethodField()
    updated_at_formatted = serializers.SerializerMethodField()
    adresse_complete = serializers.SerializerMethodField()
    
    class Meta:
        model = Structure
        fields = [
            'id',
            'nom',
            'type_affiliation',
            'numero_adresse',
            'rue_adresse',
            'code_postale_adresse',
            'adresse_complete',
            'couleur_commentaire',
            'commentaire',
            'created_at',
            'created_at_formatted',
            'updated_at',
            'updated_at_formatted'
        ]
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else ''
    
    def get_updated_at_formatted(self, obj):
        return obj.updated_at.strftime('%d/%m/%Y %H:%M') if obj.updated_at else ''
    
    def get_adresse_complete(self, obj):
        parts = []
        if obj.numero_adresse:
            parts.append(obj.numero_adresse)
        if obj.rue_adresse:
            parts.append(obj.rue_adresse)
        if obj.code_postale_adresse:
            parts.append(obj.code_postale_adresse)
        return ', '.join(parts) if parts else 'Adresse non spécifiée'
    
    def get_commentaire_preview(self, obj):
        return obj.commentaire[:100] + '...' if obj.commentaire and len(obj.commentaire) > 100 else obj.commentaire or ''


class GetStructureSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une filiale"""
    couleur_commentaire = CouleurCommentaireMinimalSerializer()
    
    class Meta:
        model = Structure
        fields = '__all__'


class AddStructureSerializer(serializers.ModelSerializer):
    """Serializer pour l'ajout d'une filiale"""
    
    nom = serializers.CharField(
        max_length=200,
        required=True,
        trim_whitespace=True,
        error_messages={
            'required': 'Le nom est obligatoire',
            'blank': 'Le nom ne peut pas être vide',
            'max_length': 'Le nom ne peut pas dépasser 200 caractères'
        }
    )
    
    type_affiliation = serializers.ChoiceField(
        choices=LIEN_ENTREPRISE_CHOICE,
        required=True,
        error_messages={
            'required': 'Le type d\'affiliation est obligatoire',
            'invalid_choice': 'Type d\'affiliation invalide'
        }
    )
    
    
    couleur_commentaire = serializers.PrimaryKeyRelatedField(
        queryset=CouleurCommentaire.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Structure
        fields = [
            'acheteur',
            'nom',
            'type_affiliation',
            'numero_adresse',
            'rue_adresse',
            'code_postale_adresse',
            'couleur_commentaire',
            'commentaire'
        ]
    
    def validate_nom(self, value):
        """Validation du nom"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le nom est obligatoire")
        if len(value) < 2:
            raise serializers.ValidationError("Le nom doit contenir au moins 2 caractères")
        return value
    
    def validate_numero_adresse(self, value):
        """Validation du numéro d'adresse"""
        if value and len(value) > 50:
            raise serializers.ValidationError("Le numéro d'adresse ne peut pas dépasser 50 caractères")
        return value.strip() if value else value
    
    def validate_rue_adresse(self, value):
        """Validation de la rue"""
        if value and len(value) > 200:
            raise serializers.ValidationError("La rue ne peut pas dépasser 200 caractères")
        return value.strip() if value else value
    
    def validate_code_postale_adresse(self, value):
        """Validation du code postal"""
        if value and len(value) > 20:
            raise serializers.ValidationError("Le code postal ne peut pas dépasser 20 caractères")
        return value.strip() if value else value
    
    def validate(self, attrs):
        """Validation globale"""
        # Vérification de l'adresse complète
        if attrs.get('numero_adresse') or attrs.get('rue_adresse'):
            if not attrs.get('numero_adresse'):
                raise serializers.ValidationError({
                    'numero_adresse': 'Le numéro d\'adresse est requis si vous spécifiez une adresse'
                })
            if not attrs.get('rue_adresse'):
                raise serializers.ValidationError({
                    'rue_adresse': 'La rue est requise si vous spécifiez une adresse'
                })
        
        # Validation de la longueur du commentaire
        commentaire = attrs.get('commentaire', '')
        if len(commentaire) > 10000:
            raise serializers.ValidationError({
                'commentaire': 'Le commentaire est trop long (max: 10,000 caractères)'
            })
        
        return attrs


class EditStructureSerializer(serializers.ModelSerializer):
    """Serializer pour la modification d'une filiale"""
    
    nom = serializers.CharField(
        required=False,
        max_length=200,
        trim_whitespace=True
    )
    
    type_affiliation = serializers.ChoiceField(
        choices=[
            ('Société - mère', 'Société - mère'),
            ('Filiale', 'Filiale'),
            ('Subsidiary', 'Subsidiary'),
            ('Société Sœur', 'Société Sœur'),
            ('La holding', 'La holding'),
            ('Le groupe de sociétés', 'Le groupe de sociétés'),
            ('Société de gestion', 'Société de gestion'),
        ],
        required=False
    )
    
    
    couleur_commentaire = serializers.PrimaryKeyRelatedField(
        queryset=CouleurCommentaire.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Structure
        fields = [
            'nom',
            'type_affiliation',
            'numero_adresse',
            'rue_adresse',
            'code_postale_adresse',
            'couleur_commentaire',
            'commentaire'
        ]
    
    def validate_nom(self, value):
        """Validation du nom"""
        if value is not None:
            value = value.strip()
            if not value:
                raise serializers.ValidationError("Le nom ne peut pas être vide")
            if len(value) < 2:
                raise serializers.ValidationError("Le nom doit contenir au moins 2 caractères")
        return value
    
    def validate(self, attrs):
        """Validation globale"""
        # Validation partielle de l'adresse
        if attrs.get('numero_adresse') or attrs.get('rue_adresse'):
            if attrs.get('numero_adresse') and not attrs.get('rue_adresse'):
                # Si on a un numéro mais pas de rue, c'est OK (mise à jour partielle)
                pass
            elif attrs.get('rue_adresse') and not attrs.get('numero_adresse'):
                # Si on a une rue mais pas de numéro, c'est OK (mise à jour partielle)
                pass
        
        return attrs













class AnalyseSectorielleSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = AnalyseSectorielle
        fields = "__all__"


class GetAnalyseSectorielleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyseSectorielle
        fields = "__all__"


class AddAnalyseSectorielleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyseSectorielle
        fields = ["acheteur", "couleur_commentaire", "commentaire", "impact_covid_19"]


class EditAnalyseSectorielleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyseSectorielle
        fields = ["acheteur", "couleur_commentaire", "commentaire", "impact_covid_19"]
















class CompteFinancierSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer(read_only=True)
    couleur_commentaire = CouleurCommentaireSerializer(read_only=True)

    class Meta:
        model = CompteFinancier
        fields = "__all__"
        depth = 1


class GetCompteFinancierSerializer(serializers.ModelSerializer):
    couleur_commentaire = CouleurCommentaireSerializer(read_only=True)
    
    class Meta:
        model = CompteFinancier
        fields = [
            "id", 
            "cabinet", 
            "requis_pour_deposer", 
            "credibilite_cabinet", 
            "source", 
            "presentation",
            "date_compte", 
            "date_fin", 
            "date_compte_n_moins_un", 
            "date_fin_n_moins_un",
            "date_compte_n_moins_deux", 
            "date_fin_n_moins_deux",
            "type_compte", 
            "devise", 
            "type_bilan",
            "couleur_commentaire", 
            "commentaire",
            "created_at", 
            "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]


class AddCompteFinancierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancier
        fields = [
            "acheteur", 
            "cabinet", 
            "requis_pour_deposer", 
            "credibilite_cabinet", 
            "source", 
            "presentation",
            "date_compte", 
            "date_fin", 
            "date_compte_n_moins_un", 
            "date_fin_n_moins_un",
            "date_compte_n_moins_deux", 
            "date_fin_n_moins_deux",
            "type_compte", 
            "devise", 
            "type_bilan",
            "couleur_commentaire", 
            "commentaire"
        ]


class EditCompteFinancierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancier
        fields = [
            "cabinet", 
            "requis_pour_deposer", 
            "credibilite_cabinet", 
            "source", 
            "presentation",
            "date_compte", 
            "date_fin", 
            "date_compte_n_moins_un", 
            "date_fin_n_moins_un",
            "date_compte_n_moins_deux", 
            "date_fin_n_moins_deux",
            "type_compte", 
            "devise", 
            "type_bilan",
            "couleur_commentaire", 
            "commentaire"
        ]










class ListeImportationSerializer(serializers.ModelSerializer):
    # Ajoutez cette ligne pour inclure libelle
    libelle = serializers.CharField(read_only=True)
    
    class Meta:
        model = ListeImportation
        fields = ['id', 'libelle']
    
    def to_representation(self, instance):
        # S'assurer que libelle est toujours présent
        representation = super().to_representation(instance)
        representation['libelle'] = representation.get('libelle', '')
        return representation


class OperationEtHistoriqueSerializer(serializers.ModelSerializer):
    acheteur_nom = serializers.SerializerMethodField()
    importation_list = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    updated_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = OperationEtHistorique
        fields = [
            'id',
            'acheteur',
            'acheteur_nom',
            'commentaire_ratios',
            'description_complete_activite',
            'importation',
            'importation_list',
            'historique',
            'created_at',
            'updated_at',
            'created_at_formatted',
            'updated_at_formatted'
        ]
    
    def get_acheteur_nom(self, obj):
        return obj.acheteur.nom if obj.acheteur else None
    
    def get_importation_list(self, obj):
        # Utilisez libelle au lieu de nom
        return [{'id': imp.id, 'libelle': str(imp)} for imp in obj.importation.all()]
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else None
    
    def get_updated_at_formatted(self, obj):
        return obj.updated_at.strftime('%d/%m/%Y %H:%M') if obj.updated_at else None


class GetOperationEtHistoriqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationEtHistorique
        fields = "__all__"


class OperationEtHistoriqueCreateSerializer(serializers.ModelSerializer):
    importation = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ListeImportation.objects.all(),
        required=False
    )
    
    class Meta:
        model = OperationEtHistorique
        fields = [
            'commentaire_ratios',
            'description_complete_activite',
            'importation',
            'historique',
            'acheteur'
        ]


class OperationEtHistoriqueUpdateSerializer(serializers.ModelSerializer):
    importation = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ListeImportation.objects.all(),
        required=False
    )
    
    class Meta:
        model = OperationEtHistorique
        fields = [
            'commentaire_ratios',
            'description_complete_activite',
            'importation',
            'historique'
        ]










class LocauxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locaux
        fields = ['id', 'nom']


class ProprieteEtActifSerializer(serializers.ModelSerializer):
    acheteur_nom = serializers.SerializerMethodField()
    locaux_list = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    updated_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = ProprieteEtActif
        fields = [
            'id',
            'acheteur',
            'acheteur_nom',
            'branche',
            'locaux',
            'locaux_list',
            'created_at',
            'updated_at',
            'created_at_formatted',
            'updated_at_formatted'
        ]
    
    def get_acheteur_nom(self, obj):
        return obj.acheteur.nom if obj.acheteur else None
    
    def get_locaux_list(self, obj):
        return [{'id': local.id, 'nom': local.nom} for local in obj.locaux.all()]
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else None
    
    def get_updated_at_formatted(self, obj):
        return obj.updated_at.strftime('%d/%m/%Y %H:%M') if obj.updated_at else None


class GetProprieteEtActifSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProprieteEtActif
        fields = "__all__"


class AddProprieteEtActifSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProprieteEtActif
        fields = ["acheteur", "locaux", "locaux_ref", "branche"]


class EditProprieteEtActifSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProprieteEtActif
        fields = ["acheteur", "locaux", "locaux_ref", "branche"]
        
        
class ProprieteEtActifCreateSerializer(serializers.ModelSerializer):
    locaux = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Locaux.objects.all(),
        required=False
    )
    
    class Meta:
        model = ProprieteEtActif
        fields = [
            'branche',
            'locaux',
            'acheteur'
        ]


class ProprieteEtActifUpdateSerializer(serializers.ModelSerializer):
    locaux = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Locaux.objects.all(),
        required=False
    )
    
    class Meta:
        model = ProprieteEtActif
        fields = [
            'branche',
            'locaux'
        ]











class ConditionAchatSerializer(serializers.ModelSerializer):
    acheteur_nom = serializers.SerializerMethodField()
    local_list = serializers.SerializerMethodField()
    importation_list = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    updated_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = ConditionAchat
        fields = [
            'id',
            'acheteur',
            'acheteur_nom',
            'local',
            'local_list',
            'importation',
            'importation_list',
            'les_clients',
            'fournisseur',
            'created_at',
            'updated_at',
            'created_at_formatted',
            'updated_at_formatted'
        ]
    
    def get_acheteur_nom(self, obj):
        return obj.acheteur.nom if obj.acheteur else None
    
    def get_local_list(self, obj):
        return [{'id': item.id, 'nom': item.nom} for item in obj.local.all()]
    
    def get_importation_list(self, obj):
        return [{'id': item.id, 'nom': item.nom} for item in obj.importation.all()]
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else None
    
    def get_updated_at_formatted(self, obj):
        return obj.updated_at.strftime('%d/%m/%Y %H:%M') if obj.updated_at else None


class GetConditionAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionAchat
        fields = "__all__"


class AddConditionAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionAchat
        fields = ["acheteur", "local", "importation", "les_clients", "fournisseur"]


class EditConditionAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionAchat
        fields = ["acheteur", "local", "importation", "les_clients", "fournisseur"]
        

class ConditionAchatCreateSerializer(serializers.ModelSerializer):
    local = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ListeConditionAchat.objects.all(),
        required=False
    )
    importation = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ListeConditionAchat.objects.all(),
        required=False
    )
    
    class Meta:
        model = ConditionAchat
        fields = [
            'les_clients',
            'fournisseur',
            'local',
            'importation',
            'acheteur'
        ]


class ConditionAchatUpdateSerializer(serializers.ModelSerializer):
    local = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ListeConditionAchat.objects.all(),
        required=False
    )
    importation = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ListeConditionAchat.objects.all(),
        required=False
    )
    
    class Meta:
        model = ConditionAchat
        fields = [
            'les_clients',
            'fournisseur',
            'local',
            'importation'
        ]


class ListeConditionAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListeConditionAchat
        fields = ['id', 'nom']











class ConditionDeVenteSerializer(serializers.ModelSerializer):
    acheteur_nom = serializers.SerializerMethodField()
    local_list = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    updated_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = ConditionDeVente
        fields = [
            'id',
            'acheteur',
            'acheteur_nom',
            'local',
            'local_list',
            'recouvrement_de_dette_jugement',
            'comportement_de_paiement',
            'created_at',
            'updated_at',
            'created_at_formatted',
            'updated_at_formatted'
        ]
    
    def get_acheteur_nom(self, obj):
        return obj.acheteur.nom if obj.acheteur else None
    
    def get_local_list(self, obj):
        return [{'id': item.id, 'nom': item.nom} for item in obj.local.all()]
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else None
    
    def get_updated_at_formatted(self, obj):
        return obj.updated_at.strftime('%d/%m/%Y %H:%M') if obj.updated_at else None


class GetConditionDeVenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionDeVente
        fields = "__all__"


class AddConditionDeVenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionDeVente
        fields = [
            "acheteur",
            "local",
            "recouvrement_de_dette_jugement",
            "recouvrement_de_dette_jugement_ref",
            "comportement_de_paiement",
            "comportement_de_paiement_ref",
        ]


class EditConditionDeVenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionDeVente
        fields = [
            "acheteur",
            "local",
            "recouvrement_de_dette_jugement",
            "recouvrement_de_dette_jugement_ref",
            "comportement_de_paiement",
            "comportement_de_paiement_ref",
        ]
        

class ConditionDeVenteCreateSerializer(serializers.ModelSerializer):
    local = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ListeConditionVente.objects.all(),
        required=False
    )
    
    class Meta:
        model = ConditionDeVente
        fields = [
            'recouvrement_de_dette_jugement',
            'comportement_de_paiement',
            'local',
            'acheteur'
        ]


class ConditionDeVenteUpdateSerializer(serializers.ModelSerializer):
    local = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ListeConditionVente.objects.all(),
        required=False
    )
    
    class Meta:
        model = ConditionDeVente
        fields = [
            'recouvrement_de_dette_jugement',
            'comportement_de_paiement',
            'local'
        ]


class ListeConditionVenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListeConditionVente
        fields = ['id', 'nom']















class SommaireEtAvisSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer(read_only=True)
    couleur_commentaire = CouleurCommentaireSerializer(read_only=True)

    class Meta:
        model = SommaireEtAvis
        fields = "__all__"
        depth = 1


class GetSommaireEtAvisSerializer(serializers.ModelSerializer):
    couleur_commentaire = CouleurCommentaireSerializer(read_only=True)
    
    class Meta:
        model = SommaireEtAvis
        fields = ["id", "commentaire", "couleur_commentaire", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class AddSommaireEtAvisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SommaireEtAvis
        fields = ["acheteur", "couleur_commentaire", "commentaire"]


class EditSommaireEtAvisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SommaireEtAvis
        fields = ["couleur_commentaire", "commentaire"]









class AdviceSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer(read_only=True)

    class Meta:
        model = Advice
        fields = "__all__"
        depth = 1


class GetAdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = [
            "id", 
            "points_forts", 
            "points_faibles", 
            "dynamisme_court_terme", 
            "dynamisme_long_terme", 
            "risque_potentiel_court_terme",
            "created_at", 
            "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]


class AddAdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = [
            "acheteur", 
            "points_forts", 
            "points_faibles", 
            "dynamisme_court_terme", 
            "dynamisme_long_terme", 
            "risque_potentiel_court_terme"
        ]


class EditAdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = [
            "points_forts", 
            "points_faibles", 
            "dynamisme_court_terme", 
            "dynamisme_long_terme", 
            "risque_potentiel_court_terme"
        ]












class GeopoliticsSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer(read_only=True)

    class Meta:
        model = Geopolitics
        fields = "__all__"
        depth = 1


class GetGeopoliticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geopolitics
        fields = [
            "id", 
            "stabilite_politique", 
            "etat_droit", 
            "efficacite", 
            "qualite", 
            "liberte_expression",
            "donnees_politiques", 
            "donnees_economiques",
            "created_at", 
            "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]


class AddGeopoliticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geopolitics
        fields = [
            "acheteur", 
            "stabilite_politique", 
            "etat_droit", 
            "efficacite", 
            "qualite", 
            "liberte_expression",
            "donnees_politiques", 
            "donnees_economiques"
        ]


class EditGeopoliticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geopolitics
        fields = [
            "stabilite_politique", 
            "etat_droit", 
            "efficacite", 
            "qualite", 
            "liberte_expression",
            "donnees_politiques", 
            "donnees_economiques"
        ]







class BanquierSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()  # Utilisez un sérialiseur imbriqué pour l'acheteur
    ville = VilleSerializer()
    couleur_commentaire = CouleurCommentaireSerializer()

    class Meta:
        model = Banquier
        fields = "__all__"


class VilleMinimalSerializer(serializers.ModelSerializer):
    """Serializer minimal pour les villes"""
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'code']


class BanquierListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des banquiers"""
    ville = VilleMinimalSerializer()
    couleur_commentaire = CouleurCommentaireMinimalSerializer()
    created_at_formatted = serializers.SerializerMethodField()
    updated_at_formatted = serializers.SerializerMethodField()
    adresse_complete = serializers.SerializerMethodField()
    commentaire_preview = serializers.SerializerMethodField()  # CORRECTION : commentaire_preview au lieu de commentaire
    
    class Meta:
        model = Banquier
        fields = [
            'id',
            'nom_banque',
            'numero_compte',
            'type_relation',
            'numero',
            'rue',
            'ville',
            'code_postal',
            'adresse_complete',
            'couleur_commentaire',
            'commentaire_preview',  # CORRECTION : commentaire_preview
            'commentaire',  # Garder le champ original si besoin
            'created_at',
            'created_at_formatted',
            'updated_at',
            'updated_at_formatted'
        ]
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else ''
    
    def get_updated_at_formatted(self, obj):
        return obj.updated_at.strftime('%d/%m/%Y %H:%M') if obj.updated_at else ''
    
    def get_adresse_complete(self, obj):
        parts = []
        if obj.numero:
            parts.append(obj.numero)
        if obj.rue:
            parts.append(obj.rue)
        if obj.ville:
            parts.append(f"{obj.ville.nom} ({obj.ville.code})")  # CORRECTION : ville.code
        elif obj.code_postal:
            parts.append(obj.code_postal)
        return ', '.join(parts) if parts else 'Adresse non spécifiée'
    
    def get_commentaire_preview(self, obj):  # CORRECTION : get_commentaire_preview
        return obj.commentaire[:100] + '...' if obj.commentaire and len(obj.commentaire) > 100 else obj.commentaire or ''


class GetBanquierSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un banquier"""
    ville = VilleMinimalSerializer()
    couleur_commentaire = CouleurCommentaireMinimalSerializer()
    
    class Meta:
        model = Banquier
        fields = '__all__'


class AddBanquierSerializer(serializers.ModelSerializer):
    """Serializer pour l'ajout d'un banquier"""
    
    nom_banque = serializers.CharField(
        max_length=200,
        required=True,
        trim_whitespace=True,
        error_messages={
            'required': 'Le nom de la banque est obligatoire',
            'blank': 'Le nom de la banque ne peut pas être vide',
            'max_length': 'Le nom de la banque ne peut pas dépasser 200 caractères'
        }
    )
    
    ville = serializers.PrimaryKeyRelatedField(
        queryset=Ville.objects.all(),
        required=False,
        allow_null=True,
        error_messages={
            'does_not_exist': 'La ville sélectionnée n\'existe pas'
        }
    )
    
    couleur_commentaire = serializers.PrimaryKeyRelatedField(
        queryset=CouleurCommentaire.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Banquier
        fields = [
            'acheteur',
            'nom_banque',
            'numero_compte',
            'type_relation',
            'numero',
            'rue',
            'ville',
            'code_postal',
            'couleur_commentaire',
            'commentaire'
        ]
    
    def validate_nom_banque(self, value):
        """Validation du nom de la banque"""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le nom de la banque est obligatoire")
        if len(value) < 2:
            raise serializers.ValidationError("Le nom de la banque doit contenir au moins 2 caractères")
        return value
    
    def validate_numero_compte(self, value):
        """Validation du numéro de compte"""
        if value and len(value) > 500:
            raise serializers.ValidationError("Le numéro de compte ne peut pas dépasser 500 caractères")
        return value.strip() if value else value
    
    def validate_numero(self, value):
        """Validation du numéro d'adresse"""
        if value and len(value) > 50:
            raise serializers.ValidationError("Le numéro d'adresse ne peut pas dépasser 50 caractères")
        return value.strip() if value else value
    
    def validate_rue(self, value):
        """Validation de la rue"""
        if value and len(value) > 200:
            raise serializers.ValidationError("La rue ne peut pas dépasser 200 caractères")
        return value.strip() if value else value
    
    def validate_code_postal(self, value):
        """Validation du code postal"""
        if value and len(value) > 20:
            raise serializers.ValidationError("Le code postal ne peut pas dépasser 20 caractères")
        return value.strip() if value else value
    
    def validate(self, attrs):
        """Validation globale"""
        # Vérification de l'adresse complète
        if attrs.get('numero') or attrs.get('rue'):
            if not attrs.get('numero'):
                raise serializers.ValidationError({
                    'numero': 'Le numéro est requis si vous spécifiez une adresse'
                })
            if not attrs.get('rue'):
                raise serializers.ValidationError({
                    'rue': 'La rue est requise si vous spécifiez une adresse'
                })
        
        # Validation de la longueur du commentaire
        commentaire = attrs.get('commentaire') or ''
        if len(commentaire) > 10000:
            raise serializers.ValidationError({
                'commentaire': 'Le commentaire est trop long (max: 10,000 caractères)'
            })

        # Si code postal spécifié manuellement, vérifier la cohérence avec la ville
        ville = attrs.get('ville')
        code_postal = attrs.get('code_postal')
        if ville and code_postal:
            # CORRECTION : Utiliser ville.code au lieu de ville.code_postal
            if ville.code and code_postal != ville.code:
                raise serializers.ValidationError({
                    'code_postal': f'Le code postal doit correspondre à celui de la ville ({ville.code})'
                })
        
        return attrs


class EditBanquierSerializer(serializers.ModelSerializer):
    """Serializer pour la modification d'un banquier"""
    
    nom_banque = serializers.CharField(
        required=False,
        max_length=200,
        trim_whitespace=True
    )
    
    ville = serializers.PrimaryKeyRelatedField(
        queryset=Ville.objects.all(),
        required=False
    )
    
    couleur_commentaire = serializers.PrimaryKeyRelatedField(
        queryset=CouleurCommentaire.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Banquier
        fields = [
            'nom_banque',
            'numero_compte',
            'type_relation',
            'numero',
            'rue',
            'ville',
            'code_postal',
            'couleur_commentaire',
            'commentaire'
        ]
    
    def validate_nom_banque(self, value):
        """Validation du nom de la banque"""
        if value is not None:
            value = value.strip()
            if not value:
                raise serializers.ValidationError("Le nom de la banque ne peut pas être vide")
            if len(value) < 2:
                raise serializers.ValidationError("Le nom de la banque doit contenir au moins 2 caractères")
        return value
    
    def validate(self, attrs):
        """Validation globale"""
        # Validation partielle de l'adresse
        if attrs.get('numero') or attrs.get('rue'):
            if attrs.get('numero') and not attrs.get('rue'):
                pass  # OK pour mise à jour partielle
            elif attrs.get('rue') and not attrs.get('numero'):
                pass  # OK pour mise à jour partielle
        
        # Si ville ou code postal modifié, vérifier la cohérence
        ville = attrs.get('ville')
        code_postal = attrs.get('code_postal')
        
        if ville is not None or code_postal is not None:
            instance = self.instance
            ville = ville if ville is not None else instance.ville
            code_postal = code_postal if code_postal is not None else instance.code_postal
            
            if ville and code_postal:
                # CORRECTION : Utiliser ville.code au lieu de ville.code_postal
                if ville.code and code_postal != ville.code:
                    raise serializers.ValidationError({
                        'code_postal': f'Le code postal doit correspondre à celui de la ville ({ville.code})'
                    })
        
        return attrs








class ActifASerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = ActifA
        fields = "__all__"

    def validate_biens_installations_equipements(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_inventaire(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_creances_commerciales_autres_creances(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_actif_impots_courant(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_caisses_banques(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value


class AnneeUniciteAnnuelleMixin:
    """
    Mixin appliqué aux serializers Add/Edit de bilans.
    - Rend l'année obligatoire.
    - Si le CompteFinancier de l'acheteur a type_compte = 'Annuel',
      interdit deux enregistrements du même type pour la même année.
      (Pour les edits, l'instance courante est exclue du contrôle.)
    """

    def validate(self, data):
        annee = data.get('annee')
        acheteur = data.get('acheteur')

        if not annee:
            raise serializers.ValidationError(
                {'annee': "L'année est obligatoire."}
            )

        if annee and acheteur:
            compte = CompteFinancier.objects.filter(acheteur=acheteur).first()
            if compte and compte.type_compte == 'Annuel':
                qs = self.Meta.model.objects.filter(acheteur=acheteur, annee=annee)
                if self.instance:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    raise serializers.ValidationError({
                        'annee': (
                            "Un bilan de ce type existe déjà pour cette année. "
                            "Le type de compte est « Annuel » : une seule entrée par année est autorisée."
                        )
                    })

        return super().validate(data)


ACTIF_A_FIELDS = [
    "id", "annee", "acheteur",
    # Non-current
    "biens_installations_equipements", "droit_utilisation", "immobilisations_incorporelles",
    "goodwill", "actif_impot_differe", "investissements_associes",
    "creances_pret_non_courant", "actifs_financiers_juste_valeur_resultat",
    # Current
    "inventaire", "creances_commerciales_autres_creances", "actif_impots_courant",
    "creances_pret_courant", "caisses_banques", "actifs_financiers_derives",
    "created_by", "updated_by",
]

PASSIF_A_FIELDS = [
    "id", "annee", "acheteur",
    # Capital & reserves
    "capital_social", "prime_emission", "reserve_couverture_tresorerie",
    "reserve_cout_couverture", "reserve_conversion_devise", "benefices_non_distribues",
    "resultat_net_exercice", "reserve_distribuable",
    # Non-current liabilities
    "dettes_financieres_pret_bancaire", "dettes_commerciales_long_terme",
    "compte_courant_administrateurs", "provisions_long_terme", "autres_passifs_long_terme",
    # Current liabilities
    "dettes_commerciales_autres_dettes", "dettes_location", "avantages_employes",
    "impots", "passifs_financiers_derives",
    "created_by", "updated_by",
]

RESULTAT_A_FIELDS = [
    "id", "annee", "acheteur",
    # Revenue / direct costs
    "chiffre_affaires", "cout_des_ventes", "charges_exploitation",
    # Other income
    "autres_revenus",
    # Operating expenses
    "charges_administratives", "depreciation_amortissement", "couts_occupation",
    "couts_personnel", "autres_couts",
    # Disposal / extraordinary
    "perte_cession_immobilisations", "profit_cession_activite",
    # Finance
    "revenus_financiers", "charges_financieres", "charge_nette_financement",
    # Tax / associates / OCI
    "charge_impot_sur_revenu", "quote_part_perte_associes", "autres_elements_resultat_global",
    "created_by", "updated_by",
]


class AddActifASerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ActifA
        fields = ACTIF_A_FIELDS


class GetActifASerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifA
        fields = "__all__"


class EditActifASerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ActifA
        fields = ACTIF_A_FIELDS


class PassifASerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = PassifA
        fields = "__all__"


class AddPassifASerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = PassifA
        fields = PASSIF_A_FIELDS


class GetPassifASerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifA
        fields = "__all__"


class EditPassifASerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = PassifA
        fields = PASSIF_A_FIELDS


class ResultatASerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = ResultatA
        fields = "__all__"


class AddResultatASerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ResultatA
        fields = RESULTAT_A_FIELDS


class GetResultatASerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatA
        fields = "__all__"


class EditResultatASerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ResultatA
        fields = RESULTAT_A_FIELDS


class ActifCSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = ActifC
        fields = "__all__"

    def validate_capital_souscrit_non_app(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_frais_recherche_developpement(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_brevet_licence_logiciels(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_fonds_commercial(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_immobilisations_incorporelles(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_terrains(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_constructions(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_materiels_et_outils(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_materiel_de_transport(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_immos_corp(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_immos_en_cours(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_avances_et_acptes(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_participations(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_prets(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_stocks_mp(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_stocks_encours_mp(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_stocks_pf(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_stocks_encours_pf(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_stocks_encours_services(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_stocks_mses(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_avances_acptes_verses(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_clients_et_cptes_rattaches(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_creances(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_valeurs_a_encaisser(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_banques_cheques_postaux_caisse(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_cca(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_charges_a_repartir_et_frais_etablissement(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_primes_de_rbt(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_eca(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_ene(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_effectif(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_amortissements(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_provisions_stocks(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_provisions_creances(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_provisions_vmp(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value


class AddActifCSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ActifC
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital_souscrit_non_app",
            "frais_recherche_developpement",
            "brevet_licence_logiciels",
            "fonds_commercial",
            "autres_immobilisations_incorporelles",
            "terrains",
            "constructions",
            "materiels_et_outils",
            "materiel_de_transport",
            "autres_immos_corp",
            "immos_en_cours",
            "avances_et_acptes",
            "participations",
            "prets",
            "autres",
            "stocks_mp",
            "stocks_encours_mp",
            "stocks_pf",
            "stocks_encours_pf",
            "stocks_encours_services",
            "stocks_mses",
            "avances_acptes_verses",
            "clients_et_cptes_rattaches",
            "autres_creances",
            "valeurs_a_encaisser",
            "banques_cheques_postaux_caisse",
            "cca",
            "charges_a_repartir_et_frais_etablissement",
            "primes_de_rbt",
            "eca",
            "eene",
            "effectif",
            "amortissements",
            "provisions_stocks",
            "provisions_creances",
            "provisions_vmp",
            "created_by",
            "updated_by",
        ]


class GetActifCSerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = UserSerializer()
    # updated_by = UserSerializer()

    class Meta:
        model = ActifC
        fields = "__all__"


class EditActifCSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ActifC
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital_souscrit_non_app",
            "frais_recherche_developpement",
            "brevet_licence_logiciels",
            "fonds_commercial",
            "autres_immobilisations_incorporelles",
            "terrains",
            "constructions",
            "materiels_et_outils",
            "materiel_de_transport",
            "autres_immos_corp",
            "immos_en_cours",
            "avances_et_acptes",
            "participations",
            "prets",
            "autres",
            "stocks_mp",
            "stocks_encours_mp",
            "stocks_pf",
            "stocks_encours_pf",
            "stocks_encours_services",
            "stocks_mses",
            "avances_acptes_verses",
            "clients_et_cptes_rattaches",
            "autres_creances",
            "valeurs_a_encaisser",
            "banques_cheques_postaux_caisse",
            "cca",
            "charges_a_repartir_et_frais_etablissement",
            "primes_de_rbt",
            "eca",
            "eene",
            "effectif",
            "amortissements",
            "provisions_stocks",
            "provisions_creances",
            "provisions_vmp",
            "created_by",
            "updated_by",
        ]


class PassifCSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = PassifC
        fields = "__all__"

    def validate_capital_social(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_primes(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_ecarts_de_reevaluation(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_reserve(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_report_a_nouveau(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_resultat_exercice(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_subv_invest(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_provision_regl(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_emprunts(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dette_credit_bail_contrat_assimile(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dettes_financiere_diverses(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_provision_financiere_risque_charge(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dettes_fournisseurs_divers(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_avance_et_acomptes_recu(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dettes(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dettes_fiscales_sociales(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_dettes(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_banques_credit_escompte(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_banque_credit_caisse(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_banques_decouvert(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_ecart_conversion_passif(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value


class AddPassifCSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = PassifC
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital_social",
            "primes",
            "ecarts_de_reevaluation",
            "reserve",
            "report_a_nouveau",
            "resultat_exercice",
            "subv_invest",
            "provision_regl",
            "emprunts",
            "dette_credit_bail_contrat_assimile",
            "dettes_financiere_diverses",
            "provision_financiere_risque_charge",
            "dettes_fournisseurs_divers",
            "avance_et_acomptes_recu",
            "dettes",
            "dettes_fiscales_sociales",
            "autres_dettes",
            "banques_credit_escompte",
            "banque_credit_caisse",
            "banques_decouvert",
            "ecart_conversion_passif",
            "created_by",
            "updated_by",
        ]


class GetPassifCSerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = UserSerializer()
    # updated_by = UserSerializer()

    class Meta:
        model = PassifC
        fields = "__all__"


class EditPassifCSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = PassifC
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital_social",
            "primes",
            "ecarts_de_reevaluation",
            "reserve",
            "report_a_nouveau",
            "resultat_exercice",
            "subv_invest",
            "provision_regl",
            "emprunts",
            "dette_credit_bail_contrat_assimile",
            "dettes_financiere_diverses",
            "provision_financiere_risque_charge",
            "dettes_fournisseurs_divers",
            "avance_et_acomptes_recu",
            "dettes",
            "dettes_fiscales_sociales",
            "autres_dettes",
            "banques_credit_escompte",
            "banque_credit_caisse",
            "banques_decouvert",
            "ecart_conversion_passif",
            "created_by",
            "updated_by",
        ]


class ResultatCSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = ResultatC
        fields = "__all__"

    def validate_vente_de_mdses(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_ventes_de_produits_fabriques(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_travaux_services_vendus(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_produit_accessoires(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_production_imblise(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_subventions_exploitations(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_production_stockee(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_reprises_de_provision(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_transferts_charges(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_produits(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_achat_mdses(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_variation_stock_mdses(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_achat_mp_autres_appro(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_var_stk_mp_app(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_achats(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_variation_de_stocks_autres_appro(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_transports(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_services_ext(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_impots_taxes(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_charges_valeur_ajoutee(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_charges_personnel(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dotation_aux_amorts(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dotation_aux_provisions(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_autres_charges_excedent_brute(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_revenus_fin_assimiles(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_prof_vmp_et_cre_actif_immo(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_interets_produit_assim(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_reprise_prov_et_transfert(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_diff_positive_de_change(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_prod_nets_cessions_vmp(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dap(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_frais_fin_charges_assi(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_diff_negatives_de_change(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_ch_nettes_cessions_vmp(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_sur_op_gestion_prod_except(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_sur_op_en_capital_prod_except(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_reprise_prov_transfert(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_sur_op_gestion_charg_except(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_sur_op_en_capital_charg_except(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_dap_et_transfert_charg_except(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value


class AddResultatCSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ResultatC
        fields = [
            "id",
            "annee",
            "acheteur",
            "vente_de_mdses",
            "ventes_de_produits_fabriques",
            "travaux_services_vendus",
            "produit_accessoires",
            "production_imblise",
            "subventions_exploitations",
            "production_stockee",
            "reprises_de_provision",
            "transferts_charges",
            "autres_produits",
            "achat_mdses",
            "variation_stock_mdses",
            "achat_mp_autres_appro",
            "var_stk_mp_app",
            "autres_achats",
            "variation_de_stocks_autres_appro",
            "transports",
            "services_ext",
            "impots_taxes",
            "autres_charges_valeur_ajoutee",
            "charges_personnel",
            "dotation_aux_amorts",
            "dotation_aux_provisions",
            "autres_charges_excedent_brute",
            "revenus_fin_assimiles",
            "prof_vmp_et_cre_actif_immo",
            "interets_produit_assim",
            "reprise_prov_et_transfert",
            "diff_positive_de_change",
            "prod_nets_cessions_vmp",
            "dap",
            "frais_fin_charges_assi",
            "diff_negatives_de_change",
            "ch_nettes_cessions_vmp",
            "sur_op_gestion_prod_except",
            "sur_op_en_capital_prod_except",
            "reprise_prov_transfert",
            "sur_op_gestion_charg_except",
            "sur_op_en_capital_charg_except",
            "dap_et_transfert_charg_except",
            "participation_salairies",
            "impot_sur_benefices",
            "created_by",
            "updated_by",
        ]


class GetResultatCSerializer(serializers.ModelSerializer):
    # acheteur = AcheteurSerializer()
    # annee = AnneeSerializer()
    # created_by = UserSerializer()
    # updated_by = UserSerializer()

    class Meta:
        model = ResultatC
        fields = "__all__"


class EditResultatCSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ResultatC
        fields = [
            "id",
            "annee",
            "acheteur",
            "vente_de_mdses",
            "ventes_de_produits_fabriques",
            "travaux_services_vendus",
            "produit_accessoires",
            "production_imblise",
            "subventions_exploitations",
            "production_stockee",
            "reprises_de_provision",
            "transferts_charges",
            "autres_produits",
            "achat_mdses",
            "variation_stock_mdses",
            "achat_mp_autres_appro",
            "var_stk_mp_app",
            "autres_achats",
            "variation_de_stocks_autres_appro",
            "transports",
            "services_ext",
            "impots_taxes",
            "autres_charges_valeur_ajoutee",
            "charges_personnel",
            "dotation_aux_amorts",
            "dotation_aux_provisions",
            "autres_charges_excedent_brute",
            "revenus_fin_assimiles",
            "prof_vmp_et_cre_actif_immo",
            "interets_produit_assim",
            "reprise_prov_et_transfert",
            "diff_positive_de_change",
            "prod_nets_cessions_vmp",
            "dap",
            "frais_fin_charges_assi",
            "diff_negatives_de_change",
            "ch_nettes_cessions_vmp",
            "sur_op_gestion_prod_except",
            "sur_op_en_capital_prod_except",
            "reprise_prov_transfert",
            "sur_op_gestion_charg_except",
            "sur_op_en_capital_charg_except",
            "dap_et_transfert_charg_except",
            "participation_salairies",
            "impot_sur_benefices",
            "created_by",
            "updated_by",
        ]


class ActifSysCohadaSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = ActifS
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_frais_developpement_prospection(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddActifSysCohadaSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ActifS
        fields = [
            "id",
            "annee",
            "acheteur",
            "frais_developpement_prospection",
            "brevets_licences_logiciels",
            "droits_propriete_commerciale_baux",
            "autres_immo_incorporelles",
            "terrains",
            "dons_investissements_net",
            "batiments",
            "agencements_amenagements_installations",
            "materiel_mobilier_actif_biologiques",
            "materiel_transport",
            "avances_acompte_immobilisations",
            "titres_participation",
            "autres_immobilisations_financieres",
            "actif_circulant_hao",
            "stock_encours",
            "fournisseurs_avances_versee",
            "clients",
            "autres_creances",
            "valeurs_mobilieres_placement",
            "disponibilites",
            "banque_cheque_postal_caisse_assimiles",
            "ecart_conversion_actif",
            "created_by",
            "updated_by",
        ]


class GetActifSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifS
        fields = "__all__"


class EditActifSysCohadaSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ActifS
        fields = [
            "id",
            "annee",
            "acheteur",
            "frais_developpement_prospection",
            "brevets_licences_logiciels",
            "droits_propriete_commerciale_baux",
            "autres_immo_incorporelles",
            "terrains",
            "dons_investissements_net",
            "batiments",
            "agencements_amenagements_installations",
            "materiel_mobilier_actif_biologiques",
            "materiel_transport",
            "avances_acompte_immobilisations",
            "titres_participation",
            "autres_immobilisations_financieres",
            "actif_circulant_hao",
            "stock_encours",
            "fournisseurs_avances_versee",
            "clients",
            "autres_creances",
            "valeurs_mobilieres_placement",
            "disponibilites",
            "banque_cheque_postal_caisse_assimiles",
            "ecart_conversion_actif",
            "created_by",
            "updated_by",
        ]


class PassifSysSCohadaSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = PassifS
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_capital(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddPassifSysCohadaSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = PassifS
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital",
            "capital_non_appele_apporteurs",
            "primes_liees_capital_social",
            "ecart_reevaluation",
            "reserves_indisponibles",
            "reserves_libres",
            "report_nouveau",
            "resultat_net_exercice",
            "subventions_investissements",
            "provisions_reglees",
            "emprunts_dettes_financieres_diverse",
            "dettes_location_vente",
            "provisions_risques_charges",
            "passif_circulant_hao",
            "clients_avances_recues",
            "fournisseurs_exploitation",
            "dettes_fiscales_sociales",
            "autres_dettes",
            "provisions_risques_court_terme",
            "banques_credit_escompte",
            "banques_etablissements_financiers_credit_caisse",
            "ecart_conversion_passif",
            "created_by",
            "updated_by",
        ]


class GetPassifSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifS
        fields = "__all__"


class EditPassifSysCohadaSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = PassifS
        fields = [
            "id",
            "annee",
            "acheteur",
            "capital",
            "capital_non_appele_apporteurs",
            "primes_liees_capital_social",
            "ecart_reevaluation",
            "reserves_indisponibles",
            "reserves_libres",
            "report_nouveau",
            "resultat_net_exercice",
            "subventions_investissements",
            "provisions_reglees",
            "emprunts_dettes_financieres_diverse",
            "dettes_location_vente",
            "provisions_risques_charges",
            "passif_circulant_hao",
            "clients_avances_recues",
            "fournisseurs_exploitation",
            "dettes_fiscales_sociales",
            "autres_dettes",
            "provisions_risques_court_terme",
            "banques_credit_escompte",
            "banques_etablissements_financiers_credit_caisse",
            "ecart_conversion_passif",
            "created_by",
            "updated_by",
        ]


class ResultatSysCohadaSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()
    annee = AnneeSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = ResultatS
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_ventes_marchandises_a(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddResultatSysCohadaSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ResultatS
        fields = [
            "id",
            "annee",
            "acheteur",
            "ventes_marchandises_a",
            "achats_marchandises",
            "variation_stock_marchandises",
            "ventes_produits_manufactures",
            "travaux_services_vendus_c",
            "produits_accessoires_d",
            "production_stockee",
            "production_immobilisee",
            "subvention_exploitation",
            "autres_produits",
            "transfert_charges_exploitation",
            "achats_matieres_premieres_fournitures_connexes",
            "variation_stock_matieres_premieres_fournitures_connexes",
            "autres_achats",
            "variation_stock_autres_fournitures",
            "transport",
            "services_exterieurs",
            "impots_taxes",
            "autres_depenses",
            "frais_personnel",
            "reprise_depreciations_amortissements_provision_pertes_valeurs_p",
            "reprise_depreciations_amortissements_provision_pertes_valeurs_m",
            "produits_financiers_assimiles",
            "reprise_provision_perte_valeur",
            "transfert_charges_financieres",
            "dotations_provisions_depreciations_financieres",
            "produits_cession_immobilisations",
            "autres_produits_hao",
            "valeur_comptable_cessions_actifs_immobilises",
            "autres_charges_hao",
            "participation_travailleurs",
            "charge_impot_revenu",
            "created_by",
            "updated_by",
        ]


class GetResultatSysCohadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatS
        fields = "__all__"


class EditResultatSysCohadaSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ResultatS
        fields = [
            "id",
            "annee",
            "acheteur",
            "ventes_marchandises_a",
            "achats_marchandises",
            "variation_stock_marchandises",
            "ventes_produits_manufactures",
            "travaux_services_vendus_c",
            "produits_accessoires_d",
            "production_stockee",
            "production_immobilisee",
            "subvention_exploitation",
            "autres_produits",
            "transfert_charges_exploitation",
            "achats_matieres_premieres_fournitures_connexes",
            "variation_stock_matieres_premieres_fournitures_connexes",
            "autres_achats",
            "variation_stock_autres_fournitures",
            "transport",
            "services_exterieurs",
            "impots_taxes",
            "autres_depenses",
            "frais_personnel",
            "reprise_depreciations_amortissements_provision_pertes_valeurs_p",
            "reprise_depreciations_amortissements_provision_pertes_valeurs_m",
            "produits_financiers_assimiles",
            "reprise_provision_perte_valeur",
            "transfert_charges_financieres",
            "dotations_provisions_depreciations_financieres",
            "produits_cession_immobilisations",
            "autres_produits_hao",
            "valeur_comptable_cessions_actifs_immobilises",
            "autres_charges_hao",
            "participation_travailleurs",
            "charge_impot_revenu",
            "created_by",
            "updated_by",
        ]


class AssetsSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = Assets
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_banques_centrales(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddAssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = [
            "id",
            "annee",
            "acheteur",
            "caisse",
            "banques_centrales",
            "tresorerie_cpp",
            "autres_ets_credit",
            "a_terme",
            "credits_campagne",
            "credits_ordinaire",
            "credits_campagne_acc",
            "credits_ordinaire_acc",
            "creances_ordinaires",
            "affacturage",
            "titres_placement",
            "immobilisation_fin",
            "operation_credit_bail",
            "immobilisation_incorporelle",
            "immobilisation_corporelle",
            "actionnaire_ou_associe",
            "autres_actifs",
            "comptes_commande_divers",
            "created_by",
            "updated_by",
        ]


class GetAssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = "__all__"


class EditAssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = [
            "id",
            "annee",
            "acheteur",
            "caisse",
            "banques_centrales",
            "tresorerie_cpp",
            "autres_ets_credit",
            "a_terme",
            "credits_campagne",
            "credits_ordinaire",
            "credits_campagne_acc",
            "credits_ordinaire_acc",
            "creances_ordinaires",
            "affacturage",
            "titres_placement",
            "immobilisation_fin",
            "operation_credit_bail",
            "immobilisation_incorporelle",
            "immobilisation_corporelle",
            "actionnaire_ou_associe",
            "autres_actifs",
            "comptes_commande_divers",
            "created_by",
            "updated_by",
        ]


class LiabilitiesSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = Liabilities
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_tresorerie_ccp(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddLiabilitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liabilities
        fields = [
            "id",
            "annee",
            "acheteur",
            "tresorerie_ccp",
            "autres_etablissement_credit",
            "a_terme",
            "comptes_epargne_court_terme",
            "comptes_epargne_terme",
            "bons_caisse",
            "autres_dette_a_vue",
            "autres_dette_a_terme",
            "titres_creance_autres_dettes",
            "compte_dordre_divers",
            "provision_pour_risque_charge",
            "provision_reglementee",
            "emprunt_subordonne_tire_emis",
            "subventions_investissement",
            "fonds_affecte",
            "fonds_pour_risque_bancaire_generaux",
            "capital_ou_dotation",
            "primes_liees_reserve_capital",
            "ecarts_reevaluation",
            "benefices_non_distribue",
            "resultat_net_exercie",
            "created_by",
            "updated_by",
        ]


class GetLiabilitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liabilities
        fields = "__all__"


class EditLiabilitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liabilities
        fields = [
            "id",
            "annee",
            "acheteur",
            "tresorerie_ccp",
            "autres_etablissement_credit",
            "a_terme",
            "comptes_epargne_court_terme",
            "comptes_epargne_terme",
            "bons_caisse",
            "autres_dette_a_vue",
            "autres_dette_a_terme",
            "titres_creance_autres_dettes",
            "compte_dordre_divers",
            "provision_pour_risque_charge",
            "provision_reglementee",
            "emprunt_subordonne_tire_emis",
            "subventions_investissement",
            "fonds_affecte",
            "fonds_pour_risque_bancaire_generaux",
            "capital_ou_dotation",
            "primes_liees_reserve_capital",
            "ecarts_reevaluation",
            "benefices_non_distribue",
            "resultat_net_exercie",
            "created_by",
            "updated_by",
        ]


class OffBalanceSheetSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = OffBalanceSheet
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_en_faveur_des_ets_credit(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddOffBalanceSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffBalanceSheet
        fields = [
            "id",
            "annee",
            "acheteur",
            "en_faveur_des_ets_credit",
            "en_faveur_clientele",
            "pour_compte_ets_credit",
            "pour_compte_clientele",
            "engagement_sur_titre",
            "recu_ets_credit",
            "recu_ets_credit2",
            "recu_clientele",
            "engagement_sur_titre2",
            "created_by",
            "updated_by",
        ]


class GetOffBalanceSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffBalanceSheet
        fields = "__all__"


class EditOffBalanceSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffBalanceSheet
        fields = [
            "id",
            "annee",
            "acheteur",
            "en_faveur_des_ets_credit",
            "en_faveur_clientele",
            "pour_compte_ets_credit",
            "pour_compte_clientele",
            "engagement_sur_titre",
            "recu_ets_credit",
            "recu_ets_credit2",
            "recu_clientele",
            "engagement_sur_titre2",
            "created_by",
            "updated_by",
        ]


class ExpensesSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = Expenses
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_interet_charges_assimilee_dette_interbancaire(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = [
            "id",
            "annee",
            "acheteur",
            "interet_charges_assimilee_dette_interbancaire",
            "interet_charge_assimilee_dette_clientele",
            "interet_charge_assimilee_titre_creance",
            "chargesc_compte_bloque_dactionnaire_emprunt_sub",
            "autres_interets_charges_assimilee",
            "charges_sur_op_credit_bail_assimile",
            "commissions",
            "charges_sur_titre_placement",
            "charges_sur_operation_change",
            "charges_sur_operation_hors_bilan",
            "frais_divers_exploitation_bancaire",
            "achat_marchandises",
            "stocks_vendus",
            "variations_stocks_marchanides",
            "frais_personnel",
            "autres_frais_generaux",
            "dotations_amortissement_provision_immobilisation",
            "solde_perte_creance_hors_bilan",
            "excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux",
            "charges_exceptionnelle",
            "pertes_exercice_anterieurs",
            "impot_sur_revenu",
            "total_charges",
            "created_by",
            "updated_by",
        ]


class GetExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = "__all__"


class EditExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = [
            "id",
            "annee",
            "acheteur",
            "interet_charges_assimilee_dette_interbancaire",
            "interet_charge_assimilee_dette_clientele",
            "interet_charge_assimilee_titre_creance",
            "chargesc_compte_bloque_dactionnaire_emprunt_sub",
            "autres_interets_charges_assimilee",
            "charges_sur_op_credit_bail_assimile",
            "commissions",
            "charges_sur_titre_placement",
            "charges_sur_operation_change",
            "charges_sur_operation_hors_bilan",
            "frais_divers_exploitation_bancaire",
            "achat_marchandises",
            "stocks_vendus",
            "variations_stocks_marchanides",
            "frais_personnel",
            "autres_frais_generaux",
            "dotations_amortissement_provision_immobilisation",
            "solde_perte_creance_hors_bilan",
            "excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux",
            "charges_exceptionnelle",
            "pertes_exercice_anterieurs",
            "impot_sur_revenu",
            "total_charges",
            "created_by",
            "updated_by",
        ]


class ProductsSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer()
    acheteur = AcheteurSerializer()
    created_by = UserSerializer()
    updated_by = UserSerializer()

    class Meta:
        model = Products
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    # Ajoutez des validateurs pour chaque champ DecimalField si nécessaire
    def validate_interets_produit_assimile_sur_pret_avance_interbancaire(self, value):
        return self.validate_decimal_field(value)

    # Répétez pour chaque champ DecimalField...


class AddProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = [
            "id",
            "annee",
            "acheteur",
            "interets_produit_assimile_sur_pret_avance_interbancaire",
            "ineterets_produit_assimile_pret_avance_clientele",
            "interet_produit_sur_titre_dinvestissement",
            "revenu_gains_titre_pret_titre_subordonne",
            "autres_interets_produits_assimiles",
            "produits_leansing_operation_connexes",
            "commissions",
            "revenus_titre_negociable",
            "dividendes_produits_assimiles",
            "revenus_operation_de_change",
            "produits_opeations_hors_bilan",
            "produits_bancaire_divers",
            "marges_vente",
            "ventes_marchandises",
            "variation_stocks_marchandises",
            "produit_dexploitation_generale",
            "reprise_damortissement_provisions_sur_immobilisation",
            "solde_resultat_correction_valeur_sur_creance_hors_bilan",
            "excedent_reprise_fonds_pour_risque_bancaire_generaux",
            "produits_exceptionnels",
            "benefice_sur_exercice_anterieur",
            "perte",
            "created_by",
            "updated_by",
        ]


class GetProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = "__all__"


class EditProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = [
            "id",
            "annee",
            "acheteur",
            "interets_produit_assimile_sur_pret_avance_interbancaire",
            "ineterets_produit_assimile_pret_avance_clientele",
            "interet_produit_sur_titre_dinvestissement",
            "revenu_gains_titre_pret_titre_subordonne",
            "autres_interets_produits_assimiles",
            "produits_leansing_operation_connexes",
            "commissions",
            "revenus_titre_negociable",
            "dividendes_produits_assimiles",
            "revenus_operation_de_change",
            "produits_opeations_hors_bilan",
            "produits_bancaire_divers",
            "marges_vente",
            "ventes_marchandises",
            "variation_stocks_marchandises",
            "produit_dexploitation_generale",
            "reprise_damortissement_provisions_sur_immobilisation",
            "solde_resultat_correction_valeur_sur_creance_hors_bilan",
            "excedent_reprise_fonds_pour_risque_bancaire_generaux",
            "produits_exceptionnels",
            "benefice_sur_exercice_anterieur",
            "perte",
            "created_by",
            "updated_by",
        ]


class CommandesSerializer(serializers.ModelSerializer):
    client = UserSerializer()
    acheteur = AcheteurSerializer()
    pays = PaysSerializer()
    ville = VilleSerializer()
    devise_credit_demande = DeviseSerializer()
    devise_credit_recommande = DeviseSerializer()

    class Meta:
        model = Commande
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_credit_demande(self, value):
        return self.validate_decimal_field(value)

    def validate_credit_recommande(self, value):
        return self.validate_decimal_field(value)


COMMANDE_EDITABLE_FIELDS = [
        "id",
        "notre_ref",
        "reference_client",
        "date_recept_commande",
        "date_rapport",
        "delais",
        "priorite",
        "raison_sociale",
        "type_rapport",
        "credit_demande",
        "devise_credit_demande",
        "credit_recommande",
        "devise_credit_recommande",
        "numero_adresse",
        "rue_adresse",
        "code_postale_adresse",
        "telephone",
        "email",
        "type_commande",
        "type_traitement",
        "client_nom",
        "pays",
        "ville",
        "client",
        "acheteur",
        "status",
        "validateur",
        "date_envoi_client",
        "email_envoye",
        "imprimer_avec_etats_fin",
        "company_identification_number",
        "address_additional",
        "state",
        "postcode",
        "post_office",
        "provider",
        "comments",
]


class AddCommandeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Commande
        fields = COMMANDE_EDITABLE_FIELDS


class GetCommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commande
        fields = "__all__"


class CheckCommandeSerializer(serializers.ModelSerializer):
    client = UserSerializer()
    acheteur = AcheteurSerializer()
    pays = PaysSerializer()
    ville = VilleSerializer()
    validateur = UserSerializer()
    devise_credit_demande = DeviseSerializer()
    devise_credit_recommande = DeviseSerializer()

    class Meta:
        model = Commande
        fields = "__all__"

    def validate_decimal_field(self, value):
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("La valeur doit être un nombre décimal.")
        return value

    def validate_credit_demande(self, value):
        return self.validate_decimal_field(value)

    def validate_credit_recommande(self, value):
        return self.validate_decimal_field(value)


class EditCommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commande
        fields = COMMANDE_EDITABLE_FIELDS


class AlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerte
        fields = "__all__"


class AddAlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerte
        fields = ["reference", "objet", "content"]


class EditAlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerte
        fields = ["reference", "objet", "content"]


class DocumentAlerteSerializer(serializers.ModelSerializer):
    alerte = AlerteSerializer()

    class Meta:
        model = DocumentAlerte
        fields = "__all__"


class AddDocumentAlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAlerte
        fields = ["titre", "fichier", "alerte"]


class EditDocumentAlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAlerte
        fields = ["alerte", "titre", "fichier"]



class AcheteurSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Acheteur
        fields = ["id", "nom", "code"]


class WarningAttachmentSerializer(serializers.ModelSerializer):
    filename = serializers.SerializerMethodField()
    upload_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = WarningAttachment
        fields = ["id", "filename", "upload_url", "file_size", "uploaded_at"]

    def get_filename(self, obj):
        return obj.filename()

    def get_upload_url(self, obj):
        request = self.context.get("request")
        if not obj.upload:
            return None

        file_url = obj.upload.url
        return request.build_absolute_uri(file_url) if request else file_url

    def get_file_size(self, obj):
        try:
            return obj.upload.size if obj.upload else 0
        except Exception:
            return 0


class WarningListSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    acheteurs_count = serializers.SerializerMethodField()
    attachments_count = serializers.SerializerMethodField()

    class Meta:
        model = Warning
        fields = [
            "id",
            "titre",
            "description",
            "created_by",
            "created_by_username",
            "acheteurs_count",
            "attachments_count",
            "created_at",
            "email_sent",
            "email_sent_at",
            "email_to",
            "email_subject",
        ]

    def get_acheteurs_count(self, obj):
        return obj.acheteurs.count()

    def get_attachments_count(self, obj):
        return obj.warning_attachments.count()


class WarningDetailSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    acheteurs = AcheteurSimpleSerializer(many=True, read_only=True)
    warning_attachments = WarningAttachmentSerializer(many=True, read_only=True)
    acheteurs_count = serializers.SerializerMethodField()
    attachments_count = serializers.SerializerMethodField()

    class Meta:
        model = Warning
        fields = [
            "id",
            "titre",
            "description",
            "acheteurs",
            "acheteurs_count",
            "attachments_count",
            "created_by",
            "created_by_username",
            "created_at",
            "warning_attachments",
            "email_subject",
            "email_to",
            "email_cc",
            "email_bcc",
            "email_sent",
            "email_sent_at",
        ]

    def get_acheteurs_count(self, obj):
        return obj.acheteurs.count()

    def get_attachments_count(self, obj):
        return obj.warning_attachments.count()


class WarningUpsertSerializer(serializers.ModelSerializer):
    acheteurs = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all(), many=True
    )

    class Meta:
        model = Warning
        fields = [
            "titre", "description", "acheteurs",
            "email_subject", "email_to", "email_cc", "email_bcc",
        ]

    def validate_titre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Le titre est obligatoire.")
        return value.strip()

    def validate_description(self, value):
        return (value or "").strip()

    def create(self, validated_data):
        acheteurs = validated_data.pop("acheteurs", [])
        warning = Warning.objects.create(**validated_data)
        warning.acheteurs.set(acheteurs)
        return warning

    def update(self, instance, validated_data):
        acheteurs = validated_data.pop("acheteurs", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if acheteurs is not None:
            instance.acheteurs.set(acheteurs)

        return instance

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"


class AddClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "nom",
            "email",
            "telephone",
            "adresse",
            "date_inscription",
            "actif",
        ]


class GetClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"


class CheckClientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = "__all__"


class EditClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "nom",
            "email",
            "telephone",
            "adresse",
            "date_inscription",
            "actif",
        ]


class ContactSerializer(serializers.ModelSerializer):
    client = (
        ClientSerializer()
    )  # Utilisez le sérialiseur pour inclure les détails du pays

    class Meta:
        model = Contact
        fields = [
            "id",
            "client",
            "nom",
            "email",
            "telephone",
            "actif",
        ]


class AddContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "client",
            "nom",
            "email",
            "telephone",
            "actif",
        ]


class GetContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"


class CheckContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"


class EditContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "client",
            "nom",
            "email",
            "telephone",
            "actif",
        ]


class PortefeuilleSerializer(serializers.ModelSerializer):
    client = ClientSerializer()
    nb_acheteurs = serializers.SerializerMethodField()
    nb_elements = serializers.SerializerMethodField()

    class Meta:
        model = Portefeuille
        fields = "__all__"

    def get_nb_acheteurs(self, obj):
        return obj.portefeuilleclient_set.count()

    def get_nb_elements(self, obj):
        return obj.elements_surveillance_actifs.count()


class AddPortefeuilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portefeuille
        fields = "__all__"


class AddPortefeuilleWithAcheteursSerializer(serializers.ModelSerializer):
    elements_surveillance_actifs = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ElementSurveillance.objects.all(), required=False
    )
    acheteurs = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, default=list
    )

    class Meta:
        model = Portefeuille
        fields = [
            "id", "client", "nom", "frequence_alertes",
            "elements_surveillance_actifs", "acheteurs",
            "created_at", "updated_at",
        ]

    def create(self, validated_data):
        acheteurs_ids = validated_data.pop("acheteurs", [])
        elements = validated_data.pop("elements_surveillance_actifs", [])
        portefeuille = Portefeuille.objects.create(**validated_data)
        if elements:
            portefeuille.elements_surveillance_actifs.set(elements)
        for acheteur_id in acheteurs_ids:
            PortefeuilleClient.objects.get_or_create(
                portefeuille=portefeuille, acheteur_id=acheteur_id,
                defaults={"categorie": "autre"}
            )
        return portefeuille

    def update(self, instance, validated_data):
        acheteurs_ids = validated_data.pop("acheteurs", None)
        elements = validated_data.pop("elements_surveillance_actifs", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if elements is not None:
            instance.elements_surveillance_actifs.set(elements)
        if acheteurs_ids is not None:
            PortefeuilleClient.objects.filter(portefeuille=instance).delete()
            for acheteur_id in acheteurs_ids:
                PortefeuilleClient.objects.create(
                    portefeuille=instance, acheteur_id=acheteur_id, categorie="autre"
                )
        return instance


class GetPortefeuilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portefeuille
        fields = "__all__"


class CheckPortefeuilleSerializer(serializers.ModelSerializer):
    client = ClientSerializer()  # Assurez-vous d'avoir un ClientSerializer défini

    class Meta:
        model = Portefeuille
        fields = "__all__"


class EditPortefeuilleSerializer(serializers.ModelSerializer):
    elements_surveillance_actifs = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ElementSurveillance.objects.all(), required=False
    )

    class Meta:
        model = Portefeuille
        fields = [
            "id",
            "client",
            "frequence_alertes",
            "nom",
            "elements_surveillance_actifs",
            "created_at",
            "updated_at",
        ]


class PortefeuilleClientSerializer(serializers.ModelSerializer):
    portefeuille = PortefeuilleSerializer()
    acheteur = AcheteurSerializer()  # Assurez-vous d'avoir un AcheteurSerializer défini

    class Meta:
        model = PortefeuilleClient
        fields = "__all__"


class AddPortefeuilleClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortefeuilleClient
        fields = ["id", "portefeuille", "acheteur", "categorie"]


class GetPortefeuilleClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortefeuilleClient
        fields = "__all__"


class CheckPortefeuilleClientSerializer(serializers.ModelSerializer):
    portefeuille = PortefeuilleSerializer()
    acheteur = AcheteurSerializer()  # Assurez-vous d'avoir un AcheteurSerializer défini

    class Meta:
        model = PortefeuilleClient
        fields = "__all__"


class CompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = "__all__"


class AddCompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = ["id", "nom", "type_compte", "sous_type"]


class GetCompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = "__all__"


class CheckCompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = "__all__"


class EditCompteFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteFinancierIrfs
        fields = ["id", "nom", "type_compte", "sous_type"]


class ValeurCompteIrfsSerializer(serializers.ModelSerializer):

    compte = CompteFinancierIrfsSerializer()
    devise = DeviseSerializer()
    annee = AnneeSerializer()

    class Meta:
        model = ValeurCompteIrfs
        fields = "__all__"


class AddValeurCompteIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurCompteIrfs
        fields = ["id", "acheteur", "compte", "annee", "valeur", "devise"]


class GetValeurCompteIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurCompteIrfs
        fields = "__all__"


class CheckValeurCompteIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurCompteIrfs
        fields = "__all__"


class EditValeurCompteIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurCompteIrfs
        fields = ["id", "acheteur", "compte", "annee", "valeur", "devise"]


class RatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = "__all__"


class AddRatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = ["id", "type_ratio", "nom", "formule"]


class GetRatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = "__all__"


class CheckRatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = "__all__"


class EditRatioFinancierIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatioFinancierIrfs
        fields = ["id", "type_ratio", "nom", "formule"]


class ValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = "__all__"


class AddValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = ["id", "acheteur", "ratio", "annee", "valeur"]


class GetValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = "__all__"


class CheckValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = "__all__"


class EditValeurRatioIrfsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValeurRatioIrfs
        fields = ["id", "acheteur", "ratio", "annee", "valeur"]





from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers

User = get_user_model()


# serializers.py
class NewUserSerializer(serializers.ModelSerializer):
    pays = serializers.SerializerMethodField()
    date_joined_formatted = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    avatar_url_absolute = serializers.SerializerMethodField()  # Pour le frontend
    groups = serializers.SerializerMethodField()
    affectation = serializers.SerializerMethodField()
    affectation_possible = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'telephone', 'activation', 'pays', 
            'date_joined', 'date_joined_formatted', 'avatar_url',
            'avatar_url_absolute', 'profession', 'address', 'email_cc',
            'is_staff', 'is_superuser', 'is_client', 'groups',
            'affectation', 'affectation_possible'
        ]
    
    def get_pays(self, obj):
        if obj.pays:
            return {
                'id': obj.pays.id,
                'nom': obj.pays.nom,
                'code': obj.pays.code if hasattr(obj.pays, 'code') else None
            }
        return None
    
    def get_date_joined_formatted(self, obj):
        if obj.date_joined:
            mois_fr = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin',
                      'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
            return f"{obj.date_joined.day} {mois_fr[obj.date_joined.month-1]} {obj.date_joined.year}"
        return None
    
    def get_avatar_url(self, obj):
        """Retourne le chemin relatif de l'avatar"""
        if obj.avatar:
            # Retourne juste le nom du fichier ou le chemin relatif
            if hasattr(obj.avatar, 'url'):
                return obj.avatar.url  # Retourne '/media/avatars/filename.jpg'
            elif hasattr(obj.avatar, 'name'):
                return f"/media/{obj.avatar.name}"
        return None
    
    def get_avatar_url_absolute(self, obj):
        """Retourne l'URL absolue pour le frontend"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                # En développement avec request
                return request.build_absolute_uri(obj.avatar.url)
            else:
                # En production sans request, construire l'URL
                from django.conf import settings
                if hasattr(settings, 'DOMAIN'):
                    domain = settings.DOMAIN
                else:
                    # Essayer de déterminer le domaine depuis les settings
                    domain = getattr(settings, 'SITE_DOMAIN', '')
                    if not domain:
                        # Par défaut, utiliser le nom d'hôte
                        import socket
                        domain = f"http://{socket.gethostname()}"
                
                # Construire l'URL complète
                avatar_path = obj.avatar.url if hasattr(obj.avatar, 'url') else f"/media/{obj.avatar.name}"
                return f"{domain}{avatar_path}"
        return None   
    
    def get_groups(self, obj):
        return list(obj.groups.values("id", "name"))

    def get_affectation(self, obj):
        return list(obj.affectation.values("id", "nom"))

    def get_affectation_possible(self, obj):
        return list(obj.affectation_possible.values("id", "nom"))
    
    
class GetUserSerializerTwo(serializers.ModelSerializer):
    # pays = PaysSerializer()
    date_joined_formatted = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = "__all__"

    def get_date_joined_formatted(self, obj):
        # Formatez la date selon vos besoins
        return obj.date_joined.strftime("%d.%m.%Y à %H:%M:%S")


class AddUserSerializerTwo(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "email_cc",
            "address",
            "activation",
            "telephone",
            "profession",
            "role",
            "pays",
        ]
        
        
class AddUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    activation = serializers.BooleanField(default=True)
    pays = serializers.PrimaryKeyRelatedField(
        queryset=Pays.objects.all(),
        required=True,
        error_messages={
            'does_not_exist': 'Le pays sélectionné n\'existe pas.',
            'incorrect_type': 'Veuillez fournir un ID de pays valide.'
        }
    )
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        many=True,
        required=False,
    )
    affectation = serializers.PrimaryKeyRelatedField(
        queryset=Pays.objects.all(),
        many=True,
        required=False,
    )
    affectation_possible = serializers.PrimaryKeyRelatedField(
        queryset=Pays.objects.all(),
        many=True,
        required=False,
    )
    is_staff = serializers.BooleanField(required=False, default=False)
    is_superuser = serializers.BooleanField(required=False, default=False)
    is_client = serializers.BooleanField(required=False, default=False)
    
    class Meta:
        model = User
        fields = [
            "username", "first_name", "last_name", "email",
            "email_cc", "address", "activation", "telephone",
            "profession", "role", "pays", "password",
            "groups", "affectation", "affectation_possible",
            "is_staff", "is_superuser", "is_client"
        ]
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'role': {'required': True},
            'pays': {'required': True},
        }
    
    def validate(self, data):
        # Validation de l'email
        if User.objects.filter(email__iexact=data.get('email', '')).exists():
            raise serializers.ValidationError({
                "email": "Cet email est déjà utilisé par un autre utilisateur."
            })
        
        # Validation du username
        if User.objects.filter(username__iexact=data.get('username', '')).exists():
            raise serializers.ValidationError({
                "username": "Ce nom d'utilisateur est déjà pris."
            })
        
        # S'assurer que le pays existe
        if 'pays' in data and not Pays.objects.filter(id=data['pays'].id).exists():
            raise serializers.ValidationError({
                "pays": "Le pays sélectionné n'existe pas."
            })
        
        return data
    
    def create(self, validated_data):
        # Extraire le mot de passe
        password = validated_data.pop('password', None)
        groups = validated_data.pop('groups', [])
        affectation = validated_data.pop('affectation', [])
        affectation_possible = validated_data.pop('affectation_possible', [])
        
        # Créer l'utilisateur
        user = User(**validated_data)
        
        # Définir le mot de passe
        if password:
            user.set_password(password)
        else:
            # Générer un mot de passe par défaut
            import secrets
            default_password = secrets.token_urlsafe(12)
            user.set_password(default_password)
        
        user.save()
        if groups:
            user.groups.set(groups)

        if user.pays and user.pays not in affectation:
            affectation.append(user.pays)
        if user.pays and user.pays not in affectation_possible:
            affectation_possible.append(user.pays)

        if affectation:
            user.affectation.set(affectation)
        if affectation_possible:
            user.affectation_possible.set(affectation_possible)
        return user



# serializers.py
class GetUserSerializer(serializers.ModelSerializer):
    pays_id = serializers.IntegerField(source='pays.id', read_only=True)
    pays_nom = serializers.CharField(source='pays.nom', read_only=True)
    date_joined_formatted = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    affectation = serializers.SerializerMethodField()
    affectation_possible = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "email",
            "email_cc", "address", "activation", "telephone", "profession",
            "role", "pays_id", "pays_nom", "date_joined", "date_joined_formatted",
            "last_login",
            "is_staff", "is_superuser", "is_client", "groups",
            "affectation", "affectation_possible"
        ]
    
    def get_date_joined_formatted(self, obj):
        if obj.date_joined:
            return obj.date_joined.strftime("%d.%m.%Y à %H:%M:%S")
        return None

    def get_groups(self, obj):
        return list(obj.groups.values("id", "name"))

    def get_affectation(self, obj):
        return list(obj.affectation.values("id", "nom"))

    def get_affectation_possible(self, obj):
        return list(obj.affectation_possible.values("id", "nom"))


class EditUserSerializer(serializers.ModelSerializer):
    pays = serializers.PrimaryKeyRelatedField(
        queryset=Pays.objects.all(),
        required=False,
        allow_null=True
    )
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        many=True,
        required=False,
    )
    affectation = serializers.PrimaryKeyRelatedField(
        queryset=Pays.objects.all(),
        many=True,
        required=False,
    )
    affectation_possible = serializers.PrimaryKeyRelatedField(
        queryset=Pays.objects.all(),
        many=True,
        required=False,
    )
    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)
    is_client = serializers.BooleanField(required=False)
    
    class Meta:
        model = User
        fields = [
            "username", "first_name", "last_name", "email",
            "email_cc", "address", "activation", "telephone",
            "profession", "role", "pays", "groups",
            "affectation", "affectation_possible",
            "is_staff", "is_superuser", "is_client"
        ]
    
    def validate_email(self, value):
        # Exclure l'utilisateur actuel de la vérification d'unicité
        instance = self.instance
        if instance and User.objects.filter(email__iexact=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        elif not instance and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value
    
    def validate_username(self, value):
        instance = self.instance
        if instance and User.objects.filter(username__iexact=value).exclude(id=instance.id).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        elif not instance and User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value

    def update(self, instance, validated_data):
        groups = validated_data.pop("groups", None)
        affectation = validated_data.pop("affectation", None)
        affectation_possible = validated_data.pop("affectation_possible", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if groups is not None:
            instance.groups.set(groups)

        if affectation is not None:
            if instance.pays and instance.pays not in affectation:
                affectation.append(instance.pays)
            instance.affectation.set(affectation)

        if affectation_possible is not None:
            if instance.pays and instance.pays not in affectation_possible:
                affectation_possible.append(instance.pays)
            instance.affectation_possible.set(affectation_possible)

        return instance


class EditUserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "avatar"]







from rest_framework import serializers

from .models import ElementSurveillance


class ListElementSurveillanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementSurveillance
        fields = [
            "id",
            "nom",
            "code_interne",
            "categorie",
            "sous_categorie",
            "description",
        ]


class AddElementSurveillanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementSurveillance
        fields = ["nom", "code_interne", "categorie", "sous_categorie", "description"]


class DetailElementSurveillanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementSurveillance
        fields = [
            "id",
            "nom",
            "code_interne",
            "categorie",
            "sous_categorie",
            "description",
        ]


class EditElementSurveillanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementSurveillance
        fields = [
            "id",
            "nom",
            "code_interne",
            "categorie",
            "sous_categorie",
            "description",
        ]
        extra_kwargs = {
            "id": {"read_only": True},  # Le champ 'id' est en lecture seule
        }


class SearchElementSurveillanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementSurveillance
        fields = [
            "id",
            "nom",
            "code_interne",
            "categorie",
            "sous_categorie",
            "description",
        ]


from rest_framework import serializers

from .models import (Certification, ConformiteReglementation,
                     InnovationDeveloppement, StrategiePlanification)


class ListCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = [
            "id",
            "acheteur",
            "type_certification",
            "nom_certification",
            "date_obtention",
            "organisme_delivreur",
            "description",
            "couleur_commentaire",
            "commentaire",
        ]

class AddCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = [
            "acheteur",
            "type_certification",
            "nom_certification",
            "date_obtention",
            "organisme_delivreur",
            "description",
            "couleur_commentaire",
            "commentaire",
        ]

class DetailCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = [
            "id",
            "acheteur",
            "type_certification",
            "nom_certification",
            "date_obtention",
            "organisme_delivreur",
            "description",
            "couleur_commentaire",
            "commentaire",
        ]

class EditCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = [
            "id",
            "acheteur",
            "type_certification",
            "nom_certification",
            "date_obtention",
            "organisme_delivreur",
            "description",
            "couleur_commentaire",
            "commentaire",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }

class SearchCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = [
            "id",
            "acheteur",
            "type_certification",
            "nom_certification",
            "date_obtention",
            "organisme_delivreur",
            "description",
            "couleur_commentaire",
            "commentaire",
        ]
        
###########################################################################    
#    
# CERTIFICATION ACHETEUR 
#    
###########################################################################   

class CertificationOneSerializer(serializers.ModelSerializer):
    acheteur_info = serializers.SerializerMethodField()
    type_certification_display = serializers.CharField(source='get_type_display', read_only=True)
    created_by = UserSimpleOneSerializer(read_only=True)
    updated_by = UserSimpleOneSerializer(read_only=True)

    class Meta:
        model = Certification
        fields = [
            'id',
            'acheteur',
            'acheteur_info',
            'type_certification',
            'type_certification_display',
            'nom_certification', 
            'date_obtention',
            'organisme_delivreur',
            'description',
            'couleur_commentaire',
            'commentaire',
            'created_at', 
            'updated_at',
            'created_by', 
            'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'acheteur_info', 'type_certification_display']
    
    def get_acheteur_info(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'code': obj.acheteur.code,
                'sigle': obj.acheteur.sigle
            }
        return None

class CertificationDetailOneSerializer(serializers.ModelSerializer):
    type_certification_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Certification
        fields = ['id', 'acheteur', 'type_certification', 'type_certification_display', 'nom_certification', 
                  'date_obtention', 'organisme_delivreur', 'description', 'couleur_commentaire', 'commentaire']
        read_only_fields = ['type_certification_display']

class AddCertificationOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    
    class Meta:
        model = Certification
        fields = ['type_certification', 'nom_certification', 'date_obtention', 
                  'organisme_delivreur', 'description', 'couleur_commentaire', 'commentaire', 'acheteur']
    
    def create(self, validated_data):
        """Override create method to handle created_by and updated_by"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
            validated_data['updated_by'] = request.user
        
        return super().create(validated_data)
    
    def validate(self, data):
        """Validation globale de la certification"""
        acheteur = data.get('acheteur')
        type_certification = data.get('type_certification')
        nom_certification = data.get('nom_certification', '').strip()
        
        # Vérifier l'unicité selon la contrainte du modèle
        existing = Certification.objects.filter(
            acheteur=acheteur,
            type_certification=type_certification,
            nom_certification=nom_certification
        ).exists()
        
        if existing and self.instance is None:
            raise serializers.ValidationError({
                'nom_certification': 'Cette certification existe déjà pour cet acheteur.'
            })
        
        # Si le type est "autre", vérifier que le nom est renseigné
        if type_certification == 'autre' and not nom_certification:
            raise serializers.ValidationError({
                'nom_certification': 'Le nom de la certification est obligatoire pour le type "Autre".'
            })
        
        return data
    
    def validate_date_obtention(self, value):
        """Validation de la date d'obtention"""
        if value and value > timezone.now().date():
            raise serializers.ValidationError("La date d'obtention ne peut pas être dans le futur.")
        return value
    
    def validate_nom_certification(self, value):
        """Validation du nom de certification"""
        if value:
            value = value.strip()
            if len(value) < 2:
                raise serializers.ValidationError("Le nom de la certification doit contenir au moins 2 caractères.")
        return value

class EditCertificationOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = ['type_certification', 'nom_certification', 'date_obtention', 
                  'organisme_delivreur', 'description', 'couleur_commentaire', 'commentaire']
    
    def update(self, instance, validated_data):
        """Override update method to handle updated_by"""
        # Mettre à jour les champs
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Mettre à jour updated_by si request est dans le contexte
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            instance.updated_by = request.user
        
        instance.save()
        return instance
    
    def validate(self, data):
        """Validation pour l'édition"""
        type_certification = data.get('type_certification', self.instance.type_certification)
        nom_certification = data.get('nom_certification', self.instance.nom_certification or '')
        
        # Vérifier l'unicité
        if 'type_certification' in data or 'nom_certification' in data:
            existing = Certification.objects.filter(
                acheteur=self.instance.acheteur,
                type_certification=type_certification,
                nom_certification=nom_certification.strip()
            ).exclude(id=self.instance.id).exists()
            
            if existing:
                raise serializers.ValidationError({
                    'nom_certification': 'Cette certification existe déjà pour cet acheteur.'
                })
        
        # Si le type est "autre", vérifier que le nom est renseigné
        if type_certification == 'autre' and not nom_certification.strip():
            raise serializers.ValidationError({
                'nom_certification': 'Le nom de la certification est obligatoire pour le type "Autre".'
            })
        
        return data
    
    def validate_date_obtention(self, value):
        """Validation de la date d'obtention"""
        if value and value > timezone.now().date():
            raise serializers.ValidationError("La date d'obtention ne peut pas être dans le futur.")
        return value
    
    def validate_nom_certification(self, value):
        """Validation du nom de certification"""
        if value:
            value = value.strip()
            if len(value) < 2:
                raise serializers.ValidationError("Le nom de la certification doit contenir au moins 2 caractères.")
        return value

class CertificationSearchSerializer(serializers.ModelSerializer):
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    acheteur_code = serializers.CharField(source='acheteur.code', read_only=True)
    type_certification_display = serializers.CharField(source='get_type_certification_display', read_only=True)
    
    class Meta:
        model = Certification
        fields = ['id', 'type_certification', 'type_certification_display', 'nom_certification', 
                  'date_obtention', 'organisme_delivreur', 'commentaire', 'couleur_commentaire', 'acheteur_nom', 'acheteur_code', 
                  'created_at', 'updated_at']





class ListInnovationDeveloppementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InnovationDeveloppement
        fields = [
            "id",
            "acheteur",
            "type_innovation",
            "titre",
            "description",
            "date_debut",
            "date_fin",
            "couleur_commentaire",
            "commentaire",
        ]

class AddInnovationDeveloppementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InnovationDeveloppement
        fields = [
            "acheteur",
            "type_innovation",
            "titre",
            "description",
            "date_debut",
            "date_fin",
            "couleur_commentaire",
            "commentaire",
        ]

class DetailInnovationDeveloppementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InnovationDeveloppement
        fields = [
            "id",
            "acheteur",
            "type_innovation",
            "titre",
            "description",
            "date_debut",
            "date_fin",
            "couleur_commentaire",
            "commentaire",
        ]

class EditInnovationDeveloppementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InnovationDeveloppement
        fields = [
            "id",
            "acheteur",
            "type_innovation",
            "titre",
            "description",
            "date_debut",
            "date_fin",
            "couleur_commentaire",
            "commentaire",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }

class SearchInnovationDeveloppementSerializer(serializers.ModelSerializer):
    class Meta:
        model = InnovationDeveloppement
        fields = [
            "id",
            "acheteur",
            "type_innovation",
            "titre",
            "description",
            "date_debut",
            "date_fin",
            "couleur_commentaire",
            "commentaire",
        ]
        
###########################################################################    
#    
# INNOVATION ET DEVELOPPEMENT 
#    
###########################################################################   

class InnovationDeveloppementOneSerializer(serializers.ModelSerializer):
    acheteur_info = serializers.SerializerMethodField()
    created_by_info = serializers.SerializerMethodField()
    updated_by_info = serializers.SerializerMethodField()
    type_innovation_display = serializers.CharField(source='get_type_innovation_display', read_only=True)
    
    class Meta:
        model = InnovationDeveloppement
        fields = [
            'id', 
            'acheteur', 
            'acheteur_info',
            'type_innovation',
            'type_innovation_display',
            'titre', 
            'description',
            'date_debut',
            'date_fin',
            'couleur_commentaire',
            'commentaire',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_info',
            'updated_by',
            'updated_by_info'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_acheteur_info(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'code': obj.acheteur.code,
                'sigle': obj.acheteur.sigle
            }
        return None
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
                'email': obj.created_by.email,
                'full_name': obj.created_by.get_full_name()
            }
        return None
    
    def get_updated_by_info(self, obj):
        if obj.updated_by:
            return {
                'id': obj.updated_by.id,
                'username': obj.updated_by.username,
                'email': obj.updated_by.email,
                'full_name': obj.updated_by.get_full_name()
            }
        return None

class AddInnovationDeveloppementOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    
    class Meta:
        model = InnovationDeveloppement
        fields = [
            'acheteur',
            'type_innovation',
            'titre',
            'description',
            'date_debut',
            'date_fin',
            'couleur_commentaire',
            'commentaire',
        ]
    
    def validate(self, data):
        """Validation globale"""
        # Vérifier les dates
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')
        
        if date_debut and date_fin and date_fin < date_debut:
            raise serializers.ValidationError({
                'date_fin': 'La date de fin doit être postérieure à la date de début.'
            })
        
        return data

class EditInnovationDeveloppementOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = InnovationDeveloppement
        fields = [
            'type_innovation',
            'titre',
            'description',
            'date_debut',
            'date_fin',
            'couleur_commentaire',
            'commentaire',
        ]
    
    def validate(self, data):
        """Validation pour l'édition"""
        date_debut = data.get('date_debut', self.instance.date_debut)
        date_fin = data.get('date_fin', self.instance.date_fin)
        
        if date_debut and date_fin and date_fin < date_debut:
            raise serializers.ValidationError({
                'date_fin': 'La date de fin doit être postérieure à la date de début.'
            })
        
        return data

class InnovationDeveloppementSearchSerializer(serializers.ModelSerializer):
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    acheteur_code = serializers.CharField(source='acheteur.code', read_only=True)
    type_innovation_display = serializers.CharField(source='get_type_innovation_display', read_only=True)
    
    class Meta:
        model = InnovationDeveloppement
        fields = [
            'id', 
            'acheteur_nom',
            'acheteur_code',
            'type_innovation',
            'type_innovation_display',
            'titre', 
            'description',
            'date_debut',
            'date_fin',
            'couleur_commentaire',
            'commentaire',
            'created_at',
            'updated_at'
        ]








class ListStrategiePlanificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategiePlanification
        fields = [
            "id",
            "acheteur",
            "type_strategie",
            "description",
            "date_mise_en_place",
            "couleur_commentaire",
            "commentaire",
        ]

class AddStrategiePlanificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategiePlanification
        fields = ["acheteur", "type_strategie", "description", "date_mise_en_place", "couleur_commentaire", "commentaire"]

class DetailStrategiePlanificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategiePlanification
        fields = [
            "id",
            "acheteur",
            "type_strategie",
            "description",
            "date_mise_en_place",
            "couleur_commentaire",
            "commentaire",
        ]

class EditStrategiePlanificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategiePlanification
        fields = [
            "id",
            "acheteur",
            "type_strategie",
            "description",
            "date_mise_en_place",
            "couleur_commentaire",
            "commentaire",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }

class SearchStrategiePlanificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategiePlanification
        fields = [
            "id",
            "acheteur",
            "type_strategie",
            "description",
            "date_mise_en_place",
            "couleur_commentaire",
            "commentaire",
        ]
        
###########################################################################    
#    
# STRATEGIE ET PLANIFICATION 
#    
###########################################################################   

class StrategiePlanificationOneSerializer(serializers.ModelSerializer):
    acheteur_info = serializers.SerializerMethodField()
    created_by_info = serializers.SerializerMethodField()
    updated_by_info = serializers.SerializerMethodField()
    type_strategie_display = serializers.CharField(source='get_type_strategie_display', read_only=True)
    
    class Meta:
        model = StrategiePlanification
        fields = [
            'id', 
            'acheteur', 
            'acheteur_info',
            'type_strategie',
            'type_strategie_display',
            'description',
            'date_mise_en_place',
            'couleur_commentaire',
            'commentaire',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_info',
            'updated_by',
            'updated_by_info'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_acheteur_info(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'code': obj.acheteur.code,
                'sigle': obj.acheteur.sigle
            }
        return None
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
                'email': obj.created_by.email,
                'full_name': obj.created_by.get_full_name()
            }
        return None
    
    def get_updated_by_info(self, obj):
        if obj.updated_by:
            return {
                'id': obj.updated_by.id,
                'username': obj.updated_by.username,
                'email': obj.updated_by.email,
                'full_name': obj.updated_by.get_full_name()
            }
        return None

class AddStrategiePlanificationOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    
    class Meta:
        model = StrategiePlanification
        fields = [
            'acheteur',
            'type_strategie',
            'description',
            'date_mise_en_place',
            'couleur_commentaire',
            'commentaire',
        ]
    
    def validate_date_mise_en_place(self, value):
        """Validation de la date de mise en place"""
        if value and value > timezone.now().date():
            raise serializers.ValidationError("La date de mise en place ne peut pas être dans le futur.")
        return value

class EditStrategiePlanificationOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategiePlanification
        fields = [
            'type_strategie',
            'description',
            'date_mise_en_place',
            'couleur_commentaire',
            'commentaire',
        ]
    
    def validate_date_mise_en_place(self, value):
        """Validation de la date de mise en place"""
        if value and value > timezone.now().date():
            raise serializers.ValidationError("La date de mise en place ne peut pas être dans le futur.")
        return value

class StrategiePlanificationSearchSerializer(serializers.ModelSerializer):
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    acheteur_code = serializers.CharField(source='acheteur.code', read_only=True)
    type_strategie_display = serializers.CharField(source='get_type_strategie_display', read_only=True)
    
    class Meta:
        model = StrategiePlanification
        fields = [
            'id', 
            'acheteur_nom',
            'acheteur_code',
            'type_strategie',
            'type_strategie_display',
            'description',
            'date_mise_en_place',
            'couleur_commentaire',
            'commentaire',
            'created_at',
            'updated_at'
        ]










class ListConformiteReglementationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformiteReglementation
        fields = [
            "id",
            "acheteur",
            "type_conformite",
            "statut",
            "details_non_conformite",
            "date_verification",
            "organisme_controle",
            "commentaires",
        ]

class AddConformiteReglementationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformiteReglementation
        fields = [
            "acheteur",
            "type_conformite",
            "statut",
            "details_non_conformite",
            "date_verification",
            "organisme_controle",
            "commentaires",
        ]

class DetailConformiteReglementationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformiteReglementation
        fields = [
            "id",
            "acheteur",
            "type_conformite",
            "statut",
            "details_non_conformite",
            "date_verification",
            "organisme_controle",
            "commentaires",
        ]

class EditConformiteReglementationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformiteReglementation
        fields = [
            "id",
            "acheteur",
            "type_conformite",
            "statut",
            "details_non_conformite",
            "date_verification",
            "organisme_controle",
            "commentaires",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }

class SearchConformiteReglementationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformiteReglementation
        fields = [
            "id",
            "acheteur",
            "type_conformite",
            "statut",
            "details_non_conformite",
            "date_verification",
            "organisme_controle",
            "commentaires",
        ]
        
###########################################################################    
#    
# CONFORMITE ET REGLEMENTATION 
#    
###########################################################################   

class ConformiteReglementationOneSerializer(serializers.ModelSerializer):
    acheteur_info = serializers.SerializerMethodField()
    created_by_info = serializers.SerializerMethodField()
    updated_by_info = serializers.SerializerMethodField()
    type_conformite_display = serializers.CharField(source='get_type_conformite_display', read_only=True)
    statut_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ConformiteReglementation
        fields = [
            'id', 
            'acheteur', 
            'acheteur_info',
            'type_conformite',
            'type_conformite_display',
            'statut',
            'statut_display',
            'details_non_conformite',
            'date_verification',
            'organisme_controle',
            'commentaires',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_info',
            'updated_by',
            'updated_by_info'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_acheteur_info(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'code': obj.acheteur.code,
                'sigle': obj.acheteur.sigle
            }
        return None
    
    def get_created_by_info(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
                'email': obj.created_by.email,
                'full_name': obj.created_by.get_full_name()
            }
        return None
    
    def get_updated_by_info(self, obj):
        if obj.updated_by:
            return {
                'id': obj.updated_by.id,
                'username': obj.updated_by.username,
                'email': obj.updated_by.email,
                'full_name': obj.updated_by.get_full_name()
            }
        return None
    
    def get_statut_display(self, obj):
        return "Conforme" if obj.statut else "Non-conforme"

class AddConformiteReglementationOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    
    class Meta:
        model = ConformiteReglementation
        fields = [
            'acheteur',
            'type_conformite',
            'statut',
            'details_non_conformite',
            'date_verification',
            'organisme_controle',
            'commentaires'
        ]
    
    def validate(self, data):
        """Validation globale"""
        statut = data.get('statut', True)
        details_non_conformite = data.get('details_non_conformite')
        
        # Si non-conforme, les détails de non-conformité sont requis
        if not statut and not details_non_conformite:
            raise serializers.ValidationError({
                'details_non_conformite': 'Les détails de la non-conformité sont requis lorsque le statut est "Non-conforme".'
            })
        
        # Si conforme, effacer les détails de non-conformité
        if statut and details_non_conformite:
            data['details_non_conformite'] = None
        
        # Validation de la date
        date_verification = data.get('date_verification')
        if date_verification and date_verification > timezone.now().date():
            raise serializers.ValidationError({
                'date_verification': 'La date de vérification ne peut pas être dans le futur.'
            })
        
        return data

class EditConformiteReglementationOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConformiteReglementation
        fields = [
            'type_conformite',
            'statut',
            'details_non_conformite',
            'date_verification',
            'organisme_controle',
            'commentaires'
        ]
    
    def validate(self, data):
        """Validation pour l'édition"""
        statut = data.get('statut', self.instance.statut)
        details_non_conformite = data.get('details_non_conformite', self.instance.details_non_conformite)
        
        # Si non-conforme, les détails de non-conformité sont requis
        if not statut and not details_non_conformite:
            raise serializers.ValidationError({
                'details_non_conformite': 'Les détails de la non-conformité sont requis lorsque le statut est "Non-conforme".'
            })
        
        # Si conforme, effacer les détails de non-conformité
        if statut and details_non_conformite:
            data['details_non_conformite'] = None
        
        # Validation de la date
        date_verification = data.get('date_verification', self.instance.date_verification)
        if date_verification and date_verification > timezone.now().date():
            raise serializers.ValidationError({
                'date_verification': 'La date de vérification ne peut pas être dans le futur.'
            })
        
        return data

class ConformiteReglementationSearchSerializer(serializers.ModelSerializer):
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    acheteur_code = serializers.CharField(source='acheteur.code', read_only=True)
    type_conformite_display = serializers.CharField(source='get_type_conformite_display', read_only=True)
    statut_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ConformiteReglementation
        fields = [
            'id', 
            'acheteur_nom',
            'acheteur_code',
            'type_conformite',
            'type_conformite_display',
            'statut',
            'statut_display',
            'details_non_conformite',
            'date_verification',
            'organisme_controle',
            'commentaires',
            'created_at',
            'updated_at'
        ]
    
    def get_statut_display(self, obj):
        return "Conforme" if obj.statut else "Non-conforme"











from rest_framework import serializers

from main.models import AlerteLog


class ListAlerteLogSerializer(serializers.ModelSerializer):
    portefeuille = PortefeuilleSerializer()
    acheteur = AcheteurSerializer()
    element_surveille = ListElementSurveillanceSerializer()

    class Meta:
        model = AlerteLog
        fields = [
            "id",
            "portefeuille",
            "acheteur",
            "element_surveille",
            "date_creation",
            "message",
            "lu",
        ]


class AddAlerteLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlerteLog
        fields = [
            "portefeuille",
            "acheteur",
            "element_surveille",
            "message",
            "content_type",
            "object_id",
        ]


class DetailAlerteLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlerteLog
        fields = [
            "id",
            "portefeuille",
            "acheteur",
            "element_surveille",
            "date_creation",
            "message",
            "lu",
            "content_type",
            "object_id",
        ]


class EditAlerteLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlerteLog
        fields = [
            "id",
            "portefeuille",
            "acheteur",
            "element_surveille",
            "message",
            "lu",
            "content_type",
            "object_id",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
        }


class SearchAlerteLogSerializer(serializers.ModelSerializer):
    portefeuille = PortefeuilleSerializer()
    acheteur = AcheteurSerializer()
    element_surveille = ListElementSurveillanceSerializer()

    class Meta:
        model = AlerteLog
        fields = [
            "id",
            "portefeuille",
            "acheteur",
            "element_surveille",
            "date_creation",
            "message",
            "lu",
            "content_type",
            "object_id",
        ]







class AssetsSerializer(serializers.ModelSerializer):
    """Serializer générique pour la lecture (liste et détail)."""
    
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Propriétés calculées
    a_vue = serializers.SerializerMethodField()
    pret_interbancaire = serializers.SerializerMethodField()
    creance_sur_la_clientele = serializers.SerializerMethodField()
    porteuille_papier_commercial = serializers.SerializerMethodField()
    autres_concours_clients = serializers.SerializerMethodField()
    total_assets = serializers.SerializerMethodField()

    class Meta:
        model = Assets
        fields = "__all__"  # Affiche tous les champs du modèle
    
    def to_representation(self, instance):
        """Ajouter des logs pour voir ce qui est sérialisé"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Sérialisation de l'asset ID: {instance.id}")
        logger.info(f"Type de bilan: {instance.type_bilan}")
        logger.info(f"Année: {instance.annee}")
        logger.info(f"Valeurs importantes: caisse={instance.caisse}, immobilisation_corporelle={instance.immobilisation_corporelle}")
        
        representation = super().to_representation(instance)
        logger.info(f"Représentation sérialisée (premiers champs): {dict(list(representation.items())[:10])}")
        
        return representation
    
    def get_a_vue(self, obj):
        return obj.a_vue
    
    def get_pret_interbancaire(self, obj):
        return obj.pret_interbancaire
    
    def get_creance_sur_la_clientele(self, obj):
        return obj.creance_sur_la_clientele
    
    def get_porteuille_papier_commercial(self, obj):
        return obj.porteuille_papier_commercial
    
    def get_autres_concours_clients(self, obj):
        return obj.autres_concours_clients
    
    def get_total_assets(self, obj):
        return obj.total_assets


class AddAssetsSerializer(serializers.ModelSerializer):
    """Serializer pour l'ajout d'un nouvel actif."""

    class Meta:
        model = Assets
        # Exclut les champs auto-gérés et inutiles pour l'ajout
        exclude = ("created_at", "updated_at", "created_by", "updated_by")
    
    def create(self, validated_data):
        # Récupère l'utilisateur actuel de manière sécurisée
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data["created_by"] = request.user
        else:
            validated_data["created_by"] = None
            
        return super().create(validated_data)


class DetailAssetsSerializer(serializers.ModelSerializer):
    """Serializer pour l'ajout d'un nouvel actif."""

    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = Assets
        fields = "__all__"  # Affiche tous les champs du modèle


class EditAssetsSerializer(serializers.ModelSerializer):
    """Serializer pour la modification d'un actif."""

    class Meta:
        model = Assets
        exclude = ("created_at", "updated_at", "created_by", "updated_by")
    
    def update(self, instance, validated_data):
        # Assigne l'utilisateur connecté à updated_by
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data["updated_by"] = request.user
        else:
            validated_data["updated_by"] = None
        return super().update(instance, validated_data)







class LiabilitiesSerializer(serializers.ModelSerializer):
    """
    Serializer générique pour la lecture des passifs (liste et détail).
    Affiche les détails des objets liés (Année, Acheteur, etc.).
    """

    # Relations avec d'autres modèles (en lecture seule)
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Propriétés calculées du modèle
    a_vue = serializers.ReadOnlyField()
    dette_interbancaire = serializers.ReadOnlyField()
    dette_envers_clientelle = serializers.ReadOnlyField()
    total_liabilities = serializers.ReadOnlyField()

    class Meta:
        model = Liabilities
        # Inclut tous les champs du modèle et les propriétés définies ci-dessus
        fields = "__all__"


# ---


class AddLiabilitiesSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'ajout (création) d'un nouvel enregistrement de passif.
    """

    class Meta:
        model = Liabilities
        # Exclut les champs auto-gérés et inutiles pour l'ajout
        exclude = ("created_at", "updated_at", "created_by", "updated_by")
    
    def create(self, validated_data):
        # Récupère l'utilisateur actuel de manière sécurisée
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data["created_by"] = request.user
        else:
            validated_data["created_by"] = None
            
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Personnalise la méthode de mise à jour pour assigner automatiquement
        l'utilisateur connecté au champ 'updated_by'.
        """
        # Assigne l'utilisateur qui fait la mise à jour
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data["updated_by"] = request.user
        else:
            validated_data["updated_by"] = None
            
        return super().update(validated_data)






class ExpensesSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture des Dépenses (liste et détail).

    Ce serializer inclut les détails des objets liés (Année, Acheteur, etc.)
    et expose les propriétés calculées du modèle comme des champs en lecture seule.
    """

    # Relations avec d'autres modèles (en lecture seule pour l'affichage)
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Propriétés calculées du modèle exposées en lecture seule
    interet_charges_assimilee = serializers.ReadOnlyField()
    charge_sur_operation_financiere = serializers.ReadOnlyField()
    prestation = serializers.ReadOnlyField()
    frais_generaux_dexploitation = serializers.ReadOnlyField()
    total_des_charges = serializers.ReadOnlyField()

    class Meta:
        model = Expenses
        # Inclut tous les champs du modèle ainsi que les propriétés définies ci-dessus
        fields = "__all__"


# ---


class AddExpensesSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'ajout et la modification d'un enregistrement de Dépense.
    """

    class Meta:
        model = Expenses
        # Exclut les champs gérés automatiquement par le système.
        # Le champ 'total_charges' est aussi exclu car il est calculé par la propriété.
        exclude = (
            "total_charges",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )

    def create(self, validated_data):
        """
        Personnalise la méthode de création pour assigner automatiquement
        l'utilisateur connecté au champ 'created_by'.
        """
        # Assigne l'utilisateur qui fait la mise à jour
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data["created_by"] = request.user
        else:
            validated_data["created_by"] = None
            
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Personnalise la méthode de mise à jour pour assigner automatiquement
        l'utilisateur connecté au champ 'updated_by'.
        """
        # Assigne l'utilisateur qui fait la mise à jour
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data["updated_by"] = request.user
        else:
            validated_data["updated_by"] = None
            
        return super().update(validated_data)
    
    
        


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture des Produits (Compte de Résultat).
    Expose les champs du modèle ainsi que les totaux calculés via les propriétés.
    """

    # Nested serializers pour afficher les détails des objets liés
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Exposition des propriétés du modèle comme des champs en lecture seule
    interet_produit_assimile = serializers.ReadOnlyField()
    revenu_d_operation_financiere = serializers.ReadOnlyField()
    autres_produits_exploitation = serializers.ReadOnlyField()
    total_produit = serializers.ReadOnlyField()

    class Meta:
        model = Products
        fields = "__all__"


# ---


class AddProductSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'ajout et la modification d'un enregistrement de Produit.
    """

    class Meta:
        model = Products
        # Exclut les champs qui sont automatiquement gérés par le système
        exclude = ("created_at", "updated_at", "created_by", "updated_by")

    def create(self, validated_data):
        """
        Personnalise la méthode de création pour assigner automatiquement
        l'utilisateur connecté au champ 'created_by'.
        """
        # Assigne l'utilisateur qui fait la mise à jour
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data["created_by"] = request.user
        else:
            validated_data["created_by"] = None
            
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Personnalise la méthode de mise à jour pour assigner automatiquement
        l'utilisateur connecté au champ 'updated_by'.
        """
        # Assigne l'utilisateur qui fait la mise à jour
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data["updated_by"] = request.user
        else:
            validated_data["updated_by"] = None
            
        return super().update(validated_data)







class OffBalanceSheetSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture des données du Hors Bilan.
    """
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Totaux calculés
    total_engagement_financement_donne = serializers.ReadOnlyField()
    total_engagement_garantie_donne = serializers.ReadOnlyField()
    total_engagements_donnes = serializers.ReadOnlyField()
    total_engagement_financement_recu = serializers.ReadOnlyField()
    total_engagements_recus = serializers.ReadOnlyField()
    total_general = serializers.ReadOnlyField()

    class Meta:
        model = OffBalanceSheet
        fields = [
            "id",
            "type_bilan",
            "annee",
            "semestre",
            "acheteur",
            # Champs des engagements
            "en_faveur_des_ets_credit",
            "en_faveur_clientele",
            "pour_compte_ets_credit",
            "pour_compte_clientele",
            "engagement_sur_titre",
            "recu_ets_credit",
            "recu_ets_credit2",
            "recu_clientele",
            "engagement_sur_titre2",
            # Totaux calculés
            "total_engagement_financement_donne",
            "total_engagement_garantie_donne",
            "total_engagements_donnes",
            "total_engagement_financement_recu",
            "total_engagements_recus",
            "total_general",
            # Champs de suivi
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]


class AddOffBalanceSheetSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création d'une instance OffBalanceSheet.
    """
    class Meta:
        model = OffBalanceSheet
        fields = [
            # Champs d'identification
            "type_bilan",
            "annee",
            "semestre",
            "acheteur",
            # Champs des engagements
            "en_faveur_des_ets_credit",
            "en_faveur_clientele",
            "pour_compte_ets_credit",
            "pour_compte_clientele",
            "engagement_sur_titre",
            "recu_ets_credit",
            "recu_ets_credit2",
            "recu_clientele",
            "engagement_sur_titre2",
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data["created_by"] = request.user
        return super().create(validated_data)


class EditOffBalanceSheetSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'édition des données hors bilan.
    """
    class Meta:
        model = OffBalanceSheet
        fields = [
            # Champs d'identification
            "type_bilan",
            "annee",
            "semestre",
            # Champs des engagements
            "en_faveur_des_ets_credit",
            "en_faveur_clientele",
            "pour_compte_ets_credit",
            "pour_compte_clientele",
            "engagement_sur_titre",
            "recu_ets_credit",
            "recu_ets_credit2",
            "recu_clientele",
            "engagement_sur_titre2",
        ]

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data["updated_by"] = request.user
        return super().update(instance, validated_data) 
    
      
class GetOffBalanceSheetSerializer(serializers.ModelSerializer):
    """Serializer utilisé par la vue EditAcheteurOffBalanceSheetView (GET)"""
    annee = AnneeSerializer(read_only=True)
    
    class Meta:
        model = OffBalanceSheet
        fields = [
            "id",
            "type_bilan",
            "annee",
            "semestre",
            "en_faveur_des_ets_credit",
            "en_faveur_clientele",
            "pour_compte_ets_credit",
            "pour_compte_clientele",
            "engagement_sur_titre",
            "recu_ets_credit",
            "recu_ets_credit2",
            "recu_clientele",
            "engagement_sur_titre2",
            "total_engagements_donnes",
            "total_engagements_recus",
            "total_general",
        ]


# Vues compatibles avec votre template actuel
class LegacyListOffBalanceSheetView(APIView):
    """Vue compatible avec votre template actuel"""
    permission_classes = [IsAuthenticated]

    def get(self, request, acheteur_id, *args, **kwargs):
        # Cette vue utilise les mêmes paramètres que votre template
        page_number = request.query_params.get("page", 1)
        search_term = request.query_params.get("search", "")
        
        # Appeler la nouvelle vue
        list_view = ListAcheteurOffBalanceSheetView()
        return list_view.get(request, acheteur_id)    
   
   
   
   
   
        
        
# Fichier: DANS VOTRE FICHIER serializers.py

from rest_framework import serializers

from .models import ActifIFRS, PassifIFRS, RatiosIFRS, ResultatIFRS

# Assurez-vous d'importer vos autres serializers (AnneeSerializer, etc.)
# from .serializers import AnneeSerializer, AcheteurSerializer, UserSerializer


class ActifIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture (détail) d'un actif IFRS.
    Inclut les objets liés et le total calculé.
    """

    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Propriété calculée du modèle
    total_actif_non_courant = serializers.ReadOnlyField()
    total_actif_courant = serializers.ReadOnlyField()
    total_actif = serializers.ReadOnlyField()

    class Meta:
        model = ActifIFRS
        fields = "__all__"


class AddActifIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'ajout et la modification d'un actif IFRS.
    """

    class Meta:
        model = ActifIFRS
        # Exclut les champs auto-gérés
        exclude = ("created_at", "updated_at", "created_by", "updated_by")

    def create(self, validated_data):
        # Assigne l'utilisateur qui effectue la création
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Assigne l'utilisateur qui effectue la mise à jour
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


# Fichier: DANS VOTRE FICHIER serializers.py


class PassifIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture d'un passif et capitaux propres IFRS.
    """

    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Propriétés calculées
    total_capitaux_propres = serializers.ReadOnlyField()
    total_passif_non_courant = serializers.ReadOnlyField()
    total_passif_courant = serializers.ReadOnlyField()
    total_passif = serializers.ReadOnlyField()

    class Meta:
        model = PassifIFRS
        fields = "__all__"


class AddPassifIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création et la modification d'un passif IFRS.
    """

    class Meta:
        model = PassifIFRS
        exclude = ("created_at", "updated_at", "created_by", "updated_by")

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


# Fichier: DANS VOTRE FICHIER serializers.py


class ResultatIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture d'un compte de résultat IFRS.
    """

    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Exposition des soldes intermédiaires de gestion
    # --- DÉBUT DE LA MODIFICATION ---
    # Déclaration des nouvelles propriétés de calcul
    chiffre_affaires = serializers.ReadOnlyField()
    autres_produits_operationnels = serializers.ReadOnlyField()
    total_produits = serializers.ReadOnlyField()
    cout_des_ventes = serializers.ReadOnlyField()
    charges_operationnelles = serializers.ReadOnlyField()
    amortissements_et_provisions = serializers.ReadOnlyField()
    total_charges = serializers.ReadOnlyField()
    resultat_operationnel = serializers.ReadOnlyField()
    resultat_financier = serializers.ReadOnlyField()
    resultat_avant_impot = serializers.ReadOnlyField()
    resultat_net = serializers.ReadOnlyField()
    # --- FIN DE LA MODIFICATION ---

    class Meta:
        model = ResultatIFRS
        fields = "__all__"


class AddResultatIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'ajout et la modification d'un compte de résultat IFRS.
    """

    class Meta:
        model = ResultatIFRS
        exclude = ("created_at", "updated_at", "created_by", "updated_by")

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


# Fichier: serializers.py

# Fichier: serializers.py


class RatiosIFRSSerializer(serializers.ModelSerializer):
    """
    Serializer pour la lecture des ratios financiers.
    """

    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)

    # Assurez-vous que TOUS ces ratios sont déclarés ici
    roa = serializers.ReadOnlyField()
    roe = serializers.ReadOnlyField()
    liquidite_generale = serializers.ReadOnlyField()
    liquidite_immediate = serializers.ReadOnlyField()
    ratio_endettement_total = serializers.ReadOnlyField()
    ratio_couverture_interets = serializers.ReadOnlyField()
    marge_brute = serializers.ReadOnlyField()
    marge_operationnelle = serializers.ReadOnlyField()
    marge_nette = serializers.ReadOnlyField()
    rotation_des_actifs = serializers.ReadOnlyField()
    dso = serializers.ReadOnlyField()

    class Meta:
        model = RatiosIFRS
        # La liste fields DOIT contenir les noms exacts des ratios
        fields = [
            "id",
            "annee",
            "acheteur",
            "roa",
            "roe",
            "liquidite_generale",  # <--- Ce champ doit être ici
            "liquidite_immediate",
            "ratio_endettement_total",  # <--- Et celui-ci aussi
            "ratio_couverture_interets",
            "marge_brute",
            "marge_operationnelle",
            "marge_nette",
            "rotation_des_actifs",
            "dso",
        ]





class UserSimpleSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class TelephoneAcheteurSerializer(serializers.ModelSerializer):
    created_by = UserSimpleSerializer(read_only=True)
    updated_by = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = TelephoneAcheteur
        fields = [
            "id", 
            "telephone", 
            "acheteur",
            "created_at", 
            "updated_at",
            "created_by", 
            "updated_by"
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]


class GetTelephoneAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephoneAcheteur
        fields = "__all__"


class AddTelephoneAcheteurSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    
    def create(self, validated_data):
        # Récupérer l'utilisateur du contexte (passé par la vue)
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['updated_by'] = user
        return super().create(validated_data)
    
    class Meta:
        model = TelephoneAcheteur
        fields = ["telephone", "nom", "acheteur"]

    def validate_telephone(self, value):
        """Validation du numéro de téléphone fixe"""
        import re
        
        cleaned = re.sub(r'\D', '', value)
        
        if not cleaned:
            raise serializers.ValidationError("Le numéro de téléphone est requis.")
        
        if len(cleaned) < 6:
            raise serializers.ValidationError(
                "Le numéro de téléphone doit contenir au moins 6 chiffres."
            )
        
        if len(cleaned) > 15:
            raise serializers.ValidationError(
                "Le numéro de téléphone ne peut pas dépasser 15 chiffres."
            )
        
        return value
     

class EditTelephoneAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephoneAcheteur
        fields = ["telephone", "nom", "updated_by"]
        
    def update(self, instance, validated_data):
        # Récupérer l'utilisateur du contexte (passé par la vue)
        user = self.context['request'].user
        validated_data['updated_by'] = user
        return super().update(instance, validated_data)
    
    def validate_telephone(self, value):
        """Même validation que pour l'ajout"""
        import re
        
        # Nettoyer le numéro
        cleaned = re.sub(r'\D', '', value)
        
        # Validation de base
        if not cleaned:
            raise serializers.ValidationError("Le numéro de téléphone est requis.")
        
        if len(cleaned) < 6:
            raise serializers.ValidationError(
                "Le numéro de téléphone doit contenir au moins 6 chiffres."
            )
        
        if len(cleaned) > 15:
            raise serializers.ValidationError(
                "Le numéro de téléphone ne peut pas dépasser 15 chiffres."
            )
        
        return value 
 
 
        
        
class AdresseAcheteurSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = AdresseAcheteur
        fields = "__all__"

class GetAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = "__all__"


class AddAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = [
            "adresse",
            "acheteur",
        ]


class EditAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = [
            "adresse",
        ]
        
class AdresseAcheteurSerializer(serializers.ModelSerializer):
    acheteur_nom = serializers.SerializerMethodField()
    created_by_nom = serializers.SerializerMethodField()
    updated_by_nom = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    updated_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = AdresseAcheteur
        fields = [
            'id',
            'adresse',
            'acheteur',
            'acheteur_nom',
            'created_at',
            'updated_at',
            'created_at_formatted',
            'updated_at_formatted',
            'created_by',
            'created_by_nom',
            'updated_by',
            'updated_by_nom'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_acheteur_nom(self, obj):
        return obj.acheteur.nom if obj.acheteur else None
    
    def get_created_by_nom(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None
    
    def get_updated_by_nom(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else None
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else None
    
    def get_updated_at_formatted(self, obj):
        return obj.updated_at.strftime('%d/%m/%Y %H:%M') if obj.updated_at else None

class AdresseAcheteurCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = ['adresse', 'rue', 'numero_porte', 'bp', 'nom', 'acheteur']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user if request else None
        return super().create(validated_data)

class AdresseAcheteurUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = ['adresse', 'rue', 'numero_porte', 'bp', 'nom']

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request:
            instance.updated_by = request.user
        return super().update(instance, validated_data)
        
        
        
        
        
        
class PortableAcheteurSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = PortableAcheteur
        fields = "__all__"

class GetPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = "__all__"


class AddPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = ["portable", "nom", "acheteur"]


class EditPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = ["portable", "nom"]
       
        
class UserSimpleSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class PortableAcheteurSerializer(serializers.ModelSerializer):
    created_by = UserSimpleSerializer(read_only=True)
    updated_by = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = PortableAcheteur
        fields = [
            "id", 
            "portable", 
            "acheteur",
            "created_at", 
            "updated_at",
            "created_by", 
            "updated_by"
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]


class AddPortableAcheteurSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    
    class Meta:
        model = PortableAcheteur
        fields = ["portable", "acheteur"]  # Enlever created_by
    
    def validate_portable(self, value):
        """Validation du numéro de portable"""
        import re
        
        cleaned = re.sub(r'\D', '', value)
        
        if not cleaned:
            raise serializers.ValidationError("Le numéro de portable est requis.")
        
        if len(cleaned) < 8:
            raise serializers.ValidationError(
                "Le numéro de portable doit contenir au moins 8 chiffres."
            )
        
        if len(cleaned) > 15:
            raise serializers.ValidationError(
                "Le numéro de portable ne peut pas dépasser 15 chiffres."
            )
        
        return value
     

class EditPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = ["portable", "updated_by"]
    
    def validate_portable(self, value):
        """Même validation que pour l'ajout"""
        import re
        
        # Nettoyer le numéro
        cleaned = re.sub(r'\D', '', value)
        
        # Validation de base
        if not cleaned:
            raise serializers.ValidationError("Le numéro de portable est requis.")
        
        if len(cleaned) < 8:
            raise serializers.ValidationError(
                "Le numéro de portable doit contenir au moins 8 chiffres."
            )
        
        if len(cleaned) > 15:
            raise serializers.ValidationError(
                "Le numéro de portable ne peut pas dépasser 15 chiffres."
            )
        
        return value    
        
        
        
        
        
        
        
        
        
        
        
class EmailAcheteurSerializer(serializers.ModelSerializer):
    created_by = UserSimpleSerializer(read_only=True)
    updated_by = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = EmailAcheteur
        fields = [
            "id", 
            "email", 
            "acheteur",
            "created_at", 
            "updated_at",
            "created_by", 
            "updated_by"
        ]
        read_only_fields = ["created_at", "updated_at", "created_by", "updated_by"]


class GetEmailAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAcheteur
        fields = "__all__"


class AddEmailAcheteurSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )

    class Meta:
        model = EmailAcheteur
        fields = ["email", "description", "acheteur"]
    
    def validate_email(self, value):
        """Validation de l'adresse email"""
        # Normaliser l'email (minuscules, suppression des espaces)
        email = value.strip().lower()
        
        # Vérifier la longueur
        if len(email) > 254:
            raise serializers.ValidationError(
                "L'adresse email ne peut pas dépasser 254 caractères."
            )
        
        # Vérifier le format avec une regex simple
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise serializers.ValidationError(
                "Veuillez saisir une adresse email valide."
            )
        
        # Vérification Django
        try:
            validate_email(email)
        except DjangoValidationError:
            raise serializers.ValidationError(
                "Adresse email invalide."
            )
        
        return email


class EditEmailAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAcheteur
        fields = ["email", "description", "updated_by"]
    
    def validate_email(self, value):
        """Même validation que pour l'ajout"""
        # Normaliser l'email (minuscules, suppression des espaces)
        email = value.strip().lower()
        
        # Vérifier la longueur
        if len(email) > 254:
            raise serializers.ValidationError(
                "L'adresse email ne peut pas dépasser 254 caractères."
            )
        
        # Vérifier le format avec une regex simple
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise serializers.ValidationError(
                "Veuillez saisir une adresse email valide."
            )
        
        # Vérification Django
        try:
            validate_email(email)
        except DjangoValidationError:
            raise serializers.ValidationError(
                "Adresse email invalide."
            )
        
        return email
    
    
    
    
    
    
        
        
        
        
        
class DocumentSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = Document
        fields = "__all__"

class GetDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"

class AddDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "acheteur",
            "titre",
            "fichier",
            "description",
        ]

class EditDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "titre",
            "description",
            "fichier", # Le fichier est inclus car on pourrait vouloir le remplacer
        ]
        
        
        
        
        
class SwotSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = Swot
        fields = "__all__"

class GetSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = "__all__"

class AddSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = [
            "acheteur",
            "forces",
            "faiblesses",
            "opportunites",
            "menaces",
            "couleur_commentaire",
            "commentaire",
        ]

class EditSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = [
            "forces",
            "faiblesses",
            "opportunites",
            "menaces",
            "couleur_commentaire",
            "commentaire",
        ]
        
        
###########################################################################    
#    
# SWOT ACHETEUR 
#    
###########################################################################   

class SwotOneSerializer(serializers.ModelSerializer):
    created_by = UserSimpleOneSerializer(read_only=True)
    updated_by = UserSimpleOneSerializer(read_only=True)
    acheteur_info = serializers.SerializerMethodField()
    forces_count = serializers.SerializerMethodField()
    faiblesses_count = serializers.SerializerMethodField()
    opportunites_count = serializers.SerializerMethodField()
    menaces_count = serializers.SerializerMethodField()
    total_elements = serializers.SerializerMethodField()
    
    class Meta:
        model = Swot
        fields = [
            'id', 
            'acheteur', 
            'acheteur_info',
            'forces',
            'faiblesses',
            'opportunites',
            'menaces',
            'couleur_commentaire',
            'commentaire',
            'forces_count',
            'faiblesses_count',
            'opportunites_count',
            'menaces_count',
            'total_elements',
            'created_at', 
            'updated_at',
            'created_by', 
            'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'acheteur_info']
    
    def get_acheteur_info(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'code': obj.acheteur.code,
                'sigle': obj.acheteur.sigle
            }
        return None
    
    def get_forces_count(self, obj):
        if obj.forces:
            return len([f for f in obj.forces.split('\n') if f.strip()])
        return 0
    
    def get_faiblesses_count(self, obj):
        if obj.faiblesses:
            return len([f for f in obj.faiblesses.split('\n') if f.strip()])
        return 0
    
    def get_opportunites_count(self, obj):
        if obj.opportunites:
            return len([o for o in obj.opportunites.split('\n') if o.strip()])
        return 0
    
    def get_menaces_count(self, obj):
        if obj.menaces:
            return len([m for m in obj.menaces.split('\n') if m.strip()])
        return 0
    
    def get_total_elements(self, obj):
        return (self.get_forces_count(obj) + 
                self.get_faiblesses_count(obj) + 
                self.get_opportunites_count(obj) + 
                self.get_menaces_count(obj))

class SwotDetailOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = ['id', 'acheteur', 'forces', 'faiblesses', 'opportunites', 'menaces', 'couleur_commentaire', 'commentaire']

class AddSwotOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    
    class Meta:
        model = Swot
        fields = ['acheteur', 'forces', 'faiblesses', 'opportunites', 'menaces', 'couleur_commentaire', 'commentaire']
    
    def validate(self, data):
        """Validation globale de l'analyse SWOT"""
        acheteur = data.get('acheteur')
        
        # Vérifier si une analyse SWOT existe déjà pour cet acheteur
        existing = Swot.objects.filter(acheteur=acheteur).exists()
        
        if existing and self.instance is None:
            raise serializers.ValidationError({
                'acheteur': 'Une analyse SWOT existe déjà pour cet acheteur.'
            })
        
        # Validation du contenu (au moins un champ doit être rempli)
        forces = data.get('forces', '')
        faiblesses = data.get('faiblesses', '')
        opportunites = data.get('opportunites', '')
        menaces = data.get('menaces', '')
        
        if not any([forces, faiblesses, opportunites, menaces]):
            raise serializers.ValidationError({
                'non_field_errors': 'Au moins un des champs (forces, faiblesses, opportunités, menaces) doit être renseigné.'
            })
        
        return data

class EditSwotOneSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Swot
        fields = ['forces', 'faiblesses', 'opportunites', 'menaces', 'couleur_commentaire', 'commentaire']
    
    def validate(self, data):
        """Validation pour l'édition"""
        # Validation du contenu (au moins un champ doit être rempli)
        forces = data.get('forces', self.instance.forces if self.instance else '')
        faiblesses = data.get('faiblesses', self.instance.faiblesses if self.instance else '')
        opportunites = data.get('opportunites', self.instance.opportunites if self.instance else '')
        menaces = data.get('menaces', self.instance.menaces if self.instance else '')
        
        if not any([forces, faiblesses, opportunites, menaces]):
            raise serializers.ValidationError({
                'non_field_errors': 'Au moins un des champs (forces, faiblesses, opportunités, menaces) doit être renseigné.'
            })
        
        return data
        
        
        



        
        
        
class ProduitServiceSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = ProduitService
        fields = "__all__"

class GetProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = "__all__"

class AddProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = [
            "acheteur",
            "produits",
            "services",
            "couleur_commentaire",
            "commentaire",
        ]

class EditProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = [
            "produits",
            "services",
            "couleur_commentaire",
            "commentaire",
        ]
        
        
        
        
        
class MarqueSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = Marque
        fields = "__all__"

class GetMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = "__all__"

class AddMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = [
            "acheteur",
            "marques",
            "couleur_commentaire",
            "commentaire",
        ]

class EditMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = [
            "marques",
            "couleur_commentaire",
            "commentaire",
        ]
        
        
        
        
        
class ProcedureCollectiveSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = ProcedureCollective
        fields = "__all__"

class GetProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = "__all__"

class AddProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = [
            "acheteur",
            "type_procedure",
            "date_ouverture",
            "date_cloture",
            "description",
            "couleur_commentaire",
            "commentaire",
        ]

class EditProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = [
            "type_procedure",
            "date_ouverture",
            "date_cloture",
            "description",
            "couleur_commentaire",
            "commentaire",
        ]
        
###########################################################################    
#    
# PROCEDURE COLLECTIVE ACHETEUR 
#    
###########################################################################   

class ProcedureCollectiveOneSerializer(serializers.ModelSerializer):
    created_by = UserSimpleOneSerializer(read_only=True)
    updated_by = UserSimpleOneSerializer(read_only=True)
    acheteur_info = serializers.SerializerMethodField()
    statut = serializers.SerializerMethodField()
    duree_jours = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcedureCollective
        fields = [
            'id', 
            'acheteur', 
            'acheteur_info',
            'type_procedure',
            'date_ouverture',
            'date_cloture',
            'tribunal',
            'numero_dossier',
            'secteur_activite',
            'description',
            'couleur_commentaire',
            'commentaire',
            'montant_creance',
            'impact_assureur',
            'statut',
            'duree_jours',
            'created_at', 
            'updated_at',
            'created_by', 
            'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'acheteur_info', 'statut', 'duree_jours']
    
    def get_acheteur_info(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'code': obj.acheteur.code,
                'sigle': obj.acheteur.sigle
            }
        return None
    
    def get_statut(self, obj):
        if obj.date_cloture:
            return 'Clôturée'
        return 'En cours'
    
    def get_duree_jours(self, obj):
        if obj.date_ouverture:
            if obj.date_cloture:
                return (obj.date_cloture - obj.date_ouverture).days
            return (datetime.date.today() - obj.date_ouverture).days
        return None

class ProcedureCollectiveDetailOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = ['id', 'acheteur', 'type_procedure', 'date_ouverture', 'date_cloture', 
                  'tribunal', 'numero_dossier', 'secteur_activite', 'description', 'couleur_commentaire', 'commentaire',
                  'montant_creance', 'impact_assureur']

class AddProcedureCollectiveOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    
    class Meta:
        model = ProcedureCollective
        fields = ['acheteur', 'type_procedure', 'date_ouverture', 'date_cloture',
                  'tribunal', 'numero_dossier', 'secteur_activite', 'description',
                  'montant_creance', 'impact_assureur', 'couleur_commentaire', 'commentaire']
    
    def validate(self, data):
        """Validation globale de la procédure collective"""
        date_ouverture = data.get('date_ouverture')
        date_cloture = data.get('date_cloture')
        
        # Validation des dates
        if date_cloture and date_ouverture and date_cloture < date_ouverture:
            raise serializers.ValidationError({
                'date_cloture': 'La date de clôture ne peut pas être antérieure à la date d\'ouverture.'
            })
        
        # Validation du montant
        montant_creance = data.get('montant_creance')
        if montant_creance is not None and montant_creance < 0:
            raise serializers.ValidationError({
                'montant_creance': 'Le montant des créances ne peut pas être négatif.'
            })
        
        return data
    
    def validate_type_procedure(self, value):
        """Validation du type de procédure"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Le type de procédure est obligatoire.")
        return value.strip()

class EditProcedureCollectiveOneSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProcedureCollective
        fields = ['type_procedure', 'date_ouverture', 'date_cloture',
                  'tribunal', 'numero_dossier', 'secteur_activite', 'description',
                  'montant_creance', 'impact_assureur', 'couleur_commentaire', 'commentaire']
    
    def validate(self, data):
        """Validation pour l'édition"""
        date_ouverture = data.get('date_ouverture', self.instance.date_ouverture if self.instance else None)
        date_cloture = data.get('date_cloture', self.instance.date_cloture if self.instance else None)
        
        # Validation des dates
        if date_cloture and date_ouverture and date_cloture < date_ouverture:
            raise serializers.ValidationError({
                'date_cloture': 'La date de clôture ne peut pas être antérieure à la date d\'ouverture.'
            })
        
        # Validation du montant
        montant_creance = data.get('montant_creance', self.instance.montant_creance if self.instance else None)
        if montant_creance is not None and montant_creance < 0:
            raise serializers.ValidationError({
                'montant_creance': 'Le montant des créances ne peut pas être négatif.'
            })
        
        return data
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
class RegistreCommerceSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = RegistreCommerce
        fields = "__all__"

class GetRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = "__all__"

class AddRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = [
            "acheteur",
            "numero",
            "date_inscription",
            "statut_registre",
            "commentaire",
        ]

class EditRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = [
            "numero",
            "date_inscription",
            "statut_registre",
            "commentaire",
        ]

###########################################################################    
#    
# REGISTRE COMMERCE ACHETEUR 
#    
###########################################################################   

class RegistreCommerceOneSerializer(serializers.ModelSerializer):
    acheteur_info = serializers.SerializerMethodField()
    created_by = UserSimpleOneSerializer(read_only=True)
    updated_by = UserSimpleOneSerializer(read_only=True)
    
    class Meta:
        model = RegistreCommerce
        fields = [
            'id',
            'acheteur',
            'acheteur_info',
            'numero',
            'date_inscription',
            'est_actif',
            'statut_registre',
            'commentaire',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'acheteur_info']
    
    def get_acheteur_info(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'code': obj.acheteur.code,
                'sigle': obj.acheteur.sigle
            }
        return None

class RegistreCommerceDetailOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = ['id', 'acheteur', 'numero', 'date_inscription', 'est_actif', 'statut_registre', 'commentaire']

class AddRegistreCommerceOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    
    class Meta:
        model = RegistreCommerce
        fields = ['numero', 'date_inscription', 'est_actif', 'statut_registre', 'commentaire', 'acheteur']
    
    def create(self, validated_data):
        """Override create method to handle created_by and updated_by"""
        acheteur = validated_data.get("acheteur")
        est_actif = validated_data.get("est_actif", False)

        # Créer l'instance
        instance = RegistreCommerce(**validated_data)
        
        # Ajouter created_by et updated_by si request est dans le contexte
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            instance.created_by = request.user
            instance.updated_by = request.user
        
        instance.save()

        # Un seul registre actif par acheteur
        if est_actif and acheteur:
            RegistreCommerce.objects.filter(acheteur=acheteur).exclude(id=instance.id).update(est_actif=False)

        return instance
    
    def validate(self, data):
        """Validation globale du registre de commerce"""
        acheteur = data.get('acheteur')
        numero = data.get('numero')
        
        # Vérifier si ce numéro de registre existe déjà pour cet acheteur
        existing = RegistreCommerce.objects.filter(
            acheteur=acheteur,
            numero=numero
        ).exists()
        
        if existing and self.instance is None:
            raise serializers.ValidationError({
                'numero': 'Ce numéro de registre de commerce est déjà associé à cet acheteur.'
            })
        
        return data
    
    def validate_numero(self, value):
        """Validation du numéro de registre"""
        if not value:
            raise serializers.ValidationError("Le numéro de registre est obligatoire.")
        
        if len(value) < 3:
            raise serializers.ValidationError("Le numéro de registre doit contenir au moins 3 caractères.")
        
        return value.strip()

class EditRegistreCommerceOneSerializer(serializers.ModelSerializer):
    date_inscription_input = serializers.CharField(
        required=False, 
        allow_null=True, 
        allow_blank=True,
        write_only=True
    )
    
    class Meta:
        model = RegistreCommerce
        fields = ['numero', 'date_inscription', 'date_inscription_input', 'est_actif', 'statut_registre', 'commentaire']
        extra_kwargs = {
            'date_inscription': {'read_only': True}  # On gère la date via date_inscription_input
        }
    
    def validate(self, data):
        """Gérer la conversion de date"""
        date_input = data.pop('date_inscription_input', None)
        
        if date_input is not None:
            if date_input.strip() == '':
                data['date_inscription'] = None
            else:
                from datetime import datetime
                
                # Essayez différents formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        data['date_inscription'] = datetime.strptime(date_input.strip(), fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    raise serializers.ValidationError({
                        'date_inscription': 'Format de date invalide. Utilisez JJ/MM/AAAA ou AAAA-MM-JJ.'
                    })
        
        # Validation du numéro
        numero = data.get('numero')
        if self.instance and numero and numero != self.instance.numero:
            existing = RegistreCommerce.objects.filter(
                acheteur=self.instance.acheteur,
                numero=numero
            ).exclude(id=self.instance.id).exists()
            
            if existing:
                raise serializers.ValidationError({
                    'numero': 'Ce numéro de registre de commerce est déjà associé à cet acheteur.'
                })
        
        return data
    
    def validate_numero(self, value):
        if not value:
            raise serializers.ValidationError("Le numéro de registre est obligatoire.")
        
        if len(value) < 3:
            raise serializers.ValidationError("Le numéro de registre doit contenir au moins 3 caractères.")
        
        return value.strip()

    def update(self, instance, validated_data):
        est_actif = validated_data.get("est_actif", instance.est_actif)
        instance = super().update(instance, validated_data)

        # Un seul registre actif par acheteur
        if est_actif and instance.acheteur_id:
            RegistreCommerce.objects.filter(acheteur_id=instance.acheteur_id).exclude(id=instance.id).update(est_actif=False)

        return instance

class RegistreCommerceSearchSerializer(serializers.ModelSerializer):
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    acheteur_code = serializers.CharField(source='acheteur.code', read_only=True)
    
    class Meta:
        model = RegistreCommerce
        fields = ['id', 'numero', 'date_inscription', 'couleur_commentaire', 'commentaire', 'acheteur_nom', 'acheteur_code', 'created_at', 'updated_at']   
        
        
        
        
        
        
        
        
        
        
        

###########################################################################
#  IdentifiantFiscal — Serializers
###########################################################################

class IdentifiantFiscalOneSerializer(serializers.ModelSerializer):
    created_by = UserSimpleOneSerializer(read_only=True)
    updated_by = UserSimpleOneSerializer(read_only=True)

    class Meta:
        model = IdentifiantFiscal
        fields = [
            'id', 'acheteur',
            'nif', 'numero_tva', 'numero_statistique',
            'numero_cnss_employeur', 'numero_national_unique',
            'commentaire',
            'created_at', 'updated_at', 'created_by', 'updated_by',
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class SaveIdentifiantFiscalOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(queryset=Acheteur.objects.all(), required=False)

    class Meta:
        model = IdentifiantFiscal
        fields = [
            'acheteur',
            'nif', 'numero_tva', 'numero_statistique',
            'numero_cnss_employeur', 'numero_national_unique',
            'commentaire',
        ]

    def _clean(self, value):
        return value.strip() if value and value.strip() else None

    def validate(self, data):
        for field in ['nif', 'numero_tva', 'numero_statistique',
                      'numero_cnss_employeur', 'numero_national_unique']:
            if field in data:
                data[field] = self._clean(data[field])
        return data


###########################################################################

class CotisationSerializer(serializers.ModelSerializer):
    acheteur = AcheteurSerializer()

    class Meta:
        model = Cotisation
        fields = "__all__"

class GetCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = "__all__"

class AddCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = [
            "acheteur",
            "numero",
            "date_affiliation",
            "couleur_commentaire",
            "commentaire",
        ]

class EditCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = [
            "numero",
            "date_affiliation",
            "couleur_commentaire",
            "commentaire",
        ]   
        
###########################################################################    
#    
# COTISATION SOCIALE ACHETEUR 
#    
###########################################################################   

class CotisationOneSerializer(serializers.ModelSerializer):
    acheteur_info = serializers.SerializerMethodField()
    created_by = UserSimpleOneSerializer(read_only=True)
    updated_by = UserSimpleOneSerializer(read_only=True)
    
    class Meta:
        model = Cotisation
        fields = [
            'id', 
            'acheteur', 
            'acheteur_info',
            'numero', 
            'date_affiliation',
            'couleur_commentaire',
            'commentaire',
            'created_at', 
            'updated_at',
            'created_by', 
            'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'acheteur_info']
    
    def get_acheteur_info(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'code': obj.acheteur.code,
                'sigle': obj.acheteur.sigle
            }
        return None

class CotisationDetailOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = ['id', 'acheteur', 'numero', 'date_affiliation', 'couleur_commentaire', 'commentaire']

class AddCotisationOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    
    class Meta:
        model = Cotisation
        fields = ['numero', 'date_affiliation', 'couleur_commentaire', 'commentaire', 'acheteur']
    
    def create(self, validated_data):
        """Override create method to handle created_by and updated_by"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
            validated_data['updated_by'] = request.user
        
        return super().create(validated_data)
    
    def validate(self, data):
        """Validation globale de la cotisation sociale"""
        acheteur = data.get('acheteur')
        numero = data.get('numero')
        
        # Vérifier si ce numéro de sécurité sociale existe déjà pour cet acheteur
        existing = Cotisation.objects.filter(
            acheteur=acheteur,
            numero=numero
        ).exists()
        
        if existing and self.instance is None:
            raise serializers.ValidationError({
                'numero': 'Ce numéro de sécurité sociale est déjà associé à cet acheteur.'
            })
        
        return data
    
    def validate_numero(self, value):
        """Validation du numéro de sécurité sociale"""
        if not value:
            raise serializers.ValidationError("Le numéro de sécurité sociale est obligatoire.")
        
        # Vérifier la longueur minimale
        if len(value) < 3:
            raise serializers.ValidationError("Le numéro de sécurité sociale doit contenir au moins 3 caractères.")
        
        # Optionnel: validation spécifique pour les numéros de sécurité sociale
        # Exemple pour la France: 15 chiffres
        # if not value.isdigit() or len(value) != 15:
        #     raise serializers.ValidationError("Le numéro de sécurité sociale doit contenir 15 chiffres.")
        
        return value.strip()

class EditCotisationOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = ['numero', 'date_affiliation', 'couleur_commentaire', 'commentaire']
    
    def update(self, instance, validated_data):
        """Override update method to handle updated_by"""
        # Mettre à jour les champs de base d'abord
        instance.numero = validated_data.get('numero', instance.numero)
        instance.date_affiliation = validated_data.get('date_affiliation', instance.date_affiliation)
        instance.couleur_commentaire = validated_data.get('couleur_commentaire', instance.couleur_commentaire)
        instance.commentaire = validated_data.get('commentaire', instance.commentaire)
        
        # Mettre à jour updated_by si request est dans le contexte
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            instance.updated_by = request.user
        
        instance.save()
        return instance
    
    def validate(self, data):
        """Validation pour l'édition"""
        numero = data.get('numero')
        acheteur = self.instance.acheteur
        
        if numero and numero != self.instance.numero:
            # Vérifier si ce numéro existe déjà pour un autre enregistrement du même acheteur
            existing = Cotisation.objects.filter(
                acheteur=acheteur,
                numero=numero
            ).exclude(id=self.instance.id).exists()
            
            if existing:
                raise serializers.ValidationError({
                    'numero': 'Ce numéro de sécurité sociale est déjà associé à cet acheteur.'
                })
        
        return data
    
    def validate_numero(self, value):
        """Validation du numéro de sécurité sociale"""
        if not value:
            raise serializers.ValidationError("Le numéro de sécurité sociale est obligatoire.")
        
        if len(value) < 3:
            raise serializers.ValidationError("Le numéro de sécurité sociale doit contenir au moins 3 caractères.")
        
        return value.strip()

class CotisationSearchSerializer(serializers.ModelSerializer):
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    acheteur_code = serializers.CharField(source='acheteur.code', read_only=True)
    
    class Meta:
        model = Cotisation
        fields = ['id', 'numero', 'date_affiliation', 'couleur_commentaire', 'commentaire', 'acheteur_nom', 'acheteur_code', 'created_at', 'updated_at'] 
        

        
        
        
        
        
        
# serializers.py
from rest_framework import serializers
from .models import Marque

class ListMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ["id", "acheteur", "marques", "couleur_commentaire", "commentaire", "created_at", "updated_at"]

class AddMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ["acheteur", "marques", "couleur_commentaire", "commentaire"]

class DetailMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ["id", "acheteur", "marques", "couleur_commentaire", "commentaire", "created_at", "updated_at"]

class EditMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ["id", "acheteur", "marques", "couleur_commentaire", "commentaire", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchMarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ["id", "acheteur", "marques", "couleur_commentaire", "commentaire", "created_at", "updated_at"]
        
###########################################################################    
#    
# MARQUE ACHETEUR 
#    
###########################################################################   

class MarqueOneSerializer(serializers.ModelSerializer):
    acheteur_info = serializers.SerializerMethodField()
    created_by = UserSimpleOneSerializer(read_only=True)
    updated_by = UserSimpleOneSerializer(read_only=True)
    
    class Meta:
        model = Marque
        fields = [
            'id', 
            'acheteur', 
            'acheteur_info',
            'marques', 
            'couleur_commentaire',
            'commentaire',
            'created_at', 
            'updated_at',
            'created_by', 
            'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'acheteur_info']
    
    def get_acheteur_info(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'code': obj.acheteur.code,
                'sigle': obj.acheteur.sigle
            }
        return None

class MarqueDetailOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ['id', 'acheteur', 'marques', 'couleur_commentaire', 'commentaire']

class AddMarqueOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    
    class Meta:
        model = Marque
        fields = ['marques', 'couleur_commentaire', 'commentaire', 'acheteur']
    
    def create(self, validated_data):
        """Override create method to handle created_by and updated_by"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
            validated_data['updated_by'] = request.user
        
        return super().create(validated_data)
    
    def validate(self, data):
        """Validation globale des marques"""
        acheteur = data.get('acheteur')
        marques = data.get('marques', '').strip()
        
        # Vérifier si cet acheteur a déjà des marques enregistrées
        # (On suppose qu'un acheteur ne peut avoir qu'un seul enregistrement Marque)
        existing = Marque.objects.filter(
            acheteur=acheteur
        ).exists()
        
        # if existing and self.instance is None:
        #     raise serializers.ValidationError({
        #         'acheteur': 'Cet acheteur possède déjà des marques enregistrées.'
        #     })
        
        # Vérifier que le champ marques est rempli
        if not marques:
            raise serializers.ValidationError({
                'marques': 'Le champ marques est obligatoire.'
            })
        
        return data
    
    def validate_marques(self, value):
        """Validation des marques"""
        if value:
            value = value.strip()
            if len(value) < 3:
                raise serializers.ValidationError("Veuillez fournir une description des marques (au moins 3 caractères).")
        return value

class EditMarqueOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ['marques', 'couleur_commentaire', 'commentaire']
    
    def update(self, instance, validated_data):
        """Override update method to handle updated_by"""
        # Mettre à jour les champs de base
        instance.marques = validated_data.get('marques', instance.marques)
        instance.couleur_commentaire = validated_data.get('couleur_commentaire', instance.couleur_commentaire)
        instance.commentaire = validated_data.get('commentaire', instance.commentaire)
        
        # Mettre à jour updated_by si request est dans le contexte
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            instance.updated_by = request.user
        
        instance.save()
        return instance
    
    def validate(self, data):
        """Validation pour l'édition"""
        marques = data.get('marques')
        
        # Si marques n'est pas dans les données, utiliser la valeur actuelle
        if marques is None:
            marques = self.instance.marques if self.instance else ''
        
        # Vérifier que le champ a du contenu
        if not marques.strip():
            raise serializers.ValidationError({
                'marques': 'Le champ marques est obligatoire.'
            })
        
        return data
    
    def validate_marques(self, value):
        """Validation des marques"""
        if value:
            value = value.strip()
            if len(value) < 3:
                raise serializers.ValidationError("Veuillez fournir une description des marques (au moins 3 caractères).")
        return value

class MarqueSearchSerializer(serializers.ModelSerializer):
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    acheteur_code = serializers.CharField(source='acheteur.code', read_only=True)
    
    class Meta:
        model = Marque
        fields = ['id', 'marques', 'couleur_commentaire', 'commentaire', 'acheteur_nom', 'acheteur_code', 'created_at', 'updated_at']










# serializers.py
from rest_framework import serializers
from .models import ProduitService

class ListProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = ["id", "acheteur", "produits", "services", "couleur_commentaire", "commentaire", "created_at", "updated_at"]

class AddProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = ["acheteur", "produits", "services", "couleur_commentaire", "commentaire"]

class DetailProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = ["id", "acheteur", "produits", "services", "couleur_commentaire", "commentaire", "created_at", "updated_at"]

class EditProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = ["id", "acheteur", "produits", "services", "couleur_commentaire", "commentaire", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchProduitServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = ["id", "acheteur", "produits", "services", "couleur_commentaire", "commentaire", "created_at", "updated_at"]
        
###########################################################################    
#    
# PRODUIT & SERVICE ACHETEUR 
#    
###########################################################################   

class ProduitServiceOneSerializer(serializers.ModelSerializer):
    acheteur_info = serializers.SerializerMethodField()
    created_by = UserSimpleOneSerializer(read_only=True)
    updated_by = UserSimpleOneSerializer(read_only=True)
    
    class Meta:
        model = ProduitService
        fields = [
            'id', 
            'acheteur', 
            'acheteur_info',
            'produits', 
            'services',
            'couleur_commentaire',
            'commentaire',
            'created_at', 
            'updated_at',
            'created_by', 
            'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'acheteur_info']
    
    def get_acheteur_info(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'code': obj.acheteur.code,
                'sigle': obj.acheteur.sigle
            }
        return None

class ProduitServiceDetailOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = ['id', 'acheteur', 'produits', 'services', 'couleur_commentaire', 'commentaire']

class AddProduitServiceOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    
    class Meta:
        model = ProduitService
        fields = ['produits', 'services', 'couleur_commentaire', 'commentaire', 'acheteur']
    
    def create(self, validated_data):
        """Override create method to handle created_by and updated_by"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
            validated_data['updated_by'] = request.user
        
        return super().create(validated_data)
    
    def validate(self, data):
        """Validation globale des produits et services"""
        import re

        def strip_html(value):
            if not value:
                return ''
            return re.sub(r'<[^>]+>', '', str(value)).strip()

        produits = strip_html(data.get('produits'))
        services = strip_html(data.get('services'))

        if not produits and not services:
            raise serializers.ValidationError({
                'non_field_errors': 'Veuillez renseigner au moins un produit ou un service.'
            })

        return data

class EditProduitServiceOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProduitService
        fields = ['produits', 'services', 'couleur_commentaire', 'commentaire']
    
    def update(self, instance, validated_data):
        """Override update method to handle updated_by"""
        # Mettre à jour les champs de base
        instance.produits = validated_data.get('produits', instance.produits)
        instance.services = validated_data.get('services', instance.services)
        instance.couleur_commentaire = validated_data.get('couleur_commentaire', instance.couleur_commentaire)
        instance.commentaire = validated_data.get('commentaire', instance.commentaire)
        
        # Mettre à jour updated_by si request est dans le contexte
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            instance.updated_by = request.user
        
        instance.save()
        return instance
    
    def validate(self, data):
        """Validation pour l'édition"""
        # Vérifier qu'au moins un champ est rempli après modification
        produits = data.get('produits')
        services = data.get('services')
        
        current_produits = self.instance.produits if self.instance else ''
        current_services = self.instance.services if self.instance else ''
        
        # Si produits n'est pas dans les données, utiliser la valeur actuelle
        if produits is None:
            produits = current_produits
        
        # Si services n'est pas dans les données, utiliser la valeur actuelle
        if services is None:
            services = current_services
        
        # Vérifier qu'au moins un champ a du contenu
        if not produits.strip() and not services.strip():
            raise serializers.ValidationError({
                'non_field_errors': 'Veuillez renseigner au moins un produit ou un service.'
            })
        
        return data

class ProduitServiceSearchSerializer(serializers.ModelSerializer):
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    acheteur_code = serializers.CharField(source='acheteur.code', read_only=True)
    
    class Meta:
        model = ProduitService
        fields = ['id', 'produits', 'services', 'couleur_commentaire', 'commentaire', 'acheteur_nom', 'acheteur_code', 'created_at', 'updated_at']







# serializers.py
from rest_framework import serializers
from .models import Cotisation

class ListCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = ["id", "acheteur", "numero", "date_affiliation", "couleur_commentaire", "commentaire", "created_at", "updated_at"]

class AddCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = ["acheteur", "numero", "date_affiliation", "couleur_commentaire", "commentaire"]

class DetailCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = ["id", "acheteur", "numero", "date_affiliation", "couleur_commentaire", "commentaire", "created_at", "updated_at"]

class EditCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = ["id", "acheteur", "numero", "date_affiliation", "couleur_commentaire", "commentaire", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}

class SearchCotisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotisation
        fields = ["id", "acheteur", "numero", "date_affiliation", "couleur_commentaire", "commentaire", "created_at", "updated_at"]







# serializers.py
from rest_framework import serializers
from .models import Swot

class ListSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = ["id", "acheteur", "forces", "faiblesses", "opportunites", "menaces", "couleur_commentaire", "commentaire", "created_at", "updated_at"]

class AddSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = ["acheteur", "forces", "faiblesses", "opportunites", "menaces", "couleur_commentaire", "commentaire"]

class DetailSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = ["id", "acheteur", "forces", "faiblesses", "opportunites", "menaces", "couleur_commentaire", "commentaire", "created_at", "updated_at"]

class EditSwotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swot
        fields = ["id", "acheteur", "forces", "faiblesses", "opportunites", "menaces", "couleur_commentaire", "commentaire", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}





# serializers.py
from rest_framework import serializers
from .models import RegistreCommerce

class ListRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = ["id", "acheteur", "numero", "date_inscription", "est_actif", "statut_registre", "commentaire", "created_at", "updated_at"]

class AddRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = ["acheteur", "numero", "date_inscription", "est_actif", "statut_registre", "commentaire"]

class DetailRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = ["id", "acheteur", "numero", "date_inscription", "est_actif", "statut_registre", "commentaire", "created_at", "updated_at"]

class EditRegistreCommerceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistreCommerce
        fields = ["id", "acheteur", "numero", "date_inscription", "est_actif", "statut_registre", "commentaire", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}









# serializers.py
from rest_framework import serializers
from .models import ProcedureCollective

class ListProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = ["id", "acheteur", "type_procedure", "date_ouverture", "date_cloture", "description", "couleur_commentaire", "commentaire", "created_at", "updated_at"]

class AddProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = ["acheteur", "type_procedure", "date_ouverture", "date_cloture", "description", "couleur_commentaire", "commentaire"]

class DetailProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = ["id", "acheteur", "type_procedure", "date_ouverture", "date_cloture", "description", "couleur_commentaire", "commentaire", "created_at", "updated_at"]

class EditProcedureCollectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureCollective
        fields = ["id", "acheteur", "type_procedure", "date_ouverture", "date_cloture", "description", "couleur_commentaire", "commentaire", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}










# serializers.py
from rest_framework import serializers
from .models import Document

class ListDocumentSerializer(serializers.ModelSerializer):
    fichier_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "acheteur", "titre", "fichier", "fichier_url", "description", "created_at", "updated_at"]

    def get_fichier_url(self, obj):
        if obj.fichier:
            return obj.fichier.url
        return None

class AddDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["acheteur", "titre", "fichier", "description"]

class DetailDocumentSerializer(serializers.ModelSerializer):
    fichier_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "acheteur", "titre", "fichier", "fichier_url", "description", "created_at", "updated_at"]

    def get_fichier_url(self, obj):
        if obj.fichier:
            return obj.fichier.url
        return None

class EditDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "acheteur", "titre", "fichier", "description", "created_at", "updated_at"]
        extra_kwargs = {"id": {"read_only": True}, "created_at": {"read_only": True}}
        
        
###########################################################################    
#    
# DOCUMENT ACHETEUR 
#    
########################################################################### 
class UserSimpleOneSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
  

class DocumentOneSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    created_by = UserSimpleOneSerializer(read_only=True)
    updated_by = UserSimpleOneSerializer(read_only=True)
    acheteur_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 
            'acheteur', 
            'acheteur_info',
            'titre', 
            'description',
            'fichier',
            'file_url',
            'file_name',
            'file_extension',
            'file_size',
            'created_at', 
            'updated_at',
            'created_by', 
            'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'acheteur_info']
    
    def get_file_url(self, obj):
        if obj.fichier and hasattr(obj.fichier, 'url'):
            return obj.fichier.url
        return None
    
    def get_file_name(self, obj):
        if obj.fichier and hasattr(obj.fichier, 'name'):
            return obj.fichier.name.split('/')[-1] if '/' in obj.fichier.name else obj.fichier.name
        return None
    
    def get_file_extension(self, obj):
        if obj.fichier and hasattr(obj.fichier, 'name'):
            try:
                return obj.fichier.name.split('.')[-1].lower()
            except:
                return 'unknown'
        return None
    
    def get_file_size(self, obj):
        if obj.fichier and hasattr(obj.fichier, 'size'):
            return obj.fichier.size
        return None
    
    def get_acheteur_info(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'code': obj.acheteur.code,
                'sigle': obj.acheteur.sigle
            }
        return None

class DocumentDetailOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'acheteur', 'titre', 'description', 'fichier']

class AddDocumentOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    
    class Meta:
        model = Document
        fields = ['titre', 'description', 'fichier', 'acheteur']
    
    def validate_fichier(self, value):
        # Validation de la taille du fichier (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(f"La taille du fichier ne doit pas dépasser {max_size/(1024*1024)}MB.")
        
        # Validation de l'extension
        allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(f"Type de fichier non supporté. Types acceptés: {', '.join(allowed_extensions)}")
        
        return value
    
    def validate(self, data):
        """Validation globale du document"""
        acheteur = data.get('acheteur')
        titre = data.get('titre')
        
        # Vérifier si un document avec le même titre existe déjà pour cet acheteur
        existing = Document.objects.filter(
            acheteur=acheteur,
            titre=titre
        ).exists()
        
        if existing and self.instance is None:
            raise serializers.ValidationError({
                'titre': 'Un document avec ce titre existe déjà pour cet acheteur.'
            })
        
        return data

class EditDocumentOneSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Document
        fields = ['titre', 'description']
    
    def validate(self, data):
        """Validation pour l'édition"""
        titre = data.get('titre')
        acheteur = self.instance.acheteur
        
        # Vérifier si un autre document avec le même titre existe déjà
        existing = Document.objects.filter(
            acheteur=acheteur,
            titre=titre
        ).exclude(id=self.instance.id).exists()
        
        if existing:
            raise serializers.ValidationError({
                'titre': 'Un autre document avec ce titre existe déjà pour cet acheteur.'
            })
        
        return data
       
class DocumentSearchSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = ['id', 'titre', 'description', 'file_url', 'file_name', 'file_extension', 'file_size', 'created_at', 'updated_at']
    
    def get_file_url(self, obj):
        return obj.fichier.url if obj.fichier else None
    
    def get_file_name(self, obj):
        return obj.fichier.name.split('/')[-1] if obj.fichier else None
    
    def get_file_extension(self, obj):
        if obj.fichier:
            try:
                return obj.fichier.name.split('.')[-1].lower()
            except:
                return 'unknown'
        return None
    
    def get_file_size(self, obj):
        return obj.fichier.size if obj.fichier else None
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        









class ListAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = ["id", "adresse", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class AddAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = ["adresse", "rue", "numero_porte", "bp", "nom", "acheteur"]

class DetailAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = ["id", "adresse", "rue", "numero_porte", "bp", "nom", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class EditAdresseAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdresseAcheteur
        fields = ["id", "adresse", "rue", "numero_porte", "bp", "nom", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "created_by": {"read_only": True},
            "acheteur": {"read_only": True}
        }












class ListPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = ["id", "portable", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class AddPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = ["portable", "nom", "acheteur"]

class DetailPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = ["id", "portable", "nom", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class EditPortableAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortableAcheteur
        fields = ["id", "portable", "nom", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "created_by": {"read_only": True},
            "acheteur": {"read_only": True}
        }










class ListTelephoneAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephoneAcheteur
        fields = ["id", "telephone", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class AddTelephoneAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephoneAcheteur
        fields = ["telephone", "nom", "acheteur"]

class DetailTelephoneAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephoneAcheteur
        fields = ["id", "telephone", "nom", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class EditTelephoneAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelephoneAcheteur
        fields = ["id", "telephone", "nom", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "created_by": {"read_only": True},
            "acheteur": {"read_only": True}
        }










class ListEmailAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAcheteur
        fields = ["id", "email", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class AddEmailAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAcheteur
        fields = ["email", "description", "acheteur"]

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Veuillez entrer une adresse email valide.")
        return value

class DetailEmailAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAcheteur
        fields = ["id", "email", "description", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]

class EditEmailAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAcheteur
        fields = ["id", "email", "description", "acheteur", "created_at", "updated_at", "created_by", "updated_by"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "created_by": {"read_only": True},
            "acheteur": {"read_only": True}
        }

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Veuillez entrer une adresse email valide.")
        return value









class CategoryNaceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNaceCode
        fields = ["id", "code", "libelle", "poids", "active"]

class SubCategoryNaceCodeSerializer(serializers.ModelSerializer):
    category = CategoryNaceCodeSerializer(read_only=True)

    class Meta:
        model = SubCategoryNaceCode
        fields = ["id", "code", "libelle", "poids", "active", "category"]



class ListCodeNaceAcheteurSerializer(serializers.ModelSerializer):
    code = SubCategoryNaceCodeSerializer(read_only=True)

    class Meta:
        model = CodeNaceAcheteur
        fields = ["id", "acheteur", "code", "created_at", "updated_at"]

class AddCodeNaceAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeNaceAcheteur
        fields = ["acheteur", "code"]

class DetailCodeNaceAcheteurSerializer(serializers.ModelSerializer):
    code = SubCategoryNaceCodeSerializer(read_only=True)

    class Meta:
        model = CodeNaceAcheteur
        fields = ["id", "acheteur", "code", "created_at", "updated_at"]

class EditCodeNaceAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeNaceAcheteur
        fields = ["id", "acheteur", "code", "created_at", "updated_at"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "acheteur": {"read_only": True}
        }
        
        
from rest_framework import serializers
from django.core.validators import ValidationError as DjangoValidationError
from django.core.validators import validate_email
import re
from main.models import CodeNaceAcheteur, SubCategoryNaceCode, CategoryNaceCode, Acheteur, User
from django.utils.translation import gettext_lazy as _


class UserSimpleSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class CategoryNaceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNaceCode
        fields = ["id", "code", "libelle", "active", "poids", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class SubCategoryNaceCodeSerializer(serializers.ModelSerializer):
    category = CategoryNaceCodeSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=CategoryNaceCode.objects.all(),
        source="category",
        write_only=True,
        required=False
    )
    
    class Meta:
        model = SubCategoryNaceCode
        fields = [
            "id", "code", "libelle", "active", "poids", 
            "category", "category_id", "created_at", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]


class CodeNaceAcheteurSerializer(serializers.ModelSerializer):
    code_details = SubCategoryNaceCodeSerializer(source='code', read_only=True)
    acheteur_details = serializers.SerializerMethodField()
    created_by = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = CodeNaceAcheteur
        fields = [
            "id", 
            "acheteur", 
            "acheteur_details",
            "code", 
            "code_details",
            "created_at", 
            "updated_at",
            "created_by"
        ]
        read_only_fields = ["created_at", "updated_at", "created_by"]
    
    def get_acheteur_details(self, obj):
        if obj.acheteur:
            return {
                "id": obj.acheteur.id,
                "nom": obj.acheteur.nom,
                "code": obj.acheteur.code,
                "sigle": obj.acheteur.sigle
            }
        return None


class GetCodeNaceAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeNaceAcheteur
        fields = "__all__"


class AddCodeNaceAcheteurSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    code = serializers.PrimaryKeyRelatedField(
        queryset=SubCategoryNaceCode.objects.filter(active=True)
    )
    
    class Meta:
        model = CodeNaceAcheteur
        fields = ["acheteur", "code"]
    
    def validate(self, data):
        """Validation de l'association code NACE - acheteur"""
        acheteur = data.get('acheteur')
        code = data.get('code')
        
        # Vérifier si cette association existe déjà
        if CodeNaceAcheteur.objects.filter(acheteur=acheteur, code=code).exists():
            raise serializers.ValidationError(
                _("Cet acheteur possède déjà ce code NACE.")
            )
        
        # Vérifier que le code NACE est actif
        if not code.active:
            raise serializers.ValidationError(
                _("Ce code NACE n'est pas actif.")
            )
        
        return data


class EditCodeNaceAcheteurSerializer(serializers.ModelSerializer):
    code = serializers.PrimaryKeyRelatedField(
        queryset=SubCategoryNaceCode.objects.filter(active=True),
        required=False
    )
    
    class Meta:
        model = CodeNaceAcheteur
        fields = ["code"]
    
    def validate(self, data):
        """Validation pour l'édition"""
        instance = self.instance
        new_code = data.get('code')
        
        if new_code and new_code != instance.code:
            # Vérifier si cette association existe déjà pour cet acheteur
            if CodeNaceAcheteur.objects.filter(
                acheteur=instance.acheteur, 
                code=new_code
            ).exclude(id=instance.id).exists():
                raise serializers.ValidationError(
                    _("Cet acheteur possède déjà ce code NACE.")
                )
            
            # Vérifier que le code NACE est actif
            if not new_code.active:
                raise serializers.ValidationError(
                    _("Ce code NACE n'est pas actif.")
                )
        
        return data


# Serializers pour la recherche de codes NACE
class SearchSubCategoryNaceCodeSerializer(serializers.ModelSerializer):
    category_details = CategoryNaceCodeSerializer(source='category', read_only=True)
    
    class Meta:
        model = SubCategoryNaceCode
        fields = ["id", "code", "libelle", "category", "category_details", "active", "poids"]


class CodeNaceAcheteurWithDetailsSerializer(serializers.ModelSerializer):
    code_details = SubCategoryNaceCodeSerializer(source='code', read_only=True)
    category_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeNaceAcheteur
        fields = [
            "id", "acheteur", "code", "code_details", 
            "category_details", "created_at"
        ]
    
    def get_category_details(self, obj):
        if obj.code and obj.code.category:
            return {
                "id": obj.code.category.id,
                "code": obj.code.category.code,
                "libelle": obj.code.category.libelle
            }
        return None
    
    
    
###########################################################################    
#    
# CODE NACE ACHETEUR 
#    
###########################################################################   
    
class CategoryNaceCodeOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNaceCode
        fields = ['id', 'code', 'libelle', 'active', 'poids']

class SubCategoryNaceCodeOneSerializer(serializers.ModelSerializer):
    category = CategoryNaceCodeOneSerializer(read_only=True)
    
    class Meta:
        model = SubCategoryNaceCode
        fields = ['id', 'category', 'code', 'libelle', 'active', 'poids']
        read_only_fields = ['category']

class SubCategoryNaceCodeSimpleOneSerializer(serializers.ModelSerializer):
    category_info = serializers.SerializerMethodField()
    
    class Meta:
        model = SubCategoryNaceCode
        fields = ['id', 'code', 'libelle', 'category_info', 'active', 'poids']
        read_only_fields = ['category_info']
    
    def get_category_info(self, obj):
        if obj.category:
            return {
                'id': obj.category.id,
                'code': obj.category.code,
                'libelle': obj.category.libelle
            }
        return None
    
    def to_representation(self, instance):
        """S'assurer que toutes les valeurs sont présentes"""
        data = super().to_representation(instance)
        
        # S'assurer que les valeurs par défaut sont présentes
        data['code'] = data.get('code', '')
        data['libelle'] = data.get('libelle', '')
        data['active'] = data.get('active', False)
        data['poids'] = data.get('poids', 0.0)
        
        return data
    
class UserSimpleOneSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name()

class CodeNaceAcheteurOneSerializer(serializers.ModelSerializer):
    subcategory_details = SubCategoryNaceCodeOneSerializer(source='code', read_only=True)
    created_by = UserSimpleOneSerializer(read_only=True)
    updated_by = UserSimpleOneSerializer(read_only=True)
    acheteur_info = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeNaceAcheteur
        fields = [
            'id', 
            'acheteur', 
            'acheteur_info',
            'code', 
            'subcategory_details',
            'created_at', 
            'updated_at',
            'created_by', 
            'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'acheteur_info']
    
    def get_acheteur_info(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'code': obj.acheteur.code,
                'sigle': obj.acheteur.sigle
            }
        return None

class CodeNaceAcheteurDetailOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeNaceAcheteur
        fields = ['id', 'acheteur', 'code']

class AddCodeNaceAcheteurOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    code = serializers.PrimaryKeyRelatedField(
        queryset=SubCategoryNaceCode.objects.filter(active=True)
    )
    
    class Meta:
        model = CodeNaceAcheteur
        fields = ['code', 'acheteur']
    
    def validate(self, data):
        """Validation globale de l'association code NACE - acheteur"""
        acheteur = data.get('acheteur')
        code = data.get('code')
        
        # Vérifier si cette association existe déjà
        existing = CodeNaceAcheteur.objects.filter(
            acheteur=acheteur,
            code=code
        ).exists()
        
        if existing and self.instance is None:
            raise serializers.ValidationError({
                'code': 'Ce code NACE est déjà associé à cet acheteur.'
            })
        
        return data

class EditCodeNaceAcheteurOneSerializer(serializers.ModelSerializer):
    code = serializers.PrimaryKeyRelatedField(
        queryset=SubCategoryNaceCode.objects.filter(active=True)
    )
    
    class Meta:
        model = CodeNaceAcheteur
        fields = ['code']
    
    def validate(self, data):
        """Validation pour l'édition"""
        code = data.get('code')
        acheteur = self.instance.acheteur
        
        # Vérifier si cette association existe déjà (pour un autre enregistrement)
        existing = CodeNaceAcheteur.objects.filter(
            acheteur=acheteur,
            code=code
        ).exclude(id=self.instance.id).exists()
        
        if existing:
            raise serializers.ValidationError({
                'code': 'Ce code NACE est déjà associé à cet acheteur.'
            })
        
        return data
       
class CodeNaceAcheteurSearchSerializer(serializers.ModelSerializer):
    code = serializers.SerializerMethodField()
    libelle = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    poids = serializers.SerializerMethodField()
    active = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeNaceAcheteur
        fields = ['id', 'code', 'libelle', 'category', 'poids', 'active', 'created_at', 'updated_at']
    
    def get_code(self, obj):
        return obj.code.code if obj.code else None
    
    def get_libelle(self, obj):
        return obj.code.libelle if obj.code else None
    
    def get_category(self, obj):
        if obj.code and obj.code.category:
            return {
                'code': obj.code.category.code,
                'libelle': obj.code.category.libelle
            }
        return None
    
    def get_poids(self, obj):
        return obj.code.poids if obj.code else None
    
    def get_active(self, obj):
        return obj.code.active if obj.code else False






















class CategoryNafCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNafCode
        fields = ["id", "code", "libelle", "active"]

class SubCategoryNafCodeSerializer(serializers.ModelSerializer):
    category = CategoryNafCodeSerializer(read_only=True)

    class Meta:
        model = SubCategoryNafCode
        fields = ["id", "code", "libelle", "active", "category"]

class ListCodeNafAcheteurSerializer(serializers.ModelSerializer):
    code = SubCategoryNafCodeSerializer(read_only=True)

    class Meta:
        model = CodeNafAcheteur
        fields = ["id", "acheteur", "code", "created_at", "updated_at"]

class AddCodeNafAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeNafAcheteur
        fields = ["acheteur", "code"]

class DetailCodeNafAcheteurSerializer(serializers.ModelSerializer):
    code = SubCategoryNafCodeSerializer(read_only=True)

    class Meta:
        model = CodeNafAcheteur
        fields = ["id", "acheteur", "code", "created_at", "updated_at"]

class EditCodeNafAcheteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeNafAcheteur
        fields = ["id", "acheteur", "code", "created_at", "updated_at"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "acheteur": {"read_only": True}
        }
        
###########################################################################    
#    
# CODE NAF ACHETEUR 
#    
###########################################################################   
    
class CategoryNafCodeOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNafCode  # À adapter selon votre modèle
        fields = ['id', 'code', 'libelle', 'active', 'poids']

class SubCategoryNafCodeOneSerializer(serializers.ModelSerializer):
    category = CategoryNafCodeOneSerializer(read_only=True)
    
    class Meta:
        model = SubCategoryNafCode  # À adapter selon votre modèle
        fields = ['id', 'category', 'code', 'libelle', 'active', 'poids']
        read_only_fields = ['category']

class SubCategoryNafCodeSimpleOneSerializer(serializers.ModelSerializer):
    category_info = serializers.SerializerMethodField()

    class Meta:
        model = SubCategoryNafCode
        fields = ['id', 'code', 'libelle', 'libelle_en', 'category_info', 'active', 'poids']
        read_only_fields = ['category_info']

    def get_category_info(self, obj):
        if obj.category:
            return {
                'id': obj.category.id,
                'code': obj.category.code,
                'libelle': obj.category.libelle,
                'libelle_en': obj.category.libelle_en or '',
            }
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['code'] = data.get('code', '')
        data['libelle'] = data.get('libelle', '')
        data['libelle_en'] = data.get('libelle_en') or ''
        data['active'] = data.get('active', False)
        data['poids'] = data.get('poids', 0.0)
        return data
    
class CodeNafAcheteurOneSerializer(serializers.ModelSerializer):
    subcategory_details = SubCategoryNafCodeOneSerializer(source='code', read_only=True)
    created_by = UserSimpleOneSerializer(read_only=True)
    updated_by = UserSimpleOneSerializer(read_only=True)
    acheteur_info = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeNafAcheteur
        fields = [
            'id', 
            'acheteur', 
            'acheteur_info',
            'code', 
            'subcategory_details',
            'created_at', 
            'updated_at',
            'created_by', 
            'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'acheteur_info']
    
    def get_acheteur_info(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'code': obj.acheteur.code,
                'sigle': obj.acheteur.sigle
            }
        return None

class CodeNafAcheteurDetailOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeNafAcheteur
        fields = ['id', 'acheteur', 'code']

class AddCodeNafAcheteurOneSerializer(serializers.ModelSerializer):
    acheteur = serializers.PrimaryKeyRelatedField(
        queryset=Acheteur.objects.all()
    )
    code = serializers.PrimaryKeyRelatedField(
        queryset=SubCategoryNafCode.objects.filter(active=True)
    )
    
    class Meta:
        model = CodeNafAcheteur
        fields = ['code', 'acheteur']
    
    def validate(self, data):
        """Validation globale de l'association code NAF - acheteur"""
        acheteur = data.get('acheteur')
        code = data.get('code')
        
        # Vérifier si cette association existe déjà
        existing = CodeNafAcheteur.objects.filter(
            acheteur=acheteur,
            code=code
        ).exists()
        
        if existing and self.instance is None:
            raise serializers.ValidationError({
                'code': 'Ce code NAF est déjà associé à cet acheteur.'
            })
        
        return data

class EditCodeNafAcheteurOneSerializer(serializers.ModelSerializer):
    code = serializers.PrimaryKeyRelatedField(
        queryset=SubCategoryNafCode.objects.filter(active=True)
    )
    
    class Meta:
        model = CodeNafAcheteur
        fields = ['code']
    
    def validate(self, data):
        """Validation pour l'édition"""
        code = data.get('code')
        acheteur = self.instance.acheteur
        
        # Vérifier si cette association existe déjà (pour un autre enregistrement)
        existing = CodeNafAcheteur.objects.filter(
            acheteur=acheteur,
            code=code
        ).exclude(id=self.instance.id).exists()
        
        if existing:
            raise serializers.ValidationError({
                'code': 'Ce code NAF est déjà associé à cet acheteur.'
            })
        
        return data
       
class CodeNafAcheteurSearchSerializer(serializers.ModelSerializer):
    code = serializers.SerializerMethodField()
    libelle = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    poids = serializers.SerializerMethodField()
    active = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeNafAcheteur
        fields = ['id', 'code', 'libelle', 'category', 'poids', 'active', 'created_at', 'updated_at']
    
    def get_code(self, obj):
        return obj.code.code if obj.code else None
    
    def get_libelle(self, obj):
        return obj.code.libelle if obj.code else None
    
    def get_category(self, obj):
        if obj.code and obj.code.category:
            return {
                'code': obj.code.category.code,
                'libelle': obj.code.category.libelle
            }
        return None
    
    def get_poids(self, obj):
        return obj.code.poids if obj.code else None
    
    def get_active(self, obj):
        return obj.code.active if obj.code else False



























class CommandeSerializer(serializers.ModelSerializer):
    client_username = serializers.CharField(source='client.username', read_only=True)
    pays_nom = serializers.CharField(source='pays.nom', read_only=True)
    validateur_username = serializers.CharField(source='validateur.username', read_only=True)
    acheteur_id = serializers.IntegerField(source='acheteur.id', read_only=True, allow_null=True)
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True, allow_null=True)

    class Meta:
        model = Commande
        fields = [
            'id', 'notre_ref', 'reference_client', 'type_rapport', 'raison_sociale',
            'date_recept_commande', 'date_rapport', 'priorite', 'status',
            'client', 'client_username', 'pays', 'pays_nom', 'validateur',
            'validateur_username', 'date_envoi_client', 'email_envoye',
            'acheteur_id', 'acheteur_nom',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['validateur', 'date_envoi_client', 'email_envoye']

class AffectationAnalysteSerializer(serializers.ModelSerializer):
    analyste = UserSerializer(read_only=True)
    
    class Meta:
        model = AffectationAnalyste
        fields = ['id', 'commande', 'analyste', 'date_affectation']

class ValidationRapportSerializer(serializers.ModelSerializer):
    validateur = UserSerializer(read_only=True)

    class Meta:
        model = ValidationRapport
        fields = ['id', 'rapport', 'validateur', 'status', 'commentaire', 'date_validation']

class RapportSerializer(serializers.ModelSerializer):
    analyste = UserSerializer(read_only=True)
    validation = ValidationRapportSerializer(source='validationrapport', read_only=True)
    
    class Meta:
        model = Rapport
        fields = ['id', 'commande', 'analyste', 'fichier', 'date_soumission', 'validation']

class SuiviCommandeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = SuiviCommande
        fields = ['id', 'commande', 'user', 'action', 'type', 'commentaire', 'date_action']

class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'user', 'type', 'message', 'is_read', 'created_at']
        
        
        
        
        
        
        
        
        
        
        
        
# --- Sérialiseurs pour le modèle ActifC ---
class ActifClassiqueSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Inclusion des propriétés de calcul en lecture seule
    elements_incorporels = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    elements_corporels = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    elements_financiers = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_I = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    stocks = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    creances = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    disponibilites_vmp = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_II = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    compte_regul = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_III = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    general_total = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ActifC
        fields = '__all__'


class AddActifClassiqueSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ActifC
        fields = [
            'annee', 'acheteur', 'capital_souscrit_non_app', 'frais_recherche_developpement',
            'brevet_licence_logiciels', 'fonds_commercial', 'autres_immobilisations_incorporelles',
            'terrains', 'constructions', 'materiels_et_outils', 'materiel_de_transport',
            'autres_immos_corp', 'immos_en_cours', 'avances_et_acptes',
            'participations', 'prets', 'autres', 'stocks_mp', 'stocks_encours_mp',
            'stocks_pf', 'stocks_encours_pf', 'stocks_encours_services', 'stocks_mses',
            'avances_acptes_verses', 'clients_et_cptes_rattaches', 'autres_creances',
            'valeurs_a_encaisser', 'banques_cheques_postaux_caisse', 'cca',
            'charges_a_repartir_et_frais_etablissement', 'primes_de_rbt', 'eca', 'eene',
            'amortissements', 'provisions_stocks', 'provisions_creances', 'provisions_vmp',
            'effectif' # J'ajoute l'effectif car il semble être une donnée d'entrée
        ]


class EditActifClassiqueSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ActifC
        fields = [
            'annee', 'acheteur', 'capital_souscrit_non_app', 'frais_recherche_developpement',
            'brevet_licence_logiciels', 'fonds_commercial', 'autres_immobilisations_incorporelles',
            'terrains', 'constructions', 'materiels_et_outils', 'materiel_de_transport',
            'autres_immos_corp', 'immos_en_cours', 'avances_et_acptes',
            'participations', 'prets', 'autres', 'stocks_mp', 'stocks_encours_mp',
            'stocks_pf', 'stocks_encours_pf', 'stocks_encours_services', 'stocks_mses',
            'avances_acptes_verses', 'clients_et_cptes_rattaches', 'autres_creances',
            'valeurs_a_encaisser', 'banques_cheques_postaux_caisse', 'cca',
            'charges_a_repartir_et_frais_etablissement', 'primes_de_rbt', 'eca', 'eene',
            'amortissements', 'provisions_stocks', 'provisions_creances', 'provisions_vmp',
            'effectif'
        ]

# --- Sérialiseurs pour le modèle PassifC ---
class PassifClassiqueSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Inclusion des propriétés de calcul
    total_I = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_II = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_III = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_IV = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_V = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_general = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = PassifC
        fields = '__all__'


class AddPassifClassiqueSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = PassifC
        fields = [
            'annee', 'acheteur', 'capital_social', 'primes', 'ecarts_de_reevaluation',
            'reserve', 'report_a_nouveau', 'resultat_exercice', 'subv_invest',
            'provision_regl', 'emprunts', 'dette_credit_bail_contrat_assimile',
            'dettes_financiere_diverses', 'provision_financiere_risque_charge',
            'dettes_fournisseurs_divers', 'avance_et_acomptes_recu', 'dettes',
            'dettes_fiscales_sociales', 'autres_dettes', 'banques_credit_escompte',
            'banque_credit_caisse', 'banques_decouvert', 'ecart_conversion_passif',
        ]


class EditPassifClassiqueSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = PassifC
        fields = [
            'annee', 'acheteur', 'capital_social', 'primes', 'ecarts_de_reevaluation',
            'reserve', 'report_a_nouveau', 'resultat_exercice', 'subv_invest',
            'provision_regl', 'emprunts', 'dette_credit_bail_contrat_assimile',
            'dettes_financiere_diverses', 'provision_financiere_risque_charge',
            'dettes_fournisseurs_divers', 'avance_et_acomptes_recu', 'dettes',
            'dettes_fiscales_sociales', 'autres_dettes', 'banques_credit_escompte',
            'banque_credit_caisse', 'banques_decouvert', 'ecart_conversion_passif',
        ]

# --- Sérialiseurs pour le modèle ResultatC ---
class ResultatClassiqueSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Inclusion des propriétés de calcul
    ca = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_I = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    marge_brute = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    valeur_ajoutee = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    excedent_brut_ex = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_exploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    financier_total_I = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    financier_total_II = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_financier = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_courant_avant_impots = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    excep_total_I = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    excep_total_II = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_excep = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_exercice = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ResultatC
        fields = '__all__'


class AddResultatClassiqueSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ResultatC
        fields = [
            'annee', 'acheteur', 'vente_de_mdses', 'ventes_de_produits_fabriques',
            'travaux_services_vendus', 'produit_accessoires', 'production_imblise',
            'subventions_exploitations', 'production_stockee', 'reprises_de_provision',
            'transferts_charges', 'autres_produits', 'achat_mdses', 'variation_stock_mdses',
            'achat_mp_autres_appro', 'var_stk_mp_app', 'autres_achats',
            'variation_de_stocks_autres_appro', 'transports', 'services_ext',
            'impots_taxes', 'autres_charges_valeur_ajoutee', 'charges_personnel',
            'dotation_aux_amorts', 'dotation_aux_provisions',
            'autres_charges_excedent_brute', 'revenus_fin_assimiles',
            'prof_vmp_et_cre_actif_immo', 'interets_produit_assim',
            'reprise_prov_et_transfert', 'diff_positive_de_change',
            'prod_nets_cessions_vmp', 'dap', 'frais_fin_charges_assi',
            'diff_negatives_de_change', 'ch_nettes_cessions_vmp',
            'sur_op_gestion_prod_except', 'sur_op_en_capital_prod_except',
            'reprise_prov_transfert', 'sur_op_gestion_charg_except',
            'sur_op_en_capital_charg_except', 'dap_et_transfert_charg_except',
            'participation_salairies', 'impot_sur_benefices',
        ]


class EditResultatClassiqueSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ResultatC
        fields = [
            'annee', 'acheteur', 'vente_de_mdses', 'ventes_de_produits_fabriques',
            'travaux_services_vendus', 'produit_accessoires', 'production_imblise',
            'subventions_exploitations', 'production_stockee', 'reprises_de_provision',
            'transferts_charges', 'autres_produits', 'achat_mdses', 'variation_stock_mdses',
            'achat_mp_autres_appro', 'var_stk_mp_app', 'autres_achats',
            'variation_de_stocks_autres_appro', 'transports', 'services_ext',
            'impots_taxes', 'autres_charges_valeur_ajoutee', 'charges_personnel',
            'dotation_aux_amorts', 'dotation_aux_provisions',
            'autres_charges_excedent_brute', 'revenus_fin_assimiles',
            'prof_vmp_et_cre_actif_immo', 'interets_produit_assim',
            'reprise_prov_et_transfert', 'diff_positive_de_change',
            'prod_nets_cessions_vmp', 'dap', 'frais_fin_charges_assi',
            'diff_negatives_de_change', 'ch_nettes_cessions_vmp',
            'sur_op_gestion_prod_except', 'sur_op_en_capital_prod_except',
            'reprise_prov_transfert', 'sur_op_gestion_charg_except',
            'sur_op_en_capital_charg_except', 'dap_et_transfert_charg_except',
            'participation_salairies', 'impot_sur_benefices',
        ]
        
        
        
        
        
        
        
        
        
        
        
        


# --- Sérialiseurs pour le modèle ActifS ---
class ActifSysOhadaSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Inclusion des propriétés de calcul en lecture seule
    immobilisations_incorporelles = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    immobilisations_corporelles = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    immobilisations_financieres = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actif_immobilise = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    creances_emplois_similaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_tresorerie_equivalents = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actif_circulant = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actif = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ActifS
        fields = '__all__'


class AddActifSysOhadaSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ActifS
        fields = [
            'annee', 'acheteur', 'frais_developpement_prospection', 'brevets_licences_logiciels',
            'droits_propriete_commerciale_baux', 'autres_immo_incorporelles', 'terrains',
            'dons_investissements_net', 'batiments', 'agencements_amenagements_installations',
            'materiel_mobilier_actif_biologiques', 'materiel_transport',
            'avances_acompte_immobilisations', 'titres_participation',
            'autres_immobilisations_financieres', 'actif_circulant_hao', 'stock_encours',
            'fournisseurs_avances_versee', 'clients', 'autres_creances',
            'valeurs_mobilieres_placement', 'disponibilites',
            'banque_cheque_postal_caisse_assimiles', 'ecart_conversion_actif'
        ]


class EditActifSysOhadaSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ActifS
        fields = [
            'annee', 'acheteur', 'frais_developpement_prospection', 'brevets_licences_logiciels',
            'droits_propriete_commerciale_baux', 'autres_immo_incorporelles', 'terrains',
            'dons_investissements_net', 'batiments', 'agencements_amenagements_installations',
            'materiel_mobilier_actif_biologiques', 'materiel_transport',
            'avances_acompte_immobilisations', 'titres_participation',
            'autres_immobilisations_financieres', 'actif_circulant_hao', 'stock_encours',
            'fournisseurs_avances_versee', 'clients', 'autres_creances',
            'valeurs_mobilieres_placement', 'disponibilites',
            'banque_cheque_postal_caisse_assimiles', 'ecart_conversion_actif'
        ]



# --- Sérialiseurs pour le modèle PassifS ---
class PassifSysOhadaSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Inclusion des propriétés de calcul
    total_capitaux_propres_ressources_similaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_dettes_financieres_ressources_similaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_ressources_stables = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_passifs_courants = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_tresorerie_equivalents = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_passifs = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = PassifS
        fields = '__all__'


class AddPassifSysOhadaSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = PassifS
        fields = [
            'annee', 'acheteur', 'capital', 'capital_non_appele_apporteurs',
            'primes_liees_capital_social', 'ecart_reevaluation', 'reserves_indisponibles',
            'reserves_libres', 'report_nouveau', 'resultat_net_exercice',
            'subventions_investissements', 'provisions_reglees',
            'emprunts_dettes_financieres_diverse', 'dettes_location_vente',
            'provisions_risques_charges', 'passif_circulant_hao',
            'clients_avances_recues', 'fournisseurs_exploitation',
            'dettes_fiscales_sociales', 'autres_dettes',
            'provisions_risques_court_terme', 'banques_credit_escompte',
            'banques_etablissements_financiers_credit_caisse',
            'ecart_conversion_passif'
        ]


class EditPassifSysOhadaSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = PassifS
        fields = [
            'annee', 'acheteur', 'capital', 'capital_non_appele_apporteurs',
            'primes_liees_capital_social', 'ecart_reevaluation', 'reserves_indisponibles',
            'reserves_libres', 'report_nouveau', 'resultat_net_exercice',
            'subventions_investissements', 'provisions_reglees',
            'emprunts_dettes_financieres_diverse', 'dettes_location_vente',
            'provisions_risques_charges', 'passif_circulant_hao',
            'clients_avances_recues', 'fournisseurs_exploitation',
            'dettes_fiscales_sociales', 'autres_dettes',
            'provisions_risques_court_terme', 'banques_credit_escompte',
            'banques_etablissements_financiers_credit_caisse',
            'ecart_conversion_passif'
        ]



# --- Sérialiseurs pour le modèle ResultatS ---
class ResultatSysOhadaSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    # Inclusion des propriétés de calcul
    marge_commerciale = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    chiffre_affaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    valeur_ajoutee = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    excedent_brute_exploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_exploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_financier = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_activites_ordinaires_xe = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_activites_ordinaires_tn = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_net = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ResultatS
        fields = '__all__'


class AddResultatSysOhadaSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ResultatS
        fields = [
            'annee', 'acheteur', 'ventes_marchandises_a', 'achats_marchandises',
            'variation_stock_marchandises', 'ventes_produits_manufactures',
            'travaux_services_vendus_c', 'produits_accessoires_d',
            'production_stockee', 'production_immobilisee', 'subvention_exploitation',
            'autres_produits', 'transfert_charges_exploitation',
            'achats_matieres_premieres_fournitures_connexes',
            'variation_stock_matieres_premieres_fournitures_connexes',
            'autres_achats', 'variation_stock_autres_fournitures',
            'transport', 'services_exterieurs', 'impots_taxes', 'autres_depenses',
            'frais_personnel',
            'reprise_depreciations_amortissements_provision_pertes_valeurs_p',
            'reprise_depreciations_amortissements_provision_pertes_valeurs_m',
            'produits_financiers_assimiles', 'reprise_provision_perte_valeur',
            'transfert_charges_financieres', 'charges_financieres_assimilees',
            'dotations_provisions_depreciations_financieres',
            'produits_cession_immobilisations', 'autres_produits_hao',
            'valeur_comptable_cessions_actifs_immobilises', 'autres_charges_hao',
            'participation_travailleurs', 'charge_impot_revenu',
        ]


class EditResultatSysOhadaSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ResultatS
        fields = [
            'annee', 'acheteur', 'ventes_marchandises_a', 'achats_marchandises',
            'variation_stock_marchandises', 'ventes_produits_manufactures',
            'travaux_services_vendus_c', 'produits_accessoires_d',
            'production_stockee', 'production_immobilisee', 'subvention_exploitation',
            'autres_produits', 'transfert_charges_exploitation',
            'achats_matieres_premieres_fournitures_connexes',
            'variation_stock_matieres_premieres_fournitures_connexes',
            'autres_achats', 'variation_stock_autres_fournitures',
            'transport', 'services_exterieurs', 'impots_taxes', 'autres_depenses',
            'frais_personnel',
            'reprise_depreciations_amortissements_provision_pertes_valeurs_p',
            'reprise_depreciations_amortissements_provision_pertes_valeurs_m',
            'produits_financiers_assimiles', 'reprise_provision_perte_valeur',
            'transfert_charges_financieres', 'charges_financieres_assimilees',
            'dotations_provisions_depreciations_financieres',
            'produits_cession_immobilisations', 'autres_produits_hao',
            'valeur_comptable_cessions_actifs_immobilises', 'autres_charges_hao',
            'participation_travailleurs', 'charge_impot_revenu',
        ]
        
        
        
        
        
        
        
        
        
        
        
        
        


# --- Sérialiseurs pour le modèle ActifA ---
class ActifAnglaisSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    total_actifs_non_courants = serializers.SerializerMethodField()
    total_actif_circulant = serializers.SerializerMethodField()
    total_actif = serializers.SerializerMethodField()

    def get_total_actifs_non_courants(self, obj):
        return obj.total_actifs_non_courants()

    def get_total_actif_circulant(self, obj):
        return obj.total_actif_circulant()

    def get_total_actif(self, obj):
        return obj.total_actif()

    class Meta:
        model = ActifA
        fields = '__all__'


class AddActifAnglaisSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ActifA
        fields = ACTIF_A_FIELDS


class EditActifAnglaisSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ActifA
        fields = ACTIF_A_FIELDS


# --- Sérialiseurs pour le modèle PassifA ---
class PassifAnglaisSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    total_fonds_propres = serializers.SerializerMethodField()
    total_passif_long_terme = serializers.SerializerMethodField()
    total_passif_circulant = serializers.SerializerMethodField()
    total_passif = serializers.SerializerMethodField()
    total_capitaux_propres_et_passif = serializers.SerializerMethodField()

    def get_total_fonds_propres(self, obj):
        return obj.total_fonds_propres()

    def get_total_passif_long_terme(self, obj):
        return obj.total_passif_long_terme()

    def get_total_passif_circulant(self, obj):
        return obj.total_passif_circulant()

    def get_total_passif(self, obj):
        return obj.total_passif()

    def get_total_capitaux_propres_et_passif(self, obj):
        return obj.total_capitaux_propres_et_passif()

    class Meta:
        model = PassifA
        fields = '__all__'


class AddPassifAnglaisSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = PassifA
        fields = PASSIF_A_FIELDS


class EditPassifAnglaisSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = PassifA
        fields = PASSIF_A_FIELDS


# --- Sérialiseurs pour le modèle ResultatA ---
class ResultatAnglaisSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)

    gross_profit = serializers.SerializerMethodField()
    total_income = serializers.SerializerMethodField()
    operating_profit = serializers.SerializerMethodField()
    profit_before_finance_cost_and_taxation = serializers.SerializerMethodField()
    profit_before_taxation = serializers.SerializerMethodField()
    profit_for_the_year = serializers.SerializerMethodField()
    retained_earnings = serializers.SerializerMethodField()

    def get_gross_profit(self, obj):
        return obj.gross_profit()

    def get_total_income(self, obj):
        return obj.total_income()

    def get_operating_profit(self, obj):
        return obj.operating_profit()

    def get_profit_before_finance_cost_and_taxation(self, obj):
        return obj.profit_before_finance_cost_and_taxation()

    def get_profit_before_taxation(self, obj):
        return obj.profit_before_taxation()

    def get_profit_for_the_year(self, obj):
        return obj.profit_for_the_year()

    def get_retained_earnings(self, obj):
        return obj.retained_earnings()

    class Meta:
        model = ResultatA
        fields = '__all__'


class AddResultatAnglaisSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ResultatA
        fields = RESULTAT_A_FIELDS


class EditResultatAnglaisSerializer(AnneeUniciteAnnuelleMixin, serializers.ModelSerializer):
    class Meta:
        model = ResultatA
        fields = RESULTAT_A_FIELDS
        
        
        
        
# main/serializers.py
from rest_framework import serializers
from .models import (
    ScoringSansBilanAcheteur,
    FormeJuridique,
    ModeleComportementPaiement,
    ModeleAgeSociete,
    ModeleAvisCommercial,
    ModeleBail,
    CategoryNaceCode,
)

# serializers.py
class ModeleComportementPaiementScoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleComportementPaiement
        fields = ["id", "code", "libelle", "poids"]

class FormeJuridiqueScoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormeJuridique
        fields = ["id", "code", "libelle", "poids"]

class ModeleAgeSocieteScoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAgeSociete
        fields = ["id", "code", "libelle", "poids"]

class ModeleAvisCommercialScoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleAvisCommercial
        fields = ["id", "code", "libelle", "poids"]

class ModeleBailScoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleBail
        fields = ["id", "code", "libelle", "poids"]

class CategoryNaceCodeScoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNaceCode
        fields = ["id", "code", "libelle", "poids"]
    
    
    
class ScoringSansBilanAcheteurSerializer(serializers.ModelSerializer):
    # Champs en lecture seule pour l'affichage
    categories_nace_ref = CategoryNaceCodeScoringSerializer(many=True, read_only=True)
    comportement_de_paiement_ref = ModeleComportementPaiementScoringSerializer(read_only=True)
    age_company_ref = ModeleAgeSocieteScoringSerializer(read_only=True)
    forme_juridique = FormeJuridiqueScoringSerializer(read_only=True)
    avis_commercial_ref = ModeleAvisCommercialScoringSerializer(read_only=True)
    locaux_ref = ModeleBailScoringSerializer(read_only=True)
    
    created_by = UserSimpleSerializer(read_only=True)
    updated_by = UserSimpleSerializer(read_only=True)
    
    # Champs en écriture pour la mise à jour
    comportement_de_paiement_ref_id = serializers.PrimaryKeyRelatedField(
        queryset=ModeleComportementPaiement.objects.all(), 
        source='comportement_de_paiement_ref', 
        write_only=True, 
        required=False,
        allow_null=True
    )
    age_company_ref_id = serializers.PrimaryKeyRelatedField(
        queryset=ModeleAgeSociete.objects.all(), 
        source='age_company_ref', 
        write_only=True, 
        required=False,
        allow_null=True
    )
    forme_juridique_id = serializers.PrimaryKeyRelatedField(
        queryset=FormeJuridique.objects.all(), 
        source='forme_juridique', 
        write_only=True, 
        required=False,
        allow_null=True
    )
    avis_commercial_ref_id = serializers.PrimaryKeyRelatedField(
        queryset=ModeleAvisCommercial.objects.all(), 
        source='avis_commercial_ref', 
        write_only=True, 
        required=False,
        allow_null=True
    )
    locaux_ref_id = serializers.PrimaryKeyRelatedField(
        queryset=ModeleBail.objects.all(), 
        source='locaux_ref', 
        write_only=True, 
        required=False,
        allow_null=True
    )
    categories_nace_ref_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = ScoringSansBilanAcheteur
        fields = [
            "id", "code", "acheteur", 
            "comportement_de_paiement_ref", "comportement_de_paiement_ref_id",
            "age_company_ref", "age_company_ref_id",
            "forme_juridique", "forme_juridique_id", 
            "avis_commercial_ref", "avis_commercial_ref_id",
            "locaux_ref", "locaux_ref_id",
            "categories_nace_ref", "categories_nace_ref_ids",
            "scoring_value", "interpretation", "commentaire", 
            "created_at", "updated_at", "created_by", "updated_by"
        ]
        read_only_fields = ["scoring_value", "interpretation", "created_at", "updated_at", "created_by", "updated_by"]
        
    def get_object(self):
        acheteur_id = self.kwargs.get("acheteur_id")
        return get_object_or_404(ScoringSansBilanAcheteur, acheteur_id=acheteur_id)

    def update(self, instance, validated_data):
        print("🔄 Mise à jour du scoring...")
        
        # Extraire les données pour les relations ManyToMany
        categories_nace_ids = validated_data.pop('categories_nace_ref_ids', None)
        
        # Mettre à jour les champs simples
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Sauvegarder d'abord pour avoir un ID
        instance.save()
        
        # Mettre à jour les catégories NACE
        if categories_nace_ids is not None:
            instance.categories_nace_ref.set(categories_nace_ids)
            print(f"📝 Catégories NACE mises à jour: {categories_nace_ids}")
        
        # Sauvegarder à nouveau pour recalculer le score
        instance.save()
        
        print(f"🎯 Score final: {instance.scoring_value}")
        return instance








from rest_framework import serializers
from django.db import models
from decimal import Decimal

class ScoreACREMACBilanSerializer(serializers.Serializer):
    acheteur_id = serializers.IntegerField(required=True)
    annee_n = serializers.IntegerField(required=True)
    annee_n1 = serializers.IntegerField(required=True)
    annee_n2 = serializers.IntegerField(required=True)
    
    # Données calculées (en lecture seule)
    score_n = serializers.FloatField(read_only=True)
    score_n1 = serializers.FloatField(read_only=True)
    score_n2 = serializers.FloatField(read_only=True)
    probabilite_defaillance = serializers.FloatField(read_only=True)
    classe_risque = serializers.CharField(read_only=True)
    commentaire = serializers.CharField(read_only=True)
    
    # Ratios pour l'année N
    r1_ff_ebe = serializers.FloatField(read_only=True)
    r2_creances_dettes_ct = serializers.FloatField(read_only=True)
    r3_capitaux_permanents_passif = serializers.FloatField(read_only=True)
    r4_va_ca = serializers.FloatField(read_only=True)
    r5_tresorerie_ventes_j = serializers.FloatField(read_only=True)
    r6_fdr_ca_j = serializers.FloatField(read_only=True)

class CalculScoreACREMACBilanSerializer(serializers.Serializer):
    # Données d'entrée pour le calcul
    frais_financiers = serializers.DecimalField(max_digits=15, decimal_places=2)
    ebe = serializers.DecimalField(max_digits=15, decimal_places=2)
    creances_disponibilites = serializers.DecimalField(max_digits=15, decimal_places=2)
    dettes_court_terme = serializers.DecimalField(max_digits=15, decimal_places=2)
    capitaux_permanents = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_passif = serializers.DecimalField(max_digits=15, decimal_places=2)
    valeur_ajoutee = serializers.DecimalField(max_digits=15, decimal_places=2)
    chiffre_affaires = serializers.DecimalField(max_digits=15, decimal_places=2)
    tresorerie = serializers.DecimalField(max_digits=15, decimal_places=2)
    fonds_roulement = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Coefficients fixes
    coefficient_constante = serializers.FloatField(default=0.57)
    coefficient_r1 = serializers.FloatField(default=0.0535)
    coefficient_r2 = serializers.FloatField(default=0.0115)
    coefficient_r3 = serializers.FloatField(default=0.0371)
    coefficient_r4 = serializers.FloatField(default=0.0246)
    coefficient_r5 = serializers.FloatField(default=0.0115)
    coefficient_r6 = serializers.FloatField(default=0.0096)
    
    
    
    
    
    
    
# Serializers pour le scoring avec bilan classique
class BilanClassiqueScoreSerializer(serializers.Serializer):
    acheteur_id = serializers.IntegerField(required=True)
    annee_n = serializers.IntegerField(required=True)
    annee_n1 = serializers.IntegerField(required=True)
    annee_n2 = serializers.IntegerField(required=True)
    bilan_type = serializers.CharField(default='classique')

class BilanClassiqueDataSerializer(serializers.Serializer):
    # Données extraites pour le calcul
    frais_financiers = serializers.DecimalField(max_digits=15, decimal_places=2)
    ebe = serializers.DecimalField(max_digits=15, decimal_places=2)
    creances_disponibilites = serializers.DecimalField(max_digits=15, decimal_places=2)
    dettes_court_terme = serializers.DecimalField(max_digits=15, decimal_places=2)
    capitaux_permanents = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_passif = serializers.DecimalField(max_digits=15, decimal_places=2)
    valeur_ajoutee = serializers.DecimalField(max_digits=15, decimal_places=2)
    chiffre_affaires = serializers.DecimalField(max_digits=15, decimal_places=2)
    tresorerie = serializers.DecimalField(max_digits=15, decimal_places=2)
    fonds_roulement = serializers.DecimalField(max_digits=15, decimal_places=2)

class ScoreACREMACResultSerializer(serializers.Serializer):
    score = serializers.FloatField()
    ratios = serializers.DictField()
    ratios_bornees = serializers.DictField()
    classe_risque = serializers.CharField()
    probabilite_defaillance = serializers.FloatField()
    commentaire = serializers.CharField()
    coefficients = serializers.DictField()

class BilanClassiqueScoreResponseSerializer(serializers.Serializer):
    acheteur = serializers.CharField()
    annees = serializers.DictField()
    scores = serializers.DictField()
    score_principal = serializers.FloatField()
    bilan_type = serializers.CharField()
    
    
    







from rest_framework import serializers

class BilanAnglaisScoreSerializer(serializers.Serializer):
    acheteur_id = serializers.IntegerField(required=True)
    annee_n = serializers.IntegerField(required=True)
    annee_n1 = serializers.IntegerField(required=True)
    annee_n2 = serializers.IntegerField(required=True)
    bilan_type = serializers.CharField(default='anglais')

class BilanAnglaisDataSerializer(serializers.Serializer):
    # Données extraites pour le calcul ACREMAC
    frais_financiers = serializers.DecimalField(max_digits=15, decimal_places=2)
    ebe = serializers.DecimalField(max_digits=15, decimal_places=2)
    creances_disponibilites = serializers.DecimalField(max_digits=15, decimal_places=2)
    dettes_court_terme = serializers.DecimalField(max_digits=15, decimal_places=2)
    capitaux_permanents = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_passif = serializers.DecimalField(max_digits=15, decimal_places=2)
    valeur_ajoutee = serializers.DecimalField(max_digits=15, decimal_places=2)
    chiffre_affaires = serializers.DecimalField(max_digits=15, decimal_places=2)
    tresorerie = serializers.DecimalField(max_digits=15, decimal_places=2)
    fonds_roulement = serializers.DecimalField(max_digits=15, decimal_places=2)

class BilanAnglaisScoreResponseSerializer(serializers.Serializer):
    acheteur = serializers.CharField()
    annees = serializers.DictField()
    scores = serializers.DictField()
    score_principal = serializers.FloatField()
    bilan_type = serializers.CharField()
    
    
    
    
    
    
    
    
    
# serializers.py - Ajoutez ces sérialiseurs

class AssetsBancaireSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Propriétés calculées
    a_vue = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    pret_interbancaire = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    porteuille_papier_commercial = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    autres_concours_clients = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    creance_sur_la_clientele = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_assets = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = Assets
        fields = '__all__'

class AddAssetsBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            'caisse', 'banques_centrales', 'tresorerie_cpp', 'autres_ets_credit',
            'a_terme', 'credits_campagne', 'credits_ordinaire', 
            'credits_campagne_acc', 'credits_ordinaire_acc', 'creances_ordinaires',
            'affacturage', 'titres_placement', 'immobilisation_fin',
            'operation_credit_bail', 'immobilisation_incorporelle',
            'immobilisation_corporelle', 'actionnaire_ou_associe',
            'autres_actifs', 'comptes_commande_divers'
        ]

class LiabilitiesBancaireSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Propriétés calculées
    a_vue = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    dette_interbancaire = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    dette_envers_clientelle = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_liabilities = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = Liabilities
        fields = '__all__'

class AddLiabilitiesBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liabilities
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            'tresorerie_ccp', 'autres_etablissement_credit', 'a_terme',
            'comptes_epargne_court_terme', 'comptes_epargne_terme', 'bons_caisse',
            'autres_dette_a_vue', 'autres_dette_a_terme', 'titres_creance_autres_dettes',
            'compte_dordre_divers', 'provision_pour_risque_charge', 'provision_reglementee',
            'emprunt_subordonne_tire_emis', 'subventions_investissement', 'fonds_affecte',
            'fonds_pour_risque_bancaire_generaux', 'capital_ou_dotation',
            'primes_liees_reserve_capital', 'ecarts_reevaluation', 'benefices_non_distribue',
            'resultat_net_exercie'
        ]

class ExpensesBancaireSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Propriétés calculées
    interet_charges_assimilee = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    charge_sur_operation_financiere = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    prestation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    frais_generaux_dexploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_des_charges = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = Expenses
        fields = '__all__'

class AddExpensesBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            'interet_charges_assimilee_dette_interbancaire',
            'interet_charge_assimilee_dette_clientele',
            'interet_charge_assimilee_titre_creance',
            'chargesc_compte_bloque_dactionnaire_emprunt_sub',
            'autres_interets_charges_assimilee',
            'charges_sur_op_credit_bail_assimile', 'commissions',
            'charges_sur_titre_placement', 'charges_sur_operation_change',
            'charges_sur_operation_hors_bilan', 'frais_divers_exploitation_bancaire',
            'achat_marchandises', 'stocks_vendus', 'variations_stocks_marchanides',
            'frais_personnel', 'autres_frais_generaux',
            'dotations_amortissement_provision_immobilisation',
            'solde_perte_creance_hors_bilan',
            'excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux',
            'charges_exceptionnelle', 'pertes_exercice_anterieurs', 'impot_sur_revenu'
        ]

class ProductsBancaireSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Propriétés calculées
    interet_produit_assimile = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    revenu_d_operation_financiere = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    autres_produits_exploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_produit = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = Products
        fields = '__all__'

class AddProductsBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            'interets_produit_assimile_sur_pret_avance_interbancaire',
            'ineterets_produit_assimile_pret_avance_clientele',
            'interet_produit_sur_titre_dinvestissement',
            'revenu_gains_titre_pret_titre_subordonne',
            'autres_interets_produits_assimiles',
            'produits_leansing_operation_connexes', 'commissions',
            'revenus_titre_negociable', 'dividendes_produits_assimiles',
            'revenus_operation_de_change', 'produits_opeations_hors_bilan',
            'produits_bancaire_divers', 'marges_vente', 'ventes_marchandises',
            'variation_stocks_marchandises', 'produit_dexploitation_generale',
            'reprise_damortissement_provisions_sur_immobilisation',
            'solde_resultat_correction_valeur_sur_creance_hors_bilan',
            'excedent_reprise_fonds_pour_risque_bancaire_generaux',
            'produits_exceptionnels', 'benefice_sur_exercice_anterieur', 'perte'
        ]

class OffBalanceSheetBancaireSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Propriétés calculées
    total_engagement_financement_donne = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_engagement_garantie_donne = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_engagements_donnes = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_engagement_financement_recu = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_engagements_recus = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = OffBalanceSheet
        fields = '__all__'

class AddOffBalanceSheetBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = OffBalanceSheet
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            'engagement_financement_donne_ets_credit',
            'engagement_financement_donne_clientele',
            'engagement_garantie_donne_ets_credit',
            'engagement_garantie_donne_clientele',
            'engagement_sur_titres_donnes',
            'engagement_financement_recu_ets_credit',
            'engagement_financement_recu_clientele',
            'engagement_garantie_recu_ets_credit',
            'engagement_sur_titres_recus'
        ]

# Serializer pour le calcul de score
class BilanBancaireScoreSerializer(serializers.Serializer):
    acheteur_id = serializers.IntegerField()
    annee_n = serializers.IntegerField()
    annee_n1 = serializers.IntegerField()
    annee_n2 = serializers.IntegerField()
    bilan_type = serializers.ChoiceField(choices=TYPE_BILAN_CHOICES)
    semestre = serializers.ChoiceField(choices=SEMESTRE_CHOICES, required=False, allow_null=True)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
# serializers.py - Ajoutez ces sérialiseurs

class BilanSyscohadaScoreSerializer(serializers.Serializer):
    acheteur_id = serializers.IntegerField()
    annee_n = serializers.IntegerField()
    annee_n1 = serializers.IntegerField()
    annee_n2 = serializers.IntegerField()

class ActifSSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Propriétés calculées
    immobilisations_incorporelles = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    immobilisations_corporelles = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    immobilisations_financieres = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actif_immobilise = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    creances_emplois_similaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_tresorerie_equivalents = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actif_circulant = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_actif = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ActifS
        fields = '__all__'

class PassifSSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Propriétés calculées
    total_capitaux_propres_ressources_similaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_dettes_financieres_ressources_similaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_ressources_stables = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_passifs_courants = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_tresorerie_equivalents = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    total_passifs = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = PassifS
        fields = '__all__'

class ResultatSSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Propriétés calculées
    marge_commerciale = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    chiffre_affaires = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    valeur_ajoutee = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    excedent_brute_exploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_exploitation = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_financier = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_activites_ordinaires_xe = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_activites_ordinaires_tn = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)
    resultat_net = serializers.DecimalField(max_digits=100, decimal_places=2, read_only=True)

    class Meta:
        model = ResultatS
        fields = '__all__'
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
# serializers.py - Ajoutez ces sérialiseurs

class BilanIFRSScoreSerializer(serializers.Serializer):
    acheteur_id = serializers.IntegerField()
    annee_n = serializers.IntegerField()
    annee_n1 = serializers.IntegerField()
    annee_n2 = serializers.IntegerField()

class ActifIFRSSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Propriétés calculées
    total_actif_non_courant = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_actif_courant = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_actif = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = ActifIFRS
        fields = '__all__'

class PassifIFRSSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Propriétés calculées
    total_capitaux_propres = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_passif_non_courant = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_passif_courant = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_passif = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = PassifIFRS
        fields = '__all__'

class ResultatIFRSSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Propriétés calculées
    chiffre_affaires = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    cout_des_ventes = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    charges_operationnelles = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    amortissements_et_provisions = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    total_charges = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    resultat_operationnel = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    resultat_financier = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    resultat_avant_impot = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)
    resultat_net = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = ResultatIFRS
        fields = '__all__'
        
        
        
# serializers.py - Ajoutez ces classes à votre fichier serializers.py

# serializers.py - CORRECTION DU SERIALIZER

# CORRECTION 1: Classe AnneeListView
class AnneeListView(ListAPIView):
    """Liste des années pour le formulaire"""
    permission_classes = [IsAuthenticated]
    pagination_class = NoPagination
    
    def get(self, request, *args, **kwargs):
        annees = Annee.objects.filter(is_active=True).order_by('-annee')
        data = [
            {
                'id': annee.id,
                'annee': annee.annee,
                'is_active': annee.is_active
            }
            for annee in annees
        ]
        return Response(data)

# serializers.py
class ScoringSerializer(serializers.ModelSerializer):
    annee_details = serializers.SerializerMethodField(read_only=True)
    acheteur_details = serializers.SerializerMethodField(read_only=True)
    created_by_details = UserSimpleSerializer(source='created_by', read_only=True)
    updated_by_details = UserSimpleSerializer(source='updated_by', read_only=True)
    score_category = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Scoring
        fields = [
            'id',
            'annee', 'annee_details',
            'acheteur', 'acheteur_details',
            'score', 'score_category',
            'commentaire',
            'created_at', 'updated_at',
            'created_by', 'created_by_details',
            'updated_by', 'updated_by_details'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_annee_details(self, obj):
        if obj.annee:
            return {
                'id': obj.annee.id,
                'annee': obj.annee.annee,
                'is_active': obj.annee.is_active
            }
        return None
    
    def get_acheteur_details(self, obj):
        if obj.acheteur:
            return {
                'id': obj.acheteur.id,
                'nom': obj.acheteur.nom,
                'sigle': obj.acheteur.sigle,
                'code': obj.acheteur.code
            }
        return None
    
    def get_score_category(self, obj):
        return obj.get_score_category()
    
    def validate_score(self, value):
        """Validation du score"""
        if value is None or value == '':
            raise serializers.ValidationError("Le score est obligatoire")
        
        try:
            score_float = float(value)
            if score_float < 0 or score_float > 10:
                raise serializers.ValidationError("Le score doit être entre 0 et 10")
        except (ValueError, TypeError):
            raise serializers.ValidationError("Le score doit être un nombre valide entre 0 et 10")
        
        return str(score_float)  # S'assurer que c'est une chaîne
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ScoringDelphiSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le Score Commercial Delphi ACREMAC."""
    acheteur_nom = serializers.SerializerMethodField(read_only=True)
    created_by_details = UserSimpleSerializer(source='created_by', read_only=True)
    updated_by_details = UserSimpleSerializer(source='updated_by', read_only=True)
    bande_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ScoringDelphi
        fields = [
            'id', 'acheteur', 'acheteur_nom',
            # A — Paiement
            'dbt', 'tendance_dbt_hausse', 'montants_contestes',
            # B — Légal
            'est_en_liquidation', 'petition_faillite',
            'nb_procedures_collectives', 'nb_inscriptions_privileges', 'nb_jugements_tribunaux',
            # C — Finances
            'ratio_liquidite', 'marge_nette', 'ebitda_ratio', 'ratio_endettement', 'retard_depot_bilan',
            # D — Démographie
            'age_entreprise', 'historique_dirigeants_negatif',
            # Résultats
            'score_delphi', 'bande', 'bande_display', 'etoiles', 'niveau_risque',
            # Méta
            'commentaire', 'created_at', 'updated_at',
            'created_by', 'created_by_details',
            'updated_by', 'updated_by_details',
        ]
        read_only_fields = [
            'score_delphi', 'bande', 'etoiles', 'niveau_risque',
            'created_at', 'updated_at', 'created_by', 'updated_by',
        ]

    def get_acheteur_nom(self, obj):
        return str(obj.acheteur) if obj.acheteur else None

    def get_bande_display(self, obj):
        bande_labels = {
            'A': 'A — Risque très faible',
            'B': 'B — Faible risque',
            'C': 'C — Risque inférieur à la moyenne',
            'D': 'D — Risque supérieur à la moyenne',
            'E': 'E — Risque élevé',
            'F': 'F — Risque maximal',
            'G': 'G — Faillite imminente',
            '-': '— Dissoute / Liquidée',
        }
        return bande_labels.get(obj.bande, obj.bande)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


# CORRECTION 2: ScoringListView - amélioration des filtres
class ScoringListView(ListAPIView):
    """Liste des scorings manuels avec filtrage"""
    serializer_class = ScoringSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    page_size = 10  # Définir une taille de page
    
    def get_queryset(self):
        queryset = Scoring.objects.select_related(
            'annee', 'acheteur', 'created_by'
        ).order_by('-created_at')
        
        # Filtrage par acheteur (ID de l'acheteur courant)
        acheteur_id = self.request.query_params.get('acheteur_id')
        if acheteur_id and acheteur_id != 'null':
            try:
                queryset = queryset.filter(acheteur_id=int(acheteur_id))
            except (ValueError, TypeError):
                pass
        
        # Filtrage par année
        annee_id = self.request.query_params.get('annee_id')
        if annee_id and annee_id != '' and annee_id != 'null':
            try:
                queryset = queryset.filter(annee_id=int(annee_id))
            except (ValueError, TypeError):
                pass
        
        # Filtrage par score (gestion des erreurs)
        try:
            score_min = self.request.query_params.get('score_min')
            if score_min and score_min != '':
                score_min_float = float(score_min)
                # Filtrage pour scores numériques
                queryset = queryset.filter(
                    Q(score__gte=str(score_min_float)) |
                    Q(score__isnull=False) & ~Q(score='')
                )
        except (ValueError, TypeError):
            pass
        
        try:
            score_max = self.request.query_params.get('score_max')
            if score_max and score_max != '':
                score_max_float = float(score_max)
                queryset = queryset.filter(
                    Q(score__lte=str(score_max_float)) |
                    Q(score__isnull=False) & ~Q(score='')
                )
        except (ValueError, TypeError):
            pass
        
        # Recherche texte
        search = self.request.query_params.get('search')
        if search and search != '':
            queryset = queryset.filter(
                Q(acheteur__nom__icontains=search) |
                Q(acheteur__sigle__icontains=search) |
                Q(commentaire__icontains=search)
            )
        
        return queryset

# CORRECTION 3: APIView pour obtenir les détails d'un acheteur
class AcheteurDetailView(APIView):
    """Récupérer les détails d'un acheteur pour l'encart"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, acheteur_id):
        try:
            acheteur = Acheteur.objects.select_related(
                'statut_entreprise', 'forme_juridique',
                'pays', 'province', 'ville'
            ).get(id=acheteur_id)
            
            data = {
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
            return Response(data)
        except Acheteur.DoesNotExist:
            return Response({'error': 'Acheteur non trouvé'}, status=404)
    """Serializer simplifié pour les listes"""
    
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    acheteur_sigle = serializers.CharField(source='acheteur.sigle', read_only=True)
    annee_value = serializers.IntegerField(source='annee.annee', read_only=True)
    score_category = serializers.SerializerMethodField()
    score_numeric = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Scoring
        fields = [
            'id',
            'annee', 'annee_value',
            'acheteur', 'acheteur_nom', 'acheteur_sigle',
            'score', 'score_category', 'score_numeric',
            'commentaire',
            'created_at',
            'created_by_name'
        ]
    
    def get_score_category(self, obj):
        return obj.get_score_category()
    
    def get_score_numeric(self, obj):
        return obj.get_score_numeric()
    
    
    
    
    
    
    


# Serializers pour le modèle ActifIFRS
class ActifIFRSOneSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Inclusion des propriétés de calcul en lecture seule
    total_actif_non_courant = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    total_actif_courant = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    total_actif = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    
    # Champ pour afficher le type de bilan
    type_bilan_display = serializers.CharField(
        source='get_type_bilan_display', read_only=True
    )
    
    # Champ pour afficher le semestre
    semestre_display = serializers.CharField(
        source='get_semestre_display', read_only=True
    )

    class Meta:
        model = ActifIFRS
        fields = '__all__'


class AddActifIFRSOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifIFRS
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            # Actif non courant
            'goodwill', 'marques_et_droits_auteur', 'brevets_et_licences',
            'autres_immobilisations_incorporelles', 'terrains', 'batiments',
            'materiel_et_equipement', 'participations_dans_des_societes',
            'prets_a_long_terme',
            # Actif courant
            'matieres_premieres', 'produits_finis', 'creances_a_court_terme',
            'avances_et_acomptes', 'creances_diverses', 'disponibilites_bancaires'
        ]
        extra_kwargs = {'semestre': {'required': False, 'allow_null': True}}
    
    def validate(self, data):
        # Validation pour s'assurer que le semestre est fourni si type est semestriel
        if data.get('type_bilan') == 'semestriel' and not data.get('semestre'):
            raise serializers.ValidationError({
                'semestre': 'Le semestre est obligatoire pour un bilan semestriel.'
            })
        
        # Validation pour s'assurer que le semestre n'est pas fourni si type est annuel
        if data.get('type_bilan') == 'annuel' and data.get('semestre'):
            raise serializers.ValidationError({
                'semestre': 'Le semestre ne doit pas être renseigné pour un bilan annuel.'
            })
        
        return data


class EditActifIFRSOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActifIFRS
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            # Actif non courant
            'goodwill', 'marques_et_droits_auteur', 'brevets_et_licences',
            'autres_immobilisations_incorporelles', 'terrains', 'batiments',
            'materiel_et_equipement', 'participations_dans_des_societes',
            'prets_a_long_terme',
            # Actif courant
            'matieres_premieres', 'produits_finis', 'creances_a_court_terme',
            'avances_et_acomptes', 'creances_diverses', 'disponibilites_bancaires'
        ]
        extra_kwargs = {'semestre': {'required': False, 'allow_null': True}}
    
    def validate(self, data):
        # Reprendre la même validation que pour l'ajout
        type_bilan = data.get('type_bilan', self.instance.type_bilan if self.instance else None)
        semestre = data.get('semestre', self.instance.semestre if self.instance else None)
        
        if type_bilan == 'semestriel' and not semestre:
            raise serializers.ValidationError({
                'semestre': 'Le semestre est obligatoire pour un bilan semestriel.'
            })
        
        if type_bilan == 'annuel' and semestre:
            raise serializers.ValidationError({
                'semestre': 'Le semestre ne doit pas être renseigné pour un bilan annuel.'
            })
        
        return data
    
    
    


# Serializers pour le modèle PassifIFRS
class PassifIFRSOneSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Inclusion des propriétés de calcul en lecture seule
    total_capitaux_propres = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    total_passif_non_courant = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    total_passif_courant = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    total_passif = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    
    # Champ pour afficher le type de bilan
    type_bilan_display = serializers.CharField(
        source='get_type_bilan_display', read_only=True
    )
    
    # Champ pour afficher le semestre
    semestre_display = serializers.CharField(
        source='get_semestre_display', read_only=True
    )

    class Meta:
        model = PassifIFRS
        fields = '__all__'


class AddPassifIFRSOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifIFRS
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            # Capitaux Propres
            'capital_social', 'primes_emission', 'reserves_legales',
            'reserves_statutaires', 'reserves_facultatives', 'autres_reserves',
            'resultat_net_reporte',
            # Passif non courant
            'emprunts_bancaires_long_terme', 'obligations',
            'provisions_pour_retraites_et_pensions', 'autres_provisions',
            # Passif courant
            'dettes_fournisseurs_a_court_terme', 'impots_sur_le_revenu',
            'cotisations_sociales', 'emprunts_bancaires_court_terme',
            'dettes_diverses', 'dividendes_a_payer'
        ]
        extra_kwargs = {'semestre': {'required': False, 'allow_null': True}}
    
    def validate(self, data):
        # Validation pour s'assurer que le semestre est fourni si type est semestriel
        if data.get('type_bilan') == 'semestriel' and not data.get('semestre'):
            raise serializers.ValidationError({
                'semestre': 'Le semestre est obligatoire pour un bilan semestriel.'
            })
        
        # Validation pour s'assurer que le semestre n'est pas fourni si type est annuel
        if data.get('type_bilan') == 'annuel' and data.get('semestre'):
            raise serializers.ValidationError({
                'semestre': 'Le semestre ne doit pas être renseigné pour un bilan annuel.'
            })
        
        return data


class EditPassifIFRSOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassifIFRS
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            # Capitaux Propres
            'capital_social', 'primes_emission', 'reserves_legales',
            'reserves_statutaires', 'reserves_facultatives', 'autres_reserves',
            'resultat_net_reporte',
            # Passif non courant
            'emprunts_bancaires_long_terme', 'obligations',
            'provisions_pour_retraites_et_pensions', 'autres_provisions',
            # Passif courant
            'dettes_fournisseurs_a_court_terme', 'impots_sur_le_revenu',
            'cotisations_sociales', 'emprunts_bancaires_court_terme',
            'dettes_diverses', 'dividendes_a_payer'
        ]
        extra_kwargs = {'semestre': {'required': False, 'allow_null': True}}
    
    def validate(self, data):
        # Reprendre la même validation que pour l'ajout
        type_bilan = data.get('type_bilan', self.instance.type_bilan if self.instance else None)
        semestre = data.get('semestre', self.instance.semestre if self.instance else None)
        
        if type_bilan == 'semestriel' and not semestre:
            raise serializers.ValidationError({
                'semestre': 'Le semestre est obligatoire pour un bilan semestriel.'
            })
        
        if type_bilan == 'annuel' and semestre:
            raise serializers.ValidationError({
                'semestre': 'Le semestre ne doit pas être renseigné pour un bilan annuel.'
            })
        
        return data
    
    
    

# Serializers pour le modèle ResultatIFRS
class ResultatIFRSOneSerializer(serializers.ModelSerializer):
    annee = AnneeSerializer(read_only=True)
    acheteur = AcheteurSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    # Inclusion des propriétés de calcul en lecture seule
    chiffre_affaires = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    autres_produits_operationnels = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    total_produits = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    cout_des_ventes = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    charges_operationnelles = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    amortissements_et_provisions = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    total_charges = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    resultat_operationnel = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    resultat_financier = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    resultat_avant_impot = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    resultat_net = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True
    )
    
    # Champ pour afficher le type de bilan
    type_bilan_display = serializers.CharField(
        source='get_type_bilan_display', read_only=True
    )
    
    # Champ pour afficher le semestre
    semestre_display = serializers.CharField(
        source='get_semestre_display', read_only=True
    )

    class Meta:
        model = ResultatIFRS
        fields = '__all__'


class AddResultatIFRSOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatIFRS
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            # Produits
            'ventes_biens', 'ventes_services', 'subventions_exploitation',
            'revenus_exceptionnels', 'revenus_financiers',
            # Charges
            'achats_matieres_premieres', 'autres_couts_directs',
            'salaires_et_charges_sociales', 'loyer_et_charges_locatives',
            'autres_charges_exploitation', 'amortissement_des_immobilisations',
            'provisions_pour_risques_et_charges', 'charges_financieres',
            'impot_sur_les_societes'
        ]
        extra_kwargs = {'semestre': {'required': False, 'allow_null': True}}
    
    def validate(self, data):
        # Validation pour s'assurer que le semestre est fourni si type est semestriel
        if data.get('type_bilan') == 'semestriel' and not data.get('semestre'):
            raise serializers.ValidationError({
                'semestre': 'Le semestre est obligatoire pour un bilan semestriel.'
            })
        
        # Validation pour s'assurer que le semestre n'est pas fourni si type est annuel
        if data.get('type_bilan') == 'annuel' and data.get('semestre'):
            raise serializers.ValidationError({
                'semestre': 'Le semestre ne doit pas être renseigné pour un bilan annuel.'
            })
        
        return data


class EditResultatIFRSOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultatIFRS
        fields = [
            'type_bilan', 'annee', 'semestre', 'acheteur',
            # Produits
            'ventes_biens', 'ventes_services', 'subventions_exploitation',
            'revenus_exceptionnels', 'revenus_financiers',
            # Charges
            'achats_matieres_premieres', 'autres_couts_directs',
            'salaires_et_charges_sociales', 'loyer_et_charges_locatives',
            'autres_charges_exploitation', 'amortissement_des_immobilisations',
            'provisions_pour_risques_et_charges', 'charges_financieres',
            'impot_sur_les_societes'
        ]
        extra_kwargs = {'semestre': {'required': False, 'allow_null': True}}
    
    def validate(self, data):
        # Reprendre la même validation que pour l'ajout
        type_bilan = data.get('type_bilan', self.instance.type_bilan if self.instance else None)
        semestre = data.get('semestre', self.instance.semestre if self.instance else None)
        
        if type_bilan == 'semestriel' and not semestre:
            raise serializers.ValidationError({
                'semestre': 'Le semestre est obligatoire pour un bilan semestriel.'
            })
        
        if type_bilan == 'annuel' and semestre:
            raise serializers.ValidationError({
                'semestre': 'Le semestre ne doit pas être renseigné pour un bilan annuel.'
            })
        
        return data







class UserMailingSerializer(serializers.ModelSerializer):
    """
    Serializer pour les clients dans le module d'emailing
    """
    full_name = serializers.SerializerMethodField()
    email_principal = serializers.EmailField(source='email')
    telephone_display = serializers.CharField(source='telephone', read_only=True)
    pays_nom = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'full_name',
            'email_principal',
            'telephone_display',
            'pays_nom',
            'profession',
            'is_active',
        ]
    
    def get_full_name(self, obj):
        """Retourne le nom complet de l'utilisateur"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username
    
    def get_pays_nom(self, obj):
        """Retourne le nom du pays de l'utilisateur"""
        if hasattr(obj, 'pays') and obj.pays:
            return obj.pays.nom
        return None

class AcheteurCommandeSerializer(serializers.ModelSerializer):
    """
    Serializer pour les acheteurs liés aux commandes
    """
    class Meta:
        model = Acheteur
        fields = [
            'id',
            'nom',
            'code',
            'sigle',
        ]

class CommandeMailingSerializer(serializers.ModelSerializer):
    """
    Serializer pour les commandes dans le module d'emailing
    """
    acheteur_details = AcheteurCommandeSerializer(source='acheteur', read_only=True)
    date_commande_formatted = serializers.SerializerMethodField()
    montant_formatted = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Commande
        fields = [
            'id',
            'reference_client',
            'date_recept_commande',
            'date_commande_formatted',
            'credit_demande',
            'montant_formatted',
            'status',
            'statut_display',
            'acheteur',
            'acheteur_details',
            'comments',
        ]
    
    def get_date_commande_formatted(self, obj):
        """Formatage de la date de réception commande"""
        if obj.date_recept_commande:
            return obj.date_recept_commande.strftime('%d/%m/%Y')
        return None
    
    def get_montant_formatted(self, obj):
        """Formatage du montant (credit_demande)"""
        if obj.credit_demande:
            # Format sans décimales
            montant = int(float(obj.credit_demande))
            return f"{montant:,} FCFA".replace(',', ' ')
        return "0 FCFA"

class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer pour les documents
    """
    taille_formatted = serializers.SerializerMethodField()
    date_upload_formatted = serializers.SerializerMethodField()
    icone_class = serializers.SerializerMethodField()
    uploader = serializers.CharField(source='created_by.username', read_only=True, default="Inconnu")
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id',
            'titre',
            'fichier',
            'created_at',
            'date_upload_formatted',
            'description',
            'acheteur',
            'acheteur_nom',
            'uploader',
            'icone_class',
            'taille_formatted'
        ]
    
    def get_taille_formatted(self, obj):
        """Formate la taille du fichier"""
        if not obj.fichier or not hasattr(obj.fichier, 'size') or not obj.fichier.size:
            return "0 Ko"
        
        taille = obj.fichier.size
        if taille < 1024:
            return f"{taille} o"
        elif taille < 1024 * 1024:
            return f"{taille / 1024:.1f} Ko"
        else:
            return f"{taille / (1024 * 1024):.1f} Mo"
    
    def get_date_upload_formatted(self, obj):
        """Formate la date de création"""
        if obj.created_at:
            return obj.created_at.strftime('%d/%m/%Y %H:%M')
        return None
    
    def get_icone_class(self, obj):
        """Retourne la classe CSS de l'icône selon le type de fichier"""
        if not obj.fichier or not obj.fichier.name:
            return 'fa-file'
        
        extension = obj.fichier.name.split('.')[-1].lower() if '.' in obj.fichier.name else ''
        
        icones = {
            'pdf': 'fa-file-pdf',
            'doc': 'fa-file-word',
            'docx': 'fa-file-word',
            'xls': 'fa-file-excel',
            'xlsx': 'fa-file-excel',
            'jpg': 'fa-file-image',
            'jpeg': 'fa-file-image',
            'png': 'fa-file-image',
            'gif': 'fa-file-image',
            'txt': 'fa-file-alt',
            'csv': 'fa-file-csv',
        }
        
        return icones.get(extension, 'fa-file')

class EnvoyerEmailSerializer(serializers.Serializer):
    """
    Serializer pour valider les données d'envoi d'email
    """
    client_id = serializers.IntegerField(required=True)
    periode = serializers.CharField(required=True, allow_blank=True)
    sujet = serializers.CharField(required=True, max_length=500)
    message = serializers.CharField(required=True)
    cc = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    commandes = serializers.CharField(required=True)  # JSON string
    documents = serializers.CharField(required=True)  # JSON string
    rapports = serializers.CharField(required=False, allow_blank=True, allow_null=True)  # JSON string
    total_attachments = serializers.IntegerField(required=False, default=0)
    total_commands = serializers.IntegerField(required=False, default=0)
    
    def validate_client_id(self, value):
        """Vérifie que le client existe"""
        try:
            User.objects.get(id=value, role__iexact='Client', is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("Client non trouvé ou inactif")
        return value
    
    def validate_commandes(self, value):
        """Valide et parse la liste des commandes"""
        try:
            commandes_list = json.loads(value)
            if not isinstance(commandes_list, list):
                raise serializers.ValidationError("Le format des commandes est invalide")
            
            # Vérifier que toutes les commandes existent
            for cmd_id in commandes_list:
                try:
                    Commande.objects.get(id=cmd_id)
                except Commande.DoesNotExist:
                    raise serializers.ValidationError(f"Commande {cmd_id} non trouvée")
            
            return commandes_list
        except json.JSONDecodeError:
            raise serializers.ValidationError("Format JSON invalide pour les commandes")
    
    def validate_documents(self, value):
        """Valide et parse la liste des documents"""
        try:
            documents_list = json.loads(value)
            if not isinstance(documents_list, list):
                raise serializers.ValidationError("Le format des documents est invalide")
            
            # Vérifier que tous les documents existent
            for doc_id in documents_list:
                try:
                    Document.objects.get(id=doc_id)
                except Document.DoesNotExist:
                    raise serializers.ValidationError(f"Document {doc_id} non trouvé")
            
            return documents_list
        except json.JSONDecodeError:
            raise serializers.ValidationError("Format JSON invalide pour les documents")
    
    def validate_rapports(self, value):
        """Valide et parse la liste des rapports (optionnel)"""
        if not value:
            return []
        
        try:
            rapports_list = json.loads(value)
            if not isinstance(rapports_list, list):
                raise serializers.ValidationError("Le format des rapports est invalide")
            return rapports_list
        except json.JSONDecodeError:
            raise serializers.ValidationError("Format JSON invalide pour les rapports")
    
    def validate_cc(self, value):
        """Valide les emails en CC"""
        if not value:
            return ""
        
        emails = [email.strip() for email in value.split(';') if email.strip()]
        for email in emails:
            import re
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                raise serializers.ValidationError(f"Email invalide: {email}")
        
        return value

class MailInfoDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour l'historique"""
    commandes_details = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    destinataire = serializers.SerializerMethodField()
    
    class Meta:
        model = MailInfo
        fields = '__all__'
    
    def get_commandes_details(self, obj):
        return [{
            'id': cmd.id,
            'notre_ref': cmd.notre_ref,
            'raison_sociale': cmd.raison_sociale,
            'status': cmd.status
        } for cmd in obj.commands.all()]
    
    def get_attachments(self, obj):
        return [{
            'id': att.id,
            'nom': att.upload.name.split('/')[-1],
            'url': att.upload.url if att.upload else '',
            'taille': att.upload.size if att.upload else 0,
            'est_document': getattr(att, 'is_document', False)
        } for att in MailAttachment.objects.filter(mailinfo=obj)]
    
    def get_destinataire(self, obj):
        # Récupérer le premier client à partir des commandes
        commande = obj.commands.first()
        if commande and commande.client:
            return {
                'nom': commande.client.nom,
                'email': commande.client.email
            }
        return None

class EmailComposeSerializer(serializers.Serializer):
    """Serializer pour la composition d'email"""
    client_id = serializers.IntegerField()
    commandes_ids = serializers.ListField(child=serializers.IntegerField())
    sujet = serializers.CharField(max_length=500)
    message = serializers.CharField()
    html_message = serializers.CharField(required=False, allow_blank=True)
    cc = serializers.CharField(required=False, allow_blank=True)
    formats = serializers.ListField(child=serializers.CharField(), default=['pdf'])
    documents_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=[])
    inclure_email_acheteur = serializers.BooleanField(default=True)
    periode_jours = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_client_id(self, value):
        if not Client.objects.filter(id=value, actif=True).exists():
            raise serializers.ValidationError("Client invalide")
        return value
    
    def validate_commandes_ids(self, value):
        commandes = Commande.objects.filter(id__in=value)
        if commandes.count() != len(value):
            raise serializers.ValidationError("Certaines commandes sont invalides")
        
        # Vérifier que les commandes sont éligibles
        commandes_non_envoyees = commandes.filter(email_envoye=False)
        if commandes_non_envoyees.count() != len(value):
            raise serializers.ValidationError("Certaines commandes ont déjà été envoyées")
        
        return value
