# Heading indentation

`headingStyle.indentation` is an optional profile object, applied to all body
heading levels (1–9), in both locale profiles. It uses native Word styles and
multilevel numbering, rather than typed spaces or tabs in heading text.

| Field | Meaning (points) |
| --- | --- |
| `basePt` | Level-1 number's left position, relative to the page's text margin |
| `incrementPt` | Additional inset per semantic heading level |
| `hangingPt` | Reserved number width from the level anchor to text and continuation-line start. Accepts one width for all levels or nine widths ordered from levels 1 to 9. |

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
Choose the smallest hanging area that fits the widest rendered number at that
level in the target font, including the longest expected multilevel label (for
example `10.12.3`). Do not use a large fixed width such as 72 pt without a
measured need: the suffix tab places the heading text at `anchor + hangingPt`,
so an oversized value creates a visibly large number-to-text gap. Confirm the
result and wrapped-line alignment in desktop Word.

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

## 2026-11-18 修订版桌面 Word 实际核验

继续恢复电脑控制后成功打开 `arachne-loom-验收修订1.docx`。此前点击打开后的连续超时存在模态提示因素：发送 Escape 后读取到“该文档包含的域可能引用了其他文件，是否更新”提示，选择“否”后成功显示文档。不能再将此类超时直接视为不可恢复。

直接截图观察（非 AX 文本推断）：
- 第一页 1、1.1、1.1.1 至九级编号逐级右移；二级 1.2 回到同级位置；四级及九级长标题续行与正文对齐。
- 两组无序列表圆点与正文分离，正文起点一致，长项目续行与正文对齐。
- 有序列表 9、10、11 的正文起点一致，9/10 长项目续行对齐；新列表从 1、2 重启；指定起点列表显示 9、10。
- Cmd+S 保存、Cmd+W 关闭后，重新从 Word 打开同一 URL，处理同样域提示；重新截图确认标题阶梯、无序列表续行和 9/10 有序列表对齐保持稳定。

本次通过上述样例的视觉及保存重开检查。截图可见于本次聊天工具输出；未向仓库写入混有其他窗口信息的电脑截图。Word AX 内容将编号转写成普通 Markdown 序列，不能用于替代画面中的编号核验。版本继续保持草稿，待用户复核。

## 用户验收与发布授权（2026-11-18）

用户已明确验收通过并要求更新发布。以 v0.0.4 发布完整修订，保留 v0.0.3 历史标签，不覆盖旧标签。
