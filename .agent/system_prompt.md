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
  Produce a task plan following the format in §2.1.
- **Execute:** Write code in isolated, atomic steps to prevent context rot.
- **Verify:** See §3. Do not declare a task "done" based on output generation
  alone.

### 2.1 Task Plan Format
When creating a task plan (task.md, implementation checklist, or equivalent),
write it so that a **less capable agent** can execute it literally without
making design decisions. Every task item must include:

1. **Exact file paths** — absolute or project-relative paths to every file
   that will be created or modified. Never say "add the relevant files."
2. **Explicit content requirements** — spell out column names, types,
   constraints, function signatures, enum values, and relationships. Do NOT
   say "add the columns from the spec"; list every column with its type.
3. **Verification steps** — after each logical group of tasks, include a
   `[VERIFY]` step with the exact terminal command to run and the expected
   output (e.g., `uv run pytest tests/ -v → ALL tests pass`).
4. **Ordering and dependencies** — number the sections. State if a section
   depends on a prior one. The executor works top-to-bottom and must not
   skip ahead.
5. **No ambiguity** — if there are two reasonable interpretations of a
   requirement, pick one and state it explicitly. Do not leave design
   decisions to the executor.
6. **Imports and wiring** — when a new file imports from another new file,
   state the import path explicitly (e.g., `from alphaforge.models import
   Base`).

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
