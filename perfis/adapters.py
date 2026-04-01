import logging
from threading import Thread

from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

from .consent import has_required_consents

logger = logging.getLogger(__name__)

class AsyncAccountAdapter(DefaultAccountAdapter):
    """Envia e-mails do allauth em background para reduzir latencia no signup."""

    def send_mail(self, template_prefix, email, context):
        message = self.render_mail(template_prefix, email, context)
        Thread(target=self._send_message, args=(message,), daemon=True).start()

    def get_login_redirect_url(self, request):
        if request.session.pop("force_lgpd_redirect", False):
            return f"{reverse('lgpd_hub')}?tab=meus-dados"

        user = getattr(request, "user", None)
        if user and user.is_authenticated and not has_required_consents(user):
            return f"{reverse('lgpd_hub')}?tab=meus-dados"

        return super().get_login_redirect_url(request)

    @staticmethod
    def _send_message(message):
        try:
            message.send()
        except Exception:
            logger.exception("Falha ao enviar e-mail de confirmacao em background")
