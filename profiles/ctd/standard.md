# CTD Standard Format Contract

This profile defines one default CTD standard with explicit task-level overrides. It does not infer semantic structure from arbitrary DOCX.

## Required behavior

- Content, visible text, table data, resources, and declared relationships come from the Canonical Model.
- Headings use Word Heading semantics and profile-resolved style roles.
- Captions use localized display labels plus native `STYLEREF` and `SEQ` fields.
- Body references use `REF bookmark \h` and display label plus number only.
- Word must be able to open, update, edit, and continue managing the result.

## Presentation defaults

- CTD headings are upright (not italic), including level 4 and below.
- Table and figure captions are 12 pt, bold, centered, single-spaced, with 0 pt before and 6 pt after.
- Figures are centered in their own paragraph; figure captions remain below the image.
- The body TOC defaults to Heading 1-3. A task may explicitly raise this with `tocMaxLevel` (1-9); it must not be inferred from the source.
- TOC, table-list, and figure-list headings are front matter: they do not consume body chapter numbers. Entries retain document occurrence order.

The v0 engine supports Letter/A4 page configuration, Times New Roman body text, 1.5 line spacing, justified body paragraphs, 10.5 pt tables, and native clickable REF fields with blue initial text. Color after Word field refresh requires desktop verification. Unsupported capabilities are rejected rather than silently downgraded.
