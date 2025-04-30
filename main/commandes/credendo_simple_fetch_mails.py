import imaplib
import email
from email.policy import default
import re
from datetime import datetime
from django.utils.timezone import make_aware
from main.models import CredendoCommande  # Adapter le chemin vers ton modèle

# Configurer la connexion à l'IMAP
EMAIL_HOST = "imap.gmail.com"  # Modifier selon ton fournisseur
EMAIL_USER = "bucrepcontact@gmail.com"
EMAIL_PASS = "sstowojejndggzxc"

def extract_data_from_email(email_body):
    """
    Extrait les informations du corps de l'email en utilisant des regex.
    """
    data = {
        "reference": re.search(r"Our references:\s*\[(.*?)\]", email_body),
        "internal_bp_id": re.search(r"Internal BP id:\s*(\d+)", email_body),
        "nom": re.search(r"Name\(s\):\s*(.+)", email_body),
        "rue": re.search(r"Street:\s*(.+)", email_body),
        "ville": re.search(r"City:\s*(.+)", email_body),
        "pays": re.search(r"Country:\s*(.+)", email_body),
        "remarque": re.search(r"Remark on the request\s*:\s*(.+)?", email_body),
        "priorite": re.search(r"Priority\s*:\s*(\w+)", email_body),
        "montant": re.search(r"receive your credit advice for an amount up to (\d+,\d+|\d+)", email_body),
    }

    for key, match in data.items():
        data[key] = match.group(1).strip() if match else None

    # Extraire devise et convertir le montant
    if data["montant"]:
        montant_split = data["montant"].replace(",", ".").split(" ")
        data["montant"] = float(montant_split[0])
        data["devise"] = montant_split[1] if len(montant_split) > 1 else "EUR"

    return data

def fetch_emails():
    """
    Récupère les nouveaux emails et enregistre les commandes dans la base de données.
    """
    try:
        mail = imaplib.IMAP4_SSL(EMAIL_HOST)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")  # Modifier si nécessaire

        # Rechercher les emails non lus
        status, messages = mail.search(None, 'UNSEEN')

        for num in messages[0].split():
            status, msg_data = mail.fetch(num, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1], policy=default)
                    email_id = msg["Message-ID"]
                    date_reception = make_aware(datetime.strptime(msg["Date"], "%a, %d %b %Y %H:%M:%S %z"))

                    # Vérifier si l'email a déjà été traité
                    if CredendoCommande.objects.filter(email_id=email_id).exists():
                        continue

                    # Extraire le texte de l'email
                    email_body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                email_body = part.get_payload(decode=True).decode("utf-8")
                                break
                    else:
                        email_body = msg.get_payload(decode=True).decode("utf-8")

                    # Extraire les données
                    extracted_data = extract_data_from_email(email_body)
                    extracted_data["email_id"] = email_id
                    extracted_data["texte_complet"] = email_body
                    extracted_data["date_reception"] = date_reception

                    # Créer et enregistrer la commande
                    CredendoCommande.objects.create(**extracted_data)

                    print(f"Commande enregistrée : {extracted_data['reference']}")

        mail.logout()
    except Exception as e:
        print(f"Erreur lors de la récupération des emails : {e}")

