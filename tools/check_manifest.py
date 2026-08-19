#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PT-CB2 T3 · manifest 登记表一次性校验脚本（B1 验收项）。

校验 DATA/boundaries/presets/manifest.json（图层户口登记表）：
  1. JSON 可解析 + 顶层结构（list of {group, items[]}）          [ERR]
  2. item 必填字段 id/label/file                                 [ERR]
  3. id 跨组唯一                                                 [ERR]
  4. usage 值域 {input, analysis_output} + 全覆盖统计            [缺失 WARN]
  5. file 路径存在性（相对 presets 目录解析·含 ../../analysis/） [缺失 WARN]
  6. nameField 缺失提示                                          [WARN]

  注：snapshot 与 usage 为正交维度（snapshot=物理快照视图·防双头权威；usage=原料/结论语义）——
  input 底座同时为快照是 T1 合法设计，不做一致性校验（首版误设此规则·实测 4 误报后移除）。

exit code：有 ERR → 1（可挂 CI）；仅 WARN → 0。

用法：py tools/check_manifest.py [manifest路径]（缺省仓库内默认路径）。
追踪：一次性验收工具（无 @track——非运行时业务模块，同 gen_stages_mirror 惯例）。
"""


def _safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('gbk', 'replace').decode('gbk'))


import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = os.path.join(REPO, 'DATA', 'boundaries', 'presets', 'manifest.json')

_ERR, _WARN = 0, 0


def _err(msg):
    global _ERR
    _ERR += 1
    _safe_print(f'[ERR] {msg}')


def _warn(msg):
    global _WARN
    _WARN += 1
    _safe_print(f'[WARN] {msg}')


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    presets_dir = os.path.dirname(path)

    if not os.path.isfile(path):
        _err(f'manifest 不存在: {path}')
        return 1
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception as e:
        _err(f'JSON 解析失败: {e}')
        return 1
    _safe_print(f'[OK] JSON 可解析: {path}')

    if not isinstance(data, list) or not all(isinstance(g, dict) for g in data):
        _err('顶层结构应为 group 数组 [{group, items[]}]')
        return 1
    _safe_print(f'[OK] 顶层结构: {len(data)} groups')

    seen_ids, usage_stat, snapshot_ok = {}, {'input': 0, 'analysis_output': 0, None: 0}, 0
    for g in data:
        gname = g.get('group') or '(未命名组)'
        items = g.get('items')
        if not isinstance(items, list):
            _err(f'group「{gname}」items 非列表')
            continue
        for it in items:
            iid = it.get('id')
            if not iid or not it.get('label') or not it.get('file'):
                _err(f'group「{gname}」item 必填字段缺失（id/label/file）: {json.dumps(it, ensure_ascii=False)[:80]}')
                continue
            if iid in seen_ids:
                _err(f'id 重复: {iid}（{seen_ids[iid]} 与 {gname}）')
            else:
                seen_ids[iid] = gname
            if 'nameField' not in it:
                _warn(f'{iid}: 无 nameField（前端 where 构造与名称列规范依赖它）')
            usage = it.get('usage')
            if usage in ('input', 'analysis_output'):
                usage_stat[usage] += 1
            else:
                usage_stat[None] += 1
                _warn(f'{iid}: usage 缺失/非法（{usage!r}·守卫将按未注册放行）')
            if it.get('snapshot'):
                snapshot_ok += 1
            # 路径存在性（相对 presets 目录；reference_only/missing 属存量治理项→WARN 不 ERR）
            f = it.get('file', '')
            full = os.path.normpath(os.path.join(presets_dir, f))
            if not os.path.isfile(full):
                note = (it.get('note') or '')
                tag = 'reference_only' if 'reference' in note else ('标 missing' if 'missing' in note else '文件缺失')
                _warn(f'{iid}: file 不存在（{tag}）: {f}')

    total = sum(len(g.get('items', [])) for g in data if isinstance(g.get('items'), list))
    _safe_print(f'[OK] 层数: {total}（id 唯一 {len(seen_ids)}）| usage: input={usage_stat["input"]} '
                f'analysis_output={usage_stat["analysis_output"]} 未标={usage_stat[None]} | snapshot: {snapshot_ok}')

    if _ERR:
        _safe_print(f'[ERR] 校验未通过: {_ERR} err / {_WARN} warn')
        return 1
    _safe_print(f'[OK] 校验通过: 0 err / {_WARN} warn')
    return 0


if __name__ == '__main__':
    sys.exit(main())
