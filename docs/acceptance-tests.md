# Acceptance Tests

Static checks verify ZIP/XML integrity, field/bookmark targets, input hashes, and expected-versus-actual manifests. The release gate additionally requires desktop Microsoft Word evidence for:

1. Open without repair, permissions, or text recovery prompts.
2. Update all fields without missing-style or missing-reference errors.
3. Click a body reference and jump to the target caption; display only label and number.
4. Confirm Word's caption/cross-reference dialogs recognize generated objects.
5. Insert a same-kind caption and continue the chapter numbering rule.
6. Insert, move, and delete objects, then update numbering, references, and lists.
7. Save, close, reopen, and confirm fields, bookmarks, navigation, and visible output remain stable.

Manual-edit boundary test: insert a new object from a body paragraph or from after the caption title. Do not insert by pressing Enter at the caption's label/number start; that position is an object-bookmark/field boundary in the generated DOCX and Word can split it. Inspect the saved file after the edit and reject it if a native field crosses paragraphs or an `rdx_` bookmark spans paragraphs.

## Figure probe (v0.1)

Use only `examples/quickstart/build-figure-no-lists/document.docx` for this probe. Confirm that the image is present, the figure caption is centered below it, the body figure reference jumps to the caption, and updating fields preserves the figure number. Insert a second figure from a body paragraph, update fields, and confirm both figure captions and references renumber. Do not enable table/figure lists in this probe.

## Lists probe (v0.2)

Compile `examples/quickstart/figure-sample.md` with `examples/quickstart/figure-config.json` into a separate output directory. The result must contain native `TOC \\o`, `TOC \\c "Table"`, and `TOC \\c "Figure"` fields. In desktop Word, update all fields and confirm the body TOC includes Heading 1-4, the table list contains the table caption, and the figure list contains the figure caption. Then insert a new table and figure from body paragraphs, update all fields, and confirm all three lists and all body references remain correct. Any field/bookmark split or duplicate caption result fails this probe.

The verified minimal closure currently covers a Chinese title, one table, one caption, and one body REF under Microsoft Word for Mac 16.110.3. Body reference color persistence is an accepted v0 deviation.
