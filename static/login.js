/**
 * Login Page Script
 * Handles user authentication
 */

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const errorBox = document.getElementById('error-box');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');

    console.log('Login page cargada');

    /**
     * Handle login form submission
     */
    loginForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        console.log('Formulario de login enviado');

        // Hide previous error messages
        errorBox.style.display = 'none';

        // Get form values
        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        console.log('Intentando login con usuario:', username);

        // Validate inputs
        if (!username || !password) {
            showError('Por favor complete todos los campos');
            return;
        }

        try {
            // Send login request
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            const data = await response.json();
            console.log('Respuesta del servidor:', data);

            if (data.success && data.token) {
                console.log('Login exitoso');
                console.log('Token recibido:', data.token);
                console.log('Username recibido:', data.username);
                
                // Store token and username in sessionStorage
                sessionStorage.setItem('authToken', data.token);
                sessionStorage.setItem('username', data.username);
                
                console.log('Token guardado:', sessionStorage.getItem('authToken'));
                console.log('Username guardado:', sessionStorage.getItem('username'));
                
                // Redirect to dashboard
                console.log('Redirigiendo a index.html...');
                window.location.href = 'index.html';
            } else {
                console.log('Login fallido:', data.message);
                showError(data.message || 'Credenciales incorrectas');
            }

        } catch (error) {
            console.error('Login error:', error);
            showError('Error de conexion con el servidor');
        }
    });

    /**
     * Display error message
     * @param {string} message - Error message to display
     */
    function showError(message) {
        errorBox.textContent = message;
        errorBox.style.display = 'block';
    }
});