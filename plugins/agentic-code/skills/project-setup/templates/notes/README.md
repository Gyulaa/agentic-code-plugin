# {{PROJECT_NAME}} notes

The team's shared memory: where we are, what we decided and why, which bugs we know, who waits for whom.
People and agents write it together. Rules: [CLAUDE.md](CLAUDE.md). Settings: [config.json](config.json).

## What's new
- {{DATE}}: notes set up. Read [CLAUDE.md](CLAUDE.md) and [STATE.md](STATE.md).

## Getting started (once per machine)
1. Clone this repo next to the code repos listed in `config.json`.
2. `git config core.hooksPath .githooks` (the hook stops secrets, personal data and malformed notes).
3. `python3 scripts/notes.py whoami --set <your id from config.json>`.
4. Read `CLAUDE.md` and `STATE.md`, then start Claude Code and run `/agentic-code:resume-work`.
5. Catch up since your first day: `python3 scripts/notes_team.py inbox --since YYYY-MM-DD`.

## A day
Start: `/agentic-code:resume-work` (it runs the digest and shows what waits for you). Work. End: `/agentic-code:save-work`.
Every few weeks: `/agentic-code:tidy-notes`.
