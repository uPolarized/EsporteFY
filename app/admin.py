from django.contrib import admin

from .models import DataAccessRequest, DataDeletionRequest, DocumentoLGPD, Feedback, UserConsentLog


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
	list_display = ("id", "categoria", "assunto", "usuario", "lido", "respondido", "data_criacao")
	list_filter = ("categoria", "lido", "respondido", "data_criacao")
	search_fields = ("assunto", "mensagem", "email_contato", "usuario__username")
	readonly_fields = ("data_criacao",)


@admin.register(DocumentoLGPD)
class DocumentoLGPDAdmin(admin.ModelAdmin):
	list_display = ("tipo_documento", "titulo", "versao", "ativo", "data_vigencia", "atualizado_em")
	list_filter = ("tipo_documento", "ativo")
	search_fields = ("titulo", "versao", "conteudo")
	readonly_fields = ("criado_em", "atualizado_em")


@admin.register(DataAccessRequest)
class DataAccessRequestAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "status", "data_solicitacao", "data_processamento")
	list_filter = ("status", "data_solicitacao")
	search_fields = ("user__username", "user__email", "motivo")
	readonly_fields = ("data_solicitacao",)


@admin.register(UserConsentLog)
class UserConsentLogAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "consent_type", "accepted", "document_version", "source", "timestamp")
	list_filter = ("consent_type", "accepted", "source", "timestamp")
	search_fields = ("user__username", "user__email", "ip_address", "user_agent")
	readonly_fields = ("timestamp",)


@admin.register(DataDeletionRequest)
class DataDeletionRequestAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "status", "data_solicitacao", "data_expiracao", "data_processamento")
	list_filter = ("status", "data_solicitacao", "data_expiracao")
	search_fields = ("user__username", "user__email", "motivo", "confirm_token")
	readonly_fields = (
		"data_solicitacao",
		"data_expiracao",
		"data_confirmacao",
		"data_cancelamento",
		"data_processamento",
	)
