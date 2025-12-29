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
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from safedelete.models import SOFT_DELETE_CASCADE, SafeDeleteModel as Model
from simple_history.models import HistoricalRecords

from main.utilitaires import constantes


# ============================================================================
# VALIDATEURS PERSONNALISÉS
# ============================================================================

couleur_validator = RegexValidator(
    r"^#([0-9A-Fa-f]{3}){1,2}$",
    "La couleur doit être au format hexadécimal (#RRGGBB ou #RGB).",
)


# ============================================================================
# CONSTANTES ET CHOIX
# ============================================================================

ROLES_USERS = [
    ("Root", "Root"),
    ("Validateur", "Validateur"),
    ("Analyste", "Analyste"),
    ("Client", "Client"),
]


# ============================================================================
# MODÈLE UTILISATEUR
# ============================================================================

class User(AbstractUser):
    """
    Modèle utilisateur personnalisé étendant AbstractUser.
    Gère les utilisateurs du système avec des fonctionnalités avancées.
    
    Attributs hérités d'AbstractUser :
    - username, first_name, last_name, email
    - is_staff, is_active, date_joined
    - password, last_login, etc.
    """
    
    # ========================================================================
    # CHAMPS D'AUTHENTIFICATION ET SÉCURITÉ
    # ========================================================================
    
    avatar = models.ImageField(
        _("avatar"),
        upload_to="avatars/",
        null=True,
        blank=True,
        help_text=_("Image de profil de l'utilisateur."),
    )
    
    code_secret = models.CharField(
        _("code secret"),
        max_length=6,
        null=True,
        blank=True,
        help_text=_("Code à 6 chiffres pour la réinitialisation du mot de passe."),
    )
    
    code_connexion = models.CharField(
        _("code de connexion"),
        max_length=6,
        null=True,
        blank=True,
        help_text=_("Code à 6 chiffres pour l'authentification à deux facteurs."),
    )
    
    auth_a2f = models.BooleanField(
        _("authentification à deux facteurs"),
        default=False,
        help_text=_("Activer l'authentification à deux facteurs pour cet utilisateur."),
    )
    
    reset_token = models.CharField(
        _("jeton de réinitialisation"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Jeton utilisé pour la réinitialisation du mot de passe."),
    )
    
    password_changed_at = models.DateTimeField(
        _("dernière modification du mot de passe"),
        null=True,
        blank=True,
        help_text=_("Date et heure de la dernière modification du mot de passe."),
    )
    
    # ========================================================================
    # INFORMATIONS PERSONNELLES
    # ========================================================================
    
    address = models.CharField(
        _("adresse"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Adresse postale de l'utilisateur."),
    )
    
    phone = models.CharField(
        _("téléphone"),
        max_length=20,
        null=True,
        blank=True,
        help_text=_("Numéro de téléphone de l'utilisateur."),
    )
    
    profession = models.CharField(
        _("profession"),
        max_length=100,
        null=True,
        blank=True,
        help_text=_("Profession ou métier de l'utilisateur."),
    )
    
    email_cc = models.EmailField(
        _("email en copie"),
        null=True,
        blank=True,
        help_text=_("Adresse email à mettre en copie pour les notifications."),
    )
    
    # ========================================================================
    # GESTION DU COMPTE ET AUTORISATIONS
    # ========================================================================
    
    activation = models.BooleanField(
        _("activation du compte"),
        default=True,
        help_text=_("État d'activation du compte utilisateur."),
    )
    
    role = models.CharField(
        max_length=100,
        choices=ROLES_USERS,
        verbose_name="rôle utilisateur",
        null=True,
        blank=True,
        help_text=_("Rôle et permissions de l'utilisateur dans le système."),
    )
    
    is_client = models.BooleanField(
        default=False,
        verbose_name="est client",
        help_text=_("Indique si l'utilisateur est un client externe."),
    )
    
    # ========================================================================
    # RELATIONS AVEC LES PAYS
    # ========================================================================
    
    pays = models.ForeignKey(
        "Pays",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="pays_utilisateurs",
        verbose_name=_("Pays"),
        help_text=_("Pays principal d'affectation de l'utilisateur."),
    )
    
    affectation = models.ManyToManyField(
        "Pays",
        blank=True,
        related_name="affectation_utilisateurs",
        verbose_name=_("pays d'affectation"),
        help_text=_("Pays où l'utilisateur est actuellement affecté."),
    )
    
    affectation_possible = models.ManyToManyField(
        "Pays",
        blank=True,
        related_name='affectations_possibles',
        verbose_name=_("pays d'affectation possibles"),
        help_text=_("Pays où l'utilisateur peut potentiellement être affecté."),
    )
    
    # ========================================================================
    # HISTORIQUE ET MÉTADONNÉES
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle de l'utilisateur."""
        return self.username
    
    def fullname(self):
        """
        Retourne le nom complet de l'utilisateur.
        
        Returns:
            str: Prénom et nom concaténés
        """
        return f"{self.first_name} {self.last_name}".strip()
    
    @classmethod
    def get_user_country(cls, request):
        """
        Récupère le pays de l'utilisateur connecté.
        
        Args:
            request: Objet requête Django
            
        Returns:
            Pays: Pays de l'utilisateur connecté
        """
        return request.user.pays if hasattr(request.user, 'pays') else None
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour détecter les changements de mot de passe.
        
        Logique:
        1. Pour un utilisateur existant: compare le mot de passe avec l'ancien
        2. Pour un nouvel utilisateur: enregistre la date courante
        3. Appelle la méthode save parent
        """
        # Détecter si le mot de passe a changé pour un utilisateur existant
        if self.pk:
            try:
                old_user = User.objects.get(pk=self.pk)
                if self.password != old_user.password:
                    self.password_changed_at = timezone.now()
            except User.DoesNotExist:
                pass
        elif self.password:
            # Nouvel utilisateur avec mot de passe défini
            self.password_changed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # # app_label = 'report'
        verbose_name = _("utilisateur")
        verbose_name_plural = _("utilisateurs")


# ============================================================================
# MODÈLE DE RÉFÉRENCE ENTRE GROUPES
# ============================================================================

class Referer(models.Model):
    """
    Modèle de référence entre groupes d'utilisateurs.
    Définit les relations de notification entre différents groupes.
    
    Exemple: Le groupe "Analystes" notifie le groupe "Validateurs"
    """
    
    # ========================================================================
    # RELATIONS
    # ========================================================================
    
    source = models.ForeignKey(
        Group,
        on_delete=models.DO_NOTHING,
        related_name='referer_sources',
        verbose_name=_("groupe source"),
        help_text=_("Groupe qui initie la notification."),
    )
    
    target = models.ForeignKey(
        Group,
        on_delete=models.DO_NOTHING,
        related_name='referer_targets',
        verbose_name=_("groupe cible"),
        help_text=_("Groupe qui reçoit la notification."),
    )
    
    # ========================================================================
    # GESTION DE LA SUPPRESSION
    # ========================================================================
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle de la référence."""
        return f"{self.source} notifie {self.target}"
    
    def clean(self):
        """
        Validation personnalisée.
        Empêche une relation réflexive (source == target).
        """
        if self.source == self.target:
            raise ValidationError(
                _("Le groupe source et le groupe cible ne peuvent pas être identiques.")
            )
        super().clean()
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        verbose_name = _("référence de groupe")
        verbose_name_plural = _("références de groupes")
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'target'],
                name='unique_source_target',
                violation_error_message=_(
                    "Cette relation entre les groupes existe déjà."
                )
            )
        ]
        ordering = ['source__name', 'target__name']


# ============================================================================
# MODÈLE DES EMAILS ADMINISTRATEURS
# ============================================================================

class AdminMails(models.Model):
    """
    Modèle de stockage des emails des administrateurs.
    Utilisé pour les notifications système et les alertes.
    """
    
    # ========================================================================
    # CHAMPS
    # ========================================================================
    
    email = models.EmailField(
        max_length=255,
        unique=True,
        verbose_name=_("adresse email"),
        help_text=_("Adresse email de l'administrateur pour les notifications."),
    )
    
    # ========================================================================
    # GESTION DE LA SUPPRESSION
    # ========================================================================
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle de l'email administrateur."""
        return self.email
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        verbose_name = _("email administrateur")
        verbose_name_plural = _("emails administrateurs")
        ordering = ['email']


# ============================================================================
# MODÈLES GÉOGRAPHIQUES
# ============================================================================

class Pays(Model):
    """
    Modèle représentant un pays dans le système.
    
    Utilisé pour la géolocalisation et l'organisation des données
    par territoire national.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # INFORMATIONS GÉOGRAPHIQUES
    # ========================================================================
    
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
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
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
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle du pays."""
        return f"{self.nom} ({self.code})"
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # # app_label = 'report'
        verbose_name = _("Pays")
        verbose_name_plural = _("Pays")
        ordering = ["nom"]  # Trie les pays par nom dans l'ordre alphabétique.


class Province(Model):
    """
    Modèle représentant une province ou région administrative.
    
    Subdivision d'un pays, utilisée pour une organisation géographique
    plus fine.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # INFORMATIONS GÉOGRAPHIQUES
    # ========================================================================
    
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
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
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
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle de la province."""
        return f"{self.nom} ({self.code})"
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # # app_label = 'report'
        verbose_name = _("Province")
        verbose_name_plural = _("Provinces")
        ordering = ["nom"]  # Trie les provinces par nom dans l'ordre alphabétique.


class Ville(Model):
    """
    Modèle représentant une ville.
    
    Subdivision d'une province, niveau le plus fin de l'organisation
    géographique dans le système.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # INFORMATIONS GÉOGRAPHIQUES
    # ========================================================================
    
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
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
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
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle de la ville."""
        return f"{self.nom} ({self.code})"
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # # app_label = 'report'
        verbose_name = _("Ville")
        verbose_name_plural = _("Villes")
        ordering = ["nom"]  # Trie les villes par nom dans l'ordre alphabétique.


# ============================================================================
# MODÈLES DE RÉFÉRENCE TEMPORELLE
# ============================================================================

class Annee(Model):
    """
    Modèle représentant une année civile.
    
    Utilisé pour organiser les données par période temporelle
    et gérer les références temporelles dans le système.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # INFORMATIONS TEMPORELLES
    # ========================================================================
    
    annee = models.IntegerField(
        unique=True,
        verbose_name=_("Année"),
        help_text=_("Année de référence, par exemple 2025."),
    )
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
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
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle de l'année."""
        return str(self.annee)
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # # app_label = 'report'
        verbose_name = _("Année civile")
        verbose_name_plural = _("Années civiles")
        ordering = ["annee"]  # Trie les années par ordre croissant.


# ============================================================================
# MODÈLES FINANCIERS
# ============================================================================

class Devise(Model):
    """
    Modèle représentant une devise monétaire.
    
    Utilisé pour gérer les transactions multi-devises
    et les conversions monétaires dans le système.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # INFORMATIONS MONÉTAIRES
    # ========================================================================
    
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
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
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
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle de la devise."""
        return f"{self.nom} ({self.code})"
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # # app_label = 'report'
        verbose_name = _("Devise")
        verbose_name_plural = _("Devises")
        ordering = ["nom"]  # Trie les devises par nom dans l'ordre alphabétique.


# ============================================================================
# MODÈLES D'INTERFACE UTILISATEUR
# ============================================================================

class CouleurCommentaire(Model):
    """
    Modèle représentant une couleur pour les commentaires.
    
    Utilisé pour le système de coloration des commentaires
    dans l'interface utilisateur.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # INFORMATIONS DE COULEUR
    # ========================================================================
    
    couleur = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Nom de la Couleur"),
        help_text=_("Nom de la couleur, par exemple 'Rouge' ou 'Vert'."),
    )
    
    code = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Code Couleur"),
        validators=[couleur_validator],
        help_text=_("Code hexadécimal de la couleur, par exemple '#FF5733'."),
    )
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle de la couleur."""
        return self.couleur or self.code
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # # app_label = 'report'
        verbose_name = _("Coloration")
        verbose_name_plural = _("Colorations")
        ordering = ["code"]  # Trie les couleurs par code dans l'ordre alphabétique.



# ============================================================================
# MODÈLES DE CONFIGURATION ET LISTES DE RÉFÉRENCE
# ============================================================================

class Locaux(Model):
    """
    Modèle représentant un local ou un espace physique.
    
    Utilisé pour identifier et organiser les différents espaces
    physiques au sein de l'organisation (bureaux, entrepôts, etc.).
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # INFORMATIONS DU LOCAL
    # ========================================================================
    
    nom = models.CharField(
        _("nom"),
        max_length=100,
        verbose_name=_("Nom du local"),
        help_text=_("Nom ou identifiant du local, par exemple 'Bureau Principal' ou 'Entrepôt A'."),
    )
    
    # ========================================================================
    # INFORMATIONS COMPLÉMENTAIRES
    # ========================================================================
    
    code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Code du local"),
        help_text=_("Code interne pour identifier le local."),
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_("Description détaillée du local et de son utilisation."),
    )
    
    capacite = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Capacité"),
        help_text=_("Capacité d'accueil ou de stockage du local."),
    )
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création du local."),
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification"),
        help_text=_("Date et heure de la dernière modification du local."),
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si le local est actif ou désactivé."),
    )
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle du local."""
        return self.nom
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # app_label = 'report'
        verbose_name = _("Local")
        verbose_name_plural = _("Locaux")
        ordering = ["nom"]
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['is_active']),
        ]


class ListeConditionAchat(Model):
    """
    Modèle représentant une condition d'achat dans le système.
    
    Liste de référence pour les différentes conditions d'achat
    pouvant être appliquées aux transactions commerciales.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # INFORMATIONS DE LA CONDITION
    # ========================================================================
    
    nom = models.CharField(
        _("nom"),
        max_length=100,
        unique=True,
        verbose_name=_("Condition d'achat"),
        help_text=_("Nom de la condition d'achat, par exemple '30 jours net' ou 'Paiement comptant'."),
    )
    
    # ========================================================================
    # DÉTAILS DE LA CONDITION
    # ========================================================================
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_("Description détaillée de la condition d'achat."),
    )
    
    delai_jours = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Délai en jours"),
        help_text=_("Délai de paiement en jours pour cette condition."),
        validators=[MinValueValidator(0)]
    )
    
    ordre_affichage = models.IntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage"),
        help_text=_("Ordre d'affichage de la condition dans les listes déroulantes."),
    )
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création de la condition d'achat."),
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification"),
        help_text=_("Date et heure de la dernière modification de la condition d'achat."),
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si la condition d'achat est active ou désactivée."),
    )
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle de la condition d'achat."""
        return self.nom
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # app_label = 'report'
        verbose_name = _("Condition d'achat")
        verbose_name_plural = _("Conditions d'achat")
        ordering = ["ordre_affichage", "nom"]
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['is_active', 'ordre_affichage']),
        ]


class ListeConditionVente(Model):
    """
    Modèle représentant une condition de vente dans le système.
    
    Liste de référence pour les différentes conditions de vente
    pouvant être appliquées aux transactions commerciales.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # INFORMATIONS DE LA CONDITION
    # ========================================================================
    
    nom = models.CharField(
        _("nom"),
        max_length=100,
        unique=True,
        null=True,
        verbose_name=_("Condition de vente"),
        help_text=_("Nom de la condition de vente, par exemple 'Livraison sous 48h' ou 'Garantie 2 ans'."),
    )
    
    # ========================================================================
    # DÉTAILS DE LA CONDITION
    # ========================================================================
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_("Description détaillée de la condition de vente."),
    )
    
    delai_jours = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Délai en jours"),
        help_text=_("Délai de livraison ou d'exécution en jours."),
        validators=[MinValueValidator(0)]
    )
    
    ordre_affichage = models.IntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage"),
        help_text=_("Ordre d'affichage de la condition dans les listes déroulantes."),
    )
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création de la condition de vente."),
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification"),
        help_text=_("Date et heure de la dernière modification de la condition de vente."),
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si la condition de vente est active ou désactivée."),
    )
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle de la condition de vente."""
        return self.nom
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # app_label = 'report'
        verbose_name = _("Condition de vente")
        verbose_name_plural = _("Conditions de vente")
        ordering = ["ordre_affichage", "nom"]
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['is_active', 'ordre_affichage']),
        ]


class ListeImportation(Model):
    """
    Modèle représentant une information d'importation.
    
    Liste de référence pour les différentes informations
    liées aux processus d'importation dans le système.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # INFORMATIONS D'IMPORTATION
    # ========================================================================
    
    libelle = models.TextField(
        _("nom"),
        max_length=2000,
        verbose_name=_("Libellé d'importation"),
        help_text=_("Description détaillée de l'information d'importation."),
    )
    
    # ========================================================================
    # CATÉGORISATION
    # ========================================================================
    
    categorie = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Catégorie"),
        help_text=_("Catégorie de l'information d'importation."),
    )
    
    code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Code"),
        help_text=_("Code unique pour identifier l'information d'importation."),
    )
    
    ordre_affichage = models.IntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage"),
        help_text=_("Ordre d'affichage dans les listes déroulantes."),
    )
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création de l'information d'importation."),
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification"),
        help_text=_("Date et heure de la dernière modification de l'information d'importation."),
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si l'information d'importation est active ou désactivée."),
    )
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle de l'information d'importation."""
        return self.libelle[:100] + "..." if len(self.libelle) > 100 else self.libelle
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # app_label = 'report'
        verbose_name = _("Information d'importation")
        verbose_name_plural = _("Informations d'importation")
        ordering = ["ordre_affichage", "categorie", "libelle"]
        indexes = [
            models.Index(fields=['categorie']),
            models.Index(fields=['is_active', 'ordre_affichage']),
        ]


class ListeComportementsPaiement(Model):
    """
    Modèle représentant un comportement de paiement.
    
    Liste de référence pour les différents comportements de paiement
    observés chez les clients ou partenaires commerciaux.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # INFORMATIONS DU COMPORTEMENT
    # ========================================================================
    
    libelle = models.TextField(
        _("libelle"),
        max_length=255,
        verbose_name=_("Comportement de paiement"),
        help_text=_("Description du comportement de paiement."),
    )
    
    couleur = models.CharField(
        _("couleur"),
        max_length=10,
        verbose_name=_("Couleur d'affichage"),
        help_text=_("Couleur pour l'affichage visuel du comportement."),
        validators=[couleur_validator],
    )
    
    # ========================================================================
    # CATÉGORISATION
    # ========================================================================
    
    niveau_risque = models.IntegerField(
        choices=[
            (1, "Faible"),
            (2, "Modéré"),
            (3, "Élevé"),
            (4, "Critique"),
        ],
        default=1,
        verbose_name=_("Niveau de risque"),
        help_text=_("Niveau de risque associé à ce comportement de paiement."),
    )
    
    code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Code"),
        help_text=_("Code unique pour identifier le comportement de paiement."),
    )
    
    ordre_affichage = models.IntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage"),
        help_text=_("Ordre d'affichage dans les listes déroulantes."),
    )
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création du comportement de paiement."),
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification"),
        help_text=_("Date et heure de la dernière modification du comportement de paiement."),
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si le comportement de paiement est actif ou désactivé."),
    )
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle du comportement de paiement."""
        return self.libelle[:80] + "..." if len(self.libelle) > 80 else self.libelle
    
    def couleur_html(self):
        """Retourne la couleur formatée pour HTML."""
        return self.couleur if self.couleur.startswith('#') else f'#{self.couleur}'
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # app_label = 'report'
        verbose_name = _("Comportement de paiement")
        verbose_name_plural = _("Comportements de paiement")
        ordering = ["ordre_affichage", "libelle"]
        indexes = [
            models.Index(fields=['niveau_risque']),
            models.Index(fields=['is_active', 'ordre_affichage']),
        ]


class ListeInformationsRating(Model):
    """
    Modèle représentant une information de rating.
    
    Liste de référence pour les différentes informations
    utilisées dans le processus de rating ou d'évaluation.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # INFORMATIONS DE RATING
    # ========================================================================
    
    libelle = models.TextField(
        _("libelle"),
        max_length=255,
        verbose_name=_("Information de rating"),
        help_text=_("Description de l'information utilisée dans le processus de rating."),
    )
    
    couleur = models.CharField(
        _("couleur"),
        max_length=10,
        verbose_name=_("Couleur d'affichage"),
        help_text=_("Couleur pour l'affichage visuel de l'information de rating."),
        validators=[couleur_validator],
    )
    
    # ========================================================================
    # CATÉGORISATION
    # ========================================================================
    
    categorie = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Catégorie"),
        help_text=_("Catégorie de l'information de rating."),
    )
    
    code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Code"),
        help_text=_("Code unique pour identifier l'information de rating."),
    )
    
    impact = models.IntegerField(
        choices=[
            (1, "Faible"),
            (2, "Moyen"),
            (3, "Important"),
            (4, "Critique"),
        ],
        default=2,
        verbose_name=_("Impact"),
        help_text=_("Impact de cette information sur le rating global."),
    )
    
    ordre_affichage = models.IntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage"),
        help_text=_("Ordre d'affichage dans les listes déroulantes."),
    )
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création de l'information de rating."),
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification"),
        help_text=_("Date et heure de la dernière modification de l'information de rating."),
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si l'information de rating est active ou désactivée."),
    )
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle de l'information de rating."""
        return self.libelle[:80] + "..." if len(self.libelle) > 80 else self.libelle
    
    def couleur_html(self):
        """Retourne la couleur formatée pour HTML."""
        return self.couleur if self.couleur.startswith('#') else f'#{self.couleur}'
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # app_label = 'report'
        verbose_name = _("Information de rating")
        verbose_name_plural = _("Informations de rating")
        ordering = ["ordre_affichage", "categorie", "libelle"]
        indexes = [
            models.Index(fields=['categorie', 'impact']),
            models.Index(fields=['is_active', 'ordre_affichage']),
        ]


class ListeInformationsAvisCommercial(Model):
    """
    Modèle représentant une information pour l'avis commercial.
    
    Liste de référence pour les différentes informations
    utilisées dans la préparation des avis commerciaux.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    # ========================================================================
    # INFORMATIONS POUR AVIS COMMERCIAL
    # ========================================================================
    
    libelle = models.TextField(
        _("libelle"),
        max_length=255,
        verbose_name=_("Information pour avis commercial"),
        help_text=_("Description de l'information utilisée dans les avis commerciaux."),
    )
    
    couleur = models.CharField(
        _("couleur"),
        max_length=20,
        verbose_name=_("Couleur d'affichage"),
        help_text=_("Couleur pour l'affichage visuel de l'information."),
        validators=[couleur_validator],
    )
    
    # ========================================================================
    # CATÉGORISATION
    # ========================================================================
    
    type_avis = models.CharField(
        max_length=50,
        choices=[
            ("POSITIF", "Positif"),
            ("NEUTRE", "Neutre"),
            ("NEGATIF", "Négatif"),
            ("ALERTE", "Alerte"),
        ],
        default="NEUTRE",
        verbose_name=_("Type d'avis"),
        help_text=_("Type d'avis associé à cette information."),
    )
    
    code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Code"),
        help_text=_("Code unique pour identifier l'information."),
    )
    
    priorite = models.IntegerField(
        choices=[
            (1, "Basse"),
            (2, "Normale"),
            (3, "Haute"),
            (4, "Urgente"),
        ],
        default=2,
        verbose_name=_("Priorité"),
        help_text=_("Priorité de cette information dans l'avis commercial."),
    )
    
    ordre_affichage = models.IntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage"),
        help_text=_("Ordre d'affichage dans les listes déroulantes."),
    )
    
    # ========================================================================
    # GESTION DU CYCLE DE VIE
    # ========================================================================
    
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création"),
        help_text=_("Date et heure de la création de l'information."),
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification"),
        help_text=_("Date et heure de la dernière modification de l'information."),
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Actif"),
        help_text=_("Indique si l'information est active ou désactivée."),
    )
    
    # ========================================================================
    # HISTORIQUE
    # ========================================================================
    
    history = HistoricalRecords()
    
    # ========================================================================
    # MÉTHODES
    # ========================================================================
    
    def __str__(self):
        """Représentation textuelle de l'information pour avis commercial."""
        return self.libelle[:80] + "..." if len(self.libelle) > 80 else self.libelle
    
    def couleur_html(self):
        """Retourne la couleur formatée pour HTML."""
        return self.couleur if self.couleur.startswith('#') else f'#{self.couleur}'
    
    def get_type_avis_display_color(self):
        """Retourne la couleur associée au type d'avis."""
        color_map = {
            "POSITIF": "#28a745",  # Vert
            "NEUTRE": "#6c757d",   # Gris
            "NEGATIF": "#dc3545",  # Rouge
            "ALERTE": "#ffc107",   # Jaune/Orange
        }
        return color_map.get(self.type_avis, "#6c757d")
    
    # ========================================================================
    # META
    # ========================================================================
    
    class Meta:
        # app_label = 'report'
        verbose_name = _("Information pour avis commercial")
        verbose_name_plural = _("Informations pour avis commercial")
        ordering = ["ordre_affichage", "type_avis", "priorite", "libelle"]
        indexes = [
            models.Index(fields=['type_avis', 'priorite']),
            models.Index(fields=['is_active', 'ordre_affichage']),
        ]





# ============================================================================
# MODÈLES DE CLASSIFICATION ET RÉFÉRENCES ENTREPRISES
# ============================================================================

class CategoryNaceCode(Model):
    """
    Modèle représentant une catégorie de code NACE (Nomenclature statistique
    des Activités économiques dans la Communauté Européenne).
    
    Utilisé pour classifier les entreprises par secteur d'activité économique
    selon la norme européenne NACE.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant la catégorie NACE.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Description ou nom de la catégorie NACE.")
    )
    active = models.BooleanField(
        _("Actif"),
        default=True,
        help_text=_("Indique si cette catégorie est active dans le système.")
    )
    poids = models.FloatField(
        _("Poids"),
        default=0.0,
        help_text=_("Poids associé à cette catégorie pour les calculs de scoring.")
    )

    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création de la catégorie.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle de la catégorie NACE."""
        return f"{self.code} - {self.libelle}" if self.code else self.libelle or str(self.pk)

    class Meta:
        app_label = 'report'
        verbose_name = _("Catégorie Code NACE")
        verbose_name_plural = _("Catégories Code NACE")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['active']),
        ]


class SubCategoryNaceCode(Model):
    """
    Modèle représentant une sous-catégorie de code NACE.
    
    Sous-classification plus détaillée des activités économiques
    appartenant à une catégorie NACE parente.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    category = models.ForeignKey(
        CategoryNaceCode,
        on_delete=models.CASCADE,
        related_name="subcategories",
        verbose_name=_("Catégorie"),
        help_text=_("Catégorie NACE parente à laquelle appartient cette sous-catégorie.")
    )
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant la sous-catégorie NACE.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Description ou nom de la sous-catégorie NACE.")
    )
    active = models.BooleanField(
        _("Actif"),
        default=True,
        help_text=_("Indique si cette sous-catégorie est active dans le système.")
    )
    poids = models.FloatField(
        _("Poids"),
        default=0.0,
        help_text=_("Poids associé à cette sous-catégorie pour les calculs de scoring.")
    )

    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création de la sous-catégorie.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle de la sous-catégorie NACE."""
        return f"{self.code} - {self.libelle}" if self.code else self.libelle or _("Sous-Catégorie Code NACE")

    class Meta:
        app_label = 'report'
        verbose_name = _("Sous-Catégorie Code NACE")
        verbose_name_plural = _("Sous-Catégories Code NACE")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['category', 'code']),
            models.Index(fields=['active']),
        ]


class CategoryNafCode(Model):
    """
    Modèle représentant une catégorie de code NAF (Nomenclature d'Activités Française).
    
    Utilisé pour classifier les entreprises par secteur d'activité économique
    selon la norme française NAF, adaptation française de la nomenclature NACE.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant la catégorie NAF.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Description ou nom de la catégorie NAF.")
    )
    active = models.BooleanField(
        _("Actif"),
        default=True,
        help_text=_("Indique si cette catégorie est active dans le système.")
    )
    poids = models.FloatField(
        _("Poids"),
        default=0.0,
        help_text=_("Poids associé à cette catégorie pour les calculs de scoring.")
    )

    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création de la catégorie.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle de la catégorie NAF."""
        return f"{self.code} - {self.libelle}" if self.code else self.libelle or _("Catégorie Code NAF")

    class Meta:
        app_label = 'report'
        verbose_name = _("Catégorie Code NAF")
        verbose_name_plural = _("Catégories Code NAF")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['active']),
        ]


class SubCategoryNafCode(Model):
    """
    Modèle représentant une sous-catégorie de code NAF.
    
    Sous-classification plus détaillée des activités économiques
    appartenant à une catégorie NAF parente.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    category = models.ForeignKey(
        CategoryNafCode,
        on_delete=models.CASCADE,
        related_name="subcategories",
        verbose_name=_("Catégorie"),
        help_text=_("Catégorie NAF parente à laquelle appartient cette sous-catégorie.")
    )
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant la sous-catégorie NAF.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Description ou nom de la sous-catégorie NAF.")
    )
    active = models.BooleanField(
        _("Actif"),
        default=True,
        help_text=_("Indique si cette sous-catégorie est active dans le système.")
    )
    poids = models.FloatField(
        _("Poids"),
        default=0.0,
        help_text=_("Poids associé à cette sous-catégorie pour les calculs de scoring.")
    )

    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création de la sous-catégorie.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle de la sous-catégorie NAF."""
        return f"{self.code} - {self.libelle}" if self.code else self.libelle or _("Sous-Catégorie Code NAF")

    class Meta:
        app_label = 'report'
        verbose_name = _("Sous-Catégorie Code NAF")
        verbose_name_plural = _("Sous-Catégories Code NAF")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['category', 'code']),
            models.Index(fields=['active']),
        ]


class FormeJuridique(Model):
    """
    Modèle représentant une forme juridique d'entreprise.
    
    Référentiel des différentes structures juridiques que peut prendre une entreprise
    (SARL, SA, SAS, EI, etc.) avec leurs caractéristiques.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant la forme juridique.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom ou description de la forme juridique.")
    )
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description détaillée de la forme juridique.")
    )
    poids = models.FloatField(
        _("Poids"),
        default=0.0,
        help_text=_("Poids associé à cette forme juridique pour les calculs de scoring.")
    )
    active = models.BooleanField(
        _("Actif"),
        default=True,
        help_text=_("Indique si cette forme juridique est active dans le système.")
    )

    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création de la forme juridique.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle de la forme juridique."""
        return f"{self.code} - {self.libelle}" if self.code else self.libelle or _("Forme juridique")

    class Meta:
        app_label = 'report'
        verbose_name = _("Forme juridique")
        verbose_name_plural = _("Formes juridiques")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['active']),
        ]


class DomaineEntreprise(Model):
    """
    Modèle représentant un domaine d'activité d'entreprise.
    
    Classification générale des secteurs d'activité économique
    (Industrie, Services, Commerce, BTP, etc.).
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le domaine d'entreprise.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Nom du domaine d'activité de l'entreprise.")
    )
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description détaillée du domaine d'activité.")
    )
    active = models.BooleanField(
        _("Actif"),
        default=True,
        help_text=_("Indique si ce domaine est actif dans le système.")
    )

    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du domaine.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du domaine d'entreprise."""
        return f"{self.code} - {self.libelle}" if self.code else self.libelle or _("Domaine entreprise")

    class Meta:
        app_label = 'report'
        verbose_name = _("Domaine entreprise")
        verbose_name_plural = _("Domaines entreprise")
        ordering = ["libelle"]
        indexes = [
            models.Index(fields=['libelle']),
            models.Index(fields=['active']),
        ]


class PosteEntreprise(Model):
    """
    Modèle représentant un poste ou fonction dans une entreprise.
    
    Référentiel des différents postes et fonctions que peuvent occuper
    les employés ou dirigeants dans une entreprise.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    domaine = models.ForeignKey(
        DomaineEntreprise,
        on_delete=models.CASCADE,
        related_name="postes",
        verbose_name=_("Domaine Entreprise"),
        help_text=_("Domaine d'activité auquel ce poste est associé.")
    )
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le poste dans l'entreprise.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Intitulé ou nom du poste dans l'entreprise.")
    )
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description détaillée des responsabilités et attributions du poste.")
    )
    active = models.BooleanField(
        _("Actif"),
        default=True,
        help_text=_("Indique si ce poste est actif dans le système.")
    )

    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du poste.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du poste d'entreprise."""
        if self.domaine and self.libelle:
            return f"{self.libelle} ({self.domaine.libelle})"
        return self.libelle or _("Poste entreprise")

    class Meta:
        app_label = 'report'
        verbose_name = _("Poste entreprise")
        verbose_name_plural = _("Postes entreprise")
        ordering = ["libelle"]
        indexes = [
            models.Index(fields=['domaine', 'libelle']),
            models.Index(fields=['active']),
        ]


class CategorieEntreprise(Model):
    """
    Modèle représentant une catégorie d'entreprise.
    
    Classification des entreprises par taille ou type
    (PME, Grande Entreprise, TPE, Start-up, etc.).
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Code identifiant la catégorie d'entreprise.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom de la catégorie d'entreprise.")
    )
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description détaillée de la catégorie d'entreprise.")
    )
    active = models.BooleanField(
        _("Actif"),
        default=True,
        help_text=_("Indique si cette catégorie est active dans le système.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création de la catégorie.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle de la catégorie d'entreprise."""
        return self.libelle or _("Catégorie d'entreprise")

    class Meta:
        app_label = 'report'
        verbose_name = _("Catégorie d'Entreprise")
        verbose_name_plural = _("Catégories d'Entreprises")
        ordering = ["libelle"]
        indexes = [
            models.Index(fields=['libelle']),
            models.Index(fields=['active']),
        ]


class StructureEntreprise(Model):
    """
    Modèle représentant une structure organisationnelle d'entreprise.
    
    Classification des types de structures organisationnelles
    (Hiérarchique, Matricielle, Divisionnelle, etc.).
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Code identifiant la structure d'entreprise.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom de la structure d'entreprise.")
    )
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description détaillée de la structure d'entreprise.")
    )
    active = models.BooleanField(
        _("Actif"),
        default=True,
        help_text=_("Indique si cette structure est active dans le système.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création de la structure.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle de la structure d'entreprise."""
        return self.libelle or _("Structure d'entreprise")

    class Meta:
        app_label = 'report'
        verbose_name = _("Structure d'Entreprise")
        verbose_name_plural = _("Structures d'Entreprises")
        ordering = ["libelle"]
        indexes = [
            models.Index(fields=['libelle']),
            models.Index(fields=['active']),
        ]


class StatutEntreprise(Model):
    """
    Modèle représentant un statut juridique ou opérationnel d'entreprise.
    
    Référentiel des différents statuts qu'une entreprise peut avoir
    (Active, En liquidation, Dissoute, En redressement judiciaire, etc.).
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Code identifiant le statut d'entreprise.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom du statut d'entreprise.")
    )
    description = models.TextField(
        _("Description"),
        null=True,
        blank=True,
        help_text=_("Description détaillée du statut d'entreprise.")
    )
    active = models.BooleanField(
        _("Actif"),
        default=True,
        help_text=_("Indique si ce statut est actif dans le système.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du statut.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du statut d'entreprise."""
        return self.libelle or _("Statut d'entreprise")

    class Meta:
        app_label = 'report'
        verbose_name = _("Statut d'Entreprise")
        verbose_name_plural = _("Statuts d'Entreprises")
        ordering = ["libelle"]
        indexes = [
            models.Index(fields=['libelle']),
            models.Index(fields=['active']),
        ]


# ============================================================================
# MODÈLES DE MODÈLES ET TEMPLATES
# ============================================================================

class ModeleRapport(Model):
    """
    Modèle représentant un modèle de rapport standardisé.
    
    Template ou structure prédéfinie pour la génération de rapports
    d'analyse d'entreprise.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le modèle de rapport.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom ou description du modèle de rapport.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du modèle.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du modèle de rapport."""
        if self.code and self.libelle:
            return f"{self.code} - {self.libelle}"
        return self.code or self.libelle or _("Modèle de rapport")

    def is_empty(self):
        """Vérifie si le modèle est vide (sans code ni libellé)."""
        return not self.code and not self.libelle

    class Meta:
        app_label = 'report'
        verbose_name = _("Modèle de rapport")
        verbose_name_plural = _("Modèles de rapport")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
        ]


class ModeleAlarme(Model):
    """
    Modèle représentant un modèle d'alarme ou d'alerte.
    
    Template prédéfini pour les règles d'alerte et les notifications
    dans le système de surveillance.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le modèle d'alarme.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom ou description du modèle d'alarme.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du modèle.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du modèle d'alarme."""
        if self.code and self.libelle:
            return f"{self.code} - {self.libelle}"
        return self.code or self.libelle or _("Modèle d'alarme")

    def is_empty(self):
        """Vérifie si le modèle est vide (sans code ni libellé)."""
        return not self.code and not self.libelle

    class Meta:
        app_label = 'report'
        verbose_name = _("Modèle d'alarme")
        verbose_name_plural = _("Modèles d'alarme")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
        ]


class ModeleBilan(Model):
    """
    Modèle représentant un modèle de bilan comptable.
    
    Structure prédéfinie pour la présentation des bilans comptables
    selon différents standards (Classique, Syscohada, Anglais, etc.).
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le modèle de bilan.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom ou description du modèle de bilan.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du modèle.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du modèle de bilan."""
        if self.code and self.libelle:
            return f"{self.code} - {self.libelle}"
        return self.code or self.libelle or _("Modèle de bilan")

    def is_empty(self):
        """Vérifie si le modèle est vide (sans code ni libellé)."""
        return not self.code and not self.libelle

    class Meta:
        app_label = 'report'
        verbose_name = _("Modèle de bilan")
        verbose_name_plural = _("Modèles de bilan")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
        ]


class ModeleBail(Model):
    """
    Modèle représentant un modèle de bail ou contrat de location.
    
    Template prédéfini pour les contrats de location immobilière
    avec poids pour le scoring financier.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le modèle de bail.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom ou description du modèle de bail.")
    )
    poids = models.FloatField(
        _("Poids"),
        default=0.0,
        help_text=_("Poids associé à ce modèle de bail pour les calculs de scoring.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du modèle.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du modèle de bail."""
        if self.code and self.libelle:
            return f"{self.code} - {self.libelle}"
        return self.code or self.libelle or _("Modèle de bail")

    def is_empty(self):
        """Vérifie si le modèle est vide (sans code ni libellé)."""
        return not self.code and not self.libelle

    class Meta:
        app_label = 'report'
        verbose_name = _("Modèle de bail")
        verbose_name_plural = _("Modèles de bail")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
        ]


class ModeleNotation(Model):
    """
    Modèle représentant un modèle de notation ou scoring.
    
    Template prédéfini pour les systèmes de notation et d'évaluation
    des risques d'entreprise.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le modèle de notation.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom ou description du modèle de notation.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du modèle.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du modèle de notation."""
        if self.code and self.libelle:
            return f"{self.code} - {self.libelle}"
        return self.code or self.libelle or _("Modèle de notation")

    def is_empty(self):
        """Vérifie si le modèle est vide (sans code ni libellé)."""
        return not self.code and not self.libelle

    class Meta:
        app_label = 'report'
        verbose_name = _("Modèle de notation")
        verbose_name_plural = _("Modèles de notation")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
        ]


class ModeleAvisCommercial(Model):
    """
    Modèle représentant un modèle d'avis commercial.
    
    Template prédéfini pour les avis et recommandations commerciales
    avec poids pour l'influence sur les décisions.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le modèle d'avis commercial.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom ou description du modèle d'avis commercial.")
    )
    poids = models.FloatField(
        _("Poids"),
        default=0.0,
        help_text=_("Poids associé à cet avis commercial pour les calculs de scoring.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du modèle.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du modèle d'avis commercial."""
        if self.code and self.libelle:
            return f"{self.code} - {self.libelle}"
        return self.code or self.libelle or _("Modèle d'avis commercial")

    def is_empty(self):
        """Vérifie si le modèle est vide (sans code ni libellé)."""
        return not self.code and not self.libelle

    class Meta:
        app_label = 'report'
        verbose_name = _("Modèle d'avis commercial")
        verbose_name_plural = _("Modèles d'avis commercial")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
        ]


class ModeleRelationEntreprise(Model):
    """
    Modèle représentant un modèle de relation inter-entreprises.
    
    Template prédéfini pour les types de relations entre entreprises
    (Filiale, Sous-traitant, Partenaire, Concurrent, etc.).
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le modèle de relation entreprise.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom ou description du modèle de relation entreprise.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du modèle.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du modèle de relation entreprise."""
        if self.code and self.libelle:
            return f"{self.code} - {self.libelle}"
        return self.code or self.libelle or _("Modèle de relation entreprise")

    def is_empty(self):
        """Vérifie si le modèle est vide (sans code ni libellé)."""
        return not self.code and not self.libelle

    class Meta:
        app_label = 'report'
        verbose_name = _("Modèle de relation entreprise")
        verbose_name_plural = _("Modèles de relation entreprise")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
        ]


class ModeleInformationNotationEntreprise(Model):
    """
    Modèle représentant un modèle d'information pour la notation d'entreprise.
    
    Template prédéfini pour les informations nécessaires à l'évaluation
    et à la notation des entreprises.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le modèle d'information pour notation.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom ou description du modèle d'information pour notation.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du modèle.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du modèle d'information pour notation."""
        if self.code and self.libelle:
            return f"{self.code} - {self.libelle}"
        return self.code or self.libelle or _("Modèle d'information notation")

    def is_empty(self):
        """Vérifie si le modèle est vide (sans code ni libellé)."""
        return not self.code and not self.libelle

    class Meta:
        app_label = 'report'
        verbose_name = _("Modèle d'information sur notation entreprise")
        verbose_name_plural = _("Modèles d'information sur notation entreprise")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
        ]


class ModeleComportementPaiement(Model):
    """
    Modèle représentant un modèle de comportement de paiement.
    
    Template prédéfini pour les types de comportements de paiement
    observés chez les clients (Bon payeur, Retardataire, etc.)
    avec poids pour le scoring de risque.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le modèle de comportement de paiement.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom ou description du modèle de comportement de paiement.")
    )
    poids = models.FloatField(
        _("Poids"),
        default=0.0,
        help_text=_("Poids associé à ce comportement pour les calculs de scoring.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du modèle.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du modèle de comportement de paiement."""
        if self.code and self.libelle:
            return f"{self.code} - {self.libelle}"
        return self.code or self.libelle or _("Modèle comportement paiement")

    def is_empty(self):
        """Vérifie si le modèle est vide (sans code ni libellé)."""
        return not self.code and not self.libelle

    class Meta:
        app_label = 'report'
        verbose_name = _("Modèle de comportement de paiement")
        verbose_name_plural = _("Modèles de comportement de paiement")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
        ]


class ModeleComportementJugement(Model):
    """
    Modèle représentant un modèle de comportement judiciaire.
    
    Template prédéfini pour les types de comportements judiciaires
    (Litige, Procédure, Jugement défavorable, etc.).
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le modèle de comportement de jugement.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom ou description du modèle de comportement de jugement.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du modèle.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du modèle de comportement de jugement."""
        if self.code and self.libelle:
            return f"{self.code} - {self.libelle}"
        return self.code or self.libelle or _("Modèle comportement jugement")

    def is_empty(self):
        """Vérifie si le modèle est vide (sans code ni libellé)."""
        return not self.code and not self.libelle

    class Meta:
        app_label = 'report'
        verbose_name = _("Modèle de comportement de jugement")
        verbose_name_plural = _("Modèles de comportement de jugement")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
        ]


class ModeleAgeSociete(Model):
    """
    Modèle représentant un modèle d'âge de société.
    
    Template prédéfini pour les catégories d'âge des entreprises
    (Jeune, Moyenne, Ancienne, etc.) avec poids pour le scoring.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le modèle d'âge de société.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom ou description du modèle d'âge de société.")
    )
    poids = models.FloatField(
        _("Poids"),
        default=0.0,
        help_text=_("Poids associé à cette catégorie d'âge pour les calculs de scoring.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du modèle.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du modèle d'âge de société."""
        if self.code and self.libelle:
            return f"{self.code} - {self.libelle}"
        return self.code or self.libelle or _("Modèle d'âge de société")

    def is_empty(self):
        """Vérifie si le modèle est vide (sans code ni libellé)."""
        return not self.code and not self.libelle

    class Meta:
        app_label = 'report'
        verbose_name = _("Modèle d'age de société")
        verbose_name_plural = _("Modèles d'age de société")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
        ]


class ModeleInterpretationScoringSansBilan(Model):
    """
    Modèle représentant un modèle d'interprétation de scoring sans bilan.
    
    Template prédéfini pour l'interprétation des scores de risque
    lorsque les bilans financiers ne sont pas disponibles.
    """
    
    safedelete_policy = SOFT_DELETE_CASCADE
    
    code = models.CharField(
        _("Code"),
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Code unique identifiant le modèle d'interprétation.")
    )
    libelle = models.CharField(
        _("Libellé"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Nom ou description du modèle d'interprétation.")
    )
    poids = models.FloatField(
        _("Poids"),
        default=0.0,
        help_text=_("Poids associé à cette interprétation pour les calculs.")
    )
    
    created_at = models.DateTimeField(
        _("Date de Création"),
        auto_now_add=True,
        help_text=_("Date et heure de création du modèle.")
    )
    updated_at = models.DateTimeField(
        _("Date de Mise à Jour"),
        auto_now=True,
        help_text=_("Date et heure de la dernière mise à jour.")
    )
    
    history = HistoricalRecords()
    
    def __str__(self):
        """Représentation textuelle du modèle d'interprétation."""
        if self.code and self.libelle:
            return f"{self.code} - {self.libelle}"
        return self.code or self.libelle or _("Modèle interpretation scoring")

    def is_empty(self):
        """Vérifie si le modèle est vide (sans code ni libellé)."""
        return not self.code and not self.libelle

    class Meta:
        app_label = 'report'
        verbose_name = _("Modèle interpretation scoring sans bilan")
        verbose_name_plural = _("Modèles interpretations scoring sans bilan")
        ordering = ["code"]
        indexes = [
            models.Index(fields=['code']),
        ]






# ============================================================================
# NOTES ET RECOMMANDATIONS
# ============================================================================

"""
RECOMMANDATIONS POUR L'ÉVOLUTION DU MODÈLE:

1. SÉCURITÉ:
   - Ajouter un champ `last_login_ip` pour tracer les connexions
   - Implémenter une politique d'expiration des mots de passe
   - Ajouter un compteur de tentatives de connexion échouées

2. PERFORMANCE:
   - Ajouter des index sur les champs fréquemment interrogés:
     * `username`, `email`, `role`
     * `activation`, `is_client`

3. VALIDATION:
   - Ajouter des validateurs Regex pour le champ `phone`
   - Implémenter des contraintes de complexité pour les mots de passe

4. INTERNATIONALISATION:
   - S'assurer que tous les `help_text` sont traduits
   - Ajouter des traductions pour les choix `ROLES_USERS`

5. INTÉGRITÉ DES DONNÉES:
   - Vérifier la cohérence entre `role` et `is_client`
   - Ajouter des signaux pour maintenir la cohérence des relations

6. DOCUMENTATION:
   - Documenter les relations avec le modèle `Pays`
   - Ajouter des exemples d'utilisation dans les docstrings
"""