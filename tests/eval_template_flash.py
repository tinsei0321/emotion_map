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
            ok = got == expected
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


if __name__ == '__main__':
    run_eval()
