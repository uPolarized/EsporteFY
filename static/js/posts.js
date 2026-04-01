/**
 * Sistema de Posts - Funções Principais
 * Gerencia criação, listagem, likes, comentários e deleção de posts
 */

const PostsManager = {
    state: {
        offset: 0,
        limit: 20,
        filtro: 'todos',
        isLoading: false,
    },

    /**
     * Inicializar o sistema de posts
     */
    init() {
        this.determinarFiltro();
        this.carregarPosts();
        this.setupEventListeners();
    },

    /**
     * Determinar filtro baseado na página atual
     */
    determinarFiltro() {
        const pathname = window.location.pathname;
        const profilePage = document.querySelector('.profile-page[data-profile-user-id]');
        const profileUserId = profilePage?.dataset?.profileUserId;
        
        if (pathname.includes('/meu-perfil/') || pathname.includes('/perfis/me/')) {
            this.state.filtro = 'meu';
        } else if (pathname.includes('/perfis/') && !pathname.includes('/me/')) {
            if (profileUserId && /^\d+$/.test(profileUserId)) {
                this.state.filtro = `usuario_${profileUserId}`;
            } else {
                this.state.filtro = 'todos';
            }
        } else {
            this.state.filtro = 'todos';
        }
    },

    /**
     * Configurar event listeners globais
     */
    setupEventListeners() {
        // Fechar menus ao clicar fora
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.post-menu')) {
                document.querySelectorAll('.post-menu-dropdown.show').forEach(menu => {
                    menu.classList.remove('show');
                });
            }
        });

        // Update character count em tempo real
        const textarea = document.getElementById('postConteudo');
        if (textarea) {
            textarea.addEventListener('input', () => {
                this.updateCharCount();
            });
        }
    },

    /**
     * Carregar posts
     */
    carregarPosts() {
        if (this.state.isLoading) return;
        
        this.state.isLoading = true;
        this.state.offset = 0;
        
        const params = new URLSearchParams({
            filtro: this.state.filtro,
            limite: this.state.limit,
            offset: this.state.offset
        });
        
        fetch(`/social/posts/?${params}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => this.handlePostsResponse(data))
        .catch(error => {
            console.error('Erro ao carregar posts:', error);
            this.showError('Erro ao carregar posts');
        })
        .finally(() => {
            this.state.isLoading = false;
        });
    },

    /**
     * Carregar mais posts
     */
    carregarMaisPosts() {
        if (this.state.isLoading) return;
        
        this.state.isLoading = true;
        
        const params = new URLSearchParams({
            filtro: this.state.filtro,
            limite: this.state.limit,
            offset: this.state.offset
        });
        
        fetch(`/social/posts/?${params}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.posts) {
                this.appendPosts(data.posts);
                this.state.offset += this.state.limit;
                
                // Mostrar/esconder botão de carregar mais
                document.getElementById('loadMoreContainer').style.display = 
                    data.posts.length < this.state.limit ? 'none' : 'block';
            }
        })
        .catch(error => {
            console.error('Erro ao carregar mais posts:', error);
            this.showError('Erro ao carregar mais posts');
        })
        .finally(() => {
            this.state.isLoading = false;
        });
    },

    /**
     * Processar resposta de posts
     */
    handlePostsResponse(data) {
        if (data.success && data.posts) {
            this.renderPosts(data.posts);
            this.state.offset = this.state.limit;
            
            // Controlar visibilidade de botões
            const loadMoreBtn = document.getElementById('loadMoreContainer');
            const emptyState = document.getElementById('emptyState');
            
            if (loadMoreBtn) {
                loadMoreBtn.style.display = data.posts.length < this.state.limit ? 'none' : 'block';
            }
            
            if (emptyState) {
                emptyState.style.display = data.posts.length === 0 ? 'block' : 'none';
            }
        }
    },

    /**
     * Renderizar posts
     */
    renderPosts(posts) {
        const container = document.getElementById('postsList');
        if (!container) return;
        
        container.innerHTML = '';
        posts.forEach(post => {
            container.appendChild(this.createPostElement(post));
        });
    },

    /**
     * Adicionar posts ao final da lista
     */
    appendPosts(posts) {
        const container = document.getElementById('postsList');
        if (!container) return;
        
        posts.forEach(post => {
            container.appendChild(this.createPostElement(post));
        });
    },

    prependPost(post) {
        const container = document.getElementById('postsList');
        if (!container || !post) {
            this.carregarPosts();
            return;
        }

        const emptyState = document.getElementById('emptyState');
        if (emptyState) {
            emptyState.style.display = 'none';
        }

        const postEl = this.createPostElement(post);
        container.prepend(postEl);
    },

    /**
     * Criar elemento HTML de um post
     */
    createPostElement(post) {
        const postDiv = document.createElement('div');
        postDiv.className = 'post-card';
        postDiv.id = `post-${post.id}`;
        postDiv.dataset.isOwner = post.pode_deletar ? '1' : '0';

        const safeUsername = this.escaparHTML(post.autor.username || 'usuario');
        const safeDisplayName = this.escaparHTML(post.autor.nome_exibicao || post.autor.username || 'Usuário');
        const userAvatar = this.sanitizeUrl(post.autor.foto) ||
                          `https://ui-avatars.com/api/?name=${encodeURIComponent(post.autor.username || 'usuario')}&background=random`;
        const profileUrl = `/perfis/usuario/${encodeURIComponent(post.autor.username || '')}/`;
        
        let imageHtml = '';
        if (post.imagem) {
            const postImageUrl = this.sanitizeUrl(post.imagem);
            if (postImageUrl) {
                imageHtml = `<img src="${postImageUrl}" alt="Post image" class="post-image">`;
            }
        }

        let gifHtml = '';
        if (post.gif_url) {
            const postGifUrl = this.sanitizeUrl(post.gif_url);
            if (postGifUrl) {
                gifHtml = `<img src="${postGifUrl}" alt="Post GIF" class="post-image">`;
            }
        }
        
        let menuHtml = '';
        if (post.pode_deletar) {
            const nextVisibility = post.visibilidade === 'amigos' ? 'publico' : 'amigos';
            const visibilityLabel = post.visibilidade === 'amigos' ? 'Tornar público' : 'Somente amigos';
            menuHtml = `
                <div class="post-menu">
                    <button class="post-menu-btn" onclick="PostsManager.toggleMenu(${post.id})">
                        <i class="bi bi-three-dots"></i>
                    </button>
                    <div class="post-menu-dropdown" id="menu-${post.id}">
                        <button class="post-menu-item" onclick="PostsManager.toggleFixarPost(${post.id})">
                            <i class="bi ${post.fixado ? 'bi-pin-angle-fill' : 'bi-pin-angle'}"></i> ${post.fixado ? 'Desafixar post' : 'Fixar post'}
                        </button>
                        <button class="post-menu-item" onclick="PostsManager.atualizarVisibilidade(${post.id}, '${nextVisibility}')">
                            <i class="bi ${post.visibilidade === 'amigos' ? 'bi-globe' : 'bi-people'}"></i> ${visibilityLabel}
                        </button>
                        <button class="post-menu-item delete" onclick="PostsManager.deletarPost(${post.id})">
                            <i class="bi bi-trash"></i> Deletar
                        </button>
                    </div>
                </div>
            `;
        }
        
        postDiv.innerHTML = `
            <div class="post-header">
                <a href="${profileUrl}" class="post-author" data-profile-modal="${post.autor.id || ''}">
                    <img src="${userAvatar}" alt="${safeUsername}" class="post-avatar">
                    <div class="post-author-info">
                        <h6>${safeDisplayName}</h6>
                        <small>@${safeUsername} · ${this.formatarData(post.criado_em)}</small>
                    </div>
                </a>
                ${menuHtml}
            </div>
            
            <div class="post-content">${this.escaparHTML(post.conteudo)}</div>
            
            ${imageHtml}
            ${gifHtml}
            
            <div class="post-actions">
                <button class="post-action-btn" onclick="PostsManager.toggleReplyForm(${post.id})" title="Responder">
                    <i class="bi bi-chat"></i>
                    <span>${post.comentarios_count}</span>
                </button>
                <button class="post-action-btn like-btn" onclick="PostsManager.toggleLike(${post.id}, this)" title="Curtir">
                    <i class="bi ${post.usuario_like ? 'bi-heart-fill active' : 'bi-heart'}"></i>
                    <span>${post.likes_count}</span>
                </button>
            </div>
            
            <div class="comments-section" id="comments-${post.id}" style="display: ${post.comentarios.length > 0 ? 'block' : 'none'};">
                ${post.comentarios.map(comment => `
                    <div class="comment">
                        <img src="${this.sanitizeUrl(comment.autor.foto) || `https://ui-avatars.com/api/?name=${encodeURIComponent(comment.autor.username || 'usuario')}&background=random`}" 
                             alt="${this.escaparHTML(comment.autor.username || 'usuario')}" 
                             style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover; cursor: pointer;"
                             data-profile-modal="${comment.autor.id || ''}">
                        <div class="comment-content">
                            <div class="comment-author" style="cursor: pointer;" data-profile-modal="${comment.autor.id || ''}">@${this.escaparHTML(comment.autor.username || 'usuario')}</div>
                              <div class="comment-text">
                                  ${this.formatCommentText(comment.conteudo)}
                                  ${this.sanitizeUrl(comment.imagem) ? `<div style="margin-top: 8px;"><img src="${this.sanitizeUrl(comment.imagem)}" style="max-width: 100%; border-radius: 8px;" alt="Imagem"></div>` : ''}
                                  ${this.sanitizeUrl(comment.gif_url) ? `<div style="margin-top: 8px;"><img src="${this.sanitizeUrl(comment.gif_url)}" style="max-width: 100%; border-radius: 8px;" alt="GIF" border="1"></div>` : ''}
                              </div>
                              <div class="comment-actions">
                                  <span>${this.formatarData(comment.criado_em)}</span>
                                  <button class="comment-delete-btn" onclick="PostsManager.responderComentario(${post.id}, '${this.escapeJsString(comment.autor.username || 'usuario')}')">Responder</button>
                                  <button class="comment-delete-btn" onclick="PostsManager.toggleLikeComentario(${comment.id}, this)">
                                      <i class="bi ${comment.usuario_like ? 'bi-heart-fill' : 'bi-heart'}" style="${comment.usuario_like ? 'color: var(--x-pink);' : ''}"></i> <span>${comment.likes_count || 0}</span>
                                  </button>
                                  ${post.pode_deletar ? `<button class="comment-delete-btn" onclick="PostsManager.toggleFixarComentario(${comment.id})" title="${comment.fixado ? 'Desafixar' : 'Fixar'}">
                                      <i class="bi ${comment.fixado ? 'bi-pin-fill' : 'bi-pin'}" style="${comment.fixado ? 'color: #ff6b6b;' : ''}"></i>
                                  </button>` : ''}
                                  ${comment.pode_deletar ? `<button class="comment-delete-btn" onclick="PostsManager.deletarComentario(${comment.id})">Deletar</button>` : ''}
                              </div>
                          </div>
                      </div>
                  `).join('')}
              </div>

              <div class="reply-container" id="replyForm-${post.id}" style="display: none; flex-direction: column;">
                  <div class="reply-form">
                      <label for="replyImage-${post.id}" style="cursor: pointer; padding: 0 5px; margin: 0; display: flex; align-items: center; color: var(--text-muted); title: 'Enviar imagem';">
                          <i class="bi bi-image" style="font-size: 1.2rem;"></i>
                      </label>
                      <input type="file" id="replyImage-${post.id}" accept="image/*" style="display: none;" onchange="PostsManager.previewComentarioImagem(${post.id})">
                      
                      <button onclick="PostsManager.abrirGifModal(${post.id})" style="cursor: pointer; padding: 0 5px; margin: 0; background: none; border: none; display: flex; align-items: center; color: var(--text-muted); font-size: 1.2rem;" title="Enviar GIF">
                          <i class="bi bi-filetype-gif"></i>
                      </button>
                      
                      <input type="text"
                             id="replyInput-${post.id}"
                             placeholder="Responda este post..."
                             maxlength="300"
                             onkeypress="if(event.key==='Enter') PostsManager.enviarComentario(${post.id})">
                      
                      <input type="hidden" id="replyGifUrl-${post.id}" value="">
                      
                      <button onclick="PostsManager.enviarComentario(${post.id})" style="min-width: 40px;">
                          <i class="bi bi-send"></i>
                      </button>
                  </div>
                  <div id="replyImagePreviewBox-${post.id}" style="display:none; padding: 10px; padding-left: 50px;">
                      <div style="position: relative; display: inline-block;">
                          <img id="replyImagePreview-${post.id}" src="" style="max-width: 150px; border-radius: 8px; border: 1px solid var(--border-color);">
                          <button style="position: absolute; top: 5px; right: 5px; background: rgba(0,0,0,0.5); color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; display: flex; align-items: center; justify-content: center;" onclick="PostsManager.removerImagemComentario(${post.id})"><i class="bi bi-x"></i></button>
                      </div>
                  </div>
                  <div id="replyGifPreviewBox-${post.id}" style="display:none; padding: 10px; padding-left: 50px;">
                      <div style="position: relative; display: inline-block;">
                          <img id="replyGifPreview-${post.id}" src="" style="max-width: 150px; border-radius: 8px; border: 1px solid var(--border-color);">
                          <button style="position: absolute; top: 5px; right: 5px; background: rgba(0,0,0,0.5); color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; display: flex; align-items: center; justify-content: center;" onclick="PostsManager.removerGifComentario(${post.id})"><i class="bi bi-x"></i></button>
                      </div>
                  </div>
        `;
        
        return postDiv;
    },

    /**
     * Toggle menu de opções do post
     */
    toggleMenu(postId) {
        const menu = document.getElementById(`menu-${postId}`);
        if (menu) {
            menu.classList.toggle('show');
        }
    },

    /**
     * Toggle formulário de resposta
     */
    toggleReplyForm(postId) {
        const form = document.getElementById(`replyForm-${postId}`);
        if (!form) return;
        
        const isHidden = form.style.display === 'none';
        form.style.display = isHidden ? 'flex' : 'none';
        
        if (isHidden) {
            const input = document.getElementById(`replyInput-${postId}`);
            if (input) {
                input.focus();
                input.setSelectionRange(input.value.length, input.value.length);
            }
        }
    },

    responderComentario(postId, username) {
        const form = document.getElementById(`replyForm-${postId}`);
        if (form && form.style.display === 'none') {
            form.style.display = 'flex';
        }

        const input = document.getElementById(`replyInput-${postId}`);
        if (!input) return;

        const postCard = document.getElementById(`post-${postId}`);
        const isOwnerPost = postCard?.dataset?.isOwner === '1';

        const mention = `@${(username || 'usuario').trim()} `;
        if (!isOwnerPost && !input.value.includes(mention)) {
            input.value = input.value ? `${input.value.trim()} ${mention}` : mention;
        }

        input.focus();
        input.setSelectionRange(input.value.length, input.value.length);
    },

    atualizarVisibilidade(postId, visibilidade) {
        const formData = new FormData();
        formData.append('visibilidade', visibilidade);

        fetch(`/social/post/${postId}/visibilidade/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken'),
            },
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                this.showError(data.error || 'Erro ao atualizar visibilidade');
                return;
            }
            this.carregarPosts();
        })
        .catch(() => this.showError('Erro ao atualizar visibilidade'));
    },

    abrirGifModal(postId) {
        console.log('[PostsManager] Abrindo GIF picker para post:', postId);
        
        // Aguardar se GifPickerV2 ainda não está pronto
        const waitForGifPicker = () => {
            if (window.GifPickerV2) {
                console.log('[PostsManager] GifPickerV2 encontrado, abrindo modal');
                GifPickerV2.abrirModal(postId);
            } else {
                console.warn('[PostsManager] GifPickerV2 ainda não disponível, tentando novamente...');
                setTimeout(waitForGifPicker, 100);
            }
        };
        
        waitForGifPicker();
    },

    selecionarGifFinal(postId, gifUrl) {
        console.log('[PostsManager] GIF selecionado para post/composer:', postId, ':', gifUrl);
        
        // Caso especial: composer
        if (postId === 'composer') {
            const previewBox = document.getElementById('composerGifPreview');
            const gifPreview = document.getElementById('composerGifPreviewImg');
            const gifUrlInput = document.getElementById('composerGifUrl');
            
            if (!previewBox || !gifPreview || !gifUrlInput) {
                console.error('[PostsManager] Elementos de composer não encontrados');
                this.showError('Erro ao adicionar GIF ao post');
                return;
            }
            
            try {
                gifPreview.src = gifUrl;
                gifUrlInput.value = gifUrl;
                previewBox.style.display = 'block';
                console.log('[PostsManager] GIF adicionado ao composer');
                this.showSuccess('GIF adicionado ao post!');
            } catch (error) {
                console.error('[PostsManager] Erro ao adicionar GIF:', error);
                this.showError('Erro ao adicionar GIF');
            }
            return;
        }
        
        // Caso normal: comentário
        const previewBox = document.getElementById(`replyGifPreviewBox-${postId}`);
        const gifPreview = document.getElementById(`replyGifPreview-${postId}`);
        const gifInput = document.getElementById(`replyGifUrl-${postId}`);
        
        if (!previewBox || !gifPreview || !gifInput) {
            console.error('[PostsManager] Elementos de preview não encontrados:', {
                previewBoxId: `replyGifPreviewBox-${postId}`,
                gifPreviewId: `replyGifPreview-${postId}`,
                gifInputId: `replyGifUrl-${postId}`,
                previewBoxFound: !!previewBox,
                gifPreviewFound: !!gifPreview,
                gifInputFound: !!gifInput
            });
            this.showError('Erro ao adicionar GIF (elementos não encontrados)');
            return;
        }
        
        try {
            gifPreview.dataset.expectedGifUrl = gifUrl;
            gifPreview.src = gifUrl;
            gifPreview.onerror = () => {
                // Ignora erro de carga se o GIF já foi limpo/trocado no preview
                if (gifPreview.dataset.expectedGifUrl !== gifUrl || !gifInput.value) {
                    return;
                }
                console.error('[PostsManager] Erro ao carregar GIF:', gifUrl);
                this.showError('Erro ao carregar GIF');
            };
            gifInput.value = gifUrl;
            previewBox.style.display = 'block';
            console.log('[PostsManager] GIF exibido com sucesso');
            this.showSuccess('GIF adicionado!');
        } catch (error) {
            console.error('[PostsManager] Erro ao adicionar GIF:', error);
            this.showError('Erro ao adicionar GIF');
        }
    },

    removerGifComentario(postId) {
        const previewBox = document.getElementById(`replyGifPreviewBox-${postId}`);
        const gifPreview = document.getElementById(`replyGifPreview-${postId}`);
        const gifInput = document.getElementById(`replyGifUrl-${postId}`);
        if (previewBox) previewBox.style.display = 'none';
        if (gifPreview) {
            gifPreview.onerror = null;
            delete gifPreview.dataset.expectedGifUrl;
            gifPreview.src = '';
        }
        if (gifInput) gifInput.value = '';
    },

    /**
     * Toggle like em um post
     */
    toggleLike(postId, button) {
        fetch(`/social/post/${postId}/like/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken'),
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const icon = button.querySelector('i');
                const count = button.querySelector('span');
                icon.classList.toggle('active', data.liked);
                icon.classList.toggle('bi-heart-fill', data.liked);
                icon.classList.toggle('bi-heart', !data.liked);
                count.textContent = data.likes_count;
            }
        })
        .catch(error => console.error('Erro ao dar like:', error));
    },

    /**
     * Toggle like em um comentario
     */
    toggleLikeComentario(comentarioId, button) {
        fetch(`/social/comentario/${comentarioId}/like/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken'),
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const icon = button.querySelector('i');
                const count = button.querySelector('span');
                if (data.liked) {
                    icon.classList.remove('bi-heart');
                    icon.classList.add('bi-heart-fill');
                    icon.style.color = 'var(--x-pink)';
                } else {
                    icon.classList.remove('bi-heart-fill');
                    icon.classList.add('bi-heart');
                    icon.style.color = '';
                }
                count.textContent = data.likes_count;
            }
        })
        .catch(error => console.error('Erro ao dar like no comentário:', error));
    },

    /**
     * Enviar comentario
     */
                previewComentarioImagem(postId) {
        const input = document.getElementById(`replyImage-${postId}`);
        const previewBox = document.getElementById(`replyImagePreviewBox-${postId}`);
        const previewImg = document.getElementById(`replyImagePreview-${postId}`);

        if (input && input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImg.src = e.target.result;
                previewBox.style.display = 'block';
            }
            reader.readAsDataURL(input.files[0]);
        }
    },

    removerImagemComentario(postId) {
        const input = document.getElementById(`replyImage-${postId}`);
        const previewBox = document.getElementById(`replyImagePreviewBox-${postId}`);
        const previewImg = document.getElementById(`replyImagePreview-${postId}`);

        if (input) input.value = '';
        if (previewImg) previewImg.src = '';
        if (previewBox) previewBox.style.display = 'none';
    },

    enviarComentario(postId) {
        const input = document.getElementById(`replyInput-${postId}`);
        const imageInput = document.getElementById(`replyImage-${postId}`);
        const gifInput = document.getElementById(`replyGifUrl-${postId}`);
        if (!input) return;

        const conteudo = input.value.trim();
        const hasImage = imageInput && imageInput.files && imageInput.files.length > 0;
        const gifUrl = gifInput ? gifInput.value.trim() : '';
        const hasGif = !!gifUrl;

        console.log(`[PostsManager] Enviando comentário - postId: ${postId}, conteudo: "${conteudo}", hasImage: ${hasImage}, hasGif: ${hasGif}`);
        console.log('[PostsManager] Estado do GIF no comentário:', {
            gifInputFound: !!gifInput,
            gifUrl,
            gifInputValue: gifInput ? gifInput.value : null,
        });

        if (!conteudo && !hasImage && !hasGif) {
            console.warn('[PostsManager] Sem conteúdo, imagem ou GIF');
            return;
        }

        const formData = new FormData();
        formData.append('conteudo', conteudo);
        
        if (hasImage) {
            formData.append('imagem', imageInput.files[0]);
            console.log('[PostsManager] Adicionando imagem');
        }
        
        if (hasGif) {
            formData.append('gif_url', gifUrl);
            console.log('[PostsManager] Adicionando GIF:', gifUrl);
        }

        fetch(`/social/post/${postId}/comentar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken')
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('[PostsManager] Comentário enviado com sucesso');
                input.value = '';
                this.removerImagemComentario(postId);
                this.removerGifComentario(postId);
                this.adicionarComentarioNoPost(postId, data.comment);
            } else {
                this.showError(data.error || 'Erro ao enviar...');
            }
        })
        .catch(error => {
            console.error('Erro ao enviar...', error);
            this.showError('Erro ao enviar...');
        });
    },

    adicionarComentarioNoPost(postId, comment) {
        const commentsSection = document.getElementById(`comments-${postId}`);
        if (!commentsSection || !comment) {
            this.carregarPosts();
            return;
        }

        // Verificar se o usuário atual é dono do post
        const postCard = document.getElementById(`post-${postId}`);
        const isPostOwner = postCard?.dataset?.isOwner === '1';

        const html = `
            <div class="comment">
                <img src="${this.sanitizeUrl(comment.autor?.foto) || `https://ui-avatars.com/api/?name=${encodeURIComponent(comment.autor?.username || 'usuario')}&background=random`}" 
                     alt="${this.escaparHTML(comment.autor?.username || 'usuario')}" 
                     style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover; cursor: pointer;"
                     data-profile-modal="${comment.autor?.id || ''}">
                <div class="comment-content">
                    <div class="comment-author" style="cursor: pointer;" data-profile-modal="${comment.autor?.id || ''}">@${this.escaparHTML(comment.autor?.username || 'usuario')}</div>
                    <div class="comment-text">
                        ${this.formatCommentText(comment.conteudo || '')}
                        ${this.sanitizeUrl(comment.imagem) ? `<div style="margin-top: 8px;"><img src="${this.sanitizeUrl(comment.imagem)}" style="max-width: 100%; border-radius: 8px;" alt="Imagem"></div>` : ''}
                        ${this.sanitizeUrl(comment.gif_url) ? `<div style="margin-top: 8px;"><img src="${this.sanitizeUrl(comment.gif_url)}" style="max-width: 100%; border-radius: 8px;" alt="GIF"></div>` : ''}
                    </div>
                    <div class="comment-actions">
                        <span>${this.formatarData(comment.criado_em)}</span>
                        <button class="comment-delete-btn" onclick="PostsManager.responderComentario(${postId}, '${this.escapeJsString(comment.autor?.username || 'usuario')}')">Responder</button>
                        <button class="comment-delete-btn" onclick="PostsManager.toggleLikeComentario(${comment.id}, this)">
                            <i class="bi ${comment.usuario_like ? 'bi-heart-fill' : 'bi-heart'}" style="${comment.usuario_like ? 'color: var(--x-pink);' : ''}"></i> <span>${comment.likes_count || 0}</span>
                        </button>
                        ${isPostOwner ? `<button class="comment-delete-btn" onclick="PostsManager.toggleFixarComentario(${comment.id})" title="${comment.fixado ? 'Desafixar' : 'Fixar'}">
                            <i class="bi ${comment.fixado ? 'bi-pin-fill' : 'bi-pin'}" style="${comment.fixado ? 'color: #ff6b6b;' : ''}"></i>
                        </button>` : ''}
                        ${comment.pode_deletar ? `<button class="comment-delete-btn" onclick="PostsManager.deletarComentario(${comment.id})">Deletar</button>` : ''}
                    </div>
                </div>
            </div>
        `;

        commentsSection.insertAdjacentHTML('beforeend', html);
        commentsSection.style.display = 'block';

        const commentsCountSpan = postCard?.querySelector('.post-actions .post-action-btn span');
        if (commentsCountSpan) {
            const current = parseInt(commentsCountSpan.textContent || '0', 10) || 0;
            commentsCountSpan.textContent = String(current + 1);
        }
    },

    /**
     * Deletar comentário
     */
    deletarComentario(comentarioId) {
        this.confirmAction('Excluir este comentário?', 'Confirmar exclusão').then((confirmed) => {
            if (!confirmed) return;

            fetch(`/social/comentario/${comentarioId}/deletar/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.carregarPosts();
                } else {
                    this.showError(data.error || 'Erro ao deletar comentário');
                }
            })
            .catch(error => {
                console.error('Erro ao deletar comentário:', error);
                this.showError('Erro ao deletar comentário');
            });
        });
    },

    /**
     * Fixar/Desafixar comentário
     */
    toggleFixarComentario(comentarioId) {
        fetch(`/social/comentario/${comentarioId}/fixar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken'),
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log(`[PostsManager] Comentário ${data.fixado ? 'fixado' : 'desafixado'}`);
                // Recarregar para refletir a mudança de ordem
                this.carregarPosts();
                this.showSuccess(data.message);
            } else {
                this.showError(data.error || 'Erro ao fixar comentário');
            }
        })
        .catch(error => {
            console.error('Erro ao fixar comentário:', error);
            this.showError('Erro ao fixar comentário');
        });
    },

    toggleFixarPost(postId) {
        fetch(`/social/post/${postId}/fixar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken'),
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.carregarPosts();
                this.showSuccess(data.message);
            } else {
                this.showError(data.error || 'Erro ao fixar post');
            }
        })
        .catch(error => {
            console.error('Erro ao fixar post:', error);
            this.showError('Erro ao fixar post');
        });
    },

    /**
     * Deletar post
     */
    deletarPost(postId) {
        this.confirmAction('Excluir este post? Essa ação não pode ser desfeita.', 'Confirmar exclusão').then((confirmed) => {
            if (!confirmed) return;

            fetch(`/social/post/${postId}/deletar/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const postElement = document.getElementById(`post-${postId}`);
                    if (postElement) {
                        postElement.style.opacity = '0.5';
                        setTimeout(() => {
                            postElement.remove();
                            this.carregarPosts();
                        }, 300);
                    }
                } else {
                    this.showError(data.error || 'Erro ao deletar post');
                }
            })
            .catch(error => {
                console.error('Erro ao deletar post:', error);
                this.showError('Erro ao deletar post');
            });
        });
    },

    /**
     * Update character counter
     */
    updateCharCount() {
        const textarea = document.getElementById('postConteudo');
        const counter = document.getElementById('charCount');
        if (textarea && counter) {
            counter.textContent = textarea.value.length;
        }
    },

    /**
     * Formatar data relativa
     */
    formatarData(data) {
        const date = new Date(data);
        const agora = new Date();
        const diff = Math.floor((agora - date) / 1000);
        
        if (diff < 60) return 'agora';
        if (diff < 3600) return `${Math.floor(diff / 60)}m`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
        if (diff < 604800) return `${Math.floor(diff / 86400)}d`;
        
        return date.toLocaleDateString('pt-BR');
    },

    /**
     * Escapar HTML para prevenir XSS
     */
    escaparHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    formatCommentText(text) {
        let normalized = String(text || '')
            .replace(/\r\n/g, '\n')  // Normaliza CRLF para LF
            .replace(/\r/g, '\n')     // Normaliza CR para LF
            .trim();
        
        // Escapar HTML primeiro (para caracteres perigosos como <, >, &)
        const escaped = this.escaparHTML(normalized);
        
        // Depois converter newlines em <br> tags (após escapar, para não ser escapado)
        const withBreaks = escaped.replace(/\n/g, '<br>');
        
        return withBreaks;
    },

    escapeJsString(value) {
        return String(value || '')
            .replace(/\\/g, '\\\\')
            .replace(/'/g, "\\'")
            .replace(/\n/g, ' ')
            .replace(/\r/g, ' ');
    },

    sanitizeUrl(url) {
        const value = String(url || '').trim();
        if (!value) return '';
        if (value.startsWith('/')) return value;
        if (value.startsWith('http://') || value.startsWith('https://')) return value;
        return '';
    },

    /**
     * Obter CSRF token
     */
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    ensureFeedbackModals() {
        if (!document.getElementById('postsFeedbackModal')) {
            document.body.insertAdjacentHTML('beforeend', `
                <div class="modal fade" id="postsFeedbackModal" tabindex="-1" aria-hidden="true" data-bs-theme="dark">
                    <div class="modal-dialog modal-dialog-centered modal-sm">
                        <div class="modal-content bg-dark text-light border-secondary">
                            <div class="modal-header py-2 border-secondary">
                                <h5 class="modal-title" id="postsFeedbackTitle">Aviso</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Fechar"></button>
                            </div>
                            <div class="modal-body">
                                <p id="postsFeedbackMessage" class="mb-0"></p>
                            </div>
                            <div class="modal-footer py-2 border-secondary">
                                <button type="button" class="btn btn-primary btn-sm" data-bs-dismiss="modal">OK</button>
                            </div>
                        </div>
                    </div>
                </div>
            `);
        }

        if (!document.getElementById('postsConfirmModal')) {
            document.body.insertAdjacentHTML('beforeend', `
                <div class="modal fade" id="postsConfirmModal" tabindex="-1" aria-hidden="true" data-bs-theme="dark">
                    <div class="modal-dialog modal-dialog-centered modal-sm">
                        <div class="modal-content bg-dark text-light border-secondary">
                            <div class="modal-header py-2 border-secondary">
                                <h5 class="modal-title" id="postsConfirmTitle">Confirmar</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Fechar"></button>
                            </div>
                            <div class="modal-body">
                                <p id="postsConfirmMessage" class="mb-0"></p>
                            </div>
                            <div class="modal-footer py-2 border-secondary">
                                <button type="button" class="btn btn-outline-light btn-sm" id="postsConfirmCancel" data-bs-dismiss="modal">Cancelar</button>
                                <button type="button" class="btn btn-danger btn-sm" id="postsConfirmOk">Excluir</button>
                            </div>
                        </div>
                    </div>
                </div>
            `);
        }
    },

    confirmAction(message, title = 'Confirmar') {
        this.ensureFeedbackModals();

        const modalEl = document.getElementById('postsConfirmModal');
        const titleEl = document.getElementById('postsConfirmTitle');
        const msgEl = document.getElementById('postsConfirmMessage');
        const okBtn = document.getElementById('postsConfirmOk');

        if (!modalEl || !window.bootstrap || !okBtn) {
            this.showModalMessage(message, title);
            return Promise.resolve(false);
        }

        if (titleEl) titleEl.textContent = title;
        if (msgEl) msgEl.textContent = message;

        return new Promise((resolve) => {
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

            const onCancel = () => {
                cleanup();
                resolve(false);
            };

            const onOk = () => {
                cleanup();
                modal.hide();
                resolve(true);
            };

            const cleanup = () => {
                okBtn.removeEventListener('click', onOk);
                modalEl.removeEventListener('hidden.bs.modal', onCancel);
            };

            okBtn.addEventListener('click', onOk);
            modalEl.addEventListener('hidden.bs.modal', onCancel, { once: true });
            modal.show();
        });
    },

    showModalMessage(message, title = 'Aviso') {
        this.ensureFeedbackModals();

        const modalEl = document.getElementById('postsFeedbackModal');
        const titleEl = document.getElementById('postsFeedbackTitle');
        const msgEl = document.getElementById('postsFeedbackMessage');

        if (titleEl) titleEl.textContent = title;
        if (msgEl) msgEl.textContent = String(message || 'Ocorreu um erro');

        if (modalEl && window.bootstrap) {
            bootstrap.Modal.getOrCreateInstance(modalEl).show();
        } else {
            console.error(message);
        }
    },

    /**
     * Mostrar mensagem de erro
     */
    showError(message) {
        console.error(message);
        this.showModalMessage(message, 'Erro');
    },

    /**
     * Mostrar mensagem de sucesso
     */
    showSuccess(message) {
        console.log(message);
        // Pode ser customizado com toast notifications
    }
};

// Garantir acesso global para integração com GifPickerV2
window.PostsManager = PostsManager;
console.log('[PostsManager] Exposto em window.PostsManager');

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    PostsManager.init();
});

