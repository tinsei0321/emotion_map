# 模块三：Execution Layer（执行层）— 定稿

> **状态**：✅ 已决议  
> **日期**：2026-07-27  
> **关联决策**：D016-D018

---

## 一、职责

> 编排器说「调 density(params)」→ TOOLS 对象找到对应函数 → 调 Toolbox → 图层上地图 → 返回 observation 给 finalStep

## 二、改造

### 2.1 统一 Observation 格式

```
[OK] 动作（实际参数）→ 产出类型「图层名」（数量 单位）
     └─ 关键统计（可选·仅分析型工具）

[ERR] 动作失败: 原因

[WARN] 动作完成·局限说明
```

**核心规则**：
- 只写**实际使用**的参数值，不暴露未使用的默认值
- 单位明确：「网格单元」≠「点」≠「区域」
- 失败原因具体——LLM 据此判断「换参数重试」还是「放弃」

### 2.2 generateHeatmapForAI 接入 computeStyle

```
generateHeatmapForAI 加 analysis 参数
  → 调 computeStyle(analysis, level, polarity) 自动推导 rampKey
  → 删硬编码 rampKey:'rainbow'
  
tools.js density 工具
  → 补 polarity→analysis 映射（P→positive/N→negative/O→neutral）
  → 传 analysis 给 generateHeatmapForAI
```

### 2.3 EMC 组空 FC 修复

```
focusLayer (state.js:797):
  父组 fc 为空 → 返回子层自身（而非空父组）
  → Overview 显示正确的 feature 数量
```

## 三、决策

| ID | 决策 |
|----|------|
| D016 | 统一 observation 格式·[OK]/[ERR]/[WARN] + 实际参数 + 明确单位 |
| D017 | generateHeatmapForAI 接入 computeStyle·EMC density 补 analysis 映射 |
| D018 | focusLayer 父组空 FC 时返回子层·修 Overview「0 条」 |

---

*关联文档：README.md·`docs/catch-ball/emc-arch-deepdive/`*
