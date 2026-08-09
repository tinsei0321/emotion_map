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
  urban_governance: ['治理', '交通', '停车', '施工', '城管', '环境', '城市体检'],   // CB-16 Wave 1：补「城市体检」长词（防"健康体检/体检中心"误触）
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
export const GEO_VERB_KW = ['核密度', '密度分析', '热力', '热点', '裁出', '裁剪', '缓冲', '叠加', '叠置', '聚合', '网格', '排序', '最近邻', '可达性', '出图', '生成图', '地点', '在哪', '坐标'];   // CB-15 P1：lookup_place 触发（避开"周边/附近"·留 buffer）

// G6b 联网搜索词（纯问答大问题/聚焦问题·general 短路内触发·禁假大空需宜昌实据）
// CB-12 B3 修复（Codex+glm组 共识）：删「情绪地图」（项目名·概念问误触发）·删「对比/介绍」（过泛·对比两区应走 zonal）·
// 删「产品/意义/价值」（过泛·概念问本地答更准）·保留实据型（政策/策略/作用/应用/案例/新闻/现状/方案/做法/趋势/理念/定位/实施/情况/最新）
export const SEARCH_KW = ['理念', '定位', '政策', '策略', '作用', '应用', '案例', '新闻', '方案', '做法', '趋势', '实施'];
// 实据词判定（概念问 + 实据词 → 搜索；概念问 + 无实据词 → 本地直答）
export const SEARCH_EVIDENCE_RE = /政策|策略|方案|案例|新闻|趋势|实施|应用场景|做法|作用/;   // CB-12 弱实据词删（最新/现状/情况·空间问高频·防「西陵区最新的情绪分布」误进搜索）

// CB-22 RAG：开放语义知识检索触发（哪些/如何/为什么+跨文档综合·B 路径未命中降级）
// ★ 临时承担 B 路径结构化词（CB-22b query_knowledge_base 建后删除下列·转 KNOWLEDGE_QUERY_KW·RAG 只保留开放语义）
// TODO(CB-22b): B 路径建后·删"有哪些项目/体检问题/体检指标/更新项目"等临时结构化词
export const RAG_QUERY_KW = [
  // 开放语义（RAG 本职·开放语义/跨文档综合）
  '哪些城市', '哪些案例', '哪些项目适合', '如何参考', '做法', '机制', '路径',
  // ★ 临时承担 B 路径结构化（CB-22b 建后移除）
  '有哪些项目', '体检问题', '体检指标', '更新项目', '项目库', '问题清单',
];
// 知识词判定（开放语义 + 知识词 → rag_query 短路；无知识词不触发·宁落不误断）
export const RAG_KNOWLEDGE_RE = /项目|指标|体检|案例|政策|片区|问题|做法|机制/;

// CB-22 分类→回答范式映射（显式契约·防"分类正确但范式错位"）。
// text_qa=纯文字直答（finalStep 纯问答）· knowledge_qa=知识问答（检索素材 → finalStep LLM 综合+引用来源·
//   CB-22 用户修正·成功路径必须 LLM 综合·零 LLM 仅限失败兜底 R3 EXIT_CONCEPT）· layer=finalStep 图层（分析）
export const PARADIGM_MAP = {
  'general': 'text_qa',
  'search': 'text_qa',            // general 子路径（CB-12 联网素材注入）
  'rag_query': 'knowledge_qa',    // RAG 检索 → LLM 综合素材（修正后·非零 LLM）
  'knowledge_query': 'knowledge_qa', // B 路径（CB-22b·确定性查询·建后收紧）
  'gis_operation': 'layer',
  'emotion_analysis': 'layer',
};

// 宜昌地名（_quickIntent → 落 diagnose·可能 B/C）
export const REGION_KW = ['西陵', '伍家岗', '点军', '夷陵', '猇亭', '宜昌', '滨江', '奥体', '二马路', '大南门', 'cbd'];

// CB-16 Wave 0：出口卡片触发词表（镜像 ai_qa/outlet_kb/build_outlet_schema.py TRIGGER_WORDS·
// 单一权威源在后端·仅 UI 提示不改控制流·触发判定收敛在后端）
export const OUTLET_TRIGGER_KW = ['更新', '体检', '需求', '满意度', '排序', '识别', '时序', '改造'];
// CB-16 Codex/glm：UI 语境排除表（与后端 _UI_CONTEXT_WORDS 同步·防"更新图层"提示与后端行为不一致）
export const OUTLET_UI_EXCLUDE_KW = ['更新图层', '更新时间', '更新样式', '刷新', '重新加载'];
