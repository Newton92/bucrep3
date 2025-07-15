import logging
import smtplib
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction  # Pour les opérations atomiques
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

# Assurez-vous que ces imports sont corrects selon la structure de vos modèles
from .models import AlerteLog, Contact, Portefeuille

logger = logging.getLogger(__name__)

# ---


@shared_task(bind=True)
def send_test_email(self):
    """
    Tâche simple pour envoyer un e-mail de test afin de vérifier la configuration SMTP.
    Utilisé pour le débogage.
    """
    try:
        subject = "Test Email from BUCREP Celery"
        message = (
            "This is a test email sent from a Celery task in your BUCREP application."
        )
        from_email = settings.DEFAULT_FROM_EMAIL
        # Remplacez par une adresse e-mail de test réelle si 'bucrepcontact@gmail.com' n'est pas votre DEFAULT_FROM_EMAIL
        recipient_list = ["yannickabohthierry@gmail.com"]

        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        logger.info(f"Test email sent successfully to {recipient_list}")
        return "Test email sent successfully!"
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending test email: {e}")
        raise self.retry(
            exc=e, countdown=60, max_retries=3
        )  # Réessai en cas d'erreur SMTP
    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        # Ne pas réessayer pour les erreurs non-SMTP, ou définir une stratégie différente
        raise


# ---


@shared_task(bind=True)
def send_monitoring_alerts(self, frequence):
    """
    Tâche Celery pour envoyer les alertes de surveillance par email
    pour les portefeuilles d'une fréquence donnée.
    """
    logger.info(
        f"Démarrage de la tâche send_monitoring_alerts pour la fréquence : {frequence}"
    )

    try:
        # Test de connexion SMTP initial, si vous voulez détecter les problèmes tôt
        try:
            with smtplib.SMTP(
                settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10
            ) as server:
                if settings.EMAIL_USE_TLS:
                    server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                logger.debug("Connexion SMTP réussie pour la tâche d'alertes.")
        except Exception as e:
            logger.error(
                f"Échec de la connexion SMTP pour les alertes ({frequence}): {e}"
            )
            raise self.retry(
                exc=e, countdown=60
            )  # On retente après 60s si le SMTP est down

        # Récupérer les portefeuilles actifs correspondant à la fréquence
        portefeuilles = Portefeuille.objects.filter(
            frequence_alertes=frequence, client__actif=True
        )
        logger.info(
            f"Found {portefeuilles.count()} portefeuilles for frequency '{frequence}'."
        )

        for portefeuille in portefeuilles:
            try:
                client = portefeuille.client
                logger.info(
                    f"Processing portefeuille '{portefeuille.nom}' (Client: {client.nom})."
                )

                # Déterminer la date de début pour récupérer les alertes
                # Si c'est la première vérification, prenez les 7 derniers jours par défaut.
                # Sinon, prenez les alertes depuis la dernière vérification.
                start_date = (
                    portefeuille.derniere_verification
                    if portefeuille.derniere_verification
                    else (timezone.now() - timedelta(days=7))
                )

                # Récupérer les alertes non lues pour ce portefeuille depuis la dernière vérification
                alerts_to_send = AlerteLog.objects.filter(
                    portefeuille=portefeuille, date_creation__gte=start_date, lu=False
                ).order_by("date_creation")

                if not alerts_to_send.exists():
                    logger.info(
                        f"No new alerts to send for portefeuille '{portefeuille.nom}'."
                    )
                    continue

                # Préparation des destinataires de l'email
                recipient_list = [client.email]
                active_contacts_emails = Contact.objects.filter(
                    client=client, actif=True
                ).values_list("email", flat=True)
                for email in active_contacts_emails:
                    if (
                        email and email not in recipient_list
                    ):  # Assurer que l'email n'est pas vide et éviter les doublons
                        recipient_list.append(email)

                if not recipient_list:
                    logger.warning(
                        f"No valid recipients found for portefeuille '{portefeuille.nom}'. Skipping email send."
                    )
                    continue

                # Contexte pour le template d'email
                context = {
                    "client_name": client.nom,
                    "portefeuille_name": portefeuille.nom,
                    "frequence": portefeuille.get_frequence_alertes_display(),
                    "alerts": alerts_to_send,
                    "base_url": "http://bucrep.acremac.net",  # Assurez-vous que cette URL est correcte
                }

                # Rendu du template et envoi de l'email
                subject = f"Alertes de Surveillance BUCREP pour {portefeuille.nom}"
                html_message = render_to_string(
                    "main/emails/monitoring_alerts.html", context
                )
                plain_message = strip_tags(html_message)
                from_email = (
                    settings.DEFAULT_FROM_EMAIL
                )  # Utilisation de l'adresse configurée dans settings.py

                send_mail(
                    subject,
                    plain_message,
                    from_email,
                    recipient_list,
                    html_message=html_message,
                    fail_silently=False,
                )

                logger.info(
                    f"Successfully sent {alerts_to_send.count()} alerts for '{portefeuille.nom}' to {len(recipient_list)} recipients."
                )

                # Marquer les alertes comme lues et mettre à jour la date de dernière vérification du portefeuille
                # Utilisez une transaction atomique pour garantir la cohérence
                with transaction.atomic():
                    alerts_to_send.update(lu=True)
                    portefeuille.derniere_verification = timezone.now()
                    portefeuille.save(update_fields=["derniere_verification"])
                logger.debug(
                    f"Alerts marked as read and portefeuille '{portefeuille.nom}' updated."
                )

            except Exception as e:
                # Loguer l'erreur spécifique pour ce portefeuille, mais continuer avec les autres
                logger.error(
                    f"Error processing portefeuille '{portefeuille.nom}': {e}",
                    exc_info=True,
                )
                # Optionnel: ici, vous pourriez loguer l'erreur dans un modèle d'erreurs pour un suivi ultérieur
                # ou envoyer une notification à un admin.

    except Exception as e:
        logger.critical(
            f"Critical error in send_monitoring_alerts task ({frequence}): {e}",
            exc_info=True,
        )
        # En cas d'erreur critique, demander à Celery de retenter toute la tâche
        raise self.retry(exc=e, countdown=300)  # Réessayer après 5 minutes

    logger.info(
        f"Tâche send_monitoring_alerts pour la fréquence '{frequence}' terminée."
    )
    return True


# ---

# --- Tâche de délégation potentielle pour les alertes de ResponsableAcheteur ---
# Si la sauvegarde de ResponsableAcheteur devient lente.
# Décommentez et adaptez si vous décidez de déplacer la logique.

# @shared_task
# def log_responsable_acheteur_changes(responsable_acheteur_id, changes_data):
#     """
#     Tâche asynchrone pour créer des AlerteLog suite aux changements
#     sur un ResponsableAcheteur.
#     """
#     try:
#         responsable_acheteur = ResponsableAcheteur.objects.get(pk=responsable_acheteur_id)
#     except ResponsableAcheteur.DoesNotExist:
#         logger.error(f"ResponsableAcheteur with ID {responsable_acheteur_id} not found for logging changes.")
#         return

#     logger.info(f"Logging changes for ResponsableAcheteur: {responsable_acheteur}")

#     field_to_element_code = {
#         'nom': 'EXECUTIVE_CHANGE',
#         'prenom': 'EXECUTIVE_CHANGE',
#         'sexe': 'EXECUTIVE_CHANGE',
#         'poste_ref_id': 'EXECUTIVE_CHANGE',
#         'nationalite': 'EXECUTIVE_CHANGE',
#         'commentaire': 'EXECUTIVE_REPUTATION',
#     }

#     # Reconstruire la logique de création d'alertes ici, en utilisant changes_data
#     # changes_data devrait contenir les messages d'alerte déjà formatés
#     # ou les informations nécessaires pour les reconstruire.

#     for element_code, messages in changes_data.items():
#         try:
#             element_surveillance = ElementSurveillance.objects.get(code_interne=element_code)
#             portefeuilles_concernés = Portefeuille.objects.filter(
#                 portefeuilleclient__acheteur=responsable_acheteur.acheteur,
#                 elements_surveillance_actifs=element_surveillance
#             ).distinct()

#             for portefeuille in portefeuilles_concernés:
#                 for message in messages:
#                     AlerteLog.objects.create(
#                         portefeuille=portefeuille,
#                         acheteur=responsable_acheteur.acheteur,
#                         element_surveille=element_surveillance,
#                         message=message,
#                         content_object=responsable_acheteur,
#                         lu=False
#                     )
#                     logger.info(f"Alerte créée pour {responsable_acheteur}: {message}")
#         except ElementSurveillance.DoesNotExist:
#             logger.warning(f"ElementSurveillance with code_interne '{element_code}' not found for {responsable_acheteur}. Skipping alert log.")
#         except Exception as e:
#             logger.error(f"Error creating AlerteLog for {responsable_acheteur}: {e}", exc_info=True)

#     logger.info(f"Finished logging changes for ResponsableAcheteur: {responsable_acheteur}")

# --- Fin de la tâche de délégation potentielle ---
