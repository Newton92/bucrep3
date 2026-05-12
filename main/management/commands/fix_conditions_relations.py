# management/commands/fix_conditions_relations.py
from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Vérifie et corrige les relations ManyToMany des conditions'
    
    def handle(self, *args, **options):
        self.stdout.write("="*60)
        self.stdout.write("VÉRIFICATION DES RELATIONS CONDITIONS")
        self.stdout.write("="*60)
        
        self.check_m2m_tables()
        self.check_model_structure()
        self.create_missing_relations()
    
    def check_m2m_tables(self):
        """Vérifie les tables ManyToMany"""
        self.stdout.write("\n1. Vérification des tables M2M...")
        
        expected_tables = [
            'main_conditionachat_local',
            'main_conditionachat_importation',
            'main_conditiondevente_local',
        ]
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name LIKE 'main_condition%';
            """)
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            for table in expected_tables:
                if table in existing_tables:
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {table}"))
                else:
                    self.stdout.write(self.style.ERROR(f"  ✗ {table} (manquante)"))
                    
                    # Afficher la structure attendue
                    if 'conditionachat_local' in table:
                        self.stdout.write("    Structure attendue:")
                        self.stdout.write("    - conditionachat_id (FK vers ConditionAchat)")
                        self.stdout.write("    - listeconditionachat_id (FK vers ListeConditionAchat)")
    
    def check_model_structure(self):
        """Vérifie la structure des modèles"""
        self.stdout.write("\n2. Vérification des modèles...")
        
        try:
            from main.models import ConditionAchat, ConditionDeVente
            
            # ConditionAchat
            self.stdout.write("\nConditionAchat:")
            for field in ConditionAchat._meta.many_to_many:
                self.stdout.write(f"  • {field.name} -> {field.related_model.__name__}")
            
            # ConditionDeVente
            self.stdout.write("\nConditionDeVente:")
            for field in ConditionDeVente._meta.many_to_many:
                self.stdout.write(f"  • {field.name} -> {field.related_model.__name__}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur: {str(e)}"))
    
    def create_missing_relations(self):
        """Crée les relations manquantes"""
        self.stdout.write("\n3. Création des relations manquantes...")
        
        # Vérifier si les modèles de base existent
        try:
            from main.models import ListeConditionAchat, ListeConditionVente
            
            # Créer quelques exemples de données de test
            if not ListeConditionAchat.objects.exists():
                self.stdout.write("Création des conditions d'achat de base...")
                conditions = [
                    "Paiement comptant",
                    "Paiement à réception",
                    "Paiement par virement",
                ]
                for condition in conditions:
                    ListeConditionAchat.objects.get_or_create(nom=condition)
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {condition}"))
            
            if not ListeConditionVente.objects.exists():
                self.stdout.write("Création des conditions de vente de base...")
                conditions = [
                    "Espèces",
                    "Chèque",
                    "Virement bancaire",
                ]
                for condition in conditions:
                    ListeConditionVente.objects.get_or_create(nom=condition)
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {condition}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Impossible de créer les données: {str(e)}"))