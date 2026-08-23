# -*- coding: utf-8 -*-
"""SHELL2(FIX) FIX-08：S4 引擎发射层（createEngineEmitter）wire 事件流过 S6 真实校验器。

补审计缺口 C5-1（此前仅 BA 降级形态过校验器·S4 主路只过了 node 镜像）。
驱动：node tests/acp_schema/s4_wire_dump.mjs（fake hooks 全 14 方法·无浏览器）→ 三断言：
  1. 四族（msg_delta/tool_begin/tool_end/error）wire 逐个过 jsonschema 真校验·
     未定稿族（turn/render）不得带 wire；
  2. 过程族事件信封 provenance 恒 'real'（轻循环引擎·契约 §五-1）；
  3. 分层纪律：render→content / 其余→process·六族齐·toolcall begin/end 配对。
node 缺席时 skip（双机差异注记）。
"""
import json
import subprocess
from pathlib import Path

import jsonschema
import pytest
from jsonschema import Draft202012Validator

HERE = Path(__file__).parent
DUMP = HERE / 's4_wire_dump.mjs'
SCHEMA_DIR = HERE / 'schemas'

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
        pytest.fail(f's4_wire_dump.mjs 失败: {proc.stderr[-400:]}')
    return json.loads(proc.stdout)['events']


def _validator(name):
    return Draft202012Validator(
        json.loads((SCHEMA_DIR / f'{name}.schema.json').read_text(encoding='utf-8')),
        format_checker=jsonschema.FormatChecker(),
    )


def test_s4_wire_pass_schemas():
    """断言 1：四族 wire 过真实 schema 校验；turn/render 未定稿族不带 wire。"""
    events = _dump_events()
    checked = 0
    for e in events:
        name = FAMILY_TO_SCHEMA.get(e['family'])
        if not name:
            assert e['wire'] is None, f"未定稿族不得带 wire: {e['family']}"
            continue
        if e['family'] == 'tool.begin' and e['sub'] == 'thought':
            continue   # thought 子型无 wire（与 call 子型区分·设计如此）
        assert e['wire'], f"{e['family']} 事件缺 wire: {e}"
        _validator(name).validate(e['wire'])
        checked += 1
    assert checked >= 6, f'wire 校验件数过少（实 {checked}）'


def test_s4_provenance_real():
    """断言 2：过程族信封 provenance 恒 real（轻循环引擎·非降级形态）。"""
    events = _dump_events()
    for e in events:
        if e['family'] in ('msg.delta', 'tool.begin', 'tool.end', 'error'):
            assert e['provenance'] == 'real', f"S4 主路应恒 real: {e['family']}"


def test_s4_lane_and_coverage():
    """断言 3：分层纪律 + 六族覆盖 + toolcall 配对。"""
    events = _dump_events()
    fams = {e['family'] for e in events}
    assert fams == {'msg.delta', 'tool.begin', 'tool.end', 'turn', 'error', 'render'}, f'族不齐: {fams}'
    for e in events:
        expect = 'content' if e['family'] == 'render' else 'process'
        assert e['lane'] == expect, f"{e['family']} lane 应 {expect}: {e}"
    # toolcall 配对：begin(call) 与 end 的 wire.toolcall_id 两两相等
    begins = [e for e in events if e['family'] == 'tool.begin' and e['sub'] == 'call']
    ends = [e for e in events if e['family'] == 'tool.end']
    assert len(begins) == 2 and len(ends) == 2
    assert {b['wire']['toolcall_id'] for b in begins} == {e['wire']['toolcall_id'] for e in ends}
    # msg.delta seq 单调
    seqs = [e['wire']['seq'] for e in events if e['family'] == 'msg.delta']
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
