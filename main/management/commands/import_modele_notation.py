# management/commands/import_modele_notation.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from main.models import ModeleNotation


class Command(BaseCommand):
    help = 'Import Modèle de notation data from hardcoded choices'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate import without saving to database',
        )

    def handle(self, *args, **options):
        clear_data = options['clear']
        dry_run = options.get('dry_run', False)
        
        # Données à importer - extraites de LIEN_PLUS_INFORMATIONS_NOTATION_CHOICE
        notation_data = [
            # Format: (code, libelle)
            ("40", _("Cette société est une filiale d'un groupe")),
            ("35", _("Cette société est une société autonome")),
            ("30", _("En raison de ses liens avec le groupe, elle est considérée comme une filiale indépendante")),
            ("25", _("Cette entreprise est considérée comme une grande entreprise")),
            ("20", _("Cette entreprise est considérée comme une entreprise de taille moyenne")),
            ("15", _("Cette entreprise est considérée comme une petite entreprise")),
            ("10", _("Inconnu de nos sources")),
        ]
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No data will be saved"))
            self.simulate_import(notation_data, clear_data)
            return
        
        try:
            with transaction.atomic():
                # Étape 1: Vider les données existantes si demandé
                if clear_data:
                    self.clear_existing_data()
                
                # Étape 2: Importer les nouvelles données
                stats = self.import_data(notation_data)
                
                self.stdout.write(self.style.SUCCESS('Successfully imported Modèle de notation data!'))
                self.print_stats(stats)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise
    
    def clear_existing_data(self):
        """Vide toutes les données existantes du modèle ModeleNotation"""
        self.stdout.write(self.style.WARNING('Clearing existing Modèle de notation data...'))
        
        # Compter avant suppression
        count = ModeleNotation.objects.count()
        
        # Supprimer toutes les entrées
        ModeleNotation.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(f'Cleared {count} Modèle de notation entries.'))
    
    def import_data(self, entries):
        """Importe les données dans le modèle ModeleNotation"""
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        self.stdout.write("Starting Modèle de notation data import...")
        
        # Traiter chaque entrée
        for code, libelle in entries:
            # Vérifier si le code existe déjà
            existing = ModeleNotation.objects.filter(code=code).first()
            
            if existing:
                # Vérifier si les données sont identiques
                if existing.libelle == str(libelle):
                    skipped_count += 1
                    self.stdout.write(self.style.WARNING(f'↺ Skipped (identical): {code} - {libelle}'))
                    continue
                else:
                    # Mettre à jour l'entrée existante
                    existing.libelle = str(libelle)
                    existing.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f'↻ Updated: {code} - {libelle}'))
            else:
                # Créer une nouvelle entrée
                ModeleNotation.objects.create(
                    code=code,
                    libelle=str(libelle)
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {code} - {libelle}'))
        
        return {
            'created': created_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'total': len(entries)
        }
    
    def simulate_import(self, entries, clear_data):
        """Simule l'importation sans enregistrer en base de données"""
        self.stdout.write("="*60)
        self.stdout.write("DRY RUN - SIMULATION ONLY")
        self.stdout.write("="*60)
        
        if clear_data:
            self.stdout.write(self.style.WARNING("Would clear all existing ModeleNotation data"))
        
        self.stdout.write("\nEntries to import:")
        for code, libelle in entries:
            self.stdout.write(f"  {code}: {libelle}")
        
        # Vérifier les doublons potentiels
        codes = [code for code, _ in entries]
        duplicates = {code for code in codes if codes.count(code) > 1}
        
        if duplicates:
            self.stdout.write(self.style.ERROR(f"\nWARNING: Duplicate codes found: {duplicates}"))
        else:
            self.stdout.write(self.style.SUCCESS("\nNo duplicate codes found"))
        
        self.stdout.write(f"\nTotal entries to process: {len(entries)}")
        self.stdout.write("="*60)
    
    def print_stats(self, stats):
        """Affiche les statistiques d'importation"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("IMPORT STATISTICS")
        self.stdout.write("="*50)
        self.stdout.write(f"Total entries in source: {stats['total']}")
        self.stdout.write(f"Entries created: {stats['created']}")
        self.stdout.write(f"Entries updated: {stats['updated']}")
        self.stdout.write(f"Entries skipped (identical): {stats['skipped']}")
        self.stdout.write("="*50)
        
        # Vérifier l'intégrité
        total_processed = stats['created'] + stats['updated'] + stats['skipped']
        if total_processed == stats['total']:
            self.stdout.write(self.style.SUCCESS("✓ All entries processed successfully"))
        else:
            self.stdout.write(self.style.ERROR(f"⚠ Mismatch: processed {total_processed} out of {stats['total']}"))


# Version alternative avec bulk_create pour meilleure performance
class CommandOptimized(BaseCommand):
    help = 'Import Modèle de notation data (optimized version)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import',
        )
    
    def handle(self, *args, **options):
        clear_data = options['clear']
        
        notation_data = [
            ("40", "Cette société est une filiale d'un groupe"),
            ("35", "Cette société est une société autonome"),
            ("30", "En raison de ses liens avec le groupe, elle est considérée comme une filiale indépendante"),
            ("25", "Cette entreprise est considérée comme une grande entreprise"),
            ("20", "Cette entreprise est considérée comme une entreprise de taille moyenne"),
            ("15", "Cette entreprise est considérée comme une petite entreprise"),
            ("10", "Inconnu de nos sources"),
        ]
        
        try:
            with transaction.atomic():
                if clear_data:
                    ModeleNotation.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS('Cleared existing data'))
                
                # Préparer les objets pour bulk_create
                objets_a_creer = []
                for code, libelle in notation_data:
                    objets_a_creer.append(
                        ModeleNotation(
                            code=code,
                            libelle=libelle
                        )
                    )
                
                # Utiliser bulk_create pour meilleure performance
                ModeleNotation.objects.bulk_create(objets_a_creer)
                
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully imported {len(objets_a_creer)} Modèle de notation entries!'
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise
        
        
# 1. Importation standard (met à jour ou crée si nécessaire)        
# python manage.py import_modele_notation

# 2. Vider et réimporter
# python manage.py import_modele_notation --clear

# 3. Simulation (dry-run)
# python manage.py import_modele_notation --dry-run

# 4. Combinaison des options
# python manage.py import_modele_notation --clear --dry-run