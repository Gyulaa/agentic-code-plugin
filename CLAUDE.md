# agentic-code-plugin

Az `agentic-code` Claude Code plugin forrása: skillek, a guard hook és a `project-setup` sablonjai. Gyula saját projektjeihez készül, és később nyilvános lehet; GitHub-repó: `Gyulaa/agentic-code-plugin` (most privát).

Kezdés: `STATE.md` (hol tartunk, egy oldal). A plugin leírása a `README.md`-ben; ez a fájl csak az állandó korlátokat tartja.

## Parancsok
```bash
scripts/check.sh                             # szintaxis, JSON, plugin validate, tesztek; "OK" = zöld (a pre-commit hook --staged móddal futtatja)
claude --plugin-dir ./plugins/agentic-code   # a helyi, még ki nem adott változat kipróbálása
git config core.hooksPath .githooks          # klónonként egyszer
```

## Amit a kódból nem látni
- A futó skillek a telepített példányból jönnek (`~/.claude/plugins/cache/agentic-code-plugin/`), nem ebből a mappából. Egy itteni változás csak push és `/plugin marketplace update agentic-code-plugin` után él; előtte `--plugin-dir`-rel kell kipróbálni. A telepített viselkedésből ne következtess az itteni kódra, és fordítva.
- Csak a `plugins/agentic-code/` kerül a felhasználókhoz. A gyökérben lévő `CLAUDE.md`, `STATE.md`, `docs/`, `scripts/`, `.githooks/` és `tests/` csak a fejlesztést szolgálja.
- A repó minden commitolt fájlja nyilvánosan is vállalható: nincs benne titok, személyes adat, helyi útvonal, más projekt belső részlete, és harmadik fél szövege csak a licence szerint. A kutatási jegyzetek és a forrásanyagok kivonatai a `research/` mappába kerülnek, amely gitignore-olt és csak helyben él.
- A plugin általános: a skillekbe és a sablonokba nem kerül egyetlen projekt saját neve, útvonala vagy szabálya sem.
- A skillek, a sablonok és a README angolul íródnak; ez a fájl és a jegyzetek (`STATE.md`, `docs/`, `research/`) magyarul.
- Minden fusson a macOS-es bash 3.2-vel és a python3 standard könyvtárával, függőség nélkül.

## Kiadás
Új verzió: a `plugins/agentic-code/.claude-plugin/plugin.json` `version` mezője, és egy dátumozott sor a README „What's new” szakaszába (legújabb felül). A guard hook vagy a `check.sh` / githook sablon változásához teszt kell a `tests/` alá.

## Megszeghetetlen
- Push és PR csak külön, kifejezett engedéllyel.

## Hol mi van
| Kell | Olvasd |
|---|---|
| Hol tartunk, mi a következő | `STATE.md` |
| Miért olyan, amilyen | `docs/decisions.md` |
| Mit tud a plugin, telepítés, fejlesztői parancsok | `README.md` |
| Kutatás egy készülő skillhez (helyi, nincs a gitben) | `research/` |

## Munkamód
Tömörítéskor tartsd meg a módosított fájlok listáját, a check parancsot és a nyitott döntéseket.
Az agentic-code skillek érvényesek: `working-mode` mindig, `quality-gate` és `match-the-codebase` kódváltoztatás előtt (a skillek szövege itt kódnak számít), `spec` az egy mondatnál nagyobb változáshoz, `git-workflow` ág, commit vagy PR előtt. Munka eleje `/agentic-code:resume-work`, vége `/agentic-code:save-work`.
