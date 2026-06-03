#!/bin/bash
# ============================================================
# ifrit-apitest Web UI 调试启动脚本（Linux/macOS）
# 作者：孙文龙
# 用途：前台启动 UI 服务，用于开发和调试
# ============================================================

set -e

# 获取脚本所在目录
UI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$UI_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo ""
echo "============================================================"
echo " ifrit-apitest Web UI 调试模式启动"
echo " 提示: 按 Ctrl+C 停止服务"
echo "============================================================"
echo ""

# ============================================================
# 检查 Python 环境
# ============================================================

log_info "检查 Python 环境..."

if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    log_error "未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
log_success "Python 版本: $PYTHON_VERSION"

# ============================================================
# 检查虚拟环境
# ============================================================

VENV_DIR="$UI_DIR/.venv"
REQUIREMENTS="$UI_DIR/requirements-ui.txt"

if [ ! -d "$VENV_DIR" ]; then
    log_info "虚拟环境不存在，正在创建..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    log_success "虚拟环境创建完成"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# ============================================================
# 安装依赖
# ============================================================

if [ -f "$REQUIREMENTS" ]; then
    log_info "检查依赖安装..."
    
    if ! pip show flask &> /dev/null; then
        log_info "安装依赖包..."
        pip install -r "$REQUIREMENTS" --quiet
        log_success "依赖安装完成"
    else
        log_success "依赖已安装"
    fi
else
    log_error "依赖文件不存在: $REQUIREMENTS"
    exit 1
fi

# ============================================================
# 检查配置文件
# ============================================================

CONFIG_FILE="$UI_DIR/config.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    log_error "配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 读取配置
PORT=$(grep 'port:' "$CONFIG_FILE" | awk '{print $2}')
DEBUG=$(grep 'debug:' "$CONFIG_FILE" | awk '{print $2}')

log_success "配置加载完成"
log_info "服务端口: $PORT"
log_info "调试模式: $DEBUG"

# ============================================================
# 启动服务（前台）
# ============================================================

echo ""
echo "============================================================"
echo " 启动调试模式..."
echo " 访问地址: http://localhost:$PORT"
echo " 按 Ctrl+C 停止服务"
echo "============================================================"
echo ""

# 前台启动（不后台运行）
$PYTHON_CMD app.py
