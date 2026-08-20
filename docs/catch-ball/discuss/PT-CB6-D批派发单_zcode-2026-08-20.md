# PT-CB6 · D 批打磨派发单（zcode 主手签发·2026-08-20）

> 派发方：zcode（主手）。执行：dsh（通用副手）。背景：Codex 全量审计四线通过（`PT-CB6-审计_Codex-2026-08-20.md`）·新增缺陷 D9-D13 经主手抽验全部成立·D9 主手裁决豁免。
> 本批 = 缺陷清单 D1-D4 + D10-D13 共 8 件（D5/D6-D8 已销·D9 豁免）。D10 着色语义规格由主手定稿（CB-41 双 bug 敏感区），dsh 按规格执行。
> 纪律：白名单制（见 §三）；零判裁（规格已定·按规格实现）；分支 `EMC_harness_dsh`；开工前 pull。

---

## 一、任务清单（8 件·按文件分组·可串行做）

### 组 A：`tools/mcp_server_emc.py`（D1/D2/D3/D4/D11·5 件）

| # | 任务 | 规格 | 验收 |
|---|---|---|---|
| D1 | zonal_stats/rank 增 `sort_by` 支持（P1） | 枚举扩 `sort_by: point_count\|polarity_index\|score_mean`（默认维持 polarity_index 向后兼容）；`point_count`=按件数降序（**不做**极性加权）；rank 同扩。测试：point_count 排序用例（真实小层）+ 默认行为零退化断言 | 新用例过；既有 zonal 用例全绿 |
| D2 | zonal_stats 描述增 layer_output 引导 | description 补一句：`layer_output=True 返回 geojson 可直接 render_spec 内联铺图（推荐用于出图链）` | grep 描述在位 |
| D3 | rag_query 描述差异化 | description 明确三点：策展来源（本地治理知识库）/检索维度（知识类非空间）/适用场景（口径·规则·背景问答·非空间分析） | grep 三要点在位 |
| D4 | main() stdout [OK] 行改 stderr | `print(..., file=sys.stderr)` 且保持 ASCII `[OK]`；协议纯度（stdout 仅 JSON-RPC 帧） | 代码审读；stdio 冒烟无多余 stdout 行（环境有 mcp 包则跑·无则记代码审读代验） |
| D11 | community_caliber 加 K-C1 校验（P2） | dataset 路：从 manifest note/口径注册表解析已知 scope（page7_12345_top10=154 派生·base_174=174）自动填 community 且与调用方声明不一致时**告警字段**返回；inline 路：值过 K-C1 枚举校验（174/154/118/193/130），非法值返回语义化 hint | 混配断言用例（174 声明在 154 层→告警字段可见） |

### 组 B：`frontend/js/render_client.js`（D10·1 件·规格主手定稿）

| # | 任务 | 规格（主手定稿·按此实现） | 验收 |
|---|---|---|---|
| D10 | choropleth 着色按 value_field 语义分派（P2） | `community_choropleth_v1` 分支：value_field ∈ polarity 系（polarity_index/polarity/score_mean 含 polarity 子串）→ 走 **`piToNorm` 极性归一 + `polarityStops('overall')`**（与 ai_qa 同源函数·禁自造）；其余 → 维持计数着色（`_normCommunityCount`+countStops）。**禁**：改默认 value_field；新引入第三种着色路径 | 渲染语义分派单测（或 e2e 采样）：polarity 字段→极性色带；count 字段→计数色带 |

### 组 C：`tools/demo_pioneer.py`（D12·1 件）

| # | 任务 | 规格 | 验收 |
|---|---|---|---|
| D12 | 演示脚本名实相符（P2） | D1 落地后：zonal_stats 显式 `sort_by=point_count`（件数口径）；若本批 D1 与 D12 同时完成则直接显式化。若 D1 未先行：脚本改名「12345情绪极性Top10（件数着色）」+注释待 D1 | 脚本重跑输出图名与数据口径一致 |

### 组 D：`api/render_routes.py`（D13·1 件）

| # | 任务 | 规格 | 验收 |
|---|---|---|---|
| D13 | 两处裸 print 改 _safe_print（P3） | `:68/:83` 改 `_safe_print(..., file=sys.stderr)` 形态（_safe_print 变体或等效）；消息保持 ASCII 标记 | grep 无裸 print |

## 二、白名单

- 允许触碰：`tools/mcp_server_emc.py`、`frontend/js/render_client.js`、`tools/demo_pioneer.py`、`api/render_routes.py`、`tests/test_usage_guard.py` 或新增 `tests/test_d_batch.py`（D1/D11 用例）、本派发单执行记录（落盘 `docs/catch-ball/discuss/PT-CB6-D批执行记录_dsh-2026-08-20.md`）。
- **禁碰**：main、tool_contracts.py、ai_qa/paradigm.py、口径注册表、frontend/js/toolbox/shared.js（D10 只调用同源函数不修改它）。
- git：只 add 上述文件；commit 前缀 `PT-CB6(D):`；push origin 分支。

## 三、纪律与验收标准

1. 门禁：全量 `py -m pytest tests/ -q` = **427 passed + 2 skipped**；新增测试上浮须在执行记录注明。
2. JS 改动 `node --check` 过；Python 改动 `py -m py_compile` 过。
3. ASCII 标记、`_safe_print`、无 emoji；追踪 ID 零新增（本批不改注册表——D9 豁免无需动）。
4. D11 校验逻辑禁 LLM 调用（纯规则查表·闭包）。
5. 全部完成或按组提交均可（组间独立）；每组完成即 commit，避免大杂烩。

## 四、主手已裁决与挂账（dsh 勿动）

- **D9 豁免**：F_029 高频 1s 扫描免 @track——与 field_dictionary「热路径 helper 不 track」既有惯例一致；主手将固化纪律条款（tracker 纪律：高频循环扫描类免埋点·注册表描述注明）。
- notes 顺修挂账（不在本批）：A9 fail-open 收窄 / inbox TTL 补偿 / _count_norm 抽公共函数 / dataset 字段白名单 / K-C1 补 118 行 / demo 点层 preset 注册裁决。

---
> dsh 交付后主手回收抽验（重点：D10 着色分派是否严格走同源函数、D11 混配断言、D1 默认零退化）。随后与 Q3/Q4 用户复测一并收口。
