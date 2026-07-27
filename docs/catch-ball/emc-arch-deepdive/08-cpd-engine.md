# 模块八：CPD 引擎 — 定稿

> **状态**：✅ 已决议  
> **日期**：2026-07-27  
> **关联决策**：D030-D034

---

## 一、定位

> CPD 不调 LLM。消费 Pro 产出的 plans[]，展示为引导选项。和追问胶囊相辅相成——L3 胶囊触发 CPD 介入。

## 二、Pro → CPD 数据流

```
Pro 产出: plans = [
  { rank:1, label, tool, params },  → 编排器执行
  { rank:2, label, tool, params },  → CPD 选项
  { rank:3, label, tool, params },  → CPD 选项
  ...
]
```

| 消费方 | 取什么 | 做什么 |
|------|------|------|
| 编排器 | rank=1 | 直接执行（跳过 Flash·params 已由 Pro 填好） |
| CPD | rank=2+ | 展示为可点击选项 |

## 三、交互流程

```
用户点 CPD 选项 → 编排器直接执行（跳过 Flash）→ finalStep 出结论
  → 该选项从 CPD 列表中移除
  → 剩余选项继续展示
  → 全部执行完 → 展示完成状态
```

## 四、设计决策

| ID | 决策 |
|----|------|
| D030 | CPD 不调 LLM·内容全部来自 Pro plans |
| D031 | CPD 选项点击后直接执行·跳过 Flash（params 已由 Pro 填好） |
| D032 | 已执行选项自动移除·剩余继续展示·不重新走 Pro |
| D033 | 全部执行完毕后展示完成状态·不进一步建议新问题 |
| D034 | 用户选项偏好记入自我成长·优化 Pro 排序 |

---

*关联文档：README.md·`docs/catch-ball/emc-arch-deepdive/`*
