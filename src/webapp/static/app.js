// AI Prompt Helper - Frontend JavaScript
console.log('JavaScript file loaded successfully!');

class PromptGenerator {
    constructor() {
        console.log('PromptGenerator constructor called');
        this.templates = [];
        this.currentTemplate = null;
        this.init();
    }

    init() {
        this.loadTemplates();
        this.setupEventListeners();
    }

    setupEventListeners() {
        const templateSelect = document.getElementById('template-select');
        const generateBtn = document.getElementById('generate-btn');

        console.log('Setting up event listeners...');
        console.log('Template select element:', templateSelect);
        console.log('Generate button element:', generateBtn);

        templateSelect.addEventListener('change', (e) => {
            console.log('Template selection changed to:', e.target.value);
            if (e.target.value) {
                this.loadTemplate(e.target.value);
            } else {
                this.clearForm();
            }
        });

        generateBtn.addEventListener('click', () => {
            console.log('Generate button clicked');
            this.generatePrompt();
        });
        
        console.log('Event listeners set up successfully');
    }

    async loadTemplates() {
        try {
            const response = await fetch('/api/templates');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.templates = data.templates;

            this.populateTemplateSelect();
        } catch (error) {
            console.error('Error loading templates:', error);
            this.showError('Failed to load templates');
        }
    }

    populateTemplateSelect() {
        const select = document.getElementById('template-select');
        
        // Clear existing options except the first one
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }

        this.templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template;
            option.textContent = this.formatTemplateName(template);
            select.appendChild(option);
        });
    }

    formatTemplateName(filename) {
        // Convert "coding_planning_template.md" to "Coding Planning Template"
        return filename
            .replace('_template.md', '')
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    loadTemplate(templateName) {
        console.log('Loading template:', templateName);
        
        // For debugging, let's use mock data first
        const mockPlaceholders = ['role_type', 'domain', 'project_description', 'specific_task'];
        console.log('Using mock placeholders:', mockPlaceholders);
        
        this.currentTemplate = {
            name: templateName,
            placeholders: mockPlaceholders
        };

        console.log('About to generate form...');
        this.generateForm(mockPlaceholders);
        this.showGenerateButton();
        console.log('Form generation completed');
        
        // Comment out API call for now to test form generation
        /*
        fetch('/api/parse-template', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ template_name: templateName })
        })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received placeholders:', data.placeholders);
            
            this.currentTemplate = {
                name: templateName,
                placeholders: data.placeholders
            };

            console.log('About to generate form...');
            this.generateForm(data.placeholders);
            this.showGenerateButton();
            console.log('Form generation completed');
        })
        .catch(error => {
            console.error('Error loading template:', error);
            this.showError('Failed to load template: ' + error.message);
        });
        */
    }

    getMockPlaceholders(templateName) {
        // Mock placeholders based on template name for testing
        const mockData = {
            'coding_planning_template.md': [
                'role_persona',
                'project_overview', 
                'planning_deliverables',
                'success_criteria',
                'constraints'
            ],
            'coding_brainstorming_template.md': [
                'project_type',
                'target_audience',
                'key_features',
                'technical_constraints'
            ],
            'project_init_template.md': [
                'project_name',
                'project_description',
                'tech_stack',
                'timeline'
            ],
            'research_topic_template.md': [
                'research_topic',
                'research_scope',
                'target_depth',
                'output_format'
            ]
        };

        return mockData[templateName] || ['example_variable', 'another_variable'];
    }

    generateForm(placeholders) {
        console.log('generateForm called with:', placeholders);
        const form = document.getElementById('prompt-form');
        console.log('Form element found:', form);
        
        if (!form) {
            console.error('Form element not found!');
            return;
        }
        
        form.innerHTML = ''; // Clear existing form

        const formTitle = document.createElement('h3');
        formTitle.textContent = 'Fill in the template variables:';
        form.appendChild(formTitle);
        console.log('Added form title');

        placeholders.forEach((placeholder, index) => {
            console.log(`Creating field ${index + 1} for:`, placeholder);
            
            const fieldContainer = document.createElement('div');
            fieldContainer.className = 'form-field';

            const label = document.createElement('label');
            label.textContent = this.formatPlaceholderLabel(placeholder);
            label.setAttribute('for', placeholder);

            const input = document.createElement('textarea');
            input.id = placeholder;
            input.name = placeholder;
            input.placeholder = `Enter ${this.formatPlaceholderLabel(placeholder).toLowerCase()}...`;
            input.rows = 3;
            input.required = true;

            fieldContainer.appendChild(label);
            fieldContainer.appendChild(input);
            form.appendChild(fieldContainer);
            
            console.log(`Added field for ${placeholder}`);
        });
        
        console.log('Form generation complete, form children count:', form.children.length);
    }

    formatPlaceholderLabel(placeholder) {
        // Convert "role_persona" to "Role Persona"
        return placeholder
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    showGenerateButton() {
        const generateBtn = document.getElementById('generate-btn');
        generateBtn.style.display = 'block';
    }

    clearForm() {
        const form = document.getElementById('prompt-form');
        const generateBtn = document.getElementById('generate-btn');
        const outputContainer = document.getElementById('output-container');

        form.innerHTML = '';
        generateBtn.style.display = 'none';
        outputContainer.style.display = 'none';
        
        this.currentTemplate = null;
    }

    async generatePrompt() {
        if (!this.currentTemplate) {
            this.showError('No template selected');
            return;
        }

        const formData = this.collectFormData();
        if (!formData) {
            this.showError('Please fill in all required fields');
            return;
        }

        try {
            this.showLoading();

            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    template_name: this.currentTemplate.name,
                    user_data: formData
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.showResult(data.generated_prompt);
            } else {
                this.showError(data.error || 'Failed to generate prompt');
            }
        } catch (error) {
            console.error('Error generating prompt:', error);
            this.showError('Failed to generate prompt');
        }
    }

    collectFormData() {
        const form = document.getElementById('prompt-form');
        const formData = new FormData(form);
        const data = {};
        let allFieldsFilled = true;

        for (let [key, value] of formData.entries()) {
            if (!value.trim()) {
                allFieldsFilled = false;
                break;
            }
            data[key] = value.trim();
        }

        return allFieldsFilled ? data : null;
    }

    generateMockResponse(formData) {
        // Generate a mock response for testing
        const templateName = this.formatTemplateName(this.currentTemplate.name);
        
        let mockPrompt = `# ${templateName}\n\n`;
        
        Object.entries(formData).forEach(([key, value]) => {
            const label = this.formatPlaceholderLabel(key);
            mockPrompt += `## ${label}\n${value}\n\n`;
        });

        mockPrompt += `---\n\n*Generated using AI Prompt Helper*\n`;
        mockPrompt += `*Template: ${this.currentTemplate.name}*\n`;
        mockPrompt += `*Generated at: ${new Date().toLocaleString()}*`;

        return mockPrompt;
    }

    showLoading() {
        const outputContainer = document.getElementById('output-container');
        const outputPrompt = document.getElementById('output-prompt');
        
        outputPrompt.textContent = 'Generating prompt... Please wait.';
        outputContainer.style.display = 'block';
        
        // Scroll to output
        outputContainer.scrollIntoView({ behavior: 'smooth' });
    }

    showResult(promptText) {
        const outputContainer = document.getElementById('output-container');
        const outputPrompt = document.getElementById('output-prompt');
        
        outputPrompt.textContent = promptText;
        outputContainer.style.display = 'block';
        
        // Scroll to output
        outputContainer.scrollIntoView({ behavior: 'smooth' });
    }

    showError(message) {
        const outputContainer = document.getElementById('output-container');
        const outputPrompt = document.getElementById('output-prompt');
        
        outputPrompt.textContent = `Error: ${message}`;
        outputPrompt.style.color = '#e74c3c';
        outputContainer.style.display = 'block';
        
        // Reset color after a few seconds
        setTimeout(() => {
            outputPrompt.style.color = '';
        }, 3000);
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded, initializing PromptGenerator...');
    new PromptGenerator();
});

console.log('JavaScript file completely loaded, waiting for DOM...');