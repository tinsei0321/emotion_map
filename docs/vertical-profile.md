# Vertical Profile · 垂直域档案契约 v0.1（S9 垂域切换位预留 · 2026-08-23）

> **性质**：壳阶段 S9 产出（联合任务书 v1.0 §一.5）——**只预留切换位·不做多垂域实现**（先两垂域后抽象·R26 架子先行纪律的垂域版）。
> **依据**：平台化愿景登记（四层图）+ 壳阶段联合任务书 v1.0 + ACP 契约 v1.1 §六（共享不变量清单·与本文互为表里）。
> **终局定位**：城市规划大模型平台 = 平台层（不变量）× N 个 Vertical Profile（六件套）。

---

## 一 六件套（垂域实例化清单·v1.0 定稿）

| # | 件 | 内容（垂域①情绪地图现状对应） | 备注 |
|---|---|---|---|
| 1 | **数据包** | preset/点层：`DATA/boundaries/presets/manifest.json` + 点层注册表（`core/geo_registry.py`） | 层 id 含垂域前缀（yichang_*）——属垂域数据命名·非平台耦合 |
| 2 | **知识库** | **分两槽**（主手裁定）：**语料槽**=RAG 向量语料（`ai_qa/outlet_kb/` 等白名单目录）；**范式槽**=prompt 组装用结构化知识（`ai_qa/paradigm.py` 尺度-方法-范式矩阵 + `ai_qa/manifesto.py` 领域宪法） | 两形态不同（向量语料 vs 结构化文本）·分槽显式化防混淆 |
| 3 | **口径注册表** | K/G 卡体系 + 社区口径枚举 K-C1（`_口径注册表.md`） | 治理字段 schema 属平台不变量（见 §三-4）·卡内容属垂域 |
| 4 | **身份卡/人设** | FACTS 身份卡（`ai_qa/outlet_kb/urban_renewal_knowledge.py`·topic=identity）+ dsh 人设（preset persona） | 供 kb_facts/presona 双消费 |
| 5 | **工具预设** | 默认 layer/趋势层映射/KB 查询城市（如 `city='宜昌'`·`_TREND_LAYERS`）——当前散落在 `tools/mcp_server_emc.py` 的默认参数 | **切换位第一清偿对象**（见 §二-现状违例） |
| 6 | **渲染预设** | 受管色带词表的垂域子集（HEATMAP_RAMPS）+ 垂域 scheme（情绪极性 diverging / 未来体检达标率 sequential） | 样式权威仍在 EMC 平台层（图层同源红线）·垂域只做**词表内选择**·禁自带色值（render-contract §九） |

> 六件套由五件套扩来（+渲染预设·Qoder 评审漏件①）；知识库分两槽（主手裁定·Qoder 评审漏件②）。

## 二 挂载点参数化（切换位设计·只设计不实现）

**单一入口**：`vertical_profile.json`（建议落 `DATA/vertical/profile.json`·平台层对垂域的唯一引用入口）——**三挂载点**读它取垂域参数：

| 挂载点 | 现状散落位置 | 参数化后读 profile 的字段 |
|---|---|---|
| ① grounding 数据上下文 | 前端 buildContext 推送的图层摘要 | `data.presets_manifest` / `data.point_layers` |
| ② 身份卡查询 | kb_facts 的 `city='宜昌'` 硬编码 | `identity.kb_city` / `identity.facts_topic` |
| ③ 口径表引用 | K-C1 枚举散落（server+前端） | `caliber.community_scopes` |

结构草案（设计件·非实现）：

```json
{
  "vertical_id": "emotion_map_yichang",
  "city": "宜昌",
  "data":      { "presets_manifest": "DATA/boundaries/presets/manifest.json",
                 "point_layers": "core/geo_registry.py" },
  "knowledge": { "corpus_whitelist": ["ai_qa/outlet_kb/", "docs/urban-renewal-plan/"],
                 "paradigm": ["ai_qa/paradigm.py", "ai_qa/manifesto.py"] },
  "caliber":   { "registry": "_口径注册表.md", "community_scopes": [174, 154, 118, 130, 193] },
  "identity":  { "facts_topic": "EMC", "kb_city": "宜昌", "persona_ref": "dsh preset persona" },
  "tool_presets": { "default_layer": "yichang_l2_t1",
                    "trend_layers": { "T1": "yichang_l2_t1", "T2": "yichang_l2_t2", "T3": "yichang_l2_t3" } },
  "render":    { "schemes": ["community_choropleth_v1", "point_default_v1", "boundary_fill_v1"],
                 "ramps_subset": ["grid-warm", "red-3", "ylorrd"] }
}
```

**现状违例登记（切换位预留阶段的诚实账）**：平台层代码现有 400+ 处城市名硬编码（tools/core/api/frontend），已由 `tests/test_vertical_profile_boundary.py` baseline 封顶管理——**防新增·存量随垂域化清偿**（清偿顺序建议：工具预设（第 5 件·集中度最高）→ 身份卡 city → 投影 CRS → grounding 地图初值）。

## 三 共享不变量（互引 ACP 契约 v1.1 §六）

换垂域时必须零改动的五项：①ACP 事件语义 ②MCP 工具签名（18 件） ③渲染契约结构（spec 七段） ④治理字段 schema（status/lineage/X-01） ⑤四态出口契约——真身载体见 `docs/acp-contract-v1.md` §六。

**垂域②试点（城市体检医生 Agent）核心观察项**：试点要验证的就是上述五不变量在第二垂域上零改动——**有一项要改 = 抽象层划线错了·早发现早便宜**（试点串行于壳阶段收口后·任务书 v1.0 §四-2）。

## 四 审计门禁（grep 硬审计·可跑）

`tests/test_vertical_profile_boundary.py`（S9 随件测试）：
- **词表**：宜昌/yichang/西陵/伍家岗/点军/猇亭/夷陵（忽略大小写）；
- **平台层范围**：`core/` `tools/` `api/` `frontend/js/` `serve.py`（测试资产 test-*.js 豁免——测试数据用真实地名合理）；
- **断言**：命中文件集与每文件计数均不得超出 baseline（新文件/新增命中 = 测试失败并打印「新增违例清单：文件:行号:内容」）；
- **纪律**：baseline 只减不增（垂域化清偿时更新下调·禁止上调）。

---

> SHELL(S129) S9 · Qoder · 2026-08-23 · 垂域切换位预留（六件套+挂载点+不变量+审计）·zcode 审读收敛
