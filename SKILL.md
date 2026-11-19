---
name: arachne-loom
description: Generate Word documents from explicitly structured content with native Word headings, numbering, nested lists, captions, cross-references, and tables of contents; conservatively normalize recognized native headings and lists in existing DOCX files. Use when creating or formatting structured DOCX output, or when standardizing supported Word-native paragraph geometry. Do not use as an automatic converter or repair tool for arbitrary Word documents.
---

# Arachne Loom

Use the shared deterministic compiler to produce or conservatively normalize DOCX files. The compiler has no AI dependency; this Skill describes how an agent should prepare inputs, select configuration, verify output, and report boundaries.

## Start here

All repository-relative paths below are relative to this Skill root. Follow `README.md` → Quick start for installation and exact CLI commands. Use `examples/quickstart/config.json` as a task example and read `docs/list-formatting.md` for nested-list syntax and verification.

## Choose the path

- For structured Markdown or Canonical Model JSON, read `docs/authoring-guide.md`, preserve supplied content, then use `parse` (Markdown only), `validate`, and `compile`.
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
3. Verify in desktop Word: heading levels step inward and same-level headings align; number-to-text spacing is compact; nested numbering, restarts, and continuation lines align; no marker-only line or unintended break separates a label from its text.
4. Save, close, reopen, and repeat the visual checks. Static XML checks alone do not establish acceptance.
5. Give an independent reviewer the original requirement, manifests, and output DOCX.

If output is wrong, classify the evidence as a compiler/profile defect, workflow ambiguity, or unsupported input structure. Fix the reusable capability or report the precise limitation; do not use an ad hoc file-specific patch in place of reusable behavior.

## Scope

The repository currently supplies CTD Chinese and English profiles. The engine's supported structures can be reused for other medical and non-medical documents, including CSR and protocols, but those use cases have no dedicated shipped profile or whole-document acceptance. A reusable structure does not imply compliance with an institution template, medical-writing convention, or regulatory requirement. See `README.md` for scope and `docs/docx-normalization.md` for existing-DOCX limits.

The Claude Code integration is an example only; this Skill and compiler are not Claude-specific.
