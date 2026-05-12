from rest_framework import serializers
from main.models import *




class ReportCommandeSerializer(serializers.ModelSerializer):
    client_username = serializers.CharField(source='client.username', read_only=True)
    acheteur_nom = serializers.CharField(source='acheteur.nom', read_only=True)
    pays_nom = serializers.CharField(source='pays.nom', read_only=True)
    ville_nom = serializers.CharField(source='ville.nom', read_only=True)
    devise_credit_demande_code = serializers.CharField(source='devise_credit_demande.code', read_only=True)
    devise_credit_recommande_code = serializers.CharField(source='devise_credit_recommande.code', read_only=True)
    type_rapport_libelle = serializers.CharField(source='ref_type_rapport.libelle', read_only=True)
    
    class Meta:
        model = Commande
        fields = [
            'id', 'notre_ref', 'reference_client', 'date_recept_commande', 
            'date_rapport', 'delais', 'priorite', 'raison_sociale', 'type_rapport_libelle',
            'credit_demande', 'devise_credit_demande_code', 'credit_recommande', 
            'devise_credit_recommande_code', 'numero_adresse', 'rue_adresse', 
            'code_postale_adresse', 'telephone', 'email', 'pays_nom', 'ville_nom',
            'client_username', 'acheteur_nom', 'status', 'date_envoi_client',
            'created_at', 'updated_at'
        ]

class ReportAcheteurSerializer(serializers.ModelSerializer):
    pays_nom = serializers.CharField(source='pays.nom', read_only=True)
    province_nom = serializers.CharField(source='province.nom', read_only=True)
    ville_nom = serializers.CharField(source='ville.nom', read_only=True)
    forme_juridique_libelle = serializers.CharField(source='forme_juridique.libelle', read_only=True)
    statut_entreprise_libelle = serializers.CharField(source='statut_entreprise.libelle', read_only=True)
    class Meta:
        model = Acheteur
        fields = [
            'id', 'code', 'nom', 'sigle', 'description', 'date_creation',
            'activite_principale', 'email', 'site_internet', 'fax', 'boite_postale',
            'numero_adresse', 'rue_adresse', 'code_postal', 'pays_nom', 'province_nom',
            'ville_nom', 'forme_juridique_libelle', 'statut_entreprise_libelle',
            'commentaire'
        ]

class ReportResumeSerializer(serializers.ModelSerializer):
    devise_code = serializers.CharField(source='devise.code', read_only=True)
    
    class Meta:
        model = Resume
        fields = [
            'capital_social', 'chiffre_affaire', 'resultat_net', 'capitaux_propre',
            'nombre_employe', 'date_creation', 'devise_code', 'commentaire'
        ]

class ReportRiskRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskRating
        fields = [
            'remboursabilite', 'situation_liquidite', 'performance_rentabilite',
            'perspective_secteur', 'qualite_information_analyse', 'existence_garantie',
            'terme_financier_duree_pret', 'mesure_propre_soutenir_credit',
            'cotation_du_risque', 'indice_du_risque', 'interpretation', 'analyse'
        ]

class ReportDonneesEnregistrementSerializer(serializers.ModelSerializer):
    forme_juridique_libelle = serializers.CharField(source='forme_juridique_ref.libelle', read_only=True)
    statut_registre_libelle = serializers.CharField(source='statut_registre_ref.libelle', read_only=True)
    
    class Meta:
        model = DonneesEnregistrement
        fields = [
            'date_creation', 'date_registre', 'forme_juridique_libelle',
            'numero_registre_commerce', 'numero_fiscale', 'statut_registre_libelle',
            'commentaire'
        ]

class ReportAntecedantsJuridiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AntecedantsJuridique
        fields = [
            'dossier_faillite', 'jugement_cour', 'antecedant_redressement',
            'autre', 'commentaire'
        ]

class ReportResponsableAcheteurSerializer(serializers.ModelSerializer):
    poste_libelle = serializers.CharField(source='poste_ref.libelle', read_only=True)
    
    class Meta:
        model = ResponsableAcheteur
        fields = [
            'nom', 'prenom', 'sexe', 'poste_libelle', 'nationalite', 'commentaire'
        ]

class ReportRiskManagmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskManagment
        fields = [
            'professionalisme', 'organisation', 'turn_over', 'greve',
            'degradation_qualite', 'non_respect_condition', 'commentaire'
        ]

class ReportCompositionCapitalSocialSerializer(serializers.ModelSerializer):
    devise_code = serializers.CharField(source='devise.code', read_only=True)
    
    class Meta:
        model = CompositionCapitalSocial
        fields = ['emis', 'publie', 'libere', 'devise_code', 'commentaire']

class ReportCompositionActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompositionAction
        fields = ['nom', 'prenom', 'pourcentage', 'commentaire']

class ReportStructureSerializer(serializers.ModelSerializer):
    type_affiliation_libelle = serializers.CharField(source='type_affiliation_ref.libelle', read_only=True)
    
    class Meta:
        model = Structure
        fields = ['nom', 'type_affiliation_libelle', 'numero_adresse', 'rue_adresse', 'code_postale_adresse', 'commentaire']

class ReportAnalyseSectorielleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyseSectorielle
        fields = ['impact_covid_19', 'commentaire']

class ReportTendanceSerializer(serializers.ModelSerializer):
    avis_commercial_libelle = serializers.CharField(source='avis_commercial_ref.libelle', read_only=True)
    
    class Meta:
        model = Tendance
        fields = ['avis_commercial_libelle', 'presse_media', 'principaux_concurrent', 'commentaire']

class ReportGeopoliticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geopolitics
        fields = ['donnees_politiques', 'donnees_economiques']

class ReportBanquierSerializer(serializers.ModelSerializer):
    ville_nom = serializers.CharField(source='ville.nom', read_only=True)
    
    class Meta:
        model = Banquier
        fields = [
            'nom_banque', 'numero_compte', 'type_relation', 'numero', 'rue',
            'ville_nom', 'code_postal', 'commentaire'
        ]

class ReportCompteFinancierSerializer(serializers.ModelSerializer):
    type_bilan_libelle = serializers.CharField(source='type_bilan_ref.libelle', read_only=True)
    
    class Meta:
        model = CompteFinancier
        fields = [
            'cabinet', 'requis_pour_deposer', 'credibilite_cabinet', 'source',
            'presentation', 'type_compte', 'devise', 'type_bilan_libelle',
            'date_compte', 'date_fin', 'date_compte_n_moins_un', 'date_fin_n_moins_un',
            'date_compte_n_moins_deux', 'date_fin_n_moins_deux', 'commentaire'
        ]


class ReportOperationHistoriqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationEtHistorique
        fields = [
            'description_complete_activite', 'importation', 'historique',
            'commentaire_ratios'
        ]

class ReportProprieteActifSerializer(serializers.ModelSerializer):
    locaux_libelle = serializers.CharField(source='locaux_ref.libelle', read_only=True)
    
    class Meta:
        model = ProprieteEtActif
        fields = ['locaux_libelle', 'branche']

class ReportConditionAchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionAchat
        fields = ['local', 'importation', 'les_clients', 'fournisseur']

class ReportConditionVenteSerializer(serializers.ModelSerializer):
    comportement_paiement_libelle = serializers.CharField(source='comportement_de_paiement_ref.libelle', read_only=True)
    recouvrement_jugement_libelle = serializers.CharField(source='recouvrement_de_dette_jugement_ref.libelle', read_only=True)
    
    class Meta:
        model = ConditionDeVente
        fields = [
            'local', 'recouvrement_jugement_libelle', 'comportement_paiement_libelle'
        ]

class ReportSommaireAvisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SommaireEtAvis
        fields = ['commentaire']

class ReportAdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = [
            'points_forts', 'points_faibles', 'dynamisme_court_terme',
            'dynamisme_long_terme'
        ]

class ReportScoringSansBilanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoringSansBilanAcheteur
        fields = ['scoring_value', 'interpretation', 'commentaire']
        
        


# Serializers pour Bilan Classique
class ReportActifCSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    
    class Meta:
        model = ActifC
        fields = [
            'annee_valeur', 'capital_souscrit_non_app', 'frais_recherche_developpement',
            'brevet_licence_logiciels', 'fonds_commercial', 'autres_immobilisations_incorporelles',
            'terrains', 'constructions', 'materiels_et_outils', 'materiel_de_transport',
            'autres_immos_corp', 'immos_en_cours', 'avances_et_acptes', 'participations',
            'prets', 'autres', 'stocks_mp', 'stocks_encours_mp', 'stocks_pf', 'stocks_encours_pf',
            'stocks_encours_services', 'stocks_mses', 'avances_acptes_verses',
            'clients_et_cptes_rattaches', 'autres_creances', 'valeurs_a_encaisser',
            'banques_cheques_postaux_caisse', 'cca', 'charges_a_repartir_et_frais_etablissement',
            'primes_de_rbt', 'eca', 'eene', 'effectif', 'amortissements', 'provisions_stocks',
            'provisions_creances', 'provisions_vmp'
        ]

class ReportPassifCSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    
    class Meta:
        model = PassifC
        fields = [
            'annee_valeur', 'capital_social', 'primes', 'ecarts_de_reevaluation',
            'reserve', 'report_a_nouveau', 'resultat_exercice', 'subv_invest',
            'provision_regl', 'emprunts', 'dette_credit_bail_contrat_assimile',
            'dettes_financiere_diverses', 'provision_financiere_risque_charge',
            'dettes_fournisseurs_divers', 'avance_et_acomptes_recu', 'dettes',
            'dettes_fiscales_sociales', 'autres_dettes', 'banques_credit_escompte',
            'banque_credit_caisse', 'banques_decouvert', 'ecart_conversion_passif'
        ]

class ReportResultatCSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    
    class Meta:
        model = ResultatC
        fields = [
            'annee_valeur', 'vente_de_mdses', 'ventes_de_produits_fabriques',
            'travaux_services_vendus', 'produit_accessoires', 'production_imblise',
            'subventions_exploitations', 'production_stockee', 'reprises_de_provision',
            'transferts_charges', 'autres_produits', 'achat_mdses', 'variation_stock_mdses',
            'achat_mp_autres_appro', 'var_stk_mp_app', 'autres_achats',
            'variation_de_stocks_autres_appro', 'transports', 'services_ext',
            'impots_taxes', 'autres_charges_valeur_ajoutee', 'charges_personnel',
            'dotation_aux_amorts', 'dotation_aux_provisions', 'autres_charges_excedent_brute',
            'revenus_fin_assimiles', 'prof_vmp_et_cre_actif_immo', 'interets_produit_assim',
            'reprise_prov_et_transfert', 'diff_positive_de_change', 'prod_nets_cessions_vmp',
            'dap', 'frais_fin_charges_assi', 'diff_negatives_de_change', 'ch_nettes_cessions_vmp',
            'sur_op_gestion_prod_except', 'sur_op_en_capital_prod_except', 'reprise_prov_transfert',
            'sur_op_gestion_charg_except', 'sur_op_en_capital_charg_except',
            'dap_et_transfert_charg_except', 'participation_salairies', 'impot_sur_benefices'
        ]

class ReportRatiosClassiqueSerializer(serializers.Serializer):
    annee = serializers.IntegerField()
    fonds_de_roulement = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    autonomie_fin = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    liquidite_reduite = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    liquidite_immediat = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    rentabilite_economique = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    rentabilite_fin = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    rotation_des_stock_de_mp = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    rotation_des_stock_de_pf = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    credit_clients = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    credits_fournisseurs = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    solvabilite = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    rendement_capitaux_propres = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)        
    
    
    
# Serializers pour Bilan Anglais
class ReportActifASerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    
    class Meta:
        model = ActifA
        fields = [
            'annee_valeur', 'biens_installations_equipements', 'inventaire',
            'creances_commerciales_autres_creances', 'actif_impots_courant',
            'caisses_banques'
        ]

class ReportPassifASerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    
    class Meta:
        model = PassifA
        fields = [
            'annee_valeur', 'capital_reserves', 'capital_declare', 'benefices_non_distribues',
            'pret_bancaire', 'compte_courant_administrateurs', 'dettes_commerciales_autres_dettes',
            'decouvert_bancaire', 'impots'
        ]

class ReportResultatASerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    
    class Meta:
        model = ResultatA
        fields = [
            'annee_valeur', 'produits_activites_ordinaires', 'ventes', 'charges_exploitation',
            'frais_vente_generaux_administratifs', 'autres_revenus', 'frais_financier',
            'charge_impot_sur_revenu', 'autres_elements_resultat_global'
        ]

class ReportRatiosAnglaisSerializer(serializers.Serializer):
    annee = serializers.IntegerField()
    solvabilite = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    autonomie_financiere = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    rendement_capitaux_propres = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    taux_marge_net = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    liquidite_generale = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    jour_recouvrement_moyen = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    jour_paiement_moyen = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    
    
    
    

# Serializers pour Bilan SYSCOHADA
class ReportActifSSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    
    class Meta:
        model = ActifS
        fields = [
            'annee_valeur', 'frais_developpement_prospection', 'brevets_licences_logiciels',
            'droits_propriete_commerciale_baux', 'autres_immo_incorporelles', 'terrains',
            'dons_investissements_net', 'batiments', 'agencements_amenagements_installations',
            'materiel_mobilier_actif_biologiques', 'materiel_transport',
            'avances_acompte_immobilisations', 'titres_participation',
            'autres_immobilisations_financieres', 'actif_circulant_hao', 'stock_encours',
            'fournisseurs_avances_versee', 'clients', 'autres_creances',
            'valeurs_mobilieres_placement', 'disponibilites', 'banque_cheque_postal_caisse_assimiles',
            'ecart_conversion_actif'
        ]

class ReportPassifSSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    
    class Meta:
        model = PassifS
        fields = [
            'annee_valeur', 'capital', 'capital_non_appele_apporteurs', 'primes_liees_capital_social',
            'ecart_reevaluation', 'reserves_indisponibles', 'reserves_libres', 'report_nouveau',
            'resultat_net_exercice', 'subventions_investissements', 'provisions_reglees',
            'emprunts_dettes_financieres_diverse', 'dettes_location_vente', 'provisions_risques_charges',
            'passif_circulant_hao', 'clients_avances_recues', 'fournisseurs_exploitation',
            'dettes_fiscales_sociales', 'autres_dettes', 'provisions_risques_court_terme',
            'banques_credit_escompte', 'banques_etablissements_financiers_credit_caisse',
            'ecart_conversion_passif'
        ]

class ReportResultatSSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    
    class Meta:
        model = ResultatS
        fields = [
            'annee_valeur', 'ventes_marchandises_a', 'achats_marchandises', 'variation_stock_marchandises',
            'ventes_produits_manufactures', 'travaux_services_vendus_c', 'produits_accessoires_d',
            'production_stockee', 'production_immobilisee', 'subvention_exploitation', 'autres_produits',
            'transfert_charges_exploitation', 'achats_matieres_premieres_fournitures_connexes',
            'variation_stock_matieres_premieres_fournitures_connexes', 'autres_achats',
            'variation_stock_autres_fournitures', 'transport', 'services_exterieurs', 'impots_taxes',
            'autres_depenses', 'frais_personnel', 'reprise_depreciations_amortissements_provision_pertes_valeurs_p',
            'reprise_depreciations_amortissements_provision_pertes_valeurs_m', 'produits_financiers_assimiles',
            'reprise_provision_perte_valeur', 'transfert_charges_financieres', 'charges_financieres_assimilees',
            'dotations_provisions_depreciations_financieres', 'produits_cession_immobilisations',
            'autres_produits_hao', 'valeur_comptable_cessions_actifs_immobilises', 'autres_charges_hao',
            'participation_travailleurs', 'charge_impot_revenu'
        ]

class ReportRatiosSyscohadaSerializer(serializers.Serializer):
    annee = serializers.IntegerField()
    fonds_de_roulement = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    besoin_fonds_de_roulement = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    position_net_de_tresorerie = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    cafsys = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    autonomie_financiere = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    liquidite_general = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)
    rotation_stock = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    
    
    
    

# Serializers pour Bilan Bancaire
class ReportAssetsSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    semestre_display = serializers.CharField(source='get_semestre_display', read_only=True)
    
    class Meta:
        model = Assets
        fields = [
            'annee_valeur', 'semestre_display', 'type_bilan', 'caisse', 'banques_centrales',
            'tresorerie_cpp', 'autres_ets_credit', 'a_terme', 'credits_campagne',
            'credits_ordinaire', 'credits_campagne_acc', 'credits_ordinaire_acc',
            'creances_ordinaires', 'affacturage', 'titres_placement', 'immobilisation_fin',
            'operation_credit_bail', 'immobilisation_incorporelle', 'immobilisation_corporelle',
            'actionnaire_ou_associe', 'autres_actifs', 'comptes_commande_divers'
        ]

class ReportLiabilitiesSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    semestre_display = serializers.CharField(source='get_semestre_display', read_only=True)
    
    class Meta:
        model = Liabilities
        fields = [
            'annee_valeur', 'semestre_display', 'type_bilan', 'tresorerie_ccp',
            'autres_etablissement_credit', 'a_terme', 'comptes_epargne_court_terme',
            'comptes_epargne_terme', 'bons_caisse', 'autres_dette_a_vue',
            'autres_dette_a_terme', 'titres_creance_autres_dettes', 'compte_dordre_divers',
            'provision_pour_risque_charge', 'provision_reglementee', 'emprunt_subordonne_tire_emis',
            'subventions_investissement', 'fonds_affecte', 'fonds_pour_risque_bancaire_generaux',
            'capital_ou_dotation', 'primes_liees_reserve_capital', 'ecarts_reevaluation',
            'benefices_non_distribue', 'resultat_net_exercie'
        ]

class ReportExpensesSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    semestre_display = serializers.CharField(source='get_semestre_display', read_only=True)
    
    class Meta:
        model = Expenses
        fields = [
            'annee_valeur', 'semestre_display', 'type_bilan',
            'interet_charges_assimilee_dette_interbancaire',
            'interet_charge_assimilee_dette_clientele',
            'interet_charge_assimilee_titre_creance',
            'chargesc_compte_bloque_dactionnaire_emprunt_sub',
            'autres_interets_charges_assimilee',
            'charges_sur_op_credit_bail_assimile', 'commissions',
            'charges_sur_titre_placement', 'charges_sur_operation_change',
            'charges_sur_operation_hors_bilan', 'frais_divers_exploitation_bancaire',
            'achat_marchandises', 'stocks_vendus', 'variations_stocks_marchanides',
            'frais_personnel', 'autres_frais_generaux',
            'dotations_amortissement_provision_immobilisation',
            'solde_perte_creance_hors_bilan',
            'excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux',
            'charges_exceptionnelle', 'pertes_exercice_anterieurs', 'impot_sur_revenu'
        ]

class ReportProductsSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    semestre_display = serializers.CharField(source='get_semestre_display', read_only=True)
    
    class Meta:
        model = Products
        fields = [
            'annee_valeur', 'semestre_display', 'type_bilan',
            'interets_produit_assimile_sur_pret_avance_interbancaire',
            'ineterets_produit_assimile_pret_avance_clientele',
            'interet_produit_sur_titre_dinvestissement',
            'revenu_gains_titre_pret_titre_subordonne',
            'autres_interets_produits_assimiles',
            'produits_leansing_operation_connexes', 'commissions',
            'revenus_titre_negociable', 'dividendes_produits_assimiles',
            'revenus_operation_de_change', 'produits_opeations_hors_bilan',
            'produits_bancaire_divers', 'marges_vente', 'ventes_marchandises',
            'variation_stocks_marchandises', 'produit_dexploitation_generale',
            'reprise_damortissement_provisions_sur_immobilisation',
            'solde_resultat_correction_valeur_sur_creance_hors_bilan',
            'excedent_reprise_fonds_pour_risque_bancaire_generaux',
            'produits_exceptionnels', 'benefice_sur_exercice_anterieur', 'perte'
        ]

class ReportOffBalanceSheetSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    semestre_display = serializers.CharField(source='get_semestre_display', read_only=True)
    
    class Meta:
        model = OffBalanceSheet
        fields = [
            'annee_valeur', 'semestre_display', 'type_bilan',
            'engagement_financement_donne_ets_credit',
            'engagement_financement_donne_clientele',
            'engagement_garantie_donne_ets_credit',
            'engagement_garantie_donne_clientele',
            'engagement_sur_titres_donnes',
            'engagement_financement_recu_ets_credit',
            'engagement_financement_recu_clientele',
            'engagement_garantie_recu_ets_credit',
            'engagement_sur_titres_recus'
        ]
        
        
        
        
# Serializers pour Bilan IFRS COBAC
class ReportActifIFRSSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    semestre_display = serializers.CharField(source='get_semestre_display', read_only=True)
    
    class Meta:
        model = ActifIFRS
        fields = [
            'annee_valeur', 'semestre_display', 'type_bilan', 'goodwill',
            'marques_et_droits_auteur', 'brevets_et_licences', 'autres_immobilisations_incorporelles',
            'terrains', 'batiments', 'materiel_et_equipement', 'participations_dans_des_societes',
            'prets_a_long_terme', 'matieres_premieres', 'produits_finis', 'creances_a_court_terme',
            'avances_et_acomptes', 'creances_diverses', 'disponibilites_bancaires'
        ]

class ReportPassifIFRSSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    semestre_display = serializers.CharField(source='get_semestre_display', read_only=True)
    
    class Meta:
        model = PassifIFRS
        fields = [
            'annee_valeur', 'semestre_display', 'type_bilan', 'capital_social',
            'primes_emission', 'reserves_legales', 'reserves_statutaires', 'reserves_facultatives',
            'autres_reserves', 'resultat_net_reporte', 'emprunts_bancaires_long_terme',
            'obligations', 'provisions_pour_retraites_et_pensions', 'autres_provisions',
            'dettes_fournisseurs_a_court_terme', 'impots_sur_le_revenu', 'cotisations_sociales',
            'emprunts_bancaires_court_terme', 'dettes_diverses', 'dividendes_a_payer'
        ]

class ReportResultatIFRSSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    semestre_display = serializers.CharField(source='get_semestre_display', read_only=True)
    
    class Meta:
        model = ResultatIFRS
        fields = [
            'annee_valeur', 'semestre_display', 'type_bilan', 'ventes_biens', 'ventes_services',
            'subventions_exploitation', 'revenus_exceptionnels', 'revenus_financiers',
            'achats_matieres_premieres', 'autres_couts_directs', 'salaires_et_charges_sociales',
            'loyer_et_charges_locatives', 'autres_charges_exploitation',
            'amortissement_des_immobilisations', 'provisions_pour_risques_et_charges',
            'charges_financieres', 'impot_sur_les_societes'
        ]

class ReportRatiosIFRSSerializer(serializers.ModelSerializer):
    annee_valeur = serializers.IntegerField(source='annee.annee', read_only=True)
    
    class Meta:
        model = RatiosIFRS
        fields = [
            'annee_valeur', 'roa', 'roe', 'liquidite_generale', 'liquidite_immediate',
            'ratio_endettement_total', 'ratio_couverture_interets', 'marge_brute',
            'marge_operationnelle', 'marge_nette', 'rotation_des_actifs', 'dso'
        ]
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    



# Serializer principal qui agrège tous les autres
class ReportBilanDataSerializer(serializers.Serializer):
    """Serializer pour les données de bilan selon le type sélectionné"""
    type_bilan = serializers.CharField()
    annees = serializers.ListField(child=serializers.IntegerField())
    
    # Données pour bilan classique
    actifs_classique = ReportActifCSerializer(many=True, required=False)
    passifs_classique = ReportPassifCSerializer(many=True, required=False)
    resultats_classique = ReportResultatCSerializer(many=True, required=False)
    ratios_classique = ReportRatiosClassiqueSerializer(many=True, required=False)
    
    # Données pour bilan anglais
    actifs_anglais = ReportActifASerializer(many=True, required=False)
    passifs_anglais = ReportPassifASerializer(many=True, required=False)
    resultats_anglais = ReportResultatASerializer(many=True, required=False)
    ratios_anglais = ReportRatiosAnglaisSerializer(many=True, required=False)
    
    # Données pour bilan SYSCOHADA
    actifs_syscohada = ReportActifSSerializer(many=True, required=False)
    passifs_syscohada = ReportPassifSSerializer(many=True, required=False)
    resultats_syscohada = ReportResultatSSerializer(many=True, required=False)
    ratios_syscohada = ReportRatiosSyscohadaSerializer(many=True, required=False)
    
    # Données pour bilan bancaire
    actifs_bancaire = ReportAssetsSerializer(many=True, required=False)
    passifs_bancaire = ReportLiabilitiesSerializer(many=True, required=False)
    depenses_bancaire = ReportExpensesSerializer(many=True, required=False)
    produits_bancaire = ReportProductsSerializer(many=True, required=False)
    hors_bilan_bancaire = ReportOffBalanceSheetSerializer(many=True, required=False)
    
    # Données pour bilan IFRS
    actifs_ifrs = ReportActifIFRSSerializer(many=True, required=False)
    passifs_ifrs = ReportPassifIFRSSerializer(many=True, required=False)
    resultats_ifrs = ReportResultatIFRSSerializer(many=True, required=False)
    ratios_ifrs = ReportRatiosIFRSSerializer(many=True, required=False)

class ReportEvolutionStatisticsSerializer(serializers.Serializer):
    """Serializer pour les statistiques d'évolution sur 3 ans"""
    indicateur = serializers.CharField()
    annee_n = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    annee_n_1 = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    annee_n_2 = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    evolution_n_n1 = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    evolution_n1_n2 = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    tendance = serializers.CharField()  # 'hausse', 'baisse', 'stable'

# Serializer principal mis à jour
class ReportSolvabiliteCompletSerializer(serializers.Serializer):
    acheteur = ReportAcheteurSerializer(read_only=True)
    commande = ReportCommandeSerializer(read_only=True, required=False)  # Nouveau champ
    resume = ReportResumeSerializer(read_only=True)
    risk_rating = ReportRiskRatingSerializer(read_only=True)
    donnees_enregistrement = ReportDonneesEnregistrementSerializer(read_only=True)
    antecedants_juridiques = ReportAntecedantsJuridiqueSerializer(read_only=True)
    responsables = ReportResponsableAcheteurSerializer(many=True, read_only=True)
    risk_management = ReportRiskManagmentSerializer(read_only=True)
    capital_social = ReportCompositionCapitalSocialSerializer(read_only=True)
    actionnaires = ReportCompositionActionSerializer(many=True, read_only=True)
    structures = ReportStructureSerializer(many=True, read_only=True)
    analyse_sectorielle = ReportAnalyseSectorielleSerializer(read_only=True)
    tendance = ReportTendanceSerializer(read_only=True)
    geopolitics = ReportGeopoliticsSerializer(read_only=True)
    banquiers = ReportBanquierSerializer(many=True, read_only=True)
    compte_financier = ReportCompteFinancierSerializer(read_only=True)
    operation_historique = ReportOperationHistoriqueSerializer(read_only=True)
    proprietes_actifs = ReportProprieteActifSerializer(many=True, read_only=True)
    conditions_achat = ReportConditionAchatSerializer(read_only=True)
    conditions_vente = ReportConditionVenteSerializer(read_only=True)
    sommaire_avis = ReportSommaireAvisSerializer(read_only=True)
    advice = ReportAdviceSerializer(read_only=True)
    scoring_sans_bilan = ReportScoringSansBilanSerializer(read_only=True)
    
    # Champs calculés dynamiquement
    bilan_data = ReportBilanDataSerializer(read_only=True)
    ratios_data = serializers.DictField(read_only=True)
    evolution_statistics = ReportEvolutionStatisticsSerializer(many=True, read_only=True)
    statistiques_evolution = serializers.DictField(read_only=True)  # Pour les graphiques