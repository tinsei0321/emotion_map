# 会话交接卡

> 单份当前快照，每次交接覆写「当前节点」，旧的删；历史在 `docs/revision-log.md` + git。
> 最后更新：07月23日收工（**CPD v1.3→v1.5 + EMC v1.4→v1.6 核心 bug 修复 + 测试飞轮 v3（100例）**）| 分支 `cpd` | 已 push

## 本轮完成（v1.3→v1.7）

### CPD 引擎（v1.3）
视觉焦点卡片 + 阶段 A 方向 + 阶段 B 细化级联 + 双域架构（收起光环/展开提示条）+ 空态欢迎语 + Step 2 diagnose 参数提示 + Step 3 deliberateStep（gate 收紧）+ hint 消失 bug 修。

### EMC 核心修复（v1.4→v1.6）
- P0 分析型工具误判 GAP（zonal/compare rows 非空=成功）
- P1 zonal/compare 产红-绿聚合图层 + activeAnalysis 认
- P2 Smart ask_user（失败/缺参→提问非放弃）
- 滚动跳顶修复 + 字段失败 Smart 恢复
- F3 gate 扩 C 类（假完成）+ deliberateStep gate 收紧（省调用）
- density 网格→3d 语义兜底 + extract_feature 字段校验 + clip 语义
- Pro/Flash→大脑/闪电 SVG + 浮窗底部对齐

### 测试飞轮（v1→v3）
项目网页端抽屉（?test=1）+ 100 例 data-driven + 8 项 UX（弹窗选类型/重跑/跳转答案/V/X 评价/LLM 自动展开/DATA CSV/按钮状态）+ Prompt 设计原则 8 条 + 行内 V/X 按钮。

## 4 痛点
1 效率 ✅(deliberateStep gate) ｜ 2 字段 🔄(ask 兜底+校验·根未除) ｜ 3 gis ✅(误判GAP+density兜底) ｜ 4 假完成 ✅(F3扩C)

## 下一步
- C grid 独立 skill（中期·前后端 paradigm 同步）
- D method 标准化（远期·需拍板·触 diagnose 输出）
- G2-G4 CPD banner/全状态/抛光
- bug-log + catalog 扩展
- 测试飞轮 full 模式实测（~40min·收集失败→第三方根因）

## 承重不变
diagnose prompt / 四态出口 / harness 主循环 / tracker 不动 ｜ CPD 纯确定性 ｜ 不派 subagent
