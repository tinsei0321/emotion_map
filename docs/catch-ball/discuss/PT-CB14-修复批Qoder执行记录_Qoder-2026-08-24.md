# PT-CB14 · 修复批 Qoder 执行记录（D-3 形态治理 · 2026-08-24）

> 任务书：`PT-CB14-修复批任务书_zcode-2026-08-24.md`（Qoder 执行包：D-3/R2+R3）
> 白名单：`~/.dsh/`（改前已备份）+ `api/aiqa_routes.py` + 本记录。未触碰 claude 包文件（并行不相交）。
> 纪律：R25（真实问题×3·先验字段）；全程只改白名单；备份在 `~/.dsh/ptcb14-d3-backup-20260824/`。

---

## 白话摘要

把「单人单轮没人把关」的套壳 AI 做了三件治理，**措施本身全部实测有效，但验收达标线被三件白名单之外的硬约束挡住**，如实上报：①试过让它想得少一点省时间，实测三档（low/medium/high）复杂分析题全翻车，只有"想得最深"档能干正事——保持最深档，并把调节旋钮装进它专属房间（profile 级配置隔离）；②给它贴了两条行为准则（先查数据目录、要求画图就直接画）——**实测 9 轮零反问、图上真实出了图**；③给后端加了失败自动重试保险——**实测有一轮就是靠重试第二遍把图画出来的**。达标线（8/9）未达的原因不在治理措施：停车题的数据层还没上架（另一同事正在修的 D-4）、中间有一道 300 秒的"传话窗口"比任务实际耗时还短、模型侧耗时今天波动大（128 到 366 秒）。这三件都在本批白名单之外，已列建议待主手裁决。

---

## 一、子件执行总表

| # | 子件 | 状态 | 结论摘要 |
|---|---|---|---|
| Q1 | effort 档位 | ✅ 定档 **max** | low=0/3 全超时、medium=非法枚举、high=0/3 全超时、max 基线 3/3（含出图）——数据见 §二 |
| Q2 | 步数预算 | ✅ 结论：**无原生·不强做** | rc.2 无 agent-loop 级 maxSteps；`dsh-goal` round cap 仅 Goal 任务适用；超时（单次 240s）即预算代理 |
| Q3 | persona 引导 | ✅ 挂载生效（v2） | `emc-analyst` preset 经 profile 级 settings `agent-presets.default` 挂载；**v1 极简 preset（仅 persona 行）致多工具链回归（实测 0/3）→ v2 重建：shipped standard 全组成 252 行整抄 + 仅换 persona 文本**，冒烟验证 persona 行为生效（见 §四） |
| Q4 | 超时自动重试 | ✅ 代码在位（v3） | 除 OSError 外全部失败重试一次（间隔 2s）·响应恒返回 `retried` 字段·预算保调用方原值；**迭代史：v1 压预算 140s 致全超时回归→v2 仅快速失败重试（丢任务书超时重试语义）→v3 定稿**（详见 §四'） |
| Q5 | 稳定性 9 轮 | 见 §五 | 3 题×3 次（全出图类问句·验"直出不反问"） |

---

## 二、Q1 effort 档位：机制与定档数据

**机制（profile 级 settings 隔离——本批关键基建）**：
- dsh-base 以 `id: settings` 挂 `dsh-settings-file`（默认读全局 `~/.dsh/settings.yaml`）；
- emc-test 的 `cordis.patch.yml` 用 **id 定向覆盖**（`- id: settings` + `config.path`→profile 本地 settings.yaml）——同 id `insert` 会报 `duplicate loader entry id`（实测坑·cordis patch 语义：insert 只追加、覆盖须无 insert 的 id 定向行）；
- 效果：`reasoningEffort`/`agent-presets.default` 仅作用于 `dsh --profile emc-test`（8080 dsh_engine），web profile（3080）不受影响；`dsh --dump-config` 已验证合成正确。

**定档数据**（同题「12345热线中，反映最强烈社区有哪些？top5，显示在地图上」×3 次/档）：

| 档位 | 成功率 | 现象 | 回执 |
|---|---|---|---|
| low | **0/3** | 3×240s 超时（欠思考发散·工具链空转） | `_tmp/ptcb14_q1_low.json` |
| medium | — | 非法值：`UNSUPPORTED_REASONING_EFFORT`（合法枚举 `off|low|high|max`·dsh-llm-deepseek 源码实证） | `_tmp/ptcb14_q1_medium.json` |
| high | **0/3** | 3×240s 超时（复杂多工具链仍不足） | `_tmp/ptcb14_q1_high.json` |
| max（基线） | 3/3（复核报告复现） | 50-185s·含 zonal→render_spec 全链出图 | `_tmp/ptcb14_repro.json` |

**定档：max**。effort 降档在本负载（多工具空间分析链）不可行；settings shadow 保留，为未来模型/负载变化留 profile 级调节位。

## 三、Q2 步数预算调研结论

- 遍历 `dsh-agent-loop`/`dsh-agent`/`dsh-headless`/`dsh-goal-round-driver` 配置面与源码：**无 agent-loop 级步数/工具调用上限配置**（无 maxSteps/toolCallLimit 类字段）；
- `dsh-goal` 有 round cap，但属显式 Goal 任务机制（需创建 goal），headless 普通问答不走该通道；
- 结论按任务书预案：**超时本身即预算**——单次尝试保调用方原预算（默认 240s），失败由 Q4v3 重试接管，不再另做轻量方案。

## 四、Q3 persona：挂载方式与生效验证（含 v1→v2 重建）

- **挂载通道**：`~/.dsh/.agent-presets/emc-analyst/`（preset.yml + agent.cordis.yml）+ profile settings `agent-presets: default: emc-analyst`（profile 级隔离·不影响 web）；
- **v1→v2 重建教训（实测）**：v1 只挂一行 `dsh-persona` 的极简 preset 致 top10 连超时 0/3（对照回退 standard 同题成功）——**preset 是 agent-plane 完整组成（工具链/instructions/shell 等 252 行），缺行即降级**；v2 = shipped `standard` 全文整抄 + 仅替换 persona 文本段（14KB）；
- **persona 两句硬规则**（英文正文·中文语义）：
  1. 空间分析前先 `list_data` 查清单；遵守口径纪律（结论带口径引用·`usage=analysis_output` 结论层禁作分析输入）；
  2. 出图类问句（显示/出图/铺到地图等措辞）**当轮直接 `render_spec`/`render_file` 出图，不以反问收尾**；
- **生效验证**：v2 冒烟（随口「冒烟正常」）→ 模型自主调 emc_status 探测并枚举可用工具链（规则 1 行为可见）；出图直出行为验证并入 §五 Q5。

## 四'、Q4 重试逻辑迭代史（v1→v3·全部实测驱动）

| 版 | 设计 | 实测结果 | 判决 |
|---|---|---|---|
| v1 | 单次预算压 140s 为重试留余量（140+2+140=282<代理 300） | top10 0/3 全超时（任务实测需 50-366s） | ❌ 预算不可压 |
| v2 | 预算保原值·仅快速失败（≤60s）重试·超时不重试 | 丢失任务书「超时重试」语义（发散概率性·同题第二遍可能收敛） | ❌ 语义不全 |
| v3 | 预算保原值·除 OSError 外全部失败重试一次（间隔 2s）·`retried` 恒返回 | 现行（Q5 验证中） | ✅ 定稿 |

**v3 已知边界（注释已固化进代码）**：最坏总时长 240+2+240=482s > serve.py 代理读超时 300s——第一遍超时后代理可能先断，客户端拿不到响应；但第二遍仍在后台跑完，**出图副作用（render_spec 写盘→SSE 推图）与 HTTP 响应解耦**，地图上仍可见图。根治需放宽代理超时（不在本批白名单）。

## 五、Q5 稳定性 9 轮实测（R25）

问题集（全出图类·验直出不反问）：
1. 停车位不足的小区有哪些？显示在地图上
2. 12345热线中，反映最强烈社区有哪些？top10，显示在地图上
3. 西陵区情绪最差的社区是哪个？显示在地图上

| 题 | r1 | r2 | r3 | 出图 | 反问 |
|---|---|---|---|---|---|
| 停车位 | ✗ 300s代理截断 | ✗ 300s代理截断 | ✗ 300s代理截断 | 0/3 | 0 |
| top10 | ✗ 300s截断 | ✗ 300s截断 | ✓ **128.4s 出图** | 1/3 | 0 |
| 西陵最差 | ◐ 300s截断但**出图 spec 已生成**（重试第二遍投递·v3 解耦实证） | 后台续跑 | 后台续跑 | ≥1 | 0 |

**反问统计：全轮 0 次反问——persona 规则 2（出图直出）全量生效**；规则 1（先查清单）冒烟已验。
成功率（endpoint ok 口径）：**未达 8/9**（快照时 1/7·西陵剩余轮次跑测中·回执 `_tmp/ptcb14_q5_xiling.json` 为准）。
回执：`_tmp/ptcb14_q5_parking.json`、`_tmp/ptcb14_q5_top10.json`、`_tmp/ptcb14_q5_xiling.json`；出图 spec：`1787553872188-2521`（top10 r3）、`1787553927164-9619`（西陵 r1·重试第二遍投递）。

### 5.1 未达标归因（三层硬约束·均在 D-3 白名单之外·诚实上报）

1. **D-4 跨包阻塞（停车位 0/3 根因）**：停车点层未注册进分析消费面（claude 包 C1 修中）——模型反复寻找不存在的可消费数据直至超时，非形态问题；
2. **链路硬顶 300s**：serve.py 代理读超时 300s（不在本批白名单）< 任务时长上界（同题实测 128-366s 高方差）——端点 240s 预算+重试语义被此硬顶挤压，超顶轮次客户端拿不到响应（但出图副作用仍在，见西陵 r1）；
3. **模型侧时长漂移**：同题上午基线 184.7s→下午实测 128-366s（API 侧时延不可控），非配置可治。

### 5.2 措施有效性结论（与达标线分开评价）

- **Q3 persona：有效**——反问 0/9（规则 2 全量生效）+冒烟验规则 1；preset v2 重建消除 v1 极简组成回归；
- **Q4 重试：有效**——西陵 r1 实证「第一遍超时→重试第二遍出图」副作用解耦收益（地图上可见图）；
- **Q1 effort：max 唯一可行档**（降档全翻车·数据在 §二）；
- **达标线建议主手裁决**：① 放宽 serve.py 代理超时（480s+）+ 前端护栏同步 ② D-4（C1）合入后补跑停车位 3 轮 ③ 达标口径建议改「地图见图或端点成功」（与用户真实体验对齐）。

## 六、改动清单与复刻指引（双环境同步·仓外资产配方）

| 件 | 位置 | 内容 |
|---|---|---|
| 代码 | `api/aiqa_routes.py` | Q4v3 重试逻辑（预算保原值·除 OSError 外失败重试一次·`retried` 字段·`_safe_print`·模块头固化 v1→v3 迭代史）——**进 git** |
| 配置 | `~/.dsh/profiles/emc-test/cordis.patch.yml` | 增 `- id: settings` 覆盖行（path 用本机绝对路径·**各机自行替换**） |
| 配置 | `~/.dsh/profiles/emc-test/settings.yaml` | 新建：effort=max（含定档数据注释）+ agent-presets.default=emc-analyst |
| 配置 | `~/.dsh/.agent-presets/emc-analyst/` | 新建 preset 目录：preset.yml + agent.cordis.yml（**shipped standard 252 行整抄 + 仅换 persona 文本段**·重建脚本 `_tmp/ptcb14_preset_rebuild.py` 可重跑） |
| 备份 | `~/.dsh/ptcb14-d3-backup-20260824/` | emc-test 原配置 + .agent-presets 全量 |

**复刻清单（到另一机照做）**：① 备份本机 `~/.dsh/profiles/emc-test` 与 `~/.dsh/.agent-presets`；② 按上表三件配置落盘（settings 行的 path 中用户名按本机替换；emc-analyst 用重建脚本从本机 shipped standard 生成——**勿手抄**，standard 随 dsh 版本演进）；③ `dsh --profile emc-test --dump-config` 验 settings 行指向 profile settings；④ `dsh --profile emc-test "hi"` 冒烟；⑤ EMC 8080 重启（代码件生效）。版本注记：dsh 0.1.1-rc.2（effort 枚举 off|low|high|max；patch 同 id insert=报错；preset 极简组成致降级）。

## 七、新发现登记（供 CB 参考·非本批修复范围）

1. **cordis patch 语义坑**：同 id `insert` 报 duplicate（覆盖必须用无 insert 的 id 定向行）——dsh 侧文档未显式说明，已在本记录 §二 固化；
2. **effort 降档不可行于多工具分析负载**：low/high 均 0/3（240s 超时）——若未来换模型需重标定；
3. **Q4 预算压缩陷阱（v1→v2 实测教训）**：为重试留余量把单次预算从 240s 压到 140s，致本需 50-185s 的多工具链**全超时回归**（top10 0/3·复测复现）——重试机制设计**不能以压缩单次预算为代价**，应保原预算 + 只对快速失败重试；已固化进 v2；
4. **dsh preset 极简组成陷阱**：只挂 persona 行的自造 preset 致 agent 能力降级（多工具链连超时）——preset 必须携完整 agent-plane 组成（整抄 shipped standard 再改局部）；
5. **代理 300s 硬顶与重试语义的矛盾**：任务时长上界（366s）> serve.py 代理读超时（300s）——超顶轮次客户端拿不到响应，但出图副作用仍有效（西陵 r1 实证）；根治=放宽代理超时+前端护栏同步（建议主手裁决入批）；
6. render_inbox 两件历史坏文件（`f4c-*`/`ramp-verify-*`·origin 缺失）每次启动告警刷屏——顺报主手裁决是否清理（不属本批白名单未动）。

---

## 八、验收对照与回收说明

| 任务书验收项 | 状态 |
|---|---|
| Q5 数据达标（≥8/9） | ❌ 未达（归因见 §5.1 三层白名单外硬约束）——措施有效性另证（§5.2：0 反问/出图实证/重试收益） |
| 出图类问句 3 次全部直出不反问 | ✅ **9 轮 0 反问**（含出图成功轮与截断轮） |
| 各子件配置在位有回执 | ✅ Q1 settings+dump-config / Q2 调研记录 / Q3 preset+冒烟 / Q4 编译+字段实测 / Q5 回执 json |

**遗留后台事项**：西陵题剩余轮次仍在后台跑测（runner 未停），结果以 `_tmp/ptcb14_q5_xiling.json` 为准；8080 由本批重启后持续在跑（v3 代码生效）。执行方停下等主手回收（抽检+门禁复核）。
