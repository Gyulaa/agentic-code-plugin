"""Project guard for Claude Code (PreToolUse on Bash).

Looks for `.claude/guard.json` in the command's working directory and its parents
(a `~/.claude/guard.json` therefore acts as a guard for every project under the
home folder). No file: the hook does nothing. Each rule:

    {"name": "...", "match": "<regex>", "unless": "<regex, optional>",
     "action": "deny" | "ask", "reason": "..."}

A command that matches `match` and not `unless` is denied, or sent to the user
for confirmation. An unreadable guard file never fails open: every command then
asks for confirmation, with the reason.

Standard library only; Python 3.8+ (the python3 on macOS and Linux).
"""

import json
import os
import re
import sys

GUARD_FILE = os.path.join(".claude", "guard.json")


def find_guard(start):
    path = os.path.abspath(start or os.getcwd())
    while True:
        candidate = os.path.join(path, GUARD_FILE)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent


def load_rules(guard_path):
    with open(guard_path, encoding="utf-8") as f:
        data = json.load(f)
    rules = data.get("rules")
    if not isinstance(rules, list):
        raise ValueError("'rules' must be a list")
    for rule in rules:
        re.compile(rule["match"])
        if rule.get("unless"):
            re.compile(rule["unless"])
        if rule.get("action", "deny") not in ("deny", "ask"):
            raise ValueError("action must be deny or ask: %s" % rule.get("name", "?"))
    return rules


# Rules are checked per command segment, so an allowed part ("--project test")
# cannot excuse a forbidden part chained after it with && ; || | or a newline.
SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|\n]")


def decide(command, rules):
    """Returns (action, reason) for the strictest matching rule, or None."""
    found = None
    for segment in SEGMENT_SPLIT.split(command):
        for rule in rules:
            if not re.search(rule["match"], segment):
                continue
            unless = rule.get("unless")
            if unless and re.search(unless, segment):
                continue
            name = rule.get("name", "guard rule")
            reason = rule.get("reason", "blocked by the project guard")
            action = rule.get("action", "deny")
            if action == "deny":
                return action, "%s: %s" % (name, reason)
            found = found or (action, "%s: %s" % (name, reason))
    return found


def respond(action, reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": action,
            "permissionDecisionReason": "Project guard (.claude/guard.json) - " + reason,
        }
    }, ensure_ascii=False))


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    command = (data.get("tool_input") or {}).get("command") or ""
    if not command:
        return
    guard_path = find_guard(data.get("cwd"))
    if not guard_path:
        return
    try:
        rules = load_rules(guard_path)
    except Exception as error:
        respond("ask", "the guard file %s could not be read (%s); confirm this command by hand" % (guard_path, error))
        return
    decision = decide(command, rules)
    if decision:
        respond(*decision)


if __name__ == "__main__":
    main()
