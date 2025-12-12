# your_app/management/commands/import_province_pays.py
import requests
import json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext as _
from ...models import Pays, Province

class Command(BaseCommand):
    help = _("Importe les provinces pour chaque pays à partir d'API externes")
    
    # Base de données de provinces par pays (à étendre)
    PREDEFINED_PROVINCES = {
        # Afrique de l'Ouest
        'cm': [  # Cameroun
            {'nom': 'Centre', 'code': 'CE'},
            {'nom': 'Littoral', 'code': 'LT'},
            {'nom': 'Ouest', 'code': 'OU'},
            {'nom': 'Nord', 'code': 'NO'},
            {'nom': 'Extrême-Nord', 'code': 'EN'},
            {'nom': 'Sud', 'code': 'SU'},
            {'nom': 'Est', 'code': 'ES'},
            {'nom': 'Adamaoua', 'code': 'AD'},
            {'nom': 'Nord-Ouest', 'code': 'NW'},
            {'nom': 'Sud-Ouest', 'code': 'SW'},
        ],
        'ci': [  # Côte d'Ivoire
            {'nom': 'Abidjan', 'code': 'ABJ'},
            {'nom': 'Bas-Sassandra', 'code': 'BAS'},
            {'nom': 'Comoé', 'code': 'COM'},
            {'nom': 'Denguélé', 'code': 'DEN'},
            {'nom': 'Gôh-Djiboua', 'code': 'GDJ'},
            {'nom': 'Lacs', 'code': 'LAC'},
            {'nom': 'Lagunes', 'code': 'LAG'},
            {'nom': 'Montagnes', 'code': 'MON'},
            {'nom': 'Sassandra-Marahoué', 'code': 'SAS'},
            {'nom': 'Savanes', 'code': 'SAV'},
            {'nom': 'Vallée du Bandama', 'code': 'VAL'},
            {'nom': 'Woroba', 'code': 'WOR'},
            {'nom': 'Zanzan', 'code': 'ZAN'},
        ],
        'sn': [  # Sénégal
            {'nom': 'Dakar', 'code': 'DK'},
            {'nom': 'Diourbel', 'code': 'DB'},
            {'nom': 'Fatick', 'code': 'FK'},
            {'nom': 'Kaffrine', 'code': 'KA'},
            {'nom': 'Kaolack', 'code': 'KL'},
            {'nom': 'Kédougou', 'code': 'KE'},
            {'nom': 'Kolda', 'code': 'KD'},
            {'nom': 'Louga', 'code': 'LG'},
            {'nom': 'Matam', 'code': 'MT'},
            {'nom': 'Saint-Louis', 'code': 'SL'},
            {'nom': 'Sédhiou', 'code': 'SE'},
            {'nom': 'Tambacounda', 'code': 'TC'},
            {'nom': 'Thiès', 'code': 'TH'},
            {'nom': 'Ziguinchor', 'code': 'ZG'},
        ],
        # Afrique Centrale
        'cd': [  # République Démocratique du Congo
            {'nom': 'Kinshasa', 'code': 'KIN'},
            {'nom': 'Kongo Central', 'code': 'KON'},
            {'nom': 'Kwango', 'code': 'KWA'},
            {'nom': 'Kwilu', 'code': 'KWI'},
            {'nom': 'Mai-Ndombe', 'code': 'MAI'},
            {'nom': 'Équateur', 'code': 'EQU'},
            {'nom': 'Mongala', 'code': 'MON'},
            {'nom': 'Nord-Ubangi', 'code': 'NUB'},
            {'nom': 'Sud-Ubangi', 'code': 'SUB'},
            {'nom': 'Tshuapa', 'code': 'TSH'},
        ],
        # Afrique de l'Est
        'ke': [  # Kenya
            {'nom': 'Nairobi', 'code': 'NBO'},
            {'nom': 'Central', 'code': 'CEN'},
            {'nom': 'Coast', 'code': 'COA'},
            {'nom': 'Eastern', 'code': 'EAS'},
            {'nom': 'North Eastern', 'code': 'NEA'},
            {'nom': 'Nyanza', 'code': 'NYA'},
            {'nom': 'Rift Valley', 'code': 'RIF'},
            {'nom': 'Western', 'code': 'WES'},
        ],
        'tz': [  # Tanzanie
            {'nom': 'Arusha', 'code': 'ARU'},
            {'nom': 'Dar es Salaam', 'code': 'DAR'},
            {'nom': 'Dodoma', 'code': 'DOD'},
            {'nom': 'Geita', 'code': 'GEI'},
            {'nom': 'Iringa', 'code': 'IRI'},
            {'nom': 'Kagera', 'code': 'KAG'},
            {'nom': 'Katavi', 'code': 'KAT'},
            {'nom': 'Kigoma', 'code': 'KIG'},
            {'nom': 'Kilimanjaro', 'code': 'KIL'},
            {'nom': 'Lindi', 'code': 'LIN'},
            {'nom': 'Manyara', 'code': 'MAN'},
            {'nom': 'Mara', 'code': 'MAR'},
            {'nom': 'Mbeya', 'code': 'MBE'},
            {'nom': 'Morogoro', 'code': 'MOR'},
            {'nom': 'Mtwara', 'code': 'MTW'},
            {'nom': 'Mwanza', 'code': 'MWA'},
            {'nom': 'Njombe', 'code': 'NJO'},
            {'nom': 'Pemba North', 'code': 'PNB'},
            {'nom': 'Pemba South', 'code': 'PSB'},
            {'nom': 'Pwani', 'code': 'PWA'},
            {'nom': 'Rukwa', 'code': 'RUK'},
            {'nom': 'Ruvuma', 'code': 'RUV'},
            {'nom': 'Shinyanga', 'code': 'SHI'},
            {'nom': 'Simiyu', 'code': 'SIM'},
            {'nom': 'Singida', 'code': 'SIN'},
            {'nom': 'Songwe', 'code': 'SON'},
            {'nom': 'Tabora', 'code': 'TAB'},
            {'nom': 'Tanga', 'code': 'TAN'},
            {'nom': 'Zanzibar North', 'code': 'ZNB'},
            {'nom': 'Zanzibar South', 'code': 'ZSB'},
            {'nom': 'Zanzibar West', 'code': 'ZWB'},
        ],
        # Afrique du Nord
        'ma': [  # Maroc
            {'nom': 'Tanger-Tétouan-Al Hoceïma', 'code': 'TTA'},
            {'nom': "L'Oriental", 'code': 'ORI'},
            {'nom': 'Fès-Meknès', 'code': 'FES'},
            {'nom': 'Rabat-Salé-Kénitra', 'code': 'RSK'},
            {'nom': 'Béni Mellal-Khénifra', 'code': 'BMK'},
            {'nom': 'Casablanca-Settat', 'code': 'CAS'},
            {'nom': 'Marrakech-Safi', 'code': 'MAR'},
            {'nom': 'Drâa-Tafilalet', 'code': 'DRA'},
            {'nom': 'Souss-Massa', 'code': 'SOU'},
            {'nom': 'Guelmim-Oued Noun', 'code': 'GON'},
            {'nom': 'Laâyoune-Sakia El Hamra', 'code': 'LAH'},
            {'nom': 'Dakhla-Oued Ed-Dahab', 'code': 'DAK'},
        ],
        'dz': [  # Algérie
            {'nom': 'Adrar', 'code': 'ADR'},
            {'nom': 'Chlef', 'code': 'CHL'},
            {'nom': 'Laghouat', 'code': 'LAG'},
            {'nom': 'Oum El Bouaghi', 'code': 'OEB'},
            {'nom': 'Batna', 'code': 'BAT'},
            {'nom': 'Béjaïa', 'code': 'BEJ'},
            {'nom': 'Biskra', 'code': 'BIS'},
            {'nom': 'Béchar', 'code': 'BEC'},
            {'nom': 'Blida', 'code': 'BLI'},
            {'nom': 'Bouira', 'code': 'BOU'},
            {'nom': 'Tamanrasset', 'code': 'TAM'},
            {'nom': 'Tébessa', 'code': 'TEB'},
            {'nom': 'Tlemcen', 'code': 'TLE'},
            {'nom': 'Tiaret', 'code': 'TIA'},
            {'nom': 'Tizi Ouzou', 'code': 'TIZ'},
            {'nom': 'Alger', 'code': 'ALG'},
            {'nom': 'Djelfa', 'code': 'DJF'},
            {'nom': 'Jijel', 'code': 'JIJ'},
            {'nom': 'Sétif', 'code': 'SET'},
            {'nom': 'Saïda', 'code': 'SAI'},
            {'nom': 'Skikda', 'code': 'SKI'},
            {'nom': 'Sidi Bel Abbès', 'code': 'SBA'},
            {'nom': 'Annaba', 'code': 'ANN'},
            {'nom': 'Guelma', 'code': 'GUEL'},
            {'nom': 'Constantine', 'code': 'CON'},
            {'nom': 'Médéa', 'code': 'MED'},
            {'nom': 'Mostaganem', 'code': 'MOS'},
            {'nom': "M'Sila", 'code': 'MSI'},
            {'nom': 'Mascara', 'code': 'MAS'},
            {'nom': 'Ouargla', 'code': 'OUA'},
            {'nom': 'Oran', 'code': 'ORA'},
            {'nom': 'El Bayadh', 'code': 'EBA'},
            {'nom': 'Illizi', 'code': 'ILL'},
            {'nom': 'Bordj Bou Arréridj', 'code': 'BBA'},
            {'nom': 'Boumerdès', 'code': 'BMD'},
            {'nom': 'El Tarf', 'code': 'ETA'},
            {'nom': 'Tindouf', 'code': 'TIN'},
            {'nom': 'Tissemsilt', 'code': 'TIS'},
            {'nom': 'El Oued', 'code': 'EOU'},
            {'nom': 'Khenchela', 'code': 'KHE'},
            {'nom': 'Souk Ahras', 'code': 'SOU'},
            {'nom': 'Tipaza', 'code': 'TIP'},
            {'nom': 'Mila', 'code': 'MIL'},
            {'nom': 'Aïn Defla', 'code': 'AIN'},
            {'nom': 'Naâma', 'code': 'NAA'},
            {'nom': 'Aïn Témouchent', 'code': 'AIT'},
            {'nom': 'Ghardaïa', 'code': 'GHA'},
            {'nom': 'Relizane', 'code': 'REL'},
        ],
        # Afrique Australe
        'za': [  # Afrique du Sud
            {'nom': 'Eastern Cape', 'code': 'EC'},
            {'nom': 'Free State', 'code': 'FS'},
            {'nom': 'Gauteng', 'code': 'GP'},
            {'nom': 'KwaZulu-Natal', 'code': 'KZN'},
            {'nom': 'Limpopo', 'code': 'LP'},
            {'nom': 'Mpumalanga', 'code': 'MP'},
            {'nom': 'Northern Cape', 'code': 'NC'},
            {'nom': 'North West', 'code': 'NW'},
            {'nom': 'Western Cape', 'code': 'WC'},
        ],
        'ng': [  # Nigeria
            {'nom': 'Abia', 'code': 'AB'},
            {'nom': 'Adamawa', 'code': 'AD'},
            {'nom': 'Akwa Ibom', 'code': 'AK'},
            {'nom': 'Anambra', 'code': 'AN'},
            {'nom': 'Bauchi', 'code': 'BA'},
            {'nom': 'Bayelsa', 'code': 'BY'},
            {'nom': 'Benue', 'code': 'BE'},
            {'nom': 'Borno', 'code': 'BO'},
            {'nom': 'Cross River', 'code': 'CR'},
            {'nom': 'Delta', 'code': 'DE'},
            {'nom': 'Ebonyi', 'code': 'EB'},
            {'nom': 'Edo', 'code': 'ED'},
            {'nom': 'Ekiti', 'code': 'EK'},
            {'nom': 'Enugu', 'code': 'EN'},
            {'nom': 'FCT Abuja', 'code': 'FC'},
            {'nom': 'Gombe', 'code': 'GO'},
            {'nom': 'Imo', 'code': 'IM'},
            {'nom': 'Jigawa', 'code': 'JI'},
            {'nom': 'Kaduna', 'code': 'KD'},
            {'nom': 'Kano', 'code': 'KN'},
            {'nom': 'Katsina', 'code': 'KT'},
            {'nom': 'Kebbi', 'code': 'KE'},
            {'nom': 'Kogi', 'code': 'KO'},
            {'nom': 'Kwara', 'code': 'KW'},
            {'nom': 'Lagos', 'code': 'LA'},
            {'nom': 'Nasarawa', 'code': 'NA'},
            {'nom': 'Niger', 'code': 'NI'},
            {'nom': 'Ogun', 'code': 'OG'},
            {'nom': 'Ondo', 'code': 'ON'},
            {'nom': 'Osun', 'code': 'OS'},
            {'nom': 'Oyo', 'code': 'OY'},
            {'nom': 'Plateau', 'code': 'PL'},
            {'nom': 'Rivers', 'code': 'RI'},
            {'nom': 'Sokoto', 'code': 'SO'},
            {'nom': 'Taraba', 'code': 'TA'},
            {'nom': 'Yobe', 'code': 'YO'},
            {'nom': 'Zamfara', 'code': 'ZA'},
        ],
        # Ajoutez d'autres pays africains selon vos besoins
    }

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(_("Début de l'importation des provinces...")))
        
        pays_list = Pays.objects.filter(is_active=True)
        total_created = 0
        
        for pays in pays_list:
            country_code = pays.code.lower()
            self.stdout.write(f"\nTraitement de {pays.nom} ({country_code})...")
            
            provinces_count = self.import_provinces_for_country(pays)
            total_created += provinces_count
            
            if provinces_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ {provinces_count} provinces importées")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"  ✗ Aucune province trouvée")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nImportation terminée. Total: {total_created} provinces créées"
            )
        )
    
    def get_api_strategy_for_country(self, pays):
        """
        Détermine la meilleure stratégie pour un pays donné
        """
        country_code = pays.code.lower()
        
        # 1. API officielle française pour les DOM-TOM
        if country_code in ['fr', 'gf', 'gp', 'mq', 're', 'yt']:
            return ('api_france', "https://geo.api.gouv.fr/regions")
        
        # 2. Données pré-définies (priorité pour l'Afrique)
        if country_code in self.PREDEFINED_PROVINCES:
            return ('predefined', None)
        
        # 3. API OpenStreetMap Nominatim (générique)
        return ('nominatim', None)
    
    def import_provinces_for_country(self, pays):
        """
        Importe les provinces pour un pays spécifique
        """
        strategy, api_url = self.get_api_strategy_for_country(pays)
        
        if strategy == 'api_france':
            return self.import_french_regions(pays, api_url)
        elif strategy == 'predefined':
            return self.import_predefined_provinces(pays)
        elif strategy == 'nominatim':
            return self.import_via_nominatim(pays)
        else:
            self.stdout.write(
                self.style.WARNING(f"  Stratégie non définie pour {pays.code}")
            )
            return 0
    
    def import_french_regions(self, pays, api_url):
        """Importe les régions françaises comme provinces"""
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            regions = response.json()
            
            created_count = 0
            with transaction.atomic():
                for region in regions:
                    province, created = Province.objects.get_or_create(
                        code=region['code'],
                        pays=pays,
                        defaults={
                            'nom': region['nom'],
                            'is_active': True
                        }
                    )
                    if created:
                        created_count += 1
            
            return created_count
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Erreur API: {str(e)}"))
            return 0
    
    def import_predefined_provinces(self, pays):
        """Utilise les données pré-définies"""
        country_code = pays.code.lower()
        provinces_data = self.PREDEFINED_PROVINCES.get(country_code, [])
        
        created_count = 0
        with transaction.atomic():
            for province_data in provinces_data:
                province, created = Province.objects.get_or_create(
                    code=province_data['code'],
                    pays=pays,
                    defaults={
                        'nom': province_data['nom'],
                        'is_active': True
                    }
                )
                if created:
                    created_count += 1
        
        return created_count
    
    def import_via_nominatim(self, pays):
        """
        Utilise OpenStreetMap Nominatim pour les pays sans données pré-définies
        Attention: Limite de 1 requête par seconde
        """
        import time
        
        try:
            # Recherche les subdivisions administratives du pays
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'country': pays.nom,
                'featuretype': 'state',  # ou 'admin_level' pour différents niveaux
                'format': 'json',
                'limit': 50,
                'polygon': 0
            }
            headers = {
                'User-Agent': 'Django-Provinces-Import/1.0'
            }
            
            time.sleep(1)  # Respect de la limite de taux
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                states = response.json()
                created_count = 0
                
                with transaction.atomic():
                    for state in states:
                        # Extrait le nom et le code
                        display_name = state.get('display_name', '')
                        state_name = display_name.split(',')[0] if display_name else state.get('name', '')
                        
                        # Crée un code simplifié
                        province_code = self.generate_province_code(state_name, pays.code)
                        
                        if state_name:
                            province, created = Province.objects.get_or_create(
                                code=province_code,
                                pays=pays,
                                defaults={
                                    'nom': state_name,
                                    'is_active': True
                                }
                            )
                            if created:
                                created_count += 1
                
                return created_count
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Nominatim error: {str(e)}"))
        
        return 0
    
    def generate_province_code(self, province_name, country_code):
        """Génère un code de province basé sur le nom"""
        # Retire les caractères spéciaux et prend les 3 premières lettres
        import re
        
        clean_name = re.sub(r'[^a-zA-Z]', '', province_name)
        base_code = clean_name[:3].upper() if clean_name else 'PRO'
        
        # Combine avec le code pays pour éviter les doublons
        return f"{country_code}_{base_code}"
    
    
    
    
    
    
    
    
# 1. Importez d'abord les provinces pour chaque pays
# python manage.py import_province_pays

# 2. Associez les villes aux provinces
# python manage.py import_province_in_ville

# Avec options
# python manage.py import_province_in_ville --batch-size=200 --dry-run