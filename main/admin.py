import os
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from safedelete.admin import SafeDeleteAdmin, highlight_deleted
from simple_history.admin import SimpleHistoryAdmin
from django.contrib import messages  # Ajout de l'import manquant
from django.utils.html import format_html  # Ajout pour format_html
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.admin import GenericTabularInline
from django.urls import reverse
from django.utils.safestring import mark_safe
from decimal import Decimal
import base64
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum, Avg, Max, Min
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils.http import urlencode

User = get_user_model()

from main.models import *
from main.forms import *

# Register your models here.



@admin.register(Referer)
class RefererAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
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


@admin.register(Pays)
class PaysAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):  # Retirer ImportExportModelAdmin si non installé
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
            'fields': ('code', 'nom')
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

@admin.register(Province)
class ProvinceAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    list_display = [
        'code', 'nom', 'pays', 'is_active', 'deleted', 
        'date_creation', 'date_modification'
    ]
    list_display_links = ['code', 'nom']
    list_filter = [
        'is_active', 'pays',
        ('date_creation', admin.DateFieldListFilter),
        ('date_modification', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['nom', 'code', 'pays__nom']
    list_select_related = ['pays']
    list_editable = ['is_active']
    raw_id_fields = ['pays']
    ordering = ['nom']
    autocomplete_fields = ['pays']
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'nom', 'pays')
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
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('pays')

@admin.register(Ville)
class VilleAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    list_display = [
        'code', 'nom', 'province', 'get_country', 'is_active', 
        'deleted', 'date_creation'
    ]
    list_display_links = ['code', 'nom']
    list_filter = [
        'is_active', 'province__pays', 'province',
        ('date_creation', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    search_fields = ['nom', 'code', 'province__nom', 'province__pays__nom']
    list_select_related = ['province', 'province__pays']
    list_editable = ['is_active']
    raw_id_fields = ['province']
    ordering = ['nom']
    autocomplete_fields = ['province']
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('code', 'nom', 'province')
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
    
    def get_country(self, obj):
        return obj.province.pays if obj.province and obj.province.pays else "-"
    get_country.short_description = _('Pays')
    get_country.admin_order_field = 'province__pays__nom'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('province__pays')

@admin.register(Annee)
class AnneeAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    list_display = [
        'annee', 'is_active', 'deleted', 'date_creation', 'date_modification'
    ]
    list_filter = [
        'is_active',
        ('annee', admin.RelatedOnlyFieldListFilter),
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
    model = NotificationLog
    extra = 0
    readonly_fields = ['portefeuille', 'code_evenement', 'date_notification', 'description', 'actif']
    can_delete = False
    max_num = 5
    verbose_name = _('Notification récente')
    verbose_name_plural = _('Notifications récentes')
    classes = ['collapse']

class AlerteLogInline(admin.TabularInline):
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
    list_display = [
        'code', 'nom', 'sigle', 'forme_juridique', 'categorie_entreprise',
        'statut_entreprise', 'pays', 'ville', 'created_at',
        'portefeuilles_count', 'alertes_recentes'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_display_links = ['code', 'nom']
    list_filter = [
        'forme_juridique', 'categorie_entreprise', 'statut_entreprise',
        'pays', 'province', 'ville',
        'created_by', 'updated_by',
        ('date_creation', admin.DateFieldListFilter),
        ('created_at', admin.DateFieldListFilter),
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = [
        'code', 'nom', 'sigle', 'email', 'site_internet',
        'activite_principale', 'description',
        'pays__nom', 'ville__nom', 'province__nom',
        'forme_juridique__libelle', 'categorie_entreprise__libelle'
    ]
    
    list_select_related = [
        'forme_juridique', 'categorie_entreprise', 'statut_entreprise',
        'pays', 'province', 'ville', 'couleur_commentaire',
        'created_by', 'updated_by'
    ]
    
    list_editable = ['sigle']
    raw_id_fields = [
        'forme_juridique', 'categorie_entreprise', 'statut_entreprise',
        'pays', 'province', 'ville', 'couleur_commentaire',
        'created_by', 'updated_by'
    ]
    
    autocomplete_fields = [
        'forme_juridique', 'categorie_entreprise', 'statut_entreprise',
        'pays', 'province', 'ville', 'couleur_commentaire'
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
            'fields': ('forme_juridique', 'categorie_entreprise', 'statut_entreprise', 'date_creation'),
            'classes': ('collapse',)
        }),
        (_('Activité'), {
            'fields': ('code_nace', 'activite_principale'),
            'classes': ('collapse',)
        }),
        (_('Coordonnées'), {
            'fields': ('email', 'site_internet', 'fax', 'telephone'),
            'classes': ('collapse',)
        }),
        (_('Adresse'), {
            'fields': (
                'numero_adresse', 'rue_adresse', 'code_postal', 'boite_postale',
                'pays', 'province', 'ville'
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
            'forme_juridique', 'categorie_entreprise', 'statut_entreprise',
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
        
        
        
        


# ================ CLASSE DE BASE COMMUNE ================

class AcheteurLinkedModelAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Classe de base pour tous les modèles liés à Acheteur"""
    
    list_display = ['acheteur', 'created_at', 'updated_by_display', 'created_by_display']
    list_display_links = ['acheteur']
    list_filter = [
        'acheteur',
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
        'created_by', 'updated_by',
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = ['acheteur__nom', 'acheteur__code', 'commentaire']
    list_select_related = ['acheteur', 'created_by', 'updated_by']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    raw_id_fields = ['acheteur', 'created_by', 'updated_by']
    autocomplete_fields = ['acheteur']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def updated_by_display(self, obj):
        if obj.updated_by:
            return obj.updated_by.username
        return "-"
    updated_by_display.short_description = _('Mis à jour par')
    updated_by_display.admin_order_field = 'updated_by__username'
    
    def created_by_display(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return "-"
    created_by_display.short_description = _('Créé par')
    created_by_display.admin_order_field = 'created_by__username'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvel objet
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'acheteur', 'created_by', 'updated_by'
        )

# ================ RÉSUMÉ FINANCIER ================

@admin.register(Resume)
class ResumeAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'capital_social', 'chiffre_affaire', 'resultat_net',
        'capitaux_propre', 'nombre_employe', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + [
        'devise__nom', 'commentaire'
    ]
    list_select_related = AcheteurLinkedModelAdmin.list_select_related + ['devise', 'couleur_commentaire']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('acheteur', 'devise', 'date_creation')
        }),
        (_('Indicateurs financiers'), {
            'fields': (
                'capital_social', 'chiffre_affaire', 'resultat_net',
                'capitaux_propre', 'nombre_employe'
            ),
            'classes': ('wide',)
        }),
        (_('Commentaire'), {
            'fields': ('couleur_commentaire', 'commentaire'),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + ['devise', 'couleur_commentaire']
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + ['devise', 'couleur_commentaire']
    
    actions = ['calculate_financial_ratios', 'export_financial_data']
    
    @admin.action(description=_('Calculer les ratios financiers'))
    def calculate_financial_ratios(self, request, queryset):
        for resume in queryset:
            if resume.chiffre_affaire and resume.resultat_net:
                try:
                    # Calcul de la marge nette
                    marge_nette = (resume.resultat_net / resume.chiffre_affaire) * 100
                    self.message_user(
                        request,
                        f"Résumé {resume.id}: Marge nette = {marge_nette:.2f}%",
                        messages.INFO
                    )
                except ZeroDivisionError:
                    self.message_user(
                        request,
                        f"Résumé {resume.id}: Chiffre d'affaire nul",
                        messages.WARNING
                    )
        self.message_user(
            request,
            'Calcul des ratios terminé.',
            messages.SUCCESS
        )

# ================ ÉVALUATION DU RISQUE ================

class RiskScoreFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les scores de risque"""
    title = _('Score de risque')
    parameter_name = 'risk_score'
    
    def lookups(self, request, model_admin):
        return (
            ('0-2', _('Faible (0-2)')),
            ('3-5', _('Moyen (3-5)')),
            ('6-8', _('Élevé (6-8)')),
            ('9', _('Maximum (9)')),
        )
    
    def queryset(self, request, queryset):
        if self.value() == '0-2':
            return queryset.annotate(
                score=models.Count(
                    models.Case(
                        models.When(remboursabilite=True, then=1),
                        models.When(situation_liquidite=True, then=1),
                        models.When(performance_rentabilite=True, then=1),
                        models.When(perspective_secteur=True, then=1),
                        models.When(qualite_information_analyse=True, then=1),
                        models.When(existence_garantie=True, then=1),
                        models.When(terme_financier_duree_pret=True, then=1),
                        models.When(mesure_propre_soutenir_credit=True, then=1),
                        output_field=models.IntegerField(),
                    )
                )
            ).filter(score__lte=2)
        elif self.value() == '3-5':
            return queryset.annotate(
                score=models.Count(
                    models.Case(
                        models.When(remboursabilite=True, then=1),
                        models.When(situation_liquidite=True, then=1),
                        models.When(performance_rentabilite=True, then=1),
                        models.When(perspective_secteur=True, then=1),
                        models.When(qualite_information_analyse=True, then=1),
                        models.When(existence_garantie=True, then=1),
                        models.When(terme_financier_duree_pret=True, then=1),
                        models.When(mesure_propre_soutenir_credit=True, then=1),
                        output_field=models.IntegerField(),
                    )
                )
            ).filter(score__gte=3, score__lte=5)
        elif self.value() == '6-8':
            return queryset.annotate(
                score=models.Count(
                    models.Case(
                        models.When(remboursabilite=True, then=1),
                        models.When(situation_liquidite=True, then=1),
                        models.When(performance_rentabilite=True, then=1),
                        models.When(perspective_secteur=True, then=1),
                        models.When(qualite_information_analyse=True, then=1),
                        models.When(existence_garantie=True, then=1),
                        models.When(terme_financier_duree_pret=True, then=1),
                        models.When(mesure_propre_soutenir_credit=True, then=1),
                        output_field=models.IntegerField(),
                    )
                )
            ).filter(score__gte=6, score__lte=8)
        elif self.value() == '9':
            return queryset.annotate(
                score=models.Count(
                    models.Case(
                        models.When(remboursabilite=True, then=1),
                        models.When(situation_liquidite=True, then=1),
                        models.When(performance_rentabilite=True, then=1),
                        models.When(perspective_secteur=True, then=1),
                        models.When(qualite_information_analyse=True, then=1),
                        models.When(existence_garantie=True, then=1),
                        models.When(terme_financier_duree_pret=True, then=1),
                        models.When(mesure_propre_soutenir_credit=True, then=1),
                        output_field=models.IntegerField(),
                    )
                )
            ).filter(score=9)
        return queryset

@admin.register(RiskRating)
class RiskRatingAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'risk_score_display', 'cotation_du_risque',
        'indice_du_risque', 'risk_gauge_preview', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_filter = [
        'cotation_du_risque', 'indice_du_risque', RiskScoreFilter
    ] + AcheteurLinkedModelAdmin.list_filter
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('acheteur',)
        }),
        (_('Évaluation des risques'), {
            'fields': (
                'remboursabilite', 'situation_liquidite', 'performance_rentabilite',
                'perspective_secteur', 'qualite_information_analyse', 'existence_garantie',
                'terme_financier_duree_pret', 'mesure_propre_soutenir_credit'
            ),
            'classes': ('wide',)
        }),
        (_('Cotation et indice'), {
            'fields': ('cotation_du_risque', 'indice_du_risque'),
            'classes': ('collapse',)
        }),
        (_('Analyse et interprétation'), {
            'fields': ('interpretation', 'analyse'),
            'classes': ('wide',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['risk_score_display', 'risk_gauge_preview']
    
    def risk_score_display(self, obj):
        score = obj.calculate_risk_score()
        if score <= 2:
            color = 'green'
            text = f'Faible ({score}/8)'
        elif score <= 5:
            color = 'orange'
            text = f'Moyen ({score}/8)'
        else:
            color = 'red'
            text = f'Élevé ({score}/8)'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, text)
    risk_score_display.short_description = _('Score risque')
    
    def risk_gauge_preview(self, obj):
        try:
            # Essayer de générer l'image SVG
            score = obj.calculate_risk_score()
            svg_content = self.generate_risk_gauge_svg(score)
            return format_html(
                '<div style="text-align: center;">'
                '<div style="margin-bottom: 10px;">Score: {}/8</div>'
                '{}'
                '</div>',
                score,
                mark_safe(svg_content)
            )
        except Exception as e:
            return format_html(
                '<div style="color: red;">Erreur de génération: {}</div>',
                str(e)
            )
    risk_gauge_preview.short_description = _('Jauge risque')
    
    def generate_risk_gauge_svg(self, score):
        """Génère un SVG simple pour la jauge de risque"""
        # Score sur 8 points
        percentage = (score / 8) * 100
        
        # Couleur basée sur le score
        if score <= 2:
            color = '#4CAF50'  # Vert
        elif score <= 5:
            color = '#FF9800'  # Orange
        else:
            color = '#F44336'  # Rouge
        
        svg = f'''
        <svg width="200" height="100" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
            <!-- Arc de fond -->
            <path d="M20,80 A60,60 0 0,1 180,80" fill="none" stroke="#e0e0e0" stroke-width="20"/>
            
            <!-- Arc de score -->
            <path d="M20,80 A60,60 0 0,1 {20 + (percentage/100)*160},80" 
                  fill="none" stroke="{color}" stroke-width="20" stroke-linecap="round"/>
            
            <!-- Aiguille -->
            <line x1="100" y1="80" 
                  x2="{100 + 50 * (percentage/100 - 0.5)}" 
                  y2="{40}" 
                  stroke="#333" stroke-width="3"/>
            <circle cx="100" cy="80" r="5" fill="#333"/>
            
            <!-- Textes -->
            <text x="100" y="95" text-anchor="middle" font-size="12" fill="#333">
                {score}/8
            </text>
        </svg>
        '''
        return svg
    
    actions = ['recalculate_all_scores', 'generate_risk_reports']
    
    @admin.action(description=_('Recalculer tous les scores'))
    def recalculate_all_scores(self, request, queryset):
        for risk in queryset:
            score = risk.calculate_risk_score()
            # Mettre à jour la cotation basée sur le score
            if score <= 2:
                risk.cotation_du_risque = "non_douteux"
            elif score <= 4:
                risk.cotation_du_risque = "risque_faible"
            elif score <= 6:
                risk.cotation_du_risque = "risque_modere"
            else:
                risk.cotation_du_risque = "mise_en_garde"
            risk.save(update_fields=['cotation_du_risque'])
        
        self.message_user(
            request,
            f'{queryset.count()} scores recalculés.',
            messages.SUCCESS
        )

# ================ DONNÉES D'ENREGISTREMENT ================

@admin.register(DonneesEnregistrement)
class DonneesEnregistrementAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'nom_anterieur', 'forme_juridique',
        'statut_registre', 'numero_registre_commerce',
        'date_creation', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + [
        'nom_anterieur', 'numero_registre_commerce', 'numero_fiscale',
        'forme_juridique', 'statut_registre'
    ]
    list_select_related = AcheteurLinkedModelAdmin.list_select_related + ['couleur_commentaire']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('acheteur', 'nom_anterieur', 'date_creation', 'date_registre')
        }),
        (_('Identifiants légaux'), {
            'fields': ('numero_registre_commerce', 'numero_fiscale'),
            'classes': ('collapse',)
        }),
        (_('Statut juridique'), {
            'fields': ('forme_juridique', 'statut_registre'),
            'classes': ('collapse',)
        }),
        (_('Commentaire'), {
            'fields': ('couleur_commentaire', 'commentaire'),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + ['couleur_commentaire']
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + ['couleur_commentaire']

# ================ TENDANCE ================


# ================ RESPONSABLE ACHETEUR ================

class ResponsableAcheteurInline(admin.TabularInline):
    model = ResponsableAcheteur
    extra = 1
    fields = ['nom', 'prenom', 'sexe', 'poste', 'nationalite', 'commentaire_preview']
    readonly_fields = ['commentaire_preview']
    verbose_name = _('Responsable')
    verbose_name_plural = _('Responsables')
    classes = ['collapse']
    
    def commentaire_preview(self, obj):
        if obj.commentaire:
            preview = obj.commentaire[:50]
            if len(obj.commentaire) > 50:
                preview += "..."
            return preview
        return "-"
    commentaire_preview.short_description = _('Commentaire')

@admin.register(ResponsableAcheteur)
class ResponsableAcheteurAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'full_name_display', 'poste', 'sexe',
        'nationalite', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_filter = [
        'sexe', 'poste', 'nationalite'
    ] + AcheteurLinkedModelAdmin.list_filter
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + [
        'nom', 'prenom', 'poste', 'nationalite', 'commentaire'
    ]
    list_select_related = AcheteurLinkedModelAdmin.list_select_related + ['couleur_commentaire']
    
    fieldsets = (
        (_('Informations personnelles'), {
            'fields': ('acheteur', 'nom', 'prenom', 'sexe', 'nationalite')
        }),
        (_('Poste et fonction'), {
            'fields': ('poste',),
            'classes': ('collapse',)
        }),
        (_('Commentaire'), {
            'fields': ('couleur_commentaire', 'commentaire'),
            'classes': ('wide',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name_display(self, obj):
        return f"{obj.nom} {obj.prenom}"
    full_name_display.short_description = _('Nom complet')
    full_name_display.admin_order_field = 'nom'
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + ['couleur_commentaire']
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + ['couleur_commentaire']

# ================ ANTÉCÉDENTS JURIDIQUES ================

@admin.register(AntecedantsJuridique)
class AntecedantsJuridiqueAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'antecedent_type_display', 'dossier_faillite',
        'jugement_cour', 'commentaire_preview', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + [
        'dossier_faillite', 'jugement_cour', 'antecedant_redressement',
        'autre', 'commentaire'
    ]
    list_select_related = AcheteurLinkedModelAdmin.list_select_related + ['couleur_commentaire']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('acheteur',)
        }),
        (_('Antécédents juridiques'), {
            'fields': (
                'dossier_faillite', 'jugement_cour',
                'antecedant_redressement', 'autre'
            ),
            'classes': ('wide',)
        }),
        (_('Commentaire'), {
            'fields': ('couleur_commentaire', 'commentaire'),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def antecedent_type_display(self, obj):
        if obj.dossier_faillite and obj.dossier_faillite.strip():
            return format_html('<span style="color: red;">Faillite</span>')
        elif obj.jugement_cour and obj.jugement_cour.strip():
            return format_html('<span style="color: orange;">Jugement</span>')
        elif obj.antecedant_redressement and obj.antecedant_redressement.strip():
            return format_html('<span style="color: blue;">Redressement</span>')
        elif obj.autre and obj.autre.strip():
            return format_html('<span style="color: gray;">Autre</span>')
        return "-"
    antecedent_type_display.short_description = _('Type')
    
    def commentaire_preview(self, obj):
        if obj.commentaire:
            preview = obj.commentaire[:60]
            if len(obj.commentaire) > 60:
                preview += "..."
            return preview
        return "-"
    commentaire_preview.short_description = _('Commentaire')
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + ['couleur_commentaire']
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + ['couleur_commentaire']

# ================ GESTION DES RISQUES ================

@admin.register(RiskManagment)
class RiskManagmentAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'management_score_display', 'professionalisme',
        'organisation', 'turn_over', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_filter = [
        'professionalisme', 'organisation', 'turn_over',
        'greve', 'degradation_qualite', 'non_respect_condition'
    ] + AcheteurLinkedModelAdmin.list_filter
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('acheteur',)
        }),
        (_('Évaluation de la gestion'), {
            'fields': (
                'professionalisme', 'organisation', 'turn_over',
                'greve', 'degradation_qualite', 'non_respect_condition'
            ),
            'classes': ('wide',)
        }),
        (_('Commentaire'), {
            'fields': ('couleur_commentaire', 'commentaire'),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def management_score_display(self, obj):
        score = obj.get_management_score()
        oui_count = score['oui_count']
        total = score['total']
        
        if oui_count >= 4:
            color = 'green'
            rating = 'Bonne'
        elif oui_count >= 2:
            color = 'orange'
            rating = 'Moyenne'
        else:
            color = 'red'
            rating = 'Faible'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({}/{})</span>',
            color, rating, oui_count, total
        )
    management_score_display.short_description = _('Score gestion')
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + ['couleur_commentaire']
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + ['couleur_commentaire']

# ================ CONSEIL D'ADMINISTRATION ================

@admin.register(ConseilAdministration)
class ConseilAdministrationAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'nom', 'fonction_dans_le_conseil',
        'code_postale_adresse', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + [
        'nom', 'fonction_dans_le_conseil', 'numero_adresse',
        'rue_adresse', 'code_postale_adresse', 'commentaire'
    ]
    list_select_related = AcheteurLinkedModelAdmin.list_select_related + ['couleur_commentaire']
    
    fieldsets = (
        (_('Informations personnelles'), {
            'fields': ('acheteur', 'nom')
        }),
        (_('Fonction et adresse'), {
            'fields': (
                'fonction_dans_le_conseil',
                'numero_adresse', 'rue_adresse', 'code_postale_adresse'
            ),
            'classes': ('collapse',)
        }),
        (_('Commentaire'), {
            'fields': ('couleur_commentaire', 'commentaire'),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + ['couleur_commentaire']
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + ['couleur_commentaire']

# ================ COMPOSITION DU CAPITAL SOCIAL ================

@admin.register(CompositionCapitalSocial)
class CompositionCapitalSocialAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'devise', 'emis', 'publie', 'libere',
        'capital_total_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + ['commentaire']
    list_select_related = AcheteurLinkedModelAdmin.list_select_related + ['devise', 'couleur_commentaire']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('acheteur', 'devise')
        }),
        (_('Capital social'), {
            'fields': ('emis', 'publie', 'libere'),
            'classes': ('wide',)
        }),
        (_('Commentaire'), {
            'fields': ('couleur_commentaire', 'commentaire'),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def capital_total_display(self, obj):
        total = sum(filter(None, [obj.emis, obj.publie, obj.libere]))
        if total:
            return f"{total:,.2f}"
        return "-"
    capital_total_display.short_description = _('Total capital')
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + ['devise', 'couleur_commentaire']
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + ['devise', 'couleur_commentaire']

# ================ COMPOSITION DE L'ACTIONNARIAT ================

@admin.register(CompositionAction)
class CompositionActionAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'nom', 'prenom', 'pourcentage',
        'pourcentage_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + ['nom', 'prenom', 'commentaire']
    list_select_related = AcheteurLinkedModelAdmin.list_select_related + ['couleur_commentaire']
    
    fieldsets = (
        (_('Informations personnelles'), {
            'fields': ('acheteur', 'nom', 'prenom')
        }),
        (_('Participation'), {
            'fields': ('pourcentage',),
            'classes': ('wide',)
        }),
        (_('Commentaire'), {
            'fields': ('couleur_commentaire', 'commentaire'),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def pourcentage_display(self, obj):
        if obj.pourcentage:
            if obj.pourcentage > 50:
                color = 'green'
                icon = '🏢'
            elif obj.pourcentage > 10:
                color = 'blue'
                icon = '👤'
            else:
                color = 'gray'
                icon = '🔹'
            
            return format_html(
                '<span style="color: {};">{} {:.2f}%</span>',
                color, icon, obj.pourcentage
            )
        return "-"
    pourcentage_display.short_description = _('% détention')
    
    actions = ['calculate_total_percentage', 'normalize_percentages']
    
    @admin.action(description=_('Calculer le total des pourcentages'))
    def calculate_total_percentage(self, request, queryset):
        acheteurs = set()
        for comp in queryset:
            acheteurs.add(comp.acheteur)
        
        results = []
        for acheteur in acheteurs:
            total = CompositionAction.objects.filter(
                acheteur=acheteur
            ).aggregate(total=models.Sum('pourcentage'))['total'] or Decimal('0')
            
            results.append(f"{acheteur}: {total:.2f}%")
        
        if results:
            self.message_user(
                request,
                f"Totaux: {' | '.join(results)}",
                messages.INFO
            )
    
    @admin.action(description=_('Normaliser les pourcentages à 100%'))
    def normalize_percentages(self, request, queryset):
        updated = 0
        for comp in queryset:
            if comp.acheteur:
                total = CompositionAction.objects.filter(
                    acheteur=comp.acheteur
                ).exclude(pk=comp.pk).aggregate(
                    total=models.Sum('pourcentage')
                )['total'] or Decimal('0')
                
                disponible = Decimal('100') - total
                if comp.pourcentage > disponible:
                    comp.pourcentage = disponible
                    comp.save(update_fields=['pourcentage'])
                    updated += 1
        
        self.message_user(
            request,
            f'{updated} pourcentages normalisés.',
            messages.SUCCESS
        )
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + ['couleur_commentaire']
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + ['couleur_commentaire']

# ================ OPINION CRÉDIT ACREMAC ================

@admin.register(OpinionCreditAcremac)
class OpinionCreditAcremacAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'risk_summary_display', 'montant_credit_maximum',
        'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + ['commentaire']
    list_select_related = AcheteurLinkedModelAdmin.list_select_related + ['couleur_commentaire']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('acheteur', 'montant_credit_maximum')
        }),
        (_('Évaluation des risques'), {
            'fields': (
                'risque_de_defaut', 'risque_de_concentration_credit',
                'risque_de_reputation', 'risque_pays',
                'risque_de_taux_dinteret', 'risque_de_liquidite'
            ),
            'classes': ('wide',)
        }),
        (_('Classification des risques'), {
            'fields': (
                'risque_eleve', 'risque_moyen', 'risque_faible'
            ),
            'classes': ('collapse',)
        }),
        (_('Commentaire'), {
            'fields': ('couleur_commentaire', 'commentaire'),
            'classes': ('wide',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def risk_summary_display(self, obj):
        # Calculer le risque total
        risques = [
            obj.risque_de_defaut,
            obj.risque_de_concentration_credit,
            obj.risque_de_reputation,
            obj.risque_pays,
            obj.risque_de_taux_dinteret,
            obj.risque_de_liquidite
        ]
        
        total_risque = sum(filter(None, risques))
        
        if total_risque <= 10:
            color = 'green'
            niveau = 'Faible'
        elif total_risque <= 30:
            color = 'orange'
            niveau = 'Moyen'
        else:
            color = 'red'
            niveau = 'Élevé'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({}/60)</span>',
            color, niveau, total_risque
        )
    risk_summary_display.short_description = _('Résumé risque')
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + ['couleur_commentaire']
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + ['couleur_commentaire']
    
    
    


# ================ CLASSE DE BASE COMMUNE ================

class AcheteurLinkedModelAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    """Classe de base pour tous les modèles liés à Acheteur"""
    
    list_display = ['acheteur', 'created_at', 'updated_by_display', 'created_by_display']
    list_display_links = ['acheteur']
    list_filter = [
        'acheteur',
        ('created_at', admin.DateFieldListFilter),
        ('updated_at', admin.DateFieldListFilter),
        'created_by', 'updated_by',
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = ['acheteur__nom', 'acheteur__code', 'commentaire']
    list_select_related = ['acheteur', 'created_by', 'updated_by']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    raw_id_fields = ['acheteur', 'created_by', 'updated_by']
    autocomplete_fields = ['acheteur']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def updated_by_display(self, obj):
        if obj.updated_by:
            return obj.updated_by.username
        return "-"
    updated_by_display.short_description = _('Mis à jour par')
    updated_by_display.admin_order_field = 'updated_by__username'
    
    def created_by_display(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return "-"
    created_by_display.short_description = _('Créé par')
    created_by_display.admin_order_field = 'created_by__username'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvel objet
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'acheteur', 'created_by', 'updated_by'
        )

# ================ STRUCTURE (FILIALE OU BRANCHE) ================

@admin.register(Structure)
class StructureAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'nom', 'type_affiliation', 'type_affiliation_ref',
        'code_postale_adresse', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + [
        'nom', 'type_affiliation', 'numero_adresse', 'rue_adresse',
        'code_postale_adresse', 'commentaire'
    ]
    list_select_related = AcheteurLinkedModelAdmin.list_select_related + [
        'type_affiliation_ref', 'couleur_commentaire'
    ]
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('acheteur', 'nom')
        }),
        (_('Affiliation'), {
            'fields': ('type_affiliation', 'type_affiliation_ref'),
            'classes': ('collapse',)
        }),
        (_('Adresse'), {
            'fields': ('numero_adresse', 'rue_adresse', 'code_postale_adresse'),
            'classes': ('collapse',)
        }),
        (_('Commentaire'), {
            'fields': ('couleur_commentaire', 'commentaire'),
            'classes': ('wide',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + [
        'type_affiliation_ref', 'couleur_commentaire'
    ]
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + [
        'type_affiliation_ref', 'couleur_commentaire'
    ]

# ================ ANALYSE SECTORIELLE ================

@admin.register(AnalyseSectorielle)
class AnalyseSectorielleAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'commentaire_preview', 'impact_covid_preview', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('acheteur',)
        }),
        (_('Analyse sectorielle'), {
            'fields': ('commentaire', 'impact_covid_19'),
            'classes': ('wide',)
        }),
        (_('Apparence'), {
            'fields': ('couleur_commentaire',),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def commentaire_preview(self, obj):
        if obj.commentaire:
            preview = obj.commentaire[:80]
            if len(obj.commentaire) > 80:
                preview += "..."
            return preview
        return "-"
    commentaire_preview.short_description = _('Commentaire')
    
    def impact_covid_preview(self, obj):
        if obj.impact_covid_19:
            preview = obj.impact_covid_19[:80]
            if len(obj.impact_covid_19) > 80:
                preview += "..."
            return preview
        return "-"
    impact_covid_preview.short_description = _('Impact COVID')
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + ['couleur_commentaire']
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + ['couleur_commentaire']

# ================ COMPTE FINANCIER ================

class DateRangeFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les périodes de compte"""
    title = _('Période de compte')
    parameter_name = 'date_range'
    
    def lookups(self, request, model_admin):
        return (
            ('has_n', _('A N')),
            ('has_n1', _('A N-1')),
            ('has_n2', _('A N-2')),
            ('complete', _('Complet')),
            ('incomplete', _('Incomplet')),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'has_n':
            return queryset.filter(date_compte__isnull=False, date_fin__isnull=False)
        elif self.value() == 'has_n1':
            return queryset.filter(date_compte_n_moins_un__isnull=False, date_fin_n_moins_un__isnull=False)
        elif self.value() == 'has_n2':
            return queryset.filter(date_compte_n_moins_deux__isnull=False, date_fin_n_moins_deux__isnull=False)
        elif self.value() == 'complete':
            return queryset.filter(
                date_compte__isnull=False, date_fin__isnull=False,
                date_compte_n_moins_un__isnull=False, date_fin_n_moins_un__isnull=False,
                date_compte_n_moins_deux__isnull=False, date_fin_n_moins_deux__isnull=False
            )
        elif self.value() == 'incomplete':
            return queryset.filter(
                models.Q(date_compte__isnull=True) | models.Q(date_fin__isnull=True) |
                models.Q(date_compte_n_moins_un__isnull=True) | models.Q(date_fin_n_moins_un__isnull=True) |
                models.Q(date_compte_n_moins_deux__isnull=True) | models.Q(date_fin_n_moins_deux__isnull=True)
            )
        return queryset

@admin.register(CompteFinancier)
class CompteFinancierAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'cabinet', 'type_compte', 'devise', 'type_bilan',
        'date_range_display', 'est_rempli_display', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_filter = [
        'devise', 'type_bilan', 'credibilite_cabinet', DateRangeFilter
    ] + AcheteurLinkedModelAdmin.list_filter
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + [
        'cabinet', 'requis_pour_deposer', 'source', 'presentation',
        'type_compte', 'commentaire'
    ]
    
    list_select_related = AcheteurLinkedModelAdmin.list_select_related + ['couleur_commentaire']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('acheteur', 'cabinet', 'source', 'presentation')
        }),
        (_('Validation'), {
            'fields': ('requis_pour_deposer', 'credibilite_cabinet'),
            'classes': ('collapse',)
        }),
        (_('Périodes de compte'), {
            'fields': (
                ('date_compte', 'date_fin'),
                ('date_compte_n_moins_un', 'date_fin_n_moins_un'),
                ('date_compte_n_moins_deux', 'date_fin_n_moins_deux')
            ),
            'classes': ('wide',)
        }),
        (_('Caractéristiques'), {
            'fields': ('type_compte', 'devise', 'type_bilan'),
            'classes': ('collapse',)
        }),
        (_('Commentaire'), {
            'fields': ('couleur_commentaire', 'commentaire'),
            'classes': ('wide',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def date_range_display(self, obj):
        periods = []
        if obj.date_compte and obj.date_fin:
            periods.append(f"N: {obj.date_compte.year}")
        if obj.date_compte_n_moins_un and obj.date_fin_n_moins_un:
            periods.append(f"N-1: {obj.date_compte_n_moins_un.year}")
        if obj.date_compte_n_moins_deux and obj.date_fin_n_moins_deux:
            periods.append(f"N-2: {obj.date_compte_n_moins_deux.year}")
        
        if periods:
            return ", ".join(periods)
        return _("Aucune période")
    date_range_display.short_description = _('Périodes')
    
    def est_rempli_display(self, obj):
        if obj.est_rempli():
            return format_html('<span style="color: green;">✓ Complet</span>')
        return format_html('<span style="color: orange;">⚠ Incomplet</span>')
    est_rempli_display.short_description = _('Statut')
    
    actions = ['mark_as_complete', 'export_financial_data']
    
    @admin.action(description=_('Marquer comme complet'))
    def mark_as_complete(self, request, queryset):
        updated = 0
        for compte in queryset:
            # Ajouter des valeurs par défaut pour les champs manquants
            if not compte.type_compte:
                compte.type_compte = "Annuel"
            if not compte.devise:
                compte.devise = "XAF"
            if not compte.type_bilan:
                compte.type_bilan = "Classique"
            compte.save()
            updated += 1
        
        self.message_user(
            request,
            f'{updated} comptes marqués comme complets.',
            messages.SUCCESS
        )
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + ['couleur_commentaire']
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + ['couleur_commentaire']

# ================ OPÉRATION ET HISTORIQUE ================

class OperationEtHistoriqueInline(admin.TabularInline):
    model = OperationEtHistorique.importation.through
    extra = 1
    verbose_name = _('Importation')
    verbose_name_plural = _('Importations')
    classes = ['collapse']

@admin.register(OperationEtHistorique)
class OperationEtHistoriqueAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'description_preview', 'historique_preview',
        'importation_count', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + [
        'commentaire_ratios', 'description_complete_activite',
        'historique', 'importation__nom'
    ]
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('acheteur',)
        }),
        (_('Activité'), {
            'fields': ('description_complete_activite',),
            'classes': ('wide',)
        }),
        (_('Historique'), {
            'fields': ('historique',),
            'classes': ('wide',)
        }),
        (_('Analyse'), {
            'fields': ('commentaire_ratios',),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['importation']
    
    def description_preview(self, obj):
        if obj.description_complete_activite:
            preview = obj.description_complete_activite[:60]
            if len(obj.description_complete_activite) > 60:
                preview += "..."
            return preview
        return "-"
    description_preview.short_description = _('Description activité')
    
    def historique_preview(self, obj):
        if obj.historique:
            preview = obj.historique[:60]
            if len(obj.historique) > 60:
                preview += "..."
            return preview
        return "-"
    historique_preview.short_description = _('Historique')
    
    def importation_count(self, obj):
        return obj.importation.count()
    importation_count.short_description = _('Nb importations')
    
    actions = ['export_operations_report']

# ================ PROPRIÉTÉ ET ACTIF ================

class ProprieteEtActifInline(admin.TabularInline):
    model = ProprieteEtActif.locaux.through
    extra = 1
    verbose_name = _('Local')
    verbose_name_plural = _('Locaux')
    classes = ['collapse']

@admin.register(ProprieteEtActif)
class ProprieteEtActifAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'branche', 'locaux_count', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + [
        'branche', 'locaux__nom'
    ]
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('acheteur', 'branche')
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['locaux']
    
    def locaux_count(self, obj):
        return obj.locaux.count()
    locaux_count.short_description = _('Nb locaux')
    
    actions = ['export_properties_report']

# ================ CONDITION D'ACHAT ================

class ConditionAchatInlineLocal(admin.TabularInline):
    model = ConditionAchat.local.through
    extra = 1
    verbose_name = _('Condition locale')
    verbose_name_plural = _('Conditions locales')
    classes = ['collapse']

class ConditionAchatInlineImportation(admin.TabularInline):
    model = ConditionAchat.importation.through
    extra = 1
    verbose_name = _('Condition importation')
    verbose_name_plural = _('Conditions importation')
    classes = ['collapse']

@admin.register(ConditionAchat)
class ConditionAchatAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'clients_preview', 'fournisseur_preview',
        'local_count', 'importation_count', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + [
        'les_clients', 'fournisseur', 'local__nom', 'importation__nom'
    ]
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('acheteur',)
        }),
        (_('Clients'), {
            'fields': ('les_clients',),
            'classes': ('wide',)
        }),
        (_('Fournisseurs'), {
            'fields': ('fournisseur',),
            'classes': ('wide',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['local', 'importation']
    
    def clients_preview(self, obj):
        if obj.les_clients:
            preview = obj.les_clients[:60]
            if len(obj.les_clients) > 60:
                preview += "..."
            return preview
        return "-"
    clients_preview.short_description = _('Clients')
    
    def fournisseur_preview(self, obj):
        if obj.fournisseur:
            preview = obj.fournisseur[:60]
            if len(obj.fournisseur) > 60:
                preview += "..."
            return preview
        return "-"
    fournisseur_preview.short_description = _('Fournisseurs')
    
    def local_count(self, obj):
        return obj.local.count()
    local_count.short_description = _('Nb cond. locales')
    
    def importation_count(self, obj):
        return obj.importation.count()
    importation_count.short_description = _('Nb cond. import')
    
    actions = ['export_purchase_conditions']

# ================ CONDITION DE VENTE ================

class ConditionDeVenteInlineLocal(admin.TabularInline):
    model = ConditionDeVente.local.through
    extra = 1
    verbose_name = _('Condition locale')
    verbose_name_plural = _('Conditions locales')
    classes = ['collapse']

@admin.register(ConditionDeVente)
class ConditionDeVenteAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'recouvrement_de_dette_jugement',
        'comportement_de_paiement', 'local_count', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_filter = [
        'recouvrement_de_dette_jugement', 'comportement_de_paiement'
    ] + AcheteurLinkedModelAdmin.list_filter
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + [
        'recouvrement_de_dette_jugement', 'comportement_de_paiement',
        'local__nom'
    ]
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('acheteur',)
        }),
        (_('Comportements'), {
            'fields': ('recouvrement_de_dette_jugement', 'comportement_de_paiement'),
            'classes': ('wide',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['local']
    
    def local_count(self, obj):
        return obj.local.count()
    local_count.short_description = _('Nb conditions')
    
    actions = ['evaluate_payment_behavior', 'export_sales_conditions']
    
    @admin.action(description=_('Évaluer comportement paiement'))
    def evaluate_payment_behavior(self, request, queryset):
        for condition in queryset:
            if "retard" in condition.comportement_de_paiement.lower():
                condition.comportement_de_paiement = "Mauvais payeur"
                condition.save(update_fields=['comportement_de_paiement'])
        
        self.message_user(
            request,
            f'{queryset.count()} comportements évalués.',
            messages.SUCCESS
        )

# ================ SOMMAIRE ET AVIS ================

@admin.register(SommaireEtAvis)
class SommaireEtAvisAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'commentaire_preview', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('acheteur',)
        }),
        (_('Sommaire et avis'), {
            'fields': ('commentaire',),
            'classes': ('wide',)
        }),
        (_('Apparence'), {
            'fields': ('couleur_commentaire',),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def commentaire_preview(self, obj):
        if obj.commentaire:
            preview = obj.commentaire[:100]
            if len(obj.commentaire) > 100:
                preview += "..."
            return preview
        return "-"
    commentaire_preview.short_description = _('Commentaire')
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + ['couleur_commentaire']
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + ['couleur_commentaire']

# ================ ADVICE (CONSEILS) ================

@admin.register(Advice)
class AdviceAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'points_forts_preview', 'points_faibles_preview',
        'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('acheteur',)
        }),
        (_('Points forts et faibles'), {
            'fields': ('points_forts', 'points_faibles'),
            'classes': ('wide',)
        }),
        (_('Dynamisme'), {
            'fields': ('dynamisme_court_terme', 'dynamisme_long_terme'),
            'classes': ('collapse',)
        }),
        (_('Risques'), {
            'fields': ('risque_potentiel_court_terme',),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def points_forts_preview(self, obj):
        if obj.points_forts:
            preview = obj.points_forts[:80]
            if len(obj.points_forts) > 80:
                preview += "..."
            return preview
        return "-"
    points_forts_preview.short_description = _('Points forts')
    
    def points_faibles_preview(self, obj):
        if obj.points_faibles:
            preview = obj.points_faibles[:80]
            if len(obj.points_faibles) > 80:
                preview += "..."
            return preview
        return "-"
    points_faibles_preview.short_description = _('Points faibles')
    
    actions = ['generate_advice_summary', 'export_advices']

# ================ GÉOPOLITIQUE ================

class ScoreRangeFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les scores de géopolitique"""
    title = _('Score moyen')
    parameter_name = 'avg_score'
    
    def lookups(self, request, model_admin):
        return (
            ('0-3', _('Très faible (0-3)')),
            ('4-6', _('Moyen (4-6)')),
            ('7-10', _('Élevé (7-10)')),
        )
    
    def queryset(self, request, queryset):
        if self.value() == '0-3':
            return queryset.annotate(
                avg_score=models.Case(
                    models.When(
                        models.Q(stabilite_politique__isnull=False) |
                        models.Q(etat_droit__isnull=False) |
                        models.Q(efficacite__isnull=False) |
                        models.Q(qualite__isnull=False) |
                        models.Q(liberte_expression__isnull=False),
                        then=models.Avg(models.Cast(
                            models.Case(
                                models.When(
                                    stabilite_politique__isnull=False,
                                    then=models.Cast('stabilite_politique', models.IntegerField())
                                ),
                                models.When(
                                    etat_droit__isnull=False,
                                    then=models.Cast('etat_droit', models.IntegerField())
                                ),
                                models.When(
                                    efficacite__isnull=False,
                                    then=models.Cast('efficacite', models.IntegerField())
                                ),
                                models.When(
                                    qualite__isnull=False,
                                    then=models.Cast('qualite', models.IntegerField())
                                ),
                                models.When(
                                    liberte_expression__isnull=False,
                                    then=models.Cast('liberte_expression', models.IntegerField())
                                ),
                                default=models.Value(0),
                                output_field=models.IntegerField()
                            ),
                            models.FloatField()
                        ))
                    ),
                    default=models.Value(0),
                    output_field=models.FloatField()
                )
            ).filter(avg_score__lte=3)
        elif self.value() == '4-6':
            # Même logique avec les bornes adaptées
            return queryset.filter(
                stabilite_politique__gte=4, stabilite_politique__lte=6
            )
        elif self.value() == '7-10':
            return queryset.filter(
                stabilite_politique__gte=7, stabilite_politique__lte=10
            )
        return queryset

@admin.register(Geopolitics)
class GeopoliticsAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'average_score_display', 'stabilite_politique',
        'etat_droit', 'data_preview', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_filter = [ScoreRangeFilter] + AcheteurLinkedModelAdmin.list_filter
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('acheteur',)
        }),
        (_('Indicateurs géopolitiques'), {
            'fields': (
                'stabilite_politique', 'etat_droit', 'efficacite',
                'qualite', 'liberte_expression'
            ),
            'classes': ('wide',)
        }),
        (_('Données'), {
            'fields': ('donnees_politiques', 'donnees_economiques'),
            'classes': ('wide',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def average_score_display(self, obj):
        avg_score = obj.get_average_score()
        if avg_score >= 7:
            color = 'green'
            niveau = 'Élevé'
        elif avg_score >= 4:
            color = 'orange'
            niveau = 'Moyen'
        else:
            color = 'red'
            niveau = 'Faible'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({}/10)</span>',
            color, niveau, avg_score
        )
    average_score_display.short_description = _('Score moyen')
    
    def data_preview(self, obj):
        if obj.donnees_politiques:
            preview = obj.donnees_politiques[:60]
            if len(obj.donnees_politiques) > 60:
                preview += "..."
            return preview
        elif obj.donnees_economiques:
            preview = obj.donnees_economiques[:60]
            if len(obj.donnees_economiques) > 60:
                preview += "..."
            return preview
        return "-"
    data_preview.short_description = _('Données')
    
    actions = ['calculate_average_scores', 'export_geopolitics_data']

# ================ SCORING ================

class ScoringYearFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les années de scoring"""
    title = _('Année')
    parameter_name = 'year'
    
    def lookups(self, request, model_admin):
        # Récupérer les années disponibles
        years = Scoring.objects.values_list('annee__annee', flat=True).distinct().order_by('-annee__annee')
        return [(str(year), str(year)) for year in years]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(annee__annee=self.value())
        return queryset

@admin.register(Scoring)
class ScoringAdmin(SafeDeleteAdmin, SimpleHistoryAdmin):
    list_display = [
        'acheteur', 'annee', 'score_display', 'commentaire_preview',
        'created_by', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    list_display_links = ['acheteur', 'annee']
    list_filter = [
        ScoringYearFilter, 'acheteur', 'annee',
        ('created_at', admin.DateFieldListFilter),
        'created_by', 'updated_by',
    ] + list(SafeDeleteAdmin.list_filter)
    
    search_fields = [
        'acheteur__nom', 'acheteur__code', 'score', 'commentaire',
        'annee__annee', 'created_by__username'
    ]
    
    list_select_related = ['acheteur', 'annee', 'created_by', 'updated_by']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    raw_id_fields = ['acheteur', 'annee', 'created_by', 'updated_by']
    autocomplete_fields = ['acheteur', 'annee']
    ordering = ['-annee__annee', 'acheteur__nom']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Informations de scoring'), {
            'fields': ('acheteur', 'annee', 'score')
        }),
        (_('Commentaire'), {
            'fields': ('commentaire',),
            'classes': ('wide',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def score_display(self, obj):
        if obj.score:
            try:
                score_int = int(obj.score)
                if score_int >= 7:
                    color = 'green'
                elif score_int >= 5:
                    color = 'orange'
                else:
                    color = 'red'
                return format_html(
                    '<span style="color: {}; font-weight: bold;">{}/10</span>',
                    color, obj.score
                )
            except ValueError:
                return obj.score
        return "-"
    score_display.short_description = _('Score')
    score_display.admin_order_field = 'score'
    
    def commentaire_preview(self, obj):
        if obj.commentaire:
            preview = obj.commentaire[:80]
            if len(obj.commentaire) > 80:
                preview += "..."
            return preview
        return "-"
    commentaire_preview.short_description = _('Commentaire')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvel objet
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['calculate_average_scores', 'export_scoring_data', 'update_scores']
    
    @admin.action(description=_('Calculer scores moyens par année'))
    def calculate_average_scores(self, request, queryset):
        from django.db.models import Avg, Count
        
        # Grouper par année et calculer la moyenne
        stats = queryset.values('annee__annee').annotate(
            avg_score=Avg('score'),
            count=Count('id')
        ).order_by('-annee__annee')
        
        results = []
        for stat in stats:
            results.append(f"{stat['annee__annee']}: {stat['avg_score']:.1f} ({stat['count']} scores)")
        
        if results:
            self.message_user(
                request,
                f"Moyennes par année: {' | '.join(results)}",
                messages.INFO
            )
        else:
            self.message_user(request, "Aucune donnée à analyser.", messages.WARNING)

# ================ BANQUIER ================

@admin.register(Banquier)
class BanquierAdmin(AcheteurLinkedModelAdmin):
    list_display = [
        'acheteur', 'nom_banque', 'type_relation', 'numero_compte',
        'ville', 'created_at'
    ] + list(SafeDeleteAdmin.list_display)
    
    search_fields = AcheteurLinkedModelAdmin.search_fields + [
        'nom_banque', 'numero_compte', 'type_relation',
        'numero', 'rue', 'code_postal', 'commentaire'
    ]
    list_select_related = AcheteurLinkedModelAdmin.list_select_related + ['ville', 'couleur_commentaire']
    
    fieldsets = (
        (_('Informations bancaires'), {
            'fields': ('acheteur', 'nom_banque', 'numero_compte', 'type_relation')
        }),
        (_('Adresse bancaire'), {
            'fields': ('numero', 'rue', 'ville', 'code_postal'),
            'classes': ('collapse',)
        }),
        (_('Commentaire'), {
            'fields': ('couleur_commentaire', 'commentaire'),
            'classes': ('wide',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    raw_id_fields = AcheteurLinkedModelAdmin.raw_id_fields + ['ville', 'couleur_commentaire']
    autocomplete_fields = AcheteurLinkedModelAdmin.autocomplete_fields + ['ville', 'couleur_commentaire']
    
    actions = ['export_banking_data', 'merge_duplicate_banks']
    
    @admin.action(description=_('Exporter données bancaires'))
    def export_banking_data(self, request, queryset):
        count = queryset.count()
        self.message_user(
            request,
            f'Prêt à exporter {count} entrées bancaires.',
            messages.INFO
        )
        
        
        
        


# =============================================================================
# BILAN CLASSIQUE
# =============================================================================

@admin.register(ActifC)
class ActifCAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'total_I', 'total_II', 'total_III', 'general_total', 'created_at']
    list_filter = ['acheteur', 'annee', 'created_at']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['total_I', 'total_II', 'total_III', 'general_total', 'elements_incorporels', 
                      'elements_corporels', 'elements_financiers', 'stocks', 'creances', 
                      'disponibilites_vmp', 'compte_regul', 'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee')
        }),
        ('Actif Immobilisé', {
            'fields': ('capital_souscrit_non_app', 'frais_recherche_developpement', 
                      'brevet_licence_logiciels', 'fonds_commercial', 
                      'autres_immobilisations_incorporelles', 'terrains', 'constructions',
                      'materiels_et_outils', 'materiel_de_transport', 'autres_immos_corp',
                      'immos_en_cours', 'avances_et_acptes', 'participations', 'prets', 'autres')
        }),
        ('Actif Circulant', {
            'fields': ('stocks_mp', 'stocks_encours_mp', 'stocks_pf', 'stocks_encours_pf',
                      'stocks_encours_services', 'stocks_mses', 'avances_acptes_verses',
                      'clients_et_cptes_rattaches', 'autres_creances', 'valeurs_a_encaisser',
                      'banques_cheques_postaux_caisse')
        }),
        ('Comptes de Régularisation', {
            'fields': ('cca',)
        }),
        ('Autres éléments', {
            'fields': ('charges_a_repartir_et_frais_etablissement', 'primes_de_rbt', 'eca',
                      'eene', 'effectif', 'amortissements', 'provisions_stocks',
                      'provisions_creances', 'provisions_vmp')
        }),
        ('Calculs automatiques', {
            'fields': ('elements_incorporels', 'elements_corporels', 'elements_financiers',
                      'total_I', 'stocks', 'creances', 'disponibilites_vmp', 'total_II',
                      'compte_regul', 'total_III', 'general_total')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PassifC)
class PassifCAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'total_I', 'total_II', 'total_III', 'total_IV', 'total_general']
    list_filter = ['acheteur', 'annee', 'created_at']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['total_I', 'total_II', 'total_III', 'total_IV', 'total_general', 
                      'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee')
        }),
        ('Capitaux Propres', {
            'fields': ('capital_social', 'primes', 'ecarts_de_reevaluation', 'reserve',
                      'report_a_nouveau', 'resultat_exercice', 'subv_invest', 'provision_regl')
        }),
        ('Dettes Financières', {
            'fields': ('emprunts', 'dette_credit_bail_contrat_assimile', 
                      'dettes_financiere_diverses', 'provision_financiere_risque_charge')
        }),
        ('Dettes Circulantes', {
            'fields': ('dettes_fournisseurs_divers', 'avance_et_acomptes_recu', 'dettes',
                      'dettes_fiscales_sociales', 'autres_dettes', 'banques_credit_escompte',
                      'banque_credit_caisse', 'banques_decouvert')
        }),
        ('Comptes de Régularisation', {
            'fields': ('ecart_conversion_passif',)
        }),
        ('Calculs automatiques', {
            'fields': ('total_I', 'total_II', 'total_III', 'total_IV', 'total_general')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ResultatC)
class ResultatCAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'ca', 'resultat_exploitation', 'resultat_exercice']
    list_filter = ['acheteur', 'annee', 'created_at']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['ca', 'marge_brute', 'valeur_ajoutee', 'excedent_brut_ex', 
                      'resultat_exploitation', 'resultat_financier', 
                      'resultat_courant_avant_impots', 'resultat_excep', 'resultat_exercice',
                      'total_I', 'financier_total_I', 'financier_total_II', 
                      'excep_total_I', 'excep_total_II', 'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee')
        }),
        ('Produits', {
            'fields': ('vente_de_mdses', 'ventes_de_produits_fabriques', 
                      'travaux_services_vendus', 'produit_accessoires', 
                      'production_imblise', 'subventions_exploitations',
                      'production_stockee', 'reprises_de_provision', 
                      'transferts_charges', 'autres_produits')
        }),
        ('Charges', {
            'fields': ('achat_mdses', 'variation_stock_mdses', 'achat_mp_autres_appro',
                      'var_stk_mp_app', 'autres_achats', 
                      'variation_de_stocks_autres_appro', 'transports', 'services_ext',
                      'impots_taxes', 'autres_charges_valeur_ajoutee', 'charges_personnel',
                      'dotation_aux_amorts', 'dotation_aux_provisions',
                      'autres_charges_excedent_brute')
        }),
        ('Produits Financiers', {
            'fields': ('revenus_fin_assimiles', 'prof_vmp_et_cre_actif_immo',
                      'interets_produit_assim', 'reprise_prov_et_transfert',
                      'diff_positive_de_change', 'prod_nets_cessions_vmp')
        }),
        ('Charges Financières', {
            'fields': ('dap', 'frais_fin_charges_assi', 'diff_negatives_de_change',
                      'ch_nettes_cessions_vmp')
        }),
        ('Produits Exceptionnels', {
            'fields': ('sur_op_gestion_prod_except', 'sur_op_en_capital_prod_except',
                      'reprise_prov_transfert')
        }),
        ('Charges Exceptionnelles', {
            'fields': ('sur_op_gestion_charg_except', 'sur_op_en_capital_charg_except',
                      'dap_et_transfert_charg_except')
        }),
        ('Autres éléments', {
            'fields': ('participation_salairies', 'impot_sur_benefices')
        }),
        ('Calculs automatiques', {
            'fields': ('ca', 'marge_brute', 'valeur_ajoutee', 'excedent_brut_ex',
                      'resultat_exploitation', 'financier_total_I', 'financier_total_II',
                      'resultat_financier', 'resultat_courant_avant_impots',
                      'excep_total_I', 'excep_total_II', 'resultat_excep',
                      'resultat_exercice')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# BILAN BANCAIRE
# =============================================================================

@admin.register(Assets)
class AssetsAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'semestre', 'total_assets', 'pret_interbancaire', 'creance_sur_la_clientele']
    list_filter = ['acheteur', 'annee', 'type_bilan', 'semestre']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['pret_interbancaire', 'a_vue', 'creance_sur_la_clientele', 
                      'porteuille_papier_commercial', 'autres_concours_clients', 
                      'total_assets', 'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee', 'type_bilan', 'semestre')
        }),
        ('Trésorerie', {
            'fields': ('caisse',)
        }),
        ('Prêts interbancaires - A vue', {
            'fields': ('banques_centrales', 'tresorerie_cpp', 'autres_ets_credit')
        }),
        ('Prêts interbancaires - A terme', {
            'fields': ('a_terme',)
        }),
        ('Portefeuille papier commercial', {
            'fields': ('credits_campagne', 'credits_ordinaire')
        }),
        ('Autres concours clients', {
            'fields': ('credits_campagne_acc', 'credits_ordinaire_acc')
        }),
        ('Autres créances', {
            'fields': ('creances_ordinaires', 'affacturage')
        }),
        ('Autres actifs', {
            'fields': ('titres_placement', 'immobilisation_fin', 'operation_credit_bail',
                      'immobilisation_incorporelle', 'immobilisation_corporelle',
                      'actionnaire_ou_associe', 'autres_actifs', 'comptes_commande_divers')
        }),
        ('Calculs automatiques', {
            'fields': ('a_vue', 'pret_interbancaire', 'porteuille_papier_commercial',
                      'autres_concours_clients', 'creance_sur_la_clientele', 'total_assets')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Liabilities)
class LiabilitiesAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'semestre', 'total_liabilities', 'dette_interbancaire', 'dette_envers_clientelle']
    list_filter = ['acheteur', 'annee', 'type_bilan', 'semestre']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['a_vue', 'dette_interbancaire', 'dette_envers_clientelle', 
                      'total_liabilities', 'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee', 'type_bilan', 'semestre')
        }),
        ('Dettes interbancaires - A vue', {
            'fields': ('tresorerie_ccp', 'autres_etablissement_credit')
        }),
        ('Dettes interbancaires - A terme', {
            'fields': ('a_terme',)
        }),
        ('Dettes envers la clientèle', {
            'fields': ('comptes_epargne_court_terme', 'comptes_epargne_terme', 
                      'bons_caisse', 'autres_dette_a_vue', 'autres_dette_a_terme')
        }),
        ('Autres passifs', {
            'fields': ('titres_creance_autres_dettes', 'compte_dordre_divers',
                      'provision_pour_risque_charge', 'provision_reglementee',
                      'emprunt_subordonne_tire_emis', 'subventions_investissement',
                      'fonds_affecte', 'fonds_pour_risque_bancaire_generaux')
        }),
        ('Capitaux propres', {
            'fields': ('capital_ou_dotation', 'primes_liees_reserve_capital',
                      'ecarts_reevaluation', 'benefices_non_distribue',
                      'resultat_net_exercie')
        }),
        ('Calculs automatiques', {
            'fields': ('a_vue', 'dette_interbancaire', 'dette_envers_clientelle', 'total_liabilities')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Expenses)
class ExpensesAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'semestre', 'total_des_charges', 'interet_charges_assimilee', 'frais_generaux_dexploitation']
    list_filter = ['acheteur', 'annee', 'type_bilan', 'semestre']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['interet_charges_assimilee', 'charge_sur_operation_financiere',
                      'prestation', 'frais_generaux_dexploitation', 'total_des_charges',
                      'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee', 'type_bilan', 'semestre')
        }),
        ('Intérêts et charges assimilées', {
            'fields': ('interet_charges_assimilee_dette_interbancaire',
                      'interet_charge_assimilee_dette_clientele',
                      'interet_charge_assimilee_titre_creance',
                      'chargesc_compte_bloque_dactionnaire_emprunt_sub',
                      'autres_interets_charges_assimilee')
        }),
        ('Charges sur opérations financières', {
            'fields': ('charges_sur_op_credit_bail_assimile', 'commissions',
                      'charges_sur_titre_placement', 'charges_sur_operation_change',
                      'charges_sur_operation_hors_bilan')
        }),
        ('Coût des marchandises vendues', {
            'fields': ('achat_marchandises', 'stocks_vendus', 'variations_stocks_marchanides')
        }),
        ('Frais généraux d\'exploitation', {
            'fields': ('frais_divers_exploitation_bancaire', 'frais_personnel',
                      'autres_frais_generaux')
        }),
        ('Autres charges', {
            'fields': ('dotations_amortissement_provision_immobilisation',
                      'solde_perte_creance_hors_bilan',
                      'excedent_dotation_reprises_fonds_pour_risque_bancaire_generaux',
                      'charges_exceptionnelle', 'pertes_exercice_anterieurs',
                      'impot_sur_revenu')
        }),
        ('Calculs automatiques', {
            'fields': ('interet_charges_assimilee', 'charge_sur_operation_financiere',
                      'prestation', 'frais_generaux_dexploitation', 'total_des_charges')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'semestre', 'total_produit', 'interet_produit_assimile', 'revenu_d_operation_financiere']
    list_filter = ['acheteur', 'annee', 'type_bilan', 'semestre']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['interet_produit_assimile', 'revenu_d_operation_financiere',
                      'autres_produits_exploitation', 'total_produit',
                      'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee', 'type_bilan', 'semestre')
        }),
        ('Intérêts et produits assimilés', {
            'fields': ('interets_produit_assimile_sur_pret_avance_interbancaire',
                      'ineterets_produit_assimile_pret_avance_clientele',
                      'interet_produit_sur_titre_dinvestissement',
                      'revenu_gains_titre_pret_titre_subordonne',
                      'autres_interets_produits_assimiles')
        }),
        ('Revenus d\'opérations financières', {
            'fields': ('produits_leansing_operation_connexes', 'commissions',
                      'revenus_titre_negociable', 'dividendes_produits_assimiles',
                      'revenus_operation_de_change', 'produits_opeations_hors_bilan')
        }),
        ('Autres produits d\'exploitation', {
            'fields': ('produits_bancaire_divers', 'marges_vente', 'ventes_marchandises',
                      'variation_stocks_marchandises', 'produit_dexploitation_generale')
        }),
        ('Autres produits', {
            'fields': ('reprise_damortissement_provisions_sur_immobilisation',
                      'solde_resultat_correction_valeur_sur_creance_hors_bilan',
                      'excedent_reprise_fonds_pour_risque_bancaire_generaux',
                      'produits_exceptionnels', 'benefice_sur_exercice_anterieur',
                      'perte')
        }),
        ('Calculs automatiques', {
            'fields': ('interet_produit_assimile', 'revenu_d_operation_financiere',
                      'autres_produits_exploitation', 'total_produit')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(OffBalanceSheet)
class OffBalanceSheetAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'semestre', 'total_engagements_donnes', 'total_engagements_recus']
    list_filter = ['acheteur', 'annee', 'type_bilan', 'semestre']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['total_engagement_financement_donne', 'total_engagement_garantie_donne',
                      'total_engagements_donnes', 'total_engagement_financement_recu',
                      'total_engagements_recus', 'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee', 'type_bilan', 'semestre')
        }),
        ('Engagements donnés - Financement', {
            'fields': ('engagement_financement_donne_ets_credit',
                      'engagement_financement_donne_clientele',
                      'en_faveur_des_ets_credit', 'en_faveur_clientele')
        }),
        ('Engagements donnés - Garantie', {
            'fields': ('engagement_garantie_donne_ets_credit',
                      'engagement_garantie_donne_clientele',
                      'pour_compte_ets_credit', 'pour_compte_clientele')
        }),
        ('Engagements donnés - Titres', {
            'fields': ('engagement_sur_titres_donnes', 'engagement_sur_titre')
        }),
        ('Engagements reçus - Financement', {
            'fields': ('engagement_financement_recu_ets_credit',
                      'engagement_financement_recu_clientele',
                      'recu_ets_credit', 'recu_clientele')
        }),
        ('Engagements reçus - Autres', {
            'fields': ('engagement_garantie_recu_ets_credit',
                      'engagement_sur_titres_recus', 'recu_ets_credit2',
                      'engagement_sur_titre2')
        }),
        ('Calculs automatiques', {
            'fields': ('total_engagement_financement_donne', 'total_engagement_garantie_donne',
                      'total_engagements_donnes', 'total_engagement_financement_recu',
                      'total_engagements_recus')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# BILAN SYSCOHADA
# =============================================================================

@admin.register(ActifS)
class ActifSAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'total_actif_immobilise', 'total_actif_circulant', 'total_actif']
    list_filter = ['acheteur', 'annee']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['immobilisations_incorporelles', 'immobilisations_corporelles',
                      'immobilisations_financieres', 'total_actif_immobilise',
                      'creances_emplois_similaires', 'total_tresorerie_equivalents',
                      'total_actif_circulant', 'total_actif', 'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee')
        }),
        ('Immobilisations incorporelles', {
            'fields': ('frais_developpement_prospection', 'brevets_licences_logiciels',
                      'droits_propriete_commerciale_baux', 'autres_immo_incorporelles')
        }),
        ('Immobilisations corporelles', {
            'fields': ('terrains', 'dons_investissements_net', 'batiments',
                      'agencements_amenagements_installations',
                      'materiel_mobilier_actif_biologiques', 'materiel_transport')
        }),
        ('Immobilisations financières', {
            'fields': ('titres_participation', 'autres_immobilisations_financieres')
        }),
        ('Avances et acomptes', {
            'fields': ('avances_acompte_immobilisations',)
        }),
        ('Actif circulant', {
            'fields': ('actif_circulant_hao', 'stock_encours', 'fournisseurs_avances_versee',
                      'clients', 'autres_creances')
        }),
        ('Trésorerie', {
            'fields': ('valeurs_mobilieres_placement', 'disponibilites',
                      'banque_cheque_postal_caisse_assimiles')
        }),
        ('Écart de conversion', {
            'fields': ('ecart_conversion_actif',)
        }),
        ('Calculs automatiques', {
            'fields': ('immobilisations_incorporelles', 'immobilisations_corporelles',
                      'immobilisations_financieres', 'total_actif_immobilise',
                      'creances_emplois_similaires', 'total_tresorerie_equivalents',
                      'total_actif_circulant', 'total_actif')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PassifS)
class PassifSAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'total_capitaux_propres_ressources_similaires', 'total_passifs_courants', 'total_passifs']
    list_filter = ['acheteur', 'annee']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['total_capitaux_propres_ressources_similaires',
                      'total_dettes_financieres_ressources_similaires',
                      'total_ressources_stables', 'total_passifs_courants',
                      'total_tresorerie_equivalents', 'total_passifs',
                      'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee')
        }),
        ('Capitaux propres et ressources assimilées', {
            'fields': ('capital', 'capital_non_appele_apporteurs',
                      'primes_liees_capital_social', 'ecart_reevaluation',
                      'reserves_indisponibles', 'reserves_libres', 'report_nouveau',
                      'resultat_net_exercice', 'subventions_investissements',
                      'provisions_reglees')
        }),
        ('Dettes financières', {
            'fields': ('emprunts_dettes_financieres_diverse', 'dettes_location_vente',
                      'provisions_risques_charges')
        }),
        ('Passifs courants', {
            'fields': ('passif_circulant_hao', 'clients_avances_recues',
                      'fournisseurs_exploitation', 'dettes_fiscales_sociales',
                      'autres_dettes', 'provisions_risques_court_terme')
        }),
        ('Trésorerie', {
            'fields': ('banques_credit_escompte',
                      'banques_etablissements_financiers_credit_caisse')
        }),
        ('Écart de conversion', {
            'fields': ('ecart_conversion_passif',)
        }),
        ('Calculs automatiques', {
            'fields': ('total_capitaux_propres_ressources_similaires',
                      'total_dettes_financieres_ressources_similaires',
                      'total_ressources_stables', 'total_passifs_courants',
                      'total_tresorerie_equivalents', 'total_passifs')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ResultatS)
class ResultatSAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'chiffre_affaires', 'resultat_net', 'marge_commerciale']
    list_filter = ['acheteur', 'annee']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['marge_commerciale', 'chiffre_affaires', 'valeur_ajoutee',
                      'excedent_brute_exploitation', 'resultat_exploitation',
                      'resultat_financier', 'resultat_activites_ordinaires_xe',
                      'resultat_activites_ordinaires_tn', 'resultat_net',
                      'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee')
        }),
        ('Ventes', {
            'fields': ('ventes_marchandises_a', 'ventes_produits_manufactures',
                      'travaux_services_vendus_c', 'produits_accessoires_d')
        }),
        ('Achats et stocks', {
            'fields': ('achats_marchandises', 'variation_stock_marchandises',
                      'achats_matieres_premieres_fournitures_connexes',
                      'variation_stock_matieres_premieres_fournitures_connexes',
                      'autres_achats', 'variation_stock_autres_fournitures')
        }),
        ('Autres produits', {
            'fields': ('production_stockee', 'production_immobilisee',
                      'subvention_exploitation', 'autres_produits',
                      'transfert_charges_exploitation')
        }),
        ('Charges d\'exploitation', {
            'fields': ('transport', 'services_exterieurs', 'impots_taxes',
                      'autres_depenses', 'frais_personnel')
        }),
        ('Reprises de dépréciations', {
            'fields': ('reprise_depreciations_amortissements_provision_pertes_valeurs_p',
                      'reprise_depreciations_amortissements_provision_pertes_valeurs_m')
        }),
        ('Résultat financier', {
            'fields': ('produits_financiers_assimiles', 'reprise_provision_perte_valeur',
                      'transfert_charges_financieres', 'charges_financieres_assimilees',
                      'dotations_provisions_depreciations_financieres')
        }),
        ('Résultat HAO', {
            'fields': ('produits_cession_immobilisations', 'autres_produits_hao',
                      'valeur_comptable_cessions_actifs_immobilises', 'autres_charges_hao')
        }),
        ('Résultat net', {
            'fields': ('participation_travailleurs', 'charge_impot_revenu')
        }),
        ('Calculs automatiques', {
            'fields': ('marge_commerciale', 'chiffre_affaires', 'valeur_ajoutee',
                      'excedent_brute_exploitation', 'resultat_exploitation',
                      'resultat_financier', 'resultat_activites_ordinaires_xe',
                      'resultat_activites_ordinaires_tn', 'resultat_net')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# BILAN IFRS
# =============================================================================

@admin.register(ActifIFRS)
class ActifIFRSAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'semestre', 'total_actif_non_courant', 'total_actif_courant', 'total_actif']
    list_filter = ['acheteur', 'annee', 'type_bilan', 'semestre']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['total_actif_non_courant', 'total_actif_courant', 'total_actif',
                      'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee', 'type_bilan', 'semestre')
        }),
        ('Actif non courant - Immobilisations incorporelles', {
            'fields': ('goodwill', 'marques_et_droits_auteur', 'brevets_et_licences',
                      'autres_immobilisations_incorporelles')
        }),
        ('Actif non courant - Immobilisations corporelles', {
            'fields': ('terrains', 'batiments', 'materiel_et_equipement')
        }),
        ('Actif non courant - Immobilisations financières', {
            'fields': ('participations_dans_des_societes', 'prets_a_long_terme')
        }),
        ('Actif courant - Stocks', {
            'fields': ('matieres_premieres', 'produits_finis')
        }),
        ('Actif courant - Créances', {
            'fields': ('creances_a_court_terme', 'avances_et_acomptes', 'creances_diverses')
        }),
        ('Actif courant - Trésorerie', {
            'fields': ('disponibilites_bancaires',)
        }),
        ('Calculs automatiques', {
            'fields': ('total_actif_non_courant', 'total_actif_courant', 'total_actif')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PassifIFRS)
class PassifIFRSAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'semestre', 'total_capitaux_propres', 'total_passif_courant', 'total_passif']
    list_filter = ['acheteur', 'annee', 'type_bilan', 'semestre']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['total_capitaux_propres', 'total_passif_non_courant',
                      'total_passif_courant', 'total_passif', 'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee', 'type_bilan', 'semestre')
        }),
        ('Capitaux propres', {
            'fields': ('capital_social', 'primes_emission', 'reserves_legales',
                      'reserves_statutaires', 'reserves_facultatives', 'autres_reserves',
                      'resultat_net_reporte')
        }),
        ('Passif non courant', {
            'fields': ('emprunts_bancaires_long_terme', 'obligations',
                      'provisions_pour_retraites_et_pensions', 'autres_provisions')
        }),
        ('Passif courant', {
            'fields': ('dettes_fournisseurs_a_court_terme', 'impots_sur_le_revenu',
                      'cotisations_sociales', 'emprunts_bancaires_court_terme',
                      'dettes_diverses', 'dividendes_a_payer')
        }),
        ('Calculs automatiques', {
            'fields': ('total_capitaux_propres', 'total_passif_non_courant',
                      'total_passif_courant', 'total_passif')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ResultatIFRS)
class ResultatIFRSAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'annee', 'semestre', 'chiffre_affaires', 'resultat_net', 'resultat_operationnel']
    list_filter = ['acheteur', 'annee', 'type_bilan', 'semestre']
    search_fields = ['acheteur__nom', 'annee__annee']
    readonly_fields = ['chiffre_affaires', 'autres_produits_operationnels', 'total_produits',
                      'cout_des_ventes', 'charges_operationnelles', 
                      'amortissements_et_provisions', 'total_charges',
                      'resultat_operationnel', 'resultat_financier', 
                      'resultat_avant_impot', 'resultat_net', 'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'annee', 'type_bilan', 'semestre')
        }),
        ('Produits', {
            'fields': ('ventes_biens', 'ventes_services', 'subventions_exploitation',
                      'revenus_exceptionnels', 'revenus_financiers')
        }),
        ('Charges', {
            'fields': ('achats_matieres_premieres', 'autres_couts_directs',
                      'salaires_et_charges_sociales', 'loyer_et_charges_locatives',
                      'autres_charges_exploitation', 'amortissement_des_immobilisations',
                      'provisions_pour_risques_et_charges', 'charges_financieres',
                      'impot_sur_les_societes')
        }),
        ('Calculs automatiques', {
            'fields': ('chiffre_affaires', 'autres_produits_operationnels', 'total_produits',
                      'cout_des_ventes', 'charges_operationnelles', 
                      'amortissements_et_provisions', 'total_charges',
                      'resultat_operationnel', 'resultat_financier', 
                      'resultat_avant_impot', 'resultat_net')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


   
    
    

from django.shortcuts import redirect
import re

@admin.register(Logo)
class LogoAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'preview_image', 'created_at']
    list_filter = ['acheteur', 'created_at']
    search_fields = ['acheteur__nom', 'description']
    readonly_fields = ['preview_image', 'created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur',)
        }),
        ('Logo', {
            'fields': ('image', 'preview_image', 'description')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 200px;" />', obj.image.url)
        return "-"
    preview_image.short_description = "Aperçu"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Optimiser les requêtes
        return qs.select_related('acheteur')
    
    def save_model(self, request, obj, form, change):
        # Vérifier qu'un seul logo existe par acheteur
        if not change:
            existing_logo = Logo.objects.filter(acheteur=obj.acheteur).first()
            if existing_logo:
                messages.warning(request, f"Un logo existe déjà pour {obj.acheteur.nom}. Il sera remplacé.")
        super().save_model(request, obj, form, change)


@admin.register(TelephoneAcheteur)
class TelephoneAcheteurAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'formatted_telephone', 'call_link', 'created_at']
    list_filter = ['acheteur', 'created_at']
    search_fields = ['acheteur__nom', 'telephone']
    readonly_fields = ['formatted_telephone', 'call_link_display', 'created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'telephone')
        }),
        ('Informations formatées', {
            'fields': ('formatted_telephone', 'call_link_display')
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def formatted_telephone(self, obj):
        return obj.get_formatted_number()
    formatted_telephone.short_description = "Téléphone formaté"
    
    def call_link(self, obj):
        link = obj.get_call_link()
        return format_html('<a href="{}" target="_blank">📞 Appeler</a>', link) if link else "-"
    call_link.short_description = "Appeler"
    
    def call_link_display(self, obj):
        link = obj.get_call_link()
        return format_html('<a href="{}" class="button" target="_blank">📞 Appeler ce numéro</a>', link) if link else "-"
    call_link_display.short_description = "Lien d'appel"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Nettoyer le numéro de téléphone
        if obj.telephone:
            obj.telephone = obj.telephone.strip()
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')


@admin.register(AdresseAcheteur)
class AdresseAcheteurAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'short_adresse', 'created_at']
    list_filter = ['acheteur', 'created_at']
    search_fields = ['acheteur__nom', 'adresse']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'adresse')
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def short_adresse(self, obj):
        if obj.adresse:
            if len(obj.adresse) > 50:
                return obj.adresse[:50] + "..."
        return obj.adresse or "-"
    short_adresse.short_description = "Adresse"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Nettoyer l'adresse
        if obj.adresse:
            obj.adresse = ' '.join(obj.adresse.split())  # Supprimer les espaces multiples
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')


@admin.register(PortableAcheteur)
class PortableAcheteurAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'formatted_portable', 'call_link', 'whatsapp_link', 'created_at']
    list_filter = ['acheteur', 'created_at']
    search_fields = ['acheteur__nom', 'portable']
    readonly_fields = ['formatted_portable', 'call_link_display', 'whatsapp_link_display', 
                      'created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'portable')
        }),
        ('Informations formatées', {
            'fields': ('formatted_portable', 'call_link_display', 'whatsapp_link_display')
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def formatted_portable(self, obj):
        return obj.get_formatted_number()
    formatted_portable.short_description = "Portable formaté"
    
    def call_link(self, obj):
        link = obj.get_call_link()
        return format_html('<a href="{}" target="_blank">📞 Appeler</a>', link) if link else "-"
    call_link.short_description = "Appeler"
    
    def whatsapp_link(self, obj):
        link = obj.get_whatsapp_link()
        return format_html('<a href="{}" target="_blank">💬 WhatsApp</a>', link) if link else "-"
    whatsapp_link.short_description = "WhatsApp"
    
    def call_link_display(self, obj):
        link = obj.get_call_link()
        return format_html('<a href="{}" class="button" target="_blank">📞 Appeler ce portable</a>', link) if link else "-"
    call_link_display.short_description = "Lien d'appel"
    
    def whatsapp_link_display(self, obj):
        link = obj.get_whatsapp_link()
        return format_html('<a href="{}" class="button" target="_blank" style="background-color: #25D366; color: white;">💬 Ouvrir WhatsApp</a>', link) if link else "-"
    whatsapp_link_display.short_description = "Lien WhatsApp"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Nettoyer le numéro de portable
        if obj.portable:
            obj.portable = obj.portable.strip()
        
        # Valider avant de sauvegarder
        try:
            obj.full_clean()
        except ValidationError as e:
            # Afficher les erreurs dans l'admin
            messages.error(request, f"Erreur de validation : {e}")
            return
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ajouter une aide au format
        form.base_fields['portable'].help_text = "Format accepté : +241 XX XX XX XX ou 0X XX XX XX (minimum 8 chiffres)"
        return form


@admin.register(EmailAcheteur)
class EmailAcheteurAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'display_email', 'mail_link', 'created_at']
    list_filter = ['acheteur', 'created_at']
    search_fields = ['acheteur__nom', 'email']
    readonly_fields = ['display_email_field', 'mail_link_display', 'created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'email')
        }),
        ('Informations formatées', {
            'fields': ('display_email_field', 'mail_link_display')
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def display_email(self, obj):
        return obj.get_display_email()
    display_email.short_description = "Email"
    
    def mail_link(self, obj):
        link = obj.get_mailto_link()
        return format_html('<a href="{}" target="_blank">📧 Envoyer</a>', link) if link else "-"
    mail_link.short_description = "Envoyer"
    
    def display_email_field(self, obj):
        return obj.get_display_email()
    display_email_field.short_description = "Email formaté"
    
    def mail_link_display(self, obj):
        link = obj.get_mailto_link()
        return format_html('<a href="{}" class="button" target="_blank">📧 Envoyer un email</a>', link) if link else "-"
    mail_link_display.short_description = "Lien email"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Normaliser l'email
        if obj.email:
            obj.email = obj.email.strip().lower()
        
        # Valider avant de sauvegarder
        try:
            obj.full_clean()
        except ValidationError as e:
            # Afficher les erreurs dans l'admin
            messages.error(request, f"Erreur de validation : {e}")
            return
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'titre', 'file_preview', 'created_at']
    list_filter = ['acheteur', 'created_at']
    search_fields = ['acheteur__nom', 'titre', 'description']
    readonly_fields = ['file_preview_field', 'file_size', 'file_type', 'created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'titre', 'description')
        }),
        ('Fichier', {
            'fields': ('fichier', 'file_preview_field', 'file_size', 'file_type')
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def file_preview(self, obj):
        if obj.fichier:
            filename = obj.fichier.name.split('/')[-1]
            return format_html('<a href="{}" target="_blank">{}</a>', obj.fichier.url, filename[:30] + "..." if len(filename) > 30 else filename)
        return "-"
    file_preview.short_description = "Fichier"
    
    def file_preview_field(self, obj):
        if obj.fichier:
            filename = obj.fichier.name.split('/')[-1]
            return format_html(
                '<div style="margin: 10px 0;">'
                '<a href="{}" target="_blank" style="display: inline-block; padding: 10px; background: #f0f0f0; border-radius: 5px; margin-right: 10px;">'
                '📄 Télécharger</a>'
                '<span>{}</span>'
                '</div>',
                obj.fichier.url,
                filename
            )
        return "-"
    file_preview_field.short_description = "Prévisualisation"
    
    def file_size(self, obj):
        if obj.fichier:
            try:
                size = obj.fichier.size
                if size < 1024:
                    return f"{size} octets"
                elif size < 1024 * 1024:
                    return f"{size/1024:.1f} Ko"
                else:
                    return f"{size/(1024*1024):.1f} Mo"
            except:
                return "N/A"
        return "-"
    file_size.short_description = "Taille"
    
    def file_type(self, obj):
        if obj.fichier:
            ext = obj.fichier.name.split('.')[-1].lower() if '.' in obj.fichier.name else ''
            types = {
                'pdf': 'PDF',
                'doc': 'Word',
                'docx': 'Word',
                'xls': 'Excel',
                'xlsx': 'Excel',
                'jpg': 'Image',
                'jpeg': 'Image',
                'png': 'Image',
                'txt': 'Texte',
            }
            return types.get(ext, ext.upper() if ext else 'Inconnu')
        return "-"
    file_type.short_description = "Type"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')


@admin.register(Swot)
class SwotAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'forces_preview', 'faiblesses_preview', 'created_at']
    list_filter = ['acheteur', 'created_at']
    search_fields = ['acheteur__nom', 'forces', 'faiblesses', 'opportunites', 'menaces']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur',)
        }),
        ('Analyse SWOT', {
            'fields': ('forces', 'faiblesses', 'opportunites', 'menaces'),
            'classes': ('wide',)
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def forces_preview(self, obj):
        if obj.forces:
            if len(obj.forces) > 50:
                return obj.forces[:50] + "..."
        return obj.forces or "-"
    forces_preview.short_description = "Forces"
    
    def faiblesses_preview(self, obj):
        if obj.faiblesses:
            if len(obj.faiblesses) > 50:
                return obj.faiblesses[:50] + "..."
        return obj.faiblesses or "-"
    faiblesses_preview.short_description = "Faiblesses"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Augmenter la hauteur des zones de texte
        form.base_fields['forces'].widget.attrs['rows'] = 5
        form.base_fields['faiblesses'].widget.attrs['rows'] = 5
        form.base_fields['opportunites'].widget.attrs['rows'] = 5
        form.base_fields['menaces'].widget.attrs['rows'] = 5
        form.base_fields['forces'].widget.attrs['style'] = 'width: 95%;'
        form.base_fields['faiblesses'].widget.attrs['style'] = 'width: 95%;'
        form.base_fields['opportunites'].widget.attrs['style'] = 'width: 95%;'
        form.base_fields['menaces'].widget.attrs['style'] = 'width: 95%;'
        return form


# =============================================================================
# CUSTOM ACTIONS
# =============================================================================

def format_phone_numbers(modeladmin, request, queryset):
    """Action pour formater les numéros de téléphone"""
    for phone in queryset:
        if phone.telephone:
            # Nettoyer le numéro
            cleaned = re.sub(r'\D', '', phone.telephone)
            phone.telephone = cleaned
            phone.save()
    modeladmin.message_user(request, f"{queryset.count()} numéros formatés.")
format_phone_numbers.short_description = "Formater les numéros de téléphone"

def format_portable_numbers(modeladmin, request, queryset):
    """Action pour formater les numéros de portable"""
    for portable in queryset:
        if portable.portable:
            # Nettoyer le numéro
            cleaned = re.sub(r'\D', '', portable.portable)
            portable.portable = cleaned
            try:
                portable.full_clean()
                portable.save()
            except ValidationError as e:
                modeladmin.message_user(request, f"Erreur pour {portable.portable}: {e}", messages.ERROR)
    modeladmin.message_user(request, f"{queryset.count()} numéros de portable formatés.")
format_portable_numbers.short_description = "Formater les numéros de portable"

def normalize_emails(modeladmin, request, queryset):
    """Action pour normaliser les emails (minuscules, trim)"""
    for email in queryset:
        if email.email:
            email.email = email.email.strip().lower()
            try:
                email.full_clean()
                email.save()
            except ValidationError as e:
                modeladmin.message_user(request, f"Erreur pour {email.email}: {e}", messages.ERROR)
    modeladmin.message_user(request, f"{queryset.count()} emails normalisés.")
normalize_emails.short_description = "Normaliser les emails"

# Ajouter les actions aux modèles concernés
TelephoneAcheteurAdmin.actions = [format_phone_numbers]
PortableAcheteurAdmin.actions = [format_portable_numbers]
EmailAcheteurAdmin.actions = [normalize_emails]


# =============================================================================
# INLINES (pour intégrer dans l'admin d'Acheteur)
# =============================================================================

class TelephoneAcheteurInline(admin.TabularInline):
    model = TelephoneAcheteur
    extra = 1
    readonly_fields = ['formatted_telephone', 'call_link_display']
    fields = ['telephone', 'formatted_telephone', 'call_link_display']
    verbose_name = "Téléphone"
    verbose_name_plural = "Téléphones"

class PortableAcheteurInline(admin.TabularInline):
    model = PortableAcheteur
    extra = 1
    readonly_fields = ['formatted_portable', 'call_link_display', 'whatsapp_link_display']
    fields = ['portable', 'formatted_portable', 'call_link_display', 'whatsapp_link_display']
    verbose_name = "Portable"
    verbose_name_plural = "Portables"

class EmailAcheteurInline(admin.TabularInline):
    model = EmailAcheteur
    extra = 1
    readonly_fields = ['display_email_field', 'mail_link_display']
    fields = ['email', 'display_email_field', 'mail_link_display']
    verbose_name = "Email"
    verbose_name_plural = "Emails"

class AdresseAcheteurInline(admin.TabularInline):
    model = AdresseAcheteur
    extra = 1
    fields = ['adresse']
    verbose_name = "Adresse"
    verbose_name_plural = "Adresses"

class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1
    fields = ['titre', 'fichier', 'description']
    verbose_name = "Document"
    verbose_name_plural = "Documents"

class LogoInline(admin.TabularInline):
    model = Logo
    extra = 1
    fields = ['image', 'description']
    verbose_name = "Logo"
    verbose_name_plural = "Logo"

class SwotInline(admin.TabularInline):
    model = Swot
    extra = 1
    fields = ['forces', 'faiblesses', 'opportunites', 'menaces']
    verbose_name = "Analyse SWOT"
    verbose_name_plural = "Analyse SWOT"


# =============================================================================
# SITE HEADER PERSONNALISÉ
# =============================================================================

admin.site.site_header = "Gestion des Acheteurs"
admin.site.site_title = "Admin Acheteurs"
admin.site.index_title = "Administration"






@admin.register(ProduitService)
class ProduitServiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'produits_preview', 'services_preview', 'created_at']
    list_filter = ['acheteur', 'created_at']
    search_fields = ['acheteur__nom', 'produits', 'services']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur',)
        }),
        ('Produits et Services', {
            'fields': ('produits', 'services'),
            'classes': ('wide',)
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def produits_preview(self, obj):
        if obj.produits:
            if len(obj.produits) > 50:
                return obj.produits[:50] + "..."
        return obj.produits or "-"
    produits_preview.short_description = "Produits"
    
    def services_preview(self, obj):
        if obj.services:
            if len(obj.services) > 50:
                return obj.services[:50] + "..."
        return obj.services or "-"
    services_preview.short_description = "Services"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Nettoyer les textes
        if obj.produits:
            obj.produits = obj.produits.strip()
        if obj.services:
            obj.services = obj.services.strip()
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Augmenter la hauteur des zones de texte
        form.base_fields['produits'].widget.attrs['rows'] = 5
        form.base_fields['services'].widget.attrs['rows'] = 5
        form.base_fields['produits'].widget.attrs['style'] = 'width: 95%;'
        form.base_fields['services'].widget.attrs['style'] = 'width: 95%;'
        return form


@admin.register(Marque)
class MarqueAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'marques_preview', 'created_at']
    list_filter = ['acheteur', 'created_at']
    search_fields = ['acheteur__nom', 'marques']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur',)
        }),
        ('Marques', {
            'fields': ('marques',),
            'classes': ('wide',)
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def marques_preview(self, obj):
        if obj.marques:
            if len(obj.marques) > 50:
                return obj.marques[:50] + "..."
        return obj.marques or "-"
    marques_preview.short_description = "Marques"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Nettoyer les textes
        if obj.marques:
            obj.marques = obj.marques.strip()
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Augmenter la hauteur des zones de texte
        form.base_fields['marques'].widget.attrs['rows'] = 5
        form.base_fields['marques'].widget.attrs['style'] = 'width: 95%;'
        return form


@admin.register(ProcedureCollective)
class ProcedureCollectiveAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'type_procedure', 'date_ouverture', 
                    'date_cloture', 'status_display', 'montant_creance', 'created_at']
    list_filter = ['acheteur', 'type_procedure', 'date_ouverture', 'date_cloture']
    search_fields = ['acheteur__nom', 'type_procedure', 'tribunal', 
                     'numero_dossier', 'secteur_activite']
    readonly_fields = ['status_field', 'duree_procedure', 'created_at', 
                      'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'type_procedure', 'numero_dossier')
        }),
        ('Dates et tribunal', {
            'fields': ('date_ouverture', 'date_cloture', 'tribunal', 'status_field', 'duree_procedure')
        }),
        ('Informations complémentaires', {
            'fields': ('secteur_activite', 'montant_creance', 'description')
        }),
        ('Impact assureur', {
            'fields': ('impact_assureur',),
            'classes': ('wide',)
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def status_display(self, obj):
        if obj.date_cloture:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ Clôturée</span>'
            )
        elif obj.date_ouverture:
            now = timezone.now().date()
            if obj.date_ouverture > now:
                return format_html(
                    '<span style="color: orange; font-weight: bold;">⏳ À venir</span>'
                )
            else:
                return format_html(
                    '<span style="color: red; font-weight: bold;">⚠️ En cours</span>'
                )
        return "-"
    status_display.short_description = "Statut"
    
    def status_field(self, obj):
        """Champ calculé pour l'affichage dans le formulaire"""
        if obj.date_cloture:
            return "Clôturée"
        elif obj.date_ouverture:
            now = timezone.now().date()
            if obj.date_ouverture > now:
                return "À venir"
            else:
                return "En cours"
        return "Non définie"
    status_field.short_description = "Statut de la procédure"
    
    def duree_procedure(self, obj):
        """Calcul de la durée de la procédure"""
        if obj.date_ouverture and obj.date_cloture:
            delta = obj.date_cloture - obj.date_ouverture
            return f"{delta.days} jours"
        elif obj.date_ouverture:
            now = timezone.now().date()
            if obj.date_ouverture <= now:
                delta = now - obj.date_ouverture
                return f"{delta.days} jours (en cours)"
        return "N/A"
    duree_procedure.short_description = "Durée"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Validation des dates
        if obj.date_ouverture and obj.date_cloture:
            if obj.date_cloture < obj.date_ouverture:
                raise ValidationError("La date de clôture ne peut pas être antérieure à la date d'ouverture.")
        
        # Nettoyer les champs texte
        if obj.type_procedure:
            obj.type_procedure = obj.type_procedure.strip()
        if obj.tribunal:
            obj.tribunal = obj.tribunal.strip()
        if obj.numero_dossier:
            obj.numero_dossier = obj.numero_dossier.strip()
        if obj.secteur_activite:
            obj.secteur_activite = obj.secteur_activite.strip()
        if obj.description:
            obj.description = obj.description.strip()
        if obj.impact_assureur:
            obj.impact_assureur = obj.impact_assureur.strip()
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ajouter des attributs HTML aux champs
        form.base_fields['date_ouverture'].widget.attrs['placeholder'] = 'JJ/MM/AAAA'
        form.base_fields['date_cloture'].widget.attrs['placeholder'] = 'JJ/MM/AAAA'
        form.base_fields['montant_creance'].widget.attrs['placeholder'] = '0.00'
        form.base_fields['montant_creance'].widget.attrs['style'] = 'text-align: right;'
        
        # Augmenter la hauteur des zones de texte
        form.base_fields['description'].widget.attrs['rows'] = 4
        form.base_fields['impact_assureur'].widget.attrs['rows'] = 4
        form.base_fields['description'].widget.attrs['style'] = 'width: 95%;'
        form.base_fields['impact_assureur'].widget.attrs['style'] = 'width: 95%;'
        
        # Ajouter des classes CSS
        form.base_fields['type_procedure'].widget.attrs['class'] = 'vTextField'
        form.base_fields['numero_dossier'].widget.attrs['class'] = 'vTextField'
        form.base_fields['tribunal'].widget.attrs['class'] = 'vTextField'
        form.base_fields['secteur_activite'].widget.attrs['class'] = 'vTextField'
        
        return form
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'type_procedure':
            field.choices = [
                ('', '---------'),
                ('Redressement judiciaire', 'Redressement judiciaire'),
                ('Liquidation judiciaire', 'Liquidation judiciaire'),
                ('Sauvegarde', 'Sauvegarde'),
                ('Concordat', 'Concordat'),
                ('Règlement amiable', 'Règlement amiable'),
                ('Autre', 'Autre'),
            ]
        return field


@admin.register(RegistreCommerce)
class RegistreCommerceAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'numero', 'date_inscription', 'anciennete', 'created_at']
    list_filter = ['acheteur', 'date_inscription']
    search_fields = ['acheteur__nom', 'numero']
    readonly_fields = ['anciennete_field', 'created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur',)
        }),
        ('Informations registre', {
            'fields': ('numero', 'date_inscription', 'anciennete_field')
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def anciennete(self, obj):
        """Calcul de l'ancienneté depuis l'inscription"""
        if obj.date_inscription:
            now = timezone.now().date()
            delta = now - obj.date_inscription
            years = delta.days // 365
            months = (delta.days % 365) // 30
            if years > 0:
                return f"{years} an(s), {months} mois"
            else:
                return f"{months} mois"
        return "-"
    anciennete.short_description = "Ancienneté"
    
    def anciennete_field(self, obj):
        """Champ calculé pour l'affichage dans le formulaire"""
        return self.anciennete(obj)
    anciennete_field.short_description = "Ancienneté depuis l'inscription"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Nettoyer le numéro
        if obj.numero:
            obj.numero = obj.numero.strip().upper()
        
        # Validation de la date
        if obj.date_inscription:
            now = timezone.now().date()
            if obj.date_inscription > now:
                messages.warning(request, "La date d'inscription est dans le futur.")
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ajouter des attributs HTML aux champs
        form.base_fields['numero'].widget.attrs['placeholder'] = 'Ex: RC/AB/2023/1234'
        form.base_fields['date_inscription'].widget.attrs['placeholder'] = 'JJ/MM/AAAA'
        form.base_fields['numero'].widget.attrs['style'] = 'font-family: monospace;'
        return form


@admin.register(Cotisation)
class CotisationAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'numero', 'date_affiliation', 'anciennete_affiliation', 'created_at']
    list_filter = ['acheteur', 'date_affiliation']
    search_fields = ['acheteur__nom', 'numero']
    readonly_fields = ['anciennete_affiliation_field', 'created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur',)
        }),
        ('Informations sécurité sociale', {
            'fields': ('numero', 'date_affiliation', 'anciennete_affiliation_field')
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def anciennete_affiliation(self, obj):
        """Calcul de l'ancienneté depuis l'affiliation"""
        if obj.date_affiliation:
            now = timezone.now().date()
            delta = now - obj.date_affiliation
            years = delta.days // 365
            months = (delta.days % 365) // 30
            if years > 0:
                return f"{years} an(s), {months} mois"
            else:
                return f"{months} mois"
        return "-"
    anciennete_affiliation.short_description = "Ancienneté"
    
    def anciennete_affiliation_field(self, obj):
        """Champ calculé pour l'affichage dans le formulaire"""
        return self.anciennete_affiliation(obj)
    anciennete_affiliation_field.short_description = "Ancienneté depuis l'affiliation"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Nettoyer le numéro
        if obj.numero:
            obj.numero = obj.numero.strip()
        
        # Validation de la date
        if obj.date_affiliation:
            now = timezone.now().date()
            if obj.date_affiliation > now:
                messages.warning(request, "La date d'affiliation est dans le futur.")
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ajouter des attributs HTML aux champs
        form.base_fields['numero'].widget.attrs['placeholder'] = 'Ex: 123456789012345'
        form.base_fields['date_affiliation'].widget.attrs['placeholder'] = 'JJ/MM/AAAA'
        form.base_fields['numero'].widget.attrs['style'] = 'font-family: monospace;'
        return form


# =============================================================================
# ACTIONS PERSONNALISÉES
# =============================================================================

def calculer_anciennete_registre(modeladmin, request, queryset):
    """Action pour calculer l'ancienneté des inscriptions au registre de commerce"""
    for registre in queryset:
        if registre.date_inscription:
            now = timezone.now().date()
            delta = now - registre.date_inscription
            years = delta.days // 365
            months = (delta.days % 365) // 30
            modeladmin.message_user(
                request, 
                f"{registre.acheteur.nom}: {registre.numero} - {years} an(s), {months} mois d'ancienneté",
                messages.INFO
            )
    modeladmin.message_user(request, f"Ancienneté calculée pour {queryset.count()} registres.")
calculer_anciennete_registre.short_description = "Calculer l'ancienneté des registres"

def calculer_anciennete_cotisation(modeladmin, request, queryset):
    """Action pour calculer l'ancienneté des affiliations à la sécurité sociale"""
    for cotisation in queryset:
        if cotisation.date_affiliation:
            now = timezone.now().date()
            delta = now - cotisation.date_affiliation
            years = delta.days // 365
            months = (delta.days % 365) // 30
            modeladmin.message_user(
                request, 
                f"{cotisation.acheteur.nom}: {cotisation.numero} - {years} an(s), {months} mois d'ancienneté",
                messages.INFO
            )
    modeladmin.message_user(request, f"Ancienneté calculée pour {queryset.count()} cotisations.")
calculer_anciennete_cotisation.short_description = "Calculer l'ancienneté des cotisations"

def verifier_procedures_en_cours(modeladmin, request, queryset):
    """Action pour vérifier les procédures en cours"""
    now = timezone.now().date()
    for procedure in queryset:
        if procedure.date_ouverture and not procedure.date_cloture:
            if procedure.date_ouverture <= now:
                modeladmin.message_user(
                    request,
                    f"⚠️ {procedure.acheteur.nom}: {procedure.type_procedure} en cours depuis {procedure.date_ouverture}",
                    messages.WARNING
                )
            else:
                modeladmin.message_user(
                    request,
                    f"⏳ {procedure.acheteur.nom}: {procedure.type_procedure} prévue pour {procedure.date_ouverture}",
                    messages.INFO
                )
    modeladmin.message_user(request, f"Vérification terminée pour {queryset.count()} procédures.")
verifier_procedures_en_cours.short_description = "Vérifier les procédures en cours"

# Ajouter les actions aux modèles concernés
RegistreCommerceAdmin.actions = [calculer_anciennete_registre]
CotisationAdmin.actions = [calculer_anciennete_cotisation]
ProcedureCollectiveAdmin.actions = [verifier_procedures_en_cours]


# =============================================================================
# INLINES (pour intégrer dans l'admin d'Acheteur)
# =============================================================================

class ProduitServiceInline(admin.TabularInline):
    model = ProduitService
    extra = 1
    fields = ['produits', 'services']
    verbose_name = "Produits & Services"
    verbose_name_plural = "Produits & Services"
    classes = ['collapse']

class MarqueInline(admin.TabularInline):
    model = Marque
    extra = 1
    fields = ['marques']
    verbose_name = "Marque"
    verbose_name_plural = "Marques"
    classes = ['collapse']

class ProcedureCollectiveInline(admin.TabularInline):
    model = ProcedureCollective
    extra = 1
    fields = ['type_procedure', 'date_ouverture', 'date_cloture', 'numero_dossier', 'montant_creance']
    verbose_name = "Procédure Collective"
    verbose_name_plural = "Procédures Collectives"
    classes = ['collapse']

class RegistreCommerceInline(admin.TabularInline):
    model = RegistreCommerce
    extra = 1
    fields = ['numero', 'date_inscription']
    verbose_name = "Registre de Commerce"
    verbose_name_plural = "Registres de Commerce"
    classes = ['collapse']

class CotisationInline(admin.TabularInline):
    model = Cotisation
    extra = 1
    fields = ['numero', 'date_affiliation']
    verbose_name = "Cotisation Sociale"
    verbose_name_plural = "Cotisations Sociales"
    classes = ['collapse']


# =============================================================================
# FILTRES PERSONNALISÉS
# =============================================================================

class AncienneteFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour l'ancienneté des registres de commerce"""
    title = _('Ancienneté du registre')
    parameter_name = 'anciennete'

    def lookups(self, request, model_admin):
        return (
            ('moins_1_an', _('Moins d\'un an')),
            ('1_3_ans', _('1 à 3 ans')),
            ('3_5_ans', _('3 à 5 ans')),
            ('plus_5_ans', _('Plus de 5 ans')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'moins_1_an':
            date_limite = timezone.now().date() - timedelta(days=365)
            return queryset.filter(date_inscription__gte=date_limite)
        elif self.value() == '1_3_ans':
            date_min = timezone.now().date() - timedelta(days=3*365)
            date_max = timezone.now().date() - timedelta(days=365)
            return queryset.filter(date_inscription__range=(date_min, date_max))
        elif self.value() == '3_5_ans':
            date_min = timezone.now().date() - timedelta(days=5*365)
            date_max = timezone.now().date() - timedelta(days=3*365)
            return queryset.filter(date_inscription__range=(date_min, date_max))
        elif self.value() == 'plus_5_ans':
            date_limite = timezone.now().date() - timedelta(days=5*365)
            return queryset.filter(date_inscription__lt=date_limite)
        return queryset


# Ajouter le filtre personnalisé
RegistreCommerceAdmin.list_filter = ['acheteur', 'date_inscription', AncienneteFilter]
CotisationAdmin.list_filter = ['acheteur', 'date_affiliation']


# =============================================================================
# STYLE CSS PERSONNALISÉ
# =============================================================================

class Media:
    css = {
        'all': ('admin/custom.css',)
    }
    
    js = ('admin/custom.js',)
    
    
    
    


@admin.register(CodeNaceAcheteur)
class CodeNaceAcheteurAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'code_details', 'created_at']
    list_filter = ['acheteur', 'created_at']
    search_fields = ['acheteur__nom', 'code__code', 'code__description']
    readonly_fields = ['code_details_field', 'created_at', 'updated_at', 
                      'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'code')
        }),
        ('Informations détaillées', {
            'fields': ('code_details_field',)
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def code_details(self, obj):
        if obj.code:
            return f"{obj.code.code} - {obj.code.description[:50]}..."
        return "-"
    code_details.short_description = "Code NACE"
    
    def code_details_field(self, obj):
        """Champ calculé pour l'affichage détaillé dans le formulaire"""
        if obj.code:
            return format_html(
                '<div style="padding: 10px; background: #f9f9f9; border-radius: 5px; margin: 10px 0;">'
                '<strong>Code:</strong> {}<br>'
                '<strong>Description:</strong> {}<br>'
                '<strong>Catégorie:</strong> {}<br>'
                '<strong>Sous-catégorie:</strong> {}'
                '</div>',
                obj.code.code,
                obj.code.description,
                obj.code.category_nace.description if obj.code.category_nace else '-',
                obj.code.subcategory_nace.description if obj.code.subcategory_nace else '-'
            )
        return "-"
    code_details_field.short_description = "Détails du code NACE"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Vérifier si le code NACE est déjà associé à cet acheteur
        existing = CodeNaceAcheteur.objects.filter(
            acheteur=obj.acheteur, 
            code=obj.code
        ).exclude(pk=obj.pk).first()
        
        if existing:
            messages.warning(request, f"Ce code NACE est déjà associé à {obj.acheteur.nom}")
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'code', 'code__category_nace', 
                                'code__subcategory_nace', 'created_by', 'updated_by')


@admin.register(CodeNafAcheteur)
class CodeNafAcheteurAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'code_details', 'created_at']
    list_filter = ['acheteur', 'created_at']
    search_fields = ['acheteur__nom', 'code__code', 'code__description']
    readonly_fields = ['code_details_field', 'created_at', 'updated_at', 
                      'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'code')
        }),
        ('Informations détaillées', {
            'fields': ('code_details_field',)
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def code_details(self, obj):
        if obj.code:
            return f"{obj.code.code} - {obj.code.description[:50]}..."
        return "-"
    code_details.short_description = "Code NAF"
    
    def code_details_field(self, obj):
        """Champ calculé pour l'affichage détaillé dans le formulaire"""
        if obj.code:
            return format_html(
                '<div style="padding: 10px; background: #f9f9f9; border-radius: 5px; margin: 10px 0;">'
                '<strong>Code:</strong> {}<br>'
                '<strong>Description:</strong> {}<br>'
                '<strong>Catégorie:</strong> {}<br>'
                '<strong>Sous-catégorie:</strong> {}'
                '</div>',
                obj.code.code,
                obj.code.description,
                obj.code.category_naf.description if obj.code.category_naf else '-',
                obj.code.subcategory_naf.description if obj.code.subcategory_naf else '-'
            )
        return "-"
    code_details_field.short_description = "Détails du code NAF"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Vérifier si le code NAF est déjà associé à cet acheteur
        existing = CodeNafAcheteur.objects.filter(
            acheteur=obj.acheteur, 
            code=obj.code
        ).exclude(pk=obj.pk).first()
        
        if existing:
            messages.warning(request, f"Ce code NAF est déjà associé à {obj.acheteur.nom}")
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'code', 'code__category_naf', 
                                'code__subcategory_naf', 'created_by', 'updated_by')


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'type_certification_display', 'nom_certification', 
                    'date_obtention', 'organisme_delivreur', 'created_at']
    list_filter = ['acheteur', 'type_certification', 'date_obtention', 'organisme_delivreur']
    search_fields = ['acheteur__nom', 'type_certification', 'nom_certification', 
                     'organisme_delivreur', 'description']
    readonly_fields = ['type_certification_display_field', 'created_at', 'updated_at', 
                      'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'type_certification', 'nom_certification')
        }),
        ('Informations certification', {
            'fields': ('date_obtention', 'organisme_delivreur', 'description')
        }),
        ('Informations affichées', {
            'fields': ('type_certification_display_field',)
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def type_certification_display(self, obj):
        return obj.get_type_certification_display()
    type_certification_display.short_description = "Type de certification"
    
    def type_certification_display_field(self, obj):
        """Champ calculé pour l'affichage dans le formulaire"""
        return obj.get_type_certification_display()
    type_certification_display_field.short_description = "Type de certification (affiché)"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Nettoyer les champs texte
        if obj.nom_certification:
            obj.nom_certification = obj.nom_certification.strip()
        if obj.organisme_delivreur:
            obj.organisme_delivreur = obj.organisme_delivreur.strip()
        if obj.description:
            obj.description = obj.description.strip()
        
        # Validation de la date
        if obj.date_obtention:
            now = timezone.now().date()
            if obj.date_obtention > now:
                messages.warning(request, "La date d'obtention est dans le futur.")
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ajouter des attributs HTML aux champs
        form.base_fields['date_obtention'].widget.attrs['placeholder'] = 'JJ/MM/AAAA'
        form.base_fields['nom_certification'].widget.attrs['placeholder'] = 'Ex: ISO 9001:2015'
        form.base_fields['organisme_delivreur'].widget.attrs['placeholder'] = 'Ex: AFNOR Certification'
        
        # Augmenter la hauteur des zones de texte
        form.base_fields['description'].widget.attrs['rows'] = 4
        form.base_fields['description'].widget.attrs['style'] = 'width: 95%;'
        
        return form


@admin.register(InnovationDeveloppement)
class InnovationDeveloppementAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'type_innovation_display', 'titre', 
                    'date_debut', 'date_fin', 'status_innovation', 'created_at']
    list_filter = ['acheteur', 'type_innovation', 'date_debut', 'date_fin']
    search_fields = ['acheteur__nom', 'type_innovation', 'titre', 'description']
    readonly_fields = ['type_innovation_display_field', 'status_innovation_field', 
                      'duree_innovation', 'created_at', 'updated_at', 
                      'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'type_innovation', 'titre')
        }),
        ('Période', {
            'fields': ('date_debut', 'date_fin', 'status_innovation_field', 'duree_innovation')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('wide',)
        }),
        ('Informations affichées', {
            'fields': ('type_innovation_display_field',)
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def type_innovation_display(self, obj):
        return obj.get_type_innovation_display()
    type_innovation_display.short_description = "Type d'innovation"
    
    def status_innovation(self, obj):
        if obj.date_fin:
            return format_html('<span style="color: green;">✅ Terminée</span>')
        elif obj.date_debut:
            now = timezone.now().date()
            if obj.date_debut > now:
                return format_html('<span style="color: orange;">⏳ Planifiée</span>')
            else:
                return format_html('<span style="color: blue;">🔄 En cours</span>')
        return "-"
    status_innovation.short_description = "Statut"
    
    def type_innovation_display_field(self, obj):
        return obj.get_type_innovation_display()
    type_innovation_display_field.short_description = "Type d'innovation (affiché)"
    
    def status_innovation_field(self, obj):
        if obj.date_fin:
            return "Terminée"
        elif obj.date_debut:
            now = timezone.now().date()
            if obj.date_debut > now:
                return "Planifiée"
            else:
                return "En cours"
        return "Non définie"
    status_innovation_field.short_description = "Statut de l'innovation"
    
    def duree_innovation(self, obj):
        """Calcul de la durée de l'innovation"""
        if obj.date_debut and obj.date_fin:
            delta = obj.date_fin - obj.date_debut
            return f"{delta.days} jours"
        elif obj.date_debut:
            now = timezone.now().date()
            if obj.date_debut <= now:
                delta = now - obj.date_debut
                return f"{delta.days} jours (en cours)"
        return "N/A"
    duree_innovation.short_description = "Durée"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Nettoyer les champs texte
        if obj.titre:
            obj.titre = obj.titre.strip()
        if obj.description:
            obj.description = obj.description.strip()
        
        # Validation des dates
        if obj.date_debut and obj.date_fin:
            if obj.date_fin < obj.date_debut:
                raise ValidationError("La date de fin ne peut pas être antérieure à la date de début.")
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ajouter des attributs HTML aux champs
        form.base_fields['date_debut'].widget.attrs['placeholder'] = 'JJ/MM/AAAA'
        form.base_fields['date_fin'].widget.attrs['placeholder'] = 'JJ/MM/AAAA'
        form.base_fields['titre'].widget.attrs['placeholder'] = 'Ex: Nouveau système de production'
        
        # Augmenter la hauteur des zones de texte
        form.base_fields['description'].widget.attrs['rows'] = 4
        form.base_fields['description'].widget.attrs['style'] = 'width: 95%;'
        
        return form


@admin.register(StrategiePlanification)
class StrategiePlanificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'type_strategie_display', 'date_mise_en_place', 
                    'anciennete_strategie', 'created_at']
    list_filter = ['acheteur', 'type_strategie', 'date_mise_en_place']
    search_fields = ['acheteur__nom', 'type_strategie', 'description']
    readonly_fields = ['type_strategie_display_field', 'anciennete_strategie_field', 
                      'created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'type_strategie')
        }),
        ('Mise en place', {
            'fields': ('date_mise_en_place', 'anciennete_strategie_field')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('wide',)
        }),
        ('Informations affichées', {
            'fields': ('type_strategie_display_field',)
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def type_strategie_display(self, obj):
        return obj.get_type_strategie_display()
    type_strategie_display.short_description = "Type de stratégie"
    
    def anciennete_strategie(self, obj):
        """Calcul de l'ancienneté de la stratégie"""
        if obj.date_mise_en_place:
            now = timezone.now().date()
            delta = now - obj.date_mise_en_place
            years = delta.days // 365
            months = (delta.days % 365) // 30
            if years > 0:
                return f"{years} an(s), {months} mois"
            else:
                return f"{months} mois"
        return "-"
    anciennete_strategie.short_description = "Ancienneté"
    
    def type_strategie_display_field(self, obj):
        return obj.get_type_strategie_display()
    type_strategie_display_field.short_description = "Type de stratégie (affiché)"
    
    def anciennete_strategie_field(self, obj):
        return self.anciennete_strategie(obj)
    anciennete_strategie_field.short_description = "Ancienneté de la stratégie"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Nettoyer les champs texte
        if obj.description:
            obj.description = obj.description.strip()
        
        # Validation de la date
        if obj.date_mise_en_place:
            now = timezone.now().date()
            if obj.date_mise_en_place > now:
                messages.warning(request, "La date de mise en place est dans le futur.")
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ajouter des attributs HTML aux champs
        form.base_fields['date_mise_en_place'].widget.attrs['placeholder'] = 'JJ/MM/AAAA'
        
        # Augmenter la hauteur des zones de texte
        form.base_fields['description'].widget.attrs['rows'] = 4
        form.base_fields['description'].widget.attrs['style'] = 'width: 95%;'
        
        return form


@admin.register(ConformiteReglementation)
class ConformiteReglementationAdmin(admin.ModelAdmin):
    list_display = ['id', 'acheteur', 'type_conformite_display', 'statut_display', 
                    'date_verification', 'organisme_controle', 'created_at']
    list_filter = ['acheteur', 'type_conformite', 'statut', 'organisme_controle']
    search_fields = ['acheteur__nom', 'type_conformite', 'organisme_controle', 
                     'details_non_conformite', 'commentaires']
    readonly_fields = ['type_conformite_display_field', 'statut_display_field', 
                      'anciennete_verification', 'created_at', 'updated_at', 
                      'created_by', 'updated_by']
    fieldsets = (
        ('Identification', {
            'fields': ('acheteur', 'type_conformite')
        }),
        ('Statut', {
            'fields': ('statut', 'statut_display_field', 'details_non_conformite')
        }),
        ('Vérification', {
            'fields': ('date_verification', 'organisme_controle', 'anciennete_verification')
        }),
        ('Commentaires', {
            'fields': ('commentaires',),
            'classes': ('wide',)
        }),
        ('Informations affichées', {
            'fields': ('type_conformite_display_field',)
        }),
        ('Dates et utilisateurs', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    def type_conformite_display(self, obj):
        return obj.get_type_conformite_display()
    type_conformite_display.short_description = "Type de conformité"
    
    def statut_display(self, obj):
        if obj.statut:
            return format_html('<span style="color: green; font-weight: bold;">✅ Conforme</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">❌ Non-conforme</span>')
    statut_display.short_description = "Statut"
    
    def type_conformite_display_field(self, obj):
        return obj.get_type_conformite_display()
    type_conformite_display_field.short_description = "Type de conformité (affiché)"
    
    def statut_display_field(self, obj):
        if obj.statut:
            return "Conforme"
        else:
            return "Non-conforme"
    statut_display_field.short_description = "Statut (affiché)"
    
    def anciennete_verification(self, obj):
        """Calcul de l'ancienneté depuis la dernière vérification"""
        if obj.date_verification:
            now = timezone.now().date()
            delta = now - obj.date_verification
            days = delta.days
            if days < 30:
                return f"{days} jour(s)"
            elif days < 365:
                months = days // 30
                return f"{months} mois"
            else:
                years = days // 365
                months = (days % 365) // 30
                return f"{years} an(s), {months} mois"
        return "Jamais vérifiée"
    anciennete_verification.short_description = "Délai depuis vérification"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        # Nettoyer les champs texte
        if obj.organisme_controle:
            obj.organisme_controle = obj.organisme_controle.strip()
        if obj.details_non_conformite:
            obj.details_non_conformite = obj.details_non_conformite.strip()
        if obj.commentaires:
            obj.commentaires = obj.commentaires.strip()
        
        # Validation de la date
        if obj.date_verification:
            now = timezone.now().date()
            if obj.date_verification > now:
                messages.warning(request, "La date de vérification est dans le futur.")
        
        # Avertissement si non-conformité
        if not obj.statut and not obj.details_non_conformite:
            messages.warning(request, "Veuillez fournir des détails sur la non-conformité.")
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('acheteur', 'created_by', 'updated_by')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ajouter des attributs HTML aux champs
        form.base_fields['date_verification'].widget.attrs['placeholder'] = 'JJ/MM/AAAA'
        form.base_fields['organisme_controle'].widget.attrs['placeholder'] = 'Ex: DGCCRF, ANSM, etc.'
        
        # Augmenter la hauteur des zones de texte
        form.base_fields['details_non_conformite'].widget.attrs['rows'] = 3
        form.base_fields['commentaires'].widget.attrs['rows'] = 3
        form.base_fields['details_non_conformite'].widget.attrs['style'] = 'width: 95%;'
        form.base_fields['commentaires'].widget.attrs['style'] = 'width: 95%;'
        
        # Ajouter des classes CSS
        form.base_fields['statut'].widget.attrs['class'] = 'vCheckboxField'
        
        return form


# =============================================================================
# ACTIONS PERSONNALISÉES
# =============================================================================

def verifier_conformites_expirees(modeladmin, request, queryset):
    """Action pour vérifier les conformités dont la vérification est expirée (plus d'un an)"""
    now = timezone.now().date()
    limite = now - timedelta(days=365)
    
    for conformite in queryset.filter(date_verification__lt=limite):
        days = (now - conformite.date_verification).days
        modeladmin.message_user(
            request,
            f"⚠️ {conformite.acheteur.nom}: {conformite.get_type_conformite_display()} - "
            f"Dernière vérification il y a {days} jours ({conformite.date_verification})",
            messages.WARNING
        )
    
    count = queryset.filter(date_verification__lt=limite).count()
    modeladmin.message_user(request, f"{count} conformités nécessitent une nouvelle vérification.")
verifier_conformites_expirees.short_description = "Vérifier les conformités expirées"

def verifier_innovations_en_cours(modeladmin, request, queryset):
    """Action pour vérifier les innovations en cours"""
    now = timezone.now().date()
    
    for innovation in queryset.filter(date_debut__lte=now, date_fin__isnull=True):
        days = (now - innovation.date_debut).days
        modeladmin.message_user(
            request,
            f"🔄 {innovation.acheteur.nom}: {innovation.get_type_innovation_display()} - "
            f"En cours depuis {days} jours",
            messages.INFO
        )
    
    count = queryset.filter(date_debut__lte=now, date_fin__isnull=True).count()
    modeladmin.message_user(request, f"{count} innovations sont en cours.")
verifier_innovations_en_cours.short_description = "Vérifier les innovations en cours"

def verifier_certifications_expirees(modeladmin, request, queryset):
    """Action pour vérifier les certifications anciennes (plus de 3 ans)"""
    now = timezone.now().date()
    limite = now - timedelta(days=3*365)
    
    for certification in queryset.filter(date_obtention__lt=limite):
        days = (now - certification.date_obtention).days
        modeladmin.message_user(
            request,
            f"📅 {certification.acheteur.nom}: {certification.get_type_certification_display()} - "
            f"Obtenue il y a {days} jours ({certification.date_obtention})",
            messages.INFO
        )
    
    count = queryset.filter(date_obtention__lt=limite).count()
    modeladmin.message_user(request, f"{count} certifications ont plus de 3 ans.")
verifier_certifications_expirees.short_description = "Vérifier les certifications anciennes"

# Ajouter les actions aux modèles concernés
ConformiteReglementationAdmin.actions = [verifier_conformites_expirees]
InnovationDeveloppementAdmin.actions = [verifier_innovations_en_cours]
CertificationAdmin.actions = [verifier_certifications_expirees]


# =============================================================================
# FILTRES PERSONNALISÉS
# =============================================================================

class StatutConformiteFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour le statut de conformité"""
    title = _('Statut de conformité')
    parameter_name = 'statut_conformite'

    def lookups(self, request, model_admin):
        return (
            ('conforme', _('✅ Conforme')),
            ('non_conforme', _('❌ Non-conforme')),
            ('non_verifie', _('⚠️ Non vérifié récemment')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'non_verifie':
            limite = timezone.now().date() - timedelta(days=365)
            return queryset.filter(date_verification__lt=limite)
        return queryset


class TypeInnovationFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les types d'innovation"""
    title = _('Type d\'innovation')
    parameter_name = 'type_innovation'

    def lookups(self, request, model_admin):
        # Récupérer les valeurs disponibles depuis le modèle
        from .models import InnovationDeveloppement
        return InnovationDeveloppement.TYPES_INNOVATION

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type_innovation=self.value())
        return queryset


# Ajouter les filtres personnalisés
ConformiteReglementationAdmin.list_filter = ['acheteur', 'type_conformite', 
                                             StatutConformiteFilter, 'organisme_controle']
InnovationDeveloppementAdmin.list_filter = ['acheteur', TypeInnovationFilter, 
                                           'date_debut', 'date_fin']


# =============================================================================
# INLINES (pour intégrer dans l'admin d'Acheteur)
# =============================================================================

class CodeNaceAcheteurInline(admin.TabularInline):
    model = CodeNaceAcheteur
    extra = 1
    fields = ['code']
    verbose_name = "Code NACE"
    verbose_name_plural = "Codes NACE"
    autocomplete_fields = ['code']
    classes = ['collapse']

class CodeNafAcheteurInline(admin.TabularInline):
    model = CodeNafAcheteur
    extra = 1
    fields = ['code']
    verbose_name = "Code NAF"
    verbose_name_plural = "Codes NAF"
    autocomplete_fields = ['code']
    classes = ['collapse']

class CertificationInline(admin.TabularInline):
    model = Certification
    extra = 1
    fields = ['type_certification', 'nom_certification', 'date_obtention', 
              'organisme_delivreur', 'description']
    verbose_name = "Certification"
    verbose_name_plural = "Certifications"
    classes = ['collapse']

class InnovationDeveloppementInline(admin.TabularInline):
    model = InnovationDeveloppement
    extra = 1
    fields = ['type_innovation', 'titre', 'date_debut', 'date_fin', 'description']
    verbose_name = "Innovation & Développement"
    verbose_name_plural = "Innovations & Développements"
    classes = ['collapse']

class StrategiePlanificationInline(admin.TabularInline):
    model = StrategiePlanification
    extra = 1
    fields = ['type_strategie', 'date_mise_en_place', 'description']
    verbose_name = "Stratégie & Planification"
    verbose_name_plural = "Stratégies & Planifications"
    classes = ['collapse']

class ConformiteReglementationInline(admin.TabularInline):
    model = ConformiteReglementation
    extra = 1
    fields = ['type_conformite', 'statut', 'details_non_conformite', 
              'date_verification', 'organisme_controle', 'commentaires']
    verbose_name = "Conformité & Réglementation"
    verbose_name_plural = "Conformités & Réglementations"
    classes = ['collapse']


# =============================================================================
# AUTOFILDS POUR L'AUTOCOMPLÉTION
# =============================================================================

class CodeNaceAcheteurAdminAutocomplete(admin.ModelAdmin):
    search_fields = ['code__code', 'code__description', 'acheteur__nom']
    autocomplete_fields = ['code', 'acheteur']

class CodeNafAcheteurAdminAutocomplete(admin.ModelAdmin):
    search_fields = ['code__code', 'code__description', 'acheteur__nom']
    autocomplete_fields = ['code', 'acheteur']


# =============================================================================
# ADMIN SITE PERSONNALISÉ
# =============================================================================

# Configuration des titres
admin.site.site_header = "Gestion des Acheteurs - Codes et Conformités"
admin.site.site_title = "Admin Acheteurs - Codes NACE/NAF"
admin.site.index_title = "Administration des codes et conformités"






# =============================================================================
# ADMIN ACTIONS PERSONNALISÉES
# =============================================================================

def marquer_comme_lues_action(modeladmin, request, queryset):
    """Action pour marquer les notifications comme lues"""
    updated = queryset.update(is_read=True)
    modeladmin.message_user(request, f"{updated} notification(s) marquée(s) comme lue(s).")
marquer_comme_lues_action.short_description = "Marquer comme lues"

def passer_en_cours_action(modeladmin, request, queryset):
    """Action pour passer des commandes en statut 'en cours'"""
    for commande in queryset:
        commande.status = "en_cours"
        commande.save()
    modeladmin.message_user(request, f"{queryset.count()} commande(s) passée(s) en cours de traitement.")
passer_en_cours_action.short_description = "Passer en cours de traitement"

def valider_rapports_action(modeladmin, request, queryset):
    """Action pour valider des rapports"""
    for validation in queryset.filter(status="en_attente"):
        validation.status = "valide"
        validation.validateur = request.user
        validation.save()
    modeladmin.message_user(request, f"{queryset.filter(status='en_attente').count()} rapport(s) validé(s).")
valider_rapports_action.short_description = "Valider les rapports sélectionnés"

def demander_correction_action(modeladmin, request, queryset):
    """Action pour demander une correction sur des rapports"""
    for validation in queryset.filter(status="en_attente"):
        validation.status = "a_corriger"
        validation.validateur = request.user
        validation.save()
    modeladmin.message_user(request, f"{queryset.filter(status='en_attente').count()} correction(s) demandée(s).")
demander_correction_action.short_description = "Demander correction"

def envoyer_au_client_action(modeladmin, request, queryset):
    """Action pour envoyer des rapports au client"""
    now = timezone.now()
    for commande in queryset.filter(status="rapport_valide", email_envoye=False):
        commande.status = "envoye_client"
        commande.date_envoi_client = now
        commande.email_envoye = True
        commande.save()
    modeladmin.message_user(request, f"{queryset.filter(status='rapport_valide', email_envoye=False).count()} rapport(s) envoyé(s) au client.")
envoyer_au_client_action.short_description = "Envoyer au client"

def generer_notification_rappel_action(modeladmin, request, queryset):
    """Action pour générer des notifications de rappel"""
    for commande in queryset:
        if commande.date_rapport:
            jours_restants = (commande.date_rapport - timezone.now().date()).days
            if jours_restants <= 3:
                # Créer une notification de rappel
                Notification.objects.create(
                    user=commande.client,
                    type="RAPPEL",
                    message=f"Rappel : La commande {commande.notre_ref} doit être livrée dans {jours_restants} jour(s)"
                )
    modeladmin.message_user(request, f"Notifications de rappel générées pour {queryset.count()} commande(s).")
generer_notification_rappel_action.short_description = "Générer notifications de rappel"


# =============================================================================
# FILTRES PERSONNALISÉS
# =============================================================================

class NotificationTypeFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les types de notification"""
    title = _('Type de notification')
    parameter_name = 'type_notif'

    def lookups(self, request, model_admin):
        return Notification.TYPE_NOTIF

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type=self.value())
        return queryset


class CommandeStatusFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les statuts de commande"""
    title = _('Statut de commande')
    parameter_name = 'status_commande'

    def lookups(self, request, model_admin):
        return Commande.STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class RetardCommandeFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les commandes en retard"""
    title = _('Retard de commande')
    parameter_name = 'retard'

    def lookups(self, request, model_admin):
        return (
            ('en_retard', _('En retard')),
            ('a_jour', _('À jour')),
            ('bientot_en_retard', _('Bientôt en retard (3 jours)')),
        )

    def queryset(self, request, queryset):
        now = timezone.now().date()
        if self.value() == 'en_retard':
            return queryset.filter(date_rapport__lt=now)
        elif self.value() == 'bientot_en_retard':
            limite = now + timedelta(days=3)
            return queryset.filter(date_rapport__range=(now, limite))
        elif self.value() == 'a_jour':
            return queryset.filter(date_rapport__gte=now)
        return queryset


class ValidationStatusFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les statuts de validation"""
    title = _('Statut de validation')
    parameter_name = 'status_validation'

    def lookups(self, request, model_admin):
        return [
            ("en_attente", _("En attente")),
            ("valide", _("Validé")),
            ("a_corriger", _("À corriger")),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


# =============================================================================
# INLINES
# =============================================================================

class SuiviCommandeInline(admin.TabularInline):
    model = SuiviCommande
    extra = 1
    readonly_fields = ['user', 'date_action']
    fields = ['type', 'action', 'user', 'date_action', 'commentaire']
    verbose_name = "Étape de suivi"
    verbose_name_plural = "Historique du suivi"
    classes = ['collapse']
    ordering = ['-date_action']

class AffectationAnalysteInline(admin.TabularInline):
    model = AffectationAnalyste
    extra = 1
    readonly_fields = ['date_affectation']
    fields = ['analyste', 'date_affectation']
    verbose_name = "Affectation"
    verbose_name_plural = "Affectations des analystes"
    classes = ['collapse']

class RapportInline(admin.TabularInline):
    model = Rapport
    extra = 1
    readonly_fields = ['analyste', 'date_soumission']
    fields = ['analyste', 'fichier', 'date_soumission']
    verbose_name = "Rapport"
    verbose_name_plural = "Rapports soumis"
    classes = ['collapse']




# =============================================================================
# MODEL ADMINS
# =============================================================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'type_display', 'message_preview', 
                    'is_read_display', 'created_at']
    list_filter = [NotificationTypeFilter, 'is_read', 'created_at', 'user']
    search_fields = ['user__username', 'user__email', 'message', 'type']
    readonly_fields = ['created_at']
    actions = [marquer_comme_lues_action]
    fieldsets = (
        ('Notification', {
            'fields': ('user', 'type', 'message', 'is_read')
        }),
        ('Dates', {
            'fields': ('created_at',)
        }),
    )
    
    def type_display(self, obj):
        icons = {
            "AFFECTATION": "👤",
            "RAPPORT_SOUMIS": "📄",
            "VALIDATION": "✅",
            "CORRECTION": "⚠️",
            "ENVOI_CLIENT": "📧",
            "RAPPEL": "⏰",
        }
        return format_html(
            '<span style="font-size: 1.2em;">{} {}</span>',
            icons.get(obj.type, "📢"),
            obj.get_type_display()
        )
    type_display.short_description = "Type"
    
    def message_preview(self, obj):
        if len(obj.message) > 50:
            return obj.message[:50] + "..."
        return obj.message
    message_preview.short_description = "Message"
    
    def is_read_display(self, obj):
        if obj.is_read:
            return format_html('<span style="color: green;">✅ Lu</span>')
        else:
            return format_html('<span style="color: orange; font-weight: bold;">🔴 Non lu</span>')
    is_read_display.short_description = "Statut"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
    
    class Media:
        css = {
            'all': ('admin/css/notifications.css',)
        }


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ['id', 'notre_ref', 'raison_sociale', 'type_rapport_display', 
                    'status_display', 'date_recept_commande', 'date_rapport', 
                    'delais_jours_restants', 'client', 'created_at']
    list_filter = [CommandeStatusFilter, RetardCommandeFilter, 'type_rapport', 
                   'client', 'date_recept_commande', 'created_at']
    search_fields = ['notre_ref', 'reference_client', 'raison_sociale', 
                     'acheteur__nom', 'client__username', 'client__email']
    readonly_fields = ['status_display_field', 'delais_jours_restants_field', 
                      'email_envoye_display', 'created_at', 'updated_at']
    actions = [passer_en_cours_action, envoyer_au_client_action, 
               generer_notification_rappel_action]
    inlines = [SuiviCommandeInline, AffectationAnalysteInline, 
               RapportInline]
    
    fieldsets = (
        ('Références', {
            'fields': ('notre_ref', 'reference_client')
        }),
        ('Dates et délais', {
            'fields': ('date_recept_commande', 'date_rapport', 'delais', 
                      'priorite', 'delais_jours_restants_field')
        }),
        ('Informations rapport', {
            'fields': ('raison_sociale', 'type_rapport', 'imprimer_avec_etats_fin')
        }),
        ('Crédit', {
            'fields': ('credit_demande', 'devise_credit_demande', 
                      'credit_recommande', 'devise_credit_recommande')
        }),
        ('Adresse', {
            'fields': ('numero_adresse', 'rue_adresse', 'code_postale_adresse', 
                      'address_additional', 'state', 'postcode', 'post_office')
        }),
        ('Contacts', {
            'fields': ('telephone', 'email')
        }),
        ('Localisation', {
            'fields': ('pays', 'ville')
        }),
        ('Clients et acteurs', {
            'fields': ('client', 'acheteur', 'validateur')
        }),
        ('Statut et suivi', {
            'fields': ('status', 'status_display_field', 'email_envoye_display', 
                      'date_envoi_client')
        }),
        ('Informations supplémentaires', {
            'fields': ('company_identification_number', 'provider', 'comments'),
            'classes': ('collapse',)
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def type_rapport_display(self, obj):
        return obj.get_type_rapport_display()
    type_rapport_display.short_description = "Type rapport"
    
    def status_display(self, obj):
        status_colors = {
            "nouvelle": "blue",
            "en_cours": "orange",
            "rapport_soumis": "purple",
            "rapport_valide": "green",
            "envoye_client": "darkgreen",
            "terminee": "gray",
            "annulee": "red",
        }
        color = status_colors.get(obj.status, "black")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = "Statut"
    
    def delais_jours_restants(self, obj):
        if obj.date_rapport:
            now = timezone.now().date()
            delta = obj.date_rapport - now
            days = delta.days
            
            if days < 0:
                return format_html(
                    '<span style="color: red; font-weight: bold;">⚠️ En retard ({} jours)</span>',
                    abs(days)
                )
            elif days <= 3:
                return format_html(
                    '<span style="color: orange; font-weight: bold;">⏰ {} jours</span>',
                    days
                )
            else:
                return format_html(
                    '<span style="color: green;">✅ {} jours</span>',
                    days
                )
        return "-"
    delais_jours_restants.short_description = "Délais"
    
    def status_display_field(self, obj):
        return self.status_display(obj)
    status_display_field.short_description = "Statut (affiché)"
    
    def delais_jours_restants_field(self, obj):
        return self.delais_jours_restants(obj)
    delais_jours_restants_field.short_description = "Délais restants"
    
    def email_envoye_display(self, obj):
        if obj.email_envoye:
            if obj.date_envoi_client:
                return format_html(
                    '<span style="color: green;">✅ Oui (le {})</span>',
                    obj.date_envoi_client.strftime('%d/%m/%Y %H:%M')
                )
            return format_html('<span style="color: green;">✅ Oui</span>')
        return format_html('<span style="color: orange;">❌ Non</span>')
    email_envoye_display.short_description = "Email envoyé"
    
    def save_model(self, request, obj, form, change):
        # Logique pour créer un suivi automatique
        if change:
            original = Commande.objects.get(pk=obj.pk)
            
            # Vérifier les changements de statut
            if original.status != obj.status:
                SuiviCommande.objects.create(
                    commande=obj,
                    user=request.user,
                    action=f"Changement de statut : {original.get_status_display()} → {obj.get_status_display()}",
                    type="AUTRE"
                )
            
            # Vérifier l'envoi au client
            if not original.email_envoye and obj.email_envoye:
                obj.date_envoi_client = timezone.now()
                SuiviCommande.objects.create(
                    commande=obj,
                    user=request.user,
                    action="Rapport envoyé au client",
                    type="ENVOI_CLIENT"
                )
        else:
            # Nouvelle commande
            SuiviCommande.objects.create(
                commande=obj,
                user=request.user,
                action="Commande créée",
                type="CREATION"
            )
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('client', 'acheteur', 'validateur', 
                               'devise_credit_demande', 'devise_credit_recommande',
                               'pays', 'ville')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ajouter des attributs HTML aux champs
        form.base_fields['date_recept_commande'].widget.attrs['placeholder'] = 'JJ/MM/AAAA'
        form.base_fields['date_rapport'].widget.attrs['placeholder'] = 'JJ/MM/AAAA'
        form.base_fields['notre_ref'].widget.attrs['placeholder'] = 'Ex: CMD-2024-001'
        form.base_fields['reference_client'].widget.attrs['placeholder'] = 'Ex: REF-CLIENT-001'
        
        # Masquer certains champs selon le statut
        if obj and obj.status != 'rapport_valide':
            form.base_fields['date_envoi_client'].widget.attrs['readonly'] = True
            form.base_fields['email_envoye'].widget.attrs['disabled'] = True
        
        return form
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        commande = self.get_object(request, object_id)
        
        # Ajouter des statistiques au contexte
        extra_context['statistiques'] = {
            'total_suivis': commande.suivicommande_set.count(),
            'total_affectations': commande.affectationanalyste_set.count(),
            'total_rapports': commande.rapport_set.count(),
            'total_validations': commande.validationrapport_set.count(),
        }
        
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(SuiviCommande)
class SuiviCommandeAdmin(admin.ModelAdmin):
    list_display = ['id', 'commande', 'type_display', 'action_preview', 
                    'user', 'date_action']
    list_filter = ['type', 'date_action', 'user']
    search_fields = ['commande__notre_ref', 'commande__raison_sociale', 
                     'action', 'commentaire', 'user__username']
    readonly_fields = ['date_action']
    fieldsets = (
        ('Suivi', {
            'fields': ('commande', 'user', 'type', 'action', 'commentaire')
        }),
        ('Dates', {
            'fields': ('date_action',)
        }),
    )
    
    def type_display(self, obj):
        icons = {
            "CREATION": "➕",
            "AFFECTATION": "👤",
            "SOUMISSION": "📄",
            "VALIDATION": "✅",
            "CORRECTION": "⚠️",
            "ENVOI_CLIENT": "📧",
            "CLOTURE": "🔒",
            "ANNULATION": "❌",
            "AUTRE": "ℹ️",
        }
        return format_html(
            '<span style="font-size: 1.2em;">{} {}</span>',
            icons.get(obj.type, "ℹ️"),
            obj.get_type_display()
        )
    type_display.short_description = "Type"
    
    def action_preview(self, obj):
        if len(obj.action) > 50:
            return obj.action[:50] + "..."
        return obj.action
    action_preview.short_description = "Action"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('commande', 'user')
    
    def has_add_permission(self, request):
        # Éviter l'ajout manuel de suivi
        return False


@admin.register(AffectationAnalyste)
class AffectationAnalysteAdmin(admin.ModelAdmin):
    list_display = ['id', 'commande', 'analyste', 'date_affectation']
    list_filter = ['date_affectation', 'analyste']
    search_fields = ['commande__notre_ref', 'commande__raison_sociale', 
                     'analyste__username', 'analyste__email']
    readonly_fields = ['date_affectation']
    fieldsets = (
        ('Affectation', {
            'fields': ('commande', 'analyste')
        }),
        ('Dates', {
            'fields': ('date_affectation',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('commande', 'analyste')


@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = ['id', 'commande', 'analyste', 'fichier_link', 
                    'date_soumission', 'validation_status']
    list_filter = ['date_soumission', 'analyste']
    search_fields = ['commande__notre_ref', 'commande__raison_sociale', 
                     'analyste__username', 'analyste__email']
    readonly_fields = ['analyste', 'date_soumission', 'validation_status_field']
    fieldsets = (
        ('Rapport', {
            'fields': ('commande', 'analyste', 'fichier')
        }),
        ('Validation', {
            'fields': ('validation_status_field',)
        }),
        ('Dates', {
            'fields': ('date_soumission',)
        }),
    )
    
    def fichier_link(self, obj):
        if obj.fichier:
            filename = obj.fichier.name.split('/')[-1]
            return format_html(
                '<a href="{}" target="_blank">📄 {}</a>',
                obj.fichier.url,
                filename[:30] + "..." if len(filename) > 30 else filename
            )
        return "-"
    fichier_link.short_description = "Fichier"
    
    def validation_status(self, obj):
        try:
            validation = obj.validationrapport
            if validation.status == "valide":
                return format_html('<span style="color: green;">✅ Validé</span>')
            elif validation.status == "a_corriger":
                return format_html('<span style="color: orange;">⚠️ À corriger</span>')
            else:
                return format_html('<span style="color: blue;">⏳ En attente</span>')
        except ValidationRapport.DoesNotExist:
            return format_html('<span style="color: gray;">📝 Non soumis</span>')
    validation_status.short_description = "Statut validation"
    
    def validation_status_field(self, obj):
        return self.validation_status(obj)
    validation_status_field.short_description = "Statut de validation"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('commande', 'analyste')


@admin.register(ValidationRapport)
class ValidationRapportAdmin(admin.ModelAdmin):
    list_display = ['id', 'rapport', 'validateur', 'status_display', 
                    'date_validation', 'commentaire_preview']
    list_filter = [ValidationStatusFilter, 'date_validation', 'validateur']
    search_fields = ['rapport__commande__notre_ref', 'rapport__commande__raison_sociale',
                     'validateur__username', 'validateur__email', 'commentaire']
    readonly_fields = ['validateur', 'date_validation']
    actions = [valider_rapports_action, demander_correction_action]
    fieldsets = (
        ('Validation', {
            'fields': ('rapport', 'validateur', 'status', 'commentaire')
        }),
        ('Dates', {
            'fields': ('date_validation',)
        }),
    )
    
    def status_display(self, obj):
        if obj.status == "valide":
            return format_html('<span style="color: green; font-weight: bold;">✅ Validé</span>')
        elif obj.status == "a_corriger":
            return format_html('<span style="color: orange; font-weight: bold;">⚠️ À corriger</span>')
        else:
            return format_html('<span style="color: blue; font-weight: bold;">⏳ En attente</span>')
    status_display.short_description = "Statut"
    
    def commentaire_preview(self, obj):
        if obj.commentaire and len(obj.commentaire) > 50:
            return obj.commentaire[:50] + "..."
        return obj.commentaire or "-"
    commentaire_preview.short_description = "Commentaire"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('rapport', 'rapport__commande', 'validateur')
    
    def save_model(self, request, obj, form, change):
        if not obj.validateur_id:
            obj.validateur = request.user
        
        # Créer un suivi de commande pour la validation
        if obj.status == "valide":
            SuiviCommande.objects.create(
                commande=obj.rapport.commande,
                user=request.user,
                action="Rapport validé",
                type="VALIDATION"
            )
            # Mettre à jour le statut de la commande
            obj.rapport.commande.status = "rapport_valide"
            obj.rapport.commande.save()
        
        elif obj.status == "a_corriger":
            SuiviCommande.objects.create(
                commande=obj.rapport.commande,
                user=request.user,
                action="Correction demandée sur le rapport",
                type="CORRECTION"
            )
        
        super().save_model(request, obj, form, change)


@admin.register(ReportRequest)
class ReportRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'request_id', 'buyer_name', 'country', 'city', 
                    'created_at', 'created_by']
    list_filter = ['country', 'city', 'created_at', 'created_by']
    search_fields = ['request_id', 'buyer_name', 'vat_number', 
                     'registration_number', 'address', 'city']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    fieldsets = (
        ('Identifiants', {
            'fields': ('request_id', 'requester_id', 'vat_number', 
                      'registration_number', 'source_id')
        }),
        ('Entreprise', {
            'fields': ('buyer_name', 'country')
        }),
        ('Adresse', {
            'fields': ('address', 'postal_code', 'city')
        }),
        ('Contacts', {
            'fields': ('buyer_phone_number', 'buyer_fax_number')
        }),
        ('Commentaire', {
            'fields': ('comment',)
        }),
        ('Système', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('created_by')


# =============================================================================
# DASHBOARD PERSONNALISÉ
# =============================================================================

class CommandesDashboard(admin.ModelAdmin):
    """Tableau de bord personnalisé pour les commandes"""
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Statistiques globales
        stats = {
            'total': Commande.objects.count(),
            'nouvelles': Commande.objects.filter(status='nouvelle').count(),
            'en_cours': Commande.objects.filter(status='en_cours').count(),
            'rapport_soumis': Commande.objects.filter(status='rapport_soumis').count(),
            'rapport_valide': Commande.objects.filter(status='rapport_valide').count(),
            'envoye_client': Commande.objects.filter(status='envoye_client').count(),
            'terminees': Commande.objects.filter(status='terminee').count(),
            'annulees': Commande.objects.filter(status='annulee').count(),
        }
        
        # Commandes en retard
        now = timezone.now().date()
        en_retard = Commande.objects.filter(date_rapport__lt=now).count()
        
        extra_context.update({
            'stats': stats,
            'en_retard': en_retard,
            'dashboard': True,
        })
        
        return super().changelist_view(request, extra_context)


# =============================================================================
# SITE HEADER PERSONNALISÉ
# =============================================================================

admin.site.site_header = "Gestion des Commandes et Rapports"
admin.site.site_title = "Admin Commandes"
admin.site.index_title = "Tableau de bord des commandes"

# Surcharger la vue d'accueil pour ajouter des statistiques
admin.site.index_template = 'admin/commandes_index.html'










# =============================================================================
# ACTIONS PERSONNALISÉES
# =============================================================================

def archiver_alertes_action(modeladmin, request, queryset):
    """Action pour archiver des alertes"""
    for alerte in queryset:
        alerte.reference = f"ARCHIVE-{alerte.reference}"
        alerte.save()
    modeladmin.message_user(request, f"{queryset.count()} alerte(s) archivée(s).")
archiver_alertes_action.short_description = "Archiver les alertes sélectionnées"

def notifier_clients_action(modeladmin, request, queryset):
    """Action pour notifier les clients concernés par des alertes"""
    for warning in queryset:
        for acheteur in warning.acheteurs.all():
            # Créer une notification pour chaque client concerné
            clients = acheteur.commandes.values_list('client', flat=True).distinct()
            for client_id in clients:
                NotifClient.objects.create(
                    client_id=client_id,
                )
                # Ajouter l'acheteur à la notification
                notif = NotifClient.objects.last()
                notif.acheteurs.add(acheteur)
    
    modeladmin.message_user(request, f"{queryset.count()} warning(s) notifié(s) aux clients concernés.")
notifier_clients_action.short_description = "Notifier les clients concernés"

def exporter_alertes_action(modeladmin, request, queryset):
    """Action pour exporter des alertes (simulation)"""
    # Cette action pourrait générer un fichier CSV ou PDF
    # Pour l'instant, on simule juste l'export
    from django.http import HttpResponse
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Référence', 'Objet', 'Message', 'Date création', 'Documents'])
    
    for alerte in queryset:
        documents = ", ".join([doc.titre for doc in alerte.documents_alerte.all()])
        writer.writerow([
            alerte.reference,
            alerte.objet,
            alerte.content[:100],  # Premiers 100 caractères
            alerte.created_at.strftime('%d/%m/%Y %H:%M'),
            documents
        ])
    
    output.seek(0)
    response = HttpResponse(output, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="alertes_export.csv"'
    modeladmin.message_user(request, "Export CSV prêt.")
    return response
exporter_alertes_action.short_description = "Exporter en CSV"

def ajouter_aux_favoris_action(modeladmin, request, queryset):
    """Action pour ajouter des alertes aux favoris (simulation)"""
    # Cette action pourrait utiliser un champ 'favori' ou une relation ManyToMany
    # Pour l'instant, on ajoute un tag dans le message
    for alerte in queryset:
        if not alerte.content.startswith("⭐ "):
            alerte.content = f"⭐ {alerte.content}"
            alerte.save()
    
    modeladmin.message_user(request, f"{queryset.count()} alerte(s) marquée(s) comme favorite(s).")
ajouter_aux_favoris_action.short_description = "Ajouter aux favoris"


# =============================================================================
# FILTRES PERSONNALISÉS
# =============================================================================

class AlerteDateFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les alertes par date"""
    title = _('Période de création')
    parameter_name = 'periode'

    def lookups(self, request, model_admin):
        return (
            ('aujourdhui', _("Aujourd'hui")),
            ('cette_semaine', _("Cette semaine")),
            ('ce_mois', _("Ce mois")),
            ('cette_annee', _("Cette année")),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'aujourdhui':
            today = now.date()
            return queryset.filter(created_at__date=today)
        elif self.value() == 'cette_semaine':
            week_start = now - timedelta(days=now.weekday())
            return queryset.filter(created_at__gte=week_start)
        elif self.value() == 'ce_mois':
            return queryset.filter(created_at__year=now.year, created_at__month=now.month)
        elif self.value() == 'cette_annee':
            return queryset.filter(created_at__year=now.year)
        return queryset


class WarningAcheteurFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les warnings par acheteur"""
    title = _('Acheteur concerné')
    parameter_name = 'acheteur'

    def lookups(self, request, model_admin):
        # Récupérer les acheteurs qui ont des warnings
        acheteurs_ids = Warning.objects.values_list('acheteurs', flat=True).distinct()
        from .models import Acheteur
        acheteurs = Acheteur.objects.filter(id__in=acheteurs_ids)
        return [(a.id, a.nom) for a in acheteurs]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(acheteurs__id=self.value())
        return queryset


class DocumentTypeFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les types de documents"""
    title = _('Type de document')
    parameter_name = 'type_document'

    def lookups(self, request, model_admin):
        return [
            ('pdf', 'PDF'),
            ('doc', 'Word'),
            ('excel', 'Excel'),
            ('image', 'Image'),
            ('autre', 'Autre'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'pdf':
            return queryset.filter(fichier__endswith='.pdf')
        elif self.value() == 'doc':
            return queryset.filter(fichier__endswith__in=['.doc', '.docx'])
        elif self.value() == 'excel':
            return queryset.filter(fichier__endswith__in=['.xls', '.xlsx', '.csv'])
        elif self.value() == 'image':
            return queryset.filter(fichier__endswith__in=['.jpg', '.jpeg', '.png', '.gif'])
        elif self.value() == 'autre':
            extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.jpg', '.jpeg', '.png', '.gif']
            return queryset.exclude(fichier__endswith__in=extensions)
        return queryset


# =============================================================================
# INLINES
# =============================================================================

class DocumentAlerteInline(admin.TabularInline):
    model = DocumentAlerte
    extra = 1
    fields = ['titre', 'fichier', 'preview_document']
    readonly_fields = ['preview_document_field']  # changer le nom
    verbose_name = "Document associé"
    verbose_name_plural = "Documents associés"
    classes = ['collapse']
    
    def preview_document_field(self, obj):
        # Implémenter la prévisualisation
        if obj.document:
            return format_html(f'<a href="{obj.document.url}" target="_blank">Voir</a>')
        return "Aucun document"
    preview_document_field.short_description = "Prévisualisation"

class WarningAttachmentInline(admin.TabularInline):
    model = WarningAttachment
    extra = 1
    fields = ['upload', 'uploaded_at', 'file_preview']
    readonly_fields = ['file_preview_field']  # changer le nom
    verbose_name = "Pièce jointe"
    verbose_name_plural = "Pièces jointes"
    classes = ['collapse']
    
    def file_preview_field(self, obj):
        if obj.file:
            return format_html(f'<a href="{obj.file.url}" target="_blank">Télécharger</a>')
        return "Aucun fichier"
    file_preview_field.short_description = "Fichier"


# =============================================================================
# MODEL ADMINS
# =============================================================================

@admin.register(Alerte)
class AlerteAdmin(admin.ModelAdmin):
    list_display = ['id', 'reference', 'objet', 'content_preview', 
                    'created_at', 'documents_count', 'urgence_level']
    list_filter = [AlerteDateFilter, 'created_at']
    search_fields = ['reference', 'objet', 'content']
    readonly_fields = ['created_at', 'updated_at', 'documents_list', 
                      'urgence_level_display']
    actions = [archiver_alertes_action, exporter_alertes_action, 
               ajouter_aux_favoris_action]
    inlines = [DocumentAlerteInline]
    
    fieldsets = (
        ('Informations alerte', {
            'fields': ('reference', 'objet', 'content', 'urgence_level_display')
        }),
        ('Documents associés', {
            'fields': ('documents_list',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        if len(obj.content) > 100:
            return obj.content[:100] + "..."
        return obj.content
    content_preview.short_description = "Message"
    
    def documents_count(self, obj):
        count = obj.documents_alerte.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #e3f2fd; padding: 2px 8px; border-radius: 12px; font-weight: bold;">📎 {}</span>',
                count
            )
        return "-"
    documents_count.short_description = "Documents"
    
    def urgence_level(self, obj):
        # Déterminer le niveau d'urgence en fonction du contenu
        content_lower = obj.content.lower()
        if any(word in content_lower for word in ['urgent', 'important', 'critique', 'grave']):
            return format_html('<span style="color: red; font-weight: bold;">⚠️ Urgent</span>')
        elif any(word in content_lower for word in ['attention', 'alerte', 'signaler']):
            return format_html('<span style="color: orange; font-weight: bold;">⚠️ Attention</span>')
        else:
            return format_html('<span style="color: blue;">ℹ️ Information</span>')
    urgence_level.short_description = "Urgence"
    
    def urgence_level_display(self, obj):
        return self.urgence_level(obj)
    urgence_level_display.short_description = "Niveau d'urgence"
    
    def documents_list(self, obj):
        documents = obj.documents_alerte.all()
        if documents:
            html = '<div style="margin-top: 10px;">'
            for doc in documents:
                html += format_html(
                    '<div style="margin-bottom: 5px; padding: 5px; background: #f5f5f5; border-radius: 3px;">'
                    '📎 <a href="{}" target="_blank">{}</a>'
                    '</div>',
                    doc.fichier.url if doc.fichier else '#',
                    doc.titre
                )
            html += '</div>'
            return mark_safe(html)
        return "Aucun document"
    documents_list.short_description = "Liste des documents"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('documents_alerte')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ajouter des attributs HTML aux champs
        form.base_fields['reference'].widget.attrs['placeholder'] = 'Ex: ALERT-2024-001'
        form.base_fields['objet'].widget.attrs['placeholder'] = 'Ex: Délai de paiement dépassé'
        
        # Augmenter la hauteur de la zone de texte
        form.base_fields['content'].widget.attrs['rows'] = 5
        form.base_fields['content'].widget.attrs['style'] = 'width: 95%;'
        
        return form
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        alerte = self.get_object(request, object_id)
        
        # Ajouter des statistiques au contexte
        extra_context['statistiques'] = {
            'total_documents': alerte.documents_alerte.count(),
            'age_alerte': (timezone.now() - alerte.created_at).days,
        }
        
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(DocumentAlerte)
class DocumentAlerteAdmin(admin.ModelAdmin):
    list_display = ['id', 'alerte_link', 'titre', 'fichier_link', 
                    'file_type', 'file_size', 'created_at']
    list_filter = [DocumentTypeFilter, 'created_at', 'alerte']
    search_fields = ['alerte__reference', 'alerte__objet', 'titre', 'fichier']
    readonly_fields = ['file_preview', 'file_type_display', 'file_size_display', 
                      'created_at', 'updated_at']
    fieldsets = (
        ('Document', {
            'fields': ('alerte', 'titre', 'fichier', 'file_preview')
        }),
        ('Informations fichier', {
            'fields': ('file_type_display', 'file_size_display'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def alerte_link(self, obj):
        if obj.alerte:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:app_alerte_change', args=[obj.alerte.id]),
                f"{obj.alerte.reference} - {obj.alerte.objet[:30]}..."
            )
        return "-"
    alerte_link.short_description = "Alerte"
    
    def fichier_link(self, obj):
        if obj.fichier:
            filename = obj.fichier.name.split('/')[-1]
            return format_html(
                '<a href="{}" target="_blank">📄 {}</a>',
                obj.fichier.url,
                filename[:30] + "..." if len(filename) > 30 else filename
            )
        return "-"
    fichier_link.short_description = "Fichier"
    
    def file_type(self, obj):
        if obj.fichier:
            ext = obj.fichier.name.split('.')[-1].lower() if '.' in obj.fichier.name else ''
            types = {
                'pdf': '📕 PDF',
                'doc': '📘 Word',
                'docx': '📘 Word',
                'xls': '📗 Excel',
                'xlsx': '📗 Excel',
                'csv': '📗 CSV',
                'jpg': '🖼️ Image',
                'jpeg': '🖼️ Image',
                'png': '🖼️ Image',
                'gif': '🖼️ Image',
            }
            return types.get(ext, f'📁 {ext.upper()}' if ext else '📁 Inconnu')
        return "-"
    file_type.short_description = "Type"
    
    def file_size(self, obj):
        if obj.fichier:
            try:
                size = obj.fichier.size
                if size < 1024:
                    return f"{size} octets"
                elif size < 1024 * 1024:
                    return f"{size/1024:.1f} Ko"
                else:
                    return f"{size/(1024*1024):.1f} Mo"
            except:
                return "N/A"
        return "-"
    file_size.short_description = "Taille"
    
    def file_preview(self, obj):
        if obj.fichier:
            ext = obj.fichier.name.split('.')[-1].lower() if '.' in obj.fichier.name else ''
            if ext in ['jpg', 'jpeg', 'png', 'gif']:
                return format_html(
                    '<div style="margin: 10px 0;">'
                    '<a href="{}" target="_blank">'
                    '<img src="{}" style="max-width: 300px; max-height: 200px; border: 1px solid #ddd;" />'
                    '</a>'
                    '</div>',
                    obj.fichier.url,
                    obj.fichier.url
                )
            else:
                filename = obj.fichier.name.split('/')[-1]
                return format_html(
                    '<div style="margin: 10px 0;">'
                    '<a href="{}" target="_blank" style="display: inline-block; padding: 10px; background: #f0f0f0; border-radius: 5px; text-decoration: none; color: #333;">'
                    '📄 Télécharger "{}"'
                    '</a>'
                    '</div>',
                    obj.fichier.url,
                    filename
                )
        return "Aucun fichier"
    file_preview.short_description = "Prévisualisation"
    
    def file_type_display(self, obj):
        return self.file_type(obj)
    file_type_display.short_description = "Type de fichier"
    
    def file_size_display(self, obj):
        return self.file_size(obj)
    file_size_display.short_description = "Taille du fichier"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('alerte')


@admin.register(Warning)
class WarningAdmin(admin.ModelAdmin):
    list_display = ['id', 'titre_preview', 'description_preview', 
                    'acheteurs_count', 'created_by', 'created_at', 
                    'attachments_count']
    list_filter = [WarningAcheteurFilter, 'created_at', 'created_by']
    search_fields = ['titre', 'description', 'acheteurs__nom', 'created_by__username']
    readonly_fields = ['created_at', 'acheteurs_list', 'attachments_list']
    actions = [notifier_clients_action]
    inlines = [WarningAttachmentInline]
    filter_horizontal = ['acheteurs']
    
    fieldsets = (
        ('Avertissement', {
            'fields': ('titre', 'description')
        }),
        ('Destinataires', {
            'fields': ('acheteurs', 'acheteurs_list')
        }),
        ('Pièces jointes', {
            'fields': ('attachments_list',),
            'classes': ('collapse',)
        }),
        ('Création', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def titre_preview(self, obj):
        if len(obj.titre) > 50:
            return obj.titre[:50] + "..."
        return obj.titre
    titre_preview.short_description = "Titre"
    
    def description_preview(self, obj):
        if len(obj.description) > 100:
            return obj.description[:100] + "..."
        return obj.description or "-"
    description_preview.short_description = "Description"
    
    def acheteurs_count(self, obj):
        count = obj.acheteurs.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #ffebee; padding: 2px 8px; border-radius: 12px; font-weight: bold;">👥 {}</span>',
                count
            )
        return "-"
    acheteurs_count.short_description = "Acheteurs"
    
    def attachments_count(self, obj):
        count = obj.warning_attachments.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #e8f5e8; padding: 2px 8px; border-radius: 12px; font-weight: bold;">📎 {}</span>',
                count
            )
        return "-"
    attachments_count.short_description = "Pièces jointes"
    
    def acheteurs_list(self, obj):
        acheteurs = obj.acheteurs.all()
        if acheteurs:
            html = '<ul style="margin-top: 10px; padding-left: 20px;">'
            for acheteur in acheteurs:
                html += format_html(
                    '<li><a href="{}" target="_blank">{}</a></li>',
                    reverse('admin:app_acheteur_change', args=[acheteur.id]),
                    acheteur.nom
                )
            html += '</ul>'
            return mark_safe(html)
        return "Aucun acheteur associé"
    acheteurs_list.short_description = "Liste des acheteurs"
    
    def attachments_list(self, obj):
        attachments = obj.warning_attachments.all()
        if attachments:
            html = '<div style="margin-top: 10px;">'
            for attachment in attachments:
                html += format_html(
                    '<div style="margin-bottom: 5px; padding: 5px; background: #f5f5f5; border-radius: 3px;">'
                    '📎 <a href="{}" target="_blank">{}</a>'
                    '</div>',
                    attachment.upload.url if attachment.upload else '#',
                    attachment.filename()
                )
            html += '</div>'
            return mark_safe(html)
        return "Aucune pièce jointe"
    attachments_list.short_description = "Liste des pièces jointes"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('acheteurs', 'warning_attachments').select_related('created_by')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Augmenter la hauteur de la zone de texte
        form.base_fields['description'].widget.attrs['rows'] = 5
        form.base_fields['description'].widget.attrs['style'] = 'width: 95%;'
        
        return form


@admin.register(WarningAttachment)
class WarningAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'warning_link', 'filename', 'upload_link', 
                    'file_size', 'uploaded_at']
    list_filter = ['uploaded_at', 'warning']
    search_fields = ['warning__titre', 'upload']
    readonly_fields = ['file_preview', 'filename_display', 'file_size_display', 
                      'uploaded_at']
    fieldsets = (
        ('Pièce jointe', {
            'fields': ('warning', 'upload', 'file_preview')
        }),
        ('Informations fichier', {
            'fields': ('filename_display', 'file_size_display'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    def warning_link(self, obj):
        if obj.warning:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:app_warning_change', args=[obj.warning.id]),
                obj.warning.titre[:50] + "..." if len(obj.warning.titre) > 50 else obj.warning.titre
            )
        return "-"
    warning_link.short_description = "Warning"
    
    def filename(self, obj):
        return obj.filename()
    filename.short_description = "Nom du fichier"
    
    def upload_link(self, obj):
        if obj.upload:
            return format_html(
                '<a href="{}" target="_blank">📄 Télécharger</a>',
                obj.upload.url
            )
        return "-"
    upload_link.short_description = "Fichier"
    
    def file_size(self, obj):
        if obj.upload:
            try:
                size = obj.upload.size
                if size < 1024:
                    return f"{size} octets"
                elif size < 1024 * 1024:
                    return f"{size/1024:.1f} Ko"
                else:
                    return f"{size/(1024*1024):.1f} Mo"
            except:
                return "N/A"
        return "-"
    file_size.short_description = "Taille"
    
    def file_preview(self, obj):
        if obj.upload:
            filename = obj.upload.name.lower()
            if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                return format_html(
                    '<div style="margin: 10px 0;">'
                    '<a href="{}" target="_blank">'
                    '<img src="{}" style="max-width: 300px; max-height: 200px; border: 1px solid #ddd;" />'
                    '</a>'
                    '</div>',
                    obj.upload.url,
                    obj.upload.url
                )
            else:
                return format_html(
                    '<div style="margin: 10px 0;">'
                    '<a href="{}" target="_blank" style="display: inline-block; padding: 10px; background: #f0f0f0; border-radius: 5px; text-decoration: none; color: #333;">'
                    '📄 Télécharger "{}"'
                    '</a>'
                    '</div>',
                    obj.upload.url,
                    obj.filename()
                )
        return "Aucun fichier"
    file_preview.short_description = "Prévisualisation"
    
    def filename_display(self, obj):
        return obj.filename()
    filename_display.short_description = "Nom du fichier"
    
    def file_size_display(self, obj):
        return self.file_size(obj)
    file_size_display.short_description = "Taille du fichier"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('warning')


@admin.register(NotifClient)
class NotifClientAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'acheteurs_count', 'created_display']
    list_filter = ['client', 'acheteurs']
    search_fields = ['client__username', 'client__email', 'acheteurs__nom']
    readonly_fields = ['acheteurs_list', 'created_display_field']
    filter_horizontal = ['acheteurs']
    
    fieldsets = (
        ('Notification client', {
            'fields': ('client', 'acheteurs', 'acheteurs_list')
        }),
        ('Informations', {
            'fields': ('created_display_field',),
            'classes': ('collapse',)
        }),
    )
    
    def acheteurs_count(self, obj):
        count = obj.acheteurs.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #e3f2fd; padding: 2px 8px; border-radius: 12px; font-weight: bold;">👥 {}</span>',
                count
            )
        return "-"
    acheteurs_count.short_description = "Acheteurs concernés"
    
    def created_display(self, obj):
        # Ce modèle n'a pas de created_at, on utilise l'ID comme approximation
        return f"Notif #{obj.id}"
    created_display.short_description = "Référence"
    
    def acheteurs_list(self, obj):
        acheteurs = obj.acheteurs.all()
        if acheteurs:
            html = '<ul style="margin-top: 10px; padding-left: 20px;">'
            for acheteur in acheteurs:
                html += format_html(
                    '<li><a href="{}" target="_blank">{}</a></li>',
                    reverse('admin:app_acheteur_change', args=[acheteur.id]),
                    acheteur.nom
                )
            html += '</ul>'
            return mark_safe(html)
        return "Aucun acheteur associé"
    acheteurs_list.short_description = "Liste des acheteurs"
    
    def created_display_field(self, obj):
        return self.created_display(obj)
    created_display_field.short_description = "Référence de notification"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('acheteurs').select_related('client')


# =============================================================================
# DASHBOARD ALERTES
# =============================================================================

class AlertesDashboard(admin.ModelAdmin):
    """Tableau de bord personnalisé pour les alertes"""
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Statistiques globales
        from django.db.models import Count
        stats = {
            'total_alertes': Alerte.objects.count(),
            'total_warnings': Warning.objects.count(),
            'alertes_recentes': Alerte.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'warnings_recents': Warning.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
        }
        
        # Alertes avec documents
        alertes_avec_docs = Alerte.objects.annotate(
            doc_count=Count('documents_alerte')
        ).filter(doc_count__gt=0).count()
        
        # Warnings avec pièces jointes
        warnings_avec_pj = Warning.objects.annotate(
            pj_count=Count('warning_attachments')
        ).filter(pj_count__gt=0).count()
        
        extra_context.update({
            'stats': stats,
            'alertes_avec_docs': alertes_avec_docs,
            'warnings_avec_pj': warnings_avec_pj,
            'dashboard': True,
        })
        
        return super().changelist_view(request, extra_context)


# =============================================================================
# SITE HEADER PERSONNALISÉ
# =============================================================================

admin.site.site_header = "Gestion des Alertes et Warnings"
admin.site.site_title = "Admin Alertes"
admin.site.index_title = "Tableau de bord des alertes"

# Surcharger la vue d'accueil pour ajouter des statistiques
admin.site.index_template = 'admin/alertes_index.html'


# =============================================================================
# CSS ET JS PERSONNALISÉS
# =============================================================================

class Media:
    css = {
        'all': ('admin/css/alertes.css',)
    }
    
    js = ('admin/js/alertes.js',)
    
    
    
    
    


# =============================================================================
# ACTIONS PERSONNALISÉES
# =============================================================================

def reenvoyer_emails_action(modeladmin, request, queryset):
    """Action pour réenvoyer des emails"""
    for mail in queryset.filter(success=False):
        # Logique de réenvoi d'email
        # À implémenter selon votre service d'email
        mail.success = True
        mail.save()
    
    modeladmin.message_user(request, f"{queryset.filter(success=False).count()} email(s) marqué(s) pour réenvoi.")
reenvoyer_emails_action.short_description = "Réenvoyer les emails"

def generer_rapport_telechargements_action(modeladmin, request, queryset):
    """Action pour générer un rapport des téléchargements"""
    from django.http import HttpResponse
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Client', 'Acheteur', 'Email client'])
    
    for download in queryset:
        writer.writerow([
            download.date.strftime('%d/%m/%Y %H:%M'),
            download.client.username,
            download.acheteur.nom,
            download.client.email
        ])
    
    output.seek(0)
    response = HttpResponse(output, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="telechargements_rapport.csv"'
    modeladmin.message_user(request, "Rapport CSV des téléchargements généré.")
    return response
generer_rapport_telechargements_action.short_description = "Générer rapport CSV"

def exporter_liste_references_action(modeladmin, request, queryset):
    """Action pour exporter une liste de références"""
    model_type = modeladmin.model.__name__
    filename = f"{model_type.lower()}_export.csv"
    
    from django.http import HttpResponse
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # En-têtes selon le type de modèle
    if model_type == 'Locaux':
        writer.writerow(['ID', 'Nom'])
        for item in queryset:
            writer.writerow([item.id, item.nom])
    elif model_type in ['ListeConditionAchat', 'ListeConditionVente']:
        writer.writerow(['ID', 'Nom'])
        for item in queryset:
            writer.writerow([item.id, item.nom])
    elif model_type in ['ListeComportementsPaiement', 'ListeInformationsRating', 'ListeInformationsAvisCommercial']:
        writer.writerow(['ID', 'Libellé', 'Couleur'])
        for item in queryset:
            writer.writerow([item.id, item.libelle, item.couleur])
    elif model_type == 'ListeImportation':
        writer.writerow(['ID', 'Libellé'])
        for item in queryset:
            writer.writerow([item.id, item.libelle[:200]])  # Limiter la longueur
    
    output.seek(0)
    response = HttpResponse(output, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    modeladmin.message_user(request, f"Export CSV de {model_type} généré.")
    return response
exporter_liste_references_action.short_description = "Exporter en CSV"

def nettoyer_anciens_logs_action(modeladmin, request, queryset):
    """Action pour nettoyer les anciens logs d'activité"""
    date_limite = timezone.now() - timedelta(days=365)  # 1 an
    anciens_logs = ActivityLog.objects.filter(date__lt=date_limite)
    count = anciens_logs.count()
    anciens_logs.delete()
    
    modeladmin.message_user(request, f"{count} ancien(s) log(s) d'activité supprimé(s).")
nettoyer_anciens_logs_action.short_description = "Nettoyer les anciens logs"

def archiver_logs_action(modeladmin, request, queryset):
    """Action pour archiver des logs d'activité"""
    # Ici, vous pourriez exporter les logs vers un fichier avant de les supprimer
    # Pour l'instant, on marque juste avec un préfixe
    for log in queryset:
        if not log.action.startswith("[ARCHIVE] "):
            log.action = f"[ARCHIVE] {log.action}"
            log.save()
    
    modeladmin.message_user(request, f"{queryset.count()} log(s) d'activité archivé(s).")
archiver_logs_action.short_description = "Archiver les logs"


# =============================================================================
# FILTRES PERSONNALISÉS
# =============================================================================

class MailSuccessFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les emails par succès"""
    title = _('Succès d\'envoi')
    parameter_name = 'success'

    def lookups(self, request, model_admin):
        return (
            ('success', _('✅ Succès')),
            ('failed', _('❌ Échec')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'success':
            return queryset.filter(success=True)
        elif self.value() == 'failed':
            return queryset.filter(success=False)
        return queryset


class MailDateFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les emails par date"""
    title = _('Date d\'envoi')
    parameter_name = 'date_envoi'

    def lookups(self, request, model_admin):
        return (
            ('today', _("Aujourd'hui")),
            ('week', _("Cette semaine")),
            ('month', _("Ce mois")),
            ('year', _("Cette année")),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            today = now.date()
            return queryset.filter(date_sent__date=today)
        elif self.value() == 'week':
            week_start = now - timedelta(days=now.weekday())
            return queryset.filter(date_sent__gte=week_start)
        elif self.value() == 'month':
            return queryset.filter(date_sent__year=now.year, date_sent__month=now.month)
        elif self.value() == 'year':
            return queryset.filter(date_sent__year=now.year)
        return queryset


class DocDownloadDateFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les téléchargements par date"""
    title = _('Date de téléchargement')
    parameter_name = 'date_download'

    def lookups(self, request, model_admin):
        return (
            ('today', _("Aujourd'hui")),
            ('week', _("Cette semaine")),
            ('month', _("Ce mois")),
            ('year', _("Cette année")),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            today = now.date()
            return queryset.filter(date__date=today)
        elif self.value() == 'week':
            week_start = now - timedelta(days=now.weekday())
            return queryset.filter(date__gte=week_start)
        elif self.value() == 'month':
            return queryset.filter(date__year=now.year, date__month=now.month)
        elif self.value() == 'year':
            return queryset.filter(date__year=now.year)
        return queryset


class ActivityLogTypeFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les types de logs d'activité"""
    title = _('Type d\'activité')
    parameter_name = 'type_activite'

    def lookups(self, request, model_admin):
        # Analyse des types d'actions courants
        actions = ActivityLog.objects.values_list('action', flat=True).distinct()
        types = set()
        for action in actions:
            if action:
                # Extraire le type d'action (premier mot ou partie)
                if 'created' in action.lower():
                    types.add('creation')
                elif 'updated' in action.lower():
                    types.add('modification')
                elif 'deleted' in action.lower():
                    types.add('suppression')
                elif 'viewed' in action.lower() or 'accessed' in action.lower():
                    types.add('consultation')
                elif 'logged' in action.lower():
                    types.add('connexion')
        
        return [
            (type_name, _(type_name.capitalize()))
            for type_name in sorted(types)
        ]

    def queryset(self, request, queryset):
        if self.value() == 'creation':
            return queryset.filter(action__icontains='created')
        elif self.value() == 'modification':
            return queryset.filter(action__icontains='updated')
        elif self.value() == 'suppression':
            return queryset.filter(action__icontains='deleted')
        elif self.value() == 'consultation':
            return queryset.filter(action__icontains__in=['viewed', 'accessed'])
        elif self.value() == 'connexion':
            return queryset.filter(action__icontains='logged')
        return queryset


class ColorFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les couleurs"""
    title = _('Couleur')
    parameter_name = 'couleur'

    def lookups(self, request, model_admin):
        # Récupérer les couleurs disponibles pour ce modèle
        colors = model_admin.model.objects.values_list('couleur', flat=True).distinct()
        return [(color, color) for color in sorted(colors) if color]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(couleur=self.value())
        return queryset


# =============================================================================
# INLINES
# =============================================================================

class MailAttachmentInline(admin.TabularInline):
    model = MailAttachment
    extra = 1
    fields = ['upload', 'file_preview', 'uploaded_at_display']
    readonly_fields = ['file_preview', 'uploaded_at_display']
    verbose_name = "Pièce jointe"
    verbose_name_plural = "Pièces jointes"
    classes = ['collapse']
    
    def file_preview(self, obj):
        if obj.upload:
            filename = obj.upload.name.lower()
            if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                return format_html(
                    '<div style="margin: 5px 0;">'
                    '<a href="{}" target="_blank">'
                    '<img src="{}" style="max-width: 100px; max-height: 80px; border: 1px solid #ddd;" />'
                    '</a>'
                    '</div>',
                    obj.upload.url,
                    obj.upload.url
                )
            else:
                return format_html(
                    '<div style="margin: 5px 0;">'
                    '📎 <a href="{}" target="_blank">{}</a>'
                    '</div>',
                    obj.upload.url,
                    obj.upload.name.split('/')[-1][:30]
                )
        return "Aucun fichier"
    file_preview.short_description = "Fichier"
    
    def uploaded_at_display(self, obj):
        if hasattr(obj, 'uploaded_at'):
            return obj.uploaded_at.strftime('%d/%m/%Y %H:%M')
        return "-"
    uploaded_at_display.short_description = "Date d'upload"


class CommandeMailInline(admin.TabularInline):
    """Inline pour afficher les commandes associées à un mail"""
    model = MailInfo.commands.through
    extra = 0
    verbose_name = "Commande associée"
    verbose_name_plural = "Commandes associées"
    classes = ['collapse']
    readonly_fields = ['commande_link']
    
    def commande_link(self, obj):
        if hasattr(obj, 'commande'):
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:app_commande_change', args=[obj.commande.id]),
                obj.commande.notre_ref or f"Commande #{obj.commande.id}"
            )
        return "-"
    commande_link.short_description = "Commande"


# =============================================================================
# MODEL ADMINS
# =============================================================================

@admin.register(MailInfo)
class MailInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'date_sent_display', 'user', 'subject_preview', 
                    'success_display', 'commands_count', 'attachments_count', 
                    'cc_count']
    list_filter = [MailSuccessFilter, MailDateFilter, 'user', 'date_sent']
    search_fields = ['user__username', 'user__email', 'subject', 'cc_emails']
    readonly_fields = ['date_sent', 'success_display_field', 'commands_list', 
                      'attachments_list', 'cc_list_display', 'formats_generes_display']
    actions = [reenvoyer_emails_action]
    inlines = [MailAttachmentInline, CommandeMailInline]
    
    fieldsets = (
        ('Informations email', {
            'fields': ('user', 'subject', 'success_display_field')
        }),
        ('Destinataires', {
            'fields': ('cc_emails', 'cc_list_display')
        }),
        ('Commandes associées', {
            'fields': ('commands_list',),
            'classes': ('collapse',)
        }),
        ('Pièces jointes', {
            'fields': ('attachments_list',),
            'classes': ('collapse',)
        }),
        ('Paramètres', {
            'fields': ('custom_days', 'formats_generes_display'),
            'classes': ('collapse',)
        }),
        ('Date d\'envoi', {
            'fields': ('date_sent',),
            'classes': ('collapse',)
        }),
    )
    
    def date_sent_display(self, obj):
        return obj.date_sent.strftime('%d/%m/%Y %H:%M')
    date_sent_display.short_description = "Date d'envoi"
    
    def subject_preview(self, obj):
        if obj.subject and len(obj.subject) > 50:
            return obj.subject[:50] + "..."
        return obj.subject or "Sans objet"
    subject_preview.short_description = "Sujet"
    
    def success_display(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✅ Succès</span>')
        else:
            return format_html('<span style="color: red;">❌ Échec</span>')
    success_display.short_description = "Statut"
    
    def commands_count(self, obj):
        count = obj.commands.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #e3f2fd; padding: 2px 8px; border-radius: 12px; font-weight: bold;">📦 {}</span>',
                count
            )
        return "-"
    commands_count.short_description = "Commandes"
    
    def attachments_count(self, obj):
        count = obj.mailattachment_set.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #e8f5e8; padding: 2px 8px; border-radius: 12px; font-weight: bold;">📎 {}</span>',
                count
            )
        return "-"
    attachments_count.short_description = "Pièces jointes"
    
    def cc_count(self, obj):
        if obj.cc_emails:
            emails = [e.strip() for e in obj.cc_emails.split(';') if e.strip()]
            return format_html(
                '<span style="background-color: #fff3e0; padding: 2px 8px; border-radius: 12px; font-weight: bold;">👥 {}</span>',
                len(emails)
            )
        return "-"
    cc_count.short_description = "CC"
    
    def success_display_field(self, obj):
        return self.success_display(obj)
    success_display_field.short_description = "Statut d'envoi"
    
    def commands_list(self, obj):
        commands = obj.commands.all()
        if commands:
            html = '<ul style="margin-top: 10px; padding-left: 20px;">'
            for commande in commands:
                html += format_html(
                    '<li><a href="{}" target="_blank">{}</a></li>',
                    reverse('admin:app_commande_change', args=[commande.id]),
                    f"{commande.notre_ref} - {commande.raison_sociale}"
                )
            html += '</ul>'
            return mark_safe(html)
        return "Aucune commande associée"
    commands_list.short_description = "Liste des commandes"
    
    def attachments_list(self, obj):
        attachments = obj.mailattachment_set.all()
        if attachments:
            html = '<ul style="margin-top: 10px; padding-left: 20px;">'
            for attachment in attachments:
                html += format_html(
                    '<li><a href="{}" target="_blank">{}</a></li>',
                    attachment.upload.url if attachment.upload else '#',
                    attachment.upload.name.split('/')[-1] if attachment.upload else 'Fichier'
                )
            html += '</ul>'
            return mark_safe(html)
        return "Aucune pièce jointe"
    attachments_list.short_description = "Liste des pièces jointes"
    
    def cc_list_display(self, obj):
        emails = obj.get_cc_list()
        if emails:
            html = '<ul style="margin-top: 10px; padding-left: 20px;">'
            for email in emails:
                html += format_html('<li>{}</li>', email)
            html += '</ul>'
            return mark_safe(html)
        return "Aucun email en CC"
    cc_list_display.short_description = "Liste des emails en CC"
    
    def formats_generes_display(self, obj):
        formats = obj.formats_generes or []
        if formats:
            html = '<ul style="margin-top: 10px; padding-left: 20px;">'
            for fmt in formats:
                html += format_html('<li>{}</li>', fmt)
            html += '</ul>'
            return mark_safe(html)
        return "Aucun format généré"
    formats_generes_display.short_description = "Formats générés"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('commands', 'mailattachment_set')


@admin.register(MailAttachment)
class MailAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'upload_link', 'mailinfo_link', 'file_type', 
                    'file_size', 'upload_date']
    list_filter = ['mailinfo', 'upload']
    search_fields = ['upload', 'mailinfo__user__username']
    readonly_fields = ['file_preview', 'file_type_display', 'file_size_display', 
                      'upload_date_display']
    fieldsets = (
        ('Pièce jointe', {
            'fields': ('mailinfo', 'upload', 'file_preview')
        }),
        ('Informations fichier', {
            'fields': ('file_type_display', 'file_size_display'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('upload_date_display',),
            'classes': ('collapse',)
        }),
    )
    
    def upload_link(self, obj):
        if obj.upload:
            filename = obj.upload.name.split('/')[-1]
            return format_html(
                '<a href="{}" target="_blank">📎 {}</a>',
                obj.upload.url,
                filename[:30] + "..." if len(filename) > 30 else filename
            )
        return "-"
    upload_link.short_description = "Fichier"
    
    def mailinfo_link(self, obj):
        if obj.mailinfo:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:app_mailinfo_change', args=[obj.mailinfo.id]),
                f"Mail #{obj.mailinfo.id}"
            )
        return "-"
    mailinfo_link.short_description = "Email associé"
    
    def file_type(self, obj):
        if obj.upload:
            ext = obj.upload.name.split('.')[-1].lower() if '.' in obj.upload.name else ''
            types = {
                'pdf': '📕 PDF',
                'doc': '📘 Word',
                'docx': '📘 Word',
                'xls': '📗 Excel',
                'xlsx': '📗 Excel',
                'csv': '📗 CSV',
                'jpg': '🖼️ Image',
                'jpeg': '🖼️ Image',
                'png': '🖼️ Image',
                'gif': '🖼️ Image',
            }
            return types.get(ext, f'📁 {ext.upper()}' if ext else '📁 Inconnu')
        return "-"
    file_type.short_description = "Type"
    
    def file_size(self, obj):
        if obj.upload:
            try:
                size = obj.upload.size
                if size < 1024:
                    return f"{size} octets"
                elif size < 1024 * 1024:
                    return f"{size/1024:.1f} Ko"
                else:
                    return f"{size/(1024*1024):.1f} Mo"
            except:
                return "N/A"
        return "-"
    file_size.short_description = "Taille"
    
    def upload_date(self, obj):
        if hasattr(obj, 'uploaded_at') and obj.uploaded_at:
            return obj.uploaded_at.strftime('%d/%m/%Y')
        return "-"
    upload_date.short_description = "Date d'upload"
    
    def file_preview(self, obj):
        if obj.upload:
            filename = obj.upload.name.lower()
            if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                return format_html(
                    '<div style="margin: 10px 0;">'
                    '<a href="{}" target="_blank">'
                    '<img src="{}" style="max-width: 300px; max-height: 200px; border: 1px solid #ddd;" />'
                    '</a>'
                    '</div>',
                    obj.upload.url,
                    obj.upload.url
                )
            else:
                return format_html(
                    '<div style="margin: 10px 0;">'
                    '<a href="{}" target="_blank" style="display: inline-block; padding: 10px; background: #f0f0f0; border-radius: 5px; text-decoration: none; color: #333;">'
                    '📄 Télécharger "{}"'
                    '</a>'
                    '</div>',
                    obj.upload.url,
                    obj.upload.name.split('/')[-1]
                )
        return "Aucun fichier"
    file_preview.short_description = "Prévisualisation"
    
    def file_type_display(self, obj):
        return self.file_type(obj)
    file_type_display.short_description = "Type de fichier"
    
    def file_size_display(self, obj):
        return self.file_size(obj)
    file_size_display.short_description = "Taille du fichier"
    
    def upload_date_display(self, obj):
        if hasattr(obj, 'uploaded_at'):
            return obj.uploaded_at.strftime('%d/%m/%Y %H:%M')
        return "-"
    upload_date_display.short_description = "Date d'upload"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('mailinfo')


@admin.register(DocDownload)
class DocDownloadAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'acheteur_link', 'date_display', 
                    'client_email', 'acheteur_pays']
    list_filter = [DocDownloadDateFilter, 'client', 'acheteur', 'date']
    search_fields = ['client__username', 'client__email', 'acheteur__nom', 
                     'acheteur__ville__nom']
    readonly_fields = ['date']
    actions = [generer_rapport_telechargements_action]
    
    fieldsets = (
        ('Téléchargement', {
            'fields': ('client', 'acheteur')
        }),
        ('Date', {
            'fields': ('date',)
        }),
    )
    
    def acheteur_link(self, obj):
        if obj.acheteur:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:app_acheteur_change', args=[obj.acheteur.id]),
                obj.acheteur.nom
            )
        return "-"
    acheteur_link.short_description = "Acheteur"
    
    def date_display(self, obj):
        return obj.date.strftime('%d/%m/%Y %H:%M')
    date_display.short_description = "Date"
    
    def client_email(self, obj):
        return obj.client.email
    client_email.short_description = "Email client"
    
    def acheteur_pays(self, obj):
        if obj.acheteur and obj.acheteur.pays:
            return obj.acheteur.pays.nom
        return "-"
    acheteur_pays.short_description = "Pays acheteur"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('client', 'acheteur', 'acheteur__pays')


# =============================================================================
# MODELES DE RÉFÉRENCES PELBA
# =============================================================================








# =============================================================================
# JOURNAL D'ACTIVITÉ
# =============================================================================

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'action_type']  # minimal d'abord
    list_filter = ['user', 'action_type', 'created_at']  # au lieu de ['user', 'date']
    search_fields = ['user__username', 'action', 'ip_address', 'user_agent']
    readonly_fields = ['created_at']  # au lieu de ['date']
    actions = [nettoyer_anciens_logs_action, archiver_logs_action]
    
    fieldsets = (
        ('Activité', {
            'fields': ('user', 'action_full')
        }),
        ('Informations utilisateur', {
            'fields': ('user_details',),
            'classes': ('collapse',)
        }),
        ('Contexte technique', {
            'fields': ('ip_address', 'user_agent_full'),
            'classes': ('collapse',)
        }),
        ('Date', {
            'fields': ('date',),
            'classes': ('collapse',)
        }),
    )
    
    def action_preview(self, obj):
        if obj.action and len(obj.action) > 100:
            return obj.action[:100] + "..."
        return obj.action
    action_preview.short_description = "Action"
    
    def date_display(self, obj):
        return obj.date.strftime('%d/%m/%Y %H:%M:%S')
    date_display.short_description = "Date"
    
    def user_agent_preview(self, obj):
        if obj.user_agent and len(obj.user_agent) > 50:
            return obj.user_agent[:50] + "..."
        return obj.user_agent or "-"
    user_agent_preview.short_description = "Navigateur"
    
    def user_details(self, obj):
        if obj.user:
            return format_html(
                '<div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">'
                '<strong>Utilisateur:</strong> {}<br>'
                '<strong>Email:</strong> {}<br>'
                '<strong>Dernière connexion:</strong> {}<br>'
                '<strong>Date de création:</strong> {}'
                '</div>',
                obj.user.username,
                obj.user.email,
                obj.user.last_login.strftime('%d/%m/%Y %H:%M') if obj.user.last_login else 'Jamais',
                obj.user.date_joined.strftime('%d/%m/%Y %H:%M') if hasattr(obj.user, 'date_joined') else 'N/A'
            )
        return "Utilisateur anonyme"
    user_details.short_description = "Détails de l'utilisateur"
    
    def action_full(self, obj):
        return obj.action or "Aucune action"
    action_full.short_description = "Action complète"
    
    def user_agent_full(self, obj):
        if obj.user_agent:
            return format_html(
                '<div style="font-family: monospace; padding: 10px; background: #f5f5f5; border-radius: 5px; word-break: break-all;">'
                '{}'
                '</div>',
                obj.user_agent
            )
        return "Aucune information"
    user_agent_full.short_description = "User-Agent complet"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').order_by('-date')
    
    def has_add_permission(self, request):
        # Empêcher l'ajout manuel de logs
        return False
    
    def has_change_permission(self, request, obj=None):
        # Empêcher la modification des logs
        return False


# =============================================================================
# SITE HEADER PERSONNALISÉ
# =============================================================================

admin.site.site_header = "Administration Complète"
admin.site.site_title = "Admin Système"
admin.site.index_title = "Tableau de bord principal"

# Surcharger la vue d'accueil pour ajouter des statistiques
admin.site.index_template = 'admin/dashboard_index.html'


# =============================================================================
# CSS ET JS PERSONNALISÉS
# =============================================================================

class Media:
    css = {
        'all': ('admin/css/dashboard.css',)
    }
    
    js = ('admin/js/dashboard.js',)
    
    
    
    
    
# admin.py (suite)

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _

# Import des nouveaux modèles
from .models import (
    CompteFinancierIrfs, ValeurCompteIrfs,
    RatioFinancierIrfs, ValeurRatioIrfs,
    CredendoCommande
)

# =============================================================================
# ACTIONS PERSONNALISÉES
# =============================================================================

def calculer_ratios_automatiques_action(modeladmin, request, queryset):
    """Action pour calculer automatiquement les ratios financiers"""
    for compte in queryset:
        # Cette action pourrait déclencher un calcul automatique des ratios
        # Pour l'instant, on ajoute un tag dans la description
        if not compte.type_compte.startswith("[CALCULÉ]"):
            compte.type_compte = f"[CALCULÉ] {compte.type_compte}"
            compte.save()
    
    modeladmin.message_user(request, f"{queryset.count()} compte(s) marqué(s) pour calcul de ratios.")
calculer_ratios_automatiques_action.short_description = "Calculer ratios automatiques"

def exporter_comptes_excel_action(modeladmin, request, queryset):
    """Action pour exporter les comptes financiers en Excel"""
    from django.http import HttpResponse
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nom', 'Type', 'Sous-Type', 'Valeurs Année', 'Dernière Mise à Jour'])
    
    for compte in queryset:
        # Récupérer les valeurs par année
        valeurs = compte.valeurcomptefilter.all()
        annees = ", ".join([str(v.annee.annee) for v in valeurs[:3]])  # 3 premières années
        if len(valeurs) > 3:
            annees += f"... (+{len(valeurs)-3})"
        
        writer.writerow([
            compte.id,
            compte.nom,
            compte.get_type_compte_display(),
            compte.get_sous_type_display(),
            annees or "Aucune",
            compte.history.latest().history_date.strftime('%d/%m/%Y') if compte.history.exists() else "N/A"
        ])
    
    output.seek(0)
    response = HttpResponse(output, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="comptes_financiers_export.csv"'
    modeladmin.message_user(request, "Export CSV des comptes financiers généré.")
    return response
exporter_comptes_excel_action.short_description = "Exporter en CSV"

def importer_valeurs_action(modeladmin, request, queryset):
    """Action pour importer des valeurs de comptes (simulation)"""
    # Cette action pourrait ouvrir un formulaire d'import CSV
    # Pour l'instant, on simule juste l'import
    modeladmin.message_user(
        request, 
        f"{queryset.count()} compte(s) sélectionné(s) pour import de valeurs.",
        messages.INFO
    )
importer_valeurs_action.short_description = "Importer des valeurs"

def traiter_commandes_credendo_action(modeladmin, request, queryset):
    """Action pour traiter des commandes CREDENDO"""
    for commande in queryset:
        # Logique de traitement des commandes CREDENDO
        # À implémenter selon votre workflow
        if not commande.reference.startswith("TRAITÉ"):
            commande.reference = f"TRAITÉ-{commande.reference}"
            commande.save()
    
    modeladmin.message_user(request, f"{queryset.count()} commande(s) CREDENDO marquée(s) comme traitées.")
traiter_commandes_credendo_action.short_description = "Traiter les commandes"

def generer_rapport_credendo_action(modeladmin, request, queryset):
    """Action pour générer un rapport des commandes CREDENDO"""
    from django.http import HttpResponse
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Référence', 'Nom', 'Pays', 'Ville', 'Priorité', 
                     'Montant', 'Devise', 'Date Réception', 'Identifiants'])
    
    for commande in queryset:
        writer.writerow([
            commande.reference,
            commande.nom,
            commande.pays,
            commande.ville,
            commande.priorite,
            commande.montant or "N/A",
            commande.devise or "N/A",
            commande.date_reception.strftime('%d/%m/%Y %H:%M'),
            commande.identifiants[:50] + "..." if commande.identifiants and len(commande.identifiants) > 50 else commande.identifiants or "N/A"
        ])
    
    output.seek(0)
    response = HttpResponse(output, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="commandes_credendo_rapport.csv"'
    modeladmin.message_user(request, "Rapport CSV des commandes CREDENDO généré.")
    return response
generer_rapport_credendo_action.short_description = "Générer rapport CSV"


# =============================================================================
# FILTRES PERSONNALISÉS
# =============================================================================

class TypeCompteFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les types de comptes financiers"""
    title = _('Type de compte')
    parameter_name = 'type_compte'

    def lookups(self, request, model_admin):
        return CompteFinancierIrfs.TYPE_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type_compte=self.value())
        return queryset


class SousTypeCompteFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les sous-types de comptes financiers"""
    title = _('Sous-type de compte')
    parameter_name = 'sous_type'

    def lookups(self, request, model_admin):
        return CompteFinancierIrfs.SOUS_TYPE_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(sous_type=self.value())
        return queryset


class TypeRatioFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les types de ratios financiers"""
    title = _('Type de ratio')
    parameter_name = 'type_ratio'

    def lookups(self, request, model_admin):
        return RatioFinancierIrfs.TYPE_RATIO_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type_ratio=self.value())
        return queryset


class CommandeCredendoPaysFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les commandes CREDENDO par pays"""
    title = _('Pays')
    parameter_name = 'pays'

    def lookups(self, request, model_admin):
        # Récupérer les pays distincts des commandes CREDENDO
        pays = CredendoCommande.objects.values_list('pays', flat=True).distinct()
        return [(p, p) for p in sorted(pays) if p]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(pays=self.value())
        return queryset


class CommandeCredendoPrioriteFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les commandes CREDENDO par priorité"""
    title = _('Priorité')
    parameter_name = 'priorite'

    def lookups(self, request, model_admin):
        # Récupérer les priorités distinctes
        priorities = CredendoCommande.objects.values_list('priorite', flat=True).distinct()
        return [(p, p) for p in sorted(priorities) if p]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(priorite=self.value())
        return queryset


class CommandeCredendoDateFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour les commandes CREDENDO par date"""
    title = _('Date de réception')
    parameter_name = 'date_reception'

    def lookups(self, request, model_admin):
        return (
            ('today', _("Aujourd'hui")),
            ('week', _("Cette semaine")),
            ('month', _("Ce mois")),
            ('year', _("Cette année")),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            today = now.date()
            return queryset.filter(date_reception__date=today)
        elif self.value() == 'week':
            week_start = now - timedelta(days=now.weekday())
            return queryset.filter(date_reception__gte=week_start)
        elif self.value() == 'month':
            return queryset.filter(date_reception__year=now.year, date_reception__month=now.month)
        elif self.value() == 'year':
            return queryset.filter(date_reception__year=now.year)
        return queryset


# =============================================================================
# INLINES
# =============================================================================

class ValeurCompteIrfsInline(admin.TabularInline):
    model = ValeurCompteIrfs
    extra = 1
    fields = ['annee', 'valeur', 'devise', 'acheteur']
    verbose_name = "Valeur annuelle"
    verbose_name_plural = "Valeurs annuelles"
    classes = ['collapse']
    autocomplete_fields = ['acheteur', 'devise', 'annee']

class ValeurRatioIrfsInline(admin.TabularInline):
    model = ValeurRatioIrfs
    extra = 1
    fields = ['annee', 'valeur', 'acheteur']
    verbose_name = "Valeur ratio"
    verbose_name_plural = "Valeurs ratio"
    classes = ['collapse']
    autocomplete_fields = ['acheteur', 'annee']


# =============================================================================
# MODEL ADMINS
# =============================================================================

@admin.register(CompteFinancierIrfs)
class CompteFinancierIrfsAdmin(admin.ModelAdmin):
    list_display = ['id', 'nom', 'type_compte_display', 'sous_type_display', 
                    'valeurs_count', 'derniere_modification']
    list_filter = [TypeCompteFilter, SousTypeCompteFilter]
    search_fields = ['nom', 'type_compte', 'sous_type']
    readonly_fields = ['type_compte_display_field', 'sous_type_display_field', 
                      'valeurs_list', 'historique_modifications']
    actions = [calculer_ratios_automatiques_action, exporter_comptes_excel_action, 
               importer_valeurs_action]
    inlines = [ValeurCompteIrfsInline]
    
    fieldsets = (
        ('Compte financier', {
            'fields': ('nom', 'type_compte', 'sous_type')
        }),
        ('Informations affichées', {
            'fields': ('type_compte_display_field', 'sous_type_display_field')
        }),
        ('Valeurs associées', {
            'fields': ('valeurs_list',),
            'classes': ('collapse',)
        }),
        ('Historique', {
            'fields': ('historique_modifications',),
            'classes': ('collapse',)
        }),
    )
    
    def type_compte_display(self, obj):
        return obj.get_type_compte_display()
    type_compte_display.short_description = "Type"
    
    def sous_type_display(self, obj):
        return obj.get_sous_type_display() or "-"
    sous_type_display.short_description = "Sous-type"
    
    def valeurs_count(self, obj):
        count = obj.valeurcomptefilter.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #e3f2fd; padding: 2px 8px; border-radius: 12px; font-weight: bold;">💰 {}</span>',
                count
            )
        return "-"
    valeurs_count.short_description = "Valeurs"
    
    def derniere_modification(self, obj):
        if obj.history.exists():
            last = obj.history.latest()
            return last.history_date.strftime('%d/%m/%Y')
        return "-"
    derniere_modification.short_description = "Dernière modif"
    
    def type_compte_display_field(self, obj):
        return self.type_compte_display(obj)
    type_compte_display_field.short_description = "Type (affiché)"
    
    def sous_type_display_field(self, obj):
        return self.sous_type_display(obj)
    sous_type_display_field.short_description = "Sous-type (affiché)"
    
    def valeurs_list(self, obj):
        valeurs = obj.valeurcomptefilter.all().select_related('annee', 'devise', 'acheteur')
        if valeurs:
            html = '<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">'
            html += '<tr style="background-color: #f5f5f5;">'
            html += '<th style="padding: 8px; border: 1px solid #ddd;">Année</th>'
            html += '<th style="padding: 8px; border: 1px solid #ddd;">Valeur</th>'
            html += '<th style="padding: 8px; border: 1px solid #ddd;">Devise</th>'
            html += '<th style="padding: 8px; border: 1px solid #ddd;">Acheteur</th>'
            html += '</tr>'
            
            for valeur in valeurs:
                html += format_html(
                    '<tr style="border-bottom: 1px solid #ddd;">'
                    '<td style="padding: 8px;">{}</td>'
                    '<td style="padding: 8px; text-align: right; font-weight: bold;">{}</td>'
                    '<td style="padding: 8px;">{}</td>'
                    '<td style="padding: 8px;"><a href="{}" target="_blank">{}</a></td>'
                    '</tr>',
                    valeur.annee.annee,
                    f"{valeur.valeur:,.2f}",
                    valeur.devise.code if valeur.devise else "-",
                    reverse('admin:app_acheteur_change', args=[valeur.acheteur.id]) if valeur.acheteur else '#',
                    valeur.acheteur.nom if valeur.acheteur else "-"
                )
            
            html += '</table>'
            return mark_safe(html)
        return "Aucune valeur enregistrée"
    valeurs_list.short_description = "Liste des valeurs"
    
    def historique_modifications(self, obj):
        history = obj.history.all()[:10]  # 10 dernières modifications
        if history:
            html = '<ul style="margin-top: 10px; padding-left: 20px;">'
            for entry in history:
                html += format_html(
                    '<li>{} - par {} ({})</li>',
                    entry.history_date.strftime('%d/%m/%Y %H:%M'),
                    entry.history_user.username if entry.history_user else "Système",
                    entry.get_history_type_display()
                )
            html += '</ul>'
            return mark_safe(html)
        return "Aucune modification enregistrée"
    historique_modifications.short_description = "Historique des modifications"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('valeurcomptefilter')


@admin.register(ValeurCompteIrfs)
class ValeurCompteIrfsAdmin(admin.ModelAdmin):
    list_display = ['id', 'compte', 'annee', 'valeur_format', 'devise', 
                    'acheteur_link', 'created_at_display']
    list_filter = ['annee', 'devise', 'acheteur', 'compte__type_compte']
    search_fields = ['compte__nom', 'acheteur__nom', 'annee__annee']
    readonly_fields = ['created_at_display_field']
    autocomplete_fields = ['compte', 'acheteur', 'annee', 'devise']
    
    fieldsets = (
        ('Valeur de compte', {
            'fields': ('compte', 'acheteur', 'annee', 'valeur', 'devise')
        }),
        ('Dates', {
            'fields': ('created_at_display_field',),
            'classes': ('collapse',)
        }),
    )
    
    def valeur_format(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: {};">{}</span>',
            'green' if obj.valeur >= 0 else 'red',
            f"{obj.valeur:,.2f}"
        )
    valeur_format.short_description = "Valeur"
    
    def acheteur_link(self, obj):
        if obj.acheteur:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:app_acheteur_change', args=[obj.acheteur.id]),
                obj.acheteur.nom
            )
        return "-"
    acheteur_link.short_description = "Acheteur"
    
    def created_at_display(self, obj):
        if hasattr(obj, 'created_at') and obj.created_at:
            return obj.created_at.strftime('%d/%m/%Y')
        return "-"
    created_at_display.short_description = "Créé le"
    
    def created_at_display_field(self, obj):
        return self.created_at_display(obj)
    created_at_display_field.short_description = "Date de création"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('compte', 'acheteur', 'annee', 'devise')


@admin.register(RatioFinancierIrfs)
class RatioFinancierIrfsAdmin(admin.ModelAdmin):
    list_display = ['id', 'nom', 'type_ratio_display', 'formule', 
                    'valeurs_count', 'created_at_display']
    list_filter = [TypeRatioFilter]
    search_fields = ['nom', 'formule', 'type_ratio']
    readonly_fields = ['type_ratio_display_field', 'valeurs_list']
    actions = [exporter_comptes_excel_action]
    inlines = [ValeurRatioIrfsInline]
    
    fieldsets = (
        ('Ratio financier', {
            'fields': ('nom', 'type_ratio', 'formule')
        }),
        ('Informations affichées', {
            'fields': ('type_ratio_display_field',)
        }),
        ('Valeurs associées', {
            'fields': ('valeurs_list',),
            'classes': ('collapse',)
        }),
    )
    
    def type_ratio_display(self, obj):
        return obj.get_type_ratio_display()
    type_ratio_display.short_description = "Type"
    
    def valeurs_count(self, obj):
        count = obj.valeurratioirfs_set.count()
        if count > 0:
            return format_html(
                '<span style="background-color: #e8f5e8; padding: 2px 8px; border-radius: 12px; font-weight: bold;">📊 {}</span>',
                count
            )
        return "-"
    valeurs_count.short_description = "Valeurs"
    
    def created_at_display(self, obj):
        if hasattr(obj, 'created_at') and obj.created_at:
            return obj.created_at.strftime('%d/%m/%Y')
        return "-"
    created_at_display.short_description = "Créé le"
    
    def type_ratio_display_field(self, obj):
        return self.type_ratio_display(obj)
    type_ratio_display_field.short_description = "Type (affiché)"
    
    def valeurs_list(self, obj):
        valeurs = obj.valeurratioirfs_set.all().select_related('annee', 'acheteur')
        if valeurs:
            html = '<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">'
            html += '<tr style="background-color: #f5f5f5;">'
            html += '<th style="padding: 8px; border: 1px solid #ddd;">Année</th>'
            html += '<th style="padding: 8px; border: 1px solid #ddd;">Valeur</th>'
            html += '<th style="padding: 8px; border: 1px solid #ddd;">Acheteur</th>'
            html += '</tr>'
            
            for valeur in valeurs:
                html += format_html(
                    '<tr style="border-bottom: 1px solid #ddd;">'
                    '<td style="padding: 8px;">{}</td>'
                    '<td style="padding: 8px; text-align: right; font-weight: bold; color: {};">{}</td>'
                    '<td style="padding: 8px;"><a href="{}" target="_blank">{}</a></td>'
                    '</tr>',
                    valeur.annee.annee,
                    'green' if valeur.valeur >= 0 else 'red',
                    f"{valeur.valeur:,.2f}",
                    reverse('admin:app_acheteur_change', args=[valeur.acheteur.id]) if valeur.acheteur else '#',
                    valeur.acheteur.nom if valeur.acheteur else "-"
                )
            
            html += '</table>'
            return mark_safe(html)
        return "Aucune valeur enregistrée"
    valeurs_list.short_description = "Liste des valeurs"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('valeurratioirfs_set')


@admin.register(ValeurRatioIrfs)
class ValeurRatioIrfsAdmin(admin.ModelAdmin):
    list_display = ['id', 'ratio', 'annee', 'valeur_format', 'acheteur_link', 
                    'created_at_display']
    list_filter = ['annee', 'acheteur', 'ratio__type_ratio']
    search_fields = ['ratio__nom', 'acheteur__nom', 'annee__annee']
    readonly_fields = ['created_at_display_field']
    autocomplete_fields = ['ratio', 'acheteur', 'annee']
    
    fieldsets = (
        ('Valeur de ratio', {
            'fields': ('ratio', 'acheteur', 'annee', 'valeur')
        }),
        ('Dates', {
            'fields': ('created_at_display_field',),
            'classes': ('collapse',)
        }),
    )
    
    def valeur_format(self, obj):
        # Déterminer la couleur selon la valeur du ratio
        color = 'black'
        if obj.ratio.type_ratio == "Liquidité" and obj.valeur >= 1:
            color = 'green'
        elif obj.ratio.type_ratio == "Liquidité" and obj.valeur < 1:
            color = 'orange'
        elif obj.ratio.type_ratio == "Solvabilité" and obj.valeur >= 0.3:
            color = 'green'
        elif obj.ratio.type_ratio == "Solvabilité" and obj.valeur < 0.3:
            color = 'orange'
        
        return format_html(
            '<span style="font-weight: bold; color: {};">{}</span>',
            color,
            f"{obj.valeur:,.2f}"
        )
    valeur_format.short_description = "Valeur"
    
    def acheteur_link(self, obj):
        if obj.acheteur:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:app_acheteur_change', args=[obj.acheteur.id]),
                obj.acheteur.nom
            )
        return "-"
    acheteur_link.short_description = "Acheteur"
    
    def created_at_display(self, obj):
        if hasattr(obj, 'created_at') and obj.created_at:
            return obj.created_at.strftime('%d/%m/%Y')
        return "-"
    created_at_display.short_description = "Créé le"
    
    def created_at_display_field(self, obj):
        return self.created_at_display(obj)
    created_at_display_field.short_description = "Date de création"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('ratio', 'acheteur', 'annee')


@admin.register(CredendoCommande)
class CredendoCommandeAdmin(admin.ModelAdmin):
    list_display = ['id', 'reference', 'nom_preview', 'pays', 'ville', 
                    'priorite_display', 'montant_format', 'date_reception_display', 
                    'identifiants_preview']
    list_filter = [CommandeCredendoPaysFilter, CommandeCredendoPrioriteFilter, 
                   CommandeCredendoDateFilter]
    search_fields = ['reference', 'nom', 'pays', 'ville', 'identifiants', 
                     'internal_bp_id', 'email_id']
    readonly_fields = ['date_reception', 'texte_complet_display', 'identifiants_display', 
                      'rue_display', 'remarque_display']
    actions = [traiter_commandes_credendo_action, generer_rapport_credendo_action]
    
    fieldsets = (
        ('Références', {
            'fields': ('sender_id', 'email_id', 'reference', 'internal_bp_id')
        }),
        ('Entreprise', {
            'fields': ('nom', 'identifiants_display')
        }),
        ('Adresse', {
            'fields': ('rue_display', 'ville', 'pays')
        }),
        ('Commande', {
            'fields': ('remarque_display', 'priorite', 'montant', 'devise')
        }),
        ('Texte complet', {
            'fields': ('texte_complet_display',),
            'classes': ('wide',)
        }),
        ('Date de réception', {
            'fields': ('date_reception',),
            'classes': ('collapse',)
        }),
    )
    
    def nom_preview(self, obj):
        if len(obj.nom) > 30:
            return obj.nom[:30] + "..."
        return obj.nom
    nom_preview.short_description = "Nom"
    
    def priorite_display(self, obj):
        color_map = {
            'Haute': 'red',
            'Moyenne': 'orange',
            'Basse': 'green',
            'Urgent': 'darkred',
            'Normale': 'blue',
        }
        color = color_map.get(obj.priorite, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.priorite
        )
    priorite_display.short_description = "Priorité"
    
    def montant_format(self, obj):
        if obj.montant:
            return format_html(
                '<span style="font-weight: bold;">{} {}</span>',
                f"{obj.montant:,.2f}",
                obj.devise or ""
            )
        return "-"
    montant_format.short_description = "Montant"
    
    def date_reception_display(self, obj):
        return obj.date_reception.strftime('%d/%m/%Y %H:%M')
    date_reception_display.short_description = "Date réception"
    
    def identifiants_preview(self, obj):
        if obj.identifiants and len(obj.identifiants) > 20:
            return obj.identifiants[:20] + "..."
        return obj.identifiants or "-"
    identifiants_preview.short_description = "Identifiants"
    
    def texte_complet_display(self, obj):
        if obj.texte_complet:
            return format_html(
                '<div style="padding: 10px; background: #f5f5f5; border-radius: 5px; max-height: 200px; overflow-y: auto; font-family: monospace; white-space: pre-wrap;">'
                '{}'
                '</div>',
                obj.texte_complet
            )
        return "Aucun texte"
    texte_complet_display.short_description = "Texte complet"
    
    def identifiants_display(self, obj):
        if obj.identifiants:
            return format_html(
                '<div style="padding: 10px; background: #e8f5e8; border-radius: 5px; font-family: monospace;">'
                '{}'
                '</div>',
                obj.identifiants
            )
        return "Aucun identifiant"
    identifiants_display.short_description = "Identifiants (affichés)"
    
    def rue_display(self, obj):
        if obj.rue:
            return format_html(
                '<div style="padding: 10px; background: #f0f0f0; border-radius: 5px;">'
                '{}'
                '</div>',
                obj.rue
            )
        return "Aucune adresse"
    rue_display.short_description = "Rue (affichée)"
    
    def remarque_display(self, obj):
        if obj.remarque:
            return format_html(
                '<div style="padding: 10px; background: #fff3e0; border-radius: 5px;">'
                '{}'
                '</div>',
                obj.remarque
            )
        return "Aucune remarque"
    remarque_display.short_description = "Remarque (affichée)"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('-date_reception')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ajouter des attributs HTML aux champs
        form.base_fields['reference'].widget.attrs['placeholder'] = 'Ex: CRED-2024-001'
        form.base_fields['internal_bp_id'].widget.attrs['placeholder'] = 'Ex: BP123456'
        form.base_fields['email_id'].widget.attrs['placeholder'] = 'ID unique du mail'
        form.base_fields['montant'].widget.attrs['style'] = 'text-align: right;'
        
        # Masquer certains champs en lecture seule
        if obj:
            form.base_fields['email_id'].widget.attrs['readonly'] = True
            form.base_fields['sender_id'].widget.attrs['readonly'] = True
        
        return form


# =============================================================================
# DASHBOARD FINANCIER
# =============================================================================

class FinancierDashboard(admin.ModelAdmin):
    """Tableau de bord personnalisé pour les modules financiers"""
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Statistiques financières
        from django.db.models import Count, Sum
        stats = {
            'total_comptes': CompteFinancierIrfs.objects.count(),
            'total_valeurs': ValeurCompteIrfs.objects.count(),
            'total_ratios': RatioFinancierIrfs.objects.count(),
            'total_valeurs_ratios': ValeurRatioIrfs.objects.count(),
            'commandes_credendo': CredendoCommande.objects.count(),
            'commandes_recentes': CredendoCommande.objects.filter(
                date_reception__gte=timezone.now() - timedelta(days=7)
            ).count(),
        }
        
        # Distribution par type de compte
        types_comptes = CompteFinancierIrfs.objects.values('type_compte').annotate(
            count=Count('id')
        )
        
        # Commandes par priorité
        commandes_par_priorite = CredendoCommande.objects.values('priorite').annotate(
            count=Count('id')
        )
        
        extra_context.update({
            'stats': stats,
            'types_comptes': list(types_comptes),
            'commandes_par_priorite': list(commandes_par_priorite),
            'dashboard': True,
        })
        
        return super().changelist_view(request, extra_context)


# =============================================================================
# SITE HEADER PERSONNALISÉ
# =============================================================================

admin.site.site_header = "Administration BUCREP"
admin.site.site_title = "Admin Bucrep"
admin.site.index_title = "Tableau de bord Bucrep"

# Surcharger la vue d'accueil pour ajouter des statistiques
admin.site.index_template = 'admin/financier_index.html'


# =============================================================================
# CSS ET JS PERSONNALISÉS
# =============================================================================

class Media:
    css = {
        'all': ('admin/css/financier.css',)
    }
    
    js = ('admin/js/financier.js',)
    
    
    
