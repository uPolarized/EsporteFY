from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib import messages

@receiver(user_logged_in)
def post_login(sender, user, request, **kwargs):
    """
    Este sinal é disparado toda vez que um usuário faz login.
    """
    # Verifica se o login foi recente (para evitar mostrar a mensagem
    # em sessões antigas "lembradas"). a.is_new é True no primeiro login.
    if user.is_authenticated and kwargs.get('is_new', False):
        messages.info(
            request, 
            f'Bem-vindo ao EsporteFY, {user.username}! Confira as partidas abertas e as últimas notícias.',
            extra_tags='welcome-toast' # Uma "tag" especial para o nosso toast
        )