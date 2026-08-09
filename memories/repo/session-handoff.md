# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月10日凌晨（**CB-22d 地图标记路径跑通闭环 + 分支合并 fix/emc-buglog → main**）| 分支 `main` @ `7eee7c3`（与远程同步·工作区干净）
>
> 🔗 **CB 入口**：`docs/catch-ball/_cb-index.md`（**双阵营：claude组 开发主 + Codex/glm组 评估**）
> 🏠🏢 **换机卡片**：`docs/catch-ball/_handoff/HOME.md`（家）+ `OFFICE.md`（公司·08-10 续做）

## 当前节点：CB-22d 地图标记路径跑通闭环（用户实测成功·两组复验通过）

08-10 大轮（实测失败 → 三证合一根因 → 用户两想法 → 两组修正 → 根治实施 → 闭环）：

### 场景（用户复现）
问「宜昌市城市更新项目有哪些？」→ 知识问答文字回答 OK → 追问「能在地图上标记出这些项目的位置吗？」→ 首版全未匹配 + **停半途 7 分钟**（计时不结束）。

### 三证合一根因
- **trace（sess-19156）**：FC 选对 generate_point_layer ✓ · search_place 对片区名 0 命中 ✗ · 第二轮 LLM 挂起
- **用户提供 EMC 思考内容**：FC 完全理解意图 + names 提取 16 个 ✓ · 但 while-loop 反复权衡「要不要再调/request_upload/胶囊」不终止（铁证）
- **两组复验预判**：Codex（tier-2 面化未实现 + tier-1 无甄别）· glm（片区名落 tier-3 文字）

### 用户两想法（北极星·已落地）
1. **地点模糊搜索须 LLM 参与**·非纯算法硬匹配——业界做法 = 意图分层 + 分词 + 加权（高德专利 CN104679801A）·LLM 判意图 + 成熟 API（高德优先）+ 本地 jieba 兜底·**不造轮子**
2. **无法识别地点就放弃**·像人思维·不能 while-loop 无限思考——聚合名/无地点描述归 unmatched·零命中零 LLM 确定性出口

### 两组根因修正（claude 原根因被修正 + 补 3 层）
- **Codex**：挂起 = finalStep 单调用挂起（非 while-loop 重试·trace 无 F_002）·新增根因 C（names 拼接串被当单名）+ D（冷加载 12.4s > 5s 超时）+ 依赖（rapidfuzz/pypinyin 未装）
- **glm**：数据缺口 = 匹配入口未分词（POI 库有数据·完整 q 无 substring 命中）·补单轮超时·先验高德 API·**后续自我修正**（agentStep 超时其实已有·挂起源实为 finalStep·B1 才是根治）

### 实施（commit `ace4f8f`·路径跑通）
- **P0-0 前提**：names split（拼接串→逐名）+ 冷加载 20s + 装 rapidfuzz/pypinyin
- **P0-1 数据层**：高德 API 优先（`amap_first`）+ A0 jieba 分词双路（`_core_entities` + forward 双路·复用 `_match_score`）+ 聚合名放弃（`_isAggregate`·引号容忍）
- **P0-2 决策层**：**B1 零命中零 LLM 确定性出口**（不调 finalStep·像人放弃·根治挂起）
- **验证**：pytest 307 passed + 3 skipped 零回归 · validate_generate_point_layer 9 断言 · 路径跑通 8/9

### 闭环
- 两组复验均**判定通过**（Codex：B1 根治 + 8/9 输出 · glm：端到端实证 + 自我修正）
- 用户实测「**基本成功生成正确图层**」

## 分支合并（08-10 收尾）

- **fix/emc-buglog（368 提交）→ main** · merge commit `b77daef`（保留全部历史 + 本地 main `81784f0`）
- 推 origin main（`76124d6..b77daef`）· 删本地 + 远程 fix 分支
- **当前唯一分支 = main**（`7eee7c3`）· 工作区干净
- **到公司**：`git checkout main` + `git pull` + `git fetch --prune origin`（删过时 fix 引用）· 后续开发在 main

## 今日 commit（main）

| commit | 内容 | push |
|---|---|---|
| `7eee7c3` | 分支合并进度同步（todo/交接卡/revision-log/cb-journal） | ✅ |
| `b77daef` | merge fix/emc-buglog → main（368 提交·含 CB-22d 全链） | ✅ |
| `ace4f8f` | CB-22d 地图标记路径跑通根治（names split/冷加载/高德优先/A0 分词/聚合名放弃/B1 零 LLM） | ✅（在 fix 分支·已并入 main） |
| `6431465`/`037af19`/`8f8009b` | 08-10 收工 + 交接卡 + 日期修正 | ✅（已并入 main） |

## 关键架构（下会话须知道）

- **CB-22d 地图标记链路**（新定稿）：追问「标记到地图」→ FC 选 generate_point_layer（契约 when 诱导）→ names split → 高德优先（amap_first·成熟 API）→ 本地 jieba 兜底（`_core_entities` 分词双路·复用 `_match_score`）→ 聚合名放弃（`_isAggregate`·无地点不强匹配）→ 命中落橙色点位图层 / 未命中 B1 零 LLM 确定性文字出口（exit='answered'·不挂起）
- **地点信息源 5 层**：S1 GIS 体检图层（停车泊位缺口.小区名/危旧房.住宅名·真实坐标·最高置信·**未接入·A1 待做**）+ S2 本地 POI 库（4490 条）+ S3 高德 API 兜底 + S4 面 preset + S5 项目库坐标（P1）
- **出口三段式**（旧定稿仍生效）：观点先行 → 4 要点 → 行业接口参数
- **热点图定稿**（旧）：KDE 热力面主图 + Gi\* 显著聚集五档 + setTerrain 连续曲面
- **CB-22 三层架构**：知识问答通道（RAG→LLM 综合·禁图层）·意图判断归 LLM
- **trace 取证纪律**：根因分析先 `trace_query --stats`·跑测试带 session

## 【下一步】（用户定·公司 08-10 续做）

1. **CB-22d 后续项**（准确度 + 防护·用户确认「准确度后续完善」）：
   - 准确度：`_core_entities` 多实体返全候选（红星路-二马路→[红星路,二马路]）+ 宜昌地名自定义词典（jieba.load_userdict）+「老城中心」泛词入挡词表 + amap 置信标注「高德解析·大致位置」
   - **finalStep 失败兜底**（P0-2-3）：复用 `_composeDegradedConclusion`·治部分命中 finalStep 45s 超时卡顿
   - A1 GIS 甄别增强（最高置信·未接入）·tier-2 面化（葛洲坝→西陵区面）·A3 项目库坐标（附件5 docx）
   - B3 飞轮用例（知识问答→追问标记→断言标记+<30s）·行为级测试（stub 全未命中→B1·部分命中→落图）
2. **RAG 遗留**（OFFICE 卡）：B 路径 query_knowledge_base · 混合检索（fact 加权）· 全仓 [中文]+类 扫描 · Recall@5 · P0-6 复审

## 测试基建

- pytest：**307 passed + 3 skipped**（含 CB-22d 变更·零回归）
- validate：validate_generate_point_layer **9 断言**（契约/镜像/接线/B1 零 LLM 防回归）+ test_emc_template + validate_skill_params
- 路径跑通：模拟 9 名 → 8/9 有输出（葛洲坝片区/红星路/夷陵广场/达门船厂命中·污水厂网示范区/其他项目正确放弃）
- 前端语法：node --input-type=module --check（改动文件）
- 飞轮：`py tests/browser/flywheel_audit.py --batch B3`（带 `EMOTION_TRACE_SESSION=B3-<批>`）
- **自测前必须重启 serve**（`start.bat`）·否则跑旧代码

## CB 状态
- 当前：**CB-22d 路径跑通闭环**（实测失败 → 根治 → 两组复验通过 → 用户实测成功）
- **双阵营**：claude组（开发主）+ Codex + glm组（评估）
- 反评价轨迹：`docs/catch-ball/cb-journal.md` + `docs/catch-ball/discuss/CB22d-*`
- **CB 工作流提醒**：每阶段主动标注「已过 CB→继续推进」vs「需发两组 prompt」（用户会忘本轮是否过 CB）

## 红线 / 纪律（下会话守）

- **承重**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema / **`@track()` 签名 / `_TRACKING_REGISTRY` 格式** · finalStep D019 极瘦（`<3000B`·冻结模板加字）
- **不造轮子**：地点模糊搜索用成熟组件（jieba/rapidfuzz/pypinyin/高德 API）·不重写 `_match_score` 分层
- **出口抽象层**：不新增 LLM 阶段（撞 D019）·outlet 契约走 tool_contracts 单一源
- **CB 机制**：每轮工作进 CB（计划+实施都进）·评估方只读不 git（claude组 负责 git）·prompt 用代码块包裹·plan/草案也进 CB
- **数据红线**：改 DATA 需备份 + 用户确认
- **trace 取证**：根因分析先 `trace_query --stats`·推断只作假设
- **EMC 产物不临时创造样式**；不动 FC prompt；代码禁 emoji；print 走 `_safe_print`
- **改 Python 后重启 serve**；commit 后 push

## 恢复指引（新会话·换环境后）

1. `git checkout main` + `git pull` + `git fetch --prune origin`（拉 `7eee7c3`·删过时 fix 引用）。
2. 读本卡「关键架构」+「下一步」。
3. 读 `docs/todo.md` 08-10 段 + `docs/revision-log.md` §5 最新（含 CB-22d 条目）。
4. 读 `docs/catch-ball/_handoff/OFFICE.md`（公司续做卡·CB-22d 后续 + RAG 遗留）。
5. 读 CLAUDE.md「出口抽象层」顶层纲领节 + 「演示逻辑链」北极星。
6. 启动：`start.bat`（serve.py 自起后端 :8000 + 前端 :8080）。
7. 从「下一步」继续（核心 = CB-22d 后续准确度 + finalStep 兜底）。
