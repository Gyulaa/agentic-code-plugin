---
name: save
description: Save the outcome of the current session into the project's notes - the one-page state file, decisions, bugs and, in larger projects, a session log - so the next session can resume cheaply. Use when the user invokes /save, after finishing a task, a commit or a decision, or before ending a long session.
argument-hint: "[short description of what was done]"
---

# Save

Write down what the next session needs, in the project's own note layout (the project `CLAUDE.md` says where; the defaults come from `project-setup`).

1. **State file** (`STATE.md`): rewrite it to stay **one page**. Keep: what the project is (one line), the current state of each active thread, open PRs and branches, what is blocked and on whom, the next step. Remove what is finished and no longer useful; history belongs in the session log or git, not here. Date it (`YYYY-MM-DD`, from the system clock).
2. **Decisions:** every lasting decision made this session gets an entry in the decision log (`docs/decisions.md`, or one file per decision in larger projects): date, the decision, why, what it affects. A changed decision is updated, not duplicated.
3. **Bugs:** every bug found but not fixed gets an entry in the bug list (`docs/bugs.md` or one file per bug): ID (the next free number), severity (critical / high / medium / low), status (open / in progress / PR open / fixed), one line, where it is in the code, and `origin:` if it came from an earlier change.
4. **Session log** (only if the project keeps one, typically larger or team projects): `docs/sessions/YYYY-MM-DD-short-topic.md` with what was done, what was created or changed, and links to the decisions and bugs above.
5. **Never** write a secret, token, password or personal data into notes. Never paste whole files; link to them.
6. Show the user, in a few lines, what you wrote and where. **Commit only if the user asks** or the project's rules say notes are committed automatically; pushing still needs permission (`git-workflow`).

$ARGUMENTS, if given, is the user's own summary of the session: use it as the starting point.
