@echo off
title EMC x dsh Launcher
echo ================================================
echo   EMC x dsh One-Click Launcher
echo ================================================
echo.

REM Check if MCP (8600) already running
netstat -ano | findstr ":8600.*LISTENING" >nul 2>&1
if not %errorlevel%==0 (
    echo [LOAD] Starting MCP server (port 8600)...
    cd /d D:\Github\emotion_map
    start "EMC MCP Server" /min py tools\mcp_server_emc.py --http --port 8600
) else (
    echo [OK] MCP server already running (8600)
)

REM Check if 8080 already running
netstat -ano | findstr ":8080.*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [OK] EMC web already running (8080)
    goto OPEN_BROWSER
)

REM Start EMC web
echo [LOAD] Starting EMC web (~30s)...
cd /d D:\Github\emotion_map
start /b py frontend\serve.py 8080 >nul 2>&1

set /a COUNT=0
:WAIT_LOOP
timeout /t 2 /nobreak >nul 2>&1
set /a COUNT+=1
py -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/v1/health', timeout=3)" >nul 2>&1
if %errorlevel%==0 goto OPEN_BROWSER
if %COUNT% lss 30 goto WAIT_LOOP
echo [WARN] Web timeout. Check: http://localhost:8080
goto SHOW_HINT

:OPEN_BROWSER
echo [OK] EMC ready!
start http://localhost:8080/frontend/index.html

:SHOW_HINT
echo.
echo ================================================
echo   Browser: EMC map
echo   MCP server: port 8600 (persistent)
echo.
echo   In any terminal:
echo     dsh --profile emc-test "your question"
echo.
echo   Terminal can be closed freely.
echo ================================================
pause
