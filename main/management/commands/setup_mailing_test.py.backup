# management/commands/setup_mailing_test.py
from django.core.management.base import BaseCommand
from main.utils import generate_test_commandes
from main.utils import assign_commandes_to_clients

class Command(BaseCommand):
    help = 'Setup complet pour tester le module mailing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=15,
            help='Nombre de commandes à générer'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write('[LAUNCH] Setup du module mailing...')
        
        # Étape 1: Générer les commandes
        self.stdout.write('1. Génération des commandes...')
        generate_test_commandes(count)
        
        # Étape 2: Corriger les associations
        self.stdout.write('2. Correction des associations...')
        assign_commandes_to_clients()
        
        # Étape 3: Vérification
        self.stdout.write('3. Vérification...')
        from main.models import Client, Commande
        
        clients = Client.objects.all()
        self.stdout.write(f"👥 Clients: {clients.count()}")
        self.stdout.write(f"📦 Commandes totales: {Commande.objects.count()}")
        
        for client in clients:
            commandes_count = Commande.objects.filter(email=client.email).count()
            self.stdout.write(
                self.style.SUCCESS(f"   {client.nom}: {commandes_count} commande(s)")
            )
        
        self.stdout.write(
            self.style.SUCCESS('[DONE] Setup terminé! Le module mailing est prêt.')
        )