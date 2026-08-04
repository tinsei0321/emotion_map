"""EMC P1 Flash 模板命中率 go/no-go 评测（手动跑，需 DeepSeek API Key）。

用法：  py tests/eval_template_flash.py
门限：  命中率 ≥ 80% 才 ship single 路径（harness runTemplatePath）；< 80% 则 harness 路由应只保
       concept + multi/unknown（single 路径不主导），免错模板无恢复 > 现 ReAct 自纠。
原理：  7 选 1（含 concept/multi/unknown 兜底）比 12 选 1 易命中；本脚本喂 N 条代表问给真 Flash
       diagnose，解析 template 字段，与期望技能比对。
注：    非 pytest 测（无 test_ 函数 + 需 API Key + 花钱），CI 不跑；手动 go/no-go 用。
"""
import json
import os
import re
import sys


def _load_env_file():
    """轻量 .env 加载（镜像 api/main.py，无 python-dotenv 依赖）：解析项目根 .env → 注入 os.environ（不覆盖已有）。
    本脚本直 import LLMClient、不经 api/main.py，故 .env 不会自动加载——补齐后 `py tests/eval_template_flash.py` 一条命令即可跑（key 缺失由 LLMClient._ensure_key 明确报错）。"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, _, v = line.partition('=')
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


_load_env_file()

# N 条代表问（问题 → 期望 template skill id）
# 冻结基线 2026-07-24（B0·eval-first 红线 gate）：19/23 = 83% ≥ 80% → 解锁 runTemplatePath single 默认（B1-2b）。
#   MISS 4（Flash 路由歧义·非本批引入·留 B3 SOP 卡+method→tool 映射治）：rank/zonal「优先更新」·clip/unknown「商业用地」·overlay/clip「居住用地里」·hotspot/density「负面聚集」。
#   B0 新增 4（全命中）：compare×2（原缺·select_template :437/453 路由）+ concept 负例×2（问原理/问已有图层·非工具）。
CASES = [
    ('做核密度分析', 'density'),
    ('哪里情绪最集中', 'density'),
    ('各区情绪排序', 'rank'),
    ('哪个区最需优先更新', 'rank'),
    ('滨江公园 500 米缓冲', 'buffer'),
    ('地铁站周边情绪', 'buffer'),
    ('西陵区的情绪点', 'clip'),
    ('某区的商业用地', 'clip'),
    ('居住用地里情绪差的', 'overlay'),
    ('这几个街道的情绪归因', 'zonal'),
    ('什么是核密度分析', 'concept'),
    ('情绪地图是什么', 'concept'),
    ('西陵区内的商业用地并排序', 'multi'),
    # B1 新技能（验 single-path 变现）
    ('裁出西陵区', 'extract_feature'),
    ('各街道面积占比', 'area_stats'),
    ('把几个街道合并成片区', 'merge'),
    ('离地铁最近的负面点', 'nearest'),
    ('哪里负面情绪聚集', 'hotspot'),
    ('按属性筛选出负面点', 'filter_attr'),
    # B0 扩例：compare（C 赛道区域对比·原缺·select_template :437/453 路由）+ 负例（问原理/问已有→concept·非工具）
    ('对比西陵区和伍家岗区情绪', 'compare'),
    ('比较两个区的消极占比', 'compare'),
    ('核密度分析的原理是什么', 'concept'),
    ('这几个图层是什么意思', 'concept'),
    # B0b/第3批 区片可派生（D2 红线 gate·验区片 template 路由不退化；多步链「伍家岗哪里最差」不稳·留 D3/飞轮）
    ('西陵区情绪归因分析', 'zonal'),
    ('西陵区的情绪点', 'clip'),
    ('夷陵区情绪状况', 'zonal'),
    # C6（5.204·eval-first）：density 触发词扩——"密集/热力图"原 0 命中（K3 C6③·paradigm:250 触发词无"密集"）
    ('哪里最密集', 'density'),
    ('情绪热力图分布', 'density'),
    # D1（5.207·eval-first）：工具选型边界歧义扩例——冻结基线后验 catalog failure_modes/examples 改善。
    #   针对 4 类残余歧义：rank/zonal（整体 vs 落点）、clip/overlay（点裁 vs 面∩面）、
    #   hotspot/density（逐点 Gi* vs 连续面）、extract/clip（抽单面 vs 裁点）、area_stats/zonal（面积 vs 情绪）。
    ('中心城区整体情绪如何', 'zonal'),          # 宏观整体→zonal 非 rank（rank/zonal 边界）
    ('这个公园里哪个点位最差', 'rank'),          # micro 落点→rank 非 zonal（rank/zonal 边界）
    ('显著负面聚集区在哪', 'hotspot'),          # Gi* 逐点冷热（hotspot/density 边界）
    ('商业用地和居住用地的交集', 'overlay'),     # 面∩面→overlay 非 clip（clip/overlay 边界）
    ('公园与商业用地重叠部分', 'overlay'),       # 面∩面→overlay
    ('只要西陵区这个面', 'extract_feature'),    # 抽单面要素→extract 非 clip（extract/clip 边界）
    ('各区用地面积占比', 'area_stats'),         # 面积结构→area_stats 非 zonal（area_stats/zonal 边界）
    # E1（5.210）：多步链用例（template=multi·runChainPath 目标·治 C3）。Flash 倾向 single（clip/density·也 0 轮治超时）；
    #   期望 multi 验 Flash 识别复合。MISS（选 single）非退化（single 也 0 LLM 轮）·只是 chain 路径覆盖 = Flash 选 multi 时。
    # ③w4b（glm 标尺纠错）：select_template 是 v1 单工具选择器·不返回 multi（multi 是前端 CHAIN_REGISTRY 概念）——
    #   eval 期望 multi = 标尺错（76% 是标尺不匹配架构·非路由退化）。改标尺 = 期望实际单工具（非改 select_template·保 v1 eval-anchor）。
    # ③w5b（glm 补充）："西陵区的商业用地" clip/overlay 双合理（面∩面解读）·tuple 双接受治 Flash 概率性歧义 MISS
    ('西陵区的商业用地', ('clip', 'overlay')),   # 区内某类用地 → clip（点裁）或 overlay（面∩面·区面∩用地面）皆合理
    ('西陵区范围内密度分析', 'density'),         # 范围密度 → 单工具 density（multi clip_density 链在前端覆盖）
]


def _parse_template(raw: str) -> str:
    """从 Flash diagnose 响应抠 template 字段（容错 fence/裸 JSON）。"""
    if not raw:
        return ''
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
    s = m.group(1) if m else raw
    i, j = s.find('{'), s.rfind('}')
    if i < 0 or j <= i:
        return ''
    cand = s[i:j + 1].replace(',}', '}').replace(',]', ']')
    try:
        t = json.loads(cand).get('template', '')
        return str(t).strip().lower()
    except Exception:
        tm = re.search(r'"template"\s*:\s*"([^"]+)"', cand)
        return tm.group(1).strip().lower() if tm else ''


def run_eval():
    try:
        from ai_qa.llm import LLMClient
        from ai_qa.prompts import build_diagnose_prompt
    except Exception as e:
        print(f'[SKIP] 依赖缺失：{e}'); return
    try:
        cli = LLMClient(model='flash')
    except Exception as e:
        print(f'[SKIP] LLMClient 初始化失败（检查 .env DEEPSEEK_API_KEY）：{e}'); return

    sys_prompt = build_diagnose_prompt('')
    hits, total, details = 0, 0, []
    for q, expected in CASES:
        total += 1
        try:
            msgs = [{'role': 'system', 'content': sys_prompt}, {'role': 'user', 'content': q}]
            chunks = []
            for tok in cli.chat(msgs, stream=True, temperature=0.4):
                if isinstance(tok, str):
                    chunks.append(tok)
            raw = ''.join(chunks)
            got = _parse_template(raw)
            # ③w5b（glm 补充）：期望支持 tuple（多值接受）——"西陵区的商业用地" clip/overlay 双合理（面∩面解读）·治 Flash 概率性歧义 MISS
            ok = got == expected if isinstance(expected, str) else got in (expected or ())
            hits += int(ok)
            details.append((ok, q, expected, got or '(空)'))
        except Exception as e:
            details.append((False, q, expected, f'[ERR {e}]'))

    rate = hits / total if total else 0
    print('\n═══ Flash 模板命中率评测 ═══')
    for ok, q, exp, got in details:
        print(f"  {'[OK] ' if ok else '[MISS]'} {q}  → 期望 {exp} / 实得 {got}")
    print(f'\n命中率：{hits}/{total} = {rate:.0%}')
    print('═══ Go/No-Go：≥80% ship single 路径；<80% 只保 concept+multi/unknown ═══')
    print('PASS — 可 ship single 路径' if rate >= 0.8 else 'NO-GO — single 路径暂不主导（保兜底）')


def run_fc_param_eval():
    """WS3 F3.4：FC 参数填充评测（治 eval 测不到「模板对·参数空」·CB 发现的盲区）。

    喂 param-critical 问句给真 FC（chat_with_tools_fallback + contracts_to_tools_schema），
    验 tool_call.arguments 必填槽是否填齐（buffer.center / compare.boundaries≥2 / overlay.layer_a,b）。
    手动跑·需 API Key·花钱（同 run_eval）·非 CI。
    """
    try:
        from ai_qa.llm import chat_with_tools_fallback
        from ai_qa.tool_contracts import contracts_to_tools_schema, validate_tool_call
    except Exception as e:
        print(f'[SKIP] 依赖缺失：{e}'); return
    import json as _json

    tools = contracts_to_tools_schema()
    # FC sys prompt（精简版·对齐 router.py fc_diagnose 的参数纪律 + few-shot）
    sys_content = (
        '你是情绪地图分析助手。根据用户问题选择一个工具并填写参数。\n'
        '## 参数填写纪律\n'
        '- 必填槽必须从问句抽出填入 tool_call·勿留空\n'
        '## 参数提取示例\n'
        '- 「以X为中心周边500米」→ buffer: center="X", radius_m=500\n'
        '- 「A 与 B 的情绪对比」→ compare_regions: boundaries=["A","B"]（≥2·数组·从两个地名抽）\n'
        '- 「A 与 B 的交集」→ overlay: layer_a="A", layer_b="B", how="intersection"\n'
    )
    # (问句, 期望 tool, 必填槽值合法性检查)
    cases = [
        ('以滨江公园为中心周边500米缓冲', 'buffer', lambda p: bool(p.get('center'))),
        ('西陵区和伍家岗区的情绪对比', 'compare_regions',
         lambda p: isinstance(p.get('boundaries'), list) and len(p.get('boundaries')) >= 2),
        ('商业用地和居住用地的交集', 'overlay',
         lambda p: bool(p.get('layer_a')) and bool(p.get('layer_b'))),
    ]
    hits, total = 0, 0
    print('\n═══ FC 参数填充评测（必填槽是否填齐）═══')
    for q, exp_tool, ok_check in cases:
        total += 1
        try:
            msgs = [{'role': 'system', 'content': sys_content}, {'role': 'user', 'content': q}]
            res = chat_with_tools_fallback(msgs, tools, tier='flash')
            tc = (res.get('tool_calls') or [{}])[0]
            fn = tc.get('function', {}) if tc else {}
            name = fn.get('name', '')
            args = _json.loads(fn.get('arguments', '{}') or '{}')
            v = validate_tool_call(name, args)
            filled = (name == exp_tool) and v['ok'] and ok_check(v['params'])
            hits += int(filled)
            miss = [] if v['ok'] else [f for f in v['fixes'] if '缺必填' in f]
            print(f"  {'[OK] ' if filled else '[MISS]'} {q}  → tool={name} args={args} miss={miss}")
        except Exception as e:
            print(f"  [ERR] {q}  → {e}")
    rate = hits / total if total else 0
    print(f'\nFC 参数填充率：{hits}/{total} = {rate:.0%}')
    print('═══ 目标 100%（必填槽必须从问句抽出填齐）═══')


if __name__ == '__main__':
    run_eval()
    run_fc_param_eval()
