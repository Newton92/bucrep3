# your_app/management/commands/import_provinces_api.py
import requests
from django.core.management.base import BaseCommand
from ...models import Pays, Province

class Command(BaseCommand):
    """Version utilisant l'API RestCountries + Geonames"""
    
    def handle(self, *args, **options):
        for pays in Pays.objects.filter(is_active=True):
            self.import_via_restcountries(pays)
    
    def import_via_restcountries(self, pays):
        """
        Combine RestCountries pour les infos de base et Geonames pour les subdivisions
        """
        country_code = pays.code.lower()
        
        # 1. Obtenir les informations de base du pays
        rest_url = f"https://restcountries.com/v3.1/alpha/{country_code}"
        
        try:
            response = requests.get(rest_url, timeout=10)
            if response.status_code == 200:
                country_data = response.json()[0]
                
                # 2. Récupérer les subdivisions depuis Geonames
                subdivisions = self.get_subdivisions_from_geonames(
                    country_data.get('cca2', ''),
                    country_data.get('name', {}).get('common', '')
                )
                
                # 3. Importer les provinces
                if subdivisions:
                    self.import_subdivisions(pays, subdivisions)
                    
        except Exception as e:
            self.stdout.write(f"Erreur pour {pays.nom}: {str(e)}")
    
    def get_subdivisions_from_geonames(self, country_code, country_name):
        """
        Récupère les subdivisions administratives depuis Geonames
        Nécessite un compte gratuit sur geonames.org
        """
        # Configuration (à mettre dans les settings)
        GEONAMES_USERNAME = 'votre_username'  # Inscrivez-vous sur geonames.org
        
        if not GEONAMES_USERNAME:
            return None
        
        url = "http://api.geonames.org/childrenJSON"
        params = {
            'geonameId': self.get_geoname_id(country_code),
            'username': GEONAMES_USERNAME
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('geonames', [])
        except:
            pass
        
        return None
    
    def get_geoname_id(self, country_code):
        """Mapping des ID Geonames par pays (exemples)"""
        geoname_ids = {
            'cm': 2233387,  # Cameroun
            'ci': 2287781,  # Côte d'Ivoire
            'sn': 2245662,  # Sénégal
            'cd': 203312,   # RDC
            'ma': 2542007,  # Maroc
            'dz': 2589581,  # Algérie
            'za': 953987,   # Afrique du Sud
            'ng': 2328926,  # Nigeria
            # Ajoutez d'autres ID selon vos besoins
        }
        return geoname_ids.get(country_code.lower(), None)