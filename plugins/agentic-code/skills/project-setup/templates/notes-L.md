# Notes layout for scale L (a team, several repos)

Use when several people and their agents share knowledge across repos. Keep the notes in their own repo (or a folder of the main repo) so every clone sees the same state.

```
notes/                     (or a separate "<project>-notes" repo)
├── CLAUDE.md              how to read and write these notes (the rules below)
├── STATE.md               one page; a section per work thread, each owner writes their own
├── architecture/          how the system works now (one note per area)
├── decisions/             one file per decision: d-<slug>.md, + decisions-index.md
├── bugs/                  one file per bug: <ID>.md, + bugs-index.md
├── tasks/                 one file per larger task: t<NN>-<slug>.md, + tasks-index.md
└── sessions/              one log per session: YYYY-MM-DD-<topic>.md
```

Rules to put into `notes/CLAUDE.md`:
- **Header on every note:** `title`, `type` (bug / decision / task / log / permanent / index), `status`, `created`, `updated`; bugs also `severity`. The header is the single truth; the index repeats it.
- **Status values:** bug: open / pr-open / in-progress / fixed / wontfix; decision: open / proposed / accepted / rejected; task: open / in-progress / done / dropped.
- **Links:** every note links at least two others; refer to IDs as links, not plain text.
- **IDs:** the highest existing + 1, taken after a pull. On a branch, use a temporary name and assign the number when it merges, so parallel branches don't collide.
- **Git:** commit, then `pull --rebase`, then push; stop and ask on a conflict.
- **Never in the notes:** secrets, personal data, other clients' information.
- Optional, once it grows past ~100 notes: a small script that checks headers and links in a pre-commit hook, and a query helper (`filter type=bug status=open`).

The parent folder of the repos gets its own `CLAUDE.md` (not in git) with a table of the repos, their default branches, and where the notes are.
