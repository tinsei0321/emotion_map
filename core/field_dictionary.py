"""字段语义层 · 统一字段字典 + alias 解析（P1 核心）。

把散落 9+ 处的字段同义词映射（FIELD_SYNONYMS / _KEY_FIELDS / manifest nameField /
dominantDLMC / range_selector name_candidates / resolve_boundary / extract_feature 兜底）
收敛为单一权威源。物理列名不改，只加 canonical（=标准名）别名解析层。

角色（role）= 字段的语义类型（不是物理列名）。如 "sentiment"/"情绪"/"极性" 都是 polarity role。
  - 用户上传字段：polarity/score/text/location/emotion_type/emotion_intensity/name/category/
    domain/element/topic/timestamp/geometry_lon/geometry_lat/boundary_name/boundary_id/land_use_class
  - 自产层契约（self_produced，只声明不归一）：polarity_index/point_count/domain_top/element_top/
    issue_label/attribution/suggestion/density/Gi_Z/Gi_P/hotspot/area_km2
  - 渲染契约（render_contract，_fieldSamples 过滤）：_level/_norm/_grid_h/_grid_norm/_ui/_band

用地类型值域见 ai_qa/landuse_codes_2023.py（国标 24/111/40）。
LLM 推断端点（P2）复用 ai_qa/llm.py chat_with_fallback，miss 字段才调。
"""

# ════════════ 字段角色字典 ═════════════
# variants 之间不重叠（name/boundary_name/land_use_class 各自独占其物理字段名）。
FIELD_ROLE_DICT = {
    # —— 用户上传情绪点层常见字段 ——
    'polarity': {
        'variants': ['polarity', 'sentiment', 'label', 'sentiment_label', 'emotion', '情绪', '极性', '情感倾向'],
        'dtype_hint': 'categorical',
        'description': '情绪极性标签（5 级：very_positive/positive/neutral/negative/very_negative）',
    },
    'score': {
        'variants': ['score', 'sentiment_score', '分数', '得分', '评分'],
        'dtype_hint': 'number',
        'description': '情绪得分（数值，sentiment score，非置信度）',
    },
    'confidence': {
        'variants': ['l1_confidence', 'l2_confidence', 'confidence', 'ai_confidence', '置信度', '可信度', '数据置信度'],
        'dtype_hint': 'number',
        'description': '数据置信度（L1 治理阶段 LLM 判断的数据相关性置信度，0~1；与 score 情绪得分不同）',
    },
    'text': {
        'variants': ['text', 'content', 'comment', 'review', '评论', '文本', '内容', '正文'],
        'dtype_hint': 'string',
        'description': '评论文本内容',
    },
    'location': {
        'variants': ['location', 'place', 'address', '地点', '位置', '地址'],
        'dtype_hint': 'string',
        'description': '地点/位置描述',
    },
    'emotion_type': {
        'variants': ['emotion_type', 'emotionType', '情绪类型', '情感类型'],
        'dtype_hint': 'categorical',
        'description': '情绪类型分类',
    },
    'emotion_intensity': {
        'variants': ['emotion_intensity', 'emotionIntensity', '情绪强度', '情感强度', 'intensity'],
        'dtype_hint': 'number',
        'description': '情绪强度（数值）',
    },
    # —— 通用名称/类别（上传点/面层均可）——
    'name': {
        'variants': ['name', 'NAME', 'Name', '名称', '地名', '点名称'],
        'dtype_hint': 'string',
        'description': '通用名称字段',
    },
    'category': {
        'variants': ['category', 'type', 'class', '类别', '类型', '分类', '类别名'],
        'dtype_hint': 'categorical',
        'description': '通用类别/类型字段',
    },
    # —— 4×5 归因字段 ——
    'domain': {
        'variants': ['domain', '领域', '归因领域'],
        'dtype_hint': 'categorical',
        'description': '4×5 治理领域（urban_planning/renewal/operation/governance）',
    },
    'element': {
        'variants': ['element', '要素', '归因要素'],
        'dtype_hint': 'categorical',
        'description': '4×5 治理要素（facility/environment/service/culture/event）',
    },
    'topic': {
        'variants': ['topic', '主题', '关键词', 'keyword'],
        'dtype_hint': 'categorical',
        'description': '话题/关键词',
    },
    'timestamp': {
        'variants': ['timestamp', 'time', 'date', 'created_at', '时间', '日期', '发布时间', 'datetime'],
        'dtype_hint': 'datetime',
        'description': '时间戳',
    },
    'geometry_lon': {
        'variants': ['lon', 'lng', 'longitude', '经度', 'lng_'],
        'dtype_hint': 'number',
        'description': '经度',
    },
    'geometry_lat': {
        'variants': ['lat', 'latitude', '纬度', 'lat_'],
        'dtype_hint': 'number',
        'description': '纬度',
    },
    # —— 面层/边界字段 ——
    'boundary_name': {
        # 边界层特有名称字段（不含通用 name、不含 DLMC——DLMC 归 land_use_class）
        'variants': ['MC', '街道', '社区', '编号', '区域名称', '县名', '市名', 'Layer', 'LAYER',
                     'FID_规划', 'FID', '行政区', '行政区名称', '单元名', '单元编号'],
        'dtype_hint': 'string',
        'description': '面层/边界的名称字段（抽取/筛选某区某单元用）',
    },
    'boundary_id': {
        'variants': ['id', 'ID', 'fid', 'FID', 'code', '代码', 'OBJECTID', 'objectid'],
        'dtype_hint': 'string',
        'description': '面层/边界唯一标识',
    },
    'land_use_class': {
        'variants': ['DLMC', 'dlmc', 'DLMC_NAME', '地类名称', '地类编码', '用地类型', '用地代码',
                     'landuse', 'land_use'],
        'dtype_hint': 'categorical',
        'description': '用地类型分类（值域见 ai_qa/landuse_codes_2023.py：国标 24 一级/111 二级/40 三级）',
    },
    # —— 自产层契约字段（只声明，不归一；_fieldSamples 不过滤，AI 写 where 要用）——
    'polarity_index': {'variants': ['polarity_index'], 'dtype_hint': 'number', 'self_produced': True,
                       'description': '极性指数（-2~+2，EMC 自产聚合层）'},
    'point_count': {'variants': ['point_count'], 'dtype_hint': 'number', 'self_produced': True,
                    'description': '点数（EMC 自产聚合层）'},
    'domain_top': {'variants': ['domain_top'], 'dtype_hint': 'categorical', 'self_produced': True,
                   'description': '4×5 归因领域众数（EMC 自产）'},
    'element_top': {'variants': ['element_top'], 'dtype_hint': 'categorical', 'self_produced': True,
                    'description': '4×5 归因要素众数（EMC 自产）'},
    'issue_label': {'variants': ['issue_label'], 'dtype_hint': 'string', 'self_produced': True,
                    'description': '城建问题标签（EMC 自产）'},
    'attribution': {'variants': ['attribution'], 'dtype_hint': 'string', 'self_produced': True,
                    'description': '归因描述（EMC 自产）'},
    'suggestion': {'variants': ['suggestion'], 'dtype_hint': 'string', 'self_produced': True,
                   'description': '建议（EMC 自产）'},
    # —— 渲染契约（下划线前缀，_fieldSamples 过滤）——
    '_level': {'variants': ['_level'], 'dtype_hint': 'number', 'self_produced': True, 'render_contract': True,
               'description': 'KDE 等级（渲染）'},
    '_norm': {'variants': ['_norm'], 'dtype_hint': 'number', 'self_produced': True, 'render_contract': True,
              'description': '归一化值（渲染）'},
    '_grid_h': {'variants': ['_grid_h'], 'dtype_hint': 'number', 'self_produced': True, 'render_contract': True,
                'description': '网格高度（渲染）'},
    '_grid_norm': {'variants': ['_grid_norm'], 'dtype_hint': 'number', 'self_produced': True, 'render_contract': True,
                   'description': '网格归一化（渲染）'},
    '_ui': {'variants': ['_ui'], 'dtype_hint': 'object', 'self_produced': True, 'render_contract': True,
            'description': '渲染元数据（渲染）'},
    '_band': {'variants': ['_band'], 'dtype_hint': 'number', 'self_produced': True, 'render_contract': True,
              'description': 'KDE 波段（渲染）'},
    # —— 工具特定产物 ——
    'density': {'variants': ['density'], 'dtype_hint': 'number', 'self_produced': True,
                'description': '核密度值（KDE 自产）'},
    'Gi_Z': {'variants': ['Gi_Z', 'GiZ', 'gi_z'], 'dtype_hint': 'number', 'self_produced': True,
             'description': 'Gi* Z 值（hotspot 自产）'},
    'Gi_P': {'variants': ['Gi_P', 'GiP', 'gi_p'], 'dtype_hint': 'number', 'self_produced': True,
             'description': 'Gi* P 值（hotspot 自产）'},
    'hotspot': {'variants': ['hotspot'], 'dtype_hint': 'categorical', 'self_produced': True,
                'description': '热点标签 hot/cold/ns（hotspot 自产）'},
    'area_km2': {'variants': ['area_km2', 'area'], 'dtype_hint': 'number', 'self_produced': True,
                 'description': '面积 km²（buffer/overlay 自产）'},
}

# 反查索引：variant（小写归一）→ role。构建一次，resolve_role O(1) 查。
_VARIANT_INDEX = {}
for _role, _info in FIELD_ROLE_DICT.items():
    for _v in _info['variants']:
        _VARIANT_INDEX[_v.lower()] = _role
del _role, _info, _v


# ════════════ 查询函数 ═════════════

def resolve_role(field, hint=None):
    """字段名 → canonical role。命中返回 role 字符串，miss 返回 None。

    解析序：精确匹配 variants → 小写归一匹配。
    hint=可选上下文（如 layer kind='point'|'polygon'），预留歧义消解（当前 variants 不重叠，暂不用）。
    """
    if not field:
        return None
    f = str(field)
    # 精确匹配（区分大小写，如 MC 不与 mc 混）
    for role, info in FIELD_ROLE_DICT.items():
        if f in info['variants']:
            return role
    # 小写归一匹配
    return _VARIANT_INDEX.get(f.lower())


def resolve_field_alias(field, columns, hint=None):
    """把用户传的 field 名解析到 columns 里实际存在的列名。命中返回列名，miss 返回 None。

    物理列名不改——本函数只读 columns 找对应列，不 rename。

    解析序：
      1. field 精确在 columns → 返回 field
      2. field 经 resolve_role 得 role；在 columns 找同 role 的列 → 返回该列
      3. case-insensitive 在 columns 匹配 → 返回
      4. miss → None
    """
    if not field:
        return None
    cols = list(columns) if columns is not None else []
    f = str(field)
    # 1. 精确
    if f in cols:
        return f
    # 2. role 匹配（field 的 role → 找 columns 里同 role 的列）
    role = resolve_role(f, hint)
    if role:
        for c in cols:
            if resolve_role(c, hint) == role:
                return c
    # 3. case-insensitive
    fl = f.lower()
    for c in cols:
        if c.lower() == fl:
            return c
    # 4. miss
    return None


def is_self_produced(role):
    """role 是否为 EMC 自产层契约字段。"""
    info = FIELD_ROLE_DICT.get(role) if role else None
    return bool(info and info.get('self_produced'))


def is_render_contract(role):
    """role 是否为渲染契约字段（_fieldSamples 过滤用）。"""
    info = FIELD_ROLE_DICT.get(role) if role else None
    return bool(info and info.get('render_contract'))


def is_internal_field(field):
    """字段是否为内部/渲染字段（下划线前缀），_fieldSamples 过滤用。
    保留原 _fieldSamples 的 k[0]!=='_' 行为兜底（未登记的 _xxx 也过滤）。"""
    return bool(field) and str(field).startswith('_')


def find_boundary_name_column(columns):
    """面层/边界 nameField 推断：按优先级找名称列，返回列名或 None。

    优先级：boundary_name role（MC/街道/社区/...）→ name role（name/名称/...）
    → land_use_class role（DLMC/地类名称——用地层名称）。
    用于 resolve_boundary 的 send-in GeoJSON 路径（preset 路径仍优先读 manifest nameField）。
    """
    cols = list(columns) if columns is not None else []
    for target_role in ('boundary_name', 'name', 'land_use_class'):
        for c in cols:
            if resolve_role(c) == target_role:
                return c
    return None


def role_label(role):
    """role → 中文描述（注入 grounding 用）。"""
    info = FIELD_ROLE_DICT.get(role) if role else None
    return info['description'] if info else ''


# FIELD_INFER 推断 confidence 低于此值视为"纯猜"不可承重（rubric 0.3=纯猜档）→ role 置 null，
# 防低置信 role 经 grounding/aggregate 误导（承重：与 ⑤② alias 解析配套，只让有把握的 LLM role 进链路）。
LLM_ROLE_CONFIDENCE_FLOOR = 0.3


def validate_llm_roles(inferred):
    """校验 LLM 推断返回的 {field: {role, confidence, reason}} ——
    1) role 必须在字典内；2) confidence ≥ LLM_ROLE_CONFIDENCE_FLOOR(0.3)。任一不满足 → role 置 None（不承重）。
    用于 P2 /aiqa/profile_fields 端点（所有 LLM 推断 role 的唯一 choke point）。"""
    out = {}
    for fld, v in (inferred or {}).items():
        if not isinstance(v, dict):
            continue
        role = v.get('role')
        conf = v.get('confidence', 0.5)
        if role and role in FIELD_ROLE_DICT and conf >= LLM_ROLE_CONFIDENCE_FLOOR:
            out[fld] = {'role': role, 'confidence': conf, 'reason': v.get('reason', '')}
        else:
            _why = 'invalid role' if not (role and role in FIELD_ROLE_DICT) else f'low confidence ({conf} < {LLM_ROLE_CONFIDENCE_FLOOR})'
            out[fld] = {'role': None, 'confidence': 0, 'reason': _why}
    return out


if __name__ == '__main__':
    # 自检
    assert resolve_role('sentiment') == 'polarity'
    assert resolve_role('情绪') == 'polarity'
    assert resolve_role('MC') == 'boundary_name'
    assert resolve_role('DLMC') == 'land_use_class'
    assert resolve_role('name') == 'name'
    assert resolve_role('不存在字段') is None
    # alias 解析
    cols = ['sentiment', 'score', 'MC', 'DLMC']
    assert resolve_field_alias('polarity', cols) == 'sentiment'   # role 匹配
    assert resolve_field_alias('情绪', cols) == 'sentiment'        # 中文同义词
    assert resolve_field_alias('MC', cols) == 'MC'                  # 精确
    assert resolve_field_alias('name', cols) is None                # miss（无 name role 列，boundary_name 是不同 role）
    assert resolve_field_alias('区域名称', cols) == 'MC'             # boundary_name 同义词→role 匹配 MC
    # 边界名称推断
    assert find_boundary_name_column(['MC', 'DLMC']) == 'MC'
    assert find_boundary_name_column(['DLMC']) == 'DLMC'            # 用地层名称兜底
    assert find_boundary_name_column(['name']) == 'name'
    # 自产/渲染
    assert is_self_produced('polarity_index')
    assert not is_self_produced('polarity')
    assert is_render_contract('_level')
    assert is_internal_field('_level')
    assert not is_internal_field('polarity')
    print(f'[OK] {len(FIELD_ROLE_DICT)} roles, resolve_role/alias/boundary_name/is_* 自检全过')
    print('  sentiment→', resolve_role('sentiment'), '| MC→', resolve_role('MC'), '| DLMC→', resolve_role('DLMC'))
