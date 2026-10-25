# agentic-code

A Claude Code plugin for working on any codebase the disciplined way: accurate answers from few tokens, a quality gate before every change, strict git and permission rules, and a setup skill that builds this working environment for a new project or restructures an existing one.

It grew out of the workflow used on the Onix project and is generalised here for any project, personal or team.

## What is inside

| Skill | Invoked | What it does |
|---|---|---|
| `working-mode` | automatically | Context order (state file → `CLAUDE.md` → targeted search), token hygiene, subagent briefing, safety rules |
| `quality-gate` | automatically, before code changes | Acceptance criteria, test first, one-command check, diff self-review, definition of done, stop rule |
| `git-workflow` | automatically, before branch/commit/PR | One change per repo and branch, commit style, permission for push and PR, cross-repo changes, branch cleanup |
| `match-the-codebase` | automatically, when writing code | Reuse before adding, no new dependency without asking, the file's idiom, what we never ship |
| `privacy-check` | automatically, in products with users | Four questions after every change; keeps published privacy documents true to the code |
| `project-setup` | `/agentic-code:project-setup [new\|existing]` | Interviews you and scaffolds a new project, or audits an existing one and proposes and applies a restructure |
| `resume` | `/agentic-code:resume [topic]` | Picks up work from the one-page `STATE.md`, checks it against git and open PRs |
| `save` | `/agentic-code:save [summary]` | Writes the session's outcome into `STATE.md`, the decision and bug logs |

Plus a **project guard** hook: if a project has `.claude/guard.json`, every shell command Claude runs there is checked against its rules (deny, or ask you first). Projects without the file are not affected. A `~/.claude/guard.json` guards every project under your home folder.

## Install (once per machine)

In Claude Code:

```
/plugin marketplace add Gyulaa/agentic-code-plugin
/plugin install agentic-code@agentic-code-plugin
```

The repository is private: the first command uses your git credentials for GitHub (`gh auth login` or an SSH key). If it cannot reach the repo, add it from a local clone instead: `/plugin marketplace add /path/to/agentic-code-plugin`.

Update later with `/plugin marketplace update agentic-code-plugin`. Nothing has to be copied into your projects: the skills are available in every project once the plugin is installed. Turn it off for one project with `"enabledPlugins": {"agentic-code@agentic-code-plugin": false}` in that project's `.claude/settings.json`.

While developing the plugin itself, try a change without installing: `claude --plugin-dir ./plugins/agentic-code`.

## Use

- **New project:** create an empty folder, open Claude Code in it, run `/agentic-code:project-setup new`. Answer the questions; review the file plan; approve.
- **Existing project:** open Claude Code in the repo, run `/agentic-code:project-setup existing`. You get an audit table and a numbered list of proposals; pick what to apply. Changes land on a `chore/claude-setup` branch.
- **Every day:** `/agentic-code:resume` at the start, `scripts/check.sh` before a commit (the pre-commit hook runs it anyway), `/agentic-code:save` at the end.

## The project layout it creates

| Scale | Files |
|---|---|
| S (personal, one repo) | `CLAUDE.md`, `CLAUDE.local.md` (git-ignored), `STATE.md`, `docs/decisions.md`, `docs/bugs.md`, `scripts/check.sh`, `.githooks/pre-commit` |
| M (a product, one or two people) | S + `docs/agent-brief.md`, `.claude/guard.json` if there is production |
| L (a team, several repos) | a notes folder or repo with one file per decision, bug, task and session, plus a parent-folder `CLAUDE.md` mapping the repos |

## Development

```bash
python3 -m unittest discover -s tests   # the guard hook
bash tests/test_check.sh                # the check.sh template
claude plugin validate . && claude plugin validate plugins/agentic-code
```

Everything works with the bash 3.2 and python3 that ship with macOS, and on Linux.
