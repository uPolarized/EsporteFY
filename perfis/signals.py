from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Perfil
from social.models import Atividade
from django.core.mail import send_mail
from django.conf import settings
from django.db.models.signals import post_save
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth.models import User

@receiver(m2m_changed, sender=Perfil.amigos.through)
def criar_atividade_nova_amizade(sender, instance, action, pk_set, **kwargs):
    """
    Cria apenas uma atividade quando uma nova amizade é formada.
    Evita duplicações e exibe corretamente os dois nomes.
    """
    if action == "post_add" and hasattr(instance, "user") and instance.user:
        quem_aceitou = instance.user

        for user_pk in pk_set:
            try:
                quem_enviou = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                continue

            # Garante que ambos têm username válido
            nome_aceitou = getattr(quem_aceitou, "username", "Usuário")
            nome_enviou = getattr(quem_enviou, "username", "Usuário")

            # 🔒 Cria apenas se não existir amizade entre esses dois
            if not Atividade.objects.filter(
                verbo__icontains="agora são amigos",
                ator__in=[quem_aceitou, quem_enviou]
            ).exists():
                Atividade.objects.create(
                    ator=quem_aceitou,
                    verbo=f"{nome_aceitou} e {nome_enviou} agora são amigos 🤝"
                )

@receiver(post_save, sender=User)
def enviar_email_boas_vindas(sender, instance, created, **kwargs):
    if created:
        contexto = {
            'username': instance.username,
            'year': timezone.now().year,
        }

        assunto = "🎉 Bem-vindo ao EsporteFY!"
        texto = render_to_string('emails/boas_vindas.txt', contexto)
        html = render_to_string('emails/boas_vindas.html', contexto)

        email = EmailMultiAlternatives(
            subject=assunto,
            body=texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[instance.email]
        )
        email.attach_alternative(html, "text/html")
        email.send(fail_silently=True)