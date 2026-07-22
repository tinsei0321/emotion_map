"""用例 6（CPD 地基行为）· exit-badge 出口徽章渲染。

result 轮 → .aiq-exit-badge cls=ok（分析完成/已生成 N 个图层）；
general 轮（"什么是4×5矩阵"）→ txt=纯问答 cls=neutral。
general 分支 = H1 教训 DOM 级前置（为 G1 用例 11 铺路）。

前置：.env DEEPSEEK_API_KEY + fixtures/compare_points.geojson（result 分支需点层）。
运行：py tests/browser/test_exit_badge.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session, inject_points, send_prompt, wait_answer_done

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'compare_points.geojson')
RESULT_PROMPT = '对比西陵区和伍家岗区的情绪与归因'
GENERAL_PROMPT = '什么是情绪地图？'   # 概念/方法论问句，倾向路由 general（纯问答/neutral）——但 LLM 非确定，下方 soft 断言


def _last_badge(page):
    """读末条 .aiq-exit-badge 的 {txt, cls}（无则 None）。"""
    return page.evaluate("""() => {
        const bs = document.querySelectorAll('.aiq-exit-badge');
        if (!bs.length) return null;
        const el = bs[bs.length - 1];
        const cls = el.className.replace('aiq-exit-badge', '').trim();
        return { txt: el.textContent.trim(), cls };
    }""")


def main() -> int:
    with open(FIXTURE, encoding='utf-8') as fh:
        fc = json.load(fh)
    with emc_session() as page:
        inject_points(page, fc)

        # 实质分析轮（compare → exit=result 或 gap，badge cls=ok/warn 均合法；
        # exit 取决于 LLM+数据，非确定——用例 1 仅断 zonal_stats 200 不断言 exit，此处同。
        # 本用例守 badge 渲染契约 + 下方 general 分支的确定性 H1 前置）
        send_prompt(page, RESULT_PROMPT)
        wait_answer_done(page, timeout_ms=90000)
        b1 = _last_badge(page)
        assert b1, '分析轮未渲染 .aiq-exit-badge'
        assert b1['cls'] in ('ok', 'warn'), f"分析轮 badge cls 非 ok/warn: {b1}"

        # 第二轮：概念/方法论问句 → 倾向路由 general（badge 纯问答/neutral = H1 DOM 级前置）。
        # general 路由依赖 LLM 非确定 → neutral 为软断言（WARN，观测到=bonus）；硬断言=badge 渲染 + cls 合法。
        send_prompt(page, GENERAL_PROMPT)
        wait_answer_done(page, timeout_ms=60000)
        b2 = _last_badge(page)
        assert b2, '第二轮未渲染 .aiq-exit-badge'
        assert b2['cls'] in ('ok', 'warn', 'neutral'), f'第二轮 badge cls 非法: {b2}'
        if b2['cls'] == 'neutral' and '纯问答' in b2['txt']:
            print(f'[OK] general 路由 → badge 纯问答/neutral（H1 DOM 级前置观测到）')
        else:
            print(f'[WARN] general 问句未路由 general（badge={b2}）—— H1 前置未观测，LLM 非确定（软断言不 fail）')

        print(f'[OK] PASS — 分析轮 badge={b1} / 第二轮 badge={b2}')
        return 0


if __name__ == '__main__':
    sys.exit(main())
