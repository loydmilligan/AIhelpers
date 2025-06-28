// Minimal working version
console.log('Minimal app loading...');

function initializeApp() {
    console.log('App initializing...');
    
    const templateSelect = document.getElementById('template-select');
    const promptForm = document.getElementById('prompt-form');
    const generateBtn = document.getElementById('generate-btn');
    
    console.log('Elements found:', {
        templateSelect: !!templateSelect,
        promptForm: !!promptForm,
        generateBtn: !!generateBtn
    });
    
    if (!templateSelect || !promptForm || !generateBtn) {
        console.error('Required elements not found!');
        return;
    }
    
    // Add templates to select
    const templates = ['demo_template.md', 'coding_planning_template.md'];
    templates.forEach(template => {
        const option = document.createElement('option');
        option.value = template;
        option.textContent = template.replace('_template.md', '').replace(/_/g, ' ');
        templateSelect.appendChild(option);
    });
    
    // Handle template selection
    templateSelect.addEventListener('change', function(e) {
        console.log('Template selected:', e.target.value);
        
        if (e.target.value) {
            // Clear form
            promptForm.innerHTML = '';
            
            // Add title
            const title = document.createElement('h3');
            title.textContent = 'Fill in the template variables:';
            promptForm.appendChild(title);
            
            // Add sample fields
            const fields = ['role_type', 'domain', 'project_description', 'specific_task'];
            fields.forEach(field => {
                const div = document.createElement('div');
                div.className = 'form-field';
                
                const label = document.createElement('label');
                label.textContent = field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                
                const textarea = document.createElement('textarea');
                textarea.name = field;
                textarea.rows = 3;
                textarea.placeholder = `Enter ${field.replace(/_/g, ' ')}...`;
                
                div.appendChild(label);
                div.appendChild(textarea);
                promptForm.appendChild(div);
            });
            
            generateBtn.style.display = 'block';
            console.log('Form created with', fields.length, 'fields');
        } else {
            promptForm.innerHTML = '';
            generateBtn.style.display = 'none';
        }
    });
    
    generateBtn.addEventListener('click', function() {
        console.log('Generate button clicked');
        alert('Generate functionality would work here');
    });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}

console.log('Minimal app script loaded');