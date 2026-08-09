"""
压缩前快照钩子 (PreCompact Hook)
在 Claude Code 上下文压缩（auto-compact，阈值 85%）前自动执行。
机器采集可恢复锚点 → 写 memories/repo/.wip.md，给压缩后/新会话一个落点。

设计：hook 无语义理解，采 git 状态 + 最近 commit + trace 决策尾 + 未提交文件清单。
  语义化「当前任务叙述」由 Claude 在全局 CLAUDE.md「上下文连贯纪律」下维护（重活前 /snapshot 或保 .wip.md 新鲜）。
永不阻塞压缩：全 try/except、恒 exit 0。
若此 Claude Code 版本不暴露 PreCompact 事件，此 hook 不触发（无害），退化方案见全局 CLAUDE.md。
"""
import os
import subprocess
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WIP_PATH = os.path.join(PROJECT_ROOT, 'memories', 'repo', '.wip.md')


def _run(args):
    try:
        r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8',
                           errors='replace', cwd=PROJECT_ROOT, timeout=10)
        return (r.stdout or '').strip()
    except Exception:
        return '(检查失败)'


def _run_safe_ahead():
    try:
        r = subprocess.run(['git', 'rev-list', '--count', '@{u}..HEAD'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace',
                           cwd=PROJECT_ROOT, timeout=10)
        return (r.stdout or '').strip() or '?'
    except Exception:
        return '?'


def main():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    git_status = _run(['git', 'status', '--short'])
    git_log = _run(['git', 'log', '--oneline', '-5'])
    git_branch = _run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    ahead = _run_safe_ahead()

    # trace 决策尾（最近 8 条 [TRACE]）
    trace_tail = ''
    trace_path = os.path.join(PROJECT_ROOT, '.trace', 'trace.log')
    if os.path.exists(trace_path):
        try:
            with open(trace_path, encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-8:]
            trace_tail = ''.join(lines).strip()
        except Exception:
            trace_tail = '(读取失败)'

    body = [
        '# WIP . 压缩前快照（机器采集）',
        f'> 生成：{ts}（PreCompact hook）| 分支 `{git_branch}` | 本地领先 origin `{ahead}`',
        '',
        '## 当前任务（待 Claude 补语义叙述）',
        '> 压缩后/新会话：先读本节 + 下方 git/trace 锚点恢复，再续作。',
        '',
        '_(本节由 Claude 在重活前手填，或读最近交接卡 `session-handoff.md` 补全)_',
        '',
        '## 未提交文件（git status）',
        '```',
        git_status or '(工作区干净)',
        '```',
        '',
        '## 最近 5 个 commit',
        '```',
        git_log,
        '```',
        '',
        '## trace 决策尾（最近 8 条）',
        '```',
        trace_tail or '(无 trace)',
        '```',
        '',
        '--- 压缩完成后此文件可由 Claude 合并/清除 ---',
    ]
    try:
        os.makedirs(os.path.dirname(WIP_PATH), exist_ok=True)
        with open(WIP_PATH, 'w', encoding='utf-8') as f:
            f.write('\n'.join(body))
        print(f"[HOOK] PreCompact — WIP 快照已写 memories/repo/.wip.md（{ts}）")
    except Exception as e:
        print(f"[HOOK] PreCompact — 写 .wip.md 失败：{e}")


if __name__ == '__main__':
    main()
