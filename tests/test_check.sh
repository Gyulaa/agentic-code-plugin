#!/usr/bin/env bash
# Tests for the check.sh template. Run: bash tests/test_check.sh
# Uses fake format/lint/test commands in a throwaway git repo.
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$HERE/plugins/agentic-code/skills/project-setup/templates/scripts/check.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
pass=0; failn=0

expect() { # name, expected exit code, expected text, actual exit code, output
  if [ "$2" = "$4" ] && printf '%s' "$5" | grep -q -- "$3"; then pass=$((pass+1)); else
    failn=$((failn+1)); echo "FAIL: $1 (exit $4, wanted $2; wanted text: $3)"; printf '%s\n' "$5" | sed 's/^/    /'; fi
}

cd "$TMP" && git init -q && git config user.email t@example.com && git config user.name t
mkdir scripts && cp "$TEMPLATE" scripts/check.sh && chmod +x scripts/check.sh

# Unconfigured template must refuse to run.
out=$(scripts/check.sh 2>&1); rc=$?
expect "unconfigured" 1 "not configured" $rc "$out"

export EXTS="txt"
# "Formatted" means: no line with trailing spaces. The fixer strips them.
export FORMAT_CHECK='! grep -l " $"'
export FORMAT_FIX='sed -i.bak "s/ *$//" "$@" && rm -f -- *.bak'
export LINT='true'
export TEST='test ! -f failing'
export TEST_ARGS_NOT_MACOS=""

echo "ok" > a.txt
out=$(scripts/check.sh 2>&1); rc=$?
expect "clean, no commits yet" 0 "OK" $rc "$out"

git add -A && git commit -q -m init --no-verify
out=$(scripts/check.sh 2>&1); rc=$?
expect "nothing changed" 0 "no changed files" $rc "$out"

printf 'bad \n' > b.txt && git add b.txt
out=$(scripts/check.sh --staged 2>&1); rc=$?
expect "staged unformatted" 1 "unformatted" $rc "$out"

out=$(scripts/check.sh 2>&1); rc=$?
expect "fix formats" 0 "OK" $rc "$out"
if grep -q ' $' b.txt; then failn=$((failn+1)); echo "FAIL: fixer did not strip trailing space"; else pass=$((pass+1)); fi

touch failing
out=$(scripts/check.sh 2>&1); rc=$?
expect "failing tests" 1 "ERROR: tests" $rc "$out"
rm failing

out=$(LINT='echo boom; false' scripts/check.sh 2>&1); rc=$?
expect "failing lint shows output" 1 "boom" $rc "$out"

out=$(scripts/check.sh no-such-branch 2>&1); rc=$?
expect "missing base" 1 "base does not exist" $rc "$out"

# A command that already uses "$@" gets the files only once.
out=$(FORMAT_CHECK='test -z "$(grep -l " $" "$@")"' scripts/check.sh --staged 2>&1); rc=$?
expect "command with \$@" 0 "Format check" $rc "$out"

out=$(TEST='' scripts/check.sh 2>&1); rc=$?
expect "no tests configured" 0 "none configured" $rc "$out"

# The commit-msg hook strips AI attribution lines and the blank lines they leave.
HOOK="$HERE/plugins/agentic-code/skills/project-setup/templates/githooks/commit-msg"
printf 'fix: thing\n\nWhy it changed.\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n' > msg
sh "$HOOK" msg; out=$(cat msg); rc=$?
expect "commit-msg strips the trailer" 0 "Why it changed" $rc "$out"
if grep -q -i 'anthropic' msg || [ -z "$(tail -n 1 msg)" ]; then failn=$((failn+1)); echo "FAIL: commit-msg left the trailer or a trailing blank line"; cat msg; else pass=$((pass+1)); fi
printf 'docs: x\n' > msg; sh "$HOOK" msg
if [ "$(cat msg)" = "docs: x" ]; then pass=$((pass+1)); else failn=$((failn+1)); echo "FAIL: commit-msg changed a clean message"; fi

echo "check.sh tests: $pass passed, $failn failed"
[ $failn -eq 0 ]
