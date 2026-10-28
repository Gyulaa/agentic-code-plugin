# Spec: dinamikus tesztelés, tesztadósság, biztonsági lista és munkamód-javítások (0.4.1 és 0.5.0)

2026-10-28. Ágak: `fix/hook-env-and-merge-rules` (0.4.1), `feat/risk-based-testing` (0.5.0). A háttér helyben: `research/workflow-learnings-research.md` (nincs a gitben). A döntések: Gyula 2026-10-28-i igene a hét javaslatra; a három megválaszolt kérdés (lásd „Döntések”).

## Cél
Egy másik, a plugintól független projekt munkamódjából hét olyan tanulság jön át, amely bármely projektben hasznos, általánosítva és saját szöveggel:
1. a pre-commit hook helyes környezete (egy valódi hiba a sablonjainkban);
2. biztonságos beolvasztás és ütközésfeloldás;
3. **dinamikus tesztszint és tesztadósság**: a teendő a változás méretétől és veszélyességétől függ, a besorolást egy szkript végzi a diffből, a kihagyott teszt nem vész el;
4. `security-check` skill („soha ne bízz a kliensben”);
5. a `save-work` döntés-próbája, archiválása és a rövid „What's new”;
6. legrosszabb eset adatra a `design-review`-ban;
7. mérési eljárás az `improve-workflow`-ban.

A közös elv a `quality-gate` mostani első mondata: a minőség az első, a tesztekre nem spórolunk. A dinamikus tesztelés **nem lazít**: kevesebb kört ad ott, ahol nincs kockázat, és szigorúbbat ott, ahol van. Tokent a felesleges körökön és az újraolvasáson spórolunk (egy munkamenet költségének nagy részét az előzmény újraolvasása adja), a teszten nem.

## Viselkedés (elfogadási feltételek)

### 0.4.1
- [ ] A `check.sh` sablon és a repó saját `scripts/check.sh`-ja: a fájllista összegyűjtése után, a külső eszközök (formázó, lint, teszt) indítása előtt törli a git helyi környezeti változóit (`git rev-parse --local-env-vars` listája, ciklussal). A fájllistát még a hook környezetében gyűjti, mert `git commit -o` és `-a` esetén a `GIT_INDEX_FILE` mondja meg, mi van kijelölve.
- [ ] Teszt: valódi pre-commit hookkal, ideiglenes repóban, részleges commitnál (`git commit -o <fájl>`) a konfigurált teszt parancs nem lát `GIT_DIR`-t és `GIT_INDEX_FILE`-t, és a check zöld.
- [ ] `git-workflow`: új szakasz az ütközésfeloldásról és beolvasztásról: kódütközést csak helyben oldunk (`git merge origin/<default>` az ágba), a web-szerkesztőben nem; a feloldott fájlt mindkét oldal tartalmával együtt olvasjuk el, `ours` vagy `theirs` egészében csak indoklással; **minden beolvasztás után (ütközéssel vagy anélkül) lefut a check, és csak utána megy a push**, mert a tiszta, szöveges beolvasztás is törhet (szemantikus ütközés: egy átnevezés és egy új hívó két külön PR-ban); ha a default ág nem épül, az kritikus hiba a hibalistában, `origin:` sorral; a felhasználónak javasolni (nem megtenni): a védett ágon „branches must be up to date” vagy merge queue.

### 0.5.0: dinamikus tesztszint
- [ ] **Két tengely.** Szélesség (mekkora): `small` (legfeljebb 50 kódsor, 1 terület), `medium` (legfeljebb 300 sor, legfeljebb 2 terület), `large` (afölött, új felület vagy funkció, release ág, vagy betelt adósságplafon). Mélység (mennyire veszélyes): `normal`, `sensitive`, `critical`. A teendő a kettő uniója: egy egysoros, kritikus változás nem kap felületi mátrixot, de kap határeset-tesztet és visszafordítás-próbát.
- [ ] **Kritikus** az, ami pénzt, időt és dátumot, jogosultságot, hozzáférési szabályt, adatírási utat, szerver-szerződést (API-séma), migrációt, függőséget vagy jogi ígéretet érint. Teendők: `new-test`, `edge-cases` (határeset-unit teszt: 0, negatív, éjfél, kerekítés, üres, nagyon nagy), `revert-proof`, `adversarial-review` (friss, csak olvasó al-ügynök, amely a diffet és a feltételeket látja, az észjárást nem), `contract-test` (szabály- vagy szerződésteszt, ha van ilyen réteg), `server-twin` (a másik oldal jelzése, ha a logika két helyen él), és a `security-check` skill. **Itt semmi nem írható adósságba.**
- [ ] **Érzékeny:** adatréteg, közös komponens, adatírás, a kódgráfban sok függő (ha a projektben van gráf), a térképen kívüli fájl. Teendő: `full-write` (az írás a teljes mezőlistát írja: egy kihagyott mező törölheti a tárolt értéket). Szélesség szerinti teendők mellé.
- [ ] **Szélesség szerinti teendők:** `small`: a végén egyszer a check; új teszt nem kell. `medium`: új vagy módosított teszt a megváltozott viselkedésre (`new-test`). `large`: felületi mátrix az új felületre (`ui-matrix`: állapotok, kis képernyő, nagy betű, mindkét téma; csak ha a térkép `ui` útvonalat ad), egyszer élőben kipróbálva (`live-try`), és a terület nyitott adósságának törlesztése (`pay-debt`).
- [ ] **A besorolást a szkript adja a diffből**, nem az ügynök leírásából, így megfogalmazással nem vihető lejjebb. Egy fájl pontosan egy osztályba esik, sorrendben, az első egyezés nyer: `skip` (dokumentáció, képek, generált és lock-fájlok), `critical` (fájl vagy fájl + **tartalmi horgony**: reguláris kifejezés a változott soron, így egy általában ártalmatlan fájl csak akkor kritikus, ha a horgonyt érinti), `test`, `sensitive` (útvonal vagy tartalmi jel, például írás a változott sorban), `normal`, **ami semmire sem illik: `unknown`, érzékenyként kezelve, figyelmeztetéssel** (hibabiztos alapállás: ha a térkép hiányos, semmi nem csúszik le „kicsibe”).
- [ ] **Térkép:** `scripts/risk-map.json` (a repóban, a kóddal együtt változik). Mezői: `skip`, `test`, `critical` (elemei: `glob`, opcionális `anchor`, `why`, `server_twin`), `sensitive` (`glob` vagy `content`), `normal` (a ténylegesen ismert forrás-útvonalak), `ui` (globok), `areas` (hogyan lesz a fájl útvonalából terület; alap: az első két útvonalelem), `thresholds` (a szélesség küszöbei), `debt_ceiling` (`open`: 5, `days`: 14), `gate` (`strict` vagy `warn`), `test_one` (egy teszt futtatásának parancsa `{file}` és `{name}` helyettesítéssel, `shlex.quote`-olva), `ui_matrix_marker` (reguláris kifejezés, amely a diffben bizonyítja a mátrixot, alap üres: akkor csak igazolható). Térkép nélkül a kapu csak a szélességet számolja, minden futáskor szól, hogy nincs térkép, és soha nem állít meg.
- [ ] **A kapu** (`risk_level.py gate`, a pre-commit hookban a check után): minden teendőre három út van, harmadik nincs: (1) **a diff bizonyítja** (`new-test`: a változásban van teszt-osztályú fájl; `ui-matrix`: a `ui_matrix_marker` illeszkedik; `debt`: a diffben új adósságtétel ugyanarra a teendőre); (2) **igazolva** (`risk_level.py done <teendő> "<mit csináltál, mi lett>"`, egyetlen commitra szól, a HEAD azonosítójához kötve, ezért magától lejár, és nincs szükség post-commit hookra); (3) **adósságba írva**, ha a szint megengedi (kritikusnál soha). Ha egyik sem, a commit megáll, és a kimenet a pontos parancsot írja. `--no-verify` soha. `RISK_GATE=warn` csak a felhasználó kifejezett kérésére.
- [ ] **A kapu kihagyja:** a csak `skip`-osztályú fájlokat tartalmazó commitot, és az összeolvasztó commitot (`MERGE_HEAD` van), mindkettőnél egy sor üzenettel. A beolvasztás után a kézi check (lásd 0.4.1) marad az ellenőrzés.
- [ ] **Gyengített teszt:** ha a diffben teszt-osztályú fájl törlődik, vagy a teszt-sorok nettó száma csökken, a kimenet külön, figyelmeztető sort ír („tesztet töröltél vagy gyengítettél: a bukó teszt követelmény, nem akadály”); nem állít meg, mert van jogos eset, de látszik.
- [ ] **Terület-szint:** a terület az útvonalból jön; az adósságplafon (nyitott tételek száma vagy a legrégebbi kora) a terület következő változását `large`-ra emeli, törlesztéssel.
- [ ] **Térkép-lefedettség:** `risk_level.py map-coverage` kilistázza a követett fájlokat, amelyek `unknown`-ba esnek. A `project-setup` a térkép megírása után futtatja, és nullára viszi.
- [ ] A szkript kimenete rövid (kb. 20 sor): `LEVEL: large x sensitive (349 lines; area: onboarding)`, az okok soronként (`ok: sensitive: path (why)`), a teendők állapottal (`done by diff`, `attested`, `debt`, `MISSING`). `--json` géppel olvasható kimenetet ad.

### 0.5.0: tesztadósság
- [ ] **Felírás:** `test_debt.py add <teendő> --given … --when … --then …` egy fájlt hoz létre: `docs/test-debt/TD-<ÉÉÉÉHHNN>-<4 hex>.json` (az azonosítóban nincs sorszám, hogy két ág ne ütközzön). A fájl a commit része, az ággal együtt él és hal; egy elvetett ág nem hagy árva adósságot.
- [ ] **A gép tölti ki, amit a diffből tud:** cél (fájl, szimbólum, egy jellegzetes kódsor horgonyként, sorszám nélkül, mert elcsúszik), változás (szülő commit, legfeljebb 15 sor diff), hova (a célt importáló meglévő tesztfájl, különben a tükör-útvonal; a teszt pontos neve, benne az azonosító), minta (a terület legközelebbi, azonos típusú tesztje), futtatás (a `test_one` kitöltve). **Az ügynök csak az állítást írja** (adott / amikor / akkor), úgy, hogy egy olyan ügynök is elég legyen, amelyik a mostani beszélgetést nem látta.
- [ ] **Homályos állítást visszadob:** mindhárom mező legalább 12 karakter, konkrét érték kell (szám, szerepkör, állapot, idézett szöveg), és az „akkor” nem lehet csak „működjön” vagy „helyes”.
- [ ] **Kritikus mélységnél a felírás elutasított** (kilépési kód 2, a magyarázattal), a kapu is.
- [ ] **Lezárás csak bizonyítással** (`test_debt.py close <id>`): (1) a megnevezett teszt létezik a megadott fájlban; (2) a tesztfájl importálja vagy említi a célt; (3) csak ez a teszt lefut, és zöld; (4) **visszafordítás-próba** változás-bizonyításnál: a célfájl a szülő commit állapotába kerül, és a tesztnek ott **el kell buknia**; ha a régi kódon is zöld, a teszt nem a változást védi, a lezárás elutasított. Élő próbánál nincs teszt: `close <id> --attested "<mit csináltál, mi lett>"`.
- [ ] **A visszafordítás-próba nem veszíthet munkát:** csak akkor indul, ha a célfájlnak nincs nem commitolt módosítása (különben elutasít, és megmondja miért); a fájl másolata a git-könyvtáron belülre kerül, a visszaállítás `finally` ágban fut, és egy helyreállítási jelölő is készül, amelyből a következő futás visszaállít, ha a folyamat megszakadt. A szkript soha nem használ `git stash`-t és `git checkout -- .`-ot.
- [ ] **Listázás:** `test_debt.py list [--area X]` (nyitott tételek, kor szerint), `show <id>`. A `risk_level.py level` kiírja a terület nyitott tételeit, ha a szélesség `large`.
- [ ] **A tesztadósság nem hibalista:** a hiba a viselkedés hibája, az adósság egy hiányzó teszt; ezt a `save-work` és a `quality-gate` szövege is kimondja.

### 0.5.0: skillek és sablonok
- [ ] `quality-gate`: új szakasz „Test level” (rövid, a táblázatok és a szabály), részletek a `quality-gate/references/test-level.md`-ben; a „Who triggers what” táblázat új sora a kapuról; a `security-check` hivatkozása kritikus változásnál. **Szkript nélkül is használható szabályként:** ugyanaz a két tengely, kézzel, és bizonytalanságnál a magasabb szint.
- [ ] `project-setup`: az interjúba kérdés a kockázatos területekről („mi kezel pénzt, időt, jogosultságot, hozzáférési szabályt, adatírást, szerver-szerződést?”); a sablonok közé `scripts/risk_level.py`, `scripts/test_debt.py`, `scripts/risk-map.json` (a projekt kockázatos területeiből megírva, nem üresen), a `githooks/pre-commit` bővítése a kapuval; csak kérésre (M és L méret ajánlott, S-nél ajánlás nélkül); a térkép-lefedettség lefut; a `CLAUDE.md` sablon egy sort kap; az ajánlott skillek közé a `security-check`.
- [ ] A kapu a hook sablonjában csak akkor fut, ha `scripts/risk_level.py` létezik; a `SKIP_CHECK=1` mindkettőt kihagyja, mint most.
- [ ] README: skilltábla (`security-check`), egy mondat az őszinte elvárásról (a fő haszon a minőség és a kevesebb felesleges kör; a token-megtakarítás mérsékelt, mérni kell: lásd `improve-workflow`), „What's new”, források.

### 0.5.0: `security-check`
- [ ] Új skill, `skills/security-check/SKILL.md` + `references/`. **Mikor:** csak biztonsági szempontból érzékeny változásnál (hitelesítés, szerepkör és tagság, hozzáférési szabály, végpont, export, fizetés, feltöltés, titok, korlát, meghívás), ha a `risk_level.py` kritikust jelez, vagy ha a felhasználó azt kérdezi, biztonságos-e. Nem a hétköznapi felület- és szövegváltozásra.
- [ ] **Alapelv:** soha ne bízz a kliensben: minden ár, azonosító, szerepkör, előfizetési állapot, korlát és számláló, ami csak a kliensben vagy a kérés törzsében él, a támadó kezében van; a kliensoldali ellenőrzés kényelem, nem védelem.
- [ ] **Jelentés:** csak valódi hiba, súlyosság szerint (kritikus, magas, közepes, alacsony), mindegyikhez fájl és sor, **mit tud vele tenni a támadó konkrétan**, és a javítás; a kritikus a válasz elején; stílus- és „még jobb lenne” megjegyzés nincs. Javítás csak a felhasználó választása után.
- [ ] **A lista** (általános, technológiafüggetlen; a technológia-specifikus részek a `references/`-ben, az ügynök csak az illőt tölti be): (1) hozzáférési szabályok (adatbázis-szabály, RLS, policy): nyitott vagy csak bejelentkezés-függő szabály, tulajdon- és bérlő-ellenőrzés, **mezőszintű írásvédelem** (a felhasználó ne írhassa át a saját szerepkörét, jogosultsági és előfizetési mezőjét), gyerek-gyűjtemények és -táblák saját szabálya, a szerepkör aláírt tokenből vagy a szerverről jöjjön, ne a felhasználó által írható dokumentumból, minden szabályváltozáshoz teszt emulátoron vagy tesztadatbázison; (2) szerepkör és tagság; (3) létszámkorlát és előfizetés a szerveren; (4) több-bérlős adat: a bérlőazonosító minden dokumentumban van és minden lekérdezés szűr rá; (5) meghívó és bearer token: soha nem kerül kliensbe; (6) végpontok és export: hitelesítés minden hívásnál, a hívó jogosultsága az erőforrásra, a törzsből jövő azonosítóban, árban, szerepkörben nem bízunk, a felhasználó adta URL-re szerveroldali kérés (SSRF) tiltott vagy szűrt; (7) szerveroldali korlát a drága vagy visszaélhető végpontra (export, e-mail, AI-hívás), napi felsővel; AI-szolgáltatás kulcsa soha nem kerül a kliensbe; (8) titkok: nincs a kódban és a commitban, ha kikerült, **cserélni kell**, a törlés nem elég; (9) fizetés: az árat a szerver számolja, a webhook aláírását ellenőrizzük; (10) mobil és böngésző: token biztonságos tárolóban, nem sima `localStorage`-ban vagy beállításfájlban; (11) bemenet: injektálás, kimenet-kódolás, fájlfeltöltés típus- és méretellenőrzése; (12) telepítés: debug kikapcsolva, CORS szűk, nincs titok a forrástérképben; (13) személyes adat: ha a változás új adatot gyűjt, a `privacy-check` is fut.
- [ ] **Forrás:** a README „Sources” sora és a skill végén egy mondat megnevezi a `raroque/vibe-security-skill` (MIT) kilenc kategóriáját mint ihletet, és az OWASP Top 10 2025-öt (a hozzáférés-vezérlés hibája az első; az SSRF beleolvadt). A szöveg saját; ha bármely mondatot szó szerint veszünk át, az MIT-értesítés a forrás LICENSE-éből mellé kerül, a szerző nevével szó szerint.

### 0.5.0: `save-work`, `design-review`, `improve-workflow`
- [ ] `save-work`, **döntés-próba:** döntésnaplóba csak az kerül, ami a jövőbeli munkát irányítja: szabály, irány, vagy egy ok, amely nélkül a kérdés újra előkerülne (a visszafordítás drága vagy zavaros lenne az ok ismerete nélkül). Egyszeri lépés (ág beolvasztása, függvény törlése, egy szöveg), hibajavítás, rutin függőségfrissítés és az, amit egy elfogadott döntés már fed, nem döntés: a naplóba, az állapotfájlba vagy a PR-ba megy. Csapatnál a bejegyzésben ott a „ki döntött”.
- [ ] `save-work`, **archiválás:** ahol a projekt tételenként egy fájlt vagy külön archívumot használ, a lezárt tételek (javított hiba, elvetett vagy felváltott döntés, 30 napnál régebbi napló) egy menetben, a fájlnév megtartásával az archívumba költöznek; az elfogadott döntés marad; döntést és hibát nem törlünk, csak állapotot váltunk; egyszerre legfeljebb 20, afölött a felhasználó dönt.
- [ ] `save-work`, **What's new:** ahol a README csapat-hírfolyam (nem kiadási napló), legfeljebb 5 bejegyzés marad, egyik sem régebbi 7 napnál; a fölösleg változatlanul az archívumba megy; ha a témának már van sora, azt frissítjük, nem írunk újat. A kiadási napló jellegű szakaszhoz (mint ez a plugin saját README-je) nem nyúl.
- [ ] `design-review`, **legrosszabb eset adatra:** új lépés a „Check everything in one pass” után: minden megjelenített értékhez a valószerű legrosszabb eset (hosszú, szóköz nélküli és összetett szavas nevek, egykarakteres név, hiányzó és null mezők, üres lista, nulla, hatalmas darabszám, extrém összeg és dátum, ékezetek, emoji, jobbról balra író szöveg, 200%-os betűméret, keskeny szélesség, lassú és offline betöltés); a két adathalmaz egy **csak fejlesztői** kapcsoló mögött és egy tesztben; jelentés: mi tört el, súlyosság (adatvesztés, elrontott elrendezés, olvashatatlan, kozmetikai), és a javítás. A lépés nem tervez újra és nem ítél ízlést. Katalógus: `design-review/references/worst-case-data.md`. A `design` skill ellenőrző lépésébe egy sor hivatkozás.
- [ ] `design-review` forrás: Emil Kowalski `break-ui` (MIT) ötlete a README „Sources” sorában; a szöveg saját; szó szerinti átvételnél az MIT-értesítés az eredeti LICENSE-ből.
- [ ] `improve-workflow`, **új szakasz „Measure a change”:** ugyanaz a feladat két friss al-ügynökkel, az egyik az alap eszközökkel, a másik a vizsgált beállítással; **előbb rögzítsd:** a feladat szövege szó szerint egyetlen önálló promptként, a kiinduló commit, a modell és az effort (mindkét oldalon ugyanaz), az elfogadási feltétel; két homokozó-klón (`git clone --local` a scratchpadbe), soha az élő repó; **utólag csak visszajátszással mérj**, a mostani, betöltött kontextusban nem (a cache torzít); mérés: token és eszközhívás az al-ügynökök befejezési értesítéséből, pontosság a rögzített feltétel szerint; 10% alatti különbségnél mindkettő még egyszer fusson (n=2), az átlag számít; előtte mondd meg, hogy a mérés kb. a feladat két-háromszorosába kerül, és változtatási feladatnál kérdezz rá; spórolási százalékot csak a saját mérési táblából idézz.

## Nincs benne
- Gyorsított check-mód (`--fast`, csak a változott fájlok tesztjei): a mért gépi idő kicsi, a költség az ügynök körei, és a „kapcsolódó teszt” stack-specifikus; később, mérés után.
- CI-kapu a teljes PR-ágra és a lezárt adósságtételek újraellenőrzése; változás-plafon (a legutóbbi teljes teszt óta változott sorok); kalibrációs minta a régi commitokból: a `project-setup` ajánlásában említett következő lépések, nem ennek a kiadásnak a része.
- Kódgráf-alapú „sok függő” jel (a projektek többségében nincs gráf); a térkép `sensitive` útvonalai ezt helyettesítik.
- Hook, amely a tesztfájl szerkesztését tiltja (a `quality-gate` szabálya marad szöveg és a kapu figyelmeztetése).
- Tartós szolgáltatáshoz kötött adósság-tár (külön adatbázis, közös jegyzettár); az adósság a repóban él.
- A védett ág szabályának beállítása (a felhasználó dolga, az ügynök csak javasolja).
- Windows natív támogatása (a szkriptek macOS bash 3.2-n, Linuxon és Git Bash-ben a célok; Windowson nem teszteljük).

## Terv

### Fájlok
Új:
- `plugins/agentic-code/skills/security-check/SKILL.md`, `references/` (`access-control.md`, `server-and-secrets.md`, `client-and-mobile.md`)
- `plugins/agentic-code/skills/quality-gate/references/test-level.md`
- `plugins/agentic-code/skills/design-review/references/worst-case-data.md`
- `plugins/agentic-code/skills/project-setup/templates/scripts/risk_level.py`, `test_debt.py`, `risk-map.json`
- `tests/test_risk_level.py`, `tests/test_test_debt.py`, a hook-környezet esete a `tests/test_check.sh`-ban

Módosított: a `check.sh` sablon és a repó `scripts/check.sh`-ja, a `githooks/pre-commit` sablon és a repó `.githooks/pre-commit`-je, `git-workflow`, `quality-gate`, `save-work`, `design-review`, `design`, `improve-workflow`, `project-setup` (SKILL, interjú, stacks), a `CLAUDE.md` sablon, `README.md`, `plugin.json`, `docs/decisions.md`, `STATE.md`.

### Minta, amit követ
- A szkriptek: a `slop_check.py` és a `seo_check.py` (python3 stdlib, `path:line: [rule] message` stílus, kilépési kódok 0 / 2 / 1: rendben / találat vagy elutasítás / hibás használat); tesztjeik subprocessel és ideiglenes fájlokkal, mint a `tests/test_guard.py`.
- A hook és a check: a meglévő `check.sh` sablon (bash 3.2, `set -u`, rövid kimenet, `OK` / `FAILED`).
- Skillek: a `privacy-check` szerkezete (rövid, kérdések, mikor nem kell).

### Megkötések
- Minden fut macOS bash 3.2-vel és python3 standard könyvtárral (3.8 vagy újabb), függőség nélkül; nincs walrus-operátor, nincs `match`.
- A szkriptek soha nem `eval`-ezik a térkép vagy az adósságfájl tartalmát; az egyetlen futtatott, repó által adott parancs a `test_one` (ugyanaz a bizalmi szint, mint a `check.sh` konfigurációja), a helyettesített értékek `shlex.quote`-olva.
- A szkriptek csak a repó munkafájljaiba és a git-könyvtár `agentic/` almappájába (igazolások, helyreállítási jelölő; `git rev-parse --git-path`) írnak; a worktree-k és az almodulok miatt a git-könyvtár útvonalát soha nem találgatják.
- Szélső esetek, amelyeket a szkriptnek kezelnie kell: nincs commit még (üres repó), detached HEAD, átnevezés (`-M`), bináris fájl, törölt fájl, üres diff, nem commitolt módosítás a cél-fájlon, párhuzamos futás (a helyreállítási jelölő zárként is szolgál).
- A repó minden fájlja nyilvánosan vállalható marad (`CLAUDE.md`): a skillekbe, sablonokba és tesztekbe nem kerül egyetlen projekt neve, útvonala vagy szabálya sem; a példák kitaláltak (egy webshop, egy bérszámfejtő modul).

## Feladatok

**0.4.1** (ág: `fix/hook-env-and-merge-rules`)
1. **Hook-környezet.** Előbb a bukó teszt (`tests/test_check.sh`: részleges commit valódi hookkal, a teszt parancs `GIT_DIR`-t vagy `GIT_INDEX_FILE`-t lát: piros), utána a javítás a sablonban és a repó saját `scripts/check.sh`-jában. Commit: `fix: clear the git hook environment before running project tools`.
2. **`git-workflow` ütközés-szakasz.** Szöveg, nincs kód; a `quality-gate` „Known traps” szakaszába egy sor hivatkozás. Commit: `docs: resolve merge conflicts locally and check after every merge`.
3. **Kiadás 0.4.1:** `plugin.json` `version`, egy dátumozott sor a README „What's new” szakaszba (legújabb felül), külön commit: `chore: release 0.4.1`. `scripts/check.sh` → `OK`. A push és a PR külön engedélyre vár.

**0.5.0** (ág: `feat/risk-based-testing`, a 0.4.1 beolvadása után a frissített `main`-ről)
4. **`risk_level.py`: besorolás.** Tesztek először (ideiglenes git-repó): osztályozási sorrend, tartalmi horgony, `unknown` = érzékeny, szélesség küszöbök, terület, térkép nélküli viselkedés, átnevezés és törlés, üres diff, `--json`; utána a kód. `map-coverage` parancs.
5. **`risk_level.py`: kapu és igazolás.** Tesztek: bizonyítás a diffből, `done` (HEAD-hez kötött, lejár a következő commit után), kritikusnál adósság elutasítva, a kapu megáll és a pontos parancsot írja, összeolvasztó és csak-`skip` commit kihagyva, `RISK_GATE=warn`, gyengített teszt figyelmeztetés; utána a kód.
6. **`test_debt.py`.** Tesztek: `add` (gép tölti ki a mezőket, homályos állítás visszadobva, kritikusnál elutasítva), `list` és `show`, `close` négy bizonyítékkal, **a visszafordítás-próba mutációval ellenőrizve** (olyan teszt, amely a régi kódon is zöld, el kell utasítódjon), megszakadás utáni helyreállítás, nem commitolt módosításnál elutasítás; az adósságplafon bekötése a `risk_level.py`-ba; utána a kód.
7. **Térkép- és hook-sablon.** `risk-map.json` sablon, a `githooks/pre-commit` bővítése (a kapu csak ha a szkript létezik), a repó saját `.githooks/pre-commit`-je változatlan marad, ha a repónak nincs térképe (a saját `scripts/` csak a hook-környezet javítást kapja).
8. **`quality-gate` és `test-level.md`.** A két tengely, a táblázatok, a teendők, az adósság, a szkript nélküli használat, az „nem lazít” állítás és a mérés hivatkozása.
9. **`project-setup`.** Interjú, sablonok, ajánlott skillek, térkép-írás a kockázatos területekből, `map-coverage`, `CLAUDE.md` sor.
10. **`security-check` skill és referenciák.** A forrás-LICENSE letöltése és elolvasása előbb; saját szöveg.
11. **`save-work`.** Döntés-próba, archiválás, rövid „What's new”.
12. **`design-review` legrosszabb eset adatra** és a katalógus; `design` hivatkozás.
13. **`improve-workflow` „Measure a change”.**
14. **A projekt frissítése:** README (skilltábla, elvárás, források, „What's new”), `plugin.json` leírás, `docs/decisions.md` (a tesztszint és az adósság helye a repóban, a kapu szigora, a két kiadás), `STATE.md`.
15. **Kiadás 0.5.0:** `version`, „What's new”, külön commit. `scripts/check.sh` → `OK`. Push és PR külön engedélyre.

## Ellenőrzés
- `scripts/check.sh` → `OK` mindkét kiadás előtt (szintaxis, JSON, `claude plugin validate`, az összes teszt, a `security-check` skill is megjelenik).
- **Vég-vég tesztforgatókönyv** egy ideiglenes mintaprojekten (kitalált webshop, térképpel): (a) csak dokumentációt érintő commit: a kapu kihagy; (b) egysoros szövegjavítás egy `normal` fájlban: `small x normal`, nincs új teszt, a kapu átenged; (c) egysoros változás egy kritikus fájl horgonyán, teszt nélkül: a kapu megáll, kiírja a `new-test`, `edge-cases` és `revert-proof` hiányát és a pontos parancsot; teszttel és igazolással: átenged; (d) új, kockázatmentes képernyő: `large x normal`, a mátrix és az élő próba hiányzik, egy adósságtétel írható; (e) kritikus változásnál az adósság elutasított; (f) `close` olyan teszttel, amely a régi kódon is zöld: elutasított; olyannal, amely ott elbukik és az újon zöld: lezárva, a célfájl változatlanul visszaállt; (g) a `close` közben megszakított folyamat: a következő futás visszaállít; (h) összeolvasztó commit: a kapu kihagy; (i) részleges commit (`git commit -o`) valódi hookkal: a teszt parancs nem lát `GIT_*` helyi változót.
- `claude --plugin-dir ./plugins/agentic-code` alatt a `security-check` megjelenik, a `quality-gate` és a `design-review` az új szakaszokkal; egy kritikus változáson a `quality-gate` a `security-check`-re hivatkozik.
- A `check.sh` tesztje és a `shellcheck`-szerű átnézés a bash 3.2-re (`bash --version`; ahol nincs 3.2, a bash 3.2-ben nem létező szerkezetek, például asszociatív tömb, `${var,,}`, `mapfile`, kézi átnézése).
- Adatvédelmi ellenőrzés: **privacy: no change** (a szkriptek csak a repóba és a git-könyvtárba írnak, hálózatot nem hívnak, személyes adatot nem gyűjtenek).
- Átnézés a spec ellen (friss, csak olvasó al-ügynök): minden feltétel megvan, a szélső esetek tesztelve, a `Nincs benne` listához nem nyúltunk, és a repóban nincs projekt-specifikus név.

## Döntések (Gyula, 2026-10-28)
- A tesztszint: **szabály és opcionális szkriptek** (a `quality-gate` szabályként is használható; a szkriptet a `project-setup` kérésre teszi be).
- A tesztadósság: **a repóban, tételenként egy fájl** (`docs/test-debt/`), a commit része.
- A kapu: **alapból megállít**; két kiadás: **0.4.1** (két javítás) és **0.5.0** (a többi).

## Nyitott
- A küszöbök (50 és 300 sor, 2 terület, 5 tétel, 14 nap) egy másik projekt 60 napjának 153 commitjából származó első becslések; az első valódi projekten mérni és igazítani kell. A mérés a `improve-workflow` „Measure a change” szakasza szerint megy.
- Az elsődleges forrásokat (TDAD, ImpossibleBench) a README idézése előtt el kell olvasni; addig csak a másodlagos összefoglalókat ismerjük (`research/workflow-learnings-research.md`).
