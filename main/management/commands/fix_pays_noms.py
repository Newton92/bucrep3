"""
Corrige les enregistrements Pays dont le champ `nom` contient
le code ISO à 2 lettres au lieu du nom complet du pays.

Deux cas couverts :
  1. nom == code  (ex : nom='GA', code='GA')
  2. nom ressemble à un code court (len <= 3) mais code est différent ou vide
     (ex : nom='GA', code='Gabon' — champs inversés)

Usage :
    python manage.py fix_pays_noms
    python manage.py fix_pays_noms --dry-run
    python manage.py fix_pays_noms --diagnose   # affiche toutes les données sans rien modifier
"""
import pycountry
from django.core.management.base import BaseCommand
from main.models import Pays


class Command(BaseCommand):
    help = "Corrige les pays dont nom == code ou nom ressemble à un code ISO"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche les corrections sans modifier la base de données",
        )
        parser.add_argument(
            "--diagnose",
            action="store_true",
            help="Affiche toutes les données Pays pour diagnostic (lecture seule)",
        )

    def _lookup_country(self, nom, code):
        """Cherche le bon nom via pycountry en essayant le code puis le nom comme code."""
        country = None
        if code and len(code.strip()) == 2:
            country = pycountry.countries.get(alpha_2=code.strip().upper())
        if not country and nom and len(nom.strip()) == 2:
            country = pycountry.countries.get(alpha_2=nom.strip().upper())
        if not country and code and len(code.strip()) == 3:
            country = pycountry.countries.get(alpha_3=code.strip().upper())
        return country

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        diagnose = options["diagnose"]

        if diagnose:
            self.stdout.write(self.style.NOTICE("=== DIAGNOSTIC : enregistrements Pays ==="))
            for pays in Pays.objects.all():
                self.stdout.write(
                    f"  pk={pays.pk:4d}  code={repr(pays.code):12s}  nom={repr(pays.nom)}"
                )
            return

        fixed = 0
        skipped = 0

        for pays in Pays.objects.all():
            nom_raw = (pays.nom or "").strip()
            code_raw = (pays.code or "").strip()

            # Cas 1 : nom == code (ex : nom='GA', code='GA')
            # Cas 2 : nom ressemble à un code court (len <= 3)
            is_suspect = (
                nom_raw.upper() == code_raw.upper()
                or (1 <= len(nom_raw) <= 3 and nom_raw.isalpha())
            )

            if not is_suspect:
                skipped += 1
                continue

            country = self._lookup_country(nom_raw, code_raw)
            if not country:
                self.stdout.write(
                    self.style.WARNING(
                        f"[IGNORÉ] pk={pays.pk} code={repr(code_raw)} nom={repr(nom_raw)} "
                        f"— pays inconnu dans pycountry"
                    )
                )
                skipped += 1
                continue

            proper_name = getattr(country, "name", None) or getattr(country, "official_name", None)
            if not proper_name:
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"[DRY-RUN] pk={pays.pk} code={repr(code_raw)} : {repr(nom_raw)} → {repr(proper_name)}"
                )
            else:
                # On corrige aussi le code si nécessaire
                new_code = country.alpha_2
                update_fields = {"nom": proper_name}
                if code_raw != new_code:
                    update_fields["code"] = new_code
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[CORRIGÉ] pk={pays.pk} : nom {repr(nom_raw)} → {repr(proper_name)}"
                            f", code {repr(code_raw)} → {repr(new_code)}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[CORRIGÉ] pk={pays.pk} code={repr(code_raw)} : "
                            f"nom {repr(nom_raw)} → {repr(proper_name)}"
                        )
                    )
                Pays.objects.filter(pk=pays.pk).update(**update_fields)
            fixed += 1

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
