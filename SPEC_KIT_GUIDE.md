# GitHub Spec Kit Integration Guide

## ✅ Installation Complete!

GitHub Spec Kit has been successfully installed and configured for the BMS Agent project with Claude Code support.

## What is Spec Kit?

Spec Kit is GitHub's toolkit for **Spec-Driven Development** - a structured workflow that helps you build features methodically:
1. **Establish principles** (constitution)
2. **Define requirements** (specification)
3. **Create implementation plan** (technical design)
4. **Generate tasks** (actionable steps)
5. **Execute** (implementation)

## Available Slash Commands

You can now use these slash commands in Claude Code:

### Core Workflow Commands (Run in Order)

1. **`/speckit.constitution`** - Establish project principles and development guidelines
   - Define coding standards, architecture patterns, quality gates
   - Set up non-negotiable constraints (e.g., security, performance)

2. **`/speckit.specify`** - Create baseline specification
   - Define WHAT to build and WHY (not HOW)
   - Focus on requirements, user stories, acceptance criteria
   - Avoid technical implementation details

3. **`/speckit.plan`** - Create implementation plan
   - Design HOW to build it with your chosen tech stack
   - Architecture decisions, API design, data models
   - Technology choices and integration points

4. **`/speckit.tasks`** - Generate actionable tasks
   - Break down the plan into executable steps
   - Dependency-ordered task list
   - Clear completion criteria for each task

5. **`/speckit.implement`** - Execute implementation
   - Run all tasks to build the feature
   - Automated implementation following the plan

### Enhancement Commands (Optional)

- **`/speckit.clarify`** (run before `/speckit.plan`)
  - Ask structured questions to de-risk ambiguous requirements
  - Reduce uncertainty before technical planning

- **`/speckit.checklist`** (run after `/speckit.plan`)
  - Generate quality checklists
  - Validate requirements completeness and consistency

- **`/speckit.analyze`** (run after `/speckit.tasks`, before `/speckit.implement`)
  - Cross-artifact consistency check
  - Alignment report across constitution, spec, plan, and tasks

## Example Workflow

### Building a New Feature: "Document Search Filters"

```bash
# 1. Establish principles (if not done already)
/speckit.constitution

# 2. Specify requirements
/speckit.specify
# Result: spec stored in .specify/specs/002-search-filters/spec.md

# 3. (Optional) Clarify ambiguities
/speckit.clarify

# 4. Create technical plan
/speckit.plan
# Result: plan stored in .specify/plans/search-filters-plan.md

# 5. (Optional) Validate with checklist
/speckit.checklist

# 6. Generate tasks
/speckit.tasks
# Result: tasks stored in .specify/tasks/search-filters-tasks.md

# 7. (Optional) Analyze consistency
/speckit.analyze

# 8. Implement
/speckit.implement
```

## Directory Structure

Spec Kit creates and uses these directories:

```
/workspace/bms-agent/
├── .claude/
│   └── commands/              # Slash command definitions
│       ├── speckit.constitution.md
│       ├── speckit.specify.md
│       ├── speckit.plan.md
│       ├── speckit.tasks.md
│       ├── speckit.implement.md
│       ├── speckit.clarify.md
│       ├── speckit.checklist.md
│       └── speckit.analyze.md
└── .specify/                  # Your project artifacts
    ├── memory/
    │   └── constitution.md    # Project principles
    ├── specs/
    │   └── 001-bms-agent/     # Existing spec
    │       └── spec.md
    ├── plans/
    │   └── *.md               # Technical plans
    └── tasks/
        └── *.md               # Task lists
```

## Existing Spec Kit Artifacts

You already have some Spec Kit artifacts in `.specify/`:

- **Constitution**: `.specify/memory/constitution.md`
- **Existing Spec**: `.specify/specs/001-bms-agent/spec.md`
- **Plan**: `.specify/plans/runpod-deployment-plan.md`
- **Technical Plan**: `.specify/technical-plan.md`

## Integration with BMS Agent

Spec Kit complements your existing workflow:

- **Existing `tasks.md`**: Your current deployment tasks
- **Spec Kit**: Structured workflow for new features
- **CLAUDE.md**: Context for AI assistants

You can use Spec Kit for:
- Planning new features (e.g., advanced search, analytics)
- Major refactoring projects
- New integrations (e.g., new document types)
- Architecture changes

## Installation Details

### What Was Installed

1. **`uv` package manager** (v0.9.5) - Python package installer
   - Location: `~/.local/bin/uv`
   - Added to PATH in `~/.bashrc`

2. **`specify-cli`** (v0.0.20) - GitHub Spec Kit CLI
   - Installed via: `uv tool install`
   - Command: `specify`
   - Location: `~/.local/bin/specify`

3. **Slash commands** - 8 Claude Code commands
   - Location: `.claude/commands/`
   - Automatically detected by Claude Code

### Persistence on POD

✅ **Persistent** (in `/workspace`):
- `.claude/` directory with slash commands
- `.specify/` directory with your artifacts (specs, plans, tasks)
- All your work and documentation

❌ **Requires reinstall on new POD**:
- `uv` tool (add to `init.sh` if needed)
- `specify-cli` tool (add to `init.sh` if needed)

### Adding to init.sh (Optional)

If you want Spec Kit to survive pod restarts automatically, add to `/workspace/bms-agent/init.sh`:

```bash
# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install specify-cli if not present
if ! command -v specify &> /dev/null; then
    echo "Installing GitHub Spec Kit..."
    uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
fi
```

## Security Note

⚠️ The `.claude/` directory may contain credentials or auth tokens. It has been added to `.gitignore` to prevent accidental commits.

## Resources

- **GitHub Spec Kit Repo**: https://github.com/github/spec-kit
- **Spec-Driven Development Blog**: https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/
- **Local Commands**: In `.claude/commands/` directory

## Quick Reference

```bash
# Check installation
specify --help

# View command details
cat .claude/commands/speckit.specify.md

# Start a new feature spec
/speckit.specify

# Update uv and specify-cli
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git
```

---

**Ready to use!** Start with `/speckit.constitution` to establish your project principles, or jump to `/speckit.specify` to define your next feature.
