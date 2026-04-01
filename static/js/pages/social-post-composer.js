// Character counter
const composerTextarea = document.getElementById('postConteudo');
if (composerTextarea) {
    composerTextarea.addEventListener('input', function() {
        const counter = document.getElementById('charCount');
        if (counter) {
            counter.textContent = this.value.length;
        }
    });
}

function showComposerModal(message, title = 'Aviso') {
    const titleEl = document.getElementById('composerFeedbackTitle');
    const msgEl = document.getElementById('composerFeedbackMessage');
    const modalEl = document.getElementById('composerFeedbackModal');

    if (titleEl) titleEl.textContent = title;
    if (msgEl) msgEl.textContent = message;

    if (modalEl && window.bootstrap) {
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    } else {
        console.error('[composer] Bootstrap modal indisponível:', message);
    }
}

// Image preview
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('previewImg').src = e.target.result;
            document.getElementById('imagePreview').style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Remove image
function removerImagem() {
    document.getElementById('postImagem').value = '';
    document.getElementById('imagePreview').style.display = 'none';
}

// Remove GIF from composer
function removerGifComposer() {
    document.getElementById('composerGifPreviewImg').src = '';
    document.getElementById('composerGifPreview').style.display = 'none';
    document.getElementById('composerGifUrl').value = '';
}

// Submit form
function enviarPost(event) {
    event.preventDefault();
    
    const conteudo = document.getElementById('postConteudo').value.trim();
    const visibilidade = document.getElementById('composerVisibilidade')?.value || 'publico';
    const imagem = document.getElementById('postImagem').files[0];
    const gifUrl = document.getElementById('composerGifUrl')?.value || '';
    
    if (!conteudo && !imagem && !gifUrl) {
        showComposerModal('Adicione texto, imagem ou GIF para postar!', 'Campo obrigatório');
        return;
    }
    
    // Show loading state
    document.getElementById('submitPostBtn').disabled = true;
    document.getElementById('postLoadingState').style.display = 'block';
    
    // Create FormData
    const formData = new FormData();
    formData.append('conteudo', conteudo);
    formData.append('visibilidade', visibilidade);
    if (imagem) {
        formData.append('imagem', imagem);
    }
    if (gifUrl) {
        formData.append('gif_url', gifUrl);
    }
    
    // Send request
    const submitUrl = document.getElementById('postComposerForm')?.dataset.postUrl || '/social/posts/criar/';
    console.log('[enviarPost] Enviando para:', submitUrl);
    
    fetch(submitUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        }
    })
    .then(response => {
        console.log('[enviarPost] Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('[enviarPost] Response data:', data);
        
        if (data.success) {
            console.log('[enviarPost] Sucesso! Post criado:', data.post);
            
            // Clear form  
            document.getElementById('postComposerForm').reset();
            document.getElementById('postConteudo').value = '';
            document.getElementById('charCount').textContent = '0';
            document.getElementById('imagePreview').style.display = 'none';
            document.getElementById('postImagem').value = '';
            removerGifComposer();
            
            // Atualização em tempo real sem recarregar página
            if (window.PostsManager && data.post) {
                try {
                    if (typeof window.PostsManager.prependPost === 'function') {
                        console.log('[enviarPost] Chamando prependPost');
                        window.PostsManager.prependPost(data.post);
                    } else {
                        console.warn('[enviarPost] prependPost não é função, recarregando');
                        window.PostsManager.carregarPosts();
                    }
                } catch (error) {
                    console.error('[enviarPost] Erro ao adicionar post:', error);
                    window.PostsManager.carregarPosts();
                }
            } else {
                console.warn('[enviarPost] PostsManager não disponível, recarregando');
                setTimeout(() => {
                    window.PostsManager?.carregarPosts?.();
                }, 500);
            }
        } else {
            showComposerModal('Erro ao postar: ' + (data.error || 'Tente novamente'), 'Falha ao postar');
        }
    })
    .catch(error => {
        console.error('[enviarPost] Erro:', error);
        showComposerModal('Erro ao enviar post', 'Falha de rede');
    })
    .finally(() => {
        document.getElementById('submitPostBtn').disabled = false;
        document.getElementById('postLoadingState').style.display = 'none';
    });
}

function setComposerVisibility(visibilidade) {
    const input = document.getElementById('composerVisibilidade');
    const label = document.getElementById('composerPrivacyLabel');
    const dropdown = document.getElementById('composerPrivacyDropdown');
    if (!input || !label) return;

    input.value = visibilidade === 'amigos' ? 'amigos' : 'publico';
    if (input.value === 'amigos') {
        label.innerHTML = '<i class="bi bi-people me-1"></i>Somente amigos';
    } else {
        label.innerHTML = '<i class="bi bi-globe me-1"></i>Público';
    }

    if (dropdown) {
        dropdown.classList.remove('show');
    }
}


