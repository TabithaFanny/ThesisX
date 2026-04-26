#!/bin/bash
# Mac 打包脚本
# 在 Mac 上运行此脚本

set -e

echo "=== 文表智联 Mac 打包脚本 ==="

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 创建虚拟环境
if [ ! -d "venv_mac" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv_mac
fi

# 激活虚拟环境
source venv_mac/bin/activate

# 安装依赖
echo "安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# 转换图标 (如果有 iconutil)
if [ -f "app/resources/thesisx_icon.ico" ] && ! [ -f "app/resources/thesisx_icon.icns" ]; then
    echo "注意: 需要手动转换图标为 .icns 格式"
    echo "可以使用在线工具或 iconutil 命令"
fi

# 打包
echo "开始打包..."
pyinstaller build_mac.spec --noconfirm

echo ""
echo "=== 打包完成 ==="
echo "输出目录: dist/文表智联.app"
echo ""
echo "分发前请进行代码签名:"
echo "  codesign --deep --force --sign \"Developer ID Application: YOUR_NAME\" dist/文表智联.app"
