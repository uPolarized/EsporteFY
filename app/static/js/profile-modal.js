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

            // Buscar status online
            let isOnline = false;
            try {
                const statusRes = await fetch(`/perfis/api/status/?ids=${userId}`);
                if (statusRes.ok) {
                    const statusData = await statusRes.json();
                    isOnline = statusData[userId] || false;
                }
            } catch (e) {
                console.warn('Erro ao buscar status:', e);
            }

            this.renderContent(profile, isOnline);
        } catch (error) {
            console.error('Erro ao abrir perfil modal:', error);
            this.content.innerHTML = '<div class="profile-modal-error">Erro ao carregar perfil</div>';
        }
    }

    renderContent(profile, isOnline) {
        const currentUserId = this.getCurrentUserId();
        const isFriend = profile.is_friend || false;
        const hasRequest = profile.has_request || false;

        // Avatar com suporte a GIF
        const avatarSrc = profile.foto;
        const statusClass = isOnline ? 'online' : 'offline';
        const statusDot = `<div class="profile-modal-status-dot profile-modal-status-${statusClass}"></div>`;
        
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
        const headerStyle = `background-image: url('${bannerSrc}'); background-size: cover; background-position: center;`;
        const headerHTML = `<div class="profile-modal-header" style="${headerStyle}"></div>`;

        // Status removido - apenas bolinha no avatar

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
                            <i class="bi bi-hourglass-split"></i> Solicitação Enviada
                        </button>
                        <a href="/perfis/usuario/${profile.user.username}/" class="profile-modal-btn profile-modal-btn-secondary">
                            <i class="bi bi-arrow-up-right"></i> Ver Perfil
                        </a>
                    </div>
                `;
            } else {
                actions = `
                    <div class="profile-modal-actions">
                        <button class="profile-modal-btn profile-modal-btn-primary" onclick="window.profileModalAddFriend(${profile.user.id})">
                            <i class="bi bi-person-plus"></i> Adicionar
                        </button>
                        <a href="/perfis/usuario/${profile.user.username}/" class="profile-modal-btn profile-modal-btn-secondary">
                            <i class="bi bi-arrow-up-right"></i> Ver Perfil
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
                <p class="profile-modal-bio">${this.escapeHtml(bio)}</p>
                ${stats}
                ${actions}
            </div>
        `;
        
        // Armazenar userId para polling de status
        this.currentUserId = profile.user.id;
        this.startStatusPolling();
    }

    startStatusPolling() {
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
        const response = await fetch(`/perfis/solicitacoes/enviar/${userId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: userId })
        });

        if (response.ok) {
            if (window.showToast) showToast('success', 'Solicitação de amizade enviada!');
            window.profileModal.open(userId);
        } else {
            if (window.showToast) showToast('error', 'Erro ao enviar solicitação');
        }
    } catch (error) {
        console.error('Erro:', error);
        if (window.showToast) showToast('error', 'Erro ao processar');
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
            if (window.showToast) showToast('success', 'Amigo removido');
            window.profileModal.close();
        } else {
            if (window.showToast) showToast('error', 'Erro ao remover amigo');
        }
    } catch (error) {
        console.error('Erro:', error);
        if (window.showToast) showToast('error', 'Erro ao processar');
    }
};
