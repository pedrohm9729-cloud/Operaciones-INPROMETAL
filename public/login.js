const API_BASE_URL = ''; // Usamos rutas relativas locales para Hostinger.

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const btnSubmit = document.getElementById('btn-submit-login');
    const errorPanel = document.getElementById('error-panel');
    const errorText = document.getElementById('error-text');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Estado de carga
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<span>Verificando...</span>';
        errorPanel.style.display = 'none';
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;

        try {
            const fetchOptions = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            };
            
            // Permitir el paso de cookies de sesión para CORS
            if (API_BASE_URL) {
                fetchOptions.credentials = 'include';
            }

            const response = await fetch(API_BASE_URL + '/api/login.php', fetchOptions);

            const data = await response.json();

            if (response.ok && data.success) {
                // Redirigir al dashboard
                window.location.href = '/index.html';
            } else {
                // Credenciales inválidas
                showError(data.error || 'Credenciales inválidas.');
            }
        } catch (error) {
            console.error('Error de red al intentar login:', error);
            showError('Error de red. Asegúrate de que el servidor está activo.');
        } finally {
            // Restaurar estado del botón
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = '<span>Ingresar al Sistema</span>';
        }
    });

    function showError(message) {
        errorText.innerText = message;
        errorPanel.style.display = 'flex';
    }
});
