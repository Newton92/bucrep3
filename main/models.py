from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import datetime
from decimal import Decimal
import time
from main.utilitaires.constantes import *
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model

# User = get_user_model()

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
        help_text=_('The address of the user.')
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
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
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
        









# === Models Acheteurs et compagnies === #

class ModeleRapport(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.code and self.libelle else _("Modèle sans informations complètes")

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de rapport")
        verbose_name_plural = _("Modèles de rapport")



class ModeleAlarme(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.code and self.libelle else _("Modèle sans informations complètes")

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle d'alarme")
        verbose_name_plural = _("Modèles d'alarme")



class ModeleBilan(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.code and self.libelle else _("Modèle sans informations complètes")

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de bilan")
        verbose_name_plural = _("Modèles de bilan")



class ModeleBail(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.code and self.libelle else _("Modèle sans informations complètes")

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de bail")
        verbose_name_plural = _("Modèles de bail")
        
   
        
class ModeleNotation(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.code and self.libelle else _("Modèle sans informations complètes")

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de notation")
        verbose_name_plural = _("Modèles de notation")




class ModeleAvisCommercial(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.code and self.libelle else _("Modèle sans informations complètes")

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle d'avis commercial")
        verbose_name_plural = _("Modèles d'avis commercial")



class ModeleRelationEntreprise(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.code and self.libelle else _("Modèle sans informations complètes")

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de relation entreprise")
        verbose_name_plural = _("Modèles de relation entreprise")



class ModeleInformationNotationEntreprise(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.code and self.libelle else _("Modèle sans informations complètes")

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle d'information sur notation entreprise")
        verbose_name_plural = _("Modèles d'information sur notation entreprise")



class ModeleComportementPaiement(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.code and self.libelle else _("Modèle sans informations complètes")

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de comportement de paiement")
        verbose_name_plural = _("Modèles de comportement de paiement")



class ModeleComportementJugement(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.libelle}" if self.code and self.libelle else _("Modèle sans informations complètes")

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de comportement de jugement")
        verbose_name_plural = _("Modèles de comportement de jugement")
        











##########################################################
##########################################################
# Debut Modules Portefeuille  & Client
##########################################################
##########################################################  




class Client(models.Model):
    nom = models.CharField(
        max_length=255,
        verbose_name=_("Nom"),
        help_text=_("Nom du client.")
    )
    email = models.EmailField(
        unique=True,
        verbose_name=_("Email"),
        help_text=_("Adresse email du client.")
    )
    telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Téléphone"),
        help_text=_("Numéro de téléphone du client.")
    )
    adresse = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Adresse"),
        help_text=_("Adresse postale du client.")
    )
    date_inscription = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date d'inscription"),
        help_text=_("Date et heure d'inscription du client.")
    )
    actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si le client est actif.")
    )

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")

    def __str__(self):
        return self.nom





class Portefeuille(models.Model):
    client = models.ForeignKey(
        'Client',
        on_delete=models.CASCADE,
        related_name='portefeuilles_client',
        verbose_name=_("Client"),
        help_text=_("Client propriétaire du portefeuille.")
    )
    nom = models.CharField(
        max_length=255,
        verbose_name=_("Nom"),
        help_text=_("Nom du portefeuille.")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création du portefeuille.")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour"),
        help_text=_("Date et heure de la dernière mise à jour du portefeuille.")
    )

    class Meta:
        verbose_name = _("Portefeuille")
        verbose_name_plural = _("Portefeuilles")

    def __str__(self):
        return f"{self.nom} - {self.client.nom}"
    
    
    

class PortefeuilleClient(models.Model):
    CATEGORY_CHOICES = [
        ('grande', 'Grande entreprise'),
        ('pme', 'Petite et moyenne entreprise'),
        ('autre', 'Autre'),
    ]

    portefeuille = models.ForeignKey('Portefeuille', on_delete=models.CASCADE)
    acheteur = models.ForeignKey('Acheteur', on_delete=models.CASCADE)
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name=_("Catégorie"),
        help_text=_("Catégorie de l'acheteur dans le portefeuille.")
    )

    class Meta:
        verbose_name = _("Portefeuille client")
        verbose_name_plural = _("Portefeuilles client")
        unique_together = ('portefeuille', 'acheteur')

    def __str__(self):
        return f"{self.acheteur.nom} - {self.get_categorie_display()}"







##########################################################
##########################################################
# Fin Modules Portefeuille
##########################################################
##########################################################  









##########################################################
##########################################################
# Debut Modules Acheteur
##########################################################
##########################################################    

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
        _("Activité Principale"),
        max_length=255,
        blank=True,
        help_text=_("Activité principale de l'entreprise")
    )

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
    
    

# Prevoir la gestion d'adresse multiple pour un acheteur 
# Ce qui veut dire que un acheteur peut avoir occuper plusieurs adresses
# il serait important de les recenser toutes 


##########################################################
##########################################################
# Debut Modules Acheteur
##########################################################
##########################################################    
    
    
    
    
    
    
    
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
        _("Capital émis"), max_digits=100, decimal_places=2, blank=True, null=True, help_text=_("Montant du capital émis")
    )
    publie = models.DecimalField(
        _("Capital publié"), max_digits=100, decimal_places=2, blank=True, null=True, help_text=_("Montant du capital publié")
    )
    libere = models.DecimalField(
        _("Capital libéré"), max_digits=100, decimal_places=2, blank=True, null=True, help_text=_("Montant du capital libéré")
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
        _("Pourcentage"), max_digits=100, decimal_places=2, blank=True, null=True, help_text=_("Pourcentage de détention d'actions")
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
    montant_credit_maximum = models.DecimalField(
        _("Capital émis"), max_digits=100, decimal_places=2, blank=True, null=True, help_text=_("Montant crédit maximum conseillée")
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
    recouvrement_de_dette_jugement_ref = models.ForeignKey(
        'ModeleComportementJugement', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Référence sur les locaux")
    )
    
    comportement_de_paiement = models.CharField(
        max_length=255, 
        choices=LIEN_COMPORTEMENT_PAIEMENT_CHOICE, 
        default="--------",
        verbose_name=_("Comportement de paiement")
    )
    comportement_de_paiement_ref = models.ForeignKey(
        'ModeleComportementPaiement', null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Référence sur les locaux")
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
        return f"Conseils pour {self.acheteur}"

    class Meta:
        verbose_name = _("Conseil")
        verbose_name_plural = _("Conseils")


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
# Fin Modules Bilan Anglais
##########################################################
##########################################################
class ActifA(models.Model):
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

    biens_installations_equipements = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Biens, installations et équipements"))
    inventaire = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    creances_commerciales_autres_creances = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Créances commerciales et autres"))
    actif_impots_courant = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Actif d'Impôts courant"))
    caisses_banques = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Caisse et banque"))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='actifa_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return _("Actif bilan anglais : ") + str(self.id) + ". " + str(self.acheteur) + " (" + str(self.annee) + ")"

    class Meta:
        verbose_name = _("Actif bilan anglais")
        verbose_name_plural = _("Actifs bilans anglais")
        
        
    #  Liste des methodes utiles pour ce model
    
    #  total_actifs_non_courants
    #  total_actif_circulant
    #  total_actif_circulant
        
        
        
class PassifA(models.Model):
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

    capital_reserves = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Capital et Réserves"))
    capital_declare = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Capital déclaré"))
    benefices_non_distribues = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Bénéfices non distribués"))

    pret_bancaire = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Prêt bancaire"))
    compte_courant_administrateurs = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Compte courant des administrateurs"))

    dettes_commerciales_autres_dettes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dettes commerciales et autres dettes"))
    decouvert_bancaire = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Découvert bancaire"))
    impots = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Impôts"))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='passifa_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return _("Passif bilan anglais : ") + str(self.id) + ". " + str(self.acheteur) + " (" + str(self.annee) + ")"

    class Meta:
        verbose_name = _("Passif bilan anglais")
        verbose_name_plural = _("Passifs bilans anglais")
        
        
    #  Liste des methodes utiles pour ce model
    
    #  total_fonds_propres
    #  total_passif_long_terme
    #  total_passif_circulant
    #  total_passif
    #  Total_fonds_propres_passif
        
        
        
        
class ResultatA(models.Model):
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

    produits_activites_ordinaires = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('Produits des activités ordinaires'))
    ventes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    charges_exploitation = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Charges d'exploitation"))
    frais_vente_generaux_administratifs = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('Frais de vente, généraux et administratifs'))
    autres_revenus = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    frais_financier = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    charge_impot_sur_revenu = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Charge d'impôt sur le revenu"))
    autres_elements_resultat_global = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('Autres éléments du résultat global'))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='resultata_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return _("Résultat bilan anglais : ") + str(self.id) + ". " + str(self.acheteur) + " (" + str(self.annee) + ")"

    class Meta:
        verbose_name = _("Résultat bilan anglais")
        verbose_name_plural = _("Résultat bilans anglais")
        
        
    #  Liste des methodes utiles pour ce model
    
    #  marge_brut
    #  resultat_exploitation
    #  benefice_avant_cout_financier_impots
    #  resultat_avant_impots
    #  benefice_annee
    #  benefices_non_distribues
    
    
    
    
    
#  Calcul des ratios

#  init(self, acheteur, annee)

#  solvabilite
#  autonomiefin
#  rendement_capitaux_propres
#  taux_marge_net
#  liquidite_generale
#  jour_recouvrement_moyen
#  jour_paiement_moyen
#  taux_rotation_creance
#  taux_rotation_stock
#  taux_rotation_actif
#  ratio_endettement1
#  ratio_endettement2
#  passif_cour_terme
#  ratios_couverture_interet
#  ratios_liquidite_general
#  ratios_liquidite2
#  ratio_g_score_fin
#  ratio_endettement_g_score




##########################################################
##########################################################
# Fin Modules Bilan Anglais
##########################################################
##########################################################








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

    capital_souscrit_non_app = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Capital sousc. non app"))
    frais_recherche_developpement = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Frais recherche developpement"))
    brevet_licence_logiciels = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Brevet licence logiciels"))
    fonds_commercial = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Fonds commercial"))
    autres_immobilisations_incorporelles = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres immobilisations incorporelles"))

    terrains = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Terrains"))
    constructions = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Constructions"))
    materiels_et_outils = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Materiels et outils"))
    materiel_de_transport = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Materiel de transport"))
    autres_immos_corp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres immos corp"))
    immos_en_cours = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Immos en cours"))
    avances_et_acptes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Avances et acptes"))

    participations = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Participations"))
    prets = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Prets"))
    autres = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres"))

    stocks_mp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Stocks mp"))
    stocks_encours_mp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Stocks encours mp"))
    stocks_pf = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Stocks pf"))
    stocks_encours_pf = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Stocks encours pf"))
    stocks_encours_services = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Stocks encours services"))
    stocks_mses = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Stocks mses"))

    avances_acptes_verses = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Avances acptes verses"))
    clients_et_cptes_rattaches = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Clients et cptes rattaches"))
    autres_creances = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres creances"))

    valeurs_a_encaisser = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Valeurs a encaisser"))
    banques_cheques_postaux_caisse = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Banques cheques postaux caisse"))

    cca = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Cca"))
    charges_a_repartir_et_frais_etablissement = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Charges a repartir et frais etablissement"))
    primes_de_rbt = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Primes de rbt"))
    eca = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Eca"))

    eene = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Eene"))
    effectif = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Effectif"))
    amortissements = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Amortissements"))
    provisions_stocks = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provisions stocks"))
    provisions_creances = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provisions creances"))
    provisions_vmp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provisions vmp"))

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

    class Meta:
        verbose_name = _("Actif bilan classique")
        verbose_name_plural = _("Actifs bilans classiques")
        
        
    #  Liste des methodes utiles pour ce model
    
    #  elements_incorporels
    #  elements_corporels
    #  elements_financiers
    #  total_I
    #  stocks
    #  creances
    #  disponibilites_vmp
    #  total_II
    #  compte_regul
    #  total_III
    #  general_total
    
    
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

    capital_social = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Capital social"))
    primes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Primes"))
    ecarts_de_reevaluation = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Eca"))
    reserve = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Reserve"))
    report_a_nouveau = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Report a nouveau"))
    resultat_exercice = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Resultat exercice"))
    subv_invest = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Subventions investies"))
    provision_regl = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provision regle"))

    emprunts = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Emprunts"))
    dette_credit_bail_contrat_assimile = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Credit lease debts and related contracts"))
    dettes_financiere_diverses = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dettes financiere diverses"))
    provision_financiere_risque_charge = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provision financiere risque charge"))

    dettes_fournisseurs_divers = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dettes fournisseurs divers"))
    avance_et_acomptes_recu = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Avance et acomptes recu"))
    dettes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dettes"))
    dettes_fiscales_sociales = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dettes fiscales sociales"))
    autres_dettes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres dettes"))

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

    vente_de_mdses = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Vente de mdses"))
    ventes_de_produits_fabriques = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Ventes de produits fabriques"))
    travaux_services_vendus = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Travaux services vendus"))
    produit_accessoires = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Produit accessoires"))
    production_imblise = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Production imblise"))

    subventions_exploitations = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Subventions exploitations"))
    production_stockee = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Production stockee"))
    reprises_de_provision = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Reprises de provision"))
    transferts_charges = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Transferts charges"))
    autres_produits = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres produits"))

    achat_mdses = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Achat mdses"))
    variation_stock_mdses = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Variation stock mdses"))

    achat_mp_autres_appro = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Achat mp autres appro"))
    var_stk_mp_app = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Var stk mp app"))
    autres_achats = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres achats"))
    variation_de_stocks_autres_appro = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Variation de stocks autres appro"))
    transports = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Transports"))
    services_ext = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Services ext"))
    impots_taxes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Impots taxes"))
    autres_charges_valeur_ajoutee = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres charges valeur ajoutee"))

    charges_personnel = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Charges personnel"))

    dotation_aux_amorts = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dotation aux amorts"))
    dotation_aux_provisions = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dotation aux provisions"))
    autres_charges_excedent_brute = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres charges excedent brute"))

    revenus_fin_assimiles = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Revenus fin assimiles"))
    prof_vmp_et_cre_actif_immo = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Prof vmp et cre actif immo"))
    interets_produit_assim = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Interets produit assim"))
    reprise_prov_et_transfert = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Reprise prov et transfert"))
    diff_positive_de_change = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Diff positive de change"))
    prod_nets_cessions_vmp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Prod nets cessions vmp"))

    dap = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dot. aux prov. & depreciations"))
    frais_fin_charges_assi = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Frais fin. & chrges assimilées"))
    diff_negatives_de_change = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Diff negatives de change"))
    ch_nettes_cessions_vmp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Ch nettes cessions vmp"))

    sur_op_gestion_prod_except = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Sur op gestion prod except"))
    sur_op_en_capital_prod_except = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Sur op en capital prod except"))
    reprise_prov_transfert = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Reprise prov transfert"))

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

    class Meta:
        verbose_name = _("Résultat bilan classique")
        verbose_name_plural = _("Résultats bilans classiques")
        
        
    #  Liste des methodes utiles pour ce model
    
    #  ca
    #  total_I
    #  marge_brute
    #  valeur_ajoutee
    #  excedent_brut_ex
    #  resultat_exploitation
    #  financier_total_I
    #  financier_total_II
    #  resultat_financier
    #  resultat_courant_avant_impots
    #  excep_total_I
    #  excep_total_II
    #  resultat_excep
    #  resultat_exercice
    





    
#  Calcul des ratios

#  init(self, acheteur, annee)

#  fonds_de_roulement
#  fdr_normati
#  autonomie_fin
#  liquidite_reduite
#  liquidite_immediat
#  caf
#  caf_ht
#  rentabilite_economique
#  rentabilite_fin
#  rentabilite_de_loutil_de_production
#  couverture_des_frais_financiers
#  rotation_des_stock_de_mp
#  rotation_des_stock_de_pf
#  rotation_des_stock_de_marchandises
#  rotation_des_stock_de_services
#  credit_clients
#  credits_fournisseurs



##########################################################
##########################################################
# Fin Modules Bilan Classique
##########################################################
##########################################################








##########################################################
##########################################################
# Debut Modules Bilan Bancaire
##########################################################
##########################################################

class Assets(models.Model):
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

    caisse = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Caisse"))
    # ASSETS
    # At Sight
    banques_centrales = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('-Banques centrales'))
    tresorerie_cpp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('-Trésorerie, CCP'))
    autres_ets_credit = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('-Autres établissements de crédit'))

    a_terme = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('A Terme'))

    # Claims on Customers
    ## Commercial paper portofolio
    credits_campagne = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('-Crédits de campagne'))
    credits_ordinaire = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('-Crédits ordinaires'))
    ## Other Customer Contests
    credits_campagne_acc = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('-Crédits de campagne'))
    credits_ordinaire_acc = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('-Crédits ordinaires'))

    creances_ordinaires = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('Créances ordinaires'))
    affacturage = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('Affacturage'))

    titres_placement = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('TITRES DE PLACEMENT'))
    immobilisation_fin = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('IMMOBILISATIONS FINANCIÈRES'))
    operation_credit_bail = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('OPÉRATIONS DE CRÉDIT-BAIL ET ASSIMILÉES'))
    immobilisation_incorporelle = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('IMMOBILISATIONS INCORPORELLES'))
    immobilisation_corporelle = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('IMMOBILISATIONS CORPORELLES'))
    actionnaire_ou_associe = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('ACTIONNAIRES OU ASSOCIÉS'))
    autres_actifs = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('AUTRES ACTIFS'))
    comptes_commande_divers = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('COMPTES DE COMMANDES ET DIVERS'))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='assets_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return _("Actif bilan bancaire : ") + str(self.id) + ". " + str(self.acheteur) + " (" + str(self.annee) + ")"

    class Meta:
        verbose_name = _("Actif bilan bancaire")
        verbose_name_plural = _("Actifs bilans bancaires")
        
        
    #  Liste des methodes utiles pour ce model
    
    #  pret_interbancaire
    #  a_vue
    #  creance_sur_la_clientele
    #  porteuille_papier_commercial
    #  autres_concours_clients
    #  total_assets




class Liabilities(models.Model):
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

    # Interbank debt
    tresorerie_ccp = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('-Trésorerie, CCP'))
    autres_etablissement_credit = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('-Autres établissements de crédit'))
    ## At term
    a_terme = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('A Terme'))
    # Debts Owed To Customers
    comptes_epargne_court_terme = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Comptes d'épargne à court terme"))
    comptes_epargne_terme = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Comptes d'épargne à terme"))
    bons_caisse = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Bons de caisse"))
    autres_dette_a_vue = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres dettes à vue"))
    autres_dette_a_terme = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres dettes à terme"))

    titres_creance_autres_dettes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("TITRES DE CRÉANCE AUTRES DETTES"))
    compte_dordre_divers = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("COMPTES D'ORDRE ET DIVERS"))
    provision_pour_risque_charge = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("PROVISIONS POUR RISQUES ET CHARGES"))
    provision_reglementee = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("PROVISIONS RÉGLEMENTÉES"))
    emprunt_subordonne_tire_emis = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("EMPRUNTS SUBORDONNÉS ET TITRES ÉMIS"))
    subventions_investissement = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("SUBVENTIONS D'INVESTISSEMENT"))
    fonds_affecte = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("FONDS AFFECTÉS"))
    fonds_pour_risque_bancaire_generaux = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("FONDS POUR RISQUES BANCAIRES GÉNÉRAUX"))
    capital_ou_dotation = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("CAPITAL OU DOTATIONS"))
    primes_liees_reserve_capital = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("PRIMES LIÉES AUX RÉSERVES DE CAPITAL"))
    ecarts_reevaluation = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("ÉCARTS DE RÉÉVALUATION"))
    benefices_non_distribue = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("BÉNÉFICES NON DISTRIBUÉS (+/-)"))
    resultat_net_exercie = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("RÉSULTAT NET DE L'EXERCICE (+/-)"))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='liabilities_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return _("Passif bilan bancaire : ") + str(self.id) + ". " + str(self.acheteur) + " (" + str(self.annee) + ")"

    class Meta:
        verbose_name = _("Passif bilan bancaire")
        verbose_name_plural = _("Passifs bilans bancaires")
        
        
    #  Liste des methodes utiles pour ce model
    
    #  dette_interbancaire
    #  a_vue
    #  dette_envers_clientelle
    #  total_passif
    
    
  
    
class OffBalanceSheet(models.Model):
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

    en_faveur_des_ets_credit = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("En faveur des établissements de crédit"))
    en_faveur_clientele = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("En faveur de la clientèle"))
    pour_compte_ets_credit = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Pour le compte des établissements de crédit"))
    pour_compte_clientele = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('Pour le compte de la clientèle'))

    engagement_sur_titre = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_('ENGAGEMENTS SUR TITRES'))
    recu_ets_credit = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Reçus d'établissements de crédit"))
    recu_ets_credit2 = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Reçus d'établissements de crédit"))
    recu_clientele = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Reçus de la clientèle"))
    engagement_sur_titre2 = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("ENGAGEMENTS SUR TITRES"))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='offbalance_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return _("Hors bilan bancaire : ") + str(self.id) + ". " + str(self.acheteur) + " (" + str(self.annee) + ")"

    class Meta:
        verbose_name = _("Hors Bilan bancaire")
        verbose_name_plural = _("Hors Bilans bancaires")
        
        
    #  Liste des methodes utiles pour ce model
    
    #  engagement_donne
    #  engagement_financement
    #  engagement_de_garantie
    #  engagement_recu
    #  engagement_financement2
    #  engagement_de_garantie2
    
    
    
    
class Expenses(models.Model):
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

    interet_charges_assimilee_dette_interbancaire = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("Intérêts et charges assimilées sur dettes interbancaires"))
    interet_charge_assimilee_dette_clientele = models.DecimalField(max_digits=100, decimal_places=2, help_text="", verbose_name=_("Intérêts et charges assimilées sur dettes envers la clientèle"))
    interet_charge_assimilee_titre_creance = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("Intérêts et charges assimilées sur titres de créances"))
    chargesc_compte_bloque_dactionnaire_emprunt_sub = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("Charges sur comptes bloqués d'actionnaires emprunts sur titres subordonnés"))
    autres_interets_charges_assimilee = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("Autres Intérêts et charges assimilées"))
    charges_sur_op_credit_bail_assimile = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("CHARGES SUR OPÉRATIONS DE CRÉDIT-BAIL ET ASSIMILÉES"))
    commissions = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("COMMISSIONS"))

    charges_sur_titre_placement = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text=_("Charges sur titres de placement"), verbose_name=_("Charges sur titres de placement"))
    charges_sur_operation_change = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text=_("Charges sur titres de placement"), verbose_name=_("Charges sur opérations de change"))
    charges_sur_operation_hors_bilan = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("Charges sur opérations hors bilan"))
    frais_divers_exploitation_bancaire = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("FRAIS DIVERS D'EXPLOITATION BANCAIRE"))
    achat_marchandises = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("ACHAT DE MARCHANDISES"))
    stocks_vendus = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("STOCKS VENDUS"))
    variations_stocks_marchanides = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("VARIATIONS DES STOCKS DE MARCHANDISES"))
    frais_personnel = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Frais de personnel"))

    autres_frais_generaux = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres frais généraux"))
    dotations_amortissement_provision_immobilisation = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("DOTATIONS AUX AMORTISSEMENTS ET PROVISIONS SUR IMMOBILISATIONS"))
    solde_perte_creance_hors_bilan = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("SOLDE DES PERTES SUR CRÉANCES ET HORS BILAN"))
    excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("EXCÉDENT DES DOTATIONS SUR LES REPRISES DU FONDS POUR RISQUES BANCAIRES GÉNÉRAUX"))
    charges_exceptionnelle = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("LES CHARGES EXCEPTIONNELLES"))
    pertes_exercice_anterieurs = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("PERTES SUR EXERCICES ANTÉRIEURS"))
    impot_sur_revenu = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("IMPÔTS SUR LE REVENU"))
    total_charges = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("TOTAL DES CHARGES"))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='expenses_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return _("Dépense bilan bancaire : ") + str(self.id) + ". " + str(self.acheteur) + " (" + str(self.annee) + ")"

    class Meta:
        verbose_name = _("Dépense bilan bancaire")
        verbose_name_plural = _("Dépenses bilans bancaires")
        
        
    #  Liste des methodes utiles pour ce model
    
    #  interet_charges_assimilee
    #  charge_sur_operation_financiere
    #  frais_generaux_dexploitation
    #  prestation
    #  total_charges
    
    
    

class Products(models.Model):
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

    interets_produit_assimile_sur_pret_avance_interbancaire = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("Intérêts et produits assimilés sur prêts et avances interbancaires"))
    ineterets_produit_assimile_pret_avance_clientele = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("Intérêts et produits assimilés sur prêts et avances à la clientèle"))
    interet_produit_sur_titre_dinvestissement = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Intérêts et produits assimilés sur titres d'investissement"))
    revenu_gains_titre_pret_titre_subordonne = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("Revenus et gains sur titres de prêts et titres subordonnés émis"))

    autres_interets_produits_assimiles = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres intérêts et produits assimilés"))
    produits_leansing_operation_connexes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("PRODUITS DE LEASING ET OPÉRATIONS CONNEXES "))
    commissions = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("COMMISSIONS"))

    revenus_titre_negociable = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Revenus de titres négociables"))
    dividendes_produits_assimiles = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dividendes et produits assimilés"))
    revenus_operation_de_change = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Revenus d'opérations de change"))
    produits_opeations_hors_bilan = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("Produits des opérations hors bilan"))

    produits_bancaire_divers = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("PRODUITS BANCAIRES DIVERS"))
    marges_vente = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("MARGES DE VENTE"))
    ventes_marchandises = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("VENTES DE MARCHANDISES"))
    variation_stocks_marchandises = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("VARIATION DES STOCKS DE MARCHANDISES"))
    produit_dexploitation_generale = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("PRODUITS D'EXPLOITATION GÉNÉRALE"))

    reprise_damortissement_provisions_sur_immobilisation = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("REPRISES D'AMORTISSEMENTS ET DE PROVISIONS SUR IMMOBILISATIONS"))
    solde_resultat_correction_valeur_sur_creance_hors_bilan = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("SOLDE DU RÉSULTAT DES CORRECTIONS DE VALEUR SUR CRÉANCES ET HORS BILAN"))
    excedent_reprise_fonds_pour_risque_bancaire_generaux = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("EXCÉDENT DES REPRISES DU FONDS POUR RISQUES BANCAIRES GÉNÉRAUX"))

    produits_exceptionnels = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("PRODUITS EXCEPTIONNELS"))
    benefice_sur_exercice_anterieur = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("BÉNÉFICES SUR EXERCICES ANTÉRIEURS"))
    perte = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, help_text="", verbose_name=_("PERTES"))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='product_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return _("Produit bilan bancaire : ") + str(self.id) + ". " + str(self.acheteur) + " (" + str(self.annee) + ")"

    class Meta:
        verbose_name = _("Produit bilan bancaire")
        verbose_name_plural = _("Produits bilans bancaires")
        
        
    #  Liste des methodes utiles pour ce model
    
    #  interet_produit_assimile
    #  revenu_dopeation_financiere
    #  total_produit

##########################################################
##########################################################
# Fin Modules Bilan Bancaire
##########################################################
##########################################################








##########################################################
##########################################################
# Debut Modules Bilan SysCohada
##########################################################
##########################################################

class ActifS(models.Model):
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

    # Immobilisation incorporelles
    frais_developpement_prospection = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Frais de développement et prospection"))
    brevets_licences_logiciels = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Brevets, licences et logiciels"))
    droits_propriete_commerciale_baux = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Droits de propriété commerciale et baux"))
    autres_immo_incorporelles = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres immobilisations incorporelles"))

    # Immobilisations corporelles
    terrains = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Terrains"))
    dons_investissements_net = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dons et investissements nets"))
    batiments = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Bâtiments"))

    # dons_investissements_net2 = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    agencements_amenagements_installations = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Agencements, aménagements et installations"))
    materiel_mobilier_actif_biologiques = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Matériel, mobilier et actifs biologiques"))
    materiel_transport = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Matériel de transport"))

    # Avances et acomptes sur immobilisations
    avances_acompte_immobilisations = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Avances et acomptes sur immobilisations"))
    # Immobilisations financieres
    titres_participation = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Titres de participation"))
    autres_immobilisations_financieres = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres immobilisations financières"))

    # Actif circulant de HAO
    actif_circulant_hao = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Actif circulant HAO"))

    # Stock et En-cours (calcule)
    stock_encours = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Stock et en-cours"))

    # Creances et emplois similaires (calcule)
    fournisseurs_avances_versee = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Fournisseurs, avances versées"))
    clients = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Clients"))
    autres_creances = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres créances"))

    # Total de l'actif circulant
    valeurs_mobilieres_placement = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Valeurs mobilières de placement"))
    disponibilites = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Disponibilités"))
    banque_cheque_postal_caisse_assimiles = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Banque, chèque postal, caisse et assimilés"))

    # Total de la trésorerie et des équivalents de trésorerie
    ecart_conversion_actif = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Écart de conversion actif"))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='actifs_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return _("Actif bilan SYSCOHADA : ") + str(self.id) + ". " + str(self.acheteur) + " (" + str(self.annee) + ")"

    class Meta:
        verbose_name = _("Actif bilan SYSCOHADA")
        verbose_name_plural = _("Actifs bilans SYSCOHADA")
        
    #  Liste des methodes utiles pour ce model
    
    #  immobilisation_incorporelles
    #  immobilisations_corporelles
    #  immobilisations_financieres
    #  total_actif_immobilise
    #  creances_emplois_similaires
    #  total_actif_circulant
    #  total_tresorerie_equivalents
    #  total_actif
    
    
    



class PassifS(models.Model):
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

    capital = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Capital"))
    capital_non_appele_apporteurs = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Capital non appelé des apporteurs"))
    primes_liees_capital_social = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Primes liées au capital social"))
    ecart_reevaluation = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Écart de réévaluation"))
    reserves_indisponibles = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Réserves indisponibles"))
    reserves_libres = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Réserves libres"))
    report_nouveau = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Report à nouveau (+ ou -)"))
    resultat_net_exercice = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Résultat net de l'exercice (bénéfice + ou perte -)"))
    subventions_investissements = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Subventions d'investissement"))
    provisions_reglees = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provisions réglées"))

    # Total des capitaux propres et ressources similaires
    emprunts_dettes_financieres_diverse = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Emprunts et dettes financières diverses"))
    dettes_location_vente = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dettes de location-vente"))
    provisions_risques_charges = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provisions pour risques et charges"))

    # Total des dettes financières et ressources assimilées
    # Total des ressources stables
    passif_circulant_hao = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Passif circulant HAO"))
    clients_avances_recues = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Clients, avances reçues"))
    fournisseurs_exploitation = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Fournisseurs d'exploitation"))
    dettes_fiscales_sociales = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Dettes fiscales et sociales"))
    autres_dettes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Autres dettes"))
    provisions_risques_court_terme = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Provisions pour risques à court terme"))

    # Total des passifs courants
    banques_credit_escompte = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Banques, crédits d'escompte"))
    banques_etablissements_financiers_credit_caisse = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Banques, établissements financiers et crédits de caisse"))

    # Total de la trésorerie et des équivalents de trésorerie
    ecart_conversion_passif = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Écarts de conversion - Passif"))

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='passifs_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return _("Passif bilan SYSCOHADA : ") + str(self.id) + ". " + str(self.acheteur) + " (" + str(self.annee) + ")"

    class Meta:
        verbose_name = _("Passif bilan SYSCOHADA")
        verbose_name_plural = _("Passifs bilans SYSCOHADA")
        
        
    #  Liste des methodes utiles pour ce model
    
    #  total_capitaux_propres_ressources_similaires
    #  total_dettes_financieres_ressources_similaires
    #  total_ressources_stables
    #  total_passifs_courants
    #  total_tresorerie_equivalents
    #  total_passifs





class ResultatS(models.Model):
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
    

    ventes_marchandises_a = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Ventes de marchandises A (+)')
    achats_marchandises = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Achats de marchandises (-)')
    variation_stock_marchandises = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Variation des stocks de marchandises (-/+)')
    
    # Marge commerciale
    ventes_produits_manufactures = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Ventes de produits manufacturés B (+)')
    travaux_services_vendus_c = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Travaux, services vendus C (+)')
    produits_accessoires_d = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Produits accessoires D (+)')
    
    # Chiffre d'affaires
    production_stockee = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Production stockée (ou déstockage) (-/+)')
    production_immobilisee = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Production Immobilisée (+)')
    subvention_exploitation = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Subvention d\'exploitation (+)')
    autres_produits = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Autres produits (+)')
    transfert_charges_exploitation = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Transfert de charges d\'exploitation (+)')
    achats_matieres_premieres_fournitures_connexes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Achats de matières premières et fournitures connexes (-)')
    variation_stock_matieres_premieres_fournitures_connexes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Variation des stocks de matières premières et fournitures connexes (-/+)')
    autres_achats = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Autres achats (-)')
    variation_stock_autres_fournitures = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Variation des stocks d\'autres fournitures (-/+)')
    transport = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Transport (-)')
    services_exterieurs = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Services extérieurs (-)')
    impots_taxes = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Impots et taxes (-)')
    autres_depenses = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Autres dépenses (-)')
    
    # Valeur ajoutee
    frais_personnel = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Frais de personnel (-)')
    
    # Excedent brut d'exploitation
    reprise_depreciations_amortissements_provision_pertes_valeurs_p = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Reprises de dépréciations, amortissements, provisions et pertes de valeur (+)')
    reprise_depreciations_amortissements_provision_pertes_valeurs_m = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Reprises de dépréciations, amortissements, provisions et pertes de valeur (-)')
    
    # Resultat d'exploitation
    produits_financiers_assimiles = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Produits financiers et assimilés (+)')
    reprise_provision_perte_valeur = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Reprises sur provisions et pertes de valeur (+)')
    transfert_charges_financieres = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Transfert de charges financières (+)')
    charges_financieres_assimilees = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Charges financières et assimilées (-)')
    dotations_provisions_depreciations_financieres = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Dotations aux provisions et dépréciations financières (-)')
    
    # Resultat Financier
    # Resultat des activites ordinaires (XE + XF)
    produits_cession_immobilisations = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Produits des cessions d\'immobilisations (+)')
    autres_produits_hao = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Autres produits HAO (+)')
    valeur_comptable_cessions_actifs_immobilises = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Valeur comptable des cessions d\'actifs immobilisés (-)')
    autres_charges_hao = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Autres charges HAO (-)')
    
    # Resultats des activites ordinaires (Somme TN à RP)
    participation_travailleurs = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Participation des travailleurs (-)')
    charge_impot_revenu = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True, verbose_name='Charge d\'impôt sur le revenu (-)')
    #Resultat net (XG + XH + RQ +RS)
    
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name=_("Date de mise à jour")
    )
    
    created_by = models.ForeignKey('CustomUser', on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey('CustomUser', related_name='resultats_user_update', null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return "Résultat bilan SYSCOHADA : " + self.id + ". " +  self.acheteur + " (" + self.annee + ")"

    class Meta:
        verbose_name = _("Résultat bilan SYSCOHADA")
        verbose_name_plural = _("Résultats bilans SYSCOHADA")
        
        
    #  Liste des methodes utiles pour ce model
    
    #  marge_commerciale
    #  chiffre_affaires
    #  valeur_ajoutee
    #  excedent_brute_exploitation
    #  resultat_exploitation
    #  resultat_financier
    #  resultat_activites_ordinaires_xe
    #  resultat_activites_ordinaires_tn
    #  resultat_net
    
        
        
    #  Liste des methodes utiles pour ce model
    
    #  marge_commerciale
    #  chiffre_affaires
    #  valeur_ajoutee
    #  excedent_brute_exploitation
    #  resultat_exploitation
    #  resultat_financier
    #  resultat_activites_ordinaires_xe
    #  resultat_activites_ordinaires_tn
    #  resultat_net
    
    
# Ratios Bilan SYSCOHADA

#  fonds_de_roulement
#  besoin_fonds_de_roulement
#  position_net_de_tresorerie
#  cafsys
#  solvabilite
#  autonomie_financiere
#  benefice_net
#  turnover
#  benefice_net_chiffre_affaire
#  ebitda_chiffre_affaire
#  liquidite_general
#  liquidite_reduite
#  liquidite_immediate
#  jour_collecte_moyens
#  moyen_paiement
#  compte_debiteur
#  rotation_stock
#  rotation_actif
#  rotation_dendettement
#  rotation_dette_capitaux_propres
#  passif_court_terme_par_rapport_valeur_net
#  ratio_des_couverture_des_interets
#  ratio_courant
#  ratio_de_liquidite
#  ratio_financier
#  ratio_de_la_dette
#  ratio_de_liquidite2

##########################################################
##########################################################
# Fin Modules Bilan SysCohada
##########################################################
##########################################################





##########################################################
##########################################################
# Debut Modules Additifs
##########################################################
##########################################################
class Logo(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='logo',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au logo")
    )
    image = models.ImageField(
        _("Image"),
        upload_to='logos/',
        null=True,
        blank=True,
        help_text=_("Image du logo de l'entreprise")
    )
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description du logo")
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
        verbose_name = _("Logo")
        verbose_name_plural = _("Logos")

    def __str__(self):
        return f"Logo de {self.acheteur.nom}"




class TelephoneAcheteur(models.Model):
    telephone = models.TextField(
        max_length=100,
        verbose_name=_("Téléphone")
    )
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='telephones',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au téléphone")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.DO_NOTHING,
        null=True,
        related_name='telephones_created'
    )
    updated_by = models.ForeignKey(
        'CustomUser',
        related_name='telephones_updated',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING
    )

    class Meta:
        verbose_name = _("Téléphone")
        verbose_name_plural = _("Téléphones")

    def __str__(self):
        return f"Numéro de téléphone de {self.acheteur.nom}"





class AdresseAcheteur(models.Model):
    adresse = models.TextField(
        max_length=100,
        verbose_name=_("Adresse")
    )
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='adresses',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au téléphone")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.DO_NOTHING,
        null=True,
        related_name='adresses_created'
    )
    updated_by = models.ForeignKey(
        'CustomUser',
        related_name='adresses_updated',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING
    )

    class Meta:
        verbose_name = _("Adresse")
        verbose_name_plural = _("Adresses")

    def __str__(self):
        return f"Adresse de {self.acheteur.nom}"





class PortableAcheteur(models.Model):
    portable = models.TextField(
        max_length=100,
        verbose_name=_("Numéro portable")
    )
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='portables',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au portable")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.DO_NOTHING,
        null=True,
        related_name='portables_created'
    )
    updated_by = models.ForeignKey(
        'CustomUser',
        related_name='portables_updated',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING
    )

    class Meta:
        verbose_name = _("Portable")
        verbose_name_plural = _("Portables")

    def __str__(self):
        return f"Numéro de portable de {self.acheteur.nom}"





class EmailAcheteur(models.Model):
    email = models.TextField(
        max_length=254,  # Limite la taille à celle d'une adresse email standard
        verbose_name=_("Adresse email")
    )
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='emails',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé à l'email")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.DO_NOTHING,
        null=True,
        related_name='emails_created'
    )
    updated_by = models.ForeignKey(
        'CustomUser',
        related_name='emails_updated',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING
    )

    class Meta:
        verbose_name = _("Email")
        verbose_name_plural = _("Emails")

    def __str__(self):
        return f"Email de {self.acheteur.nom}"




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





class Swot(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='swot',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé à l'analyse SWOT")
    )
    forces = models.TextField(
        _("Forces"),
        null=True,
        blank=True,
        help_text=_("Forces de l'entreprise")
    )
    faiblesses = models.TextField(
        _("Faiblesses"),
        null=True,
        blank=True,
        help_text=_("Faiblesses de l'entreprise")
    )
    opportunites = models.TextField(
        _("Opportunités"),
        null=True,
        blank=True,
        help_text=_("Opportunités de l'entreprise")
    )
    menaces = models.TextField(
        _("Menaces"),
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
        return f"SWOT de {self.acheteur.nom}"
    
    
  
    
    
class ProduitService(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='produits_services',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé")
    )
    produits = models.TextField(
        _("Produits"),
        null=True,
        blank=True,
        help_text=_("Produits de l'entreprise")
    )
    services = models.TextField(
        _("Services"),
        null=True,
        blank=True,
        help_text=_("Services de l'entreprise")
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
        verbose_name = _("Produit & Service")
        verbose_name_plural = _("Produits & Services")

    def __str__(self):
        return f"Produits & Services de {self.acheteur.nom}"
    
    
    
    
    
class Marque(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='marques',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé")
    )
    marques = models.TextField(
        _("Marques"),
        null=True,
        blank=True,
        help_text=_("Marques de l'entreprise")
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
        verbose_name = _("Marque")
        verbose_name_plural = _("Marques")

    def __str__(self):
        return f"Marque de {self.acheteur.nom}"





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
    date_ouverture = models.DateField(
        _("Date d'ouverture"),
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





class Cotisation(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='cotisations',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au numéro de sécurité sociale")
    )
    numero = models.CharField(
        _("Numéro de sécurité sociale"),
        max_length=255,
        help_text=_("Numéro de sécurité sociale de l'entreprise")
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
        verbose_name = _("Cotisation Sociale")
        verbose_name_plural = _("Cotisations Sociales")

    def __str__(self):
        return f"Cotisations Sociales de {self.acheteur.nom}"





class CodeNaceAcheteur(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='code_nace',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au code NACE")
    )
    code = models.ForeignKey(
        'SubCategoryNaceCode',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='code_nace_acheteur',
        verbose_name=_("Acheteur"),
        help_text=_("Code associé au code NACE")
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
        verbose_name = _("Code NACE Acheteur")
        verbose_name_plural = _("Codes NACE Acheteur")

    def __str__(self):
        return f"Code NACE de {self.acheteur.nom}"





class CodeNafAcheteur(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='code_naf',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au code NAF")
    )
    code = models.ForeignKey(
        'SubCategoryNafCode',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='code_naf_acheteur',
        verbose_name=_("Acheteur"),
        help_text=_("Code associé au code NAF")
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
        verbose_name = _("Code NAF Acheteur")
        verbose_name_plural = _("Codes NAF Acheteur")

    def __str__(self):
        return f"Code NAF de {self.acheteur.nom}"



##########################################################
##########################################################
# Fin Modules Additifs
##########################################################
##########################################################






##########################################################
##########################################################
# Debut Modules Commande
##########################################################
##########################################################
class Notification(models.Model):
    TYPE_NOTIF = [
        ("AFFECTATION", "Nouvelle affectation"),
        ("RAPPORT_SOUMIS", "Rapport soumis"),
        ("VALIDATION", "Rapport validé"),
        ("CORRECTION", "Correction demandée"),
        ("ENVOI_CLIENT", "Rapport envoyé au client"),
        ("RAPPEL", "Rappel de notification"),
    ]

    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name="notifications", verbose_name=_("Utilisateur concerné"))
    # commande = models.ForeignKey('Commande', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Commande associée"))
    type = models.CharField(max_length=50, choices=TYPE_NOTIF, verbose_name=_("Type de notification"))
    message = models.TextField(verbose_name=_("Message de notification"))
    is_read = models.BooleanField(default=False, verbose_name=_("Lu"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} - {self.user.username} ({'Lu' if self.is_read else 'Non lu'})"



class Commande(models.Model):
    
    STATUS_CHOICES = [
        ("nouvelle", _("Nouvelle")),
        ("en_cours", _("En cours de traitement")),
        ("rapport_soumis", _("Rapport soumis")),
        ("rapport_valide", _("Rapport validé")),
        ("envoye_client", _("Envoyé au client")),
        ("terminee", _("Terminée")),
        ("annulee", _("Annulée")),
    ]
    
    notre_ref = models.CharField(
        max_length=100,
        verbose_name=_("Notre référence"),
        help_text=_("Référence interne de la commande."),
        null=True,
        blank=True
    )
    reference_client = models.CharField(
        max_length=100,
        verbose_name=_("Référence client"),
        help_text=_("Référence attribuée par le client."),
        null=True,
        blank=True
    )
    
    date_recept_commande = models.DateField(
        verbose_name=_("Date de réception de la demande"),
        help_text=_("Date à laquelle la demande a été reçue."),
        null=True,
        blank=True
    )
    date_rapport = models.DateField(
        verbose_name=_("Date du rapport"),
        help_text=_("Date prévue pour l'émission du rapport."),
        null=True,
        blank=True
    )
    
    delais = models.CharField(
        max_length=100,
        verbose_name=_("Délais"),
        help_text=_("Délai de traitement de la commande."),
        null=True,
        blank=True
    )
    priorite = models.CharField(
        max_length=100,
        verbose_name=_("Priorité"),
        help_text=_("Niveau de priorité de la commande."),
        null=True,
        blank=True
    )
    
    raison_sociale = models.CharField(
        max_length=100,
        verbose_name=_("Raison sociale"),
        help_text=_("Nom de l'entreprise ou de l'entité concernée par la commande."),
    )
    type_rapport = models.CharField(
        max_length=100,
        choices=LIEN_TYPE_RAPPORT_CHOICE,
        default="--------",
        verbose_name=_("Type de rapport"),
        help_text=_("Type de rapport demandé par le client."),
    )
    ref_type_rapport = models.ForeignKey(
        'ModeleRapport',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Référence du modèle de rapport"),
        help_text=_("Modèle de rapport utilisé pour cette commande."),
    )
    
    credit_demande = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        verbose_name=_("Crédit demandé"),
        help_text=_("Montant du crédit initialement demandé par le client."),
        null=True,
        blank=True
    )
    devise_credit_demande = models.ForeignKey(
        'Devise',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Devise du crédit demandé"),
        help_text=_("Devise utilisée pour le crédit demandé."),
        related_name="devise_credit_demande"
    )
    
    credit_recommande = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        verbose_name=_("Crédit recommandé"),
        help_text=_("Montant du crédit finalement recommandé."),
        null=True,
        blank=True
    )
    devise_credit_recommande = models.ForeignKey(
        'Devise',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Devise du crédit recommandé"),
        help_text=_("Devise utilisée pour le crédit recommandé."),
        related_name="devise_credit_recommande"
    )
    
    numero_adresse = models.CharField(
        max_length=100,
        verbose_name=_("Numéro d'adresse"),
        help_text=_("Numéro de rue ou d'unité de l'adresse concernée."),
        null=True,
        blank=True
    )
    rue_adresse = models.CharField(
        max_length=200,
        verbose_name=_("Rue adresse"),
        help_text=_("Nom de la rue de l'adresse concernée."),
        null=True,
        blank=True
    )
    code_postale_adresse = models.CharField(
        max_length=200,
        verbose_name=_("Code postal adresse"),
        help_text=_("Code postal de l'adresse concernée."),
        null=True,
        blank=True
    )
    telephone = models.CharField(
        max_length=100,
        verbose_name=_("Téléphone"),
        help_text=_("Numéro de téléphone du contact."),
        null=True,
        blank=True
    )
    email = models.CharField(
        max_length=100,
        verbose_name=_("Email"),
        help_text=_("Adresse email du contact."),
        null=True,
        blank=True
    )
    
    ville = models.ForeignKey(
        'Ville',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Ville"),
        help_text=_("Ville où se trouve l'entreprise ou le client."),
    )
    client = models.ForeignKey(
        'CustomUser',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Client"),
        help_text=_("Client ayant passé la commande."),
    )
    acheteur = models.ForeignKey(
        'Acheteur',
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
        help_text=_("Personne ou entité achetant le service ou produit."),
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="nouvelle", verbose_name=_("Statut de la commande"))
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création de la commande."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour"),
        help_text=_("Date et heure de la dernière mise à jour de la commande."),
    )
    
    class Meta:
        verbose_name = _("Commande")
        verbose_name_plural = _("Commandes")

    def __str__(self):
        return f"Commande {self.notre_ref or 'N/A'} - {self.raison_sociale}"



class SuiviCommande(models.Model):
    TYPE_ACTIONS = [
        ("CREATION", "Création"),
        ("AFFECTATION", "Affectation"),
        ("SOUMISSION", "Soumission de rapport"),
        ("VALIDATION", "Validation"),
        ("CORRECTION", "Correction demandée"),
        ("ENVOI_CLIENT", "Envoi au client"),
        ("CLOTURE", "Clôture"),
        ("ANNULATION", "Annulation"),
        ("AUTRE", "Autre"),
    ]

    commande = models.ForeignKey('Commande', on_delete=models.CASCADE, verbose_name=_("Commande"))
    user = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Utilisateur"))
    action = models.CharField(max_length=255, verbose_name=_("Action"))
    type = models.CharField(max_length=50, choices=TYPE_ACTIONS, default="AUTRE", verbose_name=_("Type d'action"))
    commentaire = models.TextField(null=True, blank=True, verbose_name=_("Commentaire"))
    date_action = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de l'action"))

    class Meta:
        verbose_name = _("Suivi de commande")
        verbose_name_plural = _("Suivis de commande")
        ordering = ['-date_action']

    def __str__(self):
        return f"{self.get_type_display()} - {self.commande.notre_ref} ({self.user.username if self.user else 'Système'})"



class AffectationAnalyste(models.Model):
    commande = models.ForeignKey('Commande', on_delete=models.CASCADE, verbose_name=_("Commande"))
    analyste = models.ForeignKey('CustomUser', on_delete=models.CASCADE, verbose_name=_("Analyste"), related_name="analystes")
    date_affectation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'affectation"))

    class Meta:
        verbose_name = _("Affectation d'analyste")
        verbose_name_plural = _("Affectations des analystes")

    def __str__(self):
        return f"Commande {self.commande.notre_ref} affectée à {self.analyste.username}"



class Rapport(models.Model):
    commande = models.ForeignKey('Commande', on_delete=models.CASCADE, verbose_name=_("Commande"))
    analyste = models.ForeignKey('CustomUser', on_delete=models.CASCADE, verbose_name=_("Analyste"), related_name="rapports")
    fichier = models.FileField(upload_to="rapports/", verbose_name=_("Fichier rapport"))
    date_soumission = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de soumission"))

    class Meta:
        verbose_name = _("Rapport")
        verbose_name_plural = _("Rapports")

    def __str__(self):
        return f"Rapport de {self.analyste.username} pour {self.commande.notre_ref}"



class ValidationRapport(models.Model):
    rapport = models.OneToOneField('Rapport', on_delete=models.CASCADE, verbose_name=_("Rapport"))
    validateur = models.ForeignKey('CustomUser', on_delete=models.CASCADE, verbose_name=_("Analyste validateur"), related_name="validations")
    status = models.CharField(max_length=20, choices=[
        ("en_attente", _("En attente")),
        ("valide", _("Validé")),
        ("a_corriger", _("À corriger")),
    ], default="en_attente", verbose_name=_("Statut de validation"))
    commentaire = models.TextField(null=True, blank=True, verbose_name=_("Commentaire du validateur"))
    date_validation = models.DateTimeField(auto_now=True, verbose_name=_("Date de validation"))

    class Meta:
        verbose_name = _("Validation de rapport")
        verbose_name_plural = _("Validations de rapports")

    def __str__(self):
        return f"Validation de {self.rapport.commande.notre_ref} par {self.validateur.username}"




##########################################################
##########################################################
# Fin Modules Commande
##########################################################
##########################################################









##########################################################
##########################################################
# Debut Module WARNING (Alerte)
##########################################################
##########################################################
class Alerte(models.Model):
    
    reference = models.CharField(max_length=255, verbose_name=_("Référence"), help_text=_("Référence de l'alerte.")) 
    objet = models.CharField(max_length=255, verbose_name=_("Objet"), help_text=_("Objet de l'alerte.")) 
    content = models.TextField(verbose_name=_("Message"), help_text=_("Message de l'alerte.")) 
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création de l'alerte."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour"),
        help_text=_("Date et heure de la dernière mise à jour de l'alerte."),
    ) 

    class Meta:
        verbose_name = _("Alerte")
        verbose_name_plural = _("Alertes")

    def __str__(self):
        return f"{self.reference} - {self.objet}"
    
    
    
class DocumentAlerte(models.Model):
    alerte = models.ForeignKey(
        'Alerte',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='documents_alerte',
        verbose_name=_("Alerte"),
        help_text=_("Alerte associé au document")
    )
    titre = models.CharField(
        _("Titre"),
        max_length=255,
        help_text=_("Titre du document")
    )
    fichier = models.FileField(
        _("Fichier"),
        upload_to='alertes/',
        help_text=_("Fichier du document")
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
        verbose_name = _("Document alerte")
        verbose_name_plural = _("Documents alerte")

    def __str__(self):
        return f"{self.titre} - {self.acheteur.nom}"






##########################################################
##########################################################
# Fin Module WARNING (Alerte)
##########################################################
##########################################################














##########################################################
##########################################################
# Debut Module IRFS COBAC
##########################################################
##########################################################
from django.db import models
from django.utils.translation import gettext_lazy as _

class CompteFinancierIrfs(models.Model):
    TYPE_CHOICES = [
        ('Actif', _('Actif')),
        ('Passif', _('Passif')),
        ('Produit', _('Produit')),
        ('Charge', _('Charge')),
        ('Compte de Résultat', _('Compte de Résultat')),
    ]

    SOUS_TYPE_CHOICES = [
        ('Actif non courant', _('Actif non courant')),
        ('Passif non courant', _('Passif non courant')),
        ('Actif courant', _('Actif courant')),
        ('Capitaux propres', _('Capitaux propres')),
        ('Passif courant', _('Passif courant')),
        ('Produits', _('Produits')),
        ('Charges', _('Charges')),
        ('Autre', _('Autre')),
    ]

    nom = models.CharField(
        _('Nom'),
        max_length=255
    )
    type_compte = models.CharField(
        _('Type de Compte'),
        max_length=255,
        choices=TYPE_CHOICES
    )
    sous_type = models.CharField(
        _('Sous-Type'),
        max_length=255,
        choices=SOUS_TYPE_CHOICES,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.nom

    def get_type_compte_display(self):
        return dict(CompteFinancierIrfs.TYPE_CHOICES).get(self.type_compte, '')

    def get_sous_type_display(self):
        return dict(CompteFinancierIrfs.SOUS_TYPE_CHOICES).get(self.sous_type, '')



class ValeurCompteIrfs(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='comptes_financiers_irfs_acheteur',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au registre de commerce")
    )
    compte = models.ForeignKey(
        CompteFinancierIrfs,
        verbose_name=_('Compte Financier'),
        on_delete=models.CASCADE
    )
    annee = models.ForeignKey(
        'Annee',
        verbose_name=_('Année'),
        on_delete=models.CASCADE
    )
    valeur = models.DecimalField(
        _('Valeur'),
        max_digits=20,
        decimal_places=2
    )
    devise = models.ForeignKey(
        'Devise',
        verbose_name=_('Devise'),
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.compte.nom} - {self.annee.nom}"



class RatioFinancierIrfs(models.Model):
    TYPE_RATIO_CHOICES = [
        ('Ratio financier', _('Ratio financier')),
        ('Liquidité', _('Liquidité')),
        ('Solvabilité', _('Solvabilité')),
        ('Rentabilité des ventes', _('Rentabilité des ventes')),
        ('Gestion', _('Gestion')),
    ]
    
    type_ratio = models.CharField(
        _('Type de Ratio'),
        max_length=255,
        choices=TYPE_RATIO_CHOICES
    )
    
    nom = models.CharField(
        _('Nom'),
        max_length=255
    )
    formule = models.CharField(
        _('Formule'),
        max_length=255
    )

    def __str__(self):
        return self.nom



class ValeurRatioIrfs(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur',
        on_delete=models.DO_NOTHING,
        null=True, 
        blank=True, 
        related_name='ratios_irfs_acheteur',
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au registre de commerce")
    )
    ratio = models.ForeignKey(
        RatioFinancierIrfs,
        verbose_name=_('Ratio Financier'),
        on_delete=models.CASCADE
    )
    annee = models.ForeignKey(
        'Annee',
        verbose_name=_('Année'),
        on_delete=models.CASCADE
    )
    valeur = models.DecimalField(
        _('Valeur'),
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.ratio.nom} - {self.annee.nom}"


##########################################################
##########################################################
# Fin Module IRFS COBAC
##########################################################
##########################################################












##########################################################
##########################################################
# Debut Modules Automatisation Commande CREDENDO
##########################################################
##########################################################

# === Models Commandes client === #

class CredendoCommande(models.Model):
    sender_id = models.CharField(max_length=255, null=True, blank=True)  # ID unique du mail
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

    class Meta:
        verbose_name = _("Commande CREDENDO")
        verbose_name_plural = _("Commandes CREDENDO")

    def __str__(self):
        return f"{self.reference} - {self.nom} - {self.pays}"




##########################################################
##########################################################
# Fin Modules Automatisation Commande CREDENDO
##########################################################
##########################################################









##########################################################
##########################################################
#  Modules Additif
##########################################################
##########################################################
# ----Gestions des logos des acheteurs
#Telephone Acheteur V2


#------ DOCUMENT

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
    
    
    
##########################################################
##########################################################
# Fin Modules Additif
##########################################################
##########################################################