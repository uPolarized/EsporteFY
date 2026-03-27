import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'esportefy.settings')
django.setup()

from app.feed_utils import build_activity_payload
from social.models import Atividade
from django.contrib.auth.models import User
import json

# Pega a primeira atividade de amizade
activities = Atividade.objects.filter(verbo__icontains='amigos').first()
if activities:
    user = User.objects.first()
    payload = build_activity_payload(activities, viewer=user)
    print('=== PAYLOAD DE AMIZADE ===')
    print(json.dumps({
        'cta_type': payload.get('cta_type'),
        'like_count': payload.get('like_count'),
        'user_liked': payload.get('user_liked'),
        'cta_label': payload.get('cta_label'),
        'activity_id': payload.get('activity_id'),
    }, indent=2))
else:
    print('Sem atividades de amizade no banco')
    print(f'Total de atividades: {Atividade.objects.count()}')
