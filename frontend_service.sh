#!/bin/bash

# 前端服务管理脚本
# 用法: ./frontend_service.sh [start|stop|restart|status]

FRONTEND_DIR="/Users/chen/Qoder/event-manage/frontend"
SERVICE_NAME="前端开发服务器"
PORT=3000
PID_FILE="/tmp/frontend_service.pid"

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

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查目录是否存在
check_directory() {
    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "前端目录不存在: $FRONTEND_DIR"
        exit 1
    fi
}

# 检查Node.js和npm是否安装
check_dependencies() {
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装"
        exit 1
    fi
    
    log_info "Node.js 版本: $(node --version)"
    log_info "npm 版本: $(npm --version)"
}

# 检查端口是否被占用
check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "端口 $PORT 已被占用"
        return 1
    fi
    return 0
}

# 获取服务PID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE" 2>/dev/null
    else
        pgrep -f "npm run dev.*frontend" 2>/dev/null
    fi
}

# 启动服务
start_service() {
    log_info "正在启动 $SERVICE_NAME..."
    
    check_directory
    check_dependencies
    
    if is_running; then
        log_warning "$SERVICE_NAME 已经在运行中 (PID: $(get_pid))"
        return 0
    fi
    
    if ! check_port; then
        log_error "无法启动服务，端口 $PORT 被占用"
        return 1
    fi
    
    cd "$FRONTEND_DIR" || exit 1
    
    # 清理可能的缓存
    if [ -d "node_modules/.vite" ]; then
        log_info "清理 Vite 缓存..."
        rm -rf node_modules/.vite
    fi
    
    # 启动服务
    log_info "启动开发服务器..."
    nohup npm run dev > /tmp/frontend.log 2>&1 &
    local pid=$!
    
    # 保存PID
    echo $pid > "$PID_FILE"
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 5
    
    if is_running; then
        log_success "$SERVICE_NAME 启动成功! (PID: $pid)"
        log_info "服务地址: http://localhost:$PORT"
        log_info "日志文件: /tmp/frontend.log"
        return 0
    else
        log_error "$SERVICE_NAME 启动失败"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止服务
stop_service() {
    log_info "正在停止 $SERVICE_NAME..."
    
    local pid=$(get_pid)
    if [ -z "$pid" ]; then
        log_warning "$SERVICE_NAME 未在运行"
        rm -f "$PID_FILE"
        return 0
    fi
    
    # 尝试优雅停止
    if kill -TERM "$pid" 2>/dev/null; then
        log_info "发送停止信号到进程 $pid..."
        sleep 3
        
        if kill -0 "$pid" 2>/dev/null; then
            log_warning "进程未响应，强制停止..."
            kill -KILL "$pid" 2>/dev/null
        fi
    fi
    
    # 清理PID文件
    rm -f "$PID_FILE"
    
    # 检查是否还有相关进程
    local remaining_pid=$(pgrep -f "npm run dev.*frontend" 2>/dev/null)
    if [ -n "$remaining_pid" ]; then
        log_warning "强制停止剩余进程: $remaining_pid"
        kill -KILL "$remaining_pid" 2>/dev/null
    fi
    
    log_success "$SERVICE_NAME 已停止"
}

# 重启服务
restart_service() {
    log_info "正在重启 $SERVICE_NAME..."
    stop_service
    sleep 2
    start_service
}

# 检查服务状态
is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
    return 1
}

# 显示服务状态
show_status() {
    log_info "$SERVICE_NAME 状态检查..."
    
    local pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        log_success "$SERVICE_NAME 正在运行 (PID: $pid)"
        
        # 检查端口
        if check_port; then
            log_info "端口 $PORT: 可用"
        else
            log_warning "端口 $PORT: 被占用"
        fi
        
        # 显示进程信息
        if command -v ps &> /dev/null; then
            echo ""
            log_info "进程信息:"
            ps -p "$pid" -o pid,ppid,cmd,etime
        fi
        
        # 显示日志最后几行
        if [ -f "/tmp/frontend.log" ]; then
            echo ""
            log_info "最新日志 (最后10行):"
            tail -10 /tmp/frontend.log
        fi
        
        return 0
    else
        log_warning "$SERVICE_NAME 未在运行"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    echo "前端服务管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start    启动前端服务"
    echo "  stop     停止前端服务"
    echo "  restart  重启前端服务"
    echo "  status   显示服务状态"
    echo "  help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动服务"
    echo "  $0 stop     # 停止服务"
    echo "  $0 status   # 查看状态"
}

# 主函数
main() {
    case "${1:-help}" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
