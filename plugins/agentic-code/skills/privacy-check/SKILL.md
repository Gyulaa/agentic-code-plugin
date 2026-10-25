---
name: privacy-check
description: Use whenever a change in a product may alter what personal data is collected, how long it is kept, who can access it, or which third party processes it (new fields, logging, analytics, cookies, e-mails, exports, new vendors or regions, retention, account deletion), at the end of every implementation in such a product as a check, and whenever published privacy or legal documents are read or edited. Keeps the published documents and the code true to each other and warns on any mismatch.
---

# Privacy check

Applies to projects that handle other people's personal data and publish a privacy policy, terms or a data processing agreement. For a purely personal hobby project without users, say so once and skip it.

## The four questions (at the end of every implementation)
Did this change alter:
1. **what personal data we collect** (a new field, a log line with a name or e-mail, an analytics event, a cookie, a device identifier)?
2. **how long we keep it** (a new store, a cache, a backup, a log, deletion that no longer reaches something)?
3. **who can access it** (a new role, a share, an export, an admin screen, a support tool)?
4. **which third party processes it** (a new SDK, API, hosting region, e-mail or analytics provider, AI service, or a font, embed or script loaded from someone else's server, which sends them the visitor's IP address)?

If all four are no, say "privacy: no change" in one line and move on.

## When one is yes
- **Warn prominently, right away**, not in a footnote: what changed, in which file, and which published statement it affects.
- Find the documents' single source of truth (the project `CLAUDE.md` names it; typically a `legal/` folder). **Never create a second copy** of a legal text inside a code repo.
- The update belongs to the same piece of work, as a separate commit or PR in the repo that holds the documents: the text first, then the published version (for example HTML), and the version and effective date bumped everywhere they appear.
- Say what the publication requires: how the pages go live, and whether users must be notified in advance (terms changes usually need advance notice; check the documents' own rules).

## When an update is NOT needed
UI changes, refactors, bug fixes and performance work that don't touch the four questions. Every update can cost a user notification, so don't create one without reason.

## Load-bearing promises
Published documents usually promise things the code must keep true: an opt-out in settings, an in-app link to the documents, a hosting region, retention periods, that an account can be deleted. Before removing or changing such a feature, find the statement that depends on it. If the project keeps a table of these promises, keep it current.

## Mismatch found while doing something else
Report it immediately, with the file and the statement, even if the task was unrelated. Don't fix legal text on your own initiative; propose the change.
