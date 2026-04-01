(function () {
  async function atualizarBotoesDeAvaliacao() {
    const cards = Array.from(document.querySelectorAll('.partida-card[data-id]'));
    if (!cards.length) return;

    const ids = cards.map(c => c.getAttribute('data-id')).filter(Boolean);
    try {
      const url = `/partidas/statuses/?ids=${ids.join(',')}`;
      const resp = await fetch(url, { method: 'GET', credentials: 'same-origin' });
      if (!resp.ok) return;
      const data = await resp.json();

      cards.forEach(card => {
        const pid = card.getAttribute('data-id');
        const status = data[pid]?.avaliada;
        const actions = card.querySelector('.card-actions');
        if (!actions) return;

        // botão existente
        const btn = actions.querySelector('.avaliar-link, .transition-btn');
        if (status) {
          const b = document.createElement('button');
          b.className = 'btn btn-sm btn-success transition-btn';
          b.disabled = true;
          b.innerHTML = '<i class="bi bi-check-circle-fill"></i> Avaliada';
          if (btn) btn.replaceWith(b);
        } else {
          const a = document.createElement('a');
          a.className = 'btn btn-sm btn-primary avaliar-link';
          a.href = `/partidas/${pid}/avaliar/`;
          a.innerHTML = '<i class="bi bi-star-fill"></i> Avaliar';
          if (btn) btn.replaceWith(a);
        }
      });
    } catch (e) {
      console.warn('Erro ao verificar avaliações:', e);
    }
  }

  document.addEventListener('DOMContentLoaded', atualizarBotoesDeAvaliacao);
  window.addEventListener('pageshow', atualizarBotoesDeAvaliacao);
})();
