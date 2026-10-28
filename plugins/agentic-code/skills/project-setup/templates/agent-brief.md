# Subagent brief

Paste the block below at the top of every subagent prompt, before the task, with the paths filled in. A subagent briefed like this does not have to map the project from scratch (an unbriefed review can cost ten times the tokens).

```text
PROJECT BRIEF (read before touching anything)

Where things are
- State (one page, start here): {{ROOT}}/STATE.md
- Rules: {{ROOT}}/CLAUDE.md — read "Non-negotiables" and "Environments" before any change.
- Known bugs: {{ROOT}}/docs/bugs.md. Don't report a known bug as new; refer to its ID.
  (With shared notes: `python3 {{ROOT}}/scripts/notes.py find type=bug status=open,in-progress,pr-open`, and `notes.py find --text WORD` before reporting anything as new. Read-only: do not create or edit notes unless the task says so.)
- Check: {{ROOT}}/scripts/check.sh (format + lint + tests; "OK" = green).

How to search
- Search by code names (class, function, field), then read only the lines around the hit.
- For "every occurrence" questions use two methods and compare the counts.

Forbidden (no exceptions)
- Writing to production ({{PROD_ENV}}); any call to a live endpoint.
- Commit, push, PR, merge, rebase, reset — unless the task explicitly asks.
- Printing or saving secrets.
- Tests with network or side effects.

Output: in {{LANGUAGE}}; every finding with file:line evidence; a separate list of what you could not verify.
```
