---
version: alpha
name: "{{PRODUCT_NAME}}"
description: "{{ONE_SENTENCE: what it is and who it is for}}"
colors:
  primary: "{{oklch(...) or #RRGGBB: the main action}}"
  on-primary: "{{text on primary}}"
  secondary: "{{supporting colour}}"
  tertiary: "{{accent, used sparingly}}"
  neutral: "{{page surface, tinted toward the brand hue}}"
  on-neutral: "{{body text}}"
  error: "{{error}}"
  neutral-dark: "{{page surface in dark theme; delete the -dark tokens if there is no dark theme}}"
  on-neutral-dark: "{{body text in dark theme}}"
typography:
  display:
    fontFamily: "{{display family}}"
    fontSize: "{{3rem}}"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "{{-0.02em}}"
  headline:
    fontFamily: "{{display or text family}}"
    fontSize: "{{2rem}}"
    fontWeight: 600
    lineHeight: 1.2
  body:
    fontFamily: "{{text family}}"
    fontSize: "{{1rem}}"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "{{UI family}}"
    fontSize: "{{0.875rem}}"
    fontWeight: 500
    lineHeight: 1.3
rounded:
  sm: "{{4px}}"
  md: "{{8px}}"
  lg: "{{16px}}"
spacing:
  xs: "{{4px}}"
  sm: "{{8px}}"
  md: "{{16px}}"
  lg: "{{32px}}"
  xl: "{{64px}}"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "{{12px}}"
---

<!-- Compatible with the Google Stitch DESIGN.md format (version alpha): the YAML above holds the normative tokens, the sections below explain how to use them, in this order. Validate with `npx @google/design.md lint DESIGN.md` if Node is available. Delete every {{placeholder}} line that does not apply. -->

## Overview
{{Two or three sentences: the direction, taken from the subject (its materials, places, vocabulary), and what only this product has.}}

- **Audience and use:** {{who, on what device, how often, in what situation}}
- **The one action:** {{what a visitor or user should do}}
- **Mode:** {{Persuade / Operate / Read / Experience, per surface}}
- **Voice:** {{funny-serious, casual-formal, irreverent-respectful, enthusiastic-matter-of-fact}}; form of address: {{e.g. informal "you" / formal}}
- **Off limits:** {{what must never appear}}

## Colors
{{Each colour's role and where it may appear; the contrast pairs that were checked (WCAG 2.2 AA); how the dark theme differs.}}

## Typography
{{Why these families; the scale; body measure; numbers (tabular figures where they align); where the fonts are hosted and their licence.}}

## Layout
{{Grid and breakpoints; the spacing rhythm; density per surface; where the one bold move lives.}}

## Elevation & Depth
{{Shadow layers and tint, or how hierarchy works without shadows (surface steps, borders).}}

## Shapes
{{Radii by size; concentric nesting; any signature shape.}}

## Components
{{Buttons, inputs, cards, navigation: variants, every state (hover, focus-visible, active, disabled, loading), and what is never customised.}}

## Do's and Don'ts
- Do: {{a rule that keeps the direction}}
- Don't: {{a tell this product must avoid}}

## Motion
{{What moves and why; durations and easing; behaviour under reduced motion.}}

## Platforms
{{Web, iOS, Android, Flutter: what follows the platform (navigation, gestures, controls) and what stays the brand's; where the theme lives in code (CSS custom properties, Tailwind theme, ThemeData and ThemeExtension).}}
