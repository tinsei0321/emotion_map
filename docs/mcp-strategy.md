# MCP 策略与路由手册 (MCP Strategy)

> 项目 vibe coding 的「能力外挂层」：哪些 MCP 干什么活、同类优先选谁。
> 配套决策：[ADR-013 智谱 MCP 优先](decisions.md#adr-013) ｜ 上次实测：2026-06-17

---

## 1. 一句话原则

**同类功能优先选智谱（Z.AI / BigModel）；智谱连不上再退到备选。**

理由见 ADR-013：用户已持有 GLM Coding Plan（API Key 已配），搜索/阅读/视觉/读仓四类能力集中在智谱一家，认证、计费、延迟统一，且主循环模型本就是 GLM 系。

**回退阶梯（高 → 低）**：

```
智谱 MCP（主）  →  其他厂商 MCP（火山引擎 / 4_5v 等，备选）  →  Skill 内置能力（兜底）
```

> 兜底示例：联网搜索若 `web-search-prime` 不通，再用 `byted-deepsearch` / `WebSearch` skill。

---

## 2. MCP 清单（2026-06-17 实测）

| MCP 服务 | 提供方 | 类型 | 配置位置 | 状态 | 用途 |
|----------|--------|------|----------|------|------|
| `zai-mcp-server` | 智谱 GLM-4.6V | stdio | 用户 `~/.claude.json` | ✅ | **视觉理解主**：识图/图表/截图/技术图/UI 对比 |
| `web-search-prime` | 智谱 | http | 用户 `~/.claude.json` | ✅ | **联网搜索主** |
| `web-reader` | 智谱 | http | 用户 `~/.claude.json` | ✅ | **读网页/文档主** |
| `zread` | 智谱 | http | 用户 `~/.claude.json` | ✅ | **读开源仓库主**（结构/文件/问答） |
| `vision-bridge` | 火山引擎 Ark | stdio(本地py) | 项目 `.mcp.json` | ✅ | 视觉理解备选（本地识图） |
| `playwright` | Microsoft | stdio | 项目 `.mcp.json` | ✅ | 浏览器自动化 / 前端 E2E |
| `github` | GitHub | stdio | 项目 `.mcp.json` | ❌ 认证失败 | GitHub Issues/PRs（PAT 失效，见 §5） |
| `4_5v_mcp` | 待查 | ? | 不在两份配置（插件来源） | ✅ | 仅远程 URL 识图，来源待核实 |
| `web_reader`（下划线） | 智谱 | http | 重复 | ✅ | **与 `web-reader` 同端点，建议移除**（见 §5） |

> 配置两处：项目级 `.mcp.json`（随 Git 走、团队共享）、用户级 `~/.claude.json`（本机个人、含密钥）。

---

## 3. 任务 → MCP 路由表（日常查阅）

| 我想做的事 | 首选 MCP | 备选 | 备注 |
|-----------|----------|------|------|
| 看一张 UI 截图 / 报错截图 / 技术图 | `zai-mcp-server` | `vision-bridge` → `4_5v_mcp` | 智谱先；UI 配色细节肉眼复核（见 CLAUDE.md 验证节奏） |
| 数据可视化图表分析 | `zai-mcp-server`(analyze_data_visualization) | — | 专图专工具 |
| UI 设计稿 ↔ 实现比对 | `zai-mcp-server`(ui_diff_check) | — | |
| 联网搜资料 / 查最新 API | `web-search-prime` | `WebSearch` skill / `byted-deepsearch` | 智谱先 |
| 读某个网页 / 文档 URL 正文 | `web-reader` | `WebFetch` | 不要用下划线重复项 |
| 理解一个开源仓库（结构/某文件/某概念） | `zread` | `github` MCP（原始 API） / 直接 clone | zread 偏语义，github 偏操作 |
| 浏览器里点页面 / 截图 / E2E | `playwright` | — | 重，按需；非默认 |
| GitHub 建仓 / 开 Issue / 开 PR | `github` MCP | `gh` CLI | **当前 PAT 失效**，修复前用 `gh` |
| 把本地截图给模型看 | `zai-mcp-server`（本地路径） | `vision-bridge` | 见 CLAUDE.md 规则 11 |

---

## 4. 分家族手册

### 4.1 视觉 / 识图（同功能三家，智谱优先）

| MCP | 输入 | 提供方 | 定位 |
|-----|------|--------|------|
| `zai-mcp-server.analyze_image` | 本地路径 **或** 远程 URL | 智谱 GLM-4.6V | **主** |
| `vision-bridge.analyze_image` | 仅本地路径 | 火山引擎 Ark | 备选（项目自建，让不支持图的模型也能看图） |
| `4_5v_mcp.analyze_image` | 仅远程 URL | 待查 | 仅当无本地文件时 |

**优先级**：本地文件 → `zai-mcp-server`；若智谱报错/超时 → `vision-bridge`；只有远程 URL 且无本地副本 → `4_5v_mcp`。

> `zai-mcp-server` 另有专用工具：`extract_text_from_screenshot`（OCR）、`diagnose_error_screenshot`（报错诊断）、`understand_technical_diagram`（架构图）、`ui_to_artifact`（UI→代码）、`ui_diff_check`（UI 比对）、`analyze_data_visualization`（图表）、`analyze_video`。按场景选专用工具，比通用 `analyze_image` 更准。

### 4.2 联网搜索

`web-search-prime`（智谱）。参数 `location: cn` 走中文区，`content_size: high` 要深度时用。不通则退 `WebSearch` skill。

### 4.3 读网页

`web-reader.webReader(url)`。**不要用** `web_reader`（下划线）——同端点重复服务，保留一份即可（见 §5）。

### 4.4 读开源仓库

`zread` 三件套：`get_repo_structure`（结构树）/ `read_file`（读文件）/ `search_doc`（语义问答）。
**已知限制**：zread 走 zread.ai 索引，部分仓库未收录（如 `mapbox/geojson.io` 返回 "repo not found"）。此时退 `github` MCP 的 `get_file_contents` 或直接 `gh api`。

### 4.5 浏览器自动化

`playwright`。能力全（导航/点击/填表/截图/network/snapshot）。**按 CLAUDE.md 验证节奏**：常规前端改动不自动上 Playwright，仅在异步/控制流/数据流隐患或用户明确要求时用。

### 4.6 GitHub

`github` MCP（Issues/PRs/代码搜索/分支）。**当前 `Bad credentials`**——`.mcp.json` 里 `GITHUB_PERSONAL_ACCESS_TOKEN: ${GITHUB_PAT}` 未注入环境变量，且条目标了 `disabled:true` 却仍被加载。修复见 §5。修复前用 `gh` CLI 顶替。

---

## 5. 已知问题 & 运维

### 5.1 ❌ github MCP 认证失败（待修）
- 现象：任何调用返回 `Authentication Failed: Bad credentials`。
- 原因：`.mcp.json` 用 `${GITHUB_PAT}` 占位，但本机环境变量未设；且 `disabled:true` 未生效（仍被加载）。
- 修复二选一：
  - **启用**：设环境变量 `GITHUB_PAT`（有效 token），把 `disabled` 改回 `false`/删除。
  - **彻底关**：保留 `disabled:true` 并确认重启 Claude Code 后不再加载；或从 `.mcp.json` 移除该条目。
- 临时方案：用 `gh` CLI。

### 5.2 ⚠️ web-reader 重复服务
- `web-reader`（连字符）与 `web_reader`（下划线）指向同一智谱端点，两份都活着。
- 建议：保留 `web-reader`（与 `.claude.json` 键名一致），移除 `web_reader` 来源（需排查其配置位置，可能在插件层）。

### 5.3 🔑 API Key 安全
- 智谱 Key（GLM Coding Plan）当前以明文存于用户级 `~/.claude.json`。该文件在项目外、不入 Git，但属敏感凭据：
  - **勿**将 Key 复制进任何项目文件 / 文档 / 提交 / 截图。
  - 若怀疑泄露 → 立即去智谱控制台轮换。
  - 项目内引用一律写「智谱 API Key (GLM Coding Plan)」，不写实值。
- `.mcp.json` 中 github 用 `${GITHUB_PAT}` 环境变量占位，是更安全的范式，新 MCP 宜效仿。

---

## 6. 新增 MCP 流程

1. **同类查重**：先看本表 §2 是否已有同功能 MCP。有 → 优先用智谱那一个（除非连不上）。
2. **配置落位**：团队共享的进项目 `.mcp.json`（随 Git）；含个人密钥的进用户 `~/.claude.json`。
3. **密钥**：能用 `${ENV_VAR}` 占位就别硬编码；必须硬编码的只放用户级、不入 Git。
4. **冒烟测试**：加完后各发一个最轻量调用（搜索一词 / 读 example.com / 读一个已知仓结构），确认非 4xx/5xx。
5. **回填本文档**：更新 §2 清单 + §3 路由表，状态写实测结果与日期。
6. **评估是否升 ADR**：若引入改变架构选型（如换默认视觉 provider），补一条 ADR。

---

## 7. 测试日志

### 2026-06-17 首次全量冒烟测试
- `web-reader` ✅ 读 example.com 正常
- `web_reader`（下划线）✅ 同上（确认重复，见 §5.2）
- `web-search-prime` ✅ 「MapLibre GL JS 热力图」「智谱 BigModel MCP server」均返回结果
- `zread` ✅ `maplibre/maplibre-gl-js` 结构树正常；`mapbox/geojson.io` 返回 not-found（索引未收录）
- `zai-mcp-server` ✅ 本地 PNG 识图正常（toolbar-v1 / geojson-io-ref）
- `vision-bridge` ✅ 本地 PNG 识图正常（火山引擎）
- `4_5v_mcp` ✅ 远程 URL 识图正常
- `playwright` ✅ 导航 example.com + snapshot 正常
- `github` ❌ `Bad credentials`（见 §5.1）
