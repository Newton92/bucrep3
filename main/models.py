from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

# Create your models here.

couleur_validator = RegexValidator(r'^#([0-9A-Fa-f]{3}){1,2}$', 'La couleur doit être au format hexadécimal (#RRGGBB ou #RGB).')



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
    pays = models.ForeignKey(
        'Pays',
        null=True,
        on_delete=models.DO_NOTHING,
        verbose_name=_("Pays"),
        help_text=_("Pays auquel appartient la ville.")
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
        return f"{self.code} - {self.libelle}" if self.libelle else _("Catégorie Code NACE sans libellé")

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
        
        
class BaseModele(models.Model):
    code = models.CharField(_("Code"), max_length=50, unique=True, null=True, blank=True)
    libelle = models.CharField(_("Libellé"), max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(_("Date de Création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de Mise à Jour"), auto_now=True)

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
