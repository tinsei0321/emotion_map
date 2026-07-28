"""L3 情境日志 · 每次问答自动 append（自成长闭环的"记忆"原料）。

不动 prompt（不注入）；只被 ai_qa/consolidate.py 周期挖掘 → 提议 L2 编辑（人审）。
存储：DATA/ai_qa/episodes.jsonl（本地，.gitignore 排除——含用户问题，隐私）。

字段精简到"够挖掘"：question 摘要 / diagnose 卡关键字段 / defense 防线结果（CB-09 D024·取代旧 review 判定）/ final 摘要（不全文）。
"""
import json
import os
import time

_EPISODE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'DATA', 'ai_qa')
_EPISODE_PATH = os.path.join(_EPISODE_DIR, 'episodes.jsonl')

_FINAL_EXCERPT = 360   # final 答文 excerpt 长度（控制 jsonl 体积；全文留 trace/历史，不进 episode）


def _excerpt(s, n=_FINAL_EXCERPT):
    s = s or ''
    return s if len(s) <= n else s[:n] + '…'


def log_episode(question, diagnose=None, final=None, defense=None, ok=True, extra=None, capsule_clicked=None):
    """append 一条 episode 到 jsonl。失败静默（不阻塞问答交付）。

    diagnose: diagnose 卡 dict（取 scale/domain_lens/decision_type/outlet/data_plan.strategy/method）
    defense:  质量防线结果 dict（CB-09 D024·取 degraded/fixes/skipped·取代旧 review verdicts）
    final:    最终答文（excerpt）
    capsule_clicked: CB-09 D034 用户点击的胶囊 skill（Pro 排序自我成长偏好信号·供 consolidate 挖掘）
    """
    try:
        os.makedirs(_EPISODE_DIR, exist_ok=True)
    except Exception:
        return False
    dp = (diagnose or {}).get('data_plan') or {}
    rec = {
        'ts': int(time.time()),
        'ok': bool(ok),
        'question': _excerpt(question, 200),
        'diagnose': {
            'scale': (diagnose or {}).get('scale'),
            'domains': (diagnose or {}).get('domain_lens') or [],
            'decision_type': (diagnose or {}).get('decision_type'),
            'outlet': (diagnose or {}).get('outlet'),
            'strategy': dp.get('strategy'),
            'method': (diagnose or {}).get('method') or [],
        } if diagnose and not diagnose.get('degraded') else {'degraded': True},
        'defense': {
            'degraded': (defense or {}).get('degraded', False),
            'fixes': (defense or {}).get('fixes') or [],
            'skipped': (defense or {}).get('skipped'),
        } if defense else None,
        'final_excerpt': _excerpt(final),
        'capsule_clicked': capsule_clicked,   # CB-09 D034：None=非胶囊点击 / skill=点击的胶囊
    }
    if extra:
        rec.update(extra)
    try:
        with open(_EPISODE_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        return True
    except Exception:
        return False


def read_episodes():
    """读全部 episode（consolidate 用）。坏行跳过。"""
    if not os.path.isfile(_EPISODE_PATH):
        return []
    out = []
    with open(_EPISODE_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def episode_path():
    return _EPISODE_PATH
