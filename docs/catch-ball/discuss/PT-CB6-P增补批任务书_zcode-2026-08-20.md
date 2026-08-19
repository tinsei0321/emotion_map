# PT-CB6 · P 增补批任务书（先行件增补·dsh 执行）

> 依据：主任务书 §九增补件（50384e07）**未随三砖实施**（dsh 从旧版开工）——本单为落地版。白名单五件：`tools/mcp_server_emc.py`、`frontend/js/render_client.js`、`tools/demo_pioneer.py`（新）、`tests/test_render_channel.py`、执行记录增补段。commit `PT-CB6(P+)`。基线 **425+2**（注明·并查明一条 skip 翻转原因）。

## 任务四件

### +1 scheme 受管样式预设（覆盖旧 token 机制）

- spec `style` 改为 `{"scheme": "...", "value_field": "...", "ramp_hint": ""}`；词表 v1 两项：
  - `community_choropleth_v1`：**sequential 分级着色**（适用 count/件数类字段）——grep 复用现有社区面按件数分层着色机制（page4/6 先例·map.js/shared.js 真身·分档+色带照抄·**勿用 piToNorm**——那是极性专用 -2~2）；
  - `point_default_v1`：现 point circle 样式照旧。
- render_spec 校验 scheme∈词表（未知→ok:False+词表名提示）；前端按名解析·未知拒渲染+控制台词表提示。旧 `token` 字段兼容读（映射到对应 scheme）但不再产出。

### +2 F2 数据性质徽标

- `list_data`：点层按池路径判 `data_nature: 'demo'|'real'`（performance 路径=demo·其余=real）；preset 项同字段透传（sim 层 demo）。
- render_spec：spec `caliber_lite` 增 `data_nature`（dataset 路径判定·inline 由调用方声明参数 `data_nature='real'|'demo'` 默认 real）。
- 前端：图层名徽标 `[真实] ` / `[演示] `（在 `[dsh]` 之后）。

### +3 demo_pioneer.py 演示脚本（v2 场景本机版·无 dsh 验砖）

顺序执行并打印回执：①`zonal_stats(layer='checkup_12345_2024', boundary='<174社区面 preset id>', top_n=10, layer_output=True)` ②`render_spec(kind='choropleth', scheme='community_choropleth_v1', value_field='point_count', name='12345热线诉求最密集社区(真实)', data_nature='real')`（inline 路）③安全/民生社区点层各一张同法 ④每步打印 ok/spec_id/inbox 路径 + 末尾提示「起 serve 后开 8080·EventSource 自动消费」。174 社区面 preset id 以 list_data 实查为准（找不到则停手记录）。

### +4 caliber_lite 口径字段

- render_spec 增可选参数 `community_caliber: int`（174|154|118|130…）；填则入 `caliber_lite.community`（K-C1 语义）；demo 脚本三图均传 174。zonal layer_output 的返回附 boundary 对应口径提示（可选）。

## 验收

pytest 全绿（上浮注明+skip 翻转说明）；`py tools/demo_pioneer.py` 实跑三 spec 落 inbox 回执齐全；node --check；执行记录增补段（四件销号+skip 说明+174 preset id 记录）。
