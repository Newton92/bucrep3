# management/commands/import_forme_juridique.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from main.models import FormeJuridique


class Command(BaseCommand):
    help = 'Import Forme juridique data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate import without saving to database',
        )
        parser.add_argument(
            '--no-weights',
            action='store_true',
            help='Import without weights (set all to 0.0)',
        )

    def handle(self, *args, **options):
        clear_data = options['clear']
        dry_run = options.get('dry_run', False)
        no_weights = options.get('no_weights', False)
        
        # Données à importer
        formes_juridiques = [
            # Format: (code, libelle, poids, active, description)
            ("ADPU", "Administration publique", 0.2, True, None),
            ("ASS", "Association", 0.1, True, None),
            ("COOP", "Coopérative", 0.75, True, None),
            ("EI", "Entreprise Individuelle", 0.5, True, None),  # Poids mis à 0.5
            ("EIRL", "Entreprise individuelle à responsabilité limitée", 0.2, True, None),
            ("FEECC", "Fiducie exploitant une entreprise à caractère commercial", 0.25, True, None),
            ("GIE", "Groupement d'intérêt économique", 0.3, True, None),
            ("GRDP", "Groupement de personnes", 1.0, True, None),
            ("LTD", "Private Limited Company", 0.5, True, None),
            ("PART", "Partenariat", 0.2, True, None),
            ("PLC", "Public Limited Company", 1.0, True, None),
            ("PMSBL", "Personne morale sans but lucratif", 0.1, True, None),
            ("PRL", "Partenership à responsibilité limitée", 0.5, True, None),
            ("SA", "Société anonyme", 1.0, True, None),
            ("SAAG", "Société anonyme avec administration générale", 1.0, True, None),
            ("SACA", "Société anonyme avec conseil d'administration", 1.0, True, None),
            ("SAP", "Société anonyme pluripersonnelle", 1.0, True, None),
            ("SARL", "Société à responsabilité limitée pluripersonnelle", 0.5, True, None),
            ("SARLU", "Société à responsabilité limitée unipersonnelle", 0.5, True, None),  # Code modifié pour éviter le doublon avec "SARL U"
            ("SAS", "Société par action simplifiée pluripersonnelle", 0.5, True, None),
            ("SASU", "Société par action simplifiée unipersonnelle", 0.5, True, None),
            ("SAU", "Société anonyme unipersonnelle", 1.0, True, None),
            ("SCFSF", "Société créée de fait et société de fait", 0.1, True, None),
            ("SCI", "Sociétés civiles", 0.25, True, None),
            ("SCIMO", "Sociétés civiles immobilières", 0.25, True, None),
            ("SCP", "Société civile professionnelle", 0.25, True, None),
            ("SCS", "Société en commandite simple", 0.5, True, None),
            ("SEP", "Société en participation", 0.2, True, None),
            ("SETA", "Société d'État", 0.4, True, None),
            ("SNC", "Société en nom collectif", 0.5, True, None),
            ("SPRL", "Société privée à responsabilité limitée", 0.5, True, None),
            ("SSPJ", "Société sans personnalité juridique", 0.0, True, None),
            ("SYDCO", "Syndicat de copropriété", 0.1, True, None),
            # NOUVELLES FORMULES JURIDIQUES (poids = 0.5 par défaut)
            ("EI_FULL", "Entreprise Individuelle (EI)", 0.5, True, None),
            ("SARL_FULL", "Société à Responsabilité Limitée (SARL)", 0.5, True, None),
            ("SARLU_FULL", "Société à Responsabilité Limitée Unipersonnelle (SARL U)", 0.5, True, None),
            ("SCS_FULL", "Société en Commandite Simple (SCS)", 0.5, True, None),
            ("SAS_FULL", "Société par Actions Simplifiée (SAS)", 0.5, True, None),
            ("SNC_FULL", "Société en Nom Collectif (SNC)", 0.5, True, None),
            ("SP_FULL", "Société en Participation (SP)", 0.5, True, None),
            ("GIE_FULL", "Groupement d'Intérêt Economique (GIE)", 0.5, True, None),
            ("ASS_FULL", "Association", 0.5, True, None),
            ("COOP_FULL", "Coopérative de Groupement", 0.5, True, None),
            ("SA_FULL", "Société Anonyme (SA)", 0.5, True, None),
            ("EPIC", "Etablissement Public à Caractère Industriel et Commercial (EPIC)", 0.5, True, None),
            ("EPCC", "Etablissement Public à Caractère Commercial (EPCC)", 0.5, True, None),
            ("SUCC", "Succursale", 0.5, True, None),
            ("FIL", "Filiale", 0.5, True, None),
        ]

        
        # Si option --no-weights est activée, mettre tous les poids à 0.0
        if no_weights:
            formes_juridiques = [
                (code, libelle, 0.0, active, description)
                for code, libelle, poids, active, description in formes_juridiques
            ]
            self.stdout.write(self.style.WARNING("All weights set to 0.0 (--no-weights option)"))
        
        if dry_run:
            self.stdout.write("[WARNING] " + "DRY RUN MODE - No data will be saved")
            self.simulate_import(formes_juridiques, clear_data)
            return
        
        try:
            with transaction.atomic():
                # Étape 1: Vider les données existantes si demandé
                if clear_data:
                    self.clear_existing_data()
                
                # Étape 2: Importer les nouvelles données
                stats = self.import_data(formes_juridiques)
                
                self.stdout.write("[SUCCESS] " + 'Successfully imported Forme juridique data!')
                self.print_stats(stats)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise
    
    def clear_existing_data(self):
        """Vide toutes les données existantes du modèle FormeJuridique"""
        self.stdout.write("[WARNING] " + 'Clearing existing Forme juridique data...')
        
        # Compter avant suppression
        count = FormeJuridique.objects.count()
        
        # Supprimer toutes les entrées
        FormeJuridique.objects.all().delete()
        
        self.stdout.write("[SUCCESS] " + f'Cleared {count} Forme juridique entries.')
    
    def import_data(self, entries):
        """Importe les données dans le modèle FormeJuridique"""
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        self.stdout.write("Starting Forme juridique data import...")
        
        # Traiter chaque entrée
        for code, libelle, poids, active, description in entries:
            try:
                # Vérifier si le code existe déjà
                existing = FormeJuridique.objects.filter(code=code).first()
                
                if existing:
                    # Vérifier si les données sont identiques
                    data_identical = (
                        existing.libelle == libelle and
                        existing.poids == poids and
                        existing.active == active and
                        existing.description == description
                    )
                    
                    if data_identical:
                        skipped_count += 1
                        self.stdout.write(self.style.WARNING(f'↺ Skipped (identical): {code} - {libelle}'))
                    else:
                        # Mettre à jour l'entrée existante
                        existing.libelle = libelle
                        existing.poids = poids
                        existing.active = active
                        existing.description = description
                        existing.save()
                        updated_count += 1
                        self.stdout.write(self.style.WARNING(
                            f'[UPD] Updated: {code} - {libelle} (poids: {poids})'
                        ))
                else:
                    # Créer une nouvelle entrée
                    FormeJuridique.objects.create(
                        code=code,
                        libelle=libelle,
                        poids=poids,
                        active=active,
                        description=description
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'[OK] Created: {code} - {libelle} (poids: {poids})'
                    ))
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f'✗ Error importing {code}: {str(e)}'
                ))
        
        return {
            'created': created_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'errors': error_count,
            'total': len(entries)
        }
    
    def simulate_import(self, entries, clear_data):
        """Simule l'importation sans enregistrer en base de données"""
        self.stdout.write("="*60)
        self.stdout.write("DRY RUN - SIMULATION ONLY")
        self.stdout.write("="*60)
        
        if clear_data:
            self.stdout.write("[WARNING] " + "Would clear all existing FormeJuridique data")
        
        self.stdout.write("\nEntries to import:")
        for code, libelle, poids, active, description in entries:
            status = "[OK] Actif" if active else "✗ Inactif"
            self.stdout.write(f"  {code:6} - {libelle:50} (poids: {poids:4}, {status})")
        
        # Vérifier les doublons potentiels
        codes = [code for code, _, _, _, _ in entries]
        duplicates = {code for code in codes if codes.count(code) > 1}
        
        if duplicates:
            self.stdout.write("[ERROR] " + f"\nWARNING: Duplicate codes found: {duplicates}")
        else:
            self.stdout.write("[SUCCESS] " + "\nNo duplicate codes found")
        
        # Vérifier les poids valides
        invalid_weights = [(code, poids) for code, _, poids, _, _ in entries if not isinstance(poids, (int, float))]
        if invalid_weights:
            self.stdout.write("[ERROR] " + f"\nWARNING: Invalid weights found: {invalid_weights}")
        
        self.stdout.write(f"\nTotal entries to process: {len(entries)}")
        self.stdout.write("="*60)
    
    def print_stats(self, stats):
        """Affiche les statistiques d'importation"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("IMPORT STATISTICS")
        self.stdout.write("="*50)
        self.stdout.write(f"Total entries in source: {stats['total']}")
        self.stdout.write(f"Entries created: {stats['created']}")
        self.stdout.write(f"Entries updated: {stats['updated']}")
        self.stdout.write(f"Entries skipped (identical): {stats['skipped']}")
        self.stdout.write(f"Entries with errors: {stats['errors']}")
        self.stdout.write("="*50)
        
        # Vérifier l'intégrité
        total_processed = stats['created'] + stats['updated'] + stats['skipped'] + stats['errors']
        if total_processed == stats['total']:
            self.stdout.write("[SUCCESS] " + "[OK] All entries processed")
        else:
            self.stdout.write("[ERROR] " + f"[WARN] Mismatch: processed {total_processed} out of {stats['total']}")


# Version avec bulk_create pour meilleure performance
class CommandBulk(BaseCommand):
    help = 'Import Forme juridique data (optimized bulk version)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before import',
        )
    
    def handle(self, *args, **options):
        clear_data = options['clear']
        
        formes_juridiques = [
            ("ADPU", "Administration publique", 0.2, True, None),
            ("ASS", "Association", 0.1, True, None),
            ("COOP", "Coopérative", 0.75, True, None),
            ("EI", "Entreprise Individuelle", 0.1, True, None),
            ("EIRL", "Entreprise individuelle à responsabilité limitée", 0.2, True, None),
            ("FEECC", "Fiducie exploitant une entreprise à caractère commercial", 0.25, True, None),
            ("GIE", "Groupement d'intérêt économique", 0.3, True, None),
            ("GRDP", "Groupement de personnes", 1.0, True, None),
            ("LTD", "Private Limited Company", 0.5, True, None),
            ("PART", "Partenariat", 0.2, True, None),
        ]
        
        try:
            with transaction.atomic():
                if clear_data:
                    deleted_count = FormeJuridique.objects.all().delete()[0]
                    self.stdout.write("[SUCCESS] " + f'Cleared {deleted_count} existing entries')
                
                # Préparer les objets pour bulk_create
                objets_a_creer = []
                for code, libelle, poids, active, description in formes_juridiques:
                    objets_a_creer.append(
                        FormeJuridique(
                            code=code,
                            libelle=libelle,
                            poids=poids,
                            active=active,
                            description=description
                        )
                    )
                
                # Utiliser bulk_create pour meilleure performance
                created_count = len(FormeJuridique.objects.bulk_create(objets_a_creer))
                
                self.stdout.write("[SUCCESS] " + 
                    f'Successfully imported {created_count} Forme juridique entries!'
                )
                
                # Afficher le résumé
                self.stdout.write("\nImported data:")
                for obj in objets_a_creer:
                    status = "[OK] Actif" if obj.active else "✗ Inactif"
                    self.stdout.write(f"  {obj.code:6} - {obj.libelle:50} (poids: {obj.poids:4}, {status})")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise