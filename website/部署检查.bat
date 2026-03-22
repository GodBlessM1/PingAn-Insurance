@echo off
chcp 65001 >nul
echo =========================================
echo   平安寿险收益分析网站 - 部署检查
echo =========================================
echo.

cd /d "%~dp0"

echo 步骤1：检查部署文件...
if exist "index.html" (
    echo [√] index.html
) else (
    echo [×] index.html - 缺失
)

if exist "simple.html" (
    echo [√] simple.html
) else (
    echo [×] simple.html - 缺失
)

if exist "README.md" (
    echo [√] README.md
) else (
    echo [×] README.md - 缺失
)

if exist "部署指南.md" (
    echo [√] 部署指南.md
) else (
    echo [×] 部署指南.md - 缺失
)

if exist "启动网站.bat" (
    echo [√] 启动网站.bat
) else (
    echo [×] 启动网站.bat - 缺失
)

echo.
echo 步骤2：检查图表文件...
if exist "charts" (
    echo [√] charts/ 目录存在
    dir /b "charts\*.png" >nul 2>&1
    if %errorlevel% equ 0 (
        for /f %%a in ('dir /b "charts\*.png" ^| find /c /v ""') do set count=%%a
        echo [√] 找到 %count% 个图表文件
    ) else (
        echo [×] charts/ 目录中没有PNG文件
    )
) else (
    echo [×] charts/ 目录不存在
)

echo.
echo =========================================
echo   检查完成！
echo =========================================
echo.
echo 推荐部署方式：
echo.
echo 方式1：Netlify（最简单，免费）
echo   1. 访问 https://www.netlify.com/
echo   2. 注册或登录
echo   3. 将当前文件夹拖拽到网页
echo   4. 等待1-2分钟
echo   5. 获得公网地址
echo.
echo 方式2：GitHub Pages（免费）
echo   1. 访问 https://github.com/
echo   2. 创建新仓库
echo   3. 上传文件
echo   4. 启用GitHub Pages
echo   5. 获得公网地址
echo.
echo 详细说明请查看：部署指南.md
echo.
echo 按任意键打开部署指南...
pause >nul
start "" "部署指南.md"
