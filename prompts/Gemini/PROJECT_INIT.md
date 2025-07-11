## Prompt: Initialize a New Software Project

**Objective:** Set up a new project repository with a clean, standard structure. 


**Instructions for the AI Assistant:**

Before you begin, ask the user for the following information:

1.  **Project Name:** What is the name of the project?
2.  **Primary Language:** What is the main programming language? (e.g., Python, JavaScript/TypeScript, Go, Rust)
3.  **AI Model Files:** Should any AI model-specific configuration files be created? (e.g., `GEMINI.md`, `COPILOT.md`)

Once you have this information, perform the following setup steps:

### 1. Git Initialization

- [ ] Run `git init` to initialize a new Git repository.

### 2. Core Directory Structure

Create the following directories:

- [ ] `src/` (or `app/`, `lib/` depending on language conventions) for the main source code.
- [ ] `tests/` (or `spec/`) for test files.
- [ ] `docs/` for documentation.
- [ ] `scripts/` for helper or build scripts.

### 3. Core Project Files

Create the following files with standard, sensible defaults:

- [ ] `README.md`: Include the project name as the main heading.
- [ ] `.gitignore`: Use a comprehensive template for the specified primary language (e.g., from gitignore.io).
- [ ] `CHANGELOG.md`: An empty file to track changes.
- [ ] `LICENSE`: An empty file. Advise the user to add a license like MIT or Apache 2.0.
- [ ] `.env.example`: An example file for environment variables.

### 4. Language-Specific Setup

Based on the user's choice of primary language, perform these additional steps:

- **For Python:**
    - [ ] Create a virtual environment (e.g., `python3 -m venv venv`).
    - [ ] Create an empty `requirements.txt` file.
- **For JavaScript/TypeScript (Node.js):**
    - [ ] Run `npm init -y` to create a `package.json` file.
    - [ ] If TypeScript, initialize a `tsconfig.json` (`npx tsc --init`).

### 5. AI Model Configuration

- [ ] If the user requested any AI model configuration files, create them with a basic header (e.g., `# [MODEL_NAME] Configuration`).

**Final Output:**

Confirm that all steps have been completed and list the created file and directory structure.