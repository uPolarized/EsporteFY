from django.urls import path
from .views import HomeView, FeedView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('feed/', FeedView.as_view(), name='feed'),
]