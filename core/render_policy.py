# -*- coding: utf-8 -*-
"""PT-CB11 B3-1/B3-2 · 渲染通道字段政策（单一权威源·纯常量+纯函数·零副作用）。

消费方（两侧共用·**任何一侧不得再自持键表**——双头漂移正是注入层灰框 B-3 的根因之一）：
  - api/render_routes.py：dataset 端点属性过滤（C2-4 白名单 + preset 声明字段透传）
  - tools/mcp_server_emc.py：render_spec 的 value_field 服务端校验（错配→语义化拒绝）

政策三层：
  1. 静态键集 DATASET_PROP_KEYS 显式枚举（默认拒绝·防办件编号等准标识字段外流）——
     PT-CB11 P2-2 收紧（claude 审计·08-22）：原前缀通配（poi_*/place_* 等任意后缀自动放行）
     改为已知字段全集枚举（实测仅 polarity_score_5 依赖前缀·已入枚举）；新增字段须显式声明。
  2. manifest 声明：nameField 自动放行（可读名·图例/tip 必需）+ renderFields 显式声明
     （契约优先：preset 想被渲染通道消费的指标字段必须显式声明·未声明默认拒绝）
  3. 实际字段（dataset_field_names 读文件首要素属性——校验 value_field 错配的地面真相）

纯常量模块（先例 ai_qa/manifesto.py）·无 @track 埋点需求。
"""
import json
import os

# C2-4 静态键集（自 api/render_routes.py 迁入·语义不变·2026-08-21）
DATASET_PROP_KEYS = {
    # 名称类（边界/要素可读名）
    'name', 'Name', 'NAME', 'MC', '区名', '社区', '街道', '行政区', '单元',
    # 极性/情绪类
    'polarity', 'polarity_hint', 'polarity_index', 'score', 'score_mean',
    'l1_confidence', 'emotion_intensity',
    # 领域/归因类
    'domain', 'domain_top', 'element', 'element_top', 'topic', 'issue_label',
    # 指标/地点类
    'point_count', 'place_name', 'place_name_source', 'poi_names', 'poi_count',
    # 口径类（K-02 全覆盖口径必备 来源 字段）
    '来源',
}
# P2-2 收紧：前缀通配退役——聚合衍生列（score_sum/score_std）与体检轨 polarity_score_5 显式入枚举
DATASET_PROP_KEYS |= {'score_sum', 'score_std', 'polarity_score_5'}

# 大文件防炸：超过该体积不做全量 json.load（首要素块解码兜底·再失败返回 None 降级）
_FULL_LOAD_LIMIT_MB = 25


def _manifest_groups():
    """读边界 preset manifest（manifest 缺失/坏 → []·不抛）。"""
    from core.range_selector import _PRESETS_MANIFEST
    try:
        with open(_PRESETS_MANIFEST, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return []


def _manifest_entry(dataset_id):
    for group in _manifest_groups():
        for it in group.get('items', []):
            if it.get('id') == dataset_id:
                return it
    return None


def preset_render_fields(dataset_id):
    """preset → 声明可经渲染通道透传的字段集（nameField 自动 + renderFields 显式）。非 preset → 空集。"""
    entry = _manifest_entry(dataset_id)
    if not entry:
        return set()
    fields = set()
    if entry.get('nameField'):
        fields.add(entry['nameField'])
    for f in entry.get('renderFields') or []:
        fields.add(f)
    return fields


def _dataset_file_path(dataset_id):
    """dataset → geojson 文件路径（preset 按 manifest file·点层按 geo_registry）。未知 → None。"""
    entry = _manifest_entry(dataset_id)
    if entry and entry.get('file'):
        from core.range_selector import _PRESETS_DIR
        return os.path.normpath(os.path.join(_PRESETS_DIR, entry['file']))
    try:
        from core.geo_registry import _POINT_LAYERS, _layer_path
        if dataset_id in _POINT_LAYERS:
            return os.path.normpath(_layer_path(_POINT_LAYERS[dataset_id]))
    except Exception:
        pass
    return None


def _first_feature_props(path):
    """读文件前几个要素的属性键并集（地面真相·不载几何）。

    快路径：读首 4MB 找 "properties" 块 raw_decode（覆盖大文件）；
    失败且文件 ≤25MB → 全量 json.load；仍失败 → None（调用方降级为仅政策校验·不硬拒）。
    """
    try:
        size = os.path.getsize(path)
        if size > _FULL_LOAD_LIMIT_MB * 1024 * 1024:
            with open(path, 'r', encoding='utf-8') as fh:
                chunk = fh.read(4 * 1024 * 1024)
            keys = set()
            decoder = json.JSONDecoder()
            idx = 0
            for _ in range(3):
                pos = chunk.find('"properties"', idx)
                if pos < 0:
                    break
                brace = chunk.find('{', pos)
                if brace < 0:
                    break
                try:
                    obj, _ = decoder.raw_decode(chunk[brace:])
                    keys.update(k for k in (obj or {}) if isinstance(k, str))
                except ValueError:
                    break
                idx = brace + 1
            return keys or None
        with open(path, 'r', encoding='utf-8') as fh:
            fc = json.load(fh)
        keys = set()
        for f in (fc.get('features') or [])[:3]:
            keys.update((f.get('properties') or {}).keys())
        return keys or None
    except (OSError, ValueError):
        return None


def dataset_field_names(dataset_id):
    """dataset 实际要素属性字段集（读文件·preset 与点层皆可）。未知/不可读 → None（降级仅政策校验）。"""
    path = _dataset_file_path(dataset_id)
    if not path or not os.path.exists(path):
        return None
    return _first_feature_props(path)


def field_allowed(field, dataset_id=''):
    """字段能否经渲染通道透传（静态键/前缀/preset 声明三层并集）。"""
    if not field:
        return False
    if field in DATASET_PROP_KEYS:
        return True
    return field in preset_render_fields(dataset_id)


def renderable_fields(dataset_id):
    """前端真正能收到的字段（实际字段 ∩ 政策·用于错误提示）。实际读不到 → 政策集。"""
    actual = dataset_field_names(dataset_id)
    if actual is None:
        allowed = {f for f in DATASET_PROP_KEYS}
        allowed |= preset_render_fields(dataset_id)
        return allowed
    return {f for f in actual if field_allowed(f, dataset_id)}
