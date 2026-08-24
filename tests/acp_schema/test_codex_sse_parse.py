# -*- coding: utf-8 -*-
"""PT-CB15 PROMOTE P2-7/P2-11：SSE 帧解析离线测（node 桥式·同源 ba_wire_dump 测法）。

驱动：node tests/acp_schema/codex_sse_parse_dump.mjs → stdout JSON。
断言：LF 多帧 / CRLF 归一化 / 尾部残留 / 噪音帧 / 空输入。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

HERE = Path(__file__).resolve().parent
DUMP = HERE / 'codex_sse_parse_dump.mjs'


@pytest.fixture(scope='module')
def dump():
    if shutil.which('node') is None:
        pytest.skip('node 不在 PATH')
    proc = subprocess.run(['node', str(DUMP)], capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        pytest.fail(f'codex_sse_parse_dump.mjs 失败: {proc.stderr[-400:]}')
    return json.loads(proc.stdout.strip())


def test_lf_two_frames(dump):
    r = dump['lf_two']
    assert len(r['frames']) == 2
    assert r['frames'][0]['ev'] == 'delta'
    assert json.loads(r['frames'][0]['data'])['n'] == 1
    assert r['frames'][1]['ev'] == 'done'
    assert r['rest'] == ''


def test_crlf_frames(dump):
    r = dump['crlf']   # P2-11：CRLF 帧分隔等价解析
    assert len(r['frames']) == 2
    assert [f['ev'] for f in r['frames']] == ['delta', 'ping']
    assert json.loads(r['frames'][0]['data'])['n'] == 2
    assert r['rest'] == ''


def test_trailing_partial(dump):
    r = dump['trailing']
    assert len(r['frames']) == 1          # 完整帧提取
    assert r['frames'][0]['ev'] == 'delta'
    assert r['rest'].startswith('event: tool')   # 未完成尾部残留待下一 chunk


def test_mixed_noise_frame(dump):
    r = dump['mixed']
    # 完整帧：delta + 噪音帧（只有 data·ev 空仍算帧供上层丢弃）+ CRLF tool 帧
    assert len(r['frames']) == 3
    assert r['frames'][0]['ev'] == 'delta'
    assert r['frames'][1]['ev'] == '' and r['frames'][1]['data']
    assert r['frames'][2]['ev'] == 'tool'
    assert r['rest'] == ''


def test_empty_input(dump):
    r = dump['empty']
    assert r['frames'] == [] and r['rest'] == ''
