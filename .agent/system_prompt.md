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
