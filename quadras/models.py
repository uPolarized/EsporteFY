from django.db import models

class Quadra(models.Model):
    BAIRRO_CHOICES = [
        ('flamengo', 'Flamengo'),
        ('centro', 'Centro'),
        ('sao_jose', 'São José do Imbassaí'),
        ('itaipuacu', 'Itaipuaçu'),
        ('itaocaia', 'Itaocaia Valley'),
        ('parque_nanci', 'Parque Nanci'),
        ('guaratiba', 'Guaratiba'),
        ('barroco', 'Barroco'),
        ('caxito', 'Caxito'),
        ('mumbuca', 'Mumbuca'),
        ('bananal', 'Bananal'),
        ('inoã', 'Inoã'),
        ('itapeba', 'Itapeba'),
    ]

    nome = models.CharField(max_length=100, verbose_name="Nome da Quadra")
    bairro = models.CharField(max_length=50, choices=BAIRRO_CHOICES, verbose_name="Bairro")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição da Quadra")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Longitude")
    fonte = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fonte dos dados")

    class Meta:
        verbose_name = "Quadra"
        verbose_name_plural = "Quadras"
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.get_bairro_display()})'

    def foto_principal(self):
        return self.fotos.first()


class FotoQuadra(models.Model):
    quadra = models.ForeignKey(Quadra, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='fotos_quadras/', verbose_name="Imagem")

    class Meta:
        verbose_name = "Foto da Quadra"
        verbose_name_plural = "Fotos das Quadras"

    def __str__(self):
        return f"Foto de {self.quadra.nome}"
