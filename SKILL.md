---
name: arachne-loom
description: Use when generating or formatting medical-writing DOCX files that need structured Word headings, multilevel lists, captions, cross-references, tables of contents, or conservative normalization of recognized Word-native headings and lists.
---

# Arachne Loom

Use the shared deterministic compiler to produce or conservatively normalize DOCX files. The compiler has no AI dependency; this Skill describes how an agent should prepare inputs, select configuration, verify output, and report boundaries.

## Start here

All repository-relative paths below are relative to this Skill root. Follow `README.md` → Quick start for installation and exact CLI commands. Use `examples/quickstart/config.json` as a task example and read `docs/list-formatting.md` for nested-list syntax and verification.

## Choose the path

- For structured Markdown or Canonical Model JSON, read `docs/authoring-guide.md`, preserve supplied content, then use `parse` (Markdown only), `validate`, and `compile`.
- Select the profile matching the medical document type and language: `profiles/ctd/{zh-CN,en-US}/config.json` for CTD or `profiles/csr/{zh-CN,en-US}/config.json` for CSR. The profiles share the same formatting baseline but use different caption chapter levels; see the Scope section.
- For new DOCX generation, supply the selected profile to `loom validate` and `loom compile`. Put any requested variation in a copy of the profile. Use `body.lineSpacing` (line multiplier), `body.alignment` (`left`, `center`, `right`, or `justified`), `body.paragraphAfterPt` (points), and `table.fontSizePt` (points). The compiler writes these settings as native Word paragraph and cell text formatting.
- For an existing DOCX, run `loom inspect` first and review its structure and limitations. Use `loom normalize` only for recognized native Heading 1–9 paragraphs and native ordered/unordered list definitions. Always write to a different output path; never overwrite the source.
- If heading/list semantics are uncertain, report the affected paragraphs for author confirmation. Do not infer headings from appearance or turn every `1.` or bullet-like character into a list.

## Native structure requirements

- Use Word heading styles and native multilevel numbering. Configure heading indentation from the widest expected rendered label in the target font, with a compact hanging width that fits.
- Structured Markdown supports up to nine nested list levels using two-space indentation per level. Canonical Model list items use `level` 0–8 and may specify per-level `kind` and initial `start`. Compile each list block as one native Word multilevel numbering definition. Validate emitted `ilvl`, numbering format, and restarts; never flatten nested levels or simulate numbering with typed markers and tabs.
- Generated list markers must remain Word-native numbering. Do not insert marker characters as ordinary paragraph text.
- Existing-DOCX normalization changes geometry only for recognized native headings/lists. It does not convert typed numbering, infer headings, import/rebuild the full document, or guarantee arbitrary Word features.

## Verification and handoff

1. Compare source and output text, tables, images, fields, bookmarks, section properties, and package-part hashes.
2. Run the independent inspector and resolve structural issues.
3. For new DOCX output, check the selected profile against Word’s Paragraph settings on body paragraphs and the font size of both table header and data cells. Then verify in desktop Word: heading levels step inward and same-level headings align; number-to-text spacing is compact; nested numbering, restarts, and continuation lines align; no marker-only line or unintended break separates a label from its text.
4. Save, close, reopen, and repeat the visual checks. Static XML checks alone do not establish acceptance.
5. Give an independent reviewer the original requirement, manifests, and output DOCX.

If output is wrong, classify the evidence as a compiler/profile defect, workflow ambiguity, or unsupported input structure. Fix the reusable capability or report the precise limitation; do not use an ad hoc file-specific patch in place of reusable behavior.

## Scope

Organize the formatting behavior in two levels:

1. **Shared medical-writing formatting rules:** preserve supplied text and data; use native Word heading levels and numbering, nested ordered/unordered lists, rectangular tables, figures, chapter-based captions, cross-references, and body/table/figure lists. Apply the selected profile's implemented page, body paragraph, table text size, heading/list/caption style, and numbering parameters; validate the structure and inspect the result in Word.
2. **Document-type profiles:** choose the CTD or CSR profile for the document's language. Both currently choose 1.5 line spacing, justified body paragraphs, 6 pt after each body paragraph, and 10.5 pt table text. They also share page, heading-style, caption-style, cross-reference, and TOC settings. CTD captions take their chapter number from Heading 3 for tables and Heading 4 for figures, resetting the corresponding sequence at that level. CSR captions take their chapter number from Heading 1 for both tables and figures, resetting both sequences at level 1. These caption-level choices are profile settings, not different Word mechanisms.

The repository supplies Chinese and English profiles for both CTD and CSR. See `README.md` for the profile paths and `docs/docx-normalization.md` for existing-DOCX limits.

The Claude Code integration is an example only; this Skill and compiler are not Claude-specific.
