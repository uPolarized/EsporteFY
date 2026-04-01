document.addEventListener('DOMContentLoaded', function() {
    const modalEl = document.getElementById('modalCriarPartida');
    if (!modalEl) return;

    let currentStep = 1;
    const totalSteps = 3;

    // Elementos do DOM
    const stepContainer = document.getElementById('wizardStepContainer');
    const btnAvancar = document.getElementById('btnWizardAvancar');
    const btnVoltar = document.getElementById('btnWizardVoltar');
    const btnConfirmar = document.getElementById('btnWizardConfirmar');
    const progressBar = document.getElementById('wizardProgressBar');
    const alertError = document.getElementById('wizardAlertError');
    const errorText = document.getElementById('wizardFormErrorText');
    const step1Error = document.getElementById('step1Error');
    
    // Inputs Principais
    const inputQuadraId = document.getElementById('wizardQuadraId');
    const selectEsporte = document.getElementById('wizardEsporteSelect');
    const inputTitulo = document.querySelector('input[name="titulo"]');
    const inputDataHora = document.getElementById('wizardDataHora');
    const inputVagas = document.getElementById('wizardVagas');

    // Resumo
    const ctxEsporte = document.getElementById('resumoEsporteText');
    const ctxQuadra = document.getElementById('resumoQuadraText');
    const ctxVagas = document.getElementById('resumoVagasText');
    const ctxData = document.getElementById('resumoDataText');

    let loadedData = false;

    // MAPA REAL DE VAGAS POR ESPORTE (Pesquisado)
    // Valores totais padrão considerando os 2 times em jogo.
    const ESPORTE_VAGAS_MAP = {
        'futebol': 22,       // Campo: 11 x 11
        'futsal': 10,        // Quadra: 5 x 5
        'society': 14,       // Sintético: 7 x 7
        'basquete': 10,      // 5 x 5
        'vôlei': 12,         // Quadra: 6 x 6
        'volei': 12,
        'vôlei de areia': 4, // 2 x 2
        'volei de areia': 4,
        'futevôlei': 4,      // 2 x 2
        'futevolei': 4,
        'tênis': 2,          // Simples padrão (mas pode ser 4 pra duplas, 2 é o principal default)
        'tennis': 2,
        'beach tennis': 4,   // Jogado majoritariamente em duplas 2 x 2
        'padel': 4,          // Sempre em duplas 2 x 2
        'handebol': 14       // 7 x 7
    };

    // Ao abrir o modal
    modalEl.addEventListener('show.bs.modal', function() {
        if (currentStep !== 1) resetWizard();
        if (!loadedData) {
            carregarEsportes();
            carregarQuadras();
            loadedData = true;
        }
    });

    // Auto-preencher Vagas baseado no Esporte
    selectEsporte.addEventListener('change', function() {
        if(this.value && this.options[this.selectedIndex]) {
            const esporteNome = this.options[this.selectedIndex].text.toLowerCase().trim();
            
            let foundMatch = false;
            for(const chave in ESPORTE_VAGAS_MAP) {
                if(esporteNome.includes(chave)) {
                    inputVagas.value = ESPORTE_VAGAS_MAP[chave];
                    // Efeito visual de destaque (pisca uma cor)
                    inputVagas.style.backgroundColor = 'rgba(220, 53, 69, 0.2)';
                    setTimeout(() => inputVagas.style.backgroundColor = '', 500);
                    foundMatch = true;
                    break;
                }
            }
            if (!foundMatch && !inputVagas.value) {
                // Se não achar, não faz nada, deixa o usuário digitar.
                inputVagas.value = ''; 
            }
        }
    });

    // Navegação (Avançar/Voltar com Animação)
    btnAvancar.addEventListener('click', function() {
        if (!validarPasso(currentStep)) return;
        
        // Se estiver indo para a etapa 2, injetar a foto da quadra lá em cima
        if (currentStep === 1) {
            const selectedCard = document.querySelector('.quadra-card.selected');
            const quadraHeader = document.getElementById('step2SelectedQuadra');
            if (selectedCard && quadraHeader) {
                const imgEl = selectedCard.querySelector('img');
                const imgUrl = imgEl ? imgEl.src : '';
                const titleEl = selectedCard.querySelector('.card-title');
                const titleObj = titleEl ? titleEl.textContent.trim() : 'Quadra Selecionada';
                
                // Cria um funda que mescla foto do local com o fundo da tela Dark
                // O degrade de baixo pra cima começa transparente e vai esmagando pro Dark do bootstrap (#212529) para "sumir" a bordinha
                quadraHeader.style.backgroundImage = `linear-gradient(to bottom, transparent 0%, rgba(33, 37, 41, 0.7) 40%, rgba(33, 37, 41, 1) 100%), url('${imgUrl}')`;
                quadraHeader.innerHTML = `
                    <div class="position-absolute bottom-0 start-0 w-100 p-2 pb-3 text-center" style="z-index: 2;">
                        <h4 class="text-white fw-bolder mb-1" style="text-shadow: 0 4px 15px rgba(0,0,0,1);"><i class="fa-solid fa-location-dot text-danger me-2"></i>${titleObj}</h4>
                        <span class="badge bg-danger bg-opacity-75 rounded-pill px-3 py-1 shadow-sm"><i class="fa-solid fa-check me-1"></i>Local Selecionado</span>
                    </div>
                `;
            }
        }
        
        currentStep++;
        atualizarUI();
    });

    btnVoltar.addEventListener('click', function() {
        currentStep--;
        atualizarUI();
    });

    // Atualiza a vista fazendo translado horizontal do container
    function atualizarUI() {
        // Zera eventuais vazamentos de scroll interno do HTML/Navegador p/ não bugar a transição
        const mBody = modalEl.querySelector('.modal-body');
        if(mBody) mBody.scrollLeft = mBody.scrollTop = 0;
        stepContainer.scrollLeft = 0;

        // Mover o contêiner no Eixo X
        // Passo 1 = 0%, Passo 2 = -100%, Passo 3 = -200%
        const translateValue = -(currentStep - 1) * 100;
        stepContainer.style.transform = `translateX(${translateValue}%)`;

        // Atualizar barra de progresso (3 steps = (1=33%, 2=66%, 3=100%))
        progressBar.style.width = ((currentStep) / (totalSteps)) * 100 + '%';

        // Botões de fluxo
        if (currentStep === 1) {
            btnVoltar.style.visibility = 'hidden';
            btnAvancar.classList.remove('d-none');
            btnConfirmar.classList.add('d-none');
        } else if (currentStep === totalSteps) {
            btnVoltar.style.visibility = 'visible';
            btnAvancar.classList.add('d-none');
            btnConfirmar.classList.remove('d-none');
            preencherResumo();
        } else {
            btnVoltar.style.visibility = 'visible';
            btnAvancar.classList.remove('d-none');
            btnConfirmar.classList.add('d-none');
        }
        
        alertError.classList.add('d-none');
    }

    function validarPasso(step) {
        if (step === 1) {
            let isValid = true;
            if (!inputQuadraId.value) {
                step1Error.classList.remove('d-none');
                
                // Animação de tremor horizontal na lista de quadras para chamar atenção
                const quadraList = document.getElementById('wizardListaQuadras');
                quadraList.style.transform = 'translateX(10px)';
                setTimeout(() => quadraList.style.transform = 'translateX(-10px)', 100);
                setTimeout(() => quadraList.style.transform = 'translateX(0)', 200);
                
                isValid = false;
            } else {
                step1Error.classList.add('d-none');
            }
            return isValid;
        }

        if (step === 2) {
            let isValid = true;
            
            if (!inputTitulo.value.trim()) {
                inputTitulo.classList.add('is-invalid');
                isValid = false;
            }

            if (!selectEsporte.value) {
                selectEsporte.classList.add('is-invalid');
                isValid = false;
            }

            if (!inputDataHora.value) {
                inputDataHora.classList.add('is-invalid');
                isValid = false;
            } else {
                const selectedDate = new Date(inputDataHora.value);
                if (selectedDate < new Date()) {
                    inputDataHora.classList.add('is-invalid');
                    isValid = false;
                }
            }

            if (!inputVagas.value || inputVagas.value < 2) {
                inputVagas.classList.add('is-invalid');
                isValid = false;
            }
            return isValid;
        }

        return true;
    }

    function preencherResumo() {
        ctxEsporte.textContent = selectEsporte.options[selectEsporte.selectedIndex]?.text || '-';
        
        const selectedCard = document.querySelector('.quadra-card.selected');
        ctxQuadra.textContent = selectedCard ? selectedCard.querySelector('.card-title').textContent.trim() : '-';
        
        ctxVagas.textContent = inputVagas.value + ' vagas totais';
        
        if (inputDataHora.value) {
            const dateObj = new Date(inputDataHora.value);
            ctxData.textContent = dateObj.toLocaleDateString('pt-BR', {day: '2-digit', month: '2-digit'}) + ' às ' + dateObj.toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'});
        }
    }

    function resetWizard() {
        currentStep = 1;
        document.getElementById('formCriarPartida').reset();
        document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        document.querySelectorAll('.quadra-card').forEach(c => c.classList.remove('selected'));
        inputQuadraId.value = '';
        step1Error.classList.add('d-none');
        alertError.classList.add('d-none');
        atualizarUI();
    }

    // Carregar Esportes API
    async function carregarEsportes() {
        try {
            const res = await fetch('/partidas/api/esportes/');
            if(!res.ok) throw new Error('Falha esportes');
            const data = await res.json();
            
            selectEsporte.innerHTML = '<option value="">Selecione um esporte...</option>';
            data.esportes.forEach(e => {
                selectEsporte.innerHTML += `<option value="${e.id}">${e.nome}</option>`;
            });
        } catch(e) {
            console.error(e);
            selectEsporte.innerHTML = '<option value="">Erro ao carregar esportes.</option>';
        }
    }

    // Carregar Quadras API na ROLAGEM HORIZONTAL
    async function carregarQuadras() {
        const container = document.getElementById('wizardListaQuadras');
        try {
            const res = await fetch('/api/quadras/');
            if(!res.ok) throw new Error('Falha quadras');
            const data = await res.json();
            
            const quadras = Array.isArray(data) ? data : (data.results || []);
            
            container.innerHTML = '';
            
            if(quadras.length === 0) {
                container.innerHTML = '<div class="text-muted w-100 text-center py-5">Nenhuma quadra disponível para seleção.</div>';
                return;
            }

            quadras.forEach(q => {
                let imgUrl = '/static/images/quadra-placeholder.jpg';
                if(q.fotos && q.fotos.length > 0) imgUrl = q.fotos[0].imagem;
                
                // Modificado para o Wrapper da Rolagem (flex: 0 0 80%)
                // Layout focado em fotos GRANDES, inspirado em apps nativos premium (Airbnb/Booking)
                const html = `
                <div class="quadra-card-wrapper">
                    <div class="card h-100 quadra-card bg-dark border-0 position-relative shadow-lg" data-id="${q.id}" style="border-radius: 1.5rem;">
                        <div class="position-relative w-100" style="height: 55vh; min-height: 360px; max-height: 480px; border-radius: 1.5rem; overflow: hidden;">
                            <!-- Imagem grande cobrindo 100% da altura do card -->
                            <img src="${imgUrl}" class="w-100 h-100 object-fit-cover" alt="${q.nome}">
                            
                            <!-- Gradiente Escuro Gigante Embaixo - Foca no contraste do texto -->
                            <div class="position-absolute bottom-0 start-0 w-100 p-4 pt-5 d-flex flex-column justify-content-end" 
                                 style="background: linear-gradient(to top, rgba(15,15,15,0.95) 0%, rgba(15,15,15,0.7) 40%, transparent 100%); min-height: 60%;">
                                <h3 class="card-title fw-bolder text-white mb-2" style="text-shadow: 2px 2px 8px rgba(0,0,0,1);">${q.nome}</h3>
                                <p class="card-text text-light mb-0 fs-6 fw-medium d-flex align-items-center">
                                    <i class="fa-solid fa-location-dot me-2 text-danger"></i>
                                    ${q.bairro || 'Localização não informada'}
                                </p>
                            </div>
                            
                            <!-- Checkmark estilizado gigante no canto -->
                            <div class="select-indicator position-absolute top-0 end-0 m-3 bg-danger rounded-circle align-items-center justify-content-center shadow-lg" 
                                 style="width: 44px; height: 44px; border: 3px solid white; z-index: 10;">
                                <i class="fa-solid fa-check text-white fs-4"></i>
                            </div>
                        </div>
                    </div>
                </div>`;
                
                container.insertAdjacentHTML('beforeend', html);
            });

            // Adiciona interação nos cards
            document.querySelectorAll('.quadra-card').forEach(card => {
                card.addEventListener('click', function() {
                    document.querySelectorAll('.quadra-card').forEach(c => c.classList.remove('selected'));
                    this.classList.add('selected');
                    inputQuadraId.value = this.dataset.id;
                    step1Error.classList.add('d-none');
                    
                    // Centraliza o card clicado suavemente calculando o scroll e impedindo que o container vaze
                    const container = document.getElementById('wizardListaQuadras');
                    const wrapper = this.parentElement; // a <div class="quadra-card-wrapper">
                    const targetLeft = wrapper.offsetLeft - (container.offsetWidth / 2) + (wrapper.offsetWidth / 2);
                    container.scrollTo({ left: targetLeft, behavior: 'smooth' });
                });
            });
            
        } catch(e) {
            console.error(e);
            container.innerHTML = '<div class="text-danger w-100 text-center py-5">Não foi possível carregar as quadras disponíveis.</div>';
        }
    }

    // Submit do Form
    btnConfirmar.addEventListener('click', async function() {
        const form = document.getElementById('formCriarPartida');
        const formData = new FormData(form);
        
        btnConfirmar.disabled = true;
        btnConfirmar.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Criando...';
        alertError.classList.add('d-none');

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const result = await response.json();
            
            if((response.ok && result.status === 'success') || result.status === 'success') {
                window.location.href = result.redirect_url || '/';
            } else {
                let errorMsg = result.message || 'Verifique os dados informados.';
                if(result.errors) {
                    errorMsg = typeof result.errors === 'string' ? result.errors : Object.values(result.errors).map(e => e.join(' ')).join(' | ');
                }
                throw new Error(errorMsg);
            }
        } catch(err) {
            console.error(err);
            errorText.textContent = err.message;
            alertError.classList.remove('d-none');
            btnConfirmar.disabled = false;
            btnConfirmar.innerHTML = 'Criar <i class="fa-solid fa-check ms-1"></i>';
        }
    });

    
    // Navegação Fluida pelo TECLADO (Setinhas Left/Right)
    document.addEventListener('keydown', function(e) {
        // Assegura que atua apenas no modal aberto e no Passo 1
        if (!modalEl.classList.contains('show') || currentStep !== 1) return;

        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
            e.preventDefault(); // Impede do ecrã principal rolar
            
            const cards = Array.from(document.querySelectorAll('.quadra-card'));
            if (cards.length === 0) return;

            let currentIndex = cards.findIndex(c => c.classList.contains('selected'));
            
            if (e.key === 'ArrowRight') {
                if (currentIndex === -1) currentIndex = 0;
                else if (currentIndex < cards.length - 1) currentIndex++;
            } else if (e.key === 'ArrowLeft') {
                if (currentIndex === -1) currentIndex = 0;
                else if (currentIndex > 0) currentIndex--;
            }

            // Realiza o foco de forma viva acionando click() que joga pro centro e marca
            cards[currentIndex].click();
        }
    });

// Limpa erros ao digitar
    [inputTitulo, selectEsporte, inputDataHora, inputVagas].forEach(inp => {
        if(inp) {
            inp.addEventListener('input', () => {
                inp.classList.remove('is-invalid');
            });
        }
    });
});
