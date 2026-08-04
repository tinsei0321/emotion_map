"""CB-16 Wave 3 CI：出口消费字段 vs 聚合产物字段校验（防死字段/缺消费·Codex CI 守卫）。

权威源 ai_qa/outlet_kb/（OUTLET_CONTRACTS field_mapping + METRIC_MAPPINGS emc_field）：
- **死字段**：契约/指标引用了聚合产物不存在的字段 → CI fail（硬错·防"分析了很多行业用不上"）
- **缺消费**：产物有字段但契约没用 → warning（软提醒·非 fail）

产物字段白名单（_EMC_FIELDS + 动态前缀 n_dom_*/n_elem_*/n_*·来自 core/spatial_analysis.py 聚合）。

跑：py -m pytest tests/validate_outlet_fields.py -q
"""
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

# 聚合产物真实字段白名单（core/spatial_analysis.py 产出 + 动态前缀）
_EMC_FIELDS = {
    'polarity_index', 'point_count', 'domain_top', 'element_top', 'place_name',
    'topic_top', 'issue_label', 'attribution', 'suggestion', 'category_top',
    'poi_names', 'place_name_source', 'nearest_poi_name', 'nearest_poi_dist_m',
    'score_mean', 'l1_confidence_mean', 'emotion_intensity_mean',
}
# 动态前缀字段（n_dom_*/n_elem_*/n_* 极性计数·前缀级消费合法）
_DYN_PREFIXES = ('n_dom_', 'n_elem_', 'n_')


def _extract_contract_fields():
    """提取 OUTLET_CONTRACTS field_mapping 引用的字段（ASCII 标识符·去 qualifier/说明/scale）。"""
    from ai_qa.outlet_kb.build_outlet_schema import OUTLET_CONTRACTS
    consumed = set()
    for contract in OUTLET_CONTRACTS.values():
        for expr in (contract.get('field_mapping') or {}).values():
            _e = re.sub(r'\[scale=[a-z]+\]', '', str(expr))   # 剥 scale 限定（micro/meso/macro 非字段）
            for m in re.findall(r'[a-z_][a-z0-9_]*', _e):
                if m not in ('图层', '评论', '不能测'):
                    consumed.add(m)
    return consumed


def _extract_metric_fields():
    """提取 METRIC_MAPPINGS emc_field 引用的字段（'字段A=值 + 字段B（关键词）' 拆·取 ASCII 标识符字段）。

    字段名都是 ASCII 标识符（element_top/topic_top/polarity_index 等）·中文是说明/关键词（"4×5 归因综合"/"城市舒适度值"）·
    用正则 [a-z_][a-z0-9_]* 只收真实字段·跳过纯中文说明段。
    """
    from ai_qa.outlet_kb.urban_checkup_outlets import METRIC_MAPPINGS
    consumed = set()
    for metric in METRIC_MAPPINGS.values():
        _e = str(metric.get('emc_field') or '')
        for m in re.findall(r'[a-z_][a-z0-9_]*', _e):
            consumed.add(m)
    return consumed


def _is_valid(field):
    """字段合法：白名单内 或 动态前缀匹配（n_dom_* 等）。"""
    if field in _EMC_FIELDS:
        return True
    return any(field.startswith(p) for p in _DYN_PREFIXES)


def test_no_dead_fields_in_contracts():
    """契约 field_mapping 引用字段都应存在于聚合产物（死字段 → fail·防"暂无数据"）。"""
    consumed = _extract_contract_fields()
    dead = sorted(f for f in consumed if not _is_valid(f))
    assert not dead, f'死字段（契约引用·产物不存在）：{dead}——需在聚合层产出或改契约'


def test_no_dead_fields_in_metrics():
    """METRIC_MAPPINGS emc_field 引用字段都应存在于聚合产物。"""
    consumed = _extract_metric_fields()
    dead = sorted(f for f in consumed if not _is_valid(f))
    assert not dead, f'死字段（指标引用·产物不存在）：{dead}'


if __name__ == '__main__':
    # 手动跑：打印缺消费警告（软提醒）
    from ai_qa.outlet_kb.build_outlet_schema import OUTLET_CONTRACTS
    all_consumed = _extract_contract_fields() | _extract_metric_fields()
    unused = sorted(f for f in _EMC_FIELDS if f not in all_consumed)
    print(f'[WARN] 产物字段未消费：{unused}' if unused else '[OK] 产物字段全被消费')
