#!/bin/bash
# ============================================================
# ifrit-apitest Web UI 启动脚本（Linux/macOS）
# 作者：孙文龙
# 用途：后台启动 UI 服务，自动检查环境和安装依赖
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
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================
# 检查 Python 环境
# ============================================================

log_info "检查 Python 环境..."

if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    log_error "未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

# 优先使用 python3
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
    log_success "虚拟环境创建完成: $VENV_DIR"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# ============================================================
# 安装依赖
# ============================================================

if [ -f "$REQUIREMENTS" ]; then
    log_info "检查依赖安装..."
    
    # 检查是否已安装依赖
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

log_success "配置文件检查通过"

# ============================================================
# 检查端口占用
# ============================================================

PORT=$(grep 'port:' "$CONFIG_FILE" | awk '{print $2}')

if command -v lsof &> /dev/null; then
    if lsof -i :"$PORT" &> /dev/null; then
        log_warn "端口 $PORT 已被占用，正在尝试停止旧进程..."
        bash "$UI_DIR/stop.sh"
        sleep 2
    fi
fi

# ============================================================
# 启动服务
# ============================================================

PID_FILE="$UI_DIR/ui.pid"
LOG_FILE="$UI_DIR/ui.log"

log_info "启动 ifrit-apitest Web UI..."
log_info "服务端口: $PORT"
log_info "日志文件: $LOG_FILE"

# 后台启动
nohup $PYTHON_CMD app.py > "$LOG_FILE" 2>&1 &
PID=$!

# 保存 PID
echo $PID > "$PID_FILE"

# 等待服务启动
sleep 2

# 检查进程是否存活
if kill -0 $PID 2>/dev/null; then
    log_success "UI 服务启动成功!"
    log_info "进程 ID: $PID"
    log_info "访问地址: http://0.0.0.0:$PORT"
    log_info "停止服务: bash $UI_DIR/stop.sh"
else
    log_error "服务启动失败，请查看日志: $LOG_FILE"
    exit 1
fi

echo ""
echo "============================================================"
echo " ifrit-apitest Web UI 已启动"
echo " 访问地址: http://localhost:$PORT"
echo " 停止服务: bash stop.sh"
echo "============================================================"
echo ""
