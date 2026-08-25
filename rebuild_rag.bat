@echo off
REM PT-CB16 S2: RAG 索引半自动重建（双击=检查知识源是否新于索引，陈旧才重建）
cd /d "%~dp0"
set HF_HUB_OFFLINE=1
py tools\rag_index.py --rebuild-if-stale
echo.
pause
