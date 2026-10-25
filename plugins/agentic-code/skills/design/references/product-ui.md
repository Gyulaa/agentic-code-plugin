# Product UI: apps, dashboards, tables, forms

In Operate mode the user came to get something done. Precision, density that fits the task, familiar patterns and calm surfaces beat novelty. Colour is reserved for meaning (status, data, the primary action).

## Contents
- Hierarchy and density
- Tables and lists
- Forms
- Dashboards and data
- States
- Navigation and feedback
- Destructive actions

## Hierarchy and density
- One primary action per view; secondary actions look secondary.
- Density follows frequency: tools used all day can be compact (offer a comfortable option); occasional tools get more air.
- Quiet panels: separate with spacing and one surface step, not with borders, shadows and colour at once.

## Tables and lists
- Numbers right-aligned with tabular figures; text left-aligned; units in the header, not in every cell.
- Sticky header on long tables; visible sort state; a row action menu instead of five icons per row.
- Long text truncates with the full value available (tooltip, expansion); never break the layout.
- On phones, a table becomes a list of cards with the two or three fields that matter, or scrolls horizontally with the first column pinned.

## Forms
- Labels above the field, always visible (a placeholder is not a label); one column.
- Correct `type`, `inputmode` and `autocomplete` on the web; the matching keyboard type natively.
- Validate on blur or submit, not on every keystroke; the error sits next to the field, says what is wrong and how to fix it, and keeps what the user typed.
- Mark the optional fields, not the required ones, when most are required.
- The submit button says what happens ("Send request", "Save changes"); it shows progress and prevents a double submit.

## Dashboards and data
- Each chart answers one question, stated in its title. The number that matters most is the largest thing on the screen.
- Charts follow the project's data-visualisation rules if it has any; otherwise direct labels over legends, no 3D, no dual axes without need, and colour only for meaning.
- Show the time range and the freshness of the data ("updated 5 minutes ago").

## States
Design all of them, not only the happy path:
| State | What it shows |
|---|---|
| Empty (first use) | what will appear here and the one action that fills it |
| Empty (no results) | what was searched, how to widen it |
| Loading | a skeleton in the final layout's shape, only after about 300 ms; nothing that jumps when data arrives |
| Error | what happened in plain words, what the user can do, and their input kept |
| Partial or offline | what is stale or missing, and what still works |
| Too much | very long names, huge numbers, 1000 rows, 0 rows, one row |
| No permission | why, and who can grant it |

## Navigation and feedback
- The user always knows where they are (current item marked, page title matching the menu label) and how to get back.
- Toasts for confirmation of something that already happened; never for an error that needs action (keep that inline and persistent).
- Keyboard: a logical focus order, `Esc` closes overlays, shortcuts for frequent actions shown in menus or tooltips.
- Undo over "Are you sure?" for anything reversible.

## Destructive actions
- Irreversible and important (deleting an account, sending money): a confirmation that names the thing ("Delete project 'Spring catalogue'?"), and for the most serious, typing its name.
- The destructive button is styled as destructive and is not the default focus.
