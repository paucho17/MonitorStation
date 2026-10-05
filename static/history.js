/**
 * History Page Script
 * Displays historical sensor data in table format
 */

/**
 * Check if user is authenticated
 */
function checkAuthentication() {
    const token = sessionStorage.getItem('authToken');
    
    if (!token) {
        console.log('No hay token en history');
        redirectToLogin();
        return false;
    }
    
    console.log('Token encontrado en history');
    return true;
}

/**
 * Redirect to login page
 */
function redirectToLogin() {
    window.location.href = 'login.html';
}

/**
 * Fetch historical sensor data from API
 */
async function fetchHistoryData() {
    const token = sessionStorage.getItem('authToken');
    
    if (!token) {
        redirectToLogin();
        return null;
    }

    try {
        const response = await fetch('/api/history', {
            method: 'GET',
            headers: {
                'Authorization': token,
                'Content-Type': 'application/json'
            }
        });

        if (response.status === 401) {
            // Unauthorized - token invalid or expired
            sessionStorage.removeItem('authToken');
            redirectToLogin();
            return null;
        }

        if (!response.ok) {
            console.error('Error fetching history:', response.statusText);
            return null;
        }

        const data = await response.json();
        return data;

    } catch (error) {
        console.error('Error fetching history data:', error);
        return null;
    }
}

/**
 * Format date/time string for display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
function formatDateTime(dateString) {
    if (!dateString) return '--';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('es-CO', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    } catch (error) {
        return dateString;
    }
}

/**
 * Format sensor value for display
 * @param {*} value - Sensor value
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted value or '--'
 */
function formatValue(value, decimals = 2) {
    if (value === null || value === undefined) {
        return '--';
    }
    
    if (typeof value === 'number') {
        return value.toFixed(decimals);
    }
    
    return value;
}

/**
 * Populate history table with data
 * @param {Array} historyData - Array of sensor data records
 */
function populateHistoryTable(historyData) {
    const tbody = document.querySelector('#tabla tbody');
    
    if (!tbody) {
        console.error('Table body not found');
        return;
    }

    // Clear existing rows
    tbody.innerHTML = '';

    // Check if data is empty
    if (!historyData || historyData.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = '<td colspan="11">No hay datos disponibles</td>';
        tbody.appendChild(emptyRow);
        return;
    }

    // Create table rows
    historyData.forEach(record => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${formatDateTime(record.received_at)}</td>
            <td>${record.node_id || '--'}</td>
            <td>${formatValue(record.ph)}</td>
            <td>${formatValue(record.turbidity)}</td>
            <td>${formatValue(record.temperature)}</td>
            <td>${formatValue(record.humidity)}</td>
            <td>${formatValue(record.soil_humidity, 0)}</td>
            <td>${formatValue(record.correctedppm)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * Load and display historical data
 */
async function loadHistoryData() {
    const historyData = await fetchHistoryData();
    
    if (historyData) {
        populateHistoryTable(historyData);
    }
}

/**
 * Initialize history page
 */
function initializeHistoryPage() {
    console.log('Inicializando página de histórico...');
    
    // Check authentication
    const isAuthenticated = checkAuthentication();
    
    if (!isAuthenticated) {
        return;
    }

    // Load history data
    loadHistoryData();
    
    // Auto-refresh every 10 seconds
    setInterval(loadHistoryData, 10000);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeHistoryPage);