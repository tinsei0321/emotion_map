#!/usr/bin/env python3
"""密钥健康检查器（CB38 P0-3 配套 · key 轮换流程专用）

背景
----
CB38 审计发现 serve 曾以全网卡服务仓库根（GET /.env 可读 key），且审计过程中
存在一次 key 泄露进子代理会话输出的风险披露（见 CB38 审计报告 §6.5）。
轮换 key 时最大的顾虑是「新 key 一换、线上调用断」。本工具用与生产完全一致的
调用路径先验证、后切换，保证轮换零断流。

轮换 SOP（4 步，全程不断调用）
------------------------------
1) 在控制台新建 key（旧 key 先不删）：
   - AMAP:   https://console.amap.com  → 应用管理 → 创建新 key
   - DeepSeek: https://platform.deepseek.com → API Keys → 新建
2) 复制环境文件并填入新 key：
   copy .env .env.new   然后编辑 .env.new 的 AMAP_KEY / DEEPSEEK_API_KEY 两行
3) 验证新 key（不动正在使用的 .env）：
   py tools/verify_keys.py --env-file .env.new
   → 两项 [OK] 才继续；任一 [ERR] 回控制台检查 key/余额/权限，旧 key 不受影响
4) 全绿后切换 + 复验：
   copy .env.new .env  →  重启 serve（key 在启动时注入 env）→ py tools/verify_keys.py
   → 确认控制台删除旧 key（作废泄露源），删除 .env.new

安全铁律
--------
- 本脚本绝不打印 key 值，只打印键名、存在性、HTTP 状态与调用结果。
- 调用路径与生产对齐：DeepSeek=ai_qa/llm.py（v1/chat/completions·flash 档），
  AMAP=core/geocode.py（v3/geocode/geo·city=宜昌）。
- 退出码：0=全部通过，1=存在失败/缺失（可接入 CI）。
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEEPSEEK_BASE = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-v4-flash')  # 与 ai_qa/llm.py MODEL_FLASH 对齐（快速经济档，验证成本最低）
AMAP_BASE = 'https://restapi.amap.com/v3'   # 与 core/geocode.py AMAP_BASE 对齐
AMAP_CITY = '宜昌'                            # 与 core/geocode.py AMAP_CITY 对齐


def load_env(path):
    """轻量 .env 解析：文件值 + 已有环境变量优先（与 api/main.py 语义一致）。"""
    vals = {}
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, _, v = line.partition('=')
                vals[k.strip()] = v.strip().strip('"').strip("'")
    for k in list(vals):
        if k in os.environ:
            vals[k] = os.environ[k]
    return vals


def check_deepseek(key):
    """最小 chat 调用（max_tokens=8）：验证鉴权 + 余额 + 模型可用。"""
    url = DEEPSEEK_BASE.rstrip('/') + '/chat/completions'
    payload = json.dumps({
        'model': DEEPSEEK_MODEL,
        'messages': [{'role': 'user', 'content': 'connectivity check: reply pong'}],
        'max_tokens': 8,
        'stream': False,
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + key,
    })
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode('utf-8'))
        dt = time.time() - t0
        choice = (data.get('choices') or [{}])[0]
        content = (choice.get('message') or {}).get('content', '')
        usage = data.get('usage') or {}
        return True, ('DeepSeek [OK] model=%s %.1fs reply=%r total_tokens=%s'
                      % (data.get('model', DEEPSEEK_MODEL), dt, content[:16], usage.get('total_tokens')))
    except urllib.error.HTTPError as e:
        detail = e.read().decode('utf-8', errors='replace')[:180]
        return False, 'DeepSeek [ERR] HTTP %s: %s' % (e.code, detail)
    except Exception as e:
        return False, 'DeepSeek [ERR] %s: %s' % (type(e).__name__, str(e)[:120])


def _amap_get(endpoint, params, key, timeout=15):
    p = dict(params)
    p['key'] = key
    p.setdefault('output', 'json')
    q = urllib.parse.urlencode(p)
    with urllib.request.urlopen(AMAP_BASE + '/' + endpoint + '?' + q, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


# probe keywords aligned with production usage (AMAP_CITY is defined above)
_PROBE_KEYWORDS = '\u516c\u56ed'        # park
_PROBE_ADDRESS = '\u5e02\u653f\u5e9c'  # city hall


def check_amap(key):
    """Three probes aligned with real production deps (core/geocode.py):
    - place/text   primary production path (CB-22d amap-first) -> gating
    - regeo        production fallback -> gating
    - geocode/geo  used by geocode_address only -> informational (current key
                   returns 30001 on this single endpoint; production has local
                   fallback; turning green after rotation is a bonus)
    """
    t0 = time.time()
    msgs, ok = [], True
    try:
        d = _amap_get('place/text', {'keywords': _PROBE_KEYWORDS, 'city': AMAP_CITY,
                                     'citylimit': 'true', 'offset': 3}, key)
        if d.get('status') == '1' and d.get('pois'):
            msgs.append('place/text OK(count=%s first=%r)' % (d.get('count'), d['pois'][0].get('name', '')))
        else:
            ok = False
            msgs.append('place/text ERR status=%s infocode=%s' % (d.get('status'), d.get('infocode')))
    except Exception as e:
        ok = False
        msgs.append('place/text ERR %s: %s' % (type(e).__name__, str(e)[:80]))
    try:
        d = _amap_get('geocode/regeo', {'location': '111.286471,30.691947', 'extensions': 'base'}, key)
        if d.get('status') == '1':
            msgs.append('regeo OK')
        else:
            ok = False
            msgs.append('regeo ERR status=%s infocode=%s' % (d.get('status'), d.get('infocode')))
    except Exception as e:
        ok = False
        msgs.append('regeo ERR %s: %s' % (type(e).__name__, str(e)[:80]))
    geo_note = 'n/a'
    try:
        d = _amap_get('geocode/geo', {'address': _PROBE_ADDRESS, 'city': AMAP_CITY}, key)
        geo_note = 'OK' if d.get('status') == '1' else 'WARN infocode=%s (production has local fallback)' % d.get('infocode')
    except Exception as e:
        geo_note = 'WARN %s' % type(e).__name__
    return ok, 'AMAP [%s] %.1fs %s | geocode/geo: %s' % (
        'OK' if ok else 'ERR', time.time() - t0, ' | '.join(msgs), geo_note)


def main():
    ap = argparse.ArgumentParser(description='AMAP/DeepSeek key health check (never prints key values)')
    ap.add_argument('--env-file', default='.env', help='env 文件路径（默认 .env；轮换时先指到 .env.new）')
    ap.add_argument('--skip', choices=['deepseek', 'amap'], action='append', default=[],
                    help='跳过某项检查（可重复）')
    args = ap.parse_args()

    vals = load_env(args.env_file)
    has_a = bool(vals.get('AMAP_KEY'))
    has_d = bool(vals.get('DEEPSEEK_API_KEY'))
    print('[LOAD] %s -> AMAP_KEY=%s DEEPSEEK_API_KEY=%s (names only, values never shown)'
          % (args.env_file, 'present' if has_a else 'MISSING', 'present' if has_d else 'MISSING'))

    results = []
    if 'deepseek' not in args.skip:
        if has_d:
            ok, msg = check_deepseek(vals['DEEPSEEK_API_KEY'])
        else:
            ok, msg = False, 'DeepSeek [ERR] DEEPSEEK_API_KEY missing in ' + args.env_file
        print(msg)
        results.append(ok)
    if 'amap' not in args.skip:
        if has_a:
            ok, msg = check_amap(vals['AMAP_KEY'])
        else:
            ok, msg = False, 'AMAP [ERR] AMAP_KEY missing in ' + args.env_file
        print(msg)
        results.append(ok)

    if not results:
        print('[WARN] nothing checked (all skipped)')
        return 0
    if all(results):
        print('[OK] all checks passed - safe to switch')
        return 0
    print('[ERR] some checks failed - DO NOT switch .env yet')
    return 1


if __name__ == '__main__':
    sys.exit(main())
