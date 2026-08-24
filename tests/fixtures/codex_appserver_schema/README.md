# codex app-server 协议 Schema 锁（PT-CB15 SPIKE）

> 用途：Codex 版本漂移检测锚点。Codex CLI 升级后重新生成并 diff——差异即协议变化面。
> 版本锚点：**codex-cli 0.149.1**（2026-08-24 spike 实测版·npm `@openai/codex`）
> 稳定性：本锁只覆盖**稳定面**（未加 `--experimental`——实验面无兼容承诺·不依赖）

## 重建命令（派生资产·可重建）

```
codex app-server generate-json-schema --out tests/fixtures/codex_appserver_schema
```

全量产物 = 291 文件 / ~2.95MB（v1/ v2/ 目录 + 逐方法 Params/Response + 聚合
`codex_app_server_protocol.schemas.json` 613KB / `.v2.` 521KB）。按沉淀纪律
（派生资产可重建·只记命令），仓内只留两个锚点文件：

| 文件 | 大小 | 内容 |
|---|---|---|
| `ClientRequest.json` | 182KB | 请求面聚合 schema（initialize/thread/start/turn/start 等全部方法签名） |
| `ClientNotification.json` | 0.4KB | 通知面入口（v2 聚合为逐方法文件·此入口近乎空——通知 schema 见全量重建） |

## 升级检查流程

1. `codex --version` 记录新版本号；
2. 重建到临时目录：`codex app-server generate-json-schema --out $TMP`；
3. `diff` 两版 `ClientRequest.json`（方法增删/参数变化一目了然）；
4. 有差异 → 过一遍 `core/codex_bridge.py` 用到的字段（thread/start·turn/start·
   item/agentMessage/delta·turn/completed）是否受影响。
