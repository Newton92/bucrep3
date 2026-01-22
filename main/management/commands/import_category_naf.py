# management/commands/import_category_naf.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from main.models import CategoryNafCode


class Command(BaseCommand):
    help = 'Importe les catégories principales NAF (Nomenclature d\'Activités Française)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Efface les données existantes avant l\'importation',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule l\'importation sans sauvegarder en base de données',
        )

    def handle(self, *args, **options):
        clear_data = options['clear']
        dry_run = options.get('dry_run', False)
        
        # Données des catégories NAF principales
        # Ces codes correspondent aux sections de la NAF
        naf_categories = [
            # Format: (code, libelle, poids)
            ("A", "Agriculture, sylviculture et pêche", 0.5),
            ("B", "Industries extractives", 1.0),
            ("C", "Industrie manufacturière", 1.0),
            ("D", "Production et distribution d'électricité, de gaz, de vapeur et d'air conditionné", 1.0),
            ("E", "Production et distribution d'eau ; assainissement, gestion des déchets et dépollution", 0.5),
            ("F", "Construction", 0.1),
            ("G", "Commerce ; réparation d'automobiles et de motocycles", 0.2),
            ("H", "Transports et entreposage", 0.2),
            ("I", "Hébergement et restauration", 0.1),
            ("J", "Information et communication", 0.2),
            ("K", "Activités financières et d'assurance", 1.0),
            ("L", "Activités immobilières", 0.5),
            ("M", "Activités spécialisées, scientifiques et techniques", 0.2),
            ("N", "Activités de services administratifs et de soutien", 0.1),
            ("O", "Administration publique", 0.0),
            ("P", "Enseignement", 0.0),
            ("Q", "Santé humaine et action sociale", 0.0),
            ("R", "Arts, spectacles et activités récréatives", 0.1),
            ("S", "Autres activités de services", 0.1),
            ("T", "Activités des ménages en tant qu'employeurs ; activités indifférenciées des ménages en tant que producteurs de biens et services pour usage propre", 0.0),
            ("U", "Activités extra-territoriales", 0.0),
        ]

        try:
            if dry_run:
                self.stdout.write("[WARNING] " + "MODE SIMULATION - Aucune donnée ne sera sauvegardée")
                self.simulate_import(naf_categories)
            else:
                with transaction.atomic():
                    # Étape 1: Vider les données existantes si demandé
                    if clear_data:
                        self.clear_existing_data()
                    
                    # Étape 2: Importer les nouvelles données
                    self.import_categories(naf_categories)
                    
                    self.stdout.write(self.style.SUCCESS('[SUCCESS] ' + 'Importation des catégories NAF terminée avec succès!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {str(e)}'))
            import traceback
            traceback.print_exc()
            raise
    
    def clear_existing_data(self):
        """Vide toutes les données existantes des catégories NAF"""
        self.stdout.write("[WARNING] " + 'Suppression des données NAF existantes...')
        
        categories_count = CategoryNafCode.objects.count()
        
        # Vérifier si des sous-catégories existent
        from main.models import SubCategoryNafCode
        subcategories_count = SubCategoryNafCode.objects.count()
        
        if subcategories_count > 0:
            self.stdout.write(self.style.WARNING(
                f'Attention: {subcategories_count} sous-catégories existent. '
                f'Leur suppression est recommandée avant de supprimer les catégories.'
            ))
        
        # Supprimer les catégories
        deleted_count, _ = CategoryNafCode.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(
            f'[SUCCESS] Suppression de {deleted_count} catégories NAF.'
        ))
    
    def import_categories(self, categories_data):
        categories_created = 0
        categories_updated = 0
        
        self.stdout.write("Début de l'importation des catégories NAF...")
        
        for code, libelle, poids in categories_data:
            try:
                category, created = CategoryNafCode.objects.update_or_create(
                    code=code,
                    defaults={
                        'libelle': libelle,
                        'active': True,
                        'poids': poids,
                    }
                )
                
                if created:
                    categories_created += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'[CRÉÉ] Catégorie: {code} - {libelle} (poids: {poids})'
                    ))
                else:
                    categories_updated += 1
                    self.stdout.write(self.style.WARNING(
                        f'[MAJ] Catégorie mise à jour: {code} - {libelle} (poids: {poids})'
                    ))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'[ERREUR] Impossible de créer/mettre à jour la catégorie {code}: {str(e)}'
                ))
        
        # Résumé final
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS('[SUCCESS] ' + 'Importation terminée!'))
        self.stdout.write(f"Catégories créées: {categories_created}")
        self.stdout.write(f"Catégories mises à jour: {categories_updated}")
        self.stdout.write(f"Total catégories: {categories_created + categories_updated}")
        self.stdout.write("="*50)
    
    def simulate_import(self, categories_data):
        """Simule l'importation sans sauvegarder"""
        self.stdout.write("SIMULATION - Voici ce qui serait importé:")
        
        for code, libelle, poids in categories_data:
            self.stdout.write(f"• {code} - {libelle} (poids: {poids})")
        
        self.stdout.write(f"\nTotal: {len(categories_data)} catégories seraient importées")