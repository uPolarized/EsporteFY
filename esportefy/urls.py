from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('app.urls')),
    path('perfis/', include('perfis.urls')),
    path('partidas/', include('partidas.urls')),
    path('social/', include('social.urls')),
]

# Serve os arquivos de mídia apenas em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# -----------------------------------