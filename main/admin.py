from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role', 'is_active', 'activation', 'auth_a2f', 'telephone', 'profession', 'email_cc')
    list_filter = ('is_staff', 'is_active', 'activation', 'auth_a2f', 'is_active', 'role')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'avatar', 'address', 'telephone', 'profession', 'email_cc')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Custom fields', {'fields': ('code_connexion', 'code_secret', 'activation', 'auth_a2f')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'role', 'avatar', 'address', 'telephone', 'profession', 'email_cc', 'is_active', 'is_staff', 'activation', 'auth_a2f', 'code_connexion', 'code_secret')}
        ),
    )
    search_fields = ('username', 'email', 'role', 'first_name', 'last_name', 'telephone', 'profession', 'email_cc')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)



@admin.register(Pays)
class PaysAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'afficher_au_dashboard', 'is_active', 'date_creation', 'date_modification')
    list_filter = ('afficher_au_dashboard', 'is_active')
    search_fields = ('nom', 'code')
    ordering = ('nom',)
    readonly_fields = ('date_creation', 'date_modification')
    fieldsets = (
        (None, {
            'fields': ('nom', 'code', 'afficher_au_dashboard', 'is_active')
        }),
        ('Dates importantes', {
            'fields': ('date_creation', 'date_modification'),
        }),
    )
    
    
@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'pays', 'is_active', 'date_creation', 'date_modification')
    list_filter = ('is_active', 'pays')
    search_fields = ('nom', 'code')
    ordering = ('nom',)
    readonly_fields = ('date_creation', 'date_modification')
    fieldsets = (
        (None, {
            'fields': ('nom', 'code', 'pays', 'is_active')
        }),
        ('Dates importantes', {
            'fields': ('date_creation', 'date_modification'),
        }),
    )
    
    
@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'pays', 'province', 'is_active', 'date_creation', 'date_modification')
    list_filter = ('is_active', 'pays', 'province')
    search_fields = ('nom', 'code')
    ordering = ('nom',)
    readonly_fields = ('date_creation', 'date_modification')
    fieldsets = (
        (None, {
            'fields': ('nom', 'code', 'pays', 'province', 'is_active')
        }),
        ('Dates importantes', {
            'fields': ('date_creation', 'date_modification'),
        }),
    )
    
    
@admin.register(Annee)
class AnneeAdmin(admin.ModelAdmin):
    list_display = ("annee", "is_active", "date_creation", "date_modification")
    list_filter = ("is_active",)  # Ajoute des filtres par statut actif/inactif
    search_fields = ("annee",)  # Ajoute une barre de recherche
    ordering = ("annee",)  # Trie les années dans l'ordre croissant
    list_editable = ("is_active",)  # Permet de modifier rapidement le statut actif/inactif
    readonly_fields = ("date_creation", "date_modification")  # Champs en lecture seule


@admin.register(Devise)
class DeviseAdmin(admin.ModelAdmin):
    list_display = ("nom", "code", "symbole", "is_active", "date_creation", "date_modification")
    list_filter = ("is_active",)  # Filtre par statut actif/inactif
    search_fields = ("nom", "code")  # Ajoute une barre de recherche
    ordering = ("nom",)  # Trie les devises par ordre alphabétique
    list_editable = ("is_active",)  # Permet de modifier rapidement le statut actif/inactif
    readonly_fields = ("date_creation", "date_modification")  # Champs en lecture seule
    
    
class CouleurCommentaireAdmin(admin.ModelAdmin):
    list_display = ['couleur', 'code']  # Ce qui sera affiché dans la liste
    search_fields = ['couleur', 'code']  # Permet de rechercher par couleur et code
    list_filter = ['couleur']  # Permet de filtrer par couleur

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


@admin.register(PosteEntreprise)
class PosteEntrepriseAdmin(admin.ModelAdmin):
    list_display = ["libelle", "domaine", "active", "created_at", "updated_at"]
    search_fields = ["libelle", "code", "domaine__libelle"]
    list_filter = ["domaine", "active"]
    ordering = ["libelle"]
    
    
class BaseModeleAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'libelle', 'created_at', 'updated_at')
    search_fields = ('code', 'libelle')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at',)

admin.site.register(ModeleRapport, BaseModeleAdmin)
admin.site.register(ModeleAvisCommercial, BaseModeleAdmin)
admin.site.register(ModeleAlarme, BaseModeleAdmin)
admin.site.register(ModeleBilan, BaseModeleAdmin)
admin.site.register(ModeleBail, BaseModeleAdmin)
admin.site.register(ModeleRelationEntreprise, BaseModeleAdmin)
admin.site.register(ModeleInformationNotationEntreprise, BaseModeleAdmin)
admin.site.register(ModeleComportementPaiement, BaseModeleAdmin)
admin.site.register(ModeleComportementJugement, BaseModeleAdmin)
    
    

