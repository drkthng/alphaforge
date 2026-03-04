#!/usr/bin/env python3
"""
Spec-Driven Development (SDD) Project Scaffolding Tool

Usage:
    python scaffold-sdd.py                  # scaffold in current directory
    python scaffold-sdd.py my-project       # scaffold in ./my-project/
"""

import os
import subprocess
import sys
from datetime import date

TODAY = date.today().isoformat()

FILES = {

".agent/system_prompt.md": """\
# Global Agent Instructions: Spec-Driven Development

## 1. Critical Startup Protocol
Before running ANY tool, executing ANY command, or modifying ANY file:
1. Run `git status` to confirm you are inside a git repository.
2. If on `main` or `master`, create an isolated branch:
   `git switch -c feature/<task-name>` or `git switch -c fix/<task-name>`.
3. DO NOT proceed until you are on an isolated feature branch.
4. Run the Tech-Stack Detection Protocol (see §6).

## 2. Anti-Vibe Coding Mandate
You are strictly prohibited from generating code based on vague assumptions.
Follow the **Plan → Execute → Verify** loop:
- **Plan:** Read `docs/SPEC.md` and `docs/PROGRESS.md`. Perform gap analysis.
  Draft the list of files you will create or modify.
- **Execute:** Write code in isolated, atomic steps to prevent context rot.
- **Verify:** See §3. Do not declare a task "done" based on output generation
  alone.

## 3. Verification Before Completion
Every task requires a Validation Phase:
- **Code tasks:** You MUST use terminal execution tools to run the build
  command and/or the test suite. Reading or reviewing code you just wrote
  does NOT count as verification.
- **Proof of Work:** Completion requires pasting relevant terminal output
  (build logs, test results) into the chat. If building a UI, you MUST
  explicitly state that you used browser verification tools to check the
  rendering.
- **If verification fails:** Attempt to fix independently by analyzing the
  error. Only escalate to the user after 2 failed fix attempts.

## 4. Build Quality Standards
- **Precision over speed.** The project must build cleanly after every change.
- **TDD preferred:** Write a failing test (Red) → implement (Green) →
  refactor. If TDD is infeasible, use the Micro-Step Protocol (Rule 01).
- **Autonomy:** Analyze errors independently before asking the user.

## 5. Terminal Command Protocol
- **Atomic Execution:** One logical command per tool call.
- **No sequential chaining:** Do NOT use `;` or `&&` to join independent
  commands. Each must be issued and verified separately.
- **Pipes are acceptable:** A single pipeline for data transformation counts
  as one command (e.g., `cat data.json | jq '.items'`).

## 6. Tech-Stack Detection Protocol
1. Scan the project root for package manifests (`package.json`,
   `requirements.txt`, `pyproject.toml`, `Cargo.toml`, `go.mod`,
   `pubspec.yaml`, `*.csproj`, etc.) and read `docs/SPEC.md` section 4
   (Tech Stack).
2. Check `.agent/rules/tech-stacks/` for existing rule files.
3. If a relevant rule file already exists, load it and DO NOT regenerate
   it. The user may manually edit these files to override defaults.
4. If no matching file exists, generate one based on the stack defined in
   SPEC.md. Use the stack name exactly as written in SPEC.md section 4
   for the filename (lowercase, hyphenated). Save it as
   `.agent/rules/tech-stacks/<stack-name>.md`. The file must cover:
   - Mandatory security settings
   - Project structure conventions
   - Build / compile / lint commands
   - Testing framework as required by the Spec
   - Common pitfalls specific to that stack
5. Commit the new rule file: `chore: add <stack> agent rules`.
""",

".agent/rules/00-spec-driven.md": """\
# Rule 00: Spec-Driven Workflow & Context Management

## 1. Context Rot Prevention
AI context windows degrade over long sessions. Countermeasures:
- Keep tasks small and atomic.
- Treat `docs/PROGRESS.md` as your external memory — never rely solely on
  conversational history.
- When a session becomes long or complex, recommend spawning a fresh
  sub-agent or new chat for the next task.

## 2. The Task Lifecycle
Every task follows this exact sequence:
1. **Initialize:** Read `docs/SPEC.md` and `docs/PROGRESS.md`.
2. **Plan:** List the specific files you will create or modify.
3. **Execute:** Write the code.
4. **Verify:** Run build / tests using terminal execution tools. For UI
   changes, verify visually using browser verification tools.
5. **Commit:** `git add` only the files relevant to this task. Write a
   Conventional Commit message (e.g., `feat: add user login endpoint`).
6. **Update:** Mark the task done in `docs/PROGRESS.md`. Log any issues
   in `docs/OBSTACLES.md`.
""",

".agent/rules/01-coding-build.md": """\
# Rule 01: Coding Standards & Buildability

## 1. Test-Driven Development (TDD)
When technically feasible:
1. Write the test first.
2. Run it — confirm it fails (Red).
3. Write the minimum code to pass the test (Green).
4. Refactor while keeping the test green.

## 2. Micro-Step Protocol
When TDD is infeasible (complex UI scaffolding, undocumented APIs, etc.):
- Write no more than **one logical unit** at a time (one function, one
  component, one API endpoint).
- Immediately run the build command using terminal execution tools.
- You are **forbidden** from starting the next unit while the current
  build is failing.

## 3. Error Handling
- Never silently swallow errors.
- Bare `except:` (Python) or empty `catch {}` (JS/TS) blocks are forbidden.
- Errors must be logged with sufficient context or re-raised to the caller.
""",

".agent/rules/02-knowledge.md": """\
# Rule 02: Knowledge Management & Handoffs

## 1. Progress Tracking (`docs/PROGRESS.md`)
- This is the **single source of truth** for project state.
- After every successful commit, check off the completed task.
- Add any new sub-tasks discovered during implementation.
- Format:
  - [x] `YYYY-MM-DD` Task description — **Done**
  - [ ] `YYYY-MM-DD` Task description — **Pending**
  - [ ] `YYYY-MM-DD` Task description — **Blocked** (see OBSTACLES.md#anchor)

## 2. Obstacle Log (`docs/OBSTACLES.md`)
If you spend more than 2 fix attempts on a specific error, document it:

### <anchor-id>: Short title
- **Problem:** What went wrong.
- **Root Cause:** Why it failed.
- **Solution:** How it was fixed (or "Unresolved").
- **Prevention:** How to avoid this in future tasks.

Future agents MUST read this file before beginning work.
""",

".agent/workflows/pre-task.md": """\
# Pre-Task Checklist

1. **Read** `docs/PROGRESS.md` — find the next pending task.
2. **Read** `docs/OBSTACLES.md` — avoid repeating known mistakes.
3. **Tech-stack detection** — run the protocol from System Prompt §6.
   If `.agent/rules/tech-stacks/` is empty or missing a relevant stack,
   generate the rule file now. If a file already exists, load it as-is.
4. **Verify clean baseline** — use terminal execution tools to run the
   build/test command. Confirm the codebase is healthy BEFORE making changes.
5. **Branch check** — confirm you are on a feature branch, not
   `main`/`master`.
""",

".agent/workflows/during-task.md": """\
# During-Task Checklist

1. **Atomic execution** — work on one file or module at a time.
2. **Frequent builds** — use terminal execution tools to run compilation /
   linting after every logical unit.
3. **UI verification** — if modifying frontend code, use browser verification
   tools to check rendering and console for errors.
4. **Obstacle logging** — if a dependency fails, an API is deprecated, or a
   workaround is needed, log it immediately in `docs/OBSTACLES.md`.
""",

".agent/workflows/post-task.md": """\
# Post-Task Checklist

1. **Full build** — use terminal execution tools to confirm the entire
   project builds without errors or warnings.
2. **Test suite** — all unit and integration tests must pass. Paste output.
3. **Atomic commit** — stage only task-relevant files. Use a Conventional
   Commit message (e.g., `feat: add user authentication`).
4. **Update progress** — mark the task complete in `docs/PROGRESS.md`.
5. **Proof of work** — state in the chat: the branch name, the verification
   method used (terminal build, browser preview, test suite), and the result.
""",

"docs/SPEC.md": """\
# Project Specification

> **Fill this out before writing any code.** This is the single source of
> truth that the AI agent reads to understand what to build.

## 1. Overview
<!-- What is this project? One paragraph. -->

## 2. Goals & Non-Goals
<!-- What are you building? What are you explicitly NOT building? -->

## 3. Architecture
<!-- High-level system design. List major components/services. -->

## 4. Tech Stack
<!-- Languages, frameworks, databases, infrastructure. -->
<!-- The agent uses these names to generate rule files in              -->
<!-- .agent/rules/tech-stacks/. Use lowercase hyphenated names         -->
<!-- (e.g., "react", "python-fastapi", "electron").                    -->

## 5. Requirements
<!-- Functional requirements as a numbered list. -->

## 6. Milestones
<!-- Ordered list of deliverables. The agent works through these sequentially. -->
""",

"docs/PROGRESS.md": f"""\
# Project Progress

## Pending
- [ ] `{TODAY}` Define project specification in `docs/SPEC.md`
- [ ] `{TODAY}` Initial scaffolding and dependency installation

## In Progress

## Completed
""",

"docs/OBSTACLES.md": """\
# Known Obstacles

Document solved (and unresolved) technical issues here so that future
sessions and agents do not repeat the same mistakes.

<!-- Use the format from .agent/rules/02-knowledge.md -->
""",

".gitignore": """\
# OS
.DS_Store
Thumbs.db

# Editors
.vscode/
.idea/
*.swp
*.swo

# Dependencies
node_modules/
__pycache__/
*.pyc
.venv/
venv/

# Build output
dist/
build/
*.egg-info/

# Environment
.env
.env.local
""",

"README.md": """\
# {project_name}

> Scaffolded with the Spec-Driven Development (SDD) template.

## Quick Start

1. Fill out `docs/SPEC.md` with your project goals and architecture.
2. Open this project in your AI-enabled IDE (Antigravity, Cursor, etc.).
3. The agent will read `.agent/system_prompt.md`, detect the tech stack,
   auto-generate stack-specific rules, and follow the Plan → Execute → Verify
   loop.

## Structure
.agent/ → Agent instructions (do not delete)
system_prompt.md → Master agent instructions
rules/ → Behavioral rules loaded per-task
tech-stacks/ → Auto-generated by the agent at runtime
workflows/ → Pre / during / post-task checklists
docs/ → Project documentation (source of truth)
SPEC.md → What to build
PROGRESS.md → What has been done / what is next
OBSTACLES.md → Known issues and solutions

text

""",

}

EMPTY_DIRS = [
    ".agent/rules/tech-stacks",
]


def create_scaffold(root: str = "."):
    project_name = os.path.basename(os.path.abspath(root)) or "my-project"

    print(f"Initializing SDD scaffold in: {os.path.abspath(root)}\n")

    # Create empty dirs with .gitkeep
    for d in EMPTY_DIRS:
        path = os.path.join(root, d)
        os.makedirs(path, exist_ok=True)
        gitkeep = os.path.join(path, ".gitkeep")
        if not os.path.exists(gitkeep):
            open(gitkeep, "w").close()
        print(f"  ✓ {d}/  (empty — agent-generated at runtime)")

    # Create files
    for filepath, content in FILES.items():
        full_path = os.path.join(root, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        rendered = content.replace("{project_name}", project_name)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        print(f"  ✓ {filepath}")

    # Initialize git (with crash protection)
    git_dir = os.path.join(root, ".git")
    if not os.path.exists(git_dir):
        print("\n  Initializing git repository...")
        try:
            subprocess.run(
                ["git", "init", root],
                check=True, capture_output=True
            )
            subprocess.run(
                ["git", "-C", root, "add", "."],
                check=True, capture_output=True
            )
            subprocess.run(
                ["git", "-C", root, "commit", "-m",
                 "chore: scaffold SDD project structure"],
                check=True, capture_output=True
            )
            print("  ✓ Git initialized with initial commit")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  ⚠ Git initialization failed (Git not installed or "
                  "repository error). Skipping version control setup.")
    else:
        print("\n  Git repository already exists — skipping init.")

    print(f"\n  Done. Next step: fill out docs/SPEC.md and start building.\n")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    create_scaffold(target)