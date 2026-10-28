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

# Under a real pre-commit hook the project tools must not inherit git's local variables
# (GIT_DIR, GIT_INDEX_FILE, ...): a test that runs git in another repo would hit this one.
# The file list is still collected in the hook environment: on "git commit -o" the temporary
# index named by GIT_INDEX_FILE says which files are part of the commit.
HOOKTEMPLATE="$HERE/plugins/agentic-code/skills/project-setup/templates/githooks/pre-commit"
HOOKREPO="$TMP/hookrepo"
mkdir "$HOOKREPO" && cd "$HOOKREPO" && git init -q && git config user.email t@example.com && git config user.name t
mkdir -p scripts .git/hooks && cp "$TEMPLATE" scripts/check.sh && chmod +x scripts/check.sh
cp "$HOOKTEMPLATE" .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
echo one > a.txt && echo one > b.txt && git add -A && git commit -q -m init
echo two >> a.txt && echo two >> b.txt && git add a.txt
rm -f "$TMP/seen"
out=$(EXTS=txt LINT='' FORMAT_FIX='' FORMAT_CHECK='printf "%s\n" "$@" > "'"$TMP"'/seen"' \
  TEST='for v in $(git rev-parse --local-env-vars); do if env | grep -q "^$v="; then echo "leaked $v"; exit 1; fi; done' \
  git commit -o b.txt -m partial 2>&1); rc=$?
expect "partial commit: tools see no git environment" 0 "OK" $rc "$out"
if [ "$(cat "$TMP/seen" 2>/dev/null)" = "b.txt" ]; then pass=$((pass+1)); else
  failn=$((failn+1)); echo "FAIL: partial commit: wanted the format check to see only b.txt, got: $(cat "$TMP/seen" 2>/dev/null)"; fi

# The risk gate runs after the check, only when the project has scripts/risk_level.py;
# SKIP_CHECK=1 skips both. A stub stands in for the gate here (its own tests are in test_risk_level.py).
cd "$HOOKREPO"
commit_change() { # message; changes a.txt and tries to commit it, output in $out, exit code in $rc
  echo "$1" >> a.txt && git add a.txt && out=$(git commit -q -m "$1" 2>&1); rc=$?
}
commit_change "no gate script"
expect "no risk_level.py: the hook only checks" 0 "OK" $rc "$out"
if printf '%s' "$out" | grep -q "gate ran"; then failn=$((failn+1)); echo "FAIL: the gate ran without scripts/risk_level.py"; else pass=$((pass+1)); fi
printf 'import os, sys\nprint("gate ran", sys.argv[1:])\nsys.exit(int(os.environ.get("STUB_EXIT", "0")))\n' > scripts/risk_level.py
git add scripts/risk_level.py && git commit -q --no-verify -m "stub gate"
STUB_EXIT=2 commit_change "gate stops"
expect "the gate can stop the commit" 1 "gate ran \['gate'\]" $rc "$out"
if [ "$(git log -1 --format=%s)" = "gate stops" ]; then failn=$((failn+1)); echo "FAIL: the commit went through a stopping gate"; else pass=$((pass+1)); fi
STUB_EXIT=0 commit_change "gate passes"
expect "a passing gate lets the commit through" 0 "gate ran" $rc "$out"
echo "skipped" >> a.txt && git add a.txt && out=$(STUB_EXIT=2 SKIP_CHECK=1 git commit -q -m skipped 2>&1); rc=$?
expect "SKIP_CHECK=1 skips the check and the gate" 0 "skipped" $rc "$out"
if printf '%s' "$out" | grep -q "gate ran"; then failn=$((failn+1)); echo "FAIL: SKIP_CHECK=1 did not skip the gate"; else pass=$((pass+1)); fi
# The notes gate runs first, only when the project has scripts/notes.py, and SKIP_CHECK=1 does not skip it.
printf 'import os, sys\nprint("notes ran", sys.argv[1:])\nsys.exit(int(os.environ.get("STUB_NOTES", "0")))\n' > scripts/notes.py
git add scripts/notes.py && git commit -q --no-verify -m "stub notes"
echo "n1" >> a.txt && git add a.txt && out=$(STUB_NOTES=1 SKIP_CHECK=1 git commit -q -m "notes stop" 2>&1); rc=$?
expect "the notes gate stops the commit even with SKIP_CHECK=1" 1 "notes ran \['check', '--staged'\]" $rc "$out"
if [ "$(git log -1 --format=%s)" = "notes stop" ]; then failn=$((failn+1)); echo "FAIL: the commit went through a stopping notes gate"; else pass=$((pass+1)); fi
out=$(STUB_NOTES=0 git commit -q -m "notes pass" 2>&1); rc=$?
expect "a passing notes gate lets the commit through" 0 "notes ran" $rc "$out"
# The notes-only hook (no check.sh) runs just the gate.
NOTESREPO="$TMP/notesrepo"
mkdir "$NOTESREPO" && cd "$NOTESREPO" && git init -q && git config user.email t@example.com && git config user.name t
mkdir -p scripts .githooks && cp "$HERE/plugins/agentic-code/skills/project-setup/templates/githooks/pre-commit-notes" .githooks/pre-commit
chmod +x .githooks/pre-commit && git config core.hooksPath .githooks
cp "$TMP/hookrepo/scripts/notes.py" scripts/notes.py
echo x > n.md && git add -A && out=$(STUB_NOTES=1 git commit -q -m x 2>&1); rc=$?
expect "notes-only hook: the gate can stop the commit" 1 "notes ran" $rc "$out"
out=$(STUB_NOTES=0 git commit -q -m x 2>&1); rc=$?
expect "notes-only hook: a passing gate lets the commit through" 0 "notes ran" $rc "$out"
cd "$TMP"

# The commit-msg hook strips AI attribution lines and the blank lines they leave.
HOOK="$HERE/plugins/agentic-code/skills/project-setup/templates/githooks/commit-msg"
printf 'fix: thing\n\nWhy it changed.\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n' > msg
sh "$HOOK" msg; out=$(cat msg); rc=$?
expect "commit-msg strips the trailer" 0 "Why it changed" $rc "$out"
if grep -q -i 'anthropic' msg || [ -z "$(tail -n 1 msg)" ]; then failn=$((failn+1)); echo "FAIL: commit-msg left the trailer or a trailing blank line"; cat msg; else pass=$((pass+1)); fi
printf 'feat: x\n\nStrips the trailer or "Generated with Claude Code".\n\nGenerated with [Claude Code](https://claude.com/claude-code)\n' > msg; sh "$HOOK" msg
if grep -q 'Strips the trailer' msg && ! grep -q 'claude.com' msg; then pass=$((pass+1)); else failn=$((failn+1)); echo "FAIL: commit-msg must keep a mention and drop the link line"; cat msg; fi
printf 'docs: x\n' > msg; sh "$HOOK" msg
if [ "$(cat msg)" = "docs: x" ]; then pass=$((pass+1)); else failn=$((failn+1)); echo "FAIL: commit-msg changed a clean message"; fi

echo "check.sh tests: $pass passed, $failn failed"
[ $failn -eq 0 ]
