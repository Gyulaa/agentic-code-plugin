# Native: iOS, Android and Flutter

On native platforms the platform's guidelines decide the structure (navigation, gestures, controls); the brand lives in the themable layer (colour, type, shape, imagery, one signature detail). An app that fights its platform feels broken before it feels distinctive.

## Contents
- iOS
- Android
- Flutter
- Cross-platform apps

## iOS
- **Liquid Glass** (iOS 26 and later) belongs to the navigation and control layer (tab bars, toolbars, sheets), not to content. Use the system materials and components rather than hand-drawn blur, and still measure contrast: glass over busy content can fail it.
- Dynamic Type: every text style scales; test at the largest accessibility size. SF Symbols for icons, matched to the text weight.
- Targets at least 44 by 44 pt. Semantic system colours (`label`, `secondaryLabel`, `systemBackground`) so light, dark and increased contrast work.
- Keep the system navigation: large titles where they fit, swipe-back always on, sheets with detents, the system share sheet.
- Haptics sparingly, for confirmation and selection, never decoration. Respect Reduce Motion and Reduce Transparency.

## Android
- **Material 3** (and its Expressive update): colour by role (`primary`, `onPrimary`, `surface`, `surfaceContainer…`, `error`), dynamic colour from the wallpaper where the brand allows, shape and motion tokens. Expressive adds spring-based motion, shape morphing and bolder type; use it where it serves the task, not everywhere.
- Targets at least 48 by 48 dp; text in `sp` so it follows the user's font size.
- Edge-to-edge layout with proper insets; predictive back supported.
- Follow the platform's navigation patterns (navigation bar, rail or drawer by width).

## Flutter
- **Theme in one place:** `ThemeData` with a `ColorScheme` (from `ColorScheme.fromSeed` or written by hand from `DESIGN.md`), a `TextTheme` and component themes. Project-specific tokens (spacing, radii, extra colours) in a `ThemeExtension`, read with `Theme.of(context).extension<…>()`; no colour or size literals in widgets.
- **Material and Cupertino packages:** these are moving out of the framework into standalone packages (`material_ui`, `cupertino_ui`). Follow the imports the project already uses; in a new project, check the current Flutter migration guide before choosing.
- **Adaptive, not identical:** use the `.adaptive` constructors where they exist (switches, sliders, progress indicators, dialogs) and branch on `Theme.of(context).platform` for navigation and gestures. iOS users expect swipe-back and Cupertino-style page transitions.
- **Accessibility:** text scales with `MediaQuery.textScalerOf(context)` (test at 200%); `Semantics` labels for icon-only buttons; `MediaQuery.disableAnimationsOf(context)` honoured by every custom animation; `SafeArea` for notches and home indicators; targets at least 48 by 48.
- **Motion:** implicit animations (`AnimatedContainer`, `AnimatedOpacity`) for simple state changes, with `Curves.easeOutCubic` or similar for entering; never `Curves.easeIn` for UI. Durations as on the web.
- **Checking:** `flutter screenshot` from a running device, or golden tests where the project uses them (`matchesGoldenFile`), on a small and a large device size and at a large text scale.
- **Flutter web is not for content that must be found in search:** its output does not give search engines indexable text. Build marketing, landing and help pages in HTML (or a DOM-based Dart framework) and keep the app in Flutter (`seo`).

## Cross-platform apps
A Material-based app on iPhone still owes iOS users the platform's guarantees: safe areas, Reduce Motion, swipe-back, Dynamic Type, the system share sheet and keyboard behaviour. Decide per platform which parts adapt (navigation, dialogs, pickers) and which stay the brand's (colour, type, illustration).
