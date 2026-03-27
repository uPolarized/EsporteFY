import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esportefy.settings')
django.setup()

from django.contrib.sites.models import Site
from django.contrib.socialaccount.models import SocialApp

# Pega ou cria o site
site, _ = Site.objects.get_or_create(pk=1, defaults={'domain': 'localhost:8000', 'name': 'EsporteFY'})

# Cria a SocialApp do Google
google_app, created = SocialApp.objects.get_or_create(
    provider='google',
    defaults={
        'name': 'Google',
        'client_id': os.getenv('GOOGLE_CLIENT_ID', '507570514838-25euhqevu5raq8eb031fsccfqup497o7.apps.googleusercontent.com'),
        'secret': os.getenv('GOOGLE_CLIENT_SECRET', 'seu_secret_aqui'),
    }
)

if created:
    google_app.sites.add(site)
    print("✓ Google SocialApp criada")
else:
    print("✓ Google SocialApp já existe")

print(f"✓ Site: {site.domain}")
print(f"✓ Total SocialApps: {SocialApp.objects.count()}")
