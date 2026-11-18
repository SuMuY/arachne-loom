# Heading indentation

`headingStyle.indentation` is an optional profile object, applied to all body
heading levels (1–9), in both locale profiles. It uses native Word styles and
multilevel numbering, rather than typed spaces or tabs in heading text.

| Field | Meaning (points) |
| --- | --- |
| `basePt` | Level-1 number's left position, relative to the page's text margin |
| `incrementPt` | Additional inset per semantic heading level |
| `hangingPt` | Distance from number anchor to text and continuation-line start |

For semantic level L, the number anchor is `basePt + (L - 1) * incrementPt`;
the text starts at that anchor plus `hangingPt`. Values are rounded to Word's
1/20-point units. All three fields are required, finite, and non-negative.
Unknown keys are rejected to catch typos. Zero increments permit aligned levels;
a zero hanging area is accepted, but provides no reserved width for the number.

The same indentation is written into heading styles and numbering levels, with
an explicit number suffix tab and matching tab stop. Same-level headings reuse
the same style and numbering level throughout the document. Existing profiles
without this object retain the previous behavior. TOC entries, TOC titles, body
paragraphs, and captions have their own formatting and do not receive this rule.
This feature applies during generation; it does not reformat an existing DOCX.

## Runnable example

Use `examples/quickstart/indented-profile.json` with
`examples/quickstart/indented-headings.md`, following the README commands.
The example includes repeated levels and a long heading for wrap verification.
Choose a hanging area wide enough for the longest number in the actual font;
Word advances past the tab if a number outgrows that area.

## Verification

Automated regression checks compile real DOCX files for zh-CN/en-US and examine
all nine style/numbering geometries, tab positions, same-level style reuse,
invalid settings, and omitted-setting compatibility. The full existing suite
also checks captions, references, lists, and document inspection.

2026-11-18 automated verification: 22 tests passed; the new tests first failed
on missing geometry and missing config validation (15 failures, one legacy
compatibility pass), then passed after implementation. The CLI example compiled
successfully.

Desktop Word verification was attempted on 2026-11-18. Its Open dialog selected
the generated DOCX but did not open it after Open, Return, or double-click;
the final cancel operation returned computer-use timeoutReached (-10005).
The preview thumbnail is insufficient to judge wrapping. Full-size Word visual
acceptance remains pending; the release's geometry verification is automated
OOXML validation. Open the README example to check stepped number positions,
same-level alignment, and long-heading continuation lines in desktop Word.

## 2026-11-18 用户验收失败与修订

用户截图及随后直接连接 Word 的截图均显示：各级标题平齐，编号从 9 连续递增，视觉验收失败。旧自动测试只读取编号属性，未检查编号部件的完整元素顺序。

诊断发现：新增 abstractNum 被 append 到现有 num 之后，违反 CT_Numbering 要求的 abstractNum 先于 num 的顺序。补充失败回归测试后，将标题及列表两处写入改为 insert_element_before；37 项测试通过。

修订文件：下载目录下 arachne-loom-验收修订1.docx。尝试经 Word 打开对话框和访达打开，电脑控制工具返回 noWindowsAvailable、cgWindowNotFound 及 ScreenCaptureKit -3811 音频/视频捕捉失败。因此修订版尚未完成 Word 视觉验证，不能认定本修订已消除截图问题。发布继续禁止。
