from django.urls import path
from .views import (
    csp_report_view,
    FeedView,
    FeedbackView,
    HomeView,
    LgpdCancelAccountDeletionView,
    LgpdConfirmAccountDeletionView,
    LgpdHubView,
    LgpdRequestAccountDeletionView,
    LgpdRequestDataAccessView,
    LgpdUpdateConsentView,
    ResendVerificationView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('security/csp-report/', csp_report_view, name='csp_report'),
    path('feed/', FeedView.as_view(), name='feed'),
    path('suporte/', FeedbackView.as_view(), name='feedback'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
    path('lgpd/', LgpdHubView.as_view(), name='lgpd_hub'),
    path('lgpd/meus-dados/solicitar/', LgpdRequestDataAccessView.as_view(), name='lgpd_request_data_access'),
    path('lgpd/consentimento/atualizar/', LgpdUpdateConsentView.as_view(), name='lgpd_update_consent'),
    path('lgpd/excluir-conta/solicitar/', LgpdRequestAccountDeletionView.as_view(), name='lgpd_request_account_deletion'),
    path('lgpd/excluir-conta/cancelar/<int:request_id>/', LgpdCancelAccountDeletionView.as_view(), name='lgpd_cancel_account_deletion'),
    path('lgpd/excluir-conta/confirmar/<str:token>/', LgpdConfirmAccountDeletionView.as_view(), name='lgpd_confirm_account_deletion'),
]