"""Tests for the seo skill's seo_check.py. Run: python3 -m unittest discover -s tests"""

import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "agentic-code", "skills", "seo", "scripts", "seo_check.py")

BODY = "<p>" + "A paragraph of real text that a crawler can read without running any script. " * 5 + "</p>"


def page(title="Descaling a kettle: a five-minute guide", lang="en", canonical="https://example.com/a",
         description="How to descale a kettle with vinegar or citric acid, how often to do it, and what to avoid.",
         extra_head="", body=BODY, h1="<h1>Descaling a kettle</h1>"):
    head = '<meta name="viewport" content="width=device-width, initial-scale=1">'
    head += '<meta property="og:image" content="https://example.com/a.jpg">'
    if title is not None:
        head += f"<title>{title}</title>"
    if description is not None:
        head += f'<meta name="description" content="{description}">'
    if canonical is not None:
        head += f'<link rel="canonical" href="{canonical}">'
    lang_attr = f' lang="{lang}"' if lang else ""
    return f"<!doctype html><html{lang_attr}><head>{head}{extra_head}</head><body>{h1}{body}</body></html>"


def run(*args):
    p = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
    return p.returncode, p.stdout


class SeoCheckTest(unittest.TestCase):
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
        return {line.split("[", 1)[1].split("]", 1)[0] for line in out.splitlines() if "] " in line}

    def site(self):
        self.write("robots.txt", "User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n\n"
                                 "Sitemap: https://example.com/sitemap.xml\n")
        self.write("sitemap.xml", '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                  "<url><loc>https://example.com/a</loc><lastmod>2026-10-01</lastmod></url></urlset>")

    def test_good_site_passes(self):
        self.site()
        self.write("index.html", page())
        code, out = run(self.dir)
        self.assertEqual(code, 0, out)
        self.assertIn("training-bot-blocked", self.rules(out))  # a note, not a warning
        self.assertIn("0 warnings", out)

    def test_missing_basics(self):
        self.site()
        self.write("bad.html", page(title=None, description=None, canonical=None, lang=None, h1=""))
        code, out = run(self.dir)
        self.assertEqual(code, 2)
        for rule in ("no-title", "no-description", "no-canonical", "no-lang", "no-h1"):
            self.assertIn(rule, self.rules(out), rule)

    def test_empty_client_rendered_page(self):
        self.write("app.html", page(body='<div id="root"></div><script src="/app.js"></script>'))
        code, out = run(os.path.join(self.dir, "app.html"))
        self.assertEqual(code, 2)
        self.assertIn("little-text", self.rules(out))

    def test_jsonld(self):
        good = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article","headline":"x"}</script>'
        faq = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage"}</script>'
        broken = '<script type="application/ld+json">{"@context": "https://schema.org", "@type": }</script>'
        self.write("good.html", page(extra_head=good + faq))
        code, out = run(os.path.join(self.dir, "good.html"))
        self.assertEqual(code, 0, out)
        self.assertIn("jsonld-retired", self.rules(out))
        self.write("broken.html", page(extra_head=broken, canonical="https://example.com/b"))
        code, out = run(os.path.join(self.dir, "broken.html"))
        self.assertEqual(code, 2)
        self.assertIn("jsonld-invalid", self.rules(out))

    def test_images(self):
        self.write("img.html", page(body=BODY + '<img src="a.jpg"><img src="b.jpg" alt="" width="10" height="10">'))
        code, out = run(os.path.join(self.dir, "img.html"))
        self.assertEqual(code, 2)
        self.assertEqual(out.count("[img-no-alt]"), 1)
        self.assertEqual(out.count("[img-no-size]"), 1)

    def test_duplicates_across_pages(self):
        self.site()
        self.write("a.html", page(canonical="https://example.com/a"))
        self.write("b.html", page(canonical="https://example.com/b"))
        code, out = run(self.dir)
        self.assertEqual(code, 2)
        self.assertIn("duplicate-title", self.rules(out))
        self.assertIn("duplicate-description", self.rules(out))

    def test_noindex_page_is_skipped(self):
        self.write("thanks.html", page(title=None, extra_head='<meta name="robots" content="noindex">'))
        code, out = run(os.path.join(self.dir, "thanks.html"))
        self.assertEqual(code, 0, out)
        self.assertIn("noindex", self.rules(out))

    def test_blocked_search_bots(self):
        self.write("robots.txt", "User-agent: OAI-SearchBot\nDisallow: /\n\nUser-agent: *\nDisallow: /\n")
        self.write("index.html", page())
        code, out = run(self.dir)
        self.assertEqual(code, 2)
        self.assertIn("OAI-SearchBot may not crawl", out)
        self.assertIn("Googlebot may not crawl", out)
        self.assertIn("no-sitemap", self.rules(out))

    def test_hreflang_reciprocity(self):
        self.site()
        alt_en = '<link rel="alternate" hreflang="hu" href="https://example.com/hu">'
        self.write("en.html", page(canonical="https://example.com/en", extra_head=alt_en))
        self.write("hu.html", page(canonical="https://example.com/hu", lang="hu",
                                   title="Vízkőmentesítés: ötperces útmutató",
                                   description="Hogyan vízkőmentesítsd a vízforralót ecettel vagy citromsavval, és milyen gyakran."))
        code, out = run(self.dir)
        self.assertEqual(code, 2)
        self.assertIn("hreflang-not-reciprocal", self.rules(out))

    def test_no_info_hides_notes(self):
        self.write("img.html", page(body=BODY + '<img src="b.jpg" alt="">'))
        code, out = run("--no-info", os.path.join(self.dir, "img.html"))
        self.assertEqual(code, 0, out)
        self.assertNotIn("img-no-size", out)

    def test_non_string_type_does_not_crash(self):
        bad = '<script type="application/ld+json">{"@context":"https://schema.org","@type":{"bad":1}}</script>'
        self.write("t.html", page(extra_head=bad))
        code, out = run(os.path.join(self.dir, "t.html"))
        self.assertEqual(code, 2, out)
        self.assertIn("jsonld-bad-type", self.rules(out))

    def test_omitted_head_end_tag_still_counts_body_text(self):
        html = page().replace("</head>", "") + '<script src="a.js"></script>'
        self.write("nohead.html", html)
        code, out = run(os.path.join(self.dir, "nohead.html"))
        self.assertNotIn("little-text", self.rules(out))

    def test_robots_none_is_noindex(self):
        self.write("n.html", page(title=None, extra_head='<meta name="robots" content="none">'))
        code, out = run(os.path.join(self.dir, "n.html"))
        self.assertEqual(code, 0, out)

    def test_robots_exact_agent_and_longest_match(self):
        self.write("robots.txt", "User-agent: Applebot\nAllow: /\n\n"
                                 "User-agent: Applebot-Extended\nDisallow: /\n\n"
                                 "User-agent: *\nDisallow: /\nAllow: /$\n\n"
                                 "Sitemap: https://example.com/sitemap.xml\n")
        self.write("index.html", page())
        code, out = run(self.dir)
        self.assertIn("Applebot-Extended blocked", out)
        self.assertNotIn("search-bot-blocked", self.rules(out))

    def test_usage_errors(self):
        self.assertEqual(run()[0], 1)
        self.assertEqual(run(os.path.join(self.dir, "missing.html"))[0], 1)
        self.assertEqual(run("--bogus", self.dir)[0], 1)


if __name__ == "__main__":
    unittest.main()
