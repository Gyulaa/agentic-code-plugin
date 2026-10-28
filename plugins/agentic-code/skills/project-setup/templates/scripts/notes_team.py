#!/usr/bin/env python3
"""Team layer of the project notes: the start-of-work digest, safe saving, tidy lists, migration.

Usage:
  scripts/notes_team.py inbox [--since YYYY-MM-DD]   what happened since your last run and what waits for you
  scripts/notes_team.py snapshot                     open branches of the configured repos, one line each
  scripts/notes_team.py tidy                         the clean-up baskets (read-only)
  scripts/notes_team.py save "message" FILE ...      commit the named notes safely (pull --rebase; push only if allowed)
  scripts/notes_team.py migrate [--apply]            split docs/decisions.md and docs/bugs.md into note files

Needs scripts/notes.py next to it. Exit codes: 0 done, 1 a git step failed (nothing was guessed), 2 refused.
Python 3.8+, standard library only.
"""

import argparse
import collections
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import notes as N  # noqa: E402

START, END = "<!-- snapshot:start -->", "<!-- snapshot:end -->"


def person_of(ctx, author):
    a = N.fold(author)
    for pid, info in ctx.cfg["people"].items():
        names = [N.fold(x) for x in N.as_list(info.get("names") if isinstance(info, dict) else info)] + [N.fold(pid)]
        if a in names:
            return pid
    return a


def stamp_file(ctx):
    gitdir = N.git(ctx.git_root, "rev-parse", "--git-dir", clean=True) or ".git"
    return os.path.join(os.path.abspath(os.path.join(ctx.git_root, gitdir)), "notes-stamp")


def read_stamp(ctx):
    try:
        data = json.loads(N.slurp(stamp_file(ctx)))
        return float(data.get("ts") or 0), str(data.get("commit") or "")
    except (OSError, ValueError, AttributeError):
        return None, ""


def repo_paths(ctx):
    workspace = os.path.normpath(os.path.join(ctx.git_root, ctx.cfg.get("workspace", "..")))
    out = []
    for r in ctx.cfg["repos"]:
        out.append((r.get("name", ""), os.path.join(workspace, r.get("path") or r.get("name", "")), r.get("default")))
    return out


def repo_default(path, configured):
    if configured:
        return configured
    ref = N.git(path, "symbolic-ref", "--short", "refs/remotes/origin/HEAD", clean=True)
    if ref:
        return ref.split("/", 1)[-1]
    for name in ("main", "master"):
        if N.git(path, "rev-parse", "--verify", "--quiet", "refs/heads/" + name, clean=True):
            return name
    return ""


# --- snapshot --------------------------------------------------------------------------------------

def snapshot(ctx):
    lines = []
    for name, path, configured in repo_paths(ctx):
        if not os.path.isdir(path) or not N.git(path, "rev-parse", "--git-dir", clean=True):
            lines.append("- %s: not cloned here" % name)
            continue
        default = repo_default(path, configured)
        current = N.git(path, "branch", "--show-current", clean=True)
        dirty = len([l for l in N.git(path, "status", "--porcelain", clean=True).splitlines() if l])
        other_wt = set()
        wt = N.git(path, "worktree", "list", "--porcelain", clean=True).split("\n\n")
        for block in wt[1:]:
            for l in block.splitlines():
                if l.startswith("branch refs/heads/"):
                    other_wt.add(l[len("branch refs/heads/"):])
        unmerged = set(N.git(path, "branch", "--no-merged", default, "--format=%(refname:short)",
                             clean=True).splitlines()) if default else set()
        if current and current != default:
            unmerged.add(current)
        rows = N.git(path, "for-each-ref", "--format=%(refname:short)|%(objectname:short)|%(upstream:short)|"
                     "%(upstream:track)", "refs/heads", clean=True).splitlines()
        found = 0
        for row in sorted(rows):
            branch, sha, up, track = (row.split("|") + ["", "", "", ""])[:4]
            if branch not in unmerged:
                continue
            found += 1
            notes_ = []
            ahead = re.search(r"ahead (\d+)", track)
            behind = re.search(r"behind (\d+)", track)
            if ahead:
                notes_.append("ahead %s" % ahead.group(1))
            if behind:
                notes_.append("behind %s" % behind.group(1))
            notes_.append("pushed" if up and not ahead and "gone" not in track else "not pushed")
            if branch in other_wt:
                notes_.append("worktree")
            if branch == current and dirty:
                notes_.append("%d uncommitted file(s)" % dirty)
            lines.append("- %s: %s @%s (%s)" % (name, branch, sha, ", ".join(notes_)))
        if not found:
            lines.append("- %s: only %s%s" % (name, default or current,
                                              " (%d uncommitted file(s))" % dirty if dirty else ""))
    return lines


def cmd_snapshot(ctx, args):
    lines = snapshot(ctx)
    print("\n".join(lines) if lines else "(no repos in config.json)")
    return 0


# --- inbox -----------------------------------------------------------------------------------------

def gh_list(path, args):
    rc, out, _ = N.run(path, ["gh"] + args, clean=True, timeout=20)
    if rc != 0:
        return []
    try:
        return json.loads(out)
    except ValueError:
        return []


def open_age(n):
    return N.days_since(n.fm.get("updated")) or 0


def cmd_inbox(ctx, args):
    started = datetime.datetime.now().timestamp()
    cfg, me = ctx.cfg, N.whoami(ctx)
    if cfg["people"] and me not in cfg["people"]:
        print("NOTE: I do not know who you are (%s); the waiting list may be empty. Fix: scripts/notes.py whoami --set <id>"
              % (me or "unset"))
    pulled = ""
    branch = N.git(ctx.git_root, "branch", "--show-current")
    if ctx.dedicated and branch and branch == N.default_branch(ctx) and N.upstream_ref(ctx):
        if N.git(ctx.git_root, "status", "--porcelain", "-uno"):
            pulled = "not pulled: you have uncommitted changes"
        else:
            rc, _, err = N.run(ctx.git_root, ["git", "pull", "--ff-only", "--quiet"], clean=True, timeout=60)
            pulled = "" if rc == 0 else "pull failed (%s)" % (err.strip().splitlines() or ["offline?"])[0][:60]
    last_ts, last_commit = read_stamp(ctx)
    if args.since:
        try:
            since = datetime.datetime.strptime(args.since, "%Y-%m-%d")
        except ValueError:
            raise N.Refused("--since needs a date like 2026-10-20")
        last_commit = ""
    elif last_ts is not None:
        since = datetime.datetime.fromtimestamp(last_ts)
    else:
        since = datetime.datetime.now() - datetime.timedelta(days=3)
    iso = since.strftime("%Y-%m-%dT%H:%M:%S")
    head = N.git(ctx.git_root, "rev-parse", "HEAD")
    if last_commit and N.run(ctx.git_root, ["git", "merge-base", "--is-ancestor", last_commit, "HEAD"])[0] == 0:
        rng = ["%s..HEAD" % last_commit]
    else:
        rng = ["HEAD", "--since=" + iso]
    spec = [] if ctx.dedicated else ["--", os.path.relpath(ctx.root, ctx.git_root)]
    commits = [l.split("|", 1) for l in N.git(ctx.git_root, "log", *(rng + ["--format=%an|%s"] + spec)).splitlines()
               if "|" in l]
    others = [(person_of(ctx, a), s) for a, s in commits if person_of(ctx, a) != me]
    changed, seen = [], set()
    log = N.run(ctx.root, ["git", "log"] + rng + ["--format=@%an", "--name-status", "-M", "--",
                                                  "decisions/", "archive/decisions/"])[1]
    author = ""
    for line in log.splitlines():
        if line.startswith("@"):
            author = person_of(ctx, line[1:])
            continue
        parts = line.split("\t")
        stem = os.path.splitext(os.path.basename(parts[-1]))[0]
        if len(parts) < 2 or author == me or stem in seen or stem.startswith("_"):
            continue
        seen.add(stem)
        for folder in ("decisions", "archive/decisions"):
            p = os.path.join(ctx.root, folder, stem + ".md")
            if os.path.isfile(p):
                fm = N.parse_header(N.slurp(p))[0]
                changed.append((stem, N.scalar(fm.get("status")) or "?", author))
                break
    print("NEWS (since %s; you: %s)%s:" % (since.strftime("%m-%d %H:%M"), me or "?", " [" + pulled + "]" if pulled else ""))
    news = 0
    day = since.strftime("%Y-%m-%d")
    for name, path, _ in repo_paths(ctx):
        if not os.path.isdir(path):
            continue
        for pr in gh_list(path, ["pr", "list", "--state", "merged", "--search", "merged:>=" + day, "--json",
                                 "number,title,author", "-L", "5"]):
            print("  merged: %s #%s %s (%s)" % (name, pr.get("number"), str(pr.get("title"))[:60],
                                                (pr.get("author") or {}).get("login", "?")))
            news += 1
        for pr in gh_list(path, ["pr", "list", "--state", "open", "--search", "created:>=" + day, "--json",
                                 "number,title,author", "-L", "5"]):
            print("  new PR: %s #%s %s (%s)" % (name, pr.get("number"), str(pr.get("title"))[:60],
                                                (pr.get("author") or {}).get("login", "?")))
            news += 1
    if others:
        count = collections.Counter(a for a, _ in others)
        print("  notes: %s; latest: %s" % (", ".join("%s %d commit(s)" % kv for kv in sorted(count.items())),
                                          others[0][1][:60]))
        news += 1
    for stem, status, who in changed:
        print("  decision %s -> %s (%s)" % (stem, status, who))
        news += 1
    yellow = collections.OrderedDict()
    names = N.run(ctx.root, ["git", "log"] + rng + ["--format=@%an", "--name-only", "--", "."])[1]
    author = ""
    for line in names.splitlines():
        if line.startswith("@"):
            author = person_of(ctx, line[1:])
        elif line and author != me:
            rel = os.path.relpath(os.path.join(ctx.git_root, line), ctx.root).replace(os.sep, "/")
            if N.zone_of(ctx, rel) == "yellow":
                yellow.setdefault(rel, author)
    for rel, who in yellow.items():
        print("  changed in the yellow zone: %s (%s)" % (rel, who))
        news += 1
    if not news:
        print("  nothing new")
    live = [n for n in N.collect(ctx) if not n.archived and not n.error]
    waiting = []
    for n in live:
        spec_ = ctx.types()[n.type_name]
        if n.status in spec_["open"] and me and me in N.as_list(n.fm.get("waiting-on")):
            waiting.append((open_age(n), n))
    waiting.sort(key=lambda w: (-w[0], w[1].stem))
    if waiting:
        print("WAITING FOR YOU (%d):" % len(waiting))
        for age, n in waiting[:5]:
            print("  %s, %s: %s (%s, %d days)" % (n.type_name, n.status, N.scalar(n.fm.get("title"))[:60], n.stem, age))
        if len(waiting) > 5:
            print("  ... and %d more (scripts/notes.py find waiting-on=%s)" % (len(waiting) - 5, me))
    else:
        print("WAITING FOR YOU: nothing")
    orphans = [n for n in live if n.type_name == "decision" and n.status in ctx.types()["decision"]["open"]
               and not N.as_list(n.fm.get("waiting-on"))]
    if orphans:
        oldest = max(orphans, key=open_age)
        print("OWNERLESS: %d open decision(s) without waiting-on (oldest: %s, %d days)" %
              (len(orphans), oldest.stem, open_age(oldest)))
    stale = [n for n in live if n.status in ctx.types()[n.type_name]["open"] and open_age(n) >= cfg["stale_days"]]
    if stale:
        print("TIDY: %d open item(s) have not moved for %d days (/agentic-code:tidy-notes)" % (len(stale), cfg["stale_days"]))
    state = os.path.join(ctx.root, cfg["state"])
    if os.path.isfile(state):
        text = N.slurp(state)
        if START in text and END in text and cfg["repos"]:
            have = [l.strip() for l in text.split(START, 1)[1].split(END, 1)[0].splitlines() if l.strip()]
            if have != [l.strip() for l in snapshot(ctx) if l.strip()]:
                print("SNAPSHOT: the code snapshot in %s differs from the repos (scripts/notes_team.py snapshot)" %
                      cfg["state"])
    if not args.since:
        try:
            with open(stamp_file(ctx), "w", encoding="utf-8") as f:
                json.dump({"ts": started, "commit": head}, f)
        except OSError:
            pass
    return 0


# --- tidy ------------------------------------------------------------------------------------------

def cmd_tidy(ctx, args):
    notes = N.collect(ctx)
    live = [n for n in notes if not n.archived and not n.error]
    cfg = ctx.cfg
    by_stem = dict((n.stem.lower(), n) for n in notes)
    baskets = collections.OrderedDict()
    baskets["1 archivable (closed, still in place)"] = [
        "%s (%s)" % (n.stem, n.status) for n in live if n.status in ctx.types()[n.type_name]["closed"]]
    superseded = collections.defaultdict(list)
    for n in live:
        for target, rel in n.links():
            t = by_stem.get(target.lower())
            if rel == "supersedes" and t and t is not n:
                superseded[t.stem].append(n.stem)
    mismatch = []
    for n in live:
        if n.type_name == "decision" and n.stem in superseded:
            want = {"accepted": "superseded", "open": "rejected", "proposed": "rejected"}.get(n.status)
            if want:
                mismatch.append("%s is %s but %s supersedes it -> %s" % (n.stem, n.status, superseded[n.stem][0], want))
    baskets["2 superseded but not marked so"] = mismatch
    baskets["3 ownerless (open, no waiting-on)"] = [
        "%s (%d days)" % (n.stem, open_age(n)) for n in live
        if n.type_name in ("decision", "message") and n.status in ctx.types()[n.type_name]["open"]
        and not N.as_list(n.fm.get("waiting-on"))]
    stale = sorted((n for n in live if n.status in ctx.types()[n.type_name]["open"]
                    and open_age(n) >= cfg["stale_days"]), key=lambda n: -open_age(n))
    baskets["4 not moved for %d days or more" % cfg["stale_days"]] = [
        "%s [%s, %s; %s; %d days] %s" % (n.stem, n.type_name, n.status, ",".join(N.as_list(n.fm.get("waiting-on"))) or "-",
                                          open_age(n), N.scalar(n.fm.get("title"))[:50]) for n in stale]
    issues, _, _ = N.check(ctx)
    bad = sorted(set(i["path"] for i in issues if i["path"].endswith(".md") and not i["path"].endswith("_index.md")
                     and not i["soft"]))
    baskets["5 header or link errors (scripts/notes.py check)"] = bad
    stuck = []
    skipped = False
    for n in live:
        if n.type_name == "bug" and n.status in ("in-progress", "pr-open") and n.fm.get("pr"):
            merged = N.pr_merged(N.scalar(n.fm.get("pr")), ctx.git_root)
            if merged is None:
                skipped = True
            elif merged:
                stuck.append("%s is %s but PR %s is merged" % (n.stem, n.status, N.scalar(n.fm.get("pr"))))
    baskets["6 bugs whose PR is merged" + (" (gh unavailable for some: skipped)" if skipped else "")] = stuck
    baskets["7 conflict copies"] = [i["path"] for i in issues if "conflict copy" in i["msg"]]
    total = 0
    for title, items in baskets.items():
        print("%s: %d" % (title, len(items)))
        for line in items[:10]:
            print("  " + line)
        if len(items) > 10:
            print("  ... %d more" % (len(items) - 10))
        total += len(items)
    print("nothing to tidy" if not total else "%d item(s); /agentic-code:tidy-notes checks each against the code" % total)
    return 0


# --- save ------------------------------------------------------------------------------------------

def in_rebase(ctx):
    gd = N.git(ctx.git_root, "rev-parse", "--git-dir", clean=True)
    gd = os.path.abspath(os.path.join(ctx.git_root, gd))
    return os.path.isdir(os.path.join(gd, "rebase-merge")) or os.path.isdir(os.path.join(gd, "rebase-apply"))


def resolve_generated(ctx):
    """In a stopped rebase, regenerate conflicted _index.md files and go on; False if anything else conflicts."""
    for _ in range(50):
        if not in_rebase(ctx):
            return True
        unmerged = N.git(ctx.git_root, "diff", "--name-only", "--diff-filter=U", clean=True).splitlines()
        if not unmerged or any(os.path.basename(p) != "_index.md" for p in unmerged):
            return False
        notes = N.collect(ctx)
        for p in unmerged:
            folder = os.path.basename(os.path.dirname(p))
            for t, spec in ctx.types().items():
                if spec.get("index") and spec["folder"] == folder:
                    with open(os.path.join(ctx.git_root, p), "w", encoding="utf-8") as f:
                        f.write(N.render_index(ctx, t, notes))
            N.run(ctx.git_root, ["git", "add", "--", p], clean=True)
        N.run(ctx.git_root, ["git", "-c", "core.editor=true", "rebase", "--continue"], clean=True)
    return not in_rebase(ctx)


def cmd_save(ctx, args):
    cfg = ctx.cfg
    if in_rebase(ctx):
        raise N.Refused("a rebase is in progress in the notes repo; look at git status first, do not save on top of it")
    branch = N.git(ctx.git_root, "branch", "--show-current")
    default = N.default_branch(ctx)
    if ctx.dedicated and branch != default and branch not in cfg["save_branches"]:
        raise N.Refused("the notes repo is on '%s'; saving goes to %s (or one of save_branches)" % (branch or "no branch", default))
    if not ctx.dedicated and branch == default:
        raise N.Refused("notes live in the code repo; do not commit on %s, use a branch and a pull request" % default)
    files = [os.path.abspath(f) for f in args.files]
    for f in files:
        if not f.startswith(ctx.git_root + os.sep):
            raise N.Refused("not inside the repo: %s" % f)
        if N.CONFLICT_COPY.match(os.path.basename(f)):
            raise N.Refused("conflict copy, not saved: %s" % f)
        if not os.path.exists(f) and N.run(ctx.git_root, ["git", "ls-files", "--error-unmatch", "--", f])[0] != 0:
            raise N.Refused("no such file: %s" % f)
    N.fetch(ctx)
    up = N.upstream_ref(ctx)
    for f in files:
        rel = os.path.relpath(f, ctx.git_root).replace(os.sep, "/")
        if not os.path.exists(f) or os.path.basename(f).startswith("_"):
            continue
        new = N.run(ctx.git_root, ["git", "cat-file", "-e", "HEAD:" + rel])[0] != 0
        if new and up and N.run(ctx.git_root, ["git", "cat-file", "-e", "%s:%s" % (up, rel)])[0] == 0:
            raise N.Refused("%s already exists upstream (a number or name taken by someone else); run "
                            "scripts/notes.py renumber <id> and save again" % rel)
    present = [f for f in files if os.path.exists(f) and f.startswith(ctx.root + os.sep)]
    issues, _, mode = N.check(ctx, files=present)
    blocking = [i for i in issues if not i["soft"] and (mode == "block" or i["hard"])]
    if blocking:
        for i in blocking:
            print("ERROR %s: %s" % (i["path"], i["msg"]))
        raise N.Refused("the notes do not pass scripts/notes.py check; nothing was committed")
    for f in files:
        if os.path.exists(f) or N.run(ctx.git_root, ["git", "ls-files", "--error-unmatch", "--", f])[0] == 0:
            N.run(ctx.git_root, ["git", "add", "--", f])
    if N.run(ctx.git_root, ["git", "diff", "--cached", "--quiet", "--"] + files)[0] == 0:
        print("nothing to save")
        return 0
    rc, out, err = N.run(ctx.git_root, ["git", "commit", "-q", "-m", args.message, "--"] + files)
    if rc != 0:
        print("commit failed (a hook stopped it?):\n" + (out + err).strip())
        return 1
    sha = N.git(ctx.git_root, "log", "-1", "--format=%h %s")
    if not up:
        print("saved locally (no upstream): %s" % sha)
        return 0
    rc, out, err = N.run(ctx.git_root, ["git", "pull", "--rebase", "--autostash", "--quiet"], clean=True, timeout=120)
    if rc != 0 and in_rebase(ctx) and resolve_generated(ctx):
        rc = 0
    if rc != 0:
        if in_rebase(ctx):
            print("CONFLICT while pulling: stop and tell the people involved (git status). Do not resolve it by guessing.")
        else:
            print("pull failed (offline?): %s" % (err.strip() or out.strip())[:200])
            print("your save is local (%s); the next save or `git pull --rebase && git push` sends it" % sha)
        return 1
    stale = N.write_indexes(ctx)
    if stale:
        for rel in stale:
            N.run(ctx.git_root, ["git", "add", "--", os.path.join(ctx.root, rel)])
        N.run(ctx.git_root, ["git", "commit", "-q", "-m", "refresh generated indexes", "--"] +
              [os.path.join(ctx.root, rel) for rel in stale])
    zones_ok = bool(cfg["zones"].get("green")) and all(
        N.zone_of(ctx, ctx.rel(f)) in ("green", "yellow") for f in files if f.startswith(ctx.root + os.sep))
    if cfg["auto_push"] and ctx.dedicated and zones_ok:
        rc, out, err = N.run(ctx.git_root, ["git", "push", "--quiet"], clean=True, timeout=120)
        if rc != 0:
            print("push failed: %s" % (err.strip() or out.strip())[:200])
            print("your save is local (%s); `git push` sends it" % sha)
            return 1
        print("saved and pushed: %s" % sha)
    else:
        why = "auto_push is off" if not cfg["auto_push"] else (
            "not a separate notes repo" if not ctx.dedicated else "a file is outside the green and yellow zones")
        print("saved, not pushed (%s): %s" % (why, sha))
    return 0


# --- migrate ---------------------------------------------------------------------------------------

STATUS_MAP = {"open": "open", "in progress": "in-progress", "in-progress": "in-progress", "pr open": "pr-open",
              "pr-open": "pr-open", "fixed": "fixed", "wontfix": "wontfix", "won't fix": "wontfix",
              "invalid": "invalid"}


def first_sentence(text, limit):
    text = re.sub(r"\s+", " ", text).strip()
    m = re.match(r"^(.+?[.!?])(\s|$)", text)
    s = m.group(1) if m and len(m.group(1)) <= limit else text
    return s if len(s) <= limit else s[:limit - 3].rstrip() + "..."


def cmd_migrate(ctx, args):
    plan, manual = [], []
    dpath = os.path.join(ctx.git_root, args.decisions)
    if os.path.isfile(dpath):
        text = N.slurp(dpath)
        chunks = re.split(r"(?m)^## ", text)[1:]
        used = set(n.stem for n in N.collect(ctx))
        for chunk in chunks:
            head, _, rest = chunk.partition("\n")
            m = re.match(r"^(\d{4}-\d{2}-\d{2}) · (.+)$", head.strip())
            if not m or "{{" in head:
                if "{{" not in head:
                    manual.append("%s: section '%s' does not look like '## DATE · TITLE'" % (args.decisions, head.strip()[:50]))
                continue
            date, title = m.group(1), m.group(2).strip()
            fields = dict((k.lower(), v.strip()) for k, v in re.findall(r"(?m)^- \*\*([\w ]+):\*\*\s*(.*)$", rest))
            stem, i = N.slugify(title), 2
            while stem in used:
                stem = "%s-%d" % (N.slugify(title), i)
                i += 1
            used.add(stem)
            body = "\n# %s\n\n" % title + "".join("**%s:** %s\n" % (k.capitalize(), fields[k])
                                                   for k in ("decision", "why", "affects") if k in fields)
            if not fields:
                body += rest.strip() + "\n"
            body += "\nMigrated from %s. Related: [[%s]]\n" % (args.decisions, os.path.splitext(os.path.basename(ctx.cfg["state"]))[0])
            summary = first_sentence(fields.get("decision") or rest, ctx.cfg["summary_max"])
            fm = collections.OrderedDict([("title", '"%s"' % title.replace('"', "'")), ("type", "decision"),
                                          ("status", "accepted")])
            if ctx.cfg["areas"]:
                fm["area"] = ""
            fm.update([("summary", '"%s"' % summary.replace('"', "'")), ("decided-by", "team"), ("created", date),
                       ("updated", date)])
            plan.append(("decisions/%s.md" % stem, "---\n" + "".join("%s: %s\n" % kv for kv in fm.items()) + "---\n" + body))
    bpath = os.path.join(ctx.git_root, args.bugs)
    if os.path.isfile(bpath):
        numbers = set()
        rows = []
        for line in N.slurp(bpath).splitlines():
            if not line.startswith("|") or re.match(r"^\|[\s:|-]+\|$", line) or "{{" in line:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 4 or cells[0].lower() == "id":
                continue
            rows.append(cells + [""] * (6 - len(cells)))
        for cells in rows:
            m = re.match(r"^[A-Za-z]*(\d+)$", cells[0])
            if m:
                numbers.add(int(m.group(1)))
        spec = ctx.types()["bug"]
        nxt = max(numbers or {0}) + 1
        for cells in rows:
            ident, sev, status, what, where, origin = cells[:6]
            m = re.match(r"^[A-Za-z]*(\d+)$", ident)
            if m:
                num = int(m.group(1))
            else:
                num, nxt = nxt, nxt + 1
                manual.append("%s: row '%s' has no number, numbered B%d" % (args.bugs, ident[:20], num))
            st = STATUS_MAP.get(status.lower().replace("`", ""))
            if not st:
                manual.append("B%d: status '%s' is not known, set to open; check it" % (num, status))
                st = "open"
            sev = sev.lower()
            if sev not in ctx.cfg["severity"]:
                manual.append("B%d: severity '%s' is not known, set to medium; check it" % (num, sev))
                sev = "medium" if "medium" in ctx.cfg["severity"] else ctx.cfg["severity"][0]
            where = re.sub(r":\d+$", "", where.replace("`", "").strip())
            fm = collections.OrderedDict([("title", '"%s"' % what[:80].replace('"', "'")), ("type", "bug"),
                                          ("status", st), ("severity", sev)])
            if ctx.cfg["areas"]:
                fm["area"] = ""
            fm["summary"] = '"%s"' % first_sentence(what, ctx.cfg["summary_max"]).replace('"', "'")
            if N.CODE_PATH.match(where or "-"):
                if N.code_exists(ctx, where):
                    fm["code"] = "[%s]" % where
                else:
                    manual.append("B%d: code path %s not found, left out" % (num, where))
            if origin and origin != "-":
                fm["origin"] = '"%s"' % origin.replace('"', "'")
            fm["created"] = fm["updated"] = N.today()
            body = "\n# %s\n\n%s\n\nMigrated from %s. Related: [[%s]]\n" % (
                what[:80], what, args.bugs, os.path.splitext(os.path.basename(ctx.cfg["state"]))[0])
            plan.append(("bugs/%s%d.md" % (spec["prefix"], num), "---\n" + "".join("%s: %s\n" % kv for kv in fm.items()) + "---\n" + body))
    created = 0
    for rel, text in plan:
        dest = os.path.join(ctx.root, rel)
        if os.path.exists(dest):
            manual.append("%s exists, skipped" % rel)
            continue
        print("%s %s" % ("create" if args.apply else "would create", rel))
        if args.apply:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(text)
        created += 1
    if args.apply and created:
        N.cmd_index(ctx, None)
    for m in manual:
        print("manual: " + m)
    if not plan:
        print("nothing to migrate (looked for %s and %s)" % (args.decisions, args.bugs))
    elif args.apply:
        print("done: %d note(s). Decisions are marked accepted and decided-by team (the log did not say who); fix "
              "that where it is wrong, fill in area where the config has areas, run scripts/notes.py check, and "
              "remove the old files once you have read the result." % created)
    else:
        print("dry run: %d note(s); add --apply to write them" % created)
    return 0


# --- main ------------------------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(prog="notes_team.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd")
    i = sub.add_parser("inbox")
    i.add_argument("--since")
    sub.add_parser("snapshot")
    sub.add_parser("tidy")
    s = sub.add_parser("save")
    s.add_argument("message")
    s.add_argument("files", nargs="+")
    m = sub.add_parser("migrate")
    m.add_argument("--apply", action="store_true")
    m.add_argument("--decisions", default="docs/decisions.md")
    m.add_argument("--bugs", default="docs/bugs.md")
    args = p.parse_args(argv)
    if not args.cmd:
        print(__doc__)
        return 1
    commands = {"inbox": cmd_inbox, "snapshot": cmd_snapshot, "tidy": cmd_tidy, "save": cmd_save, "migrate": cmd_migrate}
    try:
        return commands[args.cmd](N.load_ctx(), args)
    except N.Refused as e:
        print("refused: %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
