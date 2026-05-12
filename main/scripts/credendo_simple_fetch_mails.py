from django.core.management.base import BaseCommand

from main.commandes.credendo_simple_fetch_mails import fetch_emails


class Command(BaseCommand):
    help = "Récupère les emails de commandes et les stocke en base"

    def handle(self, *args, **kwargs):
        fetch_emails()
