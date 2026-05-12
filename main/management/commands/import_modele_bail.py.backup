# main/management/commands/import_modeles_bail.py
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import ModeleBail
from datetime import datetime

class Command(BaseCommand):
    help = "Importe ou met à jour les modèles de bail"
    
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

    def handle(self, *args, **options):
        # Supprimer l'utilisation de _() ou l'importer localement
        from django.utils.translation import gettext as _
        
        self.stdout.write("[SUCCESS] " + "Début de l'importation des modèles de bail...")
        
        # Données à importer
        modeles_bail_data = [
            {'code': '1', 'libelle_fr': 'Usine', 'poids': 1.0},
            {'code': '2', 'libelle_fr': 'Bureaux', 'poids': 0.25},
            {'code': '3', 'libelle_fr': 'Entrepôt', 'poids': 0.10},
            {'code': '4', 'libelle_fr': 'Entrepôt et bureaux', 'poids': 0.10},
            {'code': '5', 'libelle_fr': "Salle d'exposition", 'poids': 0.10},
            {'code': '6', 'libelle_fr': "Bureau et usine", 'poids': 0.10},
            {'code': '7', 'libelle_fr': "Entrepôt, bureau et usine", 'poids': 0.10},
            {'code': '8', 'libelle_fr': "Locataire des locaux", 'poids': 0.10},
            {'code': '9', 'libelle_fr': "Propriétaire des locaux", 'poids': 0.50},
            {'code': '10', 'libelle_fr': "Showroom", 'poids': 0.25},
        ]
        
        year = options['year']
        
        if options['clear'] and not options['dry_run']:
            deleted_count, _ = ModeleBail.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"Supprimé {deleted_count} modèle(s) existant(s)"
            ))
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        if not options['dry_run']:
            with transaction.atomic():
                for index, data in enumerate(modeles_bail_data, start=1):
                    # Format: MDB-YYYY-NN (avec NN sur 2 chiffres)
                    code_complet = f"MDB-{year}-{index:02d}"
                    libelle_complet = data['libelle_fr']
                    
                    modele, created = ModeleBail.objects.update_or_create(
                        code=code_complet,
                        defaults={
                            'libelle': libelle_complet,
                            'poids': data['poids']
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
            for index, data in enumerate(modeles_bail_data, start=1):
                code_complet = f"MDB-{year}-{index:02d}"
                exists = ModeleBail.objects.filter(code=code_complet).exists()
                
                if exists:
                    self.stdout.write(f"[EXIST]  Existe déjà : {code_complet} - {data['libelle_fr']}")
                    skipped_count += 1
                else:
                    self.stdout.write(f"[NEW] À créer : {code_complet} - {data['libelle_fr']}")
                    created_count += 1
        
        # Résumé
        self.stdout.write("\n" + "="*50)
        if options['dry_run']:
            self.stdout.write("[INFO] " + "SIMULATION - Aucune donnée modifiée")
        self.stdout.write("[SUCCESS] " + "Résumé de l'importation :")
        self.stdout.write(f"- Codes générés : MDB-{year}-01 à MDB-{year}-{len(modeles_bail_data):02d}")
        self.stdout.write(f"- Modèles à créer : {created_count}")
        self.stdout.write(f"- Modèles à mettre à jour : {updated_count}")
        if options['dry_run']:
            self.stdout.write(f"- Modèles existants : {skipped_count}")