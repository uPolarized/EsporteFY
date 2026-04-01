/**
 * GIF Picker V2 - Fluxo Simplificado e Testável
 * Permite selecionar GIFs da Giphy API de forma simples
 */

const GifPickerV2 = {
    state: {
        currentPostId: null,
        selectedGif: null,
        apiKey: window.GIPHY_API_KEY || 'dc6zaTOxFJmzC',
    },

    /**
     * Inicializar GIF Picker
     */
    init() {
        console.log('[GifPickerV2] Inicializando...');
        this.createModal();
        this.attachEventListeners();
        console.log('[GifPickerV2] Inicialização completa');
    },

    /**
     * Criar modal HTML
     */
    createModal() {
        // Verificar se já existe
        if (document.getElementById('gifPickerV2Modal')) {
            console.log('[GifPickerV2] Modal já existe');
            return;
        }

        const html = `
            <div id="gifPickerV2Modal" class="modal fade" tabindex="-1" aria-hidden="true" data-bs-theme="dark">
                <div class="modal-dialog modal-lg modal-dialog-centered">
                    <div class="modal-content bg-dark text-light border-secondary">
                        <div class="modal-header border-bottom border-secondary">
                            <h5 class="modal-title">
                                <i class="bi bi-filetype-gif me-2" style="color: #ff6b6b;"></i>
                                Escolher GIF
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Fechar"></button>
                        </div>

                        <div class="modal-body" style="max-height: 60vh; overflow-y: auto;">
                            <!-- Search Section -->
                            <div class="mb-3">
                                <div class="input-group">
                                    <input type="text" id="gifSearchV2" class="form-control bg-secondary text-light border-secondary" placeholder="Buscar GIFs..." />
                                    <button class="btn btn-primary" type="button" id="gifSearchBtnV2">
                                        <i class="bi bi-search"></i> Buscar
                                    </button>
                                </div>
                            </div>

                            <!-- Trending Categories -->
                            <div class="mb-3">
                                <div class="d-flex gap-2 flex-wrap">
                                    <button class="btn btn-sm btn-outline-info gif-trend-btn" data-trend="trending">
                                        <i class="bi bi-fire"></i> Tendências
                                    </button>
                                    <button class="btn btn-sm btn-outline-info gif-trend-btn" data-trend="happy">
                                        <i class="bi bi-emoji-smile"></i> Feliz
                                    </button>
                                    <button class="btn btn-sm btn-outline-info gif-trend-btn" data-trend="funny">
                                        <i class="bi bi-emoji-laughing"></i> Engraçado
                                    </button>
                                    <button class="btn btn-sm btn-outline-info gif-trend-btn" data-trend="love">
                                        <i class="bi bi-heart"></i> Amor
                                    </button>
                                    <button class="btn btn-sm btn-outline-info gif-trend-btn" data-trend="sport">
                                        <i class="bi bi-trophy"></i> Esporte
                                    </button>
                                </div>
                            </div>

                            <!-- Loading State -->
                            <div id="gifLoadingV2" style="display: none; text-align: center; padding: 20px;">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Carregando...</span>
                                </div>
                            </div>

                            <!-- GIFs Grid -->
                            <div id="gifGridV2" class="row g-2"></div>

                            <!-- No Results -->
                            <div id="gifNoResultsV2" style="display: none; text-align: center; padding: 40px; color: #999;">
                                <i class="bi bi-inbox" style="font-size: 2rem;"></i>
                                <p class="mt-2">Nenhum GIF encontrado</p>
                            </div>
                        </div>

                        <div class="modal-footer border-top border-secondary">
                            <!-- Selected GIF Preview -->
                            <div id="gifPreviewV2" style="display: none; flex: 1;">
                                <img id="gifPreviewImgV2" src="" alt="Preview" style="max-height: 60px; border-radius: 4px;" />
                            </div>
                            <button type="button" class="btn btn-secondary btn-outline-light" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-primary" id="gifSelectBtnV2" disabled>
                                <i class="bi bi-check"></i> Adicionar GIF
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', html);
        console.log('[GifPickerV2] Modal criado no DOM');
    },

    /**
     * Anexar event listeners
     */
    attachEventListeners() {
        const searchBtn = document.getElementById('gifSearchBtnV2');
        const searchInput = document.getElementById('gifSearchV2');
        const trendBtns = document.querySelectorAll('.gif-trend-btn');
        const selectBtn = document.getElementById('gifSelectBtnV2');
        const gridContainer = document.getElementById('gifGridV2');

        // Search button
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.search());
        }

        // Search on Enter
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.search();
            });
        }

        // Trend buttons
        trendBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const trend = btn.dataset.trend;
                this.loadTrend(trend);
            });
        });

        // Select button
        if (selectBtn) {
            selectBtn.addEventListener('click', () => this.confirmSelection());
        }

        // Grid click delegation for GIF selection
        if (gridContainer) {
            gridContainer.addEventListener('click', (e) => {
                const gifItem = e.target.closest('.gif-item-v2');
                if (gifItem) {
                    this.selectGif(gifItem);
                }
            });
        }

        console.log('[GifPickerV2] Event listeners anexados');
    },

    /**
     * Buscar GIFs por termo
     */
    search() {
        const query = document.getElementById('gifSearchV2').value.trim();
        if (!query) {
            if (window.PostsManager && typeof window.PostsManager.showError === 'function') {
                window.PostsManager.showError('Digite um termo para buscar');
            } else {
                console.warn('[GifPickerV2] Digite um termo para buscar');
            }
            return;
        }
        this.loadGifs(`https://api.giphy.com/v1/gifs/search?q=${encodeURIComponent(query)}&limit=40&rating=g&api_key=${this.state.apiKey}`);
    },

    /**
     * Carregar GIFs por tendência
     */
    loadTrend(trend) {
        const queries = {
            trending: 'trending',
            happy: 'happy',
            funny: 'funny',
            love: 'love',
            sport: 'sport'
        };

        if (trend === 'trending') {
            this.loadGifs(`https://api.giphy.com/v1/gifs/trending?limit=40&rating=g&api_key=${this.state.apiKey}`);
        } else {
            this.loadGifs(`https://api.giphy.com/v1/gifs/search?q=${queries[trend]}&limit=40&rating=g&api_key=${this.state.apiKey}`);
        }
    },

    /**
     * Carregar GIFs via API
     */
    loadGifs(url) {
        console.log('[GifPickerV2] Carregando GIFs:', url);

        const loading = document.getElementById('gifLoadingV2');
        const grid = document.getElementById('gifGridV2');
        const noResults = document.getElementById('gifNoResultsV2');

        // Mostrar loading
        loading.style.display = 'block';
        grid.innerHTML = '';
        noResults.style.display = 'none';

        fetch(url)
            .then(r => r.json())
            .then(data => {
                const gifs = data.data || [];
                console.log('[GifPickerV2] Gifs recebidos:', gifs.length);

                if (gifs.length === 0) {
                    noResults.style.display = 'block';
                } else {
                    grid.innerHTML = gifs.map(gif => {
                        // Grid: miniatura leve | Seleção: versão maior para melhor qualidade
                        const previewUrl = gif.images?.fixed_height?.url || gif.images?.preview_gif?.url || gif.images?.original?.url;
                        const selectedUrl = gif.images?.downsized_large?.url || gif.images?.downsized?.url || gif.images?.original?.url || previewUrl;

                        return `
                            <div class="col-6 col-md-3">
                                <div class="gif-item-v2" style="cursor: pointer; border-radius: 8px; overflow: hidden; aspect-ratio: 1; background: #f0f0f0;" data-gif-url="${selectedUrl}">
                                    <img src="${previewUrl}" 
                                         alt="GIF" 
                                         style="width: 100%; height: 100%; object-fit: cover; display: block;">
                                </div>
                            </div>
                        `;
                    }).join('');
                }
            })
            .catch(err => {
                console.error('[GifPickerV2] Erro ao carregar GIFs:', err);
                grid.innerHTML = '<p class="text-danger">Erro ao carregar GIFs</p>';
            })
            .finally(() => {
                loading.style.display = 'none';
            });
    },

    /**
     * Selecionar GIF
     */
    selectGif(gifItem) {
        const url = gifItem.dataset.gifUrl;
        console.log('[GifPickerV2] GIF selecionado:', url);

        // Remover seleção anterior
        document.querySelectorAll('.gif-item-v2').forEach(el => {
            el.style.border = 'none';
        });

        // Marcar como selecionado
        gifItem.style.border = '3px solid #007bff';

        // Atualizar preview
        this.state.selectedGif = url;
        const preview = document.getElementById('gifPreviewV2');
        const previewImg = document.getElementById('gifPreviewImgV2');
        previewImg.src = url;
        preview.style.display = 'block';

        // Ativar botão de select
        document.getElementById('gifSelectBtnV2').disabled = false;
    },

    /**
     * Confirmar seleção
     */
    confirmSelection() {
        console.log('[GifPickerV2] confirmSelection state:', {
            selectedGif: this.state.selectedGif,
            currentPostId: this.state.currentPostId,
            hasWindowPostsManager: !!window.PostsManager,
            hasWindowGifPicker: !!window.GifPickerV2,
        });

        if (!this.state.selectedGif || !this.state.currentPostId) {
            if (window.PostsManager && typeof window.PostsManager.showError === 'function') {
                window.PostsManager.showError('Erro: nenhum GIF selecionado');
            } else {
                console.warn('[GifPickerV2] Erro: nenhum GIF selecionado');
            }
            return;
        }

        console.log('[GifPickerV2] Confirmando seleção:', this.state.selectedGif);

        // Chamar callback
        const manager = window.PostsManager || (typeof PostsManager !== 'undefined' ? PostsManager : null);
        if (manager && typeof manager.selecionarGifFinal === 'function') {
            console.log('[GifPickerV2] Chamando PostsManager.selecionarGifFinal');
            manager.selecionarGifFinal(this.state.currentPostId, this.state.selectedGif);
        } else {
            console.error('[GifPickerV2] PostsManager indisponível ou inválido', {
                managerFound: !!manager,
                hasMethod: !!(manager && manager.selecionarGifFinal),
            });
        }

        // Fechar modal
        if (document.activeElement && typeof document.activeElement.blur === 'function') {
            document.activeElement.blur();
        }
        const modal = bootstrap.Modal.getInstance(document.getElementById('gifPickerV2Modal'));
        if (modal) modal.hide();

        // Limpar
        this.state.selectedGif = null;
    },

    /**
     * Abrir modal
     */
    abrirModal(postId) {
        console.log('[GifPickerV2] Abrindo modal para post:', postId);
        this.state.currentPostId = postId;

        // Reset
        this.state.selectedGif = null;
        document.getElementById('gifGridV2').innerHTML = '';
        document.getElementById('gifPreviewV2').style.display = 'none';
        document.getElementById('gifSelectBtnV2').disabled = true;

        // Abrir modal
        const modal = new bootstrap.Modal(document.getElementById('gifPickerV2Modal'));
        modal.show();

        // Carregar tendências por padrão
        this.loadTrend('trending');
    }
};

// Inicializar quando DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => GifPickerV2.init());
} else {
    GifPickerV2.init();
}

// Expor globalmente para que posts.js consiga acessar
window.GifPickerV2 = GifPickerV2;
console.log('[GifPickerV2] Exposto em window.GifPickerV2');
