from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Perfil(models.Model):
    # Opções para os esportes
    ESPORTES_CHOICES = [
        ('Futebol', 'Futebol'),
        ('Tenis', 'Tênis'),
        ('Volei', 'Vôlei'),
        ('Basquete', 'Basquete'),
        ('Queimada', 'Queimada'),
    ]

    # Relação um-para-um com o usuário padrão do Django
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Nossos novos campos de perfil
    esportes_preferidos = models.CharField(max_length=100, choices=ESPORTES_CHOICES, blank=True, null=True, verbose_name="Esporte Preferido")
    
    def __str__(self):
        return f'Perfil de {self.user.username}'

# Esta função cria um Perfil automaticamente toda vez que um novo User é criado
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.perfil.save()
