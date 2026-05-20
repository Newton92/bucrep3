"""
Commande de polling IMAP pour les mails entrants clients.

Usage:
  python manage.py poll_mail
  python manage.py poll_mail --verbose
  python manage.py poll_mail --days 30
"""

import email
import email.header
import email.utils
import hashlib
import imaplib
import socket
from datetime import datetime, timezone as dt_tz, timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from main.models import MailInboxConfig, MailSource, IncomingMail, MailAttachment, User


class Command(BaseCommand):
    help = "Poll les boîtes IMAP configurées et intercepte les mails clients."

    SPAM_FOLDERS = [
        "Spam", "Junk", "SPAM", "JUNK", "Junk Email", "Junk Mail",
        "[Gmail]/Spam", "INBOX.Spam", "INBOX.Junk", "Bulk Mail",
    ]

    def add_arguments(self, parser):
        parser.add_argument("--verbose", action="store_true", help="Détail de chaque email traité")
        parser.add_argument("--days", type=int, default=None, help="Fenêtre de recherche en jours")
        parser.add_argument("--config-id", dest="config_id", type=int, default=None,
                            help="ID d'une configuration IMAP spécifique à utiliser")

    def handle(self, *args, **options):
        self.verbose = options.get("verbose", False)
        self.force_days = options.get("days")
        config_id = options.get("config_id")

        if config_id is not None:
            try:
                configs = [MailInboxConfig.objects.get(id=config_id)]
            except MailInboxConfig.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Configuration IMAP id={config_id} introuvable."))
                return
        else:
            configs = list(MailInboxConfig.objects.filter(is_active=True).exclude(imap_host="").order_by("id"))

        if not configs:
            self.stdout.write("Aucune configuration IMAP active.")
            return

        for cfg in configs:
            if not cfg.is_active or not cfg.imap_host:
                self.stdout.write(f"  [{cfg.id}] Ignoré (inactif ou hôte vide).")
                continue
            self.stdout.write(f"→ Polling [{cfg.id}] {cfg.imap_user}@{cfg.imap_host}…")
            try:
                new_count = self._poll(cfg)
                self.stdout.write(self.style.SUCCESS(f"  ✓ {new_count} nouveau(x) mail(s) intercepté(s)."))
            except Exception as exc:
                cfg.last_error = str(exc)
                cfg.last_polled_at = timezone.now()
                cfg.save(update_fields=["last_error", "last_polled_at"])
                self.stderr.write(self.style.ERROR(f"  ✗ Erreur : {exc}"))

    def _poll(self, cfg: MailInboxConfig) -> int:
        socket.setdefaulttimeout(30)
        if cfg.use_ssl:
            imap = imaplib.IMAP4_SSL(cfg.imap_host, cfg.imap_port)
        else:
            imap = imaplib.IMAP4(cfg.imap_host, cfg.imap_port)

        imap.login(cfg.imap_user, cfg.imap_password)

        if self.force_days:
            since_dt = timezone.now() - timedelta(days=self.force_days)
        elif cfg.last_polled_at:
            since_dt = cfg.last_polled_at - timedelta(days=1)
        else:
            since_dt = timezone.now() - timedelta(days=30)
        since_str = since_dt.strftime("%d-%b-%Y")

        sources = list(MailSource.objects.filter(is_active=True))
        if self.verbose:
            self.stdout.write(f"  Sources actives ({len(sources)}) : " +
                              (", ".join(s.email_or_domain for s in sources) or "(aucune)"))

        _, folder_list = imap.list()
        available_folders = []
        for f in folder_list:
            if isinstance(f, bytes):
                parts = f.decode().split('"')
                folder_name = parts[-1].strip().strip('"').strip()
                if folder_name:
                    available_folders.append(folder_name)

        folders_to_scan = [cfg.mailbox]
        for spam_folder in self.SPAM_FOLDERS:
            if spam_folder in available_folders and spam_folder != cfg.mailbox:
                folders_to_scan.append(spam_folder)

        new_count = 0
        for folder in folders_to_scan:
            try:
                status, _ = imap.select(folder)
                if status != "OK":
                    continue
                _, data = imap.search(None, f'SINCE "{since_str}"')
                uid_list = [u for u in data[0].split() if u]
                if uid_list:
                    self.stdout.write(f"  [{folder}] {len(uid_list)} message(s) depuis le {since_str}.")
                elif self.verbose:
                    self.stdout.write(f"  [{folder}] 0 message.")

                for uid in uid_list:
                    try:
                        created, reason = self._process_uid(imap, uid, sources)
                        if created:
                            new_count += 1
                        elif self.verbose:
                            self.stdout.write(f"    UID {uid.decode()} ignoré — {reason}")
                    except Exception as exc:
                        self.stderr.write(f"    UID {uid} — erreur : {exc}")
            except Exception as exc:
                if self.verbose:
                    self.stdout.write(f"  [{folder}] inaccessible — {exc}")

        imap.logout()
        cfg.last_polled_at = timezone.now()
        cfg.last_error = ""
        cfg.save(update_fields=["last_polled_at", "last_error"])
        return new_count

    def _process_uid(self, imap, uid, sources):
        _, msg_data = imap.fetch(uid, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        message_id = (msg.get("Message-ID") or "").strip()
        if not message_id:
            message_id = "no-id-" + hashlib.md5(raw[:512]).hexdigest()

        if IncomingMail.objects.filter(message_id=message_id).exists():
            return False, "doublon (message_id déjà enregistré)"

        from_header = msg.get("From", "")
        from_name_raw, from_email_raw = email.utils.parseaddr(from_header)
        from_name = self._decode_header(from_name_raw)
        from_email = from_email_raw.lower().strip()
        if not from_email:
            return False, "aucun expéditeur détectable"

        matched_source = self._match_source(from_email, sources)
        if not matched_source:
            return False, f"expéditeur '{from_email}' ne correspond à aucune source active"

        subject = self._decode_header(msg.get("Subject", ""))

        date_str = msg.get("Date", "")
        try:
            received_at = email.utils.parsedate_to_datetime(date_str)
            if received_at.tzinfo is None:
                received_at = received_at.replace(tzinfo=dt_tz.utc)
        except Exception:
            received_at = timezone.now()

        body_text, body_html = self._extract_body(msg)

        incoming = IncomingMail.objects.create(
            mail_source=matched_source,
            message_id=message_id,
            from_email=from_email,
            from_name=from_name,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            received_at=received_at,
        )

        self._save_attachments(msg, incoming)

        if self.verbose:
            self.stdout.write(self.style.SUCCESS(
                f"    ✓ Intercepté : {from_email} — « {subject[:60]} »"
            ))

        self._notify_root_users(incoming)
        return True, "ok"

    def _match_source(self, from_email: str, sources):
        domain = from_email.split("@")[-1] if "@" in from_email else ""
        for source in sources:
            pattern = source.email_or_domain.lower()
            if "@" in pattern:
                if from_email == pattern:
                    return source
            else:
                if domain == pattern:
                    return source
        return None

    def _decode_header(self, value: str) -> str:
        if not value:
            return ""
        parts = email.header.decode_header(value)
        decoded = []
        for part, charset in parts:
            if isinstance(part, bytes):
                decoded.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                decoded.append(part)
        return " ".join(decoded).strip()

    def _extract_body(self, msg):
        body_text = ""
        body_html = ""
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                cd = str(part.get("Content-Disposition", ""))
                if "attachment" in cd:
                    continue
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                if ct == "text/plain" and not body_text:
                    body_text = payload.decode(charset, errors="replace")
                elif ct == "text/html" and not body_html:
                    body_html = payload.decode(charset, errors="replace")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                if msg.get_content_type() == "text/html":
                    body_html = payload.decode(charset, errors="replace")
                else:
                    body_text = payload.decode(charset, errors="replace")
        return body_text, body_html

    def _save_attachments(self, msg, incoming: IncomingMail):
        if not msg.is_multipart():
            return
        for part in msg.walk():
            cd = str(part.get("Content-Disposition", ""))
            if "attachment" not in cd and "inline" not in cd:
                continue
            filename = part.get_filename()
            if not filename:
                continue
            filename = self._decode_header(filename)
            data = part.get_payload(decode=True)
            if not data:
                continue
            ct = part.get_content_type() or "application/octet-stream"
            attachment = MailAttachment(
                mail=incoming,
                filename=filename,
                content_type=ct,
                size=len(data),
            )
            safe_name = filename.replace("/", "_").replace("\\", "_")
            path = f"mail_attachments/{incoming.id}/{safe_name}"
            attachment.file.save(path, ContentFile(data), save=True)

    def _notify_root_users(self, incoming: IncomingMail):
        root_users = User.objects.filter(role="Root", is_active=True).exclude(email="")
        for user in root_users:
            try:
                send_mail(
                    subject=f"[BUCREP] Nouveau mail client — {incoming.subject[:80]}",
                    message=(
                        f"Bonjour {user.first_name or user.username},\n\n"
                        f"Un nouveau mail client a été reçu.\n\n"
                        f"De : {incoming.from_name or incoming.from_email} <{incoming.from_email}>\n"
                        f"Objet : {incoming.subject}\n"
                        f"Client : {incoming.mail_source.client_name if incoming.mail_source else '—'}\n\n"
                        f"Connectez-vous à l'application BUCREP pour le consulter et le dispatcher."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception:
                pass
