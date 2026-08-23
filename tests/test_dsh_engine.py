# -*- coding: utf-8 -*-
"""SHELL2(FIX) P1 配套测试：/aiqa/dsh_engine 端点（FIX-01/02/03/05）。

覆盖（monkeypatch subprocess/shutil·零真实 spawn）：
  ① 命令解析三分支：无 dsh→语义化拒绝 / POSIX 直调 / npm shim→node 直调 bin.js；
  ② FIX-03 fail-closed：bin.js 缺失→「安装布局未识别」（死路径已删）；
  ③ FIX-02：max_length=4000 pydantic 422 + OSError→语义化降级；空问句拒绝；
  ④ 超时夹取（10→30 / 999→600）+ TimeoutExpired 语义化；
  ⑤ FIX-05：stdout >200KB 截断标记；
  ⑥ FIX-01：Semaphore(2) 有界并发（4 并发→峰值 ≤2·全完成）。
"""
import asyncio
import subprocess
import threading

import pytest
from pydantic import ValidationError

from api.aiqa_routes import DshEngineIn, post_dsh_engine, _dsh_semaphore


def _run(coro):
    return asyncio.run(coro)


def _ok_proc(stdout='答案文本', stderr='', rc=0):
    class P:
        pass
    p = P()
    p.stdout, p.stderr, p.returncode = stdout, stderr, rc
    return p


class TestDshEngineResolve:
    """①命令解析三分支 + ②fail-closed（FIX-03）。"""

    def test_no_dsh_in_path(self, monkeypatch):
        monkeypatch.setattr('shutil.which', lambda name: None)
        r = _run(post_dsh_engine(DshEngineIn(question='什么是留改拆')))
        assert r['ok'] is False and 'not found' in r['error']

    def test_posix_direct(self, monkeypatch):
        calls = []
        monkeypatch.setattr('shutil.which', lambda name: '/usr/local/bin/dsh' if name == 'dsh' else None)
        monkeypatch.setattr('subprocess.run', lambda cmd, **kw: calls.append((cmd, kw)) or _ok_proc())
        r = _run(post_dsh_engine(DshEngineIn(question='什么是留改拆')))
        assert r['ok'] is True and r['output'] == '答案文本'
        cmd = calls[0][0]
        assert cmd[:3] == ['/usr/local/bin/dsh', '--profile', 'emc-test'] and cmd[3] == '什么是留改拆'
        assert calls[0][1].get('shell') is False   # 零 shell 拼接

    def test_npm_shim_node_direct(self, monkeypatch):
        """Windows npm shim→node 直调 bin.js（argv 传参·零注入主路径）。"""
        calls = []
        monkeypatch.setattr('shutil.which', lambda name: (r'C:\npm\dsh.cmd' if name == 'dsh' else 'node'))

        def fake_isfile(path):
            return path.endswith('bin.js')   # bin.js 在·node.exe 不在（走 PATH node）

        monkeypatch.setattr('os.path.isfile', fake_isfile)
        monkeypatch.setattr('subprocess.run', lambda cmd, **kw: calls.append(cmd) or _ok_proc())
        r = _run(post_dsh_engine(DshEngineIn(question='问句含 & | > " 特殊字符')))
        assert r['ok'] is True
        cmd = calls[0]
        assert cmd[0] == 'node' and cmd[1].endswith('bin.js')
        assert cmd[-1] == '问句含 & | > " 特殊字符'   # 问句作为单一 argv 元素（无元字符面）

    def test_shim_missing_binjs_fail_closed(self, monkeypatch):
        """FIX-03：bin.js 缺失→语义化拒绝（不留死路径·不跑字符串 cmdline）。"""
        ran = []
        monkeypatch.setattr('shutil.which', lambda name: r'C:\npm\dsh.cmd' if name == 'dsh' else None)
        monkeypatch.setattr('os.path.isfile', lambda path: False)
        monkeypatch.setattr('subprocess.run', lambda *a, **kw: ran.append(1) or _ok_proc())
        r = _run(post_dsh_engine(DshEngineIn(question='q')))
        assert r['ok'] is False and '安装布局未识别' in r['error']
        assert not ran, 'fail-closed 分支不得触发 subprocess'


class TestDshEngineValidation:
    """③FIX-02 + 空问句 + ④超时。"""

    def test_empty_question(self):
        r = _run(post_dsh_engine(DshEngineIn(question='   ')))
        assert r['ok'] is False and r['error'] == 'empty question'

    def test_max_length_rejects(self):
        with pytest.raises(ValidationError):
            DshEngineIn(question='x' * 4001)
        DshEngineIn(question='x' * 4000)   # 边界值可收

    def test_oserror_semantic(self, monkeypatch):
        """FIX-02：subprocess OSError（如 WinError 206 命令行过长）→ ok:False 不 500。"""
        monkeypatch.setattr('shutil.which', lambda name: '/usr/local/bin/dsh')

        def boom(cmd, **kw):
            raise OSError(206, '文件名或扩展名太长')

        monkeypatch.setattr('subprocess.run', boom)
        r = _run(post_dsh_engine(DshEngineIn(question='q')))
        assert r['ok'] is False and '问句过长或系统限制' in r['error']

    @pytest.mark.parametrize('ask, expect', [(10, 30), (999, 600), (120, 120)])
    def test_timeout_clamp(self, monkeypatch, ask, expect):
        got = []
        monkeypatch.setattr('shutil.which', lambda name: '/usr/local/bin/dsh')
        monkeypatch.setattr('subprocess.run', lambda cmd, **kw: got.append(kw.get('timeout')) or _ok_proc())
        _run(post_dsh_engine(DshEngineIn(question='q', timeout_s=ask)))
        assert got[0] == expect

    def test_timeout_expired_semantic(self, monkeypatch):
        monkeypatch.setattr('shutil.which', lambda name: '/usr/local/bin/dsh')

        def slow(cmd, **kw):
            raise subprocess.TimeoutExpired(cmd, kw.get('timeout'))

        monkeypatch.setattr('subprocess.run', slow)
        r = _run(post_dsh_engine(DshEngineIn(question='q', timeout_s=45)))
        assert r['ok'] is False and 'timeout' in r['error'] and '45s' in r['error']


class TestDshEngineOutput:
    """⑤FIX-05 输出截断。"""

    def test_stdout_truncate_200kb(self, monkeypatch):
        monkeypatch.setattr('shutil.which', lambda name: '/usr/local/bin/dsh')
        big = 'A' * (200 * 1024 + 999)
        monkeypatch.setattr('subprocess.run', lambda cmd, **kw: _ok_proc(stdout=big))
        r = _run(post_dsh_engine(DshEngineIn(question='q')))
        assert r['ok'] is True and r['truncated'] is True and len(r['output']) == 200 * 1024

    def test_small_output_not_truncated(self, monkeypatch):
        monkeypatch.setattr('shutil.which', lambda name: '/usr/local/bin/dsh')
        monkeypatch.setattr('subprocess.run', lambda cmd, **kw: _ok_proc(stdout='短答案'))
        r = _run(post_dsh_engine(DshEngineIn(question='q')))
        assert r['truncated'] is False and r['output'] == '短答案'


class TestDshEngineConcurrency:
    """⑥FIX-01：Semaphore(2) 有界并发——4 并发→峰值 ≤2·全完成。"""

    def test_semaphore_bounds(self, monkeypatch):
        assert _dsh_semaphore._value == 2   # 闸容量锁定（防误改）
        monkeypatch.setattr('shutil.which', lambda name: '/usr/local/bin/dsh')
        lock = threading.Lock()
        state = {'active': 0, 'peak': 0}

        def tracked_run(cmd, **kw):
            with lock:
                state['active'] += 1
                state['peak'] = max(state['peak'], state['active'])
            try:
                import time
                time.sleep(0.25)   # 真实小睡·制造重叠窗口
            finally:
                with lock:
                    state['active'] -= 1
            return _ok_proc()

        monkeypatch.setattr('subprocess.run', tracked_run)

        async def burst():
            return await asyncio.gather(*[
                post_dsh_engine(DshEngineIn(question=f'q{i}')) for i in range(4)
            ])

        results = _run(burst())
        assert all(r['ok'] for r in results), '4 并发全完成'
        assert state['peak'] <= 2, f"并发峰值 {state['peak']} > 2（信号量失效）"
