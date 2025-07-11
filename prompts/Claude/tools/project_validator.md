# Project Validator - Multi-Phase Organization and Validation Command

```bash
claude-code "Validate and organize project structure for current development phase.

## Task: Project Organization and Phase Validation

**Phase:** [post_productbrief/post_specifications/post_task_generation/final_setup]

**Arguments:** phase_name [additional_context]

**Example Usage:**
- `claude-code project_validator \"post_productbrief\"`
- `claude-code project_validator \"post_specifications\"`
- `claude-code project_validator \"post_task_generation\"`
- `claude-code project_validator \"final_setup\"`

Start your response with: \"🔧 **PROJECT_VALIDATOR EXECUTING** - Organizing project for [PHASE] phase\"

## Phase-Aware Project Organization:

### 1. Detect Current Project State
- **Scan existing files** and directories in current location
- **Identify phase outputs** (research results, specifications, tasks, etc.)
- **Assess organization level** (what's organized vs. what needs organizing)
- **Detect git repository status** (initialized, commits needed, etc.)

### 2. Phase-Specific Organization Logic

#### **Phase: post_productbrief**
**Expected Inputs:**
- ProductBrief orchestration results (various research files)
- Market research reports
- User research reports  
- Feature analysis files
- MVP validation results

**Organization Actions:**
```
project-root/
├── research/
│   ├── market_research/
│   │   └── [Move all market research files here]
│   ├── user_research/
│   │   └── [Move all user research files here]
│   ├── feature_analysis/
│   │   └── [Move all feature analysis files here]
│   └── mvp_validation/
│       └── [Move MVP validation results here]
├── .gitignore (create if missing)
└── README.md (create initial version)
```

**Git Actions:**
- Initialize repository if not exists
- Add and commit research phase: \"Research phase complete: ProductBrief validation\"

#### **Phase: post_specifications**
**Expected Inputs:**
- Feature specifications (JSON + MD)
- UI specifications (JSON + MD)
- Product requirements document (JSON + MD)
- Pipeline reports
- Implementation guides

**Organization Actions:**
```
project-root/
├── research/ (from previous phase)
├── docs/
│   ├── specifications/
│   │   ├── feature_specifications.json
│   │   ├── feature_specifications.md
│   │   ├── ui_specification.json
│   │   ├── ui_specification.md
│   │   ├── product_requirements_document.json
│   │   └── product_requirements_document.md
│   └── implementation_guides/
│       └── [Move implementation guides here]
├── claude.md (create from specifications context)
└── README.md (update with project overview from specs)
```

**Git Actions:**
- Commit specifications phase: \"Specifications complete: Ready for task generation\"

#### **Phase: post_task_generation**
**Expected Inputs:**
- Adaptive task list (JSON + MD)
- Task breakdown analysis
- Implementation timeline

**Organization Actions:**
```
project-root/
├── research/ (preserved)
├── docs/ (preserved + additions)
│   ├── specifications/ (preserved)
│   └── project_planning/
│       ├── adaptive_task_list.json
│       ├── adaptive_task_list.md
│       ├── implementation_timeline.md
│       └── complexity_analysis.md
├── tasks/
│   ├── task_list.md (converted from JSON for manifest workflow)
│   ├── prepared/ (empty, for future use)
│   └── completed/ (empty, for future use)
├── claude.md (update with task workflow context)
└── README.md (update with implementation approach)
```

**Git Actions:**
- Commit task planning phase: \"Task planning complete: Ready for implementation setup\"

#### **Phase: final_setup**
**Expected Inputs:**
- All previous phase outputs organized
- Ready to begin manifest-driven development

**Organization Actions:**
```
project-root/
├── research/ (preserved)
├── docs/ (preserved)
├── tasks/ (preserved)
├── codebase_manifest.json (create from project context)
├── claude.md (final update with complete workflow)
├── README.md (final update with quick start guide)
└── .gitignore (complete version)
```

**Git Actions:**
- Commit final setup: \"Project setup complete: Ready for manifest-driven implementation\"

### 3. Adaptive File Detection and Organization

#### **Smart File Detection:**
- **Don't assume specific filenames** - scan for content patterns
- **Detect file purposes** based on content and structure
- **Handle variations** in naming conventions from different orchestrators
- **Preserve important files** that don't fit expected patterns

#### **Organization Logic:**
```
FOR each file in current directory:
    IF file matches market research pattern:
        MOVE to research/market_research/
    ELIF file matches user research pattern:
        MOVE to research/user_research/
    ELIF file matches feature specification pattern:
        MOVE to docs/specifications/
    ELIF file matches task list pattern:
        CONVERT and MOVE to tasks/
    ELSE:
        LOG as unrecognized, preserve in current location
```

### 4. Project Context File Creation

#### **claude.md Creation/Updates:**
Base content on actual project files rather than templates:

```markdown
# [Project Name] - AI Workflow Guide

> Generated from project specifications and task breakdown

## Project Overview
[Extract from feature specifications and PRD]

## Development Approach
This project uses manifest-driven development with systematic task implementation.

## Current Phase: [Current phase status]

## Available Commands
The manifest-driven workflow uses commands from ~/.claude/commands/:

- `claude-code generate_manifest` - Analyze codebase and create/update manifests
- `claude-code process_task \"Task-X.X\"` - Prepare tasks for implementation
- `claude-code implement_task \"tasks/prepared/Task-X.X.json\"` - Implement prepared tasks
- `claude-code check_task \"Task-X.X\"` - Validate implementation
- `claude-code resolve_mismatch \"Task-X.X\"` - Handle implementation discrepancies
- `claude-code commit_task \"Task-X.X\"` - Commit completed tasks

## Project Context
- **Specifications**: See docs/specifications/ for detailed requirements
- **Task Planning**: See docs/project_planning/ for implementation breakdown
- **Research**: See research/ for market and user validation

## Implementation Workflow
1. Review next task in tasks/task_list.md
2. Process task: `claude-code process_task \"Task-X.X\"`
3. Implement: `claude-code implement_task \"tasks/prepared/Task-X.X.json\"`
4. Validate: `claude-code check_task \"Task-X.X\"`
5. Commit: `claude-code commit_task \"Task-X.X\"`

## Project Status
[Current implementation status and next steps]
```

#### **codebase_manifest.json Creation:**
Generate from actual project specifications:

```json
{
  \"version\": \"1.0\",
  \"generated\": \"[current timestamp]\",
  \"project\": {
    \"name\": \"[extract from specifications]\",
    \"description\": \"[extract from PRD]\",
    \"version\": \"0.1.0\",
    \"tech_stack\": \"[infer from feature specifications]\",
    \"deployment\": \"[extract from specifications]\",
    \"repository\": \"[current git remote or local]\"
  },
  \"documentation\": {
    \"specifications\": \"docs/specifications/\",
    \"research\": \"research/\",
    \"task_planning\": \"docs/project_planning/\",
    \"implementation_guide\": \"claude.md\"
  },
  \"files\": {
    \"// Note\": \"Files will be added as implementation progresses\"
  },
  \"dependencies\": {
    \"// Note\": \"Dependencies will be added based on implementation needs\"
  },
  \"architecture\": {
    \"main_flow\": \"[extract from specifications]\",
    \"data_flow\": \"[extract from UI and technical specifications]\",
    \"configuration\": \"[extract from implementation requirements]\",
    \"key_components\": \"[list from feature specifications]\",
    \"integration_points\": \"[extract from technical requirements]\"
  },
  \"development\": {
    \"approach\": \"manifest-driven development with task-by-task implementation\",
    \"workflow\": \"process_task -> implement_task -> check_task -> resolve_mismatch (if needed) -> commit_task\",
    \"task_status\": \"[current phase status]\",
    \"current_phase\": \"[implementation_ready/in_progress]\",
    \"version_control\": \"git commits tied to task completion\"
  }
}
```

### 5. Quality Validation for Each Phase

#### **Validation Checks:**
- **File Completeness**: All expected outputs present and organized
- **Content Quality**: Key files contain expected content structure
- **Git Status**: Repository properly initialized and committed
- **Workflow Readiness**: Next phase can begin with organized inputs

#### **Error Recovery:**
- **Missing Files**: Report what's missing, continue with available files
- **Misorganized Content**: Detect and relocate improperly placed files
- **Git Issues**: Handle repository problems gracefully
- **Workflow Blockers**: Identify and report issues preventing next phase

### 6. Phase Transition Reporting

**Generate Phase Report:**
```json
{
  \"phase_validation\": {
    \"phase_name\": \"[post_specifications]\",
    \"validation_timestamp\": \"[ISO timestamp]\",
    \"organization_status\": \"[complete/partial/failed]\",
    \"files_organized\": \"[count and list]\",
    \"git_status\": \"[committed/pending/issues]\",
    \"next_phase_ready\": true,
    \"issues_found\": [\"[Any problems encountered]\"],
    \"recommendations\": [\"[Next steps or improvements]\"]
  }
}
```

## Success Criteria by Phase:

### **post_productbrief:**
- ✅ Research files organized by type
- ✅ Git repository initialized and first commit made
- ✅ Ready for specification generation

### **post_specifications:**
- ✅ All specifications organized and accessible
- ✅ claude.md created with project context
- ✅ Ready for task generation

### **post_task_generation:**
- ✅ Task breakdown organized and converted for workflow
- ✅ Implementation timeline established
- ✅ Ready for final project setup

### **final_setup:**
- ✅ Complete project structure organized and documented
- ✅ Manifest-driven development ready to begin (using global commands)
- ✅ All documentation and guides in place
- ✅ Team can start implementing tasks immediately

## Error Handling:

### **Common Issues:**
- **Phase Mismatch**: Called for wrong phase based on available files
- **Missing Outputs**: Expected files from previous orchestrations not found
- **Git Problems**: Repository issues or commit failures
- **File Conflicts**: Multiple files that could serve same purpose

### **Recovery Strategies:**
- **Graceful Degradation**: Work with available files, report missing pieces
- **Smart Detection**: Use content analysis when filenames are unexpected
- **User Guidance**: Provide clear next steps when manual intervention needed
- **State Preservation**: Never delete files, only organize and create

The project validation and organization is complete for the [PHASE] phase."
```