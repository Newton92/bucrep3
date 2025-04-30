from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from main.models import CredendoCommande, CustomUser

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver
from main.models import Notification

@receiver(post_save, sender=CredendoCommande)
def envoyer_email_aux_analystes_et_validateurs(sender, instance, created, **kwargs):
    if created:  # Vérifie si la commande vient d'être créée
        pays_commande = instance.pays  # Récupère le pays de la commande

        # Rechercher les utilisateurs Analyste et Validateur avec le même pays
        utilisateurs_cibles = CustomUser.objects.filter(
            role__in=['Analyste', 'Validateur'],
            pays__code=pays_commande  # Si "pays" est une ForeignKey
        ) | CustomUser.objects.filter(
            role__in=['Analyste', 'Validateur'],
            pays=pays_commande  # Si "pays" est stocké en texte
        )

        if utilisateurs_cibles.exists():
            emails = utilisateurs_cibles.values_list('email', flat=True)  # Récupérer leurs emails

            sujet = "Nouvelle commande enregistrée"
            message = f"Une nouvelle commande a été enregistrée pour {pays_commande}.\n\n"
            message += f"Référence: {instance.reference}\nNom: {instance.nom}\nMontant: {instance.montant} {instance.devise}\n\n"
            message += "Connectez-vous pour plus de détails."

            send_mail(
                sujet,
                message,
                settings.DEFAULT_FROM_EMAIL,
                list(emails),
                fail_silently=False,
            )



def send_ws_notification(user, type_notif, message, commande=None):
    """Envoie une notification en temps réel via WebSockets."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "send_notification",
            "message": message,
            "type": type_notif,
            "commande": commande.notre_ref if commande else None,
        }
    )

@receiver(post_save, sender=Notification)
def notifier_utilisateur(sender, instance, created, **kwargs):
    """Quand une notification est créée, on l'envoie aussi en temps réel."""
    if created:
        send_ws_notification(instance.user, instance.type, instance.message, instance.commande)
