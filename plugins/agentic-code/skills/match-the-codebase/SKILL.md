---
name: match-the-codebase
description: Use whenever you write or change code in an existing project. Code the way this codebase already does - reuse before adding, no new dependency without asking, the file's own idiom, what we never ship, doing exactly what was asked and reporting precisely what was run. The yardstick is a diff a reviewer cannot tell was written by a machine.
---

# Code the way this codebase does

The yardstick: a diff about which the reviewer cannot say a machine wrote it. This complements the `quality-gate` procedure.

## Reuse first, in this order
1. An existing helper or component (search: code graph or index if present, grep).
2. A package already in the manifest (`package.json`, `pubspec.yaml`, `pyproject.toml`, `requirements.txt`, `go.mod`, `Cargo.toml` …): icons, state, tables, charts, toasts, loading states, file formats.
3. **A new dependency only after asking**, with a reason: what it replaces, its size and maintenance, its licence. A package that talks to an outside service can make that service a data processor (`privacy-check`).

## The shape of the solution is the existing one too
Use the patterns the code already uses for permission gates, error responses, data access and the client/server split. A second, "better" pattern next to a working one is not an improvement but a fork; if the existing one is truly wrong, say so and propose changing it everywhere, as its own task.

## The file's idiom
- Names, structure, error handling, how state is passed. Before creating a new file, read its neighbour.
- Colours, spacing and radii from the design system's tokens, never literals.
- Don't reformat, rename or "tidy" what you were not asked to touch.
- Comments in the language and density of the surrounding file.

## What we never ship
- A comment that repeats the code (a comment says *why*, where a reader would stop).
- Leftover code, unused imports, debug prints.
- An abstraction written for a single caller, or a "just in case" parameter.
- A silently swallowed exception (the exception: a deliberately guarded fan-out where each query fails on its own, with a comment saying so).
- An invented field name, endpoint, package or key. If you don't know it, find it or ask.
- A defensive rewrite of working code only because it looks unusual.
- In user-facing text: the em dash (—) and other tells of machine-written copy, unless the project says otherwise. Use a comma, colon, parentheses or two sentences.

## Do what was asked, completely
Not narrower, and not with three unrequested fixes on top. What you notice along the way, say; don't fix it silently. Report by name what you ran (the check script, lint, typecheck, tests) and, just as clearly, what you did not run or could not verify, and what you did not do.
