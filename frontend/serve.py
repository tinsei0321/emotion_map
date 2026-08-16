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
    py frontend/serve.py 8080 --host=0.0.0.0   # explicit LAN access (default 127.0.0.1 only)

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
# CB-19 发版回归（三组并发）：--backend-port 可覆盖（防多组 serve 撞 8000·各自后端独立）。
BACKEND_ORIGIN = 'http://127.0.0.1:8000'   # 默认 8000·--backend-port 动态覆盖

# ---------------------------------------------------------------------------
# CB38 P0-3 (Codex audit 2026-08-16): serve path whitelist + loopback-only bind.
# SimpleHTTPRequestHandler used to serve the whole repo root and bind '' (all
# interfaces) -- anyone on the LAN could GET /.env and read real keys.
# Now: static serving is whitelist-only (403 otherwise); default bind is
# 127.0.0.1, LAN access requires explicit --host=0.0.0.0.
# ---------------------------------------------------------------------------
_SERVE_ALLOWED_PREFIXES = (
    '/frontend/',           # main app + css/js/vendor/assets + topology.html
    '/api/',                # reverse proxy to backend (never touches disk)
    '/_test/',              # dev-only flywheel dashboard (?test=1 drawer)
    '/DATA/performance/',   # data pool read directly by frontend (panel.js etc.)
    '/DATA/boundaries/',    # boundary geojson (e2e-seam / range presets)
)


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    """对每个响应强制 no-store，并对 index.html 注入 ?v 绕缓存；/api/* 反代后端。"""

    protocol_version = 'HTTP/1.1'   # WS1 F1.4：HTTP/1.1 必需（1.0 浏览器缓冲到连接关闭·流式 flush 无效·前开发卡此）

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Connection', 'close')   # WS1 F1.4 修正：HTTP/1.1 + 单线程 HTTPServer 必须关连接（keep-alive 占死唯一线程·致 :8080 全挂）
        super().end_headers()
        self.close_connection = True   # 每响应后关连接·单线程服务不阻塞·SSE 仍按 Connection:close 流式

    def do_GET(self):
        # /api/* → 反代后端（同源，消除浏览器跨域这一跳）
        if self.path.split('?')[0].startswith('/api/'):
            return self._proxy_api()
        # 拦截 index.html：注入 ?v=<mtime> 到本地 css/js 引用（绕浏览器缓存）
        norm = self.path.split('?')[0]
        # CB38 P0-3: root -> redirect to main UI; outside whitelist -> 403
        if norm in ('/', ''):
            self.send_response(302)
            self.send_header('Location', '/frontend/index.html')
            self.end_headers()
            return
        if not norm.startswith(_SERVE_ALLOWED_PREFIXES):
            self.send_error(403, 'Forbidden: path outside serve whitelist')
            return
        # /_test/reports | /_test/buglog → 飞轮仪表盘数据（dev-only·?test=1 抽屉读取）
        if norm.startswith('/_test/reports') or norm.startswith('/_test/buglog'):
            return self._serve_test_get(norm)
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
        """同源 /api/* → 后端 :8000 透传。SSE（text/event-stream）分块流式转发（WS1 F1.4·渐进 token）；
        其余缓冲转发。浏览器只跟 :8080 说话，后端这一跳在服务端完成——绕开浏览器跨域拦截。"""
        import urllib.request, urllib.error
        length = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(length) if length else None
        # 转发请求头：剔除 hop-by-hop 与会干扰后端的（host/accept-encoding/gzip 等）
        drop = {'host', 'content-length', 'connection', 'transfer-encoding',
                'accept-encoding', 'keep-alive', 'upgrade'}
        fwd = {k: v for k, v in self.headers.items() if k.lower() not in drop}
        req = urllib.request.Request(BACKEND_ORIGIN + self.path, data=body,
                                     method=self.command, headers=fwd)
        try:
            resp = urllib.request.urlopen(req, timeout=60)   # 不用 with·SSE 分支边读边转（WS1 F1.5：60s）
        except urllib.error.HTTPError as e:   # 后端 4xx/5xx 透传（缓冲）
            self._send_buffered(e.code, list(e.headers.items()), e.read())
            return
        except Exception as e:                # 后端连不上
            msg = f'[proxy] backend unreachable: {e}'.encode('utf-8')
            try:
                self.send_response(502)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Length', str(len(msg)))
                self.end_headers()
                self.wfile.write(msg)
            except Exception:                 # 浏览器已断连·写响应崩（CB-19 B3 教训：连接中断致 serve 线程崩·静默吞）
                pass
            return
        try:
            rheaders = list(resp.getheaders())
            ct = next((v for k, v in rheaders if k.lower() == 'content-type'), '') or ''
            if 'text/event-stream' in ct.lower():
                self._send_streamed(resp.getcode(), rheaders, resp)   # SSE 分块流式（渐进 token）
            else:
                self._send_buffered(resp.getcode(), rheaders, resp.read())   # 其余缓冲
        finally:
            resp.close()

    def _send_buffered(self, status, rheaders, rbody):
        """非 SSE：缓冲整响应一次写（带 Content-Length）。"""
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

    def _send_streamed(self, status, rheaders, resp):
        """SSE 流式：分块转发（WS1 F1.4 + Hotfix R2 S1）。不设 Content-Length·Connection: close（浏览器读到 EOF）。
        read1 绕 BufferedReader（实测 read(4096) 攒到 ≥4096B/EOF 才返·read1 逐 chunk 返）+ TCP_NODELAY 禁 Nagle。"""
        try:
            import socket as _sock
            self.connection.setsockopt(_sock.IPPROTO_TCP, _sock.TCP_NODELAY, 1)   # 禁 Nagle·小包即发
        except Exception:
            pass
        self.send_response(status)
        for k, v in rheaders:
            if k.lower() in ('content-type', 'content-disposition',
                             'content-language', 'etag', 'last-modified'):
                self.send_header(k, v)
        self.end_headers()
        # CB-22i P0（glm）：反代总超时——后端 uvicorn 挂死（DeepSeek 首 chunk 前挂）时·read1 永久阻塞
        #   会拖死 serve 单线程（后续请求排队）·Timer 到时强制 close resp 中断阻塞·返 502 → 前端降级。
        #   50s 比前端 45s abort 略宽（前端降级先行·serve 线程随后释放·不拖死后续请求）。
        import threading as _th
        _proxy_timer = _th.Timer(50.0, lambda: resp.close())
        _proxy_timer.start()
        try:
            while True:
                try:
                    chunk = resp.fp.read1(4096)   # 绕 BufferedReader·逐 chunk（实测：read 攒包·read1 流式）
                except Exception:
                    chunk = resp.read(4096)        # 兜底（resp.fp 非公开 API·个别环境不可用→回退缓冲读）
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()   # 每块 flush·浏览器渐进渲染 token
        except Exception:
            pass   # 客户端断开等·静默
        finally:
            _proxy_timer.cancel()   # 正常完成·取消 Timer

    def _test_reports_dir(self):
        """测试报告固定落盘目录：<repo>/tests/reports/（不存在则建）。"""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        d = os.path.join(repo_root, 'tests', 'reports')
        os.makedirs(d, exist_ok=True)
        return d

    def _save_test_report(self):
        """POST /_test/report {content,date,type,json} → 写 tests/reports/report-<date>-<NN>-<type>.md(+.json)。
        编号按同日已有文件数自增（跨会话唯一）。json=结构化报告（H5），补 commit/savedAt 落同名 .json。dev-only（?test=1 抽屉调用）。"""
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
        req_name = payload.get('name')
        if req_name:   # 覆写指定文件（手动存报告「覆盖」分支·不 +1 编号）
            name = re.sub(r'[^a-zA-Z0-9_\-]', '', str(req_name)) + '.md'
            n = existing.index(name) + 1 if name in existing else len(existing) + 1
        else:
            n = len(existing) + 1
            name = f'report-{date}-{n:02d}-{typ}.md'
        with open(os.path.join(d, name), 'w', encoding='utf-8') as f:
            f.write(content)
        # H5: 同步落结构化 JSON（同名异后缀），补 commit + savedAt（前端拿不到 git sha）
        json_name = None
        data = payload.get('json')
        if isinstance(data, dict):
            meta = data.setdefault('meta', {})
            try:
                import subprocess
                repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                meta['commit'] = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'],
                    cwd=repo, stderr=subprocess.DEVNULL, text=True, timeout=3).strip()
            except Exception:
                meta['commit'] = 'unknown'
            meta['savedAt'] = time.strftime('%Y-%m-%dT%H:%M:%S')
            json_name = name[:-3] + '.json'
            with open(os.path.join(d, json_name), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
        rel = f'tests/reports/{name}'
        body = json.dumps({'ok': True, 'name': name, 'path': rel, 'n': n, 'json': json_name}).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        extra = f' +{json_name}' if json_name else ''
        sys.stderr.write(f'[serve] 测试报告已存: {rel}{extra}\n')

    def _serve_test_get(self, norm):
        """GET /_test/reports | /_test/buglog → 飞轮仪表盘 JSON（dev-only·?test=1）。"""
        try:
            if norm.startswith('/_test/reports'):
                payload = self._test_reports_summary()
            else:  # /_test/buglog
                payload = self._test_buglog_summary()
        except Exception as e:
            payload = {'error': str(e)}
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _test_reports_summary(self):
        """扫描 tests/reports/report-*.json → 汇总列表（文件名降序·最新在前）。
        pass%/p50/p95 由 cases 现算（.json meta 无·md RUN 头才有）；复用 EMC-SUM v1 schema。"""
        d = self._test_reports_dir()
        items = []
        for fn in sorted(os.listdir(d), reverse=True):
            if not (fn.startswith('report-') and fn.endswith('.json')):
                continue
            try:
                with open(os.path.join(d, fn), 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                continue
            cases = data.get('cases') or []
            meta = data.get('meta') or {}
            total = len(cases)
            passed = sum(1 for c in cases if c.get('pass'))
            durs = sorted((c.get('durationSolo') or 0) for c in cases if c.get('durationSolo'))
            def _pct(q):
                if not durs:
                    return 0
                return round(durs[min(len(durs) - 1, int(q * len(durs)))] / 1000, 1)
            parts = fn.split('-')
            date = '-'.join(parts[1:4]) if len(parts) >= 4 else ''
            items.append({
                'name': fn[:-5], 'date': date, 'mode': meta.get('mode'),
                'total': total, 'pass': passed,
                'pct': round(passed / total * 100) if total else 0,
                'p50': _pct(0.5), 'p95': _pct(0.95),
                'commit': meta.get('commit'), 'startedAt': meta.get('startedAt'),
                'fails': [c.get('id') for c in cases if not c.get('pass')][:12],
            })
        return items

    def _test_buglog_summary(self):
        """读 tests/buglog/ → 汇总（复用 _gen_index.load_entries 单一解析源·非另写解析）。"""
        import sys as _sys
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bg = os.path.join(repo, 'tests', 'buglog')
        if bg not in _sys.path:
            _sys.path.insert(0, bg)
        try:
            import _gen_index as _bg
            entries = _bg.load_entries()
        except Exception:
            entries = []
        def _e(e):
            return {'id': e.get('id'), 'title': e.get('title'), 'type': e.get('type'),
                    'severity': e.get('severity'), 'status': e.get('_status'),
                    'module': e.get('module'), 'repro': int(e.get('repro_count') or 0),
                    'cb': e.get('cb'), 'case_ref': e.get('case_ref'), 'path': e.get('_path')}
        open_list = [_e(e) for e in entries if e.get('_status') == 'open']
        rec_list = sorted([_e(e) for e in entries if int(e.get('repro_count') or 0) >= 2],
                          key=lambda x: -x['repro'])
        reg_list = [_e(e) for e in entries if e.get('_status') == 'resolved']
        return {
            'total': len(entries), 'open': len(open_list),
            'resolved': len(entries) - len(open_list),
            'openList': open_list, 'recList': rec_list, 'regressionList': reg_list,
        }

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


def _dirty_check(repo_root):
    """CB-12（用户诉求·每次打开网页都应最新代码）：工作树脏检查——git status 非空 → [WARN] 显性提示。
    洞：磁盘文件 ≠ 提交状态时（未提交改动），换机/拉取/演示机 = 旧代码。serve 每次起的是磁盘最新，
    但若提交 ≠ 磁盘，演示/测试可能非最新提交状态——显性警告·不静默吞。"""
    try:
        r = subprocess.run(['git', 'status', '--porcelain'], cwd=repo_root,
                           capture_output=True, text=True, timeout=5)
        dirty = [l for l in r.stdout.splitlines() if l.strip()]
        if dirty:
            n = len(dirty)
            sample = '、'.join(d.split()[1] if len(d.split()) > 1 else d for d in dirty[:3])
            print(f'[WARN] 工作树有 {n} 个未提交改动（{sample}…）——演示/测试为磁盘最新，但非最新提交；'
                  f'换机/拉取/演示机将用旧代码。建议先 git add+commit。')
    except Exception:
        pass   # git 不可用/非仓库 → 静默（不影响 serve）


def _spawn_backend(repo_root, backend_port=8000):
    """启动 uvicorn 子进程并等 /health 就绪。每次启动**强制清 :port 重起**（不复用旧进程），
    保证后端是最新代码——避免复用旧后端（health 通但缺新路由如 /spatial/grid）导致 404。
    若需保留手动起的后端，用 `py frontend/serve.py 8080 --no-backend`。"""
    import urllib.request, time
    _dirty_check(repo_root)   # CB-12：脏检查警告（未提交改动 → 显性提示·防演示用旧代码）
    _free_port(backend_port)   # 清 :port 所有残留（旧后端/死进程），保证起最新代码

    try:
        proc = subprocess.Popen(
            ['py', '-m', 'uvicorn', 'api.main:app', '--port', str(backend_port)],
            cwd=repo_root,   # stdout/stderr 继承——uvicorn 启动日志/错误直接进 serve 控制台
        )
    except Exception as e:
        print(f'[WARN] 后端启动失败（{e}）；前端照常，网格/缓冲/分析不可用')
        return None
    print(f'[OK] backend uvicorn 启动中（:{backend_port}, PID {proc.pid}）…')
    print('[WAIT] BGE RAG 模型预热中（本地嵌入模型加载·约 10-20s·同步阻塞是有意设计——启动慢换首问稳定·完成后打印 [OK] RAG 模型预热完成）…')
    for _ in range(90):   # ≤45s（冷启动 + geopandas 首次 import + BGE 同步预热 10-20s 均可能）
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
    # CB-19 发版回归（三组并发）：--backend-port 覆盖后端端口（默认 8000·防多组 serve 撞后端）
    backend_port = 8000
    for _i, _a in enumerate(args):
        if _a == '--backend-port' and _i + 1 < len(args):
            backend_port = int(args[_i + 1])
    global BACKEND_ORIGIN
    BACKEND_ORIGIN = f'http://127.0.0.1:{backend_port}'
    # --open=both|main|test|none：serve 就绪后自动开浏览器（start.bat 用 both；直接 py serve 默认 none 不开）
    open_what = 'none'
    for _a in args:
        if _a.startswith('--open='):
            open_what = _a.split('=', 1)[1]
        elif _a == '--open':
            open_what = 'both'
    # CB38 P0-3: default bind 127.0.0.1 (was '' = all interfaces); LAN needs explicit --host=
    host = '127.0.0.1'
    for _a in args:
        if _a.startswith('--host='):
            host = _a.split('=', 1)[1]
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # frontend/ 的上一层 = repo root
    _free_port(port)   # 清掉同端口的僵尸 serve，避免返回旧版
    backend_proc = None if no_backend else _spawn_backend(repo_root, backend_port=backend_port)
    with ReuseTCPServer((host, port), NoCacheHandler) as httpd:
        if open_what != 'none':
            _open_browser(open_what, port)   # socket 已 listen → 后台线程延迟开浏览器
        if host not in ('127.0.0.1', 'localhost'):
            print(f'[WARN] bind {host}: visible on LAN (whitelist limits readable paths; switch back to 127.0.0.1 after demo)')
        print(f'[OK] frontend serve on http://{host}:{port} (no-cache + ?v auto-inject + path whitelist)')
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
