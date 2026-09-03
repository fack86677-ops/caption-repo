@echo off
title Push Harsh Caption Generator to GitHub
cls
echo ========================================================
echo  Harsh Caption Generator - GitHub Push Utility
echo ========================================================
echo.
echo Repo Target: https://github.com/fack86677-ops/caption-repo.git
echo.
set /p TOKEN="Apna GitHub Personal Access Token (PAT) yahan enter karein: "

if "%TOKEN%"=="" (
    echo [ERROR] Token enter nahi kiya gaya!
    pause
    exit /b
)

echo.
echo [1/3] Staging and Committing all files...
"%~dp0tools\git\cmd\git.exe" add -A
"%~dp0tools\git\cmd\git.exe" commit -m "Harsh Caption Generator - Full Stack Update" 2>nul

echo [2/3] Setting remote with authentication...
"%~dp0tools\git\cmd\git.exe" remote set-url origin https://%TOKEN%@github.com/fack86677-ops/caption-repo.git

echo [3/3] Pushing to main branch...
"%~dp0tools\git\cmd\git.exe" push -u origin main --force

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo  [SUCCESS] Code successfully pushed to GitHub!
    echo  URL: https://github.com/fack86677-ops/caption-repo
    echo ========================================================
) else (
    echo.
    echo [ERROR] Push fail ho gaya. Kripya apna Token check karein.
)

echo.
pause
