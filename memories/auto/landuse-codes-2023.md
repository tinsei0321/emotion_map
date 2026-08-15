---
name: landuse-codes-2023
description: 国标用地用海分类（2023.11）权威源位置——读 .py 勿再读 PDF
metadata: 
  node_type: memory
  type: reference
  originSessionId: a1f14bd2-ca0c-4b3f-8dc0-14dd3262d601
---

国标《国土空间调查、规划、用途管制用地用海分类指南（2023.11）》用地分类已固化：
- **权威数据源**：`ai_qa/landuse_codes_2023.py`（24 一级 / 111 二级 / 40 三级 + 代码 + 查询函数 landuse_name/level/parent/children/search + EMC_PRESET_TO_GB 对照）
- **人可读概览**：`docs/landuse-classification-2023.md`

需要用地类型/代码/层级时**读 .py，勿再读 PDF**（PDF 在 docs/ 下，已提取完毕，无需重读）。

编码体系：2 位=一级类、4 位=二级类、6 位=三级类。三级类仅 06-12 城镇建设类设立（40 个），其余一级类仅设到二级。指南 P5 述 140 三级类但 PDF 实际 40，以 PDF 为准。

EMC 现有用地预设（land_commercial/residential/park，按 DLMC 落色）是国标子集，对照 EMC_PRESET_TO_GB（商业→09/0901，居住→07/0701，公园广场→14/1401）。规划中的字段语义层 land_use_class role 以此代码+名称为值域。链接 [[emc-tri-state-exit-contract]]。
