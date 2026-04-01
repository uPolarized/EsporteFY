/**
 * GIF Picker - Sistema de seleção de GIFs para comentários
 * Similar ao Discord/TikTok/Redes Sociais
 */

const GifPicker = {
    state: {
        currentPostId: null,
        selectedGif: null,
        searchQuery: '',
        gifs: [],
        isLoading: false,
    },

    /**
     * Inicializar o GIF Picker
     */
    init() {
        console.log('[GifPicker] Initializing GifPicker...');
        this.createModal();
        console.log('[GifPicker] GifPicker initialization complete');
    },

    /**
     * Criar a modal do GIF Picker
     */
    createModal() {
        if (document.getElementById('gifModal')) {
            console.log('[GifPicker] Modal already exists.');
            return;
        }
        console.log('[GifPicker] Creating modal...');
        
        const modal = document.createElement('div');
        modal.id = 'gifModal';
        modal.className = 'giphy-modal';
        modal.innerHTML = `
            <div class="giphy-modal-content">
                <div class="giphy-modal-header">
                    <h5>Escolha um GIF</h5>
                    <button class="giphy-modal-close" onclick="GifPicker.fecharModal()">
                        <i class="bi bi-x"></i>
                    </button>
                </div>
                <div style="padding: 10px 15px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                    <div style="display: flex; gap: 8px;">
                        <input type="text" id="gifSearchInput" placeholder="Buscar GIFs..." 
                               style="flex: 1; padding: 8px 12px; border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; font-size: 14px; background: rgba(255,255,255,0.05); color: #fff;"
                               onkeypress="if(event.key==='Enter') GifPicker.buscarGifs()">
                        <button onclick="GifPicker.buscarGifs()" style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500;">
                            Buscar
                        </button>
                    </div>
                    <div style="margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap;">
                        <button onclick="GifPicker.buscarGifsTendencia('trending')" style="padding: 6px 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 20px; cursor: pointer; font-size: 12px; color: #fff; transition: all 0.2s;">
                            Tendência
                        </button>
                        <button onclick="GifPicker.buscarGifsTendencia('happy')" style="padding: 6px 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 20px; cursor: pointer; font-size: 12px; color: #fff; transition: all 0.2s;">
                            Feliz
                        </button>
                        <button onclick="GifPicker.buscarGifsTendencia('funny')" style="padding: 6px 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 20px; cursor: pointer; font-size: 12px; color: #fff; transition: all 0.2s;">
                            Engraçado
                        </button>
                        <button onclick="GifPicker.buscarGifsTendencia('love')" style="padding: 6px 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 20px; cursor: pointer; font-size: 12px; color: #fff; transition: all 0.2s;">
                            Amor
                        </button>
                        <button onclick="GifPicker.buscarGifsTendencia('sport')" style="padding: 6px 12px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 20px; cursor: pointer; font-size: 12px; color: #fff; transition: all 0.2s;">
                            Esporte
                        </button>
                    </div>
                </div>
                <div class="giphy-modal-body" id="gifContainer">
                    <div style="text-align: center; padding: 40px; color: rgba(255,255,255,0.5);">
                        Clique em um botão acima ou busque GIFs
                    </div>
                </div>
            </div>
        `;
        
        console.log('[GifPicker] Appending modal to body');
        document.body.appendChild(modal);
        console.log('[GifPicker] Modal added to DOM');
        
        // Fechar ao clicar fora
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.fecharModal();
            }
        });
    },

    /**
     * Abrir modal de GIF
     */
    abrirModal(postId) {
        console.log('[GifPicker] abrirModal called with postId:', postId);
        this.state.currentPostId = postId;
        const modal = document.getElementById('gifModal');
        console.log('[GifPicker] Modal element:', modal);
        if (modal) {
            modal.classList.add('active');
            console.log('[GifPicker] Modal classes after add:', modal.className);
            // Carregar tendências inicial
            this.buscarGifsTendencia('trending');
        } else {
            console.error('[GifPicker] Modal not found in DOM!');
        }
    },

    /**
     * Fechar modal de GIF
     */
    fecharModal() {
        const modal = document.getElementById('gifModal');
        if (modal) {
            modal.classList.remove('active');
        }
    },

    /**
     * Buscar GIFs por termo de busca
     */
    buscarGifs() {
        const searchInput = document.getElementById('gifSearchInput');
        const query = searchInput ? searchInput.value.trim() : '';
        
        if (!query) {
            alert('Digite um termo para buscar');
            return;
        }
        
        this.buscarGifsPorQuery(query);
    },

    /**
     * Buscar GIFs por categorias/tendências
     */
    buscarGifsTendencia(tendencia) {
        const tendenciaTerms = {
            'trending': null,
            'happy': 'happy',
            'funny': 'funny',
            'love': 'love',
            'sport': 'sport'
        };
        
        if (tendenciaTerms[tendencia] === null) {
            this.buscarGifsTrendingApi();
        } else {
            this.buscarGifsPorQuery(tendenciaTerms[tendencia]);
        }
    },

    /**
     * Buscar GIFs trending da API
     */
    buscarGifsTrendingApi() {
        this.state.isLoading = true;
        const container = document.getElementById('gifContainer');
        container.innerHTML = '<div style="text-align: center; padding: 20px; color: rgba(255,255,255,0.6);"><i class="bi bi-hourglass-split"></i> Carregando...</div>';
        
        // Usar GIPHY_API_KEY do Django settings (injetado no HTML)
        const apiKey = window.GIPHY_API_KEY || 'dc6zaTOxFJmzC';
        fetch(`https://api.giphy.com/v1/gifs/trending?limit=40&rating=g&api_key=${apiKey}`)
            .then(response => response.json())
            .then(data => {
                this.state.gifs = data.data || [];
                this.renderizarGifs();
            })
            .catch(error => {
                console.error('Erro ao carregar GIFs trending:', error);
                container.innerHTML = '<div style="text-align: center; padding: 20px; color: #ff6b6b;">Erro ao carregar GIFs</div>';
            })
            .finally(() => {
                this.state.isLoading = false;
            });
    },

    /**
     * Buscar GIFs por query
     */
    buscarGifsPorQuery(query) {
        this.state.isLoading = true;
        const container = document.getElementById('gifContainer');
        container.innerHTML = '<div style="text-align: center; padding: 20px; color: rgba(255,255,255,0.6);"><i class="bi bi-hourglass-split"></i> Buscando...</div>';
        
        const apiKey = window.GIPHY_API_KEY || 'dc6zaTOxFJmzC';
        const params = new URLSearchParams({
            q: query,
            limit: 40,
            rating: 'g',
            api_key: apiKey
        });
        
        fetch(`https://api.giphy.com/v1/gifs/search?${params}`)
            .then(response => response.json())
            .then(data => {
                this.state.gifs = data.data || [];
                if (this.state.gifs.length === 0) {
                    container.innerHTML = '<div style="text-align: center; padding: 20px; color: rgba(255,255,255,0.5);">Nenhum GIF encontrado</div>';
                } else {
                    this.renderizarGifs();
                }
            })
            .catch(error => {
                console.error('Erro ao buscar GIFs:', error);
                container.innerHTML = '<div style="text-align: center; padding: 20px; color: #ff6b6b;">Erro ao buscar GIFs</div>';
            })
            .finally(() => {
                this.state.isLoading = false;
            });
    },

    /**
     * Renderizar grid de GIFs
     */
    renderizarGifs() {
        const container = document.getElementById('gifContainer');
        
        if (this.state.gifs.length === 0) {
            container.innerHTML = '<div style="text-align: center; padding: 20px; color: rgba(255,255,255,0.5);">Nenhum GIF encontrado</div>';
            return;
        }
        
        const grid = document.createElement('div');
        grid.className = 'giphy-grid';
        
        this.state.gifs.forEach(gif => {
            const item = document.createElement('div');
            item.className = 'giphy-item';
            item.style.cursor = 'pointer';
            item.innerHTML = `
                <img src="${gif.images.fixed_height.url}" 
                     alt="${gif.title}" 
                     onclick="GifPicker.selecionarGif('${gif.images.original.url}', '${gif.id}')"
                     style="width: 100%; height: 120px; object-fit: cover; border-radius: 8px;">
            `;
            grid.appendChild(item);
        });
        
        container.innerHTML = '';
        container.appendChild(grid);
    },

    /**
     * Selecionar um GIF
     */
    selecionarGif(gifUrl, gifId) {
        const postId = this.state.currentPostId;
        if (!postId) {
            alert('Erro: Post ID não encontrado');
            return;
        }
        
        // Salvar GIF para enviar depois
        this.state.selectedGif = {
            url: gifUrl,
            id: gifId
        };
        
        // Mostrar preview
        const previewBox = document.getElementById(`replyGifPreviewBox-${postId}`);
        const previewImg = document.getElementById(`replyGifPreview-${postId}`);
        
        if (previewImg) {
            previewImg.src = gifUrl;
            previewBox.style.display = 'block';
        }
        
        // Fechar modal
        this.fecharModal();
        
        // Focar no campo de texto
        const input = document.getElementById(`replyInput-${postId}`);
        if (input) input.focus();
    },

    /**
     * Remover GIF selecionado
     */
    removerGifSelecionado(postId) {
        this.state.selectedGif = null;
        const previewBox = document.getElementById(`replyGifPreviewBox-${postId}`);
        const previewImg = document.getElementById(`replyGifPreview-${postId}`);
        
        if (previewImg) previewImg.src = '';
        if (previewBox) previewBox.style.display = 'none';
    }
};

if (typeof window !== 'undefined') {
    window.GifPicker = GifPicker;
}

// Inicializar ao carregar a página
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => GifPicker.init());
} else {
    GifPicker.init();
}
