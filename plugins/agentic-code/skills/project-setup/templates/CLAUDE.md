# {{PROJECT_NAME}}

{{ONE_SENTENCE_WHAT_IT_IS}} Used by: {{WHO_USES_IT}}.

Start here: `STATE.md` (where things stand, one page). Context lives in `README.md`; this file is only the always-on guardrails.

## Commands
```bash
{{RUN_COMMAND}}            # run it locally
scripts/check.sh           # format + lint + tests; "OK" means green (the pre-commit hook runs it with --staged)
git config core.hooksPath .githooks   # once per clone
```

## Environments
| Environment | Identifier | Claude may |
|---|---|---|
| Local / test | {{TEST_ENV}} | read and write |
| Production | {{PROD_ENV}} | **read only**; enforced by `.claude/guard.json` |

## Non-negotiables
- {{HARD_RULE_1}}
- Push, pull request, merge and deploy only with explicit permission, asked separately; never push to `{{DEFAULT_BRANCH}}`.
- Secrets never go into git, logs or notes. `.env*` stays ignored.

## Language
- Notes (`STATE.md`, `docs/`) and this file: {{NOTES_LANGUAGE}}.
- Code comments and commit messages: {{CODE_LANGUAGE}}. User-facing text: {{UI_LANGUAGE}}.

## Where things are
| Need | Read |
|---|---|
| Where we are, what is next | `STATE.md` |
| Why something is the way it is | `docs/decisions.md` |
| Known bugs | `docs/bugs.md` |
| Architecture, data model, features | `README.md` |

## Working mode
When compacting, keep the list of modified files, the check command and any open decision.
Use the agentic-code skills: `working-mode` always, `quality-gate` and `match-the-codebase` before a code change, `spec` before anything bigger than a one-sentence diff, `git-workflow` before a branch, commit or PR{{PRIVACY_LINE}}{{DESIGN_LINE}}. Start a session with `/agentic-code:resume-work`, end it with `/agentic-code:save-work`.
