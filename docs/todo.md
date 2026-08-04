# 开发追踪 (Tracker)

> 每日 = TODO List + 开发日志。倒序排列。  
> 状态：⬜ 待办 / 🔄 进行中 / ✅ 完成 / ⏸️ 暂缓

> 📦 周归档机制：按自然周（周一~周日）归档历史内容至 `todo-archive/`；本周（含）留本文件，历史周已移归档。
> 📝 详版历史 = [revision-log §5](revision-log.md#L226)（永久审计底）·本文件只记当前 + 计划。
> 📌 **架构版本**：v1（三阶段 5.231-5.242）→ **v2（单次 LLM + FC·5.243-5.245b·第三方实施）** → **v3（v2 做对·5.246-657c2e3·GLM 修复）** → **v3.1**（reg.filter 崩溃修复 + SCAN P1）→ **v3.2**（CB-09 bug 修复·D057 修订·代码自动扩展·全自动多步执行·fix/emc-buglog 分支 7 commit）→ **v3.5**（CB-10/CB-11 系列·merge 多图层 + 只说不做根治）

---

## 📅 2026-08-04（CB-16 全链路闭环 + 发版准备：Wave 0-3 + ③z 余留 + ③w2~③w7 全局优化/措辞修复/发版收尾）

### ✅ ③w4~③w7 措辞修复 + 发版 backlog 收尾 · 全闭环（两组通过·已推 0bb55df）

- **③w4/③w5 措辞修复 + 发版遗留**（已闭环·78db0e3 + 2130a49）：用户实测「EMC 无法回答时结论'无法生成图层'·但问题可能跟图层无关」→ gap 措辞 failedObs 判据（零工具尝试「无法直接回答/无法理解」·试过工具「未生成图层」）+ eval 标尺纠错（select_template 单工具·76%→84% GO·tuple 双接受）+ RST-L06 preset fallback + buffer stale-tool 门控 + e2e-seam 措辞断言
- **③w6/③w7 发版 backlog 收尾**（已闭环·23efe74 + 0bb55df）：footer 条件化（failedObs>0 才「未生成图层」）+ **preset 行政区清 4 要素**（FIXED_ADMIN_DISTRICTS·备份 .bak9·用户拍板·PRM-07 根治）+ **district-stats 8→4 组团** + RST-L06 fallback 补 MC（Codex P1 死代码）+ eval 注释 + **fixture 静态守卫**（防回潮）
- **验证**：pytest 278 passed 零回归·ESM-OK·eval 84% GO·link_checkup 20/20 PASS·B3 快照 84.6%（方差区间）
- **已推**（0bb55df·先验后推解锁·远端 0/0 同步）
- **待续**：发版就绪度回归（B3 重跑 + eval 复采 + RST-L06 复跑·前台 serve）·时间轴专题（manifest 404 同源派生方案）·backlog（陈旧注释·FC boundary·MOD_PLACE·MOD_LLM.F_002）

### ✅ ③w2/③w3 全局优化 + 发版快照 · 全闭环（两组通过·已推 ff7b125）

- **全局优化**：CLAUDE.md 当前开发状态 5 行（L3✅·L4🔄·空间✅·UI✅·L0→L1 sim）+ todo 周归档（07-27~08-02）+ decisions ADR-017~019 + 记忆 GC
- **backlog 收尾**：validate_skill_params drift 修复（paradigm `_sync_geo_catalog_guard_fields`·1 FAIL→4 passed）+ renewal 卡 perceptible_metrics domain 门控
- **发版快照**：B3 26 例 pass=22（84.6%·Codex 方差区间）·link_checkup 20/20 PASS·tracklog F_002=25 调用·eval 76% NO-GO（③w5 修·标尺错）·RST-L06 回归（③w4 修·clip range derive）
- **已推**（ff7b125·远端同步）

### ✅ Wave 3 + ③z 余留 2b/P2 · 全闭环（两组检查通过·已推）

- **范围**：出口深化最后一块（多卡 + validate_outlet_fields CI + 可感知计算器 2a + **③z 余留 2b + P2**）
- **多卡落地**：resolve_outlet_ids（跨 domain 多卡·同 domain 最高分）+ build_outlet_schema 返 cards + build_outlet_schema_single 兼容 + /outlet_card 返 {cards, card} + 前端多卡渲染
- **validate_outlet_fields CI 落地**：tests/validate_outlet_fields.py（正则提取消费字段→死字段 fail/缺消费 warn）
- **③z 2b 落地**（两组预检 P1×3 全采纳）：`_parse_emc_expr`（拆 `+`·**多值 `/` 拆列表**·含 polarity→2a）+ compute_perceptible_metrics 2a/2b（**生态宜居明示留 2a**·2b 仅可感知·条件不匹配→跳过·**关键词未命中→跳过**·source 对齐）+ `_kw_hit` 共用
- **③z P2 落地**：checkup_satisfaction prose→真实字段（满意度 polarity_index·8 领域 element_top/domain_top **element_top 优先**·不满意项不动）
- **panel.js 渲染 perceptible_metrics**（可感知指标小节·Codex P2 并入）+ .outlet-metrics CSS（③z3b P2-1）
- **③z3b 检查两组通过**（无 P0/P1）·采纳 P2-1/3（CSS + 边界测试·+2）·P2-2（`==`）不采纳
- **验证**：pytest 276 passed（+9）零回归·真端点（cards 2 张 + B 类条件命中出值·source 标条件+命中）
- **已推**（0a0d103·先验后推解锁·远端 0/0 同步）
- **后续**：backlog（7 工具 drift·MOD_PLACE 渲染风暴·MOD_LLM.F_002·CPD-L01/L02·时间轴 manifest·renewal 卡 domain 门控）

### ✅ CB-15 P1 · 实施后检查通过 + P2 补修（**可 push**·先验后推）

- **范围**：让地点进 EMC 问答管线（A buffer 中文 POI + C lookup_place + D 归因落点模板·B 评论↔POI 后置 Wave 3）
- **两组预检反评价**：四子项方向全对路·无 P0
- **A 落地**：`/geo/buffer` fallback search_place（preset 优先·top-1·无命中诚实 400·WGS84·只对 str center）
- **C 落地**：lookup_place 契约后端 + 前端执行混合（TOOL_CONTRACTS + paradigm + tools.js + SKILL_DEFS + GEO_VERB_KW + track ID F_013）
- **D 落地**：_extract_emc_value 扩 `+` 多字段合成 + 暴露 poi_names/place_name_source + 修 :179 陈旧文案
- **两组检查反评价**：通过·可推（buffer 中文名 200/400 实测·drift 既有性回测确认）+ **P2×4 补修**（触发词去"附近"·source 只列非空·docstring 修·required_slots 对齐）
- **验证**：pytest 266 passed 零回归·括号平衡×3
- **backlog**：validate_skill_params 7 工具 drift（density/buffer/clip/overlay/zonal/extract/merge·paradigm when 同步）
- **✅ 可 push**（两组已验）· **待用户 push** · Wave 3

### ✅ Wave 2 / CB-15 数据认知 P0 · 实施后检查通过 + P1/P2 补修（**可 push**·先验后推）

- **范围**：下钻链最小闭环（place_name 双源融合 + poi_names + /grid/pois + 3220 接入 + 去重）
- **两组预检反评价**：P0 实锤 place_layer 未读 3220（1270≠3220·FC 字段错配）→ _read_pois_geojson 适配层 + _load 合并 + _dedup_pois·P1 语义分层（polygon 保留边界名·grid POI 优先·最近质心）+ place_name_source
- **两组检查反评价**：主体通过 + **glm组 P1**（_dedup_pois 连锁店误删·_seen 先锁 name → name+坐标容差联合判定）+ **Codex P2**（create_square_grid 输出 cell_id 列）+ **测试边界 3 新增**
- **验证**：all_pois=4342（恢复 32 误删连锁店）·grid/pois 200（count=32 CBD）·**pytest 261 passed 零回归**（+3 新增）
- **✅ 可 push**（两组已验）· **待用户 push** · P1（lookup_place/归因落点模板）

### ✅ Wave 1（macro 出口）· 实施后检查通过 + P1/P2 补修（**可 push**·先验后推）

- **范围**：renewal_object_identify（更新对象识别·macro）+ checkup_dimension（体检四维度·含 macro）
- **两组预检**：Codex P1（checkup_dimension 四维度×单尺度语义错位→`[scale=xxx]` 槽位限定）+ claude组 P1×3（① `_extract_emc_value` 统一收 rows/features 单入口 ③ DOMAIN_KW 补「城市体检」长词 ⑤ data_base rows 分支·N=单元数）+ rows 可达性缓存（`_lastToolRows`×3）
- **两组检查反评价**：主体通过（5 环节正确·单测 23 passed）+ **glm组 P1**（runAllToolCalls rows 处理·else 误判 + 守护漏 hasRows→三独立 if + hasRows 放行）+ **Codex P1**（跨轮重置 `_lastToolRows = null`）+ P2×2（while-loop rows 捕获 / 测试改名）
- **测试**：pytest 253 passed · 括号平衡 · test_outlet_macro.py E2E 两场景全过
- **✅ 可 push**（两组已验·先验后推）· **待用户 push + 浏览器复验** · **Wave 2（CB-15 前置·后置）**

### ⏸️ CB-15 数据认知（Wave 2 前置·用户定后置·Wave 1 先行）

- 格↔POI sjoin + place_name 双源 + /grid/pois 端点（讨论稿共识已立·落地未做）
- **排进待办**：Wave 1 完成后推进（用户定优先级）

### ✅ R7 补修（commit a42fb1a·**待用户 push**·两组检查反评价）

R7 修复发实施后检查 → 两组 SCAN：**claude组 P0 发现** `lastIndexOf('.')` 误切 markdown 列表标题「**4.**」句点 → 结论第 N 点落 1500 边界时复现原 bug（场景 4 实测）→ **方案 A 去 `.` 切句符**。
- 采纳：Codex 断句符补 `！？` + 悬空编号行剥除（`/\n\d+\.\s*$/`）+ claude组 文案微调（"已精简"→"已截断保留要点"）+ 补边界测试
- **新增** `tests/browser/test_r7_truncation.py`（e2e-seam 直测真实 JS 逻辑·3 场景：多要素完整 / 失控截断无空标题 / {{show:}} 完整）
- **验证**：新测试全过 + 括号配对 +2/+2 + **pytest 249 passed 零回归**
- **待用户 F5 复验**

### ✅ R7 结论截断修复（commit 0aff59e·**待用户 push**·用户实测发现）

用户浏览器实测「大南门·二马路片区更新需求分析」发现结尾「**4.**\n…（结论已截断）」→ 问"未完成"。
- **根因**：R7 防线（harness.js applyQualityDefense）`>800 字 → slice(0,800)` 字符级硬切·阈值过低（用户定：多要素结论超 800 正常）+ 切点不感知 markdown（切「**4.**」标题后）+ R2 按钮被切连带 + 文案误导
- **修复**（纯 harness.js）：阈值 **800→1500**（用户定）+ 切点**结构回切**（句号/换行·治空标题）+ **R2 移 R7 后**（按钮保留）+ 文案场景化
- **验证**：括号配对完整（+7/+7）·Playwright 页面零 console 错误·**pytest 249 passed 零回归**
- **待用户 F5 复验**：重问「大南门·二马路片区更新需求分析」→ 应不再出现「**4.**」空标题

### ✅ 大南门·二马路数据接入 EMC 出口链路（commit c792c5d·**待用户 push**）

交接卡【下一步】核心待续项打穿——Wave 0 端到端演示数据场景。两组预检通过（Codex 必补项 + claude组 建议全纳入）→ 实施 → 验证 249 passed。

- **backfill**：`SCRIPT/backfill_ermawu_coords.py`（一次性·id_e 断言·保 BOM·备份·生成器修复 TODO）→ T1/T2/T3 共 2400 行补 lon/lat
- **注册点层**：`core/geo_registry.py` 追加 `ermawu_l3l4_t{1,2,3}`（level='L3L4'·富归因列原样保留）
- **边界登记**：`DATA/boundaries/presets/manifest.json` 加 `damanmen_area` + **复制 geojson 进 presets/**（Codex 必补项·name 属性改为片区名）
- **测试**：`tests/test_geo_registry.py` 新建 4 例 + `test_outlet_schema.py` +1 真实聚合出卡
- **端到端验证**：/geo/catalog 暴露 3 ermawu 层 + damanmen 边界 → /geo/zonal_stats 578 点（polarity_index 0.73·文化）→ /outlet_card 命中 **renewal_demand 需求分析卡**（需求强度 0.73·停车难·N=578）
- **pytest 249 passed（+7·零回归）**

### 待续
- **浏览器 EMC 真实问答肉眼验证**（问"大南门·二马路片区更新需求分析"→ 应出诊断卡 + 分析执行 + 出口需求分析卡·LLM 选层/路由走真实链路 + **perceptible_metrics 可感知指标小节**）
- **时间轴 manifest（_time_manifest.json）**（用户定·与需求分析是两件事·后置）
- **backlog**：validate_skill_params 7 工具 drift（paradigm when 同步）· MOD_PLACE 渲染风暴 + MOD_LLM.F_002 fallback 重核 + CPD-L01/L02 + 时间轴 manifest 404 · renewal 卡 perceptible_metrics domain 门控（③z3 已知）

---

## 📅 2026-08-03（CB-13 反评价闭环 · 多步问最终收敛 + PRM-08/CPD 根因定案）

### ✅ CB-13 反评价闭环（revision-log 5.254，commit e052fe7 · **用户手动 push**）

- **多步问最终收敛（CB-12→13 闭环）**：RST-L06 两轮连续 PASS·while-loop 根治（F_002=4）·pro 0 守住
- **PRM-08 根因定案**（两组一致）：FC 选型偏离 compare→extract_feature·非路由退化/非测量层·compare 缺确定性路由兜底 → CB-14 修（先取证）
- **CPD-L01/L02 = 测试基建文件名过期**（Codex 实锤）：`test-cases.js:8` 引用已改名的 `xiling_wujia_*`·1 行修复·产品引导逻辑正常
- **上轮 3 注意点已落地**（_hasSeq 收紧·Pro chain 前置·recover 链前置）
- **反评价**：8 agree / 2 partial / 0 disagree·learning 入库 KNOWLEDGE §3
- **backlog 修正**：MOD_LLM.F_002 79 次=调用数非 fallback 数

### ✅ CB-12 B3-verify-05 全量重测闭环（revision-log 5.253，session B3-verify-05 · **用户手动 push**）

- **B3 全量 26 例（含 RST-L06 新增）pass=23（88.5%）历史最佳**·RST-L06 多步问 PASS（tools=clip,density）→ **多步问修复收敛·CB-12 闭环**
- **PRM 9/10**（PRM-08 compare 链路 fail·tools=extract_feature 单工具·boundary[ERR]）·**F_002=4**（≤5 阈值·while-loop 早停生效）·**pro 0**·计划命中 16/20 步
- 0 timeout·误杀/漏判 0·p95 50s·11.2min
- **残余（非阻塞）**：PRM-08（compare 路由退化）+ CPD-L01/02（引导态 hint 未推）·转 backlog
- **下一步**：进入 CB-13（让 Codex/glm 组检查 PRM-08/CPD 残余 + 多步问修复确认）

### 待续

- PRM-08 compare 确定性路由兜底（CB-14·先带 session 取证 FC 选型）
- CPD-L01/L02 测试基建 1 行修复（CSV 改 resolvePoints('L1-T1')）+ CPD-L03 硬断言
- 发版候选评估（B3 88.5% 达标上沿·整体评估）
- MOD_PLACE 渲染风暴 + fallback 重试（backlog）

