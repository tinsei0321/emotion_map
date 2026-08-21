@echo off
title EMC x dsh Launcher
echo ================================================
echo   EMC x dsh One-Click Launcher
echo ================================================
echo.
cd /d D:\Github\emotion_map

REM Start MCP server (port 8600) if not running
netstat -ano | findstr ":8600.*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [OK] MCP server already running (8600)
) else (
    echo [LOAD] Starting MCP server (port 8600)...
    start "EMC MCP (8600)" /min py tools\mcp_server_emc.py --http --port 8600
)

REM Start EMC web (port 8080) if not running
netstat -ano | findstr ":8080.*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [OK] EMC web already running (8080)
    goto OPEN_BROWSER
)

echo [LOAD] Starting EMC web (8080)...
start "EMC Web (8080)" /min py frontend\serve.py 8080

REM Wait for web ready
echo [LOAD] Waiting for web ready...
set /a COUNT=0
:WAIT_LOOP
timeout /t 2 /nobreak >nul 2>&1
set /a COUNT+=1
py -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/v1/health', timeout=3)" >nul 2>&1
if %errorlevel%==0 goto OPEN_BROWSER
if %COUNT% lss 30 goto WAIT_LOOP
echo [WARN] Web startup timeout (60s)
goto SHOW_HINT

:OPEN_BROWSER
echo [OK] EMC ready!
start http://localhost:8080/frontend/index.html

:SHOW_HINT
echo.
echo ================================================
echo   Browser: EMC map (8080)
echo   MCP server: port 8600 (persistent)
echo   Both run in minimized windows.
echo.
echo   In any terminal:
echo     dsh --profile emc-test "question"
echo ================================================
pause
