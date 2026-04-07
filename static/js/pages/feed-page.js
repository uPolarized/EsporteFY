document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('toggle-minhas-partidas');
  const partidas = document.querySelectorAll('.match-card');
  const feedFilterButtons = document.querySelectorAll('.activity-filter-pill');
  const feedFilterRow = document.getElementById('feed-filter-row');
  const feedFilterEmpty = document.getElementById('feed-filter-empty');
  const feedSectionsRoot = document.getElementById('feed-sections');
  const activityFeedShell = document.querySelector('.activity-feed-shell');
  const feedToggleFilters = document.getElementById('feed-toggle-filters');
  const onlineFriendsCounter = document.querySelector('[data-online-friends-count]');
  let ocultando = false;
  let activeFeedFilter = 'all';

  async function refreshOnlineFriendsCounter() {
    if (!onlineFriendsCounter) return;

    try {
      const response = await fetch('/perfis/api/online-players/?limit=40', {
        credentials: 'same-origin',
      });

      if (!response.ok) return;

      const data = await response.json();
      const players = Array.isArray(data.players) ? data.players : [];
      const friendsOnline = players.filter((player) => Boolean(player.is_online) && Boolean(player.is_friend)).length;

      onlineFriendsCounter.textContent = String(friendsOnline);
    } catch (_) {
      // Silencia falha de rede para evitar ruído no feed.
    }
  }

  if (onlineFriendsCounter) {
    refreshOnlineFriendsCounter();
    setInterval(refreshOnlineFriendsCounter, 30000);
  }

  toggleBtn.addEventListener('click', () => {
    ocultando = !ocultando;

    partidas.forEach(card => {
      const ehMinha = card.dataset.organizador === 'true';
      if (ehMinha) {
        if (ocultando) {
          card.classList.add('fade-out');
          setTimeout(() => card.style.display = 'none', 200);
        } else {
          card.style.display = '';
          card.classList.remove('fade-out');
        }
      }
    });

    toggleBtn.innerHTML = ocultando
      ? '<i class="bi bi-eye"></i> Mostrar minhas partidas'
      : '<i class="bi bi-eye-slash"></i> Ocultar minhas partidas';
  });

  function escapeFeedValue(value) {
    if (typeof window.escapeHtml === 'function') {
      return window.escapeHtml(value == null ? '' : String(value));
    }
    const div = document.createElement('div');
    div.innerText = value == null ? '' : String(value);
    return div.innerHTML;
  }

  function renderActivityAvatar(data) {
    const actorId = escapeFeedValue(data.actor_id || '');
    const actorName = escapeFeedValue(data.actor_name || 'Jogador');
    if (data.actor_avatar_url) {
      const url = `${data.actor_avatar_url}${String(data.actor_avatar_url).includes('?') ? '&' : '?'}v=${Date.now()}`;
      return `<img src="${escapeFeedValue(url)}" alt="${actorName}" class="activity-card__avatar" data-profile-modal="${actorId}" style="cursor: pointer;" title="Abrir mini perfil de ${actorName}" aria-label="Abrir mini perfil de ${actorName}">`;
    }
    return `<div class="activity-card__avatar activity-card__avatar--placeholder" data-profile-modal="${actorId}" style="cursor: pointer;" title="Abrir mini perfil de ${actorName}" aria-label="Abrir mini perfil de ${actorName}">${escapeFeedValue(data.actor_initial || '?')}</div>`;
  }

  function renderActivityMeta(data) {
    if (!Array.isArray(data.meta) || !data.meta.length) return '';
    return `<div class="activity-card__meta">${data.meta.map((item) => `<span>${escapeFeedValue(item)}</span>`).join('')}</div>`;
  }

  function renderActivityStats(data) {
    if (!Array.isArray(data.stats) || !data.stats.length) return '';
    return `
      <div class="activity-card__stats">
        ${data.stats.map((stat) => `
          <div class="activity-card__stat">
            <small>${escapeFeedValue(stat.label || '')}</small>
            <strong>${escapeFeedValue(stat.value || '')}</strong>
          </div>
        `).join('')}
      </div>`;
  }

  function renderActivityCta(data) {
    if (data.cta_type === 'like') {
      const likeClass = data.user_liked ? ' is-liked' : '';
      const likeCount = data.like_count || 0;
      return `<button type="button" class="activity-card__cta activity-card__like${likeClass}" data-activity-id="${escapeFeedValue(data.activity_id)}" data-liked="${data.user_liked}" data-like-count="${likeCount}">
        <i class="bi bi-heart-fill"></i>
        <span class="like-count">${likeCount}</span>
      </button>`;
    }
    if (data.cta_type === 'modal' && data.cta_target && document.getElementById(data.cta_target)) {
      return `<button type="button" class="activity-card__cta" data-bs-toggle="modal" data-bs-target="#${escapeFeedValue(data.cta_target)}">${escapeFeedValue(data.cta_label || 'Ver partida')}</button>`;
    }
    if (data.cta_url) {
      return `<a href="${escapeFeedValue(data.cta_url)}" class="activity-card__cta">${escapeFeedValue(data.cta_label || 'Abrir')}</a>`;
    }
    return '';
  }

  function renderActivityCard(data) {
    const pastClass = data.is_past ? ' activity-card--past' : '';
    return `
      <article class="activity-card activity-card--${escapeFeedValue(data.kind || 'generic')}${pastClass}" data-category="${escapeFeedValue(data.category || 'geral')}" data-activity-id="${escapeFeedValue(data.id)}" style="--activity-delay: 0ms;">
        <div class="activity-card__top">
          ${renderActivityAvatar(data)}
          <div class="activity-card__content">
            <div class="activity-card__badge">
              <i class="bi ${escapeFeedValue(data.icon || 'bi-lightning-charge-fill')}"></i>
              ${escapeFeedValue(data.badge_label || 'Atividade')}
            </div>
            <h3 class="activity-card__headline">${escapeFeedValue(data.headline || '')}</h3>
            <p class="activity-card__description">${escapeFeedValue(data.description || '')}</p>
          </div>
          <div class="activity-card__time">${escapeFeedValue(data.timestamp_label || 'agora')}</div>
        </div>
        ${renderActivityMeta(data)}
        ${renderActivityStats(data)}
        <div class="activity-card__actions">${renderActivityCta(data)}</div>
      </article>`;
  }

  function updateFilterCounter(category) {
    const allCounter = document.querySelector('[data-count-for="all"]');
    if (allCounter) {
      allCounter.textContent = String((parseInt(allCounter.textContent, 10) || 0) + 1);
    }

    if (category && ['partidas', 'avaliacoes'].includes(category)) {
      const counter = document.querySelector(`[data-count-for="${category}"]`);
      if (counter) {
        counter.textContent = String((parseInt(counter.textContent, 10) || 0) + 1);
      }
    }
  }

  function updateFeedVisibility() {
    const cards = document.querySelectorAll('.activity-card');
    let visibleCount = 0;

    cards.forEach((card) => {
      const shouldShow = activeFeedFilter === 'all' || card.dataset.category === activeFeedFilter;
      card.classList.toggle('d-none', !shouldShow);
      if (shouldShow) visibleCount += 1;
    });

    document.querySelectorAll('.activity-period').forEach((section) => {
      const visibleCards = section.querySelectorAll('.activity-card:not(.d-none)');
      section.classList.toggle('d-none', visibleCards.length === 0);
    });

    if (feedFilterEmpty) {
      feedFilterEmpty.classList.toggle('d-none', visibleCount !== 0);
    }
  }

  feedFilterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      activeFeedFilter = button.dataset.filter || 'all';
      feedFilterButtons.forEach((item) => item.classList.toggle('is-active', item === button));
      updateFeedVisibility();
    });
  });

  if (feedToggleFilters) {
    feedToggleFilters.addEventListener('click', () => {
      const expanded = !feedFilterRow.classList.contains('is-collapsed');
      feedFilterRow.classList.toggle('is-collapsed', expanded);
      feedToggleFilters.setAttribute('aria-pressed', String(!expanded));
      feedToggleFilters.classList.toggle('is-active', !expanded);
    });
  }

  if (activityFeedShell && feedSectionsRoot && window.innerWidth > 768) {
    activityFeedShell.addEventListener('wheel', (event) => {
      const canScrollInside = feedSectionsRoot.scrollHeight > feedSectionsRoot.clientHeight;
      if (!canScrollInside) return;

      const goingDown = event.deltaY > 0;
      const atTop = feedSectionsRoot.scrollTop <= 0;
      const atBottom = Math.ceil(feedSectionsRoot.scrollTop + feedSectionsRoot.clientHeight) >= feedSectionsRoot.scrollHeight;

      if ((goingDown && !atBottom) || (!goingDown && !atTop)) {
        event.preventDefault();
        feedSectionsRoot.scrollTop += event.deltaY;
      }
    }, { passive: false });
  }

  window.feedUi = {
    renderActivityCard,
    updateFilterCounter,
    updateFeedVisibility,
    getActiveFilter: () => activeFeedFilter,
  };

  updateFeedVisibility();
  setupLikeButtons();

  // Setup like buttons
  function setupLikeButtons() {
    const likeButtons = document.querySelectorAll('.activity-card__like');
    likeButtons.forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        const atividadeId = btn.dataset.activityId;
        const likeCountSpan = btn.querySelector('.like-count');
        
        // Otimistic UI - muda imediatamente
        const wasLiked = btn.classList.contains('is-liked');
        btn.classList.toggle('is-liked');
        
        if (likeCountSpan) {
          const currentCount = parseInt(likeCountSpan.textContent, 10) || 0;
          likeCountSpan.textContent = wasLiked ? currentCount - 1 : currentCount + 1;
        }
        
        try {
          const response = await fetch(`/social/atividade/${atividadeId}/like/`, {
            method: 'POST',
            headers: {
              'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
              'Content-Type': 'application/json',
            },
          });
          
          if (!response.ok) throw new Error('Erro na requisição');
          
          const data = await response.json();
          if (data.success) {
            btn.dataset.liked = data.liked;
            btn.dataset.likeCount = data.like_count;
            btn.classList.toggle('is-liked', data.liked);
            
            // Atualiza o contador com o valor real do backend
            if (likeCountSpan) {
              likeCountSpan.textContent = data.like_count;
            }
          }
        } catch (err) {
          console.error('Erro ao curtir:', err);
          // Rollback do otimistic UI
          btn.classList.toggle('is-liked');
          if (likeCountSpan) {
            const currentCount = parseInt(likeCountSpan.textContent, 10) || 0;
            likeCountSpan.textContent = wasLiked ? currentCount + 1 : currentCount - 1;
          }
        }
      });
    });
  }

  window.feedSetupLikeButtons = setupLikeButtons;
  setupLikeButtons();

  // Aviso central antes de redirecionar para o Google Maps
  const mapsRedirectConfirmLink = document.getElementById('mapsRedirectConfirmLink');
  if (mapsRedirectConfirmLink) {
    document.addEventListener('click', (event) => {
      const mapsBtn = event.target.closest('.js-open-maps-popup');
      if (!mapsBtn) return;

      event.preventDefault();
      const destinationUrl = mapsBtn.getAttribute('data-maps-url') || mapsBtn.getAttribute('href') || '#';
      mapsRedirectConfirmLink.setAttribute('href', destinationUrl);
    });
  }

  // Submodal de jogadores (abre sem fechar modal de detalhes)
  document.addEventListener('click', (event) => {
    const openBtn = event.target.closest('.js-open-jogadores-inline');
    if (openBtn) {
      event.preventDefault();
      const modalId = openBtn.getAttribute('data-jogadores-modal');
      const modalEl = modalId ? document.getElementById(modalId) : null;
      if (modalEl) {
        modalEl.classList.add('is-open');
        modalEl.setAttribute('aria-hidden', 'false');
      }
      return;
    }

    const closeBtn = event.target.closest('.js-close-jogadores-inline');
    if (closeBtn) {
      const modalEl = closeBtn.closest('.jogadores-inline-modal');
      if (modalEl) {
        modalEl.classList.remove('is-open');
        modalEl.setAttribute('aria-hidden', 'true');
      }
      return;
    }

    const overlay = event.target.closest('.jogadores-inline-modal');
    if (overlay && event.target === overlay) {
      overlay.classList.remove('is-open');
      overlay.setAttribute('aria-hidden', 'true');
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    document.querySelectorAll('.jogadores-inline-modal.is-open').forEach((modalEl) => {
      modalEl.classList.remove('is-open');
      modalEl.setAttribute('aria-hidden', 'true');
    });
  });
});


const feedSectionLabels = {
  today: 'Hoje',
  yesterday: 'Ontem',
  week: 'Esta semana',
  older: 'Mais antigas',
};

function ensureFeedSection(sectionKey) {
  const sectionsRoot = document.getElementById('feed-sections');
  if (!sectionsRoot) return null;

  const existing = document.getElementById(`activity-section-items-${sectionKey}`);
  if (existing) return existing;

  const emptyState = document.getElementById('feed-empty-state');
  if (emptyState) emptyState.remove();

  const wrapper = document.createElement('section');
  wrapper.className = 'activity-period';
  wrapper.dataset.sectionKey = sectionKey;
  wrapper.id = `activity-section-${sectionKey}`;
  wrapper.innerHTML = `
    <div class="activity-period__header">
      <span>${feedSectionLabels[sectionKey] || 'Agora'}</span>
      <small>1 item</small>
    </div>
    <div class="activity-period__items" id="activity-section-items-${sectionKey}"></div>
  `;

  sectionsRoot.prepend(wrapper);
  return wrapper.querySelector('.activity-period__items');
}

function refreshSectionCounters() {
  document.querySelectorAll('.activity-period').forEach((section) => {
    const headerCounter = section.querySelector('.activity-period__header small');
    const total = section.querySelectorAll('.activity-card').length;
    if (headerCounter) {
      headerCounter.textContent = `${total} item${total === 1 ? '' : 's'}`;
    }
  });
}

const feedProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const feedUserIdEl = document.getElementById('json-user-id');
const feedUsernameEl = document.getElementById('json-username');
const feedTokenEl = document.getElementById('json-ws-token');
const feedUserId = feedUserIdEl ? encodeURIComponent(JSON.parse(feedUserIdEl.textContent)) : '';
const feedUsername = feedUsernameEl ? encodeURIComponent(JSON.parse(feedUsernameEl.textContent)) : '';
const feedToken = feedTokenEl ? encodeURIComponent(JSON.parse(feedTokenEl.textContent)) : '';

let feedSocket = null;

if (feedUserId && feedUsername && feedToken) {
  feedSocket = new WebSocket(
    `${feedProtocol}${window.location.hostname}:8080/ws/feed/?user=${feedUserId}&username=${feedUsername}&token=${feedToken}`
  );
} else {
  console.warn('[feed] WebSocket não iniciado: credenciais ausentes no template.');
}

if (feedSocket) {
feedSocket.onmessage = function(e) {
  const data = JSON.parse(e.data);
  if (!window.feedUi) return;

  if (data.type === 'feed_remove') {
    const targetCard = document.querySelector(`.activity-card[data-activity-id="${String(data.id)}"]`);
    if (targetCard) {
      targetCard.remove();
      refreshSectionCounters();
      window.feedUi.updateFeedVisibility();
    }
    return;
  }

  if (data.type !== 'feed_update') return;

  if (data.category === 'amizades' || data.kind === 'friendship') return;
  const sectionKey = data.section_key || 'today';
  const container = ensureFeedSection(sectionKey);
  if (!container) return;

  const alreadyExists = document.querySelector(`.activity-card[data-activity-id="${String(data.id)}"]`);
  if (alreadyExists) {
    alreadyExists.remove();
  }

  container.insertAdjacentHTML('afterbegin', window.feedUi.renderActivityCard(data));
  refreshSectionCounters();
  window.feedUi.updateFilterCounter(data.category || 'geral');
  
  // Reattach like button handlers para novas atividades
  if (typeof window.feedSetupLikeButtons === 'function') {
    window.feedSetupLikeButtons();
  }

  const filterButtons = document.querySelectorAll('.activity-filter-pill');
  const activeFilter = window.feedUi.getActiveFilter();
  document.querySelectorAll('.activity-card').forEach((card) => {
    const shouldShow = activeFilter === 'all' || card.dataset.category === activeFilter;
    card.classList.toggle('d-none', !shouldShow);
  });
  document.querySelectorAll('.activity-period').forEach((section) => {
    section.classList.toggle('d-none', section.querySelectorAll('.activity-card:not(.d-none)').length === 0);
  });
  const filterEmpty = document.getElementById('feed-filter-empty');
  if (filterEmpty) {
    filterEmpty.classList.toggle('d-none', document.querySelectorAll('.activity-card:not(.d-none)').length !== 0);
  }
  filterButtons.forEach((button) => button.classList.toggle('is-active', button.dataset.filter === activeFilter));
};
}

