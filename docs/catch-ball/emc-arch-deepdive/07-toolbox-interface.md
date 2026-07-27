# 模块七：Toolbox ↔ EMC 接口 — 定稿

> **状态**：✅ 已决议  
> **日期**：2026-07-27  
> **关联决策**：D027-D029

---

## 一、定位

> EMC 执行链路最后一公里——调 Toolbox 时参数完整传递、结果准确返回。

## 二、④ 参数契约完整性

审计 15 个 `generate*ForAI` 函数：**14 个通过、1 个已修（density·模块三）。**

各函数 AI 入口参数均已覆盖 Toolbox dialog 控件。之前 SCAN 发现的参数缺口（P1a~P1f）通过模块六 contracts 单一源 + 模块二 _PARAM_ALIAS 分区全部消除。

**仅剩**：rank `by` 默认值 `'polarity'` → `'worst'`（归入 contracts 定义·模块六 R1）。

## 三、⑤ EMC 组互斥

| 决策 | 内容 |
|------|------|
| **互斥规则** | 保留——分析图层互斥是合理设计（避免视觉混乱） |
| **体验修复** | 图层被互斥隐藏时·侧栏显示原因提示；EMC 组 children 全部不可见时·不显示空组卡片 |
| **归属** | UI 体验需求·非架构决策·由 Designer 后续出方案 |

## 四、⑥ ForAI = dialog 镜像

| 决策 | 内容 |
|------|------|
| **定义** | AI 入口参数 ⊇ dialog 控件参数（不是代码一样·是能力等价） |
| **落地** | contracts 中 `panel_source` 字段 + CI 校验脚本（`validate_forai_mirror.py`） |
| **开发铁律** | dialog 新增控件 → contracts 同步 → CI 校验 AI 入口是否支持 |

## 五、决策

| ID | 决策 |
|----|------|
| D027 | generate*ForAI 参数契约完整性已审计·15 个全过 |
| D028 | 保留 enforceMutualExclusion·增加被隐藏提示+隐藏空组卡片 |
| D029 | ForAI = dialog 镜像通过 contracts + CI 校验落地 |

---

*关联文档：README.md·`docs/catch-ball/emc-arch-deepdive/`*
