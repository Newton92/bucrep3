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