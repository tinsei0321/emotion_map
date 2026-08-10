"""CB-22i P0 验证：LLMClient.chat 流式 Timer 主动中断（首 chunk 前挂死）。

本地起 HTTP server·返 200 + text/event-stream 但永不发数据（模拟 DeepSeek 首 chunk 前挂死）·
调 LLMClient.chat 流式·断言 TTL（缩短为 1s 加速）内 Timer 强制 resp.close 中断·抛错（非永久阻塞）。

运行：py tests/test_llm_timer_active.py
"""
import os
import sys
import threading
import time
import http.server

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_qa.llm import LLMClient, LLMError

HANG = True   # True=永不返回·模拟挂死


class _HangHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        # 永不写数据·连接挂着（模拟 DeepSeek 首 chunk 前挂死）
        try:
            while HANG:
                time.sleep(1)
        except Exception:
            pass

    def log_message(self, *a):
        pass


def main():
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), _HangHandler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f'[OK] hang server on :{port}')

    cli = LLMClient(base_url=f'http://127.0.0.1:{port}', model='x', api_key='sk-test')
    cli._total_ttl = 1.0   # 1s TTL·加速
    start = time.time()
    try:
        for chunk in cli.chat([{'role': 'user', 'content': 'hi'}], stream=True):
            pass
        print('[FAIL] 未中断·永久阻塞（>5s）')
        return 1
    except LLMError as e:
        elapsed = time.time() - start
        print(f'[OK] Timer 主动中断·{elapsed:.1f}s 抛 LLMError: {str(e)[:60]}')
        return 0
    except Exception as e:
        elapsed = time.time() - start
        print(f'[OK] {elapsed:.1f}s 中断·抛 {type(e).__name__}: {str(e)[:60]}（Timer close resp 生效）')
        return 0
    finally:
        server.shutdown()


if __name__ == '__main__':
    sys.exit(main())
