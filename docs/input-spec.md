# Input Specification

The v0 adapter supports ATX headings with an optional explicit chapter path, paragraphs, rectangular tables, figures, cross-references, and explicit references. IDs are stable user IDs; generated bookmark names and OOXML numeric IDs are separate namespaces. Resources must be under the task resource root and must use supported local image formats.

Unsupported merged tables, external URLs, path traversal, missing images, duplicate IDs, missing reference targets, and unconfigured caption chapter levels are rejected during validation.
