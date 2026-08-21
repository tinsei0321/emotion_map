@echo off
title EMC x dsh - One-Click Launcher
chcp 65001 >nul

echo ================================================
echo   EMC 情绪地图 x dsh 一键启动
echo ================================================
echo.

REM ── 检查 8080 是否已在运行 ──
netstat -ano | findstr ":8080.*LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [OK] EMC 服务已在运行 (8080)
    goto :OPEN_BROWSER
)

REM ── 启动 EMC 后端+前端 ──
echo [LOAD] 启动 EMC 服务 (约 30 秒含 RAG 预热)...
cd /d D:\Github\emotion_map
start /b py frontend\serve.py 8080 >nul 2>&1

REM ── 等待就绪 ──
set /a COUNT=0
:WAIT_LOOP
timeout /t 2 /nobreak >nul
set /a COUNT+=1
curl -s -o nul -w "%%{http_code}" http://localhost:8080/api/v1/health 2>nul | findstr "200" >nul
if %errorlevel%==0 (
    echo [OK] EMC 服务就绪 ^(耗时 %COUNT%x2s^)
    goto :OPEN_BROWSER
)
if %COUNT% lss 30 goto :WAIT_LOOP
echo [WARN] 等待超时 (60s)·请手动检查 http://localhost:8080
goto :EOF

:OPEN_BROWSER
echo [OK] 打开浏览器...
start http://localhost:8080/frontend/index.html
echo.
echo ================================================
echo   浏览器已打开 EMC 地图
echo.
echo   在 dsh 终端中使用:
echo     dsh --profile emc-test "你的分析问题"
echo.
echo   关闭 EMC: 关闭本窗口或 Ctrl+C
echo ================================================
pause >nul
