# agentic-code

A Claude Code plugin for working on any codebase the disciplined way: accurate answers from few tokens, a quality gate before every change, strict git and permission rules, and a setup skill that builds this working environment for a new project or restructures an existing one.

It grew out of the workflow used on the Onix project and is generalised here for any project, personal or team.

## What it is built on
- Anthropic, [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices): give Claude a check it can run; explore, plan, then code; keep `CLAUDE.md` short; hooks for must-always rules; fresh-context review; `/clear` between tasks.
- Anthropic, [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents): context as a finite budget, structured notes outside the window (`STATE.md`), just-in-time retrieval, subagents returning condensed summaries.
- Kent Beck, [Augmented coding: beyond the vibes](https://kentbeck.com/summaries/augmented-coding-beyond-the-vibes/): TDD as the guardrail; agents must not delete or weaken tests to get green.
- GitHub, [Spec Kit](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/): specify, plan, tasks, implement.
- ETH Zurich and LogicStar, *Evaluating AGENTS.md* (arXiv 2602.11988): auto-generated context files hurt more than they help; keep them minimal and human-curated.
- METR, [the 2025 randomized study](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) (developers 19% slower while feeling faster): measure, don't assume.
- Simon Willison's "lethal trifecta": private data + untrusted content + a way out is how agents leak data.

## What is inside

| Skill | Invoked | What it does |
|---|---|---|
| `working-mode` | automatically | Context order (state file → `CLAUDE.md` → targeted search), token hygiene, subagent briefing, safety rules |
| `quality-gate` | automatically, before code changes | Acceptance criteria, test first, one-command check, diff self-review, definition of done, stop rule |
| `git-workflow` | automatically, before branch/commit/PR | One change per repo and branch, commit style, permission for push and PR, cross-repo changes, branch cleanup |
| `match-the-codebase` | automatically, when writing code | Reuse before adding, no new dependency without asking, the file's idiom, what we never ship |
| `spec` | automatically for non-trivial changes, or `/agentic-code:spec <feature>` | Explore read-only, interview you about the hard parts, write a self-contained spec with tasks and an end-to-end check, implement it in a fresh session, review against it |
| `privacy-check` | automatically, in products with users | Four questions after every change; keeps published privacy documents true to the code |
| `project-setup` | `/agentic-code:project-setup [new\|existing]` | Interviews you and scaffolds a new project, or audits an existing one and proposes and applies a restructure |
| `resume-work` | `/agentic-code:resume-work [topic]` | Picks up work from the one-page `STATE.md`, checks it against git and open PRs |
| `save-work` | `/agentic-code:save-work [summary]` | Writes the session's outcome into `STATE.md`, the decision and bug logs |

Plus a **project guard** hook: if a project has `.claude/guard.json`, every shell command Claude runs there is checked against its rules (deny, or ask you first), segment by segment, so an allowed part of a chained command cannot excuse a forbidden one. Projects without the file are not affected. A `~/.claude/guard.json` guards every project under your home folder. It is a guard rail against mistakes, not a security boundary: a determined command can always be phrased around a regex.

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
- **Every day:** `/agentic-code:resume-work` at the start, `scripts/check.sh` before a commit (the pre-commit hook runs it anyway), `/agentic-code:save-work` at the end.

## The project layout it creates

| Scale | Files |
|---|---|
| S (personal, one repo) | `CLAUDE.md`, `CLAUDE.local.md` (git-ignored), `STATE.md`, `docs/decisions.md`, `docs/bugs.md`, `scripts/check.sh`, `.githooks/pre-commit`, `.claude/settings.json` (allowlist for safe commands) |
| M (a product, one or two people) | S + `docs/agent-brief.md`, `.claude/guard.json` if there is production |
| L (a team, several repos) | a notes folder or repo with one file per decision, bug, task and session, plus a parent-folder `CLAUDE.md` mapping the repos |

## Development

```bash
python3 -m unittest discover -s tests   # the guard hook
bash tests/test_check.sh                # the check.sh template
claude plugin validate . && claude plugin validate plugins/agentic-code
```

Everything works with the bash 3.2 and python3 that ship with macOS, and on Linux.
