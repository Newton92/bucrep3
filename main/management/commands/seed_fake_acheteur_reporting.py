from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from main.models import (
    Acheteur,
    Advice,
    Annee,
    AnalyseSectorielle,
    AntecedantsJuridique,
    Assets,
    Banquier,
    CategorieEntreprise,
    CodeNaceAcheteur,
    CodeNafAcheteur,
    CompteFinancier,
    CompositionAction,
    CompositionCapitalSocial,
    ConditionAchat,
    ConditionDeVente,
    ConseilAdministration,
    CouleurCommentaire,
    Devise,
    DonneesEnregistrement,
    Expenses,
    FormeJuridique,
    Geopolitics,
    Liabilities,
    ListeComportementsPaiement,
    ListeConditionAchat,
    ListeConditionVente,
    ListeImportation,
    ListeInformationsAvisCommercial,
    Locaux,
    OffBalanceSheet,
    OperationEtHistorique,
    OpinionCreditAcremac,
    PassifA,
    PassifC,
    PassifIFRS,
    PassifS,
    Pays,
    Products,
    ProprieteEtActif,
    Province,
    ResponsableAcheteur,
    ResultatA,
    ResultatC,
    ResultatIFRS,
    ResultatS,
    Resume,
    RiskManagment,
    RiskRating,
    ScoringSansBilanAcheteur,
    SommaireEtAvis,
    StatutEntreprise,
    Structure,
    SubCategoryNaceCode,
    SubCategoryNafCode,
    TelephoneAcheteur,
    Tendance,
    Ville,
    ActifA,
    ActifC,
    ActifIFRS,
    ActifS,
    CategoryNaceCode,
    CategoryNafCode,
    Commande,
)


class Command(BaseCommand):
    help = (
        "Create or refresh a fake buyer and all major related records used by "
        "solvency reporting generation (profile + contextual sections + all balance types)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--code",
            type=str,
            default=None,
            help="Buyer code to use. If omitted, one is generated automatically.",
        )
        parser.add_argument(
            "--years",
            type=str,
            default="2025,2024,2023",
            help="Comma-separated fiscal years to seed (example: 2025,2024,2023).",
        )
        parser.add_argument(
            "--with-commande",
            action="store_true",
            help="Also create one fake Commande linked to this buyer.",
        )

    def handle(self, *args, **options):
        years = self._parse_years(options["years"])
        if len(years) < 3:
            raise CommandError("Please provide at least 3 years for reporting/scoring.")

        user = self._pick_user()
        if user is None:
            raise CommandError("No user found. Create at least one user before running this command.")

        buyer_code = options["code"] or f"FAKE-RPT-{timezone.now().strftime('%Y%m%d%H%M%S')}"

        with transaction.atomic():
            refs = self._ensure_reference_data()
            acheteur = self._upsert_acheteur(buyer_code, years, refs, user)
            self._upsert_general_sections(acheteur, refs, user)
            self._upsert_financial_sections(acheteur, years, user)
            if options["with_commande"]:
                self._upsert_commande(acheteur, refs, user)

        self.stdout.write(self.style.SUCCESS("Seed completed successfully."))
        self.stdout.write(f"Acheteur ID: {acheteur.id}")
        self.stdout.write(f"Acheteur Code: {acheteur.code}")
        self.stdout.write(f"Years seeded: {', '.join(str(y) for y in years)}")

    def _parse_years(self, raw):
        try:
            years = [int(x.strip()) for x in raw.split(",") if x.strip()]
            years = sorted(set(years), reverse=True)
            return years
        except Exception as exc:
            raise CommandError(f"Invalid --years value: {raw}. Error: {exc}")

    def _pick_user(self):
        User = get_user_model()
        return (
            User.objects.filter(is_superuser=True).first()
            or User.objects.filter(role="Root").first()
            or User.objects.first()
        )

    def _ensure_reference_data(self):
        pays = Pays.objects.first()
        if not pays:
            pays = Pays.objects.create(nom="Gabon", code="GA")

        province = Province.objects.filter(pays=pays).first()
        if not province:
            province = Province.objects.create(nom="Estuaire", code="EST", pays=pays)

        ville = Ville.objects.filter(province=province, pays=pays).first()
        if not ville:
            ville = Ville.objects.create(nom="Libreville", code="LBV", pays=pays, province=province)

        devise, _ = Devise.objects.get_or_create(
            code="XAF",
            defaults={"nom": "Franc CFA", "symbole": "FCFA"},
        )
        couleur, _ = CouleurCommentaire.objects.get_or_create(
            couleur="Vert",
            defaults={"code": "#28A745"},
        )

        categorie, _ = CategorieEntreprise.objects.get_or_create(
            code="CAT-FAKE",
            defaults={"libelle": "Entreprise commerciale"},
        )
        forme, _ = FormeJuridique.objects.get_or_create(
            code="SARL",
            defaults={"libelle": "SARL", "description": "Societe a responsabilite limitee"},
        )
        statut, _ = StatutEntreprise.objects.get_or_create(
            code="ACTIF",
            defaults={"libelle": "Actif"},
        )

        avis_commercial, _ = ListeInformationsAvisCommercial.objects.get_or_create(
            libelle="Positif",
            defaults={"couleur": "green"},
        )
        import_item, _ = ListeImportation.objects.get_or_create(libelle="Import de produits finis")
        achat_item, _ = ListeConditionAchat.objects.get_or_create(nom="Paiement 30 jours")
        vente_item, _ = ListeConditionVente.objects.get_or_create(nom="Paiement comptant")
        comportement, _ = ListeComportementsPaiement.objects.get_or_create(
            libelle="Bon",
            defaults={"couleur": "green"},
        )
        local_item, _ = Locaux.objects.get_or_create(nom="Siege principal")

        nace_subcat = SubCategoryNaceCode.objects.filter(active=True).first()
        if not nace_subcat:
            nace_cat, _ = CategoryNaceCode.objects.get_or_create(code="NACE-FAKE", defaults={"libelle": "NACE Fake"})
            nace_subcat, _ = SubCategoryNaceCode.objects.get_or_create(
                category=nace_cat,
                code="47.11",
                defaults={"libelle": "Commerce de detail", "active": True},
            )

        naf_subcat = SubCategoryNafCode.objects.filter(active=True).first()
        if not naf_subcat:
            naf_cat, _ = CategoryNafCode.objects.get_or_create(code="NAF-FAKE", defaults={"libelle": "NAF Fake"})
            naf_subcat, _ = SubCategoryNafCode.objects.get_or_create(
                category=naf_cat,
                code="47.11A",
                defaults={"libelle": "Commerce alimentaire", "active": True},
            )

        return {
            "pays": pays,
            "province": province,
            "ville": ville,
            "devise": devise,
            "couleur": couleur,
            "categorie": categorie,
            "forme": forme,
            "statut": statut,
            "avis_commercial": avis_commercial,
            "import_item": import_item,
            "achat_item": achat_item,
            "vente_item": vente_item,
            "comportement": comportement,
            "local_item": local_item,
            "nace_subcat": nace_subcat,
            "naf_subcat": naf_subcat,
        }

    def _upsert_acheteur(self, buyer_code, years, refs, user):
        current_year = years[0]
        defaults = {
            "nom": "Societe Fake Reporting",
            "sigle": "SFR",
            "email": "contact.fake.reporting@example.com",
            "date_creation": date(current_year - 8, 1, 15),
            "activite_principale": "Commerce general et distribution",
            "description": "Acheteur fictif pour tests de rapport de solvabilite.",
            "commentaire": "Genere automatiquement par management command.",
            "site_internet": "https://fake-reporting.local",
            "numero_adresse": "12",
            "rue_adresse": "Rue des Tests",
            "code_postal": "00000",
            "boite_postale": "BP 100",
            "fax": "+24101010101",
            "pays": refs["pays"],
            "province": refs["province"],
            "ville": refs["ville"],
            "categorie_entreprise": refs["categorie"],
            "forme_juridique": refs["forme"],
            "statut_entreprise": refs["statut"],
            "couleur_commentaire": refs["couleur"],
            "created_by": user,
            "updated_by": user,
            "code_nace": refs["nace_subcat"].code or "",
        }
        acheteur, _ = Acheteur.objects.update_or_create(code=buyer_code, defaults=defaults)
        return acheteur

    def _upsert_general_sections(self, acheteur, refs, user):
        TelephoneAcheteur.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "telephone": "+241 06 00 00 00",
                "created_by": user,
                "updated_by": user,
            },
        )

        Resume.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "devise": refs["devise"],
                "capital_social": Decimal("125000000"),
                "chiffre_affaire": Decimal("890000000"),
                "resultat_net": Decimal("112000000"),
                "capitaux_propre": Decimal("265000000"),
                "nombre_employe": Decimal("75"),
                "date_creation": date(2018, 1, 15),
                "commentaire": "Resume fictif complet pour reporting.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        CodeNaceAcheteur.objects.get_or_create(acheteur=acheteur, code=refs["nace_subcat"])
        CodeNafAcheteur.objects.get_or_create(acheteur=acheteur, code=refs["naf_subcat"])

        RiskRating.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "remboursabilite": True,
                "situation_liquidite": True,
                "performance_rentabilite": True,
                "perspective_secteur": True,
                "qualite_information_analyse": True,
                "existence_garantie": False,
                "terme_financier_duree_pret": True,
                "mesure_propre_soutenir_credit": True,
                "cotation_du_risque": "Risque faible",
                "indice_du_risque": "Faible",
                "interpretation": "Entreprise solvable avec vigilance standard.",
                "analyse": "Donnees fictives coherentes pour tests.",
                "created_by": user,
                "updated_by": user,
            },
        )

        OpinionCreditAcremac.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "risque_de_defaut": 1,
                "risque_de_concentration_credit": 1,
                "risque_de_reputation": 1,
                "risque_pays": 1,
                "risque_de_taux_dinteret": 1,
                "risque_de_liquidite": 1,
                "risque_eleve": 0,
                "risque_moyen": 0,
                "risque_faible": 1,
                "montant_credit_maximum": Decimal("350000000"),
                "commentaire": "Avis favorable dans le cadre de tests.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        DonneesEnregistrement.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "nom_anterieur": "Fake Corporation SA",
                "date_creation": date(2018, 1, 15),
                "date_registre": date(2018, 2, 10),
                "forme_juridique": "SARL",
                "numero_registre_commerce": "RCCM-LBV-FAKE-001",
                "numero_fiscale": "NIU-FAKE-001",
                "statut_registre": "A jour",
                "commentaire": "Registre conforme.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        AntecedantsJuridique.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "dossier_faillite": "Non",
                "jugement_cour": "Non",
                "antecedant_redressement": "Non",
                "Autre": "Aucun",
                "commentaire": "Aucun antecedent defavorable.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        RiskManagment.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "professionalisme": "Oui",
                "organisation": "Oui",
                "turn_over": "Non",
                "greve": "Non",
                "degradation_qualite": "Non",
                "non_respect_condition": "Non",
                "commentaire": "Management stable.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        ResponsableAcheteur.objects.update_or_create(
            acheteur=acheteur,
            nom="MBOUMBA",
            defaults={
                "prenom": "Jean",
                "Sexe": "Masculin",
                "poste": "Directeur des achats",
                "nationalite": "Gabonaise",
                "commentaire": "Responsable principal.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        ConseilAdministration.objects.update_or_create(
            acheteur=acheteur,
            nom="NTOUTOUME",
            defaults={
                "fonction_dans_le_conseil": "President du Conseil",
                "numero_adresse": "10",
                "rue_adresse": "Avenue de la Republique",
                "code_postale_adresse": "00001",
                "commentaire": "Membre actif.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        CompositionCapitalSocial.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "devise": refs["devise"],
                "emis": Decimal("250000000"),
                "publie": Decimal("250000000"),
                "libere": Decimal("250000000"),
                "commentaire": "Capital entierement libere.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        CompositionAction.objects.update_or_create(
            acheteur=acheteur,
            nom="DOE",
            prenom="Alice",
            defaults={
                "pourcentage": Decimal("65"),
                "commentaire": "Actionnaire majoritaire.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        Structure.objects.update_or_create(
            acheteur=acheteur,
            nom="Filiale Nord",
            defaults={
                "type_affiliation": "Filiale",
                "numero_adresse": "5",
                "rue_adresse": "Rue du Commerce",
                "code_postale_adresse": "00002",
                "commentaire": "Filiale operationnelle.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        AnalyseSectorielle.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "commentaire": "Secteur en croissance reguliere.",
                "impact_covid_19": "Impact modere et maitrise.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        Tendance.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "avis_commercial": refs["avis_commercial"],
                "plus_informations": "Marche en expansion.",
                "presse_media": "Couverture neutre.",
                "alarmes": "Aucune alarme.",
                "principaux_concurrent": "Concurrent A, Concurrent B",
                "commentaire": "Tendance favorable.",
                "created_by": user,
                "updated_by": user,
            },
        )

        Advice.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "points_forts": "Structure financiere solide.",
                "points_faibles": "Dependance partielle a 2 gros clients.",
                "dynamisme_court_terme": "Bon",
                "dynamisme_long_terme": "Bon",
                "risque_potentiel_court_terme": "Faible",
                "created_by": user,
                "updated_by": user,
            },
        )

        Geopolitics.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "stabilite_politique": "Oui",
                "etat_droit": "Oui",
                "efficacite": "Oui",
                "qualite": "Oui",
                "liberte_expression": "Oui",
                "donnees_politiques": "Contexte stable",
                "donnees_economiques": "Croissance moderee",
                "created_by": user,
                "updated_by": user,
            },
        )

        Banquier.objects.update_or_create(
            acheteur=acheteur,
            nom_banque="Banque Test SA",
            defaults={
                "numero_compte": "GA001122334455",
                "type_relation": "Compte principal",
                "numero": "22",
                "rue": "Boulevard Central",
                "ville": refs["ville"],
                "code_postal": "00003",
                "commentaire": "Relation bancaire normale.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        CompteFinancier.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "cabinet": "Cabinet Audit Fake",
                "requis_pour_deposer": "Oui",
                "credibilite_cabinet": "Elevee",
                "source": "Depots comptables",
                "presentation": "Normale",
                "date_compte": date(2025, 1, 1),
                "date_fin": date(2025, 12, 31),
                "date_compte_n_moins_un": date(2024, 1, 1),
                "date_fin_n_moins_un": date(2024, 12, 31),
                "date_compte_n_moins_deux": date(2023, 1, 1),
                "date_fin_n_moins_deux": date(2023, 12, 31),
                "type_compte": "Annuel",
                "devise": "XAF",
                "type_bilan": "classique",
                "commentaire": "Compte financier seed.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        op_hist, _ = OperationEtHistorique.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "commentaire_ratios": "Ratios globalement satisfaisants.",
                "description_complete_activite": "Distribution B2B et B2C.",
                "historique": "Activite demarree en 2018, croissance stable.",
                "created_by": user,
                "updated_by": user,
            },
        )
        op_hist.importation.set([refs["import_item"]])

        prop, _ = ProprieteEtActif.objects.update_or_create(
            acheteur=acheteur,
            branche="Branche principale",
            defaults={
                "created_by": user,
                "updated_by": user,
            },
        )
        prop.locaux.set([refs["local_item"]])

        achat, _ = ConditionAchat.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "les_clients": "Portefeuille diversifie.",
                "fournisseur": "Fournisseurs regionaux",
                "created_by": user,
                "updated_by": user,
            },
        )
        achat.local.set([refs["achat_item"]])
        achat.importation.set([refs["achat_item"]])

        vente, _ = ConditionDeVente.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "recouvrement_de_dette_jugement": "Non",
                "comportement_de_paiement": "Bon",
                "created_by": user,
                "updated_by": user,
            },
        )
        vente.local.set([refs["vente_item"]])

        SommaireEtAvis.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "commentaire": "Conclusion positive avec risque faible.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        try:
            ScoringSansBilanAcheteur.objects.update_or_create(
                acheteur=acheteur,
                defaults={
                    "code": f"SCB-{acheteur.code or acheteur.id}",
                    "libelle": "Scoring sans bilan fake",
                    "forme_juridique": refs["forme"],
                    "scoring_value": 7.4,
                    "interpretation": "Risque faible a modere",
                    "commentaire": "Scoring seed pour tests reporting.",
                    "created_by": user,
                    "updated_by": user,
                },
            )
        except Exception:
            # Some environments fail here because the model save() prints unicode symbols.
            # Reporting still works with fallback scoring values if this record is missing.
            pass

    def _upsert_commande(self, acheteur, refs, user):
        Commande.objects.update_or_create(
            acheteur=acheteur,
            reference_client=f"CMD-{acheteur.code or acheteur.id}",
            defaults={
                "notre_ref": f"ACR-{timezone.now().strftime('%Y%m%d%H%M')}",
                "raison_sociale": acheteur.nom,
                "type_rapport": "Rapport Solvabilite",
                "date_recept_commande": timezone.now().date(),
                "date_rapport": timezone.now().date(),
                "delais": "10 jours",
                "priorite": "Normale",
                "credit_demande": Decimal("150000000"),
                "credit_recommande": Decimal("120000000"),
                "devise_credit_demande": refs["devise"],
                "devise_credit_recommande": refs["devise"],
                "numero_adresse": acheteur.numero_adresse or "12",
                "rue_adresse": acheteur.rue_adresse or "Rue des Tests",
                "code_postale_adresse": acheteur.code_postal or "00000",
                "telephone": "+241 06 00 00 00",
                "email": acheteur.email or "contact.fake.reporting@example.com",
                "pays": refs["pays"],
                "ville": refs["ville"],
                "client": user,
                "status": "nouvelle",
            },
        )

    def _upsert_financial_sections(self, acheteur, years, user):
        for idx, y in enumerate(years):
            annee, _ = Annee.objects.get_or_create(annee=y)
            base = Decimal("1000000") + Decimal(idx) * Decimal("250000")

            self._upsert_financial_model(ActifC, acheteur, annee, base, user)
            self._upsert_financial_model(PassifC, acheteur, annee, base, user)
            self._upsert_financial_model(ResultatC, acheteur, annee, base, user)

            self._upsert_financial_model(ActifA, acheteur, annee, base, user)
            self._upsert_financial_model(PassifA, acheteur, annee, base, user)
            self._upsert_financial_model(ResultatA, acheteur, annee, base, user)

            self._upsert_financial_model(ActifS, acheteur, annee, base, user)
            self._upsert_financial_model(PassifS, acheteur, annee, base, user)
            self._upsert_financial_model(ResultatS, acheteur, annee, base, user)

            self._upsert_financial_model(Assets, acheteur, annee, base, user, type_bilan="annuel")
            self._upsert_financial_model(Liabilities, acheteur, annee, base, user, type_bilan="annuel")
            self._upsert_financial_model(Products, acheteur, annee, base, user, type_bilan="annuel")
            self._upsert_financial_model(Expenses, acheteur, annee, base, user, type_bilan="annuel")
            self._upsert_financial_model(OffBalanceSheet, acheteur, annee, base, user, type_bilan="annuel")

            self._upsert_financial_model(ActifIFRS, acheteur, annee, base, user, type_bilan="annuel")
            self._upsert_financial_model(PassifIFRS, acheteur, annee, base, user, type_bilan="annuel")
            self._upsert_financial_model(ResultatIFRS, acheteur, annee, base, user, type_bilan="annuel")

    def _upsert_financial_model(self, model_cls, acheteur, annee, base, user, type_bilan=None):
        decimal_fields = [
            f.name for f in model_cls._meta.fields if f.__class__.__name__ == "DecimalField"
        ]
        defaults = {}
        for i, name in enumerate(decimal_fields):
            defaults[name] = base + Decimal(i * 1000)

        if "created_by" in [f.name for f in model_cls._meta.fields]:
            defaults["created_by"] = user
        if "updated_by" in [f.name for f in model_cls._meta.fields]:
            defaults["updated_by"] = user
        if type_bilan and "type_bilan" in [f.name for f in model_cls._meta.fields]:
            defaults["type_bilan"] = type_bilan

        lookup = {"acheteur": acheteur, "annee": annee}
        if "semestre" in [f.name for f in model_cls._meta.fields]:
            lookup["semestre"] = None

        model_cls.objects.update_or_create(**lookup, defaults=defaults)
