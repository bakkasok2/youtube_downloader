@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
title Jini YouTube Downloader - zrok Server
cd /d "%~dp0"

set "ZROK_EXE=%CD%\zrok2.exe"
set "ZROK_ARCHIVE=%CD%\zrok2_windows.tar.gz"
set "ZROK_NAME_FILE=%CD%\.zrok_name"
set "ZROK_STATUS_FILE=%TEMP%\jini_zrok_status.txt"

echo.
echo ==============================================
echo   Jini YouTube Downloader 무료 고정 주소 서버
echo ==============================================
echo.

where py >nul 2>nul
if errorlevel 1 (
    echo Python이 설치되어 있지 않습니다.
    echo https://www.python.org/downloads/ 에서 Python을 먼저 설치해 주세요.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/5] Python 실행 환경을 만드는 중...
    py -3 -m venv .venv
    if errorlevel 1 goto :error
) else (
    echo [1/5] Python 실행 환경 확인 완료
)

echo [2/5] 필요한 프로그램을 설치하는 중...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --quiet -r requirements.txt
if errorlevel 1 goto :error

if not exist "%ZROK_EXE%" (
    echo [3/5] 최신 zrok2를 받는 중...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $release=Invoke-RestMethod 'https://api.github.com/repos/openziti/zrok/releases/latest'; $asset=$release.assets | Where-Object { $_.name -match 'windows_amd64\.tar\.gz$' } | Select-Object -First 1; if (-not $asset) { throw 'Windows zrok2 download was not found.' }; Invoke-WebRequest -UseBasicParsing -Uri $asset.browser_download_url -OutFile 'zrok2_windows.tar.gz'"
    if errorlevel 1 goto :error
    tar -xf "%ZROK_ARCHIVE%" -C "%CD%" zrok2.exe
    if errorlevel 1 goto :error
    del /q "%ZROK_ARCHIVE%" >nul 2>nul
) else (
    echo [3/5] zrok2 확인 완료
)

"%ZROK_EXE%" status >"%ZROK_STATUS_FILE%" 2>&1
findstr /C:"<<SET>>" "%ZROK_STATUS_FILE%" >nul 2>nul
if errorlevel 1 (
    echo.
    echo [4/5] zrok 계정을 이 컴퓨터에 연결합니다.
    echo zrok 웹 화면에서 Account Token을 복사해 아래에 붙여넣으세요.
    echo 토큰은 이 컴퓨터의 zrok 설정에만 저장됩니다.
    set /p "ZROK_TOKEN=Account Token: "
    if not defined ZROK_TOKEN (
        echo 토큰을 입력하지 않았습니다.
        goto :error
    )
    "%ZROK_EXE%" enable "%ZROK_TOKEN%"
    set "ZROK_TOKEN="
    if errorlevel 1 goto :error
) else (
    echo [4/5] zrok 계정 연결 확인 완료
)

if exist "%ZROK_NAME_FILE%" (
    set /p "ZROK_NAME="<"%ZROK_NAME_FILE%"
)
if not defined ZROK_NAME set "ZROK_NAME=jini-youtube-downloader"

:reserve_name
powershell -NoProfile -Command "if ($env:ZROK_NAME -notmatch '^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$') { exit 1 }"
if errorlevel 1 (
    echo.
    echo 주소 이름은 영문 소문자, 숫자, 하이픈만 사용할 수 있습니다.
    set "ZROK_NAME="
    set /p "ZROK_NAME=새 주소 이름: "
    if not defined ZROK_NAME goto :error
    goto :reserve_name
)

"%ZROK_EXE%" list names | findstr /I /C:"%ZROK_NAME%" >nul 2>nul
if not errorlevel 1 goto :name_ready

echo.
echo 고정 주소 이름 "%ZROK_NAME%"을 예약하는 중...
"%ZROK_EXE%" create name -n public "%ZROK_NAME%"
if errorlevel 1 (
    echo.
    echo 이 주소 이름은 이미 다른 사람이 사용 중이거나 사용할 수 없습니다.
    echo 영문 소문자, 숫자, 하이픈만 사용해 다른 이름을 입력하세요.
    set "ZROK_NAME="
    set /p "ZROK_NAME=새 주소 이름: "
    if not defined ZROK_NAME goto :error
    goto :reserve_name
)

:name_ready
>"%ZROK_NAME_FILE%" echo %ZROK_NAME%

echo [5/5] 다운로드 서버를 시작하는 중...
start "Jini YouTube Server" /min ".venv\Scripts\python.exe" app.py
timeout /t 5 /nobreak >nul

echo.
echo ==============================================
echo   고정 접속 주소
echo   https://%ZROK_NAME%.share.zrok.io
echo ==============================================
echo.
echo 위 주소는 다음에 실행해도 그대로입니다.
echo 이 창과 컴퓨터가 켜져 있어야 주소가 작동합니다.
echo 종료하려면 이 창에서 Ctrl+C를 누르세요.
echo.

"%ZROK_EXE%" share public 127.0.0.1:10000 -n "public:%ZROK_NAME%" --headless
goto :eof

:error
echo.
echo 설치 또는 실행 중 오류가 발생했습니다.
echo 이 창의 마지막 오류 내용을 확인해 주세요.
pause
exit /b 1
