# Állapot

Frissítve: 2026-10-28. Egy oldal maradjon: a `/agentic-code:save-work` írja át, a `/agentic-code:resume-work` olvassa először.

## Mi ez
Az `agentic-code` Claude Code plugin forrása (skillek, guard hook, `project-setup` sablonok).

## Most
- **0.6.0 megvalósítva, helyben, nincs pusholva:** ág `feat/team-notes` (az `origin/main`-ről indult a #7 előtt), 4 commit a spec után; `scripts/check.sh` → `OK` (181 egységteszt + 29 `test_check.sh`). Spec: `docs/specs/2026-10-28-team-notes-0.6.md`; a döntés és a 8 eltérés a `docs/decisions.md` legfelső bejegyzésében.
- **#7 PR nyitva** (`fix/pr-base-rule` → `main`, 0.5.1, egyesíthető, Gyula beolvasztására vár). Nincs más nyitott PR.
- Új fájlok: `plugins/agentic-code/skills/project-setup/templates/scripts/notes.py` és `notes_team.py`, `templates/notes/` (config, CLAUDE, STATE, README, gitignore/gitattributes/local-names), `templates/githooks/pre-commit-notes`, a `pre-commit` bővítve; `skills/tidy-notes/`; módosítva: `project-setup` (SKILL, `references/interview.md`, `audit.md`, `agent-brief.md`), `save-work`, `resume-work`, `git-workflow`, `working-mode`, README, `plugin.json` 0.6.0; tesztek: `tests/test_notes.py`, `test_notes_team.py`, `test_notes_e2e.py`, `test_check.sh` bővítve. A `templates/notes-L.md` törölve.
- A kutatás helyben: `research/notes-system-comparison.md` (egy külső, érett csapatrendszer elemzése; a repóba nem kerülhet).

## Blokkol / várunk rá
- Gyula: a #7 beolvasztása; utána a `feat/team-notes` kapja meg a `main`-t (`git merge origin/main`; ütközik a README „What's new” szakasza, a `plugin.json` verziója, a `STATE.md`: a 0.6.0 és ez a szöveg marad, a 0.5.1 sora a 0.6.0 alá kerül), `scripts/check.sh`, és csak ezután kérhető a push és a PR (alap: `main`, külön engedéllyel).
- Nincs lefuttatva: (1) a spec „friss, csak olvasó al-ügynökkel átnézés” lépése (nem indítottam al-ügynököt); (2) a kézi próba: `claude --plugin-dir ./plugins/agentic-code` egy mintaprojekten, `project-setup new` L2-ként, `resume-work`, `save-work`, második klón, `tidy-notes`. A `claude plugin validate` zöld.

## Következő lépés
1. Gyula beolvasztja a #7-et → `git fetch`, `git merge origin/main` a `feat/team-notes`-ba, ütközés feloldása (lásd fent), `scripts/check.sh`.
2. Az al-ügynökös átnézés a spec ellen (csak olvasó, friss; csak a helyességet vagy a követelményeket érintő hiányok), a kézi próba, a találatok javítása.
3. Push és PR a `main`-re Gyula engedélyével; beolvasztás után ellenőrizni, hová került; `/plugin marketplace update agentic-code-plugin`.
4. A 0.6.0 kipróbálása egy valódi többfős projekten; `notes.py health --save` kiindulás, négy hét múlva összevetés és a tokenmérés (`improve-workflow` „Measure a change”). Az üzenet-modul egyszerűsítendő vagy elhagyandó, ha 6 hét után a szálak nem záródnak.
5. Régebbi nyitott tételek: a 0.5.0 küszöbeinek mérése (50 és 300 sor, 2 terület, 5 tétel, 14 nap); a TDAD és az ImpossibleBench elsődleges forrásait el kell olvasni, mielőtt a README idézi őket.

## Súrlódás
- A `scripts/check.sh` kb. 35 s (a notes-tesztek ~13 s-ot adtak a korábbi ~17 s-hoz, valódi git-repókkal), minden commitnál lefut. Ha zavaró lesz: a lassú tesztek külön címkére.
- A hook alatt a `git commit` exportálja a `GIT_AUTHOR_NAME`-et és társait: az ideiglenes git-repós tesztek ettől hibáztak (a commit szerzője felülíródott); a notes-tesztek importkor törlik a `GIT_*` változókat. Új ilyen teszt ugyanígy tegye.
- Egymásra épülő PR: a #5 a fix ágba olvadt, a `main`-ből kimaradt a 0.5.0 (egy extra PR, a #6 a javítás). A szabály a #7-ben vár.
