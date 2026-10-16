@echo off
chcp 65001 >nul
title 个人工作生活 APP
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境 .venv
    echo 请先执行: python -m venv .venv
    echo          .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo 正在启动服务，请稍候...
".venv\Scripts\python.exe" run.py

echo.
echo 服务已停止。
pause
