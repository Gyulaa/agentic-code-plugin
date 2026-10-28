# Test level: the details

`SKILL.md` has the two tables. This file says what each piece of work means, what counts as proof, and how the optional scripts enforce it.

## Classifying by hand
Ask in this order and stop at the first yes for each file.
1. Docs, images, generated and lock files: **skip**, they ask for nothing.
2. Does it touch money, time or dates, permissions, an access rule, a data write path, a server contract, a migration, a dependency or a legal promise? **critical**. A file that is harmless in general can be critical only when its changed lines touch such a thing (for example one function in a large module).
3. Is it a test? Then it is not risk, it is the answer to it.
4. Does it write stored data, belong to a shared component, or sit in a place nobody has classified? **sensitive**.
5. Ordinary source: **normal**.
The change's depth is the highest of its files; its width comes from the size and the number of areas (the first two folders of a path are a good default area).

## The work, one by one
| Work | Meaning | Proof |
|---|---|---|
| `new-test` | a test that exercises the changed behaviour | a test file in the diff |
| `edge-cases` | unit tests of the edges: 0, negative, midnight, rounding, empty input, very large input | the cases are in the tests; say which |
| `revert-proof` | put the changed code back as it was; the new test must fail there. A test that is green on the old code does not protect the change | what you ran and that it failed |
| `adversarial-review` | a fresh, read-only subagent sees the diff and the acceptance criteria, not your reasoning, and looks for correctness gaps | its findings and what you did with them |
| `contract-test` | a rule or contract test for the changed rule, where the project has such a layer (access rules against an emulator, an API schema test) | the test, or why the project has no such layer |
| `server-twin` | the same logic lives on the other side of a contract (client and server): change both, or say which PR carries the other half | the other change or its PR |
| `security-check` | run the `security-check` skill on the diff | its report |
| `full-write` | every write lists the whole field set; a missing field is not written as empty or removed | the write sites you checked |
| `ui-matrix` | for new UI: loading, empty, error, success and forbidden states, a small screen, large text, both themes | the project's marker in the diff, or what you looked at |
| `live-try` | use it once for real, in the simulator, browser or a device | what you did and what came out |
| `pay-debt` | close an open test-debt item of this area | a debt file changed to closed |

## The scripts (optional, installed by `project-setup` on request)
- `scripts/risk_level.py level` prints the level, the reasons and the work; `--staged` looks at the index, `--json` is for tools. It classifies from `scripts/risk-map.json`: `skip`, `critical` (a path, and optionally a regular expression that a changed line must match), `test`, `sensitive` (a path or a content pattern), `normal`; a file that matches nothing is `unknown` and is treated as sensitive, with a warning, so a gap in the map never lets a change slip down to "small". Without a map the script counts only the width and never stops anything.
- `scripts/risk_level.py gate` runs in the pre-commit hook after the check. For every piece of work there are three ways out and no fourth: **the diff proves it** (a test file; the UI marker; a new debt item for the same work; a debt item closed), **you attest it** with `risk_level.py done <work> "<what you did, what came out>"` (valid for the next commit only, it expires when HEAD moves), or **write it down as test debt**, below critical depth and only for missing tests. Otherwise the commit stops and the output names the exact command. Merge commits and commits with only skip-class files pass.
- Never `--no-verify`. `RISK_GATE=warn` turns the stop into a warning, and only when the user asks for it explicitly.
- The gate warns when a test file is deleted or the number of test lines drops: a failing test is a requirement, not an obstacle. It does not stop, because there are legitimate cases, but it shows.
- `scripts/test_debt.py add <work> --given … --when … --then …` writes `docs/test-debt/TD-<date>-<hex>.json`, committed with the change. The machine fills in the target, the diff, where the test goes (an existing test that imports the target, else a mirror path), a nearby test as a pattern and the command that runs one test. You write only the claim. It is thrown back if a field is under 12 characters, names no concrete value, or says only "works" or "is correct". `close <id>` needs the proof described above, including the revert proof, which restores the target file from a backup inside the git directory and puts it back even after a crash. A live try is closed with `close <id> --attested "…"`.
- An area with five open items, or an item older than 14 days, makes its next change large, with a repayment. `risk_level.py map-coverage` lists tracked files the map does not know; `project-setup` runs it after writing the map and takes it to zero.

## Honest expectations
The main gain is quality and fewer pointless rounds: a one-line text fix no longer gets the treatment of a payment change, and a payment change gets more than it did. The token saving is moderate and has to be measured, not assumed: see the "Measure a change" section of `improve-workflow`. The thresholds (50 and 300 lines, two areas, five items, 14 days) are first estimates; adjust them in the map after a few weeks of real commits.
