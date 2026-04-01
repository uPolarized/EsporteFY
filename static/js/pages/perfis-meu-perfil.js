function abrirModalAmigos() { document.getElementById('modalAmigos').classList.add('open'); }
function fecharModalAmigos() { document.getElementById('modalAmigos').classList.remove('open'); }
window.addEventListener('click', function(e){ const modal=document.getElementById('modalAmigos'); if(e.target===modal) fecharModalAmigos(); });

function atualizarStatusAmigos() {
  const cards = document.querySelectorAll('.friend-card-sidebar[data-friend-id]');
  if (!cards.length) return;
  const ids = Array.from(cards).map(c => c.dataset.friendId).join(',');
  fetch(`/perfis/api/status/?ids=${ids}`)
    .then(r => r.json())
    .then(data => {
      for (const [userId, isOnline] of Object.entries(data)) {
        const badge = document.getElementById(`status-badge-${userId}`);
        if (badge) {
          badge.innerHTML = isOnline
            ? '<span class="status-online" title="Online agora">🟢</span>'
            : '<span title="Offline">⚫</span>';
        }
      }
    })
    .catch(err => console.error('Status tickrate error:', err));
}

window.addEventListener('DOMContentLoaded', function() {
  setInterval(() => {
    if (document.visibilityState !== 'visible') return;
    atualizarStatusAmigos();
  }, 30000);
  atualizarStatusAmigos();
});
