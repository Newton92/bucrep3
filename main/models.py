from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import datetime
import time
from main.utilitaires.constantes import *

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
        return self.nom or _("Structure sans nom")

    class Meta:
        verbose_name = _("Structure")
        verbose_name_plural = _("Structures")


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


class OpinionCreditAcremac(models.Model):
    acheteur = models.ForeignKey(
        'Acheteur', 
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur")
    )
    risque_de_defaut = models.BooleanField(
        default=False, 
        verbose_name=_("Risque de défaut")
    )
    risque_de_concentration_credit = models.BooleanField(
        default=False, 
        verbose_name=_("Risque de concentration de crédit")
    )
    risque_de_reputation = models.BooleanField(
        default=False, 
        verbose_name=_("Risque de réputation")
    )
    risque_pays = models.BooleanField(
        default=False, 
        verbose_name=_("Risque pays")
    )
    risque_de_taux_dinteret = models.BooleanField(
        default=False, 
        verbose_name=_("Risque de taux d'intérêt")
    )
    risque_de_liquidite = models.BooleanField(
        default=False, 
        verbose_name=_("Risque de liquidité")
    )
    risque_eleve = models.BooleanField(
        default=False, 
        verbose_name=_("Risque élevé")
    )
    risque_moyen = models.BooleanField(
        default=False, 
        verbose_name=_("Risque moyen")
    )
    risque_faible = models.BooleanField(
        default=False, 
        verbose_name=_("Risque faible")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    def __str__(self):
        return f"Opinion Credit Acremac for {self.acheteur}"

    class Meta:
        verbose_name = _("Opinion Credit Acremac")
        verbose_name_plural = _("Opinions Credit Acremac")


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








# === Models Commandes client === #

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
