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

## Round 3: the notes system (only for scale L, or when the user asks for shared notes)
Ask in one round, defaults in brackets. Several of these decide between tier L1 and L2 (see SKILL.md).
13. **Who writes the notes?** How many people, and do several agents run in parallel? [one repo, a few people: L1; several people or several repos: L2]
14. **Where do they live,** and with what tool? In the code repo under `notes/` [L1], or in a separate notes repo that everyone clones [L2]. Do they use Obsidian? [the notes are Obsidian-compatible either way; it is not required]
15. **People and areas:** an id and the git name of every person; the areas of the product (default: the area names of the risk map, if there is one) and who owns each.
16. **Repos** the team works across: name, folder next to the workspace folder, default branch. [L2 only]
17. **Messages between people and agents** (a thread file per topic)? [yes for L2, no for L1]
18. **Gate strength:** `block` stops a commit with malformed notes, `warn` only warns [block]. Secrets and personal data are always stopped.
19. **Pushing notes without asking each time** (`auto_push`)? Only for a separate notes repo, and only for the green and yellow zones (content, never the scripts or the config). Say plainly that a yes is a standing permission. [no]
20. **Privacy:** which e-mail domains are the team's own (so they are not flagged), and what stays local-only (people, meetings, incidents) [`local/`].
21. **Optional:** a session log per session [off], categories for decisions [none].

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
| 13-14 | the notes tier (L1 or L2) and the location; `config.json`; the hook (`pre-commit`, or `pre-commit-notes` in a notes-only repo) |
| 15-16 | `config.json` `people`, `areas`, `repos` |
| 17 | whether `messages/` and the `merge=union` line exist |
| 18-21 | `config.json` `gate`, `auto_push`, `privacy`, `sessions`, `categories`, `zones` |
