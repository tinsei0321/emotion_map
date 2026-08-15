---
name: js-chinese-identifier-trap
description: JS 中 let/const 后紧跟中文无空格（如 let口径）会被词法器吞成单标识符，语法合法运行时崩
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 450f231f-e51a-4fd7-8f99-06d6aadcbffe
---

写 `let口径;`（let 后无空格直接写中文变量名）→ JS 词法器把 `let口径` 当成**一个标识符**（let 是合法标识符开头字符，紧邻的中文也是合法标识符字符，无分隔→合并），不是 `let` 声明 `口径`。结果 `口径 = ...` 引用的是另一个未声明变量 → 运行时 `ReferenceError: let口径 is not defined`。

**致命点**：`node --check` **查不出来**——因为 `let口径 = x` 语法上是「赋值给标识符 let口径」的 expression statement，语法合法。只有运行到该行才崩。

**Why**：Task 2.7 cell-popup 的 `_cellMeta` 里写了 `let口径;`，showCellPopup 调它时抛错中断，导致 cell-popup 只填了 badge/size、loc/meta/kv 全空、cell:selected 不 dispatch、Overview 不切——首轮实测差点交付带病代码。

**How to apply**：①**变量名一律用英文**（mood/level/dim 等），中文只进字符串值（'网格'）和对象 key；②若非要用中文标识符，`let` 与变量名之间**必加空格**；③`node --check` 只查语法不查运行时，**前端改动必上 Playwright 真数据实测**才能抓到这类 bug。关联 [[maplibre-query-array-stringify]]。
