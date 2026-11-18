# 🕸️ arachne-loom

> Weave loose semantic threads into a Word document whose cross-references, captions, and numbering are **native Word objects** — not text that merely looks right.

`arachne-loom` is a deterministic compiler. It takes an explicit **Canonical Model** — headings, tables, figures, and the *relationships* between them — and weaves a `.docx` in which every `SEQ`/`REF`/`TOC` field, bookmark, and multilevel number is a real object Microsoft Word can renumber, update, and follow. It has **no AI dependency** and runs anywhere Python runs.

<sub>Named after Arachne, the mortal weaver of Greek myth whose work outshone a goddess's, and her **loom** — the machine that turns scattered thread into exact structure. Sibling to `ariadne-thread`.</sub>

---

## Quick reference

<sub>Dense summary for agents and readers in a hurry. Prose and diagrams follow below.</sub>

**What it is.** A deterministic, AI-free CLI/library that compiles a semantic model into a `.docx` with native `SEQ`/`REF`/`TOC` fields, bookmarks, and multilevel heading numbering.

**I/O contract.**
- **Input:** a Canonical Model (JSON), *or* CTD-Markdown that `parse` converts into one — plus a CTD profile and a task config. The Canonical Model is the single semantic contract; the compiler never re-guesses meaning from Markdown.
- **Output:** `document.docx` + `expected-manifest.json` + `actual-manifest.json` + `acceptance-report.json` + `unresolved-issues.json`.

**Commands.**
```sh
loom parse    <input.md> -o <model.json>
loom validate <model.json> <profile.json> <task.json>
loom compile  <model.json> <profile.json> <task.json> --out-dir <dir>
loom inspect  <document.docx> -o <actual-manifest.json>
```

**Minimal CTD-Markdown input** (headings carry explicit chapter numbers; every table/figure has a stable `id`; cross-references use `[@id]`, never a typed number):
````md
---
title: "临床有效性"
language: zh-CN
---

### 2.7.3 临床有效性

:::table id=tbl-study title="已完成的评价有效性的研究"
| 研究 | 设计 | 人群 |
| --- | --- | --- |
| STUDY-001 | 随机、双盲 | 成人受试者 |
:::

研究信息见 [@tbl-study]。
````

**Hard rules the compiler enforces (invalid input is rejected, never guessed):**
- Duplicate `id` → rejected.
- Cross-reference to a non-existent `id` → rejected (and listed).
- Missing/unsupported image → rejected.
- Heading level jump the config cannot explain → rejected.
- Unsupported structure (merged cells, literature fields, …) → rejected, not silently emitted.

**Invariants for integrators.**
- *Model correct → document correct*: the compiler is pinned by a test suite; same input yields same output.
- The independent reviewer sees requirement + model + both manifests + document, **never** the compiler's code or logs.
- Static XML/OOXML checks **do not** replace desktop-Word behavior verification.

**Authoritative sources.** Semantic contract: [`compiler/arachne_loom/model.schema.json`](compiler/arachne_loom/model.schema.json). Markdown syntax: [`docs/input-spec.md`](docs/input-spec.md). Word mapping: [`docs/word-primitives.md`](docs/word-primitives.md).

---

## The problem it solves

When a document is authored as prose, `"Table 2.7.3-1"` is just characters. It has **no link** to the table above it:

```
insert a new table    →  the number does not reflow
click the reference   →  nothing happens
update fields         →  "Error! Reference source not found"
```

The intent — *which table this sentence points to* — was lost the moment the text was typed. Repairing it afterward means **guessing** the lost relationships. `arachne-loom` never lets the intent get lost: it is recorded up front, then compiled into real Word fields.

```
❌  prose-first      "Table 2.7.3-1"  =  frozen characters, no link
✅  arachne-loom     [@tbl-study]  →  REF field → bookmark → SEQ (auto-numbered)
```

---

## How it works — three independent gates

Loose threads become exact cloth by passing through three stations. **No station grades its own work** — that separation is the core of the design.

```
        loose threads              the loom                 woven cloth
   ┌───────────────────┐   ┌───────────────────────┐   ┌──────────────────┐
   │  ① AUTHOR         │   │  ② COMPILE            │   │  ③ REVIEW        │
   │  make intent      │──▶│  deterministic weave  │──▶│  independent      │
   │  explicit         │   │                       │   │  blind check      │
   ├───────────────────┤   ├───────────────────────┤   ├──────────────────┤
   │ tag every table   │   │ reject invalid input  │   │ compare against   │
   │ with an id;       │   │ (dup id? dangling     │   │ requirement +     │
   │ reference it by   │   │ ref? missing image?)  │   │ model + manifests │
   │ id, never by      │   │ then emit native      │   │ + document.       │
   │ typed number      │   │ SEQ/REF/TOC/bookmark  │   │ never reads the   │
   │                   │   │ + heading numbering   │   │ compiler internals│
   └───────────────────┘   └───────────────────────┘   └──────────────────┘
      CTD-Markdown            arachne-loom (this repo)      reviewer / CI
       or JSON                no AI dependency              + desktop Word
            │                        │                            │
            ▼                        ▼                            ▼
     Canonical Model  ─────▶  document.docx  ─────▶  expected vs actual
     (one true input)         + manifests           manifest diff
```

- **① Author** turns writing into structure. Any human or any AI can produce the input; the tool does not care which.
- **② Compile** is this repository. It validates, refuses anything it cannot map, and weaves the Word objects. Given the same input it produces the same output.
- **③ Review** is deliberately blind: it sees the original requirement, the model, the two manifests, and the finished document — **never** the compiler's code or logs. Structural legality is proven by the compiler; *semantic* correctness ("does this point to the right table?") is proven here.

### Why the loom is the crown jewel

The compiler is a **plain Python program with no AI inside**, so it can be pinned by a test suite: feed it a model, assert the exact Word structure that comes out. That is the proof of *"model correct → document correct."* Word behavior a machine cannot judge (clickable jumps, field reflow) is recorded separately against a named desktop Word version — **XML checks never claim to replace it.**

---

## One model, many entry points

The loom accepts exactly one semantic contract — the **Canonical Model**. CTD-Markdown and JSON are just *threads* fed into it; the compiler never re-guesses meaning from Markdown at weave time.

```
   CTD-Markdown ┐
                ├──▶  parse ──▶  Canonical Model (schema-checked)  ──▶  compile ──▶  .docx
   JSON model  ─┘                       ▲
                                one true input contract
```

This is what makes it reusable: the engine knows *Word formatting*, not medicine. Swap the **profile** (fonts, caption numbering, page size, failure catalog) and the same engine serves any structured Word document — the CTD profile is simply the first one shipped.

---

## Quick start (60 seconds)

```sh
python -m pip install -e compiler          # installs the `loom` command; pulls python-docx + lxml

loom parse    examples/quickstart/sample.md -o /tmp/model.json
loom validate /tmp/model.json profiles/ctd/zh-CN/config.json examples/quickstart/config.json
loom compile  /tmp/model.json profiles/ctd/zh-CN/config.json examples/quickstart/config.json --out-dir /tmp/loom-build
```

Open `/tmp/loom-build/document.docx` in desktop Word:

- click the `表 2.7.3-1` reference → it **jumps** to the table caption
- insert a new table before it and update fields → every number **reflows**

The output directory also holds `expected-manifest.json`, `actual-manifest.json`, an `acceptance-report.json`, and `unresolved-issues.json`.

<sub>`loom` and `arachne-loom` are the same command. Word itself is only needed for the desktop acceptance steps, not for compilation.</sub>

---

## What v0 supports

| Woven natively | Deferred |
|---|---|
| Headings 1–9 + multilevel numbering | Merged table cells |
| Rectangular tables + captions | Literature-management fields |
| Figures + captions | Comments / tracked revisions |
| Body cross-references (`REF … \h`) | Section-specific headers |
| Body TOC, table list, figure list | Automated desktop Word testing |
| Input validation + independent DOCX inspection | |

The v0 contract is provisional and **intentionally rejects** structures it does not yet support, rather than emitting something Word cannot manage.

---

## Repository layout

```
arachne-loom/
├── compiler/            the loom — deterministic CLI/library (no AI dependency)
│   └── arachne_loom/    parser · model · generator · fields · validator · inspector
├── profiles/ctd/        CTD formatting profile (config, contract, failure catalog)
├── docs/                first-principles, three-gates, Word primitives, acceptance log
├── examples/quickstart/ runnable sample + tested artifacts + negative fixtures
└── integrations/        thin, workbench-neutral wrappers (generic-cli, claude-code)
```

## Word acceptance

The compiler and its `tests/` run with **no Word and no AI**. Native field behavior — clickable jumps, field-update reflow, caption insertion, save-and-reopen stability — must be verified in desktop Word. Recorded results and the tested Word version live in `docs/word-acceptance-log.md`.

## License

MIT — see [LICENSE](LICENSE).

## Hierarchical heading indentation (v0.0.3)

To indent deeper heading levels, add this optional object to your profile:

```json
"headingStyle": {
  "italic": false,
  "indentation": {"basePt": 0, "incrementPt": 18, "hangingPt": 72}
}
```

The level-1 number starts at 0 pt; levels 2 and 3 start at 18 and 36 pt.
Text and continuation lines start 72 pt after each number's anchor. The generous
hanging area accommodates longer chapter numbers; choose it for your document's
font and deepest numbering. All three fields are required non-negative numbers
in points (72 pt = 1 inch). Omit `indentation` to retain the previous layout.
The standard CTD profiles are unchanged.

Try the complete example:

```sh
loom parse examples/quickstart/indented-headings.md -o /tmp/indented-model.json
loom compile /tmp/indented-model.json examples/quickstart/indented-profile.json examples/quickstart/config.json --out-dir /tmp/loom-indented
```

See [the heading indentation guide](docs/heading-indentation.md) for geometry,
Word verification, and scope.

## Uniform ordered and unordered lists (pending acceptance)

Native single-level Word lists use consistent marker positions, text tab stops,
and hanging indents throughout the document. Set `listStyle.ordered` and
`listStyle.unordered` with `markerPt`/`textPt` to customize them.
See [list formatting](docs/list-formatting.md) for input syntax and examples.
This change is under development; the release remains a draft pending desktop
Word acceptance of both heading and list formatting.
