# Állapot

Frissítve: 2026-10-28. Egy oldal maradjon: a `/agentic-code:save-work` írja át, a `/agentic-code:resume-work` olvassa először.

## Mi ez
Az `agentic-code` Claude Code plugin forrása (skillek, guard hook, `project-setup` sablonok).

## Most
- A `main` a 0.5.0 (a #4, #5, #6 beolvadt; ellenőrizve: a `plugin.json` 0.5.0, a szkriptek és a `security-check` a `main`-en). A beolvadt ágak törölve, helyben és a remote-on.
- `fix/pr-base-rule` (0.5.1: a PR alapja a default ág; beolvasztás után ellenőrizni, hová került; platform-viselkedésről nem állítunk ellenőrizetlenül; a `resume-work` a beolvadt PR alapját is nézi): helyben, a `main`-nel szinkronban, check `OK`, **nincs pusholva** (push és PR külön engedélyre).
- Nincs nyitott PR. A kutatás helyben: `research/`. A 0.5.0 spec-eltérései a `docs/decisions.md` 2026-10-28-i bejegyzésének végén.

## Blokkol / várunk rá
- Gyula engedélye a `fix/pr-base-rule` pushához és PR-jéhez.
- A 0.5.0 spec „friss, csak olvasó al-ügynökkel átnézés” lépése nincs lefuttatva; a `claude --plugin-dir ./plugins/agentic-code` alatti kézi kipróbálás sem (a `claude plugin validate` zöld).

## Következő lépés
1. `fix/pr-base-rule` push és PR; beolvasztás után `/plugin marketplace update agentic-code-plugin`.
2. **Új nagy téma (új ablakban, 0 kontextussal, spec-pel kezdve):** a jegyzet-, döntés- és üzenetrendszer, valamint a csapatkoordináció komoly szintre emelése a `project-setup`-ban és a `save-work`/`resume-work`-ben. A mostani rendszer (STATE.md, decisions.md, bugs.md, az L méret `notes-L.md`) egyszerűbb, mint egy érett, vault-alapú csapatrendszer. Ebbe még nem kezdtünk bele.
3. A 0.5.0 kipróbálása egy valódi projekten (`project-setup existing`, térkép, kapu, adósság); a küszöbök (50 és 300 sor, 2 terület, 5 tétel, 14 nap) mérése az `improve-workflow` „Measure a change” szerint.
4. A TDAD és az ImpossibleBench elsődleges forrásait el kell olvasni, mielőtt a README idézi őket.

## Súrlódás
- A `scripts/check.sh` kb. 17 s (a `risk_level` és `test_debt` tesztek kb. 14 s, valódi git-repókkal), minden commitnál lefut. Ha zavaró lesz: a lassú tesztek külön címkére.
- Egymásra épülő PR: a #5 a fix ágba olvadt, a `main`-ből kimaradt a 0.5.0 (egy extra PR a javítás). Oka: ellenőrizetlen állítás a PR-szövegben (a GitHub átállítja az alapot), a repóban `delete_branch_on_merge` = false. A szabály a `fix/pr-base-rule` ágon vár.
