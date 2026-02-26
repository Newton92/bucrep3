#!/usr/bin/env python
import os
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bucrep.settings')
django.setup()

from main.models import Commande, User, Acheteur, Devise, Pays, Ville

# Récupérer ou créer le client
client_user, created = User.objects.get_or_create(
    username='acremac_test',
    defaults={
        'email': 'acremac_test@example.com',
        'first_name': 'ACREMAC',
        'last_name': 'TEST',
        'is_staff': False,
        'is_active': True,
    }
)
print(f"Client User: {client_user.username} ({'créé' if created else 'existant'})")

# Récupérer l'acheteur (ou créer s'il n'existe pas)
try:
    acheteur = Acheteur.objects.get(nom='Bati Plus')
    print(f"Acheteur trouvé: {acheteur.nom}")
except Acheteur.DoesNotExist:
    acheteur = Acheteur.objects.create(nom='Bati Plus')
    print(f"Acheteur créé: {acheteur.nom}")

# Récupérer la devise par défaut (le script utilisera USD ou EUR)
try:
    devise_usd = Devise.objects.get(code='USD')
except Devise.DoesNotExist:
    devise_usd = Devise.objects.first()  # prendre la première devise disponible

print(f"Devise: {devise_usd.code if devise_usd else 'Aucune devise trouvée'}")

# Types de rapports disponibles dans le modèle
LIEN_TYPE_RAPPORT_CHOICE = [
    ("Rapport de solvabilité", "Rapport de solvabilité"),
    ("Rapport complet", "Rapport complet"),
    ("Rapport simplifié", "Rapport simplifié"),
]

# Créer 15 commandes
commandes_created = 0
for i in range(1, 16):
    # Générer des valeurs uniques pour chaque commande
    notre_ref = f"CMD-ACREMAC-{i:03d}"
    reference_client = f"REF-CLIENT-ACREMAC-{i:03d}"
    date_recept = datetime.now().date() - timedelta(days=i)
    date_rapport = date_recept + timedelta(days=7)
    
    # Monnaies et délais
    credit_montant = Decimal(str(5000 + (i * 1000)))
    delai = f"{3 + (i % 5)} jours"
    priorite = ["Basse", "Normale", "Haute", "Urgente"][i % 4]
    
    # Créer la commande
    commande = Commande.objects.create(
        notre_ref=notre_ref,
        reference_client=reference_client,
        date_recept_commande=date_recept,
        date_rapport=date_rapport,
        delais=delai,
        priorite=priorite,
        raison_sociale='Bati Plus',
        type_rapport='Rapport de solvabilité',
        credit_demande=credit_montant,
        devise_credit_demande=devise_usd,
        credit_recommande=credit_montant * Decimal('0.9'),  # 90% du crédit demandé
        devise_credit_recommande=devise_usd,
        numero_adresse=str(10 + i),
        rue_adresse=f"Rue de la Bati {i}",
        code_postale_adresse=f"BP-000{i:02d}",
        telephone=f"+228 2251234{i:02d}",
        email=f"contact-bati-plus-{i}@acremac.tg",
        type_commande='NORMALE',
        type_traitement='MANUEL',
        client_nom='ACREMAC TEST',
        client=client_user,
        acheteur=acheteur,
        status='nouvelle',
        imprimer_avec_etats_fin='Oui',
        company_identification_number=f"CIN-BATI-{i:04d}",
        post_office="Lomé",
    )
    
    commandes_created += 1
    print(f"✓ Commande créée: {commande.notre_ref} | Montant: {commande.credit_demande} {devise_usd.code if devise_usd else 'N/A'} | Acheteur: {acheteur.nom}")

print(f"\n✓ Total: {commandes_created} commandes créées avec succès pour le client acremac_test et l'acheteur Bati plus")
