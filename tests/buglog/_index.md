# Bug Log 索引

> 自动生成（`py tests/buglog/_gen_index.py`）·勿手改。条目总数 **8**·未解决 **7**。
> recurring（历史复发 >=2）见 [_trend.md](_trend.md)。

## 概览

### 按状态

| 值 | 数量 |
|---|:-:|
| [OPEN] | 7 |
| [RESOLVED] | 1 |


### 按类型

| 值 | 数量 |
|---|:-:|
| [BUG] | 6 |
| [PERF] | 1 |
| [UI] | 1 |


### 按严重度

| 值 | 数量 |
|---|:-:|
| [HIGH] | 4 |
| [CRIT] | 3 |
| [MED] | 1 |


### 按模块

| 值 | 数量 |
|---|:-:|
| finalStep | 2 |
| FC诊断 | 2 |
| 工具调用 | 2 |
| 数据识别 | 1 |
| UI | 1 |


## 全部条目

| ID | 标题 | 类型 | 严重度 | 状态 | 模块 | 复现 | 关联 |
|:-:|------|:-:|:-:|:-:|:-:|:-:|------|
| B001 | 多要素裁剪失败螺旋（extract_feature 字段重命名断裂 + 单工具限制 + FC 推理死循环） | [BUG] | [HIGH] | [RESOLVED] | 数据识别 | 4 | CB-09 TC-06 |
| B002 | finalStep 假结论 — "只说不做/只做一半"（复现） | [BUG] | [CRIT] | [OPEN] | finalStep | 3 | CB-09 TC-21 |
| B003 | LLM 推理螺旋 — 简单查询耗时异常（复现） | [PERF] | [HIGH] | [OPEN] | FC诊断 | 2 | CB-09 TC-22 |
| B004 | finalStep 假结论 — 筛选点图层"只说不做"（复现） | [BUG] | [CRIT] | [OPEN] | finalStep | 2 | CB-09 TC-23 |
| B005 | 多步操作链 — 只做一半停下（部分新） | [BUG] | [CRIT] | [OPEN] | 工具调用 | 1 | CB-09 TC-24 |
| B006 | 意图理解偏差 + 图层样式不匹配（部分新） | [BUG] | [HIGH] | [OPEN] | FC诊断 | 1 | CB-09 TC-25 |
| B007 | 图层类型混乱 — 声称面层实际产出点层（部分新） | [BUG] | [HIGH] | [OPEN] | 工具调用 | 1 | CB-09 TC-26 |
| B008 | 网格聚合 2D/3D 视角未解耦（新发现） | [UI] | [MED] | [OPEN] | UI | 3 | CB-09 TC-27 |
