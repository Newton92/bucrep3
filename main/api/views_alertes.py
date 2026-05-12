import json

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import Acheteur, Pays, Warning, WarningAttachment
from main.serializers import (
    AcheteurSimpleSerializer,
    WarningDetailSerializer,
    WarningListSerializer,
    WarningUpsertSerializer,
)


def _send_warning_email(warning):
    """Envoie l'alerte par email selon les champs email_to/cc/bcc/subject."""
    to_list = warning.get_email_to_list()
    if not to_list:
        return False

    subject = warning.email_subject or warning.titre
    cc_list = warning.get_email_cc_list()
    bcc_list = warning.get_email_bcc_list()

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'bucrepcontact@gmail.com')

    # Corps texte brut (fallback)
    import re
    text_body = re.sub(r'<[^>]+>', ' ', warning.description or '').strip()

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=to_list,
        cc=cc_list if cc_list else [],
        bcc=bcc_list if bcc_list else [],
    )
    msg.attach_alternative(warning.description or '', 'text/html')
    msg.send(fail_silently=False)

    warning.email_sent = True
    warning.email_sent_at = timezone.now()
    warning.save(update_fields=['email_sent', 'email_sent_at'])
    return True


def _resolve_selected_pays_id(request):
    pays_id = request.query_params.get("pays_id")
    if pays_id:
        try:
            parsed = int(pays_id)
            if Pays.objects.filter(id=parsed).exists():
                return parsed
        except (TypeError, ValueError):
            pass

    session_value = request.session.get("selected_pays_id")
    if session_value:
        try:
            parsed = int(session_value)
            if Pays.objects.filter(id=parsed).exists():
                return parsed
        except (TypeError, ValueError):
            pass

    user_pays = getattr(request.user, "pays", None)
    if user_pays:
        return user_pays.id

    return None


class WarningPaginationMixin:
    default_page_size = 10
    max_page_size = 100

    def _parse_int(self, value, default):
        try:
            parsed = int(value)
            return parsed if parsed > 0 else default
        except (TypeError, ValueError):
            return default

    def paginate(self, queryset, request):
        page = self._parse_int(request.query_params.get("page", 1), 1)
        page_size = self._parse_int(
            request.query_params.get("page_size", self.default_page_size),
            self.default_page_size,
        )
        page_size = min(page_size, self.max_page_size)

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        return paginator, page_obj, page_size


class ListWarningView(APIView, WarningPaginationMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get("search", "").strip()
        sent_only = request.query_params.get("sent_only", "").lower() in ("1", "true", "yes")

        warnings = (
            Warning.objects.select_related("created_by")
            .prefetch_related("acheteurs", "warning_attachments")
            .all()
            .order_by("-created_at")
        )

        if sent_only:
            warnings = warnings.filter(email_sent=True)

        if search_query:
            warnings = warnings.filter(
                Q(titre__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(created_by__username__icontains=search_query)
                | Q(acheteurs__nom__icontains=search_query)
            ).distinct()

        paginator, page_obj, page_size = self.paginate(warnings, request)
        serializer = WarningListSerializer(
            page_obj.object_list,
            many=True,
            context={"request": request},
        )

        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "page": page_obj.number,
                "page_size": page_size,
                "next": page_obj.has_next(),
                "previous": page_obj.has_previous(),
            }
        )


class ListWarningAcheteurView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        search_query = request.query_params.get("search", "").strip()
        selected_pays_id = _resolve_selected_pays_id(request)

        acheteurs = Acheteur.objects.all().order_by("nom")

        if selected_pays_id:
            acheteurs = acheteurs.filter(pays_id=selected_pays_id)

        if search_query:
            acheteurs = acheteurs.filter(
                Q(nom__icontains=search_query) | Q(code__icontains=search_query)
            )

        serializer = AcheteurSimpleSerializer(acheteurs[:150], many=True)
        return Response({"results": serializer.data, "selected_pays_id": selected_pays_id})


class AddWarningView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = WarningUpsertSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        warning = serializer.save(created_by=request.user)

        files = request.FILES.getlist("attachments")
        for file_obj in files:
            WarningAttachment.objects.create(warning=warning, upload=file_obj)

        # Envoi email immédiat si demandé
        email_error = None
        if request.data.get("send_now") in (True, "true", "1", 1):
            try:
                _send_warning_email(warning)
            except Exception as exc:
                email_error = str(exc)

        data = WarningDetailSerializer(warning, context={"request": request}).data
        if email_error:
            data["email_error"] = email_error
        return Response(data, status=status.HTTP_201_CREATED)


class GetWarningView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        warning = get_object_or_404(
            Warning.objects.prefetch_related("acheteurs", "warning_attachments"),
            id=id,
        )
        serializer = WarningDetailSerializer(warning, context={"request": request})
        return Response(serializer.data)


class EditWarningView(APIView):
    permission_classes = [IsAuthenticated]

    def _extract_ids(self, request, key):
        values = []
        data = request.data

        if hasattr(data, "getlist"):
            values.extend(data.getlist(key))
            values.extend(data.getlist(f"{key}[]"))

        raw_value = data.get(key)
        if raw_value is not None:
            if isinstance(raw_value, list):
                values.extend(raw_value)
            elif isinstance(raw_value, str):
                cleaned = raw_value.strip()
                if cleaned:
                    try:
                        parsed = json.loads(cleaned)
                        if isinstance(parsed, list):
                            values.extend(parsed)
                        else:
                            values.append(parsed)
                    except json.JSONDecodeError:
                        values.extend([item for item in cleaned.split(",") if item])
            else:
                values.append(raw_value)

        output = []
        for value in values:
            try:
                output.append(int(value))
            except (TypeError, ValueError):
                continue

        return list(dict.fromkeys(output))

    @transaction.atomic
    def put(self, request, id, *args, **kwargs):
        warning = get_object_or_404(Warning, id=id)

        serializer = WarningUpsertSerializer(warning, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        warning = serializer.save()

        attachment_ids_to_delete = self._extract_ids(request, "attachments_delete")
        if attachment_ids_to_delete:
            attachments_to_delete = WarningAttachment.objects.filter(
                warning=warning, id__in=attachment_ids_to_delete
            )
            for attachment in attachments_to_delete:
                attachment.delete()

        files_to_add = request.FILES.getlist("attachments_add")
        for file_obj in files_to_add:
            WarningAttachment.objects.create(warning=warning, upload=file_obj)

        # Envoi email immédiat si demandé
        email_error = None
        if request.data.get("send_now") in (True, "true", "1", 1):
            try:
                _send_warning_email(warning)
            except Exception as exc:
                email_error = str(exc)

        data = WarningDetailSerializer(warning, context={"request": request}).data
        if email_error:
            data["email_error"] = email_error
        return Response(data)


class DeleteWarningView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        if not isinstance(ids, list) or not ids:
            return Response(
                {"error": "Une liste d'IDs est requise."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        warnings = Warning.objects.filter(id__in=ids)
        if not warnings.exists():
            return Response(
                {"error": "Aucune alerte trouvée pour les IDs fournis."},
                status=status.HTTP_404_NOT_FOUND,
            )

        deleted_count = 0
        for warning in warnings:
            for attachment in warning.warning_attachments.all():
                attachment.delete()
            warning.delete()
            deleted_count += 1

        return Response(
            {"message": f"{deleted_count} alerte(s) supprimée(s) avec succès."},
            status=status.HTTP_200_OK,
        )


class DeleteWarningAttachmentView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id, *args, **kwargs):
        attachment = get_object_or_404(WarningAttachment, id=id)
        attachment.delete()
        return Response({"message": "Pièce jointe supprimée avec succès."})


class SendWarningEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id, *args, **kwargs):
        warning = get_object_or_404(Warning, id=id)

        # Mise à jour éventuelle des champs email avant envoi
        for field in ("email_to", "email_cc", "email_bcc", "email_subject"):
            if field in request.data:
                setattr(warning, field, request.data[field])
        warning.save(update_fields=["email_to", "email_cc", "email_bcc", "email_subject"])

        if not warning.get_email_to_list():
            return Response(
                {"error": "Veuillez saisir au moins un destinataire (champ À)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            _send_warning_email(warning)
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        data = WarningDetailSerializer(warning, context={"request": request}).data
        return Response({"message": "Alerte envoyée avec succès.", "warning": data})
