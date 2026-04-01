from django.conf import settings
from django.db import models


class Feedback(models.Model):
	CATEGORIA_CHOICES = [
		("bug", "🐛 Bug/Erro"),
		("feature", "✨ Feature Request"),
		("sugestao", "💡 Sugestão Geral"),
		("outro", "❓ Outro"),
	]

	usuario = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="feedbacks",
		null=True,
		blank=True,
		help_text="Usuário que enviou o feedback. Null se anônimo.",
	)
	categoria = models.CharField(
		max_length=20,
		choices=CATEGORIA_CHOICES,
		default="sugestao",
		help_text="Tipo de feedback",
	)
	assunto = models.CharField(max_length=200, help_text="Título do feedback")
	mensagem = models.TextField(help_text="Descrição detalhada do feedback")
	email_contato = models.EmailField(
		blank=True,
		help_text="Email para contato (copiado de user.email se logado)",
	)
	data_criacao = models.DateTimeField(auto_now_add=True)
	lido = models.BooleanField(default=False, help_text="Se o admin já viu")
	respondido = models.BooleanField(default=False, help_text="Se foi respondido")
	resposta = models.TextField(blank=True, help_text="Resposta do admin")

	class Meta:
		verbose_name = "Feedback"
		verbose_name_plural = "Feedbacks"
		ordering = ("-data_criacao",)

	def __str__(self):
		return f"{self.get_categoria_display()} - {self.assunto}"


class DocumentoLGPD(models.Model):
	TIPO_CHOICES = [
		("privacy_policy", "Politica de Privacidade"),
		("terms_of_service", "Termos de Servico"),
	]

	tipo_documento = models.CharField(max_length=20, choices=TIPO_CHOICES, db_column="tipo")
	titulo = models.CharField(max_length=200)
	versao = models.CharField(max_length=40, blank=True, default="")
	conteudo = models.TextField()
	ativo = models.BooleanField(default=True)
	data_vigencia = models.DateField(null=True, blank=True)
	criado_em = models.DateTimeField(auto_now_add=True)
	atualizado_em = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = "Documento LGPD"
		verbose_name_plural = "Documentos LGPD"
		ordering = ("tipo_documento", "-data_vigencia", "-atualizado_em")

	def __str__(self):
		return f"{self.get_tipo_documento_display()} - v{self.versao or 's/versao'}"


class DataAccessRequest(models.Model):
	STATUS_PENDING = "pending"
	STATUS_PROCESSING = "processing"
	STATUS_COMPLETED = "completed"
	STATUS_DENIED = "denied"

	STATUS_CHOICES = [
		(STATUS_PENDING, "Pendente"),
		(STATUS_PROCESSING, "Em processamento"),
		(STATUS_COMPLETED, "Concluida"),
		(STATUS_DENIED, "Negada"),
	]

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="data_access_requests",
		db_column="usuario_id",
	)
	motivo = models.TextField(blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	data_solicitacao = models.DateTimeField(auto_now_add=True)
	data_processamento = models.DateTimeField(null=True, blank=True)
	arquivo_exportacao = models.FileField(upload_to="data_exports/", null=True, blank=True)
	observacoes_admin = models.TextField(blank=True, default="")

	class Meta:
		verbose_name = "Solicitacao de acesso a dados"
		verbose_name_plural = "Solicitacoes de acesso a dados"
		ordering = ("-data_solicitacao",)

	def __str__(self):
		return f"{self.user.username} - {self.get_status_display()}"


class UserConsentLog(models.Model):
	TYPE_TERMS = "terms_of_service"
	TYPE_PRIVACY = "privacy_policy"
	TYPE_COOKIES = "cookies"

	CONSENT_TYPE_CHOICES = [
		(TYPE_TERMS, "Termos de Servico"),
		(TYPE_PRIVACY, "Politica de Privacidade"),
		(TYPE_COOKIES, "Cookies Opcionais"),
	]

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="consent_logs",
		db_column="usuario_id",
	)
	consent_type = models.CharField(max_length=40, choices=CONSENT_TYPE_CHOICES)
	accepted = models.BooleanField(default=False)
	document_version = models.CharField(max_length=40, blank=True, default="")
	source = models.CharField(max_length=20, blank=True, default="web")
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	user_agent = models.TextField(blank=True, default="")
	timestamp = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = "Log de consentimento"
		verbose_name_plural = "Logs de consentimento"
		ordering = ("-timestamp",)
		indexes = [
			models.Index(fields=["user", "consent_type", "-timestamp"], name="app_usercon_user_id_6e698f_idx"),
		]

	def __str__(self):
		status = "aceito" if self.accepted else "recusado"
		return f"{self.user.username} - {self.consent_type} ({status})"


class DataDeletionRequest(models.Model):
	STATUS_PENDING = "pending"
	STATUS_CANCELED = "canceled"
	STATUS_COMPLETED = "completed"
	STATUS_EXPIRED = "expired"

	STATUS_CHOICES = [
		(STATUS_PENDING, "Pendente"),
		(STATUS_CANCELED, "Cancelada"),
		(STATUS_COMPLETED, "Concluida"),
		(STATUS_EXPIRED, "Expirada"),
	]

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="data_deletion_requests",
		db_column="usuario_id",
	)
	motivo = models.TextField(blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	confirm_token = models.CharField(max_length=80, unique=True)
	data_solicitacao = models.DateTimeField(auto_now_add=True)
	data_expiracao = models.DateTimeField()
	data_confirmacao = models.DateTimeField(null=True, blank=True)
	data_cancelamento = models.DateTimeField(null=True, blank=True)
	data_processamento = models.DateTimeField(null=True, blank=True)

	class Meta:
		verbose_name = "Solicitacao de exclusao de conta"
		verbose_name_plural = "Solicitacoes de exclusao de conta"
		ordering = ("-data_solicitacao",)

	def __str__(self):
		return f"{self.user.username} - {self.get_status_display()}"


