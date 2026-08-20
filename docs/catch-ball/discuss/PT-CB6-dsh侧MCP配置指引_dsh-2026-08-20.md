# PT-CB6 · dsh 侧 MCP 配置指引（S1 实证 + 环境预检记录·dsh·2026-08-20）

> 执行：dsh（副手）· 2026-08-20 · 分支：`EMC_harness_dsh`。
> 本指引所有配置字段均来自本地仓 `D:\Github\dsh` 文档实测（file:line），非记忆转述。

---

## 一 配置实证（S1）

### 1.1 权威文档位

| 出处 | 内容 |
|---|---|
| `D:\Github\dsh\packages\mcp\mcp-client\README.md:9-30` | 一个 MCP server = 一个插件实例（cordis 行）；stdio/streamable-http 两例；工具名 `mcp__<serverName>__<rawName>` |
| `D:\Github\dsh\docs\config-catalog.md:1218-1247` | `StdioConfig` 全字段：`transport/serverName/command/args/env/cwd/toolCallTimeoutMs/failOnStartupError/reconnect` |
| `D:\Github\dsh\docs\config-catalog.md:1236` | `toolCallTimeoutMs`（per callTool·默认见 README:46=60000） |
| `D:\Github\dsh\packages\mcp\mcp-client\README.md:34-51` | 配置表：transport/serverName 必填；stdio 的 command 必填、args/env/cwd 可选；`toolCallTimeoutMs` 默认 60000；`failOnStartupError` 默认 false |
| `D:\Github\dsh\docs\user\develop\basic\config.md:34-43` | profile patch 插入新插件行的语法必须是 `- insert: [- id: ... name: ... config: ...]`（普通 `- id: name:` 会被当作对既有行 id 的覆盖，实测报 `entry not found`） |

### 1.2 实际应用片段（已写入 `~/.dsh/profiles/emc-test/cordis.patch.yml`）

```yaml
- insert:
    - id: mcp-emc
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: emc
        transport: stdio
        command: py
        args: ['D:/Github/emotion_map/tools/mcp_server_emc.py']
        cwd: 'D:/Github/emotion_map'
        toolCallTimeoutMs: 60000
        failOnStartupError: true
```

- `serverName: emc` → 工具名形如 `mcp__emc__zonal_stats`（README.md:5）。
- `command: py`（Windows 用 py 启动器·对齐本仓 P1-5 双解释器纪律）；`args` 正斜杠绝对路径；`cwd` 指向仓根；未设 `env`（server 自读 `.env`）。
- `toolCallTimeoutMs: 60000` 覆盖空间工具首调冷启动 8-10s；`failOnStartupError: true` 让配置失败可见。

### 1.3 profile 装配（emc-test）

`~/.dsh/profiles/emc-test/package.json`（`dsh.profile.bundles`）：

```json
["@deepseek-ai/dsh-base", "@deepseek-ai/dsh-web-app"]
```

`~/.dsh/profiles/emc-test/package.json` dependencies 含：

```json
"@deepseek-ai/dsh-mcp-client": "link:D:/Github/dsh/packages/mcp/mcp-client"
```

> 注意：mcp-client **没有 `dsh.bundle`**（`dsh plugin add` 实测警告「installed as a plain dependency, not a profile layer」），**不能**放进 bundles；它是被 `cordis.patch.yml` 的 `insert` 行实例化的插件。

### 1.4 L0 验证专用 headless 双胞胎

- profile `emc-test-headless`：bundles = `@deepseek-ai/dsh-base` + `@deepseek-ai/dsh-headless`，同一 `cordis.patch.yml`；
- profile settings.yaml（仅该测试 profile）：`deepseek-v4-flash` + `agent-presets: minimal-windows`（缩短自测轮次）；**未改用户日常 web profile**。

---

## 二 环境预检记录（S2 逐项）

| # | 项 | 结果 |
|---|---|---|
| 1 | mcp 版本 | `importlib.metadata.version('mcp')` = **1.29.0**（<2.0 锁内·FastMCP 可用；`mcp.__version__` 在 1.29 无此属性） |
| 2 | py 解释器 | `C:\Users\Hi\AppData\Local\Python\pythoncore-3.14-64\python.exe`（与上一步同解释器） |
| 3 | RAG 构建 | `py tools/rag_index.py --build` 成功：事实卡 67 + 笔记 282 + 案例 5 + 概念 9 = **363 条**·维度 512·29s |
| 4 | 8080 display 就绪 | `py frontend/serve.py 8080` 后台启动成功（uvicorn :8000 + 8080 反代；`/api/v1/health` 200；RAG 预热 OK）。浏览器开页属用户步（本机无自动截图） |
| 5 | MCP 超时 | `toolCallTimeoutMs` 配置 60000；官方默认 60000（README.md:46）·覆盖空间工具 8-10s 冷启动 |
| 6 | 模型 API 可达 | `py tools/verify_keys.py` 全绿：DeepSeek 0.8s OK（model=deepseek-v4-flash·回显无 key 值）；AMAP place/text/regeo OK（geocode/geo 仍 30001·生产已有本地兜底） |

---

## 三 L0 配置层验证（S3）

- `dsh --profile emc-test --dump-config` 已见 `mcp-emc` 行插入（serverName=emc/stdio/py/cwd/toolCallTimeoutMs 60000）。
- `dsh --profile emc-test-headless "仅列出 mcp__emc 开头工具…"` 实际输出 **8 工具在位**：
  ```
  mcp__emc__buffer
  mcp__emc__kb_facts
  mcp__emc__list_data
  mcp__emc__outlet_card
  mcp__emc__rag_query
  mcp__emc__rank
  mcp__emc__render_spec
  mcp__emc__zonal_stats
  ```
- 额外复验：Python `mcp` SDK stdio client 连 `py tools/mcp_server_emc.py` → `list_tools` 同样 8 工具（说明 server 侧 L0 独立可证）。


## 附：office 侧复建实录（zcode·2026-08-20）

四件套核验/补齐结果（对照 HOME 卡备测节）：

1. **python 依赖**：office pip 默认源被网络阻断（`from versions: none`）——`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple "mcp>=1.0.0,<2.0.0"` 装得 **mcp-1.29.0**（符合锁）。
2. **密钥**：`py tools/verify_keys.py` 全过（DeepSeek/AMAP [OK]·无需处理）。
3. **dsh profile 重建**：照本指引 §1.2-1.4 建 `emc-test`（web 版）+ `emc-test-headless`（自测版）。**两处 office 适配差异**：
   - 依赖协议 `link:` → **`file:`**（office 用 npm·不认 link: 协议报 EUNSUPPORTEDPROTOCOL；家机为 pnpm。`file:D:/Github/dsh/packages/mcp/mcp-client` 等效·npm install 通过）；
   - `agent-presets: minimal-windows` 家机专属预设 office 的 dsh checkout 不存在（仅 code/cordis/minimal/standard）——headless 的 settings.yaml 暂只配 flash 模型，如需缩短轮次再查键名补 `minimal`。
4. **端到端验证**：stdio 冒烟（initialize+tools/list）8 工具列全；`dsh --profile emc-test-headless "仅列出 mcp__emc 开头工具"` 实测输出 **8 个 mcp__emc__* 工具**（server [OK] 启动行入 stderr·D4 修复生效）。

> 注：RAG 预热会阻塞 stdio 响应数秒——冒烟脚本需先 sleep ≥3s 再发 initialize（首次排障曾误判空列表）。
