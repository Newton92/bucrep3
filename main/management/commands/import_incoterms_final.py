# management/commands/import_incoterms_final.py
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils.translation import gettext_lazy as _

class Command(BaseCommand):
    help = 'Import Incoterms data - Workaround for SafeDelete issues'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--truncate',
            action='store_true',
            help='Truncate table before import (SQL TRUNCATE)',
        )
        parser.add_argument(
            '--skip-check',
            action='store_true',
            help='Skip database structure check',
        )
    
    def handle(self, *args, **options):
        truncate = options.get('truncate', False)
        skip_check = options.get('skip_check', False)
        
        # Données à importer
        incoterms = [
            "1- EXW – Ex-Works – À l'usine \n"
            "Le vendeur (expéditeur) met à disposition les marchandises transportées dans un endroit convenu "
            "(obligation minimale pour le vendeur). L'acheteur supporte tous les coûts de transport et de formalités.",
            
            "2- FCA – Free-CArrier – Franco-transporteur\n"
            "Le vendeur livre la marchandise au destinataire désigné et payé par l'acheteur. "
            "Le transfert des risques est matérialisé lors de cette opération. "
            "Si la livraison est effectuée dans les locaux du vendeur, il est responsable du chargement de la marchandise. "
            "Si la livraison a lieu dans un autre endroit, le vendeur n'est plus responsable du déchargement.",
            
            "3- CPT – Carriage Paid To – Port payé jusqu'à\n"
            "La marchandise est livrée au premier transporteur à l'étranger, frais payés par le vendeur, "
            "sans assurance pour le transport. L'acheteur assume les risques et tous les autres frais encourus "
            "par la marchandise dès la remise de la marchandise au premier transporteur. "
            "L'acheteur prend en charge toutes les opérations qui ont lieu à l'arrivée.",
            
            "4- CIP – Carriage Insurance Paid to – Port payé, assurance comprise jusqu'à DAP\n"
            "Règle Incoterms identique au CPT avec comme seule différence l'assurance : "
            "le vendeur prend en charge l'assurance du transport.",
            
            "5- DAP – Delivered At Place – Rendu au lieu de destination\n"
            "Le vendeur prend en charge le transport des marchandises jusqu'au point de livraison convenu. "
            "Il assume les coûts et les risques jusqu'à ce point. "
            "L'acheteur supporte le déchargement et le dédouanement import.",
            
            "6- DPU – Delivered at place unloaded, rendu au lieu de destination (ancien DAT)\n"
            "Le vendeur organise le transport et paie le déchargement au lieu de destination. "
            "Une fois au terminal l'acheteur est responsable de la marchandise et doit effectuer "
            "les formalités d'importation et s'acquitte des droits et taxes liés.",
            
            "7- DDP – Delivered Duty Paid – Rendu droits acquittés\n"
            "Le vendeur livre la marchandise à l'acheteur en ayant tout pris en charge, "
            "y compris les formalités douanières import et le paiement des droits et taxes "
            "(Obligation maximal pour le vendeur).",
            
            "8- FAS (Free alongside ship)\n"
            "Le vendeur règle les frais de transport jusqu'au port d'embarquement et effectue "
            "les formalités d'exportation. La marchandise est livrée le long du navire dans le port "
            "désigné par l'acheteur. Cette livraison marque le transfert des risques, des frais et "
            "des formalités à l'acheteur. L'Incoterm FAS impose au vendeur l'obligation de dédouaner "
            "le fret à l'exportation.",
            
            "9- FOB (Free on board)\n"
            "Le vendeur livre la marchandise sur le navire au port d'embarquement convenu. "
            "Le transfert des charges et des risques se fait lorsque la marchandise est à bord du navire. "
            "Le vendeur doit dédouaner la marchandise.",
            
            "10- CFR (Cost and freight)\n"
            "Le vendeur se charge du transport principal jusqu'au port de destination. "
            "Il se charge des formalités d'export et doit s'acquitter des droits et taxes liés. "
            "Le transfert de frais à lieu à l'arrivée des marchandises au port d'arrivée, "
            "mais le vendeur n'est plus responsable de la marchandise dès que celle-ci a été chargée "
            "sur le port de départ.",
            
            "11- CIF (Cost, insurance and freight)\n"
            "Le vendeur livre la marchandise sur le navire au port d'embarquement convenu. "
            "Le vendeur se charge des formalités d'export et règles les droits et taxes liés. "
            "Le transfert des frais se fait au port de destination mais le transfert des risques a lieu "
            "au port de départ. L'acheteur prend en charge les frais à l'arrivée des marchandises au port "
            "de destination, et les formalités à l'import.",
        ]
        
        if not skip_check:
            self.check_database_structure()
        
        try:
            # Vider la table si demandé
            if truncate:
                self.truncate_table()
            
            # Importer les données
            self.import_with_raw_sql(incoterms)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            traceback.print_exc()
    
    def check_database_structure(self):
        """Vérifie la structure de la table"""
        self.stdout.write("Checking database structure...")
        
        with connection.cursor() as cursor:
            # Vérifier les colonnes de la table
            cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'main_listeimportation'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            self.stdout.write(f"Table structure ({len(columns)} columns):")
            
            for col in columns:
                self.stdout.write(f"  {col[0]:20} {col[1]:15} NULL={col[2]}")
            
            # Vérifier les contraintes NOT NULL problématiques
            problematic = [col[0] for col in columns if col[2] == 'NO' and col[0] in ['deleted', 'deleted_by_cascade']]
            
            if problematic:
                self.stdout.write(self.style.WARNING(
                    f"\nWARNING: Problematic NOT NULL columns: {problematic}"
                ))
                self.stdout.write("You may need to alter these columns to allow NULL:")
                for col in problematic:
                    self.stdout.write(f"  ALTER TABLE main_listeimportation ALTER COLUMN {col} DROP NOT NULL;")
    
    def truncate_table(self):
        """Vide la table avec TRUNCATE (plus propre que DELETE)"""
        self.stdout.write(self.style.WARNING("Truncating table..."))
        
        with connection.cursor() as cursor:
            try:
                cursor.execute("TRUNCATE TABLE main_listeimportation RESTART IDENTITY CASCADE;")
                self.stdout.write(self.style.SUCCESS("Table truncated successfully"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not truncate: {str(e)}"))
                self.stdout.write("Trying DELETE instead...")
                cursor.execute("DELETE FROM main_listeimportation;")
                self.stdout.write(self.style.SUCCESS("Data deleted"))
    
    def import_with_raw_sql(self, incoterms):
        """Importe les données avec SQL brut pour contourner Django ORM"""
        self.stdout.write("Importing Incoterms with raw SQL...")

        # Détecter la structure une seule fois avant la boucle
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'main_listeimportation'"
            )
            columns = [row[0] for row in cursor.fetchall()]

        has_safedelete = 'deleted_by_cascade' in columns
        self.stdout.write(f"SafeDelete fields detected: {has_safedelete}")

        success_count = 0
        error_count = 0

        for i, incoterm in enumerate(incoterms, 1):
            code = "???"
            for inc_code in ['EXW', 'FCA', 'CPT', 'CIP', 'DAP', 'DPU', 'DDP', 'FAS', 'FOB', 'CFR', 'CIF']:
                if inc_code in incoterm:
                    code = inc_code
                    break

            # Chaque INSERT dans son propre curseur pour isoler les erreurs
            try:
                with connection.cursor() as cursor:
                    if has_safedelete:
                        cursor.execute(
                            "INSERT INTO main_listeimportation (libelle, deleted, deleted_by_cascade) "
                            "VALUES (%s, NULL, NULL) RETURNING id;",
                            [incoterm]
                        )
                    else:
                        cursor.execute(
                            "INSERT INTO main_listeimportation (libelle) VALUES (%s) RETURNING id;",
                            [incoterm]
                        )
                    inserted_id = cursor.fetchone()[0]

                success_count += 1
                self.stdout.write(self.style.SUCCESS(f"{i:2}. [{code}] Inserted ID: {inserted_id}"))

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"{i:2}. [{code}] Error: {str(e)[:120]}"))

        # Compter le total final dans un curseur séparé
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM main_listeimportation;")
            total = cursor.fetchone()[0]

        self.stdout.write("\n" + "="*60)
        if error_count == 0:
            self.stdout.write(self.style.SUCCESS(f"SUCCESS: All {success_count} Incoterms imported"))
        else:
            self.stdout.write(self.style.WARNING(f"PARTIAL: {success_count} ok, {error_count} errors"))
        self.stdout.write(f"Total in table: {total}")
        self.stdout.write("="*60)