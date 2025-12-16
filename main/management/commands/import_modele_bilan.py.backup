# main/management/commands/import_modele_bilan.py
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import ModeleBilan
from datetime import datetime

class Command(BaseCommand):
    help = "Importe ou met à jour les modèles de bilan"
    
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
            default='MDB',
            help="Préfixe pour les codes (défaut: MDB pour Modèle De Bilan)"
        )

    def handle(self, *args, **options):
        self.stdout.write("[SUCCESS] " + "Début de l'importation des modèles de bilan...")
        
        # Données à importer
        modeles_bilan_data = [
            {'libelle': 'Classique'},
            {'libelle': 'Syscohada'},
            {'libelle': 'Anglais'},
            {'libelle': 'Bancaire'},
            {'libelle': 'Ifrs Cobac'},
        ]
        
        year = options['year']
        prefix = options['prefix']
        
        if options['clear'] and not options['dry_run']:
            deleted_count, _ = ModeleBilan.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"Supprimé {deleted_count} modèle(s) de bilan existant(s)"
            ))
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        if not options['dry_run']:
            with transaction.atomic():
                for index, data in enumerate(modeles_bilan_data, start=1):
                    # Format: PREFIX-YYYY-NN (avec NN sur 2 chiffres)
                    code_complet = f"{prefix}-{year}-{index:02d}"
                    libelle_complet = data['libelle']
                    
                    modele, created = ModeleBilan.objects.update_or_create(
                        code=code_complet,
                        defaults={
                            'libelle': libelle_complet,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"[OK] Créé : {code_complet} - {libelle_complet}")
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f"[UPD] Mis à jour : {code_complet} - {libelle_complet}")
                        )
        else:
            # Mode simulation
            for index, data in enumerate(modeles_bilan_data, start=1):
                code_complet = f"{prefix}-{year}-{index:02d}"
                exists = ModeleBilan.objects.filter(code=code_complet).exists()
                
                if exists:
                    self.stdout.write(f"[EXIST]  Existe déjà : {code_complet} - {data['libelle']}")
                    skipped_count += 1
                else:
                    self.stdout.write(f"[NEW] À créer : {code_complet} - {data['libelle']}")
                    created_count += 1
        
        # Résumé
        self.stdout.write("\n" + "="*50)
        if options['dry_run']:
            self.stdout.write("[INFO] " + "SIMULATION - Aucune donnée modifiée")
        self.stdout.write("[SUCCESS] " + "Résumé de l'importation :")
        self.stdout.write(f"- Codes générés : {prefix}-{year}-01 à {prefix}-{year}-{len(modeles_bilan_data):02d}")
        self.stdout.write(f"- Modèles créés : {created_count}")
        self.stdout.write(f"- Modèles mis à jour : {updated_count}")
        if options['dry_run']:
            self.stdout.write(f"- Modèles existants : {skipped_count}")