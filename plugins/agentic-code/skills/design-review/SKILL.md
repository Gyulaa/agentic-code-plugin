---
name: design-review
description: Use to review a user interface - a page, screen, flow or component, on the web or in an iOS, Android or Flutter app - for accessibility, craft, platform fit, generic machine-made patterns and copy, after a large UI change or when the user asks for a design review, a UI audit or feedback on how something looks or reads. Reports findings ranked by severity with evidence, and changes nothing until the user picks what to fix.
argument-hint: "[page, screen, flow or path]"
---

# Design review

A review finds what blocks the user and the goal first, and polish last. It shares its rules with the `design` skill, whose files it reads: `${CLAUDE_PLUGIN_ROOT}/skills/design/references/` (`anti-patterns.md`, `web.md`, `native.md`, `product-ui.md`, `copy.md`). Read the ones the surface needs.

## 1. Scope and context
- What is reviewed (pages, screens, a flow, a component), on which platforms, and what it is for: the one action it must lead to.
- The project's `DESIGN.md` if it exists (the review measures against it, not against taste), and the surface's mode (Persuade, Operate, Read, Experience; see the `design` skill).
- Ask only what cannot be seen: the audience, the goal, known constraints.

## 2. Look at the real thing
- Rendered screenshots, as in `design` §5: three widths on the web (about 375, 768 and 1440 px), a small and a large device natively, light and dark, the largest text size. If no screenshot tool is available, say so, suggest one, and review from the code and from screenshots the user provides.
- The accessibility tree or page text for headings, labels, names and reading order; it is cheaper than images and shows what screen readers and agents get.
- The code for what pictures hide: tokens versus literals, states, focus styles, reduced-motion handling.
- Optional, on request: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/slop_check.py" <paths>` for code-level tells.

## 3. Check everything in one pass
**Floor (accessibility and platform):** text and UI contrast measured (WCAG 2.2 AA); visible focus; targets (24 px on the web, 44 pt on iOS, 48 dp on Android); zoom and text scaling work; reduced motion honoured; labels, alt text and accessible names; keyboard order; no state shown by colour alone; platform conventions (back gesture, safe areas, system controls).

**Craft:** one primary action per view; clear hierarchy; spacing rhythm and alignment; type scale and measure; consistent radii and shadows; every state designed (empty, loading, error, partial, overflow, no permission); extreme content (long names, big numbers, empty lists); dark theme; browser surfaces (selection, scrollbars, focus ring, 404).

**Generic tells:** against `anti-patterns.md`, including the self-check: what on the screen could only belong to this client?

**Copy:** the five-second test (what is it, who is it for, what do I do next); the visitor chain from `copy.md` (arrive, understand, believe, act, complete, know what happens next), naming the element responsible for each step and its weak point; specific rather than inflated claims; the same button name through a flow; consistent voice and form of address; no fake urgency, invented proof or placeholder that looks real.

**System:** colour and size literals instead of tokens; drift from `DESIGN.md`; a second pattern next to an existing one.

**Hand-offs:** a public page that should be found in search: say in one line that `seo` applies. Third-party fonts, embeds or analytics: `privacy-check`.

## 4. Worst-case data
A screen drawn with the designer's tidy sample data hides what real data does to it. For every value the screen shows, put in the realistic worst case from `references/worst-case-data.md`: very long names without spaces, a one-character name, missing and null fields, an empty list, zero, a huge count, an extreme amount or date, accents, emoji, right-to-left text, 200% text size, a narrow width, a slow or offline load.
- Keep two data sets, the worst case and the empty or missing one, behind a **development-only** switch (compiled out of the release build, never a production setting) and in one test at the narrowest width and the largest text size.
- Report what broke, with a severity: **data loss** (a value cut off or saved wrong), **broken layout** (overlap, overflow, an unreachable control), **unreadable**, **cosmetic**; and the fix for each.
- This step does not redesign and does not judge taste: it reports what real data breaks.

## 5. Report
Ranked, most severe first, at most about ten findings unless the user asks for all:
| Severity | Meaning |
|---|---|
| **Blocker** | broken, inaccessible, misleading or legally risky |
| **Major** | hurts the goal (the action, comprehension, trust) |
| **Minor** | polish |
Each finding: where (`file:line`, or the screenshot and the region), what is wrong, why (the rule or the evidence), and the proposed fix. Then **what works and must stay**, and **what could not be checked** (a device not available, a state that could not be reproduced). No style preferences presented as defects.

## 6. Fix only what the user picks
Apply the chosen fixes with the `design` skill's rules and the project's tokens, then take new screenshots of the changed areas only, and report before and after.
