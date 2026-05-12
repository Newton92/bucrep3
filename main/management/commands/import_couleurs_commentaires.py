# main/management/commands/import_couleurs_commentaires.py

from django.core.management.base import BaseCommand
from main.models import CouleurCommentaire


class Command(BaseCommand):
    help = "Import des couleurs standards des commentaires (SafeDelete compatible)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Supprimer les couleurs existantes avant import (soft delete)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulation sans écriture en base",
        )

    COULEURS = (
        {"couleur": "Normal", "code": "#000000"},
        {"couleur": "Rouge", "code": "#FF0000"},
        {"couleur": "Jaune", "code": "#FFFF00"},
        {"couleur": "Vert", "code": "#00FF00"},
    )

    def handle(self, *args, **options):
        clear = options["clear"]
        dry_run = options["dry_run"]

        self.stdout.write(self.style.NOTICE("=== IMPORT COULEURS COMMENTAIRES ==="))

        if clear:
            self.clear_data(dry_run)

        self.import_data(dry_run)

        self.stdout.write(self.style.SUCCESS("✔ Import terminé"))

    # ------------------------------------------------------------------

    def clear_data(self, dry_run):
        self.stdout.write(self.style.WARNING("Nettoyage des couleurs existantes"))

        if dry_run:
            self.stdout.write("DRY RUN → aucune suppression")
            return

        CouleurCommentaire.objects.all().delete()

    def import_data(self, dry_run):
        for data in self.COULEURS:
            couleur = data["couleur"]
            code = data["code"]

            if dry_run:
                self.stdout.write(f"DRY RUN → {couleur} ({code})")
                continue

            # Inclure les soft-deleted
            existing = CouleurCommentaire.objects.all_with_deleted().filter(code=code).first()

            if existing:
                if hasattr(existing, "deleted") and existing.deleted:
                    # Restaurer
                    existing.deleted = None
                    existing.deleted_by_cascade = None
                    existing.couleur = couleur
                    existing.save()
                    self.stdout.write(
                        self.style.WARNING(f"[RESTORED] {couleur} ({code})")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"[SKIP] {couleur} ({code}) déjà existante")
                    )
            else:
                CouleurCommentaire.objects.create(
                    couleur=couleur,
                    code=code,
                    deleted=None,
                    deleted_by_cascade=None,
                )
                self.stdout.write(
                    self.style.SUCCESS(f"[CREATED] {couleur} ({code})")
                )


# Import normal
# python manage.py import_couleurs_commentaires

# Simulation (aucune écriture)
# python manage.py import_couleurs_commentaires --dry-run

# Réinitialiser + réimporter
# python manage.py import_couleurs_commentaires --clear
