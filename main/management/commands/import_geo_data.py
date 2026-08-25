import requests
import pycountry
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from slugify import slugify

from main.models import Pays, Province, Ville


GEONAMES_USERNAME = settings.GEONAMES_USERNAME


class Command(BaseCommand):
    help = "Importer pays, provinces et villes via Geonames"

    def handle(self, *args, **options):
        try:
            self.import_pays()

            for pays in Pays.objects.filter(is_active=True):
                self.stdout.write(f"🌍 {pays.nom}")
                self.import_provinces(pays)
                self.import_villes(pays)

            self.stdout.write(self.style.SUCCESS("✅ Import terminé"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur lors de l'import: {e}"))

    # -------------------------
    # PAYS
    # -------------------------
    def import_pays(self):
        """Import countries from pycountry"""
        count = 0
        for country in pycountry.countries:
            # Get the name in the primary language
            nom = getattr(country, 'name', getattr(country, 'official_name', country.alpha_2))
            
            # Truncate if too long
            nom = nom[:50] if nom else country.alpha_2
            
            pays, created = Pays.objects.update_or_create(
                code=country.alpha_2,
                defaults={
                    "nom": nom,
                    "is_active": True,
                },
            )
            if created:
                count += 1

        self.stdout.write(f"✅ {count} pays importés/actualisés")

    # -------------------------
    # PROVINCES (ADM1)
    # -------------------------
    def import_provinces(self, pays):
        """Import provinces for a specific country"""
        if not GEONAMES_USERNAME:
            self.stdout.write(self.style.WARNING(f"  ⚠️ Username Geonames non configuré pour {pays.nom}"))
            return 0

        url = "http://api.geonames.org/searchJSON"
        params = {
            "country": pays.code,
            "featureCode": "ADM1",
            "maxRows": 1000,
            "username": GEONAMES_USERNAME,
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'geonames' not in data:
                self.stdout.write(f"  ⚠️ Aucune donnée pour {pays.nom}")
                return 0
                
            provinces = data.get("geonames", [])
            imported_count = 0
            
            for p in provinces:
                nom = p.get("name", "Inconnu")[:50]
                code = p.get("adminCode1", str(p.get("geonameId", "")))[:10]
                
                if not code:
                    code = slugify(nom)[:10].upper()
                
                # Check if province already exists
                if not Province.objects.filter(nom=nom, pays=pays).exists():
                    Province.objects.create(
                        nom=nom,
                        code=code,
                        pays=pays,
                        is_active=True,
                    )
                    imported_count += 1
            
            self.stdout.write(f"  └─ {imported_count} provinces importées")
            return imported_count
            
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Erreur API pour {pays.nom}: {e}"))
            return 0
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Erreur inattendue pour {pays.nom}: {e}"))
            return 0

    # -------------------------
    # VILLES
    # -------------------------
    def import_villes(self, pays):
        """Import cities for a specific country"""
        if not GEONAMES_USERNAME:
            return 0

        provinces = Province.objects.filter(pays=pays, is_active=True)
        total_cities = 0
        
        for province in provinces:
            url = "http://api.geonames.org/searchJSON"
            params = {
                "country": pays.code,
                "adminCode1": province.code,
                "featureClass": "P",  # Cities, villages, etc.
                "maxRows": 1000,
                "username": GEONAMES_USERNAME,
            }

            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'geonames' not in data:
                    continue
                    
                villes = data.get("geonames", [])
                city_count = 0
                
                for v in villes:
                    nom = v.get("name", "Inconnu")[:50]
                    geoname_id = v.get("geonameId")
                    
                    if not geoname_id:
                        continue
                    
                    code = str(geoname_id)[:10]
                    
                    # Check if city already exists
                    if not Ville.objects.filter(
                        nom=nom, 
                        province=province, 
                        pays=pays
                    ).exists():
                        Ville.objects.create(
                            nom=nom,
                            code=code,
                            pays=pays,
                            province=province,
                            is_active=True,
                        )
                        city_count += 1
                
                total_cities += city_count
                self.stdout.write(f"     └─ {province.nom}: {city_count} villes")
                
            except requests.exceptions.RequestException:
                # Silently skip if API fails for this province
                continue
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"     ⚠️ Erreur pour {province.nom}: {e}"))
                continue
        
        return total_cities