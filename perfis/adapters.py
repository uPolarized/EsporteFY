import logging
from threading import Thread

from allauth.account.adapter import DefaultAccountAdapter

logger = logging.getLogger(__name__)


class AsyncAccountAdapter(DefaultAccountAdapter):
    """Envia e-mails do allauth em background para reduzir latencia no signup."""

    def send_mail(self, template_prefix, email, context):
        message = self.render_mail(template_prefix, email, context)
        Thread(target=self._send_message, args=(message,), daemon=True).start()

    @staticmethod
    def _send_message(message):
        try:
            message.send()
        except Exception:
            logger.exception("Falha ao enviar e-mail de confirmacao em background")
