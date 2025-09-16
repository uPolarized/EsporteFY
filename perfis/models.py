from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    esportes_preferidos = models.CharField(max_length=100, choices=ESPORTES_CHOICES, blank=True, null=True, verbose_name="Esporte Preferido")
    nivel_habilidade = models.CharField(max_length=50, choices=NIVEL_HABILIDADE_CHOICES, blank=True, null=True, verbose_name="Nível de Habilidade")
    idade = models.PositiveIntegerField(blank=True, null=True, verbose_name="Idade")
    foto = models.ImageField(upload_to='fotos_perfil/', null=True, blank=True, default='fotos_perfil/default.jpg', verbose_name="Foto de Perfil")
    
    # --- CAMPOS CORRIGIDOS ---
    mini_bio = models.TextField(max_length=500, blank=True, verbose_name="Sobre Mim")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    
    # ... o restante do seu modelo Perfil continua igual
    amigos = models.ManyToManyField(User, related_name='amigos', blank=True)
    
    def __str__(self):
        return f'Perfil de {self.user.username}'

# ... (o resto do seu código, incluindo a função 'receiver' e a classe 'SolicitacaoAmizade')

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)
    instance.perfil.save()


    # --- NOVO MODELO DE SOLICITAÇÃO DE AMIZADE ---
class SolicitacaoAmizade(models.Model):
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitacoes_enviadas')
    receptor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitacoes_recebidas')
    timestamp = models.DateTimeField(auto_now_add=True)
    aceito = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Solicitação de Amizade"
        verbose_name_plural = "Solicitações de Amizade"
        # Garante que um usuário não possa enviar mais de um pedido para a mesma pessoa
        unique_together = ('solicitante', 'receptor')

    def __str__(self):
        return f'De {self.solicitante.username} para {self.receptor.username}'