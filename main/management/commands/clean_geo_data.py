# management/commands/clean_geo_data.py
from django.core.management.base import BaseCommand
from main.models import Pays, Province, Ville

class Command(BaseCommand):
    help = "Nettoyer les données géographiques"
    
    def handle(self, *args, **options):
        # Delete duplicates
        for pays in Pays.objects.all():
            provinces = Province.objects.filter(pays=pays)
            for province in provinces:
                # Keep only one instance of each city
                villes = Ville.objects.filter(province=province, pays=pays)
                seen = set()
                for ville in villes:
                    key = (ville.nom, ville.province_id, ville.pays_id)
                    if key in seen:
                        ville.delete()
                    else:
                        seen.add(key)
        
        self.stdout.write(self.style.SUCCESS("✅ Nettoyage terminé"))