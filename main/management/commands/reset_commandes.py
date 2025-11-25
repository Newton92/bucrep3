from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import Commande, MailInfo, MailAttachment, SuiviCommande
from django.db import transaction

class Command(BaseCommand):
    help = 'Supprime toutes les commandes et données associées pour repartir de zéro'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-recent',
            action='store_true',
            help='Garder les commandes des dernières 24 heures'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmer la suppression sans prompt'
        )
    
    def handle(self, *args, **options):
        keep_recent = options['keep_recent']
        confirm = options['confirm']
        
        # Compter les données
        commandes_count = Commande.objects.count()
        mail_info_count = MailInfo.objects.count()
        suivi_count = SuiviCommande.objects.count()
        
        if keep_recent:
            yesterday = timezone.now() - timezone.timedelta(days=1)
            commandes_to_delete = Commande.objects.filter(created_at__lt=yesterday)
            commandes_count = commandes_to_delete.count()
            self.stdout.write(f"🗑️  Commandes à supprimer (avant hier): {commandes_count}")
        else:
            self.stdout.write(f"📊 Données actuelles:")
            self.stdout.write(f"   Commandes: {commandes_count}")
            self.stdout.write(f"   Infos mail: {mail_info_count}")
            self.stdout.write(f"   Suivis: {suivi_count}")
        
        if not confirm:
            confirm = input("❌ Voulez-vous vraiment tout supprimer? (yes/NO): ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('❌ Suppression annulée'))
                return
        
        with transaction.atomic():
            # Supprimer dans l'ordre pour éviter les erreurs de clés étrangères
            self.stdout.write('🧹 Nettoyage en cours...')
            
            # 1. Supprimer les attachments de mail
            MailAttachment.objects.all().delete()
            self.stdout.write('✅ Pièces jointes supprimées')
            
            # 2. Supprimer les infos de mail
            MailInfo.objects.all().delete()
            self.stdout.write('✅ Historique emails supprimé')
            
            # 3. Supprimer les suivis
            SuiviCommande.objects.all().delete()
            self.stdout.write('✅ Suivis supprimés')
            
            # 4. Supprimer les commandes
            if keep_recent:
                commandes_deleted = commandes_to_delete.delete()
            else:
                commandes_deleted = Commande.objects.all().delete()
            
            self.stdout.write('✅ Commandes supprimées')
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Nettoyage terminé! Base prête pour de nouveaux tests.')
        )
        
        
        
# Supprimer tout
# python manage.py reset_commandes --confirm

# Garder les commandes récentes (24h)
# python manage.py reset_commandes --keep-recent --confirm