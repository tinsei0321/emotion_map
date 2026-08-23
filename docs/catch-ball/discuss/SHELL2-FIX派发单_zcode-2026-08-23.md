# SHELL2(FIX) · 深度审计修复批派发单（Qoder 执行·claude 复审·zcode 收敛）

> 依据：壳工程深度审计收敛（`壳工程深度审计收敛_zcode-2026-08-23.md`）·合并 Qoder+claude 双组审计全部 P1+P2 发现。
> 执行=Qoder·复审=claude·收敛=zcode。commit 前缀 `SHELL2(FIX):`。本地仓即最新·零 pull 零 push。
> 门禁基线 **557+2**·RAG 96.7% 零退化红线。

## P1 必修三件（阻断级）

### FIX-01 dsh 端点并发安全（QA-01+QA-02+C3-3 合并）

**问题**：`post_dsh_engine` 为 sync def → uvicorn 共享线程池（40 槽）同步阻塞至 240s——少量并发 dsh 调用拖垮全部 sync 端点；且无并发限流·多用户同时 spawn dsh（profile 竞争风险）。

**修法**：
1. `api/aiqa_routes.py` post_dsh_engine 改 `async def` + `asyncio.to_thread` 包 subprocess
2. 模块级 `_dsh_semaphore = asyncio.Semaphore(2)`（有界并发·上限 2）
3. 信号量满时排队等待（不快速失败——用户场景低频可接受排队）

### FIX-02 question 长度上限 + OSError 捕获（C3-1）

**问题**：Windows 命令行限 32767 字符·超长问句 subprocess 抛 OSError(WinError 206)→未捕获→500。

**修法**：
1. DshEngineIn.question 加 `max_length=4000`（pydantic 422 语义化拒绝）
2. subprocess.run 外补 `except OSError` → `{ok:False, error:'问句过长或系统限制'}`

### FIX-03 fallback 死路径封死 + OSError 全覆盖（QA-04）

**问题**：Windows 下 `shell=False` + 字符串 cmdline 调 .cmd 跑不起来；若真触发 OSError 未捕获→500。

**修法**：删 fallback 分支（bin.js 缺失→直接 `{ok:False, error:'dsh 安装布局未识别'}` fail-closed）。主路径（node 直调 argv）已覆盖全部已知环境。

## P2 限期修九件

| # | 问题 | 修法 | 来源 |
|---|---|---|---|
| FIX-04 | 前端无总超时护栏 | brain-adapter-dsh.js fetch 加 `Promise.race` 超时（330s>代理 300s）→主动 abort+降级卡 | QA-03/C2-1 |
| FIX-05 | 输出无上限 | post_dsh_engine stdout 截 200KB+截断标记 | QA-05 |
| FIX-06 | _summary 全量序列化 | acp-channel.js 先按类型廉价判长（string slice / Array length / 对象键名列表） | QA-06 |
| FIX-07 | 8600 依赖未声明 | start.bat 或 README 注记 dsh 引擎需 8600 MCP 在跑 | QA-07 |
| FIX-08 | S4 主路 wire 未过 S6 校验 | 新建 s4_wire_dump（fake hooks 驱动 createEngineEmitter 全 14 方法）→jsonschema 三断言 | C5-1 |
| FIX-09 | S5 chips 三态零独立测试 | 新建 test_followup_chips.py（空 cues/ask 互斥/截 3/非串过滤/优先级） | C5-2 |
| FIX-10 | hint 三层断链 | ①acp-channel.js error wire 补 `hint` 字段 ②panel 降级卡前追加一行白名单原因（非裸文本） | X-2/QA-12 |
| FIX-11 | dsh 轮兜底追问不搭调 | panel._followUps 补 `intent==='dsh'` 分支（知识类追问） | C4-1 |
| FIX-12 | caliber 契约对齐 | 契约 v1.1 增补时 caliber 降为「有则带」（S4 发射层暂无工具结果 caliber 源·不硬造） | C1-1 |

## P1 配套测试（随 FIX-01/02/03 同批）

- `tests/test_dsh_engine.py`：monkeypatch subprocess.run 测——命令解析三分支/超时夹取/空问句/超长拒绝(OSError→ok:False)/并发信号量（两请求→一跑一排队）
- FIX-08 S4 wire dump 测试
- FIX-09 chips 三态测试

## DoD

- [ ] P1 三件全修+配套测试全绿
- [ ] P2 九件全修（FIX-12 可仅改契约文档）
- [ ] 全量 pytest **570+ 绿**（557+2 基线+新增约 15 测试）
- [ ] rag_eval 96.7% 零退化
- [ ] 执行记录落盘 `SHELL2-FIX执行记录_Qoder-2026-08-23.md`（白话摘要段+逐件修法+验证数字）
- [ ] 显式路径 commit·零 pull 零 push

## 完成后流转

Qoder 交付 → claude 复审（对照本派发单+两组原审计逐项核验修复到位）→ zcode 收敛终裁。

> zcode 主手 · 2026-08-23 · SHELL2(FIX) 派发
