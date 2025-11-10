from django.db import models
from django.contrib.auth.models import User
from quadras.models import Quadra


# ---------------------------------------------------------
# 🔹 MODELO DE ESPORTES (usado dinamicamente nas partidas)
# ---------------------------------------------------------
class Esporte(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Esporte"
        verbose_name_plural = "Esportes"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


# ---------------------------------------------------------
# 🔹 MODELO PRINCIPAL: PARTIDA
# ---------------------------------------------------------
class Partida(models.Model):
    organizador = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='partidas_organizadas'
    )
    titulo = models.CharField(max_length=100, verbose_name="Título da Partida")
    esporte = models.ForeignKey(
        Esporte, on_delete=models.CASCADE, verbose_name="Esporte"
    )
    quadra = models.ForeignKey(
        Quadra,
        on_delete=models.SET_NULL,
        null=True,
        related_name='partidas',
        verbose_name="Quadra"
    )
    data_hora = models.DateTimeField(verbose_name="Data e Hora")
    jogadores_necessarios = models.PositiveIntegerField(verbose_name="Jogadores Necessários")
    jogadores_confirmados = models.ManyToManyField(
        User, related_name='partidas_confirmadas', blank=True
    )

    class Meta:
        ordering = ['data_hora']
        verbose_name = "Partida"
        verbose_name_plural = "Partidas"

    def __str__(self):
        return self.titulo

    @property
    def vagas_preenchidas(self):
        """Retorna o número de jogadores confirmados."""
        return self.jogadores_confirmados.count()

    @property
    def vagas_restantes(self):
        """Calcula quantas vagas ainda estão disponíveis."""
        return self.jogadores_necessarios - self.vagas_preenchidas


# ---------------------------------------------------------
# 🔹 AVALIAÇÃO DE QUADRA
# ---------------------------------------------------------
class AvaliacaoQuadra(models.Model):
    partida = models.ForeignKey(
        Partida, on_delete=models.CASCADE, related_name='avaliacoes_quadra'
    )
    avaliador = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='avaliacoes_quadra_feitas'
    )
    nota_quadra = models.PositiveIntegerField(verbose_name="Nota para a Quadra (1 a 5)")
    comentario = models.TextField(blank=True, null=True, verbose_name="Comentário")
    data_avaliacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avaliação da Quadra"
        verbose_name_plural = "Avaliações das Quadras"
        unique_together = ('partida', 'avaliador')

    def __str__(self):
        return f"Avaliação de {self.partida} por {self.avaliador}"


# ---------------------------------------------------------
# 🔹 AVALIAÇÃO DE JOGADOR
# ---------------------------------------------------------
class AvaliacaoJogador(models.Model):
    partida = models.ForeignKey(
        Partida, on_delete=models.CASCADE, related_name='avaliacoes_jogador'
    )
    avaliador = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='avaliacoes_jogador_feitas'
    )
    avaliado = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='avaliacoes_jogador_recebidas'
    )
    nota_fair_play = models.PositiveIntegerField(verbose_name="Nota de Fair Play (1 a 5)")
    data_avaliacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avaliação de Jogador"
        verbose_name_plural = "Avaliações de Jogadores"
        unique_together = ('partida', 'avaliador', 'avaliado')

    def __str__(self):
        return f"{self.avaliado} avaliado por {self.avaliador}"
