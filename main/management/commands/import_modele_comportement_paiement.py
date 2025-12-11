# management/commands/import_modele_comportement_paiement.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext_lazy as _
# Importez le modèle ModeleComportementPaiement
from main.models import ModeleComportementPaiement 


class Command(BaseCommand):
    """
    Commande d'importation personnalisée pour le modèle ModeleComportementPaiement.
    Les codes sont générés au format MCP-YYYY-XX.
    """
    help = 'Import ModeleComportementPaiement data with sequential codes (MCP-YYYY-XX)'

    # Données à importer (uniquement le comportement de paiement, basé sur la grille)
    # Format: (libelle, poids)
    # Les codes séquentiels seront générés automatiquement.
    BASE_PAYMENT_DATA = [
        # Note: L'entrée "DEFAUT" manquante est ajoutée pour être complète
        (_("Défaut"), 0.0), 
        (_("En Avance"), 1.0),
        (_("En Temps et en heure"), 0.5),
        (_("En Retard"), -0.15),
        (_("Normal"), 0.5),
        (_("Mauvais payeur"), -1.0),
        (_("Plainte isolée"), -0.25),
        (_("Inconnu de nos sources"), 0.0),
        (
            _("En raison des informations sur les procédures d'insolvabilité/préliminaires/réglementaires, ACREMAC n'est pas en mesure de donner une évaluation finale du comportement de paiement de l'entreprise à ce stade"),
            0.0
        ),
        (
            _("Aucune expérience de paiement d'une quelconque importance n'est disponible"),
            0.0
        ),
        # Les entrées suivantes ne sont pas dans la grille, le poids reste à 0.0 (par défaut/neutre)
        ( 
            _("En raison des informations sur les procédures d'insolvabilité/préliminaires/réglementaires, ACREMAC n'est pas en mesure de donner une évaluation finale du comportement de paiement de l'entreprise à ce stade"),
            0.0
        ),
        (
            _("Aucune expérience de paiement d'une quelconque importance n'est disponible"),
            0.0
        ),
        (
         _("Aucune information négative n'a été trouvée"), 
         0.0
        ),
        
        (
         _("Il n'existe aucune trace d'une quelconque action de recouvrement de créances par ACREMAC à l'encontre de cette entreprise"), 
         0.0
        ),
        
        (
         _("Selon nos sources, l'entreprise n'est pas en situation d'insolvabilité/procédure préliminaire/procédure de répartition des dettes"), 
         0.0
        ),
        
        (
            _("Des actions en recouvrement judiciaire sont ouvertes contre l'acheteur"), 
         -0.5 # Hypotèse d'un impact négatif
        ),
        
        (
         _("Des actions de recouvrement à l'amiable sont ouvertes contre l'acheteur"), 
         -0.2 # Hypotèse d'un impact légèrement négatif
        ),
        
        (
         _("Des cas de recouvrement fermés existent chez nos sources sur l'acheteur"), 
         -0.1 # Hypotèse d'un impact très légèrement négatif (l'action est terminée)
        ),
        
        (_("Inconnu de nos sources"), 0.0),
        
        # J'ai ajouté les deux lignes que vous aviez mises en commentaire 
        # (car elles peuvent être nécessaires si elles n'existent pas déjà dans le modèle)
        (
            _("En raison des informations sur les procédures d'insolvabilité/préliminaires/réglementaires, ACREMAC n'est pas en mesure de donner une évaluation finale du comportement de paiement de l'entreprise à ce stade"),
            -0.8 # Fort impact négatif/incertitude
        ),
        (
            _("Aucune expérience de paiement d'une quelconque importance n'est disponible"),
            0.0
        ),
    ]

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

    def generate_sequential_codes(self):
        """
        Génère la liste finale d'entrées avec des codes séquentiels.
        Ex: MCP-2025-01, MCP-2025-02, ...
        """
        data_with_codes = []
        year = 2025 # Définir l'année souhaitée
        
        for index, (libelle, poids) in enumerate(self.BASE_PAYMENT_DATA, 1):
            code = f"MCP-{year}-{index:02d}"
            data_with_codes.append((code, libelle, poids))
        
        return data_with_codes


    def handle(self, *args, **options):
        clear_data = options['clear']
        dry_run = options.get('dry_run', False)
        
        # Générer les données avec les codes séquentiels
        notation_data = self.generate_sequential_codes()
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No data will be saved"))
            self.simulate_import(notation_data, clear_data)
            return
        
        try:
            with transaction.atomic():
                # Étape 1: Vider les données existantes si demandé
                if clear_data:
                    self.clear_existing_data()
                
                # Étape 2: Importer les nouvelles données
                stats = self.import_data(notation_data)
                
                self.stdout.write(self.style.SUCCESS(
                    'Successfully imported Modèle de comportement de paiement data!'
                ))
                self.print_stats(stats)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during import: {str(e)}'))
            # Remontée de l'exception dans le cas réel pour annuler la transaction
            raise

    # --- Méthodes utilitaires (légèrement modifiées pour la cohérence) ---

    def clear_existing_data(self):
        """Vide toutes les données existantes du modèle ModeleComportementPaiement"""
        self.stdout.write(
            self.style.WARNING('Clearing existing ModeleComportementPaiement data...')
        )
        count = ModeleComportementPaiement.objects.count()
        ModeleComportementPaiement.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f'Cleared {count} ModeleComportementPaiement entries.')
        )
    
    def import_data(self, entries):
        """Importe les données dans le modèle ModeleComportementPaiement"""
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        self.stdout.write("Starting ModeleComportementPaiement data import...")
        
        for code, libelle, poids in entries:
            libelle_str = str(libelle)
            
            # Utilisation du code généré pour la recherche d'existence
            existing = ModeleComportementPaiement.objects.filter(code=code).first()
            
            if existing:
                # Vérifier si les données sont identiques (libellé OU poids)
                if existing.libelle == libelle_str and existing.poids == poids:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'↺ Skipped (identical): {code} - {libelle_str}')
                    )
                    continue
                else:
                    # Mettre à jour l'entrée existante
                    existing.libelle = libelle_str
                    existing.poids = poids
                    existing.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Updated: {code} - {libelle_str} (Poids: {poids})')
                    )
            else:
                # Créer une nouvelle entrée
                ModeleComportementPaiement.objects.create(
                    code=code,
                    libelle=libelle_str,
                    poids=poids
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {code} - {libelle_str} (Poids: {poids})')
                )
        
        return {
            'created': created_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'total': len(entries)
        }
    
    def simulate_import(self, entries, clear_data):
        """Simule l'importation sans enregistrer en base de données"""
        self.stdout.write("="*60)
        self.stdout.write("DRY RUN - SIMULATION ONLY")
        self.stdout.write("="*60)
        
        if clear_data:
            self.stdout.write(
                self.style.WARNING("Would clear all existing ModeleComportementPaiement data")
            )
        
        self.stdout.write("\nEntries to import:")
        for code, libelle, poids in entries:
            self.stdout.write(f"  {code}: {libelle} (Poids: {poids})")
        
        self.stdout.write(self.style.SUCCESS("\nNo duplicate codes found (generated sequentially)"))
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
        self.stdout.write("="*50)
        
        total_processed = stats['created'] + stats['updated'] + stats['skipped']
        if total_processed == stats['total']:
            self.stdout.write(self.style.SUCCESS("✓ All entries processed successfully"))
        else:
            self.stdout.write(
                self.style.ERROR(f"⚠ Mismatch: processed {total_processed} out of {stats['total']}")
            )





     
            
            
            
            
            
            
# Pour importer, créer ou mettre à jour (recommandé)
# python manage.py import_modele_comportement_paiement

# Pour vider toutes les données puis importer
# python manage.py import_modele_comportement_paiement --clear

# Pour simuler l'importation sans toucher à la base de données
# python manage.py import_modele_comportement_paiement --dry-run