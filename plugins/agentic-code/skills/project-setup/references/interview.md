# Interview for a new project

Ask in at most two rounds. Offer sensible defaults so the user can answer with one word. Skip anything already answered.

## Round 1: what and for whom
1. **What is it,** in one sentence? (Becomes the first line of `CLAUDE.md`.)
2. **Who uses it?** Only you / a few known people / the public. (Decides whether `privacy-check` applies and how strict the guard must be.)
3. **Stack:** language and framework, or "you suggest". If the user asks you to suggest, propose one with a one-line reason and the alternative.
4. **Where does it run?** Local only / a server or hosting you name / an app store. Is there a **production** system (database, deploy target, payment account) the agent must never change? Its identifiers go into the guard.
5. **Alone or with others?** Decides the scale (S/M/L) and whether the repo is shared (shared → team files by PR, personal preferences in `CLAUDE.local.md`).
6. **Is there a user interface, and public pages that should be found in search?** None / an app or internal tool / a public website too. (Decides `design`, `design-review`, a `DESIGN.md`, and `seo`.)

## Round 2: how you want to work (defaults in brackets)
7. **Git hosting** and the default branch name [GitHub, `main`]. Should the repo be created now? (Creating a remote repo is outward-facing: only on an explicit yes.)
8. **Languages:** notes and `CLAUDE.md` [the conversation's language]; commit messages and code comments [English]; user-facing text [ask].
9. **Tests:** what level is expected [unit tests for logic, a widget or component test for UI, no end-to-end at first]. Any device or browser matrix (smallest screen, dark mode, large text)?
10. **Hard rules** the agent must never break (for example "never change the database schema without asking", "never touch the payments code"). These become the non-negotiables in `CLAUDE.md`.
11. **Style preferences** you already know (formatting, naming, comment density, no em dash in UI text). Unknown is fine: they can be added to `CLAUDE.local.md` later, whenever you correct the agent.
12. **Risky areas:** what handles money, time or dates, permissions, access rules, writes to stored data, or a server contract (an API the client and server must agree on)? Name the folders or modules. Then offer the risk gate: a pre-commit step that sizes each change from its diff and stops a commit whose tests or checks are missing, in proportion to how big and how dangerous the change is. Recommended for a product or a team (scale M and L); for a personal project (S) only mention it if the user asks. Needs python3.

## Turning answers into files
| Answer | Goes to |
|---|---|
| 1, 3, 4 | `CLAUDE.md` header, "Commands", "Environments" |
| 2 | whether `privacy-check` is recommended; guard strictness |
| 4 (production identifiers) | `.claude/guard.json` rules |
| 5 | scale; shared vs personal files |
| 6 | `{{DESIGN_LINE}}` in `CLAUDE.md` (for example ", `design` for new screens, `design-review` after a large UI change, `seo` on public pages"; empty without a UI); whether to offer a `DESIGN.md` |
| 8 | the language lines of `CLAUDE.md` |
| 9 | `scripts/check.sh` steps; the test matrix line in `CLAUDE.md` |
| 10 | `CLAUDE.md` "Non-negotiables" |
| 11 | `CLAUDE.local.md` (personal) or `CLAUDE.md` (if the team agrees) |
| 12 | `scripts/risk-map.json` (`critical`, `sensitive`, `server_twin`), and whether the risk gate is installed at all; `{{RISK_COMMAND}}` in `CLAUDE.md` |
