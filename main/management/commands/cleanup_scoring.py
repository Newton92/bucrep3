# management/commands/cleanup_scoring.py

from django.core.management.base import BaseCommand
from django.db import connection
from main.models import Scoring

class Command(BaseCommand):
    help = 'Nettoyer les scorings corrompus'
    
    def handle(self, *args, **options):
        self.stdout.write("🧹 Nettoyage des scorings...")
        
        # 1. Hard delete tous les scorings soft-deleted
        from safedelete.models import HARD_DELETE
        
        deleted_scorings = Scoring.objects.filter(deleted__isnull=False)
        count = deleted_scorings.count()
        
        if count > 0:
            self.stdout.write(f"Suppression de {count} scorings soft-deleted...")
            deleted_scorings.delete(force_policy=HARD_DELETE)
        
        # 2. Supprimer les doublons
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM main_scoring 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM main_scoring 
                    GROUP BY annee_id, acheteur_id
                )
            """)
            duplicates = cursor.rowcount
            if duplicates > 0:
                self.stdout.write(f"Suppression de {duplicates} doublons")
        
        self.stdout.write(self.style.SUCCESS("✅ Nettoyage terminé !"))