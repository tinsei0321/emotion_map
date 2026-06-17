# Trace 错误摘要 (Error Digest)

> 闭环补强 Wave4：SessionEnd 自动从 `.trace/trace.log` 摘取**新增** ERR/WARN 沉淀于此。
> 让 debug 史不再蒸发——可检索、可回灌。游标 `.claude/.trace-digest-cursor` 防重复（gitignored）。
>
> 说明：首个块曾含 pytest 负路径测试产生的 ERR 噪声，已清为干净种子头；
> 后续仅沉淀真实会话中产生的 ERR/WARN。

<!-- SessionEnd hook 会在下方按日期追加 ## YYYY-MM-DD HH:MM（N 条新增 ERR/WARN）块 -->
