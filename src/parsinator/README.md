# Parsinator

A powerful CLI tool that converts project briefs into detailed, dependency-aware task lists. Parsinator helps developers systematically break down projects into manageable tasks without manual planning overhead.

## Features

- **🧠 Intelligent Brief Parsing**: Automatically detects and processes setup, feature, and deployment briefs
- **🔗 Smart Dependency Analysis**: Maps task relationships with confidence scoring
- **🆔 Advanced ID Management**: Handles both new projects and additive sessions
- **📝 Template Validation**: Ensures briefs follow the correct format
- **📊 Comprehensive Analytics**: Detailed summaries and dependency insights
- **🔄 Additive Sessions**: Add new tasks to existing projects without conflicts

## Installation

Parsinator is part of the AIhelpers project. From the project root:

```bash
# The tool is ready to use as a Python module
cd /path/to/AIhelpers
python -m src.parsinator.main --help
```

## Quick Start

### 1. Using Example Briefs

Process the included example briefs to see Parsinator in action:

```bash
# Process a single brief
python -m src.parsinator.main process-brief docs/parsinator/briefs/parsinator_setup_brief.md

# Process all briefs in a directory
python -m src.parsinator.main process-briefs docs/parsinator/briefs/ --output-dir ./output

# Validate a brief format
python -m src.parsinator.main validate-brief docs/parsinator/briefs/parsinator_feature_brief.md
```

### 2. Creating Your Own Briefs

Use the templates in `docs/parsinator/brief_templates/` as starting points:

- `project_brief_template.md` - For project setup tasks
- `feature_brief_template.md` - For feature implementation
- `deployment_brief_template.md` - For testing and deployment

### 3. Output

Parsinator generates:
- **`tasks.json`** - Master task list with dependencies
- **`generation_summary.json`** - Detailed analytics and insights
- **Individual task files** - Use `generate-task-files` command

## CLI Commands

### Core Commands

**`process-brief <file>`** - Process a single brief file
```bash
python -m src.parsinator.main process-brief my_project_setup.md \
  --output-dir ./tasks \
  --project-name "My Project"
```

**`process-briefs <directory>`** - Process all briefs in a directory
```bash
python -m src.parsinator.main process-briefs ./briefs/ \
  --output-dir ./tasks \
  --existing-tasks ./existing_tasks.json  # For additive sessions
```

### Analysis Commands

**`validate-brief <file>`** - Validate brief format
```bash
python -m src.parsinator.main validate-brief my_brief.md \
  --template-type setup
```

**`analyze-brief <file>`** - Show detailed parsing results
```bash
python -m src.parsinator.main analyze-brief my_brief.md
```

**`analyze-dependencies <directory>`** - Detailed dependency analysis
```bash
python -m src.parsinator.main analyze-dependencies ./briefs/ \
  --confidence-threshold 0.7
```

**`analyze-tasks <tasks.json>`** - Analyze generated tasks
```bash
python -m src.parsinator.main analyze-tasks ./output/tasks.json
```

**`generate-task-files <tasks.json>`** - Generate individual task files
```bash
python -m src.parsinator.main generate-task-files ./output/tasks.json \
  --output-dir ./docs/tasks \
  --file-format txt  # or md
```

### Utility Commands

**`list-templates`** - Show available brief templates
```bash
python -m src.parsinator.main list-templates
```

**`hello`** - Test that Parsinator is working
```bash
python -m src.parsinator.main hello
```

## Brief Format

### Brief Types

Parsinator recognizes three types of briefs:

1. **Setup Briefs** - Project infrastructure and foundation
2. **Feature Briefs** - Specific feature implementation  
3. **Deployment Briefs** - Testing, documentation, and release

### Required Sections

Each brief type has specific required sections. See the templates in `docs/parsinator/brief_templates/` for complete format specifications.

**Common sections:**
- Project/Feature Name
- Problem Statement  
- Core Tasks (with numbered list format)
- Success Criteria

**Task Format:**
```markdown
## Core Setup Tasks
1. **Task Name**: Brief description of what needs to be done
2. **Another Task**: Another brief description
```

## Advanced Features

### Additive Sessions

Add new tasks to existing projects without ID conflicts:

```bash
# First run - creates initial tasks
python -m src.parsinator.main process-briefs ./initial-briefs/ --output-dir ./tasks

# Later run - adds new tasks to existing project
python -m src.parsinator.main process-briefs ./new-briefs/ \
  --output-dir ./tasks \
  --existing-tasks ./tasks/tasks.json
```

### Dependency Analysis

Parsinator automatically analyzes task relationships:

- **Sequential dependencies** within briefs
- **Cross-brief dependencies** (setup → feature → deployment)  
- **Content-based dependencies** using keyword analysis
- **Confidence scoring** for suggested dependencies

```bash
# Get detailed dependency insights
python -m src.parsinator.main analyze-dependencies ./briefs/ \
  --confidence-threshold 0.5
```

### Template Validation

Ensure your briefs follow the correct format:

```bash
# Auto-detect brief type and validate
python -m src.parsinator.main validate-brief my_brief.md

# Validate against specific template
python -m src.parsinator.main validate-brief my_brief.md --template-type feature
```

## Examples

### Example: Processing Project Briefs

```bash
# Create a directory with your briefs
mkdir my-project-briefs/
# Add: 01_setup.md, 02_core_features.md, 03_deployment.md

# Process all briefs
python -m src.parsinator.main process-briefs my-project-briefs/ \
  --output-dir ./generated-tasks \
  --project-name "My Awesome Project"

# Generate individual task files
python -m src.parsinator.main generate-task-files ./generated-tasks/tasks.json \
  --output-dir ./docs/tasks

# Review the results
python -m src.parsinator.main analyze-tasks ./generated-tasks/tasks.json
```

### Example: Adding New Features

```bash
# You already have tasks from previous brief processing
# Now add new feature briefs

python -m src.parsinator.main process-briefs ./new-features/ \
  --output-dir ./generated-tasks \
  --existing-tasks ./generated-tasks/tasks.json
```

## Output Format

### tasks.json Structure
```json
{
  "master": {
    "tasks": [
      {
        "id": 1,
        "title": "Task Title",
        "description": "Detailed description",
        "priority": "high",
        "dependencies": [2, 3],
        "status": "to-do"
      }
    ],
    "metadata": {
      "created": "2024-01-01T12:00:00",
      "updated": "2024-01-01T12:00:00",
      "description": "Project description"
    }
  }
}
```

### generation_summary.json
Contains detailed analytics about the generation process, including:
- Brief processing statistics
- Dependency analysis results  
- Task distribution by priority
- Confidence scores and warnings

## Integration

Parsinator is designed to integrate with existing task management workflows:

- **JSON Output** - Compatible with task management systems
- **Individual Task Files** - For detailed task descriptions
- **Dependency Tracking** - Maintains task relationships
- **Status Management** - Supports to-do/in-progress/done workflow

## Architecture

- **BriefParser** - Extracts structured data from markdown briefs
- **TaskIDManager** - Handles ID assignment and conflict resolution
- **DependencyMapper** - Analyzes and suggests task relationships  
- **TemplateManager** - Validates brief formats
- **EnhancedTaskGenerator** - Orchestrates the complete workflow

## Contributing

Parsinator is part of the larger AIhelpers project. See the main project documentation for contribution guidelines.

## Examples in Action

Check out the real examples in `docs/parsinator/briefs/` to see exactly how briefs should be formatted and what kind of output Parsinator generates.