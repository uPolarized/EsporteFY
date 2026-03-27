from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from .models import Perfil
from social.models import Atividade
import requests
from django.core.files.base import ContentFile
from allauth.socialaccount.signals import social_account_added
from allauth.socialaccount.models import SocialAccount

# Certifique-se de que o nome do seu modelo é esse

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