from datetime import timedelta
from decimal import Decimal
import base64
import os

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Avg, Max, Min, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from safedelete.admin import SafeDeleteAdmin, highlight_deleted
from simple_history.admin import SimpleHistoryAdmin

from main.forms import *
from main.models import *


User = get_user_model()


# Register your models here.



@admin.register(Referer)
class RefererAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: RefererAdmin."""
    list_display = ['id', 'source', 'target'] + list(SafeDeleteAdmin.list_display)
    list_filter = ['source', 'target'] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['source__name', 'target__name']
    raw_id_fields = ['source', 'target']
    ordering = ['source__name']
    
    fieldsets = (
        (None, {
            'fields': ('source', 'target')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if obj:
            return fields + ('source', 'target')
        return fields

@admin.register(AdminMails)
class AdminMailsAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: AdminMailsAdmin."""
    list_display = ['id', 'email'] + list(SafeDeleteAdmin.list_display)
    list_filter = SafeDeleteAdmin.list_filter
    search_fields = ['email']
    ordering = ['email']
    
    fieldsets = (
        (None, {
            'fields': ('email',)
        }),
    )

@admin.register(User)
class UserAdmin(BaseUserAdmin, SimpleHistoryAdmin):  # Retirer SafeDeleteAdmin
    """Configuration admin: UserAdmin."""
    form = CustomUserChangeForm        # 🔴 OBLIGATOIRE
    add_form = CustomUserCreationForm  # 🔴 OBLIGATOIRE
    
    # Configuration pour l'affichage en liste
    list_display = [
        'username', 'email', 'fullname', 'role', 'pays',
        'is_active', 'is_staff', 'password_changed_at'
    ]

    list_filter = [
        'role', 'is_active', 'is_staff', 'pays',
        'auth_a2f', 'activation'
    ]
    
    search_fields = [
        'username', 'email', 'first_name', 'last_name',
        'telephone', 'profession', 'role',
    ]
    raw_id_fields = ['pays']
    ordering = ['username']
    filter_horizontal = ['affectation', 'affectation_possible']
    date_hierarchy = 'date_joined'
    
    # Configuration des formulaires (ajout et modification)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': (
                'avatar', 'first_name', 'last_name', 'email',
                'email_cc', 'telephone', 'address', 'profession',
            )
        }),
        (_('Permissions'), {
            'fields': (
                'role', 'is_active', 'is_staff', 'is_superuser',
                'activation', 'auth_a2f',
                'groups', 'user_permissions'
            ),
        }),
        (_('Location info'), {
            'fields': (
                'pays', 'affectation', 'affectation_possible'
            )
        }),
        (_('Security info'), {
            'fields': (
                'code_secret', 'code_connexion', 'reset_token',
                'password_changed_at'
            ),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'first_name', 'last_name', 'is_active',
                'is_staff'
            ),
        }),
        (_('Additional info'), {
            'classes': ('collapse',),
            'fields': (
                'telephone', 'address', 'profession', 'email_cc',
                'pays', 'activation', 'auth_a2f', 'role',
            ),
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return self.fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:
            # Empêcher la modification de certains champs après création
            readonly_fields.extend(['username', 'date_joined', 'password_changed_at'])
        return readonly_fields
    
    def fullname(self, obj):
        return obj.fullname()
    fullname.short_description = _('Full Name')
    fullname.admin_order_field = 'last_name'
    
    def get_form(self, request, obj=None, **kwargs):
        kwargs['fields'] = '__all__'
        return super().get_form(request, obj, **kwargs)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "pays":
            kwargs["queryset"] = Pays.all_objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


    
    def save_model(self, request, obj, form, change):
        # Appeler la méthode save personnalisée du modèle
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        # Utiliser le queryset normal puisque User n'utilise pas safedelete
        qs = super().get_queryset(request)
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs   


class VilleInline(admin.TabularInline):
    """Inline : gérer les villes directement depuis la fiche d'un pays."""
    model = Ville
    extra = 1
    fields = ['code', 'nom', 'is_active']
    ordering = ['nom']
    show_change_link = True
    verbose_name = _("Ville")
    verbose_name_plural = _("Villes du pays")


@admin.register(Pays)
class PaysAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):  # Retirer ImportExportModelAdmin si non installé
    """Configuration admin: PaysAdmin."""
    list_display = [
        'code', 'nom', 'is_active', 'afficher_au_dashboard', 
        'deleted', 'date_creation', 'date_modification'
    ]
    list_display_links = ['code', 'nom']
    list_filter = [
        'is_active', 'afficher_au_dashboard', 
        ('date_creation', admin.DateFieldListFilter),
        ('date_modification', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['nom', 'code']
    list_editable = ['is_active', 'afficher_au_dashboard']
    ordering = ['nom']
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'nom', 'devise')
        }),
        (_('Configuration'), {
            'fields': ('is_active', 'afficher_au_dashboard'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['date_creation', 'date_modification']
    inlines = [VilleInline]

    # Actions personnalisées
    actions = ['activate_countries', 'deactivate_countries', 'toggle_dashboard_display']
    
    @admin.action(description=_('Activer les pays sélectionnés'))
    def activate_countries(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} pays activés.', messages.SUCCESS)
    
    @admin.action(description=_('Désactiver les pays sélectionnés'))
    def deactivate_countries(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} pays désactivés.', messages.WARNING)
    
    @admin.action(description=_('Basculer l\'affichage dashboard'))
    def toggle_dashboard_display(self, request, queryset):
        for country in queryset:
            country.afficher_au_dashboard = not country.afficher_au_dashboard
            country.save(update_fields=['afficher_au_dashboard'])
        self.message_user(request, f'{queryset.count()} pays mis à jour.', messages.SUCCESS)


@admin.register(Ville)
class VilleAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Villes — liées directement à un pays."""
    list_display = ['code', 'nom', 'pays', 'is_active', 'deleted', 'date_creation']
    list_display_links = ['code', 'nom']
    list_filter = [
        'is_active', 'pays',
        ('date_creation', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['nom', 'code', 'pays__nom']
    list_select_related = ['pays']
    list_editable = ['is_active']
    autocomplete_fields = ['pays']
    ordering = ['pays__nom', 'nom']

    fieldsets = (
        (_('Informations'), {
            'fields': ('code', 'nom', 'pays', 'is_active')
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['date_creation', 'date_modification']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('pays')

@admin.register(Region)
class RegionAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Régions — liées à un pays."""
    list_display = ['code', 'nom', 'pays', 'is_active', 'deleted']
    list_display_links = ['code', 'nom']
    list_filter = ['is_active', 'pays'] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['nom', 'code', 'pays__nom']
    list_select_related = ['pays']
    list_editable = ['is_active']
    autocomplete_fields = ['pays']
    ordering = ['pays__nom', 'nom']

    fieldsets = (
        (_('Informations'), {
            'fields': ('code', 'nom', 'pays', 'is_active')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('pays')


@admin.register(Annee)
class AnneeAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: AnneeAdmin."""
    list_display = [
        'annee', 'is_active', 'deleted', 'date_creation', 'date_modification'
    ]
    list_filter = [
        'is_active',
        'annee',  # filtre simple sur IntegerField
        ('date_creation', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['annee']
    list_editable = ['is_active']
    ordering = ['-annee']
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('annee',)
        }),
        (_('Statut'), {
            'fields': ('is_active',),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['date_creation', 'date_modification']
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'annee':
            kwargs['min_value'] = 1900
            kwargs['max_value'] = 2100
        return super().formfield_for_dbfield(db_field, request, **kwargs)

@admin.register(Devise)
class DeviseAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: DeviseAdmin."""
    list_display = [
        'code', 'nom', 'symbole', 'is_active', 'deleted', 
        'date_creation', 'date_modification'
    ]
    list_filter = [
        'is_active',
        ('date_creation', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['code', 'nom', 'symbole']
    list_editable = ['is_active', 'symbole']
    ordering = ['nom']
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'nom', 'symbole')
        }),
        (_('Statut'), {
            'fields': ('is_active',),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['date_creation', 'date_modification']
    
    @admin.action(description=_('Définir comme devises principales (EUR, USD, XAF)'))
    def set_main_currencies(self, request, queryset):
        main_currencies = {
            'EUR': {'nom': 'Euro', 'symbole': '€'},
            'USD': {'nom': 'Dollar américain', 'symbole': '$'},
            'XAF': {'nom': 'Franc CFA', 'symbole': 'FCFA'},
        }
        
        for code, data in main_currencies.items():
            Devise.objects.update_or_create(
                code=code,
                defaults={
                    'nom': data['nom'],
                    'symbole': data['symbole'],
                    'is_active': True
                }
            )
        self.message_user(request, 'Devises principales mises à jour.', messages.SUCCESS)

@admin.register(CouleurCommentaire)
class CouleurCommentaireAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: CouleurCommentaireAdmin."""
    list_display = [
        'couleur', 'code', 'color_preview', 'deleted'
    ]
    list_filter = SafeDeleteAdmin.list_filter
    search_fields = ['couleur', 'code']
    ordering = ['couleur']
    
    fieldsets = (
        (_('Informations de couleur'), {
            'fields': ('couleur', 'code'),
            'description': _('Utilisez des codes hexadécimaux (#FF5733) ou des noms de couleur CSS.')
        }),
    )
    
    def color_preview(self, obj):
        if obj.code:
            return format_html(
                '<div style="width: 20px; height: 20px; background-color: {}; '
                'border: 1px solid #ccc; display: inline-block; margin-right: 10px;"></div>'
                '<span>{}</span>',
                obj.code, obj.code
            )
        return "-"
    color_preview.short_description = _('Aperçu')
    color_preview.allow_tags = True
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'code':
            kwargs['widget'] = admin.widgets.AdminTextInputWidget(attrs={
                'style': 'width: 100px;',
                'placeholder': '#FF5733'
            })
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
    
    


@admin.register(CategoryNaceCode)
class CategoryNaceCodeAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: CategoryNaceCodeAdmin."""
    list_display = [
        'code', 'libelle', 'active', 'poids', 
        'subcategories_count', 'deleted', 'created_at'
    ]
    list_display_links = ['code', 'libelle']
    list_filter = [
        'active',
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['code', 'libelle']
    list_editable = ['active', 'poids']
    ordering = ['code']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle')
        }),
        (_('Paramètres'), {
            'fields': ('active', 'poids')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def subcategories_count(self, obj):
        return obj.subcategories.count()
    subcategories_count.short_description = _('Nb sous-catégories')
    subcategories_count.admin_order_field = 'subcategories_count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            subcategories_count=models.Count('subcategories')
        )
    
    actions = ['activate_selected', 'deactivate_selected']
    
    @admin.action(description=_('Activer les catégories sélectionnées'))
    def activate_selected(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} catégories activées.', messages.SUCCESS)
    
    @admin.action(description=_('Désactiver les catégories sélectionnées'))
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} catégories désactivées.', messages.WARNING)

@admin.register(SubCategoryNaceCode)
class SubCategoryNaceCodeAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: SubCategoryNaceCodeAdmin."""
    list_display = [
        'code', 'libelle', 'category', 'active', 'poids', 
        'deleted', 'created_at'
    ]
    list_display_links = ['code', 'libelle']
    list_filter = [
        'active', 'category',
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['code', 'libelle', 'category__code', 'category__libelle']
    list_select_related = ['category']
    list_editable = ['active', 'poids']
    raw_id_fields = ['category']
    ordering = ['code']
    autocomplete_fields = ['category']
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('category', 'code', 'libelle')
        }),
        (_('Paramètres'), {
            'fields': ('active', 'poids')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')

@admin.register(CategoryNafCode)
class CategoryNafCodeAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: CategoryNafCodeAdmin."""
    list_display = [
        'code', 'libelle', 'active', 'poids', 
        'subcategories_count', 'deleted', 'created_at'
    ]
    list_display_links = ['code', 'libelle']
    list_filter = [
        'active',
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['code', 'libelle']
    list_editable = ['active', 'poids']
    ordering = ['code']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle')
        }),
        (_('Paramètres'), {
            'fields': ('active', 'poids')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def subcategories_count(self, obj):
        return obj.subcategories.count()
    subcategories_count.short_description = _('Nb sous-catégories')
    subcategories_count.admin_order_field = 'subcategories_count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            subcategories_count=models.Count('subcategories')
        )
    
    actions = ['activate_selected', 'deactivate_selected']
    
    @admin.action(description=_('Activer les catégories sélectionnées'))
    def activate_selected(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} catégories activées.', messages.SUCCESS)
    
    @admin.action(description=_('Désactiver les catégories sélectionnées'))
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} catégories désactivées.', messages.WARNING)

@admin.register(SubCategoryNafCode)
class SubCategoryNafCodeAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: SubCategoryNafCodeAdmin."""
    list_display = [
        'code', 'libelle', 'category', 'active', 'poids', 
        'deleted', 'created_at'
    ]
    list_display_links = ['code', 'libelle']
    list_filter = [
        'active', 'category',
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['code', 'libelle', 'category__code', 'category__libelle']
    list_select_related = ['category']
    list_editable = ['active', 'poids']
    raw_id_fields = ['category']
    ordering = ['code']
    autocomplete_fields = ['category']
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('category', 'code', 'libelle')
        }),
        (_('Paramètres'), {
            'fields': ('active', 'poids')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')

@admin.register(FormeJuridique)
class FormeJuridiqueAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: FormeJuridiqueAdmin."""
    list_display = [
        'code', 'libelle', 'active', 'poids', 
        'description_preview', 'deleted', 'created_at'
    ]
    list_display_links = ['code', 'libelle']
    list_filter = [
        'active',
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['code', 'libelle', 'description']
    list_editable = ['active', 'poids']
    ordering = ['code']
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle', 'description')
        }),
        (_('Paramètres'), {
            'fields': ('active', 'poids')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def description_preview(self, obj):
        if obj.description:
            # Tronquer la description pour l'affichage en liste
            preview = obj.description[:50]
            if len(obj.description) > 50:
                preview += "..."
            return preview
        return "-"
    description_preview.short_description = _('Description')
    
    # Personnalisation du widget pour le champ description
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'description':
            kwargs['widget'] = admin.widgets.AdminTextareaWidget(attrs={
                'rows': 4,
                'cols': 80,
            })
        return super().formfield_for_dbfield(db_field, request, **kwargs)

@admin.register(DomaineEntreprise)
class DomaineEntrepriseAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: DomaineEntrepriseAdmin."""
    list_display = [
        'code', 'libelle', 'active', 
        'description_preview', 'deleted', 'created_at'
    ]
    list_display_links = ['code', 'libelle']
    list_filter = [
        'active',
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['code', 'libelle', 'description']
    list_editable = ['active']
    ordering = ['libelle']
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle', 'description')
        }),
        (_('Statut'), {
            'fields': ('active',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def description_preview(self, obj):
        if obj.description:
            # Tronquer la description pour l'affichage en liste
            preview = obj.description[:50]
            if len(obj.description) > 50:
                preview += "..."
            return preview
        return "-"
    description_preview.short_description = _('Description')
    
    # Personnalisation du widget pour le champ description
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'description':
            kwargs['widget'] = admin.widgets.AdminTextareaWidget(attrs={
                'rows': 4,
                'cols': 80,
            })
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
    
@admin.register(PosteEntreprise)
class PosteEntrepriseAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: PosteEntrepriseAdmin."""
    list_display = [
        'code', 'libelle', 'domaine', 'active',
        'description_preview', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_display_links = ['code', 'libelle']
    list_filter = [
        'active', 'domaine',
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = ['code', 'libelle', 'description', 'domaine__libelle']
    list_select_related = ['domaine']
    list_editable = ['active']
    raw_id_fields = ['domaine']
    ordering = ['libelle']
    autocomplete_fields = ['domaine']
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('domaine', 'code', 'libelle', 'description')
        }),
        (_('Statut'), {
            'fields': ('active',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def description_preview(self, obj):
        if obj.description:
            preview = obj.description[:50]
            if len(obj.description) > 50:
                preview += "..."
            return preview
        return "-"
    description_preview.short_description = _('Description')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('domaine')
    
    actions = ['activate_postes', 'deactivate_postes']
    
    @admin.action(description=_('Activer les postes sélectionnés'))
    def activate_postes(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} postes activés.', messages.SUCCESS)
    
    @admin.action(description=_('Désactiver les postes sélectionnés'))
    def deactivate_postes(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} postes désactivés.', messages.WARNING)
    
    # Personnalisation du widget pour le champ description
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'description':
            kwargs['widget'] = admin.widgets.AdminTextareaWidget(attrs={
                'rows': 4,
                'cols': 80,
            })
        return super().formfield_for_dbfield(db_field, request, **kwargs)

@admin.register(CategorieEntreprise)
class CategorieEntrepriseAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: CategorieEntrepriseAdmin."""
    list_display = [
        'code', 'libelle', 'active',
        'description_preview', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_display_links = ['code', 'libelle']
    list_filter = [
        'active',
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = ['code', 'libelle', 'description']
    list_editable = ['active']
    ordering = ['libelle']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle', 'description')
        }),
        (_('Statut'), {
            'fields': ('active',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def description_preview(self, obj):
        if obj.description:
            preview = obj.description[:50]
            if len(obj.description) > 50:
                preview += "..."
            return preview
        return "-"
    description_preview.short_description = _('Description')
    
    actions = ['activate_categories', 'deactivate_categories']
    
    @admin.action(description=_('Activer les catégories sélectionnées'))
    def activate_categories(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} catégories activées.', messages.SUCCESS)
    
    @admin.action(description=_('Désactiver les catégories sélectionnées'))
    def deactivate_categories(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} catégories désactivées.', messages.WARNING)
    
    # Personnalisation du widget pour le champ description
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'description':
            kwargs['widget'] = admin.widgets.AdminTextareaWidget(attrs={
                'rows': 4,
                'cols': 80,
            })
        return super().formfield_for_dbfield(db_field, request, **kwargs)

@admin.register(StructureEntreprise)
class StructureEntrepriseAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: StructureEntrepriseAdmin."""
    list_display = [
        'code', 'libelle', 'active',
        'description_preview', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_display_links = ['code', 'libelle']
    list_filter = [
        'active',
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = ['code', 'libelle', 'description']
    list_editable = ['active']
    ordering = ['libelle']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle', 'description')
        }),
        (_('Statut'), {
            'fields': ('active',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def description_preview(self, obj):
        if obj.description:
            preview = obj.description[:50]
            if len(obj.description) > 50:
                preview += "..."
            return preview
        return "-"
    description_preview.short_description = _('Description')
    
    actions = ['activate_structures', 'deactivate_structures']
    
    @admin.action(description=_('Activer les structures sélectionnées'))
    def activate_structures(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} structures activées.', messages.SUCCESS)
    
    @admin.action(description=_('Désactiver les structures sélectionnées'))
    def deactivate_structures(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} structures désactivées.', messages.WARNING)
    
    # Personnalisation du widget pour le champ description
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'description':
            kwargs['widget'] = admin.widgets.AdminTextareaWidget(attrs={
                'rows': 4,
                'cols': 80,
            })
        return super().formfield_for_dbfield(db_field, request, **kwargs)

@admin.register(StatutEntreprise)
class StatutEntrepriseAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: StatutEntrepriseAdmin."""
    list_display = [
        'code', 'libelle', 'active',
        'description_preview', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_display_links = ['code', 'libelle']
    list_filter = [
        'active',
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = ['code', 'libelle', 'description']
    list_editable = ['active']
    ordering = ['libelle']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle', 'description')
        }),
        (_('Statut'), {
            'fields': ('active',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def description_preview(self, obj):
        if obj.description:
            preview = obj.description[:50]
            if len(obj.description) > 50:
                preview += "..."
            return preview
        return "-"
    description_preview.short_description = _('Description')
    
    actions = ['activate_statuts', 'deactivate_statuts']
    
    @admin.action(description=_('Activer les statuts sélectionnés'))
    def activate_statuts(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} statuts activés.', messages.SUCCESS)
    
    @admin.action(description=_('Désactiver les statuts sélectionnés'))
    def deactivate_statuts(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} statuts désactivés.', messages.WARNING)
    
    # Personnalisation du widget pour le champ description
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'description':
            kwargs['widget'] = admin.widgets.AdminTextareaWidget(attrs={
                'rows': 4,
                'cols': 80,
            })
        return super().formfield_for_dbfield(db_field, request, **kwargs)




# Classe de base commune pour tous les modèles
class ModeleBaseAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Classe de base pour tous les modèles de modèles"""
    
    list_display = [
        'code', 'libelle', 'get_poids_display', 
        'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_display_links = ['code', 'libelle']
    list_filter = [
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = ['code', 'libelle']
    ordering = ['code']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def is_empty_display(self, obj):
        if obj.is_empty():
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠ {}</span>',
                _('Incomplet')
            )
        return format_html(
            '<span style="color: green;">✓ {}</span>',
            _('Complet')
        )
    is_empty_display.short_description = _('Statut')
    is_empty_display.admin_order_field = 'code'
    
    def get_poids_display(self, obj):
        if hasattr(obj, 'poids'):
            if obj.poids > 0:
                return format_html(
                    '<span style="color: blue; font-weight: bold;">{}</span>',
                    obj.poids
                )
            return format_html(
                '<span style="color: gray;">{}</span>',
                obj.poids
            )
        return "-"
    get_poids_display.short_description = _('Poids')
    get_poids_display.admin_order_field = 'poids'
    
    actions = ['mark_as_complete', 'mark_as_incomplete', 'export_modeles']
    
    @admin.action(description=_('Marquer comme complet'))
    def mark_as_complete(self, request, queryset):
        count = 0
        for modele in queryset:
            if modele.is_empty():
                modele.code = modele.code or f"CODE_{modele.id}"
                modele.libelle = modele.libelle or f"Libellé {modele.id}"
                modele.save()
                count += 1
        if count > 0:
            self.message_user(
                request, 
                f'{count} modèles marqués comme complets.', 
                messages.SUCCESS
            )
        else:
            self.message_user(
                request, 
                'Tous les modèles sélectionnés sont déjà complets.', 
                messages.INFO
            )
    
    @admin.action(description=_('Marquer comme incomplet'))
    def mark_as_incomplete(self, request, queryset):
        updated = queryset.update(code=None, libelle=None)
        self.message_user(
            request, 
            f'{updated} modèles marqués comme incomplets.', 
            messages.WARNING
        )
    
    @admin.action(description=_('Exporter les modèles sélectionnés'))
    def export_modeles(self, request, queryset):
        count = queryset.count()
        model_name = self.model._meta.verbose_name_plural
        self.message_user(
            request,
            f'Prêt à exporter {count} {model_name}.',
            messages.INFO
        )

# Classes spécifiques avec personnalisations

@admin.register(ModeleRapport)
class ModeleRapportAdmin(ModeleBaseAdmin):
    """Configuration admin: ModeleRapportAdmin."""
    list_display = [
        'code', 'libelle', 'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle'),
            'description': _('Modèle de rapport pour les entreprises')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    class Meta:
        verbose_name = _("Modèle de rapport")
        verbose_name_plural = _("Modèles de rapport")

@admin.register(ModeleAlarme)
class ModeleAlarmeAdmin(ModeleBaseAdmin):
    """Configuration admin: ModeleAlarmeAdmin."""
    list_display = [
        'code', 'libelle', 'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle'),
            'description': _('Modèle d\'alarme pour le monitoring')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    class Meta:
        verbose_name = _("Modèle d'alarme")
        verbose_name_plural = _("Modèles d'alarme")

@admin.register(ModeleBilan)
class ModeleBilanAdmin(ModeleBaseAdmin):
    """Configuration admin: ModeleBilanAdmin."""
    list_display = [
        'code', 'libelle', 'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle'),
            'description': _('Modèle de bilan financier')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    class Meta:
        verbose_name = _("Modèle de bilan")
        verbose_name_plural = _("Modèles de bilan")

@admin.register(ModeleBail)
class ModeleBailAdmin(ModeleBaseAdmin):
    """Configuration admin: ModeleBailAdmin."""
    list_display = [
        'code', 'libelle', 'get_poids_display', 
        'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle', 'poids'),
            'description': _('Modèle de bail avec poids pour calculs')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Personnalisation du champ poids
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'poids':
            kwargs['widget'] = admin.widgets.AdminTextInputWidget(attrs={
                'style': 'width: 100px;',
                'step': '0.1',
                'min': '0',
                'max': '100'
            })
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
    actions = ModeleBaseAdmin.actions + ['adjust_weights']
    
    @admin.action(description=_('Ajuster les poids (normaliser)'))
    def adjust_weights(self, request, queryset):
        total_weight = sum(m.poids for m in queryset if m.poids > 0)
        if total_weight > 0:
            for modele in queryset:
                if modele.poids > 0:
                    modele.poids = (modele.poids / total_weight) * 100
                    modele.save(update_fields=['poids'])
            self.message_user(
                request,
                f'Poids normalisés pour {queryset.count()} modèles.',
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                'Aucun poids positif à normaliser.',
                messages.WARNING
            )
    
    class Meta:
        verbose_name = _("Modèle de bail")
        verbose_name_plural = _("Modèles de bail")

@admin.register(ModeleNotation)
class ModeleNotationAdmin(ModeleBaseAdmin):
    """Configuration admin: ModeleNotationAdmin."""
    list_display = [
        'code', 'libelle', 'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle'),
            'description': _('Modèle de notation pour l\'évaluation')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    class Meta:
        verbose_name = _("Modèle de notation")
        verbose_name_plural = _("Modèles de notation")

@admin.register(ModeleAvisCommercial)
class ModeleAvisCommercialAdmin(ModeleBaseAdmin):
    """Configuration admin: ModeleAvisCommercialAdmin."""
    list_display = [
        'code', 'libelle', 'get_poids_display', 
        'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle', 'poids'),
            'description': _('Modèle d\'avis commercial avec pondération')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Personnalisation du champ poids
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'poids':
            kwargs['widget'] = admin.widgets.AdminTextInputWidget(attrs={
                'style': 'width: 100px;',
                'step': '0.1',
                'min': '0',
                'max': '100'
            })
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
    actions = ModeleBaseAdmin.actions + ['reset_weights']
    
    @admin.action(description=_('Réinitialiser les poids à 0'))
    def reset_weights(self, request, queryset):
        updated = queryset.update(poids=0.0)
        self.message_user(
            request,
            f'{updated} poids réinitialisés à 0.',
            messages.INFO
        )
    
    class Meta:
        verbose_name = _("Modèle d'avis commercial")
        verbose_name_plural = _("Modèles d'avis commercial")
        
        
        
        

# Réutilisation de la classe de base existante
class ModeleBaseAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Classe de base pour tous les modèles de modèles"""
    
    list_display = [
        'code', 'libelle', 'get_poids_display', 
        'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_display_links = ['code', 'libelle']
    list_filter = [
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = ['code', 'libelle']
    ordering = ['code']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def is_empty_display(self, obj):
        if obj.is_empty():
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠ {}</span>',
                _('Incomplet')
            )
        return format_html(
            '<span style="color: green;">✓ {}</span>',
            _('Complet')
        )
    is_empty_display.short_description = _('Statut')
    is_empty_display.admin_order_field = 'code'
    
    def get_poids_display(self, obj):
        if hasattr(obj, 'poids'):
            if obj.poids > 0:
                return format_html(
                    '<span style="color: blue; font-weight: bold;">{}</span>',
                    obj.poids
                )
            return format_html(
                '<span style="color: gray;">{}</span>',
                obj.poids
            )
        return "-"
    get_poids_display.short_description = _('Poids')
    get_poids_display.admin_order_field = 'poids'
    
    actions = ['mark_as_complete', 'mark_as_incomplete', 'export_modeles']
    
    @admin.action(description=_('Marquer comme complet'))
    def mark_as_complete(self, request, queryset):
        count = 0
        for modele in queryset:
            if modele.is_empty():
                modele.code = modele.code or f"CODE_{modele.id}"
                modele.libelle = modele.libelle or f"Libellé {modele.id}"
                modele.save()
                count += 1
        if count > 0:
            self.message_user(
                request, 
                f'{count} modèles marqués comme complets.', 
                messages.SUCCESS
            )
        else:
            self.message_user(
                request, 
                'Tous les modèles sélectionnés sont déjà complets.', 
                messages.INFO
            )
    
    @admin.action(description=_('Marquer comme incomplet'))
    def mark_as_incomplete(self, request, queryset):
        updated = queryset.update(code=None, libelle=None)
        self.message_user(
            request, 
            f'{updated} modèles marqués comme incomplets.', 
            messages.WARNING
        )
    
    @admin.action(description=_('Exporter les modèles sélectionnés'))
    def export_modeles(self, request, queryset):
        count = queryset.count()
        model_name = self.model._meta.verbose_name_plural
        self.message_user(
            request,
            f'Prêt à exporter {count} {model_name}.',
            messages.INFO
        )

# Classe spéciale pour les modèles avec poids
class ModeleAvecPoidsAdmin(ModeleBaseAdmin):
    """Classe pour les modèles avec champ poids"""
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle', 'poids'),
            'description': _('Modèle avec pondération pour les calculs')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Personnalisation du champ poids
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'poids':
            kwargs['widget'] = admin.widgets.AdminTextInputWidget(attrs={
                'style': 'width: 100px;',
                'step': '0.1',
                'min': '0',
                'max': '100',
                'placeholder': '0.0'
            })
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
    actions = ModeleBaseAdmin.actions + ['adjust_weights', 'reset_weights']
    
    @admin.action(description=_('Ajuster les poids (normaliser)'))
    def adjust_weights(self, request, queryset):
        total_weight = sum(m.poids for m in queryset if m.poids > 0)
        if total_weight > 0:
            for modele in queryset:
                if modele.poids > 0:
                    modele.poids = (modele.poids / total_weight) * 100
                    modele.save(update_fields=['poids'])
            self.message_user(
                request,
                f'Poids normalisés pour {queryset.count()} modèles.',
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                'Aucun poids positif à normaliser.',
                messages.WARNING
            )
    
    @admin.action(description=_('Réinitialiser les poids à 0'))
    def reset_weights(self, request, queryset):
        updated = queryset.update(poids=0.0)
        self.message_user(
            request,
            f'{updated} poids réinitialisés à 0.',
            messages.INFO
        )

# Classes spécifiques pour chaque modèle

@admin.register(ModeleRelationEntreprise)
class ModeleRelationEntrepriseAdmin(ModeleBaseAdmin):
    """Configuration admin: ModeleRelationEntrepriseAdmin."""
    list_display = [
        'code', 'libelle', 'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle'),
            'description': _('Modèle pour les relations entre entreprises (filiales, partenaires, etc.)')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    class Meta:
        verbose_name = _("Modèle de relation entreprise")
        verbose_name_plural = _("Modèles de relation entreprise")

@admin.register(ModeleInformationNotationEntreprise)
class ModeleInformationNotationEntrepriseAdmin(ModeleBaseAdmin):
    """Configuration admin: ModeleInformationNotationEntrepriseAdmin."""
    list_display = [
        'code', 'libelle', 'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle'),
            'description': _('Modèle pour les informations sur la notation des entreprises')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    class Meta:
        verbose_name = _("Modèle d'information sur notation entreprise")
        verbose_name_plural = _("Modèles d'information sur notation entreprise")

@admin.register(ModeleComportementPaiement)
class ModeleComportementPaiementAdmin(ModeleAvecPoidsAdmin):
    """Configuration admin: ModeleComportementPaiementAdmin."""
    list_display = [
        'code', 'libelle', 'get_poids_display', 
        'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle', 'poids'),
            'description': _('Modèle pour évaluer le comportement de paiement (paiements à temps, retards, etc.)')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ModeleAvecPoidsAdmin.actions + ['set_payment_weights']
    
    @admin.action(description=_('Définir poids standards paiement'))
    def set_payment_weights(self, request, queryset):
        weights_mapping = {
            'EXCELLENT': 10.0,
            'BON': 7.5,
            'MOYEN': 5.0,
            'MAUVAIS': 2.5,
            'TRES_MAUVAIS': 0.0
        }
        
        updated = 0
        for modele in queryset:
            libelle_upper = modele.libelle.upper() if modele.libelle else ""
            for key, weight in weights_mapping.items():
                if key in libelle_upper:
                    modele.poids = weight
                    modele.save(update_fields=['poids'])
                    updated += 1
                    break
        
        self.message_user(
            request,
            f'{updated} poids définis selon le comportement de paiement.',
            messages.SUCCESS
        )
    
    class Meta:
        verbose_name = _("Modèle de comportement de paiement")
        verbose_name_plural = _("Modèles de comportement de paiement")

@admin.register(ModeleComportementJugement)
class ModeleComportementJugementAdmin(ModeleBaseAdmin):
    """Configuration admin: ModeleComportementJugementAdmin."""
    list_display = [
        'code', 'libelle', 'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle'),
            'description': _('Modèle pour les comportements liés aux jugements (litiges, contentieux, etc.)')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ModeleBaseAdmin.actions + ['categorize_judgments']
    
    @admin.action(description=_('Catégoriser les jugements'))
    def categorize_judgments(self, request, queryset):
        categories = {
            'AUCUN': 'Aucun jugement',
            'FAIBLE': 'Jugements mineurs',
            'MOYEN': 'Jugements significatifs',
            'GRAVE': 'Jugements graves',
            'TRES_GRAVE': 'Jugements très graves'
        }
        
        updated = 0
        for modele in queryset:
            if modele.libelle:
                libelle_upper = modele.libelle.upper()
                for cat_code, cat_libelle in categories.items():
                    if cat_code in libelle_upper or cat_libelle.upper() in libelle_upper:
                        modele.code = cat_code
                        modele.save(update_fields=['code'])
                        updated += 1
                        break
        
        self.message_user(
            request,
            f'{updated} modèles catégorisés.',
            messages.SUCCESS
        )
    
    class Meta:
        verbose_name = _("Modèle de comportement de jugement")
        verbose_name_plural = _("Modèles de comportement de jugement")

@admin.register(ModeleAgeSociete)
class ModeleAgeSocieteAdmin(ModeleAvecPoidsAdmin):
    """Configuration admin: ModeleAgeSocieteAdmin."""
    list_display = [
        'code', 'libelle', 'get_poids_display', 
        'age_range_display', 'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle', 'poids'),
            'description': _('Modèle pour l\'âge de la société (ancienneté) avec pondération')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def age_range_display(self, obj):
        if obj.libelle:
            # Essayer d'extraire des informations d'âge du libellé
            libelle_lower = obj.libelle.lower()
            if 'moins' in libelle_lower or '<' in libelle_lower or '0-1' in libelle_lower:
                return format_html('<span style="color: #ff6b6b;">🔴 Jeune</span>')
            elif '1-3' in libelle_lower or '2-5' in libelle_lower:
                return format_html('<span style="color: #ffa726;">🟠 Moyen</span>')
            elif '5-10' in libelle_lower or 'plus' in libelle_lower or '>' in libelle_lower:
                return format_html('<span style="color: #66bb6a;">🟢 Ancien</span>')
        return "-"
    age_range_display.short_description = _('Tranche d\'âge')
    
    actions = ModeleAvecPoidsAdmin.actions + ['set_age_weights']
    
    @admin.action(description=_('Définir poids par ancienneté'))
    def set_age_weights(self, request, queryset):
        age_weights = {
            'JEUNE': (0, 2, 3.0),  # moins de 2 ans
            'MOYEN': (2, 5, 6.0),  # 2-5 ans
            'ANCIEN': (5, 10, 8.0), # 5-10 ans
            'TRES_ANCIEN': (10, 999, 10.0) # plus de 10 ans
        }
        
        updated = 0
        for modele in queryset:
            if modele.libelle:
                libelle_upper = modele.libelle.upper()
                for age_code, (min_age, max_age, weight) in age_weights.items():
                    if age_code in libelle_upper:
                        modele.poids = weight
                        modele.save(update_fields=['poids'])
                        updated += 1
                        break
        
        self.message_user(
            request,
            f'{updated} poids définis selon l\'ancienneté.',
            messages.SUCCESS
        )
    
    class Meta:
        verbose_name = _("Modèle d'age de société")
        verbose_name_plural = _("Modèles d'age de société")

@admin.register(ModeleInterpretationScoringSansBilan)
class ModeleInterpretationScoringSansBilanAdmin(ModeleAvecPoidsAdmin):
    """Configuration admin: ModeleInterpretationScoringSansBilanAdmin."""
    list_display = [
        'code', 'libelle', 'get_poids_display', 
        'scoring_range_display', 'is_empty_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'libelle', 'poids'),
            'description': _('Modèle pour l\'interprétation du scoring sans bilan financier')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def scoring_range_display(self, obj):
        if obj.libelle:
            # Essayer d'identifier la plage de scoring
            libelle_lower = obj.libelle.lower()
            if 'faible' in libelle_lower or 'risque' in libelle_lower or '0-' in libelle_lower:
                return format_html('<span style="color: #ff6b6b;">🔴 Risque élevé</span>')
            elif 'moyen' in libelle_lower or 'modéré' in libelle_lower:
                return format_html('<span style="color: #ffa726;">🟠 Risque modéré</span>')
            elif 'bon' in libelle_lower or 'fiable' in libelle_lower or '100' in libelle_lower:
                return format_html('<span style="color: #66bb6a;">🟢 Faible risque</span>')
        return "-"
    scoring_range_display.short_description = _('Niveau risque')
    
    actions = ModeleAvecPoidsAdmin.actions + ['set_scoring_weights']
    
    @admin.action(description=_('Définir poids par niveau de risque'))
    def set_scoring_weights(self, request, queryset):
        scoring_weights = {
            'TRES_FAIBLE': 1.0,
            'FAIBLE': 3.0,
            'MOYEN': 5.0,
            'ELEVE': 7.0,
            'TRES_ELEVE': 9.0
        }
        
        updated = 0
        for modele in queryset:
            if modele.libelle:
                libelle_upper = modele.libelle.upper()
                for risk_level, weight in scoring_weights.items():
                    if risk_level in libelle_upper:
                        modele.poids = weight
                        modele.save(update_fields=['poids'])
                        updated += 1
                        break
        
        self.message_user(
            request,
            f'{updated} poids définis selon le niveau de risque.',
            messages.SUCCESS
        )
    
    class Meta:
        verbose_name = _("Modèle interpretation scoring sans bilan")
        verbose_name_plural = _("Modèles interpretations scoring sans bilan")
        
        
        




@admin.register(Client)
class ClientAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: ClientAdmin."""
    list_display = [
        'nom', 'email', 'telephone', 'actif',
        'portefeuilles_count', 'date_inscription'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_display_links = ['nom', 'email']
    list_filter = [
        'actif',
        ('date_inscription', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = ['nom', 'email', 'telephone', 'adresse']
    list_editable = ['actif']
    ordering = ['nom']
    date_hierarchy = 'date_inscription'
    
    fieldsets = (
        (_('Informations principales'), {
            'fields': ('nom', 'email', 'telephone')
        }),
        (_('Adresse'), {
            'fields': ('adresse',),
            'classes': ('collapse',)
        }),
        (_('Statut'), {
            'fields': ('actif',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['date_inscription']
    
    def portefeuilles_count(self, obj):
        return obj.portefeuilles_client.count()
    portefeuilles_count.short_description = _('Nb portefeuilles')
    portefeuilles_count.admin_order_field = 'portefeuilles_count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            portefeuilles_count=models.Count('portefeuilles_client')
        )
    
    actions = ['activate_clients', 'deactivate_clients', 'send_welcome_email']
    
    @admin.action(description=_('Activer les clients'))
    def activate_clients(self, request, queryset):
        updated = queryset.update(actif=True)
        self.message_user(request, f'{updated} clients activés.', messages.SUCCESS)
    
    @admin.action(description=_('Désactiver les clients'))
    def deactivate_clients(self, request, queryset):
        updated = queryset.update(actif=False)
        self.message_user(request, f'{updated} clients désactivés.', messages.WARNING)
    
    @admin.action(description=_('Envoyer email de bienvenue (simulé)'))
    def send_welcome_email(self, request, queryset):
        count = queryset.count()
        self.message_user(
            request,
            f'Email de bienvenue prêt à envoyer à {count} client(s).',
            messages.INFO
        )

@admin.register(Contact)
class ContactAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: ContactAdmin."""
    list_display = [
        'nom', 'email', 'telephone', 'client', 'actif'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_display_links = ['nom', 'email']
    list_filter = [
        'actif', 'client',
        ('created_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = ['nom', 'email', 'telephone', 'client__nom']
    list_select_related = ['client']
    list_editable = ['actif']
    raw_id_fields = ['client']
    ordering = ['nom']
    autocomplete_fields = ['client']
    
    fieldsets = (
        (_('Informations du contact'), {
            'fields': ('nom', 'email', 'telephone')
        }),
        (_('Association'), {
            'fields': ('client',),
            'classes': ('collapse',)
        }),
        (_('Statut'), {
            'fields': ('actif',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client')
    
    actions = ['activate_contacts', 'deactivate_contacts', 'export_contacts']
    
    @admin.action(description=_('Activer les contacts'))
    def activate_contacts(self, request, queryset):
        updated = queryset.update(actif=True)
        self.message_user(request, f'{updated} contacts activés.', messages.SUCCESS)
    
    @admin.action(description=_('Désactiver les contacts'))
    def deactivate_contacts(self, request, queryset):
        updated = queryset.update(actif=False)
        self.message_user(request, f'{updated} contacts désactivés.', messages.WARNING)



class NotificationLogInline(admin.TabularInline):
    """Configuration admin: NotificationLogInline."""
    model = NotificationLog
    extra = 0
    readonly_fields = ['portefeuille', 'code_evenement', 'date_notification', 'description', 'actif']
    can_delete = False
    max_num = 5
    verbose_name = _('Notification récente')
    verbose_name_plural = _('Notifications récentes')
    classes = ['collapse']

class AlerteLogInline(admin.TabularInline):
    """Configuration admin: AlerteLogInline."""
    model = AlerteLog
    extra = 0
    readonly_fields = ['acheteur', 'element_surveille', 'date_creation', 'message', 'lu']
    can_delete = False
    max_num = 5
    verbose_name = _('Alerte récente')
    verbose_name_plural = _('Alertes récentes')
    classes = ['collapse']



@admin.register(NotificationLog)
class NotificationLogAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: NotificationLogAdmin."""
    list_display = [
        'portefeuille', 'code_evenement', 'date_notification',
        'actif_display', 'description_preview'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_display_links = ['portefeuille', 'code_evenement']
    list_filter = [
        'actif', 'portefeuille',
        ('date_notification', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = [
        'portefeuille__nom', 'code_evenement', 'description',
        'portefeuille__client__nom'
    ]
    list_select_related = ['portefeuille']
    readonly_fields = ['date_notification']
    ordering = ['-date_notification']
    date_hierarchy = 'date_notification'
    
    fieldsets = (
        (_('Notification'), {
            'fields': ('portefeuille', 'code_evenement', 'description')
        }),
        (_('Statut'), {
            'fields': ('actif',),
            'classes': ('collapse',)
        }),
        (_('Date'), {
            'fields': ('date_notification',),
            'classes': ('collapse',)
        }),
    )
    
    def description_preview(self, obj):
        if obj.description:
            preview = obj.description[:60]
            if len(obj.description) > 60:
                preview += "..."
            return preview
        return "-"
    description_preview.short_description = _('Description')
    
    def actif_display(self, obj):
        if obj.actif:
            return format_html('<span style="color: green;">✓ Envoyée</span>')
        return format_html('<span style="color: orange;">⏳ En attente</span>')
    actif_display.short_description = _('Statut')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('portefeuille__client')
    
    actions = ['mark_as_sent', 'mark_as_pending', 'resend_notifications']
    
    @admin.action(description=_('Marquer comme envoyées'))
    def mark_as_sent(self, request, queryset):
        updated = queryset.update(actif=True)
        self.message_user(
            request,
            f'{updated} notifications marquées comme envoyées.',
            messages.SUCCESS
        )
    
    @admin.action(description=_('Marquer comme en attente'))
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(actif=False)
        self.message_user(
            request,
            f'{updated} notifications marquées comme en attente.',
            messages.WARNING
        )

      
        
        


@admin.register(UpdatedObjects)
class UpdatedObjectsAdmin(admin.ModelAdmin):
    """Admin pour le suivi des objets mis à jour"""
    list_display = [
        'acheteur', 'updated_model', 'updated_at', 'get_time_ago'
    ]
    list_display_links = ['acheteur']
    list_filter = [
        'updated_model',
        ('updated_at', admin.DateFieldListFilter),
    ]
    search_fields = [
        'acheteur__nom', 'updated_model',
        'acheteur__code', 'acheteur__email'
    ]
    list_select_related = ['acheteur']
    readonly_fields = ['updated_at']
    ordering = ['-updated_at']
    date_hierarchy = 'updated_at'
    
    fieldsets = (
        (_('Suivi des mises à jour'), {
            'fields': ('acheteur', 'updated_model')
        }),
        (_('Date'), {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_time_ago(self, obj):
        if obj.updated_at:
            delta = timezone.now() - obj.updated_at
            if delta.days > 0:
                return f"{delta.days} jour(s)"
            elif delta.seconds // 3600 > 0:
                return f"{delta.seconds // 3600} heure(s)"
            elif delta.seconds // 60 > 0:
                return f"{delta.seconds // 60} minute(s)"
            return "À l'instant"
        return "-"
    get_time_ago.short_description = _('Il y a')
    get_time_ago.admin_order_field = 'updated_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('acheteur')
    
    actions = ['clean_old_entries', 'export_update_logs']
    
    @admin.action(description=_('Nettoyer les entrées anciennes (>30 jours)'))
    def clean_old_entries(self, request, queryset):
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count, _ = queryset.filter(updated_at__lt=cutoff_date).delete()
        self.message_user(
            request,
            f'{deleted_count} entrées anciennes supprimées.',
            messages.SUCCESS
        )

class AcheteurUploadInline(admin.TabularInline):
    """Configuration admin: AcheteurUploadInline."""
    model = AcheteurUpload
    extra = 1
    readonly_fields = ['uploaded_at', 'file_preview', 'file_size']
    fields = ['upload', 'uploaded_at', 'file_preview', 'file_size']
    verbose_name = _('Fichier associé')
    verbose_name_plural = _('Fichiers associés')
    classes = ['collapse']
    
    def file_preview(self, obj):
        if obj.upload:
            filename = os.path.basename(obj.upload.name)
            extension = os.path.splitext(filename)[1].lower()
            
            # Icônes selon le type de fichier
            icons = {
                '.pdf': '📄',
                '.doc': '📝', '.docx': '📝',
                '.xls': '📊', '.xlsx': '📊',
                '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
                '.txt': '📃',
                '.zip': '📦', '.rar': '📦',
            }
            
            icon = icons.get(extension, '📎')
            return format_html(
                '{} <a href="{}" target="_blank">{}</a>',
                icon, obj.upload.url, filename
            )
        return "-"
    file_preview.short_description = _('Fichier')
    
    def file_size(self, obj):
        if obj.upload and obj.upload.size:
            size = obj.upload.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f} KB"
            else:
                return f"{size/(1024*1024):.1f} MB"
        return "-"
    file_size.short_description = _('Taille')

class RapportTelechargerInline(admin.TabularInline):
    """Configuration admin: RapportTelechargerInline."""
    model = RapportTelecharger
    extra = 0
    max_num = 5
    readonly_fields = [
        'downloaded_by', 'download_at', 'type_rapport',
        'ref_commande_client', 'ref_commande_acremac'
    ]
    fields = [
        'type_rapport', 'downloaded_by', 'download_at',
        'ref_commande_client', 'ref_commande_acremac'
    ]
    verbose_name = _('Rapport téléchargé')
    verbose_name_plural = _('Rapports téléchargés récents')
    classes = ['collapse']

@admin.register(Acheteur)
class AcheteurAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: AcheteurAdmin."""
    list_display = [
        'code', 'nom', 'sigle', 'forme_juridique',
        'statut_entreprise', 'pays', 'ville', 'created_at',
        'portefeuilles_count', 'alertes_recentes'
    ] + list(SafeDeleteAdmin.list_display)

    list_display_links = ['code', 'nom']
    list_filter = [
        'forme_juridique', 'statut_entreprise',
        'pays', 'ville',
        'created_by', 'updated_by',
        ('date_creation', admin.DateFieldListFilter),
        ('created_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)

    search_fields = [
        'code', 'nom', 'sigle', 'email', 'site_internet',
        'activite_principale', 'description',
        'pays__nom', 'ville__nom',
        'forme_juridique__libelle',
    ]

    list_select_related = [
        'forme_juridique', 'statut_entreprise',
        'pays', 'ville', 'couleur_commentaire',
        'created_by', 'updated_by'
    ]

    list_editable = ['sigle']
    raw_id_fields = [
        'forme_juridique', 'statut_entreprise',
        'pays', 'province', 'ville', 'couleur_commentaire',
        'created_by', 'updated_by'
    ]

    autocomplete_fields = [
        'forme_juridique', 'statut_entreprise',
        'pays', 'ville', 'couleur_commentaire'
    ]
    
    ordering = ['nom']
    date_hierarchy = 'created_at'
    filter_horizontal = []
    readonly_fields = ['created_at', 'updated_at', 'code']
    
    fieldsets = (
        (_('Identité et code'), {
            'fields': ('code', 'nom', 'sigle', 'description'),
            'classes': ('wide',)
        }),
        (_('Caractéristiques juridiques'), {
            'fields': ('forme_juridique', 'statut_entreprise', 'date_creation'),
            'classes': ('collapse',)
        }),
        (_('Activité'), {
            'fields': ('activite_principale',),
            'classes': ('collapse',)
        }),
        (_('Coordonnées'), {
            'fields': ('email', 'site_internet', 'fax', 'telephone'),
            'classes': ('collapse',)
        }),
        (_('Adresse'), {
            'fields': (
                'numero_adresse', 'rue_adresse', 'code_postal', 'boite_postale',
                'pays', 'ville'
            ),
            'classes': ('collapse',)
        }),
        (_('Commentaire et couleur'), {
            'fields': ('couleur_commentaire', 'commentaire'),
            'classes': ('collapse',)
        }),
        (_('Audit et suivi'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [
        AcheteurUploadInline,
        RapportTelechargerInline
    ]
    
    def portefeuilles_count(self, obj):
        count = obj.portefeuilleclient_set.count()
        if count > 0:
            url = reverse('admin:main_portefeuilleclient_changelist')
            url += f'?acheteur__id__exact={obj.id}'
            return format_html(
                '<a href="{}" style="color: blue;">{} portefeuille(s)</a>',
                url, count
            )
        return "0"
    portefeuilles_count.short_description = _('Dans portefeuilles')
    portefeuilles_count.admin_order_field = 'portefeuilleclient_count'
    
    def alertes_recentes(self, obj):
        from .models import AlerteLog
        count = AlerteLog.objects.filter(acheteur=obj, lu=False).count()
        if count > 0:
            url = reverse('admin:main_alertelog_changelist')
            url += f'?acheteur__id__exact={obj.id}&lu__exact=0'
            return format_html(
                '<a href="{}" style="color: red; font-weight: bold;">⚠ {} alerte(s)</a>',
                url, count
            )
        return format_html('<span style="color: green;">✓ Aucune</span>')
    alertes_recentes.short_description = _('Alertes non lues')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'forme_juridique', 'statut_entreprise',
            'pays', 'province', 'ville', 'couleur_commentaire',
            'created_by', 'updated_by'
        ).annotate(
            portefeuilleclient_count=models.Count('portefeuilleclient')
        )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvel objet
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        
        # Enregistrer dans UpdatedObjects
        UpdatedObjects.objects.update_or_create(
            acheteur=obj,
            defaults={'updated_model': 'Acheteur'}
        )
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, AcheteurUpload) and hasattr(instance, 'upload'):
                # S'assurer que le fichier est lié à l'acheteur
                instance.acheteur = form.instance
            instance.save()
        formset.save_m2m()
    
    actions = [
        'generate_missing_codes', 'update_statut_to_active',
        'update_statut_to_inactive', 'export_acheteurs_csv',
        'send_test_email'
    ]
    
    @admin.action(description=_('Générer les codes manquants'))
    def generate_missing_codes(self, request, queryset):
        updated = 0
        for acheteur in queryset.filter(code__isnull=True):
            if not acheteur.code:
                acheteur.code = acheteur.generate_unique_code()
                acheteur.save(update_fields=['code'])
                updated += 1
        self.message_user(
            request,
            f'{updated} codes générés.',
            messages.SUCCESS
        )
    
    @admin.action(description=_('Marquer comme actif'))
    def update_statut_to_active(self, request, queryset):
        from .models import StatutEntreprise
        try:
            statut_actif = StatutEntreprise.objects.filter(libelle__icontains='actif').first()
            if statut_actif:
                updated = queryset.update(statut_entreprise=statut_actif)
                self.message_user(
                    request,
                    f'{updated} acheteur(s) marqué(s) comme actif.',
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    'Statut "actif" non trouvé.',
                    messages.WARNING
                )
        except Exception as e:
            self.message_user(
                request,
                f'Erreur: {str(e)}',
                messages.ERROR
            )
    
    @admin.action(description=_('Marquer comme inactif'))
    def update_statut_to_inactive(self, request, queryset):
        from .models import StatutEntreprise
        try:
            statut_inactif = StatutEntreprise.objects.filter(libelle__icontains='inactif').first()
            if statut_inactif:
                updated = queryset.update(statut_entreprise=statut_inactif)
                self.message_user(
                    request,
                    f'{updated} acheteur(s) marqué(s) comme inactif.',
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    'Statut "inactif" non trouvé.',
                    messages.WARNING
                )
        except Exception as e:
            self.message_user(
                request,
                f'Erreur: {str(e)}',
                messages.ERROR
            )

@admin.register(AcheteurUpload)
class AcheteurUploadAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: AcheteurUploadAdmin."""
    list_display = [
        'acheteur', 'file_preview', 'file_size', 'uploaded_at', 'get_time_ago'
    ]
    list_display_links = ['acheteur', 'file_preview']
    list_filter = [
        ('uploaded_at', admin.DateFieldListFilter),
        'acheteur',
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = [
        'acheteur__nom', 'acheteur__code',
        'upload__name', 'filename'
    ]
    
    list_select_related = ['acheteur']
    readonly_fields = ['uploaded_at', 'file_size_display', 'file_preview_detail']
    ordering = ['-uploaded_at']
    date_hierarchy = 'uploaded_at'
    raw_id_fields = ['acheteur']
    autocomplete_fields = ['acheteur']
    
    fieldsets = (
        (_('Fichier'), {
            'fields': ('acheteur', 'upload')
        }),
        (_('Informations fichier'), {
            'fields': ('file_preview_detail', 'file_size_display', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_preview(self, obj):
        return obj.filename()
    file_preview.short_description = _('Fichier')
    file_preview.admin_order_field = 'upload'
    
    def file_preview_detail(self, obj):
        if obj.upload:
            return format_html(
                '<a href="{}" target="_blank" style="font-weight: bold;">📂 {}</a>',
                obj.upload.url, obj.filename()
            )
        return "-"
    file_preview_detail.short_description = _('Prévisualisation')
    
    def file_size_display(self, obj):
        if obj.upload and obj.upload.size:
            size = obj.upload.size
            if size < 1024:
                return f"{size} octets"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f} KB"
            else:
                return f"{size/(1024*1024):.1f} MB"
        return "-"
    file_size_display.short_description = _('Taille')
    
    def file_size(self, obj):
        if obj.upload and obj.upload.size:
            size_kb = obj.upload.size / 1024
            return f"{size_kb:.1f} KB"
        return "-"
    file_size.short_description = _('Taille')
    
    def get_time_ago(self, obj):
        if obj.uploaded_at:
            delta = timezone.now() - obj.uploaded_at
            if delta.days > 0:
                return f"{delta.days} jour(s)"
            elif delta.seconds // 3600 > 0:
                return f"{delta.seconds // 3600} heure(s)"
            elif delta.seconds // 60 > 0:
                return f"{delta.seconds // 60} minute(s)"
            return "À l'instant"
        return "-"
    get_time_ago.short_description = _('Il y a')
    get_time_ago.admin_order_field = 'uploaded_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('acheteur')
    
    actions = ['delete_files_and_records', 'export_file_list']
    
    @admin.action(description=_('Supprimer fichiers et enregistrements'))
    def delete_files_and_records(self, request, queryset):
        count = 0
        for upload in queryset:
            upload.delete()  # Appelle la méthode delete personnalisée
            count += 1
        self.message_user(
            request,
            f'{count} fichiers et enregistrements supprimés.',
            messages.SUCCESS
        )

@admin.register(RapportTelecharger)
class RapportTelechargerAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Configuration admin: RapportTelechargerAdmin."""
    list_display = [
        'acheteur', 'type_rapport', 'downloaded_by',
        'download_at', 'ref_commande_client', 'ref_commande_acremac'
    ]
    list_display_links = ['acheteur', 'type_rapport']
    list_filter = [
        'type_rapport',
        'downloaded_by',
        ('download_at', admin.DateFieldListFilter),
        ('created_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = [
        'acheteur__nom', 'acheteur__code',
        'type_rapport', 'ref_commande_client', 'ref_commande_acremac',
        'pays_acheteur', 'downloaded_by__username'
    ]
    
    list_select_related = ['acheteur', 'downloaded_by']
    readonly_fields = ['download_at', 'created_at', 'updated_at']
    ordering = ['-download_at']
    date_hierarchy = 'download_at'
    raw_id_fields = ['acheteur', 'downloaded_by']
    autocomplete_fields = ['acheteur', 'downloaded_by']
    
    fieldsets = (
        (_('Informations du rapport'), {
            'fields': ('acheteur', 'type_rapport')
        }),
        (_('Commandes et références'), {
            'fields': ('ref_commande_client', 'ref_commande_acremac'),
            'classes': ('collapse',)
        }),
        (_('Localisation'), {
            'fields': ('pays_acheteur',),
            'classes': ('collapse',)
        }),
        (_('Utilisateur'), {
            'fields': ('downloaded_by',),
            'classes': ('collapse',)
        }),
        (_('Dates'), {
            'fields': ('download_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'acheteur', 'downloaded_by'
        )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau téléchargement
            obj.downloaded_by = request.user
            obj.download_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    actions = ['export_download_logs', 'clean_old_records']
    
    @admin.action(description=_('Exporter les logs de téléchargement'))
    def export_download_logs(self, request, queryset):
        count = queryset.count()
        self.message_user(
            request,
            f'Prêt à exporter {count} logs de téléchargement.',
            messages.INFO
        )
    
    @admin.action(description=_('Nettoyer les anciens records (>90 jours)'))
    def clean_old_records(self, request, queryset):
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count, _ = queryset.filter(download_at__lt=cutoff_date).delete()
        self.message_user(
            request,
            f'{deleted_count} anciens records supprimés.',
            messages.SUCCESS
        )
        
        
@admin.register(Locaux)
class LocauxAdmin(admin.ModelAdmin):
    """Configuration admin: LocauxAdmin."""
    list_display = ("id", "nom")
    search_fields = ("nom",)
    ordering = ("nom",)


@admin.register(ListeConditionAchat)
class ListeConditionAchatAdmin(admin.ModelAdmin):
    """Configuration admin: ListeConditionAchatAdmin."""
    list_display = ("id", "nom_fr", "nom_en")
    search_fields = ("nom_fr", "nom_en", "nom")
    ordering = ("nom_fr",)


@admin.register(ListeConditionVente)
class ListeConditionVenteAdmin(admin.ModelAdmin):
    """Configuration admin: ListeConditionVenteAdmin."""
    list_display = ("id", "nom")
    search_fields = ("nom",)
    ordering = ("nom",)


@admin.register(ListeImportation)
class ListeImportationAdmin(admin.ModelAdmin):
    """Configuration admin: ListeImportationAdmin."""
    list_display = ("id", "libelle")
    search_fields = ("libelle",)



@admin.register(ListeComportementsPaiement)
class ListeComportementsPaiementAdmin(admin.ModelAdmin):
    """Configuration admin: ListeComportementsPaiementAdmin."""
    list_display = ("id", "libelle", "couleur")
    search_fields = ("libelle",)
    list_filter = ("couleur",)



@admin.register(ListeInformationsRating)
class ListeInformationsRatingAdmin(admin.ModelAdmin):
    """Configuration admin: ListeInformationsRatingAdmin."""
    list_display = ("id", "libelle", "couleur")
    search_fields = ("libelle",)
    list_filter = ("couleur",)



@admin.register(ListeInformationsAvisCommercial)
class ListeInformationsAvisCommercialAdmin(admin.ModelAdmin):
    """Configuration admin: ListeInformationsAvisCommercialAdmin."""
    list_display = ("id", "libelle", "couleur")
    search_fields = ("libelle",)
    list_filter = ("couleur",)





@admin.register(ScoringSansBilanAcheteur)
class ScoringSansBilanAcheteurAdmin(admin.ModelAdmin):
    """Configuration admin: ScoringSansBilanAcheteurAdmin."""
    # -------------------------
    # LISTE
    # -------------------------
    list_display = (
        "code",
        "libelle",
        "acheteur",
        "scoring_value",
        "short_interpretation",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "forme_juridique",
        "avis_commercial_ref",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "code",
        "libelle",
        "acheteur__nom",
    )

    ordering = ("-updated_at",)

    autocomplete_fields = (
        "acheteur",
        "comportement_de_paiement_ref",
        "age_company_ref",
        "forme_juridique",
        "avis_commercial_ref",
        "locaux_ref",
        "categories_nace_ref",
        "created_by",
        "updated_by",
    )

    readonly_fields = (
        "scoring_value",
        "interpretation",
        "created_at",
        "updated_at",
    )

    filter_horizontal = ("categories_nace_ref",)

    # -------------------------
    # FORMULAIRE
    # -------------------------
    fieldsets = (
        (_("Identification"), {
            "fields": ("code", "libelle", "acheteur")
        }),
        (_("Critères de scoring"), {
            "fields": (
                "comportement_de_paiement_ref",
                "age_company_ref",
                "forme_juridique",
                "avis_commercial_ref",
                "locaux_ref",
                "categories_nace_ref",
            )
        }),
        (_("Résultat du scoring (calculé automatiquement)"), {
            "fields": ("scoring_value", "interpretation"),
        }),
        (_("Commentaire"), {
            "fields": ("commentaire",),
        }),
        (_("Audit"), {
            "fields": (
                "created_at",
                "updated_at",
                "created_by",
                "updated_by",
            )
        }),
    )

    # -------------------------
    # MÉTHODES D'AFFICHAGE
    # -------------------------
    @admin.display(
        description=_("Interprétation"),
        ordering="scoring_value",
    )
    def short_interpretation(self, obj):
        if not obj.interpretation:
            return "-"
        return (
            obj.interpretation[:80] + "…"
            if len(obj.interpretation) > 80
            else obj.interpretation
        )

    # -------------------------
    # AUTOMATISATION USERS
    # -------------------------
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

# Enregistrement automatique des modeles non declares avec un ModelAdmin par defaut.
AUTO_REGISTERED_MODELS = [
    ActifA,
    ActifC,
    ActifIFRS,
    ActifS,
    ActivityLog,
    AdresseAcheteur,
    Advice,
    AffectationAnalyste,
    Alerte,
    AlerteLog,
    AnalyseSectorielle,
    AntecedantsJuridique,
    Assets,
    Banquier,
    Certification,
    CodeNaceAcheteur,
    CodeNafAcheteur,
    Commande,
    CompositionAction,
    CompositionCapitalSocial,
    CompteFinancier,
    CompteFinancierIrfs,
    ConditionAchat,
    ConditionDeVente,
    ConformiteReglementation,
    ConseilAdministration,
    CredendoCommande,
    DocDownload,
    Document,
    DocumentAlerte,
    DonneesEnregistrement,
    ElementSurveillance,
    EmailAcheteur,
    Expenses,
    GeneratedReport,
    Geopolitics,
    InnovationDeveloppement,
    Liabilities,
    Logo,
    MailAttachment,
    MailInfo,
    Marque,
    NotifClient,
    Notification,
    OffBalanceSheet,
    OperationEtHistorique,
    OpinionCreditAcremac,
    PassifA,
    PassifC,
    PassifIFRS,
    PassifS,
    PortableAcheteur,
    Portefeuille,
    PortefeuilleClient,
    ProcedureCollective,
    Products,
    ProduitService,
    ProprieteEtActif,
    Rapport,
    RatioFinancierIrfs,
    RatiosIFRS,
    RegistreCommerce,
    ReportRequest,
    ResponsableAcheteur,
    ResultatA,
    ResultatC,
    ResultatIFRS,
    ResultatS,
    Resume,
    RiskManagment,
    RiskRating,
    Scoring,
    SommaireEtAvis,
    StrategiePlanification,
    Structure,
    SuiviCommande,

    TelephoneAcheteur,
    Tendance,
    UserReportQuota,
    ValeurCompteIrfs,
    ValeurRatioIrfs,
    ValidationRapport,
    Warning,
    WarningAttachment
]

for model in AUTO_REGISTERED_MODELS:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass


@admin.register(MailInboxConfig)
class MailInboxConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "imap_user", "imap_host", "imap_port", "use_ssl", "is_active", "last_polled_at")
    list_filter = ("is_active", "use_ssl")
    search_fields = ("name", "imap_user", "imap_host")
    readonly_fields = ("last_polled_at", "last_error", "created_at", "updated_at")


@admin.register(MailSource)
class MailSourceAdmin(admin.ModelAdmin):
    list_display = ("client_name", "email_or_domain", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("client_name", "email_or_domain")


class MailAttachmentInline(admin.TabularInline):
    model = MailAttachment
    extra = 0
    readonly_fields = ("filename", "content_type", "size", "file", "created_at")
    can_delete = False


@admin.register(IncomingMail)
class IncomingMailAdmin(admin.ModelAdmin):
    list_display = ("subject", "from_email", "status", "received_at", "assigned_to")
    list_filter = ("status",)
    search_fields = ("subject", "from_email", "message_id")
    readonly_fields = ("message_id", "received_at", "created_at", "updated_at")
    inlines = [MailAttachmentInline]

