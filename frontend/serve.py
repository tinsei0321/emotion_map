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
        # /api/* POST（export/buffer/analyze/governance）→ 反代后端
        if self.path.split('?')[0].startswith('/api/'):
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


def main():
    args = sys.argv[1:]
    port = int(args[0]) if args and args[0].isdigit() else 8080
    no_backend = '--no-backend' in args
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # frontend/ 的上一层 = repo root
    _free_port(port)   # 清掉同端口的僵尸 serve，避免返回旧版
    backend_proc = None if no_backend else _spawn_backend(repo_root)
    with ReuseTCPServer(('', port), NoCacheHandler) as httpd:
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
