# management/commands/import_modele_notation.py - VERSION CORRIGÉE
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import ModeleNotation

class Command(BaseCommand):
    help = 'Import Modèle de notation data from hardcoded choices'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Force delete all existing data before import (including soft-deleted)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate import without saving to database',
        )
        parser.add_argument(
            '--hard-delete',
            action='store_true',
            help='Permanently delete instead of soft delete when using --clear',
        )

    def handle(self, *args, **options):
        clear_data = options['clear']
        dry_run = options.get('dry_run', False)
        hard_delete = options.get('hard_delete', False)
        
        # Données à importer
        notation_data = [
            ("40", "Cette société est une filiale d'un groupe"),
            ("35", "Cette société est une société autonome"),
            ("30", "En raison de ses liens avec le groupe, elle est considérée comme une filiale indépendante"),
            ("25", "Cette entreprise est considérée comme une grande entreprise"),
            ("20", "Cette entreprise est considérée comme une entreprise de taille moyenne"),
            ("15", "Cette entreprise est considérée comme une petite entreprise"),
            ("10", "Inconnu de nos sources"),
        ]
        
        if dry_run:
            self.stdout.write("[WARNING] DRY RUN MODE - No data will be saved")
            self.simulate_import(notation_data, clear_data, hard_delete)
            return
        
        try:
            with transaction.atomic():
                # Étape 1: Vider les données existantes si demandé
                if clear_data:
                    self.clear_existing_data(hard_delete)
                
                # Étape 2: Importer les nouvelles données
                stats = self.import_data(notation_data)
                
                self.stdout.write("[SUCCESS] Successfully imported Modèle de notation data!")
                self.print_stats(stats)
                
        except Exception as e:
            self.stdout.write(f"[ERROR] Error: {str(e)}")
            raise
    
    def clear_existing_data(self, hard_delete=False):
        """Vide toutes les données existantes du modèle ModeleNotation"""
        self.stdout.write("[WARNING] Clearing existing Modèle de notation data...")
        
        # Compter AVANT suppression (inclut les soft-deleted si on veut)
        count_all = ModeleNotation.objects.all().count()
        count_active = ModeleNotation.objects.all_with_deleted().filter(deleted__isnull=True).count()
        
        if hard_delete:
            # SUPPRESSION DÉFINITIVE (bypass safedelete)
            deleted_count, _ = ModeleNotation.objects.all_with_deleted().delete()
            self.stdout.write(f"[SUCCESS] Permanently deleted {deleted_count} entries (including soft-deleted)")
        else:
            # SOFT DELETE seulement (le comportement normal)
            deleted_count = ModeleNotation.objects.all().delete()[0]
            self.stdout.write(f"[SUCCESS] Soft-deleted {deleted_count} active entries")
            self.stdout.write(f"[INFO] Total entries in DB (including soft-deleted): {count_all}")
            self.stdout.write(f"[INFO] Active entries before delete: {count_active}")
    
    def import_data(self, entries):
        """Importe les données dans le modèle ModeleNotation"""
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        self.stdout.write("Starting Modèle de notation data import...")
        
        # Traiter chaque entrée avec update_or_create
        for code, libelle in entries:
            # Utiliser update_or_create pour éviter les doublons
            obj, created = ModeleNotation.objects.update_or_create(
                code=code,
                defaults={
                    'libelle': libelle,
                    'deleted': None  # S'assurer que c'est restauré si soft-deleted
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"[OK] Created: {code} - {libelle}")
            else:
                updated_count += 1
                self.stdout.write(f"[UPD] Updated: {code} - {libelle}")
        
        return {
            'created': created_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'total': len(entries)
        }
    
    def simulate_import(self, entries, clear_data, hard_delete):
        """Simule l'importation sans enregistrer en base de données"""
        self.stdout.write("="*60)
        self.stdout.write("DRY RUN - SIMULATION ONLY")
        self.stdout.write("="*60)
        
        if clear_data:
            if hard_delete:
                self.stdout.write("[WARNING] Would PERMANENTLY delete all ModeleNotation data (including soft-deleted)")
            else:
                self.stdout.write("[WARNING] Would soft-delete all active ModeleNotation data")
        
        self.stdout.write("\nEntries to import:")
        for code, libelle in entries:
            # Vérifier si existe déjà
            exists = ModeleNotation.objects.filter(code=code).exists()
            exists_deleted = ModeleNotation.objects.all_with_deleted().filter(code=code, deleted__isnull=False).exists()
            
            status = "[NEW]"
            if exists:
                status = "[EXISTS]"
            elif exists_deleted:
                status = "[SOFT-DELETED]"
            
            self.stdout.write(f"  {status} {code}: {libelle}")
        
        # Vérifier les doublons potentiels
        codes = [code for code, _ in entries]
        duplicates = {code for code in codes if codes.count(code) > 1}
        
        if duplicates:
            self.stdout.write(f"\n[ERROR] WARNING: Duplicate codes in source data: {duplicates}")
        else:
            self.stdout.write("\n[SUCCESS] No duplicate codes in source data")
        
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
        self.stdout.write(f"Entries skipped: {stats['skipped']}")
        self.stdout.write("="*50)