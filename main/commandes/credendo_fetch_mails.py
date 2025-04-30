import imaplib
import email
from email.header import decode_header
from datetime import datetime
import pytz
from main.models import CredendoCommande
import re

EMAIL_HOST = "imap.example.com"
EMAIL_USER = "business.info@acremac.com"
EMAIL_PASS = "mot_de_passe"


def extract_data_from_email(body):
    """
    Extrait les informations du mail et les retourne sous forme de dictionnaire.
    """

    # Extraction des données avec regex
    reference_match = re.search(r"Our references:\s*\[(.*?)\]", body)
    internal_bp_id_match = re.search(r"Internal BP id:\s*(\d+)", body)
    nom_match = re.search(r"Name\(s\):\s*(.*)", body)
    identifiants_match = re.search(r"Identifier\(s\):\s*(.*)", body)
    rue_match = re.search(r"Street:\s*(.*)", body)
    ville_match = re.search(r"City:\s*(.*)", body)
    pays_match = re.search(r"Country:\s*(.*)", body)
    remarque_match = re.search(r"Remark on the request\s*:\s*(.*)", body, re.DOTALL)
    priorite_match = re.search(r"Priority\s*:\s*(\w+)", body)
    
    # Texte après "Priority"
    texte_apres_priorite = re.split(r"Priority\s*:\s*\w+", body, maxsplit=1)[-1].strip() if priorite_match else ""

    # Extraction du montant et devise
    montant_match = re.search(r"an amount up to ([\d,]+)\s*(\w+)", body)

    # Nettoyage et conversion
    montant = float(montant_match.group(1).replace(",", "")) if montant_match else None
    devise = montant_match.group(2) if montant_match else None

    return {
        "reference": reference_match.group(1) if reference_match else None,
        "internal_bp_id": internal_bp_id_match.group(1) if internal_bp_id_match else None,
        "nom": nom_match.group(1).strip() if nom_match else None,
        "identifiants": identifiants_match.group(1).strip() if identifiants_match else None,
        "rue": rue_match.group(1).strip() if rue_match else None,
        "ville": ville_match.group(1).strip() if ville_match else None,
        "pays": pays_match.group(1).strip() if pays_match else None,
        "remarque": remarque_match.group(1).strip() if remarque_match else None,
        "priorite": priorite_match.group(1).strip() if priorite_match else None,
        "texte_complet": texte_apres_priorite,
        "montant": montant,
        "devise": devise
    }


def connect_to_email():
    """ Connexion au serveur IMAP """
    mail = imaplib.IMAP4_SSL(EMAIL_HOST)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")
    return mail

def get_last_email_id():
    """ Récupère l'ID du dernier email traité """
    last_email = CredendoCommande.objects.order_by('-id').first()
    return last_email.email_id if last_email else None

def fetch_new_credendo_emails():
    mail = connect_to_email()
    last_email_id = get_last_email_id()

    status, messages = mail.search(None, 'ALL')
    messages = messages[0].split()

    for num in messages:
        if last_email_id and int(num) <= int(last_email_id):
            continue  # Ignore les emails déjà traités

        _, msg_data = mail.fetch(num, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                # 📅 Récupération de la date de réception
                date_tuple = email.utils.parsedate_tz(msg["Date"])
                if date_tuple:
                    timestamp = email.utils.mktime_tz(date_tuple)
                    date_reception = datetime.fromtimestamp(timestamp, pytz.UTC)  # Conversion UTC

                # 📩 Récupération du contenu du mail
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()

                            # Extraction des données
                            data = extract_data_from_email(body)
                            data["date_reception"] = date_reception  # Ajout de la date de réception

                            if data["reference"]:  # Vérifier qu'on a bien extrait des données
                                CredendoCommande.objects.create(email_id=num, **data)
                                print(f"Commande Credendo enregistrée avec date {date_reception} pour email ID: {num}")

    mail.logout()

if __name__ == "__main__":
    fetch_new_credendo_emails()
