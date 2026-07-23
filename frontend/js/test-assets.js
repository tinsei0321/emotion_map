// ═══ test-assets.js — DATA 资产语义清单（测试自动提取，不硬编码路径）═══
// 范围文件：DATA/boundaries/（顶层；presets/ 已并于顶层）
// 点层：DATA/processed/
// 用例通过语义名引用（'L2-T1' / '行政区' / '二马路片区'），llmRun 解析为实际文件。
// 数据增减只改本文件，用例零改动。

export const RANGES = {
  '行政区':     { file: '行政区.geojson',                 desc: '宜昌行政区划（含西陵/伍家岗/夷陵等区，MC 字段）' },
  '社区':       { file: '社区.geojson',                   desc: '社区边界' },
  '商业用地':   { file: '用地_商业.geojson',              desc: '三调商业服务业用地' },
  '居住用地':   { file: '用地_居住.geojson',              desc: '三调居住用地' },
  '公园广场':   { file: '用地_公园广场.geojson',          desc: '公园广场用地' },
  '二马路片区': { file: '大南门二马路滨江片区.geojson',   desc: '大南门·二马路滨江片区边界（周边分析用）' },
  '核心主城':   { file: '西陵伍家核心主城.geojson',       desc: '西陵+伍家核心主城范围' },
  '中心城区':   { file: '中心城区行政区划_1623.geojson',  desc: '中心城区 1623 行政区划' },
  '现状水系':   { file: '现状水系.geojson',               desc: '现状水系' },
};

export const POINTS = {
  'L2-T1':    'xiling_wujia_L2_T1_L2_result_csv.csv',
  'L2-T2':    'xiling_wujia_L2_T2_L2_result_csv.csv',
  'L2-T3':    'xiling_wujia_L2_T3_L2_result_csv.csv',
  'L1-T1':    'xiling_wujia_L1_T1_result_csv.csv',
  'ermawu-T1':'ermawu_l3l4_T1_result_csv.csv',
};

// 语义名 → 文件名；未知则原样返回（向后兼容直接传文件名）
export function resolveRange(sem) { const r = RANGES[sem]; return r ? r.file : sem; }
export function resolvePoints(sem) { return POINTS[sem] || sem; }
