#!/usr/bin/env python3
"""Check built pages for search and AI-search basics.

Usage: python3 seo_check.py [--no-info] <build folder | .html file | http(s) URL> [...]
Per page: lang, title, meta description, canonical, one h1, robots meta, viewport,
hreflang (with reciprocity across the scanned pages), JSON-LD validity, images without
alt or size, and how much text the HTML carries without JavaScript. Across pages:
duplicate titles and descriptions. Per site: robots.txt for the known search and
AI crawlers, and the sitemap.
Output: "where: warn|info [rule] message" lines, then a summary line.
Exit code: 0 no warnings, 2 warnings, 1 usage error.
A URL is fetched as served (no JavaScript runs), which is what most AI crawlers see.
Python 3 standard library only.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

SKIP_DIRS = {".git", "node_modules", ".next", ".nuxt", ".svelte-kit", ".astro", ".dart_tool", "vendor"}
USER_AGENT = "seo_check/1.0 (agentic-code plugin)"
TIMEOUT = 15  # seconds; a page that takes longer is a finding in itself

# Crawlers whose block removes the site from a search or answer engine.
SEARCH_BOTS = {
    "Googlebot": "Google Search, including AI Overviews and AI Mode",
    "Bingbot": "Bing and Copilot",
    "OAI-SearchBot": "ChatGPT search",
    "Claude-SearchBot": "Claude's search answers",
    "PerplexityBot": "Perplexity",
    "Applebot": "Apple's Siri and Spotlight suggestions",
}
# Crawlers that collect training data: blocking them is the owner's choice.
TRAINING_BOTS = ["GPTBot", "ClaudeBot", "Google-Extended", "Applebot-Extended", "CCBot"]

TITLE_MAX = 60        # characters; Google cuts titles by pixel width, about 60 characters
DESC_MIN, DESC_MAX = 50, 160
MIN_TEXT = 250        # characters of visible body text below which a page looks empty without JavaScript
RETIRED_TYPES = {"FAQPage": "FAQ", "HowTo": "HowTo"}
HEAD_TAGS = {"html", "head", "title", "meta", "link", "script", "style", "base", "noscript", "template"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.title = None
        self.description = None
        self.robots = ""
        self.canonical = None
        self.viewport = False
        self.og_image = False
        self.alternates = []      # (hreflang, href)
        self.h1 = 0
        self.images = []          # (line, has_alt, has_size)
        self.jsonld = []          # (line, text)
        self.scripts = 0
        self.text_len = 0
        self._stack = []
        self._in_title = False
        self._title_parts = []
        self._jsonld_line = None
        self._jsonld_parts = []

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        line = self.getpos()[0]
        if "head" in self._stack and tag not in HEAD_TAGS:
            # </head> is optional: the first body tag ends the head
            while self._stack and self._stack.pop() != "head":
                pass
        if tag == "html":
            self.lang = a.get("lang") or None
        elif tag == "title" and self.title is None:
            self._in_title = True
        elif tag == "meta":
            name = a.get("name", "").lower()
            prop = a.get("property", "").lower()
            if name == "description":
                self.description = a.get("content", "").strip()
            elif name in ("robots", "googlebot"):
                self.robots += " " + a.get("content", "").lower()
            elif name == "viewport":
                self.viewport = True
            elif prop == "og:image":
                self.og_image = True
        elif tag == "link":
            rel = a.get("rel", "").lower().split()
            if "canonical" in rel:
                self.canonical = a.get("href", "").strip()
            elif "alternate" in rel and a.get("hreflang"):
                self.alternates.append((a["hreflang"].lower(), a.get("href", "").strip()))
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img":
            has_size = ("width" in a and "height" in a) or "aspect-ratio" in a.get("style", "")
            self.images.append((line, "alt" in a, has_size))
        elif tag == "script":
            self.scripts += 1
            if a.get("type", "").lower() == "application/ld+json":
                self._jsonld_line = line
                self._jsonld_parts = []
        if tag not in ("meta", "link", "img", "br", "hr", "input", "source", "wbr"):
            self._stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title = "".join(self._title_parts).strip()
        if tag == "script" and self._jsonld_line is not None:
            self.jsonld.append((self._jsonld_line, "".join(self._jsonld_parts)))
            self._jsonld_line = None
        if tag in self._stack:
            while self._stack and self._stack.pop() != tag:
                pass

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)
        elif self._jsonld_line is not None:
            self._jsonld_parts.append(data)
        elif not any(t in ("script", "style", "noscript", "template", "head") for t in self._stack):
            self.text_len += len(data.strip())


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read().decode(r.headers.get_content_charset() or "utf-8", errors="replace")
            return r.status, {k.lower(): v for k, v in r.headers.items()}, body
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, ""
    except (urllib.error.URLError, OSError) as e:
        return None, {}, str(e)


def collect_types(node, out):
    if isinstance(node, list):
        for item in node:
            collect_types(item, out)
    elif isinstance(node, dict):
        if "@type" in node:
            t = node["@type"]
            out.extend(t if isinstance(t, list) else [t])
        for key in ("@graph", "mainEntity", "itemListElement"):
            if key in node:
                collect_types(node[key], out)


class Report:
    def __init__(self, show_info):
        self.show_info = show_info
        self.warnings = 0
        self.notes = 0

    def add(self, where, level, rule, message):
        if level == "warn":
            self.warnings += 1
        else:
            self.notes += 1
            if not self.show_info:
                return
        print(f"{where}: {level} [{rule}] {message}")


def check_page(name, html, headers, report):
    p = Page()
    p.feed(html)
    p.close()
    robots = set(re.split(r"[\s,]+", p.robots + " " + headers.get("x-robots-tag", "").lower()))
    if robots & {"noindex", "none"}:
        report.add(name, "info", "noindex", "excluded from search by noindex; other checks skipped")
        return None
    where = lambda line=1: f"{name}:{line}"
    if not p.lang:
        report.add(where(), "warn", "no-lang", "<html> has no lang attribute")
    if not p.title:
        report.add(where(), "warn", "no-title", "no <title>")
    elif len(p.title) > TITLE_MAX:
        report.add(where(), "info", "long-title", f"title is {len(p.title)} characters; about {TITLE_MAX} show in results")
    if not p.description:
        report.add(where(), "warn", "no-description", "no meta description")
    elif not DESC_MIN <= len(p.description) <= DESC_MAX:
        report.add(where(), "info", "description-length",
                   f"description is {len(p.description)} characters; about {DESC_MIN}-{DESC_MAX} works best")
    if not p.canonical:
        report.add(where(), "warn", "no-canonical", "no <link rel=\"canonical\">")
    elif not p.canonical.startswith(("http://", "https://")):
        report.add(where(), "warn", "relative-canonical", f"canonical should be an absolute URL: {p.canonical}")
    if p.h1 == 0:
        report.add(where(), "warn", "no-h1", "no <h1>")
    elif p.h1 > 1:
        report.add(where(), "info", "several-h1", f"{p.h1} <h1> elements; one main heading is clearer")
    if not p.viewport:
        report.add(where(), "warn", "no-viewport", "no viewport meta; the page will not be mobile-friendly")
    if not p.og_image:
        report.add(where(), "info", "no-og-image", "no og:image; shared links will have no preview image")
    codes = [c for c, _ in p.alternates]
    if p.alternates and "x-default" not in codes:
        report.add(where(), "info", "no-x-default", "hreflang set without x-default")
    if len(codes) != len(set(codes)):
        report.add(where(), "warn", "duplicate-hreflang", "the same hreflang code appears twice")
    for line, has_alt, has_size in p.images:
        if not has_alt:
            report.add(where(line), "warn", "img-no-alt", "image without alt (use alt=\"\" for decorative images)")
        if not has_size:
            report.add(where(line), "info", "img-no-size", "image without width and height; it can shift the layout")
    for line, text in p.jsonld:
        try:
            data = json.loads(text)
        except ValueError as e:
            report.add(where(line), "warn", "jsonld-invalid", f"JSON-LD does not parse: {e}")
            continue
        types = []
        collect_types(data, types)
        if not types:
            report.add(where(line), "warn", "jsonld-no-type", "JSON-LD without @type")
        for t in types:
            if not isinstance(t, str):
                report.add(where(line), "warn", "jsonld-bad-type", f"@type must be a string, not {json.dumps(t)}")
            elif t in RETIRED_TYPES:
                report.add(where(line), "info", "jsonld-retired",
                           f"{t}: Google no longer shows {RETIRED_TYPES[t]} rich results")
        nodes = data if isinstance(data, list) else [data]
        if not all(isinstance(n, dict) and "@context" in n for n in nodes):
            report.add(where(line), "warn", "jsonld-no-context", "JSON-LD without @context")
    if p.text_len < MIN_TEXT and p.scripts:
        report.add(where(), "warn", "little-text",
                   f"only {p.text_len} characters of text in the HTML; crawlers that do not run JavaScript "
                   "(most AI crawlers) see an almost empty page: render it on the server or prerender it")
    return p


def parse_robots(text):
    """Groups as (user-agents, rules) and the Sitemap URLs, per RFC 9309."""
    groups, sitemaps = [], []
    agents, rules, in_rules = [], [], False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (x.strip() for x in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if in_rules:
                groups.append((agents, rules))
                agents, rules, in_rules = [], [], False
            agents.append(value.lower())
        elif key in ("allow", "disallow"):
            in_rules = True
            if value:
                rules.append((key == "allow", value))
        elif key == "sitemap":
            sitemaps.append(value)
    if agents:
        groups.append((agents, rules))
    return groups, sitemaps


def rule_matches(pattern, path):
    regex = re.escape(pattern).replace(r"\*", ".*")
    if regex.endswith(r"\$"):
        regex = regex[:-2] + "$"
    return re.match(regex, path) is not None


def can_fetch(groups, bot, path="/"):
    """Exact user-agent match, else the * group; the longest matching rule wins, allow on a tie."""
    bot = bot.lower()
    rules = [r for agents, rs in groups if bot in agents for r in rs]
    if not any(bot in agents for agents, _ in groups):
        rules = [r for agents, rs in groups if "*" in agents for r in rs]
    best = None
    for allow, pattern in rules:
        if rule_matches(pattern, path):
            key = (len(pattern), allow)
            if best is None or key > best[0]:
                best = (key, allow)
    return True if best is None else best[1]


def check_robots(where, text, report):
    groups, sitemaps = parse_robots(text)
    for bot, engine in SEARCH_BOTS.items():
        if not can_fetch(groups, bot):
            report.add(where, "warn", "search-bot-blocked", f"{bot} may not crawl /: the site drops out of {engine}")
    for bot in TRAINING_BOTS:
        if not can_fetch(groups, bot):
            report.add(where, "info", "training-bot-blocked", f"{bot} blocked (training crawler; the owner's choice)")
    return sitemaps


def check_sitemap(where, text, report):
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        report.add(where, "warn", "sitemap-invalid", f"sitemap is not valid XML: {e}")
        return
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    locs = root.findall(f".//{ns}loc")
    lastmods = root.findall(f".//{ns}lastmod")
    if not locs:
        report.add(where, "warn", "sitemap-empty", "sitemap lists no URLs")
    elif not lastmods:
        report.add(where, "info", "sitemap-no-lastmod", "no lastmod; an accurate lastmod helps engines recrawl changes")


def html_files(folder):
    for root, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if name.lower().endswith((".html", ".htm")):
                yield os.path.join(root, name)


def check_site_folder(folder, report):
    robots_path = os.path.join(folder, "robots.txt")
    sitemaps = []
    if os.path.isfile(robots_path):
        with open(robots_path, encoding="utf-8", errors="replace") as f:
            sitemaps = check_robots(robots_path, f.read(), report)
    else:
        report.add(folder, "info", "no-robots", "no robots.txt in this folder (fine if the server generates one)")
    local = [os.path.join(folder, n) for n in ("sitemap.xml", "sitemap-index.xml", "sitemap_index.xml", "sitemap-0.xml")]
    found = [p for p in local if os.path.isfile(p)]
    for p in found:
        with open(p, encoding="utf-8", errors="replace") as f:
            check_sitemap(p, f.read(), report)
    if not found and not sitemaps:
        report.add(folder, "warn", "no-sitemap", "no sitemap found (neither a sitemap file nor a Sitemap line in robots.txt)")


def check_site_url(origin, report):
    status, _, body = fetch(origin + "/robots.txt")
    sitemaps = []
    if status == 200:
        sitemaps = check_robots(origin + "/robots.txt", body, report)
    else:
        report.add(origin + "/robots.txt", "info", "no-robots", f"robots.txt not served (status {status})")
    for url in sitemaps or [origin + "/sitemap.xml"]:
        status, _, body = fetch(url)
        if status == 200:
            check_sitemap(url, body, report)
        else:
            report.add(url, "warn", "no-sitemap", f"sitemap not reachable (status {status})")


def main(argv):
    show_info = "--no-info" not in argv
    targets = [a for a in argv if not a.startswith("--")]
    unknown = [a for a in argv if a.startswith("--") and a != "--no-info"]
    if unknown or not targets:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 1
    report = Report(show_info)
    pages = {}
    origins = []
    for t in targets:
        if t.startswith(("http://", "https://")):
            status, headers, body = fetch(t)
            if status != 200:
                report.add(t, "warn", "http-status", f"status {status}: {body[:120] if status is None else ''}".strip())
                continue
            pages[t] = check_page(t, body, headers, report)
            parts = urllib.parse.urlsplit(t)
            origin = f"{parts.scheme}://{parts.netloc}"
            if origin not in origins:
                origins.append(origin)
        elif os.path.isdir(t):
            for f in html_files(t):
                with open(f, encoding="utf-8", errors="replace") as fh:
                    pages[f] = check_page(f, fh.read(), {}, report)
            check_site_folder(t, report)
        elif os.path.isfile(t):
            with open(t, encoding="utf-8", errors="replace") as fh:
                pages[t] = check_page(t, fh.read(), {}, report)
        else:
            print(f"seo_check: not found: {t}", file=sys.stderr)
            return 1
    for origin in origins:
        check_site_url(origin, report)

    indexed = {name: p for name, p in pages.items() if p is not None}
    for attr, rule in (("title", "duplicate-title"), ("description", "duplicate-description")):
        seen = {}
        for name, p in indexed.items():
            value = getattr(p, attr)
            if value:
                seen.setdefault(value, []).append(name)
        for value, names in seen.items():
            if len(names) > 1:
                report.add(names[0], "warn", rule, f"same {attr} on {len(names)} pages: {', '.join(names[1:])}")
    by_canonical = {p.canonical: (name, p) for name, p in indexed.items() if p.canonical}
    for name, p in indexed.items():
        for code, href in p.alternates:
            if href in by_canonical and href != p.canonical and p.canonical:
                other_name, other = by_canonical[href]
                if p.canonical not in [h for _, h in other.alternates]:
                    report.add(other_name, "warn", "hreflang-not-reciprocal",
                               f"{name} lists this page as '{code}', but this page does not link back")

    n = len(pages)
    print(f"seo_check: {report.warnings} warnings, {report.notes} notes in {n} page{'' if n == 1 else 's'}")
    return 2 if report.warnings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
