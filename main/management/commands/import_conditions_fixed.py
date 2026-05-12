# management/commands/import_conditions_fixed.py
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils.translation import gettext_lazy as _
import sys

class Command(BaseCommand):
    help = 'Import des conditions avec correction SafeDelete'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-db',
            action='store_true',
            help='Corriger la structure de la base avant import',
        )
        parser.add_argument(
            '--sql-only',
            action='store_true',
            help='Utiliser uniquement SQL brut (contourne Django ORM)',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Tester seulement (pas de modification)',
        )

    def handle(self, *args, **options):
        fix_db = options.get('fix_db', False)
        sql_only = options.get('sql_only', False)
        test_mode = options.get('test', False)
        
        self.stdout.write("="*70)
        self.stdout.write("IMPORT DES CONDITIONS (VERSION CORRIGÉE)")
        self.stdout.write("="*70)
        
        if test_mode:
            self.stdout.write(self.style.WARNING("MODE TEST - Pas de modifications"))
            self.test_database_structure()
            return
        
        if fix_db:
            self.fix_database_structure()
        
        if sql_only:
            self.import_with_sql_only()
        else:
            self.import_with_orm()
    
    def test_database_structure(self):
        """Teste la structure de la base"""
        self.stdout.write("\nTest de la structure de la base...")
        
        tables_to_check = [
            'main_listeconditionachat',
            'main_listeconditionvente',
            'main_locaux',
            'main_listeimportation',
        ]
        
        with connection.cursor() as cursor:
            for table in tables_to_check:
                # Vérifier si la table existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, [table])
                
                exists = cursor.fetchone()[0]
                
                if not exists:
                    self.stdout.write(self.style.ERROR(f"  ✗ {table} (n'existe pas)"))
                    continue
                
                # Vérifier les colonnes problématiques
                cursor.execute("""
                    SELECT column_name, is_nullable, data_type
                    FROM information_schema.columns
                    WHERE table_name = %s
                    AND column_name IN ('deleted', 'deleted_by_cascade');
                """, [table])
                
                columns = cursor.fetchall()
                
                if not columns:
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {table} (pas de colonnes SafeDelete)"))
                    continue
                
                self.stdout.write(f"\n  {table}:")
                problems = []
                for col_name, is_nullable, data_type in columns:
                    if is_nullable == 'NO':
                        problems.append(col_name)
                        self.stdout.write(self.style.ERROR(f"    ✗ {col_name}: {data_type}, NULL=NO"))
                    else:
                        self.stdout.write(self.style.SUCCESS(f"    ✓ {col_name}: {data_type}, NULL=YES"))
                
                if problems:
                    self.stdout.write(self.style.WARNING(f"    ⚠ Commande de correction:"))
                    for col in problems:
                        self.stdout.write(f"      ALTER TABLE {table} ALTER COLUMN {col} DROP NOT NULL;")
    
    def fix_database_structure(self):
        """Corrige la structure de la base"""
        self.stdout.write("\nCorrection de la structure de la base...")
        
        # Commandes SQL pour corriger
        fix_commands = [
            ("main_listeconditionachat", "ALTER TABLE main_listeconditionachat ALTER COLUMN deleted DROP NOT NULL;"),
            ("main_listeconditionachat", "ALTER TABLE main_listeconditionachat ALTER COLUMN deleted_by_cascade DROP NOT NULL;"),
            ("main_listeconditionvente", "ALTER TABLE main_listeconditionvente ALTER COLUMN deleted DROP NOT NULL;"),
            ("main_listeconditionvente", "ALTER TABLE main_listeconditionvente ALTER COLUMN deleted_by_cascade DROP NOT NULL;"),
        ]
        
        success_count = 0
        error_count = 0
        
        with connection.cursor() as cursor:
            for table_name, sql in fix_commands:
                try:
                    cursor.execute(sql)
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {table_name} corrigé"))
                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    
                    # Si l'erreur est que la colonne n'existe pas, c'est normal
                    if 'column' in error_msg.lower() and 'does not exist' in error_msg.lower():
                        self.stdout.write(self.style.WARNING(f"  ⚠ {table_name}: colonne non trouvée (normal si pas SafeDelete)"))
                    else:
                        self.stdout.write(self.style.ERROR(f"  ✗ {table_name}: {error_msg[:100]}"))
        
        self.stdout.write(f"\nRésultat: {success_count} succès, {error_count} erreurs")
    
    def import_with_sql_only(self):
        """Import avec SQL brut uniquement"""
        self.stdout.write("\nImport avec SQL brut...")
        
        # Données pour ListeConditionAchat
        conditions_achat = [
            (1, "Paiement comptant"),
            (2, "Paiement à réception"),
            (3, "Paiement par virement"),
            (4, "Paiement contre documents"),
            (5, "Crédit documentaire"),
            (6, "Lettre de crédit à terme"),
            (7, "Lettre de crédit à vue"),
            (8, "Délai de paiement de 30 à 60 jours date BL"),
            (9, "Délai de paiement de 60 à 90 jours date LB"),
            (10, "Délai de paiement de 90 à 120 Jours date BL"),
            (11, "Délais de paiement de 30 à 60 jours avec pénalités de retard"),
            (12, "Délais de paiement de 60 à 90 jours avec pénalités de retard"),
            (13, "Délais de paiement de 90 à 120 jours avec pénalités de retard"),
            (14, "Délais de paiement de 120 à 180 jours avec pénalités de retard"),
        ]
        
        # Données pour ListeConditionVente
        conditions_vente = [
            (1, "Espèces"),
            (2, "Chèque"),
            (3, "Virement bancaire"),
            (4, "Effets de commerce papier"),
            (5, "Lettre de Change"),
            (6, "Billet à ordre"),
            (7, "Carte de credit/debit"),
            (8, "Délais de paiement de 15 à 30 jours avec pénalités de retard"),
            (9, "Délais de paiement de 30 à 60 jours avec pénalités de retard"),
            (10, "Délais de paiement de 60 à 90 jours avec pénalités de retard"),
        ]
        
        success_count = 0
        error_count = 0
        
        with connection.cursor() as cursor:
            # 1. ListeConditionAchat
            self.stdout.write("\nConditions d'achat:")
            for num, nom in conditions_achat:
                try:
                    # Vérifier la structure de la table
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'main_listeconditionachat';
                    """)
                    
                    columns = [row[0] for row in cursor.fetchall()]
                    
                    if 'deleted_by_cascade' in columns:
                        # Avec SafeDelete
                        sql = """
                            INSERT INTO main_listeconditionachat (nom, deleted, deleted_by_cascade)
                            VALUES (%s, NULL, NULL)
                            ON CONFLICT DO NOTHING;
                        """
                    else:
                        # Sans SafeDelete
                        sql = """
                            INSERT INTO main_listeconditionachat (nom)
                            VALUES (%s)
                            ON CONFLICT DO NOTHING;
                        """
                    
                    cursor.execute(sql, [nom])
                    if cursor.rowcount > 0:
                        success_count += 1
                        self.stdout.write(self.style.SUCCESS(f"  ✓ {nom}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"  ↺ {nom} (déjà existant)"))
                        
                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    
                    # Si erreur NOT NULL, essayer avec valeur par défaut
                    if 'not null' in error_msg.lower() and 'deleted_by_cascade' in error_msg.lower():
                        try:
                            cursor.execute("""
                                INSERT INTO main_listeconditionachat (nom, deleted_by_cascade)
                                VALUES (%s, FALSE)
                                ON CONFLICT DO NOTHING;
                            """, [nom])
                            
                            if cursor.rowcount > 0:
                                success_count += 1
                                self.stdout.write(self.style.SUCCESS(f"  ✓ {nom} (avec FALSE)"))
                            else:
                                self.stdout.write(self.style.WARNING(f"  ↺ {nom} (déjà existant)"))
                        except:
                            self.stdout.write(self.style.ERROR(f"  ✗ {nom}: {error_msg[:80]}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"  ✗ {nom}: {error_msg[:80]}"))
            
            # 2. ListeConditionVente
            self.stdout.write("\nConditions de vente:")
            for num, nom in conditions_vente:
                try:
                    # Vérifier la structure de la table
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'main_listeconditionvente';
                    """)
                    
                    columns = [row[0] for row in cursor.fetchall()]
                    
                    if 'deleted_by_cascade' in columns:
                        # Avec SafeDelete
                        sql = """
                            INSERT INTO main_listeconditionvente (nom, deleted, deleted_by_cascade)
                            VALUES (%s, NULL, NULL)
                            ON CONFLICT DO NOTHING;
                        """
                    else:
                        # Sans SafeDelete
                        sql = """
                            INSERT INTO main_listeconditionvente (nom)
                            VALUES (%s)
                            ON CONFLICT DO NOTHING;
                        """
                    
                    cursor.execute(sql, [nom])
                    if cursor.rowcount > 0:
                        success_count += 1
                        self.stdout.write(self.style.SUCCESS(f"  ✓ {nom}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"  ↺ {nom} (déjà existant)"))
                        
                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    
                    # Si erreur NOT NULL, essayer avec valeur par défaut
                    if 'not null' in error_msg.lower() and 'deleted_by_cascade' in error_msg.lower():
                        try:
                            cursor.execute("""
                                INSERT INTO main_listeconditionvente (nom, deleted_by_cascade)
                                VALUES (%s, FALSE)
                                ON CONFLICT DO NOTHING;
                            """, [nom])
                            
                            if cursor.rowcount > 0:
                                success_count += 1
                                self.stdout.write(self.style.SUCCESS(f"  ✓ {nom} (avec FALSE)"))
                            else:
                                self.stdout.write(self.style.WARNING(f"  ↺ {nom} (déjà existant)"))
                        except:
                            self.stdout.write(self.style.ERROR(f"  ✗ {nom}: {error_msg[:80]}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"  ✗ {nom}: {error_msg[:80]}"))
        
        # Résumé
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"RÉSULTAT: {success_count} importés, {error_count} erreurs")
        
        # Vérifier le contenu final
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM main_listeconditionachat;")
            count_achat = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM main_listeconditionvente;")
            count_vente = cursor.fetchone()[0]
            
            self.stdout.write(f"Conditions d'achat en base: {count_achat}")
            self.stdout.write(f"Conditions de vente en base: {count_vente}")
            
            if count_achat >= 10 and count_vente >= 7:
                self.stdout.write(self.style.SUCCESS("✓ Import réussi!"))
            else:
                self.stdout.write(self.style.WARNING("⚠ Import partiel"))
    
    def import_with_orm(self):
        """Import avec Django ORM (après correction)"""
        self.stdout.write("\nImport avec Django ORM...")
        
        try:
            from main.models import ListeConditionAchat, ListeConditionVente
            
            # Conditions d'achat
            conditions_achat = [
                "Paiement comptant",
                "Paiement à réception",
                "Paiement par virement",
                "Paiement contre documents",
                "Crédit documentaire",
                "Lettre de crédit à terme",
                "Lettre de crédit à vue",
                "Délai de paiement de 30 à 60 jours date BL",
                "Délai de paiement de 60 à 90 jours date LB",
                "Délai de paiement de 90 à 120 Jours date BL",
                "Délais de paiement de 30 à 60 jours avec pénalités de retard",
                "Délais de paiement de 60 à 90 jours avec pénalités de retard",
                "Délais de paiement de 90 à 120 jours avec pénalités de retard",
                "Délais de paiement de 120 à 180 jours avec pénalités de retard",
            ]
            
            # Conditions de vente
            conditions_vente = [
                "Espèces",
                "Chèque",
                "Virement bancaire",
                "Effets de commerce papier",
                "Lettre de Change",
                "Billet à ordre",
                "Carte de credit/debit",
                "Délais de paiement de 15 à 30 jours avec pénalités de retard",
                "Délais de paiement de 30 à 60 jours avec pénalités de retard",
                "Délais de paiement de 60 à 90 jours avec pénalités de retard",
            ]
            
            created_achat = 0
            created_vente = 0
            errors = 0
            
            self.stdout.write("\nConditions d'achat:")
            for condition in conditions_achat:
                try:
                    # Méthode spéciale pour SafeDelete
                    obj = ListeConditionAchat(nom=condition)
                    
                    # Définir explicitement les champs SafeDelete
                    if hasattr(obj, 'deleted'):
                        obj.deleted = None
                    if hasattr(obj, 'deleted_by_cascade'):
                        obj.deleted_by_cascade = None
                    
                    obj.save()
                    created_achat += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {condition}"))
                    
                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f"  ✗ {condition}: {str(e)[:80]}"))
            
            self.stdout.write("\nConditions de vente:")
            for condition in conditions_vente:
                try:
                    # Méthode spéciale pour SafeDelete
                    obj = ListeConditionVente(nom=condition)
                    
                    # Définir explicitement les champs SafeDelete
                    if hasattr(obj, 'deleted'):
                        obj.deleted = None
                    if hasattr(obj, 'deleted_by_cascade'):
                        obj.deleted_by_cascade = None
                    
                    obj.save()
                    created_vente += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {condition}"))
                    
                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f"  ✗ {condition}: {str(e)[:80]}"))
            
            # Résumé
            self.stdout.write("\n" + "="*50)
            self.stdout.write(f"RÉSULTAT:")
            self.stdout.write(f"  Conditions d'achat créées: {created_achat}")
            self.stdout.write(f"  Conditions de vente créées: {created_vente}")
            self.stdout.write(f"  Erreurs: {errors}")
            self.stdout.write(f"  Total en base:")
            self.stdout.write(f"    - Achat: {ListeConditionAchat.objects.count()}")
            self.stdout.write(f"    - Vente: {ListeConditionVente.objects.count()}")
            
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"Erreur import modèles: {str(e)}"))
            self.stdout.write("Utilisez l'option --sql-only")