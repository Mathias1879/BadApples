// Bad Apples Database - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
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

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation enhancement
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const fileSize = (file.size / 1024 / 1024).toFixed(2);
                const maxSize = 16; // 16MB
                
                if (file.size > maxSize * 1024 * 1024) {
                    alert(`File size (${fileSize}MB) exceeds maximum allowed size (${maxSize}MB)`);
                    input.value = '';
                    return;
                }
                
                // Show file info
                const fileInfo = document.createElement('small');
                fileInfo.className = 'form-text text-success';
                fileInfo.textContent = `Selected: ${file.name} (${fileSize}MB)`;
                
                // Remove previous file info
                const existingInfo = input.parentNode.querySelector('.form-text.text-success');
                if (existingInfo) {
                    existingInfo.remove();
                }
                
                input.parentNode.appendChild(fileInfo);
            }
        });
    });

    // Real-time search functionality with AJAX
    const searchInput = document.querySelector('input[name="q"]');
    let searchTimeout;
    
    if (searchInput) {
        // Create search results dropdown
        const searchResultsDiv = document.createElement('div');
        searchResultsDiv.className = 'search-results-dropdown position-absolute bg-white border rounded shadow-lg d-none';
        searchResultsDiv.style.cssText = 'top: 100%; left: 0; right: 0; max-height: 400px; overflow-y: auto; z-index: 1000;';
        searchInput.parentElement.style.position = 'relative';
        searchInput.parentElement.appendChild(searchResultsDiv);
        
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            // Clear previous timeout
            clearTimeout(searchTimeout);
            
            // Hide results if query too short
            if (query.length < 3) {
                searchResultsDiv.classList.add('d-none');
                return;
            }
            
            // Debounce search
            searchTimeout = setTimeout(() => {
                performLiveSearch(query, searchResultsDiv);
            }, 300);
        });
        
        // Hide results when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !searchResultsDiv.contains(e.target)) {
                searchResultsDiv.classList.add('d-none');
            }
        });
    }
    
    async function performLiveSearch(query, resultsDiv) {
        try {
            const response = await fetch(`/api/live_search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.officers.length === 0 && data.incidents.length === 0 && data.vehicles.length === 0) {
                resultsDiv.innerHTML = '<div class="p-3 text-muted"><i class="fas fa-search me-2"></i>No results found</div>';
            } else {
                let html = '<div class="p-2">';
                
                // Officers
                if (data.officers.length > 0) {
                    html += '<div class="mb-2"><strong class="text-muted">Officers</strong></div>';
                    data.officers.forEach(officer => {
                        html += `
                            <a href="/officer/${officer.id}" class="list-group-item list-group-item-action border-0">
                                <i class="fas fa-user me-2"></i>${officer.first_name} ${officer.last_name} 
                                <span class="badge bg-secondary">${officer.badge_number}</span>
                            </a>
                        `;
                    });
                }
                
                // Incidents
                if (data.incidents.length > 0) {
                    html += '<div class="mb-2 mt-2"><strong class="text-muted">Incidents</strong></div>';
                    data.incidents.forEach(incident => {
                        html += `
                            <a href="/officer/${incident.officer_id}" class="list-group-item list-group-item-action border-0">
                                <i class="fas fa-exclamation-triangle me-2 text-danger"></i>${incident.incident_type}
                                <small class="text-muted d-block">${incident.officer_name}</small>
                            </a>
                        `;
                    });
                }
                
                // Vehicles
                if (data.vehicles.length > 0) {
                    html += '<div class="mb-2 mt-2"><strong class="text-muted">Vehicles</strong></div>';
                    data.vehicles.forEach(vehicle => {
                        html += `
                            <a href="/officer/${vehicle.officer_id}" class="list-group-item list-group-item-action border-0">
                                <i class="fas fa-car me-2"></i>${vehicle.make} ${vehicle.model} 
                                <span class="badge bg-info">${vehicle.license_plate || 'No Plate'}</span>
                            </a>
                        `;
                    });
                }
                
                html += '</div>';
                resultsDiv.innerHTML = html;
            }
            
            resultsDiv.classList.remove('d-none');
        } catch (error) {
            console.error('Search error:', error);
            resultsDiv.innerHTML = '<div class="p-3 text-danger"><i class="fas fa-exclamation-circle me-2"></i>Error performing search</div>';
            resultsDiv.classList.remove('d-none');
        }
    }

    // Officer card hover effects
    const officerCards = document.querySelectorAll('.officer-card');
    officerCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        });
    });

    // Evidence download tracking
    const downloadLinks = document.querySelectorAll('a[href*="download_evidence"]');
    downloadLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Track download (could send analytics event)
            console.log('Evidence downloaded:', this.href);
        });
    });

    // Tab switching with smooth transitions
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const target = document.querySelector(this.getAttribute('data-bs-target'));
            if (target) {
                target.style.opacity = '0';
                setTimeout(() => {
                    target.style.opacity = '1';
                }, 150);
            }
        });
    });

    // Form auto-save (localStorage)
    const formInputs = document.querySelectorAll('form input, form textarea, form select');
    formInputs.forEach(input => {
        const formId = input.closest('form').id || 'default-form';
        const inputId = input.name || input.id;
        
        if (inputId) {
            // Load saved data
            const savedValue = localStorage.getItem(`${formId}-${inputId}`);
            if (savedValue && input.type !== 'file') {
                input.value = savedValue;
            }
            
            // Save data on change
            input.addEventListener('input', function() {
                if (this.type !== 'file') {
                    localStorage.setItem(`${formId}-${inputId}`, this.value);
                }
            });
        }
    });

    // Clear form data on successful submission
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            // Clear localStorage after successful submission
            setTimeout(() => {
                const formId = this.id || 'default-form';
                const keys = Object.keys(localStorage);
                keys.forEach(key => {
                    if (key.startsWith(`${formId}-`)) {
                        localStorage.removeItem(key);
                    }
                });
            }, 1000);
        });
    });

    // Loading states for buttons
    const submitButtons = document.querySelectorAll('button[type="submit"], input[type="submit"]');
    submitButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.form && this.form.checkValidity()) {
                this.innerHTML = '<span class="loading"></span> Processing...';
                this.disabled = true;
            }
        });
    });

    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Print functionality
    const printButtons = document.querySelectorAll('.print-btn');
    printButtons.forEach(button => {
        button.addEventListener('click', function() {
            window.print();
        });
    });

    // Export functionality
    const exportButtons = document.querySelectorAll('.export-btn');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const url = this.getAttribute('data-export-url');
            if (url) {
                window.open(url, '_blank');
            }
        });
    });

    // Confirmation dialogs for destructive actions
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Real-time character count for textareas
    const textareas = document.querySelectorAll('textarea[maxlength]');
    textareas.forEach(textarea => {
        const maxLength = parseInt(textarea.getAttribute('maxlength'));
        const counter = document.createElement('small');
        counter.className = 'form-text text-muted';
        counter.textContent = `0/${maxLength} characters`;
        
        textarea.parentNode.appendChild(counter);
        
        textarea.addEventListener('input', function() {
            const currentLength = this.value.length;
            counter.textContent = `${currentLength}/${maxLength} characters`;
            
            if (currentLength > maxLength * 0.9) {
                counter.className = 'form-text text-warning';
            } else if (currentLength > maxLength) {
                counter.className = 'form-text text-danger';
            } else {
                counter.className = 'form-text text-muted';
            }
        });
    });

    // Image preview for file uploads
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Create preview
                    const preview = document.createElement('img');
                    preview.src = e.target.result;
                    preview.className = 'img-thumbnail mt-2';
                    preview.style.maxWidth = '200px';
                    preview.style.maxHeight = '200px';
                    
                    // Remove existing preview
                    const existingPreview = input.parentNode.querySelector('.img-thumbnail');
                    if (existingPreview) {
                        existingPreview.remove();
                    }
                    
                    input.parentNode.appendChild(preview);
                };
                reader.readAsDataURL(file);
            }
        });
    });
});

// Utility functions
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    const toast = createToast(message, type);
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

function createToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    return toast;
}

// Export functions for global use
window.BadApples = {
    showToast: showToast,
    utils: {
        formatDate: function(date) {
            return new Date(date).toLocaleDateString();
        },
        formatCurrency: function(amount) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(amount);
        }
    }
};
