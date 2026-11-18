# Changelog

## 0.0.3 - Hierarchical heading indentation

- Added optional `headingStyle.indentation` with base, per-level increment, and hanging indent in points, for heading levels 1–9.
- Synchronized heading styles, native multilevel numbering, and tab stops so wrapped text aligns with heading text.
- Reject malformed, negative, non-finite, and unknown indentation settings. Existing profiles retain their previous layout.
- Added a runnable Chinese example and regression coverage for Chinese/English profiles.
- Automated OOXML checks cover the new geometry; desktop Word observations are recorded in the heading indentation guide.

## 0.0.2 - Word-probed

- Recorded target Word acceptance for figure captions/references and body/table/figure lists.
- Added the manual-edit boundary rule for caption field/bookmark starts.
- Kept the minimal table/reference document as the stable v0 handoff and retained figure/list output as a separate tested artifact.

## 0.0.1 - provisional

- Added Canonical Model, CTD-Markdown parser, validator, native-field generator, independent inspector, and CLI.
- Added a clean python-docx base document for development only; desktop Word purity evidence remains required.
- Explored a styled `HYPERLINK \l` wrapper around an updateable `REF` field; it was not retained as the v0 baseline because target Word behavior was not stable.
- Reverted the v0 baseline to plain `REF bookmark \h` after target Word rejected tested `CHARFORMAT` and `MERGEFORMAT` switches; blue/underline persistence remains open.
