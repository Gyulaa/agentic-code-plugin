#!/usr/bin/env python3
"""Project notes: one file per decision, bug, task and message, a header schema, and a gate that keeps them honest.

Usage:
  scripts/notes.py check [--staged] [--warn] [FILE ...]   the gate (exit 1 on errors)
  scripts/notes.py new TYPE "Title" [--area A] [--waiting-on P,..] [--to P,..] [--severity S] [--owner P]
  scripts/notes.py find [key=value ...] [--text WORD] [--archive] [--json]
  scripts/notes.py show ID | related ID [--depth N] | area NAME | code PATH
  scripts/notes.py index                     rewrite the generated _index.md files
  scripts/notes.py health [--save] [--json] [--prs]
  scripts/notes.py graph [--out FILE]        deterministic graph of headers and links, no model
  scripts/notes.py archive ID ...            move closed notes to archive/<folder>/ (at most 20)
  scripts/notes.py whoami [--set ID]         who you are (NOTES_ME, then .notes-me, then git user.name)
  scripts/notes.py renumber ID               give a not yet committed B/T note the next free number

The notes folder is the one with config.json: $NOTES_DIR, else <repo>/notes, else the repo root.
Exit codes: 0 done, 1 the notes have errors, 2 refused (with the reason).
Python 3.8+, standard library only. Header syntax read: flat "key: value", inline lists "key: [a, b]" and
block lists ("key:" then "  - a"); anything else is refused with a message.
"""

import argparse
import collections
import datetime
import fnmatch
import json
import os
import re
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULTS = {
    "state": "STATE.md",
    "types": {
        "decision": {"folder": "decisions", "index": True, "open": ["open", "proposed"],
                     "statuses": ["open", "proposed", "accepted", "rejected", "superseded"],
                     "closed": ["rejected", "superseded"]},
        "bug": {"folder": "bugs", "prefix": "B", "index": True, "open": ["open", "in-progress", "pr-open"],
                "statuses": ["open", "in-progress", "pr-open", "fixed", "wontfix", "invalid"],
                "closed": ["fixed", "wontfix", "invalid"]},
        "task": {"folder": "tasks", "prefix": "T", "index": True, "open": ["open", "in-progress"],
                 "statuses": ["open", "in-progress", "done", "dropped"], "closed": ["done", "dropped"]},
        "message": {"folder": "messages", "open": ["open"], "statuses": ["open", "closed"], "closed": ["closed"]},
        "knowledge": {"folder": "knowledge", "open": [], "statuses": ["active", "archived"],
                      "closed": ["archived"]},
    },
    "severity": ["critical", "high", "medium", "low"],
    "categories": [],
    "areas": {},
    "people": {},
    "repos": [],
    "min_links": 1,
    "stale_days": 30,
    "summary_max": 160,
    "archive_limit": 20,
    "gate": "block",
    "sessions": False,
    "auto_push": False,
    "save_branches": [],
    "zones": {},
    "privacy": {"allowed_email_domains": [], "local_dirs": ["local"]},
}
RELATIONS = {"solves", "causes", "supersedes", "depends", "part-of", "affects"}
BUILTIN_EMAIL_OK = {"example.com", "example.org", "example.net", "localhost", "users.noreply.github.com"}
NO_SCAN_DIRS = {"scripts", ".githooks", ".git", ".notes", ".obsidian"}
LINK = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\\?\|[^\]]*)?\]\]")
TYPED = re.compile(r"(?:^|\s)([a-z][a-z-]*)::\s*((?:\[\[[^\]]+\]\][\s,]*)+)")
FENCE = re.compile(r"```.*?```|`[^`\n]*`", re.S)
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CONFLICT_COPY = re.compile(r"^.+ \d{1,3}\.md$")
SECRETS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "GitHub token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), "API key"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"(?i)authorization:\s*bearer\s+[A-Za-z0-9._~+/=-]{16,}"), "bearer token"),
]
ASSIGN = re.compile(r"(?i)\b(?:password|passwd|secret|api[_-]?key|token)\b[\"']?\s*[:=]\s*[\"']?([^\s\"'<>{}\[\]()]{8,})")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})")
CODE_PATH = re.compile(r"^[\w./-]+/[\w./-]+$|^[\w.-]+\.(?:py|js|ts|tsx|jsx|dart|go|rs|java|kt|swift|md|json|sh|ya?ml|rb|c|h|cpp|cs|php|html|css)$")


class Refused(Exception):
    """A request the script will not carry out (exit code 2)."""


# --- git -------------------------------------------------------------------------------------------

def run(cwd, args, clean=False, timeout=60):
    env = None
    if clean:
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") or k == "GIT_SSH_COMMAND"}
    try:
        p = subprocess.run(args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           universal_newlines=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 127, "", str(e)
    return p.returncode, p.stdout, p.stderr


def git(cwd, *args, clean=False):
    """Standard output of a git command, stripped; an empty string if it failed."""
    rc, out, _ = run(cwd, ["git"] + list(args), clean=clean)
    return out.strip() if rc == 0 else ""


def slurp(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def today():
    return os.environ.get("NOTES_TODAY") or datetime.date.today().isoformat()


def days_since(text):
    try:
        then = datetime.date.fromisoformat(str(text))
        return (datetime.date.fromisoformat(today()) - then).days
    except ValueError:
        return None


# --- context ---------------------------------------------------------------------------------------

class Ctx(object):
    def __init__(self, root, git_root, cfg):
        self.root, self.git_root, self.cfg = root, git_root, cfg

    @property
    def dedicated(self):
        return os.path.realpath(self.root) == os.path.realpath(self.git_root)

    def rel(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, "/")

    def types(self):
        return self.cfg["types"]

    def folder_of(self, type_name):
        return self.cfg["types"][type_name]["folder"]


def load_config(root):
    with open(os.path.join(root, "config.json"), encoding="utf-8") as f:
        data = json.load(f)
    cfg = json.loads(json.dumps(DEFAULTS))
    for key, value in data.items():
        if key.startswith("_"):
            continue
        if key == "types":
            for name, spec in value.items():
                cfg["types"].setdefault(name, {}).update(spec)
        elif key == "privacy":
            cfg["privacy"].update(value)
        else:
            cfg[key] = value
    return cfg


def load_ctx(start=None):
    start = start or HERE
    git_root = git(start, "rev-parse", "--show-toplevel", clean=True) or os.path.dirname(start)
    candidates = [os.environ.get("NOTES_DIR"), os.path.join(git_root, "notes"), git_root]
    for c in candidates:
        if c and os.path.isfile(os.path.join(c, "config.json")):
            return Ctx(os.path.abspath(c), git_root, load_config(c))
    raise Refused("no notes folder: config.json not found (looked in $NOTES_DIR, <repo>/notes, <repo>)")


def default_branch(ctx):
    ref = git(ctx.git_root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD", clean=True)
    if ref:
        return ref.split("/", 1)[-1]
    for name in ("main", "master"):
        if git(ctx.git_root, "rev-parse", "--verify", "--quiet", "refs/heads/" + name, clean=True):
            return name
    return git(ctx.git_root, "branch", "--show-current", clean=True)


def upstream_ref(ctx):
    ref = git(ctx.git_root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", clean=True)
    if ref:
        return ref
    branch = git(ctx.git_root, "branch", "--show-current", clean=True)
    cand = "origin/" + branch
    if branch and git(ctx.git_root, "rev-parse", "--verify", "--quiet", cand, clean=True):
        return cand
    return ""


def fetch(ctx):
    if git(ctx.git_root, "remote", clean=True):
        run(ctx.git_root, ["git", "fetch", "--quiet"], clean=True, timeout=30)


# --- header ----------------------------------------------------------------------------------------

def parse_header(text):
    """(dict, body, error). The error is None when the header was read."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text, "no header (the file must start with a --- block)"
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text, "the header is not closed with ---"
    fm, current = {}, None
    for no, raw in enumerate(lines[1:end], start=2):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = re.match(r"^\s+-\s+(.*)$", raw)
        if m and current is not None and isinstance(fm.get(current), list):
            fm[current].append(unquote(m.group(1).strip()))
            continue
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", raw)
        if not m or raw[0] in " \t":
            return {}, text, "header line %d is not supported (use key: value, [a, b] or - items): %s" % (no, raw.strip()[:40])
        key, value = m.group(1), m.group(2).strip()
        if value == "":
            fm[key], current = [], key
        elif value[0] in "|>{&*!" or (value[0] == "[" and value[-1] != "]"):
            return {}, text, "header line %d is not supported (multi-line, object or anchor): %s" % (no, raw.strip()[:40])
        elif value[0] == "[":
            inner = value[1:-1].strip()
            fm[key] = [unquote(p.strip()) for p in inner.split(",") if p.strip()]
            current = None
        else:
            fm[key], current = unquote(value), None
    for key, value in list(fm.items()):
        if value == [] and not isinstance(value, str):
            # "key:" with no items is an empty scalar; "key: []" stays an empty list
            pass
    return fm, "\n".join(lines[end + 1:]), None


def unquote(v):
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def as_list(v):
    if v is None or v == "":
        return []
    return list(v) if isinstance(v, list) else [v]


def scalar(v):
    return v if isinstance(v, str) else ("" if not v else str(v[0]))


# --- notes -----------------------------------------------------------------------------------------

class Note(object):
    def __init__(self, ctx, path, type_name, archived):
        self.path, self.type_name, self.archived = path, type_name, archived
        self.rel = ctx.rel(path)
        self.stem = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            self.text = f.read()
        self.fm, self.body, self.error = parse_header(self.text)

    @property
    def status(self):
        return scalar(self.fm.get("status"))

    def links(self):
        """(target, relation or None) for every wikilink outside code."""
        body = FENCE.sub("", self.body)
        typed = {}
        for m in TYPED.finditer(body):
            for target in LINK.findall(m.group(2)):
                typed[target.strip()] = m.group(1)
        out = []
        for m in LINK.finditer(body):
            t = m.group(1).strip()
            out.append((t, typed.get(t)))
        return out


def collect(ctx):
    notes = []
    for type_name, spec in ctx.types().items():
        for archived, base in ((False, ctx.root), (True, os.path.join(ctx.root, "archive"))):
            folder = os.path.join(base, spec["folder"])
            if not os.path.isdir(folder):
                continue
            for name in sorted(os.listdir(folder)):
                if name.endswith(".md") and not name.startswith("_"):
                    notes.append(Note(ctx, os.path.join(folder, name), type_name, archived))
    return notes


def extra_names(ctx):
    names = {"claude", "readme", os.path.splitext(os.path.basename(ctx.cfg["state"]))[0].lower()}
    path = os.path.join(ctx.root, "local-names.txt")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    names.add(line.lower())
    return names


def slugify(title):
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:50].strip("-")
    return s or "note"


def stem_ok(spec, type_name, stem):
    if spec.get("prefix"):
        return re.match(r"^%s\d+$" % re.escape(spec["prefix"]), stem) is not None
    if type_name == "message":
        return re.match(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*$", stem) is not None
    return re.match(r"^[a-z0-9][a-z0-9-]*$", stem) is not None


# --- check -----------------------------------------------------------------------------------------

def issue(path, msg, hard=False, soft=False):
    """hard: never let through; soft: a warning that never stops anything (ownerless, plain-text identifier)."""
    return {"path": path, "msg": msg, "hard": hard, "soft": soft}


def zone_of(ctx, rel):
    for zone in ("red", "yellow", "green"):
        for pat in ctx.cfg["zones"].get(zone, []):
            if zmatch(rel, pat):
                return zone
    return None


def zmatch(rel, pat):
    if pat.endswith("/**"):
        return rel.startswith(pat[:-2])
    return fnmatch.fnmatch(rel, pat)


def scan_privacy(ctx, rel, text):
    out = []
    allowed = BUILTIN_EMAIL_OK | set(d.lower() for d in ctx.cfg["privacy"].get("allowed_email_domains", []))
    for pat, what in SECRETS:
        if pat.search(text):
            out.append(issue(rel, "looks like a secret (%s); never commit it" % what, True))
    for m in ASSIGN.finditer(text):
        value = m.group(1)
        if re.match(r"^(x+|\*+|\.+|\$|<|example|changeme|redacted|your)", value, re.I):
            continue
        if len(value) >= 16 or re.search(r"\d", value):
            out.append(issue(rel, "looks like a secret (a credential assignment); never commit it", True))
            break
    for m in EMAIL.finditer(text):
        if m.group(1).lower() not in allowed:
            out.append(issue(rel, "personal e-mail address (%s); keep it in a local-only folder or allow its domain "
                                  "in config.json privacy.allowed_email_domains" % m.group(0), True))
            break
    return out


def staged_files(ctx):
    rc, out, _ = run(ctx.git_root, ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"])
    return [os.path.join(ctx.git_root, p) for p in out.split("\0") if p]


def code_exists(ctx, entry):
    if not CODE_PATH.match(entry):
        return True
    bases = [ctx.git_root, ctx.root]
    workspace = os.path.dirname(ctx.git_root)
    for r in ctx.cfg["repos"]:
        bases.append(os.path.join(workspace, r.get("path") or r.get("name", "")))
    bases.append(workspace)
    return any(os.path.exists(os.path.join(b, entry)) for b in bases)


def check_note(ctx, note, known, people, issues):
    cfg, spec = ctx.cfg, ctx.types()[note.type_name]
    add = lambda msg, hard=False, soft=False: issues.append(issue(note.rel, msg, hard, soft))
    if note.error:
        add(note.error)
        return
    fm = note.fm
    for key in ("title", "type", "status", "created", "updated"):
        if not scalar(fm.get(key)):
            add("missing header field: %s" % key)
    if scalar(fm.get("type")) and scalar(fm.get("type")) != note.type_name:
        add("type is %s but the note lives in %s/" % (scalar(fm.get("type")), spec["folder"]))
    if note.status and note.status not in spec["statuses"]:
        add("status '%s' is not one of: %s" % (note.status, ", ".join(spec["statuses"])))
    for key in ("created", "updated"):
        if scalar(fm.get(key)) and not DATE.match(scalar(fm.get(key))):
            add("%s must be YYYY-MM-DD" % key)
    if not stem_ok(spec, note.type_name, note.stem):
        add("file name '%s' does not fit the %s naming" % (note.stem, note.type_name))
    summary = scalar(fm.get("summary"))
    if not summary:
        add("missing header field: summary (one sentence saying what the note states)")
    elif len(summary) > cfg["summary_max"]:
        add("summary is %d characters, at most %d" % (len(summary), cfg["summary_max"]))
    areas = cfg["areas"]
    area_values = as_list(fm.get("area"))
    if areas:
        if not area_values:
            add("missing header field: area (one of: %s)" % ", ".join(sorted(areas)))
        for a in area_values:
            if a not in areas:
                add("area '%s' is not in config.json areas" % a)
    def person_ok(p):
        return not people or p in people
    for key in ("waiting-on", "to", "owner"):
        for p in as_list(fm.get(key)):
            if not person_ok(p):
                add("%s: '%s' is not in config.json people" % (key, p))
    if note.type_name == "decision":
        if note.status in ("accepted", "rejected"):
            d = scalar(fm.get("decided-by"))
            if not d:
                add("missing header field: decided-by (who decided; a person, team or agent)")
            elif d not in ("team", "agent") and not person_ok(d):
                add("decided-by: '%s' is not in config.json people" % d)
        if note.status in spec["open"] and not as_list(fm.get("waiting-on")):
            add("no waiting-on: whose decision is this waiting for? (ownerless)", soft=True)
        if cfg["categories"]:
            c = scalar(fm.get("category"))
            if c not in cfg["categories"]:
                add("category must be one of: %s" % ", ".join(cfg["categories"]))
    if note.type_name == "bug":
        sev = scalar(fm.get("severity"))
        if sev not in cfg["severity"]:
            add("severity must be one of: %s" % ", ".join(cfg["severity"]))
    if note.type_name == "message":
        if not as_list(fm.get("to")):
            add("missing header field: to")
        if note.status in spec["open"] and not as_list(fm.get("waiting-on")):
            add("no waiting-on on an open message", soft=True)
    links = note.links()
    if len(links) < cfg["min_links"]:
        add("%d wikilink(s), at least %d needed" % (len(links), cfg["min_links"]))
    for target, rel in links:
        if target.lower() not in known:
            add("broken link: [[%s]]" % target)
        if rel and rel not in RELATIONS:
            add("unknown relation '%s::' (use: %s)" % (rel, ", ".join(sorted(RELATIONS))))
    prefixes = [s["prefix"] for s in ctx.types().values() if s.get("prefix")]
    if prefixes:
        plain = FENCE.sub("", LINK.sub("", note.body))
        ids = sorted(set(re.findall(r"\b(?:%s)\d+\b" % "|".join(map(re.escape, prefixes)), plain)))
        if ids:
            add("identifier written as plain text, write it as a link: %s" % ", ".join(ids), soft=True)
    for entry in as_list(fm.get("code")):
        if not code_exists(ctx, entry):
            add("code path not found: %s" % entry)


def render_index(ctx, type_name, notes):
    spec = ctx.types()[type_name]
    mine = sorted((n for n in notes if n.type_name == type_name and not n.error), key=lambda n: n.stem)
    lines = ["<!-- generated by scripts/notes.py index; do not edit -->", "", "# " + spec["folder"].capitalize(), ""]
    groups = collections.OrderedDict((s, []) for s in spec["statuses"])
    for n in mine:
        groups.setdefault(n.status or "(no status)", []).append(n)
    for status, group in groups.items():
        if not group:
            continue
        lines += ["## %s (%d)" % (status, len(group)), "", "| Note | Area | Who | Summary |", "|---|---|---|---|"]
        for n in group:
            who = ", ".join(as_list(n.fm.get("waiting-on")) or as_list(n.fm.get("owner")) or
                            as_list(n.fm.get("decided-by")))
            summary = scalar(n.fm.get("summary")).replace("|", "\\|")
            lines.append("| [[%s]] | %s | %s | %s |" % (n.stem, ", ".join(as_list(n.fm.get("area"))), who, summary))
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def index_path(ctx, type_name):
    return os.path.join(ctx.root, ctx.folder_of(type_name), "_index.md")


def check(ctx, files=None, staged=False, warn=False):
    """(issues, number of files looked at, effective mode)."""
    cfg = ctx.cfg
    notes = collect(ctx)
    known = set(n.stem.lower() for n in notes) | extra_names(ctx)
    people = set(cfg["people"])
    issues = []
    targets, other = None, []
    if staged or files:
        paths = staged_files(ctx) if staged else [os.path.abspath(f) for f in files]
        paths = [p for p in paths if p.startswith(ctx.root + os.sep)]
        targets = set(paths)
        by_path = set(n.path for n in notes)
        other = [p for p in paths if p not in by_path and os.path.isfile(p)]
    for n in notes:
        if targets is None or n.path in targets:
            check_note(ctx, n, known, people, issues)
    # whole-tree checks
    counts = collections.Counter(n.stem.lower() for n in notes)
    for n in notes:
        if counts[n.stem.lower()] > 1 and (targets is None or n.path in targets):
            issues.append(issue(n.rel, "duplicate note name '%s' (two notes with the same id); run "
                                       "scripts/notes.py renumber" % n.stem, True))
    for dirpath, dirnames, filenames in os.walk(ctx.root):
        dirnames[:] = [d for d in dirnames if d not in (".git", ".notes", ".obsidian")]
        for name in filenames:
            if CONFLICT_COPY.match(name):
                p = os.path.join(dirpath, name)
                if targets is None or p in targets:
                    issues.append(issue(ctx.rel(p), "conflict copy (sync tool or merge leftover); compare with the "
                                                    "original and delete it", True))
    scan = [n.path for n in notes if targets is None or n.path in targets] + other
    if targets is None:
        for name in ("STATE.md", "README.md", "CLAUDE.md", "local-names.txt"):
            p = os.path.join(ctx.root, name)
            if os.path.isfile(p):
                scan.append(p)
    for p in sorted(set(scan)):
        rel = ctx.rel(p)
        if rel.split("/")[0] in NO_SCAN_DIRS or not p.endswith((".md", ".json", ".txt")):
            continue
        with open(p, encoding="utf-8", errors="replace") as f:
            issues += scan_privacy(ctx, rel, f.read())
    for p in sorted(targets or []):
        rel = ctx.rel(p)
        top = rel.split("/")[0]
        if top in cfg["privacy"].get("local_dirs", []) or top in (".notes", ".obsidian"):
            issues.append(issue(rel, "local-only; this folder is never committed", True))
    for t, spec in ctx.types().items():
        if not spec.get("index"):
            continue
        touched = targets is None or any(n.type_name == t and n.path in targets for n in notes)
        if not touched or not any(n.type_name == t for n in notes):
            continue
        ip = index_path(ctx, t)
        want = render_index(ctx, t, notes)
        have = slurp(ip) if os.path.isfile(ip) else None
        if have != want:
            issues.append(issue(ctx.rel(ip), "index is %s; run scripts/notes.py index" %
                                ("missing" if have is None else "out of date")))
    # the very first commit of a new notes repo creates the scripts and the config, so the zones start after it
    if staged and ctx.dedicated and git(ctx.git_root, "rev-parse", "--verify", "--quiet", "HEAD"):
        branch = git(ctx.git_root, "branch", "--show-current")
        if branch and branch == default_branch(ctx):
            for p in sorted(targets or []):
                if zone_of(ctx, ctx.rel(p)) == "red":
                    issues.append(issue(ctx.rel(p), "red zone: this file changes how the notes work and needs a pull "
                                                    "request, not a commit on %s" % branch, True))
            rc, out, _ = run(ctx.git_root, ["git", "diff", "--cached", "--name-status", "-M"])
            moves = sum(1 for l in out.splitlines() if l.startswith("R"))
            if moves > cfg["archive_limit"]:
                issues.append(issue("(commit)", "%d renames at once on %s; more than %d needs a pull request" %
                                    (moves, branch, cfg["archive_limit"]), True))
    mode = "warn" if (warn or cfg["gate"] == "warn" or os.environ.get("NOTES_GATE") == "warn") else "block"
    return issues, len(scan) + len(set(n.path for n in notes if targets is None or n.path in targets)), mode


def cmd_check(ctx, args):
    issues, _, mode = check(ctx, args.files, args.staged, args.warn)
    errors = 0
    for i in issues:
        soft = i["soft"] or (mode == "warn" and not i["hard"])
        print("%s %s: %s" % ("WARN " if soft else "ERROR", i["path"], i["msg"]))
        errors += 0 if soft else 1
    if mode == "warn" and issues and os.environ.get("NOTES_GATE") == "warn":
        print("NOTES_GATE=warn lets header errors through; write down in a bug note why the gate was bypassed. "
              "Secrets and personal data are never let through.")
    if not issues:
        print("OK")
    elif errors:
        print("%d error(s)" % errors)
    return 1 if errors else 0


# --- queries ---------------------------------------------------------------------------------------

def fold(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii").lower()


def build_graph(notes):
    names = dict((n.stem.lower(), n) for n in notes)
    edges = []
    for n in notes:
        for target, rel in n.links():
            if target.lower() in names:
                edges.append((n.stem, names[target.lower()].stem, rel or "link"))
    return names, edges


def line_of(n):
    who = ",".join(as_list(n.fm.get("waiting-on")) or as_list(n.fm.get("owner")))
    return "%-14s %-9s %-12s %-10s %s" % (n.stem[:14], n.type_name[:9], n.status[:12], who[:10],
                                          scalar(n.fm.get("summary"))[:70])


def cmd_find(ctx, args):
    conds = []
    for c in args.conds:
        if "=" not in c:
            raise Refused("a condition looks like key=value (got '%s')" % c)
        k, v = c.split("=", 1)
        conds.append((k, [fold(x) for x in v.split(",")]))
    found = []
    for n in collect(ctx):
        if n.archived and not args.archive:
            continue
        ok = True
        for k, wanted in conds:
            have = [fold(n.stem)] if k == "id" else [fold(x) for x in as_list(n.fm.get(k))]
            if k == "type":
                have = [fold(n.type_name)]
            if not any(w in have for w in wanted):
                ok = False
        if ok and args.text:
            hay = fold(" ".join([scalar(n.fm.get("title")), scalar(n.fm.get("summary")), n.stem]))
            ok = fold(args.text) in hay
        if ok:
            found.append(n)
    if args.json:
        print(json.dumps([dict(id=n.stem, type=n.type_name, archived=n.archived, **n.fm) for n in found],
                         indent=1, sort_keys=True))
    else:
        for n in found:
            print(line_of(n))
        if not found:
            print("(nothing found)")
    return 0


def get_note(notes, ident):
    for n in notes:
        if n.stem.lower() == ident.lower():
            return n
    raise Refused("no note named '%s'" % ident)


def cmd_show(ctx, args):
    notes = collect(ctx)
    n = get_note(notes, args.id)
    _, edges = build_graph(notes)
    print("%s (%s%s)" % (n.stem, n.rel, ", archived" if n.archived else ""))
    for k, v in n.fm.items():
        print("  %s: %s" % (k, ", ".join(as_list(v)) if isinstance(v, list) else v))
    out = sorted(set((d, r) for s, d, r in edges if s == n.stem))
    inc = sorted(set((s, r) for s, d, r in edges if d == n.stem))
    print("links out: " + (", ".join("%s%s" % (d, "" if r == "link" else " (%s)" % r) for d, r in out) or "-"))
    print("links in:  " + (", ".join("%s%s" % (s, "" if r == "link" else " (%s)" % r) for s, r in inc) or "-"))
    return 0


def cmd_related(ctx, args):
    notes = collect(ctx)
    n = get_note(notes, args.id)
    _, edges = build_graph(notes)
    adj = collections.defaultdict(set)
    for s, d, _ in edges:
        adj[s].add(d)
        adj[d].add(s)
    seen, frontier = {n.stem: 0}, [n.stem]
    for depth in range(1, args.depth + 1):
        nxt = []
        for x in frontier:
            for y in sorted(adj[x]):
                if y not in seen:
                    seen[y] = depth
                    nxt.append(y)
        frontier = nxt
    by = dict((m.stem, m) for m in notes)
    for stem, depth in sorted(seen.items(), key=lambda kv: (kv[1], kv[0])):
        if depth:
            print("%d  %s" % (depth, line_of(by[stem])))
    if len(seen) == 1:
        print("(no linked notes)")
    return 0


def cmd_area(ctx, args):
    groups = collections.defaultdict(list)
    for n in collect(ctx):
        if not n.archived and args.name in as_list(n.fm.get("area")):
            groups[n.type_name].append(n)
    for t in sorted(groups):
        print("%s (%d)" % (t, len(groups[t])))
        for n in sorted(groups[t], key=lambda x: x.stem):
            print("  " + line_of(n))
    if not groups:
        print("(no live notes in area %s)" % args.name)
    return 0


def cmd_code(ctx, args):
    want = args.path.rstrip("/")
    hits = 0
    for n in collect(ctx):
        if n.archived:
            continue
        for entry in as_list(n.fm.get("code")):
            if entry == want or want.startswith(entry.rstrip("/") + "/") or entry.startswith(want + "/") \
                    or entry.endswith("." + want):
                print(line_of(n))
                hits += 1
                break
    if not hits:
        print("(no note mentions %s)" % args.path)
    return 0


# --- writing ---------------------------------------------------------------------------------------

def taken_upstream(ctx):
    up = upstream_ref(ctx)
    return git(ctx.git_root, "ls-tree", "-r", "--name-only", up, clean=True).splitlines() if up else []


def next_number(ctx, prefix):
    fetch(ctx)
    best = 0
    names = [os.path.basename(p) for p in taken_upstream(ctx)]
    for dirpath, _, filenames in os.walk(ctx.root):
        names += filenames
    for name in names:
        m = re.match(r"^%s(\d+)\.md$" % re.escape(prefix), name)
        if m:
            best = max(best, int(m.group(1)))
    return best + 1


def exists_anywhere(ctx, folder, stem):
    rel = "%s/%s.md" % (folder, stem)
    if os.path.exists(os.path.join(ctx.root, rel)) or os.path.exists(os.path.join(ctx.root, "archive", rel)):
        return True
    root_rel = ctx.rel(ctx.root) if False else os.path.relpath(ctx.root, ctx.git_root).replace(os.sep, "/")
    prefix = "" if root_rel == "." else root_rel + "/"
    return any(p in (prefix + rel, prefix + "archive/" + rel) for p in taken_upstream(ctx))


def similar(a, b):
    wa, wb = set(fold(a).split()), set(fold(b).split())
    if not wa or not wb:
        return False
    return len(wa & wb) / float(len(wa | wb)) >= 0.6 or fold(a) in fold(b) or fold(b) in fold(a)


def csv(v):
    return [x.strip() for x in (v or "").split(",") if x.strip()]


def whoami(ctx):
    me = os.environ.get("NOTES_ME", "").strip()
    if not me:
        p = os.path.join(ctx.root, ".notes-me")
        if os.path.isfile(p):
            me = slurp(p).strip()
    if not me:
        name = fold(git(ctx.git_root, "config", "user.name", clean=True))
        for pid, info in ctx.cfg["people"].items():
            names = [fold(x) for x in as_list(info.get("names") if isinstance(info, dict) else info)] + [fold(pid)]
            if name and name in names:
                me = pid
                break
    return me


def cmd_new(ctx, args):
    spec = ctx.types().get(args.type)
    if not spec:
        raise Refused("unknown type '%s' (one of: %s)" % (args.type, ", ".join(sorted(ctx.types()))))
    d, slug = today(), slugify(args.title)
    folder = spec["folder"]
    if spec.get("prefix"):
        stem = "%s%d" % (spec["prefix"], next_number(ctx, spec["prefix"]))
    elif args.type == "message":
        stem = "%s-%s" % (d, slug)
    else:
        stem = slug
    if exists_anywhere(ctx, folder, stem):
        raise Refused("%s/%s.md already exists" % (folder, stem))
    for n in collect(ctx):
        if n.type_name == args.type and not n.archived and similar(scalar(n.fm.get("title")), args.title):
            print("note: a similar note exists: %s (%s); update it instead of adding a second one if it is the same "
                  "thing" % (n.stem, scalar(n.fm.get("title"))))
            break
    fm = collections.OrderedDict([("title", '"%s"' % args.title.replace('"', "'")), ("type", args.type),
                                  ("status", spec["statuses"][0])])
    if ctx.cfg["areas"] or args.area:
        fm["area"] = args.area or ""
    fm["summary"] = ""
    if args.type == "decision":
        fm["waiting-on"] = "[%s]" % ", ".join(csv(args.waiting_on))
        if ctx.cfg["categories"]:
            fm["category"] = ""
    if args.type == "bug":
        fm["severity"] = args.severity or ""
    if args.type == "task" and args.owner:
        fm["owner"] = args.owner
    if args.type == "message":
        to = csv(args.to)
        fm["to"] = "[%s]" % ", ".join(to)
        fm["waiting-on"] = "[%s]" % ", ".join(csv(args.waiting_on) or to)
    fm["created"], fm["updated"] = d, d
    me = whoami(ctx) or "me"
    body = "\n# %s\n\n" % args.title
    if args.type == "message":
        body += "Related: \n\n%s · %s -> %s: \n" % (d, me, ", ".join(csv(args.to)))
    else:
        body += "Related: \n"
    text = "---\n" + "".join("%s: %s\n" % (k, v) for k, v in fm.items()) + "---\n" + body
    dest = os.path.join(ctx.root, folder, stem + ".md")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(text)
    print(ctx.rel(dest))
    print("fill in summary and add at least %d link(s), then: scripts/notes.py index && scripts/notes.py check" %
          ctx.cfg["min_links"])
    return 0


def write_indexes(ctx):
    """Rewrite the generated index files that are missing or stale; the relative paths written."""
    notes = collect(ctx)
    wrote = []
    for t, spec in ctx.types().items():
        if not spec.get("index") or not any(n.type_name == t for n in notes):
            continue
        ip, want = index_path(ctx, t), render_index(ctx, t, notes)
        have = slurp(ip) if os.path.isfile(ip) else None
        if have != want:
            with open(ip, "w", encoding="utf-8") as f:
                f.write(want)
            wrote.append(ctx.rel(ip))
    return wrote


def cmd_index(ctx, args):
    wrote = write_indexes(ctx)
    for rel in wrote:
        print("wrote " + rel)
    if not wrote:
        print("indexes are up to date")
    return 0


def tracked(ctx, path):
    return run(ctx.git_root, ["git", "ls-files", "--error-unmatch", "--", path])[0] == 0


def cmd_archive(ctx, args):
    notes = collect(ctx)
    if len(args.ids) > ctx.cfg["archive_limit"]:
        raise Refused("%d notes at once; at most %d per pass (more needs a decision from a person)" %
                      (len(args.ids), ctx.cfg["archive_limit"]))
    plan = []
    for ident in args.ids:
        n = get_note(notes, ident)
        spec = ctx.types()[n.type_name]
        if n.archived:
            raise Refused("%s is already archived" % n.stem)
        if n.status not in spec["closed"]:
            raise Refused("%s is '%s'; only closed notes (%s) move to the archive" %
                          (n.stem, n.status, ", ".join(spec["closed"]) or "none for this type"))
        dest = os.path.join(ctx.root, "archive", spec["folder"], n.stem + ".md")
        plan.append((n, dest))
    for n, dest in plan:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if tracked(ctx, n.path):
            rc, _, err = run(ctx.git_root, ["git", "mv", "--", n.path, dest])
            if rc != 0:
                raise Refused("git mv failed: " + err.strip())
        else:
            os.rename(n.path, dest)
        print("archived %s -> %s" % (n.stem, ctx.rel(dest)))
    return 0


def pending_files(ctx):
    rc, out, _ = run(ctx.git_root, ["git", "status", "--porcelain", "-z", "-uall"])
    result = []
    for entry in out.split("\0"):
        if len(entry) > 3:
            result.append((entry[:2], os.path.join(ctx.git_root, entry[3:])))
    return result


def cmd_renumber(ctx, args):
    notes = collect(ctx)
    n = get_note(notes, args.id)
    spec = ctx.types()[n.type_name]
    if not spec.get("prefix"):
        raise Refused("only numbered notes (%s) are renumbered" % ", ".join(
            s["prefix"] + "<n>" for s in ctx.types().values() if s.get("prefix")))
    pend = pending_files(ctx)
    mine = [(st, p) for st, p in pend if p == n.path]
    if not mine or mine[0][0] not in ("??", "A ", "AM"):
        raise Refused("%s is already committed; only a note that is not committed yet can be renumbered" % n.stem)
    new = "%s%d" % (spec["prefix"], next_number(ctx, spec["prefix"]))
    dest = os.path.join(os.path.dirname(n.path), new + ".md")
    if mine[0][0] == "??":
        os.rename(n.path, dest)
    else:
        run(ctx.git_root, ["git", "mv", "--", n.path, dest])
    pat = re.compile(r"\[\[%s(?=[\]|#\\])" % re.escape(n.stem))
    touched = 0
    for _, p in pend:
        p = dest if p == n.path else p
        if p.endswith(".md") and p.startswith(ctx.root + os.sep) and os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                text = f.read()
            new_text = pat.sub("[[" + new, text)
            if new_text != text:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(new_text)
                touched += 1
    print("%s -> %s (links rewritten in %d of your uncommitted file(s))" % (n.stem, new, touched))
    return 0


def cmd_whoami(ctx, args):
    if args.set:
        if ctx.cfg["people"] and args.set not in ctx.cfg["people"]:
            raise Refused("'%s' is not in config.json people (%s)" % (args.set, ", ".join(sorted(ctx.cfg["people"]))))
        with open(os.path.join(ctx.root, ".notes-me"), "w", encoding="utf-8") as f:
            f.write(args.set + "\n")
    print(whoami(ctx) or "unknown (set it: scripts/notes.py whoami --set <id>)")
    return 0


# --- health and graph ------------------------------------------------------------------------------

def pr_merged(ref, cwd):
    """True or False for a PR number or URL, None when it cannot be told (no gh, no network)."""
    num = re.search(r"(\d+)\s*$", str(ref))
    if not num:
        return None
    rc, out, _ = run(cwd, ["gh", "pr", "view", num.group(1), "--json", "state,mergedAt"], clean=True, timeout=20)
    if rc != 0:
        return None
    try:
        data = json.loads(out)
    except ValueError:
        return None
    return bool(data.get("mergedAt")) or data.get("state") == "MERGED"


def health(ctx, prs=False):
    notes = [n for n in collect(ctx)]
    live = [n for n in notes if not n.archived and not n.error]
    stale_days = ctx.cfg["stale_days"]
    counts = collections.Counter(n.type_name for n in live)
    open_decisions = [n for n in live if n.type_name == "decision" and n.status in ctx.types()["decision"]["open"]]
    ownerless = [n for n in open_decisions if not as_list(n.fm.get("waiting-on"))]
    stale = [n for n in live if n.status in ctx.types()[n.type_name].get("open", [])
             and (days_since(n.fm.get("updated")) or 0) >= stale_days]
    issues, _, _ = check(ctx)
    failing = len(set(i["path"] for i in issues if i["path"].endswith(".md") and not i["path"].endswith("_index.md")
                      and not i["soft"]))
    msg_ages = sorted(days_since(n.fm.get("updated")) or 0 for n in live
                      if n.type_name == "message" and n.status in ctx.types()["message"]["open"])
    state = os.path.join(ctx.root, ctx.cfg["state"])
    debt_dir = os.path.join(ctx.git_root, "docs", "test-debt")
    debt = None
    if os.path.isdir(debt_dir):
        debt = 0
        for name in os.listdir(debt_dir):
            if name.endswith(".json"):
                try:
                    if json.loads(slurp(os.path.join(debt_dir, name))).get("status") == "open":
                        debt += 1
                except ValueError:
                    pass
    result = {
        "date": today(),
        "notes": dict(counts),
        "ownerless_decisions": len(ownerless),
        "ownerless_oldest": max(ownerless, key=lambda n: days_since(n.fm.get("updated")) or 0).stem if ownerless else None,
        "stale": len(stale),
        "failing_check": failing,
        "state_bytes": os.path.getsize(state) if os.path.isfile(state) else None,
        "open_message_median_age": msg_ages[len(msg_ages) // 2] if msg_ages else None,
        "open_test_debt": debt,
    }
    if prs:
        merged = 0
        for n in live:
            if n.type_name == "bug" and n.status in ("in-progress", "pr-open") and n.fm.get("pr"):
                if pr_merged(scalar(n.fm.get("pr")), ctx.git_root):
                    merged += 1
        result["bugs_with_merged_pr_not_fixed"] = merged
    return result


def cmd_health(ctx, args):
    h = health(ctx, args.prs)
    if args.save:
        d = os.path.join(ctx.root, ".notes")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "health.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(h, sort_keys=True) + "\n")
    if args.json:
        print(json.dumps(h, indent=1, sort_keys=True))
        return 0
    print("notes: " + (", ".join("%s %d" % kv for kv in sorted(h["notes"].items())) or "none"))
    print("ownerless open decisions: %d%s" % (h["ownerless_decisions"],
          " (oldest: %s)" % h["ownerless_oldest"] if h["ownerless_oldest"] else ""))
    print("not moved for %d days or more: %d" % (ctx.cfg["stale_days"], h["stale"]))
    print("notes failing the check: %d" % h["failing_check"])
    print("state file: %s" % ("%d bytes" % h["state_bytes"] if h["state_bytes"] is not None else "missing"))
    if h["open_message_median_age"] is not None:
        print("open messages, median age: %d days" % h["open_message_median_age"])
    if h["open_test_debt"] is not None:
        print("open test debt: %d" % h["open_test_debt"])
    if "bugs_with_merged_pr_not_fixed" in h:
        print("bugs whose PR is merged but are not fixed: %d" % h["bugs_with_merged_pr_not_fixed"])
    return 0


def cmd_graph(ctx, args):
    notes = [n for n in collect(ctx) if not n.error]
    nodes, edges = {}, set()
    for n in notes:
        nodes[n.stem] = {"id": n.stem, "kind": "note", "type": n.type_name, "status": n.status,
                         "archived": n.archived, "title": scalar(n.fm.get("title"))}
    names = dict((n.stem.lower(), n.stem) for n in notes)
    for n in notes:
        for target, rel in n.links():
            if target.lower() in names:
                edges.add((n.stem, names[target.lower()], rel or "link", "typed" if rel else "link"))
        for a in as_list(n.fm.get("area")):
            nodes.setdefault("area:" + a, {"id": "area:" + a, "kind": "area"})
            edges.add((n.stem, "area:" + a, "in-area", "area"))
        for c in as_list(n.fm.get("code")):
            nodes.setdefault("code:" + c, {"id": "code:" + c, "kind": "code"})
            edges.add((n.stem, "code:" + c, "touches", "code"))
    data = {"nodes": [nodes[k] for k in sorted(nodes)],
            "edges": [{"source": s, "target": t, "relation": r, "via": v, "provenance": "EXTRACTED"}
                      for s, t, r, v in sorted(edges)]}
    out = args.out or os.path.join(ctx.root, ".notes", "graph.json")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
        f.write("\n")
    print("%d nodes, %d edges -> %s" % (len(data["nodes"]), len(data["edges"]), out))
    return 0


# --- main ------------------------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(prog="notes.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd")
    c = sub.add_parser("check")
    c.add_argument("--staged", action="store_true")
    c.add_argument("--warn", action="store_true")
    c.add_argument("files", nargs="*")
    n = sub.add_parser("new")
    n.add_argument("type")
    n.add_argument("title")
    n.add_argument("--area")
    n.add_argument("--waiting-on")
    n.add_argument("--to")
    n.add_argument("--severity")
    n.add_argument("--owner")
    f = sub.add_parser("find")
    f.add_argument("conds", nargs="*")
    f.add_argument("--text")
    f.add_argument("--archive", action="store_true")
    f.add_argument("--json", action="store_true")
    sub.add_parser("show").add_argument("id")
    r = sub.add_parser("related")
    r.add_argument("id")
    r.add_argument("--depth", type=int, default=2)
    sub.add_parser("area").add_argument("name")
    sub.add_parser("code").add_argument("path")
    sub.add_parser("index")
    h = sub.add_parser("health")
    h.add_argument("--save", action="store_true")
    h.add_argument("--json", action="store_true")
    h.add_argument("--prs", action="store_true")
    g = sub.add_parser("graph")
    g.add_argument("--out")
    sub.add_parser("archive").add_argument("ids", nargs="+")
    w = sub.add_parser("whoami")
    w.add_argument("--set")
    sub.add_parser("renumber").add_argument("id")
    return p


COMMANDS = {"check": cmd_check, "new": cmd_new, "find": cmd_find, "show": cmd_show, "related": cmd_related,
            "area": cmd_area, "code": cmd_code, "index": cmd_index, "health": cmd_health, "graph": cmd_graph,
            "archive": cmd_archive, "whoami": cmd_whoami, "renumber": cmd_renumber}


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not args.cmd:
        print(__doc__)
        return 1
    try:
        return COMMANDS[args.cmd](load_ctx(), args)
    except Refused as e:
        print("refused: %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
