# Failure Modes

### Static caption numbers
**Rule**: Generate `SEQ` fields, not typed numbers.
**Why**: Insertion and deletion must renumber later objects.
**Detection**: Caption bookmarks contain `SEQ Table` or `SEQ Figure` instructions.
**Counterexample**: A table caption remains `表 2.7.3-1` after a preceding table is inserted.

### Broken references
**Rule**: Generate `REF` fields targeting an existing caption bookmark.
**Why**: A blue string is not proof of a clickable, updateable reference.
**Detection**: Every REF target must resolve in the independent manifest.
**Counterexample**: A hyperlink jumps correctly but its displayed number never updates.

### Word-split REF after caption insertion
**Rule**: Treat any `REF`, `SEQ`, or `STYLEREF` field that begins and ends in different paragraphs as a failed artifact; repair the field/bookmark boundary before further updates.
**Why**: Word can split an object/reference field when a new caption is inserted at a bookmark or field boundary. The resulting REF may display both the old and new caption results.
**Detection**: The independent inspector reports `cross-paragraph-field` and/or `crossing-bookmark` for an `rdx_` object bookmark. TOC fields are excluded because their generated results may span paragraphs.
**Counterexample**: After inserting a table, the body reference shows the old table number followed by the new table number.

### Orphan object bookmark in an empty paragraph
**Rule**: An object bookmark must start and end inside the same caption paragraph and may not be anchored in an empty paragraph.
**Why**: A blank paragraph carrying an `rdx_` bookmark start lets Word extend the reference range when a new caption is inserted.
**Detection**: The independent inspector reports `object-bookmark-in-empty-paragraph` or `bookmark-spans-paragraphs`.
**Counterexample**: An apparently blank line between a body reference and a table caption causes the reference to display two table numbers after field update.

### Missing style names
**Rule**: Resolve actual style names from the accepted base before writing STYLEREF.
**Why**: Numeric IDs and language-specific guesses are unstable.
**Detection**: Static style lookup and Word field update.
**Counterexample**: Word shows a missing-style error after updating fields.

### Dirty base template
**Rule**: Runtime base documents contain no sample captions, fields, bookmarks, static TOC, comments, revisions, or unrelated media.
**Why**: Residual content contaminates sequences and manifests.
**Detection**: ZIP-level purity audit before profile acceptance.
**Counterexample**: A template's sample `SEQ` consumes the first production number.

### Unsupported semantic input
**Rule**: Reject unsupported merged tables, literature citations, missing resources, duplicate IDs, and unresolved references at input time.
**Why**: A successful-looking partial compile is unsafe.
**Detection**: Validator returns a complete error list before output is written.
**Counterexample**: A literature citation is rendered as a static blue number.
