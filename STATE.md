# Állapot

Frissítve: 2026-10-28. Egy oldal maradjon: a `/agentic-code:save-work` írja át, a `/agentic-code:resume-work` olvassa először.

## Mi ez
Az `agentic-code` Claude Code plugin forrása (skillek, guard hook, `project-setup` sablonok).

## Most
- A spec (`docs/specs/2026-10-28-testing-security-and-workflow-0.5.md`) mind a 15 feladata kész, pusholva, két PR-ben. `scripts/check.sh` → `OK`.
- 0.4.1 a `fix/hook-env-and-merge-rules` ágon (hook-környezet javítása, ütközésfeloldás szabálya). 0.5.0 a `feat/risk-based-testing` ágon, erre épül: tesztszint (`risk_level.py`, kapu), tesztadósság (`test_debt.py`), `security-check`, `save-work`, `design-review` legrosszabb eset, `improve-workflow` mérés.
- A spec-eltérések a `docs/decisions.md` 2026-10-28-i bejegyzésének végén.
- A kutatás helyben, a gitben nincs: `research/`.

## Nyitott ágak és PR-ek
- PR #4 `fix/hook-env-and-merge-rules` → `main` (0.4.1), nyitva.
- PR #5 `feat/risk-based-testing` → `fix/hook-env-and-merge-rules` (0.5.0, egymásra épülő PR), nyitva. A #4 beolvadása után a #5-öt a `main`-re kell állítani (a GitHub megteszi, ha a fix ág törlődik), `git merge origin/main`, check.

## Blokkol / várunk rá
- Gyula átnézi és beolvasztja a PR-eket (#4, utána #5); a beolvasztáshoz külön engedély kell.
- A spec „friss, csak olvasó al-ügynökkel átnézés” lépése nincs lefuttatva (al-ügynököt nem indítottam).
- A `claude --plugin-dir ./plugins/agentic-code` alatti kézi kipróbálás (a skillek megjelenése) még hátra van; a `claude plugin validate` zöld.

## Következő lépés
1. PR #4, majd #5 átnézése és beolvasztása; utána `/plugin marketplace update agentic-code-plugin`.
2. Kipróbálás egy valódi projekten (`project-setup existing`, térkép, kapu, adósság); a küszöbök (50 és 300 sor, 2 terület, 5 tétel, 14 nap) mérése az `improve-workflow` „Measure a change” szerint.
3. A TDAD és az ImpossibleBench elsődleges forrásait el kell olvasni, mielőtt a README idézi őket.

## Súrlódás
- A `scripts/check.sh` kb. 17 s (a `risk_level` és `test_debt` tesztek kb. 14 s, valódi git-repókkal), minden commitnál lefut. Ha zavaró lesz: a lassú tesztek külön címkére.
