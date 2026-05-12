# management/commands/init_conditions.py
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils.translation import gettext_lazy as _

class Command(BaseCommand):
    help = 'Initialisation complète du système de conditions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la réinitialisation même si des données existent',
        )
        parser.add_argument(
            '--skip-m2m',
            action='store_true',
            help='Sauter la vérification des relations ManyToMany',
        )
    
    def handle(self, *args, **options):
        force = options.get('force', False)
        skip_m2m = options.get('skip_m2m', False)
        
        self.stdout.write("="*70)
        self.stdout.write("INITIALISATION DU SYSTÈME DE CONDITIONS")
        self.stdout.write("="*70)
        
        # 1. Vérifier les modèles
        self.check_models()
        
        # 2. Vérifier les tables M2M
        if not skip_m2m:
            self.check_m2m_tables()
        
        # 3. Importer les données de base
        self.import_base_data(force)
        
        # 4. Vérifier le résultat
        self.verify_import()
    
    def check_models(self):
        """Vérifie que les modèles existent"""
        self.stdout.write("\n1. Vérification des modèles...")
        
        models_to_check = [
            'ListeConditionAchat',
            'ListeConditionVente',
            'ConditionAchat',
            'ConditionDeVente',
        ]
        
        try:
            from django.apps import apps
            
            for model_name in models_to_check:
                try:
                    model = apps.get_model('main', model_name)
                    field_count = len(model._meta.fields)
                    m2m_count = len(model._meta.many_to_many)
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✓ {model_name}: {field_count} champs, {m2m_count} relations M2M"
                    ))
                except LookupError:
                    self.stdout.write(self.style.ERROR(f"  ✗ {model_name} (introuvable)"))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur vérification: {str(e)}"))
    
    def check_m2m_tables(self):
        """Vérifie les tables de relations ManyToMany"""
        self.stdout.write("\n2. Vérification des tables de relations...")
        
        m2m_tables = {
            'main_conditionachat_local': 'ConditionAchat ↔ ListeConditionAchat (local)',
            'main_conditionachat_importation': 'ConditionAchat ↔ ListeConditionAchat (importation)',
            'main_conditiondevente_local': 'ConditionDeVente ↔ ListeConditionVente (local)',
        }
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name IN %s;
            """, [tuple(m2m_tables.keys())])
            
            existing = [row[0] for row in cursor.fetchall()]
            
            for table, description in m2m_tables.items():
                if table in existing:
                    # Vérifier les colonnes
                    cursor.execute(f"""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_name = '{table}';
                    """)
                    columns = cursor.fetchall()
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"  ✓ {description}"
                    ))
                    self.stdout.write(f"    Colonnes: {[col[0] for col in columns]}")
                else:
                    self.stdout.write(self.style.WARNING(f"  ⚠ {description} (manquante)"))
    
    def import_base_data(self, force=False):
        """Importe les données de base"""
        self.stdout.write("\n3. Import des données de base...")
        
        # Données pour ListeConditionAchat
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
        
        # Données pour ListeConditionVente
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
        
        try:
            from main.models import ListeConditionAchat, ListeConditionVente
            
            # Vérifier s'il y a déjà des données
            has_achat_data = ListeConditionAchat.objects.exists()
            has_vente_data = ListeConditionVente.objects.exists()
            
            if (has_achat_data or has_vente_data) and not force:
                self.stdout.write(self.style.WARNING(
                    "Des données existent déjà. Utilisez --force pour écraser."
                ))
                return
            
            # Import avec transaction
            with transaction.atomic():
                # Conditions d'achat
                self.stdout.write("\nConditions d'achat:")
                if force and has_achat_data:
                    ListeConditionAchat.objects.all().delete()
                    self.stdout.write("  Anciennes données supprimées")
                
                for condition in conditions_achat:
                    obj, created = ListeConditionAchat.objects.get_or_create(nom=condition)
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"  ✓ {condition}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"  ↺ {condition} (existe déjà)"))
                
                # Conditions de vente
                self.stdout.write("\nConditions de vente:")
                if force and has_vente_data:
                    ListeConditionVente.objects.all().delete()
                    self.stdout.write("  Anciennes données supprimées")
                
                for condition in conditions_vente:
                    obj, created = ListeConditionVente.objects.get_or_create(nom=condition)
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"  ✓ {condition}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"  ↺ {condition} (existe déjà)"))
                        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur import: {str(e)}"))
            # Essayer avec SQL brut
            self.import_with_sql(conditions_achat, conditions_vente)
    
    def import_with_sql(self, conditions_achat, conditions_vente):
        """Import avec SQL brut en fallback"""
        self.stdout.write("\nEssai avec SQL brut...")
        
        with connection.cursor() as cursor:
            # Conditions d'achat
            for condition in conditions_achat:
                try:
                    cursor.execute("""
                        INSERT INTO main_listeconditionachat (nom)
                        VALUES (%s)
                        ON CONFLICT (nom) DO NOTHING;
                    """, [condition])
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {condition}"))
                except:
                    self.stdout.write(self.style.WARNING(f"  ⚠ {condition} (erreur)"))
            
            # Conditions de vente
            for condition in conditions_vente:
                try:
                    cursor.execute("""
                        INSERT INTO main_listeconditionvente (nom)
                        VALUES (%s)
                        ON CONFLICT (nom) DO NOTHING;
                    """, [condition])
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {condition}"))
                except:
                    self.stdout.write(self.style.WARNING(f"  ⚠ {condition} (erreur)"))
    
    def verify_import(self):
        """Vérifie que l'import s'est bien passé"""
        self.stdout.write("\n4. Vérification de l'import...")
        
        try:
            from main.models import ListeConditionAchat, ListeConditionVente
            
            achat_count = ListeConditionAchat.objects.count()
            vente_count = ListeConditionVente.objects.count()
            
            self.stdout.write(f"  Conditions d'achat: {achat_count}/14")
            self.stdout.write(f"  Conditions de vente: {vente_count}/10")
            
            if achat_count >= 10 and vente_count >= 7:
                self.stdout.write(self.style.SUCCESS("\n✓ Import réussi!"))
            else:
                self.stdout.write(self.style.WARNING("\n⚠ Import partiel, vérifiez les données"))
                
            # Afficher un échantillon
            if achat_count > 0:
                self.stdout.write("\n  Échantillon conditions d'achat:")
                for obj in ListeConditionAchat.objects.all()[:3]:
                    self.stdout.write(f"    • {obj.nom}")
                    
            if vente_count > 0:
                self.stdout.write("\n  Échantillon conditions de vente:")
                for obj in ListeConditionVente.objects.all()[:3]:
                    self.stdout.write(f"    • {obj.nom}")
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur vérification: {str(e)}"))
            
            
            
            
            
            
            
            
            
            
            
            
            
# Import normal des deux types
# python manage.py import_conditions_base

# Import seulement les conditions d'achat
# python manage.py import_conditions_base --type achat

# Import avec suppression préalable
# python manage.py import_conditions_base --clear

# Simulation
# python manage.py import_conditions_base --dry-run

# Version SQL brute
# python manage.py import_conditions_sql

# Initialisation complète
# python manage.py init_conditions

# Initialisation forcée
# python manage.py init_conditions --force

# Vérifier les relations
# python manage.py fix_conditions_relations