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
