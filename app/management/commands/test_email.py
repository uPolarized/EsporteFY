"""
Management command para simular o envio do e-mail de boas-vindas/confirmacao.

Uso:
    python manage.py test_email lozeborges19@gmail.com
    python manage.py test_email lozeborges19@gmail.com --name "Joao"
"""

from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from types import SimpleNamespace


class Command(BaseCommand):
    help = "Envia o e-mail de confirmacao/boas-vindas de teste para um endereco."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Endereco de e-mail de destino")
        parser.add_argument(
            "--name",
            type=str,
            default="Atleta",
            help="Nome de exibicao no e-mail (padrao: Atleta)",
        )

    def handle(self, *args, **options):
        dest_email = options["email"]
        display_name = options["name"]

        # Objeto usuario simulado com os campos que os templates esperam
        mock_user = SimpleNamespace(
            username=display_name,
            email=dest_email,
            first_name=display_name,
            last_name="",
            pk=0,
        )

        # Contexto identico ao que o allauth injeta nos templates de email
        context = {
            "user": mock_user,
            "activate_url": "http://localhost:8000/accounts/confirm-email/SIMULADO/",
            "key": "TEST-LINK-SIMULADO",
            "expiration_days": getattr(settings, "ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS", 3),
            "current_site": SimpleNamespace(
                name="EsporteFY",
                domain="esportefy.com.br",
            ),
            "request": None,
        }

        subject = "Confirme seu e-mail - EsporteFY [TESTE]"

        # Renderiza o HTML (template standalone, nao usa extends)
        html_body = render_to_string(
            "account/email/email_confirmation_signup_message.html", context
        )

        # Fallback TXT simples (evita depender do extends do allauth no shell)
        txt_body = (
            f"Ola {display_name}, bem-vindo ao EsporteFY!\n\n"
            "Para confirmar seu e-mail, acesse o link abaixo:\n"
            f"{context['activate_url']}\n\n"
            "(Esta e uma mensagem de teste — o link acima e ficticio.)"
        )

        from_email = getattr(
            settings, "DEFAULT_FROM_EMAIL", "contato.esportefy@gmail.com"
        )

        msg = EmailMultiAlternatives(subject, txt_body, from_email, [dest_email])
        msg.attach_alternative(html_body, "text/html")
        msg.send()

        self.stdout.write(
            self.style.SUCCESS(f"E-mail de teste enviado com sucesso para {dest_email}")
        )
