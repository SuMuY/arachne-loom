# Word Acceptance Log

This log records desktop behavior observed for the current v0 baseline. It is evidence for the package, not a replacement for the independent static inspector.

## Environment

- Application: Microsoft Word for Mac
- Version: 16.110.3 (26070318)
- License/channel shown by Word: Office LTSC Standard for Mac 2024
- Baseline: `examples/quickstart/build/document.docx`

## Minimal v0 results

| Check | Result | Notes |
|---|---|---|
| Open the generated DOCX | PASS | Opens without repair or recovery prompt. |
| Update fields | PASS | Native heading, caption `SEQ`, and body `REF` update. |
| Navigate from a body reference | PASS | The body `REF ... \\h` jumps to the caption. |
| Caption/reference management in Word | PASS | Word recognizes the generated caption/reference structure. |
| Insert a same-kind table from a body paragraph | PASS | Numbering and the body reference update correctly. |
| Body reference color after update | ACCEPTED DEVIATION | Black is accepted for v0; navigation and updating remain functional. |
| Press Enter at the caption label/number boundary | UNSUPPORTED EDIT | Word can split the object bookmark/field across paragraphs; later updates may duplicate or corrupt the reference. |

The last case is an editing boundary, not a style rule. Insert before a caption from the preceding body paragraph, or after the caption title outside the numbered field. Run `arachne-loom inspect` after manual edits and reject any cross-paragraph field/bookmark finding.

## Remaining release evidence

Save-close-reopen stability, move/delete scenarios, figure support, and TOC/table-list/figure-list behavior remain separate acceptance gates. Probe artifacts must not be treated as the stable v0 baseline until those scenarios are tested in the target Word version.

## Extended probe results

The following results were subsequently confirmed in the target Word environment using separate probe files:

- `examples/quickstart/build-figure-no-lists/document.docx`: figure, figure caption, and body figure reference passed; inserting a second figure from a body paragraph and updating fields passed.
- `examples/quickstart/build-lists-probe/document.docx`: body TOC, table list, and figure list updated correctly; inserting a table and figure from body paragraphs and updating all fields passed.

These probes are accepted for the recorded environment. The minimal `build/document.docx` remains the recommended stable v0 handoff because it has the smallest editable field surface.

## CSR regression on Word for Mac 16.115.1 (2026-11-20)

Tested implementation `8b88179`. The 62 compiler regression tests passed.

- Existing DOCX normalization: after saving and reopening the CSR copy, 133 native headings were recognized. Text starts for levels 1–4 were 54, 72, 90, and 108 pt. Paragraph text was preserved.
- CSR table captions and body references: after updating fields, saving, and reopening, the first table in each of two chapters displayed its chapter number and sequence 1. The chapter 2 reference stayed blue and underlined. Command-clicking it on page 9 jumped to the caption on page 2.
- Table layout: in print layout, the 69-row, 11-column table fit across the printable text area with no vertical grid lines. On page 2, the repeated header appeared when enabled and was absent when disabled.
- Generated DOCX headings: compiled the real CSR heading text through the normal CLI. Word displayed aligned titles at the same level and progressively indented levels 1–4. The four levels reserve 54 pt each for the number and tab. Short level-1 numbers therefore leave a visibly wider gap than the longer level-4 numbers. This verifies alignment, with compact spacing for short numbers still unresolved.
- Still pending in desktop Word: nested list insertion/restarts/wrapping and save/reopen, and CSR figure numbering across chapters. The inspected CSR source and its available Word variants contained no embedded images or paragraph numbering below list level 0.

- Compact heading follow-up: recompiled the same CSR headings and visually checked levels 1–4 in Word. Their reserved widths are now 24, 32, 42, and 54 pt. The first three levels have less space after their numbers, and same-level alignment and progressive indentation were visible. All 64 automated tests passed.

## Native nested-list verification (2026-11-20)

Used only the inclusion/exclusion criteria text from the CSR acceptance copy to construct a new list-focused DOCX; the source document was not modified. Word for Mac 16.115.1 displayed native ordered numbering 1–24, including 9-to-10 and 19-to-20 transitions. The long items wrapped to the text column, aligned under their text rather than under the number. A subordinate 1–4 list was nested under item 2 and restarted at 1 after the parent sequence advanced to item 3. This verifies initial layout and restart behavior. Save-close-reopen for this exact list-focused file remains pending; the attempted reopen was interrupted by Word's open dialog, so no persistence result is claimed.
- Nested-list save/reopen follow-up: saved the focused CSR criteria document, closed it, and reopened it in Word 16.115.1. The first and last pages retained ordered numbering through 24, the nested sequence restarted at 1 beneath its parent, and long-item continuation remained aligned. PASS.
