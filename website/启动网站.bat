@echo off
chcp 65001 >nul
echo 正在启动平安寿险收益分析网站...
echo.
echo 网站地址: http://localhost:8080
echo.
echo 按 Ctrl+C 停止服务器
echo.

cd /d "%~dp0"
python -m http.server 8080
