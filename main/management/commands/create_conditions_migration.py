# management/commands/create_conditions_migration.py
from django.core.management.base import BaseCommand
from django.db import migrations, models
import os

class Command(BaseCommand):
    help = 'Crée une migration pour les modèles de conditions'
    
    def handle(self, *args, **options):
        # Créer le contenu de la migration
        migration_content = '''# Generated manually for initial data
from django.db import migrations
from django.utils.translation import gettext_lazy as _


def create_conditions_achat(apps, schema_editor):
    ListeConditionAchat = apps.get_model('main', 'ListeConditionAchat')
    
    conditions = [
        _("Paiement comptant"),
        _("Paiement à réception"),
        _("Paiement par virement"),
        _("Paiement contre documents"),
        _("Crédit documentaire"),
        _("Lettre de crédit à terme"),
        _("Lettre de crédit à vue"),
        _("Délai de paiement de 30 à 60 jours date BL"),
        _("Délai de paiement de 60 à 90 jours date LB"),
        _("Délai de paiement de 90 à 120 Jours date BL"),
        _("Délais de paiement de 30 à 60 jours avec pénalités de retard"),
        _("Délais de paiement de 60 à 90 jours avec pénalités de retard"),
        _("Délais de paiement de 90 à 120 jours avec pénalités de retard"),
        _("Délais de paiement de 120 à 180 jours avec pénalités de retard"),
    ]
    
    for condition in conditions:
        ListeConditionAchat.objects.get_or_create(nom=condition)


def create_conditions_vente(apps, schema_editor):
    ListeConditionVente = apps.get_model('main', 'ListeConditionVente')
    
    conditions = [
        _("Espèces"),
        _("Chèque"),
        _("Virement bancaire"),
        _("Effets de commerce papier"),
        _("Lettre de Change"),
        _("Billet à ordre"),
        _("Carte de credit/debit"),
        _("Délais de paiement de 15 à 30 jours avec pénalités de retard"),
        _("Délais de paiement de 30 à 60 jours avec pénalités de retard"),
        _("Délais de paiement de 60 à 90 jours avec pénalités de retard"),
    ]
    
    for condition in conditions:
        ListeConditionVente.objects.get_or_create(nom=condition)


def reverse_migration(apps, schema_editor):
    # Pour rollback, supprimer toutes les données
    ListeConditionAchat = apps.get_model('main', 'ListeConditionAchat')
    ListeConditionVente = apps.get_model('main', 'ListeConditionVente')
    
    ListeConditionAchat.objects.all().delete()
    ListeConditionVente.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('main', 'XXXX_previous_migration'),  # À remplacer
    ]

    operations = [
        migrations.RunPython(
            code=create_conditions_achat,
            reverse_code=reverse_migration,
        ),
        migrations.RunPython(
            code=create_conditions_vente,
            reverse_code=reverse_migration,
        ),
    ]
'''
        
        # Déterminer le prochain numéro de migration
        migrations_dir = 'main/migrations'
        existing_migrations = [f for f in os.listdir(migrations_dir) if f.endswith('.py')]
        next_num = len(existing_migrations) + 1
        
        # Nom du fichier
        filename = f'{migrations_dir}/{next_num:04d}_initial_conditions.py'
        
        # Créer le fichier
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(migration_content)
        
        self.stdout.write(self.style.SUCCESS(f'Migration créée: {filename}'))