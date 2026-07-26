@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Jini YouTube Downloader - zrok Server
cd /d "%~dp0"

set "ZROK_EXE=%CD%\zrok2.exe"
set "ZROK_ARCHIVE=%CD%\zrok2_windows.tar.gz"
set "ZROK_NAME_FILE=%CD%\.zrok_name"
set "ZROK_STATUS_FILE=%TEMP%\jini_zrok_status.txt"

echo.
echo ==============================================
echo   Jini YouTube Downloader - Free Fixed URL
echo ==============================================
echo.

where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo Install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/5] Creating the Python environment...
    py -3 -m venv .venv
    if errorlevel 1 goto :error
) else (
    echo [1/5] Python environment: OK
)

echo [2/5] Installing required packages...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --quiet --upgrade pip
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --quiet -r requirements.txt
if errorlevel 1 goto :error

if not exist "%ZROK_EXE%" goto :install_zrok
echo [3/5] zrok2: OK
goto :check_zrok_account

:install_zrok
echo [3/5] Downloading the latest official zrok2...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $release=Invoke-RestMethod 'https://api.github.com/repos/openziti/zrok/releases/latest'; $asset=$release.assets | Where-Object { $_.name -match 'windows_amd64\.tar\.gz$' } | Select-Object -First 1; if (-not $asset) { throw 'Windows zrok2 download was not found.' }; Invoke-WebRequest -UseBasicParsing -Uri $asset.browser_download_url -OutFile 'zrok2_windows.tar.gz'"
if errorlevel 1 goto :error
tar -xf "%ZROK_ARCHIVE%" -C "%CD%" zrok2.exe
if errorlevel 1 goto :error
del /q "%ZROK_ARCHIVE%" >nul 2>nul

:check_zrok_account
"%ZROK_EXE%" status >"%ZROK_STATUS_FILE%" 2>&1
findstr /C:"<<SET>>" "%ZROK_STATUS_FILE%" >nul 2>nul
if not errorlevel 1 goto :account_ready

echo.
echo [4/5] Connect this computer to your zrok account.
echo Copy the Account Token from the zrok web page.
echo Do not send the token to ChatGPT or GitHub.
set /p "ZROK_TOKEN=Paste Account Token here: "
if not defined ZROK_TOKEN (
    echo [ERROR] No token was entered.
    goto :error
)
"%ZROK_EXE%" enable "%ZROK_TOKEN%"
set "ZROK_TOKEN="
if errorlevel 1 goto :error
goto :choose_name

:account_ready
echo [4/5] zrok account: OK

:choose_name
if exist "%ZROK_NAME_FILE%" set /p ZROK_NAME=<"%ZROK_NAME_FILE%"
if not defined ZROK_NAME set "ZROK_NAME=jini-youtube-downloader"

:validate_name
powershell -NoProfile -Command "if ($env:ZROK_NAME -notmatch '^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$') { exit 1 }"
if not errorlevel 1 goto :check_name
echo.
echo Use only lowercase letters, numbers, and hyphens.
set "ZROK_NAME="
set /p "ZROK_NAME=Enter a fixed URL name: "
if not defined ZROK_NAME goto :error
goto :validate_name

:check_name
"%ZROK_EXE%" list names >"%TEMP%\jini_zrok_names.txt" 2>&1
findstr /I /C:"%ZROK_NAME%" "%TEMP%\jini_zrok_names.txt" >nul 2>nul
if not errorlevel 1 goto :name_ready

echo.
echo Reserving the fixed URL name: %ZROK_NAME%
"%ZROK_EXE%" create name -n public "%ZROK_NAME%"
if not errorlevel 1 goto :name_ready

echo.
echo That URL name is unavailable.
set "ZROK_NAME="
set /p "ZROK_NAME=Enter another name: "
if not defined ZROK_NAME goto :error
goto :validate_name

:name_ready
>"%ZROK_NAME_FILE%" echo %ZROK_NAME%

echo [5/5] Starting the download server...
start "Jini YouTube Server" /min ".venv\Scripts\python.exe" app.py
timeout /t 5 /nobreak >nul

echo.
echo ==============================================
echo   FIXED URL
echo   https://%ZROK_NAME%.share.zrok.io
echo ==============================================
echo.
echo Keep this window and your computer running.
echo Press Ctrl+C in this window to stop the server.
echo.

"%ZROK_EXE%" share public 127.0.0.1:10000 -n "public:%ZROK_NAME%" --headless
goto :eof

:error
echo.
echo [ERROR] Setup or startup failed.
echo Check the last error shown above.
pause
exit /b 1
