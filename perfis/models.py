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
    bio = models.TextField(max_length=500, blank=True, verbose_name="Sobre Mim")
    
    


    def __str__(self):
        return f'Perfil de {self.user.username}'

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)
    instance.perfil.save()