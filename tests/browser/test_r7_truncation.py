"""R7 结论截断边界测试（CB-16 用户实测 + 两组检查·claude组 建议补防回归）。

经 e2e-seam 暴露的 window.__emcTest.applyQualityDefense 直测真实 JS 逻辑（非 Python 复刻）：
- 场景 1：多要素结论（~1100 字）→ 不触发 R7 完整通过（用户实测场景·阈值 1500 合理）
- 场景 2：>1500 字失控长文 → 触发 R7·截断不残留「**N.」空标题（结构回切 + 去 '.' 切句符 + 悬空编号行剥除）
- 场景 3：{{show:}} 不被 R7 切出残句（R2 移 R7 后补全）

注：R2 补按钮依赖 getArtifacts() 产物态（realLayers）——纯调 def 未注入产物时不触发 R2（模块态限制·如实标注）。
无需 LLM（纯调防线函数），与 test_cpd_predicates 同级稳定。

运行：py tests/browser/test_r7_truncation.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session

# 多要素结论项（仿 FINAL_TEMPLATE 编号列表·含「**4. 标题。**」形态）
_ITEMS = ['问题类型：停车难与配套不足', '需求强度：极性指数偏低', '需求位置：大南门滨江片区', '需求类型：设施与服务']


def _def_call(page, text):
    """调 applyQualityDefense（真实 JS 逻辑·obsOk=true·无产物态）。"""
    return page.evaluate("""(text) => {
      const def = window.__emcTest.applyQualityDefense;
      return def(text, { toolHistoryText: '动作: zonal_stats(...)\\n', obsOk: true });
    }""", text)


def main() -> int:
    with emc_session() as page:
        page.wait_for_function("() => !!(window.__emcTest && window.__emcTest.applyQualityDefense)", timeout=45000)

        # ── 场景 1：多要素结论（~1100 字·用户实测）→ 不触发 R7 完整通过 ──
        long1 = '\n'.join(f'**{i}. {_ITEMS[i % 4]}。** 这是第{i}段的详细描述内容，涵盖停车难、业态同质化、施工扰民等多要素分析。'
                          for i in range(1, 20))
        r1 = _def_call(page, long1)
        assert not any(f['rule'] == 'R7' for f in r1['fixes']), \
            f'场景1（{len(long1)} 字多要素）不应触发 R7（fixes={r1["fixes"]}）'
        assert r1['final'] == long1, '场景1 应原样完整通过（不截断不追加）'

        # ── 场景 2：>1500 字失控长文 → 触发 R7·无空标题残留 ──
        long2 = '\n'.join(f'**{i}. 第{i}项分析内容。** 这是第{i}段的详细描述，包含停车难、业态同质化、施工扰民、配套不足等多个要素的完整分析。'
                          for i in range(1, 40))
        r2 = _def_call(page, long2)
        assert any(f['rule'] == 'R7' for f in r2['fixes']), f'场景2（{len(long2)} 字）应触发 R7'
        assert '…（结论已截断' in r2['final'] or '…（结论较长' in r2['final'], '场景2 应含截断标注'
        # 空标题残留检查：标注前不应是「**N.」或「\nN.」形态（claude组 场景4 bug 的回归防线）
        _head = r2['final'].split('…（')[0].rstrip('\n ')
        assert not _head.endswith(('**1.', '**2.', '**3.', '**4.', '**5.', '**6.', '**7.', '**8.', '**9.', '1.', '2.', '3.', '4.', '5.')), \
            f'场景2 截断残留空标题（head 尾={_head[-30:]!r}）'

        # ── 场景 3：{{show:}} 不被切出残句（draft 自带按钮 + 长文）──
        long3 = '\n'.join(f'**{i}. 第{i}项分析内容。** 这是第{i}段的详细描述，涵盖停车难、业态同质化等多要素。' for i in range(1, 20)) \
            + '\n{{show:大南门聚合}}\n' + '\n'.join(f'**{i}. 补充第{i}项。** 这是补充内容，进一步说明需求强度、需求位置与优先级的完整分析。' for i in range(1, 20))
        r3 = _def_call(page, long3)
        assert '{{show:' in r3['final'], f'场景3 按钮应存在（被 R7 切则 R2 会补·但纯调 def 无产物态故 R2 不触发——需按钮在 draft 前部保留或 R2 补）'
        # 关键：按钮应完整（{{show:xxx}} 成对·无残句）
        assert r3['final'].count('{{show:') == 1 and '}}' in r3['final'], \
            f'场景3 {{show:}} 应完整（final={r3["final"][-80:]!r}）'

        print('[OK] PASS — R7 边界：多要素完整通过 / 失控长文截断无空标题 / {{show:}} 完整')
        return 0


if __name__ == '__main__':
    sys.exit(main())
