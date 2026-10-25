# Állapot

Frissítve: 2026-10-25. Egy oldal maradjon: a `/agentic-code:save-work` írja át, a `/agentic-code:resume-work` olvassa először.

## Mi ez
Az `agentic-code` Claude Code plugin forrása (skillek, guard hook, `project-setup` sablonok).

## Most
- 0.3.1 (2026-10-25): a `match-the-codebase` minden commitot nyilvánosnak tekint; a README és a skillek nem nevezik meg, melyik projektből nőtt ki a plugin. A repó nyilvánossá tehető állapotban marad (`docs/decisions.md`).
- A repó saját munkakörnyezete (`CLAUDE.md`, `STATE.md`, `docs/decisions.md`, `scripts/check.sh`, pre-commit hook) a `main`-ben.
- Kész a kutatás két design skillhez (`design`, `design-review`) és a szövegíráshoz: `research/design-skills-research.md`, `research/copy-research.md` (helyi, nincs a gitben).

## Nyitott ágak és PR-ek
- (nincs)

## Blokkol / várunk rá
- (semmi)

## Következő lépés
1. `spec` a két design skillre a `research/` két jegyzete alapján, új `feat/design-skills` ágon. A döntések a `research/design-skills-research.md` 8. pontjában: két skill, Stitch-kompatibilis `DESIGN.md`, `slop_check.py` csak kérésre, képernyőkép azzal, ami elérhető, Flutter az első körben, a szövegírás a `design` referenciája, 3D csak pár sorban.

## Súrlódás
- (még nincs; soronként egy: mi volt lassú vagy hibázott ismételten, milyen gyakran)
