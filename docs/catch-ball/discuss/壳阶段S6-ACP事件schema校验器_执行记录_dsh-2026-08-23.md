# 壳阶段 S6 · ACP 事件 schema 校验器 · 执行记录（dsh · 2026-08-23）

> 派发：用户令（2026-08-23）——`壳阶段联合任务书v1.0` §二 S6「ACP 事件 schema 校验器（五族+provenance·pytest 桩）·C 短包·执行=dsh」（排期裁定：dsh 即刻可做 S6）。
> 权威源：`docs/acp-contract-v1.md`——本件按 **v1 骨架（commit 6737dfcc·PT-CB12(T2)）** 建；执行期间 zcode 落地 v1.1 增补（commit be30774a·SHELL(S129)·S2+S9+S1 三件批）——版本注记位方向与其完全一致（见 §三）。
> 分支 `EMC_harness_dsh`·commit 前缀 `SHELL(S6):`·零 pull 零 push。

---

## 〇 一句话结论

**S6 完成·定向 30 用例全绿**：五族事件（msg.delta/tool.begin/tool.end/error/approval.req）+ 三状态对象（session/turn/toolcall）的 JSON Schema（draft 2020-12）+ pytest 校验桩（齐全性/metaschema/合法样例通过/故坏样例字段级失败断言）落盘 `tests/acp_schema/`；S2 v1.1 增补未定稿——按用户依赖注记只按 v1 骨架建·版本注记位已预留（各 schema `$comment` + README §二 五条待补清单）。

---

## 一 交付清单

| 件 | 路径 | 说明 |
|---|---|---|
| 8 份 JSON Schema | `tests/acp_schema/schemas/*.schema.json` | 五族事件+三状态对象·draft 2020-12·`additionalProperties:false` 严格 envelope |
| 校验桩 | `tests/acp_schema/test_acp_schema.py` | 30 用例：齐全性(无孤儿)/metaschema/合法样例通过(8)/故坏样例字段级失败(21) |
| 版本注记位 | `tests/acp_schema/README.md` | §二 版本登记表：v1.1 待补 5 条增量 + 落地动作 |
| 依赖声明 | `requirements.txt` | `jsonschema>=4.0`（本机已装 4.26·双机重建可复现） |
| 本记录 | `docs/catch-ball/discuss/壳阶段S6-ACP事件schema校验器_执行记录_dsh-2026-08-23.md` | — |

---

## 二 设计要点（骨架级决策·留痕）

1. **严格 envelope·宽松 caliber 内层**：事件/状态对象外层 `additionalProperties:false`（故坏样例即考验此线）；`caliber` 内层 `additionalProperties:true`（v1 契约未定其内形·§5-2 载荷结构模式落地后收紧为必带 scale/refs——README §二 #2 登记）。
2. **opened_at 用 pattern 硬校验**：实测 jsonschema 的 `format: date-time` 检查依赖可选包 rfc3339-validator（未装即**静默跳过**·'yesterday' 能误过）——补 RFC3339 `pattern` 双保险（format 保留作元数据）。零新依赖。
3. **FormatChecker 开启**：校验桩统一走 `Draft202012Validator(schema, format_checker=FormatChecker())`——已支持 format 的字段强制校验（防静默跳过族）。
4. **错误字段级定位断言**：故坏样例断言 `field ∈ message 或 path`——防「错了但错在别的字段」的误过（R8.1 同律）。
5. **零新追踪 ID**：纯测试资产·不进 tracker 注册面（AGENTS 铁律 10 不适用·编号连续性零扰动）。

---

## 三 依赖注记执行（用户令原文落地）

> 「S2 的 v1.1 增补（kind 子类型/provenance/载荷结构）未定稿——先按 v1 骨架建·S2 落地后补 schema 增量（预留版本注记位）。」

- 本件**只按 v1 骨架**（契约 §二/§三·commit 6737dfcc）建 schema；
- 版本注记位 = 各 schema `$comment`（预留）+ README §二 版本登记表（5 条待补增量：provenance 诚实性标记 / tool.end 载荷结构模式 / followup_cue 载荷字段 / approval.req 接线注记 / S9 共享不变量清单的机器守护定位）；
- 执行期间 zcode 落地 v1.1（commit be30774a·SHELL(S129)）——本件只读未改契约·零冲突；实测预留的 5 条待补增量与 v1.1 定稿方向**四条全中**（provenance real|synthesized / 载荷结构模式+必带 caliber 摘要 / followup_cue 载荷字段 / approval.req kb_inbox 接线注记）·第 5 条为 §六 共享不变量清单（ACP 事件语义=五不变量之首）——**S2 已落地·schema 增量补件随时可排**（动作表 README §二 现成）。

---

## 四 门禁

| 项 | 结果 |
|---|---|
| 定向 `py -m pytest tests/acp_schema/ -q` | **30 passed** |
| 全量 `py -m pytest tests/ -q` | **554 passed + 2 skipped**（522+2 基线 + 本件 30 + 并行在途 2·不降·见注） |
| 追踪面 | 零新 ID·`validate_track_ids` 绿（含在全量内） |

> 注：全量数字随并行线在途件浮动——本件增量恒为 +30（8 合法样例 + 21 坏例 + 1 齐全性）。

---

## 五 纪律自查

- [x] 禁 emoji（schema/测试/记录全文无 emoji·中文标点与 ASCII 标记合规）
- [x] 零新追踪 ID（纯测试资产·未 @track·未 register）
- [x] 零 pull 零 push·显式路径 commit（tests/acp_schema/ + requirements.txt + 本记录·前缀 SHELL(S6):）
- [x] 契约只读未改（acp-contract-v1.md 权威源零触碰·v1.1 在途编辑未打扰）
- [x] 他组在途未触碰：docs/progress.md（M）、契约 v1.1 diff、PT-CB9R-A2B3 回收件等

---

## 六 待主手回收注记

1. **v1.1 落地后 schema 增量补件**：README §二 5 条待补清单·由主手随 S2 收口排（本件只留位不越位）。
2. **五族边界提醒**：契约 §二 表含 `proc.delta`（可选族·EMC 暂无）——本件按用户令五族范围建（proc.delta 未建 schema）·壳阶段若启用 proc.delta 需新加一族（README §三 新增流程已备）。
3. 契约 v1.1 若改动 **v1 骨架语义本身**（如五族列表/状态枚举变化）→ 本目录 schema 同步改（非增量）·以契约为准。

---

> dsh · 2026-08-23 · S6 交付 · 待主手 zcode 回收
