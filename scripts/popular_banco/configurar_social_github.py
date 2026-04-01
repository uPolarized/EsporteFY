import os

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


def run():
    site, _ = Site.objects.get_or_create(
        pk=1,
        defaults={"domain": "localhost:8000", "name": "EsporteFY"},
    )

    app, created = SocialApp.objects.get_or_create(
        provider="github",
        defaults={
            "name": "GitHub",
            "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
            "secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
        },
    )

    app.sites.add(site)

    return {
        "created": created,
        "site_domain": site.domain,
        "total_social_apps": SocialApp.objects.count(),
    }
