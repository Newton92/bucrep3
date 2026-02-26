#!/usr/bin/env python
"""
Script pour insérer 15 nouvelles commandes dans la base de données
Client: acremac_test
Acheteur: Bati Plus
"""

import os
import django
from datetime import datetime, timedelta
import random

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bucrep.settings')
django.setup()

from main.models import Commande, User, Acheteur, Devise, Pays, Ville

def insert_commandes():
    # Récupérer le client acremac_test
    try:
        client = User.objects.get(username='acremac_test')
        print(f"✓ Client trouvé: {client.username}")
    except User.DoesNotExist:
        print("✗ Client 'acremac_test' non trouvé")
        return

    # Récupérer l'acheteur Bati Plus
    try:
        acheteur = Acheteur.objects.get(nom='Bati Plus')
        print(f"✓ Acheteur trouvé: {acheteur.nom}")
    except Acheteur.DoesNotExist:
        print("✗ Acheteur 'Bati Plus' non trouvé")
        return

    # Récupérer une devise (XOF par défaut)
    devise = Devise.objects.filter(code='XOF').first()
    if not devise:
        devise = Devise.objects.first()
    print(f"✓ Devise: {devise.code if devise else 'N/A'}")

    # Types de rapports possibles
    types_rapports = ['SOLVABILITE', 'CREDIT', 'FINANCIERE', 'COMMERCIALE']
    priorites = ['Faible', 'Normal', 'Urgent']
    delais = ['3 jours', '5 jours', '7 jours', '1 semaine', '2 semaines']
    
    # Noms d'entreprises variées
    entreprises = [
        'Entreprise Bâtiment Dakar',
        'Construction Plus SARL',
        'Matériaux de Construction Senegal',
        'Bati Services Abidjan',
        'Groupe Immobilier Ouest Africain',
        'Promoteur Immobilier Senegal',
        'Commerce Bâtiment Côte d\'Ivoire',
        'Négoce Construction Ouagadougou',
        'Entreprise BTP Yamoussoukro',
        'Travaux Publics Benin',
        'Chantier et Bâtiment Mali',
        'Constructeur Professionnel Togo',
        'Développement Immobilier Senegal',
        'Infrastructure Plus Niger',
        'Rénovation Bâtiment Conakry',
    ]

    commandes_creees = []
    
    for i in range(15):
        # Dates aléatoires
        date_recept = datetime.now().date() - timedelta(days=random.randint(1, 30))
        date_rapport = date_recept + timedelta(days=random.randint(3, 15))
        
        # Montants aléatoires
        credit_demande = random.randint(1000000, 100000000)
        credit_recommande = int(credit_demande * random.uniform(0.7, 1.0))
        
        # Créer la commande
        commande = Commande(
            notre_ref=f"CMD-2026-{i+1:04d}",
            reference_client=f"REF-ACREMAC-{i+1:03d}",
            date_recept_commande=date_recept,
            date_rapport=date_rapport,
            delais=random.choice(delais),
            priorite=random.choice(priorites),
            raison_sociale=entreprises[i],
            type_rapport=random.choice(types_rapports),
            credit_demande=credit_demande,
            devise_credit_demande=devise,
            credit_recommande=credit_recommande,
            devise_credit_recommande=devise,
            numero_adresse=f'{random.randint(1, 500)}',
            rue_adresse=f'Rue de la Construction {i+1}',
            code_postale_adresse=f'{10000 + random.randint(0, 90000)}',
            telephone=f'+221 77 {random.randint(100, 999)} {random.randint(1000, 9999)}',
            email=f'contact-{i+1}@batiplus.com',
            type_commande='NORMALE',
            type_traitement='MANUEL',
            client_nom='acremac_test',
            client=client,
            acheteur=acheteur,
            company_identification_number=f'TIN-{random.randint(100000000, 999999999)}',
            comments=f'Commande insérée automatiquement {i+1}',
        )
        
        commande.save()
        commandes_creees.append(commande)
        print(f"✓ Commande {i+1}/15 créée: {commande.notre_ref} - {commande.raison_sociale}")

    print(f"\n✓✓✓ {len(commandes_creees)} commandes créées avec succès!")
    return commandes_creees

if __name__ == '__main__':
    insert_commandes()
