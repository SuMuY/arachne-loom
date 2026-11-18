# 🕸️ arachne-loom

> Weave loose semantic threads into a Word document whose cross-references, captions, and numbering are **native Word objects** — not text that merely looks right.

`arachne-loom` is a deterministic compiler. It takes an explicit **Canonical Model** — headings, tables, figures, and the *relationships* between them — and weaves a `.docx` in which every `SEQ`/`REF`/`TOC` field, bookmark, and multilevel number is a real object Microsoft Word can renumber, update, and follow. It has **no AI dependency** and runs anywhere Python runs.

<sub>Named after Arachne, the mortal weaver of Greek myth whose work outshone a goddess's, and her **loom** — the machine that turns scattered thread into exact structure. Sibling to `ariadne-thread`.</sub>

---

## 适用范围：通用排版能力与医学文档配置

**当前定位：以 CTD 为首个配置场景的结构化 Word 生成工具。底层机制可复用于非医学文档，也可用于 CSR、临床试验方案等医学文档中的受支持结构。仓库目前提供 CTD 中英文配置，尚未交付单独的通用、CSR 或方案配置及相应全文验收。**

### 哪些是通用能力？

| 能力 | 可复用范围与现有支持 |
| --- | --- |
| 标题层级、编号、缩进 | 支持 1–9 级标题及逐级缩进；编号目前采用 `1 / 1.1 / 1.1.1` |
| 有序、无序列表 | 单层原生列表；全文统一标记位置、正文起点和续行缩进；支持独立起始编号 |
| 图表题注与交叉引用 | 原生 `STYLEREF`、`SEQ`、`REF` 域及书签；对象移动后由 Word 管理编号与引用 |
| 目录 | 正文目录、图目录、表目录；目录域需在 Word 中更新 |
| 页面与正文基础设置 | A4/Letter、页边距、正文字体与字号；标题/列表缩进及题注的部分样式可配置 |
| 结构检查 | 输入对象 ID、引用目标、资源路径及生成 DOCX 的域/书签检查 |

这些机制不检查医学内容或 CTD 章节名称。普通技术报告和业务报告也可使用，但必须采用当前支持的输入结构和编号方式。

### 哪些适用于医学写作？哪些属于 CTD 默认配置？

**可以复用到医学写作的工程规则**包括：正文、图表数据及引用关系由明确的输入模型提供；排版不擅自改写科学内容；使用真实标题层级与原生编号；图表题注和交叉引用保持关联；先做结构检查，再用桌面 Word 验收。这些规则也适用于其他严肃文档，并非医学专属。

**CTD profile 是本仓库的排版预设，不是所有医学文件的统一规范。** 它包含中英文样式映射、默认字体/页面参数、题注外观，以及按章节组织图表编号的规则。当前默认表题依赖三级标题，图题依赖四级标题；依赖层级可调整。是否适合具体申办方或项目，须对照其模板确认。

| 文档场景 | 当前适用方式 |
| --- | --- |
| CTD 文档 | 使用已提供的 CTD 配置；仍按目标项目模板核对参数及受支持结构 |
| CSR、临床试验方案等 | 可复用标题、列表、图表及引用机制；须调整配置并以目标文档验收，目前无专用成品配置 |
| 非医学报告 | 可使用相同机制生成受支持结构；独立通用配置尚未提供 |

例如，CSR 若采用 `1 / 1.1` 标题和按章图表编号，可以复用相应机制；若要求图表全篇连续编号、横向大表、合并表头、复杂页眉页脚、修订或文献管理域，则需要先补齐对应能力。工具不检查 CSR 内容完整性或监管要求。

### “增加通用配置、让规则真正可配置”是什么意思？

目标是由同一套引擎读取不同的排版方案：通用报告、医学文档公共规则，以及 CTD/CSR/方案的具体模板。以下为后续设计方向，**不是当前已交付功能**：

- **独立通用配置**：提供不沿用 CTD 章级假设的基础预设，CTD 保留为独立配置；用户选择目标配置即可使用。
- **编号模式可选**：标题支持其他编号形式或无编号；图表支持按章重置或全文连续编号，而非仅改标签文字。
- **配置确实生效**：目前正文 `lineSpacing`、`alignment`、`paragraphAfterPt` 虽写在 CTD 配置里，生成器未主动应用；表格当前固定使用 `Table Grid`。后续需实现对应行为并验证，不能仅增加 JSON 字段。
- **格式验证可复用**：用不同场景样例检查同一配置是否始终生效，并做 CTD 回归，保留已验收能力。

### 能否拿任意已有 Word 直接统一格式？

**当前没有完整的 DOCX 导入或原位格式统一入口。** `parse` 读取约定的 Markdown，`compile` 读取 Canonical Model JSON；`inspect` 能检查 DOCX 的部分结构，但不输出可供编译器重建全文的模型。基础模板 `baseTemplate` 也不是源文档导入器。

将已有 Word 的内容和关系先整理成受支持模型，再生成新 Word，是可探索的转换流程；当前尚未提供经过验证的自动转换器。对于现有原生标题/列表，可探索保留结构直接调整样式；对于手打编号、普通字符圆点或仅靠字号模拟标题的文件，则需识别语义并处理歧义。两种路径都需要专门验证。

验证应使用代表性 `.docx` 和目标模板/格式要求，先盘点标题、列表、表格、图片、题注、引用、分节及修订，再比较处理前后正文、表格数据、对象关系和 Word 实际行为。真实项目文件留在仓库外；公开测试只使用合成或经确认脱敏的样例。具体文件能否可靠处理，要以这个测试结果判断。

---

## Quick reference

<sub>Dense summary for agents and readers in a hurry. Prose and diagrams follow below.</sub>

**What it is.** A deterministic, AI-free CLI/library that compiles a semantic model into a `.docx` with native `SEQ`/`REF`/`TOC` fields, bookmarks, and multilevel heading numbering.

**I/O contract.**
- **Input:** a Canonical Model (JSON), *or* CTD-Markdown that `parse` converts into one — plus a formatting profile and a task config (CTD presets are currently supplied). The Canonical Model is the single semantic contract; the compiler never re-guesses meaning from Markdown.
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

The model and Word field mechanics are reusable across domains. A **profile** selects the implemented presentation policies; the supplied profiles target CTD. Other document types can reuse supported structures, but requirements outside the current numbering and layout capabilities need implementation and separate acceptance. See the scope section above for concrete limits.

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
| Single-level ordered/unordered lists | Nested lists |
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

## Hierarchical heading indentation (v0.0.4)

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

## Uniform ordered and unordered lists (v0.0.4)

Native single-level Word lists use consistent marker positions, text tab stops,
and hanging indents throughout the document. Set `listStyle.ordered` and
`listStyle.unordered` with `markerPt`/`textPt` to customize them.
See [list formatting](docs/list-formatting.md) for input syntax and examples.
Desktop Word visual and save/reopen checks and user acceptance were completed
on 2026-11-18. See the acceptance records in the heading indentation guide.
