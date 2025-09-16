from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Partida(models.Model):
    BAIRRO_CHOICES = [
        ('flamengo', 'Flamengo'),
        ('centro', 'Centro'),
        ('sao_jose', 'São José do Imbassaí'),
        ('itaipuacu', 'Itaipuaçu'),
        ('itaocaia', 'Itaocaia Valley'),
        ('parque_nanci', 'Parque Nanci'),
    ]

    organizador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='partidas_organizadas')
    titulo = models.CharField(max_length=100, verbose_name="Título da Partida")
    esporte = models.CharField(max_length=50, verbose_name="Esporte")
    bairro = models.CharField(max_length=50, choices=BAIRRO_CHOICES, verbose_name="Bairro")
    local = models.CharField(max_length=200, verbose_name="Local (Nome da quadra, rua, etc.)")
    data_hora = models.DateTimeField(verbose_name="Data e Hora")
    jogadores_necessarios = models.PositiveIntegerField(verbose_name="Jogadores Necessários")
    jogadores_confirmados = models.ManyToManyField(User, related_name='partidas_confirmadas', blank=True)
    
    class Meta:
        ordering = ['data_hora']
        verbose_name = "Partida"
        verbose_name_plural = "Partidas"

    def __str__(self):
        return f'{self.titulo} em {self.get_bairro_display()}'
    
     
    @property
    def vagas_preenchidas(self):
        # Retorna o número de jogadores confirmados + o organizador
        return self.jogadores_confirmados.count()

    @property
    def vagas_restantes(self):
        # Calcula as vagas que ainda faltam
        return self.jogadores_necessarios - self.vagas_preenchidas
    # ---------------------------



# Renomeie o modelo Avaliacao para AvaliacaoQuadra
class AvaliacaoQuadra(models.Model):
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name='avaliacoes_quadra')
    avaliador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avaliacoes_quadra_feitas')
    nota_quadra = models.PositiveIntegerField(verbose_name="Nota para a Quadra (1 a 5)")
    comentario = models.TextField(blank=True, null=True, verbose_name="Comentário")
    data_avaliacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avaliação da Quadra"
        verbose_name_plural = "Avaliações das Quadras"
        unique_together = ('partida', 'avaliador')

# --- NOVO MODELO PARA AVALIAR JOGADORES ---
class AvaliacaoJogador(models.Model):
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name='avaliacoes_jogador')
    avaliador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avaliacoes_jogador_feitas')
    avaliado = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avaliacoes_jogador_recebidas')
    nota_fair_play = models.PositiveIntegerField(verbose_name="Nota de Fair Play (1 a 5)")
    data_avaliacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avaliação de Jogador"
        verbose_name_plural = "Avaliações de Jogadores"
        # Garante que um usuário só pode avaliar outro jogador uma vez por partida
        unique_together = ('partida', 'avaliador', 'avaliado')