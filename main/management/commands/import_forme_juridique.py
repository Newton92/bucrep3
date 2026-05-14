"""Populate FormeJuridique with the standard OHADA/CEMAC list.

Codes and libelles match FORME_JURIDIQUE_EN / FORME_JURIDIQUE_LIBELLE_EN
in serializers.py so that EN translation works correctly.
"""
from django.core.management.base import BaseCommand
from main.models import FormeJuridique

FORMES = [
    # (code, libelle_fr, poids)  — codes must match FORME_JURIDIQUE_EN keys
    ("ASSOC",    "Association",                                                         0.10),
    ("COOP",     "Coopérative",                                                         0.75),
    ("EI",       "Entreprise individuelle (EI)",                                        0.50),
    ("EIRL",     "Entreprise individuelle à responsabilité limitée (EIRL)",             0.20),
    ("FIDUCIE",  "Fiducie exploitant une entreprise à caractère commercial",            0.25),
    ("GIE",      "Groupement d'intérêt économique (GIE)",                              0.30),
    ("GP",       "Groupement de personnes",                                             0.20),
    ("LLP",      "Partnership à responsabilité limitée (LLP)",                         0.50),
    ("LTD",      "Private Limited Company (Ltd)",                                       0.50),
    ("PARTNER",  "Partnership / Partenariat",                                           0.20),
    ("PLC",      "Public Limited Company (PLC)",                                        1.00),
    ("PMSBL",    "Personne morale sans but lucratif",                                   0.10),
    ("SA",       "Société anonyme (SA)",                                                1.00),
    ("SA-AG",    "Société anonyme avec administration générale (SA)",                   1.00),
    ("SA-CA",    "Société anonyme avec conseil d'administration (SA)",                  1.00),
    ("SA-PLURI", "Société anonyme pluripersonnelle (SA)",                              1.00),
    ("SARL",     "Société à responsabilité limitée pluripersonnelle (SARL)",           0.50),
    ("SARL-U",   "Société à responsabilité limitée unipersonnelle (SARL U)",           0.50),
    ("SAS",      "Société par action simplifiée pluripersonnelle (SAS)",               0.50),
    ("SASU",     "Société par action simplifiée unipersonnelle (SASU)",                0.50),
    ("SAU",      "Société anonyme unipersonnelle (SAU)",                               1.00),
    ("SC",       "Sociétés civiles (SC)",                                               0.25),
    ("SCI",      "Société civile immobilière (SCI)",                                    0.25),
    ("SCP",      "Société civile professionnelle (SCP)",                               0.25),
    ("SCS",      "Société en commandite simple (SCS)",                                 0.50),
    ("SDF",      "Société créée de fait / Société de fait",                            0.10),
    ("SE",       "Société d'état (SE)",                                                 0.40),
    ("SEP",      "Société en participation (SEP)",                                      0.20),
    ("SNC",      "Société en nom collectif (SNC)",                                      0.50),
    ("SPRL",     "Société privée à responsabilité limitée (SPRL)",                     0.50),
    ("SSPJ",     "Sociétés sans personnalité juridique",                               0.00),
    ("SYNDIC",   "Syndicat de copropriété",                                             0.10),
]


class Command(BaseCommand):
    help = "Import/update the standard FormeJuridique list (codes aligned with EN translation)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing records first (FKs on Acheteur set to NULL)",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = FormeJuridique.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Supprimé {deleted} forme(s) juridique(s) existante(s)."))

        created = updated = 0
        for code, libelle, poids in FORMES:
            _, was_created = FormeJuridique.objects.update_or_create(
                code=code,
                defaults={"libelle": libelle, "poids": poids, "active": True},
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done — créé: {created}, mis à jour: {updated}"
        ))
