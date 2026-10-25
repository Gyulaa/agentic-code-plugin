# Döntések

Tartós döntésenként egy bejegyzés, legújabb felül. Ha egy döntés változik, a helyén javítjuk (a változás dátumával), nem duplikáljuk.

## 2026-10-25 · A repó nyilvánossá tehető állapotban marad; a kutatás helyben
- **Döntés:** Minden commitolt fájl nyilvánosan is vállalható. A kutatási jegyzetek (források kivonatai, harmadik fél anyagainak értékelése) a gitignore-olt `research/` mappába kerülnek. A pluginban a `match-the-codebase` "What we never ship" listája is kimondja: minden commit úgy készül, mintha a repó nyilvános lenne.
- **Miért:** A plugin később nyilvános lehet. A git története a commitolt fájlokat akkor is megőrzi, ha később töröljük őket, a kutatásokért pedig Gyula nem akar nyilvánosan felelősséget vállalni.
- **Érinti:** `.gitignore`, `CLAUDE.md`, `plugins/agentic-code/skills/match-the-codebase/SKILL.md`. A `research/` nincs mentve a gitben, a biztonsági mentése a meghajtó mentésén múlik.

## 2026-10-25 · A plugin a saját repójában is a saját szabályai szerint működik, könnyített setuppal
- **Döntés:** A plugin fejlesztésekor is a plugin skilljeit használjuk (resume-work, save-work, quality-gate, git-workflow). A repó S méretű setupot kap, csak `CLAUDE.md`, `STATE.md`, `docs/decisions.md`, `scripts/check.sh` (a lint lépés külön a `scripts/lint.sh`-ban: shell-, Python- és JSON-szintaxis, `claude plugin validate`) és `.githooks/pre-commit` fájlokkal. Kimarad: `.claude/guard.json` (nincs éles rendszer), `privacy-check` (nincs személyes adat), kódgráf (kicsi a repó), `docs/bugs.md` (az első valódi hibánál jön létre), `CLAUDE.local.md` és `.claude/settings.json` (egyszemélyes repó, kevés parancs).
- **Miért:** Itt bukkannak fel először a plugin hibái. A gyökérbe kerülő fájlok nem szennyezik a plugint, mert a marketplace csak a `./plugins/agentic-code` mappát szállítja.
- **Érinti:** a repó gyökere; a `plugins/agentic-code/` nem változott.
