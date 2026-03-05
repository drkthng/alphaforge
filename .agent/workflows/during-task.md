---
description: 
---

# During-Task Checklist

1. **Atomic execution** — work on one file or module at a time.
2. **One command per tool call** — never chain commands with `;`, `&&`, or
   `||`. Even trivially related commands (e.g., `mkdir` + `touch`) must be
   separate tool calls.
3. **Frequent builds** — use terminal execution tools to run compilation /
   linting after every logical unit.
4. **UI verification** — if modifying frontend code, use browser verification
   tools to check rendering and console for errors.
5. **Obstacle logging** — if a dependency fails, an API is deprecated, or a
   workaround is needed, log it immediately in `docs/OBSTACLES.md`.
6. **Gate before user review** — before calling `notify_user` or requesting
   any user review, confirm: have you updated `docs/OBSTACLES.md` with any
   issues encountered during this session? If issues were encountered and
   not logged, do it NOW before proceeding.
