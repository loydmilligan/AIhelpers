# Parsinator Quick Start Guide

Get up and running with Parsinator in 5 minutes! 🚀

## TL;DR - Try It Now

```bash
cd /path/to/AIhelpers

# Test the CLI
python3 -m src.parsinator.main hello

# Process example briefs
python3 -m src.parsinator.main process-briefs docs/parsinator/briefs/ --output-dir ./my-tasks

# Check results
cat my-tasks/tasks.json
```

## Step 1: Verify Installation

```bash
cd /home/mmariani/Projects/AIhelpers
python3 -m src.parsinator.main hello
```

**Expected output:** `Parsinator is ready!`

## Step 2: Try Example Briefs

Process the included example briefs to see Parsinator in action:

```bash
# Process all example briefs
python3 -m src.parsinator.main process-briefs docs/parsinator/briefs/ \
  --output-dir ./example-output \
  --project-name "My Example Project"
```

**What this does:**
- Finds 3 example briefs (setup, feature, deployment)
- Parses them into 16 structured tasks
- Maps dependencies between tasks
- Generates `tasks.json` and `generation_summary.json`

## Step 3: Examine the Output

```bash
# Check the main task file
cat example-output/tasks.json | head -30

# See detailed generation report
cat example-output/generation_summary.json
```

**You'll see:**
- 16 tasks with proper IDs and dependencies
- Priority assignments (high/medium/low)
- Dependency relationships between tasks
- Metadata about the generation process

## Step 4: Create Your Own Brief

Copy a template and customize it:

```bash
# Copy a template
cp docs/parsinator/brief_templates/project_brief_template.md my_project_brief.md

# Edit with your project details
# Then process it
python3 -m src.parsinator.main process-brief my_project_brief.md --output-dir ./my-project
```

## Key Commands You'll Use

### Process Briefs
```bash
# Single brief
python3 -m src.parsinator.main process-brief my_brief.md --output-dir ./output

# Multiple briefs
python3 -m src.parsinator.main process-briefs ./my-briefs/ --output-dir ./output

# Add to existing project
python3 -m src.parsinator.main process-briefs ./new-briefs/ \
  --existing-tasks ./output/tasks.json --output-dir ./output
```

### Validation & Analysis
```bash
# Validate brief format
python3 -m src.parsinator.main validate-brief my_brief.md

# Analyze dependencies
python3 -m src.parsinator.main analyze-dependencies ./briefs/

# Check generated tasks
python3 -m src.parsinator.main analyze-tasks ./output/tasks.json

# Generate individual task files
python3 -m src.parsinator.main generate-task-files ./output/tasks.json --output-dir ./docs/tasks
```

## Brief Format Basics

Every brief needs these sections:

```markdown
# Project Name

## Problem Statement
What you're trying to solve

## Core [Setup/Feature/Deployment] Tasks
1. **Task Name**: Brief description
2. **Another Task**: Another description

## Success Criteria
- Measurable outcome 1
- Measurable outcome 2
```

## Common Use Cases

### New Project
```bash
# Create setup brief → process → get foundation tasks
python3 -m src.parsinator.main process-brief setup_brief.md --output-dir ./project
```

### Add Features
```bash
# Add feature briefs to existing project
python3 -m src.parsinator.main process-briefs ./features/ \
  --existing-tasks ./project/tasks.json --output-dir ./project
```

### Release Preparation
```bash
# Process deployment brief last
python3 -m src.parsinator.main process-brief deployment_brief.md \
  --existing-tasks ./project/tasks.json --output-dir ./project
```

## Troubleshooting

### "Module not found" error
- Make sure you're in the AIhelpers root directory
- Use `python3` not `python`

### "No brief files found"
- Check that your `.md` files are in the specified directory
- Verify the directory path is correct

### Validation errors
- Compare your brief to the templates in `docs/parsinator/brief_templates/`
- Ensure required sections are present with proper `##` headings

### Empty output
- Check that your brief has numbered task lists: `1. **Task**: Description`
- Verify the brief follows the template format

## Next Steps

1. **Review the README** - Full documentation at `src/parsinator/README.md`
2. **Study the examples** - Check `docs/parsinator/briefs/` for real examples
3. **Use templates** - Start with `docs/parsinator/brief_templates/`
4. **Integrate with workflow** - Use the generated `tasks.json` in your task management system

## Example Workflow

```bash
# 1. Create your briefs
mkdir my-project-briefs
cp docs/parsinator/brief_templates/* my-project-briefs/
# Edit the templates with your project details

# 2. Process them
python3 -m src.parsinator.main process-briefs my-project-briefs/ \
  --output-dir ./my-project-tasks \
  --project-name "My Awesome Project"

# 3. Generate individual task files
python3 -m src.parsinator.main generate-task-files ./my-project-tasks/tasks.json \
  --output-dir ./my-project-tasks/individual-tasks

# 4. Review results
python3 -m src.parsinator.main analyze-tasks ./my-project-tasks/tasks.json

# 5. Start working!
# Use tasks.json with your task management system
```

That's it! You now have structured, dependency-aware tasks generated from your project briefs. 🎉