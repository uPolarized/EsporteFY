from django.contrib import admin
from django.urls import path, include
from app import views

# A linha "from app.forms import CustomSignupForm" foi removida daqui

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("app.urls")),
    path('accounts/', include('allauth.urls'))
]
