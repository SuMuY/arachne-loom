# Existing DOCX normalization

`loom normalize` provides a conservative path for formatting an existing Word
file without rebuilding its content as a Canonical Model. It updates the
paragraph geometry for recognized Heading 1–9 styles and the geometry of
recognized native ordered and unordered list definitions. The source and
output must be different files.

```sh
loom normalize input.docx profiles/ctd/zh-CN/config.json --out output.docx
```

The operation preserves paragraph text and copies all original DOCX package
parts except `word/document.xml` and `word/numbering.xml`. It does not convert
typed markers such as `1.` or `•` into automatic numbering; those characters
may be prose, identifiers, doses, or references. It does not infer a heading
from font appearance, add missing numbering to headings, restructure nested
lists, or guarantee semantic preservation of every unsupported Word feature.
Revision markup, text boxes, headers/footers, and unusual numbering inheritance
need separate coverage before they can be claimed as supported.

Use `loom inspect` on source and output, compare extracted text and object
counts, and verify in desktop Word. Check heading hierarchy, compact
number-to-text gaps, list labels and continuation alignment, page breaks, and
save-close-reopen stability. A passing XML/package check is not a substitute
for Word visual acceptance.
