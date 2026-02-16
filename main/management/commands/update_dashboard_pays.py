# main/management/commands/update_dashboard_pays.py
from django.core.management.base import BaseCommand
from main.models import Pays

class Command(BaseCommand):
    help = 'Met à jour l\'affichage au dashboard pour les pays spécifiés'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule l\'opération sans modifier la base de données'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche plus de détails sur les modifications'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        # Liste des pays à activer
        pays_a_activer = [
            "Afrique du sud", "South Africa", "Benin", "Burkina Faso", "Cameroun", 
            "Centrafrique", "Central African Republic", "Congo", "Côte d'Ivoire", "Gabon", 
            "Ghana", "Guinee bissau", "Guinee-bissau", "Guinee equatoriale", "Mali", 
            "Maroc", "Morocco", "Mauritanie", "Mauritania", "Niger", "Nigeria", 
            "Republique democratique du Congo", "Democratic Republic of the Congo", "Senegal", "Tchad", "Chad", "Togo"
        ]
        
        # Nettoyer les noms pour la recherche (gérer les espaces, accents, etc.)
        from django.db.models import Q
        import unicodedata
        
        def normalize_text(text):
            """Normalise le texte pour la recherche (enlève accents, met en minuscule)"""
            text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
            return text.lower().strip()
        
        # Construire la requête pour trouver les pays
        query = Q()
        for pays in pays_a_activer:
            query |= Q(nom__icontains=pays)
        
        pays_a_modifier = Pays.objects.filter(query)
        
        # Statistiques
        total_pays = Pays.objects.count()
        pays_trouves = pays_a_modifier.count()
        pays_non_trouves = set(pays_a_activer) - set(pays_a_modifier.values_list('nom', flat=True))
        
        self.stdout.write(self.style.WARNING(f"Total des pays en base: {total_pays}"))
        self.stdout.write(self.style.WARNING(f"Pays trouvés pour activation: {pays_trouves}"))
        
        if pays_non_trouves:
            self.stdout.write(
                self.style.ERROR(f"Pays non trouvés: {', '.join(pays_non_trouves)}")
            )
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] Aucune modification en base"))
            if verbose:
                for pays in pays_a_modifier:
                    self.stdout.write(f"  - {pays.nom} ({pays.code}) -> True")
        else:
            # Mettre à jour les pays trouvés
            count_updated = pays_a_modifier.update(afficher_au_dashboard=True)
            
            # Mettre à jour tous les autres pays à False
            autres_pays = Pays.objects.exclude(id__in=pays_a_modifier)
            autres_pays.update(afficher_au_dashboard=False)
            
            self.stdout.write(
                self.style.SUCCESS(f"\n✓ {count_updated} pays activés pour le dashboard")
            )
            self.stdout.write(
                self.style.SUCCESS(f"✓ {autres_pays.count()} pays désactivés")
            )
            
            if verbose:
                self.stdout.write("\nPays activés:")
                for pays in pays_a_modifier:
                    self.stdout.write(f"  ✓ {pays.nom} ({pays.code})")
                    
                    
                    
                    
# Simulation
# python manage.py update_dashboard_pays --dry-run

# Simulation avec détails
# python manage.py update_dashboard_pays --dry-run --verbose

# Exécution réelle
# python manage.py update_dashboard_pays

# Exécution avec détails
# python manage.py update_dashboard_pays --verbose