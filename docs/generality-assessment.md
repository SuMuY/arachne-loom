# 通用性核对（2026-11-18）

用户询问当前工具是否能脱离 CTD。结论：核心文档结构与 Word 机制可复用，现有交付配置以 CTD 为主；可生成非医学结构化文档，尚不是开箱即用的通用 Word 格式工具。

已核对源码：model.schema.json 的 heading/paragraph/list/table/figure/crossReference 无医学内容字段；validator 无 CTD 章节名称或医学内容强制检查；CLI 接收显式 profile，无 profiles/ctd 路径硬编码。

残留约束：只交付 CTD profile 和中英模板；validator 即使文档无图表也要求两类 caption 完整配置；图表生成固定使用 STYLEREF 章节前缀加 SEQ 序号，未提供无章节前缀的全篇连续编号；标准 profile 的表依赖三级标题、图依赖四级标题，但章级可配置，不是固定在内核。标题编号固定阿拉伯数字点分层级。部分 profile 字段尚未落实：正文 lineSpacing/alignment/paragraphAfterPt 未在 _apply_profile 中应用，table style 固定 Table Grid。输入是约定 Markdown/JSON 生成新 DOCX，不是任意现有 Word 原位统一格式。

建议：保留现有内核及 CTD 配置，后续增加独立通用 profile，按需补全编号模式和格式配置执行；用非医学文档增加端到端验收，CTD 保持兼容。此次仅核对与讨论，未授权实施通用化重构。

## README 范围澄清与 Word 输入探测（2026-11-18）

用户要求明确通用能力、医学写作公共规则、CTD 预设及 CSR 等场景适用条件，并询问通用化含义及已有 Word 文件的验证方式。已在 README 增加中文说明并修正“换 profile 即可服务任意结构化文档”的过度表述。本次仅改说明，没有新增通用/CSR 配置或导入器。

证据：CLI 只有 parse/validate/compile/inspect；用仓库合成 build/document.docx 调用 parse_markdown 得到 UnicodeDecodeError，确认当前入口读取文本，不能导入 DOCX。inspect 成功输出 fields/bookmarks/tables/images 等清单，不含 blocks，不能据此重建全文。现有 integrations 仅说明 AI/工作台先生成 Markdown/JSON，未提供 DOCX 自动转换路径。上述探测用于确认当前入口，不证明后续实现 DOCX 统一格式不可行。

后续以用户代表性 .docx 和目标格式核验：原生样式调整或重建模型两条路径，比较内容/对象关系保留率及 Word 实际结果。真实材料不进入公开仓库。
