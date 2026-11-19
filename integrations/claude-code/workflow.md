# Claude Code Workflow

1. Route the input before editing. This compiler accepts CTD-Markdown or Canonical Model JSON and generates a new DOCX; it is not an existing-DOCX normalizer. For an existing Word file, do not silently switch to a one-off OOXML patch and describe it as a supported compiler workflow. First inventory structures and limitations, then report whether conversion requires a separately reviewed process.
2. For supported structured input, read `docs/authoring-guide.md`, preserve supplied content, and encode meaning in the Canonical Model. Treat heading levels, ordered lists, and unordered lists as distinct semantic objects. Nested lists are unsupported and must be surfaced as a blocker; never flatten them or keep typed markers and claim native automatic numbering.
3. Run the shared generic CLI `parse`, `validate`, and `compile` commands. Inspect the emitted DOCX structure and acceptance report.
4. For headings, use native heading styles and native multilevel numbering. Set profile indentation only from the longest expected rendered label in the target font; use a compact hanging width that fits that label. Do not choose a large arbitrary number-to-text gap. For body lists, use native Word numbering with consistent text start and hanging alignment; never simulate it by inserting tabs after typed markers.
5. Verify in desktop Word: heading levels step inward and same-level headings align; number-to-text spacing is compact; continuation lines align with text; ordered and unordered lists have native markers; no marker-only line or unintended break separates a label from its text. Save, close, reopen, and repeat the visual checks. Static XML checks alone do not establish this acceptance.
6. Give an independent review role only the original requirement, expected/actual manifests, and generated DOCX.

If Word output is wrong, classify evidence before changing anything: (a) compiler/profile capability or defect, (b) missing/ambiguous workflow instruction that invited a guess, or (c) an input structure outside the supported contract. State which category is evidenced, and fix the reusable compiler/profile/workflow or report the capability gap. Do not repair a user's source DOCX as a substitute for fixing this Skill/workflow when the task is to improve the tool.

No Claude SDK is imported by the compiler.
