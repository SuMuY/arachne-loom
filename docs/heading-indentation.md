# Heading indentation

`headingStyle.indentation` is an optional profile object, applied to all body
heading levels (1–9), in both locale profiles. It uses native Word styles and
multilevel numbering, rather than typed spaces or tabs in heading text.

| Field | Meaning (points) |
| --- | --- |
| `basePt` | Level-1 number's left position, relative to the page's text margin |
| `incrementPt` | Additional inset per semantic heading level |
| `hangingPt` | Distance from number anchor to text and continuation-line start |

For semantic level L, the number anchor is `basePt + (L - 1) * incrementPt`;
the text starts at that anchor plus `hangingPt`. Values are rounded to Word's
1/20-point units. All three fields are required, finite, and non-negative.
Unknown keys are rejected to catch typos. Zero increments permit aligned levels;
a zero hanging area is accepted, but provides no reserved width for the number.

The same indentation is written into heading styles and numbering levels, with
an explicit number suffix tab and matching tab stop. Same-level headings reuse
the same style and numbering level throughout the document. Existing profiles
without this object retain the previous behavior. TOC entries, TOC titles, body
paragraphs, and captions have their own formatting and do not receive this rule.
This feature applies during generation; it does not reformat an existing DOCX.

## Runnable example

Use `examples/quickstart/indented-profile.json` with
`examples/quickstart/indented-headings.md`, following the README commands.
The example includes repeated levels and a long heading for wrap verification.
Choose a hanging area wide enough for the longest number in the actual font;
Word advances past the tab if a number outgrows that area.

## Verification

Automated regression checks compile real DOCX files for zh-CN/en-US and examine
all nine style/numbering geometries, tab positions, same-level style reuse,
invalid settings, and omitted-setting compatibility. The full existing suite
also checks captions, references, lists, and document inspection.

2026-11-18 automated verification: 22 tests passed; the new tests first failed
on missing geometry and missing config validation (15 failures, one legacy
compatibility pass), then passed after implementation. The CLI example compiled
successfully.

Desktop Word verification was attempted on 2026-11-18. Its Open dialog selected
the generated DOCX but did not open it after Open, Return, or double-click;
the final cancel operation returned computer-use timeoutReached (-10005).
The preview thumbnail is insufficient to judge wrapping. Full-size Word visual
acceptance remains pending; the release's geometry verification is automated
OOXML validation. Open the README example to check stepped number positions,
same-level alignment, and long-heading continuation lines in desktop Word.
