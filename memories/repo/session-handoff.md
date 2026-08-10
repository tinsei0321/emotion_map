# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：08月10日 晚（office 环境·CB-22i 追问标记崩溃根因修复·完整链路实测通过·回家交接）| 分支 `main` @ `a27c0e2e`
>
> 🔗 **CB 入口**：`docs/catch-ball/_cb-index.md`（**双阵营：claude组 开发主 + Codex/glm组 评估**）
> 🏠🏢 **换机卡片**：`docs/catch-ball/_handoff/HOME.md`（家）+ `OFFICE.md`（公司·08-10 续做）

## 当前节点：CB-22i 追问标记崩溃根因修复（.slice bug·完整链路实测通过）

08-10 大轮（追问读秒卡住 → 三组四轮根因 → 最终定位前端 JS 崩溃）：

### 真实根因（最终定位）

- **追问标记「没反应」直接根因 = 前端 JS 崩溃**：`panel.js:1616 _distillTurn` extracted 回灌写 `JSON.parse(JSON.stringify(_ext)).slice(0, 5)`——`_ext` 是 **`{geo,attrs}` 对象·无 `.slice` 方法** → `PAGEERROR: JSON.parse(...).slice is not a function` → 追问消费 `priorTurn.extracted` 时链路崩（CB-22f 阶段3 引入）
- **Playwright 抓 console 定位**（浏览器 console 是前端崩溃的直接证据）
- **修**：对象属性限制（geo≤5·attrs≤8·深拷贝）·commit `a27c0e2e`

### 修复链（CB-22g/22h/22i 全记录）

| 轮 | 修复 | 结果 |
|---|---|---|
| CB-22g | F_018 改号（query_knowledge_base 撞 build_outlet_schema）+ FC 埋点 F_019 + stages.js:322 + 体检 RAG 整合（36→52 facts） | 315 passed |
| CB-22h | `_assembleKnowledgeQA` finalStep catch 降级 `_composeKnowledgeDegraded` + 墙钟 deadline + httpx 分段 + BGE 预热同步 | 316 passed·首问网络挂起 60s 收尾 |
| CB-22i | **`.slice` bug 修复（追问崩溃真凶）** + Timer 主动中断修正（覆盖 `client.stream()` __enter__ 等响应头·本地挂死 server 1.0s 中断）+ serve 反代 50s 超时 + 前端 Promise.race | **完整链路实测通过** |

### 完整链路验证（Playwright·真实 DeepSeek）

- 首问「宜昌市有哪些城市更新项目？」→ **11s 完成**（55 项目/51.33 亿 + 来源）
- 追问「能帮我把这些项目标记在地图上吗？」→ **7s 出图层「宜昌城市更新项目点位」**·0 挂起·PAGEERROR 消失

## 关键架构（下会话须知道）

- **追问标记链路**：首问知识问答（rag_search→finalStep·_assembleKnowledgeQA）→ 追问「标记」→ `_followupCue`/`_markupCue` 引导 → FC 选 generate_point_layer → names split → 高德优先 + jieba 兜底 → 落点位图层 / 未命中 B1 诚实文字
- **CB-22f 识别衔接**：fact meta 透传（region/topic/year/keywords）→ `ctx.extracted`（实体清单级）→ priorTurn 回灌 → `_followupCue` 分类器（8 场景 PASS）+ `_deterministicRecover` 扩 analyze/compare
- **流式超时三层兜底**：后端 LLM Timer 主动中断（`LLMClient.chat`·`_total_ttl`）→ serve 反代 50s Timer → 前端 fetch Promise.race（45s+5s）
- **降级兜底**：`_composeKnowledgeDegraded`（知识问答专属·列素材要点·skipped='rag-finalstep-degraded'）+ `_composeDegradedConclusion`（通用）
- **CLAUDE.md 铁律 13**：禁非专业概念创造·来源标注可读·不越维

## 【下一步】

1. **CB-22i 用户浏览器实测**（回家后）：强刷 Ctrl+Shift+R 完整链路（首问→追问标记出图层）·若仍异常抓 console PAGEERROR 发我
2. **CB-22f B3 飞轮实跑**（留后验证）·**动作链 2 步 demo**（标记→分析·Phase2·预载 L2-T1）
3. **CB-22f 遗留**：A1 GIS 甄别 / tier-2 面化 / A3 项目库坐标（G 盘重活·单独轮）·RAG 收尾已做（query_knowledge_base F_018 + fact 加权）

## 测试基建

- pytest：**316 passed + 3 skipped 零回归**
- validate：validate_generate_point_layer 9 + validate_knowledge_route 5 + validate_track_ids 2 + validate_paradigm_map 5 + validate_rag_material 9
- Playwright：`tests/browser/test_markup_chain_hm.py`（完整链路·首问+追问标记）+ `test_hang_degraded_hm.py`（挂起 45s 降级）+ `test_degraded_conclusion_hm.py`（N/M 选行）
- **自测前必须重启 serve**（`py frontend/serve.py 8080`·BGE 预热同步 ~15s）·否则跑旧代码
- 前端语法：`cat x.js | node --input-type=module --check`

## CB 状态

- 当前：**CB-22i 追问标记崩溃修复完成**（.slice bug·完整链路实测通过）·用户待浏览器实测
- 双阵营：claude组（开发主）+ Codex + glm组（评估）
- 反评价轨迹：`docs/catch-ball/cb-journal.md` + `docs/catch-ball/discuss/CB22{g,h,i}-*`
- **CB 工作流提醒**：每阶段主动标注「已过 CB→继续推进」vs「需发两组 prompt」

## 红线 / 纪律（下会话守）

- **承重**：diagnose prompt / harness orchestrate 主循环 / ChatRequest schema / `@track()` 签名 / `_TRACKING_REGISTRY` 格式 / finalStep D019 极瘦
- **不造轮子**：地点模糊搜索用成熟组件（jieba/rapidfuzz/pypinyin/高德 API）·复用 rag_search/_assembleKnowledgeQA/_composeDegradedConclusion
- **追踪编号连续**：新增公开函数须 `register_track_id`·先 grep 全仓（含 outlet_kb/）取现有最大 +1
- **CB 机制**：每轮工作进 CB·评估方只读不 git·prompt 用代码块包裹
- **trace 取证**：先核会话身份（PID 对照 wmic）+ 核 track ID 语义·不能凭计数推断
- **前端崩溃排查**：先抓浏览器 console PAGEERROR（`.slice` bug 教训）
- 代码禁 emoji·print 走 `_safe_print`

## 恢复指引（新会话·换环境后）

1. `git pull`（对齐远端 main）+ 读本卡
2. 读 `docs/catch-ball/_cb-index.md`（当前 CB-22i）+ `docs/todo.md` 08-10 段
3. 读 CLAUDE.md「出口抽象层」+「演示逻辑链」北极星
4. 启动：`py frontend/serve.py 8080`（BGE 预热同步 ~15s）
5. 从「下一步」继续（CB-22i 用户实测 + B3 飞轮 + 动作链 2 步 demo）
