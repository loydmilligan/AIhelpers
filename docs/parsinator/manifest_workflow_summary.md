# **Manifest Workflow Summary**
## **Context-Efficient Code Analysis for Large Projects**

---

## **The Problem**
Large codebases create context management challenges for AI assistants. Analyzing entire projects consumes excessive tokens and leads to incomplete or shallow analysis. We need a scalable approach that maintains detailed understanding while keeping prompts manageable.

## **The Solution: Three-Tier Manifest System**

### **Tier 1: Directory Manifests** 📁
**Purpose**: Day-to-day development and focused analysis  
**Scope**: Current directory + one level of subdirectories  
**Output**: `directory_manifest.json` (per directory)  
**Context**: Minimal - only immediate directory contents

**When to Use:**
- Working on specific features or components
- Adding/modifying functions in a directory  
- Understanding local code structure
- Regular development workflow

**Command**: `generate_directory_manifest.md`

### **Tier 2: Combined Codebase Manifest** 🔗
**Purpose**: High-level architecture and cross-directory analysis  
**Scope**: Combines all existing directory manifests  
**Output**: `codebase_manifest.json` (project root)  
**Context**: Moderate - metadata from directory manifests only

**When to Use:**
- Architecture reviews and planning
- Understanding project structure
- Identifying dependencies between modules
- Monthly/quarterly project health checks

**Command**: `codebase_from_directory_manifest.md`

### **Tier 3: Full Codebase Analysis** 🔍
**Purpose**: Complete deep analysis (legacy approach)  
**Scope**: Entire project with all files  
**Output**: `codebase_manifest.json` (comprehensive)  
**Context**: Maximum - all code files analyzed

**When to Use:**
- Initial project setup
- Major refactoring decisions
- Complete architecture overhauls
- When directory manifests don't exist yet

**Command**: `generate_manifest.md`

---

## **Workflow Rules & Guidelines**

### **Daily Development** (Use Tier 1)
✅ Generate directory manifests as you work in different parts of the codebase  
✅ Update directory manifest when making significant changes  
✅ Keep directory manifests fresh (< 7 days old)  

### **Weekly/Monthly** (Use Tier 2)
✅ Combine directory manifests for architectural overview  
✅ Review cross-directory dependencies and integration points  
✅ Identify stale directory manifests and refresh as needed  

### **Quarterly/Major Changes** (Use Tier 3)
✅ Run full codebase analysis for comprehensive review  
✅ Use when starting work on unfamiliar large codebases  
✅ Validate architecture after major refactoring  

### **Freshness Management**
- **Fresh**: < 7 days (high confidence)
- **Moderate**: 7-30 days (note age in analysis)
- **Stale**: > 30 days (flag as potentially outdated)
- **Missing**: Directory exists but no manifest

---

## **Benefits of This Approach**

### **🚀 Scalability**
- Works for projects with hundreds of directories
- Context usage scales linearly, not exponentially
- Enables AI analysis of enterprise-scale codebases

### **⚡ Efficiency** 
- Directory manifests: ~1-5% of full analysis context
- Combined manifests: ~10-20% of full analysis context
- Faster analysis and response times

### **🎯 Focused Analysis**
- Detailed understanding where you're working
- High-level awareness of overall architecture
- Right level of detail for the task at hand

### **🔄 Maintainability**
- Only update manifests for changed directories
- Incremental rather than complete re-analysis
- Clear indicators of what needs updating

---

## **Implementation Best Practices**

### **For AI Assistants:**
1. **Start with directory manifest** for most development tasks
2. **Check manifest freshness** before using for important decisions
3. **Escalate to combined manifest** for cross-directory questions
4. **Use full analysis sparingly** and only when necessary

### **For Development Teams:**
1. **Establish manifest update habits** - refresh when working in new directories
2. **Automate combined manifest generation** in CI/CD pipelines
3. **Set freshness alerts** for critical directories
4. **Use manifests for onboarding** new team members

### **Context Budget Management:**
- **Small task**: Directory manifest only (~500-2000 tokens)
- **Medium task**: Directory + 1-2 related directories (~2000-5000 tokens)  
- **Large task**: Combined codebase manifest (~5000-15000 tokens)
- **Major task**: Full analysis (varies widely by project size)

---

## **File Structure Example**

```
my-large-project/
├── codebase_manifest.json           ← Tier 2: Combined view
├── src/
│   ├── directory_manifest.json      ← Tier 1: Local detail
│   ├── models/
│   │   └── directory_manifest.json  ← Tier 1: Local detail
│   └── routes/
│       └── directory_manifest.json  ← Tier 1: Local detail
├── frontend/
│   ├── directory_manifest.json      ← Tier 1: Local detail
│   └── components/
│       └── directory_manifest.json  ← Tier 1: Local detail
└── tests/
    └── directory_manifest.json      ← Tier 1: Local detail
```

---

## **Quick Reference Commands**

| Task | Command | Output | Context Used |
|------|---------|--------|--------------|
| Working in a directory | `generate_directory_manifest.md` | `directory_manifest.json` | Minimal |
| Architecture review | `codebase_from_directory_manifest.md` | `codebase_manifest.json` | Moderate |
| Deep analysis | `generate_manifest.md` | `codebase_manifest.json` | Maximum |

**Remember**: Choose the right tool for the job. Most development tasks only need directory-level detail, while architectural decisions benefit from the combined view.