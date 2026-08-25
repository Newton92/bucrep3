"""
Corrige les enregistrements Pays dont le champ `nom` contient
le code ISO à 2 lettres au lieu du nom complet du pays.

Cause : des commandes d'import antérieures utilisaient get_or_create,
ce qui ne mettait pas à jour `nom` si le record existait déjà.

Usage :
    python manage.py fix_pays_noms
    python manage.py fix_pays_noms --dry-run
"""
import pycountry
from django.core.management.base import BaseCommand
from main.models import Pays


class Command(BaseCommand):
    help = "Corrige les pays dont nom == code (ex : nom='GA' au lieu de 'Gabon')"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche les corrections sans modifier la base de données",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        fixed = 0
        skipped = 0

        for pays in Pays.objects.all():
            if not pays.nom or not pays.code:
                continue

            # Si le nom ressemble déjà au code (ex : "GA" == code "GA"), on corrige
            if pays.nom.strip().upper() == pays.code.strip().upper():
                country = pycountry.countries.get(alpha_2=pays.code.strip().upper())
                if country:
                    proper_name = getattr(country, "name", None) or getattr(
                        country, "official_name", None
                    )
                    if proper_name:
                        if dry_run:
                            self.stdout.write(
                                f"[DRY-RUN] {pays.code} : '{pays.nom}' → '{proper_name}'"
                            )
                        else:
                            Pays.objects.filter(pk=pays.pk).update(nom=proper_name)
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"[CORRIGÉ] {pays.code} : '{pays.nom}' → '{proper_name}'"
                                )
                            )
                        fixed += 1
                        continue

            skipped += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDRY-RUN terminé : {fixed} corrections prévues, {skipped} pays inchangés."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nTerminé : {fixed} pays corrigés, {skipped} pays inchangés."
                )
            )
