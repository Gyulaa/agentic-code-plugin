"""Tests for notes_team.py: two people, one bare origin. Run: python3 -m unittest discover -s tests"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

try:
    from test_notes import CONFIG, SCRIPTS, git, header, silence, slurp
except ImportError:
    from tests.test_notes import CONFIG, SCRIPTS, git, header, silence, slurp

import notes  # noqa: E402  (test_notes put the scripts folder on sys.path)
import notes_team  # noqa: E402

TEAM_CONFIG = dict(CONFIG, auto_push=True)


class Peer(object):
    def __init__(self, path, name):
        self.root = path
        git(path, "config", "user.email", name.lower().replace(" ", ".") + "@example.com")
        git(path, "config", "user.name", name)

    @property
    def ctx(self):
        return notes.Ctx(self.root, self.root, notes.load_config(self.root))

    def write(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def decision(self, stem, status="open", **extra):
        fm = dict(title='"%s"' % stem, type="decision", status=status, area="billing", summary="Use a queue.",
                  created="2026-10-20", updated="2026-10-20")
        if status in ("open", "proposed"):
            fm["waiting-on"] = "[bob]"
        if status in ("accepted", "rejected"):
            fm["decided-by"] = "bob"
        fm.update(extra)
        return self.write("decisions/%s.md" % stem, "---\n" + "".join("%s: %s\n" % kv for kv in fm.items()) +
                          "---\n\n# t\n\nSee [[STATE]].\n")

    def say(self, fn, **kw):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                rc = fn(self.ctx, type("A", (), kw))
            except notes.Refused as e:
                rc = "refused: %s" % e
        return rc, buf.getvalue()

    def save(self, message, *files):
        return self.say(notes_team.cmd_save, message=message, files=[os.path.join(self.root, f) for f in files])

    def inbox(self, since=None):
        return self.say(notes_team.cmd_inbox, since=since)[1]


class TeamCase(unittest.TestCase):
    config = TEAM_CONFIG

    def setUp(self):
        silence(self)
        self.tmp = tempfile.TemporaryDirectory()
        base = self.tmp.name
        self.origin = os.path.join(base, "origin.git")
        git(base, "init", "-q", "--bare", "-b", "main", self.origin)
        seed = os.path.join(base, "alice")
        git(base, "init", "-q", "-b", "main", seed)
        self.alice = Peer(seed, "Alice A")
        self.alice.write("config.json", json.dumps(self.config))
        self.alice.write("STATE.md", "# State\n")
        self.alice.write(".gitattributes", "messages/*.md merge=union\n")
        self.alice.write(".gitignore", ".notes-me\n.notes/\n")
        git(seed, "add", ".")
        git(seed, "commit", "-q", "-m", "init")
        git(seed, "remote", "add", "origin", self.origin)
        git(seed, "push", "-q", "-u", "origin", "main")
        git(self.origin, "symbolic-ref", "HEAD", "refs/heads/main")
        bob_path = os.path.join(base, "bob")
        git(base, "clone", "-q", self.origin, bob_path)
        self.bob = Peer(bob_path, "Bob B")

    def tearDown(self):
        self.tmp.cleanup()


class SaveTest(TeamCase):
    def test_save_pushes_green_files_and_the_other_person_sees_the_wait(self):
        a = self.alice
        self.bob.inbox()  # sets bob's stamp
        a.decision("retry-policy", status="proposed")
        notes.cmd_index(a.ctx, None)
        rc, out = a.save("add retry policy", "decisions/retry-policy.md", "decisions/_index.md")
        self.assertEqual(rc, 0, out)
        self.assertIn("saved and pushed", out)
        out = self.bob.inbox()
        self.assertIn("WAITING FOR YOU (1):", out)
        self.assertIn("decision, proposed: retry-policy (retry-policy, 8 days)", out)
        self.assertIn("notes: alice 1 commit(s)", out)
        self.assertIn("decision retry-policy -> proposed (alice)", out)
        # the stamp: the next run has no news
        self.assertIn("nothing new", self.bob.inbox())

    def test_accepting_needs_the_decider_and_alice_sees_it(self):
        a, b = self.alice, self.bob
        a.decision("retry-policy", status="proposed")
        notes.cmd_index(a.ctx, None)
        a.save("add", "decisions/retry-policy.md", "decisions/_index.md")
        b.inbox()
        git(b.root, "pull", "-q")
        a.inbox()
        b.decision("retry-policy", status="accepted", **{"decided-by": ""})
        rc, out = b.save("accept", "decisions/retry-policy.md")
        self.assertTrue(str(rc).startswith("refused"), (rc, out))
        self.assertIn("decided-by", out)
        b.decision("retry-policy", status="accepted")
        notes.cmd_index(b.ctx, None)
        rc, out = b.save("accept", "decisions/retry-policy.md", "decisions/_index.md")
        self.assertEqual(rc, 0, out)
        out = a.inbox()
        self.assertIn("decision retry-policy -> accepted (bob)", out)
        self.assertIn("WAITING FOR YOU: nothing", out)

    def test_refusals(self):
        a = self.alice
        a.decision("x")
        a.write("decisions/x 2.md", "copy")
        rc, _ = a.save("m", "decisions/x 2.md")
        self.assertTrue(str(rc).startswith("refused: conflict copy"))
        rc, _ = a.save("m", "decisions/missing.md")
        self.assertTrue(str(rc).startswith("refused: no such file"))
        git(a.root, "switch", "-q", "-c", "feat/y")
        rc, _ = a.save("m", "decisions/x.md")
        self.assertTrue(str(rc).startswith("refused: the notes repo is on 'feat/y'"))

    def test_a_note_that_fails_the_check_is_not_committed(self):
        a = self.alice
        a.decision("bad", summary="")
        rc, out = a.save("m", "decisions/bad.md")
        self.assertTrue(str(rc).startswith("refused"))
        self.assertIn("summary", out)
        self.assertEqual(git(a.root, "log", "--oneline").count("\n"), 0)

    def test_a_number_taken_upstream_is_refused_and_renumber_fixes_it(self):
        a, b = self.alice, self.bob
        for p in (a, b):
            p.write("bugs/B1.md", "---\ntitle: x\ntype: bug\nstatus: open\narea: export\nsummary: s\nseverity: low\n"
                    "created: 2026-10-20\nupdated: 2026-10-20\n---\n\nSee [[STATE]].\n")
        notes.cmd_index(b.ctx, None)
        self.assertEqual(b.save("bob bug", "bugs/B1.md", "bugs/_index.md")[0], 0)
        rc, out = a.save("alice bug", "bugs/B1.md")
        self.assertTrue(str(rc).startswith("refused: bugs/B1.md already exists upstream"), (rc, out))
        a.write("decisions/d.md", "---\ntitle: d\ntype: decision\nstatus: accepted\narea: billing\nsummary: s\n"
                "decided-by: alice\ncreated: 2026-10-20\nupdated: 2026-10-20\n---\n\nSolves [[B1]] and [[STATE]].\n")
        rc, out = a.say(notes.cmd_renumber, id="B1")
        self.assertEqual(rc, 0, out)
        self.assertIn("B1 -> B2", out)
        notes.cmd_index(a.ctx, None)
        rc, out = a.save("alice bug", "bugs/B2.md", "decisions/d.md", "bugs/_index.md")
        self.assertEqual(rc, 0, out)
        self.assertIn("[[B2]]", slurp(os.path.join(a.root, "decisions", "d.md")))

    def test_two_people_adding_notes_at_once_do_not_fight_over_the_index(self):
        a, b = self.alice, self.bob
        a.decision("one", status="proposed")
        notes.cmd_index(a.ctx, None)
        self.assertEqual(a.save("one", "decisions/one.md", "decisions/_index.md")[0], 0)
        b.decision("two", status="proposed")  # bob has not pulled yet
        notes.cmd_index(b.ctx, None)
        rc, out = b.save("two", "decisions/two.md", "decisions/_index.md")
        self.assertEqual(rc, 0, out)
        self.assertIn("saved and pushed", out)
        index = slurp(os.path.join(b.root, "decisions", "_index.md"))
        self.assertIn("[[one]]", index)
        self.assertIn("[[two]]", index)
        self.assertEqual(notes.check(b.ctx)[0], [])
        self.assertEqual(git(b.root, "status", "--short"), "")
        self.assertEqual(git(b.root, "rev-parse", "HEAD"), git(self.origin, "rev-parse", "main"))

    def test_a_real_conflict_stops_and_a_second_save_is_refused(self):
        a, b = self.alice, self.bob
        a.decision("c", status="proposed")
        notes.cmd_index(a.ctx, None)
        a.save("c", "decisions/c.md", "decisions/_index.md")
        git(b.root, "pull", "-q")
        b.decision("c", status="proposed", summary="Bob's version.")
        notes.cmd_index(b.ctx, None)
        self.assertEqual(b.save("bob", "decisions/c.md", "decisions/_index.md")[0], 0)
        a.decision("c", status="proposed", summary="Alice's version.")
        notes.cmd_index(a.ctx, None)
        rc, out = a.save("alice", "decisions/c.md", "decisions/_index.md")
        self.assertEqual(rc, 1, out)
        self.assertIn("CONFLICT", out)
        rc, _ = a.save("again", "decisions/c.md")
        self.assertTrue(str(rc).startswith("refused: a rebase is in progress"))
        git(a.root, "rebase", "--abort")

    def test_messages_from_two_people_merge_without_a_conflict(self):
        a, b = self.alice, self.bob
        head = ("---\ntitle: Staging\ntype: message\nstatus: open\nto: [alice, bob]\nwaiting-on: [bob]\nsummary: s\n"
                "area: export\ncreated: 2026-10-27\nupdated: 2026-10-27\n---\n\nSee [[STATE]].\n\n")
        a.write("messages/2026-10-27-staging.md", head + "2026-10-27 · alice -> bob: reset staging?\n")
        self.assertEqual(a.save("m", "messages/2026-10-27-staging.md")[0], 0)
        git(b.root, "pull", "-q")
        with open(os.path.join(b.root, "messages", "2026-10-27-staging.md"), "a") as f:
            f.write("2026-10-28 · bob -> alice: yes, after 5pm\n")
        with open(os.path.join(a.root, "messages", "2026-10-27-staging.md"), "a") as f:
            f.write("2026-10-28 · alice -> bob: thanks, noted\n")
        self.assertEqual(b.save("bob replies", "messages/2026-10-27-staging.md")[0], 0)
        rc, out = a.save("alice replies", "messages/2026-10-27-staging.md")
        self.assertEqual(rc, 0, out)
        text = slurp(os.path.join(a.root, "messages", "2026-10-27-staging.md"))
        self.assertIn("yes, after 5pm", text)
        self.assertIn("thanks, noted", text)


class PushPolicyTest(TeamCase):
    def test_auto_push_off_and_red_zone_do_not_push(self):
        a = self.alice
        a.decision("one")
        notes.cmd_index(a.ctx, None)
        a.write("config.json", json.dumps(dict(self.config, auto_push=False)))
        git(a.root, "commit", "-q", "-am", "config")
        git(a.root, "push", "-q")
        rc, out = a.save("one", "decisions/one.md", "decisions/_index.md")
        self.assertEqual(rc, 0, out)
        self.assertIn("saved, not pushed (auto_push is off)", out)
        a.write("config.json", json.dumps(self.config))
        a.decision("two")
        notes.cmd_index(a.ctx, None)
        rc, out = a.save("two and config", "decisions/two.md", "config.json", "decisions/_index.md")
        self.assertIn("outside the green and yellow zones", out)


class YellowZoneTest(TeamCase):
    config = dict(TEAM_CONFIG, zones={"green": ["decisions/*"], "yellow": ["knowledge/*"]})

    def test_a_yellow_zone_change_by_someone_else_is_pointed_out(self):
        self.bob.inbox()
        self.alice.write("knowledge/export.md", "---\ntitle: Export\ntype: knowledge\nstatus: active\narea: export\n"
                         "summary: How exports work.\ncreated: 2026-10-28\nupdated: 2026-10-28\n---\n\nSee [[STATE]].\n")
        self.assertEqual(self.alice.save("how exports work", "knowledge/export.md")[0], 0)
        self.assertIn("changed in the yellow zone: knowledge/export.md (alice)", self.bob.inbox())


class InboxTest(TeamCase):
    def test_ownerless_stale_and_since(self):
        a = self.alice
        a.write("decisions/old.md", "---\ntitle: Old\ntype: decision\nstatus: open\narea: billing\nsummary: s\n"
                "created: 2026-08-01\nupdated: 2026-08-01\n---\n\nSee [[STATE]].\n")
        out = a.inbox(since="2026-10-01")
        self.assertIn("OWNERLESS: 1 open decision(s) without waiting-on (oldest: old, 88 days)", out)
        self.assertIn("TIDY: 1 open item(s) have not moved for 30 days", out)
        self.assertFalse(os.path.exists(notes_team.stamp_file(a.ctx)))  # --since does not move the stamp

    def test_unknown_person_is_said_out_loud(self):
        git(self.bob.root, "config", "user.name", "Somebody Else")
        self.assertIn("I do not know who you are", self.bob.inbox())

    def test_uncommitted_changes_stop_the_pull(self):
        git(self.bob.root, "checkout", "--", ".")
        with open(os.path.join(self.bob.root, "STATE.md"), "a") as f:
            f.write("local edit\n")
        self.assertIn("not pulled: you have uncommitted changes", self.bob.inbox())


class SnapshotAndTidyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = self.tmp.name
        origin = os.path.join(base, "api.git")
        git(base, "init", "-q", "--bare", "-b", "main", origin)
        api = os.path.join(base, "api")
        git(base, "clone", "-q", origin, api)
        git(api, "config", "user.email", "t@example.com")
        git(api, "config", "user.name", "Alice A")
        git(api, "checkout", "-q", "-b", "main")
        with open(os.path.join(api, "a.txt"), "w") as f:
            f.write("a")
        git(api, "add", ".")
        git(api, "commit", "-q", "-m", "init")
        git(api, "push", "-q", "-u", "origin", "main")
        git(api, "switch", "-q", "-c", "feat/export")
        with open(os.path.join(api, "b.txt"), "w") as f:
            f.write("b")
        git(api, "add", ".")
        git(api, "commit", "-q", "-m", "work")
        self.api = api
        self.notes = Peer(os.path.join(base, "api", "notes"), "Alice A") if False else None
        os.makedirs(os.path.join(api, "notes"))
        git(api, "switch", "-q", "main")
        git(api, "switch", "-q", "feat/export")
        cfg = dict(CONFIG, repos=[{"name": "api", "path": "api"}, {"name": "web", "path": "web"}])
        with open(os.path.join(api, "notes", "config.json"), "w") as f:
            json.dump(cfg, f)
        with open(os.path.join(api, "notes", "STATE.md"), "w") as f:
            f.write("# State\n")
        self.ctx = notes.Ctx(os.path.join(api, "notes"), api, notes.load_config(os.path.join(api, "notes")))
        self.ctx.cfg["workspace"] = ".."

    def tearDown(self):
        self.tmp.cleanup()

    def test_snapshot_lines(self):
        lines = notes_team.snapshot(self.ctx)
        self.assertEqual(lines[1], "- web: not cloned here")
        self.assertTrue(lines[0].startswith("- api: feat/export @"), lines)
        self.assertIn("not pushed", lines[0])
        self.assertIn("uncommitted", lines[0])  # the notes folder is untracked

    def test_tidy_baskets(self):
        def put(rel, text):
            p = os.path.join(self.ctx.root, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write(text)
        base = "area: billing\nsummary: s\ncreated: 2026-08-01\nupdated: %s\n---\n\n%s\n"
        put("decisions/fresh.md", "---\ntitle: Fresh\ntype: decision\nstatus: accepted\ndecided-by: bob\n" +
            base % ("2026-10-27", "See [[STATE]]. supersedes:: [[stale]]"))
        put("decisions/stale.md", "---\ntitle: Stale\ntype: decision\nstatus: accepted\ndecided-by: bob\n" +
            base % ("2026-08-01", "See [[STATE]]."))
        put("decisions/loose.md", "---\ntitle: Loose\ntype: decision\nstatus: open\n" + base % ("2026-08-01", "See [[STATE]]."))
        put("bugs/B1.md", "---\ntitle: Done\ntype: bug\nstatus: fixed\nseverity: low\n" + base % ("2026-10-01", "See [[STATE]]."))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            notes_team.cmd_tidy(self.ctx, None)
        out = buf.getvalue()
        self.assertIn("1 archivable (closed, still in place): 1\n  B1 (fixed)", out)
        self.assertIn("stale is accepted but fresh supersedes it -> superseded", out)
        self.assertIn("ownerless (open, no waiting-on): 1\n  loose (88 days)", out)
        self.assertIn("not moved for 30 days or more: 1", out)
        self.assertIn("header or link errors", out)


class MigrateTest(unittest.TestCase):
    DECISIONS = ("# Decisions\n\n## 2026-10-02 · Use a job queue\n- **Decision:** Exports run through a job queue. "
                 "More later.\n- **Why:** A request must not wait for a big export.\n- **Affects:** `exporter/`\n\n"
                 "## 2026-10-01 · Use a job queue\n- **Decision:** Same title again.\n\n"
                 "## {{DATE}} · {{DECISION_TITLE}}\n- **Decision:** {{WHAT}}\n\n## Odd heading\ntext\n")
    BUGS = ("# Bugs\n\n| ID | Severity | Status | What | Where | Origin |\n|---|---|---|---|---|---|\n"
            "| B3 | high | PR open | Export times out for big accounts. | `exporter/writer.py:88` | abc123 |\n"
            "| B1 | Medium | fixed | Typo in the footer. | - | - |\n"
            "| B2 | urgent | waiting | Odd row. | - | - |\n"
            "| B1 | {{critical}} | {{open}} | {{one line}} | `{{file:line}}` | {{commit}} |\n")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        git(root, "init", "-q", "-b", "main")
        for rel, text in (("docs/decisions.md", self.DECISIONS), ("docs/bugs.md", self.BUGS),
                          ("notes/STATE.md", "# State\n"), ("exporter/writer.py", "x = 1\n"),
                          ("notes/config.json", json.dumps({"areas": {}, "people": {}}))):
            p = os.path.join(root, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write(text)
        self.ctx = notes.Ctx(os.path.join(root, "notes"), root, notes.load_config(os.path.join(root, "notes")))

    def tearDown(self):
        self.tmp.cleanup()

    def run_migrate(self, apply):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            notes_team.cmd_migrate(self.ctx, type("A", (), {"apply": apply, "decisions": "docs/decisions.md",
                                                           "bugs": "docs/bugs.md"}))
        return buf.getvalue()

    def test_dry_run_writes_nothing(self):
        out = self.run_migrate(False)
        self.assertIn("would create decisions/use-a-job-queue.md", out)
        self.assertIn("would create decisions/use-a-job-queue-2.md", out)
        self.assertIn("would create bugs/B3.md", out)
        self.assertIn("dry run", out)
        self.assertFalse(os.path.exists(os.path.join(self.ctx.root, "decisions")))

    def test_apply_creates_notes_that_pass_the_gate(self):
        out = self.run_migrate(True)
        self.assertIn("manual: B2: status 'waiting' is not known", out)
        self.assertIn("manual: B2: severity 'urgent' is not known", out)
        self.assertIn("manual: docs/decisions.md: section 'Odd heading'", out)
        self.assertEqual(notes.check(self.ctx)[0], [], notes.check(self.ctx)[0])
        fm, _, _ = notes.parse_header(slurp(os.path.join(self.ctx.root, "bugs", "B3.md")))
        self.assertEqual((fm["status"], fm["severity"], fm["code"], fm["origin"]),
                         ("pr-open", "high", ["exporter/writer.py"], "abc123"))
        fm, body, _ = notes.parse_header(slurp(os.path.join(self.ctx.root, "decisions", "use-a-job-queue.md")))
        self.assertEqual((fm["status"], fm["decided-by"], fm["summary"]),
                         ("accepted", "team", "Exports run through a job queue."))
        self.assertIn("**Why:** A request must not wait", body)
        self.assertIn("_index.md", " ".join(os.listdir(os.path.join(self.ctx.root, "bugs"))))
        again = self.run_migrate(True)
        self.assertIn("exists, skipped", again)


if __name__ == "__main__":
    unittest.main()
