---
name: design
description: Use when building or redesigning a user interface - a website, landing page, web app, dashboard, form, or an iOS, Android or Flutter app - or when the user asks for a design, a look, a theme, a design system or UI copy. Produces modern, distinctive work that does not look machine-made - reads or writes the project's DESIGN.md (Google Stitch format), picks how much expression the surface allows, plans before coding, builds with the project's own tokens and components, writes the copy, and checks the rendered result in screenshots.
argument-hint: "[what to design]"
---

# Design

Without direction, a model converges on the most probable look: Inter, a purple gradient on white, a centred hero over three equal cards. Banning one default only moves it to the next. This skill replaces defaults with decisions taken from the subject, the audience and the project's own design system. Accessibility and the platform's conventions are the floor; distinctiveness is built on top of them, never instead.

Files next to this SKILL.md, read when the step needs them:
- `references/anti-patterns.md`: the tells of generic, machine-made design. Read it before planning.
- `references/web.md`: CSS, colour, type, motion numbers, browser surfaces, performance.
- `references/native.md`: iOS, Android and Flutter.
- `references/product-ui.md`: dashboards, tables, forms, navigation and every state.
- `references/copy.md`: copywriting, persuasion that holds up, voice and tone.
- `templates/DESIGN.md`: the project design file.
- `scripts/slop_check.py`: a pattern scan, run on request.

## 1. Context first
- Read `DESIGN.md` at the project root and the theme or token files it names. It wins over this skill's defaults; the user's brief wins over both.
- **No `DESIGN.md` and a new direction or a redesign:** ask in one round (the question tool if available): who uses it, on what device and how often; the one action it must lead to; the voice (`references/copy.md`, Voice) and, in languages that have it, the form of address; what exists (brand colours, logo, fonts, sites or apps they like and dislike, real photos); what is off limits. Then write `DESIGN.md` from `templates/DESIGN.md` and show it.
- **An existing UI without `DESIGN.md`:** derive the file from the code (theme, tokens, components) instead of inventing a new system, and ask before changing direction.
- **A small change inside an existing UI:** don't force a `DESIGN.md`; follow what is there.

## 2. Pick the mode: how much expression fits
| Mode | Surfaces | What it means |
|---|---|---|
| **Persuade** | landing page, pricing, campaign, product site | bold, a world of its own, one memorable idea |
| **Operate** | app, dashboard, admin, forms, settings | precision and restraint, familiar patterns; the brand lives in type, palette, density and one signature detail |
| **Read** | documentation, articles, blog, help | typography, measure and rhythm lead; nothing competes with the text |
| **Experience** | portfolio, gallery, event, showcase | the work leads, the interface recedes |
A product usually has several: decide per surface (the marketing site persuades, the app operates). "Not generic" means something different on a dashboard than on a landing page.

## 3. Plan before code
Write a short plan in the reply:
- **Direction from the subject:** three to five words from the domain (its materials, tools, places, vocabulary), and what only this client has (real photos, data, history, a process). Not "modern and clean".
- **Palette:** four to six named colours in OKLCH by role (surface, text, primary action, accent, states), neutrals tinted toward the brand hue, contrast pairs checked against WCAG 2.2 AA (4.5:1 for text, 3:1 for large text and UI parts).
- **Type:** roles (display, text, UI and numbers), each family chosen for a reason; a scale; body measure 60 to 75 characters.
- **Layout:** an ASCII sketch of the key screen at phone and desktop width, and where the one bold move is.
- **Motion:** what moves, why and for how long (`references/web.md` or `references/native.md`).
- **The generic test:** would I propose the same for any similar brief? Check the plan against `references/anti-patterns.md`. If yes, change the direction, not one colour.
For a new direction or a redesign, wait for the user's OK. For a component inside an existing system, go on.

## 4. Build
- Use the project's components, tokens and patterns (`match-the-codebase`). A new token goes into `DESIGN.md` and the theme file in the same change.
- Web: `references/web.md`. Product UI: `references/product-ui.md`. iOS, Android, Flutter: `references/native.md`. All text: `references/copy.md`.
- Every interactive element has its states (default, hover on pointer devices, focus-visible, active, disabled, loading); every data view has empty, loading, error, partial and overflowing content.
- Real content: realistic lengths, licensed images with credit (the client's own, Openverse, Wikimedia Commons, or a stock licence the user holds), and visibly marked placeholders such as `[client name]` instead of invented names, quotes, logos or numbers.
- Fonts are self-hosted and their licence checked. Loading them from a third-party CDN sends every visitor's IP address to that company; a German court found this unlawful without consent (`privacy-check`).
- 3D or heavy WebGL only when the subject is spatial (a product to turn, a place, data with depth) and the mode is Persuade or Experience: load it lazily, give a still fallback, respect reduced motion, and keep the page fully usable without it.

## 5. Check the rendered result
- **Screenshots with what the session has:** Playwright MCP, Claude in Chrome, Chrome DevTools MCP or a built-in browser for the web; `xcrun simctl io booted screenshot <file>`, `adb exec-out screencap -p > <file>`, `flutter screenshot`, or golden tests where the project already has them, for native. If nothing is available, say so, suggest Playwright MCP (`claude mcp add playwright -- npx @playwright/mcp@latest`), and meanwhile ask the user for screenshots.
- **Web:** three widths (about 375, 768 and 1440 px), light and dark if both exist. **Native:** a small and a large device, and the largest text size.
- **Batch it:** look at everything at once, name the three biggest problems (hierarchy, spacing rhythm, contrast, alignment, generic look, a broken state), fix them together, then look again. At most three rounds; then report what is left. Screenshots are expensive (`working-mode` §6): crop to the area, and check text through the accessibility tree or page text instead.
- **Pattern scan, on request** or before handing over a large piece: `python3 "${CLAUDE_SKILL_DIR}/scripts/slop_check.py" <files or folders>`. It finds code-level tells (animating everything, gradient text, zoom disabled, a CDN font, inflated copy); it does not judge the design. A line containing `slop-ok` is a deliberate choice and is skipped.
- **Real data, before handing over:** try the worst case, not the sample (very long names, empty, zero, huge, 200% text): the step and the catalogue are in `design-review` (`${CLAUDE_PLUGIN_ROOT}/skills/design-review/references/worst-case-data.md`).
- For a large change, finish with `design-review`. A public page that should be found in search also gets `seo`.

## Never
- Disable zoom, remove the focus ring without a visible replacement, show state by colour alone, autoplay sound, or bury the primary action under decoration.
- Fake urgency or scarcity, invented testimonials, reviews, logos, ratings or numbers (`references/copy.md`, Never).
- Copy a real company's identity unless it is the user's own.
