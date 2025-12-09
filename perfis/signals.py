from django.db import models
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Perfil
from social.models import Atividade
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone


@receiver(m2m_changed, sender=Perfil.amigos.through)
def criar_atividade_nova_amizade(sender, instance, action, pk_set, **kwargs):
    """
    Cria apenas uma atividade quando uma nova amizade é formada.
    Evita duplicações e exibe corretamente os dois nomes.
    """
    if action != "post_add":
        return

    if not hasattr(instance, "user") or not instance.user:
        return

    quem_aceitou = instance.user

    for user_pk in pk_set:
        try:
            quem_enviou = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            continue

        nome_aceitou = getattr(quem_aceitou, "username", None) or getattr(quem_aceitou, "first_name", None) or "Usuário"
        nome_enviou = getattr(quem_enviou, "username", None) or getattr(quem_enviou, "first_name", None) or "Usuário"

        # ⚠️ NÃO usa .filter() com GenericForeignKey. Verifica via Python:
        existe = any(
            (a.ator == quem_aceitou and a.alvo == quem_enviou) or
            (a.ator == quem_enviou and a.alvo == quem_aceitou)
            for a in Atividade.objects.filter(verbo__icontains="agora são amigos")
        )

        if not existe:
            Atividade.objects.create(
                ator=quem_aceitou,
                alvo=quem_enviou,
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