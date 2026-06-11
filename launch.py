"""
情绪地图 v1.0 — 一键启动
══════════════════════════════════════════════════════════════
用法:
    python launch.py
"""
import subprocess, sys, os, time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

cmd = [sys.executable, '-m', 'streamlit', 'run', 'apps/app_main.py', '--server.port', '8501']
print(f'启动: {" ".join(cmd)}')
print()
print('═' * 56)
print('  情绪地图 v1.0')
print('═' * 56)
print('  地图浏览器 : http://localhost:8501')
print('  分析控制台 : http://localhost:8501/?page=console')
print('═' * 56)
print('  按 Ctrl+C 停止')
print()

p = subprocess.Popen(cmd)
try:
    p.wait()
except KeyboardInterrupt:
    p.terminate()
    print('已停止')
