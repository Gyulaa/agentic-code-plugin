"""Tests for test_debt.py. Run: python3 -m unittest discover -s tests"""

import glob
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest

try:
    from test_risk_level import MAP, Repo
except ImportError:
    from tests.test_risk_level import MAP, Repo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "agentic-code", "skills", "project-setup", "templates", "scripts",
                      "test_debt.py")

TEST_ONE = "python3 -m unittest discover -s tests -t . -k {name}"
OLD = "def discount(amount, pct):\n    return amount\n"
NEW = "def discount(amount, pct):\n    return amount - amount * pct // 100\n"
GOOD_TEST = ("import unittest\nfrom shop import coupon\n\n\nclass CouponTest(unittest.TestCase):\n"
             "    def %s(self):\n        self.assertEqual(coupon.discount(200, 10), 180)\n")
GIVEN, WHEN, THEN = ("a cart of 200 with a 10 percent coupon", "the coupon discount is applied",
                     "the amount is 180")


class DebtTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(self.tmp.name)
        r = self.repo
        r.write("scripts/risk-map.json", json.dumps(dict(MAP, test_one=TEST_ONE)))
        r.write("shop/__init__.py", "")
        r.write("tests/__init__.py", "")
        r.write("shop/coupon.py", OLD)
        r.write("tests/test_util.py", "def test(): pass\n")
        r.commit("base")

    def tearDown(self):
        self.tmp.cleanup()

    def debt(self, *args):
        p = subprocess.run([sys.executable, SCRIPT, *args], cwd=self.repo.dir, env=self.repo.env,
                           capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr

    def add(self, todo="new-test", given=GIVEN, when=WHEN, then=THEN, *extra):
        return self.debt("add", todo, "--given", given, "--when", when, "--then", then, *extra)

    def items(self):
        found = sorted(glob.glob(os.path.join(self.repo.dir, "docs", "test-debt", "TD-*.json")))
        return [self.load(f) for f in found]

    def load(self, path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def path(self, name):
        return os.path.join(self.repo.dir, name)

    def read(self, name):
        with open(self.path(name), encoding="utf-8") as f:
            return f.read()

    def change_and_add(self, **kw):
        """The change, its debt item, both committed; returns the item."""
        self.repo.write("shop/coupon.py", NEW)
        code, out, err = self.add(**kw)
        self.assertEqual(code, 0, out + err)
        self.repo.commit("coupon discount")
        return self.items()[0]

    def write_test(self, item, body=GOOD_TEST):
        name = item["where"]["name"]
        self.repo.write(item["where"]["file"], body % name if "%s" in body else body)
        return name

    # ---- add -----------------------------------------------------------------------------------

    def test_add_fills_in_what_the_diff_knows(self):
        self.repo.write("shop/coupon.py", NEW)
        code, out, err = self.add()
        self.assertEqual(code, 0, out + err)
        (item,) = self.items()
        self.assertRegex(item["id"], r"^TD-\d{8}-[0-9a-f]{4}$")
        self.assertEqual((item["todo"], item["status"], item["area"]), ("new-test", "open", "shop"))
        self.assertEqual((item["given"], item["when"], item["then"]), (GIVEN, WHEN, THEN))
        self.assertEqual(item["target"]["file"], "shop/coupon.py")
        self.assertIn("amount * pct", item["target"]["anchor"])
        self.assertEqual(item["change"]["parent"], self.repo.git("rev-parse", "HEAD").strip())
        self.assertTrue(0 < len(item["change"]["diff"]) <= 15)
        self.assertEqual(item["where"]["file"], "tests/test_coupon.py")
        self.assertRegex(item["where"]["name"], r"^test_td_\d{8}_[0-9a-f]{4}_")
        self.assertIn(item["id"].lower().replace("-", "_"), item["where"]["name"])
        self.assertIn(item["where"]["name"], item["run"])
        self.assertIn(item["id"], out)

    def test_add_prefers_an_existing_test_that_imports_the_target(self):
        self.repo.write("tests/test_coupon_flow.py", "from shop import coupon\n")
        self.repo.commit("flow test")
        self.repo.write("shop/coupon.py", NEW)
        self.assertEqual(self.add()[0], 0)
        self.assertEqual(self.items()[0]["where"]["file"], "tests/test_coupon_flow.py")

    def test_add_names_a_pattern_from_the_same_area(self):
        self.repo.write("shop/coupon.py", NEW)
        self.assertEqual(self.add()[0], 0)
        self.assertEqual(self.items()[0]["pattern"]["file"], "tests/test_util.py")

    def test_vague_claims_are_thrown_back(self):
        self.repo.write("shop/coupon.py", NEW)
        for kw in ({"then": "works"}, {"then": "it should work correctly"}, {"given": "a cart"},
                   {"when": "it runs", "then": "the result is correct"}):
            code, out, err = self.add(**kw)
            self.assertEqual(code, 2, kw)
            self.assertIn("vague", out + err)
        self.assertEqual(self.items(), [])

    def test_critical_depth_cannot_be_written_as_debt(self):
        self.repo.write("shop/pricing.py", "price = 11\n")
        code, out, err = self.add()
        self.assertEqual(code, 2)
        self.assertIn("critical", out + err)
        self.assertEqual(self.items(), [])

    def test_only_tests_can_be_debt(self):
        self.repo.write("shop/coupon.py", NEW)
        code, out, err = self.add("edge-cases")
        self.assertEqual(code, 2)
        self.assertIn("new-test", out + err)
        code, _, err = self.add("tidy-up")
        self.assertEqual(code, 1)

    def test_no_change_no_debt(self):
        code, out, err = self.add()
        self.assertEqual(code, 2)
        self.assertIn("no change", out + err)

    def test_list_and_show(self):
        self.change_and_add()
        code, out, _ = self.debt("list")
        self.assertEqual(code, 0)
        self.assertIn(self.items()[0]["id"], out)
        self.assertIn("shop", out)
        self.assertNotIn(self.items()[0]["id"], self.debt("list", "--area", "storefront")[1])
        self.assertIn(self.items()[0]["id"], self.debt("list", "--area", "shop")[1])
        listed = json.loads(self.debt("list", "--json")[1])
        self.assertEqual([i["id"] for i in listed], [self.items()[0]["id"]])
        code, out, _ = self.debt("show", self.items()[0]["id"])
        self.assertEqual((code, json.loads(out)["then"]), (0, THEN))
        self.assertEqual(self.debt("show", "TD-00000000-0000")[0], 1)

    # ---- close ---------------------------------------------------------------------------------

    def test_close_with_a_test_that_fails_on_the_old_code(self):
        item = self.change_and_add()
        self.write_test(item)
        before = os.stat(self.path("shop/coupon.py")).st_mtime_ns
        code, out, err = self.debt("close", item["id"])
        self.assertEqual(code, 0, out + err)
        self.assertIn("closed", out)
        self.assertEqual(self.read("shop/coupon.py"), NEW)  # restored
        self.assertEqual(os.stat(self.path("shop/coupon.py")).st_mtime_ns, before)
        self.assertEqual(self.items()[0]["status"], "closed")
        self.assertEqual(self.items()[0]["closed"]["how"], "test")
        self.assertEqual(self.repo.git("status", "--porcelain", "--", "shop/coupon.py"), "")

    def test_a_test_that_is_green_on_the_old_code_does_not_close_the_debt(self):
        item = self.change_and_add()
        body = GOOD_TEST.replace("coupon.discount(200, 10), 180", "coupon.discount(200, 0), 200")
        self.write_test(item, body)
        code, out, err = self.debt("close", item["id"])
        self.assertEqual(code, 2)
        self.assertIn("old code", out + err)
        self.assertEqual(self.read("shop/coupon.py"), NEW)
        self.assertEqual(self.items()[0]["status"], "open")

    def test_a_missing_test_name_is_refused(self):
        item = self.change_and_add()
        self.repo.write(item["where"]["file"], "from shop import coupon\n")
        code, out, err = self.debt("close", item["id"])
        self.assertEqual(code, 2)
        self.assertIn(item["where"]["name"], out + err)

    def test_a_test_that_never_mentions_the_target_is_refused(self):
        item = self.change_and_add()
        self.repo.write(item["where"]["file"],
                        "import unittest\n\n\nclass T(unittest.TestCase):\n    def %s(self):\n        pass\n"
                        % item["where"]["name"])
        code, out, err = self.debt("close", item["id"])
        self.assertEqual(code, 2)
        self.assertIn("coupon", out + err)

    def test_a_test_that_is_red_on_the_new_code_is_refused(self):
        item = self.change_and_add()
        self.write_test(item, GOOD_TEST.replace("180", "999"))
        code, out, err = self.debt("close", item["id"])
        self.assertEqual(code, 2)
        self.assertIn("pass", out + err)
        self.assertEqual(self.read("shop/coupon.py"), NEW)

    def test_uncommitted_changes_on_the_target_stop_the_revert_proof(self):
        item = self.change_and_add()
        self.write_test(item)
        self.repo.write("shop/coupon.py", NEW + "# work in progress\n")
        code, out, err = self.debt("close", item["id"])
        self.assertEqual(code, 2)
        self.assertIn("uncommitted", out + err)
        self.assertEqual(self.read("shop/coupon.py"), NEW + "# work in progress\n")

    def test_a_vanished_parent_commit_needs_an_explicit_one(self):
        item = self.change_and_add()
        self.write_test(item)
        path = self.path("docs/test-debt/%s.json" % item["id"])
        data = self.load(path)
        good = data["change"]["parent"]
        data["change"]["parent"] = "0" * 40
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        self.repo.commit("rewrite history, so to speak")
        code, out, err = self.debt("close", item["id"])
        self.assertEqual(code, 2)
        self.assertIn("--parent", out + err)
        code, out, err = self.debt("close", item["id"], "--parent", good)
        self.assertEqual(code, 0, out + err)

    def test_a_cached_bytecode_of_the_same_size_cannot_pose_as_the_old_code(self):
        same_old = "def discount(amount, pct):\n    return amount - 0 * pct\n"
        same_new = "def discount(amount, pct):\n    return amount - 2 * pct\n"
        self.repo.write("shop/coupon.py", same_old)
        self.repo.commit("same-size base")
        self.repo.write("shop/coupon.py", same_new)
        self.assertEqual(self.add()[0], 0)
        self.repo.commit("coupon discount")
        subprocess.run([sys.executable, "-c", "import shop.coupon"], cwd=self.repo.dir, env=self.repo.env,
                       check=True)  # a developer's own run leaves a .pyc of the new code behind
        item = self.items()[0]
        self.write_test(item)
        code, out, err = self.debt("close", item["id"])
        self.assertEqual(code, 0, out + err)

    def test_a_new_file_has_no_old_state_to_restore(self):
        self.repo.write("shop/newmod.py", "def fee(amount):\n    return amount // 10\n")
        code, out, err = self.add(then="the fee for 200 is 20")
        self.assertEqual(code, 0, out + err)
        self.repo.commit("new module")
        item = self.items()[0]
        self.repo.write(item["where"]["file"],
                        "import unittest\nfrom shop import newmod\n\n\nclass T(unittest.TestCase):\n"
                        "    def %s(self):\n        self.assertEqual(newmod.fee(200), 20)\n" % item["where"]["name"])
        code, out, err = self.debt("close", item["id"])
        self.assertEqual(code, 0, out + err)
        self.assertIn("new file", out)

    def test_attested_close_is_for_a_live_try(self):
        self.repo.write("shop/coupon.py", NEW)
        self.assertEqual(self.add("live-try", then="the coupon line shows 180 on the phone")[0], 0)
        item = self.items()[0]
        self.assertEqual(self.debt("close", item["id"], "--attested", "ok")[0], 1)
        code, out, err = self.debt("close", item["id"], "--attested", "tried it on the phone: shows 180")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.items()[0]["closed"]["how"], "attested")

    def test_attested_close_is_refused_for_a_test_debt(self):
        item = self.change_and_add()
        code, out, err = self.debt("close", item["id"], "--attested", "I looked at it and it is fine")
        self.assertEqual(code, 2)
        self.assertEqual(self.items()[0]["status"], "open")

    def test_closing_twice_is_an_error(self):
        item = self.change_and_add()
        self.write_test(item)
        self.assertEqual(self.debt("close", item["id"])[0], 0)
        self.assertEqual(self.debt("close", item["id"])[0], 1)

    # ---- a killed close must not lose work ------------------------------------------------------

    def test_a_killed_revert_proof_is_undone_by_the_next_run(self):
        slow = ("import sys, time\n"
                "if 'amount - amount' not in open('shop/coupon.py').read():\n"
                "    time.sleep(60)\n")
        self.repo.write("slow.py", slow)
        self.repo.write("scripts/risk-map.json", json.dumps(dict(MAP, test_one="python3 slow.py {name}")))
        self.repo.commit("slow test runner")
        item = self.change_and_add()
        self.write_test(item)
        marker = os.path.join(self.repo.dir, ".git", "agentic", "revert.lock")
        proc = subprocess.Popen([sys.executable, SCRIPT, "close", item["id"]], cwd=self.repo.dir,
                                env=self.repo.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True)
        try:
            deadline = time.time() + 20
            while not os.path.exists(marker) and time.time() < deadline:
                time.sleep(0.05)
            self.assertTrue(os.path.exists(marker), "the revert proof never started")
            time.sleep(0.3)
            self.assertEqual(self.read("shop/coupon.py"), OLD)  # the old code is in place
        finally:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
        self.assertEqual(self.read("shop/coupon.py"), OLD)  # the kill left it that way
        code, out, err = self.debt("list")
        self.assertEqual(code, 0, out + err)
        self.assertIn("restored", out + err)
        self.assertEqual(self.read("shop/coupon.py"), NEW)
        self.assertFalse(os.path.exists(marker))
        self.assertEqual(self.repo.git("status", "--porcelain", "--", "shop/coupon.py"), "")

    def test_a_running_revert_proof_is_a_lock(self):
        item = self.change_and_add()
        self.write_test(item)
        os.makedirs(os.path.join(self.repo.dir, ".git", "agentic"))
        with open(os.path.join(self.repo.dir, ".git", "agentic", "revert.lock"), "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "file": "shop/coupon.py", "backup": "x", "mtime_ns": 0}, f)
        code, out, err = self.debt("close", item["id"])
        self.assertEqual(code, 2)
        self.assertIn("running", out + err)
        self.assertEqual(self.read("shop/coupon.py"), NEW)

    def test_the_script_never_stashes_or_resets(self):
        with open(SCRIPT, encoding="utf-8") as f:
            text = f.read()
        for forbidden in ("stash", "checkout --", "reset --hard", "checkout\", \"--\""):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
