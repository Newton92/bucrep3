from celery import shared_task
from commandes.credendo_fetch_mails import fetch_new_credendo_emails
from commandes.bucrepcontact_fetch_mails import fetch_new_bucrepcontact_emails

@shared_task
def check_new_emails():
    fetch_new_credendo_emails()
    fetch_new_bucrepcontact_emails()
