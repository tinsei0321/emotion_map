@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  [到岗后同步] 从硬盘拉取并 rebase
echo ============================================
py tools/sync_guard.py --mode arrive
echo.
pause
