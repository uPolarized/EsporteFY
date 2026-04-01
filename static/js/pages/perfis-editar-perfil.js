document.addEventListener('DOMContentLoaded', function () {

    /* ════════════════════════════════════════════
       UTILITÁRIOS
    ════════════════════════════════════════════ */
    function isGif(file) {
        if (!file) return false;
        return file.type === 'image/gif' || file.name.toLowerCase().endsWith('.gif');
    }

    function showToastSafe(type, msg, duration) {
        if (typeof window.showToast === 'function') window.showToast(type, msg, duration || 4000);
    }


    /* ════════════════════════════════════════════
       CROP — AVATAR
    ════════════════════════════════════════════ */
    const fileInput       = document.getElementById('id_foto');
    const fileNameDisplay = document.getElementById('file-name-display');
    const removePhotoBtn  = document.querySelector('.remove-photo-btn');
    const clearPhotoInput = document.getElementById('id_foto-clear');
    const avatarPreview   = document.getElementById('avatar-preview-live');
    const previewBadge    = document.getElementById('preview-badge');
    const cropImageEl     = document.getElementById('crop-image');
    const previewCircle   = document.getElementById('crop-preview-circle');

    let avatarCropper = null;
    let avatarFlippedH = false;

    function openAvatarCropper(file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            cropImageEl.src = e.target.result;
            const modal = new bootstrap.Modal(document.getElementById('cropModal'));
            modal.show();
            document.getElementById('cropModal').addEventListener('shown.bs.modal', function handler() {
                if (avatarCropper) { avatarCropper.destroy(); avatarCropper = null; }
                avatarFlippedH = false;
                avatarCropper = new Cropper(cropImageEl, {
                    aspectRatio: 1,
                    viewMode: 1,
                    dragMode: 'move',
                    autoCropArea: 0.85,
                    responsive: true,
                    restore: false,
                    guides: true,
                    highlight: false,
                    preview: previewCircle,
                });
                this.removeEventListener('shown.bs.modal', handler);
            }, { once: true });
        };
        reader.readAsDataURL(file);
    }

    document.getElementById('btn-zoom-in')  .addEventListener('click', () => avatarCropper?.zoom(0.15));
    document.getElementById('btn-zoom-out') .addEventListener('click', () => avatarCropper?.zoom(-0.15));
    document.getElementById('btn-rotate-cw').addEventListener('click', () => avatarCropper?.rotate(90));
    document.getElementById('btn-flip-h')   .addEventListener('click', () => {
        avatarFlippedH = !avatarFlippedH;
        avatarCropper?.scaleX(avatarFlippedH ? -1 : 1);
    });
    document.getElementById('btn-reset').addEventListener('click', () => {
        avatarCropper?.reset(); avatarFlippedH = false;
    });

    document.getElementById('btn-confirmar-crop').addEventListener('click', function () {
        if (!avatarCropper) return;
        avatarCropper.getCroppedCanvas({ width: 512, height: 512, imageSmoothingQuality: 'high' })
            .toBlob(function (blob) {
                const croppedFile = new File([blob], 'foto_perfil.jpg', { type: 'image/jpeg' });
                const dt = new DataTransfer(); dt.items.add(croppedFile);
                fileInput.files = dt.files;
                fileNameDisplay.textContent = 'Foto pronta para envio ✔';
                if (clearPhotoInput) clearPhotoInput.value = '';
                if (avatarPreview) avatarPreview.src = URL.createObjectURL(blob);
                if (previewBadge) previewBadge.style.display = 'block';
                bootstrap.Modal.getInstance(document.getElementById('cropModal')).hide();
            }, 'image/jpeg', 0.92);
    });

    document.getElementById('btn-cancelar-crop').addEventListener('click', () => {
        fileInput.value = '';
        fileNameDisplay.textContent = 'Nenhuma foto selecionada';
    });

    if (fileInput) {
        fileInput.addEventListener('change', function () {
            const file = fileInput.files[0];
            if (!file) return;
            if (isGif(file)) {
                fileNameDisplay.textContent = 'GIF pronto para envio ✔';
                if (clearPhotoInput) clearPhotoInput.value = '';
                if (avatarPreview) avatarPreview.src = URL.createObjectURL(file);
                if (previewBadge) previewBadge.style.display = 'block';
                showToastSafe('info', 'GIF animado selecionado. O recorte foi desativado para preservar a animação.', 4200);
                return;
            }
            openAvatarCropper(file);
        });
    }

    if (removePhotoBtn && clearPhotoInput) {
        removePhotoBtn.addEventListener('click', function () {
            fileInput.value = '';
            fileNameDisplay.textContent = 'Nenhuma foto selecionada';
            clearPhotoInput.value = 'true';
            removePhotoBtn.style.display = 'none';
            if (previewBadge) previewBadge.style.display = 'none';
            if (avatarPreview) avatarPreview.src = '/media/fotos_perfil/default.jpg?v=' + Date.now();
            document.getElementById('current-photo-status').textContent = 'Nenhuma imagem (salve para confirmar).';
        });
    }

    const currentFileLink = document.querySelector('.current-photo-link');
    if (currentFileLink && !fileInput.files.length)
        fileNameDisplay.textContent = 'Foto atual definida';


    /* ════════════════════════════════════════════
       BANNER — VARIÁVEIS
    ════════════════════════════════════════════ */
    const bannerInput    = document.getElementById('id_banner');
    const bannerClearInp = document.getElementById('id_banner_clear');
    const bannerPosInp   = document.getElementById('id_banner_position');
    const bannerDropZone = document.getElementById('banner-drop-zone');
    const bannerPreview  = document.getElementById('banner-preview-img');
    const bannerPlaceholder = document.getElementById('banner-placeholder');
    const bannerGifBadge = document.getElementById('banner-gif-badge');
    const bannerPosTag   = document.getElementById('position-tag');
    const gifDragHint    = document.getElementById('gif-drag-hint');
    const btnCropBanner  = document.getElementById('btn-crop-banner');
    const btnRemoveBanner = document.getElementById('btn-remove-banner');

    let bannerCropper = null;
    let bannerFlippedH = false;
    let bannerIsGif = false;

    const hasInitialBanner = bannerDropZone && bannerDropZone.classList.contains('has-image');
    const hasInitialGifBanner = bannerDropZone && bannerDropZone.dataset.initialGif === '1';
    if (hasInitialBanner) {
        bannerIsGif = hasInitialGifBanner;
        bannerGifBadge.classList.toggle('visible', hasInitialGifBanner);
        gifDragHint.style.display = hasInitialGifBanner ? 'block' : 'none';
        btnCropBanner.style.display = hasInitialGifBanner ? 'none' : 'inline-flex';
        btnRemoveBanner.style.display = 'inline-flex';
    }

    /* ── Activar estado "tem imagem" ── */
    function activateBannerPreview(src, isGifFile) {
        bannerIsGif = isGifFile || false;
        bannerPreview.src = src;
        bannerPreview.classList.add('visible');
        bannerDropZone.classList.add('has-image');
        bannerPlaceholder.style.display = 'none';
        bannerGifBadge.classList.toggle('visible', bannerIsGif);
        gifDragHint.style.display = bannerIsGif ? 'block' : 'none';
        // Botão de recorte só faz sentido para imagem estática
        btnCropBanner.style.display = bannerIsGif ? 'none' : 'inline-flex';
        btnRemoveBanner.style.display = 'inline-flex';
        bannerClearInp.value = '';
    }

    /* ── Desativar banner ── */
    function deactivateBannerPreview() {
        bannerPreview.src = '';
        bannerPreview.classList.remove('visible');
        bannerDropZone.classList.remove('has-image');
        bannerPlaceholder.style.display = '';
        bannerGifBadge.classList.remove('visible');
        gifDragHint.style.display = 'none';
        btnCropBanner.style.display = 'none';
        btnRemoveBanner.style.display = 'none';
        bannerPosTag.textContent = 'pos: 50% 50%';
        bannerPreview.style.objectPosition = '50% 50%';
        bannerPosInp.value = '50% 50%';
        bannerIsGif = false;
    }

    /* ── Upload do banner ── */
    bannerInput.addEventListener('change', function () {
        const file = bannerInput.files[0];
        if (!file) return;

        const isGifFile = isGif(file);
        const objectURL = URL.createObjectURL(file);

        if (isGifFile) {
            // GIF: não recorta — só seta preview + permite drag para reposicionar
            activateBannerPreview(objectURL, true);
            showToastSafe('info', 'GIF animado carregado! Arraste no preview para ajustar a posição.', 4500);
        } else {
            // Imagem estática: abre o cropper
            activateBannerPreview(objectURL, false);
            openBannerCropper(file);
        }
    });

    /* ── Clique na zona do banner abre o file picker (sem arrastar) ── */
    bannerDropZone.addEventListener('click', function (e) {
        // Se já tem imagem, o clique é para drag — não abre picker
        if (bannerDropZone.classList.contains('has-image')) return;
        bannerInput.click();
    });

    /* ── Botão Recortar Banner ── */
    btnCropBanner.addEventListener('click', function () {
        if (!bannerInput.files[0]) return;
        openBannerCropper(bannerInput.files[0]);
    });

    /* ── Botão Remover Banner ── */
    btnRemoveBanner.addEventListener('click', function () {
        bannerInput.value = '';
        bannerClearInp.value = 'true';
        deactivateBannerPreview();
        showToastSafe('info', 'Banner removido. Clique em Salvar para confirmar.', 3500);
    });


    /* ════════════════════════════════════════════
       BANNER — DRAG TO REPOSITION
       Funciona para GIF E para imagem estática
       Não modifica o arquivo — apenas salva object-position
    ════════════════════════════════════════════ */
    let isDraggingBanner = false;
    let dragStartX = 0, dragStartY = 0;
    let currentPosX = 50, currentPosY = 50; // em %

    function parseBannerPosition() {
        const val = bannerPosInp.value || '50% 50%';
        const parts = val.split(' ');
        currentPosX = parseFloat(parts[0]) || 50;
        currentPosY = parseFloat(parts[1]) || 50;
    }
    parseBannerPosition();

    function updateBannerPosition(px, py) {
        const x = Math.min(100, Math.max(0, px));
        const y = Math.min(100, Math.max(0, py));
        currentPosX = x; currentPosY = y;
        const val = x.toFixed(1) + '% ' + y.toFixed(1) + '%';
        bannerPreview.style.objectPosition = val;
        bannerPosInp.value = val;
        bannerPosTag.textContent = 'pos: ' + val;
    }

    bannerDropZone.addEventListener('mousedown', function (e) {
        if (!bannerDropZone.classList.contains('has-image')) return;
        isDraggingBanner = true;
        dragStartX = e.clientX;
        dragStartY = e.clientY;
        bannerDropZone.style.cursor = 'grabbing';
        e.preventDefault();
    });

    document.addEventListener('mousemove', function (e) {
        if (!isDraggingBanner) return;
        const rect = bannerDropZone.getBoundingClientRect();
        // Sensibilidade: 1px de movimento = 0.15% de mudança na posição
        const sensitivity = 0.15;
        const dx = (dragStartX - e.clientX) * sensitivity;
        const dy = (dragStartY - e.clientY) * sensitivity;
        updateBannerPosition(currentPosX + dx, currentPosY + dy);
        dragStartX = e.clientX;
        dragStartY = e.clientY;
    });

    document.addEventListener('mouseup', function () {
        if (!isDraggingBanner) return;
        isDraggingBanner = false;
        bannerDropZone.style.cursor = bannerDropZone.classList.contains('has-image') ? 'grab' : 'pointer';
    });

    // Touch support (mobile)
    bannerDropZone.addEventListener('touchstart', function (e) {
        if (!bannerDropZone.classList.contains('has-image')) return;
        const t = e.touches[0];
        isDraggingBanner = true;
        dragStartX = t.clientX;
        dragStartY = t.clientY;
        e.preventDefault();
    }, { passive: false });

    document.addEventListener('touchmove', function (e) {
        if (!isDraggingBanner) return;
        const t = e.touches[0];
        const sensitivity = 0.2;
        const dx = (dragStartX - t.clientX) * sensitivity;
        const dy = (dragStartY - t.clientY) * sensitivity;
        updateBannerPosition(currentPosX + dx, currentPosY + dy);
        dragStartX = t.clientX;
        dragStartY = t.clientY;
        e.preventDefault();
    }, { passive: false });

    document.addEventListener('touchend', () => { isDraggingBanner = false; });

    // Aplica a posição salva ao carregar (banner atual)
    if (bannerPreview.classList.contains('visible')) {
        bannerPreview.style.objectPosition = bannerPosInp.value || '50% 50%';
        bannerPosTag.textContent = 'pos: ' + (bannerPosInp.value || '50% 50%');
    }


    /* ════════════════════════════════════════════
       BANNER — CROP (apenas imagens estáticas)
    ════════════════════════════════════════════ */
    function openBannerCropper(file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            const cropImg = document.getElementById('crop-banner-image');
            cropImg.src = e.target.result;
            const modal = new bootstrap.Modal(document.getElementById('cropBannerModal'));
            modal.show();
            document.getElementById('cropBannerModal').addEventListener('shown.bs.modal', function handler() {
                if (bannerCropper) { bannerCropper.destroy(); bannerCropper = null; }
                bannerFlippedH = false;
                bannerCropper = new Cropper(cropImg, {
                    // Proporção do banner: largura ÷ altura ≈ 4.5 (ex: 1350×300)
                    aspectRatio: 4.5,
                    viewMode: 1,
                    dragMode: 'move',
                    autoCropArea: 0.9,
                    responsive: true,
                    restore: false,
                    guides: true,
                    highlight: false,
                    preview: document.getElementById('crop-preview-banner'),
                });
                this.removeEventListener('shown.bs.modal', handler);
            }, { once: true });
        };
        reader.readAsDataURL(file);
    }

    document.getElementById('btn-banner-zoom-in') .addEventListener('click', () => bannerCropper?.zoom(0.1));
    document.getElementById('btn-banner-zoom-out').addEventListener('click', () => bannerCropper?.zoom(-0.1));
    document.getElementById('btn-banner-rotate')  .addEventListener('click', () => bannerCropper?.rotate(90));
    document.getElementById('btn-banner-flip')    .addEventListener('click', () => {
        bannerFlippedH = !bannerFlippedH;
        bannerCropper?.scaleX(bannerFlippedH ? -1 : 1);
    });
    document.getElementById('btn-banner-reset').addEventListener('click', () => {
        bannerCropper?.reset(); bannerFlippedH = false;
    });

    document.getElementById('btn-confirmar-banner-crop').addEventListener('click', function () {
        if (!bannerCropper) return;
        // Gera o canvas com 1350×300 (proporção 4.5:1 — ótimo para banners)
        bannerCropper.getCroppedCanvas({ width: 1350, height: 300, imageSmoothingQuality: 'high' })
            .toBlob(function (blob) {
                const croppedFile = new File([blob], 'banner.jpg', { type: 'image/jpeg' });
                const dt = new DataTransfer(); dt.items.add(croppedFile);
                bannerInput.files = dt.files;

                // Atualiza preview com a imagem recortada
                const previewUrl = URL.createObjectURL(blob);
                activateBannerPreview(previewUrl, false);
                // Reseta posição para centro
                updateBannerPosition(50, 50);
                bannerClearInp.value = '';

                bootstrap.Modal.getInstance(document.getElementById('cropBannerModal')).hide();
                showToastSafe('success', 'Banner ajustado! Arraste para reposicionar se quiser.', 4000);
            }, 'image/jpeg', 0.92);
    });

    document.getElementById('btn-cancelar-banner-crop').addEventListener('click', () => {
        // Se não havia banner anterior, limpa o input
        if (!bannerPreview.classList.contains('visible')) {
            bannerInput.value = '';
            deactivateBannerPreview();
        }
    });

});
