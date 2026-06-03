#!/bin/bash
# ============================================================
# ifrit-apitest Web UI 停止脚本（Linux/macOS）
# 作者：孙文龙
# 用途：停止后台运行的 UI 服务
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
# 读取 PID 文件
# ============================================================

PID_FILE="$UI_DIR/ui.pid"

if [ ! -f "$PID_FILE" ]; then
    log_warn "PID 文件不存在，服务可能未运行"
    exit 0
fi

PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ! kill -0 "$PID" 2>/dev/null; then
    log_warn "进程 $PID 不存在，清理 PID 文件"
    rm -f "$PID_FILE"
    exit 0
fi

# ============================================================
# 停止服务
# ============================================================

log_info "正在停止 UI 服务 (PID: $PID)..."

# 优雅停止
kill -15 "$PID" 2>/dev/null

# 等待进程退出
WAIT_TIME=0
MAX_WAIT=10

while kill -0 "$PID" 2>/dev/null && [ $WAIT_TIME -lt $MAX_WAIT ]; do
    sleep 1
    WAIT_TIME=$((WAIT_TIME + 1))
    echo -n "."
done

echo ""

# 检查是否已退出
if kill -0 "$PID" 2>/dev/null; then
    log_warn "进程未响应优雅停止，强制终止..."
    kill -9 "$PID" 2>/dev/null
    sleep 1
fi

# 清理 PID 文件
rm -f "$PID_FILE"

if ! kill -0 "$PID" 2>/dev/null; then
    log_success "UI 服务已停止"
else
    log_error "停止失败，请手动执行: kill -9 $PID"
    exit 1
fi

echo ""
echo "============================================================"
echo " ifrit-apitest Web UI 已停止"
echo "============================================================"
echo ""
