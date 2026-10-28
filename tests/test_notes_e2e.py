"""End-to-end scenario for the team notes: templates, scripts, hook, two people, one origin.

Run: python3 -m unittest discover -s tests
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETUP = os.path.join(ROOT, "plugins", "agentic-code", "skills", "project-setup", "templates")
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
ENV.update(NOTES_TODAY="2026-10-28", GIT_CONFIG_NOSYSTEM="1")
ENV.pop("NOTES_GATE", None)
ENV.pop("NOTES_ME", None)


def sh(cwd, *args, **env):
    e = dict(ENV, **env)
    p = subprocess.run(args, cwd=cwd, env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    return p.returncode, p.stdout


def slurp(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def spit(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class Person(object):
    def __init__(self, root, name):
        self.root, self.name = root, name

    def notes(self, *args, **env):
        return sh(self.root, sys.executable, "scripts/notes.py", *args, **env)

    def team(self, *args, **env):
        return sh(self.root, sys.executable, "scripts/notes_team.py", *args, **env)

    def git(self, *args, **env):
        return sh(self.root, "git", *args, **env)

    def path(self, rel):
        return os.path.join(self.root, rel)

    def fill(self, rel, summary, status=None, extra=None):
        text = slurp(self.path(rel))
        text = text.replace("summary: \n", "summary: %s\n" % summary).replace("Related: \n", "Related: [[STATE]]\n")
        if status:
            text = text.replace("status: open\n", "status: %s\n" % status, 1)
        for old, new in (extra or {}).items():
            text = text.replace(old, new)
        spit(self.path(rel), text)


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = self.tmp.name
        origin = os.path.join(base, "origin.git")
        sh(base, "git", "init", "-q", "--bare", "-b", "main", origin)
        seed = os.path.join(base, "alice")
        sh(base, "git", "init", "-q", "-b", "main", seed)
        # the repo as project-setup would build it for a separate notes repo (tier L2)
        for name in ("STATE.md", "CLAUDE.md", "README.md"):
            shutil.copy(os.path.join(SETUP, "notes", name), seed)
        os.makedirs(os.path.join(seed, "scripts"))
        for name in ("notes.py", "notes_team.py"):
            shutil.copy(os.path.join(SETUP, "scripts", name), os.path.join(seed, "scripts", name))
        os.makedirs(os.path.join(seed, ".githooks"))
        shutil.copy(os.path.join(SETUP, "githooks", "pre-commit-notes"), os.path.join(seed, ".githooks", "pre-commit"))
        os.chmod(os.path.join(seed, ".githooks", "pre-commit"), 0o755)
        shutil.copy(os.path.join(SETUP, "notes", "gitignore.txt"), os.path.join(seed, ".gitignore"))
        shutil.copy(os.path.join(SETUP, "notes", "gitattributes.txt"), os.path.join(seed, ".gitattributes"))
        shutil.copy(os.path.join(SETUP, "notes", "local-names.txt"), os.path.join(seed, "local-names.txt"))
        cfg = json.loads(slurp(os.path.join(SETUP, "notes", "config.json")))
        cfg.update(people={"alice": {"names": ["Alice A"]}, "bob": {"names": ["Bob B"]}},
                   areas={"export": {"owner": "bob"}, "billing": {"owner": "alice"}}, auto_push=True,
                   zones={"green": ["decisions/*", "bugs/*", "tasks/*", "messages/*", "STATE.md"],
                          "red": ["config.json", "scripts/**", ".githooks/**"]})
        spit(os.path.join(seed, "config.json"), json.dumps(cfg, indent=1))
        sh(seed, "git", "config", "user.email", "alice@example.com")
        sh(seed, "git", "config", "user.name", "Alice A")
        sh(seed, "git", "config", "core.hooksPath", ".githooks")
        sh(seed, "git", "add", ".")
        rc, out = sh(seed, "git", "commit", "-q", "-m", "init")
        self.assertEqual(rc, 0, out)
        sh(seed, "git", "remote", "add", "origin", origin)
        sh(seed, "git", "push", "-q", "-u", "origin", "main")
        sh(origin, "git", "symbolic-ref", "HEAD", "refs/heads/main")
        bob_path = os.path.join(base, "bob")
        sh(base, "git", "clone", "-q", origin, bob_path)
        sh(bob_path, "git", "config", "user.email", "bob@example.com")
        sh(bob_path, "git", "config", "user.name", "Bob B")
        sh(bob_path, "git", "config", "core.hooksPath", ".githooks")
        self.alice, self.bob = Person(seed, "alice"), Person(bob_path, "bob")

    def tearDown(self):
        self.tmp.cleanup()

    def test_scenario(self):
        a, b = self.alice, self.bob
        # 1. a fresh tree is green and healthy
        rc, out = a.notes("check")
        self.assertEqual((rc, out.strip()), (0, "OK"), out)
        rc, out = a.notes("health")
        self.assertIn("ownerless open decisions: 0", out)
        self.assertEqual(b.team("inbox")[0], 0)  # sets bob's stamp

        # 2. alice asks bob for a decision; bob's start-of-work digest shows it
        rc, out = a.notes("new", "decision", "Retry policy for exports", "--area", "export", "--waiting-on", "bob")
        self.assertEqual(rc, 0, out)
        a.fill("decisions/retry-policy-for-exports.md", "Exports retry three times, then fail loudly.")
        self.assertEqual(a.notes("index")[0], 0)
        rc, out = a.team("save", "propose retry policy", "decisions/retry-policy-for-exports.md", "decisions/_index.md")
        self.assertEqual(rc, 0, out)
        self.assertIn("saved and pushed", out)
        rc, out = b.team("inbox")
        self.assertIn("WAITING FOR YOU (1):", out)
        self.assertIn("Retry policy for exports", out)
        self.assertIn("notes: alice 1 commit(s)", out)

        # 3. bob accepts; the gate wants to know who decided
        b.fill("decisions/retry-policy-for-exports.md", "Exports retry three times, then fail loudly.",
               extra={"status: open\n": "status: accepted\n", "waiting-on: [bob]\n": ""})
        b.notes("index")
        rc, out = b.team("save", "accept", "decisions/retry-policy-for-exports.md", "decisions/_index.md")
        self.assertEqual(rc, 2, out)
        self.assertIn("decided-by", out)
        text = slurp(b.path("decisions/retry-policy-for-exports.md")).replace("created:", "decided-by: bob\ncreated:")
        spit(b.path("decisions/retry-policy-for-exports.md"), text)
        b.notes("index")
        rc, out = b.team("save", "accept", "decisions/retry-policy-for-exports.md", "decisions/_index.md")
        self.assertEqual(rc, 0, out)
        self.assertIn("decision retry-policy-for-exports -> accepted (bob)", a.team("inbox")[1])

        # 4. both create a bug while offline from each other: the number is taken upstream
        for p in (a, b):
            sh(p.root, "git", "remote", "rename", "origin", "gone")  # no fetch: the two do not see each other's B1
            rc, out = p.notes("new", "bug", "Export timeout %s" % p.name, "--area", "export", "--severity", "high")
            self.assertEqual(rc, 0, out)
            p.fill("bugs/B1.md", "The export times out for %s." % p.name)
            p.notes("index")
            sh(p.root, "git", "remote", "rename", "gone", "origin")
        self.assertEqual(a.team("save", "bug", "bugs/B1.md", "bugs/_index.md")[0], 0)
        rc, out = b.team("save", "bug", "bugs/B1.md", "bugs/_index.md")
        self.assertEqual(rc, 2, out)
        self.assertIn("already exists upstream", out)
        rc, out = b.notes("renumber", "B1")
        self.assertIn("B1 -> B2", out)
        b.notes("index")
        rc, out = b.team("save", "bug", "bugs/B2.md", "bugs/_index.md")
        self.assertEqual(rc, 0, out)
        self.assertEqual(b.notes("check")[0], 0)

        # 5. a message thread: both append at the same time, nothing is lost
        rc, out = a.notes("new", "message", "Reset staging?", "--to", "bob")
        a.fill("messages/2026-10-28-reset-staging.md", "Alice asks whether staging may be reset.", extra={
            "area: \n": "area: export\n"})
        self.assertEqual(a.team("save", "ask", "messages/2026-10-28-reset-staging.md")[0], 0)
        self.assertIn("Reset staging?", b.team("inbox")[1])
        for p, line in ((a, "alice -> bob: tonight?"), (b, "bob -> alice: after 5pm")):
            with open(p.path("messages/2026-10-28-reset-staging.md"), "a") as f:
                f.write("2026-10-28 · %s\n" % line)
        self.assertEqual(b.team("save", "reply", "messages/2026-10-28-reset-staging.md")[0], 0)
        rc, out = a.team("save", "reply", "messages/2026-10-28-reset-staging.md")
        self.assertEqual(rc, 0, out)
        thread = slurp(a.path("messages/2026-10-28-reset-staging.md"))
        self.assertIn("tonight?", thread)
        self.assertIn("after 5pm", thread)

        # 6. the hook stops a red-zone file on main, and a secret, even with the escape hatch
        spit(a.path("config.json"), slurp(a.path("config.json")).replace('"stale_days": 30', '"stale_days": 10'))
        a.git("add", "config.json")
        rc, out = a.git("commit", "-q", "-m", "tune")
        self.assertNotEqual(rc, 0)
        self.assertIn("red zone", out)
        a.git("reset", "-q", "HEAD", "config.json")
        a.git("checkout", "--", "config.json")
        a.notes("new", "bug", "Leaky note", "--area", "export", "--severity", "low")
        a.fill("bugs/B3.md", "A note with a token.")
        with open(a.path("bugs/B3.md"), "a") as f:
            f.write("token: ghp_" + "a" * 30 + "\n")
        a.notes("index")
        a.git("add", "bugs/B3.md", "bugs/_index.md")
        for gate in ("block", "warn"):
            rc, out = a.git("commit", "-q", "-m", "leak", NOTES_GATE=gate)
            self.assertNotEqual(rc, 0, gate)
            self.assertIn("looks like a secret", out)
        a.git("reset", "-q")
        os.remove(a.path("bugs/B3.md"))
        a.notes("index")
        a.git("checkout", "--", "bugs/_index.md")

        # 7. an old ownerless decision shows up in the digest and in the tidy baskets; closed notes archive
        spit(a.path("decisions/cache-ttl.md"), "---\ntitle: Cache TTL\ntype: decision\nstatus: open\narea: billing\n"
             "summary: How long may the price cache live?\ncreated: 2026-08-01\nupdated: 2026-08-01\n---\n\n"
             "Related: [[STATE]]\n")
        rc, out = a.team("inbox")
        self.assertIn("OWNERLESS: 1 open decision(s) without waiting-on (oldest: cache-ttl, 88 days)", out)
        self.assertIn("TIDY:", out)
        rc, out = a.team("tidy")
        self.assertIn("ownerless (open, no waiting-on): 1\n  cache-ttl (88 days)", out)
        text = slurp(a.path("bugs/B1.md")).replace("status: open\n", "status: fixed\n")
        spit(a.path("bugs/B1.md"), text)
        self.assertIn("1 archivable (closed, still in place): 1", a.team("tidy")[1])
        rc, out = a.notes("archive", "B1")
        self.assertEqual(rc, 0, out)
        self.assertTrue(os.path.isfile(a.path("archive/bugs/B1.md")))
        a.notes("index")
        rc, out = a.notes("check")
        self.assertIn("WARN  decisions/cache-ttl.md: no waiting-on", out)  # ownerless is a warning, not a stop
        self.assertEqual(rc, 0)

        # 8. health numbers and the graph
        rc, out = a.notes("health", "--json")
        h = json.loads(out)
        self.assertEqual(h["ownerless_decisions"], 1)
        self.assertEqual(h["stale"], 1)
        self.assertEqual(a.notes("graph")[0], 0)
        self.assertTrue(os.path.isfile(a.path(".notes/graph.json")))
        self.assertNotIn(".notes", a.git("status", "--short")[1])  # ignored


if __name__ == "__main__":
    unittest.main()
