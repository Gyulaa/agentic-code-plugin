"""Tests for the project guard hook. Run: python3 -m unittest discover -s tests"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "agentic-code", "hooks", "guard.py")
TEMPLATE = os.path.join(ROOT, "plugins", "agentic-code", "skills", "project-setup", "templates", "claude", "guard.json")

PROD = "my-prod" + "-project"


def run_hook(command, cwd):
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd})
    out = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, check=True).stdout
    if not out.strip():
        return "allow"
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"]


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = self.tmp.name
        self.sub = os.path.join(self.project, "src", "deep")
        os.makedirs(self.sub)

    def tearDown(self):
        self.tmp.cleanup()

    def write_guard(self, content):
        os.makedirs(os.path.join(self.project, ".claude"), exist_ok=True)
        with open(os.path.join(self.project, ".claude", "guard.json"), "w", encoding="utf-8") as f:
            f.write(content)

    def test_no_guard_file_allows_everything(self):
        self.assertEqual(run_hook("firebase deploy", self.sub), "allow")

    def test_template_rules(self):
        with open(TEMPLATE, encoding="utf-8") as f:
            self.write_guard(f.read())
        cases = [
            ("firebase deploy --project " + PROD, "deny"),
            ("firebase deploy", "deny"),
            ("firebase deploy --project my-test-project", "allow"),
            ("firebase emulators:exec --project demo-x 'npm test'", "allow"),
            ("firebase functions:list --project my-test-project", "allow"),
            ("git push origin main", "deny"),
            ("git push -u origin feat/login", "allow"),
            ("git push -u origin feat/main-menu", "allow"),
            ("git push origin HEAD:main", "deny"),
            ("git push --force origin master && echo done", "deny"),
            ("git push origin +main", "deny"),
            ("vercel --prod", "ask"),
            ("firebase deploy --project my-test-project && firebase deploy --project " + PROD, "deny"),
            ("vercel --prod; git push origin main", "deny"),
            ("ls -la", "allow"),
        ]
        for command, expected in cases:
            with self.subTest(command=command):
                self.assertEqual(run_hook(command, self.sub), expected)

    def test_ai_attribution_is_denied_everywhere(self):
        trailer = "Co-Authored-By: Claude Opus <noreply" + "@anthropic.com>"
        cases = [
            ("git commit -m \"$(cat <<'EOF'\nfix: thing\n\n%s\nEOF\n)\"" % trailer, "deny"),
            ("git -C repo commit -m 'feat: x' -m '%s'" % trailer, "deny"),
            ("gh pr create --title t --body 'body\n\nGenerated with [Claude Code](https://claude.com/claude-code)'", "deny"),
            ("git commit -m 'fix: thing'", "allow"),
            ("grep -rn 'noreply" + "@anthropic.com' .", "allow"),
            ("git commit -m 'feat: x' -m 'strips the trailer or \"Generated with Claude Code\"'", "allow"),
        ]
        for command, expected in cases:
            with self.subTest(command=command):
                self.assertEqual(run_hook(command, self.sub), expected)

    def test_ai_attribution_can_be_allowed(self):
        self.write_guard(json.dumps({"allow_ai_attribution": True, "rules": []}))
        msg = "git commit -m 'x' -m 'Co-Authored-By: Claude <noreply" + "@anthropic.com>'"
        self.assertEqual(run_hook(msg, self.sub), "allow")

    def test_broken_guard_asks(self):
        self.write_guard("{not json")
        self.assertEqual(run_hook("ls", self.project), "ask")

    def test_bad_action_asks(self):
        self.write_guard(json.dumps({"rules": [{"match": "x", "action": "allow"}]}))
        self.assertEqual(run_hook("x", self.project), "ask")


if __name__ == "__main__":
    unittest.main()
