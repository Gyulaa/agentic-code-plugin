# How these notes work

One file per decision, bug, task and message. Everything else is generated or in `config.json`, the single source of the
rules below (people, areas, statuses, zones). `scripts/notes.py check` is the gate: it stops a commit that breaks them.

## Before you ask or write
Search first: `python3 scripts/notes.py find type=decision status=open,proposed`, `find --text WORD`, `area NAME`,
`code PATH`, `show ID`. If a note already says it, quote it instead of asking, and update it instead of adding a second.

## Writing a note
1. `python3 scripts/notes.py new decision|bug|task|message "Title" --area A` (IDs, dates and the header come from the script).
2. Fill in `summary:` (one sentence saying what the note **states**, at most 160 characters) and write the body.
3. Link it: at least {{MIN_LINKS}} `[[wikilink]]` to the narrowest related note (never to an index). Write identifiers as links
   (`[[B12]]`, not "B12"). A relation goes at the end: `solves:: [[B12]]`; relations: solves, causes, supersedes, depends,
   part-of, affects. Backlinks are computed, never written.
4. `python3 scripts/notes.py index` then `python3 scripts/notes.py check` (0 errors).
5. Save: {{SAVE_COMMAND}}

## Fields and status cycles
`title`, `type`, `status`, `created`, `updated`, `summary` always; `area` from `config.json`; `code:` lists real paths.
- decision: `open -> proposed -> accepted | rejected`, `accepted -> superseded` (the newer decision says `supersedes:: [[old]]`).
  While open or proposed it has `waiting-on:` (whose decision it is); once accepted or rejected it has `decided-by:`
  (a person, `team` or `agent`). Accepting adds a line under the title: `Accepted (date): evidence`.
- bug: `open -> in-progress -> pr-open -> fixed | wontfix | invalid`, with `severity:`; `pr:` once there is one.
- task: `open -> in-progress -> done | dropped`, `owner:`.
- message: `open | closed`, `to:`, `waiting-on:`.
A status change updates `updated:`. A missing test is not a bug: it is test debt (`docs/test-debt/`, where the project has it).

## What is a decision
Only what guides future work: a rule, a direction, or a reason without which the question would come back. A one-off step
(merging a branch, deleting a function, rewording a text) belongs in the task, the message or the PR.

## Messages
`messages/DATE-slug.md`, append only, one line per message: `DATE · from -> to: text` (at most 3 sentences; details go in a
linked note). Whoever opened the thread closes it when they got what they asked for. An agent writes in a thread only when
the person asked, or when the work needs another person's answer and it told its person so; otherwise it proposes the line.

## Never
- Secrets, tokens, passwords or personal data in a note: the gate refuses them. Personal notes live in `local/` (never committed).
- `git add -A` in the notes: name the files.
- Resolving a conflict by guessing: stop and tell the people involved.
- Editing a generated `_index.md` or someone else's section of `STATE.md` by hand.
