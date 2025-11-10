from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

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
    
class Conversa(models.Model):
    participantes = models.ManyToManyField(User, related_name='conversas')
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversa #{self.id}"



class Mensagem(models.Model):
    conversa = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name='mensagens')
    remetente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensagens_enviadas')
    conteudo = models.TextField(blank=True, null=True)
    imagem = models.ImageField(upload_to='chat_images/', blank=True, null=True)  # 🖼️ campo novo
    timestamp = models.DateTimeField(auto_now_add=True)

    visivel_para_remetente = models.BooleanField(default=True)
    visivel_para_destinatario = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.remetente} - {self.conversa.id}'
    
    