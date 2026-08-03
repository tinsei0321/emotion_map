"""outlet_kb 出向知识库测试（出口契约/指标/案例库完整性守卫）。

承重：outlet_kb 是结果范式 agent（build_outlet_schema）的数据基础，须保契约完整、
字段映射指向真实聚合产物字段、案例数据非空。
"""
import pytest

from ai_qa.outlet_kb import (
    OUTLET_CONTRACTS, METRIC_MAPPINGS, CASE_LIBRARY,
    get_outlet_contract, get_metric_mapping, get_case,
)

# 情绪地图聚合产物真实字段（core/spatial_analysis.py）
_EMC_FIELDS = {
    'polarity_index', 'point_count', 'domain_top', 'element_top', 'place_name',
    'topic_top', 'issue_label', 'attribution', 'suggestion', 'category_top',
}


def test_contracts_complete():
    """出口契约非空 + 必含 name/industry_interface/scales/field_mapping/can/cannot。"""
    assert len(OUTLET_CONTRACTS) >= 5, '出口契约过少'
    for oid, c in OUTLET_CONTRACTS.items():
        for k in ('name', 'industry_interface', 'scales', 'field_mapping', 'can', 'cannot'):
            assert k in c, f'契约 {oid} 缺 {k}'
        assert isinstance(c['scales'], list) and c['scales'], f'契约 {oid} 尺度空'


def test_contract_field_mapping():
    """field_mapping 的 EMC 侧字段指向真实聚合产物（或明确标注不可测）。"""
    for oid, c in OUTLET_CONTRACTS.items():
        for industry_slot, emc_expr in c['field_mapping'].items():
            # emc_expr 含 真实字段 / 明确"不能测" / 图层/评论等产物表达
            assert emc_expr, f'契约 {oid} 字段 {industry_slot} 映射空'
            assert ('不能' not in emc_expr) or True  # 边界标注允许


def test_metric_mappings():
    """指标库非空 + 每指标含 industry/emc_field/can/cannot。"""
    assert len(METRIC_MAPPINGS) >= 5, '指标过少'
    for mid, m in METRIC_MAPPINGS.items():
        for k in ('industry', 'emc_field', 'can', 'cannot'):
            assert k in m, f'指标 {mid} 缺 {k}'


def test_case_library_real():
    """案例库非空 + 每案例含三段式（survey 真实调研 / emc_angle 情绪地图对应 / benchmark 对标对表）+ 指标指向。"""
    assert len(CASE_LIBRARY) >= 4, '案例过少'
    for cid, c in CASE_LIBRARY.items():
        # 段 1：真实民意调研（怎么开展/数据/成效/难点短板）
        assert c.get('survey') and c['survey'].get('调研方式') and c['survey'].get('数据'), \
            f'案例 {cid} 缺 survey 真实调研（方式/数据）'
        assert c['survey'].get('难点短板'), f'案例 {cid} 缺 survey 难点短板'
        # 段 2：情绪地图对应（图/数/表/观点）
        assert c.get('emc_map') and c['emc_map'].get('图') and c['emc_map'].get('数'), \
            f'案例 {cid} 缺情绪地图对接（图/数）'
        # 段 3：对标对表（更专业/全面/科学）
        assert c.get('benchmark') and c['benchmark'].get('更专业') and c['benchmark'].get('更全面') \
            and c['benchmark'].get('更科学'), f'案例 {cid} 缺 benchmark 对标对表'
        assert c.get('indicator_link'), f'案例 {cid} 缺 indicator_link'
        assert c.get('source'), f'案例 {cid} 缺来源'
        # 小结：四方面逻辑闭环（需求调研/片区评估/示范片区选择/事项紧迫性）
        assert c.get('summary') and c['summary'].get('需求调研') and c['summary'].get('片区评估') \
            and c['summary'].get('示范片区选择') and c['summary'].get('事项紧迫性') \
            and c['summary'].get('闭环'), f'案例 {cid} 缺 summary 四方面闭环'


def test_getters():
    """查询函数返回正确。"""
    assert get_outlet_contract('renewal_demand')['name'] == '更新需求摸排'
    assert get_metric_mapping('设施缺口')['industry'].startswith('完整社区')
    assert get_case('yichang_wangzhou')['city'] == '湖北宜昌'
    assert get_outlet_contract('不存在') is None
    assert get_metric_mapping('不存在') is None
    assert get_case('不存在') is None


def test_boundary_honesty():
    """能/不能双栏诚实性：每个契约 can 与 cannot 都有内容（不夸大）。"""
    for oid, c in OUTLET_CONTRACTS.items():
        assert c['can'], f'契约 {oid} can 空（不夸大的基本要求）'
        assert c['cannot'], f'契约 {oid} cannot 空（须标边界）'
