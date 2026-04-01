document.querySelectorAll('.toggle-consent').forEach(checkbox => {
    checkbox.addEventListener('change', async function() {
        const tipo = this.dataset.tipo;
        const accepted = this.checked;
        const csrf = this.dataset.csrf;
        const urlTemplate = this.dataset.urlTemplate || '/lgpd/consent/TYPE/';
        
        try {
            const response = await fetch(urlTemplate.replace('TYPE', tipo), {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrf,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `accepted=${accepted}`
            });
            
            if (response.ok) {
                if (typeof window.showToast === 'function') {
                    window.showToast('success', 'Consentimento atualizado com sucesso.', 3500);
                }
            } else {
                this.checked = !this.checked;
                if (typeof window.showToast === 'function') {
                    window.showToast('error', 'Não foi possível atualizar o consentimento.', 4500);
                }
            }
        } catch (error) {
            console.error('Erro ao atualizar consentimento:', error);
            this.checked = !this.checked;
            if (typeof window.showToast === 'function') {
                window.showToast('error', 'Erro de conexão ao atualizar consentimento.', 4500);
            }
        }
    });
});
