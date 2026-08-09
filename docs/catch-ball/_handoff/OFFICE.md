# 办公室 · 工作交接卡

> **位置**：办公室 | **最后更新**：2026-08-11（从家续做） | **操作人**：claude组（Claude Code）
> **同步**：家 08-10 收工已 push（`6431465`）·**到公司 git pull 即可看到全部进度**。

## 今日（08-11）待做（公司续做·CB-22d 后续 + RAG 遗留）

### CB-22d 地图标记·后续项（准确度 + 防护·家已完成路径跑通）

> **背景**：家 08-10 已闭环 CB-22d 路径跑通（追问「能在地图上标记项目位置吗」→ 出图层 + 未命中诚实文字 + 不挂起·用户实测成功·两组复验通过·commit `ace4f8f`）。**本卡列的是「准确度后续完善」+「防护补全」**。

- [ ] **准确度完善**（用户明确「准确度后续完善」·家未做）：
  - [ ] `_core_entities` 多实体返全候选（红星路-二马路→[红星路,二马路]·防丢二马路）
  - [ ] jieba 自定义词典（`jieba.load_userdict`·加宜昌地名：葛洲坝/三峡/二马路/大南门·防专名被拆：三峡青年城→[青年城]）
  - [ ] 「老城中心」泛词入 `_AGGREGATE_WORDS` / `_ZONE_SUFFIXES`（实测误导命中「中心人民医院」）
  - [ ] amap 命中置信标注「高德解析·大致位置」（source='amap' score 恒 0·无置信档·防用户误读高精度）
- [ ] **finalStep 失败兜底**（P0-2-3·Codex/glm 建议）：复用 `_composeDegradedConclusion`·治「部分命中→finalStep 45s 超时」卡顿·兑现「任何情况必收尾」
- [ ] **A1 GIS 甄别增强**：generate_point_layer 优先查 GIS 体检图层要素（停车泊位缺口.小区名/危旧房.住宅名·真实坐标·最高置信）——家已取证（`{URENEWAL_ROOT}/3_gis数据` 2 GDB 31 图层·pyogrio 可读）
- [ ] **tier-2 面化**：片区名未命中 POI → 行政区/街道面 + 名称标注（葛洲坝→西陵区面）
- [ ] **A3 项目库坐标**（P1）：附件5 docx → geocode → 项目点位源（聚合名「污水厂网一体示范区」最终解）
- [ ] **B3 飞轮用例**：知识问答→追问标记→断言标记+<30s+0 挂起·行为级测试（stub 全未命中→B1 出口·stub 部分命中→落图）

### RAG 遗留（08-09 OFFICE 卡·未完成）

- [ ] **B 路径（CB-22b·query_knowledge_base 确定性查询）**——RAG_QUERY_KW 临时结构化词待迁移
- [ ] **混合检索**（P1）：fact 加权或 Top-5 保底 ≥1 fact·降 note 占比
- [ ] **全仓 `[中文]+类` 扫描 + 逐条核实源文档**
- [ ] **Recall@5 素材质量机制**（黄金集 Recall≥80%）
- [ ] **P0-6 分通道 tier 复审**（暂缓·路径跑顺后勿忘）
- [ ] **L2 出向任务**（outlet_kb 接入运行时·进 CB 讨论）

## 公司环境准备（08-11 到岗）

1. `git pull`（拉家 08-10 进度·`6431465`）
2. **装 RAG 依赖**（若未装）：`pip install -r requirements-rag.txt`（torch +cpu 需阿里云镜像 `mirrors.aliyun.com/pytorch-wheels/cpu`）·BGE 模型 HF 镜像·`py tools/rag_index.py --build`
3. **rapidfuzz/pypinyin/jieba**（CB-22d A0 依赖·家已装·公司若缺补 `pip install rapidfuzz pypinyin`）
4. **G 盘资料库**：`G:\OneDrive\2026\15_城市更新专项规划研究\`（GIS 数据 + 附件5 项目库在 `1 宜昌市城市体检/3-附件/`）

## 关键文件速查

| 看什么 | 路径 |
|------|------|
| CB 入口 | `docs/catch-ball/_cb-index.md` |
| CB 轨迹 | `docs/catch-ball/cb-journal.md`（CB-22d 最新·路径跑通闭环） |
| CB-22d 定稿 | `docs/catch-ball/discuss/CB22d-地图标记失败_反评价收敛定稿_2026-08-10.md` |
| CB-22d 实施 | `docs/catch-ball/discuss/CB22d-地图标记路径跑通_实施复验发起_2026-08-10.md` |
| 地点信息源 | `docs/catch-ball/discuss/CB22d-地点信息源与实现路径管线_2026-08-10.md` |
| 家里进度 | `docs/catch-ball/_handoff/HOME.md` |
| todo 日志 | `docs/todo.md`（08-10 收工段） |
| revision-log | `docs/revision-log.md`（08-10 最新） |

## 关键 learning（家 08-10·防踩坑）

- **地点模糊搜索 = LLM 判意图 + 成熟 API（高德优先）+ 本地 jieba 兜底**（不造轮子·高德专利 CN104679801A：意图分层 + 分词 + 加权·非机械剥后缀）
- **聚合名/无地点描述 → 放弃**（像人思维·不能 while-loop 无限思考）——污水厂网一体示范区/其他项目归 unmatched
- **挂起根治 = 零命中零 LLM 确定性出口**（B1·不调 finalStep）·agentStep 30s 超时已有（api.js:34）·流式 token 输出已有（用户能看到思考）
- **names 拼接串要 split**（逗号/顿号/分号/空格）·冷加载 > 前端超时要放宽（5s→20s）
- **真实数据端到端实测**胜过静态复验（两组静态「通过」没拦住用户实测失败·教训）
