---
name: tidy-notes
description: Use when the project keeps shared notes (a notes/config.json with scripts/notes.py), every few weeks, when the start-of-work digest says OWNERLESS or TIDY, or when the user asks to clean up decisions, bugs, tasks or messages. Goes through old, stalled, ownerless, superseded and wrongly-stated items, checks each against the code and the pull requests, proposes changes with evidence in one table, and writes only after the user agrees.
argument-hint: "[area or note id]"
---

# Tidy the notes

Old notes mislead. This skill closes what is finished, finds an owner for what is orphaned, and asks the right person about what is really open. It never closes or changes a decision on a guess.

## 1. List (read-only)
1. Update: `python3 scripts/notes_team.py inbox` pulls the notes repo when safe (tier L1: nothing to pull).
2. `python3 scripts/notes_team.py tidy` prints seven baskets: (1) closed but not archived, (2) superseded but not marked, (3) ownerless, (4) not moved for `stale_days`, (5) header or link errors, (6) bugs whose PR is merged, (7) conflict copies. For tier L1, which has no `notes_team.py`, use `notes.py find status=open,proposed` and `notes.py health`.
3. If `$ARGUMENTS` names an area or a note, limit the work to it.

## 2. Check each item against reality (evidence, not feelings)
For every stalled or ownerless decision, bug or task, look at the code and the history before you propose anything: the default branch (`git fetch`, `git ls-tree`, `git log --grep`), merged pull requests (`gh pr list --state merged --search ...`, `gh pr view`), the state file and the related notes (`notes.py show ID`, `related ID`). Then it is one of four things:
- **done in fact:** propose the closing status, with the proof (commit, PR, file);
- **no longer relevant** because the work went another way: propose `rejected` (decision) or `dropped` (task) or `invalid` (bug), with one sentence of reason;
- **ownerless:** propose a person for `waiting-on:` from the area owners in `config.json` (`areas.<name>.owner`), the person confirms;
- **really open:** if the person in `waiting-on` is the user, put it to them as a question (decide, reject, or stay open, with a reason); if it is someone else, propose a short message to them (`notes.py new message ... --to ID`), one or two sentences.
Superseded items (basket 2): the older note becomes `superseded` (accepted) or `rejected` (open or proposed), with one line under its title saying what replaced it. A decision that states a rule still in force is never archived, however old. A one-off decision that has been carried out (a branch merged, a repo deleted) is proposed for archiving, with the proof, and stays `accepted`.
Bugs in basket 6: propose `fixed`, with the merged PR as the proof. Conflict copies (basket 7): compare with the original (`cmp`), propose deleting identical ones, show the difference otherwise.

## 3. Show one table, then wait
| Note | Now | Proposal | Evidence |
|---|---|---|---|
Do not write anything before the user answers. Their answers win. Never change the status or the owner of a decision without it, and never delete a note: closing means a status plus `notes.py archive`.

## 4. Write
After the yes, per approved row: edit the header (`status`, `waiting-on`/`decided-by`, `updated`) and add the one-line "Accepted (date): evidence" or "Superseded by [[id]]" line where it applies; `notes.py archive <ids>` for what moved to a closed status (at most 20 per pass; more needs the user to split it); `notes.py index`; `notes.py check` (0 errors); then save: `notes_team.py save "tidy: <what>" <files>` (tier L2) or the project's own way (tier L1). Send the agreed messages the same way.

## 5. Report
In a few lines: how many items were closed, archived, given an owner, put to someone; how many are still open and for whom; and the new numbers from `notes.py health --save` next to the previous ones (`.notes/health.jsonl`). If the same kinds of items keep piling up (always ownerless in one area, always stalled waiting on one person), say so in one sentence: that is a process question for `/agentic-code:improve-workflow`, not something to tidy.
