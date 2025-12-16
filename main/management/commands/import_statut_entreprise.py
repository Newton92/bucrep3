# main/management/commands/import_statut_entreprise.py - VERSION CORRIGÉE
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import StatutEntreprise
from datetime import datetime

class Command(BaseCommand):
    help = "Importe ou met à jour les statuts d'entreprise"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help="Supprime tous les statuts existants avant l'importation"
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
            default='STE',
            help="Préfixe pour les codes (défaut: STE pour STatut d'Entreprise)"
        )
        parser.add_argument(
            '--inactive-only',
            action='store_true',
            help="Marque tous les statuts comme inactifs sauf 'Entreprise active'"
        )

    def handle(self, *args, **options):
        # Utiliser des caractères ASCII pour éviter les problèmes d'encodage
        self.stdout.write("Début de l'importation des statuts d'entreprise...")
        
        # Données à importer
        statuts_data = [
            {'libelle': 'Entreprise active', 'categorie': 'actif'},
            {'libelle': 'Entreprise inactive', 'categorie': 'inactif'},
            {'libelle': 'Entreprise en fusion', 'categorie': 'transition'},
            {'libelle': 'Entreprise fusionnée', 'categorie': 'inactif'},
            {'libelle': "L'entreprise n'existe pas", 'categorie': 'inexistant'},
            {'libelle': "L'entreprise n'a pas pu être identifiée", 'categorie': 'indetermine'},
            {'libelle': 'Entreprise est en sommeil', 'categorie': 'inactif'},
            {'libelle': "Impossible de localiser l'entreprise", 'categorie': 'indetermine'},
            {'libelle': "L'activité a cessé", 'categorie': 'inactif'},
            {'libelle': "L'entreprise n'est pas immatriculée", 'categorie': 'irregulier'},
            {'libelle': "L'entreprise n'est pas immatriculée localement", 'categorie': 'irregulier'},
            {'libelle': 'Activité commerciale limitée', 'categorie': 'actif'},
            {'libelle': 'Aucune activité commerciale visible localement', 'categorie': 'inactif'},
            {'libelle': 'Dissolution volontaire', 'categorie': 'dissous'},
            {'libelle': 'Dissolution volontaire du créancier', 'categorie': 'dissous'},
            {'libelle': 'Dissolution forcée', 'categorie': 'dissous'},
            {'libelle': 'Radiation', 'categorie': 'dissous'},
            {'libelle': 'Entreprise en cours de désimmatriculation', 'categorie': 'transition'},
            {'libelle': 'Dissoute', 'categorie': 'dissous'},
            {'libelle': 'Va suivre', 'categorie': 'indetermine'},
            {'libelle': 'Entreprise Introuvable', 'categorie': 'indetermine'},
        ]
        
        year = options['year']
        prefix = options['prefix']
        
        if options['clear'] and not options['dry_run']:
            deleted_count, _ = StatutEntreprise.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"Supprimé {deleted_count} statut(s) d'entreprise existant(s)"
            ))
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        if not options['dry_run']:
            with transaction.atomic():
                for index, data in enumerate(statuts_data, start=1):
                    # Format: STE-YYYY-NN (avec NN sur 2 chiffres)
                    code_complet = f"{prefix}-{year}-{index:02d}"
                    libelle_complet = data['libelle']
                    categorie = data['categorie']
                    
                    # Déterminer si le statut est actif
                    if options['inactive_only']:
                        is_active = (libelle_complet == 'Entreprise active')
                    else:
                        is_active = (categorie == 'actif')
                    
                    # Description basée sur la catégorie
                    description_map = {
                        'actif': "Entreprise en activité normale",
                        'inactif': "Entreprise non active actuellement",
                        'transition': "Entreprise en transition ou processus administratif",
                        'inexistant': "L'entreprise n'existe plus ou n'a jamais existé",
                        'indetermine': "Statut indéterminé ou information manquante",
                        'irregulier': "Situation administrative irrégulière",
                        'dissous': "Entreprise dissoute ou radiée"
                    }
                    description = description_map.get(categorie, "Statut d'entreprise")
                    
                    statut, created = StatutEntreprise.objects.update_or_create(
                        code=code_complet,
                        defaults={
                            'libelle': libelle_complet,
                            'description': description,
                            'active': is_active
                        }
                    )
                    
                    if created:
                        created_count += 1
                        # CARACTÈRES ASCII SEULEMENT
                        self.stdout.write(f"[OK] Créé : {code_complet}")
                        self.stdout.write(f"     Statut : {libelle_complet}")
                        self.stdout.write(f"     Catégorie : {categorie} | Actif : {'Oui' if is_active else 'Non'}")
                    else:
                        updated_count += 1
                        self.stdout.write(f"[UPD] Mis à jour : {code_complet}")
        else:
            # Mode simulation
            self.stdout.write("Mode simulation - Aucune donnée ne sera modifiée")
            for index, data in enumerate(statuts_data, start=1):
                code_complet = f"{prefix}-{year}-{index:02d}"
                exists = StatutEntreprise.objects.filter(code=code_complet).exists()
                
                if exists:
                    self.stdout.write(f"[EXIST] Existe déjà : {code_complet}")
                    self.stdout.write(f"        Statut : {data['libelle']}")
                    skipped_count += 1
                else:
                    self.stdout.write(f"[NEW] À créer : {code_complet}")
                    self.stdout.write(f"      Statut : {data['libelle']}")
                    self.stdout.write(f"      Catégorie : {data['categorie']}")
                    created_count += 1
        
        # Résumé
        self.stdout.write("\n" + "="*50)
        if options['dry_run']:
            self.stdout.write("SIMULATION - Aucune donnée modifiée")
        
        self.stdout.write("Résumé de l'importation :")
        
        # Statistiques par catégorie
        categories_stats = {}
        for data in statuts_data:
            cat = data['categorie']
            categories_stats[cat] = categories_stats.get(cat, 0) + 1
        
        self.stdout.write("\nStatistiques par catégorie:")
        for categorie, count in sorted(categories_stats.items()):
            self.stdout.write(f"  - {categorie}: {count} statut(s)")
        
        self.stdout.write(f"\n- Codes générés : {prefix}-{year}-01 à {prefix}-{year}-{len(statuts_data):02d}")
        self.stdout.write(f"- Statuts créés : {created_count}")
        self.stdout.write(f"- Statuts mis à jour : {updated_count}")
        if options['dry_run']:
            self.stdout.write(f"- Statuts existants : {skipped_count}")
        
        if options['inactive_only']:
            self.stdout.write("\nNOTE: Mode 'inactive-only' activé: seul 'Entreprise active' est marqué comme actif")
        else:
            active_count = sum(1 for data in statuts_data if data['categorie'] == 'actif')
            self.stdout.write(f"- Statuts marqués comme actifs : {active_count}")