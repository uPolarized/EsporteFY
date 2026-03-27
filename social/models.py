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
    
    def get_objeto(self):
        """Retorna o objeto alvo (ex: Partida) da atividade."""
        return self.alvo

    def get_descricao_formatada(self):
        """Retorna a descrição completa e formatada da atividade."""
        obj = self.get_objeto()
        titulo_obj = ''
        
        if obj is not None:
            titulo_obj = getattr(obj, 'titulo', '') or ''
        else:
            # Tentativa adicional: se o objeto já não estiver disponível
            if self.content_type and self.content_type.model == 'partida':
                from partidas.models import Partida
                try:
                    partida_link = Partida.objects.filter(id=self.object_id).first()
                    if partida_link:
                        titulo_obj = partida_link.titulo
                except Exception:
                    pass

        verbo_text = (self.verbo or '').strip()
        verbo_low = verbo_text.lower()

        if titulo_obj:
            if 'criou' in verbo_low:
                return f'Criou a partida {titulo_obj}'
            elif 'entrou' in verbo_low:
                return f'Entrou na partida {titulo_obj}'
            elif 'saiu' in verbo_low:
                return f'Saiu da partida {titulo_obj}'
            else:
                return f'{verbo_text} {titulo_obj}'.strip()
        else:
            # Fallback sem título
            if 'criou' in verbo_low:
                return 'Criou a partida'
            elif 'entrou' in verbo_low:
                return 'Entrou na partida'
            elif 'saiu' in verbo_low:
                return 'Saiu da partida'
            else:
                return verbo_text or 'Atividade registrada'



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


class LikeAtividade(models.Model):
    """Modelo para rastrear curtidas em atividades do feed."""
    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE, related_name='likes')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_atividades')
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('atividade', 'usuario')
        verbose_name = "Like de Atividade"
        verbose_name_plural = "Likes de Atividades"
        ordering = ['-data_criacao']

    def __str__(self):
        return f'{self.usuario.username} curtiu atividade #{self.atividade.id}'