---
name: frontend-default-light-theme
description: "The MapLibre frontend (frontend/) is LIGHT theme (geojson.io), never dark chrome"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1da6d0cb-5116-4e1d-a6b1-fe291f78f57f
---

The MapLibre frontend (`frontend/`) is **LIGHT theme overall (geojson.io)**, BUT the top title band is a **dark navy accent `#0c1c2e`** (white text). NOT all-white, NOT all-black.

- **Title bar** (top 40px band, "宜昌市情绪地图 v1.0"): `#0c1c2e` navy, white bold text.
- **Toolbar** (below title, with S/Pt/L/Import/Export/M): light `#ffffff`, dark text `#404040`.
- **Panels / map / tables / sections**: light (`#ffffff`/`#f5f5f5`, text `#171717`, borders `#e5e5e5`, hover `#f5f5f5`).
- **Collapse handles**: slender dark vertical pills `#1a1a1a` (12×44px), rounded on the map-facing side, flat on the panel side; hover → brand `#007afc`.
- **Tool buttons**: dark text on transparent, ~4px radius; active = `#007afc` fill + white text.
- **EXCEPTION — EMC module (`#emc-panel`, AI Copilot in left-rail lower half) is DELIBERATELY DARK** (Claude Code style, 5.50): base `#1f1f1f` / raised `#262626` / text `#ECECEC` / **Claude orange accent `#D97757`** (send, active Pro/Flash, thinking, tool accents). Done by scoping `--geojson-color-*` overrides on `#emc-panel` in `ai_qa.css`. User chose this over the earlier purple+white (5.49). Do NOT "fix" EMC back to light.

**Why:** user explicitly: "默认浅色主题（记住）" but also "标题的底色不是白色也不是黑色，是我截图里的颜色（深蓝）" → title band navy `#0c1c2e` (confirmed via screenshot, matches Tianditu navy). The analyze_image tool is unreliable for chrome colors (hallucinated `#1a1e24`/`#1a1a1a`); trust the user + `docs/vision-inbox/latest.md`.

**How to apply:** keep panels/toolbar/map light; title band navy; **EMC (`#emc-panel`) dark**. Active/selected = brand `#007afc` (except inside EMC where accent = Claude orange `#D97757`). See [[no-routine-playwright-verify]].
