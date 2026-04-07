from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.dateparse import parse_date, parse_time
from django.db.models import Prefetch
from django.db import connection
from django.urls import reverse
from datetime import timedelta
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.cache import cache # ✅ OTIMIZAÇÃO: Importa o cache do Django
from django.contrib.contenttypes.models import ContentType # ✅ OTIMIZAÇÃO: Para pré-buscar GFKs
from django.contrib import messages
from django.contrib.auth.models import User
from allauth.account.views import ConfirmEmailView
from allauth.account.models import EmailAddress
from allauth.socialaccount.views import ConnectionsView
import json
import uuid
import logging
import hashlib
import random

# Importações dos modelos e API
import requests
from partidas.models import AvaliacaoJogador, AvaliacaoQuadra, Esporte, Partida, PartidaRSVP
from partidas.finalizacao import processar_partidas_finalizadas
from quadras.models import Quadra
from social.models import Atividade
from app.feed_utils import build_activity_sections
from .forms import DataAccessRequestForm, FeedbackForm
from .models import DataAccessRequest, DataDeletionRequest, DocumentoLGPD, Feedback, UserConsentLog
from perfis.models import AccountLoginEvent, UserPrivacySettings
# ✅ OTIMIZAÇÃO: As funções da API são importadas do cliente,
# não definidas localmente.
from conteudo.api_client import buscar_noticias_esportivas, buscar_clima_marica, buscar_previsao_chuva


logger = logging.getLogger(__name__)


class CustomSocialConnectionsView(ConnectionsView):
    template_name = 'socialaccount/connections.html'
    _TWO_FACTOR_KEY_HASH = 'pending_2fa_code_hash'
    _TWO_FACTOR_KEY_EXP = 'pending_2fa_expires_at'
    _TWO_FACTOR_KEY_TARGET = 'pending_2fa_target_state'

    def _privacy_settings(self):
        settings_obj, _ = UserPrivacySettings.objects.get_or_create(user=self.request.user)
        return settings_obj

    def _get_active_sessions(self):
        sessions = []
        now = timezone.now()
        current_key = self.request.session.session_key

        for db_session in Session.objects.filter(expire_date__gte=now):
            try:
                data = db_session.get_decoded()
            except Exception:
                continue

            if str(data.get('_auth_user_id')) != str(self.request.user.id):
                continue

            last_seen_raw = data.get('_device_last_seen')
            last_seen = parse_datetime(last_seen_raw) if last_seen_raw else None

            sessions.append({
                'session_key': db_session.session_key,
                'is_current': db_session.session_key == current_key,
                'ip': data.get('_device_ip') or 'Não disponível',
                'user_agent': data.get('_device_ua') or 'Dispositivo não identificado',
                'last_seen': last_seen,
                'expires_at': db_session.expire_date,
            })

        fallback_dt = timezone.now() - timedelta(days=36500)
        sessions.sort(key=lambda item: item['last_seen'] or fallback_dt, reverse=True)
        return sessions

    def _is_two_factor_pending(self):
        expires_at = self.request.session.get(self._TWO_FACTOR_KEY_EXP)
        if not expires_at:
            return False
        parsed = parse_datetime(expires_at)
        if not parsed:
            return False
        return parsed > timezone.now()

    def _clear_two_factor_pending(self):
        for key in (self._TWO_FACTOR_KEY_HASH, self._TWO_FACTOR_KEY_EXP, self._TWO_FACTOR_KEY_TARGET):
            if key in self.request.session:
                del self.request.session[key]

    def _issue_two_factor_code(self, target_enabled):
        code = f'{random.randint(0, 999999):06d}'
        digest = hashlib.sha256(f"{settings.SECRET_KEY}:{self.request.user.id}:{code}".encode('utf-8')).hexdigest()
        self.request.session[self._TWO_FACTOR_KEY_HASH] = digest
        self.request.session[self._TWO_FACTOR_KEY_EXP] = (timezone.now() + timedelta(minutes=10)).isoformat()
        self.request.session[self._TWO_FACTOR_KEY_TARGET] = '1' if target_enabled else '0'

        send_mail(
            subject='Código de segurança EsporteFY',
            message=(
                f'Olá, {self.request.user.username}.\n\n'
                f'Seu código de verificação é: {code}\n'
                'Ele expira em 10 minutos.\n\n'
                'Se você não solicitou essa ação, ignore esta mensagem.'
            ),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=[self.request.user.email],
            fail_silently=False,
        )

    def _verify_two_factor_code(self, provided_code):
        expires_at = self.request.session.get(self._TWO_FACTOR_KEY_EXP)
        expected_hash = self.request.session.get(self._TWO_FACTOR_KEY_HASH)
        if not expires_at or not expected_hash:
            return False, 'Nenhum código pendente. Solicite um novo código.'

        parsed_exp = parse_datetime(expires_at)
        if not parsed_exp or parsed_exp <= timezone.now():
            self._clear_two_factor_pending()
            return False, 'Código expirado. Solicite um novo código.'

        code = (provided_code or '').strip()
        if not code.isdigit() or len(code) != 6:
            return False, 'Código inválido. Digite os 6 números recebidos por e-mail.'

        digest = hashlib.sha256(f"{settings.SECRET_KEY}:{self.request.user.id}:{code}".encode('utf-8')).hexdigest()
        if digest != expected_hash:
            return False, 'Código incorreto. Verifique e tente novamente.'

        target_enabled = self.request.session.get(self._TWO_FACTOR_KEY_TARGET) == '1'
        self._clear_two_factor_pending()
        return True, target_enabled

    def get_context_data(self, **kwargs):
        context = {}
        request = kwargs.get('request')
        processar_partidas_finalizadas()

        user_agent = (request.META.get('HTTP_USER_AGENT') or '').lower()
        is_mobile_client = any(token in user_agent for token in ['mobi', 'android', 'iphone', 'ipad'])

        if is_mobile_client:
            aba_atual = request.GET.get('aba', 'partidas')
            if aba_atual not in ['feed', 'partidas', 'atividades', 'noticias']:
                aba_atual = 'partidas'
        else:
            # No desktop o feed deve ser sempre completo.
            aba_atual = 'feed'
        context['aba_atual'] = aba_atual

        if aba_atual in ['feed', 'noticias']:
            context['clima_atual'] = buscar_clima_marica()
            context['noticias'] = buscar_noticias_esportivas()
            context['previsao_chuva'] = buscar_previsao_chuva()

        if aba_atual in ['feed', 'partidas']:
            bairro_filtrado = request.GET.get('bairro', 'todos')
            esporte_filtrado = request.GET.get('esporte', 'todos')
            data_filtro = request.GET.get('date_filter', 'all')
            custom_date_raw = request.GET.get('custom_date', '').strip()
            custom_time_raw = request.GET.get('custom_time', '').strip()
            
            partidas_queryset = Partida.objects.filter(
                data_hora__gte=timezone.now()
            ).select_related(
                'quadra', 'esporte', 'organizador'
            ).prefetch_related(
                'jogadores_confirmados',
                'quadra__fotos',
            ).order_by('data_hora')

            if bairro_filtrado and bairro_filtrado != 'todos':
                partidas_queryset = partidas_queryset.filter(quadra__bairro=bairro_filtrado)

            if esporte_filtrado and esporte_filtrado != 'todos':
                partidas_queryset = partidas_queryset.filter(esporte__id=esporte_filtrado)

            hoje_local = timezone.localdate()
            if data_filtro == 'today':
                partidas_queryset = partidas_queryset.filter(data_hora__date=hoje_local)
            elif data_filtro == 'tomorrow':
                partidas_queryset = partidas_queryset.filter(data_hora__date=hoje_local + timedelta(days=1))
            elif data_filtro == 'custom':
                custom_date = parse_date(custom_date_raw) if custom_date_raw else None
                custom_time = parse_time(custom_time_raw) if custom_time_raw else None
                if custom_date:
                    partidas_queryset = partidas_queryset.filter(data_hora__date=custom_date)
                if custom_time:
                    partidas_queryset = partidas_queryset.filter(data_hora__time__gte=custom_time)

            partidas_list = list(partidas_queryset[:self.FEED_MAX_PARTIDAS])

            rsvp_by_partida = {
                partida_id: status
                for partida_id, status in PartidaRSVP.objects.filter(
                    partida__in=partidas_list,
                    jogador=request.user,
                ).values_list('partida_id', 'status')
            }

            confirmadas_ids = set(
                Partida.jogadores_confirmados.through.objects.filter(
                    user_id=request.user.id,
                    partida_id__in=[p.id for p in partidas_list],
                ).values_list('partida_id', flat=True)
            )

            pending_by_partida = {}
            pending_qs = PartidaRSVP.objects.filter(
                partida__in=partidas_list,
                partida__organizador=request.user,
                status=PartidaRSVP.STATUS_AGUARDANDO,
            ).select_related('jogador', 'jogador__perfil').order_by('criado_em')
            for rsvp in pending_qs:
                pending_by_partida.setdefault(rsvp.partida_id, []).append(rsvp)

            for partida in partidas_list:
                fallback_status = (
                    PartidaRSVP.STATUS_CONFIRMADO
                    if partida.id in confirmadas_ids
                    else None
                )
                partida.user_rsvp_status = rsvp_by_partida.get(partida.id, fallback_status)
                partida.pending_rsvps = pending_by_partida.get(partida.id, [])

            context['partidas'] = partidas_list
            context['esportes_disponiveis'] = Esporte.objects.all()
            context['bairros_disponiveis'] = Quadra.BAIRRO_CHOICES
            context['bairro_atual'] = bairro_filtrado
            context['bairro_atual_nome'] = dict(Quadra.BAIRRO_CHOICES).get(bairro_filtrado, 'Todos')
            context['esporte_atual'] = esporte_filtrado
            context['esporte_atual_nome'] = (
                Esporte.objects.filter(id=esporte_filtrado).values_list('nome', flat=True).first()
                if esporte_filtrado != 'todos' else 'Todos'
            ) or 'Todos'
            context['data_filtro'] = data_filtro
            context['custom_date'] = custom_date_raw
            context['custom_time'] = custom_time_raw

            if data_filtro == 'today':
                context['data_filtro_nome'] = 'Hoje'
            elif data_filtro == 'tomorrow':
                context['data_filtro_nome'] = 'Amanhã'
            elif data_filtro == 'custom' and custom_date_raw and custom_time_raw:
                context['data_filtro_nome'] = f'{custom_date_raw} · {custom_time_raw}'
            elif data_filtro == 'custom' and custom_date_raw:
                context['data_filtro_nome'] = custom_date_raw
            elif data_filtro == 'custom' and custom_time_raw:
                context['data_filtro_nome'] = f'Após {custom_time_raw}'
            else:
                context['data_filtro_nome'] = 'Qualquer data'

            context['partidas_hoje_count'] = partidas_queryset.filter(data_hora__date=hoje_local).count()

            online_threshold = timezone.now() - timedelta(minutes=30)
            context['jogadores_online_count'] = User.objects.filter(last_login__gte=online_threshold).count()

            if bairro_filtrado and bairro_filtrado != 'todos':
                context['quadras_proximas_count'] = Quadra.objects.filter(bairro=bairro_filtrado).count()
            else:
                context['quadras_proximas_count'] = Quadra.objects.count()

        if aba_atual in ['feed', 'atividades']:
            uma_semana_atras = timezone.now() - timedelta(days=7)

            atividades_list = Atividade.objects.filter(
                timestamp__gte=uma_semana_atras
            ).select_related(
                'ator__perfil'
            ).order_by('-timestamp')[:20]

            gfk_map = {}
            for atividade in atividades_list:
                if atividade.content_type_id not in gfk_map:
                    gfk_map[atividade.content_type_id] = []
                gfk_map[atividade.content_type_id].append(atividade.object_id)

            content_cache = {}
            for ct_id, object_ids in gfk_map.items():
                try:
                    ct = ContentType.objects.get_for_id(ct_id)
                    model_class = ct.model_class()
                    
                    if model_class == Partida:
                        queryset = model_class.objects.filter(id__in=object_ids).select_related('quadra')
                    else:
                        queryset = model_class.objects.filter(id__in=object_ids)
                    
                    for obj in queryset:
                        content_cache[(ct_id, obj.id)] = obj
                        
                except Exception as e:
                    pass

            for atividade in atividades_list:
                cache_key = (atividade.content_type_id, atividade.object_id)
                atividade.alvo = content_cache.get(cache_key)

            context['atividades'] = atividades_list

            partidas_rel_ids = {p.id for p in context.get('partidas', [])} if context.get('partidas') else set()
            activity_sections, activity_counts, featured_activities = build_activity_sections(
                atividades_list,
                viewer=request.user,
                available_partida_ids=partidas_rel_ids,
            )
            context['activity_sections'] = activity_sections
            context['activity_counts'] = activity_counts
            context['featured_activities'] = featured_activities

        return context

    def post(self, request, *args, **kwargs):
        if 'action_remove' in request.POST:
            return super().post(request, *args, **kwargs)

        privacy = self._privacy_settings()

        if 'action_privacy_save' in request.POST:
            privacy.show_profile_public = bool(request.POST.get('show_profile_public'))
            privacy.show_online_status = bool(request.POST.get('show_online_status'))
            privacy.allow_friend_requests = bool(request.POST.get('allow_friend_requests'))
            privacy.save(update_fields=['show_profile_public', 'show_online_status', 'allow_friend_requests', 'updated_at'])
            messages.success(request, 'Configurações de privacidade atualizadas com sucesso.')
            return redirect('socialaccount_connections')

        if 'action_sessions_logout_others' in request.POST:
            current_key = request.session.session_key
            removed = 0
            for db_session in Session.objects.filter(expire_date__gte=timezone.now()):
                try:
                    data = db_session.get_decoded()
                except Exception:
                    continue
                if str(data.get('_auth_user_id')) != str(request.user.id):
                    continue
                if db_session.session_key == current_key:
                    continue
                db_session.delete()
                removed += 1

            if removed:
                messages.success(request, f'{removed} sessão(ões) encerrada(s).')
            else:
                messages.info(request, 'Nenhuma outra sessão ativa foi encontrada.')
            return redirect('socialaccount_connections')

        if 'action_2fa_send_code' in request.POST:
            target_enabled = not privacy.two_factor_email_enabled
            if not request.user.email:
                messages.error(request, 'Adicione um e-mail válido antes de configurar 2FA por e-mail.')
                return redirect('socialaccount_connections')

            try:
                self._issue_two_factor_code(target_enabled=target_enabled)
            except Exception:
                logger.exception('Falha ao enviar código 2FA por e-mail')
                messages.error(request, 'Não foi possível enviar o código agora. Tente novamente em instantes.')
                return redirect('socialaccount_connections')

            messages.success(request, 'Código enviado para seu e-mail. Digite-o para confirmar a alteração.')
            return redirect('socialaccount_connections')

        if 'action_2fa_verify' in request.POST:
            ok, result = self._verify_two_factor_code(request.POST.get('two_factor_code'))
            if not ok:
                messages.error(request, result)
                return redirect('socialaccount_connections')

            privacy.two_factor_email_enabled = bool(result)
            privacy.save(update_fields=['two_factor_email_enabled', 'updated_at'])
            messages.success(request, '2FA por e-mail atualizada com sucesso.')
            return redirect('socialaccount_connections')

        return super().post(request, *args, **kwargs)


@csrf_exempt
@require_POST
def csp_report_view(request):
    raw_body = request.body or b''
    if len(raw_body) > 32_000:
        raw_body = raw_body[:32_000]

    try:
        payload = json.loads(raw_body.decode('utf-8') or '{}')
    except Exception:
        payload = {'invalid_json': True}

    report = payload.get('csp-report') if isinstance(payload, dict) else None
    logger.warning('CSP report received: %s', report or payload)
    return JsonResponse({'ok': True})


class EsporteFYConfirmEmailView(ConfirmEmailView):
    """Sobrescreve o allauth para redirecionar ao feed com mensagem de sucesso."""
    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        # Só adiciona a mensagem quando a confirmação foi bem-sucedida (redirect 3xx)
        if response.status_code in (301, 302):
            messages.success(
                self.request,
                "E-mail confirmado com sucesso! Bem-vindo ao EsporteFY!",
            )
        return response

    def get_success_url(self):
        return '/feed/'


class ResendVerificationView(LoginRequiredMixin, View):
    """Reenvia o e-mail de confirmação para o usuário autenticado."""
    def post(self, request, *args, **kwargs):
        try:
            email_address = EmailAddress.objects.get(user=request.user, primary=True, verified=False)
            email_address.send_confirmation(request)
            messages.info(request, "E-mail de confirmação reenviado. Verifique sua caixa de entrada.")
        except EmailAddress.DoesNotExist:
            messages.warning(request, "Nenhum e-mail pendente de verificação encontrado.")
        return redirect('account_email_verification_sent')


class HomeView(View):
    template_name = "home.html"
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('feed')
        return render(request, self.template_name)


class FeedbackView(View):
    template_name = "account/feedback.html"

    def get(self, request, *args, **kwargs):
        initial = {}
        if request.user.is_authenticated:
            initial["email_contato"] = request.user.email or ""
        form = FeedbackForm(initial=initial)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            if request.user.is_authenticated:
                feedback.usuario = request.user
                if not feedback.email_contato:
                    feedback.email_contato = request.user.email or ""
            feedback.save()
            messages.success(request, "Feedback enviado com sucesso. Obrigado por contribuir com o EsporteFY!")
            return redirect("feedback")

        return render(request, self.template_name, {"form": form})

class FeedView(LoginRequiredMixin, View):
    FEED_MAX_PARTIDAS = 40

    template_name = 'feed.html'
    
    def get(self, request, *args, **kwargs):
        # Bloqueia acesso ao feed enquanto o e-mail não for confirmado
        if not EmailAddress.objects.filter(user=request.user, verified=True).exists():
            return redirect('account_email_verification_sent')
        context = self.get_context_data(request=request)
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = {}
        request = kwargs.get('request')

        user_agent = (request.META.get('HTTP_USER_AGENT') or '').lower()
        is_mobile_client = any(token in user_agent for token in ['mobi', 'android', 'iphone', 'ipad'])

        if is_mobile_client:
            aba_atual = request.GET.get('aba', 'partidas')
            if aba_atual not in ['feed', 'partidas', 'atividades', 'noticias']:
                aba_atual = 'partidas'
        else:
            # Desktop sempre carrega o feed completo.
            aba_atual = 'feed'

        context['is_mobile_client'] = is_mobile_client
        context['aba_atual'] = aba_atual

        if aba_atual in ['feed', 'noticias']:
            context['clima_atual'] = buscar_clima_marica()
            context['noticias'] = buscar_noticias_esportivas()
            context['previsao_chuva'] = buscar_previsao_chuva()

        if aba_atual in ['feed', 'partidas']:
            bairro_filtrado = request.GET.get('bairro', 'todos')
            esporte_filtrado = request.GET.get('esporte', 'todos')
            data_filtro = request.GET.get('date_filter', 'all')
            custom_date_raw = request.GET.get('custom_date', '').strip()
            custom_time_raw = request.GET.get('custom_time', '').strip()
            
            partidas_queryset = Partida.objects.filter(
                data_hora__gte=timezone.now()
            ).select_related(
                'quadra', 'esporte', 'organizador'
            ).prefetch_related(
                'jogadores_confirmados',
                'quadra__fotos',
            ).order_by('data_hora')

            if bairro_filtrado and bairro_filtrado != 'todos':
                partidas_queryset = partidas_queryset.filter(quadra__bairro=bairro_filtrado)

            if esporte_filtrado and esporte_filtrado != 'todos':
                partidas_queryset = partidas_queryset.filter(esporte__id=esporte_filtrado)

            hoje_local = timezone.localdate()
            if data_filtro == 'today':
                partidas_queryset = partidas_queryset.filter(data_hora__date=hoje_local)
            elif data_filtro == 'tomorrow':
                partidas_queryset = partidas_queryset.filter(data_hora__date=hoje_local + timedelta(days=1))
            elif data_filtro == 'custom':
                custom_date = parse_date(custom_date_raw) if custom_date_raw else None
                custom_time = parse_time(custom_time_raw) if custom_time_raw else None
                if custom_date:
                    partidas_queryset = partidas_queryset.filter(data_hora__date=custom_date)
                if custom_time:
                    partidas_queryset = partidas_queryset.filter(data_hora__time__gte=custom_time)

            partidas_list = list(partidas_queryset[:self.FEED_MAX_PARTIDAS])

            rsvp_by_partida = {
                partida_id: status
                for partida_id, status in PartidaRSVP.objects.filter(
                    partida__in=partidas_list,
                    jogador=request.user,
                ).values_list('partida_id', 'status')
            }

            confirmadas_ids = set(
                Partida.jogadores_confirmados.through.objects.filter(
                    user_id=request.user.id,
                    partida_id__in=[p.id for p in partidas_list],
                ).values_list('partida_id', flat=True)
            )

            pending_by_partida = {}
            pending_qs = PartidaRSVP.objects.filter(
                partida__in=partidas_list,
                partida__organizador=request.user,
                status=PartidaRSVP.STATUS_AGUARDANDO,
            ).select_related('jogador', 'jogador__perfil').order_by('criado_em')
            for rsvp in pending_qs:
                pending_by_partida.setdefault(rsvp.partida_id, []).append(rsvp)

            for partida in partidas_list:
                fallback_status = (
                    PartidaRSVP.STATUS_CONFIRMADO
                    if partida.id in confirmadas_ids
                    else None
                )
                partida.user_rsvp_status = rsvp_by_partida.get(partida.id, fallback_status)
                partida.pending_rsvps = pending_by_partida.get(partida.id, [])

            context['partidas'] = partidas_list
            context['esportes_disponiveis'] = Esporte.objects.all()
            context['bairros_disponiveis'] = Quadra.BAIRRO_CHOICES
            context['bairro_atual'] = bairro_filtrado
            context['bairro_atual_nome'] = dict(Quadra.BAIRRO_CHOICES).get(bairro_filtrado, 'Todos')
            context['esporte_atual'] = esporte_filtrado
            context['esporte_atual_nome'] = (
                Esporte.objects.filter(id=esporte_filtrado).values_list('nome', flat=True).first()
                if esporte_filtrado != 'todos' else 'Todos'
            ) or 'Todos'
            context['data_filtro'] = data_filtro
            context['custom_date'] = custom_date_raw
            context['custom_time'] = custom_time_raw

            if data_filtro == 'today':
                context['data_filtro_nome'] = 'Hoje'
            elif data_filtro == 'tomorrow':
                context['data_filtro_nome'] = 'Amanhã'
            elif data_filtro == 'custom' and custom_date_raw and custom_time_raw:
                context['data_filtro_nome'] = f'{custom_date_raw} · {custom_time_raw}'
            elif data_filtro == 'custom' and custom_date_raw:
                context['data_filtro_nome'] = custom_date_raw
            elif data_filtro == 'custom' and custom_time_raw:
                context['data_filtro_nome'] = f'Após {custom_time_raw}'
            else:
                context['data_filtro_nome'] = 'Qualquer data'

            context['partidas_hoje_count'] = partidas_queryset.filter(data_hora__date=hoje_local).count()

            online_threshold = timezone.now() - timedelta(minutes=30)
            context['jogadores_online_count'] = User.objects.filter(last_login__gte=online_threshold).count()

            if bairro_filtrado and bairro_filtrado != 'todos':
                context['quadras_proximas_count'] = Quadra.objects.filter(bairro=bairro_filtrado).count()
            else:
                context['quadras_proximas_count'] = Quadra.objects.count()

        if aba_atual in ['feed', 'atividades']:
            uma_semana_atras = timezone.now() - timedelta(days=7)

            atividades_list = Atividade.objects.filter(
                timestamp__gte=uma_semana_atras
            ).select_related(
                'ator__perfil'
            ).order_by('-timestamp')[:20]

            gfk_map = {}
            for atividade in atividades_list:
                if atividade.content_type_id not in gfk_map:
                    gfk_map[atividade.content_type_id] = []
                gfk_map[atividade.content_type_id].append(atividade.object_id)

            content_cache = {}
            for ct_id, object_ids in gfk_map.items():
                try:
                    ct = ContentType.objects.get_for_id(ct_id)
                    model_class = ct.model_class()
                    
                    if model_class == Partida:
                        queryset = model_class.objects.filter(id__in=object_ids).select_related('quadra')
                    else:
                        queryset = model_class.objects.filter(id__in=object_ids)
                    
                    for obj in queryset:
                        content_cache[(ct_id, obj.id)] = obj
                        
                except Exception as e:
                    pass

            for atividade in atividades_list:
                cache_key = (atividade.content_type_id, atividade.object_id)
                atividade.alvo = content_cache.get(cache_key)

            context['atividades'] = atividades_list

            partidas_rel_ids = {p.id for p in context.get('partidas', [])} if context.get('partidas') else set()
            activity_sections, activity_counts, featured_activities = build_activity_sections(
                atividades_list,
                viewer=request.user,
                available_partida_ids=partidas_rel_ids,
            )
            context['activity_sections'] = activity_sections
            context['activity_counts'] = activity_counts
            context['featured_activities'] = featured_activities

        return context

# 🐛 CORREÇÃO: Removemos a definição local de buscar_clima_marica().
# Ela deve viver em 'conteudo/api_client.py' e ser importada (como feito acima).


def _table_exists(table_name):
    try:
        return table_name in connection.introspection.table_names()
    except Exception:
        return False


def _resolve_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _get_active_document(doc_type):
    if not _table_exists(DocumentoLGPD._meta.db_table):
        return None
    return (
        DocumentoLGPD.objects.filter(tipo_documento=doc_type, ativo=True)
        .order_by("-data_vigencia", "-atualizado_em")
        .first()
    )


def _serialize_datetime(value):
    if not value:
        return None
    return timezone.localtime(value).isoformat()


def _expire_pending_deletion_requests():
    if not _table_exists(DataDeletionRequest._meta.db_table):
        return
    now = timezone.now()
    DataDeletionRequest.objects.filter(
        status=DataDeletionRequest.STATUS_PENDING,
        data_expiracao__lt=now,
    ).update(status=DataDeletionRequest.STATUS_EXPIRED)


def _build_user_data_export_payload(user):
    perfil = getattr(user, "perfil", None)

    payload = {
        "export_date": timezone.now().isoformat(),
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": _serialize_datetime(user.date_joined),
        },
        "profile": {
            "age": getattr(perfil, "idade", None) if perfil else None,
            "city": getattr(perfil, "cidade", None) if perfil else None,
            "sports": getattr(perfil, "esportes_preferidos", None) if perfil else None,
            "skill_level": getattr(perfil, "nivel_habilidade", None) if perfil else None,
            "bio": getattr(perfil, "mini_bio", "") if perfil else "",
        },
        "posts": [],
        "comments": [],
        "matches": [],
        "evaluations": [],
        "feedback": [],
        "consent_logs": [],
    }

    try:
        for partida in Partida.objects.filter(organizador=user).order_by("-data_hora"):
            payload["matches"].append({
                "id": partida.id,
                "title": partida.titulo,
                "sport": partida.esporte.nome if partida.esporte_id else None,
                "court": partida.quadra.nome if partida.quadra_id else None,
                "date": _serialize_datetime(partida.data_hora),
                "required_players": partida.jogadores_necessarios,
                "confirmed_players": partida.vagas_preenchidas,
            })
    except Exception:
        pass

    try:
        avaliacoes_quadra = AvaliacaoQuadra.objects.filter(avaliador=user).select_related("partida")
        avaliacoes_jogador = AvaliacaoJogador.objects.filter(avaliador=user).select_related("partida", "avaliado")
        for av in avaliacoes_quadra:
            payload["evaluations"].append({
                "type": "court",
                "match_id": av.partida_id,
                "match_title": av.partida.titulo if av.partida_id else None,
                "score": av.nota_quadra,
                "comment": av.comentario,
                "created_at": _serialize_datetime(av.data_avaliacao),
            })
        for av in avaliacoes_jogador:
            payload["evaluations"].append({
                "type": "player",
                "match_id": av.partida_id,
                "match_title": av.partida.titulo if av.partida_id else None,
                "rated_user": av.avaliado.username if av.avaliado_id else None,
                "score": av.nota_fair_play,
                "created_at": _serialize_datetime(av.data_avaliacao),
            })
    except Exception:
        pass

    try:
        for item in Feedback.objects.filter(usuario=user).order_by("-data_criacao"):
            payload["feedback"].append({
                "id": item.id,
                "category": item.categoria,
                "subject": item.assunto,
                "message": item.mensagem,
                "created_at": _serialize_datetime(item.data_criacao),
            })
    except Exception:
        pass

    try:
        logs = UserConsentLog.objects.filter(user=user).order_by("-timestamp")
        for item in logs:
            payload["consent_logs"].append({
                "type": item.get_consent_type_display(),
                "accepted": item.accepted,
                "timestamp": _serialize_datetime(item.timestamp),
                "version": item.document_version or "1.0",
            })
    except Exception:
        pass

    return payload


def _process_data_access_request(data_request):
    now = timezone.now()
    data_request.status = DataAccessRequest.STATUS_PROCESSING
    data_request.save(update_fields=["status"])

    try:
        payload = _build_user_data_export_payload(data_request.user)
        file_content = json.dumps(payload, ensure_ascii=False, indent=2)
        filename = f"user_data_{data_request.user_id}_{int(now.timestamp())}.json"
        data_request.arquivo_exportacao.save(
            filename,
            ContentFile(file_content.encode("utf-8")),
            save=False,
        )
        data_request.status = DataAccessRequest.STATUS_COMPLETED
        data_request.data_processamento = timezone.now()
        data_request.save(update_fields=["arquivo_exportacao", "status", "data_processamento"])
    except Exception as exc:
        data_request.status = DataAccessRequest.STATUS_DENIED
        data_request.data_processamento = timezone.now()
        data_request.observacoes_admin = f"Falha ao gerar arquivo: {exc}"
        data_request.save(update_fields=["status", "data_processamento", "observacoes_admin"])


def _send_account_deletion_email(request, deletion_request):
    confirm_url = request.build_absolute_uri(
        reverse("lgpd_confirm_account_deletion", kwargs={"token": deletion_request.confirm_token})
    )
    cancel_url = request.build_absolute_uri(
        reverse("lgpd_hub") + "?tab=meus-dados"
    )

    context = {
        "username": deletion_request.user.username,
        "confirm_url": confirm_url,
        "cancel_url": cancel_url,
        "expires_at": timezone.localtime(deletion_request.data_expiracao).strftime("%d/%m/%Y %H:%M"),
        "support_email": getattr(settings, "DEFAULT_FROM_EMAIL", "contato.esportefy@gmail.com"),
    }
    subject = "EsporteFY | Confirmacao de exclusao da conta"
    text_body = render_to_string("emails/account_deletion_confirmation.txt", context)
    html_body = render_to_string("emails/account_deletion_confirmation.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[deletion_request.user.email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)


def _anonymize_user_account(user):
    unique_suffix = f"{user.id}_{int(timezone.now().timestamp())}"
    user.username = f"deleted_{unique_suffix}"
    user.email = f"deleted_{unique_suffix}@deleted.local"
    user.first_name = ""
    user.last_name = ""
    user.is_active = False
    user.set_unusable_password()
    user.save(update_fields=["username", "email", "first_name", "last_name", "is_active", "password"])


class LgpdHubView(View):
    template_name = "lgpd/centro_privacidade.html"

    def get(self, request, *args, **kwargs):
        tab_ativa = request.GET.get("tab") or "politica"
        if tab_ativa not in {"politica", "termos", "meus-dados"}:
            tab_ativa = "politica"
        if tab_ativa == "meus-dados" and not request.user.is_authenticated:
            tab_ativa = "politica"

        _expire_pending_deletion_requests()

        politica = _get_active_document("privacy_policy")
        termos = _get_active_document("terms_of_service")

        has_data_access_table = _table_exists(DataAccessRequest._meta.db_table)
        has_consent_log_table = _table_exists(UserConsentLog._meta.db_table)
        has_data_deletion_table = _table_exists(DataDeletionRequest._meta.db_table)

        data_access_requests = []
        can_request_data_access = False
        data_access_form = DataAccessRequestForm()
        data_deletion_requests = []
        can_request_data_deletion = False

        consentimentos_atuais = {
            "terms_of_service": None,
            "privacy_policy": None,
            "cookies": None,
        }

        if request.user.is_authenticated:
            if has_data_access_table:
                data_access_requests = list(
                    DataAccessRequest.objects.filter(user=request.user).order_by("-data_solicitacao")[:20]
                )
                can_request_data_access = not DataAccessRequest.objects.filter(
                    user=request.user,
                    status__in=[
                        DataAccessRequest.STATUS_PENDING,
                        DataAccessRequest.STATUS_PROCESSING,
                    ],
                ).exists()

            if has_data_deletion_table:
                data_deletion_requests = list(
                    DataDeletionRequest.objects.filter(user=request.user).order_by("-data_solicitacao")[:20]
                )
                can_request_data_deletion = not DataDeletionRequest.objects.filter(
                    user=request.user,
                    status=DataDeletionRequest.STATUS_PENDING,
                    data_expiracao__gte=timezone.now(),
                ).exists()

            if has_consent_log_table:
                consent_logs = (
                    UserConsentLog.objects.filter(user=request.user)
                    .order_by("consent_type", "-timestamp")
                )
                for log in consent_logs:
                    if log.consent_type in consentimentos_atuais and consentimentos_atuais[log.consent_type] is None:
                        consentimentos_atuais[log.consent_type] = log

        context = {
            "tab_ativa": tab_ativa,
            "politica": politica,
            "termos": termos,
            "has_data_access_table": has_data_access_table,
            "has_consent_log_table": has_consent_log_table,
            "has_data_deletion_table": has_data_deletion_table,
            "data_access_form": data_access_form,
            "data_access_requests": data_access_requests,
            "can_request_data_access": can_request_data_access,
            "data_deletion_requests": data_deletion_requests,
            "can_request_data_deletion": can_request_data_deletion,
            "consentimentos_atuais": consentimentos_atuais,
            "support_email": getattr(settings, "DEFAULT_FROM_EMAIL", "contato.esportefy@gmail.com"),
        }
        return render(request, self.template_name, context)


class LgpdRequestDataAccessView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if not _table_exists(DataAccessRequest._meta.db_table):
            error_msg = "Funcao de solicitacao indisponivel. Rode as migracoes e tente novamente."
            if is_ajax:
                return JsonResponse({"ok": False, "error": error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

        has_open_request = DataAccessRequest.objects.filter(
            user=request.user,
            status__in=[DataAccessRequest.STATUS_PENDING, DataAccessRequest.STATUS_PROCESSING],
        ).exists()
        if has_open_request:
            warning_msg = "Voce ja possui uma solicitacao de dados em andamento."
            if is_ajax:
                return JsonResponse({"ok": False, "error": warning_msg}, status=400)
            messages.warning(request, warning_msg)
            return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

        form = DataAccessRequestForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            _process_data_access_request(instance)
            success_msg = "Solicitacao registrada e arquivo gerado com sucesso."
            if is_ajax:
                return JsonResponse({
                    "ok": True,
                    "message": success_msg,
                    "request": {
                        "id": instance.id,
                        "created_at": timezone.localtime(instance.data_solicitacao).strftime("%d/%m/%Y %H:%M"),
                        "status": instance.status,
                        "status_label": instance.get_status_display(),
                        "processed_at": (
                            timezone.localtime(instance.data_processamento).strftime("%d/%m/%Y %H:%M")
                            if instance.data_processamento else "-"
                        ),
                        "file_url": instance.arquivo_exportacao.url if instance.arquivo_exportacao else "",
                    },
                })
            messages.success(request, success_msg)
        else:
            error_msg = "Nao foi possivel registrar a solicitacao. Revise os dados."
            if is_ajax:
                return JsonResponse({"ok": False, "error": error_msg}, status=400)
            messages.error(request, error_msg)

        return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")


class LgpdUpdateConsentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if not _table_exists(UserConsentLog._meta.db_table):
            error_msg = "Modulo de consentimento indisponivel. Rode as migracoes e tente novamente."
            if is_ajax:
                return JsonResponse({"ok": False, "error": error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

        consent_type = (request.POST.get("consent_type") or "").strip()
        accepted = request.POST.get("accepted") in {"1", "true", "True", "on"}

        valid_types = {
            UserConsentLog.TYPE_TERMS,
            UserConsentLog.TYPE_PRIVACY,
            UserConsentLog.TYPE_COOKIES,
        }
        if consent_type not in valid_types:
            error_msg = "Tipo de consentimento invalido."
            if is_ajax:
                return JsonResponse({"ok": False, "error": error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

        latest_log = (
            UserConsentLog.objects
            .filter(user=request.user, consent_type=consent_type)
            .order_by("-timestamp")
            .first()
        )
        if latest_log and latest_log.accepted and accepted:
            already_msg = "Consentimento ja registrado como aceito."
            if is_ajax:
                return JsonResponse({
                    "ok": True,
                    "message": already_msg,
                    "consent_type": consent_type,
                    "accepted": True,
                    "document_version": latest_log.document_version,
                    "timestamp": latest_log.timestamp.isoformat(),
                    "timestamp_label": timezone.localtime(latest_log.timestamp).strftime("%d/%m/%Y %H:%M"),
                })
            messages.info(request, already_msg)
            return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

        document_version = "1.0"
        if consent_type in {UserConsentLog.TYPE_TERMS, UserConsentLog.TYPE_PRIVACY}:
            doc_type = "terms_of_service" if consent_type == UserConsentLog.TYPE_TERMS else "privacy_policy"
            active_doc = _get_active_document(doc_type)
            if active_doc and active_doc.versao:
                document_version = active_doc.versao

        consent_log = UserConsentLog.objects.create(
            user=request.user,
            consent_type=consent_type,
            accepted=accepted,
            document_version=document_version,
            source="lgpd_hub",
            ip_address=_resolve_client_ip(request),
            user_agent=(request.META.get("HTTP_USER_AGENT") or ""),
        )

        response_message = "Consentimento atualizado com sucesso."
        if consent_type in {UserConsentLog.TYPE_TERMS, UserConsentLog.TYPE_PRIVACY}:
            if accepted:
                response_message = "Consentimento atualizado com sucesso."
                messages.success(request, response_message)
            else:
                response_message = "Termos e politica sao obrigatorios para uso da plataforma."
                messages.warning(request, response_message)
        else:
            response_message = "Preferencia de cookies atualizada."
            messages.success(request, response_message)

        if is_ajax:
            return JsonResponse({
                "ok": True,
                "message": response_message,
                "consent_type": consent_type,
                "accepted": accepted,
                "document_version": document_version,
                "timestamp": consent_log.timestamp.isoformat(),
                "timestamp_label": timezone.localtime(consent_log.timestamp).strftime("%d/%m/%Y %H:%M"),
            })

        return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")


class LgpdRequestAccountDeletionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if not _table_exists(DataDeletionRequest._meta.db_table):
            error_msg = "Funcao de exclusao indisponivel. Rode as migracoes e tente novamente."
            if is_ajax:
                return JsonResponse({"ok": False, "error": error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

        _expire_pending_deletion_requests()

        has_open_request = DataDeletionRequest.objects.filter(
            user=request.user,
            status=DataDeletionRequest.STATUS_PENDING,
            data_expiracao__gte=timezone.now(),
        ).exists()
        if has_open_request:
            warning_msg = "Voce ja possui uma solicitacao de exclusao pendente."
            if is_ajax:
                return JsonResponse({"ok": False, "error": warning_msg}, status=400)
            messages.warning(request, warning_msg)
            return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

        if not request.user.email:
            error_msg = "Sua conta nao possui e-mail valido para confirmar a exclusao."
            if is_ajax:
                return JsonResponse({"ok": False, "error": error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

        motivo = (request.POST.get("motivo") or request.POST.get("motivo_exclusao") or "").strip()
        now = timezone.now()
        deletion_request = DataDeletionRequest.objects.create(
            user=request.user,
            motivo=motivo,
            confirm_token=uuid.uuid4().hex,
            data_expiracao=now + timedelta(hours=48),
        )

        try:
            _send_account_deletion_email(request, deletion_request)
        except Exception as exc:
            deletion_request.status = DataDeletionRequest.STATUS_CANCELED
            deletion_request.data_cancelamento = timezone.now()
            deletion_request.save(update_fields=["status", "data_cancelamento"])
            error_msg = f"Nao foi possivel enviar o e-mail de confirmacao ({exc})."
            if is_ajax:
                return JsonResponse({"ok": False, "error": error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

        success_msg = "Solicitacao registrada. Enviamos um e-mail para confirmar a exclusao em ate 48 horas."
        if is_ajax:
            return JsonResponse({
                "ok": True,
                "message": success_msg,
                "request": {
                    "id": deletion_request.id,
                    "created_at": timezone.localtime(deletion_request.data_solicitacao).strftime("%d/%m/%Y %H:%M"),
                    "status": deletion_request.status,
                    "status_label": deletion_request.get_status_display(),
                    "expires_at": timezone.localtime(deletion_request.data_expiracao).strftime("%d/%m/%Y %H:%M"),
                },
            })

        messages.success(request, success_msg)
        return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")


class LgpdCancelAccountDeletionView(LoginRequiredMixin, View):
    def post(self, request, request_id, *args, **kwargs):
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if not _table_exists(DataDeletionRequest._meta.db_table):
            error_msg = "Funcao de cancelamento indisponivel."
            if is_ajax:
                return JsonResponse({"ok": False, "error": error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

        _expire_pending_deletion_requests()
        deletion_request = DataDeletionRequest.objects.filter(id=request_id, user=request.user).first()
        if not deletion_request:
            error_msg = "Solicitacao nao encontrada."
            if is_ajax:
                return JsonResponse({"ok": False, "error": error_msg}, status=404)
            messages.error(request, error_msg)
            return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

        if deletion_request.status != DataDeletionRequest.STATUS_PENDING:
            error_msg = "Apenas solicitacoes pendentes podem ser canceladas."
            if is_ajax:
                return JsonResponse({"ok": False, "error": error_msg}, status=400)
            messages.warning(request, error_msg)
            return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

        if deletion_request.data_expiracao < timezone.now():
            deletion_request.status = DataDeletionRequest.STATUS_EXPIRED
            deletion_request.save(update_fields=["status"])
            error_msg = "O prazo de cancelamento expirou."
            if is_ajax:
                return JsonResponse({"ok": False, "error": error_msg}, status=400)
            messages.warning(request, error_msg)
            return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")

        deletion_request.status = DataDeletionRequest.STATUS_CANCELED
        deletion_request.data_cancelamento = timezone.now()
        deletion_request.save(update_fields=["status", "data_cancelamento"])

        success_msg = "Solicitacao de exclusao cancelada com sucesso."
        if is_ajax:
            return JsonResponse({"ok": True, "message": success_msg, "request_id": deletion_request.id})

        messages.success(request, success_msg)
        return redirect(f"{reverse('lgpd_hub')}?tab=meus-dados")


class LgpdConfirmAccountDeletionView(View):
    def get(self, request, token, *args, **kwargs):
        if not _table_exists(DataDeletionRequest._meta.db_table):
            messages.error(request, "Funcao de exclusao indisponivel.")
            return redirect("home")

        _expire_pending_deletion_requests()
        deletion_request = DataDeletionRequest.objects.filter(confirm_token=token).select_related("user").first()

        if not deletion_request:
            messages.error(request, "Link de confirmacao invalido ou inexistente.")
            return redirect("home")

        if deletion_request.status != DataDeletionRequest.STATUS_PENDING:
            messages.warning(request, "Esta solicitacao ja foi processada ou cancelada.")
            return redirect("home")

        if deletion_request.data_expiracao < timezone.now():
            deletion_request.status = DataDeletionRequest.STATUS_EXPIRED
            deletion_request.save(update_fields=["status"])
            messages.warning(request, "O link de confirmacao expirou apos 48 horas.")
            return redirect("home")

        user = deletion_request.user
        deletion_request.status = DataDeletionRequest.STATUS_COMPLETED
        deletion_request.data_confirmacao = timezone.now()
        deletion_request.data_processamento = timezone.now()
        deletion_request.save(update_fields=["status", "data_confirmacao", "data_processamento"])

        _anonymize_user_account(user)

        if request.user.is_authenticated and request.user.id == user.id:
            logout(request)

        messages.success(request, "Conta excluida com sucesso.")
        return redirect("home")