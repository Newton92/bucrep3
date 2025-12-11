# management/commands/import_modele_notation_simple.py
from django.core.management.base import BaseCommand
from main.models import ModeleNotation


class Command(BaseCommand):
    help = 'Simple import for Modèle de notation (always recreates)'
    
    def handle(self, *args, **options):
        notation_data = [
            ("40", "Cette société est une filiale d'un groupe"),
            ("35", "Cette société est une société autonome"),
            ("30", "En raison de ses liens avec le groupe, elle est considérée comme une filiale indépendante"),
            ("25", "Cette entreprise est considérée comme une grande entreprise"),
            ("20", "Cette entreprise est considérée comme une entreprise de taille moyenne"),
            ("15", "Cette entreprise est considérée comme une petite entreprise"),
            ("10", "Inconnu de nos sources"),
        ]
        
        # Toujours supprimer avant de créer
        ModeleNotation.objects.all().delete()
        
        # Créer toutes les entrées
        for code, libelle in notation_data:
            ModeleNotation.objects.create(code=code, libelle=libelle)
            self.stdout.write(f'Created: {code} - {libelle}')
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully imported {len(notation_data)} Modèle de notation entries!'
        ))