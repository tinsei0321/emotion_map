"""用例 10（G1 配套）· A1 谓词真值。

cpd-state.js 谓词（hasImport/hasRange/hasAnalysis/hasVisibleEmotionLayer）经 e2e-seam 暴露为
window.__cpdPredicates，page.evaluate 直读真值——把死信号/谓词盲区（M2 无情绪层撒谎
"点击深绿/深橙"）从评审发现变测试发现（GUIDANCE §1.1）。

核心硬断言（M2 回归·CB-CPD-03）：注入「无情绪字段」点层 → hasVisibleEmotionLayer=false。
无需 LLM（纯注入 + 谓词读），与用例 5 同级稳定。

运行：py tests/browser/test_cpd_predicates.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))

from emc_helpers import emc_session, inject_points, read_predicate, wait_predicate

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')


def _load(name):
    with open(os.path.join(FIX, name), encoding='utf-8') as f:
        return json.load(f)


def main() -> int:
    with emc_session() as page:
        # 等 e2e-seam 暴露谓词（dynamic-import，?e2e=1）
        page.wait_for_function("() => !!window.__cpdPredicates", timeout=30000)

        # 1. 空态：无导入、无情绪层
        assert read_predicate(page, "() => window.__cpdPredicates.hasImport()") is False, '空态 hasImport 应 false'
        assert read_predicate(page, "() => window.__cpdPredicates.hasVisibleEmotionLayer()") is False, '空态 visEmotion 应 false'

        # 2. plain_poi（无 polarity/score 字段）：导入点层但非情绪 → hasImport=true ∧ visEmotion=false（M2 硬断言）
        inject_points(page, _load('plain_poi.geojson'))
        assert wait_predicate(page, "() => window.__cpdPredicates.hasImport()", True), \
            'plain_poi 为导入点层，hasImport 应 true'
        vis = wait_predicate(page, "() => window.__cpdPredicates.hasVisibleEmotionLayer()", False)
        assert vis is False, \
            f'M2 回归失败：无情绪字段点层 hasVisibleEmotionLayer 应 false（演示链第一环断点），实测 {vis!r}'

        # 3. 情绪层（compare_points，含 polarity/score）：visEmotion=true
        inject_points(page, _load('compare_points.geojson'))
        assert wait_predicate(page, "() => window.__cpdPredicates.hasVisibleEmotionLayer()", True), \
            '情绪层注入后 visEmotion 应 true'

        # hasAnalysis（grid/zonal/heatmap 工具层 ∨ AI 组）需 dock 产图或 LLM 对话→见用例 6/11，本例不测（免 LLM，保稳定）。
        print('[OK] PASS — hasImport/visEmotion 真值：空→false×2 / plain_poi→hasImport true + visEmotion false(M2) / 情绪层→visEmotion true')
        return 0


if __name__ == '__main__':
    sys.exit(main())
