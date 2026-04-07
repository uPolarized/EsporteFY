/**
 * Profile Modal Manager
 * Gerencia a exibição do modal de perfil ao clicar em avatares
 */

class ProfileModal {
    constructor() {
        this.createModal();
        this.attachEventListeners();
    }

    createModal() {
        // Criar HTML do modal
        const modalHTML = `
            <div id="profileModal" class="profile-modal-overlay" style="display: none;">
                <div class="profile-modal">
                    <button class="profile-modal-close" aria-label="Fechar">
                        <i class="bi bi-x-lg"></i>
                    </button>
                    <div class="profile-modal-content">
                        <!-- Conteúdo carregado dinamicamente -->
                    </div>
                </div>
            </div>
        `;

        // Adicionar ao body
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        this.overlay = document.getElementById('profileModal');
        this.modal = document.querySelector('.profile-modal');
        this.closeBtn = document.querySelector('.profile-modal-close');
        this.content = document.querySelector('.profile-modal-content');

        // Event listeners
        this.closeBtn.addEventListener('click', () => this.close());
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) this.close();
        });
    }

    attachEventListeners() {
        // Delegar cliques em elementos com data-profile-modal
        document.addEventListener('click', (e) => {
            const link = e.target.closest('[data-profile-modal]');
            if (!link) return;

            e.preventDefault();
            e.stopPropagation();

            const userId = link.dataset.profileModal;
            const currentUserId = this.getCurrentUserId();

            // Não permitir abrir modal do próprio perfil
            if (String(userId) === String(currentUserId)) {
                return;
            }

            this.open(userId);
        });
    }

    getCurrentUserId() {
        const elem = document.getElementById('json-user-id');
        return elem ? elem.textContent.replace(/"/g, '') : null;
    }

    async open(userId) {
        try {
            this.overlay.style.display = 'flex';
            this.content.innerHTML = '<div class="profile-modal-loading"><i class="bi bi-hourglass-split"></i></div>';

            // Buscar dados do perfil
            const profileRes = await fetch(`/perfis/api/perfil/${userId}/`);
            if (!profileRes.ok) throw new Error('Erro ao carregar perfil');
            const profile = await profileRes.json();

            this.renderContent(profile);
        } catch (error) {
            console.error('Erro ao abrir perfil modal:', error);
            this.content.innerHTML = '<div class="profile-modal-error">Erro ao carregar perfil</div>';
        }
    }

    renderContent(profile) {
        const currentUserId = this.getCurrentUserId();
        const isFriend = profile.is_friend || false;
        const hasRequest = profile.has_request || false;
        const showOnlineStatus = profile.show_online_status !== false;
        const isOnline = Boolean(profile.is_online);

        // Avatar com suporte a GIF
        const avatarSrc = profile.foto;
        const statusClass = isOnline ? 'online' : 'offline';
        const statusDot = showOnlineStatus
            ? `<div class="profile-modal-status-dot profile-modal-status-${statusClass}"></div>`
            : '';
        
        const avatarHTML = avatarSrc
            ? `<div class="profile-modal-avatar-wrapper">
                <img src="${avatarSrc}" alt="${profile.user.username}" class="profile-modal-avatar">
                ${statusDot}
              </div>`
            : `<div class="profile-modal-avatar-wrapper">
                <div class="profile-modal-avatar profile-modal-avatar-placeholder">${profile.user.username[0].toUpperCase()}</div>
                ${statusDot}
              </div>`;

        // Header com banner como background
        const bannerSrc = profile.banner || '/static/images/placeholder-banner.jpg';
        const headerStyle = profile.banner
            ? `background-image: linear-gradient(to bottom, rgba(7, 7, 10, 0.04), rgba(7, 7, 10, 0.7)), url('${bannerSrc}'); background-size: cover; background-position: center;`
            : '';
        const headerClass = profile.banner ? 'profile-modal-header' : 'profile-modal-header profile-modal-header--default';
        const headerHTML = `<div class="${headerClass}" style="${headerStyle}"></div>`;

        const lastSeenLabel = profile.last_seen_label || 'Sem registro recente';
        const basicEsporte = profile.esporte || 'Não informado';
        const basicNivel = profile.nivel || 'Não informado';
        const basicMembroDesde = profile.member_since || '—';

        const presenceLines = [];
        if (showOnlineStatus) {
            const statusClass = isOnline ? 'is-online' : 'is-offline';
            const statusText = isOnline ? 'Online agora' : 'Offline';
            presenceLines.push(`<div class="profile-modal-presence-line ${statusClass}"><span class="profile-modal-presence-dot" aria-hidden="true"></span><span>${statusText}</span></div>`);
        }
        presenceLines.push(`<div class="profile-modal-presence-line profile-modal-presence-last-seen"><i class="bi bi-clock-history"></i><span>Visto por último: ${this.escapeHtml(lastSeenLabel)}</span></div>`);

        const presenceHTML = `<div class="profile-modal-presence">${presenceLines.join('')}</div>`;

        // Bio
        const bio = profile.mini_bio || 'Sem bio';

        // Stats
        const stats = `
            <div class="profile-modal-stats">
                <div class="profile-modal-stat">
                    <div class="profile-modal-stat-value">${profile.partidas_count || 0}</div>
                    <div class="profile-modal-stat-label">Partidas</div>
                </div>
                <div class="profile-modal-stat">
                    <div class="profile-modal-stat-value">${profile.amigos_count || 0}</div>
                    <div class="profile-modal-stat-label">Amigos</div>
                </div>
                <div class="profile-modal-stat">
                    <div class="profile-modal-stat-value">${profile.rating || '—'}</div>
                    <div class="profile-modal-stat-label">Rating</div>
                </div>
            </div>
        `;

        const basicInfo = `
            <div class="profile-modal-basic-grid">
                <div class="profile-modal-basic-item">
                    <span class="profile-modal-basic-label">Esporte</span>
                    <strong class="profile-modal-basic-value">${this.escapeHtml(basicEsporte)}</strong>
                </div>
                <div class="profile-modal-basic-item">
                    <span class="profile-modal-basic-label">Nível</span>
                    <strong class="profile-modal-basic-value">${this.escapeHtml(basicNivel)}</strong>
                </div>
                <div class="profile-modal-basic-item profile-modal-basic-item--full">
                    <span class="profile-modal-basic-label">Membro desde</span>
                    <strong class="profile-modal-basic-value">${this.escapeHtml(basicMembroDesde)}</strong>
                </div>
            </div>
        `;

        // Botões de ação
        let actions = '';
        if (String(profile.user.id) !== String(currentUserId)) {
            if (isFriend) {
                actions = `
                    <div class="profile-modal-actions">
                        <button class="profile-modal-btn profile-modal-btn-danger" onclick="window.profileModalRemoveFriend(${profile.user.id})">
                            <i class="bi bi-person-dash"></i> Remover Amigo
                        </button>
                        <a href="/perfis/usuario/${profile.user.username}/" class="profile-modal-btn profile-modal-btn-secondary">
                            <i class="bi bi-arrow-up-right"></i> Ver Perfil
                        </a>
                    </div>
                `;
            } else if (hasRequest) {
                actions = `
                    <div class="profile-modal-actions">
                        <button class="profile-modal-btn profile-modal-btn-secondary" disabled>
                            Solicitação enviada
                        </button>
                        <a href="/perfis/usuario/${profile.user.username}/" class="profile-modal-btn profile-modal-btn-secondary">
                            Ver perfil
                        </a>
                    </div>
                `;
            } else if (profile.allow_friend_requests === false) {
                actions = `
                    <div class="profile-modal-actions">
                        <button class="profile-modal-btn profile-modal-btn-secondary" disabled>
                            Solicitações desativadas
                        </button>
                        <a href="/perfis/usuario/${profile.user.username}/" class="profile-modal-btn profile-modal-btn-secondary">
                            Ver perfil
                        </a>
                    </div>
                `;
            } else {
                actions = `
                    <div class="profile-modal-actions">
                        <button class="profile-modal-btn profile-modal-btn-primary" onclick="window.profileModalAddFriend(${profile.user.id})">
                            Adicionar
                        </button>
                        <a href="/perfis/usuario/${profile.user.username}/" class="profile-modal-btn profile-modal-btn-secondary">
                            Ver perfil
                        </a>
                    </div>
                `;
            }
        } else {
            actions = `
                <div class="profile-modal-actions">
                    <a href="/perfis/editar/" class="profile-modal-btn profile-modal-btn-primary" style="width: 100%;">
                        <i class="bi bi-pencil"></i> Editar Perfil
                    </a>
                </div>
            `;
        }

        this.content.innerHTML = `
            ${headerHTML}
            ${avatarHTML}
            <div class="profile-modal-body">
                <h2 class="profile-modal-username">${this.escapeHtml(profile.user.username)}</h2>
                ${presenceHTML}
                <p class="profile-modal-bio">${this.escapeHtml(bio)}</p>
                ${basicInfo}
                ${stats}
                ${actions}
            </div>
        `;
        
        // Armazenar userId para polling de status
        this.currentUserId = profile.user.id;
        this.currentShowOnlineStatus = showOnlineStatus;
        this.startStatusPolling();
    }

    startStatusPolling() {
        if (!this.currentShowOnlineStatus) {
            return;
        }

        // Atualizar status a cada 5 segundos
        if (this.statusPollingInterval) {
            clearInterval(this.statusPollingInterval);
        }
        
        this.statusPollingInterval = setInterval(async () => {
            if (!this.currentUserId) return;
            
            try {
                const statusRes = await fetch(`/perfis/api/status/?ids=${this.currentUserId}`);
                if (statusRes.ok) {
                    const statusData = await statusRes.json();
                    const isOnline = statusData[String(this.currentUserId)] || false;
                    
                    // Atualizar a bolinha de status
                    const statusDot = document.querySelector('.profile-modal-status-dot');
                    if (statusDot) {
                        statusDot.className = `profile-modal-status-dot profile-modal-status-${isOnline ? 'online' : 'offline'}`;
                    }
                }
            } catch (error) {
                console.error('Erro ao atualizar status:', error);
            }
        }, 5000);
    }

    close() {
        // Parar o polling de status
        if (this.statusPollingInterval) {
            clearInterval(this.statusPollingInterval);
            this.statusPollingInterval = null;
        }
        this.currentShowOnlineStatus = false;
        this.overlay.style.display = 'none';
        this.content.innerHTML = '';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Inicializar modal quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.profileModal = new ProfileModal();
    });
} else {
    window.profileModal = new ProfileModal();
}

// Funções globais para ações de amigo
window.profileModalAddFriend = async function(userId) {
    try {
        const response = await fetch(`/perfis/solicitacao/enviar/${userId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: userId })
        });

        if (response.ok) {
            if (window.showToast) showToast('success', 'Solicitação de amizade enviada.');
            window.profileModal.open(userId);
        } else {
            if (window.showToast) showToast('error', 'Não foi possível enviar a solicitação de amizade.');
        }
    } catch (error) {
        console.error('Erro:', error);
        if (window.showToast) showToast('error', 'Não foi possível processar a solicitação.');
    }
};

window.profileModalRemoveFriend = async function(userId) {
    if (!confirm('Deseja remover este amigo?')) return;

    try {
        const response = await fetch(`/perfis/remover-amigo/${userId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: userId })
        });

        if (response.ok) {
            if (window.showToast) showToast('success', 'Amigo removido com sucesso.');
            window.profileModal.close();
        } else {
            if (window.showToast) showToast('error', 'Não foi possível remover o amigo.');
        }
    } catch (error) {
        console.error('Erro:', error);
        if (window.showToast) showToast('error', 'Não foi possível processar a remoção.');
    }
};
