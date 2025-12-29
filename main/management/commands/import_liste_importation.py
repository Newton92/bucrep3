# management/commands/import_liste_importation.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from main.models import ListeImportation


class Command(BaseCommand):
    help = 'Import Incoterms data into ListeImportation model (SafeDelete compatible)'
    
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
            '--hard-delete',
            action='store_true',
            help='Perform hard delete instead of soft delete',
        )

    def handle(self, *args, **options):
        clear_data = options['clear']
        dry_run = options.get('dry_run', False)
        hard_delete = options.get('hard_delete', False)
        
        # Données à importer (Incoterms)
        LISTE_IMPORTATION_HISTORIQUE = (
            (_("1- EXW – Ex-Works – À l'usine \n Le vendeur (expéditeur) met à disposition les marchandises transportées dans un endroit convenu (obligation minimale pour le vendeur). L'acheteur supporte tous les coûts de transport et de formalités."),),
            (_("2- FCA – Free-CArrier – Franco-transporteur\n  Le vendeur livre la marchandise au destinataire désigné et payé par l'acheteur. Le transfert des risques est matérialisé lors de cette opération. Si la livraison est effectuée dans les locaux du vendeur, il est responsable du chargement de la marchandise. Si la livraison a lieu dans un autre endroit, le vendeur n'est plus responsable du déchargement."),),
            (_("3- CPT – Carriage Paid To – Port payé jusqu'à \n La marchandise est livrée au premier transporteur à l'étranger, frais payés par le vendeur, sans assurance pour le transport. L'acheteur assume les risques et tous les autres frais encourus par la marchandise dès la remise de la marchandise au premier transporteur. L'acheteur prend en charge toutes les opérations qui ont lieu à l'arrivée."),),
            (_("4- CIP – Carriage Insurance Paid to – Port payé, assurance comprise jusqu'à DAP \n Règle Incoterms identique au CPT avec comme seule différence l'assurance : le vendeur prend en charge l'assurance du transport."),),
            (_("5- DAP – Delivered At Place – Rendu au lieu de destination \n Le vendeur prend en charge le transport des marchandises jusqu'au point de livraison convenu. Il assume les coûts et les risques jusqu'à ce point. L'acheteur supporte le déchargement et le dédouanement import."),),
            (_("6- DPU – Delivered at place unloaded, rendu au lieu de destination (ancien DAT) \n Le vendeur organise le transport et paie le déchargement au lieu de destination. Une fois au terminal l'acheteur est responsable de la marchandise et doit effectuer les formalités d'importation et s'acquitte des droits et taxes liés."),),
            (_("7- DDP – Delivered Duty Paid – Rendu droits acquittés \n Le vendeur livre la marchandise à l'acheteur en ayant tout pris en charge, y compris les formalités douanières import et le paiement des droits et taxes (Obligation maximal pour le vendeur)."),),
            (_("8- FAS (Free alongside ship) \n Le vendeur règle les frais de transport jusqu'au port d'embarquement et effectue les formalités d'exportation. La marchandise est livrée le long du navire dans le port désigné par l'acheteur. Cette livraison marque le transfert des risques, des frais et des formalités à l'acheteur. L'Incoterm FAS impose au vendeur l'obligation de dédouaner le fret à l'exportation."),),
            (_("9- FOB (Free on board) \n Le vendeur livre la marchandise sur le navire au port d'embarquement convenu. Le transfert des charges et des risques se fait lorsque la marchandise est à bord du navire. Le vendeur doit dédouaner la marchandise."),),
            (_("10- CFR (Cost and freight) \n Le vendeur se charge du transport principal jusqu'au port de destination. Il se charge des formalités d'export et doit s'acquitter des droits et taxes liés. Le transfert de frais à lieu à l'arrivée des marchandises au port d'arrivée, mais le vendeur n'est plus responsable de la marchandise dès que celle-ci a été chargée sur le port de départ."),),
            (_("11- CIF (Cost, insurance and freight) \n Le vendeur livre la marchandise sur le navire au port d'embarquement convenu. Le vendeur se charge des formalités d'export et règles les droits et taxes liés. Le transfert des frais se fait au port de destination mais le transfert des risques a lieu au port de départ. L'acheteur prend en charge les frais à l'arrivée des marchandises au port de destination, et les formalités à l'import."),),
        )
        
        # Simplifier les données
        incoterms_data = [libelle[0] for libelle in LISTE_IMPORTATION_HISTORIQUE]
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No data will be saved"))
            self.simulate_import(incoterms_data, clear_data, hard_delete)
            return
        
        try:
            # NE PAS utiliser transaction.atomic() avec SafeDeleteModel
            # car les erreurs dans la transaction bloquent les requêtes suivantes
            
            # Étape 1: Vider les données existantes si demandé
            if clear_data:
                self.clear_existing_data(hard_delete)
            
            # Étape 2: Importer les nouvelles données
            stats = self.import_data(incoterms_data)
            
            self.stdout.write(self.style.SUCCESS('Successfully imported Incoterms data!'))
            self.print_stats(stats)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            traceback.print_exc()
    
    def clear_existing_data(self, hard_delete=False):
        """Vide toutes les données existantes du modèle ListeImportation"""
        self.stdout.write(self.style.WARNING('Clearing existing Incoterms data...'))
        
        # Compter avant suppression
        count = ListeImportation.objects.all().count()
        
        if hard_delete:
            # Suppression physique
            deleted_count = ListeImportation.objects.all().hard_delete()
            self.stdout.write(self.style.SUCCESS(f'Hard deleted {deleted_count} Incoterms entries.'))
        else:
            # Suppression logique (soft delete)
            deleted_count = ListeImportation.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Soft deleted {deleted_count[0]} Incoterms entries.'))
    
    def import_data(self, entries):
        """Importe les données dans le modèle ListeImportation"""
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        self.stdout.write("Starting Incoterms data import...")
        
        # Traiter chaque entrée SANS transaction globale
        for index, libelle in enumerate(entries, 1):
            try:
                # Nettoyer le libellé
                clean_libelle = self.clean_libelle(libelle)
                
                # Vérifier si un libellé similaire existe déjà (même supprimé)
                existing = self.find_existing_entry(clean_libelle)
                
                if existing:
                    # Si l'entrée existe et est supprimée, la restaurer
                    if hasattr(existing, 'deleted') and existing.deleted:
                        existing.deleted = None
                        existing.deleted_by_cascade = None
                        existing.save()
                        updated_count += 1
                        self.stdout.write(self.style.WARNING(
                            f'[RESTORED] ({index}/11): {clean_libelle[:50]}...'
                        ))
                    else:
                        # Vérifier si les données sont identiques
                        if existing.libelle == clean_libelle:
                            skipped_count += 1
                            self.stdout.write(self.style.WARNING(
                                f'↺ Skipped identical ({index}/11): {clean_libelle[:50]}...'
                            ))
                        else:
                            # Mettre à jour l'entrée existante
                            existing.libelle = clean_libelle
                            existing.save()
                            updated_count += 1
                            self.stdout.write(self.style.WARNING(
                                f'[UPD] Updated ({index}/11): {clean_libelle[:50]}...'
                            ))
                else:
                    # Créer une nouvelle entrée avec les champs SafeDelete
                    try:
                        # Méthode 1: Créer avec tous les champs requis
                        ListeImportation.objects.create(
                            libelle=clean_libelle,
                            deleted=None,  # Explicitement défini comme NULL
                            deleted_by_cascade=None  # Explicitement défini comme NULL
                        )
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'[OK] Created ({index}/11): {clean_libelle[:50]}...'
                        ))
                    except Exception as e:
                        # Méthode 2: Utiliser bulk_create qui gère mieux les champs
                        # Créer l'objet manuellement
                        obj = ListeImportation(libelle=clean_libelle)
                        
                        # Définir explicitement les champs SafeDelete
                        if hasattr(obj, 'deleted'):
                            obj.deleted = None
                        if hasattr(obj, 'deleted_by_cascade'):
                            obj.deleted_by_cascade = None
                        
                        obj.save()
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'[OK] Created via save() ({index}/11): {clean_libelle[:50]}...'
                        ))
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f'✗ Error importing entry {index}: {str(e)[:100]}...'
                ))
                # Continuer avec l'entrée suivante
        
        return {
            'created': created_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'errors': error_count,
            'total': len(entries)
        }
    
    def clean_libelle(self, libelle):
        """Nettoie et formate le libellé"""
        # S'assurer que c'est une chaîne de caractères
        if hasattr(libelle, '_proxy____args'):
            # C'est un objet gettext_lazy, le convertir en string
            libelle = str(libelle)
        
        # Nettoyer les espaces multiples
        import re
        libelle = re.sub(r'\s+', ' ', libelle.strip())
        
        # Capitaliser la première lettre
        if libelle:
            libelle = libelle[0].upper() + libelle[1:]
        
        return libelle
    
    def find_existing_entry(self, libelle):
        """Recherche une entrée existante avec un libellé similaire"""
        # Recherche exacte (y compris les entrées supprimées)
        try:
            # Inclure les entrées supprimées dans la recherche
            from safedelete.managers import SafeDeleteManager
            manager = SafeDeleteManager()
            manager.model = ListeImportation
            
            # Chercher toutes les entrées (même supprimées)
            existing = ListeImportation.objects.all_with_deleted().filter(libelle=libelle).first()
            if existing:
                return existing
            
            # Recherche par début de libellé
            if len(libelle) > 50:
                search_term = libelle[:50]
                existing = ListeImportation.objects.all_with_deleted().filter(
                    libelle__startswith=search_term
                ).first()
                if existing:
                    return existing
            
            # Recherche par mots clés (Incoterms)
            incoterms_keywords = ['EXW', 'FCA', 'CPT', 'CIP', 'DAP', 'DPU', 'DDP', 'FAS', 'FOB', 'CFR', 'CIF']
            for keyword in incoterms_keywords:
                if keyword in libelle:
                    existing = ListeImportation.objects.all_with_deleted().filter(
                        libelle__contains=keyword
                    ).first()
                    if existing:
                        return existing
        
        except Exception as e:
            # Fallback: recherche simple
            existing = ListeImportation.objects.filter(libelle=libelle).first()
            if existing:
                return existing
        
        return None
    
    def simulate_import(self, entries, clear_data, hard_delete):
        """Simule l'importation sans enregistrer en base de données"""
        self.stdout.write("="*60)
        self.stdout.write("DRY RUN - SIMULATION ONLY")
        self.stdout.write("="*60)
        
        if clear_data:
            delete_type = "HARD DELETE" if hard_delete else "SOFT DELETE"
            self.stdout.write(f"[WARNING] Would perform {delete_type} on existing data")
        
        self.stdout.write(f"\n{len(entries)} Incoterms to import:\n")
        
        for i, libelle in enumerate(entries, 1):
            clean_libelle = self.clean_libelle(libelle)
            
            # Extraire le code Incoterm
            incoterm_code = "N/A"
            codes = ['EXW', 'FCA', 'CPT', 'CIP', 'DAP', 'DPU', 'DDP', 'FAS', 'FOB', 'CFR', 'CIF']
            for code in codes:
                if code in clean_libelle:
                    incoterm_code = code
                    break
            
            # Afficher avec formatage
            lines = clean_libelle.split('\n')
            first_line = lines[0] if lines else ""
            self.stdout.write(f"{i:2}. [{incoterm_code:3}] {first_line[:70]}...")
            
            # Vérifier la longueur
            if len(clean_libelle) > 2000:
                self.stdout.write(f"   ⚠  WARNING: Libellé trop long ({len(clean_libelle)} > 2000 caractères)")
        
        self.stdout.write("="*60)
    
    def print_stats(self, stats):
        """Affiche les statistiques d'importation"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("IMPORT STATISTICS")
        self.stdout.write("="*50)
        self.stdout.write(f"Total entries in source: {stats['total']}")
        self.stdout.write(f"Entries created: {stats['created']}")
        self.stdout.write(f"Entries updated: {stats['updated']}")
        self.stdout.write(f"Entries skipped: {stats['skipped']}")
        self.stdout.write(f"Entries with errors: {stats['errors']}")
        self.stdout.write("="*50)
        
        # Vérifier l'intégrité
        total_processed = stats['created'] + stats['updated'] + stats['skipped'] + stats['errors']
        if total_processed == stats['total']:
            self.stdout.write(self.style.SUCCESS("[OK] All entries processed"))
        else:
            self.stdout.write(self.style.WARNING(
                f"[WARN] Mismatch: processed {total_processed} out of {stats['total']}"
            ))
        
        # Afficher un résumé final
        self.stdout.write("\n" + "-"*50)
        self.stdout.write("DATABASE STATUS")
        self.stdout.write("-"*50)
        
        try:
            total_count = ListeImportation.objects.count()
            deleted_count = ListeImportation.objects.deleted_only().count()
            active_count = total_count - deleted_count
            
            self.stdout.write(f"Total entries in database: {total_count}")
            self.stdout.write(f"Active entries: {active_count}")
            self.stdout.write(f"Soft-deleted entries: {deleted_count}")
            
            if active_count > 0:
                self.stdout.write("\nActive Incoterms:")
                for incoterm in ListeImportation.objects.all()[:5]:
                    libelle = str(incoterm.libelle)
                    code = "???"
                    for inc_code in ['EXW', 'FCA', 'CPT', 'CIP', 'DAP', 'DPU', 'DDP', 'FAS', 'FOB', 'CFR', 'CIF']:
                        if inc_code in libelle:
                            code = inc_code
                            break
                    
                    first_line = libelle.split('\n')[0] if '\n' in libelle else libelle[:60]
                    self.stdout.write(f"  [{code}] {first_line}...")
                
                if active_count > 5:
                    self.stdout.write(f"  ... and {active_count - 5} more")
        
        except Exception as e:
            self.stdout.write(f"Could not query database: {str(e)}")


        
        
        
# Version basique
# python manage.py import_liste_importation

# Vider les données existantes avant import
# python manage.py import_liste_importation --clear

# Simulation (pas de sauvegarde en base)
# python manage.py import_liste_importation --dry-run

# Ignorer les doublons
# python manage.py import_liste_importation --skip-duplicates

# Combiner les options
# python manage.py import_liste_importation --clear --dry-run