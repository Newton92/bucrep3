from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import datetime
import time
from main.utilitaires.constantes import *
from phonenumber_field.modelfields import PhoneNumberField #Gestion des numéros de téléphones
from django_countries.fields import CountryField #Gestion des pays

from decimal import Decimal

from .utils import calculer_grille_age

# Create your models here.

couleur_validator = RegexValidator(r'^#([0-9A-Fa-f]{3}){1,2}$', 'La couleur doit être au format hexadécimal (#RRGGBB ou #RGB).')



def generate_unique_code():
    # Obtenir l'année en cours
    current_year = datetime.datetime.now().year

    # Obtenir le timestamp actuel
    timestamp = int(time.time())

    # Formater le code unique
    unique_code = f"{current_year}-{timestamp}"

    return unique_code

# Exemple d'utilisation
unique_code = generate_unique_code()
print(unique_code)




# === Models CustomUser === #

ROLES_USERS = [
    ('Root', 'Root'),
    ('Validateur', 'Validateur'),
    ('Analyste', 'Analyste'),
    ('Client', 'Client'),
]

class CustomUser(AbstractUser):
    # Attributs par défaut de AbstractUser (masqués)
    # username = models.CharField(
    #     _('username'),
    #     max_length=150,
    #     unique=True,
    #     help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
    #     validators=[AbstractUser.username_validator],
    #     error_messages={
    #         'unique': _("A user with that username already exists."),
    #     },
    # )
    # first_name = models.CharField(_('first name'), max_length=150, blank=True)
    # last_name = models.CharField(_('last name'), max_length=150, blank=True)
    # email = models.EmailField(_('email address'), blank=True)
    # is_staff = models.BooleanField(
    #     _('staff status'),
    #     default=False,
    #     help_text=_('Designates whether the user can log into this admin site.'),
    # )
    # is_active = models.BooleanField(
    #     _('active'),
    #     default=True,
    #     help_text=_(
    #         'Designates whether this user should be treated as active. '
    #         'Unselect this instead of deleting accounts.'
    #     ),
    # )
    # date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    # Attributs supplémentaires
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text=_('Upload an image for your avatar.')
    )
    code_secret = models.CharField(
        _('secret code'),
        max_length=6,
        null=True,
        blank=True,
        help_text=_('A 6-digit code for forgot and reset password.')
    )
    code_connexion = models.CharField(
        _('connexion code'),
        max_length=6,
        null=True,
        blank=True,
        help_text=_('A 6-digit code for two-factor authentication.')
    )
    address = models.CharField(
        _('adresse'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("L'adresse de l'utilisateur.")
    )
    activation = models.BooleanField(
        _('activation'),
        default=True,
        help_text=_('Designates whether the user account is activated.')
    )
    auth_a2f = models.BooleanField(
        _('two-factor authentication'),
        default=False,
        help_text=_('Designates whether two-factor authentication is enabled for the user.')
    )
    telephone = models.CharField(
        _('telephone'),
        max_length=20,
        null=True,
        blank=True,
        help_text=_('The telephone number of the user.')
    )
    profession = models.CharField(
        _('profession'),
        max_length=100,
        null=True,
        blank=True,
        help_text=_('The profession of the user.')
    )
    email_cc = models.EmailField(
        _('email cc'),
        null=True,
        blank=True,
        help_text=_('The carbon copy email address of the user.')
    )

    role = models.CharField(max_length=100, choices=ROLES_USERS, verbose_name="Droits utilisateur", null=True, blank=True)
    
    reset_token = models.CharField(
        _('reset token'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_('Token for password reset.')
    )

    pays = models.ForeignKey(
        'Pays',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name=_("Pays"),
        help_text=_("Pays où l'employé est affecté")
    )

    def __str__(self):
        return self.username

    
    def fullname(self):
        return '%s %s' % (self.first_name, self.last_name)
    
    
# === Models Localisation === #


class Pays(models.Model):
    nom = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name=_("Nom du pays"), 
        help_text=_("Nom complet du pays, par exemple 'France' ou 'Cameroun'.")
    )
    code = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name=_("Code du pays"), 
        help_text=_("Code unique du pays, par exemple 'FR' pour la France ou 'CM' pour le Cameroun.")
    )
    afficher_au_dashboard = models.BooleanField(
        default=False, 
        verbose_name=_("Afficher au dashboard"), 
        help_text=_("Indique si ce pays doit apparaître dans les tableaux de bord.")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Date de création"), 
        help_text=_("Date et heure à laquelle ce pays a été ajouté.")
    )
    date_modification = models.DateTimeField(
        auto_now=True, 
        verbose_name=_("Date de dernière modification"), 
        help_text=_("Date et heure de la dernière mise à jour de ce pays.")
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name=_("Actif"), 
        help_text=_("Indique si le pays est actif ou désactivé.")
    )

    class Meta:
        verbose_name = _("Pays")
        verbose_name_plural = _("Pays")
        ordering = ["nom"]  # Trie les pays par nom dans l'ordre alphabétique.

    def __str__(self):
        return f"{self.nom} ({self.code})"
    

class Province(models.Model):
    nom = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Nom de la province"),
        help_text=_("Nom complet de la province, par exemple 'Île-de-France' ou 'Ouest'.")
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Code de la province"),
        help_text=_("Code unique de la province, par exemple 'IDF' pour l'Île-de-France ou 'OUEST' pour l'Ouest.")
    )
    pays = models.ForeignKey(
        'Pays',
        null=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Pays"),
        help_text=_("Pays auquel appartient la province.")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure à laquelle cette province a été ajoutée.")
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de dernière modification"),
        help_text=_("Date et heure de la dernière mise à jour de cette province.")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si la province est active ou désactivée.")
    )

    class Meta:
        verbose_name = _("Province")
        verbose_name_plural = _("Provinces")
        ordering = ["nom"]  # Trie les provinces par nom dans l'ordre alphabétique.

    def __str__(self):
        return f"{self.nom} ({self.code})"


class Ville(models.Model):
    nom = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Nom de la ville"),
        help_text=_("Nom complet de la ville, par exemple 'Paris' ou 'Douala'.")
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Code de la ville"),
        help_text=_("Code unique de la ville, par exemple 'PAR' pour Paris ou 'DOU' pour Douala.")
    )
    province = models.ForeignKey(
        'Province',
        null=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Province"),
        help_text=_("Province à laquelle appartient la ville.")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure à laquelle cette ville a été ajoutée.")
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de dernière modification"),
        help_text=_("Date et heure de la dernière mise à jour de cette ville.")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si la ville est active ou désactivée.")
    )

    class Meta:
        verbose_name = _("Ville")
        verbose_name_plural = _("Villes")
        ordering = ["nom"]  # Trie les villes par nom dans l'ordre alphabétique.

    def __str__(self):
        return f"{self.nom} ({self.code})"


class Annee(models.Model):
    annee = models.IntegerField(
        unique=True,
        verbose_name=_("Année"),
        help_text=_("Année de référence, par exemple 2025.")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création de l'année.")
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification"),
        help_text=_("Date et heure de la dernière modification de l'année.")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si l'année est active ou désactivée.")
    )

    class Meta:
        verbose_name = _("Année civile")
        verbose_name_plural = _("Années civiles")
        ordering = ["annee"]  # Trie les années par ordre croissant.

    def __str__(self):
        return str(self.annee)


class Devise(models.Model):
    nom = models.CharField(
        max_length=50,
        verbose_name=_("Nom"),
        help_text=_("Nom complet de la devise, par exemple 'Dollar américain'.")
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Code"),
        help_text=_("Code unique de la devise, par exemple 'USD' pour le Dollar ou 'EUR' pour l'Euro.")
    )
    symbole = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("Symbole"),
        help_text=_("Symbole de la devise, par exemple '$' pour le Dollar ou '€' pour l'Euro.")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création de la devise.")
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification"),
        help_text=_("Date et heure de la dernière modification de la devise.")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si la devise est active ou désactivée.")
    )

    class Meta:
        verbose_name = _("Devise")
        verbose_name_plural = _("Devises")
        ordering = ["nom"]  # Trie les devises par nom dans l'ordre alphabétique.

    def __str__(self):
        return f"{self.nom} ({self.code})"


class CouleurCommentaire(models.Model):
    couleur = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Nom de la Couleur"),
        help_text=_("Nom de la couleur, par exemple '#FF5733'.")
    )
    code = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Code Couleur"),
        validators=[couleur_validator],
        help_text=_("Code hexadécimal de la couleur, par exemple '#FF5733'.")
    )

    class Meta:
        verbose_name = _("Coloration")
        verbose_name_plural = _("Colorations")
        ordering = ["code"]  # Trie les devises par nom dans l'ordre alphabétique.

    def __str__(self):
        return self.couleur
        
        
class CategoryNaceCode(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    grille = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True, verbose_name=_("Grille"))
    active = models.BooleanField(_("Actif"), default=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}"

    class Meta:
        verbose_name = _("Catégorie Code NACE")
        verbose_name_plural = _("Catégories Code NACE")
        ordering = ["code"]


class SubCategoryNaceCode(models.Model):
    category = models.ForeignKey(
        CategoryNaceCode,
        on_delete=models.CASCADE,
        related_name="subcategories",
        verbose_name=_("Catégorie"),
    )
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.libelle else _("Sous-Catégorie Code NACE sans libellé")

    class Meta:
        verbose_name = _("Sous-Catégorie Code NACE")
        verbose_name_plural = _("Sous-Catégories Code NACE")
        ordering = ["code"]
        
        
class CategoryNafCode(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.libelle else _("Catégorie Code NAF sans libellé")

    class Meta:
        verbose_name = _("Catégorie Code NAF")
        verbose_name_plural = _("Catégories Code NAF")
        ordering = ["code"]


class SubCategoryNafCode(models.Model):
    category = models.ForeignKey(
        CategoryNafCode,
        on_delete=models.CASCADE,
        related_name="subcategories",
        verbose_name=_("Catégorie"),
    )
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.libelle else _("Sous-Catégorie Code NAF sans libellé")

    class Meta:
        verbose_name = _("Sous-Catégorie Code NAF")
        verbose_name_plural = _("Sous-Catégories Code NAF")
        ordering = ["code"]
        
        
class FormeJuridique(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    grille = models.DecimalField(max_digits=100, decimal_places=3, null=True, blank=True, verbose_name=_("Grille"))
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.libelle else _("Forme juridique sans libellé")

    class Meta:
        verbose_name = _("Forme juridique")
        verbose_name_plural = _("Formes juridiques")
        ordering = ["code"]
# 
class Local(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    grille = models.DecimalField(max_digits=100, decimal_places=3, null=True, blank=True, verbose_name=_("Grille"))
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.libelle else _("Local sans libellé")

    class Meta:
        verbose_name = _("Local")
        verbose_name_plural = _("Locaux")
        ordering = ["code"]


class ExperiencePaiement(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    grille = models.DecimalField(max_digits=100, decimal_places=3, null=True, blank=True, verbose_name=_("Grille"))
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.libelle else _("Expérience de paiement sans libellé")

    class Meta:
        verbose_name = _("Expérience de paiement")
        verbose_name_plural = _("Expérience de paiements")
        ordering = ["code"]


        
class DomaineEntreprise(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, unique=True, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.libelle else _("Domaine entreprise sans libellé")

    class Meta:
        verbose_name = _("Domaine entreprise")
        verbose_name_plural = _("Domaines entreprise")
        ordering = ["libelle"]


class PosteEntreprise(models.Model):
    domaine = models.ForeignKey(
        DomaineEntreprise,
        on_delete=models.CASCADE,
        related_name="postes",
        verbose_name=_("Domaine Entreprise"),
    )
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.libelle} ({self.domaine.libelle})" if self.domaine else _("Poste entreprise sans domaine")

    class Meta:
        verbose_name = _("Poste entreprise")
        verbose_name_plural = _("Postes entreprise")
        ordering = ["libelle"]
        

class CategorieEntreprise(models.Model):
    code = models.CharField(_("Code"), max_length=255, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return self.libelle or _("Catégorie sans libellé")

    class Meta:
        verbose_name = _("Catégorie d'Entreprise")
        verbose_name_plural = _("Catégories d'Entreprises")
        
        
class StructureEntreprise(models.Model):
    code = models.CharField(_("Code"), max_length=255, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return self.libelle or _("Structure sans libellé")

    class Meta:
        verbose_name = _("Structure d'Entreprise")
        verbose_name_plural = _("Structures d'Entreprises")
        
        
class StatutEntreprise(models.Model):
    code = models.CharField(_("Code"), max_length=255, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return self.libelle or _("Statut sans libellé")

    class Meta:
        verbose_name = _("Statut d'Entreprise")
        verbose_name_plural = _("Statuts d'Entreprises")
        



#####################################################
########### Début gestion des modèles


class BaseModele(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si le modèle est activé ou désactivée.")
    )

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.code and self.libelle else _("Modèle sans informations complètes")

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        abstract = True

class ModeleRapport(BaseModele):
    class Meta:
        verbose_name = _("Modèle de rapport")
        verbose_name_plural = _("Modèles de rapport")

class ModeleAvisCommercial(BaseModele):
    class Meta:
        verbose_name = _("Modèle d'avis commercial")
        verbose_name_plural = _("Modèles d'avis commercial")

class ModeleAlarme(BaseModele):
    class Meta:
        verbose_name = _("Modèle d'alarme")
        verbose_name_plural = _("Modèles d'alarme")

class ModeleBilan(BaseModele):
    class Meta:
        verbose_name = _("Modèle de bilan")
        verbose_name_plural = _("Modèles de bilan")

class ModeleBail(BaseModele):
    class Meta:
        verbose_name = _("Modèle de bail")
        verbose_name_plural = _("Modèles de bail")
class ModeleNotation(BaseModele):

    class Meta:
        verbose_name = _("Modèle de notation")
        verbose_name_plural = _("Modèles de notation")

class ModeleRelationEntreprise(BaseModele):
    class Meta:
        verbose_name = _("Modèle de relation entreprise")
        verbose_name_plural = _("Modèles de relation entreprise")

class ModeleInformationNotationEntreprise(BaseModele):
    class Meta:
        verbose_name = _("Modèle d'information sur notation entreprise")
        verbose_name_plural = _("Modèles d'information sur notation entreprise")

class ModeleComportementPaiement(BaseModele):
    class Meta:
        verbose_name = _("Modèle de comportement de paiement")
        verbose_name_plural = _("Modèles de comportement de paiement")

class ModeleComportementJugement(BaseModele):
    class Meta:
        verbose_name = _("Modèle de comportement de jugement")
        verbose_name_plural = _("Modèles de comportement de jugement")

#####################################################
##########Fin gestion des modèles





# === Models Acheteurs et compagnies === #



class Acheteur(models.Model):
    code = models.CharField(
        _("Code"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Code unique de l'acheteur")
    )

    categorie_entreprise = models.ForeignKey(
        'CategorieEntreprise',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Catégorie d'Entreprise"),
        help_text=_("Catégorie à laquelle appartient l'entreprise")
    )

    forme_juridique = models.ForeignKey(
        'FormeJuridique',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Forme Juridique"),
        help_text=_("Forme juridique de l'entreprise")
    )
    
    activite_principale = models.CharField(
        _("Activité principale"),
        max_length=255,
        blank=True,
        help_text=_("Activité principale de l'entreprise")
    )
    local = models.ForeignKey(
        'Local',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Local"),
        help_text=_("Type local de l'entreprise juridique de l'entreprise")
    )
    experience_paiement = models.ForeignKey(
        'ExperiencePaiement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("ExperiencePaiement"),
        help_text=_("Experience de Paiement de l'entreprise")
    )
    # Attribut pour la gestion du calcul des scorings
    TYPE_BILAN_CHOICE = [
        ('Classique', 'Classique'),
        ('Syscohada', 'Syscohada'),
        ('Anglais', 'Anglais'),
        ('Bancaire', 'Bancaire'),
    ]
    # type_bilan = models.ForeignKey(
    #     'ExperiencePaiement',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     verbose_name=_("ExperiencePaiement"),
    #     help_text=_("Experience de Paiement de l'entreprise")
    # )
    type_bilan = models.CharField(
        max_length=255, 
        choices=TYPE_BILAN_CHOICE, 
        default="Classique", 
        verbose_name=_("Type de bilan"))
    
    nom = models.CharField(
        _("Raison sociale"),
        max_length=1000,
        blank=False,
        unique=True,
        help_text=_("Nom officiel de l'entreprise")
    )

    sigle = models.CharField(
        _("Sigle"),
        max_length=255,
        blank=True,
        help_text=_("Sigle de l'entreprise")
    )

    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description de l'entreprise")
    )

    date_creation = models.DateField(
        _("Date de Création"),
        null=True,
        blank=True,
        help_text=_("Date de création de l'entreprise")
    )

    statut_entreprise = models.ForeignKey(
        'StatutEntreprise',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Statut actuel de l'entreprise"),
        help_text=_("Statut actuel de l'entreprise")
    )

    code_postal = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Code postal de l'entreprise")
    )

    fax = models.CharField(
        max_length=300,
        blank=True,
        help_text=_("Numéro de fax de l'entreprise")
    )

    boite_postale = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Boîte postale de l'entreprise")
    )

    email = models.EmailField(
        blank=True,
        help_text=_("Adresse email de l'entreprise")
    )

    site_internet = models.URLField(
        max_length=300,
        blank=True,
        help_text=_("Site internet de l'entreprise")
    )

    numero_adresse = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Numéro de l'adresse de l'entreprise")
    )

    rue_adresse = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Rue de l'adresse de l'entreprise")
    )

    pays = models.ForeignKey(
        'Pays',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name=_("Pays"),
        help_text=_("Pays où l'entreprise est située")
    )

    province = models.ForeignKey(
        'Province',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name=_("Province"),
        help_text=_("Province où l'entreprise est située")
    )

    ville = models.ForeignKey(
        'Ville',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name=_("Ville"),
        help_text=_("Ville où l'entreprise est située")
    )

    couleur_commentaire = models.ForeignKey(
        'CouleurCommentaire',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        help_text=_("Couleur du commentaire")
    )

    commentaire = models.TextField(
        blank=True,
        help_text=_("Commentaire sur l'entreprise")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
        help_text=_("Date de création de l'enregistrement")
    )

    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date de la dernière mise à jour de l'enregistrement")
    )
    # @@@@@@@@@@@@@@@ Ajouter ces codes NACE et NAFES à l'entreprise 
    # Exemple d'ajout de codes NACE à une entreprise
        #company = Company.objects.create(name="Ma Super Entreprise")
        #Récupérer des codes NACE existants
        #-nace_code_1 = NaceCode.objects.create(code="A01", description="Culture et production de produits agricoles")
        #-nace_code_2 = NaceCode.objects.create(code="C10", description="Fabrication de produits alimentaires")

        # Ajouter ces codes NACE à l'entreprise
        #company.nace_codes.add(nace_code_1, nace_code_2)
    naces_codes = models.ManyToManyField(CategoryNaceCode)  # Relation many-to-many avec les codes NACES
    nafs_codes = models.ManyToManyField(CategoryNafCode)  # Relation many-to-many avec les codes NAF
  

    class Meta:
        verbose_name = _("Acheteur")
        verbose_name_plural = _("Acheteurs")
        ordering = ['nom']
        unique_together = ('nom', 'email')

    def __str__(self):
        return self.nom

    def clean(self):
        # Ajouter des validateurs pour éviter les doublons
        if Acheteur.objects.filter(nom=self.nom).exclude(pk=self.pk).exists():
            raise ValidationError(_("Un acheteur avec ce nom existe déjà."))
        if Acheteur.objects.filter(email=self.email).exclude(pk=self.pk).exists():
            raise ValidationError(_("Un acheteur avec cet email existe déjà."))

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        super(Acheteur, self).save(*args, **kwargs)

    def generate_unique_code(self):
        # Obtenir l'année en cours
        current_year = datetime.datetime.now().year

        # Obtenir le timestamp actuel
        timestamp = int(time.time())

        # Formater le code unique
        unique_code = f"{current_year}-{timestamp}"

        return unique_code



    
##########################################################
##########################################################
# Debut Modules Yannick
##########################################################
##########################################################    
class Resume(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        null=True, blank=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur concerné par ce résumé.")
    )
    devise = models.ForeignKey(
        'Devise', 
        null=True, blank=True, 
        on_delete=models.DO_NOTHING, 
        verbose_name=_("Devise du capital social"), 
        related_name="devise_resume"
    )
    capital_social = models.DecimalField(
        max_digits=100, decimal_places=0, 
        blank=True, null=True, 
        verbose_name=_("Capital social"),
        help_text=_("Capital social de l'acheteur.")
    )
    chiffre_affaire = models.DecimalField(
        max_digits=100, decimal_places=0, 
        blank=True, null=True, 
        verbose_name=_("Chiffre d'affaire"),
        help_text=_("Chiffre d'affaire annuel de l'acheteur.")
    )
    resultat_net = models.DecimalField(
        max_digits=100, decimal_places=0, 
        blank=True, null=True, 
        verbose_name=_("Résultat net"),
        help_text=_("Résultat net après impôts.")
    )
    capitaux_propre = models.DecimalField(
        max_digits=100, decimal_places=0, 
        blank=True, null=True, 
        verbose_name=_("Capitaux propres"),
        help_text=_("Capitaux propres de l'acheteur.")
    )
    nombre_employe = models.DecimalField(
        max_digits=100, decimal_places=0, 
        blank=True, null=True, 
        verbose_name=_("Nombre d'employés"),
        help_text=_("Nombre total d'employés dans l'entreprise.")
    )
    date_creation = models.DateField(
        null=True, blank=True, 
        verbose_name=_("Date de création de l'entreprise")
    )
    couleur_commentaire = models.ForeignKey(
        'CouleurCommentaire', 
        null=True, blank=True, 
        on_delete=models.DO_NOTHING, 
        verbose_name=_("Couleur du commentaire")
    )
    commentaire = models.TextField(blank=True, verbose_name=_("Commentaire"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Dernière mise à jour"))

    class Meta:
        verbose_name = _("Résumé Financier")
        verbose_name_plural = _("Résumés Financiers")

    def __str__(self):
        return f"Résumé {self.pk} - {self.acheteur}"
    
    
class RiskRating(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        null=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur concerné par l'évaluation du risque.")
    )
    remboursabilite = models.BooleanField(default=False, verbose_name=_("Remboursabilité"))
    situation_liquidite = models.BooleanField(default=False, verbose_name=_("Situation de liquidité"))
    performance_rentabilite = models.BooleanField(default=False, verbose_name=_("Performance et rentabilité"))
    perspective_secteur = models.BooleanField(default=False, verbose_name=_("Perspective du secteur"))
    qualite_information_analyse = models.BooleanField(default=False, verbose_name=_("Qualité de l'information analysée"))
    existence_garantie = models.BooleanField(default=False, verbose_name=_("Existence de garantie"))
    terme_financier_duree_pret = models.BooleanField(default=False, verbose_name=_("Terme financier et durée du prêt"))
    mesure_propre_soutenir_credit = models.BooleanField(default=False, verbose_name=_("Mesure propre à soutenir le crédit"))
    interpretation = models.TextField(blank=True, verbose_name=_("Interprétation"))
    analyse = models.TextField(blank=True, verbose_name=_("Analyse détaillée"))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Dernière mise à jour"))

    class Meta:
        verbose_name = _("Évaluation du Risque")
        verbose_name_plural = _("Évaluations des Risques")

    def __str__(self):
        return f"RiskRating {self.pk} - {self.acheteur}"


class DonneesEnregistrement(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        null=True, blank=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    date_creation = models.DateField(null=True, blank=True, verbose_name=_("Date de création"))
    date_registre = models.DateField(null=True, blank=True, verbose_name=_("Date d'enregistrement"))
    
    # Ancien attribut avec choices
    forme_juridique = models.CharField(
        max_length=4000, 
        choices=FORMEJURIDIQUE_CHOICES, 
        default="Veuillez choisir la forme juridique",
        verbose_name=_("Forme Juridique")
    )
    
    # Nouvel attribut avec ForeignKey
    forme_juridique_ref = models.ForeignKey(
        'FormeJuridique', 
        null=True, blank=True, 
        on_delete=models.SET_NULL,
        verbose_name=_("Référence Forme Juridique")
    )
    
    numero_registre_commerce = models.CharField(max_length=50, blank=True, verbose_name=_("Numéro de registre du commerce"))
    numero_fiscale = models.CharField(max_length=100, blank=True, verbose_name=_("Numéro fiscal"))
    
    # Ancien champ avec choices
    statut_registre = models.CharField(
        max_length=4000, 
        choices=LIEN_STATUT_CHOICE, 
        default="--------",
        verbose_name=_("Statut au registre du commerce")
    )

    # Nouvel attribut avec ForeignKey
    statut_registre_ref = models.ForeignKey(
        'StatutEntreprise', 
        null=True, blank=True, 
        on_delete=models.SET_NULL,
        verbose_name=_("Référence Statut au Registre")
    )
    
    commentaire = models.TextField(blank=True, verbose_name=_("Commentaire"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Dernière mise à jour"))

    class Meta:
        verbose_name = _("Données d'Enregistrement")
        verbose_name_plural = _("Données d'Enregistrement")

    def __str__(self):
        return f"Données Enregistrement {self.pk} - {self.acheteur}"


class Tendance(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        null=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    
    # Ancien attribut avec choices
    avis_commercial = models.CharField(
        max_length=100, 
        choices=LIEN_AVIS_COMMERCIAL_CHOICE, 
        blank=True,
        verbose_name=_("Avis commercial")
    )
    
    # Nouvel attribut avec ForeignKey
    avis_commercial_ref = models.ForeignKey(
        'ModeleAvisCommercial', 
        null=True, blank=True, 
        on_delete=models.SET_NULL,
        verbose_name=_("Référence Avis Commercial")
    )
    
    presse_media = models.CharField(max_length=100, blank=True, verbose_name=_("Presse et Médias"))
    principaux_concurrent = models.TextField(blank=True, verbose_name=_("Principaux concurrents"))
    commentaire = models.TextField(blank=True, verbose_name=_("Commentaire"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Dernière mise à jour"))

    class Meta:
        verbose_name = _("Tendance")
        verbose_name_plural = _("Tendances")

    def __str__(self):
        return f"Tendance {self.pk} - {self.acheteur}"


class ResponsableAcheteur(models.Model):
    STATUS_MASCULIN = 'Masculin'
    STATUS_FEMININ = 'Feminin'
    STATUS_CHOICES = (
        (STATUS_MASCULIN, _('Masculin')),
        (STATUS_FEMININ, _('Féminin'))
    )

    acheteur = models.ForeignKey(
        'Acheteur', 
        null=True, blank=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    nom = models.CharField(_("Nom"), max_length=50, blank=True, null=True)
    prenom = models.CharField(_("Prénom"), max_length=50, blank=True, null=True)
    sexe = models.CharField(_("Sexe"), max_length=20, default=STATUS_MASCULIN, choices=STATUS_CHOICES, blank=True, null=True)
    
    poste = models.CharField(_("Poste"), max_length=100, choices=BON_POST_CHOICES_CHOICES, blank=True)
    poste_ref = models.ForeignKey(
        'PosteEntreprise', 
        null=True, blank=True, 
        on_delete=models.SET_NULL,
        verbose_name=_("Référence Poste")
    )

    nationalite = models.CharField(_("Nationalité"), max_length=100, blank=True)
    couleur_commentaire = models.ForeignKey(
        'CouleurCommentaire', 
        null=True, blank=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire")
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    class Meta:
        verbose_name = _("Responsable Acheteur")
        verbose_name_plural = _("Responsables Acheteurs")

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.acheteur})"
    
    
class AntecedantsJuridique(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        blank=True, null=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    dossier_faillite = models.CharField(_("Dossier de Faillite"), max_length=100, blank=True)
    jugement_cour = models.CharField(_("Jugement de Cour"), max_length=100, blank=True)
    antecedant_redressement = models.CharField(_("Antécédent de Redressement"), max_length=100, blank=True)
    autre = models.CharField(_("Autre"), max_length=100, blank=True)
    
    couleur_commentaire = models.ForeignKey(
        'CouleurCommentaire', 
        null=True, blank=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire")
    )
    commentaire = models.TextField(_("Commentaire"), max_length=10000000, blank=True, null=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    class Meta:
        verbose_name = _("Antécédent Juridique")
        verbose_name_plural = _("Antécédents Juridiques")

    def __str__(self):
        return f"Antécédent {self.id} - {self.acheteur}"
    
    
class RiskManagment(models.Model):
    STATUS_AUCUN = 'Aucun'
    STATUS_OUI = 'Oui'
    STATUS_NON = 'Non'
    STATUS_CHOICES = (
        (STATUS_AUCUN, _('Aucun')),
        (STATUS_OUI, _('Oui')),
        (STATUS_NON, _('Non'))
    )

    acheteur = models.ForeignKey(
        'Acheteur', 
        null=True, on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )

    professionalisme = models.CharField(_("Professionnalisme"), max_length=20, default=STATUS_AUCUN, choices=STATUS_CHOICES)
    organisation = models.CharField(_("Organisation"), max_length=20, default=STATUS_AUCUN, choices=STATUS_CHOICES)
    turn_over = models.CharField(_("Non départ des employés"), max_length=20, default=STATUS_AUCUN, choices=STATUS_CHOICES)
    greve = models.CharField(_("Non grève"), max_length=20, default=STATUS_AUCUN, choices=STATUS_CHOICES)
    degradation_qualite = models.CharField(_("Non dégradation de la qualité du travail"), max_length=20, default=STATUS_AUCUN, choices=STATUS_CHOICES)
    non_respect_condition = models.CharField(_("Respect des Employés"), max_length=20, default=STATUS_AUCUN, choices=STATUS_CHOICES)

    couleur_commentaire = models.ForeignKey(
        'CouleurCommentaire', 
        null=True, blank=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire")
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    class Meta:
        verbose_name = _("Gestion des Risques")
        verbose_name_plural = _("Gestión des Risques")

    def __str__(self):
        return f"Gestion des Risques - {self.acheteur}"
    
      
class ConseilAdministration(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        null=True, blank=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    nom = models.CharField(_("Nom"), max_length=100, default='Neant', blank=True)
    
    fonction_dans_le_conseil = models.CharField(_("Fonction dans le Conseil"), max_length=100, choices=BON_POST_CHOICES_CHOICES, blank=True)
    fonction_dans_le_conseil_ref = models.ForeignKey(
        'PosteEntreprise', 
        null=True, blank=True, 
        on_delete=models.SET_NULL,
        verbose_name=_("Référence Fonction Conseil")
    )

    numero_adresse = models.CharField(_("Numéro Adresse"), max_length=200, blank=True)
    rue_adresse = models.CharField(_("Rue Adresse"), max_length=200, blank=True)
    code_postale_adresse = models.CharField(_("Code Postal Adresse"), max_length=200, blank=True)
    
    couleur_commentaire = models.ForeignKey(
        'CouleurCommentaire', 
        null=True, blank=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire")
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    class Meta:
        verbose_name = _("Conseil d'Administration")
        verbose_name_plural = _("Conseils d'Administration")

    def __str__(self):
        return f"{self.nom} ({self.acheteur})"


class CompositionCapitalSocial(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Acheteur")
    )
    devise = models.ForeignKey(
        'Devise', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Dévise capital libéré")
    )
    emis = models.DecimalField(
        _("Capital émis"), max_digits=100, decimal_places=5, blank=True, null=True, help_text=_("Montant du capital émis")
    )
    publie = models.DecimalField(
        _("Capital publié"), max_digits=100, decimal_places=5, blank=True, null=True, help_text=_("Montant du capital publié")
    )
    libere = models.DecimalField(
        _("Capital libéré"), max_digits=100, decimal_places=5, blank=True, null=True, help_text=_("Montant du capital libéré")
    )
    couleur_commentaire = models.ForeignKey(
        'CouleurCommentaire', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Couleur du commentaire")
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"Capital Social ({self.acheteur})" if self.acheteur else _("Composition Capital Social")

    class Meta:
        verbose_name = _("Composition du Capital Social")
        verbose_name_plural = _("Compositions du Capital Social")


class CompositionAction(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Acheteur")
    )
    nom = models.CharField(_("Nom"), max_length=200, blank=True)
    prenom = models.CharField(_("Prénom"), max_length=200, blank=True)
    pourcentage = models.DecimalField(
        _("Pourcentage"), max_digits=100, decimal_places=5, blank=True, null=True, help_text=_("Pourcentage de détention d'actions")
    )
    couleur_commentaire = models.ForeignKey(
        'CouleurCommentaire', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Couleur du commentaire")
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.nom} {self.prenom} - {self.pourcentage}%" if self.nom else _("Composition Action")

    class Meta:
        verbose_name = _("Composition de l'Actionnariat")
        verbose_name_plural = _("Compositions de l'Actionnariat")
        
        
        
class OpinionCreditAcremac(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    risque_de_defaut = models.IntegerField(
        default=0, 
        verbose_name=_("Risque de défaut")
    )
    risque_de_concentration_credit = models.IntegerField(
        default=0, 
        verbose_name=_("Risque de concentration de crédit")
    )
    risque_de_reputation = models.IntegerField(
        default=0, 
        verbose_name=_("Risque de réputation")
    )
    risque_pays = models.IntegerField(
        default=0, 
        verbose_name=_("Risque pays")
    )
    risque_de_taux_dinteret = models.IntegerField(
        default=0, 
        verbose_name=_("Risque de taux d'intérêt")
    )
    risque_de_liquidite = models.IntegerField(
        default=0, 
        verbose_name=_("Risque de liquidité")
    )
    risque_eleve = models.IntegerField(
        default=0, 
        verbose_name=_("Risque élevé")
    )
    risque_moyen = models.IntegerField(
        default=0, 
        verbose_name=_("Risque moyen")
    )
    risque_faible = models.IntegerField(
        default=0, 
        verbose_name=_("Risque faible")
    )
    couleur_commentaire = models.ForeignKey(
        'CouleurCommentaire', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Couleur du commentaire")
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    def __str__(self):
        return f"Opinion Credit Acremac for {self.acheteur}"

    class Meta:
        verbose_name = _("Opinion Credit Acremac")
        verbose_name_plural = _("Opinions Credit Acremac")



##########################################################
##########################################################
# Fin Modules Yannick
##########################################################
##########################################################


##########################################################
##########################################################
# Debut Modules KBZ
##########################################################
##########################################################

#------------------- Module filiale ou branche
class Structure(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Acheteur")
    )
    nom = models.CharField(_("Nom"), max_length=200, blank=True)
    
    type_affiliation =  models.CharField(max_length=100,choices=LIEN_ENTREPRISE_CHOICE, blank=True, verbose_name=_("Type d'affiliation"))
    type_affiliation_ref = models.ForeignKey(
        'StructureEntreprise', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Référence Type d'affiliation")
    )
    numero_adresse = models.CharField(_("Numéro adresse"), max_length=200, blank=True)
    rue_adresse = models.CharField(_("Rue adresse"), max_length=200, blank=True)
    code_postale_adresse = models.CharField(_("Code postal adresse"), max_length=200, blank=True)
    couleur_commentaire = models.ForeignKey(
        'CouleurCommentaire', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Couleur du commentaire")
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return self.nom or _("Filiale sans nom")

    class Meta:
        verbose_name = _("Filiale ou Branche")
        verbose_name_plural = _("Filiales ou Branches")


class AnalyseSectorielle(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Acheteur")
    )
    couleur_commentaire = models.ForeignKey(
        'CouleurCommentaire', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Couleur du commentaire")
    )
    commentaire = models.TextField(_("Commentaire"), max_length=10000000, blank=True)
    impact_covid_19 = models.TextField(_("Impact COVID-19"), max_length=10000000, blank=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return _("Analyse sectorielle")

    class Meta:
        verbose_name = _("Analyse Sectorielle")
        verbose_name_plural = _("Analyses Sectorielles")



class CompteFinancier(models.Model):
    
    XAF = 'XAF'
    XOF = 'XOF'
    EUR = 'EUR'
    USD = 'USD'
    CHF = 'CHF'
    
    STATUS_CHANGE = (
        (XAF, 'XAF'),
        (XOF, 'XOF'),
        (EUR, 'EUR'),
        (USD, 'USD'),
        (CHF, 'CHF'),
    )

    acheteur = models.ForeignKey('Acheteur', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Acheteur"))
    cabinet = models.CharField(max_length=200, blank=True, verbose_name=_("Cabinet"))
    requis_pour_deposer = models.CharField(max_length=200, blank=True, verbose_name=_("Requis pour déposer"))
    credibilite_cabinet = models.CharField(max_length=200, blank=True, choices=STATUS__OUI_NON, verbose_name=_("Crédibilité du cabinet pour ACREMAC"))
    source = models.CharField(max_length=200, blank=True, verbose_name=_("Source"))
    presentation = models.CharField(max_length=200, blank=True, verbose_name=_("Présentation"))
    
    date_compte = models.DateField(blank=True, verbose_name=_("Début de période de compte N"))
    date_fin = models.DateField(blank=True, null=True, verbose_name=_("Fin clôture de compte N"))
    date_compte_n_moins_un = models.DateField(blank=True, null=True, verbose_name=_("Début de période de compte N-1"))
    date_fin_n_moins_un = models.DateField(blank=True, null=True, verbose_name=_("Fin clôture de compte N-1"))
    date_compte_n_moins_deux = models.DateField(blank=True, null=True, verbose_name=_("Début de période de compte N-2"))
    date_fin_n_moins_deux = models.DateField(blank=True, null=True, verbose_name=_("Fin clôture de compte N-2"))
    
    type_compte = models.CharField(max_length=200, null=True, blank=True, verbose_name=_("Type de compte"))
    devise = models.CharField(max_length=20, default=XAF, choices=STATUS_CHANGE, blank=True, verbose_name=_("Devise"))
    type_bilan = models.CharField(max_length=255, choices=LIEN_TYPE_BILAN_CHOICE, default="--------", verbose_name=_("Type de bilan"))
    type_bilan_ref = models.ForeignKey(
        'ModeleBilan', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Référence Type de bilan")
    )
    
    couleur_commentaire = models.ForeignKey('CouleurCommentaire', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Couleur du commentaire"))
    commentaire = models.TextField(blank=True, max_length=10000000, verbose_name=_("Commentaire"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    def __str__(self):
        return f"{self.acheteur} - {self.cabinet}" if self.acheteur else _("Compte Financier")

    class Meta:
        verbose_name = _("Compte Financier")
        verbose_name_plural = _("Comptes Financiers")


class OperationEtHistorique(models.Model):
    acheteur = models.ForeignKey('Acheteur', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Acheteur"))
    commentaire_ratios = models.TextField(blank=True, verbose_name=_("Commentaire sur les ratios"))
    description_complete_activite = models.TextField(blank=True, verbose_name=_("Description complète de l'activité"))
    importation = models.TextField(blank=True, verbose_name=_("Importation"))
    historique = models.TextField(blank=True, verbose_name=_("Historique"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    def __str__(self):
        return f"{self.acheteur} - {self.description_complete_activite[:50]}..." if self.acheteur else _("Opération et Historique")

    class Meta:
        verbose_name = _("Opération et Historique")
        verbose_name_plural = _("Opérations et Historiques")


class ProprieteEtActif(models.Model):
    acheteur = models.ForeignKey('Acheteur', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Acheteur"))
    locaux = models.CharField(max_length=255, choices=LIEN_COMPORTEMENT_PREMISES_CHOICE, blank=True, verbose_name=_("Locaux"))
    locaux_ref = models.ForeignKey(
        'ModeleBail', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Référence sur les locaux")
    )
    
    branche = models.CharField(max_length=255, blank=True, verbose_name=_("Branche"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    def __str__(self):
        return f"{self.acheteur} - {self.branche}" if self.acheteur else _("Propriété et Actif")

    class Meta:
        verbose_name = _("Propriété et Actif")
        verbose_name_plural = _("Propriétés et Actifs")



class ConditionAchat(models.Model):
    acheteur = models.ForeignKey('Acheteur', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Acheteur"))
    local = models.CharField(max_length=255, blank=True, verbose_name=_("Local"))
    importation = models.TextField(blank=True, verbose_name=_("Importation"))
    les_clients = models.TextField(blank=True, verbose_name=_("Les clients"))
    fournisseur = models.TextField(blank=True, verbose_name=_("Fournisseur"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    def __str__(self):
        return f"{self.acheteur} - {self.local}" if self.acheteur else _("Condition d'Achat")

    class Meta:
        verbose_name = _("Condition d'Achat")
        verbose_name_plural = _("Conditions d'Achat")



class ConditionDeVente(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        null=True, 
        blank=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    local = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name=_("Local")
    )
    recouvrement_de_dette_jugement = models.CharField(
        max_length=255, 
        choices=LIEN_COMPORTEMENT_JUGEMENT_CHOICE, 
        default="--------",
        verbose_name=_("Recouvrement de dette jugement")
    )
    comportement_de_paiement = models.CharField(
        max_length=255, 
        choices=LIEN_COMPORTEMENT_PAIEMENT_CHOICE, 
        default="--------",
        verbose_name=_("Comportement de paiement")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    def __str__(self):
        return f"Condition de vente for {self.acheteur} - {self.local}"

    class Meta:
        verbose_name = _("Condition de Vente")
        verbose_name_plural = _("Conditions de Vente")


class SommaireEtAvis(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        null=True, 
        blank=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    couleur_commentaire = models.ForeignKey(
        'CouleurCommentaire', 
        null=True, 
        blank=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire")
    )
    commentaire = models.TextField(
        max_length=10000000, 
        blank=True, 
        verbose_name=_("Commentaire")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    def __str__(self):
        return f"Sommaire et avis for {self.acheteur}"

    class Meta:
        verbose_name = _("Sommaire et Avis")
        verbose_name_plural = _("Sommaires et Avis")


class Advice(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    points_forts = models.TextField(
        max_length=10000000, 
        blank=True, 
        verbose_name=_("Points forts")
    )
    points_faibles = models.TextField(
        max_length=10000000, 
        blank=True, 
        verbose_name=_("Points faibles")
    )
    dynamisme_court_terme = models.TextField(
        max_length=10000000, 
        blank=True, 
        verbose_name=_("Dynamisme à court terme")
    )
    dynamisme_long_terme = models.TextField(
        max_length=10000000, 
        blank=True, 
        verbose_name=_("Dynamisme à long terme")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    def __str__(self):
        return f"Advice for {self.acheteur}"

    class Meta:
        verbose_name = _("Advice")
        verbose_name_plural = _("Advices")


class Geopolitics(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    donnees_politiques = models.TextField(
        max_length=10000000, 
        blank=True, 
        verbose_name=_("Données politiques")
    )
    donnees_economiques = models.TextField(
        max_length=10000000, 
        blank=True, 
        verbose_name=_("Données économiques")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    def __str__(self):
        return f"Geopolitics for {self.acheteur}"

    class Meta:
        verbose_name = _("Geopolitique")
        verbose_name_plural = _("Géopolitiques")



class Banquier(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        null=True, 
        blank=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    nom_banque = models.CharField(
        blank=True, 
        max_length=200,
        verbose_name=_("Nom de la banque")
    )
    numero_compte = models.CharField(
        default="", 
        max_length=500, 
        blank=True, 
        null=True,
        verbose_name=_("Numéro de compte")
    )
    type_relation = models.CharField(
        blank=True, 
        max_length=200, 
        null=True,
        verbose_name=_("Type de relation")
    )
    numero = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name=_("Numéro")
    )
    rue = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name=_("Rue")
    )
    ville = models.ForeignKey(
        'Ville', 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Ville")
    )
    code_postal = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name=_("Code postal")
    )
    couleur_commentaire = models.ForeignKey(
        'CouleurCommentaire', 
        null=True, 
        blank=True, 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire")
    )
    commentaire = models.TextField(
        blank=True,
        verbose_name=_("Commentaire")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name=_("Date de mise à jour")
    )

    def __str__(self):
        return self.nom_banque

    class Meta:
        verbose_name = _("Donnée bancaire")
        verbose_name_plural = _("Données bancaires")


##########################################################
##########################################################
# Fin Modules KBZ
##########################################################
##########################################################


##########################################################
##########################################################
#  Modules Additif
##########################################################
##########################################################
# ----Gestions des logos des acheteurs
class Logo(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    image = models.ImageField(upload_to='logos/')
    description = models.CharField(max_length=255, blank=True, null=True)
    #date_uploaded = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    def __str__(self):
        return f"Logo for {self.acheteur}"

    class Meta:
        verbose_name = _("Logo")
        verbose_name_plural = _("Logos")
# ----Gestions des numéros de téléphones des acheteurs V3
"""
class TelephonesAcheteur(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    country = CountryField()  # Sélection du pays
    phone_number = PhoneNumberField( null=True, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    #phone_number = PhoneNumberField(region="US")
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    def __str__(self):
        return f'{self.description} - {self.phone_number}'
    class Meta:
        verbose_name = _("Téléphone")
        verbose_name_plural = _("Téléphones")
 """
#Telephone Acheteur V2
class TelephoneAcheteur(models.Model):
    #_safedelete_policy = SOFT_DELETE_CASCADE
    telephone = models.TextField(max_length=100, verbose_name=_("Téléphone"))
    acheteur = models.ForeignKey('Acheteur', null=True, blank=True, on_delete=models.DO_NOTHING)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='telephone_user_update', null=True, blank=True,
                                   on_delete=models.DO_NOTHING)
# ----Gestions des différents emails des acheteurs V3
"""
class EmailsAcheteur(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    #country = CountryField()  # Sélection du pays
    email = PhoneNumberField( null=True, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    #phone_number = PhoneNumberField(region="US")
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    def __str__(self):
        return f'{self.description} - {self.email}'
    class Meta:
        verbose_name = _("Email")
        verbose_name_plural = _("Emails")
"""
class PortableAcheteur(models.Model): #V2
   # _safedelete_policy = SOFT_DELETE_CASCADE
    portable = models.TextField(max_length=100, verbose_name=_("Portable"))
    acheteur = models.ForeignKey('Acheteur', null=True, blank=True, on_delete=models.DO_NOTHING)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='portable_user_update', null=True, blank=True,
                                   on_delete=models.DO_NOTHING)

    #history = HistoricalRecords()

class EmailAcheteur(models.Model):
    #_safedelete_policy = SOFT_DELETE_CASCADE
    email = models.TextField(max_length=10000000, verbose_name=_("Adresse email"))
    acheteur = models.ForeignKey('Acheteur', null=True, blank=True, on_delete=models.DO_NOTHING)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='email_user_update', null=True, blank=True,
                                   on_delete=models.DO_NOTHING)

    #history = HistoricalRecords()

#------ DOCUMENT
class Document(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='documents',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au document")
    )
    titre = models.CharField(
        _("Titre"),
        max_length=255,
        help_text=_("Titre du document")
    )
    fichier = models.FileField(
        _("Fichier"),
        upload_to='documents/',
        help_text=_("Fichier du document")
    )
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description du document")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    def __str__(self):
        return f"{self.titre} - {self.acheteur.nom}"



#--------- SWOT
class SWOTAnalysis(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='swot',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé à l'analyse SWOT")
    )
    force = models.TextField(
        _("Force"),
        null=True,
        blank=True,
        help_text=_("Forces de l'entreprise")
    )
    faiblesse = models.TextField(
        _("Faiblesse"),
        null=True,
        blank=True,
        help_text=_("Faiblesses de l'entreprise")
    )
    opportunite = models.TextField(
        _("Opportunité"),
        null=True,
        blank=True,
        help_text=_("Opportunités de l'entreprise")
    )
    menace = models.TextField(
        _("Menace"),
        null=True,
        blank=True,
        help_text=_("Menaces de l'entreprise")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    class Meta:
        verbose_name = _("SWOT")
        verbose_name_plural = _("SWOT")

    def __str__(self):
        return f"SWOT Analysis de {self.acheteur.nom}"

class TypeProcedureCollective(models.Model):
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.libelle} - {self.libelle}" if self.libelle else _("Type de procédure sans libellé")

    class Meta:
        verbose_name = _("Type de procédure collective ")
        verbose_name_plural = _("Type de procédures collectives")
        ordering = ["libelle"]

#----- PROCEDURE COLLECTIVE
class ProcedureCollective(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='procedures_collectives',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé à la procédure collective")
    )
    type_procedure = models.CharField(
        _("Type de procédure"),
        max_length=255,
        help_text=_("Type de procédure collective")
    )
    # Nouvel attribut avec ForeignKey
    type_procedure_ref = models.ForeignKey(
        'TypeProcedureCollective', 
        null=True, blank=True, 
        on_delete=models.SET_NULL,
        verbose_name=_("Référence Type de procédure collective")
    )
    
    statut = models.CharField(max_length=50, 
                              choices=[
                                  ('Non débutée', 'Non débutée'),
                                    ('En cours', 'En cours'),
                                     ('Terminé', 'Terminé')
                                  ])
    date_ouverture = models.DateField(
        _("Date d'ouverture"),
        null=True,
        blank=True,
        help_text=_("Date d'ouverture de la procédure")
    )
    deadline = models.DateField(
        _("Deadline de la procédure"),
        null=True,
        blank=True,
        help_text=_("Date d'ouverture de la procédure")
    )
    date_cloture = models.DateField(
        _("Date de clôture"),
        null=True,
        blank=True,
        help_text=_("Date de clôture de la procédure")
    )
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description de la procédure collective")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    class Meta:
        verbose_name = _("Procédure Collective")
        verbose_name_plural = _("Procédures Collectives")

    def __str__(self):
        return f"{self.type_procedure} - {self.acheteur.nom}"



#------------- REGISTRE COMMERCE
class RegistreCommerce(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='registre_commerce',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au registre de commerce")
    )
    numero = models.CharField(
        _("Numéro de registre de commerce"),
        max_length=255,
        help_text=_("Numéro de registre de commerce de l'entreprise")
    )
    date_inscription = models.DateField(
        _("Date d'inscription"),
        null=True,
        blank=True,
        help_text=_("Date d'inscription au registre de commerce")
    )
    description = models.TextField(
        max_length=10000000, 
        blank=True, 
        verbose_name=_("Description")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    class Meta:
        verbose_name = _("Registre de Commerce")
        verbose_name_plural = _("Registres de Commerce")

    def __str__(self):
        return f"Registre de commerce de {self.acheteur.nom}"

#-------------- COTISATION SOCIALE
class Cotisations(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='cnss',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au numéro de sécurité sociale")
    )
    libelle = models.CharField(
        _("Titre"),
        max_length=255,
        help_text=_("libelle de la cotisation")
    )
    numero = models.CharField(
        _("Numéro de sécurité sociale"),
        max_length=255,
        help_text=_("Numéro de la cotisation de l'entreprise")
    )
    date_affiliation = models.DateField(
        _("Date d'affiliation"),
        null=True,
        blank=True,
        help_text=_("Date d'affiliation à la sécurité sociale")
    )
   
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    class Meta:
        verbose_name = _("CNSS")
        verbose_name_plural = _("CNSS")

    def __str__(self):
        return f"Cotisations de {self.acheteur.nom}"

#-------------- PRODUITS et SERVICES
class ProduitServices(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='produitService',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au produit ou service")
    )
    libelle = models.CharField(
        _("Titre"),
        max_length=255,
        help_text=_("libelle du produit ou service")
    )
    stock_duree = models.PositiveIntegerField(
        _("Stock ou duréé"),
        help_text=_("Stock ou durée")
    )
    prix = models.DecimalField(
        _("Prix"),
        max_digits=15, 
        decimal_places=2,
        blank=True, 
        null=True)  # Prix du produit et service 
    
    # prix = models.DecimalField(
    #     _("Prix"),
    #     null=True,
    #     blank=True,
    #     help_text=_(" Prix du produit ou service")
    # )
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description du produit/service")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    class Meta:
        verbose_name = _("ProduitService")
        verbose_name_plural = _("ProduitService")

    def __str__(self):
        return f"Cotisations de {self.acheteur.nom}"

class Marque(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='Marque',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé à la marque")
    )
    nom = models.CharField(
       _("nom"),
        max_length=255,
        help_text=_("nom de la marque")
        )
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='marques/', blank=True, null=True)
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    def __str__(self):
        return self.nom

#------------- NUMERO IDENTIFICATION FISCAL
# class NumeroIdentificationFiscale(models.Model):
#     acheteur = models.ForeignKey(
#         'Acheteur',
#         on_delete=models.DO_NOTHING,
#         null=True, 
#         blank=True, 
#         related_name='numero_identification_fiscale',
#         verbose_name=_("Acheteur"),
#         help_text=_("Acheteur associé au numéro d'identification fiscale")
#     )
#     numero = models.CharField(
#         _("Numéro d'identification fiscale"),
#         max_length=255,
#         help_text=_("Numéro d'identification fiscale de l'entreprise")
#     )

#     created_at = models.DateTimeField(
#         auto_now_add=True,
#         verbose_name=_("Date de création")
#     )
#     updated_at = models.DateTimeField(
#         auto_now=True,
#         verbose_name=_("Date de mise à jour")
#     )

#     class Meta:
#         verbose_name = _("Numéro d'Identification Fiscale")
#         verbose_name_plural = _("Numéros d'Identification Fiscale")

#     def __str__(self):
#         return f"Numéro d'identification fiscale de {self.acheteur.nom}"



#------------------- NUMERO IDENTIFICATION UNIQUE
# class NumeroIdentificationUnique(models.Model):
#     acheteur = models.ForeignKey(
#         'Acheteur',
#         on_delete=models.DO_NOTHING,
#         null=True, 
#         blank=True, 
#         related_name='numero_identification_unique',
#         verbose_name=_("Acheteur"),
#         help_text=_("Acheteur associé au numéro d'identification unique")
#     )
#     numero = models.CharField(
#         _("Numéro d'identification unique"),
#         max_length=255,
#         help_text=_("Numéro d'identification unique de l'entreprise")
#     )

#     created_at = models.DateTimeField(
#         auto_now_add=True,
#         verbose_name=_("Date de création")
#     )
#     updated_at = models.DateTimeField(
#         auto_now=True,
#         verbose_name=_("Date de mise à jour")
#     )

#     class Meta:
#         verbose_name = _("Numéro d'Identification Unique")
#         verbose_name_plural = _("Numéros d'Identification Unique")

#     def __str__(self):
#         return f"Numéro d'identification unique de {self.acheteur.nom}"

##########################################################
##########################################################
# Fin Modules Additif
##########################################################
##########################################################
# === Models Commandes client === #



##########################################################
##########################################################
# Debut Modules Bilan Classique
##########################################################
##########################################################

class ActifC(models.Model):
    annee = models.ForeignKey(
        'Annee',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile")
    )
    acheteur = models.ForeignKey(
        'Acheteur',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )

    TYPE_BILAN = [
        ('annuel', 'Annuel'),
        ('semestriel', 'Semestriel'),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_BILAN,
        default='annuel',
        help_text=_("Type de l'actif")
    )
    #Capital Souscrit Non versé 
    capital_souscrit_non_app = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Capital sousc. non app"))
    
    #Immobilisations incorporelles
    frais_recherche_developpement = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Frais recherche developpement"))
    brevet_licence_logiciels = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Brevet licence logiciels"))
    fonds_commercial = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Fonds commercial"))
    autres_immobilisations_incorporelles = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres immobilisations incorporelles"))

    #Immobilisations icorporelles
    terrains = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Terrains"))
    constructions = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Constructions"))
    materiels_et_outils = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Materiels et outils"))
    materiel_de_transport = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Materiel de transport"))
    autres_immos_corp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres immos corp"))
    immos_en_cours = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Immos en cours"))
    avances_et_acptes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Avances et acptes"))
    
    #Elements financiers
    participations = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Participations"))
    prets = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Prets"))
    autres = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres"))

    #stocks
    Actif_circuilant_hors_exploitation = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Actif circuilant hors exploitation"))
    stocks_mp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Stocks matière première"))
    stocks_encours_mp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Stocks encours matière première "))
    stocks_pf = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Stocks produits finis"))
    stocks_encours_pf = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Stocks encours produits finis"))
    stocks_encours_services = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Stocks encours services"))
    stocks_mses = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Stocks marchandises"))

    #Créances et emplois assimilés
    avances_acptes_verses = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Avances acptes verses"))
    clients_et_cptes_rattaches = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Clients et cptes rattaches"))
    autres_creances = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres creances"))

    #Trésorerie actif
    valeurs_a_encaisser = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Valeurs a encaisser"))
    banques_cheques_postaux_caisse = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Banques cheques postaux caisse"))

    #Comptes de REGULARISATION
    cca = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Cca"))
    charges_a_repartir_et_frais_etablissement = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Charges a repartir et frais etablissement"))
    primes_de_rbt = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Primes de rembourssement"))
    eca = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Ecart de conversion actif"))


    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ATTRIBUT Revoir (INEXISTANT DANS LE FICHIER)

    eene = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Eene"))
    effectif = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Effectif"))
    amortissements = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Amortissements"))
    provisions_stocks = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provisions stocks"))
    provisions_creances = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provisions creances"))
    provisions_vmp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provisions vmp"))
   
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! FIN ATTRIBUT A REVOIR

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='actif_classique_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return _("Actif bilan classique : ") + str(self.id) + ". " + str(self.acheteur) + " (" + str(self.annee) + ")"
    
    
    #Sommes Immobilisations incorporelles
    def elements_incorporels(self):
        o = Decimal(0.0)
        return ((self.frais_recherche_developpement or o) +
                (self.brevet_licence_logiciels or o) +
                (self.fonds_commercial or o) +
                (self.autres_immobilisations_incorporelles or o))
    
    #Sommes Immobilisations corporelles
    def elements_corporels(self):
        o = Decimal(0.0)
        return ((self.terrains or o) +
                (self.constructions or o) +
                (self.materiels_et_outils or o) +
                (self.materiel_de_transport or o) +
                (self.autres_immos_corp or o) +
                (self.immos_en_cours or o) +
                (self.avances_et_acptes or o))
    
    #Sommes Elements financiers
    def elements_financiers(self):
        o = Decimal(0.0)
        return ((self.participations or o) +
                (self.prets or o) +
                (self.autres or o))

    #TOTAL I
    def total_I(self):
        return (self.elements_corporels() +
                self.elements_incorporels() +
                self.elements_financiers())
    #STOCK
    def stocks(self):
        o = Decimal(0.0)
        return ((self.stocks_mp or o) +
                (self.stocks_encours_mp or o) +
                (self.stocks_pf or o) +
                (self.stocks_encours_pf or o) +
                (self.stocks_encours_services or o) +
                (self.stocks_mses or o))

    #Créances et emplois assimilés
    def creances(self):
        o = Decimal(0.0)
        return ((self.avances_acptes_verses or o) +
                (self.clients_et_cptes_rattaches or o) +
                (self.autres_creances or o))

    #Trésorerie actif
    def disponibilites_vmp(self):
        o = Decimal(0.0)
        return ((self.valeurs_a_encaisser or o) + (self.banques_cheques_postaux_caisse or o))

    #TOTAL II
    def total_II(self):
        return (self.stocks() + self.creances() + self.disponibilites_vmp())

    #Compte de REGULARISATION
    def compte_regul(self):
        o = Decimal(0.0)
        return ((self.cca or o) +
                (self.charges_a_repartir_et_frais_etablissement or o) +
                (self.primes_de_rbt or o) +
                (self.eca or o))

    #TOTAL III
    def total_III(self):
        return self.compte_regul()

    #Total GENERAL
    def general_total(self):
        o = Decimal(0.0)
        return ((self.total_III() or o) +
                (self.total_II() or o) +
                (self.total_I() or o) +
                (self.capital_souscrit_non_app or o))
    class Meta:
        verbose_name = _("Actif bilan classique")
        verbose_name_plural = _("Actifs bilans classiques")
        
    
    
class PassifC(models.Model):
    annee = models.ForeignKey(
        'Annee',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile")
    )
    acheteur = models.ForeignKey(
        'Acheteur',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )

    TYPE_BILAN = [
        ('annuel', 'Annuel'),
        ('semestriel', 'Semestriel'),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_BILAN,
        default='annuel',
        help_text=_("Type du passif")
    )

    #CAPITAUX PROPRES
    capital_social = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Capital social"))
    primes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Primes"))
    ecarts_de_reevaluation = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Eca"))
    reserve = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Reserve indisponibles "))
    reserve_libre = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Reserve Libres"))
    report_a_nouveau = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Report a nouveau"))
    resultat_exercice = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Resultat exercice"))
    subv_invest = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Subventions investies"))
    provision_regl = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provision regle"))

    #DETTES FINANCIERES ET RESSOURCE CONNEXES
    emprunts = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Emprunts"))
    dette_credit_bail_contrat_assimile = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Credit lease debts and related contracts"))
    dettes_financiere_diverses = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dettes financiere diverses"))
    provision_financiere_risque_charge = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provision financiere risque charge"))

    #PASSIFS COURANTS
    dettes_fournisseurs_divers = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dettes fournisseurs divers"))
    avance_et_acomptes_recu = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Avance et acomptes recu"))
    dettes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dettes circulantes Hors Exploitation"))
    dettes_fiscales_sociales = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dettes fiscales sociales"))
    provision_risk_court_terme = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provisions pour risques à court terme"))
    autres_dettes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres dettes"))

    #TRESORERIE PASSIF
    banques_credit_escompte = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Banques credit escompte"))
    banque_credit_caisse = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Banque credit caisse"))
    banques_decouvert = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Banques decouvert"))

    ecart_conversion_passif = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Ecart conversion passif"))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='passif_classique_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return _("Passif bilan classique : ") + str(self.id) + ". " + str(self.acheteur) + " (" + str(self.annee) + ")"

    #TOTAL I
    def total_I(self):
        o = Decimal(0.0)
        return ((self.capital_social or o) + (self.primes or o) + (self.ecarts_de_reevaluation or o) +
                (self.reserve or o) + (self.report_a_nouveau or o) + (self.resultat_exercice or o) +
                (self.subv_invest or o) + (self.provision_regl or o))

    #TOTAL II
    def total_II(self):
        o = Decimal(0.0)
        return ((self.emprunts or o) + (self.dette_credit_bail_contrat_assimile or o) + (
                    self.dettes_financiere_diverses or o) + (self.provision_financiere_risque_charge or o))

    #TOTAL I_II
    def total_I_II(self):
        return (self.total_I() + self.total_II())

    #TOTAL III
    def total_III(self):
        o = Decimal(0.0)
        return ((self.dettes_fournisseurs_divers or o) + (self.avance_et_acomptes_recu or o) +
                (self.dettes or o) + (self.dettes_fiscales_sociales or o) + (self.autres_dettes or o))

    def total_IV(self):
        o = Decimal(0.0)
        return ((self.banques_credit_escompte or o) + (self.banque_credit_caisse or o) + (self.banques_decouvert or o))

    def total_general(self):
        o = Decimal(0.0)
        return ((self.ecart_conversion_passif or o) + self.total_I_II() + self.total_III() + self.total_IV())

    class Meta:
        verbose_name = _("Passif bilan classique")
        verbose_name_plural = _("Passifs bilans classiques")
        
        
    #  Liste des methodes utiles pour ce model
    
    #  total_I
    #  total_II
    #  total_III
    #  total_IV
    #  total_general
    
    
class ResultatC(models.Model):
    annee = models.ForeignKey(
        'Annee',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile")
    )
    acheteur = models.ForeignKey(
        'Acheteur',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )

    TYPE_BILAN = [
        ('annuel', 'Annuel'),
        ('semestriel', 'Semestriel'),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_BILAN,
        default='annuel',
        help_text=_("Type du résultat")
    )
    #Poduits d'exploitation
    vente_de_mdses = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Vente de mdses"))
    ventes_de_produits_fabriques = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Ventes de produits fabriques"))
    travaux_services_vendus = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Travaux services vendus"))
    produit_accessoires = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Produit accessoires"))
    production_imblise = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Production imblise"))

    #Autres produits d'exploitations
    subventions_exploitations = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Subventions exploitations"))
    #!!!!!!!!!!!!!!!!!! Absent dans le fichier
    production_stockee = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Production stockee"))
    reprises_de_provision = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Reprises de provision"))
    transferts_charges = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Transferts charges"))
    autres_produits = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres produits"))

    #Marge brute
    achat_mdses = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Achat mdses"))
    variation_stock_mdses = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Variation stock mdses"))

    #Valeur ajoutée
    achat_mp_autres_appro = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Achat mp autres appro"))
    var_stk_mp_app = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Var stk mp app"))
    autres_achats = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres achats"))
    variation_de_stocks_autres_appro = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Variation de stocks autres appro"))
    transports = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Transports"))
    services_ext = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Services ext"))
    impots_taxes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Impots taxes"))
    autres_charges_valeur_ajoutee = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres charges valeur ajoutee"))

    #Excédent bruit d'exploitation
    charges_personnel = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Charges personnel"))

    #RESULTAT D'EXPLOITATION
    dotation_aux_amorts = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dotation aux amorts"))
    dotation_aux_provisions = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dotation aux provisions"))
    #!!!!!!!!!!!!!!!!!!!! Absent dans le fichier
    autres_charges_excedent_brute = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres charges excedent brute"))

    #Prdouits financiers
    revenus_fin_assimiles = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Revenus fin assimiles"))
    prof_vmp_et_cre_actif_immo = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Prof vmp et cre actif immo"))
    interets_produit_assim = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Interets produit assim"))
    reprise_prov_et_transfert = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Reprise prov et transfert"))
    diff_positive_de_change = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Diff positive de change"))
    prod_nets_cessions_vmp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Prod nets cessions vmp"))

    #Charges financières
    dap = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dot. aux prov. & depreciations"))
    frais_fin_charges_assi = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Frais fin. & chrges assimilées"))
    diff_negatives_de_change = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Diff negatives de change"))
    ch_nettes_cessions_vmp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Ch nettes cessions vmp"))

    #Produits exceptionnels
    sur_op_gestion_prod_except = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Sur op gestion prod except"))
    sur_op_en_capital_prod_except = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Sur op en capital prod except"))
    reprise_prov_transfert = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Reprise prov transfert"))

    #Charges exceptionnelles
    sur_op_gestion_charg_except = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Sur op gestion charg except"))
    sur_op_en_capital_charg_except = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Sur op en capital charg except"))
    dap_et_transfert_charg_except = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dap et transfert charg except"))
    
    participation_salairies = models.DecimalField(_("Participations des salariés"), max_digits=100, decimal_places=2, null=True, blank=True)
    impot_sur_benefices = models.DecimalField(_("Impôts sur les bénéfices"), max_digits=100, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='resultat_classique_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return _("Résultat bilan classique : ") + str(self.id) + ". " + str(self.acheteur) + " (" + str(self.annee) + ")"

    #Chiffes d'affaires
    def ca(self):
        o = Decimal(0.0)
        return ((self.vente_de_mdses or o) + (self.ventes_de_produits_fabriques or o) +
                (self.travaux_services_vendus or o) + (self.produit_accessoires or o))

    def total_I(self):
        o = Decimal(0.0)
        return ((self.production_stockee or o) + (self.production_imblise or o) +
                (self.subventions_exploitations or o) + (self.reprises_de_provision or o) +
                (self.transferts_charges or o) + (self.autres_produits or o))

    def marge_brute(self):
        o = Decimal(0.0)
        return ((self.vente_de_mdses or o) - (self.achat_mdses or o) - (self.variation_stock_mdses or o))

    #!!!!!!!!!!!!!!!!!!!! FORMULE DE CALCUL (VOIR FICHIER EXCEL)
    def valeur_ajoutee(self):
        o = Decimal(0.0)
        return (self.ca() - (self.achat_mdses or o) - (self.variation_stock_mdses or o)
                -(self.achat_mp_autres_appro or o)-(self.var_stk_mp_app or o)-(self.autres_achats or o)
                -(self.variation_de_stocks_autres_appro or o) - (self.transports or o)
                -(self.services_ext or o) - (self.impots_taxes or o)-(self.autres_charges_valeur_ajoutee or o)
                +(self.total_I())
                )

    #Excédent brut d'exploitation
    def excedent_brut_ex(self):
        o = Decimal(0.0)
        return (self.valeur_ajoutee() - (self.charges_personnel or o))

    #!!!!!!!!!!!!!!!!FORMULE A REVOIR (ABSCENCE DES SOMMES DES ELEMENTS DU TOTAL I)
    def resultat_exploitation(self):
        o = Decimal(0.0)
        return (self.excedent_brut_ex() - (self.dotation_aux_amorts or o) - (self.dotation_aux_provisions or o) )

    def financier_total_I(self):
        o = Decimal(0.0)
        return ((self.revenus_fin_assimiles or o) + (self.prof_vmp_et_cre_actif_immo or o) +
                (self.interets_produit_assim or o) + (self.reprise_prov_et_transfert or o) +
                (self.diff_positive_de_change or o) + (self.prod_nets_cessions_vmp or o))

    def financier_total_II(self):
        o = Decimal(0.0)
        return ((self.dap or o) + (self.frais_fin_charges_assi or o) + (self.diff_negatives_de_change or o) + (
                    self.ch_nettes_cessions_vmp or o))

    def resultat_financier(self):
        return (self.financier_total_I() - self.financier_total_II())

    def resultat_courant_avant_impots(self):
        return (self.resultat_exploitation() + self.resultat_financier())

    #TOTAL I Produits exceptionnels
    def excep_total_I(self):
        o = Decimal(0.0)
        return ((self.sur_op_gestion_prod_except or o) + (self.sur_op_en_capital_prod_except or o) + (
                    self.reprise_prov_transfert or o))

    # TOTAL II Produits exceptionnels
    def excep_total_II(self):
        o = Decimal(0.0)
        return ((self.sur_op_gestion_charg_except or o) + (self.sur_op_en_capital_charg_except or o) + (
                    self.dap_et_transfert_charg_except or o))

    def resultat_excep(self):
        return (self.excep_total_I() - self.excep_total_II())

    def resultat_exercice(self):
        o = Decimal(0.0)
        return (self.resultat_courant_avant_impots() + self.resultat_excep() -
                (self.participation_salairies or o) - (self.impot_sur_benefices or o))


    class Meta:
        verbose_name = _("Résultat bilan classique")
        verbose_name_plural = _("Résultats bilans classiques")
    


class Ratio:
    #On initialise avec un acheteur et une année
    def __init__(self, acheteur, annee):
        #--- actifc_set est donc un gestionnaire permettant d'accéder à tous les objets Actifc associés à un Acheteur donné
        self.actifs = list(
            acheteur.actifc_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).order_by('-annee'))
        self.passifs = list(
            acheteur.passifc_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).order_by('-annee'))
        self.resultats = list(
            acheteur.resultatc_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).order_by('-annee'))
    def fonds_de_roulement_ameliorer(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
                try:
                    actif = self.actifs[i].total_I()
                    passif = self.passifs[i].total_I_II()
                    if actif:  # éviter division par 0
                        res[i] = passif / actif
                except IndexError:
                    res[i] = None  # si l'année i n'existe pas
                except Exception:
                    res[i] = None  # pour d'autres erreurs éventuelles
                try:
                    # variation relative entre année 0 et 1
                    if res.get(1) not in (None, 0):
                        res['var'] = (res.get(0) - res.get(1)) / res.get(1)
                except Exception:
                    res['var'] = None
                return res

    def fonds_de_roulement(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.passifs[i].total_I_II() / self.actifs[i].total_I()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def fdr_normatif(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.passifs[i].total_III() - self.passifs[i].total_IV()) / self.actifs[i].total_II()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def autonomie_fin(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.passifs[i].total_I() / self.passifs[i].total_I_II()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def liquidite_reduite(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.actifs[i].creances() / self.passifs[i].total_III()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def liquidite_immediate(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.actifs[i].disponibilites_vmp() / self.passifs[i].total_III()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def caf(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.resultats[i].excedent_brut_ex() + (
                            self.resultats[i].financier_total_I() + self.resultats[i].excep_total_I()) - (
                                     self.resultats[i].financier_total_II() + self.resultats[i].excep_total_II())
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def caf_ht(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.resultats[i].ca() / self.actifs[i].effectif
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def rentabilite_economique(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.resultats[i].resultat_exercice() + self.resultats[i].financier_total_I()) / self.passifs[
                    i].total_I_II()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def rentabilite_fin(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.resultats[i].resultat_exercice() / self.actifs[i].total_I()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def rentabilite_de_loutil_de_production(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.actifs[i].total_I() + self.resultats[i].autres_charges_valeur_ajoutee) / self.resultats[
                    i].resultat_exploitation()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def couverture_des_frais_financiers(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.resultats[i].resultat_exploitation() / self.resultats[i].resultat_financier()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def rotation_des_stock_de_mp(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.actifs[i].stocks_mp * 360) / self.resultats[i].achat_mp_autres_appro
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def rotation_des_stock_de_pf(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.actifs[i].stocks_pf * 360) / self.resultats[i].ventes_de_produits_fabriques
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def rotation_des_stock_de_marchandises(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.actifs[i].stocks_mses * 360) / self.resultats[i].achat_mdses
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def rotation_des_stock_de_services(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.actifs[i].stocks_encours_services * 360) / (
                            self.resultats[i].ca() - self.resultats[i].resultat_exploitation())
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def credit_clients(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.actifs[i].creances() / self.resultats[i].ca()) * 360
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def credits_fournisseurs(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.passifs[i].dettes_fournisseurs_divers) / (
                            self.resultats[i].achat_mdses + self.resultats[i].achat_mp_autres_appro + self.resultats[
                        i].autres_achats + self.resultats[i].services_ext) * 360
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

##########################################################
##########################################################
# Fin Modules Bilan Classique
##########################################################
##########################################################


##########################################################
# Debut Modules Bilan Anglais
##########################################################

class ActifA(models.Model):
    # _safedelete_policy = SOFT_DELETE_CASCADE
    annee = models.ForeignKey('Annee', on_delete=models.DO_NOTHING)
    acheteur = models.ForeignKey('Acheteur', on_delete=models.DO_NOTHING)

    TYPE_BILAN = [
        ('annuel', 'Annuel'),
        ('semestriel', 'Semestriel'),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_BILAN,
        default='annuel',
        help_text=_("Type du résultat")
    )
    
    biens_installations_equipements = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                                          verbose_name="Biens, installations et équipements")
    # Attribut rajouté à partir de la V3
    actifs_non_courant = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                                          verbose_name="Actifs non courants")
    
    inventaire = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    creances_commerciales_autres_creances = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                                                verbose_name="Créances commerciales et autres")
    actif_impots_courant = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                               verbose_name="Actif d'Impôts courant")
    caisses_banques = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                          verbose_name="Caisse et banque")
       # Attribut rajouté à partir de la V3
    actifs_courant = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                                          verbose_name="Actifs courants")

    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='actifa_user_update', null=True, blank=True,
                                   on_delete=models.DO_NOTHING)

    def total_actifs_non_courants(self):
        o = Decimal(0.0)
        return (self.biens_installations_equipements or o)

    def total_actif_circulant(self):
        o = Decimal(0.0)
        return ((self.inventaire or o) +
                (self.creances_commerciales_autres_creances or o) +
                (self.actif_impots_courant or o) +
                (self.caisses_banques or o))

    def total_actif(self):
        return (self.total_actifs_non_courants() + self.total_actif_circulant())

class PassifA(models.Model):
    # _safedelete_policy = SOFT_DELETE_CASCADE
    annee = models.ForeignKey('Annee', on_delete=models.DO_NOTHING)
    acheteur = models.ForeignKey('Acheteur', on_delete=models.DO_NOTHING)

    TYPE_BILAN = [
        ('annuel', 'Annuel'),
        ('semestriel', 'Semestriel'),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_BILAN,
        default='annuel',
        help_text=_("Type du résultat")
    )
    
    # ----Total des fonds propres(capital_reserves + capital_declare + benefices_non_distribues
    capital_reserves = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                           verbose_name="Capital et Réserves")
    capital_declare = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                          verbose_name="Capital déclaré")
    benefices_non_distribues = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                                   verbose_name="Bénéfices non distribués")
    # ---Total du passif à long terme  ( passif_long_terme + pret_bancaire + compte_courant_administrateurs)
    # Nouvel attribut V3
    passif_long_terme = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                           verbose_name="Passif à long terme")
    pret_bancaire = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                        verbose_name="Prêt bancaire")
    compte_courant_administrateurs = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                                         verbose_name="Compte courant des administrateurs")
    
    # -----Total du passif à court terme  ( passif_courant + dettes_commerciales_autres_dettes + decouvert_bancaire + impots )
        # Nouvel attribut V3
    passif_courant = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                           verbose_name="  Passifs courants  ")
    dettes_commerciales_autres_dettes = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                                            verbose_name="Dettes commerciales et autres dettes")
    decouvert_bancaire = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                             verbose_name="Découvert bancaire")
    impots = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name="Impôts")


    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='passifa_user_update', null=True, blank=True,
                                   on_delete=models.DO_NOTHING)
    def total_fonds_propres(self):
        o = Decimal(0.0)
        return ((self.capital_reserves or o) + (self.capital_declare or o) + (self.benefices_non_distribues or o))

    def total_passif_long_terme(self):
        o = Decimal(0.0)
        return ((self.pret_bancaire or o) + (self.compte_courant_administrateurs or o))

    def total_passif_circulant(self):
        o = Decimal(0.0)
        return ((self.dettes_commerciales_autres_dettes or o) + (self.decouvert_bancaire or o) + (self.impots or o))

    def total_passif(self):
        return (self.total_passif_long_terme() + self.total_passif_circulant())

    def Total_fonds_propres_passif(self):
        return (self.total_passif() + self.total_fonds_propres())
    
class ResultatA(models.Model):
    # _safedelete_policy = SOFT_DELETE_CASCADE
    annee = models.ForeignKey('Annee', on_delete=models.DO_NOTHING)
    acheteur = models.ForeignKey('Acheteur', on_delete=models.DO_NOTHING)

    TYPE_BILAN = [
        ('annuel', 'Annuel'),
        ('semestriel', 'Semestriel'),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_BILAN,
        default='annuel',
        help_text=_("Type du résultat")
    )

    # Bénéfice brut
    produits_activites_ordinaires = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,                                                   verbose_name='Produits des activités ordinaires')
    ventes = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    charges_exploitation = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                               verbose_name="Charges d'exploitation")
    # Bénéfice d'exploitation
    frais_vente_generaux_administratifs = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                                              verbose_name='Frais de vente, généraux et administratifs')
    # Bénéfice avant coût financier et impots
    autres_revenus = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    # Bénéfice avant impôts
    frais_financier = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    # Bénéfice de l'année
    charge_impot_sur_revenu = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                                  verbose_name="Charge d'impôt sur le revenu")
    # Bénéfices non distribuées
    autres_elements_resultat_global = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
                                                          verbose_name='Autres éléments du résultat global')
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='resultata_user_update', null=True, blank=True,
                                   on_delete=models.DO_NOTHING)

    def marge_brut(self):
        o = Decimal(0.0)
        return ((self.produits_activites_ordinaires or o) + (self.ventes or o) + (self.charges_exploitation or o))

    def resultat_exploitation(self):
        o = Decimal(0.0)
        return (self.marge_brut() + (self.frais_vente_generaux_administratifs or o))

    def benefice_avant_cout_financier_impots(self):
        o = Decimal(0.0)
        return (self.resultat_exploitation() + (self.autres_revenus or o))

    def resultat_avant_impots(self):
        o = Decimal(0.0)
        return (self.benefice_avant_cout_financier_impots() + (self.frais_financier or o))

    def benefice_annee(self):
        o = Decimal(0.0)
        return (self.resultat_avant_impots() + (self.charge_impot_sur_revenu or o))

    def benefices_non_distribues(self):
        o = Decimal(0.0)
        return (self.benefice_annee() + (self.autres_elements_resultat_global or o))


class Ratioang:
    def __init__(self, acheteur, annee):
        self.actifang = list(
            acheteur.actifa_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).order_by('-annee'))
        self.passifang = list(
            acheteur.passifa_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).order_by('-annee'))
        self.resultatang = list(
            acheteur.resultata_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).order_by('-annee'))

    def solvabilite(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.passifang[i].total_fonds_propres() / self.actifang[i].total_actif()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def autonomiefin(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.passifang[i].total_fonds_propres() / (
                            self.passifang[i].total_fonds_propres() + self.passifang[i].total_passif_long_terme())
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def rendement_capitaux_propres(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.resultatang[i].benefice_annee() / self.passifang[i].total_fonds_propres()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def taux_marge_net(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.resultatang[i].benefice_annee() / self.resultatang[i].produits_activites_ordinaires
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def liquidite_generale(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.actifang[i].total_actif_circulant() / self.passifang[i].total_passif_circulant()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def jour_recouvrement_moyen(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = ((self.actifang[i].total_actif_circulant() - self.actifang[i].inventaire) / self.resultatang[
                    i].produits_activites_ordinaires) * 365
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def jour_paiement_moyen(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.passifang[i].dettes_commerciales_autres_dettes / self.resultatang[i].ventes) * 365
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def taux_rotation_creance(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.resultatang[i].produits_activites_ordinaires / (
                            self.actifang[i].total_actif_circulant() - self.actifang[i].inventaire)
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def taux_rotation_stock(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.resultatang[i].produits_activites_ordinaires / self.actifang[i].inventaire
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def taux_rotation_actif(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.resultatang[i].produits_activites_ordinaires / self.actifang[i].total_actifs_non_courants
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def ratio_endettement1(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.passifang[i].pret_bancaire + self.passifang[i].dettes_commerciales_autres_dettes) / \
                         self.passifang[i].Total_fonds_propres_passif()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def ratio_endettement2(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.passifang[i].pret_bancaire / self.actifang[i].total_actifs_non_courants()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def passif_cour_terme(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.passifang[i].total_passif_circulant() / self.actifang[i].total_actifs_non_courants()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def ratios_couverture_interet(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                pass
                res[i] = self.resultatang[i].benefice_avant_cout_financier_impots() / self.resultatang[
                    i].frais_financier
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def ratios_liquidite_general(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.actifang[i].total_actif_circulant() / self.passifang[i].total_passif_circulant()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def ratios_liquidite2(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.actifang[i].total_actif_circulant() - self.actifang[i].inventaire) / self.passifang[
                    i].total_passif_circulant()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def ratio_g_score_fin(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.actifang[i].total_actifs_non_courants() / self.actifang[i].total_actif()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def ratio_endettement_g_score(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.passifang[i].pret_bancaire / self.passifang[i].total_fonds_propres()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res


##########################################################
# FIN Modules Bilan Anglais
##########################################################

##########################################################
# Debut Modules Bilan SYSCOHADA
##########################################################

class ActifS(models.Model):
    # _safedelete_policy = SOFT_DELETE_CASCADE
    annee = models.ForeignKey('Annee', on_delete=models.DO_NOTHING)
    acheteur = models.ForeignKey('Acheteur', on_delete=models.DO_NOTHING)

    TYPE_BILAN = [
        ('annuel', 'Annuel'),
        ('semestriel', 'Semestriel'),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_BILAN,
        default='annuel',
        help_text=_("Type du résultat")
    )
    #------ Immobilisation incorporelles
    frais_developpement_prospection = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    brevets_licences_logiciels = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    droits_propriete_commerciale_baux = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    autres_immo_incorporelles = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    # -----Immobilisations corporelles
    terrains = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name="Terrains")
    dons_investissements_net = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    batiments = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    # dons_investissements_net2 = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    agencements_amenagements_installations = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    materiel_mobilier_actif_biologiques = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    materiel_transport = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    # ---Avances et acomptes sur immobilisations
    avances_acompte_immobilisations = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    # Immobilisations financieres
    titres_participation = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)  
    autres_immobilisations_financieres = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    # Actif circulant de HAO
    actif_circulant_hao = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    # Stock et En-cours (calcule)
    stock_encours = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    # Creances et emplois similaires (calcule)
    fournisseurs_avances_versee = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    clients = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    autres_creances = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    # Total de l'actif circulant
    valeurs_mobilieres_placement = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    disponibilites = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    banque_cheque_postal_caisse_assimiles = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    # Total de la tresorerie et des equivalents de tresorerie
    ecart_conversion_actif = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='actifs_user_update', null=True, blank=True,
                                   on_delete=models.DO_NOTHING)

    def immobilisation_incorporelles(self):
        o = Decimal(0.0)
        return ((self.frais_developpement_prospection or o) +
                (self.brevets_licences_logiciels or o) +
                (self.droits_propriete_commerciale_baux or o) +
                (self.autres_immo_incorporelles or o))

    def immobilisations_corporelles(self):
        o = Decimal(0.0)
        return ((self.terrains or o) +
                (self.dons_investissements_net or o) +
                (self.batiments or o) +
                # self.dons_investissements_net2 +
                (self.agencements_amenagements_installations or o) +
                (self.materiel_mobilier_actif_biologiques or o) +
                (self.materiel_transport or o))

    def immobilisations_financieres(self):
        o = Decimal(0.0)
        return ((self.titres_participation or o) +
                (self.autres_immobilisations_financieres or o))

    def total_actif_immobilise(self):
        o = Decimal(0.0)
        return ((self.immobilisation_incorporelles() or o) +
                (self.immobilisations_corporelles() or o)+
                (self.avances_acompte_immobilisations  or o)+
                (self.immobilisations_financieres() or o))

    def creances_emplois_similaires(self):
        o = Decimal(0.0)
        return ((self.fournisseurs_avances_versee or o) +
                (self.clients or o) +
                (self.autres_creances or o))

    def total_actif_circulant(self):
        o = Decimal(0.0)
        return ((self.actif_circulant_hao or o) +
                (self.stock_encours or o) +
                (self.creances_emplois_similaires() or o))

    def total_tresorerie_equivalents(self):
        o = Decimal(0.0)
        return ((self.valeurs_mobilieres_placement or o) +
                (self.disponibilites or o) +
                (self.banque_cheque_postal_caisse_assimiles or o))

    def total_actif(self):
        o = Decimal(0.0)
        return ((self.total_actif_immobilise() or o) +
                (self.total_actif_circulant() or o) +
                (self.total_tresorerie_equivalents() or o) +
                (self.ecart_conversion_actif or o))


class PassifS(models.Model):
    # _safedelete_policy = SOFT_DELETE_CASCADE
    annee = models.ForeignKey('Annee', on_delete=models.DO_NOTHING)
    acheteur = models.ForeignKey('Acheteur', on_delete=models.DO_NOTHING)

    TYPE_BILAN = [
        ('annuel', 'Annuel'),
        ('semestriel', 'Semestriel'),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_BILAN,
        default='annuel',
        help_text=_("Type du résultat")
    )

    capital = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    capital_non_appele_apporteurs = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name="Capital non appelé des apporteurs")
    primes_liees_capital_social = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Primes liées capital social')
    ecart_reevaluation = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Ecart de réevaluation')
    reserves_indisponibles = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    reserves_libres = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    report_nouveau = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Report à nouveau (+ ou -)')
    resultat_net_exercice = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Résultat net de l\'exercice (bénéfice + ou perte -)')
    subventions_investissements = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name="Subventions d'investissement")
    provisions_reglees = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name="Provisions réglées")
    # Total des capitaux propres et resources similaires
    emprunts_dettes_financieres_diverse = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Emprunts et dettes financières diverses')
    dettes_location_vente = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name="Dettes de location-vente")
    provisions_risques_charges = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name="Provisions pour risques et charges")
    # Total des dettes financieres et ressources assimiles
    # Total des ressources stables
    passif_circulant_hao = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Passif circulant HAO')
    clients_avances_recues = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Clients, avances reçues')
    fournisseurs_exploitation = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name="Fournisseurs d'exploitation")
    dettes_fiscales_sociales = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name="Dettes fiscales et sociales")
    autres_dettes = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True)
    provisions_risques_court_terme = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name="Provisions pour risques à court terme")
    # Total des passifs courants
    banques_credit_escompte = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name="Banques, crédits d'escompte")
    banques_etablissements_financiers_credit_caisse = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name="Banques, établissements financiers et crédits de caisse")
    # Total de la tresorerie et des equivalents de tresorerie
    ecart_conversion_passif = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name="Ecarts de conversion - Passif")
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='passifs_user_update', null=True, blank=True,
                                   on_delete=models.DO_NOTHING)

    def total_capitaux_propres_ressources_similaires(self):
        o = Decimal(0.0)
        return ((self.capital or o) +
                (self.capital_non_appele_apporteurs  or o) +
                (self.primes_liees_capital_social  or o) +
                (self.ecart_reevaluation   or o)+
                (self.reserves_indisponibles  or o) +
                (self.reserves_libres  or o) +
                (self.report_nouveau   or o)+
                (self.resultat_net_exercice  or o) +
                (self.subventions_investissements  or o) +
                (self.provisions_reglees  or o))

    def total_dettes_financieres_ressources_similaires(self):
        o = Decimal(0.0)
        return ((self.emprunts_dettes_financieres_diverse or o) +
                (self.dettes_location_vente or o) +
                (self.provisions_risques_charges or o))

    def total_ressources_stables(self):
        o = Decimal(0.0)
        return ((self.total_capitaux_propres_ressources_similaires() or o) +
                (self.total_dettes_financieres_ressources_similaires() or o))

    def total_passifs_courants(self):
        o = Decimal(0.0)
        return ((self.passif_circulant_hao or o) +
                (self.clients_avances_recues or o) +
                (self.fournisseurs_exploitation or o) +
                (self.dettes_fiscales_sociales or o) +
                (self.autres_dettes or o) +
                (self.provisions_risques_court_terme or o))

    def total_tresorerie_equivalents(self):
        o = Decimal(0.0)
        return ((self.banques_credit_escompte or o) +
                (self.banques_etablissements_financiers_credit_caisse or o))

    def total_passifs(self):
        o = Decimal(0.0)
        return ((self.total_ressources_stables() or o) +
                (self.total_passifs_courants() or o) +
                (self.total_tresorerie_equivalents() or o) +
                (self.ecart_conversion_passif or o))


class ResultatS(models.Model):
    # _safedelete_policy = SOFT_DELETE_CASCADE
    annee = models.ForeignKey('Annee', on_delete=models.DO_NOTHING)
    acheteur = models.ForeignKey('Acheteur', on_delete=models.DO_NOTHING)

    TYPE_BILAN = [
        ('annuel', 'Annuel'),
        ('semestriel', 'Semestriel'),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_BILAN,
        default='annuel',
        help_text=_("Type du résultat")
    )

    ventes_marchandises_a = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Ventes de marchandises A (+)')
    achats_marchandises = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Achats de marchandises (-)')
    variation_stock_marchandises = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Variation des stocks de marchandises (-/+)')
    # Marge commerciale
    ventes_produits_manufactures = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Ventes de produits manufacturés B (+)')
    travaux_services_vendus_c = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Travaux, services vendus C (+)')
    produits_accessoires_d = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Produits accessoires D (+)')
    # Chiffre d'affaires
    production_stockee = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Production stockée (ou déstockage) (-/+)')
    production_immobilisee = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Production Immobilisée (+)')
    subvention_exploitation = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Subvention d\'exploitation (+)')
    autres_produits = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Autres produits (+)')
    transfert_charges_exploitation = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Transfert de charges d\'exploitation (+)')
    achats_matieres_premieres_fournitures_connexes = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
            verbose_name='Achats de matières premières et fournitures connexes (-)')
    variation_stock_matieres_premieres_fournitures_connexes = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
            verbose_name='Variation des stocks de matières premières et fournitures connexes (-/+)')
    autres_achats = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Autres achats (-)')
    variation_stock_autres_fournitures = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
            verbose_name='Variation des stocks d\'autres fournitures (-/+)')
    transport = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Transport (-)')
    services_exterieurs = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Services extérieurs (-)')
    impots_taxes = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Impots et taxes (-)')
    autres_depenses = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Autres dépenses (-)')
    # Valeur ajoutee
    frais_personnel = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Frais de personnel (-)')
    # Excedent brut d'exploitation
    reprise_depreciations_amortissements_provision_pertes_valeurs_p = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, 
            verbose_name='Reprises de dépréciations, amortissements, provisions et pertes de valeur (+)')
    reprise_depreciations_amortissements_provision_pertes_valeurs_m = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, 
            verbose_name='Reprises de dépréciations, amortissements, provisions et pertes de valeur (-)')
    # Resultat d'exploitation
    produits_financiers_assimiles = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
            verbose_name='Produits financiers et assimilés (+)')
    reprise_provision_perte_valeur = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
            verbose_name='Reprises sur provisions et pertes de valeur (+)')
    transfert_charges_financieres = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
            verbose_name='Transfert de charges financières (+)')
    charges_financieres_assimilees = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, 
            verbose_name='Charges financières et assimilées (-)')
    dotations_provisions_depreciations_financieres = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
            verbose_name='Dotations aux provisions et dépréciations financières (-)')
    # Resultat Financier
    # Resultat des activites ordinaires (XE + XF)
    produits_cession_immobilisations = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, 
            verbose_name='Produits des cessions d\'immobilisations (+)')
    autres_produits_hao = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Autres produits HAO (+)')
    valeur_comptable_cessions_actifs_immobilises = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
            verbose_name='Valeur comptable des cessions d\'actifs immobilisés (-)')
    autres_charges_hao = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, verbose_name='Autres charges HAO (-)')
    # Resultats des activites ordinaires (Somme TN à RP)
    participation_travailleurs = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True, 
            verbose_name='Participation des travailleurs (-)')
    charge_impot_revenu = models.DecimalField(max_digits=100, decimal_places=5, null=True, blank=True,
            verbose_name='Charge d\'impôt sur le revenu (-)')
    #Resultat net (XG + XH + RQ +RS)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='resultats_user_update', null=True, blank=True,
                                   on_delete=models.DO_NOTHING)

    def marge_commerciale(self):
        o = Decimal(0.0)
        return ((self.variation_stock_marchandises or o) * 1 +
                (self.achats_marchandises or o) * -1 +
                (self.ventes_marchandises_a or o) * 1)

    def chiffre_affaires(self):
        o = Decimal(0.0)
        return ((self.ventes_marchandises_a or o)  * 1 +
                (self.ventes_produits_manufactures or o)  * 1 +
                (self.travaux_services_vendus_c or o)  * 1 +
                (self.produits_accessoires_d or o)  * 1)


    def valeur_ajoutee(self):
        o = Decimal(0.0)
        return ((self.chiffre_affaires() or o) +
                (self.achats_marchandises or o) * -1 +
                 (self.variation_stock_marchandises or o) * 1 +
                (self.autres_depenses or o) * -1 +
                (self.impots_taxes or o) * -1 +
                (self.services_exterieurs or o) * -1 +
                (self.transport or o) * -1 +
                (self.variation_stock_autres_fournitures or o) * 1 +
                (self.autres_achats or o) * -1 +
                (self.variation_stock_matieres_premieres_fournitures_connexes or o) * 1 +
                (self.achats_matieres_premieres_fournitures_connexes or o) * -1 +
                (self.transfert_charges_exploitation or o) * 1 +
                (self.autres_produits or o) * 1 +
                (self.subvention_exploitation or o) * 1 +
                (self.production_immobilisee or o) * 1 +
                (self.production_stockee or o) * 1)

    def excedent_brute_exploitation(self):
        o = Decimal(0.0)
        return (self.valeur_ajoutee() +
                 (self.frais_personnel or o) * -1)

    def resultat_exploitation(self):
        o = Decimal(0.0)
        return (self.excedent_brute_exploitation() +
                (self.reprise_depreciations_amortissements_provision_pertes_valeurs_p or o) * 1 +
                (self.reprise_depreciations_amortissements_provision_pertes_valeurs_m or o) * -1)

    def resultat_financier(self):
        o = Decimal(0.0)
        return (
            (self.dotations_provisions_depreciations_financieres or o) * -1 +
            (self.charges_financieres_assimilees or o) * -1 +
            (self.transfert_charges_financieres or o) * 1 +
            (self.reprise_provision_perte_valeur or o) * 1 +
            (self.produits_financiers_assimiles or o) * 1)

    def resultat_activites_ordinaires_xe(self):
        return (self.resultat_exploitation() + self.resultat_financier())

    def resultat_activites_ordinaires_tn(self):
        o = Decimal(0.0)
        return ((self.produits_cession_immobilisations or o) * 1 +
                (self.autres_produits_hao or o) * 1 +
                (self.valeur_comptable_cessions_actifs_immobilises or o) * -1 +
                (self.autres_charges_hao or o) * -1)

    def resultat_net(self):
        o = Decimal(0.0)
        return (self.resultat_activites_ordinaires_xe() +
                self.resultat_activites_ordinaires_tn() +
                (self.participation_travailleurs or o) * -1 +
                (self.charge_impot_revenu or o) * -1)



class Ratiosys:
    def __init__(self, acheteur, annee):
        self.actifsys = list(acheteur.actifs_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).order_by('-annee'))
        self.passifsys = list(acheteur.passifs_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).order_by('-annee'))
        self.resultatsys = list(acheteur.resultats_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).order_by('-annee'))

    def fonds_de_roulement(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.passifsys[i].total_ressources_stables() - self.actifsys[i].total_actif_immobilise()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def besoin_fonds_de_roulement(self):
        res = { 0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0 }
        for i in range(3):
            try:
                res[i] = (self.actifsys[i].total_actif_circulant() - self.passifsys[i].total_passifs_courants())
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def position_net_de_tresorerie(self):
        res = { 0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0 }
        for i in range(3):
            try:
                res[i] = (self.passifsys[i].total_ressources_stables() - self.actifsys[i].total_actif_immobilise())-(self.actifsys[i].total_actif_circulant() - self.passifsys[i].total_passifs_courants())
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res


    def cafsys(self):
        res = { 0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0 }
        for i in range(3):
            try:
                res[i] = (self.resultatsys[i].excedent_brute_exploitation() + self.resultatsys[i].ventes_marchandises_a + self.resultatsys[i].ventes_produits_manufactures + self.resultatsys[i].travaux_services_vendus_c + self.resultatsys[i].produits_accessoires_d + self.resultatsys[i].autres_produits +self.resultatsys[i].produits_financiers_assimiles + self.resultatsys[i].reprise_provision_perte_valeur + self.resultatsys[i].transfert_charges_financieres)-(self.resultatsys[i].achats_marchandises + self.resultatsys[i].achats_matieres_premieres_fournitures_connexes + self.resultatsys[i].autres_achats + self.resultatsys[i].transport + self.resultatsys[i].services_exterieurs + self.resultatsys[i].impots_taxes + self.resultatsys[i].autres_depenses + self.resultatsys[i].frais_personnel + self.resultatsys[i].valeur_comptable_cessions_actifs_immobilises + self.resultatsys[i].autres_charges_hao + self.resultatsys[i].charges_financieres_assimilees + self.resultatsys[i].dotations_provisions_depreciations_financieres)+1000
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res


    def solvabilite(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.passifsys[i].total_capitaux_propres_ressources_similaires() / self.passifsys[i].total_passifs()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def autonomie_financiere(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.passifsys[i].total_capitaux_propres_ressources_similaires() / self.passifsys[i].passif_circulant_hao
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res


    def benefice_net(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.resultatsys[i].resultat_net()/self.passifsys[i].total_capitaux_propres_ressources_similaires()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res



    def turnover(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] =((self.resultatsys[i].excedent_brute_exploitation() + self.resultatsys[i].ventes_marchandises_a + self.resultatsys[i].ventes_produits_manufactures + self.resultatsys[i].travaux_services_vendus_c + self.resultatsys[i].produits_accessoires_d + self.resultatsys[i].autres_produits + self.resultatsys[i].produits_financiers_assimiles + self.resultatsys[i].reprise_provision_perte_valeur + self.resultatsys[i].transfert_charges_financieres) -( self.resultatsys[i].achats_marchandises + self.resultatsys[i].achats_matieres_premieres_fournitures_connexes + self.resultatsys[i].autres_achats + self.resultatsys[i].transport + self.resultatsys[i].services_exterieurs + self.resultatsys[i].impots_taxes + self.resultatsys[i].autres_depenses + self.resultatsys[i].frais_personnel + self.resultatsys[i].valeur_comptable_cessions_actifs_immobilises + self.resultatsys[i].autres_charges_hao +self.resultatsys[i].charges_financieres_assimilees + self.resultatsys[i].dotations_provisions_depreciations_financieres ))/self.resultatsys[i].chiffre_affaires()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def benefice_net_chiffre_affaire(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.resultatsys[i].resultat_net()/self.resultatsys[i].chiffre_affaires()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def ebitda_chiffre_affaire(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.resultatsys[i].excedent_brute_exploitation()/self.resultatsys[i].chiffre_affaires()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def liquidite_general(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.actifsys[i].total_actif_circulant()/ self.passifsys[i].total_passifs_courants()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def liquidite_reduite(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.actifsys[i].creances_emplois_similaires()+self.actifsys[i].total_tresorerie_equivalents())/self.passifsys[i].total_passifs_courants()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def liquidite_immediate(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.actifsys[i].total_tresorerie_equivalents() / self.passifsys[i].total_passifs_courants()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def jour_collecte_moyens(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.actifsys[i].creances_emplois_similaires()/(self.resultatsys[i].chiffre_affaires()+self.resultatsys[i].autres_produits + self.resultatsys[i].transfert_charges_exploitation + self.resultatsys[i].subvention_exploitation + self.resultatsys[i].production_immobilisee))*365
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res


    def moyen_paiement(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.passifsys[i].total_passifs_courants()/(self.resultatsys[i].achats_marchandises + self.resultatsys[i].achats_matieres_premieres_fournitures_connexes + self.resultatsys[i].autres_achats))*365
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res


    def compte_debiteur(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.resultatsys[i].chiffre_affaires()+self.resultatsys[i].production_immobilisee+self.resultatsys[i].subvention_exploitation + self.resultatsys[i].autres_produits +self.resultatsys[i].transfert_charges_exploitation)/self.actifsys[i].creances_emplois_similaires()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def rotation_stock(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.resultatsys[i].chiffre_affaires()+self.resultatsys[i].production_immobilisee+self.resultatsys[i].subvention_exploitation + self.resultatsys[i].autres_produits +self.resultatsys[i].transfert_charges_exploitation)/self.actifsys[i].stock_encours
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res


    def rotation_actif(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.resultatsys[i].chiffre_affaires()+self.resultatsys[i].production_immobilisee+self.resultatsys[i].subvention_exploitation + self.resultatsys[i].autres_produits +self.resultatsys[i].transfert_charges_exploitation)/self.actifsys[i].total_actif_immobilise()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res


    def rotation_dendettement(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.passifsys[i].emprunts_dettes_financieres_diverse+self.passifsys[i].total_passifs_courants())/self.actifsys[i].creances_emplois_similaires()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res


    def rotation_dette_capitaux_propres(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.passifsys[i].emprunts_dettes_financieres_diverse/self.actifsys[i].total_actif_immobilise()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def passif_court_terme_par_rapport_valeur_net(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.passifsys[i].total_passifs_courants()/self.actifsys[i].total_actif_immobilise()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def ratio_des_couverture_des_interets(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.resultatsys[i].resultat_activites_ordinaires_xe()/self.resultatsys[i].charges_financieres_assimilees
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res


    def ratio_courant(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.actifsys[i].total_actif_circulant()/self.passifsys[i].total_passifs_courants()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def ratio_de_liquidite(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = (self.actifsys[i].total_actif_circulant()-self.actifsys[i].stock_encours)/self.passifsys[i].total_passifs_courants()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res


    def ratio_financier(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.actifsys[i].immobilisations_financieres()/self.actifsys[i].total_actif()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def ratio_de_la_dette(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.passifsys[i].total_dettes_financieres_ressources_similaires()/self.passifsys[i].total_capitaux_propres_ressources_similaires()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

    def ratio_de_liquidite2(self):
        res = {0: 0.0, 1: 0.0, 2: 0.0, 'var': 0.0}
        for i in range(3):
            try:
                res[i] = self.actifsys[i].autres_immo_incorporelles/self.passifsys[i].total_capitaux_propres_ressources_similaires()
            except:
                pass
        try:
            res['var'] = res.get(0) - res.get(1) / res.get(1)
        except:
            pass
        return res

##########################################################
# FIN Modules Bilan SYSCOHADA
##########################################################

##########################################################
# Debut  SCORING
##########################################################
class Scoring(models.Model):
    # _safedelete_policy = SOFT_DELETE_CASCADE
    annee = models.ForeignKey('Annee', on_delete=models.DO_NOTHING)
    acheteur = models.ForeignKey('Acheteur', on_delete=models.DO_NOTHING)
    score = models.CharField(max_length=4, blank=True, null=True)
    commentaire = models.TextField(blank=True, max_length=10000000, null=True, verbose_name=_("Commentaire"))
    updated_at = models.DateTimeField(auto_now=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='scoring_user_update', null=True, blank=True,
                                   on_delete=models.DO_NOTHING)
    # history = HistoricalRecords()

    def auto(acheteur, annee):
        from datetime import datetime
        from decimal import Decimal

        val = 0
        if acheteur:
            actifs = list(
                acheteur.actifc_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).order_by('-annee__annee'))
            passifs = list(
                acheteur.passifc_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).order_by('-annee__annee'))
            resultats = list(
                acheteur.resultatc_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).order_by('-annee__annee'))

            if len(actifs) == 0 and len(passifs) == 0 and len(resultats) == 0:
                de = (acheteur.donneesenregistrement_set.all()
                      .order_by('-date_creation').first())

                try:
                    if de:
                        nb = datetime.now().year - de.date_creation.year
                        if nb == 0:
                            val = 0
                        elif nb <= 2:
                            val = 0.1
                        elif nb <= 4:
                            val = 0.2
                        elif nb <= 6:
                            val = 0.4
                        elif nb <= 8:
                            val = 0.6
                        elif nb <= 10:
                            val = 0.8
                        else:
                            val = 1

                    if (de.forme_juridique == "Public limited company (SA)" or
                            de.forme_juridique == "Société Anonyme(SA)" or
                            de.forme_juridique == "Anonimous company"):
                        val += 1
                    elif (de.forme_juridique == "Limited Liability Company (SARL)" or
                          de.forme_juridique == "Société à Responsabilité Limitée (SARL)"):
                        val += 0.75
                    elif (de.forme_juridique == "Entreprise Individuelle (EI)" or
                          de.forme_juridique == "Individual company(EI)" or
                          de.forme_juridique == "Sole Proprietorship (SP)"):
                        val += 0.05
                    elif (de.forme_juridique == "Société à Responsabilité Limitée Unipersonnelle (SARL U)" or
                          de.forme_juridique == "One Person Limited Liability Company (SARL U)"):
                        val += 0.5
                    elif (de.forme_juridique == "Branch" or
                          de.forme_juridique == "Succursale" or
                          de.forme_juridique == "Government body" or
                          de.forme_juridique == "Corps Gouvernemental"):
                        val += 0.005
                    elif (de.forme_juridique == "Other legal form" or
                          de.forme_juridique == "Autre forme juridique"):
                        val += 0.003
                except:
                    pass

                pe = acheteur.proprieteetactif_set.all().first()
                if pe:
                    if (pe.locaux == "Owner" or pe.locaux == "Propriétaire"):
                        val += 1
                    elif (pe.locaux == "Tenant" or pe.locaux == "Locataire"):
                        val += 0.5

                cv = acheteur.conditiondevente_set.all().first()
                if cv:
                    if (cv.comportement_de_paiement == "En Avance" or cv.comportement_de_paiement == "In Advance"):
                        val += 1
                    elif (
                            cv.comportement_de_paiement == "En Temps et en heure" or cv.comportement_de_paiement == "In Time"):
                        val += 0.5
                    elif (cv.comportement_de_paiement == "Normal"):
                        val += 0.25
                    elif (
                            cv.comportement_de_paiement == "Mauvais payeur" or cv.comportement_de_paiement == "Bad Payer"):
                        val -= 1

                tc = acheteur.tendance_set.all().first()
                if tc:
                    if (tc.avis_commercial == "Medium" or tc.avis_commercial == "Moyen"):
                        val += 0.25
                    elif (tc.avis_commercial == "Good" or tc.avis_commercial == "Bon"):
                        val += 0.5
                    elif (tc.avis_commercial == "Very good" or tc.avis_commercial == "Très bien"):
                        val += 0.75

                if val > 10:
                    val = 10
                if val < 0:
                    val = 0
                return {0: val}
            else:
                scores = {0: 0, 1: 0, 2: 0}
                for i in range(3):
                    o = Decimal(0.0)
                    ffi = o
                    ebe = o
                    ca = o
                    va = o
                    cred_disp_net = o
                    dettes = o
                    cours_permanent = o
                    passif = o
                    fdr = o

                    typebilan = acheteur.comptefinancier_set.all().first()
                    # print(typebilan.type_bilan)
                    try:
                        typebilan = acheteur.comptefinancier_set.all().first()
                        print(typebilan.type_bilan)

                        if typebilan.type_bilan == "Classique":

                            actifs = acheteur.actifc_set.get(annee__annee=annee - i)
                            passifs = acheteur.passifc_set.get(annee__annee=annee - i)
                            resultats = acheteur.resultatc_set.get(annee__annee=annee - i)
                            try:
                                ffi = (resultats.frais_fin_charges_assi or o)
                                ebe = resultats.excedent_brut_ex()
                                ca = resultats.ca()
                                va = resultats.valeur_ajoutee()
                            except:
                                pass

                            try:
                                cred_disp_net = ((actifs.clients_et_cptes_rattaches or o) +
                                                 (actifs.autres_creances or o) +
                                                 (actifs.valeurs_a_encaisser or o) +
                                                 (actifs.banques_cheques_postaux_caisse or o))
                                tresorerie = ((actifs.banques_cheques_postaux_caisse or o) - (
                                        actifs.valeurs_a_encaisser or o))
                            except:
                                pass

                            try:
                                cours_permanent = passifs.total_I_II()
                                passif = passifs.total_general()
                                dettes = passifs.total_III() + passifs.total_IV()
                            except:
                                pass

                            caj = ca / Decimal(360.0)

                            try:
                                fdr = ((actifs.banques_cheques_postaux_caisse or o) - passifs.total_I_II())
                            except:
                                try:
                                    fdr = (actifs.banques_cheques_postaux_caisse or o)
                                except:
                                    try:
                                        fdr = -passifs.total_I_II()
                                    except:
                                        fdr = o

                            R1 = (ffi / ebe) * Decimal(100.0) if ebe != o else o
                            R2 = (cred_disp_net / dettes) * Decimal(100.0) if dettes != o else o
                            R3 = (cours_permanent / passif) * Decimal(100.0) if passif != o else o
                            R4 = (va / ca) * Decimal(100.0) if ca != o else o
                            R5 = (tresorerie / caj) * Decimal(100.0) if caj != o else o
                            R6 = (fdr / caj) * Decimal(0.0) if caj != o else o
                        elif typebilan.type_bilan == "Syscohada":
                            actifsys = acheteur.actifs_set.get(annee__annee=annee - i)
                            passifsys = acheteur.passifs_set.get(annee__annee=annee - i)
                            resultatsys = acheteur.resultats_set.get(annee__annee=annee - i)

                            # try:
                            ffi = (resultatsys.charges_financieres_assimilees or o)
                            ebe = resultatsys.excedent_brute_exploitation()
                            ca = resultatsys.chiffre_affaires()
                            va = resultatsys.valeur_ajoutee()
                            # except:
                            #   pass

                            # try:
                            cred_disp_net = (
                                    actifsys.creances_emplois_similaires() + actifsys.total_tresorerie_equivalents())
                            tresorerie = actifsys.total_actif_circulant()

                            # except:
                            #   pass

                            # try:
                            cours_permanent = passifsys.total_ressources_stables()
                            passif = passifsys.total_passifs()
                            CT_debts = (passifsys.total_passifs_courants() + passifsys.total_tresorerie_equivalents())
                            # except:
                            #   pass

                            try:
                                fdr = (
                                            passifsys.total_capitaux_propres_ressources_similaires() - actifsys.total_actif_immobilise())
                            except:
                                try:
                                    fdr = (passifsys.total_capitaux_propres_ressources_similaires())
                                except:
                                    try:
                                        fdr = -actifsys.total_actif_immobilise()
                                    except:
                                        fdr = o

                            caj = ca / Decimal(360.0)

                            R1 = (ffi / ebe) * Decimal(100.0) if ebe != o else o
                            R2 = (cred_disp_net / CT_debts) * Decimal(100.0) if CT_debts != o else o
                            R3 = (cours_permanent / passif) * Decimal(100.0) if passif != o else o
                            R4 = (va / ca) * Decimal(100.0) if ca != o else o
                            R5 = (tresorerie / caj) if caj != o else o
                            R6 = (fdr / caj) * Decimal(0.0) if caj != o else o

                        elif typebilan.type_bilan == "Anglais":

                            # print("Nous sommes tous dans le score en Anglais")
                            actifang = acheteur.actifa_set.get(annee__annee=annee - i)
                            passifang = acheteur.passifa_set.get(annee__annee=annee - i)
                            resultatang = acheteur.resultata_set.get(annee__annee=annee - i)

                            # try:
                            ffi = (resultatang.frais_financier or o)
                            ebe = resultatang.benefice_avant_cout_financier_impots()
                            ca = (resultatang.produits_activites_ordinaires or o)
                            va = resultatang.marge_brut()
                            # except:
                            # pass

                            # try:
                            cred_disp_net = ((actifang.caisses_banques or o) + (
                                        actifang.creances_commerciales_autres_creances or o))
                            tresorerie = (actifang.caisses_banques or o)

                            # except:
                            #   pass

                            # try:
                            cours_permanent = passifang.total_passif_long_terme() + passifang.total_fonds_propres()
                            passif = passifang.Total_fonds_propres_passif()

                            CT_debts = (passifang.decouvert_bancaire or o) + (
                                        passifang.dettes_commerciales_autres_dettes or o) + (passifang.impots or o)
                            # except:
                            #    pass

                            try:
                                fdr = (passifang.total_passif_long_terme() + passifang.total_fonds_propres()) - (
                                        (actifang.creances_commerciales_autres_creances or o) + (
                                            actifang.caisses_banques or o))
                            except:
                                try:
                                    fdr = (passifang.total_passif_long_terme() + passifang.total_fonds_propres())
                                except:
                                    try:
                                        fdr = -((actifang.creances_commerciales_autres_creances or o) + (
                                                    actifang.caisses_banques or o))
                                    except:
                                        fdr = o

                            caj = ca / Decimal(360.0)

                            R1 = (ffi / ebe) * Decimal(100.0) if ebe != o else o
                            R2 = (cred_disp_net / CT_debts) * Decimal(100.0) if CT_debts != o else o
                            R3 = (cours_permanent / passif) * Decimal(100.0) if passif != o else o
                            R4 = (va / ca) * Decimal(100.0) if ca != o else o
                            R5 = (tresorerie / caj) if caj != o else o
                            R6 = (fdr / caj) * Decimal(0.0) if caj != o else o

                        # application des bornes
                        if R1 < Decimal(0.0):
                            R1 = Decimal(0.0)
                        elif R1 > Decimal(100.0):
                            R1 = Decimal(100.0)

                        if R2 < Decimal(0.0):
                            R2 = Decimal(0.0)
                        elif R2 > Decimal(200.0):
                            R2 = Decimal(200.0)

                        if R3 < Decimal(-25.0):
                            R3 = Decimal(-25.0)
                        elif R3 > Decimal(100.0):
                            R3 = Decimal(100.0)

                        if R4 < Decimal(0.0):
                            R4 = Decimal(0.0)
                        elif R4 > Decimal(100.0):
                            R4 = Decimal(100.0)

                        if R5 < Decimal(-100.0):
                            R5 = Decimal(-100.0)
                        elif R5 > Decimal(100.0):
                            R5 = Decimal(100.0)

                        if R6 < Decimal(-100.0):
                            R6 = Decimal(-100.0)
                        elif R6 > Decimal(150.0):
                            R6 = Decimal(150.0)

                        # calcul contributions
                        c1 = Decimal(0.0535) * R1
                        c2 = Decimal(0.0115) * R2
                        c3 = Decimal(0.0371) * R3
                        c4 = Decimal(0.0246) * R4
                        c5 = Decimal(0.0115) * R5
                        c6 = Decimal(0.0096) * R6

                        # print("{0:.3g}, {1:.3g},{2:.3g},{3:.3g},{4:.3g},{5:.3g}".format(c1, c2, c3, c4, c5, c6), i, actifs.annee)

                        valeur_calcul = (c1 + c2 + c3 + c4 + c5 + c6)

                        if valeur_calcul > 10:
                            scores[i] = 10
                        elif valeur_calcul < 0:
                            scores[i] = 0
                        else:
                            scores[i] = valeur_calcul

                        # scores[i] = (c1 + c2 + c3 + c4 + c5 + c6)
                    except Exception as e:
                        print('Acheteur.Scoring:', e, " i = ", i)
                return scores
        else:
            return {0: 0}
        ##########################################################
        #     # Décomposition du calcul de score pour la maintenance
        ##########################################################

    # Détection de données financières disponibles
    def has_financial_data(self,acheteur, annee):
        return any([
            acheteur.actifc_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).exists(),
            acheteur.passifc_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).exists(),
            acheteur.resultatc_set.filter(annee__annee__in=[annee, annee - 1, annee - 2]).exists()
        ])
  
    # @@@@@@@@@@@@@@ Calcul du score financier (par type de bilan)
    # Fonction utilitaire : appliquer_contributions(...) communes aux trois bilans
    def appliquer_contributions(self,R1, R2, R3, R4, R5, R6):
        def borne(val, mini, maxi):
            return min(max(val, Decimal(mini)), Decimal(maxi))

        # Appliquer bornes
        R1 = borne(R1, 0, 100)
        R2 = borne(R2, 0, 200)
        R3 = borne(R3, -25, 100)
        R4 = borne(R4, 0, 100)
        R5 = borne(R5, -100, 100)
        R6 = borne(R6, -100, 150)

        # Coefficients
        c1 = Decimal("0.0535") * R1
        c2 = Decimal("0.0115") * R2
        c3 = Decimal("0.0371") * R3
        c4 = Decimal("0.0246") * R4
        c5 = Decimal("0.0115") * R5
        c6 = Decimal("0.0096") * R6

        score = c1 + c2 + c3 + c4 + c5 + c6
        return float(min(10, max(0, score)))
        # return score
    
    # Bilan Classique
    def score_bilan_classique(self,acheteur, annee):
        o = Decimal(0.0)

        try:
            actif = acheteur.actifc_set.get(annee__annee=annee)
            passif = acheteur.passifc_set.get(annee__annee=annee)
            resultat = acheteur.resultatc_set.get(annee__annee=annee)

            # Récupération des valeurs
            ffi = resultat.frais_fin_charges_assi or o
            ebe = resultat.excedent_brut_ex() or o
            ca = resultat.ca() or o
            va = resultat.valeur_ajoutee() or o

            cred_disp_net = (
                (actif.clients_et_cptes_rattaches or o) +
                (actif.autres_creances or o) +
                (actif.valeurs_a_encaisser or o) +
                (actif.banques_cheques_postaux_caisse or o)
            )
            tresorerie = (actif.banques_cheques_postaux_caisse or o) - (actif.valeurs_a_encaisser or o)

            cours_permanent = passif.total_I_II()
            total_passif = passif.total_general()
            dettes_ct = passif.total_III() + passif.total_IV()

            caj = ca / Decimal(360.0) if ca != o else o

            try:
                fdr = (actif.banques_cheques_postaux_caisse or o) - passif.total_I_II()
            except:
                fdr = (actif.banques_cheques_postaux_caisse or o) if passif.total_I_II() == 0 else -passif.total_I_II()

            # Ratios
            R1 = (ffi / ebe * 100) if ebe != o else o
            R2 = (cred_disp_net / dettes_ct * 100) if dettes_ct != o else o
            R3 = (cours_permanent / total_passif * 100) if total_passif != o else o
            R4 = (va / ca * 100) if ca != o else o
            R5 = (tresorerie / caj) if caj != o else o
            R6 = (fdr / caj) if caj != o else o

            return self.appliquer_contributions(1, 2, 3, 4, 5, 6)
                    # return self.appliquer_contributions(R1, R2, R3, R4, R5, R6)

        except Exception as e:
            print("Erreur bilan classique:", e)
            return 0

    # Bilan Syscohada
    def score_bilan_syscohada(self,acheteur, annee):
        o = Decimal(0.0)

        try:
            actifsys = acheteur.actifs_set.get(annee__annee=annee)
            passifsys = acheteur.passifs_set.get(annee__annee=annee)
            resultatsys = acheteur.resultats_set.get(annee__annee=annee)

            ffi = resultatsys.charges_financieres_assimilees or o
            ebe = resultatsys.excedent_brute_exploitation() or o
            ca = resultatsys.chiffre_affaires() or o
            va = resultatsys.valeur_ajoutee() or o

            cred_disp_net = actifsys.creances_emplois_similaires() + actifsys.total_tresorerie_equivalents()
            tresorerie = actifsys.total_actif_circulant() or o

            cours_permanent = passifsys.total_ressources_stables() or o
            total_passif = passifsys.total_passifs() or o
            CT_debts = passifsys.total_passifs_courants() + passifsys.total_tresorerie_equivalents()

            try:
                fdr = passifsys.total_capitaux_propres_ressources_similaires() - actifsys.total_actif_immobilise()
            except:
                try:
                    fdr = passifsys.total_capitaux_propres_ressources_similaires()
                except:
                    try:
                        fdr = -actifsys.total_actif_immobilise()
                    except:
                        fdr = o

            caj = ca / Decimal(360.0) if ca != o else o

            R1 = (ffi / ebe * 100) if ebe != o else o
            R2 = (cred_disp_net / CT_debts * 100) if CT_debts != o else o
            R3 = (cours_permanent / total_passif * 100) if total_passif != o else o
            R4 = (va / ca * 100) if ca != o else o
            R5 = (tresorerie / caj) if caj != o else o
            R6 = (fdr / caj) if caj != o else o

            return self.appliquer_contributions(R1, R2, R3, R4, R5, R6)

        except Exception as e:
            print("Erreur bilan Syscohada:", e)
            return 0

    # Bilan Anglais
    def score_bilan_anglais(self,acheteur, annee):
        o = Decimal(0.0)

        try:
            actifang = acheteur.actifa_set.get(annee__annee=annee)
            passifang = acheteur.passifa_set.get(annee__annee=annee)
            resultatang = acheteur.resultata_set.get(annee__annee=annee)

            ffi = resultatang.frais_financier or o
            ebe = resultatang.benefice_avant_cout_financier_impots() or o
            ca = resultatang.produits_activites_ordinaires or o
            va = resultatang.marge_brut() or o

            cred_disp_net = (actifang.caisses_banques or o) + (actifang.creances_commerciales_autres_creances or o)
            tresorerie = actifang.caisses_banques or o

            cours_permanent = passifang.total_passif_long_terme() + passifang.total_fonds_propres()
            total_passif = passifang.Total_fonds_propres_passif()

            CT_debts = (passifang.decouvert_bancaire or o) + (passifang.dettes_commerciales_autres_dettes or o) + (passifang.impots or o)

            try:
                fdr = (passifang.total_passif_long_terme() + passifang.total_fonds_propres()) - (
                    (actifang.creances_commerciales_autres_creances or o) + (actifang.caisses_banques or o)
                )
            except:
                try:
                    fdr = passifang.total_passif_long_terme() + passifang.total_fonds_propres()
                except:
                    try:
                        fdr = -((actifang.creances_commerciales_autres_creances or o) + (actifang.caisses_banques or o))
                    except:
                        fdr = o

            caj = ca / Decimal(360.0) if ca != o else o

            R1 = (ffi / ebe * 100) if ebe != o else o
            R2 = (cred_disp_net / CT_debts * 100) if CT_debts != o else o
            R3 = (cours_permanent / total_passif * 100) if total_passif != o else o
            R4 = (va / ca * 100) if ca != o else o
            R5 = (tresorerie / caj) if caj != o else o
            R6 = (fdr / caj) if caj != o else o

            # return R1

            return self.appliquer_contributions(R1, R2, R3, R4, R5, R6)

        except Exception as e:
            print("Erreur bilan Anglais:", e)
            return 0


    # Dispatcher selon le type de bilan
    def calculer_score_financier(self,acheteur, annee):
        scores = {}
        type_bilan = acheteur.type_bilan
        # type_bilan = "Syscohada"
        if not type_bilan:
            return {0: 0}

        for i in range(3):
            try:
                # if type_bilan.type_bilan == "Classique":
                if type_bilan == "Classique":
                    scores[i] = self.score_bilan_classique(acheteur, annee - i)
                elif type_bilan == "Syscohada":
                # elif type_bilan.type_bilan == "Syscohada":
                    scores[i] = self.score_bilan_syscohada(acheteur, annee - i)
                elif type_bilan == "Anglais":
                # elif type_bilan.type_bilan == "Anglais":
                    scores[i] = self.score_bilan_anglais(acheteur, annee - i)
                    # scores[i] = self.score_bilan_anglais(acheteur, annee - i)
                else:
                    scores[i] = 0
            except Exception as e:
                print("Erreur score financier:", e)
                scores[i] = 0
        return scores

            ##########################################################
        #     # FIN Décomposition du calcul de score pour la maintenance
        ##########################################################
   # @@@@@@@@@@@@@@ FIN Calcul du score financier (par type de bilan)

   # Score basé sur les métadonnées de l’acheteur
    def scoreSansBilan(self,acheteur, annee):
        from datetime import datetime
        from decimal import Decimal
           # @@@@@@@@@@@@@@@@@@@@@@@Calcul du score sans bilan
        score_sans_bilan = Decimal('0')
            # Récupération du score de la forme juridique
        de = (acheteur.donneesenregistrement_set.all()
                      .order_by('-date_creation').first())
        forme_juridique = de.forme_juridique_ref if de else None
        grille_forme_jur = forme_juridique.grille if forme_juridique else 0

            # Récupération du score des locaux
        grille_local = acheteur.local.grille if acheteur.local else 0

            # Récupération du score de l'expérience paiement
        grille_experience_paiement = acheteur.experience_paiement.grille if acheteur.experience_paiement else 0
        try:
            grille_age = calculer_grille_age(acheteur.date_creation)
                # return JsonResponse({"grille": grille})
        except ValueError as e:
                pass

            # Récupération du score des codes naces
        codes_naces = acheteur.naces_codes.all()
        grille_naces = 0
        for code_nace in codes_naces:
            grille_naces += code_nace.grille or 0

        score_sans_bilan = Decimal(str(grille_forme_jur)) + Decimal(str(grille_local))  + Decimal(str(grille_experience_paiement))  + Decimal(str(grille_age))  + Decimal(str(grille_naces)) 

        return score_sans_bilan
    # Fonction finale pour le scoring(Avec et sans bilan)
 
    # Nouvelles méthodes de calcul du scoring  
    def autoNew(self, acheteur, annee):
        if not acheteur:
            return {0: 0}

        score_sans_bilan = self.scoreSansBilan(acheteur,annee)

        if not self.has_financial_data(acheteur, annee):
            # Pas de données financières, on retourne juste le score sans bilan pour année 0
            return {0: min(max(score_sans_bilan, 0), 10)}

        scores_financiers = self.calculer_score_financier(acheteur, annee)
        scores_avec_sans_bilan = {}

        for annee_clef, score_financier in scores_financiers.items():
            total = Decimal(str(score_financier)) + Decimal(str(score_sans_bilan)) 
            # bornes entre 0 et 10
            total = min(max(total, 0), 10)
            scores_avec_sans_bilan[annee_clef] = total

        return scores_avec_sans_bilan

##########################################################
# FIN SCORING 
##########################################################










class CredendoCommande(models.Model):
    email_id = models.CharField(max_length=255, unique=True)  # ID unique du mail
    reference = models.CharField(max_length=255)  # Our references
    internal_bp_id = models.CharField(max_length=255)  # Internal BP id
    nom = models.CharField(max_length=255)  # Name(s)
    identifiants = models.TextField(blank=True, null=True)  # Identifier(s)
    rue = models.TextField()  # Street
    ville = models.CharField(max_length=100)  # City
    pays = models.CharField(max_length=100)  # Country
    remarque = models.TextField(blank=True, null=True)  # Remark on the request
    priorite = models.CharField(max_length=50)  # Priority
    texte_complet = models.TextField()  # Texte après "Priority"
    montant = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)  # Montant demandé
    devise = models.CharField(max_length=10, blank=True, null=True)  # Devise
    date_reception = models.DateTimeField()  # Date de réception du mail

    def __str__(self):
        return f"{self.reference} - {self.nom} - {self.pays}"
