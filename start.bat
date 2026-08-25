@echo off
cd /d "%~dp0"

REM ---- PT-CB17: cdh 产品层 AGENTS.md 同步（仓内权威副本 docs/cdh/AGENTS.md → Codex 工作目录）----
REM 双机纪律：权威副本在仓内，_codex_cwd 为派生位置；每次启动强制同步（防两处漂移）。
if not exist "..\_codex_cwd" mkdir "..\_codex_cwd" >nul 2>&1
copy /Y "docs\cdh\AGENTS.md" "..\_codex_cwd\AGENTS.md" >nul 2>&1
if %errorlevel%==0 (echo [OK] cdh AGENTS.md synced to ..\_codex_cwd) else (echo [WARN] cdh AGENTS.md sync failed - using existing copy)

REM ---- SHELL2(FIX) FIX-07: dsh engine dependency note ----
REM The EMC dsh engine (?engine=dsh in the chat panel) calls dsh headless, whose
REM emc-test profile consumes EMC tools via MCP over HTTP at http://127.0.0.1:8600/mcp.
REM Without 8600 running, dsh degrades to tool-less pure QA (knowledge answers only,
REM no map linkage). This launcher starts 8600 below BEFORE the web app, so the
REM dependency is satisfied. Health check: netstat -ano | findstr ":8600.*LISTENING"

REM ---- MCP server (port 8600) ----
REM PT-CB17 治本（21:15 旧病复发案）：旧逻辑「8600 在听就跳过」= 工具进程永远载旧码
REM （8000/8080 重启了但工具是 8600 供的——修复不生效的根因）。改为与 8000 同款：先杀旧再起新。
netstat -ano | findstr ":8600.*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [LOAD] Killing stale MCP server ^(8600^) to load latest code...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8600.*LISTENING"') do (
        echo       - killed PID %%a ^(port 8600^)
        taskkill /F /PID %%a >nul 2>&1
    )
    ping -n 2 127.0.0.1 >nul 2>&1
)
echo [LOAD] Starting MCP server ^(8600^)...
start "EMC MCP ^(8600^)" /min py tools\mcp_server_emc.py --http --port 8600
echo [OK] MCP server starting in background

REM ---- wait for MCP (8600) ready ----
REM 时序坑修复(08-23)：dsh web 的 mcp-emc 插件 failOnStartupError=true，8600 未监听就起 3080
REM 会 ECONNREFUSED 崩掉（PT-CB11 段竞态：spawn 8600 后立即起 dsh web，而 MCP 预热 15-30s 含 RAG 模型加载）。
REM 轮询等待 8600 LISTENING，最多 40s；超时警告后继续（dsh web 若仍崩，等 MCP 起来后重跑 start.bat 即可）。
set /a _mcp_wait=0
:MCP_WAIT
netstat -ano | findstr ":8600.*LISTENING" >nul 2>&1
if %errorlevel%==0 goto MCP_READY
set /a _mcp_wait+=1
if %_mcp_wait% GEQ 40 (
    echo [WARN] MCP 8600 not ready after 40s - starting dsh web anyway ^(may crash, rerun start.bat after MCP is up^)
    goto DSH_CHECK
)
ping -n 2 127.0.0.1 >nul 2>&1
goto MCP_WAIT
:MCP_READY
if %_mcp_wait% GTR 0 echo [OK] MCP server ready on 8600 ^(waited %_mcp_wait%s^)

REM ---- dsh web (port 3080) from EMCxDSH workspace ----
REM PT-CB11 修复(08-22)：本段原在 serve.py(前台阻塞)之后=永不执行；移到前面·并把 MCP 段的 goto 改 if/else 防 skipped
:DSH_CHECK
netstat -ano | findstr ":3080.*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [OK] dsh web already running ^(3080^)
) else (
    echo [LOAD] Starting dsh web from EMCxDSH...
    cd /d D:\Github\EMCxDSH
    start "dsh web ^(3080^)" /min dsh web
    cd /d "%~dp0"
)

:WEB_START
echo.


echo ============================================================
echo  emotion-map launcher (single instance: auto-cleans old ones)
echo  [NEW] auto-opens MAIN + TEST pages when serve is ready
echo ============================================================
echo.
echo  本机最新提交（本次将运行的代码）：
git log -1 --format="    %%h  %%cI  %%s"
echo.
echo [WAIT] Killing old serve.py / backend (PIDs on 8080 / 8000)...
set _killed=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /C:":8080 " ^| findstr /C:"LISTENING"') do (
  echo       - killed PID %%a ^(port 8080^)
  taskkill /F /PID %%a >nul 2>&1
  set _killed=1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /C:":8000 " ^| findstr /C:"LISTENING"') do (
  echo       - killed PID %%a ^(port 8000^)
  taskkill /F /PID %%a >nul 2>&1
  set _killed=1
)
if "%_killed%"=="0" echo       (no old instance - clean start)
ping -n 2 127.0.0.1 >nul 2>&1

echo.
echo [OK] Starting serve.py (auto-opens browser when ready) ...
echo      Main(cdh): http://localhost:8080/frontend/index.html?engine=codex
echo      Light:     http://localhost:8080/frontend/index.html
echo      Test:      http://localhost:8080/frontend/index.html?test=1
echo      Stop: press Ctrl+C in this window (stops frontend + backend)
echo      After code edits: hard-reload browser (Ctrl+Shift+R),
echo             check the build stamp time (bottom-right) updated.
echo.
echo [WAIT] 预计 20-30s 就绪（含 BGE RAG 模型同步预热~15s：启动慢是有意设计·换首问稳定）
echo      怀疑撞旧码时：双击 devcheck.bat 一键核对三进程载码新旧
echo.
echo ------------------------------------------------------------
py frontend/serve.py 8080 --open=codex

echo.
echo [ERR] serve.py exited (if you did not press Ctrl+C, check the error above).
pause

