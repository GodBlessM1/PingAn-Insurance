# Git上传指南

## 前置条件

1. **安装Git**
   - 下载：https://git-scm.com/downloads
   - 安装时使用默认设置
   - 验证安装：打开命令行输入 `git --version`

2. **注册GitHub账号**
   - 访问：https://github.com/signup
   - 完成注册和邮箱验证

## 方法1：使用自动脚本（推荐，最简单）

### 步骤：
1. 双击运行 `git上传.bat`
2. 脚本会自动完成：
   - ✓ 初始化Git仓库
   - 创建.gitignore文件
   - 添加所有文件
   - 创建初始提交
3. 脚本会自动打开GitHub创建新仓库页面
4. 在GitHub上创建仓库后，按照脚本提示的命令连接和推送

### 优点：
- 一键完成所有准备工作
- 自动配置.gitignore
- 避免上传敏感文件

## 方法2：手动操作（适合了解Git的用户）

### 步骤1：初始化Git仓库
```bash
cd c:\Users\zhaoy\PycharmProjects\PingAn_Life_Returns_Analyzer
git init
```

### 步骤2：创建.gitignore文件
```bash
# Python
__pycache__/
*.py[cod]
*$py.class
*.so

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Data Files (Sensitive)
data/raw/*
data/processed/*
!data/raw/.gitkeep
!data/processed/.gitkeep

# Logs
logs/*.log
!logs/.gitkeep

# Environment Variables
.env
.env.local
.env.*.local

# Configuration with Secrets
config/config_local.yaml
config/secrets.yaml
```

### 步骤3：添加文件到Git
```bash
git add .
```

### 步骤4：创建提交
```bash
git commit -m "Initial commit: 平安寿险收益分析项目"
```

### 步骤5：在GitHub创建仓库
1. 访问：https://github.com/new
2. 仓库名：`PingAn_Life_Returns_Analyzer`
3. 选择：Public 或 Private
4. 点击 "Create repository"

### 步骤6：连接远程仓库
```bash
git remote add origin https://github.com/你的用户名/PingAn_Life_Returns_Analyzer.git
```

### 步骤7：推送到GitHub
```bash
git branch -M main
git push -u origin main
```

## 方法3：使用GitHub CLI（更现代）

### 安装GitHub CLI
1. 下载：https://cli.github.com/
2. 安装后验证：`gh --version`

### 登录GitHub
```bash
gh auth login
```

### 一键创建并推送
```bash
cd c:\Users\zhaoy\PycharmProjects\PingAn_Life_Returns_Analyzer
git init
git add .
git commit -m "Initial commit"
gh repo create PingAn_Life_Returns_Analyzer --public --source=. --remote=origin
git push -u origin main
```

## 常见问题

### Q1：提示需要配置用户信息？
A: 配置Git用户信息：
```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

### Q2：推送时提示认证失败？
A: 使用Personal Access Token：
1. GitHub设置 → Developer settings → Personal access tokens
2. 生成新token，选择repo权限
3. 使用token代替密码登录

### Q3：文件太大无法推送？
A: Git默认限制100MB，超过需要使用Git LFS：
```bash
git lfs install
git lfs track "*.parquet"
git lfs track "*.xlsx"
git add .gitattributes
```

### Q4：如何只上传website目录？
A: 进入website目录后单独初始化：
```bash
cd website
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/website.git
git push -u origin main
```

### Q5：如何更新已上传的代码？
A:
```bash
git add .
git commit -m "更新描述"
git push
```

## 推荐工作流

### 日常开发流程
1. 修改代码
2. 查看修改：`git status`
3. 添加修改：`git add .`
4. 提交修改：`git commit -m "描述修改内容"`
5. 推送到GitHub：`git push`

### 分支管理（可选）
```bash
# 创建新分支
git checkout -b feature-新功能

# 开发完成后
git checkout main
git merge feature-新功能
git push
```

## PyCharm集成

### 在PyCharm中使用Git
1. VCS → Enable Version Control Integration
2. 选择Git
3. 右键项目 → Git → Commit
4. 右键项目 → Git → Push

### 优点：
- 图形界面操作
- 可视化查看修改
- 方便的冲突解决

## 安全建议

1. **不要上传敏感数据**
   - .gitignore已配置忽略原始数据
   - 不要包含API密钥、密码等

2. **使用私有仓库**
   - 如果包含敏感信息，使用Private仓库
   - Public仓库任何人可见

3. **定期备份**
   - GitHub本身就是备份
   - 也可以定期导出仓库

## 下一步

上传成功后，您可以：
1. 启用GitHub Pages部署网站
2. 邀请协作者共同开发
3. 创建Issues跟踪问题
4. 使用Actions自动化部署

## 需要帮助？

- Git官方文档：https://git-scm.com/doc
- GitHub帮助：https://docs.github.com/
- PyCharm Git文档：https://www.jetbrains.com/help/pycharm/git.html
