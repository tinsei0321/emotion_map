# -*- coding: utf-8 -*-
"""壳二期件① · BrainAdapter dsh 适配器事件流 schema 校验（SHELL2(BA)·Qoder·2026-08-23）。

覆盖（契约 docs/brain-adapter.md §三验收三条中的 1/3）：
  1. wire 兼容性：BA 发出的 msg_delta/tool_begin/tool_end/error 四族 wire 对象
     逐个过 tests/acp_schema/schemas/*.schema.json（真实 jsonschema 校验·非镜像）；
  2. 降级形态诚实性：BA 发出的全部 msg.delta/tool.*/error 信封 provenance 恒 'synthesized'
     （契约 §三-3——缺省即违规）；turn 族无 provenance 惯例（与 S4 引擎发射层一致）；
  3. 过程-内容分层：全部事件 lane=process（BA 不发 render 族——dsh 输出经 seal 渲染）。

驱动：node tests/acp_schema/ba_wire_dump.mjs（fake fetch·无网络无浏览器）→ stdout JSON。
node 缺席时 skip（双机差异：office/home 均有 node·CI 无则跳过不红）。
"""
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest
from jsonschema import Draft202012Validator

HERE = Path(__file__).parent
DUMP = HERE / 'ba_wire_dump.mjs'
SCHEMA_DIR = HERE / 'schemas'

# bus family → wire schema 名映射（turn/render 族 wire 未定稿·不校验 wire）
FAMILY_TO_SCHEMA = {
    'msg.delta': 'msg_delta',
    'tool.begin': 'tool_begin',
    'tool.end': 'tool_end',
    'error': 'error',
}


def _dump_events():
    try:
        proc = subprocess.run(
            ['node', str(DUMP)], capture_output=True, text=True,
            encoding='utf-8', timeout=60, cwd=str(HERE),
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip('node 不可用（双机差异·本机装 node 后跑）')
    if proc.returncode != 0:
        pytest.fail(f'ba_wire_dump.mjs 失败: {proc.stderr[-400:]}')
    return json.loads(proc.stdout)['events']


def _validator(name):
    return Draft202012Validator(
        json.loads((SCHEMA_DIR / f'{name}.schema.json').read_text(encoding='utf-8')),
        format_checker=jsonschema.FormatChecker(),
    )


def test_ba_wire_events_pass_schemas():
    """四族 wire 对象逐个过真实 schema 校验器（S6 资产直接消费——「过 S6 校验器」红线）。"""
    events = _dump_events()
    checked = 0
    for e in events:
        name = FAMILY_TO_SCHEMA.get(e['family'])
        if not name:
            assert e['wire'] is None, f"{e['family']} 族不应带 wire（schema 未定稿）: {e}"
            continue
        assert e['wire'], f"{e['family']} 事件缺 wire 对象: {e}"
        _validator(name).validate(e['wire'])   # 不抛即过（字段级错误由 jsonschema 抛出）
        checked += 1
    assert checked >= 6, f'wire 校验件数过少（实 {checked}·应含 桩/配对/ping×N/全文/失败 error）'


def test_ba_degraded_form_provenance_honesty():
    """降级形态诚实性：msg.delta/tool.*/error 信封 provenance 恒 synthesized（契约 §三-3）。"""
    events = _dump_events()
    for e in events:
        if e['family'] in ('msg.delta', 'tool.begin', 'tool.end', 'error'):
            assert e['provenance'] == 'synthesized', \
                f"BA 事件 provenance 非 synthesized（伪装真流式·违规）: {e['family']} {e.get('kind') or e.get('verb')}"


def test_ba_lane_and_families():
    """分层与族齐：全部 process lane；含 turn(diagnose/seal)/tool.begin 桩/tool.end/msg.delta reason+content/error。"""
    events = _dump_events()
    assert all(e['lane'] == 'process' for e in events), 'BA 事件应全走 process lane（不发 render 族）'
    fams = {e['family'] for e in events}
    assert {'turn', 'tool.begin', 'tool.end', 'msg.delta', 'error'} <= fams, f'族不齐: {fams}'
    kinds = {(e['family'], e.get('kind')) for e in events}
    assert ('msg.delta', 'reason') in kinds and ('msg.delta', 'content') in kinds, '缺 ping 桩或全文批量'
    verbs = {(e['family'], e.get('verb'), e.get('phase')) for e in events}
    assert ('turn', 'step', 'diagnose') in verbs and ('turn', 'seal', None) in verbs, '缺 diagnose 卡或 seal 定稿'
