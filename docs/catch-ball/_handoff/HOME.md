# 家里 · 工作交接卡

> **位置**：家 | **最后更新**：2026-08-17 早（**收工**·EMC×dsh 合体讨论 R0-R3·zcode组） | **同步**：分支已推 origin(gitee)+github+hub。**到公司读 `OFFICE.md` + `discuss/EMC-dsh整体合体_讨论过程台账.md`**。

## 收工快照（08-16 晚~08-17 早 · EMC×dsh 合体讨论 · 分支 `EMC_harness_dsh`·已推三远端）

- **R0** zcode 评估发起：用户设想「情绪地图整体寄生进 dsh」→ 拆方案A（整体寄生·六维反对）/方案B（工具级寄生·MCP）·发起稿落盘+三组 prompt 交用户投递。
- **R1** 三组回应全回收：**D1 否决A / D2 立项B+spike / D3 MCP 唯一解（dsh 原生 MCP 客户端实锤）/ D4 dsh组回归——四决策点三组全一致**，待用户拍板。
- **R2** 澄清轮：方案B 提升三层+核心改变（可达性与安全性·非能力新增）+四条诚实边界。
- **R3** **纠偏轮（本轮最重要）**：用户指出真痛点 = **EMC 入口聪明度不足**（意图→方法+工具路径不聪明·拆东墙补西墙）。zcode 机理：四层叠加（封闭分类法/单发诊断不可恢复/参数闭卷/eval 失真）；reframe = **灵活性归还入口端非中间开放**。**讨论稿落盘：`discuss/EMC-聪明路径_入口端灵活性_讨论稿_zcode-2026-08-17.md`**（四机制 M4→M2→M1→M3 + 决策点 E1-E3·M2 红线兼容关键=走 schema 侧不走 prompt 侧）。
- **office 待做（按用户指令）**：① 用户拍板 D1-D4（A/B/G10 线）；② 拍板 E1-E3（聪明路径线·是否并入底稿专题会话）；③ 两线收敛后统一出总优先级表（G1-G5+G6-G10+M 系）。
- **接手入口**：`discuss/EMC-dsh整体合体_讨论过程台账.md`（活文档·R0-R3 全记录·含文件清单与立场对照）。main 上 CB-39 B/C 线不受影响（本分支纯文档·未合并）。
- 双环境续法：office `git fetch && git checkout EMC_harness_dsh`（origin=gitee 可达）→ 读台账 → 按用户指令推进。

## 历史状态（08-10 收工 · CB-22d 闭环 · 分支已合并 main）

- **分支**：`main` @ `b77daef`（**fix/emc-buglog 已合并入 main·分支已删**·本地 = 远程 = main·工作区干净）
- **CB-22d 知识问答→地图标记**：路径跑通闭环（用户实测「基本成功生成正确图层」·两组复验均通过）
  - 根因：三证合一（trace + 用户思考内容 + 两组复验）·用户两想法（LLM 参与模糊搜索 / 放弃不可识别·像人思维）
  - 实施（`ace4f8f`）：names split + 冷加载20s + rapidfuzz/pypinyin装 + 高德优先(amap_first) + A0 jieba分词双路 + 聚合名放弃(_isAggregate) + **B1 零命中零LLM出口（根治挂起）**
  - 307 passed 零回归 · validate 9 断言 · 路径跑通 8/9
- **公司待做（08-10 上午·详见 OFFICE.md）**：到公司 `git pull` + `git fetch --prune origin`（拉 main·删 fix 引用）→ CB-22d 后续（准确度多实体/宜昌词典/finalStep兜底/A1 GIS/A2面化/A3项目库/B3用例）+ RAG 遗留（B路径/混合检索/全仓扫描/Recall@5）
- **另两组同步**：Codex/glm 只读本地不 git·claude 已 push main·它们读本地 main 即最新（勿用 fix 分支路径）
- **接手文档**：`OFFICE.md`（08-10 公司续做卡）+ `DEEPSEEK_ONBOARDING_2026-07-30.md`（历史）

## 家环境已就绪（08-09/08-10）

- ✅ RAG 链：依赖（torch 2.13.0+cpu 阿里云镜像）+ BGE 模型 + 索引 235 条 + 检索冒烟
- ✅ AMAP_KEY 已补（历史会话找回·高德 API status=1 有效）
- ✅ 双环境路径：`_PATHS.md` 家庭 `C:\Users\Hi\OneDrive\2026\15_城市更新专项规划研究`（878 文件）
- ✅ rapidfuzz/pypinyin/jieba 全装（CB-22d A0 分词双路依赖）

## 关键文件速查

| 看什么 | 路径 |
|------|------|
| CB 入口 | `docs/catch-ball/_cb-index.md` |
| CB 轨迹 | `docs/catch-ball/cb-journal.md`（CB-22d 最新·路径跑通闭环） |
| CB-22d 定稿 | `docs/catch-ball/discuss/CB22d-地图标记失败_反评价收敛定稿_2026-08-10.md` |
| 公司续做 | `docs/catch-ball/_handoff/OFFICE.md`（08-10 卡） |
| todo 日志 | `docs/todo.md`（08-10 收工段） |
| revision-log | `docs/revision-log.md`（08-10 最新） |
| 记忆索引 | `~/.claude/projects/d--Github-emotion-map/memory/MEMORY.md` |
