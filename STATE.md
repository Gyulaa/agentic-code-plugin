# Állapot

Frissítve: 2026-10-28. Egy oldal maradjon: a `/agentic-code:save-work` írja át, a `/agentic-code:resume-work` olvassa először.

## Mi ez
Az `agentic-code` Claude Code plugin forrása (skillek, guard hook, `project-setup` sablonok).

## Most
- A 0.4.0 (`design`, `design-review`, `seo`, MIT-licenc) a `main`-en van, a PR #3 beolvadt.
- Spec kész, jóváhagyásra vár: `docs/specs/2026-10-28-testing-security-and-workflow-0.5.md`: 0.4.1 (a hook-környezet javítása, az ütközésfeloldás szabálya) és 0.5.0 (dinamikus tesztszint és tesztadósság szkriptekkel, `security-check`, `save-work` döntés-próba, legrosszabb eset adat a `design-review`-ban, mérés az `improve-workflow`-ban).
- A kutatás helyben, a gitben nincs: `research/` (`workflow-learnings-research.md` az új, a többi a design, szöveg és seo).

## Nyitott ágak és PR-ek
- Nincs.

## Blokkol / várunk rá
- Gyula átnézi a specet; push és PR csak külön engedélyre.

## Következő lépés
1. Spec átnézése; `/clear`, majd „implement `docs/specs/2026-10-28-testing-security-and-workflow-0.5.md` task by task”, a 0.4.1-gyel (1-3. feladat) kezdve.
2. Kiadás után `/plugin marketplace update agentic-code-plugin`; kipróbálás egy valódi projekten (landing oldal, mobilképernyő, a kapu és az adósság).

## Súrlódás
- (még nincs; soronként egy: mi volt lassú vagy hibázott ismételten, milyen gyakran)
