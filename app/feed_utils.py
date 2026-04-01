from collections import Counter
from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.timesince import timesince

from partidas.models import Partida


SECTION_LABELS = {
    'today': 'Hoje',
    'yesterday': 'Ontem',
    'week': 'Esta semana',
    'older': 'Mais antigas',
}

PRIORITY_BY_KIND = {
    'cancelled': 95,
    'created': 90,
    'joined': 78,
    'review': 74,
    'left': 68,
    'generic': 50,
}


def _safe_avatar_url(user):
    if not user or not hasattr(user, 'perfil') or not user.perfil.foto:
        return ''
    try:
        return user.perfil.foto.url
    except ValueError:
        return ''


def _section_key_for(timestamp):
    local_ts = timezone.localtime(timestamp)
    today = timezone.localdate()
    event_day = local_ts.date()

    if event_day == today:
        return 'today'
    if event_day == today - timedelta(days=1):
        return 'yesterday'
    if event_day >= today - timedelta(days=7):
        return 'week'
    return 'older'


def _time_label(timestamp):
    return f"ha {timesince(timestamp, timezone.now()).split(',')[0]}"


def _partida_meta(partida):
    meta = []

    if getattr(partida, 'esporte', None):
        meta.append(f"Esporte: {partida.esporte.nome}")

    if getattr(partida, 'quadra', None):
        meta.append(f"{partida.quadra.nome} • {partida.quadra.get_bairro_display()}")

    if getattr(partida, 'data_hora', None):
        meta.append(timezone.localtime(partida.data_hora).strftime('%d/%m • %H:%M'))

    if hasattr(partida, 'jogadores_necessarios'):
        meta.append(f"{partida.vagas_preenchidas}/{partida.jogadores_necessarios} jogadores")

    return meta[:4]


def build_activity_payload(activity, viewer=None, available_partida_ids=None):
    actor = activity.ator
    target = getattr(activity, 'alvo', None)
    actor_name = actor.username if actor else 'Usuario'
    target_name = getattr(target, 'username', str(target) if target else '')
    verb = (activity.verbo or '').lower()

    payload = {
        'id': activity.id,
        'actor_name': actor_name,
        'actor_initial': actor_name[:1].upper() if actor_name else '?',
        'actor_avatar_url': _safe_avatar_url(actor),
        'timestamp_label': _time_label(activity.timestamp),
        'timestamp_short': timezone.localtime(activity.timestamp).strftime('%H:%M'),
        'timestamp_iso': timezone.localtime(activity.timestamp).isoformat(),
        'section_key': _section_key_for(activity.timestamp),
        'kind': 'generic',
        'category': 'geral',
        'badge_label': 'Atividade',
        'icon': 'bi-lightning-charge-fill',
        'headline': f'{actor_name} movimentou o feed',
        'description': activity.verbo,
        'meta': [],
        'stats': [],
        'cta_type': 'url',
        'cta_label': 'Ver perfil',
        'cta_url': reverse('perfis:meu_perfil') if viewer and actor == viewer else reverse('perfis:ver_perfil', kwargs={'username': actor_name}),
        'cta_target': '',
        'priority': PRIORITY_BY_KIND['generic'],
        'is_past': False,
    }

    if 'agora sao amigos' in verb or 'agora são amigos' in verb:
        return None

    if isinstance(target, Partida):
        has_modal = available_partida_ids is None or target.id in available_partida_ids
        is_partida_past = target.data_hora < timezone.now()
        
        payload['category'] = 'partidas'
        payload['is_past'] = is_partida_past
        payload['meta'] = _partida_meta(target)
        payload['stats'] = [
            {'label': 'Esporte', 'value': target.esporte.nome if getattr(target, 'esporte', None) else 'Partida'},
            {'label': 'Vagas', 'value': f'{target.vagas_preenchidas}/{target.jogadores_necessarios}'},
        ]
        
        # Partida já aconteceu: desabilita CTA modal
        if is_partida_past:
            payload['cta_type'] = 'none'
            payload['cta_label'] = 'Partida finalizada'
            payload['meta'].insert(0, '⏱️ Esta partida já foi realizada')
        else:
            payload['cta_type'] = 'modal' if has_modal else 'none'
            payload['cta_label'] = 'Ver partida'
        
        payload['cta_target'] = f'detalhesPartidaModal{target.id}' if (has_modal and not is_partida_past) else ''
        payload['cta_url'] = '' if has_modal else payload['cta_url']

        if 'criou' in verb:
            payload.update({
                'kind': 'created',
                'badge_label': 'Nova Partida',
                'icon': 'bi-dribbble',
                'headline': target.titulo,
                'description': f'{actor_name} abriu uma nova partida para a comunidade.',
                'priority': PRIORITY_BY_KIND['created'],
            })
        elif 'entrou' in verb:
            payload.update({
                'kind': 'joined',
                'badge_label': 'Entrada',
                'icon': 'bi-person-check-fill',
                'headline': target.titulo,
                'description': f'{actor_name} confirmou presenca nessa partida.',
                'priority': PRIORITY_BY_KIND['joined'],
            })
        elif 'saiu' in verb:
            payload.update({
                'kind': 'left',
                'badge_label': 'Saida',
                'icon': 'bi-door-open-fill',
                'headline': target.titulo,
                'description': f'{actor_name} saiu dessa partida e liberou uma vaga.',
                'priority': PRIORITY_BY_KIND['left'],
            })
        elif 'cancelou' in verb:
            payload.update({
                'kind': 'cancelled',
                'badge_label': 'Cancelamento',
                'icon': 'bi-x-octagon-fill',
                'headline': target.titulo,
                'description': f'{actor_name} cancelou a partida antes do horario marcado.',
                'priority': PRIORITY_BY_KIND['cancelled'],
            })
        elif 'avaliou' in verb:
            payload.update({
                'kind': 'review',
                'category': 'avaliacoes',
                'badge_label': 'Avaliacao',
                'icon': 'bi-star-fill',
                'headline': target.titulo,
                'description': f'{actor_name} avaliou essa experiencia de jogo.',
                'priority': PRIORITY_BY_KIND['review'],
            })
            if not has_modal:
                payload.update({
                    'cta_type': 'url',
                    'cta_label': 'Ver minhas partidas',
                    'cta_url': reverse('partidas:minhas_partidas'),
                })

        return payload

    return payload


def build_activity_sections(activities, viewer=None, available_partida_ids=None):
    grouped = {key: [] for key in SECTION_LABELS}
    counts = Counter({'all': 0, 'partidas': 0, 'avaliacoes': 0})
    flat_items = []

    for activity in activities:
        payload = build_activity_payload(activity, viewer=viewer, available_partida_ids=available_partida_ids)
        if payload is None:
            continue
        grouped[payload['section_key']].append(payload)
        flat_items.append(payload)
        counts['all'] += 1
        if payload['category'] in ('partidas', 'avaliacoes'):
            counts[payload['category']] += 1

    sections = []
    for key, label in SECTION_LABELS.items():
        items = grouped[key]
        if items:
            sections.append({'key': key, 'label': label, 'items': items})

    # Destaques removidos temporariamente
    featured_items = []

    return sections, counts, featured_items