# -*- coding: utf-8 -*-
"""PT-CB15 PROMOTE P2-7：codex_engine 端点错误路径 + P2-9 竞争锁行为测。

端点（TestClient·仅挂 aiqa_router·轻量）：
- 空问句 → {'ok': False}（同步拒·不 422/500）；
- 桥启动失败（monkeypatch 解析 None）→ SSE error 帧 CODEX_BRIDGE_START（fail-closed·不 500）。
竞争锁（P2-9）：
- 自持/锁空/死 pid → 抢占成功；活实例持锁 → 让出（返 False）。
"""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _client():
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from api.aiqa_routes import aiqa_router
    app = FastAPI()
    app.include_router(aiqa_router)
    return TestClient(app)


def test_codex_engine_empty_question():
    c = _client()
    r = c.post('/aiqa/codex_engine', json={'question': '   '})
    assert r.status_code == 200
    assert r.json().get('ok') is False


def test_codex_engine_bridge_fail_sse(monkeypatch):
    """桥启动失败 → SSE 流内 error 帧（已开流不 500·语义化降级）。"""
    import core.codex_bridge as cb
    monkeypatch.setattr(cb, '_resolve_codex_exe', lambda: None)
    # 单例可能残留状态——强制重置（测隔离）
    br = cb.get_bridge()
    br._proc = None
    br._thread_id = None
    c = _client()
    with c.stream('POST', '/aiqa/codex_engine',
                  json={'question': 'hi', 'timeout_s': 30}) as r:
        assert r.status_code == 200
        body = ''.join(r.iter_text())
    assert 'CODEX_BRIDGE_START' in body
    assert 'event: error' in body


# ── P2-9 竞争锁行为 ─────────────────────────────────────────────────
def test_inbox_lock_claim_and_takeover(tmp_path, monkeypatch):
    import api.render_routes as rr
    monkeypatch.setattr(rr, 'INBOX_DIR', str(tmp_path))
    monkeypatch.setattr(rr, '_PIDLOCK', str(tmp_path / '.watcher.pid'))

    assert rr._try_claim_watch() is True            # 锁空 → 抢占（写入自身 pid）
    assert rr._try_claim_watch() is True            # 自持 → 续持
    (tmp_path / '.watcher.pid').write_text('999999999')   # 死 pid → 抢占接管
    assert rr._try_claim_watch() is True


def test_inbox_lock_yield_to_live_holder(tmp_path, monkeypatch):
    """活实例（子进程）持锁 → 本实例让出（返 False）。"""
    import api.render_routes as rr
    monkeypatch.setattr(rr, 'INBOX_DIR', str(tmp_path))
    monkeypatch.setattr(rr, '_PIDLOCK', str(tmp_path / '.watcher.pid'))

    holder = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
    try:
        (tmp_path / '.watcher.pid').write_text(str(holder.pid))
        assert rr._try_claim_watch() is False       # 他活实例持锁 → 让出
    finally:
        holder.kill()
        holder.wait()
