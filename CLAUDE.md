# AIhelpers Project - Claude AI Assistant Instructions

## Project Overview

AIhelpers is an AI coding workflow management platform that transforms ad-hoc prompting into systematic, reusable processes. The current MVP includes:

- **Prompt Generation System**: Template-based prompt creation with AI assembly using Google Gemini
- **Parsinator**: Converts project briefs into structured, dependency-aware task lists  
- **Web Interface**: FastAPI backend with HTMX frontend for both prompt generation and Parsinator
- **CLI Tools**: Command-line interfaces for both prompt generation and brief processing

**Current Status**: 75% complete MVP with plans to expand into comprehensive AI workflow platform supporting Claude Code, Cursor integration, team collaboration, and session context preservation.

## Architecture Understanding

### Current Tech Stack
- **Backend**: FastAPI with Pydantic models
- **Frontend**: HTMX-powered interface with modern CSS
- **AI Integration**: Google Gemini for prompt generation
- **Task Processing**: Parsinator CLI system with dependency analysis
- **Data Storage**: File-based (transitioning to PostgreSQL per PRD)
- **Development**: Python 3.8+ with comprehensive CLI tooling

### Key Components
1. **Prompt Generation** (`src/main.py`, `src/prompt_generator.py`)
2. **Web Application** (`src/webapp/main.py`)
3. **Parsinator System** (`src/parsinator/` - complete task generation framework)
4. **Frontend Interface** (`src/webapp/static/` - HTMX-based UI)

## Development Approach: Manifest-Driven Development

This project uses a **manifest-driven development** approach for systematic, context-efficient development.

### Core Principle
Always work with the `codebase_manifest.json` as your source of truth for understanding project structure, component relationships, and current implementation status.

### When to Update the Manifest
- After completing major features or components
- When architectural decisions change the project structure
- When adding new files or significantly modifying existing ones
- Before starting work on complex features to plan changes

### Task Management System
The project uses a structured task system located in `tasks/`:
- **`tasks.json`**: Master task registry with dependencies and status
- **Individual task files**: Detailed implementation guidance
- **Priority-based execution**: Always follow dependency chains and priority levels

## Development Guidelines

### Working with Prompt Generation
- Templates are stored in `prompts/` directory as Markdown files
- The system uses `{{placeholder}}` format for variable substitution
- AI assembly happens via Google Gemini using `prompts/meta_prompt.md`
- Web interface provides dynamic form generation based on template parsing

### Working with Parsinator
- Brief templates are in `docs/parsinator/brief_templates/`
- Example briefs are in `docs/parsinator/briefs/`
- Parsinator converts briefs → structured tasks with dependency analysis
- CLI entry point: `python -m src.parsinator.main [command]`
- Web integration available through `/api/parsinator/` endpoints

### Code Quality Standards
- Follow existing patterns in FastAPI endpoints and Pydantic models
- Maintain HTMX frontend patterns for dynamic interactions
- Use comprehensive error handling and logging
- Write clear docstrings and type hints
- Preserve backward compatibility when extending features

### File Organization Rules
- **`src/`**: All application code
- **`src/webapp/`**: Web application components
- **`src/parsinator/`**: Task generation system
- **`docs/`**: Documentation, templates, and examples
- **`tasks/`**: Task management and tracking
- **`prompts/`**: Prompt templates for generation system

## AI Assistant Behavior Guidelines

### When Analyzing the Codebase
1. **Start with the manifest**: Always reference `codebase_manifest.json` for current project understanding
2. **Check task status**: Review `tasks/tasks.json` to understand current development priorities
3. **Understand context**: This is a working MVP with real users, so maintain stability while adding features

### When Making Changes
1. **Follow the PRD**: Major new features should align with `docs/PRD_AI_Coding_Workflow_MVP.md`
2. **Maintain existing functionality**: Don't break current prompt generation or Parsinator capabilities
3. **Update documentation**: Keep README and relevant docs current with changes
4. **Consider the task list**: New features should integrate with the planned task roadmap

### When Debugging Issues
1. **Check both CLI and web interfaces**: Issues may manifest differently
2. **Verify environment setup**: Ensure `GEMINI_API_KEY` and dependencies are correct
3. **Test with existing templates**: Use templates in `prompts/` and example briefs
4. **Check the FastAPI logs**: Web interface issues often show in server logs

### Working with Users
- This is a productivity tool for developers, so focus on developer experience
- Users expect the tool to "just work" for prompt generation and brief processing
- Performance matters - keep response times under 2 seconds for most operations
- Provide clear error messages and helpful guidance

## Current Development Priorities

Based on the task list and PRD, focus areas are:

### High Priority
1. **Complete current web interface improvements** (Task 9 in progress)
2. **Database migration planning** (per PRD Task 1)
3. **Authentication system foundation** (per PRD Task 2)
4. **Enhanced prompt organization** (per PRD Task 3)

### Medium Priority
1. **Performance optimization** for larger prompt libraries
2. **Mobile responsiveness** improvements
3. **Enhanced error handling** and user feedback
4. **API documentation** and developer resources

### Future Vision
The PRD outlines expansion into:
- Claude Code and Cursor integration
- Team collaboration features
- Session context preservation
- Advanced analytics and AI-powered insights
- Enterprise features and scaling

## Success Metrics to Keep in Mind

- **User Experience**: 70% of users should create/use prompt templates within first week
- **Performance**: <2 second response times for 95% of requests
- **Efficiency**: 60% reduction in AI session setup time
- **Reliability**: 99.5% uptime for production deployment
- **Growth**: Path to 1,000 registered users within 3 months

## Integration Points

### AI Tool Integration (Future)
- Claude Code API integration for prompt sharing
- Cursor extension for context preservation
- Universal session bridge for cross-tool workflows

### Current Integrations
- Google Gemini for AI-powered prompt assembly
- FastAPI for robust web API framework
- HTMX for dynamic frontend without complex JavaScript
- Parsinator for intelligent task generation

## Common Development Patterns

### Adding New API Endpoints
```python
# Follow existing pattern in src/webapp/main.py
@app.post("/api/new-feature", response_model=FeatureResponse)
async def new_feature_endpoint(request: FeatureRequest):
    try:
        # Implementation
        return FeatureResponse(success=True, data=result)
    except Exception as e:
        return FeatureResponse(success=False, error=str(e))
```

### Extending Parsinator
- Add new brief templates to `docs/parsinator/brief_templates/`
- Extend parser logic in `src/parsinator/parser.py`
- Update CLI commands in `src/parsinator/main.py`
- Test with example briefs in `docs/parsinator/briefs/`

### Frontend Enhancements
- Use HTMX attributes for dynamic interactions
- Follow existing CSS patterns in `src/webapp/static/style.css`
- Maintain tab-based navigation structure
- Ensure mobile responsiveness

Remember: This is a real product with users who depend on it for their daily development workflow. Every change should enhance their experience while maintaining the reliability and simplicity that makes the tool valuable.