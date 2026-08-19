"""PT-CB2 复审修复 L3 · manifest schema 门禁包装（Codex 审计建议）。

把 tools/check_manifest.py 纳入 pytest 门禁：ERR 级问题（结构/必填/唯一性/usage 值域）
将直接红测，不再依赖人工记得跑脚本。WARN（存量文件缺失等）不阻断。
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, 'tools', 'check_manifest.py')


def test_manifest_schema_gate_zero_err():
    r = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', cwd=REPO)
    out = r.stdout or ''
    # 门禁语义：退出码 0 = 无 ERR（WARN 放行·存量项有主）
    assert r.returncode == 0, f'manifest schema 门禁失败:\n{out}\n{r.stderr or ""}'
    assert '[ERR] 校验未通过' not in out
    assert '[OK] 校验通过' in out
