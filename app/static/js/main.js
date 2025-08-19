// LITE - Linux Investigation & Triage Environment - Main JavaScript

// Global variables
let loadingOverlay = null;
let currentDataTable = null;

// Initialize when document is ready
$(document).ready(function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize file upload handlers
    initializeFileUpload();
    
    // Initialize form handlers
    initializeFormHandlers();
    
    // Initialize data tables
    initializeDataTables();
    
    // Initialize charts
    initializeCharts();
    
    // Initialize auto-refresh
    initializeAutoRefresh();
    
    // Initialize search functionality
    initializeSearch();
    
    // Auto-hide alerts
    autoHideAlerts();
    
    console.log('LITE application initialized successfully');
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Show loading overlay
 */
function showLoading(message = 'Loading...') {
    if (loadingOverlay) {
        hideLoading();
    }
    
    loadingOverlay = $(`
        <div class="loading-overlay">
            <div class="text-center">
                <div class="loading-spinner"></div>
                <div class="mt-3">
                    <h5>${message}</h5>
                </div>
            </div>
        </div>
    `);
    
    $('body').append(loadingOverlay);
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    if (loadingOverlay) {
        loadingOverlay.remove();
        loadingOverlay = null;
    }
}

/**
 * Format file size in human readable format
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format timestamp to readable format
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info', duration = 5000) {
    const alertId = 'alert-' + Date.now();
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas fa-${getAlertIcon(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('#alerts-container').prepend(alertHtml);
    
    // Auto-hide after duration
    if (duration > 0) {
        setTimeout(() => {
            $(`#${alertId}`).alert('close');
        }, duration);
    }
}

/**
 * Get icon for alert type
 */
function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Auto-hide alerts after 5 seconds
 */
function autoHideAlerts() {
    setTimeout(() => {
        $('.alert').not('.alert-permanent').fadeOut(500, function() {
            $(this).remove();
        });
    }, 5000);
}

/**
 * Initialize file upload functionality
 */
function initializeFileUpload() {
    // File input change handler
    $(document).on('change', 'input[type="file"]', function() {
        const files = this.files;
        const maxSize = 500 * 1024 * 1024; // 500MB
        const allowedTypes = ['.json'];
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            // Check file size
            if (file.size > maxSize) {
                showAlert(`File "${file.name}" is too large. Maximum size is 500MB.`, 'danger');
                this.value = '';
                return;
            }
            
            // Check file type
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
            if (!allowedTypes.includes(fileExtension)) {
                showAlert(`File "${file.name}" has invalid type. Only JSON files are allowed.`, 'danger');
                this.value = '';
                return;
            }
        }
        
        // Update file info display
        updateFileInfo(files);
    });
    
    // Drag and drop handlers
    $(document).on('dragover dragenter', '.file-upload-area', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('dragover');
    });
    
    $(document).on('dragleave dragend', '.file-upload-area', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
    });
    
    $(document).on('drop', '.file-upload-area', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('dragover');
        
        const files = e.originalEvent.dataTransfer.files;
        const fileInput = $(this).find('input[type="file"]')[0];
        
        if (fileInput && files.length > 0) {
            fileInput.files = files;
            $(fileInput).trigger('change');
        }
    });
}

/**
 * Update file info display
 */
function updateFileInfo(files) {
    const fileInfoContainer = $('#file-info');
    if (fileInfoContainer.length === 0) return;
    
    if (files.length === 0) {
        fileInfoContainer.html('<p class="text-muted">No files selected</p>');
        return;
    }
    
    let html = '<div class="selected-files">';
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        html += `
            <div class="file-item d-flex justify-content-between align-items-center p-2 border rounded mb-2">
                <div>
                    <i class="fas fa-file-code text-primary me-2"></i>
                    <strong>${file.name}</strong>
                </div>
                <div class="text-muted">
                    ${formatFileSize(file.size)}
                </div>
            </div>
        `;
    }
    html += '</div>';
    
    fileInfoContainer.html(html);
}

/**
 * Initialize form handlers
 */
function initializeFormHandlers() {
    // Form submission with progress
    $(document).on('submit', 'form[data-async="true"]', function(e) {
        e.preventDefault();
        
        const form = $(this);
        const formData = new FormData(this);
        const url = form.attr('action') || window.location.href;
        const method = form.attr('method') || 'POST';
        
        // Show progress modal if exists
        const progressModal = $('#progressModal');
        if (progressModal.length > 0) {
            progressModal.modal('show');
        } else {
            showLoading('Processing...');
        }
        
        // Submit form via AJAX
        $.ajax({
            url: url,
            method: method,
            data: formData,
            processData: false,
            contentType: false,
            xhr: function() {
                const xhr = new window.XMLHttpRequest();
                
                // Upload progress
                xhr.upload.addEventListener('progress', function(evt) {
                    if (evt.lengthComputable) {
                        const percentComplete = (evt.loaded / evt.total) * 100;
                        updateProgress(percentComplete);
                    }
                }, false);
                
                return xhr;
            },
            success: function(response) {
                handleFormSuccess(response, form);
            },
            error: function(xhr, status, error) {
                handleFormError(xhr, form);
            },
            complete: function() {
                hideLoading();
                if (progressModal.length > 0) {
                    setTimeout(() => {
                        progressModal.modal('hide');
                    }, 1000);
                }
            }
        });
    });
}

/**
 * Update progress bar
 */
function updateProgress(percent) {
    const progressBar = $('.progress-bar');
    const progressText = $('#progress-text');
    
    if (progressBar.length > 0) {
        progressBar.css('width', percent + '%').attr('aria-valuenow', percent);
    }
    
    if (progressText.length > 0) {
        progressText.text(Math.round(percent) + '%');
    }
}

/**
 * Handle form success response
 */
function handleFormSuccess(response, form) {
    if (response.success) {
        showAlert(response.message || 'Operation completed successfully', 'success');
        
        // Redirect if specified
        if (response.redirect) {
            setTimeout(() => {
                window.location.href = response.redirect;
            }, 1500);
        } else {
            // Refresh current page or specific elements
            if (response.refresh) {
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            }
        }
        
        // Reset form if specified
        if (response.reset_form) {
            form[0].reset();
            updateFileInfo([]);
        }
    } else {
        showAlert(response.message || 'Operation failed', 'danger');
    }
}

/**
 * Handle form error response
 */
function handleFormError(xhr, form) {
    let message = 'An error occurred while processing your request';
    
    if (xhr.responseJSON && xhr.responseJSON.message) {
        message = xhr.responseJSON.message;
    } else if (xhr.responseText) {
        try {
            const response = JSON.parse(xhr.responseText);
            message = response.message || message;
        } catch (e) {
            // Use default message
        }
    }
    
    showAlert(message, 'danger');
}

/**
 * Initialize DataTables
 */
function initializeDataTables() {
    // Initialize all tables with class 'data-table'
    $('.data-table').each(function() {
        const table = $(this);
        const config = {
            responsive: true,
            pageLength: 25,
            lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
            order: [[0, 'desc']], // Default sort by first column descending
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ entries",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                infoEmpty: "No entries available",
                infoFiltered: "(filtered from _MAX_ total entries)",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            },
            dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
                 '<"row"<"col-sm-12"tr>>' +
                 '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>'
        };
        
        // Check if table has AJAX source
        const ajaxUrl = table.data('ajax-url');
        if (ajaxUrl) {
            config.ajax = {
                url: ajaxUrl,
                type: 'GET',
                error: function(xhr, error, thrown) {
                    showAlert('Error loading table data: ' + error, 'danger');
                }
            };
            config.serverSide = true;
            config.processing = true;
        }
        
        // Initialize DataTable
        const dataTable = table.DataTable(config);
        
        // Store reference for later use
        if (table.hasClass('main-data-table')) {
            currentDataTable = dataTable;
        }
    });
}

/**
 * Initialize charts
 */
function initializeCharts() {
    // Initialize Chart.js charts
    initializeDashboardCharts();
    initializeCaseCharts();
}

/**
 * Initialize dashboard charts
 */
function initializeDashboardCharts() {
    // Case Status Distribution Chart
    const statusChartCanvas = document.getElementById('caseStatusChart');
    if (statusChartCanvas) {
        const ctx = statusChartCanvas.getContext('2d');
        
        // Get data from data attributes or AJAX
        const chartData = JSON.parse(statusChartCanvas.dataset.chartData || '{}');
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: chartData.labels || ['Active', 'Inactive', 'Closed'],
                datasets: [{
                    data: chartData.data || [0, 0, 0],
                    backgroundColor: [
                        '#27ae60',
                        '#f39c12',
                        '#e74c3c'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Monthly Cases Chart
    const monthlyChartCanvas = document.getElementById('monthlyCasesChart');
    if (monthlyChartCanvas) {
        const ctx = monthlyChartCanvas.getContext('2d');
        
        const chartData = JSON.parse(monthlyChartCanvas.dataset.chartData || '{}');
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels || [],
                datasets: [{
                    label: 'Cases Created',
                    data: chartData.data || [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
}

/**
 * Initialize case-specific charts
 */
function initializeCaseCharts() {
    // Data distribution chart for analysis pages
    const distributionChartCanvas = document.getElementById('dataDistributionChart');
    if (distributionChartCanvas) {
        const ctx = distributionChartCanvas.getContext('2d');
        
        const chartData = JSON.parse(distributionChartCanvas.dataset.chartData || '{}');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels || [],
                datasets: [{
                    label: 'Records',
                    data: chartData.data || [],
                    backgroundColor: 'rgba(52, 152, 219, 0.8)',
                    borderColor: '#3498db',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

/**
 * Initialize auto-refresh functionality
 */
function initializeAutoRefresh() {
    // Auto-refresh dashboard stats every 30 seconds
    if ($('#dashboard-stats').length > 0) {
        setInterval(refreshDashboardStats, 30000);
    }
    
    // Auto-refresh case stats every 60 seconds
    if ($('#case-stats').length > 0) {
        setInterval(refreshCaseStats, 60000);
    }
}

/**
 * Refresh dashboard statistics
 */
function refreshDashboardStats() {
    $.ajax({
        url: '/api/dashboard/stats',
        method: 'GET',
        success: function(data) {
            updateDashboardStats(data);
        },
        error: function() {
            console.log('Failed to refresh dashboard stats');
        }
    });
}

/**
 * Update dashboard statistics display
 */
function updateDashboardStats(data) {
    // Update stat cards
    $('#total-cases').text(data.total_cases || 0);
    $('#active-cases').text(data.active_cases || 0);
    $('#total-ingestions').text(data.total_ingestions || 0);
    $('#data-processed').text(formatFileSize(data.data_processed || 0));
    
    // Update last updated timestamp
    $('#last-updated').text('Last updated: ' + formatTimestamp(new Date()));
}

/**
 * Refresh case statistics
 */
function refreshCaseStats() {
    const caseUuid = $('#case-uuid').val();
    if (!caseUuid) return;
    
    $.ajax({
        url: `/api/cases/${caseUuid}/stats`,
        method: 'GET',
        success: function(data) {
            updateCaseStats(data);
        },
        error: function() {
            console.log('Failed to refresh case stats');
        }
    });
}

/**
 * Update case statistics display
 */
function updateCaseStats(data) {
    $('#total-files').text(data.total_files || 0);
    $('#processed-files').text(data.processed_files || 0);
    $('#failed-files').text(data.failed_files || 0);
    $('#total-records').text(data.total_records || 0);
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    // Global search with debounce
    let searchTimeout;
    $(document).on('input', '#global-search', function() {
        const query = $(this).val();
        
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performGlobalSearch(query);
        }, 500);
    });
    
    // Category search
    $(document).on('input', '#category-search', function() {
        const query = $(this).val();
        
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performCategorySearch(query);
        }, 300);
    });
}

/**
 * Perform global search across case data
 */
function performGlobalSearch(query) {
    if (query.length < 3) return;
    
    const caseUuid = $('#case-uuid').val();
    if (!caseUuid) return;
    
    $.ajax({
        url: `/api/cases/${caseUuid}/search`,
        method: 'GET',
        data: { q: query },
        success: function(data) {
            displaySearchResults(data);
        },
        error: function() {
            showAlert('Search failed. Please try again.', 'danger');
        }
    });
}

/**
 * Perform category-specific search
 */
function performCategorySearch(query) {
    if (currentDataTable) {
        currentDataTable.search(query).draw();
    }
}

/**
 * Display search results
 */
function displaySearchResults(results) {
    const container = $('#search-results');
    if (container.length === 0) return;
    
    if (results.length === 0) {
        container.html('<p class="text-muted">No results found</p>');
        return;
    }
    
    let html = '<div class="search-results">';
    results.forEach(result => {
        html += `
            <div class="search-result-item p-3 border rounded mb-2">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">${result.table}</h6>
                        <p class="mb-1 text-muted">${result.snippet}</p>
                        <small class="text-muted">Match in: ${result.column}</small>
                    </div>
                    <a href="${result.url}" class="btn btn-sm btn-outline-primary">View</a>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    container.html(html);
}

/**
 * Case management functions
 */
function changeStatus(caseUuid, newStatus) {
    if (!confirm(`Are you sure you want to change the case status to ${newStatus}?`)) {
        return;
    }
    
    showLoading('Updating case status...');
    
    $.ajax({
        url: `/cases/${caseUuid}/status`,
        method: 'POST',
        data: {
            status: newStatus,
            csrf_token: $('meta[name=csrf-token]').attr('content')
        },
        success: function(response) {
            if (response.success) {
                showAlert('Case status updated successfully', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showAlert(response.message || 'Failed to update case status', 'danger');
            }
        },
        error: function() {
            showAlert('Error updating case status', 'danger');
        },
        complete: function() {
            hideLoading();
        }
    });
}

/**
 * Delete case with confirmation
 */
function deleteCase(caseUuid, caseName) {
    const confirmMessage = `Are you sure you want to delete the case "${caseName}"?\n\nThis action cannot be undone and will permanently delete all case data including uploaded files and analysis results.`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    showLoading('Deleting case...');
    
    $.ajax({
        url: `/cases/${caseUuid}`,
        method: 'DELETE',
        data: {
            csrf_token: $('meta[name=csrf-token]').attr('content')
        },
        success: function(response) {
            if (response.success) {
                showAlert('Case deleted successfully', 'success');
                setTimeout(() => {
                    window.location.href = '/cases';
                }, 1500);
            } else {
                showAlert(response.message || 'Failed to delete case', 'danger');
            }
        },
        error: function() {
            showAlert('Error deleting case', 'danger');
        },
        complete: function() {
            hideLoading();
        }
    });
}

/**
 * Export data functions
 */
function exportData(format, caseUuid, category = null) {
    let url = `/api/cases/${caseUuid}/export?format=${format}`;
    if (category) {
        url += `&category=${category}`;
    }
    
    showLoading('Preparing export...');
    
    // Create a temporary link to download the file
    const link = document.createElement('a');
    link.href = url;
    link.download = `case_${caseUuid}_${category || 'all'}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setTimeout(() => {
        hideLoading();
        showAlert('Export completed successfully', 'success');
    }, 2000);
}

/**
 * Utility functions
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Copied to clipboard', 'success', 2000);
    }).catch(() => {
        showAlert('Failed to copy to clipboard', 'danger');
    });
}

function viewRowDetails(data) {
    const modal = $('#rowDetailsModal');
    if (modal.length === 0) return;
    
    let html = '<div class="row">';
    for (const [key, value] of Object.entries(data)) {
        html += `
            <div class="col-md-6 mb-3">
                <strong>${key}:</strong><br>
                <span class="text-muted">${value || 'N/A'}</span>
            </div>
        `;
    }
    html += '</div>';
    
    modal.find('.modal-body').html(html);
    modal.modal('show');
}

function viewJsonData(data) {
    const modal = $('#jsonModal');
    if (modal.length === 0) return;
    
    const formattedJson = JSON.stringify(data, null, 2);
    modal.find('#json-content').text(formattedJson);
    modal.modal('show');
}

// Export functions for global access
window.LITE = {
    showLoading,
    hideLoading,
    showAlert,
    formatFileSize,
    formatTimestamp,
    changeStatus,
    deleteCase,
    exportData,
    copyToClipboard,
    viewRowDetails,
    viewJsonData,
    refreshDashboardStats,
    refreshCaseStats
};

console.log('LITE JavaScript library loaded successfully');