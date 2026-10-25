# Spec: `design`, `design-review` és `seo` skill (0.4.0)

2026-10-25. Ág: `feat/design-skills`. A háttér helyben: `research/design-skills-research.md`, `research/copy-research.md`, `research/seo-research.md` (nincs a gitben). A döntések: a design-jegyzet 8. pontja, és Gyula 2026-10-25-i igene a külön `seo` skillre.

## Cél
A plugin felhasználói (bármilyen projektben) weboldalt és appot tudjanak építeni Claude-dal úgy, hogy az eredmény korszerű, nem gépi kinézetű, akadálymentes, a platformhoz illő, jó szövegű, és nyilvános oldalnál a klasszikus és az AI-keresőkben is megtalálható legyen.

## Viselkedés (elfogadási feltételek)
- [ ] `design` skill: kontextus (`DESIGN.md`, vagy egy kérdéskör után megírja a sablonból), a felület módja (Persuade / Operate / Read / Experience), terv a kód előtt (irány a tárgyból, 4–6 OKLCH-szín, betűszerepek, ASCII-vázlat, generikus-teszt), build a projekt tokenjeivel, ellenőrzés képernyőképpel (3 szélesség vagy 2 eszköz, legfeljebb 3 kör), azzal az eszközzel, ami elérhető; ha nincs, javasol egyet.
- [ ] `design` referenciák: `anti-patterns.md`, `web.md`, `native.md` (iOS, Android, Flutter), `product-ui.md`, `copy.md`; a 3D csak pár sorban.
- [ ] `templates/DESIGN.md`: a Google Stitch formátumával kompatibilis (YAML front matter, a nyolc szakasz a kanonikus sorrendben), plusz `Motion` és `Platforms` szakasz a végén.
- [ ] `scripts/slop_check.py`: python3 stdlib, csak kérésre fut; CSS, HTML, JSX/TSX, Vue, Svelte, Astro és Dart fájlokra; `path:line: [rule] message` kimenet; a `slop-ok` jelölésű sor kimarad; kilépési kód 0 (nincs találat), 2 (van), 1 (hibás használat).
- [ ] `design-review` skill: hatókör és kontextus, renderelt nézet, egyszerre végigvitt ellenőrzőlista (alapszint, kidolgozás, generikus jelek, szöveg a látogatói lépéslánccal, tokenek), súlyosság szerint rangsorolt jelentés bizonyítékkal; javítás csak a felhasználó választása után.
- [ ] `seo` skill: az oldal célja és keresési szándéka, technikai kapuk (szerveroldali HTML, crawlerek, kanonikus URL, sitemap, hreflang, CWV), tartalom (válasz elöl, tények forrással, szerző), metaadat és strukturált adat, mérés és őszinte elvárások; a tanítási botokról a tulajdonos dönt.
- [ ] `seo` referenciák: `technical.md`, `content.md`, `structured-data.md`.
- [ ] `scripts/seo_check.py`: python3 stdlib, kérésre; HTML-fájlokra, mappára vagy URL-re; oldalanként title, description, `lang`, canonical, `h1`, `meta robots`, `hreflang`, JSON-LD érvényesség, kép `alt` és méret, szöveg a HTML-ben; oldalak között duplikált title és description; robots.txt ismert botonként; sitemap. Kilépési kód 0/2/1, mint a `slop_check.py`.
- [ ] A projekt befogadja: `project-setup` (interjúkérdés, ajánlott skillek, `DESIGN.md` UI-projektnél, `CLAUDE.md` sablon sora), `quality-gate` (UI- és nyilvános oldal-változásnál a két skill), `privacy-check` (harmadik féltől betöltött font és beágyazás), README (skilltábla, "What's new", források), `plugin.json` leírás.
- [ ] Minden fájl angol, általános, nincs benne egyetlen projekt neve sem; a fizetős kurzusanyagból nincs szöveg.

## Nincs benne
- Mély 3D-munka, képgenerálás, külön `copywriting` skill, hook a két szkripthez, `llms.txt` alapértelmezésként, a Stitch CLI mint függőség.

## Terv
- Új: `plugins/agentic-code/skills/design/` (`SKILL.md`, `references/`, `templates/DESIGN.md`, `scripts/slop_check.py`), `skills/design-review/SKILL.md`, `skills/seo/` (`SKILL.md`, `references/`, `scripts/seo_check.py`).
- A `design-review` a `design` fájljaira `${CLAUDE_PLUGIN_ROOT}/skills/design/...` úton hivatkozik; a saját szkriptre `${CLAUDE_SKILL_DIR}`.
- Tesztek: `tests/test_slop_check.py`, `tests/test_seo_check.py` (subprocess, ideiglenes fájlok, mint a `tests/test_guard.py`); a `scripts/check.sh` már futtatja a `tests/` alatti unittesteket.

## Feladatok
1. `design` skill, referenciák, sablon.
2. `slop_check.py` és a tesztje.
3. `design-review` skill.
4. `seo` skill és referenciák.
5. `seo_check.py` és a tesztje.
6. A projekt frissítése (project-setup, quality-gate, privacy-check, README, plugin.json leírás, `docs/decisions.md`, `STATE.md`).
7. Kiadás: 0.4.0 külön commitban.

## Ellenőrzés
- `scripts/check.sh` → `OK` (szintaxis, JSON, `claude plugin validate`, az összes teszt).
- Mindkét szkript lefut egy kis mintaprojekten (szándékos hibákkal és tiszta változattal).
- `claude --plugin-dir ./plugins/agentic-code` alatt a három skill megjelenik a listában.
- Független, csak olvasó átnézés a spec ellen.
- privacy: a skillek nem gyűjtenek adatot; a `seo_check.py` csak a megadott URL-eket, a hosztjuk `robots.txt`-jét és a sitemapet kéri le (a `robots.txt`-ben megnevezett sitemap más hoszton is lehet).
