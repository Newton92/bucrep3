# tasks.py - Tâches Celery pour le système d'alertes

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def surveiller_portefeuilles():
    """
    Tâche principale qui vérifie tous les portefeuilles
    Doit être exécutée quotidiennement
    """
    from .models import Portefeuille

    portefeuilles = Portefeuille.objects.filter(client__actif=True).prefetch_related(
        "portefeuilleclient_set__acheteur"
    )

    for portefeuille in portefeuilles:
        # Vérifier si c'est le moment d'envoyer les alertes
        if _doit_traiter_portefeuille(portefeuille):
            traiter_surveillance_portefeuille.delay(portefeuille.id)


@shared_task
def traiter_surveillance_portefeuille(portefeuille_id):
    """
    Traite la surveillance pour un portefeuille spécifique
    """
    from .models import Portefeuille

    try:
        portefeuille = Portefeuille.objects.get(id=portefeuille_id)

        # Collecter tous les acheteurs du portefeuille
        acheteurs = []
        for pc in portefeuille.portefeuilleclient_set.all():
            acheteurs.append(pc.acheteur)

        # Détecter les changements pour chaque acheteur
        nouveaux_evenements = []
        for acheteur in acheteurs:
            evenements = SurveillanceService.detecter_changements(
                acheteur, portefeuille
            )
            nouveaux_evenements.extend(evenements)

        # Envoyer les alertes si nécessaire
        if nouveaux_evenements:
            envoyer_alertes_portefeuille.delay(
                portefeuille.id, [e.id for e in nouveaux_evenements]
            )

        logger.info(
            f"Surveillance terminée pour le portefeuille {portefeuille.nom}: {len(nouveaux_evenements)} événements détectés"
        )

    except Exception as e:
        logger.error(
            f"Erreur lors de la surveillance du portefeuille {portefeuille_id}: {str(e)}"
        )


@shared_task
def envoyer_alertes_portefeuille(portefeuille_id, evenement_ids):
    """
    Envoie les alertes par email pour un portefeuille
    """
    from .models import EvenementSurveillance, NotificationLog, Portefeuille

    try:
        portefeuille = Portefeuille.objects.get(id=portefeuille_id)
        evenements = EvenementSurveillance.objects.filter(id__in=evenement_ids)

        # Regrouper les événements par type
        evenements_groupes = {}
        for evenement in evenements:
            code = evenement.element_surveillance.code_interne
            if code not in evenements_groupes:
                evenements_groupes[code] = []
            evenements_groupes[code].append(evenement)

        # Préparer le contenu de l'email
        contenu_email = _preparer_contenu_alerte(portefeuille, evenements_groupes)

        # Envoyer l'email
        success = _envoyer_email_alerte(portefeuille.client, contenu_email)

        if success:
            # Marquer les événements comme traités
            evenements.update(
                traite=True, alerte_envoyee=True, date_traitement=timezone.now()
            )

            # Créer log de notification
            for code, events in evenements_groupes.items():
                NotificationLog.objects.create(
                    portefeuille=portefeuille,
                    code_evenement=code,
                    description=f"{len(events)} événement(s) détecté(s)",
                    actif=True,
                )

            logger.info(
                f"Alertes envoyées avec succès pour le portefeuille {portefeuille.nom}"
            )
        else:
            logger.error(
                f"Échec d'envoi des alertes pour le portefeuille {portefeuille.nom}"
            )

    except Exception as e:
        logger.error(
            f"Erreur lors de l'envoi d'alertes pour le portefeuille {portefeuille_id}: {str(e)}"
        )


def _doit_traiter_portefeuille(portefeuille):
    """
    Détermine si un portefeuille doit être traité selon sa fréquence
    """
    from .models import NotificationLog

    maintenant = timezone.now()

    # Récupérer la dernière notification
    derniere_notification = (
        NotificationLog.objects.filter(portefeuille=portefeuille, actif=True)
        .order_by("-date_notification")
        .first()
    )

    if not derniere_notification:
        return True  # Première fois

    delta_depuis_derniere = maintenant - derniere_notification.date_notification

    if portefeuille.frequence_alertes == "quotidienne":
        return delta_depuis_derniere >= timedelta(days=1)
    elif portefeuille.frequence_alertes == "hebdomadaire":
        return delta_depuis_derniere >= timedelta(days=7)
    elif portefeuille.frequence_alertes == "mensuelle":
        return delta_depuis_derniere >= timedelta(days=30)

    return False


def _preparer_contenu_alerte(portefeuille, evenements_groupes):
    """
    Prépare le contenu HTML de l'email d'alerte
    """
    contenu = {
        "portefeuille": portefeuille,
        "client": portefeuille.client,
        "evenements_groupes": evenements_groupes,
        "date_rapport": timezone.now(),
        "total_evenements": sum(len(events) for events in evenements_groupes.values()),
    }

    return contenu


def _envoyer_email_alerte(client, contenu):
    """
    Envoie l'email d'alerte au client
    """
    try:
        sujet = f"Rapport de surveillance - {contenu['portefeuille'].nom}"

        # Rendu du template HTML
        html_message = render_to_string("emails/alerte_surveillance.html", contenu)

        # Message texte simple
        message_text = f"""
        Rapport de surveillance pour le portefeuille: {contenu['portefeuille'].nom}

        {contenu['total_evenements']} événement(s) détecté(s):

        """

        for code, events in contenu["evenements_groupes"].items():
            message_text += (
                f"- {events[0].element_surveillance.nom}: {len(events)} événement(s)\n"
            )

        send_mail(
            subject=sujet,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[client.email],
            html_message=html_message,
            fail_silently=False,
        )

        return True

    except Exception as e:
        logger.error(f"Erreur lors de l'envoi d'email à {client.email}: {str(e)}")
        return False


# management/commands/init_surveillance.py
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Initialise les configurations de surveillance"

    def handle(self, *args, **options):
        from myapp.models import SurveillanceService

        self.stdout.write("Initialisation des configurations de surveillance...")
        SurveillanceService.initialiser_configurations()
        self.stdout.write(
            self.style.SUCCESS(
                "Configurations de surveillance initialisées avec succès"
            )
        )


# signals.py - Pour la surveillance en temps réel (optionnel)
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender="votre_app.Acheteur")
def acheteur_change_handler(sender, instance, created, **kwargs):
    """
    Handler appelé quand un acheteur est modifié
    Déclenche la surveillance en temps réel si nécessaire
    """
    if not created:  # Seulement pour les modifications
        # Récupérer tous les portefeuilles qui surveillent cet acheteur
        from .models import PortefeuilleClient

        portefeuilles_clients = PortefeuilleClient.objects.filter(acheteur=instance)

        for pc in portefeuilles_clients:
            # Déclencher la vérification asynchrone
            from .tasks import traiter_changement_temps_reel

            traiter_changement_temps_reel.delay(
                pc.portefeuille.id, instance.id, "Acheteur"
            )


@receiver(post_save, sender="votre_app.ResponsableAcheteur")
def dirigeant_change_handler(sender, instance, created, **kwargs):
    """
    Handler pour les changements de dirigeants
    """
    if instance.acheteur:
        portefeuilles_clients = PortefeuilleClient.objects.filter(
            acheteur=instance.acheteur
        )

        for pc in portefeuilles_clients:
            # Vérifier si le portefeuille surveille les changements de dirigeants
            if pc.portefeuille.elements_surveillance_actifs.filter(
                code_interne="EXECUTIVE_CHANGE"
            ).exists():
                from .tasks import traiter_changement_temps_reel

                traiter_changement_temps_reel.delay(
                    pc.portefeuille.id, instance.acheteur.id, "ResponsableAcheteur"
                )


@shared_task
def traiter_changement_temps_reel(portefeuille_id, acheteur_id, model_name):
    """
    Traite les changements détectés en temps réel
    """
    from .models import Acheteur, Portefeuille

    try:
        portefeuille = Portefeuille.objects.get(id=portefeuille_id)
        acheteur = Acheteur.objects.get(id=acheteur_id)

        # Pour la surveillance temps réel, on peut soit :
        # 1. Envoyer immédiatement une alerte
        # 2. Marquer pour traitement lors du prochain cycle
        # 3. Accumuler jusqu'à la prochaine fréquence programmée

        # Option 3 recommandée : stocker l'événement pour traitement groupé
        evenements = SurveillanceService.detecter_changements(acheteur, portefeuille)

        if evenements:
            logger.info(
                f"Changement temps réel détecté pour {acheteur.nom} dans {portefeuille.nom}"
            )

    except Exception as e:
        logger.error(f"Erreur lors du traitement temps réel: {str(e)}")


# Scheduler configuration (settings.py ou séparé)
CELERY_BEAT_SCHEDULE = {
    "surveillance-quotidienne": {
        "task": "votre_app.tasks.surveiller_portefeuilles",
        "schedule": crontab(hour=8, minute=0),  # Tous les jours à 8h
    },
    "nettoyage-historique": {
        "task": "votre_app.tasks.nettoyer_historique",
        "schedule": crontab(hour=2, minute=0, day_of_week=1),  # Chaque lundi à 2h
    },
}


@shared_task
def nettoyer_historique():
    """
    Nettoie les anciens historiques pour éviter l'accumulation
    """
    from .models import EvenementSurveillance, HistoriqueDonnees

    # Supprimer les historiques de plus de 6 mois
    limite_date = timezone.now() - timedelta(days=180)

    anciens_historiques = HistoriqueDonnees.objects.filter(date_capture__lt=limite_date)
    count_historiques = anciens_historiques.count()
    anciens_historiques.delete()

    # Supprimer les événements traités de plus de 3 mois
    limite_evenements = timezone.now() - timedelta(days=90)
    anciens_evenements = EvenementSurveillance.objects.filter(
        traite=True, date_traitement__lt=limite_evenements
    )
    count_evenements = anciens_evenements.count()
    anciens_evenements.delete()

    logger.info(
        f"Nettoyage terminé: {count_historiques} historiques et {count_evenements} événements supprimés"
    )


# 1. Créer les migrations
# python manage.py makemigrations

# 2. Appliquer les migrations
# python manage.py migrate

# 3. Initialiser les configurations
# python manage.py init_surveillance

# 4. Configurer Celery beat pour les tâches programmées
# celery -A votre_projet beat --loglevel=info

# 5. Lancer les workers Celery
# celery -A votre_projet worker --loglevel=info
