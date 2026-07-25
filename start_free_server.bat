@echo off
chcp 65001 >nul
title Jini YouTube Downloader - Free Server
cd /d "%~dp0"

echo.
echo ==============================================
echo   Jini YouTube Downloader 무료 서버 시작
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
    echo [1/4] Python 실행 환경을 만드는 중...
    py -3 -m venv .venv
    if errorlevel 1 goto :error
)

echo [2/4] 필요한 프로그램을 설치하는 중...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --quiet -r requirements.txt
if errorlevel 1 goto :error

if not exist "cloudflared.exe" (
    echo [3/4] 무료 접속 주소 프로그램을 받는 중...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'"
    if errorlevel 1 goto :error
) else (
    echo [3/4] 무료 접속 주소 프로그램 확인 완료
)

echo [4/4] 다운로드 서버를 시작하는 중...
start "Jini YouTube Server" /min ".venv\Scripts\python.exe" app.py
timeout /t 5 /nobreak >nul

echo.
echo 아래에 표시되는 https:// 로 시작하는 trycloudflare.com 주소를 사용하세요.
echo 이 창을 닫으면 주소와 다운로드 서버가 종료됩니다.
echo.
cloudflared.exe tunnel --url http://127.0.0.1:10000
goto :eof

:error
echo.
echo 설치 또는 실행 중 오류가 발생했습니다.
echo 이 창의 마지막 오류 내용을 확인해 주세요.
pause
exit /b 1
