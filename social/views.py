import os
import json
import redis
import logging
from urllib.parse import urlparse
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Prefetch

from .models import Comment, Conversa, LikeAtividade, LikeComment, LikePost, Mensagem, Post, Atividade
from .forms import MensagemForm
from .utils.image_moderation import analisar_imagem
from .security import throttle_request

# Configuração de Log para ver o erro no terminal
logger = logging.getLogger(__name__)

# Garante a URL do Redis correta para o Docker
REDIS_URL = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')


def _is_allowed_gif_url(url_value):
    value = (url_value or '').strip()
    if not value:
        return True

    try:
        parsed = urlparse(value)
    except Exception:
        return False

    if parsed.scheme not in {'http', 'https'}:
        return False

    if not parsed.netloc:
        return False

    # Bloqueia userinfo em URL para evitar ambiguidades do tipo user@host.
    if parsed.username or parsed.password:
        return False

    host = (parsed.hostname or '').lower()
    allowed_hosts = tuple(getattr(settings, 'SOCIAL_ALLOWED_GIF_HOSTS', ()) or ())
    if not allowed_hosts:
        return False

    return any(host == allowed or host.endswith(f'.{allowed}') for allowed in allowed_hosts)


def _validate_uploaded_image(uploaded_file):
    if not uploaded_file:
        return True, None

    max_bytes = int(getattr(settings, 'SOCIAL_IMAGE_MAX_UPLOAD_BYTES', 5 * 1024 * 1024) or 5 * 1024 * 1024)
    allowed_mimes = set(getattr(settings, 'SOCIAL_ALLOWED_IMAGE_MIME_TYPES', ()) or ())

    if uploaded_file.size and uploaded_file.size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        return False, f'Imagem muito grande (máx. {max_mb:.0f} MB).'

    content_type = (getattr(uploaded_file, 'content_type', '') or '').lower().strip()
    if not content_type or content_type not in allowed_mimes:
        return False, 'Formato de imagem não permitido.'

    return True, None


def _is_friend(user_a, user_b):
    try:
        return user_a.perfil.amigos.filter(id=user_b.id).exists()
    except Exception:
        return False


def _can_view_post(user, post):
    if post.autor_id == user.id:
        return True
    if post.visibilidade == Post.VIS_PUBLICO:
        return True
    return _is_friend(user, post.autor)


def _can_interact_post(user, post):
    return _can_view_post(user, post)


def _serialize_comment(comment, request_user):
    autor_foto = comment.autor.perfil.foto.url if hasattr(comment.autor, 'perfil') and comment.autor.perfil.foto else None
    return {
        'id': comment.id,
        'conteudo': comment.conteudo_plano,
        'imagem': comment.imagem.url if comment.imagem else None,
        'gif_url': comment.gif_url,
        'criado_em': comment.criado_em.isoformat(),
        'likes_count': comment.likes.count(),
        'usuario_like': comment.likes.filter(usuario=request_user).exists(),
        'pode_deletar': comment.autor_id == request_user.id,
        'fixado': getattr(comment, 'fixado', False),
        'autor': {
            'id': comment.autor_id,
            'username': comment.autor.username,
            'foto': autor_foto,
        },
    }


def _serialize_post(post, request_user):
    autor_foto = post.autor.perfil.foto.url if hasattr(post.autor, 'perfil') and post.autor.perfil.foto else None
    comentarios = [_serialize_comment(c, request_user) for c in post.comentarios.all()[:20]]
    return {
        'id': post.id,
        'conteudo': post.conteudo_plano,
        'imagem': post.imagem.url if post.imagem else None,
        'gif_url': post.gif_url,
        'fixado': getattr(post, 'fixado', False),
        'visibilidade': post.visibilidade,
        'criado_em': post.criado_em.isoformat(),
        'likes_count': post.likes.count(),
        'comentarios_count': post.comentarios.count(),
        'usuario_like': post.likes.filter(usuario=request_user).exists(),
        'pode_deletar': post.autor_id == request_user.id,
        'autor': {
            'id': post.autor_id,
            'username': post.autor.username,
            'nome_exibicao': post.autor.username,
            'foto': autor_foto,
        },
        'comentarios': comentarios,
    }


def _build_posts_queryset(request_user, filtro):
    base = Post.objects.select_related('autor', 'autor__perfil').prefetch_related(
        'likes',
        Prefetch('comentarios', queryset=Comment.objects.select_related('autor', 'autor__perfil').prefetch_related('likes').order_by('criado_em')),
    ).order_by('-criado_em')

    if filtro == 'meu':
        return base.filter(autor=request_user)

    if filtro.startswith('usuario_'):
        target_id = filtro.split('usuario_', 1)[1]
        if not target_id.isdigit():
            return base.none()
        target_user = User.objects.filter(id=int(target_id)).first()
        if not target_user:
            return base.none()
        if target_user.id == request_user.id:
            return base.filter(autor_id=target_user.id)
        if _is_friend(request_user, target_user):
            return base.filter(autor_id=target_user.id)
        return base.filter(autor_id=target_user.id, visibilidade=Post.VIS_PUBLICO)

    friend_ids = list(request_user.perfil.amigos.values_list('id', flat=True)) if hasattr(request_user, 'perfil') else []
    return base.filter(
        Q(autor=request_user)
        | Q(visibilidade=Post.VIS_PUBLICO)
        | Q(autor_id__in=friend_ids, visibilidade=Post.VIS_AMIGOS)
    )


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default

class ConversaView(LoginRequiredMixin, View):
    def get(self, request, username):
        outro_usuario = get_object_or_404(User, username=username)
        
        # Busca ou cria conversa
        conversa = Conversa.objects.filter(participantes=request.user).filter(participantes=outro_usuario).first()
        
        mensagens = []
        if conversa:
            mensagens = conversa.mensagens.all().order_by('timestamp')

        form = MensagemForm()

        # Sidebar ordenada pela data da última mensagem
        try:
            conversas_qs = Conversa.objects.filter(participantes=request.user).order_by('-ultima_mensagem_data')
        except Exception:
            # Fallback se a migração não tiver sido feita corretamente
            conversas_qs = Conversa.objects.filter(participantes=request.user)

        conversas_usuario = []
        for c in conversas_qs:
            outro = c.participantes.exclude(id=request.user.id).first()
            if outro:
                conversas_usuario.append({
                    "outro": outro,
                    "ultima_mensagem": c.mensagens.last(),
                })

        context = {
            "outro_usuario": outro_usuario,
            "mensagens": mensagens,
            "form": form,
            "conversas_usuario": conversas_usuario,
        }
        return render(request, "social/conversa.html", context)

@login_required
def enviar_mensagem(request, username):
    """
    API que recebe a mensagem, salva no Postgres e avisa o Redis.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método inválido"}, status=405)

    conteudo = request.POST.get("conteudo", "").strip()
    imagem = request.FILES.get("imagem")

    if not conteudo and not imagem:
        return JsonResponse({"error": "Mensagem vazia"}, status=400)

    outro_usuario = get_object_or_404(User, username=username)
    if outro_usuario.id == request.user.id:
        return JsonResponse({'error': 'Destino inválido'}, status=400)

    if not _is_friend(request.user, outro_usuario):
        return JsonResponse({'error': 'Você só pode conversar com amigos.'}, status=403)

    allowed, _ = throttle_request(request, scope='chat_send', limit=30, window_seconds=60)
    if not allowed:
        return JsonResponse({'error': 'Muitas mensagens em pouco tempo. Aguarde um instante.'}, status=429)

    # 1. BANCO DE DADOS (Postgres)
    try:
        conversa = Conversa.objects.filter(participantes=request.user).filter(participantes=outro_usuario).first()
        if not conversa:
            conversa = Conversa.objects.create()
            conversa.participantes.add(request.user, outro_usuario)

        # Salva a mensagem
        mensagem = Mensagem.objects.create(
            conversa=conversa,
            remetente=request.user,
            conteudo=conteudo,
            imagem=imagem if imagem else None,
        )
        
        # Atualiza data da conversa
        conversa.ultima_mensagem_data = timezone.now()
        conversa.save()
        
        print(f"✅ [Django] Mensagem {mensagem.id} salva no Banco.")

    except Exception as e:
        logger.exception('Erro ao salvar mensagem no banco')
        return JsonResponse({'error': 'Falha interna ao enviar mensagem.'}, status=500)

    # 2. REAL-TIME (Redis) - DIAGNÓSTICO
    try:
        timestamp_local = mensagem.timestamp.astimezone(timezone.get_current_timezone()).strftime("%H:%M")
        
        user_avatar = ""
        if hasattr(mensagem.remetente, "perfil") and mensagem.remetente.perfil.foto:
            user_avatar = mensagem.remetente.perfil.foto.url

        data_msg = {
            "type": "chat_message",
            "message": mensagem.conteudo or "",
            "username": mensagem.remetente.username,
            "user_avatar_url": user_avatar,
            "timestamp": timestamp_local,
            "image_url": mensagem.imagem.url if mensagem.imagem else None,
        }

        # Conexão
        # OBS: Se estiver imprimindo 'redis://redis:6379/0', está certo para Docker.
        print(f"🔌 [Django] Conectando Redis em: {REDIS_URL}")
        r = redis.from_url(REDIS_URL)
        
        # Nomes
        u1 = request.user.username.lower().strip()
        u2 = outro_usuario.username.lower().strip()
        
        room_members = sorted([u1, u2])
        group_name = f"chat_{'_'.join(room_members)}"
        
        # Publica e pega o NÚMERO DE RECEBEDORES
        recebedores = r.publish(group_name, json.dumps(data_msg))
        
        print(f"📡 [Django PUBLISH] Canal: '{group_name}' | Recebedores: {recebedores}")
        
        if recebedores == 0:
            print("⚠️ [ALERTA] Ninguém escutou! O FastAPI não está inscrito neste canal.")
            print("   -> Verifique se o FastAPI conectou no Redis.")
            print("   -> Verifique se o nome do canal no FastAPI é EXATAMENTE igual.")

    except Exception as e:
        print(f"❌ [Django ERRO REDIS] {e}")

    return JsonResponse({
        "success": True, 
        "message": "Enviada",
        "msg_id": mensagem.id
    })


@login_required
@require_GET
def listar_posts(request):
    filtro = (request.GET.get('filtro') or 'todos').strip()
    limite = max(1, min(_safe_int(request.GET.get('limite', 20), default=20), 40))
    offset = max(0, _safe_int(request.GET.get('offset', 0), default=0))

    queryset = _build_posts_queryset(request.user, filtro)
    posts = list(queryset[offset:offset + limite])
    return JsonResponse({'success': True, 'posts': [_serialize_post(p, request.user) for p in posts]})


@login_required
@require_POST
def criar_post(request):
    allowed, _ = throttle_request(request, scope='post_create', limit=10, window_seconds=60)
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Muitas publicações em pouco tempo.'}, status=429)

    conteudo = (request.POST.get('conteudo') or '').strip()
    visibilidade = (request.POST.get('visibilidade') or Post.VIS_PUBLICO).strip()
    imagem = request.FILES.get('imagem')
    gif_url = (request.POST.get('gif_url') or '').strip()

    image_ok, image_error = _validate_uploaded_image(imagem)
    if not image_ok:
        return JsonResponse({'success': False, 'error': image_error}, status=400)

    if visibilidade not in {Post.VIS_PUBLICO, Post.VIS_AMIGOS}:
        return JsonResponse({'success': False, 'error': 'Visibilidade inválida.'}, status=400)

    if not _is_allowed_gif_url(gif_url):
        return JsonResponse({'success': False, 'error': 'GIF inválido.'}, status=400)

    if not conteudo and not imagem and not gif_url:
        return JsonResponse({'success': False, 'error': 'Post vazio.'}, status=400)

    if len(conteudo) > 500:
        return JsonResponse({'success': False, 'error': 'Texto muito longo (máx. 500 caracteres).'}, status=400)

    post = Post(
        autor=request.user,
        visibilidade=visibilidade,
        imagem=imagem if imagem else None,
        gif_url=gif_url or None,
    )
    post.definir_conteudo(conteudo)
    post.save()

    if imagem:
        try:
            is_safe, _ = analisar_imagem(post.imagem.path)
            if not is_safe:
                post.imagem.delete(save=False)
                post.delete()
                return JsonResponse({'success': False, 'error': 'Imagem recusada por segurança.'}, status=400)
        except Exception:
            # Fail-closed: sem validação de segurança válida, não publica a imagem.
            post.imagem.delete(save=False)
            post.delete()
            logger.exception('Falha ao analisar imagem do post')
            return JsonResponse({'success': False, 'error': 'Não foi possível validar a imagem.'}, status=503)

    return JsonResponse({'success': True, 'post': _serialize_post(post, request.user)})


@login_required
@require_POST
def toggle_like_post(request, post_id):
    allowed, _ = throttle_request(request, scope='post_like', limit=80, window_seconds=60)
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Muitas ações de curtida.'}, status=429)

    post = get_object_or_404(Post, id=post_id)
    if not _can_interact_post(request.user, post):
        return JsonResponse({'success': False, 'error': 'Acesso negado.'}, status=403)

    like, created = LikePost.objects.get_or_create(post=post, usuario=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({'success': True, 'liked': liked, 'likes_count': post.likes.count()})


@login_required
@require_POST
def comentar_post(request, post_id):
    allowed, _ = throttle_request(request, scope='comment_create', limit=30, window_seconds=60)
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Muitos comentários em pouco tempo.'}, status=429)

    post = get_object_or_404(Post, id=post_id)
    if not _can_interact_post(request.user, post):
        return JsonResponse({'success': False, 'error': 'Acesso negado.'}, status=403)

    conteudo = (request.POST.get('conteudo') or '').strip()
    imagem = request.FILES.get('imagem')
    gif_url = (request.POST.get('gif_url') or '').strip()

    image_ok, image_error = _validate_uploaded_image(imagem)
    if not image_ok:
        return JsonResponse({'success': False, 'error': image_error}, status=400)

    if not conteudo and not imagem and not gif_url:
        return JsonResponse({'success': False, 'error': 'Comentário vazio.'}, status=400)

    if len(conteudo) > 300:
        return JsonResponse({'success': False, 'error': 'Comentário muito longo (máx. 300).'}, status=400)

    if not _is_allowed_gif_url(gif_url):
        return JsonResponse({'success': False, 'error': 'GIF inválido.'}, status=400)

    comment = Comment(post=post, autor=request.user, imagem=imagem if imagem else None, gif_url=gif_url or None)
    comment.definir_conteudo(conteudo)
    comment.save()

    if imagem:
        try:
            is_safe, _ = analisar_imagem(comment.imagem.path)
            if not is_safe:
                comment.imagem.delete(save=False)
                comment.delete()
                return JsonResponse({'success': False, 'error': 'Imagem recusada por segurança.'}, status=400)
        except Exception:
            # Fail-closed: sem validação de segurança válida, não publica a imagem.
            comment.imagem.delete(save=False)
            comment.delete()
            logger.exception('Falha ao analisar imagem do comentário')
            return JsonResponse({'success': False, 'error': 'Não foi possível validar a imagem.'}, status=503)

    return JsonResponse({'success': True, 'comment': _serialize_comment(comment, request.user)})


@login_required
@require_POST
def toggle_like_comentario(request, comentario_id):
    allowed, _ = throttle_request(request, scope='comment_like', limit=100, window_seconds=60)
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Muitas ações de curtida.'}, status=429)

    comment = get_object_or_404(Comment.objects.select_related('post', 'post__autor'), id=comentario_id)
    if not _can_interact_post(request.user, comment.post):
        return JsonResponse({'success': False, 'error': 'Acesso negado.'}, status=403)

    like, created = LikeComment.objects.get_or_create(comment=comment, usuario=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({'success': True, 'liked': liked, 'likes_count': comment.likes.count()})


@login_required
@require_POST
def deletar_comentario(request, comentario_id):
    comment = get_object_or_404(Comment, id=comentario_id)
    if comment.autor_id != request.user.id:
        return JsonResponse({'success': False, 'error': 'Acesso negado.'}, status=403)
    comment.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def deletar_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.autor_id != request.user.id:
        return JsonResponse({'success': False, 'error': 'Acesso negado.'}, status=403)
    post.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def atualizar_visibilidade_post(request, post_id):
    allowed, _ = throttle_request(request, scope='post_visibility', limit=40, window_seconds=60)
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Muitas alterações em pouco tempo.'}, status=429)

    post = get_object_or_404(Post, id=post_id)
    if post.autor_id != request.user.id:
        return JsonResponse({'success': False, 'error': 'Acesso negado.'}, status=403)

    visibilidade = (request.POST.get('visibilidade') or '').strip()
    if visibilidade not in {Post.VIS_PUBLICO, Post.VIS_AMIGOS}:
        return JsonResponse({'success': False, 'error': 'Visibilidade inválida.'}, status=400)

    post.visibilidade = visibilidade
    post.save(update_fields=['visibilidade', 'atualizado_em'])
    return JsonResponse({'success': True, 'visibilidade': post.visibilidade})


@login_required
@require_POST
def toggle_fixar_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.autor_id != request.user.id:
        return JsonResponse({'success': False, 'error': 'Acesso negado.'}, status=403)

    post.fixado = not post.fixado
    post.save(update_fields=['fixado', 'atualizado_em'])
    return JsonResponse({
        'success': True,
        'fixado': post.fixado,
        'message': 'Post fixado!' if post.fixado else 'Post desafixado!',
    })


@login_required
@require_POST
def toggle_fixar_comentario(request, comentario_id):
    """
    Toggle para fixar/desafixar um comentário.
    Apenas o autor do post pode fixar comentários.
    """
    comment = get_object_or_404(Comment, id=comentario_id)
    post = comment.post
    
    # Apenas o autor do POST pode fixar comentários
    if post.autor_id != request.user.id:
        return JsonResponse({'success': False, 'error': 'Acesso negado.'}, status=403)
    
    # Toggle fixado
    comment.fixado = not comment.fixado
    comment.save(update_fields=['fixado', 'atualizado_em'])
    
    return JsonResponse({
        'success': True,
        'fixado': comment.fixado,
        'message': 'Fixado!' if comment.fixado else 'Desafixado!'
    })


@login_required
@require_POST
def toggle_like_atividade(request, atividade_id):
    """
    API para curtir/descurtir uma atividade.
    """
    atividade = get_object_or_404(Atividade, id=atividade_id)
    
    allowed, _ = throttle_request(request, scope='atividade_like', limit=80, window_seconds=60)
    if not allowed:
        return JsonResponse({'success': False, 'error': 'Muitas ações de curtida.'}, status=429)

    like, created = LikeAtividade.objects.get_or_create(
        atividade=atividade,
        usuario=request.user
    )
    
    if not created:
        # Se já existia, deleta (unlike)
        like.delete()
        liked = False
    else:
        liked = True
    
    like_count = atividade.likes.count()
    
    return JsonResponse({
        "success": True,
        "liked": liked,
        "like_count": like_count,
        "cta_label": "Curtido" if liked else "Curtir",
    })