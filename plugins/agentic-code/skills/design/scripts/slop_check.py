#!/usr/bin/env python3
"""Scan UI code for code-level tells of generic, machine-made design.

Usage: python3 slop_check.py [--list-rules] <file or folder> [...]
Scans CSS, HTML, JSX/TSX, Vue, Svelte, Astro and Dart files (copy rules also read
Markdown). A line containing "slop-ok" is skipped: it marks a deliberate choice.
Output: one "path:line: [rule] message" per finding, then a summary line.
Exit code: 0 no findings, 2 findings, 1 usage error.
It finds patterns, it does not judge a design: a clean run is not a good design.
Python 3 standard library only.
"""

import colorsys
import os
import re
import sys

STYLE_EXTS = {".css", ".scss", ".sass", ".less"}
MARKUP_EXTS = {".html", ".htm", ".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte", ".astro"}
DART_EXTS = {".dart"}
COPY_EXTS = {".md", ".mdx"}
ALL_EXTS = STYLE_EXTS | MARKUP_EXTS | DART_EXTS | COPY_EXTS

SKIP_DIRS = {".git", "node_modules", "dist", "build", "out", ".next", ".nuxt", ".svelte-kit",
             ".astro", ".dart_tool", ".output", "vendor", "coverage", "Pods", ".venv", "__pycache__"}

CODE = STYLE_EXTS | MARKUP_EXTS | DART_EXTS
WEB = STYLE_EXTS | MARKUP_EXTS
TEXT = MARKUP_EXTS | DART_EXTS | COPY_EXTS

# (id, extensions, pattern, message). Patterns are matched per line, case-sensitive unless (?i).
LINE_RULES = [
    ("transition-all", WEB, re.compile(r"transition(-property)?\s*:\s*all\b|\btransition-all\b"),
     "transition on all properties; name the ones that change (transform, opacity)"),
    ("scale-zero", WEB, re.compile(r"scale\(\s*0(\.0+)?\s*\)|\bscale-0\b"),
     "animating from scale(0) looks cheap; start at 0.9-0.97 with opacity 0"),
    ("ease-in", WEB, re.compile(r"\bease-in\b(?!-out)"),
     "ease-in on UI feels sluggish; use ease-out for entering and leaving"),
    ("ease-in", DART_EXTS, re.compile(r"\bCurves\.easeIn\b"),
     "Curves.easeIn on UI feels sluggish; use an ease-out curve for entering and leaving"),
    ("spring-easing", WEB | DART_EXTS, re.compile(r"\b(Curves\.elastic\w*|Curves\.bounce\w*|easeOutBack|easeInOutBack)\b"),
     "elastic or bouncing easing on UI; keep it for rare, playful moments"),
    ("gradient-text", WEB, re.compile(r"background-clip\s*:\s*text|\bbg-clip-text\b"),
     "gradient text: a common generic tell; chosen or default?"),
    ("purple-gradient", WEB, re.compile(r"\b(from|via|to)-(indigo|violet|purple|fuchsia)-\d{2,3}\b"),
     "indigo/purple gradient: the most common AI default; chosen or default?"),
    ("side-stripe", WEB, re.compile(r"border-left\s*:\s*([3-9]|\d{2,})px|\bborder-l-([4-9]|\[\d+px\])\b"),
     "thick coloured left border on a card: a generic tell; chosen or default?"),
    ("offset-shadow", WEB, re.compile(r"box-shadow\s*:\s*(-?[1-9]\d*px\s+-?\d+(px)?|-?\d+(px)?\s+-?[1-9]\d*px)\s+0(px)?\s"),
     "hard offset shadow; only inside a deliberate neo-brutalist system"),
    ("default-font", WEB, re.compile(
        r"font-family\s*:\s*[\"']?(Inter|Roboto|Arial|Helvetica|Space Grotesk)\b(?![ -](Mono|Slab|Serif|Condensed|Flex|Tight))|"
        r"\bimport\s*\{[^}]*\b(Inter|Roboto|Space_Grotesk)\b[^}]*\}\s*from\s*[\"']next/font/google"),
     "default typeface; choose a family for a reason (or mark the line slop-ok)"),
    ("default-font", DART_EXTS, re.compile(r"fontFamily\s*:\s*[\"'](Inter|Roboto|Space Grotesk)[\"']|GoogleFonts\.(inter|roboto|spaceGrotesk)(TextTheme)?\b"),
     "default typeface; choose a family for a reason (or mark the line slop-ok)"),
    ("font-cdn", WEB, re.compile(r"fonts\.(googleapis|gstatic)\.com|use\.typekit\.net|fonts\.bunny\.net"),
     "font loaded from a third-party CDN sends visitor IP addresses to it; self-host the font (privacy-check)"),
    ("font-cdn", DART_EXTS, re.compile(r"\bGoogleFonts\.\w+\("),
     "google_fonts fetches fonts at runtime by default; bundle the font files as assets"),
    ("zoom-disabled", {".html", ".htm", ".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte", ".astro"},
     re.compile(r"user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b|userScalable\s*:\s*false|maximumScale\s*:\s*1\b"),
     "zoom disabled: an accessibility failure (WCAG 1.4.4)"),
    ("em-dash", TEXT, re.compile("\u2014"),
     "em dash in user-facing text reads as machine-written; use a comma, colon, parentheses or two sentences"),
    ("inflated-copy", TEXT, re.compile(
        r"(?i)\b(revolutionary|revolutioni[sz]e|seamless(ly)?|unlock (your|the)|elevate your|supercharge|game[- ]changer|"
        r"cutting[- ]edge|next[- ]level|effortless(ly)?|world[- ]class|a testament to|in the world of|"
        r"forradalmi|zökkenőmentes\w*|új szintre emel\w*|páratlan élmény\w*)"),
     "inflated vocabulary; say the specific thing instead"),
    ("not-just", TEXT, re.compile(r"(?i)\b(it's|is) not just (a|an|about)\b.{0,60}\bit's\b|\bnem csak\b.{0,60}\bhanem\b"),
     "'not just X, but Y': a machine-writing tic"),
    ("placeholder-name", TEXT | STYLE_EXTS, re.compile(r"\b(John Doe|Jane Doe|Acme( Inc| Corp)?|Lorem ipsum)\b"),
     "placeholder that looks like content; use a visible placeholder such as [customer name], or real content"),
]

# Copy rules look at user-facing text, so comment lines in code files are skipped for them.
COPY_RULES = {"em-dash", "inflated-copy", "not-just", "placeholder-name"}
COMMENT_STARTS = ("//", "/*", "*", "#", "<!--", "{/*")

HEX = re.compile(r"#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
# A hex value in a colour position (after ":", "=", "[", "(" or ","), not an anchor such as href="#add".
COLOR_HEX = re.compile(r"[:=\[(,]\s*[\"']?#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
# Places where a literal colour is expected or no colour is meant: anchors, the theme-color meta, inline SVG paint.
LITERAL_OK = re.compile(r"(href|xlink:href|to)\s*=\s*[\"']#[^\"']*[\"']|<meta[^>]*theme-color[^>]*>|\b(fill|stroke|stop-color)\s*=\s*[\"']#\w+[\"']")
CSS_VAR_DEF = re.compile(r"(^|[{;\s])--[\w-]+\s*:")
OUTLINE_NONE = re.compile(r"outline\s*:\s*(none|0)\b|\boutline-none\b")
FOCUS_VISIBLE = re.compile(r"focus-visible")
MOTION = re.compile(r"@keyframes|\banimation\s*:|\btransition\s*:|\banimate-|\btransition-\w|framer-motion|\bmotion\.\w")
REDUCED = re.compile(r"prefers-reduced-motion|motion-reduce:|motion-safe:|useReducedMotion|reducedMotion")
DART_MOTION = re.compile(r"\bAnimationController\b|\bAnimated[A-Z]\w*\(")
DART_REDUCED = re.compile(r"disableAnimations")
DART_FONTS_BUNDLED = re.compile(r"allowRuntimeFetching\s*=\s*false")
DART_LITERAL_COLOR = re.compile(r"\bColor\(0x[0-9a-fA-F]{8}\)|\bColors\.(?!transparent\b)\w+")


def is_purple(hex_value):
    h = hex_value.lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hue, light, sat = colorsys.rgb_to_hls(r, g, b)
    return 0.66 <= hue <= 0.81 and sat >= 0.45 and 0.3 <= light <= 0.75


def iter_files(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for name in sorted(files):
                if name.endswith((".min.css", ".min.js")):
                    continue
                if os.path.splitext(name)[1].lower() in ALL_EXTS:
                    yield os.path.join(root, name)


def is_theme_file(path):
    base = os.path.basename(path).lower()
    return any(k in base for k in ("theme", "token", "color", "colour", "palette", "design_system", "tailwind.config"))


def scan(paths):
    findings = []
    has_tokens = False
    motion_at = None
    reduced = False
    dart_motion_at = None
    dart_reduced = False
    dart_fonts_bundled = False
    files = [f for f in iter_files(paths) if os.path.splitext(f)[1].lower() in ALL_EXTS]
    texts = {}
    for f in files:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                texts[f] = fh.read().splitlines()
        except OSError as e:
            print(f"{f}: cannot read: {e}", file=sys.stderr)
    for f, lines in texts.items():
        ext = os.path.splitext(f)[1].lower()
        if ext in WEB and any(CSS_VAR_DEF.search(l) and HEX.search(l) for l in lines):
            has_tokens = True
    for f, lines in texts.items():
        ext = os.path.splitext(f)[1].lower()
        joined = "\n".join(lines)
        has_focus_visible = bool(FOCUS_VISIBLE.search(joined))
        for n, line in enumerate(lines, 1):
            if "slop-ok" in line:
                continue
            comment = ext not in COPY_EXTS and line.lstrip().startswith(COMMENT_STARTS)
            for rule, exts, pattern, message in LINE_RULES:
                if comment and rule in COPY_RULES:
                    continue
                if ext in exts and pattern.search(line):
                    findings.append((f, n, rule, message))
            if ext in WEB:
                for m in HEX.finditer(line):
                    if is_purple(m.group(0)):
                        findings.append((f, n, "purple", f"{m.group(0)} is indigo/purple: chosen or default?"))
                        break
                if (has_tokens and not CSS_VAR_DEF.search(line) and COLOR_HEX.search(LITERAL_OK.sub("", line))
                        and not is_theme_file(f)):
                    findings.append((f, n, "literal-color", "colour literal next to design tokens; use the token"))
                if OUTLINE_NONE.search(line) and not has_focus_visible:
                    findings.append((f, n, "focus-removed", "focus outline removed and no :focus-visible style in this file"))
                if motion_at is None and MOTION.search(line):
                    motion_at = (f, n)
                if REDUCED.search(line):
                    reduced = True
            if ext in DART_EXTS:
                if DART_LITERAL_COLOR.search(line) and not is_theme_file(f):
                    findings.append((f, n, "literal-color", "colour literal in a widget; read it from the theme"))
                if dart_motion_at is None and DART_MOTION.search(line):
                    dart_motion_at = (f, n)
                if DART_REDUCED.search(line):
                    dart_reduced = True
                if DART_FONTS_BUNDLED.search(line):
                    dart_fonts_bundled = True
    if dart_fonts_bundled:
        findings = [x for x in findings if not (x[2] == "font-cdn" and x[0].endswith(".dart"))]
    if motion_at and not reduced:
        findings.append((motion_at[0], motion_at[1], "reduced-motion",
                         "animation found but prefers-reduced-motion is handled nowhere in the scanned files"))
    if dart_motion_at and not dart_reduced:
        findings.append((dart_motion_at[0], dart_motion_at[1], "reduced-motion",
                         "animation found but MediaQuery.disableAnimationsOf is checked nowhere in the scanned files"))
    return len(texts), findings


def main(argv):
    if "--list-rules" in argv:
        seen = []
        for rule, _, _, message in LINE_RULES:
            if rule not in seen:
                seen.append(rule)
                print(f"{rule}: {message}")
        for rule, message in (("purple", "indigo/purple hex colour"), ("literal-color", "colour literal next to tokens"),
                              ("focus-removed", "outline removed without :focus-visible"),
                              ("reduced-motion", "animation without a reduced-motion path")):
            print(f"{rule}: {message}")
        return 0
    paths = [a for a in argv if not a.startswith("-")]
    unknown = [a for a in argv if a.startswith("-") and a != "--list-rules"]
    if unknown or not paths:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 1
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        print(f"slop_check: not found: {', '.join(missing)}", file=sys.stderr)
        return 1
    unsupported = [p for p in paths if os.path.isfile(p) and os.path.splitext(p)[1].lower() not in ALL_EXTS]
    if unsupported:
        print(f"slop_check: not a file type it scans: {', '.join(unsupported)}", file=sys.stderr)
        return 1
    count, findings = scan(paths)
    for f, n, rule, message in findings:
        print(f"{f}:{n}: [{rule}] {message}")
    files = f"{count} file{'' if count == 1 else 's'}"
    if findings:
        print(f"slop_check: {len(findings)} findings in {files}")
        return 2
    print(f"slop_check: OK ({files})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
