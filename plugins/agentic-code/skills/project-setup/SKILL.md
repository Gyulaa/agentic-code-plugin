---
name: project-setup
description: Set up a project for disciplined, token-efficient work with Claude Code. Two modes - build a new project's working environment from scratch from the user's answers, or audit an existing project and restructure and optimise it. Produces a short CLAUDE.md, a one-page state file, decision and bug logs, a one-command check script with a pre-commit hook, an optional production guard, and recommends which skills to use. Use when the user asks to set up, bootstrap, scaffold, initialise, restructure, optimise or "make Claude-ready" a project, or invokes /project-setup.
argument-hint: "[new | existing] [path]"
---

# Project setup

Builds the working environment around the code, not the code itself: instructions for Claude, notes that keep the next session cheap, one command that says "green", a hook that keeps it green, and guard rails. The other skills in this plugin (`working-mode`, `quality-gate`, `git-workflow`, `match-the-codebase`, `privacy-check`, `security-check`, `design`, `design-review`, `seo`, `resume-work`, `save-work`) assume this layout.

Files next to this SKILL.md: `references/interview.md` (questions), `references/audit.md` (existing-project audit), `references/stacks.md` (check commands per stack), `references/code-graph.md` (optional code graph), `templates/` (the files to generate). Read a reference only when you reach the step that needs it.

## Principles
- **Ask, then show the plan, then write.** Nothing is written before the user approves the file list. Never overwrite an existing file: merge into it, and show the diff.
- **As small as the project allows.** A weekend project gets four files; a team product with several repos gets the full layout. Every file must earn its place: if nobody will read or run it, leave it out.
- **Shared repo or personal?** In a repo other people work in, adding files is the team's decision: commit them on a branch and propose a PR, and put personal preferences into `CLAUDE.local.md` (git-ignored), never into the shared `CLAUDE.md`.
- **`CLAUDE.md` holds only what Claude cannot infer from the code,** and the user reviews it. It is loaded every session, so every line costs tokens and attention: for each line ask "would removing this cause a mistake?". No file-by-file tour, no architecture essay, no generic advice ("write clean code"). In a 2026 ETH Zurich study, auto-generated context files lowered task success in most settings and raised cost by about 20%, while human-curated ones helped slightly: write a minimal draft and ask the user to edit it.
- **Rules that must hold every time become hooks or scripts,** not more `CLAUDE.md` text: instructions are advisory, hooks are deterministic.
- **Verify what you generate:** the check script must actually run and pass (or fail for a real reason) before you call the setup done.
- Reply in the user's language. Generated `CLAUDE.md` and notes use the language the user picks (default: the language of the conversation); code-facing files (scripts, commit messages) follow the project's convention, default English.

## 0. Choose the mode
- `$ARGUMENTS` says `new` or `existing`: use it.
- Otherwise look at the target folder (default: the working directory): source files or a git history → **existing**; empty or near-empty → **new**. If unclear, ask.

## Mode A: a new project
1. **Interview** with `references/interview.md`: ask the questions in one or two short rounds (use the question tool if available), not one by one. Skip what the user already said.
2. **Pick the scale:**
   | Scale | When | Notes layout |
   |---|---|---|
   | **S** | personal or hobby, one repo, one person | `STATE.md`, `docs/decisions.md`, `docs/bugs.md` |
   | **M** | a real product, one or two people, one repo | as S, plus `docs/agent-brief.md`, a guard if there is production |
   | **L** | a team, several repos | a notes folder or repo: `decisions/`, `bugs/`, `sessions/`, one file per item with an index; `STATE.md` at its root; the parent-folder `CLAUDE.md` maps the repos |
3. **Show the plan:** the file tree you will create, each file with one line on why, and the commands you will run (`git init`, `git config core.hooksPath .githooks`). Wait for approval.
4. **Generate** from `templates/` (fill every `{{placeholder}}`; delete template sections that don't apply instead of leaving them empty):
   - `CLAUDE.md` from `templates/CLAUDE.md`: what the project is, the commands, the non-negotiables, where things are. Keep it under about 80 lines; detail belongs in the README or in skills.
   - `STATE.md` from `templates/STATE.md`.
   - `docs/decisions.md`, `docs/bugs.md` from the templates (scale S/M); for scale L the folder layout described in `templates/notes-L.md`.
   - `scripts/check.sh` from `templates/scripts/check.sh`, configured with the stack's commands from `references/stacks.md`; `chmod +x`.
   - `.githooks/pre-commit` and `.githooks/commit-msg` from `templates/githooks/` (the second strips AI attribution lines from every commit message), and `git config core.hooksPath .githooks` (this is per clone; say it in the README too).
   - `.claude/guard.json` from `templates/claude/guard.json` **only if there is a production system** the agent must not change (a database, a deploy target, a payment account). The plugin's hook enforces it.
   - `{{SECURITY_LINE}}` in `CLAUDE.md` becomes `, \`security-check\` on security-relevant changes` for any product with accounts, roles, payments, secrets or server endpoints, gate or not; otherwise delete it.
   - `CLAUDE.local.md` from `templates/CLAUDE.local.md`, and `CLAUDE.local.md` added to `.gitignore`.
   - `.claude/settings.json` from `templates/claude/settings.json`: an allowlist for the safe, frequent commands (the check script, read-only git, the test runner), so the user is not clicking through approvals. Never allowlist push, deploy or anything touching production.
   - If the user also uses other coding agents (Codex, Cursor, Gemini CLI): an `AGENTS.md` containing only `See CLAUDE.md.` plus anything tool-specific, so there is one source of truth.
   - Optional, for long unattended runs: a `Stop` hook that runs `scripts/check.sh` and keeps the turn going until it passes (see the Claude Code hooks documentation). Offer it, don't add it by default.
   - **The risk gate**, only when the user wants it (recommend it for scale M and L, say nothing about it for S): `scripts/risk_level.py` and `scripts/test_debt.py` copied as they are (`chmod +x`), and `scripts/risk-map.json` **written from the project's risky areas (interview question 12) and its real folder layout**, never left empty or with placeholders. Fill `skip` (docs, assets, lock files), `test`, `critical` (a `why` for each; an `anchor` regular expression where only part of a file is risky; `server_twin` where the same logic lives on both sides of a contract), `sensitive`, `normal` (the source paths that exist), `ui`, and `test_one` from `references/stacks.md`. The `.githooks/pre-commit` template runs the gate by itself once `scripts/risk_level.py` exists. After writing the map run `python3 scripts/risk_level.py map-coverage` and extend the map until it lists nothing; then run `python3 scripts/risk_level.py level` on a real or sample diff and show the user what it says. Tell them plainly: a commit that lacks the work its level asks for stops, with the exact command to run; the thresholds are first estimates to adjust after a few weeks. In `CLAUDE.md`, `{{RISK_COMMAND}}` becomes `python3 scripts/risk_level.py level   # test level of the current change; the pre-commit hook runs the gate` (delete the line when there is no gate).
   - Scale M/L: `docs/agent-brief.md` from `templates/agent-brief.md` (the block pasted at the top of every subagent prompt).
   - Scale M/L, or whenever other people read the repo: a README written for a person, not for Claude: what this is, how to start, the daily workflow, where things are, the rules, and a **"What's new"** section at the top (newest first, one dated line each, what changed and what to do differently). `save-work` keeps it current, so someone back from a break reads only that section.
   - Large codebases or several connected repos: offer the code graph from `references/code-graph.md`. Don't add it to small projects.
   - A project with a user interface: offer a `DESIGN.md` at the root, written with the `design` skill from its `templates/DESIGN.md` (the Google Stitch format: design tokens plus how to use them). Don't fill it with invented values: ask, or derive it from an existing theme.
5. **Verify:** run `scripts/check.sh` once. If the project has no tests yet, the test step is skipped with a note, not faked. Run the guard against one forbidden and one allowed example command if you created it.
6. **Report:** what was created, how to use it day to day (`/agentic-code:resume-work` at the start, `/agentic-code:save-work` at the end, `scripts/check.sh` before a commit), and which skills apply (see "Skills to recommend" below). Offer the first commit; commit only on a yes.

## Mode B: an existing project
1. **Audit, read-only,** with `references/audit.md`. It is cheap by design: manifests, top-level layout, existing instructions, git state, CI, test setup; no full-code reading.
2. **Report the findings** in a short table: area, current state, risk, proposed change, effort (S/M/L). Start with what already works and must be kept. Then a numbered list of proposed changes, smallest and most valuable first.
3. **The user picks** which changes to make (all, some, none). Restructuring source code (moving folders, renaming modules) is out of scope unless the user explicitly asks; propose it as a separate task.
4. **Apply on a branch** (`chore/claude-setup`), following `git-workflow`: merge into existing `CLAUDE.md` and README instead of replacing them; move outdated instructions into the notes as history rather than deleting them silently; never touch secrets or `.env` files.
5. **Verify** as in mode A step 5, and run the project's existing checks too.
6. **Report** the before/after, the remaining recommendations, and offer the commit and, with separate permission, the PR.

## Skills to recommend
After setup, tell the user which skills apply to this project and when:
- always: `working-mode` (context order, tokens, safety), `git-workflow`;
- before any code change: `quality-gate` and `match-the-codebase`;
- if the product handles other people's personal data: `privacy-check`;
- if it has accounts, roles, payments, secrets or any server endpoint: `security-check` on every security-relevant change;
- if it has a user interface (web or native): `design` for new screens and redesigns, `design-review` after a large UI change;
- if it has public pages that should be found in search: `seo`;
- daily: `/agentic-code:resume-work` and `/agentic-code:save-work`;
- every few weeks, or when the Friction list grows: `/agentic-code:improve-workflow`.
If the project needs something these don't cover (a recurring domain procedure, a deploy runbook), propose a project-local skill in `.claude/skills/<name>/SKILL.md` with a one-line description of what it would hold, and write it only if the user wants it.
