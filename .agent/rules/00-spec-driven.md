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
