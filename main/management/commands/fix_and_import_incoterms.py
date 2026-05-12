# management/commands/fix_and_import_incoterms.py
from django.core.management.base import BaseCommand
from django.db import connection, transaction

class Command(BaseCommand):
    help = 'Fix database and import Incoterms in one command'
    
    def handle(self, *args, **options):
        self.stdout.write("="*60)
        self.stdout.write("FIX AND IMPORT INCOTERMS")
        self.stdout.write("="*60)
        
        # Étape 1: Corriger la structure de la base
        self.fix_database_structure()
        
        # Étape 2: Importer les données
        self.import_incoterms()
    
    def fix_database_structure(self):
        """Corrige les colonnes NOT NULL problématiques"""
        self.stdout.write("\n1. Fixing database structure...")
        
        with connection.cursor() as cursor:
            # Vérifier si les colonnes existent
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'main_listeimportation' 
                AND column_name IN ('deleted', 'deleted_by_cascade');
            """)
            
            columns = [row[0] for row in cursor.fetchall()]
            
            if not columns:
                self.stdout.write("  No SafeDelete columns found.")
                return
            
            for column in columns:
                try:
                    # Essayer de rendre la colonne nullable
                    cursor.execute(f"""
                        ALTER TABLE main_listeimportation 
                        ALTER COLUMN {column} DROP NOT NULL;
                    """)
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Column '{column}' is now nullable"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  ⚠ Could not alter {column}: {str(e)[:100]}"))
                    
                    # Essayer de mettre une valeur par défaut si pas nullable
                    if column == 'deleted_by_cascade':
                        try:
                            cursor.execute(f"""
                                ALTER TABLE main_listeimportation 
                                ALTER COLUMN {column} SET DEFAULT FALSE;
                            """)
                            self.stdout.write(self.style.SUCCESS(f"  ✓ Set default FALSE for '{column}'"))
                        except:
                            pass
    
    def import_incoterms(self):
        """Importe les données d'Incoterms"""
        self.stdout.write("\n2. Importing Incoterms...")
        
        incoterms = [
            "1- EXW – Ex-Works – À l'usine",
            "2- FCA – Free-CArrier – Franco-transporteur",
            "3- CPT – Carriage Paid To – Port payé jusqu'à",
            "4- CIP – Carriage Insurance Paid to – Port payé, assurance comprise jusqu'à DAP",
            "5- DAP – Delivered At Place – Rendu au lieu de destination",
            "6- DPU – Delivered at place unloaded, rendu au lieu de destination (ancien DAT)",
            "7- DDP – Delivered Duty Paid – Rendu droits acquittés",
            "8- FAS (Free alongside ship)",
            "9- FOB (Free on board)",
            "10- CFR (Cost and freight)",
            "11- CIF (Cost, insurance and freight)",
        ]
        
        with connection.cursor() as cursor:
            # D'abord vider la table
            cursor.execute("DELETE FROM main_listeimportation;")
            self.stdout.write("  Cleared existing data")
            
            # Insérer les nouveaux
            for i, incoterm in enumerate(incoterms, 1):
                try:
                    # Vérifier les colonnes disponibles
                    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'main_listeimportation'")
                    available_cols = [row[0] for row in cursor.fetchall()]
                    
                    if 'deleted_by_cascade' in available_cols:
                        # Avec SafeDelete
                        cursor.execute("""
                            INSERT INTO main_listeimportation (libelle, deleted_by_cascade)
                            VALUES (%s, FALSE);
                        """, [incoterm])
                    else:
                        # Sans SafeDelete
                        cursor.execute("""
                            INSERT INTO main_listeimportation (libelle)
                            VALUES (%s);
                        """, [incoterm])
                    
                    self.stdout.write(self.style.SUCCESS(f"  {i:2}. {incoterm[:40]}..."))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  {i:2}. Error: {str(e)[:100]}"))
            
            # Compter
            cursor.execute("SELECT COUNT(*) FROM main_listeimportation;")
            count = cursor.fetchone()[0]
            
            self.stdout.write(f"\n  Total imported: {count} Incoterms")