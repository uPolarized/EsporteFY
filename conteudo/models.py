from django.db import models
from django.contrib.auth.models import User

class Noticia(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título")
    subtitulo = models.CharField(max_length=300, blank=True, null=True, verbose_name="Subtítulo")
    conteudo = models.TextField(verbose_name="Conteúdo")
    imagem = models.ImageField(upload_to='noticias/', blank=True, null=True, verbose_name="Imagem de Destaque")
    link_externo = models.URLField(blank=True, null=True, verbose_name="Link da Fonte Externa")
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Autor")
    data_publicacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Publicação")

    class Meta:
        verbose_name = "Notícia"
        verbose_name_plural = "Notícias"
        ordering = ['-data_publicacao']

    def __str__(self):
        return self.titulo