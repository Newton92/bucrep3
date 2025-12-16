# main/management/commands/import_modele_age_societe.py
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import ModeleAgeSociete
from datetime import datetime

class Command(BaseCommand):
    help = "Importe ou met à jour les modèles d'âge de société"
    
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
            '--prefix',
            type=str,
            default='MAS',
            help="Préfixe pour les codes (défaut: MAS pour Modèle d'Âge de Société)"
        )
        parser.add_argument(
            '--tri-par-age',
            action='store_true',
            help="Trie les données par âge croissant plutôt que par code"
        )

    def handle(self, *args, **options):
        self.stdout.write("[SUCCESS] " + "Début de l'importation des modèles d'âge de société...")
        
        # Données à importer - triées par âge croissant
        modeles_age_societe_data = [
            {'code_num': '1', 'libelle': 'Moins de un an', 'poids': 0.0, 'ordre_age': 1},
            {'code_num': '2', 'libelle': '1 an', 'poids': 0.1, 'ordre_age': 2},
            {'code_num': '3', 'libelle': '2-4 ans', 'poids': 0.2, 'ordre_age': 3},
            {'code_num': '4', 'libelle': '5-6 ans', 'poids': 0.4, 'ordre_age': 4},
            {'code_num': '5', 'libelle': '7-8 ans', 'poids': 0.6, 'ordre_age': 5},
            {'code_num': '6', 'libelle': '9-10 ans', 'poids': 0.8, 'ordre_age': 6},
            {'code_num': '7', 'libelle': 'Supérieur à 10 ans', 'poids': 1.0, 'ordre_age': 7},
        ]
        
        year = options['year']
        prefix = options['prefix']
        
        # Tri des données si demandé
        if options['tri_par_age']:
            # Tri par ordre d'âge croissant (déjà le cas dans la liste)
            data_to_process = sorted(modeles_age_societe_data, key=lambda x: x['ordre_age'])
            self.stdout.write("[OK] Données triées par âge croissant")
        else:
            # Tri par code numérique
            data_to_process = sorted(modeles_age_societe_data, key=lambda x: int(x['code_num']))
            self.stdout.write("[OK] Données triées par code")
        
        if options['clear'] and not options['dry_run']:
            deleted_count, _ = ModeleAgeSociete.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"Supprimé {deleted_count} modèle(s) d'âge de société existant(s)"
            ))
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        if not options['dry_run']:
            with transaction.atomic():
                for data in data_to_process:
                    # Format: MAS-YYYY-N (avec N correspondant au code_num original)
                    code_complet = f"{prefix}-{year}-{data['code_num']}"
                    libelle_complet = data['libelle']
                    poids = data['poids']
                    
                    modele, created = ModeleAgeSociete.objects.update_or_create(
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
                            f"   Âge : {libelle_complet}"
                        )
                        self.stdout.write(
                            f"   Poids : {poids}"
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f"[UPD] Mis à jour : {code_complet}")
                        )
                        self.stdout.write(
                            f"   Âge : {libelle_complet}"
                        )
        else:
            # Mode simulation
            self.stdout.write("Mode simulation - Aucune donnée ne sera modifiée")
            for data in data_to_process:
                code_complet = f"{prefix}-{year}-{data['code_num']}"
                exists = ModeleAgeSociete.objects.filter(code=code_complet).exists()
                
                if exists:
                    self.stdout.write(f"[EXIST]  Existe déjà : {code_complet}")
                    self.stdout.write(f"   Âge : {data['libelle']}")
                    self.stdout.write(f"   Poids : {data['poids']}")
                    skipped_count += 1
                else:
                    self.stdout.write(f"[NEW] À créer : {code_complet}")
                    self.stdout.write(f"   Âge : {data['libelle']}")
                    self.stdout.write(f"   Poids : {data['poids']}")
                    created_count += 1
        
        # Résumé
        self.stdout.write("\n" + "="*50)
        if options['dry_run']:
            self.stdout.write("[INFO] " + "SIMULATION - Aucune donnée modifiée")
        
        self.stdout.write("[SUCCESS] " + "Résumé de l'importation :")
        
        # Afficher l'ordre logique des âges
        self.stdout.write("\n[STATS] Échelle des âges (avec poids):")
        for data in sorted(data_to_process, key=lambda x: x['ordre_age']):
            self.stdout.write(f"  - {data['libelle']}: poids = {data['poids']}")
        
        self.stdout.write(f"\n- Codes générés : {prefix}-{year}-01 à {prefix}-{year}-{len(data_to_process):02d}")
        self.stdout.write(f"- Modèles créés : {created_count}")
        self.stdout.write(f"- Modèles mis à jour : {updated_count}")
        if options['dry_run']:
            self.stdout.write(f"- Modèles existants : {skipped_count}")