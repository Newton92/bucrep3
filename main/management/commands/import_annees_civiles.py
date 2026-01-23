from django.core.management.base import BaseCommand
from django.db import transaction

from main.models import Annee


class Command(BaseCommand):
    help = "Importe les années civiles de 2000 à 2026"

    def handle(self, *args, **options):
        start_year = 2000
        end_year = 2026

        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            for year in range(start_year, end_year + 1):
                obj, created = Annee.objects.get_or_create(
                    annee=year,
                    defaults={"is_active": True},
                )

                if created:
                    created_count += 1
                else:
                    skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Import terminé : {created_count} année(s) créée(s), "
            f"{skipped_count} déjà existante(s)."
        ))
