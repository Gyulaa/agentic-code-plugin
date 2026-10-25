# Interview for a new project

Ask in at most two rounds. Offer sensible defaults so the user can answer with one word. Skip anything already answered.

## Round 1: what and for whom
1. **What is it,** in one sentence? (Becomes the first line of `CLAUDE.md`.)
2. **Who uses it?** Only you / a few known people / the public. (Decides whether `privacy-check` applies and how strict the guard must be.)
3. **Stack:** language and framework, or "you suggest". If the user asks you to suggest, propose one with a one-line reason and the alternative.
4. **Where does it run?** Local only / a server or hosting you name / an app store. Is there a **production** system (database, deploy target, payment account) the agent must never change? Its identifiers go into the guard.
5. **Alone or with others?** Decides the scale (S/M/L) and whether the repo is shared (shared → team files by PR, personal preferences in `CLAUDE.local.md`).

## Round 2: how you want to work (defaults in brackets)
6. **Git hosting** and the default branch name [GitHub, `main`]. Should the repo be created now? (Creating a remote repo is outward-facing: only on an explicit yes.)
7. **Languages:** notes and `CLAUDE.md` [the conversation's language]; commit messages and code comments [English]; user-facing text [ask].
8. **Tests:** what level is expected [unit tests for logic, a widget or component test for UI, no end-to-end at first]. Any device or browser matrix (smallest screen, dark mode, large text)?
9. **Hard rules** the agent must never break (for example "never change the database schema without asking", "never touch the payments code"). These become the non-negotiables in `CLAUDE.md`.
10. **Style preferences** you already know (formatting, naming, comment density, no em dash in UI text). Unknown is fine: they can be added to `CLAUDE.local.md` later, whenever you correct the agent.

## Turning answers into files
| Answer | Goes to |
|---|---|
| 1, 3, 4 | `CLAUDE.md` header, "Commands", "Environments" |
| 2 | whether `privacy-check` is recommended; guard strictness |
| 4 (production identifiers) | `.claude/guard.json` rules |
| 5 | scale; shared vs personal files |
| 7 | the language lines of `CLAUDE.md` |
| 8 | `scripts/check.sh` steps; the test matrix line in `CLAUDE.md` |
| 9 | `CLAUDE.md` "Non-negotiables" |
| 10 | `CLAUDE.local.md` (personal) or `CLAUDE.md` (if the team agrees) |
