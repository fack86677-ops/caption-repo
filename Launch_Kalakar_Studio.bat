@echo off
title Kalakar AI Caption & Subtitle Studio
cd /d "%~dp0"
echo ============================================================
echo   Starting Kalakar AI Caption Studio Web Server...
echo ============================================================
echo.
echo Server starting on http://localhost:7860 ...
echo Please keep this window open while using the app!
echo.
timeout /t 2 /nobreak >nul
start "" "http://localhost:7860"
"C:\Users\Abc\AppData\Local\Programs\Python311\python.exe" server.py 7860
pause
