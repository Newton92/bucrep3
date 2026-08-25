# main/management/commands/import_gabon_localites.py

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from main.models import Pays, Province, Ville


class Command(BaseCommand):
    help = "Import du Gabon, de ses provinces et villes principales (SafeDelete compatible)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Supprimer les données existantes avant import (soft delete)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulation sans écriture en base",
        )

    def handle(self, *args, **options):
        clear = options["clear"]
        dry_run = options["dry_run"]

        self.stdout.write(self.style.NOTICE("=== IMPORT GABON LOCALITÉS ==="))

        if clear:
            self.clear_data(dry_run)

        self.import_data(dry_run)

        self.stdout.write(self.style.SUCCESS("✔ Import terminé"))

    # ------------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------------

    GABON_DATA = {
        "pays": {"nom": "Gabon", "code": "GA"},
        "provinces": {
            "EST": {
                "nom": "Estuaire",
                "villes": ["Libreville", "Owendo", "Akanda", "Ntoum"],
            },
            "HO": {
                "nom": "Haut-Ogooué",
                "villes": ["Franceville", "Moanda", "Bakoumba"],
            },
            "MO": {
                "nom": "Moyen-Ogooué",
                "villes": ["Lambaréné", "Ndjolé"],
            },
            "NG": {
                "nom": "Ngounié",
                "villes": ["Mouila", "Fougamou", "Malinga"],
            },
            "NY": {
                "nom": "Nyanga",
                "villes": ["Tchibanga", "Mayumba"],
            },
            "OI": {
                "nom": "Ogooué-Ivindo",
                "villes": ["Makokou", "Booué", "Mékambo"],
            },
            "OL": {
                "nom": "Ogooué-Lolo",
                "villes": ["Koulamoutou", "Lastoursville", "Pana"],
            },
            "OM": {
                "nom": "Ogooué-Maritime",
                "villes": ["Port-Gentil", "Omboué", "Gamba"],
            },
            "WN": {
                "nom": "Woleu-Ntem",
                "villes": ["Oyem", "Bitam", "Minvoul", "Mitzic"],
            },
        },
    }

    # ------------------------------------------------------------------
    # LOGIC
    # ------------------------------------------------------------------

    def clear_data(self, dry_run):
        self.stdout.write(self.style.WARNING("Nettoyage des données existantes"))

        if dry_run:
            self.stdout.write("DRY RUN → aucune suppression")
            return

        Ville.objects.all().delete()
        Province.objects.all().delete()
        Pays.objects.filter(code="GA").delete()

    def import_data(self, dry_run):
        data = self.GABON_DATA

        # ---- PAYS ----
        if dry_run:
            self.stdout.write("DRY RUN → Création pays Gabon")
            pays = None
        else:
            pays, created = Pays.objects.update_or_create(
                code=data["pays"]["code"],
                defaults={
                    "nom": data["pays"]["nom"],
                    "afficher_au_dashboard": True,
                    "is_active": True,
                },
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"[PAYS] {pays.nom} ({'créé' if created else 'mis à jour'})"
                )
            )

        # ---- PROVINCES & VILLES ----
        for code, province_data in data["provinces"].items():
            if dry_run:
                self.stdout.write(f"DRY RUN → Province {province_data['nom']}")
                continue

            province, created = Province.objects.get_or_create(
                nom=province_data["nom"],
                pays=pays,
                defaults={"code": code, "is_active": True},
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"[PROVINCE] {province.nom} ({'créée' if created else 'existante'})"
                )
            )

            for ville_nom in province_data["villes"]:
                ville, created = Ville.objects.get_or_create(
                    nom=ville_nom,
                    province=province,
                    pays=pays,
                    defaults={
                        "code": ville_nom[:5].upper(),
                        "is_active": True,
                    },
                )

                self.stdout.write(
                    f"   └─ [VILLE] {ville.nom} ({'créée' if created else 'existante'})"
                )



# Import normal
# python manage.py import_gabon_localites

# Simulation
# python manage.py import_gabon_localites --dry-run

# Réinitialisation + import
# python manage.py import_gabon_localites --clear
