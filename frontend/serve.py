#!/usr/bin/env python3
"""
前端开发服务器（no-cache + ?v 自动注入）— 彻底解决浏览器缓存旧 JS/CSS
====================================================================
1. 所有响应强制 Cache-Control: no-store（浏览器不缓存）。
2. 返回 index.html 时，自动给本地 css/ js/ 引用注入 ?v=<文件mtime>：
   文件一改 → mtime 变 → URL 变 → 浏览器拉新，无需手动 bump 版本号。
   开发者改前端后零手动，硬刷即可见最新。

用法：
    py frontend/serve.py          # 默认 :8080
    py frontend/serve.py 8080

启动后访问 http://localhost:8080/frontend/index.html
（务必走 serve，勿用 file:// —— 自动注入只在 serve 时生效）
"""
import http.server
import socketserver
import sys
import os
import re
import json
import time
import subprocess

# 本地 css/js 引用（相对路径 css/.. js/..）→ 注入 ?v=<mtime>
_LOCAL_REF = re.compile(r'((?:href|src)=["\'])(css|js)/([^"\']+?\.(?:css|js))(["\'])')


def _inject_versions(html, basedir):
    """把 index.html 里 css/X.css、js/X.js 引用加上 ?v=<文件修改时间>。"""
    def repl(m):
        pre, folder, name, q = m.group(1), m.group(2), m.group(3), m.group(4)
        full = os.path.join(basedir, folder, name)
        try:
            v = int(os.path.getmtime(full))
        except OSError:
            v = 0
        return f'{pre}{folder}/{name}?v={v}{q}'
    return _LOCAL_REF.sub(repl, html)


# ES module import/export 的相对 .js 引用 → 注入 ?v=<目标 mtime>。
# 破除 Chrome module graph 缓存：子 module（如 heatmap-tool.js）改动后 URL 随之变化，
# 浏览器必然拉新——否则 main.js ?v 不变时 Chrome 复用整个 module graph，子 module 缓存旧版
# （实测：改 heatmap-tool.js 后 F5 仍跑旧版，根因即此）。
_JS_IMPORT = re.compile(r'''(['"])(\.{1,2}/[^'"]+?\.js)(?:\?[^'"]*)?(['"])''')


def _inject_import_versions(content, basedir):
    """把 JS 里 import/export 的相对 .js 路径加上 ?v=<目标 mtime>。"""
    def repl(m):
        q1, ref, q2 = m.group(1), m.group(2), m.group(3)
        full = os.path.normpath(os.path.join(basedir, ref))
        try:
            v = int(os.path.getmtime(full))
        except OSError:
            v = 0
        return f'{q1}{ref}?v={v}{q2}'
    return _JS_IMPORT.sub(repl, content)


def _git_short(basedir):
    """git 短哈希（失败返 '?'）—— build stamp 一部分，让用户核对是否跑到新提交。"""
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=basedir, text=True, stderr=subprocess.DEVNULL,
        ).strip() or '?'
    except Exception:
        return '?'


def _build_stamp(basedir):
    """build stamp = git 短哈希 + 前端 js/css 最新 mtime（递归含子目录，如 js/ai_qa/、css/ 子目录）。
    改任何前端文件 → mtime 变 → stamp 变；用户刷新看 stamp 时间 > 自己最后一次编辑 = 拿到新代码。
    每次请求现算（读盘），反映当前磁盘状态。"""
    import time
    latest = 0
    for sub in ('js', 'css'):
        root = os.path.join(basedir, sub)
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):   # 递归（旧 os.listdir 漏 ai_qa/ 等子目录，致 stamp 不更新）
            for fn in files:
                if fn.endswith(('.js', '.css')):
                    try:
                        latest = max(latest, int(os.path.getmtime(os.path.join(dirpath, fn))))
                    except OSError:
                        pass
    t = time.strftime('%m-%d %H:%M:%S', time.localtime(latest)) if latest else '?'
    return f'{_git_short(os.path.dirname(basedir))} · {t}'


def _inject_stamp(html, stamp):
    """把 build stamp 作为右下角小角标注入 index.html（</body> 前）。"""
    badge = (
        '<div id="dev-build-stamp" style="position:fixed;bottom:0;right:2px;'
        'font:9px/1.5 ui-monospace,Consolas,monospace;color:#666;'
        'background:rgba(255,255,255,.72);padding:1px 5px;border-radius:3px 0 0 0;'
        'pointer-events:none;z-index:99999;opacity:.55">build ' + stamp + '</div>'
    )
    return html.replace('</body>', badge + '</body>', 1) if '</body>' in html else html


def _inject_title(html, short):
    """把 git 短哈希注入 <title> 末尾（build 号，无日期，方便用户识别版本）。
    幂等：title 已含（）则不重复加。"""
    m = re.search(r'<title>([^<]*)</title>', html)
    if not m or '（' in m.group(1):
        return html
    return html.replace(f'<title>{m.group(1)}</title>', f'<title>{m.group(1)}（{short}）</title>', 1)


def _inject_header_version(html, short):
    """把 git 短哈希注入顶栏 .title-version span（prototype alpha v0.1（build：短哈希））。
    与 <title> build 号同源（_git_short），统一版本识别。幂等：span 已含（则不重复加。"""
    m = re.search(r'(<span class="title-version">)([^<]*)(</span>)', html)
    if not m or '（' in m.group(2):
        return html
    return html.replace(m.group(0), f'{m.group(1)}{m.group(2)}（build：{short}）{m.group(3)}', 1)


# 后端 origin（uvicorn :8000）—— /api 反向代理的目标。
# 前端同源 fetch /api/* → serve.py 透传此后端，消除浏览器跨域这一跳
#（修 export "Failed to fetch"：浏览器只跟 :8080 说话，:8000 这跳在服务端完成）。
BACKEND_ORIGIN = 'http://127.0.0.1:8000'


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    """对每个响应强制 no-store，并对 index.html 注入 ?v 绕缓存；/api/* 反代后端。"""

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        # /api/* → 反代后端（同源，消除浏览器跨域这一跳）
        if self.path.split('?')[0].startswith('/api/'):
            return self._proxy_api()
        # 拦截 index.html：注入 ?v=<mtime> 到本地 css/js 引用（绕浏览器缓存）
        norm = self.path.split('?')[0]
        if norm.endswith('index.html'):
            fs = self.translate_path(norm)
            if os.path.isfile(fs):
                basedir = os.path.dirname(fs)
                with open(fs, 'rb') as f:
                    html = f.read().decode('utf-8')
                html = _inject_versions(html, basedir)
                _short = _git_short(os.path.dirname(basedir))   # git 短哈希（版本识别，无日期）
                html = _inject_title(html, _short)              # <title> 加 build 号（prototype alpha v0.1（短哈希））
                html = _inject_header_version(html, _short)     # 顶栏 .title-version 后加（build：短哈希），与 <title> 同源
                html = _inject_stamp(html, _short)              # 右下角标也只版本号（去日期）
                body = html.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        # 拦截 .js：把 import/export 的相对 .js 引用注入 ?v=<目标 mtime>，
        # 破除 Chrome module graph 缓存（否则 main.js ?v 不变时子 module 缓存旧版）
        if norm.endswith('.js'):
            fs = self.translate_path(norm)
            if os.path.isfile(fs):
                basedir = os.path.dirname(fs)
                with open(fs, 'rb') as f:
                    content = f.read().decode('utf-8')
                content = _inject_import_versions(content, basedir)
                body = content.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/javascript; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        super().do_GET()

    def do_POST(self):
        path = self.path.split('?')[0]
        # /_test/report：测试飞轮报告落盘到 tests/reports/（dev-only，不走后端）
        if path == '/_test/report':
            return self._save_test_report()
        # /api/* POST（export/buffer/analyze/governance）→ 反代后端
        if path.startswith('/api/'):
            return self._proxy_api()
        self.send_error(405, 'Method Not Allowed')

    def _proxy_api(self):
        """同源 /api/* → 后端 :8000 透传（method/body/headers/响应全转发）。
        浏览器只跟 :8080 说话，后端这一跳在服务端完成——绕开一切浏览器跨域拦截。"""
        import urllib.request, urllib.error
        length = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(length) if length else None
        # 转发请求头：剔除 hop-by-hop 与会干扰后端的（host/accept-encoding 等）
        drop = {'host', 'content-length', 'connection', 'transfer-encoding',
                'accept-encoding', 'keep-alive', 'upgrade'}
        fwd = {k: v for k, v in self.headers.items() if k.lower() not in drop}
        req = urllib.request.Request(BACKEND_ORIGIN + self.path, data=body,
                                     method=self.command, headers=fwd)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                status, rbody = resp.getcode(), resp.read()
                rheaders = list(resp.getheaders())
        except urllib.error.HTTPError as e:   # 后端 4xx/5xx 也要透传
            status, rbody = e.code, e.read()
            rheaders = list(e.headers.items())
        except Exception as e:                # 后端连不上
            msg = f'[proxy] backend unreachable: {e}'.encode('utf-8')
            self.send_response(502)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
            return
        self.send_response(status)
        ct_sent = False
        for k, v in rheaders:
            if k.lower() in ('content-type', 'content-disposition',
                             'content-language', 'etag', 'last-modified'):
                self.send_header(k, v)
                if k.lower() == 'content-type':
                    ct_sent = True
        if not ct_sent:
            self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', str(len(rbody)))
        self.end_headers()
        self.wfile.write(rbody)

    def _test_reports_dir(self):
        """测试报告固定落盘目录：<repo>/tests/reports/（不存在则建）。"""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        d = os.path.join(repo_root, 'tests', 'reports')
        os.makedirs(d, exist_ok=True)
        return d

    def _save_test_report(self):
        """POST /_test/report {content,date,type} → 写 tests/reports/report-<date>-<NN>-<type>.md。
        编号按同日已有文件数自增（跨会话唯一）。dev-only（?test=1 抽屉调用）。"""
        length = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(length) if length else b''
        try:
            payload = json.loads(raw.decode('utf-8') or '{}')
        except Exception:
            payload = {}
        content = str(payload.get('content', ''))
        date = str(payload.get('date') or time.strftime('%Y-%m-%d'))
        typ = re.sub(r'[^a-zA-Z0-9_-]', '', str(payload.get('type', 'run'))) or 'run'
        d = self._test_reports_dir()
        existing = [f for f in os.listdir(d) if f.startswith(f'report-{date}-') and f.endswith('.md')]
        n = len(existing) + 1
        name = f'report-{date}-{n:02d}-{typ}.md'
        with open(os.path.join(d, name), 'w', encoding='utf-8') as f:
            f.write(content)
        rel = f'tests/reports/{name}'
        body = json.dumps({'ok': True, 'name': name, 'path': rel, 'n': n}).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        sys.stderr.write(f'[serve] 测试报告已存: {rel}\n')

    def log_message(self, fmt, *args):
        sys.stderr.write(f'[serve] {self.address_string()} - {fmt % args}\n')


class ReuseTCPServer(socketserver.TCPServer):
    allow_reuse_address = True   # 重启不报 "Address already in use"


def _free_port(port):
    """启动前杀掉占用该端口的旧 serve 进程（Windows: netstat+taskkill），
    避免僵尸 serve 残留导致返回旧版（之前多次后台启动的残留根因）。非 Windows 跳过。"""
    if sys.platform != 'win32':
        return
    try:
        out = subprocess.check_output(['netstat', '-ano'], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return
    pids = set()
    for line in out.splitlines():
        if f':{port}' in line and 'LISTENING' in line.upper():
            parts = line.split()
            if parts:
                pids.add(parts[-1])
    me = str(os.getpid())
    for pid in pids:
        if pid and pid != me:
            try:
                subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True)
                print(f'[OK] 已清理端口 {port} 上的旧进程 PID {pid}')
            except Exception:
                pass


def _port_free(port):
    """端口是否空闲（仅检测，不杀进程——避免误杀用户已起的后端）。"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', port)); s.close(); return True
    except OSError:
        return False


def _spawn_backend(repo_root, backend_port=8000):
    """启动 uvicorn 子进程并等 /health 就绪。每次启动**强制清 :port 重起**（不复用旧进程），
    保证后端是最新代码——避免复用旧后端（health 通但缺新路由如 /spatial/grid）导致 404。
    若需保留手动起的后端，用 `py frontend/serve.py 8080 --no-backend`。"""
    import urllib.request, time
    _free_port(backend_port)   # 清 :port 所有残留（旧后端/死进程），保证起最新代码

    try:
        proc = subprocess.Popen(
            ['py', '-m', 'uvicorn', 'api.main:app', '--port', str(backend_port)],
            cwd=repo_root,   # stdout/stderr 继承——uvicorn 启动日志/错误直接进 serve 控制台
        )
    except Exception as e:
        print(f'[WARN] 后端启动失败（{e}）；前端照常，网格/缓冲/分析不可用')
        return None
    print(f'[OK] backend uvicorn 启动中（:{backend_port}, PID {proc.pid}），等待就绪…')
    for _ in range(60):   # ≤30s（冷启动 + geopandas 首次 import 可能慢）
        if proc.poll() is not None:
            print('[WARN] backend 进程已退出（查上方 uvicorn 输出：依赖/语法/import 错）')
            return None
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{backend_port}/api/v1/health', timeout=1).read()
            print(f'[OK] backend 就绪 (:{backend_port})')
            return proc
        except Exception:
            time.sleep(0.5)
    print(f'[WARN] backend 30s 未就绪（可能仍在初始化）；前端照常，/api 暂不可用')
    return proc


def _open_browser(which, port):
    """serve 就绪后自动开浏览器（main / test / both）。后台线程延迟开，socket 已 listen 必连得上。"""
    import threading, webbrowser
    base = f'http://localhost:{port}'

    def _go():
        time.sleep(0.6)
        if which in ('main', 'both'):
            try: webbrowser.open(f'{base}/frontend/index.html')
            except Exception: pass
        if which in ('test', 'both'):
            time.sleep(0.5)
            try: webbrowser.open(f'{base}/frontend/index.html?test=1')
            except Exception: pass

    threading.Thread(target=_go, daemon=True).start()


def main():
    args = sys.argv[1:]
    port = int(args[0]) if args and args[0].isdigit() else 8080
    no_backend = '--no-backend' in args
    # --open=both|main|test|none：serve 就绪后自动开浏览器（start.bat 用 both；直接 py serve 默认 none 不开）
    open_what = 'none'
    for _a in args:
        if _a.startswith('--open='):
            open_what = _a.split('=', 1)[1]
        elif _a == '--open':
            open_what = 'both'
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # frontend/ 的上一层 = repo root
    _free_port(port)   # 清掉同端口的僵尸 serve，避免返回旧版
    backend_proc = None if no_backend else _spawn_backend(repo_root)
    with ReuseTCPServer(('', port), NoCacheHandler) as httpd:
        if open_what != 'none':
            _open_browser(open_what, port)   # socket 已 listen → 后台线程延迟开浏览器
        print(f'[OK] frontend serve on http://localhost:{port} (no-cache + ?v auto-inject)')
        print('     访问 http://localhost:{}/frontend/index.html'.format(port))
        print('     Ctrl+C 停止' + ('（同时停后端）' if backend_proc else ''))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n[OK] 已停止')
        finally:
            if backend_proc and backend_proc.poll() is None:
                backend_proc.terminate()
                try:
                    backend_proc.wait(timeout=5)
                except Exception:
                    backend_proc.kill()
                print('[OK] backend 已停止')


if __name__ == '__main__':
    main()
