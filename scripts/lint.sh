#!/usr/bin/env bash
# Static checks for the plugin: shell and Python syntax, JSON files, the plugin manifests.
# Usage: scripts/lint.sh (scripts/check.sh runs it). Exit code: 0 if everything passed.
# Works with the bash 3.2 that ships with macOS and with Linux bash.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
fail=0

while IFS= read -r f; do
  bash -n "$f" || fail=1
done < <(git ls-files '*.sh')

while IFS= read -r f; do
  sh -n "$f" || fail=1
done < <(git ls-files '.githooks/*' 'plugins/agentic-code/skills/project-setup/templates/githooks/*')

git ls-files '*.py' | python3 -c '
import ast, sys
bad = 0
for name in sys.stdin.read().split():
    try:
        ast.parse(open(name, encoding="utf-8").read(), name)
    except SyntaxError as e:
        print(f"{name}:{e.lineno}: {e.msg}"); bad = 1
sys.exit(bad)' || fail=1

git ls-files '*.json' | python3 -c '
import json, sys
bad = 0
for name in sys.stdin.read().split():
    try:
        json.load(open(name, encoding="utf-8"))
    except ValueError as e:
        print(f"{name}: {e}"); bad = 1
sys.exit(bad)' || fail=1

if command -v claude >/dev/null 2>&1; then
  claude plugin validate . >/dev/null || { claude plugin validate .; fail=1; }
  claude plugin validate plugins/agentic-code >/dev/null || { claude plugin validate plugins/agentic-code; fail=1; }
else
  echo "lint: claude CLI not found, plugin validate skipped"
fi

exit $fail
