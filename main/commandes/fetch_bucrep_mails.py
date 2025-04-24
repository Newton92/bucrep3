# utils.py
import os
from django.conf import settings
from django.db import connections, OperationalError
import imapclient
import email
from email.header import decode_header
import email
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import imapclient
from django.conf import settings
import re
from datetime import datetime
from babel.dates import format_datetime

from datetime import datetime
from babel.dates import format_datetime
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime
import datetime
import random
import string
from datetime import datetime
from main.models import CredendoCommande
from django.utils.timezone import now
import re
from django.utils.dateparse import parse_datetime
from decimal import Decimal


#####################################################################################
#                                                                                   #
#   GESTION EMAIL                                                                   #
#                                                                                   #
#####################################################################################
# inbox = get_emails_from_folder('INBOX')
# drafts = get_emails_from_folder('[Gmail]/Brouillons')
# spam = get_emails_from_folder('[Gmail]/Spam')
# trash = get_emails_from_folder('[Gmail]/Trash')
# sent = get_emails_from_folder('[Gmail]/Messages envoyés')

# Appel de la fonction pour lister les dossiers
#folders = list_folders()
#for folder in folders:
#    print(folder)

def format_date(date_string):
    # Remove timezone in parentheses, e.g., (PDT)
    date_string = re.sub(r'\s*\(.*?\)', '', date_string)
    try:
        date_obj = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %Z')
    except ValueError:
        date_obj = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %z')
    return format_datetime(date_obj, 'EEEE, d MMMM yyyy à HH:mm:ss', locale='fr_FR')

def extract_name(email_string):
    match = re.match(r'(.+?) <.+>', email_string)
    if match:
        return match.group(1)
    return email_string

def extract_bracket_content(subject):
    match = re.search(r'\[.*?\]', subject)
    if match:
        return match.group(0)
    return ''

def list_folders():
    server = imapclient.IMAPClient(settings.EMAIL_HOST, use_uid=True, ssl=True)
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    folders = server.list_folders()
    server.logout()
    return folders


def get_fetch_emails():
    return get_emails_from_folder('INBOX')


def get_emails_from_folder(folder_name):
    server = imapclient.IMAPClient(settings.EMAIL_HOST, use_uid=True, ssl=True)
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.select_folder(folder_name)

    messages = server.search(['ALL'])
    emails = []

    for uid, message_data in server.fetch(messages, ['RFC822', 'FLAGS']).items():
        msg = email.message_from_bytes(message_data[b'RFC822'])
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8')
        from_ = msg.get("From")
        from_name = extract_name(from_)
        to = msg.get("To")
        to_name = extract_name(to)
        date = msg.get("Date")
        formatted_date = format_date(date)
        bracket_content = extract_bracket_content(subject)
        is_read = b'\\Seen' in message_data[b'FLAGS']
        body = get_body(msg)
        emails.append({
            "subject": subject,
            "from": from_name,
            "recipient": to_name,
            "received_date": formatted_date,
            "body": body if body else '',
            "attachments": get_attachments(msg),
            "bracket_content": bracket_content,
            "is_read": is_read
        })

    server.logout()
    
    return emails


def get_unread_emails():
    server = imapclient.IMAPClient(settings.EMAIL_HOST, use_uid=True, ssl=True)
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.select_folder('INBOX')

    messages = server.search(['UNSEEN'])
    emails = []

    for uid, message_data in server.fetch(messages, 'RFC822').items():
        msg = email.message_from_bytes(message_data[b'RFC822'])
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8')
        from_ = msg.get("From")
        to = msg.get("To")
        date = msg.get("Date")
        emails.append({
            "subject": subject,
            "from": from_,
            "recipient": to,
            "received_date": date,
            "body": get_body(msg),
            "attachments": get_attachments(msg)
        })

    server.logout()
    return emails

def get_read_emails():
    server = imapclient.IMAPClient(settings.EMAIL_HOST, use_uid=True, ssl=True)
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.select_folder('INBOX')

    messages = server.search(['SEEN'])
    emails = []

    for uid, message_data in server.fetch(messages, 'RFC822').items():
        msg = email.message_from_bytes(message_data[b'RFC822'])
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8')
        from_ = msg.get("From")
        to = msg.get("To")
        date = msg.get("Date")
        emails.append({
            "subject": subject,
            "from": from_,
            "recipient": to,
            "received_date": date,
            "body": get_body(msg),
            "attachments": get_attachments(msg)
        })

    server.logout()
    return emails

def mark_all_as_read():
    server = imapclient.IMAPClient(settings.EMAIL_HOST, use_uid=True, ssl=True)
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.select_folder('INBOX')

    messages = server.search(['UNSEEN'])
    if messages:
        server.add_flags(messages, [imapclient.SEEN])

    server.logout()

def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))

            # skip any text/plain (txt) attachments
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                body = part.get_payload(decode=True)  # decode
                if isinstance(body, bytes):
                    return body.decode('utf-8', errors='replace')
                return body
    else:
        body = msg.get_payload(decode=True)
        if isinstance(body, bytes):
            return body.decode('utf-8', errors='replace')
        return body

def get_attachments(msg):
    attachments = []
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
            continue
        filename = part.get_filename()
        if bool(filename):
            attachments.append({
                "filename": filename,
                "data": part.get_payload(decode=True)
            })
    return attachments



















#####################################################################################
#                                                                                   #
#   TEST EMAIL                                                                      #
#                                                                                   #
#####################################################################################

# Ajouter une méthode pour filtrer les e-mails
def get_emails_from_sender(folder_name, sender_email):
    server = imapclient.IMAPClient(settings.EMAIL_HOST, use_uid=True, ssl=True)
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    server.select_folder(folder_name)

    messages = server.search(['FROM', sender_email])
    emails = []

    for uid, message_data in server.fetch(messages, ['RFC822', 'FLAGS']).items():
        msg = email.message_from_bytes(message_data[b'RFC822'])
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8')
        from_ = msg.get("From")
        to = msg.get("To")
        date = msg.get("Date")
        formatted_date = format_date(date)
        body = get_body(msg)

        # Extraire les données pertinentes du mail
        data = extract_email_data(body)
        if data:
            sender_id = from_  # ou un identifiant unique du mail
            email_id = subject  # ou un identifiant unique du mail
            save_email_to_db(sender_id, email_id, data, formatted_date)

        emails.append({
            "subject": subject,
            "from": from_,
            "recipient": to,
            "received_date": formatted_date,
            "body": body,
        })

    server.logout()
    return emails


# Extraire les informations du mail
# On va créer une fonction extract_email_data() qui va parser le contenu de l'e-mail.
def extract_email_data(body):
    patterns = {
        "reference": r"Our references:\s*\[(.*?)\]",
        "internal_bp_id": r"Internal BP id:\s*(\d+)",
        "nom": r"Name\(s\):\s*(.+)",
        "rue": r"Street:\s*(.+)",
        "ville": r"City:\s*(.+)",
        "pays": r"Country:\s*(\w+)",
        "priorite": r"Priority\s*:\s*(\w+)",
        "montant": r"amount up to ([\d\s.,]+)\s*(\w+)",  # Capture les montants avec espaces ou virgules
    }

    extracted_data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, body, re.MULTILINE)
        if match:
            extracted_data[key] = match.group(1).strip() if len(match.groups()) == 1 else match.groups()

    # Nettoyage du montant et conversion en nombre décimal
    if "montant" in extracted_data:
        montant_brut, devise = extracted_data["montant"]
        
        # Supprimer les espaces insécables et remplacer la virgule par un point
        montant_nettoye = montant_brut.replace("\xa0", "").replace(",", "").strip()
        
        try:
            extracted_data["montant"] = Decimal(montant_nettoye)  # Conversion en Decimal
        except ValueError:
            extracted_data["montant"] = None  # Enregistre None si la conversion échoue

        extracted_data["devise"] = devise

    return extracted_data if extracted_data else None




# Enregistrer les données dans CredendoCommande
# La fonction save_email_to_db() va enregistrer les informations extraites dans le modèle.
def save_email_to_db(sender_id, email_id, data, date_reception):
    # Vérifier si l'email est déjà enregistré
    if CredendoCommande.objects.filter(email_id=email_id).exists():
        print(f"L'email {email_id} est déjà enregistré.")
        return

    commande = CredendoCommande(
        sender_id=sender_id,
        email_id=email_id,
        reference=data.get("reference", ""),
        internal_bp_id=data.get("internal_bp_id", ""),
        nom=data.get("nom", ""),
        identifiants="",
        rue=data.get("rue", ""),
        ville=data.get("ville", ""),
        pays=data.get("pays", ""),
        remarque="",
        priorite=data.get("priorite", ""),
        texte_complet="",  
        montant=data.get("montant", None),
        devise=data.get("devise", None),
        date_reception=now()  # Stocke la date actuelle
    )
    commande.save()
    print(f"Commande enregistrée : {commande}")
    
    
    
# Exécuter la récupération des e-mails
# Enfin, pour lancer la récupération des e-mails et leur enregistrement
def fetch_and_save_emails():
    get_emails_from_sender("INBOX", "yannickabohthierry@gmail.com")

