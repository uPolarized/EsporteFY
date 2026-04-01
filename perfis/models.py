from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from quadras.models import Quadra


class Perfil(models.Model):
    ESPORTES_CHOICES = [
        ('Futebol', 'Futebol'), ('Tenis', 'Tênis'), ('Volei', 'Vôlei'),
        ('Basquete', 'Basquete'), ('Outro', 'Outro'),
    ]
    NIVEL_HABILIDADE_CHOICES = [
        ('Iniciante', 'Iniciante'), ('Intermediario', 'Intermediário'),
        ('Avancado', 'Avançado'), ('Competitivo', 'Competitivo'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    esportes_preferidos = models.CharField(
        max_length=100, choices=ESPORTES_CHOICES, blank=True, null=True,
        verbose_name="Esporte Preferido"
    )
    nivel_habilidade = models.CharField(
        max_length=50, choices=NIVEL_HABILIDADE_CHOICES, blank=True, null=True,
        verbose_name="Nível de Habilidade"
    )
    bairro_base = models.CharField(
        max_length=50, choices=Quadra.BAIRRO_CHOICES, blank=True, null=True,
        verbose_name="Seu Bairro Principal"
    )
    idade = models.PositiveIntegerField(blank=True, null=True, verbose_name="Idade")
    foto = models.ImageField(
        upload_to='fotos_perfil/',
        null=True,
        blank=True,
        default='fotos_perfil/default.jpg',
        verbose_name="Foto de Perfil"
    )

    # ── BANNER ──────────────────────────────────────────────
    banner = models.ImageField(
        upload_to='banners_perfil/',
        null=True,
        blank=True,
        verbose_name="Banner do Perfil"
    )
    banner_position = models.CharField(
        max_length=20,
        default='50% 50%',
        blank=True,
        verbose_name="Posição do Banner"
    )
    # ────────────────────────────────────────────────────────

    mini_bio = models.TextField(max_length=500, blank=True, verbose_name="Sobre Mim")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    amigos = models.ManyToManyField(User, related_name='amigos', blank=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)
    instance.perfil.save()


class SolicitacaoAmizade(models.Model):
    solicitante = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='solicitacoes_enviadas'
    )
    receptor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='solicitacoes_recebidas'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    aceito = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Solicitação de Amizade"
        verbose_name_plural = "Solicitações de Amizade"
        unique_together = ('solicitante', 'receptor')

    def __str__(self):
        return f'De {self.solicitante.username} para {self.receptor.username}'


class UserPrivacySettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='privacy_settings')
    show_profile_public = models.BooleanField(default=True)
    show_online_status = models.BooleanField(default=True)
    allow_friend_requests = models.BooleanField(default=True)
    two_factor_email_enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração de Privacidade'
        verbose_name_plural = 'Configurações de Privacidade'

    def __str__(self):
        return f'Privacidade de {self.user.username}'


class AccountLoginEvent(models.Model):
    LOGIN_METHOD_PASSWORD = 'password'
    LOGIN_METHOD_SOCIAL = 'social'
    LOGIN_METHOD_UNKNOWN = 'unknown'

    LOGIN_METHOD_CHOICES = (
        (LOGIN_METHOD_PASSWORD, 'Senha'),
        (LOGIN_METHOD_SOCIAL, 'Social'),
        (LOGIN_METHOD_UNKNOWN, 'Desconhecido'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_events')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, default='')
    login_method = models.CharField(max_length=16, choices=LOGIN_METHOD_CHOICES, default=LOGIN_METHOD_UNKNOWN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Evento de Login'
        verbose_name_plural = 'Eventos de Login'

    def __str__(self):
        return f'Login {self.user.username} em {self.created_at:%d/%m/%Y %H:%M}'