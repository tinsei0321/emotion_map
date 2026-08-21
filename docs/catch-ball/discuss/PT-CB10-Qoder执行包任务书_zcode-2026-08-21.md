# PT-CB10 · Qoder 执行包任务书（C1b + C2 + C5 合并）（zcode·2026-08-21）

> 签发：zcode（主手）。执行：**Qoder**（用户指定·替代原 Codex 派发）。性质：收口批执行包（三块合并·先定稿后执行）。
> 变更说明：原 C2+C5 派 Codex 之令撤销——本包统一交 Qoder；openPath 劫持修复已由主手方式 B 直改完成（22ac60c1·不在本包）。

---

## 〇 执行总纲

1. 环境：`cd D:/Github/emotion_map && git pull origin EMC_harness_dsh`（main 冻结）。
2. 三块可串行执行（C2 仓内 → C5 本机 → C1b 插件）；每块完成即记入执行记录。
3. 白名单总表（EMC 仓写入物仅执行记录一份）：见各块；git 由主手代提交（Qoder 不 push EMC 仓）。
4. 纪律：门禁 442+2 零退化（上浮注明）；规则七（双环境可复刻）；~/.dsh 操作先备份。

---

## 块一 · C2 挂账顺修（10 件·仓内为主）

| # | 项 | 规格（主手已定稿） | 文件 |
|---|---|---|---|
| C2-1 | A9 收窄 | `_reject_analysis_output` 宽 except fail-open → manifest 不可用时收窄「仅 preset 存在才判·其余显式 ok+拒绝语义」·禁静默 pass | tools/mcp_server_emc.py |
| C2-2 | inbox TTL | spec 消费后 applied/ 归档 + 7 天 TTL 清理（保留现机制） | api/render_routes.py |
| C2-3 | 公共函数 | `_count_norm` 归一与 shared.js buildZonalFc 同公式合一·单源 | frontend/js/render_client.js + toolbox/shared.js |
| C2-4 | 字段白名单 | dataset 端点属性白名单（名称/坐标/极性/领域/指标类）·禁办件编号等准标识 | api/render_routes.py |
| C2-5 | K-C1 补 118 | 口径注册表社区枚举补 118（12345 西陵+伍家岗聚合面·注派生） | docs/urban-renewal-plan/00-宜昌专项/_口径注册表.md |
| C2-6 | demo preset 注册 | 裁决=注册进 geo_registry 点层表·demo_pioneer 改注册引用 | core/geo_registry.py + tools/demo_pioneer.py |
| C2-7 | 白名单扩（与双模 P0+ 合并） | emc-analysis guard `EMC_TOOLS` 8→10 件（+emc_status+render_file）·POLICY 同步两句（8080 探测/显示到地图）·改前备份·复刻步骤入记录 | ~/.dsh/profiles/emc-analysis/ |
| C2-8 | D9 纪律固化 | tracker 纪律节：「高频循环扫描类（≥1s）免 @track·注册表描述注明」 | docs/（tracker 纪律节） |
| C2-9 | 待开发工具登记机制 | render-contract.md 增节：无权威工具时登记（工具名/场景/成本/优先级）→主手定期裁决 | docs/render-contract.md |
| C2-10 | 色板缺口登记机制 | 同上：受管色带不足时登记（场景/期望/理由）→裁决入词表 | docs/render-contract.md |

验收：各项有测试或实测；全量门禁 442+2（上浮注明）；C2-7 改后实跑 emc-analysis 冒烟。

## 块二 · C5 双模处置（4 件·本机 ~/.dsh）

| # | 项 | 规格（双模结局收敛定稿 v1.0） | 文件 |
|---|---|---|---|
| C5-1 | 研究档归档 | `profiles/emc-research` → `_retired-emc-research`（改名不删）·EMC_DUAL_MODE.md 记退役日期与复活法 | ~/.dsh/profiles/ |
| C5-2 | MODE_ESCALATION 改写 | guard 策略文本：从「use profile emc-research」改「引导用户到 3080 网页档」（研究深度需求） | emc-analysis-guard/index.mjs |
| C5-3 | 启动器瘦身 | dsh-emc.ps1：删研究关键词路由与 -Research 分支（或指向退役提示） | ~/.dsh/dsh-emc.ps1 |
| C5-4 | 说明文档改写 | EMC_DUAL_MODE.md 改单档说明+网页档指引（标题改「EMC 无头模式说明」） | ~/.dsh/EMC_DUAL_MODE.md |

验收：`dsh --profile emc-research` 预期报错（非静默）；`dsh --profile emc-analysis` 正常+9 工具；文档与实况一致；全部先备份到 `ptcb8-t7-backup-20260821/`。

## 块三 · C1b 会话归置（插件·仓内改）

| # | 项 | 规格（C1b 任务书） | 文件 |
|---|---|---|---|
| C1b-1 | 独立工作区归置 | 优先查找 id/name=`emc-lab` 工作区并 connect·会话开其下 | vendor/dsh-emc-entry/ |
| C1b-2 | 降级链 | emc-lab 不存在→实测编程创建（dsh 有无 createWorkspace API）→仍不行 fallback 当前+console.warn | 同上 |
| C1b-3 | 命名统一 | 会话标题统一 `[EMC] ` 前缀 | 同上 |
| C1b-4 | 可复刻 | emc-lab 创建步骤写入执行记录→M1 配方一节 | 执行记录 |

验收：点击入口→会话出现在 emc-lab（截图）·emotion_map 零新增；emc-lab 创建步骤可复刻。
注：openPath 劫持修复已由主手完成（不重复）；已堆积会话清理=主手另做（不派）。

## 执行记录要求

落盘 `docs/catch-ball/discuss/PT-CB10-Qoder执行包记录_Qoder-2026-08-21.md`：
三块逐项销号表 + C2-7/C5/C1b 的备份清单 + emc-lab 创建步骤 + 门禁输出 + 验收截图引用。**EMC 仓唯一新写入物·git 主手代提交。**

## 分派与回收

- Qoder 完成后停下等主手回收（逐项抽检+门禁复核+截图核对）。
- 收口批闭环后：claude 审计首用（审计任务书主手另签）。

---

> 批准（用户已指定 Qoder 执行）→ 本任务书即定稿。执行记录随批交付。
