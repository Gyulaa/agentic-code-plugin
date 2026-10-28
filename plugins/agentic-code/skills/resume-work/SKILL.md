---
name: resume-work
description: Pick up work on the current project from its one-page state file, cheaply. Use when the user starts a session with "continue", "where were we", "resume", or invokes /resume-work.
argument-hint: "[topic or task to continue]"
---

# Resume

Get back into the project with as few tokens as possible, then confirm the plan with the user.

1. Find the project root (the nearest folder with `CLAUDE.md` or `.git` upwards from the working directory). If the working directory holds several repos, the state file is the one the parent `CLAUDE.md` names.
2. **Shared notes (tier L2: `notes/config.json` and `scripts/notes_team.py` exist):** the first call is `python3 scripts/notes_team.py inbox` (it pulls the notes repo when that is safe and prints what happened since your last run, **what waits for you**, ownerless and stale items). Use its output for steps 3 and 4 below; it replaces reading anything else about the notes. For tier L1 run `python3 scripts/notes.py health` only if the user asks about the notes' state.
   Read **only** the state file (`STATE.md`, or the one `CLAUDE.md` names). Don't read decisions, bugs or session logs unless the state file or the topic ($ARGUMENTS) points to them.
3. Check that the state is still true, cheaply:
   - `git -C <repo> fetch --quiet` and `git -C <repo> status -sb` for each repo the state mentions: current branch, ahead/behind, uncommitted files;
   - for every PR the state lists as open: `gh pr view <n> --json state,mergedAt` (if `gh` is available);
   - if the state is older than the code (a branch merged, a PR closed), the code wins: say so, and offer to update the state at the next `/agentic-code:save-work`.
4. Reply in the user's language, in at most ten lines:
   - where things stand (one or two lines);
   - what changed since the state was written (merges, new commits by others);
   - the next step from the state file, or for $ARGUMENTS the first concrete step;
   - anything blocking (a question waiting for the user, a failing check);
   - with shared notes: the "waiting for you" items first, at most five, each in a few words; if the digest says OWNERLESS or TIDY, one line pointing to `/agentic-code:tidy-notes`.
5. Then wait for the user, unless they already asked you to continue with a specific task.

If there is no state file, say so and offer the `project-setup` skill.
