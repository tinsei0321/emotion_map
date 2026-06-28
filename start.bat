@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [OK] emotion-map 启动中（前端 :8080 + 后端 :8000，Ctrl+C 同时停止）...
echo.
py frontend/serve.py 8080
pause
