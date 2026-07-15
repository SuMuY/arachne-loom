# Negative fixtures

These DOCX files are intentionally broken. They are inputs for `inspector.py`
tests and failure-mode documentation, not templates or starting documents.

- `document-word-broken.docx`: bookmark spans paragraphs / cross-paragraph field.
- `document-corrupt-after-word-edit.docx`: corruption introduced by manual Word edit.
- `document-with-lists-corrupt.docx`: list-related corruption.
- `field-split-after-caption-enter.docx`: caption field split by an Enter key.

Do not open these as reference output. The stable demonstration artifact is
`../build/document.docx`.
