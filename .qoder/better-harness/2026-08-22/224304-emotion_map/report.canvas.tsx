import React from "react";

/**
 * better-harness 报告画布 — emotion_map
 * 数据源：同目录 canvas.json / findings.json（本组件内嵌镜像，保证独立可渲染）
 */

type Severity = "high" | "medium" | "low";

interface Strength {
  id: string;
  title: string;
  detail: string;
}

interface Finding {
  id: string;
  severity: Severity;
  title: string;
  evidence: string;
  fix: string;
}

const SEVERITY_LABEL: Record<Severity, string> = {
  high: "高危",
  medium: "中危",
  low: "低危",
};

const SEVERITY_COLOR: Record<Severity, string> = {
  high: "#d64545",
  medium: "#d9822b",
  low: "#5a8a6a",
};

const STRENGTHS: Strength[] = [
  { id: "S1", title: "三层记忆 + 渐进式披露", detail: "明规则全量注入 / 隐规则按需 / 专项文档场景触发，上下文成本显式分层。" },
  { id: "S2", title: "可观测性下沉 runtime", detail: "tracker.py 决策追踪，bug 定位 O(n)→O(1)；harness 纪律与产品代码双向锚定。" },
  { id: "S3", title: "失败飞轮三件套", detail: "规则蒸馏 / bug 台账 / 轮次流水，互补不重复，有维护协议。" },
  { id: "S4", title: "Hook 边界纪律", detail: "毫秒级动作才进 hook；重启/pytest 显式留给人触发。" },
  { id: "S5", title: "MCP 错层 + 降级链", detail: "智谱优先，项目级只放专属 server，全局栈不重复。" },
  { id: "S6", title: "Skills 主动治理", detail: "464→~50 精简 + 黑名单 + 外部 skill hash 锁定。" },
  { id: "S7", title: "双机同步完成定义", detail: "commit+push 才算交付；仓外资产必须带配方；判据=另一机可无脑照做。" },
];

const FINDINGS: Finding[] = [
  { id: "F1", severity: "high", title: "记忆索引指向不存在的用户路径", evidence: "MEMORY.md 指 C:\\Users\\admin\\...，本机用户为 Hi，第二层记忆静默断裂。", fix: "改占位路径并入到岗体检。" },
  { id: "F2", severity: "high", title: "Codex hooks 硬编码绝对路径", evidence: ".codex/hooks.json 硬编码 d:\\Github\\emotion_map\\...，违反自身全局规则五。", fix: "相对路径或登记差异注记。" },
  { id: "F3", severity: "medium", title: "指令层双写漂移", evidence: "铁律 11 条双写；Agent 数量口径 8 vs 9；版本节奏 v2.0 vs v2.5。", fix: "收敛单一权威源 + 指针。" },
  { id: "F4", severity: "medium", title: "Skills 索引与实体脱节", evidence: "索引列 ifly-*/daymade-*/agent-patterns-* 等，实际目录多数不存在。", fix: "按实际目录/lock 文件刷新索引。" },
  { id: "F5", severity: "medium", title: "pre-commit 门禁无启用校验", evidence: "hooksPath 依赖每机手动一次性配置，无体检核验。", fix: "并入 SessionStart 自检。" },
  { id: "F6", severity: "low", title: "Hook 解释器混用", evidence: "settings.json 中 python 与 py 混用，与 CLAUDE.md 口径不一。", fix: "统一 py。" },
  { id: "F7", severity: "low", title: "角色卡片仍诱导运行时误读", evidence: "『可调用』列与自动路由图和『非执行单元』声明张力未消（CB-01 前车之鉴）。", fix: "列更名/移附录 + 图加标注。" },
  { id: "F8", severity: "low", title: "蒸馏触发器无机制兜底", evidence: "『修≥2轮→当轮蒸馏』靠自觉，无 checklist/CI 校验。", fix: "加轻量自检项。" },
];

const METRICS: Array<[string, string]> = [
  ["Harness 宿主", "4（Claude Code / Codex / Qoder / dsh）"],
  ["Hook 类型", "5 × 2 运行时（.claude / .codex 各一套）"],
  ["已装 Skills", "44（外部 2 个 hash 锁定）"],
  ["Debug 规则", "R1–R19（三件套飞轮）"],
  ["决策追踪模块", "13 已埋点 + 9 待埋点"],
  ["指令文档", "CLAUDE.md 354 行 + AGENTS.md v2.5"],
];

const styles: Record<string, React.CSSProperties> = {
  page: { fontFamily: "'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif", background: "#0f1115", color: "#e6e6e6", padding: 32, minHeight: "100vh" },
  header: { borderBottom: "1px solid #2a2e37", paddingBottom: 16, marginBottom: 24 },
  h1: { fontSize: 24, margin: 0, fontWeight: 700 },
  meta: { marginTop: 8, color: "#9aa0ab", fontSize: 13 },
  h2: { fontSize: 17, margin: "28px 0 12px", fontWeight: 600, letterSpacing: 0.5 },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 12 },
  card: { background: "#171a20", border: "1px solid #2a2e37", borderRadius: 10, padding: 14 },
  cardTitle: { fontSize: 14, fontWeight: 600, marginBottom: 6 },
  cardDetail: { fontSize: 12.5, color: "#aeb4bf", lineHeight: 1.6 },
  metricRow: { display: "flex", gap: 12, flexWrap: "wrap" },
  metric: { background: "#171a20", border: "1px solid #2a2e37", borderRadius: 8, padding: "8px 14px", fontSize: 12.5 },
  metricLabel: { color: "#9aa0ab", marginRight: 8 },
  finding: { background: "#171a20", border: "1px solid #2a2e37", borderLeftWidth: 3, borderRadius: 8, padding: 14, marginBottom: 10 },
  findingHead: { display: "flex", alignItems: "center", gap: 10, marginBottom: 6 },
  findingTitle: { fontSize: 14, fontWeight: 600 },
  badge: { fontSize: 11, padding: "2px 8px", borderRadius: 999, color: "#fff", fontWeight: 600 },
  findingBody: { fontSize: 12.5, color: "#aeb4bf", lineHeight: 1.65 },
  fixLabel: { color: "#7fb88a", fontWeight: 600 },
  quote: { background: "#171a20", border: "1px solid #2a2e37", borderRadius: 10, padding: 18, fontSize: 14, lineHeight: 1.8, color: "#d6dbe4" },
  list: { margin: 0, paddingLeft: 20, fontSize: 13.5, lineHeight: 1.9, color: "#c4cad4" },
};

export default function ReportCanvas() {
  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={styles.h1}>Harness 实践分析 — 情绪地图 (emotion_map)</h1>
        <div style={styles.meta}>
          2026-08-22 22:43 · 分支 main · 4 宿主 / 5 hooks / 44 skills · 2 高危 + 3 中危 + 3 低危
        </div>
      </header>

      <section>
        <h2 style={styles.h2}>总览</h2>
        <ul style={styles.list}>
          <li>4 宿主并存：Claude Code (.claude) / Codex (.codex) / Qoder (.agents/skills) / dsh (.dsh-meow)，以 AGENTS.md 为跨工具统一行为规范。</li>
          <li>成熟度判断：治理密度罕见地高——问题集中在<b>配置漂移与指针断裂</b>，而非实践缺失。</li>
          <li>保留问题 8 项，其中 2 项高危均为「项目自身规则未被自身配置遵守」的自反性缺口。</li>
        </ul>
      </section>

      <section>
        <h2 style={styles.h2}>关键指标</h2>
        <div style={styles.metricRow}>
          {METRICS.map(([label, value]) => (
            <div key={label} style={styles.metric}>
              <span style={styles.metricLabel}>{label}</span>
              <span style={{ color: "#e6e6e6" }}>{value}</span>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 style={styles.h2}>亮点 — 可迁移的 Harness 实践</h2>
        <div style={styles.grid}>
          {STRENGTHS.map((s) => (
            <div key={s.id} style={styles.card}>
              <div style={styles.cardTitle}>
                <span style={{ color: "#7fb88a", marginRight: 8 }}>{s.id}</span>
                {s.title}
              </div>
              <div style={styles.cardDetail}>{s.detail}</div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 style={styles.h2}>保留问题</h2>
        {FINDINGS.map((f) => (
          <div
            key={f.id}
            style={{ ...styles.finding, borderLeftColor: SEVERITY_COLOR[f.severity] }}
          >
            <div style={styles.findingHead}>
              <span style={{ color: SEVERITY_COLOR[f.severity], fontWeight: 700 }}>{f.id}</span>
              <span style={styles.findingTitle}>{f.title}</span>
              <span
                style={{
                  ...styles.badge,
                  background: SEVERITY_COLOR[f.severity],
                }}
              >
                {SEVERITY_LABEL[f.severity]}
              </span>
            </div>
            <div style={styles.findingBody}>
              证据：{f.evidence}
              <br />
              <span style={styles.fixLabel}>修复建议：</span>
              {f.fix}
            </div>
          </div>
        ))}
      </section>

      <section>
        <h2 style={styles.h2}>一句话洞察</h2>
        <blockquote style={styles.quote}>
          该项目最强的 Harness 创新不是配置文件，而是把「规则可验证」做到了三处闭环：runtime（tracker
          ID）、流程（CB 回应销号）、纪律（双机完成定义）——但它自己的文档指针和宿主配置还没被同样的闭环覆盖，
          修复方向是把 harness 自身也纳入其已经建立的自检机制。
        </blockquote>
      </section>
    </div>
  );
}
