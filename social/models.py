from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone  # Importante para o default do campo novo

class Atividade(models.Model):
    ator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='atividades')
    verbo = models.CharField(max_length=255)

    alvo = GenericForeignKey('content_type', 'object_id')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    utilizador_relacionado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='atividades_relacionadas'
    )

    class Meta:
        ordering = ['-timestamp']

    @property
    def title(self):
        return self.verbo



class Conversa(models.Model):
    participantes = models.ManyToManyField(User, related_name='conversas')
    criado_em = models.DateTimeField(auto_now_add=True)
    
    # 🔥 NOVO CAMPO OBRIGATÓRIO PARA A VIEW FUNCIONAR 🔥
    # Usado para ordenar a sidebar (quem mandou msg por último fica em cima)
    ultima_mensagem_data = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-ultima_mensagem_data'] # Padrão: mais recentes primeiro

    def __str__(self):
        nomes = ", ".join([u.username for u in self.participantes.all()])
        return f"Conversa entre: {nomes}"


class Mensagem(models.Model):
    conversa = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name='mensagens')
    remetente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensagens_enviadas')
    
    conteudo = models.TextField(blank=True, null=True)
    imagem = models.ImageField(upload_to='chat_images/', blank=True, null=True)  # Campo de imagem
    
    timestamp = models.DateTimeField(auto_now_add=True)

    # Funcionalidade futura: "Apagar para mim"
    visivel_para_remetente = models.BooleanField(default=True)
    visivel_para_destinatario = models.BooleanField(default=True)

    class Meta:
        ordering = ['timestamp'] # Garante a ordem cronológica no chat

    def __str__(self):
        return f'{self.remetente} ({self.timestamp.strftime("%H:%M")})'