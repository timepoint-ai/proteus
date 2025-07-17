// Dashboard JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    initializeDashboard();
    
    // Setup auto-refresh
    setupAutoRefresh();
    
    // Setup real-time updates
    setupRealTimeUpdates();
    
    // Setup current time display
    setupCurrentTimeDisplay();
});

// Initialize dashboard components
function initializeDashboard() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Setup dropdown menus
    setupDropdowns();
    
    // Setup keyboard shortcuts
    setupKeyboardShortcuts();
}

// Setup auto-refresh functionality
function setupAutoRefresh() {
    // Auto-refresh every 30 seconds
    setInterval(function() {
        refreshDashboardData();
    }, 30000);
}

// Setup real-time updates
function setupRealTimeUpdates() {
    // Check for updates every 10 seconds
    setInterval(function() {
        checkForUpdates();
    }, 10000);
}

// Setup current time display
function setupCurrentTimeDisplay() {
    function updateCurrentTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            timeElement.textContent = timeString;
        }
    }
    
    // Update immediately
    updateCurrentTime();
    
    // Update every second
    setInterval(updateCurrentTime, 1000);
}

// Refresh dashboard data
function refreshDashboardData() {
    // Fetch updated statistics
    fetch('/admin/api/stats')
        .then(response => response.json())
        .then(data => {
            updateStatistics(data);
        })
        .catch(error => {
            console.error('Error refreshing dashboard data:', error);
            showNotification('Error refreshing dashboard data', 'error');
        });
        
    // Fetch network health
    fetch('/admin/api/network-health')
        .then(response => response.json())
        .then(data => {
            updateNetworkHealth(data);
        })
        .catch(error => {
            console.error('Error refreshing network health:', error);
        });
        
    // Fetch time status
    fetch('/admin/api/time-status')
        .then(response => response.json())
        .then(data => {
            updateTimeStatus(data);
        })
        .catch(error => {
            console.error('Error refreshing time status:', error);
        });
        
    // Fetch ledger summary
    fetch('/admin/api/ledger-summary')
        .then(response => response.json())
        .then(data => {
            updateLedgerSummary(data);
        })
        .catch(error => {
            console.error('Error refreshing ledger summary:', error);
        });
}

// Update statistics cards
function updateStatistics(data) {
    // Update active nodes
    const activeNodesElement = document.querySelector('[data-stat="active-nodes"]');
    if (activeNodesElement) {
        activeNodesElement.textContent = data.active_nodes || 0;
    }
    
    // Update active bets
    const activeBetsElement = document.querySelector('[data-stat="active-bets"]');
    if (activeBetsElement) {
        activeBetsElement.textContent = data.active_bets || 0;
    }
    
    // Update total stakes
    const totalStakesElement = document.querySelector('[data-stat="total-stakes"]');
    if (totalStakesElement) {
        totalStakesElement.textContent = data.total_stakes || 0;
    }
    
    // Update total transactions
    const totalTransactionsElement = document.querySelector('[data-stat="total-transactions"]');
    if (totalTransactionsElement) {
        totalTransactionsElement.textContent = data.total_transactions || 0;
    }
}

// Update network health display
function updateNetworkHealth(data) {
    const healthPercentage = (data.network_health * 100).toFixed(1);
    
    // Update health percentage
    const healthElements = document.querySelectorAll('[data-health-percentage]');
    healthElements.forEach(element => {
        element.textContent = `${healthPercentage}%`;
    });
    
    // Update progress bar
    const progressBar = document.querySelector('[data-health-progress]');
    if (progressBar) {
        progressBar.style.width = `${healthPercentage}%`;
        
        // Update progress bar color based on health
        progressBar.className = progressBar.className.replace(/(bg-\w+)/, '');
        if (data.network_health > 0.7) {
            progressBar.classList.add('bg-success');
        } else if (data.network_health > 0.3) {
            progressBar.classList.add('bg-warning');
        } else {
            progressBar.classList.add('bg-danger');
        }
    }
    
    // Update online/active nodes
    const onlineNodesElement = document.querySelector('[data-online-nodes]');
    if (onlineNodesElement) {
        onlineNodesElement.textContent = `${data.online_nodes}/${data.active_nodes}`;
    }
}

// Update time status display
function updateTimeStatus(data) {
    const timeElement = document.querySelector('[data-current-time]');
    if (timeElement) {
        timeElement.textContent = data.current_time || 'N/A';
    }
    
    const statusElement = document.querySelector('[data-time-status]');
    if (statusElement) {
        statusElement.textContent = data.sync_status ? data.sync_status.charAt(0).toUpperCase() + data.sync_status.slice(1) : 'Unknown';
        
        // Update status badge color
        statusElement.className = statusElement.className.replace(/(bg-\w+)/, '');
        if (data.sync_status === 'healthy') {
            statusElement.classList.add('bg-success');
        } else {
            statusElement.classList.add('bg-warning');
        }
    }
}

// Update ledger summary display
function updateLedgerSummary(data) {
    const totalEntriesElement = document.querySelector('[data-total-entries]');
    if (totalEntriesElement) {
        totalEntriesElement.textContent = data.total_entries || 0;
    }
    
    const reconciledEntriesElement = document.querySelector('[data-reconciled-entries]');
    if (reconciledEntriesElement) {
        reconciledEntriesElement.textContent = data.reconciled_entries || 0;
    }
    
    const reconciliationRate = (data.reconciliation_rate * 100).toFixed(1);
    const reconciliationElement = document.querySelector('[data-reconciliation-rate]');
    if (reconciliationElement) {
        reconciliationElement.textContent = `${reconciliationRate}%`;
    }
    
    // Update progress bar
    const progressBar = document.querySelector('[data-reconciliation-progress]');
    if (progressBar) {
        progressBar.style.width = `${reconciliationRate}%`;
    }
}

// Check for updates
function checkForUpdates() {
    fetch('/admin/api/updates')
        .then(response => response.json())
        .then(data => {
            if (data.updates_available) {
                showUpdateNotification(data.updates);
            }
        })
        .catch(error => {
            console.error('Error checking for updates:', error);
        });
}

// Show notification
function showNotification(message, type = 'info') {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert ${alertClass} alert-dismissible fade show`;
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the main content
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.insertBefore(alertElement, mainContent.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertElement.parentNode) {
                alertElement.remove();
            }
        }, 5000);
    }
}

// Show update notification
function showUpdateNotification(updates) {
    const updateList = updates.map(update => `<li>${update}</li>`).join('');
    const message = `
        <strong>New Updates Available:</strong>
        <ul>${updateList}</ul>
    `;
    
    showNotification(message, 'info');
}

// Setup dropdown menus
function setupDropdowns() {
    // Add click handlers for dropdown items
    document.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', function(e) {
            // Add loading state
            const icon = this.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-spinner fa-spin me-1';
            }
            
            // Reset icon after 2 seconds
            setTimeout(() => {
                if (icon) {
                    icon.className = icon.className.replace('fa-spinner fa-spin', 'fa-cogs');
                }
            }, 2000);
        });
    });
}

// Setup keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + R: Refresh dashboard
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            refreshDashboardData();
            showNotification('Dashboard refreshed', 'success');
        }
        
        // Ctrl/Cmd + D: Go to dashboard
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
            e.preventDefault();
            window.location.href = '/admin/';
        }
        
        // Ctrl/Cmd + N: Go to network view
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            window.location.href = '/admin/network';
        }
        
        // Ctrl/Cmd + T: Go to transactions view
        if ((e.ctrlKey || e.metaKey) && e.key === 't') {
            e.preventDefault();
            window.location.href = '/admin/transactions';
        }
        
        // Ctrl/Cmd + B: Go to bets view
        if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
            e.preventDefault();
            window.location.href = '/admin/bets';
        }
        
        // Ctrl/Cmd + O: Go to oracles view
        if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
            e.preventDefault();
            window.location.href = '/admin/oracles';
        }
        
        // Ctrl/Cmd + S: Go to time sync view
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            window.location.href = '/admin/time-sync';
        }
    });
}

// Chart utilities
function createLineChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true
            }
        },
        plugins: {
            legend: {
                position: 'bottom'
            }
        }
    };
    
    return new Chart(ctx, {
        type: 'line',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

function createDoughnutChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom'
            }
        }
    };
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

function createBarChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true
            }
        },
        plugins: {
            legend: {
                position: 'bottom'
            }
        }
    };
    
    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

// Utility functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    } else {
        return num.toString();
    }
}

function formatCurrency(amount, currency) {
    const formatted = parseFloat(amount).toFixed(8);
    return `${formatted} ${currency}`;
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds}s`;
    } else if (seconds < 3600) {
        return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

// Export functions for use in templates
window.dashboardUtils = {
    refreshDashboardData,
    showNotification,
    createLineChart,
    createDoughnutChart,
    createBarChart,
    formatNumber,
    formatCurrency,
    formatTimestamp,
    formatDuration
};
