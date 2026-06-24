#!/usr/bin/env python3
"""DeepSeek 地域化语料扩充（Phase 1b，可选）
================================================
起步语料 emotion_corpus.json 已达本地性目标（全图 ~60%、重点 74-79%）。
本脚本用 DeepSeek 按需把每 (zone, polarity) 桶扩到 N 条 + flavor 变体，
SnowNLP 极性带校验后追加（剔除不落带/重复），提升本地性鲁棒性与时序风味覆盖。

用法:
  set DEEPSEEK_API_KEY=...   (或 .env)
  py SCRIPT/poi_data/generate_corpus.py                 # 默认每桶补到 15 条
  py SCRIPT/poi_data/generate_corpus.py --target 20     # 每桶补到 20 条
  py SCRIPT/poi_data/generate_corpus.py --dry-run       # 只打印不写回

PII 安全：prompt 明确禁止真实用户名/ID；生成文本无个人身份信息。
"""
import os
import sys
import json
import time
import random

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.dirname(_HERE))

from core.utils import safe_print

CORPUS_FILE = os.path.join(_HERE, 'emotion_corpus.json')
DEEPSEEK_URL = os.environ.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/chat/completions')
MAX_RETRIES = 3
TIMEOUT = 40

# 复用 emotion_text_pool 的极性带 + SnowNLP 校验
from emotion_text_pool import POLARITY_BANDS, _snownlp_score, _in_band  # noqa: E402
from core.place_layer import get_place_layer  # noqa: E402

POLARITY_CN = {'positive': '积极（满意/推荐/点赞）', 'negative': '消极（抱怨/失望/吐槽）', 'neutral': '中性（客观陈述）'}


def _api_key():
    key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not key:
        # 尝试 .env
        env_path = os.path.join(_ROOT, '.env')
        if os.path.exists(env_path):
            for line in open(env_path, encoding='utf-8'):
                if line.strip().startswith('DEEPSEEK_API_KEY'):
                    key = line.split('=', 1)[1].strip().strip('"').strip("'")
    return key


def _deepseek_generate(prompt, key):
    """调 DeepSeek，返回文本。镜像 relevance_filter 的 requests+重试。"""
    import requests
    headers = {'Authorization': 'Bearer {}'.format(key), 'Content-Type': 'application/json'}
    payload = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.9,
        'max_tokens': 1200,
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content']
        except Exception as e:
            safe_print('[WARN] DeepSeek attempt {}/{}: {}'.format(attempt, MAX_RETRIES, str(e)[:120]))
            if attempt == MAX_RETRIES:
                raise
            time.sleep(2 ** attempt)
    return ''


def _parse_lines(text):
    """把 LLM 返回拆成干净短句（去编号/引号/空行）。"""
    out = []
    for line in text.splitlines():
        s = line.strip().lstrip('0123456789.-、）)）. ').strip('「」""\'')
        if 4 <= len(s) <= 40 and not s.startswith(('例', '注', '说明')):
            out.append(s)
    return out


def expand(target=15, dry_run=False):
    key = _api_key()
    if not key:
        safe_print('[ERR] DEEPSEEK_API_KEY 未设置（.env 或环境变量）。本脚本可选，起步语料已达标。')
        return
    pl = get_place_layer()
    data = json.load(open(CORPUS_FILE, encoding='utf-8'))
    cand = data.setdefault('candidates', {})
    rng = random.Random(2606)

    for zid in pl.zone_by_id:
        pk = pl.place_keywords(zid)
        place_kw = '、'.join(pk.get('place_keywords', [])[:6]) or pl.zone_by_id[zid]['name_zh']
        for pol in ('positive', 'negative', 'neutral'):
            key_str = '{}|{}'.format(zid, pol)
            cur = cand.get(key_str, [])
            need = target - len(cur)
            if need <= 0:
                continue
            prompt = (
                '你是宜昌市民，在{}（关键词：{}）发了一条{}点评。写{}条互不相同的真实感短评'
                '（每条8-25字，口语化，可带地标/特征词）。只输出短评，每行一条，'
                '禁止人名/用户名/ID，禁止编造具体店铺电话。极性必须明确{}。'
            ).format(pl.zone_by_id[zid]['name_zh'], place_kw, POLARITY_CN[pol],
                     need, POLARITY_CN[pol])
            try:
                raw = _deepseek_generate(prompt, key)
            except Exception as e:
                safe_print('[ERR] {} {} 生成失败：{}'.format(zid, pol, str(e)[:100]))
                continue
            new_texts = _parse_lines(raw)
            kept = []
            for t in new_texts:
                if t in cur or t in kept:
                    continue
                if _in_band(_snownlp_score(t), pol):   # 落极性带才收
                    kept.append(t)
            safe_print('[{}] {}|{} 现有{} 需{} 生成{} 落带{} {}'.format(
                'DRY' if dry_run else 'OK', zid, pol, len(cur), need, len(new_texts), len(kept),
                '(dry-run 不写回)' if dry_run else ''))
            if not dry_run and kept:
                cand[key_str] = cur + kept

    if not dry_run:
        json.dump(data, open(CORPUS_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        safe_print('[OK] 已写回 {}（扩充后跑 build_pool 重建校验池）'.format(CORPUS_FILE))


if __name__ == '__main__':
    tgt = 15
    dry = '--dry-run' in sys.argv
    for i, a in enumerate(sys.argv):
        if a == '--target' and i + 1 < len(sys.argv):
            tgt = int(sys.argv[i + 1])
    expand(target=tgt, dry_run=dry)
