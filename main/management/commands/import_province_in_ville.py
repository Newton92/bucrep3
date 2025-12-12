# your_app/management/commands/import_province_in_ville.py
import requests
from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.utils.translation import gettext as _
from ...models import Ville, Province, Pays

class Command(BaseCommand):
    help = _("Associe chaque ville existante à une province")

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help=_("Nombre de villes à traiter par transaction")
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help=_("Simule l'opération sans sauvegarder")
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(_("Début de l'association villes/provinces...")))
        
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        
        # Villes sans province
        villes_sans_province = Ville.objects.filter(
            province__isnull=True,
            is_active=True
        )
        
        total_villes = villes_sans_province.count()
        self.stdout.write(f"{total_villes} villes à traiter")
        
        updated_count = 0
        errors = []
        
        for i in range(0, total_villes, batch_size):
            batch = villes_sans_province[i:i + batch_size]
            
            if not dry_run:
                with transaction.atomic():
                    for ville in batch:
                        try:
                            province = self.find_province_for_city(ville)
                            if province:
                                ville.province = province
                                ville.save()
                                updated_count += 1
                                if updated_count % 50 == 0:
                                    self.stdout.write(f"  {updated_count} villes traitées...")
                            else:
                                errors.append(f"{ville.nom}: province non trouvée")
                        except Exception as e:
                            errors.append(f"{ville.nom}: {str(e)}")
            else:
                # Mode simulation
                for ville in batch:
                    province = self.find_province_for_city(ville)
                    if province:
                        updated_count += 1
        
        # Rapport final
        self.stdout.write(self.style.SUCCESS(
            _("\nOpération terminée:")
        ))
        self.stdout.write(f"  • Villes mises à jour: {updated_count}/{total_villes}")
        
        if errors:
            self.stdout.write(self.style.WARNING(
                _("\nErreurs rencontrées:")
            ))
            for error in errors[:10]:  # Affiche seulement les 10 premières erreurs
                self.stdout.write(f"  • {error}")
            if len(errors) > 10:
                self.stdout.write(f"  ... et {len(errors) - 10} autres erreurs")
        
        if dry_run:
            self.stdout.write(self.style.NOTICE(
                _("\nMode simulation - aucune donnée modifiée")
            ))
    
    def find_province_for_city(self, ville):
        """
        Trouve la province correspondante pour une ville
        """
        # Stratégie 1: Cherche par le nom de la ville dans les provinces existantes
        # (pour les pays où les provinces ont déjà été importées)
        
        # Stratégie 2: Utilise l'API de géocodage pour trouver la région/province
        if hasattr(ville, 'pays') and ville.pays:
            return self.find_province_via_api(ville)
        
        return None
    
    def find_province_via_api(self, ville):
        """
        Utilise une API de géocodage pour trouver la province
        """
        # API géo.api.gouv.fr pour les villes françaises[citation:2][citation:6]
        if ville.pays.code.lower() == 'fr':
            try:
                # Recherche la ville dans l'API des communes
                response = requests.get(
                    f"https://geo.api.gouv.fr/communes?nom={ville.nom}&fields=region",
                    timeout=5
                )
                if response.status_code == 200:
                    communes = response.json()
                    if communes:
                        region_code = communes[0].get('region', {}).get('code')
                        if region_code:
                            return Province.objects.filter(
                                code=region_code,
                                pays=ville.pays
                            ).first()
            except requests.RequestException:
                pass
        
        # Pour les autres pays, vous pouvez utiliser d'autres APIs
        # Par exemple OpenCage[citation:8] ou Nominatim (OpenStreetMap)
        
        return None