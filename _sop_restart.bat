@echo off
cd /d d:\Github\emotion_map

echo [1/4] Killing existing Streamlit processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *streamlit*" 2>nul
timeout /t 2 /nobreak >nul

echo [2/4] Clearing all __pycache__...
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
echo Done.

echo [3/4] Verifying add_selection_marker...
python -c "from core.map_engine import add_selection_marker; print('[OK] add_selection_marker:', add_selection_marker.__name__)"

echo [4/4] Starting Streamlit...
python -m streamlit run apps/app_main.py --server.port 8501