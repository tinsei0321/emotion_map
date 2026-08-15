---
name: js-regex-word-chinese-trap
description: "正则 \\w 不匹配中文——替换 {区} 等中文占位符/匹配中文用 [^}]+ 或 \\p{L}/u，绝不用 \\w/[a-z]"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 67931aba-e0c4-40d7-83a4-4dab896b2e03
  modified: 2026-07-23T15:37:53.010Z
---

JS 正则 `\w` = `[A-Za-z0-9_]`，**不含中文**。用 `\w+` 或 `[a-z]+` 去匹配含中文的 key/文本会**静默失败**（不报错、语法绿，占位符原样保留）。

**坑例**：[test-cases.js](frontend/js/test-cases.js) `_fill(tmpl,v)` 曾用 `/\{(\w+)\}/g` 替换 `{区}`/`{要素}`/`{用地}` —— `\w` 不匹配中文 → 全部 INTENT/TOOL（200 例）prompt 的 `{区}` 未替换，EMC 收到占位符乱码提问。语法检查全绿、用例计数（100/100）正常，只有**运行时输出扫描**或肉眼能发现。

**正确写法**：
- 匹配中文占位符 / 任意 key：`/\{([^}]+)\}/g`（排除法，最稳）
- 匹配中文通用：`/\p{L}/gu`（Unicode 属性，须 /u flag）或显式 `/[一-龥]/`
- 中文 literal（如 `/缺数据|未产出|需上传/`）直接写字面量，**能匹配**（字面量不受 \w 限制）

**Why**：\w 是 ASCII 词字符，JS 默认正则不开 Unicode 模式。

**How to apply**：写正则解析「可能含中文」的内容（占位符替换、中文字段名、URL 含中文段）前先问「会含中文吗」——含则用 `[^x]+` 或 `\p{L}/u`，**绝不用 \w / [a-z]**。审查正则时，重点查每个 ASCII 字符类是否被用在了中文场景。

**验证习惯**：生成器类代码改完，跑 `node --input-type=module -e "import('./x.js').then(m=>…)"` 扫输出里是否残留 `{`/`}`（占位符未替换的指纹）。

同类：[[js-chinese-identifier-trap]]（中文变量名版）。
