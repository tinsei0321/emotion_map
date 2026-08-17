# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月18日 凌晨（**EMC×dsh 专题 R0-R9 全收敛预备·收工归档**·Codex·家·commit push 已授权）| 专题分支 `EMC_harness_dsh`·主线分支 `main`（CB-39 B/C 在途·本会话未动）
>
> CB 入口：`docs/catch-ball/_cb-index.md`
> 角色：**Codex = 主开发（唯一 git 写者）**·claude组 = 评估+收敛·zcode组 = 评估·**dsh组 = dsh 专题专项（08-16 晚重邀回归·仅该专题）**。
> 换机卡片：`_handoff/HOME.md`（家）+ `OFFICE.md`（公司）

---

## 当前节点：EMC×dsh 专题全线收敛预备 · 等用户拍板三组键 · office 晨间接续

### 一、专题线（分支 EMC_harness_dsh·R0-R9 完整链·台账为准）

1. **形态3（平台化）已过三组评审、零对抗分歧**——EMC 终局=领域平台（数据口径/知识范式/渲染契约/出口接口四类资产）；NL 路由层冻结为演示壳；对话智能交通用 harness 经 MCP。
2. **拍板包在盘待用户三键**：`discuss/EMC-形态3平台化_拍板包_Codex-2026-08-18.md`——①拍 E4（裁定文案+三前置：C11 三层可操作化/QA 冻结精确化/冻结≠放烂）②拍并轨排期（B1-B4/C 照旧→G8a 即行→G8b 挂 B1→G10 <1d→G1→渲染 API 1.5-2.5d→薄壳 2d）③答 dsh B 卷去留。
3. **外挂大脑轮（R9·朋友思路）已收敛**：`discuss/EMC-dsh外挂大脑链路_回应与收敛_Codex-2026-08-18.md`——D1 双定位·B 变体实验保留（转正五条件）/ D2 剩一问（**朋友成品是否存在**→评审或 dsh组 ACP 底新写 1-2d）/ D3 独立小轮。dsh 源码实测三前提全证实（ACP/headless/@Remote·Codex 抽验 3/3）。
4. **通俗收敛报告在盘**（应用户要求·四问结构）：`discuss/EMC-dsh合体讨论_通俗收敛报告_2026-08-18.md`——用户已读懂方向（「形态3 是我想要的」）。
5. 附带：B 卷①（嵌入位置谱系）事实底座已随 dsh 回应交付；②-⑤ dsh组 可即答。

### 二、主线（main 分支·本会话未操作·状态以 main git log 为准）

- CB-39 双线实施中：P0✅验证+A 线✅（本会话 08-16 完成·9 commit）→ **B 线治理（B1-B4）→ C 线沉淀（C1-C5）在途**（另会话推进·最后已知）。
- 基线（main）：366 passed + 3 skipped；门禁钉死 `py -m pytest tests/ -q`（禁裸 python）。
- CB-40 已收官（差距四维 80/30/≈30/65·G1>G5>G2·goal-status.md 每轮必更）。

### 三、office 晨间动作序（接手即做）

1. **E7 换绑**：office 机 `git remote set-url origin` → Gitee（首推令牌当密码）——家侧三远端已是 gitee 主+github 备+hub 枢纽。
2. `git fetch` 对账两分支：`EMC_harness_dsh`（专题文档+本收工 commit）与 `main`（B/C 线进度）。
3. **向用户要三组拍板**（按优先序）：E4 形态3 三键 → 外挂大脑两键 →（可选）dsh B 卷②-⑤ 补答指令。
4. 拍板后出 **CB-41 实施计划**：首批=G8a 静态派生（零风险可即行）+ main 在途 B/C 续推；先验后推照旧。

### 四、待用户挂起项（勿催·在场时提）

- key 轮换（AMAP+DeepSeek·用户暂缓；AMAP 新 key 记得勾 geocode/geo 服务）
- G1 前置②「城市体检指定项」表清单（C 线收尾时提）
- 时间轴专题轮（D3 冻结·等用户开）

---

## 关键架构（下会话须知道·承重）

- **形态3 若拍板生效**：路由层冻结（只修演示阻断 bug）·四类资产=平台本体·G8+G10+M2 三合一管道（contracts→动态 schema→MCP）·渲染 spec「令牌+解析副本」双载防双源（解析权威留 JS）·薄壳 v0 单轮 FC（多轮 loop=踩 M1/M3 停投边界）
- **外挂大脑链路**（若转正）：大脑端口契约（EMC 定义·dsh 第一驱动）·ACP 系路线（非 Web Host 插件）·C12 十条控制面条款·G10 须经 dsh profile 全局 MCP 配置接入（ACP 会话拒挂外部 server·实测）
- **数据池三分**（DATA/README 单源）·铁律7（片区=结论）·蒸馏源纪律·追踪编号连续（MOD_AIQA.F 从 F_020 起）
- 守卫已通电：9 validate_* 进 pytest·使用 ID⊆注册表闸门·SKILL_DEFS 真身解析

## 红线 / 纪律

- diagnose prompt 永不动（冻结）·编排器确定性（冻结期维持）·契约单一源·四态出口
- 时间轴 manifest 生成须用户授权；sim 禁入·gdb 只读；密钥只输出 key 名
- 术语统一「街办」（识别字典超集并存）；交付物全中文；专业词+通俗解释（**用户已两次要求通俗讲解——技术内容须配白话**）
- CB 工作流：评估方只读+禁 git+落盘 discuss/；每轮收敛必更 _cb-index+cb-journal+goal-status（DoD 三件）

## 恢复指引（新会话·office）

1. E7 换绑 → fetch 两分支 → `git log -5` 对账
2. 读本卡 + `EMC-dsh整体合体_讨论过程台账.md`（R0-R9）+ 拍板包 + 外挂大脑收敛
3. 从「office 晨间动作序」第 3 步继续（向用户要拍板）

> 专题文件全集：台账（R0-R9）· 纪要 · 拍板包 · 通俗报告 · 外挂大脑×6（发起/三回应/收敛）· R1 三回应 · 评估与发起——均在 `docs/catch-ball/discuss/`。
