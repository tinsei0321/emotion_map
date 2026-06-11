"""
情绪地图 v1.0 — 一键启动所有服务
══════════════════════════════════════════════════════════════
用法:
    python launch.py              # 启动全部（地图 + 控制台）
    python launch.py --map        # 仅地图
    python launch.py --console    # 仅控制台
"""
import subprocess, sys, os, time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

STREAMLIT = [sys.executable, '-m', 'streamlit', 'run']

APPS = {
    'map':     ['apps/app_main.py',            '--server.port', '8501'],
    'console': ['apps/analysis_console.py',     '--server.port', '8502'],
}


def launch(name: str):
    """启动一个 Streamlit 应用"""
    cmd = STREAMLIT + APPS[name]
    print(f'🚀 启动 {name}: {" ".join(cmd)}')
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding='utf-8', errors='replace')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='情绪地图 v1.0 启动器')
    parser.add_argument('--map', action='store_true', help='仅启动地图 (8501)')
    parser.add_argument('--console', action='store_true', help='仅启动控制台 (8502)')
    args = parser.parse_args()

    # 默认启动全部
    start_all = not (args.map or args.console)

    processes = {}
    if start_all or args.map:
        processes['map'] = launch('map')
    if start_all or args.console:
        processes['console'] = launch('console')

    time.sleep(2)
    print()
    print('═' * 56)
    print('  🗺  情绪地图 v1.0 已启动')
    print('═' * 56)
    if 'map' in processes:
        print('  📍 地图浏览器 : http://localhost:8501')
    if 'console' in processes:
        print('  🔬 分析控制台 : http://localhost:8502')
    print('═' * 56)
    print('  按 Ctrl+C 停止全部服务')
    print()

    try:
        for p in processes.values():
            p.wait()
    except KeyboardInterrupt:
        print('\n⏹ 正在停止...')
        for p in processes.values():
            p.terminate()
        print('✅ 已停止')


if __name__ == '__main__':
    main()
