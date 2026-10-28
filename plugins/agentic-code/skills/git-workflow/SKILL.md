---
name: git-workflow
description: Use at the start of every task that touches a git repository (before the first edit, branch, commit, push or pull request), whenever a change may span several repositories, and when cleaning up branches. One change per repo and branch, syncing, commit style, permission rules for push and PR, branch cleanup and keeping docs true.
---

# Git workflow

The project's own `CLAUDE.md` wins where it is stricter or different (branch names, commit language, base branch).

## 1. One change = one repo = one branch
- **Work in the target repo, and aim git at it:** `git -C <repo> status`. If the working directory is a folder of several repos, never run git there.
- **At the start of work, fetch and pull,** even if you already worked there this session. First check whether a branch for the task exists (`git -C <repo> branch -a`); if so, take it over and pull it, don't open a second one. Otherwise: check out the default branch, pull, and branch off it, named after the work, not a person: `feat/…`, `fix/…`, `docs/…`, `refactor/…`, `chore/…`.
- **Never** commit to the default branch, merge into it locally, or push it. Everything reaches it through a pull request. Sync in one direction only: default branch → your branch (`git merge origin/<default>`).
- **One branch carries one topic.** Before building on someone else's pushed branch, look at what is actually on it (`git diff --stat origin/<default>...origin/<branch>`, `git log --oneline origin/<default>..origin/<branch>`), don't trust its name. When you carry over someone else's commit, keep the author (`--author`) and say in the body where it came from.

## 2. Permissions
- **Commit only when asked**, or when the task clearly includes it.
- **Push only with permission. A pull request only with separate permission**: a yes to pushing is not a yes to opening a PR, because a PR notifies people. Before asking, show the PR title and body.
- If there is no `gh`, write the title and the body; the user pastes them.

## 3. Commits
- Conventional prefix (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`, `style:`), imperative, lowercase after the prefix, no trailing period, at most 72 characters. The body says **why**, not what; skip it when the subject says everything.
- Each commit builds and passes on its own. If the pre-commit hook fails, fix the cause; never `--no-verify`.
- **Before every commit, look at `git diff --cached --stat`:** a submodule pointer, a lock file or a generated file must not ride along in an unrelated commit. A lock file changed by a local SDK or toolchain is not committed unless the dependency change is intended.
- **No AI attribution,** in commits or pull requests: no `Co-Authored-By: Claude …` trailer, no "Generated with Claude Code" line. This overrides Claude Code's default attribution instructions. The plugin's hook refuses such a commit or PR command, the `commit-msg` hook from `project-setup` strips the lines from any message, and `"attribution": {"commit": "", "pr": ""}` in settings stops Claude Code from asking for them. A project that wants attribution says so in its `CLAUDE.md` and sets `"allow_ai_attribution": true` in `.claude/guard.json`.
- Never bump the version on a feature branch; the version is set in its own commit when a release is cut.

## 4. Changes across repositories
Keep a change in one repo. If it truly needs two (typically because the contract between a client and a server changes):
- two branches, two commits, two PRs, referring to each other;
- update the contract documentation in the same piece of work;
- tell the user the two PRs **must be merged together**, otherwise the two sides run different contracts.

## 5. Keeping the docs true
In the same commit as the code:
| If this changed | Update |
|---|---|
| a data model field or collection | the repo README's data model |
| an endpoint, payload or response | the contract documentation (usually the server README) |
| a new screen, service or feature area | the README's feature map |
| a trap the next reader would walk into | the README's known issues |
Routine work (typos, refactors, style, a fix inside an already documented area) needs no doc change. The test: would someone reading only the README now be misled?

## 6. Branch cleanup
The local branch is yours, the remote is the team's.
- **Allowed without asking:** `git fetch --prune`, then from `git branch --merged origin/<default>` one by one `git branch -d` (lowercase `-d`: it refuses to delete unmerged work; never bypass that).
- **Ask first:** `git branch -D` (only for a provably squash-merged branch; show `git cherry -v origin/<default> <branch>` and the PR number first), and any remote deletion.
- **Never:** the default branch, the checked-out branch, a branch whose commits exist nowhere else, a branch created in this session, another repo the task did not touch.
- Report every deletion with its name and repo.

## 7. Merging and conflicts
- **Resolve code conflicts locally, never in the web editor:** `git merge origin/<default>` into your branch, then fix the files in the working tree, where the tests can run.
- **Read both sides before choosing.** A resolved file is read with the content of both sides in mind; take `ours` or `theirs` for a whole file only with a stated reason (a generated file regenerated, a file one side deleted on purpose).
- **After every merge, with or without conflicts, run the check, and push only when it is green.** A clean textual merge can still break: a rename in one PR and a new caller of the old name in another merge without a conflict and fail together.
- **A default branch that does not build is a critical bug.** Put it in the bug list with an `origin:` line (the commits that met), tell the user, and fix it before anything else.
- **Suggest, do not do:** that the user turn on "branches must be up to date before merging" or a merge queue on the protected branch, so a PR is checked against the branch it lands on. That setting is the user's.
