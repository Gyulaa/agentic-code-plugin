# Döntések

Tartós döntésenként egy bejegyzés, legújabb felül. Ha egy döntés változik, a helyén javítjuk (a változás dátumával), nem duplikáljuk.

## 2026-10-28 · Tesztszint két tengelyen, adósság a repóban, szigorú kapu; két kiadás
- **Döntés:** A `quality-gate` szélesség (small, medium, large) és mélység (normal, sensitive, critical) szerint skáláz; a teendő a kettő uniója, szkript nélkül is szabályként használható. A besorolást opcionális szkriptek adják a diffből (`risk_level.py`, a térkép a `scripts/risk-map.json`), nem az ügynök leírásából; ami a térképre nem illik, `unknown`, és érzékenyként kezeljük. A kapu a pre-commit hookban alapból megállít (`RISK_GATE=warn` csak a felhasználó kérésére), és három kiutat ad: a diff bizonyítja, igazolás egyetlen commitra (a HEAD-hez kötve, magától lejár), vagy tesztadósság; kritikus mélységnél adósság nincs. A tesztadósság tételenként egy fájl a repóban (`docs/test-debt/`), a commit része, és csak bizonyítással zárható, a visszafordítás-próbával együtt. Két kiadás: 0.4.1 (hook-környezet, ütközésfeloldás) és 0.5.0 (a többi).
- **Miért:** A minőség az első, de egy szövegjavítás és egy fizetési logika nem kaphatja ugyanazt a kört. A leírásból vett besorolást megfogalmazással le lehet vinni, a diffből vettet nem. A repóban élő adósság az ággal együtt él és hal, nem árvul el, és nem kell hozzá külön szolgáltatás. A kapu csak akkor ér valamit, ha megáll. A 0.4.1 két valódi hibát javít, azokat nem szabad a nagyobb kiadás mögé zárni.
- **Érinti:** `quality-gate` (SKILL és `references/test-level.md`), `project-setup` (interjú, sablonok), `security-check`, `save-work`, `design-review`, `improve-workflow`, `githooks/pre-commit` sablon, `tests/`. Spec: `docs/specs/2026-10-28-testing-security-and-workflow-0.5.md`. A küszöbök (50 és 300 sor, 2 terület, 5 tétel, 14 nap) első becslések, az első valódi projekten mérni kell.

## 2026-10-25 · MIT licenc
- **Döntés:** A repó MIT licenc alatt áll (`LICENSE` a gyökérben, „Copyright (c) 2026 Gyula Miklós”; `"license": "MIT"` a `plugin.json`-ban).
- **Miért:** Elsősorban saját használatra, ingyen készül, de nyilvános lehet. Az MIT a legegyszerűbb megengedő licenc, kizárja a felelősséget („as is”), és a plugin-katalógus is megköveteli a licencet.
- **Érinti:** `LICENSE`, `README.md` (Licence szakasz), `plugins/agentic-code/.claude-plugin/plugin.json`.

## 2026-10-25 · Design és keresés: három skill, két kérésre futó ellenőrző
- **Döntés:** `design` (DESIGN.md a Google Stitch formátumában, a felület módja, terv a kód előtt, képernyőképes ellenőrzés, szövegírás a `references/copy.md`-ben), `design-review` (rangsorolt átnézés, javítás csak választás után) és külön `seo` (klasszikus és AI-keresés). A `slop_check.py` és a `seo_check.py` csak kérésre fut, nem hook. Flutter az első körtől; 3D csak pár sorban; `llms.txt` és "AI-schema" nem alapértelmezés.
- **Miért:** A SEO máskor kell, mint a design (nyilvános oldal design nélkül is, app és belső felület SEO nélkül). A Google szerint az AI-keresésnek nincs külön követelménye; a mért különbség a JavaScriptet nem futtató AI-crawlerek és a crawlerenkénti robots-szabály. A gépi ellenőrzők mintát találnak, nem minőséget, ezért nem blokkolhatnak commitot.
- **Érinti:** `plugins/agentic-code/skills/{design,design-review,seo}/`, a `project-setup`, `quality-gate`, `privacy-check` és `match-the-codebase` egy-egy sora, `tests/test_slop_check.py`, `tests/test_seo_check.py`. Spec: `docs/specs/2026-10-25-design-and-seo-skills.md`; háttér helyben a `research/` három jegyzetében.

## 2026-10-25 · A repó nyilvánossá tehető állapotban marad; a kutatás helyben
- **Döntés:** Minden commitolt fájl nyilvánosan is vállalható. A kutatási jegyzetek (források kivonatai, harmadik fél anyagainak értékelése) a gitignore-olt `research/` mappába kerülnek. A pluginban a `match-the-codebase` "What we never ship" listája is kimondja: minden commit úgy készül, mintha a repó nyilvános lenne.
- **Miért:** A plugin később nyilvános lehet. A git története a commitolt fájlokat akkor is megőrzi, ha később töröljük őket, a kutatásokért pedig Gyula nem akar nyilvánosan felelősséget vállalni.
- **Érinti:** `.gitignore`, `CLAUDE.md`, `plugins/agentic-code/skills/match-the-codebase/SKILL.md`. A `research/` nincs mentve a gitben, a biztonsági mentése a meghajtó mentésén múlik.

## 2026-10-25 · A plugin a saját repójában is a saját szabályai szerint működik, könnyített setuppal
- **Döntés:** A plugin fejlesztésekor is a plugin skilljeit használjuk (resume-work, save-work, quality-gate, git-workflow). A repó S méretű setupot kap, csak `CLAUDE.md`, `STATE.md`, `docs/decisions.md`, `scripts/check.sh` (a lint lépés külön a `scripts/lint.sh`-ban: shell-, Python- és JSON-szintaxis, `claude plugin validate`) és `.githooks/pre-commit` fájlokkal. Kimarad: `.claude/guard.json` (nincs éles rendszer), `privacy-check` (nincs személyes adat), kódgráf (kicsi a repó), `docs/bugs.md` (az első valódi hibánál jön létre), `CLAUDE.local.md` és `.claude/settings.json` (egyszemélyes repó, kevés parancs).
- **Miért:** Itt bukkannak fel először a plugin hibái. A gyökérbe kerülő fájlok nem szennyezik a plugint, mert a marketplace csak a `./plugins/agentic-code` mappát szállítja.
- **Érinti:** a repó gyökere; a `plugins/agentic-code/` nem változott.
