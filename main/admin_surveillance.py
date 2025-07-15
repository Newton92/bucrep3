# admin.py - Interface d'administration
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.html import format_html

from .models import (EvenementSurveillance, HistoriqueDonnees, NotificationLog,
                     Portefeuille, SurveillanceConfiguration)


@admin.register(SurveillanceConfiguration)
class SurveillanceConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "element_surveillance",
        "content_type",
        "methode_detection",
        "actif",
    )
    list_filter = ("methode_detection", "actif", "content_type")
    search_fields = ("element_surveillance__nom", "element_surveillance__code_interne")

    fieldsets = (
        ("Élément surveillé", {"fields": ("element_surveillance", "content_type")}),
        (
            "Configuration de détection",
            {"fields": ("champs_surveilles", "methode_detection", "conditions")},
        ),
        (
            "Options avancées",
            {"fields": ("handler_class", "actif"), "classes": ("collapse",)},
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Édition
            return ("element_surveillance", "content_type")
        return ()


@admin.register(EvenementSurveillance)
class EvenementSurveillanceAdmin(admin.ModelAdmin):
    list_display = (
        "portefeuille",
        "element_surveillance",
        "type_evenement",
        "content_object_display",
        "date_evenement",
        "traite",
        "alerte_envoyee",
    )
    list_filter = (
        "type_evenement",
        "traite",
        "alerte_envoyee",
        "element_surveillance",
        "date_evenement",
    )
    search_fields = ("portefeuille__nom", "element_surveillance__nom")
    date_hierarchy = "date_evenement"

    readonly_fields = (
        "content_object_display",
        "donnees_avant_display",
        "donnees_apres_display",
    )

    fieldsets = (
        (
            "Informations générales",
            {
                "fields": (
                    "portefeuille",
                    "element_surveillance",
                    "type_evenement",
                    "content_object_display",
                )
            },
        ),
        (
            "Détails des changements",
            {
                "fields": (
                    "donnees_avant_display",
                    "donnees_apres_display",
                    "champs_modifies",
                )
            },
        ),
        (
            "Statut de traitement",
            {"fields": ("traite", "alerte_envoyee", "date_traitement")},
        ),
    )

    def content_object_display(self, obj):
        if obj.content_object:
            return format_html("<strong>{}</strong>", str(obj.content_object))
        return "Objet supprimé"

    content_object_display.short_description = "Objet concerné"

    def donnees_avant_display(self, obj):
        if obj.donnees_avant:
            return format_html(
                "<pre>{}</pre>",
                json.dumps(obj.donnees_avant, indent=2, ensure_ascii=False),
            )
        return "Aucune"

    donnees_avant_display.short_description = "Données avant"

    def donnees_apres_display(self, obj):
        if obj.donnees_apres:
            return format_html(
                "<pre>{}</pre>",
                json.dumps(obj.donnees_apres, indent=2, ensure_ascii=False),
            )
        return "Aucune"

    donnees_apres_display.short_description = "Données après"

    actions = ["marquer_comme_traite", "renvoyer_alerte"]

    def marquer_comme_traite(self, request, queryset):
        from django.utils import timezone

        updated = queryset.update(traite=True, date_traitement=timezone.now())
        self.message_user(request, f"{updated} événement(s) marqué(s) comme traité(s).")

    marquer_comme_traite.short_description = "Marquer comme traité"

    def renvoyer_alerte(self, request, queryset):
        from .tasks import envoyer_alertes_portefeuille

        portefeuilles_events = {}
        for event in queryset:
            if event.portefeuille.id not in portefeuilles_events:
                portefeuilles_events[event.portefeuille.id] = []
            portefeuilles_events[event.portefeuille.id].append(event.id)

        for portefeuille_id, event_ids in portefeuilles_events.items():
            envoyer_alertes_portefeuille.delay(portefeuille_id, event_ids)

        self.message_user(
            request,
            f"Alertes relancées pour {len(portefeuilles_events)} portefeuille(s).",
        )

    renvoyer_alerte.short_description = "Renvoyer les alertes"


@admin.register(HistoriqueDonnees)
class HistoriqueDonneesAdmin(admin.ModelAdmin):
    list_display = (
        "content_object_display",
        "portefeuille",
        "date_capture",
        "hash_donnees_short",
    )
    list_filter = ("content_type", "date_capture", "portefeuille")
    search_fields = ("portefeuille__nom",)
    date_hierarchy = "date_capture"

    readonly_fields = (
        "content_object_display",
        "donnees_snapshot_display",
        "hash_donnees",
    )

    def content_object_display(self, obj):
        if obj.content_object:
            return format_html("<strong>{}</strong>", str(obj.content_object))
        return "Objet supprimé"

    content_object_display.short_description = "Objet"

    def hash_donnees_short(self, obj):
        return obj.hash_donnees[:12] + "..." if obj.hash_donnees else ""

    hash_donnees_short.short_description = "Hash (tronqué)"

    def donnees_snapshot_display(self, obj):
        return format_html(
            '<pre style="max-height: 300px; overflow-y: scroll;">{}</pre>',
            json.dumps(obj.donnees_snapshot, indent=2, ensure_ascii=False),
        )

    donnees_snapshot_display.short_description = "Snapshot des données"


# Extension de l'admin existant pour Portefeuille
class EvenementSurveillanceInline(admin.TabularInline):
    model = EvenementSurveillance
    extra = 0
    readonly_fields = (
        "element_surveillance",
        "type_evenement",
        "date_evenement",
        "traite",
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# Étendre l'admin Portefeuille existant
@admin.register(Portefeuille)
class PortefeuilleAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "client",
        "frequence_alertes",
        "nb_elements_surveillance",
        "nb_acheteurs",
    )
    list_filter = ("frequence_alertes", "created_at")
    search_fields = ("nom", "client__nom", "client__email")

    inlines = [EvenementSurveillanceInline]

    fieldsets = (
        ("Informations générales", {"fields": ("client", "nom", "frequence_alertes")}),
        ("Surveillance", {"fields": ("elements_surveillance_actifs",)}),
        (
            "Métadonnées",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    def nb_elements_surveillance(self, obj):
        return obj.elements_surveillance_actifs.count()

    nb_elements_surveillance.short_description = "Éléments surveillés"

    def nb_acheteurs(self, obj):
        return obj.portefeuilleclient_set.count()

    nb_acheteurs.short_description = "Acheteurs"

    actions = ["lancer_surveillance_manuelle", "test_alertes"]

    def lancer_surveillance_manuelle(self, request, queryset):
        from .tasks import traiter_surveillance_portefeuille

        for portefeuille in queryset:
            traiter_surveillance_portefeuille.delay(portefeuille.id)

        self.message_user(
            request, f"Surveillance lancée pour {queryset.count()} portefeuille(s)."
        )

    lancer_surveillance_manuelle.short_description = "Lancer surveillance manuelle"

    def test_alertes(self, request, queryset):
        # Page de test des alertes
        if "apply" in request.POST:
            from .tasks import _envoyer_email_alerte

            for portefeuille in queryset:
                # Créer un contenu de test
                contenu_test = {
                    "portefeuille": portefeuille,
                    "client": portefeuille.client,
                    "evenements_groupes": {
                        "TEST": [
                            {
                                "element_surveillance": {"nom": "Test de surveillance"},
                                "content_object": "Acheteur Test",
                                "date_evenement": timezone.now(),
                            }
                        ]
                    },
                    "date_rapport": timezone.now(),
                    "total_evenements": 1,
                }

                success = _envoyer_email_alerte(portefeuille.client, contenu_test)
                if success:
                    messages.success(
                        request, f"Email de test envoyé à {portefeuille.client.email}"
                    )
                else:
                    messages.error(
                        request, f"Échec envoi email à {portefeuille.client.email}"
                    )

            return HttpResponseRedirect(request.get_full_path())

        return render(
            request,
            "admin/test_alertes.html",
            {"portefeuilles": queryset, "title": "Test des alertes email"},
        )

    test_alertes.short_description = "Tester les alertes email"


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("portefeuille", "code_evenement", "date_notification", "actif")
    list_filter = ("code_evenement", "actif", "date_notification")
    search_fields = ("portefeuille__nom", "description")
    date_hierarchy = "date_notification"
    readonly_fields = ("date_notification",)


import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
# views.py - Vues pour le dashboard
from django.shortcuts import get_object_or_404, render
from django.utils import timezone


@login_required
def dashboard_surveillance(request):
    """
    Dashboard principal de surveillance
    """
    # Statistiques générales
    total_portefeuilles = Portefeuille.objects.count()
    total_acheteurs = PortefeuilleClient.objects.values("acheteur").distinct().count()

    # Événements récents (7 derniers jours)
    date_limite = timezone.now() - timedelta(days=7)
    evenements_recents = EvenementSurveillance.objects.filter(
        date_evenement__gte=date_limite
    ).count()

    evenements_non_traites = EvenementSurveillance.objects.filter(traite=False).count()

    # Graphique des événements par jour (30 derniers jours)
    date_debut = timezone.now() - timedelta(days=30)
    evenements_par_jour = (
        EvenementSurveillance.objects.filter(date_evenement__gte=date_debut)
        .extra(select={"jour": "DATE(date_evenement)"})
        .values("jour")
        .annotate(count=Count("id"))
        .order_by("jour")
    )

    # Top des éléments de surveillance les plus actifs
    top_elements = (
        EvenementSurveillance.objects.filter(date_evenement__gte=date_debut)
        .values("element_surveillance__nom")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    context = {
        "total_portefeuilles": total_portefeuilles,
        "total_acheteurs": total_acheteurs,
        "evenements_recents": evenements_recents,
        "evenements_non_traites": evenements_non_traites,
        "evenements_par_jour": list(evenements_par_jour),
        "top_elements": list(top_elements),
    }

    return render(request, "surveillance/dashboard.html", context)


@login_required
def portefeuille_detail(request, portefeuille_id):
    """
    Détail d'un portefeuille avec ses événements
    """
    portefeuille = get_object_or_404(Portefeuille, id=portefeuille_id)

    # Événements récents pour ce portefeuille
    evenements = (
        EvenementSurveillance.objects.filter(portefeuille=portefeuille)
        .select_related("element_surveillance", "content_type")
        .order_by("-date_evenement")[:50]
    )

    # Statistiques du portefeuille
    stats = {
        "total_evenements": EvenementSurveillance.objects.filter(
            portefeuille=portefeuille
        ).count(),
        "evenements_non_traites": EvenementSurveillance.objects.filter(
            portefeuille=portefeuille, traite=False
        ).count(),
        "derniere_surveillance": (
            evenements.first().date_evenement if evenements else None
        ),
    }

    context = {
        "portefeuille": portefeuille,
        "evenements": evenements,
        "stats": stats,
    }

    return render(request, "surveillance/portefeuille_detail.html", context)


@login_required
def api_evenements_graphique(request, portefeuille_id):
    """
    API pour les données du graphique des événements
    """
    portefeuille = get_object_or_404(Portefeuille, id=portefeuille_id)

    # Paramètres
    jours = int(request.GET.get("jours", 30))
    date_debut = timezone.now() - timedelta(days=jours)

    # Données pour le graphique
    donnees = (
        EvenementSurveillance.objects.filter(
            portefeuille=portefeuille, date_evenement__gte=date_debut
        )
        .extra(select={"jour": "DATE(date_evenement)"})
        .values("jour")
        .annotate(count=Count("id"))
        .order_by("jour")
    )

    return JsonResponse({"data": list(donnees), "portefeuille": portefeuille.nom})


# templates/emails/alerte_surveillance.html
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport de Surveillance</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .portefeuille-info { background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .evenement { border-left: 4px solid #3498db; padding: 15px; margin-bottom: 15px; background-color: #f8f9fa; }
        .evenement.urgent { border-left-color: #e74c3c; }
        .evenement.warning { border-left-color: #f39c12; }
        .evenement-titre { font-weight: bold; color: #2c3e50; margin-bottom: 10px; }
        .evenement-details { font-size: 0.9em; color: #666; }
        .acheteur { background-color: #fff; padding: 10px; margin: 5px 0; border-radius: 3px; }
        .footer { background-color: #34495e; color: white; padding: 15px; text-align: center; font-size: 0.9em; }
        .stats { display: flex; justify-content: space-around; margin: 20px 0; }
        .stat { text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #3498db; }
        .stat-label { color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Rapport de Surveillance</h1>
        <p>{{ date_rapport|date:"d/m/Y à H:i" }}</p>
    </div>

    <div class="content">
        <div class="portefeuille-info">
            <h2>Portefeuille: {{ portefeuille.nom }}</h2>
            <p><strong>Client:</strong> {{ client.nom }} ({{ client.email }})</p>
            <p><strong>Fréquence:</strong> {{ portefeuille.get_frequence_alertes_display }}</p>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-number">{{ total_evenements }}</div>
                <div class="stat-label">Événement{{ total_evenements|pluralize }}</div>
            </div>
            <div class="stat">
                <div class="stat-number">{{ evenements_groupes|length }}</div>
                <div class="stat-label">Type{{ evenements_groupes|length|pluralize }} d'alerte</div>
            </div>
        </div>

        <h3>📋 Événements détectés</h3>

        {% for code, events in evenements_groupes.items %}
        <div class="evenement {% if 'DISSOLUTION' in code or 'LIQUIDATION' in code %}urgent{% elif 'EXECUTIVE_CHANGE' in code %}warning{% endif %}">
            <div class="evenement-titre">
                {{ events.0.element_surveillance.nom }} ({{ events|length }} événement{{ events|length|pluralize }})
            </div>

            {% for event in events %}
            <div class="acheteur">
                <strong>🏢 {{ event.content_object.nom }}</strong>
                <div class="evenement-details">
                    <p><strong>Type:</strong> {{ event.get_type_evenement_display }}</p>
                    <p><strong>Date:</strong> {{ event.date_evenement|date:"d/m/Y à H:i" }}</p>

                    {% if event.champs_modifies %}
                    <p><strong>Champs modifiés:</strong> {{ event.champs_modifies|join:", " }}</p>
                    {% endif %}

                    {% if event.donnees_avant and event.donnees_apres %}
                    <details>
                        <summary>Voir les détails des changements</summary>
                        <div style="margin-top: 10px; font-size: 0.8em;">
                            <strong>Avant:</strong>
                            <pre style="background: #f1f2f6; padding: 10px; border-radius: 3px;">{{ event.donnees_avant|pprint }}</pre>
                            <strong>Après:</strong>
                            <pre style="background: #e8f5e8; padding: 10px; border-radius: 3px;">{{ event.donnees_apres|pprint }}</pre>
                        </div>
                    </details>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        {% endfor %}

        {% if not evenements_groupes %}
        <div class="evenement">
            <div class="evenement-titre">✅ Aucun événement détecté</div>
            <p>Tout semble en ordre pour ce cycle de surveillance.</p>
        </div>
        {% endif %}
    </div>

    <div class="footer">
        <p>Ce rapport a été généré automatiquement par votre système de surveillance d'entreprise.</p>
        <p><small>Si vous avez des questions, contactez votre administrateur système.</small></p>
    </div>
</body>
</html>
"""

# Créer le fichier template
# templates/emails/alerte_surveillance.html avec le contenu EMAIL_TEMPLATE

# templates/admin/test_alertes.html
TEST_ALERTES_TEMPLATE = """
{% extends "admin/base_site.html" %}

{% block title %}Test des alertes email{% endblock %}

{% block content %}
<h1>Test des alertes email</h1>

<form method="post">
    {% csrf_token %}

    <p>Vous êtes sur le point d'envoyer un email de test aux clients des portefeuilles suivants :</p>

    <ul>
    {% for portefeuille in portefeuilles %}
        <li><strong>{{ portefeuille.nom }}</strong> → {{ portefeuille.client.email }}</li>
    {% endfor %}
    </ul>

    <p><strong>⚠️ Attention :</strong> Ceci enverra de vrais emails aux clients.</p>

    <input type="hidden" name="apply" value="yes">
    <button type="submit" class="default" onclick="return confirm('Êtes-vous sûr de vouloir envoyer ces emails de test ?')">
        Envoyer les emails de test
    </button>
    <a href="{% url 'admin:votre_app_portefeuille_changelist' %}" class="button cancel-link">Annuler</a>
</form>

{% endblock %}
"""

# urls.py - URLs pour les vues
from django.urls import path

from . import views

urlpatterns = [
    path("surveillance/", views.dashboard_surveillance, name="surveillance_dashboard"),
    path(
        "surveillance/portefeuille/<int:portefeuille_id>/",
        views.portefeuille_detail,
        name="portefeuille_detail",
    ),
    path(
        "api/evenements/<int:portefeuille_id>/",
        views.api_evenements_graphique,
        name="api_evenements",
    ),
]
