"""
Mail entrant — API views pour la configuration IMAP, les sources et l'inbox.

Routes (toutes sous /api/v1/mail/):
  GET/POST   imap/                    → lister / créer une config IMAP
  GET/PUT/DEL imap/<id>/              → détail / modifier / supprimer une config
  POST       imap/<id>/test/          → tester la connexion IMAP d'une config
  POST       imap/<id>/poll/          → déclencher un poll immédiat
  GET        imap/status/             → statut global du service de polling
  GET/POST   sources/                 → lister / créer une source
  PATCH/DEL  sources/<id>/            → modifier / supprimer
  POST       sources/<id>/toggle/     → activer/désactiver
  GET        inbox/                   → liste mails interceptés
  GET        inbox/<id>/              → détail + pièces jointes
  GET        inbox/stats/             → compteurs par statut
  POST       inbox/<id>/dispatch/     → dispatcher à un utilisateur
  POST       inbox/<id>/self-dispatch/ → se dispatcher le mail
  POST       inbox/<id>/accept/       → accepter le dossier
  POST       inbox/<id>/reassign/     → réaffecter
  POST       inbox/<id>/reject/       → rejeter
  POST       inbox/<id>/restore/      → remettre en attente
  POST       inbox/<id>/processed/    → marquer comme traité
  GET        users/                   → liste des utilisateurs pour le dispatch
  GET        attachments/<id>/download/ → télécharger une pièce jointe
"""

import imaplib
import logging
import mimetypes
import os
import socket
import threading

from django.conf import settings as dj_settings
from django.core.mail import EmailMultiAlternatives
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main.models import MailInboxConfig, MailSource, IncomingMail, MailAttachment, User

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _is_root(user) -> bool:
    return getattr(user, 'role', None) == 'Root'


def _imap_config_payload(cfg):
    return {
        "id": cfg.id,
        "name": cfg.name,
        "imap_host": cfg.imap_host,
        "imap_port": cfg.imap_port,
        "imap_user": cfg.imap_user,
        "imap_password_set": bool(cfg.imap_password),
        "use_ssl": cfg.use_ssl,
        "mailbox": cfg.mailbox,
        "is_active": cfg.is_active,
        "last_polled_at": cfg.last_polled_at,
        "last_error": cfg.last_error,
        "updated_at": cfg.updated_at,
    }


def _source_payload(src):
    return {
        "id": src.id,
        "client_name": src.client_name,
        "email_or_domain": src.email_or_domain,
        "is_domain": src.is_domain,
        "notes": src.notes,
        "is_active": src.is_active,
        "created_at": src.created_at,
    }


def _mail_list_payload(mail):
    return {
        "id": mail.id,
        "from_email": mail.from_email,
        "from_name": mail.from_name,
        "subject": mail.subject,
        "received_at": mail.received_at,
        "status": mail.status,
        "mail_source": {
            "id": mail.mail_source_id,
            "client_name": mail.mail_source.client_name if mail.mail_source else "",
            "email_or_domain": mail.mail_source.email_or_domain if mail.mail_source else "",
        } if mail.mail_source_id else None,
        "assigned_to": {
            "id": mail.assigned_to_id,
            "name": f"{mail.assigned_to.get_full_name() or mail.assigned_to.username}",
        } if mail.assigned_to_id else None,
        "attachments_count": mail.attachments.count(),
    }


def _mail_detail_payload(mail):
    payload = _mail_list_payload(mail)
    payload.update({
        "body_text": mail.body_text,
        "body_html": mail.body_html,
        "dispatch_note": mail.dispatch_note,
        "dispatched_at": mail.dispatched_at,
        "dispatched_by": {
            "id": mail.dispatched_by_id,
            "name": f"{mail.dispatched_by.get_full_name() or mail.dispatched_by.username}",
        } if mail.dispatched_by_id else None,
        "accepted_at": mail.accepted_at,
        "accepted_by": {
            "id": mail.accepted_by_id,
            "name": f"{mail.accepted_by.get_full_name() or mail.accepted_by.username}",
        } if mail.accepted_by_id else None,
        "commande": mail.commande_id,
        "attachments": [
            {
                "id": a.id,
                "filename": a.filename,
                "content_type": a.content_type,
                "size": a.size,
                "download_url": f"/api/v1/mail/attachments/{a.id}/download/",
            }
            for a in mail.attachments.all()
        ],
    })
    return payload


def _minutes_ago(dt):
    if not dt:
        return None
    return int((timezone.now() - dt).total_seconds() // 60)


# ─────────────────────────────────────────────────────────────
# Polling schedule — lecture / mise à jour de l'intervalle Beat
# ─────────────────────────────────────────────────────────────

POLL_TASK_NAME = "poll-mail-inbox"


def _get_poll_task():
    """Retourne la PeriodicTask de polling, ou None."""
    try:
        from django_celery_beat.models import PeriodicTask
        return PeriodicTask.objects.get(name=POLL_TASK_NAME)
    except Exception:
        return None


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def mail_poll_schedule(request):
    """Lire ou modifier l'intervalle de polling automatique."""
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    task = _get_poll_task()

    if request.method == "GET":
        if task is None:
            return Response({
                "configured": False,
                "enabled": False,
                "interval_minutes": 5,
                "last_run_at": None,
                "next_run_at": None,
            })

        minutes = None
        if task.interval:
            period = task.interval.period  # "minutes", "hours", etc.
            every = task.interval.every
            if period == "minutes":
                minutes = every
            elif period == "hours":
                minutes = every * 60
            elif period == "seconds":
                minutes = round(every / 60, 1)

        last = task.last_run_at
        next_run = None
        if last and minutes:
            from datetime import timedelta as _td
            next_run = last + _td(minutes=minutes)

        return Response({
            "configured": True,
            "enabled": task.enabled,
            "interval_minutes": minutes or 5,
            "last_run_at": last,
            "next_run_at": next_run,
        })

    # PUT — modifier l'intervalle
    data = request.data or {}
    try:
        minutes = int(data.get("interval_minutes") or 5)
        if minutes < 1:
            minutes = 1
    except (ValueError, TypeError):
        return Response({"detail": "interval_minutes doit être un entier positif."}, status=400)

    enabled = bool(data.get("enabled", True))

    try:
        from django_celery_beat.models import PeriodicTask, IntervalSchedule
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=minutes,
            period=IntervalSchedule.MINUTES,
        )
        if task is None:
            PeriodicTask.objects.create(
                name=POLL_TASK_NAME,
                task="main.tasks.poll_mail_inbox",
                interval=schedule,
                enabled=enabled,
            )
        else:
            task.interval = schedule
            task.enabled = enabled
            task.save(update_fields=["interval", "enabled"])
        return Response({
            "configured": True,
            "enabled": enabled,
            "interval_minutes": minutes,
        })
    except Exception as exc:
        return Response({"detail": str(exc)}, status=500)


# ─────────────────────────────────────────────────────────────
# IMAP Config — multi-record
# ─────────────────────────────────────────────────────────────

def _cfg_health(cfg):
    """Retourne (health, label) pour une config."""
    if not cfg.imap_host:
        return "unconfigured", "Non configuré"
    if not cfg.is_active:
        return "inactive", "Arrêté"
    minutes = _minutes_ago(cfg.last_polled_at)
    if minutes is None:
        return "stale", "En attente du premier passage"
    if cfg.last_error:
        return "error", f"Erreur — {cfg.last_error[:60]}"
    if minutes < 10:
        return "healthy", f"Actif — il y a {minutes} min"
    if minutes < 20:
        return "delayed", f"En retard — il y a {minutes} min"
    return "stale", f"Inactif — il y a {minutes} min"


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def mail_imap_config(request):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    if request.method == "GET":
        configs = MailInboxConfig.objects.all().order_by("id")
        return Response([_imap_config_payload(c) for c in configs])

    # POST — créer une nouvelle config
    data = request.data or {}
    imap_host = (data.get("imap_host") or "").strip()
    imap_user = (data.get("imap_user") or "").strip()
    if not imap_host or not imap_user:
        return Response({"detail": "imap_host et imap_user sont requis."}, status=400)

    cfg = MailInboxConfig.objects.create(
        name=(data.get("name") or "").strip(),
        imap_host=imap_host,
        imap_port=int(data.get("imap_port") or 993),
        imap_user=imap_user,
        imap_password=(data.get("imap_password") or ""),
        use_ssl=bool(data.get("use_ssl", True)),
        mailbox=(data.get("mailbox") or "INBOX").strip() or "INBOX",
        is_active=bool(data.get("is_active", True)),
    )
    return Response(_imap_config_payload(cfg), status=201)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def mail_imap_config_detail(request, config_id: int):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    try:
        cfg = MailInboxConfig.objects.get(id=config_id)
    except MailInboxConfig.DoesNotExist:
        return Response({"detail": "Configuration introuvable."}, status=404)

    if request.method == "GET":
        return Response(_imap_config_payload(cfg))

    if request.method == "DELETE":
        cfg.delete()
        return Response(status=204)

    # PUT — modifier
    data = request.data or {}
    if "name" in data:
        cfg.name = (data["name"] or "").strip()
    cfg.imap_host = (data.get("imap_host") or "").strip()
    cfg.imap_port = int(data.get("imap_port") or 993)
    cfg.imap_user = (data.get("imap_user") or "").strip()
    cfg.use_ssl = bool(data.get("use_ssl", True))
    cfg.mailbox = (data.get("mailbox") or "INBOX").strip() or "INBOX"
    cfg.is_active = bool(data.get("is_active", True))
    if data.get("imap_password"):
        cfg.imap_password = data["imap_password"]
    if not cfg.imap_host or not cfg.imap_user:
        return Response({"detail": "imap_host et imap_user sont requis."}, status=400)
    cfg.save()
    return Response(_imap_config_payload(cfg))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mail_imap_test(request, config_id: int = None):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    data = request.data or {}

    # Si appelé avec un config_id dans l'URL, utiliser les données sauvegardées
    if config_id is not None:
        try:
            cfg = MailInboxConfig.objects.get(id=config_id)
        except MailInboxConfig.DoesNotExist:
            return Response({"detail": "Configuration introuvable."}, status=404)
        host = cfg.imap_host
        port = cfg.imap_port
        user = cfg.imap_user
        password = cfg.imap_password
        use_ssl = cfg.use_ssl
        mailbox = cfg.mailbox
    else:
        host = (data.get("imap_host") or "").strip()
        port = int(data.get("imap_port") or 993)
        user = (data.get("imap_user") or "").strip()
        password = data.get("imap_password") or ""
        use_ssl = bool(data.get("use_ssl", True))
        mailbox = (data.get("mailbox") or "INBOX").strip()
        # Fallback : si le mot de passe est vide et qu'un config_id est fourni dans le corps,
        # on récupère le mot de passe sauvegardé (cas de l'édition sans re-saisie du mdp)
        if not password and data.get("config_id"):
            try:
                saved = MailInboxConfig.objects.get(id=int(data["config_id"]))
                password = saved.imap_password
            except (MailInboxConfig.DoesNotExist, ValueError, TypeError):
                pass

    if not host or not user:
        return Response({"detail": "Hôte et utilisateur requis."}, status=400)

    try:
        imap = imaplib.IMAP4_SSL(host, port) if use_ssl else imaplib.IMAP4(host, port)
        imap.login(user, password)
        st, resp = imap.select(mailbox, readonly=True)
        msg_count = int(resp[0]) if st == "OK" and resp[0] else 0
        imap.logout()
        return Response({
            "success": True,
            "message": f"Connexion réussie. {msg_count} message(s) dans {mailbox}.",
        })
    except imaplib.IMAP4.error as e:
        return Response({"success": False, "message": f"Erreur IMAP : {e}"}, status=400)
    except socket.gaierror:
        return Response({"success": False, "message": "Hôte IMAP introuvable."}, status=400)
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mail_imap_poll(request, config_id: int = None):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    from django.core.management import call_command

    if config_id is not None:
        try:
            cfg = MailInboxConfig.objects.get(id=config_id)
        except MailInboxConfig.DoesNotExist:
            return Response({"detail": "Configuration introuvable."}, status=404)
        if not cfg.is_active or not cfg.imap_host:
            return Response({"detail": "Configuration IMAP inactive ou non configurée."}, status=400)
        try:
            call_command("poll_mail", config_id=config_id)
            cfg.refresh_from_db()
            return Response({
                "success": True,
                "last_polled_at": cfg.last_polled_at,
                "last_error": cfg.last_error,
            })
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=500)
    else:
        # Déclencher le poll pour toutes les configs actives
        if not MailInboxConfig.objects.filter(is_active=True).exclude(imap_host="").exists():
            return Response({"detail": "Aucune configuration IMAP active."}, status=404)
        try:
            call_command("poll_mail")
            return Response({"success": True})
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mail_cron_status(request):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    configs = list(MailInboxConfig.objects.filter(is_active=True).order_by("id"))

    if not configs:
        return Response({
            "health": "unconfigured",
            "health_label": "Aucune boîte configurée",
            "is_active": False,
            "configs": [],
        })

    config_statuses = []
    health_priority = {"error": 0, "stale": 1, "delayed": 2, "inactive": 3, "unconfigured": 4, "healthy": 5}
    worst_health = "healthy"

    for cfg in configs:
        health, label = _cfg_health(cfg)
        if health_priority.get(health, 5) < health_priority.get(worst_health, 5):
            worst_health = health
        config_statuses.append({
            "id": cfg.id,
            "name": cfg.name or cfg.imap_user,
            "health": health,
            "health_label": label,
            "last_run": cfg.last_polled_at,
            "last_error": cfg.last_error,
            "minutes_since_last_run": _minutes_ago(cfg.last_polled_at),
        })

    health_labels = {
        "healthy": "Tout actif",
        "delayed": "En retard",
        "stale": "Inactif",
        "error": "Erreur IMAP",
        "inactive": "Arrêté",
        "unconfigured": "Non configuré",
    }

    return Response({
        "health": worst_health,
        "health_label": health_labels.get(worst_health, worst_health),
        "is_active": True,
        "configs": config_statuses,
    })


# ─────────────────────────────────────────────────────────────
# Sources mail
# ─────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def mail_sources(request):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    if request.method == "GET":
        sources = MailSource.objects.all()
        return Response([_source_payload(s) for s in sources])

    data = request.data or {}
    email_or_domain = (data.get("email_or_domain") or "").strip().lower()
    if not email_or_domain:
        return Response({"detail": "email_or_domain est requis."}, status=400)
    if MailSource.objects.filter(email_or_domain=email_or_domain).exists():
        return Response({"detail": "Cette source existe déjà."}, status=400)

    src = MailSource.objects.create(
        client_name=(data.get("client_name") or "").strip(),
        email_or_domain=email_or_domain,
        notes=(data.get("notes") or "").strip(),
        is_active=bool(data.get("is_active", True)),
    )
    return Response(_source_payload(src), status=201)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def mail_source_detail(request, source_id: int):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    try:
        src = MailSource.objects.get(id=source_id)
    except MailSource.DoesNotExist:
        return Response({"detail": "Source introuvable."}, status=404)

    if request.method == "DELETE":
        src.delete()
        return Response(status=204)

    data = request.data or {}
    if "client_name" in data:
        src.client_name = (data["client_name"] or "").strip()
    if "email_or_domain" in data:
        new_val = (data["email_or_domain"] or "").strip().lower()
        if new_val and new_val != src.email_or_domain:
            if MailSource.objects.filter(email_or_domain=new_val).exists():
                return Response({"detail": "Cette source existe déjà."}, status=400)
            src.email_or_domain = new_val
    if "notes" in data:
        src.notes = (data["notes"] or "").strip()
    if "is_active" in data:
        src.is_active = bool(data["is_active"])
    src.save()
    return Response(_source_payload(src))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mail_source_toggle(request, source_id: int):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    try:
        src = MailSource.objects.get(id=source_id)
    except MailSource.DoesNotExist:
        return Response({"detail": "Source introuvable."}, status=404)

    src.is_active = not src.is_active
    src.save()
    return Response(_source_payload(src))


# ─────────────────────────────────────────────────────────────
# Inbox — mails interceptés
# ─────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mail_inbox_stats(request):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    qs = IncomingMail.objects.all()
    return Response({
        "pending":    qs.filter(status=IncomingMail.Status.PENDING).count(),
        "dispatched": qs.filter(status=IncomingMail.Status.DISPATCHED).count(),
        "accepted":   qs.filter(status=IncomingMail.Status.ACCEPTED).count(),
        "processed":  qs.filter(status=IncomingMail.Status.PROCESSED).count(),
        "rejected":   qs.filter(status=IncomingMail.Status.REJECTED).count(),
        "total":      qs.count(),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mail_inbox(request):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    qs = IncomingMail.objects.select_related(
        "mail_source", "assigned_to", "dispatched_by"
    ).prefetch_related("attachments")

    status_filter = request.GET.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter.upper())

    search = (request.GET.get("search") or "").strip()
    if search:
        from django.db.models import Q
        qs = qs.filter(
            Q(subject__icontains=search) |
            Q(from_email__icontains=search) |
            Q(from_name__icontains=search)
        )

    page = max(1, int(request.GET.get("page", 1)))
    page_size = 20
    total = qs.count()
    mails = qs.order_by("-received_at")[(page - 1) * page_size: page * page_size]

    all_qs = IncomingMail.objects.all()
    stats = {
        "total":      all_qs.count(),
        "pending":    all_qs.filter(status=IncomingMail.Status.PENDING).count(),
        "dispatched": all_qs.filter(status=IncomingMail.Status.DISPATCHED).count(),
        "accepted":   all_qs.filter(status=IncomingMail.Status.ACCEPTED).count(),
        "processed":  all_qs.filter(status=IncomingMail.Status.PROCESSED).count(),
        "rejected":   all_qs.filter(status=IncomingMail.Status.REJECTED).count(),
    }

    return Response({
        "count": total,
        "page": page,
        "page_size": page_size,
        "results": [_mail_list_payload(m) for m in mails],
        "stats": stats,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mail_inbox_detail(request, mail_id: int):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    try:
        mail = (
            IncomingMail.objects
            .select_related("mail_source", "assigned_to", "dispatched_by", "accepted_by", "commande")
            .prefetch_related("attachments")
            .get(id=mail_id)
        )
    except IncomingMail.DoesNotExist:
        return Response({"detail": "Mail introuvable."}, status=404)

    return Response(_mail_detail_payload(mail))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mail_dispatch(request, mail_id: int):
    """Dispatcher un mail à un utilisateur."""
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    try:
        mail = IncomingMail.objects.select_related("mail_source", "assigned_to").get(id=mail_id)
    except IncomingMail.DoesNotExist:
        return Response({"detail": "Mail introuvable."}, status=404)

    data = request.data or {}
    assigned_to_id = data.get("assigned_to_id")
    dispatch_note = (data.get("dispatch_note") or "").strip()

    if not assigned_to_id:
        return Response({"detail": "assigned_to_id est requis."}, status=400)

    try:
        assignee = User.objects.get(id=assigned_to_id, is_active=True)
    except User.DoesNotExist:
        return Response({"detail": "Utilisateur introuvable."}, status=404)

    mail.assigned_to = assignee
    mail.dispatch_note = dispatch_note
    mail.dispatched_by = request.user
    mail.dispatched_at = timezone.now()
    mail.accepted_at = None
    mail.accepted_by = None
    mail.status = IncomingMail.Status.DISPATCHED
    mail.save()

    threading.Thread(target=_notify_dispatch, args=(mail, assignee), daemon=True).start()
    return Response(_mail_detail_payload(mail))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mail_self_dispatch(request, mail_id: int):
    """L'administrateur se dispatche le mail à lui-même."""
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    try:
        mail = IncomingMail.objects.select_related("mail_source").get(id=mail_id)
    except IncomingMail.DoesNotExist:
        return Response({"detail": "Mail introuvable."}, status=404)

    dispatch_note = (request.data.get("dispatch_note") or "").strip()
    mail.assigned_to = request.user
    mail.dispatched_by = request.user
    mail.dispatched_at = timezone.now()
    mail.dispatch_note = dispatch_note
    mail.accepted_at = None
    mail.accepted_by = None
    mail.status = IncomingMail.Status.DISPATCHED
    mail.save()
    return Response(_mail_detail_payload(mail))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mail_accept(request, mail_id: int):
    """L'utilisateur désigné accepte formellement le dossier."""
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    try:
        mail = IncomingMail.objects.select_related(
            "mail_source", "assigned_to", "dispatched_by", "accepted_by"
        ).prefetch_related("attachments").get(id=mail_id)
    except IncomingMail.DoesNotExist:
        return Response({"detail": "Mail introuvable."}, status=404)

    if mail.status != IncomingMail.Status.DISPATCHED:
        return Response({"detail": "Ce mail n'est pas en statut dispatché."}, status=400)

    if mail.assigned_to_id != request.user.id:
        return Response({"detail": "Vous n'êtes pas l'assigné de ce mail."}, status=403)

    if not mail.accepted_at:
        mail.accepted_at = timezone.now()
        mail.accepted_by = request.user
        mail.status = IncomingMail.Status.ACCEPTED
        mail.save(update_fields=["accepted_at", "accepted_by", "status", "updated_at"])

    return Response(_mail_detail_payload(mail))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mail_reassign(request, mail_id: int):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    try:
        mail = IncomingMail.objects.select_related("mail_source", "assigned_to").get(id=mail_id)
    except IncomingMail.DoesNotExist:
        return Response({"detail": "Mail introuvable."}, status=404)

    data = request.data or {}
    new_assignee_id = data.get("assigned_to_id")
    dispatch_note = (data.get("dispatch_note") or "").strip()

    if not new_assignee_id:
        return Response({"detail": "assigned_to_id est requis."}, status=400)

    try:
        assignee = User.objects.get(id=new_assignee_id, is_active=True)
    except User.DoesNotExist:
        return Response({"detail": "Utilisateur introuvable."}, status=404)

    mail.assigned_to = assignee
    mail.dispatched_by = request.user
    mail.dispatched_at = timezone.now()
    mail.dispatch_note = dispatch_note
    mail.accepted_at = None
    mail.accepted_by = None
    mail.status = IncomingMail.Status.DISPATCHED
    mail.save()

    threading.Thread(target=_notify_dispatch, args=(mail, assignee), daemon=True).start()
    return Response(_mail_detail_payload(mail))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mail_reject(request, mail_id: int):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    try:
        mail = IncomingMail.objects.get(id=mail_id)
    except IncomingMail.DoesNotExist:
        return Response({"detail": "Mail introuvable."}, status=404)

    mail.status = IncomingMail.Status.REJECTED
    mail.save(update_fields=["status", "updated_at"])
    return Response(_mail_list_payload(mail))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mail_restore(request, mail_id: int):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    try:
        mail = IncomingMail.objects.get(id=mail_id)
    except IncomingMail.DoesNotExist:
        return Response({"detail": "Mail introuvable."}, status=404)

    mail.status = IncomingMail.Status.PENDING
    mail.assigned_to = None
    mail.dispatched_at = None
    mail.dispatched_by = None
    mail.dispatch_note = ""
    mail.accepted_at = None
    mail.accepted_by = None
    mail.save()
    return Response(_mail_list_payload(mail))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mail_mark_processed(request, mail_id: int):
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    try:
        mail = IncomingMail.objects.get(id=mail_id)
    except IncomingMail.DoesNotExist:
        return Response({"detail": "Mail introuvable."}, status=404)

    mail.status = IncomingMail.Status.PROCESSED
    mail.save(update_fields=["status", "updated_at"])
    return Response(_mail_list_payload(mail))


# ─────────────────────────────────────────────────────────────
# Utilisateurs pour le dispatch
# ─────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mail_users_list(request):
    """Liste des utilisateurs actifs disponibles pour le dispatch."""
    if not _is_root(request.user):
        return Response({"detail": "Réservé aux administrateurs."}, status=403)

    users = User.objects.filter(is_active=True).order_by("last_name", "first_name")
    return Response([
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.get_full_name() or u.username,
            "email": u.email,
            "role": getattr(u, 'role', ''),
        }
        for u in users
    ])


# ─────────────────────────────────────────────────────────────
# Pièces jointes
# ─────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mail_attachment_download(request, attachment_id: int):
    if not _is_root(request.user):
        return Response({"detail": "Accès refusé."}, status=403)

    try:
        att = MailAttachment.objects.get(id=attachment_id)
    except MailAttachment.DoesNotExist:
        raise Http404

    if not att.file or not att.file.name:
        return Response({"detail": "Fichier introuvable."}, status=404)

    try:
        file_handle = att.file.open("rb")
    except (FileNotFoundError, OSError):
        return Response({"detail": "Fichier introuvable sur le serveur."}, status=404)

    content_type, _ = mimetypes.guess_type(att.filename or att.file.name)
    response = FileResponse(file_handle, content_type=content_type or "application/octet-stream")
    filename = (att.filename or os.path.basename(att.file.name)).replace('"', "")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ─────────────────────────────────────────────────────────────
# Notification de dispatch
# ─────────────────────────────────────────────────────────────

def _notify_dispatch(mail: IncomingMail, assignee: User):
    if not assignee.email:
        return

    first_name = assignee.first_name or assignee.username
    subject_line = f"[BUCREP] Demande client assignée — {mail.subject[:80]}"
    body_excerpt = (mail.body_text or "").strip()[:300]
    if len(mail.body_text or "") > 300:
        body_excerpt += "…"
    note_block = f"\n    Note de dispatch : {mail.dispatch_note}\n" if mail.dispatch_note else ""

    frontend_url = getattr(dj_settings, "FRONTEND_BASE_URL", "https://application.bucrep.net")
    inbox_url = f"{frontend_url}/root-dashboard/parametrage/boite-de-reception"

    text_body = (
        f"Bonjour {first_name},\n\n"
        f"Un dossier client vous a été assigné sur la plateforme BUCREP.\n\n"
        f"De      : {mail.from_name or mail.from_email} <{mail.from_email}>\n"
        f"Objet   : {mail.subject}\n"
        f"Reçu le : {mail.received_at.strftime('%d/%m/%Y à %H:%M')}\n"
        f"{note_block}\n"
        f"Aperçu :\n{body_excerpt}\n\n"
        f"Connectez-vous pour consulter et prendre en charge ce dossier :\n{inbox_url}\n\n"
        f"Cordialement,\nL'équipe BUCREP — ACREMAC"
    )

    note_html = (
        f'<tr><td style="padding:10px 0 0"><div style="background:#fffbeb;border-left:3px solid '
        f'#f59e0b;border-radius:4px;padding:10px 14px;font-size:13px;color:#92400e;">'
        f'<strong>Note :</strong> {mail.dispatch_note}</div></td></tr>'
    ) if mail.dispatch_note else ""

    excerpt_html = (
        f'<tr><td style="padding:14px 0 0"><p style="margin:0 0 6px;font-size:11px;'
        f'font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#94a3b8;">Aperçu</p>'
        f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px 14px;'
        f'font-size:13px;color:#475569;line-height:1.6;white-space:pre-wrap;">{body_excerpt}</div>'
        f'</td></tr>'
    ) if body_excerpt else ""

    html_body = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
        <tr><td style="background:linear-gradient(135deg,#1a3a5c 0%,#2563eb 100%);border-radius:12px 12px 0 0;padding:28px 32px;">
          <table width="100%" cellpadding="0" cellspacing="0"><tr>
            <td><span style="font-size:22px;font-weight:800;color:#fff;letter-spacing:-.5px;">BUCREP</span>
              <span style="font-size:13px;color:#bfdbfe;margin-left:8px;">ACREMAC</span></td>
            <td align="right"><span style="background:rgba(255,255,255,.15);color:#dbeafe;
              font-size:11px;font-weight:600;padding:4px 10px;border-radius:20px;">Nouvelle demande</span></td>
          </tr></table>
        </td></tr>
        <tr><td style="background:#fff;padding:32px;border-left:1px solid #e2e8f0;border-right:1px solid #e2e8f0;">
          <p style="margin:0 0 20px;font-size:16px;color:#1e293b;">
            Bonjour <strong>{first_name}</strong>,
          </p>
          <p style="margin:0 0 24px;font-size:14px;color:#475569;line-height:1.6;">
            Un dossier client vous a été assigné sur la plateforme <strong>BUCREP</strong>.
            Veuillez en prendre connaissance et y donner suite dans les meilleurs délais.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0"
            style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
            <tr><td style="padding:16px 20px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="padding:4px 0;font-size:12px;color:#94a3b8;width:90px;">Expéditeur</td>
                  <td style="padding:4px 0;font-size:13px;color:#1e293b;font-weight:600;">
                    {mail.from_name or mail.from_email}
                    {('<br><span style="font-weight:400;color:#64748b;font-size:12px;">' + mail.from_email + '</span>') if mail.from_name else ''}
                  </td>
                </tr>
                <tr>
                  <td style="padding:4px 0;font-size:12px;color:#94a3b8;">Objet</td>
                  <td style="padding:4px 0;font-size:13px;color:#1e293b;">{mail.subject or '(Sans objet)'}</td>
                </tr>
                <tr>
                  <td style="padding:4px 0;font-size:12px;color:#94a3b8;">Reçu le</td>
                  <td style="padding:4px 0;font-size:13px;color:#1e293b;">
                    {mail.received_at.strftime('%d/%m/%Y à %H:%M')}
                  </td>
                </tr>
              </table>
            </td></tr>
          </table>
          <table width="100%" cellpadding="0" cellspacing="0">
            {note_html}
            {excerpt_html}
          </table>
          <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:28px;">
            <tr><td align="center">
              <a href="{inbox_url}" target="_blank"
                style="display:inline-block;background:linear-gradient(135deg,#1a3a5c 0%,#2563eb 100%);
                color:#fff;text-decoration:none;font-size:14px;font-weight:700;
                padding:14px 32px;border-radius:8px;letter-spacing:.02em;">
                Ouvrir le dossier →
              </a>
            </td></tr>
          </table>
        </td></tr>
        <tr><td style="background:#f8fafc;border:1px solid #e2e8f0;border-top:none;
          border-radius:0 0 12px 12px;padding:20px 32px;text-align:center;">
          <p style="margin:0;font-size:11px;color:#94a3b8;line-height:1.6;">
            Cet email a été envoyé automatiquement par la plateforme BUCREP — ACREMAC.<br>
            Ne pas répondre directement à cet email.
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    try:
        msg = EmailMultiAlternatives(
            subject=subject_line,
            body=text_body,
            from_email=dj_settings.DEFAULT_FROM_EMAIL,
            to=[assignee.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
    except Exception as exc:
        logger.error("_notify_dispatch: failed to send email to %s — %s", assignee.email, exc)
