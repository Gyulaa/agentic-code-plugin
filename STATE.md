# Állapot

Frissítve: 2026-10-25. Egy oldal maradjon: a `/agentic-code:save-work` írja át, a `/agentic-code:resume-work` olvassa először.

## Mi ez
Az `agentic-code` Claude Code plugin forrása (skillek, guard hook, `project-setup` sablonok).

## Most
- 0.4.0 készül a `feat/design-skills` ágon: `design`, `design-review` és `seo` skill, `slop_check.py` és `seo_check.py` (kérésre), a `project-setup`, `quality-gate`, `privacy-check` és `match-the-codebase` igazítva. Spec: `docs/specs/2026-10-25-design-and-seo-skills.md`.
- A kutatás helyben, a gitben nincs: `research/design-skills-research.md`, `research/copy-research.md`, `research/seo-research.md`.
- 0.3.1 a `main`-ben (a nyilvános-commit szabály).

## Nyitott ágak és PR-ek
- `feat/design-skills` (helyi, még nincs pusholva).

## Blokkol / várunk rá
- Push és PR Gyula engedélyére.
- Nyilvános kiadás előtt LICENSE kell (a `claude plugin validate` jelzi); a licencről Gyula dönt.

## Következő lépés
1. Push és PR a `feat/design-skills` ágról, merge után `/plugin marketplace update agentic-code-plugin`.
2. Kipróbálás egy valódi projekten: egy landing oldal és egy Flutter-képernyő a `design` skillel, utána `design-review` és `seo`; a tapasztalat a Súrlódás listába.

## Súrlódás
- (még nincs; soronként egy: mi volt lassú vagy hibázott ismételten, milyen gyakran)
