from django.db import models


class Quadra(models.Model):
    BAIRRO_CHOICES = [
        ('flamengo', 'Flamengo'),
        ('centro', 'Centro'),
        ('sao_jose', 'São José do Imbassaí'),
        ('itaipuacu', 'Itaipuaçu'),
        ('itaocaia', 'Itaocaia Valley'),
        ('parque_nanci', 'Parque Nanci'),
    ]

    nome = models.CharField(max_length=100, verbose_name="Nome da Quadra")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    foto = models.ImageField(upload_to='fotos_quadras/', blank=True, null=True, verbose_name="Foto da Quadra")
    bairro = models.CharField(max_length=50, choices=BAIRRO_CHOICES, verbose_name="Bairro")

    class Meta:
        verbose_name = "Quadra"
        verbose_name_plural = "Quadras"

    def __str__(self):
        return self.nome