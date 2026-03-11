# main_monitoring/signals.py
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import (AlerteLog, Certification, ElementSurveillance,
                     Notification, Portefeuille, ResponsableAcheteur)

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=ResponsableAcheteur)
def log_responsible_deleted_alert(sender, instance, **kwargs):
    # Vérifiez si l'élément de surveillance KEY_EMPLOYEE_DEPARTURE existe
    try:
        element_surveillance = ElementSurveillance.objects.get(
            code_interne="KEY_EMPLOYEE_DEPARTURE"
        )
    except ElementSurveillance.DoesNotExist:
        print(
            "ATTENTION: ElementSurveillance 'KEY_EMPLOYEE_DEPARTURE' non trouvé pour les suppressions de responsables."
        )
        return

    message = (
        f"Le responsable clé '{instance.nom} {instance.prenom}' "
        f"de l'acheteur '{instance.acheteur.nom}' a été supprimé."
    )

    portefeuilles_concernés = Portefeuille.objects.filter(
        portefeuilleclient__acheteur=instance.acheteur,
        elements_surveillance_actifs=element_surveillance,
    ).distinct()

    for portefeuille in portefeuilles_concernés:
        AlerteLog.objects.create(
            portefeuille=portefeuille,
            acheteur=instance.acheteur,
            element_surveille=element_surveillance,
            message=message,
            content_object=instance,  # L'instance supprimée (attention, l'accès à ses champs pourrait être limité post-delete)
        )
    print(
        f"Alerte de suppression de responsable loggée pour {instance.nom} {instance.prenom}"
    )


@receiver(post_delete, sender=Certification)
def log_certification_loss_alert(sender, instance, **kwargs):
    try:
        element_surveillance = ElementSurveillance.objects.get(
            code_interne="CERTIFICATION_LOSS"
        )
    except ElementSurveillance.DoesNotExist:
        print(
            "ATTENTION: ElementSurveillance 'CERTIFICATION_LOSS' non trouvé pour les suppressions de certifications."
        )
        return

    message = (
        f"La certification '{instance.nom_certification or instance.get_type_certification_display()}' "
        f"de l'acheteur '{instance.acheteur.nom}' a été supprimée."
    )

    portefeuilles_concernés = Portefeuille.objects.filter(
        portefeuilleclient__acheteur=instance.acheteur,
        elements_surveillance_actifs=element_surveillance,
    ).distinct()

    for portefeuille in portefeuilles_concernés:
        AlerteLog.objects.create(
            portefeuille=portefeuille,
            acheteur=instance.acheteur,
            element_surveille=element_surveillance,
            message=message,
            content_object=instance,
        )
    print(f"Alerte de perte de certification loggée pour {instance.nom_certification}")


@receiver(post_save, sender=Notification)
def push_notification_realtime(sender, instance, created, **kwargs):
    """Diffuse la notification au groupe websocket de l'utilisateur."""
    if not created:
        return

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    payload = {
        "id": instance.id,
        "type": instance.type,
        "message": instance.message,
        "is_read": instance.is_read,
        "created_at": instance.created_at.isoformat() if instance.created_at else None,
    }

    try:
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.user_id}",
            {
                "type": "notification_message",
                "notification": payload,
            },
        )
    except Exception as exc:
        # Ne pas casser la transaction DB si le broker WS est indisponible.
        logger.warning("Realtime notification skipped (channel layer unavailable): %s", exc)
