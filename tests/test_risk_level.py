"""Tests for risk_level.py (classification). Run: python3 -m unittest discover -s tests"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "agentic-code", "skills", "project-setup", "templates", "scripts",
                      "risk_level.py")

# An invented web shop.
MAP = {
    "skip": ["docs/**", "*.md", "*.png", "*.lock"],
    "test": ["tests/**", "**/*_test.py"],
    "critical": [
        {"glob": "shop/pricing*", "why": "prices"},
        {"glob": "shop/cart.py", "anchor": "total|price", "why": "cart totals"},
        {"glob": "shop/api.py", "server_twin": "storefront/api.js", "why": "API schema"},
    ],
    "sensitive": [
        {"glob": "shop/db/**", "why": "data layer"},
        {"content": r"\.write\(|save\(", "why": "writes data"},
    ],
    "normal": ["shop/**", "storefront/**", "ui/**", "scripts/risk-map.json"],
    "ui": ["ui/**"],
    "areas": {"depth": 1},
}


def lines(n, prefix="x"):
    return "".join("%s_%d = %d\n" % (prefix, i, i) for i in range(n))


class Repo:
    def __init__(self, directory, with_map=True):
        self.dir = directory
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(HOME=directory, XDG_CONFIG_HOME=directory, GIT_CONFIG_NOSYSTEM="1",
                        GIT_CONFIG_GLOBAL=os.devnull)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        self.git("config", "commit.gpgsign", "false")
        if with_map:
            self.write("scripts/risk-map.json", json.dumps(MAP))

    def git(self, *args):
        p = subprocess.run(["git", *args], cwd=self.dir, env=self.env, capture_output=True, text=True)
        assert p.returncode == 0, (args, p.stderr)
        return p.stdout

    def write(self, name, content, binary=False):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb" if binary else "w", encoding=None if binary else "utf-8") as f:
            f.write(content)

    def commit(self, message="c"):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def run(self, *args):
        p = subprocess.run([sys.executable, SCRIPT, *args], cwd=self.dir, env=self.env,
                           capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr

    def level(self, *args):
        code, out, err = self.run("level", "--json", *args)
        assert code == 0, (code, out, err)
        return json.loads(out)


class RiskLevelTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(self.tmp.name)
        r = self.repo
        r.write("README.md", "# shop\n")
        r.write("docs/guide.md", "guide\n")
        r.write("shop/util.py", lines(10))
        r.write("shop/pricing.py", "price = 10\n")
        r.write("shop/cart.py", "items = []\ntotal = 0\n")
        r.write("shop/api.py", "SCHEMA = 1\n")
        r.write("shop/db/store.py", "rows = []\n")
        r.write("ui/page.html", "<p>shop</p>\n")
        r.write("tests/test_util.py", "def test(): pass\n")
        r.commit("base")

    def tearDown(self):
        self.tmp.cleanup()

    def classes(self, result):
        return {f["path"]: f["class"] for f in result["files"]}

    def todos(self, result):
        return [t["name"] for t in result["todos"]]

    def test_docs_only_is_none(self):
        self.repo.write("README.md", "# shop\nmore\n")
        self.repo.write("docs/guide.md", "guide\nmore\n")
        res = self.repo.level()
        self.assertEqual((res["width"], res["depth"]), ("none", "none"))
        code, out, _ = self.repo.run("level")
        self.assertEqual(code, 0)
        self.assertIn("LEVEL: none", out)

    def test_empty_diff(self):
        res = self.repo.level()
        self.assertEqual((res["width"], res["depth"], res["lines"]), ("none", "none", 0))
        self.assertIn("LEVEL: none (no changes)", self.repo.run("level")[1])

    def test_one_line_in_a_normal_file_is_small_normal(self):
        self.repo.write("shop/util.py", lines(10).replace("x_3 = 3", "x_3 = 4"))
        res = self.repo.level()
        self.assertEqual((res["width"], res["depth"]), ("small", "normal"))
        self.assertEqual(res["lines"], 2)  # one removed, one added
        self.assertEqual(self.todos(res), [])
        self.assertEqual(res["areas"], ["shop"])
        self.assertIn("LEVEL: small x normal (2 lines; area: shop)", self.repo.run("level")[1])

    def test_critical_path_asks_for_the_full_critical_set(self):
        self.repo.write("shop/pricing.py", "price = 11\n")
        res = self.repo.level()
        self.assertEqual((res["width"], res["depth"]), ("small", "critical"))
        self.assertEqual(self.classes(res)["shop/pricing.py"], "critical")
        todos = self.todos(res)
        for name in ("new-test", "edge-cases", "revert-proof", "adversarial-review", "security-check"):
            self.assertIn(name, todos)
        for name in ("ui-matrix", "live-try", "server-twin", "contract-test"):
            self.assertNotIn(name, todos)

    def test_content_anchor_makes_a_file_critical_only_when_touched(self):
        self.repo.write("shop/cart.py", "items = [1]\ntotal = 0\n")
        res = self.repo.level()
        self.assertEqual(self.classes(res)["shop/cart.py"], "normal")
        self.assertEqual(res["depth"], "normal")
        self.repo.write("shop/cart.py", "items = [1]\ntotal = 1\n")
        res = self.repo.level()
        self.assertEqual(self.classes(res)["shop/cart.py"], "critical")

    def test_anchor_matches_removed_lines_too(self):
        self.repo.write("shop/cart.py", "items = []\n")
        self.assertEqual(self.repo.level()["depth"], "critical")

    def test_server_twin_is_a_todo(self):
        self.repo.write("shop/api.py", "SCHEMA = 2\n")
        res = self.repo.level()
        self.assertEqual(res["depth"], "critical")
        twin = [t for t in res["todos"] if t["name"] == "server-twin"]
        self.assertEqual(len(twin), 1)
        self.assertIn("storefront/api.js", twin[0]["note"])

    def test_unknown_file_is_treated_as_sensitive_with_a_warning(self):
        self.repo.write("tools/odd.py", "x = 1\n")
        res = self.repo.level()
        self.assertEqual(self.classes(res)["tools/odd.py"], "unknown")
        self.assertEqual(res["depth"], "sensitive")
        self.assertTrue(any("tools/odd.py" in w for w in res["warnings"]))
        self.assertIn("full-write", self.todos(res))

    def test_sensitive_by_content_beats_normal_path(self):
        self.repo.write("shop/util.py", lines(10) + "db.write(x)\n")
        res = self.repo.level()
        self.assertEqual(self.classes(res)["shop/util.py"], "sensitive")
        self.assertEqual(res["depth"], "sensitive")

    def test_sensitive_by_path(self):
        self.repo.write("shop/db/store.py", "rows = [1]\n")
        self.assertEqual(self.repo.level()["depth"], "sensitive")

    def test_first_match_wins_skip_before_critical(self):
        self.repo.write("shop/pricing.md", "prices explained\n")
        res = self.repo.level()
        self.assertEqual(self.classes(res)["shop/pricing.md"], "skip")
        self.assertEqual(res["depth"], "none")

    def test_test_class_beats_sensitive_content(self):
        self.repo.write("tests/test_util.py", "def test(): save(1)\n")
        res = self.repo.level()
        self.assertEqual(self.classes(res)["tests/test_util.py"], "test")
        self.assertEqual(res["depth"], "normal")

    def test_test_files_do_not_count_toward_width(self):
        self.repo.write("tests/test_util.py", lines(400))
        self.repo.write("shop/util.py", lines(10).replace("x_3 = 3", "x_3 = 4"))
        res = self.repo.level()
        self.assertEqual((res["width"], res["lines"]), ("small", 2))

    def test_width_by_lines(self):
        self.repo.write("shop/big.py", lines(25))  # untracked file: 25 lines
        self.assertEqual(self.repo.level()["width"], "small")
        self.repo.write("shop/big.py", lines(51))
        self.assertEqual(self.repo.level()["width"], "medium")
        self.repo.write("shop/big.py", lines(301))
        self.assertEqual(self.repo.level()["width"], "large")

    def test_width_by_areas(self):
        self.repo.write("shop/a.py", lines(3))
        self.repo.write("storefront/a.js", lines(3))
        res = self.repo.level()
        self.assertEqual((res["width"], res["areas"]), ("medium", ["shop", "storefront"]))
        self.repo.write("ui/b.html", "<b>1</b>\n")
        self.repo.git("add", "-A")
        self.repo.commit("base 2")
        self.repo.write("shop/a.py", lines(4))
        self.repo.write("storefront/a.js", lines(4))
        self.repo.write("ui/b.html", "<b>2</b>\n")
        self.assertEqual(self.repo.level()["width"], "large")

    def test_default_area_is_the_first_two_directories(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Repo(d, with_map=False)
            repo.write("scripts/risk-map.json", json.dumps({"normal": ["**"]}))
            repo.write("a/b/c/d.py", "x = 1\n")
            repo.write("top.py", "x = 1\n")
            repo.commit("base")
            repo.write("a/b/c/d.py", "x = 2\n")
            repo.write("top.py", "x = 2\n")
            self.assertEqual(repo.level()["areas"], ["(root)", "a/b"])

    def test_new_ui_file_is_large_and_asks_for_the_surface_checks(self):
        self.repo.write("ui/screen.html", "<p>new</p>\n")
        res = self.repo.level()
        self.assertEqual((res["width"], res["depth"]), ("large", "normal"))
        for name in ("ui-matrix", "live-try"):
            self.assertIn(name, self.todos(res))
        self.assertNotIn("new-test", self.todos(res))

    def test_changing_an_existing_ui_file_is_small(self):
        self.repo.write("ui/page.html", "<p>shop!</p>\n")
        res = self.repo.level()
        self.assertEqual(res["width"], "small")
        self.assertNotIn("ui-matrix", self.todos(res))

    def test_medium_asks_for_a_new_test(self):
        self.repo.write("shop/big.py", lines(60))
        res = self.repo.level()
        self.assertEqual(self.todos(res), ["new-test"])

    def test_release_branch_is_large(self):
        self.repo.git("switch", "-q", "-c", "release/1.0")
        self.repo.write("shop/util.py", lines(10).replace("x_3 = 3", "x_3 = 4"))
        self.assertEqual(self.repo.level()["width"], "large")

    def test_deleted_critical_file_is_critical(self):
        os.remove(os.path.join(self.repo.dir, "shop/pricing.py"))
        res = self.repo.level()
        self.assertEqual(self.classes(res)["shop/pricing.py"], "critical")

    def test_rename_out_of_a_critical_path_stays_critical(self):
        self.repo.git("mv", "shop/pricing.py", "shop/legacy.py")
        res = self.repo.level()
        self.assertEqual(res["depth"], "critical")
        self.assertEqual(len(res["files"]), 1)
        self.assertEqual(res["files"][0]["old_path"], "shop/pricing.py")

    def test_binary_file_does_not_break_it(self):
        self.repo.write("ui/logo.bin", b"\x00\x01\x02binary", binary=True)
        res = self.repo.level()
        self.assertEqual(res["lines"], 0)
        self.assertEqual(self.classes(res)["ui/logo.bin"], "normal")

    def test_staged_mode_sees_only_the_index(self):
        self.repo.write("shop/pricing.py", "price = 12\n")
        self.repo.write("shop/util.py", lines(10).replace("x_3 = 3", "x_3 = 4"))
        self.repo.git("add", "shop/util.py")
        res = self.repo.level("--staged")
        self.assertEqual([f["path"] for f in res["files"]], ["shop/util.py"])
        self.assertEqual(res["depth"], "normal")
        self.assertEqual(self.repo.level()["depth"], "critical")

    def test_base_mode_compares_with_a_given_commit(self):
        self.repo.write("shop/pricing.py", "price = 12\n")
        self.repo.commit("price")
        self.assertEqual(self.repo.level()["depth"], "none")
        self.assertEqual(self.repo.level("--base", "HEAD~1")["depth"], "critical")
        code, _, err = self.repo.run("level", "--base", "no-such-ref")
        self.assertEqual(code, 1)
        self.assertIn("no-such-ref", err)

    def test_repo_without_commits(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Repo(d)
            repo.write("shop/pricing.py", "price = 1\n")
            self.assertEqual(repo.level()["depth"], "critical")
            repo.git("add", "-A")
            res = repo.level("--staged")
            self.assertEqual(res["depth"], "critical")

    def test_detached_head(self):
        self.repo.git("checkout", "-q", "--detach")
        self.repo.write("shop/util.py", lines(10).replace("x_3 = 3", "x_3 = 4"))
        self.assertEqual(self.repo.level()["width"], "small")

    def test_without_a_map_only_the_width_is_known(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Repo(d, with_map=False)
            repo.write("a.py", lines(10))
            repo.commit("base")
            repo.write("a.py", lines(10).replace("x_3 = 3", "x_3 = 4"))
            res = repo.level()
            self.assertFalse(res["map"])
            self.assertEqual((res["width"], res["depth"]), ("small", "unknown"))
            self.assertTrue(any("no risk map" in w for w in res["warnings"]))
            code, out, _ = repo.run("level")
            self.assertEqual(code, 0)
            self.assertIn("no risk map", out)

    def test_text_output_is_short(self):
        for i in range(30):
            self.repo.write("tools/odd_%d.py" % i, "x = 1\n")
        out = self.repo.run("level")[1]
        self.assertLessEqual(len(out.splitlines()), 22, out)
        self.assertIn("LEVEL: ", out.splitlines()[0])

    def test_bad_map_is_a_usage_error(self):
        self.repo.write("scripts/risk-map.json", "{not json")
        code, _, err = self.repo.run("level")
        self.assertEqual(code, 1)
        self.assertIn("risk-map.json", err)
        self.repo.write("scripts/risk-map.json", json.dumps({"critical": [{"glob": "a", "anchor": "("}]}))
        code, _, err = self.repo.run("level")
        self.assertEqual(code, 1)
        self.assertIn("anchor", err)

    def test_map_coverage(self):
        code, out, _ = self.repo.run("map-coverage")
        self.assertEqual(code, 0, out)
        self.assertIn("0 files", out)
        self.repo.write("weird/x.py", "x = 1\n")
        self.repo.commit("weird")
        code, out, _ = self.repo.run("map-coverage")
        self.assertEqual(code, 2)
        self.assertIn("weird/x.py", out)
        code, out, _ = self.repo.run("map-coverage", "--json")
        self.assertEqual(json.loads(out)["unknown"], ["weird/x.py"])

    def test_unknown_command_is_a_usage_error(self):
        code, _, _ = self.repo.run("nope")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
