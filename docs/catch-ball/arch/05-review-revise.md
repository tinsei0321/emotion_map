# 模块五：Review + Revise — 机制重做定稿

> **状态**：✅ 已决议  
> **日期**：2026-07-27  
> **关联决策**：D022-D024

---

## 一、旧 R+R（删除）

```
finalStep LLM 出草稿
  → reviewStep LLM（Flash·7项清单·4项硬失败）
    → pass → 渲染
    → fail → reviseStep LLM（Flash·重写·最多1轮）→ 渲染
```

| 属性 | 值 |
|------|------|
| 额外 LLM 调用 | 1-2 次（review + 可能 revise） |
| 额外耗时 | 5-15s |
| 覆盖范围 | 仅 while-loop + emotion_analysis（三重关闭·基本不跑） |
| 假阳性 | 高——Flash 小模型审大模型输出 |
| 假阴性 | 高——observation 不准确致 LLM 结论本身有偏差 |

---

## 二、新架构下的质量防线（三层）

```
工具执行完成 + observation（模块三·结构化）
  │
  ▼
finalStep LLM（模块四·轻 prompt·3-5s）
  → 产出: 结论 markdown + 追问胶囊列表
  │
  ▼
═══════════ 质量防线 ═══════════
  │
  ├─ L1: _verifyClaims（保留·确定性代码）
  │   检查: 声称的图层是否实际存在于地图上
  │   失败: 剔除虚假图层引用
  │   耗时: <5ms
  │
  ├─ L2: 结构化质量规则（新增·确定性代码）
  │   检查: 6 条确定性规则
  │   失败: 代码自动修正·非 LLM 重写
  │   耗时: <10ms
  │
  └─ L3: 降级渲染（兜底·确定性代码）
      触发: L1 或 L2 连续失败
      动作: 跳过 LLM 结论·直接展示 observation 原文
```

**L1+L2+L3 全部是代码——不调 LLM。总耗时 <20ms。**

---

## 三、L2 质量规则（8 条）

> **实施状态（CB-09 轮次1）**：R1/R2/R3/R4/R7 已落地（draft 级·harness.applyQualityDefense）。**R5/R6/R8 延期到轮次2**——它们依赖「追问胶囊携带 tool+params」，而胶囊绑定工具集是轮次2 P1 工作；当前胶囊为静态 `{tag,text}` prompt 串（panel.js _followUps），无 params 可校验。R8 自成长占位先在 `defense.fixes` 里带。

| ID | 规则 | 类型 | 检测内容 | 失败动作 |
|----|------|:---:|------|------|
| R1 | 非空结论 | 硬拦截 | 结论文本 > 10 字符 | 降级为纯 observation 展示 |
| R2 | 图层按钮存在 | 硬拦截 | observation OK 时·结论含 `{{show:}}` | 自动追加按钮 |
| R3 | 参数一致性 | 标记 | 结论引用的数值与 observation.params 一致 | 标记差异·不拦截 |
| R4 | 状态不矛盾 | 硬拦截 | observation OK 不说「失败」·ERR 不说「生成」 | 降级 |
| R5 | 胶囊参数合法 | 硬拦截 | 追问胶囊参数在其工具 schema 内 | 剔除无效胶囊（**轮次2**·胶囊绑定工具集后落地） |
| R6 | 胶囊工具可达 | 标记 | 胶囊目标工具在当前数据下可执行 | 标记·不拦截（**轮次2**·同 R5） |
| R7 | 结论三句骨架 | prompt约束·代码兜底 | 句1动作+句2产出+句3交互·>500字截断 | 截断+补"…" |
| R8 | 胶囊多样性 | prompt引导·代码标记 | L2 候选存在时至少 1 个 L2 胶囊 | 记日志·供自我成长（**轮次2**·同 R5） |

---

## 四、新旧对比

| 维度 | 旧 R+R | 新质量防线 |
|------|------|------|
| 机制 | Flash LLM + Flash LLM | 纯代码规则 |
| 额外耗时 | 5-15s | <20ms |
| 假阳性 | 高 | 零（确定性） |
| 修正方式 | LLM 重写 | 代码自动修补 |
| 检查范围 | 语义质量 | 结构化事实 |
| 覆盖 | 仅少量路径 | 全路径 |

---

## 五、决策

| ID | 决策 |
|----|------|
| D022 | 删除旧 R+R（review.py + reviewStep + reviseStep + REVISE_TEMPLATE + REVIEW_CHECKLIST） |
| D023 | 新质量防线三层——_verifyClaims + 结构化规则 + 降级渲染·全部代码不调 LLM |
| D024 | 旧 R+R 中 review episode 日志·迁移到新质量防线 |

---

*关联文档：README.md·`docs/catch-ball/emc-arch-deepdive/`*
