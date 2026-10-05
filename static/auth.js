/**
 * Authentication Utilities
 * Shared authentication functions for navigation and logout
 */

/**
 * Display username in navigation bar
 */
function displayUsername() {
    const username = sessionStorage.getItem('username');
    const userDisplay = document.getElementById('userDisplay');
    
    console.log('displayUsername() ejecutado');
    console.log('Username en sessionStorage:', username);
    console.log('Elemento userDisplay:', userDisplay);
    
    if (userDisplay) {
        if (username) {
            userDisplay.textContent = username;
            console.log('Username mostrado:', username);
        } else {
            userDisplay.textContent = 'Usuario';
            console.log('No hay username en sessionStorage');
        }
    } else {
        console.error('Elemento userDisplay no encontrado');
    }
}

/**
 * Handle user logout
 */
async function handleLogout() {
    console.log('Iniciando logout...');
    const token = sessionStorage.getItem('authToken');
    
    try {
        // Notify server about logout
        if (token) {
            await fetch('/api/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ token: token })
            });
        }
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        // Clear token and username
        sessionStorage.removeItem('authToken');
        sessionStorage.removeItem('username');
        console.log('Token y usuario eliminados, redirigiendo...');
        window.location.href = 'login.html';
    }
}

/**
 * Initialize logout links and username display on page load
 */
function initializeAuth() {
    console.log('=== Inicializando auth.js ===');
    console.log('sessionStorage completo:', sessionStorage);
    console.log('authToken:', sessionStorage.getItem('authToken'));
    console.log('username:', sessionStorage.getItem('username'));
    
    // Display username
    displayUsername();
    
    // Setup logout link
    const logoutLink = document.getElementById('logoutLink');
    
    if (logoutLink) {
        console.log('Logout link encontrado');
        
        // Remove previous event listeners
        const newLogoutLink = logoutLink.cloneNode(true);
        logoutLink.parentNode.replaceChild(newLogoutLink, logoutLink);
        
        newLogoutLink.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            console.log('Click en logout detectado');
            handleLogout();
        });
    } else {
        console.log('Logout link NO encontrado');
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    console.log('DOM aún cargando, esperando...');
    document.addEventListener('DOMContentLoaded', initializeAuth);
} else {
    // DOM already ready
    console.log('DOM ya está listo');
    initializeAuth();
}