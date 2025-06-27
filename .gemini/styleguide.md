# AIhelpers Python Style Guide

This guide is the single source of truth for all Python code in the AIhelpers project. Gemini must enforce these rules during code reviews and generation. Deviations from these rules will be flagged as violations.

## Python Code Style

### PEP 8 Compliance
* All code **MUST** follow PEP 8 conventions for Python formatting
* Line length **MUST NOT** exceed 88 characters (Black formatter default)
* Use 4 spaces for indentation, never tabs
* Function and variable names **MUST** use snake_case (e.g., `render_template`, `user_input`)
* Class names **MUST** use PascalCase (e.g., `TemplateRenderer`, `CLICommand`)
* Constants **MUST** use SCREAMING_SNAKE_CASE (e.g., `DEFAULT_TEMPLATE_DIR`, `MAX_RETRIES`)

### Import Organization
* Imports **MUST** be organized in this order: standard library, third-party packages, local modules
* Use absolute imports, avoid relative imports except within the same package
* One import per line for clarity
* Use `from typing import` for type hints

## CLI Tool Standards

### User-Facing Messages
* All error messages **MUST** be helpful and actionable for end users
* **DO NOT** expose technical stack traces to users - catch exceptions and provide friendly messages
* Use Rich library for colored output and formatting
* Include suggestions for fixing common errors

### Command Structure
* All CLI commands **MUST** use Typer decorators and type hints
* Command names **MUST** use kebab-case (e.g., `generate-prompt`, `list-templates`)
* **MUST** include help text for all commands and options
* Required parameters should be positional, optional parameters should be options with `--flag`

### Error Handling
* All user-facing functions **MUST** have proper error handling
* Use specific exception types, not broad `except Exception:`
* Log errors appropriately - use Python's logging module, not print statements
* For file operations, handle `FileNotFoundError`, `PermissionError`, etc. specifically

## File and Directory Organization

### Project Structure
* Source code **MUST** be in the `aihelpers/` package directory
* Templates **MUST** be stored in `templates/` directory as separate `.md` files
* Tests **MUST** be in `tests/` directory and mirror the source structure
* Configuration files **MUST** be in the project root

### Module Organization
* Each module **MUST** have a clear, single responsibility
* Keep modules under 300 lines when possible
* Use `__init__.py` files to define package APIs clearly
* Private functions and classes **MUST** start with underscore

## Documentation Standards

### Docstrings
* All public functions and classes **MUST** have docstrings using Google style format
* Docstrings **MUST** include: description, Args, Returns, Raises sections when applicable
* Example:
```python
def render_template(template_path: str, variables: dict) -> str:
    """Render a Jinja2 template with provided variables.
    
    Args:
        template_path: Path to the template file
        variables: Dictionary of variables to substitute
        
    Returns:
        Rendered template as string
        
    Raises:
        FileNotFoundError: If template file doesn't exist
        TemplateError: If template syntax is invalid
    """
```

### Code Comments
* Use comments to explain **WHY**, not **WHAT** the code does
* Complex business logic **MUST** be explained with comments
* **DO NOT** comment obvious code

## Type Hints and Validation

### Type Annotations
* All function signatures **MUST** include type hints for parameters and return values
* Use `from typing import` for complex types like `List`, `Dict`, `Optional`
* Use `pathlib.Path` for file paths, not strings
* Example: `def load_template(path: Path) -> Optional[str]:`

### Input Validation
* All user inputs **MUST** be validated before processing
* Use Pydantic models for complex data validation when appropriate
* Validate file paths exist before attempting to read
* Sanitize any user input that will be used in file operations

## Security Practices

### File Handling
* **NEVER** trust user-provided file paths without validation
* Use `pathlib.Path.resolve()` to prevent directory traversal attacks
* Check file extensions match expected types
* Set appropriate file permissions for created files

### Template Processing
* When using Jinja2, **MUST** use sandboxed environment for user-provided templates
* **DO NOT** allow arbitrary code execution in templates
* Validate template syntax before rendering

## Testing Requirements

### Test Coverage
* All public functions **MUST** have corresponding tests
* Tests **MUST** cover both success and failure cases
* Use pytest for all testing
* Test file names **MUST** start with `test_` and match module names

### Test Structure
* One test class per module being tested
* Test method names **MUST** be descriptive: `test_render_template_with_missing_file_raises_error`
* Use fixtures for common test data and setup
* **DO NOT** test internal implementation details, focus on public interfaces

## Code Formatting and Linting

### Automated Tools
* All code **MUST** be formatted with Black using default settings
* All code **MUST** pass flake8 linting with zero warnings
* Use isort for import sorting
* Run these tools before committing: `black .`, `flake8 .`, `isort .`

### Pre-commit Hooks
* Set up pre-commit hooks to run Black, flake8, and isort automatically
* **DO NOT** commit code that fails linting

## Dependencies Management

### Package Requirements
* All dependencies **MUST** be pinned in `requirements.txt` or `pyproject.toml`
* Use virtual environments for development
* Keep dependencies minimal - justify each new dependency
* Prefer standard library solutions when possible

### Version Compatibility
* Support Python 3.8+ for broad compatibility
* Test on multiple Python versions if possible
* Use type hints compatible with older Python versions (use `typing` module imports)