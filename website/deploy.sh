#!/bin/bash

echo "========================================="
echo "  平安寿险收益分析网站 - 部署脚本"
echo "========================================="
echo ""
echo "本脚本将帮助您将网站部署到Netlify"
echo ""

# 检查是否在website目录
if [ ! -f "index.html" ]; then
    echo "错误：请在website目录下运行此脚本"
    exit 1
fi

echo "步骤1：准备部署文件..."
echo "✓ 找到 index.html"
echo "✓ 找到 simple.html"
echo "✓ 找到 charts/ 目录"
echo ""

echo "步骤2：检查必要文件..."
required_files=("index.html" "simple.html" "README.md" "部署指南.md" "启动网站.bat")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "警告：以下文件缺失："
    for file in "${missing_files[@]}"; do
        echo "  - $file"
    done
    echo ""
fi

echo "步骤3：检查图表文件..."
chart_count=$(ls -1 charts/*.png 2>/dev/null | wc -l)
if [ $chart_count -eq 0 ]; then
    echo "警告：charts/ 目录中没有找到PNG图表文件"
else
    echo "✓ 找到 $chart_count 个图表文件"
fi

echo ""
echo "========================================="
echo "  部署准备完成！"
echo "========================================="
echo ""
echo "接下来的步骤："
echo ""
echo "1. 访问 https://www.netlify.com/"
echo "2. 注册或登录账号"
echo "3. 将当前目录（website/）拖拽到Netlify网页"
echo "4. 等待部署完成（约1-2分钟）"
echo "5. 获得公网访问地址"
echo ""
echo "详细说明请查看：部署指南.md"
echo ""
echo "按任意键继续..."
read -n 1
