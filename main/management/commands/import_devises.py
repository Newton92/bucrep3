# main/management/commands/import_devises.py

import pycountry
from django.core.management.base import BaseCommand

from main.models import Devise


class Command(BaseCommand):
    help = "Importer les devises (ISO 4217)"

    def handle(self, *args, **options):
        self.stdout.write("💱 Import des devises...")

        count_created = 0
        count_updated = 0

        for currency in pycountry.currencies:
            code = currency.alpha_3

            nom = getattr(currency, "name", code)
            symbole = self.get_symbol(code)

            obj, created = Devise.objects.update_or_create(
                code=code,
                defaults={
                    "nom": nom[:50],
                    "symbole": symbole,
                    "is_active": True,
                },
            )

            if created:
                count_created += 1
            else:
                count_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Import terminé — {count_created} créées, {count_updated} mises à jour"
            )
        )

    def get_symbol(self, code):
        """
        Mapping simple des symboles les plus courants
        (ISO ne fournit pas les symboles)
        """
        symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "CNY": "¥",
            "XAF": "FCFA",
            "XOF": "FCFA",
            "CAD": "$",
            "AUD": "$",
            "CHF": "CHF",
            "NGN": "₦",
            "ZAR": "R",
            "GHS": "₵",
            "MAD": "د.م.",
            "DZD": "دج",
            "TND": "د.ت",
            "EGP": "£",
        }
        return symbols.get(code, "")
