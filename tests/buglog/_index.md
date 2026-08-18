# Bug Log 索引

> 自动生成（`py tests/buglog/_gen_index.py`）·勿手改。条目总数 **13**·未解决 **5**。
> recurring（历史复发 >=2）见 [_trend.md](_trend.md)。

## 概览

### 按状态

| 值 | 数量 |
|---|:-:|
| [RESOLVED] | 8 |
| [OPEN] | 5 |


### 按类型

| 值 | 数量 |
|---|:-:|
| [BUG] | 9 |
| [UI] | 3 |
| [PERF] | 1 |


### 按严重度

| 值 | 数量 |
|---|:-:|
| [HIGH] | 5 |
| [CRIT] | 3 |
| [MED] | 3 |
| [LOW] | 2 |


### 按模块

| 值 | 数量 |
|---|:-:|
| UI | 5 |
| 工具调用 | 3 |
| finalStep | 2 |
| FC诊断 | 2 |
| 数据识别 | 1 |


## 全部条目

| ID | 标题 | 类型 | 严重度 | 状态 | 模块 | 复现 | 关联 |
|:-:|------|:-:|:-:|:-:|:-:|:-:|------|
| B001 | 多要素裁剪失败螺旋（extract_feature 字段重命名断裂 + 单工具限制 + FC 推理死循环） | [BUG] | [HIGH] | [RESOLVED] | 数据识别 | 4 | CB-09 TC-06 |
| B002 | finalStep 假结论 — "只说不做/只做一半"（复现） | [BUG] | [CRIT] | [OPEN] | finalStep | 3 | CB-09 TC-21 |
| B003 | LLM 推理螺旋 — 简单查询耗时异常（复现） | [PERF] | [HIGH] | [RESOLVED] | FC诊断 | 2 | CB-09 TC-22 |
| B004 | finalStep 假结论 — 筛选点图层"只说不做"（复现） | [BUG] | [CRIT] | [OPEN] | finalStep | 2 | CB-09 TC-23 |
| B005 | 多步操作链 — 只做一半停下（部分新） | [BUG] | [CRIT] | [RESOLVED] | 工具调用 | 1 | CB-09 TC-24 |
| B006 | 意图理解偏差 + 图层样式不匹配（部分新） | [BUG] | [HIGH] | [RESOLVED] | FC诊断 | 1 | CB-09 TC-25 |
| B007 | 图层类型混乱 — 声称面层实际产出点层（部分新） | [BUG] | [HIGH] | [RESOLVED] | 工具调用 | 1 | CB-09 TC-26 |
| B008 | 网格聚合 2D/3D 视角未解耦（新发现） | [UI] | [MED] | [OPEN] | UI | 3 | CB-09 TC-27 |
| B009 | 回到底部按钮位置+样式不当（太显眼·右下→右上） | [UI] | [LOW] | [RESOLVED] | UI | 1 | CB-09 |
| B010 | 飞轮测试数据层命名混乱 — L2·e2e 不知所云 | [UI] | [LOW] | [RESOLVED] | UI | 1 | CB-09 |
| B011 | 飞轮测试每例重复加载行政区 — 图层堆叠 | [BUG] | [MED] | [RESOLVED] | 工具调用 | 1 | CB-09 |
| B012 | 网格/地形悬停社区行张冠李戴——按格中心单点归属而非指针位置，跨界格显示邻居社区 | [BUG] | [MED] | [OPEN] | UI | 3 | CB-38 |
| B013 | L0 点层聚合 choropleth 色带反语义——点数越多颜色越浅、零点社区落最深红 | [BUG] | [HIGH] | [OPEN] | UI | 2 | CB-41 |
