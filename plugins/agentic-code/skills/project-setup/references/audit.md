# Auditing an existing project (read-only)

Goal: a reliable picture in a few thousand tokens. Read manifests, configuration and instructions; do not read source files beyond a sample when needed.

## What to look at, in this order
1. **Git state:** `git status -sb`, the default branch, `git log --oneline -15`, remote branches (`git branch -r`), uncommitted work. Never change anything here.
2. **Instructions for agents:** `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.claude/` (settings, skills, commands). Note length, duplication, contradictions with the code, stale paths.
3. **Docs:** README (does it say how to run and test?), any architecture or decision docs, a changelog.
4. **Manifests and tooling:** `package.json` scripts, `pubspec.yaml`, `pyproject.toml`, `Makefile`, `justfile`, `docker-compose.yml`, lint and format configs, `.editorconfig`, `.gitattributes`.
5. **Tests:** where they are, how many files (`git ls-files | grep -c test`), whether they run (run them once if it is cheap and side-effect free; ask if they need services or credentials).
6. **CI:** `.github/workflows/`, other CI configs: what runs on PRs, on which OS.
7. **Hooks:** `.git/hooks` (non-sample files), `core.hooksPath`, husky, pre-commit, lefthook.
8. **Secrets hygiene:** is `.env` (and similar) ignored? Are there committed secrets? Check with `git ls-files | grep -iE '\.env$|secret|serviceaccount|\.pem$|\.p12$|key\.properties'` and report only file names, never contents.
9. **Production exposure:** config that points at production by default (a default project, a `.env.local` with live URLs). This decides whether a guard is needed.
10. **Cross-platform:** case-sensitive file references (macOS and Windows hide them, Linux fails), line endings, scripts using macOS-only or GNU-only flags, hard-coded absolute paths.

## Report format
| Area | Now | Risk | Proposal | Effort |
|---|---|---|---|---|

Then:
- **Keep:** what works and must not be broken by the setup.
- **Proposed changes,** numbered, most valuable and smallest first. Typical ones:
  1. a short `CLAUDE.md` (or trimming an overlong one; move detail to the README or a skill);
  2. `STATE.md` and the decision and bug logs;
  3. `scripts/check.sh` wrapping the existing commands, plus the pre-commit hook;
  4. `.claude/guard.json` if production is reachable;
  5. fixes the audit found (ignored `.env`, `.gitattributes`, a case-sensitivity bug, a CI gap), each as its own commit;
  6. optional: a project-local skill for a recurring procedure.
- **Out of scope** unless asked: restructuring source code, upgrading dependencies, rewriting tests.
