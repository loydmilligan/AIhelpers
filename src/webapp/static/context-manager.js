/**
 * JavaScript module for context management UI interactions.
 * 
 * Provides functionality for saving, loading, searching, and managing
 * AI session contexts through the Context Manager interface.
 */

class ContextManager {
    constructor() {
        this.currentContextId = null;
        this.searchTimeout = null;
        this.contextData = {};
        
        this.initializeEventListeners();
        this.loadContextList();
    }
    
    /**
     * Initialize all event listeners for the context management interface
     */
    initializeEventListeners() {
        // Main action buttons
        document.getElementById('save-context-btn')?.addEventListener('click', () => this.showSaveForm());
        document.getElementById('load-context-btn')?.addEventListener('click', () => this.loadContextList());
        
        // Search and filtering
        document.getElementById('context-search')?.addEventListener('input', (e) => this.handleSearch(e));
        document.getElementById('tool-filter')?.addEventListener('change', () => this.loadContextList());
        
        // Save form
        document.getElementById('save-context-form')?.addEventListener('submit', (e) => this.handleSaveContext(e));
        
        // Copy functionality
        document.getElementById('copy-context-btn')?.addEventListener('click', () => this.copyContextToClipboard());
        
        // Global modal close handlers
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideAllModals();
            }
        });
    }
    
    /**
     * Show the context save form
     */
    showSaveForm() {
        const form = document.getElementById('context-save-form');
        if (form) {
            form.style.display = 'block';
            form.scrollIntoView({ behavior: 'smooth' });
            
            // Pre-fill with example data if empty
            const contextDataField = document.getElementById('context-data');
            if (contextDataField && !contextDataField.value.trim()) {
                contextDataField.value = JSON.stringify({
                    conversation: [
                        {
                            role: "user",
                            content: "Help me create a React component"
                        },
                        {
                            role: "assistant", 
                            content: "I'll help you create a React component. What type of component are you looking to build?"
                        }
                    ],
                    code_files: {
                        "src/components/Example.tsx": "import React from 'react';\n\nconst Example: React.FC = () => {\n  return <div>Hello World</div>;\n};\n\nexport default Example;"
                    },
                    project_state: {
                        framework: "React",
                        typescript: true,
                        styling: "CSS Modules"
                    }
                }, null, 2);
            }
        }
    }
    
    /**
     * Hide the context save form
     */
    hideContextForm() {
        const form = document.getElementById('context-save-form');
        if (form) {
            form.style.display = 'none';
        }
    }
    
    /**
     * Handle context save form submission
     */
    async handleSaveContext(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const contextDataText = formData.get('context_data');
        
        try {
            // Parse and validate JSON
            const contextData = JSON.parse(contextDataText);
            
            // Prepare request data
            const requestData = {
                ai_tool: formData.get('ai_tool'),
                title: formData.get('title') || null,
                description: formData.get('description') || null,
                tags: formData.get('tags') ? formData.get('tags').split(',').map(t => t.trim()).filter(t => t) : [],
                context_data: contextData,
                auto_compress: true
            };
            
            this.showStatus('Saving context...', 'info');
            
            const response = await fetch('/api/context/capture', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify(requestData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showStatus(`Context saved successfully! ID: ${result.id}`, 'success');
                this.hideContextForm();
                this.clearSaveForm();
                this.loadContextList();
            } else {
                const error = await response.json();
                this.showStatus(`Failed to save context: ${error.detail}`, 'error');
            }
            
        } catch (error) {
            if (error instanceof SyntaxError) {
                this.showStatus('Invalid JSON in context data field', 'error');
            } else {
                this.showStatus(`Error saving context: ${error.message}`, 'error');
            }
        }
    }
    
    /**
     * Load and display the context list
     */
    async loadContextList() {
        const listContainer = document.getElementById('context-list');
        if (!listContainer) return;
        
        try {
            listContainer.innerHTML = '<div class="loading-message">Loading contexts...</div>';
            
            const searchQuery = document.getElementById('context-search')?.value || '';
            const toolFilter = document.getElementById('tool-filter')?.value || '';
            
            const params = new URLSearchParams({
                limit: '20',
                offset: '0',
                sort_by: 'updated_at',
                sort_order: 'desc'
            });
            
            if (searchQuery) params.append('query', searchQuery);
            if (toolFilter) params.append('ai_tool', toolFilter);
            
            const response = await fetch(`/api/context/search?${params}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                this.renderContextList(result.contexts, result.total_count);
            } else {
                listContainer.innerHTML = '<div class="error-message">Failed to load contexts</div>';
            }
            
        } catch (error) {
            listContainer.innerHTML = '<div class="error-message">Error loading contexts</div>';
        }
    }
    
    /**
     * Render the context list in the UI
     */
    renderContextList(contexts, totalCount) {
        const listContainer = document.getElementById('context-list');
        if (!listContainer) return;
        
        if (contexts.length === 0) {
            listContainer.innerHTML = '<div class="no-contexts">No contexts found. Save your first context to get started!</div>';
            return;
        }
        
        let html = '<div class="context-list-header">';
        html += `<h4>Your Contexts (${totalCount} total)</h4>`;
        html += '</div>';
        
        contexts.forEach(context => {
            const sizeMB = (context.context_size / (1024 * 1024)).toFixed(2);
            const compressionInfo = context.compression_ratio 
                ? ` (${((1 - context.compression_ratio) * 100).toFixed(1)}% compressed)`
                : '';
            
            const createdDate = new Date(context.created_at).toLocaleDateString();
            const updatedDate = new Date(context.updated_at).toLocaleDateString();
            
            html += `
                <div class="context-item" data-context-id="${context.id}">
                    <div class="context-header">
                        <h4 class="context-title">${context.title || 'Untitled Context'}</h4>
                        <span class="context-tool">${context.ai_tool}</span>
                    </div>
                    
                    <div class="context-meta">
                        <span class="context-size">${sizeMB}MB${compressionInfo}</span>
                        <span class="context-dates">
                            Created: ${createdDate}${updatedDate !== createdDate ? ` | Updated: ${updatedDate}` : ''}
                        </span>
                    </div>
                    
                    ${context.description ? `<div class="context-description">${context.description}</div>` : ''}
                    
                    ${context.tags.length > 0 ? `
                        <div class="context-tags">
                            ${context.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                        </div>
                    ` : ''}
                    
                    <div class="context-actions">
                        <button class="btn-preview" onclick="contextManager.previewContext(${context.id})">Preview</button>
                        <button class="btn-restore" onclick="contextManager.restoreContext(${context.id})">Restore</button>
                        <button class="btn-delete" onclick="contextManager.deleteContext(${context.id}, '${context.title || 'Untitled Context'}')">Delete</button>
                    </div>
                </div>
            `;
        });
        
        listContainer.innerHTML = html;
    }
    
    /**
     * Handle search input with debouncing
     */
    handleSearch(event) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.loadContextList();
        }, 500);
    }
    
    /**
     * Preview a context
     */
    async previewContext(contextId) {
        try {
            this.showStatus('Loading context preview...', 'info');
            
            const response = await fetch(`/api/context/preview/${contextId}`, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showContextPreview(result);
                this.hideStatus();
            } else {
                const error = await response.json();
                this.showStatus(`Failed to load preview: ${error.error}`, 'error');
            }
            
        } catch (error) {
            this.showStatus(`Error loading preview: ${error.message}`, 'error');
        }
    }
    
    /**
     * Show context preview modal
     */
    showContextPreview(previewData) {
        const modal = document.getElementById('context-preview-modal');
        const content = document.getElementById('context-preview-content');
        
        if (!modal || !content) return;
        
        const metadata = previewData.metadata;
        const preview = previewData.preview_data;
        
        let html = `
            <div class="context-preview">
                <div class="preview-header">
                    <h4>${metadata.title || 'Untitled Context'}</h4>
                    <span class="context-id">ID: ${metadata.id}</span>
                </div>
                
                <div class="preview-summary">
                    <p>${previewData.summary}</p>
                </div>
                
                <div class="preview-details">
                    <div class="detail-row">
                        <strong>AI Tool:</strong> ${metadata.ai_tool}
                    </div>
                    <div class="detail-row">
                        <strong>Size:</strong> ${(metadata.context_size / (1024*1024)).toFixed(2)}MB
                    </div>
                    <div class="detail-row">
                        <strong>Created:</strong> ${new Date(metadata.created_at).toLocaleString()}
                    </div>
                    <div class="detail-row">
                        <strong>Updated:</strong> ${new Date(metadata.updated_at).toLocaleString()}
                    </div>
                    ${preview.compression_savings ? `
                        <div class="detail-row">
                            <strong>Compression:</strong> ${preview.compression_savings}
                        </div>
                    ` : ''}
                </div>
                
                <div class="preview-content">
                    <h5>Content Preview:</h5>
                    <ul class="content-indicators">
                        <li class="${preview.has_conversation ? 'available' : 'unavailable'}">
                            Conversation History ${preview.has_conversation ? '✓' : '✗'}
                        </li>
                        <li class="${preview.has_code_files ? 'available' : 'unavailable'}">
                            Code Files ${preview.has_code_files ? '✓' : '✗'}
                        </li>
                        <li class="${preview.has_project_state ? 'available' : 'unavailable'}">
                            Project State ${preview.has_project_state ? '✓' : '✗'}
                        </li>
                    </ul>
                </div>
                
                ${metadata.tags.length > 0 ? `
                    <div class="preview-tags">
                        ${metadata.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                ` : ''}
                
                <div class="preview-actions">
                    <button class="btn-primary" onclick="contextManager.restoreContext(${metadata.id})">Restore Full Context</button>
                    <button class="btn-secondary" onclick="contextManager.hideContextPreview()">Close</button>
                </div>
            </div>
        `;
        
        content.innerHTML = html;
        modal.style.display = 'block';
    }
    
    /**
     * Hide context preview modal
     */
    hideContextPreview() {
        const modal = document.getElementById('context-preview-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    /**
     * Restore a context
     */
    async restoreContext(contextId) {
        try {
            this.currentContextId = contextId;
            this.showStatus('Restoring context...', 'info');
            
            const formatSelect = document.getElementById('restore-format');
            const format = formatSelect ? formatSelect.value : '';
            
            const url = format 
                ? `/api/context/restore/${contextId}?tool_format=${format}`
                : `/api/context/${contextId}`;
            
            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showContextRestore(result);
                this.hideStatus();
            } else {
                const error = await response.json();
                this.showStatus(`Failed to restore context: ${error.error || error.detail}`, 'error');
            }
            
        } catch (error) {
            this.showStatus(`Error restoring context: ${error.message}`, 'error');
        }
    }
    
    /**
     * Show context restore modal
     */
    showContextRestore(restoreData) {
        const modal = document.getElementById('context-restore-modal');
        const content = document.getElementById('context-restore-content');
        
        if (!modal || !content) return;
        
        this.contextData = restoreData.context_data;
        
        let html = `
            <div class="restore-result">
                <div class="restore-info">
                    <p><strong>Context restored successfully!</strong></p>
                    ${restoreData.format_optimized ? '<p class="format-note">✓ Format optimized for target tool</p>' : ''}
                </div>
                
                <div class="context-data-preview">
                    <h5>Context Data Preview:</h5>
                    <pre class="json-preview">${JSON.stringify(restoreData.context_data, null, 2).slice(0, 1000)}${JSON.stringify(restoreData.context_data, null, 2).length > 1000 ? '...' : ''}</pre>
                </div>
            </div>
        `;
        
        content.innerHTML = html;
        modal.style.display = 'block';
    }
    
    /**
     * Hide context restore modal
     */
    hideContextRestore() {
        const modal = document.getElementById('context-restore-modal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.contextData = {};
    }
    
    /**
     * Copy context data to clipboard
     */
    async copyContextToClipboard() {
        if (!this.contextData || Object.keys(this.contextData).length === 0) {
            this.showStatus('No context data to copy', 'error');
            return;
        }
        
        try {
            const jsonString = JSON.stringify(this.contextData, null, 2);
            await navigator.clipboard.writeText(jsonString);
            this.showStatus('Context data copied to clipboard!', 'success');
        } catch (error) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = JSON.stringify(this.contextData, null, 2);
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showStatus('Context data copied to clipboard!', 'success');
        }
    }
    
    /**
     * Delete a context with confirmation
     */
    async deleteContext(contextId, contextTitle) {
        const confirmed = confirm(`Are you sure you want to delete "${contextTitle}"? This action cannot be undone.`);
        
        if (!confirmed) return;
        
        try {
            this.showStatus('Deleting context...', 'info');
            
            const response = await fetch(`/api/context/${contextId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                this.showStatus('Context deleted successfully', 'success');
                this.loadContextList();
            } else {
                const error = await response.json();
                this.showStatus(`Failed to delete context: ${error.detail}`, 'error');
            }
            
        } catch (error) {
            this.showStatus(`Error deleting context: ${error.message}`, 'error');
        }
    }
    
    /**
     * Hide all modals
     */
    hideAllModals() {
        this.hideContextPreview();
        this.hideContextRestore();
        this.hideContextForm();
    }
    
    /**
     * Clear the save form
     */
    clearSaveForm() {
        const form = document.getElementById('save-context-form');
        if (form) {
            form.reset();
        }
    }
    
    /**
     * Show status message
     */
    showStatus(message, type = 'info') {
        const statusDiv = document.getElementById('context-status');
        if (!statusDiv) return;
        
        statusDiv.className = `context-status ${type}`;
        statusDiv.textContent = message;
        statusDiv.style.display = 'block';
        
        // Auto-hide success and info messages
        if (type === 'success' || type === 'info') {
            setTimeout(() => this.hideStatus(), 3000);
        }
    }
    
    /**
     * Hide status message
     */
    hideStatus() {
        const statusDiv = document.getElementById('context-status');
        if (statusDiv) {
            statusDiv.style.display = 'none';
        }
    }
    
    /**
     * Get authentication token (placeholder - implement based on your auth system)
     */
    getAuthToken() {
        // This should retrieve the actual auth token from your authentication system
        // For now, returning empty string as auth is optional in development
        return localStorage.getItem('auth_token') || '';
    }
}

// Global functions for onclick handlers
window.hideContextForm = () => {
    if (window.contextManager) {
        window.contextManager.hideContextForm();
    }
};

window.hideContextPreview = () => {
    if (window.contextManager) {
        window.contextManager.hideContextPreview();
    }
};

window.hideContextRestore = () => {
    if (window.contextManager) {
        window.contextManager.hideContextRestore();
    }
};

/**
 * Initialize context management UI
 */
function initContextUI() {
    // Initialize the context manager when the context tab is shown
    const contextTab = document.getElementById('context-tab');
    if (contextTab && !window.contextManager) {
        window.contextManager = new ContextManager();
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ContextManager, initContextUI };
}