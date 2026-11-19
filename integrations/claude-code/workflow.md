# Claude Code Workflow

1. Route the input. For Markdown/Canonical Model, read `docs/authoring-guide.md`, preserve supplied content, and use `parse`, `validate`, and `compile`.
2. For an existing DOCX, first run `loom inspect` and review the structure and limitations. The `normalize` command edits only recognized native Heading 1-9 paragraphs and native ordered/unordered list definitions. Always write to a different output path; never overwrite the source. Nested lists are unsupported and must remain unchanged or be reported for a separate conversion task.
3. Example: `loom normalize input.docx profiles/ctd/zh-CN/config.json --out output.docx`. The current normalizer preserves document text and all package parts other than body paragraph properties and list numbering geometry. It does not convert manual typed numbering, infer headings from visual appearance, support nested lists, or guarantee every feature of arbitrary Word files.
4. If semantic classification is uncertain, stop and report the paragraphs that need author confirmation. Do not turn every `1.` or bullet-like character into a list. Treat headings, ordered lists, unordered lists, and body text as distinct structures. Generated list markers must remain native Word numbering; typed markers plus tabs are not an equivalent result.
5. For headings, use native heading styles and native multilevel numbering. Set profile indentation from the longest expected rendered label in the target font; use a compact hanging width that fits. For lists, retain Word-native numbering and consistent text start/hanging alignment; never simulate numbering by inserting tabs after typed markers.
6. Compare source and output text, tables, images, fields, bookmarks, section properties, and package-part hashes. Verify in desktop Word: heading levels step inward and same-level headings align; number-to-text spacing is compact; continuation lines align with text; lists remain native; no marker-only line or unintended break separates a label from its text. Save, close, reopen, and repeat the visual checks. Static XML checks alone do not establish acceptance.
7. Give an independent reviewer the original requirement, manifests, and output DOCX.

If output is wrong, classify evidence before changing anything: compiler/profile defect, workflow ambiguity, or unsupported input structure. Fix the reusable capability or disclose the exact limitation; do not substitute an ad hoc file-specific patch for a reusable normalizer.

No Claude SDK is imported by the compiler.
