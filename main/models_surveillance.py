# models.py - Extensions nécessaires

import json

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from models import *


class SurveillanceConfiguration(models.Model):
    """
    Configuration qui lie un élément de surveillance à un modèle Django
    et définit les règles de détection des changements
    """

    element_surveillance = models.OneToOneField(
        "ElementSurveillance", on_delete=models.CASCADE, related_name="configuration"
    )

    # Modèle surveillé (ex: Acheteur, ResponsableAcheteur, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    # Champs à surveiller (JSON)
    champs_surveilles = models.JSONField(
        default=list,
        help_text="Liste des champs à surveiller, ex: ['nom', 'email', 'statut_entreprise']",
    )

    # Conditions de déclenchement (JSON)
    conditions = models.JSONField(
        default=dict, help_text="Conditions spécifiques pour déclencher l'alerte"
    )

    # Méthode de détection ('FIELD_CHANGE', 'RECORD_ADDED', 'RECORD_DELETED', 'CUSTOM')
    DETECTION_METHODS = [
        ("FIELD_CHANGE", "Changement de champ"),
        ("RECORD_ADDED", "Ajout d'enregistrement"),
        ("RECORD_DELETED", "Suppression d'enregistrement"),
        ("CUSTOM", "Logique personnalisée"),
    ]

    methode_detection = models.CharField(
        max_length=20, choices=DETECTION_METHODS, default="FIELD_CHANGE"
    )

    # Classe handler personnalisée (optionnel)
    handler_class = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Classe Python pour logique personnalisée",
    )

    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Configuration de Surveillance"
        verbose_name_plural = "Configurations de Surveillance"

    def __str__(self):
        return f"{self.element_surveillance.nom} -> {self.content_type.model}"


class HistoriqueDonnees(models.Model):
    """
    Table pour stocker les snapshots des données surveillées
    """

    # Référence générique vers n'importe quel modèle
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    # Portefeuille concerné
    portefeuille = models.ForeignKey("Portefeuille", on_delete=models.CASCADE)

    # Données au moment de la capture (JSON)
    donnees_snapshot = models.JSONField()

    # Hash pour détecter les changements rapidement
    hash_donnees = models.CharField(max_length=64)

    date_capture = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historique des Données"
        verbose_name_plural = "Historiques des Données"
        indexes = [
            models.Index(fields=["content_type", "object_id", "portefeuille"]),
            models.Index(fields=["date_capture"]),
        ]


class EvenementSurveillance(models.Model):
    """
    Enregistre les événements détectés avant envoi d'alertes
    """

    portefeuille = models.ForeignKey("Portefeuille", on_delete=models.CASCADE)
    element_surveillance = models.ForeignKey(
        "ElementSurveillance", on_delete=models.CASCADE
    )

    # Objet concerné par le changement
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    # Détails de l'événement
    type_evenement = models.CharField(
        max_length=50,
        choices=[
            ("CHANGE", "Modification"),
            ("CREATE", "Création"),
            ("DELETE", "Suppression"),
        ],
    )

    # Données avant/après changement
    donnees_avant = models.JSONField(null=True, blank=True)
    donnees_apres = models.JSONField(null=True, blank=True)

    # Champs qui ont changé
    champs_modifies = models.JSONField(default=list)

    date_evenement = models.DateTimeField(auto_now_add=True)

    # Statut de traitement
    traite = models.BooleanField(default=False)
    alerte_envoyee = models.BooleanField(default=False)
    date_traitement = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Événement de Surveillance"
        verbose_name_plural = "Événements de Surveillance"
        indexes = [
            models.Index(fields=["portefeuille", "traite"]),
            models.Index(fields=["date_evenement"]),
        ]

    def __str__(self):
        return f"{self.element_surveillance.nom} - {self.content_object} - {self.date_evenement}"


# Configuration des éléments de surveillance
SURVEILLANCE_CONFIG = {
    "EXECUTIVE_CHANGE": {
        "model": "ResponsableAcheteur",
        "fields": ["nom", "prenom", "poste", "poste_ref"],
        "method": "RECORD_ADDED",  # Détecte les nouveaux dirigeants
        "description": "Détecte les changements de dirigeants",
    },
    "COMPANY_NAME_CHANGE": {
        "model": "Acheteur",
        "fields": ["nom", "sigle"],
        "method": "FIELD_CHANGE",
        "description": "Détecte les changements de raison sociale",
    },
    "CONTACT_INFO_CHANGE": {
        "model": "Acheteur",
        "fields": ["email", "numero_adresse", "rue_adresse", "code_postal", "ville"],
        "method": "FIELD_CHANGE",
        "description": "Détecte les changements d'adresse et contact",
    },
    "DISSOLUTION": {
        "model": "Acheteur",
        "fields": ["statut_entreprise"],
        "method": "FIELD_CHANGE",
        "conditions": {"statut_entreprise__nom__icontains": "dissol"},
        "description": "Détecte la dissolution d'entreprise",
    },
    # Ajoutez d'autres configurations selon vos besoins
}


# Services pour la surveillance
class SurveillanceService:
    """
    Service principal pour gérer la surveillance
    """

    @staticmethod
    def initialiser_configurations():
        """
        Initialise les configurations de surveillance basées sur SURVEILLANCE_CONFIG
        """
        from django.contrib.contenttypes.models import ContentType

        for code_interne, config in SURVEILLANCE_CONFIG.items():
            try:
                element = ElementSurveillance.objects.get(code_interne=code_interne)

                # Récupérer le ContentType
                app_label = "main"  # Remplacez par le nom de votre app
                model_name = config["model"].lower()
                content_type = ContentType.objects.get(
                    app_label=app_label, model=model_name
                )

                # Créer ou mettre à jour la configuration
                surveillance_config, created = (
                    SurveillanceConfiguration.objects.get_or_create(
                        element_surveillance=element,
                        defaults={
                            "content_type": content_type,
                            "champs_surveilles": config["fields"],
                            "methode_detection": config["method"],
                            "conditions": config.get("conditions", {}),
                        },
                    )
                )

                if created:
                    print(f"Configuration créée pour {code_interne}")

            except ElementSurveillance.DoesNotExist:
                print(f"Élément de surveillance {code_interne} non trouvé")

    @staticmethod
    def capturer_snapshot(acheteur, portefeuille):
        """
        Capture un snapshot des données d'un acheteur pour un portefeuille
        """
        import hashlib

        from django.contrib.contenttypes.models import ContentType

        # Snapshot de l'acheteur
        acheteur_data = {
            "nom": acheteur.nom,
            "email": acheteur.email,
            "statut_entreprise_id": acheteur.statut_entreprise_id,
            "numero_adresse": acheteur.numero_adresse,
            "rue_adresse": acheteur.rue_adresse,
            "code_postal": acheteur.code_postal,
            "ville_id": acheteur.ville_id,
        }

        # Snapshot des dirigeants
        dirigeants_data = []
        for dirigeant in acheteur.responsableacheteur_set.all():
            dirigeants_data.append(
                {
                    "id": dirigeant.id,
                    "nom": dirigeant.nom,
                    "prenom": dirigeant.prenom,
                    "poste": dirigeant.poste,
                    "poste_ref_id": dirigeant.poste_ref_id,
                }
            )

        donnees_completes = {
            "acheteur": acheteur_data,
            "dirigeants": dirigeants_data,
        }

        # Créer hash
        hash_donnees = hashlib.sha256(
            json.dumps(donnees_completes, sort_keys=True).encode()
        ).hexdigest()

        # Sauvegarder snapshot pour l'acheteur
        content_type = ContentType.objects.get_for_model(acheteur)

        HistoriqueDonnees.objects.update_or_create(
            content_type=content_type,
            object_id=acheteur.id,
            portefeuille=portefeuille,
            defaults={
                "donnees_snapshot": donnees_completes,
                "hash_donnees": hash_donnees,
            },
        )

    @staticmethod
    def detecter_changements(acheteur, portefeuille):
        """
        Détecte les changements pour un acheteur dans un portefeuille
        """
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(acheteur)

        # Récupérer le dernier snapshot
        try:
            dernier_historique = HistoriqueDonnees.objects.get(
                content_type=content_type,
                object_id=acheteur.id,
                portefeuille=portefeuille,
            )
        except HistoriqueDonnees.DoesNotExist:
            # Premier snapshot
            SurveillanceService.capturer_snapshot(acheteur, portefeuille)
            return []

        # Capturer l'état actuel
        SurveillanceService.capturer_snapshot(acheteur, portefeuille)

        # Comparer avec le snapshot précédent
        nouveau_historique = HistoriqueDonnees.objects.get(
            content_type=content_type, object_id=acheteur.id, portefeuille=portefeuille
        )

        if dernier_historique.hash_donnees != nouveau_historique.hash_donnees:
            return SurveillanceService._analyser_differences(
                dernier_historique.donnees_snapshot,
                nouveau_historique.donnees_snapshot,
                acheteur,
                portefeuille,
            )

        return []

    @staticmethod
    def _analyser_differences(
        anciennes_donnees, nouvelles_donnees, acheteur, portefeuille
    ):
        """
        Analyse les différences et crée les événements correspondants
        """
        evenements = []

        # Vérifier changements sur l'acheteur
        for champ in [
            "nom",
            "email",
            "statut_entreprise_id",
            "numero_adresse",
            "rue_adresse",
        ]:
            if anciennes_donnees["acheteur"].get(champ) != nouvelles_donnees[
                "acheteur"
            ].get(champ):
                # Créer événement selon le champ modifié
                element_code = SurveillanceService._determiner_element_surveillance(
                    champ
                )
                if (
                    element_code
                    and portefeuille.elements_surveillance_actifs.filter(
                        code_interne=element_code
                    ).exists()
                ):
                    evenement = SurveillanceService._creer_evenement(
                        portefeuille,
                        element_code,
                        acheteur,
                        anciennes_donnees["acheteur"],
                        nouvelles_donnees["acheteur"],
                        [champ],
                    )
                    evenements.append(evenement)

        # Vérifier changements dirigeants
        anciens_dirigeants = {d["id"]: d for d in anciennes_donnees["dirigeants"]}
        nouveaux_dirigeants = {d["id"]: d for d in nouvelles_donnees["dirigeants"]}

        # Nouveaux dirigeants
        nouveaux_ids = set(nouveaux_dirigeants.keys()) - set(anciens_dirigeants.keys())
        if (
            nouveaux_ids
            and portefeuille.elements_surveillance_actifs.filter(
                code_interne="EXECUTIVE_CHANGE"
            ).exists()
        ):
            evenement = SurveillanceService._creer_evenement(
                portefeuille,
                "EXECUTIVE_CHANGE",
                acheteur,
                None,
                list(nouveaux_dirigeants.values()),
                ["dirigeants_ajoutes"],
            )
            evenements.append(evenement)

        return evenements

    @staticmethod
    def _determiner_element_surveillance(champ):
        """
        Détermine l'élément de surveillance basé sur le champ modifié
        """
        mapping = {
            "nom": "COMPANY_NAME_CHANGE",
            "email": "CONTACT_INFO_CHANGE",
            "numero_adresse": "CONTACT_INFO_CHANGE",
            "rue_adresse": "CONTACT_INFO_CHANGE",
            "statut_entreprise_id": "DISSOLUTION",  # Ou autre selon la logique
        }
        return mapping.get(champ)

    @staticmethod
    def _determiner_element_surveillance_model(champ, model_name):
        mapping = {
            "OpinionCreditAcremac": {
                "montant_credit_maximum": "CREDIT_LIMIT_CHANGE",
                "risque_de_defaut": "CREDIT_LIMIT_CHANGE",
                "risque_de_concentration_credit": "CREDIT_LIMIT_CHANGE",
                # Ajoutez d'autres champs et mappings selon vos besoins
            },
            # Ajoutez d'autres modèles et mappings selon vos besoins
        }
        return mapping.get(model_name, {}).get(champ)

    @staticmethod
    def _creer_evenement(
        portefeuille,
        element_code,
        acheteur,
        donnees_avant,
        donnees_apres,
        champs_modifies,
    ):
        """
        Crée un événement de surveillance
        """
        from django.contrib.contenttypes.models import ContentType

        element = ElementSurveillance.objects.get(code_interne=element_code)
        content_type = ContentType.objects.get_for_model(acheteur)

        return EvenementSurveillance.objects.create(
            portefeuille=portefeuille,
            element_surveillance=element,
            content_type=content_type,
            object_id=acheteur.id,
            type_evenement="CHANGE",
            donnees_avant=donnees_avant,
            donnees_apres=donnees_apres,
            champs_modifies=champs_modifies,
        )
