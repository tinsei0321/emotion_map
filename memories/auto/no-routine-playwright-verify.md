---
name: no-routine-playwright-verify
description: "Don't Playwright-verify after every UI change — implement then let the user verify visually"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1da6d0cb-5116-4e1d-a6b1-fe291f78f57f
---

Do **not** run a Playwright pass-through after every frontend edit — it's slow and the user finds it low-value. They verify visually by opening the page themselves.

**Why:** User: "你每次修改完需要用 Playwright 验证一遍吗？这样效率很低。" And again after several rounds: "小的修改不需要 playwright 验证…为什么我一直都要用？" — even when I framed Playwright as "self-confirmation," that's exactly the misuse to avoid. The vision/analyze_image tool is unreliable for this UI anyway, so heavy automated verification gives diminishing returns.

**How to apply:** For routine CSS/HTML/JS UI edits → make the change, ensure the page loads, hand off with a one-line "验证点" list. **Do NOT run Playwright to confirm your own work on visible changes** — that's the user's job. Reserve Playwright for (a) explicitly requested checks, or (b) changes with **invisible-to-the-eye** risk: control-flow branches (replace-vs-hide logic), data-flow (coord transforms, field derivation), async races, layer-visibility sync, deck.gl-style heavy integration. 

Concrete boundary:
- ✅ Hand off directly (no Playwright): 配色/文案/删减项/布局间距/tooltip 样式/加去一个字段/纯 CSS
- 🔬 Playwright only: 控制流分支、坐标转换、字段派生、异步竞态、图层可见性同步 Map 同步、deck.gl 等重集成、用户明确要求

Default workflow: implement → user verifies (with serve.py no-cache, F5 is always fresh).
