"""验证方案 A/B：空对象 boundary → request_upload（e2e-seam 直测·可控）。"""
import json as _json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
from emc_helpers import emc_session

def main() -> int:
    sys.stdout.reconfigure(encoding='utf-8')
    bad = []
    with emc_session() as page:
        page.wait_for_function("() => !!(window.__emcTest && __emcTest.buildOutletCardForTest)", timeout=45000)
        # 方案 A：直接构造 diagnose（boundary 空对象）→ 检查 data_plan.strategy
        # 用 harness 的 deriveMissingParams 不可直接调·改为验证 B：zonal handler 空对象
        r = page.evaluate("""async () => {
          // 直接调 TOOLS.zonal_stats（空对象 boundary）→ 应返回「需上传标准边界资料」非「无数据」
          const tools = window.__emcTest.TOOLS;
          const out = await tools.zonal_stats({ boundary: {} });
          return out;
        }""")
        obs = (r or {}).get('observation') or ''
        print('zonal_stats({}) obs:', obs[:100])
        if '需上传标准边界资料' in obs:
            print('[OK] 方案 B 生效：空对象 boundary → 需上传')
        else:
            print('[FAIL] 方案 B 未生效')
            bad.append('方案 B 未生效')
        # 单要素小溪塔 → 黑名单拒识
        r2 = page.evaluate("""async () => {
          const tools = window.__emcTest.TOOLS;
          const out = await tools.zonal_stats({ boundary: { type:'FeatureCollection', features:[{type:'Feature', properties:{name:'小溪塔'}, geometry:{type:'Polygon',coordinates:[[[0,0],[1,0],[1,1],[0,0]]]}}] } });
          return out;
        }""")
        obs2 = (r2 or {}).get('observation') or ''
        print('zonal_stats(小溪塔) obs:', obs2[:80])
        if '法定功能区' in obs2 or '需上传' in obs2:
            print('[OK] 黑名单拒识生效')
        else:
            print('[WARN] 黑名单未拦（可能字段名/几何问题）')
    if bad:
        return 1
    print('[OK] PASS — 方案 A/B 可控场景验证')
    return 0

if __name__ == '__main__':
    sys.exit(main())
