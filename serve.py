#!/usr/bin/env python3
"""Dev server with Cache-Control: no-store — fixes ES module caching during development.
Usage: py serve.py  (serves on :8080 from repo root)
"""
import http.server
import socketserver

PORT = 8080

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def guess_type(self, path):
        ctype = super().guess_type(path)
        # ES modules MUST be served as text/javascript (not application/octet-stream)
        if path.endswith('.js') or path.endswith('.mjs'):
            return 'text/javascript; charset=utf-8'
        return ctype

if __name__ == '__main__':
    with socketserver.TCPServer(('', PORT), NoCacheHandler) as httpd:
        print(f'[OK] dev server on http://127.0.0.1:{PORT}/ (no-cache)')
        httpd.serve_forever()
