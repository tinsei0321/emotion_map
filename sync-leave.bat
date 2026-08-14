@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  [离开前同步] 提交全部 + 推送硬盘 + 推送 GitHub
echo ============================================
py tools/sync_guard.py --mode leave
echo.
pause
