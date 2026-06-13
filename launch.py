"""
情绪地图 v1.0 — 一键启动
══════════════════════════════════════════════════════════════
用法:
    py launch.py
"""
import subprocess, sys, os, shutil

os.chdir(os.path.dirname(os.path.abspath(__file__)))

_python = shutil.which('py') or sys.executable

# ── 自检：streamlit 是否安装 ──
print('[CHECK] 检测 streamlit ...')
r = subprocess.run([_python, '-m', 'pip', 'show', 'streamlit'],
                   capture_output=True, text=True)
if r.returncode != 0:
    print('[ERR] streamlit 未安装！')
    print('[FIX] 请在终端运行: py -m pip install -r requirements.txt')
    sys.exit(1)
print(f'[OK] {r.stdout.splitlines()[1] if r.stdout else "streamlit"}\n')

# ── 启动 ──
cmd = [_python, '-m', 'streamlit', 'run', 'apps/app_main.py',
       '--server.port', '8501']
print(f'[LAUNCH] {" ".join(cmd)}')
print()
print('=' * 56)
print('  情绪地图 v1.0')
print('=' * 56)
print('  地图浏览器 : http://localhost:8501')
print('  分析控制台 : http://localhost:8501/?page=console')
print('=' * 56)
print()

# 使用 subprocess.run 而非 Popen，错误实时可见
subprocess.run(cmd)
