from django.urls import path
from .views import HomeView, FeedView, ResendVerificationView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('feed/', FeedView.as_view(), name='feed'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
]