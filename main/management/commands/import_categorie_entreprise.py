from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import CategorieEntreprise


class Command(BaseCommand):
    help = "Importe ou met à jour les catégories d'entreprise avec codes normalisés"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help="Supprime toutes les catégories existantes avant import"
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Simule l'import sans modifier la base"
        )

    def handle(self, *args, **options):
        self.stdout.write("[SUCCESS] Début import catégories d'entreprise")

        categories = [
            # (code, libellé)
            ("CAT-001", "Agriculture"),
            ("CAT-002", "Élevage"),
            ("CAT-003", "Pêche"),
            ("CAT-004", "Aquaculture"),
            ("CAT-005", "Sylviculture"),
            ("CAT-006", "Exploitation forestière"),
            ("CAT-007", "Mines et carrières"),
            ("CAT-008", "Pétrole et gaz"),

            ("CAT-009", "Agroalimentaire"),
            ("CAT-010", "Industrie manufacturière"),
            ("CAT-011", "Transformation du bois"),
            ("CAT-012", "Transformation minière"),
            ("CAT-013", "Industrie chimique"),
            ("CAT-014", "Industrie pharmaceutique"),
            ("CAT-015", "Industrie textile"),
            ("CAT-016", "Métallurgie"),
            ("CAT-017", "Production d’énergie"),
            ("CAT-018", "BTP / Construction"),
            ("CAT-019", "Matériaux de construction"),

            ("CAT-020", "Transport routier"),
            ("CAT-021", "Transport maritime"),
            ("CAT-022", "Transport aérien"),
            ("CAT-023", "Transport ferroviaire"),
            ("CAT-024", "Logistique"),
            ("CAT-025", "Transit & douane"),
            ("CAT-026", "Entreposage"),

            ("CAT-027", "Commerce de gros"),
            ("CAT-028", "Commerce de détail"),
            ("CAT-029", "Import / Export"),
            ("CAT-030", "Distribution"),
            ("CAT-031", "E-commerce"),
            ("CAT-032", "Vente automobile"),
            ("CAT-033", "Vente de matériaux"),

            ("CAT-034", "Banque"),
            ("CAT-035", "Microfinance"),
            ("CAT-036", "Assurance"),
            ("CAT-037", "Courtage"),
            ("CAT-038", "Fintech"),
            ("CAT-039", "Crédit / Leasing"),
            ("CAT-040", "Gestion d’actifs"),

            ("CAT-041", "Technologies de l’information"),
            ("CAT-042", "Développement logiciel"),
            ("CAT-043", "Télécommunications"),
            ("CAT-044", "Services numériques"),
            ("CAT-045", "Cybersécurité"),
            ("CAT-046", "Data & Intelligence artificielle"),
            ("CAT-047", "Services cloud"),

            ("CAT-048", "Conseil"),
            ("CAT-049", "Audit"),
            ("CAT-050", "Expertise comptable"),
            ("CAT-051", "Services juridiques"),
            ("CAT-052", "Ressources humaines"),
            ("CAT-053", "Formation professionnelle"),
            ("CAT-054", "Marketing & communication"),
            ("CAT-055", "Publicité"),
            ("CAT-056", "Études & sondages"),

            ("CAT-057", "Santé"),
            ("CAT-058", "Clinique / Hôpital"),
            ("CAT-059", "Pharmacie"),
            ("CAT-060", "Laboratoire médical"),
            ("CAT-061", "Services sociaux"),
            ("CAT-062", "ONG / Associations"),
            ("CAT-063", "Action humanitaire"),

            ("CAT-064", "Éducation"),
            ("CAT-065", "Enseignement supérieur"),
            ("CAT-066", "Formation"),
            ("CAT-067", "Recherche scientifique"),

            ("CAT-068", "Hôtellerie"),
            ("CAT-069", "Restauration"),
            ("CAT-070", "Tourisme"),
            ("CAT-071", "Loisirs"),
            ("CAT-072", "Événementiel"),
            ("CAT-073", "Culture & arts"),

            ("CAT-074", "Immobilier"),
            ("CAT-075", "Promotion immobilière"),
            ("CAT-076", "Gestion immobilière"),
            ("CAT-077", "Location"),
            ("CAT-078", "Aménagement urbain"),

            ("CAT-079", "Sécurité privée"),
            ("CAT-080", "Nettoyage"),
            ("CAT-081", "Maintenance"),
            ("CAT-082", "Pressing"),
            ("CAT-083", "Réparation"),

            ("CAT-084", "Administration publique"),
            ("CAT-085", "Collectivités locales"),
            ("CAT-086", "Entreprises publiques"),
            ("CAT-087", "Institutions internationales"),
            ("CAT-088", "Organismes parapublics"),
        ]

        if options['clear'] and not options['dry_run']:
            deleted, _ = CategorieEntreprise.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"{deleted} catégories supprimées"))

        created_count = 0
        updated_count = 0

        if not options['dry_run']:
            with transaction.atomic():
                for code, libelle in categories:
                    obj, created = CategorieEntreprise.objects.update_or_create(
                        code=code,
                        defaults={
                            "libelle": libelle,
                            "active": True
                        }
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f"[OK] {code} - {libelle}"))
                    else:
                        updated_count += 1
                        self.stdout.write(self.style.WARNING(f"[UPD] {code} - {libelle}"))
        else:
            self.stdout.write("[INFO] Mode simulation")
            for code, libelle in categories:
                exists = CategorieEntreprise.objects.filter(code=code).exists()
                status = "EXIST" if exists else "NEW"
                self.stdout.write(f"[{status}] {code} - {libelle}")
                if not exists:
                    created_count += 1

        # Résumé
        self.stdout.write("\n" + "=" * 50)
        if options['dry_run']:
            self.stdout.write("[INFO] SIMULATION - Aucune modification")
        self.stdout.write("[SUCCESS] Résumé import catégories")
        self.stdout.write(f"- Total : {len(categories)}")
        self.stdout.write(f"- Créées : {created_count}")
        self.stdout.write(f"- Mises à jour : {updated_count}")
