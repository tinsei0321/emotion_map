# 会话交接卡

> 换机/新会话后读取此文件恢复上下文。**单份当前快照**——每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。

## 🔄 换机协议（常驻）

**离开前**：① `git status` 清空（全 commit）② `git push`（`git log origin/main..HEAD` 应空）③ 更 `docs/revision-log.md` + 本卡 ④ `.claude/` 改动也 commit。
**到机后**：① `git pull` + 确认同步 ② 读本卡「当前节点」③ 天地图 4 底图 JSON 被 gitignore（新机从已有机器拷，key 亦在 `core/config.py`）④ `git status` 确认。

## 当前节点 — 2026-06-24（办公机 · 地点搜索 Phase 2 待做）

### 机器 & 同步
- **机器 = 办公机**（`C:\Users\admin\`）。auto-memory 12 条本机生效。
- **分支 = `feat/location-search-emotion-rebalance`**（base `6ae4d1b`，**未 push、未并 main**——Phase 2 完成后再议合并）。
- Phase 0/1/1b 已 4 commit：`d58913b`(place 层) → `c1de771`(重平衡+本地化) → `b0ec1cb`(DeepSeek 脚本) → `9108468`(revision-log §5.11)。
- 批准的计划文件：`C:\Users\admin\.claude\plans\emotion-map-docs-revision-log-md-5-3-rippling-blanket.md`（含完整 Phase 0/1/2 设计；`REFACTOR_PLAN.md` 在仓根是同内容的执行追踪）。

### 已完成（Phase 0+1+1b，全部验证通过）
- **Phase 0 共享 place 层**：[core/place_layer.py](../../core/place_layer.py)（PlaceLayer 单例：`resolve_zone`/`classify_point`/`place_keywords`/`forward`/`reverse`，MOD_PLACE F_001-F_005）+ [DATA/place/zone_typology.json](../../DATA/place/zone_typology.json)（6 叙事区×4 时序型）+ [place_keywords.json](../../DATA/place/place_keywords.json)。三块（模拟器/corpus/搜索）共用单一 zone 词表。
- **Phase 1 重平衡 + 本地化**：[snapshot_config.py](../../SCRIPT/snapshot_config.py) `zone_caps` 替硬编码（T1=300/T2=200/T3=325）+ 日期对齐叙事（春节/暑假/五一）+ flavor；[generate_l1_mock.py](../../SCRIPT/generate_l1_mock.py) 默认 1270 高德 POI + cap 计算 + zone 打标 + 传 zone/flavor；[emotion_text_pool.py](../../SCRIPT/emotion_text_pool.py) `sample_text(zone,flavor,locality_bias=0.65)` + [emotion_corpus.json](../../SCRIPT/poi_data/emotion_corpus.json) 起步 ~80 条；[check_spatial.py](../../SCRIPT/poi_data/check_spatial.py) `--rebalance` 硬断言。
- **实测**：二马路 28%→**9/5/9%**、密度比 47×→**13-24×**、score arc **0.447/0.557/0.630**、本地性 全图 **60-69%**/重点 **74-79%**、落水 0%。`py SCRIPT/poi_data/check_spatial.py --rebalance` 全过。
- **Phase 1b**：[generate_corpus.py](../../SCRIPT/poi_data/generate_corpus.py)（DeepSeek 按需扩充 corpus，PII 安全，可选——起步语料已达标）。

### 下轮（Phase 2）— 地点搜索功能
**已锁定决策**（勿重问）：
- 地理编码源 = **本地 1270 POI 即时（rapidfuzz）+ 高德 API 补全**（混合；非纯高德——保搜索↔情绪点对应 + 断网可用）。AMAP_KEY 已在 `.env`（高德 Web 服务）。
- 搜索栏：**工具栏(#toolbar 48px)下方居中、间隔 4px 的独立悬浮元素**（z=96，非工具栏内组）；展开 **200px**（=popup 展开宽 [popup.css:19](../../frontend/css/popup.css)）/ 折叠 32px 圆；左放大镜+Search、右 Ctrl+K、灰发丝线框、**圆角胶囊**（非圆角矩形）；胶囊语言镜像 [.linestyle-cap](../../frontend/css/settings.css)（无线框+阴影+白底）；过渡 `--geojson-transition` 150ms。
- 交互：点折叠圆→展开→再点聚焦→点外收→Esc 收；**仅 pointerdown-outside+Esc 收（绝不用 blur，防 150ms 形变期误触）**；联想(debounce 300ms/≥1字/↑↓Enter)+历史(localStorage)+Ctrl+K 全局聚焦；结果→`fitBoundsTo`([map.js:511](../../frontend/js/map.js))+marker/popup。空白点击→反查 chip（[popup.js:217](../../frontend/js/popup.js) `classifyMapClick` 无 lyr- feature 分支）。
- 地理编码层 = **place_layer 已具备** `forward(query,limit)`/`reverse(lng,lat)`/`geocode_address`（本地）；Phase 2 加高德兜底包装。

**文件清单**：
- 后端：新建 [core/geocode.py](../../core/geocode.py)（MOD_GEOCODE F_001-F_004/D_001-D_002；本地 place_layer 主 + 高德 regeo/geo/place-text 兜底；**统一 `_amap_request` 强制双向 GCJ-02↔WGS84** 复用 [coord_transform.py:52-78](../../core/coord_transform.py) `gcj02_to_wgs84`/`wgs84_to_gcj02`；`AMAP_KEY=os.environ.get`；镜像 [relevance_filter.py:622-640](../../SCRIPT/relevance_filter.py) requests+重试；LRU 缓存）+ 改 [api/schemas.py](../../api/schemas.py)（PlaceSearchRequest/Hit/Response、Geocode、ReverseGeocode，镜像 BufferRequest）+ 改 [api/routes.py](../../api/routes.py)（3 GET：`/place/search`、`/geocode`、`/reverse-geocode`，调 PlaceLayer 单例；`api/main.py:39` 自动注册）+ [requirements.txt](../../requirements.txt) 加 `rapidfuzz>=3.0.0`（py3.14 无 wheel 退 difflib，place_layer 已实现回退）+ [AGENTS.md](../../AGENTS.md) 加 MOD_GEOCODE。
- 前端：[design/tokens.json](../../design/tokens.json) 加 `search.{width:200px,collapsedSize:32px,zIndex:96}` 跑 generate_css.py + 新建 `frontend/js/search-bar.js`+`frontend/css/search-bar.css`（手写状态机，不用 maplibre-gl-geocoder）+ `frontend/js/api.js` 加 `searchPlaces/geocodeAddress/reverseGeocode`（同源 `/api/`）+ [index.html](../../frontend/index.html)+[main.js](../../frontend/js/main.js) 标记+`initSearchBar(map)` + [popup.js](../../frontend/js/popup.js) 空白点击→`.place-chip`。

**验证**（项目政策=仅控制流/数据流/CRS 上 Playwright，不验像素）：① CRS：搜已知 POI→flyTo→marker 像素位 vs 静态 GeoJSON 同 POI 偏移<2px（抓漏转 GCJ-02 的 50-500m 偏移）② 控制流：状态机 6 态 + 形变期焦点不丢 ③ 数据流：空白点击→reverse→chip 独立 DOM + 下次非空点击清空 ④ CRS 反查：点大南门二马路片区→chip=`二马路-解放路核心老街`。

**红线**：AMAP_KEY 绝不进前端 JS（Web 服务 Key 是 IP 白名单，进 JS 被拦/泄露）——只 `.env`+服务端+`/api/` 反代；合并前 grep 前端无 `AMAP_KEY` 字面量。统一 `_amap_request` 包双向转 + 1m 往返单测。

### 怎么跑
```
py frontend/serve.py 8080          # 前端 + 反代 /api/* → :8000（一条命令）
py -m pytest tests/ -q             # 提交前
PYTHONUTF8=1 py SCRIPT/poi_data/check_spatial.py --rebalance   # 回归重平衡
```

### ⚠ 注意
- 分支未 push；Phase 2 完成后用户决定合并（走 PR 或直接并 main）。
- `DATA/processed/` 的 L1/L2 GeoJSON 已是 v3.3 重平衡后的（含 `zone` 列）——Phase 2 前端可直接读。
- 高德返回 GCJ-02，**每次结果必须转 WGS84**（#1 高德 bug：漏转静默偏移 50-500m）。

## 工作机制速查（memory 在线时快查）
- **session-handoff**：满载/任务边界/用户提 token/主题切换 → 主动给 4 件套（提示+理由/新会话衔接/操作/commit 小结）。
- **token-saving**：分会话（最有效）+ subagent 分流 + 少全读（grep+offset）。不降 effort。
- **maintain-revision-log**：每次 commit → §5 追加一行；任务树（顶部 ★）全程维护。
- **kde-loadbearing**（勿破坏）：联动排除 + 独占显示（新热力图隐其他层 + dispatch `layers:changed`）。
- **tool-layer-convention**：工具生成层 = 独立组卡 + 要素按钮开本工具弹窗。
- **no-routine-playwright**：UI 改动交付用户肉眼验；Playwright 仅留给控制流/数据流/CRS 风险。
- **中文交付**（plan/报告/docs）+ 术语纠正；**红线操作先问**（删文件/.env/push/rebase/发布）。
