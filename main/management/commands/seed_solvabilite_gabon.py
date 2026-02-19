from datetime import date
from decimal import Decimal
import builtins

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from safedelete.models import HARD_DELETE

from main.models import (
    Acheteur,
    ActifA,
    ActifC,
    ActifIFRS,
    ActifS,
    Advice,
    AnalyseSectorielle,
    Annee,
    AntecedantsJuridique,
    Assets,
    Banquier,
    CategorieEntreprise,
    CategoryNaceCode,
    CodeNaceAcheteur,
    CodeNafAcheteur,
    Commande,
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
    ListeConditionAchat,
    ListeConditionVente,
    ListeImportation,
    ListeInformationsAvisCommercial,
    Locaux,
    ModeleAgeSociete,
    ModeleAvisCommercial,
    ModeleBail,
    ModeleComportementPaiement,
    OffBalanceSheet,
    OpinionCreditAcremac,
    OperationEtHistorique,
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
    SubCategoryNaceCode,
    Structure,
    TelephoneAcheteur,
    Tendance,
    Ville,
)


class Command(BaseCommand):
    help = (
        "Génère (ou met à jour) un acheteur Gabon avec les données nécessaires au "
        "rapport de solvabilité: profil, management, géopolitique, scoring sans bilan "
        "et états financiers pour 2025, 2024, 2023, 2022."
    )

    def add_arguments(self, parser):
        parser.add_argument("--code", type=str, default="GAB-SOLV-001", help="Code acheteur.")
        parser.add_argument("--nom", type=str, default="GABON DISTRIBUTION SERVICES SA", help="Nom acheteur.")
        parser.add_argument(
            "--years",
            type=str,
            default="2025,2024,2023,2022",
            help="Années civiles séparées par des virgules.",
        )
        parser.add_argument(
            "--with-commande",
            action="store_true",
            help="Créer aussi une commande liée à l'acheteur.",
        )
        parser.add_argument(
            "--force-reset",
            action="store_true",
            help=(
                "Purger les données existantes du dossier de l'acheteur ciblé "
                "avant régénération."
            ),
        )

    def handle(self, *args, **options):
        years = self._parse_years(options["years"])
        user = self._pick_user()
        if user is None:
            raise CommandError("Aucun utilisateur trouvé pour les champs d'audit.")

        with transaction.atomic():
            if options["force_reset"]:
                existing = Acheteur.objects.filter(code=options["code"].strip()).first()
                if existing:
                    self._force_reset_acheteur_data(existing)
                    self.stdout.write(
                        self.style.WARNING(
                            f"Dossier existant purgé pour l'acheteur code={existing.code} (id={existing.id})."
                        )
                    )

            refs = self._ensure_refs()
            acheteur = self._upsert_acheteur(
                code=options["code"].strip(),
                nom=options["nom"].strip(),
                years=years,
                refs=refs,
                user=user,
            )
            self._upsert_reporting_sections(acheteur, refs, user)
            self._upsert_scoring_sans_bilan(acheteur, refs, user)
            self._upsert_financials(acheteur, years, user)
            if options["with_commande"]:
                self._upsert_commande(acheteur, refs, user)

        self.stdout.write(self.style.SUCCESS("Seed solvabilité Gabon terminé."))
        self.stdout.write(f"Acheteur ID: {acheteur.id}")
        self.stdout.write(f"Code: {acheteur.code}")
        self.stdout.write(f"Années: {', '.join(str(y) for y in years)}")

    def _force_reset_acheteur_data(self, acheteur):
        models_to_purge = [
            TelephoneAcheteur,
            CodeNaceAcheteur,
            CodeNafAcheteur,
            Resume,
            DonneesEnregistrement,
            RiskRating,
            OpinionCreditAcremac,
            AntecedantsJuridique,
            RiskManagment,
            ResponsableAcheteur,
            ConseilAdministration,
            CompositionCapitalSocial,
            CompositionAction,
            Structure,
            AnalyseSectorielle,
            Tendance,
            Geopolitics,
            Banquier,
            CompteFinancier,
            OperationEtHistorique,
            ProprieteEtActif,
            ConditionAchat,
            ConditionDeVente,
            Advice,
            SommaireEtAvis,
            ScoringSansBilanAcheteur,
            ActifC, PassifC, ResultatC,
            ActifA, PassifA, ResultatA,
            ActifS, PassifS, ResultatS,
            Assets, Liabilities, Products, Expenses, OffBalanceSheet,
            ActifIFRS, PassifIFRS, ResultatIFRS,
            Commande,
        ]
        for model_cls in models_to_purge:
            manager = getattr(model_cls, "all_objects", model_cls.objects)
            queryset = manager.filter(acheteur=acheteur)
            for obj in queryset:
                try:
                    obj.delete(force_policy=HARD_DELETE)
                except Exception:
                    obj.delete()

    def _parse_years(self, raw):
        try:
            years = sorted({int(x.strip()) for x in raw.split(",") if x.strip()}, reverse=True)
        except Exception as exc:
            raise CommandError(f"Paramètre --years invalide: {raw} ({exc})")
        expected = {2025, 2024, 2023, 2022}
        missing = expected - set(years)
        if missing:
            raise CommandError(f"Les années {sorted(missing)} sont requises.")
        return years

    def _pick_user(self):
        User = get_user_model()
        return (
            User.objects.filter(is_superuser=True).first()
            or User.objects.filter(is_staff=True).first()
            or User.objects.first()
        )

    def _first_choice(self, model_cls, field_name, fallback=None, skip_blank=True):
        field = model_cls._meta.get_field(field_name)
        choices = list(field.choices or [])
        for value, _label in choices:
            if skip_blank and (value is None or str(value).strip() in {"", "--------", "Veuillez choisir la forme juridique"}):
                continue
            return value
        return fallback

    def _ensure_refs(self):
        pays = (
            Pays.objects.filter(code__in=["GA", "GAB"]).first()
            or Pays.objects.filter(nom__icontains="gabon").first()
        )
        if not pays:
            pays = Pays.objects.create(nom="Gabon", code="GA", afficher_au_dashboard=True)
        elif not pays.afficher_au_dashboard:
            pays.afficher_au_dashboard = True
            pays.save(update_fields=["afficher_au_dashboard"])

        province = Province.objects.filter(pays=pays, nom__iexact="Estuaire").first()
        if not province:
            province = Province.objects.create(nom="Estuaire", code="EST", pays=pays)

        ville = Ville.objects.filter(pays=pays, nom__iexact="Libreville").first()
        if not ville:
            ville = Ville.objects.create(nom="Libreville", code="LBV", pays=pays, province=province)

        devise_xaf, _ = Devise.objects.get_or_create(code="XAF", defaults={"nom": "Franc CFA", "symbole": "FCFA"})
        couleur, _ = CouleurCommentaire.objects.get_or_create(couleur="Vert", defaults={"code": "#28A745"})
        categorie, _ = CategorieEntreprise.objects.get_or_create(code="CAT-COM", defaults={"libelle": "Entreprise commerciale"})
        forme = FormeJuridique.objects.order_by("id").first()
        if not forme:
            forme = FormeJuridique.objects.create(code="SARL", libelle="SARL", poids=1.5)
        statut, _ = StatutEntreprise.objects.get_or_create(code="ACTIF", defaults={"libelle": "Actif"})

        avis_list, _ = ListeInformationsAvisCommercial.objects.get_or_create(libelle="Satisfaisant", defaults={"couleur": "green"})
        local_item, _ = Locaux.objects.get_or_create(nom="Siège principal")
        achat_item, _ = ListeConditionAchat.objects.get_or_create(nom="Paiement 30 jours fin de mois")
        vente_item, _ = ListeConditionVente.objects.get_or_create(nom="Paiement comptant à la livraison")
        import_item, _ = ListeImportation.objects.get_or_create(libelle="Importation produits finis")

        model_comp, _ = ModeleComportementPaiement.objects.get_or_create(
            code="MCOMP-GOOD", defaults={"libelle": "Comportement satisfaisant", "poids": 2.0}
        )
        model_age, _ = ModeleAgeSociete.objects.get_or_create(
            code="MAGE-OLD", defaults={"libelle": "Société mature", "poids": 1.5}
        )
        model_avis, _ = ModeleAvisCommercial.objects.get_or_create(
            code="MAVIS-GOOD", defaults={"libelle": "Avis favorable", "poids": 2.0}
        )
        model_bail, _ = ModeleBail.objects.get_or_create(
            code="MBAIL-STABLE", defaults={"libelle": "Locaux stables", "poids": 1.0}
        )
        category_nace = CategoryNaceCode.objects.filter(active=True).order_by("id").first()
        if not category_nace:
            category_nace = CategoryNaceCode.objects.create(code="46", libelle="Commerce de gros", active=True, poids=1.2)
        subcategory_nace = SubCategoryNaceCode.objects.filter(active=True, category=category_nace).order_by("id").first()
        if not subcategory_nace:
            subcategory_nace = SubCategoryNaceCode.objects.create(
                category=category_nace,
                code="46.90",
                libelle="Commerce de gros non spécialisé",
                active=True,
                poids=1.0,
            )

        return {
            "pays": pays,
            "province": province,
            "ville": ville,
            "devise_xaf": devise_xaf,
            "couleur": couleur,
            "categorie": categorie,
            "forme": forme,
            "statut": statut,
            "avis_list": avis_list,
            "local_item": local_item,
            "achat_item": achat_item,
            "vente_item": vente_item,
            "import_item": import_item,
            "model_comp": model_comp,
            "model_age": model_age,
            "model_avis": model_avis,
            "model_bail": model_bail,
            "category_nace": category_nace,
            "subcategory_nace": subcategory_nace,
        }

    def _upsert_acheteur(self, code, nom, years, refs, user):
        current_year = years[0]
        acheteur, _ = Acheteur.objects.update_or_create(
            code=code,
            defaults={
                "nom": nom,
                "sigle": "GDS",
                "description": "Acheteur de démonstration complet pour rapport de solvabilité.",
                "date_creation": date(current_year - 10, 6, 12),
                "activite_principale": "Distribution de produits industriels et services logistiques B2B",
                "email": "contact@gds-gabon.ga",
                "site_internet": "https://www.gds-gabon.ga",
                "numero_adresse": "18",
                "rue_adresse": "Boulevard Triomphal",
                "code_postal": "BP-2281",
                "boite_postale": "BP 2281",
                "fax": "+24101123456",
                "pays": refs["pays"],
                "province": refs["province"],
                "ville": refs["ville"],
                "categorie_entreprise": refs["categorie"],
                "forme_juridique": refs["forme"],
                "statut_entreprise": refs["statut"],
                "couleur_commentaire": refs["couleur"],
                "commentaire": "Dossier généré automatiquement pour tests reporting solvabilité.",
                "created_by": user,
                "updated_by": user,
            },
        )
        TelephoneAcheteur.objects.update_or_create(
            acheteur=acheteur,
            telephone="+241 06 12 34 56",
            defaults={"created_by": user, "updated_by": user},
        )
        CodeNaceAcheteur.objects.get_or_create(acheteur=acheteur, code=refs["subcategory_nace"])
        return acheteur

    def _upsert_reporting_sections(self, acheteur, refs, user):
        Resume.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "devise": refs["devise_xaf"],
                "capital_social": Decimal("350000000"),
                "chiffre_affaire": Decimal("1480000000"),
                "resultat_net": Decimal("183000000"),
                "capitaux_propre": Decimal("620000000"),
                "nombre_employe": Decimal("142"),
                "date_creation": date(2015, 6, 12),
                "commentaire": "Activité rentable et structure de capital satisfaisante.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        DonneesEnregistrement.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "nom_anterieur": "GDS Trading SA",
                "date_creation": date(2015, 6, 12),
                "date_registre": date(2015, 7, 2),
                "forme_juridique": self._first_choice(DonneesEnregistrement, "forme_juridique", fallback=""),
                "numero_registre_commerce": "RCCM-GA-LBV-2015-B-2281",
                "numero_fiscale": "NIF-10024578-GA",
                "statut_registre": self._first_choice(DonneesEnregistrement, "statut_registre", fallback=""),
                "commentaire": "Registre et fiscalité à jour.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        RiskRating.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "remboursabilite": True,
                "situation_liquidite": True,
                "performance_rentabilite": True,
                "perspective_secteur": True,
                "qualite_information_analyse": True,
                "existence_garantie": True,
                "terme_financier_duree_pret": True,
                "mesure_propre_soutenir_credit": True,
                "cotation_du_risque": "risque_faible",
                "indice_du_risque": "faible",
                "interpretation": "Risque de contrepartie contenu avec fondamentaux solides.",
                "analyse": "Cash-flow positif, gouvernance stable, environnement commercial favorable.",
                "created_by": user,
                "updated_by": user,
            },
        )

        OpinionCreditAcremac.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "risque_de_defaut": 1,
                "risque_de_concentration_credit": 2,
                "risque_de_reputation": 1,
                "risque_pays": 2,
                "risque_de_taux_dinteret": 2,
                "risque_de_liquidite": 1,
                "risque_eleve": 0,
                "risque_moyen": 2,
                "risque_faible": 7,
                "montant_credit_maximum": Decimal("500000000"),
                "commentaire": "Opinion globalement favorable avec limite de crédit significative.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        AntecedantsJuridique.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "dossier_faillite": "Aucun dossier connu",
                "jugement_cour": "Aucun jugement défavorable",
                "antecedant_redressement": "Aucun redressement",
                "Autre": "Néant",
                "commentaire": "Aucun antécédent juridique significatif.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        RiskManagment.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "professionalisme": RiskManagment.STATUS_OUI,
                "organisation": RiskManagment.STATUS_OUI,
                "turn_over": RiskManagment.STATUS_NON,
                "greve": RiskManagment.STATUS_NON,
                "degradation_qualite": RiskManagment.STATUS_NON,
                "non_respect_condition": RiskManagment.STATUS_NON,
                "commentaire": "Management expérimenté, continuité opérationnelle maîtrisée.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        ResponsableAcheteur.objects.update_or_create(
            acheteur=acheteur,
            nom="MBOUMBA",
            prenom="Armel",
            defaults={
                "Sexe": ResponsableAcheteur.STATUS_MASCULIN,
                "poste": self._first_choice(ResponsableAcheteur, "poste", fallback=""),
                "nationalite": "Gabonaise",
                "commentaire": "Directeur général.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )
        ResponsableAcheteur.objects.update_or_create(
            acheteur=acheteur,
            nom="NTOUTOUME",
            prenom="Jessica",
            defaults={
                "Sexe": ResponsableAcheteur.STATUS_FEMININ,
                "poste": self._first_choice(ResponsableAcheteur, "poste", fallback=""),
                "nationalite": "Gabonaise",
                "commentaire": "Directrice financière.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        ConseilAdministration.objects.update_or_create(
            acheteur=acheteur,
            nom="MBOUMBA Armel",
            defaults={
                "fonction_dans_le_conseil": self._first_choice(ConseilAdministration, "fonction_dans_le_conseil", fallback=""),
                "numero_adresse": "18",
                "rue_adresse": "Boulevard Triomphal",
                "code_postale_adresse": "BP-2281",
                "commentaire": "Présidence active.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        CompositionCapitalSocial.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "devise": refs["devise_xaf"],
                "emis": Decimal("350000000"),
                "publie": Decimal("350000000"),
                "libere": Decimal("350000000"),
                "commentaire": "Capital totalement libéré.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        CompositionAction.objects.update_or_create(
            acheteur=acheteur,
            nom="MBOUMBA",
            prenom="Armel",
            defaults={
                "pourcentage": Decimal("60"),
                "commentaire": "Actionnaire de contrôle.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )
        CompositionAction.objects.update_or_create(
            acheteur=acheteur,
            nom="NTOUTOUME",
            prenom="Jessica",
            defaults={
                "pourcentage": Decimal("40"),
                "commentaire": "Actionnaire cofondatrice.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        Structure.objects.update_or_create(
            acheteur=acheteur,
            nom="Agence Port-Gentil",
            defaults={
                "type_affiliation": self._first_choice(Structure, "type_affiliation", fallback=""),
                "numero_adresse": "44",
                "rue_adresse": "Avenue du Littoral",
                "code_postale_adresse": "PG-002",
                "commentaire": "Branche opérationnelle zone Ogooué-Maritime.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        AnalyseSectorielle.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "commentaire": "Demande soutenue sur les services logistiques régionaux.",
                "impact_covid_19": "Impact ponctuel absorbé par diversification clients.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        Tendance.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "avis_commercial": refs["avis_list"],
                "plus_informations": self._first_choice(Tendance, "plus_informations", fallback=""),
                "presse_media": "Présence média neutre et institutionnelle.",
                "alarmes": self._first_choice(Tendance, "alarmes", fallback=""),
                "principaux_concurrent": "Concurrent local A; Concurrent régional B",
                "commentaire": "Tendance globale stable à favorable.",
                "created_by": user,
                "updated_by": user,
            },
        )

        Geopolitics.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "stabilite_politique": "7",
                "etat_droit": "6",
                "efficacite": "6",
                "qualite": "6",
                "liberte_expression": "5",
                "donnees_politiques": "Stabilité institutionnelle relative sur les 24 derniers mois.",
                "donnees_economiques": "Croissance soutenue par l'investissement public et privé.",
                "created_by": user,
                "updated_by": user,
            },
        )

        Banquier.objects.update_or_create(
            acheteur=acheteur,
            nom_banque="BGFI Bank Gabon",
            defaults={
                "numero_compte": "GA4600001000987654321",
                "type_relation": "Compte courant professionnel",
                "numero": "101",
                "rue": "Avenue de Cointet",
                "ville": refs["ville"],
                "code_postal": "LBV-001",
                "commentaire": "Relation bancaire stable.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        CompteFinancier.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "cabinet": "Cabinet d'Audit Central Afrique",
                "requis_pour_deposer": "Oui",
                "credibilite_cabinet": CompteFinancier.OUI,
                "source": "États certifiés",
                "presentation": "Conforme SYSCOHADA",
                "date_compte": date(2025, 1, 1),
                "date_fin": date(2025, 12, 31),
                "date_compte_n_moins_un": date(2024, 1, 1),
                "date_fin_n_moins_un": date(2024, 12, 31),
                "date_compte_n_moins_deux": date(2023, 1, 1),
                "date_fin_n_moins_deux": date(2023, 12, 31),
                "type_compte": "Annuel",
                "devise": "XAF",
                "type_bilan": "Classique",
                "commentaire": "Comptes exploitables pour scoring.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

        op_hist, _ = OperationEtHistorique.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "commentaire_ratios": "Ratios de liquidité et solvabilité satisfaisants.",
                "description_complete_activite": "Distribution, logistique et maintenance industrielle.",
                "historique": "Croissance régulière depuis 2015 avec extension régionale.",
                "created_by": user,
                "updated_by": user,
            },
        )
        op_hist.importation.set([refs["import_item"]])

        prop, _ = ProprieteEtActif.objects.update_or_create(
            acheteur=acheteur,
            branche="Activités logistiques et négoce",
            defaults={"created_by": user, "updated_by": user},
        )
        prop.locaux.set([refs["local_item"]])

        achat, _ = ConditionAchat.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "les_clients": "Clientèle privée et institutionnelle diversifiée.",
                "fournisseur": "Fournisseurs multirégionaux avec contrats-cadres.",
                "created_by": user,
                "updated_by": user,
            },
        )
        achat.local.set([refs["achat_item"]])
        achat.importation.set([refs["achat_item"]])

        vente, _ = ConditionDeVente.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "recouvrement_de_dette_jugement": self._first_choice(ConditionDeVente, "recouvrement_de_dette_jugement", fallback=""),
                "comportement_de_paiement": self._first_choice(ConditionDeVente, "comportement_de_paiement", fallback=""),
                "created_by": user,
                "updated_by": user,
            },
        )
        vente.local.set([refs["vente_item"]])

        Advice.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "points_forts": "Base clients fidèle, rentabilité opérationnelle robuste.",
                "points_faibles": "Sensibilité modérée au prix des intrants logistiques.",
                "dynamisme_court_terme": "Hausse des volumes contractuels.",
                "dynamisme_long_terme": "Perspectives favorables grâce aux infrastructures nationales.",
                "risque_potentiel_court_terme": "Risque de tension sur supply chain internationale.",
                "created_by": user,
                "updated_by": user,
            },
        )

        SommaireEtAvis.objects.update_or_create(
            acheteur=acheteur,
            defaults={
                "commentaire": "Avis global favorable avec risque de défaut limité.",
                "couleur_commentaire": refs["couleur"],
                "created_by": user,
                "updated_by": user,
            },
        )

    def _upsert_scoring_sans_bilan(self, acheteur, refs, user):
        # Le modèle ScoringSansBilanAcheteur contient des print() avec emoji
        # incompatibles cp1252 sur certaines consoles Windows.
        original_print = builtins.print
        builtins.print = lambda *args, **kwargs: None
        try:
            scoring, _ = ScoringSansBilanAcheteur.objects.update_or_create(
                acheteur=acheteur,
                defaults={
                    "code": f"SSB-{acheteur.code}",
                    "libelle": "Scoring sans bilan - Gabon",
                    "comportement_de_paiement_ref": refs["model_comp"],
                    "age_company_ref": refs["model_age"],
                    "forme_juridique": refs["forme"],
                    "avis_commercial_ref": refs["model_avis"],
                    "locaux_ref": refs["model_bail"],
                    "commentaire": "Scoring sans bilan généré automatiquement.",
                    "created_by": user,
                    "updated_by": user,
                },
            )
            scoring.categories_nace_ref.set([refs["category_nace"]])
            scoring.scoring_value = scoring.calculate_scoring_value()
            scoring.interpretation = scoring.generate_interpretation()
            scoring.save(update_fields=["scoring_value", "interpretation", "updated_at", "updated_by"])
        finally:
            builtins.print = original_print

    def _upsert_commande(self, acheteur, refs, user):
        from main.models import Commande

        Commande.objects.update_or_create(
            acheteur=acheteur,
            reference_client=f"CMD-{acheteur.code}",
            defaults={
                "notre_ref": f"ACR-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                "raison_sociale": acheteur.nom,
                "type_rapport": "--------",
                "date_recept_commande": timezone.localdate(),
                "date_rapport": timezone.localdate(),
                "delais": "10 jours",
                "priorite": "Normale",
                "credit_demande": Decimal("250000000"),
                "credit_recommande": Decimal("210000000"),
                "devise_credit_demande": refs["devise_xaf"],
                "devise_credit_recommande": refs["devise_xaf"],
                "numero_adresse": acheteur.numero_adresse or "18",
                "rue_adresse": acheteur.rue_adresse or "Boulevard Triomphal",
                "code_postale_adresse": acheteur.code_postal or "BP-2281",
                "telephone": "+24106123456",
                "email": acheteur.email or "contact@gds-gabon.ga",
                "pays": refs["pays"],
                "ville": refs["ville"],
                "client": user,
                "status": "nouvelle",
                "type_commande": "NORMALE",
                "type_traitement": "MANUEL",
                "client_nom": user.get_username() if hasattr(user, "get_username") else str(user),
            },
        )

    def _upsert_financials(self, acheteur, years, user):
        models_to_seed = [
            ActifC, PassifC, ResultatC,
            ActifA, PassifA, ResultatA,
            ActifS, PassifS, ResultatS,
            Assets, Liabilities, Products, Expenses, OffBalanceSheet,
            ActifIFRS, PassifIFRS, ResultatIFRS,
        ]
        for idx, year in enumerate(years):
            annee, _ = Annee.objects.get_or_create(annee=year, defaults={"is_active": True})
            base = Decimal("1000000") + (Decimal(idx) * Decimal("350000"))
            for model_cls in models_to_seed:
                self._upsert_financial_model(model_cls, acheteur, annee, base, user)

    def _upsert_financial_model(self, model_cls, acheteur, annee, base, user):
        field_names = [f.name for f in model_cls._meta.fields]
        decimal_fields = [f.name for f in model_cls._meta.fields if f.__class__.__name__ == "DecimalField"]

        defaults = {}
        for i, name in enumerate(decimal_fields):
            defaults[name] = base + Decimal(i * 1000)

        if "created_by" in field_names:
            defaults["created_by"] = user
        if "updated_by" in field_names:
            defaults["updated_by"] = user
        if "type_bilan" in field_names:
            defaults["type_bilan"] = "annuel"

        lookup = {"acheteur": acheteur, "annee": annee}
        if "semestre" in field_names:
            lookup["semestre"] = None

        model_cls.objects.update_or_create(**lookup, defaults=defaults)
