"""PT-CB2 复审修复 L3 · manifest schema 门禁包装（Codex 审计建议）。

把 tools/check_manifest.py 纳入 pytest 门禁：ERR 级问题（结构/必填/唯一性/usage 值域）
将直接红测，不再依赖人工记得跑脚本。WARN（存量文件缺失等）不阻断。
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, 'tools', 'check_manifest.py')


def _decode_output(data):
    """Windows GBK/UTF-8 输出自适配：先严格 UTF-8，再 GBK，最后替换兜底。"""
    if not data:
        return ''
    for enc in ('utf-8', 'gbk'):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode('utf-8', errors='replace')


def test_manifest_schema_gate_zero_err():
    r = subprocess.run([sys.executable, SCRIPT], capture_output=True, cwd=REPO)
    out = _decode_output(r.stdout)
    err = _decode_output(r.stderr)
    # 门禁语义：退出码 0 = 无 ERR（WARN 放行·存量项有主）
    assert r.returncode == 0, f'manifest schema 门禁失败:\n{out}\n{err}'
    assert '[ERR] 校验未通过' not in out
    assert '[OK] 校验通过' in out
