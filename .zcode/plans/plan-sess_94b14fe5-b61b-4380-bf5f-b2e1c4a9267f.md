## 任务：产出 CB-22e 地图标记准确度与防护评估回应（glm组）

### 产出文件
`docs/catch-ball/discuss/CB22e-地图标记准确度与防护_回应_glm组_2026-08-10.md`

### 核实结论（已完成代码级独立核实·2 Explore agent + 直读关键代码）

**claude 取证 5 项·glm 核实 4 项属实 + 1 项措辞不准：**

1. ✅ P2 兜底链路确实存在（api.js:34 45s → harness.js:801 catch `_composeDegradedConclusion`）
2. ✅ P1.1 `_core_entities` `return [best]`（place_layer.py:158·只返最长单候选）
3. ✅ P1.2 jieba `load_userdict` 全仓库零代码命中（未实施）
4. ✅ P1.3「老城中心」不在挡词表·jieba 拆后"中心"成候选误匹配
5. ⚠️ P1.4「amap score 恒 0」措辞不准——forward local score 非恒 0（_match_score 300/250/...）·search_place amap 路径 score=0.0 写死

### 6 焦点判定

| 焦点 | glm 判定 | 核心观点 |
|---|---|---|
| 1 P2 前提修正 | **partial** | 兜底存在·但 `_composeDegradedConclusion` 对部分命中表述可能不准（取末行 5 关键词·generate_point_layer observation 格式可能不匹配 → fallback 通用文案） |
| 2 P1.1 多实体 | **agree** | 候选≤3 + substring 要求 len≥3（防短词泛匹配） |
| 3 P1.2 jieba 词典 | **agree** | 仅宜昌专名·污染面可控（SCRIPT extract_tags 不受影响） |
| 4 P1.3 老城中心 | **partial** | 入 `_AGGREGATE_WORDS`（非 `_ZONE_SUFFIXES`）+ 分词前整名拦截 |
| 5 P1.4 amap 标注 | **partial** | 落 observation + 文案"高德 POI·近似位置" + 按 data_source 区分 |
| 6 P3 注入 | **agree** | 断言"标记命中≥1 + 0 挂起 + <30s" |

### 承重红线：全守（P1 改 place_layer/tools·非 diagnose/harness/D019/track）

### 纯只读评估·落盘 1 个 markdown 讨论文档