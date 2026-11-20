# Confirmed CTD Formatting Rules

### Native Word semantics
**Rule**: Use Heading styles, native caption fields, bookmarks, and `REF` fields for objects and references.
**Why**: Visual text cannot update or remain linked when objects move.
**Detection**: Inspect style, field, bookmark, and relationship structures.
**Counterexample**: A caption that looks numbered but contains only ordinary text.

### Content preservation
**Rule**: Do not rewrite visible text while applying formatting.
**Why**: Formatting is not authorization to edit scientific content.
**Detection**: Compare extracted model text, table cells, and resource lists with the generated document.
**Counterexample**: Adding spaces or changing a displayed label while compiling.

### Style-name resolution
**Rule**: Resolve `STYLEREF` using the accepted base's actual style name, never a numeric style ID.
**Why**: Word reports a missing-style error when a numeric ID is used as a style name.
**Detection**: Every `STYLEREF` name must exist in `styles.xml` and match the profile role.
**Counterexample**: `STYLEREF 3` in a document whose style is named `Heading 3`.

### Heading numbering binding
**Rule**: Keep Heading style numbering, numbering-level `pStyle`, and heading paragraph `numPr` consistent.
**Why**: Word's caption dialog and numbering engine use all three bindings.
**Detection**: Static checks plus desktop Word caption insertion.
**Counterexample**: A heading style with numbering metadata but a paragraph without `numPr`.

### Heading and caption presentation
**Rule**: Clear inherited italic from all heading levels and render captions as centered, bold 12 pt paragraphs with 0/6 pt before/after spacing.
**Why**: Locale base styles may carry presentation defaults that conflict with the CTD contract even when the semantic Heading/Caption role is correct.
**Detection**: Inspect generated paragraph style and direct paragraph properties; verify the figure paragraph is centered and the caption follows it.
**Counterexample**: A level-4 heading appears italic because the base template's Heading 4 was italic, or a figure title is left-aligned.

### TOC depth
**Rule**: Emit `TOC \\o` with the profile's default maximum level unless the task explicitly supplies `tocMaxLevel`.
**Why**: TOC depth is a document-level presentation decision; guessing it from observed heading depth makes outputs unstable.
**Detection**: Compare the emitted instruction in expected and actual manifests.
**Counterexample**: A document contains level-4 sections but the task did not authorize expanding the default three-level TOC.

### Front-matter ordering
**Rule**: Keep directory headings outside the body multilevel numbering; sort entries by their source-document occurrence order.
**Why**: Front matter must not consume chapter numbers, while occurrence order preserves Word's native TOC/list semantics.
**Detection**: Directory-heading paragraphs have no `numPr`; expected and actual manifests preserve object order.
**Counterexample**: `目录` becomes chapter 2 and shifts the first body heading, or table entries are alphabetized instead of following caption order.

### Caption scope
**Rule**: A caption bookmark encloses only its localized label and computed number.
**Why**: REF must not display the full title when the profile requests label-and-number.
**Detection**: Extract bookmark text and compare it with cached REF values.
**Counterexample**: A bookmark spanning the entire caption title.

### Reference display styling
**Rule**: Use one native `REF bookmark \* CHARFORMAT \h` field.
**Why**: Desktop Word preserved the reference style with this switch order. Putting the formatting switch after the navigation switch caused an update error.
**Detection**: Check the REF target and switch order. Update and save the document in desktop Word, then check the displayed text and effective character style.
**Counterexample**: A visually blue reference uses an unsupported switch and displays a Word error after updating.

### Resource containment
**Rule**: Read images only from the declared resource root and reject traversal or external URLs.
**Why**: Deterministic builds must not fetch undeclared content.
**Detection**: Resolve and compare canonical paths before opening the file.
**Counterexample**: A figure source of `../../secret.png`.
