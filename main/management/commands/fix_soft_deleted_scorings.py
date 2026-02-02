# main/management/commands/fix_soft_deleted_scorings.py
from django.core.management.base import BaseCommand
from main.models import Scoring
from safedelete.models import HARD_DELETE

class Command(BaseCommand):
    help = 'Nettoie les scorings soft-deleted qui causent des conflits'

    def add_arguments(self, parser):
        parser.add_argument(
            '--acheteur-id',
            type=int,
            help='ID de l\'acheteur à nettoyer',
        )
        parser.add_argument(
            '--hard-delete',
            action='store_true',
            help='Supprimer définitivement (HARD DELETE)',
        )

    def handle(self, *args, **options):
        acheteur_id = options.get('acheteur_id')
        hard_delete = options.get('hard_delete', False)
        
        # Trouver les soft-deleted
        queryset = Scoring.all_objects.filter(deleted__isnull=False)
        
        if acheteur_id:
            queryset = queryset.filter(acheteur_id=acheteur_id)
        
        count = queryset.count()
        self.stdout.write(f"Trouvé {count} scorings soft-deleted")
        
        if count > 0:
            if hard_delete:
                # Suppression définitive
                queryset.delete(force_policy=HARD_DELETE)
                self.stdout.write(self.style.SUCCESS(
                    f'{count} scorings supprimés définitivement'
                ))
            else:
                # Restaurer
                for scoring in queryset:
                    scoring.undelete()
                self.stdout.write(self.style.SUCCESS(
                    f'{count} scorings restaurés'
                ))