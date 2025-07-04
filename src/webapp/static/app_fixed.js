// AI Prompt Helper - Fixed Version
console.log('Fixed JavaScript loaded');

class PromptGenerator {
    constructor() {
        console.log('PromptGenerator constructor called');
        this.templates = [];
        this.currentTemplate = null;
        this.init();
    }

    init() {
        console.log('Initializing...');
        this.loadTemplates();
        this.setupEventListeners();
    }

    setupEventListeners() {
        const templateSelect = document.getElementById('template-select');
        const generateBtn = document.getElementById('generate-btn');

        console.log('Setting up event listeners...');

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
    }

    async loadTemplates() {
        try {
            console.log('Loading templates...');
            const response = await fetch('/api/templates');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.templates = data.templates;
            console.log('Templates loaded:', this.templates);

            this.populateTemplateSelect();
        } catch (error) {
            console.error('Error loading templates:', error);
            // Fallback to hardcoded templates
            this.templates = ['demo_template.md', 'coding_planning_template.md'];
            this.populateTemplateSelect();
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
        
        console.log('Template select populated with', this.templates.length, 'templates');
    }

    formatTemplateName(filename) {
        return filename
            .replace('_template.md', '')
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    loadTemplate(templateName) {
        console.log('Loading template:', templateName);
        
        fetch('/api/parse-template', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ template_name: templateName })
        })
        .then(response => {
            console.log('Parse template response status:', response.status);
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
            const orderedPlaceholders = this.orderPlaceholders(data.placeholders);
            this.generateForm(orderedPlaceholders);
            this.showGenerateButton();
            console.log('Form generation completed');
        })
        .catch(error => {
            console.error('Error loading template:', error);
            
            // Fallback to mock data if API fails
            console.log('Using fallback mock data');
            const mockPlaceholders = ['role_type', 'domain', 'project_description', 'specific_task'];
            this.currentTemplate = {
                name: templateName,
                placeholders: mockPlaceholders
            };
            const orderedPlaceholders = this.orderPlaceholders(mockPlaceholders);
            this.generateForm(orderedPlaceholders);
            this.showGenerateButton();
        });
    }

    generateForm(placeholders) {
        console.log('generateForm called with:', placeholders);
        const form = document.getElementById('prompt-form');
        console.log('Form element found:', !!form);
        
        if (!form) {
            console.error('Form element not found!');
            return;
        }
        
        // Clear existing form
        form.innerHTML = '';

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
            input.placeholder = this.getPlaceholderText(placeholder);
            input.rows = 3;
            input.required = true;

            fieldContainer.appendChild(label);
            fieldContainer.appendChild(input);
            form.appendChild(fieldContainer);
        });
        
        console.log('Form generation complete, form children count:', form.children.length);
    }

    formatPlaceholderLabel(placeholder) {
        // Create better, more descriptive labels
        const labelMap = {
            'research_expert_role': 'Your Expert Role',
            'research_purpose': 'Research Purpose & Goals',
            'research_scope': 'What to Research (Scope)',
            'success_criteria': 'Success Criteria',
            'constraints': 'Constraints & Limitations',
            'target_audience': 'Target Audience',
            'expert_role': 'Your Expert Role',
            'project_context': 'Project Context & Background',
            'brainstorming_focus': 'Brainstorming Focus',
            'planning_expert_role': 'Your Planning Role',
            'project_overview': 'Project Overview',
            'planning_deliverables': 'Planning Deliverables',
            'role_type': 'Your Role/Expertise',
            'domain': 'Domain/Field',
            'project_description': 'Project Description',
            'specific_task': 'Specific Task',
            'quality_level': 'Quality Level',
            'timeline': 'Timeline',
            'expected_output': 'Expected Output'
        };
        
        return labelMap[placeholder] || placeholder
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    getPlaceholderText(placeholder) {
        // Helpful placeholder text for each field
        const placeholderMap = {
            'research_expert_role': 'e.g., "You are a senior web developer and technical educator..."',
            'research_purpose': 'e.g., "To choose the best web framework for AI-assisted development..."',
            'research_scope': 'e.g., "Compare React, Vue, Angular, Svelte - their strengths, weaknesses, AI training data availability..."',
            'success_criteria': 'e.g., "Clear recommendation with pros/cons and AI compatibility assessment"',
            'constraints': 'e.g., "Focus on frameworks with good AI/LLM training data, avoid outdated info..."',
            'target_audience': 'e.g., "AI enthusiasts who use AI tools for web development"',
            'expert_role': 'e.g., "You are a senior full-stack developer with 8 years experience..."',
            'project_context': 'e.g., "Building a time tracking app for small consulting firms..."',
            'brainstorming_focus': 'e.g., "Architecture approaches and tech stack evaluation for MVP..."',
            'planning_expert_role': 'e.g., "You are a technical product manager with SaaS experience..."',
            'project_overview': 'e.g., "Build expense reporting mobile app for 10-100 employee companies..."',
            'planning_deliverables': 'e.g., "Complete PRD, MVP specs with user stories, technical architecture..."',
            'role_type': 'e.g., "software engineer", "AI researcher", "product manager"',
            'domain': 'e.g., "web development", "machine learning", "fintech"',
            'project_description': 'e.g., "Building a React dashboard for enterprise users..."',
            'specific_task': 'e.g., "optimize performance", "add authentication", "design API"',
            'quality_level': 'e.g., "production-ready", "prototype", "enterprise-grade"',
            'timeline': 'e.g., "2 weeks", "1 month", "by end of quarter"',
            'expected_output': 'e.g., "detailed implementation plan", "code examples", "architecture diagram"'
        };
        
        return placeholderMap[placeholder] || `Enter ${this.formatPlaceholderLabel(placeholder).toLowerCase()}...`;
    }

    orderPlaceholders(placeholders) {
        // Define logical order for form fields
        const order = [
            // Role fields first
            'expert_role', 'research_expert_role', 'planning_expert_role', 'role_type',
            // Context/overview fields
            'project_context', 'project_overview', 'project_description', 'domain',
            // Purpose/focus fields  
            'research_purpose', 'brainstorming_focus', 'specific_task',
            // Scope fields
            'research_scope', 'planning_deliverables',
            // Criteria fields
            'success_criteria', 'quality_level',
            // Constraints
            'constraints',
            // Audience/timeline
            'target_audience', 'timeline', 'expected_output'
        ];

        // Sort placeholders according to the defined order
        const ordered = [];
        const remaining = [...placeholders];

        // Add fields in order if they exist
        order.forEach(field => {
            const index = remaining.indexOf(field);
            if (index !== -1) {
                ordered.push(field);
                remaining.splice(index, 1);
            }
        });

        // Add any remaining fields that weren't in the order
        ordered.push(...remaining);

        return ordered;
    }

    showGenerateButton() {
        const generateBtn = document.getElementById('generate-btn');
        generateBtn.style.display = 'block';
        console.log('Generate button shown');
    }

    clearForm() {
        const form = document.getElementById('prompt-form');
        const generateBtn = document.getElementById('generate-btn');
        const outputContainer = document.getElementById('output-container');

        form.innerHTML = '';
        generateBtn.style.display = 'none';
        outputContainer.style.display = 'none';
        
        this.currentTemplate = null;
        console.log('Form cleared');
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

    showLoading() {
        const outputContainer = document.getElementById('output-container');
        const outputPrompt = document.getElementById('output-prompt');
        
        outputPrompt.textContent = 'Generating prompt... Please wait.';
        outputContainer.style.display = 'block';
        
        outputContainer.scrollIntoView({ behavior: 'smooth' });
    }

    showResult(promptText) {
        const outputContainer = document.getElementById('output-container');
        const outputPrompt = document.getElementById('output-prompt');
        
        outputPrompt.textContent = promptText;
        outputContainer.style.display = 'block';
        
        outputContainer.scrollIntoView({ behavior: 'smooth' });
    }

    showError(message) {
        const outputContainer = document.getElementById('output-container');
        const outputPrompt = document.getElementById('output-prompt');
        
        outputPrompt.textContent = `Error: ${message}`;
        outputPrompt.style.color = '#e74c3c';
        outputContainer.style.display = 'block';
        
        setTimeout(() => {
            outputPrompt.style.color = '';
        }, 3000);
    }
}

// Tab switching functionality
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab content
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Add active class to clicked tab button
    event.target.classList.add('active');
}

// Parsinator functionality
class ParsinatorController {
    constructor() {
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        document.getElementById('health-check-btn').addEventListener('click', () => this.healthCheck());
        document.getElementById('validate-brief-btn').addEventListener('click', () => this.validateBrief());
        document.getElementById('process-brief-btn').addEventListener('click', () => this.processBrief());
        document.getElementById('load-example-btn').addEventListener('click', () => this.loadExample());
    }
    
    async healthCheck() {
        this.showLoading('Checking Parsinator health...');
        
        try {
            const response = await fetch('/api/parsinator/health');
            const data = await response.json();
            
            if (data.healthy) {
                this.showResult('success', `✅ Parsinator is healthy! Available templates: ${data.available_templates}`);
            } else {
                this.showResult('error', `❌ Health check failed: ${data.error}`);
            }
        } catch (error) {
            this.showResult('error', `❌ Health check error: ${error.message}`);
        }
    }
    
    async validateBrief() {
        const briefText = document.getElementById('brief-text').value.trim();
        if (!briefText) {
            this.showResult('error', '❌ Please enter a brief to validate');
            return;
        }
        
        this.showLoading('Validating brief format...');
        
        try {
            const response = await fetch('/api/parsinator/validate-brief', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ brief_text: briefText })
            });
            
            const data = await response.json();
            
            if (data.valid) {
                this.showResult('success', `✅ Brief is valid! Type: ${data.brief_type || 'unknown'}`);
            } else {
                const errors = data.errors.join('\\n');
                this.showResult('error', `❌ Brief validation failed:\\n${errors}`);
            }
        } catch (error) {
            this.showResult('error', `❌ Validation error: ${error.message}`);
        }
    }
    
    async processBrief() {
        const briefText = document.getElementById('brief-text').value.trim();
        const projectName = document.getElementById('project-name').value.trim() || 'Web Project';
        
        if (!briefText) {
            this.showResult('error', '❌ Please enter a brief to process');
            return;
        }
        
        this.showLoading('Processing brief and generating tasks...');
        
        try {
            const response = await fetch('/api/parsinator/process-brief', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    brief_text: briefText,
                    project_name: projectName
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const summary = `✅ Successfully processed brief!
                
📊 Results:
- Tasks generated: ${data.task_count}
- Project: ${projectName}

${data.task_count > 0 ? '📋 Generated Tasks:' : '⚠️ No tasks were extracted from this brief'}`;
                
                this.showResult('success', summary, JSON.stringify(data.tasks, null, 2));
            } else {
                this.showResult('error', `❌ Processing failed: ${data.error}`);
            }
        } catch (error) {
            this.showResult('error', `❌ Processing error: ${error.message}`);
        }
    }
    
    loadExample() {
        const exampleBrief = `# Feature Brief Template

## Feature Name
User Authentication System

## Problem Statement
The application needs secure user authentication to protect user data and provide personalized experiences.

## Core Feature Tasks
### Must-Have Implementation
1. **Create User Model**: Design database schema for user accounts with email, password hash, and profile data
2. **Implement Registration**: Build user registration with email validation and password requirements
3. **Add Login System**: Create secure login with JWT token generation and session management
4. **Build Password Reset**: Implement forgot password flow with email-based reset tokens
5. **Add User Dashboard**: Create protected user profile page with account management features

## Success Criteria
- Users can register and login securely
- Passwords are properly hashed and stored
- JWT tokens expire appropriately
- Password reset works via email
- All endpoints properly authenticate requests`;

        document.getElementById('brief-text').value = exampleBrief;
        this.showResult('info', '📝 Example brief loaded! You can now validate or process it.');
    }
    
    showLoading(message) {
        const output = document.getElementById('parsinator-output');
        const status = document.getElementById('parsinator-status');
        const content = document.getElementById('parsinator-content');
        
        status.className = 'info';
        status.textContent = message;
        content.textContent = '';
        output.style.display = 'block';
    }
    
    showResult(type, message, details = '') {
        const output = document.getElementById('parsinator-output');
        const status = document.getElementById('parsinator-status');
        const content = document.getElementById('parsinator-content');
        
        status.className = type;
        status.textContent = message;
        content.textContent = details;
        output.style.display = 'block';
        
        // Scroll to results
        output.scrollIntoView({ behavior: 'smooth' });
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded, initializing applications...');
    new PromptGenerator();
    new ParsinatorController();
});

console.log('Fixed JavaScript file loaded, waiting for DOM...');