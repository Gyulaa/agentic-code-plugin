# Állapot

Frissítve: 2026-10-28. Egy oldal maradjon: a `/agentic-code:save-work` írja át, a `/agentic-code:resume-work` olvassa először.

## Mi ez
Az `agentic-code` Claude Code plugin forrása (skillek, guard hook, `project-setup` sablonok).

## Most
- A 0.5.0 spec (`docs/specs/2026-10-28-testing-security-and-workflow-0.5.md`) mind a 15 feladata kész, a #4 és a #5 PR beolvadt (2026-10-28), `scripts/check.sh` → `OK`.
- **Hiba a folyamatban:** a #5 (alap: `fix/hook-env-and-merge-rules`) a #4 beolvadása után a fix ágba olvadt, nem a `main`-be. A `main` csak a 0.4.1-et tartalmazza (`0f2db50`); az egész 0.5.0 az `origin/fix/hook-env-and-merge-rules` ágon van (16 commit a `main` előtt). Semmi nem veszett el.
- A spec-eltérések a `docs/decisions.md` 2026-10-28-i bejegyzésének végén. A kutatás helyben: `research/`.

## Nyitott ágak és PR-ek
- Nincs nyitott PR. Javítandó: PR `fix/hook-env-and-merge-rules` → `main` (hozza a 0.5.0-t).
- Beolvadt ágak, törölhetők (kérdezve): `fix/hook-env-and-merge-rules` (a PR után), `feat/risk-based-testing`, `feat/design-skills`.

## Blokkol / várunk rá
- Gyula engedélye a javító PR-hez (fix ág → `main`), majd a beolvasztáshoz.
- A spec „friss, csak olvasó al-ügynökkel átnézés” lépése nincs lefuttatva (al-ügynököt nem indítottam).
- A `claude --plugin-dir ./plugins/agentic-code` alatti kézi kipróbálás még hátra van; a `claude plugin validate` zöld.

## Következő lépés
1. Javító PR (fix ág → `main`), beolvasztás, utána `/plugin marketplace update agentic-code-plugin`.
2. Egymásra épülő PR szabálya a `git-workflow`-ba: a felső PR-t beolvasztás előtt `main`-re kell állítani (`gh pr edit --base main`), mert az alsó ág törlése nélkül a GitHub nem állítja át.
3. Kipróbálás egy valódi projekten (`project-setup existing`, térkép, kapu, adósság); a küszöbök (50 és 300 sor, 2 terület, 5 tétel, 14 nap) mérése az `improve-workflow` „Measure a change” szerint.
4. A TDAD és az ImpossibleBench elsődleges forrásait el kell olvasni, mielőtt a README idézi őket.

## Súrlódás
- A `scripts/check.sh` kb. 17 s (a `risk_level` és `test_debt` tesztek kb. 14 s, valódi git-repókkal), minden commitnál lefut. Ha zavaró lesz: a lassú tesztek külön címkére.
- Egymásra épülő PR: a 2. PR a fix ágba olvadt, a `main`-ből kimaradt a 0.5.0 (1 eset, egy extra PR a javítás).
