document.addEventListener("DOMContentLoaded", () => {
  function swapToFriendsBadge(container) {
    const actions = container.querySelector('.d-flex.gap-2');
    if (!actions) return;
    actions.innerHTML = '<span class="badge bg-success p-2">Amigos</span>';
  }

  function swapToPendingButton(container, userId) {
    const actions = container.querySelector('.d-flex.gap-2');
    if (!actions) return;
    actions.innerHTML = `<button class="btn btn-sm btn-secondary" disabled data-userid="${userId}">Pedido Enviado</button>`;
  }

  // Verifica se o WebSocket global existe
  if (!window.notificationSocket) {
    console.warn("🔌 WebSocket ainda não iniciado, aguardando...");
    return;
  }

  console.log("🎯 Monitorando notificações em tempo real na lista de usuários...");

  // Intercepta mensagens recebidas do socket
  const originalHandler = window.notificationSocket.onmessage;
  window.notificationSocket.onmessage = function(e) {
    if (originalHandler) originalHandler.call(this, e); // mantém notificações visuais

    let data;
    try {
      data = JSON.parse(e.data);
    } catch {
      console.error("❌ JSON inválido:", e.data);
      return;
    }

    const titulo = (data.titulo || "").toLowerCase();
    const msg = (data.mensagem || "").toLowerCase();

    // --- 🟢 CASO 1: amizade aceita → atualizar botão
    if (titulo.includes("amizade aceita") && data.solicitante_username) {
      const username = data.solicitante_username;
      const userCards = document.querySelectorAll('.list-group-item.card-usuario');
      userCards.forEach((container) => {
        const profileTrigger = container.querySelector('h5 [data-profile-modal]');
        if (!profileTrigger) return;
        const cardUsername = (profileTrigger.textContent || '').trim();
        if (cardUsername === username) {
          swapToFriendsBadge(container);
          console.log(`✅ Atualizado para 'Amigos' com ${username}`);
        }
      });
    }


    // --- 🔴 CASO 2: pedido recusado → voltar botão para "Adicionar Amigo"
    if (titulo.includes("pedido de amizade recusado")) {
      const usernameMatch = msg.match(/([a-zA-Z0-9_]+)/);
      if (usernameMatch) {
        const username = usernameMatch[1];
        const botoes = document.querySelectorAll(".list-group-item .btn.btn-secondary[disabled]");
        botoes.forEach(btn => {
          const container = btn.closest(".list-group-item");
          if (!container) return;
          const profileTrigger = container.querySelector('h5 [data-profile-modal]');
          const cardUsername = (profileTrigger?.textContent || '').trim();
          if (cardUsername === username) {
            swapToPendingButton(container, btn.dataset.userid || '');
            console.log(`↩️ Pedido recusado — botão restaurado para ${username}`);
          }
        });
      }
    }
  };
});
