/**
 * Register Page Script
 * Handles user registration
 */

document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const errorBox = document.getElementById('error-box');
    const successBox = document.getElementById('success-box');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');

    /**
     * Handle registration form submission
     */
    registerForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        // Hide previous messages
        errorBox.style.display = 'none';
        successBox.style.display = 'none';

        // Get form values
        const username = usernameInput.value.trim();
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        // Client-side validations
        if (!username || !password || !confirmPassword) {
            showError('Por favor complete todos los campos');
            return;
        }

        if (username.length < 3) {
            showError('El usuario debe tener al menos 3 caracteres');
            return;
        }

        if (password.length < 6) {
            showError('La contraseña debe tener al menos 6 caracteres');
            return;
        }

        if (password !== confirmPassword) {
            showError('Las contraseñas no coinciden');
            return;
        }

        try {
            // Send registration request
            const response = await fetch('/api/register', {
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

            if (data.success) {
                showSuccess('¡Registro exitoso! Redirigiendo al login...');
                
                // Clear form
                registerForm.reset();
                
                // Redirect to login after 2 seconds
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 2000);
            } else {
                showError(data.message || 'Error en el registro');
            }

        } catch (error) {
            console.error('Registration error:', error);
            showError('Error de conexión con el servidor');
        }
    });

    /**
     * Display error message
     * @param {string} message - Error message to display
     */
    function showError(message) {
        errorBox.textContent = message;
        errorBox.style.display = 'block';
        successBox.style.display = 'none';
    }

    /**
     * Display success message
     * @param {string} message - Success message to display
     */
    function showSuccess(message) {
        successBox.textContent = message;
        successBox.style.display = 'block';
        errorBox.style.display = 'none';
    }
});