# PT-CB6 · 先行件任务书：三砖（dsh 入口 + 8080 显示屏）· 详细设计与拆解

> 主手：zcode（设计）·执行：**dsh**（用户令·2026-08-20）。本单=函数级规格·零判断执行；签名不符即停手记「待主手裁决」。
> 分支 `EMC_harness_dsh`（main 冻结）。commit 前缀 `PT-CB6(P{n}):`。基线 **416+3**（上浮注明）。
> 依赖现状：七插座已上线（`tools/mcp_server_emc.py`·F_021-F_027·含 usage 守卫）；前端预设清单经 `GET /api/v1/range/presets` 服务；`DATA/exports/` 已 gitignore（运行时收件箱落此）。

---

## 〇 总图与红线

```
dsh 会话 ──MCP──> render_spec（第8插座·F_028）──写──> DATA/exports/render_inbox/*.json
                                                        │ 后端 watcher 线程（F_029）
浏览器(8080) <──SSE /api/v1/render/stream────────── api/render_routes.py
   └─ render_client.js 收 spec → 取数（inline 或 GET /api/v1/render/dataset/{id}·F_030）
        → 令牌解析（现有样式函数）→ 现有加层函数铺层（图层名前缀 [dsh]）
```

**红线**：①QA 主链路（diagnose/FC/final/面板）**零接触**——全部为新增文件+两处挂载行；②**令牌解析权威留 JS**（服务端零样式逻辑·铁律 11 精神·防双源）；③**显示不受 G-2 拒**（渲染≠分析输入——结论层允许显示·但 usage 透传前端打徽标）；④A9 纪律：watcher/守卫异常**禁宽 except 静默**（至少 log 一行）；⑤图层名用现实内容命名（铁律·禁实现术语）。

## 一 render spec 契约 v1（本批核心契约产出·第 6 张平台契约）

```json
{
  "spec_version": 1,
  "spec_id": "<UTC毫秒>-<4位随机>",
  "kind": "point | choropleth",
  "data": { "dataset_id": "<preset或点层id>" } 或 { "geojson": {FeatureCollection·要素≤60} },
  "style": { "token": "point | choropleth", "value_field": "polarity_index",
             "ramp_hint": "worst_first | 默认省略" },
  "ui": { "name": "<图层名·现实内容>", "zoom_to": true },
  "origin": { "producer": "dsh", "source_tool": "rank | zonal_stats | manual" },
  "caliber_lite": { "usage": "input | analysis_output", "note": "可选一句口径" }
}
```

## 二 P1：render_spec 第 8 插座（tools/mcp_server_emc.py 扩展）

- `register_track_id('MOD_AIQA.F_028', 'MCP render_spec（图层图纸：dataset/inline→spec 落收件箱）')` + `@track`；
- 函数 `render_spec(kind: str, name: str, dataset_id: str = '', geojson: dict = None, value_field: str = 'polarity_index', ramp_hint: str = '', zoom_to: bool = True, producer: str = 'dsh', source_tool: str = 'manual') -> dict`
- 校验（全部语义化错误+caliber）：kind∈{point,choropleth}；name 必填；data 二选一必填（都给→dataset_id 优先·fixes 注明）；`dataset_id` 须能解析（preset 任意 usage 均可渲染·查 manifest 得 usage 填 caliber_lite；点层 id 亦可——查 geo_registry）；`geojson` 须 FeatureCollection 且要素 ≤60（超限→错误提示改用 dataset_id）；choropleth 须 value_field 非空；
- 动作：spec 组装 → 写 `DATA/exports/render_inbox/<spec_id>.json`（ensure_dir·UTF-8·无 BOM）→ 返 `{ok: True, spec_id, inbox_path, caliber}`；
- 工具描述写明：「产物经 8080 前端显示屏呈现；需浏览器已打开情绪地图页面」+ 耗时声明（毫秒级）；
- caliber：`{'scale': '呈现层', 'semantics': '图层图纸（数据引用+样式令牌）——由前端解析渲染', 'limits': 'v1 语义令牌（无解析副本·场景S 双载留 v2）；非分析操作', 'refs': ['G-2(显示徽标)', '渲染契约v1']}`。

## 三 P1b：zonal_stats/rank 增 `layer_output` 参数（同文件）

- 签名加 `layer_output: bool = False`；True 时返回值增 `geojson`：**仅 top_n 行对应多边形**（merged 子集→`__geo_interface__`·WGS84·≤20 硬顶随 rows）·properties 带该行统计值（含 value 字段）；False 时行为与现状逐字节一致（默认零变化）；
- 用途：宿主把分析结果直接喂 render_spec（inline 路）。

## 四 P2：投递通道（api/render_routes.py 新文件）

- `register_track_id`：`MOD_AIQA.F_029`（inbox watcher+SSE 流）、`MOD_AIQA.F_030`（dataset 取数端点）；
- **watcher**：模块导入时起后台线程（daemon）：扫 `DATA/exports/render_inbox/*.json`（按文件名 spec_id 排序·记录 last_seen）→ 新文件 json.load 校验 spec_version → 推入 `queue.Queue`；单条异常 log 一行并跳过（A9：不静默吞线程）；目录不存在自动建；
- `GET /api/v1/render/stream`：`StreamingResponse(media_type='text/event-stream')`——连接即先推 backlog（最近 20 条缓存）再持续推 queue 新品；事件格式 `event: spec\ndata: <spec JSON>\n\n`；心跳注释行每 15s（防代理断连）；
- `GET /api/v1/render/dataset/{dataset_id}`：preset→`resolve_boundary`→fc；点层→`resolve_points`→fc；要素 >2000 时降级提示（返 `{ok:False, hint:'要素过多·请用分析工具聚合后再渲'}`）；未知 id→`{ok:False, hint:_UNKNOWN_HINT 风格}`；
- `api/main.py` 挂载（**白名单内唯二行改动**）：import + `app.include_router(render_router, prefix='/api/v1')`。

## 五 P3：前端 loader（frontend/js/render_client.js 新文件）

- ES module；`new EventSource('/api/v1/render/stream')`（onerror 原生自动重连·console 一行提示）；
- `onmessage('spec')` → `_apply(spec)`：
  1. 取数：`data.dataset_id` → `fetch('/api/v1/render/dataset/'+id)`；`data.geojson` 直接用；
  2. 解析令牌（**权威在此**）：kind=point→复用现有点层 circle 样式构造（**开工先 grep**：`generate_point_layer`/`addToolboxLayer` 在 tools.js 的样式与加层真身·照抄参数形态）；kind=choropleth→按 `style.value_field` 分层着色（grep map.js 社区面 choropleth/分层着色机制真身·色带用现有体系勿新造）；
  3. 铺层：调现有加层函数（同上 grep 所得）；图层名 = `'[dsh] ' + spec.ui.name`；layer properties 附 `origin=spec.origin` 与 `usage=spec.caliber_lite.usage`（analysis_output 时控制台提示一行·v1 徽标即此前缀）；
  4. `zoom_to` → 调现有 fitBounds 类函数（grep 真身）；
- `frontend/index.html` 加一行 module script（白名单内）；**不改任何既有 js 文件**；
- 降级：后端未起→EventSource 连接失败自动重试·页面其余功能不受影响。

## 六 测试（tests/test_render_channel.py 新）

1. render_spec 结构用例（ok+spec_id+inbox 文件落盘+内容含 spec_version/kind/origin）；
2. inline 上限（61 要素→拒）与 data 双缺（→拒）；
3. dataset_id 校验（未知→ok:False；analysis_output 的 preset → **ok:True 且 caliber_lite.usage=analysis_output**——显示不拒·徽标透传断言）；
4. zonal/rank `layer_output=True` 返 geojson 要素数=top_n 且 ≤20；默认 False 无 geojson 键；
5. watcher：tmp inbox 放两个有序文件→queue 收 2 条且顺序对；坏 JSON→跳过不崩（捕获 log）；
6. dataset 端点：preset id 返 fc 含 features。

## 七 验收（用户参与·演示三步）

1. `py frontend/serve.py 8080` 起服务·浏览器开页面；
2. dsh（或本机模拟调用）`rank(boundary='admin_district', layer_output=True, top_n=3)` → 把返回 geojson 传 `render_spec(kind='choropleth', value_field='polarity_index', name='情绪最差三区', source_tool='rank')`；
3. **8080 地图自动亮层**（[dsh] 前缀+分层着色+缩放）；另测 `render_spec(dataset_id='admin_street', kind='choropleth', ...)` 直渲一路。
node --check 两 js；pytest 全绿（416+3+新增·注明）。

## 八 白名单与产出

白名单七件：`tools/mcp_server_emc.py`、`api/render_routes.py`（新）、`api/main.py`（唯二行）、`frontend/js/render_client.js`（新）、`frontend/index.html`（唯一行）、`tests/test_render_channel.py`（新）、执行记录 md（`PT-CB6-P执行记录_dsh-{日期}.md`：三砖销号+grep 所得真身签名记录+演示截图说明/命令回执+待主手裁决项）。量级预估 1.75-2.25d。
