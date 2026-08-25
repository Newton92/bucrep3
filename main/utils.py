# utils.py
def _y(years, i):
    """Accès sécurisé à years[i] — retourne None si hors limites."""
    return years[i] if years and i < len(years) else None

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.template.loader import render_to_string

import requests
import requests
from django.db import transaction

        
from django.utils import timezone
from faker import Faker

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Important pour Django
import io
import base64
import numpy as np

from decimal import Decimal
from django.db.models import QuerySet

from django.utils import timezone
from faker import Faker
from django.db.models import Q

from django.db.models import Model
from django.db.models.fields.related import ForeignKey
from decimal import Decimal
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import os
from django.conf import settings

# utils/fix_commandes_emails.py
from django.utils import timezone
import random

from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from main.models import *
from main.models import ActifC, PassifC, ResultatC


# Importez vos classes de Ratios pour chaque type de bilan

# from main.models import *
# from main.models import User
# https://www.geonames.org/activate/rKbZUmb9/yannick1987/

# User = get_user_model()
from django.contrib.auth import get_user_model

def get_user_queryset():
    User = get_user_model()
    return User.objects.all()


def send_email_with_secret_code(
    secret_code, subject, from_email, to_emails, cc_emails=None
):
    try:
        # Créez l'objet du message
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject

        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)
            to_emails += cc_emails  # Ajoutez les emails en copie au destinataire

        # Contenu HTML
        html_content = render_to_string(
            "main/emails/email_with_secret_code.html", {"secret_code": secret_code}
        )
        msg.attach(MIMEText(html_content, "html"))

        # Configurez le serveur SMTP
        smtp_server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        smtp_server.ehlo()  # Initialise la connexion SMTP
        smtp_server.starttls()  # Activez la connexion sécurisée
        smtp_server.ehlo()
        smtp_server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

        # Envoyez l'email
        smtp_server.send_message(msg)
        smtp_server.quit()
        print("Email sent successfully")
        return True

    except Exception as e:
        print(f"Failed to send email. Error: {str(e)}")
        return False


from datetime import timedelta

from django.utils import timezone


def check_and_notify(portefeuille, code_evenement, details_evenement):
    # Vérifier si le portefeuille surveille cet événement
    if portefeuille.elements_surveillance_actifs.filter(
        code_interne=code_evenement
    ).exists():
        # Récupérer la dernière date de notification pour ce portefeuille et cet événement
        # Vous devrez stocker cette information quelque part, par exemple dans un modèle `NotificationLog`
        last_notification = (
            NotificationLog.objects.filter(
                portefeuille=portefeuille, code_evenement=code_evenement
            )
            .order_by("-date_notification")
            .first()
        )

        # Déterminer la prochaine date de notification en fonction de la fréquence
        if last_notification:
            if portefeuille.frequence_alertes == "quotidienne":
                next_notification_date = (
                    last_notification.date_notification + timedelta(days=1)
                )
            elif portefeuille.frequence_alertes == "hebdomadaire":
                next_notification_date = (
                    last_notification.date_notification + timedelta(weeks=1)
                )
            elif portefeuille.frequence_alertes == "mensuelle":
                next_notification_date = (
                    last_notification.date_notification + timedelta(days=30)
                )
        else:
            # Si aucune notification précédente, notifier immédiatement
            next_notification_date = timezone.now() - timedelta(days=1)

        # Vérifier si la date actuelle est supérieure ou égale à la prochaine date de notification
        if timezone.now() >= next_notification_date:
            # Envoyer la notification
            send_notification(portefeuille.client, details_evenement)
            # Enregistrer la notification
            NotificationLog.objects.create(
                portefeuille=portefeuille,
                code_evenement=code_evenement,
                date_notification=timezone.now(),
            )


def send_notification(client, details_evenement):
    # Logique pour envoyer la notification (email, message in-app, etc.)
    print(f"Notifier {client.nom} : {details_evenement}")
    # Creer une Alerte, envoyer un email, etc.


# Supposons une fonction qui est appelée quand la raison sociale d'un acheteur change
def handle_acheteur_raison_sociale_changed(
    acheteur_instance, ancienne_raison_sociale, nouvelle_raison_sociale
):
    code_evenement = "COMPANY_NAME_CHANGE"  # Code de l'ElementSurveillance pertinent

    # Trouver les portefeuilles qui suivent cet acheteur
    portefeuilles_clients_concernes = PortefeuilleClient.objects.filter(
        acheteur=acheteur_instance
    )

    for pc_link in portefeuilles_clients_concernes:
        portefeuille = pc_link.portefeuille
        client_a_notifier = portefeuille.client

        # Vérifier si ce portefeuille surveille ce type d'événement
        if portefeuille.elements_surveillance_actifs.filter(
            code_interne=code_evenement
        ).exists():
            # Logique de notification (email, message in-app, etc.)
            print(
                f"Notifier {client_a_notifier.nom} : L'acheteur {acheteur_instance.nom} a changé de raison sociale de '{ancienne_raison_sociale}' à '{nouvelle_raison_sociale}' dans le portefeuille '{portefeuille.nom}'."
            )
            # Creer une Alerte, envoyer un email, etc.








# 1. Récupérer et insérer les pays
def fetch_and_insert_countries():
    url = "https://restcountries.com/v3.1/all"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lève une erreur si la requête échoue
        countries = response.json()
        for country in countries:
            try:
                Pays.objects.update_or_create(
                    code=country['cca2'],
                    defaults={
                        'nom': country['name']['common'],
                        'afficher_au_dashboard': True,
                        'is_active': True
                    }
                )
            except KeyError as e:
                print(f"Erreur de clé pour le pays : {e}")
        print("Pays insérés avec succès !")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des pays : {e}")

# 2. Récupérer et insérer les provinces et villes pour un pays donné
def fetch_and_insert_provinces_and_cities_for_country(pays):
    username = "yannick1987"
    # Trouver l'ID GeoNames du pays (ex: 3017382 pour la France)
    # Vous pouvez utiliser une fonction pour rechercher cet ID ou le mapper manuellement.
    geoname_id = 3017382  # À remplacer par une recherche dynamique si nécessaire
    url = f"http://api.geonames.org/childrenJSON?geonameId={geoname_id}&username={username}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        regions = response.json().get('geonames', [])
        for region in regions:
            try:
                province, _ = Province.objects.update_or_create(
                    code=region['geonameId'],
                    defaults={
                        'nom': region['name'],
                        'pays': pays,
                        'is_active': True
                    }
                )
                # Récupérer les villes de cette province
                fetch_and_insert_cities(province, username)
            except KeyError as e:
                print(f"Erreur de clé pour la province {region.get('name')} : {e}")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des provinces pour {pays.nom} : {e}")

# 3. Récupérer et insérer les villes pour une province donnée
def fetch_and_insert_cities(province, username):
    url = f"http://api.geonames.org/childrenJSON?geonameId={province.code}&username={username}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        cities = response.json().get('geonames', [])
        for city in cities:
            try:
                Ville.objects.update_or_create(
                    code=city['geonameId'],
                    defaults={
                        'nom': city['name'],
                        'province': province,
                        'is_active': True
                    }
                )
            except KeyError as e:
                print(f"Erreur de clé pour la ville {city.get('name')} : {e}")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des villes pour {province.nom} : {e}")

# 4. Fonction principale pour tout remplir
@transaction.atomic
def populate_database():
    # 1. Insérer les pays
    fetch_and_insert_countries()
    # 2. Pour chaque pays, insérer les provinces et villes
    for pays in Pays.objects.all():
        print(f"Traitement des provinces et villes pour {pays.nom}...")
        fetch_and_insert_provinces_and_cities_for_country(pays)
    print("Base de données remplie avec succès !")

# Exécution
# if __name__ == "__main__":
#    populate_database()




def create_fake_commands(count=15):
    fake = Faker('fr_FR')

    # Récupérer les objets de la base de données une seule fois avant la boucle
    acheteurs = list(Acheteur.objects.all())
    clients = list(User.objects.filter(Q(role__icontains="Client") | Q(role__icontains="client")))
    villes = list(Ville.objects.all())
    pays_list = list(Pays.objects.all()) # ✅ Liste des pays récupérée en une seule fois
    devises = list(Devise.objects.all())
    modeles_rapport = list(ModeleRapport.objects.all())

    # Vérification que les tables contiennent des données
    if not all([acheteurs, clients, villes, pays_list, devises, modeles_rapport]):
        print("Erreur: Certaines tables ne contiennent pas de données pour la création de commandes factices.")
        return

    for _ in range(count):
        # Sélection aléatoire des objets depuis les listes
        acheteur = random.choice(acheteurs)
        client = random.choice(clients)
        ville = random.choice(villes)
        pays = random.choice(pays_list) # ✅ Sélection aléatoire depuis la liste
        devise = random.choice(devises)
        modele_rapport = random.choice(modeles_rapport)

        # Création de la commande
        Commande.objects.create(
            notre_ref=fake.unique.bothify(text='CMD-#####'),
            reference_client=fake.unique.bothify(text='CLT-#####'),
            date_recept_commande=fake.date_between(start_date='-30d', end_date='today'),
            date_rapport=fake.date_between(start_date='today', end_date='+30d'),
            delais=fake.random_element(elements=('3 jours', '1 semaine', '2 semaines', '1 mois')),
            priorite=fake.random_element(elements=('Faible', 'Moyenne', 'Haute', 'Urgent')),
            raison_sociale=acheteur.nom,
            type_rapport=fake.random_element(elements=('Rapport de crédit', 'Rapport financier', 'Rapport de conformité')),
            ref_type_rapport=modele_rapport,
            credit_demande=round(random.uniform(1000, 100000), 2),
            devise_credit_demande=devise,
            credit_recommande=round(random.uniform(1000, 100000), 2),
            devise_credit_recommande=devise,
            numero_adresse=fake.building_number(),
            rue_adresse=fake.street_name(),
            code_postale_adresse=fake.postcode(),
            telephone=fake.phone_number(),
            email=fake.email(),
            pays=pays,
            ville=ville,
            client=client,
            acheteur=acheteur,
            status=fake.random_element(elements=('nouvelle', 'en_cours', 'rapport_soumis', 'rapport_valide', 'envoye_client', 'terminee', 'annulee'))
        )
        
        
        
        
        


def create_fake_buyers(count=15):
    """
    Creates a specified number of fake Acheteur objects with realistic-looking data.
    
    Args:
        count (int): The number of fake buyers to create.
    """
    fake = Faker('fr_FR')

    # Fetch all related objects once to avoid multiple database queries inside the loop.
    try:
        categories = list(CategorieEntreprise.objects.all())
        formes_juridiques = list(FormeJuridique.objects.all())
        statuts = list(StatutEntreprise.objects.all())
        pays = list(Pays.objects.all())
        provinces = list(Province.objects.all())
        villes = list(Ville.objects.all())
        couleurs = list(CouleurCommentaire.objects.all())
    except Exception as e:
        print(f"Error fetching related objects: {e}. Ensure all these tables are populated.")
        return

    # Check that the related tables are not empty
    if not all([categories, formes_juridiques, statuts, pays, provinces, villes, couleurs]):
        print("Warning: One or more related tables (e.g., CategorieEntreprise, Pays) are empty. Cannot create fake buyers.")
        return

    for i in range(count):
        # Generate a unique company name to prevent IntegrityError
        company_name = fake.unique.company()
        while Acheteur.objects.filter(nom=company_name).exists():
            company_name = fake.unique.company()

        # Select a random object for each foreign key
        selected_categorie = random.choice(categories)
        selected_forme_juridique = random.choice(formes_juridiques)
        selected_statut = random.choice(statuts)
        selected_pays = random.choice(pays)
        selected_province = random.choice(provinces)
        selected_ville = random.choice(villes)
        selected_couleur = random.choice(couleurs)
        
        # Create the Acheteur object
        Acheteur.objects.create(
            code=fake.unique.bothify(text='BUY-#####'),
            categorie_entreprise=selected_categorie,
            forme_juridique=selected_forme_juridique,
            activite_principale=fake.job(),
            nom=company_name,
            sigle=fake.company_suffix(),
            description=fake.text(max_nb_chars=200),
            date_creation=fake.date_of_birth(minimum_age=1, maximum_age=40),
            statut_entreprise=selected_statut,
            code_postal=fake.postcode(),
            fax=fake.phone_number(),
            boite_postale=fake.postcode(),
            email=fake.unique.email(),
            site_internet=fake.url(),
            numero_adresse=fake.building_number(),
            rue_adresse=fake.street_name(),
            pays=selected_pays,
            province=selected_province,
            ville=selected_ville,
            couleur_commentaire=selected_couleur,
            commentaire=fake.sentence(),
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )

    print(f"{count} fake Acheteur objects created successfully.")






def generate_chart_image(charts_data):  # charts_data au lieu de chart_data
    """Génère une image PNG à partir des données du chart"""
    plt.figure(figsize=(10, 6))
    
    labels = charts_data['labels']  # charts_data au lieu de chart_data
    datasets = charts_data.get('datasets', [])

    # ensure ascending order by year label
    try:
        order = sorted(range(len(labels)), key=lambda i: int(labels[i]))
        labels = [labels[i] for i in order]
        datasets = [
            {**ds, 'data': [ds['data'][i] for i in order]}
            for ds in datasets
        ]
    except Exception:
        pass

    x = np.arange(len(labels))
    chart_type = charts_data.get('chart_type', 'line')
    
    # Créer le graphique selon le type
    if chart_type in ('line',):
        for i, dataset in enumerate(datasets):  # charts_data au lieu de chart_data
            plt.plot(labels, dataset['data'], label=dataset['label'], 
                    marker='o', linewidth=2, markersize=6)
    else:
        # default to bar/histogramme
        width = 0.8 / max(1, len(datasets))
        for i, dataset in enumerate(datasets):
            plt.bar(x + i * width, dataset['data'], width=width, label=dataset['label'])
        plt.xticks(x + width * (len(datasets)-1) / 2, labels)

    plt.title(charts_data.get('title', ''), fontsize=14, fontweight='bold')  # charts_data au lieu de chart_data
    plt.xlabel('Années')
    plt.ylabel('Valeurs')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Convertir en image base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    return base64.b64encode(image_png).decode('utf-8')
    
    
# utils/financial_report_generator.py



# Fonction utilitaire pour calculer les variations
def calculate_variation(n, n_minus_1):
    """Calcule la variation en pourcentage entre deux valeurs."""
    if n is None or n_minus_1 is None:
        return "N/A"

    if n_minus_1 == 0:
        return "+Inf" if n > 0 else "0.00%" if n == 0 else "-Inf"

    variation = ((n - n_minus_1) / abs(n_minus_1)) * 100
    return f"{variation:.2f}%"





class FinancialReportGenerator:
    """
    Génère les données financières pour le rapport de solvabilité en fonction
    du type de bilan et de l'acheteur.
    """
    def __init__(self, acheteur, bilan_type):
        self.acheteur = acheteur
        self.bilan_type = bilan_type
        self.years_to_retrieve = [
            datetime.now().year,
            datetime.now().year - 1,
            datetime.now().year - 2
        ]
        self.models_map = self._get_models_map()

    def _get_models_map(self):
        """
        Associe le type de bilan aux modèles Django correspondants.
        """
        mapping = {
            'Anglais': {
                'Actif': ActifA,
                'Passif': PassifA,
                'Resultat': ResultatA,
                'Ratios': RatiosAnglais
            },
            'Classique': {
                'Actif': ActifC,
                'Passif': PassifC,
                'Resultat': ResultatC,
                'Ratios': RatiosClassique
            },
            'Bancaire': {
                'Actif': Assets,
                'Passif': Liabilities,
                'Resultat': Products,
                'Depenses': Expenses,
                'HorsBilan': OffBalanceSheet,
                'Ratios': None, # Vous devrez créer cette classe
            },
            'Syscohada': {
                'Actif': ActifS,
                'Passif': PassifS,
                'Resultat': ResultatS,
                'Ratios': RatiosSyscohada
            },
            'IRFS COBAC': {
                'Actif': ActifIFRS,
                'Passif': PassifIFRS,
                'Resultat': ResultatIFRS,
                'Ratios': RatiosIFRS
            }
        }
        return mapping.get(self.bilan_type, None)

    def _get_model_data_by_year(self, model_name):
        """
        Récupère les données d'un modèle pour les 3 dernières années.
        """
        if not self.models_map:
            return None
            
        ModelClass = self.models_map.get(model_name)
        if not ModelClass:
            return None
            
        data = {}
        for year in self.years_to_retrieve:
            try:
                # Utilise select_related pour optimiser la requête si l'année est une FK
                instance = ModelClass.objects.filter(
                    acheteur=self.acheteur,
                    annee__annee=year
                ).select_related('annee').first()
                if instance:
                    data[year] = instance
            except Exception as e:
                print(f"Erreur de récupération des données pour {ModelClass.__name__} en {year}: {e}")
                data[year] = None
        return data

    def get_structured_data(self):
        """
        Génère les tableaux structurés pour les états financiers et les ratios.
        """
        if not self.models_map:
            return {
                'error': f"Type de bilan '{self.bilan_type}' non supporté."
            }

        financial_data = {}
        for model_name, ModelClass in self.models_map.items():
            if 'Ratios' in model_name:
                continue
            financial_data[model_name] = self._get_model_data_by_year(model_name)

        result = {
            'actif_table': self._build_table_data(financial_data.get('Actif')),
            'passif_table': self._build_table_data(financial_data.get('Passif')),
            'resultat_table': self._build_table_data(financial_data.get('Resultat')),
            'ratios_table': self._build_ratios_table(financial_data)
        }
        
        return result

    def _build_table_data(self, data_by_year):
        """
        Construit le tableau de données pour l'actif, le passif ou le résultat.
        """
        if not data_by_year or not any(data_by_year.values()):
            return None

        years = self.years_to_retrieve
        
        # Récupérer les champs du premier modèle disponible
        first_instance = next( (instance for instance in data_by_year.values() if instance is not None), None)
        if not first_instance:
            return None
        
        # Récupère tous les champs du modèle (sauf les champs de suivi et les FK)
        fields = [
            field.name for field in first_instance._meta.get_fields() 
            if not isinstance(field, (ForeignKey)) and field.name not in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
        ]

        table_data = []
        for field_name in fields:
            row = {'label': first_instance._meta.get_field(field_name).verbose_name}
            # Récupérer les valeurs pour l'année N, N-1, N-2
            val_n = getattr(data_by_year.get(_y(years, 0)), field_name, None)
            val_n_minus_1 = getattr(data_by_year.get(_y(years, 1)), field_name, None)
            val_n_minus_2 = getattr(data_by_year.get(_y(years, 2)), field_name, None)
            
            row['val_n'] = val_n if val_n is not None else "N/A"
            row['val_n_minus_1'] = val_n_minus_1 if val_n_minus_1 is not None else "N/A"
            row['val_n_minus_2'] = val_n_minus_2 if val_n_minus_2 is not None else "N/A"
            
            # Calculer les variations
            row['var_n_vs_n_minus_1'] = calculate_variation(val_n, val_n_minus_1)
            row['var_n_minus_1_vs_n_minus_2'] = calculate_variation(val_n_minus_1, val_n_minus_2)
            
            table_data.append(row)
        
        return table_data

    def _build_ratios_table(self, financial_data):
        """
        Construit le tableau des ratios financiers en utilisant la classe Ratios dédiée.
        """
        RatiosClass = self.models_map.get('Ratios')
        if not RatiosClass or not financial_data.get('Actif') or not financial_data.get('Passif') or not financial_data.get('Resultat'):
            return None # Aucune classe de ratios ou données de base

        years = self.years_to_retrieve
        ratios_data = {}
        
        # Obtenir une instance des ratios pour chaque année
        for year in years:
            actif_instance = financial_data.get('Actif').get(year)
            passif_instance = financial_data.get('Passif').get(year)
            resultat_instance = financial_data.get('Resultat').get(year)
            
            # Vérifier que toutes les données sont disponibles pour l'année
            if actif_instance and passif_instance and resultat_instance:
                # Instancier la classe de ratios avec les objets de l'année
                ratios_data[year] = RatiosClass(actif_instance, passif_instance, resultat_instance)
            else:
                ratios_data[year] = None
        
        # Construire le tableau de présentation
        table_data = []
        # On suppose que tous les RatiosClass ont les mêmes propriétés de calcul
        if RatiosClass:
            # Récupérer les noms des propriétés (ratios)
            ratio_properties = [prop for prop in dir(RatiosClass) if not prop.startswith('_') and isinstance(getattr(RatiosClass, prop), property)]
            
            for ratio_name in ratio_properties:
                row = {'label': ratio_name.replace('_', ' ').title()}
                val_n = getattr(ratios_data.get(_y(years, 0)), ratio_name, None) if ratios_data.get(_y(years, 0)) else None
                val_n_minus_1 = getattr(ratios_data.get(_y(years, 1)), ratio_name, None) if ratios_data.get(_y(years, 1)) else None
                val_n_minus_2 = getattr(ratios_data.get(_y(years, 2)), ratio_name, None) if ratios_data.get(_y(years, 2)) else None
                
                row['val_n'] = f"{val_n:.2f}" if isinstance(val_n, (Decimal, float)) else "N/A"
                row['val_n_minus_1'] = f"{val_n_minus_1:.2f}" if isinstance(val_n_minus_1, (Decimal, float)) else "N/A"
                row['val_n_minus_2'] = f"{val_n_minus_2:.2f}" if isinstance(val_n_minus_2, (Decimal, float)) else "N/A"
                
                row['var_n_vs_n_minus_1'] = calculate_variation(val_n, val_n_minus_1)
                row['var_n_minus_1_vs_n_minus_2'] = calculate_variation(val_n_minus_1, val_n_minus_2)
                
                table_data.append(row)
                
        return table_data
    
    
    
    
    
    
    
    
    





class AcremacScoring:
    def __init__(self, acheteur, bilan_type, annee_cible=None):
        self.acheteur = acheteur
        # FIX : Normaliser le type de bilan pour qu'il corresponde à la clé du dictionnaire
        # avant de l'utiliser.
        self.bilan_type = bilan_type.capitalize()
        self.annee_cible = annee_cible if annee_cible is not None else datetime.now().year
        
        # Mapping des classes de ratios
        self.ratios_map = {
            'Anglais': RatiosAnglais,
            'Syscohada': RatiosSyscohada,
            'Classique': RatiosClassique,
            'IRFS COBAC': RatiosIFRS,
        }
        
        # Le reste du code reste inchangé, mais maintenant self.bilan_type est correct.
        self.models_map = self._get_models_map()

    def _get_models_map(self):
        """
        Associe le type de bilan aux modèles Django correspondants.
        """
        mapping = {
            'Anglais': {
                'Actif': ActifA, 'Passif': PassifA, 'Resultat': ResultatA,
            },
            'Classique': {
                'Actif': ActifC, 'Passif': PassifC, 'Resultat': ResultatC,
            },
            'Bancaire': {
                'Actif': Assets, 'Passif': Liabilities, 'Resultat': Products,
                'Depenses': Expenses, 'HorsBilan': OffBalanceSheet,
            },
            'Syscohada': {
                'Actif': ActifS, 'Passif': PassifS, 'Resultat': ResultatS,
            },
            'IRFS COBAC': {
                'Actif': ActifIFRS, 'Passif': PassifIFRS, 'Resultat': ResultatIFRS,
            }
        }
        # FIX : L'appel à get() est maintenant sûr car self.bilan_type a été normalisé.
        return mapping.get(self.bilan_type, None)
    
    def _get_financial_data(self, year):
        """Récupère les instances des modèles financiers pour une année donnée."""
        models = self.models_map
        
        # Cette vérification est maintenant redondante, mais la rend plus robuste.
        if models is None:
            return None
        
        data = {}
        for model_name, ModelClass in models.items():
            instance = ModelClass.objects.filter(acheteur=self.acheteur, annee__annee=year).first()
            if instance:
                data[model_name] = instance
            else:
                return None  # Retourne None si les données de base sont manquantes
        return data
    def _get_limited_ratio(self, value, lower_bound, upper_bound):
        """
        Applique les bornes pour limiter la valeur d'un ratio.
        """
        if value is None:
            return 0
        if value < lower_bound:
            return Decimal(str(lower_bound))
        if value > upper_bound:
            return Decimal(str(upper_bound))
        return Decimal(str(value))


    # --- Algorithme de SCORING AVEC BILAN ---
    def calculate_score_with_bilan(self):
        """
        Calcule le score de défaillance ACREMAC en utilisant les ratios financiers.
        """
        RatiosClass = self.ratios_map.get(self.bilan_type)
        if not RatiosClass:
            return None, "Scoring avec bilan non disponible pour ce type."
            
        financial_data = self._get_financial_data(self.annee_cible)
        if not financial_data:
            return None, "Données financières manquantes pour le calcul."
        
        try:
            ratios_instance = RatiosClass(
                actif=financial_data.get('Actif'),
                passif=financial_data.get('Passif'),
                resultat=financial_data.get('Resultat'),
            )
        except Exception as e:
            return None, f"Erreur lors de l'instanciation des ratios: {e}"
        
        
        # Définir les coefficients et les bornes en fonction du type de bilan
        if self.bilan_type == 'Anglais':
            # Ratios et coefficients pour le scoring Anglais
            scoring_elements = [
                {'ratio_name': 'solvabilite', 'coeff': Decimal('0.0535'), 'bounds': {'lower': 0, 'upper': 100}}, # Exemple
                # Ajouter tous les autres ratios ici...
            ]
            constant = Decimal('0.57')
            # ... Ajoutez la logique pour les autres types de bilans ...
        elif self.bilan_type == 'Syscohada':
            # Ratios et coefficients pour le scoring SYSCOHADA
            scoring_elements = [
                {'ratio_name': 'fonds_de_roulement', 'coeff': Decimal('0.0096'), 'bounds': {'lower': -100, 'upper': 150}},
                # ...
            ]
            constant = Decimal('0.57')
        elif self.bilan_type == 'Classique':
            # Ratios et coefficients pour le scoring CLASSIQUE
            scoring_elements = [
                {'ratio_name': 'rendement_capitaux_propres', 'coeff': Decimal('0.0371'), 'bounds': {'lower': -25, 'upper': 100}},
                # ...
            ]
            constant = Decimal('0.57')
        elif self.bilan_type == 'IRFS COBAC':
            # Ratios et coefficients pour le scoring IFRS COBAC
            scoring_elements = [
                {'ratio_name': 'roe', 'coeff': Decimal('0.0371'), 'bounds': {'lower': -25, 'upper': 100}},
                # ...
            ]
            constant = Decimal('0.57')
        else:
            return None, "Type de bilan non pris en charge pour le scoring avec bilan."
        
        score_value = constant
        
        # Calcul de la contribution de chaque ratio
        score_details = []
        for element in scoring_elements:
            ratio_value = getattr(ratios_instance, element['ratio_name'], None)
            
            # Application des bornes
            limited_ratio = self._get_limited_ratio(
                ratio_value,
                element['bounds']['lower'],
                element['bounds']['upper']
            )
            
            contribution = element['coeff'] * limited_ratio
            score_value += contribution
            
            score_details.append({
                'label': element['ratio_name'].replace('_', ' ').title(),
                'value': ratio_value,
                'limited_value': limited_ratio,
                'coefficient': element['coeff'],
                'contribution': contribution
            })
        
        return {
            'score': score_value,
            'details': score_details
        }, None
        
    # --- Algorithme de SCORING SANS BILAN ---
    def calculate_score_without_bilan(self):
        """
        Calcule le score de défaillance ACREMAC sans données financières.
        """
        score_value = Decimal('0')
        details = []

        # S1: Les locaux
        premises = self.acheteur.localisation.locaux if self.acheteur.localisation else None
        grid_premises = {'Propriétaire': 1, 'Locataire': 0.5, 'Sous-locataire': 0}
        score_value += Decimal(str(grid_premises.get(premises, 0)))
        details.append({'critere': 'Locaux', 'valeur': premises, 'grille': grid_premises.get(premises, 0)})

        # S2: Forme juridique
        legal_form = self.acheteur.forme_juridique.libelle if self.acheteur.forme_juridique else None
        grid_legal_form = {'Société anonyme': 1, 'Limitée/SARL': 0.75, 'Entreprise individuelle(EI)': 0.05}
        score_value += Decimal(str(grid_legal_form.get(legal_form, 0)))
        details.append({'critere': 'Forme juridique', 'valeur': legal_form, 'grille': grid_legal_form.get(legal_form, 0)})
        
        # S3: Age de l'entreprise
        age = (datetime.now().year - self.acheteur.date_creation.year) if self.acheteur.date_creation else 0
        grid_age = {range(0, 2): 0.1, range(2, 4): 0.2, range(4, 6): 0.4, range(6, 8): 0.6, range(8, 10): 0.8, range(10, 100): 1}
        score_age = 0
        for r, val in grid_age.items():
            if age in r:
                score_age = val
                break
        score_value += Decimal(str(score_age))
        details.append({'critere': 'Age de l\'entreprise', 'valeur': f"{age} ans", 'grille': score_age})

        # S4: Comportement de paiement
        # Récupérer le comportement de paiement depuis votre modèle `ConditionDeVente`
        payment_behavior = self.acheteur.conditiondevente.comportement_de_paiement_ref.libelle if self.acheteur.conditiondevente and self.acheteur.conditiondevente.comportement_de_paiement_ref else None
        grid_payment = {'À l\'avance': 1, 'Dans les délais': 0.5, 'En retard': 0.25, 'Mauvais payeur': -1, 'Inconnu': 0}
        score_value += Decimal(str(grid_payment.get(payment_behavior, 0)))
        details.append({'critere': 'Comportement de paiement', 'valeur': payment_behavior, 'grille': grid_payment.get(payment_behavior, 0)})

        # S5: Avis commercial
        commercial_opinion = self.acheteur.tendance.avis_commercial_ref.libelle if self.acheteur.tendance and self.acheteur.tendance.avis_commercial_ref else None
        grid_commercial = {'Très bonne': 0.75, 'Bon': 0.5, 'Moyen': 0.25, 'Négatif': 0}
        score_value += Decimal(str(grid_commercial.get(commercial_opinion, 0)))
        details.append({'critere': 'Avis commercial', 'valeur': commercial_opinion, 'grille': grid_commercial.get(commercial_opinion, 0)})
        
        # S6: Code NACE
        # On suppose que les codes NACE sont stockés dans un champ ManyToMany
        # Et qu'il faut trouver une correspondance pour le score
        nace_codes_str = ', '.join([c.code for c in self.acheteur.codenaceacheteur_set.all()])
        grid_nace = {'Manufacture': 0.75, 'Commerce de gros': 0.5, 'Services': 0.5}
        # Ceci est une simplification, la logique réelle devrait être plus complexe
        score_nace = 0
        for nace, val in grid_nace.items():
            if nace in nace_codes_str: # Vérifie si le mot clé est dans la chaîne des codes
                score_nace = val
                break
        score_value += Decimal(str(score_nace))
        details.append({'critere': 'Code NACE', 'valeur': nace_codes_str, 'grille': score_nace})

        return {'score': score_value, 'details': details}, None

    def get_score_interpretation(self, score):
        """Traduit un score numérique en un niveau de risque textuel."""
        # Basé sur la grille de "probabilité de défaillance"
        # Ajuster les bornes si nécessaire
        if score <= -4.01:
            return "Risque très élevé (>17,7% de probabilité de défaillance)"
        elif -4.01 < score <= -2.57:
            return "Risque élevé (probabilité de défaillance >10%)"
        elif -2.57 < score <= -1.00:
            return "Risque élevé (probabilité de défaillance >3%)"
        # ... Définir les autres bornes ...
        else:
            return "Risque faible (probabilité de défaillance <1%)"
            
    # Méthode principale
    def get_final_score(self):
        """
        Détermine et calcule le score final en fonction de la disponibilité des données.
        """
        # Tenter d'obtenir les données financières
        data_available = self._get_financial_data(self.annee_cible) is not None
        
        if data_available:
            score_data, error = self.calculate_score_with_bilan()
            if not error:
                score = score_data['score']
                score_type = "avec bilan"
            else:
                score = None
                score_type = None
        else:
            score_data, error = self.calculate_score_without_bilan()
            if not error:
                score = score_data['score']
                score_type = "sans bilan"
            else:
                score = None
                score_type = None

        if score is not None:
            score = round(score, 2)
            interpretation = self.get_score_interpretation(score)
        else:
            interpretation = "Impossible de calculer le score. Données manquantes."
            
        return {
            'value': score,
            'type': score_type,
            'interpretation': interpretation
        }
        
        
        
        
        
        
        
from decimal import Decimal

# ... (Votre classe AcremacScoring existante) ...

def calculate_score_with_bilan_classique(self):
    """
    Calcule le score de défaillance ACREMAC Classique en utilisant les ratios financiers.
    """
    # ... (Code de récupération des données financières) ...
    # Le code de récupération des données reste le même.
    
    # Définition des coefficients et des bornes pour le scoring classique
    constant = Decimal('0.57')
    scoring_elements = [
        {'ratio_name': 'r1_frais_financiers_ebe', 'coeff': Decimal('0.0535'), 'bounds': {'lower': 0, 'upper': 100}},
        {'ratio_name': 'r2_creances_debiteurs', 'coeff': Decimal('0.0115'), 'bounds': {'lower': 0, 'upper': 200}},
        {'ratio_name': 'r3_capitaux_permanents_passif', 'coeff': Decimal('0.0371'), 'bounds': {'lower': -25, 'upper': 100}},
        {'ratio_name': 'r4_va_ac', 'coeff': Decimal('0.0246'), 'bounds': {'lower': 0, 'upper': 100}},
        {'ratio_name': 'r5_tresorerie_ventes', 'coeff': Decimal('0.0115'), 'bounds': {'lower': -100, 'upper': 100}},
        {'ratio_name': 'r6_fonds_de_roulement_ca', 'coeff': Decimal('0.0096'), 'bounds': {'lower': -100, 'upper': 150}},
    ]
    
    score_value = constant
    score_details = []
    
    # ... (Code pour la boucle de calcul) ...
    # Le reste de la fonction de calcul des contributions est le même que précédemment.

    return {
        'score': score_value,
        'details': score_details
    }, None
    
    
    
    
    
    
    
from decimal import Decimal

# ... (Votre classe AcremacScoring existante) ...

def calculate_score_without_bilan_classique(self):
    """
    Calcule le score de défaillance ACREMAC Classique sans données financières.
    """
    score_value = Decimal('0')
    details = []

    # S1: Les locaux
    premises = self.acheteur.localisation.locaux if self.acheteur.localisation else None
    grid_premises = {
        'Propriétaire': 1, 'Locataire': 0.5, 'Sous-locataire': 0,
        'Autres (Baux)': 0.1, 'Sans locaux': 0.1
    }
    score_value += Decimal(str(grid_premises.get(premises, 0)))
    details.append({'critere': 'Locaux', 'valeur': premises, 'grille': grid_premises.get(premises, 0)})

    # S2: Forme juridique
    legal_form = self.acheteur.forme_juridique.libelle if self.acheteur.forme_juridique else None
    # Liste complète des formes juridiques et leurs scores
    grid_legal_form = {
        'Société anonyme (SA)': 1, 'Société anonyme (SA) unipersonnelle': 1,
        'Société à responsabilité limitée (SARL)': 0.75, 'SARL unipersonnelle': 0.75,
        'Société en commandite par actions (SCA)': 0.75,
        'Société en nom collectif (SNC)': 0.5,
        'Entreprise individuelle (EI)': 0.05,
        # ... (ajoutez toutes les autres formes du tableau excel) ...
    }
    score_value += Decimal(str(grid_legal_form.get(legal_form, 0)))
    details.append({'critere': 'Forme juridique', 'valeur': legal_form, 'grille': grid_legal_form.get(legal_form, 0)})

    # S3: Age de la société
    age = (datetime.now().year - self.acheteur.date_creation.year) if self.acheteur.date_creation else 0
    grid_age = {
        range(0, 2): 0.1, range(2, 4): 0.2, range(4, 6): 0.4, range(6, 8): 0.6,
        range(8, 10): 0.8, range(10, 100): 1
    }
    score_age = 0
    for r, val in grid_age.items():
        if age in r:
            score_age = val
            break
    score_value += Decimal(str(score_age))
    details.append({'critere': 'Age de la société', 'valeur': f"{age} ans", 'grille': score_age})

    # S4: Comportement de paiement
    payment_behavior = self.acheteur.conditiondevente.comportement_de_paiement_ref.libelle if self.acheteur.conditiondevente and self.acheteur.conditiondevente.comportement_de_paiement_ref else None
    grid_payment = {'A l\'avance': 1, 'En temps': 0.5, 'En retard': -0.15, 'Inconnu': 0, 'Plainte isolée': -0.25}
    score_value += Decimal(str(grid_payment.get(payment_behavior, 0)))
    details.append({'critere': 'Comportement de paiement', 'valeur': payment_behavior, 'grille': grid_payment.get(payment_behavior, 0)})

    # S5: Avis commercial
    commercial_opinion = self.acheteur.tendance.avis_commercial_ref.libelle if self.acheteur.tendance and self.acheteur.tendance.avis_commercial_ref else None
    grid_commercial = {
        'Développement commercial très positif': 1, 'Développement commercial positif': 0.75,
        'Développement commercial neutre': 0.5, 'Développement commercial acceptable': 0.3,
        'Développement commercial en dent de scie': 0.1, 'Développement commercial en déclin': -1
    }
    score_value += Decimal(str(grid_commercial.get(commercial_opinion, 0)))
    details.append({'critere': 'Avis commercial', 'valeur': commercial_opinion, 'grille': grid_commercial.get(commercial_opinion, 0)})
    
    # S6: Code NACE
    nace_codes_list = [c.code for c in self.acheteur.codenaceacheteur_set.all()]
    # Il est essentiel de mapper les codes NACE aux scores. Je fournis un exemple, vous devez compléter la liste.
    grid_nace = {'01': 1, '02': 0.75, '10': 0.5, '11': 0.5, '12': 0.5}
    score_nace = 0
    for code in nace_codes_list:
        score_nace = grid_nace.get(code, 0)
        if score_nace > 0: # on prend le premier code NACE pertinent
            break
    score_value += Decimal(str(score_nace))
    details.append({'critere': 'Code NACE', 'valeur': nace_codes_list, 'grille': score_nace})

    return {'score': score_value, 'details': details}, None






# Bilan classique(Annee N, N-1 et N-2)
# Fichier : views_report.py
# ... (les importations existantes) ...

def get_simple_actifs_data(acheteur, years):
    """
    Récupère les actifs pour les années données et les structure pour le template.
    """
    actif_model = ActifC
    data_by_year = {}
    for year in years:
        instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance

    print(
        "[DEBUG][UTILS][get_simple_actifs_data] "
        f"acheteur_id={getattr(acheteur, 'id', None)} years={years} "
        f"presence_by_year={{"
        + ", ".join([f"{y}:{'OK' if data_by_year.get(y) else 'None'}" for y in years])
        + "}}"
    )

    # Définir les champs que vous voulez afficher, dans l'ordre
    fields_to_display = [
        {'label': "Capital sousc. non app", 'key': 'capital_souscrit_non_app'},
        {'label': "Frais recherche développement", 'key': 'frais_recherche_developpement'},
        {'label': "Brevet licence logiciels", 'key': 'brevet_licence_logiciels'},
        # ... Ajoutez tous les autres champs que vous voulez afficher ici
        {'label': "Terrains", 'key': 'terrains'},
        {'label': "Constructions", 'key': 'constructions'},
        {'label': "Materiels et outils", 'key': 'materiels_et_outils'},
        # ... etc.
    ]

    table_data = []
    for field_info in fields_to_display:
        row = {'label': field_info['label']}
        values = {}
        for year in years:
            value = getattr(data_by_year.get(year), field_info['key'], None)
            values[year] = value
        
        # Calcul des variations et formatage pour l'affichage
        # Année N vs N-1
        val_n = values.get(_y(years, 0))
        val_n_moins_1 = values.get(_y(years, 1))
        var_n_vs_n_moins_1 = calculate_variation(val_n, val_n_moins_1)
        
        # Année N-1 vs N-2
        val_n_moins_2 = values.get(_y(years, 2))
        var_n_moins_1_vs_n_moins_2 = calculate_variation(val_n_moins_1, val_n_moins_2)
        
        row['values'] = {
            'n': val_n,
            'n_moins_1': val_n_moins_1,
            'n_moins_2': val_n_moins_2,
        }
        row['variations'] = {
            'n_vs_n_moins_1': var_n_vs_n_moins_1,
            'n_moins_1_vs_n_moins_2': var_n_moins_1_vs_n_moins_2,
        }
        table_data.append(row)
    
    print(
        "[DEBUG][UTILS][get_simple_actifs_data] "
        f"rows={len(table_data)} "
        f"non_null_n={sum(1 for r in table_data if r.get('values', {}).get('n') is not None)} "
        f"non_null_n1={sum(1 for r in table_data if r.get('values', {}).get('n_moins_1') is not None)} "
        f"non_null_n2={sum(1 for r in table_data if r.get('values', {}).get('n_moins_2') is not None)}"
    )

    return table_data



def get_structured_actif_data(acheteur, years):
    """
    Récupère les données d'actifs, les structure par groupe
    et calcule les totaux intermédiaires et généraux.
    """
    actif_model = ActifC
    data_by_year = {}
    for year in years:
        instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance
        
    test_actif_2025 = ActifC.objects.filter(acheteur__id=1, annee__annee="2025")
    print("[DEBUG][CLASSIQUE][2026] "f"actifs={test_actif_2025}")

    print(
        "[DEBUG][UTILS][get_structured_actif_data] "
        f"acheteur_id={getattr(acheteur, 'id', None)} years={years} "
        f"presence_by_year={{"
        + ", ".join([f"{y}:{'OK' if data_by_year.get(y) else 'None'}" for y in years])
        + "}}"
    )

    # Définir la structure hiérarchique pour l'affichage des actifs
    # Chaque 'key' correspond à un champ ou une propriété calculée du modèle ActifC.
    structure_map = {
        "ACTIF IMMOBILISÉ": [
            {'label': "Capital souscrit non appelé", 'key': 'capital_souscrit_non_app'},
            {'label': "Frais de recherche et développement", 'key': 'frais_recherche_developpement'},
            {'label': "Brevets, licences, logiciels", 'key': 'brevet_licence_logiciels'},
            {'label': "Fonds commercial", 'key': 'fonds_commercial'},
            {'label': "Autres immobilisations incorporelles", 'key': 'autres_immobilisations_incorporelles'},
            {'label': "Terrains", 'key': 'terrains'},
            {'label': "Constructions", 'key': 'constructions'},
            {'label': "Matériels et outils", 'key': 'materiels_et_outils'},
            {'label': "Matériel de transport", 'key': 'materiel_de_transport'},
            {'label': "Autres immos corp", 'key': 'autres_immos_corp'},
            {'label': "Immos en cours", 'key': 'immos_en_cours'},
            {'label': "Avances et acomptes", 'key': 'avances_et_acptes'},
            {'label': "Participations", 'key': 'participations'},
            {'label': "Prêts", 'key': 'prets'},
            {'label': "Autres", 'key': 'autres'},
            {'label': "Amortissements", 'key': 'amortissements'},
            {'label': "Provisions stocks", 'key': 'provisions_stocks'},
            {'label': "Provisions créances", 'key': 'provisions_creances'},
            {'label': "Provisions VMP", 'key': 'provisions_vmp'},
            {'label': "ECA", 'key': 'eca'},
            {'label': "EENE", 'key': 'eene'},
            {'label': "Effectif", 'key': 'effectif'},
            {'label': "TOTAL ACTIF IMMOBILISÉ", 'key': 'total_I', 'is_total': True},
        ],
        "ACTIF CIRCULANT": [
            {'label': "Stocks", 'key': 'stocks', 'is_subtotal': True},
            {'label': "Créances", 'key': 'creances', 'is_subtotal': True},
            {'label': "Disponibilités", 'key': 'disponibilites_vmp', 'is_subtotal': True},
            {'label': "TOTAL ACTIF CIRCULANT", 'key': 'total_II', 'is_total': True},
        ],
        "COMPTES DE REGULARISATION": [
            {'label': "Comptes de régularisation", 'key': 'compte_regul', 'is_subtotal': True},
            {'label': "TOTAL REGULARISATION", 'key': 'total_III', 'is_total': True},
        ],
        "TOTAL GENERAL": [
            {'label': "TOTAL GÉNÉRAL", 'key': 'general_total', 'is_final_total': True},
        ]
    }

    structured_data = {}
    field_values_by_year = {}

    # Pré-calculer toutes les valeurs pour éviter les appels multiples aux propriétés
    for year in years:
        instance = data_by_year.get(year)
        if not instance:
            continue
        year_values = {}
        for section, fields_list in structure_map.items():
            for field_info in fields_list:
                key = field_info['key']
                if key:
                    value = getattr(instance, key, Decimal('0'))
                    year_values[key] = value if value is not None else Decimal('0')
        field_values_by_year[year] = year_values

    for section, fields_list in structure_map.items():
        structured_data[section] = []
        for field_info in fields_list:
            row = {'label': field_info['label'], 'is_total': field_info.get('is_total', False), 'is_final_total': field_info.get('is_final_total', False)}
            
            # Traiter la ligne comme un titre si la clé est None
            if field_info['key'] is None:
                row['is_section_title'] = True
                structured_data[section].append(row)
                continue

            values = {}
            for year in years:
                values[year] = field_values_by_year.get(year, {}).get(field_info['key'])

            val_n = values.get(_y(years, 0))
            val_n_moins_1 = values.get(_y(years, 1))
            val_n_moins_2 = values.get(_y(years, 2))

            row['values'] = {
                'n': val_n,
                'n_moins_1': val_n_moins_1,
                'n_moins_2': val_n_moins_2,
            }
            row['variations'] = {
                'n_vs_n_moins_1': calculate_variation(val_n, val_n_moins_1),
                'n_moins_1_vs_n_moins_2': calculate_variation(val_n_moins_1, val_n_moins_2),
            }
            structured_data[section].append(row)
    print(
        "[DEBUG][UTILS][get_structured_actif_data] "
        f"sections={len(structured_data.keys())} "
        f"rows_total={sum(len(v) for v in structured_data.values())}"
    )
    return structured_data



def get_structured_passif_data(acheteur, years):
    """
    Récupère les données de passif, les structure par groupe
    et calcule les totaux intermédiaires et généraux.
    """
    passif_model = PassifC
    data_by_year = {}
    for year in years:
        instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance

    # Définir la structure hiérarchique pour l'affichage du passif
    structure_map = {
        "CAPITAUX PROPRES": [
            {'label': "Capital social", 'key': 'capital_social'},
            {'label': "Primes", 'key': 'primes'},
            {'label': "Écarts de réévaluation", 'key': 'ecarts_de_reevaluation'},
            {'label': "Réserve", 'key': 'reserve'},
            {'label': "Report à nouveau", 'key': 'report_a_nouveau'},
            {'label': "Résultat de l'exercice", 'key': 'resultat_exercice'},
            {'label': "Subventions d'investissement", 'key': 'subv_invest'},
            {'label': "Provision réglementée", 'key': 'provision_regl'},
            {'label': "TOTAL I", 'key': 'total_I', 'is_total': True},
        ],
        "DETTES FINANCIÈRES ET RESSOURCES ASSIMILÉES": [
            {'label': "Emprunts", 'key': 'emprunts'},
            {'label': "Dettes de crédit-bail", 'key': 'dette_credit_bail_contrat_assimile'},
            {'label': "Dettes financières diverses", 'key': 'dettes_financiere_diverses'},
            {'label': "Provision financière risque charge", 'key': 'provision_financiere_risque_charge'},
            {'label': "TOTAL II", 'key': 'total_II', 'is_total': True},
        ],
        "PASSIF CIRCULANT": [
            {'label': "Dettes fournisseurs diverses", 'key': 'dettes_fournisseurs_divers'},
            {'label': "Avance et acomptes reçus", 'key': 'avance_et_acomptes_recu'},
            {'label': "Dettes", 'key': 'dettes'},
            {'label': "Dettes fiscales et sociales", 'key': 'dettes_fiscales_sociales'},
            {'label': "Autres dettes", 'key': 'autres_dettes'},
            {'label': "TOTAL III", 'key': 'total_III', 'is_total': True},
        ],
        "TRÉSORERIE PASSIF": [
            {'label': "Banques, crédits d'escompte", 'key': 'banques_credit_escompte'},
            {'label': "Banque, crédit caisse", 'key': 'banque_credit_caisse'},
            {'label': "Banques, découvert", 'key': 'banques_decouvert'},
            {'label': "TOTAL IV", 'key': 'total_IV', 'is_total': True},
        ],
        "COMPTES DE REGULARISATION": [
            {'label': "Écart de conversion passif", 'key': 'ecart_conversion_passif'},
            {'label': "TOTAL V", 'key': 'total_V', 'is_total': True},
        ],
        "TOTAL GENERAL": [
            {'label': "TOTAL GÉNÉRAL", 'key': 'total_general', 'is_final_total': True},
        ]
    }

    structured_data = {}
    field_values_by_year = {}

    for year in years:
        instance = data_by_year.get(year)
        if not instance: continue
        year_values = {}
        for section, fields_list in structure_map.items():
            for field_info in fields_list:
                key = field_info['key']
                if key:
                    # Accès direct à la propriété ou au champ du modèle
                    value = getattr(instance, key, Decimal('0'))
                    year_values[key] = value if value is not None else Decimal('0')
        field_values_by_year[year] = year_values

    for section, fields_list in structure_map.items():
        structured_data[section] = []
        for field_info in fields_list:
            row = {'label': field_info['label'], 'is_total': field_info.get('is_total', False), 'is_final_total': field_info.get('is_final_total', False)}
            
            # Pas de traitement pour les lignes de titre de section dans cette structure
            if field_info.get('is_section_title'):
                row['is_section_title'] = True
                structured_data[section].append(row)
                continue

            values = {year: field_values_by_year.get(year, {}).get(field_info['key']) for year in years}
            
            val_n = values.get(_y(years, 0))
            val_n_moins_1 = values.get(_y(years, 1))
            val_n_moins_2 = values.get(_y(years, 2))

            row['values'] = {
                'n': val_n,
                'n_moins_1': val_n_moins_1,
                'n_moins_2': val_n_moins_2,
            }
            row['variations'] = {
                'n_vs_n_moins_1': calculate_variation(val_n, val_n_moins_1),
                'n_moins_1_vs_n_moins_2': calculate_variation(val_n_moins_1, val_n_moins_2),
            }
            structured_data[section].append(row)

    return structured_data



def get_structured_resultat_data(acheteur, years):
    """
    Récupère les données du compte de résultat, les structure par groupe
    et calcule les totaux intermédiaires et généraux.
    """
    resultat_model = ResultatC
    data_by_year = {}
    for year in years:
        instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance

    # Définir la structure hiérarchique pour l'affichage du compte de résultat
    structure_map = {
        "PRODUITS D'ACTIVITÉS ORDINAIRES": [
            {'label': "Ventes de marchandises", 'key': 'vente_de_mdses'},
            {'label': "Ventes de produits fabriqués", 'key': 'ventes_de_produits_fabriques'},
            {'label': "Travaux, services vendus", 'key': 'travaux_services_vendus'},
            {'label': "Produits accessoires", 'key': 'produit_accessoires'},
            {'label': "Chiffre d'affaires", 'key': 'ca', 'is_total': True},
            {'label': "Production immobilisée", 'key': 'production_imblise'},
            {'label': "Subventions d'exploitations", 'key': 'subventions_exploitations'},
            {'label': "Production stockée", 'key': 'production_stockee'},
            {'label': "Reprises de provision", 'key': 'reprises_de_provision'},
            {'label': "Transferts de charges", 'key': 'transferts_charges'},
            {'label': "Autres produits", 'key': 'autres_produits'},
            {'label': "TOTAL I", 'key': 'total_I', 'is_total': True},
        ],
        "CHARGES OPÉRATIONNELLES": [
            {'label': "Achat de marchandises", 'key': 'achat_mdses'},
            {'label': "Variation stock marchandises", 'key': 'variation_stock_mdses'},
            {'label': "Achat mp, autres appro", 'key': 'achat_mp_autres_appro'},
            {'label': "Variation stock mp, appro", 'key': 'var_stk_mp_app'},
            {'label': "Autres achats", 'key': 'autres_achats'},
            {'label': "Variation de stocks autres appro", 'key': 'variation_de_stocks_autres_appro'},
            {'label': "Transports", 'key': 'transports'},
            {'label': "Services extérieurs", 'key': 'services_ext'},
            {'label': "Impôts et taxes", 'key': 'impots_taxes'},
            {'label': "Autres charges valeur ajoutée", 'key': 'autres_charges_valeur_ajoutee'},
            {'label': "Charges de personnel", 'key': 'charges_personnel'},
            {'label': "Dotation aux amorts", 'key': 'dotation_aux_amorts'},
            {'label': "Dotation aux provisions", 'key': 'dotation_aux_provisions'},
            {'label': "Autres charges excédent brut", 'key': 'autres_charges_excedent_brute'},
        ],
        "RÉSULTAT FINANCIER": [
            {'label': "Revenus financiers assimilés", 'key': 'revenus_fin_assimiles'},
            {'label': "Prof. VMP et créances immo", 'key': 'prof_vmp_et_cre_actif_immo'},
            {'label': "Intérêts produits assimilés", 'key': 'interets_produit_assim'},
            {'label': "Reprise prov. et transfert", 'key': 'reprise_prov_et_transfert'},
            {'label': "Différence positive de change", 'key': 'diff_positive_de_change'},
            {'label': "Produits nets cessions VMP", 'key': 'prod_nets_cessions_vmp'},
            {'label': "Dot. aux prov. & depreciations", 'key': 'dap'},
            {'label': "Frais fin. & chrges assimilées", 'key': 'frais_fin_charges_assi'},
            {'label': "Différence négative de change", 'key': 'diff_negatives_de_change'},
            {'label': "Ch. nettes cessions VMP", 'key': 'ch_nettes_cessions_vmp'},
            {'label': "RÉSULTAT FINANCIER", 'key': 'resultat_financier', 'is_total': True},
        ],
        "RÉSULTAT EXCEPTIONNEL": [
            {'label': "Sur opérations de gestion", 'key': 'sur_op_gestion_prod_except'},
            {'label': "Sur opérations en capital", 'key': 'sur_op_en_capital_prod_except'},
            {'label': "Reprise prov. transfert", 'key': 'reprise_prov_transfert'},
            {'label': "Sur op. gestion charg. except.", 'key': 'sur_op_gestion_charg_except'},
            {'label': "Sur op. en capital charg. except.", 'key': 'sur_op_en_capital_charg_except'},
            {'label': "Dap et transfert charg. except.", 'key': 'dap_et_transfert_charg_except'},
            {'label': "RÉSULTAT EXCEPTIONNEL", 'key': 'resultat_excep', 'is_total': True},
        ],
        "RÉSULTAT NET": [
            {'label': "Participation des salariés", 'key': 'participation_salairies'},
            {'label': "Impôts sur les bénéfices", 'key': 'impot_sur_benefices'},
            {'label': "RÉSULTAT NET DE L'EXERCICE", 'key': 'resultat_exercice', 'is_final_total': True},
        ]
    }

    structured_data = {}
    field_values_by_year = {}

    for year in years:
        instance = data_by_year.get(year)
        if not instance: continue
        year_values = {}
        for section, fields_list in structure_map.items():
            for field_info in fields_list:
                key = field_info['key']
                if key:
                    value = getattr(instance, key, Decimal('0'))
                    year_values[key] = value if value is not None else Decimal('0')
        field_values_by_year[year] = year_values

    for section, fields_list in structure_map.items():
        structured_data[section] = []
        for field_info in fields_list:
            row = {'label': field_info['label'], 'is_total': field_info.get('is_total', False), 'is_final_total': field_info.get('is_final_total', False)}
            
            if field_info.get('key') is None:
                row['is_section_title'] = True
                structured_data[section].append(row)
                continue

            values = {year: field_values_by_year.get(year, {}).get(field_info['key']) for year in years}
            
            val_n = values.get(_y(years, 0))
            val_n_moins_1 = values.get(_y(years, 1))
            val_n_moins_2 = values.get(_y(years, 2))

            row['values'] = {
                'n': val_n,
                'n_moins_1': val_n_moins_1,
                'n_moins_2': val_n_moins_2,
            }
            row['variations'] = {
                'n_vs_n_moins_1': calculate_variation(val_n, val_n_moins_1),
                'n_moins_1_vs_n_moins_2': calculate_variation(val_n_moins_1, val_n_moins_2),
            }
            structured_data[section].append(row)

    return structured_data



# ... (les importations et autres fonctions existantes) ...

def get_structured_ratios_data_v1(acheteur, years):
    """
    Récupère les données financières, calcule les ratios pour chaque année
    et les structure par groupe pour le template.
    """
    actif_model = ActifC
    passif_model = PassifC
    resultat_model = ResultatC

    ratios_by_year = {}
    for year in years:
        actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        
        if actif_instance and passif_instance and resultat_instance:
            ratios_by_year[year] = RatiosClassique(actif_instance, passif_instance, resultat_instance)
        else:
            ratios_by_year[year] = None

    # Définir la structure des ratios par catégorie
    structure_map = {
        "STRUCTURE FINANCIÈRE": [
            {'label': "Fonds de roulement", 'key': 'fonds_de_roulement'},
            {'label': "Autonomie financière", 'key': 'autonomie_fin'},
            {'label': "Solvabilité", 'key': 'solvabilite'},
        ],
        "LIQUIDITÉ": [
            {'label': "Liquidité réduite", 'key': 'liquidite_reduite'},
            {'label': "Liquidité immédiate", 'key': 'liquidite_immediat'},
        ],
        "RENTABILITÉ": [
            {'label': "Rentabilité économique", 'key': 'rentabilite_economique'},
            {'label': "Rentabilité financière", 'key': 'rentabilite_fin'},
            {'label': "Rendement capitaux propres", 'key': 'rendement_capitaux_propres'},
        ],
        "GESTION": [
            {'label': "Rotation des stocks (M.P)", 'key': 'rotation_des_stock_de_mp'},
            {'label': "Rotation des stocks (P.F)", 'key': 'rotation_des_stock_de_pf'},
            {'label': "Crédit clients (jours)", 'key': 'credit_clients'},
            {'label': "Crédits fournisseurs (jours)", 'key': 'credits_fournisseurs'},
        ],
    }

    structured_data = {}
    for section, ratios_list in structure_map.items():
        rows_data = []
        for ratio_info in ratios_list:
            row = {'label': ratio_info['label']}
            values = {}
            for year in years:
                instance = ratios_by_year.get(year)
                value = getattr(instance, ratio_info['key'], None) if instance else None
                values[year] = value
            
            # Calcul des variations et formatage
            val_n = values.get(_y(years, 0))
            val_n_moins_1 = values.get(_y(years, 1))
            val_n_moins_2 = values.get(_y(years, 2))

            row['values'] = {
                'n': val_n,
                'n_moins_1': val_n_moins_1,
                'n_moins_2': val_n_moins_2,
            }
            row['variations'] = {
                'n_vs_n_moins_1': calculate_variation(val_n, val_n_moins_1),
                'n_moins_1_vs_n_moins_2': calculate_variation(val_n_moins_1, val_n_moins_2),
            }
            rows_data.append(row)
        structured_data[section] = rows_data
        
    return structured_data



def get_structured_ratios_data(acheteur, years):
    """
    Récupère les données financières, calcule les ratios pour chaque année
    et les structure par groupe pour le template.
    """
    actif_model = ActifC
    passif_model = PassifC
    resultat_model = ResultatC

    ratios_by_year = {}
    for year in years:
        actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        
        if actif_instance and passif_instance and resultat_instance:
            ratios_by_year[year] = RatiosClassique(actif_instance, passif_instance, resultat_instance)
        else:
            ratios_by_year[year] = None

    # Définir la structure des ratios par catégorie - MIS À JOUR AVEC LES NOUVEAUX RATIOS
    # unit: 'XAF' = valeur monétaire, '%' = pourcentage (déjà ×100), 'jours' = nombre de jours, '' = ratio pur
    structure_map = {
        "STRUCTURE FINANCIÈRE": [
            {'label': "Fonds de roulement net global", 'key': 'fonds_de_roulement', 'unit': 'XAF'},
            {'label': "Fonds de roulement normatif", 'key': 'fonds_de_roulement_normatif', 'unit': '%'},
            {'label': "Autonomie financière", 'key': 'autonomie_fin', 'unit': '%'},
            {'label': "Solvabilité", 'key': 'solvabilite', 'unit': '%'},
            {'label': "Levier financier", 'key': 'levier_financier', 'unit': ''},
        ],
        "LIQUIDITÉ ET TRÉSORERIE": [
            {'label': "Liquidité réduite", 'key': 'liquidite_reduite', 'unit': ''},
            {'label': "Liquidité immédiate", 'key': 'liquidite_immediat', 'unit': ''},
            {'label': "Besoin en fonds de roulement (BFR)", 'key': 'besoin_en_fond_roulement', 'unit': 'XAF'},
            {'label': "BFR d'exploitation", 'key': 'bfr_exploitation', 'unit': 'XAF'},
        ],
        "RENTABILITÉ": [
            {'label': "Rentabilité économique", 'key': 'rentabilite_economique', 'unit': '%'},
            {'label': "Rentabilité financière", 'key': 'rentabilite_fin', 'unit': '%'},
            {'label': "Rendement capitaux propres (ROE)", 'key': 'rendement_capitaux_propres', 'unit': '%'},
            {'label': "Rentabilité de l'outil de production", 'key': 'rentabilite_de_loutil_de_production', 'unit': '%'},
            {'label': "Couverture des frais financiers", 'key': 'couverture_des_frais_financiers', 'unit': ''},
        ],
        "GESTION DES STOCKS": [
            {'label': "Rotation stocks matières premières (jours)", 'key': 'rotation_des_stock_de_mp', 'unit': 'jours'},
            {'label': "Rotation stocks produits finis (jours)", 'key': 'rotation_des_stock_de_pf', 'unit': 'jours'},
            {'label': "Rotation stocks marchandises (jours)", 'key': 'rotation_des_stock_de_marchandises', 'unit': 'jours'},
            {'label': "Rotation stocks services (jours)", 'key': 'rotation_des_stock_de_services', 'unit': 'jours'},
            {'label': "Délai moyen rotation stocks", 'key': 'delai_rotation_stocks', 'unit': 'jours'},
        ],
        "GESTION DES CRÉDITS": [
            {'label': "Crédit clients (jours)", 'key': 'credit_clients', 'unit': 'jours'},
            {'label': "Crédits fournisseurs (jours)", 'key': 'credits_fournisseurs', 'unit': 'jours'},
        ],
        "CAPACITÉ DE REMBOURSEMENT": [
            {'label': "Capacité de remboursement", 'key': 'capacite_remboursement', 'unit': ''},
        ]
    }

    structured_data = {}
    for section, ratios_list in structure_map.items():
        rows_data = []
        for ratio_info in ratios_list:
            row = {'label': ratio_info['label'], 'unit': ratio_info.get('unit', '')}
            values = {}
            for year in years:
                instance = ratios_by_year.get(year)
                value = getattr(instance, ratio_info['key'], None) if instance else None
                values[year] = value

            # Calcul des variations et formatage
            val_n = values.get(_y(years, 0))
            val_n_moins_1 = values.get(_y(years, 1))
            val_n_moins_2 = values.get(_y(years, 2))

            row['values'] = {
                'n': val_n,
                'n_moins_1': val_n_moins_1,
                'n_moins_2': val_n_moins_2,
            }
            row['variations'] = {
                'n_vs_n_moins_1': calculate_variation(val_n, val_n_moins_1),
                'n_moins_1_vs_n_moins_2': calculate_variation(val_n_moins_1, val_n_moins_2),
            }
            rows_data.append(row)
        structured_data[section] = rows_data

    return structured_data


def get_charts_structure_financiere_data_v1(acheteur, years):
    """
    Génère les données pour le chart de structure financière
    """
    actif_model = ActifC
    passif_model = PassifC
    resultat_model = ResultatC
    
    charts_data = {
        'title': 'Structure Financière',
        'labels': [str(year) for year in years],
        'datasets': [],
        'legende': {
            'FDR': 'Fonds de Roulement Net Global',
            'FDRN': 'Fonds de Roulement Normatif', 
            'AUFIN': 'Autonomie Financière',
            'LR': 'Liquidité Réduite (Quick Ratio)',
            'LI': 'Liquidité Immédiate (Cash Ratio)'
        }
    }
    
    # Calcul des ratios pour chaque année
    ratios_by_year = {}
    for year in years:
        actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        
        if actif_instance and passif_instance and resultat_instance:
            ratios = RatiosClassique(actif_instance, passif_instance, resultat_instance)
            ratios_by_year[year] = ratios
    
    # Dataset Fonds de Roulement (FDR)
    fdr_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        fdr_data.append(float(ratio.fonds_de_roulement) if ratio and ratio.fonds_de_roulement else 0)
    
    charts_data['datasets'].append({
        'label': 'FDR',
        'data': fdr_data,
        'borderColor': 'rgb(75, 192, 192)',
        'backgroundColor': 'rgba(75, 192, 192, 0.2)'
    })
    
    # Dataset Fonds de Roulement Normatif (FDRN)
    fdrn_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        fdrn_data.append(float(ratio.fonds_de_roulement_normatif) if ratio and ratio.fonds_de_roulement_normatif else 0)
    
    charts_data['datasets'].append({
        'label': 'FDRN',
        'data': fdrn_data,
        'borderColor': 'rgb(255, 99, 132)',
        'backgroundColor': 'rgba(255, 99, 132, 0.2)'
    })
    
    # Dataset Autonomie Financière (AUFIN)
    aufin_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        aufin_data.append(float(ratio.autonomie_fin) if ratio and ratio.autonomie_fin else 0)
    
    charts_data['datasets'].append({
        'label': 'AUFIN',
        'data': aufin_data,
        'borderColor': 'rgb(54, 162, 235)',
        'backgroundColor': 'rgba(54, 162, 235, 0.2)'
    })
    
    # Dataset Liquidité Réduite (LR)
    lr_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        lr_data.append(float(ratio.liquidite_reduite) if ratio and ratio.liquidite_reduite else 0)
    
    charts_data['datasets'].append({
        'label': 'LR',
        'data': lr_data,
        'borderColor': 'rgb(255, 205, 86)',
        'backgroundColor': 'rgba(255, 205, 86, 0.2)'
    })
    
    # Dataset Liquidité Immédiate (LI)
    li_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        li_data.append(float(ratio.liquidite_immediat) if ratio and ratio.liquidite_immediat else 0)
    
    charts_data['datasets'].append({
        'label': 'LI',
        'data': li_data,
        'borderColor': 'rgb(153, 102, 255)',
        'backgroundColor': 'rgba(153, 102, 255, 0.2)'
    })
    
    # return charts_data
    # Générer l'image
    image_base64 = generate_chart_image(charts_data)
    return image_base64


def get_charts_rentabilite_financiere_data_v1(acheteur, years):
    """
    Génère les données pour le chart de rentabilité financière
    """
    actif_model = ActifC
    passif_model = PassifC
    resultat_model = ResultatC
    
    charts_data = {
        'title': 'Rentabilité Financière',
        'labels': [str(year) for year in years],
        'datasets': [],
        'legende': {
            'CAF': 'Chiffre d\'Affaires',
            'CAHT': 'Chiffre d\'Affaires Hors Taxes',
            'RE': 'Rentabilité Économique',
            'REF': 'Rentabilité Financière',
            'ROP': 'Rentabilité Outil de Production',
            'CFF': 'Couverture Frais Financiers'
        }
    }
    
    # Calcul des ratios pour chaque année
    ratios_by_year = {}
    for year in years:
        actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        
        if actif_instance and passif_instance and resultat_instance:
            ratios = RatiosClassique(actif_instance, passif_instance, resultat_instance)
            ratios_by_year[year] = ratios
    
    # Dataset Chiffre d'Affaires (CAF)
    caf_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        caf_data.append(float(ratio.chiffre_d_affaires) if ratio and ratio.chiffre_d_affaires else 0)
    
    charts_data['datasets'].append({
        'label': 'CAF',
        'data': caf_data,
        'borderColor': 'rgb(75, 192, 192)',
        'backgroundColor': 'rgba(75, 192, 192, 0.2)'
    })
    
    # Dataset Chiffre d'Affaires Hors Taxes (CAHT)
    caht_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        caht_data.append(float(ratio.chiffre_d_affaires_hors_taxe) if ratio and ratio.chiffre_d_affaires_hors_taxe else 0)
    
    charts_data['datasets'].append({
        'label': 'CAHT',
        'data': caht_data,
        'borderColor': 'rgb(255, 99, 132)',
        'backgroundColor': 'rgba(255, 99, 132, 0.2)'
    })
    
    # Dataset Rentabilité Économique (RE)
    re_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        re_data.append(float(ratio.rentabilite_economique) if ratio and ratio.rentabilite_economique else 0)
    
    charts_data['datasets'].append({
        'label': 'RE',
        'data': re_data,
        'borderColor': 'rgb(54, 162, 235)',
        'backgroundColor': 'rgba(54, 162, 235, 0.2)'
    })
    
    # Dataset Rentabilité Financière (REF)
    ref_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        ref_data.append(float(ratio.rentabilite_fin) if ratio and ratio.rentabilite_fin else 0)
    
    charts_data['datasets'].append({
        'label': 'REF',
        'data': ref_data,
        'borderColor': 'rgb(255, 205, 86)',
        'backgroundColor': 'rgba(255, 205, 86, 0.2)'
    })
    
    # Dataset Rentabilité Outil de Production (ROP)
    rop_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        rop_data.append(float(ratio.rentabilite_de_loutil_de_production) if ratio and ratio.rentabilite_de_loutil_de_production else 0)
    
    charts_data['datasets'].append({
        'label': 'ROP',
        'data': rop_data,
        'borderColor': 'rgb(153, 102, 255)',
        'backgroundColor': 'rgba(153, 102, 255, 0.2)'
    })
    
    # Dataset Couverture Frais Financiers (CFF)
    cff_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        cff_data.append(float(ratio.couverture_des_frais_financiers) if ratio and ratio.couverture_des_frais_financiers else 0)
    
    charts_data['datasets'].append({
        'label': 'CFF',
        'data': cff_data,
        'borderColor': 'rgb(255, 159, 64)',
        'backgroundColor': 'rgba(255, 159, 64, 0.2)'
    })
    
    # return charts_data
    # Générer l'image
    image_base64 = generate_chart_image(charts_data)
    return image_base64


def get_charts_delais_data_v1(acheteur, years, chart_type='bar'):
    """
    Génère les données pour le chart des délais
    """
    actif_model = ActifC
    passif_model = PassifC
    resultat_model = ResultatC
    
    charts_data = {
        'title': 'Délais',
        'labels': [str(year) for year in years],
        'datasets': [],
        'legende': {
            'RSMP': 'Rotation Stocks MP (jours)',
            'RSPF': 'Rotation Stocks PF (jours)',
            'RSTM': 'Rotation Stocks Marchandises (jours)',
            'RSTS': 'Rotation Stocks Services (jours)',
            'CC': 'Crédit Clients (jours)',
            'CF': 'Crédit Fournisseurs (jours)'
        }
    }
    
    # Calcul des ratios pour chaque année
    ratios_by_year = {}
    for year in years:
        actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        
        if actif_instance and passif_instance and resultat_instance:
            ratios = RatiosClassique(actif_instance, passif_instance, resultat_instance)
            ratios_by_year[year] = ratios
    
    # Dataset Rotation Stocks MP (RSMP)
    rsmp_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        rsmp_data.append(float(ratio.rotation_des_stock_de_mp) if ratio and ratio.rotation_des_stock_de_mp else 0)
    
    charts_data['datasets'].append({
        'label': 'RSMP',
        'data': rsmp_data,
        'borderColor': 'rgb(75, 192, 192)',
        'backgroundColor': 'rgba(75, 192, 192, 0.2)'
    })
    
    # Dataset Rotation Stocks PF (RSPF)
    rspf_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        rspf_data.append(float(ratio.rotation_des_stock_de_pf) if ratio and ratio.rotation_des_stock_de_pf else 0)
    
    charts_data['datasets'].append({
        'label': 'RSPF',
        'data': rspf_data,
        'borderColor': 'rgb(255, 99, 132)',
        'backgroundColor': 'rgba(255, 99, 132, 0.2)'
    })
    
    # Dataset Rotation Stocks Marchandises (RSTM)
    rstmt_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        rstmt_data.append(float(ratio.rotation_des_stock_de_marchandises) if ratio and ratio.rotation_des_stock_de_marchandises else 0)
    
    charts_data['datasets'].append({
        'label': 'RSTM',
        'data': rstmt_data,
        'borderColor': 'rgb(54, 162, 235)',
        'backgroundColor': 'rgba(54, 162, 235, 0.2)'
    })
    
    # Dataset Rotation Stocks Services (RSTS)
    rsts_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        rsts_data.append(float(ratio.rotation_des_stock_de_services) if ratio and ratio.rotation_des_stock_de_services else 0)
    
    charts_data['datasets'].append({
        'label': 'RSTS',
        'data': rsts_data,
        'borderColor': 'rgb(255, 205, 86)',
        'backgroundColor': 'rgba(255, 205, 86, 0.2)'
    })
    
    # Dataset Crédit Clients (CC)
    cc_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        cc_data.append(float(ratio.credit_clients) if ratio and ratio.credit_clients else 0)
    
    charts_data['datasets'].append({
        'label': 'CC',
        'data': cc_data,
        'borderColor': 'rgb(153, 102, 255)',
        'backgroundColor': 'rgba(153, 102, 255, 0.2)'
    })
    
    # Dataset Crédit Fournisseurs (CF)
    cf_data = []
    for year in years:
        ratio = ratios_by_year.get(year)
        cf_data.append(float(ratio.credits_fournisseurs) if ratio and ratio.credits_fournisseurs else 0)
    
    charts_data['datasets'].append({
        'label': 'CF',
        'data': cf_data,
        'borderColor': 'rgb(255, 159, 64)',
        'backgroundColor': 'rgba(255, 159, 64, 0.2)'
    })
    
    # return charts_data
    # Générer l'image
    image_base64 = generate_chart_image(charts_data)
    return image_base64


def get_charts_structure_financiere_data(acheteur, years, chart_type='bar'):
    """
    Génère les données pour le chart de structure financière AVEC GESTION D'ERREURS.
    ``chart_type`` peut être 'bar' ou 'line'.
    """
    try:
        actif_model = ActifC
        passif_model = PassifC
        resultat_model = ResultatC
        
        # Vérifier s'il y a des données
        has_data = False
        ratios_by_year = {}
        
        for year in years:
            actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            
            if actif_instance and passif_instance and resultat_instance:
                ratios = RatiosClassique(actif_instance, passif_instance, resultat_instance)
                ratios_by_year[year] = ratios
                has_data = True
            else:
                ratios_by_year[year] = None
                print(
                    "[DEBUG][UTILS][get_charts_structure_financiere_data] "
                    f"year={year} missing={{"
                    f"actif:{'OK' if actif_instance else 'None'}, "
                    f"passif:{'OK' if passif_instance else 'None'}, "
                    f"resultat:{'OK' if resultat_instance else 'None'}"
                    f"}}"
                )
        
        if not has_data:
            print(
                "[DEBUG][UTILS][get_charts_structure_financiere_data] "
                f"acheteur_id={getattr(acheteur, 'id', None)} years={years} -> has_data=False"
            )
            return None
        
        # Préparer les données
        labels = [str(year) for year in years]
        
        # Récupérer les données avec valeurs par défaut
        fdr_data = []
        fdrn_data = []
        aufin_data = []
        lr_data = []
        li_data = []
        
        for year in years:
            ratio = ratios_by_year.get(year)
            fdr_data.append(float(ratio.fonds_de_roulement) if ratio and ratio.fonds_de_roulement else 0.0)
            fdrn_data.append(float(ratio.fonds_de_roulement_normatif) if ratio and ratio.fonds_de_roulement_normatif else 0.0)
            aufin_data.append(float(ratio.autonomie_fin) if ratio and ratio.autonomie_fin else 0.0)
            lr_data.append(float(ratio.liquidite_reduite) if ratio and ratio.liquidite_reduite else 0.0)
            li_data.append(float(ratio.liquidite_immediat) if ratio and ratio.liquidite_immediat else 0.0)

        print(
            "[DEBUG][UTILS][get_charts_structure_financiere_data] "
            f"series={{fdr:{fdr_data}, fdrn:{fdrn_data}, aufin:{aufin_data}, lr:{lr_data}, li:{li_data}}}"
        )
        
        # sort labels and corresponding data chronologically
        try:
            order = sorted(range(len(labels)), key=lambda i: int(labels[i]))
            labels = [labels[i] for i in order]
            fdr_data = [fdr_data[i] for i in order]
            fdrn_data = [fdrn_data[i] for i in order]
            aufin_data = [aufin_data[i] for i in order]
            lr_data = [lr_data[i] for i in order]
            li_data = [li_data[i] for i in order]
        except Exception:
            pass

        # Créer le graphique (barres ou lignes selon chart_type)
        plt.figure(figsize=(12, 8))
        if chart_type == 'bar':
            width = 0.15
            x = np.arange(len(labels))
            plt.bar(x - 2*width, fdr_data, width=width, label='FDR - Fonds de Roulement Net Global', color='#1f77b4')
            plt.bar(x - width, fdrn_data, width=width, label='FDRN - Fonds de Roulement Normatif', color='#ff7f0e')
            plt.bar(x, aufin_data, width=width, label='AUFIN - Autonomie Financière', color='#2ca02c')
            plt.bar(x + width, lr_data, width=width, label='LR - Liquidité Réduite', color='#d62728')
            plt.bar(x + 2*width, li_data, width=width, label='LI - Liquidité Immédiate', color='#9467bd')
            plt.xticks(x, labels)
        else:
            # Tracer les courbes
            plt.plot(labels, fdr_data, label='FDR - Fonds de Roulement Net Global', marker='o', linewidth=2, color='#1f77b4')
            plt.plot(labels, fdrn_data, label='FDRN - Fonds de Roulement Normatif', marker='s', linewidth=2, color='#ff7f0e')
            plt.plot(labels, aufin_data, label='AUFIN - Autonomie Financière', marker='^', linewidth=2, color='#2ca02c')
            plt.plot(labels, lr_data, label='LR - Liquidité Réduite', marker='d', linewidth=2, color='#d62728')
            plt.plot(labels, li_data, label='LI - Liquidité Immédiate', marker='v', linewidth=2, color='#9467bd')

        # Personnaliser le graphique
        plt.title('Structure Financière', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Années', fontsize=12)
        plt.ylabel('Valeurs', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_structure_financiere_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_charts_rentabilite_financiere_data(acheteur, years, chart_type='radar'):
    """
    Génère un radar chart (toile d'araignée) pour les ratios de rentabilité financière.
    Chaque année est représentée par un polygone, les 6 axes étant les ratios clés.
    """
    try:
        actif_model = ActifC
        passif_model = PassifC
        resultat_model = ResultatC

        has_data = False
        ratios_by_year = {}

        for year in years:
            actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()

            if actif_instance and passif_instance and resultat_instance:
                ratios = RatiosClassique(actif_instance, passif_instance, resultat_instance)
                ratios_by_year[year] = ratios
                has_data = True
            else:
                ratios_by_year[year] = None

        if not has_data:
            return None

        # Trier les années de façon croissante pour l'affichage (N-2, N-1, N)
        sorted_years = sorted(years)
        labels_years = [str(y) for y in sorted_years]

        # Extraire les valeurs pour chaque année
        re_data   = [float(ratios_by_year[y].rentabilite_economique or 0) if ratios_by_year.get(y) else 0.0 for y in sorted_years]
        ref_data  = [float(ratios_by_year[y].rentabilite_fin or 0) if ratios_by_year.get(y) else 0.0 for y in sorted_years]
        rop_data  = [float(ratios_by_year[y].rentabilite_de_loutil_de_production or 0) if ratios_by_year.get(y) else 0.0 for y in sorted_years]
        cff_data  = [float(ratios_by_year[y].couverture_des_frais_financiers or 0) if ratios_by_year.get(y) else 0.0 for y in sorted_years]
        caf_data  = [float(ratios_by_year[y].chiffre_d_affaires or 0) if ratios_by_year.get(y) else 0.0 for y in sorted_years]
        caht_data = [float(ratios_by_year[y].chiffre_d_affaires_hors_taxe or 0) if ratios_by_year.get(y) else 0.0 for y in sorted_years]

        # Normaliser le CA en millions pour que les échelles soient comparables
        caf_m  = [v / 1e6 if v else 0.0 for v in caf_data]
        caht_m = [v / 1e6 if v else 0.0 for v in caht_data]

        # Définition des axes du radar
        metric_labels = [
            'RE (%)', 'REF (%)', 'ROP (%)', 'CFF',
            'CA (M)', 'CAHT (M)'
        ]
        n_metrics = len(metric_labels)
        angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
        angles += angles[:1]  # fermer le polygone

        # Regrouper les séries par année [RE, REF, ROP, CFF, CA, CAHT]
        series = {
            labels_years[i]: [re_data[i], ref_data[i], rop_data[i], cff_data[i], caf_m[i], caht_m[i]]
            for i in range(len(sorted_years))
        }

        # Normalisation 0-1 par axe (pour rendre la toile lisible)
        all_vals = np.array([series[y] for y in labels_years], dtype=float)
        mins = all_vals.min(axis=0)
        maxs = all_vals.max(axis=0)
        ranges = maxs - mins
        ranges[ranges == 0] = 1.0
        norm_series = {y: ((np.array(series[y], dtype=float) - mins) / ranges).tolist() for y in labels_years}

        # Palette couleurs par année
        palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

        fig, ax = plt.subplots(figsize=(9, 7), subplot_kw=dict(polar=True))
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        for idx, year_label in enumerate(labels_years):
            vals = norm_series[year_label]
            vals_plot = vals + vals[:1]
            color = palette[idx % len(palette)]
            ax.plot(angles, vals_plot, 'o-', linewidth=2, label=year_label, color=color)
            ax.fill(angles, vals_plot, alpha=0.12, color=color)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels, size=10, fontweight='bold')
        ax.set_ylim(0, 1)
        ax.set_yticklabels([])
        ax.yaxis.grid(True, linestyle='--', alpha=0.5)
        ax.xaxis.grid(True, linestyle='--', alpha=0.3)

        # Valeurs réelles en annotation sur le graphe le plus récent (N)
        last_year = labels_years[-1]
        raw_vals = series[last_year]
        raw_labels = [f'{v:.1f}' for v in raw_vals]
        for angle, raw_label, norm_val in zip(angles[:-1], raw_labels, norm_series[last_year]):
            ax.annotate(raw_label, xy=(angle, norm_val),
                        xytext=(angle, min(norm_val + 0.12, 1.0)),
                        fontsize=7, ha='center', color='#333333')

        ax.set_title('Rentabilité Financière', size=15, fontweight='bold', pad=25)
        ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), title='Année', fontsize=10)

        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()

        return base64.b64encode(image_png).decode('utf-8')

    except Exception as e:
        print(f"Erreur dans get_charts_rentabilite_financiere_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_charts_delais_data(acheteur, years, chart_type='hbar'):
    """
    Génère un diagramme en barres horizontales groupées pour les délais de rotation.
    Une barre par ratio, groupée par année (N-2, N-1, N).
    """
    try:
        actif_model = ActifC
        passif_model = PassifC
        resultat_model = ResultatC

        has_data = False
        ratios_by_year = {}

        for year in years:
            actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()

            if actif_instance and passif_instance and resultat_instance:
                ratios = RatiosClassique(actif_instance, passif_instance, resultat_instance)
                ratios_by_year[year] = ratios
                has_data = True
            else:
                ratios_by_year[year] = None

        if not has_data:
            return None

        # Trier les années croissant (N-2, N-1, N)
        sorted_years = sorted(years)
        labels_years = [str(y) for y in sorted_years]

        # Noms des métriques (axe Y)
        metric_labels = [
            'Stocks MP (j)', 'Stocks PF (j)',
            'Stocks Marchandises (j)', 'Stocks Services (j)',
            'Crédit Clients (j)', 'Crédit Fournisseurs (j)',
        ]
        n_metrics = len(metric_labels)

        # Valeurs pour chaque année [rsmp, rspf, rstmt, rsts, cc, cf]
        series = {}
        for y in sorted_years:
            r = ratios_by_year.get(y)
            series[y] = [
                float(r.rotation_des_stock_de_mp or 0) if r else 0.0,
                float(r.rotation_des_stock_de_pf or 0) if r else 0.0,
                float(r.rotation_des_stock_de_marchandises or 0) if r else 0.0,
                float(r.rotation_des_stock_de_services or 0) if r else 0.0,
                float(r.credit_clients or 0) if r else 0.0,
                float(r.credits_fournisseurs or 0) if r else 0.0,
            ]

        palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        n_years = len(sorted_years)
        bar_h = 0.22
        y_pos = np.arange(n_metrics)

        fig, ax = plt.subplots(figsize=(12, 7))

        for idx, year in enumerate(sorted_years):
            offsets = y_pos - (n_years - 1) * bar_h / 2 + idx * bar_h
            vals = series[year]
            bars = ax.barh(offsets, vals, height=bar_h,
                           label=str(year), color=palette[idx % len(palette)],
                           edgecolor='white', linewidth=0.5)
            # Valeur annotée sur chaque barre
            for bar, val in zip(bars, vals):
                if val > 0:
                    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                            f'{val:.1f}', va='center', ha='left', fontsize=8, color='#333333')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(metric_labels, fontsize=10)
        ax.set_xlabel('Jours', fontsize=11)
        ax.set_title('Délais de Rotation', fontsize=15, fontweight='bold', pad=15)
        ax.legend(title='Année', loc='lower right', fontsize=10)
        ax.grid(True, alpha=0.3, axis='x', linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()

        return base64.b64encode(image_png).decode('utf-8')

    except Exception as e:
        print(f"Erreur dans get_charts_delais_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None







def generate_risk_gauge(score, max_score=9, filename="risk_gauge.png"):
    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw={'projection': 'polar'})
    ax.set_theta_offset(np.pi/2)
    ax.set_theta_direction(-1)

    # Définition des zones colorées
    categories = [
        (0, 2, 'green', 'Low Risk'),
        (2, 4, 'yellow', 'Medium Risk'),
        (4, 6, 'orange', 'High Risk'),
        (6, 9, 'red', 'Very High Risk')
    ]

    for start, end, color, label in categories:
        ax.bar(
            x=np.linspace(np.radians(start * 20), np.radians(end * 20), 100),
            height=np.ones(100),
            width=0.05,
            bottom=0,
            color=color,
            edgecolor=color,
            alpha=0.7
        )

    # Aiguille
    angle = np.radians(score * 20)  # score → angle
    ax.plot([angle, angle], [0, 1], color='black', linewidth=3)

    # Retirer les axes
    ax.set_axis_off()

    # Titre
    plt.title("EVALUATION DU RISQUE", fontsize=14, fontweight="bold", pad=20)

    # Texte en bas
    risk_level = "Low Risk" if score <= 2 else \
                 "Medium Risk" if score <= 4 else \
                 "High Risk" if score <= 6 else \
                 "Very High Risk"
    plt.figtext(0.5, 0.01, f"Score : {score} / {max_score} → {risk_level}",
                ha="center", fontsize=12, fontweight="bold")

    # Sauvegarder dans MEDIA
    filepath = os.path.join(settings.MEDIA_ROOT, filename)
    plt.savefig(filepath, bbox_inches="tight")
    plt.close()
    return os.path.join(settings.MEDIA_URL, filename)  # chemin pour l’affichage




#############################################################
#
# Fonctions utilitaires génériques
#
############################################################# 

def _build_structured_data(structure_map, data_by_year, years):
    """
    Fonction utilitaire générique pour construire les données structurées.
    """
    structured_data = {}
    field_values_by_year = {}
    # Pré-calculer toutes les valeurs
    for year in years:
        instance = data_by_year.get(year)
        if not instance:
            continue
        year_values = {}
        for section, fields_list in structure_map.items():
            for field_info in fields_list:
                key = field_info['key']
                if key:
                    # Vérifier si c'est une méthode, l'appeler
                    attr = getattr(instance, key, None)
                    if callable(attr):
                        value = attr()
                    else:
                        value = attr
                    year_values[key] = float(value) if value is not None else 0.0
        field_values_by_year[year] = year_values
    # Construire la structure finale
    for section, fields_list in structure_map.items():
        structured_data[section] = []
        for field_info in fields_list:
            row = {
                'label': field_info['label'],
                'is_total': field_info.get('is_total', False),
                'is_final_total': field_info.get('is_final_total', False)
            }

            if field_info['key'] is None:
                row['is_section_title'] = True
                structured_data[section].append(row)
                continue
            values = {}
            for year in years:
                values[year] = field_values_by_year.get(year, {}).get(field_info['key'], 0.0)
            val_n = values.get(_y(years, 0), 0.0)
            val_n_moins_1 = values.get(_y(years, 1), 0.0)
            val_n_moins_2 = values.get(_y(years, 2), 0.0)
            row['values'] = {
                'n': val_n,
                'n_moins_1': val_n_moins_1,
                'n_moins_2': val_n_moins_2,
            }
            row['variations'] = {
                'n_vs_n_moins_1': calculate_variation(val_n, val_n_moins_1),
                'n_moins_1_vs_n_moins_2': calculate_variation(val_n_moins_1, val_n_moins_2),
            }
            structured_data[section].append(row)
    return structured_data



def _build_ratios_data(structure_map, ratios_by_year, years):
    """
    Fonction utilitaire générique pour construire les données de ratios.
    """
    structured_data = {}
    for section, ratios_list in structure_map.items():
        rows_data = []
        for ratio_info in ratios_list:
            row = {'label': ratio_info['label']}
            values = {}
            for year in years:
                instance = ratios_by_year.get(year)
                if instance:
                    value = getattr(instance, ratio_info['key'], None)
                    values[year] = float(value) if value is not None else None
                else:
                    values[year] = None

            val_n = values.get(_y(years, 0))
            val_n_moins_1 = values.get(_y(years, 1))
            val_n_moins_2 = values.get(_y(years, 2))
            row['values'] = {
                'n': val_n,
                'n_moins_1': val_n_moins_1,
                'n_moins_2': val_n_moins_2,
            }
            row['variations'] = {
                'n_vs_n_moins_1': calculate_variation(val_n, val_n_moins_1),
                'n_moins_1_vs_n_moins_2': calculate_variation(val_n_moins_1, val_n_moins_2),
            }
            rows_data.append(row)
        structured_data[section] = rows_data

    return structured_data



def _build_ratios_data_v2(structure_map, ratios_by_year, years):
    """
    Construit une structure de données pour les ratios.
    """
    structured_data = {}
    for section, rows in structure_map.items():
        structured_rows = []
        for row in rows:
            key = row['key']
            label = row['label']
            is_total = row.get('is_total', False)
            is_final_total = row.get('is_final_total', False)

            values = {}
            variations = {}
            for i, year in enumerate(years):
                year_key = f"n_moins_{i}" if i > 0 else "n"
                values[year_key] = ratios_by_year.get(year, {}).get(key, 0) if ratios_by_year.get(year) else 0

            # Calcul des variations
            if len(years) >= 2:
                n = values.get('n', 0)
                n_moins_1 = values.get('n_moins_1', 0)
                variations['n_vs_n_moins_1'] = f"{((n - n_moins_1) / abs(n_moins_1) * 100 if n_moins_1 else 0):+.2f}%" if n_moins_1 else "N/A"

                if len(years) >= 3:
                    n_moins_2 = values.get('n_moins_2', 0)
                    variations['n_moins_1_vs_n_moins_2'] = f"{((n_moins_1 - n_moins_2) / abs(n_moins_2) * 100 if n_moins_2 else 0):+.2f}%" if n_moins_2 else "N/A"
                else:
                    variations['n_moins_1_vs_n_moins_2'] = "N/A"
            else:
                variations['n_vs_n_moins_1'] = "N/A"
                variations['n_moins_1_vs_n_moins_2'] = "N/A"

            structured_rows.append({
                'label': label,
                'key': key,
                'values': values,
                'variations': variations,
                'is_total': is_total,
                'is_final_total': is_final_total
            })

        structured_data[section] = structured_rows

    return structured_data



def _build_ratios_data_bancaire(structure_map, ratios_by_year, years):
    """
    Construit une structure de données pour les ratios bancaires.
    """
    structured_data = {}
    for section, ratios_list in structure_map.items():
        rows_data = []
        for ratio_info in ratios_list:
            row = {'label': ratio_info['label']}
            values = {}
            variations = {}
            for year in years:
                instance = ratios_by_year.get(year)
                if instance:
                    values[year] = {
                        'calculated': instance['ratios'].get(ratio_info['key']),
                        'bounded': instance['ratios_bornees'].get(ratio_info['key']),
                    }
                else:
                    values[year] = {'calculated': None, 'bounded': None}

            val_n = values.get(_y(years, 0))
            val_n_moins_1 = values.get(_y(years, 1))
            val_n_moins_2 = values.get(_y(years, 2))

            row['values'] = {
                'n': val_n,
                'n_moins_1': val_n_moins_1,
                'n_moins_2': val_n_moins_2,
            }

            # Calcul des variations pour les valeurs calculées
            row['variations'] = {
                'n_vs_n_moins_1': calculate_variation(
                    val_n['calculated'] if val_n else None,
                    val_n_moins_1['calculated'] if val_n_moins_1 else None,
                ),
                'n_moins_1_vs_n_moins_2': calculate_variation(
                    val_n_moins_1['calculated'] if val_n_moins_1 else None,
                    val_n_moins_2['calculated'] if val_n_moins_2 else None,
                ),
            }

            rows_data.append(row)
        structured_data[section] = rows_data

    return structured_data








#############################################################
#
# Fonctions pour le bilan SYSCOHADA
#
############################################################# 
def get_structured_actif_syscohada_data(acheteur, years):
    """
    Récupère et structure les données d'actif pour le bilan SYSCOHADA.
    """
    actif_model = ActifS
    data_by_year = {}
    for year in years:
        instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance

    structure_map = {
        "IMMOBILISATIONS": [
            {'label': "Intangible assets", 'key': 'immobilisations_incorporelles'},
            {'label': "Tangible assets", 'key': 'immobilisations_corporelles'},
            {'label': "Financial assets", 'key': 'immobilisations_financieres'},
            {'label': "Advances on fixed assets", 'key': 'avances_acompte_immobilisations'},
            {'label': "TOTAL FIXED ASSETS", 'key': 'total_actif_immobilise', 'is_total': True},
        ],
        "CURRENT ASSETS": [
            {'label': "HAO current assets", 'key': 'actif_circulant_hao'},
            {'label': "Stocks and work in progress", 'key': 'stock_encours'},
            {'label': "Trade and other receivables", 'key': 'creances_emplois_similaires'},
            {'label': "TOTAL CURRENT ASSETS", 'key': 'total_actif_circulant', 'is_total': True},
        ],
        "CASH AND EQUIVALENTS": [
            {'label': "Marketable securities", 'key': 'valeurs_mobilieres_placement'},
            {'label': "Cash", 'key': 'disponibilites'},
            {'label': "Bank and postal accounts", 'key': 'banque_cheque_postal_caisse_assimiles'},
            {'label': "TOTAL CASH", 'key': 'total_tresorerie_equivalents', 'is_total': True},
        ],
        "TOTAL ASSETS": [
            {'label': "TOTAL ASSETS", 'key': 'total_actif', 'is_final_total': True},
        ]
    }

    return _build_structured_data(structure_map, data_by_year, years)


def get_structured_passif_syscohada_data(acheteur, years):
    """
    Récupère et structure les données de passif pour le bilan SYSCOHADA.
    """
    passif_model = PassifS
    data_by_year = {}
    for year in years:
        instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance

    structure_map = {
        "SHAREHOLDERS' EQUITY": [
            {'label': "Share capital", 'key': 'capital'},
            {'label': "Share premium", 'key': 'primes_liees_capital_social'},
            {'label': "Revaluation reserves", 'key': 'ecart_reevaluation'},
            {'label': "Reserves", 'key': 'reserves_indisponibles'},
            {'label': "Retained earnings", 'key': 'report_nouveau'},
            {'label': "Net profit", 'key': 'resultat_net_exercice'},
            {'label': "Investment grants", 'key': 'subventions_investissements'},
            {'label': "Regulated provisions", 'key': 'provisions_reglees'},
            {'label': "TOTAL EQUITY", 'key': 'total_capitaux_propres_ressources_similaires', 'is_total': True},
        ],
        "LONG-TERM LIABILITIES": [
            {'label': "Loans and financial debts", 'key': 'emprunts_dettes_financieres_diverse'},
            {'label': "Finance lease debts", 'key': 'dettes_location_vente'},
            {'label': "Provisions for risks", 'key': 'provisions_risques_charges'},
            {'label': "TOTAL LONG-TERM LIABILITIES", 'key': 'total_dettes_financieres_ressources_similaires', 'is_total': True},
        ],
        "CURRENT LIABILITIES": [
            {'label': "HAO current liabilities", 'key': 'passif_circulant_hao'},
            {'label': "Trade payables", 'key': 'fournisseurs_exploitation'},
            {'label': "Tax and social debts", 'key': 'dettes_fiscales_sociales'},
            {'label': "Other debts", 'key': 'autres_dettes'},
            {'label': "Short-term provisions", 'key': 'provisions_risques_court_terme'},
            {'label': "TOTAL CURRENT LIABILITIES", 'key': 'total_passifs_courants', 'is_total': True},
        ],
        "BANK DEBT": [
            {'label': "Bank loans", 'key': 'banques_credit_escompte'},
            {'label': "Bank overdraft", 'key': 'banques_etablissements_financiers_credit_caisse'},
            {'label': "TOTAL BANK DEBT", 'key': 'total_tresorerie_equivalents', 'is_total': True},
        ],
        "TOTAL LIABILITIES": [
            {'label': "TOTAL LIABILITIES AND EQUITY", 'key': 'total_passifs', 'is_final_total': True},
        ]
    }

    return _build_structured_data(structure_map, data_by_year, years)


def get_structured_resultat_syscohada_data(acheteur, years):
    """
    Récupère et structure les données du compte de résultat SYSCOHADA.
    """
    resultat_model = ResultatS
    data_by_year = {}
    for year in years:
        instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance
    structure_map = {
        "PRODUITS D'EXPLOITATION": [
            {'label': "Ventes de marchandises", 'key': 'ventes_marchandises_a'},
            {'label': "Ventes de produits manufacturés", 'key': 'ventes_produits_manufactures'},
            {'label': "Travaux, services vendus", 'key': 'travaux_services_vendus_c'},
            {'label': "Produits accessoires", 'key': 'produits_accessoires_d'},
            {'label': "Production stockée", 'key': 'production_stockee'},
            {'label': "Production immobilisée", 'key': 'production_immobilisee'},
            {'label': "Subventions d'exploitation", 'key': 'subvention_exploitation'},
            {'label': "Autres produits", 'key': 'autres_produits'},
            {'label': "Transfert de charges", 'key': 'transfert_charges_exploitation'},
            {'label': "TOTAL PRODUITS", 'key': 'chiffre_affaires', 'is_total': True},
        ],
        "CHARGES D'EXPLOITATION": [
            {'label': "Achats de marchandises", 'key': 'achats_marchandises'},
            {'label': "Variation des stocks de marchandises", 'key': 'variation_stock_marchandises'},
            {'label': "Achats de matières premières", 'key': 'achats_matieres_premieres_fournitures_connexes'},
            {'label': "Variation des stocks de matières premières", 'key': 'variation_stock_matieres_premieres_fournitures_connexes'},
            {'label': "Autres achats", 'key': 'autres_achats'},
            {'label': "Variation des stocks d'autres fournitures", 'key': 'variation_stock_autres_fournitures'},
            {'label': "Transports", 'key': 'transport'},
            {'label': "Services extérieurs", 'key': 'services_exterieurs'},
            {'label': "Impôts et taxes", 'key': 'impots_taxes'},
            {'label': "Autres charges", 'key': 'autres_depenses'},
            {'label': "Frais de personnel", 'key': 'frais_personnel'},
            {'label': "Reprises de dépréciations", 'key': 'reprise_depreciations_amortissements_provision_pertes_valeurs_p'},
            {'label': "Dotations aux amortissements", 'key': 'reprise_depreciations_amortissements_provision_pertes_valeurs_m'},
        ],
        "RÉSULTAT FINANCIER": [
            {'label': "Produits financiers", 'key': 'produits_financiers_assimiles'},
            {'label': "Reprises sur provisions", 'key': 'reprise_provision_perte_valeur'},
            {'label': "Transfert de charges financières", 'key': 'transfert_charges_financieres'},
            {'label': "Charges financières", 'key': 'charges_financieres_assimilees'},
            {'label': "Dotations aux provisions financières", 'key': 'dotations_provisions_depreciations_financieres'},
            {'label': "RÉSULTAT FINANCIER", 'key': 'resultat_financier', 'is_total': True},
        ],
        "RÉSULTAT EXCEPTIONNEL": [
            {'label': "Produits exceptionnels", 'key': 'produits_cession_immobilisations'},
            {'label': "Autres produits HAO", 'key': 'autres_produits_hao'},
            {'label': "Valeur comptable des cessions", 'key': 'valeur_comptable_cessions_actifs_immobilises'},
            {'label': "Autres charges HAO", 'key': 'autres_charges_hao'},
            {'label': "Participation des travailleurs", 'key': 'participation_travailleurs'},
            {'label': "Charge d'impôt sur le revenu", 'key': 'charge_impot_revenu'},
            {'label': "RÉSULTAT NET", 'key': 'resultat_net', 'is_final_total': True},
        ]
    }
    return _build_structured_data(structure_map, data_by_year, years)


def get_structured_ratios_syscohada_data_v1(acheteur, years):
    """
    Récupère et structure les ratios pour le bilan SYSCOHADA.
    """
    actif_model = ActifS
    passif_model = PassifS
    resultat_model = ResultatS
    ratios_by_year = {}
    for year in years:
        actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()

        if actif_instance and passif_instance and resultat_instance:
            ratios_by_year[year] = RatiosSyscohada(actif_instance, passif_instance, resultat_instance)
        else:
            ratios_by_year[year] = None

    structure_map = {
        "STRUCTURE FINANCIÈRE": [
            {'label': "Fonds de roulement", 'key': 'fonds_de_roulement'},
            {'label': "Autonomie financière", 'key': 'autonomie_financiere'},
        ],
        "LIQUIDITÉ": [
            {'label': "Liquidité générale", 'key': 'liquidite_general'},
        ],
        "RENTABILITÉ": [
            {'label': "Capacité d'autofinancement", 'key': 'cafsys'},
            {'label': "Rentabilité économique", 'key': 'excedent_brute_exploitation'},
        ],
        "GESTION": [
            {'label': "Rotation des stocks", 'key': 'rotation_stock'},
        ],
    }
    return _build_ratios_data(structure_map, ratios_by_year, years)


def get_structured_ratios_syscohada_data(acheteur, years):
    """
    Récupère et structure les ratios pour le bilan SYSCOHADA (version étendue)
    """
    actif_model = ActifS
    passif_model = PassifS
    resultat_model = ResultatS
    ratios_by_year = {}
    for year in years:
        actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()

        if actif_instance and passif_instance and resultat_instance:
            ratios_by_year[year] = RatiosSyscohada(actif_instance, passif_instance, resultat_instance)
        else:
            ratios_by_year[year] = None

    structure_map = {
        "STRUCTURE FINANCIÈRE": [
            {'label': "Fonds de roulement", 'key': 'fonds_de_roulement'},
            {'label': "Autonomie financière", 'key': 'autonomie_financiere'},
            {'label': "Ratio d'endettement", 'key': 'rotation_dendettement'},
            {'label': "Ratio dette/capitaux propres", 'key': 'rotation_dette_capitaux_propres'},
        ],
        "LIQUIDITÉ": [
            {'label': "Liquidité générale", 'key': 'liquidite_general'},
            {'label': "Liquidité réduite", 'key': 'liquidite_reduite'},
            {'label': "Liquidité immédiate", 'key': 'liquidite_immediate'},
            {'label': "Ratio courant", 'key': 'ratio_courant'},
        ],
        "RENTABILITÉ": [
            {'label': "Capacité d'autofinancement", 'key': 'cafsys'},
            {'label': "Marge nette", 'key': 'benefice_net_chiffre_affaire'},
            {'label': "ROE (Return on Equity)", 'key': 'benefice_net'},
            {'label': "Couverture des intérêts", 'key': 'ratio_des_couverture_des_interets'},
        ],
        "GESTION": [
            {'label': "Rotation des stocks (jours)", 'key': 'rotation_stock'},
            {'label': "Jours de collecte moyens", 'key': 'jour_collecte_moyens'},
            {'label': "Jours de paiement moyens", 'key': 'moyen_paiement'},
            {'label': "Rotation des créances", 'key': 'compte_debiteur'},
        ],
        "EFFICIENCE": [
            {'label': "Rotation de l'actif", 'key': 'rotation_actif'},
            {'label': "Turnover", 'key': 'turnover'},
            {'label': "EBITDA/Chiffre d'affaires", 'key': 'ebitda_chiffre_affaire'},
            {'label': "Ratio financier", 'key': 'ratio_financier'},
        ]
    }
    return _build_ratios_data(structure_map, ratios_by_year, years)

# Les methodes pour les graphiques
# La structure financiere
# La rentabilite
# Les delais
def get_charts_structure_financiere_syscohada_data(acheteur, years):
    """
    Génère les données pour le chart de structure financière SYSCOHADA
    """
    try:
        actif_model = ActifS
        passif_model = PassifS
        
        # Vérifier s'il y a des données
        has_data = False
        data_by_year = {}
        
        for year in years:
            actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            
            if actif_instance and passif_instance:
                data_by_year[year] = {
                    'actif': actif_instance,
                    'passif': passif_instance
                }
                has_data = True
            else:
                data_by_year[year] = None
        
        if not has_data:
            return None
        
        # Préparer les données
        labels = [str(year) for year in years]
        
        # Récupérer les données avec valeurs par défaut
        total_actif_data = []
        total_passif_data = []
        capitaux_propres_data = []
        dettes_long_terme_data = []
        dettes_court_terme_data = []
        
        for year in years:
            data = data_by_year.get(year)
            if data:
                actif = data['actif']
                passif = data['passif']
                
                total_actif_data.append(float(actif.total_actif) if actif.total_actif else 0.0)
                total_passif_data.append(float(passif.total_passifs) if passif.total_passifs else 0.0)
                capitaux_propres_data.append(float(passif.total_capitaux_propres_ressources_similaires) if passif.total_capitaux_propres_ressources_similaires else 0.0)
                dettes_long_terme_data.append(float(passif.total_dettes_financieres_ressources_similaires) if passif.total_dettes_financieres_ressources_similaires else 0.0)
                dettes_court_terme_data.append(float(passif.total_passifs_courants) if passif.total_passifs_courants else 0.0)
            else:
                total_actif_data.append(0.0)
                total_passif_data.append(0.0)
                capitaux_propres_data.append(0.0)
                dettes_long_terme_data.append(0.0)
                dettes_court_terme_data.append(0.0)
        
        # Normaliser les données (division par 1M pour meilleure lisibilité)
        total_actif_data = [x / 1000000 for x in total_actif_data]
        total_passif_data = [x / 1000000 for x in total_passif_data]
        capitaux_propres_data = [x / 1000000 for x in capitaux_propres_data]
        dettes_long_terme_data = [x / 1000000 for x in dettes_long_terme_data]
        dettes_court_terme_data = [x / 1000000 for x in dettes_court_terme_data]
        
        # Créer le graphique
        plt.figure(figsize=(12, 8))
        
        # Tracer les courbes
        plt.plot(labels, total_actif_data, label='Total Actif (M)', marker='o', linewidth=2, color='#1f77b4')
        plt.plot(labels, total_passif_data, label='Total Passif (M)', marker='s', linewidth=2, color='#ff7f0e')
        plt.plot(labels, capitaux_propres_data, label='Capitaux Propres (M)', marker='^', linewidth=2, color='#2ca02c')
        plt.plot(labels, dettes_long_terme_data, label='Dettes Long Terme (M)', marker='d', linewidth=2, color='#d62728')
        plt.plot(labels, dettes_court_terme_data, label='Dettes Court Terme (M)', marker='v', linewidth=2, color='#9467bd')
        
        # Personnaliser le graphique
        plt.title('Structure Financière SYSCOHADA', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Années', fontsize=12)
        plt.ylabel('Montants (M)', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_structure_financiere_syscohada_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_charts_rentabilite_financiere_syscohada_data_v1(acheteur, years):
    """
    Génère les données pour le chart de rentabilité financière SYSCOHADA
    """
    try:
        resultat_model = ResultatS
        actif_model = ActifS
        passif_model = PassifS
        
        # Vérifier s'il y a des données
        has_data = False
        data_by_year = {}
        
        for year in years:
            resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            
            if resultat_instance and actif_instance and passif_instance:
                ratios = RatiosSyscohada(actif_instance, passif_instance, resultat_instance)
                data_by_year[year] = {
                    'resultat': resultat_instance,
                    'ratios': ratios
                }
                has_data = True
            else:
                data_by_year[year] = None
        
        if not has_data:
            return None
        
        # Préparer les données
        labels = [str(year) for year in years]
        
        # Récupérer les données avec valeurs par défaut
        chiffre_affaires_data = []
        resultat_net_data = []
        marge_nette_data = []
        roe_data = []
        roa_data = []
        
        for year in years:
            data = data_by_year.get(year)
            if data:
                resultat = data['resultat']
                ratios = data['ratios']
                
                chiffre_affaires_data.append(float(resultat.chiffre_affaires) if resultat.chiffre_affaires else 0.0)
                resultat_net_data.append(float(resultat.resultat_net) if resultat.resultat_net else 0.0)
                
                # Calcul des ratios
                marge_nette = ratios.benefice_net_chiffre_affaire
                roe = ratios.benefice_net
                roa = ratios.resultat_net / float(actif_instance.total_actif) if actif_instance and actif_instance.total_actif else 0.0
                
                marge_nette_data.append(float(marge_nette) if marge_nette else 0.0)
                roe_data.append(float(roe) if roe else 0.0)
                roa_data.append(float(roa) if roa else 0.0)
            else:
                chiffre_affaires_data.append(0.0)
                resultat_net_data.append(0.0)
                marge_nette_data.append(0.0)
                roe_data.append(0.0)
                roa_data.append(0.0)
        
        # Normaliser les données financières
        chiffre_affaires_data = [x / 1000000 for x in chiffre_affaires_data]
        resultat_net_data = [x / 1000000 for x in resultat_net_data]
        
        # Créer le graphique avec deux axes y
        fig, ax1 = plt.subplots(figsize=(12, 8))
        
        # Axe principal pour les montants financiers
        ax1.plot(labels, chiffre_affaires_data, label='Chiffre d\'affaires (M)', marker='o', linewidth=2, color='#1f77b4')
        ax1.plot(labels, resultat_net_data, label='Résultat net (M)', marker='s', linewidth=2, color='#ff7f0e')
        
        ax1.set_xlabel('Années', fontsize=12)
        ax1.set_ylabel('Montants (M)', fontsize=12, color='black')
        ax1.tick_params(axis='y', labelcolor='black')
        ax1.grid(True, alpha=0.3)
        
        # Axe secondaire pour les ratios
        ax2 = ax1.twinx()
        ax2.plot(labels, marge_nette_data, label='Marge nette (%)', marker='^', linewidth=2, color='#2ca02c')
        ax2.plot(labels, roe_data, label='ROE (%)', marker='d', linewidth=2, color='#d62728')
        ax2.plot(labels, roa_data, label='ROA (%)', marker='v', linewidth=2, color='#9467bd')
        
        ax2.set_ylabel('Ratios (%)', fontsize=12, color='black')
        ax2.tick_params(axis='y', labelcolor='black')
        
        # Titre et légende
        plt.title('Rentabilité Financière SYSCOHADA', fontsize=16, fontweight='bold', pad=20)
        
        # Combiner les légendes des deux axes
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_rentabilite_financiere_syscohada_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_charts_rentabilite_financiere_syscohada_data(acheteur, years):
    """
    Génère les données pour le chart de rentabilité financière SYSCOHADA - VERSION CORRIGEE
    """
    try:
        resultat_model = ResultatS
        actif_model = ActifS
        passif_model = PassifS
        
        # Vérifier s'il y a des données
        has_data = False
        data_by_year = {}
        
        for year in years:
            resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            
            if resultat_instance and actif_instance and passif_instance:
                ratios = RatiosSyscohada(actif_instance, passif_instance, resultat_instance)
                data_by_year[year] = {
                    'resultat': resultat_instance,
                    'actif': actif_instance,
                    'passif': passif_instance,
                    'ratios': ratios
                }
                has_data = True
        
        if not has_data:
            print("Aucune donnée complète trouvée pour la rentabilité")
            return None
        
        # Préparer les données
        labels = [str(year) for year in years]
        
        # Récupérer les données avec valeurs par défaut et gestion d'erreurs
        chiffre_affaires_data = []
        resultat_net_data = []
        marge_nette_data = []
        roe_data = []
        roa_data = []
        ebitda_data = []
        
        for year in years:
            data = data_by_year.get(year)
            if data:
                resultat = data['resultat']
                actif = data['actif']
                ratios = data['ratios']
                
                # Chiffre d'affaires avec valeur par défaut
                ca = float(resultat.chiffre_affaires) if resultat.chiffre_affaires else 0.0
                chiffre_affaires_data.append(ca)
                
                # Résultat net avec valeur par défaut
                rn = float(resultat.resultat_net) if resultat.resultat_net else 0.0
                resultat_net_data.append(rn)
                
                # Marge nette (%) - gestion de division par zéro
                marge_nette = 0.0
                if ca != 0 and rn is not None:
                    marge_nette = (rn / ca) * 100
                marge_nette_data.append(marge_nette)
                
                # ROE (%) - Return on Equity
                roe = 0.0
                capitaux_propres = float(actif.total_actif) - (float(data['passif'].total_dettes_financieres_ressources_similaires or 0) + float(data['passif'].total_passifs_courants or 0))
                if capitaux_propres != 0 and rn is not None:
                    roe = (rn / capitaux_propres) * 100
                roe_data.append(roe)
                
                # ROA (%) - Return on Assets
                roa = 0.0
                total_actif_val = float(actif.total_actif) if actif.total_actif else 1.0
                if total_actif_val != 0 and rn is not None:
                    roa = (rn / total_actif_val) * 100
                roa_data.append(roa)
                
                # EBITDA
                ebitda_val = float(resultat.excedent_brute_exploitation) if resultat.excedent_brute_exploitation else 0.0
                ebitda_data.append(ebitda_val)
                
            else:
                # Valeurs par défaut si données manquantes
                chiffre_affaires_data.append(0.0)
                resultat_net_data.append(0.0)
                marge_nette_data.append(0.0)
                roe_data.append(0.0)
                roa_data.append(0.0)
                ebitda_data.append(0.0)
        
        # Vérifier s'il y a des données non nulles
        has_financial_data = any(x != 0 for x in chiffre_affaires_data)
        has_ratio_data = any(x != 0 for x in marge_nette_data + roe_data + roa_data)
        
        if not has_financial_data and not has_ratio_data:
            print("Toutes les données de rentabilité sont nulles")
            return None
        
        # Normaliser les données financières (division par 1000 pour meilleure lisibilité)
        chiffre_affaires_data = [x / 1000 for x in chiffre_affaires_data]
        resultat_net_data = [x / 1000 for x in resultat_net_data]
        ebitda_data = [x / 1000 for x in ebitda_data]
        
        # Créer le graphique avec deux axes y
        fig, ax1 = plt.subplots(figsize=(12, 8))
        
        # Axe principal pour les montants financiers
        line1 = ax1.plot(labels, chiffre_affaires_data, label='Chiffre d\'affaires (K)', marker='o', linewidth=2, color='#1f77b4')
        line2 = ax1.plot(labels, resultat_net_data, label='Résultat net (K)', marker='s', linewidth=2, color='#ff7f0e')
        line3 = ax1.plot(labels, ebitda_data, label='EBITDA (K)', marker='^', linewidth=2, color='#8c564b')
        
        ax1.set_xlabel('Années', fontsize=12)
        ax1.set_ylabel('Montants (K)', fontsize=12, color='black')
        ax1.tick_params(axis='y', labelcolor='black')
        ax1.grid(True, alpha=0.3)
        
        # Axe secondaire pour les ratios
        ax2 = ax1.twinx()
        line4 = ax2.plot(labels, marge_nette_data, label='Marge nette (%)', marker='d', linewidth=2, color='#2ca02c', linestyle='--')
        line5 = ax2.plot(labels, roe_data, label='ROE (%)', marker='v', linewidth=2, color='#d62728', linestyle='--')
        line6 = ax2.plot(labels, roa_data, label='ROA (%)', marker='*', linewidth=2, color='#9467bd', linestyle='--')
        
        ax2.set_ylabel('Ratios (%)', fontsize=12, color='black')
        ax2.tick_params(axis='y', labelcolor='black')
        
        # Titre et légende
        plt.title('Rentabilité Financière SYSCOHADA', fontsize=16, fontweight='bold', pad=20)
        
        # Combiner les légendes des deux axes
        lines = line1 + line2 + line3 + line4 + line5 + line6
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        print("Graphique de rentabilité généré avec succès")
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_rentabilite_financiere_syscohada_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_charts_delais_syscohada_data(acheteur, years):
    """
    Génère les données pour le chart des délais SYSCOHADA
    """
    try:
        actif_model = ActifS
        passif_model = PassifS
        resultat_model = ResultatS
        
        # Vérifier s'il y a des données
        has_data = False
        ratios_by_year = {}
        
        for year in years:
            actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            
            if actif_instance and passif_instance and resultat_instance:
                ratios = RatiosSyscohada(actif_instance, passif_instance, resultat_instance)
                ratios_by_year[year] = ratios
                has_data = True
            else:
                ratios_by_year[year] = None
        
        if not has_data:
            return None
        
        # Préparer les données
        labels = [str(year) for year in years]
        
        # Récupérer les données avec valeurs par défaut
        dso_data = []
        dpo_data = []
        rotation_stock_data = []
        rotation_creances_data = []
        liquidite_data = []
        
        for year in years:
            ratio = ratios_by_year.get(year)
            dso_data.append(float(ratio.jour_collecte_moyens) if ratio and ratio.jour_collecte_moyens is not None else 0.0)
            dpo_data.append(float(ratio.moyen_paiement) if ratio and ratio.moyen_paiement is not None else 0.0)
            rotation_stock_data.append(float(ratio.rotation_stock) if ratio and ratio.rotation_stock is not None else 0.0)
            rotation_creances_data.append(float(ratio.compte_debiteur) if ratio and ratio.compte_debiteur is not None else 0.0)
            liquidite_data.append(float(ratio.liquidite_general) if ratio and ratio.liquidite_general is not None else 0.0)
        
        # Créer le graphique
        plt.figure(figsize=(12, 8))
        
        # Tracer les courbes
        plt.plot(labels, dso_data, label='Jours de collecte moyens', marker='o', linewidth=2, color='#1f77b4')
        plt.plot(labels, dpo_data, label='Jours de paiement moyens', marker='s', linewidth=2, color='#ff7f0e')
        plt.plot(labels, rotation_stock_data, label='Rotation des stocks (jours)', marker='^', linewidth=2, color='#2ca02c')
        plt.plot(labels, rotation_creances_data, label='Rotation des créances', marker='d', linewidth=2, color='#d62728')
        plt.plot(labels, liquidite_data, label='Liquidité générale', marker='v', linewidth=2, color='#9467bd')
        
        # Personnaliser le graphique
        plt.title('Délais et Rotation SYSCOHADA', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Années', fontsize=12)
        plt.ylabel('Valeurs', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_delais_syscohada_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


#############################################################
#
# Fonctions pour le bilan IFRS COBAC
#
############################################################# 
def get_structured_actif_ifrs_data(acheteur, years):
    """
    Récupère et structure les données d'actif pour le bilan IFRS.
    """
    actif_model = ActifIFRS
    data_by_year = {}
    for year in years:
        instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance

    structure_map = {
        "NON-CURRENT ASSETS": [
            {'label': "Goodwill", 'key': 'goodwill'},
            {'label': "Intangible assets", 'key': 'marques_et_droits_auteur'},
            {'label': "Property, plant and equipment", 'key': 'terrains'},
            {'label': "Financial assets", 'key': 'participations_dans_des_societes'},
            {'label': "Long-term loans", 'key': 'prets_a_long_terme'},
            {'label': "TOTAL NON-CURRENT ASSETS", 'key': 'total_actif_non_courant', 'is_total': True},
        ],
        "CURRENT ASSETS": [
            {'label': "Inventories", 'key': 'matieres_premieres'},
            {'label': "Trade receivables", 'key': 'creances_a_court_terme'},
            {'label': "Other receivables", 'key': 'creances_diverses'},
            {'label': "Cash and cash equivalents", 'key': 'disponibilites_bancaires'},
            {'label': "TOTAL CURRENT ASSETS", 'key': 'total_actif_courant', 'is_total': True},
        ],
        "TOTAL ASSETS": [
            {'label': "TOTAL ASSETS", 'key': 'total_actif', 'is_final_total': True},
        ]
    }

    return _build_structured_data(structure_map, data_by_year, years)


def get_structured_passif_ifrs_data(acheteur, years):
    """
    Récupère et structure les données de passif pour le bilan IFRS.
    """
    passif_model = PassifIFRS
    data_by_year = {}
    for year in years:
        instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance

    structure_map = {
        "SHAREHOLDERS' EQUITY": [
            {'label': "Share capital", 'key': 'capital_social'},
            {'label': "Reserves", 'key': 'reserves_legales'},
            {'label': "Retained earnings", 'key': 'resultat_net_reporte'},
            {'label': "TOTAL EQUITY", 'key': 'total_capitaux_propres', 'is_total': True},
        ],
        "NON-CURRENT LIABILITIES": [
            {'label': "Long-term borrowings", 'key': 'emprunts_bancaires_long_terme'},
            {'label': "Provisions", 'key': 'provisions_pour_retraites_et_pensions'},
            {'label': "TOTAL NON-CURRENT LIABILITIES", 'key': 'total_passif_non_courant', 'is_total': True},
        ],
        "CURRENT LIABILITIES": [
            {'label': "Trade payables", 'key': 'dettes_fournisseurs_a_court_terme'},
            {'label': "Tax liabilities", 'key': 'impots_sur_le_revenu'},
            {'label': "Short-term borrowings", 'key': 'emprunts_bancaires_court_terme'},
            {'label': "TOTAL CURRENT LIABILITIES", 'key': 'total_passif_courant', 'is_total': True},
        ],
        "TOTAL LIABILITIES AND EQUITY": [
            {'label': "TOTAL LIABILITIES AND EQUITY", 'key': 'total_passif', 'is_final_total': True},
        ]
    }

    return _build_structured_data(structure_map, data_by_year, years)


def get_structured_resultat_ifrs_data(acheteur, years):
    """
    Récupère et structure les données du compte de résultat IFRS COBAC.
    """
    resultat_model = ResultatIFRS
    data_by_year = {}
    for year in years:
        instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance
        print(f"Résultat IFRS pour l'année {year}: {instance}")
        
    # Vérifiez que les données sont bien présentes
    print(f"Données par année: {data_by_year}")
    
    structure_map = {
        "PRODUITS": [
            {'label': "Ventes de biens", 'key': 'ventes_biens'},
            {'label': "Ventes de services", 'key': 'ventes_services'},
            {'label': "Subventions d'exploitation", 'key': 'subventions_exploitation'},
            {'label': "Revenus exceptionnels", 'key': 'revenus_exceptionnels'},
            {'label': "Revenus financiers", 'key': 'revenus_financiers'},
            {'label': "TOTAL PRODUITS", 'key': 'total_produits', 'is_total': True},
        ],
        "CHARGES": [
            {'label': "Achats de matières premières", 'key': 'achats_matieres_premieres'},
            {'label': "Autres coûts directs", 'key': 'autres_couts_directs'},
            {'label': "Salaires et charges sociales", 'key': 'salaires_et_charges_sociales'},
            {'label': "Loyer et charges locatives", 'key': 'loyer_et_charges_locatives'},
            {'label': "Autres charges d'exploitation", 'key': 'autres_charges_exploitation'},
            {'label': "Amortissement des immobilisations", 'key': 'amortissement_des_immobilisations'},
            {'label': "Provisions pour risques et charges", 'key': 'provisions_pour_risques_et_charges'},
            {'label': "Charges financières", 'key': 'charges_financieres'},
            {'label': "Impôt sur les sociétés", 'key': 'impot_sur_les_societes'},
            {'label': "TOTAL CHARGES", 'key': 'total_charges', 'is_total': True},
        ],
        "RÉSULTATS": [
            {'label': "Résultat opérationnel", 'key': 'resultat_operationnel'},
            {'label': "Résultat financier", 'key': 'resultat_financier'},
            {'label': "Résultat avant impôt", 'key': 'resultat_avant_impot'},
            {'label': "Résultat net", 'key': 'resultat_net', 'is_final_total': True},
        ]
    }
    return _build_structured_data(structure_map, data_by_year, years)


def get_structured_ratios_ifrs_data(acheteur, years):
    """
    Récupère et structure les ratios pour le bilan IFRS COBAC.
    """
    actif_model = ActifIFRS
    passif_model = PassifIFRS
    resultat_model = ResultatIFRS
    ratios_by_year = {}
    for year in years:
        actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()

        if actif_instance and passif_instance and resultat_instance:
            ratios_by_year[year] = RatiosIFRS(actif=actif_instance, passif=passif_instance, resultat=resultat_instance)
        else:
            ratios_by_year[year] = None

    structure_map = {
        "RENTABILITÉ": [
            {'label': "Return on Assets (ROA)", 'key': 'roa'},
            {'label': "Return on Equity (ROE)", 'key': 'roe'},
        ],
        "LIQUIDITÉ": [
            {'label': "Liquidité générale", 'key': 'liquidite_generale'},
            {'label': "Liquidité immédiate", 'key': 'liquidite_immediate'},
        ],
        "SOLVABILITÉ": [
            {'label': "Ratio d'endettement", 'key': 'ratio_endettement_total'},
            {'label': "Ratio de couverture des intérêts", 'key': 'ratio_couverture_interets'},
        ],
        "RENTABILITÉ DES VENTES": [
            {'label': "Marge brute", 'key': 'marge_brute'},
            {'label': "Marge opérationnelle", 'key': 'marge_operationnelle'},
            {'label': "Marge nette", 'key': 'marge_nette'},
        ],
        "GESTION": [
            {'label': "Rotation des actifs", 'key': 'rotation_des_actifs'},
            {'label': "DSO (Days Sales Outstanding)", 'key': 'dso'},
        ],
    }
    return _build_ratios_data(structure_map, ratios_by_year, years)


# Les graphiques ici !
def get_charts_structure_financiere_ifrs_data(acheteur, years):
    """
    Génère les données pour le chart de structure financière IFRS COBAC
    """
    try:
        actif_model = ActifIFRS
        passif_model = PassifIFRS
        
        # Vérifier s'il y a des données
        has_data = False
        data_by_year = {}
        
        for year in years:
            actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            
            if actif_instance and passif_instance:
                data_by_year[year] = {
                    'actif': actif_instance,
                    'passif': passif_instance
                }
                has_data = True
            else:
                data_by_year[year] = None
        
        if not has_data:
            print("Aucune donnée complète trouvée pour la structure financière IFRS")
            return None
        
        # Préparer les données
        labels = [str(year) for year in years]
        
        # Récupérer les données avec valeurs par défaut
        total_actif_data = []
        total_passif_data = []
        capitaux_propres_data = []
        actif_non_courant_data = []
        actif_courant_data = []
        passif_non_courant_data = []
        passif_courant_data = []
        
        for year in years:
            data = data_by_year.get(year)
            if data:
                actif = data['actif']
                passif = data['passif']
                
                total_actif_data.append(float(actif.total_actif) if actif.total_actif else 0.0)
                total_passif_data.append(float(passif.total_passif) if passif.total_passif else 0.0)
                capitaux_propres_data.append(float(passif.total_capitaux_propres) if passif.total_capitaux_propres else 0.0)
                actif_non_courant_data.append(float(actif.total_actif_non_courant) if actif.total_actif_non_courant else 0.0)
                actif_courant_data.append(float(actif.total_actif_courant) if actif.total_actif_courant else 0.0)
                passif_non_courant_data.append(float(passif.total_passif_non_courant) if passif.total_passif_non_courant else 0.0)
                passif_courant_data.append(float(passif.total_passif_courant) if passif.total_passif_courant else 0.0)
            else:
                total_actif_data.append(0.0)
                total_passif_data.append(0.0)
                capitaux_propres_data.append(0.0)
                actif_non_courant_data.append(0.0)
                actif_courant_data.append(0.0)
                passif_non_courant_data.append(0.0)
                passif_courant_data.append(0.0)
        
        # Normaliser les données (division par 1M pour meilleure lisibilité)
        total_actif_data = [x / 1000000 for x in total_actif_data]
        total_passif_data = [x / 1000000 for x in total_passif_data]
        capitaux_propres_data = [x / 1000000 for x in capitaux_propres_data]
        actif_non_courant_data = [x / 1000000 for x in actif_non_courant_data]
        actif_courant_data = [x / 1000000 for x in actif_courant_data]
        passif_non_courant_data = [x / 1000000 for x in passif_non_courant_data]
        passif_courant_data = [x / 1000000 for x in passif_courant_data]
        
        # Créer le graphique
        plt.figure(figsize=(14, 8))
        
        # Tracer les courbes principales
        plt.plot(labels, total_actif_data, label='Total Assets (M)', marker='o', linewidth=3, color='#1f77b4')
        plt.plot(labels, total_passif_data, label='Total Liabilities & Equity (M)', marker='s', linewidth=3, color='#ff7f0e')
        plt.plot(labels, capitaux_propres_data, label='Shareholders Equity (M)', marker='^', linewidth=2, color='#2ca02c')
        
        # Tracer les sous-composantes
        plt.plot(labels, actif_non_courant_data, label='Non-Current Assets (M)', marker='d', linewidth=2, color='#1f77b4', linestyle='--', alpha=0.7)
        plt.plot(labels, actif_courant_data, label='Current Assets (M)', marker='v', linewidth=2, color='#1f77b4', linestyle=':', alpha=0.7)
        plt.plot(labels, passif_non_courant_data, label='Non-Current Liabilities (M)', marker='<', linewidth=2, color='#ff7f0e', linestyle='--', alpha=0.7)
        plt.plot(labels, passif_courant_data, label='Current Liabilities (M)', marker='>', linewidth=2, color='#ff7f0e', linestyle=':', alpha=0.7)
        
        # Personnaliser le graphique
        plt.title('IFRS Financial Structure Analysis', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Years', fontsize=12)
        plt.ylabel('Amounts (M)', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        print("Graphique de structure financière IFRS généré avec succès")
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_structure_financiere_ifrs_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_charts_rentabilite_financiere_ifrs_data(acheteur, years):
    """
    Génère les données pour le chart de rentabilité financière IFRS COBAC
    """
    try:
        resultat_model = ResultatIFRS
        actif_model = ActifIFRS
        passif_model = PassifIFRS
        
        # Vérifier s'il y a des données
        has_data = False
        data_by_year = {}
        
        for year in years:
            resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            
            if resultat_instance and actif_instance and passif_instance:
                ratios = RatiosIFRS(actif=actif_instance, passif=passif_instance, resultat=resultat_instance)
                data_by_year[year] = {
                    'resultat': resultat_instance,
                    'actif': actif_instance,
                    'passif': passif_instance,
                    'ratios': ratios
                }
                has_data = True
            else:
                data_by_year[year] = None
        
        if not has_data:
            print("Aucune donnée complète trouvée pour la rentabilité IFRS")
            return None
        
        # Préparer les données
        labels = [str(year) for year in years]
        
        # Récupérer les données avec valeurs par défaut et gestion d'erreurs
        chiffre_affaires_data = []
        resultat_net_data = []
        resultat_operationnel_data = []
        roa_data = []
        roe_data = []
        marge_nette_data = []
        marge_operationnelle_data = []
        
        for year in years:
            data = data_by_year.get(year)
            if data:
                resultat = data['resultat']
                actif = data['actif']
                ratios = data['ratios']
                
                # Données financières
                ca = float(resultat.chiffre_affaires) if resultat.chiffre_affaires else 0.0
                rn = float(resultat.resultat_net) if resultat.resultat_net else 0.0
                ro = float(resultat.resultat_operationnel) if resultat.resultat_operationnel else 0.0
                
                chiffre_affaires_data.append(ca)
                resultat_net_data.append(rn)
                resultat_operationnel_data.append(ro)
                
                # Ratios avec gestion d'erreurs
                roa_val = float(ratios.roa) if ratios.roa is not None else 0.0
                roe_val = float(ratios.roe) if ratios.roe is not None else 0.0
                marge_nette_val = float(ratios.marge_nette) if ratios.marge_nette is not None else 0.0
                marge_operationnelle_val = float(ratios.marge_operationnelle) if ratios.marge_operationnelle is not None else 0.0
                
                roa_data.append(roa_val)
                roe_data.append(roe_val)
                marge_nette_data.append(marge_nette_val)
                marge_operationnelle_data.append(marge_operationnelle_val)
                
            else:
                # Valeurs par défaut si données manquantes
                chiffre_affaires_data.append(0.0)
                resultat_net_data.append(0.0)
                resultat_operationnel_data.append(0.0)
                roa_data.append(0.0)
                roe_data.append(0.0)
                marge_nette_data.append(0.0)
                marge_operationnelle_data.append(0.0)
        
        # Vérifier s'il y a des données non nulles
        has_financial_data = any(x != 0 for x in chiffre_affaires_data)
        has_ratio_data = any(x != 0 for x in roa_data + roe_data + marge_nette_data)
        
        if not has_financial_data and not has_ratio_data:
            print("Toutes les données de rentabilité IFRS sont nulles")
            return None
        
        # Normaliser les données financières (division par 1000 pour meilleure lisibilité)
        chiffre_affaires_data = [x / 1000 for x in chiffre_affaires_data]
        resultat_net_data = [x / 1000 for x in resultat_net_data]
        resultat_operationnel_data = [x / 1000 for x in resultat_operationnel_data]
        
        # Créer le graphique avec deux axes y
        fig, ax1 = plt.subplots(figsize=(14, 8))
        
        # Axe principal pour les montants financiers
        line1 = ax1.plot(labels, chiffre_affaires_data, label='Revenue (K)', marker='o', linewidth=3, color='#1f77b4')
        line2 = ax1.plot(labels, resultat_net_data, label='Net Income (K)', marker='s', linewidth=3, color='#ff7f0e')
        line3 = ax1.plot(labels, resultat_operationnel_data, label='Operating Income (K)', marker='^', linewidth=2, color='#8c564b')
        
        ax1.set_xlabel('Years', fontsize=12)
        ax1.set_ylabel('Amounts (K)', fontsize=12, color='black')
        ax1.tick_params(axis='y', labelcolor='black')
        ax1.grid(True, alpha=0.3)
        
        # Axe secondaire pour les ratios
        ax2 = ax1.twinx()
        line4 = ax2.plot(labels, roa_data, label='ROA (%)', marker='d', linewidth=2, color='#2ca02c', linestyle='--')
        line5 = ax2.plot(labels, roe_data, label='ROE (%)', marker='v', linewidth=2, color='#d62728', linestyle='--')
        line6 = ax2.plot(labels, marge_nette_data, label='Net Margin (%)', marker='*', linewidth=2, color='#9467bd', linestyle='--')
        line7 = ax2.plot(labels, marge_operationnelle_data, label='Operating Margin (%)', marker='p', linewidth=2, color='#e377c2', linestyle='--')
        
        ax2.set_ylabel('Ratios (%)', fontsize=12, color='black')
        ax2.tick_params(axis='y', labelcolor='black')
        
        # Titre et légende
        plt.title('IFRS Profitability Analysis', fontsize=16, fontweight='bold', pad=20)
        
        # Combiner les légendes des deux axes
        lines = line1 + line2 + line3 + line4 + line5 + line6 + line7
        labels_legend = [l.get_label() for l in lines]
        ax1.legend(lines, labels_legend, bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        print("Graphique de rentabilité IFRS généré avec succès")
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_rentabilite_financiere_ifrs_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_charts_delais_ifrs_data(acheteur, years):
    """
    Génère les données pour le chart des délais et gestion IFRS COBAC
    """
    try:
        actif_model = ActifIFRS
        passif_model = PassifIFRS
        resultat_model = ResultatIFRS
        
        # Vérifier s'il y a des données
        has_data = False
        ratios_by_year = {}
        
        for year in years:
            actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            
            if actif_instance and passif_instance and resultat_instance:
                ratios = RatiosIFRS(actif=actif_instance, passif=passif_instance, resultat=resultat_instance)
                ratios_by_year[year] = ratios
                has_data = True
            else:
                ratios_by_year[year] = None
        
        if not has_data:
            print("Aucune donnée complète trouvée pour les délais IFRS")
            return None
        
        # Préparer les données
        labels = [str(year) for year in years]
        
        # Récupérer les données avec valeurs par défaut
        dso_data = []
        liquidite_generale_data = []
        liquidite_immediate_data = []
        rotation_actifs_data = []
        ratio_endettement_data = []
        couverture_interets_data = []
        
        for year in years:
            ratio = ratios_by_year.get(year)
            if ratio:
                dso_data.append(float(ratio.dso) if ratio.dso is not None else 0.0)
                liquidite_generale_data.append(float(ratio.liquidite_generale) if ratio.liquidite_generale is not None else 0.0)
                liquidite_immediate_data.append(float(ratio.liquidite_immediate) if ratio.liquidite_immediate is not None else 0.0)
                rotation_actifs_data.append(float(ratio.rotation_des_actifs) if ratio.rotation_des_actifs is not None else 0.0)
                ratio_endettement_data.append(float(ratio.ratio_endettement_total) if ratio.ratio_endettement_total is not None else 0.0)
                couverture_interets_data.append(float(ratio.ratio_couverture_interets) if ratio.ratio_couverture_interets is not None else 0.0)
            else:
                dso_data.append(0.0)
                liquidite_generale_data.append(0.0)
                liquidite_immediate_data.append(0.0)
                rotation_actifs_data.append(0.0)
                ratio_endettement_data.append(0.0)
                couverture_interets_data.append(0.0)
        
        # Vérifier s'il y a des données non nulles
        has_ratio_data = any(x != 0 for x in dso_data + liquidite_generale_data + rotation_actifs_data)
        
        if not has_ratio_data:
            print("Toutes les données de délais IFRS sont nulles")
            return None
        
        # Créer le graphique avec deux axes y pour différentes échelles
        fig, ax1 = plt.subplots(figsize=(14, 8))
        
        # Axe principal pour les ratios de liquidité et rotation
        line1 = ax1.plot(labels, liquidite_generale_data, label='Current Ratio', marker='o', linewidth=3, color='#1f77b4')
        line2 = ax1.plot(labels, liquidite_immediate_data, label='Quick Ratio', marker='s', linewidth=3, color='#ff7f0e')
        line3 = ax1.plot(labels, rotation_actifs_data, label='Asset Turnover (%)', marker='^', linewidth=2, color='#2ca02c')
        
        ax1.set_xlabel('Years', fontsize=12)
        ax1.set_ylabel('Ratio Values', fontsize=12, color='black')
        ax1.tick_params(axis='y', labelcolor='black')
        ax1.grid(True, alpha=0.3)
        
        # Axe secondaire pour DSO et ratio d'endettement
        ax2 = ax1.twinx()
        line4 = ax2.plot(labels, dso_data, label='DSO (Days)', marker='d', linewidth=2, color='#d62728', linestyle='--')
        line5 = ax2.plot(labels, ratio_endettement_data, label='Debt Ratio (%)', marker='v', linewidth=2, color='#9467bd', linestyle='--')
        line6 = ax2.plot(labels, couverture_interets_data, label='Interest Coverage', marker='*', linewidth=2, color='#8c564b', linestyle='--')
        
        ax2.set_ylabel('Days / % / Times', fontsize=12, color='black')
        ax2.tick_params(axis='y', labelcolor='black')
        
        # Titre et légende
        plt.title('IFRS Liquidity & Efficiency Analysis', fontsize=16, fontweight='bold', pad=20)
        
        # Combiner les légendes des deux axes
        lines = line1 + line2 + line3 + line4 + line5 + line6
        labels_legend = [l.get_label() for l in lines]
        ax1.legend(lines, labels_legend, bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        print("Graphique des délais IFRS généré avec succès")
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_delais_ifrs_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None




#############################################################
#
# Fonctions pour le bilan Anglais
#
############################################################# 
def get_structured_actif_anglais_data(acheteur, years):
    """
    Récupère et structure les données d'actif pour le bilan anglais.
    """
    actif_model = ActifA
    data_by_year = {}
    for year in years:
        instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance

    structure_map = {
        "NON-CURRENT ASSETS": [
            {'label': "Property, plant and equipment",                    'key': 'biens_installations_equipements'},
            {'label': "Right-of-use assets",                              'key': 'droit_utilisation'},
            {'label': "Intangible assets",                                'key': 'immobilisations_incorporelles'},
            {'label': "Goodwill",                                         'key': 'goodwill'},
            {'label': "Deferred tax assets",                              'key': 'actif_impot_differe'},
            {'label': "Investment in associates",                         'key': 'investissements_associes'},
            {'label': "Loans receivable (non-current)",                   'key': 'creances_pret_non_courant'},
            {'label': "Financial assets at fair value through P&L",       'key': 'actifs_financiers_juste_valeur_resultat'},
            {'label': "TOTAL NON-CURRENT ASSETS",                        'key': 'total_actifs_non_courants', 'is_total': True},
        ],
        "CURRENT ASSETS": [
            {'label': "Inventory",                                        'key': 'inventaire'},
            {'label': "Trade and other receivables",                      'key': 'creances_commerciales_autres_creances'},
            {'label': "Income tax receivable",                            'key': 'actif_impots_courant'},
            {'label': "Loans receivable (current)",                       'key': 'creances_pret_courant'},
            {'label': "Cash and cash equivalents",                        'key': 'caisses_banques'},
            {'label': "Derivative financial assets",                      'key': 'actifs_financiers_derives'},
            {'label': "TOTAL CURRENT ASSETS",                            'key': 'total_actif_circulant', 'is_total': True},
        ],
        "TOTAL ASSETS": [
            {'label': "TOTAL ASSETS",                                     'key': 'total_actif', 'is_final_total': True},
        ]
    }

    return _build_structured_data(structure_map, data_by_year, years)

def get_structured_passif_anglais_data(acheteur, years):
    """
    Récupère et structure les données de passif pour le bilan anglais.
    """
    passif_model = PassifA
    data_by_year = {}
    for year in years:
        instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance

    structure_map = {
        "SHAREHOLDERS' EQUITY": [
            {'label': "Share capital",                                    'key': 'capital_social'},
            {'label': "Share premium",                                    'key': 'prime_emission'},
            {'label': "Cash flow hedge reserve",                          'key': 'reserve_couverture_tresorerie'},
            {'label': "Cost of hedging reserve",                          'key': 'reserve_cout_couverture'},
            {'label': "Foreign currency translation reserve",             'key': 'reserve_conversion_devise'},
            {'label': "Retained earnings",                                'key': 'benefices_non_distribues'},
            {'label': "Net result of the year",                           'key': 'resultat_net_exercice'},
            {'label': "Distributable reserve",                            'key': 'reserve_distribuable'},
            {'label': "TOTAL EQUITY",                                     'key': 'total_fonds_propres', 'is_total': True},
        ],
        "NON-CURRENT LIABILITIES": [
            {'label': "Financial debts (bank loan)",                      'key': 'dettes_financieres_pret_bancaire'},
            {'label': "Long term trade liabilities",                      'key': 'dettes_commerciales_long_terme'},
            {'label': "Directors current account",                        'key': 'compte_courant_administrateurs'},
            {'label': "Long term provisions",                             'key': 'provisions_long_terme'},
            {'label': "Other long term liabilities",                      'key': 'autres_passifs_long_terme'},
            {'label': "TOTAL NON-CURRENT LIABILITIES",                   'key': 'total_passif_long_terme', 'is_total': True},
        ],
        "CURRENT LIABILITIES": [
            {'label': "Trade and other payables",                         'key': 'dettes_commerciales_autres_dettes'},
            {'label': "Lease liabilities",                                'key': 'dettes_location'},
            {'label': "Employee benefits",                                'key': 'avantages_employes'},
            {'label': "Income tax payable",                               'key': 'impots'},
            {'label': "Derivative financial liabilities",                 'key': 'passifs_financiers_derives'},
            {'label': "TOTAL CURRENT LIABILITIES",                       'key': 'total_passif_circulant', 'is_total': True},
        ],
        "TOTAL EQUITY AND LIABILITIES": [
            {'label': "TOTAL EQUITY AND LIABILITIES",                    'key': 'total_capitaux_propres_et_passif', 'is_final_total': True},
        ]
    }

    return _build_structured_data(structure_map, data_by_year, years)

def get_structured_resultat_anglais_data(acheteur, years):
    """
    Récupère et structure les données du compte de résultat anglais.
    """
    resultat_model = ResultatA
    data_by_year = {}
    for year in years:
        instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance

    structure_map = {
        "REVENUE": [
            {'label': "Revenue from ordinary activities", 'key': 'produits_activites_ordinaires'},
            {'label': "Sales", 'key': 'ventes'},
            {'label': "GROSS PROFIT", 'key': 'marge_brute', 'is_total': True},
        ],
        "OPERATING EXPENSES": [
            {'label': "Cost of sales", 'key': 'charges_exploitation'},
            {'label': "Selling, general and administrative expenses", 'key': 'frais_vente_generaux_administratifs'},
            {'label': "OPERATING PROFIT", 'key': 'resultat_exploitation', 'is_total': True},
        ],
        "OTHER ITEMS": [
            {'label': "Other income", 'key': 'autres_revenus'},
            {'label': "Finance costs", 'key': 'frais_financier'},
            {'label': "PROFIT BEFORE TAX", 'key': 'resultat_avant_impots', 'is_total': True},
        ],
        "TAXATION AND NET PROFIT": [
            {'label': "Income tax expense", 'key': 'charge_impot_sur_revenu'},
            {'label': "NET PROFIT FOR THE YEAR", 'key': 'resultat_net', 'is_final_total': True},
        ]
    }

    return _build_structured_data(structure_map, data_by_year, years)

def get_structured_ratios_anglais_data_v1(acheteur, years):
    """
    Récupère et structure les ratios pour le bilan anglais.
    """
    actif_model = ActifA
    passif_model = PassifA
    resultat_model = ResultatA

    ratios_by_year = {}
    for year in years:
        actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        
        if actif_instance and passif_instance and resultat_instance:
            ratios_by_year[year] = RatiosAnglais(actif_instance, passif_instance, resultat_instance)
        else:
            ratios_by_year[year] = None

    structure_map = {
        "FINANCIAL STRUCTURE": [
            {'label': "Solvency", 'key': 'solvabilite'},
            {'label': "Financial autonomy", 'key': 'autonomie_financiere'},
        ],
        "LIQUIDITY": [
            {'label': "Current ratio", 'key': 'liquidite_generale'},
        ],
        "PROFITABILITY": [
            {'label': "Return on equity", 'key': 'rendement_capitaux_propres'},
            {'label': "Net profit margin", 'key': 'taux_marge_net'},
        ],
        "MANAGEMENT": [
            {'label': "Days sales outstanding", 'key': 'jour_recouvrement_moyen'},
            {'label': "Days payable outstanding", 'key': 'jour_paiement_moyen'},
        ],
    }

    return _build_ratios_data(structure_map, ratios_by_year, years)

def get_structured_ratios_anglais_data(acheteur, years):
    """
    Récupère et structure les ratios pour le bilan anglais.
    """
    actif_model = ActifA
    passif_model = PassifA
    resultat_model = ResultatA

    ratios_by_year = {}
    for year in years:
        actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        
        if actif_instance and passif_instance and resultat_instance:
            ratios_by_year[year] = RatiosAnglais(actif_instance, passif_instance, resultat_instance)
        else:
            ratios_by_year[year] = None

    structure_map = {
        "FINANCIAL STRUCTURE": [
            {'label': "Solvency", 'key': 'solvabilite'},
            {'label': "Financial autonomy", 'key': 'autonomie_financiere'},
            {'label': "Debt ratio 1", 'key': 'ratio_endettement1'},
            {'label': "Debt ratio 2", 'key': 'ratio_endettement2'},
        ],
        "LIQUIDITY": [
            {'label': "Current ratio", 'key': 'liquidite_generale'},
            {'label': "Quick ratio", 'key': 'liquidite_reduite'},
        ],
        "PROFITABILITY": [
            {'label': "Return on equity (ROE)", 'key': 'rendement_capitaux_propres'},
            {'label': "Net profit margin", 'key': 'taux_marge_net'},
            {'label': "Interest coverage", 'key': 'ratios_couverture_interet'},
        ],
        "EFFICIENCY": [
            {'label': "Days sales outstanding", 'key': 'jour_recouvrement_moyen'},
            {'label': "Days payable outstanding", 'key': 'jour_paiement_moyen'},
            {'label': "Receivables turnover", 'key': 'taux_rotation_creance'},
            {'label': "Inventory turnover", 'key': 'taux_rotation_stock'},
            {'label': "Asset turnover", 'key': 'taux_rotation_actif'},
        ],
    }

    return _build_ratios_data(structure_map, ratios_by_year, years)

################################################################
#
# Fonctions pour les graphiques anglais
#
################################################################
def get_charts_structure_financiere_anglais_data(acheteur, years):
    """
    Génère les données pour le chart de structure financière anglais AVEC GESTION D'ERREURS
    """
    try:
        actif_model = ActifA
        passif_model = PassifA
        resultat_model = ResultatA
        
        # Vérifier s'il y a des données
        has_data = False
        ratios_by_year = {}
        
        for year in years:
            actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            
            if actif_instance and passif_instance and resultat_instance:
                ratios = RatiosAnglais(actif_instance, passif_instance, resultat_instance)
                ratios_by_year[year] = ratios
                has_data = True
            else:
                ratios_by_year[year] = None
        
        if not has_data:
            return None
        
        # Préparer les données
        labels = [str(year) for year in years]
        
        # Récupérer les données avec valeurs par défaut
        solv_data = []
        auton_data = []
        debt1_data = []
        debt2_data = []
        cr_data = []
        
        for year in years:
            ratio = ratios_by_year.get(year)
            solv_data.append(float(ratio.solvabilite) if ratio and ratio.solvabilite is not None else 0.0)
            auton_data.append(float(ratio.autonomie_financiere) if ratio and ratio.autonomie_financiere is not None else 0.0)
            debt1_data.append(float(ratio.ratio_endettement1) if ratio and ratio.ratio_endettement1 is not None else 0.0)
            debt2_data.append(float(ratio.ratio_endettement2) if ratio and ratio.ratio_endettement2 is not None else 0.0)
            cr_data.append(float(ratio.liquidite_generale) if ratio and ratio.liquidite_generale is not None else 0.0)
        
        # Créer le graphique
        plt.figure(figsize=(12, 8))
        
        # Tracer les courbes
        plt.plot(labels, solv_data, label='SOLV - Solvency (Equity/Assets)', marker='o', linewidth=2, color='#1f77b4')
        plt.plot(labels, auton_data, label='AUTON - Financial Autonomy', marker='s', linewidth=2, color='#ff7f0e')
        plt.plot(labels, debt1_data, label='DEBT1 - Debt Ratio 1', marker='^', linewidth=2, color='#2ca02c')
        plt.plot(labels, debt2_data, label='DEBT2 - Debt Ratio 2', marker='d', linewidth=2, color='#d62728')
        plt.plot(labels, cr_data, label='CR - Current Ratio', marker='v', linewidth=2, color='#9467bd')
        
        # Personnaliser le graphique
        plt.title('Financial Structure', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Years', fontsize=12)
        plt.ylabel('Ratio Values', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_structure_financiere_anglais_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None



def get_charts_rentabilite_financiere_anglais_data(acheteur, years):
    """
    Génère les données pour le chart de rentabilité financière anglais AVEC GESTION D'ERREURS
    """
    try:
        actif_model = ActifA
        passif_model = PassifA
        resultat_model = ResultatA
        
        # Vérifier s'il y a des données
        has_data = False
        ratios_by_year = {}
        data_by_year = {}
        
        for year in years:
            actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            
            if actif_instance and passif_instance and resultat_instance:
                ratios = RatiosAnglais(actif_instance, passif_instance, resultat_instance)
                ratios_by_year[year] = ratios
                data_by_year[year] = resultat_instance
                has_data = True
            else:
                ratios_by_year[year] = None
                data_by_year[year] = None
        
        if not has_data:
            return None
        
        # Préparer les données
        labels = [str(year) for year in years]
        
        # Récupérer les données des ratios
        roe_data = []
        npm_data = []
        ic_data = []
        rev_data = []
        np_data = []
        
        for year in years:
            ratio = ratios_by_year.get(year)
            instance = data_by_year.get(year)
            
            # Ratios
            roe_data.append(float(ratio.rendement_capitaux_propres) if ratio and ratio.rendement_capitaux_propres is not None else 0.0)
            npm_data.append(float(ratio.taux_marge_net) if ratio and ratio.taux_marge_net is not None else 0.0)
            ic_data.append(float(ratio.ratios_couverture_interet) if ratio and ratio.ratios_couverture_interet is not None else 0.0)
            
            # Données financières (normalisées)
            rev_value = instance.ventes if instance and instance.ventes else 0
            np_value = instance.resultat_net if instance and instance.resultat_net else 0
            rev_data.append(float(rev_value) / 1000000 if rev_value else 0.0)  # Division par 1M
            np_data.append(float(np_value) / 1000000 if np_value else 0.0)    # Division par 1M
        
        # Créer le graphique avec une seule figure (pas d'axes multiples)
        plt.figure(figsize=(12, 8))
        
        # Tracer toutes les courbes sur le même axe
        plt.plot(labels, roe_data, label='ROE - Return on Equity', marker='o', linewidth=2, color='#1f77b4')
        plt.plot(labels, npm_data, label='NPM - Net Profit Margin', marker='s', linewidth=2, color='#ff7f0e')
        plt.plot(labels, ic_data, label='IC - Interest Coverage', marker='^', linewidth=2, color='#2ca02c')
        plt.plot(labels, rev_data, label='REV - Revenue (M)', marker='d', linewidth=2, color='#d62728', linestyle='--')
        plt.plot(labels, np_data, label='NP - Net Profit (M)', marker='v', linewidth=2, color='#9467bd', linestyle='--')
        
        # Personnaliser le graphique
        plt.title('Profitability Analysis', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Years', fontsize=12)
        plt.ylabel('Values', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_rentabilite_financiere_anglais_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None



def get_charts_delais_anglais_data(acheteur, years):
    """
    Génère les données pour le chart des délais anglais AVEC GESTION D'ERREURS
    """
    try:
        actif_model = ActifA
        passif_model = PassifA
        resultat_model = ResultatA
        
        # Vérifier s'il y a des données
        has_data = False
        ratios_by_year = {}
        
        for year in years:
            actif_instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            passif_instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            resultat_instance = resultat_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            
            if actif_instance and passif_instance and resultat_instance:
                ratios = RatiosAnglais(actif_instance, passif_instance, resultat_instance)
                ratios_by_year[year] = ratios
                has_data = True
            else:
                ratios_by_year[year] = None
        
        if not has_data:
            return None
        
        # Préparer les données
        labels = [str(year) for year in years]
        
        # Récupérer les données avec valeurs par défaut
        dso_data = []
        dpo_data = []
        rt_data = []
        it_data = []
        at_data = []
        
        for year in years:
            ratio = ratios_by_year.get(year)
            dso_data.append(float(ratio.jour_recouvrement_moyen) if ratio and ratio.jour_recouvrement_moyen is not None else 0.0)
            dpo_data.append(float(ratio.jour_paiement_moyen) if ratio and ratio.jour_paiement_moyen is not None else 0.0)
            rt_data.append(float(ratio.taux_rotation_creance) if ratio and ratio.taux_rotation_creance is not None else 0.0)
            it_data.append(float(ratio.taux_rotation_stock) if ratio and ratio.taux_rotation_stock is not None else 0.0)
            at_data.append(float(ratio.taux_rotation_actif) if ratio and ratio.taux_rotation_actif is not None else 0.0)
        
        # Créer le graphique
        plt.figure(figsize=(12, 8))
        
        # Tracer les courbes
        plt.plot(labels, dso_data, label='DSO - Days Sales Outstanding', marker='o', linewidth=2, color='#1f77b4')
        plt.plot(labels, dpo_data, label='DPO - Days Payable Outstanding', marker='s', linewidth=2, color='#ff7f0e')
        plt.plot(labels, rt_data, label='RT - Receivables Turnover', marker='^', linewidth=2, color='#2ca02c')
        plt.plot(labels, it_data, label='IT - Inventory Turnover', marker='d', linewidth=2, color='#d62728')
        plt.plot(labels, at_data, label='AT - Asset Turnover', marker='v', linewidth=2, color='#9467bd')
        
        # Personnaliser le graphique
        plt.title('Days Analysis', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Years', fontsize=12)
        plt.ylabel('Values', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_delais_anglais_data: {str(e)}")
        return None


#############################################################
#
# Fonctions pour le bilan Bancaire
#
############################################################# 
def get_structured_actif_bancaire_data(acheteur, years):
    """
    Récupère et structure les données d'actif pour le bilan bancaire.
    """
    actif_model = Assets
    data_by_year = {}
    for year in years:
        instance = actif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance

    structure_map = {
        "INTERBANK ASSETS": [
            {'label': "Cash", 'key': 'caisse'},
            {'label': "At sight", 'key': 'a_vue'},
            {'label': "At term", 'key': 'a_terme'},
            {'label': "TOTAL INTERBANK ASSETS", 'key': 'pret_interbancaire', 'is_total': True},
        ],
        "CUSTOMER LOANS AND ADVANCES": [
            {'label': "Commercial paper portfolio", 'key': 'porteuille_papier_commercial'},
            {'label': "Other customer contests", 'key': 'autres_concours_clients'},
            {'label': "Ordinary receivables", 'key': 'creances_ordinaires'},
            {'label': "Factoring", 'key': 'affacturage'},
            {'label': "TOTAL CUSTOMER LOANS", 'key': 'creance_sur_la_clientele', 'is_total': True},
        ],
        "INVESTMENTS": [
            {'label': "Investment securities", 'key': 'titres_placement'},
            {'label': "Financial fixed assets", 'key': 'immobilisation_fin'},
        ],
        "OTHER ASSETS": [
            {'label': "Leasing operations", 'key': 'operation_credit_bail'},
            {'label': "Intangible fixed assets", 'key': 'immobilisation_incorporelle'},
            {'label': "Tangible fixed assets", 'key': 'immobilisation_corporelle'},
            {'label': "Shareholders accounts", 'key': 'actionnaire_ou_associe'},
            {'label': "Other assets", 'key': 'autres_actifs'},
            {'label': "Sundry accounts", 'key': 'comptes_commande_divers'},
        ],
        "TOTAL ASSETS": [
            {'label': "TOTAL ASSETS", 'key': 'total_assets', 'is_final_total': True},
        ]
    }

    return _build_structured_data(structure_map, data_by_year, years)


def get_structured_passif_bancaire_data(acheteur, years):
    """
    Récupère et structure les données de passif pour le bilan bancaire.
    """
    passif_model = Liabilities
    data_by_year = {}
    for year in years:
        instance = passif_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance

    structure_map = {
        "INTERBANK DEBT": [
            {'label': "At sight", 'key': 'a_vue'},
            {'label': "At term", 'key': 'a_terme'},
            {'label': "TOTAL INTERBANK DEBT", 'key': 'dette_interbancaire', 'is_total': True},
        ],
        "CUSTOMER DEPOSITS": [
            {'label': "Short-term savings accounts", 'key': 'comptes_epargne_court_terme'},
            {'label': "Term savings accounts", 'key': 'comptes_epargne_terme'},
            {'label': "Cash certificates", 'key': 'bons_caisse'},
            {'label': "Other sight debts", 'key': 'autres_dette_a_vue'},
            {'label': "Other term debts", 'key': 'autres_dette_a_terme'},
            {'label': "TOTAL CUSTOMER DEPOSITS", 'key': 'dette_envers_clientelle', 'is_total': True},
        ],
        "OTHER LIABILITIES": [
            {'label': "Debt securities", 'key': 'titres_creance_autres_dettes'},
            {'label': "Sundry accounts", 'key': 'compte_dordre_divers'},
            {'label': "Provisions for risks and charges", 'key': 'provision_pour_risque_charge'},
            {'label': "Regulated provisions", 'key': 'provision_reglementee'},
            {'label': "Subordinated loans", 'key': 'emprunt_subordonne_tire_emis'},
            {'label': "Investment grants", 'key': 'subventions_investissement'},
            {'label': "Appropriated funds", 'key': 'fonds_affecte'},
            {'label': "General banking risk funds", 'key': 'fonds_pour_risque_bancaire_generaux'},
        ],
        "SHAREHOLDERS' EQUITY": [
            {'label': "Capital", 'key': 'capital_ou_dotation'},
            {'label': "Share premium", 'key': 'primes_liees_reserve_capital'},
            {'label': "Revaluation reserves", 'key': 'ecarts_reevaluation'},
            {'label': "Retained earnings", 'key': 'benefices_non_distribue'},
            {'label': "Net profit", 'key': 'resultat_net_exercie'},
            {'label': "TOTAL EQUITY", 'key': 'total_liabilities', 'is_final_total': True},
        ]
    }

    return _build_structured_data(structure_map, data_by_year, years)


def get_structured_produit_bancaire_data(acheteur, years):
    """
    Récupère et structure les données de produits pour le bilan bancaire.
    """
    produit_model = Products
    data_by_year = {}
    for year in years:
        instance = produit_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance
    structure_map = {
        "INTEREST INCOME": [
            {'label': "Interbank loans", 'key': 'interets_produit_assimile_sur_pret_avance_interbancaire'},
            {'label': "Customer loans", 'key': 'ineterets_produit_assimile_pret_avance_clientele'},
            {'label': "Investment securities", 'key': 'interet_produit_sur_titre_dinvestissement'},
            {'label': "Subordinated loans", 'key': 'revenu_gains_titre_pret_titre_subordonne'},
            {'label': "Other interest income", 'key': 'autres_interets_produits_assimiles'},
            {'label': "TOTAL INTEREST INCOME", 'key': 'interet_produit_assimile', 'is_total': True},
        ],
        "OTHER INCOME": [
            {'label': "Leasing operations", 'key': 'produits_leansing_operation_connexes'},
            {'label': "Commissions", 'key': 'commissions'},
            {'label': "Negotiable securities", 'key': 'revenus_titre_negociable'},
            {'label': "Dividends", 'key': 'dividendes_produits_assimiles'},
            {'label': "Foreign exchange", 'key': 'revenus_operation_de_change'},
            {'label': "Off-balance sheet", 'key': 'produits_opeations_hors_bilan'},
            {'label': "Other banking income", 'key': 'produits_bancaire_divers'},
        ],
        "SALES": [
            {'label': "Sales margins", 'key': 'marges_vente'},
            {'label': "Merchandise sales", 'key': 'ventes_marchandises'},
            {'label': "Inventory variation", 'key': 'variation_stocks_marchandises'},
            {'label': "General operating income", 'key': 'produit_dexploitation_generale'},
        ],
        "OTHER ITEMS": [
            {'label': "Depreciation reversals", 'key': 'reprise_damortissement_provisions_sur_immobilisation'},
            {'label': "Value correction balance", 'key': 'solde_resultat_correction_valeur_sur_creance_hors_bilan'},
            {'label': "Risk fund excess", 'key': 'excedent_reprise_fonds_pour_risque_bancaire_generaux'},
            {'label': "Exceptional income", 'key': 'produits_exceptionnels'},
            {'label': "Prior year profits", 'key': 'benefice_sur_exercice_anterieur'},
            {'label': "Losses", 'key': 'perte'},
            {'label': "TOTAL INCOME", 'key': 'total_produit', 'is_final_total': True},
        ]
    }
    return _build_structured_data(structure_map, data_by_year, years)


def get_structured_depense_bancaire_data(acheteur, years):
    """
    Récupère et structure les données de dépenses pour le bilan bancaire.
    """
    depense_model = Expenses
    data_by_year = {}
    for year in years:
        instance = depense_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance
    structure_map = {
        "INTEREST EXPENSES": [
            {'label': "Interbank debt", 'key': 'interet_charges_assimilee_dette_interbancaire'},
            {'label': "Customer debt", 'key': 'interet_charge_assimilee_dette_clientele'},
            {'label': "Debt securities", 'key': 'interet_charge_assimilee_titre_creance'},
            {'label': "Blocked accounts", 'key': 'chargesc_compte_bloque_dactionnaire_emprunt_sub'},
            {'label': "Other interest expenses", 'key': 'autres_interets_charges_assimilee'},
            {'label': "TOTAL INTEREST EXPENSES", 'key': 'interet_charges_assimile', 'is_total': True},
        ],
        "OPERATING EXPENSES": [
            {'label': "Leasing operations", 'key': 'charges_sur_op_credit_bail_assimile'},
            {'label': "Commissions", 'key': 'commissions'},
            {'label': "Investment charges", 'key': 'charges_sur_titre_placement'},
            {'label': "Foreign exchange charges", 'key': 'charges_sur_operation_change'},
            {'label': "Off-balance sheet charges", 'key': 'charges_sur_operation_hors_bilan'},
            {'label': "Other banking expenses", 'key': 'frais_divers_exploitation_bancaire'},
        ],
        "COST OF SALES": [
            {'label': "Merchandise purchases", 'key': 'achat_marchandises'},
            {'label': "Inventory sold", 'key': 'stocks_vendus'},
            {'label': "Inventory variation", 'key': 'variations_stocks_marchandises'},
        ],
        "OTHER EXPENSES": [
            {'label': "Personnel expenses", 'key': 'frais_personnel'},
            {'label': "General expenses", 'key': 'autres_frais_generaux'},
            {'label': "Depreciation", 'key': 'dotations_amortissement_provision_immobilisation'},
            {'label': "Loss on receivables", 'key': 'solde_perte_creance_hors_bilan'},
            {'label': "Risk fund excess", 'key': 'excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux'},
            {'label': "Exceptional charges", 'key': 'charges_exceptionnelle'},
            {'label': "Prior year losses", 'key': 'pertes_exercice_anterieurs'},
            {'label': "Income tax", 'key': 'impot_sur_revenu'},
            {'label': "TOTAL EXPENSES", 'key': 'total_des_charges', 'is_final_total': True},
        ]
    }
    return _build_structured_data(structure_map, data_by_year, years)


def get_structured_hors_bilan_bancaire_data(acheteur, years):
    """
    Récupère et structure les données hors bilan pour le bilan bancaire.
    """
    hors_bilan_model = OffBalanceSheet
    data_by_year = {}
    for year in years:
        instance = hors_bilan_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
        data_by_year[year] = instance
    structure_map = {
        "COMMITMENTS GIVEN": [
            {'label': "Financing to credit institutions", 'key': 'engagement_financement_donne_ets_credit'},
            {'label': "Financing to customers", 'key': 'engagement_financement_donne_clientele'},
            {'label': "Guarantees to credit institutions", 'key': 'engagement_garantie_donne_ets_credit'},
            {'label': "Guarantees to customers", 'key': 'engagement_garantie_donne_clientele'},
            {'label': "Securities commitments", 'key': 'engagement_sur_titres_donnes'},
            {'label': "TOTAL COMMITMENTS GIVEN", 'key': 'total_engagements_donnes', 'is_total': True},
        ],
        "COMMITMENTS RECEIVED": [
            {'label': "Financing from credit institutions", 'key': 'engagement_financement_recu_ets_credit'},
            {'label': "Financing from customers", 'key': 'engagement_financement_recu_clientele'},
            {'label': "Guarantees from credit institutions", 'key': 'engagement_garantie_recu_ets_credit'},
            {'label': "Securities commitments received", 'key': 'engagement_sur_titres_recus'},
            {'label': "TOTAL COMMITMENTS RECEIVED", 'key': 'total_engagements_recus', 'is_total': True},
        ]
    }
    return _build_structured_data(structure_map, data_by_year, years)


def get_structured_ratios_bancaire_data_v1(acheteur, years):
    """
    Récupère et structure les ratios pour le bilan bancaire.
    Utilise les mêmes formules et bornes que ScoreACREMACBilanBancaireService.
    """
    ratios_by_year = {}
    for year in years:
        assets_instance = Assets.objects.filter(acheteur=acheteur, annee__annee=year).first()
        liabilities_instance = Liabilities.objects.filter(acheteur=acheteur, annee__annee=year).first()
        products_instance = Products.objects.filter(acheteur=acheteur, annee__annee=year).first()
        expenses_instance = Expenses.objects.filter(acheteur=acheteur, annee__annee=year).first()

        if assets_instance and liabilities_instance and products_instance and expenses_instance:
            # Récupérer les valeurs numériques et les convertir en float
            total_actif = float(assets_instance.total_assets()) if hasattr(assets_instance, 'total_assets') else 1.0
            total_passif = float(liabilities_instance.total_liabilities) if hasattr(liabilities_instance, 'total_liabilities') else 1.0
            total_produit = float(products_instance.total_produit) if hasattr(products_instance, 'total_produit') else 1.0
            total_charges = float(expenses_instance.total_des_charges) if hasattr(expenses_instance, 'total_des_charges') else 1.0

            # Calcul des composantes en float
            capitaux_propres = (
                float(liabilities_instance.capital_ou_dotation or 0) +
                float(liabilities_instance.primes_liees_reserve_capital or 0) +
                float(liabilities_instance.benefices_non_distribue or 0) +
                float(liabilities_instance.resultat_net_exercie or 0)
            )
            dettes_court_terme = (
                float(liabilities_instance.dette_envers_clientelle or 0) +
                float(liabilities_instance.autres_dette_a_vue or 0)
            )
            actifs_liquides = (
                float(assets_instance.pret_interbancaire or 0) +
                float(assets_instance.titres_placement or 0)
            )
            creance_clientele = float(assets_instance.creance_sur_la_clientele or 0)
            resultat_net = total_produit - total_charges
            interets_produits = float(products_instance.interet_produit_assimile or 0)

            # Calcul des ratios en float
            ratios = {
                'r1': (capitaux_propres / total_actif) * 100 if total_actif else 0.0,  # Ratio de solvabilité
                'r2': (actifs_liquides / dettes_court_terme) * 100 if dettes_court_terme else 0.0,  # Ratio de liquidité
                'r3': (resultat_net / total_actif) * 100 if total_actif else 0.0,  # Ratio de rentabilité
                'r4': (creance_clientele / total_actif) * 100 if total_actif else 0.0,  # Ratio de qualité des actifs
                'r5': (total_charges / total_produit) * 100 if total_produit else 0.0,  # Ratio d'efficience
                'r6': ((total_produit - interets_produits) / total_produit) * 100 if total_produit else 0.0,  # Ratio de diversification
            }

            # Application des bornes
            ratios_bornees = {
                'r1': max(4.0, min(20.0, ratios.get('r1', 0.0))),  # Solvabilité: 4% à 20%
                'r2': max(80.0, min(120.0, ratios.get('r2', 0.0))),  # Liquidité: 80% à 120%
                'r3': max(-5.0, min(3.0, ratios.get('r3', 0.0))),  # Rentabilité: -5% à 3%
                'r4': max(0.0, min(60.0, ratios.get('r4', 0.0))),  # Qualité actifs: 0% à 60%
                'r5': max(50.0, min(95.0, ratios.get('r5', 0.0))),  # Efficience: 50% à 95%
                'r6': max(5.0, min(40.0, ratios.get('r6', 0.0))),  # Diversification: 5% à 40%
            }

            ratios_by_year[year] = {
                'ratios': ratios,
                'ratios_bornees': ratios_bornees,
            }
        else:
            ratios_by_year[year] = None

    structure_map = {
        "FINANCIAL STRUCTURE": [
            {'label': "Solvency Ratio (R1)", 'key': 'r1'},
            {'label': "Liquidity Ratio (R2)", 'key': 'r2'},
        ],
        "PERFORMANCE": [
            {'label': "Profitability Ratio (R3)", 'key': 'r3'},
            {'label': "Asset Quality Ratio (R4)", 'key': 'r4'},
        ],
        "OPERATIONAL EFFICIENCY": [
            {'label': "Efficiency Ratio (R5)", 'key': 'r5'},
            {'label': "Revenue Diversification Ratio (R6)", 'key': 'r6'},
        ]
    }

    return _build_ratios_data_bancaire(structure_map, ratios_by_year, years)


def get_structured_ratios_bancaire_data(acheteur, years):
    """
    Récupère et structure les ratios pour le bilan bancaire.
    Utilise les mêmes formules et bornes que ScoreACREMACBilanBancaireService.
    """
    ratios_by_year = {}
    def safe_ratio(numerator, denominator, multiplier=1.0):
        try:
            denominator = float(denominator or 0)
            if denominator == 0:
                return None
            return (float(numerator or 0) / denominator) * float(multiplier)
        except (TypeError, ValueError, ZeroDivisionError):
            return None

    for year in years:
        assets_instance = Assets.objects.filter(acheteur=acheteur, annee__annee=year).first()
        liabilities_instance = Liabilities.objects.filter(acheteur=acheteur, annee__annee=year).first()
        products_instance = Products.objects.filter(acheteur=acheteur, annee__annee=year).first()
        expenses_instance = Expenses.objects.filter(acheteur=acheteur, annee__annee=year).first()

        if assets_instance and liabilities_instance and products_instance and expenses_instance:
            # Ne pas biaiser les ratios en cas de dénominateur nul
            total_actif = float(assets_instance.total_assets) if assets_instance.total_assets else 0.0
            total_produit = float(products_instance.total_produit) if products_instance.total_produit else 0.0
            total_charges = float(expenses_instance.total_des_charges) if expenses_instance.total_des_charges else 0.0

            # Calcul des composantes en float
            capitaux_propres = (
                float(liabilities_instance.capital_ou_dotation or 0) +
                float(liabilities_instance.primes_liees_reserve_capital or 0) +
                float(liabilities_instance.benefices_non_distribue or 0) +
                float(liabilities_instance.resultat_net_exercie or 0)
            )
            dettes_court_terme = (
                float(liabilities_instance.dette_envers_clientelle or 0) +
                float(liabilities_instance.autres_dette_a_vue or 0)
            )
            actifs_liquides = (
                float(assets_instance.pret_interbancaire or 0) +
                float(assets_instance.titres_placement or 0)
            )
            creance_clientele = float(assets_instance.creance_sur_la_clientele or 0)
            resultat_net = total_produit - total_charges
            interets_produits = float(products_instance.interet_produit_assimile or 0)

            # Calcul des ratios
            ratios = {
                'r1': safe_ratio(capitaux_propres, total_actif, 100),  # Ratio de solvabilité
                'r2': safe_ratio(actifs_liquides, dettes_court_terme, 100),  # Ratio de liquidité
                'r3': safe_ratio(resultat_net, total_actif, 100),  # Ratio de rentabilité
                'r4': safe_ratio(creance_clientele, total_actif, 100),  # Ratio de qualité des actifs
                'r5': safe_ratio(total_charges, total_produit, 100),  # Ratio d'efficience
                'r6': safe_ratio(total_produit - interets_produits, total_produit, 100),  # Ratio de diversification
            }

            # Application des bornes sans plancher biaisé
            r1 = ratios.get('r1')
            r2 = ratios.get('r2')
            r3 = ratios.get('r3')
            r4 = ratios.get('r4')
            r5 = ratios.get('r5')
            r6 = ratios.get('r6')
            ratios_bornees = {
                'r1': max(0.0, min(100.0, r1)) if r1 is not None else None,
                'r2': max(0.0, min(200.0, r2)) if r2 is not None else None,
                'r3': max(-100.0, min(100.0, r3)) if r3 is not None else None,
                'r4': max(0.0, min(100.0, r4)) if r4 is not None else None,
                'r5': max(0.0, min(200.0, r5)) if r5 is not None else None,
                'r6': max(0.0, min(100.0, r6)) if r6 is not None else None,
            }

            ratios_by_year[year] = {
                'ratios': ratios,
                'ratios_bornees': ratios_bornees,
            }
        else:
            ratios_by_year[year] = None

    structure_map = {
        "FINANCIAL STRUCTURE": [
            {'label': "Solvency Ratio (R1)", 'key': 'r1'},
            {'label': "Liquidity Ratio (R2)", 'key': 'r2'},
        ],
        "PERFORMANCE": [
            {'label': "Profitability Ratio (R3)", 'key': 'r3'},
            {'label': "Asset Quality Ratio (R4)", 'key': 'r4'},
        ],
        "OPERATIONAL EFFICIENCY": [
            {'label': "Efficiency Ratio (R5)", 'key': 'r5'},
            {'label': "Revenue Diversification Ratio (R6)", 'key': 'r6'},
        ]
    }

    return _build_ratios_data_bancaire(structure_map, ratios_by_year, years)


# Les graphiques
def get_charts_structure_financiere_bancaire_data(acheteur, years):
    """
    Génère les données pour le chart de structure financière bancaire AVEC GESTION D'ERREURS
    """
    try:
        assets_model = Assets
        liabilities_model = Liabilities
        
        # Vérifier s'il y a des données
        has_data = False
        data_by_year = {}
        
        for year in years:
            assets_instance = assets_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            liabilities_instance = liabilities_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            
            if assets_instance and liabilities_instance:
                data_by_year[year] = {
                    'assets': assets_instance,
                    'liabilities': liabilities_instance
                }
                has_data = True
            else:
                data_by_year[year] = None
        
        if not has_data:
            return None
        
        # Préparer les données
        labels = [str(year) for year in years]
        
        # Récupérer les données avec valeurs par défaut
        total_assets_data = []
        total_liabilities_data = []
        equity_data = []
        interbank_assets_data = []
        customer_loans_data = []
        
        for year in years:
            data = data_by_year.get(year)
            if data:
                assets = data['assets']
                liabilities = data['liabilities']
                
                total_assets_data.append(float(assets.total_assets) if assets.total_assets else 0.0)
                total_liabilities_data.append(float(liabilities.total_liabilities) if liabilities.total_liabilities else 0.0)
                
                # Calcul des capitaux propres
                equity = (
                    (liabilities.capital_ou_dotation or 0) +
                    (liabilities.primes_liees_reserve_capital or 0) +
                    (liabilities.benefices_non_distribue or 0) +
                    (liabilities.resultat_net_exercie or 0)
                )
                equity_data.append(float(equity))
                
                interbank_assets_data.append(float(assets.pret_interbancaire) if assets.pret_interbancaire else 0.0)
                customer_loans_data.append(float(assets.creance_sur_la_clientele) if assets.creance_sur_la_clientele else 0.0)
            else:
                total_assets_data.append(0.0)
                total_liabilities_data.append(0.0)
                equity_data.append(0.0)
                interbank_assets_data.append(0.0)
                customer_loans_data.append(0.0)
        
        # Normaliser les données (division par 1M pour meilleure lisibilité)
        total_assets_data = [x / 1000000 for x in total_assets_data]
        total_liabilities_data = [x / 1000000 for x in total_liabilities_data]
        equity_data = [x / 1000000 for x in equity_data]
        interbank_assets_data = [x / 1000000 for x in interbank_assets_data]
        customer_loans_data = [x / 1000000 for x in customer_loans_data]
        
        # Créer le graphique
        plt.figure(figsize=(12, 8))
        
        # Tracer les courbes
        plt.plot(labels, total_assets_data, label='Total Assets (M)', marker='o', linewidth=2, color='#1f77b4')
        plt.plot(labels, total_liabilities_data, label='Total Liabilities (M)', marker='s', linewidth=2, color='#ff7f0e')
        plt.plot(labels, equity_data, label='Shareholders Equity (M)', marker='^', linewidth=2, color='#2ca02c')
        plt.plot(labels, interbank_assets_data, label='Interbank Assets (M)', marker='d', linewidth=2, color='#d62728')
        plt.plot(labels, customer_loans_data, label='Customer Loans (M)', marker='v', linewidth=2, color='#9467bd')
        
        # Personnaliser le graphique
        plt.title('Bank Financial Structure', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Years', fontsize=12)
        plt.ylabel('Amounts (M)', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_structure_financiere_bancaire_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_charts_rentabilite_bancaire_data(acheteur, years):
    """
    Génère les données pour le chart de rentabilité bancaire AVEC GESTION D'ERREURS
    """
    try:
        products_model = Products
        expenses_model = Expenses
        assets_model = Assets
        
        # Vérifier s'il y a des données
        has_data = False
        data_by_year = {}
        
        for year in years:
            products_instance = products_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            expenses_instance = expenses_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            assets_instance = assets_model.objects.filter(acheteur=acheteur, annee__annee=year).first()
            
            if products_instance and expenses_instance and assets_instance:
                data_by_year[year] = {
                    'products': products_instance,
                    'expenses': expenses_instance,
                    'assets': assets_instance
                }
                has_data = True
            else:
                data_by_year[year] = None
        
        if not has_data:
            return None
        
        # Préparer les données
        labels = [str(year) for year in years]
        
        # Récupérer les données avec valeurs par défaut
        total_income_data = []
        total_expenses_data = []
        net_income_data = []
        interest_income_data = []
        other_income_data = []
        roa_data = []  # Return on Assets
        
        for year in years:
            data = data_by_year.get(year)
            if data:
                products = data['products']
                expenses = data['expenses']
                assets = data['assets']
                
                total_income = float(products.total_produit) if products.total_produit else 0.0
                total_expenses = float(expenses.total_des_charges) if expenses.total_des_charges else 0.0
                net_income = total_income - total_expenses
                interest_income = float(products.interet_produit_assimile) if products.interet_produit_assimile else 0.0
                other_income = total_income - interest_income
                total_assets = float(assets.total_assets) if assets.total_assets else 1.0
                
                total_income_data.append(total_income / 1000000)  # Normalisation
                total_expenses_data.append(total_expenses / 1000000)
                net_income_data.append(net_income / 1000000)
                interest_income_data.append(interest_income / 1000000)
                other_income_data.append(other_income / 1000000)
                roa_data.append((net_income / total_assets) * 100 if total_assets else 0.0)  # ROA en %
            else:
                total_income_data.append(0.0)
                total_expenses_data.append(0.0)
                net_income_data.append(0.0)
                interest_income_data.append(0.0)
                other_income_data.append(0.0)
                roa_data.append(0.0)
        
        # Créer le graphique avec deux axes y
        fig, ax1 = plt.subplots(figsize=(12, 8))
        
        # Axe principal pour les montants financiers
        ax1.plot(labels, total_income_data, label='Total Income (M)', marker='o', linewidth=2, color='#1f77b4')
        ax1.plot(labels, total_expenses_data, label='Total Expenses (M)', marker='s', linewidth=2, color='#ff7f0e')
        ax1.plot(labels, net_income_data, label='Net Income (M)', marker='^', linewidth=2, color='#2ca02c')
        ax1.plot(labels, interest_income_data, label='Interest Income (M)', marker='d', linewidth=2, color='#d62728')
        ax1.plot(labels, other_income_data, label='Other Income (M)', marker='v', linewidth=2, color='#9467bd')
        
        ax1.set_xlabel('Years', fontsize=12)
        ax1.set_ylabel('Amounts (M)', fontsize=12, color='black')
        ax1.tick_params(axis='y', labelcolor='black')
        ax1.grid(True, alpha=0.3)
        
        # Axe secondaire pour le ROA
        ax2 = ax1.twinx()
        ax2.plot(labels, roa_data, label='ROA (%)', marker='*', linewidth=2, color='#8c564b', linestyle='--')
        ax2.set_ylabel('ROA (%)', fontsize=12, color='black')
        ax2.tick_params(axis='y', labelcolor='black')
        
        # Titre et légende
        plt.title('Bank Profitability Analysis', fontsize=16, fontweight='bold', pad=20)
        
        # Combiner les légendes des deux axes
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_rentabilite_bancaire_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_charts_ratios_bancaire_data(acheteur, years):
    """
    Génère les données pour le chart des ratios bancaires AVEC GESTION D'ERREURS
    """
    try:
        # Utiliser la fonction existante pour récupérer les ratios
        ratios_data = get_structured_ratios_bancaire_data(acheteur, years)
        
        if not ratios_data:
            return None
        
        # Extraire les données des ratios pour chaque année
        labels = [str(year) for year in years]
        
        # Initialiser les données pour chaque ratio
        r1_data = []  # Solvency
        r2_data = []  # Liquidity
        r3_data = []  # Profitability
        r4_data = []  # Asset Quality
        r5_data = []  # Efficiency
        r6_data = []  # Diversification
        
        # Récupérer les ratios pour chaque année
        for year in years:
            year_data = None
            for section_data in ratios_data.values():
                for item in section_data:
                    if item['values'].get(year) is not None:
                        year_data = item['values']
                        break
                if year_data:
                    break
            
            if year_data and year_data.get(year):
                ratios = year_data[year].get('ratios_bornees', {})
                r1_data.append(ratios.get('r1', 0.0))
                r2_data.append(ratios.get('r2', 0.0))
                r3_data.append(ratios.get('r3', 0.0))
                r4_data.append(ratios.get('r4', 0.0))
                r5_data.append(ratios.get('r5', 0.0))
                r6_data.append(ratios.get('r6', 0.0))
            else:
                r1_data.append(0.0)
                r2_data.append(0.0)
                r3_data.append(0.0)
                r4_data.append(0.0)
                r5_data.append(0.0)
                r6_data.append(0.0)
        
        # Créer le graphique
        plt.figure(figsize=(12, 8))
        
        # Tracer les courbes des ratios
        plt.plot(labels, r1_data, label='R1 - Solvency Ratio (%)', marker='o', linewidth=2, color='#1f77b4')
        plt.plot(labels, r2_data, label='R2 - Liquidity Ratio (%)', marker='s', linewidth=2, color='#ff7f0e')
        plt.plot(labels, r3_data, label='R3 - Profitability Ratio (%)', marker='^', linewidth=2, color='#2ca02c')
        plt.plot(labels, r4_data, label='R4 - Asset Quality Ratio (%)', marker='d', linewidth=2, color='#d62728')
        plt.plot(labels, r5_data, label='R5 - Efficiency Ratio (%)', marker='v', linewidth=2, color='#9467bd')
        plt.plot(labels, r6_data, label='R6 - Diversification Ratio (%)', marker='*', linewidth=2, color='#8c564b')
        
        # Personnaliser le graphique
        plt.title('Bank Key Ratios Analysis', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Years', fontsize=12)
        plt.ylabel('Ratio Values (%)', fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        
        # Ajouter des lignes de référence pour les ratios
        plt.axhline(y=8, color='red', linestyle='--', alpha=0.3, label='Min Solvency (8%)')
        plt.axhline(y=100, color='blue', linestyle='--', alpha=0.3, label='Ideal Liquidity (100%)')
        
        plt.tight_layout()
        
        # Convertir en image base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode('utf-8')
        
    except Exception as e:
        print(f"Erreur dans get_charts_ratios_bancaire_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None









def fix_commandes_emails():
    """
    Corrige les emails des commandes pour qu'ils correspondent aux clients
    """
    print("🔧 Correction des emails des commandes...")
    
    clients = Client.objects.all()
    commandes = Commande.objects.all()
    
    print(f"👥 Clients: {clients.count()}")
    print(f"📦 Commandes: {commandes.count()}")
    
    corrections = 0
    for commande in commandes:
        # Trouver un client aléatoire pour cette commande
        client_aleatoire = random.choice(clients)
        
        # Mettre à jour l'email de la commande pour correspondre au client
        if commande.email != client_aleatoire.email:
            ancien_email = commande.email
            commande.email = client_aleatoire.email
            commande.raison_sociale = client_aleatoire.nom
            commande.telephone = client_aleatoire.telephone
            commande.save()
            
            corrections += 1
            print(f"✅ Commande {commande.notre_ref}: {ancien_email} → {client_aleatoire.email}")
    
    print(f"🎉 {corrections} commandes corrigées!")
    
    # Vérification
    print("\n📊 VÉRIFICATION:")
    for client in clients:
        commandes_client = Commande.objects.filter(email=client.email)
        print(f"   {client.nom}: {commandes_client.count()} commande(s)")
    
    return corrections

def assign_commandes_to_clients():
    """
    Assigne proprement les commandes aux clients existants
    """
    print("🔧 Assignation des commandes aux clients...")
    
    clients = list(Client.objects.all())
    commandes = list(Commande.objects.all())
    
    if not clients:
        print("❌ Aucun client trouvé!")
        return
    
    # Répartir les commandes entre les clients
    for i, commande in enumerate(commandes):
        client = clients[i % len(clients)]  # Répartition cyclique
        
        # Mettre à jour la commande avec les infos du client
        commande.email = client.email
        commande.raison_sociale = client.nom
        commande.telephone = client.telephone or commande.telephone
        
        # Optionnel: mettre à jour l'adresse aussi
        if client.adresse and not commande.rue_adresse:
            commande.rue_adresse = client.adresse
        
        commande.save()
        
        print(f"✅ {commande.notre_ref} → {client.nom}")
    
    print(f"🎉 {len(commandes)} commandes assignées!")

# Version plus simple pour tester rapidement
def quick_fix_for_testing():
    """
    Correction rapide pour les tests
    """
    print("🔧 Correction rapide des emails...")
    
    # Prendre le premier client
    client = Client.objects.first()
    if not client:
        print("❌ Aucun client trouvé!")
        return
    
    # Corriger les 10 premières commandes
    commandes = Commande.objects.all()[:10]
    
    for commande in commandes:
        commande.email = client.email
        commande.raison_sociale = client.nom
        commande.save()
        print(f"✅ {commande.notre_ref} → {client.email}")
    
    print(f"🎉 {len(commandes)} commandes corrigées pour {client.nom}!")





def cleanup_test_data(keep_today=False):
    """
    Nettoie toutes les données de test
    """
    print("🧹 Nettoyage des données de test...")
    
    with transaction.atomic():
        # Compter avant suppression
        avant_commandes = Commande.objects.count()
        avant_mails = MailInfo.objects.count()
        
        if keep_today:
            # Supprimer seulement les commandes d'avant aujourd'hui
            today = timezone.now().date()
            commandes_supprimees = Commande.objects.filter(
                created_at__date__lt=today
            ).delete()
            print(f"✅ Commandes d'avant aujourd'hui supprimées: {commandes_supprimees[0]}")
        else:
            # Supprimer les attachments et mails d'abord
            MailAttachment.objects.all().delete()
            MailInfo.objects.all().delete()
            SuiviCommande.objects.all().delete()
            
            # Puis les commandes
            commandes_supprimees = Commande.objects.all().delete()
            print(f"✅ Toutes les commandes supprimées: {commandes_supprimees[0]}")
        
        apres_commandes = Commande.objects.count()
        print(f"📊 Avant: {avant_commandes} commandes, Après: {apres_commandes} commandes")
        
        return commandes_supprimees

def cleanup_for_mailing_test():
    """
    Nettoie spécifiquement pour les tests mailing
    """
    print("🎯 Nettoyage pour tests mailing...")
    
    # Supprimer seulement les commandes de test (celles avec notre_ref TEST-)
    commandes_test = Commande.objects.filter(notre_ref__startswith='TEST-')
    count = commandes_test.count()
    
    # Supprimer les données associées
    for commande in commandes_test:
        # Supprimer les suivis de ces commandes
        SuiviCommande.objects.filter(commande=commande).delete()
    
    # Supprimer les commandes test
    commandes_test.delete()
    
    print(f"✅ {count} commandes de test supprimées")
    return count








# utils/generate_test_data.py
def generate_test_commandes(nombre=15):
    """
    Génère N commandes de test pour divers clients et acheteurs
    """
    print(f"🎯 Génération de {nombre} commandes de test...")
    
    # Récupérer ou créer les données de base
    clients = Client.objects.all()[:5]
    acheteurs = Acheteur.objects.all()[:5] 
    analysts = User.objects.filter(role='analyste')[:3]
    pays = Pays.objects.first() or Pays.objects.create(nom='Gabon')
    ville = Ville.objects.first() or Ville.objects.create(nom='Libreville', pays=pays)
    devise = Devise.objects.first() or Devise.objects.create(code='XAF', nom='Franc CFA', symbole='FCFA')
    modele_rapport = ModeleRapport.objects.first() or ModeleRapport.objects.create(nom='Standard', code='STD')
    
    # Si pas assez de clients, en créer
    if len(clients) < 3:
        clients = [
            Client.objects.create(
                nom=f"Client Test {i}", 
                email=f"client{i}@test.fr",
                telephone=f"+33 1 {random.randint(40, 89)} {random.randint(10, 99)} {random.randint(10, 99)}",
                adresse=f"{random.randint(1, 200)} Rue de Test, Paris"
            )
            for i in range(3)
        ]
        print("✅ Clients de test créés")
    
    if len(acheteurs) < 3:
        acheteurs = [
            Acheteur.objects.create(nom=f"Acheteur Test {i}", email=f"acheteur{i}@test.fr")
            for i in range(3)
        ]
        print("✅ Acheteurs de test créés")
    
    if not analysts:
        analysts = [
            User.objects.create_user(
                username=f"analyste{i}",
                email=f"analyste{i}@acremac.fr",
                password="password123",
                role="Analyste",
                first_name=f"Analyste{i}",
                last_name="Test"
            )
            for i in range(3)
        ]
        print("✅ Analystes de test créés")
    
    # Générer les commandes
    # Générer les commandes
    commandes_crees = []
    for i in range(nombre):
        # Choisir un client aléatoire (CLIENT, pas ACHETEUR)
        client_choisi = random.choice(clients)  # ← CORRECTION ICI
        acheteur_choisi = random.choice(acheteurs)  # ← Acheteur séparé
        
        commande = Commande.objects.create(
            notre_ref=f'CMD-2024-{i+1:03d}',
            reference_client=f'REF-CLIENT-{i+1:03d}',
            date_recept_commande=timezone.now().date() - timedelta(days=random.randint(1, 60)),
            date_rapport=timezone.now().date() + timedelta(days=random.randint(1, 30)),
            delais=f'{random.randint(1, 30)} jours',
            priorite=random.choice(['Haute', 'Moyenne', 'Basse']),
            raison_sociale=client_choisi.nom,  # Nom du CLIENT (bailleur de fonds)
            type_rapport=random.choice(['Standard', 'Détaillé', 'Express']),
            ref_type_rapport=modele_rapport,
            credit_demande=random.uniform(1000, 50000),
            devise_credit_demande=devise,
            credit_recommande=random.uniform(800, 45000),
            devise_credit_recommande=devise,
            numero_adresse=str(random.randint(1, 200)),
            rue_adresse=random.choice(['Rue de la Paix', 'Avenue des Ternes', 'Boulevard Saint-Germain']),
            code_postale_adresse=f'750{random.randint(1, 20):02d}',
            telephone=client_choisi.telephone,  # Téléphone du CLIENT
            email=client_choisi.email,  # Email du CLIENT - IMPORTANT pour le filtrage!
            pays=pays,
            ville=ville,
            client=random.choice(analysts),  # L'analyste responsable
            acheteur=acheteur_choisi,  # L'acheteur (différent du client)
            status=random.choice(["nouvelle", "en_cours", "rapport_soumis", "rapport_valide"]),
        )
        commandes_crees.append(commande)
        print(f"✅ Commande {i+1}/{nombre}: {commande.notre_ref} pour {client_choisi.nom} (Acheteur: {acheteur_choisi.nom})")
        print(f"🎉 {len(commandes_crees)} commandes générées avec succès!")
    
    # Afficher un résumé
    print("\n📊 RÉSUMÉ:")
    for client in clients:
        count = Commande.objects.filter(email=client.email).count()
        print(f"   {client.nom}: {count} commande(s)")
    
    return commandes_crees
