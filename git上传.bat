@echo off
chcp 65001 >nul
echo =========================================
echo   平安寿险收益分析项目 - Git上传脚本
echo =========================================
echo.

cd /d "%~dp0"

echo 步骤1：检查Git仓库...
if exist .git (
    echo [√] Git仓库已存在
) else (
    echo [×] Git仓库不存在，正在初始化...
    git init
    if %errorlevel% equ 0 (
        echo [√] Git仓库初始化成功
    ) else (
        echo [×] Git初始化失败，请确认已安装Git
        pause
        exit /b 1
    )
)

echo.
echo 步骤2：检查.gitignore...
if exist .gitignore (
    echo [√] .gitignore已存在
) else (
    echo [×] .gitignore不存在，正在创建...
    (
        echo # Python
        echo __pycache__/
        echo *.py[cod]
        echo *$py.class
        echo *.so
        echo.
        echo # IDEs
        echo .vscode/
        echo .idea/
        echo *.swp
        echo *.swo
        echo *~
        echo .DS_Store
        echo.
        echo # Data Files ^(Sensitive^)
        echo data/raw/*
        echo data/processed/*
        echo !data/raw/.gitkeep
        echo !data/processed/.gitkeep
        echo.
        echo # Logs
        echo logs/*.log
        echo !logs/.gitkeep
        echo.
        echo # Environment Variables
        echo .env
        echo .env.local
        echo .env.*.local
        echo.
        echo # Configuration with Secrets
        echo config/config_local.yaml
        echo config/secrets.yaml
    ) > .gitignore
    echo [√] .gitignore创建成功
)

echo.
echo 步骤3：添加文件到Git...
git add .
if %errorlevel% equ 0 (
    echo [√] 文件添加成功
) else (
    echo [×] 文件添加失败
    pause
    exit /b 1
)

echo.
echo 步骤4：创建初始提交...
git commit -m "Initial commit: 平安寿险收益分析项目

- 完整的数据分析系统
- 包含网站展示页面
- 详细的分析报告
- 部署指南和脚本"
if %errorlevel% equ 0 (
    echo [√] 提交成功
) else (
    echo [×] 提交失败
    pause
    exit /b 1
)

echo.
echo =========================================
echo   本地Git仓库准备完成！
echo =========================================
echo.
echo 接下来的步骤：
echo.
echo 1. 在GitHub上创建新仓库
echo    访问: https://github.com/new
echo    仓库名建议: PingAn_Life_Returns_Analyzer
echo.
echo 2. 连接到远程仓库
echo    git remote add origin https://github.com/你的用户名/PingAn_Life_Returns_Analyzer.git
echo.
echo 3. 推送到GitHub
echo    git push -u origin main
echo.
echo 或者使用GitHub CLI：
echo    gh repo create PingAn_Life_Returns_Analyzer --public
echo    git push -u origin main
echo.
echo 按任意键打开GitHub创建新仓库...
pause >nul
start "" https://github.com/new
