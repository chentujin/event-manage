#!/bin/bash

# 后端服务管理脚本
# 用法: ./backend_service.sh [start|stop|restart|status]

BACKEND_DIR="/Users/chen/Qoder/event-manage/backend"
SERVICE_NAME="后端Flask服务"
PORT=5001
PID_FILE="/tmp/backend_service.pid"
LOG_FILE="/tmp/backend.log"
PYTHON_CMD="python3"

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
    if [ ! -d "$BACKEND_DIR" ]; then
        log_error "后端目录不存在: $BACKEND_DIR"
        exit 1
    fi
}

# 检查Python和依赖是否安装
check_dependencies() {
    if ! command -v $PYTHON_CMD &> /dev/null; then
        log_error "$PYTHON_CMD 未安装"
        exit 1
    fi
    
    log_info "Python 版本: $($PYTHON_CMD --version)"
    
    # 检查是否在虚拟环境中
    if [ -n "$VIRTUAL_ENV" ]; then
        log_info "使用虚拟环境: $VIRTUAL_ENV"
    fi
    
    # 检查必要的Python包
    cd "$BACKEND_DIR" || exit 1
    if ! $PYTHON_CMD -c "import flask" 2>/dev/null; then
        log_error "Flask 未安装，请先运行: pip install -r requirements.txt"
        exit 1
    fi
    
    if ! $PYTHON_CMD -c "import sqlalchemy" 2>/dev/null; then
        log_error "SQLAlchemy 未安装，请先运行: pip install -r requirements.txt"
        exit 1
    fi
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
        pgrep -f "python3.*run.py" 2>/dev/null
    fi
}

# 检查数据库
check_database() {
    cd "$BACKEND_DIR" || exit 1
    
    if [ ! -f "instance/event_manage_dev.db" ] && [ ! -f "event_manage_dev.db" ]; then
        log_warning "数据库文件不存在，正在初始化..."
        if $PYTHON_CMD init_db.py; then
            log_success "数据库初始化成功"
        else
            log_error "数据库初始化失败"
            return 1
        fi
    fi
}

# 启动服务
start_service() {
    log_info "正在启动 $SERVICE_NAME..."
    
    check_directory
    check_dependencies
    check_database
    
    if is_running; then
        log_warning "$SERVICE_NAME 已经在运行中 (PID: $(get_pid))"
        return 0
    fi
    
    if ! check_port; then
        log_error "无法启动服务，端口 $PORT 被占用"
        return 1
    fi
    
    cd "$BACKEND_DIR" || exit 1
    
    # 清理旧的日志文件
    if [ -f "$LOG_FILE" ]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        log_info "备份旧日志文件: ${LOG_FILE}.old"
    fi
    
    # 启动服务
    log_info "启动Flask应用..."
    nohup $PYTHON_CMD run.py > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # 保存PID
    echo $pid > "$PID_FILE"
    
    # 等待服务启动
    log_info "等待服务启动..."
    local attempts=0
    local max_attempts=30
    
    while [ $attempts -lt $max_attempts ]; do
        if curl -s "http://localhost:$PORT/api/v1/health" >/dev/null 2>&1; then
            break
        fi
        sleep 1
        attempts=$((attempts + 1))
        echo -n "."
    done
    echo ""
    
    if is_running; then
        log_success "$SERVICE_NAME 启动成功! (PID: $pid)"
        log_info "服务地址: http://localhost:$PORT"
        log_info "API地址: http://localhost:$PORT/api/v1"
        log_info "日志文件: $LOG_FILE"
        
        # 测试健康检查
        if curl -s "http://localhost:$PORT/api/v1/health" >/dev/null 2>&1; then
            log_success "健康检查通过"
        else
            log_warning "健康检查失败，但服务已启动"
        fi
        
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
    local remaining_pid=$(pgrep -f "python3.*run.py" 2>/dev/null)
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
        
        # 测试API健康检查
        echo ""
        log_info "API健康检查:"
        if curl -s "http://localhost:$PORT/api/v1/health" >/dev/null 2>&1; then
            log_success "健康检查: 通过"
        else
            log_warning "健康检查: 失败"
        fi
        
        # 显示日志最后几行
        if [ -f "$LOG_FILE" ]; then
            echo ""
            log_info "最新日志 (最后10行):"
            tail -10 "$LOG_FILE"
        fi
        
        return 0
    else
        log_warning "$SERVICE_NAME 未在运行"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    echo "后端服务管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start    启动后端服务"
    echo "  stop     停止后端服务"
    echo "  restart  重启后端服务"
    echo "  status   显示服务状态"
    echo "  help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动服务"
    echo "  $0 stop     # 停止服务"
    echo "  $0 status   # 查看状态"
    echo ""
    echo "注意事项:"
    echo "  - 服务将在端口 $PORT 上启动"
    echo "  - 日志文件保存在 $LOG_FILE"
    echo "  - 自动检查数据库状态"
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
