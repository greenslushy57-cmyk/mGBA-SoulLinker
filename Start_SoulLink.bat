@echo off
cd /d "%~dp0"

set "PY_EXE="
for /f "delims=" %%I in ('where python 2^>nul') do (
    echo %%I | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        if not defined PY_EXE set "PY_EXE=%%I"
    )
)

if not defined PY_EXE (
    for %%P in (
        "%LocalAppData%\Programs\Python\Python313\python.exe"
        "%LocalAppData%\Programs\Python\Python312\python.exe"
        "%LocalAppData%\Programs\Python\Python311\python.exe"
        "%LocalAppData%\Programs\Python\Python310\python.exe"
        "C:\Python313\python.exe"
        "C:\Python312\python.exe"
        "C:\Python311\python.exe"
    ) do (
        if exist %%P if not defined PY_EXE set "PY_EXE=%%~P"
    )
)

if not defined PY_EXE (
    echo Could not find Python! Please install Python from python.org.
    pause
    exit /b 1
)

echo Using Python: %PY_EXE%
"%PY_EXE%" launch_soullink.py
