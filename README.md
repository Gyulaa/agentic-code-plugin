# agentic-code

A Claude Code plugin for working on any codebase the disciplined way: accurate answers from few tokens, a quality gate before every change, strict git and permission rules, design and search skills for websites and apps, and a setup skill that builds this working environment for a new project or restructures an existing one.

It is meant for any project, personal or team.

## What's new
- **0.5.0 (2026-10-28):** risk-based testing. `quality-gate` scales the work by how big (small, medium, large) and how dangerous (normal, sensitive, critical) a change is, and nothing is loosened: a text fix gets the check, a payment change gets edge cases, a revert proof, an adversarial review and a security check, with no postponing. Optional scripts from `project-setup` classify the diff against a risk map, stop a commit whose work is missing (`risk_level.py`), and keep a test you cannot write yet as test debt that closes only with proof (`test_debt.py`). New `security-check` skill (never trust the client). `design-review` tries the worst-case data (long names, empty, huge, 200% text). `save-work` records only decisions that guide future work, archives closed items and keeps "What's new" short; `improve-workflow` can measure a change by replaying a task on two sandbox clones. Re-run `project-setup existing` to add the gate to a project.
- **0.4.1 (2026-10-28):** the `check.sh` template runs your formatter, lint and tests without git's hook variables (`GIT_DIR`, `GIT_INDEX_FILE`), so a test that runs git in another repo no longer breaks on a partial commit (`git commit -o`). `git-workflow` gains a section on merging: resolve conflicts locally, read both sides, run the check after every merge before pushing.
- **0.4.0 (2026-10-25):** three new skills. `design` builds websites and apps (web, iOS, Android, Flutter) that don't look machine-made: it keeps a `DESIGN.md` in the Google Stitch format, plans from the subject before coding, writes copy that persuades honestly, and checks the result in screenshots. `design-review` ranks accessibility, craft, platform and copy problems and fixes only what you pick. `seo` covers classic and AI search: server-rendered HTML, crawler access per search and training bot, content answer engines can quote, metadata, structured data. Two on-request checkers: `slop_check.py` and `seo_check.py`. `project-setup` now asks about UI and public pages and offers a `DESIGN.md`. The plugin is now MIT-licensed.
- **0.3.1 (2026-10-25):** `match-the-codebase` treats every commit as if the repository were public: no secrets, credentials, personal data, local paths or hostnames, private details of other projects, or third-party text the licence does not allow.
- **0.3.0 (2026-10-25):** no AI attribution anywhere: the hook refuses a commit or PR command carrying the Claude co-author trailer or "Generated with Claude Code", and `project-setup` adds a `commit-msg` hook and the `attribution` setting. New `improve-workflow` skill (evidence, research from reliable sources, measured changes); `working-mode` looks things up after two failed attempts. `project-setup` writes a human README with a "What's new" section that `save-work` keeps current, and offers a code graph (graphify) for large codebases.
- **0.2.0 (2026-10-25):** `spec` skill; never weaken a test to get green; minimal human-reviewed `CLAUDE.md`; permission allowlist; the guard checks each part of a chained command. `resume`/`save` renamed to `resume-work`/`save-work`.
- **0.1.0 (2026-10-24):** first version.

Update with `/plugin marketplace update agentic-code-plugin`.

## What it is built on
- Anthropic, [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices): give Claude a check it can run; explore, plan, then code; keep `CLAUDE.md` short; hooks for must-always rules; fresh-context review; `/clear` between tasks.
- Anthropic, [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents): context as a finite budget, structured notes outside the window (`STATE.md`), just-in-time retrieval, subagents returning condensed summaries.
- Kent Beck, [Augmented coding: beyond the vibes](https://kentbeck.com/summaries/augmented-coding-beyond-the-vibes/): TDD as the guardrail; agents must not delete or weaken tests to get green.
- GitHub, [Spec Kit](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/): specify, plan, tasks, implement.
- ETH Zurich and LogicStar, *Evaluating AGENTS.md* (arXiv 2602.11988): auto-generated context files hurt more than they help; keep them minimal and human-curated.
- METR, [the 2025 randomized study](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) (developers 19% slower while feeling faster): measure, don't assume.
- Simon Willison's "lethal trifecta": private data + untrusted content + a way out is how agents leak data.
- Design: Anthropic, [Improving frontend design through Skills](https://claude.com/resources/articles/improving-frontend-design-through-skills) (without direction a model converges on the most probable look); Google Stitch's [DESIGN.md format](https://github.com/google-labs-code/design.md); WCAG 2.2; the [Vercel Web Interface Guidelines](https://vercel.com/design/guidelines); [Impeccable](https://github.com/pbakaus/impeccable)'s idea of surface modes; Emil Kowalski's motion numbers; Nielsen Norman Group on writing for the web and tone of voice.
- Testing and security: the idea of a revert proof and of weighing tests by risk comes from practice and from the work on AI-written code that games its tests; the security checklist is inspired by the nine categories of [raroque/vibe-security-skill](https://github.com/raroque/vibe-security-skill) (MIT) and by the [OWASP Top 10](https://owasp.org/Top10/) (2025: broken access control first, server-side request forgery now part of it); the worst-case-data step by Emil Kowalski's `break-ui` skill (MIT). The wording is our own.
- Search: Google Search Central, [AI features and your website](https://developers.google.com/search/docs/appearance/ai-features) (no special optimisation for AI Overviews and AI Mode); Vercel, [The rise of the AI crawler](https://vercel.com/blog/the-rise-of-the-ai-crawler) (AI crawlers do not run JavaScript); Aggarwal et al., [GEO](https://arxiv.org/abs/2311.09735) (KDD 2024), read with its limits.

## What is inside

| Skill | Invoked | What it does |
|---|---|---|
| `working-mode` | automatically | Context order (state file → `CLAUDE.md` → targeted search), token hygiene, subagent briefing, safety rules |
| `quality-gate` | automatically, before code changes | Acceptance criteria, test first, one-command check, diff self-review, definition of done, stop rule; the test level scales with how big and how dangerous the change is, and a missing test is written down as test debt |
| `git-workflow` | automatically, before branch/commit/PR | One change per repo and branch, commit style, permission for push and PR, cross-repo changes, branch cleanup |
| `match-the-codebase` | automatically, when writing code | Reuse before adding, no new dependency without asking, the file's idiom, what we never ship |
| `spec` | automatically for non-trivial changes, or `/agentic-code:spec <feature>` | Explore read-only, interview you about the hard parts, write a self-contained spec with tasks and an end-to-end check, implement it in a fresh session, review against it |
| `privacy-check` | automatically, in products with users | Four questions after every change; keeps published privacy documents true to the code |
| `security-check` | on security-relevant changes, or when you ask "is this safe?" | A technology-independent checklist built on never trusting the client: access rules, roles, endpoints, payments, secrets, limits; reports only real flaws, ranked, with what an attacker can do |
| `design` | automatically for UI work, or `/agentic-code:design <what>` | Websites, apps and dashboards that don't look machine-made: a `DESIGN.md` in the Google Stitch format, the surface's mode, a plan before code, copy that persuades honestly, a screenshot check; web, iOS, Android and Flutter |
| `design-review` | after a large UI change, or `/agentic-code:design-review [what]` | Accessibility, craft, platform fit, generic patterns and copy, and a worst-case-data pass (long names, empty, huge, 200% text); ranked by severity with evidence; fixes only what you pick |
| `seo` | automatically for public websites, or `/agentic-code:seo [page or URL]` | Classic and AI search (AI Overviews, ChatGPT, Perplexity, Claude, Copilot): server-rendered HTML, crawler access, content answer engines can quote, metadata, structured data, honest measurement |
| `project-setup` | `/agentic-code:project-setup [new\|existing]` | Interviews you and scaffolds a new project, or audits an existing one and proposes and applies a restructure |
| `resume-work` | `/agentic-code:resume-work [topic]` | Picks up work from the one-page `STATE.md`, checks it against git and open PRs |
| `save-work` | `/agentic-code:save-work [summary]` | Writes the session's outcome into `STATE.md`, the decision and bug logs (decisions only when they guide future work), archives closed items, and keeps the README's "What's new" short |
| `improve-workflow` | `/agentic-code:improve-workflow [topic]` | A short retro: where time and tokens went, what reliable sources recommend, a few measured changes for you to pick, and a way to measure a change by replaying the same task on two sandbox clones |

The `design` and `seo` skills each bring a checker you or Claude run on request, using only python3: `slop_check.py` finds code-level tells of generic design (animating everything, gradient text, disabled zoom, fonts from a CDN, inflated copy), and `seo_check.py` checks built pages or URLs for metadata, canonicals, headings, JSON-LD, images, text visible without JavaScript, `robots.txt` per search and AI crawler, and the sitemap.

**Risk-based testing (optional).** `quality-gate` decides how much testing a change needs from two axes: width (small, medium, large) and depth (normal, sensitive, critical). A one-line text fix gets the check; a payment change gets edge cases, a revert proof (the new test must fail on the old code), an adversarial review and the `security-check`, and none of it can be postponed. It works as a plain rule. On request, `project-setup` also installs three scripts, using only python3: `risk_level.py` classifies the staged diff against a risk map in `scripts/risk-map.json` (written from your risky areas) and its gate stops a commit whose work is missing, naming the exact command; `test_debt.py` writes a test you cannot write now below critical depth down as one file in `docs/test-debt/`, and closes it only when the test exists, passes, and fails once the code is put back to its state before the change. Be realistic about the benefit: the main gain is quality and fewer pointless rounds; the token saving is moderate and has to be measured (see `improve-workflow`, "Measure a change"). The thresholds are first estimates to adjust on a real project.

Plus a **project guard** hook: if a project has `.claude/guard.json`, every shell command Claude runs there is checked against its rules (deny, or ask you first), segment by segment, so an allowed part of a chained command cannot excuse a forbidden one. Projects without the file get no project rules. A `~/.claude/guard.json` guards every project under your home folder. In every project, the hook also refuses a `git commit` or `gh pr create/edit` whose message carries AI attribution (the Claude co-author trailer or "Generated with Claude Code"); a project that wants it sets `"allow_ai_attribution": true` in its guard file. It is a guard rail against mistakes, not a security boundary: a determined command can always be phrased around a regex.

## Install (once per machine)

In Claude Code:

```
/plugin marketplace add Gyulaa/agentic-code-plugin
/plugin install agentic-code@agentic-code-plugin
```

The repository is private: the first command uses your git credentials for GitHub (`gh auth login` or an SSH key). If it cannot reach the repo, add it from a local clone instead: `/plugin marketplace add /path/to/agentic-code-plugin`.

To stop Claude Code from asking for attribution at all, add this once to `~/.claude/settings.json`:

```json
"attribution": { "commit": "", "pr": "" }
```

Update later with `/plugin marketplace update agentic-code-plugin`. Nothing has to be copied into your projects: the skills are available in every project once the plugin is installed. Turn it off for one project with `"enabledPlugins": {"agentic-code@agentic-code-plugin": false}` in that project's `.claude/settings.json`.

While developing the plugin itself, try a change without installing: `claude --plugin-dir ./plugins/agentic-code`.

## Use

- **New project:** create an empty folder, open Claude Code in it, run `/agentic-code:project-setup new`. Answer the questions; review the file plan; approve.
- **Existing project:** open Claude Code in the repo, run `/agentic-code:project-setup existing`. You get an audit table and a numbered list of proposals; pick what to apply. Changes land on a `chore/claude-setup` branch.
- **Every day:** `/agentic-code:resume-work` at the start, `scripts/check.sh` before a commit (the pre-commit hook runs it anyway), `/agentic-code:save-work` at the end.

## The project layout it creates

| Scale | Files |
|---|---|
| S (personal, one repo) | `CLAUDE.md`, `CLAUDE.local.md` (git-ignored), `STATE.md`, `docs/decisions.md`, `docs/bugs.md`, `scripts/check.sh`, `.githooks/pre-commit` and `commit-msg`, `.claude/settings.json` (allowlist for safe commands, no attribution) |
| M (a product, one or two people) | S + `docs/agent-brief.md`, a README with "What's new", `.claude/guard.json` if there is production, a code graph if the codebase is large, and on request the risk gate (`scripts/risk_level.py`, `scripts/test_debt.py`, `scripts/risk-map.json`) |
| L (a team, several repos) | a notes folder or repo with one file per decision, bug, task and session, plus a parent-folder `CLAUDE.md` mapping the repos |

## Development

The repo uses its own setup: `CLAUDE.md`, `STATE.md` and `docs/decisions.md` at the root are for working on the plugin and are not shipped (only `plugins/agentic-code/` is).

```bash
git config core.hooksPath .githooks     # once per clone: the pre-commit hook runs scripts/check.sh
scripts/check.sh                        # everything below in one command; "OK" means green
python3 -m unittest discover -s tests   # the guard hook
bash tests/test_check.sh                # the check.sh template, the pre-commit hook and the commit-msg hook
                                        # (python3 -m unittest also covers risk_level.py and test_debt.py)
claude plugin validate . && claude plugin validate plugins/agentic-code
```

Everything works with the bash 3.2 and python3 that ship with macOS, and on Linux.

## Licence

MIT, see [LICENSE](LICENSE).
