window.__ModuleLoader__.load({
	id: "dsh-emc-entry",
	factory: (require) => {
		var module = { exports: {} };
		var exports = module.exports;
		Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
		let react = require("react");
		//#region src/client/index.ts
		/**
		* dsh-emc-entry · client half（v2 · 模型当向导 · 临时测试件）
		* 左下角（sidebar.footer.action）「EMC 情绪地图」入口：
		*  - 点击 → 新建对话 + IConversation.send(固定文本)：模型轮询 emc_status
		*    当向导（工具活动 = 实时进度；预热中提示含预计时长）；
		*  - 并行探测 8080：down → host.openPath(workspace/start_silent.vbs) 静默拉起；
		*  - 自身并行轮询 /emc-ready（2s）→ 就绪 → host.openPath(仓内跳转 HTML)
		*    弹系统默认浏览器（禁内嵌 tab 自动开——预热期乱码教训）；
		*  - 按钮进行中态：点击至就绪置灰/转圈（防重复开多对话），就绪或 90s 超时恢复；
		*    超时不另弹错，对话流自然呈现模型侧的未就绪说明。
		* 设计 token 纪律：颜色全部 var(--dsw-alias-*)，零硬编码 hex。
		*/
		const EMC_READY_URL = "http://127.0.0.1:8080/emc-ready";
		const SEND_TEXT = "请打开 EMC 情绪地图：用 emc_status 轮询 8080 服务状态（每 5 秒一次，预热约 30-60 秒），就绪(ready=true)后用一两句话欢迎我（可引 kb_facts 的 EMC 身份卡），并告诉我地图已在浏览器打开。";
		const PROBE_TIMEOUT_MS = 2e3;
		const POLL_INTERVAL_MS = 2e3;
		const BUSY_TIMEOUT_MS = 9e4;
		const inject = ["slots"];
		/** fetch + 超时中止：探测不阻塞 UI，失败归一为 down。 */
		async function fetchWithTimeout(url, ms) {
			const ctrl = new AbortController();
			const timer = setTimeout(() => ctrl.abort(), ms);
			try {
				return await fetch(url, {
					cache: "no-store",
					signal: ctrl.signal
				});
			} finally {
				clearTimeout(timer);
			}
		}
		/**
		* 三态探测：ready（200）= 前端+后端就绪；starting（503）= 服务在预热，
		* 勿重复启动；down（网络失败）= 8080 未运行，需经 vbs 拉起。
		*/
		async function probeReady() {
			try {
				return (await fetchWithTimeout(EMC_READY_URL, PROBE_TIMEOUT_MS)).ok ? "ready" : "starting";
			} catch {
				return "down";
			}
		}
		/** 经 host.openPath 的正规通道（workspaces 服务）打开路径/URL。 */
		async function openViaHost(ctx, path) {
			// PT-CB10 修复（方式B·主手直改）：better-sidebar 劫持 workspaces.openPath 为侧边栏打开
			// （实测地图被内置弹出且空白）→ 优先走 host 服务原生 openPath（绕过劫持·弹系统浏览器）；
			// rc.7 无 host.openPath 则回退 workspaces.openPath（诚实降级·日志标明通道）。
			const host = ctx.get("host");
			if (host && typeof host.openPath === "function") {
				console.log("[dsh-emc-entry] host.openPath ->", path);
				await host.openPath(path);
				console.log("[dsh-emc-entry] host.openPath ok <-", path);
				return;
			}
			console.log("[dsh-emc-entry] workspaces.openPath ->", path);
			const workspaces = ctx.get("workspaces");
			if (!workspaces?.openPath) throw new Error("workspaces.openPath 服务不可用");
			await workspaces.openPath(path);
			console.log("[dsh-emc-entry] workspaces.openPath ok <-", path);
		}
		/**
		* 新建对话并以用户身份注入固定流程文本（IConversation.send 为对话服务
		* 唯一正规接口——无伪造 assistant 消息的 API，模型回应即真实助手消息）。
		*/
		async function startConversation(ctx) {
			const workspace = currentWorkspace(ctx);
			const sessions = ctx.get("sessions");
			if (!workspace || !sessions?.open) throw new Error("dsh 会话服务不可用（无 workspace 或服务缺失）");
			const workspaces = ctx.get("workspaces");
			if (!workspaces?.connectWorkspace) throw new Error("workspaces.connectWorkspace 服务不可用");
			const sid = await workspaces.connectWorkspace(workspace.workspaceId);
			sessions.open(sid);
			const conversation = (sessions.scope?.(sid))?.get?.("conversation");
			if (!conversation?.send) throw new Error("conversation 服务不可用（会话作用域解析失败）");
			await conversation.send(SEND_TEXT);
		}
		/** 当前 Workspace 即 EMC 仓；路径由 Host 提供，不在插件内写死用户目录。 */
		function currentWorkspace(ctx) {
			const snap = ctx.get("workspaces")?.list?.getSnapshot?.();
			return snap?.items?.find((item) => item.workspaceId === snap?.recentWorkspaceId) ?? snap?.items?.[0];
		}
		function joinWorkspacePath(workspace, ...parts) {
			return [String(workspace.path).replace(/\\/g, "/").replace(/\/+$/, ""), ...parts].join("/");
		}
		/** 模块级进行中标志：跨组件重挂载防重复开多对话（连点守卫第二道）。 */
		let running = false;
		/** 入口主流程：对话先行（≤5s 出现用户消息），探测/拉起/轮询并行推进。 */
		async function runEntry(ctx, settleUi) {
			if (running) return;
			running = true;
			let settled = false;
			let poll;
			const settle = () => {
				if (settled) return;
				settled = true;
				running = false;
				if (poll !== void 0) clearInterval(poll);
				clearTimeout(deadline);
				settleUi();
			};
			const deadline = setTimeout(settle, BUSY_TIMEOUT_MS);
			const workspace = currentWorkspace(ctx);
			const launcherPath = workspace ? joinWorkspacePath(workspace, "start_silent.vbs") : "";
			const mapOpenPath = workspace ? joinWorkspacePath(workspace, "vendor", "dsh-emc-entry", "emc-open.html") : "";
			startConversation(ctx).catch((err) => {
				console.warn("[dsh-emc-entry] 对话注入失败:", err);
			});
			const state = await probeReady();
			console.log("[dsh-emc-entry] probe =", state);
			if (state === "down") openViaHost(ctx, launcherPath).catch((err) => {
				console.warn("[dsh-emc-entry] 拉起 EMC 失败:", err);
			});
			else if (state === "ready") {
				await openViaHost(ctx, mapOpenPath).catch((err) => {
					console.warn("[dsh-emc-entry] 打开浏览器失败:", err);
				});
				settle();
				return;
			}
			poll = setInterval(() => {
				probeReady().then((s) => {
					if (s !== "ready" || settled) return;
					openViaHost(ctx, mapOpenPath).then(settle, settle);
				});
			}, POLL_INTERVAL_MS);
		}
		function glyph() {
			return (0, react.createElement)("svg", {
				width: 16,
				height: 16,
				viewBox: "0 0 16 16",
				fill: "none",
				"aria-hidden": true,
				style: {
					display: "block",
					flex: "none"
				}
			}, (0, react.createElement)("path", {
				d: "M2 5.3C2 3.5 4.7 1.8 8 1.8s6 1.7 6 3.5c0 2.6-3.5 5.9-6 9-2.5-3.1-6-6.4-6-9Z",
				stroke: "currentColor",
				strokeWidth: 1.2,
				strokeLinejoin: "round"
			}), (0, react.createElement)("circle", {
				cx: 8,
				cy: 5.3,
				r: 1.7,
				stroke: "currentColor",
				strokeWidth: 1.2
			}));
		}
		/** 进行中态的转圈图标（纯 currentColor，动画只用 transform）。 */
		function spinnerGlyph() {
			return (0, react.createElement)("svg", {
				width: 16,
				height: 16,
				viewBox: "0 0 16 16",
				fill: "none",
				"aria-hidden": true,
				style: {
					display: "block",
					flex: "none"
				}
			}, (0, react.createElement)("circle", {
				cx: 8,
				cy: 8,
				r: 6,
				stroke: "currentColor",
				strokeWidth: 1.6,
				strokeLinecap: "round",
				strokeDasharray: "9 28",
				"data-spin": ""
			}));
		}
		function Entry(props) {
			const [busy, setBusy] = (0, react.useState)(false);
			return (0, react.createElement)("button", {
				type: "button",
				"data-dsh-emc-entry": "",
				"data-rail": String(!props.wide),
				"data-busy": String(busy),
				title: busy ? "EMC 地图启动中（预热约 30-60 秒），就绪后自动在浏览器打开" : "打开 EMC 情绪地图（新对话 + 模型向导 + 启动地图）",
				"aria-label": "EMC 情绪地图",
				"aria-busy": String(busy),
				onClick: () => {
					if (busy) return;
					setBusy(true);
					props.run(() => setBusy(false));
				}
			}, busy ? spinnerGlyph() : glyph(), props.wide ? (0, react.createElement)("span", { "data-label": "" }, busy ? "EMC 启动中…" : "EMC 情绪地图") : null);
		}
		function apply(ctx) {
			ctx.effect(() => {
				const style = document.createElement("style");
				style.dataset.plugin = "dsh-emc-entry";
				style.textContent = [
					"[data-dsh-emc-entry]{flex:none;display:flex;align-items:center;gap:8px;width:calc(100% + 4px);height:42px;margin:4px -2px;padding:0 10px 0 8px;box-sizing:border-box;border:none;border-radius:12px;background:transparent;cursor:pointer;overflow:hidden;color:var(--dsw-alias-label-primary);font-family:inherit;font-size:14px;line-height:22px;text-align:left}",
					"[data-dsh-emc-entry]:hover{background:var(--dsw-alias-interactive-bg-hover)}",
					"[data-dsh-emc-entry]:active{background:var(--dsw-alias-interactive-bg-active)}",
					"[data-dsh-emc-entry]:focus-visible{outline:none;box-shadow:0 0 0 2px var(--dsw-alias-border-l3)}",
					"[data-dsh-emc-entry][data-rail=\"true\"]{width:36px;height:36px;margin:8px 0 10px;justify-content:center;gap:0;padding:0;border-radius:50%}",
					"[data-dsh-emc-entry] [data-label]{min-width:0;flex:1;white-space:nowrap;text-overflow:ellipsis;overflow:hidden}",
					"[data-dsh-emc-entry][data-busy=\"true\"]{color:var(--dsw-alias-label-tertiary);pointer-events:none;cursor:default}",
					"[data-dsh-emc-entry] [data-spin]{transform-box:fill-box;transform-origin:center;animation:dsh-emc-entry-spin 0.9s linear infinite}",
					"@keyframes dsh-emc-entry-spin{to{transform:rotate(360deg)}}"
				].join("");
				document.head.appendChild(style);
				return () => {
					style.remove();
				};
			}, "dsh-emc-entry: styles");
			ctx.slots.inject("sidebar.footer.action", () => ctx.slots.register({
				name: "sidebar.footer.action",
				id: "dsh-emc-entry",
				order: 20,
				inject: () => ({ run: (settleUi) => {
					runEntry(ctx, settleUi);
				} })
			}, Entry));
		}
		//#endregion
		exports.apply = apply;
		exports.inject = inject;
		return module.exports;
	}
});
