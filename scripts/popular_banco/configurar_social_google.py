import os

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


def run():
    site, _ = Site.objects.get_or_create(
        pk=1,
        defaults={'domain': 'localhost:8000', 'name': 'EsporteFY'},
    )

    app, created = SocialApp.objects.get_or_create(
        provider='google',
        defaults={
            'name': 'Google',
            'client_id': os.getenv(
                'GOOGLE_CLIENT_ID',
                '507570514838-25euhqevu5raq8eb031fsccfqup497o7.apps.googleusercontent.com',
            ),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', 'seu_secret_aqui'),
        },
    )

    app.sites.add(site)

    return {
        'created': created,
        'site_domain': site.domain,
        'total_social_apps': SocialApp.objects.count(),
    }
