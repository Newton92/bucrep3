"""Populate StatutEntreprise with the standard 21-status list.

Codes match STATUT_ENTREPRISE_EN in serializers.py for EN translation.
French libelles match STATUT_ENTREPRISE_LIBELLE_EN for fallback translation.
"""
from django.core.management.base import BaseCommand
from main.models import StatutEntreprise

STATUTS = [
    # (code, libelle_fr)
    ("ACTIVE",         "Entreprise active"),
    ("INACTIVE",       "Entreprise inactive"),
    ("MERGING",        "Entreprises en fusion"),
    ("MERGED",         "Entreprise fusionnée"),
    ("NOT_EXIST",      "L'entreprise n'existe pas"),
    ("NOT_IDENTIFIED", "L'entreprise n'a pas pu être identifiée"),
    ("DORMANT",        "Entreprise en sommeil"),
    ("NOT_LOCATED",    "Impossible de localiser l'entreprise"),
    ("CEASED",         "Activité cessée"),
    ("NOT_REGISTERED", "L'entreprise n'est pas immatriculée"),
    ("NOT_LOCAL_REG",  "L'entreprise n'est pas immatriculée localement"),
    ("LIMITED",        "Activité commerciale limitée"),
    ("NO_VISIBLE_ACT", "Aucune activité commerciale visible localement"),
    ("WINDING_VOL",    "Dissolution volontaire"),
    ("WINDING_CRED",   "Dissolution volontaire des créanciers"),
    ("WINDING_COMP",   "Liquidation judiciaire obligatoire"),
    ("RADIATION",      "Radiation"),
    ("DEREGISTRATION", "Entreprise en cours de radiation"),
    ("DISSOLVED",      "Dissoute"),
    ("FOLLOW_UP",      "À suivre"),
    ("NOT_FOUND",      "Entreprise introuvable"),
]


class Command(BaseCommand):
    help = "Import/update the standard StatutEntreprise list (FR + EN translation via serializers)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing records first (FKs on Acheteur set to NULL)",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = StatutEntreprise.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Supprimé {deleted} statut(s) existant(s)."))

        created = updated = 0
        for code, libelle in STATUTS:
            _, was_created = StatutEntreprise.objects.update_or_create(
                code=code,
                defaults={"libelle": libelle, "active": True},
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done — créé: {created}, mis à jour: {updated}"
        ))
