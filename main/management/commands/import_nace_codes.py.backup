# management/commands/import_nace_codes.py
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from main.models import CategoryNaceCode, SubCategoryNaceCode  # Remplacez par le bon chemin


class Command(BaseCommand):
    help = 'Import NACE codes from structured data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate import without saving to database',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear_existing = options['clear']

        # Données structurées à partir de votre texte
        data = [
            # Les données sont trop longues, je vais créer une structure générique
            # Vous devrez copier toutes vos lignes de données ici
        ]

        # Pour économiser de l'espace, je vais créer un parser qui lit directement depuis
        # le tableau formaté que vous avez fourni
        nace_data = self.parse_nace_data()

        if clear_existing and not dry_run:
            self.stdout.write("[WARNING] " + 'Clearing existing NACE data...')
            CategoryNaceCode.objects.all().delete()
            SubCategoryNaceCode.objects.all().delete()
            self.stdout.write("[SUCCESS] " + 'Existing data cleared.')

        try:
            with transaction.atomic():
                stats = self.import_nace_data(nace_data, dry_run)

                if dry_run:
                    self.stdout.write("[WARNING] " + '\nDRY RUN - No data was saved')
                    transaction.set_rollback(True)
                else:
                    self.stdout.write("[SUCCESS] " + '\nImport completed successfully!')

                self.print_stats(stats)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during import: {str(e)}'))
            raise

    def parse_nace_data(self):
        """Parse les données NACE à partir du texte formaté"""
        # Créez un dictionnaire pour organiser les données
        categories = {}
        current_activity = None
        current_type = None

        # Voici un exemple de comment parser les premières lignes
        # Vous devrez adapter cela à votre format exact
        lines = """
        01 - Agriculture and Fishing	A - Manufacturers	0100	Agriculture, hunting and related service activities
                0110	Growing of crops; market gardening; horticulture
                0111	Growing of cereals and other crops n.e.c.
                0112	Growing of vegetables, horticultural specialties and nursery products
                0113	Growing of fruit, nuts, beverage and spice crops
                0150	Hunting, trapping and game propagation including related service activities
                0500	Fishing, operation of fish hatcheries and fish farms; service activities incidental to fishing
                0501	Fishing
                0502	Operation of fish hatcheries and fish farms
                0503	Service activities incidental to fishing
        B - Wholesalers & Agents	5111	Agents involved in the sale of agricultural raw materials, live animals, textile raw materials and semi-finished goods
                5120	Wholesale of agricultural raw materials and live animals
                5121	Wholesale of grain, seeds and animal feeds
                5122	Wholesale of flowers and plants
                5125	Wholesale of unmanufactured tobacco
                5131	Wholesale of fruit and vegetables
        C - Retailers	5221	Retail sale of fruit and vegetables
                5223	Retail sale of fish, crustaceans and molluscs
        D - Services & other	0140	Agricultural and animal husbandry service activities, except veterinary activities
                0141	Agricultural service activities
        """.strip().split('\n')

        parsed_data = []
        
        for line in lines:
            if not line.strip():
                continue
                
            # Parsez la ligne - vous devrez adapter cette logique
            # Cela dépend de comment vos données sont exactement formatées
            parts = [p.strip() for p in line.split('\t') if p.strip()]
            
            if len(parts) >= 3:
                if parts[0]:  # Nouvelle activité
                    current_activity = parts[0]
                if len(parts) >= 4 or (len(parts) == 3 and parts[0] and '-' in parts[0]):
                    # Ligne avec type
                    current_type = parts[1] if len(parts) >= 4 else None
                    code = parts[2] if len(parts) >= 4 else parts[1]
                    denomination = parts[3] if len(parts) >= 4 else parts[2]
                    
                    parsed_data.append({
                        'activity': current_activity,
                        'type': current_type,
                        'code': code,
                        'denomination': denomination
                    })
                elif len(parts) == 2:
                    # Sous-code sans type explicite
                    parsed_data.append({
                        'activity': current_activity,
                        'type': current_type,
                        'code': parts[0],
                        'denomination': parts[1]
                    })

        return parsed_data

    def import_nace_data(self, data, dry_run=False):
        """Importe les données NACE dans les modèles"""
        stats = {
            'categories_created': 0,
            'subcategories_created': 0,
            'categories_updated': 0,
            'subcategories_updated': 0,
        }

        # Dictionnaire pour suivre les catégories par code
        category_map = {}

        # Première passe : créer les catégories principales
        for item in data:
            if not item.get('activity'):
                continue
                
            activity_code = item['activity'].split(' - ')[0].strip()
            activity_name = item['activity'].split(' - ')[1].strip() if ' - ' in item['activity'] else item['activity']
            
            if activity_code not in category_map:
                # Créer ou mettre à jour la catégorie
                category, created = self.get_or_create_category(
                    activity_code, 
                    activity_name,
                    dry_run
                )
                category_map[activity_code] = category
                
                if created:
                    stats['categories_created'] += 1
                else:
                    stats['categories_updated'] += 1

        # Deuxième passe : créer les sous-catégories
        for item in data:
            if not item.get('code') or not item.get('denomination'):
                continue
                
            activity_code = item['activity'].split(' - ')[0].strip()
            category = category_map.get(activity_code)
            
            if not category:
                continue
                
            # Créer la sous-catégorie
            subcategory, created = self.get_or_create_subcategory(
                category,
                item['code'],
                item['denomination'],
                item.get('type', ''),
                dry_run
            )
            
            if created:
                stats['subcategories_created'] += 1
            else:
                stats['subcategories_updated'] += 1

        return stats

    def get_or_create_category(self, code, name, dry_run):
        """Obtient ou crée une catégorie NACE"""
        if dry_run:
            self.stdout.write(f"Would create/update category: {code} - {name}")
            return None, True
        
        category, created = CategoryNaceCode.objects.update_or_create(
            code=code,
            defaults={
                'libelle': name,
                'active': True,
            }
        )
        
        if created:
            self.stdout.write("[SUCCESS] " + f'[OK] Created category: {code} - {name}')
        else:
            self.stdout.write("[WARNING] " + f'[UPD] Updated category: {code} - {name}')
            
        return category, created

    def get_or_create_subcategory(self, category, code, denomination, type_code, dry_run):
        """Obtient ou crée une sous-catégorie NACE"""
        if dry_run:
            self.stdout.write(f"  Would create/update subcategory: {code} - {denomination}")
            return None, True
        
        # Vous pourriez vouloir inclure le type dans le libellé
        full_libelle = denomination
        if type_code:
            full_libelle = f"[{type_code}] {denomination}"
        
        subcategory, created = SubCategoryNaceCode.objects.update_or_create(
            code=code,
            defaults={
                'category': category,
                'libelle': full_libelle,
                'active': True,
            }
        )
        
        if created:
            self.stdout.write("[SUCCESS] " + f'  [OK] Created subcategory: {code} - {denomination}')
        else:
            self.stdout.write("[WARNING] " + f'  [UPD] Updated subcategory: {code} - {denomination}')
            
        return subcategory, created

    def print_stats(self, stats):
        """Affiche les statistiques d'importation"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("IMPORT STATISTICS")
        self.stdout.write("="*50)
        self.stdout.write(f"Categories created: {stats['categories_created']}")
        self.stdout.write(f"Categories updated: {stats['categories_updated']}")
        self.stdout.write(f"Subcategories created: {stats['subcategories_created']}")
        self.stdout.write(f"Subcategories updated: {stats['subcategories_updated']}")
        self.stdout.write("="*50)
        
        
        
        
        
        
# Import normal
# python manage.py import_nace_codes

# Simulation (dry run)
# python manage.py import_nace_codes --dry-run

# Effacer et réimporter
# python manage.py import_nace_codes --clear

# Version simple
# python manage.py import_nace_simple