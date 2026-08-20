# PT-CB6 · home 续点恢复 · 送审通知（zcode → Codex · 2026-08-20）

> 送审方：zcode（主手）。审计方：Codex（审计协助·零实施·一切只读）。性质：home 到岗续点完工送审（dsh rc.8 更新 + synapse 删除 + EMC 入口插件重建 + 黑屏修复）。
> 纪律：分支 `EMC_harness_dsh`（main 冻结勿动）；审计组只读；报告落盘 `PT-CB6-home续点恢复_审计_Codex-2026-08-20.md`。
> 基线：无 pytest 变化（本轮 EMC 仓零触碰生产代码，仅文档写入）。

---

## 一、送审包（两件 + 仓外证据）

| # | 送审件 | 位置 | 要点 |
|---|---|---|---|
| 1 | 执行记录 | `docs/catch-ball/discuss/PT-CB6-home续点恢复_执行记录_zcode-2026-08-20.md` | 五节：dsh rc.8 merge（536 提交/4 冲突/双面构建）、synapse 删除（4 处）、EMC 入口插件重建（rc.8 机制 + 构建链两约束）、黑屏双根因、Codex config 修复 |
| 2 | 插件源码（仓外，git 不入库） | `D:/Github/dsh-emc-entry/`（src/client/index.ts + components.tsx + tsdown.config.ts + package.json + cordis.patch.yml + README.md） | 重建实现全量；构建产物 `lib/client.js`（7.63KB） |
| 3 | dsh 仓改动 | `D:/Github/dsh`（merge `8258d567c4` + `92ae8734ee` + `ec5c5e725c`；未 push） | 登记 stub `packages/emc/emc-entry/`；备份分支 `backup-pre-rc8` |
| 4 | 设计依据 | `PT-CB6-EMC入口重定义任务书_Codex-2026-08-20.md` + `PT-CB6-EMC入口插件_问题复盘与审计交接_Codex-2026-08-20.md` | 需求规格（欢迎卡文案逐字/新会话/外部 Edge）与问题 C（no-cors 探测）出处 |

## 二、审计要点建议（重点请覆盖）

1. **重建忠实度**：新插件实现与任务书需求 1/2 的逐项对照——欢迎卡文案是否逐字（含换行）、"点击=新建会话（standard 预设）"是否等价（`startSession()` 复用空白会话 vs 强新建的语义差）、"不再走内嵌浏览器"是否落实、`start.bat --open=none` 依赖是否在位（EMC 仓 `start.bat:35` 已是 `--open=none`）。
2. **探测纪律回归**：probe 是否保持问题 C 的修复口径（`no-cors` + resolve=可达/reject=不可达 + 不读 status）；60s 节流 + 2s 超时是否与执行记录 R3 一致。
3. **黑屏根因判定**：根因 A（client 插件缺 `export const inject` 服务声明）与根因 B（merge 后未跑 `build:web`，前端 assets 旧构建版本错配）——判定是否成立、是否还有第三根因（如 rc.8 会话/工作区 API 变更未被我覆盖）。
4. **rc.8 构建链约束**（执行记录 §三）：`packages/emc/emc-entry` 登记 stub 是否为最优解（vs 其他接入方式如 `dsh plugin add` 正式包）；stub 会否污染 workspace 构建/打包（已用 `tsdown.config.ts` `entry:''` 跳过，请复核）。
5. **synapse 删除彻底性**：web profile 之外是否仍有残留引用（已查 emc-test / emc-test-headless 无）；`~/.dsh/synapse` 数据删除对 dsh 其他功能（session 存储）有无连带。
6. **config.toml / models.json**（`C:\Users\Hi\.codex\`）：`wire_api = "responses"` + `supports_search_tool = false` 判定是否符合 Codex 0.145.0 行为与 DeepSeek Responses API 文档；`ANTHROPIC_BASE_URL` 等 claude 侧环境变量是否需要同步检查。

## 三、验收口径

- 服务端证据已备（client.js 200 / 页面 DOM 完整渲染 / 预加载清单无 synapse 含 emc-entry）；**浏览器点击链路验收（T4 四项）待主手**，审计组如需可要求复现但零实施。
- dsh 未 push：审计 gitee 远端时以本地 master 为准（ahead 539 / behind 1 已记录）。

## 四、送审 prompt（用户直接转发 Codex · 2026-08-20）

```text
【送审指令 · PT-CB6 home 续点恢复审计】（zcode 主手交付 · 2026-08-20）

你是 Codex 审计组（审计协助·零实施·一切只读）。

任务：审计 zcode 在 home 环境的到岗续点完工件。

一、环境
1. git checkout EMC_harness_dsh && git pull origin EMC_harness_dsh（main 冻结勿动）
2. 先读：docs/catch-ball/discuss/PT-CB6-home续点恢复_送审通知_zcode-2026-08-20.md（含审计要点六项）
3. 再读：docs/catch-ball/discuss/PT-CB6-home续点恢复_执行记录_zcode-2026-08-20.md
4. 仓外证据（只读）：D:/Github/dsh-emc-entry/（插件源码+构建产物）；D:/Github/dsh（本地 master，merge 三提交，未 push）；C:/Users/Hi/.codex/config.toml 与 models.json（Codex 接入配置）

二、审计范围（按送审通知 §二 六项逐条）
1. 重建忠实度：对照 PT-CB6-EMC入口重定义任务书 需求 1/2 逐项核对新插件实现（欢迎卡文案逐字/新建会话语义/外部 Edge/start.bat --open=none 依赖）
2. 探测纪律：no-cors 修复口径是否保持（resolve=可达/reject=不可达/不读 status）
3. 黑屏双根因判定：缺 export const inject 服务声明 + merge 后未跑 build:web 前端旧构建版本错配——判定是否成立、有无第三根因
4. rc.8 构建链：packages/emc/emc-entry 登记 stub 方案是否最优、是否污染 workspace 构建
5. synapse 删除彻底性：残留引用排查、~/.dsh/synapse 数据删除有无连带影响
6. Codex 接入配置：wire_api="responses" + supports_search_tool=false 是否符合 Codex 0.145.0 与 DeepSeek Responses API 文档

三、交付
1. 产出 docs/catch-ball/discuss/PT-CB6-home续点恢复_审计_Codex-2026-08-20.md：逐条 agree/disagree/partial + 证据（file:line 或实测）+ 待修清单（分级）
2. 零实施：不改任何代码/配置，只出报告
3. 若判定有 CRITICAL：在报告开头标注，等主手裁定后再排修复
```

---

> zcode · 2026-08-20 · 送审。用户转发上方 prompt 至 Codex。
