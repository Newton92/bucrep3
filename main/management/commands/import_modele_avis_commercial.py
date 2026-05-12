# main/management/commands/import_modele_avis_commercial.py
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import ModeleAvisCommercial
from datetime import datetime

class Command(BaseCommand):
    help = "Importe ou met à jour les modèles d'avis commercial"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help="Supprime tous les modèles existants avant l'importation"
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Simule l'importation sans modifier la base de données"
        )
        parser.add_argument(
            '--year',
            type=int,
            default=datetime.now().year,
            help="Année à utiliser dans les codes (défaut: année courante)"
        )
        parser.add_argument(
            '--dataset',
            type=str,
            choices=['developpement', 'notations', 'all'],
            default='all',
            help="Dataset à importer: 'developpement', 'notations', ou 'all' (défaut)"
        )

    def handle(self, *args, **options):
        self.stdout.write("[SUCCESS] " + "Début de l'importation des modèles d'avis commercial...")
        
        year = options['year']
        dataset = options['dataset']
        
        # Dataset 1: Développement commercial (codes spécifiques)
        developpement_data = [
            {'code_num': '5', 'libelle': 'Bon développement commercial', 'poids': 0.4},
            {'code_num': '9', 'libelle': 'Développement commercial en déclin', 'poids': -1.0},
            {'code_num': '7', 'libelle': 'Développement commercial acceptable', 'poids': 0.3},
            {'code_num': '3', 'libelle': 'Développement commercial fort', 'poids': 0.6},
            {'code_num': '8', 'libelle': 'Développement commercial moyennement en déclin', 'poids': -0.5},
            {'code_num': '1', 'libelle': 'Développement commercial ne peut être déterminé par un tiers', 'poids': 0.0},
            {'code_num': '6', 'libelle': 'Développement commercial passable', 'poids': 0.35},
            {'code_num': '4', 'libelle': 'Développement commercial positif', 'poids': 0.5},
            {'code_num': '2', 'libelle': 'Développement commercial très positif', 'poids': 0.7},
        ]
        
        # Dataset 2: Notations génériques (poids à 0.1 comme demandé)
        notations_data = [
            {'libelle': 'Négatif', 'poids': 0.1},
            {'libelle': 'Inconnu', 'poids': 0.1},
            {'libelle': 'Passable', 'poids': 0.1},
            {'libelle': 'Acceptable', 'poids': 0.1},
            {'libelle': 'Moyen', 'poids': 0.1},
            {'libelle': 'Satisfaisant', 'poids': 0.1},
            {'libelle': 'Bon', 'poids': 0.1},
            {'libelle': 'Très bien', 'poids': 0.1},
        ]
        
        # Sélection des données selon l'option
        if dataset == 'developpement':
            data_to_import = developpement_data
            prefix = 'MAC'
        elif dataset == 'notations':
            data_to_import = notations_data
            prefix = 'MAC-NOT'
        else:  # 'all'
            data_to_import = developpement_data + notations_data
            prefix = 'MAC'
        
        if options['clear'] and not options['dry_run']:
            deleted_count, _ = ModeleAvisCommercial.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"Supprimé {deleted_count} modèle(s) d'avis commercial existant(s)"
            ))
        
        created_count = 0
        updated_count = 0
        
        if not options['dry_run']:
            with transaction.atomic():
                for index, data in enumerate(data_to_import, start=1):
                    # Génération des codes selon le dataset
                    if dataset == 'developpement' or (dataset == 'all' and 'code_num' in data):
                        # Dataset développement: codes spécifiques MAC-YYYY-X
                        code_complet = f"MAC-{year}-{data['code_num']}"
                    elif dataset == 'notations':
                        # Dataset notations: codes séquentiels MAC-NOT-YYYY-NN
                        code_complet = f"MAC-NOT-{year}-{index:02d}"
                    else:
                        # Dataset all: pour les notations dans 'all', continuation séquentielle
                        code_complet = f"MAC-{year}-{index+9:02d}"  # Continue après les 9 premiers
                    
                    libelle_complet = data['libelle']
                    poids = data['poids']
                    
                    modele, created = ModeleAvisCommercial.objects.update_or_create(
                        code=code_complet,
                        defaults={
                            'libelle': libelle_complet,
                            'poids': poids
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"[OK] Créé : {code_complet}")
                        )
                        self.stdout.write(
                            f"   Libellé : {libelle_complet}"
                        )
                        self.stdout.write(
                            f"   Poids : {poids}"
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f"[UPD] Mis à jour : {code_complet}")
                        )
        else:
            # Mode simulation
            self.stdout.write("Mode simulation - Aucune donnée ne sera modifiée")
            for index, data in enumerate(data_to_import, start=1):
                if dataset == 'developpement' or (dataset == 'all' and 'code_num' in data):
                    code_complet = f"MAC-{year}-{data['code_num']}"
                elif dataset == 'notations':
                    code_complet = f"MAC-NOT-{year}-{index:02d}"
                else:
                    code_complet = f"MAC-{year}-{index+9:02d}"
                
                exists = ModeleAvisCommercial.objects.filter(code=code_complet).exists()
                
                if exists:
                    self.stdout.write(f"[EXIST]  Existe déjà : {code_complet}")
                    self.stdout.write(f"   Libellé : {data['libelle']}")
                    self.stdout.write(f"   Poids : {data['poids']}")
                else:
                    self.stdout.write(f"[NEW] À créer : {code_complet}")
                    self.stdout.write(f"   Libellé : {data['libelle']}")
                    self.stdout.write(f"   Poids : {data['poids']}")
                    created_count += 1
        
        # Résumé
        self.stdout.write("\n" + "="*50)
        if options['dry_run']:
            self.stdout.write("[INFO] " + "SIMULATION - Aucune donnée modifiée")
        self.stdout.write("[SUCCESS] " + "Résumé de l'importation :")
        self.stdout.write(f"- Dataset importé : {dataset}")
        self.stdout.write(f"- Nombre total d'éléments : {len(data_to_import)}")
        if dataset == 'all':
            self.stdout.write(f"  - Développement commercial : 9 éléments")
            self.stdout.write(f"  - Notations génériques : 8 éléments")
        self.stdout.write(f"- Modèles créés : {created_count}")
        self.stdout.write(f"- Modèles mis à jour : {updated_count}")