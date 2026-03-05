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
6. **Write task.md** — produce the task plan following System Prompt §2.1
   format EXACTLY. Every item must have exact file paths, literal code
   snippets or diffs, `[VERIFY]` commands with expected output, and
   numbered dependency ordering. A vague high-level checklist is NOT
   acceptable — the plan must be executable by a less capable agent
   without making any design decisions.
