---
name: spec
description: Plan before coding when a change is not trivial - explore read-only, interview the user about the hard parts, write a self-contained spec with tasks and an end-to-end check, then implement it in a fresh session task by task. Use for new features, multi-file changes, unfamiliar code or unclear approaches, or when the user invokes /spec. Skip it when the whole diff can be described in one sentence.
argument-hint: "<feature or change to plan>"
---

# Spec first: explore, plan, then code

Jumping straight to code solves the wrong problem surprisingly often. For anything bigger than a one-sentence diff, separate understanding and planning from implementation. If you could describe the diff in one sentence (a typo, a log line, a rename), skip this and just do it.

## 1. Explore (read-only)
- Read what the change touches, following `working-mode` (state file, `CLAUDE.md`, targeted search, then only the relevant lines). For a wide investigation, use a read-only subagent so the main context stays clean.
- Find the existing patterns the change should follow (`match-the-codebase`), the tests that cover the area, and any decision or bug note about it.
- Write nothing yet.

## 2. Interview the user about the hard parts
Ask, in one or two rounds (use the question tool if available), only what the code cannot answer: behaviour in edge cases, states (empty, error, offline, no permission), UX choices, data that must not be lost, what is explicitly out of scope, tradeoffs you see. Don't ask the obvious; dig into what the user may not have considered.

## 3. Write the spec
To `docs/specs/<YYYY-MM-DD>-<slug>.md` (or where the project `CLAUDE.md` says), self-contained so a fresh session can execute it without this conversation:
- **Goal:** one paragraph, and who it is for.
- **Behaviour:** the acceptance criteria as a checklist, including the edge cases and states.
- **Out of scope:** what this change deliberately does not do.
- **Design:** the files and interfaces involved, the data model changes, the pattern it follows (with a file reference), anything crossing repos (`git-workflow` §4).
- **Tasks:** small, ordered, each one reviewable and committable on its own, each with its test.
- **Verification:** the end-to-end check that proves the feature works (a command, a test, a scripted scenario, a screenshot comparison), and the privacy check result if it applies.
Show the spec to the user. Their edits win.

## 4. Implement in a fresh session
- Recommend `/clear` (or a new session) and then: "implement `<spec path>` task by task". A clean context focused on the spec beats a long one full of exploration.
- Per task: test first, implement, run the check, tick the task in the spec, commit (`quality-gate`, `git-workflow`).
- If reality contradicts the spec, stop and update the spec with the user before continuing; don't drift silently.

## 5. Review against the spec
Before calling it done, have a fresh read-only subagent compare the diff with the spec: every criterion implemented, edge cases tested, nothing outside the scope changed. Tell it to report only gaps that affect correctness or the stated requirements, not style preferences, so the review does not push the change into over-engineering.
