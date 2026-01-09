from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _


from main.models import *

# Register your models here.


class UserAdmin(UserAdmin):
    model = User
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "role",
        "is_active",
        "activation",
        "auth_a2f",
        "telephone",
        "profession",
        "email_cc",
        "pays",
    )
    list_filter = (
        "is_staff",
        "is_active",
        "activation",
        "auth_a2f",
        "is_active",
        "role",
        "pays",
    )
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "avatar",
                    "address",
                    "telephone",
                    "profession",
                    "email_cc",
                    "pays",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        (
            "Custom fields",
            {"fields": ("code_connexion", "code_secret", "activation", "auth_a2f")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "avatar",
                    "address",
                    "telephone",
                    "profession",
                    "email_cc",
                    "is_active",
                    "is_staff",
                    "activation",
                    "auth_a2f",
                    "code_connexion",
                    "code_secret",
                    "pays",
                ),
            },
        ),
    )
    search_fields = (
        "username",
        "email",
        "role",
        "first_name",
        "last_name",
        "telephone",
        "profession",
        "email_cc",
        "pays",
    )
    ordering = ("username",)


admin.site.register(User, UserAdmin)


@admin.register(Pays)
class PaysAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "code",
        "afficher_au_dashboard",
        "is_active",
        "date_creation",
        "date_modification",
    )
    list_filter = ("afficher_au_dashboard", "is_active")
    search_fields = ("nom", "code")
    ordering = ("nom",)
    readonly_fields = ("date_creation", "date_modification")
    fieldsets = (
        (None, {"fields": ("nom", "code", "afficher_au_dashboard", "is_active")}),
        (
            "Dates importantes",
            {
                "fields": ("date_creation", "date_modification"),
            },
        ),
    )


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "code",
        "pays",
        "is_active",
        "date_creation",
        "date_modification",
    )
    list_filter = ("is_active", "pays")
    search_fields = ("nom", "code")
    ordering = ("nom",)
    readonly_fields = ("date_creation", "date_modification")
    fieldsets = (
        (None, {"fields": ("nom", "code", "pays", "is_active")}),
        (
            "Dates importantes",
            {
                "fields": ("date_creation", "date_modification"),
            },
        ),
    )


@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "code",
        "province",
        "is_active",
        "date_creation",
        "date_modification",
    )
    list_filter = ("is_active", "province")
    search_fields = ("nom", "code")
    ordering = ("nom",)
    readonly_fields = ("date_creation", "date_modification")
    fieldsets = (
        (None, {"fields": ("nom", "code", "province", "is_active")}),
        (
            "Dates importantes",
            {
                "fields": ("date_creation", "date_modification"),
            },
        ),
    )


@admin.register(Annee)
class AnneeAdmin(admin.ModelAdmin):
    list_display = ("annee", "is_active", "date_creation", "date_modification")
    list_filter = ("is_active",)  # Ajoute des filtres par statut actif/inactif
    search_fields = ("annee",)  # Ajoute une barre de recherche
    ordering = ("annee",)  # Trie les années dans l'ordre croissant
    list_editable = (
        "is_active",
    )  # Permet de modifier rapidement le statut actif/inactif
    readonly_fields = ("date_creation", "date_modification")  # Champs en lecture seule


@admin.register(Devise)
class DeviseAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "code",
        "symbole",
        "is_active",
        "date_creation",
        "date_modification",
    )
    list_filter = ("is_active",)  # Filtre par statut actif/inactif
    search_fields = ("nom", "code")  # Ajoute une barre de recherche
    ordering = ("nom",)  # Trie les devises par ordre alphabétique
    list_editable = (
        "is_active",
    )  # Permet de modifier rapidement le statut actif/inactif
    readonly_fields = ("date_creation", "date_modification")  # Champs en lecture seule


class CouleurCommentaireAdmin(admin.ModelAdmin):
    list_display = ["couleur", "code"]  # Ce qui sera affiché dans la liste
    search_fields = ["couleur", "code"]  # Permet de rechercher par couleur et code
    list_filter = ["couleur"]  # Permet de filtrer par couleur


admin.site.register(CouleurCommentaire, CouleurCommentaireAdmin)


@admin.register(CategoryNaceCode)
class CategoryNaceCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "libelle", "active", "created_at", "updated_at"]
    search_fields = ["code", "libelle"]
    list_filter = ["active"]
    ordering = ["code"]
    inlines = []

    # Inline for subcategories
    class SubCategoryInline(admin.TabularInline):
        model = SubCategoryNaceCode
        extra = 1
        fields = ["code", "libelle", "active"]

    inlines = [SubCategoryInline]


@admin.register(SubCategoryNaceCode)
class SubCategoryNaceCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "libelle", "category", "active", "created_at", "updated_at"]
    search_fields = ["code", "libelle"]
    list_filter = ["active", "category"]
    ordering = ["code"]


@admin.register(CategoryNafCode)
class CategoryNafCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "libelle", "active", "created_at", "updated_at"]
    search_fields = ["code", "libelle"]
    list_filter = ["active"]
    ordering = ["code"]
    inlines = []

    # Inline for subcategories
    class SubCategoryInline(admin.TabularInline):
        model = SubCategoryNafCode
        extra = 1
        fields = ["code", "libelle", "active"]

    inlines = [SubCategoryInline]


@admin.register(SubCategoryNafCode)
class SubCategoryNafCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "libelle", "category", "active", "created_at", "updated_at"]
    search_fields = ["code", "libelle"]
    list_filter = ["active", "category"]
    ordering = ["code"]


@admin.register(FormeJuridique)
class FormeJuridiqueAdmin(admin.ModelAdmin):
    list_display = ["code", "libelle", "active", "created_at", "updated_at"]
    search_fields = ["code", "libelle"]
    list_filter = ["active"]
    ordering = ["code"]


@admin.register(DomaineEntreprise)
class DomaineEntrepriseAdmin(admin.ModelAdmin):
    list_display = ["code", "libelle", "active", "created_at", "updated_at"]
    search_fields = ["code", "libelle"]
    list_filter = ["active"]
    ordering = ["libelle"]


@admin.register(CategorieEntreprise)
class CategorieEntrepriseAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "libelle",
        "description",
        "active",
        "created_at",
        "updated_at",
    )
    search_fields = ("code", "libelle", "description")
    list_filter = ("active",)


@admin.register(StructureEntreprise)
class StructureEntrepriseAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "libelle",
        "description",
        "active",
        "created_at",
        "updated_at",
    )
    search_fields = ("code", "libelle", "description")
    list_filter = ("active",)


@admin.register(StatutEntreprise)
class StatutEntrepriseAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "libelle",
        "description",
        "active",
        "created_at",
        "updated_at",
    )
    search_fields = ("code", "libelle", "description")
    list_filter = ("active",)


@admin.register(PosteEntreprise)
class PosteEntrepriseAdmin(admin.ModelAdmin):
    list_display = ["libelle", "domaine", "active", "created_at", "updated_at"]
    search_fields = ["libelle", "code", "domaine__libelle"]
    list_filter = ["domaine", "active"]
    ordering = ["libelle"]


class BaseModeleAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "libelle", "created_at", "updated_at")
    search_fields = ("code", "libelle")
    list_filter = ("created_at", "updated_at")
    ordering = ("-created_at",)


admin.site.register(ModeleRapport, BaseModeleAdmin)
admin.site.register(ModeleAvisCommercial, BaseModeleAdmin)
admin.site.register(ModeleAlarme, BaseModeleAdmin)
admin.site.register(ModeleBilan, BaseModeleAdmin)
admin.site.register(ModeleBail, BaseModeleAdmin)
admin.site.register(ModeleRelationEntreprise, BaseModeleAdmin)
admin.site.register(ModeleInformationNotationEntreprise, BaseModeleAdmin)
admin.site.register(ModeleComportementPaiement, BaseModeleAdmin)
admin.site.register(ModeleComportementJugement, BaseModeleAdmin)


class AcheteurAdmin(admin.ModelAdmin):
    # Affichage des champs dans la liste d'administration
    list_display = (
        "code",
        "nom",
        "categorie_entreprise",
        "forme_juridique",
        "activite_principale",
        "email",
        "date_creation",
        "statut_entreprise",
    )

    # Champs qui peuvent être filtrés
    list_filter = (
        "code",
        "categorie_entreprise",
        "forme_juridique",
        "statut_entreprise",
        "pays",
        "province",
        "ville",
    )

    # Champs qui peuvent être recherchés
    search_fields = ("nom", "email", "activite_principale", "description")

    # Champs éditables directement dans la liste (si applicable)
    list_editable = ("email",)

    # Ajout de filtres de recherche supplémentaires pour des relations de clé étrangère
    autocomplete_fields = [
        "categorie_entreprise",
        "forme_juridique",
        "statut_entreprise",
        "pays",
        "province",
        "ville",
    ]

    # Configuration des champs affichés lors de l'ajout d'un nouvel objet
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "nom",
                    "sigle",
                    "description",
                    "activite_principale",
                    "date_creation",
                    "statut_entreprise",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "email",
                    "site_internet",
                    "numero_adresse",
                    "rue_adresse",
                    "code_postal",
                    "fax",
                    "boite_postale",
                )
            },
        ),
        ("Adresse", {"fields": ("pays", "province", "ville")}),
        ("Commentaires", {"fields": ("commentaire", "couleur_commentaire")}),
    )

    # Ajout d'une option pour formater les dates dans l'interface
    date_hierarchy = "date_creation"

    # Permet de lier les champs de recherche et d'ajout
    ordering = ["nom"]

    # Exclure des champs inutiles dans la liste d'édition ou d'ajout (par exemple)
    exclude = ("code",)

    # Validation avant la sauvegarde
    def save_model(self, request, obj, form, change):
        # Vous pouvez ajouter une logique personnalisée avant la sauvegarde
        super().save_model(request, obj, form, change)


# Enregistrer le modèle avec l'administration Django
admin.site.register(Acheteur, AcheteurAdmin)


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "capital_social",
        "chiffre_affaire",
        "resultat_net",
        "capitaux_propre",
        "nombre_employe",
        "date_creation",
        "couleur_commentaire",
        "created_at",
        "updated_at",
    )
    search_fields = ("acheteur__name", "commentaire")
    list_filter = ("couleur_commentaire", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(RiskRating)
class RiskRatingAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "remboursabilite",
        "situation_liquidite",
        "performance_rentabilite",
        "perspective_secteur",
        "qualite_information_analyse",
        "existence_garantie",
        "terme_financier_duree_pret",
        "mesure_propre_soutenir_credit",
        "created_at",
        "updated_at",
    )
    search_fields = ("acheteur__name", "interpretation", "analyse")
    list_filter = (
        "remboursabilite",
        "situation_liquidite",
        "performance_rentabilite",
        "perspective_secteur",
        "qualite_information_analyse",
        "existence_garantie",
        "terme_financier_duree_pret",
        "mesure_propre_soutenir_credit",
        "created_at",
        "updated_at",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(DonneesEnregistrement)
class DonneesEnregistrementAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "date_creation",
        "date_registre",
        "forme_juridique",
        "forme_juridique_ref",
        "numero_registre_commerce",
        "numero_fiscale",
        "statut_registre",
        "statut_registre_ref",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "acheteur__name",
        "numero_registre_commerce",
        "numero_fiscale",
        "commentaire",
    )
    list_filter = (
        "forme_juridique",
        "forme_juridique_ref",
        "statut_registre",
        "statut_registre_ref",
        "created_at",
        "updated_at",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(Tendance)
class TendanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "acheteur",
        "avis_commercial",
        "avis_commercial_ref",
        "created_at",
        "updated_at",
    )
    list_filter = ("avis_commercial", "avis_commercial_ref", "created_at")
    search_fields = (
        "acheteur__nom",
        "presse_media",
        "principaux_concurrent",
        "commentaire",
    )
    autocomplete_fields = ("acheteur", "avis_commercial_ref")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Informations générales",
            {"fields": ("acheteur", "avis_commercial", "avis_commercial_ref")},
        ),
        (
            "Détails",
            {"fields": ("presse_media", "principaux_concurrent", "commentaire")},
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )


class ResponsableAcheteurAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "prenom",
        "sexe",
        "poste",
        "acheteur",
        "created_at",
        "updated_at",
    )
    search_fields = ("nom", "prenom", "acheteur__nom")
    list_filter = ("sexe", "poste", "created_at", "updated_at")


class AntecedantsJuridiqueAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "dossier_faillite",
        "jugement_cour",
        "antecedant_redressement",
        "autre",
        "created_at",
        "updated_at",
    )
    search_fields = ("acheteur__nom", "dossier_faillite", "jugement_cour")
    list_filter = ("created_at", "updated_at")


class RiskManagmentAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "professionalisme",
        "organisation",
        "turn_over",
        "greve",
        "degradation_qualite",
        "non_respect_condition",
        "created_at",
        "updated_at",
    )
    search_fields = ("acheteur__nom",)
    list_filter = (
        "professionalisme",
        "organisation",
        "turn_over",
        "greve",
        "degradation_qualite",
        "non_respect_condition",
        "created_at",
        "updated_at",
    )


class ConseilAdministrationAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "fonction_dans_le_conseil",
        "acheteur",
        "created_at",
        "updated_at",
    )
    search_fields = ("nom", "acheteur__nom")
    list_filter = ("fonction_dans_le_conseil", "created_at", "updated_at")


class CompositionCapitalSocialAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "devise",
        "emis",
        "publie",
        "libere",
        "created_at",
        "updated_at",
    )
    search_fields = ("acheteur__nom",)
    list_filter = ("devise", "created_at", "updated_at")


class CompositionActionAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "prenom",
        "pourcentage",
        "acheteur",
        "created_at",
        "updated_at",
    )
    search_fields = ("nom", "prenom", "acheteur__nom")
    list_filter = ("created_at", "updated_at")


class OpinionCreditAcremacAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "risque_de_defaut",
        "risque_de_concentration_credit",
        "risque_de_reputation",
        "risque_pays",
        "risque_de_taux_dinteret",
        "risque_de_liquidite",
        "risque_eleve",
        "risque_moyen",
        "risque_faible",
        "created_at",
        "updated_at",
    )
    search_fields = ("acheteur__nom",)
    list_filter = ("created_at", "updated_at")


class StructureAdmin(admin.ModelAdmin):
    list_display = ("nom", "type_affiliation", "acheteur", "created_at", "updated_at")
    search_fields = ("nom", "acheteur__nom")
    list_filter = ("type_affiliation", "created_at", "updated_at")


admin.site.register(ResponsableAcheteur, ResponsableAcheteurAdmin)
admin.site.register(AntecedantsJuridique, AntecedantsJuridiqueAdmin)
admin.site.register(RiskManagment, RiskManagmentAdmin)
admin.site.register(ConseilAdministration, ConseilAdministrationAdmin)
admin.site.register(CompositionCapitalSocial, CompositionCapitalSocialAdmin)
admin.site.register(CompositionAction, CompositionActionAdmin)
admin.site.register(OpinionCreditAcremac, OpinionCreditAcremacAdmin)
admin.site.register(Structure, StructureAdmin)


class AnalyseSectorielleAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "couleur_commentaire",
        "commentaire",
        "impact_covid_19",
        "created_at",
        "updated_at",
    )
    search_fields = ("acheteur__nom", "commentaire", "impact_covid_19")
    list_filter = ("created_at", "updated_at", "couleur_commentaire")
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("acheteur", "couleur_commentaire")}),
        ("Contenu", {"fields": ("commentaire", "impact_covid_19")}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")


admin.site.register(AnalyseSectorielle, AnalyseSectorielleAdmin)


class CompteFinancierAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "cabinet",
        "requis_pour_deposer",
        "credibilite_cabinet",
        "source",
        "presentation",
        "date_compte",
        "date_fin",
        "date_compte_n_moins_un",
        "date_fin_n_moins_un",
        "date_compte_n_moins_deux",
        "date_fin_n_moins_deux",
        "type_compte",
        "devise",
        "type_bilan",
        "couleur_commentaire",
        "commentaire",
        "created_at",
        "updated_at",
    )
    search_fields = ("acheteur__nom", "cabinet", "commentaire")
    list_filter = (
        "credibilite_cabinet",
        "devise",
        "type_bilan",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "acheteur",
                    "cabinet",
                    "requis_pour_deposer",
                    "credibilite_cabinet",
                    "source",
                    "presentation",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "date_compte",
                    "date_fin",
                    "date_compte_n_moins_un",
                    "date_fin_n_moins_un",
                    "date_compte_n_moins_deux",
                    "date_fin_n_moins_deux",
                )
            },
        ),
        ("Compte", {"fields": ("type_compte", "devise", "type_bilan")}),
        ("Commentaire", {"fields": ("couleur_commentaire", "commentaire")}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")


admin.site.register(CompteFinancier, CompteFinancierAdmin)


class OperationEtHistoriqueAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "commentaire_ratios",
        "description_complete_activite",
        "get_importation_display",  # Utilisez la méthode au lieu du champ
        "historique",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "acheteur__nom",
        "commentaire_ratios",
        "description_complete_activite",
    )
    list_filter = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "acheteur",
                    "commentaire_ratios",
                    "description_complete_activite",
                    "importation",
                    "historique",
                )
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")


admin.site.register(OperationEtHistorique, OperationEtHistoriqueAdmin)


class ProprieteEtActifAdmin(admin.ModelAdmin):
    list_display = ("acheteur", "locaux_list", "branche", "created_at", "updated_at")
    search_fields = ("acheteur__nom", "locaux__nom", "branche")
    list_filter = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("acheteur", "locaux", "branche")}),
        (_("Dates"), {"fields": ("created_at", "updated_at")}),
    )

    def locaux_list(self, obj):
        return ", ".join(obj.locaux.values_list("nom", flat=True))

    locaux_list.short_description = _("Locaux")



admin.site.register(ProprieteEtActif, ProprieteEtActifAdmin)


class ConditionAchatAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "local_list",  # Remplacez par une méthode
        "importation_list",  # Remplacez par une méthode
        "les_clients",
        "fournisseur",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "acheteur__nom",
        "local__nom",  # Ajoutez le champ de recherche
        "importation__nom",  # Ajoutez le champ de recherche
        "les_clients",
        "fournisseur",
    )
    list_filter = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "acheteur",
                    "local",
                    "importation",
                    "les_clients",
                    "fournisseur",
                )
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")
    
    def local_list(self, obj):
        return ", ".join(obj.local.values_list("nom", flat=True)[:3])  # Ajustez "nom" selon votre modèle ListeConditionAchat
    
    local_list.short_description = _("Local")
    
    def importation_list(self, obj):
        return ", ".join(obj.importation.values_list("nom", flat=True)[:3])  # Ajustez "nom" selon votre modèle ListeConditionAchat
    
    importation_list.short_description = _("Importation")


admin.site.register(ConditionAchat, ConditionAchatAdmin)


class ConditionDeVenteAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "local_list",  # Remplacez par une méthode
        "recouvrement_de_dette_jugement",
        "comportement_de_paiement",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "acheteur__nom",
        "local__nom",  # Ajoutez le champ de recherche
        "recouvrement_de_dette_jugement",
        "comportement_de_paiement",
    )
    list_filter = (
        "recouvrement_de_dette_jugement",
        "comportement_de_paiement",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "acheteur",
                    "local",
                    "recouvrement_de_dette_jugement",
                    "comportement_de_paiement",
                )
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")
    
    def local_list(self, obj):
        return ", ".join(obj.local.values_list("nom", flat=True)[:3])  # Ajustez "nom" selon votre modèle ListeConditionVente
    
    local_list.short_description = _("Local")


admin.site.register(ConditionDeVente, ConditionDeVenteAdmin)


class SommaireEtAvisAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "couleur_commentaire",
        "commentaire",
        "created_at",
        "updated_at",
    )
    search_fields = ("acheteur__nom", "commentaire")
    list_filter = ("couleur_commentaire", "created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("acheteur", "couleur_commentaire", "commentaire")}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")


admin.site.register(SommaireEtAvis, SommaireEtAvisAdmin)


class AdviceAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "points_forts",
        "points_faibles",
        "dynamisme_court_terme",
        "dynamisme_long_terme",
        "created_at",
        "updated_at",
    )
    search_fields = ("acheteur__nom", "points_forts", "points_faibles")
    list_filter = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "acheteur",
                    "points_forts",
                    "points_faibles",
                    "dynamisme_court_terme",
                    "dynamisme_long_terme",
                )
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")


admin.site.register(Advice, AdviceAdmin)


class GeopoliticsAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "donnees_politiques",
        "donnees_economiques",
        "created_at",
        "updated_at",
    )
    search_fields = ("acheteur__nom", "donnees_politiques", "donnees_economiques")
    list_filter = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("acheteur", "donnees_politiques", "donnees_economiques")}),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")


admin.site.register(Geopolitics, GeopoliticsAdmin)


class BanquierAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "nom_banque",
        "numero_compte",
        "type_relation",
        "numero",
        "rue",
        "ville",
        "code_postal",
        "couleur_commentaire",
        "commentaire",
        "created_at",
        "updated_at",
    )
    search_fields = ("acheteur__nom", "nom_banque", "numero_compte", "commentaire")
    list_filter = ("ville", "couleur_commentaire", "created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "acheteur",
                    "nom_banque",
                    "numero_compte",
                    "type_relation",
                    "numero",
                    "rue",
                    "ville",
                    "code_postal",
                    "couleur_commentaire",
                    "commentaire",
                )
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    readonly_fields = ("created_at", "updated_at")


admin.site.register(Banquier, BanquierAdmin)


@admin.register(Logo)
class LogoAdmin(admin.ModelAdmin):
    list_display = ("acheteur", "image", "description", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("acheteur__nom", "description")
    ordering = ("-created_at",)


@admin.register(TelephoneAcheteur)
class TelephoneAcheteurAdmin(admin.ModelAdmin):
    list_display = (
        "telephone",
        "acheteur",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("telephone", "acheteur__nom")
    ordering = ("-created_at",)


@admin.register(PortableAcheteur)
class PortableAcheteurAdmin(admin.ModelAdmin):
    list_display = (
        "portable",
        "acheteur",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("portable", "acheteur__nom")
    ordering = ("-created_at",)


@admin.register(EmailAcheteur)
class EmailAcheteurAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "acheteur",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("email", "acheteur__nom")
    ordering = ("-created_at",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "titre",
        "fichier",
        "description",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("titre", "acheteur__nom")
    ordering = ("-created_at",)


@admin.register(Swot)
class SwotAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "forces",
        "faiblesses",
        "opportunites",
        "menaces",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("acheteur__nom", "forces", "faiblesses", "opportunites", "menaces")
    ordering = ("-created_at",)


@admin.register(ProduitService)
class ProduitServiceAdmin(admin.ModelAdmin):
    list_display = ("acheteur", "produits", "services", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("acheteur__nom", "produits", "services")
    ordering = ("-created_at",)


@admin.register(ProcedureCollective)
class ProcedureCollectiveAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "type_procedure",
        "date_ouverture",
        "date_cloture",
        "description",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "type_procedure",
        "date_ouverture",
        "date_cloture",
        "created_at",
        "updated_at",
    )
    search_fields = ("acheteur__nom", "type_procedure", "description")
    ordering = ("-created_at",)


@admin.register(RegistreCommerce)
class RegistreCommerceAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "numero",
        "date_inscription",
        "created_at",
        "updated_at",
    )
    list_filter = ("date_inscription", "created_at", "updated_at")
    search_fields = ("acheteur__nom", "numero")
    ordering = ("-created_at",)


@admin.register(Cotisation)
class CotisationAdmin(admin.ModelAdmin):
    list_display = (
        "acheteur",
        "numero",
        "date_affiliation",
        "created_at",
        "updated_at",
    )
    list_filter = ("date_affiliation", "created_at", "updated_at")
    search_fields = ("acheteur__nom", "numero")
    ordering = ("-created_at",)


@admin.register(CodeNaceAcheteur)
class CodeNaceAcheteurAdmin(admin.ModelAdmin):
    list_display = ("acheteur", "code", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("acheteur__nom", "code__code")
    ordering = ("-created_at",)


@admin.register(CodeNafAcheteur)
class CodeNafAcheteurAdmin(admin.ModelAdmin):
    list_display = ("acheteur", "code", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("acheteur__nom", "code__code")
    ordering = ("-created_at",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "message", "is_read", "created_at")
    list_filter = ("type", "is_read", "created_at")
    search_fields = ("user__username", "message")
    ordering = ("-created_at",)


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = (
        "notre_ref",
        "reference_client",
        "status",
        "raison_sociale",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "created_at", "updated_at")
    search_fields = ("notre_ref", "reference_client", "raison_sociale")
    ordering = ("-created_at",)


@admin.register(SuiviCommande)
class SuiviCommandeAdmin(admin.ModelAdmin):
    list_display = ("commande", "user", "action", "type", "date_action")
    list_filter = ("type", "date_action")
    search_fields = ("commande__notre_ref", "user__username", "action")
    ordering = ("-date_action",)


@admin.register(AffectationAnalyste)
class AffectationAnalysteAdmin(admin.ModelAdmin):
    list_display = ("commande", "analyste", "date_affectation")
    list_filter = ("date_affectation",)
    search_fields = ("commande__notre_ref", "analyste__username")
    ordering = ("-date_affectation",)


@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = ("commande", "analyste", "fichier", "date_soumission")
    list_filter = ("date_soumission",)
    search_fields = ("commande__notre_ref", "analyste__username")
    ordering = ("-date_soumission",)


@admin.register(ValidationRapport)
class ValidationRapportAdmin(admin.ModelAdmin):
    list_display = ("rapport", "validateur", "status", "date_validation")
    list_filter = ("status", "date_validation")
    search_fields = ("rapport__commande__notre_ref", "validateur__username")
    ordering = ("-date_validation",)


@admin.register(CredendoCommande)
class CredendoCommandeAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "nom",
        "pays",
        "montant",
        "devise",
        "priorite",
        "date_reception",
    )
    list_filter = ("pays", "priorite", "devise", "date_reception")
    search_fields = ("reference", "nom", "internal_bp_id", "email_id")
    readonly_fields = ("email_id", "texte_complet", "date_reception")
    ordering = ("-date_reception",)

    fieldsets = (
        (
            "Informations Générales",
            {
                "fields": (
                    "sender_id",
                    "email_id",
                    "reference",
                    "internal_bp_id",
                    "nom",
                    "identifiants",
                    "priorite",
                    "remarque",
                )
            },
        ),
        ("Adresse", {"fields": ("rue", "ville", "pays")}),
        ("Montant et Devise", {"fields": ("montant", "devise")}),
        ("Autres", {"fields": ("texte_complet", "date_reception")}),
    )


@admin.register(Alerte)
class AlerteAdmin(admin.ModelAdmin):
    list_display = ("reference", "objet", "created_at", "updated_at")
    search_fields = ("reference", "objet")
    list_filter = ("created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DocumentAlerte)
class DocumentAlerteAdmin(admin.ModelAdmin):
    list_display = ("titre", "alerte", "created_at", "updated_at")
    search_fields = ("titre", "alerte__reference")
    list_filter = ("created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


# admin.py
from django.contrib import admin

from .models import ElementSurveillance, Portefeuille  # Et Client etc.


@admin.register(ElementSurveillance)
class ElementSurveillanceAdmin(admin.ModelAdmin):
    list_display = ("nom", "code_interne", "categorie", "sous_categorie")
    list_filter = ("categorie", "sous_categorie")
    search_fields = ("nom", "code_interne", "description")


@admin.register(Portefeuille)
class PortefeuilleAdmin(admin.ModelAdmin):
    list_display = ("nom", "client", "created_at", "updated_at")
    list_filter = ("client", "created_at")
    search_fields = ("nom", "client__nom")
    filter_horizontal = ("elements_surveillance_actifs",)  # Ou filter_vertical


admin.site.register(Certification)
admin.site.register(InnovationDeveloppement)
admin.site.register(StrategiePlanification)
admin.site.register(ConformiteReglementation)



@admin.register(Locaux)
class LocauxAdmin(admin.ModelAdmin):
    list_display = ("nom",)
    search_fields = ("nom",)


@admin.register(ListeConditionAchat)
class ListeConditionAchatAdmin(admin.ModelAdmin):
    list_display = ("nom",)
    search_fields = ("nom",)



@admin.register(ListeConditionVente)
class ListeConditionVenteAdmin(admin.ModelAdmin):
    list_display = ("nom",)
    search_fields = ("nom",)



@admin.register(ListeImportation)
class ListeImportationAdmin(admin.ModelAdmin):
    list_display = ("short_libelle",)
    search_fields = ("libelle",)

    def short_libelle(self, obj):
        return obj.libelle[:80] + "…" if len(obj.libelle) > 80 else obj.libelle

    short_libelle.short_description = _("Libellé")



@admin.register(ListeComportementsPaiement)
class ListeComportementsPaiementAdmin(admin.ModelAdmin):
    list_display = ("libelle", "couleur")
    search_fields = ("libelle",)
    list_filter = ("couleur",)




@admin.register(ListeInformationsRating)
class ListeInformationsRatingAdmin(admin.ModelAdmin):
    list_display = ("libelle", "couleur")
    search_fields = ("libelle",)
    list_filter = ("couleur",)






@admin.register(ListeInformationsAvisCommercial)
class ListeInformationsAvisCommercialAdmin(admin.ModelAdmin):
    list_display = ("libelle", "couleur")
    search_fields = ("libelle",)
    list_filter = ("couleur",)




@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "user",
        "action_type",
        "object_type",
        "object_id",
        "ip_address",
    )
    list_filter = ("action_type", "object_type", "created_at")
    search_fields = ("user__username", "action_type", "details", "ip_address")
    date_hierarchy = "created_at"

    readonly_fields = (
        "user",
        "action_type",
        "object_type",
        "object_id",
        "details",
        "ip_address",
        "user_agent",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

