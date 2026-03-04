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
