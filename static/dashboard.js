/**
 * Dashboard Script
 * Handles real-time sensor data display
 */

// Configuration
const REFRESH_INTERVAL = 5000; // 5 seconds
let refreshTimer = null;

/**
 * Check if user is authenticated
 */
function checkAuthentication() {
    const token = sessionStorage.getItem('authToken');
    
    if (!token) {
        console.log('No hay token en dashboard');
        redirectToLogin();
        return false;
    }
    
    console.log('Token encontrado en dashboard');
    return true;
}

/**
 * Redirect to login page
 */
function redirectToLogin() {
    window.location.href = 'login.html';
}

/**
 * Fetch latest sensor data from API with fallback for null values
 */
async function fetchLatestData() {
    const token = sessionStorage.getItem('authToken');
    
    if (!token) {
        redirectToLogin();
        return null;
    }

    try {
        const response = await fetch('/api/latest-complete', {
            method: 'GET',
            headers: {
                'Authorization': token,
                'Content-Type': 'application/json'
            }
        });

        if (response.status === 401) {
            // Unauthorized - token invalid or expired
            sessionStorage.removeItem('authToken');
            sessionStorage.removeItem('username');
            redirectToLogin();
            return null;
        }

        if (!response.ok) {
            console.error('Error fetching data:', response.statusText);
            return null;
        }

        const data = await response.json();
        return data;

    } catch (error) {
        console.error('Error fetching latest data:', error);
        return null;
    }
}

/**
 * Update dashboard with sensor data
 * @param {Object} data - Sensor data object
 */
function updateDashboard(data) {
    // Temperature
    updateElement('temp', data.temperature ?? data.temperature_c);
    
    // Humidity
    updateElement('hum', data.humidity ?? data.humidity_pct);
    
    // Corrected PPM
    updateElement('correctedppm', data.correctedppm);
    
    // Soil moisture
    updateElement('soil', data.soil_moisture ?? data.soil_humidity);
    
    // pH level
    updateElement('ph', data.ph);
    
    // Turbidity
    updateElement('turb', data.turbidity ?? data.turbidity_ntu);
}

/**
 * Update individual dashboard element
 * @param {string} elementId - Element ID to update
 * @param {*} value - Value to display
 */
function updateElement(elementId, value) {
    const element = document.getElementById(elementId);
    
    if (!element) {
        console.warn(`Element with id '${elementId}' not found`);
        return;
    }

    // Format value
    if (value === null || value === undefined) {
        element.textContent = '--';
    } else if (typeof value === 'number') {
        element.textContent = value.toFixed(2);
    } else {
        element.textContent = value;
    }
}

/**
 * Load and display sensor data
 */
async function loadDashboardData() {
    const data = await fetchLatestData();
    
    if (data) {
        updateDashboard(data);
    }
}

/**
 * Start automatic data refresh
 */
function startAutoRefresh() {
    // Clear existing timer if any
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }

    // Set up new refresh timer
    refreshTimer = setInterval(loadDashboardData, REFRESH_INTERVAL);
}

/**
 * Stop automatic data refresh
 */
function stopAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
    }
}

/**
 * Initialize dashboard
 */
async function initializeDashboard() {
    console.log('=== Inicializando dashboard ===');
    
    // Check authentication
    const isAuthenticated = await checkAuthentication();
    
    if (!isAuthenticated) {
        return;
    }

    // Load initial data
    await loadDashboardData();

    // Start auto-refresh
    startAutoRefresh();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeDashboard);

// Clean up on page unload
window.addEventListener('beforeunload', stopAutoRefresh);