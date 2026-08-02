// ═══ emc-patterns.js — EMC 词表/模式单一权威源（CB-10 分歧2 词表集中）═══
// 从 harness.js/stages.js 散落的内联正则/词表集中到此一处：
//   - _LANDUSE 用地关键词（harness._autoExpandOverlays / _deterministicRecover）
//   - _DK 领域词表（stages._deriveDomainLens B 部）
//   - _POL_MAP 极性词映射（harness._matchPlanToQuestion）
//   - _quickIntent 意图词（harness 数据清单/概念/问候）
// 新问法进注册表（此处）不进内联正则；命中遥测见 _autoExpandOverlays console。

// 用地关键词（B005/B002 裁剪/叠置/合并）：去「用地」泛词——防「商业用地」误匹配成 ['商业','用地'] 2 词
export const LANDUSE_KW = ['商业', '居住', '公园', '绿地', '工业', '广场', '办公', '教育', '医疗'];

// 领域词表（_deriveDomainLens B 部·关键词兜底）
export const DOMAIN_KW = {
  urban_planning: ['规划', '用地', '商业用地', '居住用地', '功能区', '土地'],
  urban_renewal: ['更新', '老旧', '改造', '棚改', '小区', '归因', '情绪'],
  urban_operation: ['运营', '商圈', '场馆', '奥体', '商业街', '演唱会'],
  urban_governance: ['治理', '交通', '停车', '施工', '城管', '环境'],
};

// 极性词映射（_matchPlanToQuestion·追问时匹配极性 plan）
export const POLARITY_KW = [
  { kw: ['消极', '负面', 'negative', '差'], polarity: 'negative' },
  { kw: ['积极', '正面', 'positive', '好'], polarity: 'positive' },
  { kw: ['中性', 'neutral', '客观'], polarity: 'neutral' },
  { kw: ['综合', '总体', 'overall', '全部'], polarity: 'overall' },
];

// _quickIntent 意图词（B003 数据清单短路 + 概念/日常）
export const CONCEPT_KW = ['什么是', '是什么', '含义', '意思', '解释', '区别', '定义', '为什么', '是指', '如何理解', '有哪些方法'];
export const INVENTORY_KW = ['上传了哪些', '有哪些数据', '数据列表', '加载了什么', '哪些文件', '数据清单', '有哪些图层', '加载了哪些'];
export const GREETING_KW = ['今天', '星期', '几点', '你好', '谢谢', '你是谁', '能做什么', '你能', '帮助'];

// 地理动词（_quickIntent → 落 diagnose）
export const GEO_VERB_KW = ['核密度', '密度分析', '热力', '热点', '裁出', '裁剪', '缓冲', '叠加', '叠置', '聚合', '网格', '排序', '最近邻', '可达性', '出图', '生成图'];

// G6b 联网搜索词（纯问答大问题/聚焦问题·general 短路内触发·禁假大空需宜昌实据）
// CB-12 B3 修复（Codex+glm组 共识）：删「情绪地图」（项目名·概念问误触发）·删「对比/介绍」（过泛·对比两区应走 zonal）·
// 删「产品/意义/价值」（过泛·概念问本地答更准）·保留实据型（政策/策略/作用/应用/案例/新闻/现状/方案/做法/趋势/理念/定位/实施/情况/最新）
export const SEARCH_KW = ['理念', '定位', '政策', '策略', '作用', '应用', '案例', '新闻', '现状', '方案', '做法', '趋势', '实施', '情况', '最新'];
// 实据词判定（概念问 + 实据词 → 搜索；概念问 + 无实据词 → 本地直答）
export const SEARCH_EVIDENCE_RE = /政策|策略|方案|案例|新闻|现状|趋势|实施|最新|应用场景|做法|作用|情况/;

// 宜昌地名（_quickIntent → 落 diagnose·可能 B/C）
export const REGION_KW = ['西陵', '伍家岗', '点军', '夷陵', '猇亭', '宜昌', '滨江', '奥体', '二马路', '大南门', 'cbd'];
