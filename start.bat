@echo off
cd /d "%~dp0"

REM ---- MCP server (port 8600) ----
netstat -ano | findstr ":8600.*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [OK] MCP server already running ^(8600^)
) else (
    echo [LOAD] Starting MCP server ^(8600^)...
    start "EMC MCP ^(8600^)" /min py tools\mcp_server_emc.py --http --port 8600
    echo [OK] MCP server starting in background
)

REM ---- dsh web (port 3080) from EMCxDSH workspace ----
REM PT-CB11 修复(08-22)：本段原在 serve.py(前台阻塞)之后=永不执行；移到前面·并把 MCP 段的 goto 改 if/else 防 skipped
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
echo      Main: http://localhost:8080/frontend/index.html
echo      Test: http://localhost:8080/frontend/index.html?test=1
echo      Stop: press Ctrl+C in this window (stops frontend + backend)
echo      After code edits: hard-reload browser (Ctrl+Shift+R),
echo             check the build stamp time (bottom-right) updated.
echo.
echo [WAIT] 预计 20-30s 就绪（含 BGE RAG 模型同步预热~15s：启动慢是有意设计·换首问稳定）
echo.
echo ------------------------------------------------------------
py frontend/serve.py 8080 --open=main

echo.
echo [ERR] serve.py exited (if you did not press Ctrl+C, check the error above).
pause

