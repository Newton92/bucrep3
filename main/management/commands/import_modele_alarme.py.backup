# main/management/commands/import_modele_alarme_safe.py
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import ModeleAlarme
from datetime import datetime

class Command(BaseCommand):
    help = "Importe les modèles d'alarme avec vérification des longueurs"
    
    def handle(self, *args, **options):
        self.stdout.write("[SUCCESS] " + "Importation sécurisée des modèles d'alarme...")
        
        # Données originales
        donnees_originales = [
            ("Risque d'insolvabilité", "Risque d'insolvabilité"),
            ("Une procédure préliminaire a été demandée", "Demande de composition juridique"),
            ("Une procédure prématurée a été suspendue", "Une procédure prématurée a été suspendue"),
            ("La composition du tribunal à la suite d'un examen préliminaire", 
             "La composition du tribunal à la suite d'un examen préliminaire"),
            ("Ouverture de la composition judiciaire", "Ouverture de la composition judiciaire"),
            ("Refus de l'homologation, la corruption est attendue", 
             "Refus de l'homologation, la corruption est attendue"),
        ]
        
        year = datetime.now().year
        prefix = 'MDA'
        
        created_count = 0
        
        with transaction.atomic():
            for index, (libelle, description) in enumerate(donnees_originales, start=1):
                # Vérification de la longueur
                if len(libelle) > 255:
                    self.stdout.write(self.style.WARNING(
                        f"[WARN] Libellé trop long ({len(libelle)} caractères): {libelle[:50]}..."
                    ))
                    # Tronquer si nécessaire
                    libelle = libelle[:255]
                
                code_complet = f"{prefix}-{year}-{index:02d}"
                
                modele, created = ModeleAlarme.objects.update_or_create(
                    code=code_complet,
                    defaults={'libelle': libelle}
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"[OK] {code_complet}: {libelle}")
                else:
                    self.stdout.write(f"[UPD] {code_complet} (mis à jour)")
        
        self.stdout.write("[SUCCESS] " + f"\nImportation terminée: {created_count} modèles créés")