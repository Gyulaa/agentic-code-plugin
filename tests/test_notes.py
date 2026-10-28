"""Tests for notes.py. Run: python3 -m unittest discover -s tests"""

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "plugins", "agentic-code", "skills", "project-setup", "templates", "scripts")
sys.path.insert(0, SCRIPTS)
import notes  # noqa: E402

# A running git hook exports GIT_AUTHOR_NAME and friends; they would override the throwaway repos' identities.
for _key in [k for k in os.environ if k.startswith("GIT_")]:
    del os.environ[_key]
os.environ["NOTES_TODAY"] = "2026-10-28"
os.environ.pop("NOTES_GATE", None)
os.environ.pop("NOTES_ME", None)

CONFIG = {
    "people": {"alice": {"names": ["Alice A"]}, "bob": {"names": ["Bob B"]}},
    "areas": {"billing": {"owner": "alice"}, "export": {"owner": "bob"}},
    "zones": {"green": ["decisions/*", "bugs/*", "tasks/*", "messages/*"], "red": ["config.json", "scripts/**"]},
    "privacy": {"allowed_email_domains": ["acme.test"], "local_dirs": ["local"]},
}


def slurp(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def git(cwd, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    p = subprocess.run(("git",) + args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True)
    return p.stdout.strip()


def silence(case):
    """Keep the commands' own output out of the test run."""
    stack = contextlib.ExitStack()
    stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
    case.addCleanup(stack.close)


def header(**fm):
    base = dict(created="2026-10-01", updated="2026-10-01")
    base.update(fm)
    return "---\n" + "".join("%s: %s\n" % kv for kv in base.items()) + "---\n"


class Tree(object):
    """A throwaway repo with a notes folder (dedicated: the repo root is the notes folder)."""

    def __init__(self, tmp, dedicated=False, config=None):
        self.git_root = os.path.join(tmp, "repo")
        os.makedirs(self.git_root)
        git(self.git_root, "init", "-q", "-b", "main")
        git(self.git_root, "config", "user.email", "t@example.com")
        git(self.git_root, "config", "user.name", "Alice A")
        self.root = self.git_root if dedicated else os.path.join(self.git_root, "notes")
        os.makedirs(self.root, exist_ok=True)
        cfg = dict(CONFIG)
        cfg.update(config or {})
        self.write("config.json", json.dumps(cfg))
        self.write("STATE.md", "# State\n")
        self.ctx = self.load()

    def load(self):
        return notes.Ctx(self.root, self.git_root, notes.load_config(self.root))

    def write(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def decision(self, stem, status="open", **extra):
        fm = dict(title='"%s"' % stem, type="decision", status=status, area="billing", summary="Use a queue.")
        if status in ("open", "proposed"):
            fm["waiting-on"] = "[bob]"
        if status in ("accepted", "rejected"):
            fm["decided-by"] = "bob"
        fm.update(extra)
        return self.write("decisions/%s.md" % stem, header(**fm) + "\n# t\n\nSee [[STATE]].\n")

    def bug(self, stem, status="open", body="See [[STATE]].\n", **extra):
        fm = dict(title='"%s"' % stem, type="bug", status=status, area="export", summary="Export fails.",
                  severity="high")
        fm.update(extra)
        return self.write("bugs/%s.md" % stem, header(**fm) + "\n# t\n\n" + body)

    def issues(self, **kw):
        return notes.check(self.ctx, **kw)[0]

    def msgs(self, **kw):
        return [i["msg"] for i in self.issues(**kw)]


class Base(unittest.TestCase):
    dedicated = False

    def setUp(self):
        silence(self)
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Tree(self.tmp.name, self.dedicated)

    def tearDown(self):
        self.tmp.cleanup()

    def has(self, text, **kw):
        found = [m for m in self.t.msgs(**kw) if text in m]
        self.assertTrue(found, "no issue containing %r in %r" % (text, self.t.msgs(**kw)))


class HeaderTest(unittest.TestCase):
    def test_flat_inline_and_block_lists(self):
        fm, body, err = notes.parse_header(
            "---\ntitle: \"A: b\"\ntags: [x, \"y z\"]\narea:\n  - billing\n  - export\nempty:\nnone: []\n---\nbody\n")
        self.assertIsNone(err)
        self.assertEqual(fm["title"], "A: b")
        self.assertEqual(fm["tags"], ["x", "y z"])
        self.assertEqual(fm["area"], ["billing", "export"])
        self.assertEqual(fm["none"], [])
        self.assertEqual(notes.scalar(fm["empty"]), "")
        self.assertEqual(body, "body\n")

    def test_unsupported_syntax_is_refused_with_the_line(self):
        for bad in ("a: |\n  text", "a: {b: 1}", "a: &x 1", "a: [1,\n"):
            fm, _, err = notes.parse_header("---\n%s\n---\n" % bad)
            self.assertIsNotNone(err, bad)
            self.assertIn("not supported", err)

    def test_no_header(self):
        self.assertIn("no header", notes.parse_header("# just text\n")[2])
        self.assertIn("not closed", notes.parse_header("---\na: 1\n")[2])


class CheckTest(Base):
    def test_clean_tree_is_ok(self):
        self.t.decision("use-a-queue")
        self.t.bug("B1")
        notes.cmd_index(self.t.ctx, None)
        self.assertEqual(self.t.issues(), [])

    def test_missing_fields_and_vocabulary(self):
        self.t.write("decisions/odd.md", header(title="x", type="decision", status="maybe"))
        self.has("missing header field: summary")
        self.has("status 'maybe' is not one of")
        self.has("0 wikilink(s)")

    def test_type_must_match_folder_and_file_name(self):
        self.t.write("bugs/Not-An-Id.md", header(title="x", type="decision", status="open", summary="s",
                                                  area="billing", severity="low") + "\nSee [[STATE]]\n")
        self.has("type is decision but the note lives in bugs/")
        self.has("does not fit the bug naming")

    def test_summary_length_and_area(self):
        self.t.decision("long", summary="x" * 161, area="nowhere")
        self.has("summary is 161 characters")
        self.has("area 'nowhere' is not in config.json areas")

    def test_ownerless_and_plain_identifiers_only_warn(self):
        self.t.write("decisions/w.md", header(title="w", type="decision", status="open", area="billing",
                                              summary="s") + "\nSee [[STATE]] and B7.\n")
        notes.cmd_index(self.t.ctx, None)
        issues = [i for i in self.t.issues() if i["path"] == "decisions/w.md"]
        self.assertEqual(len(issues), 2)
        self.assertTrue(all(i["soft"] for i in issues))
        out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "notes.py"), "check", "notes/decisions/w.md"],
                             cwd=self.t.git_root, env=dict(os.environ, NOTES_DIR=self.t.root),
                             stdout=subprocess.PIPE, universal_newlines=True)
        self.assertIn("WARN  decisions/w.md: no waiting-on", out.stdout)
        self.assertEqual(out.returncode, 0)

    def test_links(self):
        self.t.bug("B1", body="See [[missing-note]] and solves:: [[STATE]] and fixes:: [[STATE]] and B2 here.\n")
        self.has("broken link: [[missing-note]]")
        self.has("unknown relation 'fixes::'")
        self.has("identifier written as plain text")

    def test_archived_notes_still_resolve(self):
        self.t.bug("B2", status="fixed")
        notes.cmd_archive(self.t.ctx, type("A", (), {"ids": ["B2"]}))
        self.t.bug("B3", body="Same cause as [[B2]].\n")
        self.assertFalse([m for m in self.t.msgs() if "broken link" in m])

    def test_decision_needs_decider_and_owner_of_the_wait(self):
        self.t.decision("a", status="accepted", **{"decided-by": "carol"})
        self.has("decided-by: 'carol' is not in config.json people")
        self.t.write("decisions/b.md", header(title="b", type="decision", status="proposed", area="billing",
                                              summary="s") + "\nSee [[STATE]]\n")
        self.has("no waiting-on")
        self.t.write("decisions/c.md", header(title="c", type="decision", status="accepted", area="billing",
                                              summary="s") + "\nSee [[STATE]]\n")
        self.has("missing header field: decided-by")

    def test_bug_severity_and_unknown_person(self):
        self.t.bug("B1", severity="huge")
        self.has("severity must be one of")
        self.t.decision("w", **{"waiting-on": "[dave]"})
        self.has("waiting-on: 'dave' is not in config.json people")

    def test_category_is_optional_until_configured(self):
        self.t.decision("a")
        self.assertFalse([m for m in self.t.msgs() if "category" in m])
        self.t.write("config.json", json.dumps(dict(CONFIG, categories=["product", "money"])))
        self.t.ctx = self.t.load()
        self.has("category must be one of: product, money")

    def test_code_paths(self):
        os.makedirs(os.path.join(self.t.git_root, "src"))
        open(os.path.join(self.t.git_root, "src", "a.py"), "w").close()
        self.t.bug("B1", code="[src/a.py, Billing.charge, src/gone.py]")
        msgs = self.t.msgs()
        self.assertIn("code path not found: src/gone.py", msgs)
        self.assertFalse([m for m in msgs if "a.py" in m or "Billing" in m])

    def test_duplicate_names_and_conflict_copies(self):
        self.t.bug("B1")
        self.t.write("archive/bugs/B1.md", slurp(os.path.join(self.t.root, "bugs", "B1.md")))
        self.t.write("bugs/B1 2.md", "x")
        self.has("duplicate note name 'B1'")
        self.has("conflict copy")

    def test_secrets_and_personal_data_are_hard_errors(self):
        samples = {
            "key": "-----BEGIN RSA PRIVATE KEY-----",
            "gh": "ghp_" + "a" * 30,
            "aws": "AKIA" + "A" * 16,
            "sk": "sk-" + "b" * 24,
            "slack": "xoxb-1234567890-abcdef",
            "bearer": "Authorization: Bearer abcdefghijklmnop1234",
            "assign": "password: hunter2hunter2",
            "mail": "write to jane.doe@gmail.com",
        }
        for name, text in samples.items():
            self.t.bug("B1", body="See [[STATE]]. %s\n" % text)
            hard = [i for i in self.t.issues() if i["hard"]]
            self.assertTrue(hard, name)
            # not even the warn mode lets it through
            self.assertTrue([i for i in self.t.issues(warn=True) if i["hard"]], name)

    def test_harmless_text_passes_the_scan(self):
        self.t.bug("B1", body="See [[STATE]]. password: reset flow, token: <your-token>, mail ops@acme.test, "
                              "a@example.com, secret: xxxxxxxx\n")
        self.assertEqual([i for i in self.t.issues() if i["hard"]], [])

    def test_index_must_be_fresh(self):
        self.t.bug("B1")
        self.has("index is missing")
        notes.cmd_index(self.t.ctx, None)
        self.assertEqual(self.t.issues(), [])
        self.t.bug("B1", summary="Export fails twice.")
        self.has("index is out of date")

    def test_warn_mode_downgrades_header_errors_only(self):
        self.t.bug("B1", severity="huge")
        errs = [i for i in self.t.issues(warn=True)]
        self.assertTrue(errs and not any(i["hard"] for i in errs))
        ctx = self.t.ctx
        self.assertEqual(notes.check(ctx, warn=True)[2], "warn")

    def test_staged_mode_looks_only_at_staged_notes(self):
        self.t.bug("B1", severity="huge")
        self.t.bug("B2")
        git(self.t.git_root, "add", "notes/bugs/B2.md")
        msgs = self.t.msgs(staged=True)
        self.assertFalse([m for m in msgs if "severity" in m])

    def test_local_only_folder_cannot_be_committed(self):
        self.t.write("local/people.md", "private\n")
        git(self.t.git_root, "add", "-f", "notes/local/people.md")
        self.has("local-only", staged=True)

    def test_local_names_are_not_broken_links(self):
        self.t.write("local-names.txt", "# local notes\nalice-private\n")
        self.t.bug("B1", body="See [[alice-private]] and [[STATE]].\n")
        self.assertFalse([m for m in self.t.msgs() if "broken link" in m])


class RedZoneTest(Base):
    dedicated = True

    def test_the_first_commit_of_a_new_notes_repo_may_create_red_files(self):
        git(self.t.git_root, "add", ".")
        self.assertFalse([m for m in self.t.msgs(staged=True) if "red zone" in m])

    def test_red_file_on_the_default_branch_needs_a_pull_request(self):
        git(self.t.git_root, "add", ".")
        git(self.t.git_root, "commit", "-q", "-m", "init")
        self.t.write("config.json", json.dumps(dict(CONFIG, stale_days=10)))
        git(self.t.git_root, "add", "config.json")
        self.has("red zone", staged=True)
        git(self.t.git_root, "switch", "-q", "-c", "feat/x")
        self.assertFalse([m for m in self.t.msgs(staged=True) if "red zone" in m])


class WriteTest(Base):
    def new(self, *argv):
        args = notes.build_parser().parse_args(["new"] + list(argv))
        return notes.cmd_new(self.t.ctx, args)

    def test_new_numbers_and_slugs(self):
        self.new("bug", "Export fails", "--area", "export", "--severity", "high")
        self.new("bug", "Second one")
        self.new("decision", "Use a Queue!", "--waiting-on", "bob")
        self.new("message", "Reset staging?", "--to", "bob")
        names = sorted(os.listdir(os.path.join(self.t.root, "bugs")))
        self.assertEqual(names, ["B1.md", "B2.md"])
        self.assertTrue(os.path.isfile(os.path.join(self.t.root, "decisions", "use-a-queue.md")))
        self.assertTrue(os.path.isfile(os.path.join(self.t.root, "messages", "2026-10-28-reset-staging.md")))
        text = slurp(os.path.join(self.t.root, "bugs", "B1.md"))
        fm, _, err = notes.parse_header(text)
        self.assertIsNone(err)
        self.assertEqual((fm["status"], fm["created"], fm["severity"]), ("open", "2026-10-28", "high"))

    def test_new_note_fails_the_gate_until_it_is_filled_in(self):
        self.new("decision", "Retry policy", "--area", "export", "--waiting-on", "bob")
        self.assertTrue([m for m in self.t.msgs() if "summary" in m])

    def test_new_refuses_an_existing_name_and_warns_about_a_similar_one(self):
        self.new("decision", "Retry policy", "--waiting-on", "bob")
        with self.assertRaises(notes.Refused):
            self.new("decision", "Retry policy")
        out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "notes.py"), "new", "decision",
                              "Retry policy for exports"], cwd=self.t.git_root, env=dict(os.environ, NOTES_DIR=self.t.root),
                             stdout=subprocess.PIPE, universal_newlines=True).stdout
        self.assertIn("a similar note exists", out)

    def test_unknown_type(self):
        with self.assertRaises(notes.Refused):
            self.new("rumour", "x")

    def test_number_counts_upstream_and_archive(self):
        origin = os.path.join(self.tmp.name, "origin.git")
        git(self.tmp.name, "init", "-q", "--bare", "-b", "main", origin)
        git(self.t.git_root, "remote", "add", "origin", origin)
        self.t.bug("B4")
        git(self.t.git_root, "add", ".")
        git(self.t.git_root, "commit", "-q", "-m", "one")
        git(self.t.git_root, "push", "-q", "-u", "origin", "main")
        other = os.path.join(self.tmp.name, "other")
        git(self.tmp.name, "clone", "-q", origin, other)
        git(other, "config", "user.email", "b@example.com")
        git(other, "config", "user.name", "Bob B")
        with open(os.path.join(other, "notes", "bugs", "B5.md"), "w") as f:
            f.write("x")
        git(other, "add", ".")
        git(other, "commit", "-q", "-m", "two")
        git(other, "push", "-q")
        self.new("bug", "mine")  # fetches, sees B5 upstream
        self.assertTrue(os.path.isfile(os.path.join(self.t.root, "bugs", "B6.md")))

    def test_renumber_a_new_note_and_its_links(self):
        origin = os.path.join(self.tmp.name, "origin.git")
        git(self.tmp.name, "init", "-q", "--bare", "-b", "main", origin)
        git(self.t.git_root, "remote", "add", "origin", origin)
        self.t.bug("B1")
        git(self.t.git_root, "add", ".")
        git(self.t.git_root, "commit", "-q", "-m", "one")
        git(self.t.git_root, "push", "-q", "-u", "origin", "main")
        self.t.bug("B1x")
        os.rename(os.path.join(self.t.root, "bugs", "B1x.md"), os.path.join(self.t.root, "bugs", "B2.md"))
        self.t.write("decisions/d.md", header(title="d", type="decision", status="accepted", area="billing",
                                              summary="s", **{"decided-by": "bob"}) + "\nSolves [[B2]] and [[STATE]].\n")
        # B1 is committed: refused; B2 is new: renumbered to the next free number
        with self.assertRaises(notes.Refused):
            notes.cmd_renumber(self.t.ctx, type("A", (), {"id": "B1"}))
        os.makedirs(os.path.join(self.t.root, "archive", "bugs"))
        self.t.write("archive/bugs/B7.md", "x")
        notes.cmd_renumber(self.t.ctx, type("A", (), {"id": "B2"}))
        self.assertTrue(os.path.isfile(os.path.join(self.t.root, "bugs", "B8.md")))
        self.assertIn("[[B8]]", slurp(os.path.join(self.t.root, "decisions", "d.md")))


class QueryTest(Base):
    def setUp(self):
        Base.setUp(self)
        t = self.t
        t.decision("use-a-queue", status="proposed")
        t.decision("old-idea", status="rejected")
        t.bug("B1", body="Caused by [[use-a-queue]]. solves:: [[old-idea]]\n", code="[src/export/writer.py]")
        t.bug("B2", status="fixed", area="billing")
        self.ctx = t.ctx

    def run_cmd(self, fn, **kw):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            fn(self.ctx, type("A", (), kw))
        return buf.getvalue()

    def find(self, *conds, **kw):
        return self.run_cmd(notes.cmd_find, conds=list(conds), text=kw.get("text"), archive=kw.get("archive", False),
                            json=kw.get("json", False))

    def test_find_filters_on_any_header_field(self):
        out = self.find("type=decision", "status=proposed,open")
        self.assertIn("use-a-queue", out)
        self.assertNotIn("old-idea", out)
        self.assertIn("B1", self.find("area=export", "severity=high"))
        self.assertIn("use-a-queue", self.find("waiting-on=bob"))
        self.assertIn("B1", self.find(text="export fails"))
        self.assertIn("nothing found", self.find("status=nope"))

    def test_archive_is_hidden_unless_asked(self):
        notes.cmd_archive(self.ctx, type("A", (), {"ids": ["B2"]}))
        self.assertNotIn("B2", self.find("type=bug"))
        self.assertIn("B2", self.find("type=bug", archive=True))

    def test_show_related_area_code(self):
        out = self.run_cmd(notes.cmd_show, id="B1")
        self.assertIn("links out:", out)
        self.assertIn("old-idea (solves)", out)
        self.assertIn("B1", self.run_cmd(notes.cmd_show, id="use-a-queue").split("links in:")[1])
        rel = self.run_cmd(notes.cmd_related, id="B1", depth=2)
        self.assertIn("use-a-queue", rel)
        self.assertIn("B1", self.run_cmd(notes.cmd_area, name="export"))
        self.assertIn("B1", self.run_cmd(notes.cmd_code, path="src/export/writer.py"))
        self.assertIn("B1", self.run_cmd(notes.cmd_code, path="src/export"))
        self.assertIn("no note mentions", self.run_cmd(notes.cmd_code, path="src/other"))

    def test_archive_refuses_open_notes_and_big_batches(self):
        with self.assertRaises(notes.Refused):
            notes.cmd_archive(self.ctx, type("A", (), {"ids": ["B1"]}))
        with self.assertRaises(notes.Refused):
            notes.cmd_archive(self.ctx, type("A", (), {"ids": ["x%d" % i for i in range(21)]}))
        notes.cmd_archive(self.ctx, type("A", (), {"ids": ["B2", "old-idea"]}))
        self.assertTrue(os.path.isfile(os.path.join(self.t.root, "archive", "bugs", "B2.md")))
        self.assertTrue(os.path.isfile(os.path.join(self.t.root, "archive", "decisions", "old-idea.md")))

    def test_archive_uses_git_mv_for_tracked_notes(self):
        git(self.t.git_root, "add", ".")
        git(self.t.git_root, "commit", "-q", "-m", "x")
        notes.cmd_archive(self.ctx, type("A", (), {"ids": ["B2"]}))
        self.assertIn("R  notes/bugs/B2.md -> notes/archive/bugs/B2.md", git(self.t.git_root, "status", "--short"))

    def test_index_groups_by_status_and_includes_archived(self):
        notes.cmd_archive(self.ctx, type("A", (), {"ids": ["B2"]}))
        notes.cmd_index(self.ctx, None)
        text = slurp(os.path.join(self.t.root, "bugs", "_index.md"))
        self.assertIn("## open (1)", text)
        self.assertIn("## fixed (1)", text)
        self.assertIn("[[B2]]", text)
        self.assertTrue(text.startswith("<!-- generated"))

    def test_graph_is_deterministic(self):
        out = os.path.join(self.tmp.name, "g.json")
        notes.cmd_graph(self.ctx, type("A", (), {"out": out}))
        first = slurp(out)
        notes.cmd_graph(self.ctx, type("A", (), {"out": out}))
        self.assertEqual(first, slurp(out))
        data = json.loads(first)
        self.assertIn({"source": "B1", "target": "old-idea", "relation": "solves", "via": "typed",
                       "provenance": "EXTRACTED"}, data["edges"])
        self.assertTrue([n for n in data["nodes"] if n["id"] == "code:src/export/writer.py"])

    def test_health_numbers(self):
        self.t.write("decisions/ownerless.md", header(title="o", type="decision", status="open", area="billing",
                                                      summary="s", updated="2026-08-01") + "\nSee [[STATE]]\n")
        h = notes.health(self.ctx)
        self.assertEqual(h["notes"], {"decision": 3, "bug": 2})
        self.assertEqual(h["ownerless_decisions"], 1)
        self.assertEqual(h["ownerless_oldest"], "ownerless")
        self.assertEqual(h["stale"], 1)
        self.assertTrue(h["failing_check"] >= 1)
        self.assertEqual(h["state_bytes"], len("# State\n"))
        self.run_cmd(notes.cmd_health, save=True, json=False, prs=False)
        self.assertTrue(os.path.isfile(os.path.join(self.t.root, ".notes", "health.jsonl")))

    def test_whoami(self):
        self.assertEqual(notes.whoami(self.ctx), "alice")  # from git user.name
        notes.cmd_whoami(self.ctx, type("A", (), {"set": "bob"}))
        self.assertEqual(notes.whoami(self.ctx), "bob")
        with self.assertRaises(notes.Refused):
            notes.cmd_whoami(self.ctx, type("A", (), {"set": "carol"}))
        os.environ["NOTES_ME"] = "alice"
        try:
            self.assertEqual(notes.whoami(self.ctx), "alice")
        finally:
            del os.environ["NOTES_ME"]


class CliTest(Base):
    def test_cli_exit_codes(self):
        self.t.decision("a")
        env = dict(os.environ, NOTES_DIR=self.t.root)
        def cli(*a):
            p = subprocess.run([sys.executable, os.path.join(SCRIPTS, "notes.py")] + list(a), cwd=self.t.git_root,
                               env=env, stdout=subprocess.PIPE, universal_newlines=True)
            return p.returncode, p.stdout
        rc, out = cli("check")
        self.assertEqual(rc, 1)
        self.assertIn("index is missing", out)
        self.assertEqual(cli("index")[0], 0)
        self.assertEqual(cli("check")[0], 0)
        self.assertEqual(cli("archive", "a")[0], 2)
        env["NOTES_DIR"] = os.path.join(self.tmp.name, "nowhere")
        self.assertEqual(cli("check")[0], 2)


if __name__ == "__main__":
    unittest.main()
