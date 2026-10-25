"""Tests for the design skill's slop_check.py. Run: python3 -m unittest discover -s tests"""

import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "agentic-code", "skills", "design", "scripts", "slop_check.py")


def run(*paths):
    p = subprocess.run([sys.executable, SCRIPT, *paths], capture_output=True, text=True)
    return p.returncode, p.stdout


class SlopCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, content):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def rules(self, out):
        return {line.split("[", 1)[1].split("]", 1)[0] for line in out.splitlines() if "[" in line}

    def test_clean_files_pass(self):
        self.write("app.css", ":root { --surface: #f7f5f2; }\n"
                              ".card { transition: transform 200ms cubic-bezier(0.23, 1, 0.32, 1); }\n"
                              "a:focus-visible { outline: 2px solid var(--surface); }\n"
                              "@media (prefers-reduced-motion: reduce) { .card { transition: none; } }\n")
        self.write("page.html", "<p>Book a free consultation.</p>\n")
        code, out = run(self.dir)
        self.assertEqual(code, 0, out)
        self.assertIn("OK (2 files)", out)

    def test_css_tells_are_found(self):
        self.write("bad.css", ".a { transition: all 0.3s ease-in; }\n"
                              ".b { transform: scale(0); background-clip: text; }\n"
                              ".c { border-left: 4px solid #6366f1; font-family: Inter, sans-serif; }\n"
                              ".d { outline: none; }\n"
                              "@import url('https://fonts.googleapis.com/css2?family=Lora');\n")
        code, out = run(self.dir)
        self.assertEqual(code, 2)
        for rule in ("transition-all", "ease-in", "scale-zero", "gradient-text", "side-stripe", "purple",
                     "default-font", "focus-removed", "font-cdn", "reduced-motion"):
            self.assertIn(rule, self.rules(out), rule)

    def test_ease_in_out_and_small_scale_are_fine(self):
        self.write("ok.css", ".a { transition: opacity 200ms ease-in-out; transform: scale(0.95); }\n"
                             "@media (prefers-reduced-motion: reduce) { .a { transition: none; } }\n")
        code, out = run(self.dir)
        self.assertEqual(code, 0, out)

    def test_tailwind_and_markup_tells(self):
        self.write("Hero.tsx", 'import { Inter } from "next/font/google";\n'
                               '<h1 className="bg-gradient-to-r from-indigo-500 to-purple-600 bg-clip-text">Unlock your potential</h1>\n'
                               '<p>John Doe — CEO</p>\n'
                               '<meta name="viewport" content="width=device-width, user-scalable=no" />\n')
        code, out = run(self.dir)
        self.assertEqual(code, 2)
        for rule in ("default-font", "purple-gradient", "gradient-text", "inflated-copy", "em-dash",
                     "placeholder-name", "zoom-disabled"):
            self.assertIn(rule, self.rules(out), rule)

    def test_slop_ok_skips_a_line(self):
        self.write("brand.css", ".logo { font-family: Inter, sans-serif; } /* slop-ok: brand font */\n")
        code, out = run(self.dir)
        self.assertEqual(code, 0, out)

    def test_comments_are_not_copy(self):
        self.write("util.ts", "// seamless — internal note\nexport const x = 1;\n")
        code, out = run(self.dir)
        self.assertEqual(code, 0, out)

    def test_literal_colour_next_to_tokens(self):
        self.write("tokens.css", ":root { --primary: #1a1c1e; }\n")
        self.write("button.css", ".btn { color: #ff0000; }\n")
        code, out = run(self.dir)
        self.assertEqual(code, 2)
        self.assertIn("button.css:1: [literal-color]", out)
        self.assertNotIn("tokens.css", out)

    def test_hungarian_copy(self):
        self.write("index.md", "Forradalmi megoldás, zökkenőmentes élmény.\n")
        code, out = run(self.dir)
        self.assertEqual(code, 2)
        self.assertIn("inflated-copy", self.rules(out))

    def test_dart(self):
        self.write("lib/home.dart", "final c = AnimationController(vsync: this);\n"
                                    "final curve = Curves.easeIn;\n"
                                    "Container(color: Color(0xFF6366F1));\n"
                                    "Text('Hi', style: GoogleFonts.inter());\n")
        code, out = run(self.dir)
        self.assertEqual(code, 2)
        for rule in ("ease-in", "literal-color", "default-font", "font-cdn", "reduced-motion"):
            self.assertIn(rule, self.rules(out), rule)

    def test_dart_theme_file_and_reduced_motion(self):
        self.write("lib/theme.dart", "const primary = Color(0xFF1A1C1E);\n")
        self.write("lib/anim.dart", "final c = AnimationController(vsync: this);\n"
                                    "if (MediaQuery.disableAnimationsOf(context)) {}\n")
        code, out = run(self.dir)
        self.assertEqual(code, 0, out)

    def test_skips_dependency_folders(self):
        self.write("node_modules/lib/x.css", ".a { transition: all 1s; }\n")
        code, out = run(self.dir)
        self.assertEqual(code, 0, out)

    def test_no_false_positives_on_common_correct_code(self):
        self.write("tokens.css", ":root { --primary: #1a1c1e; }\n")
        self.write("page.html", '<meta name="theme-color" content="#0b0b0b">\n'
                                '<a href="#add">Add</a>\n'
                                '<svg><path fill="#1a1c1e" d="M0 0"/></svg>\n'
                                "<p>Sign up for our spring promotion.</p>\n")
        self.write("focus.css", "a:focus-visible { box-shadow: 0px 0px 0px 3px var(--primary); }\n"
                                ".code { font-family: 'Roboto Mono', monospace; }\n")
        self.write("tailwind.config.js", "colors: { brand: '#1a1c1e' }\n")
        code, out = run(self.dir)
        self.assertEqual(code, 0, out)

    def test_eight_digit_hex_and_text_theme(self):
        self.write("a.css", ".a { color: #6366f1ff; }\n")
        self.write("lib/t.dart", "final t = GoogleFonts.interTextTheme();\n")
        code, out = run(self.dir)
        self.assertIn("purple", self.rules(out))
        self.assertIn("default-font", self.rules(out))

    def test_dart_bundled_fonts_silence_font_cdn(self):
        self.write("lib/main.dart", "GoogleFonts.config.allowRuntimeFetching = false;\n"
                                    "Text('x', style: GoogleFonts.lora());\n")
        code, out = run(self.dir)
        self.assertNotIn("font-cdn", self.rules(out))

    def test_usage_errors(self):
        self.assertEqual(run()[0], 1)
        self.assertEqual(run(os.path.join(self.dir, "missing"))[0], 1)
        self.assertEqual(run(self.write("tool.py", "x = 1\n"))[0], 1)
        self.assertEqual(run("--bogus", self.dir)[0], 1)


if __name__ == "__main__":
    unittest.main()
