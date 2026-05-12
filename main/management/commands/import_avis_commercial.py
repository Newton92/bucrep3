from django.core.management.base import BaseCommand
from main.models import ListeInformationsAvisCommercial


DEVELOPPEMENT_DATA = [
    {'code_num': '5', 'libelle': 'Bon développement commercial', 'poids': 0.4},
    {'code_num': '9', 'libelle': 'Développement commercial en déclin', 'poids': -1.0},
    {'code_num': '7', 'libelle': 'Développement commercial acceptable', 'poids': 0.3},
    {'code_num': '3', 'libelle': 'Développement commercial fort', 'poids': 0.6},
    {'code_num': '8', 'libelle': 'Développement commercial moyennement en déclin', 'poids': -0.5},
    {'code_num': '1', 'libelle': 'Développement commercial ne peut être déterminé par un tiers', 'poids': 0.0},
    {'code_num': '6', 'libelle': 'Développement commercial passable', 'poids': 0.35},
    {'code_num': '4', 'libelle': 'Développement commercial positif', 'poids': 0.5},
    {'code_num': '2', 'libelle': 'Développement commercial très positif', 'poids': 0.7},
]


class Command(BaseCommand):
    help = "Importer les avis de développement commercial"

    def handle(self, *args, **options):
        created_count = 0

        for item in DEVELOPPEMENT_DATA:
            libelle = item["libelle"]
            couleur = self.generate_color(libelle)

            obj, created = ListeInformationsAvisCommercial.objects.get_or_create(
                libelle=libelle,
                defaults={"couleur": couleur},
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✔ Ajouté : {libelle}"))
            else:
                self.stdout.write(f"• Existe déjà : {libelle}")

        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Import terminé ({created_count} nouveaux éléments)")
        )

    def generate_color(self, libelle: str) -> str:
        """Génère une couleur selon le contenu du libellé"""
        text = libelle.lower()

        if "très positif" in text or "fort" in text:
            return "#2ecc71"  # vert foncé
        if "positif" in text or "bon" in text:
            return "#27ae60"  # vert
        if "acceptable" in text or "passable" in text:
            return "#f1c40f"  # jaune
        if "déclin" in text:
            return "#e74c3c"  # rouge
        if "ne peut être déterminé" in text:
            return "#95a5a6"  # gris

        return "#bdc3c7"  # couleur par défaut
