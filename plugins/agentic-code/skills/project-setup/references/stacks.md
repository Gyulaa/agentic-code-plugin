# Check commands per stack

Values for the configuration block of `scripts/check.sh`. `FORMAT_CHECK` and `FORMAT_FIX` receive the changed files as arguments; `LINT` and `TEST` run on the whole project. Leave a value empty to skip that step. Prefer the project's existing scripts (`npm run lint`, `make test`) over raw tools: the check must match what CI runs.

| Stack | EXTS | FORMAT_CHECK | FORMAT_FIX | LINT | TEST |
|---|---|---|---|---|---|
| Flutter / Dart | `dart` | `dart format --output=none --set-exit-if-changed` | `dart format` | `flutter analyze --no-fatal-infos` | `flutter test` |
| Node / TypeScript (npm) | `ts tsx js jsx` | `npx prettier --check` | `npx prettier --write` | `npm run lint --silent && npm run typecheck --silent` | `npm test --silent` |
| Next.js | `ts tsx js jsx css` | `npx prettier --check` | `npx prettier --write` | `npm run lint --silent` | `npm test --silent` (or empty if there are no tests) |
| Python (uv) | `py` | `uv run ruff format --check` | `uv run ruff format` | `uv run ruff check .` | `uv run pytest -q` |
| Python (pip) | `py` | `ruff format --check` | `ruff format` | `ruff check .` | `python3 -m pytest -q` |
| Go | `go` | `test -z "$(gofmt -l "$@")"` | `gofmt -w` | `go vet ./...` | `go test ./...` |
| Rust | `rs` | `rustfmt --check` | `rustfmt` | `cargo clippy -q -- -D warnings` | `cargo test -q` |
| Static site / other | `html css js` | `npx prettier --check` | `npx prettier --write` | (empty) | (empty) |

Notes:
- **pnpm / yarn / bun:** replace `npm run` / `npx` accordingly.
- **Flutter golden (screenshot) tests** differ between macOS and Linux font rendering. If the goldens are made on macOS, set `TEST_ARGS_NOT_MACOS="--exclude-tags golden"` (after tagging the golden tests) so Linux machines skip them, and let macOS CI be their source of truth. Never raise the tolerance instead.
- **Lint warnings that already exist:** if the project has old warnings, make the check fail only on errors at first, and record the warning count in `STATE.md` as a debt to pay down.
- **Monorepo:** one check script at the root that `cd`s into each package, or one per package with the root script calling them.
