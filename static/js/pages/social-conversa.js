document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 Chat Híbrido Iniciado");

    // --- Referências aos Elementos ---
    const chatLog = document.getElementById('chat-log');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('chat-message-input');
    const imageInput = document.getElementById('id_imagem');
    const previewContainer = document.getElementById('image-preview-container');
    const previewImage = document.getElementById('image-preview');
    const removeImageBtn = document.getElementById('remove-image-btn');
    
    // Pega o token CSRF do formulário
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // --- Dados do Template Django ---
    const outroUsuarioUsername = JSON.parse(document.getElementById('json-outro-usuario-username').textContent);
    const meuUsuarioUsername = JSON.parse(document.getElementById('json-meu-usuario-username').textContent);

    // ============================================================
    // 1. CONEXÃO WEBSOCKET (ESCUTA - PORTA 8080)
    // ============================================================
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const chatHost = window.location.hostname; 
    
    // Força a porta 8080 onde o FastAPI está rodando
    const userIdEl = document.getElementById('json-user-id');
    const wsTokenEl = document.getElementById('json-ws-token');
    const wsUserId = userIdEl ? JSON.parse(userIdEl.textContent) : '';
    const wsAuthToken = wsTokenEl ? JSON.parse(wsTokenEl.textContent) : '';
    const wsUrl = `${wsProtocol}//${chatHost}:8080/ws/chat/${encodeURIComponent(outroUsuarioUsername)}/?me=${encodeURIComponent(meuUsuarioUsername)}&user=${encodeURIComponent(wsUserId)}&token=${encodeURIComponent(wsAuthToken)}`;

    let chatSocket = null;

    function connectWebSocket() {
        console.log("🔌 Conectando WebSocket em:", wsUrl);
        chatSocket = new WebSocket(wsUrl);

        chatSocket.onopen = () => {
            console.log('✅ WebSocket conectado com sucesso (Porta 8080)!');
        };
        
        chatSocket.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                console.log("📩 Mensagem recebida via WS:", data);
                appendMessageToDOM(data);
            } catch (err) {
                console.error("Erro ao processar mensagem WS:", err);
            }
        };

        chatSocket.onclose = () => {
            console.warn('⚠️ WebSocket fechado. Tentando reconectar em 3s...');
            setTimeout(connectWebSocket, 3000);
        };

        chatSocket.onerror = (err) => console.error('❌ Erro no WebSocket:', err);
    }

    // Inicia a conexão
    connectWebSocket();

    // ============================================================
    // 2. FUNÇÕES DE INTERFACE
    // ============================================================

    function scrollToBottom() {
        if(chatLog) chatLog.scrollTop = chatLog.scrollHeight;
    }

    // Adiciona a mensagem ao HTML
    function appendMessageToDOM(data) {
        const isMe = (data.username === meuUsuarioUsername);
        const row = document.createElement('div');
        row.className = `message-row ${isMe ? 'me' : 'other'}`;
        
        let contentHtml = '';
        
        // Trata imagem
        if (data.image_url) {
            let imgUrl = data.image_url;
            // Corrige URL se vier relativa do Django
            if (imgUrl.startsWith('/')) imgUrl = window.location.origin + imgUrl;
            contentHtml += `<img src="${imgUrl}" class="chat-image" alt="foto">`;
        }
        
        // Trata texto
        if (data.message) {
            contentHtml += `<p class="chat-text">${data.message}</p>`;
        }
        
        row.innerHTML = `
            <div class="message-bubble">
                ${contentHtml}
                <span class="message-time">${data.timestamp || ''}</span>
            </div>
        `;
        
        chatLog.appendChild(row);
        bindImageClickEvents(); // Reaplica evento de zoom nas imagens novas
        scrollToBottom();
    }

    // ============================================================
    // 3. ENVIO DE MENSAGEM (POST - PORTA 8000)
    // ============================================================
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const messageText = messageInput.value.trim();
        const file = imageInput.files[0];

        if (!messageText && !file) return; // Evita envio vazio

        const formData = new FormData(chatForm);
        
        // URL da View Django
        const url = `/social/chat/enviar/${encodeURIComponent(outroUsuarioUsername)}/`;

        try {
            // Limpa o input imediatamente para melhor UX
            messageInput.value = '';
            limparPreview();

            const resp = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });

            if (resp.ok) {
                console.log("✅ Mensagem enviada via HTTP (Django)");
                messageInput.focus();
            } else {
                const errText = await resp.text();
                console.error("❌ Erro no envio HTTP:", errText);
                alert("Erro ao enviar mensagem. Verifique o console.");
            }
        } catch (err) {
            console.error("❌ Erro de rede:", err);
            alert("Erro de conexão com o servidor.");
        }
    });

    // ============================================================
    // 4. UTILITÁRIOS (PREVIEW E ZOOM)
    // ============================================================
    
    // Preview de imagem antes de enviar
    imageInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewContainer.style.display = 'flex';
            }
            reader.readAsDataURL(file);
        }
    });

    function limparPreview() {
        imageInput.value = '';
        previewContainer.style.display = 'none';
        previewImage.src = '';
    }
    
    removeImageBtn.addEventListener('click', limparPreview);

    // Modal de Zoom na imagem
    function bindImageClickEvents() {
        document.querySelectorAll('.chat-image').forEach(img => {
            if(img.dataset.zoomBound) return; // Evita duplicar listener
            img.dataset.zoomBound = "true";
            
            img.onclick = function() {
                const modal = document.createElement('div');
                modal.className = 'image-modal show';
                modal.innerHTML = `
                    <div class="image-modal-content">
                        <button class="image-modal-close">&times;</button>
                        <img src="${this.src}" class="image-modal-img">
                    </div>`;
                document.body.appendChild(modal);
                
                const close = () => modal.remove();
                modal.querySelector('.image-modal-close').onclick = close;
                modal.onclick = (e) => { if(e.target === modal) close(); };
            };
        });
    }

    // Enviar com Enter (sem Shift)
    messageInput.addEventListener('keydown', (e) => {
        if(e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // Inicialização
    bindImageClickEvents();
    scrollToBottom();
});
