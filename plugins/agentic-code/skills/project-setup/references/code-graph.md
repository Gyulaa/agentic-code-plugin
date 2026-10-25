# Optional: a code graph (graphify)

A code graph answers structural questions ("who calls this?", "how does A reach B?", "what does this repo call in that one?") from an index instead of reading files. On one Flutter app with three companion repos it cut the tokens of cross-repo questions by about 99% and of verification tasks by about 98%, at the same accuracy. Those are one project's measurements; on a small codebase grep is just as good and costs nothing to set up.

## When to offer it
- **Offer it:** more than roughly 300 source files, or several repos whose connections matter (an app calling a backend), or the user asks.
- **Don't:** scale S projects, scripts, a single small service. Say that grep is enough there.

## Setup (ask first; it installs a tool)
1. Install the tool once per machine: `uv tool install graphifyy` (or `pipx install graphifyy`). It provides the `graphify` command.
2. Build the graph from code only, locally, with no API key and no tokens: `graphify update .` (writes `graphify-out/`). Add `graphify-out/` to `.gitignore`: the graph is per machine and is rebuilt from the code.
3. Keep it fresh. `graphify hook install` writes into `.git/hooks`, which git ignores when `core.hooksPath` points to `.githooks`, so add the rebuild to `.githooks/post-commit` instead (and `chmod +x` it):
   ```sh
   #!/bin/sh
   # Rebuilds the code graph in the background after each commit (code only, no tokens).
   command -v graphify >/dev/null 2>&1 && (graphify update . >/dev/null 2>&1 &)
   exit 0
   ```
4. Several repos: build each repo's graph, then `graphify merge-graphs a/graphify-out/graph.json b/graphify-out/graph.json --out <notes>/graph.json`, and point queries at it with `--graph`. Rebuild the merged graph from a script, not by hand.
5. Don't run `graphify claude install`: it appends a long section to `CLAUDE.md`. Add these lines to the project `CLAUDE.md` instead:
   ```
   Code graph: `graphify query "<code name>"`, `graphify explain "<Class or .method()>"`, `graphify path "<A>" "<B>"`.
   It is blind to calls through instances, dependency injection and string keys: grep those.
   For "every caller / every write" questions use the graph and grep, and compare the counts.
   ```

## Verify
Ask the graph one question you can check by hand (`graphify explain` on a function you know the callers of) and compare it with `grep -rn`. If they disagree for a static call, the graph is stale or the language is not well supported: say so rather than relying on it.
