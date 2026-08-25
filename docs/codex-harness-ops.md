# Codex Harness（COH）运维纪律与自测指引（PT-CB15 PROMOTE·2026-08-24）

> 依据：PT-CB15 spike 执行记录 + 三方收敛处置表。引擎契约见 `docs/brain-adapter.md`，
> 配置复刻清单见 spike 执行记录 §八，协议版本锁见 `tests/fixtures/codex_appserver_schema/`。

## 一 运维纪律（硬约束）

1. **同机只跑一个后端实例**（最重要·P2-10/C-2）：
   render_inbox 投递通道是「单消费源」设计——两个后端（如 8000/8001）并存时，
   虽有竞争锁保证只有一个实例消费，但**页面连的是哪个后端，图就只出现在哪个后端**，
   另一页静默收不到（spike Q4 实证「图亮在隔壁屏幕」）。
   → 换端口组合前**先杀旧后端**；`start.bat` 已自带 8080/8000 清理，但不代清自起组合。
2. **MCP 8600 必须在位**：codex 引擎 `required=true`——8600 未起时工具调用快速失败
   （不静默退化）。`start.bat` 第一段已保证；手工起后端时先确认
   `netstat -ano | findstr ":8600.*LISTENING"`。
3. **Codex 配置仓外**：`~/.codex/config.toml` / `auth.json` 不入仓·密钥不入档；
   双机按复刻清单各配（spike 记录 §八）。
4. **cwd 隔离**：桥恒用 `{REPO}` 同级 `_codex_cwd`（P2-2 推导·勿改回本仓内——
   防 9-Agent 协作规范 AGENTS.md 注入 Codex 上下文）。
5. **升级纪律**：Codex CLI 升级 → 先 `codex app-server generate-json-schema --out` 重建
   并与仓内 `ClientRequest.json` diff（版本锁流程见该目录 README）。

## 二 自测指引（用户怎么测）

```
① 双击 start.bat（起 8600 + 8080/8000 最新代码）
② 浏览器打开 http://localhost:8080/frontend/index.html?engine=codex
③ 展开 EMC 面板 → 见绿色「引擎·codex」徽标 → 直接提问
④ 观察：逐字打字 + 工具调用条目（emc.* begin/end）+ 出图（工具链含 render_spec 时）
```

开发自测（不动主组合·独立端口）：`py frontend/serve.py 8081 --backend-port 8001`，
结束后杀 8081/8001 两进程（纪律 1）。

故障速查：
| 现象 | 先查 |
|---|---|
| 「Codex 桥启动失败」 | `codex --version`（未装：`npm i -g @openai/codex --registry=https://registry.npmmirror.com`） |
| 工具调用被拒/要求审批 | 走的是 app-server 主路？（exec 通道有独立审批语义·见 spike 记录 K-1） |
| 模型回答「数据状况待确认」/不调 emc 工具 | 数据目录或路径变更后未重启 8600/8000/8080；先杀旧进程再重启三服务 |
| 出图页面无反应 | 纪律 1——是否两个后端并存；看哪个后端日志有「watcher 让出消费权」 |
| turn 超时 | 复杂工具链 50-366s 正常区间；超 300s 收口为 `CODEX_TURN_TIMEOUT`（含 stderr_tail 诊断·P2-5） |

## 三 环境变量（P2-4）

| 变量 | 默认 | 说明 |
|---|---|---|
| `CODEX_MODEL_PROVIDER` | `deepseek` | 桥 spawn `-c model_provider=` 覆盖（用户令 08-24：DeepSeek Flash） |
| `CODEX_MODEL` | `deepseek-v4-flash` | 桥 spawn `-c model=` 覆盖（官方最新规则：弃用 `deepseek-chat` 旧别名，用规范名） |
| `CODEX_REASONING_EFFORT` | `high` | 桥 spawn `-c model_reasoning_effort=` 覆盖（v4-flash 默认思考模式） |

> 只作用于 COH 桥进程·用户桌面 Codex 顶层配置不受影响。

> **DeepSeek 规范名 + MCP 工具可见性（必读）**：`~/.codex/models.json` 里 `deepseek-v4-flash` / `deepseek-v4-pro` 若为 `"supports_search_tool": true` 且 `"tool_mode": null`，Codex 会把全部 MCP 工具设为 Deferred，导致 `list_data`/`zonal_stats`/`render_spec` 等 emc 工具在模型工具面中静默消失（只见 `list_mcp_resources`）。到岗/换机时必须把这两条模型的 `supports_search_tool` 改为 `false`；改后重启后端并跑一次 codex_engine 工具链验证。
