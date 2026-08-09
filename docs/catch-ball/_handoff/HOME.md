# 家里 · 工作交接卡

> **位置**：家 | **最后更新**：2026-08-10（收工） | **操作人**：claude组（Claude Code）
> **同步**：git push 后办公室可见。**到公司读 `OFFICE.md`**（08-10 公司续做卡·最新）。

## 当前状态（08-10 收工 · CB-22d 地图标记路径跑通闭环）

- **分支**：`fix/emc-buglog` @ `6431465`（与 origin 同步·工作区干净）
- **CB-22d 知识问答→地图标记**：路径跑通闭环（用户实测「基本成功生成正确图层」·两组复验均通过）
  - 根因：三证合一（trace + 用户思考内容 + 两组复验）·用户两想法（LLM 参与模糊搜索 / 放弃不可识别·像人思维）
  - 实施（`ace4f8f`）：names split + 冷加载20s + rapidfuzz/pypinyin装 + 高德优先(amap_first) + A0 jieba分词双路 + 聚合名放弃(_isAggregate) + **B1 零命中零LLM出口（根治挂起）**
  - 307 passed 零回归 · validate 9 断言 · 路径跑通 8/9
- **公司待做（08-10 上午·详见 OFFICE.md）**：CB-22d 后续（准确度多实体/宜昌词典/finalStep兜底/A1 GIS/A2面化/A3项目库/B3用例）+ RAG 遗留（B路径/混合检索/全仓扫描/Recall@5）
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
