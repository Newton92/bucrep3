from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import ListeInformationsAvisCommercial


AVIS_COMMERCIAL_DATA = [
    {
        'code': 0,
        'libelle': "Le développement ne peut pas être déterminé par des tiers.",
        'libelle_en': "Development cannot be determined by third parties.",
        'couleur': '#95a5a6',
    },
    {
        'code': 15,
        'libelle': (
            "En raison des informations relatives aux procédures d'insolvabilité/"
            "préliminaires/d'échelonnement des dettes, nous ne sommes pas en mesure "
            "de donner une évaluation définitive du développement de l'entreprise pour l'instant."
        ),
        'libelle_en': (
            "In view of the information on insolvency/preliminary/debt staggering procedures, "
            "we are not in a position to give a definitive assessment on the development "
            "of the company at present."
        ),
        'couleur': '#c0392b',
    },
    {
        'code': 100,
        'libelle': "Développement commercial très positif",
        'libelle_en': "Very positive business development",
        'couleur': '#27ae60',
    },
    {
        'code': 150,
        'libelle': "Fort développement commercial",
        'libelle_en': "Strong business development",
        'couleur': '#2ecc71',
    },
    {
        'code': 200,
        'libelle': "Développement commercial positif",
        'libelle_en': "Positive business development",
        'couleur': '#16a085',
    },
    {
        'code': 300,
        'libelle': "Bon développement commercial",
        'libelle_en': "Good business development",
        'couleur': '#1abc9c',
    },
    {
        'code': 350,
        'libelle': "Développement commercial satisfaisant",
        'libelle_en': "Fair business development",
        'couleur': '#f1c40f',
    },
    {
        'code': 400,
        'libelle': "Développement commercial acceptable",
        'libelle_en': "Acceptable business development",
        'couleur': '#f39c12',
    },
    {
        'code': 500,
        'libelle': "Développement commercial légèrement en déclin",
        'libelle_en': "Slightly declining business development",
        'couleur': '#e67e22',
    },
    {
        'code': 600,
        'libelle': "Développement commercial en déclin",
        'libelle_en': "Declining business development",
        'couleur': '#e74c3c',
    },
    {
        'code': 700,
        'libelle': "Développement commercial en déclin rapide",
        'libelle_en': "Rapidly declining business development",
        'couleur': '#c0392b',
    },
    {
        'code': 800,
        'libelle': "Développement commercial fortement en déclin",
        'libelle_en': "Declining business development.",
        'couleur': '#922b21',
    },
    {
        'code': 900,
        'libelle': "Développement commercial inconnu",
        'libelle_en': "Business development not known",
        'couleur': '#7f8c8d',
    },
]


class Command(BaseCommand):
    help = "Importer / mettre à jour les avis de développement commercial (bilingues FR/EN)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help="Supprime tous les enregistrements existants avant l'importation",
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted, _ = ListeInformationsAvisCommercial.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Supprimé {deleted} enregistrement(s) existant(s)"))

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for item in AVIS_COMMERCIAL_DATA:
                obj, created = ListeInformationsAvisCommercial.objects.update_or_create(
                    code_ac=item['code'],
                    defaults={
                        'libelle': item['libelle'],
                        'libelle_en': item['libelle_en'],
                        'couleur': item['couleur'],
                    },
                )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"✔ Créé [{item['code']}] : {item['libelle_en']}"))
                else:
                    updated_count += 1
                    self.stdout.write(f"↺ Mis à jour [{item['code']}] : {item['libelle_en']}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Import terminé — {created_count} créé(s), {updated_count} mis à jour"
            )
        )
