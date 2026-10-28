# Állapot

Frissítve: 2026-10-28. Egy oldal maradjon: a `/agentic-code:save-work` írja át, a `/agentic-code:resume-work` olvassa először.

## Mi ez
Az `agentic-code` Claude Code plugin forrása (skillek, guard hook, `project-setup` sablonok).

## Most
- A 0.5.0 spec (`docs/specs/2026-10-28-testing-security-and-workflow-0.5.md`) mind a 15 feladata kész, a #4 és a #5 PR beolvadt (2026-10-28), `scripts/check.sh` → `OK`.
- **Hiba a folyamatban:** a #5 (alap: `fix/hook-env-and-merge-rules`) a #4 beolvadása után a fix ágba olvadt, nem a `main`-be. A `main` csak a 0.4.1-et tartalmazza (`0f2db50`); az egész 0.5.0 az `origin/fix/hook-env-and-merge-rules` ágon van (16 commit a `main` előtt). Semmi nem veszett el.
- A spec-eltérések a `docs/decisions.md` 2026-10-28-i bejegyzésének végén. A kutatás helyben: `research/`.

## Nyitott ágak és PR-ek
- PR #6 `fix/hook-env-and-merge-rules` → `main`: hozza a 0.5.0-t, nyitva. A beolvadt ágak (`feat/*`, `chore/claude-setup`) törölve, helyben és a remote-on.
- `fix/pr-base-rule` (0.5.1: PR-alap szabály a `git-workflow`-ban és a `resume-work`-ben): helyben, **nincs pusholva** szándékosan; a #6 beolvadása után indul a `main`-ről frissítve, hogy ne legyen egymásra épülő PR.

## Blokkol / várunk rá
- Gyula beolvasztja a #6-ot (beolvasztás külön engedély); utána a `fix/pr-base-rule` push és PR külön engedélyre.
- A spec „friss, csak olvasó al-ügynökkel átnézés” lépése nincs lefuttatva (al-ügynököt nem indítottam).
- A `claude --plugin-dir ./plugins/agentic-code` alatti kézi kipróbálás még hátra van; a `claude plugin validate` zöld.

## Következő lépés
1. #6 beolvasztása; ellenőrzés: `main`-en a `plugin.json` verziója 0.5.0 (`git merge-base --is-ancestor`); a `fix/hook-env-and-merge-rules` ág törlése; utána `fix/pr-base-rule` a `main`-ről frissítve, push, PR; `/plugin marketplace update agentic-code-plugin`.
2. Kipróbálás egy valódi projekten (`project-setup existing`, térkép, kapu, adósság); a küszöbök (50 és 300 sor, 2 terület, 5 tétel, 14 nap) mérése az `improve-workflow` „Measure a change” szerint.
3. A TDAD és az ImpossibleBench elsődleges forrásait el kell olvasni, mielőtt a README idézi őket.

## Súrlódás
- A `scripts/check.sh` kb. 17 s (a `risk_level` és `test_debt` tesztek kb. 14 s, valódi git-repókkal), minden commitnál lefut. Ha zavaró lesz: a lassú tesztek külön címkére.
- Egymásra épülő PR: a #5 a fix ágba olvadt, a `main`-ből kimaradt a 0.5.0 (1 eset, egy extra PR és egy kiadás a javítás). Oka: a PR-szövegben ellenőrizetlen állítás (a GitHub átállítja az alapot), a repóban `delete_branch_on_merge` = false.
