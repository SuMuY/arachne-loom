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
