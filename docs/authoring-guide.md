# Authoring Guide

Write CTD-Markdown using `docs/input-spec.md`. Assign a stable ID at authoring time to every table and figure, and use `[@object-id]` for every cross-reference. Never type a computed table or figure number, reuse an ID, or cite an object that does not exist.

The Markdown parser is an input adapter. The Canonical Model JSON and its schema are the semantic contract consumed by the compiler.

## Editing generated DOCX in Word

Caption numbers are native `STYLEREF`/`SEQ` fields inside an `rdx_` object bookmark. Do not press Enter while the cursor is in the caption label or number area, including the apparent start of the caption: Word may split the bookmark or a field across paragraphs, after which updating fields can duplicate or corrupt a reference.

To insert content before a caption, place the cursor in the preceding body paragraph and press Enter, or click after the caption title (outside the numbered field/bookmark), press Right Arrow once if needed, and then press Enter. After manual insertion, run the independent inspector; any `cross-paragraph-field`, `bookmark-spans-paragraphs`, or `object-bookmark-in-empty-paragraph` finding means the edited file must be repaired or discarded in favor of a clean generated copy.
