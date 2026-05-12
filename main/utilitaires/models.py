from django.db import models
from django.utils.translation import gettext_lazy as _

from main.utilitaires.constantes import *

# Create your models here.


class RiskRating(models.Model):

    acheteur = models.ForeignKey("Acheteur", null=True, on_delete=models.DO_NOTHING)
    remboursabilite = models.BooleanField(default=False)
    situation_liquidite = models.BooleanField(default=False)
    performance_rentabilite = models.BooleanField(default=False)
    perspective_secteur = models.BooleanField(default=False)
    qualite_information_analyse = models.BooleanField(default=False)
    existence_garantie = models.BooleanField(default=False)
    terme_financier_duree_pret = models.BooleanField(default=False)
    mesure_propre_soutenir_credit = models.BooleanField(default=False)
    interpretation = models.TextField(blank=True, max_length=10000000)
    analyse = models.TextField(blank=True, max_length=10000000)

    def __str__(self):
        return "risk_rating: %d, %s" % (self.pk, self.acheteur)


class Resume(models.Model):

    acheteur = models.ForeignKey(
        "Acheteur", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    devise = models.ForeignKey(
        "Devise",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name="Dévise capital social",
        related_name="devise_capital_social",
    )
    capital_social = models.DecimalField(
        max_digits=100, decimal_places=0, blank=True, null=True
    )
    chiffre_affaire = models.DecimalField(
        max_digits=100, decimal_places=0, blank=True, null=True
    )
    resultat_net = models.DecimalField(
        max_digits=100, decimal_places=0, blank=True, null=True
    )
    capitaux_propre = models.DecimalField(
        max_digits=100, decimal_places=0, blank=True, null=True
    )
    nombre_employe = models.DecimalField(
        max_digits=100, decimal_places=0, blank=True, null=True
    )
    date_creation = models.DateField(null=True, blank=True)
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    commentaire = models.TextField(blank=True, max_length=10000000)


class DonneesEnregistrement(models.Model):

    acheteur = models.ForeignKey(
        "Acheteur", null=True, on_delete=models.DO_NOTHING, blank=True
    )
    date_creation = models.DateField(blank=True, null=True)
    date_registre = models.DateField(blank=True, null=True)
    forme_juridique = models.CharField(
        max_length=4000,
        choices=FORMEJURIDIQUE_CHOICES,
        default="Veuillez choisir la forme juridique",
    )
    nouvelle_forme_juridique = models.ForeignKey(
        "FormeJuridique",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donnees_enregistrement_acheteur",
        verbose_name=_("Forme Juridique"),
        help_text=_("Forme juridique de l'entreprise"),
    )
    numero_registre_commerce = models.CharField(max_length=50, blank=True)
    numero_fiscale = models.CharField(max_length=100, blank=True)
    statut_registre = models.CharField(
        max_length=4000, choices=LIEN_STATUT_CHOICE, default="--------"
    )
    nouveau_statut_registre = models.ForeignKey(
        "StatutEntreprise",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="statut_entreprise_acheteur",
        verbose_name=_("Statut Acheteur"),
        help_text=_("Statut actuel de l'acheteur"),
    )
    nom_anterieur = models.CharField(max_length=100, blank=True)
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    commentaire = models.TextField(max_length=10000000, blank=True)


class Tendance(models.Model):

    acheteur = models.ForeignKey("Acheteur", null=True, on_delete=models.DO_NOTHING)
    avis_commercial = models.CharField(
        max_length=100, choices=LIEN_AVIS_COMMERCIAL_CHOICE, blank=True
    )
    nouvel_avis_commercial = models.ForeignKey(
        "AvisCommercial",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avis_commercial_acheteur",
        verbose_name=_("Avis Commercial Acheteur"),
        help_text=_("Avis commercial sur l'acheteur"),
    )
    plus_informations = models.CharField(
        max_length=100,
        choices=LIEN_PLUS_INFORMATIONS_NOTATION_CHOICE,
        blank=True,
        verbose_name="Plus d'informations sur la notation ",
    )
    ajout_plus_informations = models.ForeignKey(
        "ModeleNotation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plus_informations_acheteur",
        verbose_name=_("Plus d'informations sur l'acheteur"),
        help_text=_("Plus d'informations sur l'acheteur"),
    )
    presse_media = models.CharField(
        max_length=100, blank=True, verbose_name="Presse/Medias"
    )
    alarmes = models.CharField(max_length=100, choices=LIEN_ALARMES_CHOICE, blank=True)
    ajout_alarmes = models.ForeignKey(
        "ModeleAlarme",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alarmes_acheteur",
        verbose_name=_("Alarme sur l'acheteur"),
        help_text=_("Alarme sur l'acheteur"),
    )
    principaux_concurrent = models.TextField(
        blank=True, max_length=10000000, verbose_name="Principaux concurrents"
    )
    commentaire = models.TextField(max_length=10000000, blank=True)


class ResponsableAcheteur(models.Model):

    STATUS_MASCULIN = "Masculin"
    STATUS_FEMININ = "Feminin"
    STATUS_CHOICES = ((STATUS_MASCULIN, "Masculin"), (STATUS_FEMININ, "Feminin"))
    acheteur = models.ForeignKey(
        "Acheteur", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    nom = models.CharField(max_length=50, blank=True, null=True)
    prenom = models.CharField(max_length=50, blank=True, null=True)
    Sexe = models.CharField(
        max_length=20,
        default=STATUS_MASCULIN,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
    )
    poste = models.CharField(
        max_length=100, choices=BON_POST_CHOICES_CHOICES, blank=True
    )
    nationalite = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    commentaire = models.TextField(blank=True, max_length=10000000)


class AntecedantsJuridique(models.Model):

    acheteur = models.ForeignKey(
        "Acheteur", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    dossier_faillite = models.CharField(max_length=100, blank=True)
    jugement_cour = models.CharField(max_length=100, blank=True)
    antecedant_redressement = models.CharField(max_length=100, blank=True)
    Autre = models.CharField(max_length=100, blank=True)
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    commentaire = models.TextField(max_length=10000000, blank=True, null=True)


class RiskManagment(models.Model):

    STATUS_AUCUN = "Aucun"
    STATUS_OUI = "Oui"
    STATUS_NON = "Non"
    STATUS_CHOICES = ((STATUS_AUCUN, ""), (STATUS_OUI, True), (STATUS_NON, False))
    acheteur = models.ForeignKey("Acheteur", null=True, on_delete=models.DO_NOTHING)
    professionalisme = models.CharField(
        max_length=20,
        default=STATUS_AUCUN,
        choices=STATUS_CHOICES,
        verbose_name="Professionalisme",
    )
    organisation = models.CharField(
        max_length=20, default=STATUS_AUCUN, choices=STATUS_CHOICES
    )
    turn_over = models.CharField(
        max_length=20,
        default=STATUS_AUCUN,
        choices=STATUS_CHOICES,
        verbose_name="Non départ des employés",
    )
    greve = models.CharField(
        max_length=20,
        default=STATUS_AUCUN,
        choices=STATUS_CHOICES,
        verbose_name="Non grève",
    )
    degradation_qualite = models.CharField(
        max_length=20,
        default=STATUS_AUCUN,
        choices=STATUS_CHOICES,
        verbose_name="Non dégradation de la qualité du travail",
    )
    non_respect_condition = models.CharField(
        max_length=20,
        default=STATUS_AUCUN,
        choices=STATUS_CHOICES,
        verbose_name="Respect des Employés",
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    commentaire = models.TextField(blank=True, max_length=10000000)


class ConseilAdministration(models.Model):

    acheteur = models.ForeignKey(
        "Acheteur", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    nom = models.CharField(max_length=100, default="Neant", blank=True)
    fonction_dans_le_conseil = models.CharField(
        max_length=100, choices=BON_POST_CHOICES_CHOICES, blank=True
    )
    numero_adresse = models.CharField(
        max_length=200, blank=True, verbose_name="Numéro adresse"
    )
    rue_adresse = models.CharField(
        max_length=200, blank=True, verbose_name="Rue adresse"
    )
    code_postale_adresse = models.CharField(
        max_length=200, blank=True, verbose_name="Code postal adresse"
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    commentaire = models.TextField(blank=True, max_length=10000000)


class CompositionCapitalSocial(models.Model):

    acheteur = models.ForeignKey(
        "Acheteur", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    devise = models.ForeignKey(
        "Devise",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        verbose_name="Dévise capital libéré",
    )
    emis = models.DecimalField(max_digits=100, decimal_places=5, blank=True, null=True)
    publie = models.DecimalField(
        max_digits=100, decimal_places=5, blank=True, null=True
    )
    libere = models.DecimalField(
        max_digits=100, decimal_places=5, blank=True, null=True
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    commentaire = models.TextField(blank=True, max_length=10000000)


class CompositionAction(models.Model):

    acheteur = models.ForeignKey(
        "Acheteur", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    nom = models.CharField(blank=True, max_length=200)
    prenom = models.CharField(blank=True, max_length=200)
    pourcentage = models.DecimalField(
        max_digits=100, decimal_places=5, blank=True, null=True
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    commentaire = models.TextField(blank=True, max_length=10000000)


class Structure(models.Model):

    acheteur = models.ForeignKey(
        "Acheteur", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    nom = models.CharField(blank=True, max_length=200)
    type_affiliation = models.CharField(
        max_length=100, choices=LIEN_ENTREPRISE_CHOICE, blank=True
    )
    numero_adresse = models.CharField(
        max_length=200, blank=True, verbose_name="Numéro adresse"
    )
    rue_adresse = models.CharField(
        max_length=200, blank=True, verbose_name="Rue adresse"
    )
    code_postale_adresse = models.CharField(
        max_length=200, blank=True, verbose_name="Code postal adresse"
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    commentaire = models.TextField(blank=True, max_length=10000000)


class AnalyseSectorielle(models.Model):

    acheteur = models.ForeignKey(
        "Acheteur", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    commentaire = models.TextField(max_length=10000000, blank=True)
    impact_covid_19 = models.TextField(max_length=10000000, blank=True)


class CompteFinancier(models.Model):

    XAF = "XAF"
    XOF = "XOF"
    EUR = "EUR"
    USD = "USD"
    CHF = "CHF"
    STATUS_CHANGE = (
        (XAF, "XAF"),
        (XOF, "XOF"),
        (EUR, "EUR"),
        (USD, "USD"),
        (CHF, "CHF"),
    )

    acheteur = models.ForeignKey(
        "Acheteur", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    cabinet = models.CharField(blank=True, max_length=200)
    requis_pour_deposer = models.CharField(blank=True, max_length=200)
    credibilite_cabinet = models.CharField(
        blank=True,
        max_length=200,
        choices=STATUS__OUI_NON,
        verbose_name="Crédibilité du cabinet pour ACREMAC",
    )
    source = models.CharField(blank=True, max_length=200)
    presentation = models.CharField(blank=True, max_length=200)
    date_compte = models.DateField(
        blank=True, verbose_name="Début de période de compte N"
    )
    date_fin = models.DateField(
        blank=True, null=True, verbose_name="Fin clôture de compte N"
    )
    date_compte_n_moins_un = models.DateField(
        blank=True, null=True, verbose_name="Début de période de compte N-1"
    )
    date_fin_n_moins_un = models.DateField(
        blank=True, null=True, verbose_name="Fin clôture de compte N-1"
    )
    date_compte_n_moins_deux = models.DateField(
        blank=True, null=True, verbose_name="Début de période de compte N-2"
    )
    date_fin_n_moins_deux = models.DateField(
        blank=True, null=True, verbose_name="Fin clôture de compte N-2"
    )
    type_compte = models.CharField(blank=True, max_length=200, null=True)
    devise = models.CharField(
        max_length=20, default=XAF, choices=STATUS_CHANGE, blank=True
    )
    type_bilan = models.CharField(
        max_length=255, choices=LIEN_TYPE_BILAN_CHOICE, default="--------"
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    commentaire = models.TextField(blank=True, max_length=10000000)


class OperationEtHistorique(models.Model):

    acheteur = models.ForeignKey(
        "Acheteur", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    commentaire_ratios = models.CharField(max_length=10000000, blank=True)
    description_complete_activite = models.CharField(max_length=10000000, blank=True)
    importation = models.CharField(max_length=10000000, blank=True)
    historique = models.TextField(blank=True)


class ProprieteEtActif(models.Model):

    acheteur = models.ForeignKey(
        "Acheteur", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    locaux = models.CharField(
        max_length=255, choices=LIEN_COMPORTEMENT_PREMISES_CHOICE, blank=True
    )
    branche = models.CharField(max_length=255, blank=True)


class ConditionAchat(models.Model):

    acheteur = models.ForeignKey(
        "Acheteur", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    local = models.CharField(max_length=255, blank=True)
    importation = models.CharField(max_length=10000000, blank=True)
    les_clients = models.CharField(max_length=10000000, blank=True)
    fournisseur = models.TextField(max_length=10000000, blank=True)


class ConditionDeVente(models.Model):

    acheteur = models.ForeignKey(
        "Acheteur", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    local = models.CharField(max_length=255, blank=True)
    recouvrement_de_dette_jugement = models.CharField(
        max_length=255, choices=LIEN_COMPORTEMENT_JUGEMENT_CHOICE, default="--------"
    )
    ajout_recouvrement_de_dette_jugement = models.ForeignKey(
        "ModeleComportementJugement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ajout_recouvrement_de_dette_jugement_condition_vente",
        verbose_name=_("Modele de comportement de jugement pour la condition de vente"),
        help_text=_("Modele de comportement de jugement pour la condition de vente"),
    )
    comportement_de_paiement = models.CharField(
        max_length=255, choices=LIEN_COMPORTEMENT_PAIEMENT_CHOICE, default="--------"
    )
    ajout_comportement_de_paiement = models.ForeignKey(
        "ModeleComportementPaiement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ajout_comportement_de_paiement_condition_vente",
        verbose_name=_("Modele de comportement de paiement pour la condition de vente"),
        help_text=_("Modele de comportement de paiement pour la condition de vente"),
    )


class SommaireEtAvis(models.Model):

    acheteur = models.ForeignKey(
        "Acheteur", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    couleur_commentaire = models.ForeignKey(
        "CouleurCommentaire", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    commentaire = models.TextField(max_length=10000000, blank=True)


class Advice(models.Model):

    acheteur = models.ForeignKey("Acheteur", on_delete=models.DO_NOTHING)
    points_forts = models.TextField(max_length=10000000, blank=True)
    points_faibles = models.TextField(max_length=10000000, blank=True)
    dynamisme_court_terme = models.TextField(max_length=10000000, blank=True)
    dynamisme_long_terme = models.TextField(max_length=10000000, blank=True)


class Geopolitics(models.Model):

    acheteur = models.ForeignKey("Acheteur", on_delete=models.DO_NOTHING)
    donnees_politiques = models.TextField(max_length=10000000, blank=True)
    donnees_economiques = models.TextField(max_length=10000000, blank=True)


class OpinionCreditAcremac(models.Model):

    acheteur = models.ForeignKey("Acheteur", on_delete=models.DO_NOTHING)
    risque_de_defaut = models.BooleanField(default=False)
    risque_de_concentration_credit = models.BooleanField(default=False)
    risque_de_reputation = models.BooleanField(default=False)
    risque_pays = models.BooleanField(default=False)
    risque_de_taux_dinteret = models.BooleanField(default=False)
    risque_de_liquidite = models.BooleanField(default=False)
    risque_eleve = models.BooleanField(default=False)
    risque_moyen = models.BooleanField(default=False)
    risque_faible = models.BooleanField(default=False)


##############################################################################
##############################################################################
