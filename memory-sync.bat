@echo off
title AutoMemory distill sync (gitee mirror)
py "%~dp0tools\memory_sync.py" push %*
pause
