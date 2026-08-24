# PT-CB14 · 修复批 claude 执行记录（claude·2026-08-24）

> 依据：`PT-CB14-修复批任务书_zcode-2026-08-24.md` claude 包（四件简单类）。分支 `EMC_harness_dsh`·git 由主手代提交。

## 总览

| # | 项 | 状态 | 验收回执 |
|---|---|---|---|
| C1 | D-4 qty 点层注册（11 层） | ✅ | list_data 点层 23（12→23）；zonal_stats 跑通 |
| C2 | D-1 清单一致性（presets 过滤 + resolve 文案） | ✅ | admin_community 不在清单；报错含「未落盘」+ 文件名 |
| C3 | D-6 测试件标记（data_nature='test'） | ✅ | 完整链路实测：图层名 `[dsh] [测试] …` |
| C4 | D-7 引擎徽标 + [dsh引擎] 前缀 | ✅ | 浏览器三态实测 light/dsh/mock 跟随 |
| — | 全量门禁 | ✅ | 581 passed + 2 skipped（基线 574+2·上浮 +7 新增测试·零退化） |

改动文件：`core/geo_registry.py` + `tools/mcp_server_emc.py` + `frontend/js/ai_qa/panel.js` + `frontend/js/ai_qa/brain-adapter-dsh.js` + `docs/render-contract.md` + `tests/test_ptcb14_claude_batch.py`（新）+ `tests/test_render_channel.py`（1 行适配）。
白名单外单行：`frontend/js/render_client.js:113`（[测试] 徽标分支——C3 验收「前端徽标 [测试]」必需·单行·主手可复核）。

## C1 · D-4 qty 点层注册

**改动**（core/geo_registry.py）：`_POINT_LAYERS` 追加 11 个 qty 层，照 `subj_12345_*` 先例：
- 第 4 元素子目录 `'DATA/boundaries/presets'`（先实测确认文件在 presets 而非 analysis）·`level='CHECKUP'`·GeoJSON 格式走既有 `get_layer_points` GeoJSON 分支。
- id 与验收口径一致：`qty_合并` `qty_安全_住房` `qty_安全_合并` `qty_安全_安全消防` `qty_安全_市政管网` `qty_民生_交通设施` `qty_民生_住房` `qty_民生_停车设施` `qty_民生_公服设施` `qty_民生_合并` `qty_民生_物业街面`。
- 数据=客观轨 77 项量化点（属性：指标/中类/board·无极性）。

**验收回执**：
- `list_data` 点层 **23**（原 12 + 11 qty）✓
- `zonal_stats(boundary='checkup_cfg_community', layer='qty_民生_停车设施', sort_by='point_count', top_n=5)` 跑通：返回 5 rows（首行营盘路社区 point_count=23）✓
- 11 个文件全在盘（`os.path.isfile(_layer_path(...))` 逐个断言）✓

## C2 · D-1 清单一致性

**改动**：
1. `tools/mcp_server_emc.py` list_data presets 循环：`available = os.path.isfile(os.path.join(os.path.dirname(MANIFEST), fname))`·不可用 continue（与点层段同纪律）+ 透出 `available: True`。
2. `core/geo_registry.py` `resolve_boundary` FileNotFoundError 文案改「文件未落盘·需上传：{file}（manifest 已登记）」——file 从 manifest 反查（读 `_PRESETS_DIR/manifest.json` 匹配 id）。

**验收回执**：
- 清单 presets 60（63 − 3 缺文件：`admin_community` / `renewal_unit` / `tmp_render_1787246545`——admin_community 不再出现在清单 ✓
- `resolve_boundary('admin_community')` 报错：「边界 preset 不可用: admin_community（文件未落盘·需上传：admin_community_official.geojson（manifest 已登记））。可用 preset: […]」✓

## C3 · D-6 测试件标记

**改动**：
1. `tools/mcp_server_emc.py` render_spec：`data_nature` 白名单增 `'test'`；**dataset_id 路径下 test 不被 dataset meta 覆盖**（real/demo 仍以 dataset 为准·防 LLM 谎报语义不破）。
2. `docs/render-contract.md` §五：`data_nature` 增 test 值 + 清理纪律一行（测试 spec 用毕即删）。
3. `frontend/js/render_client.js:113`（白名单外单行）：natureBadge 增 `'test' → '[测试] '` 分支。

**验收回执**（完整链路实测）：
- 后端：dataset 路径 + inline 路径 `data_nature='test'` → caliber_lite.data_nature='test' ✓；无显式 test → 仍 dataset meta（'real'）✓（回归）。
- 前端：投递 test spec → SSE 推流 → 图层名 = `[dsh] [测试] PT-CB14测试投递` ✓
- 测试 spec 用毕已删（清理纪律执行回执）。

## C4 · D-7 引擎徽标

**改动**：
1. `frontend/js/ai_qa/panel.js`：新增 `_initEngineBadge()`——chat-head 内 title 后、spacer 前插入常驻徽标（胶囊·无边框·EMC dark 面板色系：light 灰 #8fa0b5 / dsh 橙 #d97757 / mock 紫 #9a8fd8）·`initChatPanel()` 调用·模式读 `getEngineMode()`（单一权威）。
2. `frontend/js/ai_qa/brain-adapter-dsh.js`：error 降级卡 hint 前缀 `[dsh引擎]`（「[dsh引擎] 端点不可用：…」）。
3. `frontend/js/ai_qa/panel.js`：`_REASON_LABEL.DSH_ENGINE_FAIL` 同步加前缀「[dsh引擎] 端点暂不可用（已自动诊断）」。

**验收回执**（浏览器实测·8080）：
- 默认页：徽标「引擎·light」常驻（chat-title 右侧）✓
- `?engine=dsh`：徽标「引擎·dsh」（#d97757）✓
- `?engine=mock`：徽标「引擎·mock」（#9a8fd8）✓
- 页面 console 无新增错误（7 个 error 均为既有：arcgisonline 外网瓦片超时/favicon 403/time-source manifest 404）。

## 测试与门禁

- 新增 `tests/test_ptcb14_claude_batch.py`：7 用例（C1 注册+可读+23 层、C2 过滤+文案、C3 三路径+契约文档、C4 源码契约）。
- 适配 `tests/test_render_channel.py::test_list_data_data_nature_and_preset_passthrough`：fake manifest 的 `a.geojson` 补落盘（新过滤契约下未落盘本就不该进清单）。
- 全量门禁：**581 passed + 2 skipped**（基线 574+2 → +7 新增·零退化）✓

## 纪律回执

- 未动 Qoder 包文件（~/.dsh / api/aiqa_routes.py 零接触·并行不相交）✓
- 白名单外单行（render_client.js:113）已在上文显式注明，供主手抽检 ✓
- 测试 spec 用毕即删（清理纪律）✓
- 停止等待主手回收（抽检 + 门禁复核）。
