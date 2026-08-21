@echo off
cd /d "%~dp0"

echo ============================================================
echo  EMC x dsh One-Click Launcher (Web 8080 + MCP 8600)
echo ============================================================
echo.

REM ---- 1. Start MCP server (port 8600) ----
netstat -ano | findstr ":8600.*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [OK] MCP server already running (8600)
) else (
    echo [LOAD] Starting MCP server (8600)...
    start "EMC MCP (8600)" /min py tools\mcp_server_emc.py --http --port 8600
    echo [OK] MCP server starting in background
)
echo.

REM ---- 2. Kill old web processes ----
echo [WAIT] Cleaning old serve.py / backend (8080/8000)...
set _killed=0
for /f "tokens=5" %%a in (^'netstat -ano ^| findstr /C:":8080 " ^| findstr /C:"LISTENING"^'^) do (
  taskkill /F /PID %%a >nul 2>&1
  set _killed=1
)
for /f "tokens=5" %%a in (^'netstat -ano ^| findstr /C:":8000 " ^| findstr /C:"LISTENING"^'^) do (
  taskkill /F /PID %%a >nul 2>&1
  set _killed=1
)
if "%_killed%"=="0" echo       (clean start)
ping -n 2 127.0.0.1 >nul 2>&1
echo.

REM ---- 3. Start web (foreground) ----
echo [OK] Starting serve.py (8080)...
echo.
echo   Browser: http://localhost:8080/frontend/index.html
echo   MCP:     port 8600 (background window)
echo   dsh:     dsh --profile emc-test "question"
echo.
echo   Ctrl+C here = stop web. MCP stays running.
echo   Close MCP window (taskbar) = stop MCP.
echo.
echo [WAIT] 20-30s for RAG model warmup...
echo ------------------------------------------------------------
py frontend/serve.py 8080 --open=main

echo.
echo [ERR] serve.py exited. Check error above.
pause
