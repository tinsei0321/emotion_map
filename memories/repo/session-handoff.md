# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。

## 🔄 换机协议（常驻）

**离开前**：① `git status` 清空（全 commit）② `git push`（`git log origin/main..HEAD` 应空）③ 更 `docs/revision-log.md` + 本卡 ④ `.claude/` 改动也 commit。
**到机后**：① `git pull` + 确认同步 ② 读本卡「当前节点」③ 天地图 4 底图 JSON 被 gitignore（新机从已有机器拷，key 亦在 `core/config.py`）④ `git status` 确认。

## 当前节点 — 2026-06-25（办公机 · Phase 2 地点搜索已交付，并入 main，转 Search 继续开发）

### 机器 & 同步
- **机器 = 办公机**（`C:\Users\admin\`）。
- **分支 `feat/location-search-emotion-rebalance`**：Phase 2 两 commit `69d2c46`(后端)+`cc5d97b`(前端) **本地 ahead 2、未 push**；`main=c92b921`（PR #1/#2 已并 origin/main）。Phase 2 合并走 **PR #3**（镜像既有 #1/#2 流程，需 push）。
- **L1→L2 analysis 暂时搁置**（用户 06-25 决定）→ `test_emotion_analysis.py::test_capabilities` 既有失败不修（属搁置范畴，非本次引入，已 stash 隔离确认）。

### 已完成（Phase 0+1+1b+2，全部验证通过）
- **Phase 0/1/1b**（前次会话）：共享 place 层 + 二马路重平衡 + 评论本地化（详见 revision-log §5.11）。
- **Phase 2 地点搜索（本次会话，2 commit）**：
  - **后端** [core/geocode.py](../../core/geocode.py) MOD_GEOCODE F_001-F_004/D_001-D_002：本地 place_layer 主 + 高德 place/text·geo·regeo 兜底；`_amap_request` 注 key+3 次重试+lru_cache。**红线①** AMAP_KEY 仅服务端 `_load_env()` 读 .env（[api/main.py](../../api/main.py) 不加载 .env，故 geocode 自带兜底）；**红线②** 高德 GCJ-02 一律 `_gcj_loc_to_wgs`（正向）+ regeo 入参 `wgs84_to_gcj02`（反向）。[api/schemas.py](../../api/schemas.py) 4 schema + [api/routes.py](../../api/routes.py) 3 GET（`/place/search`、`/geocode`、`/reverse-geocode`）。[tests/test_geocode.py](../../tests/test_geocode.py) 16 测试（**1m 往返 CRS 红线** + 本地搜索/反查 + amap 降级）。
  - **前端** [frontend/js/search-bar.js](../../frontend/js/search-bar.js)+[search-bar.css](../../frontend/css/search-bar.css) 手写 6 态状态机（collapsed→expanded→focused→suggesting/history→navigating；debounce 300ms；localStorage 历史 8；Ctrl+K 全局聚焦；**仅 pointerdown-outside+Esc 收，绝不用 blur** 防 150ms 形变误触）；镜像 `.linestyle-cap` 胶囊（无线框+阴影+白底+选中蓝），32px 圆→200px。[api.js](../../frontend/js/api.js) 加 `searchPlaces`/`geocodeAddress`/`reverseGeocode`。[popup.js](../../frontend/js/popup.js) `classifyMapClick` blank 分支→reverse→`.place-chip`（独立 DOM，clear-before-show 替换）。[tokens.json](../../design/tokens.json) `layout.search.{width,collapsedSize,zIndex}` → generate_css.py。
  - **实测**（Playwright，政策=控制流/数据流/CRS 上验）：零 JS 错误；6 态 + 形变后焦点不丢；搜「万达」→10 联想→点选→flyTo `center==hit 坐标`（**CRS 自洽**，前端原样透传 WGS84）+marker+popup+入历史；空白点击→chip zone+poi 与 API 一致 + 替换不累积；>500m 触发高德 regeo 实测回街道。**红线** `grep AMAP_KEY frontend/` 零命中。

### 下轮 — Search 功能继续开发（v1 已闭环，方向待选）
v1 地点搜索闭环：POI 查 → flyTo → marker/popup → 空白点击反查 chip。候选下一步（用户 06-25 指示「马上开始 Search 功能开发」，具体方向已 AskUserQuestion 对齐）：
- **search→情绪联动**（核心价值）：选 POI → 高亮/过滤周边情绪点 + 情绪摘要（需 Import 数据后才有意义）
- **搜索体验增强**：类别/区筛选、结果分组、键盘流、历史 UI
- **逆地理增强**：chip 可点击 → 展开周边情绪/导出
- **视觉打磨**：用户开页肉眼验后的细节（政策：UI 像素交用户验）

### 怎么跑
```
py frontend/serve.py 8080          # 前端 + 反代 /api/* → :8000 + 自动起 uvicorn
py -m pytest tests/ -q             # 提交前（80/81，1 既有失败属搁置 L2）
```

### ⚠ 注意
- Phase 2 两 commit 待 push + PR #3 并 main（用户已指示合并；push 为红线，待授权）。
- `DATA/processed/` L1/L2 GeoJSON 是 v3.3 重平衡后（含 zone 列）——Search 前端可直接读。
- 高德返回 GCJ-02，**每次结果必须转 WGS84**（#1 高德 bug：漏转静默偏移 50-500m）——已 `core/geocode.py` `_gcj_loc_to_wgs` 单点兜底 + 1m 往返单测守住。

## 工作机制速查（memory 在线时快查）
- **session-handoff**：满载/任务边界/用户提 token/主题切换 → 主动给 4 件套（提示+理由/新会话衔接/操作/commit 小结）。
- **token-saving**：分会话（最有效）+ subagent 分流 + 少全读（grep+offset）。不降 effort。
- **maintain-revision-log**：每次 commit → §5 追加一行；任务树（顶部 ★）全程维护。
- **kde-loadbearing**（勿破坏）：联动排除 + 独占显示（新热力图隐其他层 + dispatch `layers:changed`）。
- **tool-layer-convention**：工具生成层 = 独立组卡 + 要素按钮开本工具弹窗。
- **no-routine-playwright**：UI 改动交付用户肉眼验；Playwright 仅留给控制流/数据流/CRS 风险。
- **中文交付**（plan/报告/docs）+ 术语纠正；**红线操作先问**（删文件/.env/push/rebase/发布）。
