/**
 * dsh-emc-entry · node half（v2 · 模型当向导）
 * v2 全部动作走客户端服务的正规接口：host.openPath（workspaces 服务）拉起
 * start_silent.vbs / 弹系统默认浏览器；对话注入走 IConversation.send()。
 * node 半不再注册任何路由——保留最小空插件占位（v1 的 /emc/launch 已随
 * 内嵌 tab 方案一并移除）。
 */

export const inject = []

export function apply(_ctx) {
  // 有意留空：v2 无 host 半职责。
}
