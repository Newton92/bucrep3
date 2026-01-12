from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"

    def ready(self):
        # Importer vos signaux ici
        import main.signals  # Assurez-vous que le chemin est correct
        
        # Importer les patches
        from . import patches
        patches.patch_changes_mixin()
