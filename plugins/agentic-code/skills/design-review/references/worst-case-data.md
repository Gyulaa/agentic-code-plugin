# Worst-case data

The catalogue for `design-review` §4. For each value on the screen, pick the entries that can really occur in this product and put them in. Examples are invented.

## Text
| Case | Try |
|---|---|
| Long name with spaces | `Maximiliana-Charlotte von Hohenzollern-Sigmaringen-Wittelsbach` |
| Long word without spaces or hyphens | `Konstantinopolitanischerdudelsackpfeifer` (can break any container that does not wrap or shrink) |
| Unbreakable string | a 60-character e-mail address, a URL, a file name without separators |
| One character, or only initials | `X`, `J. K.` (avatars, greetings, sort keys) |
| Missing | `null`, an empty string, only spaces; a field the server omitted |
| Accents and scripts | `Åsa Öztürk`, `Zażółć gęślą jaźń`, Chinese, Arabic |
| Right to left | Arabic or Hebrew text, and a mixed line with a number in it |
| Emoji and combined characters | `👩🏽‍💻`, flags, text that ends in an emoji (cut mid-character?) |
| Line breaks inside a value | a note with three paragraphs where a one-line label is expected |
| Markup-looking text | `<b>`, `&amp;`, a literal `{{name}}` (is it shown as text?) |

## Numbers, money, dates
| Case | Try |
|---|---|
| Zero, negative | `0`, `-1`, `-0.00` |
| Huge | `9 999 999` items, `1 234 567 890.99` as an amount; does the column grow or clip |
| Many decimals, rounding | `0.1 + 0.2`, `2.675`, a price that rounds to zero |
| Another currency or locale | a different decimal separator and symbol position |
| Dates | midnight, 29 February, a year boundary, a date far in the past or future, another time zone, a value with no date at all |
| Counts | `0`, `1` ("1 items"), `2`, `99+`, `10 000` |

## Lists and structure
| Case | Try |
|---|---|
| Empty list | the empty state, not a blank page |
| One item, and thousands | spacing with one; scrolling, paging and speed with many |
| Very long single row | a row whose every field is at its maximum at the same time |
| Deep nesting | a category tree ten levels deep |
| Missing related data | an order whose customer was deleted; an image that fails to load |

## Environment
| Case | Try |
|---|---|
| Text size | 200% on the web (browser zoom and text-only zoom); the largest system size on iOS and Android |
| Width | 320 px, or the smallest supported phone, and a very wide window |
| Orientation and split view | landscape, a narrow window |
| Slow, offline, failing | a request that takes 10 seconds; one that fails; a response that returns empty |
| Permissions | denied, restricted, not asked yet |
| Dark theme and high contrast | the same worst-case data in each |

## How to put it in
- **A development-only switch:** a flag that exists only in debug or development builds (compiled out of the release, never a setting a customer can flip) that swaps the data source for the worst-case set, and a second flag for the empty and missing set. Where the project has component previews or stories, add the two sets there too and skip the flag.
- **One test** that renders the screen with the worst-case set at the narrowest width and the largest text size, and fails on an overflow or an exception. Many frameworks report overflow themselves; use that.
- Do not add the data to production fixtures or seed data.

## Reporting
| Severity | Meaning | Example |
|---|---|---|
| **Data loss** | a value is cut off, rounded or saved wrong | the amount `1 234 567.89` shows as `1 234 56…` and is what the user confirms |
| **Broken layout** | overlap, overflow, an unreachable control, a layout that jumps | a long name pushes the "Save" button off screen |
| **Unreadable** | text is clipped, too small or loses contrast | two-line text in a one-line box |
| **Cosmetic** | ugly but usable | an awkward wrap |
For each: where, what you put in, what happened, the fix. Typical fixes: let text wrap or truncate with an explicit maximum of lines and a way to see the full value; give flexible children a minimum width of zero so they can shrink; set a sensible maximum width and break long words deliberately; reserve space for the empty and loading states; format numbers and dates with the locale; handle `null` where the value is read, not where it is shown.
