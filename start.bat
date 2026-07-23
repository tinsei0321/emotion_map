@echo off
cd /d "%~dp0"

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
echo ------------------------------------------------------------
py frontend/serve.py 8080 --open=both

echo.
echo [ERR] serve.py exited (if you did not press Ctrl+C, check the error above).
pause
