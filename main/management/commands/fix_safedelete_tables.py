# management/commands/fix_safedelete_tables.py
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Corrige toutes les tables SafeDelete avec problème NOT NULL'
    
    def handle(self, *args, **options):
        self.stdout.write("="*60)
        self.stdout.write("CORRECTION DES TABLES SAFEDELETE")
        self.stdout.write("="*60)
        
        # Liste de toutes les tables qui pourraient avoir SafeDelete
        all_tables_sql = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name LIKE 'main_%'
            ORDER BY table_name;
        """
        
        with connection.cursor() as cursor:
            cursor.execute(all_tables_sql)
            all_tables = [row[0] for row in cursor.fetchall()]
            
            self.stdout.write(f"Tables trouvées: {len(all_tables)}\n")
            
            for table in all_tables:
                # Vérifier si la table a des colonnes SafeDelete
                cursor.execute("""
                    SELECT column_name, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    AND column_name IN ('deleted', 'deleted_by_cascade');
                """, [table])
                
                columns = cursor.fetchall()
                
                if not columns:
                    continue  # Pas une table SafeDelete
                
                self.stdout.write(f"\n{table}:")
                
                for col_name, is_nullable in columns:
                    if is_nullable == 'NO':
                        self.stdout.write(self.style.WARNING(f"  ✗ {col_name}: NOT NULL"))
                        
                        # Essayer de corriger
                        try:
                            cursor.execute(f"""
                                ALTER TABLE {table} 
                                ALTER COLUMN {col_name} DROP NOT NULL;
                            """)
                            self.stdout.write(self.style.SUCCESS(f"    ✓ Corrigé (rendu nullable)"))
                        except Exception as e:
                            error_msg = str(e)
                            
                            # Essayer avec valeur par défaut
                            if col_name == 'deleted_by_cascade':
                                try:
                                    cursor.execute(f"""
                                        ALTER TABLE {table} 
                                        ALTER COLUMN {col_name} SET DEFAULT FALSE;
                                    """)
                                    self.stdout.write(self.style.SUCCESS(f"    ✓ Défaut FALSE défini"))
                                except:
                                    self.stdout.write(self.style.ERROR(f"    ✗ Erreur: {error_msg[:80]}"))
                            else:
                                self.stdout.write(self.style.ERROR(f"    ✗ Erreur: {error_msg[:80]}"))
                    else:
                        self.stdout.write(self.style.SUCCESS(f"  ✓ {col_name}: NULLABLE"))
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("CORRECTION TERMINÉE")
        self.stdout.write("="*60)
        
        # Vérifier le résultat
        self.stdout.write("\nVérification finale...")
        
        problematic_tables = []
        with connection.cursor() as cursor:
            for table in all_tables:
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = %s
                    AND column_name IN ('deleted', 'deleted_by_cascade')
                    AND is_nullable = 'NO';
                """, [table])
                
                if cursor.fetchall():
                    problematic_tables.append(table)
        
        if problematic_tables:
            self.stdout.write(self.style.ERROR(f"\n⚠ Tables toujours problématiques: {problematic_tables}"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ Toutes les tables SafeDelete sont correctes!"))