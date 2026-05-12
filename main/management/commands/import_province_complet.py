# your_app/management/commands/import_province_complet.py
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

class Command(BaseCommand):
    """Commande qui exécute les deux imports en séquence"""
    
    help = _("Exécute l'import complet des provinces puis l'association aux villes")
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-provinces',
            action='store_true',
            help=_("Saute l'import des provinces (déjà fait)")
        )
        parser.add_argument(
            '--skip-villes',
            action='store_true',
            help=_("Saute l'association des villes (déjà fait)")
        )
    
    def handle(self, *args, **options):
        self.stdout.write("[SUCCESS] " + _("Début de l'import complet des provinces..."))
        
        # Étape 1: Import des provinces par pays
        if not options['skip_provinces']:
            self.stdout.write(_("\n1. Import des provinces par pays..."))
            try:
                call_command('import_province_pays')
                self.stdout.write("[SUCCESS] " + _("[OK] Import provinces terminé"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(_(f"✗ Erreur import provinces: {str(e)}")))
        
        # Étape 2: Association villes/provinces
        if not options['skip_villes']:
            self.stdout.write(_("\n2. Association villes/provinces..."))
            try:
                call_command('import_province_in_ville')
                self.stdout.write("[SUCCESS] " + _("[OK] Association villes terminée"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(_(f"✗ Erreur association villes: {str(e)}")))
        
        self.stdout.write("[SUCCESS] " + _("\nImport complet terminé avec succès!"))