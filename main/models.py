import base64
import datetime
import os
import re
import time
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator, validate_email
from django.db import models
from django.db.models import ForeignKey
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from safedelete.managers import SafeDeleteManager
from safedelete.models import SOFT_DELETE_CASCADE, SafeDeleteModel
from safedelete.models import SafeDeleteModel as Model
from simple_history.models import HistoricalRecords

from main.constantes import *

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



# === Models User === #

ROLES_USERS = [
    ("Root", "Root"),
    ("Validateur", "Validateur"),
    ("Analyste", "Analyste"),
    ("Client", "Client"),
]




class UserReportQuota(models.Model):
    """Modele metier: UserReportQuota."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="report_quota"
    )
    max_reports = models.PositiveIntegerField(default=10)
    used_reports = models.PositiveIntegerField(default=0)

    def has_quota(self):
        return self.used_reports < self.max_reports

    def increment(self):
        self.used_reports += 1
        self.save(update_fields=["used_reports"])

    def __str__(self):
        return f"{self.user.username} ({self.used_reports}/{self.max_reports})"

class GeneratedReport(models.Model):
    """Modele metier: GeneratedReport."""
    REPORT_TYPES = (
        ("pdf", "PDF"),
        ("html", "HTML"),
        ("xml", "XML"),
        ("json", "JSON"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="generated_reports"
    )
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.CASCADE
    )
    report_type = models.CharField(max_length=10, choices=REPORT_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Referer(Model):
    """Modele metier: Referer."""
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


class AdminMails(Model):
    """Modele metier: AdminMails."""
    safedelete_policy = SOFT_DELETE_CASCADE
    
    email = models.EmailField(max_length=255, unique=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Email administrateur"
        verbose_name_plural = "Emails administrateurs"

    def __str__(self):
        return self.email



class User(AbstractUser):
    """Modele metier: User."""
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
        default="avatars/avatar.png",
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
        default="Root"
    )
    is_client = models.BooleanField(
        _("is client"),
        default=False,
        help_text=_("Designates whether this user is a client user."),
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
    
    password_changed_at = models.DateTimeField(
        _("password changed at"),
        null=True,
        blank=True,
        help_text=_("Date de la dernière modification du mot de passe.")
    )

    pays_actif = models.ForeignKey(
        "Pays",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="utilisateurs_pays_actif",
        verbose_name=_("Pays actif (toolbar)"),
        help_text=_("Dernier pays sélectionné dans la toolbar — persisté entre les sessions."),
    )

    preferred_language = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_("Langue préférée"),
        help_text=_("Langue de l'interface sélectionnée — persistée entre les sessions."),
    )

    history = HistoricalRecords()
    

    def __str__(self):
        return self.username
    
    def get_user_country(request):
        return request.user.pays

    def fullname(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        # Détecter si le mot de passe a changé
        if self.pk:
            old_user = User.objects.get(pk=self.pk)
            if self.password != old_user.password:
                self.password_changed_at = timezone.now()
        elif self.password:
            # Nouvel utilisateur
            self.password_changed_at = timezone.now()
        
        super().save(*args, **kwargs)


# === Models Localisation === #


class Pays(Model):
    """Modele metier: Pays."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    nom = models.CharField(
        max_length=50,
        verbose_name=_("Nom du pays"),
        help_text=_("Nom complet du pays, par exemple 'France' ou 'Cameroun'."),
    )
    code = models.CharField(
        max_length=10,
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
    devise = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name=_("Devise"),
        help_text=_("Code ou libellé de la devise, par exemple 'FCFA', 'EUR', 'USD'."),
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
    """Modele metier: Province."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    nom = models.CharField(
        max_length=50,
        verbose_name=_("Nom de la province"),
        help_text=_(
            "Nom complet de la province, par exemple 'Île-de-France' ou 'Ouest'."
        ),
    )
    code = models.CharField(
        max_length=10,
        verbose_name=_("Code de la province"),
        help_text=_(
            "Code unique de la province, par exemple 'IDF' pour l'Île-de-France ou 'OUEST' pour l'Ouest."
        ),
    )
    pays = models.ForeignKey(
        "Pays",
        blank=True,
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
        unique_together = ("nom", "pays")

    def __str__(self):
        return f"{self.nom} ({self.code})"


class Ville(Model):
    """Modele metier: Ville."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    nom = models.CharField(
        max_length=50,
        verbose_name=_("Nom de la ville"),
        help_text=_("Nom complet de la ville, par exemple 'Paris' ou 'Douala'."),
    )
    code = models.CharField(
        max_length=10,
        verbose_name=_("Code de la ville"),
        help_text=_(
            "Code unique de la ville, par exemple 'PAR' pour Paris ou 'DOU' pour Douala."
        ),
    )
    pays = models.ForeignKey(
        "Pays",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Pays"),
        help_text=_("Pays auquel appartient la ville."),
    )
    province = models.ForeignKey(
        "Province",
        blank=True,
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
        ordering = ["nom"]
        unique_together = ("nom", "pays")

    def __str__(self):
        return f"{self.nom} ({self.code})"


class Annee(Model):
    """Modele metier: Annee."""
    
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
    """Modele metier: Devise."""
    
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
    """Modele metier: CouleurCommentaire."""
    
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
    """Modele metier: CategoryNaceCode."""
    
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
    """Modele metier: SubCategoryNaceCode."""
    
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


class NaceSpecifique(Model):
    """NACE codes with 3-level classification: Activity → Type → Code."""

    activity    = models.CharField(max_length=255, db_index=True)
    type        = models.CharField(max_length=255, db_index=True)
    code        = models.CharField(max_length=50, unique=True)
    denomination = models.CharField(max_length=500)
    active      = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.denomination}"

    class Meta:
        verbose_name = "NACE Code (Specific)"
        verbose_name_plural = "NACE Codes (Specific)"
        ordering = ["activity", "type", "code"]
        indexes = [
            models.Index(fields=["activity", "type"]),
        ]


class CategoryNafCode(Model):
    """Modele metier: CategoryNafCode."""
    
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
    """Modele metier: SubCategoryNafCode."""
    
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
    """Modele metier: FormeJuridique."""
    
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
    """Modele metier: DomaineEntreprise."""
    
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
    """Modele metier: PosteEntreprise."""
    
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
    """Modele metier: CategorieEntreprise."""
    
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
    """Modele metier: StructureEntreprise."""
    
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
    """Modele metier: StatutEntreprise."""
    
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
    """Modele metier: ModeleRapport."""
    
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
    """Modele metier: ModeleAlarme."""
    
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
    """Modele metier: ModeleBilan."""
    
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
    """Modele metier: ModeleBail."""
    
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
    """Modele metier: ModeleNotation."""
    
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
    """Modele metier: ModeleAvisCommercial."""
    
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
    """Modele metier: ModeleRelationEntreprise."""
    
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
    """Modele metier: ModeleInformationNotationEntreprise."""
    
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
    """Modele metier: ModeleComportementPaiement."""
    
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
    """Modele metier: ModeleComportementJugement."""
    
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
    """Modele metier: ModeleAgeSociete."""
    
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
    """Modele metier: ModeleInterpretationScoringSansBilan."""
    
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
    """Modele metier: ElementSurveillance."""
    
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
    """Modele metier: Client."""
    
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
    """Modele metier: Contact."""
    
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
    """Modele metier: Portefeuille."""
    
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
    """Modele metier: PortefeuilleClient."""
    
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
    """Modele metier: NotificationLog."""
    
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
    """Modele metier: AlerteLog."""
    
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


class UpdatedObjects(models.Model):
    """Modele metier: UpdatedObjects."""
    acheteur = models.OneToOneField(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        related_name="updated_object",
        verbose_name=_("Acheteur"),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour"),
        db_index=True,
    )

    updated_model = models.CharField(
        max_length=255,
        verbose_name=_("Modèle mis à jour"),
        db_index=True,
    )

    class Meta:
        verbose_name = _("Objet mis à jour")
        verbose_name_plural = _("Objets mis à jour")
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["updated_model"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self):
        return f"{self.acheteur} → {self.updated_model}"


class Acheteur(Model):
    """Modele metier: Acheteur."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Code unique de l'acheteur"),
    )

    forme_juridique = models.ForeignKey(
        "FormeJuridique",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Forme Juridique"),
        help_text=_("Forme juridique de l'entreprise"),
    )
    
    code_nace = models.CharField(_("Code Nace"), max_length=100, choices=LISTE_NOUVEAUX_CODE_NACE, blank=True)

    nace_specifique = models.ForeignKey(
        "NaceSpecifique",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="NACE Code (Specific)",
        related_name="acheteurs",
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
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_created',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_update',
        verbose_name=_("Mis à jour par")
    )

    creation_complete = models.BooleanField(
        default=False,
        verbose_name=_("Création complète"),
        help_text=_("Indique si le wizard de création a été complété (4 étapes)"),
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
        field_to_element_code = {
            "nom": "COMPANY_NAME_CHANGE",
            "forme_juridique_id": "FORME_JURIDIQUE_CHANGE",
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
            "activite_principale": "ACTIVITY_CHANGE",
            "statut_entreprise_id": "STATUT_ENTREPRISE_CHANGE",
        }

        changes_detected = {}

        for field_name, element_code in field_to_element_code.items():
            original_value = self.__original_data.get(field_name)
            current_value = getattr(self, field_name)

            if field_name.endswith("_id"):
                if original_value != current_value:
                    field_verbose = self._meta.get_field(field_name).verbose_name
                    changes_detected.setdefault(element_code, []).append(
                        f"Le champ '{field_verbose}' a été modifié."
                    )
            else:
                if str(original_value or "") != str(current_value or ""):
                    field_verbose = self._meta.get_field(field_name).verbose_name
                    changes_detected.setdefault(element_code, []).append(
                        f"Le champ '{field_verbose}' est passé de '{original_value or 'vide'}' à '{current_value or 'vide'}'."
                    )

        # Logique pour les changements de statut d'entreprise
        original_statut_id = self.__original_data.get("statut_entreprise_id")
        current_statut_id = self.statut_entreprise_id

        if original_statut_id != current_statut_id and current_statut_id:
            try:
                current_statut = StatutEntreprise.objects.get(pk=current_statut_id)
                
                # CORRECTION ICI: Utilisez le bon nom d'attribut
                # Essayer différents noms possibles
                statut_name = ""
                if hasattr(current_statut, 'libelle'):
                    statut_name = current_statut.libelle.lower()
                elif hasattr(current_statut, 'nom'):
                    statut_name = current_statut.nom.lower()
                elif hasattr(current_statut, 'name'):
                    statut_name = current_statut.name.lower()
                elif hasattr(current_statut, 'titre'):
                    statut_name = current_statut.titre.lower()
                
                # Utiliser la valeur brute si on ne trouve pas le bon attribut
                if not statut_name:
                    statut_name = str(current_statut).lower()
                
                if "liquidation" in statut_name:
                    changes_detected.setdefault("LIQUIDATION", []).append(
                        f"Le statut de l'entreprise est passé à '{str(current_statut)}' (Liquidation)."
                    )
                elif "dissolution" in statut_name:
                    changes_detected.setdefault("DISSOLUTION", []).append(
                        f"Le statut de l'entreprise est passé à '{str(current_statut)}' (Dissolution)."
                    )
            except StatutEntreprise.DoesNotExist:
                pass

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
                            for message in messages:
                                AlerteLog.objects.create(
                                    portefeuille=portefeuille,
                                    acheteur=self,
                                    element_surveille=element_surveillance,
                                    message=message,
                                    content_object=self,
                                )
                    except ElementSurveillance.DoesNotExist:
                        # Ignorer silencieusement les éléments non trouvés
                        continue

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
    
    def validate_unique(self, exclude=None):
        super().validate_unique(exclude=exclude)
        print(self.nom, self.ville.pays)
        if Acheteur.objects.filter(
                nom__iexact=self.nom,
                ville__pays=self.ville.pays
        ).count() != 0:
            raise ValidationError("L'acheteur spécifié existe déjà")

    def __str__(self):
        return self.nom
    
    
def acheteur_upload_path(instance, filename):
    """
    Chemin d’upload des fichiers liés à un acheteur
    """
    acheteur_nom = slugify(instance.acheteur.nom) if instance.acheteur else "inconnu"
    filename = os.path.basename(filename)

    return f"uploads/acheteurs/{acheteur_nom}/{filename}"
    
    
class AcheteurUpload(Model):
    """Modele metier: AcheteurUpload."""
    _safedelete_policy = SOFT_DELETE_CASCADE

    acheteur = models.ForeignKey(
        Acheteur,
        on_delete=models.DO_NOTHING,
        related_name="uploads",
        verbose_name=_("Acheteur"),
    )

    upload = models.FileField(
        upload_to=acheteur_upload_path,
        verbose_name=_("Veuillez choisir le fichier"),
        max_length=500,
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de téléversement"),
        db_index=True,
    )

    class Meta:
        verbose_name = _("Fichier Acheteur")
        verbose_name_plural = _("Fichiers Acheteur")
        ordering = ("-uploaded_at",)

    def __str__(self):
        return self.filename()

    def delete(self, using=None, keep_parents=False):
        """
        Supprime le fichier physique avant la suppression DB
        """
        if self.upload:
            self.upload.delete(save=False)
        return super().delete(using=using, keep_parents=keep_parents)

    @property
    def filename(self):
        """
        Retourne le nom du fichier sans le chemin
        """
        if self.upload and hasattr(self.upload, "name"):
            return os.path.basename(self.upload.name)
        return _("Fichier introuvable")



class RapportTelecharger(Model):
    """Modele metier: RapportTelecharger."""

    downloaded_by = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        related_name="rapports_telecharges",
        verbose_name=_("Téléchargé par"),
    )

    download_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de téléchargement"),
        db_index=True,
    )

    acheteur = models.ForeignKey(
        Acheteur,
        on_delete=models.CASCADE,
        related_name="rapports_telecharges",
        verbose_name=_("Acheteur"),
    )

    type_rapport = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        verbose_name=_("Type de rapport"),
        db_index=True,
    )

    ref_commande_client = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Référence commande client"),
        db_index=True,
    )

    ref_commande_acremac = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Référence commande ACREMAC"),
        db_index=True,
    )

    pays_acheteur = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Pays de l’acheteur"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de mise à jour"),
    )

    class Meta:
        verbose_name = _("Rapport téléchargé")
        verbose_name_plural = _("Rapports téléchargés")
        ordering = ("-download_at",)
        indexes = [
            models.Index(fields=["type_rapport"]),
            models.Index(fields=["ref_commande_client"]),
            models.Index(fields=["ref_commande_acremac"]),
        ]

    def __str__(self):
        return f"{self.type_rapport or 'Rapport'} – {self.acheteur}"


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
    """Modele metier: Resume."""
    
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
        related_name="devise_capital_social",
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
    commentaire = models.TextField(
        blank=True, 
        null=True,  # Ajouter null=True comme dans V2
        max_length=10000000,  # Ajouter limite de longueur comme dans V2
        verbose_name=_("Commentaire")
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Dernière mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resume_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resume_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Résumé Financier")
        verbose_name_plural = _("Résumés Financiers")

    def __str__(self):
        return f"Résumé {self.pk} - {self.acheteur}"


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
    ("medium", _("Medium")),
    ("faible", _("Faible")),
]


class RiskRating(Model):
    """Modele metier: RiskRating."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        blank=True,  # Ajouté pour correspondre à V2
        null=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
        help_text=_("Acheteur concerné par l'évaluation du risque."),
    )
    # Champs BooleanField avec blank=True, null=True comme dans V2
    remboursabilite = models.BooleanField(
        default=False, 
        blank=True, 
        null=True,
        verbose_name=_("Remboursabilité")
    )
    situation_liquidite = models.BooleanField(
        default=False, 
        blank=True, 
        null=True,
        verbose_name=_("Situation de liquidité")
    )
    performance_rentabilite = models.BooleanField(
        default=False, 
        blank=True, 
        null=True,
        verbose_name=_("Performance de rentabilité")  # Retour au nom de V2
    )
    perspective_secteur = models.BooleanField(
        default=False, 
        blank=True, 
        null=True,
        verbose_name=_("Perspective secteur")  # Retour au nom de V2
    )
    qualite_information_analyse = models.BooleanField(
        default=False, 
        blank=True, 
        null=True,
        verbose_name=_("Qualité information analyse")  # Retour au nom de V2
    )
    existence_garantie = models.BooleanField(
        default=False, 
        blank=True, 
        null=True,
        verbose_name=_("Existence garantie")  # Retour au nom de V2
    )
    terme_financier_duree_pret = models.BooleanField(
        default=False, 
        blank=True, 
        null=True,
        verbose_name=_("Terme financier durée prêt")  # Retour au nom de V2
    )
    mesure_propre_soutenir_credit = models.BooleanField(
        default=False, 
        blank=True, 
        null=True,
        verbose_name=_("Mesure propre à soutenir le crédit")
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

    interpretation = models.TextField(
        blank=True, 
        null=True,  # Ajouté pour correspondre à V2
        max_length=10000000,  # Ajouté pour correspondre à V2
        verbose_name=_("Interprétation")
    )
    analyse = models.TextField(
        blank=True, 
        null=True,  # Ajouté pour correspondre à V2
        max_length=10000000,  # Ajouté pour correspondre à V2
        verbose_name=_("Analyse")
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Dernière mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        'User',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='risk_rating_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        'User',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='risk_rating_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Évaluation du Risque")
        verbose_name_plural = _("Évaluations des Risques")

    def __str__(self):
        return f"RiskRating {self.pk} - {self.acheteur}"
    
    # Méthodes de V2 à conserver
    def val(self):
        """Méthode de V2 - Retourne la valeur du score"""
        return self.calculate_risk_score()
    
    def img(self):
        """Méthode de V2 - Retourne le chemin de l'image"""
        return 'management_ang3.png'  # Ou utilisez la nouvelle méthode
    
    @staticmethod
    def valStr():
        """Méthode statique de V2"""
        return 'Bien'

    def _get_fallback_svg(self, score):
        """Génère un SVG de secours"""
        fallback_svg = f'''<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
            <circle cx="100" cy="100" r="90" fill="#f0f0f0" stroke="#333" stroke-width="3"/>
            <text x="100" y="110" text-anchor="middle" font-size="60" font-family="Arial" fill="#333">{score}</text>
            <text x="100" y="160" text-anchor="middle" font-size="20" font-family="Arial" fill="#666">/9</text>
        </svg>'''
        encoded_fallback = base64.b64encode(fallback_svg.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{encoded_fallback}"

    def _get_fallback_png(self, score):
        """Génère un PNG de secours pour éviter les problèmes d'affichage SVG dans le HTML local."""
        try:
            import io
            from PIL import Image, ImageDraw

            size = 220
            img = Image.new("RGBA", (size, size), (245, 247, 250, 255))
            draw = ImageDraw.Draw(img)

            draw.ellipse((15, 15, size - 15, size - 15), outline=(45, 85, 140, 255), width=6)
            draw.text((85, 78), str(score), fill=(25, 25, 25, 255))
            draw.text((98, 124), "/9", fill=(90, 90, 90, 255))

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"
        except Exception:
            return None

    def get_risk_gauge_image(self):
        from main.utils import generate_risk_gauge
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

        if score is None:
            score = 0

        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 0

        score = max(0, min(8, score))
        png_filenames = [f"{score}.png", f"{score}{score}.png"]
        svg_filename = f"{score}.svg"

        possible_png_paths = [
            os.path.join(settings.STATIC_ROOT, 'riskrating', png_name)
            for png_name in png_filenames
        ] + [
            os.path.join(settings.BASE_DIR, 'static', 'riskrating', png_name)
            for png_name in png_filenames
        ] + [
            os.path.join(settings.BASE_DIR, 'main', 'static', 'riskrating', png_name)
            for png_name in png_filenames
        ]

        for png_path in possible_png_paths:
            if os.path.exists(png_path):
                try:
                    with open(png_path, "rb") as png_file:
                        png_content = png_file.read()
                        encoded_png = base64.b64encode(png_content).decode("utf-8")
                        return f"data:image/png;base64,{encoded_png}"
                except Exception as e:
                    print(f"Erreur lecture PNG ({png_path}) : {e}")
                    continue

        possible_paths = [
            os.path.join(settings.STATIC_ROOT, 'riskrating', svg_filename),
            os.path.join(settings.BASE_DIR, 'static', 'riskrating', svg_filename),
            os.path.join(settings.BASE_DIR, 'main', 'static', 'riskrating', svg_filename),
        ]

        for svg_path in possible_paths:
            if os.path.exists(svg_path):
                try:
                    from svglib.svglib import svg2rlg
                    from reportlab.graphics import renderPM

                    drawing = svg2rlg(svg_path)
                    if drawing is not None:
                        png_bytes = renderPM.drawToString(drawing, fmt="PNG")
                        if png_bytes:
                            encoded_string = base64.b64encode(png_bytes).decode("utf-8")
                            return f"data:image/png;base64,{encoded_string}"
                except Exception as e:
                    print(f"Erreur conversion SVG->PNG ({svg_path}) : {e}")
                    continue

        fallback_png = self._get_fallback_png(score)
        if fallback_png:
            return fallback_png
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
    """Modele metier: DonneesEnregistrement."""
    
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
        null=True, blank=True, verbose_name=_("Date registre")
    )

    # Ancien attribut avec choices
    forme_juridique = models.CharField(
        max_length=4000,
        choices=NOUVEAU_LEGAL_FORM,
        default="Veuillez choisir la forme juridique",
        null=True,  # Ajouté pour correspondre à V2
        blank=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Forme juridique"),  # Nom de V2 pour la cohérence
    )

    numero_registre_commerce = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Numéro registre commerce")  # Nom de V2 pour la cohérence
    )
    numero_fiscale = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Numéro fiscal")  # Nom de V2 pour la cohérence
    )

    # Ancien champ avec choices
    statut_registre = models.CharField(
        max_length=4000,
        choices=LIEN_STATUT_CHOICE,  # Assurez-vous que cette variable est définie
        default="--------",
        null=True,  # Ajouté pour correspondre à V2
        blank=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Statut registre"),  # Nom de V2 pour la cohérence
    )

    

    commentaire = models.TextField(
        blank=True, 
        null=True,  # Ajouté pour correspondre à V2
        max_length=10000000,  # Ajouté pour correspondre à V2
        verbose_name=_("Commentaire")
    )
    couleur_commentaire = models.ForeignKey("CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Couleur Commentaire"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Dernière mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        'User',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='donnees_enregistrement_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        'User',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='donnees_enregistrement_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Données d'Enregistrement")
        verbose_name_plural = _("Données d'Enregistrement")

    def __str__(self):
        return f"Données Enregistrement {self.pk} - {self.acheteur}"
    
    # Méthodes utilitaires optionnelles
    def get_forme_juridique_display(self):
        """Retourne l'affichage de la forme juridique"""
        if self.forme_juridique:
            # Appelle la méthode de Django, pas elle-même
            return dict(NOUVEAU_LEGAL_FORM).get(self.forme_juridique, self.forme_juridique)
        return ""

    def get_statut_registre_display(self):
        """Retourne l'affichage du statut registre"""
        if self.statut_registre:
            return dict(LIEN_STATUT_CHOICE).get(self.statut_registre, self.statut_registre)
        return ""
    
    def is_registre_valide(self):
        """Vérifie si le registre est valide (a un numéro et une date)"""
        return bool(self.numero_registre_commerce and self.date_registre)
    
    def get_anciens_noms(self):
        """Retourne une liste des anciens noms (peut être étendu)"""
        noms = []
        if self.nom_anterieur:
            noms.append(self.nom_anterieur)
        return noms
    
    def clean(self):
        """Validation des données"""
        from django.core.exceptions import ValidationError
        
        super().clean()
        
        # Validation: date_registre ne peut pas être antérieure à date_creation
        if self.date_registre and self.date_creation:
            if self.date_registre < self.date_creation:
                raise ValidationError({
                    'date_registre': _("La date d'enregistrement ne peut pas être antérieure à la date de création.")
                })
        
        # Validation: vérifier le format du numéro fiscal si présent
        if self.numero_fiscale:
            # Exemple: nettoyer les espaces et vérifier la longueur
            cleaned_num = ''.join(self.numero_fiscale.split())
            if len(cleaned_num) < 5:
                raise ValidationError({
                    'numero_fiscale': _("Le numéro fiscal semble trop court.")
                })
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec validation optionnelle"""
        # Décommentez pour valider automatiquement avant la sauvegarde
        # self.full_clean()
        super().save(*args, **kwargs)


class Tendance(Model):
    """Modele metier: Tendance."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur", 
        null=True, 
        blank=True,  # Ajouté pour correspondre à V2
        on_delete=models.DO_NOTHING, 
        verbose_name=_("Acheteur")
    )

    avis_commercial = models.ForeignKey(
        "ListeInformationsAvisCommercial", 
        null=True, 
        blank=True, 
        on_delete=models.DO_NOTHING, 
        verbose_name=_("Avis commercial")
    )

    plus_informations = models.CharField(
        max_length=100, 
        choices=LIEN_PLUS_INFORMATIONS_NOTATION_CHOICE,  # Assurez-vous que cette variable est définie
        blank=True,
        verbose_name=_("Plus d'informations sur la notation")
    )
    
    presse_media = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name=_("Presse/Medias")  # Nom de V2 pour la cohérence
    )
    
    alarmes = models.CharField(
        max_length=100, 
        choices=LIEN_ALARMES_CHOICE,  # Assurez-vous que cette variable est définie
        blank=True, 
        verbose_name=_("Alarmes")
    )
    
    principaux_concurrent = models.TextField(
        blank=True, 
        max_length=10000000,  # Ajouté pour correspondre à V2
        verbose_name=_("Principaux concurrents")
    )
    
    commentaire = models.TextField(
        blank=True, 
        max_length=10000000,  # Ajouté pour correspondre à V2
        verbose_name=_("Commentaire")
    )

    created_at = models.DateTimeField(
        auto_now_add=True, 
        null=True,  # Ajouté pour correspondre à V2
        blank=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Date de création")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True, 
        null=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Dernière mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='tendance_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='tendance_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Tendance")
        verbose_name_plural = _("Tendances")

    def __str__(self):
        return f"Tendance {self.pk} - {self.acheteur}"
    
    # Méthodes utilitaires optionnelles
    @property
    def plus_informations_label(self):
        """Retourne le label lisible de 'Plus d'informations'"""
        if self.plus_informations:
            return dict(LIEN_PLUS_INFORMATIONS_NOTATION_CHOICE).get(self.plus_informations, self.plus_informations)
        return ""
    
    @property
    def alarmes_label(self):
        """Retourne le label lisible des alarmes"""
        if self.alarmes:
            return dict(LIEN_ALARMES_CHOICE).get(self.alarmes, self.alarmes)
        return ""
    
    @property
    def has_alarmes(self):
        """Vérifie s'il y a des alarmes"""
        return bool(self.alarmes and self.alarmes.strip() and self.alarmes != "--------")
    
    @property
    def has_plus_informations(self):
        """Vérifie s'il y a des informations supplémentaires"""
        return bool(self.plus_informations and self.plus_informations.strip() and self.plus_informations != "--------")
    
    def get_presse_media_list(self):
        """Retourne une liste des presse/médias (séparés par des virgules)"""
        if not self.presse_media:
            return []
        # Supposer que les médias sont séparés par des virgules
        return [media.strip() for media in self.presse_media.split(',') if media.strip()]
    
    def get_concurrents_list(self):
        """Retourne une liste des concurrents (format texte)"""
        if not self.principaux_concurrent:
            return []
        # Diviser par lignes ou points
        import re
        # Diviser par lignes ou points-virgules
        concurrents = re.split(r'[\n;]', self.principaux_concurrent)
        return [conc.strip() for conc in concurrents if conc.strip()]
    
    def get_avis_commercial_info(self):
        """Retourne les informations de l'avis commercial"""
        if self.avis_commercial:
            return {
                'id': self.avis_commercial.id,
                'nom': str(self.avis_commercial),
                # Ajouter d'autres champs si nécessaire
            }
        return None
    
    def get_summary(self):
        """Retourne un résumé des tendances"""
        summary = []
        
        if self.avis_commercial:
            summary.append(f"Avis commercial: {self.avis_commercial}")
        
        if self.has_plus_informations():
            summary.append(f"Plus d'infos: {self.get_plus_informations_display()}")
        
        if self.presse_media:
            summary.append(f"Presse/Médias: {self.presse_media}")
        
        if self.has_alarmes():
            summary.append(f"Alarmes: {self.get_alarmes_display()}")
        
        return ", ".join(summary) if summary else "Aucune information"
    
    def clean(self):
        """Validation des données"""
        from django.core.exceptions import ValidationError
        
        super().clean()
        
        # Validation: vérifier la longueur des champs si nécessaire
        if self.presse_media and len(self.presse_media) > 100:
            raise ValidationError({
                'presse_media': _("Le champ Presse/Médias ne peut pas dépasser 100 caractères.")
            })
        
        # Validation: vérifier que les choix sont valides
        if self.plus_informations and self.plus_informations not in dict(LIEN_PLUS_INFORMATIONS_NOTATION_CHOICE):
            raise ValidationError({
                'plus_informations': _("Valeur invalide pour 'Plus d'informations'.")
            })
        
        if self.alarmes and self.alarmes not in dict(LIEN_ALARMES_CHOICE):
            raise ValidationError({
                'alarmes': _("Valeur invalide pour 'Alarmes'.")
            })
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec validation optionnelle"""
        # Décommentez pour valider automatiquement avant la sauvegarde
        # self.full_clean()
        super().save(*args, **kwargs)


class ResponsableAcheteur(Model):
    """Modele metier: ResponsableAcheteur."""
    
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
    Sexe = models.CharField(
        _("Sexe"),
        max_length=20,
        default=STATUS_MASCULIN,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
    )

    poste = models.CharField(
        _("Poste"), 
        max_length=255, 
        choices=LISTE_NOUVELLE_FONCTION,  # Assurez-vous que cette variable est définie
        blank=True,
        null=True,  # Ajouté pour correspondre à V2
    )
    

    nationalite = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Nationalité")
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(
        blank=True, 
        null=True,  # Ajouté pour correspondre à V2
        max_length=10000000, 
        verbose_name=_("Commentaire")
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True, 
        null=True,  # Ajouté pour correspondre à V2
        blank=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Date de création")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True, 
        null=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Dernière mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsable_acheteur_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsable_acheteur_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Responsable Acheteur")
        verbose_name_plural = _("Responsables Acheteurs")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialiser les données originales pour le suivi des changements
        self.__original_data = {
            "nom": self.nom,
            "prenom": self.prenom,
            "Sexe": self.Sexe,
            "poste": self.poste,  # Corrigé: utiliser poste au lieu de poste_ref_id
            "nationalite": self.nationalite,
            "commentaire": self.commentaire,
        }
    
    def get_initials(self):
        """Retourne les initiales du responsable"""
        initials = ""
        if self.nom:
            initials += self.nom[0].upper()
        if self.prenom:
            initials += self.prenom[0].upper()
        return initials
    
    @property
    def commentaire_preview(self):
        """Retourne un aperçu du commentaire (100 premiers caractères)"""
        if self.commentaire:
            if len(self.commentaire) > 100:
                return self.commentaire[:100] + '...'
            return self.commentaire
        return ''
    
    @property
    def full_name(self):
        """Retourne le nom complet"""
        name_parts = []
        if self.nom:
            name_parts.append(self.nom)
        if self.prenom:
            name_parts.append(self.prenom)
        return " ".join(name_parts) if name_parts else "Non nommé"
    
    @property
    def nom_complet_inverse(self):
        """Retourne le nom complet au format "Prénom Nom" """
        name_parts = []
        if self.prenom:
            name_parts.append(self.prenom)
        if self.nom:
            name_parts.append(self.nom)
        return " ".join(name_parts) if name_parts else ""
    
    def is_masculin(self):
        """Vérifie si le responsable est masculin"""
        return self.Sexe == self.STATUS_MASCULIN
    
    def is_feminin(self):
        """Vérifie si le responsable est féminin"""
        return self.Sexe == self.STATUS_FEMININ
    
    def clean(self):
        """Validation des données"""
        from django.core.exceptions import ValidationError
        
        super().clean()
        
        # Validation: nom et prénom ne peuvent pas être vides tous les deux
        if not self.nom and not self.prenom:
            raise ValidationError(
                _("Au moins un des champs Nom ou Prénom doit être renseigné.")
            )
        
        # Validation: vérifier que le poste est valide si renseigné
        if self.poste and self.poste not in dict(LISTE_NOUVELLE_FONCTION):
            raise ValidationError({
                'poste': _("Valeur invalide pour le poste.")
            })
        
        # Validation: longueur du commentaire
        if self.commentaire and len(self.commentaire) > 10000000:
            raise ValidationError({
                'commentaire': _("Le commentaire ne peut pas dépasser 10,000,000 caractères.")
            })
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec validation et suivi des changements"""
        is_new = self.pk is None
        
        # Valider avant de sauvegarder
        self.full_clean()
        
        # Sauvegarder
        super().save(*args, **kwargs)
        
        # Mettre à jour les données originales
        self.__original_data = {
            "nom": self.nom,
            "prenom": self.prenom,
            "Sexe": self.Sexe,
            "poste": self.poste,
            "nationalite": self.nationalite,
            "commentaire": self.commentaire,
        }
        
        # Logique de surveillance des changements (optionnelle)
        if not is_new and self.acheteur:
            self._check_for_changes_and_log_alerts()

    def _check_for_changes_and_log_alerts(self):
        # Mappage des champs aux codes internes des ElementSurveillance
        field_to_element_code = {
            "nom": "EXECUTIVE_CHANGE",
            "prenom": "EXECUTIVE_CHANGE",
            "Sexe": "EXECUTIVE_CHANGE",
            "poste": "EXECUTIVE_CHANGE",
            "nationalite": "EXECUTIVE_CHANGE",
            "commentaire": "EXECUTIVE_REPUTATION",  # Alerte spécifique pour les commentaires
        }

        changes_detected = {}

        for field_name, element_code in field_to_element_code.items():
            original_value = self.__original_data.get(field_name)
            current_value = getattr(self, field_name)

            field = self._meta.get_field(field_name)
            if isinstance(field, ForeignKey):
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
    """Modele metier: AntecedantsJuridique."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    dossier_faillite = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Dossier faillite")  # Nom de V2 pour la cohérence
    )
    jugement_cour = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Jugement cour")  # Nom de V2 pour la cohérence
    )
    antecedant_redressement = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Antécédent de redressement")
    )
    Autre = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Autre")
    )

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

    created_at = models.DateTimeField(
        auto_now_add=True, 
        null=True,  # Ajouté pour correspondre à V2
        blank=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Date de création")  # Nom de V2 pour la cohérence
    )
    
    updated_at = models.DateTimeField(
        auto_now=True, 
        null=True,  # Ajouté pour correspondre à V2
        verbose_name=_("Dernière mise à jour")  # Plus clair que "Date de Mise à Jour"
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='antecedants_juridique_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name='antecedants_juridique_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    def get_antecedent_type(self):
        """Retourne le type principal de l'antécédent"""
        if self.dossier_faillite and self.dossier_faillite.strip():
            return 'faillite'
        elif self.jugement_cour and self.jugement_cour.strip():
            return 'jugement'
        elif self.antecedant_redressement and self.antecedant_redressement.strip():
            return 'redressement'
        elif self.Autre and self.Autre.strip():  # Correction: Autre avec majuscule
            return 'autre'
        return 'aucun'
    
    @property
    def has_content(self):
        """Vérifie si l'antécédent a du contenu"""
        return any([
            self.dossier_faillite and self.dossier_faillite.strip(),
            self.jugement_cour and self.jugement_cour.strip(),
            self.antecedant_redressement and self.antecedant_redressement.strip(),
            self.Autre and self.Autre.strip()  # Correction: Autre avec majuscule
        ])
    
    @property
    def has_commentaire(self):
        """Vérifie si l'antécédent a un commentaire"""
        return bool(self.commentaire and self.commentaire.strip())
    
    @property
    def commentaire_preview(self):
        """Retourne un aperçu du commentaire (100 premiers caractères)"""
        if self.commentaire:
            if len(self.commentaire) > 100:
                return self.commentaire[:100] + '...'
            return self.commentaire
        return ''
    
    def get_antecedent_summary(self):
        """Retourne un résumé de l'antécédent"""
        antecedents = []
        
        if self.dossier_faillite and self.dossier_faillite.strip():
            antecedents.append(f"Faillite: {self.dossier_faillite}")
        
        if self.jugement_cour and self.jugement_cour.strip():
            antecedents.append(f"Jugement: {self.jugement_cour}")
        
        if self.antecedant_redressement and self.antecedant_redressement.strip():
            antecedents.append(f"Redressement: {self.antecedant_redressement}")
        
        if self.Autre and self.Autre.strip():  # Correction: Autre avec majuscule
            antecedents.append(f"Autre: {self.Autre}")
        
        return "; ".join(antecedents) if antecedents else "Aucun antécédent spécifié"
    
    def get_severity_level(self):
        """Retourne le niveau de sévérité de l'antécédent"""
        if self.dossier_faillite and self.dossier_faillite.strip():
            return 'élevé'
        elif self.jugement_cour and self.jugement_cour.strip():
            return 'moyen'
        elif self.antecedant_redressement and self.antecedant_redressement.strip():
            return 'modéré'
        elif self.Autre and self.Autre.strip():  # Correction: Autre avec majuscule
            return 'faible'
        return 'aucun'
    
    def clean(self):
        """Validation des données"""
        from django.core.exceptions import ValidationError
        
        super().clean()
        
        # Validation: au moins un champ d'antécédent doit être rempli
        if not self.has_content and not self.commentaire:
            raise ValidationError(
                _("Au moins un champ d'antécédent ou un commentaire doit être renseigné.")
            )
        
        # Validation: longueur des champs
        for field_name in ['dossier_faillite', 'jugement_cour', 'antecedant_redressement', 'Autre']:
            value = getattr(self, field_name)
            if value and len(value) > 100:
                field_verbose = self._meta.get_field(field_name).verbose_name
                raise ValidationError({
                    field_name: _(f"Le champ '{field_verbose}' ne peut pas dépasser 100 caractères.")
                })
        
        # Validation: longueur du commentaire
        if self.commentaire and len(self.commentaire) > 10000000:
            raise ValidationError({
                'commentaire': _("Le commentaire ne peut pas dépasser 10,000,000 caractères.")
            })
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _("Antécédent Juridique")
        verbose_name_plural = _("Antécédents Juridiques")
        ordering = ['-created_at']

    def __str__(self):
        return f"Antécédent {self.id} - {self.acheteur}"


class RiskManagment(Model):
    """Modele metier: RiskManagment."""
    
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
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='risk_management_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='risk_management_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Gestion des Risques")
        verbose_name_plural = _("Gestión des Risques")

    def __str__(self):
        return f"Gestion des Risques - {self.acheteur}"
    
    def get_management_image_base64(self):
        """Retourne l'image en Base64 pour l'intégration directe dans le HTML"""
        relative_path = self.get_management_image_path_report()
        absolute_path = finders.find(relative_path)

        if not absolute_path:
            candidate_paths = [
                os.path.join(getattr(settings, "STATIC_ROOT", ""), relative_path),
                os.path.join(settings.BASE_DIR, "main", "static", relative_path),
                os.path.join(settings.BASE_DIR, "static", relative_path),
            ]
            for path in candidate_paths:
                if path and os.path.exists(path):
                    absolute_path = path
                    break

        if absolute_path and os.path.exists(absolute_path):
            with open(absolute_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

                if relative_path.endswith(".png"):
                    mime_type = "image/png"
                elif relative_path.endswith(".jpg") or relative_path.endswith(".jpeg"):
                    mime_type = "image/jpeg"
                elif relative_path.endswith(".svg"):
                    mime_type = "image/svg+xml"
                else:
                    mime_type = "image/png"

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
            return "/static/management/bien.png"
        elif non_count >= 4:
            return "/static/management/mauvais.png"
        else:
            return "/static/management/passable.png"
        
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
        
    def get_valeur(self):
        """Pour compatibilité avec le code existant qui utilise cette méthode"""
        valeur = 0
        if self.professionalisme == self.STATUS_NON:
            valeur += 1
        if self.organisation == self.STATUS_OUI:
            valeur += 1
        if self.turn_over == self.STATUS_NON:
            valeur += 1
        if self.greve == self.STATUS_NON:
            valeur += 1
        if self.degradation_qualite == self.STATUS_NON:
            valeur += 1
        if self.non_respect_condition == self.STATUS_OUI:
            valeur += 1
        return valeur

    def valeur_management(self, lang='fr'):
        """Pour compatibilité - à adapter à la nouvelle logique ou à déprécier"""
        score = self.get_management_score()
        
        if score['non_count'] >= 4:
            if lang == 'fr':
                return 'management_fr1.png'
            else:
                return 'management_ang1.png'
        elif score['oui_count'] >= 4:
            if lang == 'fr':
                return 'management_fr3.png'
            else:
                return 'management_ang3.png'
        else:
            if lang == 'fr':
                return 'management_fr2.png'
            else:
                return 'management_ang2.png'

    def valeur_management_entier(self, lang='fr'):
        score = self.get_management_score()
        
        if lang == 'fr':
            if score['non_count'] >= 4:
                return 'Mauvais'
            elif score['oui_count'] >= 4:
                return 'Bien'
            else:
                return 'Passable'
        else:
            if score['non_count'] >= 4:
                return 'Bad'
            elif score['oui_count'] >= 4:
                return 'Good'
            else:
                return 'Fair'


class ConseilAdministration(Model):
    """Modele metier: ConseilAdministration."""
    
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
        choices=LISTE_NOUVELLE_FONCTION,
        blank=True,
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
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conseil_administration_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conseil_administration_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Conseil d'Administration")
        verbose_name_plural = _("Conseils d'Administration")

    def __str__(self):
        return f"{self.nom} ({self.acheteur})"


class CompositionCapitalSocial(Model):
    """Modele metier: CompositionCapitalSocial."""
    
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
        default=None, # CORRIGÉ
        on_delete=models.DO_NOTHING,
        verbose_name=_("Dévise du capital libéré"),
    )
    emis = models.DecimalField(
        _("Capital émis"),
        max_digits=100,
        decimal_places=5,  # CONSERVER 5 décimales
        blank=True,
        null=True,
        help_text=_("Montant du capital émis"),
    )
    publie = models.DecimalField(
        _("Capital publié"),
        max_digits=100,
        decimal_places=5,  # CONSERVER 5 décimales
        blank=True,
        null=True,
        help_text=_("Montant du capital publié"),
    )
    libere = models.DecimalField(
        _("Capital libéré"),
        max_digits=100,
        decimal_places=5,  # CONSERVER 5 décimales
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
    commentaire = models.TextField(
        _("Commentaire"), 
        blank=True, 
        max_length=10000000,
        null=True  # AJOUTÉ pour compatibilité
    )

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='composition_capital_sociale_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='composition_capital_sociale_user_update',
        verbose_name=_("Mis à jour par")
    )

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
    """Modele metier: CompositionAction."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    nom = models.CharField(
        _("Nom"), 
        max_length=200, 
        blank=True,
        null=True  # AJOUTÉ
    )
    prenom = models.CharField(
        _("Prénom"), 
        max_length=200, 
        blank=True,
        null=True  # AJOUTÉ
    )
    pourcentage = models.DecimalField(
        _("Pourcentage"),
        max_digits=100,
        decimal_places=5,  # CONSERVER 5 décimales
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('100'))
        ],
        help_text=_("Pourcentage de détention (0-100) avec 2 décimales max")
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire"),
    )
    commentaire = models.TextField(
        _("Commentaire"), 
        blank=True, 
        max_length=10000000,
        null=True  # AJOUTÉ
    )

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='composition_action_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='composition_action_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            f"{self.nom} {self.prenom} - {self.pourcentage}%"
            if self.nom
            else _("Composition Action")
        )
        
    def clean(self):
        """Validation au niveau modèle"""
        super().clean()
        
        # Validation du pourcentage
        if self.pourcentage is not None:
            # Vérifier le format décimal
            if self.pourcentage.as_tuple().exponent < -2:
                raise ValidationError({
                    'pourcentage': 'Maximum 2 décimales autorisées'
                })
            
            # Vérifier que le total ne dépasse pas 100%
            if self.pk:  # Si mise à jour
                total = CompositionAction.objects.filter(
                    acheteur=self.acheteur
                ).exclude(pk=self.pk).aggregate(
                    total=models.Sum('pourcentage')
                )['total'] or Decimal('0')
            else:  # Si création
                total = CompositionAction.objects.filter(
                    acheteur=self.acheteur
                ).aggregate(
                    total=models.Sum('pourcentage')
                )['total'] or Decimal('0')
            
            nouveau_total = total + (self.pourcentage or Decimal('0'))
            if nouveau_total > 100:
                disponible = 100 - total
                raise ValidationError({
                    'pourcentage': f'Pourcentage disponible: {disponible:.2f}%'
                })
    
    def save(self, *args, **kwargs):
        """Override save pour inclure la validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Composition de l'Actionnariat")
        verbose_name_plural = _("Compositions de l'Actionnariat")


class OpinionCreditAcremac(Model):
    """Modele metier: OpinionCreditAcremac."""
    
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
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='opinion_acremac_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='opinion_acremac_user_update',
        verbose_name=_("Mis à jour par")
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
# Debut Modules Additifs
##########################################################
##########################################################
class Logo(Model):
    """Modele metier: Logo."""
    
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
    """Modele metier: TelephoneAcheteur."""
    
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
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="telephone_user_create",
    )
    updated_by = models.ForeignKey(
        "User",
        related_name="telephone_user_update",
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
    
    def get_formatted_number(self):
        """Retourne le numéro formaté pour l'affichage"""
        if not self.telephone:
            return ""
        
        # Nettoyer le numéro
        cleaned = re.sub(r'\D', '', str(self.telephone))
        
        # Format par préfixe de pays
        format_rules = {
            '241': lambda num: f"+{num[:3]} {num[3:5]} {num[5:7]} {num[7:9]} {num[9:11]}" if len(num) == 11 else self.telephone,
            '225': lambda num: f"+{num[:3]} {num[3:5]} {num[5:7]} {num[7:9]} {num[9:12]}" if len(num) == 12 else self.telephone,
            '223': lambda num: f"+{num[:3]} {num[3:5]} {num[5:7]} {num[7:9]} {num[9:11]}" if len(num) == 11 else self.telephone,
        }
        
        # Chercher le format correspondant
        for prefix in format_rules:
            if cleaned.startswith(prefix):
                return format_rules[prefix](cleaned)
        
        # Format général pour les numéros locaux
        if len(cleaned) == 8 and cleaned.startswith('0'):
            return f"{cleaned[:2]} {cleaned[2:4]} {cleaned[4:6]} {cleaned[6:8]}"
        elif len(cleaned) == 9 and cleaned.startswith('0'):
            return f"{cleaned[:2]} {cleaned[2:4]} {cleaned[4:6]} {cleaned[6:9]}"
        elif len(cleaned) == 10:
            return f"{cleaned[:2]} {cleaned[2:4]} {cleaned[4:6]} {cleaned[6:8]} {cleaned[8:10]}"
        
        return self.telephone
    
    def get_call_link(self):
        """Retourne le lien pour appeler le numéro"""
        if not self.telephone:
            return ""
        
        # Nettoyer le numéro de tous les caractères non numériques
        cleaned_number = re.sub(r'\D', '', str(self.telephone))
        
        # Si le numéro ne commence pas par +, l'ajouter
        if cleaned_number and not cleaned_number.startswith('+'):
            # Vérifier s'il s'agit d'un numéro local (commence par 0)
            if cleaned_number.startswith('0'):
                cleaned_number = cleaned_number[1:]
            
            # Ajouter l'indicatif par défaut si nécessaire
            cleaned_number = '+' + cleaned_number
        
        return f"tel:{cleaned_number}"
    
    def clean(self):
        """Validation du modèle"""
        super().clean()
        if self.telephone:
            # S'assurer que le téléphone contient au moins quelques chiffres
            digits = re.sub(r'\D', '', self.telephone)
            if len(digits) < 6:
                raise ValidationError({
                    'telephone': _("Le numéro de téléphone doit contenir au moins 6 chiffres.")
                })


class AdresseAcheteur(Model):
    """Modele metier: AdresseAcheteur."""
    
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
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="adresses_created",
    )
    updated_by = models.ForeignKey(
        "User",
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
    """Modele metier: PortableAcheteur."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    portable = models.TextField(max_length=100, verbose_name=_("Numéro portable"), help_text=_("Format: +241 XX XX XX XX ou 0X XX XX XX"))
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
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="portable_user_create",
    )
    updated_by = models.ForeignKey(
        "User",
        related_name="portable_user_update",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    def clean(self):
        """Validation du numéro de portable - VERSION AVEC DEBUG"""
        super().clean()
        
        import re
        
        print(f"DEBUG clean() - portable: {self.portable}")
        print(f"DEBUG clean() - acheteur: {self.acheteur}")
        print(f"DEBUG clean() - created_by: {self.created_by}")
        print(f"DEBUG clean() - type created_by: {type(self.created_by)}")
        
        if not self.portable:
            raise ValidationError({'portable': _("Le numéro de portable est requis.")})
        
        # Nettoyer le numéro
        cleaned = re.sub(r'\D', '', self.portable)
        
        # Validation de base
        if len(cleaned) < 8:
            raise ValidationError({
                'portable': _("Le numéro de portable doit contenir au moins 8 chiffres.")
            })
        
        if len(cleaned) > 15:
            raise ValidationError({
                'portable': _("Le numéro de portable ne peut pas dépasser 15 chiffres.")
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Valider avant de sauvegarder
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.portable} - {self.acheteur.nom}"
    
    def get_formatted_number(self):
        """Retourne le numéro formaté pour l'affichage - VERSION AMÉLIORÉE"""
        import re
        
        cleaned = re.sub(r'\D', '', self.portable)
        
        # Format selon la longueur et le préfixe
        if cleaned.startswith(('241', '225', '223')) and len(cleaned) == 11:
            # Format international: +XXX XX XX XX XX
            return f"+{cleaned[:3]} {cleaned[3:5]} {cleaned[5:7]} {cleaned[7:9]} {cleaned[9:11]}"
        elif cleaned.startswith('0') and len(cleaned) == 9:
            # Format local: 0X XX XX XX
            return f"{cleaned[0:2]} {cleaned[2:4]} {cleaned[4:6]} {cleaned[6:8]} {cleaned[8:9]}"
        elif len(cleaned) >= 10:
            # Format générique pour les longs numéros
            if cleaned.startswith('1') and len(cleaned) == 11:  # USA/Canada
                return f"+{cleaned[0]} ({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:11]}"
            else:
                # Groupement par 2 ou 3 chiffres
                formatted = ''
                if cleaned.startswith('+'):
                    formatted = '+'
                    cleaned = cleaned[1:]
                
                while len(cleaned) > 0:
                    if len(cleaned) >= 3:
                        formatted += cleaned[:3] + ' '
                        cleaned = cleaned[3:]
                    else:
                        formatted += cleaned + ' '
                        cleaned = ''
                
                return formatted.strip()
        
        # Retourner le numéro original si aucun format ne correspond
        return self.portable
    
    def get_call_link(self):
        """Retourne le lien pour appeler le numéro"""
        if not self.portable:
            return ""
        
        # Nettoyer le numéro de tous les caractères non numériques
        cleaned_number = re.sub(r'\D', '', str(self.portable))
        
        # Si le numéro ne commence pas par +, l'ajouter
        if cleaned_number and not cleaned_number.startswith('+'):
            # Vérifier s'il s'agit d'un numéro local (commence par 0)
            if cleaned_number.startswith('0'):
                # Supprimer le 0 initial pour certains pays
                cleaned_number = cleaned_number[1:]
            
            # Ajouter l'indicatif par défaut si nécessaire
            # (ajuster selon vos besoins)
            cleaned_number = '+' + cleaned_number
        
        return f"tel:{cleaned_number}"
    
    def get_whatsapp_link(self):
        """Retourne le lien WhatsApp"""
        if not self.portable:
            return ""
        
        # Nettoyer le numéro de tous les caractères non numériques
        cleaned_number = re.sub(r'\D', '', str(self.portable))
        
        # WhatsApp nécessite un format international sans le +
        return f"https://wa.me/{cleaned_number}"

    class Meta:
        verbose_name = _("Portable d'Acheteur")
        verbose_name_plural = _("Portables d'Acheteurs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['acheteur']),
            models.Index(fields=['created_at']),
            models.Index(fields=['portable']),
        ]
        unique_together = [['acheteur', 'portable']]  # Empêche les doublons pour le même acheteur


class EmailAcheteur(Model):
    """Modele metier: EmailAcheteur."""
    
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
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="email_user_create",
    )
    updated_by = models.ForeignKey(
        "User",
        related_name="email_user_update",
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
    
    def get_mailto_link(self):
        """Retourne le lien mailto: pour l'email"""
        if not self.email:
            return ""
        return f"mailto:{self.email}"
    
    def get_display_email(self):
        """Retourne l'email formaté pour l'affichage"""
        if not self.email:
            return ""
        
        # Pour les longs emails, on peut tronquer l'affichage
        email = self.email.strip().lower()
        if len(email) > 30:
            # Garder le début et la fin pour l'affichage
            local_part, domain = email.split('@')
            if len(local_part) > 15:
                local_part = local_part[:12] + '...'
            return f"{local_part}@{domain}"
        return email
    
    def clean(self):
        """Validation du modèle"""
        super().clean()
        
        if self.email:
            # Normaliser l'email
            self.email = self.email.strip().lower()
            
            # Vérifier la longueur
            if len(self.email) > 254:
                raise ValidationError({
                    'email': _("L'adresse email ne peut pas dépasser 254 caractères.")
                })
            
            # Vérifier le format
            try:
                validate_email(self.email)
            except DjangoValidationError:
                raise ValidationError({
                    'email': _("Adresse email invalide.")
                })


class Document(Model):
    """Modele metier: Document."""
    
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
    created_by = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="documents_created",
    )
    updated_by = models.ForeignKey(
        "User",
        related_name="documents_updated",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    def __str__(self):
        return f"{self.titre} - {self.acheteur.nom}"


class Swot(Model):
    """Modele metier: Swot."""
    
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

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="swots_created",
    )
    updated_by = models.ForeignKey(
        "User",
        related_name="swots_updated",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("SWOT")
        verbose_name_plural = _("SWOT")

    def __str__(self):
        return f"SWOT de {self.acheteur.nom}"


class ProduitService(Model):
    """Modele metier: ProduitService."""
    
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

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_produits_services',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_produits_services',
        verbose_name=_("Mis à jour par")
    )


    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Produit & Service")
        verbose_name_plural = _("Produits & Services")

    def __str__(self):
        return f"Produits & Services de {self.acheteur.nom}"


class Marque(Model):
    """Modele metier: Marque."""
    
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

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_marques',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_marques',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Marque")
        verbose_name_plural = _("Marques")

    def __str__(self):
        return f"Marque de {self.acheteur.nom}"


class ProcedureCollective(Model):
    """Modele metier: ProcedureCollective."""
    
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
    tribunal = models.CharField(
        _("Tribunal compétent"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom du tribunal compétent"),
    )
    numero_dossier = models.CharField(
        _("Numéro de dossier"),
        max_length=100,
        null=True,
        blank=True,
        help_text=_("Référence officielle du dossier"),
    )
    secteur_activite = models.CharField(
        _("Secteur d'activité"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Secteur d'activité de l'entreprise concernée"),
    )
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description détaillée de la procédure collective"),
    )
    montant_creance = models.DecimalField(
        _("Montant total des créances déclarées"),
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Montant en FCFA"),
    )
    impact_assureur = models.TextField(
        _("Impact pour l’assureur crédit"),
        null=True,
        blank=True,
        help_text=_("Résumé de l’impact et des mesures prises par l’assureur crédit"),
    )

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="procedures_collectives_created",
    )
    updated_by = models.ForeignKey(
        "User",
        related_name="procedures_collectives_updated",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Procédure Collective")
        verbose_name_plural = _("Procédures Collectives")

    def __str__(self):
        return f"{self.type_procedure} - {self.acheteur.nom if self.acheteur else ''}"


class RegistreCommerce(Model):
    """Modele metier: RegistreCommerce."""
    
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
    est_actif = models.BooleanField(
        _("Registre actif"),
        default=False,
        help_text=_("Indique si ce registre de commerce est celui actuellement en vigueur"),
    )

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_registres_commerce',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_registres_commerce',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Registre de Commerce")
        verbose_name_plural = _("Registres de Commerce")

    def __str__(self):
        return f"Registre de commerce de {self.acheteur.nom}"


class Cotisation(Model):
    """Modele metier: Cotisation."""
    
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

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_cotisations_sociales',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_cotisations_sociales',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Cotisation Sociale")
        verbose_name_plural = _("Cotisations Sociales")

    def __str__(self):
        return f"Cotisations Sociales de {self.acheteur.nom}"


class CodeNaceAcheteur(Model):
    """Modele metier: CodeNaceAcheteur."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="codes_nace",
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
    created_by = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="codes_naces_created",
    )
    updated_by = models.ForeignKey(
        "User",
        related_name="codes_naces_updated",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()


    class Meta:
        verbose_name = _("Code NACE Acheteur")
        verbose_name_plural = _("Codes NACE Acheteur")

    def __str__(self):
        return f"Code NACE de {self.acheteur.nom}"



class CodeNafAcheteur(Model):
    """Modele metier: CodeNafAcheteur."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="codes_naf",
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
    created_by = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="codes_nafs_created",
    )
    updated_by = models.ForeignKey(
        "User",
        related_name="codes_nafs_updated",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
    )

    history = HistoricalRecords()

    def __str__(self):
        return f"Code NAF de {self.acheteur.nom}"


    class Meta:
        verbose_name = _("Code NAF Acheteur")
        verbose_name_plural = _("Codes NAF Acheteur")


# Tables supplementaires

# Assuming you already have an Acheteur model defined elsewhere
# For example:
# class Acheteur(Model):
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    

class Certification(Model):
    """Modele metier: Certification."""
    
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

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_certifications',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_certifications',
        verbose_name=_("Mis à jour par")
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
    """Modele metier: InnovationDeveloppement."""
    
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

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_innovations_developpements',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_innovations_developpements',
        verbose_name=_("Mis à jour par")
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
    """Modele metier: StrategiePlanification."""
    
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

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur Commentaire"),
    )
    commentaire = models.TextField(_("Commentaire"), blank=True, max_length=10000000)

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_strategies_planifications',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_strategies_planifications',
        verbose_name=_("Mis à jour par")
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
    """Modele metier: ConformiteReglementation."""
    
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

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_conformites_reglementations',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_conformites_reglementations',
        verbose_name=_("Mis à jour par")
    )

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
# Debut Modules KBZ
##########################################################
##########################################################
class Structure(Model):
    """Modele metier: Structure."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    nom = models.CharField(
        _("Nom"), 
        max_length=200, 
        blank=True,
        null=True  # AJOUTER pour compatibilité
    )

    type_affiliation = models.CharField(
        max_length=100,
        choices=LIEN_ENTREPRISE_CHOICE,
        blank=True,
        verbose_name=_("Type d'affiliation"),
    )
    
    numero_adresse = models.CharField(
        _("Numéro adresse"), 
        max_length=200, 
        blank=True,
        null=True  # AJOUTER pour compatibilité
    )
    rue_adresse = models.CharField(
        _("Rue adresse"), 
        max_length=200, 
        blank=True,
        null=True  # AJOUTER pour compatibilité
    )
    code_postale_adresse = models.CharField(
        _("Code postal adresse"), 
        max_length=200, 
        blank=True,
        null=True  # AJOUTER pour compatibilité
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire"),
    )
    commentaire = models.TextField(
        _("Commentaire"), 
        blank=True, 
        max_length=10000000,
        null=True  # AJOUTER pour compatibilité
    )

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='structure_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='structure_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    def __str__(self):
        return self.nom or _("Filiale sans nom")

    class Meta:
        verbose_name = _("Filiale ou Branche")
        verbose_name_plural = _("Filiales ou Branches")


class AnalyseSectorielle(Model):
    """Modele metier: AnalyseSectorielle."""
    
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
    commentaire = models.TextField(_("Commentaire"), max_length=10000000, blank=True, null=True)
    impact_covid_19 = models.TextField(
        _("Impact COVID-19"), max_length=10000000, blank=True, null=True
    )

    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analyse_sectorielle_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analyse_sectorielle_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    def __str__(self):
        return _("Analyse sectorielle")

    class Meta:
        verbose_name = _("Analyse Sectorielle")
        verbose_name_plural = _("Analyses Sectorielles")


class CompteFinancier(Model):
    """Modele metier: CompteFinancier."""
    
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
    
    OUI = 'OUI'
    NON = 'NON'
    
    # Choix OUI/NON
    STATUS__OUI_NON = (
        (OUI, _('Oui')),
        (NON, _('Non')),
    )

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
    
    LIEN_TYPE_BILAN_CHOICE = (
        (gettext_lazy("Classique"), gettext_lazy("Classique")),
        (gettext_lazy("Syscohada"), gettext_lazy("Syscohada")),
        (gettext_lazy("Anglais"), gettext_lazy("Anglais")),
        (gettext_lazy("Bancaire"), gettext_lazy("Bancaire")),
    )

    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    cabinet = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("Cabinet"))
    requis_pour_deposer = models.CharField(
        max_length=200, blank=True, null=True, verbose_name=_("Requis pour déposer")
    )
    credibilite_cabinet = models.CharField(
        max_length=200,
        blank=True, 
        null=True,
        choices=STATUS__OUI_NON,
        verbose_name=_("Crédibilité du cabinet pour ACREMAC"),
    )
    source = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("Source"))
    presentation = models.CharField(
        max_length=200, blank=True, null=True, verbose_name=_("Présentation")
    )

    date_compte = models.DateField(
        blank=True, null=True, verbose_name=_("Début de période de compte N")
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
        null=True,
        verbose_name=_("Devise"),
    )
    type_bilan = models.CharField(
        max_length=255,
        choices=LIEN_TYPE_BILAN_CHOICE,
        default='',  # CORRIGER : utiliser une valeur vide
        null=True,
        verbose_name=_("Type de bilan"),
    )
   

    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire"),
    )
    commentaire = models.TextField(
        blank=True, null=True, max_length=10000000, verbose_name=_("Commentaire")
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comptefinancier_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comptefinancier_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            f"{self.acheteur} - {self.cabinet}"
            if self.acheteur
            else _("Compte Financier")
        )
        
    def est_rempli(self):
        champs_significatifs = [
            self.cabinet,
            self.requis_pour_deposer,
            self.credibilite_cabinet,
            self.source,
            self.presentation,
            self.type_compte,
            self.devise,
            self.acheteur,
            self.type_bilan,
            self.commentaire
        ]
        rempli = any(bool(champ) for champ in champs_significatifs)

        couple_n = self.date_compte and self.date_fin
        couple_n1 = self.date_compte_n_moins_un and self.date_fin_n_moins_un
        couple_n2 = self.date_compte_n_moins_deux and self.date_fin_n_moins_deux
        return rempli and (couple_n or couple_n1 or couple_n2)
    
    def get_periodes_remplies(self):
        """Retourne les périodes de compte remplies"""
        periodes = []
        
        if self.date_compte and self.date_fin:
            periodes.append({
                'periode': 'N',
                'debut': self.date_compte,
                'fin': self.date_fin,
                'complete': True
            })
        
        if self.date_compte_n_moins_un and self.date_fin_n_moins_un:
            periodes.append({
                'periode': 'N-1',
                'debut': self.date_compte_n_moins_un,
                'fin': self.date_fin_n_moins_un,
                'complete': True
            })
        
        if self.date_compte_n_moins_deux and self.date_fin_n_moins_deux:
            periodes.append({
                'periode': 'N-2',
                'debut': self.date_compte_n_moins_deux,
                'fin': self.date_fin_n_moins_deux,
                'complete': True
            })
        
        return periodes
    
    def get_completion_rate(self):
        """Retourne le taux de complétion en pourcentage"""
        champs_obligatoires = [
            self.cabinet,
            self.date_compte,
            self.date_fin,
            self.devise,
            self.acheteur
        ]
        
        remplis = sum(1 for champ in champs_obligatoires if champ)
        total = len(champs_obligatoires)
        
        return round((remplis / total) * 100, 1) if total > 0 else 0

    class Meta:
        verbose_name = _("Compte Financier")
        verbose_name_plural = _("Comptes Financiers")


class OperationEtHistorique(Model):
    """Modele metier: OperationEtHistorique."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    commentaire_ratios = models.CharField(
        max_length=10000000,  # Longueur très grande pour un CharField
        blank=True,
        null=True,  # AJOUTER pour compatibilité
        verbose_name=_("Commentaire sur les ratios")
    )

    description_complete_activite = models.CharField(
        max_length=10000000,
        blank=True,
        null=True,  # AJOUTER pour compatibilité
        verbose_name=_("Description complète de l'activité")
    )
    importation = models.ManyToManyField("ListeImportation", related_name=_("importation"), blank=True)
    historique = models.TextField(blank=True, null=True, verbose_name=_("Historique"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_historique_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_historique_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    def __str__(self):
        return (
            f"{self.acheteur} - {self.description_complete_activite[:50]}..."
            if self.acheteur
            else _("Opération et Historique")
        )
        
    def get_importation_display(self):
        """Retourne la liste des importations sous forme de chaîne"""
        importations = self.importation.all()
        if importations:
            return ", ".join([str(imp) for imp in importations])
        return _("Aucune")
    get_importation_display.short_description = _('Importations')
    
    def has_content(self):
        """Vérifie si le modèle a du contenu"""
        return any([
            bool(self.commentaire_ratios and self.commentaire_ratios.strip()),
            bool(self.description_complete_activite and self.description_complete_activite.strip()),
            bool(self.historique and self.historique.strip()),
            self.importation.exists()
        ])
    
    def get_summary(self):
        """Retourne un résumé du contenu"""
        return {
            'has_commentaire_ratios': bool(self.commentaire_ratios and self.commentaire_ratios.strip()),
            'has_description': bool(self.description_complete_activite and self.description_complete_activite.strip()),
            'has_historique': bool(self.historique and self.historique.strip()),
            'has_importations': self.importation.exists(),
            'importations_count': self.importation.count(),
            'description_length': len(self.description_complete_activite) if self.description_complete_activite else 0,
            'historique_length': len(self.historique) if self.historique else 0,
        }

    class Meta:
        verbose_name = _("Opération et Historique")
        verbose_name_plural = _("Opérations et Historiques")


class ProprieteEtActif(Model):
    """Modele metier: ProprieteEtActif."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    locaux = models.ManyToManyField("Locaux", related_name=_("Locaux"), blank=True) # ERREUR : ne pas utiliser _() pour related_name
    

    branche = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Branche"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='propriete_action_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='propriete_action_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    def __str__(self):
        if self.acheteur and self.branche:
            return f"{self.acheteur} - {self.branche}"
        elif self.acheteur:
            return f"{self.acheteur} - Propriétés et Actifs"
        else:
            return _("Propriété et Actif")
    
    def get_locaux_display(self):
        """Retourne la liste des locaux sous forme de chaîne"""
        locaux_list = self.locaux.all()
        if locaux_list:
            return ", ".join([str(local) for local in locaux_list])
        return _("Aucun")
    get_locaux_display.short_description = _('Locaux')
    
    def has_locaux(self):
        """Vérifie si des locaux sont associés"""
        return self.locaux.exists()
    
    def get_locaux_count(self):
        """Retourne le nombre de locaux"""
        return self.locaux.count()
    
    def get_summary(self):
        """Retourne un résumé des propriétés et actifs"""
        return {
            'has_branche': bool(self.branche and self.branche.strip()),
            'has_locaux': self.has_locaux(),
            'locaux_count': self.get_locaux_count(),
            'branche': self.branche or _("Non spécifié"),
        }

    class Meta:
        verbose_name = _("Propriété et Actif")
        verbose_name_plural = _("Propriétés et Actifs")


class ConditionAchat(Model):
    """Modele metier: ConditionAchat."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    local = models.ManyToManyField("ListeConditionAchat", related_name=_("local"), blank=True)  # Enlevez null=True
    importation = models.ManyToManyField("ListeConditionAchat", related_name=_("importation"), blank=True)  # Enlevez null=True
    les_clients = models.TextField(blank=True, null=True, verbose_name=_("Les clients"))
    fournisseur = models.TextField(blank=True, null=True, verbose_name=_("Fournisseur"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='condition_achat_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='condition_achat_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    def __str__(self):
        if self.acheteur:
            local_count = self.local.count()
            import_count = self.importation.count()
            return f"{self.acheteur} - {local_count} local, {import_count} import"
        return _("Conditions d'achat")
    
    def get_local_display(self):
        """Retourne la liste des conditions locales sous forme de chaîne"""
        local_items = self.local.all()
        if local_items:
            return ", ".join([str(item) for item in local_items])
        return _("Aucune condition locale")
    get_local_display.short_description = _('Conditions Locales')
    
    def get_importation_display(self):
        """Retourne la liste des conditions d'importation sous forme de chaîne"""
        import_items = self.importation.all()
        if import_items:
            return ", ".join([str(item) for item in import_items])
        return _("Aucune condition d'importation")
    get_importation_display.short_description = _('Conditions Importation')
    
    def has_clients_info(self):
        """Vérifie si des informations clients sont renseignées"""
        return bool(self.les_clients and self.les_clients.strip())
    
    def has_fournisseurs_info(self):
        """Vérifie si des informations fournisseurs sont renseignées"""
        return bool(self.fournisseur and self.fournisseur.strip())
    
    def get_summary(self):
        """Retourne un résumé des conditions d'achat"""
        return {
            'local_count': self.local.count(),
            'importation_count': self.importation.count(),
            'has_clients': self.has_clients_info(),
            'has_fournisseurs': self.has_fournisseurs_info(),
            'clients_length': len(self.les_clients) if self.les_clients else 0,
            'fournisseurs_length': len(self.fournisseur) if self.fournisseur else 0,
        }
    
    def is_complete(self, min_conditions=1):
        """Vérifie si les conditions d'achat sont suffisamment remplies"""
        conditions_count = self.local.count() + self.importation.count()
        has_text_info = self.has_clients_info() or self.has_fournisseurs_info()
        
        return conditions_count >= min_conditions or has_text_info

    class Meta:
        verbose_name = _("Condition d'Achat")
        verbose_name_plural = _("Conditions d'Achat")


class ConditionDeVente(Model):
    """Modele metier: ConditionDeVente."""
    
    LIEN_TYPE_RAPPORT_CHOICE_DEFAUT = '--------'
    
    LIEN_COMPORTEMENT_PAIEMENT_CHOICE = (
        (LIEN_TYPE_RAPPORT_CHOICE_DEFAUT, LIEN_TYPE_RAPPORT_CHOICE_DEFAUT),
        (gettext_lazy('En Avance'), gettext_lazy('En Avance')),
        (gettext_lazy('En Temps et en heure'), gettext_lazy('En Temps et en heure')),
        (gettext_lazy('En Retard'), gettext_lazy('En Retard')),
        (gettext_lazy('Normal'), gettext_lazy('Normal')),
        (gettext_lazy('Mauvais payeur'), gettext_lazy('Mauvais payeur')),
        (gettext_lazy('Plainte isolée'), gettext_lazy('Plainte isolée')),
        (gettext_lazy("Inconnu de nos sources"), gettext_lazy("Inconnu de nos sources")),
        (gettext_lazy(
            "En raison des informations sur les procédures d'insolvabilité/préliminaires/réglementaires, ACREMAC n'est pas en mesure de donner une évaluation finale du comportement de paiement de l'entreprise à ce stade"),
        gettext_lazy(
            "En raison des informations sur les procédures d'insolvabilité/préliminaires/réglementaires, ACREMAC n'est pas en mesure de donner une évaluation finale du comportement de paiement de l'entreprise à ce stade")),
        (gettext_lazy("Aucune expérience de paiement d'une quelconque importance n'est disponible"),
        gettext_lazy("Aucune expérience de paiement d'une quelconque importance n'est disponible")),

    )
    
    LIEN_COMPORTEMENT_JUGEMENT_CHOICE = (
        (LIEN_TYPE_RAPPORT_CHOICE_DEFAUT, LIEN_TYPE_RAPPORT_CHOICE_DEFAUT),

        # (gettext_lazy("En raison des informations sur les procédures d'insolvabilité/préliminaires/réglementaires, ACREMAC n'est pas en mesure de donner une évaluation finale du comportement de paiement de l'entreprise à ce stade"),gettext_lazy("En raison des informations sur les procédures d'insolvabilité/préliminaires/réglementaires, ACREMAC n'est pas en mesure de donner une évaluation finale du comportement de paiement de l'entreprise à ce stade")),
        # (gettext_lazy("Aucune expérience de paiement d'une quelconque importance n'est disponible"),gettext_lazy("Aucune expérience de paiement d'une quelconque importance n'est disponible")),
        (gettext_lazy("Aucune information négative n'a été trouvée"),
        gettext_lazy("Aucune information négative n'a été trouvée")),
        (gettext_lazy(
            "Il n'existe aucune trace d'une quelconque action de recouvrement de créances par ACREMAC à l'encontre de cette entreprise"),
        gettext_lazy(
            "Il n'existe aucune trace d'une quelconque action de recouvrement de créances par ACREMAC à l'encontre de cette entreprise")),
        (gettext_lazy(
            "Selon nos sources, l'entreprise n'est pas en situation d'insolvabilité/procédure préliminaire/procédure de répartition des dettes"),
        gettext_lazy(
            "Selon nos sources, l'entreprise n'est pas en situation d'insolvabilité/procédure préliminaire/procédure de répartition des dettes")),
        (gettext_lazy("Des actions en recouvrement judiciaire sont ouvertes contre l'acheteur"),
        gettext_lazy("Des actions en recouvrement judiciaire sont ouvertes contre l'acheteur")),
        (gettext_lazy("Des actions de recouvrement à l'amiable sont ouvertes contre l'acheteur"),
        gettext_lazy("Des actions de recouvrement à l'amiable sont ouvertes contre l'acheteur")),
        (gettext_lazy("Des cas de recouvrement fermés existent chez nos sources sur l'acheteur"), gettext_lazy("Des cas de recouvrement fermés existent chez nos sources sur l'acheteur")),
        (gettext_lazy("Inconnu de nos sources"), gettext_lazy("Inconnu de nos sources")),

    )
   
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    local = models.ManyToManyField("ListeConditionVente", related_name=_("local"), blank=True)  # Enlevez null=True

    recouvrement_de_dette_jugement = models.CharField(
        max_length=255,
        choices=LIEN_COMPORTEMENT_JUGEMENT_CHOICE,
        default='',  # CORRIGER : utiliser une valeur vide
        blank=True,  # AJOUTER : pour permettre champ vide
        verbose_name=_("Recouvrement de dette jugement"),
    )

    comportement_de_paiement = models.CharField(
        max_length=255,
        choices=LIEN_COMPORTEMENT_PAIEMENT_CHOICE,
        default='',  # CORRIGER : utiliser une valeur vide
        blank=True,  # AJOUTER : pour permettre champ vide
        verbose_name=_("Comportement de paiement"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='condition_vente_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='condition_vente_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    def __str__(self):
        if self.acheteur:
            local_count = self.local.count()
            return f"Conditions vente - {self.acheteur} ({local_count} conditions)"
        return _("Conditions de vente")
    
    def get_local_display(self):
        """Retourne la liste des conditions locales sous forme de chaîne"""
        local_items = self.local.all()
        if local_items:
            return ", ".join([str(item) for item in local_items])
        return _("Aucune condition locale")
    get_local_display.short_description = _('Conditions Locales de Vente')
    
    def get_jugement_display_full(self):
        """Retourne l'affichage complet du recouvrement/jugement"""
        if self.recouvrement_de_dette_jugement:
            return dict(self.LIEN_COMPORTEMENT_JUGEMENT_CHOICE).get(
                self.recouvrement_de_dette_jugement, 
                self.recouvrement_de_dette_jugement
            )
        return _("Non spécifié")
    
    def get_paiement_display_full(self):
        """Retourne l'affichage complet du comportement de paiement"""
        if self.comportement_de_paiement:
            return dict(self.LIEN_COMPORTEMENT_PAIEMENT_CHOICE).get(
                self.comportement_de_paiement,
                self.comportement_de_paiement
            )
        return _("Non spécifié")
    
    def get_summary(self):
        """Retourne un résumé des conditions de vente"""
        return {
            'local_count': self.local.count(),
            'has_jugement': bool(self.recouvrement_de_dette_jugement),
            'has_paiement': bool(self.comportement_de_paiement),
            'jugement': self.get_jugement_display_full(),
            'paiement': self.get_paiement_display_full(),
        }
    
    def is_complete(self):
        """Vérifie si les conditions de vente sont suffisamment remplies"""
        return any([
            self.local.exists(),
            bool(self.recouvrement_de_dette_jugement),
            bool(self.comportement_de_paiement),
        ])

    class Meta:
        verbose_name = _("Condition de Vente")
        verbose_name_plural = _("Conditions de Vente")


class SommaireEtAvis(Model):
    """Modele metier: SommaireEtAvis."""
    
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
        verbose_name=_("Couleur commentaire"),
    )
    commentaire = models.TextField(
        max_length=10000000, blank=True, verbose_name=_("Commentaire"), null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sommaire_avis_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sommaire_avis_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    def __str__(self):
        if self.acheteur:
            return f"Sommaire et avis - {self.acheteur}"
        return _("Sommaire et avis")
    
    def has_commentaire(self):
        """Vérifie si un commentaire existe"""
        return bool(self.commentaire and self.commentaire.strip())
    
    def get_commentaire_preview(self, length=100):
        """Retourne un aperçu du commentaire"""
        if self.commentaire and self.commentaire.strip():
            comment = self.commentaire.strip()
            if len(comment) > length:
                return comment[:length] + "..."
            return comment
        return _("Aucun commentaire")
    
    def get_couleur_display(self):
        """Retourne la couleur du commentaire ou une valeur par défaut"""
        if self.couleur_commentaire:
            return str(self.couleur_commentaire)
        return _("Non spécifié")
    
    def get_summary(self):
        """Retourne un résumé du sommaire et avis"""
        return {
            'has_commentaire': self.has_commentaire(),
            'has_couleur': self.couleur_commentaire is not None,
            'commentaire_length': len(self.commentaire) if self.commentaire else 0,
            'commentaire_preview': self.get_commentaire_preview(),
            'couleur': self.get_couleur_display(),
        }
    
    def is_complete(self):
        """Vérifie si le sommaire est suffisamment rempli"""
        return self.has_commentaire() or self.couleur_commentaire is not None

    class Meta:
        verbose_name = _("Sommaire et Avis")
        verbose_name_plural = _("Sommaires et Avis")


class Advice(Model):
    """Modele metier: Advice."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur", on_delete=models.DO_NOTHING, verbose_name=_("Acheteur")
    )
    
    points_forts = models.TextField(
        max_length=10000000, blank=True, null=True, verbose_name=_("Points forts")
    )
    points_faibles = models.TextField(
        max_length=10000000, blank=True, null=True, verbose_name=_("Points faibles")
    )
    
    dynamisme_court_terme = models.TextField(
        max_length=10000000, blank=True, null=True, verbose_name=_("Dynamisme à court terme")
    )
    dynamisme_long_terme = models.TextField(
        max_length=10000000, blank=True, null=True, verbose_name=_("Dynamisme à long terme")
    )
    risque_potentiel_court_terme = models.TextField(max_length=10000000, blank=True, null=True, verbose_name=_("Risques potentiels à court terme"))
    
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='advice_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='advice_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    def __str__(self):
        return f"Conseils - {self.acheteur}" if self.acheteur else _("Conseils sans acheteur")
    
    def get_summary(self):
        """Retourne un résumé des conseils"""
        return {
            'has_points_forts': bool(self.points_forts and self.points_forts.strip()),
            'has_points_faibles': bool(self.points_faibles and self.points_faibles.strip()),
            'has_dynamisme_court_terme': bool(self.dynamisme_court_terme and self.dynamisme_court_terme.strip()),
            'has_dynamisme_long_terme': bool(self.dynamisme_long_terme and self.dynamisme_long_terme.strip()),
            'has_risque_court_terme': bool(self.risque_potentiel_court_terme and self.risque_potentiel_court_terme.strip()),
            'points_forts_length': len(self.points_forts) if self.points_forts else 0,
            'points_faibles_length': len(self.points_faibles) if self.points_faibles else 0,
        }
    
    def is_complete(self, threshold=50):
        """Vérifie si les conseils sont suffisamment complets"""
        summary = self.get_summary()
        
        # Compter les champs remplis
        filled_fields = sum([
            1 for key, value in summary.items() 
            if key.startswith('has_') and value
        ])
        
        # 5 champs possibles (points_forts, points_faibles, dynamisme_court_terme, 
        # dynamisme_long_terme, risque_potentiel_court_terme)
        total_fields = 5
        
        # Calculer le pourcentage de complétion
        completion_rate = (filled_fields / total_fields) * 100
        
        return completion_rate >= threshold
    
    def get_completion_rate(self):
        """Retourne le taux de complétion en pourcentage"""
        summary = self.get_summary()
        filled_fields = sum([
            1 for key, value in summary.items() 
            if key.startswith('has_') and value
        ])
        total_fields = 5
        return round((filled_fields / total_fields) * 100, 1)

    class Meta:
        verbose_name = _("Conseil")
        verbose_name_plural = _("Conseils")


class Geopolitics(Model):
    """Modele metier: Geopolitics."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur", on_delete=models.DO_NOTHING, verbose_name=_("Acheteur")
    )
    
    stabilite_politique = models.CharField(
        max_length=4, 
        blank=True, 
        null=True, 
        verbose_name=_('Stabilité politique'),
        help_text=_("Score de 0 à 10: 0=Très instable, 5=Moyen, 10=Très stable")
    )
    
    etat_droit = models.CharField(
        max_length=4, 
        blank=True, 
        null=True, 
        verbose_name=_('Etat de droit'),
        help_text=_("Score de 0 à 10: 0=Faible, 5=Moyen, 10=Forte application de la loi")
    )
    
    efficacite = models.CharField(
        max_length=4, 
        blank=True, 
        null=True, 
        verbose_name=_('Efficacité gouvernementale'),
        help_text=_("Score de 0 à 10: 0=Très inefficace, 5=Moyen, 10=Très efficace")
    )
    
    qualite = models.CharField(
        max_length=4, 
        blank=True, 
        null=True, 
        verbose_name=_('Qualité réglementaire'),
        help_text=_("Score de 0 à 10: 0=Mauvaise, 5=Moyenne, 10=Excellente réglementation")
    )
    
    liberte_expression = models.CharField(
        max_length=4, 
        blank=True, 
        null=True, 
        verbose_name=_("Liberté d'expression"),
        help_text=_("Score de 0 à 10: 0=Très restrictive, 5=Moyenne, 10=Très libre")
    )
    
    donnees_politiques = models.TextField(
        max_length=10000000, blank=True, null=True, verbose_name=_("Données politiques")
    )
    donnees_economiques = models.TextField(
        max_length=10000000, blank=True, null=True, verbose_name=_("Données économiques")
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='geopolitique_user_create',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='geopolitique_user_update',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    def __str__(self):
        return f"Geopolitics for {self.acheteur}"
    
    def get_average_score(self):
        """Calcule le score moyen des indicateurs"""
        scores = []
        score_fields = [
            self.stabilite_politique,
            self.etat_droit,
            self.efficacite,
            self.qualite,
            self.liberte_expression
        ]
        
        for score in score_fields:
            if score and score.isdigit():
                scores.append(int(score))
        
        if scores:
            return round(sum(scores) / len(scores), 1)
        return 0

    class Meta:
        verbose_name = _("Geopolitique")
        verbose_name_plural = _("Géopolitiques")
        


class Scoring(SafeDeleteModel):  # Changez Model en SafeDeleteModel
    """Modele metier: Scoring."""
    _safedelete_policy = SOFT_DELETE_CASCADE

    annee = models.ForeignKey(
        "Annee",
        on_delete=models.DO_NOTHING,
        verbose_name=_("Année"),
        null=True,
        blank=True,
    )

    acheteur = models.ForeignKey(
        "Acheteur",
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
        null=True,
        blank=True,
    )

    score = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        verbose_name=_("Score"),
        db_index=True,
        help_text=_("Score sur 4 caractères maximum"),
    )

    commentaire = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Commentaire"),
        max_length=10000000,
        help_text=_("Commentaire détaillé sur le scoring"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
        verbose_name=_("Date de création"),
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        verbose_name=_("Date de mise à jour"),
    )

    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scoring_user_create",
        verbose_name=_("Créé par"),
    )

    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scoring_user_update",
        verbose_name=_("Mis à jour par"),
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("Scoring")
        verbose_name_plural = _("Scorings")
        ordering = ("-created_at",)
        unique_together = ("annee", "acheteur")  # Gardez cette contrainte
        indexes = [
            models.Index(fields=["annee", "acheteur"]),
            models.Index(fields=["score"]),
            models.Index(fields=["created_at"]),
        ]
    
    def clean_score(self):
        """Nettoyer et valider le score"""
        if self.score:
            # Nettoyer les espaces
            self.score = str(self.score).strip()
            
            # Valider le format
            import re
            pattern = r'^[A-F][+-]?$|^\d{1,3}(\.\d{1,2})?$'
            if not re.match(pattern, self.score):
                raise ValidationError({
                    'score': _('Format de score invalide. Utilisez un nombre (0-10) ou une note alphabétique (A-F).')
                })
            
            # Si c'est un nombre, s'assurer qu'il est entre 0 et 10
            try:
                score_num = float(self.score)
                if score_num < 0 or score_num > 10:
                    raise ValidationError({
                        'score': _('Le score doit être compris entre 0 et 10')
                    })
            except (ValueError, TypeError):
                pass

    def __str__(self):
        if self.acheteur and self.annee:
            return f"{self.acheteur} - {self.annee} : {self.score or 'N/A'}"
        elif self.acheteur:
            return f"{self.acheteur} : {self.score or 'N/A'}"
        else:
            return f"Scoring : {self.score or 'N/A'}"
    
    def get_score_numeric(self):
        """Retourne le score sous forme numérique si possible"""
        if self.score:
            try:
                # Essayer de convertir en float
                return float(self.score)
            except (ValueError, TypeError):
                pass
        return None
    
    def get_score_category(self):
        """Retourne la catégorie du score"""
        score_num = self.get_score_numeric()
        
        if score_num is None:
            return _("Non évalué")
        
        if score_num >= 8:
            return _("Excellent")
        elif score_num >= 6:
            return _("Bon")
        elif score_num >= 4:
            return _("Moyen")
        elif score_num >= 2:
            return _("Faible")
        else:
            return _("Très faible")
    
    def is_valid_score(self):
        """Vérifie si le score est valide"""
        if not self.score:
            return False
        
        # Vérifier le format (ex: "85", "A+", etc.)
        import re
        # Accepte nombres (avec ou sans décimales) et notes alphabétiques
        pattern = r'^[A-F][+-]?$|^\d{1,3}(\.\d{1,2})?$'
        return bool(re.match(pattern, str(self.score).strip()))
    
    def get_summary(self):
        """Retourne un résumé du scoring"""
        return {
            'annee': str(self.annee) if self.annee else _("Non spécifiée"),
            'acheteur': str(self.acheteur) if self.acheteur else _("Non spécifié"),
            'score': self.score or _("Non spécifié"),
            'score_numeric': self.get_score_numeric(),
            'score_category': self.get_score_category(),
            'has_commentaire': bool(self.commentaire and self.commentaire.strip()),
            'commentaire_length': len(self.commentaire) if self.commentaire else 0,
            'is_valid': self.is_valid_score(),
        }
    
    def clean(self):
        """Validation au niveau modèle"""
        super().clean()
        
        # Validation des champs obligatoires
        if not self.annee:
            raise ValidationError({
                'annee': _('L\'année est obligatoire')
            })
        
        if not self.acheteur:
            raise ValidationError({
                'acheteur': _('L\'acheteur est obligatoire')
            })


class Banquier(Model):
    """Modele metier: Banquier."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    acheteur = models.ForeignKey(
        "Acheteur",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Acheteur"),
    )
    nom_banque = models.CharField(
        blank=True, 
        max_length=200, 
        null=True,  # AJOUTER pour compatibilité
        verbose_name=_("Nom de la banque")
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
    numero = models.CharField(
        max_length=200, 
        blank=True,
        null=True,  # AJOUTER pour compatibilité
        verbose_name=_("Numéro")
    )
    rue = models.CharField(
        max_length=200, 
        blank=True,
        null=True,  # AJOUTER pour compatibilité
        verbose_name=_("Rue")
    )
    ville = models.ForeignKey(
        "Ville", 
        on_delete=models.DO_NOTHING, 
        null=True,  # AJOUTER ABSOLUMENT
        blank=True,  # AJOUTER ABSOLUMENT
        verbose_name=_("Ville")
    )
    code_postal = models.CharField(
        max_length=200, 
        blank=True,
        null=True,  # AJOUTER pour compatibilité
        verbose_name=_("Code postal")
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Couleur du commentaire"),
    )
    commentaire = models.TextField(
        blank=True, 
        max_length=10000000,  # AJOUTER pour compatibilité
        null=True,  # AJOUTER pour compatibilité
        verbose_name=_("Commentaire")
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_create_banquier',
        verbose_name=_("Créé par")
    )
    
    updated_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_update_banquier',
        verbose_name=_("Mis à jour par")
    )

    history = HistoricalRecords()


    def __str__(self):
        return self.nom_banque

    class Meta:
        verbose_name = _("Donnée bancaire")
        verbose_name_plural = _("Données bancaires")
        indexes = [
            models.Index(fields=['acheteur', 'deleted']),
            models.Index(fields=['nom_banque']),
            models.Index(fields=['ville']),
            models.Index(fields=['couleur_commentaire']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]


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
    """Modele metier: ActifA."""
    
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
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Biens, installations et équipements"),
    )
    inventaire = models.DecimalField(
        max_digits=100, decimal_places=2, null=True, blank=True
    )
    creances_commerciales_autres_creances = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Créances commerciales et autres"),
    )
    actif_impots_courant = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Actif d'Impôts courant"),
    )
    caisses_banques = models.DecimalField(
        max_digits=100,
        decimal_places=5,
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

    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
    
    # PROPRIÉTÉS ANALYTIQUES SUPPLEMENTAIRES
    
    @property
    def ratio_liquidite(self):
        """Ratio de liquidité (actifs courants / total actif)."""
        if self.total_actif:
            return float(self.actifs_courants) / float(self.total_actif)
        return 0
    
    @property
    def ratio_tresorerie(self):
        """Ratio de trésorerie (caisse / actifs courants)."""
        if self.actifs_courants and self.caisses_banques:
            return float(self.caisses_banques) / float(self.actifs_courants)
        return 0
    
    @property
    def rotation_stocks(self):
        """Rotation des stocks (inventaire / actifs courants)."""
        if self.actifs_courants and self.inventaire:
            return float(self.inventaire) / float(self.actifs_courants)
        return 0
    
    @property
    def jours_creances_clients(self):
        """Jours de créances clients estimés."""
        # Formule simplifiée : (créances / CA annuel) * 365
        # À adapter avec les données réelles de CA
        return None  # À implémenter avec données supplémentaires
    
    def get_summary(self):
        """Retourne un résumé de l'actif."""
        return {
            'actifs_non_courants': float(self.actifs_non_courants),
            'actifs_courants': float(self.actifs_courants),
            'total_actif': float(self.total_actif),
            'inventaire': float(self.inventaire) if self.inventaire else 0,
            'creances': float(self.creances_commerciales_autres_creances) if self.creances_commerciales_autres_creances else 0,
            'liquidite': float(self.caisses_banques) if self.caisses_banques else 0,
            'ratio_liquidite': self.ratio_liquidite,
            'ratio_tresorerie': self.ratio_tresorerie,
            'rotation_stocks': self.rotation_stocks,
        }


class PassifA(Model):
    """Modele metier: PassifA."""
    
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

    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
    """Modele metier: ResultatA."""
    
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

    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
    """Modele metier: ActifC."""
    
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
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Capital sousc. non app"),
    )
    frais_recherche_developpement = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Frais recherche developpement"),
    )
    brevet_licence_logiciels = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Brevet licence logiciels"),
    )
    fonds_commercial = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Fonds commercial"),
    )
    autres_immobilisations_incorporelles = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres immobilisations incorporelles"),
    )
    terrains = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Terrains"),
    )
    constructions = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Constructions"),
    )
    materiels_et_outils = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Materiels et outils"),
    )
    materiel_de_transport = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Materiel de transport"),
    )
    autres_immos_corp = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres immos corp"),
    )
    immos_en_cours = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Immos en cours"),
    )
    avances_et_acptes = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Avances et acptes"),
    )
    participations = models.DecimalField(
        max_digits=100, decimal_places=5, null=True, blank=True, verbose_name=_("Participations")
    )
    prets = models.DecimalField(
        max_digits=100, decimal_places=5, null=True, blank=True, verbose_name=_("Prets")
    )
    autres = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres"),
    )
    stocks_mp = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Stocks mp"),
    )
    stocks_encours_mp = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Stocks encours mp"),
    )
    stocks_pf = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Stocks pf"),
    )
    stocks_encours_pf = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Stocks encours pf"),
    )
    stocks_encours_services = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Stocks encours services"),
    )
    stocks_mses = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Stocks mses"),
    )
    avances_acptes_verses = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Avances acptes verses"),
    )
    clients_et_cptes_rattaches = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Clients et cptes rattaches"),
    )
    autres_creances = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres creances"),
    )
    valeurs_a_encaisser = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Valeurs a encaisser"),
    )
    banques_cheques_postaux_caisse = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Banques cheques postaux caisse"),
    )
    cca = models.DecimalField(
        max_digits=100, decimal_places=5, null=True, blank=True, verbose_name=_("Cca")
    )
    charges_a_repartir_et_frais_etablissement = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Charges a repartir et frais etablissement"),
    )
    primes_de_rbt = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Primes de rbt"),
    )
    eca = models.DecimalField(
        max_digits=100, decimal_places=5, null=True, blank=True, verbose_name=_("Eca")
    )
    eene = models.DecimalField(
        max_digits=100, decimal_places=5, null=True, blank=True, verbose_name=_("Eene")
    )
    effectif = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Effectif"),
    )
    amortissements = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Amortissements"),
    )
    provisions_stocks = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Provisions stocks"),
    )
    provisions_creances = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Provisions creances"),
    )
    provisions_vmp = models.DecimalField(
        max_digits=100,
        decimal_places=5,
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
    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
    """Modele metier: PassifC."""
    
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
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Capital social"),
    )
    primes = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Primes"),
    )
    ecarts_de_reevaluation = models.DecimalField(
        max_digits=100, decimal_places=2, null=True, blank=True, verbose_name=_("Écarts de réévaluation")
    )
    reserve = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Reserve"),
    )
    report_a_nouveau = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Report a nouveau"),
    )
    resultat_exercice = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Resultat exercice"),
    )
    subv_invest = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Subventions investies"),
    )
    provision_regl = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Provision regle"),
    )
    emprunts = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Emprunts"),
    )
    dette_credit_bail_contrat_assimile = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Credit lease debts and related contracts"),
    )
    dettes_financiere_diverses = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Dettes financiere diverses"),
    )
    provision_financiere_risque_charge = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Provision financiere risque charge"),
    )
    dettes_fournisseurs_divers = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Dettes fournisseurs divers"),
    )
    avance_et_acomptes_recu = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Avance et acomptes recu"),
    )
    dettes = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Dettes"),
    )
    dettes_fiscales_sociales = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Dettes fiscales sociales"),
    )
    autres_dettes = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres dettes"),
    )
    banques_credit_escompte = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Banques credit escompte"),
    )
    banque_credit_caisse = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Banque credit caisse"),
    )
    banques_decouvert = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Banques decouvert"),
    )
    ecart_conversion_passif = models.DecimalField(
        max_digits=100,
        decimal_places=5,
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
    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
        indexes = [
            models.Index(fields=['annee', 'acheteur']),
            models.Index(fields=['created_at']),
        ]

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
        """Calcule le total du passif circulant (III)."""
        fields = [
            self.dettes_fournisseurs_divers,
            self.avance_et_acomptes_recu,
            self.dettes,
            self.dettes_fiscales_sociales,
            self.autres_dettes,
        ]
        return sum(f or 0 for f in fields)

    @property
    def total_IV(self):
        """Calcule le total de la trésorerie passif (IV)."""
        fields = [
            self.banques_credit_escompte,
            self.banque_credit_caisse,
            self.banques_decouvert,
        ]
        return sum(f or 0 for f in fields)

    @property
    def total_V(self):
        """Calcule l'écart de conversion passif (V)."""
        return self.ecart_conversion_passif or 0

    @property
    def total_general(self):
        """Calcule le total général du passif."""
        return self.total_I + self.total_II + self.total_III + self.total_IV + self.total_V


# Compte de Résultat
class ResultatC(Model):
    """Modele metier: ResultatC."""
    
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
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Vente de mdses"),
    )
    ventes_de_produits_fabriques = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Ventes de produits fabriques"),
    )
    travaux_services_vendus = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Travaux services vendus"),
    )
    produit_accessoires = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Produit accessoires"),
    )
    production_imblise = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Production imblise"),
    )
    subventions_exploitations = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Subventions exploitations"),
    )
    production_stockee = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Production stockee"),
    )
    reprises_de_provision = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Reprises de provision"),
    )
    transferts_charges = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Transferts charges"),
    )
    autres_produits = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres produits"),
    )
    achat_mdses = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Achat mdses"),
    )
    variation_stock_mdses = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Variation stock mdses"),
    )
    achat_mp_autres_appro = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Achat mp autres appro"),
    )
    var_stk_mp_app = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Var stk mp app"),
    )
    autres_achats = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres achats"),
    )
    variation_de_stocks_autres_appro = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Variation de stocks autres appro"),
    )
    transports = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Transports"),
    )
    services_ext = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Services ext"),
    )
    impots_taxes = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Impots taxes"),
    )
    autres_charges_valeur_ajoutee = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres charges valeur ajoutee"),
    )
    charges_personnel = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Charges personnel"),
    )
    dotation_aux_amorts = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Dotation aux amorts"),
    )
    dotation_aux_provisions = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Dotation aux provisions"),
    )
    autres_charges_excedent_brute = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres charges excedent brute"),
    )
    revenus_fin_assimiles = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Revenus fin assimiles"),
    )
    prof_vmp_et_cre_actif_immo = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Prof vmp et cre actif immo"),
    )
    interets_produit_assim = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Interets produit assim"),
    )
    reprise_prov_et_transfert = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Reprise prov et transfert"),
    )
    diff_positive_de_change = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Diff positive de change"),
    )
    prod_nets_cessions_vmp = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Prod nets cessions vmp"),
    )
    dap = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Dot. aux prov. & depreciations"),
    )
    frais_fin_charges_assi = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Frais fin. & chrges assimilées"),
    )
    diff_negatives_de_change = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Diff negatives de change"),
    )
    ch_nettes_cessions_vmp = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Ch nettes cessions vmp"),
    )
    sur_op_gestion_prod_except = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Sur op gestion prod except"),
    )
    sur_op_en_capital_prod_except = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Sur op en capital prod except"),
    )
    reprise_prov_transfert = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Reprise prov transfert"),
    )
    sur_op_gestion_charg_except = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Sur op gestion charg except"),
    )
    sur_op_en_capital_charg_except = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Sur op en capital charg except"),
    )
    dap_et_transfert_charg_except = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Dap et transfert charg except"),
    )
    participation_salairies = models.DecimalField(
        _("Participations des salariés"),
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
    )
    impot_sur_benefices = models.DecimalField(
        _("Impôts sur les bénéfices"),
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
    """Modele metier: Assets."""
    
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
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Caisse"),
    )
    # ASSETS
    # At Sight
    banques_centrales = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("-Banques centrales"),
    )
    tresorerie_cpp = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("-Trésorerie, CCP"),
    )
    autres_ets_credit = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("-Autres établissements de crédit"),
    )

    a_terme = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("A Terme"),
    )

    # Claims on Customers
    ## Commercial paper portofolio
    credits_campagne = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("-Crédits de campagne"),
    )
    credits_ordinaire = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("-Crédits ordinaires"),
    )
    ## Other Customer Contests
    credits_campagne_acc = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("-Crédits de campagne"),
    )
    credits_ordinaire_acc = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("-Crédits ordinaires"),
    )

    creances_ordinaires = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Créances ordinaires"),
    )
    affacturage = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Affacturage"),
    )

    titres_placement = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("TITRES DE PLACEMENT"),
    )
    immobilisation_fin = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("IMMOBILISATIONS FINANCIÈRES"),
    )
    operation_credit_bail = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("OPÉRATIONS DE CRÉDIT-BAIL ET ASSIMILÉES"),
    )
    immobilisation_incorporelle = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("IMMOBILISATIONS INCORPORELLES"),
    )
    immobilisation_corporelle = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("IMMOBILISATIONS CORPORELLES"),
    )
    actionnaire_ou_associe = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("ACTIONNAIRES OU ASSOCIÉS"),
    )
    autres_actifs = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("AUTRES ACTIFS"),
    )
    comptes_commande_divers = models.DecimalField(
        max_digits=100,
        decimal_places=5,
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

    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
    """Modele metier: Liabilities."""
    
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

    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
    """Modele metier: Expenses."""
    
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
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("Intérêts et charges assimilées sur dettes interbancaires"),
    )
    interet_charge_assimilee_dette_clientele = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        help_text="",
        verbose_name=_("Intérêts et charges assimilées sur dettes envers la clientèle"),
    )
    interet_charge_assimilee_titre_creance = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("Intérêts et charges assimilées sur titres de créances"),
    )
    chargesc_compte_bloque_dactionnaire_emprunt_sub = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "Charges sur comptes bloqués d'actionnaires emprunts sur titres subordonnés"
        ),
    )
    autres_interets_charges_assimilee = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("Autres Intérêts et charges assimilées"),
    )
    charges_sur_op_credit_bail_assimile = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("CHARGES SUR OPÉRATIONS DE CRÉDIT-BAIL ET ASSIMILÉES"),
    )
    commissions = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("COMMISSIONS"),
    )

    charges_sur_titre_placement = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text=_("Charges sur titres de placement"),
        verbose_name=_("Charges sur titres de placement"),
    )
    charges_sur_operation_change = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text=_("Charges sur opérations de change"),
        verbose_name=_("Charges sur opérations de change"),
    )
    charges_sur_operation_hors_bilan = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("Charges sur opérations hors bilan"),
    )
    frais_divers_exploitation_bancaire = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("FRAIS DIVERS D'EXPLOITATION BANCAIRE"),
    )
    achat_marchandises = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("ACHAT DE MARCHANDISES"),
    )
    stocks_vendus = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("STOCKS VENDUS"),
    )
    variations_stocks_marchanides = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("VARIATIONS DES STOCKS DE MARCHANDISES"),
    )
    frais_personnel = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Frais de personnel"),
    )

    autres_frais_generaux = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres frais généraux"),
    )
    dotations_amortissement_provision_immobilisation = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "DOTATIONS AUX AMORTISSEMENTS ET PROVISIONS SUR IMMOBILISATIONS"
        ),
    )
    solde_perte_creance_hors_bilan = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("SOLDE DES PERTES SUR CRÉANCES ET HORS BILAN"),
    )
    excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "EXCÉDENT DES DOTATIONS SUR LES REPRISES DU FONDS POUR RISQUES BANCAIRES GÉNÉRAUX"
        ),
    )
    charges_exceptionnelle = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("LES CHARGES EXCEPTIONNELLES"),
    )
    pertes_exercice_anterieurs = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("PERTES SUR EXERCICES ANTÉRIEURS"),
    )
    impot_sur_revenu = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("IMPÔTS SUR LE REVENU"),
    )
    total_charges = models.DecimalField(
        max_digits=100,
        decimal_places=5,
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

    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
    """Modele metier: Products."""
    
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
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "Intérêts et produits assimilés sur prêts et avances interbancaires"
        ),
    )
    ineterets_produit_assimile_pret_avance_clientele = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "Intérêts et produits assimilés sur prêts et avances à la clientèle"
        ),
    )
    interet_produit_sur_titre_dinvestissement = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Intérêts et produits assimilés sur titres d'investissement"),
    )
    revenu_gains_titre_pret_titre_subordonne = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "Revenus et gains sur titres de prêts et titres subordonnés émis"
        ),
    )

    autres_interets_produits_assimiles = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres intérêts et produits assimilés"),
    )
    produits_leansing_operation_connexes = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("PRODUITS DE LEASING ET OPÉRATIONS CONNEXES "),
    )
    commissions = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("COMMISSIONS"),
    )

    revenus_titre_negociable = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Revenus de titres négociables"),
    )
    dividendes_produits_assimiles = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Dividendes et produits assimilés"),
    )
    revenus_operation_de_change = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Revenus d'opérations de change"),
    )
    produits_opeations_hors_bilan = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("Produits des opérations hors bilan"),
    )

    produits_bancaire_divers = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("PRODUITS BANCAIRES DIVERS"),
    )
    marges_vente = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("MARGES DE VENTE"),
    )
    ventes_marchandises = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("VENTES DE MARCHANDISES"),
    )
    variation_stocks_marchandises = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("VARIATION DES STOCKS DE MARCHANDISES"),
    )
    produit_dexploitation_generale = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("PRODUITS D'EXPLOITATION GÉNÉRALE"),
    )

    reprise_damortissement_provisions_sur_immobilisation = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "REPRISES D'AMORTISSEMENTS ET DE PROVISIONS SUR IMMOBILISATIONS"
        ),
    )
    solde_resultat_correction_valeur_sur_creance_hors_bilan = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "SOLDE DU RÉSULTAT DES CORRECTIONS DE VALEUR SUR CRÉANCES ET HORS BILAN"
        ),
    )
    excedent_reprise_fonds_pour_risque_bancaire_generaux = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_(
            "EXCÉDENT DES REPRISES DU FONDS POUR RISQUES BANCAIRES GÉNÉRAUX"
        ),
    )

    produits_exceptionnels = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("PRODUITS EXCEPTIONNELS"),
    )
    benefice_sur_exercice_anterieur = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        help_text="",
        verbose_name=_("BÉNÉFICES SUR EXERCICES ANTÉRIEURS"),
    )
    perte = models.DecimalField(
        max_digits=100,
        decimal_places=5,
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

    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
    """Modele metier: OffBalanceSheet."""
    
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

    
    # --- Champs de suivi (inchangés) ---
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Date de mise à jour")
    )
    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
    #   PROPRIÉTÉS CORRIGÉES (uniquement avec les champs existants)
    # ----------------------------------------

    @property
    def total_engagement_financement_donne(self):
        """Calcule le total des engagements de financement DONNÉS."""
        fields_to_sum = [
            self.en_faveur_des_ets_credit,
            self.en_faveur_clientele,
        ]
        return sum(field or 0 for field in fields_to_sum)

    @property
    def total_engagement_garantie_donne(self):
        """Calcule le total des engagements de garantie DONNÉS."""
        fields_to_sum = [
            self.pour_compte_ets_credit,
            self.pour_compte_clientele,
        ]
        return sum(field or 0 for field in fields_to_sum)

    @property
    def total_engagements_donnes(self):
        """Calcule le total de TOUS les engagements DONNÉS."""
        return (
            self.total_engagement_financement_donne
            + self.total_engagement_garantie_donne
            + (self.engagement_sur_titre or 0)
        )

    @property
    def total_engagement_financement_recu(self):
        """Calcule le total des engagements de financement REÇUS."""
        fields_to_sum = [
            self.recu_ets_credit,
            self.recu_clientele,
        ]
        return sum(field or 0 for field in fields_to_sum)

    @property
    def total_engagements_recus(self):
        """Calcule le total de TOUS les engagements REÇUS."""
        return (
            self.total_engagement_financement_recu
            + (self.recu_ets_credit2 or 0)
            + (self.engagement_sur_titre2 or 0)
        )

    @property
    def total_general(self):
        """Calcule le total général (engagements donnés + reçus)."""
        return self.total_engagements_donnes + self.total_engagements_recus


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
    """Modele metier: ActifS."""
    
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
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Frais de développement et prospection"),
    )
    brevets_licences_logiciels = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Brevets, licences et logiciels"),
    )
    droits_propriete_commerciale_baux = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Droits de propriété commerciale et baux"),
    )
    autres_immo_incorporelles = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres immobilisations incorporelles"),
    )

    # Immobilisations corporelles
    terrains = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Terrains"),
    )
    dons_investissements_net = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Dons et investissements nets"),
    )
    batiments = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Bâtiments"),
    )
    agencements_amenagements_installations = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Agencements, aménagements et installations"),
    )
    materiel_mobilier_actif_biologiques = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Matériel, mobilier et actifs biologiques"),
    )
    materiel_transport = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Matériel de transport"),
    )

    # Avances et acomptes sur immobilisations
    avances_acompte_immobilisations = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Avances et acomptes sur immobilisations"),
    )
    # Immobilisations financieres
    titres_participation = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Titres de participation"),
    )
    autres_immobilisations_financieres = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres immobilisations financières"),
    )

    # Actif circulant de HAO
    actif_circulant_hao = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Actif circulant HAO"),
    )

    # Stock et En-cours (calcule)
    stock_encours = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Stock et en-cours"),
    )

    # Creances et emplois similaires (calcule)
    fournisseurs_avances_versee = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Fournisseurs, avances versées"),
    )
    clients = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Clients"),
    )
    autres_creances = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres créances"),
    )

    # Total de l'actif circulant
    valeurs_mobilieres_placement = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Valeurs mobilières de placement"),
    )
    disponibilites = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Disponibilités"),
    )
    banque_cheque_postal_caisse_assimiles = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Banque, chèque postal, caisse et assimilés"),
    )

    # Total de la trésorerie et des équivalents de trésorerie
    ecart_conversion_actif = models.DecimalField(
        max_digits=100,
        decimal_places=5,
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

    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
    """Modele metier: PassifS."""
    
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
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Capital"),
    )
    capital_non_appele_apporteurs = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Capital non appelé des apporteurs"),
    )
    primes_liees_capital_social = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Primes liées au capital social"),
    )
    ecart_reevaluation = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Écart de réévaluation"),
    )
    reserves_indisponibles = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Réserves indisponibles"),
    )
    reserves_libres = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Réserves libres"),
    )
    report_nouveau = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Report à nouveau (+ ou -)"),
    )
    resultat_net_exercice = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Résultat net de l'exercice (bénéfice + ou perte -)"),
    )
    subventions_investissements = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Subventions d'investissement"),
    )
    provisions_reglees = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Provisions réglées"),
    )

    emprunts_dettes_financieres_diverse = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Emprunts et dettes financières diverses"),
    )
    dettes_location_vente = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Dettes de location-vente"),
    )
    provisions_risques_charges = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Provisions pour risques et charges"),
    )

    passif_circulant_hao = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Passif circulant HAO"),
    )
    clients_avances_recues = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Clients, avances reçues"),
    )
    fournisseurs_exploitation = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Fournisseurs d'exploitation"),
    )
    dettes_fiscales_sociales = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Dettes fiscales et sociales"),
    )
    autres_dettes = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Autres dettes"),
    )
    provisions_risques_court_terme = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Provisions pour risques à court terme"),
    )

    banques_credit_escompte = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Banques, crédits d'escompte"),
    )
    banques_etablissements_financiers_credit_caisse = models.DecimalField(
        max_digits=100,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_("Banques, établissements financiers et crédits de caisse"),
    )

    ecart_conversion_passif = models.DecimalField(
        max_digits=100,
        decimal_places=5,
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

    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
    """Modele metier: ResultatS."""
    
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

    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True)
    updated_by = models.ForeignKey(
        "User",
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
        "User",
        related_name="%(class)s_created",
        on_delete=models.SET_NULL,
        null=True,
    )
    updated_by = models.ForeignKey(
        "User",
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
    """Modele metier: RatiosIFRS."""
    
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
# Debut Modules Commande
##########################################################
##########################################################
class Notification(Model):
    """Modele metier: Notification."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    TYPE_NOTIF = [
        ("AFFECTATION", "Nouvelle affectation"),
        ("RAPPORT_SOUMIS", "Rapport soumis"),
        ("VALIDATION", "Rapport validé"),
        ("CORRECTION", "Correction demandée"),
        ("ENVOI_CLIENT", "Rapport envoyé au client"),
        ("RAPPEL", "Rappel de notification"),
        ('ENVOI_REUSSI', 'Envoi réussi'),
        ('ENVOI_ECHEC', "Échec d'envoi"),
        ('RAPPORT_GENERE', 'Rapport généré'),
        ('TACHE_TERMINEE', 'Tâche terminée'),
        ('INFO', 'Information'),
        ('ALERTE', 'Alerte'),
    ]

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="custom_notifications",
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
    """Modele metier: Commande."""
    
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
    
    type_commande = models.CharField(max_length=100, blank=False, null=False, default='NORMALE')
    type_traitement = models.CharField(max_length=100, blank=False, null=False, default='MANUEL')
    client_nom = models.CharField(max_length=255, blank=True, verbose_name=_('Client'))

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
        "User",
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
        "User",
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
    """Modele metier: SuiviCommande."""
    
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
        "User",
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
    """Modele metier: AffectationAnalyste."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    commande = models.ForeignKey(
        "Commande", on_delete=models.CASCADE, verbose_name=_("Commande")
    )
    analyste = models.ForeignKey(
        "User",
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
    """Modele metier: Rapport."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    commande = models.ForeignKey(
        "Commande", on_delete=models.CASCADE, verbose_name=_("Commande")
    )
    analyste = models.ForeignKey(
        "User",
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
    """Modele metier: ValidationRapport."""
    
    safedelete_policy  = SOFT_DELETE_CASCADE
    
    rapport = models.OneToOneField(
        "Rapport", on_delete=models.CASCADE, verbose_name=_("Rapport")
    )
    validateur = models.ForeignKey(
        "User",
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
    """Modele metier: ReportRequest."""
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

    created_by = models.ForeignKey("User", null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name=_("Created By"))
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
    """Modele metier: Alerte."""
    
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
    """Modele metier: DocumentAlerte."""
    
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
    """Modele metier: Warning."""
    _safedelete_policy = SOFT_DELETE_CASCADE
    titre = models.CharField(max_length=500, verbose_name=_("Titre"), null=False, blank=False)
    description = models.TextField()
    acheteurs = models.ManyToManyField(Acheteur)
    created_by = models.ForeignKey("User", on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)

    # Champs email
    email_subject = models.CharField(max_length=500, blank=True, default='', verbose_name=_("Objet de l'email"))
    email_to = models.TextField(blank=True, default='', verbose_name=_("Destinataires (À)"))
    email_cc = models.TextField(blank=True, default='', verbose_name=_("Copie (CC)"))
    email_bcc = models.TextField(blank=True, default='', verbose_name=_("Copie cachée (BCC)"))
    email_sent = models.BooleanField(default=False, verbose_name=_("Email envoyé"), db_index=True)
    email_sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Date d'envoi"))

    def __str__(self):
        return self.titre

    def get_email_to_list(self):
        return [e.strip() for e in self.email_to.split(',') if e.strip()]

    def get_email_cc_list(self):
        return [e.strip() for e in self.email_cc.split(',') if e.strip()]

    def get_email_bcc_list(self):
        return [e.strip() for e in self.email_bcc.split(',') if e.strip()]


def warning_upload_path(instance, filename):
    return 'uploads/warnings/{}'.format(filename)


class WarningAttachment(Model):
    """Modele metier: WarningAttachment."""
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
    """Modele metier: NotifClient."""
    _safedelete_policy = SOFT_DELETE_CASCADE
    acheteurs = models.ManyToManyField(Acheteur)
    client = models.ForeignKey("User", on_delete=models.CASCADE)

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


class CompteFinancierIrfs(Model):
    """Modele metier: CompteFinancierIrfs."""
    
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
    """Modele metier: ValeurCompteIrfs."""
    
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
    """Modele metier: RatioFinancierIrfs."""
    
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
    """Modele metier: ValeurRatioIrfs."""
    
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
    """Modele metier: CredendoCommande."""
    
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
    """Modele metier: ScoringSansBilanAcheteur."""
    
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

    created_by = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="scorings_sansbilan_crees",
        verbose_name=_("Créé par"),
    )

    updated_by = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="scorings_sansbilan_modifies",
        verbose_name=_("Mis à jour par"),
    )

    history = HistoricalRecords()


    def __str__(self):
        parts = []
        if self.code:
            parts.append(self.code)
        if self.libelle:
            parts.append(self.libelle)

        if parts:
            return " - ".join(parts)

        return str(_("Modèle interpretation scoring sans bilan"))

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
from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE

AUTH_USER_MODEL = settings.AUTH_USER_MODEL


class MailInfo(SafeDeleteModel):
    """Modele metier: MailInfo."""
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
    """Modele metier: MailAttachment."""
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
    """Modele metier: DocDownload."""
    acheteur = models.ForeignKey(Acheteur, on_delete=models.CASCADE)
    client = models.ForeignKey("User", on_delete=models.CASCADE)
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

class Locaux(models.Model):
    """Modele metier: Locaux."""
    _safedelete_policy = SOFT_DELETE_CASCADE
    nom = models.CharField(_("nom"), max_length=100)

    def __str__(self):
        return self.nom


class ListeConditionAchat(models.Model):
    """Modele metier: ListeConditionAchat."""
    _safedelete_policy = SOFT_DELETE_CASCADE
    nom = models.CharField(_("nom"), max_length=100)

    def __str__(self):
        return self.nom   
    
    
class ListeConditionVente(models.Model):
    """Modele metier: ListeConditionVente."""
    _safedelete_policy = SOFT_DELETE_CASCADE
    nom = models.CharField(_("nom"), max_length=100)

    def __str__(self):
        return self.nom
    
    
class ListeImportation(models.Model):
    """Modele metier: ListeImportation."""
    _safedelete_policy = SOFT_DELETE_CASCADE
    libelle = models.TextField(_("nom"), max_length=2000)

    def __str__(self):
        return self.libelle


class ListeComportementsPaiement(models.Model):
    """Modele metier: ListeComportementsPaiement."""
    _safedelete_policy = SOFT_DELETE_CASCADE
    libelle = models.TextField(_("libelle"), max_length=255)
    couleur = models.CharField(_("couleur"), max_length=10)

    def __str__(self):
        return self.libelle



class ListeInformationsRating(models.Model):
    """Modele metier: ListeInformationsRating."""
    _safedelete_policy = SOFT_DELETE_CASCADE
    libelle = models.TextField(_("libelle"), max_length=255)
    couleur = models.CharField(_("couleur"), max_length=10)

    def __str__(self):
        return self.libelle


class ListeInformationsAvisCommercial(models.Model):
    """Modele metier: ListeInformationsAvisCommercial."""
    _safedelete_policy = SOFT_DELETE_CASCADE
    code_ac = models.IntegerField(_("code"), default=0)
    libelle = models.TextField(_("libelle"), max_length=500)
    libelle_en = models.TextField(_("libelle (EN)"), max_length=500, blank=True, default="")
    couleur = models.CharField(_("couleur"), max_length=20)

    class Meta:
        ordering = ['code_ac']

    def __str__(self):
        return self.libelle


class MailInboxConfig(models.Model):
    """Configuration IMAP — supporte plusieurs boîtes mail."""
    name = models.CharField(_("nom du compte"), max_length=100, blank=True, default="")
    imap_host = models.CharField(_("hôte IMAP"), max_length=255, blank=True, default="")
    imap_port = models.PositiveSmallIntegerField(_("port"), default=993)
    imap_user = models.CharField(_("utilisateur"), max_length=255, blank=True, default="")
    imap_password = models.CharField(_("mot de passe"), max_length=500, blank=True, default="")
    use_ssl = models.BooleanField(_("SSL/TLS"), default=True)
    mailbox = models.CharField(_("boîte"), max_length=100, default="INBOX")
    is_active = models.BooleanField(_("actif"), default=True)
    last_polled_at = models.DateTimeField(_("dernier relevé"), null=True, blank=True)
    last_error = models.TextField(_("dernière erreur"), blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = _("Configuration boîte mail")
        verbose_name_plural = _("Configurations boîtes mail")
        ordering = ['id']

    def __str__(self):
        label = self.name or self.imap_user
        return f"{label} ({self.imap_host})" if label else self.imap_host


class MailSource(models.Model):
    """Expéditeur/domaine autorisé à déposer des demandes par mail."""
    client_name = models.CharField(_("nom client"), max_length=255, blank=True, default="")
    email_or_domain = models.CharField(_("email ou domaine"), max_length=255, unique=True, blank=True, default="")
    notes = models.TextField(_("notes"), blank=True, default="")
    is_active = models.BooleanField(_("actif"), default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = _("Source mail autorisée")
        verbose_name_plural = _("Sources mail autorisées")
        ordering = ['client_name']

    def __str__(self):
        return f"{self.client_name} <{self.email_or_domain}>"

    @property
    def is_domain(self):
        return self.email_or_domain.startswith('@') or '@' not in self.email_or_domain


class IncomingMail(models.Model):
    """Mail entrant reçu depuis une source autorisée."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', _("En attente")
        DISPATCHED = 'DISPATCHED', _("Dispatché")
        ACCEPTED = 'ACCEPTED', _("Accepté")
        PROCESSED = 'PROCESSED', _("Traité")
        REJECTED = 'REJECTED', _("Rejeté")

    mail_source = models.ForeignKey(
        MailSource, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mails', verbose_name=_("source"),
    )
    message_id = models.CharField(_("Message-ID"), max_length=500, unique=True, blank=True, default="")
    from_email = models.EmailField(_("expéditeur"), blank=True, default="")
    from_name = models.CharField(_("nom expéditeur"), max_length=255, blank=True, default="")
    subject = models.CharField(_("sujet"), max_length=500, blank=True, default="")
    body_text = models.TextField(_("corps texte"), blank=True, default="")
    body_html = models.TextField(_("corps HTML"), blank=True, default="")
    received_at = models.DateTimeField(_("reçu le"), null=True, blank=True)
    status = models.CharField(
        _("statut"), max_length=20, choices=Status.choices, default=Status.PENDING,
    )
    assigned_to = models.ForeignKey(
        "User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_mails', verbose_name=_("assigné à"),
    )
    dispatched_at = models.DateTimeField(_("dispatché le"), null=True, blank=True)
    dispatched_by = models.ForeignKey(
        "User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dispatched_mails', verbose_name=_("dispatché par"),
    )
    dispatch_note = models.TextField(_("note de dispatch"), blank=True, default="")
    accepted_at = models.DateTimeField(_("accepté le"), null=True, blank=True)
    accepted_by = models.ForeignKey(
        "User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name='accepted_mails', verbose_name=_("accepté par"),
    )
    commande = models.ForeignKey(
        "Commande", on_delete=models.SET_NULL, null=True, blank=True,
        related_name='incoming_mails', verbose_name=_("commande liée"),
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = _("Mail entrant")
        verbose_name_plural = _("Mails entrants")
        ordering = ['-received_at']

    def __str__(self):
        return f"[{self.status}] {self.subject} — {self.from_email}"


class MailAttachment(models.Model):
    """Pièce jointe d'un mail entrant."""
    mail = models.ForeignKey(
        IncomingMail, on_delete=models.CASCADE,
        related_name='attachments', verbose_name=_("mail"),
        null=True, blank=True,
    )
    filename = models.CharField(_("nom fichier"), max_length=500, blank=True, default="")
    content_type = models.CharField(_("type MIME"), max_length=200, blank=True, default="")
    size = models.PositiveIntegerField(_("taille (octets)"), default=0)
    file = models.FileField(_("fichier"), upload_to="mail_attachments/", blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = _("Pièce jointe mail")
        verbose_name_plural = _("Pièces jointes mail")

    def __str__(self):
        return self.filename


##########################################################
##########################################################
# Fin Modules Pelba
##########################################################
##########################################################




class ActivityLog(models.Model):
    """Journal d'activité pour suivre les actions"""
    user = models.ForeignKey("User", on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=50)
    object_id = models.IntegerField(null=True, blank=True)
    object_type = models.CharField(max_length=50)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Journal d\'activité'
        verbose_name_plural = 'Journaux d\'activité'
    
    def __str__(self):
        return f"{self.action_type} par {self.user} à {self.created_at}"
