# management/commands/import_code_naf.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from main.models import CategoryNafCode, SubCategoryNafCode


class Command(BaseCommand):
    help = 'Importe les codes NAF détaillés (sous-catégories)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Efface les données existantes avant l\'importation',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule l\'importation sans sauvegarder en base de données',
        )

    def handle(self, *args, **options):
        clear_data = options['clear']
        dry_run = options.get('dry_run', False)
        
        # Données des codes NAF détaillés
        # Format: (code_categorie, code_naf, libelle_naf)
        naf_codes = [
            # Section A - Agriculture, sylviculture et pêche
            ("A", "01", "Culture et production animale, chasse et services annexes"),
            ("A", "01.1", "Culture de céréales (à l'exception du riz), de légumineuses et de graines oléagineuses"),
            ("A", "01.11Z", "Culture de céréales (à l'exception du riz), de légumineuses et de graines oléagineuses"),
            ("A", "01.12Z", "Culture du riz"),
            ("A", "01.13Z", "Culture de légumes, de melons, de racines et de tubercules"),
            ("A", "01.2", "Culture de fruits, de fruits à coque, de boissons et de plantes à épices"),
            ("A", "01.21Z", "Culture de la vigne"),
            ("A", "01.22Z", "Culture de fruits tropicaux et subtropicaux"),
            
            ("A", "02", "Sylviculture et exploitation forestière"),
            ("A", "02.1", "Sylviculture et autres activités forestières"),
            ("A", "02.10Z", "Sylviculture et autres activités forestières"),
            ("A", "02.2", "Exploitation forestière"),
            ("A", "02.20Z", "Exploitation forestière"),
            
            ("A", "03", "Pêche et aquaculture"),
            ("A", "03.1", "Pêche"),
            ("A", "03.11Z", "Pêche en mer"),
            ("A", "03.12Z", "Pêche en eau douce"),
            
            # Section B - Industries extractives
            ("B", "05", "Extraction de houille et de lignite"),
            ("B", "05.1", "Extraction de houille"),
            ("B", "05.10Z", "Extraction de houille"),
            ("B", "05.2", "Extraction de lignite"),
            ("B", "05.20Z", "Extraction de lignite"),
            
            ("B", "06", "Extraction d'hydrocarbures"),
            ("B", "06.1", "Extraction de pétrole brut"),
            ("B", "06.10Z", "Extraction de pétrole brut"),
            ("B", "06.2", "Extraction de gaz naturel"),
            ("B", "06.20Z", "Extraction de gaz naturel"),
            
            ("B", "07", "Extraction de minerais métalliques"),
            ("B", "07.1", "Extraction de minerais de fer"),
            ("B", "07.10Z", "Extraction de minerais de fer"),
            
            # Section C - Industrie manufacturière
            ("C", "10", "Industrie alimentaire"),
            ("C", "10.1", "Transformation et conservation de la viande et préparation de produits à base de viande"),
            ("C", "10.11Z", "Transformation et conservation de la viande de boucherie"),
            ("C", "10.12Z", "Transformation et conservation de la viande de volaille"),
            ("C", "10.13A", "Préparation industrielle de produits à base de viande de boucherie"),
            
            ("C", "11", "Fabrication de boissons"),
            ("C", "11.0", "Fabrication de boissons"),
            ("C", "11.01Z", "Production de boissons alcooliques distillées"),
            ("C", "11.02Z", "Production de vin (de raisin)"),
            ("C", "11.03Z", "Fabrication de cidre et de vins de fruits"),
            
            ("C", "13", "Fabrication de textiles"),
            ("C", "13.1", "Préparation de fibres textiles et filature"),
            ("C", "13.10Z", "Préparation de fibres textiles et filature"),
            ("C", "13.2", "Tissage"),
            ("C", "13.20Z", "Tissage"),
            
            ("C", "14", "Industrie de l'habillement"),
            ("C", "14.1", "Fabrication de vêtements, autres qu'en fourrure"),
            ("C", "14.11Z", "Fabrication de vêtements en cuir"),
            ("C", "14.12Z", "Fabrication de vêtements de travail"),
            
            ("C", "15", "Industrie du cuir et de la chaussure"),
            ("C", "15.1", "Apprêt et tannage des cuirs ; préparation et teinture des fourrures"),
            ("C", "15.11Z", "Apprêt et tannage des cuirs ; préparation et teinture des fourrures"),
            ("C", "15.2", "Fabrication d'articles de voyage, de maroquinerie et de sellerie"),
            ("C", "15.20Z", "Fabrication d'articles de voyage, de maroquinerie et de sellerie"),
            
            # Section D - Production et distribution d'énergie
            ("D", "35", "Production et distribution d'électricité, de gaz, de vapeur et d'air conditionné"),
            ("D", "35.1", "Production, transport et distribution d'électricité"),
            ("D", "35.11Z", "Production d'électricité"),
            ("D", "35.12Z", "Transport d'électricité"),
            ("D", "35.13Z", "Distribution d'électricité"),
            
            # Section E - Eau et gestion des déchets
            ("E", "36", "Captage, traitement et distribution d'eau"),
            ("E", "36.0", "Captage, traitement et distribution d'eau"),
            ("E", "36.00Z", "Captage, traitement et distribution d'eau"),
            
            ("E", "37", "Collecte et traitement des eaux usées"),
            ("E", "37.0", "Collecte et traitement des eaux usées"),
            ("E", "37.00Z", "Collecte et traitement des eaux usées"),
            
            # Section F - Construction
            ("F", "41", "Construction de bâtiments"),
            ("F", "41.1", "Promotion immobilière"),
            ("F", "41.10Z", "Promotion immobilière"),
            ("F", "41.2", "Construction de bâtiments résidentiels et non résidentiels"),
            ("F", "41.20A", "Construction de maisons individuelles"),
            ("F", "41.20B", "Construction d'autres bâtiments"),
            
            ("F", "42", "Génie civil"),
            ("F", "42.1", "Construction de routes et de voies ferrées"),
            ("F", "42.11Z", "Construction de routes et autoroutes"),
            ("F", "42.12Z", "Construction de voies ferrées de surface et souterraines"),
            
            # Section G - Commerce
            ("G", "45", "Commerce et réparation d'automobiles et de motocycles"),
            ("G", "45.1", "Commerce de véhicules automobiles"),
            ("G", "45.11Z", "Commerce de voitures et de véhicules automobiles légers"),
            ("G", "45.19Z", "Commerce d'autres véhicules automobiles"),
            
            ("G", "46", "Commerce de gros, à l'exception des automobiles et des motocycles"),
            ("G", "46.1", "Intermédiaires du commerce de gros"),
            ("G", "46.11Z", "Intermédiaires du commerce en matières premières agricoles, animaux vivants, matières premières textiles et produits semi-finis"),
            
            # Section H - Transports
            ("H", "49", "Transports terrestres et transport par conduites"),
            ("H", "49.1", "Transports ferroviaires interurbains de voyageurs"),
            ("H", "49.10Z", "Transports ferroviaires interurbains de voyageurs"),
            ("H", "49.2", "Transports ferroviaires de fret"),
            ("H", "49.20Z", "Transports ferroviaires de fret"),
            
            ("H", "50", "Transports par eau"),
            ("H", "50.1", "Transports maritimes et côtiers de passagers"),
            ("H", "50.10Z", "Transports maritimes et côtiers de passagers"),
            
            # Section I - Hébergement et restauration
            ("I", "55", "Hébergement"),
            ("I", "55.1", "Hôtels et hébergement similaire"),
            ("I", "55.10Z", "Hôtels et hébergement similaire"),
            ("I", "55.2", "Hébergement touristique et autre hébergement de courte durée"),
            ("I", "55.20Z", "Hébergement touristique et autre hébergement de courte durée"),
            
            ("I", "56", "Restauration"),
            ("I", "56.1", "Restauration traditionnelle"),
            ("I", "56.10A", "Restauration traditionnelle"),
            ("I", "56.10B", "Cafétérias et autres libres-services"),
            
            # Section J - Information et communication
            ("J", "58", "Édition"),
            ("J", "58.1", "Édition de livres et périodiques et autres activités d'édition"),
            ("J", "58.11Z", "Édition de livres"),
            ("J", "58.12Z", "Édition de répertoires et de fichiers d'adresses"),
            
            ("J", "62", "Programmation, conseil et autres activités informatiques"),
            ("J", "62.0", "Programmation, conseil et autres activités informatiques"),
            ("J", "62.01Z", "Programmation informatique"),
            ("J", "62.02Z", "Conseil informatique"),
            
            # Section K - Activités financières
            ("K", "64", "Activités des services financiers, hors assurance et caisses de retraite"),
            ("K", "64.1", "Intermédiation monétaire"),
            ("K", "64.11Z", "Activités de banque centrale"),
            ("K", "64.19Z", "Autres intermédiations monétaires"),
            
            ("K", "65", "Assurance"),
            ("K", "65.1", "Assurance"),
            ("K", "65.11Z", "Assurance vie"),
            ("K", "65.12Z", "Autres assurances"),
            
            # Section L - Immobilier
            ("L", "68", "Activités immobilières"),
            ("L", "68.1", "Activités des marchands de biens immobiliers"),
            ("L", "68.10Z", "Activités des marchands de biens immobiliers"),
            ("L", "68.2", "Location et exploitation de biens immobiliers propres ou loués"),
            ("L", "68.20A", "Location de logements"),
            
            # Section M - Activités spécialisées
            ("M", "69", "Activités juridiques et comptables"),
            ("M", "69.1", "Activités juridiques"),
            ("M", "69.10Z", "Activités juridiques"),
            ("M", "69.2", "Activités comptables"),
            ("M", "69.20Z", "Activités comptables"),
            
            # Section N - Services administratifs
            ("N", "77", "Activités de location et location-bail"),
            ("N", "77.1", "Location et location-bail de véhicules automobiles"),
            ("N", "77.11Z", "Location et location-bail de voitures et de véhicules automobiles légers"),
            
            ("N", "78", "Activités liées à l'emploi"),
            ("N", "78.1", "Activités des agences de placement de main-d'œuvre"),
            ("N", "78.10Z", "Activités des agences de placement de main-d'œuvre"),
            
            # Section O - Administration publique
            ("O", "84", "Administration publique et défense ; sécurité sociale obligatoire"),
            ("O", "84.1", "Administration publique générale"),
            ("O", "84.11Z", "Administration publique générale"),
            
            # Section P - Enseignement
            ("P", "85", "Enseignement"),
            ("P", "85.1", "Enseignement pré-primaire"),
            ("P", "85.10Z", "Enseignement pré-primaire"),
            ("P", "85.2", "Enseignement primaire"),
            ("P", "85.20Z", "Enseignement primaire"),
            
            # Section Q - Santé
            ("Q", "86", "Activités pour la santé humaine"),
            ("Q", "86.1", "Activités hospitalières"),
            ("Q", "86.10Z", "Activités hospitalières"),
            ("Q", "86.2", "Activité des médecins et des dentistes"),
            ("Q", "86.21Z", "Activité des médecins généralistes"),
            
            # Section R - Arts et spectacles
            ("R", "90", "Activités créatives, artistiques et de spectacle"),
            ("R", "90.0", "Activités créatives, artistiques et de spectacle"),
            ("R", "90.01Z", "Arts du spectacle vivant"),
            ("R", "90.02Z", "Activités de soutien au spectacle vivant"),
            
            # Section S - Autres services
            ("S", "94", "Activités des organisations associatives"),
            ("S", "94.1", "Activités des organisations économiques, patronales et professionnelles"),
            ("S", "94.11Z", "Activités des organisations patronales et consulaires"),
            ("S", "94.12Z", "Activités des organisations professionnelles"),
            
            # Section T - Ménages
            ("T", "97", "Activités des ménages en tant qu'employeurs de personnel domestique"),
            ("T", "97.0", "Activités des ménages en tant qu'employeurs de personnel domestique"),
            ("T", "97.00Z", "Activités des ménages en tant qu'employeurs de personnel domestique"),
            
            # Section U - Extra-territoriales
            ("U", "99", "Activités des organisations et organismes extra-territoriaux"),
            ("U", "99.0", "Activités des organisations et organismes extra-territoriaux"),
            ("U", "99.00Z", "Activités des organisations et organismes extra-territoriaux"),
        ]

        try:
            if dry_run:
                self.stdout.write("[WARNING] " + "MODE SIMULATION - Aucune donnée ne sera sauvegardée")
                self.simulate_import(naf_codes)
            else:
                with transaction.atomic():
                    # Étape 1: Vider les données existantes si demandé
                    if clear_data:
                        self.clear_existing_data()
                    
                    # Étape 2: Importer les nouvelles données
                    self.import_naf_codes(naf_codes)
                    
                    self.stdout.write(self.style.SUCCESS('[SUCCESS] ' + 'Importation des codes NAF détaillés terminée avec succès!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {str(e)}'))
            import traceback
            traceback.print_exc()
            raise
    
    def clear_existing_data(self):
        """Vide toutes les données existantes des sous-catégories NAF"""
        self.stdout.write("[WARNING] " + 'Suppression des sous-catégories NAF existantes...')
        
        subcategories_count = SubCategoryNafCode.objects.count()
        
        # Supprimer les sous-catégories
        deleted_count, _ = SubCategoryNafCode.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(
            f'[SUCCESS] Suppression de {deleted_count} sous-catégories NAF.'
        ))
    
    def import_naf_codes(self, naf_codes):
        subcategories_created = 0
        subcategories_updated = 0
        categories_not_found = []
        
        self.stdout.write("Début de l'importation des codes NAF détaillés...")
        
        # Préparer un cache des catégories
        categories_cache = {}
        all_categories = CategoryNafCode.objects.all()
        for cat in all_categories:
            categories_cache[cat.code] = cat
        
        for i, (cat_code, naf_code, libelle) in enumerate(naf_codes, 1):
            try:
                # Vérifier si la catégorie existe
                if cat_code not in categories_cache:
                    categories_not_found.append(cat_code)
                    self.stdout.write(self.style.ERROR(
                        f'[ERREUR] Catégorie {cat_code} non trouvée pour le code NAF {naf_code}'
                    ))
                    continue
                
                category = categories_cache[cat_code]
                
                # Utiliser le poids de la catégorie parent
                poids = category.poids
                
                # Créer ou mettre à jour la sous-catégorie
                subcategory, created = SubCategoryNafCode.objects.update_or_create(
                    code=naf_code,
                    defaults={
                        'category': category,
                        'libelle': libelle,
                        'active': True,
                        'poids': poids,
                    }
                )
                
                if created:
                    subcategories_created += 1
                    # Afficher un point tous les 20 enregistrements
                    if subcategories_created % 20 == 0:
                        self.stdout.write(f"  {subcategories_created} sous-catégories créées...")
                else:
                    subcategories_updated += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'[ERREUR] Impossible de créer/mettre à jour le code NAF {naf_code}: {str(e)}'
                ))
        
        # Résumé final
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS('[SUCCESS] ' + 'Importation terminée!'))
        self.stdout.write(f"Sous-catégories créées: {subcategories_created}")
        self.stdout.write(f"Sous-catégories mises à jour: {subcategories_updated}")
        
        if categories_not_found:
            self.stdout.write(self.style.WARNING(
                f"Catégories non trouvées (à importer d'abord): {set(categories_not_found)}"
            ))
            self.stdout.write(self.style.WARNING(
                "Exécutez d'abord: python manage.py import_category_naf"
            ))
        
        self.stdout.write("="*50)
    
    def simulate_import(self, naf_codes):
        """Simule l'importation sans sauvegarder"""
        self.stdout.write("SIMULATION - Voici ce qui serait importé:")
        
        # Regrouper par catégorie pour l'affichage
        grouped_codes = {}
        for cat_code, naf_code, libelle in naf_codes:
            if cat_code not in grouped_codes:
                grouped_codes[cat_code] = []
            grouped_codes[cat_code].append((naf_code, libelle))
        
        for cat_code, codes in grouped_codes.items():
            self.stdout.write(f"\nCatégorie {cat_code}:")
            for naf_code, libelle in codes[:5]:  # Afficher seulement les 5 premiers
                self.stdout.write(f"  • {naf_code} - {libelle}")
            if len(codes) > 5:
                self.stdout.write(f"  ... et {len(codes) - 5} autres")
        
        self.stdout.write(f"\nTotal: {len(naf_codes)} codes NAF seraient importés")