import datetime
import time
import base64
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
import os

from django.contrib.auth.models import AbstractUser, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from safedelete.models import SafeDeleteModel as Model, SOFT_DELETE_CASCADE
from simple_history.models import HistoricalRecords

from main.utilitaires.constantes import *

# from main.tasks import log_responsable_acheteur_changes


# User = get_user_model()

# Create your models here.

couleur_validator = RegexValidator(
    r"^#([0-9A-Fa-f]{3}){1,2}$",
    "La couleur doit être au format hexadécimal (#RRGGBB ou #RGB).",
)


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
    ("Root", "Root"),
    ("Validateur", "Validateur"),
    ("Analyste", "Analyste"),
    ("Client", "Client"),
]


from django.db import models
from django.contrib.auth.models import Group
from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE
from simple_history.models import HistoricalRecords


class Referer(SafeDeleteModel):
    safedelete_policy = SOFT_DELETE_CASCADE

    source = models.ForeignKey(
        Group,
        on_delete=models.DO_NOTHING,
        related_name='referer_sources'
    )
    target = models.ForeignKey(
        Group,
        on_delete=models.DO_NOTHING,
        related_name='referer_targets'
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Référence de groupe"
        verbose_name_plural = "Références de groupes"
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'target'],
                name='unique_source_target'
            )
        ]

    def __str__(self):
        return f"{self.source} notifies {self.target}"


class AdminMails(SafeDeleteModel):
    safedelete_policy = SOFT_DELETE_CASCADE
    
    email = models.EmailField(max_length=255, unique=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Email administrateur"
        verbose_name_plural = "Emails administrateurs"

    def __str__(self):
        return self.email



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
        _("avatar"),
        upload_to="avatars/",
        null=True,
        blank=True,
        help_text=_("Upload an image for your avatar."),
    )
    code_secret = models.CharField(
        _("secret code"),
        max_length=6,
        null=True,
        blank=True,
        help_text=_("A 6-digit code for forgot and reset password."),
    )
    code_connexion = models.CharField(
        _("connexion code"),
        max_length=6,
        null=True,
        blank=True,
        help_text=_("A 6-digit code for two-factor authentication."),
    )
    address = models.CharField(
        _("adresse"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("The address of the user."),
    )
    activation = models.BooleanField(
        _("activation"),
        default=True,
        help_text=_("Designates whether the user account is activated."),
    )
    auth_a2f = models.BooleanField(
        _("two-factor authentication"),
        default=False,
        help_text=_(
            "Designates whether two-factor authentication is enabled for the user."
        ),
    )
    telephone = models.CharField(
        _("telephone"),
        max_length=20,
        null=True,
        blank=True,
        help_text=_("The telephone number of the user."),
    )
    profession = models.CharField(
        _("profession"),
        max_length=100,
        null=True,
        blank=True,
        help_text=_("The profession of the user."),
    )
    email_cc = models.EmailField(
        _("email cc"),
        null=True,
        blank=True,
        help_text=_("The carbon copy email address of the user."),
    )

    role = models.CharField(
        max_length=100,
        choices=ROLES_USERS,
        verbose_name="Droits utilisateur",
        null=True,
        blank=True,
    )

    reset_token = models.CharField(
        _("reset token"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Token for password reset."),
    )

    pays = models.ForeignKey(
        "Pays",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="pays_utilisateurs",
        verbose_name=_("Pays"),
        help_text=_("Pays où l'employé est affecté"),
    )
    
    affectation = models.ManyToManyField(
        "Pays",
        blank=True,
        related_name="affectation_utilisateurs"
    )
    
    affectation_possible = models.ManyToManyField(
        "Pays", blank=True, related_name='affectations_possibles'
    )
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return self.username
    
    def get_user_country(request):
        return request.user.pays

    def fullname(self):
        return f"{self.first_name} {self.last_name}"


# === Models Localisation === #


class Pays(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    nom = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Nom du pays"),
        help_text=_("Nom complet du pays, par exemple 'France' ou 'Cameroun'."),
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Code du pays"),
        help_text=_(
            "Code unique du pays, par exemple 'FR' pour la France ou 'CM' pour le Cameroun."
        ),
    )
    afficher_au_dashboard = models.BooleanField(
        default=False,
        verbose_name=_("Afficher au dashboard"),
        help_text=_("Indique si ce pays doit apparaître dans les tableaux de bord."),
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure à laquelle ce pays a été ajouté."),
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de dernière modification"),
        help_text=_("Date et heure de la dernière mise à jour de ce pays."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si le pays est actif ou désactivé."),
    )
    
    
    history = HistoricalRecords()
    

    class Meta:
        verbose_name = _("Pays")
        verbose_name_plural = _("Pays")
        ordering = ["nom"]  # Trie les pays par nom dans l'ordre alphabétique.

    def __str__(self):
        return f"{self.nom} ({self.code})"


class Province(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    nom = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Nom de la province"),
        help_text=_(
            "Nom complet de la province, par exemple 'Île-de-France' ou 'Ouest'."
        ),
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Code de la province"),
        help_text=_(
            "Code unique de la province, par exemple 'IDF' pour l'Île-de-France ou 'OUEST' pour l'Ouest."
        ),
    )
    pays = models.ForeignKey(
        "Pays",
        null=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Pays"),
        help_text=_("Pays auquel appartient la province."),
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure à laquelle cette province a été ajoutée."),
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de dernière modification"),
        help_text=_("Date et heure de la dernière mise à jour de cette province."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si la province est active ou désactivée."),
    )
    
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Province")
        verbose_name_plural = _("Provinces")
        ordering = ["nom"]  # Trie les provinces par nom dans l'ordre alphabétique.

    def __str__(self):
        return f"{self.nom} ({self.code})"


class Ville(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    nom = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Nom de la ville"),
        help_text=_("Nom complet de la ville, par exemple 'Paris' ou 'Douala'."),
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Code de la ville"),
        help_text=_(
            "Code unique de la ville, par exemple 'PAR' pour Paris ou 'DOU' pour Douala."
        ),
    )
    province = models.ForeignKey(
        "Province",
        null=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Province"),
        help_text=_("Province à laquelle appartient la ville."),
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure à laquelle cette ville a été ajoutée."),
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de dernière modification"),
        help_text=_("Date et heure de la dernière mise à jour de cette ville."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si la ville est active ou désactivée."),
    )
    
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Ville")
        verbose_name_plural = _("Villes")
        ordering = ["nom"]  # Trie les villes par nom dans l'ordre alphabétique.

    def __str__(self):
        return f"{self.nom} ({self.code})"


class Annee(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    annee = models.IntegerField(
        unique=True,
        verbose_name=_("Année"),
        help_text=_("Année de référence, par exemple 2025."),
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création de l'année."),
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification"),
        help_text=_("Date et heure de la dernière modification de l'année."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si l'année est active ou désactivée."),
    )
    
    
    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Année civile")
        verbose_name_plural = _("Années civiles")
        ordering = ["annee"]  # Trie les années par ordre croissant.

    def __str__(self):
        return str(self.annee)


class Devise(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    nom = models.CharField(
        max_length=50,
        verbose_name=_("Nom"),
        help_text=_("Nom complet de la devise, par exemple 'Dollar américain'."),
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_("Code"),
        help_text=_(
            "Code unique de la devise, par exemple 'USD' pour le Dollar ou 'EUR' pour l'Euro."
        ),
    )
    symbole = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("Symbole"),
        help_text=_(
            "Symbole de la devise, par exemple '$' pour le Dollar ou '€' pour l'Euro."
        ),
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création de la devise."),
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification"),
        help_text=_("Date et heure de la dernière modification de la devise."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si la devise est active ou désactivée."),
    )
    
    
    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Devise")
        verbose_name_plural = _("Devises")
        ordering = ["nom"]  # Trie les devises par nom dans l'ordre alphabétique.

    def __str__(self):
        return f"{self.nom} ({self.code})"


class CouleurCommentaire(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    couleur = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Nom de la Couleur"),
        help_text=_("Nom de la couleur, par exemple '#FF5733'."),
    )
    code = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Code Couleur"),
        validators=[couleur_validator],
        help_text=_("Code hexadécimal de la couleur, par exemple '#FF5733'."),
    )
    
    
    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Coloration")
        verbose_name_plural = _("Colorations")
        ordering = ["code"]  # Trie les devises par nom dans l'ordre alphabétique.

    def __str__(self):
        return self.couleur


class CategoryNaceCode(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)
    poids = models.FloatField(_("Poids"), default=0.0)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    
    
    history = HistoricalRecords()
    
    def __str__(self):
        return f"{self.code} - {self.libelle}"

    class Meta:
        verbose_name = _("Catégorie Code NACE")
        verbose_name_plural = _("Catégories Code NACE")
        ordering = ["code"]


class SubCategoryNaceCode(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    category = models.ForeignKey(
        CategoryNaceCode,
        on_delete=models.CASCADE,
        related_name="subcategories",
        verbose_name=_("Catégorie"),
    )
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)
    poids = models.FloatField(_("Poids"), default=0.0)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.libelle
            else _("Sous-Catégorie Code NACE sans libellé")
        )

    class Meta:
        verbose_name = _("Sous-Catégorie Code NACE")
        verbose_name_plural = _("Sous-Catégories Code NACE")
        ordering = ["code"]


class CategoryNafCode(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)
    poids = models.FloatField(_("Poids"), default=0.0)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.libelle
            else _("Catégorie Code NAF sans libellé")
        )

    class Meta:
        verbose_name = _("Catégorie Code NAF")
        verbose_name_plural = _("Catégories Code NAF")
        ordering = ["code"]


class SubCategoryNafCode(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    category = models.ForeignKey(
        CategoryNafCode,
        on_delete=models.CASCADE,
        related_name="subcategories",
        verbose_name=_("Catégorie"),
    )
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)
    poids = models.FloatField(_("Poids"), default=0.0)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.libelle
            else _("Sous-Catégorie Code NAF sans libellé")
        )

    class Meta:
        verbose_name = _("Sous-Catégorie Code NAF")
        verbose_name_plural = _("Sous-Catégories Code NAF")
        ordering = ["code"]


class FormeJuridique(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    poids = models.FloatField(_("Poids"), default=0.0)
    active = models.BooleanField(_("Actif"), default=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.libelle
            else _("Forme juridique sans libellé")
        )

    class Meta:
        verbose_name = _("Forme juridique")
        verbose_name_plural = _("Formes juridiques")
        ordering = ["code"]


class DomaineEntreprise(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(
        _("Libellé"), max_length=255, unique=True, null=True, blank=True
    )
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.libelle
            else _("Domaine entreprise sans libellé")
        )

    class Meta:
        verbose_name = _("Domaine entreprise")
        verbose_name_plural = _("Domaines entreprise")
        ordering = ["libelle"]


class PosteEntreprise(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    domaine = models.ForeignKey(
        DomaineEntreprise,
        on_delete=models.CASCADE,
        related_name="postes",
        verbose_name=_("Domaine Entreprise"),
    )
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.libelle} ({self.domaine.libelle})"
            if self.domaine
            else _("Poste entreprise sans domaine")
        )

    class Meta:
        verbose_name = _("Poste entreprise")
        verbose_name_plural = _("Postes entreprise")
        ordering = ["libelle"]


class CategorieEntreprise(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(_("Code"), max_length=255, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return self.libelle or _("Catégorie sans libellé")

    class Meta:
        verbose_name = _("Catégorie d'Entreprise")
        verbose_name_plural = _("Catégories d'Entreprises")


class StructureEntreprise(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(_("Code"), max_length=255, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return self.libelle or _("Structure sans libellé")

    class Meta:
        verbose_name = _("Structure d'Entreprise")
        verbose_name_plural = _("Structures d'Entreprises")


class StatutEntreprise(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(_("Code"), max_length=255, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return self.libelle or _("Statut sans libellé")

    class Meta:
        verbose_name = _("Statut d'Entreprise")
        verbose_name_plural = _("Statuts d'Entreprises")


# === Models Acheteurs et compagnies === #


class ModeleRapport(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.code and self.libelle
            else _("Modèle sans informations complètes")
        )

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de rapport")
        verbose_name_plural = _("Modèles de rapport")


class ModeleAlarme(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.code and self.libelle
            else _("Modèle sans informations complètes")
        )

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle d'alarme")
        verbose_name_plural = _("Modèles d'alarme")


class ModeleBilan(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.code and self.libelle
            else _("Modèle sans informations complètes")
        )

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de bilan")
        verbose_name_plural = _("Modèles de bilan")


class ModeleBail(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    poids = models.FloatField(_("Poids"), default=0.0)
    
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.code and self.libelle
            else _("Modèle sans informations complètes")
        )

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de bail")
        verbose_name_plural = _("Modèles de bail")


class ModeleNotation(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.code and self.libelle
            else _("Modèle sans informations complètes")
        )

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de notation")
        verbose_name_plural = _("Modèles de notation")


class ModeleAvisCommercial(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    poids = models.FloatField(_("Poids"), default=0.0)
    
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.code and self.libelle
            else _("Modèle sans informations complètes")
        )

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle d'avis commercial")
        verbose_name_plural = _("Modèles d'avis commercial")


class ModeleRelationEntreprise(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.code and self.libelle
            else _("Modèle sans informations complètes")
        )

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de relation entreprise")
        verbose_name_plural = _("Modèles de relation entreprise")


class ModeleInformationNotationEntreprise(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.code and self.libelle
            else _("Modèle sans informations complètes")
        )

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle d'information sur notation entreprise")
        verbose_name_plural = _("Modèles d'information sur notation entreprise")


class ModeleComportementPaiement(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    poids = models.FloatField(_("Poids"), default=0.0)
    
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.code and self.libelle
            else _("Modèle sans informations complètes")
        )

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de comportement de paiement")
        verbose_name_plural = _("Modèles de comportement de paiement")


class ModeleComportementJugement(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.code and self.libelle
            else _("Modèle sans informations complètes")
        )

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle de comportement de jugement")
        verbose_name_plural = _("Modèles de comportement de jugement")


class ModeleAgeSociete(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    poids = models.FloatField(_("Poids"), default=0.0)
    
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.code and self.libelle
            else _("Modèle sans informations complètes")
        )

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle d'age de société")
        verbose_name_plural = _("Modèles d'age de société")
             
        
        
class ModeleInterpretationScoringSansBilan(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    poids = models.FloatField(_("Poids"), default=0.0)
    
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    
    history = HistoricalRecords()
    

    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.code and self.libelle
            else _("Modèle interpretation scoring sans bilan")
        )

    def is_empty(self):
        return not self.code and not self.libelle

    class Meta:
        verbose_name = _("Modèle interpretation scoring sans bilan")
        verbose_name_plural = _("Modèles interpretations scoring sans bilan")



##########################################################
##########################################################
# Debut Modules Portefeuille  & Client
##########################################################
##########################################################


class ElementSurveillance(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    nom = models.CharField(
        max_length=255,
        unique=True,  # Chaque élément doit avoir un nom unique
        verbose_name=_("Nom de l'élément de surveillance"),
        help_text=_("Ex: Changement de niveau de scoring, Dissolution de l'entreprise"),
    )
    code_interne = models.CharField(
        max_length=100,  # Un code court pour une identification programmatique facile
        unique=True,
        verbose_name=_("Code interne"),
        help_text=_("Ex: SCORING_CHANGE, DISSOLUTION_ENTREPRISE"),
    )
    categorie = models.CharField(
        max_length=150,
        verbose_name=_("Catégorie de surveillance"),
        help_text=_("Ex: Santé Financière et Risque de Crédit, Procédures Collectives"),
    )
    sous_categorie = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name=_("Sous-catégorie de surveillance"),
        help_text=_("Ex: Évaluation et Notation, Cessation d'Activité"),
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description détaillée"),
        help_text=_("Description de ce que cet élément surveille."),
    )
    # Potentiellement un champ pour indiquer si l'élément est activable par défaut
    # actif_par_defaut = models.BooleanField(default=False, verbose_name=_("Activé par défaut pour les nouveaux portefeuilles"))
    
    
    history = HistoricalRecords()
    

    class Meta:
        verbose_name = _("Élément de Surveillance")
        verbose_name_plural = _("Éléments de Surveillance")
        ordering = ["categorie", "sous_categorie", "nom"]

    def __str__(self):
        return f"{self.categorie} - {self.nom}"


class Client(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    nom = models.CharField(
        max_length=255, verbose_name=_("Nom"), help_text=_("Nom du client.")
    )
    email = models.EmailField(
        unique=True, verbose_name=_("Email"), help_text=_("Adresse email du client.")
    )
    telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Téléphone"),
        help_text=_("Numéro de téléphone du client."),
    )
    adresse = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Adresse"),
        help_text=_("Adresse postale du client."),
    )
    date_inscription = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date d'inscription"),
        help_text=_("Date et heure d'inscription du client."),
    )
    actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si le client est actif."),
    )
    
    
    history = HistoricalRecords()
    

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")

    def __str__(self):
        return self.nom


class Contact(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    

    client = models.ForeignKey(
        "Client",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Entreprise du contact"),
    )

    nom = models.CharField(
        max_length=255, verbose_name=_("Nom"), help_text=_("Nom du contact.")
    )
    email = models.EmailField(
        unique=True, verbose_name=_("Email"), help_text=_("Adresse email du contact.")
    )
    telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Téléphone"),
        help_text=_("Numéro de téléphone du contact."),
    )
    actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si le contact est actif."),
    )
    
    
    history = HistoricalRecords()
    

    class Meta:
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")

    def __str__(self):
        return self.nom


class Portefeuille(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    

    FREQUENCE_CHOICES = [
        ("quotidienne", _("Quotidienne")),
        ("hebdomadaire", _("Hebdomadaire")),
        ("mensuelle", _("Mensuelle")),
    ]

    frequence_alertes = models.CharField(
        max_length=20,
        choices=FREQUENCE_CHOICES,
        default="quotidienne",
        verbose_name=_("Fréquence des Alertes"),
        help_text=_(
            "Choisissez la fréquence à laquelle vous souhaitez recevoir des alertes."
        ),
    )

    client = models.ForeignKey(
        "Client",
        on_delete=models.CASCADE,
        related_name="portefeuilles_client",
        verbose_name=_("Client"),
        help_text=_("Client propriétaire du portefeuille."),
    )
    nom = models.CharField(
        max_length=255, verbose_name=_("Nom"), help_text=_("Nom du portefeuille.")
    )

    elements_surveillance_actifs = models.ManyToManyField(
        ElementSurveillance,  # Référence au modèle que nous venons de créer
        blank=True,  # Un portefeuille peut ne choisir aucun élément spécifique (ou utiliser des valeurs par défaut plus tard)
        verbose_name=_("Éléments de surveillance activés"),
        help_text=_("Choisissez les événements à surveiller pour ce portefeuille."),
    )

    # CHAMP AJOUTÉ
    derniere_verification = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Dernière vérification effectuée le"),
        help_text=_(
            "Date de la dernière exécution de la routine de surveillance pour ce portefeuille."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création du portefeuille."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour"),
        help_text=_("Date et heure de la dernière mise à jour du portefeuille."),
    )
    
    
    history = HistoricalRecords()
    

    class Meta:
        verbose_name = _("Portefeuille")
        verbose_name_plural = _("Portefeuilles")

    def __str__(self):
        return f"{self.nom} - {self.client.nom}"


class PortefeuilleClient(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    CATEGORY_CHOICES = [
        ("grande", "Grande entreprise"),
        ("pme", "Petite et moyenne entreprise"),
        ("autre", "Autre"),
    ]

    portefeuille = models.ForeignKey("Portefeuille", on_delete=models.CASCADE)
    acheteur = models.ForeignKey("Acheteur", on_delete=models.CASCADE)
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name=_("Catégorie"),
        help_text=_("Catégorie de l'acheteur dans le portefeuille."),
    )
    
    
    history = HistoricalRecords()
    

    class Meta:
        verbose_name = _("Portefeuille client")
        verbose_name_plural = _("Portefeuilles client")
        unique_together = ("portefeuille", "acheteur")

    def __str__(self):
        return f"{self.acheteur.nom} - {self.get_categorie_display()}"


class NotificationLog(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    portefeuille = models.ForeignKey(Portefeuille, on_delete=models.CASCADE)
    code_evenement = models.CharField(max_length=100)
    date_notification = models.DateTimeField(default=timezone.now)
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description détaillée"),
        help_text=_("Description de ce que cet élément surveille."),
    )
    actif = models.BooleanField(
        default=False,
        verbose_name=_("Actif"),
        help_text=_("Indique si la notification a été envoyée."),
    )
    
    
    history = HistoricalRecords()
    

    class Meta:
        verbose_name = _("Journal des Notifications")
        verbose_name_plural = _("Journaux des Notifications")

    def __str__(self):
        return f"{self.portefeuille.nom} - {self.code_evenement} - {self.date_notification}"


class AlerteLog(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    portefeuille = models.ForeignKey(
        "Portefeuille", on_delete=models.CASCADE, verbose_name=_("Portefeuille")
    )
    acheteur = models.ForeignKey(
        "Acheteur", on_delete=models.CASCADE, verbose_name=_("Acheteur Concerné")
    )
    element_surveille = models.ForeignKey(
        ElementSurveillance,
        on_delete=models.CASCADE,
        verbose_name=_("Élément Déclenché"),
    )

    date_creation = models.DateTimeField(_("Date de création"), default=timezone.now)
    message = models.TextField(_("Message de l'alerte"))

    lu = models.BooleanField(
        _("Lu"),
        default=False,
        help_text=_("Indique si le client a consulté cette alerte."),
    )

    # Champ générique pour pointer vers l'objet exact qui a changé (optionnel mais puissant)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    
    
    history = HistoricalRecords()
    

    class Meta:
        verbose_name = _("Alerte Log")
        verbose_name_plural = _("Alertes Log")
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Alerte pour {self.acheteur.nom} sur '{self.element_surveille.nom}'"


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


class Acheteur(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Code unique de l'acheteur"),
    )

    categorie_entreprise = models.ForeignKey(
        "CategorieEntreprise",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Catégorie d'Entreprise"),
        help_text=_("Catégorie à laquelle appartient l'entreprise"),
    )

    forme_juridique = models.ForeignKey(
        "FormeJuridique",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Forme Juridique"),
        help_text=_("Forme juridique de l'entreprise"),
    )

    activite_principale = models.CharField(
        _("Activité Principale"),
        max_length=255,
        blank=True,
        help_text=_("Activité principale de l'entreprise"),
    )

    nom = models.CharField(
        _("Raison sociale"),
        max_length=1000,
        blank=False,
        unique=True,
        help_text=_("Nom officiel de l'entreprise"),
    )

    sigle = models.CharField(
        _("Sigle"), max_length=255, blank=True, help_text=_("Sigle de l'entreprise")
    )

    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description de l'entreprise"),
    )

    date_creation = models.DateField(
        _("Date de Création"),
        null=True,
        blank=True,
        help_text=_("Date de création de l'entreprise"),
    )

    statut_entreprise = models.ForeignKey(
        "StatutEntreprise",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Statut actuel de l'entreprise"),
        help_text=_("Statut actuel de l'entreprise"),
    )

    code_postal = models.CharField(
        max_length=200, blank=True, help_text=_("Code postal de l'entreprise")
    )

    fax = models.CharField(
        max_length=300, blank=True, help_text=_("Numéro de fax de l'entreprise")
    )

    boite_postale = models.CharField(
        max_length=200, blank=True, help_text=_("Boîte postale de l'entreprise")
    )

    email = models.EmailField(blank=True, help_text=_("Adresse email de l'entreprise"))

    site_internet = models.URLField(
        max_length=300, blank=True, help_text=_("Site internet de l'entreprise")
    )

    numero_adresse = models.CharField(
        max_length=200, blank=True, help_text=_("Numéro de l'adresse de l'entreprise")
    )

    rue_adresse = models.CharField(
        max_length=200, blank=True, help_text=_("Rue de l'adresse de l'entreprise")
    )

    pays = models.ForeignKey(
        "Pays",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name=_("Pays"),
        help_text=_("Pays où l'entreprise est située"),
    )

    province = models.ForeignKey(
        "Province",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name=_("Province"),
        help_text=_("Province où l'entreprise est située"),
    )

    ville = models.ForeignKey(
        "Ville",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name=_("Ville"),
        help_text=_("Ville où l'entreprise est située"),
    )

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        help_text=_("Couleur du commentaire"),
    )

    commentaire = models.TextField(
        blank=True, help_text=_("Commentaire sur l'entreprise")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
        help_text=_("Date de création de l'enregistrement"),
    )

    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date de la dernière mise à jour de l'enregistrement"),
    )
    
    history = HistoricalRecords()
    

    class Meta:
        verbose_name = _("Acheteur")
        verbose_name_plural = _("Acheteurs")
        ordering = ["nom"]
        unique_together = ("nom", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Stocke l'état original des champs surveillés lors de l'initialisation
        self.__original_data = {
            "forme_juridique_id": self.forme_juridique_id,
            "activite_principale": self.activite_principale,
            "nom": self.nom,  # Raison sociale
            "statut_entreprise_id": self.statut_entreprise_id,
            "pays_id": self.pays_id,
            "province_id": self.province_id,
            "ville_id": self.ville_id,
            "email": self.email,
            "site_internet": self.site_internet,
            "numero_adresse": self.numero_adresse,
            "rue_adresse": self.rue_adresse,
            "code_postal": self.code_postal,
            "fax": self.fax,
            "boite_postale": self.boite_postale,
            # Pourrait aussi surveiller 'taille' (si elle existe) si elle est liée à 'Santé Financière'
        }

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not is_new:
            self._check_for_changes_and_log_alerts()

        if not self.code:
            self.code = self.generate_unique_code()

        super().save(*args, **kwargs)

        # Mettre à jour l'état original après la sauvegarde
        self.__original_data = {
            "forme_juridique_id": self.forme_juridique_id,
            "activite_principale": self.activite_principale,
            "nom": self.nom,  # Raison sociale
            "statut_entreprise_id": self.statut_entreprise_id,
            "pays_id": self.pays_id,
            "province_id": self.province_id,
            "ville_id": self.ville_id,
            "email": self.email,
            "site_internet": self.site_internet,
            "numero_adresse": self.numero_adresse,
            "rue_adresse": self.rue_adresse,
            "code_postal": self.code_postal,
            "fax": self.fax,
            "boite_postale": self.boite_postale,
        }

    def _check_for_changes_and_log_alerts(self):
        # Cartographie des champs aux codes internes des ElementSurveillance
        # Utiliser les codes de votre liste fournie
        field_to_element_code = {
            # Identité et Structure de l'Entreprise
            "nom": "COMPANY_NAME_CHANGE",  # Raison sociale
            "forme_juridique_id": "FORME_JURIDIQUE_CHANGE",  # Ajouté, voir plus bas pour le détail
            "email": "CONTACT_INFO_CHANGE",
            "site_internet": "CONTACT_INFO_CHANGE",
            "numero_adresse": "CONTACT_INFO_CHANGE",
            "rue_adresse": "CONTACT_INFO_CHANGE",
            "code_postal": "CONTACT_INFO_CHANGE",
            "fax": "CONTACT_INFO_CHANGE",
            "boite_postale": "CONTACT_INFO_CHANGE",
            "pays_id": "CONTACT_INFO_CHANGE",
            "province_id": "CONTACT_INFO_CHANGE",
            "ville_id": "CONTACT_INFO_CHANGE",
            # Activité Commerciale et Contrats (si applicable, ex: changement d'activité principale)
            "activite_principale": "ACTIVITY_CHANGE",  # Ajout d'un code si vous voulez surveiller ce champ
            # Santé Financière et Risque de Crédit (si des champs comme scoring ou limite de crédit sont directement dans Acheteur)
            # Sinon, ces alertes proviendraient de modèles liés
            "statut_entreprise_id": "STATUT_ENTREPRISE_CHANGE",  # Si le statut peut être "en liquidation", "dissoute", etc.
        }

        changes_detected = {}  # Pour regrouper les messages par code d'élément

        for field_name, element_code in field_to_element_code.items():
            original_value = self.__original_data.get(field_name)
            current_value = getattr(self, field_name)

            # Traitement spécial pour les champs ForeignKey (_id)
            if field_name.endswith("_id"):
                if original_value != current_value:
                    original_obj_display = "vide"
                    current_obj_display = "vide"

                    # Tenter de récupérer l'objet lié pour un affichage plus lisible
                    if original_value:
                        try:
                            original_obj = getattr(
                                self, field_name.replace("_id", "")
                            )._default_manager.get(pk=original_value)
                            original_obj_display = str(original_obj)
                        except models.ObjectDoesNotExist:
                            original_obj_display = "Inconnu (ID: {})".format(
                                original_value
                            )

                    if current_value:
                        try:
                            current_obj = getattr(
                                self, field_name.replace("_id", "")
                            )._default_manager.get(pk=current_value)
                            current_obj_display = str(current_obj)
                        except models.ObjectDoesNotExist:
                            current_obj_display = "Inconnu (ID: {})".format(
                                current_value
                            )

                    changes_detected.setdefault(element_code, []).append(
                        f"Le champ '{self._meta.get_field(field_name).verbose_name}' est passé de "
                        f"'{original_obj_display}' à '{current_obj_display}'."
                    )
            else:  # Champs non ForeignKey (CharFields, DateFields, etc.)
                # Assurez-vous que les comparaisons sont robustes (ex: éviter de comparer None avec '')
                # Utilisez str() pour les dates ou d'autres types si nécessaire
                if str(original_value or "") != str(current_value or ""):
                    changes_detected.setdefault(element_code, []).append(
                        f"Le champ '{self._meta.get_field(field_name).verbose_name}' est passé de "
                        f"'{original_value or 'vide'}' à '{current_value or 'vide'}'."
                    )

        # Logique pour les changements de statut d'entreprise qui peuvent impliquer LIQUIDATION ou DISSOLUTION
        original_statut_id = self.__original_data.get("statut_entreprise_id")
        current_statut_id = self.statut_entreprise_id

        if original_statut_id != current_statut_id:
            if current_statut_id:
                try:
                    current_statut = StatutEntreprise.objects.get(pk=current_statut_id)
                    if "liquidation" in current_statut.nom.lower():
                        changes_detected.setdefault("LIQUIDATION", []).append(
                            f"Le statut de l'entreprise est passé à '{current_statut.nom}' (Liquidation)."
                        )
                    elif "dissolution" in current_statut.nom.lower():
                        changes_detected.setdefault("DISSOLUTION", []).append(
                            f"Le statut de l'entreprise est passé à '{current_statut.nom}' (Dissolution)."
                        )
                    # Vous pouvez ajouter d'autres conditions pour SAFEGUARD_PROCEDURE, JUDICIAL_RECOVERY_PROCEDURE
                    # si votre modèle StatutEntreprise peut refléter ces états
                except StatutEntreprise.DoesNotExist:
                    pass  # Gérer si le statut n'existe pas

        if changes_detected:
            portefeuilles_concernés = Portefeuille.objects.filter(
                portefeuilleclient__acheteur=self
            ).distinct()

            for portefeuille in portefeuilles_concernés:
                for element_code, messages in changes_detected.items():
                    try:
                        element_surveillance = ElementSurveillance.objects.get(
                            code_interne=element_code
                        )
                        if portefeuille.elements_surveillance_actifs.filter(
                            pk=element_surveillance.pk
                        ).exists():
                            for (
                                message
                            ) in messages:  # Créer une alerte par message de changement
                                AlerteLog.objects.create(
                                    portefeuille=portefeuille,
                                    acheteur=self,
                                    element_surveille=element_surveillance,
                                    message=message,
                                    content_object=self,
                                )
                    except ElementSurveillance.DoesNotExist:
                        print(
                            f"ATTENTION: Élément de surveillance avec code_interne '{element_code}' non trouvé. Veuillez l'ajouter à la liste des ElementSurveillance."
                        )

    def clean(self):
        # Ajouter des validateurs pour éviter les doublons
        if Acheteur.objects.filter(nom=self.nom).exclude(pk=self.pk).exists():
            raise ValidationError(_("Un acheteur avec ce nom existe déjà."))
        # Supprimez ou ajustez cette validation si l'email n'est pas censé être unique par acheteur
        # if self.email and Acheteur.objects.filter(email=self.email).exclude(pk=self.pk).exists():
        #     raise ValidationError(_("Un acheteur avec cet email existe déjà."))

    def generate_unique_code(self):
        # ... (votre méthode generate_unique_code existante) ...
        current_year = datetime.datetime.now().year
        timestamp = int(time.time())
        unique_code = f"{current_year}-{timestamp}"
        return unique_code

    def __str__(self):
        return self.nom


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
class Resume(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur concerné par ce résumé."),
    )
    devise = models.ForeignKey(
        "Devise",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Devise du capital social"),
        related_name="devise_resume",
    )
    capital_social = models.DecimalField(
        max_digits=100,
        decimal_places=0,
        blank=True,
        null=True,
        verbose_name=_("Capital social"),
        help_text=_("Capital social de l'acheteur."),
    )
    chiffre_affaire = models.DecimalField(
        max_digits=100,
        decimal_places=0,
        blank=True,
        null=True,
        verbose_name=_("Chiffre d'affaire"),
        help_text=_("Chiffre d'affaire annuel de l'acheteur."),
    )
    resultat_net = models.DecimalField(
        max_digits=100,
        decimal_places=0,
        blank=True,
        null=True,
        verbose_name=_("Résultat net"),
        help_text=_("Résultat net après impôts."),
    )
    capitaux_propre = models.DecimalField(
        max_digits=100,
        decimal_places=0,
        blank=True,
        null=True,
        verbose_name=_("Capitaux propres"),
        help_text=_("Capitaux propres de l'acheteur."),
    )
    nombre_employe = models.DecimalField(
        max_digits=100,
        decimal_places=0,
        blank=True,
        null=True,
        verbose_name=_("Nombre d'employés"),
        help_text=_("Nombre total d'employés dans l'entreprise."),
    )
    date_creation = models.DateField(
        null=True, blank=True, verbose_name=_("Date de création de l'entreprise")
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire"),
    )
    commentaire = models.TextField(blank=True, verbose_name=_("Commentaire"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Dernière mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Résumé Financier")
        verbose_name_plural = _("Résumés Financiers")

    def __str__(self):
        return f"Résumé {self.pk} - {self.acheteur}"


from django.db import models
from django.utils.translation import gettext_lazy as _

# Définition des choix pour la cotation du risque
RISK_RATING_CHOICES = [
    ("non_douteux", _("Non douteux")),
    ("risque_faible", _("Risque faible")),
    ("risque_modere", _("Risque modéré")),
    ("mise_en_garde", _("Mise en garde")),
    ("peu_satisfaisant", _("Peu satisfaisant")),
    ("inacceptable", _("Inacceptable")),
]

# Définition des choix pour l'indice du risque
RISK_INDEX_CHOICES = [
    ("eleve", _("Élevé")),
    ("moyen", _("Moyen")),
    ("medium", _("Moyen")),
    ("faible", _("Faible")),
]


class RiskRating(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur concerné par l'évaluation du risque."),
    )
    remboursabilite = models.BooleanField(
        default=False, verbose_name=_("Remboursabilité")
    )
    # ... (tous vos autres champsBooleanField existants) ...
    situation_liquidite = models.BooleanField(
        default=False, verbose_name=_("Situation de liquidité")
    )
    performance_rentabilite = models.BooleanField(
        default=False, verbose_name=_("Performance et rentabilité")
    )
    perspective_secteur = models.BooleanField(
        default=False, verbose_name=_("Perspective du secteur")
    )
    qualite_information_analyse = models.BooleanField(
        default=False, verbose_name=_("Qualité de l'information analysée")
    )
    existence_garantie = models.BooleanField(
        default=False, verbose_name=_("Existence de garantie")
    )
    terme_financier_duree_pret = models.BooleanField(
        default=False, verbose_name=_("Terme financier et durée du prêt")
    )
    mesure_propre_soutenir_credit = models.BooleanField(
        default=False, verbose_name=_("Mesure propre à soutenir le crédit")
    )

    # Nouveaux champs pour la cotation et l'indice du risque
    cotation_du_risque = models.CharField(
        max_length=50,
        choices=RISK_RATING_CHOICES,
        blank=True,
        null=True,
        verbose_name=_("Cotation du risque"),
    )
    indice_du_risque = models.CharField(
        max_length=50,
        choices=RISK_INDEX_CHOICES,
        blank=True,
        null=True,
        verbose_name=_("Indice du risque"),
    )

    interpretation = models.TextField(blank=True, verbose_name=_("Interprétation"))
    analyse = models.TextField(blank=True, verbose_name=_("Analyse détaillée"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Dernière mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Évaluation du Risque")
        verbose_name_plural = _("Évaluations des Risques")

    def __str__(self):
        return f"RiskRating {self.pk} - {self.acheteur}"

    def _get_fallback_svg(self, score):
        """Génère un SVG de secours"""
        fallback_svg = f'''<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
            <circle cx="100" cy="100" r="90" fill="#f0f0f0" stroke="#333" stroke-width="3"/>
            <text x="100" y="110" text-anchor="middle" font-size="60" font-family="Arial" fill="#333">{score}</text>
            <text x="100" y="160" text-anchor="middle" font-size="20" font-family="Arial" fill="#666">/9</text>
        </svg>'''
        encoded_fallback = base64.b64encode(fallback_svg.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{encoded_fallback}"

    def get_risk_gauge_image(self):
        score = self.calculate_risk_score()
        filename = f"risk_gauge_{self.pk}.png"
        return generate_risk_gauge(score, filename=filename)
    
    def get_cotation_explication(self):
        """Retourne l'explication de la cotation du risque."""
        explications = {
            "non_douteux": _(
                "Prêt entièrement garanti par l’encaisse ; Solide capitalisation ; Direction remarquable"
            ),
            "risque_faible": _(
                "Excellents antécédents financiers/tendances ; Direction solide ; Industrie stable/robuste"
            ),
            "risque_modere": _(
                "Direction solide ; Tendances financières stables ; Niveau de capitalisation modéré"
            ),
            "mise_en_garde": _(
                "Insuffisance possible de la garantie ; Insuffisance possible du service de la dette ; Tournure très défavorable des événements"
            ),
            "peu_satisfaisant": _(
                "Cessation des activités ; Changement de direction préjudiciable ; Arriérés en intérêts et capital"
            ),
            "inacceptable": _("Actif/garantie en train de disparaître ; Fraude"),
        }
        return explications.get(self.cotation_du_risque, "")

    def get_indice_explication(self):
        """Retourne l'explication de l'indice du risque."""
        explications = {
            "eleve": _("Le risque de transaction est relativement élevé."),
            "moyen": _("Le risque de transaction est relativement modéré."),
            "faible": _("Le risque de transaction est relativement faible."),
        }
        return explications.get(self.indice_du_risque, "")
    
    def calculate_risk_score(self):
        """Calcule le score de risque (0-8) basé sur les champs booléens"""
        score = 0
        fields_to_check = [
            'remboursabilite', 'situation_liquidite', 'performance_rentabilite',
            'perspective_secteur', 'qualite_information_analyse', 'existence_garantie',
            'terme_financier_duree_pret', 'mesure_propre_soutenir_credit'
        ]
        
        for field in fields_to_check:
            if getattr(self, field):
                score += 1
                
        return score
    
    def get_risk_image_path(self):
        """Retourne le chemin vers l'image SVG correspondant au score"""
        score = self.calculate_risk_score()
        return f"main/static/riskrating/{score}.svg"
    
    def calculate_risk_score_two(self):
        score = 1  # ou 0 selon votre choix
        fields_to_check = [
            'remboursabilite', 'situation_liquidite', 'performance_rentabilite',
            'perspective_secteur', 'qualite_information_analyse', 'existence_garantie',
            'terme_financier_duree_pret', 'mesure_propre_soutenir_credit'
        ]
        
        for field in fields_to_check:
            if getattr(self, field):
                score += 1
                
        return min(score, 9)  # ou 8 si vous partez de 0
    
    def get_risk_rating_image_base64(self):
        score = self.calculate_risk_score()
        print(f"Score calculé : {score}")  # Debug

        if score is None:
            score = 0

        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 0

        score = max(0, min(9, score))
        svg_filename = f"{score}.svg"
        print(f"Fichier SVG recherché : {svg_filename}")  # Debug

        possible_paths = [
            os.path.join(settings.STATIC_ROOT, 'riskrating', svg_filename),
            os.path.join(settings.BASE_DIR, 'static', 'riskrating', svg_filename),
            os.path.join(settings.BASE_DIR, 'main', 'static', 'riskrating', svg_filename),
        ]

        print(f"Chemins testés : {possible_paths}")  # Debug

        for svg_path in possible_paths:
            print(f"Test du chemin : {svg_path} - Existe : {os.path.exists(svg_path)}")  # Debug
            if os.path.exists(svg_path):
                try:
                    with open(svg_path, 'rb') as svg_file:
                        svg_content = svg_file.read()
                        encoded_string = base64.b64encode(svg_content).decode('utf-8')
                        return f"data:image/svg+xml;base64,{encoded_string}"
                except Exception as e:
                    print(f"Erreur lors de la lecture : {e}")  # Debug

        print(f"Aucun fichier SVG trouvé pour le score {score}.")  # Debug
        return self._get_fallback_svg(score)
    
    def get_risk_rating_image_url(self):
        """Retourne l'URL du fichier SVG correspondant au score de risque"""
        score = self.calculate_risk_score()
        if score is None:
            score = 0

        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 0

        score = max(0, min(9, score))
        svg_filename = f"{score}.svg"

        # Utilisez staticfiles_storage pour obtenir l'URL statique
        svg_url = staticfiles_storage.url(f'riskrating/{svg_filename}')

        return svg_url


class DonneesEnregistrement(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    
    nom_anterieur = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("Nom antérieur"))
    
    date_creation = models.DateField(
        null=True, blank=True, verbose_name=_("Date de création")
    )
    date_registre = models.DateField(
        null=True, blank=True, verbose_name=_("Date d'enregistrement")
    )

    # Ancien attribut avec choices
    forme_juridique = models.CharField(
        max_length=4000,
        choices=FORMEJURIDIQUE_CHOICES,
        default="Veuillez choisir la forme juridique",
        verbose_name=_("Forme Juridique"),
    )

    # Nouvel attribut avec ForeignKey
    forme_juridique_ref = models.ForeignKey(
        "FormeJuridique",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Référence Forme Juridique"),
    )

    numero_registre_commerce = models.CharField(
        max_length=50, blank=True, verbose_name=_("Numéro de registre du commerce")
    )
    numero_fiscale = models.CharField(
        max_length=100, blank=True, verbose_name=_("Numéro fiscal")
    )

    # Ancien champ avec choices
    statut_registre = models.CharField(
        max_length=4000,
        choices=LIEN_STATUT_CHOICE,
        default="--------",
        verbose_name=_("Statut au registre du commerce"),
    )

    # Nouvel attribut avec ForeignKey
    statut_registre_ref = models.ForeignKey(
        "StatutEntreprise",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Référence Statut au Registre"),
    )

    commentaire = models.TextField(blank=True, verbose_name=_("Commentaire"))
    couleur_commentaire = models.ForeignKey("CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Couleur Commentaire"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Dernière mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Données d'Enregistrement")
        verbose_name_plural = _("Données d'Enregistrement")

    def __str__(self):
        return f"Données Enregistrement {self.pk} - {self.acheteur}"


class Tendance(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur", null=True, on_delete=models.DO_NOTHING, verbose_name=_("Acheteur")
    )

    # Ancien attribut avec choices
    avis_commercial = models.CharField(
        max_length=100,
        choices=LIEN_AVIS_COMMERCIAL_CHOICE,
        blank=True,
        verbose_name=_("Avis commercial"),
    )

    # Nouvel attribut avec ForeignKey
    avis_commercial_ref = models.ForeignKey(
        "ModeleAvisCommercial",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Référence Avis Commercial"),
    )

    presse_media = models.CharField(
        max_length=100, blank=True, verbose_name=_("Presse et Médias")
    )
    principaux_concurrent = models.TextField(
        blank=True, verbose_name=_("Principaux concurrents")
    )
    
    plus_informations = models.CharField(max_length=100, choices=LIEN_PLUS_INFORMATIONS_NOTATION_CHOICE, blank=True, verbose_name=_("Plus d'informations sur la notation"))
    alarmes = models.CharField(max_length=100, choices=LIEN_ALARMES_CHOICE, blank=True, verbose_name=_("Alarmes"))
    
    commentaire = models.TextField(blank=True, verbose_name=_("Commentaire"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Dernière mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Tendance")
        verbose_name_plural = _("Tendances")

    def __str__(self):
        return f"Tendance {self.pk} - {self.acheteur}"


class ResponsableAcheteur(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    STATUS_MASCULIN = "Masculin"
    STATUS_FEMININ = "Feminin"
    STATUS_CHOICES = ((STATUS_MASCULIN, _("Masculin")), (STATUS_FEMININ, _("Féminin")))

    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    nom = models.CharField(_("Nom"), max_length=50, blank=True, null=True)
    prenom = models.CharField(_("Prénom"), max_length=50, blank=True, null=True)
    sexe = models.CharField(
        _("Sexe"),
        max_length=20,
        default=STATUS_MASCULIN,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
    )

    poste = models.CharField(
        _("Poste"), max_length=100, choices=BON_POST_CHOICES_CHOICES, blank=True
    )
    poste_ref = models.ForeignKey(
        "PosteEntreprise",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Référence Poste"),
    )

    nationalite = models.CharField(_("Nationalité"), max_length=100, blank=True)
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Responsable Acheteur")
        verbose_name_plural = _("Responsables Acheteurs")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_data = {
            "nom": self.nom,
            "prenom": self.prenom,
            "sexe": self.sexe,
            "poste_ref_id": self.poste_ref_id,  # Utilisez l'ID pour les FK
            "nationalite": self.nationalite,
            # Pour la détection de "Commentaires sur dirigeants"
            "commentaire": self.commentaire,
        }

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not is_new:
            self._check_for_changes_and_log_alerts()
            # Récupérez les données nécessaires et passez-les à la tâche Celery
            # Vous devrez affiner `changes_detected` pour qu'il soit sérialisable (ex: dict simple)
            # log_responsable_acheteur_changes.delay(self.pk, changes_detected)
        super().save(*args, **kwargs)
        self.__original_data = {
            "nom": self.nom,
            "prenom": self.prenom,
            "sexe": self.sexe,
            "poste_ref_id": self.poste_ref_id,
            "nationalite": self.nationalite,
            "commentaire": self.commentaire,
        }

    def _check_for_changes_and_log_alerts(self):
        # Mappage des champs aux codes internes des ElementSurveillance
        field_to_element_code = {
            "nom": "EXECUTIVE_CHANGE",
            "prenom": "EXECUTIVE_CHANGE",
            "sexe": "EXECUTIVE_CHANGE",
            "poste_ref_id": "EXECUTIVE_CHANGE",
            "nationalite": "EXECUTIVE_CHANGE",
            "commentaire": "EXECUTIVE_REPUTATION",  # Alerte spécifique pour les commentaires
        }

        changes_detected = {}

        for field_name, element_code in field_to_element_code.items():
            original_value = self.__original_data.get(field_name)
            current_value = getattr(self, field_name)

            if field_name.endswith("_id"):  # Pour les ForeignKey
                if original_value != current_value:
                    original_obj_display = "vide"
                    current_obj_display = "vide"
                    if original_value:
                        try:
                            original_obj = getattr(
                                self, field_name.replace("_id", "")
                            )._default_manager.get(pk=original_value)
                            original_obj_display = str(original_obj)
                        except models.ObjectDoesNotExist:
                            original_obj_display = "Inconnu (ID: {})".format(
                                original_value
                            )
                    if current_value:
                        try:
                            current_obj = getattr(
                                self, field_name.replace("_id", "")
                            )._default_manager.get(pk=current_value)
                            current_obj_display = str(current_obj)
                        except models.ObjectDoesNotExist:
                            current_obj_display = "Inconnu (ID: {})".format(
                                current_value
                            )

                    changes_detected.setdefault(element_code, []).append(
                        f"Le dirigeant '{self.nom} {self.prenom}' : le champ '{self._meta.get_field(field_name).verbose_name}' est passé de "
                        f"'{original_obj_display}' à '{current_obj_display}'."
                    )
            else:  # Champs non ForeignKey
                if str(original_value or "") != str(current_value or ""):
                    changes_detected.setdefault(element_code, []).append(
                        f"Le dirigeant '{self.nom} {self.prenom}' : le champ '{self._meta.get_field(field_name).verbose_name}' est passé de "
                        f"'{original_value or 'vide'}' à '{current_value or 'vide'}'."
                    )

        if changes_detected:
            portefeuilles_concernés = Portefeuille.objects.filter(
                portefeuilleclient__acheteur=self.acheteur
            ).distinct()

            for portefeuille in portefeuilles_concernés:
                for element_code, messages in changes_detected.items():
                    try:
                        element_surveillance = ElementSurveillance.objects.get(
                            code_interne=element_code
                        )
                        if portefeuille.elements_surveillance_actifs.filter(
                            pk=element_surveillance.pk
                        ).exists():
                            for message in messages:
                                AlerteLog.objects.create(
                                    portefeuille=portefeuille,
                                    acheteur=self.acheteur,
                                    element_surveille=element_surveillance,
                                    message=message,
                                    content_object=self,
                                    lu=False,  # <-- Assure-toi que c'est bien là
                                )
                                print(f"Alerte créée: {message}")
                    except ElementSurveillance.DoesNotExist:
                        print(
                            f"ATTENTION: Élément de surveillance avec code_interne '{element_code}' non trouvé. Veuillez l'ajouter à la liste des ElementSurveillance."
                        )

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.acheteur})"


class AntecedantsJuridique(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    dossier_faillite = models.CharField(
        _("Dossier de Faillite"), max_length=100, blank=True
    )
    jugement_cour = models.CharField(_("Jugement de Cour"), max_length=100, blank=True)
    antecedant_redressement = models.CharField(
        _("Antécédent de Redressement"), max_length=100, blank=True
    )
    autre = models.CharField(_("Autre"), max_length=100, blank=True)

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(
        _("Commentaire"), max_length=10000000, blank=True, null=True
    )

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Antécédent Juridique")
        verbose_name_plural = _("Antécédents Juridiques")

    def __str__(self):
        return f"Antécédent {self.id} - {self.acheteur}"


class RiskManagment(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    STATUS_AUCUN = "Aucun"
    STATUS_OUI = "Oui"
    STATUS_NON = "Non"
    STATUS_CHOICES = (
        (STATUS_AUCUN, _("Aucun")),
        (STATUS_OUI, _("Oui")),
        (STATUS_NON, _("Non")),
    )

    acheteur = models.ForeignKey(
        "Acheteur", null=True, on_delete=models.DO_NOTHING, verbose_name=_("Acheteur")
    )

    professionalisme = models.CharField(
        _("Professionnalisme"),
        max_length=20,
        default=STATUS_AUCUN,
        choices=STATUS_CHOICES,
    )
    organisation = models.CharField(
        _("Organisation"), max_length=20, default=STATUS_AUCUN, choices=STATUS_CHOICES
    )
    turn_over = models.CharField(
        _("Non départ des employés"),
        max_length=20,
        default=STATUS_AUCUN,
        choices=STATUS_CHOICES,
    )
    greve = models.CharField(
        _("Non grève"), max_length=20, default=STATUS_AUCUN, choices=STATUS_CHOICES
    )
    degradation_qualite = models.CharField(
        _("Non dégradation de la qualité du travail"),
        max_length=20,
        default=STATUS_AUCUN,
        choices=STATUS_CHOICES,
    )
    non_respect_condition = models.CharField(
        _("Respect des Employés"),
        max_length=20,
        default=STATUS_AUCUN,
        choices=STATUS_CHOICES,
    )

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Gestion des Risques")
        verbose_name_plural = _("Gestión des Risques")

    def __str__(self):
        return f"Gestion des Risques - {self.acheteur}"
    
    def get_management_image_base64(self):
        """Retourne l'image en Base64 pour l'intégration directe dans le HTML"""
        image_path = self.get_management_image_path()
        
        # Si le chemin est relatif, construire le chemin absolu
        if not os.path.isabs(image_path):
            image_path = os.path.join(settings.BASE_DIR, image_path)
        
        if os.path.exists(image_path):
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                
                # Déterminer le type MIME
                if image_path.endswith('.png'):
                    mime_type = 'image/png'
                elif image_path.endswith('.jpg') or image_path.endswith('.jpeg'):
                    mime_type = 'image/jpeg'
                elif image_path.endswith('.svg'):
                    mime_type = 'image/svg+xml'
                else:
                    mime_type = 'image/png'  # par défaut
                
                return f"data:{mime_type};base64,{encoded_string}"
        
        return None
    
    def get_management_image_path(self):
        """Retourne le chemin de l'image basé sur les statuts"""
        fields = [
            self.professionalisme,
            self.organisation,
            self.turn_over,
            self.greve,
            self.degradation_qualite,
            self.non_respect_condition
        ]
        
        oui_count = sum(1 for field in fields if field == self.STATUS_OUI)
        non_count = sum(1 for field in fields if field == self.STATUS_NON)
        
        # Logique de décision pour l'image
        if oui_count >= 4:
            return "main/static/management/bien.png"
        elif non_count >= 4:
            return "main/static/management/mauvais.png"
        else:
            return "main/static/management/passable.png"
        
    def get_management_image_path_report(self):
        fields = [
            self.professionalisme,
            self.organisation,
            self.turn_over,
            self.greve,
            self.degradation_qualite,
            self.non_respect_condition
        ]
        
        oui_count = sum(1 for field in fields if field == self.STATUS_OUI)
        non_count = sum(1 for field in fields if field == self.STATUS_NON)
        
        if oui_count >= 4:
            return "management/bien.png"
        elif non_count >= 4:
            return "management/mauvais.png"
        else:
            return "management/passable.png"

    def get_management_score(self):
        """Retourne le score de gestion des risques"""
        fields = [
            self.professionalisme,
            self.organisation,
            self.turn_over,
            self.greve,
            self.degradation_qualite,
            self.non_respect_condition
        ]
        
        oui_count = sum(1 for field in fields if field == self.STATUS_OUI)
        non_count = sum(1 for field in fields if field == self.STATUS_NON)
        
        return {
            'oui_count': oui_count,
            'non_count': non_count,
            'total': len(fields)
        }


class ConseilAdministration(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    nom = models.CharField(_("Nom"), max_length=100, default="Neant", blank=True)

    fonction_dans_le_conseil = models.CharField(
        _("Fonction dans le Conseil"),
        max_length=100,
        choices=BON_POST_CHOICES_CHOICES,
        blank=True,
    )
    fonction_dans_le_conseil_ref = models.ForeignKey(
        "PosteEntreprise",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Référence Fonction Conseil"),
    )

    numero_adresse = models.CharField(_("Numéro Adresse"), max_length=200, blank=True)
    rue_adresse = models.CharField(_("Rue Adresse"), max_length=200, blank=True)
    code_postale_adresse = models.CharField(
        _("Code Postal Adresse"), max_length=200, blank=True
    )

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Conseil d'Administration")
        verbose_name_plural = _("Conseils d'Administration")

    def __str__(self):
        return f"{self.nom} ({self.acheteur})"


class CompositionCapitalSocial(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    devise = models.ForeignKey(
        "Devise",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Dévise capital libéré"),
    )
    emis = models.DecimalField(
        _("Capital émis"),
        max_digits=100,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Montant du capital émis"),
    )
    publie = models.DecimalField(
        _("Capital publié"),
        max_digits=100,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Montant du capital publié"),
    )
    libere = models.DecimalField(
        _("Capital libéré"),
        max_digits=100,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Montant du capital libéré"),
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    history = HistoricalRecords()


    def __str__(self):
        return (
            f"Capital Social ({self.acheteur})"
            if self.acheteur
            else _("Composition Capital Social")
        )

    class Meta:
        verbose_name = _("Composition du Capital Social")
        verbose_name_plural = _("Compositions du Capital Social")


class CompositionAction(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    nom = models.CharField(_("Nom"), max_length=200, blank=True)
    prenom = models.CharField(_("Prénom"), max_length=200, blank=True)
    pourcentage = models.DecimalField(
        _("Pourcentage"),
        max_digits=100,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Pourcentage de détention d'actions"),
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    history = HistoricalRecords()


    def __str__(self):
        return (
            f"{self.nom} {self.prenom} - {self.pourcentage}%"
            if self.nom
            else _("Composition Action")
        )

    class Meta:
        verbose_name = _("Composition de l'Actionnariat")
        verbose_name_plural = _("Compositions de l'Actionnariat")


class OpinionCreditAcremac(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur", on_delete=models.DO_NOTHING, verbose_name=_("Acheteur")
    )
    risque_de_defaut = models.IntegerField(
        default=0, verbose_name=_("Risque de défaut")
    )
    risque_de_concentration_credit = models.IntegerField(
        default=0, verbose_name=_("Risque de concentration de crédit")
    )
    risque_de_reputation = models.IntegerField(
        default=0, verbose_name=_("Risque de réputation")
    )
    risque_pays = models.IntegerField(default=0, verbose_name=_("Risque pays"))
    risque_de_taux_dinteret = models.IntegerField(
        default=0, verbose_name=_("Risque de taux d'intérêt")
    )
    risque_de_liquidite = models.IntegerField(
        default=0, verbose_name=_("Risque de liquidité")
    )
    risque_eleve = models.IntegerField(default=0, verbose_name=_("Risque élevé"))
    risque_moyen = models.IntegerField(default=0, verbose_name=_("Risque moyen"))
    risque_faible = models.IntegerField(default=0, verbose_name=_("Risque faible"))
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire"),
    )
    montant_credit_maximum = models.DecimalField(
        _("Capital émis"),
        max_digits=100,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Montant crédit maximum conseillée"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


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
class Structure(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    nom = models.CharField(_("Nom"), max_length=200, blank=True)

    type_affiliation = models.CharField(
        max_length=100,
        choices=LIEN_ENTREPRISE_CHOICE,
        blank=True,
        verbose_name=_("Type d'affiliation"),
    )
    type_affiliation_ref = models.ForeignKey(
        "StructureEntreprise",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Référence Type d'affiliation"),
    )
    numero_adresse = models.CharField(_("Numéro adresse"), max_length=200, blank=True)
    rue_adresse = models.CharField(_("Rue adresse"), max_length=200, blank=True)
    code_postale_adresse = models.CharField(
        _("Code postal adresse"), max_length=200, blank=True
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    history = HistoricalRecords()


    def __str__(self):
        return self.nom or _("Filiale sans nom")

    class Meta:
        verbose_name = _("Filiale ou Branche")
        verbose_name_plural = _("Filiales ou Branches")


class AnalyseSectorielle(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), max_length=10000000, blank=True)
    impact_covid_19 = models.TextField(
        _("Impact COVID-19"), max_length=10000000, blank=True
    )

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    history = HistoricalRecords()


    def __str__(self):
        return _("Analyse sectorielle")

    class Meta:
        verbose_name = _("Analyse Sectorielle")
        verbose_name_plural = _("Analyses Sectorielles")


class CompteFinancier(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    

    XAF = 'XAF'  # Franc CFA d'Afrique centrale (CEMAC)
    XOF = 'XOF'  # Franc CFA d'Afrique de l'Ouest (UEMOA)
    EUR = 'EUR'  # Euro
    USD = 'USD'  # Dollar US
    CHF = 'CHF'  # Franc suisse
    GNF = 'GNF'  # Franc guinéen
    GHS = 'GHS'  # Cedi ghanéen
    MRU = 'MRU'  # Ouguiya mauritanien (nouvelle version, ex-MRO)
    ZAR = 'ZAR'  # Rand sud-africain

    # Maghreb
    DZD = 'DZD'  # Dinar algérien
    MAD = 'MAD'  # Dirham marocain
    TND = 'TND'  # Dinar tunisien
    LYD = 'LYD'  # Dinar libyen
    SDG = 'SDG'  # Livre soudanaise (même si Soudan ≠ Maghreb, souvent associée)

    # Autres monnaies africaines importantes
    NGN = 'NGN'  # Naira nigérian
    KES = 'KES'  # Shilling kényan
    TZS = 'TZS'  # Shilling tanzanien
    UGX = 'UGX'  # Shilling ougandais
    ETB = 'ETB'  # Birr éthiopien
    EGP = 'EGP'  # Livre égyptienne
    AOA = 'AOA'  # Kwanza angolais
    MWK = 'MWK'  # Kwacha malawite
    ZMW = 'ZMW'  # Kwacha zambien
    BWP = 'BWP'  # Pula botswanais

    STATUS_CHANGE = (
        (XAF, 'XAF'),
        (XOF, 'XOF'),
        (EUR, 'EUR'),
        (USD, 'USD'),
        (CHF, 'CHF'),
        (GNF, 'GNF'),
        (GHS, 'GHS'),
        (MRU, 'MRU'),
        (ZAR, 'ZAR'),
        (DZD, 'DZD'),
        (MAD, 'MAD'),
        (TND, 'TND'),
        (LYD, 'LYD'),
        (SDG, 'SDG'),
        (NGN, 'NGN'),
        (KES, 'KES'),
        (TZS, 'TZS'),
        (UGX, 'UGX'),
        (ETB, 'ETB'),
        (EGP, 'EGP'),
        (AOA, 'AOA'),
        (MWK, 'MWK'),
        (ZMW, 'ZMW'),
        (BWP, 'BWP'),
    )

    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    cabinet = models.CharField(max_length=200, blank=True, verbose_name=_("Cabinet"))
    requis_pour_deposer = models.CharField(
        max_length=200, blank=True, verbose_name=_("Requis pour déposer")
    )
    credibilite_cabinet = models.CharField(
        max_length=200,
        blank=True,
        choices=STATUS__OUI_NON,
        verbose_name=_("Crédibilité du cabinet pour ACREMAC"),
    )
    source = models.CharField(max_length=200, blank=True, verbose_name=_("Source"))
    presentation = models.CharField(
        max_length=200, blank=True, verbose_name=_("Présentation")
    )

    date_compte = models.DateField(
        blank=True, verbose_name=_("Début de période de compte N")
    )
    date_fin = models.DateField(
        blank=True, null=True, verbose_name=_("Fin clôture de compte N")
    )
    date_compte_n_moins_un = models.DateField(
        blank=True, null=True, verbose_name=_("Début de période de compte N-1")
    )
    date_fin_n_moins_un = models.DateField(
        blank=True, null=True, verbose_name=_("Fin clôture de compte N-1")
    )
    date_compte_n_moins_deux = models.DateField(
        blank=True, null=True, verbose_name=_("Début de période de compte N-2")
    )
    date_fin_n_moins_deux = models.DateField(
        blank=True, null=True, verbose_name=_("Fin clôture de compte N-2")
    )

    type_compte = models.CharField(
        max_length=200, null=True, blank=True, verbose_name=_("Type de compte")
    )
    devise = models.CharField(
        max_length=20,
        default=XAF,
        choices=STATUS_CHANGE,
        blank=True,
        verbose_name=_("Devise"),
    )
    type_bilan = models.CharField(
        max_length=255,
        choices=LIEN_TYPE_BILAN_CHOICE,
        default="--------",
        verbose_name=_("Type de bilan"),
    )
    type_bilan_ref = models.ForeignKey(
        "ModeleBilan",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Référence Type de bilan"),
    )

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire"),
    )
    commentaire = models.TextField(
        blank=True, max_length=10000000, verbose_name=_("Commentaire")
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            f"{self.acheteur} - {self.cabinet}"
            if self.acheteur
            else _("Compte Financier")
        )

    class Meta:
        verbose_name = _("Compte Financier")
        verbose_name_plural = _("Comptes Financiers")


class OperationEtHistorique(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    commentaire_ratios = models.TextField(
        blank=True, verbose_name=_("Commentaire sur les ratios")
    )
    description_complete_activite = models.TextField(
        blank=True, verbose_name=_("Description complète de l'activité")
    )
    importation = models.TextField(blank=True, verbose_name=_("Importation"))
    historique = models.TextField(blank=True, verbose_name=_("Historique"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            f"{self.acheteur} - {self.description_complete_activite[:50]}..."
            if self.acheteur
            else _("Opération et Historique")
        )

    class Meta:
        verbose_name = _("Opération et Historique")
        verbose_name_plural = _("Opérations et Historiques")


class ProprieteEtActif(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    locaux = models.CharField(
        max_length=255,
        choices=LIEN_COMPORTEMENT_PREMISES_CHOICE,
        blank=True,
        verbose_name=_("Locaux"),
    )
    locaux_ref = models.ForeignKey(
        "ModeleBail",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Référence sur les locaux"),
    )

    branche = models.CharField(max_length=255, blank=True, verbose_name=_("Branche"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            f"{self.acheteur} - {self.branche}"
            if self.acheteur
            else _("Propriété et Actif")
        )

    class Meta:
        verbose_name = _("Propriété et Actif")
        verbose_name_plural = _("Propriétés et Actifs")


class ConditionAchat(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    local = models.CharField(max_length=255, blank=True, verbose_name=_("Local"))
    importation = models.TextField(blank=True, verbose_name=_("Importation"))
    les_clients = models.TextField(blank=True, verbose_name=_("Les clients"))
    fournisseur = models.TextField(blank=True, verbose_name=_("Fournisseur"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            f"{self.acheteur} - {self.local}"
            if self.acheteur
            else _("Condition d'Achat")
        )

    class Meta:
        verbose_name = _("Condition d'Achat")
        verbose_name_plural = _("Conditions d'Achat")


class ConditionDeVente(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    local = models.CharField(max_length=255, blank=True, verbose_name=_("Local"))

    recouvrement_de_dette_jugement = models.CharField(
        max_length=255,
        choices=LIEN_COMPORTEMENT_JUGEMENT_CHOICE,
        default="--------",
        verbose_name=_("Recouvrement de dette jugement"),
    )
    recouvrement_de_dette_jugement_ref = models.ForeignKey(
        "ModeleComportementJugement",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Référence sur les locaux"),
    )

    comportement_de_paiement = models.CharField(
        max_length=255,
        choices=LIEN_COMPORTEMENT_PAIEMENT_CHOICE,
        default="--------",
        verbose_name=_("Comportement de paiement"),
    )
    comportement_de_paiement_ref = models.ForeignKey(
        "ModeleComportementPaiement",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Référence sur les locaux"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    def __str__(self):
        return f"Condition de vente for {self.acheteur} - {self.local}"

    class Meta:
        verbose_name = _("Condition de Vente")
        verbose_name_plural = _("Conditions de Vente")


class SommaireEtAvis(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire"),
    )
    commentaire = models.TextField(
        max_length=10000000, blank=True, verbose_name=_("Commentaire")
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    def __str__(self):
        return f"Sommaire et avis for {self.acheteur}"

    class Meta:
        verbose_name = _("Sommaire et Avis")
        verbose_name_plural = _("Sommaires et Avis")


class Advice(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur", on_delete=models.DO_NOTHING, verbose_name=_("Acheteur")
    )
    points_forts = models.TextField(
        max_length=10000000, blank=True, verbose_name=_("Points forts")
    )
    points_faibles = models.TextField(
        max_length=10000000, blank=True, verbose_name=_("Points faibles")
    )
    dynamisme_court_terme = models.TextField(
        max_length=10000000, blank=True, verbose_name=_("Dynamisme à court terme")
    )
    dynamisme_long_terme = models.TextField(
        max_length=10000000, blank=True, verbose_name=_("Dynamisme à long terme")
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    def __str__(self):
        return f"Conseils pour {self.acheteur}"

    class Meta:
        verbose_name = _("Conseil")
        verbose_name_plural = _("Conseils")


class Geopolitics(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur", on_delete=models.DO_NOTHING, verbose_name=_("Acheteur")
    )
    donnees_politiques = models.TextField(
        max_length=10000000, blank=True, verbose_name=_("Données politiques")
    )
    donnees_economiques = models.TextField(
        max_length=10000000, blank=True, verbose_name=_("Données économiques")
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    def __str__(self):
        return f"Geopolitics for {self.acheteur}"

    class Meta:
        verbose_name = _("Geopolitique")
        verbose_name_plural = _("Géopolitiques")


class Banquier(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    nom_banque = models.CharField(
        blank=True, max_length=200, verbose_name=_("Nom de la banque")
    )
    numero_compte = models.CharField(
        default="",
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("Numéro de compte"),
    )
    type_relation = models.CharField(
        blank=True, max_length=200, null=True, verbose_name=_("Type de relation")
    )
    numero = models.CharField(max_length=200, blank=True, verbose_name=_("Numéro"))
    rue = models.CharField(max_length=200, blank=True, verbose_name=_("Rue"))
    ville = models.ForeignKey(
        "Ville", on_delete=models.DO_NOTHING, verbose_name=_("Ville")
    )
    code_postal = models.CharField(
        max_length=200, blank=True, verbose_name=_("Code postal")
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire"),
    )
    commentaire = models.TextField(blank=True, verbose_name=_("Commentaire"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


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
# Debut Modules Bilan Anglais
##########################################################
##########################################################


# Debut Modules Bilan Anglais

class ActifA(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    # ... (champs existants)
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )

    biens_installations_equipements = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Biens, installations et équipements"),
    )
    inventaire = models.DecimalField(
        max_digits=100, decimal_places=2, null=True, blank=True
    )
    creances_commerciales_autres_creances = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Créances commerciales et autres"),
    )
    actif_impots_courant = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Actif d'Impôts courant"),
    )
    caisses_banques = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Caisse et banque"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="actifa_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            _("Actif bilan anglais : ")
            + str(self.id)
            + ". "
            + str(self.acheteur)
            + " ("
            + str(self.annee)
            + ")"
        )

    class Meta:
        verbose_name = _("Actif bilan anglais")
        verbose_name_plural = _("Actifs bilans anglais")

    @property
    def total_actifs_non_courants(self):
        """Calcule le total des actifs non-courants (immobilisés)."""
        return self.biens_installations_equipements or 0

    @property
    def total_actifs_courants(self):
        """Calcule le total des actifs courants."""
        fields = [self.inventaire, self.creances_commerciales_autres_creances, self.actif_impots_courant, self.caisses_banques]
        return sum(f or 0 for f in fields)
        
    @property
    def total_actif(self):
        """Calcule le total général de l'actif."""
        return self.total_actifs_non_courants + self.total_actifs_courants


class PassifA(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    # ... (champs existants)
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )

    capital_reserves = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Capital et Réserves"),
    )
    capital_declare = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Capital déclaré"),
    )
    benefices_non_distribues = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Bénéfices non distribués"),
    )

    pret_bancaire = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Prêt bancaire"),
    )
    compte_courant_administrateurs = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Compte courant des administrateurs"),
    )

    dettes_commerciales_autres_dettes = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dettes commerciales et autres dettes"),
    )
    decouvert_bancaire = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Découvert bancaire"),
    )
    impots = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Impôts"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="passifa_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            _("Passif bilan anglais : ")
            + str(self.id)
            + ". "
            + str(self.acheteur)
            + " ("
            + str(self.annee)
            + ")"
        )

    class Meta:
        verbose_name = _("Passif bilan anglais")
        verbose_name_plural = _("Passifs bilans anglais")

    @property
    def total_fonds_propres(self):
        """Calcule le total des fonds propres."""
        return (self.capital_reserves or 0) + (self.capital_declare or 0) + (self.benefices_non_distribues or 0)

    @property
    def total_passifs_non_courants(self):
        """Calcule le total des passifs à long terme."""
        fields = [self.pret_bancaire, self.compte_courant_administrateurs]
        return sum(f or 0 for f in fields)

    @property
    def total_passifs_courants(self):
        """Calcule le total des passifs courants."""
        fields = [self.dettes_commerciales_autres_dettes, self.decouvert_bancaire, self.impots]
        return sum(f or 0 for f in fields)
        
    @property
    def total_passif(self):
        """Calcule le total général du passif."""
        return self.total_fonds_propres + self.total_passifs_non_courants + self.total_passifs_courants
        
    @property
    def total_fonds_propres_passif(self):
        """Calcule le total fonds propres du passif."""
        pass


class ResultatA(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    # ... (champs existants)
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )

    produits_activites_ordinaires = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Produits des activités ordinaires"),
    )
    ventes = models.DecimalField(
        max_digits=100, decimal_places=2, null=True, blank=True
    )
    charges_exploitation = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Charges d'exploitation"),
    )
    frais_vente_generaux_administratifs = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Frais de vente, généraux et administratifs"),
    )
    autres_revenus = models.DecimalField(
        max_digits=100, decimal_places=2, null=True, blank=True
    )
    frais_financier = models.DecimalField(
        max_digits=100, decimal_places=2, null=True, blank=True
    )
    charge_impot_sur_revenu = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Charge d'impôt sur le revenu"),
    )
    autres_elements_resultat_global = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres éléments du résultat global"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="resultata_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            _("Résultat bilan anglais : ")
            + str(self.id)
            + ". "
            + str(self.acheteur)
            + " ("
            + str(self.annee)
            + ")"
        )

    class Meta:
        verbose_name = _("Résultat bilan anglais")
        verbose_name_plural = _("Résultat bilans anglais")

    @property
    def marge_brute(self):
        """Calcule la marge brute."""
        return (self.ventes or 0) - (self.charges_exploitation or 0)
    
    @property
    def resultat_exploitation(self):
        """Calcule le résultat d'exploitation (Operating Profit)."""
        return self.marge_brute - (self.frais_vente_generaux_administratifs or 0)
        
    @property
    def resultat_avant_interets_impots(self):
        """Calcule le bénéfice avant coûts financiers et impôts (EBIT)."""
        return self.resultat_exploitation + (self.autres_revenus or 0)
    
    @property
    def resultat_avant_impots(self):
        """Calcule le résultat avant impôts (PBT)."""
        return self.resultat_avant_interets_impots - (self.frais_financier or 0)
    
    @property
    def resultat_net(self):
        """Calcule le résultat net (Net Income)."""
        return self.resultat_avant_impots - (self.charge_impot_sur_revenu or 0)

    @property
    def benefices_non_distribues(self):
        """Calcule les bénéfices non distribués (Retained Earnings)."""
        return (self.resultat_net or 0) + (self.autres_elements_resultat_global or 0)

# Calcul des ratios
from decimal import Decimal

class RatiosAnglais:
    def __init__(self, actif: ActifA, passif: PassifA, resultat: ResultatA):
        self.actif = actif
        self.passif = passif
        self.resultat = resultat
    
    def _get_val(self, model, prop):
        return getattr(model, prop, Decimal('0')) or Decimal('0')

    @property
    def solvabilite(self):
        """ Solvabilité = Total passif / Total actif """
        total_actif = self._get_val(self.actif, 'total_actif')
        total_passif = self._get_val(self.passif, 'total_passif')
        if total_actif != 0:
            return total_passif / total_actif
        return None
        
    @property
    def autonomie_financiere(self):
        """ Autonomie financière = Total fonds propres / Total passif """
        fonds_propres = self._get_val(self.passif, 'total_fonds_propres')
        total_passif = self._get_val(self.passif, 'total_passif')
        if total_passif != 0:
            return fonds_propres / total_passif
        return None

    @property
    def rendement_capitaux_propres(self):
        """ Rendement des capitaux propres (ROE) = Résultat net / Total fonds propres """
        fonds_propres = self._get_val(self.passif, 'total_fonds_propres')
        resultat_net = self._get_val(self.resultat, 'resultat_net')
        if fonds_propres != 0:
            return resultat_net / fonds_propres
        return None
        
    @property
    def taux_marge_net(self):
        """ Taux de marge net = Résultat net / Ventes """
        ventes = self._get_val(self.resultat, 'ventes')
        resultat_net = self._get_val(self.resultat, 'resultat_net')
        if ventes != 0:
            return resultat_net / ventes
        return None

    @property
    def liquidite_generale(self):
        """ Ratio de liquidité générale = Actifs courants / Passifs courants """
        actifs_courants = self._get_val(self.actif, 'total_actifs_courants')
        passifs_courants = self._get_val(self.passif, 'total_passifs_courants')
        if passifs_courants != 0:
            return actifs_courants / passifs_courants
        return None
        
    @property
    def jour_recouvrement_moyen(self):
        """ Jours de recouvrement moyen = (Créances commerciales / Ventes) * 365 """
        creances = self._get_val(self.actif, 'creances_commerciales_autres_creances')
        ventes = self._get_val(self.resultat, 'ventes')
        if ventes != 0:
            return (creances / ventes) * 365
        return None
        
    @property
    def jour_paiement_moyen(self):
        """ Jours de paiement moyen = (Dettes commerciales / Coût des ventes) * 365 """
        dettes = self._get_val(self.passif, 'dettes_commerciales_autres_dettes')
        charges_exploitation = self._get_val(self.resultat, 'charges_exploitation')
        if charges_exploitation != 0:
            return (dettes / charges_exploitation) * 365
        return None
        
    @property
    def taux_rotation_creance(self):
        """Taux de rotation des créances = Ventes / Créances commerciales"""
        ventes = self._get_val(self.resultat, 'ventes')
        creances = self._get_val(self.actif, 'creances_commerciales_autres_creances')
        if creances != 0:
            return float(ventes) / float(creances)
        return None
        
    @property
    def taux_rotation_stock(self):
        """Taux de rotation des stocks = Ventes / Inventaire"""
        ventes = self._get_val(self.resultat, 'ventes')
        inventaire = self._get_val(self.actif, 'inventaire')
        if inventaire != 0:
            return float(ventes) / float(inventaire)
        return None
        
    @property
    def taux_rotation_actif(self):
        """Taux de rotation des actifs = Ventes / Actifs non courants"""
        ventes = self._get_val(self.resultat, 'ventes')
        actifs_non_courants = self._get_val(self.actif, 'total_actifs_non_courants')
        if actifs_non_courants != 0:
            return float(ventes) / float(actifs_non_courants)
        return None
        
    @property
    def ratio_endettement1(self):
        """Ratio d'endettement 1 = (Prêts bancaires + Dettes commerciales) / Total fonds propres et passif"""
        prets_bancaires = self._get_val(self.passif, 'pret_bancaire')
        dettes_commerciales = self._get_val(self.passif, 'dettes_commerciales_autres_dettes')
        total_passif = self._get_val(self.passif, 'total_passif')
        if total_passif != 0:
            return float(prets_bancaires + dettes_commerciales) / float(total_passif)
        return None
        
    @property
    def ratio_endettement2(self):
        """Ratio d'endettement 2 = Prêts bancaires / Actifs non courants"""
        prets_bancaires = self._get_val(self.passif, 'pret_bancaire')
        actifs_non_courants = self._get_val(self.actif, 'total_actifs_non_courants')
        if actifs_non_courants != 0:
            return float(prets_bancaires) / float(actifs_non_courants)
        return None
        
    @property
    def passif_cour_terme(self):
        """Passif court terme = Passifs courants / Actifs non courants"""
        passifs_courants = self._get_val(self.passif, 'total_passifs_courants')
        actifs_non_courants = self._get_val(self.actif, 'total_actifs_non_courants')
        if actifs_non_courants != 0:
            return float(passifs_courants) / float(actifs_non_courants)
        return None
        
    @property
    def ratios_couverture_interet(self):
        """Ratio de couverture des intérêts = EBIT / Frais financiers"""
        ebit = self._get_val(self.resultat, 'resultat_avant_interets_impots')
        frais_financiers = self._get_val(self.resultat, 'frais_financier')
        if frais_financiers != 0:
            return float(ebit) / float(frais_financiers)
        return None
        
    @property
    def ratio_g_score_fin(self):
        """Ratio G-Score financier = Actifs non courants / Total actif"""
        actifs_non_courants = self._get_val(self.actif, 'total_actifs_non_courants')
        total_actif = self._get_val(self.actif, 'total_actif')
        if total_actif != 0:
            return float(actifs_non_courants) / float(total_actif)
        return None
        
    @property
    def ratio_endettement_g_score(self):
        """Ratio d'endettement G-Score = Prêts bancaires / Fonds propres"""
        prets_bancaires = self._get_val(self.passif, 'pret_bancaire')
        fonds_propres = self._get_val(self.passif, 'total_fonds_propres')
        if fonds_propres != 0:
            return float(prets_bancaires) / float(fonds_propres)
        return None


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


# Debut Modules Bilan Classique

# Actif
class ActifC(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    # ... (les champs existants) ...
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )

    capital_souscrit_non_app = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Capital sousc. non app"),
    )
    frais_recherche_developpement = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Frais recherche developpement"),
    )
    brevet_licence_logiciels = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Brevet licence logiciels"),
    )
    fonds_commercial = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Fonds commercial"),
    )
    autres_immobilisations_incorporelles = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres immobilisations incorporelles"),
    )
    terrains = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Terrains"),
    )
    constructions = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Constructions"),
    )
    materiels_et_outils = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Materiels et outils"),
    )
    materiel_de_transport = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Materiel de transport"),
    )
    autres_immos_corp = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres immos corp"),
    )
    immos_en_cours = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Immos en cours"),
    )
    avances_et_acptes = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Avances et acptes"),
    )
    participations = models.DecimalField(
        max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Participations")
    )
    prets = models.DecimalField(
        max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Prets")
    )
    autres = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres"),
    )
    stocks_mp = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Stocks mp"),
    )
    stocks_encours_mp = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Stocks encours mp"),
    )
    stocks_pf = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Stocks pf"),
    )
    stocks_encours_pf = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Stocks encours pf"),
    )
    stocks_encours_services = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Stocks encours services"),
    )
    stocks_mses = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Stocks mses"),
    )
    avances_acptes_verses = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Avances acptes verses"),
    )
    clients_et_cptes_rattaches = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Clients et cptes rattaches"),
    )
    autres_creances = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres creances"),
    )
    valeurs_a_encaisser = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Valeurs a encaisser"),
    )
    banques_cheques_postaux_caisse = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Banques cheques postaux caisse"),
    )
    cca = models.DecimalField(
        max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Cca")
    )
    charges_a_repartir_et_frais_etablissement = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Charges a repartir et frais etablissement"),
    )
    primes_de_rbt = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Primes de rbt"),
    )
    eca = models.DecimalField(
        max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Eca")
    )
    eene = models.DecimalField(
        max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Eene")
    )
    effectif = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Effectif"),
    )
    amortissements = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Amortissements"),
    )
    provisions_stocks = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Provisions stocks"),
    )
    provisions_creances = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Provisions creances"),
    )
    provisions_vmp = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Provisions vmp"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="actif_classique_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            _("Actif bilan classique : ")
            + str(self.id)
            + ". "
            + str(self.acheteur)
            + " ("
            + str(self.annee)
            + ")"
        )

    class Meta:
        verbose_name = _("Actif bilan classique")
        verbose_name_plural = _("Actifs bilans classiques")

    @property
    def elements_incorporels(self):
        """Calcule le total des éléments incorporels."""
        fields = [
            self.frais_recherche_developpement,
            self.brevet_licence_logiciels,
            self.fonds_commercial,
            self.autres_immobilisations_incorporelles,
        ]
        return sum(f or 0 for f in fields)

    @property
    def elements_corporels(self):
        """Calcule le total des éléments corporels."""
        fields = [
            self.terrains,
            self.constructions,
            self.materiels_et_outils,
            self.materiel_de_transport,
            self.autres_immos_corp,
            self.immos_en_cours,
            self.avances_et_acptes,
        ]
        return sum(f or 0 for f in fields)

    @property
    def elements_financiers(self):
        """Calcule le total des éléments financiers."""
        fields = [self.participations, self.prets, self.autres]
        return sum(f or 0 for f in fields)

    @property
    def total_I(self):
        """Total Actif Immobilisé (Immobilisations nettes)"""
        return (
            self.elements_incorporels
            + self.elements_corporels
            + self.elements_financiers
        )

    @property
    def stocks(self):
        """Calcule le total des stocks."""
        fields = [
            self.stocks_mp,
            self.stocks_encours_mp,
            self.stocks_pf,
            self.stocks_encours_pf,
            self.stocks_encours_services,
            self.stocks_mses,
        ]
        return sum(f or 0 for f in fields)

    @property
    def creances(self):
        """Calcule le total des créances."""
        fields = [
            self.avances_acptes_verses,
            self.clients_et_cptes_rattaches,
            self.autres_creances,
        ]
        return sum(f or 0 for f in fields)

    @property
    def disponibilites_vmp(self):
        """Calcule le total des disponibilités et VMP."""
        fields = [self.valeurs_a_encaisser, self.banques_cheques_postaux_caisse]
        return sum(f or 0 for f in fields)

    @property
    def total_II(self):
        """Total Actif Circulant (Stocks + Créances + Disponibilités)"""
        return self.stocks + self.creances + self.disponibilites_vmp

    @property
    def compte_regul(self):
        """Calcule le total des comptes de régularisation."""
        fields = [self.cca]
        return sum(f or 0 for f in fields)

    @property
    def total_III(self):
        """Total des Comptes de Régularisation."""
        return self.compte_regul

    @property
    def general_total(self):
        """Total général de l'actif."""
        return self.total_I + self.total_II + self.total_III + (self.capital_souscrit_non_app or 0)


# Passif
class PassifC(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    # ... (les champs existants) ...
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    capital_social = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Capital social"),
    )
    primes = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Primes"),
    )
    ecarts_de_reevaluation = models.DecimalField(
        max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Eca")
    )
    reserve = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Reserve"),
    )
    report_a_nouveau = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Report a nouveau"),
    )
    resultat_exercice = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Resultat exercice"),
    )
    subv_invest = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Subventions investies"),
    )
    provision_regl = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Provision regle"),
    )
    emprunts = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Emprunts"),
    )
    dette_credit_bail_contrat_assimile = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Credit lease debts and related contracts"),
    )
    dettes_financiere_diverses = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dettes financiere diverses"),
    )
    provision_financiere_risque_charge = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Provision financiere risque charge"),
    )
    dettes_fournisseurs_divers = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dettes fournisseurs divers"),
    )
    avance_et_acomptes_recu = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Avance et acomptes recu"),
    )
    dettes = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dettes"),
    )
    dettes_fiscales_sociales = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dettes fiscales sociales"),
    )
    autres_dettes = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres dettes"),
    )
    banques_credit_escompte = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Banques credit escompte"),
    )
    banque_credit_caisse = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Banque credit caisse"),
    )
    banques_decouvert = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Banques decouvert"),
    )
    ecart_conversion_passif = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Ecart conversion passif"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="passif_classique_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            _("Passif bilan classique : ")
            + str(self.id)
            + ". "
            + str(self.acheteur)
            + " ("
            + str(self.annee)
            + ")"
        )

    class Meta:
        verbose_name = _("Passif bilan classique")
        verbose_name_plural = _("Passifs bilans classiques")

    @property
    def total_I(self):
        """Calcule le total des capitaux propres (I)."""
        fields = [
            self.capital_social,
            self.primes,
            self.ecarts_de_reevaluation,
            self.reserve,
            self.report_a_nouveau,
            self.resultat_exercice,
            self.subv_invest,
            self.provision_regl,
        ]
        return sum(f or 0 for f in fields)

    @property
    def total_II(self):
        """Calcule le total des dettes financières et ressources assimilées (II)."""
        fields = [
            self.emprunts,
            self.dette_credit_bail_contrat_assimile,
            self.dettes_financiere_diverses,
            self.provision_financiere_risque_charge,
        ]
        return sum(f or 0 for f in fields)

    @property
    def total_III(self):
        """Calcule le total des dettes du passif circulant (III)."""
        fields = [
            self.dettes_fournisseurs_divers,
            self.avance_et_acomptes_recu,
            self.dettes,
            self.dettes_fiscales_sociales,
            self.autres_dettes,
            self.banques_credit_escompte,
            self.banque_credit_caisse,
            self.banques_decouvert,
        ]
        return sum(f or 0 for f in fields)

    @property
    def total_IV(self):
        """Calcule le total des comptes de régularisation (IV)."""
        return self.ecart_conversion_passif or 0

    @property
    def total_general(self):
        """Calcule le total général du passif."""
        return self.total_I + self.total_II + self.total_III + self.total_IV


# Compte de Résultat
class ResultatC(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    # ... (les champs existants) ...
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    vente_de_mdses = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Vente de mdses"),
    )
    ventes_de_produits_fabriques = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Ventes de produits fabriques"),
    )
    travaux_services_vendus = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Travaux services vendus"),
    )
    produit_accessoires = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Produit accessoires"),
    )
    production_imblise = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Production imblise"),
    )
    subventions_exploitations = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Subventions exploitations"),
    )
    production_stockee = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Production stockee"),
    )
    reprises_de_provision = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Reprises de provision"),
    )
    transferts_charges = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Transferts charges"),
    )
    autres_produits = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres produits"),
    )
    achat_mdses = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Achat mdses"),
    )
    variation_stock_mdses = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Variation stock mdses"),
    )
    achat_mp_autres_appro = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Achat mp autres appro"),
    )
    var_stk_mp_app = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Var stk mp app"),
    )
    autres_achats = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres achats"),
    )
    variation_de_stocks_autres_appro = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Variation de stocks autres appro"),
    )
    transports = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Transports"),
    )
    services_ext = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Services ext"),
    )
    impots_taxes = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Impots taxes"),
    )
    autres_charges_valeur_ajoutee = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres charges valeur ajoutee"),
    )
    charges_personnel = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Charges personnel"),
    )
    dotation_aux_amorts = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dotation aux amorts"),
    )
    dotation_aux_provisions = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dotation aux provisions"),
    )
    autres_charges_excedent_brute = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres charges excedent brute"),
    )
    revenus_fin_assimiles = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Revenus fin assimiles"),
    )
    prof_vmp_et_cre_actif_immo = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Prof vmp et cre actif immo"),
    )
    interets_produit_assim = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Interets produit assim"),
    )
    reprise_prov_et_transfert = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Reprise prov et transfert"),
    )
    diff_positive_de_change = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Diff positive de change"),
    )
    prod_nets_cessions_vmp = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Prod nets cessions vmp"),
    )
    dap = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dot. aux prov. & depreciations"),
    )
    frais_fin_charges_assi = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Frais fin. & chrges assimilées"),
    )
    diff_negatives_de_change = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Diff negatives de change"),
    )
    ch_nettes_cessions_vmp = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Ch nettes cessions vmp"),
    )
    sur_op_gestion_prod_except = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Sur op gestion prod except"),
    )
    sur_op_en_capital_prod_except = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Sur op en capital prod except"),
    )
    reprise_prov_transfert = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Reprise prov transfert"),
    )
    sur_op_gestion_charg_except = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Sur op gestion charg except"),
    )
    sur_op_en_capital_charg_except = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Sur op en capital charg except"),
    )
    dap_et_transfert_charg_except = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dap et transfert charg except"),
    )
    participation_salairies = models.DecimalField(
        _("Participations des salariés"),
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
    )
    impot_sur_benefices = models.DecimalField(
        _("Impôts sur les bénéfices"),
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="resultat_classique_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            _("Résultat bilan classique : ")
            + str(self.id)
            + ". "
            + str(self.acheteur)
            + " ("
            + str(self.annee)
            + ")"
        )

    class Meta:
        verbose_name = _("Résultat bilan classique")
        verbose_name_plural = _("Résultats bilans classiques")

    @property
    def ca(self):
        """Calcule le chiffre d'affaires (ventes)."""
        fields = [self.vente_de_mdses, self.ventes_de_produits_fabriques, self.travaux_services_vendus, self.produit_accessoires]
        return sum(f or 0 for f in fields)
    
    @property
    def total_I(self):
        """Calcule le total des produits d'activités ordinaires."""
        fields = [self.ca, self.production_imblise, self.subventions_exploitations, self.production_stockee, self.reprises_de_provision, self.transferts_charges, self.autres_produits]
        return sum(f or 0 for f in fields)

    @property
    def marge_brute(self):
        """Calcule la marge commerciale brute."""
        return (self.vente_de_mdses or 0) - (self.achat_mdses or 0) + (self.variation_stock_mdses or 0)

    @property
    def valeur_ajoutee(self):
        """Calcule la valeur ajoutée."""
        return self.total_I - (self.achat_mp_autres_appro or 0) - (self.var_stk_mp_app or 0) - (self.autres_achats or 0) - (self.variation_de_stocks_autres_appro or 0) - (self.transports or 0) - (self.services_ext or 0) - (self.impots_taxes or 0) - (self.autres_charges_valeur_ajoutee or 0)

    @property
    def excedent_brut_ex(self):
        """Calcule l'excédent brut d'exploitation."""
        return self.valeur_ajoutee - (self.charges_personnel or 0)

    @property
    def resultat_exploitation(self):
        """Calcule le résultat d'exploitation."""
        return self.excedent_brut_ex - (self.dotation_aux_amorts or 0) - (self.dotation_aux_provisions or 0) - (self.autres_charges_excedent_brute or 0)

    @property
    def financier_total_I(self):
        """Calcule le total des produits financiers."""
        fields = [self.revenus_fin_assimiles, self.prof_vmp_et_cre_actif_immo, self.interets_produit_assim, self.reprise_prov_et_transfert, self.diff_positive_de_change, self.prod_nets_cessions_vmp]
        return sum(f or 0 for f in fields)

    @property
    def financier_total_II(self):
        """Calcule le total des charges financières."""
        fields = [self.dap, self.frais_fin_charges_assi, self.diff_negatives_de_change, self.ch_nettes_cessions_vmp]
        return sum(f or 0 for f in fields)
    
    @property
    def resultat_financier(self):
        """Calcule le résultat financier."""
        return self.financier_total_I - self.financier_total_II

    @property
    def resultat_courant_avant_impots(self):
        """Calcule le résultat courant avant impôts."""
        return self.resultat_exploitation + self.resultat_financier

    @property
    def excep_total_I(self):
        """Calcule le total des produits exceptionnels."""
        fields = [self.sur_op_gestion_prod_except, self.sur_op_en_capital_prod_except, self.reprise_prov_transfert]
        return sum(f or 0 for f in fields)
    
    @property
    def excep_total_II(self):
        """Calcule le total des charges exceptionnelles."""
        fields = [self.sur_op_gestion_charg_except, self.sur_op_en_capital_charg_except, self.dap_et_transfert_charg_except]
        return sum(f or 0 for f in fields)

    @property
    def resultat_excep(self):
        """Calcule le résultat exceptionnel."""
        return self.excep_total_I - self.excep_total_II

    @property
    def resultat_exercice(self):
        """Calcule le résultat net de l'exercice."""
        return self.resultat_courant_avant_impots + self.resultat_excep - (self.participation_salairies or 0) - (self.impot_sur_benefices or 0)


### Calcul des Ratios Financiers

# En plus des calculs internes aux modèles, voici une structure de classe pour calculer les ratios financiers 
# à partir des données des bilans et du compte de résultat. Cette logique est généralement mieux isolée dans une classe 
# dédiée pour la clarté et la réutilisation.


from decimal import Decimal

# Dans un fichier utils.py ou similaire
class RatiosClassique:
    def __init__(self, actif_c: ActifC, passif_c: PassifC, resultat_c: ResultatC):
        self.actif = actif_c
        self.passif = passif_c
        self.resultat = resultat_c

    def _get_value(self, model, field_name):
        """Récupère une valeur en toute sécurité et retourne 0 si elle est None."""
        return getattr(model, field_name, Decimal('0')) or Decimal('0')

    # Ratios de Structure financière
    # -----------------------------
    @property
    def fonds_de_roulement(self):
        """
        Calcule le Fonds de Roulement Net Global (FRNG).
        FRNG = Total des capitaux permanents - Actifs immobilisés
        """
        fdr = self.passif.total_I + self.passif.total_II - self.actif.total_I
        return fdr if self.actif and self.passif else None
    
    @property
    def fonds_de_roulement_normatif(self):
        """
        Calcule le Fonds de Roulement Normatif (FRNO).
        FRNO = (Dettes à court terme - Disponibilités) / Actif circulant
        """
        if self.actif and self.passif:
            dettes_court_terme = self.passif.total_III
            disponibilites = self.actif.disponibilites_vmp
            actif_circulant = self.actif.total_II
            
            if actif_circulant and actif_circulant != 0:
                return (dettes_court_terme - disponibilites) / actif_circulant
        return None

    @property
    def autonomie_fin(self):
        """
        Calcule le ratio d'autonomie financière.
        Autonomie financière = Capitaux propres / Total du bilan
        """
        if self.passif.total_general and self.passif.total_general != 0:
            return (self.passif.total_I / self.passif.total_general)
        return None

    # Ratios de Liquidité
    # -----------------------------
    @property
    def liquidite_reduite(self):
        """
        Calcule le ratio de liquidité réduite (Quick Ratio).
        Il mesure la capacité à payer les dettes à court terme sans compter les stocks.
        Liquidité réduite = (Actif circulant - Stocks) / Dettes à court terme
        """
        total_actif_circulant = self.actif.total_II
        stocks = self.actif.stocks
        # Les dettes à court terme correspondent aux dettes du passif circulant
        dettes_court_terme = self.passif.total_III
        
        if dettes_court_terme and dettes_court_terme != 0:
            return (total_actif_circulant - stocks) / dettes_court_terme
        return None

    @property
    def liquidite_immediat(self):
        """
        Calcule le ratio de liquidité immédiate (Cash Ratio).
        Il mesure la capacité à payer les dettes à court terme avec la trésorerie disponible.
        Liquidité immédiate = (Disponibilités + VMP) / Dettes à court terme
        """
        disponibilites = self.actif.disponibilites_vmp
        dettes_court_terme = self.passif.total_III
        
        if dettes_court_terme and dettes_court_terme != 0:
            return disponibilites / dettes_court_terme
        return None
    
    @property
    def chiffre_d_affaires(self):
        """
        Calcule le Chiffre d'affaires (CA).
        CA = Total des ventes et produits d'activité
        """
        return self.resultat.ca
    
    @property
    def chiffre_d_affaires_hors_taxe(self):
        """
        Calcule le Chiffre d'affaires hors taxe (CA HT).
        Dans la plupart des cas, le CA est déjà HT dans les comptes.
        """
        return self.resultat.ca
    
    # Ratios de Rentabilité
    # -----------------------------
    @property
    def rentabilite_economique(self):
        """
        Mesure la rentabilité de l'ensemble des capitaux investis.
        Rentabilité économique = Résultat d'exploitation / Total Actif
        """
        if self.actif.general_total and self.actif.general_total != 0:
            return self.resultat.resultat_exploitation / self.actif.general_total
        return None

    @property
    def rentabilite_fin(self):
        """
        Mesure la rentabilité des capitaux propres.
        Rentabilité financière = Résultat net / Capitaux propres
        """
        capitaux_propres = self.passif.total_I
        if capitaux_propres and capitaux_propres != 0:
            return self.resultat.resultat_exercice / capitaux_propres
        return None
    
    @property
    def rentabilite_de_loutil_de_production(self):
        """
        Mesure la rentabilité de l'outil de production (ROP).
        ROP = Valeur ajoutée / (Immobilisations brutes + BFR)
        """
        valeur_ajoutee = self.resultat.valeur_ajoutee
        immobilisations_brutes = self.actif.total_I
        bfr = (self.actif.stocks + self.actif.creances) - self.passif.total_III
        
        if (immobilisations_brutes + bfr) and (immobilisations_brutes + bfr) != 0:
            return valeur_ajoutee / (immobilisations_brutes + bfr)
        return None
    
    @property
    def couverture_des_frais_financiers(self):
        """
        Mesure la couverture des frais financiers (CFF).
        CFF = Résultat d'exploitation / Charges financières
        """
        charges_financieres = self.resultat.financier_total_II
        if charges_financieres and charges_financieres != 0:
            return self.resultat.resultat_exploitation / charges_financieres
        return None
        
    # Ratios de Gestion
    # -----------------------------
    @property
    def rotation_des_stock_de_mp(self):
        """
        Mesure le nombre de jours de stocks de matières premières.
        Rotation = (Stocks de MP / Achats de MP) * 360
        """
        if self.resultat.achat_mp_autres_appro and self.resultat.achat_mp_autres_appro != 0:
            return (self.actif.stocks_mp / self.resultat.achat_mp_autres_appro) * 360
        return None

    @property
    def rotation_des_stock_de_pf(self):
        """
        Mesure le nombre de jours de stocks de produits finis.
        Rotation = (Stocks de PF / Coût de production) * 360
        """
        # Le coût de production n'est pas directement disponible, on utilise une approximation
        # Coût de production = Production de l'exercice - Production stockée
        cout_prod_approx = (self.resultat.ventes_de_produits_fabriques or 0) - (self.resultat.production_stockee or 0)
        if cout_prod_approx and cout_prod_approx != 0:
            return (self.actif.stocks_pf / cout_prod_approx) * 360
        return None
    
    @property
    def rotation_des_stock_de_marchandises(self):
        """
        Mesure la rotation des stocks de marchandises.
        Rotation = (Stocks de marchandises / Coût des marchandises vendues) * 360
        """
        cout_marchandises_vendues = (self.resultat.achat_mdses or 0) - (self.resultat.variation_stock_mdses or 0)
        if cout_marchandises_vendues and cout_marchandises_vendues != 0:
            return (self.actif.stocks_mses / cout_marchandises_vendues) * 360
        return None
    
    @property
    def rotation_des_stock_de_services(self):
        """
        Mesure la rotation des stocks de services.
        Rotation = (Stocks en-cours services / Coût des services) * 360
        """
        cout_services_approx = (self.resultat.travaux_services_vendus or 0) - (self.resultat.production_stockee or 0)
        if cout_services_approx and cout_services_approx != 0:
            return (self.actif.stocks_encours_services / cout_services_approx) * 360
        return None

    @property
    def credit_clients(self):
        """
        Mesure le délai de paiement accordé aux clients en jours.
        Crédit clients = (Créances clients / Chiffre d'affaires) * 360
        """
        if self.resultat.ca and self.resultat.ca != 0:
            return (self.actif.clients_et_cptes_rattaches / self.resultat.ca) * 360
        return None
        
    @property
    def credits_fournisseurs(self):
        """
        Mesure le délai de paiement obtenu des fournisseurs en jours.
        Crédits fournisseurs = (Dettes fournisseurs / Achats) * 360
        """
        # On utilise le total des achats
        achats = (self.resultat.achat_mdses or 0) + (self.resultat.achat_mp_autres_appro or 0) + (self.resultat.autres_achats or 0)
        if achats and achats != 0:
            return (self.passif.dettes_fournisseurs_divers / achats) * 360
        return None
    
    
    @property
    def solvabilite(self):
        """
        Calcule le ratio de solvabilité.
        Solvabilité = Capitaux Propres / Total Actif
        """
        total_actif = self._get_value(self.actif, 'general_total')
        capitaux_propres = self._get_value(self.passif, 'total_I')
        
        if total_actif and total_actif != Decimal('0'):
            # Convertir en float pour éviter les erreurs de division de Decimal si nécessaire
            return float(capitaux_propres) / float(total_actif)
        return None
    
    
    
    @property
    def rendement_capitaux_propres(self):
        """
        Calcule le rendement des capitaux propres (ROE).
        ROE = Résultat net / Capitaux propres
        """
        resultat_net = self._get_value(self.resultat, 'resultat_exercice')
        capitaux_propres = self._get_value(self.passif, 'total_I')

        if capitaux_propres and capitaux_propres != Decimal('0'):
            return float(resultat_net) / float(capitaux_propres)
        return None
    
    @property
    def levier_financier(self):
        """
        Calcule le levier financier.
        Levier = Dettes financières / Capitaux propres
        """
        capitaux_propres = self._get_value(self.passif, 'total_I')
        dettes_financieres = self._get_value(self.passif, 'total_II')
        
        if capitaux_propres and capitaux_propres != Decimal('0'):
            return float(dettes_financieres) / float(capitaux_propres)
        return None

    @property
    def capacite_remboursement(self):
        """
        Calcule la capacité de remboursement.
        Capacité = Dettes financières / CAF
        """
        # CAF (Capacité d'Autofinancement) approximative
        caf = (self.resultat.resultat_exercice or 0) + (self.resultat.dotation_aux_amorts or 0)
        dettes_financieres = self._get_value(self.passif, 'total_II')
        
        if caf and caf != Decimal('0'):
            return float(dettes_financieres) / float(caf)
        return None

    @property
    def besoin_en_fond_roulement(self):
        """
        Calcule le Besoin en Fonds de Roulement (BFR).
        BFR = (Stocks + Créances) - Dettes à court terme
        """
        stocks_creances = self.actif.stocks + self.actif.creances
        dettes_court_terme = self.passif.total_III
        return stocks_creances - dettes_court_terme

    @property
    def bfr_exploitation(self):
        """
        Calcule le BFR d'exploitation.
        BFR Exploitation = (Stocks + Créances clients) - Dettes fournisseurs
        """
        stocks_creances_clients = self.actif.stocks + self.actif.clients_et_cptes_rattaches
        dettes_fournisseurs = self.passif.dettes_fournisseurs_divers
        return stocks_creances_clients - dettes_fournisseurs

    @property
    def delai_rotation_stocks(self):
        """
        Calcule le délai moyen de rotation des stocks.
        Délai = (Stocks / Coût des ventes) * 360
        """
        cout_ventes = (self.resultat.achat_mdses or 0) + (self.resultat.achat_mp_autres_appro or 0)
        if cout_ventes and cout_ventes != 0:
            return (self.actif.stocks / cout_ventes) * 360
        return None


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

# Enumération des types de bilan
TYPE_BILAN_CHOICES = (
    ("annuel", "Bilan annuel"),
    ("semestriel", "Bilan semestriel"),
)

# Ajoute cette énumération quelque part au-dessus de la classe Assets
SEMESTRE_CHOICES = (
    (1, "1er semestre (Janvier - Juin)"),
    (2, "2e semestre (Juillet - Décembre)"),
)


# Actifs
class Assets(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    type_bilan = models.CharField(
        max_length=20,
        choices=TYPE_BILAN_CHOICES,
        default="annuel",
        verbose_name=_("Type de bilan"),
        help_text=_("Précise s’il s’agit d’un bilan annuel ou semestriel."),
    )
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    semestre = models.PositiveSmallIntegerField(
        choices=SEMESTRE_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Semestre"),
        help_text=_("Laisser vide si le bilan est annuel."),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )

    caisse = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Caisse"),
    )
    # ASSETS
    # At Sight
    banques_centrales = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("-Banques centrales"),
    )
    tresorerie_cpp = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("-Trésorerie, CCP"),
    )
    autres_ets_credit = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("-Autres établissements de crédit"),
    )

    a_terme = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("A Terme"),
    )

    # Claims on Customers
    ## Commercial paper portofolio
    credits_campagne = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("-Crédits de campagne"),
    )
    credits_ordinaire = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("-Crédits ordinaires"),
    )
    ## Other Customer Contests
    credits_campagne_acc = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("-Crédits de campagne"),
    )
    credits_ordinaire_acc = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("-Crédits ordinaires"),
    )

    creances_ordinaires = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Créances ordinaires"),
    )
    affacturage = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Affacturage"),
    )

    titres_placement = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("TITRES DE PLACEMENT"),
    )
    immobilisation_fin = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("IMMOBILISATIONS FINANCIÈRES"),
    )
    operation_credit_bail = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("OPÉRATIONS DE CRÉDIT-BAIL ET ASSIMILÉES"),
    )
    immobilisation_incorporelle = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("IMMOBILISATIONS INCORPORELLES"),
    )
    immobilisation_corporelle = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("IMMOBILISATIONS CORPORELLES"),
    )
    actionnaire_ou_associe = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("ACTIONNAIRES OU ASSOCIÉS"),
    )
    autres_actifs = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("AUTRES ACTIFS"),
    )
    comptes_commande_divers = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("COMPTES DE COMMANDES ET DIVERS"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="assets_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    def __str__(self):
        libelle = f"{_('Actif bilan bancaire')} : {self.id}. {self.acheteur}"
        if self.annee:
            libelle += f" ({self.annee})"
        if self.semestre:
            libelle += f" - {self.get_semestre_display()}"  # Utilisation de la méthode intégrée
        return libelle

    class Meta:
        verbose_name = _("Actif bilan bancaire")
        verbose_name_plural = _("Actifs bilans bancaires")

    # ---------------------------------------------------
    #  Liste des methodes utiles pour ce model
    # ---------------------------------------------------

    @property
    def a_vue(self):
        """
        Calcule la somme des avoirs à vue.
        """
        fields_to_sum = [
            self.banques_centrales,
            self.tresorerie_cpp,
            self.autres_ets_credit,
        ]
        return sum(field or 0 for field in fields_to_sum)

    @property
    def pret_interbancaire(self):
        """
        Calcule le total des prêts interbancaires (à vue + à terme).
        """
        return self.a_vue + (self.a_terme or 0)

    @property
    def porteuille_papier_commercial(self):
        """
        Calcule le total du portefeuille de papiers commerciaux.
        """
        fields_to_sum = [self.credits_campagne, self.credits_ordinaire]
        return sum(field or 0 for field in fields_to_sum)

    @property
    def autres_concours_clients(self):
        """
        Calcule le total des autres concours à la clientèle.
        """
        fields_to_sum = [self.credits_campagne_acc, self.credits_ordinaire_acc]
        return sum(field or 0 for field in fields_to_sum)

    @property
    def creance_sur_la_clientele(self):
        """
        Calcule le total des créances sur la clientèle.
        """
        return (
            self.porteuille_papier_commercial
            + self.autres_concours_clients
            + (self.creances_ordinaires or 0)
            + (self.affacturage or 0)
        )

    @property
    def total_assets(self):
        """
        Calcule et retourne la somme de tous les champs financiers de l'actif.
        Traite les valeurs None comme 0 pour éviter les erreurs de calcul.
        """
        fields_to_sum = [
            self.caisse,
            self.banques_centrales,
            self.tresorerie_cpp,
            self.autres_ets_credit,
            self.a_terme,
            self.credits_campagne,
            self.credits_ordinaire,
            self.credits_campagne_acc,
            self.credits_ordinaire_acc,
            self.creances_ordinaires,
            self.affacturage,
            self.titres_placement,
            self.immobilisation_fin,
            self.operation_credit_bail,
            self.immobilisation_incorporelle,
            self.immobilisation_corporelle,
            self.actionnaire_ou_associe,
            self.autres_actifs,
            self.comptes_commande_divers,
        ]

        # La syntaxe (field or 0) convertit les None en 0 avant la somme
        total = sum(field or 0 for field in fields_to_sum)
        return total 

    #  Liste des methodes utiles pour ce model

    #  pret_interbancaire
    #  a_vue
    #  creance_sur_la_clientele
    #  porteuille_papier_commercial
    #  autres_concours_clients
    #  total_assets


# Passifs
class Liabilities(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    type_bilan = models.CharField(
        max_length=20,
        choices=TYPE_BILAN_CHOICES,
        default="annuel",
        verbose_name=_("Type de bilan"),
        help_text=_("Précise s’il s’agit d’un bilan annuel ou semestriel."),
    )
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    semestre = models.PositiveSmallIntegerField(
        choices=SEMESTRE_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Semestre"),
        help_text=_("Laisser vide si le bilan est annuel."),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )

    # Interbank debt
    tresorerie_ccp = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("-Trésorerie, CCP"),
    )
    autres_etablissement_credit = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("-Autres établissements de crédit"),
    )
    ## At term
    a_terme = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("A Terme"),
    )
    # Debts Owed To Customers
    comptes_epargne_court_terme = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Comptes d'épargne à court terme"),
    )
    comptes_epargne_terme = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Comptes d'épargne à terme"),
    )
    bons_caisse = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Bons de caisse"),
    )
    autres_dette_a_vue = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres dettes à vue"),
    )
    autres_dette_a_terme = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres dettes à terme"),
    )

    titres_creance_autres_dettes = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("TITRES DE CRÉANCE AUTRES DETTES"),
    )
    compte_dordre_divers = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("COMPTES D'ORDRE ET DIVERS"),
    )
    provision_pour_risque_charge = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("PROVISIONS POUR RISQUES ET CHARGES"),
    )
    provision_reglementee = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("PROVISIONS RÉGLEMENTÉES"),
    )
    emprunt_subordonne_tire_emis = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("EMPRUNTS SUBORDONNÉS ET TITRES ÉMIS"),
    )
    subventions_investissement = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("SUBVENTIONS D'INVESTISSEMENT"),
    )
    fonds_affecte = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("FONDS AFFECTÉS"),
    )
    fonds_pour_risque_bancaire_generaux = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("FONDS POUR RISQUES BANCAIRES GÉNÉRAUX"),
    )
    capital_ou_dotation = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("CAPITAL OU DOTATIONS"),
    )
    primes_liees_reserve_capital = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("PRIMES LIÉES AUX RÉSERVES DE CAPITAL"),
    )
    ecarts_reevaluation = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("ÉCARTS DE RÉÉVALUATION"),
    )
    benefices_non_distribue = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("BÉNÉFICES NON DISTRIBUÉS (+/-)"),
    )
    resultat_net_exercie = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("RÉSULTAT NET DE L'EXERCICE (+/-)"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="liabilities_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    def __str__(self):
        libelle = f"{_('Passif bilan bancaire')} : {self.id}. {self.acheteur}"
        if self.annee:
            libelle += f" ({self.annee})"
        if self.semestre:
            libelle += f" - {self.get_semestre_display()}"
        return libelle

    class Meta:
        verbose_name = _("Passif bilan bancaire")
        verbose_name_plural = _("Passifs bilans bancaires")

    # ---------------------------------------------------
    #  Liste des methodes utiles pour ce model
    # ---------------------------------------------------

    @property
    def a_vue(self):
        """Calcule la somme des dettes interbancaires à vue."""
        return (self.tresorerie_ccp or 0) + (self.autres_etablissement_credit or 0)

    @property
    def dette_interbancaire(self):
        """Calcule le total des dettes interbancaires (à vue + à terme)."""
        return self.a_vue + (self.a_terme or 0)

    @property
    def dette_envers_clientelle(self):
        """Calcule le total des dettes envers la clientèle."""
        fields_to_sum = [
            self.comptes_epargne_court_terme,
            self.comptes_epargne_terme,
            self.bons_caisse,
            self.autres_dette_a_vue,
            self.autres_dette_a_terme,
        ]
        return sum(field or 0 for field in fields_to_sum)

    @property
    def total_liabilities(self):
        """
        Calcule et retourne la somme de tous les champs financiers du passif.
        Traite les valeurs None comme 0 pour éviter les erreurs de calcul.
        """
        fields_to_sum = [
            self.tresorerie_ccp,
            self.autres_etablissement_credit,
            self.a_terme,
            self.comptes_epargne_court_terme,
            self.comptes_epargne_terme,
            self.bons_caisse,
            self.autres_dette_a_vue,
            self.autres_dette_a_terme,
            self.titres_creance_autres_dettes,
            self.compte_dordre_divers,
            self.provision_pour_risque_charge,
            self.provision_reglementee,
            self.emprunt_subordonne_tire_emis,
            self.subventions_investissement,
            self.fonds_affecte,
            self.fonds_pour_risque_bancaire_generaux,
            self.capital_ou_dotation,
            self.primes_liees_reserve_capital,
            self.ecarts_reevaluation,
            self.benefices_non_distribue,
            self.resultat_net_exercie,
        ]

        # La syntaxe (field or 0) convertit les None en 0 avant la somme
        total = sum(field or 0 for field in fields_to_sum)
        return total


# Depenses
class Expenses(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    type_bilan = models.CharField(
        max_length=20,
        choices=TYPE_BILAN_CHOICES,
        default="annuel",
        verbose_name=_("Type de bilan"),
        help_text=_("Précise s’il s’agit d’un bilan annuel ou semestriel."),
    )
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    semestre = models.PositiveSmallIntegerField(
        choices=SEMESTRE_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Semestre"),
        help_text=_("Laisser vide si le bilan est annuel."),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )

    interet_charges_assimilee_dette_interbancaire = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("Intérêts et charges assimilées sur dettes interbancaires"),
    )
    interet_charge_assimilee_dette_clientele = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        help_text="",
        verbose_name=_("Intérêts et charges assimilées sur dettes envers la clientèle"),
    )
    interet_charge_assimilee_titre_creance = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("Intérêts et charges assimilées sur titres de créances"),
    )
    chargesc_compte_bloque_dactionnaire_emprunt_sub = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "Charges sur comptes bloqués d'actionnaires emprunts sur titres subordonnés"
        ),
    )
    autres_interets_charges_assimilee = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("Autres Intérêts et charges assimilées"),
    )
    charges_sur_op_credit_bail_assimile = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("CHARGES SUR OPÉRATIONS DE CRÉDIT-BAIL ET ASSIMILÉES"),
    )
    commissions = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("COMMISSIONS"),
    )

    charges_sur_titre_placement = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Charges sur titres de placement"),
        verbose_name=_("Charges sur titres de placement"),
    )
    charges_sur_operation_change = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Charges sur opérations de change"),
        verbose_name=_("Charges sur opérations de change"),
    )
    charges_sur_operation_hors_bilan = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("Charges sur opérations hors bilan"),
    )
    frais_divers_exploitation_bancaire = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("FRAIS DIVERS D'EXPLOITATION BANCAIRE"),
    )
    achat_marchandises = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("ACHAT DE MARCHANDISES"),
    )
    stocks_vendus = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("STOCKS VENDUS"),
    )
    variations_stocks_marchanides = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("VARIATIONS DES STOCKS DE MARCHANDISES"),
    )
    frais_personnel = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Frais de personnel"),
    )

    autres_frais_generaux = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres frais généraux"),
    )
    dotations_amortissement_provision_immobilisation = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "DOTATIONS AUX AMORTISSEMENTS ET PROVISIONS SUR IMMOBILISATIONS"
        ),
    )
    solde_perte_creance_hors_bilan = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("SOLDE DES PERTES SUR CRÉANCES ET HORS BILAN"),
    )
    excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "EXCÉDENT DES DOTATIONS SUR LES REPRISES DU FONDS POUR RISQUES BANCAIRES GÉNÉRAUX"
        ),
    )
    charges_exceptionnelle = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("LES CHARGES EXCEPTIONNELLES"),
    )
    pertes_exercice_anterieurs = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("PERTES SUR EXERCICES ANTÉRIEURS"),
    )
    impot_sur_revenu = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("IMPÔTS SUR LE REVENU"),
    )
    total_charges = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("TOTAL DES CHARGES"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="expenses_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    # --- MÉTHODE __str__ AMÉLIORÉE ---
    def __str__(self):
        """
        Fournit une représentation textuelle claire de l'objet.
        """
        libelle = f"{_('Dépense bilan bancaire')} : {self.id}. {self.acheteur or 'N/A'}"
        if self.annee:
            libelle += f" ({self.annee.annee})"
        if self.semestre:
            libelle += f" - {self.get_semestre_display()}"
        return libelle

    class Meta:
        verbose_name = _("Dépense bilan bancaire")
        verbose_name_plural = _("Dépenses bilans bancaires")

    # ----------------------------------------
    #  Liste des méthodes utiles pour ce modèle
    # ----------------------------------------

    @property
    def interet_charges_assimilee(self):
        """Calcule le total des intérêts et charges assimilées."""
        fields_to_sum = [
            self.interet_charges_assimilee_dette_interbancaire,
            self.interet_charge_assimilee_dette_clientele,
            self.interet_charge_assimilee_titre_creance,
            self.chargesc_compte_bloque_dactionnaire_emprunt_sub,
            self.autres_interets_charges_assimilee,
        ]
        return sum(field or 0 for field in fields_to_sum)

    @property
    def charge_sur_operation_financiere(self):
        """Calcule le total des charges sur opérations financières."""
        fields_to_sum = [
            self.charges_sur_op_credit_bail_assimile,
            self.commissions,
            self.charges_sur_titre_placement,
            self.charges_sur_operation_change,
            self.charges_sur_operation_hors_bilan,
        ]
        return sum(field or 0 for field in fields_to_sum)

    @property
    def prestation(self):
        """Calcule le coût des marchandises vendues."""
        return (
            (self.achat_marchandises or 0)
            + (self.variations_stocks_marchanides or 0)
            - (self.stocks_vendus or 0)
        )

    @property
    def frais_generaux_dexploitation(self):
        """Calcule le total des frais généraux d'exploitation."""
        fields_to_sum = [
            self.frais_divers_exploitation_bancaire,
            self.frais_personnel,
            self.autres_frais_generaux,
        ]
        return sum(field or 0 for field in fields_to_sum)

    @property
    def total_des_charges(self):
        """
        Calcule et retourne la somme de TOUTES les charges de l'instance.
        Cette méthode est la source de vérité pour le total.
        """
        fields_to_sum = [
            self.interet_charges_assimilee,  # Utilise la propriété déjà calculée
            self.charge_sur_operation_financiere,  # Utilise la propriété déjà calculée
            self.prestation,  # Utilise la propriété déjà calculée
            self.frais_generaux_dexploitation,  # Utilise la propriété déjà calculée
            self.dotations_amortissement_provision_immobilisation,
            self.solde_perte_creance_hors_bilan,
            self.excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux,
            self.charges_exceptionnelle,
            self.pertes_exercice_anterieurs,
            self.impot_sur_revenu,
        ]
        return sum(field or 0 for field in fields_to_sum)


# Produits
class Products(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    type_bilan = models.CharField(
        max_length=20,
        choices=TYPE_BILAN_CHOICES,
        default="annuel",
        verbose_name=_("Type de bilan"),
        help_text=_("Précise s’il s’agit d’un bilan annuel ou semestriel."),
    )
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    semestre = models.PositiveSmallIntegerField(
        choices=SEMESTRE_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Semestre"),
        help_text=_("Laisser vide si le bilan est annuel."),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )

    interets_produit_assimile_sur_pret_avance_interbancaire = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "Intérêts et produits assimilés sur prêts et avances interbancaires"
        ),
    )
    ineterets_produit_assimile_pret_avance_clientele = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "Intérêts et produits assimilés sur prêts et avances à la clientèle"
        ),
    )
    interet_produit_sur_titre_dinvestissement = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Intérêts et produits assimilés sur titres d'investissement"),
    )
    revenu_gains_titre_pret_titre_subordonne = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "Revenus et gains sur titres de prêts et titres subordonnés émis"
        ),
    )

    autres_interets_produits_assimiles = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres intérêts et produits assimilés"),
    )
    produits_leansing_operation_connexes = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("PRODUITS DE LEASING ET OPÉRATIONS CONNEXES "),
    )
    commissions = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("COMMISSIONS"),
    )

    revenus_titre_negociable = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Revenus de titres négociables"),
    )
    dividendes_produits_assimiles = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dividendes et produits assimilés"),
    )
    revenus_operation_de_change = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Revenus d'opérations de change"),
    )
    produits_opeations_hors_bilan = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("Produits des opérations hors bilan"),
    )

    produits_bancaire_divers = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("PRODUITS BANCAIRES DIVERS"),
    )
    marges_vente = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("MARGES DE VENTE"),
    )
    ventes_marchandises = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("VENTES DE MARCHANDISES"),
    )
    variation_stocks_marchandises = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("VARIATION DES STOCKS DE MARCHANDISES"),
    )
    produit_dexploitation_generale = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("PRODUITS D'EXPLOITATION GÉNÉRALE"),
    )

    reprise_damortissement_provisions_sur_immobilisation = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "REPRISES D'AMORTISSEMENTS ET DE PROVISIONS SUR IMMOBILISATIONS"
        ),
    )
    solde_resultat_correction_valeur_sur_creance_hors_bilan = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "SOLDE DU RÉSULTAT DES CORRECTIONS DE VALEUR SUR CRÉANCES ET HORS BILAN"
        ),
    )
    excedent_reprise_fonds_pour_risque_bancaire_generaux = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "EXCÉDENT DES REPRISES DU FONDS POUR RISQUES BANCAIRES GÉNÉRAUX"
        ),
    )

    produits_exceptionnels = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("PRODUITS EXCEPTIONNELS"),
    )
    benefice_sur_exercice_anterieur = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("BÉNÉFICES SUR EXERCICES ANTÉRIEURS"),
    )
    perte = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("PERTES"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="product_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    # --- MÉTHODE __str__ AMÉLIORÉE ---
    def __str__(self):
        libelle = f"{_('Produit bilan bancaire')} : {self.id}. {self.acheteur or 'N/A'}"
        if self.annee:
            libelle += f" ({self.annee.annee})"
        if self.semestre:
            libelle += f" - {self.get_semestre_display()}"
        return libelle

    class Meta:
        verbose_name = _("Produit bilan bancaire")
        verbose_name_plural = _("Produits bilans bancaires")

    # ----------------------------------------
    #  Liste des méthodes utiles pour ce modèle
    # ----------------------------------------

    @property
    def interet_produit_assimile(self):
        """Calcule le total des intérêts et produits assimilés."""
        fields_to_sum = [
            self.interets_produit_assimile_sur_pret_avance_interbancaire,
            self.ineterets_produit_assimile_pret_avance_clientele,
            self.interet_produit_sur_titre_dinvestissement,
            self.revenu_gains_titre_pret_titre_subordonne,
            self.autres_interets_produits_assimiles,
        ]
        return sum(field or 0 for field in fields_to_sum)

    @property
    def revenu_d_operation_financiere(self):
        """Calcule le total des revenus sur opérations financières (corrigé)."""
        fields_to_sum = [
            self.produits_leansing_operation_connexes,
            self.commissions,
            self.revenus_titre_negociable,
            self.dividendes_produits_assimiles,
            self.revenus_operation_de_change,
            self.produits_opeations_hors_bilan,
        ]
        return sum(field or 0 for field in fields_to_sum)

    # NOUVELLE propriété pour plus de clarté
    @property
    def autres_produits_exploitation(self):
        """Calcule les autres produits liés à l'exploitation."""
        fields_to_sum = [
            self.produits_bancaire_divers,
            self.marges_vente,
            self.ventes_marchandises,
            self.variation_stocks_marchandises,
            self.produit_dexploitation_generale,
        ]
        return sum(field or 0 for field in fields_to_sum)

    @property
    def total_produit(self):
        """Calcule et retourne la somme de TOUS les produits de l'instance."""
        # On additionne les sous-totaux et les champs restants
        # La perte est soustraite
        total = (
            self.interet_produit_assimile
            + self.revenu_d_operation_financiere
            + self.autres_produits_exploitation
            + (self.reprise_damortissement_provisions_sur_immobilisation or 0)
            + (self.solde_resultat_correction_valeur_sur_creance_hors_bilan or 0)
            + (self.excedent_reprise_fonds_pour_risque_bancaire_generaux or 0)
            + (self.produits_exceptionnels or 0)
            + (self.benefice_sur_exercice_anterieur or 0)
            - (self.perte or 0)
        )
        return total


# Hors bilan
class OffBalanceSheet(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    # --- Champs d'identification (inchangés) ---
    type_bilan = models.CharField(
        max_length=20,
        choices=TYPE_BILAN_CHOICES,
        default="annuel",
        verbose_name=_("Type de bilan"),
        help_text=_("Précise s’il s’agit d’un bilan annuel ou semestriel."),
    )
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    semestre = models.PositiveSmallIntegerField(
        choices=SEMESTRE_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Semestre"),
        help_text=_("Laisser vide si le bilan est annuel."),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )

    # --- NOUVEAUX CHAMPS DE L'ANCIENNE TABLE ---
    # Ces champs sont rendus null et blank pour ne pas perturber les données existantes
    en_faveur_des_ets_credit = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Engagements en faveur des établissements de crédit"),
    )
    en_faveur_clientele = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Engagements en faveur de la clientèle"),
    )
    pour_compte_ets_credit = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Engagements pour le compte des établissements de crédit"),
    )
    pour_compte_clientele = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Engagements pour le compte de la clientèle"),
    )
    engagement_sur_titre = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Anciens engagements sur titres"),
    )
    recu_ets_credit = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Anciens engagements reçus d'établissements de crédit"),
    )
    recu_ets_credit2 = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Anciens engagements reçus d'établissements de crédit (2)"),
    )
    recu_clientele = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Anciens engagements reçus de la clientèle"),
    )
    engagement_sur_titre2 = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Anciens engagements sur titres (2)"),
    )

    # --- ENGAGEMENTS DONNÉS ---
    # Catégorie : Engagements de financement donnés
    engagement_financement_donne_ets_credit = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_(
            "Engagements de financement donnés en faveur des établissements de crédit"
        ),
    )
    engagement_financement_donne_clientele = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Engagements de financement donnés en faveur de la clientèle"),
    )

    # Catégorie : Engagements de garantie donnés
    engagement_garantie_donne_ets_credit = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_(
            "Engagements de garantie donnés pour le compte des établissements de crédit"
        ),
    )
    engagement_garantie_donne_clientele = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Engagements de garantie donnés pour le compte de la clientèle"),
    )

    # Catégorie : Engagements sur titres donnés
    engagement_sur_titres_donnes = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Engagements sur titres donnés"),
    )

    # --- ENGAGEMENTS REÇUS ---
    # Catégorie : Engagements de financement reçus
    engagement_financement_recu_ets_credit = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Engagements de financement reçus d'établissements de crédit"),
    )
    engagement_financement_recu_clientele = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Engagements de financement reçus de la clientèle"),
    )

    # Catégorie : Engagements de garantie reçus
    engagement_garantie_recu_ets_credit = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Engagements de garantie reçus d'établissements de crédit"),
    )

    # Catégorie : Engagements sur titres reçus
    engagement_sur_titres_recus = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Engagements sur titres reçus"),
    )

    # --- Champs de suivi (inchangés) ---
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="offbalance_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )
    
    # --- Champs de l'ancienne table à ne pas utiliser ---
    deleted = models.DateTimeField(null=True, blank=True)
    deleted_by_cascade = models.BooleanField(default=False)

    history = HistoricalRecords()


    # --- MÉTHODE __str__ AMÉLIORÉE ---
    def __str__(self):
        """
        Fournit une représentation textuelle claire et sécurisée de l'instance,
        inspirée du modèle Products.
        """
        libelle = f"{_('Hors bilan bancaire')} : {self.id}. {self.acheteur or 'N/A'}"
        if self.annee:
            libelle += f" ({self.annee.annee})"
        if self.semestre:
            libelle += f" - {self.get_semestre_display()}"
        return libelle

    class Meta:
        verbose_name = _("Hors Bilan bancaire")
        verbose_name_plural = _("Hors Bilans bancaires")

    # ----------------------------------------
    #   Liste des méthodes utiles pour ce modèle
    # ----------------------------------------

    # --- SOUS-TOTAUX POUR LES ENGAGEMENTS DONNÉS ---

    @property
    def total_engagement_financement_donne(self):
        """Calcule le total des engagements de financement DONNÉS."""
        fields_to_sum = [
            self.engagement_financement_donne_ets_credit,
            self.engagement_financement_donne_clientele,
            # Ajout des anciens champs
            self.en_faveur_des_ets_credit,
            self.en_faveur_clientele,
        ]
        return sum(field or 0 for field in fields_to_sum)

    @property
    def total_engagement_garantie_donne(self):
        """Calcule le total des engagements de garantie DONNÉS."""
        fields_to_sum = [
            self.engagement_garantie_donne_ets_credit,
            self.engagement_garantie_donne_clientele,
            # Ajout des anciens champs
            self.pour_compte_ets_credit,
            self.pour_compte_clientele,
        ]
        return sum(field or 0 for field in fields_to_sum)

    # --- TOTAL GÉNÉRAL DES ENGAGEMENTS DONNÉS ---

    @property
    def total_engagements_donnes(self):
        """Calcule le total de TOUS les engagements DONNÉS."""
        return (
            self.total_engagement_financement_donne
            + self.total_engagement_garantie_donne
            + (self.engagement_sur_titres_donnes or 0)
            + (self.engagement_sur_titre or 0)  # Ajout de l'ancien champ
        )

    # --- SOUS-TOTAUX POUR LES ENGAGEMENTS REÇUS ---

    @property
    def total_engagement_financement_recu(self):
        """Calcule le total des engagements de financement REÇUS."""
        fields_to_sum = [
            self.engagement_financement_recu_ets_credit,
            self.engagement_financement_recu_clientele,
            # Ajout des anciens champs
            self.recu_ets_credit,
            self.recu_clientele,
        ]
        return sum(field or 0 for field in fields_to_sum)

    # --- TOTAL GÉNÉRAL DES ENGAGEMENTS REÇUS ---

    @property
    def total_engagements_recus(self):
        """Calcule le total de TOUS les engagements REÇUS."""
        return (
            self.total_engagement_financement_recu
            + (self.engagement_garantie_recu_ets_credit or 0)
            + (self.engagement_sur_titres_recus or 0)
            + (self.recu_ets_credit2 or 0)  # Ajout de l'ancien champ
            + (self.engagement_sur_titre2 or 0)  # Ajout de l'ancien champ
        )


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



# Debut Modules Bilan SysCohada

class ActifS(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )

    # Immobilisation incorporelles
    frais_developpement_prospection = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Frais de développement et prospection"),
    )
    brevets_licences_logiciels = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Brevets, licences et logiciels"),
    )
    droits_propriete_commerciale_baux = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Droits de propriété commerciale et baux"),
    )
    autres_immo_incorporelles = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres immobilisations incorporelles"),
    )

    # Immobilisations corporelles
    terrains = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Terrains"),
    )
    dons_investissements_net = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dons et investissements nets"),
    )
    batiments = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Bâtiments"),
    )
    agencements_amenagements_installations = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Agencements, aménagements et installations"),
    )
    materiel_mobilier_actif_biologiques = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Matériel, mobilier et actifs biologiques"),
    )
    materiel_transport = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Matériel de transport"),
    )

    # Avances et acomptes sur immobilisations
    avances_acompte_immobilisations = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Avances et acomptes sur immobilisations"),
    )
    # Immobilisations financieres
    titres_participation = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Titres de participation"),
    )
    autres_immobilisations_financieres = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres immobilisations financières"),
    )

    # Actif circulant de HAO
    actif_circulant_hao = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Actif circulant HAO"),
    )

    # Stock et En-cours (calcule)
    stock_encours = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Stock et en-cours"),
    )

    # Creances et emplois similaires (calcule)
    fournisseurs_avances_versee = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Fournisseurs, avances versées"),
    )
    clients = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Clients"),
    )
    autres_creances = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres créances"),
    )

    # Total de l'actif circulant
    valeurs_mobilieres_placement = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Valeurs mobilières de placement"),
    )
    disponibilites = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Disponibilités"),
    )
    banque_cheque_postal_caisse_assimiles = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Banque, chèque postal, caisse et assimilés"),
    )

    # Total de la trésorerie et des équivalents de trésorerie
    ecart_conversion_actif = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Écart de conversion actif"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="actifs_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            _("Actif bilan SYSCOHADA : ")
            + str(self.id)
            + ". "
            + str(self.acheteur)
            + " ("
            + str(self.annee)
            + ")"
        )

    class Meta:
        verbose_name = _("Actif bilan SYSCOHADA")
        verbose_name_plural = _("Actifs bilans SYSCOHADA")
    
    @property
    def immobilisations_incorporelles(self):
        """Calcule le total des immobilisations incorporelles."""
        fields = [self.frais_developpement_prospection, self.brevets_licences_logiciels, self.droits_propriete_commerciale_baux, self.autres_immo_incorporelles]
        return sum(f or 0 for f in fields)
    
    @property
    def immobilisations_corporelles(self):
        """Calcule le total des immobilisations corporelles."""
        fields = [self.terrains, self.dons_investissements_net, self.batiments, self.agencements_amenagements_installations, self.materiel_mobilier_actif_biologiques, self.materiel_transport]
        return sum(f or 0 for f in fields)
    
    @property
    def immobilisations_financieres(self):
        """Calcule le total des immobilisations financières."""
        fields = [self.titres_participation, self.autres_immobilisations_financieres]
        return sum(f or 0 for f in fields)
        
    @property
    def total_actif_immobilise(self):
        """Total des immobilisations nettes (incorporelles + corporelles + financières)."""
        return self.immobilisations_incorporelles + self.immobilisations_corporelles + self.immobilisations_financieres
    
    @property
    def creances_emplois_similaires(self):
        """Calcule le total des créances et emplois assimilés."""
        fields = [self.fournisseurs_avances_versee, self.clients, self.autres_creances]
        return sum(f or 0 for f in fields)
    
    @property
    def total_tresorerie_equivalents(self):
        """Total de la trésorerie et des équivalents de trésorerie."""
        fields = [self.valeurs_mobilieres_placement, self.disponibilites, self.banque_cheque_postal_caisse_assimiles]
        return sum(f or 0 for f in fields)
        
    @property
    def total_actif_circulant(self):
        """Total de l'actif circulant (hors trésorerie)."""
        fields = [self.stock_encours, self.creances_emplois_similaires, self.actif_circulant_hao]
        return sum(f or 0 for f in fields)
        
    @property
    def total_actif(self):
        """Calcule le total général de l'actif."""
        return self.total_actif_immobilise + self.total_actif_circulant + self.total_tresorerie_equivalents + (self.ecart_conversion_actif or 0)


class PassifS(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )

    capital = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Capital"),
    )
    capital_non_appele_apporteurs = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Capital non appelé des apporteurs"),
    )
    primes_liees_capital_social = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Primes liées au capital social"),
    )
    ecart_reevaluation = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Écart de réévaluation"),
    )
    reserves_indisponibles = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Réserves indisponibles"),
    )
    reserves_libres = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Réserves libres"),
    )
    report_nouveau = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Report à nouveau (+ ou -)"),
    )
    resultat_net_exercice = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Résultat net de l'exercice (bénéfice + ou perte -)"),
    )
    subventions_investissements = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Subventions d'investissement"),
    )
    provisions_reglees = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Provisions réglées"),
    )

    emprunts_dettes_financieres_diverse = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Emprunts et dettes financières diverses"),
    )
    dettes_location_vente = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dettes de location-vente"),
    )
    provisions_risques_charges = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Provisions pour risques et charges"),
    )

    passif_circulant_hao = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Passif circulant HAO"),
    )
    clients_avances_recues = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Clients, avances reçues"),
    )
    fournisseurs_exploitation = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Fournisseurs d'exploitation"),
    )
    dettes_fiscales_sociales = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Dettes fiscales et sociales"),
    )
    autres_dettes = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Autres dettes"),
    )
    provisions_risques_court_terme = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Provisions pour risques à court terme"),
    )

    banques_credit_escompte = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Banques, crédits d'escompte"),
    )
    banques_etablissements_financiers_credit_caisse = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Banques, établissements financiers et crédits de caisse"),
    )

    ecart_conversion_passif = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Écarts de conversion - Passif"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="passifs_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            _("Passif bilan SYSCOHADA : ")
            + str(self.id)
            + ". "
            + str(self.acheteur)
            + " ("
            + str(self.annee)
            + ")"
        )

    class Meta:
        verbose_name = _("Passif bilan SYSCOHADA")
        verbose_name_plural = _("Passifs bilans SYSCOHADA")
        
    @property
    def total_capitaux_propres_ressources_similaires(self):
        """Calcule le total des capitaux propres et ressources assimilées."""
        fields = [self.capital, self.primes_liees_capital_social, self.ecart_reevaluation, self.reserves_indisponibles, self.reserves_libres, self.report_nouveau, self.resultat_net_exercice, self.subventions_investissements, self.provisions_reglees]
        return sum(f or 0 for f in fields) - (self.capital_non_appele_apporteurs or 0)
    
    @property
    def total_dettes_financieres_ressources_similaires(self):
        """Calcule le total des dettes financières et ressources assimilées."""
        fields = [self.emprunts_dettes_financieres_diverse, self.dettes_location_vente, self.provisions_risques_charges]
        return sum(f or 0 for f in fields)

    @property
    def total_ressources_stables(self):
        """Calcule le total des ressources stables."""
        return self.total_capitaux_propres_ressources_similaires + self.total_dettes_financieres_ressources_similaires
    
    @property
    def total_passifs_courants(self):
        """Calcule le total des passifs courants."""
        fields = [self.passif_circulant_hao, self.clients_avances_recues, self.fournisseurs_exploitation, self.dettes_fiscales_sociales, self.autres_dettes, self.provisions_risques_court_terme]
        return sum(f or 0 for f in fields)
        
    @property
    def total_tresorerie_equivalents(self):
        """Calcule le total de la trésorerie et des équivalents de trésorerie."""
        fields = [self.banques_credit_escompte, self.banques_etablissements_financiers_credit_caisse]
        return sum(f or 0 for f in fields)
        
    @property
    def total_passifs(self):
        """Calcule le total général du passif."""
        return self.total_ressources_stables + self.total_passifs_courants + self.total_tresorerie_equivalents + (self.ecart_conversion_passif or 0)


class ResultatS(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année Civile"),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )

    ventes_marchandises_a = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Ventes de marchandises A (+)",
    )
    achats_marchandises = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Achats de marchandises (-)",
    )
    variation_stock_marchandises = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Variation des stocks de marchandises (-/+)",
    )

    ventes_produits_manufactures = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Ventes de produits manufacturés B (+)",
    )
    travaux_services_vendus_c = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Travaux, services vendus C (+)",
    )
    produits_accessoires_d = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Produits accessoires D (+)",
    )

    production_stockee = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Production stockée (ou déstockage) (-/+)",
    )
    production_immobilisee = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Production Immobilisée (+)",
    )
    subvention_exploitation = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Subvention d'exploitation (+)",
    )
    autres_produits = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Autres produits (+)",
    )
    transfert_charges_exploitation = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Transfert de charges d'exploitation (+)",
    )
    achats_matieres_premieres_fournitures_connexes = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Achats de matières premières et fournitures connexes (-)",
    )
    variation_stock_matieres_premieres_fournitures_connexes = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Variation des stocks de matières premières et fournitures connexes (-/+)",
    )
    autres_achats = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Autres achats (-)",
    )
    variation_stock_autres_fournitures = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Variation des stocks d'autres fournitures (-/+)",
    )
    transport = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Transport (-)",
    )
    services_exterieurs = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Services extérieurs (-)",
    )
    impots_taxes = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Impots et taxes (-)",
    )
    autres_depenses = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Autres dépenses (-)",
    )
    frais_personnel = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Frais de personnel (-)",
    )
    reprise_depreciations_amortissements_provision_pertes_valeurs_p = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Reprises de dépréciations, amortissements, provisions et pertes de valeur (+)",
    )
    reprise_depreciations_amortissements_provision_pertes_valeurs_m = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Reprises de dépréciations, amortissements, provisions et pertes de valeur (-)",
    )
    produits_financiers_assimiles = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Produits financiers et assimilés (+)",
    )
    reprise_provision_perte_valeur = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Reprises sur provisions et pertes de valeur (+)",
    )
    transfert_charges_financieres = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Transfert de charges financières (+)",
    )
    charges_financieres_assimilees = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Charges financières et assimilées (-)",
    )
    dotations_provisions_depreciations_financieres = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Dotations aux provisions et dépréciations financières (-)",
    )
    produits_cession_immobilisations = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Produits des cessions d'immobilisations (+)",
    )
    autres_produits_hao = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Autres produits HAO (+)",
    )
    valeur_comptable_cessions_actifs_immobilises = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valeur comptable des cessions d'actifs immobilisés (-)",
    )
    autres_charges_hao = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Autres charges HAO (-)",
    )
    participation_travailleurs = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Participation des travailleurs (-)",
    )
    charge_impot_revenu = models.DecimalField(
        max_digits=100,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Charge d'impôt sur le revenu (-)",
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="resultats_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            _("Résultat bilan SYSCOHADA : ")
            + str(self.id)
            + ". "
            + str(self.acheteur)
            + " ("
            + str(self.annee)
            + ")"
        )

    class Meta:
        verbose_name = _("Résultat bilan SYSCOHADA")
        verbose_name_plural = _("Résultats bilans SYSCOHADA")

    @property
    def marge_commerciale(self):
        """Calcule la marge commerciale."""
        return (self.ventes_marchandises_a or 0) - (self.achats_marchandises or 0) + (self.variation_stock_marchandises or 0)
    
    @property
    def chiffre_affaires(self):
        """Calcule le chiffre d'affaires."""
        return (self.ventes_marchandises_a or 0) + (self.ventes_produits_manufactures or 0) + (self.travaux_services_vendus_c or 0) + (self.produits_accessoires_d or 0)

    @property
    def valeur_ajoutee(self):
        """Calcule la valeur ajoutée."""
        production = (self.chiffre_affaires or 0) + (self.production_stockee or 0) + (self.production_immobilisee or 0)
        consommation_intermediaire = (self.achats_marchandises or 0) + (self.variation_stock_marchandises or 0) + (self.achats_matieres_premieres_fournitures_connexes or 0) + (self.variation_stock_matieres_premieres_fournitures_connexes or 0) + (self.autres_achats or 0) + (self.variation_stock_autres_fournitures or 0) + (self.transport or 0) + (self.services_exterieurs or 0)
        return production - consommation_intermediaire
    
    @property
    def excedent_brute_exploitation(self):
        """Calcule l'excédent brut d'exploitation (EBE)."""
        return (self.valeur_ajoutee or 0) + (self.subvention_exploitation or 0) + (self.autres_produits or 0) + (self.transfert_charges_exploitation or 0) - (self.frais_personnel or 0) - (self.impots_taxes or 0) - (self.autres_depenses or 0)
        
    @property
    def resultat_exploitation(self):
        """Calcule le résultat d'exploitation."""
        return (self.excedent_brute_exploitation or 0) + (self.reprise_depreciations_amortissements_provision_pertes_valeurs_p or 0) - (self.reprise_depreciations_amortissements_provision_pertes_valeurs_m or 0)
    
    @property
    def resultat_financier(self):
        """Calcule le résultat financier."""
        produits_fin = (self.produits_financiers_assimiles or 0) + (self.reprise_provision_perte_valeur or 0) + (self.transfert_charges_financieres or 0)
        charges_fin = (self.charges_financieres_assimilees or 0) + (self.dotations_provisions_depreciations_financieres or 0)
        return produits_fin - charges_fin
        
    @property
    def resultat_activites_ordinaires_xe(self):
        """Calcule le résultat des activités ordinaires (hors HAO)."""
        return (self.resultat_exploitation or 0) + (self.resultat_financier or 0)
        
    @property
    def resultat_activites_ordinaires_tn(self):
        """Calcule le résultat des activités ordinaires (avec HAO)."""
        produits_hao = (self.produits_cession_immobilisations or 0) + (self.autres_produits_hao or 0)
        charges_hao = (self.valeur_comptable_cessions_actifs_immobilises or 0) + (self.autres_charges_hao or 0)
        return (self.resultat_activites_ordinaires_xe or 0) + produits_hao - charges_hao

    @property
    def resultat_net(self):
        """Calcule le résultat net de l'exercice."""
        return (self.resultat_activites_ordinaires_tn or 0) - (self.participation_travailleurs or 0) - (self.charge_impot_revenu or 0)


# Ratios Bilan SYSCOHADA

# Création d'une classe dédiée pour les ratios
from decimal import Decimal

class RatiosSyscohada:
    def __init__(self, actif: ActifS, passif: PassifS, resultat: ResultatS):
        self.actif = actif
        self.passif = passif
        self.resultat = resultat
        
    def _get_val(self, model, prop):
        return getattr(model, prop, Decimal('0')) or Decimal('0')

    @property
    def fonds_de_roulement(self):
        """ Fonds de Roulement Net Global (FRNG) = Ressources stables - Emplois stables """
        ressources_stables = self._get_val(self.passif, 'total_ressources_stables')
        emplois_stables = self._get_val(self.actif, 'total_actif_immobilise')
        return ressources_stables - emplois_stables if self.passif and self.actif else None
        
    @property
    def besoin_fonds_de_roulement(self):
        """ Besoin en Fonds de Roulement (BFR) = Actif circulant - Passif circulant """
        actif_circulant = self._get_val(self.actif, 'total_actif_circulant')
        passif_courant = self._get_val(self.passif, 'total_passifs_courants')
        return actif_circulant - passif_courant if self.actif and self.passif else None
        
    @property
    def position_net_de_tresorerie(self):
        """ Position de Trésorerie Nette = Trésorerie nette - Dettes bancaires courantes """
        tresorerie_nette = self._get_val(self.actif, 'total_tresorerie_equivalents')
        dettes_bancaires = self._get_val(self.passif, 'total_tresorerie_equivalents')
        return tresorerie_nette - dettes_bancaires if self.actif and self.passif else None

    @property
    def cafsys(self):
        """ Capacité d'Autofinancement (CAF) = Résultat net + DAP - Reprises et transferts """
        # Approximation en utilisant les champs disponibles
        dap = self._get_val(self.resultat, 'reprise_depreciations_amortissements_provision_pertes_valeurs_m')
        reprises = self._get_val(self.resultat, 'reprise_depreciations_amortissements_provision_pertes_valeurs_p')
        transferts = self._get_val(self.resultat, 'transfert_charges_exploitation')
        return (self.resultat.resultat_net or 0) + dap - (reprises + transferts) if self.resultat else None

    @property
    def autonomie_financiere(self):
        """ Autonomie financière = Capitaux propres / Dettes totales """
        dettes_totales = self._get_val(self.passif, 'total_dettes_financieres_ressources_similaires') + self._get_val(self.passif, 'total_passifs_courants')
        capitaux_propres = self._get_val(self.passif, 'total_capitaux_propres_ressources_similaires')
        if dettes_totales != 0:
            return capitaux_propres / dettes_totales
        return None

    @property
    def liquidite_general(self):
        """ Liquidité générale = Actif circulant / Passif circulant """
        actif_circulant = self._get_val(self.actif, 'total_actif_circulant') + self._get_val(self.actif, 'total_tresorerie_equivalents')
        passif_circulant = self._get_val(self.passif, 'total_passifs_courants') + self._get_val(self.passif, 'total_tresorerie_equivalents')
        if passif_circulant != 0:
            return actif_circulant / passif_circulant
        return None
        
    @property
    def rotation_stock(self):
        """ Rotation des stocks (en jours) = (Stocks / Coût des ventes) * 360 """
        if self.resultat.chiffre_affaires and self.resultat.chiffre_affaires != 0:
            stocks = self._get_val(self.actif, 'stock_encours')
            # Le coût des ventes peut être une approximation
            cout_des_ventes = (self._get_val(self.resultat, 'achats_marchandises') + self._get_val(self.resultat, 'achats_matieres_premieres_fournitures_connexes') + self._get_val(self.resultat, 'autres_achats'))
            if cout_des_ventes != 0:
                 return (stocks / cout_des_ventes) * 360
        return None
        
    # COMPLÉTION DES RATIOS MANQUANTS
    
    @property
    def benefice_net(self):
        return self.roe
        
    @property
    def benefice_net_chiffre_affaire(self):
        """ Marge nette = (Résultat net / Chiffre d'affaires) * 100 """
        try:
            if (self.resultat and 
                self.resultat.chiffre_affaires and 
                float(self.resultat.chiffre_affaires) != 0 and
                self.resultat.resultat_net is not None):
                return (float(self.resultat.resultat_net) / float(self.resultat.chiffre_affaires)) * 100
        except (TypeError, ZeroDivisionError, ValueError):
            pass
        return 0.0
        
    @property
    def turnover(self):
        """ Turnover = Chiffre d'affaires / Actif total """
        try:
            if (self.actif and 
                self.actif.total_actif and 
                float(self.actif.total_actif) != 0 and
                self.resultat and 
                self.resultat.chiffre_affaires):
                return float(self.resultat.chiffre_affaires) / float(self.actif.total_actif)
        except (TypeError, ZeroDivisionError, ValueError):
            pass
        return 0.0

    @property
    def ebitda_chiffre_affaire(self):
        """ EBITDA / Chiffre d'affaires """
        try:
            if (self.resultat and 
                self.resultat.chiffre_affaires and 
                float(self.resultat.chiffre_affaires) != 0 and
                self.resultat.excedent_brute_exploitation is not None):
                return float(self.resultat.excedent_brute_exploitation) / float(self.resultat.chiffre_affaires)
        except (TypeError, ZeroDivisionError, ValueError):
            pass
        return 0.0
        
    @property
    def liquidite_reduite(self):
        """ Liquidité réduite = (Actif circulant - Stocks) / Passif circulant """
        actif_circulant = self._get_val(self.actif, 'total_actif_circulant')
        stocks = self._get_val(self.actif, 'stock_encours')
        passif_courant = self._get_val(self.passif, 'total_passifs_courants')
        if passif_courant != 0:
            return (actif_circulant - stocks) / passif_courant
        return None
        
    @property
    def liquidite_immediate(self):
        """ Liquidité immédiate = Trésorerie / Passif circulant """
        tresorerie = self._get_val(self.actif, 'total_tresorerie_equivalents')
        passif_courant = self._get_val(self.passif, 'total_passifs_courants')
        if passif_courant != 0:
            return tresorerie / passif_courant
        return None
        
    @property
    def jour_collecte_moyens(self):
        """ Jours de collecte moyens = (Créances clients / Chiffre d'affaires) * 360 """
        if self.resultat and self.resultat.chiffre_affaires and self.resultat.chiffre_affaires != 0:
            creances_clients = self._get_val(self.actif, 'creances_emplois_similaires')
            return (creances_clients / self.resultat.chiffre_affaires) * 360
        return None
        
    @property
    def moyen_paiement(self):
        """ Jours de paiement moyens = (Dettes fournisseurs / Achats) * 360 """
        achats_totaux = (self._get_val(self.resultat, 'achats_marchandises') + 
                        self._get_val(self.resultat, 'achats_matieres_premieres_fournitures_connexes') + 
                        self._get_val(self.resultat, 'autres_achats'))
        if achats_totaux != 0:
            dettes_fournisseurs = self._get_val(self.passif, 'fournisseurs_exploitation')
            return (dettes_fournisseurs / achats_totaux) * 360
        return None
        
    @property
    def compte_debiteur(self):
        """ Rotation des créances = Chiffre d'affaires / Créances clients """
        creances_clients = self._get_val(self.actif, 'creances_emplois_similaires')
        if creances_clients != 0:
            return self.resultat.chiffre_affaires / creances_clients if self.resultat else None
        return None
        
    @property
    def rotation_actif(self):
        """ Rotation de l'actif = Chiffre d'affaires / Actif total """
        if self.actif and self.actif.total_actif and self.actif.total_actif != 0:
            return self.resultat.chiffre_affaires / self.actif.total_actif if self.resultat else None
        return None
        
    @property
    def rotation_dendettement(self):
        """ Ratio d'endettement = Dettes financières / Capitaux propres """
        dettes_financieres = self._get_val(self.passif, 'emprunts_dettes_financieres_diverse')
        capitaux_propres = self._get_val(self.passif, 'total_capitaux_propres_ressources_similaires')
        if capitaux_propres != 0:
            return dettes_financieres / capitaux_propres
        return None
        
    @property
    def rotation_dette_capitaux_propres(self):
        """ Dette / Capitaux propres = Dettes totales / Capitaux propres """
        dettes_totales = (self._get_val(self.passif, 'total_dettes_financieres_ressources_similaires') + 
                         self._get_val(self.passif, 'total_passifs_courants'))
        capitaux_propres = self._get_val(self.passif, 'total_capitaux_propres_ressources_similaires')
        if capitaux_propres != 0:
            return dettes_totales / capitaux_propres
        return None
        
    @property
    def passif_court_terme_par_rapport_valeur_net(self):
        """ Passif court terme / Actif net = Passif courant / Capitaux propres """
        passif_courant = self._get_val(self.passif, 'total_passifs_courants')
        capitaux_propres = self._get_val(self.passif, 'total_capitaux_propres_ressources_similaires')
        if capitaux_propres != 0:
            return passif_courant / capitaux_propres
        return None
        
    @property
    def ratio_des_couverture_des_interets(self):
        """ Couverture des intérêts = Résultat d'exploitation / Charges financières """
        resultat_exploitation = self.resultat.resultat_exploitation if self.resultat else None
        charges_financieres = self._get_val(self.resultat, 'charges_financieres_assimilees')
        if charges_financieres != 0:
            return resultat_exploitation / charges_financieres
        return None
        
    @property
    def ratio_courant(self):
        """ Ratio courant = Actif circulant / Passif circulant """
        actif_circulant = self._get_val(self.actif, 'total_actif_circulant')
        passif_courant = self._get_val(self.passif, 'total_passifs_courants')
        if passif_courant != 0:
            return actif_circulant / passif_courant
        return None
        
    @property
    def ratio_de_liquidite(self):
        """ Ratio de liquidité = (Actif circulant - Stocks) / Passif circulant """
        return self.liquidite_reduite  # Même calcul que liquidite_reduite
        
    @property
    def ratio_financier(self):
        """ Ratio financier = Immobilisations financières / Actif total """
        if self.actif and self.actif.total_actif and self.actif.total_actif != 0:
            immobilisations_financieres = self._get_val(self.actif, 'immobilisations_financieres')
            return immobilisations_financieres / self.actif.total_actif
        return None
        
    @property
    def ratio_de_la_dette(self):
        """ Ratio de la dette = Dettes totales / Actif total """
        if self.actif and self.actif.total_actif and self.actif.total_actif != 0:
            dettes_totales = (self._get_val(self.passif, 'total_dettes_financieres_ressources_similaires') + 
                             self._get_val(self.passif, 'total_passifs_courants'))
            return dettes_totales / self.actif.total_actif
        return None
        
    @property
    def ratio_de_liquidite2(self):
        """ Ratio de liquidité 2 = Immobilisations incorporelles / Capitaux propres """
        capitaux_propres = self._get_val(self.passif, 'total_capitaux_propres_ressources_similaires')
        if capitaux_propres != 0:
            immobilisations_incorporelles = self._get_val(self.actif, 'immobilisations_incorporelles')
            return immobilisations_incorporelles / capitaux_propres
        return None
        






##########################################################
##########################################################
# Fin Modules Bilan SysCohada
##########################################################
##########################################################

##########################################################
##########################################################
# Debut Modules Bilan IRFS COBAC
##########################################################
##########################################################
# Fichier: DANS VOTRE FICHIER models.py

from django.db import models
from django.utils.translation import gettext_lazy as _

# Ces énumérations sont déjà définies dans votre code, nous les réutilisons.
TYPE_BILAN_CHOICES = (
    ("annuel", "Bilan annuel"),
    ("semestriel", "Bilan semestriel"),
)
SEMESTRE_CHOICES = (
    (1, "1er semestre (Janvier - Juin)"),
    (2, "2e semestre (Juillet - Décembre)"),
)


class BilanIFRSBase(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    """
    Modèle abstrait de base pour les états financiers IFRS.
    Contient les champs communs d'identification et de suivi.
    """

    type_bilan = models.CharField(
        max_length=20,
        choices=TYPE_BILAN_CHOICES,
        default="annuel",
        verbose_name=_("Type de bilan"),
    )
    annee = models.ForeignKey(
        "Annee",
        null=True,
        blank=True,
        on_delete=models.PROTECT,  # Utiliser PROTECT pour éviter la suppression accidentelle
        verbose_name=_("Année Civile"),
    )
    semestre = models.PositiveSmallIntegerField(
        choices=SEMESTRE_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Semestre"),
        help_text=_("Laisser vide si le bilan est annuel."),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_("Acheteur"),
    )

    # Champs de suivi
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey(
        "CustomUser",
        related_name="%(class)s_created",
        on_delete=models.SET_NULL,
        null=True,
    )
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="%(class)s_updated",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )


    class Meta:
        abstract = True  # Indique que ce modèle est abstrait
        unique_together = (
            "acheteur",
            "annee",
            "semestre",
        )  # Assure qu'il n'y a qu'un seul bilan par période et par acheteur
        ordering = ["-annee", "-semestre"]

    def __str__(self):
        """
        Fournit une représentation textuelle claire de l'objet.
        """
        libelle = f"{self.acheteur or 'N/A'}"
        if self.annee:
            libelle += f" ({self.annee})"
        if self.semestre:
            libelle += f" - {self.get_semestre_display()}"
        return libelle


from django.db import models
from django.utils.translation import gettext_lazy as _

# Assurez-vous que BilanIFRSBase est défini au-dessus de cette classe.


class ActifIFRS(BilanIFRSBase):
    """
    Modèle pour l'Actif du bilan, basé sur la structure fournie.
    """

    # === ACTIF NON COURANT ===

    # --- Immobilisations incorporelles ---
    goodwill = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Goodwill")
    )
    marques_et_droits_auteur = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Marques et droits d'auteur"),
    )
    brevets_et_licences = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Brevets et licences"),
    )
    autres_immobilisations_incorporelles = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Autres immobilisations incorporelles"),
    )

    # --- Immobilisations corporelles ---
    terrains = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Terrains")
    )
    batiments = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Bâtiments")
    )
    materiel_et_equipement = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Matériel et équipement"),
    )

    # --- Immobilisations financières ---
    participations_dans_des_societes = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Participations dans des sociétés"),
    )
    prets_a_long_terme = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Prêts à long terme")
    )

    # === ACTIF COURANT ===

    # --- Stocks ---
    matieres_premieres = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Matières premières")
    )
    produits_finis = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Produits finis")
    )

    # --- Créances ---
    creances_a_court_terme = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Créances à court terme"),
    )
    avances_et_acomptes = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Avances et acomptes"),
    )
    creances_diverses = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Créances diverses")
    )

    # --- Trésorerie ---
    disponibilites_bancaires = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Disponibilités bancaires"),
    )

    history = HistoricalRecords()


    # === PROPRIÉTÉS DE CALCUL AUTOMATIQUE ===

    @property
    def total_actif_non_courant(self):
        """Calcule le total de l'actif non courant."""
        fields = [
            self.goodwill,
            self.marques_et_droits_auteur,
            self.brevets_et_licences,
            self.autres_immobilisations_incorporelles,
            self.terrains,
            self.batiments,
            self.materiel_et_equipement,
            self.participations_dans_des_societes,
            self.prets_a_long_terme,
        ]
        return sum(field or 0 for field in fields)

    @property
    def total_actif_courant(self):
        """Calcule le total de l'actif courant."""
        fields = [
            self.matieres_premieres,
            self.produits_finis,
            self.creances_a_court_terme,
            self.avances_et_acomptes,
            self.creances_diverses,
            self.disponibilites_bancaires,
        ]
        return sum(field or 0 for field in fields)

    @property
    def total_actif(self):
        """Calcule le total général de l'actif."""
        return self.total_actif_non_courant + self.total_actif_courant

    class Meta(BilanIFRSBase.Meta):
        verbose_name = _("Actif IFRS")
        verbose_name_plural = _("Actifs IFRS")


class PassifIFRS(BilanIFRSBase):
    """
    Modèle pour le Passif et les Capitaux Propres du bilan, basé sur la nouvelle structure.
    """

    # === CAPITAUX PROPRES ===
    capital_social = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Capital social")
    )
    primes_emission = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Primes d'émission")
    )
    reserves_legales = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Réserves légales")
    )
    reserves_statutaires = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Réserves statutaires"),
    )
    reserves_facultatives = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Réserves facultatives"),
    )
    autres_reserves = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Autres réserves")
    )
    resultat_net_reporte = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Résultat net reporté"),
    )

    # === PASSIF NON COURANT ===
    emprunts_bancaires_long_terme = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Emprunts bancaires à long terme"),
    )
    obligations = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Obligations")
    )
    provisions_pour_retraites_et_pensions = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Provisions pour retraites et pensions"),
    )
    autres_provisions = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Autres provisions")
    )

    # === PASSIF COURANT ===
    dettes_fournisseurs_a_court_terme = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Dettes fournisseurs à court terme"),
    )
    impots_sur_le_revenu = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Impôts sur le revenu"),
    )
    cotisations_sociales = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Cotisations sociales"),
    )
    emprunts_bancaires_court_terme = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Emprunts bancaires à court terme"),
    )
    dettes_diverses = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Dettes diverses")
    )
    dividendes_a_payer = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Dividendes à payer")
    )

    history = HistoricalRecords()


    # === PROPRIÉTÉS DE CALCUL AUTOMATIQUE ===

    @property
    def total_capitaux_propres(self):
        """Calcule le total des capitaux propres."""
        return sum(
            field or 0
            for field in [
                self.capital_social,
                self.primes_emission,
                self.reserves_legales,
                self.reserves_statutaires,
                self.reserves_facultatives,
                self.autres_reserves,
                self.resultat_net_reporte,
            ]
        )

    @property
    def total_passif_non_courant(self):
        """Calcule le total du passif non courant."""
        return sum(
            field or 0
            for field in [
                self.emprunts_bancaires_long_terme,
                self.obligations,
                self.provisions_pour_retraites_et_pensions,
                self.autres_provisions,
            ]
        )

    @property
    def total_passif_courant(self):
        """Calcule le total du passif courant."""
        return sum(
            field or 0
            for field in [
                self.dettes_fournisseurs_a_court_terme,
                self.impots_sur_le_revenu,
                self.cotisations_sociales,
                self.emprunts_bancaires_court_terme,
                self.dettes_diverses,
                self.dividendes_a_payer,
            ]
        )

    @property
    def total_passif(self):
        """Calcule le total général du passif (Passif + Capitaux Propres)."""
        return (
            self.total_capitaux_propres
            + self.total_passif_non_courant
            + self.total_passif_courant
        )

    class Meta(BilanIFRSBase.Meta):
        verbose_name = _("Passif IFRS")
        verbose_name_plural = _("Passifs IFRS")


from django.db import models
from django.utils.translation import gettext_lazy as _

# Assurez-vous que votre classe de base BilanIFRSBase est définie au-dessus.


class ResultatIFRS(BilanIFRSBase):
    """
    Modèle pour le Compte de Résultat, basé sur la nouvelle structure.
    """

    # === PRODUITS ===
    ventes_biens = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Ventes de biens")
    )
    ventes_services = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Ventes de services")
    )
    subventions_exploitation = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Subventions d'exploitation"),
    )
    revenus_exceptionnels = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Revenus exceptionnels"),
    )
    revenus_financiers = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, verbose_name=_("Revenus financiers")
    )

    # === CHARGES ===
    achats_matieres_premieres = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Achats de matières premières"),
    )
    autres_couts_directs = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Autres coûts directs"),
    )
    salaires_et_charges_sociales = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Salaires et charges sociales"),
    )
    loyer_et_charges_locatives = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Loyer et charges locatives"),
    )
    autres_charges_exploitation = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Autres charges d'exploitation"),
    )
    amortissement_des_immobilisations = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Amortissement des immobilisations"),
    )
    provisions_pour_risques_et_charges = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Provisions pour risques et charges"),
    )
    charges_financieres = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Charges financières (Charges d'intérêts)"),
    )
    impot_sur_les_societes = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name=_("Impôt sur les sociétés"),
    )

    history = HistoricalRecords()


    # === PROPRIÉTÉS DE CALCUL AUTOMATIQUE (SOLDES INTERMÉDIAIRES) ===

    @property
    def chiffre_affaires(self):
        return (self.ventes_biens or 0) + (self.ventes_services or 0)

    @property
    def autres_produits_operationnels(self):
        return (self.subventions_exploitation or 0) + (self.revenus_exceptionnels or 0)

    @property
    def total_produits(self):
        return self.chiffre_affaires + self.autres_produits_operationnels

    @property
    def cout_des_ventes(self):
        return (self.achats_matieres_premieres or 0) + (self.autres_couts_directs or 0)

    @property
    def charges_operationnelles(self):
        return (
            (self.salaires_et_charges_sociales or 0)
            + (self.loyer_et_charges_locatives or 0)
            + (self.autres_charges_exploitation or 0)
        )

    @property
    def amortissements_et_provisions(self):
        return (self.amortissement_des_immobilisations or 0) + (
            self.provisions_pour_risques_et_charges or 0
        )

    @property
    def total_charges(self):
        # Exclut les charges financières et l'impôt qui sont traités plus bas
        return (
            self.cout_des_ventes
            + self.charges_operationnelles
            + self.amortissements_et_provisions
        )

    @property
    def resultat_operationnel(self):
        return self.total_produits - self.total_charges

    @property
    def resultat_financier(self):
        return (self.revenus_financiers or 0) - (self.charges_financieres or 0)

    @property
    def resultat_avant_impot(self):
        return self.resultat_operationnel + self.resultat_financier

    @property
    def resultat_net(self):
        return self.resultat_avant_impot - (self.impot_sur_les_societes or 0)

    class Meta(BilanIFRSBase.Meta):
        verbose_name = _("Compte de Résultat IFRS")
        verbose_name_plural = _("Comptes de Résultat IFRS")


# Fichier: models.py


class RatiosIFRS(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    """
    Modèle pour calculer et afficher les ratios financiers clés.
    """

    actif = models.OneToOneField(ActifIFRS, on_delete=models.CASCADE, related_name="+")
    passif = models.OneToOneField(
        PassifIFRS, on_delete=models.CASCADE, related_name="+"
    )
    resultat = models.OneToOneField(
        ResultatIFRS, on_delete=models.CASCADE, related_name="+"
    )

    annee = models.ForeignKey("Annee", on_delete=models.CASCADE, null=True)
    acheteur = models.ForeignKey("Acheteur", on_delete=models.CASCADE, null=True)

    history = HistoricalRecords()


    def __str__(self):
        return f"Ratios pour {self.acheteur} ({self.annee})"

    # --- Fonctions utilitaires pour éviter les erreurs de division par zéro ---
    def _safe_divide(self, numerator, denominator, percentage=False):
        """Version améliorée avec gestion d'erreurs complète"""
        try:
            numerator = float(numerator or 0)
            denominator = float(denominator or 0)
            if denominator == 0:
                return 0
            ratio = numerator / denominator
            return ratio * 100 if percentage else ratio
        except (TypeError, ValueError, ZeroDivisionError):
            return 0

    @property
    def roe(self):
        """ ROE = (Résultat net / Capitaux propres) * 100 """
        return self._safe_divide(
            self.resultat.resultat_net, 
            self.passif.total_capitaux_propres, 
            percentage=True
        )

    @property
    def roa(self):
        """ ROA = (Résultat net / Total actif) * 100 """
        return self._safe_divide(
            self.resultat.resultat_net,
            self.actif.total_actif,
            percentage=True
        )

    @property
    def marge_nette(self):
        """ Marge nette = (Résultat net / Chiffre d'affaires) * 100 """
        return self._safe_divide(
            self.resultat.resultat_net,
            self.resultat.chiffre_affaires,
            percentage=True
        )

    @property
    def marge_operationnelle(self):
        """ Marge opérationnelle = (Résultat opérationnel / Chiffre d'affaires) * 100 """
        return self._safe_divide(
            self.resultat.resultat_operationnel,
            self.resultat.chiffre_affaires,
            percentage=True
        )

    @property
    def marge_brute(self):
        """ Marge brute = (Chiffre d'affaires - Coût des ventes) / Chiffre d'affaires * 100 """
        gross_profit = (self.resultat.chiffre_affaires or 0) - (self.resultat.cout_des_ventes or 0)
        return self._safe_divide(gross_profit, self.resultat.chiffre_affaires, percentage=True)

    @property
    def liquidite_generale(self):
        """ Current Ratio = Actif courant / Passif courant """
        return self._safe_divide(
            self.actif.total_actif_courant,
            self.passif.total_passif_courant
        )

    @property
    def liquidite_immediate(self):
        """ Quick Ratio = (Actif courant - Stocks) / Passif courant """
        quick_assets = (self.actif.total_actif_courant or 0) - (
            (self.actif.matieres_premieres or 0) + (self.actif.produits_finis or 0)
        )
        return self._safe_divide(quick_assets, self.passif.total_passif_courant)

    @property
    def ratio_endettement_total(self):
        """ Debt Ratio = Total passif / Total actif * 100 """
        return self._safe_divide(
            self.passif.total_passif,
            self.actif.total_actif,
            percentage=True
        )

    @property
    def ratio_couverture_interets(self):
        """ Interest Coverage Ratio = Résultat avant impôt / Charges financières """
        return self._safe_divide(
            self.resultat.resultat_avant_impot,
            self.resultat.charges_financieres
        )

    @property
    def rotation_des_actifs(self):
        """ Asset Turnover = Chiffre d'affaires / Total actif * 100 """
        return self._safe_divide(
            self.resultat.chiffre_affaires,
            self.actif.total_actif,
            percentage=True
        )

    @property
    def dso(self):
        """ Days Sales Outstanding = (Créances clients / Chiffre d'affaires) * 365 """
        receivables = self.actif.creances_a_court_terme or 0
        return self._safe_divide(receivables, self.resultat.chiffre_affaires) * 365

    class Meta:
        verbose_name = _("Ratio IFRS")
        verbose_name_plural = _("Ratios IFRS")
        unique_together = ("acheteur", "annee")


##########################################################
##########################################################
# Fin Modules Bilan IRFS COBAC
##########################################################
##########################################################


##########################################################
##########################################################
# Debut Modules Additifs
##########################################################
##########################################################
class Logo(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="logo",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au logo"),
    )
    image = models.ImageField(
        _("Image"),
        upload_to="logos/",
        null=True,
        blank=True,
        help_text=_("Image du logo de l'entreprise"),
    )
    description = models.TextField(
        _("Description"), null=True, blank=True, help_text=_("Description du logo")
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Logo")
        verbose_name_plural = _("Logos")

    def __str__(self):
        return f"Logo de {self.acheteur.nom}"


class TelephoneAcheteur(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    telephone = models.TextField(max_length=100, verbose_name=_("Téléphone"))
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="telephones",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au téléphone"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="telephones_created",
    )
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="telephones_updated",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Téléphone")
        verbose_name_plural = _("Téléphones")

    def __str__(self):
        return f"Numéro de téléphone de {self.acheteur.nom}"


class AdresseAcheteur(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    adresse = models.TextField(max_length=100, verbose_name=_("Adresse"))
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="adresses",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au téléphone"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="adresses_created",
    )
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="adresses_updated",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Adresse")
        verbose_name_plural = _("Adresses")

    def __str__(self):
        return f"Adresse de {self.acheteur.nom}"



class PortableAcheteur(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    portable = models.TextField(max_length=100, verbose_name=_("Numéro portable"))
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="portables",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au portable"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="portables_created",
    )
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="portables_updated",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Portable")
        verbose_name_plural = _("Portables")

    def __str__(self):
        return f"Numéro de portable de {self.acheteur.nom}"



class EmailAcheteur(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    email = models.TextField(
        max_length=254,  # Limite la taille à celle d'une adresse email standard
        verbose_name=_("Adresse email"),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="emails",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé à l'email"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey(
        "CustomUser",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="emails_created",
    )
    updated_by = models.ForeignKey(
        "CustomUser",
        related_name="emails_updated",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Email")
        verbose_name_plural = _("Emails")

    def __str__(self):
        return f"Email de {self.acheteur.nom}"


class Document(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au document"),
    )
    titre = models.CharField(
        _("Titre"), max_length=255, help_text=_("Titre du document")
    )
    fichier = models.FileField(
        _("Fichier"), upload_to="documents/", help_text=_("Fichier du document")
    )
    description = models.TextField(
        _("Description"), null=True, blank=True, help_text=_("Description du document")
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    def __str__(self):
        return f"{self.titre} - {self.acheteur.nom}"


class Swot(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="swot",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé à l'analyse SWOT"),
    )
    forces = models.TextField(
        _("Forces"), null=True, blank=True, help_text=_("Forces de l'entreprise")
    )
    faiblesses = models.TextField(
        _("Faiblesses"),
        null=True,
        blank=True,
        help_text=_("Faiblesses de l'entreprise"),
    )
    opportunites = models.TextField(
        _("Opportunités"),
        null=True,
        blank=True,
        help_text=_("Opportunités de l'entreprise"),
    )
    menaces = models.TextField(
        _("Menaces"), null=True, blank=True, help_text=_("Menaces de l'entreprise")
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("SWOT")
        verbose_name_plural = _("SWOT")

    def __str__(self):
        return f"SWOT de {self.acheteur.nom}"


class ProduitService(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="produits_services",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé"),
    )
    produits = models.TextField(
        _("Produits"), null=True, blank=True, help_text=_("Produits de l'entreprise")
    )
    services = models.TextField(
        _("Services"), null=True, blank=True, help_text=_("Services de l'entreprise")
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Produit & Service")
        verbose_name_plural = _("Produits & Services")

    def __str__(self):
        return f"Produits & Services de {self.acheteur.nom}"


class Marque(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="marques",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé"),
    )
    marques = models.TextField(
        _("Marques"), null=True, blank=True, help_text=_("Marques de l'entreprise")
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Marque")
        verbose_name_plural = _("Marques")

    def __str__(self):
        return f"Marque de {self.acheteur.nom}"


class ProcedureCollective(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="procedures_collectives",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé à la procédure collective"),
    )
    type_procedure = models.CharField(
        _("Type de procédure"),
        max_length=255,
        help_text=_("Type de procédure collective (ex: Redressement judiciaire, Liquidation...)"),
    )
    date_ouverture = models.DateField(
        _("Date d'ouverture"),
        null=True,
        blank=True,
        help_text=_("Date d'ouverture de la procédure"),
    )
    date_cloture = models.DateField(
        _("Date de clôture"),
        null=True,
        blank=True,
        help_text=_("Date de clôture de la procédure"),
    )
    #tribunal = models.CharField(
        #_("Tribunal compétent"),
        #max_length=255,
        #null=True,
        #blank=True,
        #help_text=_("Nom du tribunal compétent"),
    #)
    #numero_dossier = models.CharField(
        #_("Numéro de dossier"),
        #max_length=100,
        #null=True,
        #blank=True,
        #help_text=_("Référence officielle du dossier"),
    #)
    #secteur_activite = models.CharField(
        #_("Secteur d'activité"),
        #max_length=255,
        #null=True,
        #blank=True,
        #help_text=_("Secteur d'activité de l'entreprise concernée"),
    #)
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description détaillée de la procédure collective"),
    )
    #montant_creance = models.DecimalField(
        #_("Montant total des créances déclarées"),
        #max_digits=15,
        #decimal_places=2,
        #null=True,
        #blank=True,
        #help_text=_("Montant en FCFA"),
    #)
    #impact_assureur = models.TextField(
        #_("Impact pour l’assureur crédit"),
        #null=True,
        #blank=True,
        #help_text=_("Résumé de l’impact et des mesures prises par l’assureur crédit"),
    #)

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Procédure Collective")
        verbose_name_plural = _("Procédures Collectives")

    def __str__(self):
        return f"{self.type_procedure} - {self.acheteur.nom if self.acheteur else ''}"


class RegistreCommerce(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="registre_commerce",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au registre de commerce"),
    )
    numero = models.CharField(
        _("Numéro de registre de commerce"),
        max_length=255,
        help_text=_("Numéro de registre de commerce de l'entreprise"),
    )
    date_inscription = models.DateField(
        _("Date d'inscription"),
        null=True,
        blank=True,
        help_text=_("Date d'inscription au registre de commerce"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Registre de Commerce")
        verbose_name_plural = _("Registres de Commerce")

    def __str__(self):
        return f"Registre de commerce de {self.acheteur.nom}"


class Cotisation(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="cotisations",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au numéro de sécurité sociale"),
    )
    numero = models.CharField(
        _("Numéro de sécurité sociale"),
        max_length=255,
        help_text=_("Numéro de sécurité sociale de l'entreprise"),
    )
    date_affiliation = models.DateField(
        _("Date d'affiliation"),
        null=True,
        blank=True,
        help_text=_("Date d'affiliation à la sécurité sociale"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Cotisation Sociale")
        verbose_name_plural = _("Cotisations Sociales")

    def __str__(self):
        return f"Cotisations Sociales de {self.acheteur.nom}"


class CodeNaceAcheteur(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="code_nace",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au code NACE"),
    )
    code = models.ForeignKey(
        "SubCategoryNaceCode",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="code_nace_acheteur",
        verbose_name=_("Acheteur"),
        help_text=_("Code associé au code NACE"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Code NACE Acheteur")
        verbose_name_plural = _("Codes NACE Acheteur")

    def __str__(self):
        return f"Code NACE de {self.acheteur.nom}"



class CodeNafAcheteur(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="code_naf",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au code NAF"),
    )
    code = models.ForeignKey(
        "SubCategoryNafCode",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="code_naf_acheteur",
        verbose_name=_("Acheteur"),
        help_text=_("Code associé au code NAF"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Code NAF Acheteur")
        verbose_name_plural = _("Codes NAF Acheteur")

    def __str__(self):
        return f"Code NAF de {self.acheteur.nom}"


# Tables supplementaires

# Assuming you already have an Acheteur model defined elsewhere
# For example:
# class Acheteur(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
#     nom = models.CharField(max_length=255)
#     # ... other fields for the buyer


class Certification(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    """
    Represents certifications obtained by an Acheteur.
    """

    TYPES = [
        ("management_risque", "Management du risque"),
        ("securite_information", "Management de la sécurité de l'information"),
        ("risk_manager", "Risk Manager & Méthodes d'Appréciation du Risque"),
        ("continuite_activite", "Management de la continuité d'activité (SMCA)"),
        ("anti_corruption", "Management Anti–Corruption"),
        ("cybersecurity_manager", "Lead Cybersecurity Manager"),
        ("qualite", "Management de la Qualité"),
        ("dpo_rgpd", "DPO : RGPD, Certified Data Protection Officer"),
        ("bon_payeur", "Certificat de Bon payeur"),
        ("autre", "Autre certification"),
    ]
    acheteur = models.ForeignKey(
        "Acheteur", on_delete=models.CASCADE, related_name="certifications"
    )
    type_certification = models.CharField(
        max_length=50, choices=TYPES, verbose_name="Type de Certification"
    )
    nom_certification = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nom Spécifique de la Certification",
    )
    date_obtention = models.DateField(
        blank=True, null=True, verbose_name="Date d'Obtention"
    )
    organisme_delivreur = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Organisme Délivreur"
    )
    description = models.TextField(
        blank=True, null=True, verbose_name="Description / Commentaires"
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = "Certification"
        verbose_name_plural = "Certifications"
        unique_together = ("acheteur", "type_certification", "nom_certification")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_data = {
            "type_certification": self.type_certification,
            "nom_certification": self.nom_certification,
            "date_obtention": self.date_obtention,
            "organisme_delivreur": self.organisme_delivreur,
        }

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not is_new:
            self._check_for_changes_and_log_alerts()
        super().save(*args, **kwargs)
        self.__original_data = {
            "type_certification": self.type_certification,
            "nom_certification": self.nom_certification,
            "date_obtention": self.date_obtention,
            "organisme_delivreur": self.organisme_delivreur,
        }

    def _check_for_changes_and_log_alerts(self):
        # Mappage des champs aux codes internes des ElementSurveillance
        field_to_element_code = {
            "type_certification": "CERTIFICATION_CHANGE",  # Un changement de type est un changement de certification
            "nom_certification": "CERTIFICATION_CHANGE",  # Idem
            "date_obtention": "CERTIFICATION_CHANGE",  # Idem
            "organisme_delivreur": "CERTIFICATION_CHANGE",  # Idem
        }

        changes_detected = {}

        # Pour NEW_CERTIFICATION: Si c'est un nouvel enregistrement
        if self.pk is None:  # Si l'objet est nouveau
            changes_detected.setdefault("NEW_CERTIFICATION", []).append(
                f"Une nouvelle certification a été ajoutée : '{self.nom_certification or self.get_type_certification_display()}'."
            )

        # Pour CERTIFICATION_LOSS: Si une certification est supprimée, cela est plus complexe à gérer avec save()
        # car save() est appelé sur l'instance qui est modifiée/créée.
        # Pour une suppression, vous devriez utiliser un signal `post_delete` ou un Manager personnalisé.
        # Pour l'instant, nous nous concentrons sur les modifications via save().

        for field_name, element_code in field_to_element_code.items():
            original_value = self.__original_data.get(field_name)
            current_value = getattr(self, field_name)

            if str(original_value or "") != str(current_value or ""):
                changes_detected.setdefault(element_code, []).append(
                    f"La certification '{self.nom_certification or self.get_type_certification_display()}' "
                    f": le champ '{self._meta.get_field(field_name).verbose_name}' est passé de "
                    f"'{original_value or 'vide'}' à '{current_value or 'vide'}'."
                )

        if changes_detected:
            portefeuilles_concernés = Portefeuille.objects.filter(
                portefeuilleclient__acheteur=self.acheteur
            ).distinct()

            for portefeuille in portefeuilles_concernés:
                for element_code, messages in changes_detected.items():
                    try:
                        element_surveillance = ElementSurveillance.objects.get(
                            code_interne=element_code
                        )
                        if portefeuille.elements_surveillance_actifs.filter(
                            pk=element_surveillance.pk
                        ).exists():
                            for message in messages:
                                AlerteLog.objects.create(
                                    portefeuille=portefeuille,
                                    acheteur=self.acheteur,
                                    element_surveille=element_surveillance,
                                    message=message,
                                    content_object=self,
                                )
                    except ElementSurveillance.DoesNotExist:
                        print(
                            f"ATTENTION: Élément de surveillance avec code_interne '{element_code}' non trouvé. Veuillez l'ajouter à la liste des ElementSurveillance."
                        )

    def __str__(self):
        return f"{self.acheteur.nom} - {self.get_type_certification_display()}"


class InnovationDeveloppement(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    """
    Represents innovation and development activities of an Acheteur.
    """

    TYPES_INNOVATION = [
        ("nouveau_produit_service", "Développement de Nouveau produit ou service"),
        ("nouveaux_outils_production", "Acquisition de nouveaux outils de production"),
        ("innovation_produit", "L'innovation de produit"),
        ("innovation_procede", "L'innovation de procédé"),
        ("innovation_commercialisation", "L'innovation de commercialisation"),
        ("innovation_organisation", "L'innovation d'organisation"),
    ]
    acheteur = models.ForeignKey(
        "Acheteur", on_delete=models.CASCADE, related_name="innovations"
    )
    type_innovation = models.CharField(
        max_length=50, choices=TYPES_INNOVATION, verbose_name="Type d'Innovation"
    )
    titre = models.CharField(
        max_length=255, verbose_name="Titre de l'Innovation", blank=True, null=True
    )
    description = models.TextField(
        blank=True, null=True, verbose_name="Description / Commentaires"
    )
    date_debut = models.DateField(blank=True, null=True, verbose_name="Date de Début")
    date_fin = models.DateField(
        blank=True, null=True, verbose_name="Date de Fin (si applicable)"
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = "Innovation et Développement"
        verbose_name_plural = "Innovations et Développements"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_data = {
            "type_innovation": self.type_innovation,
            "titre": self.titre,
            "date_debut": self.date_debut,
            "date_fin": self.date_fin,
        }

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not is_new:
            self._check_for_changes_and_log_alerts()
        super().save(*args, **kwargs)
        self.__original_data = {
            "type_innovation": self.type_innovation,
            "titre": self.titre,
            "date_debut": self.date_debut,
            "date_fin": self.date_fin,
        }

    def _check_for_changes_and_log_alerts(self):
        field_to_element_code = {
            "type_innovation": "NEW_PRODUCT_SERVICE",  # Si le type d'innovation est "nouveau produit/service"
            "titre": "INNOVATION_CHANGE",  # Générique pour toute autre modification
            "date_debut": "INNOVATION_CHANGE",
            "date_fin": "INNOVATION_CHANGE",
        }

        changes_detected = {}

        if self.pk is None and self.type_innovation == "nouveau_produit_service":
            changes_detected.setdefault("NEW_PRODUCT_SERVICE", []).append(
                f"Un nouveau produit ou service a été ajouté : '{self.titre or 'Non spécifié'}'."
            )

        for field_name, element_code in field_to_element_code.items():
            original_value = self.__original_data.get(field_name)
            current_value = getattr(self, field_name)

            if str(original_value or "") != str(current_value or ""):
                # Éviter de dupliquer si déjà capturé par 'NEW_PRODUCT_SERVICE' lors de la création
                if not (self.pk is None and element_code == "NEW_PRODUCT_SERVICE"):
                    changes_detected.setdefault(element_code, []).append(
                        f"L'innovation '{self.titre or self.get_type_innovation_display()}' "
                        f": le champ '{self._meta.get_field(field_name).verbose_name}' est passé de "
                        f"'{original_value or 'vide'}' à '{current_value or 'vide'}'."
                    )

        if changes_detected:
            portefeuilles_concernés = Portefeuille.objects.filter(
                portefeuilleclient__acheteur=self.acheteur
            ).distinct()

            for portefeuille in portefeuilles_concernés:
                for element_code, messages in changes_detected.items():
                    try:
                        element_surveillance = ElementSurveillance.objects.get(
                            code_interne=element_code
                        )
                        if portefeuille.elements_surveillance_actifs.filter(
                            pk=element_surveillance.pk
                        ).exists():
                            for message in messages:
                                AlerteLog.objects.create(
                                    portefeuille=portefeuille,
                                    acheteur=self.acheteur,
                                    element_surveille=element_surveillance,
                                    message=message,
                                    content_object=self,
                                )
                    except ElementSurveillance.DoesNotExist:
                        print(
                            f"ATTENTION: Élément de surveillance avec code_interne '{element_code}' non trouvé. Veuillez l'ajouter à la liste des ElementSurveillance."
                        )

    def __str__(self):
        return f"{self.acheteur.nom} - {self.get_type_innovation_display()}"


class StrategiePlanification(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    """
    Represents strategic and planning approaches of an Acheteur.
    """

    TYPES_STRATEGIE = [
        ("specialisation", "La spécialisation (faire une seule activité)"),
        ("diversification_liees", "La diversification (activités liées)"),
        ("diversification_non_liees", "La diversification (activités non liées)"),
        ("integration", "L'intégration (faire tout, seul)"),
        ("externalisation", "L'externalisation (faire-faire)"),
        (
            "planification_strategique",
            "Planification stratégique (objectifs long terme)",
        ),
        (
            "planification_tactique",
            "Planification tactique (implémentation stratégies)",
        ),
        (
            "planification_operationnelle",
            "Planification opérationnelle (détails quotidiens)",
        ),
    ]
    acheteur = models.ForeignKey(
        "Acheteur", on_delete=models.CASCADE, related_name="strategies"
    )
    type_strategie = models.CharField(
        max_length=50, choices=TYPES_STRATEGIE, verbose_name="Type de Stratégie"
    )
    description = models.TextField(
        blank=True, null=True, verbose_name="Description / Commentaires"
    )
    date_mise_en_place = models.DateField(
        blank=True, null=True, verbose_name="Date de Mise en Place"
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = "Stratégie et Planification"
        verbose_name_plural = "Stratégies et Planifications"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_data = {
            "type_strategie": self.type_strategie,
            "date_mise_en_place": self.date_mise_en_place,
            # Pour la détection de "Nouveau partenariat stratégique" ou "Changement de politique de prix"
            # Il faudrait des champs spécifiques pour ces éléments, ou analyser 'description'
        }

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not is_new:
            self._check_for_changes_and_log_alerts()
        super().save(*args, **kwargs)
        self.__original_data = {
            "type_strategie": self.type_strategie,
            "date_mise_en_place": self.date_mise_en_place,
        }

    def _check_for_changes_and_log_alerts(self):
        field_to_element_code = {
            "type_strategie": "STRATEGY_CHANGE",  # Générique pour tout changement de stratégie
            "date_mise_en_place": "STRATEGY_CHANGE",
        }

        # Logique pour les éléments spécifiques comme NEW_STRATEGIC_PARTNERSHIP ou PRICING_POLICY_CHANGE
        # Si ces éléments ne sont pas gérés par des champs dédiés,
        # vous devrez soit:
        # 1. Ajouter des champs spécifiques (ex: is_strategic_partnership_change = BooleanField)
        # 2. Faire une analyse textuelle du champ 'description', ce qui est moins fiable et plus coûteux.
        # Pour l'instant, je vais les ajouter comme des codes génériques si le type_strategie correspond.

        changes_detected = {}

        if self.pk is None:  # Si c'est une nouvelle stratégie/planification
            if self.type_strategie == "planification_strategique":
                changes_detected.setdefault("STRATEGIC_PLANNING_ADDED", []).append(
                    f"Une nouvelle planification stratégique a été ajoutée pour l'acheteur : '{self.titre or 'Non spécifié'}'."
                )
            # Vous pouvez ajouter d'autres conditions ici pour NEW_STRATEGIC_PARTNERSHIP si votre logique le permet
            # Par exemple, si vous avez un champ 'partenariat_strategique_recent' ou si le 'description' contient des mots clés
            # Pour 'COMMERCIAL_STRATEGY_CHANGE' et 'PRICING_POLICY_CHANGE', il faudrait soit un champ dédié, soit une détection dans 'description'
            # Je vais assumer un code générique pour les modifications si un champ spécifique n'est pas présent.

        for field_name, element_code in field_to_element_code.items():
            original_value = self.__original_data.get(field_name)
            current_value = getattr(self, field_name)

            if str(original_value or "") != str(current_value or ""):
                changes_detected.setdefault(element_code, []).append(
                    f"La stratégie '{self.get_type_strategie_display()}' "
                    f": le champ '{self._meta.get_field(field_name).verbose_name}' est passé de "
                    f"'{original_value or 'vide'}' à '{current_value or 'vide'}'."
                )

        if changes_detected:
            portefeuilles_concernés = Portefeuille.objects.filter(
                portefeuilleclient__acheteur=self.acheteur
            ).distinct()

            for portefeuille in portefeuilles_concernés:
                for element_code, messages in changes_detected.items():
                    try:
                        element_surveillance = ElementSurveillance.objects.get(
                            code_interne=element_code
                        )
                        if portefeuille.elements_surveillance_actifs.filter(
                            pk=element_surveillance.pk
                        ).exists():
                            for message in messages:
                                AlerteLog.objects.create(
                                    portefeuille=portefeuille,
                                    acheteur=self.acheteur,
                                    element_surveille=element_surveillance,
                                    message=message,
                                    content_object=self,
                                )
                    except ElementSurveillance.DoesNotExist:
                        print(
                            f"ATTENTION: Élément de surveillance avec code_interne '{element_code}' non trouvé. Veuillez l'ajouter à la liste des ElementSurveillance."
                        )

    def __str__(self):
        return f"{self.acheteur.nom} - {self.get_type_strategie_display()}"


class ConformiteReglementation(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    """
    Represents compliance and regulatory status of an Acheteur.
    """

    TYPES_CONFORMITE = [
        ("reglementaire", "La conformité réglementaire"),
        ("sectorielle", "La conformité sectorielle"),
        ("donnees", "La conformité des données"),
        ("non_conformite", "Non-conformité aux principes établis"),
    ]
    acheteur = models.ForeignKey(
        "Acheteur", on_delete=models.CASCADE, related_name="conformites"
    )
    type_conformite = models.CharField(
        max_length=50, choices=TYPES_CONFORMITE, verbose_name="Type de Conformité"
    )
    statut = models.BooleanField(
        default=True, verbose_name="Est Conforme ?"
    )  # True for conform, False for non-conformité
    details_non_conformite = models.TextField(
        blank=True,
        null=True,
        verbose_name="Détails de la Non-conformité (si applicable)",
    )
    date_verification = models.DateField(
        blank=True, null=True, verbose_name="Date de la dernière vérification"
    )
    organisme_controle = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Organisme de Contrôle"
    )
    commentaires = models.TextField(blank=True, null=True, verbose_name="Commentaires")

    history = HistoricalRecords()


    class Meta:
        verbose_name = "Conformité et Réglementation"
        verbose_name_plural = "Conformités et Réglementations"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_data = {
            "type_conformite": self.type_conformite,
            "statut": self.statut,
            "date_verification": self.date_verification,
        }

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not is_new:
            self._check_for_changes_and_log_alerts()
        super().save(*args, **kwargs)
        self.__original_data = {
            "type_conformite": self.type_conformite,
            "statut": self.statut,
            "date_verification": self.date_verification,
        }

    def _check_for_changes_and_log_alerts(self):
        field_to_element_code = {
            "type_conformite": "COMPLIANCE_CHANGE",  # Générique
            "date_verification": "COMPLIANCE_CHANGE",
        }

        changes_detected = {}

        # Spécifique pour les alertes de non-conformité
        original_statut = self.__original_data.get("statut")
        current_statut = self.statut
        self.__original_data.get("type_conformite")
        current_type = self.type_conformite

        # Alerte si le statut passe à NON-CONFORME
        if original_statut is True and current_statut is False:
            changes_detected.setdefault("NON_COMPLIANCE_ALERT", []).append(
                f"L'acheteur est maintenant en non-conformité pour le type '{self.get_type_conformite_display()}'."
                f" Détails: {self.details_non_conformite or 'Aucun'}"
            )
        # Alerte si une nouvelle réglementation applicable est ajoutée (si le type correspond à 'reglementaire' et que c'est une création)
        if self.pk is None and current_type == "reglementaire":
            changes_detected.setdefault("NEW_REGULATION", []).append(
                f"Une nouvelle réglementation applicable a été ajoutée : '{self.description or 'Non spécifié'}'."
            )

        for field_name, element_code in field_to_element_code.items():
            original_value = self.__original_data.get(field_name)
            current_value = getattr(self, field_name)

            if str(original_value or "") != str(current_value or ""):
                # Éviter de dupliquer si déjà capturé par des règles spécifiques (NON_COMPLIANCE_ALERT, NEW_REGULATION)
                if not (
                    (field_name == "statut" and element_code == "NON_COMPLIANCE_ALERT")
                    or (
                        self.pk is None
                        and field_name == "type_conformite"
                        and element_code == "NEW_REGULATION"
                    )
                ):
                    changes_detected.setdefault(element_code, []).append(
                        f"La conformité '{self.get_type_conformite_display()}' "
                        f": le champ '{self._meta.get_field(field_name).verbose_name}' est passé de "
                        f"'{original_value or 'vide'}' à '{current_value or 'vide'}'."
                    )

        if changes_detected:
            portefeuilles_concernés = Portefeuille.objects.filter(
                portefeuilleclient__acheteur=self.acheteur
            ).distinct()

            for portefeuille in portefeuilles_concernés:
                for element_code, messages in changes_detected.items():
                    try:
                        element_surveillance = ElementSurveillance.objects.get(
                            code_interne=element_code
                        )
                        if portefeuille.elements_surveillance_actifs.filter(
                            pk=element_surveillance.pk
                        ).exists():
                            for message in messages:
                                AlerteLog.objects.create(
                                    portefeuille=portefeuille,
                                    acheteur=self.acheteur,
                                    element_surveille=element_surveillance,
                                    message=message,
                                    content_object=self,
                                )
                    except ElementSurveillance.DoesNotExist:
                        print(
                            f"ATTENTION: Élément de surveillance avec code_interne '{element_code}' non trouvé. Veuillez l'ajouter à la liste des ElementSurveillance."
                        )

    def __str__(self):
        status = "Conforme" if self.statut else "Non-conforme"
        return f"{self.acheteur.nom} - {self.get_type_conformite_display()} ({status})"


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
class Notification(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    TYPE_NOTIF = [
        ("AFFECTATION", "Nouvelle affectation"),
        ("RAPPORT_SOUMIS", "Rapport soumis"),
        ("VALIDATION", "Rapport validé"),
        ("CORRECTION", "Correction demandée"),
        ("ENVOI_CLIENT", "Rapport envoyé au client"),
        ("RAPPEL", "Rappel de notification"),
    ]

    user = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Utilisateur concerné"),
    )
    # commande = models.ForeignKey('Commande', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Commande associée"))
    type = models.CharField(
        max_length=50, choices=TYPE_NOTIF, verbose_name=_("Type de notification")
    )
    message = models.TextField(verbose_name=_("Message de notification"))
    is_read = models.BooleanField(default=False, verbose_name=_("Lu"))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} - {self.user.username} ({'Lu' if self.is_read else 'Non lu'})"


class Commande(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    AVEC = 'Oui'
    SANS = 'Non'
    STATUS_CHANGE = (
        (AVEC, 'Oui'),
        (SANS, 'Non'),
    )
    

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
        blank=True,
    )
    reference_client = models.CharField(
        max_length=100,
        verbose_name=_("Référence client"),
        help_text=_("Référence attribuée par le client."),
        null=True,
        blank=True,
    )

    date_recept_commande = models.DateField(
        verbose_name=_("Date de réception de la demande"),
        help_text=_("Date à laquelle la demande a été reçue."),
        null=True,
        blank=True,
    )
    date_rapport = models.DateField(
        verbose_name=_("Date du rapport"),
        help_text=_("Date prévue pour l'émission du rapport."),
        null=True,
        blank=True,
    )

    delais = models.CharField(
        max_length=100,
        verbose_name=_("Délais"),
        help_text=_("Délai de traitement de la commande."),
        null=True,
        blank=True,
    )
    priorite = models.CharField(
        max_length=100,
        verbose_name=_("Priorité"),
        help_text=_("Niveau de priorité de la commande."),
        null=True,
        blank=True,
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
        "ModeleRapport",
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
        blank=True,
    )
    devise_credit_demande = models.ForeignKey(
        "Devise",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Devise du crédit demandé"),
        help_text=_("Devise utilisée pour le crédit demandé."),
        related_name="devise_credit_demande",
    )

    credit_recommande = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        verbose_name=_("Crédit recommandé"),
        help_text=_("Montant du crédit finalement recommandé."),
        null=True,
        blank=True,
    )
    devise_credit_recommande = models.ForeignKey(
        "Devise",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Devise du crédit recommandé"),
        help_text=_("Devise utilisée pour le crédit recommandé."),
        related_name="devise_credit_recommande",
    )

    numero_adresse = models.CharField(
        max_length=100,
        verbose_name=_("Numéro d'adresse"),
        help_text=_("Numéro de rue ou d'unité de l'adresse concernée."),
        null=True,
        blank=True,
    )
    rue_adresse = models.CharField(
        max_length=200,
        verbose_name=_("Rue adresse"),
        help_text=_("Nom de la rue de l'adresse concernée."),
        null=True,
        blank=True,
    )
    code_postale_adresse = models.CharField(
        max_length=200,
        verbose_name=_("Code postal adresse"),
        help_text=_("Code postal de l'adresse concernée."),
        null=True,
        blank=True,
    )
    telephone = models.CharField(
        max_length=100,
        verbose_name=_("Téléphone"),
        help_text=_("Numéro de téléphone du contact."),
        null=True,
        blank=True,
    )
    email = models.CharField(
        max_length=100,
        verbose_name=_("Email"),
        help_text=_("Adresse email du contact."),
        null=True,
        blank=True,
    )

    pays = models.ForeignKey(
        "Pays",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Pays"),
        help_text=_("Pays où se trouve l'entreprise ou le client."),
    )

    ville = models.ForeignKey(
        "Ville",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Ville"),
        help_text=_("Ville où se trouve l'entreprise ou le client."),
    )
    client = models.ForeignKey(
        "CustomUser",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Client"),
        help_text=_("Client ayant passé la commande."),
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
        help_text=_("Personne ou entité achetant le service ou produit."),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="nouvelle",
        verbose_name=_("Statut de la commande"),
    )
    
    # Champ pour tracer le validateur responsable
    validateur = models.ForeignKey(
        "CustomUser",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Validateur responsable"),
        help_text=_("Utilisateur responsable de la validation de cette commande."),
        related_name="commandes_validees",
    )

    # Champ pour tracer la date d'envoi au client
    date_envoi_client = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'envoi au client"),
        help_text=_("Date et heure à laquelle le rapport a été envoyé au client."),
    )

    # Champ pour éviter les envois multiples
    email_envoye = models.BooleanField(
        default=False,
        verbose_name=_("Email envoyé au client"),
        help_text=_("Indique si le rapport a déjà été envoyé au client."),
    )
    
    
    # Champs supplementaires
    imprimer_avec_etats_fin = models.CharField(max_length=20, default=AVEC, choices=STATUS_CHANGE, blank=True, null=True,
                              verbose_name=_("Imprimer le rapport avec les états financiers s'ils existent"))
    company_identification_number = models.CharField(max_length=100, blank=True, null=True,  verbose_name="Company Identification Number")
    address_additional = models.CharField(max_length=100, blank=True, null=True,  verbose_name="Address additional")
    state = models.CharField(max_length=100, blank=True, null=True,  verbose_name="State")
    postcode = models.CharField(max_length=100, blank=True, null=True,  verbose_name="Postcode")
    post_office = models.CharField(max_length=100, blank=True, null=True,  verbose_name="Post office")
    provider = models.CharField(max_length=100, blank=True, null=True,  verbose_name="Provider")
    comments = models.TextField(max_length=100, blank=True, null=True,  verbose_name="Comments")

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

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Commande")
        verbose_name_plural = _("Commandes")

    def __str__(self):
        return f"Commande {self.notre_ref or 'N/A'} - {self.raison_sociale}"


class SuiviCommande(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
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

    commande = models.ForeignKey(
        "Commande", on_delete=models.CASCADE, verbose_name=_("Commande")
    )
    user = models.ForeignKey(
        "CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Utilisateur"),
    )
    action = models.CharField(max_length=255, verbose_name=_("Action"))
    type = models.CharField(
        max_length=50,
        choices=TYPE_ACTIONS,
        default="AUTRE",
        verbose_name=_("Type d'action"),
    )
    commentaire = models.TextField(null=True, blank=True, verbose_name=_("Commentaire"))
    date_action = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de l'action")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Suivi de commande")
        verbose_name_plural = _("Suivis de commande")
        ordering = ["-date_action"]

    def __str__(self):
        return f"{self.get_type_display()} - {self.commande.notre_ref} ({self.user.username if self.user else 'Système'})"


class AffectationAnalyste(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    commande = models.ForeignKey(
        "Commande", on_delete=models.CASCADE, verbose_name=_("Commande")
    )
    analyste = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        verbose_name=_("Analyste"),
        related_name="analystes",
    )
    date_affectation = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date d'affectation")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Affectation d'analyste")
        verbose_name_plural = _("Affectations des analystes")

    def __str__(self):
        return f"Commande {self.commande.notre_ref} affectée à {self.analyste.username}"


class Rapport(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    commande = models.ForeignKey(
        "Commande", on_delete=models.CASCADE, verbose_name=_("Commande")
    )
    analyste = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        verbose_name=_("Analyste"),
        related_name="rapports",
    )
    fichier = models.FileField(upload_to="rapports/", verbose_name=_("Fichier rapport"))
    date_soumission = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de soumission")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Rapport")
        verbose_name_plural = _("Rapports")

    def __str__(self):
        return f"Rapport de {self.analyste.username} pour {self.commande.notre_ref}"


class ValidationRapport(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    rapport = models.OneToOneField(
        "Rapport", on_delete=models.CASCADE, verbose_name=_("Rapport")
    )
    validateur = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        verbose_name=_("Analyste validateur"),
        related_name="validations",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("en_attente", _("En attente")),
            ("valide", _("Validé")),
            ("a_corriger", _("À corriger")),
        ],
        default="en_attente",
        verbose_name=_("Statut de validation"),
    )
    commentaire = models.TextField(
        null=True, blank=True, verbose_name=_("Commentaire du validateur")
    )
    date_validation = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de validation")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Validation de rapport")
        verbose_name_plural = _("Validations de rapports")

    def __str__(self):
        return f"Validation de {self.rapport.commande.notre_ref} par {self.validateur.username}"



class ReportRequest(Model):
    _safedelete_policy = SOFT_DELETE_CASCADE
    history = HistoricalRecords()

    country = models.CharField(max_length=255,verbose_name=_("Country"), null=False, blank=False)
    buyer_name = models.CharField(max_length=255,verbose_name=_("Buyer Name"), null=False, blank=False)

    request_id = models.CharField(max_length=100,verbose_name=_("Request ID"), null=True, blank=True)
    requester_id = models.CharField(max_length=100,verbose_name=_("Requester ID"), null=True, blank=True)
    vat_number = models.CharField(max_length=100,verbose_name=_("VAT Number"), null=True, blank=True)
    registration_number = models.CharField(max_length=100,verbose_name=_("Registration Number"), null=True, blank=True)
    source_id = models.CharField(max_length=100,verbose_name=_("Source ID"), null=True, blank=True)
    address = models.CharField(max_length=255,verbose_name=_("Address"), null=True, blank=True)
    postal_code = models.CharField(max_length=255,verbose_name=_("Postal Code"), null=True, blank=True)
    city = models.CharField(max_length=255,verbose_name=_("City"), null=True, blank=True)
    buyer_phone_number = models.CharField(max_length=255,verbose_name=_("Buyer's Phone Number"), null=True, blank=True)
    buyer_fax_number = models.CharField(max_length=255,verbose_name=_("Buyer's Fax Number"), null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)

    created_by = models.ForeignKey("CustomUser", null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Created By"))
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField()

    def __str__(self):
        return f"""
        Request ID: {self.request_id}
        Requester ID: {self.requester_id}
        VAT Number: {self.vat_number}
        Registration Number: {self.registration_number}
        Source ID: {self.source_id}
        Buyer Name: {self.buyer_name}
        Address: {self.address}
        Postal Code: {self.postal_code}
        City: {self.city}
        Buyer Phone Number: {self.buyer_phone_number}
        Buyer Fax Number: {self.buyer_fax_number}
        Country: {self.country}
        """

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(ReportRequest, self).save(*args, **kwargs)




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
class Alerte(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    

    reference = models.CharField(
        max_length=255,
        verbose_name=_("Référence"),
        help_text=_("Référence de l'alerte."),
    )
    objet = models.CharField(
        max_length=255, verbose_name=_("Objet"), help_text=_("Objet de l'alerte.")
    )
    content = models.TextField(
        verbose_name=_("Message"), help_text=_("Message de l'alerte.")
    )

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

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Alerte")
        verbose_name_plural = _("Alertes")

    def __str__(self):
        return f"{self.reference} - {self.objet}"


class DocumentAlerte(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    alerte = models.ForeignKey(
        "Alerte",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="documents_alerte",
        verbose_name=_("Alerte"),
        help_text=_("Alerte associé au document"),
    )
    titre = models.CharField(
        _("Titre"), max_length=255, help_text=_("Titre du document")
    )
    fichier = models.FileField(
        _("Fichier"), upload_to="alertes/", help_text=_("Fichier du document")
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Document alerte")
        verbose_name_plural = _("Documents alerte")

    def __str__(self):
        return f"{self.titre}"



class Warning(Model):
    _safedelete_policy = SOFT_DELETE_CASCADE
    titre = models.CharField(max_length=500,verbose_name=_("Titre"), null=False, blank=False)
    description = models.TextField()
    acheteurs = models.ManyToManyField(Acheteur)
    created_by = models.ForeignKey("CustomUser", on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre


def warning_upload_path(instance, filename):
    return 'uploads/warnings/{}'.format(filename)


class WarningAttachment(Model):
    _safedelete_policy = SOFT_DELETE_CASCADE
    upload = models.FileField(upload_to=warning_upload_path, verbose_name='Veuillez choisir le fichier',
                              max_length=500, blank=False, null=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    warning = models.ForeignKey(Warning, on_delete=models.CASCADE, related_name='warning_attachments')

    def __str__(self):
        return self.upload.name

    def delete(self, *args, **kwargs):
        self.upload.delete()
        return super().delete(*args, **kwargs)

    def filename(self):
        import os
        try:
            return os.path.basename(self.upload.file.name)
        except Exception as e:
            return '404 File Not Found'



class NotifClient(Model):
    _safedelete_policy = SOFT_DELETE_CASCADE
    acheteurs = models.ManyToManyField(Acheteur)
    client = models.ForeignKey("CustomUser", on_delete=models.CASCADE)

    def __str__(self):
        return self.client.username


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


class CompteFinancierIrfs(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    TYPE_CHOICES = [
        ("Actif", _("Actif")),
        ("Passif", _("Passif")),
        ("Produit", _("Produit")),
        ("Charge", _("Charge")),
        ("Compte de Résultat", _("Compte de Résultat")),
    ]

    SOUS_TYPE_CHOICES = [
        ("Actif non courant", _("Actif non courant")),
        ("Passif non courant", _("Passif non courant")),
        ("Actif courant", _("Actif courant")),
        ("Capitaux propres", _("Capitaux propres")),
        ("Passif courant", _("Passif courant")),
        ("Produits", _("Produits")),
        ("Charges", _("Charges")),
        ("Autre", _("Autre")),
    ]

    nom = models.CharField(_("Nom"), max_length=255)
    type_compte = models.CharField(
        _("Type de Compte"), max_length=255, choices=TYPE_CHOICES
    )
    sous_type = models.CharField(
        _("Sous-Type"), max_length=255, choices=SOUS_TYPE_CHOICES, blank=True, null=True
    )

    history = HistoricalRecords()


    def __str__(self):
        return self.nom

    def get_type_compte_display(self):
        return dict(CompteFinancierIrfs.TYPE_CHOICES).get(self.type_compte, "")

    def get_sous_type_display(self):
        return dict(CompteFinancierIrfs.SOUS_TYPE_CHOICES).get(self.sous_type, "")


class ValeurCompteIrfs(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="comptes_financiers_irfs_acheteur",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au registre de commerce"),
    )
    compte = models.ForeignKey(
        CompteFinancierIrfs,
        verbose_name=_("Compte Financier"),
        on_delete=models.CASCADE,
    )
    annee = models.ForeignKey(
        "Annee", verbose_name=_("Année"), on_delete=models.CASCADE
    )
    valeur = models.DecimalField(_("Valeur"), max_digits=20, decimal_places=2)
    devise = models.ForeignKey(
        "Devise", verbose_name=_("Devise"), on_delete=models.CASCADE
    )

    history = HistoricalRecords()


    def __str__(self):
        return f"{self.compte.nom} - {self.annee.nom}"


class RatioFinancierIrfs(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    TYPE_RATIO_CHOICES = [
        ("Ratio financier", _("Ratio financier")),
        ("Liquidité", _("Liquidité")),
        ("Solvabilité", _("Solvabilité")),
        ("Rentabilité des ventes", _("Rentabilité des ventes")),
        ("Gestion", _("Gestion")),
    ]

    type_ratio = models.CharField(
        _("Type de Ratio"), max_length=255, choices=TYPE_RATIO_CHOICES
    )

    nom = models.CharField(_("Nom"), max_length=255)
    formule = models.CharField(_("Formule"), max_length=255)

    history = HistoricalRecords()


    def __str__(self):
        return self.nom


class ValeurRatioIrfs(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="ratios_irfs_acheteur",
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur associé au registre de commerce"),
    )
    ratio = models.ForeignKey(
        RatioFinancierIrfs, verbose_name=_("Ratio Financier"), on_delete=models.CASCADE
    )
    annee = models.ForeignKey(
        "Annee", verbose_name=_("Année"), on_delete=models.CASCADE
    )
    valeur = models.DecimalField(_("Valeur"), max_digits=10, decimal_places=2)

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


class CredendoCommande(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    sender_id = models.CharField(
        max_length=255, null=True, blank=True
    )  # ID unique du mail
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
    montant = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )  # Montant demandé
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
# Debut Scoring de defaillance
##########################################################
##########################################################
 


class ScoringSansBilanAcheteur(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"), max_length=50, unique=True, null=True, blank=True
    )

    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur spécifié"),
    )
    
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)

    comportement_de_paiement_ref = models.ForeignKey(
        "ModeleComportementPaiement",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Référence sur les locaux"),
    )
    age_company_ref = models.ForeignKey(
        "ModeleAgeSociete",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Référence sur l'age de l'acheteur"),
    )

    forme_juridique = models.ForeignKey(
        "FormeJuridique",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Forme Juridique"),
        help_text=_("Forme juridique de l'entreprise"),
    )
    avis_commercial_ref = models.ForeignKey(
        "ModeleAvisCommercial",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Référence Avis Commercial"),
    )
    locaux_ref = models.ForeignKey(
        "ModeleBail",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Référence sur les locaux"),
    )

    # Remplacez la ForeignKey par une ManyToMany
    categories_nace_ref = models.ManyToManyField(
        "CategoryNaceCode",
        blank=True,
        verbose_name=_("Catégories Code NACE"),
        help_text=_("Catégories Code NACE auxquelles appartient l'acheteur"),
    )

    scoring_value = models.FloatField(_("Valeur du score de défaillance"), default=0.0)
    interpretation = models.TextField(_("Interprétation"), blank=True, max_length=10000000)

    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

    history = HistoricalRecords()


    def __str__(self):
        return (
            f"{self.code} - {self.libelle}"
            if self.code and self.libelle
            else _("Modèle interpretation scoring sans bilan")
        )

    def is_empty(self):
        return not self.code and not self.libelle
    
    def has_changed(self):
        """Vérifie si les champs ont changé depuis la dernière sauvegarde"""
        if self.pk is None:
            return True
            
        old = ScoringSansBilanAcheteur.objects.get(pk=self.pk)
        fields = ['comportement_de_paiement_ref_id', 'age_company_ref_id', 
                 'forme_juridique_id', 'avis_commercial_ref_id', 'locaux_ref_id']
        
        for field in fields:
            if getattr(self, field) != getattr(old, field):
                return True
                
        # Vérifier les catégories NACE
        old_categories = set(old.categories_nace_ref.values_list('id', flat=True))
        new_categories = set(self.categories_nace_ref.values_list('id', flat=True))
        if old_categories != new_categories:
            return True
            
        return False

    def generate_interpretation(self):
        """Génère une interprétation textuelle en fonction du scoring_value."""
        score = self.scoring_value
        if score >= 9.5:
            return _("Risque excellent : Probabilité de défaillance très faible.")
        elif 8.5 <= score < 9.5:
            return _("Risque très faible : Probabilité de défaillance faible.")
        elif 7.5 <= score < 8.5:
            return _("Risque faible : Probabilité de défaillance modérée.")
        elif 6.5 <= score < 7.5:
            return _("Risque modéré : Probabilité de défaillance acceptable.")
        elif 5.5 <= score < 6.5:
            return _("Risque acceptable : Probabilité de défaillance moyennement élevée.")
        elif 4.5 <= score < 5.5:
            return _("Risque moyennement élevé : Probabilité de défaillance importante.")
        elif 3.5 <= score < 4.5:
            return _("Risque important : Probabilité de défaillance élevée.")
        elif 2.5 <= score < 3.5:
            return _("Risque élevé : Probabilité de défaillance très élevée.")
        elif 1.5 <= score < 2.5:
            return _("Risque très élevé : Probabilité de défaillance extrêmement élevée.")
        elif 0.5 <= score < 1.5:
            return _("Risque extrêmement élevé : Procédure d'insolvabilité probable.")
        else:
            return _("Procédure d'insolvabilité/procédure préliminaire/de règlement de la dette.")

    def calculate_scoring_value(self):
        poids = 0.0
        
        print(f"🔍 Calcul du score pour l'acheteur {self.acheteur_id}")
        
        # Champs simples
        if self.comportement_de_paiement_ref:
            poids += self.comportement_de_paiement_ref.poids
            print(f"📊 Comportement paiement: +{self.comportement_de_paiement_ref.poids}")

        if self.age_company_ref:
            poids += self.age_company_ref.poids
            print(f"📊 Age société: +{self.age_company_ref.poids}")

        if self.forme_juridique:
            poids += self.forme_juridique.poids
            print(f"📊 Forme juridique: +{self.forme_juridique.poids}")

        if self.avis_commercial_ref:
            poids += self.avis_commercial_ref.poids
            print(f"📊 Avis commercial: +{self.avis_commercial_ref.poids}")

        if self.locaux_ref:
            poids += self.locaux_ref.poids
            print(f"📊 Locaux: +{self.locaux_ref.poids}")

        # Catégories NACE (ManyToMany)
        if self.pk and self.categories_nace_ref.exists():
            poids_nace = sum(categorie.poids for categorie in self.categories_nace_ref.all())
            moyenne_nace = poids_nace / self.categories_nace_ref.count()
            poids += moyenne_nace
            print(f"📊 Catégories NACE ({self.categories_nace_ref.count()} catégories): +{moyenne_nace}")

        print(f"🎯 Score total calculé: {poids}")
        return poids

    def save(self, *args, **kwargs):
        # Calculer le score AVANT la sauvegarde
        self.scoring_value = self.calculate_scoring_value()
        self.interpretation = self.generate_interpretation()
        
        print(f"💾 Sauvegarde avec score: {self.scoring_value}")
        
        # Sauvegarder une seule fois
        super().save(*args, **kwargs)


    class Meta:
        verbose_name = _("Modèle interpretation scoring sans bilan")
        verbose_name_plural = _("Modèles interpretations scoring sans bilan")





##########################################################
##########################################################
# Debut Scoring de defaillance
##########################################################
##########################################################






##########################################################
##########################################################
# Debut Emailling
##########################################################
##########################################################
from django.db import models
from django.conf import settings
from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE
from simple_history.models import HistoricalRecords

AUTH_USER_MODEL = settings.AUTH_USER_MODEL


class MailInfo(SafeDeleteModel):
    safedelete_policy = SOFT_DELETE_CASCADE

    date_sent = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Un mail peut concerner plusieurs commandes
    commands = models.ManyToManyField('Commande')

    success = models.BooleanField(default=False)
    
    # Ajouter ces champs
    subject = models.CharField(_("Sujet"), max_length=500, blank=True, null=True)
    cc_emails = models.TextField(_("Emails en CC"), blank=True, null=True)
    formats_generes = models.JSONField(_("Formats générés"), default=list, blank=True)
    custom_days = models.IntegerField(_("Nombre de jours personnalisé"), null=True, blank=True)

    # Historique complet
    history = HistoricalRecords()

    def __str__(self):
        return f"Mail envoyé le {self.date_sent} par {self.user}"
    
    def get_cc_list(self):
        """Retourne la liste des emails en CC"""
        if self.cc_emails:
            return [email.strip() for email in self.cc_emails.split(';') if email.strip()]
        return []


class MailAttachment(SafeDeleteModel):
    safedelete_policy = SOFT_DELETE_CASCADE

    # Fichier joint
    upload = models.FileField(
        upload_to='uploads/mail_attachments/%Y/%m/',
        max_length=10000
    )

    # Un fichier joint peut appartenir à un mail (ou pas)
    mailinfo = models.ForeignKey(
        MailInfo,
        on_delete=models.SET_NULL,   # évite erreurs référentielles
        blank=True,
        null=True
    )

    # Historique des fichiers joints
    history = HistoricalRecords()

    def __str__(self):
        return self.upload.name


##########################################################
##########################################################
# Fin Emailling
##########################################################
##########################################################






##########################################################
##########################################################
# Debut API
##########################################################
##########################################################


class DocDownload(models.Model):
    acheteur = models.ForeignKey(Acheteur, on_delete=models.CASCADE)
    client = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s requested %s" % (self.client.username, self.acheteur.nom)





##########################################################
##########################################################
# Fin API
##########################################################
##########################################################


##########################################################
##########################################################
# Debut Modules Pelba
##########################################################
##########################################################


##########################################################
##########################################################
# Debut Modules Pelba
##########################################################
##########################################################