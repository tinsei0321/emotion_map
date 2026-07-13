// ═══ field_dictionary.js — 字段语义层 · 前端镜像（与 ai_qa/field_dictionary.py 人工对齐）═══
// 统一字段角色字典 + alias 解析。收敛 state.js FIELD_SYNONYMS / landuse_colors dominantDLMC /
// import.js detectColorMode 等零散同义词映射。物理列名不改，只加 canonical 别名解析。
// 后端 ai_qa/field_dictionary.py 是权威源；本文件是前端镜像，改字典时两处同步。
//
// 角色（role）= 字段语义类型。variants 之间不重叠（name/boundary_name/land_use_class 各自独占）。
// 用地类型值域见 ai_qa/landuse_codes_2023.py（国标 24/111/40）。

export const FIELD_ROLES = {
  // —— 用户上传情绪点层常见字段 ——
  polarity: { variants: ['polarity', 'sentiment', 'label', 'sentiment_label', 'emotion', '情绪', '极性', '情感倾向'], dtypeHint: 'categorical', description: '情绪极性标签（5 级）' },
  score: { variants: ['score', 'l1_confidence', 'l2_confidence', 'sentiment_score', 'confidence', 'ai_confidence', '分数', '得分', '评分', '置信度'], dtypeHint: 'number', description: '情绪得分/置信度（数值）' },
  text: { variants: ['text', 'content', 'comment', 'review', '评论', '文本', '内容', '正文'], dtypeHint: 'string', description: '评论文本内容' },
  location: { variants: ['location', 'place', 'address', '地点', '位置', '地址'], dtypeHint: 'string', description: '地点/位置描述' },
  emotion_type: { variants: ['emotion_type', 'emotionType', '情绪类型', '情感类型'], dtypeHint: 'categorical', description: '情绪类型分类' },
  emotion_intensity: { variants: ['emotion_intensity', 'emotionIntensity', '情绪强度', '情感强度', 'intensity'], dtypeHint: 'number', description: '情绪强度（数值）' },
  // —— 通用名称/类别 ——
  name: { variants: ['name', 'NAME', 'Name', '名称', '地名', '点名称'], dtypeHint: 'string', description: '通用名称字段' },
  category: { variants: ['category', 'type', 'class', '类别', '类型', '分类', '类别名'], dtypeHint: 'categorical', description: '通用类别/类型字段' },
  // —— 4×5 归因字段 ——
  domain: { variants: ['domain', '领域', '归因领域'], dtypeHint: 'categorical', description: '4×5 治理领域' },
  element: { variants: ['element', '要素', '归因要素'], dtypeHint: 'categorical', description: '4×5 治理要素' },
  topic: { variants: ['topic', '主题', '关键词', 'keyword'], dtypeHint: 'categorical', description: '话题/关键词' },
  timestamp: { variants: ['timestamp', 'time', 'date', 'created_at', '时间', '日期', '发布时间', 'datetime'], dtypeHint: 'datetime', description: '时间戳' },
  geometry_lon: { variants: ['lon', 'lng', 'longitude', '经度', 'lng_'], dtypeHint: 'number', description: '经度' },
  geometry_lat: { variants: ['lat', 'latitude', '纬度', 'lat_'], dtypeHint: 'number', description: '纬度' },
  // —— 面层/边界字段 ——
  boundary_name: { variants: ['MC', '街道', '社区', '编号', '区域名称', '县名', '市名', 'Layer', 'LAYER', 'FID_规划', 'FID', '行政区', '行政区名称', '单元名', '单元编号'], dtypeHint: 'string', description: '面层/边界的名称字段' },
  boundary_id: { variants: ['id', 'ID', 'fid', 'FID', 'code', '代码', 'OBJECTID', 'objectid'], dtypeHint: 'string', description: '面层/边界唯一标识' },
  land_use_class: { variants: ['DLMC', 'dlmc', 'DLMC_NAME', '地类名称', '地类编码', '用地类型', '用地代码', 'landuse', 'land_use'], dtypeHint: 'categorical', description: '用地类型分类（值域见 landuse_codes_2023.py）' },
  // —— 自产层契约（self_produced，只声明不归一；_fieldSamples 不过滤）——
  polarity_index: { variants: ['polarity_index'], dtypeHint: 'number', selfProduced: true, description: '极性指数（EMC 自产）' },
  point_count: { variants: ['point_count'], dtypeHint: 'number', selfProduced: true, description: '点数（EMC 自产）' },
  domain_top: { variants: ['domain_top'], dtypeHint: 'categorical', selfProduced: true, description: '4×5 归因领域众数（EMC 自产）' },
  element_top: { variants: ['element_top'], dtypeHint: 'categorical', selfProduced: true, description: '4×5 归因要素众数（EMC 自产）' },
  issue_label: { variants: ['issue_label'], dtypeHint: 'string', selfProduced: true, description: '城建问题标签（EMC 自产）' },
  attribution: { variants: ['attribution'], dtypeHint: 'string', selfProduced: true, description: '归因描述（EMC 自产）' },
  suggestion: { variants: ['suggestion'], dtypeHint: 'string', selfProduced: true, description: '建议（EMC 自产）' },
  // —— 渲染契约（render_contract，_fieldSamples 过滤）——
  _level: { variants: ['_level'], dtypeHint: 'number', selfProduced: true, renderContract: true, description: 'KDE 等级（渲染）' },
  _norm: { variants: ['_norm'], dtypeHint: 'number', selfProduced: true, renderContract: true, description: '归一化值（渲染）' },
  _grid_h: { variants: ['_grid_h'], dtypeHint: 'number', selfProduced: true, renderContract: true, description: '网格高度（渲染）' },
  _grid_norm: { variants: ['_grid_norm'], dtypeHint: 'number', selfProduced: true, renderContract: true, description: '网格归一化（渲染）' },
  _ui: { variants: ['_ui'], dtypeHint: 'object', selfProduced: true, renderContract: true, description: '渲染元数据（渲染）' },
  _band: { variants: ['_band'], dtypeHint: 'number', selfProduced: true, renderContract: true, description: 'KDE 波段（渲染）' },
  // —— 工具特定产物 ——
  density: { variants: ['density'], dtypeHint: 'number', selfProduced: true, description: '核密度值（KDE 自产）' },
  Gi_Z: { variants: ['Gi_Z', 'GiZ', 'gi_z'], dtypeHint: 'number', selfProduced: true, description: 'Gi* Z 值（hotspot 自产）' },
  Gi_P: { variants: ['Gi_P', 'GiP', 'gi_p'], dtypeHint: 'number', selfProduced: true, description: 'Gi* P 值（hotspot 自产）' },
  hotspot: { variants: ['hotspot'], dtypeHint: 'categorical', selfProduced: true, description: '热点标签（hotspot 自产）' },
  area_km2: { variants: ['area_km2', 'area'], dtypeHint: 'number', selfProduced: true, description: '面积 km²（buffer/overlay 自产）' },
};

// 反查索引：variant（小写归一）→ role
const _VARIANT_INDEX = {};
for (const [role, info] of Object.entries(FIELD_ROLES)) {
  for (const v of info.variants) _VARIANT_INDEX[v.toLowerCase()] = role;
}

/** 字段名 → canonical role。命中返回 role，miss 返回 null。 */
export function resolveRole(field, _hint) {
  if (!field) return null;
  const f = String(field);
  for (const [role, info] of Object.entries(FIELD_ROLES)) {
    if (info.variants.includes(f)) return role;
  }
  return _VARIANT_INDEX[f.toLowerCase()] || null;
}

/** 把 field 解析到 columns 里实际存在的列名。物理列名不改，只读找对应列。miss 返回 null。 */
export function resolveFieldAlias(field, columns, hint) {
  if (!field) return null;
  const cols = Array.isArray(columns) ? columns : [];
  const f = String(field);
  if (cols.includes(f)) return f;                                    // 1. 精确
  const role = resolveRole(f, hint);
  if (role) {                                                        // 2. role 匹配
    for (const c of cols) if (resolveRole(c, hint) === role) return c;
  }
  const fl = f.toLowerCase();                                        // 3. case-insensitive
  for (const c of cols) if (c.toLowerCase() === fl) return c;
  return null;                                                       // 4. miss
}

export function isSelfProduced(role) {
  const info = role ? FIELD_ROLES[role] : null;
  return !!(info && info.selfProduced);
}

export function isRenderContract(role) {
  const info = role ? FIELD_ROLES[role] : null;
  return !!(info && info.renderContract);
}

/** 字段是否为内部/渲染字段（下划线前缀），_fieldSamples 过滤兜底。 */
export function isInternalField(field) {
  return !!field && String(field).startsWith('_');
}

/** 面层/边界 nameField 推断：boundary_name → name → land_use_class 优先级。 */
export function findBoundaryNameColumn(columns) {
  const cols = Array.isArray(columns) ? columns : [];
  for (const target of ['boundary_name', 'name', 'land_use_class']) {
    for (const c of cols) if (resolveRole(c) === target) return c;
  }
  return null;
}

/** 在 props 里找第一个 role 命中的字段 key（用于 detectColorMode 等按 role 找列场景）。
 *  替代旧 pickKey(props, FIELD_SYNONYMS.role)——语义同（找 role variants 命中的列）。 */
export function findKeyByRole(props, role) {
  if (!props || !role) return null;
  for (const k of Object.keys(props)) {
    if (resolveRole(k) === role && props[k] != null && props[k] !== '') return k;
  }
  return null;
}

export function roleLabel(role) {
  const info = role ? FIELD_ROLES[role] : null;
  return info ? info.description : '';
}

// 兼容旧 FIELD_SYNONYMS（state.js re-export 用；从 FIELD_ROLES 派生 {role: variants}）。
// detectColorMode 等旧调用方可继续用 FIELD_SYNONYMS.polarity，但建议改用 resolveRole。
export const FIELD_SYNONYMS = Object.fromEntries(
  Object.entries(FIELD_ROLES).map(([role, info]) => [role, info.variants])
);
