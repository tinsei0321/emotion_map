# -*- coding: utf-8 -*-
"""壳阶段 S6 · ACP 事件 schema 校验器 pytest 桩（dsh · 2026-08-23）。

覆盖：
  1. schema 文件齐全性——五族事件（msg.delta/tool.begin/tool.end/error/approval.req）
     + 三状态对象（session/turn/toolcall）·目录无孤儿 schema；
  2. 每份 schema 过 draft 2020-12 metaschema（Draft202012Validator.check_schema）；
  3. 给定事件 JSON → 校验通过断言（每族一个合法样例）；
  4. 故坏样例 → 校验失败断言（每族 2-3 坏例·错误定位到字段路径/消息·防误过）。

依赖注记：S2 v1.1 增补（kind 子类型/provenance/载荷结构）未定稿——本桩只按 v1 骨架；
v1.1 落地后补 schema 增量（版本注记位=tests/acp_schema/README.md §二 + 各 schema $comment）。
权威源：docs/acp-contract-v1.md。
"""
import json
from pathlib import Path

import pytest
import jsonschema
from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).parent / 'schemas'

# 五族事件（契约 §二）+ 三状态对象（契约 §三）
FAMILIES = {
    'msg_delta', 'tool_begin', 'tool_end', 'error', 'approval_req',
    'session', 'turn', 'toolcall',
}

VALID = {
    'msg_delta': {'kind': 'content', 'delta': '好', 'session_id': 's1',
                  'turn_id': 't1', 'seq': 0},
    'tool_begin': {'toolcall_id': 'tc1', 'verb': 'zonal_stats', 'session_id': 's1',
                   'turn_id': 't1', 'params_summary': 'boundary=checkup_cfg_community'},
    'tool_end': {'toolcall_id': 'tc1', 'verb': 'zonal_stats', 'session_id': 's1',
                 'turn_id': 't1', 'result_summary': 'rows=20',
                 'caliber': {'scale': '社区单元', 'refs': ['K-C1']}},
    'error': {'code': 'RAG_INDEX_MISSING', 'message': '索引未构建',
              'hint': 'py tools/rag_index.py --build', 'session_id': 's1'},
    'approval_req': {'id': 'ar1', 'action': 'kb_inbox.write', 'session_id': 's1',
                     'reason': '支柱二草拟层写入'},
    'session': {'id': 's1', 'topic': '望洲岗更新咨询',
                'opened_at': '2026-08-23T10:00:00Z', 'status': 'open'},
    'turn': {'id': 't1', 'session_id': 's1', 'intent': 'knowledge', 'status': 'acting'},
    'toolcall': {'id': 'tc1', 'turn_id': 't1', 'verb': 'rank', 'status': 'begin',
                 'caliber': {'scale': '社区单元', 'refs': ['K-C1']}},
}

# 故坏样例：(族, 坏样, 期望定位字段)——错误断言须落到字段级（防误过）
INVALID = [
    # msg_delta：kind 枚举越界 / 缺必填 / 多字段 / 空串
    ('msg_delta', {'kind': 'thought', 'delta': 'x', 'session_id': 's', 'turn_id': 't'}, 'kind'),
    ('msg_delta', {'kind': 'content', 'session_id': 's', 'turn_id': 't'}, 'delta'),
    ('msg_delta', {'kind': 'content', 'delta': 'x', 'session_id': 's',
                   'turn_id': 't', 'payload': 'x'}, 'payload'),
    ('msg_delta', {'kind': 'content', 'delta': '', 'session_id': 's', 'turn_id': 't'}, 'delta'),
    # tool_begin：缺 verb / verb 空串 / 多字段（完整参数应走 params_summary）
    ('tool_begin', {'toolcall_id': 'tc', 'session_id': 's', 'turn_id': 't'}, 'verb'),
    ('tool_begin', {'toolcall_id': 'tc', 'verb': '', 'session_id': 's', 'turn_id': 't'}, 'verb'),
    ('tool_begin', {'toolcall_id': 'tc', 'verb': 'rank', 'session_id': 's',
                    'turn_id': 't', 'params': {}}, 'params'),
    # tool_end：缺 turn_id / caliber refs 空 / result_summary 类型错
    ('tool_end', {'toolcall_id': 'tc', 'verb': 'rank', 'session_id': 's'}, 'turn_id'),
    ('tool_end', {'toolcall_id': 'tc', 'verb': 'rank', 'session_id': 's',
                  'turn_id': 't', 'caliber': {'refs': []}}, 'refs'),
    ('tool_end', {'toolcall_id': 'tc', 'verb': 'rank', 'session_id': 's',
                  'turn_id': 't', 'result_summary': 20}, 'result_summary'),
    # error：缺 code / hint 类型错 / session_id 空串
    ('error', {'message': 'm', 'session_id': 's'}, 'code'),
    ('error', {'code': 'X', 'message': 'm', 'session_id': 's', 'hint': 3}, 'hint'),
    ('error', {'code': 'X', 'message': 'm', 'session_id': ''}, 'session_id'),
    # approval_req：缺 action / 多字段（审批不可自带放行开关）
    ('approval_req', {'id': 'ar', 'session_id': 's'}, 'action'),
    ('approval_req', {'id': 'ar', 'action': 'kb_inbox.write', 'session_id': 's',
                      'auto_approve': True}, 'auto_approve'),
    # session：status 枚举越界 / opened_at 非 date-time
    ('session', {'id': 's', 'opened_at': '2026-08-23T10:00:00Z', 'status': 'paused'}, 'status'),
    ('session', {'id': 's', 'opened_at': 'yesterday', 'status': 'open'}, 'opened_at'),
    # turn：status 枚举越界 / 缺 session_id
    ('turn', {'id': 't', 'session_id': 's', 'status': 'waiting'}, 'status'),
    ('turn', {'id': 't', 'status': 'done'}, 'session_id'),
    # toolcall：status 枚举越界 / 缺 verb
    ('toolcall', {'id': 'tc', 'turn_id': 't', 'verb': 'rank', 'status': 'running'}, 'status'),
    ('toolcall', {'id': 'tc', 'turn_id': 't', 'status': 'begin'}, 'verb'),
]


def _load(name):
    return json.loads((SCHEMA_DIR / f'{name}.schema.json').read_text(encoding='utf-8'))


def _validator(name):
    # format_checker 必开——jsonschema 默认不强制 format（否则 opened_at 非 date-time 会误过）
    return Draft202012Validator(_load(name), format_checker=jsonschema.FormatChecker())


# ════════════ 1 · 齐全性 + metaschema ════════════

def test_schema_files_complete_and_valid():
    for name in FAMILIES:
        assert (SCHEMA_DIR / f'{name}.schema.json').is_file(), f'schema 缺失: {name}'
    orphans = sorted(p.stem.split('.')[0] for p in SCHEMA_DIR.glob('*.schema.json')
                     if p.stem.split('.')[0] not in FAMILIES)
    assert not orphans, f'schema 目录孤儿（未登记族）: {orphans}'
    for name in FAMILIES:
        Draft202012Validator.check_schema(_load(name))   # metaschema 校验·不抛即过


# ════════════ 2 · 合法样例通过 ════════════

@pytest.mark.parametrize('name', sorted(FAMILIES))
def test_valid_sample_passes(name):
    _validator(name).validate(VALID[name])


# ════════════ 3 · 故坏样例失败（字段级定位） ════════════

@pytest.mark.parametrize('name,sample,field',
                         INVALID,
                         ids=[f'{n}:{f}' for n, _s, f in INVALID])
def test_invalid_sample_fails(name, sample, field):
    with pytest.raises(jsonschema.exceptions.ValidationError) as ei:
        _validator(name).validate(sample)
    located = field in str(ei.value.message) or field in list(ei.value.path)
    assert located, f'{name} 坏样未定位到字段 {field}: message={ei.value.message} path={list(ei.value.path)}'
