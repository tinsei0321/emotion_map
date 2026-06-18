#!/usr/bin/env python3
"""
前端开发服务器（no-cache）— 彻底解决浏览器缓存旧 JS/CSS 的问题
================================================================
替代 `py -m http.server`：对所有响应强制发 Cache-Control: no-store，
浏览器每次都加载最新文件，不再出现"换个浏览器才正常"的残留旧版本问题。

用法：
    py frontend/serve.py          # 默认 :8080
    py frontend/serve.py 8080     # 指定端口

启动后访问 http://localhost:8080/frontend/index.html
"""
import http.server
import socketserver
import sys
import os

# 服务当前工作目录（从项目根启动 → URL 为 /frontend/index.html，与原 http.server 习惯一致）
# 若想只服务 frontend/，可：cd frontend && py serve.py


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    """对每个响应强制 no-store，禁用浏览器缓存。"""

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write(f'[serve] {self.address_string()} - {fmt % args}\n')


class ReuseTCPServer(socketserver.TCPServer):
    allow_reuse_address = True   # 重启不报 "Address already in use"


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    with ReuseTCPServer(('', port), NoCacheHandler) as httpd:
        print(f'[OK] frontend serve on http://localhost:{port} (no-cache)')
        print('     访问 http://localhost:{}/frontend/index.html'.format(port))
        print('     Ctrl+C 停止')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n[OK] 已停止')


if __name__ == '__main__':
    main()
