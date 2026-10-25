# Web: the craft floor and modern CSS

## Contents
- Colour
- Type
- Layout and surfaces
- Motion
- Interaction
- Browser surfaces
- Accessibility
- Images and performance

## Colour
- Define colours in OKLCH (perceptually even, so lightness steps and contrast are predictable). Derive variants with relative colour syntax, `oklch(from var(--brand) calc(l - 0.1) c h)`, and mix with `color-mix(in oklch, var(--brand) 20%, var(--surface))`. Both are Baseline in current browsers.
- Neutrals carry a little of the brand hue (chroma about 0.005 to 0.02), not pure grey.
- Contrast is measured, never eyeballed: WCAG 2.2 AA, 4.5:1 for body text, 3:1 for large text (24 px, or 18.5 px bold) and for UI parts and focus indicators. APCA can be a second opinion, never a replacement.
- Dark theme is designed, not inverted: surfaces get lighter as they rise, saturation comes down, pure black only for OLED-first designs, shadows give way to lighter surfaces and borders.
- Declare `color-scheme: light dark` (or the one you support) and a `theme-color` meta per theme.
- Colour on a coloured background: borders, shadows and secondary text take the background's hue, not grey.

## Type
- Fluid sizes with `clamp()`, for example `font-size: clamp(2rem, 1.2rem + 3vw, 3.5rem)`; a modular scale (1.2 to 1.333 for product UI, larger for marketing display).
- Body at least 16 px; inputs on mobile at least 16 px (smaller triggers zoom on iOS). Line height about 1.5 for body, 1.1 to 1.25 for display. Measure 60 to 75 characters (`max-width: 68ch`).
- `text-wrap: balance` on headings, `text-wrap: pretty` on paragraphs. Tighten large display type slightly; never below about -0.04em.
- `font-variant-numeric: tabular-nums` wherever numbers align or change (tables, prices, timers).
- Self-host fonts (`@font-face` with `font-display: swap`), subset them, preload only the one font used above the fold, and check the licence. Two families are usually enough; a variable font replaces several weights.

## Layout and surfaces
- A spacing scale on a 4 or 8 px base, used everywhere; rhythm comes from repetition, not from many values.
- Container queries (`@container`) for components that live in different widths; media queries for the page.
- Nested radii are concentric: inner radius = outer radius minus the padding between them.
- Shadows have at least two layers (a tight contact shadow and a soft ambient one), tinted toward the surface hue.
- Sticky headers and bars respect `env(safe-area-inset-*)` on phones.

## Motion
- **Easing:** entering and leaving `ease-out`, moving on screen `ease-in-out`, colour and hover `ease`; never `ease-in` for UI. The built-in curves are weak: use `cubic-bezier(0.23, 1, 0.32, 1)` (out) and `cubic-bezier(0.77, 0, 0.175, 1)` (in-out).
- **Duration:** button press 100 to 160 ms, tooltip 125 to 200 ms, dropdown 150 to 250 ms, modal or drawer 200 to 500 ms; keep UI motion under 300 ms where possible. List stagger 30 to 80 ms per item.
- **By frequency:** an action done a hundred times a day or triggered from the keyboard gets no animation; rare moments (first run, success) are where delight belongs.
- Animate only `transform` and `opacity`. Never from `scale(0)`: start at 0.9 to 0.97 with opacity 0. Set `transform-origin` toward the trigger. Never `transition: all`; name the properties.
- Ship every animation with `@media (prefers-reduced-motion: reduce)` (remove movement, keep a short fade if any), and hover effects inside `@media (hover: hover) and (pointer: fine)`.
- Entry animations without JavaScript: `@starting-style`. Page-to-page transitions: the View Transitions API, with a plain fallback.

## Interaction
- Targets at least 24 by 24 px (WCAG 2.2), 44 by 44 on touch.
- Visible `:focus-visible` on everything interactive, at 3:1 against its surroundings.
- Never disable zoom (`user-scalable=no`, `maximum-scale=1`).
- State that matters lives in the URL (filters, tabs, pagination), so back, reload and sharing work.
- Optimistic updates with undo beat confirmation dialogs for reversible actions.
- Links are `<a href>`, actions are `<button>`; never a clickable `<div>`.

## Browser surfaces
The cheapest sign that a site was built, not assembled: style `::selection`, `caret-color`, `accent-color` (checkboxes, radios, range), scrollbars (`scrollbar-color`, `scrollbar-gutter: stable`), `text-underline-offset` and `text-decoration-thickness` on links, the focus ring, the favicon in light and dark, and the `404` page.

## Accessibility
- Semantic HTML first: landmarks (`header`, `nav`, `main`, `footer`), one `h1`, headings in order, lists as lists, tables for tabular data. Native elements beat ARIA; ARIA only where no element exists.
- Every input has a visible `<label>`; errors are announced and say how to fix them.
- A skip link to `main`; a logical tab order; no keyboard traps.
- Respect `prefers-reduced-motion`, `prefers-contrast` and `forced-colors` (test in Windows high contrast mode where possible).
- In the EU, the European Accessibility Act (from June 2025) makes WCAG-level accessibility a legal duty for many consumer services.

## Images and performance
- The largest image above the fold is not lazy-loaded and has `fetchpriority="high"`; everything below the fold uses `loading="lazy"`.
- Every image has `width` and `height` (or `aspect-ratio`) so nothing shifts; AVIF or WebP with `srcset` and `sizes`.
- `alt` describes the image's purpose; decorative images get `alt=""`.
- Budgets that keep a page in the green: LCP at most 2.5 s, INP at most 200 ms, CLS at most 0.1 (75th percentile of real users).
- Prefer CSS over JavaScript animation, and system or self-hosted fonts over font services.
