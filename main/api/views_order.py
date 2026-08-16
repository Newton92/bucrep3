import csv
import logging
import unicodedata
from io import BytesIO

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import Commande, SuiviCommande, User
from main.serializers import (
    AddCommandeSerializer,
    CheckCommandeSerializer,
    CommandeSerializer,
    EditCommandeSerializer,
)

logger = logging.getLogger(__name__)

LOCKED_STATUS = "envoye_client"
LOCKED_ALLOWED_FIELDS = {
    "status",
    "validateur",
    "date_envoi_client",
    "email_envoye",
    "imprimer_avec_etats_fin",
    "comments",
}


def _simplify_text(value):
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch for ch in text if ch.isalnum())


def _normalize_status_value(raw_status):
    raw = (raw_status or "").strip()
    if not raw:
        return raw

    choices = dict(Commande.STATUS_CHOICES)
    lookup = {}
    for key, label in choices.items():
        variants = {
            key,
            key.replace("_", " "),
            str(label),
        }
        for variant in variants:
            lookup[_simplify_text(variant)] = key

    return lookup.get(_simplify_text(raw), raw)


def _sanitize_payload_values(payload):
    # Eviter les nulls invalides sur les CharField null=False
    if payload.get("client_nom", object()) is None:
        payload.pop("client_nom", None)

    # Le champ comments est limité à 100 dans le modèle.
    if payload.get("comments") is not None:
        comments = str(payload.get("comments")).strip()
        payload["comments"] = comments[:100]

    return payload


def _apply_scope_filters(queryset, request):
    selected_pays_id = _get_active_country_id(request)

    if selected_pays_id:
        queryset = queryset.filter(pays_id=selected_pays_id)

    return queryset


def _apply_list_filters(queryset, request):
    search = (request.query_params.get("search") or "").strip()
    status_filter = (request.query_params.get("status") or "").strip()
    status_filter = _normalize_status_value(status_filter)
    priorite = (request.query_params.get("priorite") or "").strip()
    type_rapport = (request.query_params.get("type_rapport") or "").strip()
    client_id = (request.query_params.get("client_id") or "").strip()
    date_from = (request.query_params.get("date_from") or "").strip()
    date_to = (request.query_params.get("date_to") or "").strip()

    if search:
        queryset = queryset.filter(
            Q(notre_ref__icontains=search)
            | Q(reference_client__icontains=search)
            | Q(raison_sociale__icontains=search)
            | Q(status__icontains=search)
            | Q(priorite__icontains=search)
            | Q(type_rapport__icontains=search)
            | Q(client__username__icontains=search)
            | Q(pays__nom__icontains=search)
            | Q(ville__nom__icontains=search)
            | Q(acheteur__nom__icontains=search)
        )

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if priorite:
        queryset = queryset.filter(priorite__iexact=priorite)
    if type_rapport:
        queryset = queryset.filter(type_rapport=type_rapport)
    if client_id.isdigit():
        queryset = queryset.filter(client_id=int(client_id))
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    analyste_id = (request.query_params.get("analyste_id") or "").strip()
    if analyste_id == "me":
        queryset = queryset.filter(affectationanalyste__analyste=request.user)
    elif analyste_id.isdigit():
        queryset = queryset.filter(affectationanalyste__analyste_id=int(analyste_id))

    return queryset


def _get_active_country_id(request):
    selected_pays_id = request.query_params.get("pays_id") or request.session.get("selected_pays_id")
    if not selected_pays_id and getattr(request.user, "pays_id", None):
        selected_pays_id = request.user.pays_id
    try:
        return int(selected_pays_id) if selected_pays_id else None
    except (TypeError, ValueError):
        return None


class OrderModuleListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = Commande.objects.select_related("client", "pays", "ville", "acheteur")
        queryset = _apply_scope_filters(queryset, request)
        queryset = _apply_list_filters(queryset, request).order_by("-created_at")

        page_number = request.query_params.get("page", 1)
        page_size = request.query_params.get("page_size", 10)

        try:
            page_size = max(1, min(int(page_size), 100))
        except (TypeError, ValueError):
            page_size = 10

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page_number)
        serializer = CommandeSerializer(page_obj, many=True)

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "page_size": page_size,
                "next": page_obj.has_next(),
                "previous": page_obj.has_previous(),
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        payload = request.data.copy()
        if not payload.get("client") and getattr(request.user, "is_client", False):
            payload["client"] = request.user.id
        payload["status"] = _normalize_status_value(payload.get("status"))
        payload = _sanitize_payload_values(payload)

        serializer = AddCommandeSerializer(data=payload)
        if serializer.is_valid():
            obj = serializer.save()
            active_country_id = _get_active_country_id(request)
            if active_country_id:
                obj.pays_id = active_country_id
            elif getattr(obj, "ville_id", None) and getattr(obj.ville, "pays_id", None):
                obj.pays_id = obj.ville.pays_id
            update_fields = []
            if obj.pays_id:
                update_fields.append("pays")
            # Auto-génération notre_ref : {id}/{code_pays}
            pays_code = ""
            if obj.pays_id:
                from main.models import Pays as _Pays
                pays_code = _Pays.objects.filter(pk=obj.pays_id).values_list("code", flat=True).first() or ""
            obj.notre_ref = f"{obj.id}/{pays_code}" if pays_code else str(obj.id)
            update_fields.append("notre_ref")
            obj.save(update_fields=update_fields)
            return Response(CheckCommandeSerializer(obj).data, status=status.HTTP_201_CREATED)
        logger.warning("Validation creation commande échouée: %s", serializer.errors)
        return Response(
            {"detail": "Validation des données échouée.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class OrderModuleRetrieveUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, commande_id):
        return Commande.objects.filter(id=commande_id).first()

    def get(self, request, commande_id, *args, **kwargs):
        commande = self.get_object(commande_id)
        if not commande:
            return Response({"detail": "Commande non trouvée."}, status=status.HTTP_404_NOT_FOUND)
        return Response(CheckCommandeSerializer(commande).data, status=status.HTTP_200_OK)

    def put(self, request, commande_id, *args, **kwargs):
        commande = self.get_object(commande_id)
        if not commande:
            return Response({"detail": "Commande non trouvée."}, status=status.HTTP_404_NOT_FOUND)

        payload = request.data.copy()
        payload["status"] = _normalize_status_value(payload.get("status"))
        payload = _sanitize_payload_values(payload)

        # Si la commande est déjà envoyée au client, on verrouille les champs sensibles.
        locked_fields_ignored = []
        if commande.status == LOCKED_STATUS:
            filtered_payload = {}
            for field, value in payload.items():
                if field in LOCKED_ALLOWED_FIELDS:
                    filtered_payload[field] = value
                else:
                    locked_fields_ignored.append(field)
            payload = filtered_payload
            if locked_fields_ignored:
                logger.info(
                    "Edition partielle commande #%s (status=%s): champs sensibles ignorés: %s",
                    commande_id,
                    commande.status,
                    ", ".join(sorted(locked_fields_ignored)),
                )

        serializer = EditCommandeSerializer(commande, data=payload, partial=True)
        if serializer.is_valid():
            serializer.save()
            active_country_id = _get_active_country_id(request)
            if active_country_id:
                commande.pays_id = active_country_id
            elif getattr(commande, "ville_id", None) and getattr(commande.ville, "pays_id", None):
                commande.pays_id = commande.ville.pays_id
            if commande.pays_id:
                commande.save(update_fields=["pays"])
            response_payload = CheckCommandeSerializer(commande).data
            if locked_fields_ignored:
                response_payload["locked_fields_ignored"] = sorted(locked_fields_ignored)
            return Response(response_payload, status=status.HTTP_200_OK)
        logger.warning(
            "Validation édition commande #%s échouée: %s",
            commande_id,
            serializer.errors,
        )
        return Response(
            {"detail": "Validation des données échouée.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, commande_id, *args, **kwargs):
        commande = self.get_object(commande_id)
        if not commande:
            return Response({"detail": "Commande non trouvée."}, status=status.HTTP_404_NOT_FOUND)
        commande.delete()
        return Response({"detail": "Commande supprimée avec succès."}, status=status.HTTP_200_OK)


class OrderModuleStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = Commande.objects.all()
        queryset = _apply_scope_filters(queryset, request)
        queryset = _apply_list_filters(queryset, request)

        today = timezone.localdate()

        by_status_raw = queryset.values("status").order_by("status").annotate(total_count=Count("id"))
        by_status = {entry["status"]: entry["total_count"] for entry in by_status_raw}

        monthly_raw = (
            queryset.annotate(month=TruncMonth("created_at"))
            .values("month")
            .order_by("month")
            .annotate(total_count=Count("id"))
        )
        monthly = [
            {
                "month": entry["month"].strftime("%Y-%m") if entry["month"] else None,
                "total": entry["total_count"],
            }
            for entry in monthly_raw
        ]

        data = {
            "total": queryset.count(),
            "today": queryset.filter(created_at__date=today).count(),
            "en_cours": queryset.filter(status="en_cours").count(),
            "terminees": queryset.filter(status__in=["terminee", "envoye_client"]).count(),
            "annulees": queryset.filter(status="annulee").count(),
            "by_status": by_status,
            "by_month": monthly,
        }
        return Response(data, status=status.HTTP_200_OK)


def _map_status_to_action_type(status_value):
    mapping = {
        "nouvelle": "CREATION",
        "en_cours": "AFFECTATION",
        "rapport_soumis": "SOUMISSION",
        "rapport_valide": "VALIDATION",
        "envoye_client": "ENVOI_CLIENT",
        "terminee": "CLOTURE",
        "annulee": "ANNULATION",
    }
    return mapping.get(status_value, "AUTRE")


def _get_timeline_filters(request):
    return {
        "type": (request.query_params.get("type") or "").strip() or None,
        "user": (request.query_params.get("user") or "").strip() or None,
        "date_from": (request.query_params.get("date_from") or "").strip() or None,
        "date_to": (request.query_params.get("date_to") or "").strip() or None,
        "source": (request.query_params.get("source") or "").strip() or None,
    }


def _build_timeline_events(commande, filters=None):
    filters = filters or {}
    events = []

    suivis_queryset = (
        SuiviCommande.objects.filter(commande=commande)
        .select_related("user")
    )

    filter_type = filters.get("type")
    filter_user = filters.get("user")
    filter_date_from = filters.get("date_from")
    filter_date_to = filters.get("date_to")
    filter_source = filters.get("source")

    if filter_type:
        suivis_queryset = suivis_queryset.filter(type=filter_type)
    if filter_user and str(filter_user).isdigit():
        suivis_queryset = suivis_queryset.filter(user_id=int(filter_user))
    if filter_date_from:
        suivis_queryset = suivis_queryset.filter(date_action__date__gte=filter_date_from)
    if filter_date_to:
        suivis_queryset = suivis_queryset.filter(date_action__date__lte=filter_date_to)

    suivis = suivis_queryset.order_by("-date_action")
    for suivi in suivis:
        events.append(
            {
                "source": "suivi",
                "id": suivi.id,
                "type": suivi.type,
                "type_label": suivi.get_type_display(),
                "action": suivi.action,
                "commentaire": suivi.commentaire,
                "date_action": suivi.date_action,
                "user": suivi.user.username if suivi.user else "Systeme",
            }
        )

    history_entries = commande.history.order_by("-history_date")[:100]
    for h in history_entries:
        history_user = getattr(h, "history_user", None)
        hist_type = "update"
        if h.history_type == "+":
            hist_type = "creation"
        elif h.history_type == "-":
            hist_type = "suppression"

        if filter_source and filter_source != "history":
            continue
        if filter_type and filter_type != hist_type:
            continue
        if filter_user and str(filter_user).isdigit():
            history_user_id = getattr(h, "history_user_id", None)
            if history_user_id != int(filter_user):
                continue
        if filter_date_from and h.history_date.date().isoformat() < filter_date_from:
            continue
        if filter_date_to and h.history_date.date().isoformat() > filter_date_to:
            continue

        events.append(
            {
                "source": "history",
                "id": h.history_id,
                "type": hist_type,
                "type_label": "Historique",
                "action": f"Modification en base ({h.history_type})",
                "commentaire": None,
                "date_action": h.history_date,
                "user": history_user.username if history_user else "Systeme",
            }
        )

    events = sorted(events, key=lambda x: x["date_action"], reverse=True)

    if filter_source and filter_source in {"suivi", "history"}:
        events = [ev for ev in events if ev["source"] == filter_source]
    return events


class OrderModuleTimelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, commande_id, *args, **kwargs):
        commande = Commande.objects.filter(id=commande_id).first()
        if not commande:
            return Response({"detail": "Commande non trouvée."}, status=status.HTTP_404_NOT_FOUND)

        filters = _get_timeline_filters(request)

        users = (
            SuiviCommande.objects.filter(commande=commande, user__isnull=False)
            .select_related("user")
            .values("user_id", "user__username")
            .distinct()
        )

        payload = {
            "commande": CheckCommandeSerializer(commande).data,
            "timeline": _build_timeline_events(commande, filters=filters),
            "status_choices": [{"value": s[0], "label": s[1]} for s in Commande.STATUS_CHOICES],
            "action_types": (
                [{"value": t[0], "label": t[1]} for t in SuiviCommande.TYPE_ACTIONS]
                + [
                    {"value": "creation", "label": "Historique création"},
                    {"value": "update", "label": "Historique mise à jour"},
                    {"value": "suppression", "label": "Historique suppression"},
                ]
            ),
            "timeline_users": [
                {"id": entry["user_id"], "username": entry["user__username"]}
                for entry in users
            ],
        }
        return Response(payload, status=status.HTTP_200_OK)

    def post(self, request, commande_id, *args, **kwargs):
        commande = Commande.objects.filter(id=commande_id).first()
        if not commande:
            return Response({"detail": "Commande non trouvée."}, status=status.HTTP_404_NOT_FOUND)

        action = (request.data.get("action") or "").strip()
        action_type = (request.data.get("type") or "AUTRE").strip()
        commentaire = (request.data.get("commentaire") or "").strip() or None
        new_status = _normalize_status_value(request.data.get("status"))
        validateur_id = request.data.get("validateur_id")

        if not action:
            return Response({"detail": "Le champ action est requis."}, status=status.HTTP_400_BAD_REQUEST)

        if action_type not in dict(SuiviCommande.TYPE_ACTIONS):
            action_type = "AUTRE"

        if new_status and new_status in dict(Commande.STATUS_CHOICES):
            commande.status = new_status
            if new_status == "envoye_client":
                commande.date_envoi_client = timezone.now()
                commande.email_envoye = True

        if validateur_id:
            validateur = User.objects.filter(id=validateur_id).first()
            commande.validateur = validateur

        commande.save()

        suivi = SuiviCommande.objects.create(
            commande=commande,
            user=request.user,
            action=action,
            type=action_type,
            commentaire=commentaire,
        )

        return Response(
            {
                "detail": "Action enregistrée.",
                "suivi_id": suivi.id,
                "timeline": _build_timeline_events(commande),
            },
            status=status.HTTP_201_CREATED,
        )


class OrderModuleStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, commande_id, *args, **kwargs):
        commande = Commande.objects.filter(id=commande_id).first()
        if not commande:
            return Response({"detail": "Commande non trouvée."}, status=status.HTTP_404_NOT_FOUND)

        new_status = _normalize_status_value(request.data.get("status"))
        commentaire = (request.data.get("commentaire") or "").strip()

        if new_status not in dict(Commande.STATUS_CHOICES):
            return Response(
                {
                    "detail": "Statut invalide.",
                    "errors": {
                        "status": [
                            f"Valeur reçue: '{request.data.get('status')}'. Valeurs attendues: {', '.join(dict(Commande.STATUS_CHOICES).keys())}"
                        ]
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        commande.status = new_status
        if new_status == "envoye_client":
            commande.date_envoi_client = timezone.now()
            commande.email_envoye = True
        commande.save()

        SuiviCommande.objects.create(
            commande=commande,
            user=request.user,
            action=f"Changement de statut -> {new_status}",
            type=_map_status_to_action_type(new_status),
            commentaire=commentaire or None,
        )

        return Response(
            {
                "detail": "Statut mis à jour.",
                "status": commande.status,
                "date_envoi_client": commande.date_envoi_client,
            },
            status=status.HTTP_200_OK,
        )


class OrderModuleTimelineExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, commande_id, *args, **kwargs):
        commande = Commande.objects.filter(id=commande_id).first()
        if not commande:
            return Response({"detail": "Commande non trouvée."}, status=status.HTTP_404_NOT_FOUND)

        export_format = (request.query_params.get("format") or "csv").lower()
        filters = _get_timeline_filters(request)
        timeline = _build_timeline_events(commande, filters=filters)

        if export_format == "csv":
            response = HttpResponse(content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = f'attachment; filename="timeline_commande_{commande_id}.csv"'
            writer = csv.writer(response)
            writer.writerow(["Date", "Source", "Type", "Action", "Commentaire", "Utilisateur"])
            for ev in timeline:
                writer.writerow(
                    [
                        ev["date_action"].strftime("%Y-%m-%d %H:%M:%S") if ev.get("date_action") else "",
                        ev.get("source", ""),
                        ev.get("type_label") or ev.get("type", ""),
                        ev.get("action", ""),
                        ev.get("commentaire", "") or "",
                        ev.get("user", ""),
                    ]
                )
            return response

        if export_format == "pdf":
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
            from reportlab.pdfgen import canvas

            buffer = BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            y = height - 2 * cm

            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(2 * cm, y, f"Timeline Commande #{commande_id} - {commande.notre_ref or '-'}")
            y -= 0.8 * cm
            pdf.setFont("Helvetica", 9)
            pdf.drawString(2 * cm, y, f"Entreprise: {commande.raison_sociale or '-'}")
            y -= 0.8 * cm

            for ev in timeline:
                if y < 2 * cm:
                    pdf.showPage()
                    y = height - 2 * cm
                    pdf.setFont("Helvetica", 9)

                date_txt = ev["date_action"].strftime("%Y-%m-%d %H:%M") if ev.get("date_action") else "-"
                line = f"[{date_txt}] {ev.get('type_label') or ev.get('type', '-')}"
                pdf.drawString(2 * cm, y, line[:120])
                y -= 0.5 * cm
                pdf.drawString(2.5 * cm, y, f"Action: {(ev.get('action') or '-')[:140]}")
                y -= 0.45 * cm
                if ev.get("commentaire"):
                    pdf.drawString(2.5 * cm, y, f"Commentaire: {ev['commentaire'][:140]}")
                    y -= 0.45 * cm
                pdf.drawString(2.5 * cm, y, f"Par: {ev.get('user', '-')}, source: {ev.get('source', '-')}")
                y -= 0.6 * cm

            pdf.save()
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="timeline_commande_{commande_id}.pdf"'
            return response

        return Response({"detail": "Format non supporté. Utilisez csv ou pdf."}, status=status.HTTP_400_BAD_REQUEST)
