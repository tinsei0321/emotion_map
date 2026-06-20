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


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    """对每个响应强制 no-store，并对 index.html 注入 ?v 绕缓存。"""

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
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
        super().do_GET()

    def log_message(self, fmt, *args):
        sys.stderr.write(f'[serve] {self.address_string()} - {fmt % args}\n')


class ReuseTCPServer(socketserver.TCPServer):
    allow_reuse_address = True   # 重启不报 "Address already in use"


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    with ReuseTCPServer(('', port), NoCacheHandler) as httpd:
        print(f'[OK] frontend serve on http://localhost:{port} (no-cache + ?v auto-inject)')
        print('     访问 http://localhost:{}/frontend/index.html'.format(port))
        print('     Ctrl+C 停止')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n[OK] 已停止')


if __name__ == '__main__':
    main()
