# 模块六：Prompt Engineering — 定稿

> **状态**：✅ 已决议  
> **日期**：2026-07-27  
> **关联决策**：D025-D026

---

## 一、定位

> 不参与运行时。是**基础设施**——让 Flash/Pro/finalStep 的 prompt 从同一份工具定义表派生，消灭手写副本和参数名漂移。

## 二、单一真相源：tool_contracts.py

```
tool_contracts.py（Python dict）
  │
  ├─→ paradigm.py      TEMPLATE_REGISTRY  ← 自动派生
  ├─→ prompts.py        工具列表段          ← 自动派生
  ├─→ stages.js          SKILL_DEFS          ← 自动派生（或镜像+校验）
  └─→ Pro prompt        工具能力字典          ← 自动派生
```

### 条目结构

```python
TOOL_CONTRACTS = {
  "density": {
    "category": "analyze",
    "triggers_cn": ["热力图","密度","网格","方格","聚集"],
    "params": [
      {"name":"analysis","type":"enum","values":["terrain","positive","negative","neutral"],
       "default":"terrain","panel_source":"heatmap-dialog#analysis-type","alias":[]},
      {"name":"radius","type":"number","range":[50,3000],"default":300,
       "panel_source":"heatmap-dialog#radius-slider","alias":["bandwidth_m"]},
      ...
    ],
    "exclusive_with": ["hotspot"],
    "composes_with": ["clip","filter_attr","buffer"]
  },
  ...
}
```

## 三、各阶段 prompt 大小定稿

| 阶段 | LLM | Prompt | Prefill | 总耗时 |
|------|:---:|:---:|:---:|:---:|
| Flash 填卡 | Flash | 1-3.5KB | <2s | <5s |
| Pro 推理 | Pro | 2.5-5KB | 1.5-3s | 5-10s |
| finalStep 结论 | Flash | 0.6-1.3KB | <1s | 3-5s |

**典型请求（单卡）**：8-10s  
**复杂请求（多卡+Pro）**：13-20s

## 四、MANIFESTO 分层

| 节 | Flash | Pro | finalStep |
|:---:|:---:|:---:|:---:|
| §1-6（概念/管道/架构/场景） | ❌ | ❌ | ❌ |
| §7（演示逻辑链） | ❌ | ❌ | ❌ |
| §8-11（策略/同步/公约/范式） | ❌ | ❌ | ❌ |

**§1-11 在新架构中全部移除。** 领域知识已在 contracts 的结构化数据中，比散文更精确。

## 五、决策

| ID | 决策 |
|----|------|
| D025 | tool_contracts.py 作为工具定义的单一真相源 |
| D026 | Flash/Pro/finalStep prompt 从 contracts 派生·不再手写 |
| R1 | rank `by` 默认值 `'polarity'` → `'worst'`（归入 contracts 定义） |

---

*关联文档：README.md·`docs/catch-ball/emc-arch-deepdive/`*
