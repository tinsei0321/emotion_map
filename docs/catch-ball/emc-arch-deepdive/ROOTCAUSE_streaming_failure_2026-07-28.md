# GLM 渐进式 Token 流式工程 — 未实现根因分析

> **分析方**：DeepSeek V4 Pro（ZCode 主线程）  
> **日期**：2026-07-28  
> **审查对象**：`b2a24ab`（WS1 latency） + `190caca`（keep-alive hotfix）  
> **变更文件**：`frontend/serve.py`（核心流式改造）

---

## 一、总评

> **GLM 的流式实现方向正确（HTTP/1.1 + chunked read + flush），代码逻辑上没有明显错误。流式失败的根本原因不在代码逻辑层面，而在 TCP/OS 层面的底层缓冲。`urllib` 底层 `BufferedReader` 以 8192 字节块读取 + Nagle 算法合并小包 + 无 `TCP_NODELAY`，三层缓冲叠加导致 token 未能逐字到达浏览器。**

---

## 二、GLM 做了什么（代码审查）

### 2.1 改造内容

| 变更 | 位置 | 评价 |
|------|------|:---:|
| `protocol_version = 'HTTP/1.1'` | `serve.py:133` | ✅ 正确。HTTP/1.0 下浏览器缓冲到连接关闭 |
| `_send_streamed()` 新增函数 | `serve.py:246-263` | ✅ 逻辑正确。`read(4096)` + `write` + `flush()` |
| 按 Content-Type 路由 | `serve.py:222-224` | ✅ `text/event-stream` → `_send_streamed` |
| `Connection: close` + `close_connection = True` | `serve.py:139,141` | ✅ 修复 HTTP/1.1 单线程死锁（`190caca`） |
| 其余响应保持缓冲 | `serve.py:226` | ✅ 合理 |

### 2.2 `_send_streamed` 逐行分析

```python
def _send_streamed(self, status, rheaders, resp):
    self.send_response(status)          # HTTP 状态行
    for k, v in rheaders:               # 转发响应头
        ...
    self.end_headers()                  # 空行分隔 header/body

    while True:
        chunk = resp.read(4096)         # ← 🔍 关键行
        if not chunk: break
        self.wfile.write(chunk)         # 写浏览器
        self.wfile.flush()              # 强制推送
```

**代码逻辑无错误**。在理想条件下（数据即刻可读 + TCP 即时发送），这段代码可以实现逐 token 转发。

---

## 三、为什么没实现 — 三层缓冲叠加

### 3.1 第一层：`urllib` 底层 `BufferedReader`（8192 字节块读取）

```
resp.read(4096)
    │
    └→ http.client.HTTPResponse._read_chunked(4096)
        │
        └→ fp.read(n)    # fp = BufferedReader(socket)
            │
            └→ 缓冲区空 → raw.read(max(8192, 4096)) = raw.read(8192)
                │
                └→ socket.recv(8192) → 只有 30 字节到达
                    │
                    返回 30 字节 → BufferedReader: buf=30, <4096
                    │
                    └→ raw.read(8192) 再次调用 → **阻塞等待更多数据**
```

**关键问题**：`BufferedReader.read(4096)` 在内部缓冲区数据不足 4096 字节时，会再次调用底层 `raw.read(8192)`。虽然 TCP socket 已有 30 字节，但 `BufferedReader` 不知道，它要求缓冲区达到 4096 才会返回给调用方。

> ⚠️ **实际上**：CPython 的 `BufferedReader.read(n)` 在缓冲区有数据但不足 n 时，会调用 `raw.read(max(CHUNK_SIZE, n - len(buf)))` 尝试获取更多数据。**这个调用会阻塞**直到新数据到达或连接关闭。

**后果**：第一个 SSE 帧（30 字节的 `data: {"token":"分"}\n\n`）被读取后停在 `BufferedReader` 内部缓冲区，**不会返回给 `_send_streamed`**，直到下一个 SSE 帧到达凑足 ≥4096 字节或 EOF。

### 3.2 第二层：TCP Nagle 算法（小包合并）

```
wfile.write(30字节) + wfile.flush()
    │
    └→ BufferedWriter.flush() → socket.sendall(30字节)
        │
        └→ OS TCP 栈：Nagle 算法启用 → 30 字节太小，等待更多数据
            │
            └→ ~200ms 超时 或 累积到 MSS(1460字节)  → 才发送
```

即使 `flush()` 推到了 TCP 层，OS 的 Nagle 算法会延迟小包的发送。`wfile` 没有设置 `TCP_NODELAY`。

### 3.3 第三层：前端渲染 RAF 批处理

```javascript
// panel.js 渲染使用了 requestAnimationFrame 批处理
// 每 ~16ms 刷新一次 DOM → token 按帧批量出现
```

这不是流式断裂的原因（用户仍看到渐进效果），但会影响"逐字蹦出"的视觉体验。

### 3.4 叠加效果

```
SSE 帧(30B) → BufferedReader 吞掉(等≥4096B) → 不转发
SSE 帧(30B) → BufferedReader 吞掉(等≥4096B) → 不转发
... × 136 帧 ...
SSE 帧(30B) → BufferedReader 累积达到 4096B → read(4096) 返回 4096B
    → wfile.write(4096B) → Nagle 延迟 ~200ms → 发送
    → 浏览器收到 4096B → 一次渲染 136 个 token
```

**用户看到的效果**：等待 20-50s → 整段文字一次性出现（与流式前完全一样）。

---

## 四、验证方法

在 `_send_streamed` 中加入调试日志：

```python
def _send_streamed(self, status, rheaders, resp):
    ...
    t0 = time.time()
    n_chunks = 0
    while True:
        chunk = resp.read(4096)
        if not chunk: break
        n_chunks += 1
        self.wfile.write(chunk)
        self.wfile.flush()
    sys.stderr.write(f'[stream] {n_chunks} chunks in {time.time()-t0:.1f}s\n')
```

如果输出是 `[stream] 1 chunks in 35.2s`，则确认：**全部 token 被合并为 1 个 chunk，BufferedReader 是根因**。

---

## 五、修复方案

### 方案 A（推荐·最可靠）：绕过代理直连后端

**思路**：`/api/v1/chat` 不经过 `serve.py` 代理，浏览器直连 `localhost:8000`。

| 步骤 | 文件 | 操作 |
|:---:|------|------|
| 1 | `api/main.py` | 加 CORS 中间件（允许 `localhost:8080`） |
| 2 | `frontend/js/ai_qa/api.js` | `/api/v1/chat` 改为 `http://localhost:8000/api/v1/chat` |

**优点**：
- ✅ 彻底消除代理缓冲问题
- ✅ 浏览器 ReadableStream 直连后端 StreamingResponse
- ✅ 改动小（~5 行）
- ✅ 不受 `urllib` / Nagle 影响

**缺点**：
- 破坏了"前端只跟 :8080 说话"的同源架构
- 需要 CORS 配置

### 方案 B（修复代理）：`TCP_NODELAY` + 小 chunk 读取

| 步骤 | 位置 | 操作 |
|:---:|------|------|
| 1 | `serve.py:__init__` | `self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)` |
| 2 | `serve.py:257` | `resp.read(4096)` → `resp.fp.read1(4096)`（绕过 BufferedReader） |
| 3 | `serve.py:261` | `self.wfile.flush()` 后加 `self.connection.setsockopt(...)`（确保写入端也 NODELAY） |

**注意**：`resp.fp` 是 `http.client.HTTPResponse` 的内部属性（非公开 API），可能随 Python 版本变化。

### 方案 C（根治·长期）：`httpx` 替代 `urllib`

```python
import httpx

def _proxy_api(self):
    ...
    with httpx.stream('POST', BACKEND_ORIGIN + self.path, ...) as resp:
        if 'text/event-stream' in resp.headers.get('content-type', ''):
            self.send_response(resp.status_code)
            ...
            for chunk in resp.iter_bytes(chunk_size=1):  # 逐字节
                self.wfile.write(chunk)
                self.wfile.flush()
```

**优点**：
- ✅ `httpx` 是项目已有依赖
- ✅ `iter_bytes` 真正的逐字节流式迭代
- ✅ 跨平台一致性

**缺点**：
- 需要重构 `_proxy_api`

---

## 六、推荐实施

| 优先级 | 方案 | 理由 |
|:---:|:---:|------|
| **立即** | A（绕过代理） | 最可靠、改动最小、即刻见效 |
| 短期 | C（httpx 替代 urllib） | 根治代理层流式问题，全局受益 |
| 可选 | B（TCP_NODELAY） | 配合 C 使用，进一步降低延迟 |

---

## 七、相关代码位置

| 文件 | 行 | 作用 |
|------|:---:|------|
| `frontend/serve.py` | 133 | `protocol_version = 'HTTP/1.1'` |
| `frontend/serve.py` | 139-141 | `Connection: close` + `close_connection = True` |
| `frontend/serve.py` | 195-228 | `_proxy_api()` — SSE 路由逻辑 |
| `frontend/serve.py` | 246-263 | `_send_streamed()` — 流式转发（关键） |
| `ai_qa/llm.py` | 96-126 | `chat()` — httpx.stream() 逐 token 产出 |
| `ai_qa/router.py` | 109-132 | `gen()` — StreamingResponse 渐进 SSE |
| `frontend/js/ai_qa/api.js` | 51-73 | `streamChat()` — ReadableStream 增量读取 |
| `api/main.py` | 63 | CORS 配置（需扩展） |

---

> **归档信息**：`docs/catch-ball/emc-arch-deepdive/ROOTCAUSE_streaming_failure_2026-07-28.md`
