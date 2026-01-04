#!/bin/bash
# 项目快速打包脚本

echo "🚀 智能农场机器人游戏 - 快速打包工具"
echo "======================================"
echo ""
echo "请选择打包选项："
echo "1) 仅核心文件"
echo "2) 核心文件 + 文档"
echo "3) 完整打包（包含文档、演示、测试）"
echo "4) 自定义选项"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo "📦 打包核心文件..."
        python3 package_project.py
        ;;
    2)
        echo "📦 打包核心文件 + 文档..."
        python3 package_project.py --docs
        ;;
    3)
        echo "📦 完整打包..."
        python3 package_project.py --all
        ;;
    4)
        echo ""
        read -p "包含文档? (y/n): " include_docs
        read -p "包含演示? (y/n): " include_demos
        read -p "包含测试? (y/n): " include_tests
        read -p "输出格式 (zip/folder): " output_format
        
        args=""
        [[ $include_docs == "y" ]] && args="$args --docs"
        [[ $include_demos == "y" ]] && args="$args --demos"
        [[ $include_tests == "y" ]] && args="$args --tests"
        [[ -n $output_format ]] && args="$args --format $output_format"
        
        echo "📦 自定义打包: python3 package_project.py $args"
        python3 package_project.py $args
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "✅ 打包完成！"
echo ""
echo "输出目录: dist/"
ls -lh dist/ | tail -n 5
