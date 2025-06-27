# Feature Brief: Parsinator Core Parser

## Feature Name
Core Brief Parser and Task Generator

## Problem Statement
Convert structured project briefs (setup, feature, deployment) into properly formatted, dependency-aware task lists that integrate seamlessly with existing task management workflow.

## Target Users
Solo developers and small teams who want to systematically break down projects into manageable, trackable tasks without manual planning overhead.

## Feature Scope
Parse all three brief types, generate tasks.json with proper dependencies, create individual task files, and handle additive sessions where new briefs build upon existing tasks.

## Core Feature Tasks
### Must-Have Implementation
1. **Brief Parser Engine**: Create parser that reads setup/feature/deployment brief files and extracts structured data including tasks, dependencies, and metadata.
2. **Task ID Management**: Implement automatic task ID assignment that handles both initial generation and additive sessions without ID conflicts.
3. **Dependency Mapper**: Build logic to analyze task relationships within briefs and suggest cross-brief dependencies based on content analysis.
4. **Tasks.json Generator**: Create formatted tasks.json output that maintains existing structure while adding new tasks with proper priority and dependency mapping.
5. **Individual Task File Creator**: Generate individual task files in docs/tasks/ directory with complete headers, details, and implementation guidance.

### Nice-to-Have Enhancements
1. **Dependency Validation**: Check that all referenced dependencies exist and warn about circular dependencies.
2. **Progress Tracking**: Show parsing progress and summary statistics for generated tasks.

## Technical Implementation
- **Primary Components**: BriefParser class, TaskGenerator class, DependencyMapper utility, FileManager for I/O operations
- **Integration Points**: Uses CLI structure from setup, outputs to existing task management system
- **Dependencies**: Requires file I/O framework, integrates with AI prompt generation system
- **Data Flow**: Brief files → Parser → Task objects → JSON formatter → File generator → Individual task files

## User Experience
- **Input**: User provides directory containing brief files (01_setup.md, 02_feature.md, etc.)
- **Process**: System parses briefs sequentially, maps dependencies, generates task IDs, creates output files
- **Output**: Updated tasks.json file and individual task files ready for task management workflow
- **Error Handling**: Clear messages for malformed briefs, missing dependencies, or file access issues

## Success Criteria
- Parse all three brief types without manual intervention
- Generate tasks.json that validates against existing schema
- Create individual task files that match current format exactly
- Handle additive sessions by reading existing tasks.json and appending new tasks
- Suggest logical dependencies between tasks from different briefs

## Constraints
- **Performance**: Process typical project briefs (3-5 files) in under 10 seconds
- **Compatibility**: Output must work with existing task management GEMINI.md rules
- **Usability**: Require minimal user configuration or manual dependency specification

## Dependencies from Other Briefs
- **Project Setup**: Requires CLI framework, file I/O capabilities, and basic project structure

## Enables Future Briefs
- **Deployment**: Provides core functionality that needs testing and documentation