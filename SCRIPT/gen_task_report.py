# -*- coding: utf-8 -*-
"""从 DSH 会话日志生成《任务过程与成本报告》Markdown。

读取当前会话 session.jsonl.zstd，解析 turn/step/reasoning/tool-call/tool-result/usage，
生成一份面向分析团队的完整 Loop 报告。机器可读中间产物另存 session_parse.json。

用法（PT-CB7 T8 会话路径参数化·缺省=首次任务原路径）：
  py SCRIPT/gen_task_report.py --log <session.jsonl.zstd> [--out-md <路径>] [--out-json <路径>]
"""
import argparse
import json
import os
import zstandard

DEFAULT_LOG = r"C:\Users\Hi\.dsh\sessions\--D-Github-dsh_test--\session-f49179a1-21f8-454e-b2ed-da1c1b2b49a4\session.jsonl.zstd"
DEFAULT_OUT_DIR = r"D:\Github\emotion_map\DATA\exports\12345_800m方格"
# 以下三个由 main() 的 argparse 覆写（保留模块常量供兼容引用）
LOG = DEFAULT_LOG
OUT_MD = os.path.join(DEFAULT_OUT_DIR, "任务过程与成本报告.md")
OUT_JSON = os.path.join(DEFAULT_OUT_DIR, "session_parse.json")


def load_events(path):
    dctx = zstandard.ZstdDecompressor()
    with open(path, "rb") as fh:
        text = dctx.stream_reader(fh).read().decode("utf-8", errors="replace")
    events = []
    for line in text.splitlines():
        try:
            events.append(json.loads(line))
        except Exception:
            continue
    return events


def fmt_ms(ms):
    if ms is None:
        return "进行中"
    sec = ms / 1000.0
    if sec < 60:
        return f"{sec:.1f}s"
    return f"{int(sec // 60)}m{sec % 60:.1f}s"


def code_block(text, max_len=None):
    if max_len and len(text) > max_len:
        text = text[:max_len] + f"\n…[截断，原文 {len(text)} 字符，完整见 session_parse.json/原始日志]"
    return "```text\n" + text + "\n```"


def main(argv=None):
    global LOG, OUT_MD, OUT_JSON
    ap = argparse.ArgumentParser(description="DSH 会话日志 → 任务过程与成本报告")
    ap.add_argument("--log", default=DEFAULT_LOG, help="session.jsonl.zstd 路径")
    ap.add_argument("--out-md", default="", help="报告 md 输出路径（缺省=默认输出目录）")
    ap.add_argument("--out-json", default="", help="session_parse.json 输出路径（缺省=默认输出目录）")
    args = ap.parse_args(argv)
    LOG = args.log
    out_md = args.out_md or os.path.join(DEFAULT_OUT_DIR, "任务过程与成本报告.md")
    out_json = args.out_json or os.path.join(DEFAULT_OUT_DIR, "session_parse.json")
    OUT_MD, OUT_JSON = out_md, out_json
    events = load_events(LOG)

    # 元信息
    meta = next((e for e in events if e.get("type") == "session"), {})
    req_header = next((e for e in events if e.get("type") == "request/header"), {})
    req_ctx = next((e for e in events if e.get("type") == "request/context"), {})
    header = req_header.get("data", {}).get("header", {})
    config = header.get("config", {})
    tools = header.get("tools", [])

    # 工具结果索引
    tool_results = {}
    for e in events:
        if e.get("type") != "tool/result":
            continue
        d = e.get("data", {})
        msg = d.get("message", {})
        call_id = None
        texts = []
        for c in msg.get("content", []):
            if c.get("type") == "tool-result":
                call_id = c.get("toolCallId")
                for cc in c.get("content", []):
                    if cc.get("type") == "text":
                        texts.append(cc.get("text", ""))
        if call_id:
            full = "\n".join(texts)
            tool_results[call_id] = full

    # 结构化 turn
    turns = {}
    order = []
    for e in events:
        t = e.get("type")
        if t == "turn/start":
            turn = e["data"]["turn"]
            turns.setdefault(turn, {
                "start": e.get("time"), "end": None, "reason": None,
                "steps": {}, "step_order": [], "tool_calls": [],
                "reasonings": [], "texts": [], "usages": [],
            })
            order.append(turn)
        elif t == "turn/end":
            turn = e["data"]["turn"]
            if turn in turns:
                turns[turn]["end"] = e.get("time")
                turns[turn]["reason"] = e["data"].get("reason")
        elif t == "step/start":
            turn = e["data"]["turn"]; step = e["data"]["step"]
            turns.setdefault(turn, {
                "start": None, "end": None, "reason": None,
                "steps": {}, "step_order": [], "tool_calls": [],
                "reasonings": [], "texts": [], "usages": [],
            })
            if step not in turns[turn]["steps"]:
                turns[turn]["steps"][step] = {"start": e.get("time"), "end": None}
                turns[turn]["step_order"].append(step)
        elif t == "step/end":
            turn = e["data"]["turn"]; step = e["data"]["step"]
            if turn in turns and step in turns[turn]["steps"]:
                turns[turn]["steps"][step]["end"] = e.get("time")
        elif t == "assistant/message":
            d = e.get("data", {})
            turn = d.get("turn"); step = d.get("step")
            turns.setdefault(turn, {
                "start": None, "end": None, "reason": None,
                "steps": {}, "step_order": [], "tool_calls": [],
                "reasonings": [], "texts": [], "usages": [],
            })
            if "usage" in d:
                turns[turn]["usages"].append({"step": step, **d["usage"]})
            for c in d.get("message", {}).get("content", []):
                if c.get("type") == "reasoning":
                    turns[turn]["reasonings"].append({"turn": turn, "step": step, "text": c.get("text", "")})
                elif c.get("type") == "text":
                    turns[turn]["texts"].append({"turn": turn, "step": step, "text": c.get("text", "")})
        elif t == "tool/call":
            d = e.get("data", {})
            turn = d.get("turn"); step = d.get("step")
            turns.setdefault(turn, {
                "start": None, "end": None, "reason": None,
                "steps": {}, "step_order": [], "tool_calls": [],
                "reasonings": [], "texts": [], "usages": [],
            })
            turns[turn]["tool_calls"].append({
                "seq": e.get("seq"), "time": e.get("time"), "turn": turn, "step": step,
                "callId": d.get("callId"), "name": d.get("name"), "arguments": d.get("arguments", ""),
            })

    # 生成 Markdown
    md = []
    md.append("# 12345 热线 800m 方格聚合任务 · 完整过程与成本报告\n")
    md.append("> 本报告由 DSH 会话日志自动生成，并补充意图判断与结果范式分析。\n")
    md.append("> 原始日志：`" + LOG + "`\n")
    md.append("> 机器可读解析：`" + OUT_JSON + "`\n")
    md.append("> 生成时间：2026-08-20\n")
    md.append("\n---\n")

    # 0 会话与模型
    md.append("## 0. 会话与模型信息\n")
    md.append("| 项 | 值 |")
    md.append("|---|---|")
    md.append(f"| Session ID | {meta.get('id')} |")
    md.append(f"| 工作目录 | `{meta.get('cwd')}` |")
    md.append(f"| 创建时间 | {meta.get('createdAt')} |")
    md.append(f"| Agent Preset | {meta.get('agentPreset')} |")
    md.append(f"| 模型 Provider | {config.get('provider')} |")
    md.append(f"| 模型 | {config.get('model')} |")
    md.append(f"| Reasoning Effort | {config.get('reasoningEffort')} |")
    md.append(f"| Max Tokens | {config.get('maxTokens')} |")
    md.append(f"| Context Window | {req_ctx.get('data', {}).get('contextWindow')} |")
    md.append(f"| 工具数量 | {len(tools)} |")
    md.append("\n---\n")

    # 1 成本统计
    md.append("## 1. 成本客观统计\n")
    md.append("### 1.1 Turn 总览\n")
    md.append("| Turn | 状态 | 耗时 | Steps | 工具调用 | Thinking 条数 | Input Tokens | Output Tokens | Cache Read | Reasoning Tokens | 约当总 Token |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|")
    grand = {"input": 0, "output": 0, "cache": 0, "reason": 0, "steps": 0, "tools": 0}
    for turn in order:
        info = turns[turn]
        dur = (info["end"] - info["start"]) if info["end"] else None
        reason = info.get("reason") or {}
        status = "completed" if info["end"] and reason.get("kind") == "completed" else ("aborted" if reason.get("kind") == "aborted" else "ongoing")
        n_steps = len(info["steps"])
        n_tools = len(info["tool_calls"])
        n_reason = len(info["reasonings"])
        inp = sum(u.get("inputTokens", 0) for u in info["usages"])
        out = sum(u.get("outputTokens", 0) for u in info["usages"])
        cache = sum(u.get("cacheReadTokens", 0) for u in info["usages"])
        reason = sum(u.get("reasoningTokens", 0) for u in info["usages"])
        total = inp + out + cache + reason
        grand["input"] += inp; grand["output"] += out; grand["cache"] += cache; grand["reason"] += reason
        grand["steps"] += n_steps; grand["tools"] += n_tools
        md.append(f"| {turn} | {status} | {fmt_ms(dur)} | {n_steps} | {n_tools} | {n_reason} | {inp} | {out} | {cache} | {reason} | {total} |")
    gt = grand["input"] + grand["output"] + grand["cache"] + grand["reason"]
    md.append(f"| 合计 | - | - | {grand['steps']} | {grand['tools']} | - | {grand['input']} | {grand['output']} | {grand['cache']} | {grand['reason']} | {gt} |")
    md.append("\n> 注：`约当总 Token` = input + output + cacheRead + reasoning 的简单加和；实际计费时 cacheRead 通常远低于 input 单价，且不同供应商计费规则不同。Turn 3 为当前报告生成任务，仍在进行中，数据为截至生成时刻的累计。\n")

    # 1.2 工具调用统计
    md.append("### 1.2 工具调用类型分布\n")
    from collections import Counter
    tool_counter = Counter()
    for turn in order:
        for tc in turns[turn]["tool_calls"]:
            tool_counter[tc["name"]] += 1
    md.append("| 工具 | 调用次数 |")
    md.append("|---|---|")
    for name, cnt in tool_counter.most_common():
        md.append(f"| {name} | {cnt} |")
    md.append("\n---\n")

    # 2 Loop 报告
    md.append("## 2. 计划-执行流水线完整记录（Loop Report）\n")
    md.append("> 以下按 Turn 1（12345 聚合主任务）逐步展开；Turn 2/3 见 2.4/2.5。\n")
    md.append("\n### 2.0 Harness / Agent Loop 运作机制说明\n")
    md.append("""DSH 会话日志以事件流方式记录了 Agent Loop 的完整路径，本报告依据以下事件类型还原执行过程：

| 事件类型 | 含义 | 对应本报告呈现 |
|---|---|---|
| `turn/start` / `turn/end` | 一次用户请求的完整回合（可含多个 step） | Turn 1/2/3 |
| `step/start` / `step/end` | 一次“模型生成 + 工具执行”循环单元 | Step N |
| `assistant/chunk` | 模型流式输出（reasoning / text / usage / tool-call） | thinking 与 token 统计 |
| `reasoning-chunks` | 流式思考分片 | 合并为 Thinking 全文 |
| `tool-call-chunks` | 流式工具调用参数分片 | 工具调用参数 |
| `tool/call` | Harness 实际发起工具调用（FC） | 工具调用记录 |
| `tool/result` | 工具执行结果回填 | 结果摘要 |
| `assistant/message` | 每个 step 结束时的完整模型消息（含 usage） | 每步 token 与最终文本 |
| `text-chunks` | 最终面向用户的文本流式输出 | 文本输出 |

**Agent Loop 路径**：用户消息 → turn/start → 循环 step（模型思考 → 并行/串行 FC → 工具结果回填 → 模型继续）→ step/end → 直到模型产出最终文本 → turn/end。
本次任务中，Turn 1 共循环 **56 个 step**，其中多数 step 含工具调用；工具以本地 PowerShell（`pwsh`）、文件编辑（`str_replace_editor`）、记忆检索（`memory_*`）为主，未观察到外部网络型 MCP 工具调用（全部为本地/项目内工具）。
""")
    md.append("\n")

    # 2.1 阶段划分
    md.append("### 2.1 阶段划分（基于 thinking 内容归纳）\n")
    md.append("| 阶段 | Steps | 内容 |")
    md.append("|---|---|---|")
    md.append("| ① 上下文与数据侦察 | 1–5 | 查记忆项目全景、定位 emotion_map 数据目录 |")
    md.append("| ② 数据探查 | 6–13 | 读取 CSV/GeoJSON 结构、统计坐标与分类分布 |")
    md.append("| ③ 工具与机制调研 | 14–20 | 阅读 grid_export / spatial_analysis / geo_registry，确认 800m 聚合能力 |")
    md.append("| ④ 方案设计与脚本编写 | 21–38 | 编写 gen_12345_grid_800m.py，处理 ok 点过滤、分类统计、输出 |")
    md.append("| ⑤ 运行调试与迭代 | 39–52 | 多次运行脚本，修复列冲突/边界漏配/区域统计等问题 |")
    md.append("| ⑥ 分析与总结 | 53–56 | 生成统计摘要、撰写分析 md、记忆落库 |")
    md.append("\n")

    # 2.2 Turn 1 每步明细
    md.append("### 2.2 Turn 1 每步 Loop 明细\n")
    turn = 1
    info = turns[turn]
    reasoning_by_step = {}
    for r in info["reasonings"]:
        reasoning_by_step.setdefault(r["step"], []).append(r["text"])
    text_by_step = {}
    for t in info["texts"]:
        text_by_step.setdefault(t["step"], []).append(t["text"])
    usage_by_step = {}
    for u in info["usages"]:
        usage_by_step[u["step"]] = u
    calls_by_step = {}
    for tc in info["tool_calls"]:
        calls_by_step.setdefault(tc["step"], []).append(tc)

    for step in info["step_order"]:
        st = info["steps"][step]
        dur = (st["end"] - st["start"]) if st["end"] else None
        usg = usage_by_step.get(step, {})
        md.append(f"#### Step {step}（耗时 {fmt_ms(dur)}）\n")
        if usg:
            md.append(f"- Input {usg.get('inputTokens')} / Output {usg.get('outputTokens')} / CacheRead {usg.get('cacheReadTokens')} / Reasoning {usg.get('reasoningTokens')}\n")
        # thinking
        for text in reasoning_by_step.get(step, []):
            md.append("**Thinking 全文：**\n")
            md.append(code_block(text))
            md.append("\n")
        # tool calls
        calls = calls_by_step.get(step, [])
        if calls:
            md.append("**工具调用：**\n")
            for tc in calls:
                md.append(f"- `{tc['name']}` (callId: `{tc['callId']}`)")
                args = tc.get("arguments", "")
                md.append("  参数：\n")
                md.append(code_block(args, max_len=4000))
                result = tool_results.get(tc["callId"])
                if result is not None:
                    md.append(f"  结果（原始 {len(result)} 字符，摘要前 1200 字符）：\n")
                    md.append(code_block(result, max_len=1200))
                else:
                    md.append("  结果：未找到（可能 turn 2 中止或尚未返回）\n")
                md.append("\n")
        else:
            md.append("**工具调用：** 无\n")
        # final text
        for text in text_by_step.get(step, []):
            md.append("**文本输出：**\n")
            md.append(code_block(text, max_len=4000))
            md.append("\n")
        md.append("---\n")

    # 2.3 循环/反复记录
    md.append("### 2.3 循环、反复与“变卦”记录\n")
    md.append("""从日志可观察到的主要循环与调整：
1. **数据源选择反复**：最初考虑直接使用 `checkup_12345_2024.csv`，后改用治理后的 `12345_有坐标点.geojson`，因为后者已含“事件/类9/方面”字段，便于分类统计。
2. **输出目录权衡**：在 `DATA/analysis` 与 `DATA/exports` 之间选择，最终按 DATA/README 规则放在 `exports`（运行产物不入库）。
3. **脚本调试循环**：脚本运行出现 `n_其他` 列冲突、边界点漏配、区域统计不准等问题，经历多轮“运行→报错→修复→重跑”。
4. **区域统计口径修正**：最初用网格质心判断是否在西陵伍家/174 社区，后改为按点级归属统计，避免质心偏差。
5. **render_inbox 多次生成**：每次重跑都会生成新的 spec，旧 spec 未清理（运行产物可接受）。
""")
    md.append("\n")

    # 2.4 Turn 2
    md.append("### 2.4 Turn 2（第一次报告请求，已中止）\n")
    if 2 in turns:
        t2 = turns[2]
        md.append(f"- 耗时：{fmt_ms((t2['end'] - t2['start']) if t2['end'] else None)}")
        md.append(f"- Steps：{len(t2['steps'])}，工具调用：{len(t2['tool_calls'])}")
        md.append(f"- 结束原因：{json.dumps(t2.get('reason'), ensure_ascii=False)}")
        md.append("- 该 turn 用户发出报告请求后很快中止，随后重新发起更详细的报告请求（Turn 3）。\n")
    md.append("\n")

    # 2.5 Turn 3
    md.append("### 2.5 Turn 3（当前报告请求，进行中）\n")
    if 3 in turns:
        t3 = turns[3]
        md.append(f"- 开始时间：{t3['start']}，状态：ongoing")
        md.append(f"- 截至生成时刻：Steps {len(t3['steps'])}，工具调用 {len(t3['tool_calls'])}，Thinking 条数 {len(t3['reasonings'])}")
        md.append("- 本报告本身即 Turn 3 的产物，正在按用户要求落盘。\n")
    md.append("\n---\n")

    # 3 意图判断与结果范式
    md.append("## 3. 意图判断与结果范式\n")
    md.append("""### 3.1 用户意图解读
用户最初给出的指令非常简短：“将12345热线数据做800米的方格网空间聚合，并做分析总结。”
- **显式目标**：对 12345 热线数据做 800m 方格网空间聚合，并输出分析总结。
- **隐含目标**：结合项目背景（emotion_map 城市体检），聚合结果应可作为图层/数据资产，分析总结应能支撑规划叙事。
- **未明说但必要的决策**：使用哪份数据、精确坐标口径（ok vs region）、输出位置、是否前端出图。

### 3.2 短任务/长任务判断
判断依据：
1. **数据规模**：CSV 16MB、5.7 万行，有坐标点 1.8 万，属于中等规模数据处理。
2. **空间分析复杂度**：800m 方格聚合涉及投影、空间连接、分类统计，需要脚本而非一次性命令。
3. **项目规范**：需要遵循 DATA/README、已有脚本模式、口径纪律，因此不能简单“跑一下”，要可复现。
4. **交付物类型**：用户要求“分析总结”，说明除了数据还要产出分析文档。

因此判断为**中长任务**，需要分阶段：侦察→探查→方案→编码→调试→总结。

### 3.3 停止条件
我在 Turn 1 判断“可以结束”的依据：
- 聚合 GeoJSON/CSV 已生成，字段完整；
- 分析 md 已写入；
- render_inbox spec 已生成，前端可展示；
- 脚本可复现；
- 核心指标（网格数、覆盖点数、TOP10、分类占比）已核算一致。

### 3.4 执行过程中的计划遵循与调整
- 总体按“侦察→探查→方案→编码→调试→总结”推进，没有偏离大方向。
- 中途因数据字段问题调整了数据源（CSV→GeoJSON）；
- 因项目规则调整了输出目录（analysis→exports）；
- 因边界漏配/列冲突进行了多轮调试，属于局部“变卦”，但最终回到原计划。
""")
    md.append("\n---\n")

    # 附录 A 工具调用总表
    md.append("## 附录 A：工具调用总表\n")
    md.append("| 全局序号 | Turn | Step | 时间 | 工具 | callId | 参数长度 | 结果长度 |")
    md.append("|---|---|---|---|---|---|---|---|")
    global_seq = 0
    for turn in order:
        for tc in turns[turn]["tool_calls"]:
            global_seq += 1
            call_id = tc["callId"]
            result = tool_results.get(call_id)
            rlen = len(result) if result is not None else 0
            arg_len = len(tc.get("arguments", ""))
            md.append(f"| {global_seq} | {turn} | {tc['step']} | {tc['time']} | {tc['name']} | `{call_id}` | {arg_len} | {rlen} |")
    md.append("\n---\n")

    # 4 附件
    md.append("## 4. 附件与数据\n")
    md.append("- `session_parse.json`：本报告机器可读版（含全部 thinking 与工具调用参数，不含 tool result 全文）。")
    md.append("- 原始会话日志：`" + LOG + "`（zstd 压缩，可用 `zstandard` 解压）。")
    md.append("- 任务产物：`12345_800m方格聚合.geojson` / `12345_800m方格聚合_统计.csv` / `12345_800m方格聚合_分析.md` / `summary.json`")
    md.append("\n")

    report = "\n".join(md)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(report)

    # 更新 session_parse.json 附上 tool_results 摘要
    with open(OUT_JSON, "r", encoding="utf-8") as f:
        parsed = json.load(f)
    parsed["tool_results_summary"] = {k: v[:500] for k, v in tool_results.items()}
    parsed["tool_results_length"] = {k: len(v) for k, v in tool_results.items()}
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=1)

    print("Report written:", OUT_MD)
    print("Chars:", len(report))


if __name__ == "__main__":
    main()
