# management/commands/import_locaux.py
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils.translation import gettext_lazy as _
from main.models import Locaux


class Command(BaseCommand):
    help = 'Import des types de locaux (prémises)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprimer les données existantes avant import',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler sans enregistrer en base',
        )
        parser.add_argument(
            '--fix-db',
            action='store_true',
            help='Corriger la structure de la base avant import',
        )

    def handle(self, *args, **options):
        clear_data = options.get('clear', False)
        dry_run = options.get('dry_run', False)
        fix_db = options.get('fix_db', False)
        
        # Données à importer
        locaux_list = [
            '1-Factory',
            '2-Offices',
            '3-Warehouse',
            '4-Warehouse and offices',
            '5-Showroom',
            '6-Office and factory',
            '7-warehouse, office and factory',
        ]
        
        self.stdout.write("="*60)
        self.stdout.write("IMPORT DES TYPES DE LOCAUX")
        self.stdout.write("="*60)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("MODE SIMULATION - Pas de sauvegarde en base"))
            self.simulate_import(locaux_list, clear_data)
            return
        
        if fix_db:
            self.fix_database_structure()
        
        try:
            # Étape 1: Nettoyer si demandé
            if clear_data:
                self.clear_existing_data()
            
            # Étape 2: Importer les données
            stats = self.import_data(locaux_list)
            
            # Étape 3: Afficher les résultats
            self.print_results(stats)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {str(e)}'))
            import traceback
            traceback.print_exc()
    
    def clear_existing_data(self):
        """Supprime les données existantes"""
        self.stdout.write(self.style.WARNING("Suppression des données existantes..."))
        
        try:
            # Compter avant suppression
            count = Locaux.objects.count()
            
            # Suppression logique (soft delete)
            deleted_count = Locaux.objects.all().delete()
            
            if isinstance(deleted_count, tuple):
                deleted_count = deleted_count[0]  # django-safedelete retourne un tuple
            
            self.stdout.write(self.style.SUCCESS(
                f"✓ {deleted_count} type(s) de locaux supprimé(s)"
            ))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠ Impossible de supprimer: {str(e)[:100]}"))
            
            # Essayer avec SQL brut
            try:
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM main_locaux;")
                    self.stdout.write(self.style.SUCCESS("✓ Données supprimées via SQL"))
            except Exception as sql_error:
                self.stdout.write(self.style.ERROR(f"✗ Erreur SQL: {str(sql_error)[:100]}"))
    
    def fix_database_structure(self):
        """Corrige la structure de la base si nécessaire"""
        self.stdout.write("Vérification de la structure de la base...")
        
        with connection.cursor() as cursor:
            try:
                # Vérifier si la table existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'main_locaux'
                    );
                """)
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    self.stdout.write(self.style.WARNING("⚠ La table 'main_locaux' n'existe pas"))
                    return
                
                # Vérifier les colonnes problématiques de SafeDelete
                cursor.execute("""
                    SELECT column_name, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'main_locaux'
                    AND column_name IN ('deleted', 'deleted_by_cascade');
                """)
                
                problematic = []
                for col_name, is_nullable in cursor.fetchall():
                    if is_nullable == 'NO':
                        problematic.append(col_name)
                
                if problematic:
                    self.stdout.write(self.style.WARNING(
                        f"⚠ Colonnes NOT NULL problématiques: {problematic}"
                    ))
                    
                    for column in problematic:
                        try:
                            cursor.execute(f"""
                                ALTER TABLE main_locaux 
                                ALTER COLUMN {column} DROP NOT NULL;
                            """)
                            self.stdout.write(self.style.SUCCESS(f"  ✓ Colonne '{column}' rendue nullable"))
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"  ✗ Impossible de modifier {column}: {str(e)[:100]}"))
                            
                            # Essayer de mettre une valeur par défaut
                            if column == 'deleted_by_cascade':
                                try:
                                    cursor.execute(f"""
                                        ALTER TABLE main_locaux 
                                        ALTER COLUMN {column} SET DEFAULT FALSE;
                                    """)
                                    self.stdout.write(self.style.SUCCESS(f"  ✓ Valeur par défaut FALSE pour '{column}'"))
                                except:
                                    pass
                else:
                    self.stdout.write(self.style.SUCCESS("✓ Structure de la base OK"))
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠ Erreur vérification structure: {str(e)[:100]}"))
    
    def import_data(self, locaux_list):
        """Importe les données dans le modèle Locaux"""
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        self.stdout.write(f"Import de {len(locaux_list)} types de locaux...")
        
        for index, nom in enumerate(locaux_list, 1):
            try:
                # Nettoyer le nom
                clean_nom = self.clean_nom(nom)
                
                # Vérifier si existe déjà
                existing = self.find_existing(clean_nom)
                
                if existing:
                    # Vérifier si identique
                    if existing.nom == clean_nom:
                        skipped_count += 1
                        self.stdout.write(self.style.WARNING(
                            f'↺ Existe déjà ({index}/{len(locaux_list)}): {clean_nom}'
                        ))
                    else:
                        # Mettre à jour
                        existing.nom = clean_nom
                        existing.save()
                        updated_count += 1
                        self.stdout.write(self.style.WARNING(
                            f'[MAJ] Mis à jour ({index}/{len(locaux_list)}): {clean_nom}'
                        ))
                else:
                    # Créer nouveau
                    try:
                        # Méthode normale
                        Locaux.objects.create(nom=clean_nom)
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'✓ Créé ({index}/{len(locaux_list)}): {clean_nom}'
                        ))
                    except Exception as create_error:
                        # Fallback: essayer avec SQL brut
                        if 'NOT NULL' in str(create_error) and 'deleted_by_cascade' in str(create_error):
                            try:
                                self.create_with_sql(clean_nom)
                                created_count += 1
                                self.stdout.write(self.style.SUCCESS(
                                    f'✓ Créé via SQL ({index}/{len(locaux_list)}): {clean_nom}'
                                ))
                            except Exception as sql_error:
                                error_count += 1
                                self.stdout.write(self.style.ERROR(
                                    f'✗ Erreur SQL ({index}/{len(locaux_list)}): {str(sql_error)[:100]}'
                                ))
                        else:
                            error_count += 1
                            self.stdout.write(self.style.ERROR(
                                f'✗ Erreur ({index}/{len(locaux_list)}): {str(create_error)[:100]}'
                            ))
                            
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f'✗ Erreur générale ({index}/{len(locaux_list)}): {str(e)[:100]}'
                ))
        
        return {
            'total': len(locaux_list),
            'created': created_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'errors': error_count,
        }
    
    def clean_nom(self, nom):
        """Retourne le nom tel quel (les préfixes numériques sont conservés)"""
        if hasattr(nom, '_proxy____args'):
            nom = str(nom)
        return nom.strip()
    
    def find_existing(self, nom):
        """Recherche un local existant"""
        # Recherche exacte
        existing = Locaux.objects.filter(nom=nom).first()
        if existing:
            return existing
        
        # Recherche insensible à la casse
        existing = Locaux.objects.filter(nom__iexact=nom).first()
        if existing:
            return existing
        
        # Recherche avec préfixe numérique
        variations = [
            f"1- {nom}",
            f"2- {nom}",
            f"3- {nom}",
            f"4- {nom}",
            f"5- {nom}",
            f"6- {nom}",
            f"7- {nom}",
        ]
        
        for variation in variations:
            existing = Locaux.objects.filter(nom=variation).first()
            if existing:
                return existing
        
        return None
    
    def create_with_sql(self, nom):
        """Crée un enregistrement avec SQL brut"""
        with connection.cursor() as cursor:
            # Vérifier les colonnes disponibles
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'main_locaux';
            """)
            
            columns = [row[0] for row in cursor.fetchall()]
            
            if 'deleted_by_cascade' in columns:
                # Table avec SafeDelete
                sql = """
                    INSERT INTO main_locaux (nom, deleted_by_cascade)
                    VALUES (%s, FALSE)
                    RETURNING id;
                """
            else:
                # Table sans SafeDelete
                sql = """
                    INSERT INTO main_locaux (nom)
                    VALUES (%s)
                    RETURNING id;
                """
            
            cursor.execute(sql, [nom])
            return cursor.fetchone()[0]
    
    def simulate_import(self, locaux_list, clear_data):
        """Simule l'importation"""
        self.stdout.write("\nSIMULATION D'IMPORT:")
        self.stdout.write("-" * 40)
        
        if clear_data:
            self.stdout.write("⚠ Les données existantes seraient supprimées")
        
        self.stdout.write(f"\n{len(locaux_list)} types de locaux à importer:\n")
        
        for i, nom in enumerate(locaux_list, 1):
            clean_nom = self.clean_nom(nom)
            
            # Vérifier si existe déjà
            existing = self.find_existing(clean_nom)
            
            if existing:
                status = "EXISTE DÉJÀ"
                style = self.style.WARNING
            else:
                status = "NOUVEAU"
                style = self.style.SUCCESS
            
            self.stdout.write(style(f"{i:2}. {clean_nom:30} [{status}]"))
        
        self.stdout.write("\n" + "-" * 40)
        self.stdout.write(f"Total: {len(locaux_list)} entrées")
        
        # Vérifier les longueurs
        for nom in locaux_list:
            clean_nom = self.clean_nom(nom)
            if len(clean_nom) > 100:
                self.stdout.write(self.style.ERROR(
                    f"⚠ '{clean_nom[:30]}...' dépasse 100 caractères ({len(clean_nom)})"
                ))
    
    def print_results(self, stats):
        """Affiche les résultats de l'import"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("RÉSULTATS DE L'IMPORT")
        self.stdout.write("="*50)
        
        self.stdout.write(f"Total à importer: {stats['total']}")
        self.stdout.write(f"Céréés: {stats['created']}")
        self.stdout.write(f"Mis à jour: {stats['updated']}")
        self.stdout.write(f"Déjà existants: {stats['skipped']}")
        self.stdout.write(f"Erreurs: {stats['errors']}")
        
        total_processed = stats['created'] + stats['updated'] + stats['skipped'] + stats['errors']
        
        if total_processed == stats['total']:
            self.stdout.write(self.style.SUCCESS("✓ Toutes les entrées traitées"))
        else:
            self.stdout.write(self.style.WARNING(
                f"⚠ Incohérence: {total_processed}/{stats['total']} traités"
            ))
        
        # Afficher le contenu final
        self.stdout.write("\n" + "-"*50)
        self.stdout.write("CONTENU ACTUEL DE LA BASE")
        self.stdout.write("-"*50)
        
        try:
            count = Locaux.objects.count()
            self.stdout.write(f"Total en base: {count} type(s) de locaux")
            
            if count > 0:
                self.stdout.write("\nListe des types de locaux:")
                for local in Locaux.objects.all().order_by('id'):
                    self.stdout.write(f"  • {local.nom}")
            
            # Vérifier les données manquantes
            expected = {
                '1-Factory', '2-Offices', '3-Warehouse', '4-Warehouse and offices',
                '5-Showroom', '6-Office and factory', '7-warehouse, office and factory'
            }
            actual = {local.nom for local in Locaux.objects.all()}
            missing = expected - actual

            if missing:
                self.stdout.write(self.style.WARNING(f"\n⚠ Manquants: {missing}"))
            else:
                self.stdout.write(self.style.SUCCESS("\n✓ Tous les types de locaux sont présents"))
                
        except Exception as e:
            self.stdout.write(f"Erreur lecture base: {str(e)}")


# Version alternative simplifiée
class CommandSimple(BaseCommand):
    """Version simplifiée sans gestion avancée d'erreurs"""
    help = 'Import rapide des types de locaux'
    
    def handle(self, *args, **options):
        LOCAUX = [
            '1-Factory',
            '2-Offices',
            '3-Warehouse',
            '4-Warehouse and offices',
            '5-Showroom',
            '6-Office and factory',
            '7-warehouse, office and factory',
        ]
        
        self.stdout.write("Import rapide des locaux...")
        
        created = 0
        errors = 0
        
        for nom in LOCAUX:
            try:
                # Vérifier si existe
                if not Locaux.objects.filter(nom=nom).exists():
                    Locaux.objects.create(nom=nom)
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"✓ {nom}"))
                else:
                    self.stdout.write(self.style.WARNING(f"↺ {nom} (existe déjà)"))
                    
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"✗ {nom}: {str(e)[:50]}"))
        
        self.stdout.write(f"\nRésumé: {created} créés, {errors} erreurs")
        self.stdout.write(f"Total en base: {Locaux.objects.count()}")
        
        
        
        
# Import normal
# python manage.py import_locaux

# Supprimer avant import
# python manage.py import_locaux --clear

# Simulation seulement
# python manage.py import_locaux --dry-run

# Corriger la base puis importer
# python manage.py import_locaux --fix-db --clear

# Version simplifiée
# python manage.py import_locaux_simple  # Si vous créez la version simple