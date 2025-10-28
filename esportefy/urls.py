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
    
    # Você não incluiu as URLs de 'quadras' e 'conteudo'
    # Se você ainda as usa, adicione-as aqui:
    # path('quadras/', include('quadras.urls')),
    # path('conteudo/', include('conteudo.urls')),
]

# Adiciona as URLs para servir arquivos estáticos e de mídia em modo DEBUG
if settings.DEBUG:
    # --- ESTA É A LINHA QUE FALTAVA ---
    # Ela serve o CSS, JS e imagens da sua pasta 'static'
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    
    # Esta linha serve os uploads dos usuários (fotos de perfil, etc.)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)