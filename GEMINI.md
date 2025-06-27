# AIhelpers Project: Gemini Agent Instructions

## Project Context

AIhelpers is a CLI tool that generates effective, structured prompts using proven templates. The goal is to transform ad-hoc prompting into a systematic, reusable process that produces higher-quality AI interactions. This tool implements the hierarchical prompt engineering concepts researched in our AI rules documentation.

## Project-Specific Guidelines

### CLI Tool Development
* **Framework:** Use Python with Typer for the CLI framework - it provides excellent type hints and automatic help generation
* **Output Formatting:** Use Rich library for beautiful terminal output, including tables, progress bars, and syntax highlighting
* **Configuration Management:** Use YAML or JSON for template storage, allow both built-in templates and user-defined ones
* **User Experience:** The CLI should be intuitive for both beginners and power users. Provide good defaults but allow customization.

### Prompt Template System
* **Template Structure:** Each template must include all sections we've defined (Role, Context, Success Criteria, etc.)
* **Variable Substitution:** Use Jinja2 templates for variable substitution - it's powerful and familiar to many developers
* **Validation:** Validate template completeness before generating final prompts
* **Extensibility:** Make it easy for users to add their own template types

### Code Organization
* **Main CLI Module:** `aihelpers/cli.py` - main entry point and command definitions
* **Template Engine:** `aihelpers/templates/` - template loading, rendering, and management
* **Interactive Prompting:** `aihelpers/interactive.py` - handles the question/answer flow for template completion
* **Configuration:** `aihelpers/config.py` - user settings and template paths
* **Templates:** `templates/` directory for built-in template files

### File Handling
* **Template Storage:** Store templates as separate .md files in a templates/ directory
* **User Templates:** Support a ~/.aihelpers/templates/ directory for user-defined templates
* **Output:** Generate complete prompts as .txt or .md files that can be copied to clipboard or saved

### Error Handling
* **User-Friendly Messages:** CLI errors should be helpful and actionable, not technical stack traces
* **Template Validation:** Clear error messages when templates are malformed or incomplete
* **Graceful Degradation:** If optional features fail, continue with core functionality

### Development Workflow
* **Testing:** Include tests for template rendering, CLI commands, and interactive flows
* **Documentation:** README with clear installation and usage instructions
* **Examples:** Include example outputs and common use cases in documentation

## AI Assistant Behavior for This Project

* **Focus on Practical CLI Patterns:** When suggesting code, emphasize patterns that work well for command-line tools
* **Template-First Thinking:** Always consider how features fit into the template-driven architecture
* **User Experience Focus:** Prioritize features that make the tool easier and more pleasant to use
* **Incremental Development:** Suggest building features in logical, testable increments

## Success Metrics

The tool should enable users to:
1. Generate structured prompts 10x faster than writing from scratch
2. Create more effective prompts through guided template completion
3. Reuse and customize prompt patterns for their specific needs
4. Learn prompt engineering principles through the interactive process