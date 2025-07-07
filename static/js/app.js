// Main application JavaScript

// Auto-refresh document status for processing documents
document.addEventListener('DOMContentLoaded', function() {
    // Check for processing documents and refresh their status
    const processingDocs = document.querySelectorAll('tr[id^="doc-"] .badge.bg-warning');
    if (processingDocs.length > 0) {
        setInterval(refreshDocumentStatus, 5000); // Refresh every 5 seconds
    }
});

// Refresh document status
async function refreshDocumentStatus() {
    const processingRows = document.querySelectorAll('tr[id^="doc-"] .badge.bg-warning');
    
    for (const badge of processingRows) {
        const row = badge.closest('tr');
        const docId = row.id.replace('doc-', '');
        
        try {
            const response = await fetch(`/api/document/${docId}/status`);
            const data = await response.json();
            
            if (data.status !== 'processing') {
                // Refresh the page to show updated status
                location.reload();
                break;
            }
        } catch (error) {
            console.error('Error refreshing document status:', error);
        }
    }
}

// Refresh documents list
function refreshDocuments() {
    location.reload();
}

// Check models status
async function checkModelsStatus() {
    const modal = new bootstrap.Modal(document.getElementById('modelsStatusModal'));
    const modalBody = document.getElementById('modelsStatusBody');
    
    modal.show();
    
    try {
        const response = await fetch('/api/models/status');
        const data = await response.json();
        
        let statusHtml = '<div class="list-group">';
        
        // Models loaded status
        statusHtml += `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                    <span><i class="fas fa-robot me-2"></i>Models Loaded</span>
                    <span class="badge bg-${data.models_loaded ? 'success' : 'danger'}">
                        ${data.models_loaded ? 'Yes' : 'No'}
                    </span>
                </div>
            </div>
        `;
        
        // Device status
        statusHtml += `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                    <span><i class="fas fa-microchip me-2"></i>Device</span>
                    <span class="badge bg-${data.device === 'cuda' ? 'success' : 'warning'}">
                        ${data.device.toUpperCase()}
                    </span>
                </div>
            </div>
        `;
        
        // GPU availability
        statusHtml += `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                    <span><i class="fas fa-bolt me-2"></i>GPU Available</span>
                    <span class="badge bg-${data.gpu_available ? 'success' : 'warning'}">
                        ${data.gpu_available ? 'Yes' : 'No'}
                    </span>
                </div>
            </div>
        `;
        
        // Embedding model
        statusHtml += `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                    <span><i class="fas fa-vector-square me-2"></i>Embedding Model</span>
                    <span class="badge bg-${data.embedding_model ? 'success' : 'danger'}">
                        ${data.embedding_model || 'Not loaded'}
                    </span>
                </div>
            </div>
        `;
        
        // LLM model
        statusHtml += `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                    <span><i class="fas fa-brain me-2"></i>LLM Model</span>
                    <span class="badge bg-${data.llm_model ? 'success' : 'danger'}">
                        ${data.llm_model || 'Not loaded'}
                    </span>
                </div>
            </div>
        `;
        
        statusHtml += '</div>';
        
        if (!data.models_loaded) {
            statusHtml += `
                <div class="alert alert-warning mt-3">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Models are not loaded. Please check the server logs for details.
                </div>
            `;
        }
        
        modalBody.innerHTML = statusHtml;
        
    } catch (error) {
        modalBody.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error loading models status: ${error.message}
            </div>
        `;
    }
}

// File upload validation
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.querySelector('input[type="file"]');
    const uploadForm = document.getElementById('uploadForm');
    
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const files = Array.from(e.target.files);
            let hasErrors = false;
            
            for (const file of files) {
                // Check file size (16MB limit)
                if (file.size > 16 * 1024 * 1024) {
                    alert(`File "${file.name}" is too large. Maximum size is 16MB.`);
                    hasErrors = true;
                    break;
                }
                
                // Check file type
                if (!file.type.includes('pdf') && !file.name.toLowerCase().endsWith('.pdf')) {
                    alert(`File "${file.name}" is not a PDF. Please select only PDF files.`);
                    hasErrors = true;
                    break;
                }
            }
            
            if (hasErrors) {
                e.target.value = '';
                return;
            }
            
            // Update form text to show number of files selected
            const formText = e.target.parentNode.querySelector('.form-text');
            if (files.length > 1) {
                formText.innerHTML = `<i class="fas fa-info-circle me-1"></i>${files.length} PDF files selected. All will be processed for chat.`;
            } else if (files.length === 1) {
                formText.innerHTML = `<i class="fas fa-info-circle me-1"></i>1 PDF file selected. It will be processed for chat.`;
            }
        });
    }
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const submitBtn = uploadForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Uploading...';
        });
    }
});

// Progress indication for long operations
function showProgress(message) {
    const progressDiv = document.createElement('div');
    progressDiv.className = 'alert alert-info d-flex align-items-center';
    progressDiv.innerHTML = `
        <i class="fas fa-spinner fa-spin me-2"></i>
        ${message}
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(progressDiv, container.firstChild);
    
    return progressDiv;
}

function hideProgress(progressDiv) {
    if (progressDiv && progressDiv.parentNode) {
        progressDiv.parentNode.removeChild(progressDiv);
    }
}

// Error handling for API calls
function handleApiError(error, fallbackMessage = 'An error occurred') {
    console.error('API Error:', error);
    
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${fallbackMessage}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+U for upload (focus file input)
    if (e.ctrlKey && e.key === 'u') {
        e.preventDefault();
        const fileInput = document.querySelector('input[type="file"]');
        if (fileInput) {
            fileInput.click();
        }
    }
    
    // Ctrl+R for refresh
    if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        refreshDocuments();
    }
});
