#!/usr/bin/env python3
"""How wide and how dangerous is this change, and what does that ask of the author.

Usage:
  scripts/risk_level.py level [--staged | --base REF] [--json] [--map FILE]
  scripts/risk_level.py gate [--json] [--map FILE]
  scripts/risk_level.py done <todo> "<what you did, what came out>"
  scripts/risk_level.py map-coverage [--json] [--map FILE]

`level` classifies the change (the working tree against HEAD plus untracked files; --staged: the
index; --base REF: the working tree against REF) from the diff, never from a description of it.
The rules live in scripts/risk-map.json. Exit codes: 0 done, 2 `map-coverage` found files the map
does not know or `gate` stopped the commit, 1 bad usage or a bad map.

`gate` (the pre-commit hook runs it) judges the staged change. For every todo there are three ways
out and no fourth: the diff proves it, `done` attests it for this one commit (it expires when HEAD
moves), or it is written down as test debt, which the level allows below critical depth.

Width (how big): small, medium or large. Depth (how dangerous): normal, sensitive or critical.
The work asked is the union of both. Python 3.8+, standard library only.
"""

import argparse
import ast
import datetime
import json
import os
import re
import subprocess
import sys

MAP_FILE = "scripts/risk-map.json"
DEFAULT_THRESHOLDS = {"small_lines": 50, "medium_lines": 300, "small_areas": 1, "medium_areas": 2}
RANK = {"skip": 0, "test": 1, "normal": 2, "sensitive": 3, "unknown": 3, "critical": 4}
DEPTH_OF = {"skip": None, "test": None, "normal": "normal", "sensitive": "sensitive",
            "unknown": "sensitive", "critical": "critical"}
DEPTH_RANK = {"normal": 0, "sensitive": 1, "critical": 2}
MAX_REASONS = 8
TODO_NAMES = ("new-test", "edge-cases", "revert-proof", "adversarial-review", "contract-test", "server-twin",
              "security-check", "full-write", "ui-matrix", "live-try", "pay-debt")
DEBTABLE = ("new-test", "ui-matrix", "live-try", "full-write")  # a missing test can be debt, below critical
DEBT_DIR = "docs/test-debt"
DEFAULT_CEILING = {"open": 5, "days": 14}
TEXT_LIMIT = 2 * 1024 * 1024


class Usage(Exception):
    pass


def git(*args, **kw):
    p = subprocess.run(["git", "-c", "core.quotepath=off", *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", input=kw.get("input"))
    return p.returncode, p.stdout, p.stderr


def repo_root():
    code, out, _ = git("rev-parse", "--show-toplevel")
    if code != 0:
        raise Usage("not inside a git repository")
    return out.strip()


def unquote(name):
    name = name.rstrip("\t")
    if len(name) >= 2 and name[0] == '"' and name[-1] == '"':
        try:
            return ast.literal_eval(name)
        except (ValueError, SyntaxError):
            return name[1:-1]
    return name


# ---- globs and the map -------------------------------------------------------------------------

_glob_cache = {}


def glob_regex(glob):
    """`*` stays inside a directory, `**` crosses them; a glob without `/` matches at any depth."""
    if glob in _glob_cache:
        return _glob_cache[glob]
    anywhere = "/" not in glob
    g = glob.lstrip("/")
    out, i = [], 0
    while i < len(g):
        if g.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif g.startswith("**", i):
            out.append(".*")
            i += 2
        elif g[i] == "*":
            out.append("[^/]*")
            i += 1
        elif g[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(g[i]))
            i += 1
    rx = re.compile("^" + ("(?:.*/)?" if anywhere else "") + "".join(out) + "$")
    _glob_cache[glob] = rx
    return rx


def matches(globs, path):
    return any(glob_regex(g).match(path) for g in globs)


def _regex(value, where):
    try:
        return re.compile(value)
    except re.error as e:
        raise Usage("%s: %s is not a valid regular expression (%s)" % (MAP_FILE, where, e))


def _str_list(data, key):
    value = data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise Usage("%s: %s must be a list of glob strings" % (MAP_FILE, key))
    return value


def load_map(root, override=None):
    """Returns the normalised map, or None when the project has none."""
    path = override or os.path.join(root, MAP_FILE)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        data = json.loads(raw)
    except (OSError, ValueError) as e:
        raise Usage("%s: cannot read (%s)" % (MAP_FILE, e))
    if "{{" in raw:
        raise Usage("%s is not configured (a {{placeholder}} is left)" % MAP_FILE)
    if not isinstance(data, dict):
        raise Usage("%s: must be a JSON object" % MAP_FILE)
    mp = {"skip": _str_list(data, "skip"), "test": _str_list(data, "test"),
          "normal": _str_list(data, "normal"), "ui": _str_list(data, "ui"),
          "critical": [], "sensitive": []}
    for entry in data.get("critical", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("glob"), str):
            raise Usage("%s: every critical entry needs a glob" % MAP_FILE)
        mp["critical"].append({
            "glob": entry["glob"], "why": entry.get("why") or "critical path",
            "anchor": _regex(entry["anchor"], "anchor") if entry.get("anchor") else None,
            "server_twin": entry.get("server_twin") or "", "contract": bool(entry.get("contract"))})
    for entry in data.get("sensitive", []):
        if isinstance(entry, str):
            entry = {"glob": entry}
        if not isinstance(entry, dict) or not (entry.get("glob") or entry.get("content")):
            raise Usage("%s: every sensitive entry needs a glob or a content pattern" % MAP_FILE)
        mp["sensitive"].append({
            "glob": entry.get("glob") or "", "why": entry.get("why") or "sensitive",
            "content": _regex(entry["content"], "content") if entry.get("content") else None})
    areas = data.get("areas") or {}
    named = [{"glob": a["glob"], "name": a["name"]} for a in areas.get("named", [])
             if isinstance(a, dict) and a.get("glob") and a.get("name")]
    depth = areas.get("depth", 2)
    mp["areas"] = {"depth": depth if isinstance(depth, int) and depth >= 1 else 2, "named": named}
    th = dict(DEFAULT_THRESHOLDS)
    for key, value in (data.get("thresholds") or {}).items():
        if key in th and isinstance(value, int) and value >= 0:
            th[key] = value
    mp["thresholds"] = th
    marker = data.get("ui_matrix_marker")
    mp["ui_matrix_marker"] = _regex(marker, "ui_matrix_marker") if isinstance(marker, str) and marker else None
    if data.get("gate", "strict") not in ("strict", "warn"):
        raise Usage("%s: gate must be \"strict\" or \"warn\"" % MAP_FILE)
    ceiling = dict(DEFAULT_CEILING)
    for key, value in (data.get("debt_ceiling") or {}).items():
        if key in ceiling and isinstance(value, int) and value >= 1:
            ceiling[key] = value
    mp["debt_ceiling"] = ceiling
    for key in ("gate", "test_one"):
        if key in data:
            mp[key] = data[key]
    return mp


def area_of(path, mp):
    areas = mp["areas"] if mp else {"depth": 2, "named": []}
    for entry in areas["named"]:
        if glob_regex(entry["glob"]).match(path):
            return entry["name"]
    return "/".join(path.split("/")[:-1][:areas["depth"]]) or "(root)"


# ---- the diff ----------------------------------------------------------------------------------

def parse_patch(text):
    files, cur, in_hunk = [], None, False
    for line in text.split("\n"):
        if line.startswith("diff --git "):
            cur = {"path": None, "old_path": None, "status": "M", "binary": False, "untracked": False,
                   "added": [], "removed": [], "contexts": [], "_a": None, "_b": None, "_hdr": line[len("diff --git "):]}
            files.append(cur)
            in_hunk = False
            continue
        if cur is None:
            continue
        if in_hunk and not line.startswith("@@"):
            if line.startswith("+"):
                cur["added"].append(line[1:])
            elif line.startswith("-"):
                cur["removed"].append(line[1:])
            continue
        if line.startswith("@@"):
            in_hunk = True
            context = line.split("@@")[2].strip() if line.count("@@") >= 2 else ""
            if context:
                cur["contexts"].append(context)
        elif line.startswith("new file mode"):
            cur["status"] = "A"
        elif line.startswith("deleted file mode"):
            cur["status"] = "D"
        elif line.startswith("rename from "):
            cur["status"], cur["old_path"] = "R", unquote(line[len("rename from "):])
        elif line.startswith("rename to "):
            cur["path"] = unquote(line[len("rename to "):])
        elif line.startswith("Binary files "):
            cur["binary"] = True
        elif line.startswith("--- "):
            cur["_a"] = unquote(line[4:])
        elif line.startswith("+++ "):
            cur["_b"] = unquote(line[4:])
    for rec in files:
        a, b = rec.pop("_a"), rec.pop("_b")
        hdr = rec.pop("_hdr")
        if rec["path"] is None:
            if b and b != "/dev/null":
                rec["path"] = b[2:]
            elif a and a != "/dev/null":
                rec["path"] = a[2:]
            else:
                n = (len(hdr) - 5) // 2  # "a/X b/X"
                rec["path"] = unquote(hdr[2:2 + n])
        if rec["status"] == "R" and rec["old_path"] == rec["path"]:
            rec["status"] = "M"
    return files


def untracked_files(paths):
    out = []
    for path in paths:
        rec = {"path": path, "old_path": None, "status": "A", "binary": False, "untracked": True,
               "added": [], "removed": [], "contexts": []}
        try:
            with open(path, "rb") as f:
                data = f.read(TEXT_LIMIT)
        except OSError:
            data = b""
        if b"\x00" in data[:8000]:
            rec["binary"] = True
        else:
            rec["added"] = data.decode("utf-8", errors="replace").split("\n")
            if rec["added"][-1] == "":
                rec["added"].pop()
        out.append(rec)
    return out


def head_ref():
    code, _, _ = git("rev-parse", "--verify", "--quiet", "HEAD^{commit}")
    if code == 0:
        return "HEAD"
    return git("hash-object", "-t", "tree", "--stdin", input="")[1].strip()


def gather(mode, base):
    """mode: "working", "staged" or "base". Returns the list of changed-file records."""
    args = ["diff", "-M", "-U0", "--no-color", "--no-ext-diff", "--no-textconv",
            "--src-prefix=a/", "--dst-prefix=b/"]
    if mode == "staged":
        args.append("--cached")
    elif mode == "base":
        if git("rev-parse", "--verify", "--quiet", base + "^{commit}")[0] != 0:
            raise Usage("base does not exist: %s" % base)
        args.append(base)
    else:
        args.append(head_ref())
    code, out, err = git(*args)
    if code != 0:
        raise Usage("git diff failed: %s" % err.strip())
    files = parse_patch(out)
    if mode != "staged":
        code, out, _ = git("ls-files", "--others", "--exclude-standard", "-z")
        files += untracked_files([p for p in out.split("\0") if p])
    return files


def current_branch():
    code, out, _ = git("symbolic-ref", "--short", "-q", "HEAD")
    return out.strip() if code == 0 else ""


# ---- classification ----------------------------------------------------------------------------

def classify_path(path, changed, mp, content=True):
    """First match wins: skip, critical, test, sensitive, normal; else unknown.
    `content` False: only the path is known (map-coverage), content rules cannot decide."""
    if matches(mp["skip"], path):
        return "skip", "", None
    for entry in mp["critical"]:
        if glob_regex(entry["glob"]).match(path):
            if entry["anchor"] is None or not content or any(entry["anchor"].search(l) for l in changed):
                return "critical", entry["why"], entry
    if matches(mp["test"], path):
        return "test", "", None
    for entry in mp["sensitive"]:
        if entry["glob"] and not glob_regex(entry["glob"]).match(path):
            continue
        if entry["content"] is not None and not entry["glob"] and not content:
            continue
        if entry["content"] is not None and content and not any(entry["content"].search(l) for l in changed):
            continue
        return "sensitive", entry["why"], None
    if matches(mp["normal"], path):
        return "normal", "", None
    return "unknown", "not in the risk map; treated as sensitive", None


def classify_file(rec, mp):
    changed = rec["added"] + rec["removed"]
    best = classify_path(rec["path"], changed, mp)
    if rec["old_path"]:
        old = classify_path(rec["old_path"], changed, mp)
        if RANK[old[0]] > RANK[best[0]]:
            best = old
    return best


def age_days(created):
    try:
        return max(0, (datetime.date.today() - datetime.date.fromisoformat(created)).days)
    except (TypeError, ValueError):
        return 0


def open_debt(files, areas):
    """Open test-debt items of the changed areas; items this very change adds do not count."""
    new = set(rec["path"] for rec in files if rec["status"] == "A")
    found = []
    try:
        names = sorted(os.listdir(DEBT_DIR))
    except OSError:
        return found
    for name in names:
        if not name.endswith(".json") or DEBT_DIR + "/" + name in new:
            continue
        try:
            with open(os.path.join(DEBT_DIR, name), encoding="utf-8") as f:
                item = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(item, dict) and item.get("status") == "open" and item.get("area") in areas:
            found.append({"id": item.get("id") or name[:-5], "area": item["area"], "todo": item.get("todo", ""),
                          "age_days": age_days(item.get("created")), "then": item.get("then", "")})
    return found


def code_lines(rec):
    return sum(1 for l in rec["added"] + rec["removed"] if l.strip())


def analyse(files, mp, branch):
    thresholds = (mp or {"thresholds": DEFAULT_THRESHOLDS})["thresholds"]
    result = {"map": mp is not None, "files": [], "warnings": [], "reasons": [], "todos": []}
    lines, areas, twins, contract, new_ui = 0, [], [], False, []
    test_net, test_deleted, has_sensitive = 0, False, False
    for rec in sorted(files, key=lambda r: r["path"]):
        if mp is None:
            cls, why, entry = "unmapped", "", None
        else:
            cls, why, entry = classify_file(rec, mp)
        n = code_lines(rec)
        result["files"].append({"path": rec["path"], "old_path": rec["old_path"], "status": rec["status"],
                                "class": cls, "lines": n, "why": why, "added": len(rec["added"]),
                                "removed": len(rec["removed"])})
        if cls == "test":
            test_net += sum(1 for l in rec["added"] if l.strip()) - sum(1 for l in rec["removed"] if l.strip())
            test_deleted = test_deleted or rec["status"] == "D"
        if cls in ("skip", "test"):
            continue
        lines += n
        area = area_of(rec["path"], mp)
        if area not in areas:
            areas.append(area)
        if mp is not None and rec["status"] == "A" and matches(mp["ui"], rec["path"]):
            new_ui.append(rec["path"])
        if cls == "critical":
            result["reasons"].append("critical: %s (%s)" % (rec["path"], why))
            if entry["server_twin"]:
                twins.append("%s: %s" % (rec["path"], entry["server_twin"]))
            contract = contract or entry["contract"]
        elif cls == "sensitive":
            result["reasons"].append("sensitive: %s (%s)" % (rec["path"], why))
            has_sensitive = True
        elif cls == "unknown":
            result["warnings"].append("unknown: %s (%s)" % (rec["path"], why))
            has_sensitive = True
    areas.sort()
    result["lines"], result["areas"] = lines, areas
    if test_deleted or test_net < 0:
        result["warnings"].append("you deleted or weakened a test: a failing test is a requirement, "
                                  "not an obstacle")

    counted = [f for f in result["files"] if f["class"] not in ("skip", "test")]
    if not result["files"] or (mp is not None and not counted and
                               all(f["class"] == "skip" for f in result["files"])):
        result["width"] = result["depth"] = "none"
        result["note"] = "no changes" if not result["files"] else "only skip-class files"
        return result

    depth = None
    if mp is not None:
        for f in counted:
            d = DEPTH_OF[f["class"]]
            if d and (depth is None or DEPTH_RANK[d] > DEPTH_RANK[depth]):
                depth = d
        depth = depth or "normal"
    result["depth"] = depth or "unknown"
    if mp is None:
        result["warnings"].append("no risk map (%s): width only, nothing can be classified" % MAP_FILE)

    if branch.startswith("release/"):
        width = "large"
        result["reasons"].append("large: release branch %s" % branch)
    elif new_ui:
        width = "large"
        result["reasons"].append("large: new surface %s" % new_ui[0])
    elif lines <= thresholds["small_lines"] and len(areas) <= thresholds["small_areas"]:
        width = "small"
    elif lines <= thresholds["medium_lines"] and len(areas) <= thresholds["medium_areas"]:
        width = "medium"
    else:
        width = "large"
    debt = open_debt(files, areas) if mp is not None else []
    result["debt"] = debt
    if mp is not None:
        ceiling = mp["debt_ceiling"]
        for area in areas:
            mine = [d for d in debt if d["area"] == area]
            oldest = max([d["age_days"] for d in mine] or [0])
            if len(mine) >= ceiling["open"] or (mine and oldest >= ceiling["days"]):
                width = "large"
                result["reasons"].append("large: area %s has %d open test-debt items (oldest %d days; the ceiling "
                                         "is %d items or %d days)" % (area, len(mine), oldest, ceiling["open"],
                                                                      ceiling["days"]))
    result["width"] = width
    result["todos"] = todos_for(width, depth, mp, result["files"], twins, contract, has_sensitive, debt)
    return result


def todos_for(width, depth, mp, files, twins, contract, has_sensitive, debt):
    todos = []

    def add(name, note=""):
        todos.append({"name": name, "note": note})

    if depth == "critical":
        add("new-test")
        add("edge-cases", "unit test of the edges: 0, negative, midnight, rounding, empty, very large")
        add("revert-proof", "the new test must fail on the old code")
        add("adversarial-review", "fresh read-only reviewer sees the diff and the criteria, not your reasoning")
        if contract:
            add("contract-test", "rule or contract test for the changed rule")
        for twin in twins:
            add("server-twin", twin)
        add("security-check", "run the security-check skill")
    if has_sensitive:
        add("full-write", "a write must list every field; a skipped field can erase a stored value")
    if width == "medium" and not any(t["name"] == "new-test" for t in todos):
        add("new-test", "a new or changed test for the changed behaviour")
    if width == "large":
        if mp is not None and mp["ui"] and any(matches(mp["ui"], f["path"]) for f in files
                                               if f["class"] not in ("skip", "test")):
            add("ui-matrix", "states, small screen, large text, both themes")
        add("live-try", "try it once, live")
        if debt:
            add("pay-debt", "close an open test-debt item of this area with test_debt.py close")
    return todos


# ---- output ------------------------------------------------------------------------------------

def render(result):
    out = []
    if result["width"] == "none":
        out.append("LEVEL: none (%s)" % result["note"])
    else:
        areas = result["areas"]
        where = ("; area: %s" % areas[0]) if len(areas) == 1 else ("; areas: %s" % ", ".join(areas)) if areas else ""
        if result["depth"] == "unknown":
            out.append("LEVEL: %s (%d lines%s; width only, no risk map)" % (result["width"], result["lines"], where))
        else:
            out.append("LEVEL: %s x %s (%d lines%s)" % (result["width"], result["depth"], result["lines"], where))
    for label, items in (("because", result["reasons"]), ("warn", result["warnings"])):
        for item in items[:MAX_REASONS]:
            out.append("%s: %s" % (label, item))
        if len(items) > MAX_REASONS:
            out.append("%s: ... and %d more" % (label, len(items) - MAX_REASONS))
    if result["width"] == "large":
        for item in result.get("debt", [])[:3]:
            out.append("debt: %s (%s, %dd) %s" % (item["id"], item["area"], item["age_days"], item["then"][:60]))
        if len(result.get("debt", [])) > 3:
            out.append("debt: ... and %d more (test_debt.py list)" % (len(result["debt"]) - 3))
    for todo in result["todos"]:
        if "status" in todo:
            detail = (" (%s)" % todo["detail"]) if todo.get("detail") else ""
            note = (" - " + todo["note"]) if todo["status"] == "MISSING" and todo["note"] else ""
            out.append("todo: %s: %s%s%s" % (todo["name"], todo["status"], detail, note))
        else:
            out.append("todo: %s%s" % (todo["name"], " - " + todo["note"] if todo["note"] else ""))
    return "\n".join(out)


# ---- commands ----------------------------------------------------------------------------------

def cmd_level(args):
    root = repo_root()
    os.chdir(root)
    mp = load_map(root, args.map)
    mode = "staged" if args.staged else "base" if args.base else "working"
    result = analyse(gather(mode, args.base), mp, current_branch())
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render(result))
    return 0


def git_path(root, name):
    path = git("rev-parse", "--git-path", name)[1].strip()
    return path if os.path.isabs(path) else os.path.join(root, path)


def head_id():
    code, out, _ = git("rev-parse", "--verify", "--quiet", "HEAD")
    return out.strip() if code == 0 else "root"


def load_attested(root):
    """What was attested for the commit that is about to be made; empty once HEAD has moved."""
    try:
        with open(git_path(root, "agentic/risk-attest.json"), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict) or data.get("head") != head_id() or not isinstance(data.get("items"), dict):
        return {}
    return data["items"]


def cmd_done(args):
    root = repo_root()
    if args.todo not in TODO_NAMES:
        raise Usage("unknown todo: %s (known: %s)" % (args.todo, ", ".join(TODO_NAMES)))
    if len(args.text.strip()) < 12:
        raise Usage("say what you did and what came out (at least 12 characters)")
    items = load_attested(root)
    items[args.todo] = args.text.strip()
    path = git_path(root, "agentic/risk-attest.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"head": head_id(), "items": items}, f)
    os.replace(tmp, path)
    print("recorded: %s, for the next commit only" % args.todo)
    return 0


def debt_todos(files):
    """The todos that the change itself writes down as new test debt."""
    found = set()
    for rec in files:
        if rec["status"] == "A" and rec["path"].startswith(DEBT_DIR + "/") and rec["path"].endswith(".json"):
            try:
                item = json.loads("\n".join(rec["added"]))
            except ValueError:
                continue
            if isinstance(item, dict) and isinstance(item.get("todo"), str):
                found.add(item["todo"])
    return found


def closes_debt(files):
    """The first debt item that the staged change turns from open to closed."""
    for rec in files:
        if rec["status"] == "M" and rec["path"].startswith(DEBT_DIR + "/") and rec["path"].endswith(".json"):
            try:
                item = json.loads(git("show", ":" + rec["path"])[1])
            except ValueError:
                continue
            if isinstance(item, dict) and item.get("status") == "closed":
                return rec["path"]
    return None


def todo_status(todo, result, files, mp, attested, debts):
    name = todo["name"]
    if name == "pay-debt" and closes_debt(files):
        return "done by diff", closes_debt(files)
    if name == "new-test":
        tests = [f["path"] for f in result["files"] if f["class"] == "test" and f["status"] != "D" and f["added"]]
        if tests:
            return "done by diff", tests[0]
    if name == "ui-matrix" and mp["ui_matrix_marker"] is not None:
        if any(mp["ui_matrix_marker"].search(l) for rec in files for l in rec["added"]):
            return "done by diff", "marker in the diff"
    if name in attested:
        return "attested", ""
    if name in DEBTABLE and result["depth"] != "critical" and name in debts:
        return "debt", ""
    return "MISSING", ""


def cmd_gate(args):
    root = repo_root()
    os.chdir(root)
    mp = load_map(root, args.map)

    def finish(result, status, message, code):
        result["gate"] = status
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if "files" in result and result["width"] != "none":
                print(render(result))
            print("gate: " + message)
        return code

    if os.path.exists(git_path(root, "MERGE_HEAD")):
        return finish({"width": "none"}, "skipped", "merge commit, skipped (run the check after a merge)", 0)
    files = gather("staged", None)
    result = analyse(files, mp, current_branch())
    if result["width"] == "none":
        why = "nothing staged" if not files else "only skip-class files"
        return finish(result, "skipped", why + ", skipped", 0)
    if mp is None:
        return finish(result, "no-map", "no risk map, so only the width is counted and nothing is stopped", 0)

    attested, debts = load_attested(root), debt_todos(files)
    missing = []
    for todo in result["todos"]:
        todo["status"], todo["detail"] = todo_status(todo, result, files, mp, attested, debts)
        if todo["status"] == "attested":
            todo["detail"] = attested[todo["name"]][:50]
        if todo["status"] == "MISSING":
            missing.append(todo)
    mode = os.environ.get("RISK_GATE") or mp.get("gate", "strict")
    if mode not in ("strict", "warn"):
        raise Usage("RISK_GATE must be strict or warn")
    if not missing:
        return finish(result, "pass", "OK", 0)
    result["missing"] = [t["name"] for t in missing]
    if mode == "warn":
        return finish(result, "warn", "warning only (RISK_GATE=warn), %d missing" % len(missing), 0)

    if args.json:
        return finish(result, "stopped", "", 2)
    print(render(result))
    print("gate: STOPPED, %d missing. Do the work, then record it (never --no-verify):" % len(missing))
    for todo in missing[:6]:
        print('  scripts/risk_level.py done %s "<what you did, what came out>"' % todo["name"])
    if len(missing) > 6:
        print("  ... and %d more, same form" % (len(missing) - 6))
    debtable = [t["name"] for t in missing if t["name"] in DEBTABLE]
    if debtable and result["depth"] != "critical":
        print("  or, for a missing test, write it down as debt: scripts/test_debt.py add %s "
              "--given ... --when ... --then ..." % debtable[0])
    result["gate"] = "stopped"
    return 2


def cmd_map_coverage(args):
    root = repo_root()
    os.chdir(root)
    mp = load_map(root, args.map)
    if mp is None:
        raise Usage("no risk map (%s)" % MAP_FILE)
    code, out, _ = git("ls-files", "-z")
    unknown = [p for p in out.split("\0") if p and classify_path(p, [], mp, content=False)[0] == "unknown"]
    if args.json:
        print(json.dumps({"unknown": unknown}))
    else:
        for path in unknown[:50]:
            print(path)
        if len(unknown) > 50:
            print("... and %d more" % (len(unknown) - 50))
        print("%d files the map does not know" % len(unknown))
    return 2 if unknown else 0


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Usage(message)


def main(argv):
    ap = Parser(description="Risk level of a change.")
    sub = ap.add_subparsers(dest="command")
    sub.required = True
    lv = sub.add_parser("level", help="classify the current change")
    lv.add_argument("--staged", action="store_true", help="the index instead of the working tree")
    lv.add_argument("--base", help="compare the working tree with this ref")
    lv.add_argument("--json", action="store_true")
    lv.add_argument("--map", help="map file (default: %s)" % MAP_FILE)
    gt = sub.add_parser("gate", help="judge the staged change (the pre-commit hook runs this)")
    gt.add_argument("--json", action="store_true")
    gt.add_argument("--map", help="map file (default: %s)" % MAP_FILE)
    dn = sub.add_parser("done", help="attest a todo for the next commit")
    dn.add_argument("todo")
    dn.add_argument("text", help="what you did and what came out")
    cv = sub.add_parser("map-coverage", help="list tracked files the map does not know")
    cv.add_argument("--json", action="store_true")
    cv.add_argument("--map", help="map file (default: %s)" % MAP_FILE)
    try:
        args = ap.parse_args(argv)
        return {"level": cmd_level, "gate": cmd_gate, "done": cmd_done,
                "map-coverage": cmd_map_coverage}[args.command](args)
    except Usage as e:
        print("risk_level.py: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
