"""PT-CB4 T3 · check_caliber 口径复核工具测试。

覆盖：
1. 千分位两种形态（5,615 与 5615）与百分比两种形态（87.9% 与 87.9）都命中 → exit 1；
2. 干净素材（现行口径值）不误报 → exit 0；
3. 命中清单含 文件/行号/命中值/卡 ID；
4. _retired/ 目录与注册表自身被排除（不把作废清单当命中）。
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import check_caliber as cc


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _make_registry(path, values):
    rows = '\n'.join(f'| **{v}** | 历史阶段值 | 已作废 | 现行卡 |' for v in values)
    text = f"""# 口径注册表（测试）

### X-01 作废数字清单

| 作废值 | 原语义 | 作废原因 | 替代 |
|---|---|---|---|
{rows}

- **状态**：作废
"""
    _write(path, text)
    return path


def _run(cc_mod, target, registry):
    return cc_mod.main([str(target), '--registry', str(registry)])


def test_comma_and_percent_both_forms_fail(tmp_path, capsys):
    """5,615/5615 与 87.9%/87.9 两种书写形态都要命中并 exit 1。"""
    reg = _make_registry(tmp_path / 'reg.md', ['5,615', '87.9%'])
    mat = tmp_path / 'material.md'
    _write(mat, '旧阶段值 5615 件\n旧占比 87.9\n')

    assert _run(cc, mat, reg) == 1

    out = capsys.readouterr().out
    assert 'material.md:1' in out and '5615' in out
    assert 'material.md:2' in out and '87.9' in out


def test_comma_form_hit_reports_card_and_line(tmp_path, capsys):
    """带千分位原文命中时输出 文件/行号/命中值/卡 ID。"""
    reg = _make_registry(tmp_path / 'reg.md', ['5,615'])
    mat = tmp_path / 'a.csv'
    _write(mat, '列1,列2\n其它,5,615\n')

    assert _run(cc, mat, reg) == 1

    out = capsys.readouterr().out
    assert 'a.csv:2' in out
    assert '5,615' in out
    assert 'X-01' in out


def test_clean_material_passes(tmp_path, capsys):
    """现行口径值（4,800/83.3%）不误报 → exit 0。"""
    reg = _make_registry(tmp_path / 'reg.md', ['5,615', '87.9%'])
    mat = tmp_path / 'ok.md'
    _write(mat, '现行口径：安全 4,800 件；三层占比 83.3%。\n')

    assert _run(cc, mat, reg) == 0
    assert '0 命中' in capsys.readouterr().out


def test_retired_dir_excluded(tmp_path, capsys):
    """_retired/ 目录内素材不扫描。"""
    reg = _make_registry(tmp_path / 'reg.md', ['5,615'])
    retired = tmp_path / '_retired' / 'old.md'
    _write(retired, '旧文命中 5,615\n')
    live = tmp_path / 'live.md'
    _write(live, '干净内容\n')

    assert _run(cc, tmp_path, reg) == 0
    assert '0 命中' in capsys.readouterr().out


def test_registry_self_excluded(tmp_path, capsys):
    """注册表自身（含作废清单）不算命中。"""
    target = tmp_path / 'docs'
    reg = _make_registry(target / 'reg.md', ['5,615'])
    _write(target / 'clean.md', '无作废值\n')

    assert _run(cc, target, reg) == 0
    assert '0 命中' in capsys.readouterr().out


def test_text_prefix_and_slash_compound_variants(tmp_path, capsys):
    """带文字前缀与斜杠复合作废值的紧凑/拆分写法也要命中。"""
    reg = _make_registry(tmp_path / 'reg.md', ['港务 1,153', '双高 16/32/3/26（各代）'])
    mat = tmp_path / 'm.md'
    _write(mat, '港务1153 件\n双高 32 个社区\n')

    assert _run(cc, mat, reg) == 1

    out = capsys.readouterr().out
    assert '港务1153' in out
    assert '双高 32' in out
    assert 'X-01' in out


def test_numeric_boundary_no_false_positive(tmp_path, capsys):
    """5615 不命中 15615/56150；裸 3 不因双高复合值误报。"""
    reg = _make_registry(tmp_path / 'reg.md', ['5,615', '双高 16/32/3/26（各代）'])
    mat = tmp_path / 'boundary.md'
    _write(mat, '数量 15615 与 56150 都不该命中\n单独数值 3 也不该命中\n')

    assert _run(cc, mat, reg) == 0
    assert '0 命中' in capsys.readouterr().out


def test_fullwidth_material_variants_hit(tmp_path, capsys):
    """素材全角数字/全角逗号千分位（５，６１５ / ８７．９％）与半角登记同义命中。"""
    reg = _make_registry(tmp_path / 'reg.md', ['5,615', '87.9%'])
    mat = tmp_path / 'full.md'
    _write(mat, '旧值 ５，６１５ 件\n旧占比 ８７．９％\n')

    assert _run(cc, mat, reg) == 1

    out = capsys.readouterr().out
    assert 'full.md:1' in out and '5,615' in out
    assert 'full.md:2' in out and '87.9%' in out


def test_fullwidth_registry_values_normalized(tmp_path, capsys):
    """注册表作废值本身为全角写法时，半角素材同样命中。"""
    reg = _make_registry(tmp_path / 'reg.md', ['５，６１５', '８７．９％'])
    mat = tmp_path / 'half.md'
    _write(mat, '旧值 5615 件\n旧占比 87.9\n')

    assert _run(cc, mat, reg) == 1

    out = capsys.readouterr().out
    assert 'half.md:1' in out and '5615' in out
    assert 'half.md:2' in out and '87.9' in out
