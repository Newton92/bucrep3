from django.db import models

# Create your models here.


class ActifSysOhada(models.Model):
    exercice_n = models.CharField(max_length=10)

    # Immobilisations incorporelles
    frais_developpement = models.DecimalField(max_digits=20, decimal_places=2)
    brevets_licences = models.DecimalField(max_digits=20, decimal_places=2)
    droits_propriete = models.DecimalField(max_digits=20, decimal_places=2)
    autres_incorporelles = models.DecimalField(max_digits=20, decimal_places=2)

    # Immobilisations corporelles
    terrains = models.DecimalField(max_digits=20, decimal_places=2)
    batiments = models.DecimalField(max_digits=20, decimal_places=2)
    agencements = models.DecimalField(max_digits=20, decimal_places=2)
    materiel_mobilier = models.DecimalField(max_digits=20, decimal_places=2)
    materiel_transport = models.DecimalField(max_digits=20, decimal_places=2)

    # Immobilisations financières
    titres_participation = models.DecimalField(max_digits=20, decimal_places=2)
    autres_financieres = models.DecimalField(max_digits=20, decimal_places=2)

    # Actif circulant
    stocks_encours = models.DecimalField(max_digits=20, decimal_places=2)
    creances_emplois = models.DecimalField(max_digits=20, decimal_places=2)
    valeurs_mobilieres = models.DecimalField(max_digits=20, decimal_places=2)
    disponibilites = models.DecimalField(max_digits=20, decimal_places=2)

    def total_actif(self):
        return (
            self.frais_developpement
            + self.brevets_licences
            + self.droits_propriete
            + self.autres_incorporelles
            + self.terrains
            + self.batiments
            + self.agencements
            + self.materiel_mobilier
            + self.materiel_transport
            + self.titres_participation
            + self.autres_financieres
            + self.stocks_encours
            + self.creances_emplois
            + self.valeurs_mobilieres
            + self.disponibilites
        )


class PassifSysOhada(models.Model):
    exercice_n = models.CharField(max_length=10)

    # Capitaux propres
    capital = models.DecimalField(max_digits=20, decimal_places=2)
    primes_capital = models.DecimalField(max_digits=20, decimal_places=2)
    ecarts_reevaluation = models.DecimalField(max_digits=20, decimal_places=2)
    reserves_indisponibles = models.DecimalField(max_digits=20, decimal_places=2)
    resultat_net = models.DecimalField(max_digits=20, decimal_places=2)
    report_nouveau = models.DecimalField(max_digits=20, decimal_places=2)

    # Dettes
    emprunts_dettes = models.DecimalField(max_digits=20, decimal_places=2)
    dettes_location = models.DecimalField(max_digits=20, decimal_places=2)
    provisions_risques = models.DecimalField(max_digits=20, decimal_places=2)

    def total_capitaux_propres(self):
        return (
            self.capital
            + self.primes_capital
            + self.ecarts_reevaluation
            + self.reserves_indisponibles
            + self.resultat_net
            + self.report_nouveau
        )

    def total_dettes(self):
        return self.emprunts_dettes + self.dettes_location + self.provisions_risques

    def total_passif(self):
        return self.total_capitaux_propres() + self.total_dettes()


class ResultatSysOhada(models.Model):
    exercice_n = models.CharField(max_length=10)

    ventes_marchandises = models.DecimalField(max_digits=20, decimal_places=2)
    achats_marchandises = models.DecimalField(max_digits=20, decimal_places=2)
    variation_stocks = models.DecimalField(max_digits=20, decimal_places=2)

    def marge_commerciale(self):
        return (
            self.ventes_marchandises - self.achats_marchandises + self.variation_stocks
        )

    # Ajoutez d'autres champs et méthodes pour le chiffre d'affaires, les charges, etc.


class RatioSysOhada(models.Model):
    exercice_n = models.CharField(max_length=10)

    working_capital = models.DecimalField(max_digits=20, decimal_places=2)
    need_working_capital = models.DecimalField(max_digits=20, decimal_places=2)
    net_cash_position = models.DecimalField(max_digits=20, decimal_places=2)
    self_financing_capacity = models.DecimalField(max_digits=20, decimal_places=2)

    def calculate_working_capital(self):
        # Logique pour calculer le Working Capital
        pass

    def calculate_need_working_capital(self):
        # Logique pour calculer le Need for Working Capital
        pass

    def calculate_net_cash_position(self):
        # Logique pour calculer la Net Cash Position
        pass

    def calculate_self_financing_capacity(self):
        # Logique pour calculer la capacité d'autofinancement
        pass


class ScoringAvecBilanSysOhada(models.Model):
    exercice_n = models.CharField(max_length=10)

    frais_financiers_ebitda = models.DecimalField(max_digits=20, decimal_places=2)
    creances_douteuses_credit_clients = models.DecimalField(
        max_digits=20, decimal_places=2
    )
    excedent_ca_actif = models.DecimalField(max_digits=20, decimal_places=2)
    actif_circulant_passif_circulant = models.DecimalField(
        max_digits=20, decimal_places=2
    )
    cash_ventes = models.DecimalField(max_digits=20, decimal_places=2)

    def calculate_score(self):
        # Logique pour calculer le score de défaillance
        pass


class ScoringSansBilanSysOhada(models.Model):
    exercice_n = models.CharField(max_length=10)

    anciennete_entreprise = models.IntegerField()
    secteur_activite = models.CharField(max_length=100)
    taille_entreprise = models.CharField(max_length=50)
    experience_dirigeant = models.IntegerField()
    historique_paiement = models.CharField(max_length=50)

    def calculate_score(self):
        # Logique pour calculer le score sans bilan
        pass
