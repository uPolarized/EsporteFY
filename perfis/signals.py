from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.models import Session
from django.utils import timezone
from .models import AccountLoginEvent, Perfil, UserPrivacySettings
from social.models import Atividade
from app.redis_utils import publish_to_redis
import requests
from django.core.files.base import ContentFile
from allauth.socialaccount.signals import social_account_added
from allauth.socialaccount.models import SocialAccount


@receiver(m2m_changed, sender=Perfil.amigos.through)
def criar_atividade_nova_amizade(sender, instance, action, pk_set, **kwargs):

# Certifique-se de que o nome do seu modelo é esse

    """
    Cria apenas uma atividade quando uma nova amizade é formada.
    Evita duplicações e exibe corretamente os dois nomes.
    """
    return


@receiver(user_logged_in)
def registrar_evento_login(sender, request, user, **kwargs):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = forwarded_for.split(',')[0].strip() if forwarded_for else request.META.get('REMOTE_ADDR')
    user_agent = (request.META.get('HTTP_USER_AGENT') or '')[:255]

    login_method = AccountLoginEvent.LOGIN_METHOD_PASSWORD
    if getattr(request.user, 'socialaccount_set', None) and request.user.socialaccount_set.exists():
        # Heurística: para ambiente allauth/social, registra como social se usuário possui conta social vinculada.
        login_method = AccountLoginEvent.LOGIN_METHOD_SOCIAL

    AccountLoginEvent.objects.create(
        user=user,
        ip_address=ip,
        user_agent=user_agent,
        login_method=login_method,
    )


@receiver(user_logged_in)
def garantir_privacidade_ao_logar(sender, request, user, **kwargs):
    UserPrivacySettings.objects.get_or_create(user=user)


@receiver(post_save, sender=User)
def garantir_privacidade_ao_criar_usuario(sender, instance, created, **kwargs):
    if created:
        UserPrivacySettings.objects.get_or_create(user=instance)


@receiver(social_account_added)
def puxar_foto_google(request, sociallogin, **kwargs):
    # Verifica se o login foi feito pelo Google (verifica se "google" está no nome)
    if 'google' in sociallogin.account.provider:
        user = sociallogin.user
        extra_data = sociallogin.account.extra_data
        
        # A URL da foto de perfil fica na chave 'picture' do json do Google
        picture_url = extra_data.get('picture')

        if picture_url:
            try:
                # Busca o perfil do usuário (ou cria se por acaso não existir ainda)
                perfil, created = Perfil.objects.get_or_create(user=user)
                
                # Faz o download da imagem da URL do Google
                response = requests.get(picture_url, timeout=8)

                if response.status_code == 200:
                    # Cria um nome de arquivo único
                    file_name = f"google_avatar_{user.username}.jpg"
                    
                    # Salva a imagem no campo 'foto' (ou o nome do campo que você usa)
                    perfil.foto.save(file_name, ContentFile(response.content), save=True)
            except Exception as e:
                # Se der erro no download, ele falha silenciosamente e mantém a foto padrão
                print(f"Erro ao baixar foto do Google: {e}")

@receiver(user_logged_in)
def verificar_foto_google_login(sender, request, user, **kwargs):
    """
    Para usuários JÁ CADASTRADOS (legado): verifica no login se a foto ainda é a padrão.
    Se for, e o usuário tiver Google vinculado, tenta puxar a foto.
    """
    # Garante que tem perfil
    if not hasattr(user, 'perfil'):
        return

    # Verifica o nome atual da foto no banco
    foto_nome = user.perfil.foto.name if user.perfil.foto else ""

    # Se a foto já foi personalizada (não tem "default" no nome), não faz nada
    if foto_nome and "default" not in foto_nome:
        return

    try:
        # Busca se existe alguma conta social vinculada que contenha "google" no nome (case insensitive)
        contas_sociais = SocialAccount.objects.filter(user=user)
        google_account = next((acc for acc in contas_sociais if 'google' in acc.provider.lower()), None)
        
        if not google_account:
            return

        # Tenta pegar a URL da foto (prioriza 'picture', fallback para 'avatar_url')
        picture_url = google_account.extra_data.get('picture') or google_account.extra_data.get('avatar_url')

        if picture_url:
            response = requests.get(picture_url, timeout=8)
            if response.status_code == 200:
                file_name = f"google_avatar_{user.username}.jpg"
                user.perfil.foto.save(file_name, ContentFile(response.content), save=True)
    except Exception as e:
        print(f"⚠️ Erro ao atualizar foto Google no login: {e}")

@receiver(user_logged_in)
def clear_other_sessions(sender, request, user, **kwargs):
    """
    Prevents multiple concurrent sessions for the same user.
    When a user logs in, any other active sessions for that user will be deleted.
    """
    current_key = request.session.session_key
    
    # Iterate all active sessions
    for db_session in Session.objects.filter(expire_date__gte=timezone.now()):
        if current_key and db_session.session_key == current_key:
            continue
        
        try:
            data = db_session.get_decoded()
        except Exception:
            continue
            
        if str(data.get('_auth_user_id')) == str(user.id):
            # Force immediate logout on old browser tabs/sessions via websocket channel.
            publish_to_redis(
                f"notifications_session_{db_session.session_key}",
                {
                    "type": "force_logout",
                    "mensagem": "Sua conta foi acessada em outro dispositivo.",
                },
            )
            db_session.delete()
