# 模块二：Orchestrator（编排层）— 定稿

> **状态**：✅ 已决议  
> **日期**：2026-07-27  
> **关联决策**：D012-D015

---

## 一、职责

> 接收执行计划（Pro 产出或 Flash 单卡直传），确定性派发工具执行。**不调 LLM。**

## 二、改造

### 2.1 runChainPath 动态化

```javascript
// Before: CHAIN_REGISTRY 固定链（2条）·正则匹配 NL
// After: 消费 Pro 产出的动态 chain [{step,tool,params,depends_on}]
// 按 depends_on 顺序执行·解析 $N 引用
```

### 2.2 while-loop 降级为异常兜底

```
Before: multi/unknown → while-loop（主要路径·最多6轮）
After:  Pro计划/Flash单卡→runTemplate/runChain（主要路径）
        while-loop 保留但缩至 2-3 轮·仅在 Pro 无法产出计划时触发
```

### 2.3 _PARAM_ALIAS 按工具分区

```javascript
// Before: 全局别名表·radius→radius_m 对所有工具有效·误伤 density
// After: 按工具注册别名·buffer 有 radius→radius_m·density 无
```

### 2.4 _GEO_TOOLS 补 ensure_zone

```javascript
// Before: _GEO_TOOLS 缺 ensure_zone → F3 门禁误判
// After: 加 'ensure_zone'
```

## 三、耗时

编排器自身：<10ms（纯 JS 派发）。工具执行：100ms-2s/步（取决于是否调后端 API）。

## 四、决策

| ID | 决策 |
|----|------|
| D012 | runChainPath 从 CHAIN_REGISTRY 固定链改为消费 Pro 动态 chain |
| D013 | while-loop 保留但降级为异常兜底·MAX_ROUNDS 缩至 2-3 |
| D014 | _PARAM_ALIAS 改为按工具分区·修 density radius 丢失 |
| D015 | _GEO_TOOLS 补 ensure_zone·修 F3 门禁误判 |
| DAG | 暂不做·先跑通线性链·记入 EMC 自我成长 |

---

*关联文档：README.md·`docs/catch-ball/emc-arch-deepdive/`*
