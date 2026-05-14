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

# Mapping libelle ancien → code_ac pour migrer les enregistrements existants
LEGACY_LIBELLE_TO_CODE = {
    "Développement commercial ne peut être déterminé par un tiers": 0,
    "Le développement ne peut pas être déterminé par des tiers.": 0,
    "Développement commercial très positif": 100,
    "Fort développement commercial": 150,
    "Développement commercial fort": 150,
    "Développement commercial positif": 200,
    "Bon développement commercial": 300,
    "Développement commercial passable": 350,
    "Développement commercial satisfaisant": 350,
    "Développement commercial acceptable": 400,
    "Développement commercial moyennement en déclin": 500,
    "Développement commercial légèrement en déclin": 500,
    "Développement commercial en déclin": 600,
    "Développement commercial en déclin rapide": 700,
    "Développement commercial fortement en déclin": 800,
    "Développement commercial inconnu": 900,
}


class Command(BaseCommand):
    help = "Importer / mettre à jour les avis de développement commercial (bilingues FR/EN)"

    def handle(self, *args, **options):
        with transaction.atomic():
            self._migrate_existing()
            self._upsert_all()

    def _migrate_existing(self):
        """Assigne code_ac aux anciens enregistrements via leur libellé."""
        unmapped = 0
        for obj in ListeInformationsAvisCommercial.objects.all():
            code = LEGACY_LIBELLE_TO_CODE.get(obj.libelle.strip())
            if code is not None and obj.code_ac != code:
                obj.code_ac = code
                obj.save(update_fields=['code_ac'])
                self.stdout.write(f"  ↺ Migration [{code}] ← \"{obj.libelle[:50]}\"")
            elif code is None:
                unmapped += 1
                self.stdout.write(
                    self.style.WARNING(f"  ? Non mappé (code_ac=-1) : \"{obj.libelle[:60]}\"")
                )
                obj.code_ac = -1
                obj.save(update_fields=['code_ac'])
        if unmapped:
            self.stdout.write(
                self.style.WARNING(f"  {unmapped} enregistrement(s) non mappés → code_ac=-1")
            )

    def _upsert_all(self):
        """Crée ou met à jour les 13 entrées standardisées."""
        created_count = updated_count = 0
        for item in AVIS_COMMERCIAL_DATA:
            # Si plusieurs enregistrements ont le même code_ac après migration,
            # on prend le premier et on supprime les doublons (sans FK active).
            qs = ListeInformationsAvisCommercial.objects.filter(code_ac=item['code'])
            if qs.count() > 1:
                # Garder le premier, supprimer les autres non référencés
                keep = qs.first()
                for duplicate in qs.exclude(pk=keep.pk):
                    try:
                        duplicate.delete()
                        self.stdout.write(self.style.WARNING(f"  🗑 Doublon supprimé id={duplicate.pk}"))
                    except Exception:
                        pass  # référencé par FK, on laisse

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
                self.stdout.write(self.style.SUCCESS(f"  ✔ Créé  [{item['code']}] {item['libelle_en']}"))
            else:
                updated_count += 1
                self.stdout.write(f"  ↺ MàJ   [{item['code']}] {item['libelle_en']}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Terminé — {created_count} créé(s), {updated_count} mis à jour"
            )
        )
