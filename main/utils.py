# utils.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.template.loader import render_to_string

from main.models import *


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






import requests
from main.models import Pays, Province, Ville
# https://www.geonames.org/activate/rKbZUmb9/yannick1987/
import requests
from django.db import transaction
from main.models import Pays, Province, Ville

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


from django.utils import timezone
from faker import Faker
import random
from django.db.models import Q
from .models import Acheteur, CustomUser, Ville, Pays, Devise, ModeleRapport, Commande, Province

def create_fake_commands(count=15):
    fake = Faker('fr_FR')

    # Récupérer les objets de la base de données une seule fois avant la boucle
    acheteurs = list(Acheteur.objects.all())
    clients = list(CustomUser.objects.filter(Q(role__icontains="Client") | Q(role__icontains="client")))
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
        
        
        
        
        
        
from django.utils import timezone
from faker import Faker
import random
from .models import Acheteur, CategorieEntreprise, FormeJuridique, StatutEntreprise, Pays, Province, Ville, CouleurCommentaire

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
    
    
    
    
    
# utils/financial_report_generator.py

from django.db.models import Model
from django.db.models.fields.related import ForeignKey
from decimal import Decimal
from datetime import datetime

# Import de tous vos modèles et classes de ratios
from .models import (
    ActifA, PassifA, ResultatA,
    ActifC, PassifC, ResultatC,
    Assets, Liabilities, Expenses, Products, OffBalanceSheet,
    ActifS, PassifS, ResultatS,
    ActifIFRS, PassifIFRS, ResultatIFRS
)

from main.models import (
    RatiosAnglais, RatiosClassique, RatiosSyscohada, RatiosIFRS,
    # Il faudra créer une classe de ratios pour le bilan bancaire
    # RatiosBancaire,
)

# Fonction utilitaire pour calculer les variations
def calculate_variation(n, n_minus_1):
    """Calcule la variation en pourcentage entre deux valeurs."""
    if not isinstance(n, (Decimal, float)) or not isinstance(n_minus_1, (Decimal, float)):
        return "N/A"
    
    # Éviter la division par zéro
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
            val_n = getattr(data_by_year.get(years[0]), field_name, None)
            val_n_minus_1 = getattr(data_by_year.get(years[1]), field_name, None)
            val_n_minus_2 = getattr(data_by_year.get(years[2]), field_name, None)
            
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
                val_n = getattr(ratios_data.get(years[0]), ratio_name, None) if ratios_data.get(years[0]) else None
                val_n_minus_1 = getattr(ratios_data.get(years[1]), ratio_name, None) if ratios_data.get(years[1]) else None
                val_n_minus_2 = getattr(ratios_data.get(years[2]), ratio_name, None) if ratios_data.get(years[2]) else None
                
                row['val_n'] = f"{val_n:.2f}" if isinstance(val_n, (Decimal, float)) else "N/A"
                row['val_n_minus_1'] = f"{val_n_minus_1:.2f}" if isinstance(val_n_minus_1, (Decimal, float)) else "N/A"
                row['val_n_minus_2'] = f"{val_n_minus_2:.2f}" if isinstance(val_n_minus_2, (Decimal, float)) else "N/A"
                
                row['var_n_vs_n_minus_1'] = calculate_variation(val_n, val_n_minus_1)
                row['var_n_minus_1_vs_n_minus_2'] = calculate_variation(val_n_minus_1, val_n_minus_2)
                
                table_data.append(row)
                
        return table_data
    
    
    
    
    
    
    
    
    


from decimal import Decimal
from django.db.models import QuerySet

# Importez vos classes de Ratios pour chaque type de bilan
from main.models import RatiosAnglais, RatiosSyscohada, RatiosClassique, RatiosIFRS


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
        val_n = values.get(years[0])
        val_n_moins_1 = values.get(years[1])
        var_n_vs_n_moins_1 = calculate_variation(val_n, val_n_moins_1)
        
        # Année N-1 vs N-2
        val_n_moins_2 = values.get(years[2])
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
        
    return table_data


# Fichier : views_report.py

# ... (les importations existantes) ...

# Fichier : views_report.py

# ... (les importations existantes) ...

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

            val_n = values.get(years[0])
            val_n_moins_1 = values.get(years[1])
            val_n_moins_2 = values.get(years[2])

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
            {'label': "Banques, crédits d'escompte", 'key': 'banques_credit_escompte'},
            {'label': "Banque, crédit caisse", 'key': 'banque_credit_caisse'},
            {'label': "Banques, découvert", 'key': 'banques_decouvert'},
            {'label': "TOTAL III", 'key': 'total_III', 'is_total': True},
        ],
        "COMPTES DE REGULARISATION": [
            {'label': "Écart de conversion passif", 'key': 'ecart_conversion_passif'},
            {'label': "TOTAL IV", 'key': 'total_IV', 'is_total': True},
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
            
            val_n = values.get(years[0])
            val_n_moins_1 = values.get(years[1])
            val_n_moins_2 = values.get(years[2])

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
            
            val_n = values.get(years[0])
            val_n_moins_1 = values.get(years[1])
            val_n_moins_2 = values.get(years[2])

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
from main.models import RatiosClassique

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
            val_n = values.get(years[0])
            val_n_moins_1 = values.get(years[1])
            val_n_moins_2 = values.get(years[2])

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







import matplotlib.pyplot as plt
import numpy as np
import os
from django.conf import settings

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
