(function () {
  function escapeHtml(value) {
    if (typeof window.escapeHtml === 'function') {
      return window.escapeHtml(value == null ? '' : String(value));
    }
    const div = document.createElement('div');
    div.innerText = value == null ? '' : String(value);
    return div.innerHTML;
  }

  function renderPlayer(player) {
    const avatar = player.avatar_url
      ? `<img src="${escapeHtml(player.avatar_url)}" alt="${escapeHtml(player.username)}" class="online-player-item__avatar" data-profile-modal="${player.id}" style="cursor:pointer;" title="Abrir mini perfil de ${escapeHtml(player.username)}">`
      : `<span class="online-player-item__avatar online-player-item__avatar--placeholder" data-profile-modal="${player.id}" style="cursor:pointer;" title="Abrir mini perfil de ${escapeHtml(player.username)}">${escapeHtml((player.username || '?').slice(0, 1).toUpperCase())}</span>`;

    const friendTag = player.is_friend ? '<span class="online-player-item__friend-tag">amigo</span>' : '';

    const presenceText = player.is_online
      ? 'Online agora'
      : `Ativo recentemente • ${escapeHtml(player.last_seen_label || 'Sem registro recente')}`;

    return `
      <article class="online-player-item" data-user-id="${player.id}">
        ${avatar}
        <div class="online-player-item__content">
          <p class="online-player-item__name" data-profile-modal="${player.id}" style="cursor:pointer;">${escapeHtml(player.username)} ${friendTag}</p>
          <p class="online-player-item__meta">${escapeHtml(player.esporte || 'Nao informado')} • ${escapeHtml(player.nivel || 'Nao informado')}</p>
          <p class="online-player-item__state">${presenceText}</p>
        </div>
      </article>
    `;
  }

  async function refreshPanel(panel) {
    const listEl = panel.querySelector('[data-online-list]');
    const countEl = panel.querySelector('[data-online-count]');
    if (!listEl || !countEl) return;

    const limit = parseInt(panel.getAttribute('data-online-limit') || '14', 10);
    const q = panel.getAttribute('data-online-query') || '';
    const params = new URLSearchParams({ limit: String(Number.isFinite(limit) ? limit : 14) });
    if (q) params.set('q', q);

    try {
      const resp = await fetch(`/perfis/api/online-players/?${params.toString()}`, { credentials: 'same-origin' });
      if (!resp.ok) throw new Error('Falha ao carregar jogadores online');

      const data = await resp.json();
      const players = Array.isArray(data.players) ? data.players : [];
      panel._onlinePlayersData = players;
      const onlineCount = Number.isFinite(data.online_count) ? data.online_count : players.filter((p) => p.is_online).length;
      const onlineTotalCount = Number.isFinite(data.online_total_count) ? data.online_total_count : onlineCount;
      countEl.textContent = `${onlineTotalCount} online`;

      if (!players.length) {
        if (data.self_online) {
          listEl.innerHTML = '<p class="online-players-panel__empty">Apenas você está online agora.</p>';
        } else {
          listEl.innerHTML = '<p class="online-players-panel__empty">Nenhum jogador online agora.</p>';
        }
        return;
      }

      listEl.innerHTML = players.map(renderPlayer).join('');
      applyPanelFilters(panel);
    } catch (err) {
      listEl.innerHTML = '<p class="online-players-panel__empty">Nao foi possivel atualizar agora.</p>';
    }
  }

  function applyPanelFilters(panel) {
    const activeFilter = panel.getAttribute('data-online-active-filter') || 'all';
    const items = panel.querySelectorAll('.online-player-item');

    let visibleCount = 0;
    items.forEach((item, index) => {
      const player = panel._onlinePlayersData?.[index] || {};
      const isFriendOk = activeFilter !== 'friends' || Boolean(player.is_friend);
      const shouldShow = isFriendOk;
      item.classList.toggle('is-hidden', !shouldShow);
      if (shouldShow) visibleCount += 1;
    });

    const listEl = panel.querySelector('[data-online-list]');
    if (visibleCount === 0 && listEl) {
      const hasItems = items.length > 0;
      listEl.querySelectorAll('.online-players-panel__empty.dynamic').forEach((el) => el.remove());
      if (hasItems) {
        const empty = document.createElement('p');
        empty.className = 'online-players-panel__empty dynamic';
        empty.textContent = 'Nenhum jogador encontrado nesse filtro.';
        listEl.appendChild(empty);
      }
    } else if (listEl) {
      listEl.querySelectorAll('.online-players-panel__empty.dynamic').forEach((el) => el.remove());
    }
  }

  function wirePanelInteractions(panel) {
    panel.setAttribute('data-online-active-filter', 'all');

    panel.querySelectorAll('[data-online-filter]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const nextFilter = btn.getAttribute('data-online-filter') || 'all';
        panel.setAttribute('data-online-active-filter', nextFilter);
        panel.querySelectorAll('[data-online-filter]').forEach((chip) => {
          chip.classList.toggle('is-active', chip === btn);
        });
        applyPanelFilters(panel);
      });
    });

    const refreshBtn = panel.querySelector('[data-online-refresh]');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => refreshPanel(panel));
    }
  }

  function initOnlinePlayersPanels() {
    const panels = Array.from(document.querySelectorAll('[data-online-players-panel]'));
    if (!panels.length) return;

    panels.forEach((panel) => {
      wirePanelInteractions(panel);
      refreshPanel(panel);
      const intervalMs = parseInt(panel.getAttribute('data-online-interval') || '15000', 10);
      const safeInterval = Number.isFinite(intervalMs) ? Math.max(5000, intervalMs) : 15000;
      setInterval(() => refreshPanel(panel), safeInterval);
    });

    if (window.notificationSocket && typeof window.notificationSocket.addEventListener === 'function') {
      let refreshTimeout = null;
      window.notificationSocket.addEventListener('message', () => {
        if (refreshTimeout) {
          clearTimeout(refreshTimeout);
        }
        refreshTimeout = setTimeout(() => {
          panels.forEach((panel) => refreshPanel(panel));
        }, 600);
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initOnlinePlayersPanels);
  } else {
    initOnlinePlayersPanels();
  }
})();
