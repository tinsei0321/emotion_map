"""导出模块测试 — export_outlet_card_csv（出口卡 CSV 导出·CB-18 S-1 补证）。

覆盖（Codex CB-18 S-1 建议）：
  - UTF-8 BOM 前缀（Excel 兼容·对齐 _csv_bytes）
  - 列：outlet_id/name/scale/interface/fields 平铺/data_base/task_link/limitations/geo_label
  - 显式脱敏（SENSITIVE_FIELDS·防字段扩展带入敏感列）
  - 返回值三元组 (bytes, filename.csv, media_type)
"""
import csv
import io

from core.export import export_outlet_card_csv, SENSITIVE_FIELDS


def _decode(data: bytes) -> str:
    return data.decode('utf-8')


def _read_rows(data: bytes) -> list[dict]:
    """解码（去 BOM）→ csv.DictReader 读取。"""
    text = _decode(data).lstrip('﻿')
    return list(csv.DictReader(io.StringIO(text)))


def test_export_outlet_card_csv_bom():
    """CSV 应有 UTF-8 BOM 前缀（Excel 兼容·对齐 _csv_bytes 约定）。"""
    data, fname, mtype = export_outlet_card_csv({}, filename='test_outlet')
    assert _decode(data).startswith('﻿'), 'CSV 应含 UTF-8 BOM 前缀'
    assert fname == 'test_outlet.csv', f'文件名应为 test_outlet.csv（{fname}）'
    assert mtype == 'text/csv; charset=utf-8', f'media_type 应为 text/csv（{mtype}）'


def test_export_outlet_card_csv_columns():
    """列应含 outlet_id/name/scale/interface + fields 平铺 + data_base + task_link + limitations + geo_label。"""
    card = {
        'outlet_id': 'renewal_demand',
        'name': '更新需求分析',
        'scale': 'meso',
        'interface': '问题清单',
        'fields': {
            '需求强度': {'value': '高'},
            '需求位置': {'value': '大南门'},
            '单一值': '纯值',
        },
        'data_base': {'N': 578, 'note': 'ermawu_l3l4_t3', 'total_points': 2400},
        'task_link': ['更新项目统计表', '满意度问卷'],
        'limitations': ['行业案例为对标参照·非评分基准'],
        'geo_label': '中观·单元：大南门',
        'source': 'sim',
    }
    data, _, _ = export_outlet_card_csv(card, filename='c')
    rows = _read_rows(data)
    assert len(rows) == 1, '应恰好一行数据'
    row = rows[0]
    assert row['outlet_id'] == 'renewal_demand'
    assert row['name'] == '更新需求分析'
    assert row['scale'] == 'meso'
    assert row['interface'] == '问题清单'
    # fields 平铺：dict 值取 value，非 dict 原样
    assert row['field_需求强度'] == '高'
    assert row['field_需求位置'] == '大南门'
    assert row['field_单一值'] == '纯值'
    # data_base 平铺
    assert row['data_base_N'] == '578'
    assert row['data_base_note'] == 'ermawu_l3l4_t3'
    assert row['data_base_total_points'] == '2400'
    # task_link/limitations 列表拼接
    assert row['task_link'] == '更新项目统计表、满意度问卷'
    assert row['limitations'] == '行业案例为对标参照·非评分基准'
    assert row['geo_label'] == '中观·单元：大南门'


def test_export_outlet_card_csv_desensitize():
    """显式脱敏：字段值精确命中 SENSITIVE_FIELDS 成员 → 整列剔除（防敏感值混入导出）。"""
    # 值精确命中 SENSITIVE_FIELDS（如「作者」「手机号」）→ 该列剔除；非敏感值保留
    card = {
        'outlet_id': 'renewal_demand',
        'fields': {
            '需求强度': {'value': '高'},
            '备注': {'value': '作者'},       # 值命中 SENSITIVE_FIELDS['作者'] → 整列剔除
            '联系方式': {'value': '手机号'}, # 值命中 SENSITIVE_FIELDS['手机号'] → 整列剔除
        },
    }
    data, _, _ = export_outlet_card_csv(card, filename='c')
    rows = _read_rows(data)
    assert len(rows) == 1
    row = rows[0]
    assert 'field_备注' not in row, '含敏感词"作者"的值应整列剔除'
    assert 'field_联系方式' not in row, '含敏感词"手机号"的值应整列剔除'
    assert row['field_需求强度'] == '高', '非敏感字段应保留'


def test_export_outlet_card_csv_empty_card():
    """空 card → 仍产出含 BOM 的合法 CSV（一行空字段·不崩溃）。"""
    data, fname, _ = export_outlet_card_csv({})
    assert _decode(data).startswith('﻿')
    assert fname == 'outlet_card.csv', f'默认文件名应为 outlet_card.csv（{fname}）'
    rows = _read_rows(data)
    assert len(rows) == 1
    # 无 outlet_id → 空字符串（不丢列）
    assert rows[0]['outlet_id'] == ''
