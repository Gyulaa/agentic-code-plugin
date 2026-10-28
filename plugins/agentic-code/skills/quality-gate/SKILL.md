---
name: quality-gate
description: Use for every code change - features, fixes, refactors, UI work, tests - before editing code. The quality procedure (understand, acceptance criteria, test first, smallest good change, machine check, self-review of the diff, independent review, commit, record), the definition of done and the stop rule.
---

# Quality gate

Quality comes first, at the level of a precise professional team: we don't skimp on tests, because finding bugs is the point. Token savings come only from not re-reading and not repeating, never from less verification.

## The procedure for every change
1. **Understand.** State file → the relevant part of the project `CLAUDE.md` → look for an existing solution (search the code; see `working-mode`). If a component or helper already exists, use it; don't write a parallel one. If the diff cannot be described in one sentence, plan first (`spec`).
2. **Acceptance criteria.** Write down (in the reply or the commit body) when it is done: behaviour, states (loading, empty, error, success, forbidden), affected platforms or devices.
3. **Test first.**
   - Bug fix: first a test that fails because of the bug, then the fix.
   - Pure logic (money, time, formatting, rules): unit tests with edge cases (0, negative, midnight, rounding, empty input, very large input).
   - UI component: the project's widget or component test style; screenshot or golden tests only where the project already uses them.
   - Security or data-access rules: a rules test against an emulator or a test environment.
   If the project has no test setup at all, say so and propose the smallest one before writing untested logic.
   - **A failing test is a requirement, not an obstacle.** Never delete, skip, weaken (looser assertion, bigger tolerance, `xfail`, commented-out case) or rewrite a test to make it pass. If you believe the test itself is wrong, stop and say why; the user decides.
   - Fix the root cause, never suppress the error (no blanket `try/except`, no lint-ignore, no `as any`) to get green.
4. **The smallest good change**, in the project's conventions (`match-the-codebase`). The rule of three: abstract only at the third repetition.
5. **Machine check:** the project's check script (`scripts/check.sh` or what `CLAUDE.md` names). The pre-commit hook runs it anyway; never bypass it (`--no-verify` is forbidden). **Show the evidence** (the command and its result line, or a screenshot for UI), don't just assert success.
6. **Self-review of the diff** before committing. Look specifically for:
   - data loss: does a save write the full field list (an omitted field can wipe a stored value)? does a write filter or overwrite more than intended?
   - the same calculation feeding both the preview and the saved value;
   - duplication, dead code, unused imports, leftover debug output;
   - missing error state, unawaited async work, using a context or component after it is gone;
   - user-facing text in the right language; accessibility (labels, touch target size).
7. **Independent review** for large or risky changes (several files, money, time, permissions, data writes): a read-only subagent with a fresh context that sees the diff and the criteria (or the spec), not your reasoning (`working-mode` §5). Ask it for gaps that affect correctness or the requirements only; treat style findings as optional, so the review does not push the change into over-engineering.
8. **Commit per topic** (`git-workflow`): each commit builds and passes on its own; if it depends on another file's change, that change belongs in it too.
9. **Record:** a lasting decision → the project's decision log; a new bug you found but did not fix → the bug list, with where it came from if known.

## Definition of done and the stop rule
Done means: the acceptance criteria are met, the machine check is green, and the diff self-review is clean. After that there is **no "one more small optimisation"**: anything not in the criteria is a new task, and the user decides about it. Optimise performance only after a measured problem.

## Who triggers what
| Level | What |
|---|---|
| **The machine, always** | pre-commit hook (check script), lint rules, CI on pull requests |
| **Claude, when warranted** | steps 1-9 above; UI and accessibility tests on UI changes; `design` rules for UI work, `design-review` after a large UI change, `seo` on public pages; independent review on large changes |
| **Claude proposes, the user starts** | mutation testing, a coverage report on a larger branch, a security review, a dependency upgrade |
| **The human** | product decisions, PR review, testing on a real device, priorities, permission to push and open PRs |

## Known traps
- A bug in a shared component is fixed in the component, with its own test, in its own commit; don't work around it at the call site.
- Live (possibly production) data in a simulator, browser or app: look only, no saves or deletes, unless it is a test environment.
- A merge, even a clean one, can break the build (a rename meeting a new caller): run the check after every merge before pushing; see `git-workflow`, "Merging and conflicts".

## Measuring
In a bug note, mark when a bug came from an earlier Claude change (`origin:` with the commit hash). That shows whether the work improves, and where this procedure needs tightening. Measure rather than assume: in a 2025 randomized study, experienced developers using AI took 19% longer while believing they were 20% faster.
