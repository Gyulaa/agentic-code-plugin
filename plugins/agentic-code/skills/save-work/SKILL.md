---
name: save-work
description: Save the outcome of the current session into the project's notes - the one-page state file, decisions, bugs and, in larger projects, a session log - so the next session can resume cheaply. Use when the user invokes /agentic-code:save-work, after finishing a task, a commit or a decision, or before ending a long session.
argument-hint: "[short description of what was done]"
---

# Save

Write down what the next session needs, in the project's own note layout (the project `CLAUDE.md` says where; the defaults come from `project-setup`).

1. **State file** (`STATE.md`): rewrite it to stay **one page**. Keep: what the project is (one line), the current state of each active thread, open PRs and branches, what is blocked and on whom, the next step. Remove what is finished and no longer useful; history belongs in the session log or git, not here. Date it (`YYYY-MM-DD`, from the system clock).
2. **Decisions:** every lasting decision made this session gets an entry in the decision log (`docs/decisions.md`, or one file per decision in larger projects): date, the decision, why, what it affects. A changed decision is updated, not duplicated.
3. **Bugs:** every bug found but not fixed gets an entry in the bug list (`docs/bugs.md` or one file per bug): ID (the next free number), severity (critical / high / medium / low), status (open / in progress / PR open / fixed), one line, where it is in the code, and `origin:` if it came from an earlier change.
4. **Session log** (only if the project keeps one, typically larger or team projects): `docs/sessions/YYYY-MM-DD-short-topic.md` with what was done, what was created or changed, and links to the decisions and bugs above.
5. **What's new** (if the README has a "What's new" section, typically in team projects): if this session changed something a teammate must know to work correctly (a new rule or workflow, a new command or tool, a decision that changes how people work, a breaking change), add one dated line at the top, written for a person who was away: what changed and what to do differently, with a link to the decision or note. Routine fixes don't go here. Keep the section to about 15 lines; older lines can go, git keeps them. If the change makes another README section untrue, fix that section too.
6. **Friction:** if something was slow or failed repeatedly this session, add one line to the state file's "Friction" list (create it if missing): what, how often, rough cost. `/agentic-code:improve-workflow` works from this list.
7. **Never** write a secret, token, password or personal data into notes. Never paste whole files; link to them.
8. Show the user, in a few lines, what you wrote and where. **Commit only if the user asks** or the project's rules say notes are committed automatically; pushing still needs permission (`git-workflow`).

$ARGUMENTS, if given, is the user's own summary of the session: use it as the starting point.
