/* ======= Helper: pega csrftoken do cookie ======= */
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function escapeHtml(value) {
    const div = document.createElement('div');
    div.innerText = value == null ? '' : String(value);
    return div.innerHTML;
}

function sanitizeHttpUrl(value, options = {}) {
    const allowRelative = options.allowRelative === true;
    const fallback = Object.prototype.hasOwnProperty.call(options, 'fallback') ? options.fallback : '';
    const raw = String(value == null ? '' : value).trim();

    if (!raw) return fallback;

    if (allowRelative && raw.startsWith('/') && !raw.startsWith('//')) {
        return raw;
    }

    try {
        const parsed = new URL(raw, window.location.origin);
        if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
            return fallback;
        }
        return parsed.href;
    } catch (_) {
        return fallback;
    }
}

function sanitizeInternalUrl(value, fallback = '#') {
    const raw = String(value == null ? '' : value).trim();
    if (!raw) return fallback;

    if (raw.startsWith('/') && !raw.startsWith('//')) {
        return raw;
    }

    try {
        const parsed = new URL(raw, window.location.origin);
        if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
            return fallback;
        }
        if (parsed.origin !== window.location.origin) {
            return fallback;
        }
        return `${parsed.pathname}${parsed.search}${parsed.hash}`;
    } catch (_) {
        return fallback;
    }
}

function toastMeta(kind) {
    if (kind === 'success') return { title: 'Sucesso!', icon: 'bi-check-circle-fill', css: 'is-success' };
    if (kind === 'error') return { title: 'Erro!', icon: 'bi-x-octagon-fill', css: 'is-error' };
    if (kind === 'warning') return { title: 'Atenção!', icon: 'bi-exclamation-triangle-fill', css: 'is-warning' };
    return { title: 'Aviso', icon: 'bi-info-circle-fill', css: 'is-info' };
}

function resolveRealtimeToastKind(data) {
    const text = `${data?.titulo || ''} ${data?.mensagem || ''}`.toLowerCase();
    if (text.includes('aceitou') || text.includes('confirmad') || text.includes('entrou')) return 'success';
    if (text.includes('recus') || text.includes('cancel') || text.includes('saiu')) return 'warning';
    if (text.includes('erro') || text.includes('falha')) return 'error';
    return 'info';
}

function showToast(kind, text, delayMs = 5000) {
    const stack = document.getElementById('toast-stack');
    if (!stack || !window.bootstrap) return;

    const meta = toastMeta(kind);
    const wrapper = document.createElement('div');
    wrapper.className = `toast esportefy-toast ${meta.css}`;
    wrapper.setAttribute('role', 'alert');
    wrapper.setAttribute('aria-live', 'assertive');
    wrapper.setAttribute('aria-atomic', 'true');
    wrapper.setAttribute('data-bs-delay', String(delayMs));
    wrapper.innerHTML = `
        <div class="toast-header">
            <i class="bi ${meta.icon} me-2"></i>
            <strong class="me-auto">${meta.title}</strong>
            <small class="text-white-50">agora</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">${escapeHtml(text)}</div>
    `;

    stack.prepend(wrapper);
    const instance = new bootstrap.Toast(wrapper);
    instance.show();
}

function dismissAllToasts() {
    if (!window.bootstrap) return;
    const toastNodes = document.querySelectorAll('.toast.esportefy-toast');
    toastNodes.forEach((toastNode) => {
        const instance = bootstrap.Toast.getInstance(toastNode) || new bootstrap.Toast(toastNode);
        instance.hide();
    });
}

function playNotificationSound() {
    const audio = document.getElementById('notification-audio');
    if (!audio) return;
    try {
        audio.volume = 0.22;
        audio.currentTime = 0;
        const promise = audio.play();
        if (promise && typeof promise.then === 'function') {
            promise.then(() => {
                window.esportefyPendingSuccessSound = false;
            }).catch(() => {
                // Navegador bloqueou autoplay; guarda para tocar após desbloqueio por interação
                window.esportefyPendingSuccessSound = true;
            });
        }
    } catch (_) {}
}

function setFeedSection(sectionKey) {
    const feedBase = window.location.pathname.replace(/\/$/, '');
    const expectedFeed = '/feed';
    if (!feedBase.startsWith(expectedFeed)) return;

    // Aplica comportamento em qualquer largura: cada aba mostra apenas sua seção.
    const mapping = {
        feed: ['feed-atividades', 'feed-partidas', 'feed-noticias'],
        partidas: ['feed-partidas'],
        noticias: ['feed-noticias'],
    };

    const allSections = ['feed-atividades', 'feed-partidas', 'feed-noticias'];
    const toShow = mapping[sectionKey] || allSections;

    allSections.forEach((id) => {
        const el = document.getElementById(id);
        if (!el) return;

        const sectionWrapper = el.closest('section, div');

        const hide = sectionKey !== 'feed' && !toShow.includes(id);

        el.classList.toggle('d-none', hide);
        if (sectionWrapper) {
            sectionWrapper.classList.toggle('d-none', hide);
        }

        // fallback: caso parent ainda contenha elementos, controlar via inline display
        if (sectionWrapper && sectionWrapper.classList.contains('d-none')) {
            sectionWrapper.style.display = 'none';
        } else if (sectionWrapper) {
            sectionWrapper.style.display = '';
        }
    });

    const navItems = document.querySelectorAll('.mobile-bottom-nav .nav-item');
    navItems.forEach((item) => {
        const itemKey = item.dataset.nav;
        if (!itemKey) return;
        if (sectionKey === 'feed') {
            item.classList.toggle('active', itemKey === 'feed');
        } else {
            item.classList.toggle('active', itemKey === sectionKey);
        }
    });
}

function updateFeedSectionFromHash() {
    const hash = window.location.hash || '#feed-atividades';
    if (hash === '#feed-partidas') {
        setFeedSection('partidas');
    } else if (hash === '#feed-noticias') {
        setFeedSection('noticias');
    } else if (hash === '#feed-atividades') {
        setFeedSection('feed');
    }
}

function unlockNotificationAudio() {
    const audio = document.getElementById('notification-audio');
    if (!audio || window.esportefyAudioUnlocked) return;

    try {
        audio.muted = true;
        const promise = audio.play();
        if (promise && typeof promise.then === 'function') {
            promise.then(() => {
                audio.pause();
                audio.currentTime = 0;
                audio.muted = false;
                window.esportefyAudioUnlocked = true;

                if (window.esportefyPendingSuccessSound) {
                    setTimeout(() => playNotificationSound(), 120);
                }
            }).catch(() => {
                audio.muted = false;
            });
        }
    } catch (_) {
        audio.muted = false;
    }
}

function triggerPopupTeste() {
    const tests = [
        { type: 'info', msg: 'João aceitou seu pedido de amizade!', time: 100 },
        { type: 'success', msg: 'Sua partida Futebol de Sexta foi criada com sucesso!', time: 1600 },
        { type: 'warning', msg: 'Atenção: A partida de Tênis de amanhã foi cancelada pelo organizador.', time: 3100 },
        { type: 'error', msg: 'Não foi possível exportar seus dados LGPD. Tente novamente.', time: 4600 },
        { type: 'info', msg: 'Você tem uma nova mensagem de contatozinho123.', time: 6100 }
    ];
    
    tests.forEach(test => {
        setTimeout(() => {
            showToast(test.type, test.msg, 6000);
            playNotificationSound();
        }, test.time);
    });
}

const HIDDEN_FRIEND_REQUESTS_KEY = 'esportefy_hidden_friend_request_notifications';
const NOTIFICATION_HISTORY_PREFIX = 'esportefy_notification_history_';

function notificationHistoryKey(userId) {
    return `${NOTIFICATION_HISTORY_PREFIX}${String(userId || '')}`;
}

function loadNotificationHistory(userId) {
    if (!userId) return [];
    try {
        const raw = localStorage.getItem(notificationHistoryKey(userId));
        if (!raw) return [];
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed.map(normalizeNotificationHistoryItem) : [];
    } catch (_) {
        return [];
    }
}

function resolveNotificationDate(...rawValues) {
    for (const raw of rawValues) {
        if (!raw) continue;
        const parsed = new Date(raw);
        if (!Number.isNaN(parsed.getTime())) {
            return parsed;
        }
    }
    return new Date();
}

function formatRelativeNotificationTime(dateValue) {
    const now = Date.now();
    const target = dateValue instanceof Date ? dateValue.getTime() : new Date(dateValue).getTime();
    if (Number.isNaN(target)) return 'agora';

    const diffSeconds = Math.max(0, Math.floor((now - target) / 1000));
    if (diffSeconds < 60) return 'agora';

    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) return `ha ${diffMinutes} min`;

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `ha ${diffHours} h`;

    const diffDays = Math.floor(diffHours / 24);
    return `ha ${diffDays} d`;
}

function normalizeNotificationHistoryItem(item) {
    if (!item || typeof item !== 'object') return item;
    const timestampIso = item.timestamp_iso || item.timestampIso || null;
    const resolvedDate = resolveNotificationDate(timestampIso, item.timestamp);

    return {
        ...item,
        timestamp_iso: resolvedDate.toISOString(),
    };
}

function saveNotificationHistory(userId, items) {
    if (!userId) return;
    try {
        localStorage.setItem(notificationHistoryKey(userId), JSON.stringify(items));
    } catch (_) {}
}

function appendNotificationHistoryItem(userId, item) {
    if (!userId || !item) return;
    const items = loadNotificationHistory(userId);
    items.unshift(normalizeNotificationHistoryItem(item));
    saveNotificationHistory(userId, items.slice(0, 60));
}

function removeNotificationHistoryItem(userId, notificationId) {
    if (!userId || !notificationId) return;
    const filtered = loadNotificationHistory(userId).filter((item) => item.notificationId !== notificationId);
    saveNotificationHistory(userId, filtered);
}

function clearNotificationHistory(userId) {
    if (!userId) return;
    saveNotificationHistory(userId, []);
}

function buildRealtimeNotificationContent(entry) {
    const remetente = escapeHtml(entry.remetente || 'Contato');
    const mensagem = escapeHtml(entry.mensagem || 'Nova notificação recebida.');
    const avatarUrl = sanitizeHttpUrl(entry.foto_url, { allowRelative: true, fallback: '' });
    const freshAvatarUrl = avatarUrl
        ? `${avatarUrl}${avatarUrl.includes('?') ? '&' : '?'}v=${Date.now()}`
        : '';
    const avatar = freshAvatarUrl
        ? `<img src="${freshAvatarUrl}" class="rounded-circle" width="40" height="40" style="object-fit: cover;">`
        : `<div class="bg-secondary rounded-circle d-flex align-items-center justify-content-center text-white" style="width: 40px; height: 40px;">${remetente.charAt(0).toUpperCase()}</div>`;

    const link = sanitizeInternalUrl(entry.conversa_url, '#');
    const receivedAt = resolveNotificationDate(entry.timestamp_iso, entry.timestampIso, entry.timestamp);
    const timestamp = escapeHtml(formatRelativeNotificationTime(receivedAt));

    return `
        <div class="rt-notification">
            <a href="${link}" class="rt-notification__link d-flex align-items-center text-decoration-none text-light gap-2 p-2 border-bottom border-secondary-subtle">
                <div class="flex-shrink-0">
                    ${avatar}
                </div>
                <div class="flex-grow-1 overflow-hidden">
                    <div class="d-flex justify-content-between align-items-center gap-2">
                        <h6 class="mb-0 fw-bold text-truncate rt-notification__sender" style="font-size: 0.9rem;">${remetente}</h6>
                        <small class="text-secondary rt-notification__time" style="font-size: 0.7rem;">${timestamp}</small>
                    </div>
                    <p class="mb-0 text-secondary small rt-notification__message">${mensagem}</p>
                </div>
            </a>
            <button type="button" class="rt-notification__toggle" aria-expanded="false" aria-label="Expandir notificação">
                <i class="bi bi-chevron-down"></i>
            </button>
        </div>
    `;
}

document.addEventListener('click', (event) => {
    const toggleBtn = event.target.closest('.rt-notification__toggle');
    if (!toggleBtn) return;

    event.preventDefault();
    event.stopPropagation();

    const wrapper = toggleBtn.closest('.notificacao-item');
    if (!wrapper) return;

    const expanded = wrapper.classList.toggle('is-expanded');
    toggleBtn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    toggleBtn.setAttribute('aria-label', expanded ? 'Recolher notificação' : 'Expandir notificação');

    const icon = toggleBtn.querySelector('i');
    if (icon) {
        icon.classList.toggle('bi-chevron-up', expanded);
        icon.classList.toggle('bi-chevron-down', !expanded);
    }
});

function prependRealtimeNotificationToLists(notificationId, contentHtml) {
    const listas = getNotificationLists();
    if (!listas.length) return;

    listas.forEach((lista) => {
        const item = document.createElement('div');
        item.classList.add('notificacao-item');
        item.dataset.notificationId = notificationId;
        item.innerHTML = `
            <button type="button" class="btn-close-notificacao" aria-label="Excluir notificação" onclick="event.preventDefault(); event.stopPropagation(); dismissNotificationById('${notificationId}')">
                <i class="bi bi-x-lg"></i>
            </button>
            ${contentHtml}
        `;
        lista.prepend(item);
    });

    syncNotificationPlaceholder();
}

function renderStoredNotificationHistory(userId) {
    const history = loadNotificationHistory(userId);
    if (!history.length) return;

    history.slice().reverse().forEach((entry) => {
        const html = buildRealtimeNotificationContent(entry);
        prependRealtimeNotificationToLists(entry.notificationId, html);
    });
}

function loadHiddenFriendRequestIds() {
    try {
        const raw = localStorage.getItem(HIDDEN_FRIEND_REQUESTS_KEY);
        if (!raw) return new Set();
        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed)) return new Set();
        return new Set(parsed.map((id) => String(id)));
    } catch (_) {
        return new Set();
    }
}

let hiddenFriendRequestIds = loadHiddenFriendRequestIds();

function persistHiddenFriendRequestIds() {
    try {
        localStorage.setItem(HIDDEN_FRIEND_REQUESTS_KEY, JSON.stringify(Array.from(hiddenFriendRequestIds)));
    } catch (_) {}
}

function removeNotificationItemById(notificationId) {
    if (!notificationId) return;
    const nodes = document.querySelectorAll(`.notificacao-item[data-notification-id="${notificationId}"]`);
    nodes.forEach((node) => node.remove());
    syncNotificationPlaceholder();
}

function dismissNotificationById(notificationId) {
    removeNotificationHistoryItem(window.esportefyCurrentUserId, notificationId);
    removeNotificationItemById(notificationId);
}

function collapseExpandedNotifications() {
    document.querySelectorAll('.notificacao-item.is-expanded').forEach((item) => {
        item.classList.remove('is-expanded');
    });

    document.querySelectorAll('.rt-notification__toggle').forEach((btn) => {
        btn.setAttribute('aria-expanded', 'false');
        btn.setAttribute('aria-label', 'Expandir notificação');
        const icon = btn.querySelector('i');
        if (icon) {
            icon.classList.add('bi-chevron-down');
            icon.classList.remove('bi-chevron-up');
        }
    });
}

function dismissFriendNotification(solicitacaoId) {
    const key = String(solicitacaoId);
    hiddenFriendRequestIds.add(key);
    persistHiddenFriendRequestIds();

    const nodes = document.querySelectorAll(`.notificacao-item-amizade[data-solicitacao-id="${key}"]`);
    nodes.forEach((node) => node.remove());
    syncNotificationPlaceholder();
}

function clearAllNotifications() {
    document.querySelectorAll('.notificacao-item-amizade[data-solicitacao-id]').forEach((node) => {
        const id = node.dataset.solicitacaoId;
        if (id) hiddenFriendRequestIds.add(String(id));
    });
    persistHiddenFriendRequestIds();

    getNotificationLists().forEach((lista) => {
        lista.querySelectorAll('.notificacao-item-amizade, .notificacao-item').forEach((node) => node.remove());
    });

    clearNotificationHistory(window.esportefyCurrentUserId);

    syncNotificationPlaceholder();
}

function getNotificationLists() {
    const desktop = document.getElementById('lista-notificacoes');
    const mobile = document.getElementById('lista-notificacoes-mobile');
    return [desktop, mobile].filter(Boolean);
}

function getPrimaryNotificationList() {
    return document.getElementById('lista-notificacoes')
        || document.getElementById('lista-notificacoes-mobile');
}

function updateNotificationBadge() {
    const lista = getPrimaryNotificationList();
    const badge = document.getElementById('badge-notificacoes');
    if (!badge) return;

    const total = lista
        ? lista.querySelectorAll('.notificacao-item-amizade, .notificacao-item').length
        : 0;

    if (total > 0) {
        badge.textContent = total;
        badge.classList.remove('d-none');
    } else {
        badge.classList.add('d-none');
    }
}

function syncNotificationPlaceholder() {
    const listas = getNotificationLists();
    if (!listas.length) return;

    listas.forEach((lista) => {
        const hasItems = lista.querySelectorAll('.notificacao-item-amizade, .notificacao-item').length > 0;
        let placeholder = lista.querySelector('.placeholder-msg');

        if (!hasItems && !placeholder) {
            placeholder = document.createElement('div');
            placeholder.className = 'placeholder-msg px-3 py-3 text-muted small text-center';
            placeholder.textContent = 'Sem notificações no momento.';
            lista.appendChild(placeholder);
        }

        if (hasItems && placeholder) {
            placeholder.remove();
        }
    });

    updateNotificationBadge();
}

/* ─── GERENCIADOR DE NOTIFICAÇÕES DE AMIZADE ─── */
async function carregarSolicitacoesAmizade() {
    try {
        const response = await fetch('/perfis/api/solicitacoes/', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) return;
        
        const data = await response.json();
        renderizarSolicitacoes(data.recebidas || []);
    } catch (err) {
        console.error('Erro ao carregar solicitações:', err);
    }
}

function renderizarSolicitacoes(recebidas) {
    const listas = getNotificationLists();
    if (!listas.length) return;

    const recebidasVisiveis = recebidas.filter((sol) => !hiddenFriendRequestIds.has(String(sol.id)));

    listas.forEach((lista) => {
        lista.querySelectorAll('.notificacao-item-amizade').forEach((node) => node.remove());
    });

    // Renderizar recebidas
    recebidasVisiveis.forEach(sol => {
        const safeId = Number.parseInt(sol.id, 10);
        if (!Number.isFinite(safeId) || safeId <= 0) {
            return;
        }

        const safeUsername = escapeHtml(sol.username || 'Usuário');
        const safeFotoUrl = sanitizeHttpUrl(sol.foto_url, {
            allowRelative: true,
            fallback: '/media/fotos_perfil/default.jpg',
        });

        const itemHtml = `
            <img src="${safeFotoUrl}" alt="${safeUsername}">
            <div class="info">
                <div class="username">${safeUsername}</div>
                <div class="tipo">Quer ser seu amigo </div>
            </div>
            <div class="notificacao-acoes">
                <button class="btn-sm btn-accept" onclick="event.preventDefault(); event.stopPropagation(); aceitarAmizade(${safeId}, this)">
                    <i class="bi bi-check"></i>
                </button>
                <button class="btn-sm btn-reject" onclick="event.preventDefault(); event.stopPropagation(); recusarAmizade(${safeId}, this)">
                    <i class="bi bi-x"></i>
                </button>
                <button class="btn-sm btn-dismiss" onclick="event.preventDefault(); event.stopPropagation(); dismissFriendNotification(${safeId})" aria-label="Excluir notificação">
                    <i class="bi bi-trash3"></i>
                </button>
            </div>
        `;

        listas.forEach((lista) => {
            const item = document.createElement('div');
            item.className = 'notificacao-item-amizade';
            item.dataset.solicitacaoId = String(sol.id);
            item.innerHTML = itemHtml;
            lista.prepend(item);
        });
    });

    syncNotificationPlaceholder();
}

async function aceitarAmizade(solicitacaoId, botao) {
    const token = getCookie('csrftoken');
    hiddenFriendRequestIds.delete(String(solicitacaoId));
    persistHiddenFriendRequestIds();
    
    try {
        const response = await fetch(`/perfis/solicitacao/aceitar/${solicitacaoId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': token,
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (response.ok) {
            const itensRelacionados = document.querySelectorAll(`.notificacao-item-amizade[data-solicitacao-id="${solicitacaoId}"]`);
            itensRelacionados.forEach((node) => {
                node.innerHTML = `<div class="py-2 px-3 text-success small"><i class="bi bi-check-circle"></i> Amizade aceita!</div>`;
            });
            setTimeout(() => {
                itensRelacionados.forEach((node) => node.remove());
                syncNotificationPlaceholder();
                actualizarBadge();
            }, 1500);
            showToast('success', 'Novo amigo adicionado! 🎉', 5000);
            playNotificationSound();
        }
    } catch (err) {
        console.error('Erro ao aceitar:', err);
        showToast('error', 'Erro ao aceitar solicitação', 5000);
    }
}

async function recusarAmizade(solicitacaoId, botao) {
    const token = getCookie('csrftoken');
    hiddenFriendRequestIds.delete(String(solicitacaoId));
    persistHiddenFriendRequestIds();
    
    try {
        const response = await fetch(`/perfis/solicitacao/recusar/${solicitacaoId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': token,
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (response.ok) {
            const itensRelacionados = document.querySelectorAll(`.notificacao-item-amizade[data-solicitacao-id="${solicitacaoId}"]`);
            itensRelacionados.forEach((node) => {
                node.innerHTML = `<div class="py-2 px-3 text-muted small"><i class="bi bi-x-circle"></i> Recusado</div>`;
            });
            setTimeout(() => {
                itensRelacionados.forEach((node) => node.remove());
                syncNotificationPlaceholder();
                actualizarBadge();
            }, 1500);
            showToast('info', 'Solicitação recusada', 5000);
            playNotificationSound();
        }
    } catch (err) {
        console.error('Erro ao recusar:', err);
        showToast('error', 'Erro ao recusar solicitação', 5000);
    }
}

function actualizarBadge() {
    carregarSolicitacoesAmizade();
}

let notificationPollIntervalId = null;

function shouldPollNotifications() {
    return document.visibilityState === 'visible';
}

function startNotificationPolling() {
    if (notificationPollIntervalId) return;
    notificationPollIntervalId = setInterval(() => {
        if (!shouldPollNotifications()) return;
        carregarSolicitacoesAmizade();
    }, 30000);
}

function stopNotificationPolling() {
    if (!notificationPollIntervalId) return;
    clearInterval(notificationPollIntervalId);
    notificationPollIntervalId = null;
}

// Carregar solicitações ao abrir o dropdown
document.addEventListener('DOMContentLoaded', () => {
    const notificDropdown = document.getElementById('notificacoesDropdown');
    const notificacoesDesktopMenu = document.querySelector('.notificacoes-dropdown');

    if (notificacoesDesktopMenu) {
        notificacoesDesktopMenu.addEventListener('click', (event) => {
            const isAllowed = !!event.target.closest('#btn-limpar-notificacoes, .btn-close-notificacao, .rt-notification__toggle');
            if (isAllowed) return;

            event.preventDefault();
            event.stopPropagation();
        }, true);
    }

    if (notificDropdown) {
        notificDropdown.addEventListener('click', carregarSolicitacoesAmizade);
        const dropdownRoot = notificDropdown.closest('.dropdown');
        if (dropdownRoot) {
            dropdownRoot.addEventListener('hidden.bs.dropdown', collapseExpandedNotifications);
        } else {
            notificDropdown.addEventListener('hidden.bs.dropdown', collapseExpandedNotifications);
        }
        // Carregar também no início
        carregarSolicitacoesAmizade();
        // Polling leve: evita chamadas contínuas quando a aba está em segundo plano.
        startNotificationPolling();
    }

    const clearDesktop = document.getElementById('btn-limpar-notificacoes');
    if (clearDesktop) {
        clearDesktop.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            clearAllNotifications();
        });
    }

    const clearMobile = document.getElementById('btn-limpar-notificacoes-mobile');
    if (clearMobile) {
        clearMobile.addEventListener('click', (event) => {
            event.preventDefault();
            clearAllNotifications();
        });
    }

    syncNotificationPlaceholder();

    document.addEventListener('visibilitychange', () => {
        if (shouldPollNotifications()) {
            carregarSolicitacoesAmizade();
            startNotificationPolling();
        } else {
            stopNotificationPolling();
        }
    });
});

document.addEventListener("DOMContentLoaded", () => {
    window.esportefyAudioUnlocked = false;
    window.esportefyPendingSuccessSound = false;

    // Desbloqueia áudio na primeira interação do usuário (política dos navegadores)
    const unlockOnce = () => unlockNotificationAudio();
    document.addEventListener('click', unlockOnce, { once: true });
    document.addEventListener('keydown', unlockOnce, { once: true });
    document.addEventListener('touchstart', unlockOnce, { once: true });
    document.addEventListener('pointerdown', unlockOnce, { once: true });
    document.addEventListener('mousemove', unlockOnce, { once: true });
    document.addEventListener('wheel', unlockOnce, { once: true });

    // Permite fechar rapidamente as notificações clicando/toquando em qualquer ponto da página.
    document.addEventListener('pointerdown', () => {
        dismissAllToasts();
    }, true);

    // Inicializa toasts renderizados pelo servidor
    var toastElList = [].slice.call(document.querySelectorAll('.toast'));
    toastElList.map(function (toastEl) {
      return new bootstrap.Toast(toastEl).show();
    });

    // Toca som para qualquer mensagem do backend, não apenas sucesso
    const hasAnyToast = toastElList.length > 0;
    if (hasAnyToast) {
        window.esportefyPendingSuccessSound = true;
        setTimeout(() => playNotificationSound(), 160);
        setTimeout(() => {
            if (window.esportefyPendingSuccessSound) {
                playNotificationSound();
            }
        }, 900);
    }

    // --- Lógica de Notificações ---
    const userIdElement = document.getElementById('json-user-id');
    const usernameElement = document.getElementById('json-username');
    const wsTokenElement = document.getElementById('json-ws-token');
    const sessionKeyElement = document.getElementById('json-session-key');

    const userId = userIdElement ? JSON.parse(userIdElement.textContent) : null;
    const username = usernameElement ? JSON.parse(usernameElement.textContent) : null;
    const wsToken = wsTokenElement ? JSON.parse(wsTokenElement.textContent) : null;
    const sessionKey = sessionKeyElement ? JSON.parse(sessionKeyElement.textContent) : null;

    window.esportefyCurrentUserId = userId;
    renderStoredNotificationHistory(userId);

    if (userId && username && wsToken) {
        initNotificationSocket(userId, username, wsToken, sessionKey);
    }

    function initNotificationSocket(uid, uname, token, session) {
        const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        const host = window.location.hostname;
        
        const port = (window.location.port === '8000' || window.location.port === '8080') ? ':8080' : '';

        const sessionParam = session ? `&session=${encodeURIComponent(session)}` : '';
        const url = `${protocol}${host}${port}/ws/notifications/?user=${encodeURIComponent(uid)}&username=${encodeURIComponent(uname)}&token=${encodeURIComponent(token)}${sessionParam}`;

        try {
            const socket = new WebSocket(url);
            window.notificationSocket = socket;
            socket.onopen = () => {};

            socket.onclose = (e) => {
                setTimeout(() => initNotificationSocket(uid, uname, token, session), 5000);
            };

            socket.onerror = () => {};

            socket.onmessage = (e) => {
                const data = JSON.parse(e.data);

                if (data.type === 'force_logout') {
                    showToast('warning', data.mensagem || 'Sua sessão foi encerrada por novo login.', 4000);
                    setTimeout(() => {
                        window.location.href = '/accounts/logout/?forced=1';
                    }, 700);
                    return;
                }
                
                // Verificar se é um evento de amizade
                if (data.type === 'send_generic_notification' || data.type === 'amizade_notification') {
                    carregarSolicitacoesAmizade();
                    
                    // Mostrar toast informando
                    let toastMsg = data.mensagem || 'Nova solicitação de amizade!';
                    showToast(resolveRealtimeToastKind(data), toastMsg, 6000);
                    playNotificationSound();
                    return;
                }
                
                let conteudoHTML = '';
                let popupTexto = data.mensagem || 'Você tem uma nova notificação.';

                if (data.type === 'new_message_notification') {
                    conteudoHTML = buildRealtimeNotificationContent(data);
                    popupTexto = `${data.remetente || 'Contato'}: ${data.mensagem || 'Nova mensagem recebida.'}`;
                } else if (data.type === 'notification') {
                    conteudoHTML = buildRealtimeNotificationContent(data);
                    // Notificações de sistema não precisam dos dois pontos (":") para não parecer chat
                    popupTexto = `${data.remetente || 'Aviso'} ${data.mensagem || ''}`;
                } else {
                    conteudoHTML = `
                        <div class="d-flex align-items-center gap-2 p-2 border-bottom">
                            <i class="bi bi-bell-fill text-warning fs-4"></i>
                            <div>
                                <h6 class="mb-0 small fw-bold">Nova notificação</h6>
                                <small class="text-muted">Você tem uma nova interação.</small>
                            </div>
                        </div>
                    `;
                }

                showToast(resolveRealtimeToastKind(data), popupTexto, 6000);
                playNotificationSound();

                const notificationId = `rt-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
                appendNotificationHistoryItem(uid, {
                    notificationId,
                    remetente: data.remetente || 'Contato',
                    mensagem: data.mensagem || 'Nova notificação recebida.',
                    foto_url: data.foto_url || '',
                    conversa_url: data.conversa_url || '/feed/',
                    timestamp: data.timestamp || 'agora',
                    timestamp_iso: data.timestamp_iso || new Date().toISOString(),
                });
                prependRealtimeNotificationToLists(notificationId, conteudoHTML);

                const badge = document.getElementById('badge-notificacoes');
                if (badge) {
                    badge.classList.add('badge-animada');
                    setTimeout(() => badge.classList.remove('badge-animada'), 500);
                }
            };

        } catch (err) {
            showToast('warning', 'Não foi possível iniciar as notificações em tempo real.');
        }
    }

    // Ativa navegação inferior no mobile e gerência de selecionado
    const mobileNav = document.getElementById('mobileBottomNav');
    const topNotificationsBtn = document.getElementById('navTopNotificacoesBtn');

    const openNotifications = () => {
        carregarSolicitacoesAmizade();

        if (window.matchMedia('(max-width: 992px)').matches) {
            const mobileModalEl = document.getElementById('mobileNotificationsModal');
            if (mobileModalEl) {
                const modal = bootstrap.Modal.getOrCreateInstance(mobileModalEl);
                modal.show();
            }
        } else {
            const dropdownEl = document.getElementById('notificacoesDropdown');
            if (dropdownEl) {
                const drop = bootstrap.Dropdown.getOrCreateInstance(dropdownEl);
                drop.show();
            }
        }
    };

    const closeMobileNotifications = () => {
        const mobileModalEl = document.getElementById('mobileNotificationsModal');
        if (!mobileModalEl) return;
        const modal = bootstrap.Modal.getInstance(mobileModalEl);
        if (modal) {
            modal.hide();
        }
    };

    if (topNotificationsBtn) {
        topNotificationsBtn.addEventListener('click', (event) => {
            event.preventDefault();
            openNotifications();
        });
    }

    if (mobileNav) {
        const currentPath = window.location.pathname.replace(/\/$/, '');
        const currentHash = window.location.hash;
        const navItems = mobileNav.querySelectorAll('.nav-item');

        navItems.forEach((item) => {
            const target = item.dataset.nav;

            if (currentPath === '/feed') {
                if (target === 'feed' && (!currentHash || currentHash === '#feed-atividades')) {
                    item.classList.add('active');
                }
                if (target === 'partidas' && currentHash === '#feed-partidas') {
                    item.classList.add('active');
                }
                if (target === 'noticias' && currentHash === '#feed-noticias') {
                    item.classList.add('active');
                }
            } else {
                if (target === 'feed' && currentPath === '/feed') {
                    item.classList.add('active');
                } else if (target === 'perfil' && currentPath.startsWith('/perfis/meu')) {
                    item.classList.add('active');
                } else if (target === 'jogadores' && currentPath.startsWith('/perfis/usuarios')) {
                    item.classList.add('active');
                }
            }

            item.addEventListener('click', (event) => {
                const targetTab = event.currentTarget.dataset.nav;
                const feedUrl = '/feed';

                // Sempre fecha modal de notificações ao navegar para outra aba
                if (targetTab !== 'notificacoes') {
                    closeMobileNotifications();
                }

                if (['feed','partidas','noticias'].includes(targetTab)) {
                    event.preventDefault();

                    // Se não estiver na página de feed, redireciona para feed com hash.
                    if (currentPath !== feedUrl) {
                        window.location.href = `${feedUrl}#${targetTab === 'feed' ? 'feed-atividades' : 'feed-' + targetTab}`;
                        return;
                    }

                    // Dentro do feed: apenas mostra a seção escolhida
                    setFeedSection(targetTab);
                    history.replaceState(null, '', `#${targetTab === 'feed' ? 'feed-atividades' : 'feed-' + targetTab}`);

                    // Força reposicionamento levemente no topo para UI consistente
                    window.scrollTo({ top: 0, behavior: 'auto' });
                }

                if (targetTab === 'notificacoes') {
                    event.preventDefault();
                    openNotifications();
                }

                navItems.forEach((nav) => nav.classList.remove('active'));
                event.currentTarget.classList.add('active');
            });
        });

        if (currentPath === '/feed') {
            updateFeedSectionFromHash();
            window.addEventListener('hashchange', updateFeedSectionFromHash);
        }
    }
});
