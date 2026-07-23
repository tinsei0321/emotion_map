# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月23日收工（**测试飞轮 v4（意图/工具各 100·方向纠偏）+ todo 机制固化**）| 分支 `main` | 已 push

## 本轮完成

### 测试飞轮 v4（用户实测 v3 后提 6 点）
- **意图识别方向纠偏（核心·痛点3）**：意图 = NL→可执行工作流转译（范围→筛选→分支→工具→步骤），非回答文本。测试断言转向 template+工具转译链（diagnose template + geoCalls 触发工具）。
- **DATA 资产系统（痛点1）**：[test-assets.js](frontend/js/test-assets.js) 语义清单（RANGES/POINTS）→ llmRun 自动加载，不再让用户补范围。用户重组 boundaries（presets/ 上移顶层）一并修。
- **摘要极简关键（痛点2）**：分型显 template/tools/params/产物（工具类 `tools:zonal_stats·区=西陵·+1层`）。
- **用例重写（痛点4）**：意图 100 + 工具 100 生成器（270 总·≤2 工具≤4 步·针对性）；slider 默认 25。
- **存报告覆盖确认（痛点5）**：手动存问覆盖；serve `/_test/report` 支持 name 覆写。
- **按钮状态机（痛点6）**：停止↔重新开始 + FAB 重配 + 重跑中断批量。

### todo 机制固化
用户级 `~/.claude/CLAUDE.md` 新增「Todo 生命周期（定期归档/删除）」节（5 条：完成即归档/阶段覆盖/活跃≤6/WIP=1/关键节点更新）。

## 下一步
- **测试飞轮 v4 实测**：跑 LLM 例（slider 25 起）收集转译断言失败 → 调 INTENT/TOOL prompt 池提 pass 率（针对性）
- 意图断言若过软可加 method/plan 信号（需 agent 暴露·动承重·暂缓）
- C grid 独立 skill（中期）/ D method 标准化（远期）
- `tests/reports/` 是否 gitignore（生成物，当前未提交）

## 承重不变
diagnose prompt / 四态出口 / harness 主循环 / tracker 不动 ｜ 改动全在 ?test=1 测试层 + serve dev + 启动器 ｜ 不派 subagent ｜ todo 短列表 + 定期归档
