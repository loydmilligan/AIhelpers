# Task Management System: AI Agent Instructions

## Overview

This directory contains the task management system for the AIhelpers project. You are responsible for systematically working through tasks using a priority-based, dependency-aware approach.

## Task File Structure

### tasks.json
- **Master task registry** containing all task metadata
- Each task has: `id`, `title`, `description`, `priority`, `dependencies`, `status`
- Valid statuses: `"to-do"`, `"in-progress"`, `"done"`
- Dependencies are arrays of task IDs that must be completed first

### Individual Task Files
- Located in `docs/tasks/[id]_[name].txt`
- Contains detailed implementation steps and requirements
- Follow the header format: `# Task ID: X`, `# Status: [status]`, etc.

## Task Selection Algorithm

**ALWAYS follow this exact process to determine your next task:**

### 1. Start with Task 1
- Begin with task ID 1 regardless of priority
- This establishes the foundation for all subsequent work

### 2. Next Task Selection Process
For each subsequent task, follow these steps **in order**:

1. **Find Unlocked Tasks**: Identify all tasks where ALL dependencies have status `"done"`
   - A task is "dependency-locked" if ANY dependency is `"to-do"` or `"in-progress"`
   - Only consider tasks with status `"to-do"`

2. **Filter by Highest Priority**: Among unlocked tasks, select only those with the highest priority level
   - Priority order: `"high"` > `"medium"` > `"low"`

3. **Choose Lowest ID**: Among the highest priority unlocked tasks, select the one with the lowest task ID number

### 3. Example Walkthrough
Given tasks 1-5 where:
- Tasks 1,2,3: medium priority
- Tasks 4,5: high priority  
- Dependencies: task 2 depends on [1], tasks 4,5 depend on [1], task 3 depends on [2]

**After completing task 1:**
- Unlocked tasks: 2, 4, 5 (all have task 1 completed)
- Highest priority among unlocked: 4, 5 (high priority)
- Lowest ID among highest priority: **Task 4**

## Task Execution Protocol

### When Starting a Task
1. **Update Status**: Change task status from `"to-do"` to `"in-progress"` in BOTH:
   - The `tasks.json` file
   - The individual task file header

2. **Document Start**: Add a comment noting when work began

### When Completing a Task
1. **Update Status**: Change task status from `"in-progress"` to `"done"` in BOTH:
   - The `tasks.json` file  
   - The individual task file header

2. **Verify Completion**: Ensure all requirements in the task details are satisfied

3. **Update Dependencies**: Check if completing this task unlocks any new tasks

## File Modification Instructions

### Updating tasks.json
```json
{
  "id": 1,
  "title": "Setup Python CLI Project Structure", 
  "status": "in-progress"  // ← Change this field
}
```

### Updating Individual Task Files
```
# Task ID: 1
# Title: Setup Python CLI Project Structure
# Status: in-progress  // ← Change this line
# Dependencies: 
# Priority: high
```

## AI Assistant Behavior

### Status Tracking
- **ALWAYS** update both files when changing task status
- **NEVER** work on multiple tasks simultaneously
- **ALWAYS** verify dependencies before starting a task

### Communication
- When starting a task, announce: "Starting Task [ID]: [Title]"
- When completing a task, announce: "Completed Task [ID]: [Title]"
- When selecting next task, explain the selection logic

### Error Handling
- If a task appears blocked by incomplete dependencies, re-verify the dependency status
- If you cannot complete a task, document the blocker and ask for guidance
- Never skip the dependency check

## Current Task Status
**Next Task**: Task 1 (Setup Python CLI Project Structure)
**Reason**: Starting point - no dependencies, highest priority in sequence

## Validation Rules
1. A task can only be started if ALL its dependencies are marked `"done"`
2. Only ONE task can have status `"in-progress"` at any time
3. Task selection MUST follow the priority → ID number hierarchy
4. Both `tasks.json` and individual task files MUST be kept in sync

## Success Metrics
- Systematic progression through tasks without dependency violations
- Consistent status updates across all files
- Clear documentation of task selection reasoning
- Efficient progression toward project completion