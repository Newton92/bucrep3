# utils.py
import os
from django.conf import settings
from django.db import connections, OperationalError
import imapclient
import email
from email.header import decode_header
from django.conf import settings
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime
import datetime
import random
import string

from datetime import datetime
import os
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

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings
from django.template.loader import render_to_string

def send_email_with_secret_code(secret_code, subject, from_email, to_emails, cc_emails=None):
    try:
        # Créez l'objet du message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject

        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)
            to_emails += cc_emails  # Ajoutez les emails en copie au destinataire

        # Contenu HTML
        html_content = render_to_string('main/emails/email_with_secret_code.html', {'secret_code': secret_code})
        msg.attach(MIMEText(html_content, 'html'))

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


