# Changelog

## 0.0.5 - Medical writing profiles and native Word formatting (2026-11-20)

- Add CTD and CSR profiles with separate chapter rules for captions.
- Support native multilevel lists and geometry normalization for recognized headings and lists in existing DOCX files.
- Apply profile settings for page, body, tables and captions, and preserve cross-reference styling after Word field updates.
- Document the Skill entry point and desktop Word acceptance.

## 0.0.4 - Accepted heading and list formatting (2026-11-18)

- Added native ordered/unordered lists, configurable global marker/text positions, and hanging indents.
- Added Markdown list parsing, independent sequences with explicit starts, configuration/model validation, and list reference manifest coverage.
- Fixed OOXML numbering definition order so Word honors heading levels and independent lists.
- Desktop Word visual and save/reopen checks completed; user accepted the revised document on 2026-11-18.
- Includes v0.0.3 heading indentation; preserves its existing tag without rewriting history.

## 0.0.3 - Hierarchical heading indentation (withdrawn; superseded by 0.0.4)

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
