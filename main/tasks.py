from celery import shared_task
from commandes.credendo_fetch_mails import fetch_new_emails

@shared_task
def check_new_emails():
    fetch_new_emails()
