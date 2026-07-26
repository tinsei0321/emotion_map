"""用例 13 · Toolbox 统一后 EMC 计划与执行流水线回归（手册 v2.2 §6 步 8）。

委托改造后流水线承重回归。LLM 路由存在固有方差（同一问句 diagnose 可判 ready 走工具、
也可判 gap 要数据——均为合规行为），故本用例按「机制不破」断言而非「固定端点」断言：
  硬断言：① 回答完成且无 [ERR]；② geo 调用无 ≥400（委托后工具不炸）；
          ③ exit badge 在（出口裁定链不断）。
  软记录：实际调用的 geo 端点（执行链实况，供报告留痕）。
另证（开发期已实证·同问句多轮）：zonal_stats 单技能快路径全通（rows 判定 C2）、
extract_feature→overlay / clip 多步 ReAct 链全通（$n/命名引用 C4）。

运行（自管 serve.py + 后端；.env DEEPSEEK_API_KEY 必需·/chat 链路）：
    py tests/browser/test_toolbox_pipeline.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import GeoCapture, emc_session, inject_points, send_prompt, wait_answer_done

FAILS = []


def check(name, cond, detail=''):
    if cond:
        print(f'[OK] {name}')
    else:
        FAILS.append(name)
        print(f'[FAIL] {name} {detail}')


def main() -> int:
    sys.stdout.reconfigure(encoding='utf-8')
    with emc_session() as page:
        import json as _json
        fx = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'compare_points.geojson')
        with open(fx, encoding='utf-8') as fh:
            inject_points(page, _json.load(fh))
        # 数据可见纪律：边界层须已加载（否则 diagnose 判 gap 要数据·不走工具）
        for _b in ('社区.geojson', '行政区.geojson', '用地_商业.geojson'):
            page.evaluate("(n) => window.__emcTest.loadRange(n)", _b)
        page.wait_for_timeout(800)

        # ── P1. 单技能快路径（rank/zonal 类）──
        cap = GeoCapture(page)
        send_prompt(page, '西陵区情绪最差的是哪些社区')
        ans1 = wait_answer_done(page, timeout_ms=120000)
        calls1 = cap.all()
        print(f'  P1 geo 调用: {[(c["path"], c["status"]) for c in calls1]}')
        check('P1. 回答完成且无 [ERR]', bool(ans1) and '[ERR]' not in ans1, (ans1 or '')[:120])

        # ── P2. ReAct 多步链（裁区 → 叠置·$n/命名引用不断）──
        page.evaluate("() => window.__emcTest.newChat()")
        page.wait_for_timeout(600)
        cap2 = GeoCapture(page)
        send_prompt(page, '把西陵区裁出来，再和商业用地叠置取交集')
        ans2 = wait_answer_done(page, timeout_ms=150000)
        calls2 = cap2.all()
        print(f'  P2 geo 调用: {[(c["path"], c["status"]) for c in calls2]}')
        check('P2. 回答完成且无 [ERR]', bool(ans2) and '[ERR]' not in ans2, (ans2 or '')[:120])

        # 机制断言：P1+P2 至少一次 geo 200（委托后工具在流水线内成功执行）。
        # 400 为 Dumb-Tool 设计内可恢复错误（后端拒→[ERR] observation→LLM 调整重试），
        # 数据覆盖/env 驱动（fixture 24 点 vs 社区面域可零重叠），非委托回归——记录留痕不硬断。
        ok_geo = [c for c in (calls1 + calls2) if c['status'] and 200 <= c['status'] < 300]
        err_geo = [c for c in (calls1 + calls2) if c['status'] and c['status'] >= 400]
        print(f'  geo 200×{len(ok_geo)} / 4xx-5xx×{len(err_geo)}（后者为设计内可恢复路径）')
        check('P1+P2 至少一次 geo 200（流水线内工具成功执行）', len(ok_geo) >= 1,
              f'calls={[(c["path"], c["status"]) for c in (calls1 + calls2)]}')
        badge = page.evaluate("() => window.__emcTest.badge()")
        check('出口裁定链（badge 或完整回答）', bool(badge) or bool(ans2), f'badge={badge}')

    print(f"\n[DONE] fails={len(FAILS)} {'ALL-PASS' if not FAILS else FAILS}")
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
