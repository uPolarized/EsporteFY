function validarRecaptcha() {
    const response = grecaptcha.getResponse();
    if (response.length === 0) {
        alert("⚠️ Por favor, confirme que você não é um robô antes de continuar.");
        return false; // bloqueia o envio do formulário
    }
    return true; // permite envio
}
