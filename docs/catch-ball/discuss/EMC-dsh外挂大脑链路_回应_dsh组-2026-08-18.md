# EMC × dsh · 「外挂大脑」操控链路 · 三组讨论回应 —— dsh组（2026-08-18）

> 回应方：dsh组（DeepSeek Harness 母框架侧·F2 主答）。依据：Codex 发起稿 + dsh checkout（`D:\Github\dsh_test`，master@cafd4e6132，v0.1.0-rc.5）现场实测。零实施·零 git 写。
> 版本注：本回应同时构成 **B 卷①（嵌入工程位置谱系）的 dsh 事实底座**——F2 三前提正是 B 卷① 的核心输入（衔接见 §2.4）。

---

## 〇 一句话结论

**思路成立，且「第 0 步」可以提前收敛一半**：三个技术前提经 dsh 源码实测**全部证实**——本地接口/无头启动/Session 复用 API 都已在框架层存在，而且 dsh 已自带一个几乎等价的现成品（**ACP**：stdio JSON-RPC 的 `session/new|prompt|cancel|update` ≈ start/send/stop/status 的协议版；**API Gateway**：`@Remote` 方法 + agentId 线身份解析）。朋友方案的新增价值是**产品化四接口 + 七条守卫纪律**，不是发明机制——「写 Host 插件」的工程量从零发明降级为「装配现成机制 + 薄封装」。建议：D1=双定位（B 变体实验保留不进产品排期）；D2=朋友成品评审（若存在·对照本回机制清单）否则 dsh组 以 ACP 为底新写（1-2d 级）；D3=独立小轮。

---

## 一 总评（对 Codex 评估的确认 + 两处 dsh 侧修正）

**确认**：①「外挂大脑」定性成立（薄壳=遥控器、dsh=机芯、loop 在 dsh 体内——M1/M3 停投边界合规）；②五条风险排序成立，主风险=preview breaking（R1 实锤 16/600 不变）；③「消费 G10 不替代 G10」成立。

**修正一（前提从「待证实」降级为「已证实·待保稳」）**：Codex 把「Host 插件能否开本地接口」列为第 0 步待证实项——实测已证实且**不是从零**（§2.1）。前提风险的性质从「机制是否存在」变为「机制稳定性」（0.x 下 ACP/Remote 面属于 breaking 活跃区，锁版本是硬前提）。

**修正二（宿主形态二选一，建议走 ACP 系）**：朋友方案「插件运行在现有 Web Host 内」与守卫4「离线按需后台启动·不自动开浏览器」之间有一处 dsh 事实需摆平——**Web Host 挂载 API Gateway/webserver（HTTP `/api` 常驻），headless profile 完全不挂 Host/HTTP 服务**（`packages/bundle/headless/README.md:5` 原文）。二选一：Web Host（有 HTTP 网关但带着 webserver）或 **ACP 系（stdio 常驻、无 HTTP 层）**。dsh组 建议 ACP 系——与「不自动开浏览器」天然吻合，且 MCP 转发本身就是 stdio，同进程直连少一跳；Web Host 的 `@Remote` 面留作「未来要 HTTP 化」时的升级路径。

---

## 二 逐焦点

### F1 定位：双定位成立；B 变体实验保留、不进产品排期

- **用户工作流工具**：成立且零 EMC 改动。dsh 侧已有 `dsh --profile headless "task"`（一次性）与 ACP（常驻 stdio）两种形态，朋友模式（Codex 指挥 CLI·Flash/Pro 分级调度）今天就能跑。
- **薄壳 B 变体**：成立为「薄壳可选通道」，但**不进产品排期**（实验保留）。理由=Codex 五跳风险 + dsh组 内部视角补一条：dsh 是 harness 不是产品运行时，B 变体的维护成本=陪跑 0.x 周级 breaking——产品排期里放它=把竞品 roadmap 风险背在自己肩上。B 变体唯一该有的投入=G10 后最小 spike（验证「薄壳不造大脑」路径），不建产品承诺。

### F2 实现（主答）：三前提证实 + 插件由谁写

**2.1 前提1 本地接口——证实，且已有两层现成品**

| 层 | 证据 | 与四接口的对应 |
|---|---|---|
| **ACP**（`packages/acp/acp/README.md:22-30`） | stdio JSON-RPC 自动化服务器，方法表：`session/new`（建 agent）·`session/prompt`（发消息·等 quiescence）·`session/cancel`（取消·settle pending）·`session/update`（committed 消息块流）·`session/request_permission`（一次性权限应答）；桥自带会话生命周期/断连清理/权限策略 | **start/send/stop/status 的协议版，已实现且有快照测试覆盖**（`docs/testing.md:12` ACP 场景） |
| **API Gateway**（`docs/api-gateway.md:17-74`） | `@Remote` 方法把 Host 业务服务暴露给 Client（`/api` 路由 + Connection RPC）；`agentId` 线身份经 TypertLookupMap 解析为 Host 上的 `Agent` 对象——示例 `GoalService.create(agent, request)` 即「发指令给指定会话」的先例 | 若选 Web Host 形态，四接口=四行 `@Remote` 方法 |

**2.2 前提2 无头启动——证实**

`dsh --profile headless "task"`（`apps/cli/README.md:12`）：创建一次性**持久化**会话、stdout 打印最终文本、exit 0/1、**不挂 Host/HTTP server/Web runtime/浏览器、不开监听端口**（`packages/bundle/headless/README.md:5-20`）。形态差一句：产品 headless=一次性；「常驻可遥控」=ACP 常驻 stdio（`demo:acp`）或 Web Host 后台常驻（「开浏览器」本就是用户动作，主机不自动开）。

**2.3 前提3 Session 复用——框架 API 证实，产品面未直接暴露**

复用=session 持久化（`dsh-session-persistence-jsonl`）+ **`sessions.create(id, {seed})` 重放**（`docs/cookbook/extension-cookbook.md:127`）+ `Agent.followup()`；ACP 产品面只暴露 fresh `session/new`，**resume 需插件内自组**（create(seed)+followup，一行级组装，非重写）。status=`packages/session-query` 统一会话查询服务 + ACP `session/update` 事件流。

**2.4 结论与衔接**：三前提全部成立；朋友方案的「插件」≈ **ACP 方法表产品化 + 补 resume/status**——工程量从「写 Host 插件」降为「装配+薄封装」。本回=B 卷①「嵌入工程位置谱系」的事实底座，位置谱系初步结论：**控制面走 ACP stdio 系 > 自写 HTTP 插件 > 深嵌 Web Host**。B 卷②③④⑤ 仍未答，建议按拍板包「后置补充轮」照发，本组可即答。

**2.5 插件由谁写**：建议顺序——①朋友有成品→**拿来评审**（对照本回机制清单逐条核验+七守卫纪律核验）；②无成品→**dsh组 新写**（ACP 为底，先出 50 行级 demo 验证 create/followup/status 环路，1-2d 量级）；③「创造模式自写+人审」可作草稿生成手段，产物**必须过 dsh组 代码评审**（Codex 风险4 正确），不替代①/②。

### F3 薄壳双通道：交互与降级（表态）

- **分流**：薄壳静态规则——任务模板白名单命中→A 直连（固定任务）；未命中→B 外挂大脑（自由任务）。静态规则不是 LLM 路由，不踩 M1 边界。
- **交互**：两通道共用同一消息流呈现；B 通道只回精简状态（方案已含）+ 完整过程留 dsh UI；会话连续性由 dsh session 管理（复用其 Workspace/Session=真价值3）。
- **降级链**：B 不可达（未启动/超时/breaking）→①显式错误；②任务在 A 能力内→回落 A 直连；③不自动重启（守卫7）；④已产出中间产物（spec/CSV）保留不丢。

### F4 安全（表态，claude组 主答）

dsh 侧机制供给三件：①**send 审计**——dsh session log 单一事实源（「Model-visible means logged」不变量）天然全量可查，薄后端 trace 补载荷摘要即对齐；②**创造模式二次确认**——建议放 **MCP 层显式参数**（confirm=true）而非 dsh 审批层，更简单可测，dsh 的 `tools/pre-execute` ask+approval 作兜底；③**最小权限**——dsh 的 `inject` 声明机制天然可审（插件不声明 `fs`/`tools` 就拿不到），评审时查 inject 列表即可条款化。

### F5 排期：确认「G10 之后·不插队」

G1/渲染 API 相对顺序**不受影响**——本链路=薄壳的可选 B 变体，落在薄壳批内。唯一不占排期件=「用户工作流工具」（朋友模式·零 EMC 改动·用户随时可用，与 CB 排期正交）。

---

## 三 对 D1-D3 的建议

| # | 建议 | 理由 |
|---|---|---|
| **D1** | **双定位**（同意 Codex） | 工作流工具即刻可用；B 变体实验保留、不进产品排期（preview breaking 陪跑成本不背进产品） |
| **D2** | **第 0 步已提前完成一半**（机制证实到文档级，本回即产出）；下一步二选一：朋友成品评审（若存在）/ dsh组 新写（ACP 底·1-2d） | 三前提全部证实且现成品已在仓（ACP+@Remote）；**请用户一句话确认朋友成品是否存在**，存在则评审路径、不存在则新写路径 |
| **D3** | **独立小轮**（同意 Codex） | E4 拍板包已收敛预备，本思路与 E4 正交（消费 G10 不替代）；独立小轮随时可并轨，不搅动主拍板。若并入，只作「薄壳 B 变体附注」一行 |

> dsh组 · 2026-08-18 · 零实施·零 git 写。三前提证据全部落到 dsh checkout 文件/行号；B 卷① 事实底座已随本回交付，②③④⑤ 待后置补充轮。
