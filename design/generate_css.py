"""
Design Token Generator — 将 tokens.json 编译为 CSS 变量和 Python 常量
======================================================================
用法: python design/generate_css.py

支持 Light/Dark 双主题:
  tokens.json 包含 theme.dark 和 theme.light 两套颜色/组件 token
  输出 CSS 通过 prefers-color-scheme 媒体查询 + [data-theme] 属性切换

输出:
  design/tokens.css   — CSS 自定义属性（含媒体查询和 data-theme 选择器）
  design/tokens.py    — Python 常量模块 + LIGHT_TOKENS / DARK_TOKENS 字典

约束:
  - 仅依赖 Python 标准库 (json, re, os, pathlib)
  - 自动解析 token 引用 {path.to.token}
"""

import json
import re
import os
from pathlib import Path


# ── 路径 ──────────────────────────────────────────────────
DESIGN_DIR = Path(__file__).resolve().parent
TOKENS_JSON = DESIGN_DIR / 'tokens.json'
OUT_CSS = DESIGN_DIR / 'tokens.css'
OUT_PY = DESIGN_DIR / 'tokens.py'


# ── 工具函数 ──────────────────────────────────────────────
def camel_to_kebab(name: str) -> str:
    """camelCase → kebab-case"""
    return re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', name).lower()


def camel_to_snake_upper(name: str) -> str:
    """camelCase → SNAKE_UPPER_CASE"""
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    return s.upper()


# ── 展平 JSON → 扁平字典 ──────────────────────────────────
def flatten_tokens(data: dict, prefix: str = '') -> dict:
    """递归展平 JSON 树，返回 { 'key-name': 'value', ... }"""
    result = {}
    for key, value in data.items():
        kebab_key = camel_to_kebab(key)
        full_key = f'{prefix}-{kebab_key}' if prefix else kebab_key
        if isinstance(value, dict):
            result.update(flatten_tokens(value, full_key))
        else:
            result[full_key] = str(value)
    return result


# ── 引用解析 ──────────────────────────────────────────────
REF_PATTERN = re.compile(r'\{([a-zA-Z0-9_.-]+)\}')


def resolve_references(flat: dict, max_passes: int = 10) -> dict:
    """多轮解析 token 引用 {path.to.token}"""
    resolved = dict(flat)
    for _ in range(max_passes):
        changed = False
        for key, value in resolved.items():
            if not isinstance(value, str):
                continue
            new_value = value
            full_match = REF_PATTERN.fullmatch(new_value.strip())
            if full_match:
                ref_path = full_match.group(1)
                if ref_path in resolved:
                    new_value = resolved[ref_path]
                    if new_value != value:
                        changed = True
            elif '{' in new_value:
                def replacer(m):
                    ref_path = m.group(1)
                    return resolved.get(ref_path, m.group(0))
                new_new = REF_PATTERN.sub(replacer, new_value)
                if new_new != new_value:
                    new_value = new_new
                    changed = True
            if new_value != value:
                resolved[key] = new_value
        if not changed:
            break
    return resolved


# ── CSS 生成 ──────────────────────────────────────────────
CSS_HEADER = '''/* ══════════════════════════════════════════════════════════════
   Design Tokens — Auto-generated from design/tokens.json
   DO NOT EDIT MANUALLY — Run: python design/generate_css.py
   Supports: prefers-color-scheme + [data-theme] manual toggle
   ══════════════════════════════════════════════════════════════ */

/* ── 基础 Token（与主题无关） ── */
:root {
'''


def token_key_to_css_var(key: str) -> str:
    return f'--{key}'


def format_css_block(flat_tokens: dict, indent: str = '  ') -> str:
    """将扁平 token 字典格式化为 CSS 属性块"""
    lines = []
    categories = {}
    for key, value in sorted(flat_tokens.items()):
        cat = key.split('-')[0]
        categories.setdefault(cat, []).append((key, value))
    for cat in sorted(categories):
        lines.append(f'{indent}/* {cat} */')
        for key, value in categories[cat]:
            lines.append(f'{indent}{token_key_to_css_var(key)}: {value};')
        lines.append('')
    return '\n'.join(lines)


def generate_css(base_tokens: dict, dark_tokens: dict, light_tokens: dict) -> str:
    """生成支持双主题的完整 CSS"""
    parts = [CSS_HEADER]
    parts.append(format_css_block(base_tokens, '  '))
    parts.append('}\n')

    # 默认暗色主题（fallback）
    parts.append('/* ── 默认暗色主题 ── */')
    parts.append(':root {')
    parts.append(format_css_block(dark_tokens, '  '))
    parts.append('}\n')

    # prefers-color-scheme: light
    parts.append('/* ── 系统浅色模式（自动跟随 OS 设置） ── */')
    parts.append('@media (prefers-color-scheme: light) {')
    parts.append('  :root {')
    parts.append(format_css_block(light_tokens, '    '))
    parts.append('  }')
    parts.append('}\n')

    # 手动切换 [data-theme]
    parts.append('/* ── 手动主题切换（JS 设置 data-theme 属性） ── */')
    parts.append('[data-theme="light"] {')
    parts.append(format_css_block(light_tokens, '  '))
    parts.append('}\n')
    parts.append('[data-theme="dark"] {')
    parts.append(format_css_block(dark_tokens, '  '))
    parts.append('}\n')

    return '\n'.join(parts)


# ── Python 常量生成 ────────────────────────────────────────
PY_HEADER = '''# ══════════════════════════════════════════════════════════════
# Design Tokens — Auto-generated from design/tokens.json
# DO NOT EDIT MANUALLY — Run: python design/generate_css.py
# ══════════════════════════════════════════════════════════════
#
# 支持 Light/Dark 双主题:
#   from design.tokens import DARK_TOKENS, LIGHT_TOKENS, get_token
#   primary = get_token('color-brand-primary', theme='dark')
#
# 向后兼容（默认 dark 主题常量）:
#   from design.tokens import COLOR_BRAND_PRIMARY, RADIUS_MD
#


'''

PY_RESERVED = {
    'from', 'import', 'class', 'def', 'return', 'if', 'else', 'elif',
    'try', 'except', 'finally', 'for', 'while', 'with', 'as', 'in',
    'not', 'and', 'or', 'is', 'lambda', 'None', 'True', 'False',
    'pass', 'break', 'continue', 'raise', 'yield', 'global', 'nonlocal',
    'del', 'assert', 'async', 'await',
}


def token_key_to_py_const(key: str) -> str:
    const = key.replace('-', '_').upper()
    if const in PY_RESERVED:
        const = f'TOKEN_{const}'
    return const


def py_value_repr(value: str) -> str:
    try:
        num = float(value)
        if num == int(num) and '.' not in value:
            return str(int(num))
        return value
    except ValueError:
        pass
    if "'" in value:
        return f'"{value}"'
    return f"'{value}'"


def generate_constants_block(flat_tokens: dict) -> str:
    """生成 Python 常量赋值代码"""
    lines = []
    categories = {}
    for key, value in sorted(flat_tokens.items()):
        cat = key.split('-')[0]
        categories.setdefault(cat, []).append((key, value))
    for cat in sorted(categories):
        lines.append(f'# ── {cat} ──')
        for key, value in categories[cat]:
            const_name = token_key_to_py_const(key)
            py_val = py_value_repr(value)
            lines.append(f'{const_name} = {py_val}')
        lines.append('')
    return '\n'.join(lines)


def generate_aggregate_dicts(flat_tokens: dict) -> str:
    """生成便捷聚合字典（COLOR, SPACING, RADIUS, EMOTION_COLORS）"""
    lines = []
    lines.append('# ── 便捷聚合 ──')
    lines.append('')
    lines.append('COLOR = {')
    for key, value in sorted(flat_tokens.items()):
        if key.startswith('color-'):
            const_name = token_key_to_py_const(key)
            lines.append(f'    {py_value_repr(key)}: {const_name},')
    lines.append('}')
    lines.append('')
    lines.append('SPACING = {')
    for key, value in sorted(flat_tokens.items()):
        if key.startswith('spacing-'):
            const_name = token_key_to_py_const(key)
            lines.append(f'    {py_value_repr(key)}: {const_name},')
    lines.append('}')
    lines.append('')
    lines.append('RADIUS = {')
    for key, value in sorted(flat_tokens.items()):
        if key.startswith('radius-'):
            const_name = token_key_to_py_const(key)
            lines.append(f'    {py_value_repr(key)}: {const_name},')
    lines.append('}')
    lines.append('')
    lines.append('EMOTION_COLORS = {')
    for key, value in sorted(flat_tokens.items()):
        if key.startswith('color-emotion-'):
            label = key.replace('color-emotion-', '')
            const_name = token_key_to_py_const(key)
            lines.append(f'    {py_value_repr(label)}: {const_name},')
    lines.append('}')
    lines.append('')
    return '\n'.join(lines)


def generate_python(base_tokens: dict, dark_tokens: dict, light_tokens: dict) -> str:
    """生成完整 Python tokens.py"""
    lines = [PY_HEADER]

    # 向后兼容：默认 dark 主题常量（平铺在模块顶层）
    lines.append('# ════════════════════════════════════════════════════════')
    lines.append('#  基础 Token（与主题无关）')
    lines.append('# ════════════════════════════════════════════════════════')
    lines.append('')
    lines.append(generate_constants_block(base_tokens))

    lines.append('# ════════════════════════════════════════════════════════')
    lines.append('#  Dark 主题 Token（向后兼容，默认值）')
    lines.append('# ════════════════════════════════════════════════════════')
    lines.append('')
    lines.append(generate_constants_block(dark_tokens))

    lines.append(generate_aggregate_dicts(dark_tokens))

    # 双主题字典
    lines.append('# ════════════════════════════════════════════════════════')
    lines.append('#  Light/Dark 双主题字典')
    lines.append('# ════════════════════════════════════════════════════════')
    lines.append('')

    lines.append('DARK_TOKENS = {')
    for key, value in sorted(dark_tokens.items()):
        lines.append(f'    {py_value_repr(key)}: {py_value_repr(value)},')
    lines.append('}')
    lines.append('')

    lines.append('LIGHT_TOKENS = {')
    for key, value in sorted(light_tokens.items()):
        lines.append(f'    {py_value_repr(key)}: {py_value_repr(value)},')
    lines.append('}')
    lines.append('')

    # 便捷函数 get_token()
    lines.append('''
def get_token(name: str, theme: str = 'dark') -> str:
    """获取指定主题的 token 值。

    参数:
        name: token 名称，如 'color-brand-primary', 'component-hud-button-background'
        theme: 'dark' | 'light'

    返回:
        token 字符串值；如未找到则返回空字符串

    示例:
        get_token('color-brand-primary', 'light')  # '#ff6b35'
        get_token('component-dialog-background', 'dark')  # 'rgba(0,0,0,0.55)'
    """
    if theme == 'light':
        return LIGHT_TOKENS.get(name, '')
    return DARK_TOKENS.get(name, '')
''')

    return '\n'.join(lines)


# ── 主流程 ─────────────────────────────────────────────────
def main():
    if not TOKENS_JSON.exists():
        print(f'[ERR] 找不到 {TOKENS_JSON}')
        return

    with open(TOKENS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. 提取各层 token
    theme_data = data.get('theme', {})
    dark_raw = theme_data.get('dark', {})
    light_raw = theme_data.get('light', {})

    # 2. 展平基础 token（typography, spacing, radius, shadow, effect）
    base_raw = {k: v for k, v in data.items() if k != 'theme'}
    base_flat = flatten_tokens(base_raw)
    base_flat = resolve_references(base_flat)

    # 3. 展平 Dark 主题 token
    dark_flat = flatten_tokens(dark_raw)
    dark_flat = resolve_references(dark_flat)

    # 4. 展平 Light 主题 token
    light_flat = flatten_tokens(light_raw)
    light_flat = resolve_references(light_flat)

    print(f'[OK] 展平: base={len(base_flat)}, dark={len(dark_flat)}, light={len(light_flat)}')

    # 5. 生成 CSS
    css_content = generate_css(base_flat, dark_flat, light_flat)
    with open(OUT_CSS, 'w', encoding='utf-8') as f:
        f.write(css_content)
    css_var_count = len([l for l in css_content.splitlines() if l.strip().startswith('--')])
    print(f'[OK] 生成 CSS → {OUT_CSS} ({len(css_content)} bytes, {css_var_count} CSS variables)')

    # 6. 生成 Python
    py_content = generate_python(base_flat, dark_flat, light_flat)
    with open(OUT_PY, 'w', encoding='utf-8') as f:
        f.write(py_content)
    py_const_count = len([l for l in py_content.splitlines() if ' = ' in l and not l.strip().startswith('#')])
    print(f'[OK] 生成 Python → {OUT_PY} ({len(py_content)} bytes, {py_const_count} constants)')

    # 7. 验证
    print(f'\n{"=" * 60}')
    print(f'Design Token 体系构建完成 (Light/Dark 双主题)')
    print(f'{"=" * 60}')
    print(f'  tokens.json  : {len(data)} 个顶层类别')
    print(f'  tokens.css   : {css_var_count} 个 CSS 变量')
    print(f'  tokens.py    : {py_const_count} 个 Python 常量')


if __name__ == '__main__':
    main()
