import ssl
from django.core.mail.backends.smtp import EmailBackend


class SkipCertVerifyEmailBackend(EmailBackend):
    """Backend SMTP qui accepte les certificats auto-signés (relais interne)."""

    def open(self):
        if self.connection:
            return False

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            import smtplib
            self.connection = smtplib.SMTP(
                self.host,
                self.port,
                local_hostname=None,
                timeout=self.timeout,
            )
            if self.use_tls:
                self.connection.starttls(context=ctx)
            elif self.use_ssl:
                import socket
                self.connection = smtplib.SMTP_SSL(
                    self.host,
                    self.port,
                    timeout=self.timeout,
                    context=ctx,
                )
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception:
            if not self.fail_silently:
                raise
