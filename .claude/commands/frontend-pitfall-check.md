---
description: 前端改动后扫三坑 — JS 中文标识符 / MapLibre query 数组序列化 / node --check ESM 假绿
argument-hint: "(可选) 指定文件或目录；默认扫本次 git 改动的 frontend/**/*.js"
---

前端三个反复踩的坑（每坑都有独立 memory，历史反复发生）的一键扫描。沉淀 `js-chinese-identifier-trap` + `maplibre-query-array-stringify` + `node-check-esm-unreliable`。

## 三坑 + 扫法

1. **JS 中文标识符被吞**（`js-chinese-identifier-trap`）：`let口径`（中英无空格紧贴）被 JS 引擎当单标识符，`node --check` 查不出、运行时 ReferenceError。
   - 扫：grep `[a-zA-Z_][一-龥]|[一-龥][a-zA-Z_]`（字母紧贴中文）→ 报警，建议加空格或改英文标识符（变量名一律英文）。
2. **MapLibre queryRenderedFeatures 数组序列化**（`maplibre-query-array-stringify`）：`queryRenderedFeatures` 返回的 `feature.properties` 里数组/对象会被序列化成字符串，直接读 `n.tags` 得到 `"[object]"` 而非数组。
   - 扫：grep `queryRenderedFeatures` 附近读 property 的代码，若无 `Array.isArray(x) ? x : JSON.parse(x)` 容错 → 报警，建议加 isArray 校验或从 geometry 现算。
3. **node --check ESM 假绿**（`node-check-esm-unreliable`）：`node --check x.js` 默认 CommonJS，不报 ESM 语法错（括号/import 等），假绿通过。
   - 扫：若本次验证用了 `node --check *.js` → 报警，建议改 `node --input-type=module --check < x.js` 或 `.mjs` 副本。

## 步骤

1. 确定扫描范围：`$ARGUMENTS` 指定文件/目录；否则 `git diff --name-only HEAD` 过滤 `frontend/**/*.js`（含 .mjs）。
2. 逐坑 grep 扫。
3. 报警 + 修法建议（给推荐，不穷举）。

## 输出

- `[PITFALL] js: frontend/js/x.js:42 — 'let口径' 中文标识符 → 建议 'let 口径' 或英文`
- 末尾 `PITFALLS: N 处（坑1=a / 坑2=b / 坑3=c）`。全绿 `PITFALLS: CLEAN`。

遵守 CLAUDE.md：结论先行、ASCII、中文、给推荐。手动触发，零被动开销。
