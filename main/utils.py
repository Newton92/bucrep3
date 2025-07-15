# utils.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.template.loader import render_to_string

from main.models import *


def send_email_with_secret_code(
    secret_code, subject, from_email, to_emails, cc_emails=None
):
    try:
        # Créez l'objet du message
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject

        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)
            to_emails += cc_emails  # Ajoutez les emails en copie au destinataire

        # Contenu HTML
        html_content = render_to_string(
            "main/emails/email_with_secret_code.html", {"secret_code": secret_code}
        )
        msg.attach(MIMEText(html_content, "html"))

        # Configurez le serveur SMTP
        smtp_server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        smtp_server.ehlo()  # Initialise la connexion SMTP
        smtp_server.starttls()  # Activez la connexion sécurisée
        smtp_server.ehlo()
        smtp_server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

        # Envoyez l'email
        smtp_server.send_message(msg)
        smtp_server.quit()
        print("Email sent successfully")
        return True

    except Exception as e:
        print(f"Failed to send email. Error: {str(e)}")
        return False


from datetime import timedelta

from django.utils import timezone


def check_and_notify(portefeuille, code_evenement, details_evenement):
    # Vérifier si le portefeuille surveille cet événement
    if portefeuille.elements_surveillance_actifs.filter(
        code_interne=code_evenement
    ).exists():
        # Récupérer la dernière date de notification pour ce portefeuille et cet événement
        # Vous devrez stocker cette information quelque part, par exemple dans un modèle `NotificationLog`
        last_notification = (
            NotificationLog.objects.filter(
                portefeuille=portefeuille, code_evenement=code_evenement
            )
            .order_by("-date_notification")
            .first()
        )

        # Déterminer la prochaine date de notification en fonction de la fréquence
        if last_notification:
            if portefeuille.frequence_alertes == "quotidienne":
                next_notification_date = (
                    last_notification.date_notification + timedelta(days=1)
                )
            elif portefeuille.frequence_alertes == "hebdomadaire":
                next_notification_date = (
                    last_notification.date_notification + timedelta(weeks=1)
                )
            elif portefeuille.frequence_alertes == "mensuelle":
                next_notification_date = (
                    last_notification.date_notification + timedelta(days=30)
                )
        else:
            # Si aucune notification précédente, notifier immédiatement
            next_notification_date = timezone.now() - timedelta(days=1)

        # Vérifier si la date actuelle est supérieure ou égale à la prochaine date de notification
        if timezone.now() >= next_notification_date:
            # Envoyer la notification
            send_notification(portefeuille.client, details_evenement)
            # Enregistrer la notification
            NotificationLog.objects.create(
                portefeuille=portefeuille,
                code_evenement=code_evenement,
                date_notification=timezone.now(),
            )


def send_notification(client, details_evenement):
    # Logique pour envoyer la notification (email, message in-app, etc.)
    print(f"Notifier {client.nom} : {details_evenement}")
    # Creer une Alerte, envoyer un email, etc.


# Supposons une fonction qui est appelée quand la raison sociale d'un acheteur change
def handle_acheteur_raison_sociale_changed(
    acheteur_instance, ancienne_raison_sociale, nouvelle_raison_sociale
):
    code_evenement = "COMPANY_NAME_CHANGE"  # Code de l'ElementSurveillance pertinent

    # Trouver les portefeuilles qui suivent cet acheteur
    portefeuilles_clients_concernes = PortefeuilleClient.objects.filter(
        acheteur=acheteur_instance
    )

    for pc_link in portefeuilles_clients_concernes:
        portefeuille = pc_link.portefeuille
        client_a_notifier = portefeuille.client

        # Vérifier si ce portefeuille surveille ce type d'événement
        if portefeuille.elements_surveillance_actifs.filter(
            code_interne=code_evenement
        ).exists():
            # Logique de notification (email, message in-app, etc.)
            print(
                f"Notifier {client_a_notifier.nom} : L'acheteur {acheteur_instance.nom} a changé de raison sociale de '{ancienne_raison_sociale}' à '{nouvelle_raison_sociale}' dans le portefeuille '{portefeuille.nom}'."
            )
            # Creer une Alerte, envoyer un email, etc.
