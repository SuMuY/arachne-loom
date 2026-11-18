# v0.0.3 标题层级缩进

需求：全文同级标题统一对齐，下一级比上一级向内缩进；保留原生编号。

方案：profile.headingStyle.indentation 为可选对象，包含必填 basePt、incrementPt、hangingPt（有限非负数，单位磅）。第 L 级编号位置为 basePt + (L-1)*incrementPt；文字及换行位置再加 hangingPt。同步标题样式、多级编号缩进与编号制表位。省略整个对象时保留旧版行为，不改变标准 CTD profile。

验证：先复现缺少缩进与无效配置未拒绝，再验证中英 profile 的 1–9 级、重复同级标题、零缩进、旧配置兼容；运行全套测试与 CLI 示例、泄漏扫描。生成合成示例供桌面 Word 核验长标题换行。发布 v0.0.3，记录实际验证范围。

DeerFlow：不适用；这是独立文档编译器仓库。
