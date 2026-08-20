"""
Supprime les doublons de FormeJuridique en base.

Stratégie :
  - Regroupe les enregistrements par libellé normalisé (strip + lowercase).
  - Dans chaque groupe, conserve celui dont le code est dans la liste standard
    (CODES_STANDARDS) ; à défaut, celui avec le plus petit ID (le plus ancien).
  - Reporte toutes les FK (Acheteur, DonneesEnregistrement, ScoringSansBilanAcheteur,
    utilitaires.DonneesEnregistrement) sur l'enregistrement conservé.
  - Supprime les doublons (hard delete pour ne pas polluer soft-delete).

Usage :
    python manage.py deduplicate_forme_juridique
    python manage.py deduplicate_forme_juridique --dry-run
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from main.models import (
    Acheteur,
    DonneesEnregistrement,
    FormeJuridique,
    ScoringSansBilanAcheteur,
)

try:
    from main.utilitaires.models import DonneesEnregistrement as UtilDonneesEnreg
    HAS_UTIL = True
except ImportError:
    HAS_UTIL = False

# Codes considérés comme « canoniques » (issus de import_forme_juridique.py)
CODES_STANDARDS = {
    "ASSOC", "COOP", "EI", "EIRL", "FIDUCIE", "GIE", "GP",
    "LLP", "LTD", "PARTNER", "PLC", "PMSBL",
    "SA", "SA-AG", "SA-CA", "SA-PLURI", "SARL", "SARL-U",
    "SAS", "SASU", "SAU", "SC", "SCI", "SCP", "SCS",
    "SDF", "SE", "SEP", "SNC", "SPRL", "SSPJ", "SYNDIC",
    "PART", "PTY_LTD", "NPC", "CC", "JV",
}


def normalize(libelle):
    return (libelle or "").strip().lower()


class Command(BaseCommand):
    help = "Déduplique les FormeJuridique en conservant un enregistrement par libellé"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simule sans toucher à la base",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Récupère tous les enregistrements, y compris soft-deleted
        all_fj = list(FormeJuridique.all_objects.all().order_by("id"))

        # Regroupe par libellé normalisé
        groups = {}
        for fj in all_fj:
            key = normalize(fj.libelle)
            groups.setdefault(key, []).append(fj)

        total_deleted = 0

        with transaction.atomic():
            for key, records in groups.items():
                if len(records) <= 1:
                    continue

                # Choisit le « gagnant » : code standard en premier, sinon plus petit ID
                winner = None
                for rec in records:
                    if rec.code in CODES_STANDARDS:
                        winner = rec
                        break
                if winner is None:
                    winner = min(records, key=lambda r: r.id)

                losers = [r for r in records if r.id != winner.id]
                loser_ids = [r.id for r in losers]

                self.stdout.write(
                    f'  Groupe "{key}" — conserve ID={winner.id} (code={winner.code}), '
                    f"supprime IDs={loser_ids}"
                )

                if not dry_run:
                    # Redirige les FK vers le gagnant
                    Acheteur.objects.filter(forme_juridique_id__in=loser_ids).update(
                        forme_juridique=winner
                    )
                    DonneesEnregistrement.objects.filter(forme_juridique_id__in=loser_ids).update(
                        forme_juridique=winner
                    )
                    ScoringSansBilanAcheteur.objects.filter(forme_juridique_id__in=loser_ids).update(
                        forme_juridique=winner
                    )
                    if HAS_UTIL:
                        UtilDonneesEnreg.objects.filter(
                            nouvelle_forme_juridique_id__in=loser_ids
                        ).update(nouvelle_forme_juridique=winner)

                    # Hard-delete (bypass SafeDelete)
                    FormeJuridique.all_objects.filter(id__in=loser_ids).delete()

                total_deleted += len(losers)

        mode = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}Terminé — {total_deleted} doublon(s) {'détecté(s)' if dry_run else 'supprimé(s)'}"
            )
        )
