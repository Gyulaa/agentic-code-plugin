#!/usr/bin/env python3
"""Test debt: a missing test written down so that it is not lost, and closed only with proof.

Usage:
  scripts/test_debt.py add <todo> --given G --when W --then T [--target FILE] [--test-file F] [--test-name N]
  scripts/test_debt.py list [--area A] [--json]
  scripts/test_debt.py show <id>
  scripts/test_debt.py close <id> [--parent REF] [--attested "what you did, what came out"]

Each item is one file, docs/test-debt/TD-<date>-<4 hex>.json, committed with the change it belongs to
(a discarded branch leaves no orphan). The machine fills in what the diff knows; you write only the
claim (given / when / then), concrete enough that someone who never saw this session can write the test.

Closing needs proof: the named test exists, mentions the target, passes, and FAILS when the target file
is put back to its state before the change (a test that is green on the old code does not protect
the change). A live try has no test: `close <id> --attested "..."`.

Exit codes: 0 done, 2 refused (with the reason), 1 bad usage. Needs scripts/risk_level.py next to it.
Python 3.8+, standard library only.
"""

import datetime
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import risk_level as rl  # noqa: E402

ID_RE = re.compile(r"^TD-\d{8}-[0-9a-f]{4}$")
TEST_LINE = re.compile(r"^\s*(def test\w*|test\(|it\(|void main|func Test\w*|@Test|fn test\w*)")
VAGUE = re.compile(r"^(it |that |this |the result |everything )?(should |must |will |needs to |has to )?(just )?"
                   r"(work|works|working|be correct|be right|be ok|be okay|be fine|is correct|is right|is ok|"
                   r"is fine|behave|behaves)( correctly| properly| well| as expected)?\W*$", re.I)
MIN_CLAIM = 12
RUN_TIMEOUT = 900
LOCK = "agentic/revert.lock"
FRESH_LOCK_SECONDS = 10


class Refused(Exception):
    pass


# ---- the items ---------------------------------------------------------------------------------

def item_path(item_id):
    if not ID_RE.match(item_id):
        raise rl.Usage("not a debt id: %s" % item_id)
    return os.path.join(rl.DEBT_DIR, item_id + ".json")


def load_item(item_id):
    path = item_path(item_id)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), path
    except (OSError, ValueError) as e:
        raise rl.Usage("cannot read %s (%s)" % (path, e))


def write_item(path, item, exclusive=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "x" if exclusive else "w", encoding="utf-8") as f:
        json.dump(item, f, indent=2, ensure_ascii=False)
        f.write("\n")


def open_items():
    items = []
    try:
        names = sorted(os.listdir(rl.DEBT_DIR))
    except OSError:
        return items
    for name in names:
        if name.endswith(".json"):
            try:
                with open(os.path.join(rl.DEBT_DIR, name), encoding="utf-8") as f:
                    item = json.load(f)
            except (OSError, ValueError):
                continue
            if isinstance(item, dict) and item.get("status") == "open":
                items.append(item)
    return sorted(items, key=lambda i: (i.get("created", ""), i.get("id", "")))


# ---- add ---------------------------------------------------------------------------------------

def check_claim(given, when, then):
    for label, text in (("given", given), ("when", when), ("then", then)):
        if len(text.strip()) < MIN_CLAIM:
            raise Refused("--%s is vague: say it in at least %d characters, with a concrete value" % (label, MIN_CLAIM))
    if VAGUE.match(then.strip()):
        raise Refused("--then is vague: \"works\" or \"is correct\" is not a result; name the value that is expected")
    if not re.search(r"""\d|['"`=]""", given + when + then):
        raise Refused("the claim is vague: name a concrete value (a number, a role, a state, a quoted text)")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:30].strip("_")


def fill(command, file, name):
    return command.replace("{file}", shlex.quote(file)).replace("{name}", shlex.quote(name))


def pick_target(files, result, wanted):
    classes = dict((f["path"], f["class"]) for f in result["files"])
    candidates = [r for r in files if r["status"] != "D" and not r["path"].startswith(rl.DEBT_DIR + "/")
                  and classes.get(r["path"]) not in ("skip", "test")]
    if wanted:
        found = [r for r in candidates if r["path"] == wanted]
        if not found:
            raise Refused("%s has no change to write debt for" % wanted)
        return found[0]
    if not candidates:
        raise Refused("no change to write debt for (nothing outside tests and docs differs from HEAD)")
    return max(candidates, key=lambda r: (rl.RANK.get(classes.get(r["path"]), 2), rl.code_lines(r)))


def anchor_of(rec):
    added = [l.strip() for l in rec["added"] if l.strip()]
    removed = [l.strip() for l in rec["removed"] if l.strip()]
    return max(added, key=len)[:120] if added else (removed[0][:120] if removed else "")


def change_diff(rec, parent):
    if rec["untracked"] or parent is None:
        return ["+" + l for l in rec["added"][:15]]
    out = rl.git("diff", "-U1", "--no-color", "--no-ext-diff", "--no-textconv", "HEAD", "--", rec["path"])[1]
    body = out.split("\n@@", 1)[1].split("\n")[1:] if "\n@@" in out else []
    return [l for l in body if l][:15]


def tracked_tests(mp):
    if mp is None:
        return []
    names = rl.git("ls-files", "-z", "--cached", "--others", "--exclude-standard")[1].split("\0")
    return sorted(p for p in names if p and rl.matches(mp["test"], p))


def read_text(path, limit=1024 * 1024):
    try:
        with open(path, "rb") as f:
            return f.read(limit).decode("utf-8", errors="replace")
    except OSError:
        return ""


def mirror_path(target, mp):
    stem, ext = os.path.splitext(os.path.basename(target))
    roots = [g[:-3] for g in (mp["test"] if mp else []) if g.endswith("/**") and "*" not in g[:-3]]
    folders = target.split("/")[1:-1]
    if ext == ".dart":
        name = stem + "_test" + ext
    elif ext in (".js", ".jsx", ".ts", ".tsx", ".mjs"):
        name = stem + ".test" + ext
    else:
        name = "test_" + stem + ext
    return "/".join([roots[0] if roots else "tests"] + folders + [name])


def find_test_file(target, mp):
    stem = os.path.splitext(os.path.basename(target))[0]
    word = re.compile(r"\b%s\b" % re.escape(stem))
    for path in tracked_tests(mp):
        if word.search(read_text(path)):
            return path
    return mirror_path(target, mp)


def find_pattern(where_file, mp):
    tests = tracked_tests(mp)
    tests.sort(key=lambda p: -len(os.path.commonprefix([p, where_file])))
    for path in tests:
        for line in read_text(path).split("\n"):
            if TEST_LINE.match(line):
                return {"file": path, "line": line.strip()[:100]}
    return None


def cmd_add(args, root):
    if args.todo not in rl.TODO_NAMES:
        raise rl.Usage("unknown todo: %s" % args.todo)
    if args.todo not in rl.DEBTABLE:
        raise Refused("only a missing test can be written down as debt (%s); %s is done, not owed"
                      % (", ".join(rl.DEBTABLE), args.todo))
    check_claim(args.given, args.when, args.then)
    mp = rl.load_map(root)
    files = rl.gather("working", None)
    result = rl.analyse(files, mp, rl.current_branch())
    if result["depth"] == "critical":
        raise Refused("this change is critical (money, time, access, a data write path, a contract): the tests "
                      "are written now, not owed. Debt is never accepted at critical depth")
    rec = pick_target(files, result, args.target)
    code, parent, _ = rl.git("rev-parse", "--verify", "--quiet", "HEAD")
    parent = parent.strip() if code == 0 else None
    area = rl.area_of(rec["path"], mp)
    for _ in range(20):
        item_id = "TD-%s-%s" % (datetime.date.today().strftime("%Y%m%d"), os.urandom(2).hex())
        path = item_path(item_id)
        if not os.path.exists(path):
            break
    where_file = args.test_file or find_test_file(rec["path"], mp)
    where_name = args.test_name or "test_%s_%s" % (item_id.lower().replace("-", "_"), slug(args.then))
    item = {
        "id": item_id, "todo": args.todo, "status": "open", "created": datetime.date.today().isoformat(),
        "area": area, "given": args.given.strip(), "when": args.when.strip(), "then": args.then.strip(),
        "target": {"file": rec["path"], "symbol": args.symbol or (rec["contexts"][0] if rec["contexts"] else ""),
                   "anchor": anchor_of(rec)},
        "change": {"parent": parent, "diff": change_diff(rec, parent)},
        "where": {"file": where_file, "name": where_name},
        "pattern": find_pattern(where_file, mp),
        "run": fill(mp["test_one"], where_file, where_name) if mp and mp.get("test_one") else None,
    }
    write_item(path, item, exclusive=True)
    print("%s written: %s (area %s, %s)" % (item_id, path, area, args.todo))
    print("test to write: %s :: %s" % (where_file, where_name))
    print("commit it with the change: git add %s" % path)
    return 0


# ---- list and show -----------------------------------------------------------------------------

def cmd_list(args, root):
    items = [i for i in open_items() if not args.area or i.get("area") == args.area]
    if args.json:
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return 0
    if not items:
        print("no open test debt")
    for i in items:
        print("%s  %s  %s  %dd  %s" % (i["id"], i.get("area", ""), i.get("todo", ""), rl.age_days(i.get("created")),
                                       i.get("then", "")[:60]))
    return 0


def cmd_show(args, root):
    item, _ = load_item(args.id)
    print(json.dumps(item, indent=2, ensure_ascii=False))
    return 0


# ---- close -------------------------------------------------------------------------------------

def lock_file(root):
    return rl.git_path(root, LOCK)


def pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def restore(root, data):
    """Put the target file back from the backup and drop the lock; verifies the result."""
    target = os.path.join(root, data["file"])
    with open(data["backup"], "rb") as f:
        content = f.read()
    with open(target, "wb") as f:
        f.write(content)
    os.utime(target, ns=(data["atime_ns"], data["mtime_ns"]))
    with open(target, "rb") as f:
        if f.read() != content:
            raise rl.Usage("could not restore %s; the original is kept at %s" % (data["file"], data["backup"]))
    os.remove(data["backup"])
    os.remove(lock_file(root))


def recover(root):
    """A close that was killed leaves the old code in place; put the file back before anything else."""
    path = lock_file(root)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError:
        return
    except ValueError:
        if time.time() - os.path.getmtime(path) > FRESH_LOCK_SECONDS:
            os.remove(path)  # a lock that never got its content: nothing was touched yet
        return
    if pid_alive(data.get("pid")) and data.get("pid") != os.getpid():
        return
    if os.path.isfile(data.get("backup", "")):
        restore(root, data)
        print("recovered: restored %s from an interrupted close" % data["file"])
    else:
        os.remove(path)


def clean_env():
    env = dict(os.environ)
    for name in rl.git("rev-parse", "--local-env-vars")[1].split():
        env.pop(name, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_test(command, root):
    p = subprocess.run(command, shell=True, cwd=root, env=clean_env(), capture_output=True, text=True,
                       errors="replace", timeout=RUN_TIMEOUT)
    tail = "\n".join((p.stdout + p.stderr).strip().split("\n")[-8:])
    return p.returncode, tail


def git_bytes(*args):
    p = subprocess.run(["git", *args], capture_output=True)
    return p.returncode, p.stdout


def revert_proof(root, item, command, parent):
    """Put the target at its state before the change, run the test, put everything back."""
    rel = item["target"]["file"]
    target = os.path.join(root, rel)
    code, old = git_bytes("show", "%s:%s" % (parent, rel))
    if code != 0:
        raise Refused("cannot read %s at %s" % (rel, parent))
    st = os.stat(target)
    backup = rl.git_path(root, "agentic/revert-%d.bak" % os.getpid())
    os.makedirs(os.path.dirname(backup), exist_ok=True)
    with open(backup + ".tmp", "wb") as f:
        with open(target, "rb") as src:
            f.write(src.read())
        f.flush()
        os.fsync(f.fileno())
    os.replace(backup + ".tmp", backup)  # a complete backup exists before anything else does
    data = {"pid": os.getpid(), "file": rel, "backup": backup, "atime_ns": st.st_atime_ns,
            "mtime_ns": st.st_mtime_ns}
    try:
        fd = os.open(lock_file(root), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        os.remove(backup)
        raise Refused("another revert proof is running")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f)
        f.flush()
        os.fsync(f.fileno())
    previous = signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(143))
    try:
        with open(target, "wb") as f:
            f.write(old)
        # a different mtime, so a build cache keyed on it (Python's .pyc) cannot serve the new code
        os.utime(target, ns=(st.st_atime_ns, st.st_mtime_ns + 7 * 10 ** 9))
        return run_test(command, root)
    finally:
        restore(root, data)
        signal.signal(signal.SIGTERM, previous)


def finish(item, path, how, note):
    item["status"] = "closed"
    item["closed"] = {"date": datetime.date.today().isoformat(), "how": how, "note": note}
    write_item(path, item)
    print("closed %s (%s: %s). Commit the changed %s" % (item["id"], how, note, path))
    return 0


def cmd_close(args, root):
    item, path = load_item(args.id)
    if item.get("status") != "open":
        raise rl.Usage("%s is already closed" % item["id"])
    if args.attested is not None:
        if item["todo"] != "live-try":
            raise Refused("--attested closes a live try; a debt for a missing test is closed with the test")
        if len(args.attested.strip()) < MIN_CLAIM:
            raise rl.Usage("say what you did and what came out (at least %d characters)" % MIN_CLAIM)
        return finish(item, path, "attested", args.attested.strip())

    if os.path.exists(lock_file(root)):
        raise Refused("a revert proof is running or was interrupted (%s); wait for it, or remove the lock "
                      "if no such process exists" % lock_file(root))
    where, target = item["where"], item["target"]
    text = read_text(os.path.join(root, where["file"]))
    if not text:
        raise Refused("the test file %s does not exist or is empty; write %s there" % (where["file"], where["name"]))
    if where["name"] not in text:
        raise Refused("the test %s is not in %s" % (where["name"], where["file"]))
    stem = os.path.splitext(os.path.basename(target["file"]))[0]
    if not re.search(r"\b%s\b" % re.escape(stem), text):
        raise Refused("%s neither imports nor mentions %s, so it does not test the change" % (where["file"], stem))
    mp = rl.load_map(root)
    if mp and mp.get("test_one"):
        command = fill(mp["test_one"], where["file"], where["name"])
    elif item.get("run"):
        command = item["run"]
    else:
        raise Refused("no test_one command in scripts/risk-map.json, so the single test cannot be run")

    parent = args.parent or item["change"]["parent"]
    proof = None
    if parent is not None:
        if rl.git("rev-parse", "--verify", "--quiet", parent + "^{commit}")[0] != 0:
            raise Refused("the parent commit %s no longer exists; name the state before the change with "
                          "--parent <ref>" % parent)
        if rl.git("status", "--porcelain", "--", target["file"])[1].strip():
            raise Refused("%s has uncommitted changes; commit them first, the revert proof would overwrite them"
                          % target["file"])
        if rl.git("cat-file", "-e", "%s:%s" % (parent, target["file"]))[0] != 0:
            proof = "new file: no old state to restore, so no revert proof"
    code, tail = run_test(command, root)
    if code != 0:
        raise Refused("the test does not pass on the current code:\n%s" % tail)
    if parent is not None and proof is None:
        code, tail = revert_proof(root, item, command, parent)
        if code == 0:
            raise Refused("the test also passes on the old code (%s): it does not protect the change" % parent[:8])
        proof = "fails on the old code, passes on the new"
    return finish(item, path, "test", proof or "no earlier state; the test passes")


def main(argv):
    ap = rl.Parser(description="Test debt: write down a missing test, close it only with proof.")
    sub = ap.add_subparsers(dest="command")
    sub.required = True
    ad = sub.add_parser("add")
    ad.add_argument("todo")
    ad.add_argument("--given", required=True)
    ad.add_argument("--when", required=True)
    ad.add_argument("--then", required=True)
    ad.add_argument("--target", help="the changed file the debt is about (default: the most important one)")
    ad.add_argument("--symbol", help="the function or class (default: git's hunk context)")
    ad.add_argument("--test-file", help="where the test goes (default: an existing test of the target, else a mirror)")
    ad.add_argument("--test-name", help="the test's name (default: contains the item id)")
    ls = sub.add_parser("list")
    ls.add_argument("--area")
    ls.add_argument("--json", action="store_true")
    sh = sub.add_parser("show")
    sh.add_argument("id")
    cl = sub.add_parser("close")
    cl.add_argument("id")
    cl.add_argument("--parent", help="the commit before the change, if the recorded one is gone")
    cl.add_argument("--attested", help="close a live try: what you did and what came out")
    try:
        args = ap.parse_args(argv)
        root = rl.repo_root()
        os.chdir(root)
        recover(root)
        handler = {"add": cmd_add, "list": cmd_list, "show": cmd_show, "close": cmd_close}[args.command]
        return handler(args, root)
    except rl.Usage as e:
        print("test_debt.py: %s" % e, file=sys.stderr)
        return 1
    except Refused as e:
        print("test_debt.py: refused: %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
