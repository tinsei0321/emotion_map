# 视觉中转站 (Vision Inbox)

> **首选方式**：[vision-bridge MCP Server](../.claude/mcp_servers/vision_bridge_server.py)
> 自动调火山引擎 Ark Vision API 识图，无需手动操作。
> 下文的手动文本桥接仅在 MCP Server 不可用时作为备用方案。

## 首选工作流（MCP 自动化）

```
你: [粘贴图片到对话框]
         │
         ▼
VS Code 自动保存到 %LOCALAPPDATA%\Temp\ScreenShot_*.png
         │
         ▼
本项目 Claude 自动调用 mcp__vision-bridge__analyze_image 工具
         │
         ▼
火山引擎 Ark Vision API 识图 → 返回文字描述 → 回复你
```

**无需任何手动操作**。CLAUDE.md 第 11 条规则确保自动触发。

## 备用工作流（手动文本桥接）

MCP Server 不可用时：在另一个支持图片的 Chat 中粘贴图片，让其写入 `latest.md`。

## 文件约定

| 文件 | 写入方 | 读取方 | 用途 |
|------|--------|--------|------|
| `latest.md` | 另一个 Chat | 本项目 Claude | **最新一次识图结果**（每次覆盖） |
| `history/` | 另一个 Chat | 本项目 Claude | 历史记录归档（可选） |

## 另一个 Chat 的写入指令

在另一个支持图片的 Chat 中，发送图片后附上这段指令：

> 请详细描述这张图片的内容。将描述文字写入文件：
> 路径：`docs/vision-inbox/latest.md`
> 格式：
> ```
> # 识图结果 — [当前时间]
> 
> ## 概述
> [一段话总结]
> 
> ## 详细描述
> [逐区域/逐元素描述]
> ```

## 本项目 Claude 的自动行为

我（本项目 Claude）会在以下时机自动检查：
- 你提到"看图"、"识图"、"图片"时
- 你告诉我"最新的图来了"

无需指定文件路径，我知道读 `docs/vision-inbox/latest.md`。
